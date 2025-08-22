"""BigQuery INFORMATION_SCHEMA and performance analysis utilities."""

import json
import os
from typing import Any, Optional

from google.cloud import bigquery
from google.cloud.exceptions import BadRequest

from .bigquery_client import get_bigquery_client

# Common INFORMATION_SCHEMA queries
INFO_SCHEMA_TEMPLATES = {
    "tables": """
        SELECT 
            table_catalog,
            table_schema,
            table_name,
            table_type,
            creation_time,
            ddl
        FROM `{project}.{dataset}.INFORMATION_SCHEMA.TABLES`
        {where_clause}
        ORDER BY table_name
        {limit_clause}
    """,
    "columns": """
        SELECT 
            table_catalog,
            table_schema,
            table_name,
            column_name,
            ordinal_position,
            is_nullable,
            data_type,
            is_partitioning_column,
            clustering_ordinal_position
        FROM `{project}.{dataset}.INFORMATION_SCHEMA.COLUMNS`
        {where_clause}
        ORDER BY table_name, ordinal_position
        {limit_clause}
    """,
    "table_storage": """
        SELECT 
            table_catalog,
            table_schema,
            table_name,
            creation_time,
            total_rows,
            total_partitions,
            total_logical_bytes,
            active_logical_bytes,
            long_term_logical_bytes,
            total_physical_bytes,
            active_physical_bytes,
            long_term_physical_bytes,
            time_travel_physical_bytes
        FROM `{project}.{dataset}.INFORMATION_SCHEMA.TABLE_STORAGE`
        {where_clause}
        ORDER BY total_logical_bytes DESC
        {limit_clause}
    """,
    "partitions": """
        SELECT 
            table_catalog,
            table_schema,
            table_name,
            partition_id,
            total_rows,
            total_logical_bytes,
            total_physical_bytes,
            last_modified_time
        FROM `{project}.{dataset}.INFORMATION_SCHEMA.PARTITIONS`
        {where_clause}
        ORDER BY table_name, partition_id
        {limit_clause}
    """,
    "views": """
        SELECT 
            table_catalog,
            table_schema,
            table_name,
            view_definition,
            use_standard_sql
        FROM `{project}.{dataset}.INFORMATION_SCHEMA.VIEWS`
        {where_clause}
        ORDER BY table_name
        {limit_clause}
    """,
    "routines": """
        SELECT 
            routine_catalog,
            routine_schema,
            routine_name,
            routine_type,
            language,
            routine_definition,
            created,
            last_altered
        FROM `{project}.{dataset}.INFORMATION_SCHEMA.ROUTINES`
        {where_clause}
        ORDER BY routine_name
        {limit_clause}
    """,
}


