# Error Reference

This document provides comprehensive documentation for all error codes and error handling patterns used by the MCP BigQuery server.

## Error Response Format

All errors follow a consistent response format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "location": {          // Optional - for syntax errors
      "line": 3,
      "column": 15
    },
    "details": [           // Optional - additional BigQuery errors
      {
        "reason": "invalidQuery",
        "location": "query", 
        "message": "Detailed error information"
      }
    ]
  }
}
```

For `bq_validate_sql`, error responses also include:
```json
{
  "isValid": false,
  "error": { /* error object */ }
}
```

## Error Codes

### INVALID_SQL

**Description**: The SQL query contains syntax errors, references invalid objects, or has parameter issues.

**Common Causes**:
- SQL syntax errors
- Invalid table/dataset references  
- Missing or invalid query parameters
- Permission denied on referenced objects
- Invalid function usage

**Examples**:

#### Syntax Error
```json
{
  "error": {
    "code": "INVALID_SQL", 
    "message": "Syntax error: Expected keyword SELECT but got identifier 'SELCT' at [1:1]",
    "location": {
      "line": 1,
      "column": 1
    }
  }
}
```

#### Missing Table
```json
{
  "error": {
    "code": "INVALID_SQL",
    "message": "Not found: Table my-project:my_dataset.nonexistent_table was not found in location US",
    "details": [
      {
        "reason": "notFound",
        "location": "query",
        "message": "Table 'my-project:my_dataset.nonexistent_table' was not found"
      }
    ]
  }
}
```

#### Parameter Error
```json
{
  "error": {
    "code": "INVALID_SQL",
    "message": "Query parameter '@missing_param' not found",
    "details": [
      {
        "reason": "invalidQuery",
        "message": "Parameter '@missing_param' is not defined"
      }
    ]
  }
}
```

**Solutions**:
- Check SQL syntax for typos and structure
- Verify table and dataset names exist and are accessible
- Ensure all query parameters are provided
- Check permissions on referenced BigQuery resources
- Validate function names and usage

### AUTHENTICATION_ERROR

**Description**: Google Cloud authentication failed or credentials are missing.

**Common Causes**:
- No Application Default Credentials (ADC) configured
- Expired authentication tokens
- Invalid service account key
- Missing required IAM permissions

**Example**:
```json
{
  "error": {
    "code": "AUTHENTICATION_ERROR",
    "message": "No BigQuery credentials found. Please set up Application Default Credentials or provide a service account key. Run 'gcloud auth application-default login' for local development."
  }
}
```

**Solutions**:
1. **For local development**:
   ```bash
   gcloud auth application-default login
   ```

2. **For service accounts**:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
   ```

3. **For Cloud environments**:
   - Ensure service account is attached to compute instance
   - Verify IAM roles include BigQuery permissions

4. **Required IAM permissions**:
   - `bigquery.jobs.create` (for dry-run queries)
   - `bigquery.datasets.get` (for dataset access)
   - `bigquery.tables.get` (for table access)

### UNKNOWN_ERROR

**Description**: An unexpected error occurred that doesn't fall into other categories.

**Common Causes**:
- Network connectivity issues
- BigQuery service outages
- Unexpected API responses
- Internal server errors

**Example**:
```json
{
  "error": {
    "code": "UNKNOWN_ERROR",
    "message": "An unexpected error occurred: Connection timeout"
  }
}
```

**Solutions**:
- Check network connectivity
- Verify BigQuery service status
- Retry the request after a brief delay
- Check server logs for additional details
- Contact support if the issue persists

## BigQuery-Specific Error Details

When available, the `details` array contains additional error information from the BigQuery API:

### Common BigQuery Error Reasons

| Reason | Description | Common Causes |
|--------|-------------|---------------|
| `invalidQuery` | SQL syntax or semantic error | Typos, invalid syntax, wrong function usage |
| `notFound` | Referenced object not found | Missing tables, datasets, or projects |
| `accessDenied` | Insufficient permissions | Missing IAM roles or dataset permissions |
| `quotaExceeded` | API quota limit reached | Too many requests, rate limiting |
| `invalidInput` | Invalid parameter values | Wrong data types, out of range values |
| `resourceInUse` | Resource is currently locked | Concurrent operations on same resource |

### Error Location Information

For syntax errors, the `location` object provides precise error positioning:

```json
{
  "location": {
    "line": 3,      // 1-based line number
    "column": 15    // 1-based column number  
  }
}
```

**Location Extraction Pattern**: `\[(\d+):(\d+)\]` in error messages

**Example**: "Syntax error at [3:15]" → `{"line": 3, "column": 15}`

## Error Handling Best Practices

### Client-Side Error Handling

