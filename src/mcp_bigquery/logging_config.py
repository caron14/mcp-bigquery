"""Logging helpers for MCP BigQuery server."""

import json
import logging
import sys
from datetime import datetime
from typing import Any, TextIO


class JSONFormatter(logging.Formatter):
    """Minimal JSON formatter for structured logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def resolve_log_level(
    *,
    default_level: str = "WARNING",
    explicit_level: str | None = None,
    verbose: int = 0,
    quiet: int = 0,
) -> str:
    """Determine the effective log level from CLI flags."""
    if explicit_level:
        return explicit_level.upper()
    if verbose >= 2:
        return "DEBUG"
    if verbose == 1:
        return "INFO"
    if quiet >= 2:
        return "CRITICAL"
    if quiet == 1:
        return "ERROR"
    return default_level.upper()


def setup_logging(
    level: str = "WARNING",
    format_json: bool = False,
    log_file: str | None = None,
    stream: TextIO | None = None,
) -> None:
    """Configure root logging."""
    target_stream = stream or sys.stderr

    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    log_level = getattr(logging, level.upper(), logging.WARNING)
    root_logger.setLevel(log_level)

    console_handler = logging.StreamHandler(target_stream)
    console_handler.setLevel(log_level)

    formatter: logging.Formatter
    if format_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Return a standard logger instance."""
    return logging.getLogger(name)


def log_performance(logger: logging.Logger, operation: str) -> Any:
    """Decorator to log performance metrics for a function."""
    import asyncio
    import functools
    import time

    def decorator(func: Any) -> Any:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                logger.info("%s completed in %.3fs", operation, time.time() - start_time)
                return result
            except Exception:
                logger.error("%s failed in %.3fs", operation, time.time() - start_time)
                raise

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                logger.info("%s completed in %.3fs", operation, time.time() - start_time)
                return result
            except Exception:
                logger.error("%s failed in %.3fs", operation, time.time() - start_time)
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
