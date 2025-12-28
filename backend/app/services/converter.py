"""EPUB/MOBI converter service."""

import logging
import subprocess
import uuid
from io import BytesIO
from pathlib import Path
from typing import Callable, Optional

from ebooklib import epub
from PIL import Image

from app.config import settings
from app.models.schemas import ImageProcessingOptions, MangaMetadata, OutputFormat
from app.services.image_processor import ImageProcessorService, ParallelImageProcessor

logger = logging.getLogger(__name__)


class ConverterService:
    """Converts images to EPUB/MOBI ebooks."""

    def __init__(
        self,
        image_options: Optional[ImageProcessingOptions] = None,
    ) -> None:
        self.quality = settings.image_quality
        self.image_options = image_options or ImageProcessingOptions()
        self.image_processor = ImageProcessorService(self.image_options)
        logger.info(f"ConverterService initialized with image options: {self.image_options}")

    def create_epub(
        self,
        images: list[Path],
        metadata: MangaMetadata,
        output_path: Path,
        cover_image: Optional[Path] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Path:
        """
        Create an EPUB from a list of images using parallel processing.

        Args:
            images: List of image paths in reading order
            metadata: Manga metadata
            output_path: Path to save the EPUB
            cover_image: Optional custom cover image
            progress_callback: Called with (completed, total) during processing

        Returns:
            Path to the created EPUB file
        """
        book = epub.EpubBook()

        # Get target dimensions for viewport
        target_width, target_height = self.image_processor.get_target_dimensions()

        # Get display title (formatted with chapter info)
        display_title = metadata.get_display_title()

        # Set metadata
        book.set_identifier(str(uuid.uuid4()))
        book.set_title(display_title)
        book.set_language("en")

        if metadata.author:
            book.add_author(metadata.author)

        # Add series metadata
        if metadata.series:
            book.add_metadata("DC", "series", metadata.series)
            # Use chapter info for series index
            chapter_str = metadata.chapter_info.format_chapter_string()
            if chapter_str:
                # For ranges like "1-16", use the start chapter as index
                if metadata.chapter_info.chapter_start is not None:
                    book.add_metadata(
                        "calibre",
                        "series_index",
                        str(metadata.chapter_info.chapter_start),
                    )

        if metadata.description:
            book.add_metadata("DC", "description", metadata.description)

        # Set reading direction for manga (right-to-left)
        book.set_direction("rtl")

        # Add fixed-layout metadata for proper Kindle rendering
        # This is critical - Kindle needs these to render manga correctly
        book.add_metadata(None, "meta", "", {"name": "fixed-layout", "content": "true"})
        book.add_metadata(
            None,
            "meta",
            "",
            {"name": "original-resolution", "content": f"{target_width}x{target_height}"},
        )
        book.add_metadata(None, "meta", "", {"name": "book-type", "content": "comic"})
        book.add_metadata(None, "meta", "", {"name": "zero-gutter", "content": "true"})
        book.add_metadata(None, "meta", "", {"name": "zero-margin", "content": "true"})
        book.add_metadata(
            None, "meta", "", {"property": "rendition:layout", "content": "pre-paginated"}
        )
        book.add_metadata(
            None, "meta", "", {"property": "rendition:spread", "content": "landscape"}
        )

        # Process and add cover (done separately, not part of parallel batch)
        cover_path = cover_image or (images[0] if images else None)
        if cover_path:
            cover_content = self.image_processor.process_image(
                cover_path, self.quality
            )
            book.set_cover("cover.jpg", cover_content)

        # PARALLEL IMAGE PROCESSING
        # Process all images in parallel using ThreadPoolExecutor
        # This is the main performance optimization - 6-8x speedup expected
        parallel_processor = ParallelImageProcessor(
            options=self.image_options,
            progress_callback=progress_callback,
        )

        logger.info(f"Starting parallel processing of {len(images)} images")
        processed_images = parallel_processor.process_batch(images, self.quality)
        logger.info(f"Parallel processing complete: {len(processed_images)} images")

        # EPUB ASSEMBLY (fast - just data copying)
        # Build chapters from pre-processed images
        chapters = []
        spine = ["nav"]

        for idx, image_content in processed_images:
            page_num = idx + 1

            # Create image item
            image_name = f"page_{page_num:04d}.jpg"
            image_item = epub.EpubItem(
                uid=f"image_{page_num}",
                file_name=f"images/{image_name}",
                media_type="image/jpeg",
                content=image_content,
            )
            book.add_item(image_item)

            # Create HTML page for the image with proper viewport for e-reader
            # Using KCC-style fixed-layout format for best Kindle compatibility
            chapter = epub.EpubHtml(
                title=f"Page {page_num}",
                file_name=f"page_{page_num:04d}.xhtml",
                lang="en",
            )
            # KCC-style HTML with explicit dimensions for fixed-layout EPUB
            html_content = f"""<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>Page {page_num}</title>
<link href="style/main.css" type="text/css" rel="stylesheet"/>
<meta name="viewport" content="width={target_width}, height={target_height}"/>
</head>
<body>
<div>
<img width="{target_width}" height="{target_height}" src="images/{image_name}" alt="Page {page_num}"/>
</div>
</body>
</html>"""
            chapter.content = html_content.encode("utf-8")

            book.add_item(chapter)
            chapters.append(chapter)
            spine.append(chapter)

        # Add navigation
        book.toc = chapters
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # Set spine
        book.spine = spine

        # KCC-style minimal CSS for fixed-layout EPUB
        # Fixed-layout EPUBs don't need complex CSS - the viewport handles sizing
        style = """
@page {
margin: 0;
}
body {
display: block;
margin: 0;
padding: 0;
background-color: #000000;
}
div {
text-align: center;
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
        logger.info(f"Writing EPUB with {len(chapters)} pages to {output_path}")
        epub.write_epub(str(output_path), book)
        logger.info(f"EPUB written successfully: {output_path.stat().st_size} bytes")

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

            logger.info(f"Running MOBI conversion: {cmd}")
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
            )
            logger.info(f"MOBI conversion result: returncode={result.returncode}")
            if result.stdout:
                logger.info(f"MOBI stdout: {result.stdout[:500]}")
            if result.stderr:
                logger.warning(f"MOBI stderr: {result.stderr[:500]}")

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

