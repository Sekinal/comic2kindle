"""Image processing service for manga conversion."""

import io
import logging
from pathlib import Path
from typing import Optional

from PIL import Image

from app.models.schemas import DeviceProfile, ImageProcessingOptions, UpscaleMethod
from app.services.device_profiles import DeviceProfileService

logger = logging.getLogger(__name__)


class ImageProcessorService:
    """Service for processing manga images for e-readers."""

    # Aspect ratio threshold for double-page spread detection
    SPREAD_ASPECT_RATIO_THRESHOLD = 1.3

    def __init__(self, options: Optional[ImageProcessingOptions] = None):
        """Initialize with processing options."""
        self.options = options or ImageProcessingOptions()
        self.device_service = DeviceProfileService()
        self.target_width, self.target_height = self.device_service.get_dimensions(
            self.options.device_profile,
            self.options.custom_width,
            self.options.custom_height,
        )

    def process_image(
        self,
        image_path: Path,
        quality: int = 85,
    ) -> bytes:
        """Process a single image for e-reader display.

        Args:
            image_path: Path to the image file
            quality: JPEG quality (1-100)

        Returns:
            Processed image as bytes
        """
        with Image.open(image_path) as img:
            return self.process_pil_image(img, quality)

    def process_image_bytes(
        self,
        image_bytes: bytes,
        quality: int = 85,
    ) -> bytes:
        """Process image from bytes.

        Args:
            image_bytes: Raw image bytes
            quality: JPEG quality (1-100)

        Returns:
            Processed image as bytes
        """
        with Image.open(io.BytesIO(image_bytes)) as img:
            return self.process_pil_image(img, quality)

    def process_pil_image(
        self,
        img: Image.Image,
        quality: int = 85,
    ) -> bytes:
        """Process a PIL Image for e-reader display.

        Args:
            img: PIL Image object
            quality: JPEG quality (1-100)

        Returns:
            Processed image as bytes
        """
        # Step 1: Check for double-page spread and rotate if needed
        if self.options.detect_spreads and self.is_double_page_spread(img):
            if self.options.rotate_spreads:
                img = self._rotate_spread(img)
                logger.debug(f"Rotated double-page spread: {img.size}")

        # Step 2: Convert to RGB if needed
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Step 3: Upscale if needed
        img = self._upscale_if_needed(img)

        # Step 4: Resize to fit device (fill screen mode)
        if self.options.fill_screen:
            img = self._resize_to_fill(img)
        else:
            img = self._resize_to_fit(img)

        # Step 5: Encode to JPEG
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        return buffer.getvalue()

    def is_double_page_spread(self, img: Image.Image) -> bool:
        """Detect if an image is a double-page spread (landscape orientation).

        A spread is detected when width is significantly greater than height,
        indicating two pages side-by-side.

        Args:
            img: PIL Image to check

        Returns:
            True if image appears to be a double-page spread
        """
        aspect_ratio = img.width / img.height
        return aspect_ratio > self.SPREAD_ASPECT_RATIO_THRESHOLD

    def _rotate_spread(self, img: Image.Image) -> Image.Image:
        """Rotate a double-page spread 90 degrees for portrait reading.

        Rotates clockwise so the right page appears on top when viewing
        in portrait mode.

        Args:
            img: PIL Image to rotate

        Returns:
            Rotated image
        """
        # Rotate 90 degrees clockwise (right page on top)
        return img.rotate(-90, expand=True)

    def _upscale_if_needed(self, img: Image.Image) -> Image.Image:
        """Upscale image if smaller than target dimensions.

        Args:
            img: PIL Image to potentially upscale

        Returns:
            Upscaled image or original if already large enough
        """
        if self.options.upscale_method == UpscaleMethod.NONE:
            return img

        # Check if upscaling is needed
        needs_upscale = img.width < self.target_width or img.height < self.target_height

        if not needs_upscale:
            return img

        if self.options.upscale_method == UpscaleMethod.AI_ESRGAN:
            # Try AI upscaling, fall back to Lanczos if unavailable
            try:
                return self._upscale_ai(img)
            except Exception as e:
                logger.warning(f"AI upscaling failed, falling back to Lanczos: {e}")
                return self._upscale_lanczos(img)
        else:
            return self._upscale_lanczos(img)

    def _upscale_lanczos(self, img: Image.Image) -> Image.Image:
        """Upscale image using high-quality Lanczos resampling.

        Args:
            img: PIL Image to upscale

        Returns:
            Upscaled image
        """
        # Calculate scale factor to reach target dimensions
        scale_w = self.target_width / img.width
        scale_h = self.target_height / img.height
        scale = max(scale_w, scale_h)

        if scale <= 1:
            return img

        new_width = int(img.width * scale)
        new_height = int(img.height * scale)

        logger.debug(f"Lanczos upscaling from {img.size} to ({new_width}, {new_height})")
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def _upscale_ai(self, img: Image.Image) -> Image.Image:
        """Upscale image using AI (Real-ESRGAN).

        This is a placeholder that will use the AIUpscaler service.

        Args:
            img: PIL Image to upscale

        Returns:
            Upscaled image
        """
        # Import here to avoid circular dependency and allow optional AI support
        try:
            from app.services.ai_upscaler import AIUpscaler

            upscaler = AIUpscaler()
            if upscaler.is_available():
                # Convert PIL to bytes
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                image_bytes = buffer.getvalue()

                # Upscale
                upscaled_bytes = upscaler.upscale(image_bytes)

                # Convert back to PIL
                return Image.open(io.BytesIO(upscaled_bytes))
        except ImportError:
            pass

        # Fall back to Lanczos if AI not available
        logger.info("AI upscaling not available, using Lanczos")
        return self._upscale_lanczos(img)

    def _resize_to_fill(self, img: Image.Image) -> Image.Image:
        """Resize image to fill device screen while maintaining aspect ratio.

        The image is scaled to fit within the device dimensions,
        potentially with letterboxing/pillarboxing for the EPUB viewer.

        Args:
            img: PIL Image to resize

        Returns:
            Resized image
        """
        # Calculate scale to fit within target
        scale_w = self.target_width / img.width
        scale_h = self.target_height / img.height
        scale = min(scale_w, scale_h)  # Fit within bounds

        new_width = int(img.width * scale)
        new_height = int(img.height * scale)

        if new_width == img.width and new_height == img.height:
            return img

        logger.debug(f"Resizing from {img.size} to ({new_width}, {new_height})")
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def _resize_to_fit(self, img: Image.Image) -> Image.Image:
        """Resize image to fit within device dimensions (downscale only).

        Only downscales if image is larger than target.

        Args:
            img: PIL Image to resize

        Returns:
            Resized image
        """
        if img.width <= self.target_width and img.height <= self.target_height:
            return img

        # Use thumbnail for downscaling (modifies in place)
        img_copy = img.copy()
        img_copy.thumbnail((self.target_width, self.target_height), Image.Resampling.LANCZOS)
        return img_copy

    def get_target_dimensions(self) -> tuple[int, int]:
        """Get the target device dimensions.

        Returns:
            Tuple of (width, height)
        """
        return (self.target_width, self.target_height)
