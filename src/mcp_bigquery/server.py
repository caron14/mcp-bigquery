"""MCP server for BigQuery dry-run operations."""

import asyncio
import json
import os
import re
from typing import Any

import mcp.server.stdio
import mcp.types as types
from google.cloud import bigquery
from google.cloud.exceptions import BadRequest
from mcp.server import NotificationOptions, Server

from . import __version__
from .bigquery_client import get_bigquery_client
from .sql_analyzer import SQLAnalyzer

server = Server("mcp-bigquery")


def extract_error_location(error_message: str) -> dict[str, int] | None:
    """
    Extract line and column from BigQuery error message.

    Looks for patterns like [3:15] in the error message.

    Args:
        error_message: The error message from BigQuery

    Returns:
        Dict with 'line' and 'column' if found, None otherwise
    """
    match = re.search(r"\[(\d+):(\d+)\]", error_message)
    if match:
        return {"line": int(match.group(1)), "column": int(match.group(2))}
    return None


def build_query_parameters(params: dict[str, Any] | None) -> list[bigquery.ScalarQueryParameter]:
    """
    Build BigQuery query parameters from a dictionary.

    Initial implementation treats all values as STRING type.

    Args:
        params: Dictionary of parameter names to values

    Returns:
        List of ScalarQueryParameter objects
    """
    if not params:
        return []

    return [
        bigquery.ScalarQueryParameter(name, "STRING", str(value)) for name, value in params.items()
    ]


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available MCP tools."""
    return [
        types.Tool(
            name="bq_validate_sql",
            description=("Validate BigQuery SQL syntax without executing the query"),
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "The SQL query to validate",
                    },
                    "params": {
                        "type": "object",
                        "description": ("Optional query parameters (key-value pairs)"),
                        "additionalProperties": True,
                    },
                },
                "required": ["sql"],
            },
        ),
        types.Tool(
            name="bq_dry_run_sql",
            description=(
                "Perform a dry-run of a BigQuery SQL query to get cost " "estimates and metadata"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "The SQL query to dry-run",
                    },
                    "params": {
                        "type": "object",
                        "description": ("Optional query parameters (key-value pairs)"),
                        "additionalProperties": True,
                    },
                    "pricePerTiB": {
                        "type": "number",
                        "description": (
                            "Price per TiB for cost estimation " "(defaults to env var or 5.0)"
                        ),
                    },
                },
                "required": ["sql"],
            },
        ),
        types.Tool(
            name="bq_analyze_query_structure",
            description=("Analyze BigQuery SQL query structure and complexity"),
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "The SQL query to analyze",
                    },
                    "params": {
                        "type": "object",
                        "description": ("Optional query parameters (key-value pairs)"),
                        "additionalProperties": True,
                    },
                },
                "required": ["sql"],
            },
        ),
        types.Tool(
            name="bq_extract_dependencies",
            description=("Extract table and column dependencies from BigQuery SQL"),
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "The SQL query to analyze",
                    },
                    "params": {
                        "type": "object",
                        "description": ("Optional query parameters (key-value pairs)"),
                        "additionalProperties": True,
                    },
                },
                "required": ["sql"],
            },
        ),
        types.Tool(
            name="bq_validate_query_syntax",
            description=("Enhanced syntax validation with detailed error reporting"),
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "The SQL query to validate",
                    },
                    "params": {
                        "type": "object",
                        "description": ("Optional query parameters (key-value pairs)"),
                        "additionalProperties": True,
                    },
                },
                "required": ["sql"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""

    if name == "bq_validate_sql":
        result = await validate_sql(sql=arguments["sql"], params=arguments.get("params"))
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "bq_dry_run_sql":
        result = await dry_run_sql(
            sql=arguments["sql"],
            params=arguments.get("params"),
            price_per_tib=arguments.get("pricePerTiB"),
        )
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "bq_analyze_query_structure":
        result = await analyze_query_structure(sql=arguments["sql"], params=arguments.get("params"))
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "bq_extract_dependencies":
        result = await extract_dependencies(sql=arguments["sql"], params=arguments.get("params"))
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "bq_validate_query_syntax":
        result = await validate_query_syntax(sql=arguments["sql"], params=arguments.get("params"))
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def validate_sql(sql: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Validate BigQuery SQL syntax using dry-run.

    Args:
        sql: The SQL query to validate
        params: Optional query parameters

    Returns:
        Dict with 'isValid' boolean and optional 'error' details
    """
    try:
        client = get_bigquery_client()

        job_config = bigquery.QueryJobConfig(
            dry_run=True,
            use_query_cache=False,
            query_parameters=build_query_parameters(params),
        )

        client.query(sql, job_config=job_config)

        return {"isValid": True}

    except BadRequest as e:
        error_msg = str(e)
        error_result = {
            "isValid": False,
            "error": {"code": "INVALID_SQL", "message": error_msg},
        }

        location = extract_error_location(error_msg)
        if location:
            error_result["error"]["location"] = location

        if hasattr(e, "errors") and e.errors:
            error_result["error"]["details"] = e.errors

        return error_result

    except Exception as e:
        return {
            "isValid": False,
            "error": {"code": "UNKNOWN_ERROR", "message": str(e)},
        }


