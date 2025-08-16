# SQL Validation Guide

Learn how to validate BigQuery SQL syntax and catch errors before execution using the `bq_validate_sql` tool. This guide covers validation concepts, practical examples, and troubleshooting techniques.

## Overview

The `bq_validate_sql` tool validates BigQuery SQL syntax without executing queries or consuming slot resources. It uses BigQuery's dry-run capability to check syntax, semantics, and access permissions.

### Key Benefits

- **Fast validation** - No query execution overhead
- **Comprehensive checking** - Syntax, semantics, and permissions
- **Detailed error reporting** - Precise error locations and descriptions
- **Cost-free operation** - No BigQuery charges for validation
- **Early error detection** - Catch issues before production deployment

## Basic Validation

### Simple Query Validation

```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT name, age FROM users WHERE age > 18"
  }
}
```

**Response (Valid SQL):**
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
    "sql": "SELECT name, FROM users WHERE age > 18"
  }
}
```

**Response (Invalid SQL):**
```json
{
  "isValid": false,
  "error": {
    "code": "INVALID_SQL",
    "message": "Syntax error: Unexpected \",\" at [1:13]",
    "location": {
      "line": 1,
      "column": 13
    }
  }
}
```

## Understanding Validation Responses

### Success Response Structure

```json
{
  "isValid": true
}
```

- **`isValid`** - Boolean indicating validation success
- Simple structure for valid queries

### Error Response Structure

```json
{
  "isValid": false,
  "error": {
    "code": "INVALID_SQL",
    "message": "Detailed error description",
    "location": {
      "line": 3,
      "column": 15
    },
    "details": [
      {
        "message": "Additional error context",
        "location": "table.field"
      }
    ]
  }
}
```

- **`isValid`** - Always `false` for errors
- **`error.code`** - Error classification
- **`error.message`** - Human-readable error description
- **`error.location`** - Precise error position (when available)
- **`error.details`** - Additional error context (when available)

## Common Error Types

### Syntax Errors

**Missing Comma:**
```json
{
  "sql": "SELECT name age FROM users"
}
```
```json
{
  "error": {
    "code": "INVALID_SQL",
    "message": "Syntax error: Expected \",\" but got \"age\" at [1:12]",
    "location": {"line": 1, "column": 12}
  }
}
```

**Invalid Function:**
```json
{
  "sql": "SELECT INVALID_FUNCTION(name) FROM users"
}
```
```json
{
  "error": {
    "code": "INVALID_SQL",
    "message": "Function not found: INVALID_FUNCTION",
    "location": {"line": 1, "column": 8}
  }
}
```

### Semantic Errors

**Table Not Found:**
```json
{
  "sql": "SELECT * FROM nonexistent_table"
}
```
```json
{
  "error": {
    "code": "INVALID_SQL",
    "message": "Table 'project.dataset.nonexistent_table' was not found",
    "details": [
      {
        "message": "Table does not exist or access denied",
        "location": "project.dataset.nonexistent_table"
      }
    ]
  }
}
```

**Column Not Found:**
```json
{
  "sql": "SELECT nonexistent_column FROM users"
}
```
```json
{
  "error": {
    "code": "INVALID_SQL",
    "message": "Unrecognized name: nonexistent_column at [1:8]",
    "location": {"line": 1, "column": 8}
  }
}
```

### Permission Errors

**Access Denied:**
```json
{
  "sql": "SELECT * FROM restricted_table"
}
```
```json
{
  "error": {
    "code": "INVALID_SQL",
    "message": "Access Denied: Table project:dataset.restricted_table",
    "details": [
      {
        "message": "User does not have permission to access this table",
        "location": "project:dataset.restricted_table"
      }
    ]
  }
}
```

## Complex SQL Validation

### Multi-Statement Queries

**Separate Validation:**
```json
{
  "sql": "CREATE TEMP TABLE temp_users AS SELECT * FROM users; SELECT COUNT(*) FROM temp_users;"
}
```

Note: BigQuery dry-run validates the entire statement block, but error locations refer to the combined text.

### Subqueries and CTEs

**Common Table Expression:**
```json
{
  "sql": "WITH user_stats AS (SELECT user_id, COUNT(*) as order_count FROM orders GROUP BY user_id) SELECT u.name, s.order_count FROM users u JOIN user_stats s ON u.id = s.user_id"
}
```

**Nested Subqueries:**
```json
{
  "sql": "SELECT name FROM users WHERE id IN (SELECT user_id FROM orders WHERE amount > (SELECT AVG(amount) FROM orders))"
}
```

### Dynamic SQL with Parameters

**Parameterized Validation:**
```json
{
  "sql": "SELECT * FROM users WHERE age > @min_age AND status = @user_status",
  "params": {
    "min_age": "18",
    "user_status": "active"
  }
}
```

## Best Practices

### Development Workflow

1. **Validate Early** - Check syntax before detailed analysis
2. **Iterative Development** - Validate after each modification
3. **Test with Real Schemas** - Use actual table structures
4. **Parameter Testing** - Validate with representative parameter values

### Query Organization

**Use Meaningful Aliases:**
```sql
-- Good
SELECT 
    u.name as user_name,
    p.title as product_title
FROM users u
JOIN products p ON u.id = p.user_id
```

**Structure Complex Queries:**
```sql
-- Good - Clear structure
WITH filtered_users AS (
    SELECT id, name 
    FROM users 
    WHERE active = true
),
user_orders AS (
    SELECT user_id, COUNT(*) as order_count
    FROM orders
    GROUP BY user_id
)
SELECT 
    u.name,
    COALESCE(o.order_count, 0) as total_orders
