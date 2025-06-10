"""
Git repository management for SimBuilder Specs Library.
"""

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from .models import GitRepositoryInfo


class GitRepositoryError(Exception):
    """Exception raised for Git repository operations."""
    pass


class GitRepository:
    """Git repository manager for template storage."""

    def __init__(self, repo_url: str, branch: str = "main", local_path: Path | None = None):
        """Initialize Git repository manager.

        Args:
            repo_url: Git repository URL
            branch: Branch to use (default: None)
            local_path: Local path for repository (default: temp directory)
        """
        self.repo_url = repo_url
        self.branch = branch
        if self.branch is None or self.branch == "":
            self.branch = "main"
        if local_path:
            self.local_path = local_path
        else:
            cache_dir = Path.home() / ".cache" / "simbuilder" / "specs"
            self.local_path = cache_dir
        self._auth_token = os.getenv("SPEC_REPO_TOKEN")

    def clone_or_pull(self) -> GitRepositoryInfo:
        """Clone repository if it doesn't exist, otherwise pull latest changes.

        Returns:
            GitRepositoryInfo: Repository information after operation

        Raises:
            GitRepositoryError: If Git operations fail
        """
        try:
            if self.local_path.exists() and (self.local_path / ".git").exists():
                return self._pull()
            else:
                return self._clone()
        except GitRepositoryError:
            raise
        except subprocess.CalledProcessError as e:
            raise GitRepositoryError(f"Git operation failed: {e}") from e
        except FileNotFoundError as e:
            raise GitRepositoryError(f"Git not found: {e}") from e
        except Exception as e:
            raise GitRepositoryError(f"Unexpected git error: {e}") from e

    def _clone(self) -> GitRepositoryInfo:
        """Clone the repository."""
        if self.local_path.exists():
            shutil.rmtree(self.local_path)

        self.local_path.parent.mkdir(parents=True, exist_ok=True)

        clone_url = self._get_authenticated_url()
        cmd = ["git", "clone", clone_url, str(self.local_path)]
        # For cloning, cwd must be None, not non-existing local_path
        try:
            subprocess.run(
                cmd,
                cwd=None,
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            raise GitRepositoryError(f"Git clone failed: {e.stderr or e}") from e
        except FileNotFoundError as e:
            raise GitRepositoryError(f"Git not found: {e}") from e
        except Exception as e:
            raise GitRepositoryError(f"Unexpected git clone error: {e}") from e

        # Optional: Checkout the branch if specified (now local_path exists)
        if self.branch:
            try:
                self._run_git_command(["checkout", self.branch])
            except GitRepositoryError:
                raise
            except subprocess.CalledProcessError as e:
                raise GitRepositoryError(f"Branch checkout failed: {e.stderr or e}") from e
            except FileNotFoundError as e:
                raise GitRepositoryError(f"Git not found: {e}") from e

        return self._get_repo_info()

    def _pull(self) -> GitRepositoryInfo:
        """Pull latest changes from repository."""
        try:
            # Ensure we're on the correct branch
            # Only call checkout if branch is specified
            if self.branch:
                self._run_git_command(["checkout", self.branch])

            # Pull latest changes (default to current branch if branch not specified)
            if self.branch:
                self._run_git_command(["pull", "origin", self.branch])
            else:
                self._run_git_command(["pull"])

            return self._get_repo_info()
        except GitRepositoryError:
            raise
        except subprocess.CalledProcessError as e:
            raise GitRepositoryError(f"Git pull failed: {e.stderr or e}") from e
        except FileNotFoundError as e:
            raise GitRepositoryError(f"Git not found: {e}") from e
        except Exception as e:
            raise GitRepositoryError(f"Unexpected git pull error: {e}") from e

    def _run_git_command(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        """Run a git command in the repository directory and wrap failures."""
        cmd = ["git"] + args
        try:
            return subprocess.run(
                cmd,
                cwd=self.local_path,
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            raise GitRepositoryError(f"Git command failed: {' '.join(cmd)}\n{e.stderr or e}") from e
        except FileNotFoundError as e:
            raise GitRepositoryError(f"Git not found: {e}") from e
        except Exception as e:
            raise GitRepositoryError(f"Unexpected git command error: {e}") from e

    def _get_authenticated_url(self) -> str:
        """Get repository URL with authentication token if available."""
        if not self._auth_token:
            return self.repo_url

        # Handle GitHub URLs with token
        if "github.com" in self.repo_url and self.repo_url.startswith("https://"):
            return self.repo_url.replace(
                "https://github.com/",
                f"https://{self._auth_token}@github.com/"
            )

        return self.repo_url

    def _get_repo_info(self) -> GitRepositoryInfo:
        """Get current repository information."""
        try:
            # Get current commit hash
            result = self._run_git_command(["rev-parse", "HEAD"])
            commit_hash = result.stdout.strip()

            return GitRepositoryInfo(
                url=self.repo_url,
                branch=self.branch,
                commit_hash=commit_hash,
                last_updated=datetime.now(),
                local_path=self.local_path
            )
        except subprocess.CalledProcessError as e:
            raise GitRepositoryError(f"Failed to get repository info: {e}") from e

    def get_file_path(self, relative_path: str) -> Path:
        """Get absolute path to a file in the repository.

        Args:
            relative_path: Relative path from repository root

        Returns:
            Path: Absolute path to file
        """
        return self.local_path / relative_path

    def list_templates(self, extension: str = ".liquid") -> list[Path]:
        """List all template files in the repository.

        Args:
            extension: File extension to filter (default: .liquid)

        Returns:
            List of template file paths relative to repository root
        """
        if not self.local_path.exists():
            return []

        template_files = []
        for file_path in self.local_path.rglob(f"*{extension}"):
            if file_path.is_file():
                # Get path relative to repository root
                relative_path = file_path.relative_to(self.local_path)
                template_files.append(relative_path)

        return sorted(template_files)

    def file_exists(self, relative_path: str) -> bool:
        """Check if a file exists in the repository.

        Args:
            relative_path: Relative path from repository root

        Returns:
            True if file exists, False otherwise
        """
        file_path = self.get_file_path(relative_path)
        return file_path.exists() and file_path.is_file()

    def get_file_content(self, relative_path: str) -> str:
        """Get content of a file in the repository.

        Args:
            relative_path: Relative path from repository root

        Returns:
            File content as string

        Raises:
            GitRepositoryError: If file doesn't exist or can't be read
        """
        file_path = self.get_file_path(relative_path)

        if not file_path.exists():
            raise GitRepositoryError(f"File not found: {relative_path}")

        try:
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            raise GitRepositoryError(f"Failed to read file {relative_path}: {e}") from e
