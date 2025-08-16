# Contributing Guide

Welcome to the MCP BigQuery contributing guide! We appreciate your interest in contributing to this project. This guide covers everything you need to know to make your first contribution.

## Quick Start for Contributors

### 1. Fork and Clone

```bash
# Fork on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/mcp-bigquery.git
cd mcp-bigquery

# Add upstream remote
git remote add upstream https://github.com/caron14/mcp-bigquery.git
```

### 2. Set Up Development Environment

```bash
# Install in development mode
uv pip install -e ".[dev]"

# Set up authentication
gcloud auth application-default login
export BQ_PROJECT="your-project-id"

# Verify setup
pytest tests/test_min.py::TestWithoutCredentials -v
```

### 3. Create Feature Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 4. Make Changes and Test

```bash
# Make your changes
# Add tests for new functionality

# Run tests
pytest tests/

# Check formatting
black src/ tests/
isort src/ tests/
```

### 5. Submit Pull Request

```bash
# Commit changes
git add .
git commit -m "feat: add your feature description"

# Push to your fork
git push origin feature/your-feature-name

# Create PR on GitHub
```

## Development Workflow

### Branch Strategy

```
main                    # Stable release branch
├── feature/new-tool    # New feature development
├── fix/bug-123         # Bug fixes
└── docs/update-guide   # Documentation updates
```

### Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Feature additions
git commit -m "feat: add support for array parameters"

# Bug fixes
git commit -m "fix: handle empty query strings gracefully"

# Documentation
git commit -m "docs: add troubleshooting section"

# Tests
git commit -m "test: add integration tests for error handling"

# Chores
git commit -m "chore: update dependencies"

# Breaking changes
git commit -m "feat!: change response format for cost estimation"
```

### Code Style and Standards

#### Python Code Standards

**Formatting**: Use Black with default settings

```bash
# Format all code
black src/ tests/

# Check formatting
black --check src/ tests/
```

**Import Sorting**: Use isort

```bash
# Sort imports
isort src/ tests/

# Check import order
isort --check-only src/ tests/
```

**Linting**: Use Ruff for fast linting

```bash
# Lint code
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/
```

#### Type Hints

Use type hints for all public functions:

```python
from typing import Dict, List, Optional, Any
from google.cloud import bigquery

