"""EPUB/MOBI converter service."""

import subprocess
import uuid
from pathlib import Path
from typing import Optional

from ebooklib import epub
from PIL import Image

from app.config import settings
from app.models.schemas import MangaMetadata, OutputFormat


class ConverterService:
    """Converts images to EPUB/MOBI ebooks."""

    def __init__(self) -> None:
        self.max_width = settings.max_image_width
        self.max_height = settings.max_image_height
        self.quality = settings.image_quality

    def create_epub(
        self,
        images: list[Path],
        metadata: MangaMetadata,
        output_path: Path,
        cover_image: Optional[Path] = None,
    ) -> Path:
        """
        Create an EPUB from a list of images.

        Args:
            images: List of image paths in reading order
            metadata: Manga metadata
            output_path: Path to save the EPUB
            cover_image: Optional custom cover image

        Returns:
            Path to the created EPUB file
        """
        book = epub.EpubBook()

        # Set metadata
        book.set_identifier(str(uuid.uuid4()))
        book.set_title(metadata.title)
        book.set_language("en")

        if metadata.author:
            book.add_author(metadata.author)

        # Add series metadata
        if metadata.series:
            book.add_metadata("DC", "series", metadata.series)
            book.add_metadata(
                "calibre", "series_index", str(metadata.series_index)
            )

        if metadata.description:
            book.add_metadata("DC", "description", metadata.description)

        # Set reading direction for manga (right-to-left)
        book.set_direction("rtl")

        # Process and add cover
        cover_path = cover_image or (images[0] if images else None)
        if cover_path:
            cover_content = self._process_image(cover_path)
            book.set_cover("cover.jpg", cover_content)

        # Create chapters (one per page)
        chapters = []
        spine = ["nav"]

        for i, image_path in enumerate(images):
            page_num = i + 1
            image_content = self._process_image(image_path)

            # Create image item
            image_name = f"page_{page_num:04d}.jpg"
            image_item = epub.EpubItem(
                uid=f"image_{page_num}",
                file_name=f"images/{image_name}",
                media_type="image/jpeg",
                content=image_content,
            )
            book.add_item(image_item)

            # Create HTML page for the image
            chapter = epub.EpubHtml(
                title=f"Page {page_num}",
                file_name=f"page_{page_num:04d}.xhtml",
                lang="en",
            )
            chapter.content = f"""<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Page {page_num}</title>
    <style type="text/css">
        body {{ margin: 0; padding: 0; text-align: center; }}
        img {{ max-width: 100%; max-height: 100%; height: auto; }}
    </style>
</head>
<body>
    <img src="images/{image_name}" alt="Page {page_num}"/>
</body>
</html>"""

            book.add_item(chapter)
            chapters.append(chapter)
            spine.append(chapter)

        # Add navigation
        book.toc = chapters
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # Set spine
        book.spine = spine

        # Add CSS
        style = """
        @page {
            margin: 0;
            padding: 0;
        }
        body {
            margin: 0;
            padding: 0;
            text-align: center;
            background-color: #000;
        }
        img {
            max-width: 100%;
            max-height: 100vh;
            object-fit: contain;
        }
        """
        css = epub.EpubItem(
            uid="style",
            file_name="style/main.css",
            media_type="text/css",
            content=style.encode("utf-8"),
        )
        book.add_item(css)

        # Write EPUB
        output_path.parent.mkdir(parents=True, exist_ok=True)
        epub.write_epub(str(output_path), book)

        return output_path

    def convert_to_mobi(self, epub_path: Path, output_path: Path) -> Path:
        """
        Convert EPUB to MOBI using Calibre's ebook-convert.

        Args:
            epub_path: Path to the EPUB file
            output_path: Path to save the MOBI file

        Returns:
            Path to the created MOBI file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Use env -i with clean environment to bypass Calibre's msgpack bug
            # Calibre uses its own bundled Python and gets confused by venv paths
            import os

            home = os.environ.get("HOME", "/tmp")
            cmd = (
                f'env -i PATH=/usr/bin:/bin HOME="{home}" LC_ALL=C '
                f'ebook-convert "{epub_path}" "{output_path}" '
                f'--output-profile=kindle --no-inline-toc --mobi-file-type=both'
            )

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
            )

            if result.returncode != 0 or not output_path.exists():
                raise ValueError(f"MOBI conversion failed: {result.stderr}")

            return output_path

        except subprocess.TimeoutExpired:
            raise ValueError("MOBI conversion timed out")
        except FileNotFoundError:
            raise ValueError(
                "Calibre ebook-convert not found. Please install Calibre."
            )

    def convert(
        self,
        images: list[Path],
        metadata: MangaMetadata,
        output_dir: Path,
        output_format: OutputFormat,
        filename: str,
        cover_image: Optional[Path] = None,
    ) -> list[Path]:
        """
        Convert images to the specified format(s).

        Args:
            images: List of image paths
            metadata: Manga metadata
            output_dir: Directory to save output files
            output_format: EPUB, MOBI, or BOTH
            filename: Base filename (without extension)
            cover_image: Optional custom cover image

        Returns:
            List of created file paths
        """
        output_files: list[Path] = []

        # Always create EPUB first
        epub_path = output_dir / f"{filename}.epub"
        self.create_epub(images, metadata, epub_path, cover_image)

        if output_format in {OutputFormat.EPUB, OutputFormat.BOTH}:
            output_files.append(epub_path)

        # Convert to MOBI if needed
        if output_format in {OutputFormat.MOBI, OutputFormat.BOTH}:
            mobi_path = output_dir / f"{filename}.mobi"
            try:
                self.convert_to_mobi(epub_path, mobi_path)
                output_files.append(mobi_path)
                # Clean up EPUB if only MOBI was requested and MOBI succeeded
                if output_format == OutputFormat.MOBI:
                    epub_path.unlink(missing_ok=True)
                    output_files.remove(epub_path)
            except ValueError as e:
                # MOBI failed - keep EPUB as fallback (modern Kindles support EPUB)
                print(f"Warning: MOBI conversion failed, using EPUB instead: {e}")
                if epub_path not in output_files:
                    output_files.append(epub_path)

        return output_files

    def convert_merged(
        self,
        image_batches: list[list[Path]],
        metadata: MangaMetadata,
        output_dir: Path,
        output_format: OutputFormat,
        filename: str,
        cover_image: Optional[Path] = None,
    ) -> list[Path]:
        """
        Convert multiple image batches to EPUB(s), handling auto-splitting.

        Args:
            image_batches: List of image batches (one per output file)
            metadata: Manga metadata
            output_dir: Directory to save output files
            output_format: EPUB, MOBI, or BOTH
            filename: Base filename (without extension)
            cover_image: Optional custom cover image

        Returns:
            List of created file paths
        """
        output_files: list[Path] = []
        total_parts = len(image_batches)

        for part_num, images in enumerate(image_batches, start=1):
            # Modify metadata for multi-part books
            part_metadata = metadata.model_copy()
            if total_parts > 1:
                part_metadata.title = f"{metadata.title} (Part {part_num}/{total_parts})"

            # Generate filename with part number if needed
            if total_parts > 1:
                part_filename = f"{filename}_part{part_num:02d}"
            else:
                part_filename = filename

            # Use first image as cover for first part, or provided cover
            part_cover = cover_image if part_num == 1 else None
            if part_cover is None and images:
                part_cover = images[0]

            # Convert this batch
            batch_files = self.convert(
                images=images,
                metadata=part_metadata,
                output_dir=output_dir,
                output_format=output_format,
                filename=part_filename,
                cover_image=part_cover,
            )
            output_files.extend(batch_files)

        return output_files

    def _process_image(self, image_path: Path) -> bytes:
        """Process an image for inclusion in EPUB."""
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Resize if too large
            if img.width > self.max_width or img.height > self.max_height:
                img.thumbnail(
                    (self.max_width, self.max_height),
                    Image.Resampling.LANCZOS,
                )

            # Save to bytes
            from io import BytesIO

            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=self.quality, optimize=True)
            return buffer.getvalue()
