"""BigQuery schema exploration utilities for datasets and tables."""

import datetime
from typing import Any, Optional

from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from tabulate import tabulate

from .bigquery_client import get_bigquery_client


async def list_datasets(
    project_id: Optional[str] = None, max_results: Optional[int] = None
) -> dict[str, Any]:
    """
    List all datasets in the project.

    Args:
        project_id: GCP project ID (uses default if not provided)
        max_results: Maximum number of datasets to return

    Returns:
        Dict with list of datasets and their metadata
    """
    try:
        # Input validation
        if max_results is not None and max_results <= 0:
            return {
                "error": {
                    "code": "INVALID_PARAMETER",
                    "message": "max_results must be a positive integer",
                }
            }

        client = get_bigquery_client()

        # Use provided project_id or client's default
        project = project_id or client.project

        datasets = []
        dataset_list = client.list_datasets(project=project, max_results=max_results)

        for dataset in dataset_list:
            dataset_ref = client.get_dataset(dataset.reference)
            datasets.append(
                {
                    "dataset_id": dataset.dataset_id,
                    "project": dataset.project,
                    "location": dataset_ref.location,
                    "created": dataset_ref.created.isoformat() if dataset_ref.created else None,
                    "modified": dataset_ref.modified.isoformat() if dataset_ref.modified else None,
                    "description": dataset_ref.description,
                    "labels": dataset_ref.labels or {},
                    "default_table_expiration_ms": dataset_ref.default_table_expiration_ms,
                    "default_partition_expiration_ms": dataset_ref.default_partition_expiration_ms,
                }
            )

        return {"project": project, "dataset_count": len(datasets), "datasets": datasets}

    except Exception as e:
        return {"error": {"code": "LIST_DATASETS_ERROR", "message": str(e)}}


