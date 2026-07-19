"""Tests for shared CI runtime-file preparation."""

from __future__ import annotations

import base64
import json
from dataclasses import replace

import pytest

from jobfinder.env import EnvSettings
from jobfinder.operations.runtime_files import (
    RuntimeFileError,
    cleanup_runtime_files,
    prepare_runtime_files,
)
from jobfinder.products import resolve_product


def temporary_product(tmp_path):
    product_dir = tmp_path / "products" / "jobfinder"
    return replace(
        resolve_product("jobs"),
        product_dir=product_dir,
        keywords_file=product_dir / "config" / "keywords.txt",
        filters_file=product_dir / "config" / "filters.json",
        master_prompt_file=product_dir / "evaluator" / "master_prompt.txt",
        cv_file=product_dir / "evaluator" / "master_cv.tex",
        cv_photo_file=product_dir / "evaluator" / "photo.png",
        spreadsheet_id_file=product_dir / "google_spreadsheet_id.txt",
    )


def google_token_json(*, include_drive_scope: bool = True) -> str:
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    if include_drive_scope:
        scopes.append("https://www.googleapis.com/auth/drive")
    return json.dumps(
        {
            "type": "authorized_user",
            "client_id": "client-id",
            "client_secret": "client-secret",
            "refresh_token": "refresh-token",
            "scopes": scopes,
        }
    )


def complete_env() -> EnvSettings:
    return EnvSettings(
        {
            "GITHUB_ACTIONS": "true",
            "APIFY_API_TOKEN": "apify_api_real_token",
            "OPENAI_API_KEY": "openai-key",
            "GOOGLE_SPREADSHEET_ID": "sheet-id",
            "GOOGLE_TOKEN_JSON": google_token_json(),
            "JOB_KEYWORDS_TEXT": "GIS analyst",
            "MASTER_PROMPT_TEXT": "Evaluate truthfully",
            "MASTER_CV_TEX": "\\documentclass{article}",
            "CV_PHOTO_BASE64": base64.b64encode(b"png-data").decode("ascii"),
            "JOBFINDER_PIPELINE_MODE": "scrape_and_evaluate",
            "JOBFINDER_SCRAPER_OUTPUT_MODE": "google_sheets",
            "JOB_EVAL_CV_PDF_OUTPUT": "true",
            "JOB_EVAL_CV_DRIVE_FOLDER_ID": "drive-folder",
        }
    )


def test_prepare_and_cleanup_runtime_files_are_product_scoped(tmp_path):
    product = temporary_product(tmp_path)
    token_file = tmp_path / "google_token.json"

    result = prepare_runtime_files(
        complete_env(),
        product,
        token_file=token_file,
    )

    assert result.product == "jobfinder"
    assert result.needs_google is True
    assert result.needs_evaluation is True
    assert result.needs_pdf is True
    assert product.keywords_file.read_text(encoding="utf-8") == "GIS analyst\n"
    assert product.cv_photo_file.read_bytes() == b"png-data"
    assert token_file.exists()

    removed = cleanup_runtime_files(
        complete_env(),
        product,
        token_file=token_file,
    )

    assert token_file.resolve() in removed
    assert not product.keywords_file.exists()
    assert not product.cv_file.exists()
    assert not product.cv_photo_file.exists()


def test_prepare_rejects_google_token_missing_drive_scope(tmp_path):
    product = temporary_product(tmp_path)
    values = dict(complete_env().local_values)
    values["GOOGLE_TOKEN_JSON"] = google_token_json(include_drive_scope=False)

    with pytest.raises(RuntimeFileError, match="missing required OAuth scope"):
        prepare_runtime_files(
            EnvSettings(values),
            product,
            token_file=tmp_path / "google_token.json",
        )


def test_prepare_is_ci_only_by_default(tmp_path):
    product = temporary_product(tmp_path)
    values = dict(complete_env().local_values)
    values.pop("GITHUB_ACTIONS")

    with pytest.raises(RuntimeFileError, match="restricted to GitHub Actions"):
        prepare_runtime_files(
            EnvSettings(values),
            product,
            token_file=tmp_path / "google_token.json",
        )
