# Troubleshooting

Fixes for the most common problems. If your issue is specific to one run mode,
the [Local guide](run-local.md) and [GitHub Actions guide](run-github-actions.md)
each have their own troubleshooting section too.

Back to the [project overview](../README.md).

## Setup & installation

| Symptom | Likely cause | What to do |
|---|---|---|
| `No module named 'jobfinder'` | Package not installed and `PYTHONPATH` not set. | Run `python -m pip install -e ".[all]"`, use the root scripts, or prefix commands with `env PYTHONPATH=src`. |
| `python: command not found` after `conda activate` | Environment isn't using the conda Python. | Recreate the environment, then check `which python` and `python --version`. |
| Console script missing | Package not reinstalled after a `pyproject.toml` change. | Reinstall the editable package. |

## Credentials & access

| Symptom | Likely cause | What to do |
|---|---|---|
| `Missing required setting(s): APIFY_API_TOKEN` | No usable Apify token. | Set `APIFY_API_TOKEN` in `.env`, the shell, or a GitHub secret. Remove placeholder values. |
| `APIFY_API_TOKEN supports at most 12` | Too many fallback tokens. | Keep 1–12 unique semicolon-separated tokens. |
| Apify 401 / 403 / 402 | Invalid token, actor access issue, or billing problem. | Confirm the token's account can run the actor and has billing/trial access. |
| `Missing required setting(s): OPENAI_API_KEY` | No OpenAI key for an evaluating run. | Set `OPENAI_API_KEY`, or run with `--mode scrape_only`. |
| Google Sheets auth fails | Missing/invalid `google_token.json`, disabled API, wrong account, or missing scopes. | Enable the Sheets and Drive APIs, delete `google_token.json`, and run `python -m jobfinder.google_auth` again. |
| Drive upload fails | Missing folder ID, invalid token, Drive API disabled, or wrong account. | Set `JOB_EVAL_CV_DRIVE_FOLDER_ID`, confirm the folder is accessible, and recreate the token if needed. |
| Spreadsheet not found | Full URL pasted instead of just the ID. | Use only the ID from `/spreadsheets/d/<id>/`. |

## Scraping

| Symptom | Likely cause | What to do |
|---|---|---|
| Apify 502 / 503 / 504 or timeout | Actor/API instability or too much concurrency. | Lower search concurrency, lower per-search limits, or increase `APIFY_RUN_TIMEOUT_SECONDS`. |
| Actor succeeds with zero jobs | Search mismatch, actor schema drift, or an overly narrow date/location filter. | Run the matching `python scripts/smoke_*.py` command to inspect raw rows before pipeline filters; enable debug logging for the first three redacted actor rows. |
| No jobs found | Search/filter window too narrow or a provider config mismatch. | Check keywords, source selection, posted-time window, Stepstone/Xing location or start URLs, and final filters. |
| Scraper writes Excel but the pipeline fails | The full pipeline forces Google Sheets. | Complete Google Sheets setup, or use the scraper alone for Excel. |

## Evaluation & CV PDFs

| Symptom | Likely cause | What to do |
|---|---|---|
| `AI CV PDF` shows `LaTeX compilation failed` | Missing LaTeX package, invalid generated LaTeX, or missing photo. | Install `latexmk` and `xelatex`, check the generated LaTeX, and confirm `JOB_EVAL_CV_PHOTO_FILE` points to the right image. |
| Evaluator skips rows | `AI Verdict` already exists and is not `Error`. | Clear those cells, or create a fresh run tab. |
| OpenAI `insufficient_quota` | No usable quota/billing on the project. | Add billing/credits to the OpenAI project, then re-run. |
| OpenAI rate limits | Concurrency or batch size too high. | Lower `JOB_EVAL_CONCURRENCY`, lower `JOB_EVAL_BATCH_SIZE`, or add pacing. |
| Expected rejected rows disappeared | Default policy removed multi-label `Not Suitable` rows. | Set `JOB_EVAL_UNSUITABLE_ROW_POLICY=keep_all` before evaluating. |

## Still stuck?

- Run `jobfinder --preflight` to validate settings and access
  without spending API credits.
- Review the relevant [Configuration reference](configuration.md) entry to make
  sure a setting does what you expect.
- Keep your secrets out of logs and commits — see the security notes in the
  [Local guide](run-local.md#security-notes) and
  [GitHub Actions guide](run-github-actions.md#security-notes).