async def query_info_schema(
    query_type: str,
    dataset_id: str,
    project_id: Optional[str] = None,
    table_filter: Optional[str] = None,
    custom_query: Optional[str] = None,
    limit: Optional[int] = 100,
) -> dict[str, Any]:
    """
    Execute INFORMATION_SCHEMA queries in dry-run mode.

    Args:
        query_type: Type of query (tables, columns, table_storage, partitions, views, routines, custom)
        dataset_id: The dataset to query metadata for
        project_id: GCP project ID (uses default if not provided)
        table_filter: Optional table name filter
        custom_query: Custom INFORMATION_SCHEMA query (when query_type is 'custom')
        limit: Maximum number of results

    Returns:
        Dict with query results or error information
    """
    try:
        client = get_bigquery_client()
        project = project_id or client.project

        # Build the query
        if query_type == "custom" and custom_query:
            # Use custom query directly
            query = custom_query
        elif query_type in INFO_SCHEMA_TEMPLATES:
            # Build query from template
            where_clause = ""
            if table_filter:
                where_clause = f"WHERE table_name = '{table_filter}'"

            limit_clause = ""
            if limit:
                limit_clause = f"LIMIT {limit}"

            query = INFO_SCHEMA_TEMPLATES[query_type].format(
                project=project,
                dataset=dataset_id,
                where_clause=where_clause,
                limit_clause=limit_clause,
            )
        else:
            return {
                "error": {
                    "code": "INVALID_QUERY_TYPE",
                    "message": f"Invalid query type '{query_type}'. Must be one of: {', '.join(INFO_SCHEMA_TEMPLATES.keys())}, custom",
                }
            }

        # Execute query in dry-run mode
        job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)

        query_job = client.query(query, job_config=job_config)

        # Get schema information from dry-run
        schema = []
        if query_job.schema:
            for field in query_job.schema:
                schema.append(
                    {
                        "name": field.name,
                        "type": field.field_type,
                        "mode": field.mode,
                        "description": field.description,
                    }
                )

        # Calculate cost estimate
        bytes_processed = query_job.total_bytes_processed or 0
        price_per_tib = float(os.environ.get("SAFE_PRICE_PER_TIB", "5.0"))
        bytes_per_tib = 1024**4
        estimated_cost_usd = (bytes_processed / bytes_per_tib) * price_per_tib

        result = {
            "query_type": query_type,
            "dataset_id": dataset_id,
            "project": project,
            "query": query.strip(),
            "schema": schema,
            "metadata": {
                "total_bytes_processed": bytes_processed,
                "estimated_cost_usd": round(estimated_cost_usd, 6),
                "cache_hit": False,  # Always false for dry-run
            },
            "info": "Query validated successfully. Execute without dry_run to get actual results.",
        }

        if table_filter:
            result["table_filter"] = table_filter

        return result

    except BadRequest as e:
        return {
            "error": {
                "code": "QUERY_ERROR",
                "message": str(e),
                "query": query if "query" in locals() else None,
            }
        }
    except Exception as e:
        return {"error": {"code": "INFO_SCHEMA_ERROR", "message": str(e)}}


