---
type: Operations Guide
title: Development, documentation, and automation runbook
description: Local setup and operational guidance for MCP BigQuery, including authentication, configuration, logging, checks, and documentation deployment.
resource: docs/development.md
tags: [operations, development, ci, documentation]
---

# Development, documentation, and automation runbook

## Local development

The project targets Python 3.10+ and uses Hatchling (`pyproject.toml`). Create an editable development environment with:

```bash
pip install -e ".[dev]"
# or
uv pip install -e ".[dev]"
```

BigQuery calls require Google authentication. Use ADC for a developer login (`gcloud auth application-default login`) or configure Google client libraries with an approved service-account credential path. Do not add credential files or secret values to the repository or wiki.

Set `BQ_PROJECT` when ADC cannot determine the desired project and `BQ_LOCATION` for regional targeting. [Architecture overview](../architecture/overview.md) explains how those defaults are resolved by the client factory. `MCP_BQ_ENABLE_PREVIEW=true` should be set only in an environment where exposing a small sample of table rows to the MCP host is acceptable; see [schema exploration](../workflows/schema-exploration.md).

Run the server with `python -m mcp_bigquery` or the installed `mcp-bigquery` command. It speaks MCP on stdio, so logs must remain on stderr.

## Logging and diagnosis

The CLI accepts `-v` / `-vv` to increase verbosity, `-q` / `-qq` to reduce it, `--log-level` for an explicit level, and `--json-logs` for structured stderr output. `LOG_LEVEL` supplies the default base level. `logging_config.py` is the shared logging entry point; do not introduce competing `logging.basicConfig` calls in feature modules.

Likely configuration failures surface early because client creation performs a lightweight dry run. The factory reports missing ADC as `AUTH_ERROR` and reports an unresolved project as `CONFIG_ERROR`; it retries transient Google Cloud failures but does not retry authentication or permission errors. Consult [architecture overview](../architecture/overview.md) before changing that behavior.

## Quality checks

The development documentation describes the normal local loop:

```bash
pytest tests/test_core.py -v
isort --check-only --diff .
black --check --diff .
ruff check src/ tests/
mypy src/
```

`pyproject.toml` configures 100-character Black/Ruff formatting and strict mypy for source modules. Test modules are deliberately exempted from mypy errors. The pre-commit configuration provides local hooks, but CI itself explicitly runs isort and Black in a Python-version matrix plus the unit suite. See [testing guidance](../testing.md) for what the tests cover and do not cover.

## Published documentation

The user documentation source is `docs/`, configured by `mkdocs.yml` and built with Material for MkDocs. `.github/workflows/docs.yml` runs `mkdocs build --strict --verbose` on relevant documentation pull requests and deploys GitHub Pages on pushes to `main`. When a feature changes the MCP contract or setup, update the README and relevant `docs/` page alongside its tests; `mkdocs.yml` has the published navigation.

Generated pages are under `openwiki/`; this guide is a map of source-backed operating practice, not a replacement for the public MkDocs documentation.

## Release note

The existing development guide documents manual build and Twine upload commands. No release/publish GitHub Actions workflow was found during initialization, so treat package publishing as a manual, separately reviewed process until automation is added.
