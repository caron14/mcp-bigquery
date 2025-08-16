# Schema Reference

This document provides complete JSON schema definitions for all request and response formats used by the MCP BigQuery server.

## Tool Input Schemas

### bq_validate_sql Input Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "sql": {
      "type": "string",
      "description": "The SQL query to validate",
      "minLength": 1,
      "maxLength": 1048576
    },
    "params": {
      "type": "object",
      "description": "Optional query parameters (key-value pairs)",
      "additionalProperties": {
        "type": ["string", "number", "boolean", "null"]
      },
      "maxProperties": 100
    }
  },
  "required": ["sql"],
  "additionalProperties": false
}
```

### bq_dry_run_sql Input Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object", 
  "properties": {
    "sql": {
      "type": "string",
      "description": "The SQL query to dry-run",
      "minLength": 1,
      "maxLength": 1048576
    },
    "params": {
      "type": "object",
      "description": "Optional query parameters (key-value pairs)",
      "additionalProperties": {
        "type": ["string", "number", "boolean", "null"]
      },
      "maxProperties": 100
    },
    "pricePerTiB": {
      "type": "number",
      "description": "Price per TiB for cost estimation (defaults to env var or 5.0)",
      "minimum": 0,
      "maximum": 1000
    }
  },
  "required": ["sql"],
  "additionalProperties": false
}
```

## Response Schemas

### bq_validate_sql Response Schema

#### Success Response Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "isValid": {
      "type": "boolean",
      "const": true,
      "description": "Indicates the SQL query is valid"
    }
  },
  "required": ["isValid"],
  "additionalProperties": false
}
```

#### Error Response Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "isValid": {
      "type": "boolean", 
      "const": false,
      "description": "Indicates the SQL query is invalid"
    },
    "error": {
      "$ref": "#/$defs/ErrorObject"
    }
  },
  "required": ["isValid", "error"],
  "additionalProperties": false,
  "$defs": {
    "ErrorObject": {
      "type": "object",
      "properties": {
        "code": {
          "type": "string",
          "enum": ["INVALID_SQL", "UNKNOWN_ERROR", "AUTHENTICATION_ERROR"],
          "description": "Error code identifying the type of error"
        },
        "message": {
          "type": "string",
          "description": "Human-readable error message"
        },
        "location": {
          "type": "object",
          "properties": {
            "line": {
              "type": "integer",
              "minimum": 1,
              "description": "Line number where the error occurred"
            },
            "column": {
              "type": "integer", 
              "minimum": 1,
              "description": "Column number where the error occurred"
            }
          },
          "required": ["line", "column"],
          "additionalProperties": false,
          "description": "Optional location information for syntax errors"
        },
        "details": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/BigQueryError"
          },
          "description": "Additional error details from BigQuery API"
        }
      },
      "required": ["code", "message"],
      "additionalProperties": false
    },
    "BigQueryError": {
      "type": "object",
      "properties": {
        "reason": {
          "type": "string",
          "description": "BigQuery error reason code"
        },
        "location": {
          "type": "string", 
          "description": "Location context for the error"
        },
        "message": {
          "type": "string",
          "description": "Detailed error message from BigQuery"
        }
      },
      "additionalProperties": true
    }
  }
}
```

### bq_dry_run_sql Response Schema

#### Success Response Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "totalBytesProcessed": {
      "type": "integer",
      "minimum": 0,
      "description": "Total number of bytes the query would process"
    },
    "usdEstimate": {
      "type": "number",
      "minimum": 0,
      "multipleOf": 0.000001,
      "description": "Estimated cost in USD, rounded to 6 decimal places"
    },
    "referencedTables": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/TableReference"
      },
      "description": "List of tables referenced by the query"
    },
    "schemaPreview": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/SchemaField"
      },
      "description": "Schema of the query result"
    }
  },
  "required": ["totalBytesProcessed", "usdEstimate", "referencedTables", "schemaPreview"],
  "additionalProperties": false,
  "$defs": {
    "TableReference": {
      "type": "object",
      "properties": {
        "project": {
          "type": "string",
          "pattern": "^[a-z0-9][a-z0-9\\-]{4,28}[a-z0-9]$",
          "description": "Google Cloud project ID"
        },
        "dataset": {
          "type": "string", 
          "pattern": "^[a-zA-Z0-9_]+$",
          "maxLength": 1024,
          "description": "BigQuery dataset ID"
        },
        "table": {
          "type": "string",
          "pattern": "^[a-zA-Z0-9_]+$", 
          "maxLength": 1024,
          "description": "BigQuery table ID"
        }
      },
      "required": ["project", "dataset", "table"],
      "additionalProperties": false
    },
    "SchemaField": {
      "type": "object",
      "properties": {
        "name": {
          "type": "string",
          "pattern": "^[a-zA-Z_][a-zA-Z0-9_]*$",
          "maxLength": 300,
          "description": "Field name"
        },
        "type": {
          "type": "string",
          "enum": [
            "STRING", "BYTES", "INTEGER", "FLOAT", "NUMERIC", "BIGNUMERIC",
            "BOOLEAN", "TIMESTAMP", "DATE", "TIME", "DATETIME", "INTERVAL",
            "RECORD", "GEOGRAPHY", "JSON"
          ],
          "description": "BigQuery field type"
        },
        "mode": {
          "type": "string",
          "enum": ["NULLABLE", "REQUIRED", "REPEATED"],
          "description": "Field mode"
        }
      },
      "required": ["name", "type", "mode"],
      "additionalProperties": false
    }
  }
}
```

#### Error Response Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "error": {
      "$ref": "#/$defs/ErrorObject"
    }
  },
  "required": ["error"],
  "additionalProperties": false,
  "$defs": {
    "ErrorObject": {
      "type": "object",
      "properties": {
        "code": {
          "type": "string",
          "enum": ["INVALID_SQL", "UNKNOWN_ERROR", "AUTHENTICATION_ERROR"],
          "description": "Error code identifying the type of error"
        },
        "message": {
          "type": "string",
          "description": "Human-readable error message"
        },
        "location": {
          "type": "object",
          "properties": {
            "line": {
              "type": "integer",
              "minimum": 1,
              "description": "Line number where the error occurred"
            },
            "column": {
              "type": "integer",
              "minimum": 1, 
              "description": "Column number where the error occurred"
            }
          },
          "required": ["line", "column"],
          "additionalProperties": false,
          "description": "Optional location information for syntax errors"
        },
        "details": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/BigQueryError"
          },
          "description": "Additional error details from BigQuery API"
        }
      },
      "required": ["code", "message"],
      "additionalProperties": false
    },
    "BigQueryError": {
      "type": "object",
      "properties": {
        "reason": {
          "type": "string",
          "description": "BigQuery error reason code"
        },
        "location": {
          "type": "string",
          "description": "Location context for the error"
        },
        "message": {
          "type": "string",
          "description": "Detailed error message from BigQuery"
        }
      },
      "additionalProperties": true
    }
  }
}
```

