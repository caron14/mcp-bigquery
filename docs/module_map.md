# Module Responsibility Map (v0.4.2)

## Overview
This document lists the primary modules, their responsibilities, and notable internal dependencies to help contributors navigate the codebase.

### Metrics Snapshot
| Module | Functions | Classes |
| --- | ---:| ---:|
| `clients/factory.py` | 4 | 0 |
| `schema_explorer/datasets.py` | 2 | 0 |
| `schema_explorer/describe.py` | 2 | 0 |
| `schema_explorer/tables.py` | 4 | 0 |

## Core Runtime
- **`mcp_bigquery.server`** — Registers MCP tools, exposes stdio server entrypoints, and orchestrates calls into schema and SQL analysis layers.
  - Depends on: `clients`, `schema_explorer`, `sql_analyzer`, `validators`.
- **`mcp_bigquery.__main__`** — CLI entrypoint; now configures logging via `logging_config` and honors `--verbose/--quiet` flags.

## BigQuery Client Management
- **`mcp_bigquery.clients.factory`** — Single source for creating BigQuery clients with caching, retries, and authentication/configuration error handling.
  - Depends on: `config`, `cache`, `exceptions`, `logging_config`.

## Schema Exploration
- **`mcp_bigquery.schema_explorer.datasets`** — Dataset listing workflows with centralised validation and formatting helpers.
- **`mcp_bigquery.schema_explorer.tables`** — Table listing and detailed metadata aggregation (partitioning, clustering, constraints).
- **`mcp_bigquery.schema_explorer.describe`** — Schema-focused describe endpoint with nested-field formatting and shared serializers.
  - Shared dependencies: `validators`, `clients`, `exceptions`.

## Shared Utilities
- **`mcp_bigquery.logging_config`** — Log level resolution, basic formatting, and a simple performance decorator.
- **`mcp_bigquery.validators`** — Pydantic models + helper to surface `InvalidParameterError` instances consistently.
- **`mcp_bigquery.cache`** — Lightweight BigQuery client cache.

## Dependency Highlights
- `schema_explorer` modules rely on `clients.factory` for BigQuery access and `validators` for input safety.
- `server` remains the sole entrypoint that touches `sql_analyzer`, minimizing cross-module coupling.
- Logging flows through `logging_config` only; no other module calls `logging.basicConfig`, ensuring consistent stdout/stderr behaviour.

Refer back to `TODO_v0.4.2.md` for outstanding chores tied to this architecture.
