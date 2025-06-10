"""
Spec validator for Liquid templates in SimBuilder Specs Library.
"""

from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from liquid import Environment
    from liquid import Template

try:
    from liquid import Environment
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

    LiquidSyntaxError = Exception  # type: ignore
    LiquidTypeError = Exception  # type: ignore
    LIQUID_AVAILABLE = False

from .models import ValidationResult
from .template_loader import TemplateLoader


class SpecValidator:
    """Validator for Liquid template specifications."""

    def __init__(self, template_loader: TemplateLoader):
        """Initialize spec validator.

        Args:
            template_loader: Template loader instance
        """
        if not LIQUID_AVAILABLE:
            raise ValueError(
                "liquid package is required for template validation. "
                "Install with: pip install liquid"
            )

        self.template_loader = template_loader

    def validate_template(
        self, template_name: str, context: dict[str, Any] | None = None
    ) -> ValidationResult:
        """Validate a Liquid template.

        Args:
            template_name: Name of template to validate
            context: Optional context for validation testing

        Returns:
            ValidationResult: Detailed validation results
        """
        if context is None:
            context = {}

        syntax_errors = []
        missing_variables = []
        warnings = []
        suggestions = []

        try:
            # Check if template exists and get metadata
            meta = self.template_loader.get_template_meta(template_name)

            # Try to load template (checks syntax)
            try:
                self.template_loader.load_template(template_name)
            except Exception as e:
                if "syntax" in str(e).lower() or "parse" in str(e).lower():
                    syntax_errors.append(f"Syntax error: {str(e)}")
                else:
                    syntax_errors.append(f"Template loading error: {str(e)}")

            # Check for missing variables in context
            if meta.variables:
                missing_variables = [var for var in meta.variables if var not in context]

                if missing_variables:
                    warnings.append(
                        f"Variables not provided in context: {', '.join(missing_variables)}"
                    )

                # Generate suggestions for common variable names
                suggestions.extend(self._generate_variable_suggestions(missing_variables))

            # Try test rendering if we have a template and context
            if not syntax_errors and context:
                try:
                    self.template_loader.render(template_name, context)
                except Exception as e:
                    if "undefined" in str(e).lower():
                        warnings.append(f"Rendering warning: {str(e)}")
                    else:
                        syntax_errors.append(f"Rendering error: {str(e)}")

            # Check template structure and provide suggestions
            if not syntax_errors:
                content = self.template_loader.repository.get_file_content(meta.path)
                suggestions.extend(self._analyze_template_structure(content))

        except Exception as e:
            syntax_errors.append(f"Validation failed: {str(e)}")

        is_valid = len(syntax_errors) == 0

        return ValidationResult(
            template_name=template_name,
            is_valid=is_valid,
            syntax_errors=syntax_errors,
            missing_variables=missing_variables,
            warnings=warnings,
            suggestions=suggestions,
        )

    def validate_all_templates(
        self, context: dict[str, Any] | None = None
    ) -> list[ValidationResult]:
        """Validate all templates in the repository.

        Args:
            context: Optional context for validation testing

        Returns:
            List of validation results for all templates
        """
        results = []

        try:
            templates = self.template_loader.list_templates()

            for template_meta in templates:
                result = self.validate_template(template_meta.name, context)
                results.append(result)

        except Exception as e:
            # Return a single error result if we can't list templates
            results.append(
                ValidationResult(
                    template_name="<unknown>",
                    is_valid=False,
                    syntax_errors=[f"Failed to list templates: {str(e)}"],
                    missing_variables=[],
                    warnings=[],
                    suggestions=[],
                )
            )

        return results

    def _generate_variable_suggestions(self, missing_variables: list[str]) -> list[str]:
        """Generate suggestions for missing variables.

        Args:
            missing_variables: List of missing variable names

        Returns:
            List of suggestion strings
        """
        suggestions = []

        # Common variable name patterns
        common_patterns = {
            "user": ["username", "user_id", "user_name"],
            "tenant": ["tenant_id", "tenant_name"],
            "resource": ["resource_id", "resource_name"],
            "config": ["configuration", "settings"],
            "env": ["environment", "env_name"],
        }

        for var in missing_variables:
            var_lower = var.lower()
            for pattern, alternatives in common_patterns.items():
                if pattern in var_lower:
                    suggestions.append(f"For '{var}', consider using: {', '.join(alternatives)}")
                    break

        return suggestions

    def _analyze_template_structure(self, content: str) -> list[str]:
        """Analyze template structure and provide improvement suggestions.

        Args:
            content: Template content

        Returns:
            List of suggestion strings
        """
        suggestions = []

        # Check for common best practices
        if not content.strip():
            suggestions.append("Template is empty. Consider adding content.")
            return suggestions

        # Check for comments
        if "{%" in content and not ("comment" in content or "#" in content):
            suggestions.append("Consider adding comments to explain complex logic.")

        # Check for error handling
        if "{% if" in content and "else" not in content:
            suggestions.append("Consider adding else conditions for better error handling.")

        # Check for whitespace control
        if "{%-" not in content and "-%}" not in content and "\n\n" in content:
            suggestions.append("Consider using whitespace control ({%- -%}) for cleaner output.")

        # Check for security
        if "| raw" in content:
            suggestions.append("Be cautious with 'raw' filter as it bypasses HTML escaping.")

        return suggestions

    def get_validation_summary(self, results: list[ValidationResult]) -> dict[str, Any]:
        """Get summary statistics from validation results.

        Args:
            results: List of validation results

        Returns:
            Summary statistics dictionary
        """
        total = len(results)
        valid = sum(1 for r in results if r.is_valid)
        invalid = total - valid

        total_errors = sum(len(r.syntax_errors) for r in results)
        total_warnings = sum(len(r.warnings) for r in results)

        return {
            "total_templates": total,
            "valid_templates": valid,
            "invalid_templates": invalid,
            "success_rate": (valid / total * 100) if total > 0 else 0,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "templates_with_missing_vars": sum(1 for r in results if r.missing_variables),
        }


def validate_repo(
    repo_url: str, branch: str = "main", context: dict[str, Any] | None = None
) -> list[ValidationResult]:
    """Validate all templates in a repository.

    Exported convenience function for repository validation.

    Args:
        repo_url: Git repository URL
        branch: Branch to validate (default: main)
        context: Optional context for validation testing

    Returns:
        List of validation results for all templates

    Raises:
        ValueError: If liquid package is not available
        Exception: If repository operations fail
    """
    from .git_repository import GitRepository
    from .template_loader import TemplateLoader

    if not LIQUID_AVAILABLE:
        raise ValueError(
            "liquid package is required for template validation. Install with: pip install liquid"
        )

    # Create repository and template loader
    repo = GitRepository(repo_url, branch)
    repo.clone_or_pull()

    loader = TemplateLoader(repo)
    validator = SpecValidator(loader)

    return validator.validate_all_templates(context)
