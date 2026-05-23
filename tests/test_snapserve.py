"""Tests for SnapServe."""

import pytest
from snapserve import __version__


def test_version():
    """Test that version is defined."""
    assert __version__ == "1.0.0"


def test_imports():
    """Test that all modules can be imported."""
    from snapserve.config import get_settings, Settings
    from snapserve.auth import RateLimiter, APIKeyAuth
    from snapserve.storage import StorageManager

    assert Settings is not None
    assert RateLimiter is not None
    assert APIKeyAuth is not None
    assert StorageManager is not None


def test_settings_defaults():
    """Test default settings."""
    from snapserve.config import Settings

    settings = Settings()
    assert settings.host == "0.0.0.0"
    assert settings.port == 8199
    assert settings.browser_headless is True
    assert settings.screenshot_format == "png"
    assert settings.pdf_format == "A4"
    assert settings.og_width == 1200
    assert settings.og_height == 630


def test_settings_validation():
    """Test settings validation."""
    from snapserve.config import Settings
    from pydantic import ValidationError

    # Invalid screenshot format
    with pytest.raises(ValidationError):
        Settings(screenshot_format="bmp")

    # Invalid PDF format
    with pytest.raises(ValidationError):
        Settings(pdf_format="B5")

    # Valid formats should work
    settings = Settings(screenshot_format="webp", pdf_format="Letter")
    assert settings.screenshot_format == "webp"
    assert settings.pdf_format == "Letter"


def test_rate_limiter():
    """Test rate limiter functionality."""
    from snapserve.auth import RateLimiter

    limiter = RateLimiter(max_requests=3, window_seconds=60)

    # First 3 requests should be allowed
    allowed, remaining = limiter.is_allowed("test_key")
    assert allowed is True
    assert remaining == 2

    allowed, remaining = limiter.is_allowed("test_key")
    assert allowed is True
    assert remaining == 1

    allowed, remaining = limiter.is_allowed("test_key")
    assert allowed is True
    assert remaining == 0

    # 4th request should be rate limited
    allowed, remaining = limiter.is_allowed("test_key")
    assert allowed is False
    assert remaining == 0

    # Different key should be allowed
    allowed, remaining = limiter.is_allowed("other_key")
    assert allowed is True


def test_api_key_auth_disabled():
    """Test API key auth when disabled."""
    from snapserve.auth import APIKeyAuth

    auth = APIKeyAuth(api_key=None)
    assert auth.is_auth_enabled() is False
    assert auth.validate(None) is True  # Should always return True when disabled


def test_api_key_auth_enabled():
    """Test API key auth when enabled."""
    from snapserve.auth import APIKeyAuth
    from unittest.mock import MagicMock

    auth = APIKeyAuth(api_key="test_secret_key", header_name="X-API-Key")
    assert auth.is_auth_enabled() is True

    # Create mock request with correct key
    request = MagicMock()
    request.headers = {"X-API-Key": "test_secret_key"}
    request.query_params = {}
    assert auth.validate(request) is True

    # Wrong key
    request.headers = {"X-API-Key": "wrong_key"}
    assert auth.validate(request) is False

    # Missing key
    request.headers = {}
    assert auth.validate(request) is False


def test_og_themes():
    """Test that OG image themes are defined."""
    from snapserve.og_image import THEMES

    assert "dark" in THEMES
    assert "light" in THEMES
    assert "blue" in THEMES
    assert "green" in THEMES
    assert "orange" in THEMES
    assert "sunset" in THEMES

    # Each theme should have required keys
    for theme_name, theme_data in THEMES.items():
        assert "bg_style" in theme_data
        assert "title_color" in theme_data
        assert "desc_color" in theme_data


def test_simple_og_image_generation():
    """Test simple OG image generation with Pillow."""
    from snapserve.og_image import generate_simple_og_image

    image_bytes = generate_simple_og_image(
        title="Test Title",
        description="Test Description",
        theme="dark",
        width=800,
        height=400,
    )

    assert isinstance(image_bytes, bytes)
    assert len(image_bytes) > 0

    # Verify it's a valid PNG
    assert image_bytes[:4] == b'\x89PNG'
