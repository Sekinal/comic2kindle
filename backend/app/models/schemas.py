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


class ConversionStatus(str, Enum):
    """Status of a conversion job."""

    PENDING = "pending"
    EXTRACTING = "extracting"
    CONVERTING = "converting"
    COMPLETED = "completed"
    FAILED = "failed"


class FileInfo(BaseModel):
    """Information about an uploaded file."""

    id: str
    original_name: str
    size: int
    page_count: int = 0
    extension: str
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


class ConversionJob(BaseModel):
    """A conversion job."""

    job_id: str
    session_id: str
    status: ConversionStatus = ConversionStatus.PENDING
    progress: float = 0.0  # 0-100
    current_file: Optional[str] = None
    output_files: list[str] = Field(default_factory=list)
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
