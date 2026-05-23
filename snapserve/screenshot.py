"""
Screenshot engine - captures web pages as images.
"""

import io
import logging
from typing import Optional

from playwright.async_api import Page

from .browser import get_browser_pool
from .config import get_settings

logger = logging.getLogger(__name__)


async def capture_screenshot(
    url: str,
    *,
    width: Optional[int] = None,
    height: Optional[int] = None,
    full_page: bool = False,
    format: str = "png",
    quality: int = 80,
    device_scale_factor: Optional[float] = None,
    clip: Optional[dict] = None,
    wait_for: Optional[str] = None,
    wait_for_timeout: int = 2000,
    hide_elements: Optional[list[str]] = None,
    remove_elements: Optional[list[str]] = None,
    dark_mode: bool = False,
    color_scheme: Optional[str] = None,
    no_ads: bool = False,
    cookie: Optional[list[dict]] = None,
    extra_headers: Optional[dict] = None,
) -> bytes:
    """
    Capture a screenshot of a web page.

    Args:
        url: The URL to capture.
        width: Viewport width in pixels.
        height: Viewport height in pixels.
        full_page: Capture the full scrollable page.
        format: Image format (png, jpeg, webp).
        quality: Image quality (1-100, for jpeg/webp).
        device_scale_factor: Device scale factor for retina screenshots.
        clip: Dictionary with x, y, width, height to clip the screenshot.
        wait_for: CSS selector to wait for before capturing.
        wait_for_timeout: Extra time to wait after page load (ms).
        hide_elements: CSS selectors of elements to hide (visibility: hidden).
        remove_elements: CSS selectors of elements to remove entirely.
        dark_mode: Enable dark mode.
        color_scheme: Color scheme (light, dark, no-preference).
        no_ads: Enable ad blocking.
        cookie: List of cookie dictionaries to set.
        extra_headers: Extra HTTP headers to set.

    Returns:
        Screenshot image bytes.
    """
    settings = get_settings()

    # Use provided values or fall back to settings
    width = width or settings.browser_width
    height = height or settings.browser_height
    device_scale_factor = device_scale_factor or settings.browser_device_scale_factor
    format = format or settings.screenshot_format
    quality = quality or settings.screenshot_quality

    pool = await get_browser_pool()

    async with pool.acquire_custom_page(width, height, device_scale_factor) as page:
        # Set extra headers
        if extra_headers:
            await page.set_extra_http_headers(extra_headers)

        # Set cookies
        if cookie:
            await page.context.add_cookies(cookie)

        # Set color scheme
        if color_scheme:
            await page.emulate_media(color_scheme=color_scheme)
        elif dark_mode:
            await page.emulate_media(color_scheme="dark")

        # Ad blocking via route interception
        if no_ads:
            ad_domains = [
                "doubleclick.net", "googlesyndication.com", "googleadservices.com",
                "google-analytics.com", "googletagmanager.com", "facebook.net",
                "fbcdn.net", "amazon-adsystem.com", "ads.yahoo.com", "adnxs.com",
                "adsrvr.org", "casalemedia.com", "criteo.com", "demdex.net",
                "moatads.com", "outbrain.com", "rubiconproject.com", "scorecardresearch.com",
                "serving-sys.com", "sharethis.com", "taboola.com", "tapad.com",
            ]
            await page.route(
                "**/*",
                lambda route, request: route.abort()
                if any(domain in request.url for domain in ad_domains)
                else route.continue_(),
            )

        # Navigate to URL
        try:
            response = await page.goto(url, wait_until="networkidle")
            if response and response.status >= 400:
                logger.warning(f"Page returned status {response.status} for {url}")
        except Exception as e:
            logger.error(f"Navigation failed for {url}: {e}")
            raise

        # Wait for specific element
        if wait_for:
            try:
                await page.wait_for_selector(wait_for, timeout=10000)
            except Exception:
                logger.warning(f"Wait for selector '{wait_for}' timed out")

        # Extra wait for dynamic content
        if wait_for_timeout > 0:
            await page.wait_for_timeout(wait_for_timeout)

        # Hide elements
        if hide_elements:
            for selector in hide_elements:
                try:
                    await page.evaluate(
                        f"""document.querySelectorAll('{selector}').forEach(el => {{
                            el.style.visibility = 'hidden';
                        }})"""
                    )
                except Exception:
                    pass

        # Remove elements
        if remove_elements:
            for selector in remove_elements:
                try:
                    await page.evaluate(
                        f"""document.querySelectorAll('{selector}').forEach(el => {{
                            el.remove();
                        }})"""
                    )
                except Exception:
                    pass

        # Capture screenshot
        screenshot_options = {
            "type": format,
            "full_page": full_page,
        }

        if format in ("jpeg", "jpg", "webp"):
            screenshot_options["quality"] = quality

        if clip:
            screenshot_options["clip"] = clip

        screenshot_bytes = await page.screenshot(**screenshot_options)
        logger.info(
            f"Screenshot captured: {url} ({width}x{height}, "
            f"format={format}, full_page={full_page}, size={len(screenshot_bytes)} bytes)"
        )
        return screenshot_bytes


async def capture_element_screenshot(
    url: str,
    selector: str,
    *,
    padding: int = 0,
    format: str = "png",
    quality: int = 80,
    wait_for_timeout: int = 2000,
) -> bytes:
    """
    Capture a screenshot of a specific element on a web page.

    Args:
        url: The URL to capture.
        selector: CSS selector of the element to capture.
        padding: Padding around the element in pixels.
        format: Image format.
        quality: Image quality (1-100, for jpeg/webp).
        wait_for_timeout: Extra time to wait after page load (ms).

    Returns:
        Screenshot image bytes of the element.
    """
    pool = await get_browser_pool()

    async with pool.acquire_page() as page:
        await page.goto(url, wait_until="networkidle")

        if wait_for_timeout > 0:
            await page.wait_for_timeout(wait_for_timeout)

        element = await page.wait_for_selector(selector, timeout=10000)
        if not element:
            raise ValueError(f"Element '{selector}' not found on page")

        if padding > 0:
            box = await element.bounding_box()
            if box:
                clip = {
                    "x": max(0, box["x"] - padding),
                    "y": max(0, box["y"] - padding),
                    "width": box["width"] + padding * 2,
                    "height": box["height"] + padding * 2,
                }
                screenshot_bytes = await page.screenshot(type=format, clip=clip, quality=quality)
            else:
                screenshot_bytes = await element.screenshot(type=format)
        else:
            screenshot_bytes = await element.screenshot(type=format)

        logger.info(
            f"Element screenshot captured: {url} selector='{selector}', "
            f"size={len(screenshot_bytes)} bytes"
        )
        return screenshot_bytes
