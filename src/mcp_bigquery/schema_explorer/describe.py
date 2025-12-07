"""Table schema description helpers."""

from __future__ import annotations

from typing import Any, Optional

from google.cloud.exceptions import NotFound

from ..bigquery_client import get_bigquery_client
from ..exceptions import MCPBigQueryError, TableNotFoundError
from ..logging_config import get_logger
from ..utils import format_error_response
from ..validators import DescribeTableRequest, validate_request
from ._formatters import (
    format_schema_table,
    partitioning_details,
    serialize_schema_field,
    serialize_timestamp,
)

logger = get_logger(__name__)


async def describe_table(
    table_id: str,
    dataset_id: str,
    project_id: Optional[str] = None,
    format_output: bool = False,
) -> dict[str, Any]:
    """Return schema metadata for a single table."""
    try:
        request = validate_request(
            DescribeTableRequest,
            {
                "table_id": table_id,
                "dataset_id": dataset_id,
                "project_id": project_id,
                "format_output": format_output,
            },
        )
    except MCPBigQueryError as exc:
        return {"error": format_error_response(exc)}

    try:
        return await _describe_table_impl(request)
    except MCPBigQueryError as exc:
        return {"error": format_error_response(exc)}
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Unexpected error while describing table")
        wrapped = MCPBigQueryError(str(exc), code="DESCRIBE_TABLE_ERROR")
        return {"error": format_error_response(wrapped)}


async def _describe_table_impl(request: DescribeTableRequest) -> dict[str, Any]:
    client = get_bigquery_client(project_id=request.project_id)
    project = request.project_id or client.project

    try:
        table = client.get_table(f"{project}.{request.dataset_id}.{request.table_id}")
    except NotFound as exc:
        raise TableNotFoundError(request.table_id, request.dataset_id, project) from exc

    schema = [serialize_schema_field(field) for field in table.schema or []]

    result: dict[str, Any] = {
        "table_id": request.table_id,
        "dataset_id": request.dataset_id,
        "project": project,
        "table_type": table.table_type,
        "schema": schema,
        "description": table.description,
        "created": serialize_timestamp(table.created),
        "modified": serialize_timestamp(table.modified),
        "expires": serialize_timestamp(getattr(table, "expires", None)),
        "labels": table.labels or {},
        "statistics": {
            "num_bytes": getattr(table, "num_bytes", None),
            "num_rows": getattr(table, "num_rows", None),
            "num_long_term_bytes": getattr(table, "num_long_term_bytes", None),
        },
        "location": table.location,
    }

    partitioning = partitioning_details(table)
    if partitioning:
        result["partitioning"] = partitioning

    clustering = getattr(table, "clustering_fields", None)
    if clustering:
        result["clustering_fields"] = list(clustering)

    if request.format_output and schema:
        result["schema_formatted"] = format_schema_table(schema)

    return result
