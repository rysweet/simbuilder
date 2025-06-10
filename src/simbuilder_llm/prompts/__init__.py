"""
Prompt loading and rendering system for SimBuilder LLM integration.

This module provides functionality to load and render Jinja2/Liquid templates
for LLM prompts with variable validation and caching.
"""

import functools
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from liquid import Environment
from liquid import FileSystemLoader
from liquid import Template
from liquid.exceptions import LiquidSyntaxError
from liquid.exceptions import TemplateNotFound

from ..exceptions import PromptRenderError

logger = logging.getLogger(__name__)


class PromptLoader:
    """Loads and renders Liquid/Jinja2 prompt templates."""

    def __init__(self, template_dir: Path | None = None) -> None:
        """Initialize the prompt loader.

        Args:
            template_dir: Directory containing prompt templates (defaults to prompts/ in this package)
        """
        if template_dir is None:
            template_dir = Path(__file__).parent

        self.template_dir = template_dir
        self._env = Environment(loader=FileSystemLoader(str(template_dir)))

    def load_template(self, name: str) -> Any:
        """Load a template by name with caching.

        Args:
            name: Template name (with or without extension)

        Returns:
            Loaded template

        Raises:
            PromptRenderError: If template cannot be found or loaded
        """
        # Try different extensions if no extension provided
        extensions = [".liquid", ".jinja", ".j2"] if "." not in name else [""]

        for ext in extensions:
            template_name = name + ext if ext else name
            try:
                logger.debug(f"Loading template: {template_name}")
                return self._env.get_template(template_name)
            except TemplateNotFound:
                continue
            except LiquidSyntaxError as e:
                raise PromptRenderError(name, f"Template has syntax errors: {str(e)}") from e
            except Exception as e:
                raise PromptRenderError(name, f"Failed to load template: {str(e)}") from e

        raise PromptRenderError(name, f"Template not found in {self.template_dir}")

    def extract_variables(self, template_name: str) -> set[str]:
        """Extract variable names from a template.

        Args:
            template_name: Name of the template

        Returns:
            Set of variable names used in the template
        """
        try:
            self.load_template(template_name)

            # Get the raw template source and extract variables using regex
            # Read the template file directly since liquid template parsing is complex
            template_path = None
            for ext in [".liquid", ".jinja", ".j2"]:
                candidate = self.template_dir / f"{template_name}{ext}"
                if candidate.exists():
                    template_path = candidate
                    break

            if template_path and template_path.exists():
                template_source = template_path.read_text()
                # Extract variables using regex (simple approach)
                # Matches {{ variable }} and {{ variable.property }}
                variable_pattern = r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)"
                matches = re.findall(variable_pattern, template_source)
                return set(matches)

            return set()

        except Exception as e:
            logger.warning(f"Could not extract variables from {template_name}: {e}")
            return set()

    def render_template(
        self,
        template_name: str,
        variables: dict[str, Any],
        validate_variables: bool = True,
    ) -> str:
        """Render a template with the provided variables.

        Args:
            template_name: Name of the template to render
            variables: Variables to use in rendering
            validate_variables: Whether to validate required variables

        Returns:
            Rendered template content

        Raises:
            PromptRenderError: If rendering fails or variables are missing
        """
        try:
            template = self.load_template(template_name)

            if validate_variables:
                required_vars = self.extract_variables(template_name)
                missing_vars = required_vars - set(variables.keys())

                if missing_vars:
                    raise PromptRenderError(
                        template_name, "Missing required variables", list(missing_vars)
                    )

            logger.debug(
                f"Rendering template {template_name} with variables: {list(variables.keys())}"
            )

            result = template.render(**variables)
            return str(result)

        except PromptRenderError:
            raise
        except Exception as e:
            raise PromptRenderError(template_name, f"Failed to render template: {str(e)}") from e

    def list_templates(self) -> list[str]:
        """List all available templates.

        Returns:
            List of template names
        """
        templates = []
        for file_path in self.template_dir.glob("*.liquid"):
            templates.append(file_path.stem)
        for file_path in self.template_dir.glob("*.jinja"):
            templates.append(file_path.stem)
        for file_path in self.template_dir.glob("*.j2"):
            templates.append(file_path.stem)

        return sorted(set(templates))


# Global prompt loader instance
_prompt_loader: PromptLoader | None = None


def get_prompt_loader() -> PromptLoader:
    """Get the global prompt loader instance."""
    global _prompt_loader
    if _prompt_loader is None:
        _prompt_loader = PromptLoader()
    return _prompt_loader


def load_prompt(name: str) -> Any:
    """Load a prompt template by name.

    Args:
        name: Template name

    Returns:
        Loaded template
    """
    return get_prompt_loader().load_template(name)


def render_prompt(name: str, variables: dict[str, Any], validate_variables: bool = True) -> str:
    """Render a prompt template with variables.

    Args:
        name: Template name
        variables: Variables for rendering
        validate_variables: Whether to validate required variables

    Returns:
        Rendered prompt content
    """
    return get_prompt_loader().render_template(name, variables, validate_variables)


def list_prompts() -> list[str]:
    """List all available prompt templates.

    Returns:
        List of template names
    """
    return get_prompt_loader().list_templates()
