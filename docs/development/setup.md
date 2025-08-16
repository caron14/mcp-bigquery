# Development Environment Setup

This guide walks you through setting up a complete development environment for MCP BigQuery.

## Prerequisites

### System Requirements

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.10+ | Required for async support |
| Git | Any recent version | For version control |
| Google Cloud SDK | Latest | For BigQuery authentication |

### Platform Support

MCP BigQuery is tested on:

- **macOS** (Apple Silicon and Intel)
- **Linux** (Ubuntu 20.04+, other distributions)
- **Windows** (10/11 with WSL recommended)

## Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/caron14/mcp-bigquery.git
cd mcp-bigquery

# Verify repository structure
ls -la
```

You should see:
```
drwxr-xr-x   docs/           # Documentation
drwxr-xr-x   examples/       # Usage examples
drwxr-xr-x   src/            # Source code
drwxr-xr-x   tests/          # Test suite
-rw-r--r--   pyproject.toml  # Project configuration
-rw-r--r--   README.md       # Project overview
```

## Step 2: Set Up Python Environment

### Option A: Using uv (Recommended)

Install uv if you haven't already:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or using pip
pip install uv
```

Create and activate environment:

```bash
# Install in development mode with all dependencies
uv pip install -e ".[dev]"

# Verify installation
uv pip list | grep mcp-bigquery
```

### Option B: Using pip and venv

```bash
# Create virtual environment
python -m venv venv

# Activate environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Verify installation
pip list | grep mcp-bigquery
```

### Verify Installation

```bash
# Check if package is installed correctly
python -c "import mcp_bigquery; print(mcp_bigquery.__version__)"

# Test the CLI
mcp-bigquery --version

# Alternative CLI invocation
python -m mcp_bigquery --version
```

## Step 3: Google Cloud Authentication

### Install Google Cloud SDK

```bash
# macOS (using Homebrew)
brew install google-cloud-sdk

# Ubuntu/Debian
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Windows (download installer)
# Visit: https://cloud.google.com/sdk/docs/install
```

### Set Up Authentication

#### Option A: Application Default Credentials (Recommended)

```bash
# Authenticate with your Google account
gcloud auth application-default login

# Set default project (optional)
gcloud config set project YOUR_PROJECT_ID

# Verify authentication
gcloud auth application-default print-access-token
```

#### Option B: Service Account Key

```bash
# Create service account (if needed)
gcloud iam service-accounts create mcp-bigquery-dev \
  --display-name="MCP BigQuery Development"

# Generate key file
gcloud iam service-accounts keys create ~/mcp-bigquery-key.json \
  --iam-account=mcp-bigquery-dev@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS=~/mcp-bigquery-key.json
```

### Grant Required Permissions

Your account needs these IAM roles:

```bash
# Grant BigQuery Job User role (minimum required)
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="user:your-email@example.com" \
  --role="roles/bigquery.jobUser"

# Optional: BigQuery Data Viewer for accessing datasets
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="user:your-email@example.com" \
  --role="roles/bigquery.dataViewer"
```

## Step 4: Environment Configuration

### Create Development Environment File

Create a `.env` file in the project root:

```bash
# Copy example environment file
cp .env.example .env

# Edit with your settings
cat > .env << EOF
# BigQuery Configuration
BQ_PROJECT=your-project-id
BQ_LOCATION=US
SAFE_PRICE_PER_TIB=5.0

# Development Settings
PYTHONPATH=src
DEBUG=true
EOF
```

### Load Environment Variables

```bash
# Add to your shell profile (.bashrc, .zshrc, etc.)
export BQ_PROJECT="your-project-id"
export BQ_LOCATION="US"
export SAFE_PRICE_PER_TIB="5.0"

# Or use direnv for automatic loading
echo "dotenv" > .envrc
direnv allow
```

## Step 5: Verify Setup

### Run Basic Tests

```bash
# Test imports and basic functionality
python -c "
import mcp_bigquery
from mcp_bigquery.server import main
from mcp_bigquery.bigquery_client import get_bigquery_client
print('✅ All imports successful')
"

# Run unit tests (no credentials required)
pytest tests/test_min.py::TestWithoutCredentials -v

# Test BigQuery connectivity
pytest tests/test_integration.py::test_bigquery_connection -v
```

