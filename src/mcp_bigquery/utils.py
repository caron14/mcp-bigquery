"""Utility functions for MCP BigQuery server."""

import re

from google.api_core.exceptions import GoogleAPIError

from .constants import REGEX_PATTERNS
from .exceptions import MCPBigQueryError, handle_bigquery_error
from .types import ErrorInfo, ErrorLocation


def extract_error_location(error_message: str) -> ErrorLocation | None:
    """Extract error location from BigQuery error message."""
    match = re.search(REGEX_PATTERNS["error_location"], error_message)
    if match:
        return ErrorLocation(line=int(match.group(1)), column=int(match.group(2)))
    return None


def format_error_response(error: Exception | MCPBigQueryError) -> ErrorInfo:
    """Format an error into a standard error response."""
    if isinstance(error, MCPBigQueryError):
        return error.to_dict()
    if isinstance(error, GoogleAPIError):
        bq_error = handle_bigquery_error(error)
        return bq_error.to_dict()
    return ErrorInfo(code="UNKNOWN_ERROR", message=str(error), location=None, details=None)
