"""Structural contract enforcement for tailored LaTeX CVs.

The model may tailor wording where the master prompt allows it, but this module
keeps machine-verifiable content anchored to the Master CV. Page-limit changes
also happen here as exact block removals, never as free-form rewriting.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from jobfinder.evaluator.models import EvaluationError
from jobfinder.products import FinderProduct, resolve_product

SECTION_RE = re.compile(r"(?m)^[ \t]*\\section\*?\{(?P<title>[^}]+)\}")
ROLE_LINE_RE = re.compile(
    r"(?m)^[ \t]*\{\\normalsize\s+.+?\}\\\\(?:\[[^\]]*\])?[ \t]*$"
)
PROJECT_START_RE = re.compile(
    r"(?m)^[ \t]*\\textbf\{(?P<title>.+?)\}\s*(?:\\hfill|\\\\)"
)
EXPERIENCE_START_RE = re.compile(
    r"(?m)^[ \t]*\\textbf\{(?P<title>.+?)\}\s*\\hfill\s*"
    r"\\textit\{(?P<date>[^}]+)\}\\\\"
)
TRAILING_SPACING_RE = re.compile(
    r"(?:\n[ \t]*\\vspace\{[^}]+\}[ \t]*)+\s*$",
    re.MULTILINE,
)

COURSE_POOL_MARKERS = {
    "MSc": (
        ("FINDER_MSC_COURSE_POOL_BEGIN", "FINDER_MSC_COURSE_POOL_END"),
        ("JOBFINDER_MSC_COURSE_POOL_BEGIN", "JOBFINDER_MSC_COURSE_POOL_END"),
    ),
    "BSc": (
        ("FINDER_BSC_COURSE_POOL_BEGIN", "FINDER_BSC_COURSE_POOL_END"),
        ("JOBFINDER_BSC_COURSE_POOL_BEGIN", "JOBFINDER_BSC_COURSE_POOL_END"),
    ),
}


@dataclass(frozen=True)
class CvContract:
    """Language and section vocabulary for one product's Master CV."""

    language: str
    profile_section: str
    education_section: str
    experience_section: str
    projects_section: str
    languages_section: str
    course_label: str
    msc_placeholder: str
    bsc_placeholder: str
    unresolved_header_terms: tuple[str, ...]

    @property
    def required_sections(self) -> tuple[str, ...]:
        """Return the section names required by this CV contract."""
        return (
            self.profile_section,
            self.education_section,
            self.experience_section,
            self.projects_section,
            self.languages_section,
        )


GERMAN_CV_CONTRACT = CvContract(
    language="German",
    profile_section="Profil",
    education_section="Ausbildung",
    experience_section="Berufserfahrung",
    projects_section="Projekte",
    languages_section="Sprachen",
    course_label="Relevante Kurse",
    msc_placeholder="<<MSc RELEVANTE KURSE>>",
    bsc_placeholder="<<BSc RELEVANTE KURSE>>",
    unresolved_header_terms=("Zielposition", "Relevantes Stichwort"),
)

ENGLISH_CV_CONTRACT = CvContract(
    language="English",
    profile_section="Profile",
    education_section="Education",
    experience_section="Experience",
    projects_section="Research Projects",
    languages_section="Languages",
    course_label="Relevant Courses",
    msc_placeholder="<<MSc RELEVANT COURSES>>",
    bsc_placeholder="<<BSc RELEVANT COURSES>>",
    unresolved_header_terms=(
        "Target Position",
        "Primary Research Field",
        "Core Methods",
    ),
)

# Backward-compatible names for the original JobFinder contract.
MSC_PLACEHOLDER = GERMAN_CV_CONTRACT.msc_placeholder
BSC_PLACEHOLDER = GERMAN_CV_CONTRACT.bsc_placeholder


@dataclass(frozen=True)
class LatexEntry:
    """One top-level project or experience block."""

    title: str
    block: str
    date: str = ""


def cv_contract_for_product(
    product: str | FinderProduct | None = None,
) -> CvContract:
    """Return the CV language contract configured for a finder product."""
    finder_product = resolve_product(product)
    if finder_product.cv_language == "English":
        return ENGLISH_CV_CONTRACT
    if finder_product.cv_language == "German":
        return GERMAN_CV_CONTRACT
    raise EvaluationError(
        f"Unsupported CV language {finder_product.cv_language!r} for "
        f"{finder_product.display_name}."
    )


