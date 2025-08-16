# Examples

This section provides practical, real-world examples of using MCP BigQuery for SQL validation and cost analysis. All examples include complete JSON request/response pairs that you can copy and adapt for your own use cases.

## Quick Navigation

### [Basic Examples](basic.md)
Essential patterns for getting started with MCP BigQuery:

- **Simple validation** - Check basic SQL syntax
- **Cost estimation** - Analyze query costs with public datasets  
- **Error handling** - Understanding and fixing common SQL errors
- **Parameter usage** - Working with parameterized queries
- **Schema preview** - Exploring result structures before execution

### [Advanced Examples](advanced.md)
Complex scenarios and optimization patterns:

- **Performance optimization** - Comparing query strategies for cost reduction
- **Complex analytics** - Window functions, CTEs, and advanced SQL patterns
- **Cross-project queries** - Working with multiple GCP projects and datasets
- **Batch operations** - Validating multiple queries efficiently
- **Production workflows** - Integration patterns for CI/CD and automated validation

## Example Categories

### By Use Case
- **Data Exploration** - Discovering and analyzing new datasets
- **Cost Optimization** - Reducing BigQuery charges through better query design
- **Quality Assurance** - Validating SQL before production deployment
- **Schema Migration** - Testing queries against evolving table structures
- **Compliance Checking** - Ensuring queries meet organizational standards

### By Query Type
- **Simple SELECT** - Basic data retrieval patterns
- **Aggregation Queries** - GROUP BY, HAVING, and statistical functions
- **JOIN Operations** - Inner, outer, and complex multi-table joins
- **Analytical Functions** - Window functions and ranking queries
- **Data Transformation** - ETL patterns and data cleaning operations

### By Dataset
- **Public Datasets** - Examples using `bigquery-public-data`
- **E-commerce Analytics** - Order processing and customer analysis
- **Financial Data** - Transaction analysis and reporting
- **IoT and Time Series** - Sensor data and temporal analysis
- **User Behavior** - Web analytics and engagement metrics

## Common Patterns Reference

### Request Structure
All MCP BigQuery tools follow this pattern:

```json
{
  "tool": "bq_validate_sql" | "bq_dry_run_sql",
  "arguments": {
    "sql": "YOUR_SQL_QUERY",
    "params": {
      "parameter_name": "parameter_value"
    },
    "pricePerTiB": 5.0  // Only for dry_run_sql
  }
}
```

### Response Types

#### Validation Success
```json
{
  "isValid": true
}
```

#### Validation Error
```json
{
  "isValid": false,
  "error": {
    "code": "INVALID_SQL",
    "message": "Error description",
    "location": {
      "line": 1,
      "column": 15
    }
  }
}
```

#### Dry-Run Success
```json
{
  "totalBytesProcessed": 1048576,
  "usdEstimate": 0.005,
  "referencedTables": [
    {
      "project": "project-id",
      "dataset": "dataset_name", 
      "table": "table_name"
    }
  ],
  "schemaPreview": [
    {
      "name": "column_name",
      "type": "STRING",
      "mode": "NULLABLE"
    }
  ]
}
```

## Public Datasets for Testing

The examples use these publicly available datasets that require no setup:

### Shakespeare Dataset
- **Table**: `bigquery-public-data.samples.shakespeare`
- **Use case**: Text analysis and word counting
- **Size**: ~164 KB (very low cost)
- **Schema**: `word` (STRING), `word_count` (INT64), `corpus` (STRING), `corpus_date` (INT64)

### GitHub Archive
- **Table**: `bigquery-public-data.github_repos.commits`
- **Use case**: Software development analytics
- **Size**: ~500 GB (high cost - use with LIMIT)
- **Schema**: Commit metadata, author info, repository details

### New York Taxi Data
- **Table**: `bigquery-public-data.new_york_taxi_trips.tlc_yellow_trips_2022`
- **Use case**: Transportation and geospatial analysis
- **Size**: ~50 GB per year (medium cost)
- **Schema**: Trip details, locations, fares, timestamps

### Stack Overflow Survey
- **Table**: `bigquery-public-data.stackoverflow.posts_questions`
- **Use case**: Developer survey and trend analysis
- **Size**: ~10 GB (medium cost)
- **Schema**: Question metadata, tags, scores, view counts

### Weather Data
- **Table**: `bigquery-public-data.noaa_gsod.gsod2022`
- **Use case**: Climate and weather analysis
- **Size**: ~100 MB per year (low cost)
- **Schema**: Temperature, precipitation, weather station data

## Best Practices

### Development Workflow
1. **Start Small** - Begin with basic validation examples
2. **Test Parameters** - Verify parameterized queries work as expected
3. **Check Costs** - Always estimate expenses before running large queries
4. **Validate Dependencies** - Ensure referenced tables and columns exist
5. **Handle Errors** - Implement proper error handling and user feedback

### Query Optimization
1. **Filter Early** - Apply WHERE clauses to reduce data scanned
2. **Select Specific Columns** - Avoid SELECT * on large tables
3. **Use Partitioning** - Leverage table partitions for date-based filtering
4. **Optimize JOINs** - Choose appropriate JOIN types and conditions
5. **Test with LIMIT** - Use LIMIT for development, but remember it doesn't reduce costs

### Production Integration
1. **Validate Before Execution** - Always check syntax first
2. **Set Cost Thresholds** - Prevent expensive queries from running automatically
3. **Monitor Usage** - Track validation API calls and quotas
4. **Cache Results** - Store validation results for identical queries
5. **Log Errors** - Capture and analyze validation failures

## Getting Help

If you encounter issues while following these examples:

1. **Check Authentication** - Ensure `gcloud auth application-default login` is completed
2. **Verify Permissions** - Confirm BigQuery Job User role is assigned
3. **Review Error Messages** - Use the `location` field to identify syntax issues
4. **Start Simple** - Test with basic queries before complex operations
5. **Consult Documentation** - See [API Reference](../api-reference/) for detailed specifications

## Contributing Examples

Have a useful example to share? Examples should include:

- **Clear Use Case** - Explain the business problem being solved
- **Complete Code** - Include full JSON request/response pairs
- **Real Data** - Use public datasets when possible
- **Cost Information** - Document expected bytes processed and costs
- **Error Scenarios** - Show common mistakes and solutions
- **Progressive Complexity** - Build from simple to advanced concepts

For more information, see the [Development Guide](../development/) for contribution guidelines.