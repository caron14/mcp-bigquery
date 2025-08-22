# mcp-bigquery

![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)
[![PyPI](https://img.shields.io/pypi/v/mcp-bigquery.svg)](https://pypi.org/project/mcp-bigquery/)
![PyPI - Downloads](https://img.shields.io/pypi/dd/mcp-bigquery)

<p align="center">
  <img src="docs/assets/images/logo.png" alt="mcp-bigquery logo" width="200">
</p>

The `mcp-bigquery` package provides a comprehensive MCP server for BigQuery SQL validation, dry-run analysis, query structure analysis, and schema discovery. This server provides eleven tools for validating, analyzing, understanding BigQuery SQL queries, and exploring BigQuery schemas without executing queries.

** IMPORTANT: This server does NOT execute queries. All operations are dry-run only. Cost estimates are approximations based on bytes processed.**

## Features

### SQL Analysis & Validation
- **SQL Validation**: Check BigQuery SQL syntax without running queries
- **Dry-Run Analysis**: Get cost estimates, referenced tables, and schema preview
- **Query Structure Analysis**: Analyze SQL complexity, JOINs, CTEs, and query patterns
- **Dependency Extraction**: Extract table and column dependencies from queries
- **Enhanced Syntax Validation**: Detailed error reporting with suggestions
- **Performance Analysis**: Query performance scoring and optimization suggestions

### Schema Discovery & Metadata (v0.4.0)
- **Dataset Explorer**: List and explore datasets in your BigQuery project
- **Table Browser**: Browse tables with metadata, partitioning, and clustering info
- **Schema Inspector**: Get detailed table schemas with nested field support
- **INFORMATION_SCHEMA Access**: Safe querying of BigQuery metadata views
- **Comprehensive Table Info**: Access all table metadata including encryption and time travel

### Additional Features
- **Parameter Support**: Validate parameterized queries
- **Cost Estimation**: Calculate USD estimates based on bytes processed
- **Safe Operations**: All operations are dry-run only, no query execution

## Quick Start

### Prerequisites

- Python 3.10+
- Google Cloud SDK with BigQuery API enabled
- Application Default Credentials configured

### Installation

#### From PyPI (Recommended)

```bash
# Install from PyPI
pip install mcp-bigquery

# Or with uv
uv pip install mcp-bigquery
```

#### From Source

```bash
# Clone the repository
git clone https://github.com/caron14/mcp-bigquery.git
cd mcp-bigquery

# Install with uv (recommended)
uv pip install -e .

# Or install with pip
pip install -e .
```

### Authentication

Set up Application Default Credentials:

```bash
gcloud auth application-default login
```

Or use a service account key:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### Configuration

#### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BQ_PROJECT` | GCP project ID | From ADC |
| `BQ_LOCATION` | BigQuery location (e.g., US, EU, asia-northeast1) | None |
| `SAFE_PRICE_PER_TIB` | Default price per TiB for cost estimation | 5.0 |
| `DEBUG` | Enable debug logging (set to any value) | None |

#### Claude Code Integration

Add to your Claude Code configuration:

```json
{
  "mcpServers": {
    "mcp-bigquery": {
      "command": "mcp-bigquery",
      "env": {
        "BQ_PROJECT": "your-gcp-project",
        "BQ_LOCATION": "asia-northeast1",
        "SAFE_PRICE_PER_TIB": "5.0"
      }
    }
  }
}
```

Or if installed from source:

```json
{
  "mcpServers": {
    "mcp-bigquery": {
      "command": "python",
      "args": ["-m", "mcp_bigquery"],
      "env": {
        "BQ_PROJECT": "your-gcp-project",
        "BQ_LOCATION": "asia-northeast1",
        "SAFE_PRICE_PER_TIB": "5.0"
      }
    }
  }
}
```

## Tools

### bq_validate_sql

Validate BigQuery SQL syntax without executing the query.

**Input:**
```json
{
  "sql": "SELECT * FROM dataset.table WHERE id = @id",
  "params": {"id": "123"}  // Optional
}
```

**Success Response:**
```json
{
  "isValid": true
}
```

**Error Response:**
```json
{
  "isValid": false,
  "error": {
    "code": "INVALID_SQL",
    "message": "Syntax error at [3:15]",
    "location": {
      "line": 3,
      "column": 15
    },
    "details": [...]  // Optional
  }
}
```

### bq_dry_run_sql

Perform a dry-run to get cost estimates and metadata without executing the query.

**Input:**
```json
{
  "sql": "SELECT * FROM dataset.table",
  "params": {"id": "123"},  // Optional
  "pricePerTiB": 6.0  // Optional, overrides default
}
```

**Success Response:**
```json
{
  "totalBytesProcessed": 1073741824,
  "usdEstimate": 0.005,
  "referencedTables": [
    {
      "project": "my-project",
      "dataset": "my_dataset",
      "table": "my_table"
    }
  ],
  "schemaPreview": [
    {
      "name": "id",
      "type": "STRING",
      "mode": "NULLABLE"
    },
    {
      "name": "created_at",
      "type": "TIMESTAMP",
      "mode": "REQUIRED"
    }
  ]
}
```

**Error Response:**
```json
{
  "error": {
    "code": "INVALID_SQL",
    "message": "Table not found: dataset.table",
    "details": [...]  // Optional
  }
}
```

### bq_analyze_query_structure

Analyze BigQuery SQL query structure and complexity.

**Input:**
```json
{
  "sql": "SELECT u.name, COUNT(*) FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.name",
  "params": {}  // Optional
}
```

**Success Response:**
```json
{
  "query_type": "SELECT",
  "has_joins": true,
  "has_subqueries": false,
  "has_cte": false,
  "has_aggregations": true,
  "has_window_functions": false,
  "has_union": false,
  "table_count": 2,
  "complexity_score": 15,
  "join_types": ["LEFT"],
  "functions_used": ["COUNT"]
}
```

### bq_extract_dependencies

Extract table and column dependencies from BigQuery SQL.

**Input:**
```json
{
  "sql": "SELECT u.name, u.email FROM users u WHERE u.created_at > '2023-01-01'",
  "params": {}  // Optional
}
```

**Success Response:**
```json
{
  "tables": [
    {
      "project": null,
      "dataset": "users",
      "table": "u",
      "full_name": "users.u"
    }
  ],
  "columns": ["created_at", "email", "name"],
  "dependency_graph": {
    "users.u": ["created_at", "email", "name"]
  },
  "table_count": 1,
  "column_count": 3
}
```

### bq_validate_query_syntax

Enhanced syntax validation with detailed error reporting.

**Input:**
```json
{
  "sql": "SELECT * FROM users WHERE name = 'John' LIMIT 10",
  "params": {}  // Optional
}
```

**Success Response:**
```json
{
  "is_valid": true,
  "issues": [
    {
      "type": "performance",
      "message": "SELECT * may impact performance - consider specifying columns",
      "severity": "warning"
    },
    {
      "type": "consistency",
      "message": "LIMIT without ORDER BY may return inconsistent results",
      "severity": "warning"
    }
  ],
  "suggestions": [
    "Specify exact columns needed instead of using SELECT *",
    "Add ORDER BY clause before LIMIT for consistent results"
  ],
  "bigquery_specific": {
    "uses_legacy_sql": false,
    "has_array_syntax": false,
    "has_struct_syntax": false
  }
}
```

### bq_list_datasets

List all datasets in the BigQuery project.

**Input:**
```json
{
  "project_id": "my-project",  // Optional, uses default if not provided
  "max_results": 100  // Optional
}
```

**Success Response:**
```json
{
  "project": "my-project",
  "dataset_count": 2,
  "datasets": [
    {
      "dataset_id": "analytics",
      "project": "my-project",
      "location": "US",
      "created": "2024-01-01T00:00:00",
      "modified": "2024-06-01T00:00:00",
      "description": "Analytics data",
      "labels": {"env": "production"},
      "default_table_expiration_ms": null,
      "default_partition_expiration_ms": null
    }
  ]
}
```

### bq_list_tables

List all tables in a BigQuery dataset with metadata.

**Input:**
```json
{
  "dataset_id": "analytics",
  "project_id": "my-project",  // Optional
  "max_results": 100,  // Optional
  "table_type_filter": ["TABLE", "VIEW"]  // Optional: TABLE, VIEW, EXTERNAL, MATERIALIZED_VIEW
}
```

**Success Response:**
```json
{
  "dataset_id": "analytics",
  "project": "my-project",
  "table_count": 3,
  "tables": [
    {
      "table_id": "users",
      "dataset_id": "analytics",
      "project": "my-project",
      "table_type": "TABLE",
      "created": "2024-01-15T00:00:00",
      "modified": "2024-06-20T00:00:00",
      "description": "User data table",
      "labels": {},
      "num_bytes": 1048576,
      "num_rows": 10000,
      "location": "US",
      "partitioning": {
        "type": "DAY",
        "field": "created_at",
        "expiration_ms": null
      },
      "clustering_fields": ["user_id"]
    }
  ]
}
```

### bq_describe_table

Get table schema, metadata, and statistics.

**Input:**
```json
{
  "table_id": "users",
  "dataset_id": "analytics",
  "project_id": "my-project",  // Optional
  "format_output": false  // Optional: format schema as table
}
```

**Success Response:**
```json
{
  "table_id": "users",
  "dataset_id": "analytics",
  "project": "my-project",
  "table_type": "TABLE",
  "schema": [
    {
      "name": "user_id",
      "type": "INTEGER",
      "mode": "REQUIRED",
      "description": "Unique user identifier"
    },
    {
      "name": "name",
      "type": "STRING",
      "mode": "NULLABLE",
      "description": "User full name"
    },
    {
      "name": "address",
      "type": "RECORD",
      "mode": "NULLABLE",
      "description": "User address",
      "fields": [
        {
          "name": "street",
          "type": "STRING",
          "mode": "NULLABLE",
          "description": "Street address"
        },
        {
          "name": "city",
          "type": "STRING",
          "mode": "NULLABLE",
          "description": "City"
        }
      ]
    }
  ],
  "description": "User data table",
  "created": "2024-01-15T00:00:00",
  "modified": "2024-06-20T00:00:00",
  "statistics": {
    "num_bytes": 1048576,
    "num_rows": 10000,
    "num_long_term_bytes": 524288
  },
  "partitioning": {
    "type": "DAY",
    "field": "created_at"
  },
  "clustering_fields": ["user_id"]
}
```

### bq_get_table_info

Get comprehensive table information including all metadata.

**Input:**
```json
{
  "table_id": "users",
  "dataset_id": "analytics",
  "project_id": "my-project"  // Optional
}
```

**Success Response:**
```json
{
  "table_id": "users",
  "dataset_id": "analytics",
  "project": "my-project",
  "full_table_id": "my-project.analytics.users",
  "table_type": "TABLE",
  "created": "2024-01-15T00:00:00",
  "modified": "2024-06-20T00:00:00",
  "expires": null,
  "description": "User data table",
  "labels": {"team": "analytics"},
  "location": "US",
  "self_link": "https://bigquery.googleapis.com/...",
  "etag": "abc123",
  "friendly_name": "User Table",
  "statistics": {
    "creation_time": "2024-01-15T00:00:00",
    "num_bytes": 1048576,
    "num_rows": 10000,
    "num_active_logical_bytes": 786432,
    "num_long_term_logical_bytes": 262144
  },
  "time_travel": {
    "max_time_travel_hours": 168
  },
  "partitioning": {
    "type": "DAY",
    "time_partitioning": {
      "type": "DAY",
      "field": "created_at",
      "require_partition_filter": false
    }
  },
  "clustering": {
    "fields": ["user_id"]
  }
}
```

### bq_query_info_schema

Query INFORMATION_SCHEMA views for metadata.

**Input:**
```json
{
  "query_type": "columns",  // tables, columns, table_storage, partitions, views, routines, custom
  "dataset_id": "analytics",
  "project_id": "my-project",  // Optional
  "table_filter": "users",  // Optional
  "limit": 100  // Optional
}
```

**Success Response:**
```json
{
  "query_type": "columns",
  "dataset_id": "analytics",
  "project": "my-project",
  "query": "SELECT ... FROM `my-project.analytics.INFORMATION_SCHEMA.COLUMNS` ...",
  "schema": [
    {
      "name": "table_name",
      "type": "STRING",
      "mode": "NULLABLE"
    },
    {
      "name": "column_name",
      "type": "STRING",
      "mode": "NULLABLE"
    }
  ],
  "metadata": {
    "total_bytes_processed": 1024,
    "estimated_cost_usd": 0.000005,
    "cache_hit": false
  },
  "info": "Query validated successfully. Execute without dry_run to get actual results."
}
```

### bq_analyze_query_performance

Analyze query performance and provide optimization suggestions.

**Input:**
```json
{
  "sql": "SELECT * FROM large_table WHERE date > '2024-01-01'",
  "project_id": "my-project"  // Optional
}
```

**Success Response:**
```json
{
  "query_analysis": {
    "bytes_processed": 107374182400,
    "bytes_billed": 107374182400,
    "gigabytes_processed": 100.0,
    "estimated_cost_usd": 0.5,
    "referenced_tables": [
      {
        "project": "my-project",
        "dataset": "analytics",
        "table": "large_table",
        "full_id": "my-project.analytics.large_table"
      }
    ],
    "table_count": 1
  },
  "performance_score": 65,
  "performance_rating": "GOOD",
  "optimization_suggestions": [
    {
      "type": "SELECT_STAR",
      "severity": "MEDIUM",
      "message": "Query uses SELECT * which processes all columns",
      "recommendation": "Select only the columns you need to reduce data processed"
    },
    {
      "type": "HIGH_DATA_SCAN",
      "severity": "HIGH",
      "message": "Query will process 100.0 GB of data",
      "recommendation": "Consider adding WHERE clauses, using partitioning, or limiting date ranges"
    }
  ],
  "suggestion_count": 2,
  "estimated_execution": {
    "note": "Actual execution time depends on cluster resources and current load",
    "complexity_indicator": "HIGH"
  }
}
```

## Examples

### Validate a Simple Query

```python
# Tool: bq_validate_sql
{
  "sql": "SELECT 1"
}
# Returns: {"isValid": true}
```

### Validate with Parameters

```python
# Tool: bq_validate_sql
{
  "sql": "SELECT * FROM users WHERE name = @name AND age > @age",
  "params": {
    "name": "Alice",
    "age": 25
  }
}
```

### Get Cost Estimate

```python
# Tool: bq_dry_run_sql
{
  "sql": "SELECT * FROM `bigquery-public-data.samples.shakespeare`",
  "pricePerTiB": 5.0
}
# Returns bytes processed, USD estimate, and schema
```

### Analyze Complex Query

```python
# Tool: bq_dry_run_sql
{
  "sql": """
    WITH user_stats AS (
      SELECT user_id, COUNT(*) as order_count
      FROM orders
      GROUP BY user_id
    )
    SELECT * FROM user_stats WHERE order_count > 10
  """
}
```

### Analyze Query Structure

```python
# Tool: bq_analyze_query_structure
{
  "sql": """
    WITH ranked_products AS (
      SELECT 
        p.name,
        p.price,
        ROW_NUMBER() OVER (PARTITION BY p.category ORDER BY p.price DESC) as rank
      FROM products p
      JOIN categories c ON p.category_id = c.id
    )
    SELECT * FROM ranked_products WHERE rank <= 3
  """
}
# Returns: Complex query analysis with CTE, window functions, and JOINs
```

### Extract Query Dependencies

```python
# Tool: bq_extract_dependencies
{
  "sql": "SELECT u.name, u.email, o.total FROM users u LEFT JOIN orders o ON u.id = o.user_id"
}
# Returns: Tables (users, orders) and columns (name, email, total, id, user_id)
```

### Enhanced Syntax Validation

```python
# Tool: bq_validate_query_syntax
{
  "sql": "SELECT * FROM users WHERE name = 'John' LIMIT 10"
}
# Returns: Validation with performance warnings and suggestions
```

### Validate BigQuery-Specific Syntax

```python
# Tool: bq_validate_query_syntax
{
  "sql": "SELECT ARRAY[1, 2, 3] as numbers, STRUCT('John' as name, 25 as age) as person"
}
# Returns: Validation recognizing BigQuery ARRAY and STRUCT syntax
```

## Testing

### Test Organization

The test suite is organized into multiple files:
- `test_features.py` - Comprehensive tests for all MCP tools and features (no credentials required)
- `test_min.py` - Minimal tests that require BigQuery credentials
- `test_integration.py` - Integration tests with real BigQuery API
- `test_imports.py` - Import and package structure validation

### Running Tests

```bash
# Install test dependencies
uv pip install -e ".[dev]"

# Run all tests
pytest tests/

# Run tests with coverage report
pytest --cov=mcp_bigquery --cov-report=term-missing tests/

# Run specific test files
pytest tests/test_features.py  # No credentials required
pytest tests/test_min.py       # Requires BigQuery credentials

# Run tests matching a pattern
pytest tests/ -k "test_list_datasets"

# Run with verbose output
pytest tests/ -v
```

### Test Coverage

Current test coverage: **75%**

```bash
# Generate HTML coverage report
pytest --cov=mcp_bigquery --cov-report=html tests/
# Open htmlcov/index.html in browser

# Show coverage for specific modules
pytest --cov=mcp_bigquery.server tests/
```

### Testing Without Credentials

Many tests use mocks and don't require BigQuery credentials:

```bash
# Run only mock-based tests
pytest tests/test_features.py
```

### Testing With Credentials

For integration tests, set up Google Cloud authentication:

```bash
# Set up Application Default Credentials
gcloud auth application-default login

# Run integration tests
pytest tests/test_integration.py
```

## Development

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Run the server locally
python -m mcp_bigquery

# Or using the console script
mcp-bigquery
```

## Limitations

- **No Query Execution**: This server only performs dry-runs and validation
- **Cost Estimates**: USD estimates are approximations based on bytes processed
- **Parameter Types**: Initial implementation treats all parameters as STRING type
- **Cache Disabled**: Queries always run with `use_query_cache=False` for accurate estimates

## License

MIT

## Changelog

### 0.4.1 (2025-08-22)
- **Stability Improvements**: Enhanced error handling and input validation
- **Better Error Messages**: More informative error messages with troubleshooting guidance
- **Input Validation**: Added comprehensive parameter validation for all schema explorer functions
- **Logging Support**: Added debug logging (enable with DEBUG environment variable)
- **Test Coverage**: All 47 tests passing with improved test reliability
- **Documentation**: Updated with v0.4.1 improvements and troubleshooting tips

### 0.4.0 (2025-08-22)
- **MAJOR FEATURE**: Added comprehensive schema discovery and metadata exploration
- **NEW TOOLS**: Six new tools for BigQuery schema and metadata operations
- **bq_list_datasets**: List all datasets in the project with metadata
- **bq_list_tables**: Browse tables with partitioning and clustering information
- **bq_describe_table**: Get detailed table schemas including nested fields
- **bq_get_table_info**: Access comprehensive table metadata and statistics
- **bq_query_info_schema**: Safe querying of INFORMATION_SCHEMA views
- **bq_analyze_query_performance**: Query performance analysis with optimization suggestions
- **Dependencies**: Added `tabulate` for enhanced table formatting
- **Backward Compatibility**: All existing tools remain unchanged
- **Testing**: Comprehensive test coverage for all new features

### 0.3.0 (2025-08-17)
- **NEW TOOLS**: Added three new SQL analysis tools for comprehensive query analysis
- **bq_analyze_query_structure**: Analyze SQL complexity, JOINs, CTEs, window functions, and calculate complexity scores
- **bq_extract_dependencies**: Extract table and column dependencies with dependency graph mapping
- **bq_validate_query_syntax**: Enhanced syntax validation with detailed error reporting and suggestions
- **SQL Analysis Engine**: New SQLAnalyzer class with comprehensive BigQuery SQL parsing capabilities
- **BigQuery-Specific Features**: Detection of ARRAY/STRUCT syntax, legacy SQL patterns, and BigQuery-specific validation
- **Backward Compatibility**: All existing tools (bq_validate_sql, bq_dry_run_sql) remain unchanged
- **Enhanced Documentation**: Updated with comprehensive examples for all five tools

### 0.2.1 (2025-08-16)
- Fixed GitHub Pages documentation layout issues
- Enhanced MkDocs Material theme compatibility
- Improved documentation dependencies and build process
- Added site/ directory to .gitignore
- Simplified documentation layout for better compatibility

### 0.2.0 (2025-08-16)
- Code quality improvements with pre-commit hooks
- Enhanced development setup with Black, Ruff, isort, and mypy
- Improved CI/CD pipeline
- Documentation enhancements

### 0.1.0 (2025-08-16)
- Initial release
- Renamed from mcp-bigquery-dryrun to mcp-bigquery
- SQL validation tool (bq_validate_sql)
- Dry-run analysis tool (bq_dry_run_sql)
- Cost estimation based on bytes processed
- Support for parameterized queries