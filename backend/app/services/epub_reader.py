"""EPUB file reading and extraction service."""

from pathlib import Path
from typing import Optional

import ebooklib
from ebooklib import epub
from PIL import Image

from app.config import settings
from app.models.schemas import MangaMetadata


# Image extensions to extract
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}


class EpubReaderService:
    """Reads and extracts content from EPUB files."""

    def extract_images(self, epub_path: Path, output_dir: Path) -> list[Path]:
        """
        Extract all images from an EPUB file (images_only mode).

        Args:
            epub_path: Path to the EPUB file
            output_dir: Directory to save extracted images

        Returns:
            List of paths to extracted images, sorted by order in EPUB
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        extracted_images: list[Path] = []

        try:
            book = epub.read_epub(str(epub_path), options={"ignore_ncx": True})
        except Exception as e:
            raise ValueError(f"Failed to read EPUB: {e}")

        # Get all image items
        image_items = list(book.get_items_of_type(ebooklib.ITEM_IMAGE))

        # Try to order images by spine if possible
        spine_order = self._get_image_order_from_spine(book)

        # Sort images: spine-referenced first, then alphabetically
        def sort_key(item: epub.EpubItem) -> tuple[int, str]:
            name = item.get_name()
            if name in spine_order:
                return (0, str(spine_order[name]).zfill(10))
            return (1, name)

        image_items.sort(key=sort_key)

        for idx, image_item in enumerate(image_items):
            file_name = Path(image_item.get_name()).name
            ext = Path(file_name).suffix.lower()

            # Skip non-image files
            if ext not in IMAGE_EXTENSIONS:
                continue

            # Create sequential filename
            output_name = f"page_{idx + 1:04d}{ext}"
            output_path = output_dir / output_name

            # Write image content
            content = image_item.get_content()
            output_path.write_bytes(content)
            extracted_images.append(output_path)

        return extracted_images

    def extract_with_structure(
        self, epub_path: Path, output_dir: Path
    ) -> dict[str, any]:
        """
        Extract EPUB preserving chapter structure.

        Args:
            epub_path: Path to the EPUB file
            output_dir: Directory to save extracted content

        Returns:
            Dict with chapters, images mapping, and metadata
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            book = epub.read_epub(str(epub_path), options={"ignore_ncx": True})
        except Exception as e:
            raise ValueError(f"Failed to read EPUB: {e}")

        result = {
            "chapters": [],
            "images": {},
            "metadata": self._extract_metadata(book),
        }

        # Extract images first and create a mapping
        images_dir = output_dir / "images"
        images_dir.mkdir(exist_ok=True)

        image_map: dict[str, Path] = {}
        for idx, image_item in enumerate(book.get_items_of_type(ebooklib.ITEM_IMAGE)):
            original_name = image_item.get_name()
            ext = Path(original_name).suffix.lower()
            if ext not in IMAGE_EXTENSIONS:
                continue

            output_name = f"image_{idx + 1:04d}{ext}"
            output_path = images_dir / output_name
            output_path.write_bytes(image_item.get_content())
            image_map[original_name] = output_path

        result["images"] = image_map

        # Extract chapters from spine
        for spine_item in book.spine:
            item_id = spine_item[0] if isinstance(spine_item, tuple) else spine_item
            item = book.get_item_with_id(item_id)

            if item and item.get_type() == ebooklib.ITEM_DOCUMENT:
                chapter_info = {
                    "id": item_id,
                    "title": getattr(item, "title", None) or item_id,
                    "file_name": item.get_name(),
                    "content": item.get_content().decode("utf-8", errors="ignore"),
                }
                result["chapters"].append(chapter_info)

        return result

    def count_pages(self, epub_path: Path) -> int:
        """
        Count the number of images in an EPUB.

        Args:
            epub_path: Path to the EPUB file

        Returns:
            Number of image pages
        """
        try:
            book = epub.read_epub(str(epub_path), options={"ignore_ncx": True})
            count = 0
            for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
                ext = Path(item.get_name()).suffix.lower()
                if ext in IMAGE_EXTENSIONS:
                    count += 1
            return count
        except Exception:
            return 0

    def get_metadata(self, epub_path: Path) -> MangaMetadata:
        """
        Extract metadata from an EPUB file.

        Args:
            epub_path: Path to the EPUB file

        Returns:
            MangaMetadata object with extracted info
        """
        try:
            book = epub.read_epub(str(epub_path), options={"ignore_ncx": True})
            return self._extract_metadata(book)
        except Exception:
            return MangaMetadata(title=epub_path.stem)

    def get_cover_image(self, epub_path: Path) -> Optional[bytes]:
        """
        Extract the cover image from an EPUB.

        Args:
            epub_path: Path to the EPUB file

        Returns:
            Cover image bytes or None if not found
        """
        try:
            book = epub.read_epub(str(epub_path), options={"ignore_ncx": True})

            # Try to get cover from metadata
            cover_id = None
            for meta in book.get_metadata("OPF", "cover"):
                if meta and len(meta) > 1:
                    cover_id = meta[1].get("content")
                    break

            if cover_id:
                item = book.get_item_with_id(cover_id)
                if item:
                    return item.get_content()

            # Fallback: get first image
            for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
                return item.get_content()

            return None
        except Exception:
            return None

    def _extract_metadata(self, book: epub.EpubBook) -> MangaMetadata:
        """Extract metadata from an EpubBook object."""
        title = book.get_metadata("DC", "title")
        title = title[0][0] if title else "Unknown"

        creator = book.get_metadata("DC", "creator")
        author = creator[0][0] if creator else ""

        description = book.get_metadata("DC", "description")
        description = description[0][0] if description else ""

        # Try to get series info
        series = ""
        series_index = 1

        # Check calibre metadata
        calibre_series = book.get_metadata("calibre", "series")
        if calibre_series:
            series = calibre_series[0][0]

        calibre_index = book.get_metadata("calibre", "series_index")
        if calibre_index:
            try:
                series_index = int(float(calibre_index[0][0]))
            except (ValueError, TypeError):
                pass

        return MangaMetadata(
            title=title,
            author=author,
            series=series,
            series_index=series_index,
            description=description,
        )

    def _get_image_order_from_spine(
        self, book: epub.EpubBook
    ) -> dict[str, int]:
        """
        Determine image order by analyzing spine documents.

        Returns a dict mapping image paths to their order number.
        """
        order: dict[str, int] = {}
        current_order = 0

        for spine_item in book.spine:
            item_id = spine_item[0] if isinstance(spine_item, tuple) else spine_item
            item = book.get_item_with_id(item_id)

            if item and item.get_type() == ebooklib.ITEM_DOCUMENT:
                content = item.get_content().decode("utf-8", errors="ignore")
                # Find image references in HTML
                import re

                for match in re.finditer(r'src=["\']([^"\']+)["\']', content):
                    img_path = match.group(1)
                    # Normalize path
                    if img_path not in order:
                        order[img_path] = current_order
                        current_order += 1

        return order
