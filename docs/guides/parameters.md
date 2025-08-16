# Parameterized Queries Guide

Master parameterized queries with MCP BigQuery to create dynamic, secure, and reusable SQL queries. Learn parameter handling, best practices, and advanced patterns.

## Overview

Parameterized queries allow you to create dynamic SQL with placeholder values that are safely substituted at runtime. The MCP BigQuery server supports parameterized queries for both validation and dry-run analysis.

### Key Benefits

- **Security** - Prevents SQL injection attacks
- **Reusability** - Single query template for multiple scenarios
- **Performance** - Query plan caching with different parameter values
- **Maintainability** - Centralized query logic with dynamic data
- **Type Safety** - Parameter validation and type checking

### Parameter Syntax

BigQuery uses named parameters with the `@parameter_name` syntax:

```sql
SELECT * FROM users WHERE age > @min_age AND status = @user_status
```

## Basic Parameter Usage

### Simple Parameter Example

```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT name, email FROM users WHERE age > @min_age",
    "params": {
      "min_age": "25"
    }
  }
}
```

**Response:**
```json
{
  "isValid": true
}
```

### Multiple Parameters

```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT * FROM orders WHERE created_at BETWEEN @start_date AND @end_date AND status = @order_status",
    "params": {
      "start_date": "2023-01-01",
      "end_date": "2023-12-31",
      "order_status": "completed"
    }
  }
}
```

**Response:**
```json
{
  "totalBytesProcessed": 5242880,
  "usdEstimate": 0.000025,
  "referencedTables": [
    {
      "project": "my-project",
      "dataset": "ecommerce",
      "table": "orders"
    }
  ],
  "schemaPreview": [
    {
      "name": "id",
      "type": "INT64",
      "mode": "NULLABLE"
    },
    {
      "name": "created_at", 
      "type": "TIMESTAMP",
      "mode": "NULLABLE"
    },
    {
      "name": "status",
      "type": "STRING",
      "mode": "NULLABLE"
    }
  ]
}
```

## Parameter Types and Handling

### MCP BigQuery Parameter Limitations

**Important:** MCP BigQuery treats all parameters as STRING type during dry-run analysis. This is a BigQuery limitation for dry-run operations.

```json
{
  "parameter_handling": {
    "input_type": "any JSON value",
    "processing_type": "STRING",
    "bigquery_conversion": "automatic type casting",
    "recommendation": "use explicit CAST() in SQL for type safety"
  }
}
```

### Type Casting in SQL

**Recommended Pattern:**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT * FROM events WHERE event_date >= CAST(@start_date AS DATE) AND user_id = CAST(@user_id AS INT64)",
    "params": {
      "start_date": "2023-01-01",
      "user_id": "12345"
    }
  }
}
```

### Common Data Type Patterns

#### Date and Time Parameters

```json
{
  "date_time_patterns": [
    {
      "type": "DATE",
      "sql": "WHERE created_date >= CAST(@start_date AS DATE)",
      "params": {"start_date": "2023-01-01"}
    },
    {
      "type": "TIMESTAMP",
      "sql": "WHERE created_at >= CAST(@start_timestamp AS TIMESTAMP)",
      "params": {"start_timestamp": "2023-01-01 12:00:00"}
    },
    {
      "type": "DATETIME",
      "sql": "WHERE event_time >= CAST(@start_datetime AS DATETIME)",
      "params": {"start_datetime": "2023-01-01 12:00:00"}
    }
  ]
}
```

#### Numeric Parameters

```json
{
  "numeric_patterns": [
    {
      "type": "INT64",
      "sql": "WHERE user_id = CAST(@user_id AS INT64)",
      "params": {"user_id": "12345"}
    },
    {
      "type": "FLOAT64",
      "sql": "WHERE price >= CAST(@min_price AS FLOAT64)",
      "params": {"min_price": "99.99"}
    },
    {
      "type": "NUMERIC",
      "sql": "WHERE amount = CAST(@amount AS NUMERIC)",
      "params": {"amount": "1234.56"}
    }
  ]
}
```

#### Boolean Parameters

```json
{
  "boolean_patterns": [
    {
      "sql": "WHERE is_active = CAST(@is_active AS BOOL)",
      "params": {"is_active": "true"}
    },
    {
      "sql": "WHERE deleted = CAST(@deleted AS BOOL)",
      "params": {"deleted": "false"}
    }
  ]
}
```

## Advanced Parameter Patterns

### Array Parameters

**Array Membership Testing:**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT * FROM products WHERE category IN UNNEST(SPLIT(@categories, ','))",
    "params": {
      "categories": "electronics,books,clothing"
    }
  }
}
```

