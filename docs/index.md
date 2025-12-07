# MCP BigQuery

<div align="center" markdown>

[![PyPI](https://img.shields.io/pypi/v/mcp-bigquery.svg)](https://pypi.org/project/mcp-bigquery/)
![PyPI - Downloads](https://img.shields.io/pypi/dd/mcp-bigquery)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

**A minimal MCP server for BigQuery SQL validation and dry-run analysis**

[Getting Started :material-rocket-launch:](installation.md){ .md-button .md-button--primary }
[View on GitHub :material-github:](https://github.com/caron14/mcp-bigquery){ .md-button }

</div>

## Overview

The `mcp-bigquery` package provides a comprehensive MCP server for BigQuery SQL validation, dry-run analysis, query structure analysis, and schema discovery. This server provides eleven tools for validating, analyzing, understanding BigQuery SQL queries, and exploring BigQuery schemas without executing queries.

!!! info "What's new in v0.4.2"
    - Schema explorer and INFORMATION_SCHEMA logic now live in dedicated subpackages with shared formatters.
    - BigQuery client creation is centralized in `mcp_bigquery.clients` so every tool inherits the same retries, caching, and dry-run safeguards.
    - Logging defaults to `WARNING` on stderr with `--verbose/--quiet`/`--json-logs` CLI switches for fine-grained control. See [Development](development.md#logging-and-debugging) for details.
    - Need a quick tour of the new layout? Read the [Module Responsibility Map](module_map.md).

!!! warning "Important"
    This server does **NOT** execute queries. All operations are dry-run only. Cost estimates are approximations based on bytes processed.

## Key Features

### 🔍 SQL Analysis & Validation
- **SQL Validation**: Check BigQuery SQL syntax without running queries
- **Dry-Run Analysis**: Get cost estimates, referenced tables, and schema preview
- **Query Structure Analysis**: Analyze SQL complexity, JOINs, CTEs, and query patterns
- **Dependency Extraction**: Extract table and column dependencies from queries
- **Enhanced Syntax Validation**: Detailed error reporting with suggestions
[→ SQL Analysis Guide](usage.md#sql-analysis)

### 📊 Schema Explorer & Metadata (updated v0.4.2)
- **Dataset Explorer**: List and explore datasets in your BigQuery project
- **Table Browser**: Browse tables with metadata, partitioning, and clustering info via dedicated formatters
- **Schema Inspector**: Get detailed table schemas with nested field support
- **INFORMATION_SCHEMA Access**: Safe querying of BigQuery metadata views
- **Comprehensive Table Info**: Access all table metadata including encryption and time travel using the new modular helpers
[→ Schema Discovery Guide](usage.md#schema-discovery)

### 🚀 Performance Analysis
- **Query Performance Scoring**: Analyze query performance without execution
- **Optimization Suggestions**: Get actionable recommendations for query improvements
- **Cost-Benefit Analysis**: Compare costs before and after optimizations
[→ Performance Guide](usage.md#performance-analysis)

### 🏷️ Additional Features
- **Parameter Support**: Validate parameterized queries
- **Safe Operations**: All operations are dry-run only, no query execution
- **BigQuery-Specific**: Support for ARRAY, STRUCT, and other BigQuery features
- **Structured Logging**: CLI exposes `--verbose/--quiet`, `--json-logs`, and `--no-color` flags governed by `logging_config`
[→ Advanced Features](usage.md#advanced-features)

## Quick Example

=== "SQL Validation"

    ```json
    {
      "tool": "bq_validate_sql",
      "arguments": {
        "sql": "SELECT * FROM `project.dataset.table` WHERE date = @date",
        "params": {"date": "2024-01-01"}
      }
    }
    ```

    **Response:**
    ```json
    {
      "isValid": true
    }
    ```

=== "Cost Estimation"

    ```json
    {
      "tool": "bq_dry_run_sql",
      "arguments": {
        "sql": "SELECT * FROM `bigquery-public-data.samples.shakespeare`"
      }
    }
    ```

    **Response:**
    ```json
    {
      "totalBytesProcessed": 1073741824,
      "usdEstimate": 0.005,
      "referencedTables": [
        {
          "project": "bigquery-public-data",
          "dataset": "samples",
          "table": "shakespeare"
        }
      ]
    }
    ```

=== "Schema Discovery"

    ```json
    {
      "tool": "bq_list_tables",
      "arguments": {
        "dataset_id": "samples",
        "project_id": "bigquery-public-data"
      }
    }
    ```

    **Response:**
    ```json
    {
      "dataset_id": "samples",
      "table_count": 3,
      "tables": [
        {
          "table_id": "shakespeare",
          "table_type": "TABLE",
          "num_rows": 164656,
          "num_bytes": 6432064
        }
      ]
    }
    ```

=== "Performance Analysis"

    ```json
    {
      "tool": "bq_analyze_query_performance",
      "arguments": {
        "sql": "SELECT * FROM large_table WHERE date > '2024-01-01'"
      }
    }
    ```

    **Response:**
    ```json
    {
      "performance_score": 65,
      "performance_rating": "GOOD",
      "optimization_suggestions": [
        {
          "type": "SELECT_STAR",
          "severity": "MEDIUM",
          "recommendation": "Select only needed columns"
        }
      ]
    }
    ```

## Installation

Install from PyPI:

```bash
pip install mcp-bigquery
```

Or with uv:

```bash
uv pip install mcp-bigquery
```

[Get Started :material-arrow-right:](installation.md){ .md-button .md-button--primary }

## Use Cases

### Development Workflow

- Validate SQL syntax during development
- Estimate query costs before execution
- Preview result schemas without running queries
- Test parameterized queries safely

### CI/CD Integration

- Automated SQL validation in pull requests
- Cost threshold checks in pipelines
- Schema compatibility verification
- Query optimization validation

### Cost Optimization

- Identify expensive queries before execution
- Compare cost estimates for different approaches
- Monitor query complexity trends
- Optimize data access patterns

## Documentation

### 🚀 [Installation](installation.md)
Setup, authentication, and configuration

### 📖 [Usage Guide](usage.md)
SQL validation, dry-run analysis, and best practices

### 📋 [API Reference](api-reference.md)
Complete tool documentation and schemas

### 💻 [Examples](examples.md)
Real-world queries and patterns

## Support

- **Issues**: [GitHub Issues](https://github.com/caron14/mcp-bigquery/issues)
- **Discussions**: [GitHub Discussions](https://github.com/caron14/mcp-bigquery/discussions)
- **Source Code**: [GitHub Repository](https://github.com/caron14/mcp-bigquery)

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/caron14/mcp-bigquery/blob/main/LICENSE) file for details.
