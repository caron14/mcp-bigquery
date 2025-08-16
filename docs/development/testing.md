# Testing Guide

MCP BigQuery uses a comprehensive testing strategy to ensure reliability across different environments and use cases. This guide covers running tests, writing new tests, and understanding the test structure.

## Test Architecture

### Test Organization

```
tests/
├── conftest.py           # Pytest configuration and fixtures
├── test_min.py          # Minimal tests with TestWithoutCredentials
├── test_imports.py      # Import validation tests
└── test_integration.py  # BigQuery API integration tests
```

### Test Categories

| Category | Purpose | Requirements | Markers |
|----------|---------|--------------|---------|
| **Unit Tests** | Test individual components in isolation | None | `@pytest.mark.unit` |
| **Integration Tests** | Test with real BigQuery API | Credentials | `@pytest.mark.integration` |
| **Import Tests** | Validate all imports work | Basic deps | None |

### Automatic Test Selection

Tests are automatically categorized and run based on available credentials:

- **With credentials**: All tests run including integration tests
- **Without credentials**: Only unit tests and import tests run
- **Missing dependencies**: Tests are skipped with helpful messages

## Running Tests

### Quick Test Commands

```bash
# Run all available tests
pytest tests/

# Run only unit tests (no credentials needed)
pytest tests/test_min.py::TestWithoutCredentials

# Run with verbose output
pytest tests/ -v

# Run specific test
pytest tests/test_min.py::TestWithoutCredentials::test_extract_error_location -v

# Run with coverage
pytest --cov=mcp_bigquery tests/
```

### Test Environment Setup

#### For Unit Tests Only

No setup required! Unit tests use mocks and don't need credentials.

```bash
# Just run the tests
pytest tests/test_min.py::TestWithoutCredentials
```

#### For Integration Tests

Set up BigQuery credentials:

```bash
# Option 1: Application Default Credentials
gcloud auth application-default login

# Option 2: Service Account Key
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json

# Set project (optional)
export BQ_PROJECT="your-project-id"

# Run all tests
pytest tests/
```

### Test Output Examples

#### Successful Unit Test Run

```bash
$ pytest tests/test_min.py::TestWithoutCredentials -v

tests/test_min.py::TestWithoutCredentials::test_extract_error_location PASSED
tests/test_min.py::TestWithoutCredentials::test_format_error_response PASSED
tests/test_min.py::TestWithoutCredentials::test_get_bigquery_client_mock PASSED
tests/test_min.py::TestWithoutCredentials::test_validate_sql_mock PASSED
tests/test_min.py::TestWithoutCredentials::test_dry_run_sql_mock PASSED

=============================== 5 passed in 0.12s ===============================
```

#### Integration Test with Credentials

```bash
$ pytest tests/test_integration.py -v

tests/test_integration.py::test_bigquery_connection PASSED
tests/test_integration.py::test_validate_simple_query PASSED
tests/test_integration.py::test_validate_invalid_query PASSED
tests/test_integration.py::test_dry_run_public_dataset PASSED
tests/test_integration.py::test_dry_run_with_parameters PASSED

=============================== 5 passed in 3.45s ===============================
```

#### Skipped Tests (No Credentials)

```bash
$ pytest tests/test_integration.py -v

tests/test_integration.py::test_bigquery_connection SKIPPED (BigQuery credentials not available)
tests/test_integration.py::test_validate_simple_query SKIPPED (BigQuery credentials not available)

=============================== 2 skipped in 0.05s ===============================
```

## Test Structure Deep Dive

### Test Configuration (conftest.py)

The `conftest.py` file provides:

#### Automatic Credential Detection

```python
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers and skip conditions."""
    
    # Check for credentials
    has_credentials = (
        os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") is not None
        or os.path.exists(os.path.expanduser("~/.config/gcloud/application_default_credentials.json"))
        or os.environ.get("GOOGLE_CLOUD_PROJECT") is not None
    )
```

#### Useful Fixtures

```python
@pytest.fixture
def mock_bigquery_client():
    """Provide a mock BigQuery client for unit tests."""
    # Returns fully mocked BigQuery client

@pytest.fixture
def sample_queries():
    """Provide sample SQL queries for testing."""
    # Returns dict with various query types

@pytest.fixture
def test_project_id():
    """Provide a test project ID for BigQuery operations."""
    # Returns project ID from environment
```

### Unit Tests (test_min.py)

#### TestWithoutCredentials Class

Contains tests that don't require BigQuery credentials:

```python
class TestWithoutCredentials:
    """Tests that don't require BigQuery credentials."""
    
    def test_extract_error_location(self):
        """Test error location extraction from BigQuery messages."""
        # Tests regex parsing of error messages
    
    def test_format_error_response(self):
        """Test error response formatting."""
        # Tests error structure creation
    
    def test_get_bigquery_client_mock(self, mock_bigquery_client):
        """Test BigQuery client creation with mocks."""
        # Tests client creation logic
```

