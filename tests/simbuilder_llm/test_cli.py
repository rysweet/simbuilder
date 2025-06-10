"""
Tests for the LLM CLI module.
"""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from src.simbuilder_llm.cli import app
from src.simbuilder_llm.exceptions import LLMError
from src.simbuilder_llm.exceptions import PromptRenderError


@pytest.fixture
def runner():
    """Provide a CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_settings():
    """Provide mock settings for testing."""
    settings = MagicMock()
    settings.azure_openai_endpoint = "https://test.openai.azure.com/"
    settings.azure_openai_key = "test-key"
    settings.azure_openai_api_version = "2024-02-15-preview"
    settings.azure_openai_model_chat = "gpt-4o"
    settings.azure_openai_model_reasoning = "gpt-4o"
    return settings


class TestChatCommand:
    """Tests for the chat command."""

    @patch("src.simbuilder_llm.cli.render_prompt")
    @patch("src.simbuilder_llm.cli.AzureOpenAIClient")
    def test_chat_success(self, mock_client_class, mock_render_prompt, runner):
        """Test successful chat command."""
        # Mock prompt rendering
        mock_render_prompt.return_value = "Hello, how can I help you?"

        # Mock client and response
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "I'm here to help!"
        mock_client.create_chat_completion.return_value = mock_response
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            app, ["chat", "--prompt", "base_prompt", "--variables", '{"question": "Hello"}']
        )

        assert result.exit_code == 0
        assert "I'm here to help!" in result.stdout
        mock_render_prompt.assert_called_once_with("base_prompt", {"question": "Hello"})

    def test_chat_invalid_json(self, runner):
        """Test chat command with invalid JSON variables."""
        result = runner.invoke(
            app, ["chat", "--prompt", "base_prompt", "--variables", '{"invalid": json}']
        )

        assert result.exit_code == 1
        assert "Invalid JSON in variables" in result.stdout

    @patch("src.simbuilder_llm.cli.render_prompt")
    def test_chat_prompt_render_error(self, mock_render_prompt, runner):
        """Test chat command with prompt rendering error."""
        mock_render_prompt.side_effect = PromptRenderError(
            "base_prompt", "Missing variables", ["question"]
        )

        result = runner.invoke(app, ["chat", "--prompt", "base_prompt", "--variables", "{}"])

        assert result.exit_code == 1
        assert "Failed to render prompt" in result.stdout

    @patch("src.simbuilder_llm.cli.render_prompt")
    @patch("src.simbuilder_llm.cli.AzureOpenAIClient")
    def test_chat_with_streaming(self, mock_client_class, mock_render_prompt, runner):
        """Test chat command with streaming enabled."""
        mock_render_prompt.return_value = "Hello"

        # Mock streaming response
        async def mock_stream():
            chunk1 = MagicMock()
            chunk1.choices = [MagicMock()]
            chunk1.choices[0].delta.content = "Hello "
            yield chunk1

            chunk2 = MagicMock()
            chunk2.choices = [MagicMock()]
            chunk2.choices[0].delta.content = "world!"
            yield chunk2

        mock_client = AsyncMock()
        mock_client.create_chat_completion.return_value = mock_stream()
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            app,
            ["chat", "--prompt", "base_prompt", "--variables", '{"question": "Hello"}', "--stream"],
        )

        assert result.exit_code == 0
        assert "Streaming response" in result.stdout

    @patch("src.simbuilder_llm.cli.render_prompt")
    @patch("src.simbuilder_llm.cli.AzureOpenAIClient")
    def test_chat_llm_error(self, mock_client_class, mock_render_prompt, runner):
        """Test chat command with LLM error."""
        mock_render_prompt.return_value = "Hello"

        mock_client = AsyncMock()
        mock_client.create_chat_completion.side_effect = LLMError("API Error")
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            app, ["chat", "--prompt", "base_prompt", "--variables", '{"question": "Hello"}']
        )

        assert result.exit_code == 1
        assert "LLM Error" in result.stdout

    @patch("src.simbuilder_llm.cli.render_prompt")
    @patch("src.simbuilder_llm.cli.AzureOpenAIClient")
    def test_chat_with_custom_options(self, mock_client_class, mock_render_prompt, runner):
        """Test chat command with custom options."""
        mock_render_prompt.return_value = "Hello"

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_client.create_chat_completion.return_value = mock_response
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            app,
            [
                "chat",
                "--prompt",
                "base_prompt",
                "--variables",
                '{"question": "Hello"}',
                "--model",
                "custom-model",
                "--temperature",
                "0.5",
                "--max-tokens",
                "100",
            ],
        )

        assert result.exit_code == 0
        mock_client.create_chat_completion.assert_called_once()
        call_args = mock_client.create_chat_completion.call_args
        assert call_args[1]["model"] == "custom-model"
        assert call_args[1]["temperature"] == 0.5
        assert call_args[1]["max_tokens"] == 100


class TestEmbedCommand:
    """Tests for the embed command."""

    @patch("src.simbuilder_llm.cli.AzureOpenAIClient")
    def test_embed_summary_format(self, mock_client_class, runner):
        """Test embed command with summary format."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.model = "gpt-4o"
        mock_response.usage.total_tokens = 10
        mock_response.data = [MagicMock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3]
        mock_client.create_embeddings.return_value = mock_response
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["embed", "--text", "Hello world", "--format", "summary"])

        assert result.exit_code == 0
        assert "Embedding Summary" in result.stdout
        assert "gpt-4o" in result.stdout

    @patch("src.simbuilder_llm.cli.AzureOpenAIClient")
    def test_embed_json_format(self, mock_client_class, runner):
        """Test embed command with JSON format."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {"model": "gpt-4o", "data": []}
        mock_client.create_embeddings.return_value = mock_response
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["embed", "--text", "Hello world", "--format", "json"])

        assert result.exit_code == 0
        # Should contain JSON output
        assert "{" in result.stdout

    @patch("src.simbuilder_llm.cli.AzureOpenAIClient")
    def test_embed_values_format(self, mock_client_class, runner):
        """Test embed command with values format."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.data = [MagicMock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3]
        mock_client.create_embeddings.return_value = mock_response
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["embed", "--text", "Hello world", "--format", "values"])

        assert result.exit_code == 0
        # Should contain the embedding values
        assert "0.1" in result.stdout

    @patch("src.simbuilder_llm.cli.AzureOpenAIClient")
    def test_embed_llm_error(self, mock_client_class, runner):
        """Test embed command with LLM error."""
        mock_client = AsyncMock()
        mock_client.create_embeddings.side_effect = LLMError("API Error")
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["embed", "--text", "Hello world"])

        assert result.exit_code == 1
        assert "LLM Error" in result.stdout


