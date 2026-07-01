"""Live, secrets-safe smoke tests for individual Apify job actors."""

from __future__ import annotations

import argparse
import logging
from types import SimpleNamespace
from typing import Any

from jobfinder.core.logging import configure_cli_logging
from jobfinder.env import EnvSettings
from jobfinder.providers import indeed, linkedin, stepstone, xing
from jobfinder.providers.apify_client import json_for_log, run_actor
from jobfinder.scraper.normalize import get_job_url, get_title
from jobfinder.scraper.settings import (
    APIFY_API_TOKEN_ENV,
    INDEED_ACTOR_ID,
    LINKEDIN_ACTOR_ID,
    STEPSTONE_ACTOR_ID,
    XING_ACTOR_ID,
    ApifyTokenPool,
    parse_apify_api_tokens,
)

LOGGER = logging.getLogger("jobfinder.scraper")
ACTOR_IDS = {
    "linkedin": LINKEDIN_ACTOR_ID,
    "indeed": INDEED_ACTOR_ID,
    "stepstone": STEPSTONE_ACTOR_ID,
    "xing": XING_ACTOR_ID,
}


def build_smoke_settings(
    *,
    keyword: str,
    location: str,
    max_items: int,
    max_pages: int,
    env: EnvSettings | None = None,
) -> SimpleNamespace:
    """Build the minimal settings object needed by all provider adapters."""
    env = env or EnvSettings()
    tokens = parse_apify_api_tokens(env.get(APIFY_API_TOKEN_ENV))
    if not tokens:
        raise RuntimeError(
            f"Set {APIFY_API_TOKEN_ENV} in .env or the environment before running "
            "a live scraper smoke test."
        )

    configured_memory = env.get_int("APIFY_RUN_MEMORY_MB", 0)
    memory_mb = max(128, configured_memory) if configured_memory > 0 else 0
    return SimpleNamespace(
        apify_api_token=tokens[0],
        apify_api_tokens=tokens,
        apify_token_pool=ApifyTokenPool(tokens),
        apify_run_timeout_seconds=max(
            60,
            env.get_int("APIFY_RUN_TIMEOUT_SECONDS", 900),
        ),
        apify_run_memory_mb=memory_mb,
        apify_client_timeout_seconds=max(
            1,
            env.get_int("APIFY_CLIENT_TIMEOUT_SECONDS", 120),
        ),
        location=location,
        geo_id="101282230" if location.casefold() in {"germany", "deutschland"} else "",
        experience_levels=[],
        contract_types=[],
        published_at="r604800",
        max_results_per_search=max_items,
        scrape_company_details=False,
        split_by_location=False,
        split_country="DE",
        indeed_country="DE",
        indeed_location=location,
        indeed_max_results_per_search=max_items,
        stepstone_location=location,
        stepstone_category="",
        stepstone_start_urls=[],
        stepstone_max_results_per_search=max_items,
        stepstone_max_concurrency=min(5, max_items),
        stepstone_min_concurrency=1,
        stepstone_max_request_retries=3,
        stepstone_use_apify_proxy=True,
        stepstone_proxy_groups=["RESIDENTIAL"],
        xing_location=location,
        xing_date_posted="LAST_WEEK",
        xing_start_url="",
        xing_max_results_per_search=max_items,
        xing_max_pages=max_pages,
    )


def build_payload(
    platform: str,
    settings: SimpleNamespace,
    keyword: str,
) -> dict[str, Any]:
    """Build one live actor payload without invoking pipeline filters."""
    if platform == "linkedin":
        url = linkedin.build_search_url(settings, keyword)
        return linkedin.build_actor_input(settings, url)
    if platform == "indeed":
        return indeed.build_actor_input(settings, keyword)
    if platform == "stepstone":
        return stepstone.build_actor_input(settings, keyword)
    if platform == "xing":
        return xing.build_actor_input(settings, keyword)
    raise ValueError(f"Unknown platform: {platform}")


def normalize_results(
    platform: str,
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Run only the provider parser, without dedupe or business filters."""
    if platform == "indeed":
        return indeed.normalize_actor_output(items)
    if platform == "stepstone":
        return stepstone.normalize_actor_output(items)
    if platform == "xing":
        return xing.normalize_actor_output(items)
    return items


def build_arg_parser(platform: str) -> argparse.ArgumentParser:
    """Build arguments shared by the four platform smoke scripts."""
    parser = argparse.ArgumentParser(
        description=(
            f"Run a live {platform.title()} Apify actor test and show raw results "
            "before pipeline filtering."
        )
    )
    parser.add_argument("--keyword", default="GIS")
    parser.add_argument("--location", default="Germany")
    parser.add_argument("--max-items", type=int, default=10)
    parser.add_argument("--max-pages", type=int, default=2)
    parser.add_argument("--sample-size", type=int, default=2)
    parser.add_argument(
        "--raw-only",
        action="store_true",
        help="Skip provider parsing after printing raw actor rows.",
    )
    return parser


def main(platform: str, argv: list[str] | None = None) -> int:
    """Run one platform actor and report whether usable raw jobs were returned."""
    configure_cli_logging()
    args = build_arg_parser(platform).parse_args(argv)
    max_items = max(1, args.max_items)
    max_pages = max(1, args.max_pages)

    try:
        settings = build_smoke_settings(
            keyword=args.keyword,
            location=args.location,
            max_items=max_items,
            max_pages=max_pages,
        )
        actor_id = ACTOR_IDS[platform]
        payload = build_payload(platform, settings, args.keyword)
        LOGGER.info("Smoke test actor: %s", actor_id)
        LOGGER.info("Smoke test input: %s", json_for_log(payload))
        raw_items = run_actor(settings, actor_id, payload, max_items)
    except Exception as exc:
        LOGGER.error("%s smoke test failed: %s", platform.title(), exc)
        return 1

    LOGGER.info("Raw Apify dataset items: %s", len(raw_items))
    for index, item in enumerate(raw_items[: max(0, args.sample_size)]):
        LOGGER.info("Raw item %s: %s", index + 1, json_for_log(item))

    if not raw_items:
        LOGGER.error(
            "%s actor completed but returned zero raw items. Review the run id, "
            "actor logs, and input printed above.",
            platform.title(),
        )
        return 2
    if args.raw_only:
        return 0

    parsed_items = normalize_results(platform, raw_items)
    invalid_items = [
        item
        for item in parsed_items
        if get_title(item) == "N/A" or get_job_url(settings, item) == "N/A"
    ]
    LOGGER.info(
        "Provider parser produced %s job(s); %s lacked a title or job URL.",
        len(parsed_items),
        len(invalid_items),
    )
    return 0 if parsed_items and not invalid_items else 3


__all__ = [
    "ACTOR_IDS",
    "build_payload",
    "build_smoke_settings",
    "main",
    "normalize_results",
]
