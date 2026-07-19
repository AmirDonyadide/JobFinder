"""Tests for evaluator CLI argument resolution."""

from __future__ import annotations

from jobfinder.env import EnvSettings
from jobfinder.evaluator.cli import build_arg_parser, parse_source
from jobfinder.evaluator.models import EvaluationError
from jobfinder.evaluator.service import (
    options_from_env,
    parse_unsuitable_row_policy,
    resolve_cv_photo_file,
    should_remove_rejected_rows,
)


def test_parse_source_accepts_google_aliases():
    """Source aliases should resolve consistently across CLI and env settings."""
    env = EnvSettings({})

    assert parse_source("sheets", "", env) == "google_sheets"
    assert parse_source("drive", "", env) == "google_sheets"
    assert parse_source("local", "", env) == "excel"


def test_parse_source_defaults_to_google_when_sheet_id_is_configured(monkeypatch):
    """A configured spreadsheet ID should make Google Sheets the default source."""
    monkeypatch.delenv("JOB_EVAL_SOURCE", raising=False)

    assert parse_source(None, "spreadsheet-id", EnvSettings({})) == "google_sheets"


def test_arg_parser_accepts_google_sheet_id_option():
    """The CLI should expose the Google Sheet ID option mentioned in errors."""
    parser = build_arg_parser(EnvSettings({}))

    args = parser.parse_args(
        ["--source", "google", "--google-sheet-id", "spreadsheet-id"]
    )

    assert args.source == "google"
    assert args.google_sheet_id == "spreadsheet-id"


def test_arg_parser_accepts_pdf_only_recovery_mode():
    parser = build_arg_parser(EnvSettings({}))

    args = parser.parse_args(["--pdf-only"])

    assert args.pdf_only is True


def test_evaluator_uses_phdfinder_asset_defaults():
    env = EnvSettings({"JOB_EVAL_CV_PDF_OUTPUT": "false"})

    options = options_from_env(
        env,
        source_arg="excel",
        sheet="latest",
        google_sheet_id_arg="",
        profile="phd",
    )

    assert options.profile.key == "phd"
    assert options.excel_file.name == "phd_jobs.xlsx"
    assert options.master_prompt_file.parent.name == "evaluator"
    assert options.master_prompt_file.parents[1].name == "phdfinder"
    assert options.cv_file.parent.name == "evaluator"
    assert options.cv_file.parents[1].name == "phdfinder"
    assert options.cv_photo_file.parent.name == "evaluator"
    assert options.cv_photo_file.parents[1].name == "phdfinder"


def test_phdfinder_requires_its_own_cv_drive_folder(monkeypatch):
    monkeypatch.setenv("JOB_EVAL_CV_DRIVE_FOLDER_ID", "jobfinder-folder")
    monkeypatch.delenv("PHDFINDER_CV_DRIVE_FOLDER_ID", raising=False)

    try:
        options_from_env(
            EnvSettings({}),
            source_arg="excel",
            sheet="latest",
            google_sheet_id_arg="",
            profile="phd",
        )
    except EvaluationError as exc:
        assert "PHDFINDER_CV_DRIVE_FOLDER_ID" in str(exc)
    else:
        raise AssertionError("Expected PhDFinder to require a separate Drive folder.")


def test_parse_unsuitable_row_policy_controls_final_filtering():
    """The evaluator should support keeping all rows or filtering rejections."""
    filtered = parse_unsuitable_row_policy("")
    keep_all = parse_unsuitable_row_policy("keep_all")

    assert should_remove_rejected_rows(filtered) is True
    assert should_remove_rejected_rows(keep_all) is False


def test_parse_unsuitable_row_policy_rejects_unknown_values():
    """Bad row-policy settings should fail before the evaluator writes output."""
    try:
        parse_unsuitable_row_policy("remove_everything")
    except EvaluationError as exc:
        assert "JOB_EVAL_UNSUITABLE_ROW_POLICY" in str(exc)
    else:
        raise AssertionError("Expected an unsupported unsuitable row policy to fail.")


def test_resolve_cv_photo_file_accepts_png_fallback(tmp_path):
    """The evaluator should find photo.png when a legacy JPG path is configured."""
    photo = tmp_path / "photo.png"
    photo.write_bytes(b"png")

    assert resolve_cv_photo_file(tmp_path / "photo.jpg") == photo