async def analyze_query_performance(sql: str, project_id: Optional[str] = None) -> dict[str, Any]:
    """
    Analyze query performance using dry-run execution plan.

    Args:
        sql: The SQL query to analyze
        project_id: GCP project ID (uses default if not provided)

    Returns:
        Dict with performance analysis and optimization suggestions
    """
    try:
        client = get_bigquery_client()
        project = project_id or client.project

        # Execute dry-run to get query plan
        job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)

        query_job = client.query(sql, job_config=job_config)

        # Extract performance metrics
        bytes_processed = query_job.total_bytes_processed or 0
        bytes_billed = query_job.total_bytes_billed or bytes_processed

        # Calculate costs
        price_per_tib = float(os.environ.get("SAFE_PRICE_PER_TIB", "5.0"))
        bytes_per_tib = 1024**4
        bytes_per_gib = 1024**3
        estimated_cost_usd = (bytes_billed / bytes_per_tib) * price_per_tib

        # Analyze referenced tables
        referenced_tables = []
        if query_job.referenced_tables:
            for table_ref in query_job.referenced_tables:
                referenced_tables.append(
                    {
                        "project": table_ref.project,
                        "dataset": table_ref.dataset_id,
                        "table": table_ref.table_id,
                        "full_id": f"{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}",
                    }
                )

        # Performance analysis
        performance_analysis = {
            "bytes_processed": bytes_processed,
            "bytes_billed": bytes_billed,
            "gigabytes_processed": round(bytes_processed / bytes_per_gib, 3),
            "estimated_cost_usd": round(estimated_cost_usd, 6),
            "slot_milliseconds": (
                query_job.estimated_bytes_processed
                if hasattr(query_job, "estimated_bytes_processed")
                else None
            ),
            "referenced_tables": referenced_tables,
            "table_count": len(referenced_tables),
        }

        # Generate optimization suggestions
        suggestions = []

        # Check for high data scan
        if bytes_processed > 100 * bytes_per_gib:  # More than 100 GB
            suggestions.append(
                {
                    "type": "HIGH_DATA_SCAN",
                    "severity": "HIGH",
                    "message": f"Query will process {round(bytes_processed / bytes_per_gib, 2)} GB of data",
                    "recommendation": "Consider adding WHERE clauses, using partitioning, or limiting date ranges",
                }
            )

        # Check for SELECT *
        if "SELECT *" in sql.upper() or "SELECT\n*" in sql.upper():
            suggestions.append(
                {
                    "type": "SELECT_STAR",
                    "severity": "MEDIUM",
                    "message": "Query uses SELECT * which processes all columns",
                    "recommendation": "Select only the columns you need to reduce data processed",
                }
            )

        # Check for missing LIMIT without ORDER BY
        has_limit = "LIMIT" in sql.upper()
        has_order_by = "ORDER BY" in sql.upper()
        if has_limit and not has_order_by:
            suggestions.append(
                {
                    "type": "LIMIT_WITHOUT_ORDER",
                    "severity": "LOW",
                    "message": "LIMIT without ORDER BY may return inconsistent results",
                    "recommendation": "Add ORDER BY clause to ensure consistent results",
                }
            )

        # Check for CROSS JOIN
        if "CROSS JOIN" in sql.upper():
            suggestions.append(
                {
                    "type": "CROSS_JOIN",
                    "severity": "HIGH",
                    "message": "CROSS JOIN can produce very large result sets",
                    "recommendation": "Verify that CROSS JOIN is necessary, consider using INNER JOIN with conditions",
                }
            )

        # Check for subqueries in WHERE clause
        if "WHERE" in sql.upper() and "SELECT" in sql.upper()[sql.upper().index("WHERE") :]:
            suggestions.append(
                {
                    "type": "SUBQUERY_IN_WHERE",
                    "severity": "MEDIUM",
                    "message": "Subquery in WHERE clause may impact performance",
                    "recommendation": "Consider using JOIN or WITH clause instead",
                }
            )

        # Check for multiple table scans
        if len(referenced_tables) > 5:
            suggestions.append(
                {
                    "type": "MANY_TABLES",
                    "severity": "MEDIUM",
                    "message": f"Query references {len(referenced_tables)} tables",
                    "recommendation": "Consider creating intermediate tables or materialized views for complex joins",
                }
            )

        # Calculate performance score (0-100)
        score = 100

        # Deduct points based on data volume
        if bytes_processed > 1 * bytes_per_tib:
            score -= 30
        elif bytes_processed > 100 * bytes_per_gib:
            score -= 20
        elif bytes_processed > 10 * bytes_per_gib:
            score -= 10

        # Deduct points for issues
        for suggestion in suggestions:
            if suggestion["severity"] == "HIGH":
                score -= 15
            elif suggestion["severity"] == "MEDIUM":
                score -= 10
            elif suggestion["severity"] == "LOW":
                score -= 5

        score = max(0, score)  # Ensure score doesn't go below 0

        # Determine performance rating
        if score >= 80:
            rating = "EXCELLENT"
        elif score >= 60:
            rating = "GOOD"
        elif score >= 40:
            rating = "FAIR"
        else:
            rating = "NEEDS_OPTIMIZATION"

        return {
            "query_analysis": performance_analysis,
            "performance_score": score,
            "performance_rating": rating,
            "optimization_suggestions": suggestions,
            "suggestion_count": len(suggestions),
            "estimated_execution": {
                "note": "Actual execution time depends on cluster resources and current load",
                "complexity_indicator": (
                    "HIGH"
                    if bytes_processed > 100 * bytes_per_gib
                    else "MEDIUM" if bytes_processed > 10 * bytes_per_gib else "LOW"
                ),
            },
        }

    except BadRequest as e:
        return {"error": {"code": "ANALYSIS_ERROR", "message": str(e)}}
    except Exception as e:
        return {"error": {"code": "PERFORMANCE_ANALYSIS_ERROR", "message": str(e)}}
