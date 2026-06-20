"""Constants for MCP BigQuery server."""

from enum import Enum


class TableType(Enum):
    """BigQuery table types."""

    TABLE = "TABLE"
    VIEW = "VIEW"
    EXTERNAL = "EXTERNAL"
    MATERIALIZED_VIEW = "MATERIALIZED_VIEW"
    SNAPSHOT = "SNAPSHOT"


REGEX_PATTERNS = {
    "error_location_brackets": r"\[(\d+)[:：](\d+)\]",
    "error_location_near_line_col": r"(?:near|at)\s+line\s+(\d+)(?:,\s+column\s+(\d+))?",
    "error_location_near_xy": r"(?:near|at)\s+(\d+)[:：](\d+)",
}
