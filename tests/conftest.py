"""
Pytest configuration: ensure project source directory is on PYTHONPATH
so that tests can import packages such as `scaffolding`, `simbuilder_api`, etc.
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

# Add `<repo>/src` to sys.path once, at highest priority
_SRC = (Path(__file__).resolve().parent.parent / "src").resolve()
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture(autouse=True)
def clear_caches():
    """Clear LRU caches before each test to ensure clean state."""
    try:
        from simbuilder_api.dependencies import get_settings, get_jwt_handler
        get_settings.cache_clear()
        get_jwt_handler.cache_clear()
    except ImportError:
        # Module might not be available for all tests
        pass
    
    try:
        from scaffolding.config import get_settings as scaffolding_get_settings
        scaffolding_get_settings.cache_clear()
    except ImportError:
        pass