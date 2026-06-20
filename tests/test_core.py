"""Core unit tests for mcp-bigquery."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_bigquery.logging_config import resolve_log_level, setup_logging
from mcp_bigquery.schema_explorer import (
    describe_table,
    get_table_info,
    list_datasets,
    list_tables,
    preview_table,
)
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
        assert len(tool_names) == 9
        assert "bq_validate_sql" in tool_names
        assert "bq_dry_run_sql" in tool_names
        assert "bq_extract_dependencies" in tool_names
        assert "bq_validate_query_syntax" in tool_names
        assert "bq_preview_table" in tool_names


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


class TestEnhancedValidationAndExceptions:
    def test_create_mock_bad_request_with_errors(self):
        from google.api_core.exceptions import BadRequest

        from mcp_bigquery.exceptions import SQLValidationError, handle_bigquery_error

        errors = [{"message": "Duplicate column name 'id'", "location": "query"}]
        exc = BadRequest("Bad Request", errors=errors)
        exc._errors = errors

        bq_err = handle_bigquery_error(exc)
        assert isinstance(bq_err, SQLValidationError)
        assert bq_err.details == errors

    def test_validation_boundary_conditions(self):
        from mcp_bigquery.exceptions import InvalidParameterError
        from mcp_bigquery.validators import (
            DescribeTableRequest,
            GetTableInfoRequest,
            ListDatasetsRequest,
            ListTablesRequest,
            validate_request,
        )

        # 1. project_id boundary validation (too short or invalid chars)
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_request(ListDatasetsRequest, {"project_id": "abc"})
        assert "project_id" in str(exc_info.value)

        with pytest.raises(InvalidParameterError) as exc_info:
            validate_request(ListDatasetsRequest, {"project_id": "Invalid_Proj"})
        assert "project_id" in str(exc_info.value)

        # 2. dataset_id / table_id boundary validation (empty or too long)
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_request(ListTablesRequest, {"dataset_id": ""})
        assert "dataset_id" in str(exc_info.value)

        with pytest.raises(InvalidParameterError) as exc_info:
            validate_request(ListTablesRequest, {"dataset_id": "a" * 1025})
        assert "dataset_id" in str(exc_info.value)

        with pytest.raises(InvalidParameterError) as exc_info:
            validate_request(DescribeTableRequest, {"dataset_id": "ds", "table_id": "a" * 1025})
        assert "table_id" in str(exc_info.value)

        with pytest.raises(InvalidParameterError) as exc_info:
            validate_request(GetTableInfoRequest, {"dataset_id": "", "table_id": "tbl"})
        assert "dataset_id" in str(exc_info.value)


class TestConcurrencyAndCache:
    @pytest.mark.asyncio
    async def test_client_cache_concurrency(self):
        import concurrent.futures

        from mcp_bigquery.cache import BigQueryClientCache

        cache = BigQueryClientCache()
        create_count = 0

        def dummy_builder(project_id: str | None, location: str | None) -> MagicMock:
            nonlocal create_count
            import time

            time.sleep(0.05)  # Simulate latency
            create_count += 1
            mock_client = MagicMock()
            mock_client.project = project_id or "default"
            return mock_client

        def task_worker() -> MagicMock:
            return cache.get_client("proj-concurrency", "US", builder=dummy_builder)  # type: ignore

        # Run concurrent accesses in a thread pool to simulate multi-threaded client retrieval
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(task_worker) for _ in range(5)]
            results = [f.result() for f in futures]

        first_result = results[0]
        for r in results:
            assert r is first_result

        assert create_count == 1


class TestPreviewTable:
    @pytest.mark.asyncio
    async def test_preview_disabled_by_default(self):
        from mcp_bigquery.config import reset_config

        reset_config()

        result = await preview_table("test_dataset", "test_table")
        assert "error" in result
        assert result["error"]["code"] == "PREVIEW_DISABLED"
        assert "MCP_BQ_ENABLE_PREVIEW=true" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_preview_enabled_successful(self):
        from mcp_bigquery.config import Config, reset_config, set_config

        set_config(Config(project_id="test-project", enable_preview=True))

        with patch("mcp_bigquery.schema_explorer.preview.get_bigquery_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.project = "test-project"

            import datetime
            from decimal import Decimal

            mock_row = MagicMock()
            mock_row.items.return_value = [
                ("id", 1),
                ("name", "Alice"),
                ("created_at", datetime.datetime(2024, 1, 1, 12, 0, 0)),
                ("price", Decimal("9.99")),
                ("data", b"hello"),
            ]
            mock_client.list_rows.return_value = [mock_row]

            result = await preview_table("test_dataset", "test_table", max_results=3)

            assert "rows" in result
            assert len(result["rows"]) == 1
            row = result["rows"][0]
            assert row["id"] == 1
            assert row["name"] == "Alice"
            assert row["created_at"] == "2024-01-01T12:00:00"
            assert row["price"] == 9.99
            assert row["data"] == "hello"

            mock_client.list_rows.assert_called_once()
            args, kwargs = mock_client.list_rows.call_args
            assert kwargs["max_results"] == 3

            reset_config()

    @pytest.mark.asyncio
    async def test_preview_max_results_clipping(self):
        from mcp_bigquery.config import Config, reset_config, set_config

        set_config(Config(project_id="test-project", enable_preview=True))

        with patch("mcp_bigquery.schema_explorer.preview.get_bigquery_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.project = "test-project"
            mock_client.list_rows.return_value = []

            await preview_table("test_dataset", "test_table", max_results=15)

            args, kwargs = mock_client.list_rows.call_args
            assert kwargs["max_results"] == 10

            reset_config()

    @pytest.mark.asyncio
    async def test_preview_empty_table(self):
        from mcp_bigquery.config import Config, reset_config, set_config

        set_config(Config(project_id="test-project", enable_preview=True))

        with patch("mcp_bigquery.schema_explorer.preview.get_bigquery_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.project = "test-project"
            mock_client.list_rows.return_value = []

            result = await preview_table("test_dataset", "test_table")
            assert "message" in result
            assert result["message"] == "テーブルは空です"

            reset_config()

    @pytest.mark.asyncio
    async def test_preview_not_found_handling(self):
        from google.cloud.exceptions import NotFound

        from mcp_bigquery.config import Config, reset_config, set_config

        set_config(Config(project_id="test-project", enable_preview=True))

        with patch("mcp_bigquery.schema_explorer.preview.get_bigquery_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.project = "test-project"
            mock_client.list_rows.side_effect = NotFound("Table not found")

            result = await preview_table("test_dataset", "not_exist_table")
            assert "error" in result
            assert result["error"]["code"] == "TABLE_NOT_FOUND"

            reset_config()
