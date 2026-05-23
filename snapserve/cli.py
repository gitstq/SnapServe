"""
CLI entry point for SnapServe.
"""

import argparse
import logging
import sys

import uvicorn


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="snapserve",
        description="SnapServe - Lightweight Self-Hosted Web Screenshot & PDF API Service",
    )
    parser.add_argument(
        "--host", "-H",
        default=None,
        help="Server host (default: 0.0.0.0, env: SNAPSERVE_HOST)",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=None,
        help="Server port (default: 8199, env: SNAPSERVE_PORT)",
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=None,
        help="Number of workers (default: 1, env: SNAPSERVE_WORKERS)",
    )
    parser.add_argument(
        "--api-key", "-k",
        default=None,
        help="API key for authentication (env: SNAPSERVE_API_KEY)",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=None,
        help="Output directory (default: ./snapserve_output, env: SNAPSERVE_OUTPUT_DIR)",
    )
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Enable debug mode",
    )
    parser.add_argument(
        "--install-browser",
        action="store_true",
        help="Install Playwright browser and exit",
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="SnapServe 1.0.0",
    )

    args = parser.parse_args()

    # Set environment variables from CLI args
    if args.host:
        import os
        os.environ["SNAPSERVE_HOST"] = args.host
    if args.port:
        import os
        os.environ["SNAPSERVE_PORT"] = str(args.port)
    if args.workers:
        import os
        os.environ["SNAPSERVE_WORKERS"] = str(args.workers)
    if args.api_key:
        import os
        os.environ["SNAPSERVE_API_KEY"] = args.api_key
    if args.output_dir:
        import os
        os.environ["SNAPSERVE_OUTPUT_DIR"] = args.output_dir
    if args.debug:
        import os
        os.environ["SNAPSERVE_DEBUG"] = "true"

    # Install browser if requested
    if args.install_browser:
        print("Installing Playwright browser...")
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True,
        )
        if result.returncode == 0:
            print("✅ Chromium browser installed successfully!")
        else:
            print(f"❌ Failed to install browser: {result.stderr.decode()}")
            sys.exit(1)
        return

    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Import config to get settings
    from .config import get_settings

    # Reset settings to pick up env vars
    import snapserve.config as config_module
    config_module.reset_settings()
    settings = get_settings()

    print(f"""
╔══════════════════════════════════════════════════╗
║          📸 SnapServe v1.0.0                    ║
║  Lightweight Web Screenshot & PDF API Service   ║
╠══════════════════════════════════════════════════╣
║  Host: {settings.host:<40s} ║
║  Port: {settings.port:<40d} ║
║  API Docs: http://{settings.host}:{settings.port}/docs{' ' * (28 - len(f'{settings.host}:{settings.port}'))}║
║  Auth: {'Enabled 🔐' if settings.api_key else 'Disabled 🔓':<40s} ║
║  Output: {str(settings.output_dir):<38s} ║
╚══════════════════════════════════════════════════╝
    """)

    # Run server
    uvicorn.run(
        "snapserve.app:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        log_level="debug" if settings.debug else "info",
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
