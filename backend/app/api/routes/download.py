"""Download API routes."""

import io
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse

from app.api.deps import get_file_manager
from app.services.file_manager import FileManager

router = APIRouter(prefix="/download", tags=["download"])


@router.get("/{session_id}/{filename}")
async def download_file(
    session_id: str,
    filename: str,
    file_manager: FileManager = Depends(get_file_manager),
) -> FileResponse:
    """
    Download a single converted file.

    The filename should include the extension (e.g., "Manga - Chapter 001.epub").
    """
    file_path = file_manager.get_output_file(session_id, filename)

    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {filename}",
        )

    # Determine media type
    extension = file_path.suffix.lower()
    media_types = {
        ".epub": "application/epub+zip",
        ".mobi": "application/x-mobipocket-ebook",
    }
    media_type = media_types.get(extension, "application/octet-stream")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/{session_id}/all")
async def download_all(
    session_id: str,
    file_manager: FileManager = Depends(get_file_manager),
) -> StreamingResponse:
    """
    Download all converted files as a ZIP archive.

    Returns a ZIP file containing all EPUB and MOBI files from the session.
    """
    output_dir = file_manager.output_dir / session_id

    if not output_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    # Collect files to zip
    files_to_zip: list[Path] = []
    for ext in [".epub", ".mobi"]:
        files_to_zip.extend(output_dir.glob(f"*{ext}"))

    if not files_to_zip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No converted files found",
        )

    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in files_to_zip:
            zf.write(file_path, file_path.name)

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="manga-kindle-{session_id[:8]}.zip"',
        },
    )


@router.get("/{session_id}")
async def list_downloads(
    session_id: str,
    file_manager: FileManager = Depends(get_file_manager),
) -> list[dict]:
    """List all available downloads for a session."""
    output_dir = file_manager.output_dir / session_id

    if not output_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    downloads = []
    for file_path in output_dir.iterdir():
        if file_path.suffix.lower() in {".epub", ".mobi"}:
            downloads.append({
                "filename": file_path.name,
                "size": file_path.stat().st_size,
                "format": file_path.suffix.lower().lstrip("."),
                "download_url": f"/api/download/{session_id}/{file_path.name}",
            })

    return downloads
