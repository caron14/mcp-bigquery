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

The `mcp-bigquery` package provides a Model Context Protocol (MCP) server that enables safe BigQuery SQL validation and analysis without executing queries. Perfect for development workflows, CI/CD pipelines, and cost optimization.

!!! warning "Important"
    This server does **NOT** execute queries. All operations are dry-run only. Cost estimates are approximations based on bytes processed.

## Key Features

### ✅ SQL Validation
Validate BigQuery SQL syntax without running queries. Catch errors early in your development workflow.
[→ Validation Guide](usage.md#sql-validation)

### 💰 Cost Estimation
Get accurate cost estimates based on bytes processed. Optimize queries before execution.
[→ Cost Estimation](usage.md#dry-run-analysis)

### 📊 Schema Preview
Preview result schemas and referenced tables without accessing actual data.
[→ Dry-Run Analysis](usage.md#dry-run-analysis)

### 🏷️ Parameter Support
Validate parameterized queries with full support for query parameters.
[→ Using Parameters](usage.md#using-parameters)

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