---
type: Source Map
title: MCP BigQuery source map
description: "Change-oriented map of the MCP BigQuery package, tests, public documentation, and automation to their responsibilities and dependencies."
resource: "src/mcp_bigquery/"
tags: [source-map, architecture, python, mcp]
---

# MCP BigQuery source map

## Runtime package

| Path | Responsibility | Start here when changing |
| --- | --- | --- |
| `__main__.py` | Console arguments, config/log startup, process exit behavior | CLI flags or startup failures |
| `server.py` | MCP server, all tool schemas, dispatch, SQL dry-run handlers | Tool surface or query behavior |
| `sql_analyzer.py` | `sqlparse` dependency extraction and static syntax heuristics | Local SQL analysis |
| `config.py` | Environment-backed config singleton | New settings or feature gates |
| `clients/factory.py` | Target resolution, client construction, early dry-run validation, retry | Connectivity, ADC, project/location behavior |
| `cache.py` | Lock-protected client reuse by project/location | Client lifecycle/concurrency |
| `validators.py` | Pydantic schema-explorer request models | Input contract changes |
| `exceptions.py` | Domain error classes and Google API translation | User-visible error semantics |
| `logging_config.py` | Logger/format/level setup and performance decorator | Logging consistency |
| `utils.py`, `constants.py`, `types.py` | Response/error helpers, shared enums/patterns, common types | Shared contract support |

The [architecture overview](architecture/overview.md) explains how `server.py` **depends on** this infrastructure rather than owning direct configuration or cloud-client lifecycle.

## Schema explorer package

| Path | Responsibility |
| --- | --- |
| `schema_explorer/datasets.py` | Validated dataset listing with full metadata lookup |
| `schema_explorer/tables.py` | Table listing, metadata summaries, and comprehensive table information |
| `schema_explorer/describe.py` | Recursive schema serialization, formatting, and partition details |
| `schema_explorer/preview.py` | Explicitly gated row preview and JSON-safe value serialization |
| `schema_explorer/__init__.py` | Public helper exports consumed by the server |

These modules **implement** the [schema exploration workflow](workflows/schema-exploration.md). Their common client and validation dependencies mean that a cross-cutting API change often needs coordinated edits to a request model, helper, server tool declaration, test mock, and public documentation.

## Tests, packaging, and public documentation

- `tests/test_core.py` is the single current core unit suite; read [testing guidance](testing.md) before adding or reorganizing coverage.
- `tests/conftest.py` sets source-path support for the test package.
- `pyproject.toml` defines package metadata, the `mcp-bigquery` console script, dependencies, tool settings, and test discovery.
- `README.md` is the main installation/tool/configuration overview.
- `docs/usage.md`, `docs/development.md`, and `docs/module_map.md` provide published operational and contributor detail; `mkdocs.yml` defines navigation and MkDocs behavior.
- `.github/workflows/ci.yml` enforces formatting and credential-free tests; `.github/workflows/docs.yml` validates/deploys MkDocs; `.github/workflows/openwiki-update.yml` refreshes this generated wiki.

## Recent evolution landmarks

The v0.7.0 series added the `bq_preview_table` public contract (`d4f569b`), concrete list-row and serialization implementation (`8e7522d`), tests (`bcb86ce`), and user documentation (`3675aeb`). Earlier work centralized BigQuery client handling and mapped errors (`4e821d7`), with follow-up concurrency/validation coverage (`533ca4d`). These are design landmarks rather than a complete changelog: when changing either domain, keep the safety and cache rationale in [architecture overview](architecture/overview.md) intact.
