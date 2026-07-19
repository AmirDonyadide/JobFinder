"""Tests for Master-CV structural enforcement and exact overflow removals."""

from __future__ import annotations

import pytest

from jobfinder.evaluator.cv_contract import (
    ENGLISH_CV_CONTRACT,
    enforce_master_cv_contract,
    experience_entries,
    project_entries,
    remove_least_relevant_experience,
    remove_least_relevant_project,
    validate_master_cv_structure,
)
from jobfinder.evaluator.models import EvaluationError

MASTER_CV = r"""\documentclass{article}
\begin{document}
{\normalsize Zielposition \textbar{} Relevantes Stichwort 1}\\[0.5em]
Locked Name, Address, Email
% JOBFINDER_MSC_COURSE_POOL_BEGIN
% Machine Learning
% Geographic Information Systems
% JOBFINDER_MSC_COURSE_POOL_END
% JOBFINDER_BSC_COURSE_POOL_BEGIN
% Surveying
% Databases
% JOBFINDER_BSC_COURSE_POOL_END
\section*{Profil}
<<PROFIL>>
\section*{Ausbildung}
Locked MSc degree
\textit{Relevante Kurse:} <<MSc RELEVANTE KURSE>>
Locked BSc degree
\textit{Relevante Kurse:} <<BSc RELEVANTE KURSE>>
\section*{Berufserfahrung}
\textbf{Role A -- Company A} \hfill \textit{2025 -- 2026}\\
\begin{itemize}\item Master A\end{itemize}
\vspace{0.4em}
\textbf{Role B -- Company B} \hfill \textit{2021 -- 2022}\\
\begin{itemize}\item Master B\end{itemize}
\section*{Projekte}
\textbf{Project One}\\
\begin{itemize}\item Exact one\end{itemize}
\vspace{0.35em}
\textbf{Project Two}\\
\begin{itemize}\item Exact two\end{itemize}
\vspace{0.35em}
\textbf{Project Three}\\
\begin{itemize}\item Exact three\end{itemize}
\vspace{0.35em}
\textbf{Project Four}\\
\begin{itemize}\item Exact four\end{itemize}
\section*{Technische Fähigkeiten}
Python, GIS
\section*{Sprachen}
Locked languages
\end{document}
"""

GENERATED_CV = r"""\documentclass{other}
\begin{document}
{\normalsize GIS-Analyst \textbar{} Python \textbar{} QGIS}\\[0.5em]
Changed personal data
\section*{Profil}
Tailored profile
\section*{Ausbildung}
Changed degree
\textit{Relevante Kurse:} Machine Learning, Geographic Information Systems
\textit{Relevante Kurse:} Surveying
\section*{Berufserfahrung}
\textbf{GIS-Analyst -- Company A} \hfill \textit{2025 -- 2026}\\
\begin{itemize}\item Tailored factual A\end{itemize}
\vspace{0.4em}
\textbf{Praktikant -- Company B} \hfill \textit{2021 -- 2022}\\
\begin{itemize}\item Tailored factual B\end{itemize}
\section*{Projekte}
\textbf{Project Three}\\
\begin{itemize}\item Rewritten and forbidden\end{itemize}
\vspace{0.35em}
\textbf{Project One}\\
\begin{itemize}\item Rewritten and forbidden\end{itemize}
\vspace{0.35em}
\textbf{Project Two}\\
\begin{itemize}\item Rewritten and forbidden\end{itemize}
\section*{Technische Fähigkeiten}
Python, GIS
\section*{Sprachen}
Invented language
\end{document}
"""

ENGLISH_MASTER_CV = (
    MASTER_CV.replace(
        r"Zielposition \textbar{} Relevantes Stichwort 1",
        r"Target Position \textbar{} Primary Research Field \textbar{} Core Methods",
    )
    .replace("JOBFINDER_", "FINDER_")
    .replace(r"\section*{Profil}", r"\section*{Profile}")
    .replace(r"\section*{Ausbildung}", r"\section*{Education}")
    .replace(r"\section*{Berufserfahrung}", r"\section*{Experience}")
    .replace(r"\section*{Projekte}", r"\section*{Research Projects}")
    .replace(r"\section*{Sprachen}", r"\section*{Languages}")
    .replace("Relevante Kurse", "Relevant Courses")
    .replace("RELEVANTE KURSE", "RELEVANT COURSES")
)

