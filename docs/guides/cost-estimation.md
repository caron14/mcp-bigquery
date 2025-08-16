# Cost Estimation Guide

Master BigQuery cost estimation and optimization using MCP BigQuery's dry-run analysis. Learn to understand, predict, and optimize query costs effectively.

## Overview

BigQuery uses a pay-per-query model based on the amount of data processed. The MCP BigQuery server provides accurate cost estimation through dry-run analysis, helping you:

- **Predict query costs** before execution
- **Optimize expensive queries** through analysis
- **Set up cost controls** and budgets
- **Compare optimization strategies** objectively
- **Plan capacity and budgets** effectively

### BigQuery Pricing Fundamentals

BigQuery charges for data processing in two main models:

**On-Demand Pricing:**
- $5.00 USD per TiB (2^40 bytes) processed
- Charges rounded to the nearest MB
- Minimum 10 MB per query
- No slot reservation required

**Flat-Rate Pricing:**
- Reserved slot capacity
- Predictable monthly costs
- Better for consistent high-volume workloads

## Cost Calculation Basics

### Understanding the Formula

```json
{
  "cost_formula": {
    "description": "Cost = (bytes_processed / 2^40) * price_per_tib",
    "components": {
      "bytes_processed": "Total data scanned by query",
      "tib_constant": 1099511627776,
      "price_per_tib": "Current BigQuery pricing (default: $5.00)"
    }
  }
}
```

### Basic Cost Estimation

```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT name, email FROM users WHERE created_at >= '2023-01-01'"
  }
}
```

**Response:**
```json
{
  "totalBytesProcessed": 524288000,
  "usdEstimate": 0.000002,
  "costBreakdown": {
    "tib_processed": 0.000000477,
    "price_per_tib": 5.0,
    "calculation": "0.000000477 * 5.0 = $0.000002"
  }
}
```

### Custom Pricing Configuration

```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT COUNT(*) FROM large_dataset",
    "pricePerTiB": 6.25
  }
}
```

**Use Cases for Custom Pricing:**
- **Regional variations** - EU/Asia pricing differences
- **Enterprise discounts** - Volume-based pricing agreements
- **Historical analysis** - Using past pricing for trend analysis
- **Conservative estimates** - Higher pricing for budget safety

## Data Volume Analysis

### Understanding Bytes Processed

The `totalBytesProcessed` metric represents the amount of data BigQuery scans:

```json
{
  "data_size_reference": {
    "1 KB": 1024,
    "1 MB": 1048576,
    "1 GB": 1073741824,
    "1 TB": 1099511627776,
    "1 TiB": 1099511627776,
    "minimum_charge": 10485760
  }
}
```

### Factors Affecting Data Processing

#### Column Selection Impact

**Full Table Scan:**
```json
{
  "sql": "SELECT * FROM wide_table",
  "result": {
    "totalBytesProcessed": 10737418240,
    "usdEstimate": 0.00005,
    "analysis": "All columns processed"
  }
}
```

**Selective Columns:**
```json
{
  "sql": "SELECT id, name FROM wide_table", 
  "result": {
    "totalBytesProcessed": 1073741824,
    "usdEstimate": 0.000005,
    "savings": "90% cost reduction"
  }
}
```

#### Partition Pruning Benefits

**Without Partition Filter:**
```json
{
  "sql": "SELECT * FROM partitioned_table WHERE status = 'active'",
  "result": {
    "totalBytesProcessed": 53687091200,
    "usdEstimate": 0.00025,
    "analysis": "Full table scan across all partitions"
  }
}
```

**With Partition Filter:**
```json
{
  "sql": "SELECT * FROM partitioned_table WHERE _PARTITIONDATE = '2023-12-01' AND status = 'active'",
  "result": {
    "totalBytesProcessed": 1073741824,
    "usdEstimate": 0.000005,
    "savings": "98% cost reduction through partition pruning"
  }
}
```

#### Clustering Impact

**Before Clustering Optimization:**
```json
{
  "sql": "SELECT * FROM events WHERE event_type = 'purchase'",
  "result": {
    "totalBytesProcessed": 21474836480,
    "usdEstimate": 0.0001,
    "analysis": "Full scan without clustering benefits"
  }
}
```

**After Clustering on event_type:**
```json
{
  "sql": "SELECT * FROM events WHERE event_type = 'purchase'",
  "result": {
    "totalBytesProcessed": 2147483648,
    "usdEstimate": 0.00001,
    "savings": "90% reduction through clustering"
  }
}
```

## Cost Optimization Strategies

### Immediate Optimizations

#### 1. Column Selection Optimization

