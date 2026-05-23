"""
FastAPI application - main API routes and server configuration.
"""

import hashlib
import io
import logging
import time
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, Field, HttpUrl

from . import __version__
from .auth import AuthMiddleware
from .browser import close_browser_pool
from .config import get_settings
from .og_image import THEMES, generate_og_image, generate_og_image_from_url, generate_simple_og_image
from .pdf_engine import generate_pdf, generate_pdf_from_html
from .screenshot import capture_element_screenshot, capture_screenshot
from .storage import close_storage, get_storage

logger = logging.getLogger(__name__)


# ─── Request/Response Models ────────────────────────────────────────────


class ScreenshotRequest(BaseModel):
    """Screenshot API request body."""

    url: str = Field(..., description="URL to capture", max_length=2048)
    width: Optional[int] = Field(None, ge=100, le=4096, description="Viewport width")
    height: Optional[int] = Field(None, ge=100, le=4096, description="Viewport height")
    full_page: bool = Field(False, description="Capture full scrollable page")
    format: str = Field("png", description="Image format: png, jpeg, webp")
    quality: int = Field(80, ge=1, le=100, description="Image quality (jpeg/webp)")
    device_scale_factor: Optional[float] = Field(None, ge=0.5, le=3.0, description="Device scale factor")
    wait_for: Optional[str] = Field(None, description="CSS selector to wait for")
    wait_for_timeout: int = Field(2000, ge=0, le=30000, description="Extra wait time (ms)")
    hide_elements: Optional[list[str]] = Field(None, description="CSS selectors to hide")
    remove_elements: Optional[list[str]] = Field(None, description="CSS selectors to remove")
    dark_mode: bool = Field(False, description="Enable dark mode")
    no_ads: bool = Field(False, description="Block ads and trackers")


class ElementScreenshotRequest(BaseModel):
    """Element screenshot API request body."""

    url: str = Field(..., description="URL to capture")
    selector: str = Field(..., description="CSS selector of element")
    padding: int = Field(0, ge=0, le=100, description="Padding around element")
    format: str = Field("png", description="Image format")
    quality: int = Field(80, ge=1, le=100, description="Image quality")


class PDFRequest(BaseModel):
    """PDF generation API request body."""

    url: str = Field(..., description="URL to convert")
    format: str = Field("A4", description="Paper format: A4, A3, Letter, Legal")
    landscape: bool = Field(False, description="Landscape orientation")
    print_background: bool = Field(True, description="Print background graphics")
    margin_top: str = Field("20mm", description="Top margin")
    margin_bottom: str = Field("20mm", description="Bottom margin")
    margin_left: str = Field("15mm", description="Left margin")
    margin_right: str = Field("15mm", description="Right margin")
    scale: float = Field(1.0, ge=0.1, le=2.0, description="Page scale factor")
    page_ranges: Optional[str] = Field(None, description="Page ranges (e.g., '1-5')")
    wait_for: Optional[str] = Field(None, description="CSS selector to wait for")
    dark_mode: bool = Field(False, description="Enable dark mode")


class HTMLToPDFRequest(BaseModel):
    """HTML to PDF API request body."""

    html: str = Field(..., description="HTML content to convert")
    format: str = Field("A4", description="Paper format")
    landscape: bool = Field(False, description="Landscape orientation")
    margin_top: str = Field("20mm", description="Top margin")
    margin_bottom: str = Field("20mm", description="Bottom margin")
    margin_left: str = Field("15mm", description="Left margin")
    margin_right: str = Field("15mm", description="Right margin")


class OGImageRequest(BaseModel):
    """OG image generation API request body."""

    title: str = Field(..., description="Main title text")
    description: str = Field("", description="Description text")
    theme: str = Field("dark", description="Theme: dark, light, blue, green, orange, sunset")
    badge: str = Field("", description="Badge text")
    footer: str = Field("", description="Footer text")
    width: Optional[int] = Field(None, ge=200, le=4096, description="Image width")
    height: Optional[int] = Field(None, ge=200, le=4096, description="Image height")


class BatchRequest(BaseModel):
    """Batch processing request body."""

    tasks: list[dict] = Field(..., min_length=1, max_length=50, description="List of capture tasks")


