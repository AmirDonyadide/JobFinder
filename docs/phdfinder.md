# PhDFinder

PhDFinder is an academic-role product built on the shared finder engine. It searches
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
python -m pip install -e ".[all]"
cp products/phdfinder/config/keywords.example.txt products/phdfinder/config/keywords.txt
cp products/phdfinder/evaluator/master_prompt.example.txt products/phdfinder/evaluator/master_prompt.txt
cp products/phdfinder/evaluator/master_cv.example.tex products/phdfinder/evaluator/master_cv.tex
```

Review `products/phdfinder/config/filters.json`, then run preflight:

```bash
phdfinder --preflight
```

Without an editable install, use direct module execution with `PYTHONPATH=src`:

```bash
PYTHONPATH=src python -m jobfinder.pipeline.cli --product phd --preflight
```

Run scraping only or the complete pipeline:

```bash
phdfinder --mode scrape_only
phdfinder --mode scrape_and_evaluate
```

The equivalent generic command is:

```bash
jobfinder --product phd --mode scrape_and_evaluate
```

The older `--profile phd` form remains accepted; `phdfinder` is the clearer
product command.

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
manual-only by design so adding this product cannot unexpectedly create paid
Apify or OpenAI usage. Enable a schedule in `.github/workflows/phd.yml` only
after a manual run has been checked.

## Extending academic coverage

The initial product searches the four existing providers. Academic-specific
sources such as EURAXESS, Academic Positions, or university vacancy pages should
be added as provider adapters in `src/jobfinder/providers/` and registered in
`src/jobfinder/providers/registry.py`; the product does not need a separate
scraper engine.
