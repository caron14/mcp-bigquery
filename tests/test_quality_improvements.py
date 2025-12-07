"""Tests for code quality improvements."""

import asyncio
import time
from unittest.mock import Mock, patch

import pytest


# Test imports of new modules
def test_new_module_imports():
    """Test that all new modules can be imported."""
    from mcp_bigquery import (
        cache,
        config,
        constants,
        exceptions,
        logging_config,
        types,
        utils,
        validators,
    )

    assert types is not None
    assert exceptions is not None
    assert config is not None
    assert constants is not None
    assert logging_config is not None
    assert utils is not None
    assert validators is not None
    assert cache is not None


class TestExceptions:
    """Test custom exception classes."""

    def test_mcp_bigquery_error(self):
        """Test base MCPBigQueryError."""
        from mcp_bigquery.exceptions import MCPBigQueryError

        error = MCPBigQueryError("Test error", code="TEST_ERROR", details={"key": "value"})
        assert str(error) == "Test error"
        assert error.code == "TEST_ERROR"
        assert error.details == {"key": "value"}

        error_dict = error.to_dict()
        assert error_dict["code"] == "TEST_ERROR"
        assert error_dict["message"] == "Test error"
        assert error_dict["details"] == {"key": "value"}

    def test_sql_validation_error(self):
        """Test SQLValidationError with location."""
        from mcp_bigquery.exceptions import SQLValidationError

        error = SQLValidationError("Syntax error", location=(10, 15))
        assert error.code == "INVALID_SQL"
        assert error.location == (10, 15)

        error_dict = error.to_dict()
        assert error_dict["location"] == {"line": 10, "column": 15}

    def test_table_not_found_error(self):
        """Test TableNotFoundError."""
        from mcp_bigquery.exceptions import TableNotFoundError

        error = TableNotFoundError("my_table", "my_dataset", "my_project")
        assert "my_project.my_dataset.my_table" in str(error)
        assert error.code == "TABLE_NOT_FOUND"

    def test_invalid_parameter_error(self):
        """Test InvalidParameterError."""
        from mcp_bigquery.exceptions import InvalidParameterError

        error = InvalidParameterError("sql", "Query is too long", expected_type="string")
        assert "Invalid parameter 'sql'" in str(error)
        assert error.code == "INVALID_PARAMETER"
        assert error.details["expected_type"] == "string"


class TestConfig:
    """Test configuration management."""

    def test_config_from_env(self, monkeypatch):
        """Test loading configuration from environment."""
        from mcp_bigquery.config import Config

        monkeypatch.setenv("BQ_PROJECT", "test-project")
        monkeypatch.setenv("BQ_LOCATION", "us-central1")
        monkeypatch.setenv("SAFE_PRICE_PER_TIB", "6.5")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("MAX_RESULTS", "500")

        config = Config.from_env()
        assert config.project_id == "test-project"
        assert config.location == "us-central1"
        assert config.price_per_tib == 6.5
        assert config.debug is True
        assert config.max_results == 500

    def test_config_validation(self):
        """Test configuration validation."""
        from mcp_bigquery.config import Config
        from mcp_bigquery.exceptions import ConfigurationError

        # Invalid price_per_tib
        config = Config(price_per_tib=-1)
        with pytest.raises(ConfigurationError, match="price_per_tib must be positive"):
            config.validate()

        # Invalid log_level
        config = Config(log_level="INVALID")
        with pytest.raises(ConfigurationError, match="Invalid log_level"):
            config.validate()

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        from mcp_bigquery.config import Config

        config = Config(project_id="test", location="US")
        config_dict = config.to_dict()

        assert config_dict["project_id"] == "test"
        assert config_dict["location"] == "US"
        assert "price_per_tib" in config_dict
        assert "max_results" in config_dict


