# API Reference

## Tools

MCP BigQuery provides eleven comprehensive tools for SQL validation, analysis, and schema discovery.

### bq_validate_sql

Validates BigQuery SQL syntax without executing the query.

**Input Schema:**

```json
{
  "type": "object",
  "properties": {
    "sql": {
      "type": "string",
      "description": "The SQL query to validate"
    },
    "params": {
      "type": "object",
      "description": "Optional query parameters",
      "additionalProperties": true
    }
  },
  "required": ["sql"]
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sql` | string | Yes | The SQL query to validate |
| `params` | object | No | Query parameters as key-value pairs |

**Response (Success):**
```json
{
  "isValid": true
}
```

**Response (Error):**
```json
{
  "isValid": false,
  "error": {
    "code": "INVALID_SQL",
    "message": "Error description",
    "location": {
      "line": 1,
      "column": 15
    }
  }
}
```

### bq_dry_run_sql

Performs a dry-run analysis to estimate costs and preview schema.

**Input Schema:**

```json
{
  "type": "object",
  "properties": {
    "sql": {
      "type": "string",
      "description": "The SQL query to analyze"
    },
    "params": {
      "type": "object",
      "description": "Optional query parameters",
      "additionalProperties": true
    },
    "pricePerTiB": {
      "type": "number",
      "description": "Price per TiB for cost estimation",
      "default": 5.0
    }
  },
  "required": ["sql"]
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `sql` | string | Yes | - | The SQL query to analyze |
| `params` | object | No | {} | Query parameters |
| `pricePerTiB` | number | No | 5.0 | USD price per TiB |

**Response (Success):**
```json
{
  "totalBytesProcessed": 1073741824,
  "usdEstimate": 0.005,
  "referencedTables": [
    {
      "project": "project-id",
      "dataset": "dataset_name",
      "table": "table_name"
    }
  ],
  "schemaPreview": [
    {
      "name": "column_name",
      "type": "STRING",
      "mode": "NULLABLE",
      "description": "Column description"
    }
  ]
}
```

**Response (Error):**
```json
{
  "error": {
    "code": "INVALID_SQL",
    "message": "Error description",
    "details": []
  }
}
```

### bq_analyze_query_structure

Analyzes SQL query structure and complexity.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "sql": {
      "type": "string",
      "description": "The SQL query to analyze"
    },
    "params": {
      "type": "object",
      "description": "Optional query parameters"
    }
  },
  "required": ["sql"]
}
```

**Response:**
```json
{
  "query_type": "SELECT",
  "has_joins": true,
  "has_subqueries": false,
  "has_cte": true,
  "has_aggregations": true,
  "has_window_functions": false,
  "table_count": 2,
  "complexity_score": 25,
  "join_types": ["LEFT", "INNER"],
  "functions_used": ["COUNT", "SUM"]
}
```

### bq_extract_dependencies

Extracts table and column dependencies from SQL.

**Response:**
```json
{
  "tables": [
    {
      "project": "my-project",
      "dataset": "my_dataset",
      "table": "my_table",
      "full_name": "my-project.my_dataset.my_table"
    }
  ],
  "columns": ["id", "name", "created_at"],
  "dependency_graph": {
    "my_dataset.my_table": ["id", "name", "created_at"]
  },
  "table_count": 1,
  "column_count": 3
}
```

### bq_validate_query_syntax

Enhanced syntax validation with detailed error reporting.

**Response:**
```json
{
  "is_valid": true,
  "issues": [
    {
      "type": "performance",
      "message": "SELECT * may impact performance",
      "severity": "warning"
    }
  ],
  "suggestions": [
    "Specify exact columns needed instead of using SELECT *"
  ],
  "bigquery_specific": {
    "uses_legacy_sql": false,
    "has_array_syntax": false,
    "has_struct_syntax": true
  }
}
```

### bq_list_datasets

Lists all datasets in the BigQuery project.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "project_id": {
      "type": "string",
      "description": "GCP project ID (uses default if not provided)"
    },
    "max_results": {
      "type": "integer",
      "description": "Maximum number of datasets to return"
    }
  }
}
```

**Response:**
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
      "labels": {"env": "production"}
    }
  ]
}
```

