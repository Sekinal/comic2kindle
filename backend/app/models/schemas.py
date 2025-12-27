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


class MangaMetadata(BaseModel):
    """Metadata for a manga."""

    title: str
    author: str = ""
    series: str = ""
    series_index: int = 1
    description: str = ""
    cover_url: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


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
    naming_pattern: str = "{series} - Chapter {index:03d}"
    epub_mode: EpubExtractionMode = EpubExtractionMode.IMAGES_ONLY
    merge_files: bool = False
    file_order: list[str] = Field(default_factory=list)
    max_output_size_mb: int = 200


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
