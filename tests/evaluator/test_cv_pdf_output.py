"""Tests for generated CV PDF output."""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from jobfinder.evaluator.latex import (
    LatexCompilationResult,
    compile_latex_to_pdf,
    parse_page_count_from_output,
    prepare_latex_for_xelatex,
    repair_reported_misplaced_ampersand,
)
from jobfinder.evaluator.models import JobEvaluation, JobRecord
from jobfinder.evaluator.pdf_output import (
    assign_cv_ids,
    cv_pdf_filename,
    drive_run_folder_name,
    generate_cv_pdf_outputs,
    sanitize_filename,
)

LATEX_CV = r"\documentclass{article}\begin{document}\section*{Profile}\end{document}"


class FakeRequest:
    """Minimal executable fake Google API request."""

    def __init__(self, result: dict[str, Any]) -> None:
        self.result = result

    def execute(self) -> dict[str, Any]:
        return self.result


class FakeDriveFiles:
    """Fake Drive files resource for folder creation tests."""

    def __init__(self, service: FakeDriveService) -> None:
        self.service = service

    def list(self, **kwargs: Any) -> FakeRequest:
        self.service.lists.append(kwargs)
        return FakeRequest({"files": []})

    def get(self, **kwargs: Any) -> FakeRequest:
        self.service.gets.append(kwargs)
        return FakeRequest(
            {
                "id": kwargs["fileId"],
                "name": "JobFinder PDFs",
                "mimeType": "application/vnd.google-apps.folder",
                "webViewLink": f"https://drive.example/{kwargs['fileId']}",
            }
        )

    def create(self, **kwargs: Any) -> FakeRequest:
        body = kwargs["body"]
        self.service.creates.append(kwargs)
        file_id = f"folder-{len(self.service.creates)}"
        return FakeRequest(
            {
                "id": file_id,
                "name": body["name"],
                "webViewLink": f"https://drive.example/{file_id}",
            }
        )


class FakeDriveService:
    """Small fake for the Google Drive service surface used by PDF output."""

    def __init__(self) -> None:
        self.gets: list[dict[str, Any]] = []
        self.lists: list[dict[str, Any]] = []
        self.creates: list[dict[str, Any]] = []

    def files(self) -> FakeDriveFiles:
        return FakeDriveFiles(self)


def test_sanitize_filename_removes_path_and_unsafe_characters():
    """Generated PDF filenames should not preserve path separators or wildcards."""
    value = sanitize_filename("../Senior: GIS/Remote*? <Berlin>|")

    assert value == "Senior GIS Remote Berlin"


def test_cv_pdf_filename_uses_requested_parts_in_order():
    """Generated PDF filenames should use ID, applicant, role, then company."""
    assert cv_pdf_filename(
        12,
        "Senior GIS Analyst (m/f/d), Remote / Geo+Maps GmbH & Co. KG",
        "Amir Donyadide",
    ) == ("12_CV_Amir_Donyadide_Senior_GIS_Analyst_m_f_Geo_Maps.pdf")
    assert cv_pdf_filename(13, "Développeur C++ / Météo AG") == (
        "13_CV_Applicant_Developpeur_C_Meteo.pdf"
    )


def test_assign_cv_ids_are_row_numbers_for_generated_cvs():
    """Only rows with generated LaTeX CVs receive stable row-number IDs."""
    records = [
        JobRecord(2, "GIS Analyst / Acme", "Job Title: GIS Analyst"),
        JobRecord(3, "Senior Manager / Acme", "Job Title: Senior Manager"),
        JobRecord(4, "Remote Sensing / Example", "Job Title: Remote Sensing"),
    ]
    evaluations = {
        2: JobEvaluation(2, "Suitable", 18, "Match", tailored_cv=LATEX_CV),
        3: JobEvaluation(3, "Not Suitable", 4, "Too senior", tailored_cv=LATEX_CV),
        4: JobEvaluation(4, "Suitable", 17, "Match", tailored_cv=LATEX_CV),
    }

    candidates = assign_cv_ids(records, evaluations)

    assert [candidate.cv_id for candidate in candidates] == [2, 4]
    assert [candidate.row_number for candidate in candidates] == [2, 4]
    assert candidates[0].filename == "2_CV_Applicant_GIS_Analyst_Acme.pdf"
    assert candidates[1].filename == "4_CV_Applicant_Remote_Sensing_Example.pdf"


