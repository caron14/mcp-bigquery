"""Thread-safe BigQuery client cache."""

from __future__ import annotations

import importlib
import threading
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from google.cloud import bigquery

from .logging_config import get_logger

logger = get_logger(__name__)


class BigQueryClientCache:
    """Thread-safe cache for BigQuery client instances."""

    def __init__(self) -> None:
        self._clients: dict[str, bigquery.Client] = {}
        self._lock = threading.Lock()

    def get_client(
        self,
        project_id: str | None = None,
        location: str | None = None,
        builder: Callable[[str | None, str | None], bigquery.Client] | None = None,
    ) -> bigquery.Client:
        """Get or create cached BigQuery client in a thread-safe manner."""
        if builder is None:
            module = importlib.import_module("mcp_bigquery.clients.factory")
            builder = module._instantiate_client
            assert builder is not None

        key = f"{project_id or 'default'}:{location or 'default'}"

        with self._lock:
            if key not in self._clients:
                logger.info("Creating new BigQuery client for %s", key)
                self._clients[key] = builder(project_id, location)
            else:
                logger.debug("Reusing BigQuery client for %s", key)

            return self._clients[key]

    def clear(self) -> None:
        """Clear all cached clients in a thread-safe manner."""
        with self._lock:
            self._clients.clear()


_client_cache: BigQueryClientCache | None = None
_cache_lock = threading.Lock()


def get_client_cache() -> BigQueryClientCache:
    """Get the global thread-safe BigQuery client cache instance."""
    global _client_cache
    if _client_cache is None:
        with _cache_lock:
            if _client_cache is None:
                _client_cache = BigQueryClientCache()
    return _client_cache
