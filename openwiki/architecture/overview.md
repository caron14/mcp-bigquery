---
type: Architecture Overview
title: MCP server and BigQuery access architecture
description: Runtime architecture for the stdio MCP server, tool dispatcher, configuration, cached BigQuery client creation, logging, validation, and error translation.
resource: src/mcp_bigquery/server.py
tags: [architecture, mcp, bigquery, python]
---

# MCP server and BigQuery access architecture

## Runtime shape

The console entry point in `src/mcp_bigquery/__main__.py` reads CLI logging flags, loads the singleton configuration, configures stderr logging, and runs the async MCP server. `src/mcp_bigquery/server.py` owns the `Server("mcp-bigquery")` instance and communicates over MCP stdio.

```text
MCP host
  -> mcp-bigquery CLI
  -> stdio MCP server / TOOL_DEFS dispatcher
     -> SQL dry-run or static-analysis helpers
     -> schema exploration helpers
        -> request validation -> shared BigQuery client -> BigQuery APIs
```

The server **dispatches to** the [SQL safety workflow](../workflows/sql-safety.md) for query-oriented tools and **dispatches to** the [schema exploration workflow](../workflows/schema-exploration.md) for metadata and optional row retrieval. It serializes every handler result as JSON text in the MCP response.

## Tool registration and dispatch

`TOOL_DEFS` is the public MCP contract: names, descriptions, JSON schemas, and required fields appear there. `handle_list_tools` converts those definitions to MCP `types.Tool` values, while `handle_call_tool` maps names to async helpers. This central ownership means a new tool needs both a declaration and a handler mapping—not merely an implementation module.

Query parameters are converted to BigQuery `ScalarQueryParameter` values and currently serialized as `STRING`; do not infer richer parameter typing from the public MCP schema.

## Configuration and client lifecycle

`Config.from_env()` in `src/mcp_bigquery/config.py` reads these non-secret environment settings:

| Setting | Purpose | Default |
| --- | --- | --- |
| `BQ_PROJECT` | Default project when a tool omits `project_id` | ADC/client resolution |
| `BQ_LOCATION` | Client location | unset |
| `LOG_LEVEL` | Base log level | `WARNING` |
| `MCP_BQ_ENABLE_PREVIEW` | Enables row preview only when literal `true` | `false` |
| `SAFE_PRICE_PER_TIB` | Dry-run cost-estimate multiplier | `5.0` (read by the SQL handler) |

The factory resolves per-call project/location over configuration defaults, then creates a `google.cloud.bigquery.Client`. Creation performs `SELECT 1` as a dry run to surface credentials or permissions early. Transient Google Cloud failures retry with exponential backoff; authentication and permission failures fail immediately. Google API errors are translated into repository domain exceptions in `src/mcp_bigquery/exceptions.py`.

The factory **reuses clients through** the thread-safe `BigQueryClientCache`, keyed by resolved project and location. The cache holds its lock during construction, which is intentional for the existing concurrency guarantee: concurrent callers for one key receive the same client rather than duplicating initialization.

## Cross-cutting boundaries

- **Validation:** Pydantic request models in `validators.py` constrain identifiers, result limits, and allowed table types for schema APIs. Validation errors become `InvalidParameterError` and are formatted as normal tool payloads.
- **Errors:** schema helpers consistently catch `MCPBigQueryError` and return formatted `error` objects; the server’s SQL dry-run helpers have their own response-shaping logic. Preserve the relevant established contract when changing a tool.
- **Logging:** modules obtain loggers from `logging_config.py`; CLI options override the configured level. Logging goes to stderr so stdout remains suitable for stdio MCP traffic.
- **Async boundary:** MCP handlers and domain helpers are async, but BigQuery client operations are synchronous calls within them. Avoid claiming the BigQuery SDK calls are non-blocking.

## History-informed constraints

A refactor represented by `4e821d7` centralized client handling, error mapping, caching, and retry behavior; follow-up tests added validation-boundary and cache-concurrency coverage. The preview feature in the v0.7.0 series was added to this shared infrastructure rather than bypassing it, so its privacy gate is configuration-based and it obtains clients through the same factory.

## Change safely

- Modify `TOOL_DEFS` and the dispatcher together, then exercise `handle_list_tools` in tests.
- Keep project/location fallback in the factory; do not create ad hoc `bigquery.Client` instances in feature helpers.
- Map expected cloud failures through `exceptions.py` and return the response format already used by the domain.
- When changing config singleton behavior, reset it in tests to avoid leaking environment-derived state.

See [source map](../source-map.md) for implementation anchors and [testing guidance](../testing.md) for the repository’s mocked-client testing pattern.
