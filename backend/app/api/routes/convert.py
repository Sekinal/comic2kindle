"""Conversion API routes."""

import asyncio
import logging
import tempfile
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

logger = logging.getLogger(__name__)

from app.api.deps import get_extractor, get_file_manager, get_merger
from app.models.schemas import (
    ConversionJob,
    ConversionRequest,
    ConversionStatus,
)
from app.services.converter import ConverterService
from app.services.extractor import ExtractorService
from app.services.file_manager import FileManager
from app.services.merger import MergerService

router = APIRouter(prefix="/convert", tags=["convert"])

# In-memory job storage (in production, use Redis or database)
jobs: dict[str, ConversionJob] = {}


def _find_file_by_id(session_dir: Path, file_id: str) -> Path | None:
    """Find a file or image folder by ID in the session directory.

    Handles both:
    - Regular archive files: {file_id}.cbz, {file_id}.epub, etc.
    - Image folders: {file_id}_images/
    """
    for f in session_dir.iterdir():
        # Match regular files by stem
        if f.is_file() and f.stem == file_id:
            return f
        # Match image folders by pattern {file_id}_images
        if f.is_dir() and f.name == f"{file_id}_images":
            return f
    return None


def _update_job(job_id: str, **kwargs: Any) -> None:
    """Update job fields."""
    if job_id in jobs:
        for key, value in kwargs.items():
            setattr(jobs[job_id], key, value)


async def _run_conversion(
    job_id: str,
    request: ConversionRequest,
    file_manager: FileManager,
    extractor: ExtractorService,
    merger: MergerService,
) -> None:
    """
    Background task to run the conversion process.

    Handles both individual file conversion and merged conversion with auto-split.
    """
    try:
        output_dir = file_manager.get_output_dir(request.session_id)
        session_dir = file_manager.get_session_dir(request.session_id)

        # Create converter with image processing options from request
        converter = ConverterService(image_options=request.image_options)

        # Determine file order
        file_ids = request.file_order if request.file_order else request.file_ids

        if request.merge_files:
            # Merge mode: combine all files into one (or multiple if > 200MB)
            await _run_merged_conversion(
                job_id=job_id,
                request=request,
                file_ids=file_ids,
                session_dir=session_dir,
                output_dir=output_dir,
                extractor=extractor,
                converter=converter,
                merger=merger,
            )
        else:
            # Individual mode: convert each file separately
            await _run_individual_conversion(
                job_id=job_id,
                request=request,
                file_ids=file_ids,
                session_dir=session_dir,
                output_dir=output_dir,
                extractor=extractor,
                converter=converter,
            )

    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        logger.error(traceback.format_exc())
        _update_job(
            job_id,
            status=ConversionStatus.FAILED,
            error=str(e),
            current_phase="Error",
        )


async def _run_individual_conversion(
    job_id: str,
    request: ConversionRequest,
    file_ids: list[str],
    session_dir: Path,
    output_dir: Path,
    extractor: ExtractorService,
    converter: ConverterService,
) -> None:
    """Convert each file individually."""
    _update_job(
        job_id,
        status=ConversionStatus.EXTRACTING,
        current_phase="Extracting files",
    )

    output_files: list[str] = []
    total_files = len(file_ids)

    for idx, file_id in enumerate(file_ids):
        # Find the file or image folder
        file_path = _find_file_by_id(session_dir, file_id)

        if not file_path:
            _update_job(
                job_id,
                status=ConversionStatus.FAILED,
                error=f"File not found: {file_id}",
                current_phase="Error",
            )
            return

        _update_job(
            job_id,
            current_file=file_path.name,
            current_phase=f"Extracting ({idx + 1}/{total_files})",
            progress=(idx / total_files) * 50,
        )

        # Extract images to temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Use asyncio.to_thread to avoid blocking the event loop
            images = await asyncio.to_thread(
                extractor.extract, file_path, temp_path, request.epub_mode
            )

            if not images:
                _update_job(
                    job_id,
                    status=ConversionStatus.FAILED,
                    error=f"No images found in: {file_path.name}",
                    current_phase="Error",
                )
                return

            _update_job(
                job_id,
                status=ConversionStatus.CONVERTING,
                current_phase=f"Converting ({idx + 1}/{total_files})",
            )

            # Generate output filename using chapter info
            metadata = request.metadata.model_copy()
            # Set chapter number for individual files
            if metadata.chapter_info.chapter_start is None:
                metadata.chapter_info.chapter_start = float(idx + 1)

            # Format filename using the naming pattern
            chapter_str = metadata.chapter_info.format_chapter_string() or str(idx + 1)
            filename = (
                request.naming_pattern.replace("{series}", metadata.series or metadata.title)
                .replace("{title}", metadata.title)
                .replace("{chapter}", chapter_str)
                .replace("{volume}", f"Vol. {metadata.chapter_info.volume}" if metadata.chapter_info.volume else "")
                .replace("{index:03d}", f"{idx + 1:03d}")
                .replace("{index}", str(idx + 1))
            )
            # Sanitize filename
            filename = "".join(
                c for c in filename if c.isalnum() or c in " -_."
            ).strip()

            # Convert using thread pool to avoid blocking event loop
            # The converter uses parallel image processing internally
            created_files = await asyncio.to_thread(
                converter.convert,
                images,
                metadata,
                output_dir,
                request.output_format,
                filename,
            )

            output_files.extend([f.name for f in created_files])

        _update_job(
            job_id,
            progress=50 + ((idx + 1) / total_files) * 50,
        )

    _update_job(
        job_id,
        status=ConversionStatus.COMPLETED,
        progress=100.0,
        output_files=output_files,
        completed_at=datetime.now(),
        current_file=None,
        current_phase="Completed",
    )