### Test MCP Server

```bash
# Start the server (will exit immediately in stdio mode)
python -m mcp_bigquery
echo "✅ MCP server starts successfully"

# Test with mock client (if you have one)
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' | python -m mcp_bigquery
```

### Validate BigQuery Access

```bash
# Test with a simple query
python -c "
from mcp_bigquery.bigquery_client import get_bigquery_client
from google.cloud import bigquery

client = get_bigquery_client()
job_config = bigquery.QueryJobConfig(dry_run=True)
query = 'SELECT 1'
job = client.query(query, job_config=job_config)
print(f'✅ BigQuery access verified')
print(f'Bytes processed: {job.total_bytes_processed}')
"
```

## Step 6: Development Tools (Optional)

### Code Quality Tools

```bash
# Install additional development tools
pip install black isort mypy ruff pre-commit

# Set up pre-commit hooks
pre-commit install

# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/mcp_bigquery/

# Linting
ruff check src/ tests/
```

### Documentation Tools

```bash
# Install documentation dependencies
pip install -r requirements-docs.txt

# Build documentation locally
mkdocs serve

# View at http://localhost:8000
```

### IDE Configuration

#### VS Code

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"],
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true
}
```

#### PyCharm

1. Open the project directory
2. Configure Python interpreter: Settings → Project → Python Interpreter
3. Set up pytest: Settings → Tools → Python Integrated Tools → Testing
4. Enable code inspections: Settings → Editor → Inspections

## Troubleshooting

### Common Issues

#### "No module named 'mcp_bigquery'"

**Solution**: Install in development mode
```bash
pip install -e ".[dev]"
```

#### "google.auth.exceptions.DefaultCredentialsError"

**Solution**: Set up authentication
```bash
gcloud auth application-default login
```

#### "Permission denied" for BigQuery

**Solution**: Grant required IAM roles
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="user:your-email@example.com" \
  --role="roles/bigquery.jobUser"
```

#### "Project not found"

**Solution**: Set project environment variable
```bash
export BQ_PROJECT="your-actual-project-id"
```

### Testing Your Setup

Run this comprehensive test:

```bash
#!/bin/bash
echo "🔍 Testing MCP BigQuery development setup..."

# Test 1: Python and package
python -c "import mcp_bigquery; print(f'✅ Package version: {mcp_bigquery.__version__}')" || exit 1

# Test 2: Dependencies
python -c "import google.cloud.bigquery, mcp.server.stdio; print('✅ Dependencies available')" || exit 1

# Test 3: Authentication
python -c "
from mcp_bigquery.bigquery_client import get_bigquery_client
client = get_bigquery_client()
print(f'✅ BigQuery client: project={client.project}')
" || exit 1

# Test 4: Unit tests
pytest tests/test_min.py::TestWithoutCredentials -q || exit 1
echo "✅ Unit tests pass"

# Test 5: Integration test (if credentials available)
if pytest tests/test_integration.py::test_bigquery_connection -q 2>/dev/null; then
    echo "✅ Integration tests pass"
else
    echo "⚠️  Integration tests skipped (credentials not available)"
fi

echo "🎉 Development setup complete!"
```

Save as `test-setup.sh`, make executable with `chmod +x test-setup.sh`, and run with `./test-setup.sh`.

## Next Steps

Your development environment is ready! Continue with:

1. **[Testing Guide](testing.md)** - Learn how to run and write tests
2. **[Contributing Guide](contributing.md)** - Understand the contribution workflow
3. **[API Reference](../api-reference/index.md)** - Explore the codebase structure

## Development Commands Reference

```bash
# Package management
uv pip install -e ".[dev]"          # Install in dev mode
uv pip list                         # List installed packages
uv pip show mcp-bigquery            # Show package info

# Testing
pytest tests/                       # Run all tests
pytest tests/test_min.py -v         # Run unit tests verbose
pytest --cov=mcp_bigquery tests/    # Run with coverage

# Development server
python -m mcp_bigquery              # Run MCP server
mcp-bigquery --version              # Check version

# Building
python -m build                     # Build package
twine check dist/*                  # Check package
```

Happy developing! 🎯