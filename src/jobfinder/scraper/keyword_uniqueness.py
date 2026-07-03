"""Keyword-level uniqueness diagnostics for scraper search results."""

from __future__ import annotations

import logging
from collections import OrderedDict
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from jobfinder.dedupe.matching import deduplicate_search_results

LOGGER = logging.getLogger("jobfinder.scraper")


@dataclass(frozen=True)
class KeywordSearchResult:
    """Jobs collected for one provider/keyword search."""

    provider: str
    provider_label: str
    keyword: str
    jobs: list[dict[str, Any]]


@dataclass(frozen=True)
class KeywordUniquenessRow:
    """Uniqueness counts for one keyword inside one provider."""

    provider: str
    provider_label: str
    keyword: str
    total_jobs: int
    duplicated_with_other_keywords: int
    unique_only_to_keyword: int
    unique_percentage: float


@dataclass
class _MutableKeywordStats:
    """Mutable accumulator for one provider/keyword pair."""

    provider: str
    provider_label: str
    keyword: str
    total_jobs: int = 0
    duplicated_with_other_keywords: int = 0

    def as_row(self) -> KeywordUniquenessRow:
        """Return the immutable public summary row."""
        unique_only = max(
            0,
            self.total_jobs - self.duplicated_with_other_keywords,
        )
        unique_percentage = (
            (unique_only / self.total_jobs) * 100 if self.total_jobs else 0.0
        )
        return KeywordUniquenessRow(
            provider=self.provider,
            provider_label=self.provider_label,
            keyword=self.keyword,
            total_jobs=self.total_jobs,
            duplicated_with_other_keywords=self.duplicated_with_other_keywords,
            unique_only_to_keyword=unique_only,
            unique_percentage=unique_percentage,
        )


def keyword_key(keyword: str) -> str:
    """Return a stable comparison key for a searched keyword."""
    return " ".join(str(keyword or "").split()).casefold()


def keyword_label(keyword: str) -> str:
    """Return a log-safe keyword label."""
    return " ".join(str(keyword or "").split()) or "(missing keyword)"


def _prepared_job(
    job: Any,
    *,
    provider: str,
    provider_label: str,
) -> dict[str, Any]:
    """Return a dedupe-safe copy of a scraped job."""
    prepared = dict(job) if isinstance(job, dict) else {"rawItem": job}
    prepared.setdefault("_source", provider)
    prepared.setdefault("_source_label", provider_label)
    return prepared


def _group_by_provider(
    search_results: Iterable[KeywordSearchResult],
) -> OrderedDict[str, list[KeywordSearchResult]]:
    """Group search results by provider while preserving search order."""
    by_provider: OrderedDict[str, list[KeywordSearchResult]] = OrderedDict()
    for result in search_results:
        by_provider.setdefault(result.provider, []).append(result)
    return by_provider


def build_keyword_uniqueness_summary(
    search_results: Iterable[KeywordSearchResult],
) -> list[KeywordUniquenessRow]:
    """Build per-provider keyword uniqueness rows before global deduplication."""
    rows: list[KeywordUniquenessRow] = []

    for provider, provider_results in _group_by_provider(search_results).items():
        stats: OrderedDict[str, _MutableKeywordStats] = OrderedDict()
        dedupe_input: list[tuple[str, list[dict[str, Any]]]] = []
        index_to_keyword_key: dict[int, str] = {}
        next_job_index = 0

        for result in provider_results:
            provider_label = result.provider_label or provider
            display_keyword = keyword_label(result.keyword)
            key = keyword_key(display_keyword)
            if key not in stats:
                stats[key] = _MutableKeywordStats(
                    provider=provider,
                    provider_label=provider_label,
                    keyword=display_keyword,
                )

            prepared_jobs = [
                _prepared_job(
                    job,
                    provider=provider,
                    provider_label=provider_label,
                )
                for job in result.jobs
            ]
            stats[key].total_jobs += len(prepared_jobs)
            for _ in prepared_jobs:
                index_to_keyword_key[next_job_index] = key
                next_job_index += 1
            dedupe_input.append((display_keyword, prepared_jobs))

        if next_job_index:
            dedupe_result = deduplicate_search_results(dedupe_input)
            for cluster in dedupe_result.clusters:
                cluster_keyword_keys = {
                    index_to_keyword_key[job.index]
                    for job in cluster
                    if job.index in index_to_keyword_key
                }
                if len(cluster_keyword_keys) <= 1:
                    continue
                for job in cluster:
                    current_key = index_to_keyword_key.get(job.index)
                    if current_key in cluster_keyword_keys and current_key in stats:
                        stats[current_key].duplicated_with_other_keywords += 1

        rows.extend(stat.as_row() for stat in stats.values())

    return rows


def log_keyword_uniqueness_summary(
    search_results: Iterable[KeywordSearchResult],
    *,
    logger: logging.Logger = LOGGER,
) -> None:
    """Log the per-platform keyword uniqueness summary."""
    rows = build_keyword_uniqueness_summary(search_results)
    if not rows:
        logger.info("Keyword uniqueness summary: no completed searches.")
        return

    logger.info("Keyword uniqueness summary:")
    for row in rows:
        logger.info(
            "- %s / %s: %s total, %s duplicated with other keywords, "
            "%s unique only to this keyword (%.1f%% unique)",
            row.provider_label,
            row.keyword,
            row.total_jobs,
            row.duplicated_with_other_keywords,
            row.unique_only_to_keyword,
            row.unique_percentage,
        )
