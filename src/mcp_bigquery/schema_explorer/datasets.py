"""Dataset exploration helpers."""

from __future__ import annotations

from typing import Any

from ..bigquery_client import get_bigquery_client
from ..exceptions import MCPBigQueryError
from ..logging_config import get_logger
from ..utils import format_error_response
from ..validators import ListDatasetsRequest, validate_request
from ._formatters import serialize_timestamp

logger = get_logger(__name__)


async def list_datasets(
    project_id: str | None = None,
    max_results: int | None = None,
) -> dict[str, Any]:
    """List datasets along with core metadata."""
    try:
        request = validate_request(
            ListDatasetsRequest,
            {"project_id": project_id, "max_results": max_results},
        )
    except MCPBigQueryError as exc:
        return {"error": format_error_response(exc)}

    try:
        return await _list_datasets_impl(request)
    except MCPBigQueryError as exc:
        return {"error": format_error_response(exc)}
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Unexpected error while listing datasets")
        wrapped = MCPBigQueryError(str(exc), code="LIST_DATASETS_ERROR")
        return {"error": format_error_response(wrapped)}


async def _list_datasets_impl(request: ListDatasetsRequest) -> dict[str, Any]:
    client = get_bigquery_client(project_id=request.project_id)
    project = request.project_id or client.project

    datasets = []
    list_kwargs: dict[str, Any] = {"project": project}
    if request.max_results is not None:
        list_kwargs["max_results"] = request.max_results

    iterator = client.list_datasets(**list_kwargs)

    for dataset in iterator:
        ref = client.get_dataset(dataset.reference)
        datasets.append(
            {
                "dataset_id": dataset.dataset_id,
                "project": dataset.project,
                "location": ref.location,
                "created": serialize_timestamp(ref.created),
                "modified": serialize_timestamp(ref.modified),
                "description": ref.description,
                "labels": ref.labels or {},
                "default_table_expiration_ms": ref.default_table_expiration_ms,
                "default_partition_expiration_ms": ref.default_partition_expiration_ms,
            }
        )

    return {
        "project": project,
        "dataset_count": len(datasets),
        "datasets": datasets,
    }
