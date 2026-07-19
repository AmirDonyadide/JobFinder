# Contributing

Thanks for improving JobFinder and PhDFinder! Feedback, ideas, and pull requests are all
welcome. The project aims to stay small enough that someone can read it in one
sitting, so please keep changes focused and easy to reason about.

## Quick setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[all,dev]"
cp .env.example .env
```

Add your own `APIFY_API_TOKEN` to `.env` before running the scraper.

## Before you commit

Run the same checks as CI:

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m pytest
```

## Where things live

| Change | Where |
|---|---|
| Change product search terms | The selected `products/<product>/config/keywords.txt` |
| Change product filters | The selected `products/<product>/config/filters.json` |
| Change shared behavior | The owning module under `src/jobfinder/` plus tests |
| Tune speed or timeouts | `.env` or GitHub Actions environment variables |
| Change default local settings | `.env.example` |
| Explain user-facing behavior | `README.md` and the relevant guide in `docs/` |

## Full details

The complete contributor reference — project layout, testing strategy, and
extension points — lives in the **[Developer guide](docs/developer-guide.md)**.

By contributing, you agree to the contribution terms in the [LICENSE](LICENSE).
