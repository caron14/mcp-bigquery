"""Main entry point for the MCP BigQuery server."""

import argparse
import asyncio
import sys

from . import __version__
from .server import main as server_main


def main():
    """Console script entry point."""
    parser = argparse.ArgumentParser(
        description="MCP BigQuery Server - Validate and analyze BigQuery SQL"
    )
    parser.add_argument("--version", action="version", version=f"mcp-bigquery {__version__}")

    # Parse arguments (unused but kept for future extensibility)
    parser.parse_args()

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