async def _run_merged_conversion(
    job_id: str,
    request: ConversionRequest,
    file_ids: list[str],
    session_dir: Path,
    output_dir: Path,
    extractor: ExtractorService,
    converter: ConverterService,
    merger: MergerService,
) -> None:
    """Merge all files into one (or multiple if > max size)."""
    _update_job(
        job_id,
        status=ConversionStatus.EXTRACTING,
        current_phase="Extracting files",
    )

    total_files = len(file_ids)
    all_image_lists: list[list[Path]] = []

    # Use a persistent temp directory for all extractions
    with tempfile.TemporaryDirectory() as temp_base:
        temp_base_path = Path(temp_base)

        # Phase 1: Extract all files
        for idx, file_id in enumerate(file_ids):
            # Find the file or image folder
            file_path = _find_file_by_id(session_dir, file_id)

            if not file_path:
                _update_job(
                    job_id,
                    status=ConversionStatus.FAILED,
                    error=f"File not found: {file_id}",
                    current_phase="Error",
                )
                return

            _update_job(
                job_id,
                current_file=file_path.name,
                current_phase=f"Extracting ({idx + 1}/{total_files})",
                progress=(idx / total_files) * 30,
            )

            # Extract to unique subdirectory using thread pool
            extract_dir = temp_base_path / f"extract_{idx:04d}"
            images = await asyncio.to_thread(
                extractor.extract, file_path, extract_dir, request.epub_mode
            )

            if not images:
                _update_job(
                    job_id,
                    status=ConversionStatus.FAILED,
                    error=f"No images found in: {file_path.name}",
                    current_phase="Error",
                )
                return

            all_image_lists.append(images)

        # Phase 2: Merge and calculate splits
        _update_job(
            job_id,
            status=ConversionStatus.MERGING,
            current_phase="Merging files",
            progress=35,
        )

        max_size = request.max_output_size_mb * 1024 * 1024
        # Use thread pool for merger to avoid blocking event loop
        image_batches = await asyncio.to_thread(
            merger.merge_images, all_image_lists, max_size
        )
        split_count = len(image_batches)

        _update_job(
            job_id,
            split_count=split_count,
            current_phase=f"Creating {split_count} file(s)",
            progress=40,
        )

        # Phase 3: Convert batches
        _update_job(
            job_id,
            status=ConversionStatus.CONVERTING,
        )

        # Generate base filename using chapter info
        chapter_str = request.metadata.chapter_info.format_chapter_string() or "1"
        filename = (
            request.naming_pattern.replace("{series}", request.metadata.series or request.metadata.title)
            .replace("{title}", request.metadata.title)
            .replace("{chapter}", chapter_str)
            .replace("{volume}", f"Vol. {request.metadata.chapter_info.volume}" if request.metadata.chapter_info.volume else "")
            .replace("{index:03d}", "001")
            .replace("{index}", "1")
        )
        filename = "".join(
            c for c in filename if c.isalnum() or c in " -_."
        ).strip()

        # Convert with auto-splitting using thread pool
        # The converter uses parallel image processing internally
        output_files = await asyncio.to_thread(
            converter.convert_merged,
            image_batches,
            request.metadata,
            output_dir,
            request.output_format,
            filename,
        )

        _update_job(
            job_id,
            status=ConversionStatus.COMPLETED,
            progress=100.0,
            output_files=[f.name for f in output_files],
            completed_at=datetime.now(),
            current_file=None,
            current_phase="Completed",
        )


@router.post("", response_model=ConversionJob)
async def start_conversion(
    request: ConversionRequest,
    background_tasks: BackgroundTasks,
    file_manager: FileManager = Depends(get_file_manager),
    extractor: ExtractorService = Depends(get_extractor),
    merger: MergerService = Depends(get_merger),
) -> ConversionJob:
    """
    Start a conversion job.

    The conversion runs in the background. Use the status endpoint
    to poll for progress and completion.

    Features:
    - Individual file conversion or merged output
    - Auto-splitting at configurable size threshold
    - EPUB input support with extraction mode
    - Custom file ordering for merge
    - Device-specific image processing (upscaling, spread detection)
    - Chapter range support for merged files
    """
    # Validate session exists
    session_dir = file_manager.get_session_dir(request.session_id)
    if not session_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {request.session_id}",
        )

    # Validate files exist (handles both regular files and image folders)
    available_ids: set[str] = set()
    for f in session_dir.iterdir():
        if f.is_file():
            available_ids.add(f.stem)
        elif f.is_dir() and f.name.endswith("_images"):
            # Extract ID from folder name like "{file_id}_images"
            available_ids.add(f.name[:-7])  # Remove "_images" suffix

    all_file_ids = set(request.file_ids)
    if request.file_order:
        all_file_ids.update(request.file_order)

    for file_id in all_file_ids:
        if file_id not in available_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {file_id}",
            )

    # Create job
    job_id = str(uuid.uuid4())
    job = ConversionJob(
        job_id=job_id,
        session_id=request.session_id,
        status=ConversionStatus.PENDING,
        current_phase="Starting",
        split_count=1,
    )
    jobs[job_id] = job

    # Start background task
    background_tasks.add_task(
        _run_conversion,
        job_id,
        request,
        file_manager,
        extractor,
        merger,
    )

    return job


@router.get("/{job_id}/status", response_model=ConversionJob)
async def get_job_status(job_id: str) -> ConversionJob:
    """Get the status of a conversion job."""
    if job_id not in jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}",
        )

    return jobs[job_id]


@router.get("", response_model=list[ConversionJob])
async def list_jobs(session_id: str | None = None) -> list[ConversionJob]:
    """List all jobs, optionally filtered by session."""
    if session_id:
        return [j for j in jobs.values() if j.session_id == session_id]
    return list(jobs.values())
