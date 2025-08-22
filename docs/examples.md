# Examples

Practical examples using MCP BigQuery with real queries and public datasets.

## Basic Examples

### Simple Validation

**Valid Query:**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT 'Hello BigQuery' as greeting"
  }
}
```

**Invalid Query (syntax error):**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT * FORM users"  // FORM instead of FROM
  }
}
```

Response shows exact error location:
```json
{
  "isValid": false,
  "error": {
    "code": "INVALID_SQL",
    "message": "Expected FROM but got FORM at [1:10]",
    "location": {"line": 1, "column": 10}
  }
}
```

### Cost Estimation

Using public Shakespeare dataset:

```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT * FROM `bigquery-public-data.samples.shakespeare`"
  }
}
```

Response:
```json
{
  "totalBytesProcessed": 2654199,
  "usdEstimate": 0.000013,
  "referencedTables": [{
    "project": "bigquery-public-data",
    "dataset": "samples",
    "table": "shakespeare"
  }]
}
```

## Working with Parameters

### Basic Parameters

```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT * FROM orders WHERE date = @order_date AND status = @status",
    "params": {
      "order_date": "2024-01-01",
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

## Real-World Scenarios

### 1. Daily Sales Report

```sql
WITH daily_sales AS (
  SELECT 
    DATE(sale_timestamp) as sale_date,
    COUNT(*) as transaction_count,
    SUM(amount) as total_sales,
    AVG(amount) as avg_sale
  FROM `project.sales.transactions`
  WHERE sale_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  GROUP BY sale_date
)
SELECT 
  sale_date,
  transaction_count,
  ROUND(total_sales, 2) as total_sales,
  ROUND(avg_sale, 2) as avg_sale,
  ROUND(AVG(total_sales) OVER (
    ORDER BY sale_date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ), 2) as moving_avg_7d
FROM daily_sales
ORDER BY sale_date DESC
```

### 2. User Activity Analysis

```sql
SELECT 
  user_id,
  COUNT(DISTINCT session_id) as sessions,
  COUNT(*) as total_events,
  ARRAY_AGG(DISTINCT event_type IGNORE NULLS) as event_types,
  MAX(event_timestamp) as last_active,
  DATE_DIFF(CURRENT_DATE(), DATE(MAX(event_timestamp)), DAY) as days_inactive
FROM `project.analytics.events`
WHERE event_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
GROUP BY user_id
HAVING sessions > 5
ORDER BY total_events DESC
LIMIT 1000
```

### 3. Cost Optimization Comparison

**Before optimization (full scan):**
```sql
SELECT * FROM `project.logs.events`
WHERE DATE(timestamp) = '2024-01-01'
```

**After optimization (partition filter):**
```sql
SELECT * FROM `project.logs.events`
WHERE timestamp >= '2024-01-01'
  AND timestamp < '2024-01-02'
```

Check cost difference:
```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT * FROM `project.logs.events` WHERE timestamp >= '2024-01-01' AND timestamp < '2024-01-02'"
  }
}
```

### 4. Data Quality Validation

```sql
WITH validation_checks AS (
  SELECT 
    'null_check' as check_type,
    COUNT(*) as failed_records
  FROM `project.dataset.table`
  WHERE required_field IS NULL
  
  UNION ALL
  
  SELECT 
    'duplicate_check' as check_type,
    COUNT(*) - COUNT(DISTINCT id) as failed_records
  FROM `project.dataset.table`
  
  UNION ALL
  
  SELECT 
    'range_check' as check_type,
    COUNT(*) as failed_records
  FROM `project.dataset.table`
  WHERE amount < 0 OR amount > 1000000
)
SELECT * FROM validation_checks
WHERE failed_records > 0
```

## Advanced Patterns

### MERGE Statement

```sql
MERGE `project.dataset.target_table` T
USING `project.dataset.source_table` S
ON T.id = S.id
WHEN MATCHED AND S.updated_at > T.updated_at THEN
  UPDATE SET 
    T.name = S.name,
    T.value = S.value,
    T.updated_at = S.updated_at
WHEN NOT MATCHED THEN
  INSERT (id, name, value, created_at, updated_at)
  VALUES (S.id, S.name, S.value, CURRENT_TIMESTAMP(), S.updated_at)
```

### Dynamic SQL with Scripting

```sql
DECLARE table_suffix STRING DEFAULT FORMAT_DATE('%Y%m%d', CURRENT_DATE());
DECLARE query STRING;

SET query = CONCAT(
  'SELECT COUNT(*) as record_count FROM `project.dataset.events_',
  table_suffix,
  '` WHERE event_type = "purchase"'
);

EXECUTE IMMEDIATE query;
```

### Window Functions for Analytics

```sql
WITH user_sessions AS (
  SELECT 
    user_id,
    session_id,
    MIN(event_timestamp) as session_start,
    MAX(event_timestamp) as session_end,
    COUNT(*) as event_count
  FROM `project.analytics.events`
  GROUP BY user_id, session_id
)
SELECT 
  user_id,
  session_id,
  session_start,
  TIMESTAMP_DIFF(session_end, session_start, SECOND) as session_duration_seconds,
  event_count,
  LAG(session_end) OVER (PARTITION BY user_id ORDER BY session_start) as previous_session_end,
  TIMESTAMP_DIFF(
    session_start,
    LAG(session_end) OVER (PARTITION BY user_id ORDER BY session_start),
    MINUTE
  ) as minutes_since_last_session
