"""
SimBuilder LLM Integration - Azure OpenAI client and prompt rendering system.

This package provides a shared, fully-testable Azure OpenAI client and prompt-rendering 
layer for downstream discovery and simulation logic.
"""

from .client import AzureOpenAIClient
from .exceptions import LLMError
from .exceptions import PromptRenderError
from .prompts import load_prompt
from .prompts import render_prompt

__all__ = [
    "AzureOpenAIClient",
    "LLMError",
    "PromptRenderError",
    "load_prompt",
    "render_prompt",
]
