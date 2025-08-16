# API Reference

The MCP BigQuery server provides two main tools for validating and analyzing BigQuery SQL queries without executing them. All operations are performed as dry-runs, ensuring no data is processed or costs incurred.

## Overview

The MCP BigQuery server implements the Model Context Protocol (MCP) and exposes the following tools:

- **[bq_validate_sql](./tools.md#bq_validate_sql)** - Validate BigQuery SQL syntax
- **[bq_dry_run_sql](./tools.md#bq_dry_run_sql)** - Perform dry-run analysis with cost estimation

## Server Information

- **Server Name**: `mcp-bigquery`
- **Protocol**: Model Context Protocol (MCP)
- **Transport**: stdio
- **Authentication**: Google Cloud Application Default Credentials (ADC)

## Tool Execution Flow

1. **Tool Discovery**: Client calls `list_tools()` to discover available tools
2. **Tool Invocation**: Client calls `call_tool()` with tool name and arguments
3. **Response**: Server returns structured JSON response with results or errors

## Common Response Format

All tools return responses in JSON format with the following structure:

### Success Response
```json
{
  // Tool-specific success fields
}
```

### Error Response
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "location": {  // Optional, for syntax errors
      "line": 3,
      "column": 15
    },
    "details": [   // Optional, additional BigQuery error details
      // BigQuery error objects
    ]
  }
}
```

## Authentication

The server requires Google Cloud authentication through Application Default Credentials (ADC). Set up authentication using:

```bash
gcloud auth application-default login
```

Or set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point to a service account key file.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BQ_PROJECT` | Google Cloud project ID | From ADC |
| `BQ_LOCATION` | BigQuery default location | None |
| `SAFE_PRICE_PER_TIB` | Price per TiB for cost estimation | 5.0 |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account key | None |

## Rate Limits and Quotas

The server uses BigQuery's dry-run API, which has the following characteristics:

- **No data processing costs** - Dry-runs are free
- **Standard API rate limits** - Subject to BigQuery API quotas
- **Authentication required** - Must have BigQuery permissions

## Error Handling

All errors are returned in a structured format with standardized error codes. See the [Error Reference](./errors.md) for complete error code documentation.

## Schema Definitions

Complete JSON schema definitions for all request and response formats are available in the [Schema Reference](./schemas.md).

## Next Steps

- [Tool Specifications](./tools.md) - Detailed tool documentation
- [Response Schemas](./schemas.md) - Complete schema definitions  
- [Error Reference](./errors.md) - Error codes and troubleshooting