ENGLISH_GENERATED_CV = (
    GENERATED_CV.replace(
        r"GIS-Analyst \textbar{} Python \textbar{} QGIS",
        r"Doctoral Researcher \textbar{} Spatial Analysis \textbar{} Python",
    )
    .replace(r"\section*{Profil}", r"\section*{Profile}")
    .replace(r"\section*{Ausbildung}", r"\section*{Education}")
    .replace(r"\section*{Berufserfahrung}", r"\section*{Experience}")
    .replace(r"\section*{Projekte}", r"\section*{Research Projects}")
    .replace(r"\section*{Sprachen}", r"\section*{Languages}")
    .replace("Relevante Kurse", "Relevant Courses")
)


def test_master_contract_restores_locked_content_and_exact_projects():
    protected = enforce_master_cv_contract(GENERATED_CV, MASTER_CV)

    assert r"\documentclass{article}" in protected
    assert "Locked Name, Address, Email" in protected
    assert "Changed personal data" not in protected
    assert "GIS-Analyst" in protected
    assert "Tailored profile" in protected
    assert "Locked MSc degree" in protected
    assert "Machine Learning, Geographic Information Systems" in protected
    assert "Locked languages" in protected
    assert "Invented language" not in protected
    assert "Rewritten and forbidden" not in protected
    assert [entry.title for entry in project_entries(protected)[1]] == [
        "Project Three",
        "Project One",
        "Project Two",
    ]
    assert [entry.block for entry in project_entries(protected)[1]][0].endswith(
        r"\begin{itemize}\item Exact three\end{itemize}"
    )


def test_master_contract_rejects_course_outside_embedded_pool():
    invalid = GENERATED_CV.replace("Machine Learning", "Invented Course", 1)

    with pytest.raises(EvaluationError, match="unsupported MSc course"):
        enforce_master_cv_contract(invalid, MASTER_CV)


def test_overflow_removes_only_last_ranked_blocks():
    protected = enforce_master_cv_contract(GENERATED_CV, MASTER_CV)
    without_project = remove_least_relevant_project(protected)
    without_experience = remove_least_relevant_experience(without_project)

    assert [entry.title for entry in project_entries(without_project)[1]] == [
        "Project Three",
        "Project One",
    ]
    assert [entry.title for entry in experience_entries(without_experience)[1]] == [
        "GIS-Analyst -- Company A"
    ]
    assert "Exact two" not in without_project
    assert "Tailored factual B" not in without_experience


def test_master_structure_validator_accepts_contract_template():
    validate_master_cv_structure(MASTER_CV)


def test_english_contract_enforces_and_trims_phdfinder_cv():
    validate_master_cv_structure(
        ENGLISH_MASTER_CV,
        contract=ENGLISH_CV_CONTRACT,
    )

    protected = enforce_master_cv_contract(
        ENGLISH_GENERATED_CV,
        ENGLISH_MASTER_CV,
        contract=ENGLISH_CV_CONTRACT,
    )

    assert r"\section*{Education}" in protected
    assert r"\textit{Relevant Courses:} Machine Learning" in protected
    assert "Locked languages" in protected
    assert "Invented language" not in protected
    assert [
        entry.title
        for entry in project_entries(protected, contract=ENGLISH_CV_CONTRACT)[1]
    ] == ["Project Three", "Project One", "Project Two"]

    without_project = remove_least_relevant_project(
        protected,
        contract=ENGLISH_CV_CONTRACT,
    )
    without_experience = remove_least_relevant_experience(
        without_project,
        contract=ENGLISH_CV_CONTRACT,
    )
    assert len(
        project_entries(without_project, contract=ENGLISH_CV_CONTRACT)[1]
    ) == 2
    assert len(
        experience_entries(without_experience, contract=ENGLISH_CV_CONTRACT)[1]
    ) == 1