async def dry_run_sql(
    sql: str,
    params: dict[str, Any] | None = None,
    price_per_tib: float | None = None,
) -> dict[str, Any]:
    """
    Perform a dry-run of a BigQuery SQL query.

    Args:
        sql: The SQL query to dry-run
        params: Optional query parameters
        price_per_tib: Price per TiB for cost estimation

    Returns:
        Dict with totalBytesProcessed, usdEstimate, referencedTables,
        and schemaPreview
        or error details if the query is invalid
    """
    try:
        client = get_bigquery_client()

        job_config = bigquery.QueryJobConfig(
            dry_run=True,
            use_query_cache=False,
            query_parameters=build_query_parameters(params),
        )

        query_job = client.query(sql, job_config=job_config)

        # Get price per TiB (precedence: arg > env > default)
        if price_per_tib is None:
            price_per_tib = float(os.environ.get("SAFE_PRICE_PER_TIB", "5.0"))

        # Calculate cost estimate
        bytes_processed = query_job.total_bytes_processed or 0
        tib_processed = bytes_processed / (2**40)
        usd_estimate = round(tib_processed * price_per_tib, 6)

        # Extract referenced tables
        referenced_tables = []
        if query_job.referenced_tables:
            for table_ref in query_job.referenced_tables:
                referenced_tables.append(
                    {
                        "project": table_ref.project,
                        "dataset": table_ref.dataset_id,
                        "table": table_ref.table_id,
                    }
                )

        # Extract schema preview
        schema_preview = []
        if query_job.schema:
            for field in query_job.schema:
                schema_preview.append(
                    {
                        "name": field.name,
                        "type": field.field_type,
                        "mode": field.mode,
                    }
                )

        return {
            "totalBytesProcessed": bytes_processed,
            "usdEstimate": usd_estimate,
            "referencedTables": referenced_tables,
            "schemaPreview": schema_preview,
        }

    except BadRequest as e:
        error_msg = str(e)
        error_result = {"error": {"code": "INVALID_SQL", "message": error_msg}}

        if hasattr(e, "errors") and e.errors:
            error_result["error"]["details"] = e.errors

        return error_result

    except Exception as e:
        return {"error": {"code": "UNKNOWN_ERROR", "message": str(e)}}


async def analyze_query_structure(sql: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Analyze BigQuery SQL query structure and complexity.

    Args:
        sql: The SQL query to analyze
        params: Optional query parameters (not used in static analysis)

    Returns:
        Dict with structure analysis including query type, complexity score,
        and feature detection
    """
    try:
        analyzer = SQLAnalyzer(sql)
        result = analyzer.analyze_structure()
        return result

    except Exception as e:
        return {
            "error": {
                "code": "ANALYSIS_ERROR",
                "message": f"Failed to analyze query structure: {str(e)}",
            }
        }


async def extract_dependencies(sql: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Extract table and column dependencies from BigQuery SQL.

    Args:
        sql: The SQL query to analyze
        params: Optional query parameters (not used in static analysis)

    Returns:
        Dict with tables, columns, and dependency graph information
    """
    try:
        analyzer = SQLAnalyzer(sql)
        result = analyzer.extract_dependencies()
        return result

    except Exception as e:
        return {
            "error": {
                "code": "ANALYSIS_ERROR",
                "message": f"Failed to extract dependencies: {str(e)}",
            }
        }


async def validate_query_syntax(sql: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Enhanced syntax validation with detailed error reporting.

    Args:
        sql: The SQL query to validate
        params: Optional query parameters (not used in static analysis)

    Returns:
        Dict with validation results, issues, and suggestions
    """
    try:
        analyzer = SQLAnalyzer(sql)
        result = analyzer.validate_syntax_enhanced()
        return result

    except Exception as e:
        return {
            "error": {
                "code": "ANALYSIS_ERROR",
                "message": f"Failed to validate query syntax: {str(e)}",
            }
        }


async def main():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            mcp.server.InitializationOptions(
                server_name="mcp-bigquery",
                server_version=__version__,
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
