"""Table schema description helpers."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any

from google.cloud.exceptions import NotFound
from tabulate import tabulate

from ..clients import get_bigquery_client
from ..exceptions import MCPBigQueryError, TableNotFoundError
from ..logging_config import get_logger
from ..utils import format_error_response
from ..validators import DescribeTableRequest, validate_request


def serialize_timestamp(value: datetime | None) -> str | None:
    """Return ISO 8601 strings for BigQuery timestamps."""
    return value.isoformat() if value else None


def serialize_schema_field(field: Any) -> dict[str, Any]:
    """Serialize a BigQuery schema field including nested children."""
    field_info: dict[str, Any] = {
        "name": field.name,
        "type": getattr(field, "field_type", getattr(field, "type", "")),
        "mode": field.mode,
        "description": getattr(field, "description", None),
    }

    if getattr(field, "fields", None):
        field_info["fields"] = [serialize_schema_field(child) for child in field.fields]

    return field_info


def format_schema_table(schema: Iterable[dict[str, Any]]) -> str:
    """Render schema information as a table for human-friendly output."""
    headers = ["Field", "Type", "Mode", "Description"]
    rows = [
        [
            field["name"],
            field["type"],
            field["mode"],
            (field.get("description") or "")[:50],
        ]
        for field in schema
    ]
    return tabulate(rows, headers=headers, tablefmt="grid")


def partitioning_details(table: Any) -> dict[str, Any] | None:
    """Extract detailed partitioning information for table metadata."""
    if not getattr(table, "partitioning_type", None):
        return None

    info: dict[str, Any] = {"type": table.partitioning_type}
    time_partitioning = getattr(table, "time_partitioning", None)
    if time_partitioning:
        info["time_partitioning"] = {
            "type": time_partitioning.type_,
            "field": time_partitioning.field,
            "expiration_ms": time_partitioning.expiration_ms,
            "require_partition_filter": time_partitioning.require_partition_filter,
        }

    range_partitioning = getattr(table, "range_partitioning", None)
    if range_partitioning:
        info["range_partitioning"] = {
            "field": range_partitioning.field,
            "range": {
                "start": range_partitioning.range_.start,
                "end": range_partitioning.range_.end,
                "interval": range_partitioning.range_.interval,
            },
        }

    return info


logger = get_logger(__name__)


async def describe_table(
    table_id: str,
    dataset_id: str,
    project_id: str | None = None,
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