class TestInfoCommand:
    """Tests for the info command."""

    @patch("src.simbuilder_llm.cli.get_settings")
    @patch("src.simbuilder_llm.cli.list_prompts")
    def test_info_success(self, mock_list_prompts, mock_get_settings, runner):
        """Test successful info command."""
        mock_get_settings.return_value = MagicMock(
            azure_openai_endpoint="https://test.openai.azure.com/",
            azure_openai_api_version="2024-02-15-preview",
            azure_openai_model_chat="gpt-4o",
            azure_openai_model_reasoning="gpt-4o",
            azure_openai_key="test-key",
        )
        mock_list_prompts.return_value = ["base_prompt", "custom_prompt"]

        result = runner.invoke(app, ["info"])

        assert result.exit_code == 0
        assert "LLM Configuration" in result.stdout
        assert "https://test.openai.azure.com/" in result.stdout
        assert "Available Prompts" in result.stdout
        assert "base_prompt" in result.stdout

    @patch("src.simbuilder_llm.cli.get_settings")
    @patch("src.simbuilder_llm.cli.list_prompts")
    def test_info_no_api_key(self, mock_list_prompts, mock_get_settings, runner):
        """Test info command with no API key."""
        mock_settings = MagicMock()
        mock_settings.azure_openai_endpoint = "https://test.openai.azure.com/"
        mock_settings.azure_openai_api_version = "2024-02-15-preview"
        mock_settings.azure_openai_model_chat = "gpt-4o"
        mock_settings.azure_openai_model_reasoning = "gpt-4o"
        mock_settings.azure_openai_key = None
        mock_get_settings.return_value = mock_settings
        mock_list_prompts.return_value = []

        result = runner.invoke(app, ["info"])

        assert result.exit_code == 0
        assert "Not Set" in result.stdout

    @patch("src.simbuilder_llm.cli.get_settings")
    @patch("src.simbuilder_llm.cli.list_prompts")
    def test_info_no_prompts(self, mock_list_prompts, mock_get_settings, runner):
        """Test info command with no prompts."""
        mock_settings = MagicMock()
        mock_settings.azure_openai_endpoint = "https://test.openai.azure.com/"
        mock_settings.azure_openai_api_version = "2024-02-15-preview"
        mock_settings.azure_openai_model_chat = "gpt-4o"
        mock_settings.azure_openai_model_reasoning = "gpt-4o"
        mock_settings.azure_openai_key = "test-key"
        mock_get_settings.return_value = mock_settings
        mock_list_prompts.return_value = []

        result = runner.invoke(app, ["info"])

        assert result.exit_code == 0
        assert "No prompt templates found" in result.stdout

    @patch("src.simbuilder_llm.cli.get_settings")
    def test_info_error(self, mock_get_settings, runner):
        """Test info command with error."""
        mock_get_settings.side_effect = Exception("Config error")

        result = runner.invoke(app, ["info"])

        assert result.exit_code == 1
        assert "Error" in result.stdout