# ─── Application Factory ────────────────────────────────────────────────


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="SnapServe",
        description=(
            "📸 Lightweight Self-Hosted Web Screenshot, PDF & OG Image API Service\n\n"
            "Zero external dependencies (no PostgreSQL/Redis). "
            "Pure Python + Playwright. Single command deployment."
        ),
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        contact={"name": "gitstq"},
        license_info={"name": "MIT"},
    )

    # CORS
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Auth & Rate Limiting
    app.add_middleware(AuthMiddleware)

    # ─── Lifecycle Events ───────────────────────────────────────────

    @app.on_event("startup")
    async def startup():
        logger.info(f"SnapServe v{__version__} starting up...")
        storage = await get_storage()
        logger.info(f"Output directory: {storage.get_output_dir()}")

    @app.on_event("shutdown")
    async def shutdown():
        logger.info("SnapServe shutting down...")
        await close_storage()
        await close_browser_pool()

    # ─── Root & Health ──────────────────────────────────────────────

    @app.get("/", tags=["Info"])
    async def root():
        """API root - service information."""
        return {
            "service": "SnapServe",
            "version": __version__,
            "status": "running",
            "endpoints": {
                "screenshot": "/api/screenshot",
                "element_screenshot": "/api/screenshot/element",
                "pdf": "/api/pdf",
                "html_to_pdf": "/api/pdf/html",
                "og_image": "/api/og-image",
                "og_from_url": "/api/og-image/url",
                "batch": "/api/batch",
                "health": "/health",
                "docs": "/docs",
            },
        }

    @app.get("/health", tags=["Info"])
    async def health():
        """Health check endpoint."""
        return {"status": "healthy", "version": __version__}

    # ─── Screenshot API ─────────────────────────────────────────────

    @app.post("/api/screenshot", tags=["Screenshot"])
    async def take_screenshot(req: ScreenshotRequest):
        """
        Capture a screenshot of a web page.

        Supports full page capture, custom viewport, dark mode, ad blocking,
        element hiding/removal, and multiple image formats.
        """
        try:
            image_bytes = await capture_screenshot(
                url=req.url,
                width=req.width,
                height=req.height,
                full_page=req.full_page,
                format=req.format,
                quality=req.quality,
                device_scale_factor=req.device_scale_factor,
                wait_for=req.wait_for,
                wait_for_timeout=req.wait_for_timeout,
                hide_elements=req.hide_elements,
                remove_elements=req.remove_elements,
                dark_mode=req.dark_mode,
                no_ads=req.no_ads,
            )

            # Save to storage
            storage = await get_storage()
            ext = req.format if req.format != "jpg" else "jpeg"
            file_id = hashlib.md5(f"{req.url}{time.time()}".encode()).hexdigest()[:12]
            filename = f"{file_id}.{ext}"
            relative_path = await storage.save_file(image_bytes, "screenshots", filename, ext)

            media_type = {
                "png": "image/png",
                "jpeg": "image/jpeg",
                "jpg": "image/jpeg",
                "webp": "image/webp",
            }.get(req.format, "image/png")

            return Response(
                content=image_bytes,
                media_type=media_type,
                headers={
                    "X-SnapServe-File": relative_path,
                    "X-SnapServe-Size": str(len(image_bytes)),
                },
            )
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/screenshot/element", tags=["Screenshot"])
    async def take_element_screenshot(req: ElementScreenshotRequest):
        """Capture a screenshot of a specific element on a web page."""
        try:
            image_bytes = await capture_element_screenshot(
                url=req.url,
                selector=req.selector,
                padding=req.padding,
                format=req.format,
                quality=req.quality,
            )

            media_type = {
                "png": "image/png",
                "jpeg": "image/jpeg",
                "jpg": "image/jpeg",
                "webp": "image/webp",
            }.get(req.format, "image/png")

            return Response(content=image_bytes, media_type=media_type)
        except Exception as e:
            logger.error(f"Element screenshot failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ─── PDF API ────────────────────────────────────────────────────

    @app.post("/api/pdf", tags=["PDF"])
    async def create_pdf(req: PDFRequest):
        """
        Generate a PDF from a web page URL.

        Supports custom paper formats, margins, scale, page ranges,
        and dark mode rendering.
        """
        try:
            pdf_bytes = await generate_pdf(
                url=req.url,
                format=req.format,
                landscape=req.landscape,
                print_background=req.print_background,
                margin_top=req.margin_top,
                margin_bottom=req.margin_bottom,
                margin_left=req.margin_left,
                margin_right=req.margin_right,
                page_ranges=req.page_ranges,
                scale=req.scale,
                wait_for=req.wait_for,
                dark_mode=req.dark_mode,
            )

            storage = await get_storage()
            file_id = hashlib.md5(f"pdf:{req.url}{time.time()}".encode()).hexdigest()[:12]
            filename = f"{file_id}.pdf"
            relative_path = await storage.save_file(pdf_bytes, "pdfs", filename, "pdf")

            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "X-SnapServe-File": relative_path,
                    "X-SnapServe-Size": str(len(pdf_bytes)),
                },
            )
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/pdf/html", tags=["PDF"])
    async def create_pdf_from_html(req: HTMLToPDFRequest):
        """Generate a PDF from raw HTML content."""
        try:
            pdf_bytes = await generate_pdf_from_html(
                html_content=req.html,
                format=req.format,
                landscape=req.landscape,
                margin_top=req.margin_top,
                margin_bottom=req.margin_bottom,
                margin_left=req.margin_left,
                margin_right=req.margin_right,
            )

            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
            )
        except Exception as e:
            logger.error(f"HTML to PDF failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ─── OG Image API ───────────────────────────────────────────────

    @app.post("/api/og-image", tags=["OG Image"])
    async def create_og_image(req: OGImageRequest):
        """
        Generate an Open Graph image for social media sharing.

        Supports multiple themes, custom dimensions, and template customization.
        """
        try:
            if req.theme not in THEMES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid theme '{req.theme}'. Available: {', '.join(THEMES.keys())}",
                )

            image_bytes = await generate_og_image(
                title=req.title,
                description=req.description,
                theme=req.theme,
                badge=req.badge,
                footer=req.footer,
                width=req.width,
                height=req.height,
            )

            storage = await get_storage()
            file_id = hashlib.md5(f"og:{req.title}{time.time()}".encode()).hexdigest()[:12]
            filename = f"{file_id}.png"
            relative_path = await storage.save_file(image_bytes, "og_images", filename, "png")

            return Response(
                content=image_bytes,
                media_type="image/png",
                headers={
                    "X-SnapServe-File": relative_path,
                    "X-SnapServe-Size": str(len(image_bytes)),
                },
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"OG image generation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/og-image/url", tags=["OG Image"])
    async def create_og_from_url(
        url: str = Query(..., description="URL to capture as OG image"),
        width: int = Query(1200, ge=200, le=4096),
        height: int = Query(630, ge=200, le=4096),
    ):
        """Capture a web page at OG image dimensions (1200x630)."""
        try:
            image_bytes = await generate_og_image_from_url(
                url=url,
                width=width,
                height=height,
            )

            return Response(content=image_bytes, media_type="image/png")
        except Exception as e:
            logger.error(f"OG from URL failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/og-image/simple", tags=["OG Image"])
    async def create_simple_og(
        title: str = Query(..., description="Title text"),
        description: str = Query("", description="Description text"),
        theme: str = Query("dark", description="Theme name"),
    ):
        """
        Generate a simple OG image using Pillow (no browser needed).
        Lightweight fallback for quick generation.
        """
        try:
            image_bytes = generate_simple_og_image(
                title=title,
                description=description,
                theme=theme,
            )
            return Response(content=image_bytes, media_type="image/png")
        except Exception as e:
            logger.error(f"Simple OG image failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ─── Batch API ──────────────────────────────────────────────────

    @app.post("/api/batch", tags=["Batch"])
    async def batch_process(req: BatchRequest):
        """
        Process multiple capture tasks in a single request.

        Each task should specify a 'type' (screenshot, pdf, og_image) and
        the corresponding parameters. Maximum 50 tasks per request.
        """
        import asyncio

        results = []

        async def process_task(task: dict, index: int):
            task_type = task.get("type", "screenshot")
            try:
                if task_type == "screenshot":
                    image_bytes = await capture_screenshot(
                        url=task["url"],
                        width=task.get("width"),
                        height=task.get("height"),
                        full_page=task.get("full_page", False),
                        format=task.get("format", "png"),
                        quality=task.get("quality", 80),
                    )
                    return {
                        "index": index,
                        "type": task_type,
                        "status": "success",
                        "size": len(image_bytes),
                        "content_type": "image/png",
                        "data": _bytes_to_base64(image_bytes),
                    }
                elif task_type == "pdf":
                    pdf_bytes = await generate_pdf(url=task["url"])
                    return {
                        "index": index,
                        "type": task_type,
                        "status": "success",
                        "size": len(pdf_bytes),
                        "content_type": "application/pdf",
                        "data": _bytes_to_base64(pdf_bytes),
                    }
                elif task_type == "og_image":
                    image_bytes = await generate_og_image(
                        title=task.get("title", ""),
                        description=task.get("description", ""),
                        theme=task.get("theme", "dark"),
                    )
                    return {
                        "index": index,
                        "type": task_type,
                        "status": "success",
                        "size": len(image_bytes),
                        "content_type": "image/png",
                        "data": _bytes_to_base64(image_bytes),
                    }
                else:
                    return {
                        "index": index,
                        "type": task_type,
                        "status": "error",
                        "error": f"Unknown task type: {task_type}",
                    }
            except Exception as e:
                return {
                    "index": index,
                    "type": task_type,
                    "status": "error",
                    "error": str(e),
                }

        # Process tasks concurrently (max 5 at a time)
        semaphore = asyncio.Semaphore(5)

        async def limited_process(task, index):
            async with semaphore:
                return await process_task(task, index)

        tasks = [limited_process(task, i) for i, task in enumerate(req.tasks)]
        results = await asyncio.gather(*tasks)

        return {
            "total": len(req.tasks),
            "results": results,
        }

    # ─── Themes List ────────────────────────────────────────────────

    @app.get("/api/themes", tags=["Info"])
    async def list_themes():
        """List available OG image themes."""
        return {
            "themes": list(THEMES.keys()),
            "default": "dark",
        }

    return app


def _bytes_to_base64(data: bytes) -> str:
    """Convert bytes to base64 string."""
    import base64
    return base64.b64encode(data).decode("utf-8")


# Application instance
app = create_app()
