# mcp-bigquery

[![PyPI](https://img.shields.io/pypi/v/mcp-bigquery.svg)](https://pypi.org/project/mcp-bigquery/)
![PyPI - Downloads](https://img.shields.io/pypi/dd/mcp-bigquery)

The `mcp-bigquery` package provides a minimal MCP server for BigQuery SQL validation and dry-run analysis. This server provides exactly two tools for validating and analyzing BigQuery SQL queries without executing them.

** IMPORTANT: This server does NOT execute queries. All operations are dry-run only. Cost estimates are approximations based on bytes processed.**

## Features

- **SQL Validation**: Check BigQuery SQL syntax without running queries
- **Dry-Run Analysis**: Get cost estimates, referenced tables, and schema preview
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

Apache-2.0

## Changelog

### 0.1.0 (2024-12-16)
- Initial release
- Renamed from mcp-bigquery-dryrun to mcp-bigquery
- SQL validation tool (bq_validate_sql)
- Dry-run analysis tool (bq_dry_run_sql)
- Cost estimation based on bytes processed
- Support for parameterized queries