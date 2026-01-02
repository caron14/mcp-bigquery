"""Client factory helpers for BigQuery."""

from __future__ import annotations

from google.cloud import bigquery

from .factory import get_bigquery_client as _get_bigquery_client
from .factory import get_bigquery_client_with_retry as _get_bigquery_client_with_retry

__all__ = ["get_bigquery_client", "get_bigquery_client_with_retry"]


def get_bigquery_client(
    project_id: str | None = None,
    location: str | None = None,
    use_cache: bool = True,
) -> bigquery.Client:
    """Compatibility wrapper for the shared BigQuery client factory."""
    return _get_bigquery_client(project_id=project_id, location=location, use_cache=use_cache)


def get_bigquery_client_with_retry(
    project_id: str | None = None,
    location: str | None = None,
    *,
    max_retries: int = 3,
    retry_delay: float = 1.0,
) -> bigquery.Client:
    """Compatibility wrapper for retry-enabled client creation."""
    return _get_bigquery_client_with_retry(
        project_id=project_id,
        location=location,
        max_retries=max_retries,
        retry_delay=retry_delay,
    )
