"""MCP BigQuery Server - Minimal MCP server for BigQuery SQL validation and dry-run analysis."""

__version__ = "0.1.0"
__author__ = "caron14"
__email__ = "caron14@users.noreply.github.com"

from .server import server, validate_sql, dry_run_sql

__all__ = ["server", "validate_sql", "dry_run_sql", "__version__"]