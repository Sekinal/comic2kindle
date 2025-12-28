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

ALLOWED_ARCHIVE_EXTENSIONS = {".cbr", ".cbz", ".zip", ".rar", ".epub"}
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff", ".tif"}
ALLOWED_EXTENSIONS = ALLOWED_ARCHIVE_EXTENSIONS | ALLOWED_IMAGE_EXTENSIONS


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
    Upload manga files (CBR/CBZ/EPUB) or image files for conversion.

    Supports:
    - Archive files: CBR, CBZ, ZIP, RAR, EPUB
    - Image files: PNG, JPG, JPEG, WEBP, GIF, BMP, TIFF

    When images are uploaded, they are grouped into a single "folder" entry.
    Creates a new session and stores the uploaded files.
    Returns the session ID and file information.
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided",
        )

    # Separate archives and images
    archive_files: list[UploadFile] = []
    image_files: list[UploadFile] = []

    for f in files:
        if f.filename:
            ext = "." + f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
            if ext in ALLOWED_ARCHIVE_EXTENSIONS:
                archive_files.append(f)
            elif ext in ALLOWED_IMAGE_EXTENSIONS:
                image_files.append(f)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid file type: {f.filename}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
                )

    # Create session
    session_id = file_manager.create_session()
    saved_files: list[FileInfo] = []
    order_counter = 0

    try:
        # Handle archive files
        for upload_file in archive_files:
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
            file_info.order = order_counter
            order_counter += 1

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

        # Handle image files - group them into a single "folder" entry
        if image_files:
            import uuid
            from datetime import datetime
            from PIL import Image
            import io

            folder_id = str(uuid.uuid4())[:8]
            images_dir = file_manager.get_session_dir(session_id) / f"{folder_id}_images"
            images_dir.mkdir(parents=True, exist_ok=True)

            total_size = 0
            first_image_path = None

            # Sort images by filename for initial order
            sorted_images = sorted(image_files, key=lambda f: f.filename or "")

            for idx, img_file in enumerate(sorted_images):
                if not img_file.filename:
                    continue

                content = await img_file.read()
                total_size += len(content)

                # Save with ordered filename to preserve order
                ext = "." + img_file.filename.rsplit(".", 1)[-1].lower()
                ordered_filename = f"{idx:04d}_{img_file.filename}"
                img_path = images_dir / ordered_filename
                img_path.write_bytes(content)

                if first_image_path is None:
                    first_image_path = img_path

            # Generate preview from first image
            preview_url = None
            if first_image_path:
                preview_path = settings.preview_dir / session_id / f"{folder_id}.jpg"
                preview_path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    with Image.open(first_image_path) as img:
                        img.thumbnail((settings.preview_thumbnail_width, settings.preview_thumbnail_height))
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                        img.save(preview_path, "JPEG", quality=85)
                    preview_url = f"/api/upload/{session_id}/{folder_id}/preview"
                except Exception:
                    pass

            # Create a single FileInfo for the image folder
            folder_name = "Uploaded Images"
            if sorted_images and sorted_images[0].filename:
                # Try to extract a common prefix from filenames
                first_name = sorted_images[0].filename.rsplit(".", 1)[0]
                folder_name = first_name if first_name else "Uploaded Images"

            file_info = FileInfo(
                id=folder_id,
                original_name=folder_name,
                size=total_size,
                page_count=len(image_files),
                extension=".images",
                input_format=InputFormat.IMAGES,
                preview_url=preview_url,
                order=order_counter,
                estimated_output_size=int(total_size * 0.8),
                uploaded_at=datetime.now(),
            )
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
    order = 0

    for item in session_dir.iterdir():
        # Handle archive files
        if item.is_file() and item.suffix.lower() in ALLOWED_ARCHIVE_EXTENSIONS:
            file_id = item.stem
            preview_path = settings.preview_dir / session_id / f"{file_id}.jpg"

            files.append(
                FileInfo(
                    id=file_id,
                    original_name=item.name,
                    size=item.stat().st_size,
                    page_count=extractor.count_pages(item),
                    extension=item.suffix.lower(),
                    input_format=_get_input_format(item.suffix),
                    preview_url=f"/api/upload/{session_id}/{file_id}/preview" if preview_path.exists() else None,
                    order=order,
                    estimated_output_size=int(item.stat().st_size * 0.8),
                )
            )
            order += 1

        # Handle image folders
        elif item.is_dir() and item.name.endswith("_images"):
            file_id = item.name[:-7]  # Remove "_images" suffix
            preview_path = settings.preview_dir / session_id / f"{file_id}.jpg"

            # Calculate total size and page count
            total_size = sum(f.stat().st_size for f in item.iterdir() if f.is_file())
            page_count = sum(1 for f in item.iterdir() if f.suffix.lower() in ALLOWED_IMAGE_EXTENSIONS)

            files.append(
                FileInfo(
                    id=file_id,
                    original_name="Uploaded Images",
                    size=total_size,
                    page_count=page_count,
                    extension=".images",
                    input_format=InputFormat.IMAGES,
                    preview_url=f"/api/upload/{session_id}/{file_id}/preview" if preview_path.exists() else None,
                    order=order,
                    estimated_output_size=int(total_size * 0.8),
                )
            )
            order += 1

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

    # Get all files and image folders
    all_items: dict[str, Path] = {}
    for item in session_dir.iterdir():
        if item.is_file() and item.suffix.lower() in ALLOWED_ARCHIVE_EXTENSIONS:
            all_items[item.stem] = item
        elif item.is_dir() and item.name.endswith("_images"):
            all_items[item.name[:-7]] = item  # Remove "_images" suffix

    # Validate all file IDs exist
    for file_id in order_update.file_order:
        if file_id not in all_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File not found: {file_id}",
            )

    # Create ordered file list
    ordered_files: list[FileInfo] = []
    for order, file_id in enumerate(order_update.file_order):
        item_path = all_items[file_id]
        preview_path = settings.preview_dir / session_id / f"{file_id}.jpg"

        if item_path.is_dir():
            # Image folder
            total_size = sum(f.stat().st_size for f in item_path.iterdir() if f.is_file())
            page_count = sum(1 for f in item_path.iterdir() if f.suffix.lower() in ALLOWED_IMAGE_EXTENSIONS)
            ordered_files.append(
                FileInfo(
                    id=file_id,
                    original_name="Uploaded Images",
                    size=total_size,
                    page_count=page_count,
                    extension=".images",
                    input_format=InputFormat.IMAGES,
                    preview_url=f"/api/upload/{session_id}/{file_id}/preview" if preview_path.exists() else None,
                    order=order,
                    estimated_output_size=int(total_size * 0.8),
                )
            )
        else:
            # Archive file
            ordered_files.append(
                FileInfo(
                    id=file_id,
                    original_name=item_path.name,
                    size=item_path.stat().st_size,
                    page_count=extractor.count_pages(item_path),
                    extension=item_path.suffix.lower(),
                    input_format=_get_input_format(item_path.suffix),
                    preview_url=f"/api/upload/{session_id}/{file_id}/preview" if preview_path.exists() else None,
                    order=order,
                    estimated_output_size=int(item_path.stat().st_size * 0.8),
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

    # Get all files and image folders with their IDs
    items: list[tuple[str, str]] = []  # List of (file_id, display_name)
    for item in session_dir.iterdir():
        if item.is_file() and item.suffix.lower() in ALLOWED_ARCHIVE_EXTENSIONS:
            items.append((item.stem, item.name))
        elif item.is_dir() and item.name.endswith("_images"):
            file_id = item.name[:-7]  # Remove "_images" suffix
            items.append((file_id, "Uploaded Images"))

    if not items:
        return []

    filenames = [name for _, name in items]

    # Get suggested order indices
    order_indices = filename_parser.suggest_order(filenames)

    # Return file IDs in suggested order
    return [items[idx][0] for idx in order_indices]


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


@router.delete("/{session_id}/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    session_id: str,
    file_id: str,
    file_manager: FileManager = Depends(get_file_manager),
) -> None:
    """
    Delete a single file from a session.

    Args:
        session_id: The session ID
        file_id: The file ID to delete

    Raises:
        404: If session or file not found
    """
    session_dir = file_manager.get_session_dir(session_id)

    if not session_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    # Find and delete the file or image folder
    import shutil as shutil_delete

    item_found = False
    for item in session_dir.iterdir():
        # Check for regular file
        if item.is_file() and item.stem == file_id:
            item.unlink()
            item_found = True
            break
        # Check for image folder
        elif item.is_dir() and item.name == f"{file_id}_images":
            shutil_delete.rmtree(item)
            item_found = True
            break

    if not item_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {file_id}",
        )

    # Also delete the preview if it exists
    preview_path = settings.preview_dir / session_id / f"{file_id}.jpg"
    if preview_path.exists():
        preview_path.unlink()
