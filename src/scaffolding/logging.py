"""
Structured logging setup for SimBuilder using structlog.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.typing import FilteringBoundLogger

from .config import get_settings


def setup_logging() -> FilteringBoundLogger:
    """
    Configure structured logging with JSON output.
    
    Returns:
        Configured structlog logger instance
    """
    settings = get_settings()

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
    )

    # Configure structlog
    structlog.configure(
        processors=[
            # Add timestamp
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            # Add context processors
            structlog.contextvars.merge_contextvars,
            structlog.processors.StackInfoRenderer(),
            # JSON formatting for production, pretty printing for development
            structlog.dev.ConsoleRenderer() if settings.is_development
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level)
        ),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger("simbuilder")


def get_logger(name: str = "simbuilder") -> FilteringBoundLogger:
    """
    Get a named logger instance.
    
    Args:
        name: Logger name, defaults to "simbuilder"
        
    Returns:
        Configured structlog logger instance
    """
    return structlog.get_logger(name)


def log_function_call(
    logger: FilteringBoundLogger,
    function_name: str,
    **kwargs: Any
) -> None:
    """
    Log a function call with parameters.
    
    Args:
        logger: Logger instance
        function_name: Name of the function being called
        **kwargs: Function parameters to log
    """
    logger.debug(
        "Function called",
        function=function_name,
        parameters=kwargs
    )


def log_error_with_context(
    logger: FilteringBoundLogger,
    error: Exception,
    context: dict[str, Any] | None = None
) -> None:
    """
    Log an error with additional context.
    
    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Additional context information
    """
    log_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
    }

    if context:
        log_data.update(context)

    logger.error("Error occurred", **log_data)


class LoggingMixin:
    """Mixin to add structured logging to classes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_logger(self.__class__.__name__)

    def log_method_call(self, method_name: str, **kwargs: Any) -> None:
        """Log a method call with parameters."""
        log_function_call(self.logger, f"{self.__class__.__name__}.{method_name}", **kwargs)

    def log_error(self, error: Exception, context: dict[str, Any] | None = None) -> None:
        """Log an error with context."""
        error_context = {"class": self.__class__.__name__}
        if context:
            error_context.update(context)
        log_error_with_context(self.logger, error, error_context)
