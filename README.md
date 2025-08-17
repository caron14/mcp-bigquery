# mcp-bigquery

![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)
[![PyPI](https://img.shields.io/pypi/v/mcp-bigquery.svg)](https://pypi.org/project/mcp-bigquery/)
![PyPI - Downloads](https://img.shields.io/pypi/dd/mcp-bigquery)

<p align="center">
  <img src="docs/assets/images/logo.png" alt="mcp-bigquery logo" width="200">
</p>

The `mcp-bigquery` package provides a comprehensive MCP server for BigQuery SQL validation, dry-run analysis, and query structure analysis. This server provides five tools for validating, analyzing, and understanding BigQuery SQL queries without executing them.

** IMPORTANT: This server does NOT execute queries. All operations are dry-run only. Cost estimates are approximations based on bytes processed.**

## Features

- **SQL Validation**: Check BigQuery SQL syntax without running queries
- **Dry-Run Analysis**: Get cost estimates, referenced tables, and schema preview
- **Query Structure Analysis**: Analyze SQL complexity, JOINs, CTEs, and query patterns
- **Dependency Extraction**: Extract table and column dependencies from queries
- **Enhanced Syntax Validation**: Detailed error reporting with suggestions
- **Parameter Support**: Validate parameterized queries
- **Cost Estimation**: Calculate USD estimates based on bytes processed

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

Run tests with pytest:

```bash
# Run all tests (requires BigQuery credentials)
pytest tests/

# Run only tests that don't require credentials
pytest tests/test_min.py::TestWithoutCredentials
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