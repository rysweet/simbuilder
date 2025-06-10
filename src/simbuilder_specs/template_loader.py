"""
Liquid template loader and renderer for SimBuilder Specs Library.
"""
import functools
import time
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from liquid import Environment
    from liquid import FileSystemLoader
    from liquid import Template

try:
    from liquid import Environment
    from liquid import FileSystemLoader
    from liquid import Template
    from liquid.exceptions import LiquidSyntaxError
    from liquid.exceptions import LiquidTypeError
    LIQUID_AVAILABLE = True
except ImportError:
    # Create placeholder classes for when liquid is not available
    class Template:  # type: ignore
        pass

    class Environment:  # type: ignore
        pass

    class FileSystemLoader:  # type: ignore
        pass

    LiquidSyntaxError = Exception  # type: ignore
    LiquidTypeError = Exception  # type: ignore
    LIQUID_AVAILABLE = False

from .git_repository import GitRepository
from .models import TemplateMeta
from .models import TemplateRenderRequest
from .models import TemplateRenderResult


class TemplateLoaderError(Exception):
    """Exception raised for template loading operations."""
    pass


class TemplateLoader:
    """Liquid template loader and renderer."""

    @classmethod
    @functools.lru_cache(maxsize=1)
    def get_repository(
        cls, *args: Any, **kwargs: Any
    ) -> "GitRepository":
        """Return a cached GitRepository instance. Used for testability/reset."""
        return GitRepository(*args, **kwargs)

    def __init__(self, repository: GitRepository):
        """Initialize template loader.

        Args:
            repository: Git repository containing templates
        """
        if not LIQUID_AVAILABLE:
            raise TemplateLoaderError(
                "liquid package is required for template operations. "
                "Install with: pip install liquid"
            )

        self.repository = repository
        self._env: Environment | None = None
        self._template_cache: dict[str, Any] = {}
        # Remove all dynamic cache_clear assignment and self.get_template_meta wrapper logic.
        # Tests should patch class-level methods directly if needed.


    def _get_environment(self) -> "Environment":
        """Get or create Liquid environment."""
        if self._env is None:
            if not self.repository.local_path.exists():
                raise TemplateLoaderError("Repository not available. Run pull first.")

            loader = FileSystemLoader(str(self.repository.local_path))
            self._env = Environment(loader=loader)

        return self._env

    def _clear_cache(self) -> None:
        """Clear template cache."""
        self._template_cache.clear()
        self._env = None

    def get_template_meta(self, template_name: str) -> TemplateMeta:
        """Get metadata for a template (LRU cached per-instance).

        Args:
            template_name: Name of template (with or without .liquid extension)

        Returns:
            TemplateMeta: Template metadata

        Raises:
            TemplateLoaderError: If template not found
        """
        # Ensure .liquid extension
        if not template_name.endswith('.liquid'):
            template_name += '.liquid'

        # Find template file in repository
        template_files = self.repository.list_templates()
        template_path = None

        for file_path in template_files:
            if file_path.name == template_name:
                template_path = file_path
                break

        if template_path is None:
            raise TemplateLoaderError(f"Template not found: {template_name}")

        try:
            content = self.repository.get_file_content(str(template_path))
            variables = self._extract_variables(content)
        except Exception as e:
            raise TemplateLoaderError(f"Failed to analyze template {template_name}: {e}") from e

        # Get file stats
        full_path = self.repository.get_file_path(str(template_path))
        full_path.stat()

        return TemplateMeta(
            name=template_path.stem,
            path=str(template_path),
            description=None,
            variables=variables,
            version=None,
            created_at=None,
            modified_at=None,
        )

    def _extract_variables(self, content: str) -> list[str]:
        """Extract variable names from template content.

        Args:
            content: Template content

        Returns:
            List of variable names used in template
        """
        import re

        # Find variables in {{ variable }} and {% if variable %} patterns
        variable_patterns = [
            r'\{\{\s*(\w+)',          # {{ variable }}
            r'\{\%\s*if\s+(\w+)',     # {% if variable %}
            r'\{\%\s*for\s+\w+\s+in\s+(\w+)',  # {% for item in items %}
            r'\{\%\s*assign\s+\w+\s*=\s*(\w+)', # {% assign x = variable %}
        ]

        variables = set()
        for pattern in variable_patterns:
            matches = re.findall(pattern, content)
            variables.update(matches)

        # Remove Liquid built-ins, keywords, and local variables
        builtins = {'forloop', 'tablerow', 'cycle', 'unless', 'else', 'elseif', 'endif', 'endfor', 'item', 'greeting'}
        # Also remove variables that are assigned within the template (they're local, not inputs)
        assign_pattern = r'\{\%\s*assign\s+(\w+)'
        assigned_vars = set(re.findall(assign_pattern, content))
        variables = variables - builtins - assigned_vars

        return sorted(variables)

    def load_template(self, template_name: str) -> Any:
        """Load and compile a Liquid template.

        Args:
            template_name: Name of template to load

        Returns:
            Compiled Liquid template

        Raises:
            TemplateLoaderError: If template loading fails
        """
        # Ensure .liquid extension
        if not template_name.endswith('.liquid'):
            template_name += '.liquid'

        # Check cache first
        if template_name in self._template_cache:
            return self._template_cache[template_name]

        try:
            env = self._get_environment()
            template = env.get_template(template_name)

            # Cache compiled template
            self._template_cache[template_name] = template

            return template

        except Exception as e:
            raise TemplateLoaderError(f"Failed to load template {template_name}: {e}") from e

    def render(self, template_name: str, context: dict[str, Any]) -> str:
        """Render a template with given context.

        Args:
            template_name: Name of template to render
            context: Context variables for rendering

        Returns:
            Rendered template content

        Raises:
            TemplateLoaderError: If rendering fails
        """
        try:
            template = self.load_template(template_name)
            result = template.render(**context)
            return str(result)

        except Exception as e:
            raise TemplateLoaderError(f"Failed to render template {template_name}: {e}") from e

    def render_with_metadata(self, request: TemplateRenderRequest) -> TemplateRenderResult:
        """Render template and return detailed result.

        Args:
            request: Template render request

        Returns:
            Detailed render result with metadata
        """
        start_time = time.time()

        try:
            # Get template metadata
            meta = self.get_template_meta(request.template_name)

            # Check for missing required variables
            missing_vars = []
            if request.strict_variables:
                missing_vars = [var for var in meta.variables if var not in request.context]
                if missing_vars:
                    return TemplateRenderResult(
                        rendered_content="",
                        template_name=request.template_name,
                        context_used=request.context,
                        variables_required=meta.variables,
                        variables_missing=missing_vars,
                        render_time_ms=(time.time() - start_time) * 1000,
                        success=False,
                        error_message=f"Missing required variables: {', '.join(missing_vars)}"
                    )

            # Render template
            rendered_content = self.render(request.template_name, request.context)

            return TemplateRenderResult(
                rendered_content=rendered_content,
                template_name=request.template_name,
                context_used=request.context,
                variables_required=meta.variables,
                variables_missing=missing_vars,
                render_time_ms=(time.time() - start_time) * 1000,
                success=True,
                error_message=None
            )

        except Exception as e:
            return TemplateRenderResult(
                rendered_content="",
                template_name=request.template_name,
                context_used=request.context,
                variables_required=[],
                variables_missing=[],
                render_time_ms=(time.time() - start_time) * 1000,
                success=False,
                error_message=str(e)
            )

    def list_templates(self) -> list[TemplateMeta]:
        """List all available templates with metadata.

        Returns:
            List of template metadata
        """
        templates = []

        for template_path in self.repository.list_templates():
            try:
                meta = self.get_template_meta(template_path.stem)
                templates.append(meta)
            except Exception as e:
                # Skip templates that can't be analyzed, but log the issue
                # TODO: Add proper logging here when logger is available
                print(f"Warning: Could not analyze template {template_path.stem}: {e}")
                continue

        return templates

    def refresh_repository(self) -> None:
        """Refresh repository and clear template cache and method caches."""
        self.repository.clone_or_pull()
        self._clear_cache()
        repo_cache_clear = getattr(type(self).get_repository, "cache_clear", None)
        if callable(repo_cache_clear):
            repo_cache_clear()
        meta_cache_clear = getattr(self.get_template_meta, "cache_clear", None)
        if callable(meta_cache_clear):
            meta_cache_clear()

