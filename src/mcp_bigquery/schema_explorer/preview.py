"""Table data preview helpers."""

from __future__ import annotations

import base64
import datetime
from decimal import Decimal
from typing import Any

from google.api_core.exceptions import GoogleAPIError
from google.cloud.exceptions import NotFound

from ..clients import get_bigquery_client
from ..config import get_config
from ..exceptions import MCPBigQueryError, handle_bigquery_error
from ..logging_config import get_logger
from ..utils import format_error_response
from ..validators import PreviewTableRequest, validate_request

logger = get_logger(__name__)


def serialize_value(val: Any) -> Any:
    """Recursively serialize BigQuery data types for JSON output."""
    if isinstance(val, datetime.datetime | datetime.date | datetime.time):
        return val.isoformat()
    elif isinstance(val, Decimal):
        return float(val)
    elif isinstance(val, bytes):
        try:
            return val.decode("utf-8")
        except UnicodeDecodeError:
            return base64.b64encode(val).decode("utf-8")
    elif isinstance(val, dict):
        return {k: serialize_value(v) for k, v in val.items()}
    elif isinstance(val, list | tuple | set):
        return [serialize_value(item) for item in val]
    elif hasattr(val, "items") and callable(val.items):
        return {k: serialize_value(v) for k, v in val.items()}
    elif hasattr(val, "keys") and hasattr(val, "__getitem__"):
        return {k: serialize_value(val[k]) for k in val.keys()}
    return val


async def preview_table(
    dataset_id: str,
    table_id: str,
    project_id: str | None = None,
    max_results: int = 5,
) -> dict[str, Any]:
    """
    Preview rows from a table (cost-free).

    Only runs if the environment variable MCP_BQ_ENABLE_PREVIEW=true is set.
    """
    try:
        request = validate_request(
            PreviewTableRequest,
            {
                "dataset_id": dataset_id,
                "table_id": table_id,
                "project_id": project_id,
                "max_results": max_results,
            },
        )
    except MCPBigQueryError as exc:
        return {"error": format_error_response(exc)}

    try:
        config = get_config()
        if not config.enable_preview:
            raise MCPBigQueryError(
                "環境変数 MCP_BQ_ENABLE_PREVIEW=true を設定してください",
                code="PREVIEW_DISABLED",
            )

        return await _preview_table_impl(request)
    except MCPBigQueryError as exc:
        return {"error": format_error_response(exc)}
    except Exception as exc:
        logger.exception("Unexpected error while previewing table")
        wrapped = MCPBigQueryError(str(exc), code="PREVIEW_ERROR")
        return {"error": format_error_response(wrapped)}


async def _preview_table_impl(request: PreviewTableRequest) -> dict[str, Any]:
    client = get_bigquery_client(project_id=request.project_id)
    project = request.project_id or client.project
    limit = min(request.max_results, 10)

    try:
        table_ref = client.dataset(request.dataset_id, project=project).table(request.table_id)
        # Note: client.list_rows is lazy, so we convert it to list within try to trigger API call.
        rows_iterable = client.list_rows(table_ref, max_results=limit)
        rows = list(rows_iterable)
    except NotFound as exc:
        raise handle_bigquery_error(exc) from exc
    except GoogleAPIError as exc:
        raise handle_bigquery_error(exc) from exc
    except Exception as exc:
        logger.exception("Unexpected BQ client error during list_rows")
        raise MCPBigQueryError(str(exc), code="PREVIEW_API_ERROR") from exc

    if not rows:
        return {
            "dataset_id": request.dataset_id,
            "table_id": request.table_id,
            "project": project,
            "message": "テーブルは空です",
        }

    serialized_rows = [serialize_value(row) for row in rows]
    return {
        "dataset_id": request.dataset_id,
        "table_id": request.table_id,
        "project": project,
        "rows": serialized_rows,
    }
