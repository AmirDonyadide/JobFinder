# JobFinder Website

This branch contains the **JobFinder project website** — a plain static site
(HTML, CSS, JavaScript) with **no build step**. The project's code and
documentation live on the
[`main` branch](https://github.com/AmirDonyadide/JobFinder/tree/main).

```
index.html        # landing page (for users)
developers.html   # developer guide page
css/styles.css    # design system + components (light/dark theming)
js/main.js        # copy buttons, tabs, FAQ, theme toggle, command builder
.nojekyll         # tells GitHub Pages to serve files as-is (skip Jekyll)
```

## Run it locally

No npm required — use the Python you already have:

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000>.

## Deploy with GitHub Pages (deploy from this branch)

1. Push this `website` branch to GitHub.
2. Repo **Settings → Pages**.
3. **Build and deployment → Source: Deploy from a branch**.
4. **Branch:** `website`, **folder:** `/ (root)` → **Save**.

The site is published at:

```
https://amirdonyadide.github.io/JobFinder/
```

Every push to this branch republishes the site. The `.nojekyll` file makes Pages
serve the static files exactly as they are.

## Editing notes

- Content is based only on what exists in the repository — no invented features,
  commands or examples.
- Colors, spacing and fonts are CSS variables at the top of `css/styles.css`.
- Deep documentation links point to the Markdown guides in `docs/` on the
  `main` branch, so the site stays in sync with the repo docs.
- Paths are relative, so the site works both locally and under the
  `/JobFinder/` GitHub Pages path.
