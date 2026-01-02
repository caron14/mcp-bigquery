# Installation & Setup

## Prerequisites

- **Python**: 3.10 or higher
- **Google Cloud SDK**: Required for authentication
- **BigQuery API**: Must be enabled in your GCP project

## Installation

### From PyPI (Recommended)

```bash
pip install mcp-bigquery
```

Or with uv:
```bash
uv pip install mcp-bigquery
```

### From Source

```bash
git clone https://github.com/caron14/mcp-bigquery.git
cd mcp-bigquery
pip install -e ".[dev]"
```

### Verify Installation

```bash
# Check version
mcp-bigquery --version

# Test server start
python -m mcp_bigquery
```

## Logging & Output Controls (v0.4.2)

The CLI now exposes unified logging controls backed by `mcp_bigquery.logging_config`. Logs default to `WARNING` on stderr so stdout stays clean for tool responses.

```bash
# Increase or decrease verbosity
mcp-bigquery --verbose          # INFO on stderr
mcp-bigquery -vv                # DEBUG
mcp-bigquery --quiet            # ERROR
mcp-bigquery --log-level=INFO   # Explicit override

# Structured output
mcp-bigquery --json-logs        # Emit JSON lines
```

Combine these flags with `LOG_LEVEL=DEBUG` in your environment when diagnosing CLI integrations.

## Authentication

### Quick Setup (Local Development)

```bash
# Login with your Google account
gcloud auth application-default login

# Set default project
gcloud config set project YOUR_PROJECT_ID

# Verify authentication
gcloud auth application-default print-access-token
```

### Service Account (Production)

```bash
# Create service account
gcloud iam service-accounts create mcp-bigquery \
  --display-name="MCP BigQuery Service Account"

# Grant permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:mcp-bigquery@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"

# Generate key file
gcloud iam service-accounts keys create key.json \
  --iam-account="mcp-bigquery@YOUR_PROJECT_ID.iam.gserviceaccount.com"

# Use the key
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

### Required Permissions

MCP BigQuery needs these IAM roles:
- `roles/bigquery.jobUser` - Create and run dry-run jobs
- `roles/bigquery.dataViewer` - Access table metadata

## Configuration

### Environment Variables

```bash
# Google Cloud Project (optional, uses default from gcloud)
export BQ_PROJECT="your-project-id"

# BigQuery Location (optional)
export BQ_LOCATION="US"  # or EU, asia-northeast1, etc.

# Cost estimation price per TiB (optional, default: 5.0)
export SAFE_PRICE_PER_TIB="5.0"

# Service account key (optional)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

### Claude Code Configuration

Add to your Claude Code configuration file:

```json
{
  "mcpServers": {
    "mcp-bigquery": {
      "command": "mcp-bigquery",
      "env": {
        "BQ_PROJECT": "your-project-id",
        "BQ_LOCATION": "US",
        "SAFE_PRICE_PER_TIB": "5.0"
      }
    }
  }
}
```

Or if installed from source:

```json
{
  "mcpServers": {
    "mcp-bigquery": {
      "command": "python",
      "args": ["-m", "mcp_bigquery"],
      "env": {
        "BQ_PROJECT": "your-project-id"
      }
    }
  }
}
```

## Quick Start

### Your First Validation

Validate a simple SQL query:

```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT 1 as test_column"
  }
}
```

**Response:**
```json
{
  "isValid": true
}
```

### Check Query Cost

Estimate cost using a public dataset:

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
  "totalBytesProcessed": 65536,
  "usdEstimate": 0.00032,
  "referencedTables": [{
    "project": "bigquery-public-data",
    "dataset": "samples",
    "table": "shakespeare"
  }],
  "schemaPreview": [
    {"name": "word", "type": "STRING", "mode": "NULLABLE"},
    {"name": "word_count", "type": "INT64", "mode": "NULLABLE"}
  ]
}
```

### Using Parameters

```json
{
  "tool": "bq_validate_sql",
  "arguments": {
    "sql": "SELECT * FROM users WHERE created_date = @date",
    "params": {
      "date": "2024-01-01"
    }
  }
}
```

## Troubleshooting

### Authentication Errors

**"Could not automatically determine credentials"**
```bash
gcloud auth application-default login
```

**"Permission denied"**
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT \
  --member="user:your-email@example.com" \
  --role="roles/bigquery.jobUser"
```

### Common Issues

**Command 'mcp-bigquery' not found**
```bash
# Use Python module instead
python -m mcp_bigquery
```

**Project not found**
```bash
export BQ_PROJECT="your-project-id"
```

**BigQuery API not enabled**
```bash
gcloud services enable bigquery.googleapis.com --project=YOUR_PROJECT
```

## Security Best Practices

1. **Never commit credentials** - Use environment variables or secret managers
2. **Use service accounts** - Create dedicated accounts with minimal permissions
3. **Rotate keys regularly** - Set up key rotation policies
4. **Enable audit logging** - Track all BigQuery operations

## Next Steps

- Learn about [SQL Validation and Analysis](usage.md)
- See [Usage Guide](usage.md) for tool documentation and workflows
