"""
Custom exceptions for the SimBuilder LLM integration package.
"""


class LLMError(Exception):
    """Base exception for LLM-related errors."""

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        """Initialize LLM error.

        Args:
            message: Human-readable error message
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.original_error = original_error

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.original_error:
            return f"{self.message} (Original: {self.original_error})"
        return self.message


class PromptRenderError(Exception):
    """Exception raised when prompt rendering fails."""

    def __init__(self, prompt_name: str, message: str, missing_variables: list[str] | None = None) -> None:
        """Initialize prompt render error.

        Args:
            prompt_name: Name of the prompt that failed to render
            message: Human-readable error message
            missing_variables: List of missing required variables
        """
        self.prompt_name = prompt_name
        self.message = message
        self.missing_variables = missing_variables or []

        error_msg = f"Failed to render prompt '{prompt_name}': {message}"
        if self.missing_variables:
            error_msg += f" (Missing variables: {', '.join(self.missing_variables)})"

        super().__init__(error_msg)

    def __str__(self) -> str:
        """Return string representation of the error."""
        error_msg = f"Failed to render prompt '{self.prompt_name}': {self.message}"
        if self.missing_variables:
            error_msg += f" (Missing variables: {', '.join(self.missing_variables)})"
        return error_msg
