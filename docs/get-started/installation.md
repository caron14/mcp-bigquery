# Installation

This guide covers different ways to install MCP BigQuery for various use cases.

## System Requirements

- **Python**: 3.10 or higher
- **Operating System**: Linux, macOS, or Windows
- **Google Cloud SDK**: Required for authentication
- **Memory**: Minimal (< 50MB)
- **Network**: Internet access for BigQuery API

## Installation Methods

### From PyPI (Recommended)

The simplest way to install MCP BigQuery:

=== "pip"

    ```bash
    pip install mcp-bigquery
    ```

=== "uv"

    ```bash
    uv pip install mcp-bigquery
    ```

=== "pipx"

    ```bash
    pipx install mcp-bigquery
    ```

### From Source

For development or latest features:

```bash
# Clone the repository
git clone https://github.com/caron14/mcp-bigquery.git
cd mcp-bigquery

# Install in development mode
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

### Using Docker

For containerized environments:

```dockerfile
FROM python:3.10-slim

# Install Google Cloud SDK
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - \
    && apt-get update && apt-get install -y google-cloud-sdk

# Install mcp-bigquery
RUN pip install mcp-bigquery

# Set up authentication (mount your credentials)
VOLUME ["/root/.config/gcloud"]

CMD ["mcp-bigquery"]
```

## Verify Installation

After installation, verify everything is working:

### Check Version

```bash
mcp-bigquery --version
```

Expected output:
```
mcp-bigquery version 0.1.0
```

### Test Server Start

```bash
python -m mcp_bigquery
```

The server should start and wait for MCP client connections.

### Run Basic Test

```python
# test_installation.py
import asyncio
from mcp_bigquery.server import validate_sql

async def test():
    result = await validate_sql({"sql": "SELECT 1"})
    print(f"Validation result: {result}")

asyncio.run(test())
```

## Package Structure

After installation, you'll have:

```
mcp-bigquery/
├── mcp_bigquery/          # Main package
│   ├── __init__.py        # Package initialization
│   ├── __main__.py        # Entry point
│   ├── server.py          # MCP server implementation
│   └── bigquery_client.py # BigQuery client utilities
└── mcp-bigquery           # Console script
```

## Environment Setup

### Required Environment Variables

```bash
# Google Cloud Project (optional, uses default from gcloud)
export BQ_PROJECT="your-project-id"

# BigQuery Location (optional)
export BQ_LOCATION="US"  # or EU, asia-northeast1, etc.

# Cost estimation price per TiB (optional, default: 5.0)
export SAFE_PRICE_PER_TIB="5.0"
```

### Development Environment

For development, create a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (optional)
pre-commit install
```

## Troubleshooting

### ImportError: No module named 'mcp_bigquery'

**Solution**: Ensure the package is installed in your active Python environment:
```bash
pip list | grep mcp-bigquery
```

### Command 'mcp-bigquery' not found

**Solution**: The console script may not be in your PATH:
```bash
# Use Python module instead
python -m mcp_bigquery

# Or add pip scripts to PATH
export PATH="$PATH:$(python -m site --user-base)/bin"
```

### Permission denied during installation

**Solution**: Use user installation or virtual environment:
```bash
# User installation
pip install --user mcp-bigquery

# Or use virtual environment (recommended)
python -m venv venv
source venv/bin/activate
pip install mcp-bigquery
```

### SSL Certificate errors

**Solution**: Update certificates or use trusted host:
```bash
# Update certificates
pip install --upgrade certifi

# Or use trusted host (not recommended for production)
pip install --trusted-host pypi.org mcp-bigquery
```

## Next Steps

- 🚀 Continue to [Quick Start](quickstart.md) for your first query validation
- 🔐 Set up [Authentication](authentication.md) with Google Cloud
- 📖 Explore the [API Reference](../api-reference/index.md)
- 💡 Check out [Examples](../examples/index.md)