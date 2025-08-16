# Dry-Run Analysis Guide

Master BigQuery dry-run analysis to understand query behavior, performance characteristics, and metadata without executing queries using the `bq_dry_run_sql` tool.

## Overview

The `bq_dry_run_sql` tool performs comprehensive query analysis without execution, providing insights into:

- **Data Processing Volume** - Bytes scanned and processed
- **Cost Estimation** - Query cost based on data volume
- **Referenced Tables** - All tables accessed by the query
- **Schema Preview** - Result set structure and column types
- **Performance Insights** - Query complexity indicators

### Key Benefits

- **Zero Execution Cost** - No slot consumption or query charges
- **Comprehensive Analysis** - Complete query metadata
- **Performance Planning** - Understand query requirements
- **Cost Optimization** - Identify expensive operations
- **Schema Discovery** - Preview result structures

## Basic Dry-Run Analysis

### Simple Query Analysis

```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT name, age, created_at FROM users WHERE age > 25"
  }
}
```

**Response:**
```json
{
  "totalBytesProcessed": 2048576,
  "usdEstimate": 0.00001,
  "referencedTables": [
    {
      "project": "my-project",
      "dataset": "analytics",
      "table": "users"
    }
  ],
  "schemaPreview": [
    {
      "name": "name",
      "type": "STRING",
      "mode": "NULLABLE"
    },
    {
      "name": "age",
      "type": "INT64",
      "mode": "NULLABLE"
    },
    {
      "name": "created_at",
      "type": "TIMESTAMP",
      "mode": "NULLABLE"
    }
  ]
}
```

### Aggregation Query Analysis

```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT status, COUNT(*) as count, AVG(age) as avg_age FROM users GROUP BY status ORDER BY count DESC"
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
      "dataset": "analytics", 
      "table": "users"
    }
  ],
  "schemaPreview": [
    {
      "name": "status",
      "type": "STRING",
      "mode": "NULLABLE"
    },
    {
      "name": "count",
      "type": "INT64",
      "mode": "NULLABLE"
    },
    {
      "name": "avg_age",
      "type": "FLOAT64",
      "mode": "NULLABLE"
    }
  ]
}
```

## Understanding Response Data

### Total Bytes Processed

The `totalBytesProcessed` field indicates the amount of data BigQuery would scan:

```json
{
  "dataVolumes": {
    "1KB": 1024,
    "1MB": 1048576,
    "1GB": 1073741824,
    "1TB": 1099511627776
  }
}
```

**Factors affecting bytes processed:**
- **Table size** - Full table scans process all data
- **Column selection** - Fewer columns = less data processed
- **Partitioning** - Partition pruning reduces scan volume
- **Clustering** - Clustered queries scan less data
- **WHERE clauses** - Effective filtering reduces scan volume

### Cost Estimation

The `usdEstimate` provides query cost based on BigQuery's on-demand pricing:

```json
{
  "costCalculation": {
    "formula": "bytes_processed / (2^40) * price_per_tib",
    "default_price_per_tib": 5.0,
    "example": {
      "bytes_processed": 1073741824,
      "tib_processed": 0.000000931,
      "cost_usd": 0.000005
    }
  }
}
```

**Cost optimization strategies:**
- Select only needed columns
- Use effective WHERE clauses
- Leverage partitioning and clustering
- Consider approximate aggregation functions
- Use materialized views for repeated queries

### Referenced Tables

The `referencedTables` array shows all tables accessed:

```json
{
  "complex_query_example": {
    "sql": "SELECT u.name, COUNT(o.id) FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.name",
    "referencedTables": [
      {
        "project": "my-project",
        "dataset": "analytics",
        "table": "users"
      },
      {
        "project": "my-project", 
        "dataset": "analytics",
        "table": "orders"
      }
    ]
  }
}
```

**Use cases for table analysis:**
- **Dependency mapping** - Understand query dependencies
- **Access planning** - Verify table permissions
- **Performance analysis** - Identify expensive table scans
- **Lineage tracking** - Map data flow through queries

### Schema Preview

The `schemaPreview` shows the structure of query results:

```json
{
  "schemaTypes": {
    "STRING": "Text data",
    "INT64": "64-bit integers", 
    "FLOAT64": "Double-precision floating point",
    "BOOLEAN": "True/false values",
    "TIMESTAMP": "Date and time with timezone",
    "DATE": "Calendar date",
    "TIME": "Time of day",
    "DATETIME": "Date and time without timezone",
    "BYTES": "Binary data",
    "ARRAY": "Repeated values",
    "STRUCT": "Nested records",
    "GEOGRAPHY": "Geospatial data"
  }
}
```

**Field modes:**
- **NULLABLE** - Can contain null values
- **REQUIRED** - Cannot be null
- **REPEATED** - Array of values

## Advanced Analysis Patterns

### Complex JOIN Analysis

```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT u.name, p.title, o.amount, o.created_at FROM users u JOIN orders o ON u.id = o.user_id JOIN products p ON o.product_id = p.id WHERE o.created_at >= '2023-01-01'"
  }
}
```

