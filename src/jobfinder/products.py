"""Product definitions for JobFinder and PhDFinder."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jobfinder.env import EnvSettings
from jobfinder.paths import (
    DEFAULT_CV_FILE,
    DEFAULT_CV_PHOTO_FILE,
    DEFAULT_EXCEL_FILE,
    DEFAULT_MASTER_PROMPT_FILE,
    FILTERS_FILE,
    GOOGLE_SPREADSHEET_ID_FILE,
    KEYWORDS_FILE,
    PRODUCTS_DIR,
)

PRODUCT_ENV = "JOBFINDER_PRODUCT"
LEGACY_PRODUCT_ENV = "JOBFINDER_PROFILE"
DEFAULT_PRODUCT = "jobs"


class FinderProductError(ValueError):
    """Raised when a finder product name is unknown."""


@dataclass(frozen=True)
class FinderProduct:
    """Paths, labels, and isolated runtime settings for one product."""

    key: str
    slug: str
    display_name: str
    spreadsheet_title: str
    cv_language: str
    product_dir: Path
    keywords_file: Path
    filters_file: Path
    master_prompt_file: Path
    cv_file: Path
    cv_photo_file: Path
    excel_output_file: Path
    spreadsheet_id_file: Path
    spreadsheet_id_env: str
    cv_drive_folder_id_env: str


JOBFINDER_PRODUCT_DIR = PRODUCTS_DIR / "jobfinder"
PHDFINDER_PRODUCT_DIR = PRODUCTS_DIR / "phdfinder"

PRODUCTS: dict[str, FinderProduct] = {
    "jobs": FinderProduct(
        key="jobs",
        slug="jobfinder",
        display_name="JobFinder",
        spreadsheet_title="jobs",
        cv_language="German",
        product_dir=JOBFINDER_PRODUCT_DIR,
        keywords_file=KEYWORDS_FILE,
        filters_file=FILTERS_FILE,
        master_prompt_file=DEFAULT_MASTER_PROMPT_FILE,
        cv_file=DEFAULT_CV_FILE,
        cv_photo_file=DEFAULT_CV_PHOTO_FILE,
        excel_output_file=DEFAULT_EXCEL_FILE,
        spreadsheet_id_file=GOOGLE_SPREADSHEET_ID_FILE,
        spreadsheet_id_env="GOOGLE_SPREADSHEET_ID",
        cv_drive_folder_id_env="JOB_EVAL_CV_DRIVE_FOLDER_ID",
    ),
    "phd": FinderProduct(
        key="phd",
        slug="phdfinder",
        display_name="PhDFinder",
        spreadsheet_title="PhDFinder",
        cv_language="English",
        product_dir=PHDFINDER_PRODUCT_DIR,
        keywords_file=PHDFINDER_PRODUCT_DIR / "config" / "keywords.txt",
        filters_file=PHDFINDER_PRODUCT_DIR / "config" / "filters.json",
        master_prompt_file=(PHDFINDER_PRODUCT_DIR / "evaluator" / "master_prompt.txt"),
        cv_file=PHDFINDER_PRODUCT_DIR / "evaluator" / "master_cv.tex",
        cv_photo_file=PHDFINDER_PRODUCT_DIR / "evaluator" / "photo.png",
        excel_output_file=PRODUCTS_DIR.parent / "phd_jobs.xlsx",
        spreadsheet_id_file=PHDFINDER_PRODUCT_DIR / "google_spreadsheet_id.txt",
        spreadsheet_id_env="PHDFINDER_GOOGLE_SPREADSHEET_ID",
        cv_drive_folder_id_env="PHDFINDER_CV_DRIVE_FOLDER_ID",
    ),
}

PRODUCT_ALIASES = {
    "default": "jobs",
    "job": "jobs",
    "jobfinder": "jobs",
    "jobs": "jobs",
    "academic": "phd",
    "phd": "phd",
    "phd-finder": "phd",
    "phd_finder": "phd",
    "phdfinder": "phd",
}


def resolve_product(value: str | FinderProduct | None = None) -> FinderProduct:
    """Resolve a canonical product from a user-facing name or alias."""
    if isinstance(value, FinderProduct):
        return value

    normalized = (value or DEFAULT_PRODUCT).strip().casefold()
    key = PRODUCT_ALIASES.get(normalized)
    if key is not None:
        return PRODUCTS[key]

    allowed = ", ".join(sorted(PRODUCTS))
    raise FinderProductError(
        f"Unknown {PRODUCT_ENV} value {value!r}. Use one of: {allowed}."
    )


def product_from_env(
    env: EnvSettings,
    override: str | FinderProduct | None = None,
) -> FinderProduct:
    """Resolve a product from an explicit override, environment, or default."""
    selected = override
    if selected is None:
        selected = env.get(PRODUCT_ENV) or env.get(LEGACY_PRODUCT_ENV)
    return resolve_product(selected)


def product_spreadsheet_id(
    env: EnvSettings,
    product: str | FinderProduct | None = None,
    *,
    explicit: str = "",
) -> str:
    """Resolve a spreadsheet ID without crossing product state boundaries."""
    if explicit.strip():
        return explicit.strip()

    finder_product = product_from_env(env, product)
    env_value = env.get(finder_product.spreadsheet_id_env)
    if env_value:
        return env_value
    if finder_product.spreadsheet_id_file.exists():
        return finder_product.spreadsheet_id_file.read_text(encoding="utf-8").strip()
    return ""


def product_cv_drive_folder_id(
    env: EnvSettings,
    product: str | FinderProduct | None = None,
) -> str:
    """Resolve the generated-CV Drive folder for one product."""
    finder_product = product_from_env(env, product)
    return env.get(finder_product.cv_drive_folder_id_env)
