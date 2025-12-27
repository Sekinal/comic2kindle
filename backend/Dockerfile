# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Production stage
FROM python:3.12-slim AS runner

WORKDIR /app

# Install system dependencies (including Vulkan for GPU and OpenMP for ncnn)
RUN apt-get update && apt-get install -y --no-install-recommends \
    calibre \
    unrar-free \
    p7zip-full \
    curl \
    unzip \
    libgl1 \
    libglib2.0-0 \
    libegl1 \
    libxkbcommon0 \
    libvulkan1 \
    mesa-vulkan-drivers \
    libgomp1 \
    libomp5 \
    vulkan-tools \
    && rm -rf /var/lib/apt/lists/*

# NVIDIA environment for GPU passthrough
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility,graphics,video

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Copy uv and virtual environment from builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY --from=builder /app/.venv /app/.venv

# Copy application code (ARG to bust cache when code changes)
ARG CACHEBUST=1
COPY --chown=appuser:appuser ./app ./app

# Create directories for uploads, output, and previews
RUN mkdir -p /app/uploads /app/output /app/previews && \
    chown -R appuser:appuser /app

USER appuser

# Add venv to PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Run with multiple workers for better concurrent request handling
# Workers = 4 provides good balance for typical deployment
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
