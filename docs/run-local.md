# Run locally

Use local runs to test filters, inspect Excel output, authorize Google, and
debug providers before enabling automation.

## Install

Python 3.14 or newer is required.

```bash
git clone https://github.com/AmirDonyadide/JobFinder.git
cd JobFinder
python -m pip install --upgrade pip
python -m pip install -e ".[all]"
cp .env.example .env
```

Add at least `APIFY_API_TOKEN` to `.env`. Evaluation also requires
`OPENAI_API_KEY`. Google Sheets and Drive setup is described below.

## Create product files

### JobFinder

```bash
cp products/jobfinder/config/keywords.example.txt products/jobfinder/config/keywords.txt
cp products/jobfinder/evaluator/master_prompt.example.txt products/jobfinder/evaluator/master_prompt.txt
cp products/jobfinder/evaluator/master_cv.example.tex products/jobfinder/evaluator/master_cv.tex
```

Review `products/jobfinder/config/filters.json`.

### PhDFinder

```bash
cp products/phdfinder/config/keywords.example.txt products/phdfinder/config/keywords.txt
cp products/phdfinder/evaluator/master_prompt.example.txt products/phdfinder/evaluator/master_prompt.txt
cp products/phdfinder/evaluator/master_cv.example.tex products/phdfinder/evaluator/master_cv.tex
```

Review `products/phdfinder/config/filters.json`.

Private keywords, prompts, CVs, photos, spreadsheet IDs, tokens, and `.env` are
ignored by Git.

## First local scrape

An Excel-only scrape requires Apify but not Google or OpenAI:

```bash
JOBFINDER_SCRAPER_OUTPUT_MODE=excel jobfinder-scrape --product jobs
JOBFINDER_SCRAPER_OUTPUT_MODE=excel jobfinder-scrape --product phd
```

The default files are `jobs.xlsx` and `phd_jobs.xlsx`.

## Google OAuth

Google Sheets export and generated-CV uploads share one authorized-user OAuth
token. Create a Google desktop OAuth client, save its JSON as
`google_client_secret.json`, then run:

```bash
python -m jobfinder.google_auth
```

Complete the browser flow. The resulting `google_token.json` must include both:

- `https://www.googleapis.com/auth/spreadsheets`
- `https://www.googleapis.com/auth/drive`

Verify access:

```bash
python -m jobfinder.google_auth --check
```

Configure distinct destinations:

```text
GOOGLE_SPREADSHEET_ID=...                  # JobFinder
JOB_EVAL_CV_DRIVE_FOLDER_ID=...           # JobFinder
PHDFINDER_GOOGLE_SPREADSHEET_ID=...        # PhDFinder
PHDFINDER_CV_DRIVE_FOLDER_ID=...           # PhDFinder
```

PhDFinder never falls back to JobFinder's spreadsheet or Drive-folder values.

## Preflight

Preflight checks configuration and access without starting Apify or OpenAI work:

```bash
jobfinder --preflight
phdfinder --preflight
```

## Run products

```bash
# Scrape to Google Sheets only
jobfinder --mode scrape_only
phdfinder --mode scrape_only

# Scrape, evaluate, and optionally generate CV PDFs
jobfinder --mode scrape_and_evaluate
phdfinder --mode scrape_and_evaluate
```

Use the focused evaluator for existing outputs:

```bash
jobfinder-evaluate --product jobs --source google_sheets --sheet latest
jobfinder-evaluate --product phd --source google_sheets --sheet latest
```

## LaTeX

CV PDF generation needs `latexmk` and `xelatex`. On Ubuntu:

```bash
sudo apt-get install -y latexmk texlive-xetex texlive-latex-extra
```

On macOS, install a TeX distribution such as MacTeX.

## Configuration priority

Settings resolve in this order:

1. Real environment variables
2. Root `.env`
3. Selected product files and built-in defaults

Common controls include:

| Setting | Purpose |
|---|---|
| `JOBFINDER_SCRAPER_SOURCES` | One provider, comma-separated providers, or `all` |
| `JOBFINDER_SCRAPER_OUTPUT_MODE` | `excel`, `google_sheets`, or `both` |
| `JOBFINDER_SCRAPER_POSTED_TIME_WINDOW` | `since_previous_run`, `last_24h`, `last_7d`, or `backfill` |
| `JOBFINDER_SCRAPER_MAX_APPLICANTS` | Applicant cap; `0` disables it |
| `JOB_EVAL_CV_PDF_OUTPUT` | Enable or disable generated CV PDFs |
| `JOB_EVAL_UNSUITABLE_ROW_POLICY` | Preserve or remove rejected rows according to policy |

See the complete [configuration reference](configuration.md).

## Troubleshooting

| Problem | Check |
|---|---|
| `No module named jobfinder` | Run `python -m pip install -e ".[all]"` or use `PYTHONPATH=src` for direct modules. |
| Private file missing | Copy the examples for the selected product. |
| No jobs | Check keywords, filters, provider source, posted window, actor status, and Apify quota. |
| Google auth fails | Recreate the token with Sheets and Drive scopes and confirm both APIs are enabled. |
| Wrong output/history | Confirm the selected product and its spreadsheet ID. |
| LaTeX fails | Validate the Master CV and confirm `latexmk` and `xelatex` are installed. |

Never include secret values in logs or bug reports.
