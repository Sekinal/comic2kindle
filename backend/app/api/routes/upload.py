"""File upload API routes."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.deps import get_extractor, get_file_manager
from app.models.schemas import FileInfo, UploadResponse
from app.services.extractor import ExtractorService
from app.services.file_manager import FileManager

router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_EXTENSIONS = {".cbr", ".cbz", ".zip", ".rar"}


@router.post("", response_model=UploadResponse)
async def upload_files(
    files: list[UploadFile] = File(...),
    file_manager: FileManager = Depends(get_file_manager),
    extractor: ExtractorService = Depends(get_extractor),
) -> UploadResponse:
    """
    Upload manga files (CBR/CBZ) for conversion.

    Creates a new session and stores the uploaded files.
    Returns the session ID and file information.
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided",
        )

    # Validate file extensions
    for f in files:
        if f.filename:
            ext = "." + f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
            if ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid file type: {f.filename}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
                )

    # Create session
    session_id = file_manager.create_session()
    saved_files: list[FileInfo] = []

    try:
        for upload_file in files:
            if not upload_file.filename:
                continue

            content = await upload_file.read()
            file_info = await file_manager.save_file(
                session_id=session_id,
                filename=upload_file.filename,
                content=content,
            )

            # Count pages in the archive
            file_path = file_manager.get_file_path(
                session_id, file_info.id, file_info.extension
            )
            file_info.page_count = extractor.count_pages(file_path)

            saved_files.append(file_info)

    except Exception as e:
        # Cleanup on failure
        file_manager.cleanup_session(session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save files: {str(e)}",
        )

    return UploadResponse(
        session_id=session_id,
        files=saved_files,
        message=f"Successfully uploaded {len(saved_files)} file(s)",
    )


@router.get("/{session_id}", response_model=list[FileInfo])
async def list_session_files(
    session_id: str,
    file_manager: FileManager = Depends(get_file_manager),
    extractor: ExtractorService = Depends(get_extractor),
) -> list[FileInfo]:
    """List all files in a session."""
    session_dir = file_manager.get_session_dir(session_id)

    if not session_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    files: list[FileInfo] = []
    for file_path in file_manager.list_files(session_id):
        if file_path.suffix.lower() in ALLOWED_EXTENSIONS:
            file_id = file_path.stem
            files.append(
                FileInfo(
                    id=file_id,
                    original_name=file_path.name,
                    size=file_path.stat().st_size,
                    page_count=extractor.count_pages(file_path),
                    extension=file_path.suffix.lower(),
                )
            )

    return files


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    file_manager: FileManager = Depends(get_file_manager),
) -> None:
    """Delete a session and all its files."""
    session_dir = file_manager.get_session_dir(session_id)

    if not session_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    file_manager.cleanup_session(session_id)
