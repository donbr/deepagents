"""Test configuration loading and validation."""

import pytest
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from deepagents_mcp_rag.config import Settings, get_settings


def test_settings_creation():
    """Test that Settings can be created with default values."""
    settings = Settings()
    assert settings is not None
    assert hasattr(settings, 'qdrant_url')
    assert hasattr(settings, 'redis_url')


def test_get_settings():
    """Test that get_settings returns a valid Settings instance."""
    settings = get_settings()
    assert isinstance(settings, Settings)
    assert settings.qdrant_url is not None
    assert settings.redis_url is not None


def test_settings_anthropic_api_key():
    """Test anthropic API key configuration."""
    settings = get_settings()
    # Should have anthropic_api_key attribute (may be None if not set)
    assert hasattr(settings, 'anthropic_api_key')


def test_settings_qdrant_url_default():
    """Test default Qdrant URL."""
    settings = Settings()
    assert 'qdrant' in settings.qdrant_url.lower() or '6333' in settings.qdrant_url


def test_settings_redis_url_default():
    """Test default Redis URL."""
    settings = Settings()
    assert 'redis' in settings.redis_url.lower() or '6379' in settings.redis_url


def test_settings_required_fields():
    """Test that settings has all required fields."""
    settings = Settings()

    # Check that core fields exist
    required_attrs = [
        'qdrant_url', 'redis_url', 'anthropic_api_key',
        'embed_model', 'log_level'
    ]

    for attr in required_attrs:
        assert hasattr(settings, attr), f"Settings should have {attr} attribute"


def test_settings_serialization():
    """Test that settings can be serialized."""
    settings = Settings()

    # Should be able to convert to dict
    settings_dict = settings.model_dump()
    assert isinstance(settings_dict, dict)
    assert 'qdrant_url' in settings_dict
    assert 'redis_url' in settings_dict