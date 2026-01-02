"""Core unit tests for mcp-bigquery."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_bigquery.logging_config import resolve_log_level, setup_logging
from mcp_bigquery.schema_explorer import describe_table, get_table_info, list_datasets, list_tables
from mcp_bigquery.server import build_query_parameters, handle_list_tools
from mcp_bigquery.sql_analyzer import SQLAnalyzer
from mcp_bigquery.utils import extract_error_location


class TestBasics:
    def test_extract_error_location(self):
        assert extract_error_location("Error at [2:4]") == {"line": 2, "column": 4}
        assert extract_error_location("No location") is None

    def test_build_query_parameters(self):
        params = {"name": "Alice", "age": 30}
        result = build_query_parameters(params)
        assert len(result) == 2
        assert all(param.type_ == "STRING" for param in result)

    @pytest.mark.asyncio
    async def test_list_tools(self):
        tools = await handle_list_tools()
        tool_names = {tool.name for tool in tools}
        assert len(tool_names) == 8
        assert "bq_validate_sql" in tool_names
        assert "bq_dry_run_sql" in tool_names
        assert "bq_extract_dependencies" in tool_names
        assert "bq_validate_query_syntax" in tool_names


class TestSQLAnalyzer:
    def test_extract_dependencies(self):
        analyzer = SQLAnalyzer("SELECT id, name FROM project.dataset.users")
        result = analyzer.extract_dependencies()
        assert result["table_count"] == 1
        assert result["columns"]

    def test_validate_syntax_enhanced(self):
        analyzer = SQLAnalyzer("SELECT * FROM users LIMIT 10")
        result = analyzer.validate_syntax_enhanced()
        assert result["is_valid"] is True
        assert result["issues"]


class TestSchemaExplorer:
    @pytest.mark.asyncio
    async def test_list_datasets(self):
        with patch("mcp_bigquery.schema_explorer.datasets.get_bigquery_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.project = "test-project"

            mock_dataset = MagicMock()
            mock_dataset.dataset_id = "test_dataset"
            mock_dataset.project = "test-project"

            mock_dataset_ref = MagicMock()
            mock_dataset_ref.location = "US"
            mock_dataset_ref.created = MagicMock()
            mock_dataset_ref.created.isoformat.return_value = "2024-01-01T00:00:00"
            mock_dataset_ref.modified = MagicMock()
            mock_dataset_ref.modified.isoformat.return_value = "2024-01-02T00:00:00"
            mock_dataset_ref.description = "Test dataset"
            mock_dataset_ref.labels = {"env": "test"}
            mock_dataset_ref.default_table_expiration_ms = None
            mock_dataset_ref.default_partition_expiration_ms = None

            mock_client.list_datasets.return_value = [mock_dataset]
            mock_client.get_dataset.return_value = mock_dataset_ref

            result = await list_datasets()
            assert result["dataset_count"] == 1

    @pytest.mark.asyncio
    async def test_list_tables(self):
        with patch("mcp_bigquery.schema_explorer.tables.get_bigquery_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.project = "test-project"

            mock_table = MagicMock()
            mock_table.table_id = "test_table"
            mock_table.dataset_id = "test_dataset"
            mock_table.project = "test-project"

            mock_table_ref = MagicMock()
            mock_table_ref.table_type = "TABLE"
            mock_table_ref.created = None
            mock_table_ref.modified = None
            mock_table_ref.description = "Test table"
            mock_table_ref.labels = {}
            mock_table_ref.num_bytes = 1024
            mock_table_ref.num_rows = 100
            mock_table_ref.location = "US"
            mock_table_ref.partitioning_type = None
            mock_table_ref.clustering_fields = None

            mock_client.list_tables.return_value = [mock_table]
            mock_client.get_table.return_value = mock_table_ref

            result = await list_tables("test_dataset")
            assert result["table_count"] == 1

    @pytest.mark.asyncio
    async def test_describe_table(self):
        with patch("mcp_bigquery.schema_explorer.describe.get_bigquery_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.project = "test-project"

            mock_table_ref = MagicMock()
            mock_table_ref.table_type = "TABLE"
            mock_table_ref.description = "Test table"
            mock_table_ref.created = MagicMock()
            mock_table_ref.created.isoformat.return_value = "2024-01-01T00:00:00"
            mock_table_ref.modified = None
            mock_table_ref.expires = None
            mock_table_ref.labels = {}
            mock_table_ref.num_bytes = 2048
            mock_table_ref.num_rows = 200
            mock_table_ref.num_long_term_bytes = 1024
            mock_table_ref.location = "US"
            mock_table_ref.partitioning_type = None
            mock_table_ref.clustering_fields = None

            mock_field = MagicMock()
            mock_field.name = "id"
            mock_field.field_type = "INTEGER"
            mock_field.mode = "REQUIRED"
            mock_field.description = "Primary key"
            mock_field.fields = None
            mock_table_ref.schema = [mock_field]

            mock_client.get_table.return_value = mock_table_ref

            result = await describe_table("test_table", "test_dataset")
            assert result["schema"][0]["name"] == "id"

    @pytest.mark.asyncio
    async def test_get_table_info(self):
        with patch("mcp_bigquery.schema_explorer.tables.get_bigquery_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.project = "test-project"

            mock_table_ref = MagicMock()
            mock_table_ref.table_type = "TABLE"
            mock_table_ref.created = MagicMock()
            mock_table_ref.created.isoformat.return_value = "2024-01-01T00:00:00"
            mock_table_ref.modified = None
            mock_table_ref.expires = None
            mock_table_ref.description = "Comprehensive test table"
            mock_table_ref.labels = {"env": "test"}
            mock_table_ref.location = "US"
            mock_table_ref.self_link = "https://bigquery.googleapis.com/..."
            mock_table_ref.etag = "abc123"
            mock_table_ref.encryption_configuration = None
            mock_table_ref.friendly_name = "Test Table"
            mock_table_ref.num_bytes = 10240
            mock_table_ref.num_long_term_bytes = 5120
            mock_table_ref.num_rows = 1000
            mock_table_ref.num_active_logical_bytes = 8192
            mock_table_ref.num_active_physical_bytes = 8192
            mock_table_ref.num_long_term_logical_bytes = 2048
            mock_table_ref.num_long_term_physical_bytes = 2048
            mock_table_ref.num_total_logical_bytes = 10240
            mock_table_ref.num_total_physical_bytes = 10240
            mock_table_ref.schema = [MagicMock()]
            mock_table_ref.streaming_buffer = None
            mock_table_ref.partitioning_type = None
            mock_table_ref.clustering_fields = None

            mock_client.get_table.return_value = mock_table_ref

            result = await get_table_info("test_table", "test_dataset")
            assert result["table_id"] == "test_table"


class TestSupportModules:
    def test_logging_helpers(self, capsys):
        assert resolve_log_level(default_level="WARNING", verbose=1) == "INFO"
        setup_logging(level="WARNING")

        import logging

        log = logging.getLogger("mcp_bigquery.logging_test")
        log.warning("warn message emitted")
        captured = capsys.readouterr()
        assert "warn message emitted" in captured.err

    def test_client_cache(self):
        from mcp_bigquery.cache import BigQueryClientCache

        with patch("mcp_bigquery.clients.factory._instantiate_client") as mock_builder:
            mock_client = Mock()
            mock_builder.return_value = mock_client
            cache = BigQueryClientCache()
            client1 = cache.get_client("project1", "US")
            mock_builder.reset_mock()
            client2 = cache.get_client("project1", "US")
            assert client1 is client2
            assert not mock_builder.called
