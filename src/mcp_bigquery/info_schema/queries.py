"""INFORMATION_SCHEMA query utilities."""

from __future__ import annotations

from typing import Any

from google.cloud import bigquery
from google.cloud.exceptions import BadRequest

from ..bigquery_client import get_bigquery_client
from ..config import get_config
from ..exceptions import MCPBigQueryError
from ..logging_config import get_logger
from ..utils import format_error_response
from ..validators import QueryInfoSchemaRequest, validate_request
from ._templates import INFO_SCHEMA_TEMPLATES

logger = get_logger(__name__)


async def query_info_schema(
    query_type: str,
    dataset_id: str,
    project_id: str | None = None,
    table_filter: str | None = None,
    custom_query: str | None = None,
    limit: int | None = 100,
) -> dict[str, Any]:
    """Execute INFORMATION_SCHEMA queries using dry-run validation."""
    try:
        request = validate_request(
            QueryInfoSchemaRequest,
            {
                "query_type": query_type,
                "dataset_id": dataset_id,
                "project_id": project_id,
                "table_filter": table_filter,
                "custom_query": custom_query,
                "limit": limit,
            },
        )
    except MCPBigQueryError as exc:
        details = exc.details if isinstance(exc.details, dict) else {}
        message_lower = exc.message.lower()
        if exc.code == "INVALID_PARAMETER" and (
            details.get("parameter") == "query_type" or "query_type" in message_lower
        ):
            allowed = sorted(INFO_SCHEMA_TEMPLATES.keys()) + ["custom"]
            custom_exc = MCPBigQueryError(
                f"Invalid query type '{query_type}'.",
                code="INVALID_QUERY_TYPE",
                details=[{"allowed": allowed}],
            )
            return {"error": format_error_response(custom_exc)}

        return {"error": format_error_response(exc)}

    try:
        return await _query_info_schema_impl(request)
    except MCPBigQueryError as exc:
        return {"error": format_error_response(exc)}
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Unexpected error while querying INFORMATION_SCHEMA")
        wrapped = MCPBigQueryError(str(exc), code="INFO_SCHEMA_ERROR")
        return {"error": format_error_response(wrapped)}


def _build_query(request: QueryInfoSchemaRequest, project: str) -> str:
    if request.query_type == "custom" and request.custom_query:
        return request.custom_query.strip()

    template = INFO_SCHEMA_TEMPLATES.get(request.query_type)
    if not template:
        raise MCPBigQueryError(
            f"Invalid query type '{request.query_type}'.",
            code="INVALID_QUERY_TYPE",
            details=[{"allowed": sorted(INFO_SCHEMA_TEMPLATES.keys()) + ["custom"]}],
        )

    where_clause = ""
    if request.table_filter:
        where_clause = f"WHERE table_name = '{request.table_filter}'"

    limit_clause = ""
    if request.limit:
        limit_clause = f"LIMIT {request.limit}"

    return template.format(
        project=project,
        dataset=request.dataset_id,
        where_clause=where_clause,
        limit_clause=limit_clause,
    ).strip()


async def _query_info_schema_impl(request: QueryInfoSchemaRequest) -> dict[str, Any]:
    client = get_bigquery_client(project_id=request.project_id)
    project = request.project_id or client.project
    query = _build_query(request, project)

    job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)

    try:
        query_job = client.query(query, job_config=job_config)
    except BadRequest as exc:
        raise MCPBigQueryError(
            str(exc),
            code="QUERY_ERROR",
            details=[{"query": query}],
        ) from exc

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

    bytes_processed = query_job.total_bytes_processed or 0
    price_per_tib = get_config().price_per_tib
    bytes_per_tib = 1024**4
    estimated_cost_usd = (bytes_processed / bytes_per_tib) * price_per_tib

    result: dict[str, Any] = {
        "query_type": request.query_type,
        "dataset_id": request.dataset_id,
        "project": project,
        "query": query,
        "schema": schema,
        "metadata": {
            "total_bytes_processed": bytes_processed,
            "estimated_cost_usd": round(estimated_cost_usd, 6),
            "cache_hit": False,
        },
        "info": "Query validated successfully. Execute without dry_run to get actual results.",
    }

    if request.table_filter:
        result["table_filter"] = request.table_filter

    return result
