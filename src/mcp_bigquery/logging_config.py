"""Logging configuration for MCP BigQuery server."""

import json
import logging
import sys
from datetime import datetime
from typing import Any, TextIO


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        return super().format(record)


class ContextLogger:
    """Logger wrapper with context support."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.context: dict[str, Any] = {}

    def set_context(self, **kwargs: Any) -> None:
        """Set context fields for all subsequent log messages."""
        self.context.update(kwargs)

    def clear_context(self) -> None:
        """Clear all context fields."""
        self.context.clear()

    def _log(self, level: int, msg: str, *args: Any, **kwargs: Any) -> None:
        """Internal logging method with context."""
        extra = kwargs.get("extra", {})
        extra["extra_fields"] = {**self.context, **extra.get("extra_fields", {})}
        kwargs["extra"] = extra
        self.logger.log(level, msg, *args, **kwargs)

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log debug message with context."""
        self._log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log info message with context."""
        self._log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log warning message with context."""
        self._log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log error message with context."""
        self._log(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log critical message with context."""
        self._log(logging.CRITICAL, msg, *args, **kwargs)

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log exception with context."""
        kwargs["exc_info"] = True
        self.error(msg, *args, **kwargs)


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
    colored: bool = True,
    log_file: str | None = None,
    stream: TextIO | None = None,
) -> None:
    """
    Setup logging configuration for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_json: Whether to use JSON formatting
        colored: Whether to use colored output (only for console)
        log_file: Optional log file path
        stream: Optional stream to write logs to (defaults to stderr)
    """
    target_stream = stream or sys.stderr

    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    log_level = getattr(logging, level.upper(), logging.WARNING)
    root_logger.setLevel(log_level)

    console_handler = logging.StreamHandler(target_stream)
    console_handler.setLevel(log_level)

    if format_json:
        console_formatter = JSONFormatter()
    elif colored and target_stream.isatty():
        console_formatter = ColoredFormatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        console_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)

        if format_json:
            file_formatter = JSONFormatter()
        else:
            file_formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(name)s - %(funcName)s:%(lineno)d - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> ContextLogger:
    """
    Get a logger instance with context support.

    Args:
        name: Logger name (usually __name__)

    Returns:
        ContextLogger instance
    """
    return ContextLogger(logging.getLogger(name))


# Performance logging utilities
def log_performance(logger: ContextLogger, operation: str) -> Any:
    """
    Decorator to log performance metrics for a function.

    Args:
        logger: Logger instance
        operation: Name of the operation being performed
    """
    import functools
    import time

    def decorator(func: Any) -> Any:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    f"{operation} completed",
                    extra={
                        "extra_fields": {
                            "operation": operation,
                            "duration_seconds": duration,
                            "status": "success",
                        }
                    },
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"{operation} failed",
                    extra={
                        "extra_fields": {
                            "operation": operation,
                            "duration_seconds": duration,
                            "status": "error",
                            "error_type": type(e).__name__,
                        }
                    },
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    f"{operation} completed",
                    extra={
                        "extra_fields": {
                            "operation": operation,
                            "duration_seconds": duration,
                            "status": "success",
                        }
                    },
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"{operation} failed",
                    extra={
                        "extra_fields": {
                            "operation": operation,
                            "duration_seconds": duration,
                            "status": "error",
                            "error_type": type(e).__name__,
                        }
                    },
                )
                raise

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
