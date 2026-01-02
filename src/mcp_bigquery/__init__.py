"""MCP BigQuery Server - MCP server for BigQuery SQL validation and dry-run."""

__version__ = "0.5.0"
__author__ = "caron14"
__email__ = "caron14@users.noreply.github.com"

from .schema_explorer import describe_table, get_table_info, list_datasets, list_tables
from .server import dry_run_sql, extract_dependencies, server, validate_query_syntax, validate_sql

__all__ = [
    "server",
    "validate_sql",
    "dry_run_sql",
    "extract_dependencies",
    "validate_query_syntax",
    "list_datasets",
    "list_tables",
    "describe_table",
    "get_table_info",
    "__version__",
]
