"""Command-line entry point for scraping and exporting jobs."""

from __future__ import annotations

import argparse
import logging
import sys

from jobfinder.core.logging import configure_cli_logging
from jobfinder.operations.reports import write_report_from_env
from jobfinder.scraper.export_google_sheets import GoogleSheetsExportError
from jobfinder.scraper.service import (
    ScraperServiceError,
    format_duration,
    parse_output_mode,
    run_scrape,
    sort_key,
)
from jobfinder.scraper.settings import (
    APIFY_API_TOKEN_ENV,
    TOKEN_PLACEHOLDER,
    load_scraper_settings,
)

LOGGER = logging.getLogger("jobfinder.scraper")

__all__ = [
    "build_arg_parser",
    "configure_logging",
    "format_duration",
    "main",
    "parse_output_mode",
    "sort_key",
]


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the scraper CLI argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Scrape jobs through Apify and export them to Excel or Google Sheets."
        )
    )
    parser.add_argument(
        "--product",
        "--profile",
        dest="profile",
        choices=("jobs", "phd"),
        help="Select JobFinder or PhDFinder; --profile is a compatibility alias.",
    )
    return parser


def configure_logging() -> None:
    """Configure scraper logging for CLI output."""
    configure_cli_logging()


def main() -> int:
    """Run the scraper CLI using resolved local settings."""
    configure_logging()
    args = build_arg_parser().parse_args()
    try:
        settings = load_scraper_settings(profile=args.profile)
    except RuntimeError as exc:
        LOGGER.error("%s", exc)
        write_report_from_env(
            "JOBFINDER_SCRAPER_REPORT_FILE",
            "failed",
            "configuration",
            {"error": str(exc)},
        )
        return 1

    if not settings.apify_api_tokens:
        LOGGER.error(
            "Please set %s in %s or as an environment variable.",
            APIFY_API_TOKEN_ENV,
            settings.token_file.name,
        )
        LOGGER.info("Example: %s=%s", APIFY_API_TOKEN_ENV, TOKEN_PLACEHOLDER)
        write_report_from_env(
            "JOBFINDER_SCRAPER_REPORT_FILE",
            "failed",
            "configuration",
            {"error": f"Missing required setting: {APIFY_API_TOKEN_ENV}"},
        )
        return 1

    try:
        result = run_scrape(settings)
    except (GoogleSheetsExportError, ScraperServiceError) as exc:
        LOGGER.error("%s", exc)
        write_report_from_env(
            "JOBFINDER_SCRAPER_REPORT_FILE",
            "failed",
            "runtime",
            {"error": str(exc)},
        )
        return 1
    write_report_from_env(
        "JOBFINDER_SCRAPER_REPORT_FILE", "succeeded", "scrape", result
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
