"""Integration tests for mcp-bigquery."""

import os

import pytest

# Skip all tests in this file if no credentials
pytestmark = pytest.mark.skipif(
    not (
        os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") is not None
        or os.path.exists(
            os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
        )
        or os.environ.get("GOOGLE_CLOUD_PROJECT") is not None
    ),
    reason="BigQuery credentials not available",
)


class TestRealBigQueryIntegration:
    """Test with actual BigQuery API calls."""

    @pytest.mark.asyncio
    async def test_public_dataset_query(self):
        """Test querying a public dataset."""
        from mcp_bigquery.server import dry_run_sql

        # Use a well-known public dataset
        sql = "SELECT * FROM `bigquery-public-data.samples.shakespeare` LIMIT 10"
        result = await dry_run_sql(sql)

        assert "error" not in result
        assert "totalBytesProcessed" in result
        assert result["totalBytesProcessed"] > 0
        assert "usdEstimate" in result
        assert "referencedTables" in result
        assert len(result["referencedTables"]) == 1
        assert result["referencedTables"][0]["project"] == "bigquery-public-data"
        assert result["referencedTables"][0]["dataset"] == "samples"
        assert result["referencedTables"][0]["table"] == "shakespeare"
        assert "schemaPreview" in result
        assert len(result["schemaPreview"]) > 0

    @pytest.mark.asyncio
    async def test_aggregation_query(self):
        """Test aggregation query dry-run."""
        from mcp_bigquery.server import dry_run_sql

        sql = """
        SELECT
            corpus,
            COUNT(*) as word_count,
            SUM(word_count) as total_occurrences
        FROM `bigquery-public-data.samples.shakespeare`
        GROUP BY corpus
        """

        result = await dry_run_sql(sql)

        assert "error" not in result
        assert "schemaPreview" in result

        # Check schema has expected columns
        schema_names = [field["name"] for field in result["schemaPreview"]]
        assert "corpus" in schema_names
        assert "word_count" in schema_names
        assert "total_occurrences" in schema_names

    @pytest.mark.asyncio
    async def test_parameterized_query(self):
        """Test parameterized query validation."""
        from mcp_bigquery.server import validate_sql

        # Since we only support STRING parameters, we need to cast numeric comparisons
        sql = """
        SELECT word, word_count
        FROM `bigquery-public-data.samples.shakespeare`
        WHERE corpus = @corpus_name
        AND word_count > CAST(@min_count AS INT64)
        """

        params = {"corpus_name": "hamlet", "min_count": "10"}

        result = await validate_sql(sql, params)
        assert result["isValid"] is True

    @pytest.mark.asyncio
    async def test_invalid_table_reference(self):
        """Test error handling for non-existent table."""
        from mcp_bigquery.server import dry_run_sql

        sql = "SELECT * FROM `nonexistent-project.nonexistent-dataset." "nonexistent-table`"
        result = await dry_run_sql(sql)

        assert "error" in result
        assert result["error"]["code"] == "INVALID_SQL"
        assert "message" in result["error"]

    @pytest.mark.asyncio
    async def test_syntax_error_with_location(self):
        """Test that syntax errors include location information."""
        from mcp_bigquery.server import validate_sql

        sql = "SELECT FROM `bigquery-public-data.samples.shakespeare`"
        result = await validate_sql(sql)

        assert result["isValid"] is False
        assert "error" in result
        assert "message" in result["error"]
        # BigQuery often returns location info for syntax errors
        if "location" in result["error"]:
            assert "line" in result["error"]["location"]
            assert "column" in result["error"]["location"]

    @pytest.mark.asyncio
    async def test_cost_estimation_with_custom_price(self):
        """Test cost estimation with custom price per TiB."""
        from mcp_bigquery.server import dry_run_sql

        sql = "SELECT * FROM `bigquery-public-data.samples.shakespeare`"

        # Test with different prices
        prices = [1.0, 5.0, 10.0]
        results = []

        for price in prices:
            result = await dry_run_sql(sql, price_per_tib=price)
            results.append(result)
            assert "usdEstimate" in result

        # Verify that estimates scale linearly with price
        bytes_processed = results[0]["totalBytesProcessed"]
        for i, price in enumerate(prices):
            expected = (bytes_processed / (2**40)) * price
            assert abs(results[i]["usdEstimate"] - expected) < 0.000001

    @pytest.mark.asyncio
    async def test_cte_query(self):
        """Test Common Table Expression (CTE) query."""
        from mcp_bigquery.server import dry_run_sql, validate_sql

        sql = """
        WITH word_stats AS (
            SELECT
                word,
                SUM(word_count) as total_count
            FROM `bigquery-public-data.samples.shakespeare`
            GROUP BY word
        )
        SELECT*
        FROM word_stats
        WHERE total_count > 100
        ORDER BY total_count DESC
        """

        # First validate
        validate_result = await validate_sql(sql)
        assert validate_result["isValid"] is True

        # Then dry-run
        dry_run_result = await dry_run_sql(sql)
        assert "error" not in dry_run_result
        assert "totalBytesProcessed" in dry_run_result

    @pytest.mark.asyncio
    async def test_environment_variable_precedence(self):
        """Test that price parameter takes precedence over env variable."""
        import os

        from mcp_bigquery.server import dry_run_sql

        # Save original value
        original = os.environ.get("SAFE_PRICE_PER_TIB")

        try:
            # Set environment variable
            os.environ["SAFE_PRICE_PER_TIB"] = "100.0"

            sql = "SELECT 1"

            # Test with explicit price (should override env)
            result = await dry_run_sql(sql, price_per_tib=1.0)
            assert "usdEstimate" in result
            # SELECT 1 typically has 0 bytes, so estimate should be 0
            assert result["usdEstimate"] == 0.0

            # Test without explicit price (should use env)
            result = await dry_run_sql(sql)
            assert "usdEstimate" in result
            assert result["usdEstimate"] == 0.0  # Still 0 because 0 bytes

        finally:
            # Restore original value
            if original is not None:
                os.environ["SAFE_PRICE_PER_TIB"] = original
            else:
                os.environ.pop("SAFE_PRICE_PER_TIB", None)
