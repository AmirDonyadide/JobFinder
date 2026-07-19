# JobFinder & PhDFinder

**Two focused search products powered by one shared, tested finder engine.**

[![Python](https://img.shields.io/badge/python-3.14%2B-blue.svg)](https://www.python.org/)
[![CI](https://github.com/AmirDonyadide/JobFinder/actions/workflows/ci.yml/badge.svg)](https://github.com/AmirDonyadide/JobFinder/actions/workflows/ci.yml)
[![License: Non-Commercial](https://img.shields.io/badge/license-Non--Commercial-orange.svg)](LICENSE)

🌐 **[Project website](https://amirdonyadide.github.io/JobFinder/)** ·
📚 **[Documentation](docs/)** ·
🧭 **[Products](products/)**

This repository automates two related searches without maintaining two copies
of the same pipeline:

| Product | Finds | Configuration | Command |
|---|---|---|---|
| **[JobFinder](products/jobfinder/)** | General employment opportunities | `products/jobfinder/` | `jobfinder` |
| **[PhDFinder](products/phdfinder/)** | PhD and academic-research opportunities | `products/phdfinder/` | `phdfinder` |

Both products search LinkedIn, Indeed, Stepstone, and Xing through Apify,
normalize results, remove duplicates, apply product-specific filters, and export
to Excel or Google Sheets. Optional OpenAI evaluation scores each result against
the matching product's private Master CV and can generate tailored CV PDFs.

## Architecture

```text
products/jobfinder ─┐
                    ├──> shared engine in src/jobfinder ──> isolated outputs
products/phdfinder ─┘
```

The products share implementation but never share private keywords, prompts,
CVs, spreadsheet history, Excel output, generated-CV Drive folders, or workflow
reports.

The shared engine owns:

- Apify and provider adapters
- Search orchestration and retry behavior
- Normalization, deterministic deduplication, and filters
- Excel and Google Sheets exports
- OpenAI evaluation and LaTeX PDF generation
- Pipeline preflight, resume behavior, and operational reports

## Quick start

Python 3.14 or newer is required.

```bash
git clone https://github.com/AmirDonyadide/JobFinder.git
cd JobFinder
python -m pip install -e ".[all]"
cp .env.example .env
```

Choose one product and create its private files.

### JobFinder

```bash
cp products/jobfinder/config/keywords.example.txt products/jobfinder/config/keywords.txt
cp products/jobfinder/evaluator/master_prompt.example.txt products/jobfinder/evaluator/master_prompt.txt
cp products/jobfinder/evaluator/master_cv.example.tex products/jobfinder/evaluator/master_cv.tex
jobfinder --preflight
```

### PhDFinder

```bash
cp products/phdfinder/config/keywords.example.txt products/phdfinder/config/keywords.txt
cp products/phdfinder/evaluator/master_prompt.example.txt products/phdfinder/evaluator/master_prompt.txt
cp products/phdfinder/evaluator/master_cv.example.tex products/phdfinder/evaluator/master_cv.tex
phdfinder --preflight
```

Add the required API credentials to `.env`, then run:

```bash
jobfinder --mode scrape_only
jobfinder --mode scrape_and_evaluate

phdfinder --mode scrape_only
phdfinder --mode scrape_and_evaluate
```

The more focused compatibility commands remain available:

```bash
jobfinder-scrape
jobfinder-evaluate
jobfinder-pipeline
```

## Repository map

```text
products/                    # product-owned configuration and examples
  jobfinder/
  phdfinder/
src/jobfinder/               # shared engine
tests/                       # unit, integration, and product-isolation tests
scripts/                     # optional live provider smoke checks
docs/                        # user, operations, and architecture guides
.github/workflows/           # CI and isolated product workflows
```

Generated outputs, credentials, tokens, private search terms, private prompts,
and private CVs are ignored by Git. Do not commit them.

## GitHub Actions

- **JobFinder Pipeline** runs manually or on its configured daily schedule.
- **PhDFinder Pipeline** is manual-only until its separate schedule is enabled.
- Both use the same tested CI runtime-file preparation code while keeping
  secrets, reports, artifacts, spreadsheet IDs, and concurrency groups separate.

See [Run with GitHub Actions](docs/run-github-actions.md) and the
[workflow reference](.github/workflows/README.md).

## Documentation

- [Documentation index](docs/README.md)
- [JobFinder product guide](products/jobfinder/README.md)
- [PhDFinder product guide](products/phdfinder/README.md)
- [Local setup](docs/run-local.md)
- [GitHub Actions setup](docs/run-github-actions.md)
- [Usage](docs/usage.md)
- [Configuration](docs/configuration.md)
- [How it works](docs/how-it-works.md)
- [Architecture](docs/architecture.md)
- [Developer guide](docs/developer-guide.md)
- [Troubleshooting](docs/troubleshooting.md)

## Development

Install all runtime and development extras, then run the same checks as CI:

```bash
python -m pip install -e ".[all,dev]"
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m pytest
```

## Status and license

The project is early-stage (`v0.1.0`) and actively developed. It uses a custom
non-commercial license: personal, educational, and other non-commercial use is
allowed; commercial use requires separate written permission. See [LICENSE](LICENSE).
