# Usage Guide

This guide covers how to run JobFinder and PhDFinder day to day: commands, run modes,
and what the output looks like. For installation, see the
[Local guide](run-local.md). For every setting, see the
[Configuration reference](configuration.md).

Back to the [project overview](../README.md).

## Table of contents

- [The two ways to run](#the-two-ways-to-run)
- [The pipeline (recommended)](#the-pipeline-recommended)
- [The scraper on its own](#the-scraper-on-its-own)
- [The evaluator on its own](#the-evaluator-on-its-own)
- [Choosing job boards](#choosing-job-boards)
- [Choosing where results go](#choosing-where-results-go)
- [Choosing how far back to search](#choosing-how-far-back-to-search)
- [Output columns](#output-columns)
- [Where to find your results](#where-to-find-your-results)

## The two ways to run

The repository provides two product commands and two focused shared-engine
commands:

| Command | What it does |
|---|---|
| `jobfinder` | Run the JobFinder product pipeline. |
| `phdfinder` | Run the PhDFinder product pipeline. |
| `jobfinder-scrape` | Run only the shared scraper for the selected product. |
| `jobfinder-evaluate` | Evaluate an already-scraped product output. |

Install the commands with `python -m pip install -e ".[all]"`. Direct module
execution remains available with `PYTHONPATH=src` for development.

## The pipeline (recommended)

The pipeline runs the scraper, then the evaluator, in one command. It always
writes to **Google Sheets**, because the evaluator reads the sheet it just
created.

```bash
jobfinder --help
```

| Option | What it does |
|---|---|
| `--mode scrape_only` | Scrape jobs to Google Sheets and stop. |
| `--mode scrape_and_evaluate` | Scrape, then score every new row with OpenAI. Resumes an unfinished same-day tab instead of scraping again. |
| `--preflight` | Validate your settings, credentials, and Google access **without** running anything or spending API credits. |
| `--product jobs` / `--product phd` | Select the JobFinder or PhDFinder configuration and state. |

```bash
# Always safe to run first — checks your setup
jobfinder --preflight

# Collect jobs only
jobfinder --mode scrape_only

# Full run: collect + AI scoring + tailored CV PDFs
jobfinder --mode scrape_and_evaluate
```

When `--mode` is omitted, the pipeline uses `JOBFINDER_PIPELINE_MODE` (default
`scrape_and_evaluate`).

For academic roles, `phdfinder` selects the isolated PhDFinder product. The
historical `jobfinder-pipeline --profile phd` form remains compatible. See the
[PhDFinder guide](phdfinder.md).

## The scraper on its own

The scraper is primarily configured through environment variables and config
files. Its `--product` option selects the JobFinder or PhDFinder inputs. This is
the tool to use for **local Excel output**.

```bash
# Uses JOBFINDER_SCRAPER_OUTPUT_MODE / SOURCES from your .env
jobfinder-scrape

# Or set them inline for a one-off run
JOBFINDER_SCRAPER_OUTPUT_MODE=excel JOBFINDER_SCRAPER_SOURCES=linkedin jobfinder-scrape
```

## The evaluator on its own

Use the evaluator to score a sheet that already exists (for example, to re-run AI
scoring without scraping again).

```bash
jobfinder-evaluate --help
```

| Option | What it does |
|---|---|
| `--source` | Where to read jobs from: `excel`, `xlsx`, `local`, `google`, `google_sheets`, `sheets`, or `drive`. |
| `--sheet` | The worksheet/tab to evaluate. Defaults to `JOB_EVAL_SHEET` or `latest`. |
| `--google-sheet-id` | A one-off spreadsheet ID for this run. |

```bash
# Score the newest Google Sheet tab
jobfinder-evaluate --source google_sheets --sheet latest

# Score the newest local Excel worksheet
jobfinder-evaluate --source excel --sheet latest
```

If `--source` is omitted, the evaluator chooses Google Sheets when a spreadsheet
ID is configured, otherwise Excel.

## Choosing job boards

Set `JOBFINDER_SCRAPER_SOURCES` to one board, a list, or `all`:

| Value | Boards searched |
|---|---|
| `linkedin` | LinkedIn only |
| `indeed` | Indeed only |
| `stepstone` | Stepstone only |
| `xing` | Xing only |
| `all` | LinkedIn, Indeed, Stepstone, and Xing |
| `linkedin,stepstone,xing` | Any explicit comma-separated list |

## Choosing where results go

Set `JOBFINDER_SCRAPER_OUTPUT_MODE`:

| Value | Output |
|---|---|
| `excel` | A local `jobs.xlsx` workbook (default for the scraper). |
| `google_sheets` | A new timestamped tab in your Google Sheet. |
| `both` | Excel **and** Google Sheets. |

> The full pipeline always forces `google_sheets`, regardless of this setting.

## Choosing how far back to search

Set `JOBFINDER_SCRAPER_POSTED_TIME_WINDOW`:

| Value | Meaning |
|---|---|
| `since_previous_run` | Only jobs newer than your last run (best for daily/scheduled use). |
| `last_24h` | Jobs posted in the last 24 hours. |
| `last_7d` | Jobs posted in the last 7 days. |
| `backfill` | No posting-date filter — fetch everything the boards return. |

`since_previous_run` works best with Google Sheets, because the cutoff comes from
the newest posting date already in your spreadsheet.

## Output columns

Each run produces a sheet with a stable set of columns:

| Column | Description |
|---|---|
| `Application Status` | Empty, or a Google Sheets dropdown you can fill in. |
| `App` | Which board(s) the job came from, e.g. `LinkedIn \| Indeed`. |
| `Job Title` | Normalized job title. |
| `Company` | Normalized company name. |
| `Location` | Normalized location. |
| `Job Type` | Employment type, when available. |
| `Job Description` | Source text used for evaluation; removed after AI cleanup. |
| `Posted` | Parsed posting date/time, when available. |
| `Applicants` | Applicant count, when the board reports it. |
| `Keywords Matched` | Which of your keywords returned this job. |
| `Job URL` | Link to the posting. |
| `Apply URL` | Link to the external application page, when available. |
| `AI Verdict` | Filled by the evaluator (e.g. suitable / not suitable). |
| `AI Fit Score` | Evaluator score on a 0–20 rubric; 11–20 is suitable unless a hard rejection applies. |
| `AI Unsuitable Reasons` | Why a rejected job was not a fit. |
| `AI CV PDF` | Google Drive link to the tailored CV PDF, or an error for that row. |

The evaluator also uses a temporary `AI Tailored CV` column, which is removed
during final cleanup when PDF output is enabled.

## Where to find your results

- **Excel runs** write `jobs.xlsx` in the project folder.
- **Google Sheets runs** add a new dated tab to your configured spreadsheet.
- **Pipeline runs** evaluate the newest tab in place, adding the `AI …` columns.
- Evaluations are saved **as each row finishes**, so a later failure keeps the
  rows already completed.
- By default, the final sheet keeps only one-label `Not Suitable` rows. Set
  `JOB_EVAL_UNSUITABLE_ROW_POLICY=keep_all` to keep every evaluated row.

Next: see the [Examples](examples.md) for common end-to-end recipes.
