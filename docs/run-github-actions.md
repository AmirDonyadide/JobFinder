# Run with GitHub Actions

GitHub Actions can run JobFinder or PhDFinder without keeping your computer on.
The products share implementation but use separate workflows, secrets, state,
reports, and outputs.

## Choose a workflow

| Workflow | Use it for | Default trigger |
|---|---|---|
| **JobFinder Pipeline** (`jobfinder.yml`) | General jobs | Manual or daily schedule |
| **PhDFinder Pipeline** (`phd.yml`) | PhD and academic roles | Manual only |

PhDFinder reads secrets from a GitHub Environment named `phdfinder`. JobFinder
continues to use repository secrets.

## Prepare private product files locally

Create the JobFinder files:

```bash
cp products/jobfinder/config/keywords.example.txt products/jobfinder/config/keywords.txt
cp products/jobfinder/evaluator/master_prompt.example.txt products/jobfinder/evaluator/master_prompt.txt
cp products/jobfinder/evaluator/master_cv.example.tex products/jobfinder/evaluator/master_cv.tex
```

Or create the PhDFinder files:

```bash
cp products/phdfinder/config/keywords.example.txt products/phdfinder/config/keywords.txt
cp products/phdfinder/evaluator/master_prompt.example.txt products/phdfinder/evaluator/master_prompt.txt
cp products/phdfinder/evaluator/master_cv.example.tex products/phdfinder/evaluator/master_cv.tex
```

Review the matching `filters.json` before creating secrets.

## Required secrets

| Secret | Required when | Value |
|---|---|---|
| `APIFY_API_TOKEN` | Every run | One token or up to 12 semicolon-separated tokens |
| `JOB_KEYWORDS_TEXT` | Every run | Full contents of the selected product's `keywords.txt` |
| `GOOGLE_TOKEN_JSON` | Google Sheets or evaluation | Authorized-user OAuth JSON with Sheets and Drive scopes |
| `GOOGLE_SPREADSHEET_ID` | Google Sheets or evaluation | Product-specific spreadsheet ID |
| `OPENAI_API_KEY` | Evaluation | OpenAI API key |
| `MASTER_PROMPT_TEXT` | Evaluation | Selected product's private evaluator prompt |
| `MASTER_CV_TEX` | Evaluation | Selected product's private Master CV |
| `JOB_EVAL_CV_DRIVE_FOLDER_ID` | PDF output | Product-specific Google Drive folder ID |
| `CV_PHOTO_BASE64` | Optional PDF photo | Base64-encoded private photo |

Never reuse JobFinder's spreadsheet or generated-CV folder for PhDFinder. The
engine enforces distinct environment names locally, and the workflows enforce
separate GitHub secret scopes.

## Add JobFinder secrets

Open:

```text
Repository → Settings → Secrets and variables → Actions
```

Create repository secrets using the table above. For example:

```bash
gh secret set JOB_KEYWORDS_TEXT < products/jobfinder/config/keywords.txt
gh secret set MASTER_PROMPT_TEXT < products/jobfinder/evaluator/master_prompt.txt
gh secret set MASTER_CV_TEX < products/jobfinder/evaluator/master_cv.tex
```

## Add PhDFinder secrets

Create a GitHub Environment named `phdfinder`, then add the same secret names
inside that environment using PhDFinder-specific values.

```bash
gh secret set --env phdfinder JOB_KEYWORDS_TEXT < products/phdfinder/config/keywords.txt
gh secret set --env phdfinder MASTER_PROMPT_TEXT < products/phdfinder/evaluator/master_prompt.txt
gh secret set --env phdfinder MASTER_CV_TEX < products/phdfinder/evaluator/master_cv.tex
```

## Run manually

Open the repository's **Actions** page, choose the product workflow, select the
sources and run mode, and press **Run workflow**.

Use `scrape_only` while validating providers or filters. Use
`scrape_and_evaluate` after the output has been checked.

## Schedules and cost

JobFinder's schedule is declared in `.github/workflows/jobfinder.yml`.
PhDFinder is deliberately manual-only. Add a PhDFinder schedule only after a
successful manual run establishes acceptable Apify and OpenAI cost.

Disabling one workflow does not disable the other.

## Runtime safety

Both workflows call the same tested runtime-file preparation module. It:

- Validates required secrets without printing their values
- Rejects more than 12 Apify tokens
- Validates Google authorized-user fields and required OAuth scopes
- Writes private files only into the selected product tree
- Records every generated private path in a product-specific manifest
- Deletes only manifest-recorded paths during cleanup

GitHub-hosted runners are temporary, but explicit cleanup remains enabled.

## Read results

Google Sheets runs write a new timestamped tab and update that product's hidden
seen-job index. Excel-only JobFinder runs upload `jobfinder-excel-output`.

Both workflows upload report artifacts even after failure:

- `jobfinder-run-reports`
- `phdfinder-run-reports`

When output is empty, inspect `reports/scraper.json`, `failed_sources`,
`unique_job_count`, and raw logs. A green workflow can still contain provider
warnings or zero-result actor runs.

## Troubleshooting

| Problem | Check |
|---|---|
| Missing secret | Confirm it exists at repository scope for JobFinder or in the `phdfinder` environment for PhDFinder. |
| Google token rejected | Recreate `google_token.json` locally with both Sheets and Drive scopes, then replace `GOOGLE_TOKEN_JSON`. |
| Wrong spreadsheet | Verify the product-specific `GOOGLE_SPREADSHEET_ID`. |
| No jobs | Inspect report artifacts, actor logs, date window, filters, and Apify quota. |
| PDF generation fails | Check the Master CV, LaTeX tools, Drive folder ID, and optional photo. |
| Duplicate scheduled runs | Check the JobFinder daily-run gate and its product-specific concurrency group. |

See the [workflow reference](../.github/workflows/README.md) and general
[troubleshooting guide](troubleshooting.md).
