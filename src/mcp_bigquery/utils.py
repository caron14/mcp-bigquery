"""Utility functions and decorators for MCP BigQuery server."""

import functools
import re
import time
from collections.abc import Callable
from typing import Any, TypeVar

from google.api_core.exceptions import GoogleAPIError
from google.cloud.exceptions import BadRequest

from .constants import REGEX_PATTERNS
from .exceptions import MCPBigQueryError, SQLValidationError, handle_bigquery_error
from .logging_config import get_logger
from .types import ErrorInfo, ErrorLocation

logger = get_logger(__name__)

T = TypeVar("T")


def extract_error_location(error_message: str) -> ErrorLocation | None:
    """
    Extract error location from BigQuery error message.

    Args:
        error_message: Error message from BigQuery

    Returns:
        ErrorLocation dict with line and column, or None
    """
    match = re.search(REGEX_PATTERNS["error_location"], error_message)
    if match:
        return ErrorLocation(line=int(match.group(1)), column=int(match.group(2)))
    return None


def format_error_response(error: Exception | MCPBigQueryError) -> ErrorInfo:
    """
    Format an error into a standard error response.

    Args:
        error: The error to format

    Returns:
        ErrorInfo dict with error details
    """
    if isinstance(error, MCPBigQueryError):
        return error.to_dict()
    elif isinstance(error, GoogleAPIError):
        bq_error = handle_bigquery_error(error)
        return bq_error.to_dict()
    else:
        return ErrorInfo(code="UNKNOWN_ERROR", message=str(error), location=None, details=None)