class TestCheckCommand:
    """Tests for the check command."""

    @patch("src.simbuilder_llm.cli.get_settings")
    @patch("src.simbuilder_llm.cli._check_connectivity")
    @patch("src.simbuilder_llm.cli._check_configuration")
    def test_check_all_pass(
        self, mock_check_config, mock_check_connectivity, mock_get_settings, runner
    ):
        """Test check command with all checks passing."""
        mock_get_settings.return_value = MagicMock()
        mock_check_config.return_value = [
            ("Config Test", True, "OK"),
        ]

        # Mock async function properly
        mock_check_connectivity.return_value = [("Connectivity Test", True, "Connected")]

        result = runner.invoke(app, ["check"])

        assert result.exit_code == 0
        assert "LLM Health Check" in result.stdout
        assert "✓ PASS" in result.stdout

    @patch("src.simbuilder_llm.cli.get_settings")
    @patch("src.simbuilder_llm.cli._check_connectivity")
    @patch("src.simbuilder_llm.cli._check_configuration")
    def test_check_some_fail(
        self, mock_check_config, mock_check_connectivity, mock_get_settings, runner
    ):
        """Test check command with some checks failing."""
        mock_get_settings.return_value = MagicMock()
        mock_check_config.return_value = [
            ("Config Test", False, "Failed"),
        ]

        mock_check_connectivity.return_value = [("Connectivity Test", True, "Connected")]

        result = runner.invoke(app, ["check"])

        assert result.exit_code == 1
        assert "✗ FAIL" in result.stdout

    @patch("src.simbuilder_llm.cli.get_settings")
    def test_check_error(self, mock_get_settings, runner):
        """Test check command with error."""
        mock_get_settings.side_effect = Exception("Config error")

        result = runner.invoke(app, ["check"])

        assert result.exit_code == 1
        assert "Error" in result.stdout


class TestCheckHelpers:
    """Tests for check helper functions."""

    def test_check_configuration_all_set(self, mock_settings):
        """Test configuration check with all settings."""
        from src.simbuilder_llm.cli import _check_configuration

        checks = _check_configuration(mock_settings)

        # All checks should pass
        assert len(checks) == 4
        assert all(status for _, status, _ in checks)

    def test_check_configuration_missing_settings(self):
        """Test configuration check with missing settings."""
        from src.simbuilder_llm.cli import _check_configuration

        settings = MagicMock()
        settings.azure_openai_endpoint = None
        settings.azure_openai_key = None
        settings.azure_openai_api_version = None
        settings.azure_openai_model_chat = None

        checks = _check_configuration(settings)

        # All checks should fail
        assert len(checks) == 4
        assert not any(status for _, status, _ in checks)

    @pytest.mark.asyncio
    @patch("src.simbuilder_llm.cli.AzureOpenAIClient")
    async def test_check_connectivity_success(self, mock_client_class):
        """Test successful connectivity check."""
        from src.simbuilder_llm.cli import _check_connectivity

        mock_client = AsyncMock()
        mock_client.check_health.return_value = {"status": "healthy", "response_id": "test-id"}
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client

        checks = await _check_connectivity()

        assert len(checks) == 1
        check_name, status, details = checks[0]
        assert check_name == "Azure OpenAI Connectivity"
        assert status is True
        assert "test-id" in details

    @pytest.mark.asyncio
    @patch("src.simbuilder_llm.cli.AzureOpenAIClient")
    async def test_check_connectivity_failure(self, mock_client_class):
        """Test failed connectivity check."""
        from src.simbuilder_llm.cli import _check_connectivity

        mock_client = AsyncMock()
        mock_client.check_health.return_value = {
            "status": "unhealthy",
            "error": "Connection failed",
        }
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client

        checks = await _check_connectivity()

        assert len(checks) == 1
        check_name, status, details = checks[0]
        assert check_name == "Azure OpenAI Connectivity"
        assert status is False
        assert "Connection failed" in details

    @pytest.mark.asyncio
    @patch("src.simbuilder_llm.cli.AzureOpenAIClient")
    async def test_check_connectivity_exception(self, mock_client_class):
        """Test connectivity check with exception."""
        from src.simbuilder_llm.cli import _check_connectivity

        mock_client = AsyncMock()
        mock_client.check_health.side_effect = Exception("Network error")
        mock_client.close = AsyncMock()
        mock_client_class.return_value = mock_client

        checks = await _check_connectivity()

        assert len(checks) == 1
        check_name, status, details = checks[0]
        assert check_name == "Azure OpenAI Connectivity"
        assert status is False
        assert "Network error" in details
