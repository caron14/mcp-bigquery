"""Minimal type definitions for MCP BigQuery server."""

from typing import Any, TypedDict


class ErrorLocation(TypedDict):
    """Error location information."""

    line: int
    column: int


class ErrorInfo(TypedDict):
    """Error information structure."""

    code: str
    message: str
    location: ErrorLocation | None
    details: list[Any] | None
