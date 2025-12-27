"""File upload API routes."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.api.deps import (
    get_extractor,
    get_file_manager,
    get_filename_parser,
    get_merger,
)
from app.config import settings
from app.models.schemas import (
    FileInfo,
    FileOrderUpdate,
    FilenameParseResult,
    InputFormat,
    UploadResponse,
)
from app.services.extractor import ExtractorService
from app.services.file_manager import FileManager
from app.services.filename_parser import FilenameParserService
from app.services.merger import MergerService

router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_EXTENSIONS = {".cbr", ".cbz", ".zip", ".rar", ".epub"}


def _get_input_format(extension: str) -> InputFormat:
    """Map file extension to InputFormat enum."""
    mapping = {
        ".cbz": InputFormat.CBZ,
        ".zip": InputFormat.ZIP,
        ".cbr": InputFormat.CBR,
        ".rar": InputFormat.RAR,
        ".epub": InputFormat.EPUB,
    }
    return mapping.get(extension.lower(), InputFormat.CBZ)


@router.post("", response_model=UploadResponse)
async def upload_files(
    files: list[UploadFile] = File(...),
    file_manager: FileManager = Depends(get_file_manager),
    extractor: ExtractorService = Depends(get_extractor),
    filename_parser: FilenameParserService = Depends(get_filename_parser),
    merger: MergerService = Depends(get_merger),
) -> UploadResponse:
    """
    Upload manga files (CBR/CBZ/EPUB) for conversion.

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
        for order, upload_file in enumerate(files):
            if not upload_file.filename:
                continue

            content = await upload_file.read()
            file_info = await file_manager.save_file(
                session_id=session_id,
                filename=upload_file.filename,
                content=content,
            )

            # Set input format
            file_info.input_format = _get_input_format(file_info.extension)
            file_info.order = order

            # Count pages in the archive
            file_path = file_manager.get_file_path(
                session_id, file_info.id, file_info.extension
            )
            file_info.page_count = extractor.count_pages(file_path)

            # Generate preview thumbnail
            preview_path = settings.preview_dir / session_id / f"{file_info.id}.jpg"
            preview_result = extractor.generate_preview(file_path, preview_path)
            if preview_result:
                file_info.preview_url = f"/api/upload/{session_id}/{file_info.id}/preview"

            # Estimate output size (rough estimate based on file size)
            file_info.estimated_output_size = int(file_info.size * 0.8)

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
    for order, file_path in enumerate(file_manager.list_files(session_id)):
        if file_path.suffix.lower() in ALLOWED_EXTENSIONS:
            file_id = file_path.stem
            preview_path = settings.preview_dir / session_id / f"{file_id}.jpg"

            files.append(
                FileInfo(
                    id=file_id,
                    original_name=file_path.name,
                    size=file_path.stat().st_size,
                    page_count=extractor.count_pages(file_path),
                    extension=file_path.suffix.lower(),
                    input_format=_get_input_format(file_path.suffix),
                    preview_url=f"/api/upload/{session_id}/{file_id}/preview" if preview_path.exists() else None,
                    order=order,
                    estimated_output_size=int(file_path.stat().st_size * 0.8),
                )
            )

    return files


@router.patch("/{session_id}/order", response_model=list[FileInfo])
async def update_file_order(
    session_id: str,
    order_update: FileOrderUpdate,
    file_manager: FileManager = Depends(get_file_manager),
    extractor: ExtractorService = Depends(get_extractor),
) -> list[FileInfo]:
    """
    Update the order of files for merging.

    Args:
        session_id: The session ID
        order_update: New file order (list of file IDs)

    Returns:
        Updated list of files with new order values
    """
    session_dir = file_manager.get_session_dir(session_id)

    if not session_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    # Get all files
    all_files = {fp.stem: fp for fp in file_manager.list_files(session_id)}

    # Validate all file IDs exist
    for file_id in order_update.file_order:
        if file_id not in all_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File not found: {file_id}",
            )

    # Create ordered file list
    ordered_files: list[FileInfo] = []
    for order, file_id in enumerate(order_update.file_order):
        file_path = all_files[file_id]
        preview_path = settings.preview_dir / session_id / f"{file_id}.jpg"

        ordered_files.append(
            FileInfo(
                id=file_id,
                original_name=file_path.name,
                size=file_path.stat().st_size,
                page_count=extractor.count_pages(file_path),
                extension=file_path.suffix.lower(),
                input_format=_get_input_format(file_path.suffix),
                preview_url=f"/api/upload/{session_id}/{file_id}/preview" if preview_path.exists() else None,
                order=order,
                estimated_output_size=int(file_path.stat().st_size * 0.8),
            )
        )

    return ordered_files


@router.get("/{session_id}/{file_id}/preview")
async def get_file_preview(
    session_id: str,
    file_id: str,
    file_manager: FileManager = Depends(get_file_manager),
    extractor: ExtractorService = Depends(get_extractor),
) -> FileResponse:
    """
    Get a thumbnail preview of the first page of a file.

    Returns a JPEG image.
    """
    session_dir = file_manager.get_session_dir(session_id)

    if not session_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    preview_path = settings.preview_dir / session_id / f"{file_id}.jpg"

    # Generate preview if it doesn't exist
    if not preview_path.exists():
        # Find the original file
        for file_path in file_manager.list_files(session_id):
            if file_path.stem == file_id:
                extractor.generate_preview(file_path, preview_path)
                break

    if not preview_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preview not available for: {file_id}",
        )

    return FileResponse(
        path=preview_path,
        media_type="image/jpeg",
        filename=f"{file_id}_preview.jpg",
    )


@router.get("/{session_id}/{file_id}/parse", response_model=FilenameParseResult)
async def parse_filename(
    session_id: str,
    file_id: str,
    file_manager: FileManager = Depends(get_file_manager),
    filename_parser: FilenameParserService = Depends(get_filename_parser),
) -> FilenameParseResult:
    """
    Parse a file's name to extract series, chapter, and volume info.

    Useful for auto-populating metadata fields.
    """
    session_dir = file_manager.get_session_dir(session_id)

    if not session_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    # Find the file
    for file_path in file_manager.list_files(session_id):
        if file_path.stem == file_id:
            return filename_parser.parse(file_path.name)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"File not found: {file_id}",
    )


@router.post("/{session_id}/suggest-order", response_model=list[str])
async def suggest_file_order(
    session_id: str,
    file_manager: FileManager = Depends(get_file_manager),
    filename_parser: FilenameParserService = Depends(get_filename_parser),
) -> list[str]:
    """
    Suggest a reading order for files based on their filenames.

    Returns ordered list of file IDs.
    """
    session_dir = file_manager.get_session_dir(session_id)

    if not session_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    files = list(file_manager.list_files(session_id))
    filenames = [f.name for f in files]

    # Get suggested order indices
    order_indices = filename_parser.suggest_order(filenames)

    # Return file IDs in suggested order
    return [files[idx].stem for idx in order_indices]


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

    # Also cleanup previews
    preview_dir = settings.preview_dir / session_id
    if preview_dir.exists():
        import shutil
        shutil.rmtree(preview_dir)