**Advanced Array Handling:**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT * FROM orders WHERE user_id IN UNNEST(CAST(SPLIT(@user_ids, ',') AS ARRAY<INT64>))",
    "params": {
      "user_ids": "123,456,789"
    }
  }
}
```

### Dynamic Date Ranges

**Relative Date Parameters:**
```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT * FROM events WHERE event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL CAST(@days_back AS INT64) DAY)",
    "params": {
      "days_back": "30"
    }
  }
}
```

**Flexible Date Range Queries:**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT * FROM sales WHERE sale_date BETWEEN COALESCE(CAST(@start_date AS DATE), DATE('1900-01-01')) AND COALESCE(CAST(@end_date AS DATE), CURRENT_DATE())",
    "params": {
      "start_date": "2023-01-01",
      "end_date": null
    }
  }
}
```

### Conditional Parameters

**Optional Filtering:**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT * FROM users WHERE (@status IS NULL OR status = @status) AND (@min_age IS NULL OR age >= CAST(@min_age AS INT64))",
    "params": {
      "status": "active",
      "min_age": null
    }
  }
}
```

**Dynamic WHERE Clauses:**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT * FROM products WHERE CASE WHEN @category != 'all' THEN category = @category ELSE TRUE END",
    "params": {
      "category": "electronics"
    }
  }
}
```

## Query Template Patterns

### Reusable Query Templates

#### User Analytics Template

```json
{
  "template_name": "user_analytics",
  "sql": "SELECT user_id, COUNT(*) as action_count, MAX(created_at) as last_action FROM user_events WHERE created_at BETWEEN CAST(@start_date AS DATE) AND CAST(@end_date AS DATE) AND (@event_type IS NULL OR event_type = @event_type) GROUP BY user_id HAVING COUNT(*) >= CAST(@min_actions AS INT64) ORDER BY action_count DESC LIMIT CAST(@limit AS INT64)",
  "parameter_definitions": {
    "start_date": {"type": "DATE", "required": true, "description": "Analysis start date"},
    "end_date": {"type": "DATE", "required": true, "description": "Analysis end date"},
    "event_type": {"type": "STRING", "required": false, "description": "Filter by event type or NULL for all"},
    "min_actions": {"type": "INT64", "required": false, "default": "1", "description": "Minimum action count"},
    "limit": {"type": "INT64", "required": false, "default": "100", "description": "Result limit"}
  }
}
```

**Usage Examples:**
```json
{
  "examples": [
    {
      "name": "all_user_activity",
      "params": {
        "start_date": "2023-01-01",
        "end_date": "2023-01-31",
        "event_type": null,
        "min_actions": "1",
        "limit": "1000"
      }
    },
    {
      "name": "high_engagement_users",
      "params": {
        "start_date": "2023-01-01",
        "end_date": "2023-01-31",
        "event_type": "purchase",
        "min_actions": "5",
        "limit": "50"
      }
    }
  ]
}
```

#### Sales Report Template

```json
{
  "template_name": "sales_report",
  "sql": "WITH filtered_sales AS (SELECT * FROM sales WHERE sale_date BETWEEN CAST(@start_date AS DATE) AND CAST(@end_date AS DATE) AND (@region IS NULL OR region = @region) AND (@product_category IS NULL OR product_category = @product_category)) SELECT DATE_TRUNC(sale_date, @date_granularity) as period, SUM(amount) as total_sales, COUNT(*) as transaction_count, AVG(amount) as avg_sale_amount FROM filtered_sales GROUP BY period ORDER BY period",
  "parameter_definitions": {
    "start_date": {"type": "DATE", "required": true},
    "end_date": {"type": "DATE", "required": true},
    "region": {"type": "STRING", "required": false},
    "product_category": {"type": "STRING", "required": false},
    "date_granularity": {"type": "STRING", "required": true, "valid_values": ["DAY", "WEEK", "MONTH", "QUARTER", "YEAR"]}
  }
}
```

### Dynamic Aggregation Patterns

