"""Application configuration."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server settings
    app_name: str = "Manga to Kindle API"
    debug: bool = False

    # File handling (defaults to local .data directory for development)
    upload_dir: Path = Path(__file__).parent.parent / ".data" / "uploads"
    output_dir: Path = Path(__file__).parent.parent / ".data" / "output"
    max_upload_size: int = 500_000_000  # 500MB

    # Supported formats
    allowed_extensions: set[str] = {".cbr", ".cbz", ".zip", ".rar", ".epub"}

    # Conversion settings
    default_output_format: str = "epub"  # epub or mobi
    image_quality: int = 85
    max_image_width: int = 1600
    max_image_height: int = 2400

    # Merge/split settings
    max_output_file_size: int = 200_000_000  # 200MB for auto-split

    # Preview settings
    preview_thumbnail_width: int = 150
    preview_thumbnail_height: int = 200
    preview_dir: Path = Path(__file__).parent.parent / ".data" / "previews"

    # API settings
    api_prefix: str = "/api"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Ensure directories exist
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.output_dir.mkdir(parents=True, exist_ok=True)
settings.preview_dir.mkdir(parents=True, exist_ok=True)
