"""Archive extraction service for CBR/CBZ/EPUB files."""

import shutil
import subprocess
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Optional

from PIL import Image

from app.config import settings
from app.models.schemas import EpubExtractionMode

# Image extensions to look for
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}


class ExtractorService:
    """Extracts images from CBR/CBZ/EPUB archives."""

    def __init__(self, epub_reader: Optional["EpubReaderService"] = None) -> None:
        self._epub_reader = epub_reader

    @property
    def epub_reader(self) -> "EpubReaderService":
        """Lazy load epub reader to avoid circular imports."""
        if self._epub_reader is None:
            from app.services.epub_reader import EpubReaderService

            self._epub_reader = EpubReaderService()
        return self._epub_reader

    def extract(
        self,
        archive_path: Path,
        output_dir: Path,
        epub_mode: EpubExtractionMode = EpubExtractionMode.IMAGES_ONLY,
    ) -> list[Path]:
        """
        Extract images from an archive file.

        Args:
            archive_path: Path to the CBR/CBZ/EPUB file
            output_dir: Directory to extract images to
            epub_mode: How to handle EPUB files

        Returns:
            List of paths to extracted images, sorted by name
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        extension = archive_path.suffix.lower()

        if extension in {".cbz", ".zip"}:
            return self._extract_zip(archive_path, output_dir)
        elif extension in {".cbr", ".rar"}:
            return self._extract_rar(archive_path, output_dir)
        elif extension == ".epub":
            return self._extract_epub(archive_path, output_dir, epub_mode)
        else:
            raise ValueError(f"Unsupported archive format: {extension}")

    def _extract_epub(
        self,
        epub_path: Path,
        output_dir: Path,
        mode: EpubExtractionMode,
    ) -> list[Path]:
        """Extract images from an EPUB file."""
        if mode == EpubExtractionMode.IMAGES_ONLY:
            return self.epub_reader.extract_images(epub_path, output_dir)
        else:
            # Preserve structure mode - for now, still extract images
            # but could be extended to preserve HTML structure
            result = self.epub_reader.extract_with_structure(epub_path, output_dir)
            return list(result["images"].values())

    def _extract_zip(self, archive_path: Path, output_dir: Path) -> list[Path]:
        """Extract a ZIP/CBZ archive."""
        extracted_images: list[Path] = []

        with zipfile.ZipFile(archive_path, "r") as zf:
            for name in zf.namelist():
                # Skip directories and hidden files
                if name.endswith("/") or name.startswith("__MACOSX"):
                    continue

                file_ext = Path(name).suffix.lower()
                if file_ext in IMAGE_EXTENSIONS:
                    # Extract with a clean filename
                    clean_name = self._sanitize_filename(name)
                    target_path = output_dir / clean_name

                    with zf.open(name) as src:
                        target_path.write_bytes(src.read())

                    extracted_images.append(target_path)

        return self._sort_images(extracted_images)

    def _extract_rar(self, archive_path: Path, output_dir: Path) -> list[Path]:
        """Extract a RAR/CBR archive using unrar command."""
        extracted_images: list[Path] = []

        # Create temp directory for extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Try unrar-free first, then p7zip
            try:
                # Using unrar-free
                result = subprocess.run(
                    ["unrar-free", "-x", str(archive_path), str(temp_path)],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if result.returncode != 0:
                    raise subprocess.CalledProcessError(
                        result.returncode, "unrar-free"
                    )
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fallback to 7z
                try:
                    result = subprocess.run(
                        ["7z", "x", str(archive_path), f"-o{temp_path}", "-y"],
                        capture_output=True,
                        text=True,
                        timeout=300,
                    )
                    if result.returncode != 0:
                        raise ValueError(f"Failed to extract RAR: {result.stderr}")
                except FileNotFoundError:
                    raise ValueError(
                        "No RAR extraction tool available (tried unrar-free and 7z)"
                    )

            # Find and move images
            for file_path in temp_path.rglob("*"):
                if file_path.is_file():
                    file_ext = file_path.suffix.lower()
                    if file_ext in IMAGE_EXTENSIONS:
                        clean_name = self._sanitize_filename(file_path.name)
                        target_path = output_dir / clean_name
                        shutil.copy2(file_path, target_path)
                        extracted_images.append(target_path)

        return self._sort_images(extracted_images)

    def _sanitize_filename(self, name: str) -> str:
        """Create a clean filename from a potentially nested path."""
        # Get just the filename part
        filename = Path(name).name
        # Remove any problematic characters
        clean = "".join(c for c in filename if c.isalnum() or c in "._- ")
        return clean

    def _sort_images(self, images: list[Path]) -> list[Path]:
        """Sort images by their numeric value in filename."""

        def extract_number(path: Path) -> int:
            """Extract numeric value from filename for sorting."""
            name = path.stem
            # Remove common prefixes
            for prefix in ["page", "p", "img", "image", "_"]:
                name = name.lower().replace(prefix, "")

            # Extract digits
            digits = "".join(c for c in name if c.isdigit())
            return int(digits) if digits else 0

        return sorted(images, key=extract_number)

    def count_pages(self, archive_path: Path) -> int:
        """Count the number of image pages in an archive."""
        extension = archive_path.suffix.lower()

        if extension in {".cbz", ".zip"}:
            with zipfile.ZipFile(archive_path, "r") as zf:
                return sum(
                    1
                    for name in zf.namelist()
                    if Path(name).suffix.lower() in IMAGE_EXTENSIONS
                    and not name.startswith("__MACOSX")
                )
        elif extension in {".cbr", ".rar"}:
            # For RAR, we'd need to actually extract or use a library
            # Return 0 for now, actual count happens during extraction
            return 0
        elif extension == ".epub":
            return self.epub_reader.count_pages(archive_path)

        return 0

    def generate_preview(
        self,
        archive_path: Path,
        output_path: Path,
    ) -> Optional[Path]:
        """
        Generate a thumbnail preview of the first page.

        Args:
            archive_path: Path to the archive file
            output_path: Path to save the thumbnail

        Returns:
            Path to the generated thumbnail or None if failed
        """
        extension = archive_path.suffix.lower()
        first_image_data: Optional[bytes] = None

        try:
            if extension in {".cbz", ".zip"}:
                first_image_data = self._get_first_image_zip(archive_path)
            elif extension in {".cbr", ".rar"}:
                first_image_data = self._get_first_image_rar(archive_path)
            elif extension == ".epub":
                first_image_data = self.epub_reader.get_cover_image(archive_path)

            if first_image_data:
                return self._create_thumbnail(first_image_data, output_path)

        except Exception:
            pass

        return None

    def _get_first_image_zip(self, archive_path: Path) -> Optional[bytes]:
        """Get the first image from a ZIP archive."""
        with zipfile.ZipFile(archive_path, "r") as zf:
            names = sorted(
                [
                    n
                    for n in zf.namelist()
                    if Path(n).suffix.lower() in IMAGE_EXTENSIONS
                    and not n.startswith("__MACOSX")
                ]
            )
            if names:
                return zf.read(names[0])
        return None

    def _get_first_image_rar(self, archive_path: Path) -> Optional[bytes]:
        """Get the first image from a RAR archive."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Try to extract just one file
            try:
                subprocess.run(
                    ["7z", "x", str(archive_path), f"-o{temp_path}", "-y"],
                    capture_output=True,
                    timeout=60,
                )
            except Exception:
                return None

            # Find first image
            images = sorted(
                [
                    f
                    for f in temp_path.rglob("*")
                    if f.suffix.lower() in IMAGE_EXTENSIONS
                ]
            )
            if images:
                return images[0].read_bytes()

        return None

    def _create_thumbnail(
        self,
        image_data: bytes,
        output_path: Path,
    ) -> Path:
        """Create a thumbnail from image data."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with Image.open(BytesIO(image_data)) as img:
            # Convert to RGB if necessary
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Create thumbnail
            img.thumbnail(
                (settings.preview_thumbnail_width, settings.preview_thumbnail_height),
                Image.Resampling.LANCZOS,
            )

            # Save as JPEG
            img.save(output_path, format="JPEG", quality=80)

        return output_path
