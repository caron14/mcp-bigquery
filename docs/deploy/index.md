# Deployment Guide

This section provides comprehensive guides for deploying MCP BigQuery in various environments and with different MCP clients.

## Overview

MCP BigQuery is a Model Context Protocol (MCP) server that can be deployed in multiple ways depending on your use case and environment. The server communicates via standard input/output (stdio) and requires minimal system resources.

## Deployment Options

<div class="grid cards" markdown>

-   :material-desktop-classic:{ .lg .middle } **[Claude Code Setup](claude-code.md)**

    ---

    Detailed configuration for Claude Code with environment variables, authentication, and troubleshooting.

-   :material-api:{ .lg .middle } **[Other MCP Clients](mcp-clients.md)**

    ---

    Configuration examples for various MCP clients and integration platforms.

</div>

## Architecture Overview

```mermaid
graph TB
    Client[MCP Client<br/>Claude Code, etc.] 
    Server[MCP BigQuery Server<br/>mcp-bigquery]
    BQ[Google BigQuery API]
    
    Client --|stdio| Server
    Server --|Authenticated API Calls| BQ
    
    subgraph "Authentication"
        ADC[Application Default Credentials]
        SA[Service Account Key]
        User[User Account]
    end
    
    Server -.-> ADC
    Server -.-> SA
    Server -.-> User
```

## System Requirements

### Minimum Requirements

- **Python**: 3.10 or higher
- **Memory**: 64MB RAM (minimal footprint)
- **Storage**: 50MB for package and dependencies
- **Network**: HTTPS access to Google APIs

### Recommended Requirements

- **Python**: 3.11+ (better performance)
- **Memory**: 128MB RAM (comfortable operation)
- **CPU**: Any modern CPU (single-threaded)

## Authentication Methods

MCP BigQuery supports multiple authentication methods for Google Cloud:

### 1. Application Default Credentials (Recommended)

```bash
# Set up user credentials
gcloud auth application-default login

# Or set up service account
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

### 2. Service Account Key File

```bash
# Download service account key from Google Cloud Console
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

### 3. Workload Identity (GKE/Cloud Run)

For containerized deployments, use Workload Identity:

```yaml
# Kubernetes service account annotation
metadata:
  annotations:
    iam.gke.io/gcp-service-account: your-sa@project.iam.gserviceaccount.com
```

## Environment Variables

Configure the server behavior with these environment variables:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `BQ_PROJECT` | GCP project ID for BigQuery operations | From ADC | No* |
| `BQ_LOCATION` | BigQuery dataset location (e.g., US, EU, asia-northeast1) | None | No |
| `SAFE_PRICE_PER_TIB` | Default price per TiB for cost estimation (USD) | 5.0 | No |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account key file | None | No** |

!!! note "Authentication Requirements"
    * Either `BQ_PROJECT` must be set or default project must be available via ADC
    ** Either `GOOGLE_APPLICATION_CREDENTIALS` or `gcloud auth application-default login` is required

## Security Considerations

### Production Deployments

#### Service Account Permissions

Create a minimal service account with only required permissions:

```bash
# Create service account
gcloud iam service-accounts create mcp-bigquery-sa \
    --description="MCP BigQuery Service Account" \
    --display-name="MCP BigQuery"

# Grant minimal permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:mcp-bigquery-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser"

# Optional: Add data viewer if your queries need to access specific datasets
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:mcp-bigquery-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataViewer"
```

#### Network Security

- **Firewall**: No incoming ports required (stdio communication)
- **Outbound**: Allow HTTPS (443) to `*.googleapis.com`
- **VPC**: Can run in private networks with Private Google Access

#### Secrets Management

Store sensitive configuration securely:

=== "Docker Secrets"
    ```yaml
    version: '3.8'
    services:
      mcp-bigquery:
        image: your-registry/mcp-bigquery
        secrets:
          - google_credentials
        environment:
          GOOGLE_APPLICATION_CREDENTIALS: /run/secrets/google_credentials
    
    secrets:
      google_credentials:
        file: ./service-account-key.json
    ```

=== "Kubernetes Secrets"
    ```yaml
    apiVersion: v1
    kind: Secret
    metadata:
      name: mcp-bigquery-secret
    type: Opaque
    data:
      service-account.json: <base64-encoded-key>
    ```

=== "Cloud Secret Manager"
    ```bash
    # Store secret
    gcloud secrets create mcp-bigquery-sa-key \
        --data-file=service-account-key.json
    
    # Grant access
    gcloud secrets add-iam-policy-binding mcp-bigquery-sa-key \
        --member="serviceAccount:mcp-bigquery-sa@PROJECT.iam.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor"
    ```

## Monitoring and Logging

### Health Checks

MCP BigQuery doesn't expose HTTP endpoints, but you can monitor:

- **Process**: Check if the Python process is running
- **BigQuery API**: Monitor API quota and error rates
- **Authentication**: Verify credential validity

```bash
# Check if process is running
pgrep -f "mcp-bigquery"

# Test authentication
python -c "
from mcp_bigquery.bigquery_client import get_bigquery_client
try:
    client = get_bigquery_client()
    print('Authentication successful')
except Exception as e:
    print(f'Authentication failed: {e}')
"
```

### Logging Configuration

Configure Python logging for troubleshooting:

```python
import logging
import os

# Set log level via environment
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Metrics Collection

Monitor key metrics:

- **Query Validation Rate**: Success/failure ratio
- **Bytes Processed**: Data volume estimates
- **API Latency**: BigQuery API response times
- **Error Types**: Categorize validation errors

## Troubleshooting

### Common Issues

#### Authentication Errors

```bash
# Error: "Could not automatically determine credentials"
# Solution: Set up Application Default Credentials
gcloud auth application-default login

# Error: "Access Denied"
# Solution: Grant BigQuery permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="user:your-email@domain.com" \
    --role="roles/bigquery.jobUser"
```

#### Permission Errors

```bash
# Error: "BigQuery Job User role required"
# Solution: Add jobUser role
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:sa@project.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser"
```

#### Network Connectivity

```bash
# Test Google APIs connectivity
curl -I https://bigquery.googleapis.com/

# Test with authentication
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    https://bigquery.googleapis.com/bigquery/v2/projects
```

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
# Set debug logging
export LOG_LEVEL=DEBUG

# Run with debug output
python -m mcp_bigquery 2>&1 | tee debug.log
```

### Validation Tests

Test your deployment:

```bash
# Test basic functionality
echo '{"method": "tools/list"}' | python -m mcp_bigquery

# Test SQL validation
echo '{
  "method": "tools/call",
  "params": {
    "name": "bq_validate_sql",
    "arguments": {"sql": "SELECT 1"}
  }
}' | python -m mcp_bigquery
```

## Next Steps

- [Configure Claude Code](claude-code.md) for desktop development
- [Set up other MCP clients](mcp-clients.md) for various environments
- [Review examples](../examples/index.md) for real-world usage patterns

## Support

If you encounter issues during deployment:

- Check the [troubleshooting section](#troubleshooting) above
- Review [GitHub Issues](https://github.com/caron14/mcp-bigquery/issues)
- Create a new issue with deployment details
- Join [GitHub Discussions](https://github.com/caron14/mcp-bigquery/discussions) for community help