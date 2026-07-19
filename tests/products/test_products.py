"""Tests for shared JobFinder and PhDFinder product resolution."""

from __future__ import annotations

import re
from dataclasses import replace

import pytest

from jobfinder.env import EnvSettings
from jobfinder.evaluator.cv_contract import validate_master_cv_structure
from jobfinder.evaluator.storage import read_google_spreadsheet_id
from jobfinder.products import (
    FinderProductError,
    product_from_env,
    product_spreadsheet_id,
    resolve_product,
)
from jobfinder.profiles import resolve_profile


def test_default_product_uses_jobfinder_paths():
    product = resolve_product()

    assert product.key == "jobs"
    assert product.keywords_file.name == "keywords.txt"
    assert product.keywords_file.parent.name == "config"
    assert product.keywords_file.parents[1].name == "jobfinder"
    assert product.excel_output_file.name == "jobs.xlsx"
    assert product.spreadsheet_id_file.name == "google_spreadsheet_id.txt"


def test_legacy_profile_facade_resolves_the_same_product():
    assert resolve_profile("phdfinder") is resolve_product("phdfinder")


def test_phdfinder_aliases_resolve_to_isolated_product_paths():
    product = resolve_product("phdfinder")

    assert product.key == "phd"
    assert product.display_name == "PhDFinder"
    assert product.keywords_file.parent.name == "config"
    assert product.keywords_file.parents[1].name == "phdfinder"
    assert product.filters_file.name == "filters.json"
    assert product.excel_output_file.name == "phd_jobs.xlsx"
    assert product.spreadsheet_id_file.parent.name == "phdfinder"


def test_product_from_env_uses_explicit_override_before_environment(monkeypatch):
    monkeypatch.delenv("JOBFINDER_PRODUCT", raising=False)
    monkeypatch.delenv("JOBFINDER_PROFILE", raising=False)
    env = EnvSettings({"JOBFINDER_PRODUCT": "jobs", "JOBFINDER_PROFILE": "phd"})

    assert product_from_env(env, "phd").key == "phd"
    assert product_from_env(env).key == "jobs"


def test_product_from_env_accepts_legacy_profile_setting(monkeypatch):
    monkeypatch.delenv("JOBFINDER_PRODUCT", raising=False)
    monkeypatch.delenv("JOBFINDER_PROFILE", raising=False)

    assert product_from_env(EnvSettings({"JOBFINDER_PROFILE": "phd"})).key == "phd"


def test_unknown_product_fails_with_canonical_choices():
    with pytest.raises(FinderProductError, match="jobs, phd"):
        resolve_product("grants")


def test_spreadsheet_cache_lookup_uses_explicit_product(tmp_path, monkeypatch):
    monkeypatch.delenv("GOOGLE_SPREADSHEET_ID", raising=False)
    product = replace(
        resolve_product("phd"),
        spreadsheet_id_file=tmp_path / "phd-sheet-id.txt",
    )
    product.spreadsheet_id_file.write_text("phd-sheet-id", encoding="utf-8")

    assert (
        read_google_spreadsheet_id("", env=EnvSettings({}), profile=product)
        == "phd-sheet-id"
    )


def test_phdfinder_does_not_reuse_jobfinder_spreadsheet_setting(tmp_path, monkeypatch):
    monkeypatch.setenv("GOOGLE_SPREADSHEET_ID", "jobfinder-sheet-id")
    monkeypatch.delenv("PHDFINDER_GOOGLE_SPREADSHEET_ID", raising=False)
    product = replace(
        resolve_product("phd"),
        spreadsheet_id_file=tmp_path / "missing-phd-sheet-id.txt",
    )

    assert product_spreadsheet_id(EnvSettings({}), product) == ""

    monkeypatch.setenv("PHDFINDER_GOOGLE_SPREADSHEET_ID", "phdfinder-sheet-id")
    assert product_spreadsheet_id(EnvSettings({}), product) == "phdfinder-sheet-id"


def test_phdfinder_example_assets_satisfy_preflight_contracts():
    product = resolve_product("phd")
    prompt = product.master_prompt_file.with_name(
        "master_prompt.example.txt"
    ).read_text(encoding="utf-8")
    master_cv = product.cv_file.with_name("master_cv.example.tex").read_text(
        encoding="utf-8"
    )

    assert re.search(r"\b20[\s-]*point", prompt, re.IGNORECASE)
    validate_master_cv_structure(master_cv)
