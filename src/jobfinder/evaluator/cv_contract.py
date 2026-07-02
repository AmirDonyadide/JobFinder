"""Structural contract enforcement for tailored LaTeX CVs.

The model may tailor wording where the master prompt allows it, but this module
keeps machine-verifiable content anchored to the Master CV.  Page-limit changes
also happen here as exact block removals, never as free-form rewriting.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from jobfinder.evaluator.models import EvaluationError

SECTION_RE = re.compile(r"(?m)^[ \t]*\\section\*?\{(?P<title>[^}]+)\}")
ROLE_LINE_RE = re.compile(
    r"(?m)^[ \t]*\{\\normalsize\s+.+?\}\\\\(?:\[[^\]]*\])?[ \t]*$"
)
COURSE_LINE_RE = re.compile(
    r"(?m)^(?P<indent>[ \t]*)\\textit\{Relevante Kurse:\}\s*(?P<value>.*?)\s*$"
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

MSC_PLACEHOLDER = "<<MSc RELEVANTE KURSE>>"
BSC_PLACEHOLDER = "<<BSc RELEVANTE KURSE>>"
COURSE_POOL_MARKERS = {
    "MSc": ("JOBFINDER_MSC_COURSE_POOL_BEGIN", "JOBFINDER_MSC_COURSE_POOL_END"),
    "BSc": ("JOBFINDER_BSC_COURSE_POOL_BEGIN", "JOBFINDER_BSC_COURSE_POOL_END"),
}


@dataclass(frozen=True)
class LatexEntry:
    """One top-level project or experience block."""

    title: str
    block: str
    date: str = ""


def _normalize_title(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


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


def project_entries(latex: str) -> tuple[str, list[LatexEntry]]:
    """Return the Projects section prefix and its top-level entries."""
    section = extract_section(latex, "Projekte")
    if not section:
        raise EvaluationError("Tailored CV is missing required section 'Projekte'.")
    return _split_entries(section, PROJECT_START_RE)


def experience_entries(latex: str) -> tuple[str, list[LatexEntry]]:
    """Return the Experience section prefix and its top-level entries."""
    section = extract_section(latex, "Berufserfahrung")
    if not section:
        raise EvaluationError(
            "Tailored CV is missing required section 'Berufserfahrung'."
        )
    return _split_entries(section, EXPERIENCE_START_RE)


def _join_entries(prefix: str, entries: list[LatexEntry], spacing: str) -> str:
    blocks = [entry.block.strip() for entry in entries]
    if not blocks:
        return prefix.strip()
    return prefix.rstrip() + "\n\n" + f"\n\n{spacing}\n\n".join(blocks)


def _course_pool(master_latex: str, level: str) -> tuple[str, ...]:
    begin_marker, end_marker = COURSE_POOL_MARKERS[level]
    pattern = re.compile(
        rf"(?ms)^%\s*{re.escape(begin_marker)}\s*$"
        rf"(?P<body>.*?)"
        rf"^%\s*{re.escape(end_marker)}\s*$"
    )
    match = pattern.search(master_latex)
    if not match:
        return ()
    courses = []
    for line in match.group("body").splitlines():
        value = re.sub(r"^\s*%\s*(?:-\s*)?", "", line).strip()
        if value:
            courses.append(value)
    return tuple(courses)


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


def _protected_education(generated_latex: str, master_latex: str) -> str:
    source = extract_section(master_latex, "Ausbildung")
    generated = extract_section(generated_latex, "Ausbildung")
    if not source or not generated:
        raise EvaluationError(
            "Master or tailored CV is missing the Ausbildung section."
        )

    pools = (_course_pool(master_latex, "MSc"), _course_pool(master_latex, "BSc"))
    generated_lines = list(COURSE_LINE_RE.finditer(generated))
    if all(pools):
        if len(generated_lines) != 2:
            raise EvaluationError(
                "Tailored CV must contain exactly two Relevante Kurse lines."
            )
        msc_value = _validated_course_value(
            generated_lines[0].group("value"), pools[0], "MSc"
        )
        bsc_value = _validated_course_value(
            generated_lines[1].group("value"), pools[1], "BSc"
        )
        if MSC_PLACEHOLDER not in source or BSC_PLACEHOLDER not in source:
            raise EvaluationError("Master CV is missing relevant-course placeholders.")
        source = source.replace(MSC_PLACEHOLDER, msc_value, 1)
        source = source.replace(BSC_PLACEHOLDER, bsc_value, 1)
    return source


def _restore_master_prefix(generated_latex: str, master_latex: str) -> str:
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
        if "Zielposition" in role_line or "Relevantes Stichwort" in role_line:
            raise EvaluationError(
                "Tailored CV left header role placeholders unresolved."
            )
        master_prefix = ROLE_LINE_RE.sub(lambda _: role_line, master_prefix, count=1)

    return master_prefix + "\n\n" + generated_latex[generated_first.start() :].lstrip()


def _protected_projects(generated_latex: str, master_latex: str) -> str:
    source_prefix, source_entries = project_entries(master_latex)
    _, generated_entries = project_entries(generated_latex)
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


def _validate_experience(generated_latex: str, master_latex: str) -> None:
    if not extract_section(master_latex, "Berufserfahrung"):
        return
    _, source_entries = experience_entries(master_latex)
    if not source_entries:
        return
    _, generated_entries = experience_entries(generated_latex)
    expected = {_experience_identity(entry) for entry in source_entries}
    actual = [_experience_identity(entry) for entry in generated_entries]
    if len(actual) != len(source_entries) or set(actual) != expected:
        raise EvaluationError(
            "Tailored CV must preserve every Master CV experience company and date "
            "exactly once before page-limit handling."
        )


def enforce_master_cv_contract(generated_latex: str, master_latex: str) -> str:
    """Return a tailored CV with all machine-verifiable master rules enforced."""
    updated = _restore_master_prefix(generated_latex.strip(), master_latex.strip())
    updated = replace_section(
        updated,
        "Ausbildung",
        _protected_education(updated, master_latex),
    )
    if extract_section(master_latex, "Projekte"):
        updated = replace_section(
            updated,
            "Projekte",
            _protected_projects(updated, master_latex),
        )
    language_section = extract_section(master_latex, "Sprachen")
    if language_section:
        updated = replace_section(updated, "Sprachen", language_section)
    _validate_experience(updated, master_latex)
    if "\\end{document}" not in updated:
        raise EvaluationError("Tailored CV is missing \\end{document}.")
    return updated.strip()


def remove_least_relevant_project(latex: str) -> str:
    """Remove exactly the last (least-relevant) selected project block."""
    prefix, entries = project_entries(latex)
    if len(entries) < 2:
        raise EvaluationError("Cannot remove a project: fewer than two remain.")
    replacement = _join_entries(prefix, entries[:-1], r"\vspace{0.35em}")
    return replace_section(latex, "Projekte", replacement)


def remove_least_relevant_experience(latex: str) -> str:
    """Remove exactly the last (least-relevant) experience block."""
    prefix, entries = experience_entries(latex)
    if len(entries) < 2:
        raise EvaluationError("Cannot remove an experience: fewer than two remain.")
    replacement = _join_entries(prefix, entries[:-1], r"\vspace{0.4em}")
    return replace_section(latex, "Berufserfahrung", replacement)


def validate_master_cv_structure(master_latex: str) -> None:
    """Validate that a Master CV exposes every structure required by the contract."""
    required_tokens = (r"\documentclass", r"\begin{document}", r"\end{document}")
    missing_tokens = [token for token in required_tokens if token not in master_latex]
    if missing_tokens:
        raise EvaluationError(
            "Master CV is missing required LaTeX token(s): " + ", ".join(missing_tokens)
        )
    for title in ("Profil", "Ausbildung", "Berufserfahrung", "Projekte", "Sprachen"):
        if not extract_section(master_latex, title):
            raise EvaluationError(f"Master CV is missing required section {title!r}.")
    if ROLE_LINE_RE.search(master_latex) is None:
        raise EvaluationError("Master CV is missing its adaptable header role line.")
    if MSC_PLACEHOLDER not in master_latex or BSC_PLACEHOLDER not in master_latex:
        raise EvaluationError("Master CV is missing relevant-course placeholders.")
    if not _course_pool(master_latex, "MSc") or not _course_pool(master_latex, "BSc"):
        raise EvaluationError(
            "Master CV must contain both embedded course evidence pools."
        )
    _, projects = project_entries(master_latex)
    if len(projects) < 4:
        raise EvaluationError(
            "Master CV must contain at least four selectable projects."
        )
    _, experiences = experience_entries(master_latex)
    if len(experiences) < 2:
        raise EvaluationError("Master CV must contain at least two experience entries.")
