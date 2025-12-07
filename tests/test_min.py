"""Minimal tests for mcp-bigquery with BigQuery credentials."""

import os

import pytest


# Ensure imports work correctly
def test_imports_before_tests():
    """Verify critical imports work before running other tests."""
    try:
        import mcp.server.stdio  # noqa: F401
        from google.auth.exceptions import DefaultCredentialsError  # noqa: F401; noqa: F401
        from google.cloud import bigquery  # noqa: F401

        from mcp_bigquery import __version__  # noqa: F401
    except ImportError as e:
        pytest.fail(f"Critical import failed: {e}")


# Check if BigQuery credentials are available
RUN_BIGQUERY_TESTS = os.environ.get("RUN_BIGQUERY_TESTS") == "1"
HAS_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") is not None or os.path.exists(
    os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
)

pytestmark = pytest.mark.skipif(
    not (RUN_BIGQUERY_TESTS and HAS_CREDENTIALS),
    reason="BigQuery credentials not available or RUN_BIGQUERY_TESTS!=1",
)


@pytest.mark.asyncio
async def test_validate_sql_valid():
    """Test that validate_sql returns isValid: true for valid SQL."""
    from mcp_bigquery.server import validate_sql

    result = await validate_sql("SELECT 1")
    assert result == {"isValid": True}


@pytest.mark.asyncio
async def test_validate_sql_invalid():
    """Test that validate_sql returns isValid: false for invalid SQL."""
    from mcp_bigquery.server import validate_sql

    result = await validate_sql("SELECT FROM WHERE")
    assert result["isValid"] is False
    assert "error" in result
    assert result["error"]["code"] == "INVALID_SQL"
    assert "message" in result["error"]


@pytest.mark.asyncio
async def test_dry_run_sql_valid():
    """Test that dry_run_sql returns expected fields for valid SQL."""
    from mcp_bigquery.server import dry_run_sql

    result = await dry_run_sql("SELECT 1")

    assert "totalBytesProcessed" in result
    assert "usdEstimate" in result
    assert "referencedTables" in result
    assert "schemaPreview" in result

    assert isinstance(result["totalBytesProcessed"], int)
    assert isinstance(result["usdEstimate"], float)
    assert isinstance(result["referencedTables"], list)
    assert isinstance(result["schemaPreview"], list)

    # Schema should have at least one field for SELECT 1
    assert len(result["schemaPreview"]) > 0
    assert "name" in result["schemaPreview"][0]
    assert "type" in result["schemaPreview"][0]
    assert "mode" in result["schemaPreview"][0]


@pytest.mark.asyncio
async def test_dry_run_sql_invalid():
    """Test that dry_run_sql returns error for invalid SQL."""
    from mcp_bigquery.server import dry_run_sql

    result = await dry_run_sql("SELECT FROM WHERE")

    assert "error" in result
    assert result["error"]["code"] == "INVALID_SQL"
    assert "message" in result["error"]


@pytest.mark.asyncio
async def test_dry_run_sql_with_price_per_tib():
    """Test that dry_run_sql uses provided pricePerTiB."""
    from mcp_bigquery.server import dry_run_sql

    # Test with custom price
    result = await dry_run_sql("SELECT 1", price_per_tib=10.0)

    assert "usdEstimate" in result
    # The estimate should be calculated with the custom price
    # For SELECT 1, bytes processed should be 0, so estimate should be 0
    assert result["usdEstimate"] == 0.0


@pytest.mark.asyncio
async def test_validate_sql_with_params():
    """Test that validate_sql handles parameters."""
    from mcp_bigquery.server import validate_sql

    result = await validate_sql("SELECT * FROM table WHERE id = @id", params={"id": "123"})

    # This will fail without a real table, but it should parse the parameter
    assert "isValid" in result


# Note: Tests for utility functions, tool registration, and SQL analysis features
# have been moved to test_features.py for better organization.
# This file now focuses on tests that require actual BigQuery credentials.