FROM user_sessions
WHERE DATE(session_start) = CURRENT_DATE()
ORDER BY user_id, session_start
```

## Testing Patterns

### 1. Pre-deployment Validation

```python
# Validate all SQL files before deployment
import json
import glob

sql_files = glob.glob("queries/*.sql")
for file in sql_files:
    with open(file, 'r') as f:
        sql = f.read()
    
    result = mcp_client.call_tool(
        "bq_validate_sql",
        {"sql": sql}
    )
    
    if not result["isValid"]:
        print(f"❌ {file}: {result['error']['message']}")
    else:
        print(f"✅ {file}: Valid")
```

### 2. Cost Threshold Check

```python
MAX_COST = 10.0  # $10 USD limit

result = mcp_client.call_tool(
    "bq_dry_run_sql",
    {"sql": production_query}
)

if result["usdEstimate"] > MAX_COST:
    raise Exception(f"Query too expensive: ${result['usdEstimate']:.2f}")
```

### 3. Schema Compatibility Check

```python
# Ensure query returns expected columns
expected_schema = [
    {"name": "user_id", "type": "STRING"},
    {"name": "total", "type": "FLOAT64"},
    {"name": "created_at", "type": "TIMESTAMP"}
]

result = mcp_client.call_tool(
    "bq_dry_run_sql",
    {"sql": query}
)

actual_fields = {f["name"]: f["type"] for f in result["schemaPreview"]}
for expected in expected_schema:
    if expected["name"] not in actual_fields:
        raise Exception(f"Missing field: {expected['name']}")
    if actual_fields[expected["name"]] != expected["type"]:
        raise Exception(f"Type mismatch for {expected['name']}")
```

## Schema Discovery Examples

### 1. Explore Available Datasets

```json
{
  "tool": "bq_list_datasets",
  "arguments": {
    "project_id": "bigquery-public-data",
    "max_results": 5
  }
}
```

Response shows available datasets:
```json
{
  "project": "bigquery-public-data",
  "dataset_count": 5,
  "datasets": [
    {
      "dataset_id": "samples",
      "location": "US",
      "description": "Sample datasets for BigQuery"
    }
  ]
}
```

### 2. Browse Tables in Dataset

```json
{
  "tool": "bq_list_tables",
  "arguments": {
    "dataset_id": "samples",
    "project_id": "bigquery-public-data",
    "table_type_filter": ["TABLE"]
  }
}
```

### 3. Get Table Schema Details

```json
{
  "tool": "bq_describe_table",
  "arguments": {
    "table_id": "shakespeare",
    "dataset_id": "samples",
    "project_id": "bigquery-public-data",
    "format_output": true
  }
}
```

### 4. Query INFORMATION_SCHEMA

Get column metadata:
```json
{
  "tool": "bq_query_info_schema",
  "arguments": {
    "query_type": "columns",
    "dataset_id": "samples",
    "project_id": "bigquery-public-data",
    "table_filter": "shakespeare"
  }
}
```

## Performance Analysis Examples

### 1. Analyze Query Performance

```json
{
  "tool": "bq_analyze_query_performance",
  "arguments": {
    "sql": "SELECT * FROM `bigquery-public-data.samples.shakespeare` WHERE word_count > 100"
  }
}
```

Response with optimization suggestions:
```json
{
  "performance_score": 75,
  "performance_rating": "GOOD",
  "optimization_suggestions": [
    {
      "type": "SELECT_STAR",
      "severity": "MEDIUM",
      "recommendation": "Select only needed columns instead of *"
    }
  ],
  "query_analysis": {
    "bytes_processed": 2654199,
    "estimated_cost_usd": 0.000013
  }
}
```

### 2. Compare Query Variations

Original query:
```json
{
  "tool": "bq_analyze_query_performance",
  "arguments": {
    "sql": "SELECT * FROM large_table"
  }
}
```

Optimized query:
```json
{
  "tool": "bq_analyze_query_performance",
  "arguments": {
    "sql": "SELECT id, name, total FROM large_table WHERE date >= '2024-01-01'"
  }
}
```

### 3. Analyze Complex Queries

```json
{
  "tool": "bq_analyze_query_structure",
  "arguments": {
    "sql": "WITH daily_stats AS (SELECT DATE(timestamp) as day, COUNT(*) as cnt FROM events GROUP BY day) SELECT * FROM daily_stats WHERE cnt > 1000"
  }
}
```

Response:
```json
{
  "query_type": "SELECT",
  "has_cte": true,
  "has_aggregations": true,
  "complexity_score": 20,
  "functions_used": ["DATE", "COUNT"]
}
```

## Common Pitfalls & Solutions

### 1. Parameter Type Issues

**Problem:** Parameters are always STRING in dry-run mode

**Solution:** Use explicit casting
```sql
-- Wrong
WHERE amount > @threshold

-- Correct
WHERE amount > CAST(@threshold AS FLOAT64)
```

### 2. Table Reference Format

**Problem:** Incorrect table reference format

**Solution:** Use fully qualified names
```sql
-- Wrong
SELECT * FROM table_name

-- Correct
SELECT * FROM `project.dataset.table_name`
```

### 3. Cost Estimation Accuracy

**Problem:** LIMIT doesn't reduce scan cost

**Solution:** Use partitioning and clustering
```sql
-- Still scans entire table
SELECT * FROM large_table LIMIT 10

-- Only scans specific partition
SELECT * FROM large_table
WHERE partition_date = '2024-01-01'
LIMIT 10
```

## Next Steps

- Review [API Reference](api-reference.md) for complete tool documentation
- See [Usage Guide](usage.md) for detailed patterns
- Check [Development](development.md) for contributing