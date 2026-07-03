"""Tests for keyword uniqueness diagnostics."""

from __future__ import annotations

import logging

from jobfinder.scraper.keyword_uniqueness import (
    KeywordSearchResult,
    build_keyword_uniqueness_summary,
    log_keyword_uniqueness_summary,
)


def row_by_provider_keyword(rows):
    """Return summary rows keyed by provider and keyword."""
    return {(row.provider, row.keyword): row for row in rows}


def test_keyword_uniqueness_summary_is_per_platform_and_includes_zero_results():
    """A duplicate on one platform should not affect another platform's keywords."""
    rows = build_keyword_uniqueness_summary(
        [
            KeywordSearchResult(
                provider="linkedin",
                provider_label="LinkedIn",
                keyword="geodaten",
                jobs=[
                    {
                        "title": "GIS Analyst",
                        "companyName": "GeoCo GmbH",
                        "location": "Berlin, Germany",
                    },
                    {
                        "title": "Remote Sensing Specialist",
                        "companyName": "MapCo",
                        "location": "Hamburg, Germany",
                    },
                ],
            ),
            KeywordSearchResult(
                provider="linkedin",
                provider_label="LinkedIn",
                keyword="gis",
                jobs=[
                    {
                        "title": "GIS Analyst (m/f/d)",
                        "companyName": "GeoCo",
                        "location": "Berlin",
                    },
                    {
                        "title": "GIS Developer",
                        "companyName": "BuildMaps",
                        "location": "Munich, Germany",
                    },
                ],
            ),
            KeywordSearchResult(
                provider="indeed",
                provider_label="Indeed",
                keyword="geodaten",
                jobs=[
                    {
                        "title": "GIS Analyst",
                        "companyName": "GeoCo GmbH",
                        "location": "Berlin, Germany",
                    }
                ],
            ),
            KeywordSearchResult(
                provider="xing",
                provider_label="Xing",
                keyword="gis",
                jobs=[],
            ),
        ]
    )

    by_key = row_by_provider_keyword(rows)

    assert by_key[("linkedin", "geodaten")].total_jobs == 2
    assert by_key[("linkedin", "geodaten")].duplicated_with_other_keywords == 1
    assert by_key[("linkedin", "geodaten")].unique_only_to_keyword == 1
    assert by_key[("linkedin", "geodaten")].unique_percentage == 50.0

    assert by_key[("linkedin", "gis")].total_jobs == 2
    assert by_key[("linkedin", "gis")].duplicated_with_other_keywords == 1
    assert by_key[("linkedin", "gis")].unique_only_to_keyword == 1
    assert by_key[("linkedin", "gis")].unique_percentage == 50.0

    assert by_key[("indeed", "geodaten")].total_jobs == 1
    assert by_key[("indeed", "geodaten")].duplicated_with_other_keywords == 0
    assert by_key[("indeed", "geodaten")].unique_only_to_keyword == 1

    assert by_key[("xing", "gis")].total_jobs == 0
    assert by_key[("xing", "gis")].duplicated_with_other_keywords == 0
    assert by_key[("xing", "gis")].unique_only_to_keyword == 0
    assert by_key[("xing", "gis")].unique_percentage == 0.0


def test_keyword_uniqueness_summary_handles_missing_fields():
    """Missing job identity fields should not break the diagnostic summary."""
    rows = build_keyword_uniqueness_summary(
        [
            KeywordSearchResult(
                provider="stepstone",
                provider_label="Stepstone",
                keyword="gis",
                jobs=[{}],
            ),
            KeywordSearchResult(
                provider="stepstone",
                provider_label="Stepstone",
                keyword="geodaten",
                jobs=[{"title": "N/A", "companyName": "", "location": None}],
            ),
        ]
    )

    by_key = row_by_provider_keyword(rows)

    assert by_key[("stepstone", "gis")].total_jobs == 1
    assert by_key[("stepstone", "gis")].duplicated_with_other_keywords == 0
    assert by_key[("stepstone", "gis")].unique_only_to_keyword == 1
    assert by_key[("stepstone", "geodaten")].total_jobs == 1
    assert by_key[("stepstone", "geodaten")].duplicated_with_other_keywords == 0
    assert by_key[("stepstone", "geodaten")].unique_only_to_keyword == 1


def test_keyword_uniqueness_summary_log_format(caplog):
    """The log should show the requested human-readable summary lines."""
    caplog.set_level(logging.INFO, logger="jobfinder.scraper")

    log_keyword_uniqueness_summary(
        [
            KeywordSearchResult(
                provider="linkedin",
                provider_label="LinkedIn",
                keyword="geodaten",
                jobs=[
                    {
                        "title": "GIS Analyst",
                        "companyName": "GeoCo",
                        "location": "Berlin",
                    }
                ],
            )
        ]
    )

    assert "Keyword uniqueness summary:" in caplog.text
    assert (
        "- LinkedIn / geodaten: 1 total, 0 duplicated with other keywords, "
        "1 unique only to this keyword (100.0% unique)"
    ) in caplog.text
