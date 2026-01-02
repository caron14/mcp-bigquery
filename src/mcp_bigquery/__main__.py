"""Main entry point for the MCP BigQuery server."""

import argparse
import asyncio
import sys

from . import __version__
from .config import get_config
from .logging_config import resolve_log_level, setup_logging
from .server import main as server_main


def main():
    """Console script entry point."""
    parser = argparse.ArgumentParser(
        description="MCP BigQuery Server - Validate and analyze BigQuery SQL"
    )
    parser.add_argument("--version", action="version", version=f"mcp-bigquery {__version__}")
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase logging verbosity (use -vv for DEBUG)",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="count",
        default=0,
        help="Reduce logging verbosity (use -qq for CRITICAL)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Explicit log level override",
    )
    parser.add_argument(
        "--json-logs",
        action="store_true",
        help="Emit logs as JSON (useful for structured log ingestion)",
    )

    args = parser.parse_args()

    config = get_config()
    level = resolve_log_level(
        default_level=config.log_level,
        explicit_level=args.log_level,
        verbose=args.verbose,
        quiet=args.quiet,
    )

    setup_logging(level=level, format_json=args.json_logs)

    # Run the server
    try:
        asyncio.run(server_main())
    except KeyboardInterrupt:
        print("\nServer stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
