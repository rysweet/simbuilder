"""
Azure OpenAI client with async support, retry logic, and error handling.
"""

import logging
from collections.abc import AsyncGenerator
from typing import Any

from openai import AsyncAzureOpenAI
from openai.types import CreateEmbeddingResponse
from openai.types.chat import ChatCompletion
from openai.types.chat import ChatCompletionChunk
from pydantic import BaseModel
from tenacity import retry
from tenacity import retry_if_exception_type
from tenacity import stop_after_attempt
from tenacity import wait_exponential

from src.scaffolding.config import get_settings

from .exceptions import LLMError

logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str
    content: str


class AzureOpenAIClient:
    """Async Azure OpenAI client with retry logic and error handling."""

    def __init__(self, settings: Any | None = None) -> None:
        """Initialize the Azure OpenAI client.
        
        Args:
            settings: Application settings (defaults to global settings)
        """
        self._settings = settings or get_settings()
        self._client: AsyncAzureOpenAI | None = None

    @property
    def client(self) -> AsyncAzureOpenAI:
        """Get or create the OpenAI client."""
        if self._client is None:
            self._client = AsyncAzureOpenAI(
                api_key=self._settings.azure_openai_key,
                api_version=self._settings.azure_openai_api_version,
                azure_endpoint=self._settings.azure_openai_endpoint,
            )
        return self._client

    def __repr__(self) -> str:
        """Return string representation with masked credentials."""
        masked_key = "***" if self._settings.azure_openai_key else "None"
        return (
            f"AzureOpenAIClient("
            f"endpoint={self._settings.azure_openai_endpoint}, "
            f"api_version={self._settings.azure_openai_api_version}, "
            f"api_key={masked_key})"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    async def create_chat_completion(
        self,
        messages: list[ChatMessage] | list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> ChatCompletion | AsyncGenerator[ChatCompletionChunk, None]:
        """Create a chat completion.
        
        Args:
            messages: List of chat messages
            model: Model to use (defaults to chat model from settings)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional parameters for the API call
            
        Returns:
            Chat completion response or async generator for streaming
            
        Raises:
            LLMError: If the API call fails
        """
        try:
            # Convert ChatMessage objects to dicts if needed
            if messages and isinstance(messages[0], ChatMessage):
                message_dicts = [{"role": msg.role, "content": msg.content} for msg in messages]
            else:
                message_dicts = messages

            model = model or self._settings.azure_openai_model_chat

            logger.debug(
                f"Creating chat completion with model={model}, "
                f"temperature={temperature}, max_tokens={max_tokens}, stream={stream}"
            )

            response = await self.client.chat.completions.create(
                model=model,
                messages=message_dicts,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs,
            )

            if stream:
                return self._stream_chat_completion(response)

            return response

        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise LLMError(f"Failed to create chat completion: {str(e)}", original_error=e)

    async def _stream_chat_completion(
        self, response: Any
    ) -> AsyncGenerator[ChatCompletionChunk, None]:
        """Stream chat completion chunks.
        
        Args:
            response: Streaming response from OpenAI
            
        Yields:
            Chat completion chunks
        """
        try:
            async for chunk in response:
                yield chunk
        except Exception as e:
            logger.error(f"Streaming chat completion failed: {e}")
            raise LLMError(f"Failed to stream chat completion: {str(e)}", original_error=e)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    async def create_embeddings(
        self,
        input_text: str | list[str],
        model: str | None = None,
        **kwargs: Any,
    ) -> CreateEmbeddingResponse:
        """Create embeddings for the given text.
        
        Args:
            input_text: Text or list of texts to embed
            model: Model to use (defaults to embedding model from settings)
            **kwargs: Additional parameters for the API call
            
        Returns:
            Embedding response
            
        Raises:
            LLMError: If the API call fails
        """
        try:
            # Note: Azure OpenAI uses the same model for embeddings as chat for now
            # In practice, you'd have a separate embedding model
            model = model or self._settings.azure_openai_model_chat

            logger.debug(f"Creating embeddings with model={model}")

            response = await self.client.embeddings.create(
                model=model,
                input=input_text,
                **kwargs,
            )

            return response

        except Exception as e:
            logger.error(f"Embedding creation failed: {e}")
            raise LLMError(f"Failed to create embeddings: {str(e)}", original_error=e)

    async def check_health(self) -> dict[str, Any]:
        """Check the health of the OpenAI connection.
        
        Returns:
            Health status information
        """
        try:
            # Simple health check by creating a minimal completion
            messages = [{"role": "user", "content": "Hello"}]

            response = await self.client.chat.completions.create(
                model=self._settings.azure_openai_model_chat,
                messages=messages,
                max_tokens=1,
                temperature=0,
            )

            return {
                "status": "healthy",
                "model": self._settings.azure_openai_model_chat,
                "endpoint": self._settings.azure_openai_endpoint,
                "api_version": self._settings.azure_openai_api_version,
                "response_id": response.id,
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "model": self._settings.azure_openai_model_chat,
                "endpoint": self._settings.azure_openai_endpoint,
                "api_version": self._settings.azure_openai_api_version,
            }

    async def get_models(self) -> list[str]:
        """Get available models.
        
        Returns:
            List of available model names
            
        Raises:
            LLMError: If the API call fails
        """
        try:
            models = await self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            logger.error(f"Failed to get models: {e}")
            raise LLMError(f"Failed to get available models: {str(e)}", original_error=e)

    async def close(self) -> None:
        """Close the client connection."""
        if self._client:
            await self._client.close()
            self._client = None
