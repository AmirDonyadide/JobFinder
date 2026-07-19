# Developer Guide

Everything you need to set up, test, and extend the shared finder engine. For the high-level
design, read [How it works](how-it-works.md) and the
[Architecture notes](architecture.md). For day-to-day usage, see the
[Usage guide](usage.md).

Back to the [project overview](../README.md).

## Table of contents

- [Local setup](#local-setup)
- [Project layout](#project-layout)
- [Checks before you commit](#checks-before-you-commit)
- [Testing strategy](#testing-strategy)
- [Extension points](#extension-points)
- [Change guidelines](#change-guidelines)

## Local setup

This repository uses a `src/` layout, so an **editable install** is the
recommended setup — it puts the `jobfinder` package on your path so commands like
`python -m jobfinder.google_auth` work from a fresh clone.

```bash
# Create an environment (conda shown; a venv works too)
conda create -n JobFinder python=3.14 -y
conda activate JobFinder
python -m pip install --upgrade pip

# Install the package, all integrations, and development tools
python -m pip install -e ".[all,dev]"

# Create your local config
cp .env.example .env
```

Add your `APIFY_API_TOKEN` to `.env` before running the scraper.

After the editable install, these console scripts are available:

```bash
jobfinder-pipeline --help
jobfinder --help
phdfinder --help
jobfinder-scrape --help
jobfinder-evaluate --help
```

If you would rather not install the package, set `PYTHONPATH=src` for direct
module execution:

```bash
jobfinder --help
env PYTHONPATH=src python -m jobfinder.pipeline.cli --help
```

For CV PDF generation you also need LaTeX. On Ubuntu / GitHub Actions:

```bash
sudo apt-get install -y latexmk texlive-xetex texlive-latex-extra
```

On macOS, install a TeX distribution that includes `latexmk` and `xelatex` (such
as MacTeX).

## Project layout

```text
JobFinder/
├── .github/workflows/      # CI plus isolated product workflows
├── products/
│   ├── jobfinder/          # JobFinder config, prompt, and CV examples
│   └── phdfinder/          # PhDFinder config, prompt, and CV examples
├── scripts/                # optional live provider smoke checks
├── src/jobfinder/          # the package (see module READMEs below)
│   ├── core/               # cross-cutting helpers (logging)
│   ├── providers/          # board adapters, Apify client, provider registry
│   ├── scraper/            # search, filters, exports, run history
│   ├── dedupe/             # deterministic duplicate matching + merge
│   ├── evaluator/          # OpenAI evaluation, parsing, storage, PDF output
│   ├── spreadsheet/        # shared column contracts
│   ├── pipeline/           # multi-step CLI and preflight
│   ├── operations/         # CI report helpers
│   └── integrations/google/# Google credentials, Sheets, Drive
└── tests/                  # pytest suite (no live network calls)
```

Each package documents itself:

| Module README | Covers |
|---|---|
| [`src/jobfinder/README.md`](../src/jobfinder/README.md) | Package map, boundaries, entry points. |
| [`src/jobfinder/scraper/README.md`](../src/jobfinder/scraper/README.md) | Scraper execution, settings, exports. |
| [`src/jobfinder/providers/README.md`](../src/jobfinder/providers/README.md) | Provider adapter contracts. |
| [`src/jobfinder/dedupe/README.md`](../src/jobfinder/dedupe/README.md) | Matching and merge design. |
| [`src/jobfinder/evaluator/README.md`](../src/jobfinder/evaluator/README.md) | Evaluation pipeline and storage. |
| [`src/jobfinder/pipeline/README.md`](../src/jobfinder/pipeline/README.md) | One-step pipeline and preflight. |
| [`products/README.md`](../products/README.md) | Product ownership and isolation. |
| [`.github/workflows/README.md`](../.github/workflows/README.md) | CI and production workflow behavior. |
| [`tests/README.md`](../tests/README.md) | Test-suite map and guidance. |

## Checks before you commit

Run the same checks as CI:

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m compileall src tests scripts
python -m json.tool products/jobfinder/config/filters.json
python -m json.tool products/phdfinder/config/filters.json
python -m pytest
```

Useful focused test runs:

```bash
python -m pytest tests/scraper/test_search.py
python -m pytest tests/dedupe/test_matching.py
python -m pytest tests/evaluator/test_storage.py
python -m pytest tests/pipeline/test_cli.py
```

For documentation-only changes, read the rendered Markdown and confirm that
commands and environment-variable names match the code.

## Testing strategy

The suite avoids real Apify, Google, and OpenAI calls by using fakes and
monkeypatching. Coverage focuses on:

- Config loading and settings coercion.
- Provider payload construction and normalization.
- Apify retry, timeout, token fallback, and concurrency behavior.
- Cross-board dedupe identity rules.
- Google Sheets run history and the hidden seen-job index.
- Spreadsheet row generation and cleanup.
- Evaluator parsing, OpenAI orchestration, incremental saves, and row policy.
- Pipeline mode and secret validation.

Before changing dedupe, provider normalization, the spreadsheet schema, or
evaluator cleanup, run the relevant focused tests **plus** the full suite.

## Extension points

| Change | Start here |
|---|---|
| Add a job board | `providers/`, `scraper/search.py`, `scraper/settings.py`, provider tests. |
| Change output columns | `spreadsheet/schema.py`, exporters, evaluator parsing/storage, docs, tests. |
| Tune dedupe identity | `dedupe/normalize.py`, `dedupe/scoring.py`, `dedupe/matching.py`, `tests/dedupe/test_matching.py`. |
| Change evaluator parsing | `evaluator/parsing.py`, `evaluator/models.py`, evaluator tests. |
| Change production scheduling | `.github/workflows/jobfinder.yml` and its README. |

New providers register a `ProviderAdapter` in `providers/registry.py`. Column
changes start in `spreadsheet/schema.py`, then flow into exporters, evaluator
parsing/storage, tests, and docs together.

## Change guidelines

- Keep changes small and easy to reason about.
- Preserve existing input/output columns unless docs and downstream users are updated together.
- Keep `.env.example` in sync with supported environment variables.
- Prefer `.env` for tuning, `products/jobfinder/config/keywords.txt` for search terms, and `products/jobfinder/config/filters.json` for search/filter words.
- Never commit tokens, Google credential files, generated workbooks, or local spreadsheet IDs.
- If you change deduplication, date parsing, or export formatting, add a short manual smoke-test note to the pull request.

See the short [Contributing notes](../CONTRIBUTING.md) for the contribution
summary and the [LICENSE](../LICENSE) for contribution terms.
