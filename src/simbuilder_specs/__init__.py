"""
SimBuilder Specs Library - External Liquid prompt template management.

This package provides Git-based storage and management of Liquid prompt templates
used by all agents in the SimBuilder system.
"""

from .git_repository import GitRepository
from .models import GitRepositoryInfo
from .models import TemplateMeta
from .models import TemplateRenderRequest
from .models import TemplateRenderResult
from .models import ValidationResult
from .spec_validator import SpecValidator
from .spec_validator import validate_repo
from .template_loader import TemplateLoader

__all__ = [
    "TemplateMeta",
    "TemplateRenderRequest",
    "TemplateRenderResult",
    "GitRepositoryInfo",
    "ValidationResult",
    "TemplateLoader",
    "GitRepository",
    "SpecValidator",
    "validate_repo",
]
