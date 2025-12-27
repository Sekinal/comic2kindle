"""Device profiles API routes."""

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import CapabilitiesResponse, DeviceProfileInfo
from app.services.ai_upscaler import check_ai_upscaling_available
from app.services.device_profiles import DeviceProfileService

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=list[DeviceProfileInfo])
async def list_devices() -> list[DeviceProfileInfo]:
    """
    List all available device profiles.

    Returns device specifications for Kindle and Kobo e-readers,
    including screen dimensions and recommended output formats.
    """
    service = DeviceProfileService()
    return service.get_all_profiles()


@router.get("/capabilities", response_model=CapabilitiesResponse)
async def get_capabilities() -> CapabilitiesResponse:
    """
    Get system capabilities.

    Returns information about available features such as
    AI upscaling support and supported file formats.
    """
    return CapabilitiesResponse(
        ai_upscaling_available=check_ai_upscaling_available(),
        supported_input_formats=["cbz", "cbr", "epub", "zip", "rar"],
        supported_output_formats=["epub", "mobi"],
    )


@router.get("/{profile_id}", response_model=DeviceProfileInfo)
async def get_device(profile_id: str) -> DeviceProfileInfo:
    """
    Get a specific device profile by ID.

    Args:
        profile_id: The device profile ID (e.g., "kindle_paperwhite_5")

    Returns:
        Device profile information including screen dimensions.

    Raises:
        404: If the device profile is not found.
    """
    service = DeviceProfileService()
    profile = service.get_profile(profile_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device profile not found: {profile_id}",
        )

    return profile.to_profile_info()
