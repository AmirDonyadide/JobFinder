# Examples & Common Workflows

Ready-to-copy commands for typical situations. These assume you have installed
JobFinder and created your private config files (see the
[Local guide](run-local.md)).

Back to the [project overview](../README.md) · [Usage guide](usage.md) ·
[Configuration reference](configuration.md).

## Try it with zero cloud setup

Scrape LinkedIn to a local Excel file. Only an Apify token is required.

```bash
JOBFINDER_SCRAPER_OUTPUT_MODE=excel JOBFINDER_SCRAPER_SOURCES=linkedin python linkedin_job_scraper.py
```

Open the resulting `jobs.xlsx`.

## Check everything before a real run

Preflight validates settings, credentials, and Google access without spending
any API credits.

```bash
python run_job_pipeline.py --mode scrape_only --preflight
```

## Collect jobs from every board into Google Sheets

```bash
JOBFINDER_SCRAPER_SOURCES=all python run_job_pipeline.py --mode scrape_only
```

A new dated tab appears in your configured Google Sheet.

## Full daily run: scrape + AI scoring + CV PDFs

```bash
python run_job_pipeline.py --mode scrape_and_evaluate
```

This scrapes to Google Sheets, scores each new job with OpenAI, and writes a
tailored CV PDF link into the `AI CV PDF` column.

## Re-score a sheet without scraping again

Useful after editing your prompt or CV.

```bash
python job_fit_evaluator.py --source google_sheets --sheet latest
```

> The evaluator skips rows that already have an `AI Verdict` (unless it is
> `Error`). To force a re-score, clear those cells first or use a fresh tab.

## Keep every rejected row (for prompt tuning)

By default the final sheet drops most `Not Suitable` rows. Keep them all while
you tune your prompt:

```bash
JOB_EVAL_UNSUITABLE_ROW_POLICY=keep_all python job_fit_evaluator.py --source google_sheets --sheet latest
```

## Debug with low concurrency

Slower, but easier to read in the terminal and gentler on provider rate limits.

```bash
JOBFINDER_SCRAPER_SEARCH_CONCURRENCY=2 JOBFINDER_SCRAPER_OUTPUT_MODE=excel python linkedin_job_scraper.py
```

## Search a single Stepstone or Xing URL

Both boards support a "direct URL" mode: instead of one search per keyword, they
run one search for the exact URL you provide.

```bash
# Stepstone
JOBFINDER_SCRAPER_SOURCES=stepstone \
  STEPSTONE_START_URLS="https://www.stepstone.de/jobs/software" \
  python linkedin_job_scraper.py

# Xing
JOBFINDER_SCRAPER_SOURCES=xing \
  XING_START_URL="https://www.xing.com/jobs/t-remote?keywords=Remote&location=Germany" \
  python linkedin_job_scraper.py
```

## Backfill an empty spreadsheet

For a first run with no history, remove the posting-date filter so you collect a
wide initial batch.

```bash
JOBFINDER_SCRAPER_POSTED_TIME_WINDOW=backfill python run_job_pipeline.py --mode scrape_only
```

Switch back to `since_previous_run` for routine daily runs.

## Scheduled runs without your laptop

To run JobFinder automatically every day, use GitHub Actions instead of your
machine. See the [GitHub Actions guide](run-github-actions.md).
