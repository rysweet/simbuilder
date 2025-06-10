"""
Tests for SimBuilder Specs models.
"""

import json
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.simbuilder_specs.models import GitRepositoryInfo
from src.simbuilder_specs.models import TemplateMeta
from src.simbuilder_specs.models import TemplateRenderRequest
from src.simbuilder_specs.models import TemplateRenderResult
from src.simbuilder_specs.models import ValidationResult


class TestTemplateMeta:
    """Test TemplateMeta model."""

    def test_minimal_template_meta(self):
        """Test TemplateMeta with minimal required fields."""
        meta = TemplateMeta(
            name="test_template",
            path="templates/test_template.liquid"
        )

        assert meta.name == "test_template"
        assert meta.path == "templates/test_template.liquid"
        assert meta.description is None
        assert meta.variables == []
        assert meta.tags == []
        assert meta.version is None
        assert meta.created_at is None
        assert meta.modified_at is None

    def test_full_template_meta(self):
        """Test TemplateMeta with all fields."""
        created = datetime.now()
        modified = datetime.now()

        meta = TemplateMeta(
            name="full_template",
            path="templates/full_template.liquid",
            description="A complete template",
            variables=["name", "age"],
            tags=["user", "profile"],
            version="1.0.0",
            created_at=created,
            modified_at=modified
        )

        assert meta.name == "full_template"
        assert meta.path == "templates/full_template.liquid"
        assert meta.description == "A complete template"
        assert meta.variables == ["name", "age"]
        assert meta.tags == ["user", "profile"]
        assert meta.version == "1.0.0"
        assert meta.created_at == created
        assert meta.modified_at == modified

    def test_template_meta_json_serialization(self):
        """Test TemplateMeta JSON serialization with datetime fields."""
        created = datetime(2024, 1, 1, 12, 0, 0)

        meta = TemplateMeta(
            name="json_template",
            path="templates/json_template.liquid",
            created_at=created
        )

        json_data = json.loads(meta.model_dump_json())
        assert json_data["created_at"] == "2024-01-01T12:00:00"


class TestTemplateRenderRequest:
    """Test TemplateRenderRequest model."""

    def test_minimal_render_request(self):
        """Test TemplateRenderRequest with minimal fields."""
        request = TemplateRenderRequest(template_name="test_template")

        assert request.template_name == "test_template"
        assert request.context == {}
        assert request.strict_variables is False

    def test_full_render_request(self):
        """Test TemplateRenderRequest with all fields."""
        request = TemplateRenderRequest(
            template_name="full_template",
            context={"name": "John", "age": 30},
            strict_variables=True
        )

        assert request.template_name == "full_template"
        assert request.context == {"name": "John", "age": 30}
        assert request.strict_variables is True

    def test_render_request_forbids_extra_fields(self):
        """Test that TemplateRenderRequest forbids extra fields."""
        with pytest.raises(ValidationError) as exc_info:
            TemplateRenderRequest(
                template_name="test",
                context={},
                extra_field="not_allowed"
            )

        error = exc_info.value.errors()[0]
        assert error["type"] == "extra_forbidden"


