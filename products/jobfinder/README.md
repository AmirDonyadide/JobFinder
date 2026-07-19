# JobFinder

JobFinder searches general employment postings, removes duplicates, applies
product-specific filters, exports results, and can evaluate them against a
private Master CV.

## Product-owned files

```text
products/jobfinder/
  config/
    filters.json
    keywords.example.txt
    keywords.txt                 # private, ignored
  evaluator/
    master_prompt.example.txt
    master_prompt.txt            # private, ignored
    master_cv.example.tex
    master_cv.tex                # private, ignored
    photo.png                    # public default; replace locally if needed
```

Create the private inputs:

```bash
cp products/jobfinder/config/keywords.example.txt products/jobfinder/config/keywords.txt
cp products/jobfinder/evaluator/master_prompt.example.txt products/jobfinder/evaluator/master_prompt.txt
cp products/jobfinder/evaluator/master_cv.example.tex products/jobfinder/evaluator/master_cv.tex
```

Then run a safe check:

```bash
jobfinder --preflight
```

JobFinder uses its own spreadsheet ID, `jobs.xlsx`, generated-CV Drive folder,
run history, and report artifacts. It never reads PhDFinder's private inputs.
