# Tools Reference

This document provides detailed specifications for all tools available in the MCP BigQuery server.

## bq_validate_sql

Validates BigQuery SQL syntax without executing the query. Performs a dry-run to check for syntax errors, invalid references, and parameter issues.

### Input Schema

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
      "description": "Optional query parameters (key-value pairs)",
      "additionalProperties": true
    }
  },
  "required": ["sql"]
}
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sql` | string | Yes | The SQL query to validate |
| `params` | object | No | Query parameters as key-value pairs |

#### Parameter Details

- **sql**: Any valid BigQuery SQL query. The query will not be executed, only validated.
- **params**: Named parameters for the query. All parameters are treated as STRING type due to BigQuery dry-run limitations. Use explicit casting in your SQL for other types.

### Response Schema

#### Success Response
```json
{
  "isValid": true
}
```

#### Error Response
```json
{
  "isValid": false,
  "error": {
    "code": "INVALID_SQL",
    "message": "Syntax error: Expected keyword FROM but got keyword WHERE at [3:15]",
    "location": {
      "line": 3,
      "column": 15
    },
    "details": [
      {
        "reason": "invalidQuery",
        "location": "query",
        "message": "Syntax error details from BigQuery"
      }
    ]
  }
}
```

### Examples

#### Basic Validation
```json
{
  "sql": "SELECT name, age FROM users WHERE age > 18"
}
```

Response:
```json
{
  "isValid": true
}
```

#### Parameterized Query Validation
```json
{
  "sql": "SELECT * FROM users WHERE name = @user_name AND age > CAST(@min_age AS INT64)",
  "params": {
    "user_name": "John",
    "min_age": "21"
  }
}
```

Response:
```json
{
  "isValid": true
}
```

#### Syntax Error Example
```json
{
  "sql": "SELECT FROM users"
}
```

Response:
```json
{
  "isValid": false,
  "error": {
    "code": "INVALID_SQL",
    "message": "Syntax error: Expected expression but got keyword FROM at [1:8]",
    "location": {
      "line": 1,
      "column": 8
    }
  }
}
```

---

## bq_dry_run_sql

Performs a comprehensive dry-run analysis of a BigQuery SQL query, providing cost estimates, schema information, and referenced tables without executing the query.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "sql": {
      "type": "string",
      "description": "The SQL query to dry-run"
    },
    "params": {
      "type": "object",
      "description": "Optional query parameters (key-value pairs)",
      "additionalProperties": true
    },
    "pricePerTiB": {
      "type": "number",
      "description": "Price per TiB for cost estimation (defaults to env var or 5.0)"
    }
  },
  "required": ["sql"]
}
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sql` | string | Yes | The SQL query to analyze |
| `params` | object | No | Query parameters as key-value pairs |
| `pricePerTiB` | number | No | Price per TiB for cost calculation |

#### Parameter Details

- **sql**: Any valid BigQuery SQL query for analysis
- **params**: Named parameters for the query (all treated as STRING type)
- **pricePerTiB**: Cost per TiB in USD. Takes precedence over `SAFE_PRICE_PER_TIB` environment variable. Defaults to 5.0 if not specified.

### Response Schema

#### Success Response
```json
{
  "totalBytesProcessed": 1048576,
  "usdEstimate": 0.000005,
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
      "type": "INTEGER",
      "mode": "REQUIRED"
    },
    {
      "name": "name",
      "type": "STRING", 
      "mode": "NULLABLE"
    }
  ]
}
```

