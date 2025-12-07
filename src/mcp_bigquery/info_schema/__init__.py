"""Information schema entrypoints."""

from .performance import analyze_query_performance
from .queries import query_info_schema

__all__ = ["query_info_schema", "analyze_query_performance"]
