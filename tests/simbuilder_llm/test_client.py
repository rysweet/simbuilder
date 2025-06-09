"""
Tests for the Azure OpenAI client module.
"""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from openai.types.chat import ChatCompletion, ChatCompletionChunk, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice, ChoiceDelta
from openai.types import CreateEmbeddingResponse, Embedding
from openai import APIError, RateLimitError

from src.simbuilder_llm.client import AzureOpenAIClient, ChatMessage
from src.simbuilder_llm.exceptions import LLMError


class MockSettings:
    """Mock settings for testing."""
    
    def __init__(self):
        self.azure_openai_endpoint = "https://test.openai.azure.com/"
        self.azure_openai_key = "test-api-key"
        self.azure_openai_api_version = "2024-02-15-preview"
        self.azure_openai_model_chat = "gpt-4o"
        self.azure_openai_model_reasoning = "gpt-4o"


@pytest.fixture
def mock_settings():
    """Provide mock settings."""
    return MockSettings()


@pytest.fixture
def client(mock_settings):
    """Provide a client instance with mock settings."""
    return AzureOpenAIClient(mock_settings)


class TestAzureOpenAIClient:
    """Tests for AzureOpenAIClient."""

    def test_init_with_settings(self, mock_settings):
        """Test client initialization with provided settings."""
        client = AzureOpenAIClient(mock_settings)
        assert client._settings == mock_settings
        assert client._client is None

    @patch('src.simbuilder_llm.client.get_settings')
    def test_init_without_settings(self, mock_get_settings):
        """Test client initialization without provided settings."""
        mock_get_settings.return_value = MockSettings()
        client = AzureOpenAIClient()
        assert client._settings is not None
        mock_get_settings.assert_called_once()

    def test_repr_masks_credentials(self, client):
        """Test that repr masks API key."""
        repr_str = repr(client)
        assert "api_key=***" in repr_str
        assert "test-api-key" not in repr_str
        assert "https://test.openai.azure.com/" in repr_str

    def test_repr_shows_none_for_missing_key(self, mock_settings):
        """Test that repr shows None for missing API key."""
        mock_settings.azure_openai_key = None
        client = AzureOpenAIClient(mock_settings)
        repr_str = repr(client)
        assert "api_key=None" in repr_str

    @patch('src.simbuilder_llm.client.AsyncAzureOpenAI')
    def test_client_property_creates_client(self, mock_azure_openai, client):
        """Test that client property creates AsyncAzureOpenAI instance."""
        mock_instance = MagicMock()
        mock_azure_openai.return_value = mock_instance
        
        result = client.client
        
        assert result == mock_instance
        mock_azure_openai.assert_called_once_with(
            api_key="test-api-key",
            api_version="2024-02-15-preview",
            azure_endpoint="https://test.openai.azure.com/",
        )

    @patch('src.simbuilder_llm.client.AsyncAzureOpenAI')
    def test_client_property_caches_client(self, mock_azure_openai, client):
        """Test that client property caches the client instance."""
        mock_instance = MagicMock()
        mock_azure_openai.return_value = mock_instance
        
        # Call twice
        result1 = client.client
        result2 = client.client
        
        assert result1 == result2
        # Should only create once
        mock_azure_openai.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_chat_completion_success(self, client):
        """Test successful chat completion."""
        # Mock the OpenAI client
        mock_client = AsyncMock()
        mock_response = ChatCompletion(
            id="test-id",
            choices=[
                Choice(
                    index=0,
                    message=ChatCompletionMessage(role="assistant", content="Test response"),
                    finish_reason="stop"
                )
            ],
            created=1234567890,
            model="gpt-4o",
            object="chat.completion",
        )
        mock_client.chat.completions.create.return_value = mock_response
        client._client = mock_client

        messages = [ChatMessage(role="user", content="Hello")]
        result = await client.create_chat_completion(messages)

        assert result == mock_response
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.7,
            max_tokens=None,
            stream=False,
        )

    @pytest.mark.asyncio
    async def test_create_chat_completion_with_dict_messages(self, client):
        """Test chat completion with dict messages."""
        mock_client = AsyncMock()
        mock_response = ChatCompletion(
            id="test-id",
            choices=[
                Choice(
                    index=0,
                    message=ChatCompletionMessage(role="assistant", content="Test response"),
                    finish_reason="stop"
                )
            ],
            created=1234567890,
            model="gpt-4o",
            object="chat.completion",
        )
        mock_client.chat.completions.create.return_value = mock_response
        client._client = mock_client

        messages = [{"role": "user", "content": "Hello"}]
        result = await client.create_chat_completion(messages)

        assert result == mock_response
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.7,
            max_tokens=None,
            stream=False,
        )

    @pytest.mark.asyncio
    async def test_create_chat_completion_with_custom_params(self, client):
        """Test chat completion with custom parameters."""
        mock_client = AsyncMock()
        mock_response = ChatCompletion(
            id="test-id",
            choices=[
                Choice(
                    index=0,
                    message=ChatCompletionMessage(role="assistant", content="Test response"),
                    finish_reason="stop"
                )
            ],
            created=1234567890,
            model="custom-model",
            object="chat.completion",
        )
        mock_client.chat.completions.create.return_value = mock_response
        client._client = mock_client

        messages = [ChatMessage(role="user", content="Hello")]
        result = await client.create_chat_completion(
            messages,
            model="custom-model",
            temperature=0.5,
            max_tokens=100,
            top_p=0.9
        )

        assert result == mock_response
        mock_client.chat.completions.create.assert_called_once_with(
            model="custom-model",
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.5,
            max_tokens=100,
            stream=False,
            top_p=0.9,
        )

    @pytest.mark.asyncio
    async def test_create_chat_completion_streaming(self, client):
        """Test streaming chat completion."""
        mock_client = AsyncMock()
        
        # Mock streaming response
        async def mock_stream():
            yield ChatCompletionChunk(
                id="test-id",
                choices=[
                    ChunkChoice(
                        index=0,
                        delta=ChoiceDelta(content="Hello"),
                        finish_reason=None
                    )
                ],
                created=1234567890,
                model="gpt-4o",
                object="chat.completion.chunk",
            )
            yield ChatCompletionChunk(
                id="test-id",
                choices=[
                    ChunkChoice(
                        index=0,
                        delta=ChoiceDelta(content=" world"),
                        finish_reason="stop"
                    )
                ],
                created=1234567890,
                model="gpt-4o",
                object="chat.completion.chunk",
            )

        mock_client.chat.completions.create.return_value = mock_stream()
        client._client = mock_client

        messages = [ChatMessage(role="user", content="Hello")]
        result = await client.create_chat_completion(messages, stream=True)

        # Collect all chunks
        chunks = []
        async for chunk in result:
            chunks.append(chunk)

        assert len(chunks) == 2
        assert chunks[0].choices[0].delta.content == "Hello"
        assert chunks[1].choices[0].delta.content == " world"

    @pytest.mark.asyncio
    async def test_create_chat_completion_api_error(self, client):
        """Test chat completion with API error."""
        mock_client = AsyncMock()
        # Create a mock request for APIError
        mock_request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
        mock_client.chat.completions.create.side_effect = APIError("API Error", request=mock_request, body=None)
        client._client = mock_client

        messages = [ChatMessage(role="user", content="Hello")]
        
        with pytest.raises(LLMError) as exc_info:
            await client.create_chat_completion(messages)
        
        assert "Failed to create chat completion" in str(exc_info.value)
        assert exc_info.value.original_error is not None

    @pytest.mark.asyncio
    async def test_create_chat_completion_rate_limit_retry(self, client):
        """Test that rate limit errors trigger retry."""
        mock_client = AsyncMock()
        
        # First call fails with rate limit, second succeeds
        mock_response = ChatCompletion(
            id="test-id",
            choices=[
                Choice(
                    index=0,
                    message=ChatCompletionMessage(role="assistant", content="Test response"),
                    finish_reason="stop"
                )
            ],
            created=1234567890,
            model="gpt-4o",
            object="chat.completion",
        )
        
        # Create a mock response for RateLimitError
        mock_response_obj = MagicMock()
        mock_response_obj.request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
        
        mock_client.chat.completions.create.side_effect = [
            RateLimitError("Rate limit exceeded", response=mock_response_obj, body=None),
            mock_response
        ]
        client._client = mock_client

        messages = [ChatMessage(role="user", content="Hello")]
        
        # This should succeed after retry
        result = await client.create_chat_completion(messages)
        assert result == mock_response
        assert mock_client.chat.completions.create.call_count == 2

    @pytest.mark.asyncio
    async def test_create_embeddings_success(self, client):
        """Test successful embedding creation."""
        mock_client = AsyncMock()
        mock_response = CreateEmbeddingResponse(
            object="list",
            data=[
                Embedding(
                    object="embedding",
                    embedding=[0.1, 0.2, 0.3],
                    index=0
                )
            ],
            model="gpt-4o",
            usage={"prompt_tokens": 5, "total_tokens": 5}
        )
        mock_client.embeddings.create.return_value = mock_response
        client._client = mock_client

        result = await client.create_embeddings("Hello world")

        assert result == mock_response
        mock_client.embeddings.create.assert_called_once_with(
            model="gpt-4o",
            input="Hello world",
        )

    @pytest.mark.asyncio
    async def test_create_embeddings_with_list_input(self, client):
        """Test embedding creation with list input."""
        mock_client = AsyncMock()
        mock_response = CreateEmbeddingResponse(
            object="list",
            data=[
                Embedding(object="embedding", embedding=[0.1, 0.2, 0.3], index=0),
                Embedding(object="embedding", embedding=[0.4, 0.5, 0.6], index=1)
            ],
            model="gpt-4o",
            usage={"prompt_tokens": 10, "total_tokens": 10}
        )
        mock_client.embeddings.create.return_value = mock_response
        client._client = mock_client

        result = await client.create_embeddings(["Hello", "world"])

        assert result == mock_response
        mock_client.embeddings.create.assert_called_once_with(
            model="gpt-4o",
            input=["Hello", "world"],
        )

    @pytest.mark.asyncio
    async def test_create_embeddings_api_error(self, client):
        """Test embedding creation with API error."""
        mock_client = AsyncMock()
        mock_request = httpx.Request("POST", "https://api.openai.com/v1/embeddings")
        mock_client.embeddings.create.side_effect = APIError("API Error", request=mock_request, body=None)
        client._client = mock_client

        with pytest.raises(LLMError) as exc_info:
            await client.create_embeddings("Hello world")
        
        assert "Failed to create embeddings" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_check_health_success(self, client):
        """Test successful health check."""
        mock_client = AsyncMock()
        mock_response = ChatCompletion(
            id="health-check-id",
            choices=[
                Choice(
                    index=0,
                    message=ChatCompletionMessage(role="assistant", content="Hi"),
                    finish_reason="stop"
                )
            ],
            created=1234567890,
            model="gpt-4o",
            object="chat.completion",
        )
        mock_client.chat.completions.create.return_value = mock_response
        client._client = mock_client

        result = await client.check_health()

        assert result["status"] == "healthy"
        assert result["model"] == "gpt-4o"
        assert result["response_id"] == "health-check-id"

    @pytest.mark.asyncio
    async def test_check_health_failure(self, client):
        """Test health check failure."""
        mock_client = AsyncMock()
        mock_request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
        mock_client.chat.completions.create.side_effect = APIError("API Error", request=mock_request, body=None)
        client._client = mock_client

        result = await client.check_health()

        assert result["status"] == "unhealthy"
        assert "API Error" in result["error"]

    @pytest.mark.asyncio
    async def test_get_models_success(self, client):
        """Test successful model retrieval."""
        mock_client = AsyncMock()
        mock_models = MagicMock()
        mock_models.data = [
            MagicMock(id="gpt-4o"),
            MagicMock(id="gpt-3.5-turbo"),
        ]
        mock_client.models.list.return_value = mock_models
        client._client = mock_client

        result = await client.get_models()

        assert result == ["gpt-4o", "gpt-3.5-turbo"]

    @pytest.mark.asyncio
    async def test_get_models_api_error(self, client):
        """Test model retrieval with API error."""
        mock_client = AsyncMock()
        mock_request = httpx.Request("GET", "https://api.openai.com/v1/models")
        mock_client.models.list.side_effect = APIError("API Error", request=mock_request, body=None)
        client._client = mock_client

        with pytest.raises(LLMError) as exc_info:
            await client.get_models()
        
        assert "Failed to get available models" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_close(self, client):
        """Test client close."""
        mock_client = AsyncMock()
        client._client = mock_client

        await client.close()

        mock_client.close.assert_called_once()
        assert client._client is None

    @pytest.mark.asyncio
    async def test_close_no_client(self, client):
        """Test close when no client exists."""
        # Should not raise an error
        await client.close()
        assert client._client is None