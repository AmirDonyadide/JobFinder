# Tests

Tests mirror the package structure so each product or shared subsystem is easy
to find. The suite never calls Apify, Google, or OpenAI over the network.

## Prerequisites

- Python 3.14 or newer.
- The `all` and `dev` dependency groups from `pyproject.toml`.
- No real API keys are required.

## Quick Start

```bash
python -m pip install -e ".[all,dev]"
python -m pytest
```

Run all tests:

```bash
python -m pytest
```

Run CI-equivalent checks from the repository root:

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m compileall src tests scripts
python -m json.tool products/jobfinder/config/filters.json
python -m json.tool products/phdfinder/config/filters.json
python -m pytest
```

## Layout

| Directory | Coverage |
|---|---|
| `products/` | Product aliases, isolated paths, and the legacy profile facade. |
| `providers/` | Indeed, LinkedIn, Stepstone, and Xing adapters. |
| `scraper/` | Configuration, settings, search, filters, normalization, export, history, and smoke payloads. |
| `dedupe/` | Cross-provider identity, blockers, provenance, and merge behavior. |
| `evaluator/` | CLI parsing, OpenAI orchestration, storage, CV contracts, and PDF output. |
| `pipeline/` | Pipeline CLI modes, preflight requirements, and resume behavior. |
| `integrations/` | Shared Google authentication and service construction. |
| `operations/` | CI secret validation, runtime-file preparation, and manifest-scoped cleanup. |

## External Service Strategy

Tests use:

- Simple fake response/service classes.
- `monkeypatch` for HTTP clients and provider runners.
- Temporary files for Excel and config tests.
- No real credentials.
- No network calls.

If a new test needs network access, prefer adding a fake adapter seam instead.

## Use This For Your Own Project

Forks should keep the suite network-free and update tests alongside any
user-facing behavior change.

| Fork change | Update or run |
|---|---|
| New provider or actor payload | Provider-specific test plus `scraper/test_search.py`. |
| New spreadsheet column | `scraper/test_export_rows.py`, `evaluator/test_parsing.py`, and `evaluator/test_storage.py`. |
| New config key or default | `scraper/test_config_files.py`, `scraper/test_settings.py`, and related docs. |
| New workflow secret or mode | `pipeline/test_cli.py`, `operations/test_runtime_files.py`, and `.github/workflows/README.md`. |
| New evaluator output format | `evaluator/test_parsing.py` and `evaluator/test_openai_client.py`. |

## Focused Test Guidance

| Change area | Suggested tests |
|---|---|
| Provider payload/normalization | `providers/` plus `scraper/test_search.py`. |
| Dedupe identity | `dedupe/test_matching.py`, `scraper/test_run_history.py`. |
| Spreadsheet schema | `scraper/test_export_rows.py`, `evaluator/test_parsing.py`, `evaluator/test_storage.py`. |
| Evaluator prompt or parsing | `evaluator/test_parsing.py`, `evaluator/test_openai_client.py`. |
| CV PDF output | `evaluator/test_cv_pdf_output.py`, `evaluator/test_storage.py`. |
| Pipeline/GitHub settings | `pipeline/test_cli.py`, `scraper/test_settings.py`, `operations/test_runtime_files.py`. |

## Maintaining Tests

- Keep tests deterministic and free of real secrets.
- Prefer small representative provider payloads over large captured fixtures.
- When changing column names, update scraper, evaluator, and schema tests
  together.
- When changing defaults, update `.env.example`, docs, and tests together.

## Troubleshooting

| Problem | What to check |
|---|---|
| `No module named 'jobfinder'` | Run tests from the repository root, or install with `python -m pip install -e ".[all]"`. |
| Ruff, mypy, or pytest is missing | Run `python -m pip install -e ".[all,dev]"`. |
| Tests unexpectedly hit real services | Replace the network call with a fake or monkeypatch; tests should not require Apify, Google, or OpenAI credentials. |
| Config tests fail after editing filters | Validate `products/jobfinder/config/filters.json` with `python -m json.tool products/jobfinder/config/filters.json`. |
