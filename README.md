# JobFinder

**Find relevant jobs automatically — scraped from multiple job boards, de-duplicated, and (optionally) scored by AI against your CV.**

[![Python](https://img.shields.io/badge/python-3.14%2B-blue.svg)](https://www.python.org/)
[![CI](https://github.com/AmirDonyadide/JobFinder/actions/workflows/ci.yml/badge.svg)](https://github.com/AmirDonyadide/JobFinder/actions/workflows/ci.yml)
[![License: Non-Commercial](https://img.shields.io/badge/license-Non--Commercial-orange.svg)](LICENSE)

🌐 **[Project website](https://amirdonyadide.github.io/JobFinder/)** · 📚 **[Documentation](docs/)** · 🚀 **[Quick Start](docs/quick-start.md)**

> The website source lives on the [`website` branch](https://github.com/AmirDonyadide/JobFinder/tree/website) and is published with GitHub Pages.

JobFinder turns a repetitive job search into a repeatable, automated workflow. It
collects fresh postings from **LinkedIn, Indeed, Stepstone, and Xing**, removes
duplicates, filters out the noise, and saves the results to **Excel or Google
Sheets**. If you want, it then asks **OpenAI** to score each job against your own
CV and generate a tailored CV PDF for the good matches.

You can run it once from your laptop, or let **GitHub Actions** run it for you on
a daily schedule — no computer required.

---

## Table of Contents

- [Why JobFinder?](#why-jobfinder)
- [Who is it for?](#who-is-it-for)
- [What it does](#what-it-does)
- [How it works](#how-it-works)
- [Quick start](#quick-start)
- [A first run](#a-first-run)
- [Documentation](#documentation)
- [Requirements](#requirements)
- [Project status & license](#project-status--license)
- [Contributing](#contributing)

## Why JobFinder?

Searching several job boards by hand is slow and repetitive. You re-run the same
queries, scroll past jobs you have already seen, and re-read the same postings to
decide whether they fit. JobFinder does that work for you and keeps everything in
one tidy spreadsheet.

- **One search, many boards.** Search LinkedIn, Indeed, Stepstone, and Xing in a single run.
- **No duplicates.** The same job posted on several boards is merged into one row.
- **Only new jobs.** On scheduled runs it can fetch only what was posted since your last run.
- **Optional AI scoring.** Get a fit score, a verdict, and a tailored CV PDF for promising roles.
- **Runs where you want.** On your machine for quick experiments, or on GitHub Actions on a schedule.

## Who is it for?

- **Job seekers** who want a daily, filtered shortlist instead of manual searching.
- **People who like spreadsheets** — results land in Excel or Google Sheets, ready to sort and track.
- **Developers and tinkerers** who want a clean, well-tested Python pipeline they can fork and extend.

> JobFinder is configured with **your own** keywords, filters, prompt, and CV.
> Those private files stay on your machine or in GitHub secrets — they are never committed.

## What it does

| Step | What happens |
|---|---|
| **1. Scrape** | Runs job-board scrapers (via [Apify](https://apify.com/) actors) for each of your keywords. |
| **2. Normalize** | Converts each board's output into one consistent set of columns. |
| **3. De-duplicate** | Merges the same job found across keywords and boards — no AI, fully deterministic. |
| **4. Filter** | Drops jobs by excluded titles, excluded companies, applicant count, and posting date. |
| **5. Export** | Writes a timestamped sheet to Excel, Google Sheets, or both. |
| **6. Evaluate** *(optional)* | Scores each new job with OpenAI, writes a verdict and a fit score, and builds a tailored CV PDF. |

## How it works

```
keywords + filters
        │
        ▼
   ┌─────────┐   ┌───────────┐   ┌────────┐   ┌─────────┐   ┌──────────────────┐
   │ Scrape  │──▶│ De-dupe & │──▶│ Export │──▶│ (opt.)  │──▶│ Excel / Google   │
   │ 4 boards│   │  filter   │   │ sheet  │   │ AI score│   │ Sheets + CV PDFs │
   └─────────┘   └───────────┘   └────────┘   └─────────┘   └──────────────────┘
```

Want the full picture? See [How it works](docs/how-it-works.md) and the
[Architecture notes](docs/architecture.md).

## Quick start

There are two ways to run JobFinder. Pick the one that fits you.

### Option A — No coding (recommended for most people)

Fork the repository, add a few secrets, and press **Run** on GitHub. GitHub does
the rest, including an optional daily schedule.

➡️ Follow the **[Quick Start guide](docs/quick-start.md)**.

### Option B — Run it on your own machine

```bash
# 1. Clone and enter the project
git clone https://github.com/AmirDonyadide/JobFinder.git
cd JobFinder

# 2. Install it (a Python 3.14+ environment is recommended)
python -m pip install -e .

# 3. Create your private config files from the examples
cp .env.example .env
cp configs/keywords.example.txt configs/keywords.txt
cp prompts/master_prompt.example.txt prompts/master_prompt.txt
cp cv/master_cv.example.tex cv/master_cv.tex
```

Add your `APIFY_API_TOKEN` to `.env`, put your search terms in
`configs/keywords.txt`, then continue with the **[Local guide](docs/run-local.md)**.

## A first run

Once installed, the quickest thing to try is a **local Excel scrape** (no Google
account or OpenAI key needed — just an Apify token):

```bash
JOBFINDER_SCRAPER_OUTPUT_MODE=excel python linkedin_job_scraper.py
```

This writes the matching jobs to `jobs.xlsx`.

Ready for the full experience? The pipeline scrapes to Google Sheets and then
scores everything with AI:

```bash
# Check your setup without spending any API credits
python run_job_pipeline.py --preflight

# Scrape to Google Sheets, then evaluate with OpenAI
python run_job_pipeline.py --mode scrape_and_evaluate
```

See the [Usage guide](docs/usage.md) for every command and option, and the
[Examples](docs/examples.md) for ready-to-copy workflows.

## Documentation

JobFinder's documentation is split into short, focused guides so you only read
what you need.

**Getting started**

- 🚀 [Quick Start](docs/quick-start.md) — fork it and run on GitHub, no coding.
- 💻 [Run locally](docs/run-local.md) — install and run from your own machine.
- ☁️ [Run on GitHub Actions](docs/run-github-actions.md) — scheduled, hands-off runs.

**Using it**

- 📖 [Usage guide](docs/usage.md) — commands, run modes, and output columns.
- 🧩 [Examples & common workflows](docs/examples.md) — copy-paste recipes.
- ⚙️ [Configuration reference](docs/configuration.md) — every setting and config file.
- 🛟 [Troubleshooting](docs/troubleshooting.md) — fixes for common errors.

**Going deeper**

- 🔍 [How it works](docs/how-it-works.md) — the scraping, dedupe, and evaluation flow.
- 🏗️ [Architecture](docs/architecture.md) — module boundaries and design notes.
- 🛠️ [Developer guide](docs/developer-guide.md) — set up, test, and extend the code.
- 📦 Package internals — each `src/jobfinder/*/README.md` documents its own module.

## Requirements

- **Python 3.14+**.
- An **Apify API token** (required for all scraping).
- For AI scoring and the full pipeline: an **OpenAI API key** and **Google OAuth**
  access (the same Google account is used for Sheets and Drive).
- For tailored CV PDFs: **LaTeX** tooling (`latexmk` and `xelatex`).

Local Excel-only runs need just Python and an Apify token. Full setup is covered
in the [Local guide](docs/run-local.md).

## Project status & license

JobFinder is an early-stage (`v0.1.0`), actively developed personal project.
Interfaces and configuration may still change between versions.

It is released under a **custom non-commercial license**: you are free to view,
run, modify, and share it for **personal, educational, and other non-commercial
purposes**. **Commercial use is not permitted** without a separate written
license. Please read the full [LICENSE](LICENSE) before using it.

## Contributing

Feedback, ideas, and pull requests are welcome. Start with the
[Developer guide](docs/developer-guide.md) and the short
[Contributing notes](CONTRIBUTING.md).
