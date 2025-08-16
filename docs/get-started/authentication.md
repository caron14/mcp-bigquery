# Authentication

MCP BigQuery uses Google Cloud authentication to access BigQuery APIs. This guide covers all authentication methods and troubleshooting.

## Overview

MCP BigQuery supports multiple authentication methods:

1. **Application Default Credentials (ADC)** - Recommended for development
2. **Service Account Keys** - For production and CI/CD
3. **Workload Identity** - For GKE and cloud environments
4. **Impersonation** - For delegated access

## Application Default Credentials (ADC)

### Local Development Setup

The simplest way to authenticate for local development:

```bash
# Login with your Google account
gcloud auth application-default login

# Verify authentication
gcloud auth application-default print-access-token
```

### Set Default Project

```bash
# Set default project
gcloud config set project YOUR_PROJECT_ID

# Verify project
gcloud config get-value project
```

### ADC Search Order

Google Cloud SDKs search for credentials in this order:

1. `GOOGLE_APPLICATION_CREDENTIALS` environment variable
2. User credentials from `gcloud auth application-default login`
3. Service account attached to the resource (GCE, GKE, Cloud Run, etc.)
4. Google Cloud SDK default credentials

## Service Account Authentication

### Create a Service Account

```bash
# Create service account
gcloud iam service-accounts create mcp-bigquery \
  --display-name="MCP BigQuery Service Account"

# Get the email
SA_EMAIL="mcp-bigquery@YOUR_PROJECT_ID.iam.gserviceaccount.com"

# Grant necessary permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/bigquery.dataViewer"
```

### Generate and Use Key File

```bash
# Generate key file
gcloud iam service-accounts keys create key.json \
  --iam-account="${SA_EMAIL}"

# Use the key file
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"

# Run MCP BigQuery
mcp-bigquery
```

!!! warning "Security Best Practice"
    - Never commit service account keys to version control
    - Rotate keys regularly
    - Use Workload Identity in GKE instead of key files
    - Store keys in secret management systems

## Required Permissions

MCP BigQuery requires these BigQuery IAM permissions:

### Minimum Permissions

| Permission | Purpose | Required |
|------------|---------|----------|
| `bigquery.jobs.create` | Create dry-run jobs | ✅ Yes |
| `bigquery.tables.get` | Get table metadata | ✅ Yes |
| `bigquery.tables.getData` | Access table data for dry-run | ✅ Yes |
| `bigquery.datasets.get` | Access dataset metadata | ✅ Yes |

### Recommended Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| `roles/bigquery.jobUser` | Run BigQuery jobs | Create and run jobs |
| `roles/bigquery.dataViewer` | View table data | Read table/dataset metadata |
| `roles/bigquery.user` | Full BigQuery access | All BigQuery operations |

### Custom Role Example

Create a minimal custom role:

```yaml
# mcp-bigquery-role.yaml
title: "MCP BigQuery Dry Run"
description: "Minimal permissions for MCP BigQuery dry-run operations"
stage: "GA"
includedPermissions:
  - bigquery.jobs.create
  - bigquery.tables.get
  - bigquery.tables.getData
  - bigquery.datasets.get
  - bigquery.routines.get  # For UDFs
  - bigquery.models.getMetadata  # For ML models
```

```bash
# Create the custom role
gcloud iam roles create mcpBigQueryDryRun \
  --project=YOUR_PROJECT_ID \
  --file=mcp-bigquery-role.yaml
```

## Environment Variables

### Authentication Variables

```bash
# Service account key file (highest priority)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"

# Default project for BigQuery operations
export BQ_PROJECT="your-project-id"

# Default location for BigQuery datasets
export BQ_LOCATION="US"  # or EU, asia-northeast1, etc.

# Impersonate a service account (optional)
export GOOGLE_IMPERSONATE_SERVICE_ACCOUNT="sa@project.iam.gserviceaccount.com"
```

### Configuration in MCP Client

```json
{
  "mcpServers": {
    "mcp-bigquery": {
      "command": "mcp-bigquery",
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/key.json",
        "BQ_PROJECT": "your-project-id",
        "BQ_LOCATION": "US"
      }
    }
  }
}
```

## Cloud Environment Authentication

### Google Kubernetes Engine (GKE)

Use Workload Identity for secure authentication:

