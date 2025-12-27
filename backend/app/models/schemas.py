"""Pydantic schemas for API models."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class OutputFormat(str, Enum):
    """Supported output formats."""

    EPUB = "epub"
    MOBI = "mobi"
    BOTH = "both"


class InputFormat(str, Enum):
    """Supported input formats."""

    CBZ = "cbz"
    CBR = "cbr"
    EPUB = "epub"
    ZIP = "zip"
    RAR = "rar"


class EpubExtractionMode(str, Enum):
    """How to handle EPUB input files."""

    IMAGES_ONLY = "images_only"
    PRESERVE_STRUCTURE = "preserve"


class ConversionStatus(str, Enum):
    """Status of a conversion job."""

    PENDING = "pending"
    EXTRACTING = "extracting"
    PROCESSING = "processing"
    MERGING = "merging"
    CONVERTING = "converting"
    SPLITTING = "splitting"
    COMPLETED = "completed"
    FAILED = "failed"


class DeviceProfile(str, Enum):
    """Target e-reader device profiles."""

    KINDLE_BASIC = "kindle_basic"
    KINDLE_PAPERWHITE_5 = "kindle_paperwhite_5"
    KINDLE_SCRIBE = "kindle_scribe"
    KOBO_CLARA_2E = "kobo_clara_2e"
    KOBO_LIBRA_2 = "kobo_libra_2"
    KOBO_SAGE = "kobo_sage"
    CUSTOM = "custom"


class UpscaleMethod(str, Enum):
    """Image upscaling method."""

    NONE = "none"
    LANCZOS = "lanczos"
    AI_ESRGAN = "ai_esrgan"


class FileInfo(BaseModel):
    """Information about an uploaded file."""

    id: str
    original_name: str
    size: int
    page_count: int = 0
    extension: str
    input_format: InputFormat = InputFormat.CBZ
    preview_url: Optional[str] = None
    order: int = 0
    estimated_output_size: int = 0
    uploaded_at: datetime = Field(default_factory=datetime.now)


class UploadResponse(BaseModel):
    """Response after file upload."""

    session_id: str
    files: list[FileInfo]
    message: str


class ChapterInfo(BaseModel):
    """Flexible chapter information for manga files."""

    chapter_start: Optional[float] = None  # Supports decimals like 10.5
    chapter_end: Optional[float] = None  # For ranges like "1-16"
    volume: Optional[int] = None
    title_prefix: str = ""
    title_suffix: str = ""

    def format_chapter_string(self) -> str:
        """Format chapter info as a string like '1' or '1-16'."""
        if self.chapter_start is not None and self.chapter_end is not None:
            start = (
                int(self.chapter_start)
                if self.chapter_start == int(self.chapter_start)
                else self.chapter_start
            )
            end = (
                int(self.chapter_end)
                if self.chapter_end == int(self.chapter_end)
                else self.chapter_end
            )
            return f"{start}-{end}"
        elif self.chapter_start is not None:
            val = (
                int(self.chapter_start)
                if self.chapter_start == int(self.chapter_start)
                else self.chapter_start
            )
            return str(val)
        return ""


class ImageProcessingOptions(BaseModel):
    """Options for image processing during conversion."""

    device_profile: DeviceProfile = DeviceProfile.KINDLE_PAPERWHITE_5
    custom_width: Optional[int] = None
    custom_height: Optional[int] = None
    upscale_method: UpscaleMethod = UpscaleMethod.LANCZOS
    detect_spreads: bool = True
    rotate_spreads: bool = True
    fill_screen: bool = True


class MangaMetadata(BaseModel):
    """Metadata for a manga."""

    title: str
    author: str = ""
    series: str = ""
    chapter_info: ChapterInfo = Field(default_factory=ChapterInfo)
    description: str = ""
    cover_url: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    title_format: str = "{series} - Ch. {chapter}"

    def get_display_title(self) -> str:
        """Generate formatted display title for e-reader."""
        chapter_str = self.chapter_info.format_chapter_string() or "1"
        volume_str = f"Vol. {self.chapter_info.volume}" if self.chapter_info.volume else ""

        return (
            self.title_format.replace("{series}", self.series or self.title)
            .replace("{title}", self.title)
            .replace("{chapter}", chapter_str)
            .replace("{volume}", volume_str)
            .replace("{prefix}", self.chapter_info.title_prefix)
            .replace("{suffix}", self.chapter_info.title_suffix)
            .strip()
        )


class MetadataSearchResult(BaseModel):
    """Result from metadata search."""

    id: str
    title: str
    author: str = ""
    description: str = ""
    cover_url: Optional[str] = None
    source: str  # mangadex, anilist, etc.


class ConversionRequest(BaseModel):
    """Request to convert files."""

    session_id: str
    file_ids: list[str]
    metadata: MangaMetadata
    output_format: OutputFormat = OutputFormat.EPUB
    naming_pattern: str = "{series} - Ch. {chapter}"
    epub_mode: EpubExtractionMode = EpubExtractionMode.IMAGES_ONLY
    merge_files: bool = False
    file_order: list[str] = Field(default_factory=list)
    max_output_size_mb: int = 200
    image_options: ImageProcessingOptions = Field(default_factory=ImageProcessingOptions)


class ConversionJob(BaseModel):
    """A conversion job."""

    job_id: str
    session_id: str
    status: ConversionStatus = ConversionStatus.PENDING
    progress: float = 0.0  # 0-100
    current_file: Optional[str] = None
    current_phase: str = ""
    split_count: int = 1
    output_files: list[str] = Field(default_factory=list)
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class FilenameParseResult(BaseModel):
    """Result of smart filename parsing."""

    series: Optional[str] = None
    chapter: Optional[int] = None
    volume: Optional[int] = None
    title: Optional[str] = None


class FileOrderUpdate(BaseModel):
    """Request to update file order."""

    file_order: list[str]


class DeviceProfileInfo(BaseModel):
    """Device profile information for API response."""

    id: str
    name: str
    display_name: str
    manufacturer: str  # kindle, kobo, custom
    width: int
    height: int
    dpi: int
    supports_color: bool = False
    recommended_format: str = "epub"


class CapabilitiesResponse(BaseModel):
    """System capabilities response."""

    ai_upscaling_available: bool = False
    supported_input_formats: list[str] = Field(
        default_factory=lambda: ["cbz", "cbr", "epub", "zip", "rar"]
    )
    supported_output_formats: list[str] = Field(default_factory=lambda: ["epub", "mobi"])
