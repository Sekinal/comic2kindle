"""Archive extraction service for CBR/CBZ files."""

import zipfile
from pathlib import Path
from typing import Optional
import tempfile
import subprocess
import shutil

# Image extensions to look for
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}


class ExtractorService:
    """Extracts images from CBR/CBZ archives."""

    def extract(self, archive_path: Path, output_dir: Path) -> list[Path]:
        """
        Extract images from an archive file.

        Args:
            archive_path: Path to the CBR/CBZ file
            output_dir: Directory to extract images to

        Returns:
            List of paths to extracted images, sorted by name
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        extension = archive_path.suffix.lower()

        if extension in {".cbz", ".zip"}:
            return self._extract_zip(archive_path, output_dir)
        elif extension in {".cbr", ".rar"}:
            return self._extract_rar(archive_path, output_dir)
        else:
            raise ValueError(f"Unsupported archive format: {extension}")

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

        return 0
