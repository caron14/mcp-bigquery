# Basic Examples

This guide provides practical examples for common MCP BigQuery usage patterns. Each example includes complete JSON request/response pairs that you can copy and run immediately.

## Prerequisites

Before running these examples, ensure you have:

- MCP BigQuery installed and configured
- Google Cloud authentication set up (`gcloud auth application-default login`)
- BigQuery Job User permissions

## 1. Simple SQL Validation

Start with basic syntax validation to ensure your SQL is correct.

### Valid Query Example

**Request:**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT 'Hello BigQuery' as greeting, CURRENT_TIMESTAMP() as current_time"
  }
}
```

**Response:**
```json
{
  "isValid": true
}
```

### Invalid Query Example

**Request:**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT name, age FORM users WHERE age > 25"
  }
}
```

**Response:**
```json
{
  "isValid": false,
  "error": {
    "code": "INVALID_SQL",
    "message": "Syntax error: Expected \"FROM\" but got \"FORM\" at [1:17]",
    "location": {
      "line": 1,
      "column": 17
    }
  }
}
```

**Key Learning:** The error response includes the exact location (`line` and `column`) where the syntax error occurs, making it easy to identify and fix issues.

## 2. Cost Estimation with Public Data

Use the Shakespeare dataset to understand cost estimation without incurring charges.

### Small Dataset Query

**Request:**
```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT word, word_count FROM `bigquery-public-data.samples.shakespeare` WHERE word_count > 100 ORDER BY word_count DESC LIMIT 10"
  }
}
```

**Response:**
```json
{
  "totalBytesProcessed": 164864,
  "usdEstimate": 0.000001,
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

**Key Learning:** Even complex queries on small datasets cost very little. The Shakespeare dataset is perfect for testing since it's only ~165 KB.

## 3. Working with Parameters

Parameters make queries reusable and safer by preventing SQL injection.

### Basic Parameterized Query

**Request:**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT word, word_count FROM `bigquery-public-data.samples.shakespeare` WHERE word_count >= @min_count AND word = @target_word",
    "params": {
      "min_count": "50",
      "target_word": "love"
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

### Array Parameters

**Request:**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT corpus, COUNT(*) as word_count FROM `bigquery-public-data.samples.shakespeare` WHERE corpus IN UNNEST(@corpus_list) GROUP BY corpus",
    "params": {
      "corpus_list": "[\"hamlet\", \"macbeth\", \"romeoandjuliet\"]"
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

**Key Learning:** In dry-run mode, all parameters are treated as STRING type. Use proper casting in your SQL when needed (e.g., `CAST(@param AS INT64)`).

## 4. Error Handling Patterns

Understanding different types of errors helps you write more robust code.

### Missing Table Error

**Request:**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT * FROM non_existent_table"
  }
}
```

**Response:**
```json
{
  "isValid": false,
  "error": {
    "code": "INVALID_SQL",
    "message": "Table 'non_existent_table' was not found in location US",
    "details": [
      {
        "message": "Table does not exist",
        "location": "non_existent_table"
      }
    ]
  }
}
```

### Column Reference Error

