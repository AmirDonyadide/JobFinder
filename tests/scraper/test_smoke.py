"""Tests for the live actor smoke-test payloads without making network calls."""

from __future__ import annotations

from jobfinder.env import EnvSettings
from jobfinder.scraper.smoke import build_payload, build_smoke_settings


def settings():
    """Return secrets-safe settings for smoke payload unit tests."""
    return build_smoke_settings(
        keyword="GIS",
        location="Germany",
        max_items=10,
        max_pages=2,
        env=EnvSettings({"APIFY_API_TOKEN": "apify_api_test_placeholder"}),
    )


def test_linkedin_smoke_payload_is_schema_compatible():
    payload = build_payload("linkedin", settings(), "GIS")
    assert set(payload) == {"urls", "count", "scrapeCompany", "splitByLocation"}
    assert payload["count"] == 10


def test_indeed_smoke_payload_is_schema_compatible():
    payload = build_payload("indeed", settings(), "GIS")
    assert payload == {
        "country": "de",
        "title": "GIS",
        "location": "Germany",
        "limit": 10,
        "datePosted": "7",
    }


def test_stepstone_smoke_payload_is_schema_compatible():
    payload = build_payload("stepstone", settings(), "GIS")
    assert payload["keyword"] == "GIS"
    assert payload["location"] == "deutschland"
    assert payload["maxItems"] == 10
    assert payload["proxy"]["apifyProxyGroups"] == ["RESIDENTIAL"]


def test_xing_smoke_payload_uses_only_deployed_schema_fields():
    payload = build_payload("xing", settings(), "GIS")
    assert payload == {
        "keyword": "GIS",
        "location": "Germany",
        "date_posted": "LAST_WEEK",
        "results_wanted": 10,
        "max_pages": 2,
    }
