# JobFinder Website

The marketing / landing site for JobFinder. It is **plain static HTML, CSS and
JavaScript** — no framework, no build step, no `node_modules`.

```
website/
├── index.html        # landing page (for users)
├── developers.html   # developer guide page
├── css/styles.css    # design system + components (light/dark theming)
└── js/main.js        # copy buttons, tabs, FAQ, theme toggle, command builder
```

## Run it locally

No npm required — use the Python you already have:

```bash
cd website
python3 -m http.server 8000
```

Then open <http://localhost:8000>.

Any static file server works just as well, for example:

```bash
npx serve website      # if you happen to have Node installed
```

> Tip: just double-clicking `index.html` also works, but a local server is
> closer to how GitHub Pages serves the site.

## Deploy to GitHub Pages

A workflow at [`.github/workflows/pages.yml`](../.github/workflows/pages.yml)
deploys this folder automatically.

**One-time setup:**

1. Go to your repo **Settings → Pages**.
2. Under **Build and deployment → Source**, choose **GitHub Actions**.

After that, every push to `main` that touches `website/` publishes the site to:

```
https://amirdonyadide.github.io/JobFinder/
```

You can also trigger it manually from **Actions → Deploy website → Run workflow**.

## Editing notes

- Content is intentionally based only on what exists in the repository — no
  invented features, commands or examples.
- Colors, spacing and fonts are controlled by CSS variables at the top of
  `css/styles.css`. Edit the `:root` and `[data-theme="dark"]` blocks to retheme.
- All deep documentation links point to the Markdown guides in
  [`../docs/`](../docs/) on GitHub, so the site stays in sync with the repo docs.
- Paths are relative, so the site works both at the local root and under the
  `/JobFinder/` GitHub Pages subpath.
