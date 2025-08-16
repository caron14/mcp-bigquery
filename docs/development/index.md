# Development Guide

Welcome to the MCP BigQuery development guide! This section helps contributors get started with developing, testing, and contributing to the project.

## Quick Overview

MCP BigQuery is a minimal Model Context Protocol (MCP) server that provides BigQuery SQL validation and dry-run analysis capabilities. The project is built with Python 3.10+ and uses the Google Cloud BigQuery client library.

### Key Features

- **Dry-run only operations** - Never executes queries, only validates and analyzes
- **Two core tools** - `bq_validate_sql` and `bq_dry_run_sql`
- **Cost estimation** - Calculates USD estimates based on bytes processed
- **Parameter support** - Handles parameterized BigQuery queries
- **MCP protocol compliance** - Standard MCP server implementation

## Architecture Overview

```
src/mcp_bigquery/
├── __init__.py          # Package initialization and version
├── __main__.py          # CLI entry point
├── server.py            # MCP server implementation
└── bigquery_client.py   # BigQuery client management
```

### Core Components

- **MCP Server** (`server.py`) - Implements the MCP protocol using `mcp.server.stdio`
- **BigQuery Client** (`bigquery_client.py`) - Manages BigQuery client creation and authentication
- **CLI Interface** (`__main__.py`) - Provides console script entry point

## Development Workflow

### 1. Environment Setup
Set up your development environment with proper authentication and dependencies.
→ [Development Setup Guide](setup.md)

### 2. Testing
Run comprehensive tests including unit tests and integration tests.
→ [Testing Guide](testing.md)

### 3. Contributing
Follow contribution guidelines for code style, PRs, and releases.
→ [Contributing Guide](contributing.md)

## Key Design Principles

### Dry-run Only
All BigQuery operations use `job_config.dry_run = True` to ensure queries are never executed.

```python
job_config = bigquery.QueryJobConfig(
    dry_run=True,
    use_query_cache=False,
    maximum_bytes_billed=0
)
```

### Error Handling
Structured error responses with location information extracted from BigQuery error messages.

```python
# Error location extraction
error_pattern = r'\[(\d+):(\d+)\]'
match = re.search(error_pattern, error_message)
```

### Parameter Support
Parameters are treated as STRING type in dry-run mode due to BigQuery limitations.

```python
# All parameters converted to STRING
for key, value in params.items():
    job_config.query_parameters.append(
        bigquery.ScalarQueryParameter(key, "STRING", str(value))
    )
```

## Development Environment

### Required Tools

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.10+ | Runtime |
| uv | Latest | Package management |
| pytest | 7.0+ | Testing |
| Google Cloud SDK | Latest | Authentication |

### Optional Tools

| Tool | Purpose |
|------|---------|
| MkDocs | Documentation |
| Black | Code formatting |
| Mypy | Type checking |
| Ruff | Linting |

## Testing Strategy

The project uses a comprehensive testing approach:

- **Unit Tests** - No external dependencies, using mocks
- **Integration Tests** - Real BigQuery API calls with public datasets
- **Credential Detection** - Automatic skipping when credentials unavailable

Test files are organized by dependency requirements:

```
tests/
├── conftest.py           # Fixtures and configuration
├── test_min.py          # Minimal tests, includes unit tests
├── test_imports.py      # Import validation
└── test_integration.py  # BigQuery API integration tests
```

## Getting Help

### Resources

- **CLAUDE.md** - Detailed project instructions and commands
- **GitHub Issues** - Bug reports and feature requests
- **GitHub Discussions** - General questions and community support

### Common Development Tasks

```bash
# Install in development mode
uv pip install -e ".[dev]"

# Run all tests
pytest tests/

# Run only unit tests (no credentials needed)
pytest tests/test_min.py::TestWithoutCredentials

# Run the server locally
python -m mcp_bigquery

# Build package
python -m build
```

## Next Steps

Ready to contribute? Start with:

1. **[Setup Your Environment](setup.md)** - Install dependencies and configure authentication
2. **[Run the Tests](testing.md)** - Ensure everything works correctly
3. **[Make Your First Contribution](contributing.md)** - Learn the contribution workflow

## Project Goals

MCP BigQuery aims to be:

- **Minimal** - Two tools, focused functionality
- **Safe** - Dry-run only, no accidental query execution
- **Reliable** - Comprehensive testing and error handling
- **Developer-friendly** - Clear documentation and examples

Happy coding! 🚀