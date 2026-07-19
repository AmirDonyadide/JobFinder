# Provider smoke scripts

Normal product operations use the installed commands `jobfinder`, `phdfinder`,
`jobfinder-scrape`, and `jobfinder-evaluate`. This directory contains only live
provider diagnostics that intentionally sit outside the automated test suite.

| Script | Provider |
|---|---|
| `smoke_linkedin.py` | LinkedIn |
| `smoke_indeed.py` | Indeed |
| `smoke_stepstone.py` | Stepstone |
| `smoke_xing.py` | Xing |

Run them from the repository root after configuring `.env` and the selected
product's private keywords:

```bash
python scripts/smoke_linkedin.py
python scripts/smoke_indeed.py
python scripts/smoke_stepstone.py
python scripts/smoke_xing.py
```

These commands call real Apify actors and may consume paid credits. Automated
tests use fakes and never make live provider calls.
