"""
OG (Open Graph) image generation engine.
Creates social media preview images from templates.
"""

import io
import logging
from typing import Optional

from PIL import Image, ImageDraw, ImageFont
from playwright.async_api import Page

from .browser import get_browser_pool
from .config import get_settings

logger = logging.getLogger(__name__)


# Default OG image template
DEFAULT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            width: {width}px;
            height: {height}px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 60px;
            {bg_style}
        }
        .title {{
            font-size: 52px;
            font-weight: 800;
            line-height: 1.2;
            margin-bottom: 20px;
            color: {title_color};
        }}
        .description {{
            font-size: 28px;
            line-height: 1.5;
            color: {desc_color};
            max-width: 90%;
        }}
        .badge {{
            position: absolute;
            top: 40px;
            right: 40px;
            background: rgba(255,255,255,0.15);
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 16px;
            color: {badge_color};
        }}
        .footer {{
            position: absolute;
            bottom: 30px;
            left: 60px;
            font-size: 18px;
            color: {footer_color};
        }}
    </style>
</head>
<body>
    <div class="badge">{badge}</div>
    <div class="title">{title}</div>
    <div class="description">{description}</div>
    <div class="footer">{footer}</div>
</body>
</html>
"""

# Predefined themes
THEMES = {
    "dark": {
        "bg_style": "background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); color: #ffffff;",
        "title_color": "#ffffff",
        "desc_color": "#b0b0c0",
        "badge_color": "#a0a0b0",
        "footer_color": "#707080",
    },
    "light": {
        "bg_style": "background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); color: #2c3e50;",
        "title_color": "#2c3e50",
        "desc_color": "#5a6c7d",
        "badge_color": "#7f8c8d",
        "footer_color": "#95a5a6",
    },
    "blue": {
        "bg_style": "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff;",
        "title_color": "#ffffff",
        "desc_color": "#e0d0f0",
        "badge_color": "#d0c0e0",
        "footer_color": "#c0b0d0",
    },
    "green": {
        "bg_style": "background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: #ffffff;",
        "title_color": "#ffffff",
        "desc_color": "#e0f5e0",
        "badge_color": "#d0f0d0",
        "footer_color": "#c0e0c0",
    },
    "orange": {
        "bg_style": "background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: #ffffff;",
        "title_color": "#ffffff",
        "desc_color": "#ffe0e8",
        "badge_color": "#ffd0d8",
        "footer_color": "#ffc0c8",
    },
    "sunset": {
        "bg_style": "background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); color: #ffffff;",
        "title_color": "#ffffff",
        "desc_color": "#fff0d0",
        "badge_color": "#ffe0b0",
        "footer_color": "#ffd090",
    },
}


async def generate_og_image(
    title: str,
    description: str = "",
    *,
    theme: str = "dark",
    badge: str = "",
    footer: str = "",
    width: Optional[int] = None,
    height: Optional[int] = None,
    custom_template: Optional[str] = None,
    custom_css: Optional[str] = None,
) -> bytes:
    """
    Generate an Open Graph image.

    Args:
        title: Main title text.
        description: Description text.
        theme: Color theme (dark, light, blue, green, orange, sunset).
        badge: Badge text (top-right corner).
        footer: Footer text.
        width: Image width (default: 1200).
        height: Image height (default: 630).
        custom_template: Custom HTML template (overrides theme).
        custom_css: Custom CSS to inject.

    Returns:
        OG image bytes (PNG).
    """
    settings = get_settings()
    width = width or settings.og_width
    height = height or settings.og_height

    # Get theme or use default
    theme_data = THEMES.get(theme, THEMES["dark"])

    if custom_template:
        html = custom_template.format(
            width=width, height=height,
            title=title, description=description,
            badge=badge, footer=footer,
            **theme_data,
        )
    else:
        html = DEFAULT_TEMPLATE.format(
            width=width, height=height,
            title=title, description=description or " ",
            badge=badge, footer=footer,
            **theme_data,
        )

    # Inject custom CSS
    if custom_css:
        html = html.replace("</head>", f"<style>{custom_css}</style></head>")

    pool = await get_browser_pool()

    async with pool.acquire_custom_page(width, height) as page:
        await page.set_content(html, wait_until="networkidle")
        await page.wait_for_timeout(500)

        image_bytes = await page.screenshot(type="png")
        logger.info(
            f"OG image generated: title='{title[:30]}...', "
            f"theme={theme}, size={len(image_bytes)} bytes"
        )
        return image_bytes


async def generate_og_image_from_url(
    url: str,
    *,
    width: int = 1200,
    height: int = 630,
    wait_for_timeout: int = 3000,
) -> bytes:
    """
    Generate an OG image by capturing a web page at OG dimensions.

    Args:
        url: The URL to capture as OG image.
        width: Image width (default: 1200).
        height: Image height (default: 630).
        wait_for_timeout: Extra wait time (ms).

    Returns:
        OG image bytes (PNG).
    """
    pool = await get_browser_pool()

    async with pool.acquire_custom_page(width, height) as page:
        await page.goto(url, wait_until="networkidle")

        if wait_for_timeout > 0:
            await page.wait_for_timeout(wait_for_timeout)

        image_bytes = await page.screenshot(type="png", full_page=False)
        logger.info(
            f"OG image from URL: {url}, size={len(image_bytes)} bytes"
        )
        return image_bytes


def generate_simple_og_image(
    title: str,
    description: str = "",
    *,
    theme: str = "dark",
    width: int = 1200,
    height: int = 630,
) -> bytes:
    """
    Generate a simple OG image using Pillow (no browser required).
    Fallback for environments without Playwright.

    Args:
        title: Main title text.
        description: Description text.
        theme: Color theme name.
        width: Image width.
        height: Image height.

    Returns:
        OG image bytes (PNG).
    """
    theme_data = THEMES.get(theme, THEMES["dark"])

    # Parse gradient colors from theme
    bg_colors = {
        "dark": ((26, 26, 46), (15, 52, 96)),
        "light": ((245, 247, 250), (195, 207, 226)),
        "blue": ((102, 126, 234), (118, 75, 162)),
        "green": ((17, 153, 142), (56, 239, 125)),
        "orange": ((240, 147, 251), (245, 87, 108)),
        "sunset": ((250, 112, 154), (254, 225, 64)),
    }
    start_color, end_color = bg_colors.get(theme, bg_colors["dark"])

    # Create gradient background
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    for y in range(height):
        ratio = y / height
        r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Draw title text
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
        desc_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
        footer_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except (OSError, IOError):
        title_font = ImageFont.load_default()
        desc_font = ImageFont.load_default()
        footer_font = ImageFont.load_default()

    # Title
    title_color = theme_data.get("title_color", "#ffffff")
    if title_color.startswith("#"):
        title_color = tuple(int(title_color[i:i+2], 16) for i in (1, 3, 5))
    else:
        title_color = (255, 255, 255)

    # Word wrap title
    max_chars_per_line = 25
    title_lines = []
    words = title.split()
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 <= max_chars_per_line:
            current_line = f"{current_line} {word}".strip()
        else:
            if current_line:
                title_lines.append(current_line)
            current_line = word
    if current_line:
        title_lines.append(current_line)

    y_offset = 180
    for line in title_lines[:4]:
        draw.text((60, y_offset), line, fill=title_color, font=title_font)
        y_offset += 70

    # Description
    if description:
        desc_color = theme_data.get("desc_color", "#b0b0c0")
        if desc_color.startswith("#"):
            desc_color = tuple(int(desc_color[i:i+2], 16) for i in (1, 3, 5))
        else:
            desc_color = (176, 176, 192)

        desc_lines = []
        words = description.split()
        current_line = ""
        for word in words:
            if len(current_line) + len(word) + 1 <= 40:
                current_line = f"{current_line} {word}".strip()
            else:
                if current_line:
                    desc_lines.append(current_line)
                current_line = word
        if current_line:
            desc_lines.append(current_line)

        y_offset += 20
        for line in desc_lines[:3]:
            draw.text((60, y_offset), line, fill=desc_color, font=desc_font)
            y_offset += 42

    # Save to bytes
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