def test_compile_latex_to_pdf_captures_subprocess_failure(tmp_path):
    """LaTeX compiler failures should return an error instead of raising."""
    output_pdf = tmp_path / "cv.pdf"

    def fake_runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=1,
            stdout="! Undefined control sequence.",
            stderr="",
        )

    result = compile_latex_to_pdf(
        r"\documentclass{article}\begin{document}\bad\end{document}",
        output_pdf,
        runner=fake_runner,
    )

    assert result.success is False
    assert "! Undefined control sequence." in result.error
    assert not output_pdf.exists()


def test_compile_latex_to_pdf_rejects_unsafe_input_commands(tmp_path):
    """Model-generated CVs should not be able to read arbitrary local files."""
    output_pdf = tmp_path / "cv.pdf"

    def fake_runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise AssertionError("unsafe LaTeX should be rejected before latexmk runs")

    result = compile_latex_to_pdf(
        r"\documentclass{article}\begin{document}\input{/etc/passwd}\end{document}",
        output_pdf,
        runner=fake_runner,
    )

    assert result.success is False
    assert "unsupported command" in result.error
    assert not output_pdf.exists()


def test_prepare_latex_for_xelatex_replaces_pdflatex_encoding_packages():
    """XeLaTeX should use OpenType fonts so German sharp s renders correctly."""
    latex = (
        "\\documentclass{article}\n"
        "\\usepackage[utf8]{inputenc}\n"
        "\\usepackage[T1]{fontenc}\n"
        "\\usepackage{geometry}\n"
        "\\begin{document}Straßenplanung, fließend\\end{document}"
    )

    prepared = prepare_latex_for_xelatex(latex)

    assert "\\usepackage[utf8]{inputenc}" not in prepared
    assert "\\usepackage[T1]{fontenc}" not in prepared
    assert "\\usepackage{fontspec}" in prepared
    assert "lmroman10-regular.otf" in prepared
    assert prepared.index("\\usepackage{fontspec}") < prepared.index(
        "\\usepackage{geometry}"
    )


def test_prepare_latex_for_xelatex_preserves_existing_fontspec():
    """A CV with an explicit fontspec setup should keep the user's font choice."""
    latex = (
        "\\documentclass{article}\n"
        "\\usepackage{fontspec}\n"
        "\\setmainfont{Helvetica Neue}\n"
        "\\begin{document}Straßenplanung\\end{document}"
    )

    prepared = prepare_latex_for_xelatex(latex)

    assert prepared == latex
    assert "lmroman10-regular.otf" not in prepared


def test_compile_latex_to_pdf_runs_normalized_xelatex_source(tmp_path):
    """Compilation should write the XeLaTeX-normalized source into the temp dir."""
    output_pdf = tmp_path / "cv.pdf"
    captured: dict[str, str] = {}

    def fake_runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        cwd = Path(kwargs["cwd"])
        captured["tex"] = (cwd / "cv.tex").read_text(encoding="utf-8")
        (cwd / "cv.pdf").write_bytes(b"%PDF-1.7\n")
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout="Output written on cv.pdf (1 page, 12345 bytes).",
            stderr="",
        )

    result = compile_latex_to_pdf(
        (
            "\\documentclass{article}\n"
            "\\usepackage[utf8]{inputenc}\n"
            "\\usepackage[T1]{fontenc}\n"
            "\\begin{document}Straßenplanung\\end{document}"
        ),
        output_pdf,
        runner=fake_runner,
    )

    assert result.success is True
    assert "\\usepackage{fontspec}" in captured["tex"]
    assert "\\usepackage[T1]{fontenc}" not in captured["tex"]
    assert result.page_count == 1
    assert output_pdf.exists()