class TestUtils:
    """Test utility functions."""

    def test_extract_error_location(self):
        """Test extracting error location from message."""
        from mcp_bigquery.utils import extract_error_location

        # With location
        error_msg = "Syntax error at [10:15]: unexpected token"
        location = extract_error_location(error_msg)
        assert location == {"line": 10, "column": 15}

        # Without location
        error_msg = "Table not found"
        location = extract_error_location(error_msg)
        assert location is None

    def test_format_bytes(self):
        """Test formatting bytes to human-readable string."""
        from mcp_bigquery.utils import format_bytes

        assert format_bytes(500) == "500 bytes"
        assert format_bytes(1024) == "1.00 KiB"
        assert format_bytes(1024 * 1024) == "1.00 MiB"
        assert format_bytes(1024 * 1024 * 1024) == "1.00 GiB"
        assert format_bytes(1024 * 1024 * 1024 * 1024) == "1.00 TiB"

    def test_calculate_cost_estimate(self):
        """Test cost calculation."""
        from mcp_bigquery.constants import BYTES_PER_TIB
        from mcp_bigquery.utils import calculate_cost_estimate

        # 1 TiB at $5/TiB
        cost = calculate_cost_estimate(BYTES_PER_TIB, price_per_tib=5.0)
        assert cost == 5.0

        # 0.5 TiB at $10/TiB
        cost = calculate_cost_estimate(BYTES_PER_TIB // 2, price_per_tib=10.0)
        assert cost == 5.0

        # Minimum billing (10 MB)
        cost = calculate_cost_estimate(1024, price_per_tib=5.0)
        assert cost > 0  # Should use minimum billing

    def test_sanitize_table_reference(self):
        """Test sanitizing table references."""
        from mcp_bigquery.utils import sanitize_table_reference

        # Clean reference
        assert sanitize_table_reference("project.dataset.table") == "project.dataset.table"

        # With backticks
        assert sanitize_table_reference("`project`.`dataset`.`table`") == "project.dataset.table"

        # With special characters
        result = sanitize_table_reference("my-project.my_dataset.table-1")
        assert result == "my-project.my_dataset.table-1"

    def test_truncate_string(self):
        """Test string truncation."""
        from mcp_bigquery.utils import truncate_string

        # Short string
        assert truncate_string("short", 10) == "short"

        # Long string
        assert truncate_string("This is a very long string", 10) == "This is..."
        assert truncate_string("This is a very long string", 15, " [...]") == "This is a [...]"


class TestValidators:
    """Test input validation models."""

    def test_sql_validation_request(self):
        """Test SQLValidationRequest validation."""
        from mcp_bigquery.validators import SQLValidationRequest

        # Valid request
        request = SQLValidationRequest(sql="SELECT 1", params={"id": "123"})
        assert request.sql == "SELECT 1"
        assert request.params == {"id": "123"}

        # Empty SQL
        with pytest.raises(ValueError):
            SQLValidationRequest(sql="", params=None)

        # Whitespace only SQL
        with pytest.raises(ValueError):
            SQLValidationRequest(sql="   \n\t  ", params=None)

        # Invalid parameter name
        with pytest.raises(ValueError):
            SQLValidationRequest(sql="SELECT 1", params={"123invalid": "value"})

    def test_list_tables_request(self):
        """Test ListTablesRequest validation."""
        from mcp_bigquery.validators import ListTablesRequest

        # Valid request
        request = ListTablesRequest(dataset_id="my_dataset", table_type_filter=["TABLE", "VIEW"])
        assert request.dataset_id == "my_dataset"
        assert request.table_type_filter == ["TABLE", "VIEW"]

        # Invalid table type
        with pytest.raises(ValueError):
            ListTablesRequest(dataset_id="my_dataset", table_type_filter=["INVALID_TYPE"])

    def test_query_info_schema_request(self):
        """Test QueryInfoSchemaRequest validation."""
        from mcp_bigquery.validators import QueryInfoSchemaRequest

        # Valid standard query
        request = QueryInfoSchemaRequest(query_type="tables", dataset_id="my_dataset", limit=50)
        assert request.query_type == "tables"
        assert request.limit == 50

        # Custom query without custom_query
        with pytest.raises(ValueError, match="custom_query is required"):
            QueryInfoSchemaRequest(query_type="custom", dataset_id="my_dataset")

        # Non-custom with custom_query
        with pytest.raises(ValueError, match="custom_query should only be provided"):
            QueryInfoSchemaRequest(
                query_type="tables", dataset_id="my_dataset", custom_query="SELECT * FROM tables"
            )


class TestCache:
    """Test caching functionality."""

    def test_cache_entry(self):
        """Test CacheEntry behavior."""
        from mcp_bigquery.cache import CacheEntry

        entry = CacheEntry("test_value", ttl=1)
        assert entry.value == "test_value"
        assert not entry.is_expired()
        assert entry.access_count == 0

        # Access the entry
        value = entry.access()
        assert value == "test_value"
        assert entry.access_count == 1

        # Test expiration
        time.sleep(1.1)
        assert entry.is_expired()

    def test_cache_operations(self):
        """Test Cache operations."""
        from mcp_bigquery.cache import Cache

        cache = Cache(max_size=3, default_ttl=10)

        # Set and get
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # Miss
        assert cache.get("nonexistent") is None

        # Delete
        assert cache.delete("key1") is True
        assert cache.get("key1") is None
        assert cache.delete("nonexistent") is False

        # LRU eviction
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1 and key2 to make key3 LRU
        cache.get("key1")
        cache.get("key2")

        # Adding key4 should evict key3
        cache.set("key4", "value4")
        assert cache.get("key3") is None
        assert cache.get("key1") == "value1"
        assert cache.get("key4") == "value4"

    def test_cache_stats(self):
        """Test cache statistics."""
        from mcp_bigquery.cache import Cache

        cache = Cache()

        # Generate some activity
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        cache.get("key1")  # Hit

        stats = cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 2 / 3
        assert stats["size"] == 1

    def test_bigquery_client_cache(self):
        """Test BigQueryClientCache."""
        from mcp_bigquery.cache import BigQueryClientCache

        with patch("mcp_bigquery.clients.factory._instantiate_client") as mock_builder:
            mock_client = Mock()
            mock_builder.return_value = mock_client

            cache = BigQueryClientCache()

            # First call creates client
            client1 = cache.get_client("project1", "US")
            assert mock_builder.called

            # Second call reuses client
            mock_builder.reset_mock()
            client2 = cache.get_client("project1", "US")
            assert not mock_builder.called
            assert client1 is client2

            # Different project creates new client
            cache.get_client("project2", "US")
            assert mock_builder.called


class TestLogging:
    """Test logging configuration."""

    def test_json_formatter(self):
        """Test JSONFormatter."""
        import json
        import logging

        from mcp_bigquery.logging_config import JSONFormatter

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert data["module"] == "test"
        assert "timestamp" in data

    def test_setup_logging_uses_stderr(self, capsys):
        """Ensure setup_logging sends warnings to stderr by default."""
        import logging

        from mcp_bigquery.logging_config import setup_logging

        setup_logging(level="WARNING", colored=False)
        logger = logging.getLogger("mcp_bigquery.logging_test")

        logger.info("info message suppressed")
        logger.warning("warn message emitted")

        captured = capsys.readouterr()
        assert captured.out == ""
        assert "warn message emitted" in captured.err
        assert "info message suppressed" not in captured.err

    def test_resolve_log_level_controls_verbosity(self):
        """resolve_log_level should respect verbose/quiet toggles."""
        from mcp_bigquery.logging_config import resolve_log_level

        assert resolve_log_level(default_level="WARNING", verbose=1) == "INFO"
        assert resolve_log_level(default_level="WARNING", verbose=2) == "DEBUG"
        assert resolve_log_level(default_level="INFO", quiet=1) == "ERROR"
        assert resolve_log_level(default_level="INFO", quiet=2) == "CRITICAL"

    def test_context_logger(self):
        """Test ContextLogger."""
        import logging

        from mcp_bigquery.logging_config import ContextLogger

        base_logger = logging.getLogger("test")
        logger = ContextLogger(base_logger)

        # Set context
        logger.set_context(user_id="123", request_id="abc")

        # Log with context (would need to capture output to fully test)
        logger.info("Test message")

        # Clear context
        logger.clear_context()
        assert logger.context == {}

    @pytest.mark.asyncio
    async def test_log_performance_decorator(self):
        """Test log_performance decorator."""
        from mcp_bigquery.logging_config import get_logger, log_performance

        logger = get_logger("test")

        @log_performance(logger, "test_operation")
        async def async_func():
            await asyncio.sleep(0.01)
            return "result"

        result = await async_func()
        assert result == "result"

        @log_performance(logger, "test_operation")
        def sync_func():
            time.sleep(0.01)
            return "result"

        result = sync_func()
        assert result == "result"
