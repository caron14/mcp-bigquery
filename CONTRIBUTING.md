# Contributing to MCP BigQuery

First off, thank you for considering contributing to MCP BigQuery! It's people like you that make MCP BigQuery such a great tool for safe BigQuery exploration.

## 🎯 Project Philosophy

MCP BigQuery follows these core principles:
- **Safety First**: All BigQuery operations must be dry-run only
- **Type Safety**: Use type hints and validation everywhere
- **Clear Documentation**: Every function needs clear documentation
- **Comprehensive Testing**: All code must have tests

## 📋 How Can I Contribute?

### 🚦 Before You Start

**Important**: Before creating a pull request, please first open an issue to discuss your proposed changes. This helps:
- Ensure your contribution aligns with the project's direction
- Avoid duplicate work
- Get feedback on your approach before investing time in implementation
- Coordinate with other contributors who might be working on similar features

The only exceptions are:
- Obvious typo fixes
- Documentation improvements that don't change functionality
- Critical security fixes (though please still notify maintainers)

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples**
- **Include your environment details** (Python version, OS, etc.)
- **Attach relevant logs** (with sensitive data removed)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide a detailed description** of the suggested enhancement
- **Explain why this enhancement would be useful**
- **List any alternative solutions** you've considered

### Pull Requests

**Prerequisites**: Before submitting a pull request:
1. **Create an issue first** to discuss your proposed changes (unless it's a trivial fix)
2. **Wait for feedback** from maintainers on your issue
3. **Get approval** on your approach before starting implementation

Once approved:
- **Follow the style guides**
- **Include tests** for new functionality
- **Update documentation** as needed
- **Follow the commit message conventions**
- **Reference the issue** in your PR description (e.g., "Fixes #123")

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- Google Cloud SDK
- Git
- A Google Cloud Project with BigQuery API enabled

### Setting Up Your Development Environment

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/mcp-bigquery.git
   cd mcp-bigquery
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -e ".[dev]"
   # Or with uv
   uv pip install -e ".[dev]"
   ```

4. **Set up Google Cloud authentication**
   ```bash
   gcloud auth application-default login
   ```

5. **Configure environment variables**
   ```bash
   export BQ_PROJECT="your-test-project"
   export DEBUG=true
   ```

## 💻 Development Workflow

### Branch Strategy

- `main` - stable release branch
- `develop` - development branch (if used)
- `feature/*` - feature branches
- `fix/*` - bug fix branches
- `docs/*` - documentation branches

### Creating a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### Making Changes

1. **Write your code**
   - Follow the existing code structure
   - Add type hints to all functions
   - Handle errors with custom exceptions
   - Add logging where appropriate

2. **Write tests**
   ```bash
   # Run tests
   pytest tests/
   
   # Run specific test file
   pytest tests/test_features.py -v
   
   # Run with coverage
   pytest --cov=mcp_bigquery tests/
   ```

3. **Format your code**
   ```bash
   # Format with black
   black src/ tests/
   
   # Check with ruff
   ruff check src/ tests/
   
   # Sort imports
   isort src/ tests/
   ```

4. **Update documentation**
   - Update docstrings
   - Update README.md if needed
   - Update CHANGELOG.md

### Commit Message Convention

We follow the Conventional Commits specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build process or auxiliary tool changes

**Examples:**
```bash
feat(sql): add support for ARRAY and STRUCT types
fix(cache): resolve memory leak in LRU eviction
docs(readme): update installation instructions
test(validators): add tests for SQL validation
```

## 📝 Coding Standards

### Python Style Guide

We follow PEP 8 with these additions:
- Line length: 100 characters
- Use type hints for all function parameters and returns
- Use docstrings for all public functions

### Type Hints

```python
from typing import Optional, Dict, Any

def validate_sql(
    sql: str,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate BigQuery SQL syntax.
    
    Args:
        sql: The SQL query to validate
        params: Optional query parameters
        
    Returns:
        Dictionary with validation results
    """
    pass
```

### Error Handling

Use custom exceptions from `exceptions.py`:

```python
from mcp_bigquery.exceptions import SQLValidationError

try:
    # Your code
    pass
except BadRequest as e:
    raise SQLValidationError(
        "Invalid SQL syntax",
        location=(10, 15)
    )
```

### Logging

Use the configured logger:

```python
from mcp_bigquery.logging_config import get_logger

logger = get_logger(__name__)

logger.info("Processing request")
logger.error("Error occurred", extra={"error": str(e)})
```

## 🧪 Testing

### Writing Tests

- Place tests in `tests/` directory
- Use pytest for testing
- Mock external dependencies
- Test both success and failure cases

```python
import pytest
from unittest.mock import Mock, patch

class TestFeature:
    def test_success_case(self):
        """Test successful operation."""
        # Your test
        assert result == expected
    
    def test_failure_case(self):
        """Test error handling."""
        with pytest.raises(ExpectedException):
            # Your test
```

### Test Coverage

- Minimum coverage: 70%
- Critical paths must have 100% coverage
- All new code must include tests

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest --cov=mcp_bigquery --cov-report=html tests/

# Run specific test markers
pytest -m "not requires_credentials" tests/
```

## 🔒 Security

### Security Principles

1. **Never execute actual queries** - All operations must be dry-run
2. **Validate all inputs** - Use validators for user input
3. **Sanitize error messages** - Remove sensitive data from logs
4. **Handle credentials safely** - Never log or expose credentials

### Reporting Security Issues

**Do not** report security vulnerabilities through public GitHub issues. Instead, please email security concerns to the maintainers directly.

## 📦 Release Process

### Version Numbering

We use Semantic Versioning (SemVer):
- MAJOR version: Breaking changes
- MINOR version: New features (backward compatible)
- PATCH version: Bug fixes (backward compatible)

### Creating a Release

1. Update version in `src/mcp_bigquery/__init__.py`
2. Update version in `pyproject.toml`
3. Update CHANGELOG.md
4. Create release notes
5. Tag the release: `git tag v0.x.x`
6. Push tags: `git push --tags`

## 🤝 Code Review Process

### What We Look For

- **Correctness**: Does the code work as intended?
- **Safety**: Does it maintain dry-run only operations?
- **Tests**: Are there adequate tests?
- **Documentation**: Is the code well-documented?
- **Style**: Does it follow our coding standards?
- **Performance**: Are there any performance concerns?

### Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation is updated
- [ ] No sensitive data in code/logs
- [ ] Dry-run principle maintained
- [ ] Type hints added
- [ ] Error handling implemented

## 📚 Resources

### Documentation

- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [BigQuery Documentation](https://cloud.google.com/bigquery/docs)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

### Tools

- [Black](https://black.readthedocs.io/) - Code formatter
- [Ruff](https://docs.astral.sh/ruff/) - Linter
- [pytest](https://docs.pytest.org/) - Testing framework
- [mypy](http://mypy-lang.org/) - Type checker

## 🌟 Recognition

Contributors will be recognized in:
- Release notes
- README.md contributors section
- GitHub contributors page

## ❓ Questions?

Feel free to:
- Open a [GitHub Discussion](https://github.com/caron14/mcp-bigquery/discussions)
- Ask in issues (label as `question`)
- Contact maintainers directly

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to MCP BigQuery! 🎉