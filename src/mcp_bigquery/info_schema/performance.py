"""Query performance analysis helpers."""

from __future__ import annotations

from typing import Any, Optional

from google.cloud import bigquery
from google.cloud.exceptions import BadRequest

from ..bigquery_client import get_bigquery_client
from ..config import get_config
from ..exceptions import MCPBigQueryError
from ..logging_config import get_logger
from ..utils import format_error_response
from ..validators import AnalyzePerformanceRequest, validate_request

logger = get_logger(__name__)


async def analyze_query_performance(
    sql: str,
    project_id: Optional[str] = None,
) -> dict[str, Any]:
    """Dry-run a query and provide performance insights."""
    try:
        request = validate_request(
            AnalyzePerformanceRequest,
            {"sql": sql, "project_id": project_id},
        )
    except MCPBigQueryError as exc:
        return {"error": format_error_response(exc)}

    try:
        return await _analyze_query_performance_impl(request)
    except MCPBigQueryError as exc:
        return {"error": format_error_response(exc)}
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Unexpected error during performance analysis")
        wrapped = MCPBigQueryError(str(exc), code="PERFORMANCE_ANALYSIS_ERROR")
        return {"error": format_error_response(wrapped)}


async def _analyze_query_performance_impl(request: AnalyzePerformanceRequest) -> dict[str, Any]:
    client = get_bigquery_client(project_id=request.project_id)
    project = request.project_id or client.project

    job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)

    try:
        query_job = client.query(request.sql, job_config=job_config)
    except BadRequest as exc:
        raise MCPBigQueryError(str(exc), code="ANALYSIS_ERROR") from exc

    bytes_processed = query_job.total_bytes_processed or 0
    bytes_billed = query_job.total_bytes_billed or bytes_processed

    price_per_tib = get_config().price_per_tib
    bytes_per_tib = 1024**4
    bytes_per_gib = 1024**3
    estimated_cost_usd = (bytes_billed / bytes_per_tib) * price_per_tib

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

    performance_analysis = {
        "bytes_processed": bytes_processed,
        "bytes_billed": bytes_billed,
        "gigabytes_processed": round(bytes_processed / bytes_per_gib, 3),
        "estimated_cost_usd": round(estimated_cost_usd, 6),
        "slot_milliseconds": getattr(query_job, "estimated_bytes_processed", None),
        "referenced_tables": referenced_tables,
        "table_count": len(referenced_tables),
    }

    suggestions = _build_suggestions(request.sql, bytes_processed, referenced_tables, bytes_per_gib)
    score, rating = _score_performance(bytes_processed, suggestions, bytes_per_gib, bytes_per_tib)

    return {
        "query_analysis": performance_analysis,
        "performance_score": score,
        "performance_rating": rating,
        "optimization_suggestions": suggestions,
        "suggestion_count": len(suggestions),
        "estimated_execution": {
            "note": "Actual execution time depends on cluster resources and current load",
            "complexity_indicator": _complexity_indicator(bytes_processed, bytes_per_gib),
        },
        "project": project,
    }


def _build_suggestions(
    sql: str,
    bytes_processed: int,
    referenced_tables: list[dict[str, Any]],
    bytes_per_gib: int,
) -> list[dict[str, Any]]:
    sql_upper = sql.upper()
    suggestions: list[dict[str, Any]] = []

    if bytes_processed > 100 * bytes_per_gib:
        suggestions.append(
            {
                "type": "HIGH_DATA_SCAN",
                "severity": "HIGH",
                "message": f"Query will process {round(bytes_processed / bytes_per_gib, 2)} GB of data",
                "recommendation": "Consider adding WHERE clauses, using partitioning, or limiting date ranges",
            }
        )

    if "SELECT *" in sql_upper or "SELECT\n*" in sql_upper:
        suggestions.append(
            {
                "type": "SELECT_STAR",
                "severity": "MEDIUM",
                "message": "Query uses SELECT * which processes all columns",
                "recommendation": "Select only the columns you need to reduce data processed",
            }
        )

    has_limit = "LIMIT" in sql_upper
    has_order_by = "ORDER BY" in sql_upper
    if has_limit and not has_order_by:
        suggestions.append(
            {
                "type": "LIMIT_WITHOUT_ORDER",
                "severity": "LOW",
                "message": "LIMIT without ORDER BY may return inconsistent results",
                "recommendation": "Add ORDER BY clause to ensure consistent results",
            }
        )

    if "CROSS JOIN" in sql_upper:
        suggestions.append(
            {
                "type": "CROSS_JOIN",
                "severity": "HIGH",
                "message": "CROSS JOIN can produce very large result sets",
                "recommendation": "Verify that CROSS JOIN is necessary, consider using INNER JOIN with conditions",
            }
        )

    if "WHERE" in sql_upper and "SELECT" in sql_upper[sql_upper.index("WHERE") :]:
        suggestions.append(
            {
                "type": "SUBQUERY_IN_WHERE",
                "severity": "MEDIUM",
                "message": "Subquery in WHERE clause may impact performance",
                "recommendation": "Consider using JOIN or WITH clause instead",
            }
        )

    if len(referenced_tables) > 5:
        suggestions.append(
            {
                "type": "MANY_TABLES",
                "severity": "MEDIUM",
                "message": f"Query references {len(referenced_tables)} tables",
                "recommendation": "Consider creating intermediate tables or materialized views for complex joins",
            }
        )

    return suggestions


def _score_performance(
    bytes_processed: int,
    suggestions: list[dict[str, Any]],
    bytes_per_gib: int,
    bytes_per_tib: int,
) -> tuple[int, str]:
    score = 100

    if bytes_processed > 1 * bytes_per_tib:
        score -= 30
    elif bytes_processed > 100 * bytes_per_gib:
        score -= 20
    elif bytes_processed > 10 * bytes_per_gib:
        score -= 10

    for suggestion in suggestions:
        severity = suggestion["severity"]
        if severity == "HIGH":
            score -= 15
        elif severity == "MEDIUM":
            score -= 10
        elif severity == "LOW":
            score -= 5

    score = max(0, score)

    if score >= 80:
        rating = "EXCELLENT"
    elif score >= 60:
        rating = "GOOD"
    elif score >= 40:
        rating = "FAIR"
    else:
        rating = "NEEDS_OPTIMIZATION"

    return score, rating


def _complexity_indicator(bytes_processed: int, bytes_per_gib: int) -> str:
    if bytes_processed > 100 * bytes_per_gib:
        return "HIGH"
    if bytes_processed > 10 * bytes_per_gib:
        return "MEDIUM"
    return "LOW"
