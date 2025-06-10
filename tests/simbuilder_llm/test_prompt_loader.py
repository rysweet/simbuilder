"""
Tests for the prompt loading and rendering system.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest

from src.simbuilder_llm.exceptions import PromptRenderError
from src.simbuilder_llm.prompts import PromptLoader
from src.simbuilder_llm.prompts import get_prompt_loader
from src.simbuilder_llm.prompts import list_prompts
from src.simbuilder_llm.prompts import load_prompt
from src.simbuilder_llm.prompts import render_prompt


@pytest.fixture
def temp_template_dir():
    """Create a temporary directory with test templates."""
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test templates
        (temp_path / "simple.liquid").write_text("Hello {{ name }}!")

        (temp_path / "with_optional.liquid").write_text("""
Hello {{ name }}!
{% if greeting %}{{ greeting }}{% endif %}
{% if message %}Message: {{ message }}{% endif %}
""".strip())

        (temp_path / "complex.liquid").write_text("""
User: {{ user }}
Context: {{ context }}
Question: {{ question }}
{% if additional_info %}
Additional Info: {{ additional_info }}
{% endif %}
""".strip())

        (temp_path / "syntax_error.liquid").write_text("Hello {{ name")  # Missing closing brace

        (temp_path / "test.jinja").write_text("Jinja template: {{ value }}")

        yield temp_path


class TestPromptLoader:
    """Tests for PromptLoader class."""

    def test_init_with_custom_dir(self, temp_template_dir):
        """Test initialization with custom template directory."""
        loader = PromptLoader(temp_template_dir)
        assert loader.template_dir == temp_template_dir

    def test_init_default_dir(self):
        """Test initialization with default template directory."""
        loader = PromptLoader()
        # Should default to prompts/ directory in the package
        assert loader.template_dir.name == "prompts"

    def test_load_template_success(self, temp_template_dir):
        """Test successful template loading."""
        loader = PromptLoader(temp_template_dir)

        template = loader.load_template("simple")
        assert template is not None

    def test_load_template_with_extension(self, temp_template_dir):
        """Test loading template with explicit extension."""
        loader = PromptLoader(temp_template_dir)

        template = loader.load_template("simple.liquid")
        assert template is not None

    def test_load_template_jinja_extension(self, temp_template_dir):
        """Test loading template with jinja extension."""
        loader = PromptLoader(temp_template_dir)

        template = loader.load_template("test.jinja")
        assert template is not None

    def test_load_template_not_found(self, temp_template_dir):
        """Test loading non-existent template."""
        loader = PromptLoader(temp_template_dir)

        with pytest.raises(PromptRenderError) as exc_info:
            loader.load_template("nonexistent")

        assert "Template not found" in str(exc_info.value)
        assert exc_info.value.prompt_name == "nonexistent"

    def test_load_template_syntax_error(self, temp_template_dir):
        """Test loading template with syntax error."""
        loader = PromptLoader(temp_template_dir)

        with pytest.raises(PromptRenderError) as exc_info:
            loader.load_template("syntax_error")

        assert "Template has syntax errors" in str(exc_info.value)

    def test_load_template_caching(self, temp_template_dir):
        """Test that templates are cached."""
        loader = PromptLoader(temp_template_dir)

        # Load same template twice
        template1 = loader.load_template("simple")
        template2 = loader.load_template("simple")

        # Should be the same object due to caching
        assert template1 is template2

    def test_extract_variables_simple(self, temp_template_dir):
        """Test variable extraction from simple template."""
        loader = PromptLoader(temp_template_dir)

        variables = loader.extract_variables("simple")
        assert "name" in variables

    def test_extract_variables_complex(self, temp_template_dir):
        """Test variable extraction from complex template."""
        loader = PromptLoader(temp_template_dir)

        variables = loader.extract_variables("complex")
        expected_vars = {"user", "context", "question", "additional_info"}
        assert variables.intersection(expected_vars) == expected_vars

    def test_extract_variables_error_handling(self, temp_template_dir):
        """Test variable extraction error handling."""
        loader = PromptLoader(temp_template_dir)

        # Should return empty set on error, not raise
        variables = loader.extract_variables("nonexistent")
        assert variables == set()

    def test_render_template_success(self, temp_template_dir):
        """Test successful template rendering."""
        loader = PromptLoader(temp_template_dir)

        result = loader.render_template("simple", {"name": "World"})
        assert result == "Hello World!"

    def test_render_template_with_optional_vars(self, temp_template_dir):
        """Test rendering template with optional variables."""
        loader = PromptLoader(temp_template_dir)

        # Only provide required variable
        result = loader.render_template("with_optional", {"name": "Alice"}, validate_variables=False)
        assert "Hello Alice!" in result

    def test_render_template_missing_variables(self, temp_template_dir):
        """Test rendering with missing required variables."""
        loader = PromptLoader(temp_template_dir)

        with pytest.raises(PromptRenderError) as exc_info:
            loader.render_template("simple", {})

        assert "Missing required variables" in str(exc_info.value)
        assert "name" in exc_info.value.missing_variables

    def test_render_template_skip_validation(self, temp_template_dir):
        """Test rendering with validation disabled."""
        loader = PromptLoader(temp_template_dir)

        # Should not raise even with missing variables
        result = loader.render_template("simple", {}, validate_variables=False)
        assert "Hello !" in result

    def test_render_template_not_found(self, temp_template_dir):
        """Test rendering non-existent template."""
        loader = PromptLoader(temp_template_dir)

        with pytest.raises(PromptRenderError) as exc_info:
            loader.render_template("nonexistent", {})

        assert exc_info.value.prompt_name == "nonexistent"

    def test_list_templates(self, temp_template_dir):
        """Test listing available templates."""
        loader = PromptLoader(temp_template_dir)

        templates = loader.list_templates()
        expected_templates = {"simple", "with_optional", "complex", "syntax_error", "test"}
        assert set(templates) == expected_templates

    def test_list_templates_empty_dir(self):
        """Test listing templates in empty directory."""
        with TemporaryDirectory() as temp_dir:
            loader = PromptLoader(Path(temp_dir))
            templates = loader.list_templates()
            assert templates == []


class TestGlobalFunctions:
    """Tests for global prompt functions."""

    @patch('src.simbuilder_llm.prompts._prompt_loader', None)
    def test_get_prompt_loader_creates_instance(self):
        """Test that get_prompt_loader creates a new instance."""
        loader = get_prompt_loader()
        assert isinstance(loader, PromptLoader)

    @patch('src.simbuilder_llm.prompts._prompt_loader')
    def test_get_prompt_loader_returns_existing(self, mock_loader):
        """Test that get_prompt_loader returns existing instance."""
        result = get_prompt_loader()
        assert result == mock_loader

    def test_load_prompt_function(self, temp_template_dir):
        """Test global load_prompt function."""
        with patch('src.simbuilder_llm.prompts.get_prompt_loader') as mock_get_loader:
            mock_loader = PromptLoader(temp_template_dir)
            mock_get_loader.return_value = mock_loader

            template = load_prompt("simple")
            assert template is not None

    def test_render_prompt_function(self, temp_template_dir):
        """Test global render_prompt function."""
        with patch('src.simbuilder_llm.prompts.get_prompt_loader') as mock_get_loader:
            mock_loader = PromptLoader(temp_template_dir)
            mock_get_loader.return_value = mock_loader

            result = render_prompt("simple", {"name": "Test"})
            assert result == "Hello Test!"

    def test_render_prompt_function_with_validation(self, temp_template_dir):
        """Test global render_prompt function with validation."""
        with patch('src.simbuilder_llm.prompts.get_prompt_loader') as mock_get_loader:
            mock_loader = PromptLoader(temp_template_dir)
            mock_get_loader.return_value = mock_loader

            result = render_prompt("simple", {"name": "Test"}, validate_variables=True)
            assert result == "Hello Test!"

    def test_list_prompts_function(self, temp_template_dir):
        """Test global list_prompts function."""
        with patch('src.simbuilder_llm.prompts.get_prompt_loader') as mock_get_loader:
            mock_loader = PromptLoader(temp_template_dir)
            mock_get_loader.return_value = mock_loader

            templates = list_prompts()
            assert "simple" in templates


class TestPromptRenderError:
    """Tests for PromptRenderError exception."""

    def test_prompt_render_error_basic(self):
        """Test basic PromptRenderError creation."""
        error = PromptRenderError("test_prompt", "Test message")

        assert error.prompt_name == "test_prompt"
        assert error.message == "Test message"
        assert error.missing_variables == []
        assert "Failed to render prompt 'test_prompt': Test message" in str(error)

    def test_prompt_render_error_with_missing_vars(self):
        """Test PromptRenderError with missing variables."""
        missing_vars = ["var1", "var2"]
        error = PromptRenderError("test_prompt", "Missing variables", missing_vars)

        assert error.missing_variables == missing_vars
        error_str = str(error)
        assert "Missing variables: var1, var2" in error_str

    def test_prompt_render_error_str_method(self):
        """Test PromptRenderError __str__ method."""
        error = PromptRenderError("test_prompt", "Test message", ["var1"])

        error_str = str(error)
        assert "Failed to render prompt 'test_prompt': Test message" in error_str
        assert "Missing variables: var1" in error_str


class TestRealPromptFiles:
    """Tests using the actual prompt files in the package."""

    def test_load_base_prompt(self):
        """Test loading the actual base_prompt.liquid file."""
        loader = PromptLoader()

        # This should work with the actual base_prompt.liquid file
        template = loader.load_template("base_prompt")
        assert template is not None

    def test_render_base_prompt(self):
        """Test rendering the actual base_prompt.liquid file."""
        loader = PromptLoader()

        variables = {
            "question": "What is Azure?",
            "context": "Cloud computing platform",
            "additional_instructions": "Be concise"
        }

        result = loader.render_template("base_prompt", variables, validate_variables=False)

        assert "What is Azure?" in result
        assert "Cloud computing platform" in result
        assert "Be concise" in result

    def test_base_prompt_minimal_variables(self):
        """Test base prompt with minimal variables."""
        loader = PromptLoader()

        # Test with just one variable
        variables = {"question": "Hello"}

        result = loader.render_template("base_prompt", variables, validate_variables=False)
        assert "Hello" in result

    def test_list_actual_prompts(self):
        """Test listing actual prompt files."""
        templates = list_prompts()

        # Should include the base_prompt
        assert "base_prompt" in templates
