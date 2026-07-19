# How the finder engine works

This guide explains what happens inside a JobFinder or PhDFinder run, from the
selected product's keywords to its isolated output. For module ownership and
design direction, see the
[Architecture notes](architecture.md).

Back to the [project overview](../README.md) · [Developer guide](developer-guide.md).

## Big picture

```mermaid
flowchart LR
    A["selected products/&lt;name&gt; files<br/>.env / secrets"] --> B["FinderProduct + ScraperSettings"]
    B --> C["Search builder<br/>scraper/search.py"]
    C --> D["Apify actors<br/>LinkedIn / Indeed / Stepstone / Xing"]
    D --> E["Provider normalizers"]
    E --> F["Dedupe pipeline<br/>dedupe/"]
    F --> G["Final filters<br/>title / company / applicants / posted window"]
    G --> H["Exports<br/>Excel or Google Sheets"]
    H --> I["Evaluator queue<br/>unevaluated rows only"]
    I --> J["OpenAI Responses API"]
    J --> K["Incremental writes<br/>final cleanup"]
```

## Runtime boundaries

| Boundary | Main modules | Responsibility |
|---|---|---|
| Configuration | `env.py`, `config_files.py`, `scraper/settings.py` | Merge env, `.env`, `filters.json`, and `keywords.txt` into typed settings. |
| Provider adapters | `providers/` | Build actor payloads, normalize actor output, register adapters. |
| Scraper orchestration | `scraper/search.py`, `scraper/service.py` | Build searches, run Apify concurrently, handle retries. |
| Dedupe | `dedupe/` | Turn raw jobs into features, match duplicates, merge canonical jobs. |
| Export | `scraper/export_excel.py`, `scraper/export_google_sheets.py` | Write stable spreadsheet rows. |
| Run history | `scraper/run_history.py` | Read prior tabs, derive previous-run windows, maintain seen-job keys. |
| Evaluation | `evaluator/` | Build prompts, call OpenAI, parse, save, clean output. |
| Pipeline | `pipeline/` | Run scraper then evaluator, plus preflight. |
| Operations | `operations/` | Sanitized JSON reports and manifest-scoped CI private files. |

## The job boards

Each board is an [Apify](https://apify.com/) actor wrapped by a provider adapter:

| Board | Actor | Adapter behavior |
|---|---|---|
| LinkedIn | `curious_coder~linkedin-jobs-scraper` | Builds search URLs from keyword, location, geo ID, experience level, job type, and posted-time window. |
| Indeed | `valig~indeed-jobs-scraper` | Builds payloads with country, title, location, and supported day-bucket date filters; normalizes employer, salary, skills, etc. |
| Stepstone | `memo23~stepstone-search-cheerio-ppr` | Builds keyword/location payloads or one direct-URL payload; normalizes salary, work mode, labels, company. |
| Xing | `shahidirfan~Xing-Jobs-Scraper` | Builds keyword/location payloads or one direct-URL payload; normalizes IDs, company, salary, work mode, links. |

The stable adapter surface lives in `src/jobfinder/providers`. The
`src/jobfinder/scraper/providers` package keeps compatibility imports for older code.

## Scraping flow

1. Product resolution selects `products/jobfinder/` or `products/phdfinder/`, then `load_scraper_settings()` reads that product's filters, keywords, `.env`, and real environment variables.
2. If Google Sheets output is on, the scraper authenticates first and reads spreadsheet history.
3. The posted-time window is applied:
   - `since_previous_run` uses the newest prior tab (plus a buffer) as a broad search window.
   - `last_24h` and `last_7d` force fixed windows.
   - `backfill` removes the posted-time filter.
4. `search.py` builds one search per board/keyword — except Stepstone/Xing direct-URL modes, which build a single configured-URL run.
5. Searches run through Apify with global and per-board concurrency limits.
6. Temporary Apify failures are retried. Exhausted or unauthorized tokens can be retired for the run when several tokens are configured.
7. Output is tagged with its source and passed into dedupe.

Stepstone and Xing failures are isolated per source so other boards still finish.
LinkedIn and Indeed execution failures are treated as fatal, since they usually
mean the main selected source did not complete.

## Dedupe flow

The production path is `jobfinder.dedupe.matching.deduplicate_search_results`. It
is **deterministic and never calls OpenAI**.

The matcher uses normalized company, title, location, job type, and posted time,
plus the external apply URL as a strong cross-board signal. It uses source-aware
blocking keys to avoid full pairwise comparison, and explicit blockers for
conflicting seniority, role family, job type, and large posted-time gaps.

It deliberately does **not** use provider job URLs as a cross-board identity
signal: the same real-world job often has different board-specific IDs.

Merged jobs preserve a combined `App` label (e.g. `LinkedIn | Indeed`), all
matched keywords in first-seen order, the richest available description, and
internal provenance for source-specific URLs, IDs, and keywords.

## Historical tracking flow

When Google Sheets output is on, `scraper/run_history.py` reads the spreadsheet
before scraping:

- The newest parseable `Posted` value across tabs sets the `since_previous_run` lower bound; timestamped tab names are only a fallback.
- `_jobfinder_seen_jobs` is a hidden tab of canonical historical job keys.
- If that hidden index is missing, the scraper scans previous tabs and seeds it during a real export.
- Preflight validates access without seeding the index.

Historical duplicate keys are built from identity fields such as source, title,
company, location, job type, posted date, and external apply URL.

## Evaluation flow

The evaluator reads from Excel or Google Sheets (Google Sheets when a spreadsheet
ID is configured, otherwise Excel).

1. Read the selected sheet, with `latest` resolving to the newest tab.
2. Ensure the AI columns exist: `AI Verdict`, `AI Fit Score`, `AI Unsuitable Reasons`, `AI Tailored CV`, `AI CV PDF`.
3. Skip rows that already have a non-`Error` `AI Verdict`.
4. Build each job advertisement from useful row columns (excluding URLs, status fields, and existing AI output).
5. Compose the model input from the selected product's evaluator prompt, the row advertisement, and its Master CV.
6. Call the OpenAI Responses API with strict machine-readable output instructions.
7. Parse the verdict, fit score, unsuitable reasons, and optional tailored LaTeX CV.
8. Save each completed evaluation immediately (or in batches via `JOB_EVAL_SAVE_BATCH_SIZE`).
9. Enforce the selected product's Master-CV contract: JobFinder restores its
   German sections, while PhDFinder restores the English `Education` and
   `Languages` sections. Both copy selected projects exactly from the Master CV
   and validate experience organizations and dates.
10. Compile generated CV LaTeX. If it exceeds two pages, remove one
    relevance-ranked project and recompile; if still long, remove one
    relevance-ranked experience and recompile. Never rewrite projects during
    page handling.
11. Upload PDFs to a timestamped Drive run folder and write the link (or error)
    to `AI CV PDF`.
12. Finalize by removing detail columns such as `Job Description` and the
    temporary `AI Tailored CV` column.
13. Apply `JOB_EVAL_UNSUITABLE_ROW_POLICY`.

## A note on output durability

Because evaluations are saved as each row finishes, a crash mid-run keeps the
rows already completed. Final cleanup removes detail columns — so if you need full
job descriptions for audit, keep a raw export or use `scrape_only` mode.
