"""
PDF generation engine - converts web pages to PDF documents.
"""

import logging
from typing import Optional

from .browser import get_browser_pool
from .config import get_settings

logger = logging.getLogger(__name__)


async def generate_pdf(
    url: str,
    *,
    format: str = "A4",
    landscape: bool = False,
    print_background: bool = True,
    margin_top: str = "20mm",
    margin_bottom: str = "20mm",
    margin_left: str = "15mm",
    margin_right: str = "15mm",
    page_ranges: Optional[str] = None,
    scale: float = 1.0,
    display_header_footer: bool = False,
    header_template: str = "",
    footer_template: str = "",
    wait_for: Optional[str] = None,
    wait_for_timeout: int = 2000,
    dark_mode: bool = False,
    cookie: Optional[list[dict]] = None,
    extra_headers: Optional[dict] = None,
) -> bytes:
    """
    Generate a PDF from a web page.

    Args:
        url: The URL to convert to PDF.
        format: Paper format (A4, A3, Letter, Legal, Tabloid, Ledger).
        landscape: Use landscape orientation.
        print_background: Print background graphics.
        margin_top: Top margin (e.g., "20mm", "1in").
        margin_bottom: Bottom margin.
        margin_left: Left margin.
        margin_right: Right margin.
        page_ranges: Page ranges to print (e.g., "1-5").
        scale: Scale factor for the page content.
        display_header_footer: Display header and footer.
        header_template: HTML template for the header.
        footer_template: HTML template for the footer.
        wait_for: CSS selector to wait for before generating.
        wait_for_timeout: Extra time to wait after page load (ms).
        dark_mode: Enable dark mode.
        cookie: List of cookie dictionaries to set.
        extra_headers: Extra HTTP headers to set.

    Returns:
        PDF document bytes.
    """
    settings = get_settings()

    format = format or settings.pdf_format
    print_background = print_background if print_background is not None else settings.pdf_print_background
    margin_top = margin_top or settings.pdf_margin_top
    margin_bottom = margin_bottom or settings.pdf_margin_bottom
    margin_left = margin_left or settings.pdf_margin_left
    margin_right = margin_right or settings.pdf_margin_right

    pool = await get_browser_pool()

    async with pool.acquire_page() as page:
        # Set extra headers
        if extra_headers:
            await page.set_extra_http_headers(extra_headers)

        # Set cookies
        if cookie:
            await page.context.add_cookies(cookie)

        # Set color scheme
        if dark_mode:
            await page.emulate_media(color_scheme="dark")

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

        # Generate PDF
        pdf_options = {
            "format": format,
            "landscape": landscape,
            "print_background": print_background,
            "margin": {
                "top": margin_top,
                "bottom": margin_bottom,
                "left": margin_left,
                "right": margin_right,
            },
            "scale": scale,
        }

        if page_ranges:
            pdf_options["page_ranges"] = page_ranges

        if display_header_footer:
            pdf_options["display_header_footer"] = True
            pdf_options["header_template"] = header_template
            pdf_options["footer_template"] = footer_template

        pdf_bytes = await page.pdf(**pdf_options)
        logger.info(
            f"PDF generated: {url} (format={format}, landscape={landscape}, "
            f"size={len(pdf_bytes)} bytes)"
        )
        return pdf_bytes


async def generate_pdf_from_html(
    html_content: str,
    *,
    format: str = "A4",
    landscape: bool = False,
    print_background: bool = True,
    margin_top: str = "20mm",
    margin_bottom: str = "20mm",
    margin_left: str = "15mm",
    margin_right: str = "15mm",
    scale: float = 1.0,
    display_header_footer: bool = False,
    header_template: str = "",
    footer_template: str = "",
) -> bytes:
    """
    Generate a PDF from raw HTML content.

    Args:
        html_content: Raw HTML string to convert.
        format: Paper format.
        landscape: Use landscape orientation.
        print_background: Print background graphics.
        margin_top: Top margin.
        margin_bottom: Bottom margin.
        margin_left: Left margin.
        margin_right: Right margin.
        scale: Scale factor.
        display_header_footer: Display header and footer.
        header_template: HTML template for the header.
        footer_template: HTML template for the footer.

    Returns:
        PDF document bytes.
    """
    pool = await get_browser_pool()

    async with pool.acquire_page() as page:
        await page.set_content(html_content, wait_until="networkidle")

        pdf_bytes = await page.pdf(
            format=format,
            landscape=landscape,
            print_background=print_background,
            margin={
                "top": margin_top,
                "bottom": margin_bottom,
                "left": margin_left,
                "right": margin_right,
            },
            scale=scale,
            display_header_footer=display_header_footer,
            header_template=header_template,
            footer_template=footer_template,
        )

        logger.info(
            f"PDF generated from HTML (format={format}, size={len(pdf_bytes)} bytes)"
        )
        return pdf_bytes