**Request:**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT word, non_existent_column FROM `bigquery-public-data.samples.shakespeare`"
  }
}
```

**Response:**
```json
{
  "isValid": false,
  "error": {
    "code": "INVALID_SQL",
    "message": "Unrecognized name: non_existent_column at [1:13]",
    "location": {
      "line": 1,
      "column": 13
    }
  }
}
```

**Key Learning:** BigQuery provides specific error codes and locations, making debugging straightforward.

## 5. Schema Exploration

Use dry-run to understand what columns a query will return.

### Basic Schema Preview

**Request:**
```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT word, word_count, UPPER(word) as word_upper, word_count * 2 as double_count FROM `bigquery-public-data.samples.shakespeare` LIMIT 1"
  }
}
```

**Response:**
```json
{
  "totalBytesProcessed": 164864,
  "usdEstimate": 0.000001,
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
    },
    {
      "name": "word_upper",
      "type": "STRING",
      "mode": "NULLABLE"
    },
    {
      "name": "double_count",
      "type": "INT64",
      "mode": "NULLABLE"
    }
  ]
}
```

**Key Learning:** The schema preview shows all columns that would be returned, including computed columns with their correct data types.

## 6. Aggregation Queries

Explore how aggregations affect cost and result schemas.

### Simple Aggregation

**Request:**
```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT corpus, COUNT(*) as total_words, SUM(word_count) as total_occurrences, AVG(word_count) as avg_word_count FROM `bigquery-public-data.samples.shakespeare` GROUP BY corpus ORDER BY total_occurrences DESC"
  }
}
```

**Response:**
```json
{
  "totalBytesProcessed": 164864,
  "usdEstimate": 0.000001,
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
      "name": "total_words",
      "type": "INT64",
      "mode": "NULLABLE"
    },
    {
      "name": "total_occurrences",
      "type": "INT64",
      "mode": "NULLABLE"
    },
    {
      "name": "avg_word_count",
      "type": "FLOAT64",
      "mode": "NULLABLE"
    }
  ]
}
```

**Key Learning:** Aggregation functions return appropriate data types (COUNT returns INT64, AVG returns FLOAT64).

## 7. Date and Time Functions

Working with temporal data is common in analytics.

### Date Functions with Public Data

**Request:**
```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT CURRENT_DATE() as today, CURRENT_TIMESTAMP() as now, DATE_ADD(CURRENT_DATE(), INTERVAL 30 DAY) as thirty_days_later, EXTRACT(YEAR FROM CURRENT_DATE()) as current_year"
  }
}
```

**Response:**
```json
{
  "totalBytesProcessed": 0,
  "usdEstimate": 0.0,
  "referencedTables": [],
  "schemaPreview": [
    {
      "name": "today",
      "type": "DATE",
      "mode": "NULLABLE"
    },
    {
      "name": "now",
      "type": "TIMESTAMP",
      "mode": "NULLABLE"
    },
    {
      "name": "thirty_days_later",
      "type": "DATE",
      "mode": "NULLABLE"
    },
    {
      "name": "current_year",
      "type": "INT64",
      "mode": "NULLABLE"
    }
  ]
}
```

**Key Learning:** Queries that don't scan tables (like date functions) have zero cost and no referenced tables.

## 8. String Functions and Regular Expressions

Text processing is essential for data cleaning and analysis.

### String Manipulation

**Request:**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT word, LENGTH(word) as word_length, UPPER(word) as upper_word, REGEXP_CONTAINS(word, r'^[aeiou]') as starts_with_vowel FROM `bigquery-public-data.samples.shakespeare` WHERE LENGTH(word) > 10 LIMIT 5"
  }
}
```

**Response:**
```json
{
  "isValid": true
}
```

### Regular Expression Extraction

**Request:**
```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT word, REGEXP_EXTRACT(word, r'([aeiou]+)') as vowel_sequence, CASE WHEN REGEXP_CONTAINS(word, r'^[AEIOU]') THEN 'Vowel Start' ELSE 'Consonant Start' END as word_type FROM `bigquery-public-data.samples.shakespeare` WHERE word IS NOT NULL LIMIT 10"
  }
}
```

**Response:**
```json
{
  "totalBytesProcessed": 164864,
  "usdEstimate": 0.000001,
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
      "name": "vowel_sequence",
      "type": "STRING",
      "mode": "NULLABLE"
    },
    {
      "name": "word_type",
      "type": "STRING",
      "mode": "NULLABLE"
    }
  ]
}
```

**Key Learning:** Regular expressions and CASE statements work as expected in dry-run mode, allowing you to test complex text processing logic.

## 9. Cost Comparison Example

Compare different query approaches to understand cost implications.

### Approach 1: SELECT * (More Expensive)

**Request:**
```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT * FROM `bigquery-public-data.samples.shakespeare` WHERE word_count > 100"
  }
}
```

