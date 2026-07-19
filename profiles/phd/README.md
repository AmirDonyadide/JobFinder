# PhDFinder Profile

PhDFinder reuses the JobFinder scraping, normalization, deduplication, export,
evaluation, and CV-generation engine while keeping academic search inputs and
state separate.

## Local setup

Create the private runtime files:

```bash
cp profiles/phd/keywords.example.txt profiles/phd/keywords.txt
cp profiles/phd/master_prompt.example.txt profiles/phd/master_prompt.txt
cp profiles/phd/master_cv.example.tex profiles/phd/master_cv.tex
```

Then run a safe configuration check:

```bash
python phd_finder.py --preflight
```

PhDFinder defaults to:

- `profiles/phd/keywords.txt`
- `profiles/phd/filters.json`
- `profiles/phd/master_prompt.txt`
- `profiles/phd/master_cv.tex`
- `profiles/phd/photo.png`
- `profiles/phd/google_spreadsheet_id.txt`
- `phd_jobs.xlsx` for local Excel output

Any existing `JOB_EVAL_*` or `JOBFINDER_SCRAPER_*` file override still takes
precedence over these profile defaults.

Use `PHDFINDER_GOOGLE_SPREADSHEET_ID` and `PHDFINDER_CV_DRIVE_FOLDER_ID` for
local cloud output. PhDFinder intentionally ignores JobFinder's generic
spreadsheet and Drive-folder settings so the two products cannot accidentally
share history or generated-CV folders.

## GitHub Actions

The manual `PhDFinder Pipeline` workflow uses a GitHub Environment named
`phdfinder`. Add the same secret names used by JobFinder to that environment,
but give it the PhDFinder-specific spreadsheet ID, Drive folder, keywords,
academic prompt, and academic CV.

The workflow intentionally has no schedule initially. Add a schedule only after
a manual run has been verified and recurring Apify/OpenAI cost is acceptable.
