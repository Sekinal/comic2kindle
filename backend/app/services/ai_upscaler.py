"""AI-based image upscaling using Real-ESRGAN."""

import io
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)


class AIUpscaler:
    """AI upscaling service using Real-ESRGAN.

    This service uses the realesrgan-ncnn-vulkan binary for GPU-accelerated
    upscaling. If not available, it falls back gracefully.
    """

    # Path to Real-ESRGAN binary
    ESRGAN_BINARY = "realesrgan-ncnn-vulkan"

    # Model name for anime/manga content
    MODEL_NAME = "realesr-animevideov3"

    def __init__(self, model_path: Optional[Path] = None):
        """Initialize the AI upscaler.

        Args:
            model_path: Optional path to model files
        """
        self.model_path = model_path or Path("/app/realesrgan")
        self._binary_path: Optional[str] = None
        self._check_availability()

    def _check_availability(self) -> None:
        """Check if Real-ESRGAN is available."""
        # Check for the binary in PATH or specified location
        self._binary_path = shutil.which(self.ESRGAN_BINARY)

        if not self._binary_path:
            # Try the model path
            potential_path = self.model_path / self.ESRGAN_BINARY
            if potential_path.exists():
                self._binary_path = str(potential_path)

    def is_available(self) -> bool:
        """Check if AI upscaling is available.

        Returns:
            True if Real-ESRGAN is installed and ready
        """
        return self._binary_path is not None

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
            model: Model name to use (default: realesr-animevideov3)

        Returns:
            Upscaled image as bytes

        Raises:
            RuntimeError: If upscaling fails or is not available
        """
        if not self.is_available():
            raise RuntimeError("Real-ESRGAN is not available")

        model = model or self.MODEL_NAME

        # Create temporary files for input/output
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.png"
            output_path = Path(tmpdir) / "output.png"

            # Save input image
            with Image.open(io.BytesIO(image_bytes)) as img:
                img.save(input_path, format="PNG")

            # Run Real-ESRGAN
            cmd = [
                self._binary_path,
                "-i",
                str(input_path),
                "-o",
                str(output_path),
                "-n",
                model,
                "-s",
                str(scale),
            ]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                )

                if result.returncode != 0:
                    logger.error(f"Real-ESRGAN failed: {result.stderr}")
                    raise RuntimeError(f"Real-ESRGAN failed: {result.stderr}")

            except subprocess.TimeoutExpired:
                raise RuntimeError("Real-ESRGAN timed out")

            # Read output image
            if not output_path.exists():
                raise RuntimeError("Real-ESRGAN did not produce output")

            with open(output_path, "rb") as f:
                return f.read()

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
            model: Model name to use

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
    try:
        upscaler = AIUpscaler()
        return upscaler.is_available()
    except Exception:
        return False
