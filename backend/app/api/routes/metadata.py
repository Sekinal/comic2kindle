"""Metadata lookup API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_metadata_service
from app.models.schemas import MetadataSearchResult
from app.services.metadata_lookup import MetadataLookupService

router = APIRouter(prefix="/metadata", tags=["metadata"])


class MetadataSearchRequest(BaseModel):
    """Request body for metadata search."""

    query: str
    limit: int = 10


@router.post("/search", response_model=list[MetadataSearchResult])
async def search_metadata(
    request: MetadataSearchRequest,
    metadata_service: MetadataLookupService = Depends(get_metadata_service),
) -> list[MetadataSearchResult]:
    """
    Search for manga metadata across MangaDex and AniList.

    Returns a list of matching results with title, author, description, and cover URL.
    """
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty",
        )

    results = await metadata_service.search(
        query=request.query.strip(),
        limit=min(request.limit, 20),  # Cap at 20 results
    )

    return results


@router.get("/cover")
async def get_cover_image(
    url: str,
    metadata_service: MetadataLookupService = Depends(get_metadata_service),
) -> bytes:
    """
    Proxy endpoint to fetch cover images from external sources.

    This avoids CORS issues when loading covers in the frontend.
    """
    if not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL is required",
        )

    image_data = await metadata_service.get_cover_image(url)

    if not image_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed to fetch cover image",
        )

    from fastapi.responses import Response

    return Response(
        content=image_data,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )
