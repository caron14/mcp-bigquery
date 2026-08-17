---
type: Repository Guide
title: MCP BigQuery quickstart
description: "Entry point for understanding, running, and changing the MCP BigQuery server: safe BigQuery SQL analysis and schema exploration over MCP."
resource: README.md
tags: [mcp, bigquery, python, onboarding]
---

# MCP BigQuery quickstart

`mcp-bigquery` is a Python Model Context Protocol (MCP) server for AI-assisted BigQuery exploration. Its core product boundary is **analysis and metadata discovery rather than query execution**: SQL validation and estimates use BigQuery dry runs, while schema tools inspect datasets and tables. The separate row-preview capability reads table rows without a query job, so it is deliberately disabled unless explicitly enabled.

The packaged command is `mcp-bigquery` (`pyproject.toml`), which parses logging options and starts the stdio MCP server through `src/mcp_bigquery/__main__.py` and `src/mcp_bigquery/server.py`.

## Start here

1. Install the package or editable development build:
   ```bash
   pip install mcp-bigquery
   # development
   pip install -e ".[dev]"
   ```
2. Authenticate with Google Application Default Credentials (ADC), for example `gcloud auth application-default login`. A service-account credential path may instead be supplied to Google client libraries through `GOOGLE_APPLICATION_CREDENTIALS`; never commit credentials.
3. Configure the target with `BQ_PROJECT` and, where needed, `BQ_LOCATION`; launch with `mcp-bigquery` or `python -m mcp_bigquery`.
4. Configure an MCP host to invoke the `mcp-bigquery` command. The public-facing examples and host configuration are in [`README.md`](../README.md) and [`docs/usage.md`](../docs/usage.md).

For operational details, including log flags and CI behavior, see [development and release operations](operations/development-and-release.md). For safe feature changes, begin with [testing guidance](testing.md).

## Concept map

- [Architecture overview](architecture/overview.md) explains the stdio server, its dispatcher, and the common configuration/client/error layers.
- [SQL safety workflow](workflows/sql-safety.md) covers the dry-run tools and the local `sqlparse` analysis that the server dispatches.
- [Schema exploration workflow](workflows/schema-exploration.md) covers metadata tools, response shaping, validation, and the preview-data opt-in.
- [Development and release operations](operations/development-and-release.md) covers configuration, logging, CI, and docs deployment.
- [Testing guidance](testing.md) describes the credential-free unit suite, mocked BigQuery seam, and enforced checks.
- [Source map](source-map.md) is the change-oriented map from behavior to implementation files.

## Tool surface at a glance

| Area | MCP tools | Runtime boundary |
| --- | --- | --- |
| BigQuery dry runs | `bq_validate_sql`, `bq_dry_run_sql` | BigQuery `QueryJobConfig(dry_run=True)` |
| Static SQL analysis | `bq_extract_dependencies`, `bq_validate_query_syntax` | Local `SQLAnalyzer` based on `sqlparse` |
| Metadata discovery | `bq_list_datasets`, `bq_list_tables`, `bq_describe_table`, `bq_get_table_info` | BigQuery metadata APIs |
| Data preview | `bq_preview_table` | `client.list_rows`; only when `MCP_BQ_ENABLE_PREVIEW=true` |

The MCP server exposes all nine tool definitions in `src/mcp_bigquery/server.py`. Its SQL and schema domains share the configured client described in [architecture overview](architecture/overview.md), but their behavior and safety semantics differ; follow the workflow pages when changing either area.

## Change checklist

- **New MCP tool or changed tool contract:** update `TOOL_DEFS`, the dispatcher, the underlying async helper, validation/error behavior, tests, and public docs. See [source map](source-map.md).
- **BigQuery access behavior:** preserve project/location resolution, early dry-run client validation, mapped errors, and cache behavior in [architecture overview](architecture/overview.md).
- **Anything that returns rows:** retain the preview opt-in, validation, and hard maximum of ten rows in [schema exploration](workflows/schema-exploration.md); cost-free does not mean risk-free.
- **SQL parser behavior:** add focused examples to the unit suite; static analysis does not call BigQuery and should stay separate from dry-run validation.

## Backlog

- **Live BigQuery integration coverage** — `tests/test_core.py`: deferred because the current suite is explicitly credential-free and no dedicated live-test configuration was found.
- **Package release automation** — `docs/development.md` publishing section: deferred because documented publishing is manual and no release workflow was found.