def test_repair_reported_misplaced_ampersand_only_changes_rejected_line():
    source = "First & unchanged\nData & Visualization\nLast & unchanged\n"
    compiler_log = "./cv.tex:2: Misplaced alignment tab character &."

    repaired = repair_reported_misplaced_ampersand(source, compiler_log)

    assert repaired == "First & unchanged\nData \\& Visualization\nLast & unchanged\n"


def test_compile_latex_to_pdf_retries_reported_bare_ampersand(tmp_path):
    calls: list[str] = []

    def fake_runner(command, *, cwd, **kwargs):
        source = (Path(cwd) / "cv.tex").read_text(encoding="utf-8")
        calls.append(source)
        if len(calls) == 1:
            line_number = next(
                index
                for index, line in enumerate(source.splitlines(), start=1)
                if "Data & Visualization" in line
            )
            return subprocess.CompletedProcess(
                command,
                1,
                f"./cv.tex:{line_number}: Misplaced alignment tab character &.",
                "",
            )
        (Path(cwd) / "cv.pdf").write_bytes(b"%PDF-1.7\n")
        return subprocess.CompletedProcess(
            command,
            0,
            "Output written on cv.pdf (1 page, 10 bytes).",
            "",
        )

    result = compile_latex_to_pdf(
        "\\documentclass{article}\n\\begin{document}\nData & Visualization\n"
        "\\end{document}",
        tmp_path / "cv.pdf",
        runner=fake_runner,
    )

    assert result.success is True
    assert len(calls) == 2
    assert "Data \\& Visualization" in calls[1]


def test_drive_run_folder_name_uses_required_format():
    """Drive run folder names should use sortable timestamps."""
    assert drive_run_folder_name(datetime(2026, 5, 20, 9, 8, 7)) == (
        "2026-05-20_09-08-07"
    )


def test_generate_cv_pdf_outputs_creates_drive_folder_and_links(tmp_path):
    """PDF generation should compile, upload, and return row-level Drive links."""
    service = FakeDriveService()
    uploads: list[tuple[Path, str, str]] = []
    records = [JobRecord(2, "GIS Analyst / Acme", "Job Title: GIS Analyst")]
    evaluations = {2: JobEvaluation(2, "Suitable", 18, "Match", tailored_cv=LATEX_CV)}

    def fake_compile(
        latex_code: str,
        output_pdf: Path,
        **kwargs: Any,
    ) -> LatexCompilationResult:
        output_pdf.write_bytes(b"%PDF-1.7\n")
        return LatexCompilationResult(success=True, pdf_path=output_pdf, page_count=1)

    def fake_upload(
        drive_service: Any,
        pdf_path: Path,
        *,
        folder_id: str,
        filename: str,
    ) -> SimpleNamespace:
        uploads.append((pdf_path, folder_id, filename))
        return SimpleNamespace(web_view_link=f"https://drive.example/{filename}")

    result = generate_cv_pdf_outputs(
        records,
        evaluations,
        drive_service=service,
        parent_folder_id="parent-folder-id",
        now=datetime(2026, 5, 20, 9, 8, 7),
        compile_latex=fake_compile,
        upload_pdf=fake_upload,
    )

    assert result.outputs == {
        2: "https://drive.example/2_CV_Applicant_GIS_Analyst_Acme.pdf"
    }
    assert result.success_count == 1
    assert result.error_count == 0
    assert service.gets[0]["fileId"] == "parent-folder-id"
    assert [call["body"]["name"] for call in service.creates] == [
        "2026-05-20_09-08-07",
    ]
    assert service.creates[0]["body"]["parents"] == ["parent-folder-id"]
    assert uploads[0][1] == "folder-1"
    assert uploads[0][2] == "2_CV_Applicant_GIS_Analyst_Acme.pdf"


def test_generate_cv_pdf_outputs_checkpoints_each_result(tmp_path):
    service = FakeDriveService()
    records = [JobRecord(2, "GIS Analyst / Acme", "job")]
    evaluations = {2: JobEvaluation(2, "Suitable", 18, "Match", tailored_cv=LATEX_CV)}
    checkpoints: list[tuple[int, str]] = []

    result = generate_cv_pdf_outputs(
        records,
        evaluations,
        drive_service=service,
        parent_folder_id="parent-folder-id",
        now=datetime(2026, 7, 2, 18, 30, 0),
        compile_latex=_make_compile_stub([2]),
        upload_pdf=_fake_upload,
        on_output=lambda row_number, value: checkpoints.append((row_number, value)),
    )

    assert checkpoints == [(2, result.outputs[2])]


