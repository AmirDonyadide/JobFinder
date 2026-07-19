# Products

This repository contains two equal products powered by the same tested engine:

| Product | Purpose | Product files | Command |
|---|---|---|---|
| [JobFinder](jobfinder/) | General employment searches | `products/jobfinder/` | `jobfinder` |
| [PhDFinder](phdfinder/) | PhD and academic-role searches | `products/phdfinder/` | `phdfinder` |

Each product owns its keywords, filters, evaluator prompt, Master CV, optional
photo, spreadsheet state, Excel output, Drive folder, and workflow reports. The
provider adapters, scraping, deduplication, exports, evaluation, and PDF engine
remain shared under `src/jobfinder/`.

The keys `jobs` and `phd` are used by `--product` and `JOBFINDER_PRODUCT`.
Historical profile terminology remains accepted for compatibility; it selects
products and does not create separate copies of the engine.