**Analysis insights:**
- **Cross-table relationships** - Verify JOIN conditions
- **Data volume impact** - Understand JOIN cardinality effects
- **Performance characteristics** - Identify expensive operations

### Window Function Analysis

```json
{
  "tool": "bq_dry_run_sql", 
  "arguments": {
    "sql": "SELECT name, amount, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) as rank FROM orders"
  }
}
```

**Window function considerations:**
- **Partition efficiency** - Smaller partitions = better performance
- **Ordering cost** - ORDER BY in window functions adds overhead
- **Memory requirements** - Large partitions require more memory

### Subquery and CTE Analysis

```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "WITH user_stats AS (SELECT user_id, COUNT(*) as order_count, SUM(amount) as total_spent FROM orders GROUP BY user_id) SELECT u.name, s.order_count, s.total_spent FROM users u JOIN user_stats s ON u.id = s.user_id WHERE s.total_spent > 1000"
  }
}
```

**CTE optimization benefits:**
- **Readable query structure** - Clear logical separation
- **Potential materialization** - BigQuery may materialize CTEs
- **Reusability** - Reference CTE multiple times

## Performance Analysis

### Identifying Expensive Operations

**High Data Volume Queries:**
```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT * FROM large_table"
  }
}
```

Response indicates full table scan:
```json
{
  "totalBytesProcessed": 107374182400,
  "usdEstimate": 0.5,
  "analysis": "Full table scan - consider adding WHERE clauses"
}
```

**Optimized Version:**
```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT id, name FROM large_table WHERE created_at >= '2023-01-01'"
  }
}
```

Response shows reduced processing:
```json
{
  "totalBytesProcessed": 5368709120,
  "usdEstimate": 0.025,
  "analysis": "Partition pruning + column selection reduced cost by 95%"
}
```

### Comparing Query Alternatives

**Approach A - Subquery:**
```json
{
  "sql": "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders WHERE amount > 100)"
}
```

**Approach B - JOIN:**
```json
{
  "sql": "SELECT DISTINCT u.* FROM users u JOIN orders o ON u.id = o.user_id WHERE o.amount > 100"
}
```

Compare `totalBytesProcessed` to choose the more efficient approach.

### Optimization Techniques

#### Column Selection Optimization

**Before - Select All:**
```json
{
  "sql": "SELECT * FROM wide_table",
  "result": {
    "totalBytesProcessed": 50000000000,
    "usdEstimate": 0.233
  }
}
```

**After - Select Specific:**
```json
{
  "sql": "SELECT id, name, email FROM wide_table",
  "result": {
    "totalBytesProcessed": 5000000000,
    "usdEstimate": 0.023
  }
}
```

#### Partition Pruning

**Before - No Partition Filter:**
```json
{
  "sql": "SELECT * FROM partitioned_table WHERE status = 'active'",
  "result": {
    "totalBytesProcessed": 20000000000,
    "usdEstimate": 0.093
  }
}
```

**After - With Partition Filter:**
```json
{
  "sql": "SELECT * FROM partitioned_table WHERE date_partition = '2023-12-01' AND status = 'active'",
  "result": {
    "totalBytesProcessed": 500000000,
    "usdEstimate": 0.002
  }
}
```

## Cost Analysis Patterns

### Setting Custom Pricing

```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT COUNT(*) FROM large_dataset",
    "pricePerTiB": 6.25
  }
}
```

**Use cases for custom pricing:**
- **Regional variations** - Different regions have different costs
- **Reserved slots** - Flat-rate pricing considerations
- **Enterprise discounts** - Volume-based pricing agreements

### Batch Cost Analysis

```json
{
  "queries": [
    {
      "name": "daily_report",
      "sql": "SELECT date, COUNT(*) FROM events WHERE date = CURRENT_DATE()",
      "estimated_frequency": "daily"
    },
    {
      "name": "weekly_analysis", 
      "sql": "SELECT user_id, SUM(amount) FROM orders WHERE created_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY) GROUP BY user_id",
      "estimated_frequency": "weekly"
    }
  ]
}
```

Analyze total cost impact across all regular queries.

### Cost Alerting Thresholds

```json
{
  "cost_thresholds": {
    "low": 0.01,
    "medium": 0.10,
    "high": 1.00,
    "critical": 10.00
  },
  "actions": {
    "medium": "review_query_optimization",
    "high": "require_approval",
    "critical": "block_execution"
  }
}
```

## Schema Analysis

### Result Schema Planning

```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT user_id, COUNT(*) as order_count, AVG(amount) as avg_amount, MAX(created_at) as last_order FROM orders GROUP BY user_id"
  }
}
```

**Schema preview usage:**
- **Application integration** - Plan data structure handling
- **Visualization tools** - Configure chart types based on data types
- **Data pipelines** - Design downstream processing
- **API responses** - Structure JSON responses

### Type Compatibility Analysis

```json
{
  "type_compatibility": {
    "joins": "Ensure compatible types in JOIN conditions",
    "unions": "All UNION queries must have matching schemas",
    "functions": "Function parameters must match expected types",
    "aggregations": "Aggregation functions have type requirements"
  }
}
```

