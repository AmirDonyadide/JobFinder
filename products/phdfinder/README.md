# PhDFinder

PhDFinder searches PhD, doctoral-researcher, research-assistant, and related
academic roles. It uses the shared finder engine while keeping all academic
configuration and runtime state separate from JobFinder.

Its evaluator and tailored LaTeX CV are English-only. The tracked prompt and CV
examples use English instructions, section headings, course labels, profiles,
and research descriptions; official proper nouns may remain in their original
form when accuracy requires it.

## Product-owned files

```text
products/phdfinder/
  config/
    filters.json
    keywords.example.txt
    keywords.txt                 # private, ignored
  evaluator/
    master_prompt.example.txt
    master_prompt.txt            # private, ignored
    master_cv.example.tex
    master_cv.tex                # private, ignored
    photo.png                    # optional, private, ignored
  google_spreadsheet_id.txt      # private, ignored
```

Create the private inputs:

```bash
cp products/phdfinder/config/keywords.example.txt products/phdfinder/config/keywords.txt
cp products/phdfinder/evaluator/master_prompt.example.txt products/phdfinder/evaluator/master_prompt.txt
cp products/phdfinder/evaluator/master_cv.example.tex products/phdfinder/evaluator/master_cv.tex
```

If you created the private prompt or CV from an older German-oriented example,
recreate it from these English templates and then add your truthful information.

Then run a safe check:

```bash
phdfinder --preflight
```

PhDFinder defaults to `phd_jobs.xlsx` and requires its own spreadsheet ID and
generated-CV Drive folder through `PHDFINDER_GOOGLE_SPREADSHEET_ID` and
`PHDFINDER_CV_DRIVE_FOLDER_ID`. Its GitHub workflow is manual-only until a
schedule is deliberately enabled.
