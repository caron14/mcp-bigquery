"""Factories and utilities for constructing configured BigQuery clients."""

from __future__ import annotations

import time
from collections.abc import Callable

from google.auth.exceptions import DefaultCredentialsError
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError

from ..config import get_config
from ..exceptions import (
    AuthenticationError,
    ConfigurationError,
    MCPBigQueryError,
    handle_bigquery_error,
)
from ..logging_config import get_logger, log_performance

logger = get_logger(__name__)


def _resolve_target(project_id: str | None, location: str | None) -> tuple[str | None, str | None]:
    """Resolve project and location values using configuration defaults when needed."""
    config = get_config()
    resolved_project = project_id or config.project_id
    resolved_location = location or config.location
    return resolved_project, resolved_location


@log_performance(logger, "create_bigquery_client")
def _instantiate_client(project_id: str | None, location: str | None) -> bigquery.Client:
    """Instantiate a BigQuery client with optional dry-run validation."""
    resolved_project, resolved_location = _resolve_target(project_id, location)

    try:
        client = bigquery.Client(project=resolved_project, location=resolved_location)
    except DefaultCredentialsError as exc:
        raise AuthenticationError(
            "Application Default Credentials not found. "
            "Run 'gcloud auth application-default login' or set GOOGLE_APPLICATION_CREDENTIALS."
        ) from exc
    except GoogleCloudError as exc:
        raise handle_bigquery_error(exc) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Unexpected error while creating BigQuery client")
        raise MCPBigQueryError(str(exc)) from exc

    # Ensure we have a resolved project after client creation
    if not client.project and not resolved_project:
        raise ConfigurationError(
            "Unable to determine the target project. "
            "Set BQ_PROJECT or provide project_id explicitly."
        )

    # Perform a lightweight dry-run to surface credential issues early.
    try:
        client.query("SELECT 1", job_config=bigquery.QueryJobConfig(dry_run=True))
    except GoogleCloudError as exc:
        raise handle_bigquery_error(exc) from exc

    return client


def get_bigquery_client(
    project_id: str | None = None,
    location: str | None = None,
    use_cache: bool = True,
    *,
    builder: Callable[[str | None, str | None], bigquery.Client] = _instantiate_client,
) -> bigquery.Client:
    """
    Get a configured BigQuery client with optional caching support.

    Args:
        project_id: Target GCP project (falls back to configuration/ADC default).
        location: BigQuery location to target for requests.
        use_cache: When True, reuse clients keyed by (project, location).
        builder: Client factory callable (primarily for testing).
    """
    resolved_project, resolved_location = _resolve_target(project_id, location)

    if not use_cache:
        return builder(resolved_project, resolved_location)

    from ..cache import get_client_cache  # Local import to avoid cycle

    client_cache = get_client_cache()
    return client_cache.get_client(
        project_id=resolved_project,
        location=resolved_location,
        builder=builder,
    )


def get_bigquery_client_with_retry(
    project_id: str | None = None,
    location: str | None = None,
    *,
    max_retries: int = 3,
    retry_delay: float = 1.0,
) -> bigquery.Client:
    """
    Retrieve a BigQuery client with retry/backoff for transient failures.

    Authentication failures raise immediately because retrying will not help.
    """
    last_error: MCPBigQueryError | None = None

    for attempt in range(1, max_retries + 1):
        try:
            return get_bigquery_client(
                project_id=project_id,
                location=location,
                use_cache=False,
            )
        except AuthenticationError:
            # Authentication issues require user action; escalating quickly helps UX.
            raise
        except MCPBigQueryError as exc:
            last_error = exc
            if attempt == max_retries:
                break

            logger.warning(
                "Failed to create BigQuery client (attempt %s/%s): %s",
                attempt,
                max_retries,
                exc,
            )
            time.sleep(retry_delay * attempt)

    if last_error:
        raise last_error

    raise AuthenticationError("Failed to create BigQuery client")
