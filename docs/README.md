# JobFinder Documentation

Welcome to the JobFinder docs. Pick a guide based on what you want to do.
For a project overview, go back to the [main README](../README.md).

## Getting started

| Guide | Use it when… |
|---|---|
| [Quick Start](quick-start.md) | You want results fast and prefer **no coding** — fork it and run on GitHub. |
| [Run locally](run-local.md) | You want to run JobFinder **from your own machine**. |
| [Run on GitHub Actions](run-github-actions.md) | You want **scheduled, hands-off** runs in the cloud. |

## Using JobFinder

| Guide | What's inside |
|---|---|
| [Usage guide](usage.md) | Every command, the two run modes, and the output columns. |
| [Examples & workflows](examples.md) | Ready-to-copy commands for common situations. |
| [Configuration reference](configuration.md) | Every environment variable and config file. |
| [Troubleshooting](troubleshooting.md) | Fixes for the most common errors. |

## Going deeper (developers)

| Guide | What's inside |
|---|---|
| [How it works](how-it-works.md) | The scraping, dedupe, history, and evaluation flow. |
| [Architecture](architecture.md) | Module ownership, boundaries, and design direction. |
| [Apify scraper audit](apify-scraper-audit.md) | Current actor schemas, parser compatibility, and live smoke-test commands. |
| [Developer guide](developer-guide.md) | Local setup, CI checks, testing, and extension points. |

The deepest reference lives next to the code: each module under
`src/jobfinder/*/README.md` documents its own responsibilities.
