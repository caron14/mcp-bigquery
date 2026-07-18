---
type: Workflow
title: SQL validation, dry runs, and static analysis
description: How MCP BigQuery validates SQL and estimates cost with BigQuery dry runs while providing separate local dependency and syntax analysis.
resource: src/mcp_bigquery/server.py
tags: [workflow, sql, bigquery, safety]
---

# SQL validation, dry runs, and static analysis

## Why this workflow exists

The product is designed to let an AI assistant inspect a prospective BigQuery query without executing a data-processing job. The public README states that operations are limited to dry-run verification; the query-facing handlers implement that with `QueryJobConfig(dry_run=True, use_query_cache=False)`.

The [MCP server](../architecture/overview.md) dispatches four tools in this domain:

| Tool | Mechanism | Main output |
| --- | --- | --- |
| `bq_validate_sql` | BigQuery dry run | `isValid` plus structured error context |
| `bq_dry_run_sql` | BigQuery dry run | processed bytes, USD estimate, referenced tables, output-schema preview |
| `bq_extract_dependencies` | local `sqlparse` traversal | physical tables, columns, dependency graph |
| `bq_validate_query_syntax` | local heuristics | issues, suggestions, BigQuery-specific indicators |

## BigQuery-backed validation and estimation

`validate_sql` creates the shared client and submits the input with `dry_run=True`. A `BadRequest` becomes `INVALID_SQL`, optionally augmented with line/column details extracted from the BigQuery error and provider-supplied error details.

`dry_run_sql` uses the same dry-run mechanism, then derives a dollar estimate:

```text
USD estimate = total_bytes_processed / 2^40 * price_per_tib
```

`price_per_tib` precedence is tool argument `pricePerTiB`, then `SAFE_PRICE_PER_TIB`, then `5.0`. This is an estimate parameter, not a billing control. Referenced tables and schema preview come from the returned dry-run job metadata.

Both paths **depend on** the configured, cached BigQuery client in [architecture overview](../architecture/overview.md). That client’s creation validation is also a dry run, so authentication and access errors can occur before the requested SQL is checked.

## Local analysis is a separate capability

`SQLAnalyzer` in `src/mcp_bigquery/sql_analyzer.py` does not create a BigQuery client. It parses the first statement with `sqlparse`, identifies CTE names, excludes those temporary names from physical-table dependencies, and extracts table and column candidates. `extract_dependencies` builds a graph that maps each discovered physical table name to the extracted column set.

Enhanced syntax validation checks common and BigQuery-oriented patterns and reports whether legacy SQL marker, array syntax, or struct syntax appears. It is heuristic/static analysis, not a guarantee that BigQuery accepts or can access a query. Keep this distinction clear in tool descriptions, tests, and user-facing docs.

## Error and parameter behavior

- The MCP interface accepts an optional `params` object for query tools; the server currently converts every value to a string-valued BigQuery scalar parameter.
- Dry-run errors are returned in the handler’s JSON payload rather than propagated as a failed MCP call.
- Static-analysis failures return `ANALYSIS_ERROR` payloads.
- Schema exploration has a different validated request model and error boundary; see [schema exploration](schema-exploration.md) rather than applying SQL assumptions to metadata tools.

## Change checklist

1. For a new BigQuery-backed SQL behavior, preserve `dry_run=True` and `use_query_cache=False`; do not introduce execution-capable job configuration.
2. For parser changes, add SQL examples covering CTEs, qualified table names, aliases, wildcards, and the failure or false-positive behavior being addressed.
3. For cost behavior, test precedence and bytes-to-TiB conversion separately from cloud interactions.
4. Update `TOOL_DEFS`, handler dispatch, public README/docs, and the `TestSQLAnalyzer` or core-handler tests as applicable.

The current unit suite starts with straightforward dependency and enhanced-validation tests; [testing guidance](../testing.md) explains the broader test and CI constraints.
