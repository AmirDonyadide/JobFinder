# GitHub workflows

The repository has one quality workflow and two isolated product workflows.

| Workflow | Product | Trigger | State boundary |
|---|---|---|---|
| `ci.yml` | Shared engine and both products | Push and pull request | No live credentials or network calls |
| `jobfinder.yml` | JobFinder | Manual and daily schedule | Repository secrets, JobFinder spreadsheet/history/reports |
| `phd.yml` | PhDFinder | Manual only | `phdfinder` environment, PhDFinder spreadsheet/history/reports |

## Shared behavior

Both product workflows:

1. Install dependency groups from `pyproject.toml`.
2. Resolve whether evaluation, Google APIs, and LaTeX are needed.
3. Call `jobfinder.operations.runtime_files prepare` to validate secrets and
   materialize private product files.
4. Run product-aware preflight.
5. Run the selected scrape or scrape-and-evaluate mode.
6. Upload sanitized reports and product-specific artifacts.
7. Call `jobfinder.operations.runtime_files cleanup`, which removes only paths
   recorded in the matching preparation manifest.

The shared preparation code validates Apify token count, required product
inputs, OpenAI requirements, Google authorized-user JSON and scopes,
product-specific spreadsheet IDs, Drive folder IDs, and optional photo base64.
Secret values are never printed.

## Product differences

| Setting | JobFinder | PhDFinder |
|---|---|---|
| Internal key | `jobs` | `phd` |
| Workflow environment | Repository secrets | GitHub Environment `phdfinder` |
| Schedule | Daily plus manual | Manual only by default |
| Applicant cap | Workflow input | Disabled by default |
| Default posted window | Since previous run | Last seven days |
| Unsuitable-row policy | Workflow input | Keep all |
| Report artifact | `jobfinder-run-reports` | `phdfinder-run-reports` |
| Concurrency group | `jobfinder-pipeline` | `phdfinder-pipeline` |

## Required secrets

Every run needs:

- `APIFY_API_TOKEN`
- `JOB_KEYWORDS_TEXT`

Google Sheets output also needs:

- `GOOGLE_TOKEN_JSON`
- `GOOGLE_SPREADSHEET_ID`

Evaluation adds:

- `OPENAI_API_KEY`
- `MASTER_PROMPT_TEXT`
- `MASTER_CV_TEX`

Generated PDFs add:

- `JOB_EVAL_CV_DRIVE_FOLDER_ID`
- `CV_PHOTO_BASE64` when a private photo is required

The same secret names are used for both workflows, but PhDFinder values belong
in its GitHub Environment and must point to PhDFinder-only resources.

## Reports and diagnostics

Always inspect the uploaded report artifact when output is empty or sparse. A
green workflow conclusion does not prove that every provider returned jobs.
Useful evidence includes:

- `reports/scraper.json`
- `failed_sources`
- `unique_job_count`
- evaluator and preflight reports
- the workflow summary and raw job log

Do not remove these reports while simplifying workflow code; they are the
primary boundary between workflow success and actual data success.

## Safe changes

- Change schedules only in the matching product workflow.
- Keep concurrency groups and artifact names product-specific.
- Put common secret-file behavior in `operations/runtime_files.py`, not copied
  inline Python blocks.
- Validate both product filter JSON files in CI.
- Keep PhDFinder manual-only until recurring Apify/OpenAI cost is accepted.