async def validate_sql(
    sql: str, 
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Validate BigQuery SQL without executing it.
    
    Args:
        sql: The SQL query to validate
        params: Optional query parameters
        
    Returns:
        Validation result with isValid flag and optional error details
    """
    # Implementation here
```

#### Docstring Standards

Use Google-style docstrings:

```python
def calculate_cost_estimate(bytes_processed: int, price_per_tib: float) -> float:
    """Calculate USD cost estimate for BigQuery query.
    
    Args:
        bytes_processed: Number of bytes that would be processed
        price_per_tib: Price per TiB in USD
        
    Returns:
        Estimated cost in USD
        
    Raises:
        ValueError: If bytes_processed is negative
        
    Example:
        >>> calculate_cost_estimate(1073741824, 5.0)  # 1 GB at $5/TiB
        0.005
    """
    if bytes_processed < 0:
        raise ValueError("bytes_processed cannot be negative")
        
    tib_processed = bytes_processed / (1024 ** 4)
    return tib_processed * price_per_tib
```

### Testing Requirements

#### Test Coverage

All new features require:

- **Unit tests** in `TestWithoutCredentials` class
- **Integration tests** if touching BigQuery API
- **Docstring examples** that can be tested

#### Test Examples

**Unit Test for New Feature**:

```python
class TestWithoutCredentials:
    def test_new_feature_logic(self, mock_bigquery_client):
        """Test new feature logic without requiring credentials."""
        from mcp_bigquery.server import new_feature_function
        
        # Configure mock
        mock_bigquery_client.query.return_value = mock_result
        
        # Test the function
        result = new_feature_function("test input")
        
        # Verify behavior
        assert result["expected_field"] == "expected_value"
        mock_bigquery_client.query.assert_called_once()
```

**Integration Test**:

```python
@pytest.mark.integration
@pytest.mark.requires_credentials  
async def test_new_feature_integration():
    """Test new feature against real BigQuery API."""
    from mcp_bigquery.server import new_feature_function
    
    result = await new_feature_function("SELECT 1")
    assert result is not None
    # Verify real API behavior
```

### Documentation Requirements

#### Code Documentation

- **All public functions** must have docstrings
- **Complex logic** should have inline comments
- **API changes** must update relevant documentation

#### User Documentation

For user-facing changes, update:

- `README.md` - If changing installation or basic usage
- `docs/` - Detailed documentation for new features
- `examples/` - Code examples for new functionality

## Pull Request Process

### Before Submitting

#### 1. Run Full Test Suite

```bash
# Run all tests
pytest tests/

# Check specific areas
pytest tests/test_min.py::TestWithoutCredentials -v  # Unit tests
pytest tests/test_integration.py -v                  # Integration tests
```

#### 2. Verify Code Quality

```bash
# Format code
black src/ tests/
isort src/ tests/

# Check linting
ruff check src/ tests/

# Type checking (optional but recommended)
mypy src/mcp_bigquery/
```

#### 3. Update Documentation

```bash
# Build docs locally to verify
mkdocs serve

# Check for broken links
mkdocs build --strict
```

### PR Checklist

Use this checklist in your PR description:

```markdown
## Changes
- [ ] Brief description of changes
- [ ] Link to related issue (if applicable)

## Testing
- [ ] Unit tests pass: `pytest tests/test_min.py::TestWithoutCredentials`
- [ ] Integration tests pass: `pytest tests/test_integration.py` (if applicable)
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Code Quality
- [ ] Code formatted with Black: `black src/ tests/`
- [ ] Imports sorted with isort: `isort src/ tests/`
- [ ] Linting passes: `ruff check src/ tests/`
- [ ] Type hints added for new functions

## Documentation
- [ ] Docstrings added for new functions
- [ ] User documentation updated (if applicable)
- [ ] CHANGELOG.md updated (for releases)

## Breaking Changes
- [ ] No breaking changes
- [ ] Breaking changes documented and justified
```

### PR Review Process

#### What Reviewers Look For

1. **Functionality** - Does the code work as intended?
2. **Tests** - Are there adequate tests covering the changes?
3. **Code Quality** - Is the code clean, readable, and maintainable?
4. **Documentation** - Are changes properly documented?
5. **Breaking Changes** - Are any breaking changes necessary and justified?

#### Responding to Review Feedback

```bash
# Make requested changes
git add .
git commit -m "fix: address review feedback"

# Update your PR
git push origin feature/your-feature-name
```

#### Keeping PR Updated

```bash
# Sync with upstream main
git checkout main
git pull upstream main

# Rebase your feature branch
git checkout feature/your-feature-name
git rebase main

# Force push (since rebase changes history)
git push --force-with-lease origin feature/your-feature-name
```

## Types of Contributions

### 🐛 Bug Fixes

1. **Reproduce the bug** with a test case
2. **Fix the issue** with minimal changes
3. **Add regression test** to prevent recurrence

Example bug fix structure:

```python
def test_bug_reproduction(self):
    """Test case that reproduces the reported bug."""
    # This test should fail before the fix
    pass

def test_bug_fix_verification(self):
    """Test case that verifies the bug is fixed."""
    # This test should pass after the fix
    pass
```

### ✨ New Features

1. **Discuss the feature** in GitHub Issues first
2. **Design the API** before implementation
3. **Implement with tests** and documentation

Feature development checklist:

- [ ] Feature request issue created and discussed
- [ ] API design documented
- [ ] Unit tests written
- [ ] Integration tests added (if applicable)
- [ ] Documentation updated
- [ ] Examples provided

### 📚 Documentation

1. **Identify gaps** in current documentation
2. **Write clear, actionable content**
3. **Include working examples**

Documentation guidelines:

- **Be clear and concise**
- **Include practical examples**
- **Link to related concepts**
- **Test all code examples**

### 🧪 Tests

1. **Improve test coverage** for existing code
2. **Add edge case testing**
3. **Performance test for critical paths**

Test contribution areas:

- More unit test coverage
- Additional integration test scenarios
- Performance benchmarks
- Error condition testing

## Release Process

### Semantic Versioning

MCP BigQuery follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features, backwards compatible  
- **PATCH** (0.0.1): Bug fixes, backwards compatible

### Release Checklist

For maintainers preparing releases:

#### 1. Pre-release Testing

```bash
# Full test suite with fresh environment
python -m venv test-env
source test-env/bin/activate
pip install -e ".[dev]"
pytest tests/

# Test installation from package
pip install dist/mcp-bigquery-*.whl
mcp-bigquery --version
```

#### 2. Version Update

```bash
# Update version in both files
vim src/mcp_bigquery/__init__.py  # __version__ = "0.2.0"
vim pyproject.toml                # version = "0.2.0"
```

#### 3. Update Changelog

```markdown
## [0.2.0] - 2024-01-15

### Added
- New feature description
- Another new feature

### Changed
- Changed behavior description

### Fixed
- Bug fix description

### Deprecated
- Deprecated feature warning

### Removed
- Removed feature description
```

#### 4. Build and Publish

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build package
python -m build

# Test on TestPyPI first
python -m twine upload --repository testpypi dist/*

# Publish to PyPI
python -m twine upload dist/*
```

#### 5. Create Release

1. Create Git tag: `git tag -a v0.2.0 -m "Release v0.2.0"`
2. Push tag: `git push origin v0.2.0`
3. Create GitHub release with changelog

## Community Guidelines

### Code of Conduct

We follow the [Contributor Covenant](https://www.contributor-covenant.org/):

- **Be respectful** of different viewpoints and experiences
- **Accept constructive criticism** gracefully
- **Focus on what's best** for the community
- **Show empathy** towards other community members

### Communication Channels

- **GitHub Issues** - Bug reports, feature requests
- **GitHub Discussions** - General questions, ideas
- **Pull Requests** - Code review and collaboration

### Getting Help

#### For Contributors

- **Setup Issues** - Check [Development Setup](setup.md)
- **Testing Questions** - See [Testing Guide](testing.md)
- **General Questions** - Use GitHub Discussions

#### For Maintainers

- **Review Guidelines** - Focus on code quality and user impact
- **Release Coordination** - Follow semantic versioning
- **Community Management** - Be welcoming and helpful

## Recognition

### Contributors

All contributors are recognized in:

- `CONTRIBUTORS.md` file
- GitHub repository contributors page
- Release notes for significant contributions

### Types of Recognition

- **First-time contributors** - Welcome message and guidance
- **Regular contributors** - Maintainer invitation consideration
- **Significant contributions** - Special recognition in releases

## Advanced Contributing

### Performance Considerations

When contributing code that affects performance:

```python
# Measure performance impact
import time

def benchmark_function():
    start = time.time()
    # Your code here
    end = time.time()
    print(f"Execution time: {end - start:.4f}s")
```

### Security Considerations

- **Never commit credentials** or sensitive data
- **Validate all inputs** in public functions
- **Use secure defaults** for configuration options
- **Follow least privilege principle** for permissions

### Backwards Compatibility

When making changes:

1. **Preserve existing APIs** when possible
2. **Deprecate before removing** features
3. **Provide migration paths** for breaking changes
4. **Document compatibility** in changelog

### Integration with MCP Ecosystem

Consider impacts on:

- **MCP protocol compliance** - Follow MCP specifications
- **Client compatibility** - Test with different MCP clients
- **Tool interactions** - Ensure tools work independently

## Troubleshooting Contributions

### Common Issues

#### My tests are failing

```bash
# Check test environment
pytest tests/ -v

# Verify credentials (for integration tests)
gcloud auth application-default print-access-token

# Check imports
python -c "import mcp_bigquery; print('OK')"
```

#### My PR build is failing

1. **Check CI logs** for specific error messages
2. **Run tests locally** with same Python version
3. **Verify all files** are committed and pushed

#### Code review feedback

1. **Read feedback carefully** and ask for clarification
2. **Make requested changes** in new commits
3. **Respond to comments** to show you've addressed them

### Getting Unstuck

If you're stuck:

1. **Check existing issues** for similar problems
2. **Create a draft PR** to get early feedback
3. **Ask questions** in GitHub Discussions
4. **Break down the problem** into smaller pieces

## Next Steps

Ready to contribute? Here's how to get started:

1. **🍴 Fork the repository** on GitHub
2. **📚 Read the [Development Setup](setup.md)** guide
3. **🔍 Look for "good first issue"** labels
4. **💬 Join the discussion** in GitHub Issues

Thank you for contributing to MCP BigQuery! 🎉

## Resources

- **Project Repository**: https://github.com/caron14/mcp-bigquery
- **Documentation**: Available in `docs/` directory
- **Issue Tracker**: GitHub Issues
- **Discussions**: GitHub Discussions
- **MCP Specification**: https://modelcontextprotocol.io/

Happy contributing! 🚀