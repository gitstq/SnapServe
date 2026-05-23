"""
Storage manager - handles file output and cleanup.
"""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Optional

import aiofiles

from .config import get_settings

logger = logging.getLogger(__name__)


class StorageManager:
    """Manages file storage for generated screenshots, PDFs, and OG images."""

    def __init__(self):
        self._output_dir: Optional[Path] = None
        self._cleanup_task: Optional[asyncio.Task] = None

    async def initialize(self) -> None:
        """Initialize the storage directory."""
        settings = get_settings()
        self._output_dir = Path(settings.output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (self._output_dir / "screenshots").mkdir(exist_ok=True)
        (self._output_dir / "pdfs").mkdir(exist_ok=True)
        (self._output_dir / "og_images").mkdir(exist_ok=True)

        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        logger.info(f"Storage initialized: {self._output_dir}")

    async def close(self) -> None:
        """Cleanup storage resources."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def save_file(
        self,
        data: bytes,
        category: str = "screenshots",
        filename: Optional[str] = None,
        extension: str = "png",
    ) -> str:
        """
        Save data to a file and return the relative path.

        Args:
            data: File content bytes.
            category: Subdirectory (screenshots, pdfs, og_images).
            filename: Optional custom filename.
            extension: File extension.

        Returns:
            Relative file path from output directory.
        """
        if not self._output_dir:
            await self.initialize()

        category_dir = self._output_dir / category
        category_dir.mkdir(exist_ok=True)

        if not filename:
            timestamp = int(time.time() * 1000)
            filename = f"{timestamp}.{extension}"

        file_path = category_dir / filename

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(data)

        logger.info(f"File saved: {file_path} ({len(data)} bytes)")
        return str(file_path.relative_to(self._output_dir))

    async def get_file(self, relative_path: str) -> bytes:
        """Read a file by its relative path."""
        if not self._output_dir:
            await self.initialize()

        file_path = self._output_dir / relative_path

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {relative_path}")

        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()

    async def delete_file(self, relative_path: str) -> bool:
        """Delete a file by its relative path."""
        if not self._output_dir:
            return False

        file_path = self._output_dir / relative_path

        if file_path.exists():
            file_path.unlink()
            logger.info(f"File deleted: {relative_path}")
            return True
        return False

    async def _periodic_cleanup(self) -> None:
        """Periodically clean up old files."""
        settings = get_settings()
        cleanup_interval = 3600  # Check every hour
        max_age_seconds = settings.keep_files_hours * 3600

        while True:
            try:
                await asyncio.sleep(cleanup_interval)
                await self._cleanup_old_files(max_age_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    async def _cleanup_old_files(self, max_age_seconds: int) -> int:
        """Remove files older than max_age_seconds. Returns count of deleted files."""
        if not self._output_dir:
            return 0

        deleted_count = 0
        current_time = time.time()

        for category_dir in self._output_dir.iterdir():
            if not category_dir.is_dir():
                continue

            for file_path in category_dir.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        deleted_count += 1

        if deleted_count > 0:
            logger.info(f"Cleanup: deleted {deleted_count} old files")
        return deleted_count

    def get_output_dir(self) -> Path:
        """Get the output directory path."""
        if not self._output_dir:
            settings = get_settings()
            return Path(settings.output_dir)
        return self._output_dir


# Global storage manager singleton
_storage: Optional[StorageManager] = None


async def get_storage() -> StorageManager:
    """Get the global storage manager instance."""
    global _storage
    if _storage is None:
        _storage = StorageManager()
        await _storage.initialize()
    return _storage


async def close_storage() -> None:
    """Close the global storage manager."""
    global _storage
    if _storage:
        await _storage.close()
        _storage = None