async def list_tables(
    dataset_id: str,
    project_id: Optional[str] = None,
    max_results: Optional[int] = None,
    table_type_filter: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    List all tables in a dataset.

    Args:
        dataset_id: The dataset ID
        project_id: GCP project ID (uses default if not provided)
        max_results: Maximum number of tables to return
        table_type_filter: Filter by table types (TABLE, VIEW, EXTERNAL, MATERIALIZED_VIEW)

    Returns:
        Dict with list of tables and their metadata
    """
    try:
        # Input validation
        if not dataset_id or not dataset_id.strip():
            return {
                "error": {
                    "code": "INVALID_PARAMETER",
                    "message": "dataset_id is required and cannot be empty",
                }
            }

        if max_results is not None and max_results <= 0:
            return {
                "error": {
                    "code": "INVALID_PARAMETER",
                    "message": "max_results must be a positive integer",
                }
            }

        valid_table_types = {"TABLE", "VIEW", "EXTERNAL", "MATERIALIZED_VIEW"}
        if table_type_filter:
            invalid_types = set(table_type_filter) - valid_table_types
            if invalid_types:
                return {
                    "error": {
                        "code": "INVALID_PARAMETER",
                        "message": f"Invalid table types: {', '.join(invalid_types)}. Valid types are: {', '.join(sorted(valid_table_types))}",
                    }
                }

        client = get_bigquery_client()
        project = project_id or client.project

        tables = []
        table_list = client.list_tables(f"{project}.{dataset_id}", max_results=max_results)

        for table in table_list:
            # Get full table metadata
            table_ref = client.get_table(table.reference)

            table_type = table_ref.table_type

            # Apply type filter if specified
            if table_type_filter and table_type not in table_type_filter:
                continue

            table_info = {
                "table_id": table.table_id,
                "dataset_id": table.dataset_id,
                "project": table.project,
                "table_type": table_type,
                "created": table_ref.created.isoformat() if table_ref.created else None,
                "modified": table_ref.modified.isoformat() if table_ref.modified else None,
                "description": table_ref.description,
                "labels": table_ref.labels or {},
                "num_bytes": table_ref.num_bytes,
                "num_rows": table_ref.num_rows,
                "location": table_ref.location,
            }

            # Add partitioning info if exists
            if table_ref.partitioning_type:
                table_info["partitioning"] = {
                    "type": table_ref.partitioning_type,
                    "field": (
                        table_ref.time_partitioning.field if table_ref.time_partitioning else None
                    ),
                    "expiration_ms": (
                        table_ref.time_partitioning.expiration_ms
                        if table_ref.time_partitioning
                        else None
                    ),
                }

            # Add clustering info if exists
            if table_ref.clustering_fields:
                table_info["clustering_fields"] = table_ref.clustering_fields

            tables.append(table_info)

        return {
            "dataset_id": dataset_id,
            "project": project,
            "table_count": len(tables),
            "tables": tables,
        }

    except NotFound:
        return {
            "error": {
                "code": "DATASET_NOT_FOUND",
                "message": f"Dataset '{dataset_id}' not found in project '{project_id or client.project}'",
            }
        }
    except Exception as e:
        return {"error": {"code": "LIST_TABLES_ERROR", "message": str(e)}}


async def describe_table(
    table_id: str, dataset_id: str, project_id: Optional[str] = None, format_output: bool = False
) -> dict[str, Any]:
    """
    Get detailed schema and metadata for a table.

    Args:
        table_id: The table ID
        dataset_id: The dataset ID
        project_id: GCP project ID (uses default if not provided)
        format_output: Whether to format schema as table string

    Returns:
        Dict with table schema, metadata, and statistics
    """
    try:
        # Input validation
        if not table_id or not table_id.strip():
            return {
                "error": {
                    "code": "INVALID_PARAMETER",
                    "message": "table_id is required and cannot be empty",
                }
            }

        if not dataset_id or not dataset_id.strip():
            return {
                "error": {
                    "code": "INVALID_PARAMETER",
                    "message": "dataset_id is required and cannot be empty",
                }
            }

        client = get_bigquery_client()
        project = project_id or client.project

        table_ref = client.get_table(f"{project}.{dataset_id}.{table_id}")

        # Extract schema information
        schema = []
        for field in table_ref.schema:
            field_info = {
                "name": field.name,
                "type": field.field_type,
                "mode": field.mode,
                "description": field.description,
            }

            # Handle nested fields
            if field.fields:
                field_info["fields"] = [
                    {
                        "name": subfield.name,
                        "type": subfield.field_type,
                        "mode": subfield.mode,
                        "description": subfield.description,
                    }
                    for subfield in field.fields
                ]

            schema.append(field_info)

        result = {
            "table_id": table_id,
            "dataset_id": dataset_id,
            "project": project,
            "table_type": table_ref.table_type,
            "schema": schema,
            "description": table_ref.description,
            "created": table_ref.created.isoformat() if table_ref.created else None,
            "modified": table_ref.modified.isoformat() if table_ref.modified else None,
            "expires": table_ref.expires.isoformat() if table_ref.expires else None,
            "labels": table_ref.labels or {},
            "statistics": {
                "num_bytes": table_ref.num_bytes,
                "num_rows": table_ref.num_rows,
                "num_long_term_bytes": table_ref.num_long_term_bytes,
            },
            "location": table_ref.location,
        }

        # Add partitioning details
        if table_ref.partitioning_type:
            result["partitioning"] = {
                "type": table_ref.partitioning_type,
            }
            if table_ref.time_partitioning:
                result["partitioning"]["field"] = table_ref.time_partitioning.field
                result["partitioning"]["expiration_ms"] = table_ref.time_partitioning.expiration_ms
                result["partitioning"][
                    "require_partition_filter"
                ] = table_ref.time_partitioning.require_partition_filter

            if table_ref.range_partitioning:
                result["partitioning"]["range"] = {
                    "field": table_ref.range_partitioning.field,
                    "start": table_ref.range_partitioning.range_.start,
                    "end": table_ref.range_partitioning.range_.end,
                    "interval": table_ref.range_partitioning.range_.interval,
                }

        # Add clustering details
        if table_ref.clustering_fields:
            result["clustering_fields"] = table_ref.clustering_fields

        # Format schema as table if requested
        if format_output and schema:
            headers = ["Field", "Type", "Mode", "Description"]
            rows = []
            for field in schema:
                rows.append(
                    [
                        field["name"],
                        field["type"],
                        field["mode"],
                        field.get("description", "")[:50],  # Truncate long descriptions
                    ]
                )
            result["schema_formatted"] = tabulate(rows, headers=headers, tablefmt="grid")

        return result

    except NotFound:
        return {
            "error": {
                "code": "TABLE_NOT_FOUND",
                "message": f"Table '{project}.{dataset_id}.{table_id}' not found",
            }
        }
    except Exception as e:
        return {"error": {"code": "DESCRIBE_TABLE_ERROR", "message": str(e)}}


async def get_table_info(
    table_id: str, dataset_id: str, project_id: Optional[str] = None
) -> dict[str, Any]:
    """
    Get comprehensive table information including all metadata.

    Args:
        table_id: The table ID
        dataset_id: The dataset ID
        project_id: GCP project ID (uses default if not provided)

    Returns:
        Dict with comprehensive table information
    """
    try:
        # Input validation
        if not table_id or not table_id.strip():
            return {
                "error": {
                    "code": "INVALID_PARAMETER",
                    "message": "table_id is required and cannot be empty",
                }
            }

        if not dataset_id or not dataset_id.strip():
            return {
                "error": {
                    "code": "INVALID_PARAMETER",
                    "message": "dataset_id is required and cannot be empty",
                }
            }

        client = get_bigquery_client()
        project = project_id or client.project

        table_ref = client.get_table(f"{project}.{dataset_id}.{table_id}")

        info = {
            "table_id": table_id,
            "dataset_id": dataset_id,
            "project": project,
            "full_table_id": f"{project}.{dataset_id}.{table_id}",
            "table_type": table_ref.table_type,
            "created": table_ref.created.isoformat() if table_ref.created else None,
            "modified": table_ref.modified.isoformat() if table_ref.modified else None,
            "expires": table_ref.expires.isoformat() if table_ref.expires else None,
            "description": table_ref.description,
            "labels": table_ref.labels or {},
            "location": table_ref.location,
            "self_link": table_ref.self_link,
            "etag": table_ref.etag,
            "encryption_configuration": (
                {"kms_key_name": table_ref.encryption_configuration.kms_key_name}
                if table_ref.encryption_configuration
                else None
            ),
            "friendly_name": table_ref.friendly_name,
            "statistics": {
                "creation_time": table_ref.created.isoformat() if table_ref.created else None,
                "last_modified_time": (
                    table_ref.modified.isoformat() if table_ref.modified else None
                ),
                "num_bytes": table_ref.num_bytes,
                "num_long_term_bytes": table_ref.num_long_term_bytes,
                "num_rows": table_ref.num_rows,
                "num_active_logical_bytes": table_ref.num_active_logical_bytes,
                "num_active_physical_bytes": table_ref.num_active_physical_bytes,
                "num_long_term_logical_bytes": table_ref.num_long_term_logical_bytes,
                "num_long_term_physical_bytes": table_ref.num_long_term_physical_bytes,
                "num_total_logical_bytes": table_ref.num_total_logical_bytes,
                "num_total_physical_bytes": table_ref.num_total_physical_bytes,
            },
            "schema_field_count": len(table_ref.schema) if table_ref.schema else 0,
        }

        # Add time travel information for TABLE type
        if table_ref.table_type == "TABLE":
            info["time_travel"] = {
                "max_time_travel_hours": (
                    table_ref.max_time_travel_hours
                    if hasattr(table_ref, "max_time_travel_hours")
                    else 168
                ),  # Default 7 days
            }

        # Add view-specific information
        if table_ref.table_type == "VIEW":
            info["view"] = {
                "query": table_ref.view_query,
                "use_legacy_sql": table_ref.view_use_legacy_sql,
            }

        # Add materialized view information
        if table_ref.table_type == "MATERIALIZED_VIEW":
            info["materialized_view"] = {
                "query": table_ref.mview_query if hasattr(table_ref, "mview_query") else None,
                "last_refresh_time": (
                    table_ref.mview_last_refresh_time.isoformat()
                    if hasattr(table_ref, "mview_last_refresh_time")
                    and table_ref.mview_last_refresh_time
                    else None
                ),
                "enable_refresh": (
                    table_ref.mview_enable_refresh
                    if hasattr(table_ref, "mview_enable_refresh")
                    else None
                ),
                "refresh_interval_minutes": (
                    table_ref.mview_refresh_interval_minutes
                    if hasattr(table_ref, "mview_refresh_interval_minutes")
                    else None
                ),
            }

        # Add external table information
        if table_ref.table_type == "EXTERNAL":
            info["external"] = {
                "source_uris": (
                    table_ref.external_data_configuration.source_uris
                    if table_ref.external_data_configuration
                    else []
                ),
                "source_format": (
                    table_ref.external_data_configuration.source_format
                    if table_ref.external_data_configuration
                    else None
                ),
            }

        # Add streaming buffer information if available
        if table_ref.streaming_buffer:
            info["streaming_buffer"] = {
                "estimated_bytes": table_ref.streaming_buffer.estimated_bytes,
                "estimated_rows": table_ref.streaming_buffer.estimated_rows,
                "oldest_entry_time": (
                    table_ref.streaming_buffer.oldest_entry_time.isoformat()
                    if table_ref.streaming_buffer.oldest_entry_time
                    else None
                ),
            }

        # Add partitioning details
        if table_ref.partitioning_type:
            info["partitioning"] = {
                "type": table_ref.partitioning_type,
            }
            if table_ref.time_partitioning:
                info["partitioning"]["time_partitioning"] = {
                    "type": table_ref.time_partitioning.type_,
                    "field": table_ref.time_partitioning.field,
                    "expiration_ms": table_ref.time_partitioning.expiration_ms,
                    "require_partition_filter": table_ref.time_partitioning.require_partition_filter,
                }
            if table_ref.range_partitioning:
                info["partitioning"]["range_partitioning"] = {
                    "field": table_ref.range_partitioning.field,
                    "range": {
                        "start": table_ref.range_partitioning.range_.start,
                        "end": table_ref.range_partitioning.range_.end,
                        "interval": table_ref.range_partitioning.range_.interval,
                    },
                }

        # Add clustering information
        if table_ref.clustering_fields:
            info["clustering"] = {"fields": table_ref.clustering_fields}

        # Add table constraints if available
        if hasattr(table_ref, "table_constraints") and table_ref.table_constraints:
            info["table_constraints"] = {
                "primary_key": (
                    table_ref.table_constraints.primary_key.columns
                    if table_ref.table_constraints.primary_key
                    else None
                ),
                "foreign_keys": (
                    [
                        {
                            "name": fk.name,
                            "referenced_table": fk.referenced_table.table_id,
                            "column_references": fk.column_references,
                        }
                        for fk in table_ref.table_constraints.foreign_keys
                    ]
                    if table_ref.table_constraints.foreign_keys
                    else []
                ),
            }

        return info

    except NotFound:
        return {
            "error": {
                "code": "TABLE_NOT_FOUND",
                "message": f"Table '{project}.{dataset_id}.{table_id}' not found",
            }
        }
    except Exception as e:
        return {"error": {"code": "GET_TABLE_INFO_ERROR", "message": str(e)}}