#### Error Response
```json
{
  "error": {
    "code": "INVALID_SQL",
    "message": "Table 'project.dataset.nonexistent_table' was not found",
    "details": [
      {
        "reason": "notFound",
        "message": "Table not found details"
      }
    ]
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `totalBytesProcessed` | integer | Number of bytes the query would process |
| `usdEstimate` | number | Estimated cost in USD (rounded to 6 decimal places) |
| `referencedTables` | array | List of tables referenced by the query |
| `schemaPreview` | array | Output schema of the query result |

#### Referenced Tables Format
Each table reference contains:
- `project`: Google Cloud project ID
- `dataset`: BigQuery dataset name  
- `table`: Table name

#### Schema Preview Format
Each field contains:
- `name`: Column name
- `type`: BigQuery data type (STRING, INTEGER, FLOAT, etc.)
- `mode`: Field mode (REQUIRED, NULLABLE, REPEATED)

### Examples

#### Basic Dry-Run
```json
{
  "sql": "SELECT * FROM `bigquery-public-data.samples.shakespeare` LIMIT 10"
}
```

Response:
```json
{
  "totalBytesProcessed": 6432735,
  "usdEstimate": 0.000030,
  "referencedTables": [
    {
      "project": "bigquery-public-data",
      "dataset": "samples",
      "table": "shakespeare"
    }
  ],
  "schemaPreview": [
    {
      "name": "word",
      "type": "STRING",
      "mode": "NULLABLE"
    },
    {
      "name": "word_count", 
      "type": "INTEGER",
      "mode": "NULLABLE"
    },
    {
      "name": "corpus",
      "type": "STRING", 
      "mode": "NULLABLE"
    },
    {
      "name": "corpus_date",
      "type": "INTEGER",
      "mode": "NULLABLE"
    }
  ]
}
```

#### Aggregation Query with Custom Pricing
```json
{
  "sql": "SELECT corpus, COUNT(*) as word_count FROM `bigquery-public-data.samples.shakespeare` GROUP BY corpus",
  "pricePerTiB": 10.0
}
```

Response:
```json
{
  "totalBytesProcessed": 6432735,
  "usdEstimate": 0.000060,
  "referencedTables": [
    {
      "project": "bigquery-public-data",
      "dataset": "samples", 
      "table": "shakespeare"
    }
  ],
  "schemaPreview": [
    {
      "name": "corpus",
      "type": "STRING",
      "mode": "NULLABLE"
    },
    {
      "name": "word_count",
      "type": "INTEGER", 
      "mode": "NULLABLE"
    }
  ]
}
```

#### Parameterized Query Dry-Run
```json
{
  "sql": "SELECT word, word_count FROM `bigquery-public-data.samples.shakespeare` WHERE corpus = @corpus_name AND word_count > CAST(@min_count AS INT64)",
  "params": {
    "corpus_name": "hamlet",
    "min_count": "10"
  }
}
```

Response:
```json
{
  "totalBytesProcessed": 6432735,
  "usdEstimate": 0.000030,
  "referencedTables": [
    {
      "project": "bigquery-public-data", 
      "dataset": "samples",
      "table": "shakespeare"
    }
  ],
  "schemaPreview": [
    {
      "name": "word",
      "type": "STRING",
      "mode": "NULLABLE"
    },
    {
      "name": "word_count",
      "type": "INTEGER",
      "mode": "NULLABLE"
    }
  ]
}
```

#### Invalid Table Reference
```json
{
  "sql": "SELECT * FROM `nonexistent-project.nonexistent-dataset.nonexistent-table`"
}
```

Response:
```json
{
  "error": {
    "code": "INVALID_SQL",
    "message": "Not found: Table nonexistent-project:nonexistent-dataset.nonexistent-table was not found in location US"
  }
}
```

## Cost Calculation

Cost estimates are calculated using the formula:

```
Cost (USD) = (Total Bytes Processed / 2^40) × Price Per TiB
```

Where:
- Total Bytes Processed: Returned by BigQuery dry-run API
- 2^40: Number of bytes in a TiB (1,099,511,627,776)
- Price Per TiB: Configurable price (default: $5.00 USD)

## Parameter Handling

Due to BigQuery dry-run API limitations, all query parameters are treated as STRING type. To use other data types in your queries:

```sql
-- For integers
WHERE age > CAST(@age_param AS INT64)

-- For floats  
WHERE price < CAST(@price_param AS FLOAT64)

-- For dates
WHERE created_date = PARSE_DATE('%Y-%m-%d', @date_param)

-- For timestamps
WHERE created_at > PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', @timestamp_param)
```

## Query Limitations

- **Dry-run only**: Queries are never executed
- **No query cache**: Cache is disabled for consistent results
- **Parameter types**: All parameters treated as STRING
- **BigQuery syntax**: Must use valid BigQuery SQL syntax
- **Permissions**: Requires read access to referenced tables/datasets