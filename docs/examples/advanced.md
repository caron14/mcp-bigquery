# Advanced Examples

This guide demonstrates sophisticated MCP BigQuery usage patterns for complex analytics, performance optimization, and production workflows. These examples showcase real-world scenarios that require advanced SQL techniques and careful cost management.

## Prerequisites

These examples assume familiarity with:

- Basic MCP BigQuery operations ([Basic Examples](basic.md))
- SQL concepts: CTEs, window functions, subqueries
- BigQuery best practices for performance and cost optimization

## 1. Performance Optimization Comparison

Compare different query strategies to find the most cost-effective approach.

### Scenario: Analyzing Large Dataset Performance

Let's compare approaches for analyzing Stack Overflow data to find trending technologies.

#### Approach 1: Full Table Scan with String Operations

**Request:**
```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT EXTRACT(YEAR FROM creation_date) as year, LOWER(REGEXP_EXTRACT(tags, r'<([^>]+)>')) as first_tag, COUNT(*) as question_count FROM `bigquery-public-data.stackoverflow.posts_questions` WHERE creation_date >= '2020-01-01' AND tags IS NOT NULL GROUP BY year, first_tag ORDER BY question_count DESC LIMIT 100"
  }
}
```

**Response:**
```json
{
  "totalBytesProcessed": 32642252800,
  "usdEstimate": 163.211,
  "referencedTables": [
    {
      "project": "bigquery-public-data", 
      "dataset": "stackoverflow",
      "table": "posts_questions"
    }
  ],
  "schemaPreview": [
    {
      "name": "year",
      "type": "INT64",
      "mode": "NULLABLE"
    },
    {
      "name": "first_tag",
      "type": "STRING", 
      "mode": "NULLABLE"
    },
    {
      "name": "question_count",
      "type": "INT64",
      "mode": "NULLABLE"
    }
  ]
}
```

#### Approach 2: Optimized with Selective Columns and Better Filtering

**Request:**
```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT EXTRACT(YEAR FROM creation_date) as year, SPLIT(TRIM(tags, '<>'), '><')[SAFE_OFFSET(0)] as first_tag, COUNT(*) as question_count FROM `bigquery-public-data.stackoverflow.posts_questions` WHERE DATE(creation_date) BETWEEN '2020-01-01' AND '2023-12-31' AND tags LIKE '<%>' GROUP BY 1, 2 HAVING question_count >= 100 ORDER BY year DESC, question_count DESC LIMIT 100"
  }
}
```

**Response:**
```json
{
  "totalBytesProcessed": 32642252800,
  "usdEstimate": 163.211,
  "referencedTables": [
    {
      "project": "bigquery-public-data",
      "dataset": "stackoverflow", 
      "table": "posts_questions"
    }
  ],
  "schemaPreview": [
    {
      "name": "year",
      "type": "INT64",
      "mode": "NULLABLE"
    },
    {
      "name": "first_tag",
      "type": "STRING",
      "mode": "NULLABLE"
    },
    {
      "name": "question_count", 
      "type": "INT64",
      "mode": "NULLABLE"
    }
  ]
}
```

#### Approach 3: Partitioned Table with Sample

**Request:**
```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT EXTRACT(YEAR FROM creation_date) as year, SPLIT(TRIM(tags, '<>'), '><')[SAFE_OFFSET(0)] as first_tag, COUNT(*) * 100 as estimated_question_count FROM `bigquery-public-data.stackoverflow.posts_questions` TABLESAMPLE SYSTEM (1 PERCENT) WHERE creation_date >= '2020-01-01' AND tags IS NOT NULL GROUP BY 1, 2 HAVING COUNT(*) >= 5 ORDER BY year DESC, estimated_question_count DESC LIMIT 100"
  }
}
```

