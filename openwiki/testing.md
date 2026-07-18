---
type: Testing Guide
title: MCP BigQuery testing guidance
description: Credential-free unit-test strategy, mocked BigQuery seams, quality commands, CI matrix, and change-specific test expectations for MCP BigQuery.
resource: tests/test_core.py
tags: [testing, python, bigquery, ci]
---

# MCP BigQuery testing guidance

## What runs in CI

`.github/workflows/ci.yml` runs on pushes and pull requests targeting `main`. It checks isort and Black, then installs `.[dev]` and runs `pytest tests/test_core.py -v` on Python 3.10, 3.11, and 3.12. The workflow explicitly labels these as unit tests requiring no credentials.

Local commands should match that intent:

```bash
pytest tests/test_core.py -v
isort --check-only --diff .
black --check --diff .
ruff check src/ tests/
mypy src/
```

The build configuration enables strict mypy for the source package but ignores mypy errors under test modules. Formatting target and line length are set in `pyproject.toml`.

## Test layout and seams

The compact suite in `tests/test_core.py` concentrates on behavioral boundaries rather than live cloud integration:

- **Server contract:** tool registration count/names and conversion of generic query parameters to BigQuery string scalar parameters.
- **Static analysis:** basic dependency extraction and enhanced syntax validation through `SQLAnalyzer`.
- **Schema exploration:** mocks the module-local `get_bigquery_client` imports in datasets, tables, and describe helpers, then supplies only the BigQuery attributes each helper reads.
- **Infrastructure:** logging emits to stderr, client caching reuses objects, domain error mapping retains BadRequest details, identifier validation rejects invalid boundaries, and cache locking preserves one client under concurrent access.
- **Preview:** later portions of the suite cover the v0.7.0 preview behavior, including the guarded feature’s scenarios.

Patch the helper at the point where it is imported—for example, `mcp_bigquery.schema_explorer.datasets.get_bigquery_client`—rather than patching a different factory reference. This keeps tests isolated from ADC and real BigQuery calls.

## Test by change type

| Change | Minimum focused coverage |
| --- | --- |
| MCP tool registration | `handle_list_tools`; declaration and dispatch path |
| SQL analysis | representative SQL, including CTE/aliases when applicable; expected static result/error |
| Client/factory behavior | config fallback, mapped error/retry decision, cache reuse or concurrent access |
| Schema metadata | mocked API object fields read by code and serialized response shape |
| Validation model | accepted boundary and rejected input with expected `INVALID_PARAMETER` behavior |
| Preview/data return | disabled default, opt-in, maximum of ten rows, serialization, empty and cloud-error paths |

Tool and workflow rationale lives in [SQL safety](workflows/sql-safety.md) and [schema exploration](workflows/schema-exploration.md); tests should preserve those behavior contracts rather than merely raise line coverage.

## Gaps and cautions

No live BigQuery integration suite, test project configuration, or CI credentials were found. That is intentional for current CI portability, but it means mocked tests cannot prove IAM behavior, actual API pagination, regional behavior, or BigQuery’s final SQL semantics. Validate those manually in an approved non-production project when changing API integration, then keep the deterministic regression case in the unit suite.

The preview feature needs special review: its `list_rows` path avoids query-job scan cost but can expose returned values. A test that preview succeeds must not weaken the default-disabled assertion described in [schema exploration](workflows/schema-exploration.md).