FROM filtered_users u
LEFT JOIN user_orders o ON u.id = o.user_id
```

### Error Prevention

**Common Mistakes to Avoid:**
- Missing commas in SELECT lists
- Unqualified column names in JOINs
- Incorrect GROUP BY clauses
- Missing table aliases
- Invalid date/time formats

**Prevention Strategies:**
- Use consistent formatting
- Always alias tables in JOINs
- Include all non-aggregate columns in GROUP BY
- Use explicit type casting
- Test with edge cases

## Advanced Validation Techniques

### Schema Dependency Checking

**Cross-Dataset References:**
```json
{
  "sql": "SELECT u.name, o.amount FROM project1.dataset1.users u JOIN project2.dataset2.orders o ON u.id = o.user_id"
}
```

Validation checks:
- Table existence in both projects
- Column availability and types
- JOIN compatibility
- Access permissions for all datasets

### Function and UDF Validation

**Built-in Functions:**
```json
{
  "sql": "SELECT EXTRACT(YEAR FROM created_at), REGEXP_EXTRACT(email, r'@(.+)') as domain FROM users"
}
```

**User-Defined Functions:**
```json
{
  "sql": "SELECT custom_function(data) FROM table WHERE custom_function IS NOT NULL"
}
```

### Data Type Validation

**Type Compatibility:**
```json
{
  "sql": "SELECT CONCAT(name, age) FROM users"
}
```
```json
{
  "error": {
    "code": "INVALID_SQL",
    "message": "No matching signature for function CONCAT for argument types: STRING, INT64",
    "location": {"line": 1, "column": 8}
  }
}
```

**Correct Type Casting:**
```json
{
  "sql": "SELECT CONCAT(name, CAST(age AS STRING)) FROM users"
}
```

## Troubleshooting

### Common Issues and Solutions

#### Authentication Problems

**Issue:** Access denied errors
```json
{
  "error": {
    "code": "UNKNOWN_ERROR",
    "message": "Could not automatically determine credentials"
  }
}
```

**Solution:**
1. Run `gcloud auth application-default login`
2. Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable
3. Verify project permissions

#### Table Reference Issues

**Issue:** Table not found despite existence
```json
{
  "error": {
    "code": "INVALID_SQL",
    "message": "Table 'users' was not found"
  }
}
```

**Solutions:**
1. Use fully qualified names: `project.dataset.table`
2. Check dataset access permissions
3. Verify table name spelling and case
4. Ensure dataset exists in specified project

#### Parameter Problems

**Issue:** Parameter type mismatches
```json
{
  "sql": "SELECT * FROM users WHERE created_at > @date_param",
  "params": {
    "date_param": "invalid-date-format"
  }
}
```

**Solutions:**
1. Use proper date formats: `2023-12-25`
2. All parameters are treated as STRING type
3. Use explicit casting in SQL: `CAST(@param AS DATE)`

### Debugging Strategies

#### Error Location Mapping

When BigQuery reports `[line:column]` positions:
1. Count from the beginning of the SQL string
2. Line numbers start at 1
3. Column numbers start at 1
4. Tabs count as single characters

#### Incremental Validation

For complex queries:
1. Start with simple SELECT
2. Add clauses incrementally
3. Validate after each addition
4. Isolate problematic sections

#### Common SQL Patterns Testing

Test frequently used patterns:
```json
{
  "patterns": [
    "Window functions: ROW_NUMBER() OVER (PARTITION BY ...)",
    "Array operations: UNNEST(array_column)",
    "JSON extraction: JSON_EXTRACT(json_column, '$.field')",
    "Date arithmetic: DATE_ADD(date_column, INTERVAL 1 DAY)"
  ]
}
```

## Integration Examples

### CI/CD Pipeline Validation

**Pre-deployment Check:**
```json
{
  "validation_workflow": [
    {
      "step": "validate_sql",
      "tool": "bq_validate_sql",
      "sql": "{{ query_from_file }}"
    },
    {
      "step": "check_response",
      "condition": "response.isValid === true",
      "on_failure": "abort_deployment"
    }
  ]
}
```

### IDE Integration

**Real-time Validation:**
```json
{
  "editor_integration": {
    "on_save": "validate_sql",
    "on_type": "debounced_validation",
    "error_highlighting": "use_location_data"
  }
}
```

### Batch Validation

**Multiple Query Validation:**
```json
{
  "batch_validation": [
    {"id": "query1", "sql": "SELECT * FROM users"},
    {"id": "query2", "sql": "SELECT * FROM orders"},
    {"id": "query3", "sql": "SELECT * FROM products"}
  ]
}
```

## Performance Considerations

### Validation Speed

- Validation is fast (typically < 1 second)
- No slot consumption or charges
- Network latency is primary factor
- Complex queries may take longer to parse

### Caching Strategies

- Cache validation results for identical queries
- Invalidate cache on schema changes
- Consider parameter variations
- Use query fingerprinting for cache keys

### Rate Limiting

- BigQuery has API rate limits
- Batch validations when possible
- Implement exponential backoff
- Monitor quota usage

## Next Steps

Now that you understand SQL validation, explore:

- **[Dry-Run Analysis Guide](dry-run.md)** - Analyze query performance and costs
- **[Cost Estimation Guide](cost-estimation.md)** - Optimize query costs
- **[Parameters Guide](parameters.md)** - Use dynamic parameterized queries

For more advanced topics, see:
- **[API Reference](../api-reference/)** - Complete tool specifications
- **[Examples](../examples/)** - Additional validation examples
- **[Development Guide](../development/)** - Integration patterns