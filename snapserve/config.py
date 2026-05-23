"""
Configuration management for SnapServe.
All settings can be overridden via environment variables.
"""

import os
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server
    host: str = "0.0.0.0"
    port: int = 8199
    workers: int = 1
    debug: bool = False

    # API
    api_key: Optional[str] = None
    api_key_header: str = "X-API-Key"
    rate_limit_per_minute: int = 60
    max_url_length: int = 2048
    request_timeout: int = 60

    # Storage
    output_dir: str = "./snapserve_output"
    max_file_size_mb: int = 50
    keep_files_hours: int = 24

    # Browser
    browser_headless: bool = True
    browser_width: int = 1280
    browser_height: int = 720
    browser_device_scale_factor: float = 1.0
    browser_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    browser_extra_args: list[str] = Field(default_factory=list)
    concurrent_browsers: int = 5
    browser_launch_timeout: int = 30
    page_load_timeout: int = 30
    page_idle_timeout: int = 2

    # Screenshot defaults
    screenshot_format: str = "png"
    screenshot_quality: int = 80
    screenshot_full_page: bool = False
    screenshot_clip: Optional[str] = None

    # PDF defaults
    pdf_format: str = "A4"
    pdf_print_background: bool = True
    pdf_margin_top: str = "20mm"
    pdf_margin_bottom: str = "20mm"
    pdf_margin_left: str = "15mm"
    pdf_margin_right: str = "15mm"

    # OG Image defaults
    og_width: int = 1200
    og_height: int = 630
    og_template_dir: str = "./templates"

    # Security
    allowed_origins: list[str] = Field(default_factory=lambda: ["*"])
    blocked_hosts: list[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1", "0.0.0.0"])
    max_concurrent_requests: int = 10

    # Cache
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600

    @field_validator("screenshot_format")
    @classmethod
    def validate_screenshot_format(cls, v: str) -> str:
        v = v.lower()
        if v not in ("png", "jpeg", "jpg", "webp"):
            raise ValueError(f"Invalid screenshot format: {v}. Must be png, jpeg, jpg, or webp")
        return v

    @field_validator("pdf_format")
    @classmethod
    def validate_pdf_format(cls, v: str) -> str:
        valid_formats = ("A4", "A3", "Letter", "Legal", "Tabloid", "Ledger")
        if v not in valid_formats:
            raise ValueError(f"Invalid PDF format: {v}. Must be one of {valid_formats}")
        return v

    model_config = {
        "env_prefix": "SNAPSERVE_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


# Global settings singleton
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance, creating it if needed."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset settings (useful for testing)."""
    global _settings
    _settings = None
