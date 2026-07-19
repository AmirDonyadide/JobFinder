# Quick start with GitHub Actions

This is the shortest path to running either product without keeping your
computer on.

## 1. Fork the repository

Use GitHub's **Fork** button and keep the default branch.

## 2. Choose a product

| Product | Workflow | Secret location |
|---|---|---|
| JobFinder | **JobFinder Pipeline** | Repository Actions secrets |
| PhDFinder | **PhDFinder Pipeline** | GitHub Environment `phdfinder` |

## 3. Add secrets

Every run needs:

- `APIFY_API_TOKEN`
- `JOB_KEYWORDS_TEXT`

Google Sheets runs also need:

- `GOOGLE_TOKEN_JSON`
- `GOOGLE_SPREADSHEET_ID`

Evaluation additionally needs:

- `OPENAI_API_KEY`
- `MASTER_PROMPT_TEXT`
- `MASTER_CV_TEX`
- `JOB_EVAL_CV_DRIVE_FOLDER_ID` when PDF output is enabled
- `CV_PHOTO_BASE64` when using a private photo

Use JobFinder values for repository secrets. Put PhDFinder-specific values in
the `phdfinder` environment. Do not share spreadsheet IDs or Drive folders
between products.

## 4. Run

Open **Actions**, choose the product workflow, select `scrape_only` for the
first run, and press **Run workflow**.

After checking the output, use `scrape_and_evaluate` if you want AI scoring and
tailored CV PDFs.

## 5. Read results

Results appear in the configured Google spreadsheet. GitHub also uploads a
product-specific report artifact. Inspect that artifact whenever output is
empty or unexpectedly sparse.

JobFinder has a daily schedule. PhDFinder is manual-only by default to avoid
unplanned Apify or OpenAI cost.

For OAuth creation, exact secret commands, schedules, and troubleshooting, see
[Run with GitHub Actions](run-github-actions.md).
