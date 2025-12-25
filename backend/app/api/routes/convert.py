"""Conversion API routes."""

import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.api.deps import get_converter, get_extractor, get_file_manager
from app.models.schemas import (
    ConversionJob,
    ConversionRequest,
    ConversionStatus,
)
from app.services.converter import ConverterService
from app.services.extractor import ExtractorService
from app.services.file_manager import FileManager

router = APIRouter(prefix="/convert", tags=["convert"])

# In-memory job storage (in production, use Redis or database)
jobs: dict[str, ConversionJob] = {}


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
    converter: ConverterService,
) -> None:
    """
    Background task to run the conversion process.

    This runs after the response is sent to the client.
    """
    try:
        _update_job(job_id, status=ConversionStatus.EXTRACTING)

        output_dir = file_manager.get_output_dir(request.session_id)
        output_files: list[str] = []
        total_files = len(request.file_ids)

        for idx, file_id in enumerate(request.file_ids):
            # Find the file
            session_dir = file_manager.get_session_dir(request.session_id)
            file_path = None

            for f in session_dir.iterdir():
                if f.stem == file_id:
                    file_path = f
                    break

            if not file_path:
                _update_job(
                    job_id,
                    status=ConversionStatus.FAILED,
                    error=f"File not found: {file_id}",
                )
                return

            _update_job(
                job_id,
                current_file=file_path.name,
                progress=(idx / total_files) * 50,  # First 50% is extraction
            )

            # Extract images to temp directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                images = extractor.extract(file_path, temp_path)

                if not images:
                    _update_job(
                        job_id,
                        status=ConversionStatus.FAILED,
                        error=f"No images found in: {file_path.name}",
                    )
                    return

                _update_job(job_id, status=ConversionStatus.CONVERTING)

                # Generate output filename
                metadata = request.metadata.model_copy()
                metadata.series_index = idx + 1

                filename = request.naming_pattern.format(
                    series=metadata.series or metadata.title,
                    title=metadata.title,
                    index=metadata.series_index,
                )
                # Sanitize filename
                filename = "".join(
                    c for c in filename if c.isalnum() or c in " -_."
                ).strip()

                # Convert
                created_files = converter.convert(
                    images=images,
                    metadata=metadata,
                    output_dir=output_dir,
                    output_format=request.output_format,
                    filename=filename,
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
        )

    except Exception as e:
        _update_job(
            job_id,
            status=ConversionStatus.FAILED,
            error=str(e),
        )


@router.post("", response_model=ConversionJob)
async def start_conversion(
    request: ConversionRequest,
    background_tasks: BackgroundTasks,
    file_manager: FileManager = Depends(get_file_manager),
    extractor: ExtractorService = Depends(get_extractor),
    converter: ConverterService = Depends(get_converter),
) -> ConversionJob:
    """
    Start a conversion job.

    The conversion runs in the background. Use the status endpoint
    to poll for progress and completion.
    """
    # Validate session exists
    session_dir = file_manager.get_session_dir(request.session_id)
    if not session_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {request.session_id}",
        )

    # Validate files exist
    available_files = {f.stem for f in session_dir.iterdir()}
    for file_id in request.file_ids:
        if file_id not in available_files:
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
    )
    jobs[job_id] = job

    # Start background task
    background_tasks.add_task(
        _run_conversion,
        job_id,
        request,
        file_manager,
        extractor,
        converter,
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
