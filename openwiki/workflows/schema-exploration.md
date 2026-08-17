---
type: Workflow
title: BigQuery schema exploration and guarded preview
description: "How MCP BigQuery validates requests, retrieves datasets and table metadata, serializes schemas, and optionally previews rows behind an explicit privacy gate."
resource: "src/mcp_bigquery/schema_explorer/"
tags: [workflow, bigquery, schema, privacy]
---

# BigQuery schema exploration and guarded preview

## Capability boundary

This workflow supports investigation of BigQuery structure: datasets, tables, table schemas, and table metadata. It uses the same client infrastructure as [architecture overview](../architecture/overview.md), but input validation, response shaping, and cloud error conversion live in `src/mcp_bigquery/schema_explorer/`.

| Tool | Implementation | Notable result content |
| --- | --- | --- |
| `bq_list_datasets` | `datasets.py` | dataset location, timestamps, descriptions, labels, default expirations |
| `bq_list_tables` | `tables.py` | type, storage/row counts, partitioning and clustering summary |
| `bq_describe_table` | `describe.py` | recursively serialized schema, metadata, optional formatted table |
| `bq_get_table_info` | `tables.py` | comprehensive table details, storage statistics, type-specific attributes |
| `bq_preview_table` | `preview.py` | up to ten serialized rows, only after opt-in |

## Request-to-response flow

1. An MCP request reaches the dispatcher in `server.py`.
2. Each schema helper creates a Pydantic request model via `validate_request`.
3. The helper resolves a cached client for the optional request project or default configured project.
4. It calls BigQuery metadata APIs (`list_datasets`, `list_tables`, `get_table`) or preview’s row API.
5. Expected repository errors are serialized with `format_error_response`; unexpected errors are wrapped in an operation-specific code.

`validators.py` constrains project IDs against a GCP-style pattern, requires nonempty dataset/table IDs up to 1024 characters, limits list sizes to 1–10,000, and limits preview input to at least one row. `list_tables` additionally accepts only table types defined in `constants.TableType`.

## Metadata depth

Dataset listing fetches each listed dataset’s full reference to include location, creation/modification time, labels, description, and default expiration settings. Table listing fetches full table references so it can include table type, labels, size/row counts, location, and optional partition/clustering information.

`describe_table` recursively serializes nested schema fields and can render a human-oriented `tabulate` table when `format_output=true`. `get_table_info` expands metadata beyond that schema view: logical/physical and long-term storage figures, encryption configuration, time-travel settings for tables, view definitions, materialized-view refresh settings, external source configuration, and streaming-buffer metadata when available.

## Preview is intentionally exceptional

The v0.7.0 history added `bq_preview_table` as a cost-free way to inspect records: it uses `client.list_rows`, not a query job. The helper caps the actual request at **ten rows** even if a larger value is supplied. It serializes dates/times, decimals, bytes, nested values, and row-like mappings for JSON output.

That API can still disclose table contents to an LLM. Therefore `Config` defaults `MCP_BQ_ENABLE_PREVIEW` to false, and `preview_table` returns `PREVIEW_DISABLED` until the environment variable is explicitly set to `true`. The public README documents the same privacy rationale. Cost-free should never be described as data-risk-free.

This privacy gate **is configured through** the shared configuration layer and **is surfaced by** the [MCP server](../architecture/overview.md). Any new row-returning behavior must follow the same explicit-risk review rather than being grouped casually with metadata.

## Change checklist

- Extend the appropriate Pydantic request model before relying on new arguments.
- Retain the public error payload convention rather than allowing cloud exceptions to escape.
- Reuse `get_bigquery_client`; do not sidestep project/location resolution, cache, or error mapping.
- For new metadata, mock only the BigQuery attributes your code reads and add an assertion to `tests/test_core.py`.
- For preview changes, test disabled state, cap behavior, empty tables, serialization, and cloud errors; preserve opt-in by default.

See [testing guidance](../testing.md) for the existing mocking seam and [source map](../source-map.md) for concrete files.