```python
def handle_mcp_response(response):
    """Example error handling for MCP BigQuery responses."""
    
    # Parse JSON response
    data = json.loads(response)
    
    # Check for validation tool response
    if "isValid" in data:
        if not data["isValid"]:
            error = data["error"]
            handle_validation_error(error)
        else:
            print("SQL is valid")
    
    # Check for dry-run tool response  
    elif "totalBytesProcessed" in data:
        handle_dry_run_success(data)
    
    # Check for error-only response
    elif "error" in data:
        handle_dry_run_error(data["error"])

def handle_validation_error(error):
    """Handle validation errors with location info."""
    print(f"Validation failed: {error['message']}")
    
    if "location" in error:
        loc = error["location"]
        print(f"Error at line {loc['line']}, column {loc['column']}")
    
    if "details" in error:
        for detail in error["details"]:
            print(f"Detail: {detail.get('message', 'No message')}")

def handle_authentication_error(error):
    """Handle authentication errors with setup guidance.""" 
    print("Authentication failed!")
    print("Setup steps:")
    print("1. Run: gcloud auth application-default login")
    print("2. Or set GOOGLE_APPLICATION_CREDENTIALS environment variable")
    print("3. Ensure BigQuery API is enabled in your project")
```

### Retry Logic

```python
import time
import random

def retry_with_backoff(func, max_retries=3):
    """Retry function with exponential backoff."""
    
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            error_data = json.loads(str(e))
            error_code = error_data.get("error", {}).get("code")
            
            # Don't retry authentication or syntax errors
            if error_code in ["AUTHENTICATION_ERROR", "INVALID_SQL"]:
                raise
            
            if attempt == max_retries - 1:
                raise
            
            # Exponential backoff with jitter
            delay = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(delay)
```

### Error Recovery Strategies

| Error Type | Recovery Strategy |
|------------|------------------|
| `INVALID_SQL` | Fix query syntax, verify table names |
| `AUTHENTICATION_ERROR` | Re-authenticate, check credentials |
| `UNKNOWN_ERROR` | Retry with backoff, check connectivity |
| Quota exceeded | Implement rate limiting, retry later |
| Network timeout | Retry with exponential backoff |

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. "No credentials found" Error

**Problem**: Authentication error when calling tools

**Solution**:
```bash
# Check current authentication
gcloud auth list

# Login if needed  
gcloud auth application-default login

# Verify project is set
gcloud config get-value project

# Set project if needed
gcloud config set project YOUR_PROJECT_ID
```

#### 2. "Table not found" Error

**Problem**: Query references non-existent table

**Diagnostic Questions**:
- Does the table exist in BigQuery console?
- Is the project ID correct?
- Do you have permission to access the dataset?
- Is the table in the correct location/region?

**Solution**:
```sql
-- Verify table exists
SELECT * FROM `project.dataset.table` LIMIT 1;

-- Check dataset location
SELECT * FROM `project.dataset.INFORMATION_SCHEMA.TABLES` 
WHERE table_name = 'your_table';
```

#### 3. Syntax Error with Location

**Problem**: SQL syntax error at specific location

**Debugging Steps**:
1. Check the exact line and column indicated
2. Look for common issues:
   - Missing commas
   - Unmatched parentheses  
   - Reserved keyword usage
   - Invalid function names

**Example Fix**:
```sql
-- Error: SELECT FROM table (missing column list)
SELECT FROM my_table;

-- Fix: Add column list or wildcard
SELECT * FROM my_table;
```

#### 4. Parameter Type Issues  

**Problem**: Query parameters not working as expected

**Cause**: All parameters are treated as STRING type

**Solution**: Use explicit casting in SQL
```sql
-- Instead of: WHERE age > @age_param
-- Use: WHERE age > CAST(@age_param AS INT64)

-- Parameter dates
WHERE date_col = PARSE_DATE('%Y-%m-%d', @date_param)

-- Parameter timestamps  
WHERE timestamp_col > PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', @ts_param)
```

#### 5. Cost Estimation Issues

**Problem**: Unexpected cost estimates

**Debugging**:
- Check `totalBytesProcessed` value
- Verify `pricePerTiB` parameter or environment variable
- Calculate manually: `(bytes / 2^40) * price`

**Example**:
```json
{
  "totalBytesProcessed": 1048576,  // 1 MB
  "pricePerTiB": 5.0,              // $5 per TiB
  "usdEstimate": 0.000005          // (1048576 / 2^40) * 5.0
}
```

## Error Response Examples

### Complete Error Scenarios

#### Invalid Query with Location
```json
{
  "isValid": false,
  "error": {
    "code": "INVALID_SQL",
    "message": "Syntax error: Expected keyword FROM but got keyword WHERE at [2:5]",
    "location": {
      "line": 2,
      "column": 5
    },
    "details": [
      {
        "reason": "invalidQuery",
        "location": "query",
        "message": "Syntax error: Expected keyword FROM but got keyword WHERE"
      }
    ]
  }
}
```

#### Permission Denied
```json
{
  "error": {
    "code": "INVALID_SQL", 
    "message": "Access Denied: Dataset my-project:restricted_dataset: User does not have permission to query dataset my-project:restricted_dataset",
    "details": [
      {
        "reason": "accessDenied",
        "location": "query",
        "message": "Access Denied: Dataset my-project:restricted_dataset"
      }
    ]
  }
}
```

#### Network/Service Error
```json
{
  "error": {
    "code": "UNKNOWN_ERROR",
    "message": "Service temporarily unavailable. Please try again later."
  }
}
```

## Support and Reporting

If you encounter errors not covered in this documentation:

1. **Check server logs** for additional error details
2. **Verify BigQuery service status** at Google Cloud Status page  
3. **Test with BigQuery console** to isolate API vs. query issues
4. **Capture full error response** including details array
5. **Report issues** with complete error information and reproduction steps