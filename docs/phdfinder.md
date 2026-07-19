# PhDFinder

PhDFinder is an academic-role profile built on the JobFinder engine. It searches
for PhD, doctoral researcher, research assistant, and related roles while
keeping its inputs and output state independent from the normal job search.

## What is shared and what is separate

The provider adapters, scraping, normalization, deduplication, exports, OpenAI
evaluation, and CV generation are shared and tested once.

PhDFinder has separate:

- Keywords and final filters
- Academic evaluation prompt and Master CV
- Local Excel workbook
- Google spreadsheet ID cache and run history
- Google Drive destination configured through its workflow environment
- GitHub Actions workflow, concurrency group, reports, and artifacts

## Local setup

Install the project and create the private PhDFinder files:

```bash
python -m pip install -e .
cp profiles/phd/keywords.example.txt profiles/phd/keywords.txt
cp profiles/phd/master_prompt.example.txt profiles/phd/master_prompt.txt
cp profiles/phd/master_cv.example.tex profiles/phd/master_cv.tex
```

Review `profiles/phd/filters.json`, then run preflight:

```bash
phdfinder --preflight
```

Without an editable install, use the root wrapper:

```bash
python phd_finder.py --preflight
```

Run scraping only or the complete pipeline:

```bash
phdfinder --mode scrape_only
phdfinder --mode scrape_and_evaluate
```

The equivalent generic command is:

```bash
python run_job_pipeline.py --profile phd --mode scrape_and_evaluate
```

The existing JobFinder commands remain unchanged and default to `--profile
jobs`.

## GitHub Actions setup

Create a GitHub Environment named `phdfinder`. Add these secrets to that
environment:

- `APIFY_API_TOKEN`
- `OPENAI_API_KEY` for evaluation runs
- `GOOGLE_SPREADSHEET_ID` pointing to a PhDFinder-only spreadsheet
- `GOOGLE_TOKEN_JSON`
- `JOB_EVAL_CV_DRIVE_FOLDER_ID` pointing to a PhDFinder-only Drive folder
- `JOB_KEYWORDS_TEXT`
- `MASTER_PROMPT_TEXT`
- `MASTER_CV_TEX`
- `CV_PHOTO_BASE64` when a photo is needed

Run **PhDFinder Pipeline** manually from GitHub Actions. The workflow is
manual-only by design so adding this profile cannot unexpectedly create paid
Apify or OpenAI usage. Enable a schedule in `.github/workflows/phd.yml` only
after a manual run has been checked.

## Extending academic coverage

The initial profile searches the four existing providers. Academic-specific
sources such as EURAXESS, Academic Positions, or university vacancy pages should
be added as provider adapters in `src/jobfinder/providers/` and registered in
`src/jobfinder/providers/registry.py`; the profile does not need a separate
scraper engine.