**Flexible Grouping:**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT CASE @group_by WHEN 'day' THEN CAST(DATE(created_at) AS STRING) WHEN 'week' THEN CAST(DATE_TRUNC(DATE(created_at), WEEK) AS STRING) WHEN 'month' THEN FORMAT_DATE('%Y-%m', DATE(created_at)) ELSE 'total' END as period, COUNT(*) as count FROM events WHERE created_at >= CAST(@start_date AS TIMESTAMP) GROUP BY period ORDER BY period",
    "params": {
      "group_by": "month",
      "start_date": "2023-01-01"
    }
  }
}
```

## Security Considerations

### SQL Injection Prevention

**Safe Parameter Usage:**
```json
{
  "secure_practices": [
    {
      "practice": "use_parameters_only",
      "example": "WHERE user_id = @user_id",
      "avoid": "WHERE user_id = " + user_input
    },
    {
      "practice": "validate_parameter_values",
      "example": "Validate date formats before passing as parameters",
      "avoid": "Passing user input directly without validation"
    },
    {
      "practice": "use_allowlists",
      "example": "Validate @sort_column against allowed column names",
      "avoid": "Dynamic column names without validation"
    }
  ]
}
```

**Parameter Validation Example:**
```json
{
  "parameter_validation": {
    "validate_date_format": {
      "regex": "^\\d{4}-\\d{2}-\\d{2}$",
      "example": "2023-01-01"
    },
    "validate_enum_values": {
      "allowed_statuses": ["active", "inactive", "pending"],
      "validation": "status in allowed_statuses"
    },
    "validate_numeric_ranges": {
      "min_age": {"min": 0, "max": 150},
      "limit": {"min": 1, "max": 10000}
    }
  }
}
```

### Access Control Patterns

**User-Scoped Queries:**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT * FROM user_data WHERE user_id = @current_user_id AND visibility IN ('public', 'user')",
    "params": {
      "current_user_id": "authenticated_user_id"
    }
  }
}
```

