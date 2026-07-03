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
from jobfinder.paths import DEFAULT_CV_FILE, DEFAULT_MASTER_PROMPT_FILE
from jobfinder.scraper.export_google_sheets import build_scraper_google_sheets_service
from jobfinder.scraper.run_history import load_google_spreadsheet_context
from jobfinder.scraper.settings import ScraperSettings, load_scraper_settings


@dataclass(frozen=True)
class PreflightResult:
    """Summary of pipeline readiness checks."""

    source_mode: str
    output_mode: str
    keyword_count: int
    google_sheets_ready: bool
    evaluation_inputs_ready: bool


def run_preflight(env: EnvSettings, *, should_evaluate: bool) -> PreflightResult:
    """Validate local config, dependencies, and Google Sheets access."""
    settings = load_scraper_settings(env)
    google_sheets_ready = validate_google_sheets(settings)

    evaluation_inputs_ready = False
    if should_evaluate:
        master_prompt_file = Path(
            env.get("JOB_EVAL_MASTER_PROMPT_FILE", str(DEFAULT_MASTER_PROMPT_FILE))
        )
        cv_file = Path(env.get("JOB_EVAL_CV_FILE", str(DEFAULT_CV_FILE)))
        master_prompt = read_text_asset(master_prompt_file, "master prompt")
        master_cv = read_text_asset(cv_file, "LaTeX CV")
        if not re.search(r"\b20[\s-]*point", master_prompt, re.IGNORECASE):
            raise RuntimeError(
                "Master prompt is not the current 20-point evaluator version."
            )
        validate_master_cv_structure(master_cv)
        if not env.get("OPENAI_API_KEY"):
            raise RuntimeError("Missing OPENAI_API_KEY.")
        if env.get_bool("JOB_EVAL_CV_PDF_OUTPUT", True) and not env.get(
            "JOB_EVAL_CV_DRIVE_FOLDER_ID"
        ):
            raise RuntimeError(
                "Missing JOB_EVAL_CV_DRIVE_FOLDER_ID. Set it to the ID of the "
                "Google Drive folder where generated CV PDFs should be uploaded, "
                "or set JOB_EVAL_CV_PDF_OUTPUT=false."
            )
        if env.get_bool("JOB_EVAL_CV_PDF_OUTPUT", True):
            validate_google_drive_folder(env)
        read_google_spreadsheet_id(env.get("JOB_EVAL_GOOGLE_SPREADSHEET_ID"))
        evaluation_inputs_ready = True

    return PreflightResult(
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


def validate_google_drive_folder(env: EnvSettings) -> bool:
    """Validate Google Drive credentials and configured PDF folder access."""
    folder_id = env.get("JOB_EVAL_CV_DRIVE_FOLDER_ID")
    service = build_google_drive_service(error_cls=RuntimeError)
    get_drive_folder(service, folder_id)
    return True
