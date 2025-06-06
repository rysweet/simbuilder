"""
SimBuilder Scaffolding Package

Provides foundational utilities, configuration management, and common infrastructure
for all SimBuilder components.
"""

__version__ = "0.1.0"
__author__ = "SimBuilder Team"

from .config import Settings
from .config import get_settings
from .exceptions import ConfigurationError
from .exceptions import DependencyError
from .logging import setup_logging

__all__ = [
    "Settings",
    "get_settings",
    "ConfigurationError",
    "DependencyError",
    "setup_logging",
    "__version__",
]
