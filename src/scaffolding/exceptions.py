"""
Shared exception types for SimBuilder components.
"""


class SimBuilderError(Exception):
    """Base exception for all SimBuilder-related errors."""

    def __init__(self, message: str, details: str | None = None):
        self.message = message
        self.details = details
        super().__init__(message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class ConfigurationError(SimBuilderError):
    """Raised when configuration is invalid or missing."""
    pass


class DependencyError(SimBuilderError):
    """Raised when a required dependency is unavailable or misconfigured."""
    pass


class ServiceUnavailableError(SimBuilderError):
    """Raised when a required service (Neo4j, NATS, etc.) is unavailable."""
    pass


class AuthenticationError(SimBuilderError):
    """Raised when authentication fails."""
    pass
