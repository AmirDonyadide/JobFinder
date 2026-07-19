"""Tests for shared JobFinder and PhDFinder profile resolution."""

from __future__ import annotations

import re
from dataclasses import replace

import pytest

from jobfinder.env import EnvSettings
from jobfinder.evaluator.cv_contract import validate_master_cv_structure
from jobfinder.evaluator.storage import read_google_spreadsheet_id
from jobfinder.profiles import (
    FinderProfileError,
    profile_from_env,
    profile_spreadsheet_id,
    resolve_profile,
)


def test_default_profile_preserves_legacy_jobfinder_paths():
    profile = resolve_profile()

    assert profile.key == "jobs"
    assert profile.keywords_file.name == "keywords.txt"
    assert profile.keywords_file.parent.name == "configs"
    assert profile.excel_output_file.name == "jobs.xlsx"
    assert profile.spreadsheet_id_file.name == "google_spreadsheet_id.txt"


def test_phdfinder_aliases_resolve_to_isolated_profile_paths():
    profile = resolve_profile("phdfinder")

    assert profile.key == "phd"
    assert profile.display_name == "PhDFinder"
    assert profile.keywords_file.parent.name == "phd"
    assert profile.filters_file.name == "filters.json"
    assert profile.excel_output_file.name == "phd_jobs.xlsx"
    assert profile.spreadsheet_id_file.parent.name == "phd"


def test_profile_from_env_uses_explicit_override_before_environment(monkeypatch):
    monkeypatch.delenv("JOBFINDER_PROFILE", raising=False)
    env = EnvSettings({"JOBFINDER_PROFILE": "jobs"})

    assert profile_from_env(env, "phd").key == "phd"


def test_unknown_profile_fails_with_canonical_choices():
    with pytest.raises(FinderProfileError, match="jobs, phd"):
        resolve_profile("grants")


def test_spreadsheet_cache_lookup_uses_explicit_profile(tmp_path, monkeypatch):
    monkeypatch.delenv("GOOGLE_SPREADSHEET_ID", raising=False)
    profile = replace(
        resolve_profile("phd"),
        spreadsheet_id_file=tmp_path / "phd-sheet-id.txt",
    )
    profile.spreadsheet_id_file.write_text("phd-sheet-id", encoding="utf-8")

    assert (
        read_google_spreadsheet_id("", env=EnvSettings({}), profile=profile)
        == "phd-sheet-id"
    )


def test_phdfinder_does_not_reuse_jobfinder_spreadsheet_setting(tmp_path, monkeypatch):
    monkeypatch.setenv("GOOGLE_SPREADSHEET_ID", "jobfinder-sheet-id")
    monkeypatch.delenv("PHDFINDER_GOOGLE_SPREADSHEET_ID", raising=False)
    profile = replace(
        resolve_profile("phd"),
        spreadsheet_id_file=tmp_path / "missing-phd-sheet-id.txt",
    )

    assert profile_spreadsheet_id(EnvSettings({}), profile) == ""

    monkeypatch.setenv("PHDFINDER_GOOGLE_SPREADSHEET_ID", "phdfinder-sheet-id")
    assert profile_spreadsheet_id(EnvSettings({}), profile) == "phdfinder-sheet-id"


def test_phdfinder_example_assets_satisfy_preflight_contracts():
    profile = resolve_profile("phd")
    prompt = profile.master_prompt_file.with_name(
        "master_prompt.example.txt"
    ).read_text(encoding="utf-8")
    master_cv = profile.cv_file.with_name("master_cv.example.tex").read_text(
        encoding="utf-8"
    )

    assert re.search(r"\b20[\s-]*point", prompt, re.IGNORECASE)
    validate_master_cv_structure(master_cv)
