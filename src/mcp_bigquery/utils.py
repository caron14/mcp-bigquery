"""Utility functions for MCP BigQuery server."""

from __future__ import annotations

from typing import cast

from google.api_core.exceptions import GoogleAPIError

from .exceptions import MCPBigQueryError
from .exceptions import extract_error_location as exc_extract_error_location
from .exceptions import handle_bigquery_error
from .types import ErrorInfo, ErrorLocation


def extract_error_location(error_message: str) -> ErrorLocation | None:
    """Extract error location from BigQuery error message."""
    loc = exc_extract_error_location(error_message)
    if loc is not None:
        return cast(ErrorLocation, {"line": loc[0], "column": loc[1]})
    return None


def format_error_response(error: Exception) -> ErrorInfo:
    """Format an error into a standard error response."""
    if isinstance(error, MCPBigQueryError):
        return cast(ErrorInfo, error.to_dict())
    if isinstance(error, GoogleAPIError):
        bq_error = handle_bigquery_error(error)
        return cast(ErrorInfo, bq_error.to_dict())
    return {
        "code": "UNKNOWN_ERROR",
        "message": str(error),
        "location": None,
        "details": None,
    }
