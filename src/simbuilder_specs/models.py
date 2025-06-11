"""
Pydantic models for SimBuilder Specs Library.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic import Field


class TemplateMeta(BaseModel):
    """Metadata for a Liquid template."""

    name: str = Field(..., description="Template name (filename without extension)")
    path: str = Field(..., description="Relative path in repository")
    description: str | None = Field(None, description="Template description")
    variables: list[str] = Field(default_factory=list, description="Required template variables")
    tags: list[str] = Field(default_factory=list, description="Template tags for categorization")
    version: str | None = Field(None, description="Template version")
    created_at: datetime | None = Field(None, description="Template creation timestamp")
    modified_at: datetime | None = Field(None, description="Last modification timestamp")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class TemplateRenderRequest(BaseModel):
    """Request to render a Liquid template."""

    template_name: str = Field(..., description="Name of template to render")
    context: dict[str, Any] = Field(default_factory=dict, description="Template context variables")
    strict_variables: bool = Field(False, description="Fail on undefined variables")

    class Config:
        """Pydantic configuration."""

        extra = "forbid"


class TemplateRenderResult(BaseModel):
    """Result of rendering a Liquid template."""

    rendered_content: str = Field(..., description="Rendered template content")
    template_name: str = Field(..., description="Name of rendered template")
    context_used: dict[str, Any] = Field(..., description="Context variables used in rendering")
    variables_required: list[str] = Field(
        default_factory=list, description="Variables required by template"
    )
    variables_missing: list[str] = Field(
        default_factory=list, description="Missing required variables"
    )
    render_time_ms: float = Field(..., description="Rendering time in milliseconds")
    success: bool = Field(..., description="Whether rendering was successful")
    error_message: str | None = Field(None, description="Error message if rendering failed")

    class Config:
        """Pydantic configuration."""

        extra = "forbid"


class GitRepositoryInfo(BaseModel):
    """Information about a Git repository."""

    url: str = Field(..., description="Repository URL")
    branch: str = Field("main", description="Current branch")
    commit_hash: str | None = Field(None, description="Current commit hash")
    last_updated: datetime | None = Field(None, description="Last repository update")
    local_path: Path | None = Field(None, description="Local repository path")

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            Path: lambda v: str(v) if v else None,
        }


class ValidationResult(BaseModel):
    """Result of template validation."""

    template_name: str = Field(..., description="Name of validated template")
    is_valid: bool = Field(..., description="Whether template is valid")
    syntax_errors: list[str] = Field(default_factory=list, description="Syntax error messages")
    missing_variables: list[str] = Field(
        default_factory=list, description="Missing required variables"
    )
    warnings: list[str] = Field(default_factory=list, description="Warning messages")
    suggestions: list[str] = Field(default_factory=list, description="Improvement suggestions")

    class Config:
        """Pydantic configuration."""

        extra = "forbid"
