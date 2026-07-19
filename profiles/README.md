# Finder Profiles

Profiles let one tested pipeline power multiple focused search products without
maintaining long-lived branches or copied repositories.

The default `jobs` profile keeps using the repository's existing `configs/`,
`prompts/`, and `cv/` paths. The `phd` profile uses `profiles/phd/` for its own
keywords, filters, evaluator prompt, CV, spreadsheet cache, and photo.

Select a profile with `--profile` or `JOBFINDER_PROFILE`:

```bash
python run_job_pipeline.py --profile jobs --preflight
python run_job_pipeline.py --profile phd --preflight
python phd_finder.py --preflight
```

Installed editable environments also expose `phdfinder` as a convenience
command for the academic profile.

