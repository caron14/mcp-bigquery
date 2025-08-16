# Quick Start

Get started with MCP BigQuery in 5 minutes. This tutorial will walk you through your first SQL validation and cost estimation.

## Prerequisites

!!! info "Before you begin"
    Make sure you've completed the [Installation](installation.md) and [Authentication](authentication.md) setup.

## Step 1: Configure Your MCP Client

### For Claude Code

Add to your Claude Code configuration file:

```json
{
  "mcpServers": {
    "mcp-bigquery": {
      "command": "mcp-bigquery",
      "env": {
        "BQ_PROJECT": "your-project-id",
        "BQ_LOCATION": "US"
      }
    }
  }
}
```

### For Other MCP Clients

Refer to your MCP client's documentation. The key configuration:

- **Command**: `mcp-bigquery` or `python -m mcp_bigquery`
- **Protocol**: Standard MCP over stdio
- **Tools**: `bq_validate_sql` and `bq_dry_run_sql`

## Step 2: Your First SQL Validation

Let's validate a simple SQL query:

### Basic Query Validation

```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT 1 as test_column"
  }
}
```

**Expected Response:**
```json
{
  "isValid": true
}
```

### Invalid Query Example

```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT * FORM users"  // Note: FORM instead of FROM
  }
}
```

**Expected Response:**
```json
{
  "isValid": false,
  "error": {
    "code": "INVALID_SQL",
    "message": "Syntax error: Expected FROM but got FORM at [1:10]",
    "location": {
      "line": 1,
      "column": 10
    }
  }
}
```

## Step 3: Analyze Query Costs

Now let's estimate the cost of a query against a public dataset:

### Public Dataset Query

```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT word, word_count FROM `bigquery-public-data.samples.shakespeare` WHERE word_count > 100"
  }
}
```

**Expected Response:**
```json
{
  "totalBytesProcessed": 65536,
  "usdEstimate": 0.00032,
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
      "type": "INT64",
      "mode": "NULLABLE"
    }
  ]
}
```

## Step 4: Work with Parameters

MCP BigQuery supports parameterized queries:

### Parameterized Query

```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT * FROM users WHERE created_date = @date AND status = @status",
    "params": {
      "date": "2024-01-01",
      "status": "active"
    }
  }
}
```

### Array Parameters

```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT * FROM products WHERE category IN UNNEST(@categories)",
    "params": {
      "categories": ["electronics", "books", "clothing"]
    }
  }
}
```

## Step 5: Complex Query Analysis

Let's analyze a more complex query with joins and aggregations:

```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "
      WITH daily_stats AS (
        SELECT 
          DATE(created_time) as date,
          COUNT(*) as order_count,
          SUM(total_amount) as daily_revenue
        FROM `your-project.sales.orders`
        WHERE created_time >= '2024-01-01'
        GROUP BY date
      )
      SELECT 
        date,
        order_count,
        daily_revenue,
        AVG(daily_revenue) OVER (
          ORDER BY date 
          ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) as moving_avg_7d
      FROM daily_stats
      ORDER BY date DESC
    ",
    "pricePerTiB": 5.0
  }
}
```

This will return:
- Total bytes that would be scanned
- Estimated cost in USD
- List of all referenced tables
- Preview of the result schema

## Common Patterns

### 1. Validate Before Execution

```python
# Always validate before running expensive queries
validation = bq_validate_sql({"sql": complex_query})
if validation["isValid"]:
    dry_run = bq_dry_run_sql({"sql": complex_query})
    if dry_run["usdEstimate"] < 10.0:  # $10 threshold
        # Safe to execute
        pass
```

### 2. Cost Comparison

```python
# Compare different query approaches
query1_cost = bq_dry_run_sql({"sql": query_with_full_scan})
query2_cost = bq_dry_run_sql({"sql": query_with_partition})

print(f"Full scan: ${query1_cost['usdEstimate']:.2f}")
print(f"Partitioned: ${query2_cost['usdEstimate']:.2f}")
```

### 3. Schema Validation

```python
# Check if query returns expected columns
result = bq_dry_run_sql({"sql": query})
expected_columns = ["user_id", "total_amount", "order_date"]

actual_columns = [field["name"] for field in result["schemaPreview"]]
assert all(col in actual_columns for col in expected_columns)
```

## Tips and Best Practices

!!! tip "Performance Tips"
    - Use table partitioning to reduce bytes scanned
    - Filter early in your WHERE clauses
    - Use LIMIT for testing, but remember it doesn't reduce scan cost
    - Leverage clustering for frequently filtered columns

!!! warning "Cost Considerations"
    - BigQuery charges are based on bytes scanned, not returned
    - Using SELECT * scans all columns even if you don't use them
    - JOINs can multiply the bytes scanned
    - Preview costs before running on large datasets

!!! info "Parameter Limitations"
    - In dry-run mode, all parameters are treated as STRING type
    - Array parameters are supported
    - Struct parameters require special handling

## Troubleshooting

### "Project not found" Error

**Solution**: Set the `BQ_PROJECT` environment variable:
```bash
export BQ_PROJECT="your-project-id"
```

### "Permission denied" Error

**Solution**: Ensure your account has BigQuery Job User role:
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT \
  --member="user:your-email@example.com" \
  --role="roles/bigquery.jobUser"
```

### "Table not found" Error

**Solution**: Check the fully qualified table name:
```sql
-- Correct format
`project-id.dataset_name.table_name`

-- For public datasets
`bigquery-public-data.dataset.table`
```

## What's Next?

- 📘 Deep dive into [SQL Validation](../guides/validation.md)
- 💰 Master [Cost Estimation](../guides/cost-estimation.md)
- 🔧 Learn about [Parameters](../guides/parameters.md)
- 🚀 Explore [Advanced Examples](../examples/advanced.md)