# Guides

Welcome to the MCP BigQuery guides! These comprehensive guides will help you master SQL validation, dry-run analysis, cost estimation, and parameterized queries with the MCP BigQuery server.

## Overview

The MCP BigQuery server provides two powerful tools for working with BigQuery SQL without executing queries:

- **`bq_validate_sql`** - Validate SQL syntax and structure
- **`bq_dry_run_sql`** - Analyze queries for cost, performance, and metadata

These guides provide in-depth coverage of each tool with practical examples, best practices, and troubleshooting tips.

## Available Guides

### [SQL Validation Guide](validation.md)
Learn how to validate BigQuery SQL syntax and catch errors before execution. This guide covers:

- Understanding validation responses
- Interpreting error messages and locations
- Handling complex SQL constructs
- Debugging invalid queries
- Best practices for SQL validation

### [Dry-Run Analysis Guide](dry-run.md)
Master dry-run analysis to understand query behavior without execution. This guide covers:

- Analyzing query metadata
- Understanding referenced tables
- Schema preview and column analysis
- Performance insights
- Troubleshooting dry-run issues

### [Cost Estimation Guide](cost-estimation.md)
Learn how to estimate and optimize BigQuery query costs. This guide covers:

- Understanding BigQuery pricing models
- Calculating accurate cost estimates
- Optimizing queries for cost efficiency
- Setting up cost controls
- Regional pricing considerations

### [Parameterized Queries Guide](parameters.md)
Master parameterized queries for dynamic SQL execution. This guide covers:

- Creating parameterized queries
- Parameter types and handling
- Best practices for parameter usage
- Security considerations
- Common parameter patterns

## Getting Started

Before diving into the guides, make sure you have:

1. **Installed MCP BigQuery** - See [Installation Guide](../get-started/installation.md)
2. **Configured Authentication** - See [Authentication Guide](../get-started/authentication.md)
3. **Completed Quickstart** - See [Quickstart Guide](../get-started/quickstart.md)

## Common Use Cases

### Development Workflow
```json
{
  "workflow": [
    "1. Validate SQL syntax with bq_validate_sql",
    "2. Analyze cost and performance with bq_dry_run_sql",
    "3. Optimize based on results",
    "4. Repeat validation after changes"
  ]
}
```

### Query Optimization
```json
{
  "steps": [
    "1. Run dry-run to get baseline metrics",
    "2. Identify expensive operations",
    "3. Apply optimization techniques",
    "4. Compare before/after results"
  ]
}
```

### Cost Management
```json
{
  "approach": [
    "1. Set up cost estimation with realistic pricing",
    "2. Validate query costs before execution",
    "3. Implement cost alerts and controls",
    "4. Monitor and optimize regularly"
  ]
}
```

## Best Practices Summary

### General Guidelines
- Always validate SQL before dry-run analysis
- Use parameterized queries for dynamic content
- Set realistic pricing for accurate cost estimates
- Test with representative data volumes
- Monitor query patterns and costs regularly

### Performance Tips
- Use dry-run to identify expensive operations
- Leverage schema preview for column optimization
- Analyze referenced tables for join optimization
- Consider partition and clustering strategies

### Security Considerations
- Use parameterized queries to prevent injection
- Validate all dynamic SQL content
- Monitor query patterns for anomalies
- Implement proper access controls

## Troubleshooting Quick Reference

### Common Issues
- **Authentication errors** → Check [Authentication Guide](../get-started/authentication.md)
- **Invalid SQL syntax** → See [Validation Guide](validation.md#troubleshooting)
- **Unexpected costs** → See [Cost Estimation Guide](cost-estimation.md#troubleshooting)
- **Parameter issues** → See [Parameters Guide](parameters.md#troubleshooting)

### Error Codes
- `INVALID_SQL` - SQL syntax or structure error
- `UNKNOWN_ERROR` - Unexpected error condition
- `AUTHENTICATION_ERROR` - BigQuery authentication failure

## Examples Repository

Each guide includes comprehensive examples, but you can also find additional examples in:

- [Examples Directory](../examples/) - Complete example configurations
- [API Reference](../api-reference/) - Detailed tool specifications
- [Development Guide](../development/) - Advanced development patterns

## Support and Community

Need help? Here are your options:

- **Documentation** - Start with these guides and API reference
- **Examples** - Check the examples directory for similar use cases
- **Issues** - Report bugs or request features on GitHub
- **Discussions** - Ask questions and share experiences

## Next Steps

Ready to get started? We recommend following this learning path:

1. **[SQL Validation Guide](validation.md)** - Master the basics of SQL validation
2. **[Dry-Run Analysis Guide](dry-run.md)** - Learn query analysis techniques
3. **[Cost Estimation Guide](cost-estimation.md)** - Understand and optimize costs
4. **[Parameterized Queries Guide](parameters.md)** - Add dynamic capabilities

Each guide builds on the previous ones, providing a comprehensive understanding of the MCP BigQuery server capabilities.