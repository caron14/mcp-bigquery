"""Test module imports and dependencies."""

import sys
from unittest.mock import patch

import pytest


class TestImports:
    """Test that all required modules can be imported correctly."""

    def test_google_auth_imports(self):
        """Test that google.auth modules are available and correct."""
        # This test would have caught our DefaultCredentialsError issue
        try:
            from google.auth.exceptions import DefaultCredentialsError

            assert DefaultCredentialsError is not None
        except ImportError as e:
            pytest.fail(
                f"Failed to import DefaultCredentialsError from " f"google.auth.exceptions: {e}"
            )

        # Verify the wrong import path doesn't work
        with pytest.raises(ImportError):
            from google.cloud.exceptions import DefaultCredentialsError

    def test_google_cloud_bigquery_imports(self):
        """Test that google-cloud-bigquery is properly installed."""
        try:
            from google.cloud import bigquery

            assert bigquery.Client is not None
        except ImportError as e:
            pytest.fail(f"Failed to import google.cloud.bigquery: {e}")

    def test_mcp_imports(self):
        """Test that MCP package is properly installed."""
        try:
            import mcp.server.stdio  # noqa: F401
            import mcp.types  # noqa: F401
            from mcp.server import NotificationOptions, Server  # noqa: F401

            assert Server is not None
        except ImportError as e:
            pytest.fail(f"Failed to import MCP modules: {e}")

    def test_package_structure(self):
        """Test that our package structure is correct."""
        try:
            # Test main package import
            import mcp_bigquery

            assert hasattr(mcp_bigquery, "__version__")

            # Test submodule imports
            from mcp_bigquery import dry_run_sql, server, validate_sql

            assert server is not None
            assert validate_sql is not None
            assert dry_run_sql is not None

            # Test internal modules
            from mcp_bigquery.bigquery_client import get_bigquery_client
            from mcp_bigquery.server import (  # noqa: F401
                build_query_parameters,
                extract_error_location,
                handle_call_tool,
                handle_list_tools,
            )

            assert get_bigquery_client is not None
            assert extract_error_location is not None

        except ImportError as e:
            pytest.fail(f"Failed to import package modules: {e}")

    def test_console_script_entry_point(self):
        """Test that the console script entry point exists."""
        try:
            from mcp_bigquery.__main__ import main

            assert callable(main)
        except ImportError as e:
            pytest.fail(f"Failed to import console script entry point: {e}")

    def test_async_compatibility(self):
        """Test that asyncio is properly configured."""
        import asyncio

        # Ensure we're using Python 3.9+ for proper async support
        assert sys.version_info >= (3, 9), "Python 3.9+ is required"

        # Test that we can create an event loop
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.close()
        except Exception as e:
            pytest.fail(f"Failed to create asyncio event loop: {e}")

    def test_environment_variables(self):
        """Test that environment variables can be accessed."""
        import os

        # These are optional, so we just test that we can access them
        os.environ.get("BQ_PROJECT")  # noqa: F841
        os.environ.get("BQ_LOCATION")  # noqa: F841
        price_per_tib = os.environ.get("SAFE_PRICE_PER_TIB")

        # If SAFE_PRICE_PER_TIB is set, verify it's a valid float
        if price_per_tib:
            try:
                float(price_per_tib)
            except ValueError:
                pytest.fail(f"SAFE_PRICE_PER_TIB must be a valid float, got: " f"{price_per_tib}")


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_missing_credentials_error_message(self):
        """Test that missing credentials produces a helpful error message."""
        from google.auth.exceptions import DefaultCredentialsError

        from mcp_bigquery.bigquery_client import get_bigquery_client
        from mcp_bigquery.exceptions import AuthenticationError

        with patch("google.cloud.bigquery.Client") as mock_client:
            mock_client.side_effect = DefaultCredentialsError("No credentials")

            with pytest.raises(AuthenticationError) as exc_info:
                get_bigquery_client(use_cache=False)

            assert "gcloud auth application-default login" in str(exc_info.value)

    def test_error_location_extraction(self):
        """Test various error message formats for location extraction."""
        from mcp_bigquery.server import extract_error_location

        test_cases = [
            # (input_message, expected_result)
            ("Syntax error at [1:5]", {"line": 1, "column": 5}),
            ("Error at [10:20]", {"line": 10, "column": 20}),
            (
                "Multiple [1:2] and [3:4]",
                {"line": 1, "column": 2},
            ),  # First match
            ("No location in this message", None),
            (
                "[999:888] at the beginning",
                {"line": 999, "column": 888},
            ),
            ("", None),
        ]

        for message, expected in test_cases:
            result = extract_error_location(message)
            assert result == expected, f"Failed for message: {message}"

    def test_query_parameter_building(self):
        """Test query parameter building with various inputs."""
        from mcp_bigquery.server import build_query_parameters

        # Test with None
        result = build_query_parameters(None)
        assert result == []

        # Test with empty dict
        result = build_query_parameters({})
        assert result == []

        # Test with various data types
        params = {
            "string_param": "hello",
            "int_param": 42,
            "float_param": 3.14,
            "bool_param": True,
            "none_param": None,
        }
        result = build_query_parameters(params)

        assert len(result) == 5
        for param in result:
            assert param.type_ == "STRING"
            assert param.name in params
            assert param.value == str(params[param.name])
