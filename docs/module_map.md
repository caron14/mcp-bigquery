# Module Responsibility Map (v0.4.2)

## Overview
The refactor in v0.4.2 reshaped the `mcp_bigquery` package around feature-specific subpackages. This document lists the primary modules, their responsibilities, and notable internal dependencies to help contributors navigate the codebase.

### Metrics Snapshot
| Module | Functions | Classes |
| --- | ---:| ---:|
| `clients/factory.py` | 4 | 0 |
| `schema_explorer/_formatters.py` | 10 | 0 |
| `schema_explorer/datasets.py` | 2 | 0 |
| `schema_explorer/describe.py` | 2 | 0 |
| `schema_explorer/tables.py` | 4 | 0 |
| `info_schema/queries.py` | 3 | 0 |
| `info_schema/performance.py` | 5 | 0 |

## Core Runtime
- **`mcp_bigquery.server`** — Registers MCP tools, exposes stdio server entrypoints, and orchestrates calls into schema, info-schema, and SQL analysis layers.
  - Depends on: `clients`, `schema_explorer`, `info_schema`, `sql_analyzer`, `validators`.
- **`mcp_bigquery.__main__`** — CLI entrypoint; now configures logging via `logging_config` and honors `--verbose/--quiet` flags.

## BigQuery Client Management
- **`mcp_bigquery.clients.factory`** — Single source for creating BigQuery clients with caching, retries, and authentication/configuration error handling.
  - Depends on: `config`, `cache`, `exceptions`, `logging_config`.
- **`mcp_bigquery.bigquery_client`** — Backward-compatible façade that forwards to the shared factory.

## Schema Exploration
- **`mcp_bigquery.schema_explorer.datasets`** — Dataset listing workflows with centralised validation and formatting helpers.
- **`mcp_bigquery.schema_explorer.tables`** — Table listing and detailed metadata aggregation (partitioning, clustering, constraints).
- **`mcp_bigquery.schema_explorer.describe`** — Schema-focused describe endpoint with nested-field formatting.
- **`mcp_bigquery.schema_explorer._formatters`** — Shared serializers for timestamps, schema trees, partition/clustering summaries.
  - Shared dependencies: `validators`, `clients`, `exceptions`, `_formatters`.

## Information Schema & Performance
- **`mcp_bigquery.info_schema.queries`** — INFORMATION_SCHEMA templating, dry-run execution, and error normalization.
- **`mcp_bigquery.info_schema.performance`** — Query plan inspection and heuristic suggestions (data scan size, joins, etc.).
- **`mcp_bigquery.info_schema._templates`** — Central repository for INFORMATION_SCHEMA SQL templates.

## Shared Utilities
- **`mcp_bigquery.logging_config`** — Structured logging, level resolution helpers, stderr-first handlers, and performance decorators.
- **`mcp_bigquery.validators`** — Pydantic models + helper to surface `InvalidParameterError` instances consistently.
- **`mcp_bigquery.cache`** — Query/schema caches and the BigQuery client cache consumed by the `clients` package.

## Dependency Highlights
- `schema_explorer` and `info_schema` modules never import each other; both rely on `clients.factory` for BigQuery access and `validators` for input safety.
- `server` remains the sole entrypoint that touches `sql_analyzer`, minimizing cross-module coupling.
- Logging flows through `logging_config` only; no other module calls `logging.basicConfig`, ensuring consistent stdout/stderr behaviour.

Refer back to `TODO_v0.4.2.md` for outstanding chores tied to this architecture.
