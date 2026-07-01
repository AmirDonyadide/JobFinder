"""LinkedIn provider integration for ``curious_coder/linkedin-jobs-scraper``."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from jobfinder.scraper.settings import ScraperSettings

LINKEDIN_MIN_COUNT = 10


def build_search_url(settings: ScraperSettings, keyword: str) -> str:
    """Build a LinkedIn job-search URL for one keyword."""
    params = {
        "keywords": keyword,
        "position": "1",
        "pageNum": "0",
    }
    if settings.location:
        params["location"] = settings.location
    if settings.geo_id:
        params["geoId"] = settings.geo_id
    if settings.experience_levels:
        params["f_E"] = ",".join(settings.experience_levels)
    if settings.contract_types:
        params["f_JT"] = ",".join(settings.contract_types)
    posted_window = getattr(settings, "provider_posted_window", settings.published_at)
    if posted_window:
        params["f_TPR"] = posted_window

    return f"https://www.linkedin.com/jobs/search/?{urlencode(params)}"


def build_actor_input(settings: ScraperSettings, search_url: str) -> dict[str, Any]:
    """Build the Apify actor payload for LinkedIn searches."""
    payload = {
        "urls": [search_url],
        "count": max(LINKEDIN_MIN_COUNT, settings.max_results_per_search),
        "scrapeCompany": settings.scrape_company_details,
        "splitByLocation": settings.split_by_location,
    }
    if settings.split_by_location:
        payload["splitCountry"] = settings.split_country
    return payload


def build_batch_actor_input(
    settings: ScraperSettings, search_urls: list[str]
) -> dict[str, Any]:
    """Build a LinkedIn actor payload containing multiple search URLs."""
    payload = build_actor_input(settings, search_urls[0])
    payload["urls"] = search_urls
    payload["count"] = max(
        LINKEDIN_MIN_COUNT,
        settings.max_results_per_search * len(search_urls),
    )
    return payload


__all__ = [
    "build_actor_input",
    "build_batch_actor_input",
    "build_search_url",
]
