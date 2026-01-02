"""Constants for MCP BigQuery server."""

from enum import Enum


class TableType(Enum):
    """BigQuery table types."""

    TABLE = "TABLE"
    VIEW = "VIEW"
    EXTERNAL = "EXTERNAL"
    MATERIALIZED_VIEW = "MATERIALIZED_VIEW"
    SNAPSHOT = "SNAPSHOT"


REGEX_PATTERNS = {"error_location": r"\[(\d+):(\d+)\]"}