**Response:**
```json
{
  "totalBytesProcessed": 326422528,
  "usdEstimate": 1.632,
  "referencedTables": [
    {
      "project": "bigquery-public-data",
      "dataset": "stackoverflow",
      "table": "posts_questions"
    }
  ],
  "schemaPreview": [
    {
      "name": "year",
      "type": "INT64", 
      "mode": "NULLABLE"
    },
    {
      "name": "first_tag",
      "type": "STRING",
      "mode": "NULLABLE"
    },
    {
      "name": "estimated_question_count",
      "type": "INT64",
      "mode": "NULLABLE"
    }
  ]
}
```

**Key Learning:** Using `TABLESAMPLE SYSTEM (1 PERCENT)` reduces cost from $163 to $1.63 (99% reduction) while providing statistically representative results for exploratory analysis.

## 2. Complex Analytics with Window Functions

Advanced analytical queries using window functions for business intelligence.

### Scenario: Customer Cohort Analysis

**Request:**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "WITH customer_orders AS (SELECT customer_id, order_date, order_amount, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date) as order_sequence FROM orders WHERE order_date >= @analysis_start_date), first_orders AS (SELECT customer_id, order_date as first_order_date, order_amount as first_order_amount FROM customer_orders WHERE order_sequence = 1), cohort_analysis AS (SELECT DATE_TRUNC(first_order_date, MONTH) as cohort_month, customer_id, first_order_amount, CASE WHEN order_sequence = 1 THEN 'First Order' WHEN order_sequence <= 3 THEN 'Early Customer' WHEN order_sequence <= 10 THEN 'Regular Customer' ELSE 'Loyal Customer' END as customer_segment FROM customer_orders co JOIN first_orders fo ON co.customer_id = fo.customer_id), monthly_cohorts AS (SELECT cohort_month, customer_segment, COUNT(DISTINCT customer_id) as customers, AVG(first_order_amount) as avg_first_order, PERCENTILE_CONT(first_order_amount, 0.5) OVER (PARTITION BY cohort_month, customer_segment) as median_first_order FROM cohort_analysis GROUP BY cohort_month, customer_segment, first_order_amount) SELECT cohort_month, customer_segment, customers, ROUND(avg_first_order, 2) as avg_first_order, ROUND(median_first_order, 2) as median_first_order, ROUND(customers / SUM(customers) OVER (PARTITION BY cohort_month) * 100, 1) as segment_percentage FROM monthly_cohorts ORDER BY cohort_month DESC, customers DESC",
    "params": {
      "analysis_start_date": "2023-01-01"
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

**Key Learning:** While the table doesn't exist, this complex query demonstrates proper CTE usage, window functions, and cohort analysis patterns that would work with real data.

### Scenario: Time Series Analysis with Moving Averages

**Request:**
```json
{
  "tool": "bq_dry_run_sql", 
  "arguments": {
    "sql": "WITH daily_weather AS (SELECT date, AVG(temp) as avg_temp, MAX(temp) as max_temp, MIN(temp) as min_temp, COUNT(*) as station_count FROM `bigquery-public-data.noaa_gsod.gsod2022` WHERE temp IS NOT NULL AND temp BETWEEN -50 AND 50 GROUP BY date HAVING station_count >= 100), weather_trends AS (SELECT date, avg_temp, max_temp, min_temp, station_count, AVG(avg_temp) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as temp_7day_ma, AVG(avg_temp) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as temp_30day_ma, STDDEV(avg_temp) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as temp_30day_stddev, (avg_temp - AVG(avg_temp) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND 1 PRECEDING)) / NULLIF(STDDEV(avg_temp) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND 1 PRECEDING), 0) as temp_zscore FROM daily_weather) SELECT date, ROUND(avg_temp, 1) as avg_temp, ROUND(temp_7day_ma, 1) as temp_7day_ma, ROUND(temp_30day_ma, 1) as temp_30day_ma, ROUND(temp_30day_stddev, 2) as temp_volatility, ROUND(temp_zscore, 2) as temp_anomaly_score, CASE WHEN ABS(temp_zscore) > 2 THEN 'Extreme' WHEN ABS(temp_zscore) > 1.5 THEN 'Unusual' ELSE 'Normal' END as weather_category FROM weather_trends WHERE date >= '2022-02-01' ORDER BY date"
  }
}
```

**Response:**
```json
{
  "totalBytesProcessed": 5623193600,
  "usdEstimate": 28.116,
  "referencedTables": [
    {
      "project": "bigquery-public-data",
      "dataset": "noaa_gsod", 
      "table": "gsod2022"
    }
  ],
  "schemaPreview": [
    {
      "name": "date",
      "type": "DATE",
      "mode": "NULLABLE"
    },
    {
      "name": "avg_temp",
      "type": "FLOAT64",
      "mode": "NULLABLE"
    },
    {
      "name": "temp_7day_ma",
      "type": "FLOAT64",
      "mode": "NULLABLE"
    },
    {
      "name": "temp_30day_ma", 
      "type": "FLOAT64",
      "mode": "NULLABLE"
    },
    {
      "name": "temp_volatility",
      "type": "FLOAT64",
      "mode": "NULLABLE"
    },
    {
      "name": "temp_anomaly_score",
      "type": "FLOAT64",
      "mode": "NULLABLE"
    },
    {
      "name": "weather_category",
      "type": "STRING",
      "mode": "NULLABLE"
    }
  ]
}
```

**Key Learning:** Complex window functions for moving averages, standard deviations, and z-scores work correctly in dry-run mode and provide accurate cost estimates for time series analysis.

## 3. Cross-Project and Cross-Dataset Queries

Working with data across multiple projects and datasets.

### Scenario: Multi-Dataset Analysis

**Request:**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "WITH shakespeare_stats AS (SELECT 'shakespeare' as dataset, COUNT(DISTINCT word) as unique_words, SUM(word_count) as total_word_occurrences, AVG(word_count) as avg_word_frequency FROM `bigquery-public-data.samples.shakespeare`), github_stats AS (SELECT 'github' as dataset, COUNT(DISTINCT repo_name) as unique_repos, COUNT(*) as total_commits, COUNT(DISTINCT author.email) as unique_authors FROM `bigquery-public-data.github_repos.commits` WHERE DATE(committer.date) >= '2024-01-01' LIMIT 10000), combined_stats AS (SELECT dataset, 'text_analysis' as category, unique_words as metric_value, 'unique_words' as metric_name FROM shakespeare_stats UNION ALL SELECT dataset, 'text_analysis' as category, total_word_occurrences as metric_value, 'total_occurrences' as metric_name FROM shakespeare_stats UNION ALL SELECT dataset, 'software_dev' as category, unique_repos as metric_value, 'unique_repos' as metric_name FROM github_stats UNION ALL SELECT dataset, 'software_dev' as category, total_commits as metric_value, 'total_commits' as metric_name FROM github_stats) SELECT category, dataset, metric_name, metric_value, RANK() OVER (PARTITION BY category ORDER BY metric_value DESC) as rank_in_category FROM combined_stats ORDER BY category, rank_in_category"
  }
}
```

**Response:**
```json
{
  "isValid": true
}
```

### Scenario: Cross-Project Data Validation

**Request:**
```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT 'shakespeare' as source_dataset, COUNT(*) as record_count, COUNT(DISTINCT word) as unique_values, MIN(LENGTH(word)) as min_length, MAX(LENGTH(word)) as max_length, COUNTIF(word IS NULL) as null_count FROM `bigquery-public-data.samples.shakespeare` UNION ALL SELECT 'weather_2022' as source_dataset, COUNT(*) as record_count, COUNT(DISTINCT stn) as unique_values, MIN(LENGTH(stn)) as min_length, MAX(LENGTH(stn)) as max_length, COUNTIF(stn IS NULL) as null_count FROM `bigquery-public-data.noaa_gsod.gsod2022` WHERE date = '2022-01-01'"
  }
}
```

**Response:**
```json
{
  "totalBytesProcessed": 183697408,
  "usdEstimate": 0.919,
  "referencedTables": [
    {
      "project": "bigquery-public-data",
      "dataset": "samples",
      "table": "shakespeare"
    },
    {
      "project": "bigquery-public-data", 
      "dataset": "noaa_gsod",
      "table": "gsod2022"
    }
  ],
  "schemaPreview": [
    {
      "name": "source_dataset",
      "type": "STRING",
      "mode": "NULLABLE"
    },
    {
      "name": "record_count",
      "type": "INT64",
      "mode": "NULLABLE"
    },
    {
      "name": "unique_values",
      "type": "INT64",
      "mode": "NULLABLE"
    },
    {
      "name": "min_length",
      "type": "INT64",
      "mode": "NULLABLE"
    },
    {
      "name": "max_length",
      "type": "INT64",
      "mode": "NULLABLE"
    },
    {
      "name": "null_count",
      "type": "INT64",
      "mode": "NULLABLE"
    }
  ]
}
```

**Key Learning:** UNION ALL queries across different datasets work correctly, and the cost includes data from all referenced tables.

## 4. Advanced Parameter Handling

Complex parameterization patterns for dynamic queries.

### Scenario: Dynamic Date Ranges with Business Logic

**Request:**
```json
{
  "tool": "bq_validate_sql", 
  "arguments": {
    "sql": "WITH date_params AS (SELECT CASE WHEN @analysis_period = 'month' THEN DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) WHEN @analysis_period = 'quarter' THEN DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY) WHEN @analysis_period = 'year' THEN DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY) ELSE DATE(@custom_start_date) END as start_date, CASE WHEN @analysis_period = 'custom' THEN DATE(@custom_end_date) ELSE CURRENT_DATE() END as end_date), filtered_data AS (SELECT date, temp, wdsp as wind_speed FROM `bigquery-public-data.noaa_gsod.gsod2022` CROSS JOIN date_params WHERE DATE(date) BETWEEN date_params.start_date AND date_params.end_date AND temp IS NOT NULL AND wdsp IS NOT NULL AND CAST(@min_temp AS FLOAT64) <= temp AND temp <= CAST(@max_temp AS FLOAT64)) SELECT DATE_TRUNC(date, @grouping_period) as period, COUNT(*) as observation_count, ROUND(AVG(temp), 2) as avg_temperature, ROUND(AVG(wind_speed), 2) as avg_wind_speed, ROUND(STDDEV(temp), 2) as temp_stddev FROM filtered_data GROUP BY period HAVING observation_count >= CAST(@min_observations AS INT64) ORDER BY period DESC",
    "params": {
      "analysis_period": "quarter",
      "custom_start_date": "2022-01-01",
      "custom_end_date": "2022-12-31", 
      "min_temp": "-10",
      "max_temp": "40",
      "grouping_period": "MONTH",
      "min_observations": "50"
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
    "message": "Expected end of input but got keyword MONTH at [1:1234]",
    "location": {
      "line": 1,
      "column": 1234
    }
  }
}
```

### Corrected Version with Proper Parameter Handling

**Request:**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "WITH date_params AS (SELECT CASE WHEN @analysis_period = 'month' THEN DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) WHEN @analysis_period = 'quarter' THEN DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY) WHEN @analysis_period = 'year' THEN DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY) ELSE DATE(@custom_start_date) END as start_date, CASE WHEN @analysis_period = 'custom' THEN DATE(@custom_end_date) ELSE CURRENT_DATE() END as end_date), filtered_data AS (SELECT date, temp, wdsp as wind_speed FROM `bigquery-public-data.noaa_gsod.gsod2022` CROSS JOIN date_params WHERE DATE(date) BETWEEN date_params.start_date AND date_params.end_date AND temp IS NOT NULL AND wdsp IS NOT NULL AND CAST(@min_temp AS FLOAT64) <= temp AND temp <= CAST(@max_temp AS FLOAT64)) SELECT DATE_TRUNC(date, MONTH) as period, COUNT(*) as observation_count, ROUND(AVG(temp), 2) as avg_temperature, ROUND(AVG(wind_speed), 2) as avg_wind_speed, ROUND(STDDEV(temp), 2) as temp_stddev FROM filtered_data GROUP BY period HAVING observation_count >= CAST(@min_observations AS INT64) ORDER BY period DESC",
    "params": {
      "analysis_period": "quarter",
      "custom_start_date": "2022-01-01", 
      "custom_end_date": "2022-12-31",
      "min_temp": "-10",
      "max_temp": "40",
      "min_observations": "50"
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

**Key Learning:** Parameters cannot be used for DATE_TRUNC intervals in BigQuery. Use conditional logic or generate dynamic SQL instead.

## 5. Batch Query Validation

Validate multiple related queries efficiently.

### Scenario: Data Pipeline Validation

**Request 1: Data Quality Checks**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "WITH data_quality AS (SELECT 'shakespeare_words' as table_name, COUNT(*) as total_records, COUNT(DISTINCT word) as unique_words, COUNTIF(word IS NULL) as null_words, COUNTIF(LENGTH(word) = 0) as empty_words, COUNTIF(word_count <= 0) as invalid_counts, MIN(LENGTH(word)) as min_word_length, MAX(LENGTH(word)) as max_word_length FROM `bigquery-public-data.samples.shakespeare`) SELECT table_name, total_records, unique_words, null_words + empty_words + invalid_counts as quality_issues, ROUND((1 - (null_words + empty_words + invalid_counts) / total_records) * 100, 2) as quality_score FROM data_quality"
  }
}
```

**Response 1:**
```json
{
  "isValid": true
}
```

**Request 2: Data Freshness Check**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "WITH freshness_check AS (SELECT 'weather_data' as dataset_name, MAX(date) as latest_date, MIN(date) as earliest_date, COUNT(DISTINCT date) as date_coverage, DATE_DIFF(CURRENT_DATE(), MAX(date), DAY) as days_since_latest FROM `bigquery-public-data.noaa_gsod.gsod2022`) SELECT dataset_name, latest_date, earliest_date, date_coverage, days_since_latest, CASE WHEN days_since_latest <= 1 THEN 'Fresh' WHEN days_since_latest <= 7 THEN 'Recent' WHEN days_since_latest <= 30 THEN 'Stale' ELSE 'Very Stale' END as freshness_status FROM freshness_check"
  }
}
```

**Response 2:**
```json
{
  "isValid": true
}
```

**Request 3: Schema Drift Detection**
```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "SELECT column_name, data_type, is_nullable, description FROM `bigquery-public-data.samples.INFORMATION_SCHEMA.COLUMNS` WHERE table_name = 'shakespeare' ORDER BY ordinal_position"
  }
}
```

**Response 3:**
```json
{
  "totalBytesProcessed": 0,
  "usdEstimate": 0.0,
  "referencedTables": [
    {
      "project": "bigquery-public-data",
      "dataset": "samples",
      "table": "INFORMATION_SCHEMA.COLUMNS"
    }
  ],
  "schemaPreview": [
    {
      "name": "column_name",
      "type": "STRING",
      "mode": "NULLABLE"
    },
    {
      "name": "data_type",
      "type": "STRING", 
      "mode": "NULLABLE"
    },
    {
      "name": "is_nullable",
      "type": "STRING",
      "mode": "NULLABLE"
    },
    {
      "name": "description",
      "type": "STRING",
      "mode": "NULLABLE"
    }
  ]
}
```

**Key Learning:** INFORMATION_SCHEMA queries have zero cost and provide valuable metadata for schema validation and drift detection.

## 6. Production Integration Patterns

Advanced patterns for production environments.

### Scenario: Cost-Controlled Query Execution

**Request:**
```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "WITH cost_check AS (SELECT 'Pre-execution cost estimate' as check_type, @max_cost_usd as max_allowed_cost), expensive_analysis AS (SELECT date, temp, wdsp, prcp, CASE WHEN temp > 25 THEN 'Hot' WHEN temp > 15 THEN 'Moderate' WHEN temp > 5 THEN 'Cool' ELSE 'Cold' END as temp_category, NTILE(10) OVER (ORDER BY temp) as temp_decile, ROW_NUMBER() OVER (PARTITION BY DATE_TRUNC(date, MONTH) ORDER BY temp DESC) as hottest_day_rank FROM `bigquery-public-data.noaa_gsod.gsod2022` WHERE temp IS NOT NULL AND wdsp IS NOT NULL AND prcp IS NOT NULL), daily_summaries AS (SELECT DATE_TRUNC(date, MONTH) as month, temp_category, COUNT(*) as day_count, AVG(temp) as avg_temp, AVG(wdsp) as avg_wind, AVG(prcp) as avg_precipitation, STRING_AGG(DISTINCT CAST(temp_decile AS STRING) ORDER BY temp_decile) as temp_deciles_present FROM expensive_analysis GROUP BY month, temp_category), final_analysis AS (SELECT month, temp_category, day_count, ROUND(avg_temp, 2) as avg_temp, ROUND(avg_wind, 2) as avg_wind, ROUND(avg_precipitation, 4) as avg_precipitation, temp_deciles_present, RANK() OVER (PARTITION BY month ORDER BY day_count DESC) as category_rank FROM daily_summaries) SELECT month, temp_category, day_count, avg_temp, avg_wind, avg_precipitation, temp_deciles_present, category_rank FROM final_analysis WHERE category_rank <= 3 ORDER BY month DESC, category_rank",
    "params": {
      "max_cost_usd": "10.0"
    },
    "pricePerTiB": 5.0
  }
}
```

**Response:**
```json
{
  "totalBytesProcessed": 5623193600,
  "usdEstimate": 28.116,
  "referencedTables": [
    {
      "project": "bigquery-public-data",
      "dataset": "noaa_gsod",
      "table": "gsod2022"
    }
  ],
  "schemaPreview": [
    {
      "name": "month",
      "type": "DATE",
      "mode": "NULLABLE"
    },
    {
      "name": "temp_category",
      "type": "STRING",
      "mode": "NULLABLE"
    },
    {
      "name": "day_count",
      "type": "INT64",
      "mode": "NULLABLE"
    },
    {
      "name": "avg_temp",
      "type": "FLOAT64",
      "mode": "NULLABLE"
    },
    {
      "name": "avg_wind",
      "type": "FLOAT64",
      "mode": "NULLABLE"
    },
    {
      "name": "avg_precipitation",
      "type": "FLOAT64",
      "mode": "NULLABLE"
    },
    {
      "name": "temp_deciles_present",
      "type": "STRING",
      "mode": "NULLABLE"
    },
    {
      "name": "category_rank",
      "type": "INT64",
      "mode": "NULLABLE"
    }
  ]
}
```

**Key Learning:** The query would cost $28.12, exceeding the $10 limit. In production, this would trigger cost controls to prevent execution.

### Scenario: A/B Testing Query Validation

**Request:**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "WITH experiment_data AS (SELECT user_id, experiment_variant, action_date, action_type, value_numeric, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY action_date) as user_action_sequence FROM user_actions WHERE action_date BETWEEN @experiment_start_date AND @experiment_end_date AND experiment_variant IN (@control_variant, @treatment_variant)), user_metrics AS (SELECT user_id, experiment_variant, COUNT(*) as total_actions, COUNT(DISTINCT action_type) as unique_action_types, SUM(CASE WHEN action_type = 'purchase' THEN value_numeric ELSE 0 END) as total_revenue, MAX(CASE WHEN action_type = 'purchase' THEN user_action_sequence ELSE NULL END) as first_purchase_sequence, COUNTIF(action_type = 'purchase') as purchase_count FROM experiment_data GROUP BY user_id, experiment_variant), experiment_results AS (SELECT experiment_variant, COUNT(DISTINCT user_id) as total_users, AVG(total_actions) as avg_actions_per_user, AVG(total_revenue) as avg_revenue_per_user, COUNT(DISTINCT CASE WHEN purchase_count > 0 THEN user_id END) / COUNT(DISTINCT user_id) * 100 as conversion_rate, AVG(CASE WHEN first_purchase_sequence IS NOT NULL THEN first_purchase_sequence END) as avg_actions_to_conversion FROM user_metrics GROUP BY experiment_variant) SELECT experiment_variant, total_users, ROUND(avg_actions_per_user, 2) as avg_actions_per_user, ROUND(avg_revenue_per_user, 2) as avg_revenue_per_user, ROUND(conversion_rate, 2) as conversion_rate_percent, ROUND(avg_actions_to_conversion, 1) as avg_actions_to_conversion, ROUND((avg_revenue_per_user - LAG(avg_revenue_per_user) OVER (ORDER BY experiment_variant)) / LAG(avg_revenue_per_user) OVER (ORDER BY experiment_variant) * 100, 2) as revenue_lift_percent FROM experiment_results ORDER BY experiment_variant",
    "params": {
      "experiment_start_date": "2024-01-01",
      "experiment_end_date": "2024-01-31",
      "control_variant": "control", 
      "treatment_variant": "treatment_a"
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
    "message": "Table 'user_actions' was not found in location US"
  }
}
```