class TestTemplateRenderResult:
    """Test TemplateRenderResult model."""

    def test_successful_render_result(self):
        """Test TemplateRenderResult for successful rendering."""
        result = TemplateRenderResult(
            rendered_content="Hello John!",
            template_name="greeting",
            context_used={"name": "John"},
            variables_required=["name"],
            variables_missing=[],
            render_time_ms=25.5,
            success=True,
            error_message=None
        )

        assert result.rendered_content == "Hello John!"
        assert result.template_name == "greeting"
        assert result.context_used == {"name": "John"}
        assert result.variables_required == ["name"]
        assert result.variables_missing == []
        assert result.render_time_ms == 25.5
        assert result.success is True
        assert result.error_message is None

    def test_failed_render_result(self):
        """Test TemplateRenderResult for failed rendering."""
        result = TemplateRenderResult(
            rendered_content="",
            template_name="broken_template",
            context_used={},
            variables_required=["name"],
            variables_missing=["name"],
            render_time_ms=5.0,
            success=False,
            error_message="Missing required variable: name"
        )

        assert result.rendered_content == ""
        assert result.template_name == "broken_template"
        assert result.context_used == {}
        assert result.variables_required == ["name"]
        assert result.variables_missing == ["name"]
        assert result.render_time_ms == 5.0
        assert result.success is False
        assert result.error_message == "Missing required variable: name"

    def test_render_result_forbids_extra_fields(self):
        """Test that TemplateRenderResult forbids extra fields."""
        with pytest.raises(ValidationError) as exc_info:
            TemplateRenderResult(
                rendered_content="test",
                template_name="test",
                context_used={},
                render_time_ms=1.0,
                success=True,
                extra_field="not_allowed"
            )

        error = exc_info.value.errors()[0]
        assert error["type"] == "extra_forbidden"


class TestGitRepositoryInfo:
    """Test GitRepositoryInfo model."""

    def test_minimal_repository_info(self):
        """Test GitRepositoryInfo with minimal fields."""
        info = GitRepositoryInfo(url="https://github.com/test/repo.git")

        assert info.url == "https://github.com/test/repo.git"
        assert info.branch == "main"
        assert info.commit_hash is None
        assert info.last_updated is None
        assert info.local_path is None

    def test_full_repository_info(self):
        """Test GitRepositoryInfo with all fields."""
        updated = datetime.now()
        local_path = Path("/tmp/repo")

        info = GitRepositoryInfo(
            url="https://github.com/test/repo.git",
            branch="develop",
            commit_hash="abc123",
            last_updated=updated,
            local_path=local_path
        )

        assert info.url == "https://github.com/test/repo.git"
        assert info.branch == "develop"
        assert info.commit_hash == "abc123"
        assert info.last_updated == updated
        assert info.local_path == local_path

    def test_repository_info_json_serialization(self):
        """Test GitRepositoryInfo JSON serialization with Path and datetime."""
        updated = datetime(2024, 1, 1, 12, 0, 0)
        local_path = Path("/tmp/repo")

        info = GitRepositoryInfo(
            url="https://github.com/test/repo.git",
            last_updated=updated,
            local_path=local_path
        )

        json_data = json.loads(info.model_dump_json())
        assert json_data["last_updated"] == "2024-01-01T12:00:00"
        assert json_data["local_path"] == "/tmp/repo"


class TestValidationResult:
    """Test ValidationResult model."""

    def test_valid_template_result(self):
        """Test ValidationResult for valid template."""
        result = ValidationResult(
            template_name="valid_template",
            is_valid=True,
            syntax_errors=[],
            missing_variables=[],
            warnings=[],
            suggestions=[]
        )

        assert result.template_name == "valid_template"
        assert result.is_valid is True
        assert result.syntax_errors == []
        assert result.missing_variables == []
        assert result.warnings == []
        assert result.suggestions == []

    def test_invalid_template_result(self):
        """Test ValidationResult for invalid template."""
        result = ValidationResult(
            template_name="invalid_template",
            is_valid=False,
            syntax_errors=["Syntax error on line 1"],
            missing_variables=["name", "age"],
            warnings=["Unused variable: email"],
            suggestions=["Consider adding error handling"]
        )

        assert result.template_name == "invalid_template"
        assert result.is_valid is False
        assert result.syntax_errors == ["Syntax error on line 1"]
        assert result.missing_variables == ["name", "age"]
        assert result.warnings == ["Unused variable: email"]
        assert result.suggestions == ["Consider adding error handling"]

    def test_validation_result_forbids_extra_fields(self):
        """Test that ValidationResult forbids extra fields."""
        with pytest.raises(ValidationError) as exc_info:
            ValidationResult(
                template_name="test",
                is_valid=True,
                extra_field="not_allowed"
            )

        error = exc_info.value.errors()[0]
        assert error["type"] == "extra_forbidden"
