"""
Tests for GitRepository class.
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from src.simbuilder_specs.git_repository import GitRepository
from src.simbuilder_specs.git_repository import GitRepositoryError


@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir) / "test_repo"
        repo_path.mkdir()

        # Initialize git repo
        subprocess.run(["git", "init", "--initial-branch=main"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)

        # Create some test template files
        templates_dir = repo_path / "templates"
        templates_dir.mkdir()

        # Simple template
        simple_template = templates_dir / "simple.liquid"
        simple_template.write_text("Hello {{ name }}!")

        # Complex template
        complex_template = templates_dir / "complex.liquid"
        complex_template.write_text("""
{% assign greeting = "Hello" %}
{% if user %}
{{ greeting }} {{ user.name }}!
Your email is: {{ user.email }}
{% else %}
{{ greeting }} Anonymous!
{% endif %}
""".strip())

        # Add and commit files
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)

        yield str(repo_path)


@pytest.fixture
def temp_local_path():
    """Provide a temporary path for local repository clones."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir) / "local_repo"


class TestGitRepository:
    """Test GitRepository functionality."""

    def test_init_default_values(self):
        """Test GitRepository initialization with default values."""
        repo = GitRepository("https://github.com/test/repo.git")

        assert repo.repo_url == "https://github.com/test/repo.git"
        assert repo.branch == "main"
        assert "simbuilder" in str(repo.local_path)
        assert "specs" in str(repo.local_path)

    def test_init_custom_values(self, temp_local_path):
        """Test GitRepository initialization with custom values."""
        repo = GitRepository(
            "https://github.com/test/repo.git",
            branch="develop",
            local_path=temp_local_path
        )

        assert repo.repo_url == "https://github.com/test/repo.git"
        assert repo.branch == "develop"
        assert repo.local_path == temp_local_path

    def test_clone_repository(self, temp_git_repo, temp_local_path):
        """Test cloning a repository."""
        repo = GitRepository(f"file://{temp_git_repo}", local_path=temp_local_path)

        repo_info = repo.clone_or_pull()

        assert temp_local_path.exists()
        assert (temp_local_path / ".git").exists()
        assert repo_info.url == f"file://{temp_git_repo}"
        assert repo_info.branch == "main"
        assert repo_info.commit_hash is not None
        assert repo_info.last_updated is not None
        assert repo_info.local_path == temp_local_path

    def test_pull_existing_repository(self, temp_git_repo, temp_local_path):
        """Test pulling changes to an existing repository."""
        repo = GitRepository(f"file://{temp_git_repo}", local_path=temp_local_path)

        # First clone
        repo.clone_or_pull()

        # Add new file to original repo
        new_file = Path(temp_git_repo) / "new_template.liquid"
        new_file.write_text("New {{ content }}!")
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, check=True)
        subprocess.run(["git", "commit", "-m", "Add new template"], cwd=temp_git_repo, check=True)

        # Pull changes
        repo_info = repo.clone_or_pull()

        assert (temp_local_path / "new_template.liquid").exists()
        assert repo_info.url == f"file://{temp_git_repo}"

    def test_clone_nonexistent_repository(self, temp_local_path):
        """Test cloning a nonexistent repository raises error."""
        repo = GitRepository("https://github.com/nonexistent/repo.git", local_path=temp_local_path)

        with pytest.raises(GitRepositoryError):
            repo.clone_or_pull()

    def test_get_file_path(self, temp_git_repo, temp_local_path):
        """Test getting absolute file path."""
        repo = GitRepository(f"file://{temp_git_repo}", local_path=temp_local_path)
        repo.clone_or_pull()

        file_path = repo.get_file_path("templates/simple.liquid")
        expected_path = temp_local_path / "templates" / "simple.liquid"

        assert file_path == expected_path

    def test_list_templates(self, temp_git_repo, temp_local_path):
        """Test listing template files."""
        repo = GitRepository(f"file://{temp_git_repo}", local_path=temp_local_path)
        repo.clone_or_pull()

        templates = repo.list_templates()

        assert len(templates) == 2
        template_names = [t.name for t in templates]
        assert "simple.liquid" in template_names
        assert "complex.liquid" in template_names

    def test_list_templates_empty_repo(self, temp_local_path):
        """Test listing templates when repository doesn't exist."""
        repo = GitRepository("https://github.com/test/repo.git", local_path=temp_local_path)

        templates = repo.list_templates()

        assert templates == []

    def test_file_exists(self, temp_git_repo, temp_local_path):
        """Test checking if file exists."""
        repo = GitRepository(f"file://{temp_git_repo}", local_path=temp_local_path)
        repo.clone_or_pull()

        assert repo.file_exists("templates/simple.liquid")
        assert repo.file_exists("templates/complex.liquid")
        assert not repo.file_exists("templates/nonexistent.liquid")
        assert not repo.file_exists("nonexistent.txt")

    def test_get_file_content(self, temp_git_repo, temp_local_path):
        """Test getting file content."""
        repo = GitRepository(f"file://{temp_git_repo}", local_path=temp_local_path)
        repo.clone_or_pull()

        content = repo.get_file_content("templates/simple.liquid")
        assert content == "Hello {{ name }}!"

    def test_get_file_content_nonexistent(self, temp_git_repo, temp_local_path):
        """Test getting content of nonexistent file raises error."""
        repo = GitRepository(f"file://{temp_git_repo}", local_path=temp_local_path)
        repo.clone_or_pull()

        with pytest.raises(GitRepositoryError, match="File not found"):
            repo.get_file_content("nonexistent.liquid")

    def test_authenticated_url_with_token(self, temp_local_path):
        """Test authenticated URL generation with token."""
        os.environ["SPEC_REPO_TOKEN"] = "test_token"
        try:
            repo = GitRepository("https://github.com/test/repo.git", local_path=temp_local_path)
            auth_url = repo._get_authenticated_url()

            assert auth_url == "https://test_token@github.com/test/repo.git"
        finally:
            del os.environ["SPEC_REPO_TOKEN"]

    def test_authenticated_url_without_token(self, temp_local_path):
        """Test authenticated URL generation without token."""
        repo = GitRepository("https://github.com/test/repo.git", local_path=temp_local_path)
        auth_url = repo._get_authenticated_url()

        assert auth_url == "https://github.com/test/repo.git"

    def test_authenticated_url_non_github(self, temp_local_path):
        """Test authenticated URL with non-GitHub URL."""
        os.environ["SPEC_REPO_TOKEN"] = "test_token"
        try:
            repo = GitRepository("https://gitlab.com/test/repo.git", local_path=temp_local_path)
            auth_url = repo._get_authenticated_url()

            # Should return original URL for non-GitHub URLs
            assert auth_url == "https://gitlab.com/test/repo.git"
        finally:
            del os.environ["SPEC_REPO_TOKEN"]

    def test_cache_directory_creation(self):
        """Test that cache directory is created in user home."""
        repo = GitRepository("https://github.com/test/repo.git")

        # Should use ~/.cache/simbuilder/specs
        expected_cache = Path.home() / ".cache" / "simbuilder" / "specs"
        assert repo.local_path == expected_cache

    def test_list_templates_with_custom_extension(self, temp_git_repo, temp_local_path):
        """Test listing templates with custom extension."""
        repo = GitRepository(f"file://{temp_git_repo}", local_path=temp_local_path)
        repo.clone_or_pull()

        # Create a file with different extension
        txt_file = temp_local_path / "test.txt"
        txt_file.write_text("test content")

        # List .txt files
        txt_files = repo.list_templates(extension=".txt")
        assert len(txt_files) == 1
        assert txt_files[0].name == "test.txt"

    def test_repository_info_properties(self, temp_git_repo, temp_local_path):
        """Test that repository info contains all expected properties."""
        repo = GitRepository(f"file://{temp_git_repo}", local_path=temp_local_path)
        repo_info = repo.clone_or_pull()

        # Verify all properties are set
        assert hasattr(repo_info, 'url')
        assert hasattr(repo_info, 'branch')
        assert hasattr(repo_info, 'commit_hash')
        assert hasattr(repo_info, 'last_updated')
        assert hasattr(repo_info, 'local_path')

        # Verify values
        assert repo_info.url == f"file://{temp_git_repo}"
        assert repo_info.branch == "main"
        assert len(repo_info.commit_hash) == 40  # Git SHA-1 hash length
        assert repo_info.local_path == temp_local_path

    def test_git_command_error_handling(self, temp_local_path):
        """Test error handling for git command failures."""
        repo = GitRepository("https://github.com/test/repo.git", local_path=temp_local_path)

        # Create a fake git repo directory without proper git structure
        temp_local_path.mkdir(parents=True)
        (temp_local_path / ".git").mkdir()

        with pytest.raises(GitRepositoryError):
            repo._run_git_command(["status"])
