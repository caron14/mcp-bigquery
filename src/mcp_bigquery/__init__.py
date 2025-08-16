"""MCP BigQuery Server - MCP server for BigQuery SQL validation and dry-run."""

__version__ = "0.1.0"
__author__ = "caron14"
__email__ = "caron14@users.noreply.github.com"

from .server import dry_run_sql, server, validate_sql

__all__ = ["server", "validate_sql", "dry_run_sql", "__version__"]
