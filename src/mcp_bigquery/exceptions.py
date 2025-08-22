"""Custom exceptions for MCP BigQuery server."""

from typing import Any, Optional

from google.api_core.exceptions import GoogleAPIError


class MCPBigQueryError(Exception):
    """Base exception for MCP BigQuery server."""

    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.code = code or "UNKNOWN_ERROR"
        self.details = details

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for response."""
        result = {"code": self.code, "message": self.message}
        if self.details:
            result["details"] = self.details
        return result


class SQLValidationError(MCPBigQueryError):
    """SQL validation error."""

    def __init__(
        self,
        message: str,
        location: Optional[tuple[int, int]] = None,
        details: Optional[Any] = None,
    ):
        super().__init__(message, code="INVALID_SQL", details=details)
        self.location = location

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary with location information."""
        result = super().to_dict()
        if self.location:
            result["location"] = {"line": self.location[0], "column": self.location[1]}
        return result


class SQLAnalysisError(MCPBigQueryError):
    """SQL analysis error."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, code="ANALYSIS_ERROR", details=details)


class AuthenticationError(MCPBigQueryError):
    """Authentication error."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, code="AUTH_ERROR", details=details)


class ConfigurationError(MCPBigQueryError):
    """Configuration error."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, code="CONFIG_ERROR", details=details)


class DatasetNotFoundError(MCPBigQueryError):
    """Dataset not found error."""

    def __init__(self, dataset_id: str, project_id: Optional[str] = None):
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

    def __init__(self, table_id: str, dataset_id: str, project_id: Optional[str] = None):
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

    def __init__(self, message: str, resource: Optional[str] = None):
        details = {"resource": resource} if resource else None
        super().__init__(message, code="PERMISSION_DENIED", details=details)


class RateLimitError(MCPBigQueryError):
    """Rate limit error."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        details = {"retry_after": retry_after} if retry_after else None
        super().__init__(message, code="RATE_LIMIT_EXCEEDED", details=details)


class InvalidParameterError(MCPBigQueryError):
    """Invalid parameter error."""

    def __init__(self, parameter: str, message: str, expected_type: Optional[str] = None):
        full_message = f"Invalid parameter '{parameter}': {message}"
        details = (
            {"parameter": parameter, "expected_type": expected_type}
            if expected_type
            else {"parameter": parameter}
        )
        super().__init__(full_message, code="INVALID_PARAMETER", details=details)


def handle_bigquery_error(error: GoogleAPIError) -> MCPBigQueryError:
    """Convert Google API errors to MCP BigQuery errors."""
    error_message = str(error)

    # Check for specific error types
    if "403" in error_message or "permission" in error_message.lower():
        return PermissionError(error_message)
    elif "404" in error_message:
        if "dataset" in error_message.lower():
            # Extract dataset ID from error message if possible
            return DatasetNotFoundError("unknown")
        elif "table" in error_message.lower():
            # Extract table ID from error message if possible
            return TableNotFoundError("unknown", "unknown")
        else:
            return MCPBigQueryError(error_message, code="NOT_FOUND")
    elif "401" in error_message or "authentication" in error_message.lower():
        return AuthenticationError(error_message)
    elif "429" in error_message or "quota" in error_message.lower():
        return RateLimitError(error_message)
    elif "400" in error_message:
        # Extract location from error message if present
        import re

        location_match = re.search(r"\[(\d+):(\d+)\]", error_message)
        if location_match:
            location = (int(location_match.group(1)), int(location_match.group(2)))
            return SQLValidationError(error_message, location=location)
        else:
            return SQLValidationError(error_message)
    else:
        return MCPBigQueryError(error_message)