**Identify Expensive Columns:**
```json
{
  "column_analysis": [
    {
      "query": "SELECT large_text_column FROM table",
      "cost": 0.05,
      "optimization": "Avoid selecting large TEXT/BYTES columns when not needed"
    },
    {
      "query": "SELECT id, name FROM table",
      "cost": 0.001,
      "benefit": "50x cost reduction by selecting only needed columns"
    }
  ]
}
```

**Best Practices:**
- Avoid `SELECT *` in production queries
- Select only required columns
- Use column pruning for nested data
- Consider view definitions for commonly used column sets

#### 2. WHERE Clause Optimization

**Effective Filtering:**
```json
{
  "filtering_strategies": [
    {
      "strategy": "early_filtering",
      "example": "WHERE date_column >= '2023-01-01'",
      "benefit": "Reduces data processed before expensive operations"
    },
    {
      "strategy": "partition_aware_filtering",
      "example": "WHERE _PARTITIONDATE BETWEEN '2023-01-01' AND '2023-01-31'",
      "benefit": "Leverages partition pruning for maximum efficiency"
    }
  ]
}
```

**Filter Optimization Examples:**

Before optimization:
```json
{
  "sql": "SELECT user_id, SUM(amount) FROM orders GROUP BY user_id HAVING SUM(amount) > 1000",
  "cost_analysis": {
    "totalBytesProcessed": 10737418240,
    "usdEstimate": 0.00005,
    "issue": "Processes all data before filtering"
  }
}
```

After optimization:
```json
{
  "sql": "SELECT user_id, SUM(amount) FROM orders WHERE amount > 100 GROUP BY user_id HAVING SUM(amount) > 1000",
  "cost_analysis": {
    "totalBytesProcessed": 2147483648,
    "usdEstimate": 0.00001,
    "improvement": "80% cost reduction through pre-filtering"
  }
}
```

### Structural Optimizations

#### 1. Table Design for Cost Efficiency

**Partitioning Strategy:**
```json
{
  "partitioning_benefits": {
    "time_based": {
      "example": "Partition by DATE(created_at)",
      "benefit": "Automatic pruning for time-range queries",
      "cost_impact": "Up to 95% reduction for filtered queries"
    },
    "ingestion_time": {
      "example": "Partition by _PARTITIONDATE",
      "benefit": "Simple partition pruning setup",
      "cost_impact": "Effective for recent data queries"
    }
  }
}
```

**Clustering Strategy:**
```json
{
  "clustering_optimization": {
    "high_cardinality": {
      "example": "CLUSTER BY user_id",
      "benefit": "Efficient for equality and range filters",
      "cost_impact": "50-90% reduction for filtered queries"
    },
    "multi_column": {
      "example": "CLUSTER BY status, created_date",
      "benefit": "Optimizes multiple filter combinations",
      "cost_impact": "Compound benefits for multi-filter queries"
    }
  }
}
```

#### 2. Query Structure Optimization

**JOIN Optimization:**

Expensive JOIN pattern:
```json
{
  "sql": "SELECT * FROM large_table l JOIN small_table s ON l.id = s.id",
  "cost_analysis": {
    "totalBytesProcessed": 107374182400,
    "usdEstimate": 0.0005,
    "issue": "Processes all columns from large table"
  }
}
```

Optimized JOIN pattern:
```json
{
  "sql": "SELECT l.id, l.name, s.category FROM large_table l JOIN small_table s ON l.id = s.id WHERE l.status = 'active'",
  "cost_analysis": {
    "totalBytesProcessed": 5368709120,
    "usdEstimate": 0.000025,
    "improvement": "95% cost reduction through column selection and filtering"
  }
}
```

**Aggregation Optimization:**

Standard aggregation:
```json
{
  "sql": "SELECT COUNT(DISTINCT user_id) FROM events",
  "cost_analysis": {
    "totalBytesProcessed": 53687091200,
    "usdEstimate": 0.00025,
    "note": "Exact distinct count requires full scan"
  }
}
```

Approximate aggregation:
```json
{
  "sql": "SELECT APPROX_COUNT_DISTINCT(user_id) FROM events",
  "cost_analysis": {
    "totalBytesProcessed": 5368709120,
    "usdEstimate": 0.000025,
    "improvement": "90% cost reduction with minimal accuracy loss"
  }
}
```

## Advanced Cost Analysis

### Query Pattern Analysis

#### Identifying Cost Patterns

```json
{
  "common_expensive_patterns": [
    {
      "pattern": "Cross JOIN",
      "example": "SELECT * FROM table1 CROSS JOIN table2",
      "cost_impact": "Exponential growth - avoid when possible",
      "alternatives": ["Use explicit JOIN conditions", "Consider WHERE clauses"]
    },
    {
      "pattern": "Unfiltered window functions",
      "example": "SELECT *, ROW_NUMBER() OVER (ORDER BY col) FROM large_table",
      "cost_impact": "Processes entire table for ordering",
      "alternatives": ["Add PARTITION BY clause", "Use WHERE filters first"]
    },
    {
      "pattern": "Large table unions",
      "example": "SELECT * FROM table1 UNION ALL SELECT * FROM table2",
      "cost_impact": "Additive costs from all unioned tables",
      "alternatives": ["Filter each table separately", "Use table sharding patterns"]
    }
  ]
}
```

