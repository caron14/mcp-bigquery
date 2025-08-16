# Development Guide

Guide for contributors and developers working on MCP BigQuery.

## Development Setup

### Prerequisites

- Python 3.10+
- Git
- Google Cloud SDK with BigQuery API enabled

### Clone and Install

```bash
# Clone repository
git clone https://github.com/caron14/mcp-bigquery.git
cd mcp-bigquery

# Install with development dependencies
pip install -e ".[dev]"

# Or using uv
uv pip install -e ".[dev]"
```

### Environment Setup

```bash
# Set up Google Cloud authentication
gcloud auth application-default login

# Configure project
export BQ_PROJECT="your-test-project"
export BQ_LOCATION="US"

# Install pre-commit hooks
pre-commit install

# Run development server
python -m mcp_bigquery
```

### Pre-commit Setup

This project uses pre-commit hooks to ensure code quality:

```bash
# Install pre-commit hooks (one-time setup)
pre-commit install

# Run all hooks manually
pre-commit run --all-files

# Update hook versions
pre-commit autoupdate
```

Configured hooks:
- **isort**: Sorts Python imports
- **black**: Formats Python code (line length: 100)
- **flake8**: Checks Python code style
- **ruff**: Fast Python linter
- **mypy**: Type checking for Python

## Project Structure

```
mcp-bigquery/
├── src/mcp_bigquery/
│   ├── __init__.py         # Package initialization
│   ├── __main__.py         # Entry point
│   ├── server.py           # MCP server implementation
│   └── bigquery_client.py  # BigQuery client utilities
├── tests/
│   ├── test_min.py         # Unit tests (no credentials)
│   ├── test_imports.py     # Import validation
│   └── test_integration.py # Integration tests
├── docs/                   # Documentation
├── examples/               # Usage examples
└── pyproject.toml         # Project configuration
```

## Testing

### Run All Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=mcp_bigquery tests/

# Run specific test file
pytest tests/test_min.py -v
```

### Test Categories

1. **Unit Tests** - No BigQuery credentials required
   ```bash
   pytest tests/test_min.py::TestWithoutCredentials
   ```

2. **Integration Tests** - Requires BigQuery access
   ```bash
   pytest tests/test_integration.py
   ```

### Writing Tests

```python
# Example unit test
import pytest
from mcp_bigquery.server import validate_sql

@pytest.mark.asyncio
async def test_validate_simple_query():
    result = await validate_sql({"sql": "SELECT 1"})
    assert result["isValid"] is True

# Example integration test
@pytest.mark.requires_credentials
async def test_public_dataset_query():
    sql = "SELECT * FROM `bigquery-public-data.samples.shakespeare`"
    result = await dry_run_sql({"sql": sql})
    assert result["totalBytesProcessed"] > 0
```

## Code Style

### Formatting

```bash
# Format with black
black src/ tests/

# Check with ruff
ruff check src/ tests/

# Type checking with mypy
mypy src/
```

### Style Guidelines

1. Follow PEP 8
2. Use type hints for all functions
3. Add docstrings to public functions
4. Keep functions small and focused
5. Use descriptive variable names

## Making Changes

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Follow the existing code patterns:

```python
async def your_new_function(params: dict) -> dict:
    """
    Brief description of function.
    
    Args:
        params: Dictionary with 'sql' and optional 'params'
    
    Returns:
        Dictionary with result or error
    """
    try:
        # Implementation
        return {"success": True}
    except Exception as e:
        return {"error": {"code": "ERROR_CODE", "message": str(e)}}
```

### 3. Test Your Changes

```bash
# Run tests
pytest tests/

# Test manually
python -m mcp_bigquery
```

### 4. Update Documentation

Update relevant documentation:
- Add new features to README.md
- Update API documentation
- Add examples if applicable

### 5. Submit Pull Request

```bash
# Commit changes
git add .
git commit -m "feat: add new feature"

# Push to GitHub
git push origin feature/your-feature-name
```

## Building and Publishing

### Build Package

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build distribution
python -m build

# Check package contents
tar -tzf dist/mcp-bigquery-*.tar.gz | head -20
```

### Test Package Locally

```bash
# Install from local build
pip install dist/mcp-bigquery-*.whl

# Test installation
mcp-bigquery --version
```

### Publish to PyPI

```bash
# Test on TestPyPI first
python -m twine upload --repository testpypi dist/*

# Publish to PyPI
python -m twine upload dist/*
```

## Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Common Issues

1. **Import errors**
   ```bash
   # Ensure package is installed in editable mode
   pip install -e .
   ```

2. **Authentication errors**
   ```bash
   # Check credentials
   gcloud auth application-default print-access-token
   ```

3. **Test failures**
   ```bash
   # Run single test with verbose output
   pytest tests/test_min.py::test_name -vvs
   ```

## Architecture Notes

### MCP Server Implementation

The server follows MCP protocol standards:

1. **Tool Registration** - Tools are registered in `handle_list_tools()`
2. **Tool Execution** - Requests handled in `handle_call_tool()`
3. **Error Handling** - Consistent error format across all tools
4. **Async Support** - All operations are async for performance

### BigQuery Client

- Uses Application Default Credentials (ADC)
- Respects environment variables (BQ_PROJECT, BQ_LOCATION)
- All queries run with `dry_run=True`
- Cache disabled for accurate cost estimates

### Error Handling

Standard error format:
```python
{
    "error": {
        "code": "INVALID_SQL",
        "message": "Human-readable error",
        "location": {"line": 1, "column": 10},
        "details": []  # Optional
    }
}
```

## Contributing Guidelines

1. **Open an issue first** - Discuss major changes before implementing
2. **Follow existing patterns** - Maintain consistency with current code
3. **Add tests** - All new features need test coverage
4. **Update docs** - Keep documentation in sync with code
5. **One feature per PR** - Keep pull requests focused

## Release Process

1. Update version in `pyproject.toml` and `src/mcp_bigquery/__init__.py`
2. Update CHANGELOG in README.md
3. Create and push git tag
4. Build and publish to PyPI
5. Create GitHub release

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/caron14/mcp-bigquery/issues)
- **Discussions**: [GitHub Discussions](https://github.com/caron14/mcp-bigquery/discussions)
- **Documentation**: This guide and API reference

## License

MIT License - See LICENSE file for details