#### Key Test Patterns

```python
# Testing error extraction
def test_extract_error_location(self):
    from mcp_bigquery.server import extract_error_location
    
    # Test cases with expected locations
    test_cases = [
        ("Syntax error at [3:15]", (3, 15)),
        ("Error at [1:1]", (1, 1)),
        ("No location info", None),
    ]
    
    for message, expected in test_cases:
        result = extract_error_location(message)
        assert result == expected

# Testing with mocks
def test_validate_sql_mock(self, mock_bigquery_client):
    import asyncio
    from mcp_bigquery.server import validate_sql
    
    # Mock successful validation
    mock_bigquery_client.query.return_value = None
    
    result = asyncio.run(validate_sql("SELECT 1", {}))
    assert result["isValid"] is True
```

### Integration Tests (test_integration.py)

#### Real BigQuery API Testing

```python
@pytest.mark.integration
@pytest.mark.requires_credentials
async def test_validate_simple_query():
    """Test validating a simple query against BigQuery."""
    from mcp_bigquery.server import validate_sql
    
    result = await validate_sql("SELECT 1", {})
    assert result["isValid"] is True

@pytest.mark.integration  
@pytest.mark.requires_credentials
async def test_dry_run_public_dataset():
    """Test dry-run against a public dataset."""
    from mcp_bigquery.server import dry_run_sql
    
    sql = "SELECT * FROM `bigquery-public-data.samples.shakespeare` LIMIT 10"
    result = await dry_run_sql(sql, {})
    
    assert "totalBytesProcessed" in result
    assert "usdEstimate" in result
    assert "referencedTables" in result
    assert result["usdEstimate"] >= 0
```

#### Testing Error Conditions

```python
async def test_validate_invalid_query():
    """Test validation of invalid SQL."""
    from mcp_bigquery.server import validate_sql
    
    result = await validate_sql("SELECT FROM WHERE", {})
    
    assert result["isValid"] is False
    assert "error" in result
    assert result["error"]["code"] == "INVALID_SQL"
    assert "location" in result["error"]
```

## Writing New Tests

### Unit Test Guidelines

#### 1. Use TestWithoutCredentials for Credential-Free Tests

```python
class TestWithoutCredentials:
    def test_new_feature(self, mock_bigquery_client):
        """Test new feature without requiring credentials."""
        # Your test logic here
        pass
```

#### 2. Mock External Dependencies

```python
def test_bigquery_operation(self, mock_bigquery_client):
    """Test BigQuery operation with mocked client."""
    from mcp_bigquery.server import some_function
    
    # Configure mock
    mock_bigquery_client.query.return_value.total_bytes_processed = 1024
    
    # Test the function
    result = some_function(mock_bigquery_client, "SELECT 1")
    
    # Verify behavior
    assert result is not None
    mock_bigquery_client.query.assert_called_once()
```

#### 3. Test Error Conditions

```python
def test_error_handling(self, mock_bigquery_client):
    """Test error handling in specific scenarios."""
    from google.cloud.exceptions import BadRequest
    from mcp_bigquery.server import validate_sql
    
    # Configure mock to raise exception
    mock_bigquery_client.query.side_effect = BadRequest("Test error")
    
    # Test error handling
    result = asyncio.run(validate_sql("SELECT 1", {}))
    assert result["isValid"] is False
    assert "error" in result
```

### Integration Test Guidelines

#### 1. Mark with Appropriate Decorators

```python
@pytest.mark.integration
@pytest.mark.requires_credentials
async def test_real_bigquery_operation():
    """Test operation against real BigQuery API."""
    # Your test logic here
    pass
```

#### 2. Use Public Datasets

```python
async def test_with_public_data():
    """Test using BigQuery public datasets."""
    from mcp_bigquery.server import dry_run_sql
    
    # Use well-known public dataset
    sql = "SELECT * FROM `bigquery-public-data.samples.shakespeare` LIMIT 5"
    result = await dry_run_sql(sql, {})
    
    # Verify expected results
    assert result["totalBytesProcessed"] > 0
    assert len(result["referencedTables"]) == 1
    assert result["referencedTables"][0]["project"] == "bigquery-public-data"
```

#### 3. Test Parameter Handling

```python
async def test_parameterized_query():
    """Test parameterized query validation."""
    from mcp_bigquery.server import validate_sql
    
    sql = "SELECT * FROM `bigquery-public-data.samples.shakespeare` WHERE word = @word"
    params = {"word": "love"}
    
    result = await validate_sql(sql, params)
    assert result["isValid"] is True
```

### Test Data and Fixtures

#### Using Sample Queries Fixture

