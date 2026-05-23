FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY snapserve/ snapserve/
COPY tests/ tests/
COPY README.md LICENSE .env.example .gitignore ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Install Playwright browser
RUN python -m playwright install chromium \
    && python -m playwright install-deps chromium

# Create output directory
RUN mkdir -p /app/snapserve_output

# Environment variables
ENV SNAPSERVE_HOST=0.0.0.0
ENV SNAPSERVE_PORT=8199
ENV SNAPSERVE_OUTPUT_DIR=/app/snapserve_output
ENV SNAPSERVE_BROWSER_HEADLESS=true

# Expose port
EXPOSE 8199

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8199/health')" || exit 1

# Start server
CMD ["snapserve", "--host", "0.0.0.0", "--port", "8199"]
