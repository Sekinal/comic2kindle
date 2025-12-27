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

# Install system dependencies
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
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Download and install Real-ESRGAN for AI upscaling (with models)
RUN mkdir -p /app/realesrgan && \
    curl -L -o /tmp/realesrgan.zip \
    "https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan/releases/download/v0.2.0/realesrgan-ncnn-vulkan-v0.2.0-ubuntu.zip" && \
    unzip /tmp/realesrgan.zip -d /tmp && \
    mv /tmp/realesrgan-ncnn-vulkan-v0.2.0-ubuntu/* /app/realesrgan/ && \
    chmod +x /app/realesrgan/realesrgan-ncnn-vulkan && \
    rm -rf /tmp/realesrgan.zip /tmp/realesrgan-ncnn-vulkan-v0.2.0-ubuntu && \
    # Download ncnn models (bin + param files for each scale)
    mkdir -p /app/realesrgan/models && \
    for scale in x2 x3 x4; do \
        curl -L -o "/app/realesrgan/models/realesr-animevideov3-${scale}.bin" \
        "https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan/raw/master/models/realesr-animevideov3-${scale}.bin" && \
        curl -L -o "/app/realesrgan/models/realesr-animevideov3-${scale}.param" \
        "https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan/raw/master/models/realesr-animevideov3-${scale}.param"; \
    done

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Copy uv and virtual environment from builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --chown=appuser:appuser ./app ./app

# Create directories for uploads, output, and previews
RUN mkdir -p /app/uploads /app/output /app/previews && \
    chown -R appuser:appuser /app

USER appuser

# Add venv and realesrgan to PATH
ENV PATH="/app/.venv/bin:/app/realesrgan:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