#### Cost Comparison Analysis

```json
{
  "query_alternatives": [
    {
      "approach": "subquery",
      "sql": "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders WHERE amount > 100)",
      "analysis": {
        "totalBytesProcessed": 10737418240,
        "usdEstimate": 0.00005
      }
    },
    {
      "approach": "join",
      "sql": "SELECT DISTINCT u.* FROM users u JOIN orders o ON u.id = o.user_id WHERE o.amount > 100",
      "analysis": {
        "totalBytesProcessed": 8589934592,
        "usdEstimate": 0.00004,
        "improvement": "20% cost reduction"
      }
    },
    {
      "approach": "exists",
      "sql": "SELECT * FROM users u WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id AND o.amount > 100)",
      "analysis": {
        "totalBytesProcessed": 6442450944,
        "usdEstimate": 0.00003,
        "improvement": "40% cost reduction - best option"
      }
    }
  ]
}
```

### Cost Budgeting and Controls

#### Setting Cost Thresholds

```json
{
  "cost_control_framework": {
    "thresholds": {
      "development": {
        "warning": 0.01,
        "limit": 0.05,
        "description": "Low thresholds for development safety"
      },
      "staging": {
        "warning": 0.10,
        "limit": 0.50,
        "description": "Medium thresholds for testing"
      },
      "production": {
        "warning": 1.00,
        "limit": 10.00,
        "description": "High thresholds for production workloads"
      }
    },
    "actions": {
      "warning": ["log_alert", "notify_developer"],
      "limit": ["block_execution", "require_approval"]
    }
  }
}
```

#### Budget Planning

**Monthly Cost Estimation:**
```json
{
  "budget_planning": {
    "regular_queries": [
      {
        "name": "daily_report",
        "cost_per_run": 0.25,
        "frequency": "daily",
        "monthly_cost": 7.75
      },
      {
        "name": "weekly_analysis",
        "cost_per_run": 2.50,
        "frequency": "weekly", 
        "monthly_cost": 10.00
      },
      {
        "name": "monthly_aggregation",
        "cost_per_run": 15.00,
        "frequency": "monthly",
        "monthly_cost": 15.00
      }
    ],
    "total_monthly_budget": 32.75,
    "safety_margin": 1.2,
    "recommended_budget": 39.30
  }
}
```

## Regional and Pricing Considerations

### Regional Pricing Variations

```json
{
  "regional_pricing": {
    "us_multi_region": {
      "price_per_tib": 5.00,
      "currency": "USD"
    },
    "europe_multi_region": {
      "price_per_tib": 5.50,
      "currency": "USD"
    },
    "asia_pacific": {
      "price_per_tib": 5.50,
      "currency": "USD"
    }
  }
}
```

**Using Regional Pricing:**
```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT COUNT(*) FROM europe_dataset",
    "pricePerTiB": 5.50
  }
}
```

### Flat-Rate vs On-Demand Analysis

```json
{
  "pricing_model_comparison": {
    "on_demand": {
      "calculation": "cost_per_query = bytes_processed * price_per_tib",
      "best_for": "Variable workloads, development, ad-hoc analysis",
      "considerations": "Costs scale with data processed"
    },
    "flat_rate": {
      "calculation": "monthly_cost = slots * slot_price * hours",
      "best_for": "Consistent high-volume workloads",
      "considerations": "Fixed cost regardless of data processed"
    }
  }
}
```

## Cost Monitoring and Optimization

### Automated Cost Tracking

```json
{
  "cost_monitoring_setup": {
    "query_logging": {
      "track_metrics": ["totalBytesProcessed", "usdEstimate", "executionTime"],
      "storage": "time_series_database",
      "retention": "12_months"
    },
    "alerting": {
      "daily_budget_exceeded": "alert_when_daily_cost > threshold",
      "expensive_query_detected": "alert_when_single_query > limit",
      "cost_trend_analysis": "alert_when_weekly_trend > growth_rate"
    }
  }
}
```

### Performance vs Cost Optimization

```json
{
  "optimization_strategies": [
    {
      "strategy": "materialized_views",
      "cost_impact": "Higher storage cost, lower query cost",
      "when_to_use": "Frequently accessed aggregations",
      "example": {
        "before": "Daily aggregation query: $5.00",
        "after": "Materialized view refresh: $5.00, Daily query: $0.01"
      }
    },
    {
      "strategy": "table_clustering",
      "cost_impact": "One-time clustering cost, ongoing query savings",
      "when_to_use": "Repeated filtered queries",
      "example": {
        "clustering_cost": "$2.00 one-time",
        "query_savings": "$0.50 per query"
      }
    }
  ]
}
```

