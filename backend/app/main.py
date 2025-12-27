"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import convert, devices, download, metadata, upload
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API for converting manga to Kindle-compatible formats",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix=settings.api_prefix, tags=["upload"])
app.include_router(metadata.router, prefix=settings.api_prefix, tags=["metadata"])
app.include_router(convert.router, prefix=settings.api_prefix, tags=["convert"])
app.include_router(download.router, prefix=settings.api_prefix, tags=["download"])
app.include_router(devices.router, prefix=settings.api_prefix, tags=["devices"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for Docker."""
    return {"status": "healthy"}


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Manga to Kindle API",
        "docs": "/docs",
        "health": "/health",
    }
