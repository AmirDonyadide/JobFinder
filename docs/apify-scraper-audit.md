# Apify Scraper Integration Audit

Verified against the deployed Apify actor builds and Store documentation on
2026-07-01.

| Platform | Actor | Input status | Output status | Expected result |
|---|---|---|---|---|
| LinkedIn | [`curious_coder/linkedin-jobs-scraper`](https://apify.com/curious_coder/linkedin-jobs-scraper) | Valid after removing the obsolete `useIncognitoMode` input. Job count is clamped to the actor minimum of 10. | The shared normalizer supports the actor's `id`, `link`, `title`, `companyName`, `location`, `descriptionText`, `postedAt`, `employmentType`, and `applyUrl` fields. | Yes, subject to LinkedIn public-search limits. |
| Indeed | [`valig/indeed-jobs-scraper`](https://apify.com/valig/indeed-jobs-scraper) | Valid: `country`, `title`, `location`, `limit`, and optional `datePosted`. | Compatible. Salary parsing now accepts the current `baseSalary.min` / `baseSalary.max` shape as well as the older aliases. | Yes. |
| Stepstone | [`memo23/stepstone-search-cheerio-ppr`](https://apify.com/memo23/stepstone-search-cheerio-ppr) | Valid: keyword/filter mode or `startUrls`, limits, concurrency, retries, and residential `proxy`. `Germany` is normalized to the actor's documented `deutschland` path segment. | Compatible with listing rows. The actor normally returns `textSnippet`, not a full description. | Yes. |
| Xing | [`shahidirfan/Xing-Jobs-Scraper`](https://apify.com/shahidirfan/xing-jobs-scraper) | Fixed. The deployed schema has `additionalProperties: false`; JobFinder previously always sent unsupported `proxyConfiguration` and could also send unsupported `discipline` / `remote`. It now sends only `startUrl`, `keyword`, `location`, `date_posted`, `results_wanted`, and `max_pages` as applicable. | Compatible with the actor's current snake_case output, including `job_id`, `company`, `description_text`, `date_posted`, `apply_url`, and `url`. | Yes. The actor is active; no login or cookie input is documented. |

## Apify execution

JobFinder uses the asynchronous API flow recommended by Apify: start the actor,
poll the run to a terminal status, read `defaultDatasetId`, and fetch dataset
items. The endpoint now uses the canonical `/v2/actors/` prefix. The deprecated
`/v2/acts/` prefix still worked but should not be used for new integrations.

The runner logs the actor ID, redacted input, run ID/status, dataset ID and item
count. Up to three raw rows are available at debug level. Empty successful runs
include the redacted input in a warning. Parser failures and final-filter skip
reasons are also logged without exposing the Apify token.

Set `JOBFINDER_LOG_LEVEL=DEBUG` to enable the raw-row and per-item diagnostics.

`APIFY_RUN_MEMORY_MB=0` uses each actor's configured default. This is safer than
forcing one value across all four actors, whose deployed memory configurations
differ. A positive value remains available as an explicit global override.

## Live smoke tests

These commands bypass dedupe, spreadsheet history, and final business filters.
They print a small redacted raw sample and then check the provider parser:

```bash
python scripts/test_linkedin_scraper.py
python scripts/test_indeed_scraper.py
python scripts/test_stepstone_scraper.py
python scripts/test_xing_scraper.py
```

All default to `GIS`, `Germany`, and 10 items. Use `--raw-only` to skip parser
validation or `--help` to see keyword, location, page, and sample-size options.
