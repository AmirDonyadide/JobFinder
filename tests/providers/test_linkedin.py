"""Tests for the LinkedIn actor integration."""

from __future__ import annotations

from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

from jobfinder.providers.linkedin import build_actor_input, build_search_url


def make_settings(**overrides) -> SimpleNamespace:
    """Build the provider settings used by LinkedIn tests."""
    values = {
        "location": "Germany",
        "geo_id": "101282230",
        "experience_levels": ["1", "2"],
        "contract_types": ["F", "P", "I"],
        "published_at": "r86400",
        "max_results_per_search": 10,
        "scrape_company_details": False,
        "split_by_location": False,
        "split_country": "DE",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_build_search_url_uses_linkedin_public_search_parameters():
    """The generated URL should carry LinkedIn's supported public filters."""
    url = build_search_url(make_settings(), "GIS analyst")
    query = parse_qs(urlparse(url).query)

    assert query == {
        "keywords": ["GIS analyst"],
        "location": ["Germany"],
        "geoId": ["101282230"],
        "f_E": ["1,2"],
        "f_JT": ["F,P,I"],
        "position": ["1"],
        "pageNum": ["0"],
        "f_TPR": ["r86400"],
    }


def test_build_actor_input_matches_current_actor_schema():
    """Payloads should contain no stale fields absent from the live schema."""
    payload = build_actor_input(
        make_settings(),
        "https://www.linkedin.com/jobs/search/?keywords=GIS",
    )

    assert payload == {
        "urls": ["https://www.linkedin.com/jobs/search/?keywords=GIS"],
        "count": 10,
        "scrapeCompany": False,
        "splitByLocation": False,
    }
    assert "useIncognitoMode" not in payload


def test_build_actor_input_respects_actor_minimum_count():
    """The live actor rejects count values below ten."""
    payload = build_actor_input(make_settings(max_results_per_search=1), "search-url")
    assert payload["count"] == 10
