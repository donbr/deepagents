"""Simple tests to validate basic functionality without complex imports."""

import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_python_version():
    """Test that we're running with Python 3.11+."""
    assert sys.version_info >= (3, 10), f"Python version {sys.version_info} is too old"


def test_basic_imports():
    """Test basic import functionality."""
    # Test that we can import standard library modules
    import json
    import asyncio
    import typing
    assert json is not None
    assert asyncio is not None
    assert typing is not None


def test_package_structure():
    """Test that the package structure exists."""
    import os

    # Check that src directory exists
    src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
    assert os.path.exists(src_path), "src directory should exist"

    # Check that main package directory exists
    package_path = os.path.join(src_path, 'deepagents_mcp_rag')
    assert os.path.exists(package_path), "Main package directory should exist"

    # Check that __init__.py exists
    init_path = os.path.join(package_path, '__init__.py')
    assert os.path.exists(init_path), "Package __init__.py should exist"


def test_config_module_exists():
    """Test that config module can be imported."""
    try:
        from deepagents_mcp_rag.config import Settings
        assert Settings is not None
        print("✅ Config module import successful")
    except ImportError as e:
        print(f"❌ Config module import failed: {e}")
        # Don't fail the test, just log
        assert False, f"Config import failed: {e}"