## Cost Optimization Workflows

### Development Workflow

```json
{
  "development_cost_workflow": [
    {
      "stage": "query_development",
      "actions": [
        "validate_sql_syntax",
        "run_dry_run_analysis", 
        "check_cost_threshold"
      ],
      "cost_limit": 0.01
    },
    {
      "stage": "testing",
      "actions": [
        "comprehensive_cost_analysis",
        "compare_optimization_alternatives",
        "performance_benchmarking"
      ],
      "cost_limit": 0.10
    },
    {
      "stage": "production_deployment",
      "actions": [
        "final_cost_validation",
        "set_monitoring_alerts",
        "document_expected_costs"
      ],
      "cost_limit": "approved_budget"
    }
  ]
}
```

### Optimization Review Process

```json
{
  "optimization_review": {
    "frequency": "monthly",
    "analysis_areas": [
      {
        "area": "top_expensive_queries",
        "action": "identify_optimization_opportunities"
      },
      {
        "area": "cost_trend_analysis", 
        "action": "detect_cost_growth_patterns"
      },
      {
        "area": "unused_resources",
        "action": "identify_elimination_candidates"
      }
    ],
    "deliverables": [
      "cost_optimization_report",
      "recommended_actions",
      "budget_adjustments"
    ]
  }
}
```

## Troubleshooting Cost Issues

### Unexpected High Costs

#### Investigation Steps

1. **Query Analysis:**
```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT table_name, total_bytes FROM __TABLES__ WHERE table_name = 'suspicious_table'"
  }
}
```

2. **Table Size Analysis:**
```json
{
  "table_investigation": [
    "Check table schema and size",
    "Verify partition and clustering status", 
    "Review recent data growth patterns",
    "Analyze query access patterns"
  ]
}
```

#### Common High-Cost Causes

```json
{
  "high_cost_causes": [
    {
      "cause": "data_growth",
      "detection": "Compare historical table sizes",
      "solution": "Implement data lifecycle management"
    },
    {
      "cause": "inefficient_queries",
      "detection": "Analyze query patterns and costs",
      "solution": "Query optimization and training"
    },
    {
      "cause": "missing_partitioning",
      "detection": "Check partition pruning effectiveness",
      "solution": "Implement table partitioning"
    }
  ]
}
```

### Cost Estimation Discrepancies

#### Dry-Run vs Actual Costs

```json
{
  "discrepancy_analysis": {
    "common_causes": [
      {
        "cause": "cached_results",
        "impact": "Actual cost may be $0 due to cache hits",
        "mitigation": "Use use_query_cache=false for accurate estimates"
      },
      {
        "cause": "data_updates",
        "impact": "Table size changed between dry-run and execution",
        "mitigation": "Run dry-run close to execution time"
      },
      {
        "cause": "dynamic_sql",
        "impact": "Parameter values affect data processing volume",
        "mitigation": "Test with representative parameter values"
      }
    ]
  }
}
```

## Integration with Cost Management

### CI/CD Cost Gates

```json
{
  "cicd_cost_integration": {
    "pre_deployment_checks": [
      {
        "check": "query_cost_validation",
        "threshold": 0.10,
        "action": "require_manual_approval_if_exceeded"
      },
      {
        "check": "cumulative_daily_cost_impact",
        "threshold": 10.00,
        "action": "block_deployment_if_exceeded"
      }
    ],
    "post_deployment_monitoring": [
      {
        "metric": "actual_vs_estimated_cost",
        "alert_threshold": "20% variance",
        "action": "investigate_and_report"
      }
    ]
  }
}
```

### Budget Management Integration

```json
{
  "budget_integration": {
    "monthly_budget_tracking": {
      "current_spending": "track_via_dry_run_estimates",
      "projected_spending": "extrapolate_from_current_trends",
      "budget_alerts": "warn_at_80%_notify_at_95%"
    },
    "cost_allocation": {
      "by_team": "tag_queries_with_team_identifiers",
      "by_project": "separate_tracking_per_project",
      "by_environment": "dev_staging_prod_cost_breakdown"
    }
  }
}
```

## Next Steps

Now that you understand cost estimation and optimization:

- **[Parameters Guide](parameters.md)** - Learn parameterized queries for dynamic cost analysis
- **[Validation Guide](validation.md)** - Ensure queries are valid before cost analysis
- **[Dry-Run Guide](dry-run.md)** - Deep dive into comprehensive query analysis

For implementation:
- **[API Reference](../api-reference/)** - Complete tool specifications
- **[Examples](../examples/)** - Cost optimization examples
- **[Development Guide](../development/)** - Integration patterns for cost controls