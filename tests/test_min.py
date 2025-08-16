"""Minimal tests for mcp-bigquery."""

import json
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys

# Ensure imports work correctly
def test_imports_before_tests():
    """Verify critical imports work before running other tests."""
    try:
        from google.auth.exceptions import DefaultCredentialsError
        from google.cloud import bigquery
        import mcp.server.stdio
        from mcp_bigquery import __version__
    except ImportError as e:
        pytest.fail(f"Critical import failed: {e}")

# Check if BigQuery credentials are available
HAS_CREDENTIALS = (
    os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") is not None
    or os.path.exists(os.path.expanduser("~/.config/gcloud/application_default_credentials.json"))
    or os.environ.get("GOOGLE_CLOUD_PROJECT") is not None
)

pytestmark = pytest.mark.skipif(
    not HAS_CREDENTIALS,
    reason="BigQuery credentials not available"
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
    
    result = await validate_sql(
        "SELECT * FROM table WHERE id = @id",
        params={"id": "123"}
    )
    
    # This will fail without a real table, but it should parse the parameter
    assert "isValid" in result


class TestWithoutCredentials:
    """Tests that run without BigQuery credentials."""
    
    def test_extract_error_location(self):
        """Test error location extraction from BigQuery error messages."""
        from mcp_bigquery.server import extract_error_location
        
        # Test with location
        error_msg = "Syntax error: Unexpected keyword WHERE at [3:15]"
        location = extract_error_location(error_msg)
        assert location == {"line": 3, "column": 15}
        
        # Test without location
        error_msg = "Syntax error: Unexpected keyword WHERE"
        location = extract_error_location(error_msg)
        assert location is None
    
    def test_build_query_parameters(self):
        """Test query parameter building."""
        from mcp_bigquery.server import build_query_parameters
        
        # Test with parameters
        params = {"name": "Alice", "age": 30}
        result = build_query_parameters(params)
        assert len(result) == 2
        
        # All should be STRING type initially
        for param in result:
            assert param.type_ == "STRING"
        
        # Test with None
        result = build_query_parameters(None)
        assert result == []
        
        # Test with empty dict
        result = build_query_parameters({})
        assert result == []
    
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test that list_tools returns the expected tools."""
        from mcp_bigquery.server import handle_list_tools
        
        tools = await handle_list_tools()
        assert len(tools) == 2
        
        tool_names = [tool.name for tool in tools]
        assert "bq_validate_sql" in tool_names
        assert "bq_dry_run_sql" in tool_names
        
        # Check tool schemas
        for tool in tools:
            assert tool.inputSchema["type"] == "object"
            assert "sql" in tool.inputSchema["properties"]
            assert "sql" in tool.inputSchema["required"]