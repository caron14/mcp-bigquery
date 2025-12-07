"""Table exploration helpers."""

from __future__ import annotations

from typing import Any, Optional

from google.cloud.exceptions import NotFound

from ..bigquery_client import get_bigquery_client
from ..exceptions import DatasetNotFoundError, MCPBigQueryError, TableNotFoundError
from ..logging_config import get_logger
from ..utils import format_error_response
from ..validators import GetTableInfoRequest, ListTablesRequest, validate_request
from ._formatters import (
    clustering_fields,
    external_table_info,
    materialized_view_info,
    partitioning_details,
    partitioning_overview,
    serialize_timestamp,
    streaming_buffer_info,
    table_statistics,
)

logger = get_logger(__name__)


async def list_tables(
    dataset_id: str,
    project_id: Optional[str] = None,
    max_results: Optional[int] = None,
    table_type_filter: Optional[list[str]] = None,
) -> dict[str, Any]:
    """List tables in a dataset."""
    try:
        request = validate_request(
            ListTablesRequest,
            {
                "dataset_id": dataset_id,
                "project_id": project_id,
                "max_results": max_results,
                "table_type_filter": table_type_filter,
            },
        )
    except MCPBigQueryError as exc:
        return {"error": format_error_response(exc)}

    try:
        return await _list_tables_impl(request)
    except MCPBigQueryError as exc:
        return {"error": format_error_response(exc)}
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Unexpected error while listing tables")
        wrapped = MCPBigQueryError(str(exc), code="LIST_TABLES_ERROR")
        return {"error": format_error_response(wrapped)}


async def _list_tables_impl(request: ListTablesRequest) -> dict[str, Any]:
    client = get_bigquery_client(project_id=request.project_id)
    project = request.project_id or client.project

    try:
        list_kwargs: dict[str, Any] = {"dataset": f"{project}.{request.dataset_id}"}
        if request.max_results is not None:
            list_kwargs["max_results"] = request.max_results

        iterator = client.list_tables(**list_kwargs)
    except NotFound as exc:
        raise DatasetNotFoundError(request.dataset_id, project) from exc

    allowed_types = set(request.table_type_filter) if request.table_type_filter else None
    tables: list[dict[str, Any]] = []

    for table in iterator:
        try:
            table_ref = client.get_table(table.reference)
        except NotFound as exc:
            raise TableNotFoundError(table.table_id, request.dataset_id, project) from exc

        table_type = table_ref.table_type
        if allowed_types and table_type not in allowed_types:
            continue

        partitioning = partitioning_overview(table_ref)
        clustering = clustering_fields(table_ref)

        table_info: dict[str, Any] = {
            "table_id": table.table_id,
            "dataset_id": table.dataset_id,
            "project": table.project,
            "table_type": table_type,
            "created": serialize_timestamp(table_ref.created),
            "modified": serialize_timestamp(table_ref.modified),
            "description": table_ref.description,
            "labels": table_ref.labels or {},
            "num_bytes": getattr(table_ref, "num_bytes", None),
            "num_rows": getattr(table_ref, "num_rows", None),
            "location": table_ref.location,
        }

        if partitioning:
            table_info["partitioning"] = partitioning
        if clustering:
            table_info["clustering_fields"] = clustering

        tables.append(table_info)

    return {
        "dataset_id": request.dataset_id,
        "project": project,
        "table_count": len(tables),
        "tables": tables,
    }


async def get_table_info(
    table_id: str,
    dataset_id: str,
    project_id: Optional[str] = None,
) -> dict[str, Any]:
    """Return comprehensive metadata for a table."""
    try:
        request = validate_request(
            GetTableInfoRequest,
            {"table_id": table_id, "dataset_id": dataset_id, "project_id": project_id},
        )
    except MCPBigQueryError as exc:
        return {"error": format_error_response(exc)}

    try:
        return await _get_table_info_impl(request)
    except MCPBigQueryError as exc:
        return {"error": format_error_response(exc)}
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Unexpected error while fetching table info")
        wrapped = MCPBigQueryError(str(exc), code="GET_TABLE_INFO_ERROR")
        return {"error": format_error_response(wrapped)}


async def _get_table_info_impl(request: GetTableInfoRequest) -> dict[str, Any]:
    client = get_bigquery_client(project_id=request.project_id)
    project = request.project_id or client.project

    try:
        table = client.get_table(f"{project}.{request.dataset_id}.{request.table_id}")
    except NotFound as exc:
        raise TableNotFoundError(request.table_id, request.dataset_id, project) from exc

    info: dict[str, Any] = {
        "table_id": request.table_id,
        "dataset_id": request.dataset_id,
        "project": project,
        "full_table_id": f"{project}.{request.dataset_id}.{request.table_id}",
        "table_type": table.table_type,
        "created": serialize_timestamp(table.created),
        "modified": serialize_timestamp(table.modified),
        "expires": serialize_timestamp(getattr(table, "expires", None)),
        "description": table.description,
        "labels": table.labels or {},
        "location": table.location,
        "self_link": getattr(table, "self_link", None),
        "etag": getattr(table, "etag", None),
        "encryption_configuration": (
            {"kms_key_name": table.encryption_configuration.kms_key_name}
            if getattr(table, "encryption_configuration", None)
            else None
        ),
        "friendly_name": getattr(table, "friendly_name", None),
        "statistics": table_statistics(table),
        "schema_field_count": len(table.schema) if table.schema else 0,
    }

    if table.table_type == "TABLE":
        info["time_travel"] = {
            "max_time_travel_hours": getattr(table, "max_time_travel_hours", 168),
        }

    if table.table_type == "VIEW":
        info["view"] = {
            "query": getattr(table, "view_query", None),
            "use_legacy_sql": getattr(table, "view_use_legacy_sql", None),
        }

    materialized = materialized_view_info(table)
    if materialized:
        info["materialized_view"] = materialized

    external = external_table_info(table)
    if external:
        info["external"] = external

    streaming = streaming_buffer_info(table)
    if streaming:
        info["streaming_buffer"] = streaming

    partitioning = partitioning_details(table)
    if partitioning:
        info["partitioning"] = partitioning

    clustering = clustering_fields(table)
    if clustering:
        info["clustering"] = {"fields": clustering}

    if getattr(table, "table_constraints", None):
        constraints = table.table_constraints
        info["table_constraints"] = {
            "primary_key": (constraints.primary_key.columns if constraints.primary_key else None),
            "foreign_keys": (
                [
                    {
                        "name": fk.name,
                        "referenced_table": fk.referenced_table.table_id,
                        "column_references": fk.column_references,
                    }
                    for fk in constraints.foreign_keys
                ]
                if constraints.foreign_keys
                else []
            ),
        }

    return info
