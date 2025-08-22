"""
Improved BigQuery client management with connection pooling and better error handling.

This module provides enhanced BigQuery client management with:
- Connection pooling for better performance
- Comprehensive error handling
- Configuration-based initialization
- Logging and monitoring
"""

from typing import Optional

from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError

from .cache import get_client_cache
from .config import get_config
from .exceptions import AuthenticationError, ConfigurationError
from .logging_config import get_logger, log_performance
from .utils import handle_bigquery_exceptions

logger = get_logger(__name__)


@handle_bigquery_exceptions
@log_performance(logger, "get_bigquery_client")
def get_bigquery_client(
    project_id: Optional[str] = None, location: Optional[str] = None, use_cache: bool = True
) -> bigquery.Client:
    """
    Get or create a BigQuery client with improved configuration and caching.

    This function creates a BigQuery client using Application Default Credentials (ADC)
    with support for connection pooling and configuration management.

    Args:
        project_id: GCP project ID. If None, uses config or ADC default.
        location: BigQuery dataset location (e.g., 'US', 'EU', 'asia-northeast1').
                 If None, uses config default.
        use_cache: Whether to use cached client instances for better performance.

    Returns:
        Configured BigQuery client instance.

    Raises:
        AuthenticationError: If credentials cannot be obtained or are invalid.
        ConfigurationError: If project ID cannot be determined.

    Examples:
        >>> # Get client with default configuration
        >>> client = get_bigquery_client()

        >>> # Get client for specific project and location
        >>> client = get_bigquery_client(
        ...     project_id="my-project",
        ...     location="US"
        ... )

        >>> # Get fresh client without caching
        >>> client = get_bigquery_client(use_cache=False)

    Notes:
        - Clients are cached by (project_id, location) pair for performance
        - Set use_cache=False to force creation of a new client
        - Authentication uses Application Default Credentials (ADC)
        - Run 'gcloud auth application-default login' to set up ADC
    """
    config = get_config()

    # Use provided values or fall back to config
    project_id = project_id or config.project_id
    location = location or config.location

    # Log configuration being used
    logger.info(
        "Getting BigQuery client",
        extra={
            "extra_fields": {"project_id": project_id, "location": location, "use_cache": use_cache}
        },
    )

    # Use cached client if enabled
    if use_cache and config.cache_enabled:
        client_cache = get_client_cache()
        return client_cache.get_client(project_id, location)

    # Create new client
    try:
        client = bigquery.Client(project=project_id, location=location)

        # Validate client can connect
        try:
            # Quick validation query
            client.query("SELECT 1", job_config=bigquery.QueryJobConfig(dry_run=True))
            logger.info(
                f"Successfully created BigQuery client for project: {project_id or 'default'}"
            )
        except GoogleCloudError as e:
            if "403" in str(e) or "401" in str(e):
                raise AuthenticationError(
                    "Failed to authenticate with BigQuery. "
                    "Please run: gcloud auth application-default login"
                )
            raise

        return client

    except Exception as e:
        if "could not automatically determine credentials" in str(e).lower():
            raise AuthenticationError(
                "Application Default Credentials not found. "
                "Please run: gcloud auth application-default login\n"
                "Or set GOOGLE_APPLICATION_CREDENTIALS environment variable "
                "to point to a service account key file."
            )
        elif "project" in str(e).lower() and "not set" in str(e).lower():
            raise ConfigurationError(
                "Project ID not specified and could not be determined from environment. "
                "Please set BQ_PROJECT environment variable or pass project_id parameter."
            )
        else:
            logger.exception("Failed to create BigQuery client")
            raise


def get_bigquery_client_with_retry(
    project_id: Optional[str] = None,
    location: Optional[str] = None,
    max_retries: int = 3,
    retry_delay: float = 1.0,
) -> bigquery.Client:
    """
    Get BigQuery client with retry logic for transient failures.

    Args:
        project_id: GCP project ID
        location: BigQuery dataset location
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds

    Returns:
        Configured BigQuery client instance

    Raises:
        AuthenticationError: If all retry attempts fail
    """
    import time

    last_error = None

    for attempt in range(max_retries):
        try:
            return get_bigquery_client(project_id, location)
        except AuthenticationError:
            # Don't retry authentication errors
            raise
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                logger.warning(
                    f"Failed to create BigQuery client (attempt {attempt + 1}/{max_retries}), retrying...",
                    extra={"extra_fields": {"error": str(e)}},
                )
                time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
            else:
                logger.error(
                    f"Failed to create BigQuery client after {max_retries} attempts",
                    extra={"extra_fields": {"error": str(e)}},
                )

    if last_error:
        raise last_error
    else:
        raise AuthenticationError("Failed to create BigQuery client")
