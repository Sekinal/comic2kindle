"""Service for merging multiple input files with auto-splitting."""

from pathlib import Path

from PIL import Image

from app.config import settings


class MergerService:
    """Merges multiple input files and handles auto-splitting."""

    def __init__(self) -> None:
        self.max_output_size = settings.max_output_file_size

    def merge_images(
        self,
        image_lists: list[list[Path]],
        max_size_bytes: int | None = None,
    ) -> list[list[Path]]:
        """
        Merge multiple image lists into batches, splitting if needed.

        Args:
            image_lists: List of image path lists (one per input file)
            max_size_bytes: Maximum output size in bytes (default from settings)

        Returns:
            List of image batches (one per output file)
        """
        max_size = max_size_bytes or self.max_output_size

        # Flatten all images into a single list
        all_images: list[Path] = []
        for images in image_lists:
            all_images.extend(images)

        if not all_images:
            return []

        # Calculate split points based on estimated sizes
        split_points = self.calculate_split_points(all_images, max_size)

        # Create batches
        batches: list[list[Path]] = []
        prev_point = 0

        for point in split_points:
            batch = all_images[prev_point:point]
            if batch:
                batches.append(batch)
            prev_point = point

        # Add remaining images
        if prev_point < len(all_images):
            batches.append(all_images[prev_point:])

        # If no splits needed, return single batch
        if not batches:
            batches = [all_images]

        return batches

    def estimate_output_size(self, images: list[Path]) -> int:
        """
        Estimate the EPUB output size for given images.

        The estimation accounts for:
        - JPEG compression (images are re-encoded)
        - EPUB overhead (HTML, CSS, metadata)
        - Image resizing (large images are scaled down)

        Args:
            images: List of image paths

        Returns:
            Estimated output size in bytes
        """
        total_size = 0
        epub_overhead = 50_000  # ~50KB for EPUB structure

        for image_path in images:
            try:
                # Get original file size
                file_size = image_path.stat().st_size

                # Estimate compressed size
                # JPEG at 85% quality typically reduces to 60-80% of original
                # Also account for resizing if image is too large
                with Image.open(image_path) as img:
                    width, height = img.size

                    # If image needs resizing, it will be smaller
                    max_w = settings.max_image_width
                    max_h = settings.max_image_height

                    if width > max_w or height > max_h:
                        ratio = min(max_w / width, max_h / height)
                        new_pixels = int(width * ratio) * int(height * ratio)
                        original_pixels = width * height
                        size_ratio = new_pixels / original_pixels
                        file_size = int(file_size * size_ratio)

                    # Apply compression factor
                    compression_factor = 0.7
                    estimated = int(file_size * compression_factor)

                    # Add HTML wrapper overhead per page (~500 bytes)
                    estimated += 500

                    total_size += estimated

            except Exception:
                # If we can't read the image, use file size as-is
                total_size += image_path.stat().st_size

        return total_size + epub_overhead

    def calculate_split_points(
        self,
        images: list[Path],
        max_size: int,
    ) -> list[int]:
        """
        Calculate indices where to split for size limit.

        Args:
            images: List of image paths
            max_size: Maximum size per output file in bytes

        Returns:
            List of split point indices
        """
        if not images:
            return []

        split_points: list[int] = []
        current_batch: list[Path] = []
        current_size = 50_000  # Start with EPUB overhead

        for idx, image_path in enumerate(images):
            # Estimate this image's contribution
            image_size = self._estimate_single_image_size(image_path)

            # Check if adding this image would exceed limit
            if current_size + image_size > max_size and current_batch:
                # Split before this image
                split_points.append(idx)
                current_batch = [image_path]
                current_size = 50_000 + image_size
            else:
                current_batch.append(image_path)
                current_size += image_size

        return split_points

    def suggest_split_count(self, images: list[Path]) -> int:
        """
        Suggest how many output files will be created.

        Args:
            images: List of all images to be included

        Returns:
            Estimated number of output files
        """
        total_size = self.estimate_output_size(images)
        if total_size <= self.max_output_size:
            return 1

        return max(1, (total_size + self.max_output_size - 1) // self.max_output_size)

    def _estimate_single_image_size(self, image_path: Path) -> int:
        """Estimate size contribution of a single image."""
        try:
            file_size = image_path.stat().st_size

            with Image.open(image_path) as img:
                width, height = img.size
                max_w = settings.max_image_width
                max_h = settings.max_image_height

                if width > max_w or height > max_h:
                    ratio = min(max_w / width, max_h / height)
                    new_pixels = int(width * ratio) * int(height * ratio)
                    original_pixels = width * height
                    file_size = int(file_size * (new_pixels / original_pixels))

            # Compression + HTML overhead
            return int(file_size * 0.7) + 500

        except Exception:
            return image_path.stat().st_size
