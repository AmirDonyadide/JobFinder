# Configuration Reference

Every JobFinder setting in one place. Most people only need a handful of these —
start with the [Local guide](run-local.md) or [Quick Start](quick-start.md), and
come here when you want to fine-tune a run.

Back to the [project overview](../README.md) · [Usage guide](usage.md).

## How settings are resolved

JobFinder reads settings from three places, in priority order:

1. **Real environment variables** (including values you set inline on the command line).
2. **`.env`** in the project root (for local runs).
3. **Config files** in `configs/` (`filters.json` and `keywords.txt`) for non-secret defaults.

Real environment variables always win over `.env`. Legacy `JOBSCRAPER_*` names
are still accepted as aliases for the newer `JOBFINDER_SCRAPER_*` names.

## Table of contents

- [Core runtime](#core-runtime)
- [Scraper search & Apify](#scraper-search--apify)
- [Indeed](#indeed)
- [Stepstone](#stepstone)
- [Xing](#xing)
- [Evaluator](#evaluator)
- [Runtime reports](#runtime-reports)
- [Config files](#config-files)
- [Cost & performance tuning](#cost--performance-tuning)
- [Settings that need confirmation](#settings-that-need-confirmation)

## Core runtime

| Variable | Default | Description |
|---|---:|---|
| `APIFY_API_TOKEN` | blank | One Apify token, or 1–12 semicolon-separated tokens for ordered fallback. |
| `OPENAI_API_KEY` | blank | Required for evaluator and full-pipeline runs. |
| `GOOGLE_SPREADSHEET_ID` | blank | Google Sheet ID. Also read from `google_spreadsheet_id.txt` when absent. |
| `JOBFINDER_SCRAPER_OUTPUT_MODE` | `excel` | `excel`, `google_sheets`, or `both`. The full pipeline forces `google_sheets`. |
| `JOBFINDER_SCRAPER_SOURCES` | `linkedin` | `linkedin`, `indeed`, `stepstone`, `xing`, `all`, or a comma-separated list. |
| `JOBFINDER_PIPELINE_MODE` | `scrape_and_evaluate` | Used by the pipeline when `--mode` is omitted. |
| `JOBFINDER_PIPELINE_RESUME_INCOMPLETE` | `true` | In full-pipeline mode, resume an incomplete same-day tab instead of scraping again. |
| `JOBFINDER_SCRAPER_TIMEZONE` | `Europe/Berlin` | Timezone for logs and timestamped worksheet names. |
| `JOBFINDER_SCRAPER_POSTED_TIMEZONE` | `Europe/Berlin` | Timezone for the `Posted` column and exact posted-window filtering. |

## Scraper search & Apify

| Variable | Default | Description |
|---|---:|---|
| `JOBFINDER_SCRAPER_SEARCH_CONCURRENCY` | `15` | Global searches allowed to run in parallel. |
| `JOBFINDER_SCRAPER_APIFY_MEMORY_LIMIT_MB` | `0` | Optional total Apify memory budget that can lower effective concurrency when `APIFY_RUN_MEMORY_MB` is also set. `0` disables the cap. |
| `JOBFINDER_SCRAPER_APIFY_BATCH_SIZE` | `1` | Optional LinkedIn search batch size. Keep `1` unless actor output provides safe attribution. |
| `JOBFINDER_SCRAPER_MAX_RESULTS_PER_SEARCH` | `500` | LinkedIn max results per keyword; also the provider fallback. |
| `JOBFINDER_SCRAPER_POSTED_TIME_WINDOW` | `since_previous_run` | `since_previous_run`, `last_24h`, `last_7d`, or `backfill`. |
| `JOBFINDER_SCRAPER_SEARCH_WINDOW_BUFFER_SECONDS` | `3600` | Extra search padding when using previous-run windows. |
| `JOBFINDER_SCRAPER_MAX_APPLICANTS` | from `filters.json` (`100`) | Applicant cap applied after scraping. `0` disables the filter. |
| `APIFY_RUN_MEMORY_MB` | `0` | Optional memory override for every actor run (minimum `128` when set). `0` uses each actor's own default and is recommended for mixed-source runs. |
| `APIFY_RUN_TIMEOUT_SECONDS` | `3600` | Actor run timeout (minimum `60`). |
| `APIFY_CLIENT_TIMEOUT_SECONDS` | `120` | HTTP timeout for Apify API calls. |
| `APIFY_TRANSIENT_ERROR_RETRIES` | `5` | Retries for temporary Apify errors. |
| `APIFY_RETRY_DELAY_SECONDS` | `30` | Base retry delay (capped at 300s). |
| `JOBFINDER_LOG_LEVEL` | `INFO` | Set to `DEBUG` to log up to three redacted raw actor rows and parser/filter skip reasons. |
| `JOBFINDER_SCRAPER_DELAY_BETWEEN_REQUESTS` | `0` | Optional delay between starting searches. |
| `JOBFINDER_SCRAPER_SCRAPE_COMPANY_DETAILS` | `false` | LinkedIn actor option. |
| `JOBFINDER_SCRAPER_SPLIT_BY_LOCATION` | `false` | LinkedIn actor option. |

## Indeed

Used when `JOBFINDER_SCRAPER_SOURCES` includes `indeed`.

| Variable | Default | Description |
|---|---:|---|
| `INDEED_COUNTRY` | `DE` | Country code used to choose the Indeed domain and actor country. |
| `INDEED_LOCATION` | LinkedIn location | Search location. |
| `INDEED_MAX_RESULTS_PER_SEARCH` | `500` | Per-keyword result limit, capped at `1000`. |
| `INDEED_MAX_CONCURRENCY` | `5` | Cap for simultaneous Indeed searches. |
| `INDEED_SAVE_ONLY_UNIQUE_ITEMS` | `true` | Stored and logged for compatibility; not sent in the active actor payload. |

Indeed date filtering maps the requested window to supported day buckets (`1`,
`3`, `7`, `14`). Longer windows omit the actor date filter and rely on
post-scrape filtering.

## Stepstone

Used when `JOBFINDER_SCRAPER_SOURCES` includes `stepstone`.

| Variable | Default | Description |
|---|---:|---|
| `STEPSTONE_LOCATION` | `filters.json` or `Germany` | Location for keyword searches. |
| `STEPSTONE_CATEGORY` | `filters.json` or blank | Optional category fallback when no keyword is used. |
| `STEPSTONE_START_URLS` | blank | Comma/newline-separated URLs. When set, runs one direct-URL search instead of one per keyword. |
| `STEPSTONE_MAX_RESULTS_PER_SEARCH` | `500` | Max results per keyword or direct URL run. |
| `STEPSTONE_MAX_CONCURRENCY` | `10` | Search cap and actor concurrency. |
| `STEPSTONE_MIN_CONCURRENCY` | `1` | Actor `minConcurrency` (capped to max). |
| `STEPSTONE_MAX_REQUEST_RETRIES` | `3` | Actor page retry count. |
| `STEPSTONE_USE_APIFY_PROXY` | `true` | Actor proxy setting. |
| `STEPSTONE_APIFY_PROXY_GROUPS` | `RESIDENTIAL` | Comma/newline-separated Apify proxy groups. |

Stepstone date filtering maps to supported day buckets (`1`, `3`, `7`); longer
windows use `all`.

## Xing

Used when `JOBFINDER_SCRAPER_SOURCES` includes `xing`.

| Variable | Default | Description |
|---|---:|---|
| `XING_LOCATION` | `filters.json` or LinkedIn location | Country, city, or region filter. |
| `XING_DATE_POSTED` | derived | Optional `LAST_24_HOURS`, `LAST_WEEK`, or `LAST_MONTH` override. Blank maps the pipeline window to the nearest supported value. |
| `XING_START_URL` | `filters.json` or blank | Optional direct search URL. When set, runs one direct-URL search instead of one per keyword. |
| `XING_MAX_RESULTS_PER_SEARCH` | `500` | Max results per keyword or direct URL run. |
| `XING_MAX_PAGES` | `20` | Maximum result pages for the actor to process. |
| `XING_MAX_CONCURRENCY` | `5` | Cap for simultaneous Xing searches. |

The deployed Xing schema rejects unknown fields, so JobFinder sends only the
documented search fields. Proxy selection is left to the actor. Windows longer
than 30 days omit `date_posted` and rely on post-scrape filtering.

## Evaluator

| Variable | Default | Description |
|---|---:|---|
| `JOB_EVAL_SOURCE` | inferred | `excel` or `google_sheets`. Inferred from the spreadsheet ID when blank. |
| `JOB_EVAL_SHEET` | `latest` | Worksheet/tab to evaluate. |
| `JOB_EVAL_GOOGLE_SPREADSHEET_ID` | blank | Evaluator-specific spreadsheet ID override. |
| `JOB_EVAL_EXCEL_FILE` | `jobs.xlsx` | Excel workbook path. |
| `JOB_EVAL_MASTER_PROMPT_FILE` | `prompts/master_prompt.txt` | Prompt file path. |
| `JOB_EVAL_CV_FILE` | `cv/master_cv.tex` | CV file path. |
| `JOB_EVAL_OPENAI_MODEL` | `gpt-5-mini` | OpenAI model used for evaluation. |
| `JOB_EVAL_BATCH_SIZE` | `40` | Queued records processed per local batch. |
| `JOB_EVAL_CONCURRENCY` | `8` | OpenAI requests allowed in parallel per batch. |
| `JOB_EVAL_OPENAI_RETRIES` | `3` | Retries for retryable OpenAI failures. |
| `JOB_EVAL_RETRY_BASE_DELAY` | `2.0` | Base exponential retry delay. |
| `JOB_EVAL_RETRY_MAX_DELAY` | `60.0` | Maximum retry delay before jitter. |
| `JOB_EVAL_OPENAI_TIMEOUT` | `120` | OpenAI request timeout (seconds). |
| `JOB_EVAL_MAX_OUTPUT_TOKENS` | `9000` | Max tokens per model response (minimum `500`). |
| `JOB_EVAL_CV_PDF_OUTPUT` | `true` | Compile generated LaTeX CVs to PDFs and upload them to Drive. |
| `JOB_EVAL_CV_PHOTO_FILE` | `cv/photo.jpg` | Optional photo copied into each isolated LaTeX build directory. |
| `JOB_EVAL_CV_PDF_TIMEOUT` | `120` | Max seconds for one LaTeX PDF compilation. |
| `JOB_EVAL_CV_DRIVE_FOLDER_ID` | blank | Drive folder ID for timestamped PDF folders. Required when PDF output is on. |
| `JOB_EVAL_CV_PDF_APPLICANT_NAME` | `Applicant` | Name used in upload-safe PDF filenames. |
| `JOB_EVAL_LARGE_QUEUE_THRESHOLD` | `200` | Enables request pacing when queued rows exceed this count. |
| `JOB_EVAL_LARGE_QUEUE_SLEEP_MS` | `2000` | Delay between request starts when pacing is enabled. |
| `JOB_EVAL_SAVE_BATCH_SIZE` | `1` | Completed evaluations saved per write. `1` preserves row-by-row crash recovery. |
| `JOB_EVAL_UNSUITABLE_ROW_POLICY` | `single_label_only` | `single_label_only` or `keep_all`. |

**Unsuitable-row policy:**

| Policy | Behavior |
|---|---|
| `single_label_only` | Keep suitable rows and only the `Not Suitable` rows with exactly one unsuitable-reason label. |
| `keep_all` | Preserve every evaluated row. |

## Runtime reports

Used mainly by GitHub Actions, but settable locally too.

| Variable | Description |
|---|---|
| `JOBFINDER_PIPELINE_REPORT_FILE` | JSON preflight report path. |
| `JOBFINDER_SCRAPER_REPORT_FILE` | JSON scraper report path. |
| `JOBFINDER_EVALUATOR_REPORT_FILE` | JSON evaluator report path. |

## Config files

Two files in `configs/` hold non-secret defaults. Full details are in
[`configs/README.md`](../configs/README.md).

### `configs/keywords.txt` (private — not committed)

One search keyword per line. Blank lines and `#` comments are ignored. Each
keyword is searched against every selected board (except Stepstone/Xing direct
URL modes).

```text
# comments are ignored
GIS analyst
geospatial data
remote sensing
```

### `configs/filters.json` (committed)

| Section | Keys | Used by |
|---|---|---|
| `linkedin_search` | `location`, `geo_id`, `published_at`, `experience_levels`, `contract_types`, `split_country` | LinkedIn URL builder and scraper settings. |
| `stepstone_search` | `location`, `category`, `start_urls` | Stepstone fallback when env vars are unset. |
| `xing_search` | `location`, `discipline`, `remote`, `start_url`, `max_pages` | Xing fallback when env vars are unset. |
| `final_filters` | `excluded_title_terms`, `excluded_company_terms`, `max_applicants` | Final filters applied after dedupe. |
| `spreadsheet` | `application_status_options` | Google Sheets dropdown values. |

## Cost & performance tuning

Apify and OpenAI both bill by usage. The biggest cost drivers:

**Apify** — number of keywords × selected boards, the `*_MAX_RESULTS_PER_SEARCH`
limits, actor memory/runtime, repeated backfills, and broad direct-URL searches.

**OpenAI** — number of unevaluated rows, job-description and CV length,
`JOB_EVAL_MAX_OUTPUT_TOKENS`, and re-evaluating rows after clearing verdicts.

Practical controls:

- Prefer `since_previous_run` for scheduled runs so you only score new jobs.
- Use specific keywords and a single board while debugging.
- Run `scrape_only` first when testing provider changes, then evaluate separately.
- Lower `JOB_EVAL_CONCURRENCY` / `JOB_EVAL_BATCH_SIZE` if you hit OpenAI rate limits.
- Keep `JOB_EVAL_SAVE_BATCH_SIZE=1` for crash recovery; raise it only if write
  volume matters more than row-by-row durability.

## Other settings in `.env.example`

These are valid settings present in `.env.example` but not listed in the tables
above:

| Variable | Default | Description |
|---|---:|---|
| `GOOGLE_API_TIMEOUT_SECONDS` | `120` | HTTP timeout for Google API calls. |
| `GOOGLE_API_RETRIES` | `3` | Retries for Google API calls. |
| `JOBFINDER_PIPELINE_STEP_TIMEOUT_SECONDS` | `21600` | Per-step timeout for each pipeline child process (6 hours). `0` disables it. |

## Settings that need confirmation

These appear in `.env.example` but seem to conflict with the rest of the project.
Confirm against the code before relying on them:

- **`JOB_EVAL_CV_DRIVE_PARENT_FOLDER`** (in `.env.example`) — not referenced in any
  README table. The documented Drive setting is `JOB_EVAL_CV_DRIVE_FOLDER_ID`.
  *Needs confirmation that this is still used.*
- **`google_service_account.json` / Sheets service-account key** — a comment in
  `.env.example` mentions a service-account key, but the rest of the project
  documents an **OAuth-only** flow using `google_token.json`. *Likely a stale
  comment; needs confirmation.*
