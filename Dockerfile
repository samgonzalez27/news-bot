# =============================================================================
# News Digest API - Multi-stage Docker Build
# =============================================================================
# Build: docker build -t news-digest-api .
# Run:   docker run -p 8000:8000 --env-file .env news-digest-api
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

# Prevent Python from writing bytecode and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for better layer caching
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Final - Production image
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS final

# Prevent Python from writing bytecode and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Application defaults (can be overridden)
    APP_ENV=production \
    HOST=0.0.0.0 \
    PORT=8000 \
    LOG_LEVEL=INFO

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=appuser:appgroup . .

# Make entrypoint script executable
RUN chmod +x /app/scripts/entrypoint.sh

# Create log directory with proper permissions
RUN mkdir -p /var/log/news-digest \
    && chown -R appuser:appgroup /var/log/news-digest

# Switch to non-root user
USER appuser

# Expose the application port
EXPOSE 8000

# Health check - verify the API is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use entrypoint script for startup orchestration
ENTRYPOINT ["/app/scripts/entrypoint.sh"]

# Default command - start the API server
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
