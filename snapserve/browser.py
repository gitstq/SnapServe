"""
Browser management - handles Playwright browser lifecycle.
Uses a pool of browser contexts for efficient concurrent rendering.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    BrowserType,
    Page,
    Playwright,
    async_playwright,
)

from .config import get_settings

logger = logging.getLogger(__name__)


class BrowserPool:
    """Manages a pool of Playwright browser contexts for concurrent rendering."""

    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the browser pool."""
        if self._initialized:
            return

        settings = get_settings()
        self._playwright = await async_playwright().start()
        self._semaphore = asyncio.Semaphore(settings.concurrent_browsers)

        launch_args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-extensions",
            "--no-first-run",
            "--no-default-browser-check",
        ]
        launch_args.extend(settings.browser_extra_args)

        self._browser = await self._playwright.chromium.launch(
            headless=settings.browser_headless,
            args=launch_args,
        )

        self._initialized = True
        logger.info(
            f"Browser pool initialized (concurrent={settings.concurrent_browsers}, "
            f"headless={settings.browser_headless})"
        )

    async def close(self) -> None:
        """Close all browser instances and cleanup."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        self._initialized = False
        logger.info("Browser pool closed")

    @asynccontextmanager
    async def acquire_page(self):
        """Acquire a browser page from the pool (context manager)."""
        if not self._initialized:
            await self.initialize()

        async with self._semaphore:
            settings = get_settings()
            context = await self._browser.new_context(
                viewport={
                    "width": settings.browser_width,
                    "height": settings.browser_height,
                },
                device_scale_factor=settings.browser_device_scale_factor,
                user_agent=settings.browser_user_agent,
                ignore_https_errors=True,
            )

            try:
                page = await context.new_page()
                page.set_default_timeout(settings.page_load_timeout * 1000)
                page.set_default_navigation_timeout(settings.page_load_timeout * 1000)
                yield page
            finally:
                await context.close()

    @asynccontextmanager
    async def acquire_custom_page(self, width: int, height: int, device_scale_factor: float = 1.0):
        """Acquire a browser page with custom viewport settings."""
        if not self._initialized:
            await self.initialize()

        async with self._semaphore:
            settings = get_settings()
            context = await self._browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=device_scale_factor,
                user_agent=settings.browser_user_agent,
                ignore_https_errors=True,
            )

            try:
                page = await context.new_page()
                page.set_default_timeout(settings.page_load_timeout * 1000)
                page.set_default_navigation_timeout(settings.page_load_timeout * 1000)
                yield page
            finally:
                await context.close()


# Global browser pool singleton
_pool: Optional[BrowserPool] = None


async def get_browser_pool() -> BrowserPool:
    """Get the global browser pool instance."""
    global _pool
    if _pool is None:
        _pool = BrowserPool()
        await _pool.initialize()
    return _pool


async def close_browser_pool() -> None:
    """Close the global browser pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
