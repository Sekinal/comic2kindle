"""AI-based image upscaling using Real-ESRGAN."""

import io
import logging
import os
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)


class AIUpscaler:
    """AI upscaling service using Real-ESRGAN via realesrgan-ncnn-py.

    This service uses the realesrgan-ncnn-py package which includes
    GPU-accelerated upscaling via ncnn/Vulkan.
    """

    # Model mapping: 0=realesr-animevideov3-x2, 1=x3, 2=x4
    SCALE_TO_MODEL = {
        2: 0,  # realesr-animevideov3-x2
        3: 1,  # realesr-animevideov3-x3
        4: 2,  # realesr-animevideov3-x4
    }

    def __init__(self):
        """Initialize the AI upscaler."""
        self._upscaler = None
        self._current_scale = None
        self._available: Optional[bool] = None

    def _get_upscaler(self, scale: int = 2):
        """Get or create the upscaler instance for the given scale."""
        if self._upscaler is not None and self._current_scale == scale:
            return self._upscaler

        try:
            from realesrgan_ncnn_py import Realesrgan

            model_id = self.SCALE_TO_MODEL.get(scale, 0)
            # gpuid: -1 for CPU, 0 for first GPU
            gpuid = -1 if os.environ.get("FORCE_CPU_UPSCALING") else 0

            self._upscaler = Realesrgan(gpuid=gpuid, model=model_id)
            self._current_scale = scale
            logger.info(f"Initialized Real-ESRGAN with model={model_id}, gpu={gpuid}")
            return self._upscaler
        except Exception as e:
            logger.error(f"Failed to initialize Real-ESRGAN: {e}")
            raise

    def is_available(self) -> bool:
        """Check if AI upscaling is available.

        Returns:
            True if Real-ESRGAN is installed and ready
        """
        if self._available is not None:
            return self._available

        try:
            from realesrgan_ncnn_py import Realesrgan
            # Quick test to see if it initializes
            Realesrgan(gpuid=-1, model=0)
            self._available = True
        except Exception as e:
            logger.warning(f"Real-ESRGAN not available: {e}")
            self._available = False

        return self._available

    def upscale(
        self,
        image_bytes: bytes,
        scale: int = 2,
        model: Optional[str] = None,
    ) -> bytes:
        """Upscale an image using Real-ESRGAN.

        Args:
            image_bytes: Input image as bytes
            scale: Upscaling factor (2, 3, or 4)
            model: Model name (ignored, uses animevideov3)

        Returns:
            Upscaled image as bytes

        Raises:
            RuntimeError: If upscaling fails or is not available
        """
        if not self.is_available():
            raise RuntimeError("Real-ESRGAN is not available")

        # Validate scale
        if scale not in self.SCALE_TO_MODEL:
            logger.warning(f"Invalid scale {scale}, using 2")
            scale = 2

        try:
            upscaler = self._get_upscaler(scale)

            # Load image
            with Image.open(io.BytesIO(image_bytes)) as img:
                # Convert to RGB if needed
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Upscale using the library
                result = upscaler.process_pil(img)

                # Save to bytes
                buffer = io.BytesIO()
                result.save(buffer, format="PNG")
                return buffer.getvalue()

        except Exception as e:
            logger.error(f"Real-ESRGAN upscaling failed: {e}")
            raise RuntimeError(f"Real-ESRGAN failed: {e}")

    def upscale_pil(
        self,
        img: Image.Image,
        scale: int = 2,
        model: Optional[str] = None,
    ) -> Image.Image:
        """Upscale a PIL Image using Real-ESRGAN.

        Args:
            img: Input PIL Image
            scale: Upscaling factor (2, 3, or 4)
            model: Model name (ignored)

        Returns:
            Upscaled PIL Image
        """
        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()

        # Upscale
        upscaled_bytes = self.upscale(image_bytes, scale, model)

        # Convert back to PIL
        return Image.open(io.BytesIO(upscaled_bytes))


def check_ai_upscaling_available() -> bool:
    """Check if AI upscaling is available on this system.

    Returns:
        True if Real-ESRGAN is installed and ready
    """
    # Check if disabled via environment variable
    if os.environ.get("DISABLE_AI_UPSCALING"):
        return False

    # Disable AI upscaling in Docker without explicit enablement
    if os.path.exists("/.dockerenv") and not os.environ.get("ENABLE_AI_UPSCALING"):
        return False

    try:
        upscaler = AIUpscaler()
        return upscaler.is_available()
    except Exception:
        return False
