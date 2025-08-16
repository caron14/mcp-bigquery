"""Pytest configuration and fixtures for mcp-bigquery tests."""

import os
import sys

import pytest


def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers",
        "requires_credentials: mark test as requiring BigQuery credentials",
    )
    config.addinivalue_line("markers", "unit: mark test as a unit test (no external dependencies)")
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test (requires BigQuery)",
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers and skip conditions."""

    # Check for credentials
    has_credentials = (
        os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") is not None
        or os.path.exists(
            os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
        )
        or os.environ.get("GOOGLE_CLOUD_PROJECT") is not None
    )

    skip_integration = pytest.mark.skip(reason="BigQuery credentials not available")

    for item in items:
        # Add markers based on test location
        if "test_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.requires_credentials)
            if not has_credentials:
                item.add_marker(skip_integration)
        elif "test_imports" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

        # Skip async tests if running in incompatible environment
        if "asyncio" in [mark.name for mark in item.iter_markers()]:
            if sys.version_info < (3, 9):
                item.add_marker(pytest.mark.skip(reason="Requires Python 3.9+ for async"))


@pytest.fixture(scope="session")
def test_project_id():
    """Provide a test project ID for BigQuery operations."""
    # Try to get from environment or use a default test project
    return os.environ.get("BQ_PROJECT", os.environ.get("GOOGLE_CLOUD_PROJECT"))


@pytest.fixture(scope="session")
def test_location():
    """Provide a test location for BigQuery operations."""
    return os.environ.get("BQ_LOCATION", "US")


@pytest.fixture
def mock_bigquery_client():
    """Provide a mock BigQuery client for unit tests."""
    from unittest.mock import MagicMock, Mock

    from google.cloud import bigquery

    mock_client = Mock(spec=bigquery.Client)
    mock_client.location = "US"
    mock_client.project = "test-project"

    # Mock query method
    mock_query_job = MagicMock()
    mock_query_job.total_bytes_processed = 1024
    mock_query_job.schema = [MagicMock(name="test_field", field_type="STRING", mode="NULLABLE")]
    mock_query_job.referenced_tables = []
    mock_client.query.return_value = mock_query_job

    return mock_client


@pytest.fixture
def sample_queries():
    """Provide sample SQL queries for testing."""
    return {
        "simple": "SELECT 1",
        "invalid": "SELECT FROM WHERE",
        "with_params": "SELECT * FROM table WHERE id = @id AND name = @name",
        "public_dataset": ("SELECT * FROM `bigquery-public-data.samples.shakespeare` LIMIT 10"),
        "aggregation": """
            SELECT
                corpus,
                COUNT(*) as count,
                SUM(word_count) as total
            FROM `bigquery-public-data.samples.shakespeare`
            GROUP BY corpus
        """,
        "cte": """
            WITH stats AS (
                SELECT
                    word,
                    SUM(word_count) as total
                FROM `bigquery-public-data.samples.shakespeare`
                GROUP BY word
            )
            SELECT* FROM stats WHERE total > 100
        """,
    }


@pytest.fixture
def environment_backup():
    """Backup and restore environment variables."""
    original_env = os.environ.copy()
    yield
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(autouse=True)
def check_imports():
    """Automatically check critical imports before each test."""
    try:
        # These imports should always work
        import mcp.server.stdio  # noqa: F401
        from google.auth.exceptions import DefaultCredentialsError  # noqa: F401
        from google.cloud import bigquery  # noqa: F401

        from mcp_bigquery import __version__  # noqa: F401
    except ImportError as e:
        pytest.skip(f"Required dependency not available: {e}")