## MCP Protocol Schemas

### Tool Definition Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "enum": ["bq_validate_sql", "bq_dry_run_sql"],
      "description": "Tool identifier"
    },
    "description": {
      "type": "string",
      "description": "Human-readable tool description"
    },
    "inputSchema": {
      "type": "object",
      "description": "JSON schema for tool input validation"
    }
  },
  "required": ["name", "description", "inputSchema"],
  "additionalProperties": false
}
```

### MCP Response Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "type": {
        "type": "string",
        "const": "text",
        "description": "Content type indicator"
      },
      "text": {
        "type": "string",
        "description": "JSON-formatted tool response"
      }
    },
    "required": ["type", "text"],
    "additionalProperties": false
  },
  "minItems": 1,
  "maxItems": 1
}
```

## Data Type Definitions

### BigQuery Data Types

The following BigQuery data types may appear in `schemaPreview` responses:

| Type | Description | JSON Representation |
|------|-------------|-------------------|
| `STRING` | Variable-length character data | string |
| `BYTES` | Variable-length binary data | string (base64) |
| `INTEGER` | 64-bit signed integer | number |
| `FLOAT` | Double precision floating point | number |
| `NUMERIC` | Exact numeric with 38 digits precision | string |
| `BIGNUMERIC` | Exact numeric with 76 digits precision | string |
| `BOOLEAN` | True/false values | boolean |
| `TIMESTAMP` | Absolute point in time | string (RFC3339) |
| `DATE` | Calendar date | string (YYYY-MM-DD) |
| `TIME` | Time of day | string (HH:MM:SS) |
| `DATETIME` | Date and time | string (YYYY-MM-DD HH:MM:SS) |
| `INTERVAL` | Duration | string |
| `RECORD` | Nested structure | object |
| `GEOGRAPHY` | Geographic data | string (WKT/GeoJSON) |
| `JSON` | JSON document | object |

### Field Modes

| Mode | Description |
|------|-------------|
| `NULLABLE` | Field can contain NULL values |
| `REQUIRED` | Field cannot contain NULL values |
| `REPEATED` | Field is an array of values |

## Validation Rules

### SQL Query Validation
- **Length**: 1 to 1,048,576 characters
- **Format**: Valid BigQuery SQL syntax
- **Encoding**: UTF-8 text

### Parameter Validation
- **Count**: Maximum 100 parameters per query
- **Names**: Must be valid BigQuery parameter names
- **Values**: Converted to strings for dry-run processing
- **Types**: Original types preserved in parameter object

### Cost Calculation Precision
- **Input**: 64-bit integer (bytes processed)
- **Calculation**: Double precision floating point
- **Output**: Rounded to 6 decimal places
- **Currency**: USD

## Error Schema Validation

All error responses must conform to the error object schema:

```json
{
  "code": "ERROR_CODE",        // Required: enum value
  "message": "Error message",  // Required: non-empty string  
  "location": {               // Optional: syntax error location
    "line": 1,                // Required if location present
    "column": 10              // Required if location present
  },
  "details": [...]            // Optional: BigQuery error array
}
```

## Schema Examples

### Complete Validation Success
```json
{
  "isValid": true
}
```

### Complete Validation Error
```json
{
  "isValid": false,
  "error": {
    "code": "INVALID_SQL",
    "message": "Syntax error: Expected keyword SELECT but got identifier 'SELCT' at [1:1]",
    "location": {
      "line": 1,
      "column": 1
    },
    "details": [
      {
        "reason": "invalidQuery",
        "location": "query",
        "message": "Syntax error: Expected keyword SELECT but got identifier 'SELCT'"
      }
    ]
  }
}
```

### Complete Dry-Run Success
```json
{
  "totalBytesProcessed": 6432735,
  "usdEstimate": 0.000030,
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
      "type": "INTEGER", 
      "mode": "NULLABLE"
    }
  ]
}
```

### Complete Dry-Run Error
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