### bq_list_tables

Lists all tables in a BigQuery dataset.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "dataset_id": {
      "type": "string",
      "description": "The dataset ID"
    },
    "project_id": {
      "type": "string",
      "description": "GCP project ID"
    },
    "max_results": {
      "type": "integer"
    },
    "table_type_filter": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Filter by table types (TABLE, VIEW, EXTERNAL, MATERIALIZED_VIEW)"
    }
  },
  "required": ["dataset_id"]
}
```

**Response:**
```json
{
  "dataset_id": "analytics",
  "project": "my-project",
  "table_count": 3,
  "tables": [
    {
      "table_id": "users",
      "table_type": "TABLE",
      "num_bytes": 1048576,
      "num_rows": 10000,
      "partitioning": {
        "type": "DAY",
        "field": "created_at"
      },
      "clustering_fields": ["user_id"]
    }
  ]
}
```

### bq_describe_table

Gets detailed table schema and metadata.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "table_id": {"type": "string"},
    "dataset_id": {"type": "string"},
    "project_id": {"type": "string"},
    "format_output": {
      "type": "boolean",
      "description": "Format schema as table"
    }
  },
  "required": ["table_id", "dataset_id"]
}
```

**Response:**
```json
{
  "table_id": "users",
  "dataset_id": "analytics",
  "table_type": "TABLE",
  "schema": [
    {
      "name": "user_id",
      "type": "INTEGER",
      "mode": "REQUIRED",
      "description": "Unique identifier"
    },
    {
      "name": "address",
      "type": "RECORD",
      "mode": "NULLABLE",
      "fields": [
        {
          "name": "street",
          "type": "STRING",
          "mode": "NULLABLE"
        }
      ]
    }
  ],
  "statistics": {
    "num_bytes": 1048576,
    "num_rows": 10000
  }
}
```

### bq_get_table_info

Gets comprehensive table information.

**Response:**
```json
{
  "table_id": "users",
  "dataset_id": "analytics",
  "full_table_id": "my-project.analytics.users",
  "table_type": "TABLE",
  "created": "2024-01-15T00:00:00",
  "statistics": {
    "num_bytes": 1048576,
    "num_rows": 10000,
    "num_active_logical_bytes": 786432
  },
  "time_travel": {
    "max_time_travel_hours": 168
  },
  "partitioning": {
    "type": "DAY",
    "time_partitioning": {
      "field": "created_at",
      "require_partition_filter": false
    }
  }
}
```

### bq_query_info_schema

Queries INFORMATION_SCHEMA views for metadata.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "query_type": {
      "type": "string",
      "enum": ["tables", "columns", "table_storage", "partitions", "views", "routines", "custom"]
    },
    "dataset_id": {"type": "string"},
    "project_id": {"type": "string"},
    "table_filter": {"type": "string"},
    "custom_query": {"type": "string"},
    "limit": {"type": "integer", "default": 100}
  },
  "required": ["query_type", "dataset_id"]
}
```

**Response:**
```json
{
  "query_type": "columns",
  "dataset_id": "analytics",
  "query": "SELECT ... FROM INFORMATION_SCHEMA.COLUMNS ...",
  "schema": [
    {
      "name": "column_name",
      "type": "STRING",
      "mode": "NULLABLE"
    }
  ],
  "metadata": {
    "total_bytes_processed": 1024,
    "estimated_cost_usd": 0.000005
  }
}
```

### bq_analyze_query_performance

Analyzes query performance and provides optimization suggestions.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "sql": {
      "type": "string",
      "description": "The SQL query to analyze"
    },
    "project_id": {"type": "string"}
  },
  "required": ["sql"]
}
```

