"""Preflight validation for scheduled pipeline runs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from jobfinder.env import EnvSettings
from jobfinder.evaluator.cv_contract import validate_master_cv_structure
from jobfinder.evaluator.parsing import read_text_asset
from jobfinder.evaluator.storage import read_google_spreadsheet_id
from jobfinder.integrations.google.drive import (
    build_google_drive_service,
    get_drive_folder,
)
from jobfinder.products import (
    FinderProduct,
    product_cv_drive_folder_id,
    product_from_env,
)
from jobfinder.scraper.export_google_sheets import build_scraper_google_sheets_service
from jobfinder.scraper.run_history import load_google_spreadsheet_context
from jobfinder.scraper.settings import ScraperSettings, load_scraper_settings


@dataclass(frozen=True)
class PreflightResult:
    """Summary of pipeline readiness checks."""

    product: str
    source_mode: str
    output_mode: str
    keyword_count: int
    google_sheets_ready: bool
    evaluation_inputs_ready: bool

    @property
    def profile(self) -> str:
        """Return the historical field name for compatibility."""
        return self.product


def run_preflight(
    env: EnvSettings,
    *,
    should_evaluate: bool,
    profile: str | FinderProduct | None = None,
) -> PreflightResult:
    """Validate local config, dependencies, and Google Sheets access."""
    finder_profile = product_from_env(env, profile)
    settings = load_scraper_settings(env, profile=finder_profile)
    google_sheets_ready = validate_google_sheets(settings)

    evaluation_inputs_ready = False
    if should_evaluate:
        master_prompt_file = Path(
            env.get(
                "JOB_EVAL_MASTER_PROMPT_FILE",
                str(finder_profile.master_prompt_file),
            )
        )
        cv_file = Path(env.get("JOB_EVAL_CV_FILE", str(finder_profile.cv_file)))
        master_prompt = read_text_asset(master_prompt_file, "master prompt")
        master_cv = read_text_asset(cv_file, "LaTeX CV")
        if not re.search(r"\b20[\s-]*point", master_prompt, re.IGNORECASE):
            raise RuntimeError(
                "Master prompt is not the current 20-point evaluator version."
            )
        validate_master_cv_structure(master_cv)
        if not env.get("OPENAI_API_KEY"):
            raise RuntimeError("Missing OPENAI_API_KEY.")
        if env.get_bool("JOB_EVAL_CV_PDF_OUTPUT", True) and not (
            product_cv_drive_folder_id(env, finder_profile)
        ):
            raise RuntimeError(
                f"Missing {finder_profile.cv_drive_folder_id_env}. Set it to the ID "
                "of the Google Drive folder where generated CV PDFs should be "
                "uploaded, "
                "or set JOB_EVAL_CV_PDF_OUTPUT=false."
            )
        if env.get_bool("JOB_EVAL_CV_PDF_OUTPUT", True):
            validate_google_drive_folder(env, profile=finder_profile)
        read_google_spreadsheet_id(
            env.get("JOB_EVAL_GOOGLE_SPREADSHEET_ID"),
            env=env,
            profile=finder_profile,
        )
        evaluation_inputs_ready = True

    return PreflightResult(
        product=finder_profile.key,
        source_mode=settings.source_mode,
        output_mode=settings.output_mode,
        keyword_count=len(settings.keywords),
        google_sheets_ready=google_sheets_ready,
        evaluation_inputs_ready=evaluation_inputs_ready,
    )


def validate_google_sheets(settings: ScraperSettings) -> bool:
    """Validate Google Sheets credentials and spreadsheet access."""
    service = build_scraper_google_sheets_service()
    load_google_spreadsheet_context(settings, service, seed_seen_jobs_index=False)
    return True


def validate_google_drive_folder(
    env: EnvSettings,
    *,
    profile: str | FinderProduct | None = None,
) -> bool:
    """Validate Google Drive credentials and configured PDF folder access."""
    folder_id = product_cv_drive_folder_id(env, profile)
    service = build_google_drive_service(error_cls=RuntimeError)
    get_drive_folder(service, folder_id)
    return True
