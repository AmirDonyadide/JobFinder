"""Prepare and remove private product files on ephemeral CI runners."""

from __future__ import annotations

import argparse
import base64
import binascii
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from jobfinder.env import EnvSettings
from jobfinder.paths import GOOGLE_TOKEN_FILE
from jobfinder.products import FinderProduct, product_from_env
from jobfinder.scraper.settings import parse_apify_api_tokens

REQUIRED_GOOGLE_SCOPES = {
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
}
MANIFEST_NAME = ".runtime-files.json"


class RuntimeFileError(RuntimeError):
    """Raised when CI secrets or generated private files are invalid."""


@dataclass(frozen=True)
class RuntimePreparation:
    """Summary of the private files written for one CI run."""

    product: str
    files: tuple[str, ...]
    needs_google: bool
    needs_evaluation: bool
    needs_pdf: bool


def _require_ci(env: EnvSettings, require_ci: bool) -> None:
    if require_ci and env.get("GITHUB_ACTIONS").strip().lower() != "true":
        raise RuntimeFileError(
            "Runtime-file preparation is restricted to GitHub Actions."
        )


def _write_private(path: Path, value: str, written: list[Path]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.strip() + "\n", encoding="utf-8")
    path.chmod(0o600)
    written.append(path)


def _token_scopes(token: dict[str, object]) -> set[str]:
    raw_scopes = token.get("scopes") or token.get("scope") or []
    if isinstance(raw_scopes, str):
        return set(raw_scopes.split())
    if isinstance(raw_scopes, list):
        return {str(scope) for scope in raw_scopes}
    return set()


def _validated_google_token(value: str) -> str:
    try:
        token = json.loads(value)
    except json.JSONDecodeError as exc:
        raise RuntimeFileError(f"GOOGLE_TOKEN_JSON is not valid JSON: {exc}") from exc

    required_fields = ("client_id", "client_secret", "refresh_token")
    if token.get("type") != "authorized_user" and not all(
        token.get(field) for field in required_fields
    ):
        raise RuntimeFileError(
            "GOOGLE_TOKEN_JSON must contain authorized-user OAuth credentials."
        )

    missing_scopes = sorted(REQUIRED_GOOGLE_SCOPES - _token_scopes(token))
    if missing_scopes:
        raise RuntimeFileError(
            "GOOGLE_TOKEN_JSON is missing required OAuth scope(s): "
            + ", ".join(missing_scopes)
        )
    return value


def prepare_runtime_files(
    env: EnvSettings | None = None,
    product: FinderProduct | None = None,
    *,
    require_ci: bool = True,
    token_file: Path = GOOGLE_TOKEN_FILE,
) -> RuntimePreparation:
    """Validate CI settings and materialize private files for one product."""
    settings = env or EnvSettings()
    _require_ci(settings, require_ci)
    finder_product = product or product_from_env(settings)

    mode = settings.get("JOBFINDER_PIPELINE_MODE", "scrape_and_evaluate")
    output_mode = settings.get("JOBFINDER_SCRAPER_OUTPUT_MODE", "google_sheets")
    needs_evaluation = mode == "scrape_and_evaluate"
    if mode not in {"scrape_only", "scrape_and_evaluate"}:
        raise RuntimeFileError(f"Unsupported pipeline mode: {mode!r}.")
    if output_mode not in {"excel", "google_sheets", "both"}:
        raise RuntimeFileError(f"Unsupported scraper output mode: {output_mode!r}.")

    needs_google = needs_evaluation or output_mode in {"google_sheets", "both"}
    pdf_output = settings.get("JOB_EVAL_CV_PDF_OUTPUT", "true").strip().lower()
    if pdf_output not in {"true", "false"}:
        raise RuntimeFileError("JOB_EVAL_CV_PDF_OUTPUT must be true or false.")
    needs_pdf = needs_evaluation and pdf_output == "true"

    try:
        apify_tokens = parse_apify_api_tokens(settings.get("APIFY_API_TOKEN"))
    except RuntimeError as exc:
        raise RuntimeFileError(str(exc)) from exc
    if not apify_tokens:
        raise RuntimeFileError("Missing required setting: APIFY_API_TOKEN.")

    keywords = settings.get("JOB_KEYWORDS_TEXT")
    if not keywords:
        raise RuntimeFileError("Missing required setting: JOB_KEYWORDS_TEXT.")

    if needs_evaluation and not settings.get("OPENAI_API_KEY"):
        raise RuntimeFileError("Missing required setting: OPENAI_API_KEY.")
    if needs_evaluation and not settings.get("MASTER_PROMPT_TEXT"):
        raise RuntimeFileError("Missing required setting: MASTER_PROMPT_TEXT.")
    if needs_evaluation and not settings.get("MASTER_CV_TEX"):
        raise RuntimeFileError("Missing required setting: MASTER_CV_TEX.")
    if needs_pdf and not settings.get(finder_product.cv_drive_folder_id_env):
        raise RuntimeFileError(
            f"Missing required setting: {finder_product.cv_drive_folder_id_env}."
        )

    photo_bytes: bytes | None = None
    photo_base64 = "".join(settings.get("CV_PHOTO_BASE64").split())
    if photo_base64 and needs_pdf:
        try:
            photo_bytes = base64.b64decode(photo_base64, validate=True)
        except binascii.Error as exc:
            raise RuntimeFileError(
                f"CV_PHOTO_BASE64 is not valid base64: {exc}"
            ) from exc

    validated_token = ""
    spreadsheet_id = ""
    if needs_google:
        token_json = settings.get("GOOGLE_TOKEN_JSON") or settings.get(
            "GOOGLE_DRIVE_TOKEN_JSON"
        )
        if not token_json:
            raise RuntimeFileError("Missing required setting: GOOGLE_TOKEN_JSON.")
        spreadsheet_id = settings.get(finder_product.spreadsheet_id_env)
        if not spreadsheet_id:
            raise RuntimeFileError(
                f"Missing required setting: {finder_product.spreadsheet_id_env}."
            )
        validated_token = _validated_google_token(token_json)

    written: list[Path] = []
    _write_private(finder_product.keywords_file, keywords, written)
    if needs_evaluation:
        _write_private(
            finder_product.master_prompt_file,
            settings.get("MASTER_PROMPT_TEXT"),
            written,
        )
        _write_private(
            finder_product.cv_file,
            settings.get("MASTER_CV_TEX"),
            written,
        )

    if photo_bytes is not None:
        finder_product.cv_photo_file.parent.mkdir(parents=True, exist_ok=True)
        finder_product.cv_photo_file.write_bytes(photo_bytes)
        finder_product.cv_photo_file.chmod(0o600)
        written.append(finder_product.cv_photo_file)

    if needs_google:
        _write_private(token_file, validated_token, written)
        _write_private(finder_product.spreadsheet_id_file, spreadsheet_id, written)

    manifest_path = finder_product.product_dir / MANIFEST_NAME
    manifest_path.write_text(
        json.dumps([str(path) for path in written], indent=2) + "\n",
        encoding="utf-8",
    )
    manifest_path.chmod(0o600)

    return RuntimePreparation(
        product=finder_product.slug,
        files=tuple(str(path) for path in written),
        needs_google=needs_google,
        needs_evaluation=needs_evaluation,
        needs_pdf=needs_pdf,
    )


def cleanup_runtime_files(
    env: EnvSettings | None = None,
    product: FinderProduct | None = None,
    *,
    require_ci: bool = True,
    token_file: Path = GOOGLE_TOKEN_FILE,
) -> tuple[Path, ...]:
    """Remove only files recorded by the matching preparation manifest."""
    settings = env or EnvSettings()
    _require_ci(settings, require_ci)
    finder_product = product or product_from_env(settings)
    manifest_path = finder_product.product_dir / MANIFEST_NAME
    if not manifest_path.exists():
        return ()

    try:
        raw_paths = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeFileError(f"Cannot read {manifest_path}: {exc}") from exc
    if not isinstance(raw_paths, list):
        raise RuntimeFileError(f"Invalid runtime-file manifest: {manifest_path}.")

    removed: list[Path] = []
    allowed_paths = {
        finder_product.keywords_file.resolve(),
        finder_product.master_prompt_file.resolve(),
        finder_product.cv_file.resolve(),
        finder_product.cv_photo_file.resolve(),
        finder_product.spreadsheet_id_file.resolve(),
        token_file.resolve(),
    }
    for raw_path in raw_paths:
        path = Path(str(raw_path)).resolve()
        if path not in allowed_paths:
            raise RuntimeFileError(f"Refusing to remove unexpected path: {path}.")
        if path.exists():
            path.unlink()
            removed.append(path)
    manifest_path.unlink(missing_ok=True)
    return tuple(removed)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "cleanup"))
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    if args.command == "prepare":
        result = prepare_runtime_files()
        print(json.dumps(asdict(result), indent=2))
    else:
        removed = cleanup_runtime_files()
        print(f"Removed {len(removed)} private runtime file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