### Complex Type Handling

**ARRAY and STRUCT Analysis:**
```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT user_id, ARRAY_AGG(STRUCT(product_id, amount)) as purchases FROM orders GROUP BY user_id"
  }
}
```

Response shows complex schema:
```json
{
  "schemaPreview": [
    {
      "name": "user_id",
      "type": "INT64",
      "mode": "NULLABLE"
    },
    {
      "name": "purchases",
      "type": "STRUCT",
      "mode": "REPEATED",
      "fields": [
        {"name": "product_id", "type": "INT64"},
        {"name": "amount", "type": "FLOAT64"}
      ]
    }
  ]
}
```

## Error Handling and Troubleshooting

### Common Dry-Run Errors

#### Invalid SQL Syntax

```json
{
  "error": {
    "code": "INVALID_SQL",
    "message": "Syntax error: Expected \")\" but got \",\" at [1:25]"
  }
}
```

**Solution:** Fix syntax errors before dry-run analysis.

#### Table Access Issues

```json
{
  "error": {
    "code": "INVALID_SQL", 
    "message": "Access Denied: Table my-project:dataset.protected_table"
  }
}
```

**Solutions:**
- Verify table permissions
- Check project and dataset access
- Ensure proper authentication

#### Query Timeout Issues

For extremely complex queries:
```json
{
  "error": {
    "code": "UNKNOWN_ERROR",
    "message": "Query analysis timeout"
  }
}
```

**Solutions:**
- Simplify query structure
- Break complex queries into parts
- Use CTEs for better organization

### Debugging Strategies

#### Progressive Analysis

1. **Start Simple:** Analyze core query without complex operations
2. **Add Complexity:** Incrementally add JOINs, aggregations, window functions
3. **Compare Results:** Monitor how each addition affects processing volume
4. **Optimize:** Address expensive operations before adding more complexity

#### Data Volume Investigation

```json
{
  "investigation_steps": [
    {
      "step": "table_size_check",
      "sql": "SELECT COUNT(*) FROM table_name"
    },
    {
      "step": "column_analysis", 
      "sql": "SELECT column_name FROM table_name LIMIT 1"
    },
    {
      "step": "partition_check",
      "sql": "SELECT _PARTITIONTIME FROM table_name LIMIT 1"
    }
  ]
}
```

## Integration Patterns

### Development Workflow

```json
{
  "workflow": [
    {
      "stage": "development",
      "action": "frequent_dry_runs",
      "purpose": "rapid_feedback"
    },
    {
      "stage": "testing",
      "action": "comprehensive_analysis", 
      "purpose": "performance_validation"
    },
    {
      "stage": "production",
      "action": "cost_monitoring",
      "purpose": "budget_control"
    }
  ]
}
```

### Automated Analysis

```json
{
  "automation": {
    "triggers": [
      "code_commit",
      "pull_request",
      "scheduled_review"
    ],
    "actions": [
      "dry_run_analysis",
      "cost_comparison",
      "performance_regression_check"
    ]
  }
}
```

### Monitoring and Alerting

```json
{
  "monitoring": {
    "metrics": [
      "query_cost_trends",
      "data_volume_growth",
      "schema_changes",
      "performance_degradation"
    ],
    "alerts": [
      "cost_threshold_exceeded",
      "unexpected_table_access",
      "schema_compatibility_issues"
    ]
  }
}
```

## Performance Optimization Guide

### Query Optimization Checklist

1. **Column Selection**
   - [ ] Select only required columns
   - [ ] Avoid SELECT * in production queries
   - [ ] Use column pruning for nested data

2. **Filtering Optimization**
   - [ ] Apply WHERE clauses early
   - [ ] Use partition filters when possible
   - [ ] Leverage clustering for filter columns

3. **JOIN Optimization**
   - [ ] Use appropriate JOIN types
   - [ ] Filter before JOINing when possible
   - [ ] Consider JOIN order for large tables

4. **Aggregation Efficiency**
   - [ ] Use appropriate GROUP BY strategies
   - [ ] Consider APPROX_ functions for large datasets
   - [ ] Optimize window function partitions

### Cost Optimization Strategies

**Immediate Optimizations:**
- Column selection refinement
- Effective WHERE clauses
- Partition pruning utilization

**Structural Optimizations:**
- Table partitioning design
- Clustering key selection
- Materialized view creation

**Long-term Optimizations:**
- Data model optimization
- Query pattern analysis
- Reserved slot evaluation

## Next Steps

Now that you understand dry-run analysis, explore:

- **[Cost Estimation Guide](cost-estimation.md)** - Deep dive into BigQuery pricing and optimization
- **[Parameters Guide](parameters.md)** - Use parameterized queries for dynamic analysis
- **[Validation Guide](validation.md)** - Ensure SQL correctness before analysis

For advanced topics:
- **[API Reference](../api-reference/)** - Complete tool specifications
- **[Examples](../examples/)** - Complex analysis scenarios
- **[Development Guide](../development/)** - Integration and automation patterns