def handle_bigquery_exceptions(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to handle BigQuery exceptions and convert them to MCP errors.

    Args:
        func: Function to decorate

    Returns:
        Decorated function
    """

    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except BadRequest as e:
            error_msg = str(e)
            location = extract_error_location(error_msg)
            raise SQLValidationError(error_msg, location=location) from e
        except GoogleAPIError as e:
            raise handle_bigquery_error(e) from e
        except MCPBigQueryError:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in {func.__name__}")
            raise MCPBigQueryError(str(e)) from e

    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except BadRequest as e:
            error_msg = str(e)
            location = extract_error_location(error_msg)
            raise SQLValidationError(error_msg, location=location) from e
        except GoogleAPIError as e:
            raise handle_bigquery_error(e) from e
        except MCPBigQueryError:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in {func.__name__}")
            raise MCPBigQueryError(str(e)) from e

    # Return appropriate wrapper based on function type
    import asyncio

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def validate_sql_length(sql: str, max_length: int | None = None) -> None:
    """
    Validate SQL query length.

    Args:
        sql: SQL query string
        max_length: Maximum allowed length (uses config default if None)

    Raises:
        InvalidParameterError: If SQL is too long
    """
    from .config import get_config
    from .exceptions import InvalidParameterError

    if max_length is None:
        max_length = get_config().max_query_length

    if len(sql) > max_length:
        raise InvalidParameterError(
            "sql",
            f"Query is too long ({len(sql)} characters, maximum {max_length})",
            expected_type="string",
        )


def validate_parameters(params: dict[str, Any] | None, max_count: int | None = None) -> None:
    """
    Validate query parameters.

    Args:
        params: Query parameters dictionary
        max_count: Maximum allowed parameter count (uses config default if None)

    Raises:
        InvalidParameterError: If parameters are invalid
    """
    if params is None:
        return

    from .config import get_config
    from .exceptions import InvalidParameterError

    if max_count is None:
        max_count = get_config().max_parameter_count

    if not isinstance(params, dict):
        raise InvalidParameterError(
            "params", "Parameters must be a dictionary", expected_type="dict"
        )

    if len(params) > max_count:
        raise InvalidParameterError(
            "params", f"Too many parameters ({len(params)}, maximum {max_count})"
        )

    # Validate parameter names (alphanumeric and underscore only)
    for param_name in params:
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", param_name):
            raise InvalidParameterError(
                param_name,
                f"Invalid parameter name: {param_name}. Must start with letter or underscore and contain only alphanumeric characters and underscores.",
            )


def sanitize_table_reference(table_ref: str) -> str:
    """
    Sanitize a table reference string.

    Args:
        table_ref: Table reference string

    Returns:
        Sanitized table reference
    """
    # Remove backticks if present
    table_ref = re.sub(REGEX_PATTERNS["backtick_identifier"], lambda m: m.group(0)[1:-1], table_ref)

    # Validate each component
    parts = table_ref.split(".")
    sanitized_parts = []

    for part in parts:
        # Allow alphanumeric, underscore, and hyphen
        if re.match(r"^[a-zA-Z0-9_-]+$", part):
            sanitized_parts.append(part)
        else:
            # If contains special characters, wrap in backticks
            sanitized_parts.append(f"`{part}`")

    return ".".join(sanitized_parts)


def format_bytes(bytes_value: int) -> str:
    """
    Format bytes into human-readable string.

    Args:
        bytes_value: Number of bytes

    Returns:
        Formatted string (e.g., "1.5 GB", "750 MB")
    """
    from .constants import BYTES_PER_GIB, BYTES_PER_TIB

    if bytes_value >= BYTES_PER_TIB:
        return f"{bytes_value / BYTES_PER_TIB:.2f} TiB"
    elif bytes_value >= BYTES_PER_GIB:
        return f"{bytes_value / BYTES_PER_GIB:.2f} GiB"
    elif bytes_value >= 1024 * 1024:
        return f"{bytes_value / (1024 * 1024):.2f} MiB"
    elif bytes_value >= 1024:
        return f"{bytes_value / 1024:.2f} KiB"
    else:
        return f"{bytes_value} bytes"


def calculate_cost_estimate(bytes_processed: int, price_per_tib: float | None = None) -> float:
    """
    Calculate cost estimate for BigQuery query.

    Args:
        bytes_processed: Number of bytes that will be processed
        price_per_tib: Price per TiB (uses config default if None)

    Returns:
        Estimated cost in USD
    """
    from .config import get_config
    from .constants import BYTES_PER_TIB, MIN_BILLING_BYTES

    if price_per_tib is None:
        price_per_tib = get_config().price_per_tib

    # Apply minimum billing threshold
    billable_bytes = max(bytes_processed, MIN_BILLING_BYTES)

    # Calculate cost
    tib_processed = billable_bytes / BYTES_PER_TIB
    return tib_processed * price_per_tib


def rate_limit(calls_per_minute: int | None = None) -> Callable:
    """
    Decorator to implement rate limiting.

    Args:
        calls_per_minute: Maximum calls per minute (uses config default if None)

    Returns:
        Decorated function
    """
    from collections import deque

    from .config import get_config
    from .exceptions import RateLimitError

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        call_times = deque()

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal call_times

            config = get_config()
            if not config.rate_limit_enabled:
                return await func(*args, **kwargs)

            max_calls = calls_per_minute or config.requests_per_minute
            current_time = time.time()

            # Remove calls older than 1 minute
            while call_times and call_times[0] < current_time - 60:
                call_times.popleft()

            # Check rate limit
            if len(call_times) >= max_calls:
                wait_time = 60 - (current_time - call_times[0])
                raise RateLimitError(retry_after=int(wait_time))

            # Record this call
            call_times.append(current_time)

            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal call_times

            config = get_config()
            if not config.rate_limit_enabled:
                return func(*args, **kwargs)

            max_calls = calls_per_minute or config.requests_per_minute
            current_time = time.time()

            # Remove calls older than 1 minute
            while call_times and call_times[0] < current_time - 60:
                call_times.popleft()

            # Check rate limit
            if len(call_times) >= max_calls:
                wait_time = 60 - (current_time - call_times[0])
                raise RateLimitError(retry_after=int(wait_time))

            # Record this call
            call_times.append(current_time)

            return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def memoize(ttl: int | None = None) -> Callable:
    """
    Decorator to cache function results.

    Args:
        ttl: Time-to-live in seconds (uses config default if None)

    Returns:
        Decorated function
    """
    from .config import get_config

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache: dict[tuple, tuple[float, Any]] = {}

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            config = get_config()
            if not config.cache_enabled:
                return await func(*args, **kwargs)

            cache_ttl = ttl or config.cache_ttl
            cache_key = (args, tuple(sorted(kwargs.items())))
            current_time = time.time()

            # Check cache
            if cache_key in cache:
                cached_time, cached_result = cache[cache_key]
                if current_time - cached_time < cache_ttl:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache[cache_key] = (current_time, result)

            # Clean old entries
            for key in list(cache.keys()):
                if current_time - cache[key][0] > cache_ttl:
                    del cache[key]

            return result

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            config = get_config()
            if not config.cache_enabled:
                return func(*args, **kwargs)

            cache_ttl = ttl or config.cache_ttl
            cache_key = (args, tuple(sorted(kwargs.items())))
            current_time = time.time()

            # Check cache
            if cache_key in cache:
                cached_time, cached_result = cache[cache_key]
                if current_time - cached_time < cache_ttl:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache[cache_key] = (current_time, result)

            # Clean old entries
            for key in list(cache.keys()):
                if current_time - cache[key][0] > cache_ttl:
                    del cache[key]

            return result

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix
