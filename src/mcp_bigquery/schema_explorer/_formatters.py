"""Helper utilities for shaping schema explorer responses."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any

from tabulate import tabulate


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


def partitioning_overview(table: Any) -> dict[str, Any] | None:
    """Extract lightweight partitioning information for table listings."""
    if not getattr(table, "partitioning_type", None):
        return None

    info: dict[str, Any] = {"type": table.partitioning_type}
    time_partitioning = getattr(table, "time_partitioning", None)
    if time_partitioning:
        info["field"] = time_partitioning.field
        info["expiration_ms"] = time_partitioning.expiration_ms

    return info


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


def clustering_fields(table: Any) -> list[str] | None:
    """Return clustering fields if present."""
    fields = getattr(table, "clustering_fields", None)
    return list(fields) if fields else None


def streaming_buffer_info(table: Any) -> dict[str, Any] | None:
    """Return streaming buffer metadata when available."""
    buffer = getattr(table, "streaming_buffer", None)
    if not buffer:
        return None

    return {
        "estimated_bytes": buffer.estimated_bytes,
        "estimated_rows": buffer.estimated_rows,
        "oldest_entry_time": serialize_timestamp(buffer.oldest_entry_time),
    }


def materialized_view_info(table: Any) -> dict[str, Any] | None:
    """Return materialized view metadata when available."""
    if getattr(table, "table_type", None) != "MATERIALIZED_VIEW":
        return None

    return {
        "query": getattr(table, "mview_query", None),
        "last_refresh_time": serialize_timestamp(getattr(table, "mview_last_refresh_time", None)),
        "enable_refresh": getattr(table, "mview_enable_refresh", None),
        "refresh_interval_minutes": getattr(table, "mview_refresh_interval_minutes", None),
    }


def external_table_info(table: Any) -> dict[str, Any] | None:
    """Return external table configuration when available."""
    if getattr(table, "table_type", None) != "EXTERNAL":
        return None

    config = getattr(table, "external_data_configuration", None)
    if not config:
        return None

    return {
        "source_uris": list(getattr(config, "source_uris", []) or []),
        "source_format": getattr(config, "source_format", None),
    }


def table_statistics(table: Any) -> dict[str, Any]:
    """Collect common table statistics into a dict."""
    return {
        "creation_time": serialize_timestamp(getattr(table, "created", None)),
        "last_modified_time": serialize_timestamp(getattr(table, "modified", None)),
        "num_bytes": getattr(table, "num_bytes", None),
        "num_long_term_bytes": getattr(table, "num_long_term_bytes", None),
        "num_rows": getattr(table, "num_rows", None),
        "num_active_logical_bytes": getattr(table, "num_active_logical_bytes", None),
        "num_active_physical_bytes": getattr(table, "num_active_physical_bytes", None),
        "num_long_term_logical_bytes": getattr(table, "num_long_term_logical_bytes", None),
        "num_long_term_physical_bytes": getattr(table, "num_long_term_physical_bytes", None),
        "num_total_logical_bytes": getattr(table, "num_total_logical_bytes", None),
        "num_total_physical_bytes": getattr(table, "num_total_physical_bytes", None),
    }
