"""Simple BigQuery client cache."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any

from .logging_config import get_logger

logger = get_logger(__name__)


class BigQueryClientCache:
    """Cache for BigQuery client instances."""

    def __init__(self) -> None:
        self._clients: dict[str, Any] = {}

    def get_client(
        self,
        project_id: str | None = None,
        location: str | None = None,
        builder: Callable[[str | None, str | None], Any] | None = None,
    ) -> Any:
        if builder is None:
            module = importlib.import_module("mcp_bigquery.clients.factory")
            builder = module._instantiate_client  # type: ignore[attr-defined]

        key = f"{project_id or 'default'}:{location or 'default'}"
        if key not in self._clients:
            logger.info("Creating new BigQuery client for %s", key)
            self._clients[key] = builder(project_id, location)
        else:
            logger.debug("Reusing BigQuery client for %s", key)

        return self._clients[key]


_client_cache: BigQueryClientCache | None = None


def get_client_cache() -> BigQueryClientCache:
    """Get the global BigQuery client cache instance."""
    global _client_cache
    if _client_cache is None:
        _client_cache = BigQueryClientCache()
    return _client_cache