**Role-Based Filtering:**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT * FROM sensitive_data WHERE CASE @user_role WHEN 'admin' THEN TRUE WHEN 'manager' THEN department = @user_department ELSE user_id = @user_id END",
    "params": {
      "user_role": "manager",
      "user_department": "sales",
      "user_id": "12345"
    }
  }
}
```

## Performance Optimization

### Parameter Impact on Query Performance

#### Partition Pruning with Parameters

**Effective Partition Pruning:**
```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT * FROM partitioned_table WHERE _PARTITIONDATE = CAST(@partition_date AS DATE)",
    "params": {
      "partition_date": "2023-12-01"
    }
  }
}
```

**Response shows minimal data processing:**
```json
{
  "totalBytesProcessed": 1048576,
  "usdEstimate": 0.000005,
  "analysis": "Effective partition pruning with parameter"
}
```

#### Clustering Optimization

**Clustered Column Filtering:**
```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT * FROM clustered_table WHERE cluster_column = @filter_value",
    "params": {
      "filter_value": "target_value"
    }
  }
}
```

### Query Plan Caching

**Parameter Variations for Caching:**
```json
{
  "caching_strategy": {
    "cache_friendly": {
      "sql": "SELECT * FROM table WHERE date_col >= @date",
      "benefit": "Query plan cached, different @date values reuse plan"
    },
    "cache_breaking": {
      "sql": "SELECT * FROM table WHERE " + dynamic_where_clause,
      "issue": "Each variation creates new query plan"
    }
  }
}
```

## Testing and Debugging

### Parameter Testing Strategies

#### Boundary Value Testing

```json
{
  "boundary_tests": [
    {
      "test_case": "minimum_date",
      "params": {"start_date": "1900-01-01"},
      "expected": "Handle historical data correctly"
    },
    {
      "test_case": "maximum_date",
      "params": {"start_date": "2099-12-31"},
      "expected": "Handle future dates correctly"
    },
    {
      "test_case": "null_values",
      "params": {"optional_filter": null},
      "expected": "Handle null parameters gracefully"
    },
    {
      "test_case": "empty_strings",
      "params": {"search_term": ""},
      "expected": "Handle empty string parameters"
    }
  ]
}
```

#### Type Conversion Testing

```json
{
  "type_conversion_tests": [
    {
      "parameter": "user_id",
      "values": ["123", "0", "-1"],
      "sql": "WHERE user_id = CAST(@user_id AS INT64)",
      "validate": "Ensure proper integer conversion"
    },
    {
      "parameter": "price",
      "values": ["99.99", "0.01", "999999.99"],
      "sql": "WHERE price >= CAST(@price AS FLOAT64)",
      "validate": "Ensure proper float conversion"
    }
  ]
}
```

### Debugging Parameter Issues

#### Common Parameter Problems

```json
{
  "common_issues": [
    {
      "issue": "parameter_not_found",
      "error": "Query error: Unrecognized name: user_id at [1:45]",
      "cause": "Parameter @user_id used in SQL but not provided in params",
      "solution": "Ensure all @parameters in SQL have corresponding params entries"
    },
    {
      "issue": "type_conversion_error",
      "error": "Invalid datetime string '2023-13-01'",
      "cause": "Invalid date format passed as parameter",
      "solution": "Validate parameter formats before passing to query"
    },
    {
      "issue": "null_parameter_handling",
      "error": "Unexpected query behavior with null parameters",
      "cause": "SQL not handling NULL parameter values correctly",
      "solution": "Use COALESCE() or CASE statements for null handling"
    }
  ]
}
```

#### Debugging Workflow

```json
{
  "debugging_steps": [
    {
      "step": 1,
      "action": "validate_sql_syntax",
      "tool": "bq_validate_sql",
      "purpose": "Ensure basic SQL syntax is correct"
    },
    {
      "step": 2,
      "action": "test_with_simple_parameters",
      "approach": "Use basic string/numeric values first"
    },
    {
      "step": 3,
      "action": "add_parameter_complexity",
      "approach": "Gradually add complex parameter types and edge cases"
    },
    {
      "step": 4,
      "action": "validate_with_dry_run",
      "tool": "bq_dry_run_sql",
      "purpose": "Confirm query analysis works with parameters"
    }
  ]
}
```

## Integration Patterns

### Application Integration

#### Parameter Generation from User Input

```json
{
  "user_input_mapping": {
    "web_form": {
      "user_inputs": {
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "category": "electronics"
      },
      "parameter_mapping": {
        "start_date": "user_inputs.start_date",
        "end_date": "user_inputs.end_date", 
        "category": "user_inputs.category || null"
      }
    }
  }
}
```

#### API Integration Patterns

```json
{
  "api_integration": {
    "rest_endpoint": "/api/analytics/users",
    "query_parameters": {
      "start_date": "query_param_or_default_30_days_ago",
      "end_date": "query_param_or_default_today",
      "limit": "query_param_or_default_100"
    },
    "mcp_call": {
      "tool": "bq_dry_run_sql",
      "arguments": {
        "sql": "user_analytics_template",
        "params": "mapped_from_api_parameters"
      }
    }
  }
}
```

### Configuration Management

#### Query Template Storage

```json
{
  "template_management": {
    "storage": {
      "location": "configuration_database_or_files",
      "format": "json_with_sql_and_parameter_definitions"
    },
    "versioning": {
      "approach": "semantic_versioning_for_templates",
      "compatibility": "parameter_backward_compatibility"
    },
    "validation": {
      "syntax_check": "validate_sql_on_template_save",
      "parameter_check": "validate_parameter_definitions"
    }
  }
}
```

#### Environment-Specific Parameters

```json
{
  "environment_config": {
    "development": {
      "default_limit": "100",
      "default_date_range": "7_days",
      "cost_threshold": "0.01"
    },
    "staging": {
      "default_limit": "1000", 
      "default_date_range": "30_days",
      "cost_threshold": "0.10"
    },
    "production": {
      "default_limit": "10000",
      "default_date_range": "90_days",
      "cost_threshold": "1.00"
    }
  }
}
```

## Best Practices Summary

### Parameter Design Principles

1. **Explicit Type Casting**
   - Always use CAST() for non-string parameters
   - Document expected parameter types
   - Validate parameter formats before use

2. **Null Handling**
   - Design queries to handle null parameters gracefully
   - Use COALESCE() for default values
   - Document null parameter behavior

3. **Security First**
   - Use parameters for all dynamic values
   - Validate parameter values against allowlists
   - Never concatenate user input into SQL strings

4. **Performance Awareness**
   - Design parameters to leverage partitioning and clustering
   - Consider query plan caching implications
   - Test parameter variations for performance impact

### Common Pitfalls to Avoid

```json
{
  "pitfalls": [
    {
      "pitfall": "dynamic_column_names",
      "problem": "Cannot use parameters for column names",
      "solution": "Use CASE statements or query generation"
    },
    {
      "pitfall": "complex_array_parameters",
      "problem": "Limited array parameter support in dry-run",
      "solution": "Use string splitting and UNNEST patterns"
    },
    {
      "pitfall": "timezone_confusion",
      "problem": "Timestamp parameters may have timezone issues",
      "solution": "Use explicit timezone conversion in SQL"
    }
  ]
}
```

### Development Workflow

1. **Start Simple** - Begin with basic string parameters
2. **Add Complexity** - Gradually introduce type casting and null handling
3. **Test Thoroughly** - Test boundary conditions and edge cases
4. **Document Well** - Clearly document parameter requirements
5. **Monitor Performance** - Track query costs with different parameter values

## Next Steps

Now that you understand parameterized queries:

- **[Validation Guide](validation.md)** - Validate parameterized queries for syntax errors
- **[Dry-Run Guide](dry-run.md)** - Analyze parameterized queries for performance and cost
- **[Cost Estimation Guide](cost-estimation.md)** - Understand cost implications of parameter variations

For advanced implementation:
- **[API Reference](../api-reference/)** - Complete parameter specifications
- **[Examples](../examples/)** - Complex parameterized query examples
- **[Development Guide](../development/)** - Integration patterns and best practices