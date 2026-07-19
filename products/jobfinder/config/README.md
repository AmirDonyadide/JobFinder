# JobFinder configuration

This directory contains JobFinder's search terms and non-secret search/filter
defaults. PhDFinder has an independent equivalent under
`products/phdfinder/config/`.

| File | Tracked | Purpose |
|---|---:|---|
| `filters.json` | Yes | Provider geography, final filters, and spreadsheet status options. |
| `keywords.example.txt` | Yes | Safe template for search terms. |
| `keywords.txt` | No | Private search terms used at runtime. |

Create and validate the local files:

```bash
cp products/jobfinder/config/keywords.example.txt products/jobfinder/config/keywords.txt
python -m json.tool products/jobfinder/config/filters.json
```

Real environment variables override `.env`, and `.env` overrides values from
`filters.json`. Keep private keywords out of Git.