**Response:**
```json
{
  "totalBytesProcessed": 164864,
  "usdEstimate": 0.000001,
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
    },
    {
      "name": "corpus",
      "type": "STRING",
      "mode": "NULLABLE"
    },
    {
      "name": "corpus_date",
      "type": "INT64",
      "mode": "NULLABLE"
    }
  ]
}
```

### Approach 2: SELECT Specific Columns (Same Cost on Small Tables)

**Request:**
```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT word, word_count FROM `bigquery-public-data.samples.shakespeare` WHERE word_count > 100"
  }
}
```

**Response:**
```json
{
  "totalBytesProcessed": 164864,
  "usdEstimate": 0.000001,
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

**Key Learning:** On columnar storage like BigQuery, selecting specific columns reduces data scanned. The Shakespeare table is small, so the difference isn't visible, but this matters on large tables.

## 10. Common Patterns for E-commerce

These examples use hypothetical e-commerce tables to demonstrate real-world patterns.

### Customer Analysis (Validation Only)

**Request:**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT customer_id, COUNT(*) as total_orders, SUM(order_amount) as total_spent, AVG(order_amount) as avg_order_value, MAX(order_date) as last_order_date FROM orders WHERE order_date >= @start_date GROUP BY customer_id HAVING COUNT(*) >= @min_orders ORDER BY total_spent DESC",
    "params": {
      "start_date": "2024-01-01",
      "min_orders": "3"
    }
  }
}
```

**Response:**
```json
{
  "isValid": false,
  "error": {
    "code": "INVALID_SQL",
    "message": "Table 'orders' was not found in location US"
  }
}
```

**Key Learning:** This query validates correctly for syntax and logic, but fails because the `orders` table doesn't exist. In a real environment with actual tables, this would validate successfully.

### Product Performance Metrics

**Request:**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "WITH monthly_sales AS (SELECT product_id, EXTRACT(YEAR FROM order_date) as year, EXTRACT(MONTH FROM order_date) as month, SUM(quantity) as units_sold, SUM(quantity * price) as revenue FROM order_items oi JOIN orders o ON oi.order_id = o.order_id WHERE order_date >= @start_date GROUP BY product_id, year, month) SELECT product_id, year, month, units_sold, revenue, LAG(revenue, 1) OVER (PARTITION BY product_id ORDER BY year, month) as prev_month_revenue, (revenue - LAG(revenue, 1) OVER (PARTITION BY product_id ORDER BY year, month)) / LAG(revenue, 1) OVER (PARTITION BY product_id ORDER BY year, month) * 100 as growth_rate FROM monthly_sales ORDER BY product_id, year, month",
    "params": {
      "start_date": "2024-01-01"
    }
  }
}
```

**Response:**
```json
{
  "isValid": false,
  "error": {
    "code": "INVALID_SQL",
    "message": "Table 'order_items' was not found in location US"
  }
}
```

**Key Learning:** Complex queries with CTEs, window functions, and joins validate correctly for syntax. The error occurs only because the referenced tables don't exist.

## Common Patterns Summary

### Validation Workflow
1. **Validate Syntax** → Use `bq_validate_sql` first
2. **Check Costs** → Use `bq_dry_run_sql` for cost estimation  
3. **Review Schema** → Examine `schemaPreview` for expected results
4. **Handle Errors** → Check `error.location` for syntax issues

### Error Prevention Tips
- Always use fully qualified table names: `project.dataset.table`
- Include all non-aggregate columns in GROUP BY clauses
- Use explicit type casting for parameters: `CAST(@param AS INT64)`
- Test with representative parameter values
- Start with simple queries and add complexity incrementally

### Cost Optimization Rules
- Select only needed columns instead of `SELECT *`
- Use WHERE clauses to filter data early
- Leverage table partitioning when available
- Test queries with LIMIT first, then remove for production
- Compare different approaches using dry-run cost estimates

## Next Steps

Now that you understand basic patterns, explore:

- **[Advanced Examples](advanced.md)** - Complex analytics, optimization techniques, and production patterns
- **[Validation Guide](../guides/validation.md)** - Comprehensive error handling and debugging
- **[Cost Estimation Guide](../guides/cost-estimation.md)** - Optimization strategies and cost management