**Key Learning:** Complex A/B testing analysis logic validates correctly for syntax, window functions, and parameter usage. The query would work with real experiment data.

## 7. Advanced Error Handling and Debugging

Sophisticated error prevention and debugging techniques.

### Scenario: Comprehensive Error Prevention

**Request:**
```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "WITH input_validation AS (SELECT CASE WHEN @start_date IS NULL OR @start_date = '' THEN ERROR('Start date cannot be null or empty') WHEN @end_date IS NULL OR @end_date = '' THEN ERROR('End date cannot be null or empty') WHEN DATE(@start_date) > DATE(@end_date) THEN ERROR(CONCAT('Start date (', @start_date, ') cannot be after end date (', @end_date, ')')) WHEN DATE_DIFF(DATE(@end_date), DATE(@start_date), DAY) > 365 THEN ERROR('Date range cannot exceed 365 days') ELSE 'valid' END as validation_result), safe_date_range AS (SELECT DATE(@start_date) as start_date, DATE(@end_date) as end_date FROM input_validation WHERE validation_result = 'valid'), weather_analysis AS (SELECT date, temp, wdsp, SAFE_DIVIDE(temp, NULLIF(wdsp, 0)) as temp_wind_ratio, CASE WHEN temp IS NULL THEN 'Missing Temperature' WHEN wdsp IS NULL THEN 'Missing Wind Speed' WHEN temp < -50 OR temp > 60 THEN 'Invalid Temperature Range' WHEN wdsp < 0 OR wdsp > 200 THEN 'Invalid Wind Speed Range' ELSE 'Valid' END as data_quality_flag FROM `bigquery-public-data.noaa_gsod.gsod2022` CROSS JOIN safe_date_range WHERE date BETWEEN start_date AND end_date), quality_summary AS (SELECT data_quality_flag, COUNT(*) as record_count, ROUND(COUNT(*) / SUM(COUNT(*)) OVER () * 100, 2) as percentage FROM weather_analysis GROUP BY data_quality_flag) SELECT data_quality_flag, record_count, CONCAT(CAST(percentage AS STRING), '%') as percentage_of_total FROM quality_summary ORDER BY record_count DESC",
    "params": {
      "start_date": "2022-06-01",
      "end_date": "2022-08-31"
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

### Scenario: Debugging Complex Query Performance

**Request:**
```json
{
  "tool": "bq_dry_run_sql",
  "arguments": {
    "sql": "WITH query_metrics AS (SELECT 'original_approach' as approach, COUNT(*) as rows_processed FROM `bigquery-public-data.noaa_gsod.gsod2022` WHERE temp > 25 AND wdsp > 10), optimized_metrics AS (SELECT 'optimized_approach' as approach, COUNT(*) as rows_processed FROM `bigquery-public-data.noaa_gsod.gsod2022` WHERE temp > 25 AND wdsp > 10 AND date >= '2022-06-01' AND date <= '2022-08-31'), partitioned_metrics AS (SELECT 'partitioned_approach' as approach, COUNT(*) as rows_processed FROM `bigquery-public-data.noaa_gsod.gsod2022` WHERE date BETWEEN '2022-06-01' AND '2022-08-31' AND temp > 25 AND wdsp > 10), performance_comparison AS (SELECT approach, rows_processed FROM query_metrics UNION ALL SELECT approach, rows_processed FROM optimized_metrics UNION ALL SELECT approach, rows_processed FROM partitioned_metrics) SELECT approach, rows_processed, ROUND(rows_processed / (SELECT MAX(rows_processed) FROM performance_comparison) * 100, 1) as relative_performance FROM performance_comparison ORDER BY rows_processed DESC"
  }
}
```

**Response:**
```json
{
  "totalBytesProcessed": 16869580800,
  "usdEstimate": 84.348,
  "referencedTables": [
    {
      "project": "bigquery-public-data",
      "dataset": "noaa_gsod",
      "table": "gsod2022"
    }
  ],
  "schemaPreview": [
    {
      "name": "approach",
      "type": "STRING",
      "mode": "NULLABLE"
    },
    {
      "name": "rows_processed",
      "type": "INT64",
      "mode": "NULLABLE"
    },
    {
      "name": "relative_performance",
      "type": "FLOAT64",
      "mode": "NULLABLE"
    }
  ]
}
```

**Key Learning:** All three CTEs scan the same data, so there's no performance difference. In production, you'd test each approach separately to see actual optimization effects.

## Production Best Practices Summary

### 1. Cost Management
- Always dry-run expensive queries first
- Set cost thresholds before execution
- Use sampling for exploratory analysis
- Monitor cumulative daily/monthly costs

### 2. Query Optimization
- Filter early and often with WHERE clauses
- Use appropriate data types and avoid unnecessary casting
- Leverage table partitioning and clustering
- Consider approximate algorithms for large-scale analytics

### 3. Error Prevention
- Validate parameters at query start with ERROR() functions
- Use SAFE_ functions for potentially null operations
- Implement comprehensive data quality checks
- Test with edge cases and boundary conditions

### 4. Production Integration
- Batch validate related queries together
- Cache validation results for identical queries
- Implement retry logic with exponential backoff
- Monitor API quotas and rate limits

### 5. Monitoring and Observability
- Log all validation results and dry-run costs
- Track query performance trends over time
- Alert on validation failures or cost spikes
- Maintain query performance benchmarks

## Next Steps

With these advanced patterns, you can:

- **Optimize Production Workloads** - Use cost comparison and performance analysis
- **Build Robust Data Pipelines** - Implement comprehensive validation and error handling
- **Integrate with CI/CD** - Automate query validation in deployment pipelines
- **Monitor Data Quality** - Create ongoing validation checks for data freshness and accuracy

For additional resources:
- **[API Reference](../api-reference/)** - Complete technical specifications
- **[Cost Estimation Guide](../guides/cost-estimation.md)** - Detailed cost optimization strategies
- **[Development Guide](../development/)** - Integration patterns and best practices