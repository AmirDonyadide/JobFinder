"""Finder profile definitions for shared JobFinder product workflows."""

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
    PROJECT_ROOT,
)

PROFILE_ENV = "JOBFINDER_PROFILE"
DEFAULT_PROFILE = "jobs"


class FinderProfileError(ValueError):
    """Raised when a finder profile name is unknown."""


@dataclass(frozen=True)
class FinderProfile:
    """Default files and product labels for one finder workflow."""

    key: str
    display_name: str
    spreadsheet_title: str
    keywords_file: Path
    filters_file: Path
    master_prompt_file: Path
    cv_file: Path
    cv_photo_file: Path
    excel_output_file: Path
    spreadsheet_id_file: Path
    spreadsheet_id_env: str
    cv_drive_folder_id_env: str


PHD_PROFILE_DIR = PROJECT_ROOT / "profiles" / "phd"

PROFILES: dict[str, FinderProfile] = {
    "jobs": FinderProfile(
        key="jobs",
        display_name="JobFinder",
        spreadsheet_title="jobs",
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
    "phd": FinderProfile(
        key="phd",
        display_name="PhDFinder",
        spreadsheet_title="PhDFinder",
        keywords_file=PHD_PROFILE_DIR / "keywords.txt",
        filters_file=PHD_PROFILE_DIR / "filters.json",
        master_prompt_file=PHD_PROFILE_DIR / "master_prompt.txt",
        cv_file=PHD_PROFILE_DIR / "master_cv.tex",
        cv_photo_file=PHD_PROFILE_DIR / "photo.png",
        excel_output_file=PROJECT_ROOT / "phd_jobs.xlsx",
        spreadsheet_id_file=PHD_PROFILE_DIR / "google_spreadsheet_id.txt",
        spreadsheet_id_env="PHDFINDER_GOOGLE_SPREADSHEET_ID",
        cv_drive_folder_id_env="PHDFINDER_CV_DRIVE_FOLDER_ID",
    ),
}

PROFILE_ALIASES = {
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


def resolve_profile(value: str | FinderProfile | None = None) -> FinderProfile:
    """Resolve a canonical finder profile from a user-facing name."""
    if isinstance(value, FinderProfile):
        return value

    normalized = (value or DEFAULT_PROFILE).strip().casefold()
    key = PROFILE_ALIASES.get(normalized)
    if key is not None:
        return PROFILES[key]

    allowed = ", ".join(sorted(PROFILES))
    raise FinderProfileError(
        f"Unknown {PROFILE_ENV} value {value!r}. Use one of: {allowed}."
    )


def profile_from_env(
    env: EnvSettings,
    override: str | FinderProfile | None = None,
) -> FinderProfile:
    """Resolve a profile from an explicit override, environment, or default."""
    selected = override if override is not None else env.get(PROFILE_ENV)
    return resolve_profile(selected)


def profile_spreadsheet_id(
    env: EnvSettings,
    profile: str | FinderProfile | None = None,
    *,
    explicit: str = "",
) -> str:
    """Resolve a spreadsheet ID without crossing profile state boundaries."""
    if explicit.strip():
        return explicit.strip()

    finder_profile = profile_from_env(env, profile)
    env_value = env.get(finder_profile.spreadsheet_id_env)
    if env_value:
        return env_value
    if finder_profile.spreadsheet_id_file.exists():
        return finder_profile.spreadsheet_id_file.read_text(encoding="utf-8").strip()
    return ""


def profile_cv_drive_folder_id(
    env: EnvSettings,
    profile: str | FinderProfile | None = None,
) -> str:
    """Resolve the CV Drive folder configured for one product profile."""
    finder_profile = profile_from_env(env, profile)
    return env.get(finder_profile.cv_drive_folder_id_env)
