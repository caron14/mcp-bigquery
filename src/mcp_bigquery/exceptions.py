"""Custom exceptions for MCP BigQuery server."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any, cast

from google.api_core.exceptions import (
    BadRequest,
    Conflict,
    Forbidden,
    GoogleAPIError,
    InternalServerError,
    NotFound,
    ServiceUnavailable,
    TooManyRequests,
    Unauthorized,
)


class MCPBigQueryError(Exception):
    """Base exception for MCP BigQuery server."""

    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or "UNKNOWN_ERROR"
        self.details = details

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for response."""
        result: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.details is not None:
            result["details"] = self.details
        return result


class SQLValidationError(MCPBigQueryError):
    """SQL validation error."""

    def __init__(
        self,
        message: str,
        location: tuple[int, int] | None = None,
        details: Any | None = None,
    ) -> None:
        super().__init__(message, code="INVALID_SQL", details=details)
        self.location = location

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary with location information."""
        result = super().to_dict()
        if self.location is not None:
            result["location"] = {"line": self.location[0], "column": self.location[1]}
        return result


class SQLAnalysisError(MCPBigQueryError):
    """SQL analysis error."""

    def __init__(self, message: str, details: Any | None = None) -> None:
        super().__init__(message, code="ANALYSIS_ERROR", details=details)


class AuthenticationError(MCPBigQueryError):
    """Authentication error."""

    def __init__(self, message: str, details: Any | None = None) -> None:
        super().__init__(message, code="AUTH_ERROR", details=details)


class ConfigurationError(MCPBigQueryError):
    """Configuration error."""

    def __init__(self, message: str, details: Any | None = None) -> None:
        super().__init__(message, code="CONFIG_ERROR", details=details)


class DatasetNotFoundError(MCPBigQueryError):
    """Dataset not found error."""

    def __init__(self, dataset_id: str, project_id: str | None = None) -> None:
        message = (
            f"Dataset not found: {project_id}.{dataset_id}"
            if project_id
            else f"Dataset not found: {dataset_id}"
        )
        super().__init__(message, code="DATASET_NOT_FOUND")
        self.dataset_id = dataset_id
        self.project_id = project_id


class TableNotFoundError(MCPBigQueryError):
    """Table not found error."""

    def __init__(self, table_id: str, dataset_id: str, project_id: str | None = None) -> None:
        message = (
            f"Table not found: {project_id}.{dataset_id}.{table_id}"
            if project_id
            else f"Table not found: {dataset_id}.{table_id}"
        )
        super().__init__(message, code="TABLE_NOT_FOUND")
        self.table_id = table_id
        self.dataset_id = dataset_id
        self.project_id = project_id


class PermissionError(MCPBigQueryError):
    """Permission error."""

    def __init__(self, message: str, resource: str | None = None) -> None:
        details = {"resource": resource} if resource else None
        super().__init__(message, code="PERMISSION_DENIED", details=details)


class RateLimitError(MCPBigQueryError):
    """Rate limit error."""

    def __init__(
        self, message: str = "Rate limit exceeded", retry_after: int | None = None
    ) -> None:
        details = {"retry_after": retry_after} if retry_after else None
        super().__init__(message, code="RATE_LIMIT_EXCEEDED", details=details)


class InvalidParameterError(MCPBigQueryError):
    """Invalid parameter error."""

    def __init__(self, parameter: str, message: str, expected_type: str | None = None) -> None:
        full_message = f"Invalid parameter '{parameter}': {message}"
        details = (
            {"parameter": parameter, "expected_type": expected_type}
            if expected_type
            else {"parameter": parameter}
        )
        super().__init__(full_message, code="INVALID_PARAMETER", details=details)


def extract_error_location(error_message: str) -> tuple[int, int] | None:
    """Extract error location (line, column) from BigQuery error message."""
    from .constants import REGEX_PATTERNS

    # 1. Bracket format: [line:col] or at [line:col]
    match1 = re.search(REGEX_PATTERNS["error_location_brackets"], error_message)
    if match1:
        return int(match1.group(1)), int(match1.group(2))

    # 2. Near line format: near line X, column Y or at line X, column Y
    match2 = re.search(REGEX_PATTERNS["error_location_near_line_col"], error_message, re.IGNORECASE)
    if match2:
        line = int(match2.group(1))
        col = int(match2.group(2)) if match2.group(2) else 1
        return line, col

    # 3. Near X:Y format: near X:Y
    match3 = re.search(REGEX_PATTERNS["error_location_near_xy"], error_message, re.IGNORECASE)
    if match3:
        return int(match3.group(1)), int(match3.group(2))

    return None


def _handle_not_found(error: GoogleAPIError) -> MCPBigQueryError:
    msg = str(error).lower()
    if "dataset" in msg:
        match = re.search(r"dataset\s+([a-zA-Z0-9_-]+:[a-zA-Z0-9_-]+|[a-zA-Z0-9_-]+)", msg)
        dataset_id = match.group(1) if match else "unknown"
        if ":" in dataset_id:
            project_id, dataset_id = dataset_id.split(":", 1)
            return DatasetNotFoundError(dataset_id, project_id)
        return DatasetNotFoundError(dataset_id)
    elif "table" in msg:
        match = re.search(
            r"table\s+([a-zA-Z0-9_-]+:[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+|[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+)",
            msg,
        )
        if match:
            table_ref = match.group(1)
            parts = table_ref.replace(":", ".").split(".")
            if len(parts) == 3:
                return TableNotFoundError(parts[2], parts[1], parts[0])
            elif len(parts) == 2:
                return TableNotFoundError(parts[1], parts[0])
        return TableNotFoundError("unknown", "unknown")
    return MCPBigQueryError(str(error), code="NOT_FOUND")


def _handle_bad_request(error: GoogleAPIError) -> MCPBigQueryError:
    error_message = str(error)
    loc = extract_error_location(error_message)
    errors = getattr(error, "errors", None)
    if loc is not None:
        return SQLValidationError(error_message, location=loc, details=errors)
    return SQLValidationError(error_message, details=errors)


# Declare types for mapping
ErrorHandler = type[MCPBigQueryError] | Callable[[GoogleAPIError], MCPBigQueryError]

ERROR_MAPPING: dict[type[GoogleAPIError], ErrorHandler] = {
    NotFound: _handle_not_found,
    Forbidden: PermissionError,
    Unauthorized: AuthenticationError,
    TooManyRequests: RateLimitError,
    BadRequest: _handle_bad_request,
    Conflict: lambda err: MCPBigQueryError(str(err), code="CONFLICT"),
    ServiceUnavailable: lambda err: MCPBigQueryError(str(err), code="SERVICE_UNAVAILABLE"),
    InternalServerError: lambda err: MCPBigQueryError(str(err), code="INTERNAL_ERROR"),
}


def handle_bigquery_error(error: GoogleAPIError) -> MCPBigQueryError:
    """Convert Google API errors to MCP BigQuery errors using declarative mapping."""
    error_class = type(error)

    # Exact match check
    if error_class in ERROR_MAPPING:
        handler = ERROR_MAPPING[error_class]
        if isinstance(handler, type):
            return cast(type[MCPBigQueryError], handler)(str(error))
        else:
            return handler(error)

    # Subclass match check
    for exc_type, handler in ERROR_MAPPING.items():
        if isinstance(error, exc_type):
            if isinstance(handler, type):
                return cast(type[MCPBigQueryError], handler)(str(error))
            else:
                return handler(error)

    # Fallback string matching
    error_message = str(error)
    if "403" in error_message or "permission" in error_message.lower():
        return PermissionError(error_message)
    elif "404" in error_message:
        return _handle_not_found(error)
    elif "401" in error_message or "authentication" in error_message.lower():
        return AuthenticationError(error_message)
    elif "429" in error_message or "quota" in error_message.lower():
        return RateLimitError(error_message)
    elif "400" in error_message:
        return _handle_bad_request(error)

    return MCPBigQueryError(error_message)