def test_generate_cv_pdf_outputs_requires_drive_folder_id():
    """PDF output should clearly report a missing Drive folder ID."""
    records = [JobRecord(2, "GIS Analyst / Acme", "Job Title: GIS Analyst")]
    evaluations = {2: JobEvaluation(2, "Suitable", 18, "Match", tailored_cv=LATEX_CV)}

    checkpoints: list[tuple[int, str]] = []
    result = generate_cv_pdf_outputs(
        records,
        evaluations,
        drive_service=FakeDriveService(),
        on_output=lambda row_number, value: checkpoints.append((row_number, value)),
    )

    assert result.success_count == 0
    assert result.error_count == 1
    assert "Missing Google Drive folder ID" in result.outputs[2]
    assert checkpoints == [(2, result.outputs[2])]


# ---------------------------------------------------------------------------
# parse_page_count_from_output
# ---------------------------------------------------------------------------


def test_parse_page_count_from_output_parses_xelatex_singular():
    """XeTeX 'Output written on ... (1 page).' should be parsed correctly."""
    stdout = "Output written on cv.pdf (1 page, 12345 bytes)."
    assert parse_page_count_from_output(stdout) == 1


def test_parse_page_count_from_output_parses_xelatex_plural():
    """XeTeX 'Output written on ... (3 pages).' should be parsed correctly."""
    stdout = (
        "This is XeTeX, Version 3.141592653\n"
        "Output written on cv.pdf (3 pages, 98765 bytes).\n"
        "Transcript written on cv.log."
    )
    assert parse_page_count_from_output(stdout) == 3


def test_parse_page_count_from_output_returns_none_when_absent():
    """Missing page-count line should return None, not raise."""
    assert parse_page_count_from_output("LaTeX compilation complete.") is None
    assert parse_page_count_from_output("") is None


# ---------------------------------------------------------------------------
# page-limit enforcement inside generate_cv_pdf_outputs
# ---------------------------------------------------------------------------


def _make_compile_stub(page_counts: list[int | None]) -> Any:
    """Return a fake compile_latex that cycles through the supplied page counts."""
    call_index = [0]

    def fake_compile(
        latex_code: str,
        output_pdf: Path,
        **kwargs: Any,
    ) -> LatexCompilationResult:
        idx = min(call_index[0], len(page_counts) - 1)
        call_index[0] += 1
        count = page_counts[idx]
        output_pdf.write_bytes(b"%PDF-1.7\n")
        return LatexCompilationResult(
            success=True, pdf_path=output_pdf, page_count=count
        )

    return fake_compile


def _fake_upload(
    drive_service: Any,
    pdf_path: Path,
    *,
    folder_id: str,
    filename: str,
) -> SimpleNamespace:
    return SimpleNamespace(web_view_link=f"https://drive.example/{filename}")


def test_generate_cv_pdf_outputs_accepts_cv_within_page_limit(tmp_path):
    """A CV within the limit must not remove projects or experiences."""
    service = FakeDriveService()
    records = [JobRecord(2, "GIS / Acme", "Job Title: GIS")]
    evaluations = {2: JobEvaluation(2, "Suitable", 18, "ok", tailored_cv=LATEX_CV)}

    removal_calls: list[str] = []

    def fake_remove_project(latex: str) -> str:
        removal_calls.append("project")
        return latex

    def fake_remove_experience(latex: str) -> str:
        removal_calls.append("experience")
        return latex

    result = generate_cv_pdf_outputs(
        records,
        evaluations,
        drive_service=service,
        parent_folder_id="folder",
        now=datetime(2026, 1, 1),
        compile_latex=_make_compile_stub([2]),  # 2 pages, limit is 2
        upload_pdf=_fake_upload,
        max_page_limit=2,
        remove_project=fake_remove_project,
        remove_experience=fake_remove_experience,
    )

    assert result.success_count == 1
    assert result.error_count == 0
    assert removal_calls == []