def _normalize_title(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def _course_line_re(contract: CvContract) -> re.Pattern[str]:
    return re.compile(
        rf"(?m)^(?P<indent>[ \t]*)\\textit\{{"
        rf"{re.escape(contract.course_label)}:\}}\s*(?P<value>.*?)\s*$"
    )


def section_span(latex: str, title: str) -> tuple[int, int] | None:
    """Return the source span for a named LaTeX section."""
    starts = list(SECTION_RE.finditer(latex))
    expected = _normalize_title(title)
    for index, match in enumerate(starts):
        if _normalize_title(match.group("title")) != expected:
            continue
        end = starts[index + 1].start() if index + 1 < len(starts) else len(latex)
        return match.start(), end
    return None


def extract_section(latex: str, title: str) -> str:
    """Extract a complete named section."""
    span = section_span(latex, title)
    if span is None:
        return ""
    return latex[span[0] : span[1]].strip()


def replace_section(latex: str, title: str, replacement: str) -> str:
    """Replace an existing section without touching adjacent sections."""
    span = section_span(latex, title)
    if span is None:
        raise EvaluationError(f"Tailored CV is missing required section {title!r}.")
    prefix = latex[: span[0]].rstrip()
    suffix = latex[span[1] :].lstrip("\n")
    return "\n\n".join(part for part in (prefix, replacement.strip(), suffix) if part)


def _split_entries(
    section: str, start_re: re.Pattern[str]
) -> tuple[str, list[LatexEntry]]:
    matches = list(start_re.finditer(section))
    if not matches:
        return section.strip(), []
    prefix = section[: matches[0].start()].rstrip()
    entries: list[LatexEntry] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(section)
        block = TRAILING_SPACING_RE.sub(
            "", section[match.start() : end].rstrip()
        ).strip()
        entries.append(
            LatexEntry(
                title=re.sub(r"\s+", " ", match.group("title")).strip(),
                block=block,
                date=(match.groupdict().get("date") or "").strip(),
            )
        )
    return prefix, entries


def project_entries(
    latex: str,
    *,
    contract: CvContract = GERMAN_CV_CONTRACT,
) -> tuple[str, list[LatexEntry]]:
    """Return the configured Projects section prefix and its top-level entries."""
    section = extract_section(latex, contract.projects_section)
    if not section:
        raise EvaluationError(
            f"Tailored CV is missing required section {contract.projects_section!r}."
        )
    return _split_entries(section, PROJECT_START_RE)


def experience_entries(
    latex: str,
    *,
    contract: CvContract = GERMAN_CV_CONTRACT,
) -> tuple[str, list[LatexEntry]]:
    """Return the configured Experience section and its top-level entries."""
    section = extract_section(latex, contract.experience_section)
    if not section:
        raise EvaluationError(
            f"Tailored CV is missing required section {contract.experience_section!r}."
        )
    return _split_entries(section, EXPERIENCE_START_RE)


def _join_entries(prefix: str, entries: list[LatexEntry], spacing: str) -> str:
    blocks = [entry.block.strip() for entry in entries]
    if not blocks:
        return prefix.strip()
    return prefix.rstrip() + "\n\n" + f"\n\n{spacing}\n\n".join(blocks)


def _course_pool(master_latex: str, level: str) -> tuple[str, ...]:
    for begin_marker, end_marker in COURSE_POOL_MARKERS[level]:
        pattern = re.compile(
            rf"(?ms)^%\s*{re.escape(begin_marker)}\s*$"
            rf"(?P<body>.*?)"
            rf"^%\s*{re.escape(end_marker)}\s*$"
        )
        match = pattern.search(master_latex)
        if not match:
            continue
        courses = []
        for line in match.group("body").splitlines():
            value = re.sub(r"^\s*%\s*(?:-\s*)?", "", line).strip()
            if value:
                courses.append(value)
        return tuple(courses)
    return ()


def _validated_course_value(value: str, allowed: tuple[str, ...], level: str) -> str:
    selected = [item.strip() for item in re.split(r"\s*[;,]\s*", value) if item.strip()]
    if not selected:
        raise EvaluationError(
            f"Tailored CV has an empty {level} relevant-courses line."
        )
    invalid = [course for course in selected if course not in allowed]
    if invalid:
        raise EvaluationError(
            f"Tailored CV contains unsupported {level} course(s): {', '.join(invalid)}."
        )
    return ", ".join(selected)


def _protected_education(
    generated_latex: str,
    master_latex: str,
    contract: CvContract,
) -> str:
    source = extract_section(master_latex, contract.education_section)
    generated = extract_section(generated_latex, contract.education_section)
    if not source or not generated:
        raise EvaluationError(
            "Master or tailored CV is missing the "
            f"{contract.education_section} section."
        )

    pools = (_course_pool(master_latex, "MSc"), _course_pool(master_latex, "BSc"))
    generated_lines = list(_course_line_re(contract).finditer(generated))
    if all(pools):
        if len(generated_lines) != 2:
            raise EvaluationError(
                "Tailored CV must contain exactly two "
                f"{contract.course_label} lines."
            )
        msc_value = _validated_course_value(
            generated_lines[0].group("value"), pools[0], "MSc"
        )
        bsc_value = _validated_course_value(
            generated_lines[1].group("value"), pools[1], "BSc"
        )
        if (
            contract.msc_placeholder not in source
            or contract.bsc_placeholder not in source
        ):
            raise EvaluationError("Master CV is missing relevant-course placeholders.")
        source = source.replace(contract.msc_placeholder, msc_value, 1)
        source = source.replace(contract.bsc_placeholder, bsc_value, 1)
    return source


def _restore_master_prefix(
    generated_latex: str,
    master_latex: str,
    contract: CvContract,
) -> str:
    master_first = SECTION_RE.search(master_latex)
    generated_first = SECTION_RE.search(generated_latex)
    if master_first is None or generated_first is None:
        raise EvaluationError("Master or tailored CV has no LaTeX sections.")

    master_prefix = master_latex[: master_first.start()].rstrip()
    generated_prefix = generated_latex[: generated_first.start()]
    master_role = ROLE_LINE_RE.search(master_prefix)
    if master_role:
        generated_role = ROLE_LINE_RE.search(generated_prefix)
        if not generated_role:
            raise EvaluationError(
                "Tailored CV is missing the adaptable header role line."
            )
        role_line = generated_role.group(0).strip()
        if any(term in role_line for term in contract.unresolved_header_terms):
            raise EvaluationError(
                "Tailored CV left header role placeholders unresolved."
            )
        master_prefix = ROLE_LINE_RE.sub(lambda _: role_line, master_prefix, count=1)

    return master_prefix + "\n\n" + generated_latex[generated_first.start() :].lstrip()


def _protected_projects(
    generated_latex: str,
    master_latex: str,
    contract: CvContract,
) -> str:
    source_prefix, source_entries = project_entries(master_latex, contract=contract)
    _, generated_entries = project_entries(generated_latex, contract=contract)
    if not 3 <= len(generated_entries) <= 4:
        raise EvaluationError(
            "Tailored CV must select exactly 3 or 4 Master CV projects."
        )

    source_by_title = {_normalize_title(entry.title): entry for entry in source_entries}
    selected: list[LatexEntry] = []
    seen: set[str] = set()
    for entry in generated_entries:
        key = _normalize_title(entry.title)
        if key in seen:
            raise EvaluationError(f"Tailored CV repeats project {entry.title!r}.")
        source_entry = source_by_title.get(key)
        if source_entry is None:
            message = (
                "Tailored CV contains a project not found in the Master CV: "
                f"{entry.title!r}."
            )
            raise EvaluationError(message)
        selected.append(source_entry)
        seen.add(key)
    return _join_entries(source_prefix, selected, r"\vspace{0.35em}")


def _experience_identity(entry: LatexEntry) -> tuple[str, str]:
    company = entry.title.rsplit("--", 1)[-1].strip()
    return _normalize_title(company), re.sub(r"\s+", " ", entry.date).strip()


def _validate_experience(
    generated_latex: str,
    master_latex: str,
    contract: CvContract,
) -> None:
    if not extract_section(master_latex, contract.experience_section):
        return
    _, source_entries = experience_entries(master_latex, contract=contract)
    if not source_entries:
        return
    _, generated_entries = experience_entries(generated_latex, contract=contract)
    expected = {_experience_identity(entry) for entry in source_entries}
    actual = [_experience_identity(entry) for entry in generated_entries]
    if len(actual) != len(source_entries) or set(actual) != expected:
        raise EvaluationError(
            "Tailored CV must preserve every Master CV experience company and date "
            "exactly once before page-limit handling."
        )


def enforce_master_cv_contract(
    generated_latex: str,
    master_latex: str,
    *,
    contract: CvContract = GERMAN_CV_CONTRACT,
) -> str:
    """Return a tailored CV with all machine-verifiable master rules enforced."""
    updated = _restore_master_prefix(
        generated_latex.strip(), master_latex.strip(), contract
    )
    updated = replace_section(
        updated,
        contract.education_section,
        _protected_education(updated, master_latex, contract),
    )
    if extract_section(master_latex, contract.projects_section):
        updated = replace_section(
            updated,
            contract.projects_section,
            _protected_projects(updated, master_latex, contract),
        )
    language_section = extract_section(master_latex, contract.languages_section)
    if language_section:
        updated = replace_section(
            updated, contract.languages_section, language_section
        )
    _validate_experience(updated, master_latex, contract)
    if "\\end{document}" not in updated:
        raise EvaluationError("Tailored CV is missing \\end{document}.")
    return updated.strip()


def remove_least_relevant_project(
    latex: str,
    *,
    contract: CvContract = GERMAN_CV_CONTRACT,
) -> str:
    """Remove exactly the last (least-relevant) selected project block."""
    prefix, entries = project_entries(latex, contract=contract)
    if len(entries) < 2:
        raise EvaluationError("Cannot remove a project: fewer than two remain.")
    replacement = _join_entries(prefix, entries[:-1], r"\vspace{0.35em}")
    return replace_section(latex, contract.projects_section, replacement)


def remove_least_relevant_experience(
    latex: str,
    *,
    contract: CvContract = GERMAN_CV_CONTRACT,
) -> str:
    """Remove exactly the last (least-relevant) experience block."""
    prefix, entries = experience_entries(latex, contract=contract)
    if len(entries) < 2:
        raise EvaluationError("Cannot remove an experience: fewer than two remain.")
    replacement = _join_entries(prefix, entries[:-1], r"\vspace{0.4em}")
    return replace_section(latex, contract.experience_section, replacement)


def validate_master_cv_structure(
    master_latex: str,
    *,
    contract: CvContract = GERMAN_CV_CONTRACT,
) -> None:
    """Validate that a Master CV exposes every structure required by its contract."""
    required_tokens = (r"\documentclass", r"\begin{document}", r"\end{document}")
    missing_tokens = [token for token in required_tokens if token not in master_latex]
    if missing_tokens:
        raise EvaluationError(
            "Master CV is missing required LaTeX token(s): " + ", ".join(missing_tokens)
        )
    for title in contract.required_sections:
        if not extract_section(master_latex, title):
            raise EvaluationError(f"Master CV is missing required section {title!r}.")
    if ROLE_LINE_RE.search(master_latex) is None:
        raise EvaluationError("Master CV is missing its adaptable header role line.")
    if (
        contract.msc_placeholder not in master_latex
        or contract.bsc_placeholder not in master_latex
    ):
        raise EvaluationError("Master CV is missing relevant-course placeholders.")
    if not _course_pool(master_latex, "MSc") or not _course_pool(master_latex, "BSc"):
        raise EvaluationError(
            "Master CV must contain both embedded course evidence pools."
        )
    _, projects = project_entries(master_latex, contract=contract)
    if len(projects) < 4:
        raise EvaluationError(
            "Master CV must contain at least four selectable projects."
        )
    _, experiences = experience_entries(master_latex, contract=contract)
    if len(experiences) < 2:
        raise EvaluationError("Master CV must contain at least two experience entries.")