```python
def test_with_sample_queries(self, sample_queries):
    """Test using predefined sample queries."""
    simple_query = sample_queries["simple"]
    invalid_query = sample_queries["invalid"]
    
    # Test with different query types
    assert simple_query == "SELECT 1"
    assert "SELECT FROM WHERE" in invalid_query
```

#### Creating Custom Fixtures

```python
@pytest.fixture
def complex_query():
    """Provide a complex query for testing."""
    return """
    WITH user_stats AS (
        SELECT user_id, COUNT(*) as order_count
        FROM orders
        GROUP BY user_id
    )
    SELECT * FROM user_stats WHERE order_count > 10
    """

def test_complex_query_validation(self, complex_query):
    """Test validation of complex queries."""
    # Use the fixture
    pass
```

## Testing Best Practices

### 1. Test Isolation

Each test should be independent:

```python
def test_feature_a(self):
    # Don't depend on test_feature_b
    pass

def test_feature_b(self):
    # Don't depend on test_feature_a
    pass
```

### 2. Clear Test Names

Use descriptive names that explain what's being tested:

```python
# Good
def test_validate_sql_returns_error_for_syntax_error(self):
    pass

# Bad
def test_sql_validation(self):
    pass
```

### 3. Test Edge Cases

```python
def test_error_location_extraction_edge_cases(self):
    """Test error location extraction with various message formats."""
    from mcp_bigquery.server import extract_error_location
    
    # Test edge cases
    assert extract_error_location("") is None
    assert extract_error_location("No bracket info") is None
    assert extract_error_location("[invalid:format]") is None
    assert extract_error_location("[1:2] valid format") == (1, 2)
```

### 4. Use Appropriate Assertions

```python
# Test specific values
assert result["isValid"] is True
assert result["usdEstimate"] == 0.005

# Test structure
assert "error" in result
assert len(result["referencedTables"]) > 0

# Test types
assert isinstance(result["totalBytesProcessed"], int)
assert isinstance(result["schemaPreview"], list)
```

## Continuous Integration

### GitHub Actions

The project uses GitHub Actions for automated testing:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.10, 3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -e ".[dev]"
    
    - name: Run unit tests
      run: |
        pytest tests/test_min.py::TestWithoutCredentials -v
    
    - name: Run integration tests
      env:
        GOOGLE_APPLICATION_CREDENTIALS: ${{ secrets.GCP_SA_KEY }}
        BQ_PROJECT: ${{ secrets.BQ_PROJECT }}
      run: |
        pytest tests/test_integration.py -v
      if: env.GOOGLE_APPLICATION_CREDENTIALS != ''
```

### Local Pre-commit Hooks

Set up pre-commit hooks to run tests before commits:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

Example `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest-unit
        name: pytest-unit
        entry: pytest tests/test_min.py::TestWithoutCredentials
        language: system
        pass_filenames: false
```

## Troubleshooting Tests

### Common Issues

#### "No module named 'mcp_bigquery'"

**Solution**: Install in development mode
```bash
pip install -e ".[dev]"
```

#### Integration tests are skipped

**Solution**: Set up BigQuery credentials
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

#### Mock assertions failing

**Solution**: Check mock configuration
```python
# Verify mock was called
mock_client.query.assert_called_once()

# Check call arguments
mock_client.query.assert_called_with(
    expected_query,
    job_config=ANY
)
```

### Debug Test Failures

#### Run with detailed output

```bash
# Verbose output
pytest tests/ -v -s

# Show local variables on failure
pytest tests/ --tb=long

# Drop into debugger on failure
pytest tests/ --pdb
```

#### Log debugging information

```python
import logging
logging.basicConfig(level=logging.DEBUG)

def test_with_logging():
    logger = logging.getLogger(__name__)
    logger.debug("Test debug information")
    # Your test logic
```

## Test Coverage

### Measuring Coverage

```bash
# Run with coverage report
pytest --cov=mcp_bigquery tests/

# Generate HTML report
pytest --cov=mcp_bigquery --cov-report=html tests/

# View report
open htmlcov/index.html
```

### Coverage Goals

- **Unit Tests**: 90%+ coverage for core logic
- **Integration Tests**: Cover main user workflows
- **Error Handling**: Test all error paths

### Coverage Example Output

```
Name                                 Stmts   Miss  Cover
--------------------------------------------------------
src/mcp_bigquery/__init__.py             2      0   100%
src/mcp_bigquery/__main__.py             8      0   100%
src/mcp_bigquery/bigquery_client.py    25      2    92%
src/mcp_bigquery/server.py             67      5    93%
--------------------------------------------------------
TOTAL                                  102      7    93%
```

## Next Steps

Now that you understand the testing framework:

1. **[Contributing Guide](contributing.md)** - Learn the full contribution workflow
2. **[API Reference](../api-reference/index.md)** - Understand the codebase structure
3. **Practice** - Write tests for a new feature or fix

Remember: Good tests are documentation for your code! 📝