def test_generate_cv_pdf_outputs_removes_project_first(tmp_path):
    """A 3-page CV must remove one project and recompile before anything else."""
    service = FakeDriveService()
    records = [JobRecord(2, "GIS / Acme", "Job Title: GIS")]
    evaluations = {2: JobEvaluation(2, "Suitable", 18, "ok", tailored_cv=LATEX_CV)}

    removal_calls: list[str] = []

    def fake_remove_project(latex: str) -> str:
        removal_calls.append("project")
        return latex + "% project removed\n"

    def fake_remove_experience(latex: str) -> str:
        removal_calls.append("experience")
        return latex + "% experience removed\n"

    result = generate_cv_pdf_outputs(
        records,
        evaluations,
        drive_service=service,
        parent_folder_id="folder",
        now=datetime(2026, 1, 1),
        compile_latex=_make_compile_stub([3, 2]),
        upload_pdf=_fake_upload,
        max_page_limit=2,
        remove_project=fake_remove_project,
        remove_experience=fake_remove_experience,
    )

    assert result.success_count == 1
    assert result.error_count == 0
    assert removal_calls == ["project"]


def test_generate_cv_pdf_outputs_keeps_cv_after_both_required_removals():
    """A still-long CV is retained after exactly one removal of each type."""
    service = FakeDriveService()
    records = [JobRecord(2, "GIS / Acme", "Job Title: GIS")]
    evaluations = {2: JobEvaluation(2, "Suitable", 18, "ok", tailored_cv=LATEX_CV)}

    removal_calls: list[str] = []

    def fake_remove_project(latex: str) -> str:
        removal_calls.append("project")
        return latex + "% project removed\n"

    def fake_remove_experience(latex: str) -> str:
        removal_calls.append("experience")
        return latex + "% experience removed\n"

    result = generate_cv_pdf_outputs(
        records,
        evaluations,
        drive_service=service,
        parent_folder_id="folder",
        now=datetime(2026, 1, 1),
        compile_latex=_make_compile_stub([3, 3, 3]),
        upload_pdf=_fake_upload,
        max_page_limit=2,
        remove_project=fake_remove_project,
        remove_experience=fake_remove_experience,
    )

    assert result.success_count == 1
    assert result.error_count == 0
    assert removal_calls == ["project", "experience"]


def test_generate_cv_pdf_outputs_rejects_unknown_page_count():
    """An unknown page count must not bypass the page contract."""
    service = FakeDriveService()
    records = [JobRecord(2, "GIS / Acme", "Job Title: GIS")]
    evaluations = {2: JobEvaluation(2, "Suitable", 18, "ok", tailored_cv=LATEX_CV)}

    result = generate_cv_pdf_outputs(
        records,
        evaluations,
        drive_service=service,
        parent_folder_id="folder",
        now=datetime(2026, 1, 1),
        compile_latex=_make_compile_stub([None]),  # page_count unknown
        upload_pdf=_fake_upload,
        max_page_limit=2,
    )

    assert result.success_count == 0
    assert result.error_count == 1
    assert "page count could not be determined" in result.outputs[2]


def test_generate_cv_pdf_outputs_reports_safe_removal_failure():
    """Failure to remove an exact block must stop rather than rewrite or over-trim."""
    service = FakeDriveService()
    records = [JobRecord(2, "GIS / Acme", "Job Title: GIS")]
    evaluations = {2: JobEvaluation(2, "Suitable", 18, "ok", tailored_cv=LATEX_CV)}

    def exploding_remove(latex: str) -> str:
        raise RuntimeError("project block not found")

    result = generate_cv_pdf_outputs(
        records,
        evaluations,
        drive_service=service,
        parent_folder_id="folder",
        now=datetime(2026, 1, 1),
        compile_latex=_make_compile_stub([3]),
        upload_pdf=_fake_upload,
        max_page_limit=2,
        remove_project=exploding_remove,
    )

    assert result.success_count == 0
    assert result.error_count == 1
    assert "Could not remove the least-relevant project" in result.outputs[2]