**Response:**
```json
{
  "query_analysis": {
    "bytes_processed": 107374182400,
    "gigabytes_processed": 100.0,
    "estimated_cost_usd": 0.5,
    "table_count": 1
  },
  "performance_score": 65,
  "performance_rating": "GOOD",
  "optimization_suggestions": [
    {
      "type": "SELECT_STAR",
      "severity": "MEDIUM",
      "message": "Query uses SELECT *",
      "recommendation": "Select only needed columns"
    }
  ]
}
```

## Response Schemas

### Error Object

All error responses follow this structure:

```typescript
interface Error {
  code: "INVALID_SQL" | "AUTHENTICATION_ERROR" | "PERMISSION_DENIED";
  message: string;
  location?: {
    line: number;
    column: number;
  };
  details?: Array<{
    reason: string;
    location: string;
    message: string;
  }>;
}
```

### Table Reference

```typescript
interface TableReference {
  project: string;
  dataset: string;
  table: string;
}
```

### Schema Field

```typescript
interface SchemaField {
  name: string;
  type: "STRING" | "INT64" | "FLOAT64" | "BOOL" | "TIMESTAMP" | "DATE" | "TIME" | "DATETIME" | "GEOGRAPHY" | "NUMERIC" | "BIGNUMERIC" | "BYTES" | "STRUCT" | "ARRAY" | "JSON";
  mode: "NULLABLE" | "REQUIRED" | "REPEATED";
  description?: string;
  fields?: SchemaField[];  // For STRUCT types
}
```

## Error Codes

| Code | Description | Common Causes |
|------|-------------|---------------|
| `INVALID_SQL` | SQL syntax or semantic error | Typos, invalid references, wrong syntax |
| `AUTHENTICATION_ERROR` | Failed to authenticate with BigQuery | Missing credentials, expired tokens |
| `PERMISSION_DENIED` | Insufficient permissions | Missing IAM roles, dataset access |

## Parameter Types

Due to BigQuery dry-run limitations, all parameters are treated as STRING type. Use explicit casting in your queries:

```sql
-- Correct way to use numeric parameters
SELECT * FROM orders 
WHERE amount > CAST(@min_amount AS FLOAT64)
  AND created_date = CAST(@date AS DATE)
```

## Rate Limits

MCP BigQuery inherits BigQuery's API quotas:

| Quota | Limit | Scope |
|-------|-------|-------|
| API requests | 100/second | Per project |
| Concurrent API requests | 300 | Per project |
| Query complexity | 50 MB uncompressed | Per query |

## Authentication

The server uses Google Cloud Application Default Credentials (ADC). See [Authentication](installation.md#authentication) for setup details.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BQ_PROJECT` | Default GCP project ID | From ADC |
| `BQ_LOCATION` | Default dataset location | None |
| `SAFE_PRICE_PER_TIB` | Default price per TiB | 5.0 |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account key | None |

## Usage Examples

### Basic Validation

```python
# Python example using MCP client
result = client.call_tool(
    "bq_validate_sql",
    {
        "sql": "SELECT * FROM dataset.table"
    }
)

if result["isValid"]:
    print("Query is valid")
else:
    print(f"Error: {result['error']['message']}")
```

### Cost Estimation

```python
result = client.call_tool(
    "bq_dry_run_sql",
    {
        "sql": "SELECT * FROM large_table",
        "pricePerTiB": 6.0  # Custom pricing
    }
)

print(f"Estimated cost: ${result['usdEstimate']:.2f}")
print(f"Bytes to scan: {result['totalBytesProcessed']:,}")
```

### Parameter Validation

```python
result = client.call_tool(
    "bq_validate_sql",
    {
        "sql": "SELECT * FROM users WHERE id = @user_id",
        "params": {"user_id": "12345"}
    }
)
```

## Limitations

1. **Parameters are STRING only** - Cast to appropriate types in SQL
2. **No query execution** - All operations are dry-run only
3. **No data returned** - Only metadata and cost estimates
4. **Cache disabled** - Always returns fresh estimates
5. **No UDF creation** - Can validate UDF usage but not create them

## Next Steps

- See [Usage Guide](usage.md) for detailed examples
- Check [Examples](examples.md) for real-world scenarios
- Read [Development](development.md) for contributing