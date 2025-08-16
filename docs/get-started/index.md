# Getting Started

Welcome to MCP BigQuery! This guide will help you get up and running with BigQuery SQL validation and dry-run analysis.

## Overview

MCP BigQuery provides a safe way to:

- ✅ Validate SQL syntax without running queries
- 💰 Estimate query costs before execution
- 📊 Preview schemas and analyze query structure
- 🔧 Test parameterized queries

## Prerequisites

Before you begin, ensure you have:

- **Python 3.10+** installed
- **Google Cloud SDK** with BigQuery API enabled
- **A Google Cloud Project** with BigQuery access
- **Authentication** configured (ADC or service account)

## Quick Start

### 1. Install the Package

```bash
pip install mcp-bigquery
```

### 2. Configure Authentication

```bash
gcloud auth application-default login
```

### 3. Test the Installation

```bash
mcp-bigquery --version
```

### 4. Configure Your MCP Client

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "mcp-bigquery": {
      "command": "mcp-bigquery",
      "env": {
        "BQ_PROJECT": "your-project-id"
      }
    }
  }
}
```

## What's Next?

<div class="grid cards" markdown>

-   :material-download:{ .lg .middle } **[Installation Guide](installation.md)**

    Detailed installation instructions for different environments

-   :material-rocket:{ .lg .middle } **[Quick Start Tutorial](quickstart.md)**

    Your first query validation in 5 minutes

-   :material-key:{ .lg .middle } **[Authentication Setup](authentication.md)**

    Configure Google Cloud authentication

-   :material-book:{ .lg .middle } **[Guides](../guides/index.md)**

    Learn advanced features and best practices

</div>

## Common Issues

### Authentication Error

If you see authentication errors:

1. Ensure you're logged in: `gcloud auth application-default login`
2. Check your project: `gcloud config get-value project`
3. Verify BigQuery API is enabled in your project

### Permission Denied

Ensure your account has the necessary BigQuery permissions:

- `bigquery.jobs.create` - Required for dry-run
- `bigquery.tables.get` - Required for table metadata
- `bigquery.datasets.get` - Required for dataset access

## Getting Help

- 📖 Check the [API Reference](../api-reference/index.md)
- 💡 Browse [Examples](../examples/index.md)
- 🐛 Report issues on [GitHub](https://github.com/caron14/mcp-bigquery/issues)
- 💬 Join discussions on [GitHub Discussions](https://github.com/caron14/mcp-bigquery/discussions)