"""Tests for MCP BigQuery features - all tools and functionality."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from google.cloud import bigquery
from google.cloud.exceptions import BadRequest, NotFound

from mcp_bigquery.info_schema import analyze_query_performance, query_info_schema
from mcp_bigquery.schema_explorer import describe_table, get_table_info, list_datasets, list_tables
from mcp_bigquery.server import (
    analyze_query_structure,
    build_query_parameters,
    dry_run_sql,
    extract_dependencies,
    extract_error_location,
    handle_list_tools,
    validate_query_syntax,
    validate_sql,
)
from mcp_bigquery.sql_analyzer import SQLAnalyzer


class TestCoreUtilities:
    """Tests for core utility functions."""

    def test_extract_error_location(self):
        """Test error location extraction from BigQuery error messages."""
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


class TestToolRegistration:
    """Tests for MCP tool registration."""

    @pytest.mark.asyncio
    async def test_list_all_tools(self):
        """Test that all MCP tools are properly registered."""
        tools = await handle_list_tools()

        # Should have 11 tools total
        assert len(tools) == 11

        tool_names = [tool.name for tool in tools]

        # SQL validation and analysis tools (v0.1.0 - v0.3.0)
        assert "bq_validate_sql" in tool_names
        assert "bq_dry_run_sql" in tool_names
        assert "bq_analyze_query_structure" in tool_names
        assert "bq_extract_dependencies" in tool_names
        assert "bq_validate_query_syntax" in tool_names

        # Schema discovery and metadata tools (v0.4.0)
        assert "bq_list_datasets" in tool_names
        assert "bq_list_tables" in tool_names
        assert "bq_describe_table" in tool_names
        assert "bq_get_table_info" in tool_names
        assert "bq_query_info_schema" in tool_names
        assert "bq_analyze_query_performance" in tool_names


class TestSQLAnalysis:
    """Tests for SQL analysis tools."""

    def test_sql_analyzer_initialization(self):
        """Test SQLAnalyzer initialization."""
        sql = "SELECT * FROM users"
        analyzer = SQLAnalyzer(sql)
        assert analyzer.sql == sql
        assert analyzer.parsed is not None

    def test_analyze_query_structure_simple(self):
        """Test query structure analysis for simple query."""
        sql = "SELECT id, name FROM users WHERE active = true"
        analyzer = SQLAnalyzer(sql)
        result = analyzer.analyze_structure()

        assert result["query_type"] == "SELECT"
        assert result["has_joins"] is False
        assert result["has_subqueries"] is False
        assert result["has_cte"] is False
        assert result["table_count"] == 1

    def test_analyze_query_structure_with_join(self):
        """Test query structure analysis with JOIN."""
        sql = """
        SELECT u.name, o.total
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        """
        analyzer = SQLAnalyzer(sql)
        result = analyzer.analyze_structure()

        assert result["has_joins"] is True
        assert "LEFT" in result["join_types"]
        assert result["table_count"] == 2

    def test_extract_dependencies_simple(self):
        """Test dependency extraction for simple query."""
        sql = "SELECT id, name FROM project.dataset.users"
        analyzer = SQLAnalyzer(sql)
        result = analyzer.extract_dependencies()

        assert len(result["tables"]) == 1
        assert result["tables"][0]["name"] == "project.dataset.users"
        assert "id" in result["columns"]
        assert "name" in result["columns"]

    def test_validate_syntax_enhanced(self):
        """Test enhanced syntax validation."""
        sql = "SELECT * FROM users LIMIT 10"
        analyzer = SQLAnalyzer(sql)
        result = analyzer.validate_syntax_enhanced()

        assert result["is_valid"] is True
        assert len(result["issues"]) > 0  # Should have warnings

        # Check for SELECT * warning
        select_star_issues = [i for i in result["issues"] if "SELECT *" in i["message"]]
        assert len(select_star_issues) > 0

        # Check for LIMIT without ORDER BY warning
        limit_issues = [i for i in result["issues"] if "LIMIT without ORDER BY" in i["message"]]
        assert len(limit_issues) > 0


class TestSchemaExplorer:
    """Tests for schema exploration features."""

    @pytest.mark.asyncio
    async def test_list_datasets_success(self):
        """Test successful dataset listing."""
        with patch("mcp_bigquery.schema_explorer.get_bigquery_client") as mock_get_client:
            # Mock BigQuery client
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.project = "test-project"

            # Mock dataset objects
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

            assert result["project"] == "test-project"
            assert result["dataset_count"] == 1
            assert len(result["datasets"]) == 1
            assert result["datasets"][0]["dataset_id"] == "test_dataset"
            assert result["datasets"][0]["location"] == "US"

    @pytest.mark.asyncio
    async def test_list_datasets_error(self):
        """Test dataset listing with error."""
        with patch("mcp_bigquery.schema_explorer.get_bigquery_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.list_datasets.side_effect = Exception("API Error")

            result = await list_datasets()

            assert "error" in result
            assert result["error"]["code"] == "LIST_DATASETS_ERROR"
            assert "API Error" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_list_tables_success(self):
        """Test successful table listing."""
        with patch("mcp_bigquery.schema_explorer.get_bigquery_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.project = "test-project"

            # Mock table objects
            mock_table = MagicMock()
            mock_table.table_id = "test_table"
            mock_table.dataset_id = "test_dataset"
            mock_table.project = "test-project"

            mock_table_ref = MagicMock()
            mock_table_ref.table_type = "TABLE"
            mock_table_ref.created = MagicMock()
            mock_table_ref.created.isoformat.return_value = "2024-01-01T00:00:00"
            mock_table_ref.modified = MagicMock()
            mock_table_ref.modified.isoformat.return_value = "2024-01-02T00:00:00"
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

            assert result["dataset_id"] == "test_dataset"
            assert result["table_count"] == 1
            assert len(result["tables"]) == 1
            assert result["tables"][0]["table_id"] == "test_table"
            assert result["tables"][0]["table_type"] == "TABLE"
            assert result["tables"][0]["num_rows"] == 100

    @pytest.mark.asyncio
    async def test_list_tables_with_filter(self):
        """Test table listing with type filter."""
        with patch("mcp_bigquery.schema_explorer.get_bigquery_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.project = "test-project"

            # Create multiple table types
            tables = []
            table_refs = []

            for i, table_type in enumerate(["TABLE", "VIEW", "EXTERNAL"]):
                mock_table = MagicMock()
                mock_table.table_id = f"test_{table_type.lower()}"
                mock_table.dataset_id = "test_dataset"
                mock_table.project = "test-project"
                tables.append(mock_table)

                mock_table_ref = MagicMock()
                mock_table_ref.table_type = table_type
                mock_table_ref.created = None
                mock_table_ref.modified = None
                mock_table_ref.description = None
                mock_table_ref.labels = {}
                mock_table_ref.num_bytes = 1024
                mock_table_ref.num_rows = 100
                mock_table_ref.location = "US"
                mock_table_ref.partitioning_type = None
                mock_table_ref.clustering_fields = None
                table_refs.append(mock_table_ref)

            mock_client.list_tables.return_value = tables
            mock_client.get_table.side_effect = table_refs

            # Filter for only TABLE and VIEW
            result = await list_tables("test_dataset", table_type_filter=["TABLE", "VIEW"])

            assert result["table_count"] == 2
            table_types = [t["table_type"] for t in result["tables"]]
            assert "TABLE" in table_types
            assert "VIEW" in table_types
            assert "EXTERNAL" not in table_types

    @pytest.mark.asyncio
    async def test_list_tables_dataset_not_found(self):
        """Test table listing when dataset not found."""
        with patch("mcp_bigquery.schema_explorer.get_bigquery_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.project = "test-project"
            mock_client.list_tables.side_effect = NotFound("Dataset not found")

            result = await list_tables("nonexistent_dataset")

            assert "error" in result
            assert result["error"]["code"] == "DATASET_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_describe_table_success(self):
        """Test successful table description."""
        with patch("mcp_bigquery.schema_explorer.get_bigquery_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.project = "test-project"

            # Mock table with schema
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
            mock_table_ref.partitioning_type = "DAY"
            mock_table_ref.time_partitioning = MagicMock()
            mock_table_ref.time_partitioning.field = "created_at"
            mock_table_ref.time_partitioning.expiration_ms = None
            mock_table_ref.time_partitioning.require_partition_filter = False
            mock_table_ref.range_partitioning = None
            mock_table_ref.clustering_fields = ["user_id"]

            # Mock schema fields
            mock_field1 = MagicMock()
            mock_field1.name = "id"
            mock_field1.field_type = "INTEGER"
            mock_field1.mode = "REQUIRED"
            mock_field1.description = "Primary key"
            mock_field1.fields = None

            mock_field2 = MagicMock()
            mock_field2.name = "name"
            mock_field2.field_type = "STRING"
            mock_field2.mode = "NULLABLE"
            mock_field2.description = "User name"
            mock_field2.fields = None

            mock_table_ref.schema = [mock_field1, mock_field2]

            mock_client.get_table.return_value = mock_table_ref

            result = await describe_table("test_table", "test_dataset")

            assert result["table_id"] == "test_table"
            assert result["dataset_id"] == "test_dataset"
            assert result["table_type"] == "TABLE"
            assert len(result["schema"]) == 2
            assert result["schema"][0]["name"] == "id"
            assert result["schema"][0]["type"] == "INTEGER"
            assert result["partitioning"]["type"] == "DAY"
            assert result["clustering_fields"] == ["user_id"]

    @pytest.mark.asyncio
    async def test_describe_table_with_nested_fields(self):
        """Test table description with nested fields."""
        with patch("mcp_bigquery.schema_explorer.get_bigquery_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.project = "test-project"

            mock_table_ref = MagicMock()
            mock_table_ref.table_type = "TABLE"
            mock_table_ref.description = None
            mock_table_ref.created = None
            mock_table_ref.modified = None
            mock_table_ref.expires = None
            mock_table_ref.labels = {}
            mock_table_ref.num_bytes = 0
            mock_table_ref.num_rows = 0
            mock_table_ref.num_long_term_bytes = 0
            mock_table_ref.location = "US"
            mock_table_ref.partitioning_type = None
            mock_table_ref.clustering_fields = None

            # Mock nested schema
            mock_subfield = MagicMock()
            mock_subfield.name = "street"
            mock_subfield.field_type = "STRING"
            mock_subfield.mode = "NULLABLE"
            mock_subfield.description = "Street address"

            mock_field = MagicMock()
            mock_field.name = "address"
            mock_field.field_type = "RECORD"
            mock_field.mode = "NULLABLE"
            mock_field.description = "Address record"
            mock_field.fields = [mock_subfield]

            mock_table_ref.schema = [mock_field]

            mock_client.get_table.return_value = mock_table_ref

            result = await describe_table("test_table", "test_dataset")

            assert len(result["schema"]) == 1
            assert result["schema"][0]["name"] == "address"
            assert result["schema"][0]["type"] == "RECORD"
            assert "fields" in result["schema"][0]
            assert len(result["schema"][0]["fields"]) == 1
            assert result["schema"][0]["fields"][0]["name"] == "street"

    @pytest.mark.asyncio
    async def test_get_table_info_comprehensive(self):
        """Test comprehensive table info retrieval."""
        with patch("mcp_bigquery.schema_explorer.get_bigquery_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.project = "test-project"

            # Mock comprehensive table info
            mock_table_ref = MagicMock()
            mock_table_ref.table_type = "TABLE"
            mock_table_ref.created = MagicMock()
            mock_table_ref.created.isoformat.return_value = "2024-01-01T00:00:00"
            mock_table_ref.modified = None
            mock_table_ref.expires = None
            mock_table_ref.description = "Comprehensive test table"
            mock_table_ref.labels = {"env": "test", "team": "data"}
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
            assert result["dataset_id"] == "test_dataset"
            assert result["full_table_id"] == "test-project.test_dataset.test_table"
            assert result["table_type"] == "TABLE"
            assert result["friendly_name"] == "Test Table"
            assert result["statistics"]["num_bytes"] == 10240
            assert result["statistics"]["num_rows"] == 1000
            assert result["labels"]["env"] == "test"
            assert result["labels"]["team"] == "data"
            assert "time_travel" in result  # TABLE type should have time travel info


class TestInfoSchema:
    """Tests for INFORMATION_SCHEMA and performance analysis features."""

    @pytest.mark.asyncio
    async def test_query_info_schema_tables(self):
        """Test querying INFORMATION_SCHEMA.TABLES."""
        with patch("mcp_bigquery.info_schema.get_bigquery_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.project = "test-project"

            # Mock query job
            mock_query_job = MagicMock()
            mock_query_job.total_bytes_processed = 1024

            # Mock schema
            mock_field = MagicMock()
            mock_field.name = "table_name"
            mock_field.field_type = "STRING"
            mock_field.mode = "NULLABLE"
            mock_field.description = None
            mock_query_job.schema = [mock_field]

            mock_client.query.return_value = mock_query_job

            result = await query_info_schema("tables", "test_dataset")

            assert result["query_type"] == "tables"
            assert result["dataset_id"] == "test_dataset"
            assert result["project"] == "test-project"
            assert "query" in result
            assert "INFORMATION_SCHEMA.TABLES" in result["query"]
            assert result["metadata"]["total_bytes_processed"] == 1024
            assert len(result["schema"]) == 1
            assert result["schema"][0]["name"] == "table_name"

    @pytest.mark.asyncio
    async def test_query_info_schema_custom(self):
        """Test custom INFORMATION_SCHEMA query."""
        with patch("mcp_bigquery.info_schema.get_bigquery_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.project = "test-project"

            mock_query_job = MagicMock()
            mock_query_job.total_bytes_processed = 2048
            mock_query_job.schema = []

            mock_client.query.return_value = mock_query_job

            custom_query = "SELECT * FROM `project.dataset.INFORMATION_SCHEMA.COLUMNS` WHERE table_name = 'users'"
            result = await query_info_schema("custom", "test_dataset", custom_query=custom_query)

            assert result["query_type"] == "custom"
            assert result["query"] == custom_query
            assert result["metadata"]["total_bytes_processed"] == 2048

    @pytest.mark.asyncio
    async def test_query_info_schema_invalid_type(self):
        """Test INFORMATION_SCHEMA query with invalid type."""
        result = await query_info_schema("invalid_type", "test_dataset")

        assert "error" in result
        assert result["error"]["code"] == "INVALID_QUERY_TYPE"
        assert "invalid_type" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_analyze_query_performance_simple(self):
        """Test query performance analysis for simple query."""
        with patch("mcp_bigquery.info_schema.get_bigquery_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.project = "test-project"

            # Mock query job
            mock_query_job = MagicMock()
            mock_query_job.total_bytes_processed = 1024 * 1024  # 1 MB
            mock_query_job.total_bytes_billed = 1024 * 1024
            mock_query_job.referenced_tables = []

            mock_client.query.return_value = mock_query_job

            result = await analyze_query_performance("SELECT * FROM table")

            assert "query_analysis" in result
            assert result["query_analysis"]["bytes_processed"] == 1024 * 1024
            assert result["query_analysis"]["gigabytes_processed"] == pytest.approx(0.001, rel=1e-3)
            assert "performance_score" in result
            assert "performance_rating" in result
            assert "optimization_suggestions" in result

            # Should have SELECT * warning
            suggestions = result["optimization_suggestions"]
            select_star_suggestions = [s for s in suggestions if s["type"] == "SELECT_STAR"]
            assert len(select_star_suggestions) > 0

    @pytest.mark.asyncio
    async def test_analyze_query_performance_complex(self):
        """Test query performance analysis for complex query."""
        with patch("mcp_bigquery.info_schema.get_bigquery_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.project = "test-project"

            # Mock query job for complex query
            mock_query_job = MagicMock()
            mock_query_job.total_bytes_processed = 200 * 1024**3  # 200 GB
            mock_query_job.total_bytes_billed = 200 * 1024**3

            # Mock multiple referenced tables
            mock_tables = []
            for i in range(7):
                mock_table = MagicMock()
                mock_table.project = "test-project"
                mock_table.dataset_id = "test_dataset"
                mock_table.table_id = f"table_{i}"
                mock_tables.append(mock_table)
            mock_query_job.referenced_tables = mock_tables

            mock_client.query.return_value = mock_query_job

            sql = """
            SELECT *
            FROM table1
            CROSS JOIN table2
            WHERE id IN (SELECT id FROM table3)
            LIMIT 100
            """

            result = await analyze_query_performance(sql)

            # Should have multiple warnings
            assert len(result["optimization_suggestions"]) > 3

            # Check for specific warnings
            suggestion_types = [s["type"] for s in result["optimization_suggestions"]]
            assert "HIGH_DATA_SCAN" in suggestion_types
            assert "SELECT_STAR" in suggestion_types
            assert "CROSS_JOIN" in suggestion_types
            assert "SUBQUERY_IN_WHERE" in suggestion_types
            assert "MANY_TABLES" in suggestion_types
            assert "LIMIT_WITHOUT_ORDER" in suggestion_types

            # Performance score should be low due to issues
            assert result["performance_score"] < 50
            assert result["performance_rating"] in ["FAIR", "NEEDS_OPTIMIZATION"]

    @pytest.mark.asyncio
    async def test_analyze_query_performance_excellent(self):
        """Test query performance analysis for optimized query."""
        with patch("mcp_bigquery.info_schema.get_bigquery_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.project = "test-project"

            # Mock query job for optimized query
            mock_query_job = MagicMock()
            mock_query_job.total_bytes_processed = 1 * 1024**3  # 1 GB
            mock_query_job.total_bytes_billed = 1 * 1024**3

            mock_table = MagicMock()
            mock_table.project = "test-project"
            mock_table.dataset_id = "test_dataset"
            mock_table.table_id = "users"
            mock_query_job.referenced_tables = [mock_table]

            mock_client.query.return_value = mock_query_job

            sql = """
            SELECT id, name, email
            FROM users
            WHERE created_at > '2024-01-01'
            ORDER BY created_at DESC
            LIMIT 100
            """

            result = await analyze_query_performance(sql)

            # Should have few or no warnings
            assert len(result["optimization_suggestions"]) <= 1

            # Performance score should be high
            assert result["performance_score"] >= 80
            assert result["performance_rating"] in ["EXCELLENT", "GOOD"]
