# Usage Guide

This guide covers how to use MCP BigQuery for SQL validation and dry-run analysis.

## SQL Validation

The `bq_validate_sql` tool validates BigQuery SQL syntax without executing queries.

### Basic Validation

```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT name, age FROM users WHERE age > 18"
  }
}
```

**Valid Response:**
```json
{
  "isValid": true
}
```

**Invalid SQL Example:**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT name, FROM users"  // Extra comma
  }
}
```

**Error Response:**
```json
{
  "isValid": false,
  "error": {
    "code": "INVALID_SQL",
    "message": "Syntax error: Unexpected ',' at [1:12]",
    "location": {
      "line": 1,
      "column": 12
    }
  }
}
```

### Common Syntax Errors

| Error | Example | Fix |
|-------|---------|-----|
| Missing FROM | `SELECT * users` | Add `FROM` keyword |
| Invalid identifier | `SELECT user-name` | Use backticks: `` `user-name` `` |
| Unclosed string | `WHERE name = 'John` | Close the string: `'John'` |
| Reserved keyword | `SELECT select FROM t` | Use backticks: `` `select` `` |

## Dry-Run Analysis

The `bq_dry_run_sql` tool provides cost estimates and metadata without executing queries.

### Cost Estimation

```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT * FROM `bigquery-public-data.samples.shakespeare`",
    "pricePerTiB": 5.0
  }
}
```

**Response:**
```json
{
  "totalBytesProcessed": 2654199,
  "usdEstimate": 0.013,
  "referencedTables": [
    {
      "project": "bigquery-public-data",
      "dataset": "samples",
      "table": "shakespeare"
    }
  ],
  "schemaPreview": [
    {"name": "word", "type": "STRING", "mode": "NULLABLE"},
    {"name": "word_count", "type": "INT64", "mode": "NULLABLE"},
    {"name": "corpus", "type": "STRING", "mode": "NULLABLE"},
    {"name": "corpus_date", "type": "INT64", "mode": "NULLABLE"}
  ]
}
```

### Cost Optimization Tips

1. **Use partitioned tables** - Filter by partition column to reduce scan
   ```sql
   SELECT * FROM events 
   WHERE date = '2024-01-01'  -- Partition column
   ```

2. **Select only needed columns** - Avoid `SELECT *`
   ```sql
   -- Bad: Scans all columns
   SELECT * FROM large_table
   
   -- Good: Scans only 2 columns
   SELECT id, name FROM large_table
   ```

3. **Use clustering** - Filter by clustered columns for efficiency
   ```sql
   SELECT * FROM sales
   WHERE region = 'US'  -- Clustered column
   AND product_id = 123
   ```

## Using Parameters

Both tools support parameterized queries for safe, reusable SQL.

### Basic Parameters

```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT * FROM orders WHERE date = @date AND status = @status",
    "params": {
      "date": "2024-01-01",
      "status": "completed"
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

### Struct Parameters

```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT * FROM users WHERE address.city = @filter.city",
    "params": {
      "filter": {
        "city": "New York",
        "state": "NY"
      }
    }
  }
}
```

**Note:** In dry-run mode, all parameters are treated as STRING type.

## Advanced Queries

### CTEs and Window Functions

```sql
WITH monthly_sales AS (
  SELECT 
    DATE_TRUNC(sale_date, MONTH) as month,
    SUM(amount) as total_sales
  FROM sales
  GROUP BY month
)
SELECT 
  month,
  total_sales,
  LAG(total_sales) OVER (ORDER BY month) as previous_month,
  total_sales - LAG(total_sales) OVER (ORDER BY month) as growth
FROM monthly_sales
ORDER BY month DESC
```

### MERGE Statements

```sql
MERGE target_table T
USING source_table S
ON T.id = S.id
WHEN MATCHED THEN
  UPDATE SET T.value = S.value, T.updated_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN
  INSERT (id, value, created_at)
  VALUES (S.id, S.value, CURRENT_TIMESTAMP())
```

### DDL Validation

```sql
CREATE OR REPLACE TABLE dataset.new_table
PARTITION BY DATE(created_at)
CLUSTER BY user_id, region
AS
SELECT * FROM dataset.source_table
WHERE created_at >= '2024-01-01'
```

## Working with Different SQL Types

### Standard SQL (Default)

```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT * FROM `project.dataset.table` WHERE date > '2024-01-01'"
  }
}
```

### DML Operations

```sql
-- INSERT
INSERT INTO table_name (col1, col2)
VALUES ('value1', 'value2')

-- UPDATE
UPDATE table_name
SET column1 = 'new_value'
WHERE condition

-- DELETE
DELETE FROM table_name
WHERE date < '2024-01-01'
```

### Scripting

```sql
DECLARE x INT64 DEFAULT 0;
DECLARE y STRING;

SET x = 5;
SET y = 'Hello';

IF x > 0 THEN
  SELECT CONCAT(y, ' World') as greeting;
END IF;
```

## Error Handling

### Understanding Error Responses

All errors follow this structure:

```json
{
  "error": {
    "code": "INVALID_SQL",
    "message": "Detailed error message",
    "location": {
      "line": 1,
      "column": 15
    },
    "details": []  // Optional additional context
  }
}
```

### Common Error Patterns

1. **Table not found**
   - Check project.dataset.table format
   - Verify permissions
   - Ensure table exists

2. **Column not found**
   - Check column name spelling
   - Verify table schema
   - Use INFORMATION_SCHEMA to list columns

3. **Type mismatch**
   - Check data types in comparisons
   - Use CAST() for type conversion
   - Verify function parameter types

## Best Practices

### 1. Validate Before Execution

Always validate queries before running them:

```python
# Pseudo-code workflow
validation = bq_validate_sql(sql)
if validation.isValid:
    dry_run = bq_dry_run_sql(sql)
    if dry_run.usdEstimate < threshold:
        # Safe to execute
        execute_query(sql)
```

### 2. Monitor Query Costs

Set cost thresholds and alerts:

```python
MAX_QUERY_COST = 10.0  # $10 USD

result = bq_dry_run_sql(sql)
if result.usdEstimate > MAX_QUERY_COST:
    raise Exception(f"Query too expensive: ${result.usdEstimate}")
```

### 3. Use Query Templates

Create reusable, parameterized queries:

```sql
-- query_template.sql
SELECT 
  user_id,
  COUNT(*) as event_count
FROM events
WHERE 
  event_type = @event_type
  AND date BETWEEN @start_date AND @end_date
GROUP BY user_id
```

### 4. Implement CI/CD Validation

Add SQL validation to your pipeline:

```yaml
# .github/workflows/validate-sql.yml
- name: Validate SQL
  run: |
    for file in queries/*.sql; do
      mcp-bigquery validate "$file"
    done
```

## Performance Tips

1. **Partition Pruning** - Always filter by partition column
2. **Clustering Benefits** - Order WHERE clauses by cluster columns
3. **Avoid SELECT *** - Specify only needed columns
4. **Use APPROX functions** - For large aggregations when exact values aren't required
5. **Materialized Views** - Pre-compute expensive aggregations
6. **Query Cache** - Note: Disabled in dry-run for accurate estimates

## Next Steps

- See [API Reference](api-reference.md) for complete tool documentation
- Check [Examples](examples.md) for real-world use cases
- Read [Development Guide](development.md) for contributing