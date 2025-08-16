# API Reference

## Tools

MCP BigQuery provides two tools for SQL validation and analysis.

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