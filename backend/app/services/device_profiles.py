"""Device profiles for e-readers (Kindle, Kobo, etc.)."""

from dataclasses import dataclass
from typing import Optional

from app.models.schemas import DeviceProfile, DeviceProfileInfo


@dataclass
class DeviceSpec:
    """Specification for an e-reader device."""

    id: str
    name: str
    display_name: str
    manufacturer: str  # kindle, kobo, custom
    width: int
    height: int
    dpi: int
    supports_color: bool = False
    recommended_format: str = "epub"

    def to_profile_info(self) -> DeviceProfileInfo:
        """Convert to API response model."""
        return DeviceProfileInfo(
            id=self.id,
            name=self.name,
            display_name=self.display_name,
            manufacturer=self.manufacturer,
            width=self.width,
            height=self.height,
            dpi=self.dpi,
            supports_color=self.supports_color,
            recommended_format=self.recommended_format,
        )


# Device specifications database
DEVICE_SPECS: dict[str, DeviceSpec] = {
    # Kindle devices
    DeviceProfile.KINDLE_BASIC.value: DeviceSpec(
        id=DeviceProfile.KINDLE_BASIC.value,
        name="kindle_basic",
        display_name="Kindle Basic (6\")",
        manufacturer="kindle",
        width=600,
        height=800,
        dpi=167,
        recommended_format="mobi",
    ),
    DeviceProfile.KINDLE_PAPERWHITE_5.value: DeviceSpec(
        id=DeviceProfile.KINDLE_PAPERWHITE_5.value,
        name="kindle_paperwhite_5",
        display_name="Kindle Paperwhite 5 (6.8\")",
        manufacturer="kindle",
        width=1236,
        height=1648,
        dpi=300,
        recommended_format="epub",
    ),
    DeviceProfile.KINDLE_SCRIBE.value: DeviceSpec(
        id=DeviceProfile.KINDLE_SCRIBE.value,
        name="kindle_scribe",
        display_name="Kindle Scribe (10.2\")",
        manufacturer="kindle",
        width=1860,
        height=2480,
        dpi=300,
        recommended_format="epub",
    ),
    # Kobo devices
    DeviceProfile.KOBO_CLARA_2E.value: DeviceSpec(
        id=DeviceProfile.KOBO_CLARA_2E.value,
        name="kobo_clara_2e",
        display_name="Kobo Clara 2E (6\")",
        manufacturer="kobo",
        width=1072,
        height=1448,
        dpi=300,
        recommended_format="epub",
    ),
    DeviceProfile.KOBO_LIBRA_2.value: DeviceSpec(
        id=DeviceProfile.KOBO_LIBRA_2.value,
        name="kobo_libra_2",
        display_name="Kobo Libra 2 (7\")",
        manufacturer="kobo",
        width=1264,
        height=1680,
        dpi=300,
        recommended_format="epub",
    ),
    DeviceProfile.KOBO_SAGE.value: DeviceSpec(
        id=DeviceProfile.KOBO_SAGE.value,
        name="kobo_sage",
        display_name="Kobo Sage (8\")",
        manufacturer="kobo",
        width=1440,
        height=1920,
        dpi=300,
        recommended_format="epub",
    ),
}


class DeviceProfileService:
    """Service for managing device profiles."""

    def get_all_profiles(self) -> list[DeviceProfileInfo]:
        """Get all available device profiles."""
        return [spec.to_profile_info() for spec in DEVICE_SPECS.values()]

    def get_profile(self, profile_id: str) -> Optional[DeviceSpec]:
        """Get a specific device profile by ID."""
        return DEVICE_SPECS.get(profile_id)

    def get_dimensions(
        self,
        profile: DeviceProfile,
        custom_width: Optional[int] = None,
        custom_height: Optional[int] = None,
    ) -> tuple[int, int]:
        """Get target dimensions for a device profile."""
        if profile == DeviceProfile.CUSTOM:
            if custom_width and custom_height:
                return (custom_width, custom_height)
            # Default custom dimensions (Kindle Paperwhite-like)
            return (1236, 1648)

        spec = DEVICE_SPECS.get(profile.value)
        if spec:
            return (spec.width, spec.height)

        # Fallback to Kindle Paperwhite 5
        return (1236, 1648)

    def get_dpi(self, profile: DeviceProfile) -> int:
        """Get DPI for a device profile."""
        if profile == DeviceProfile.CUSTOM:
            return 300  # Default DPI for custom

        spec = DEVICE_SPECS.get(profile.value)
        return spec.dpi if spec else 300