```bash
# Enable Workload Identity on cluster
gcloud container clusters update CLUSTER_NAME \
  --workload-pool=PROJECT_ID.svc.id.goog

# Create Kubernetes service account
kubectl create serviceaccount mcp-bigquery

# Bind to Google service account
gcloud iam service-accounts add-iam-policy-binding \
  SA_EMAIL@PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/iam.workloadIdentityUser \
  --member="serviceAccount:PROJECT_ID.svc.id.goog[NAMESPACE/mcp-bigquery]"

# Annotate Kubernetes service account
kubectl annotate serviceaccount mcp-bigquery \
  iam.gke.io/gcp-service-account=SA_EMAIL@PROJECT_ID.iam.gserviceaccount.com
```

### Cloud Run

Cloud Run automatically uses the service account attached to the service:

```bash
# Deploy with specific service account
gcloud run deploy mcp-bigquery \
  --image=gcr.io/PROJECT_ID/mcp-bigquery \
  --service-account=SA_EMAIL@PROJECT_ID.iam.gserviceaccount.com
```

### Compute Engine

GCE instances use the attached service account:

```bash
# Create instance with service account
gcloud compute instances create mcp-bigquery-vm \
  --service-account=SA_EMAIL@PROJECT_ID.iam.gserviceaccount.com \
  --scopes=https://www.googleapis.com/auth/bigquery
```

## Authentication Debugging

### Check Current Authentication

```bash
# Check ADC
gcloud auth application-default print-access-token

# Check active account
gcloud auth list

# Check project
gcloud config get-value project
```

### Test BigQuery Access

```bash
# Test with bq command
bq query --dry_run --use_legacy_sql=false 'SELECT 1'

# Test with Python
python -c "
import google.auth
from google.cloud import bigquery

credentials, project = google.auth.default()
client = bigquery.Client(credentials=credentials, project=project)
print(f'Authenticated as: {credentials.service_account_email if hasattr(credentials, "service_account_email") else "user"}')
print(f'Project: {project}')
"
```

### Common Authentication Errors

#### Error: "Could not automatically determine credentials"

**Causes and Solutions:**

1. **No credentials configured**
   ```bash
   gcloud auth application-default login
   ```

2. **Invalid key file path**
   ```bash
   # Check if file exists
   ls -la $GOOGLE_APPLICATION_CREDENTIALS
   ```

3. **Expired credentials**
   ```bash
   # Refresh credentials
   gcloud auth application-default login --force
   ```

#### Error: "Permission denied: Dataset PROJECT:dataset"

**Solutions:**

1. **Check IAM permissions**
   ```bash
   gcloud projects get-iam-policy PROJECT_ID \
     --flatten="bindings[].members" \
     --filter="bindings.members:YOUR_EMAIL"
   ```

2. **Grant necessary roles**
   ```bash
   gcloud projects add-iam-policy-binding PROJECT_ID \
     --member="user:YOUR_EMAIL" \
     --role="roles/bigquery.user"
   ```

#### Error: "The project PROJECT_ID has not enabled BigQuery"

**Solution:**
```bash
# Enable BigQuery API
gcloud services enable bigquery.googleapis.com --project=PROJECT_ID
```

## Security Best Practices

### 1. Principle of Least Privilege

- Grant only necessary permissions
- Use custom roles for specific needs
- Regularly audit permissions

### 2. Credential Management

- Never hardcode credentials
- Use secret management systems
- Rotate service account keys regularly
- Delete unused service accounts

### 3. Environment Isolation

```bash
# Development environment
export BQ_PROJECT="dev-project"
export GOOGLE_APPLICATION_CREDENTIALS="/secrets/dev-key.json"

# Production environment
export BQ_PROJECT="prod-project"
export GOOGLE_APPLICATION_CREDENTIALS="/secrets/prod-key.json"
```

### 4. Audit Logging

Enable audit logs for BigQuery:

```bash
gcloud logging read "resource.type=bigquery_resource" \
  --limit=10 \
  --format=json
```

## Multi-Project Setup

Access BigQuery across multiple projects:

```python
# Query across projects
sql = """
SELECT * FROM `project-a.dataset1.table1` a
JOIN `project-b.dataset2.table2` b
ON a.id = b.id
"""

# Ensure service account has access to both projects
```

Grant cross-project access:

```bash
# Grant access to project-b from project-a service account
gcloud projects add-iam-policy-binding project-b \
  --member="serviceAccount:sa@project-a.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"
```

## Next Steps

- 🚀 Continue to [Quick Start](quickstart.md)
- 📊 Learn about [SQL Validation](../guides/validation.md)
- 🔒 Set up [CI/CD Authentication](../deploy/index.md)
- 📝 Read [API Reference](../api-reference/index.md)