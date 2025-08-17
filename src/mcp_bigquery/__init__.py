"""MCP BigQuery Server - MCP server for BigQuery SQL validation and dry-run."""

__version__ = "0.3.0"
__author__ = "caron14"
__email__ = "caron14@users.noreply.github.com"

from .server import (
    analyze_query_structure,
    dry_run_sql,
    extract_dependencies,
    server,
    validate_query_syntax,
    validate_sql,
)

__all__ = [
    "server",
    "validate_sql",
    "dry_run_sql",
    "analyze_query_structure",
    "extract_dependencies",
    "validate_query_syntax",
    "__version__",
]
