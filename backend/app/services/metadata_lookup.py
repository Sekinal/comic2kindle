"""Metadata lookup service for manga information."""

import httpx
from typing import Optional

from app.models.schemas import MetadataSearchResult


class MetadataLookupService:
    """Looks up manga metadata from various sources."""

    MANGADEX_API = "https://api.mangadex.org"
    ANILIST_API = "https://graphql.anilist.co"

    async def search(
        self,
        query: str,
        limit: int = 10,
    ) -> list[MetadataSearchResult]:
        """
        Search for manga metadata across multiple sources.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of search results
        """
        results: list[MetadataSearchResult] = []

        # Try MangaDex first
        try:
            mangadex_results = await self._search_mangadex(query, limit)
            results.extend(mangadex_results)
        except Exception as e:
            print(f"MangaDex search failed: {e}")

        # Try AniList as fallback/supplement
        try:
            anilist_results = await self._search_anilist(query, limit)
            results.extend(anilist_results)
        except Exception as e:
            print(f"AniList search failed: {e}")

        return results[:limit]

    async def _search_mangadex(
        self,
        query: str,
        limit: int,
    ) -> list[MetadataSearchResult]:
        """Search MangaDex API."""
        results: list[MetadataSearchResult] = []

        async with httpx.AsyncClient() as client:
            # Search for manga
            response = await client.get(
                f"{self.MANGADEX_API}/manga",
                params={
                    "title": query,
                    "limit": limit,
                    "includes[]": ["cover_art", "author"],
                    "order[relevance]": "desc",
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            for manga in data.get("data", []):
                # Get title (prefer English)
                titles = manga.get("attributes", {}).get("title", {})
                title = (
                    titles.get("en")
                    or titles.get("ja-ro")
                    or next(iter(titles.values()), "Unknown")
                )

                # Get description
                descriptions = manga.get("attributes", {}).get("description", {})
                description = descriptions.get("en") or next(
                    iter(descriptions.values()), ""
                )

                # Get author
                author = ""
                for rel in manga.get("relationships", []):
                    if rel.get("type") == "author":
                        author = rel.get("attributes", {}).get("name", "")
                        break

                # Get cover URL
                cover_url = None
                for rel in manga.get("relationships", []):
                    if rel.get("type") == "cover_art":
                        cover_filename = rel.get("attributes", {}).get("fileName")
                        if cover_filename:
                            cover_url = (
                                f"https://uploads.mangadex.org/covers/"
                                f"{manga['id']}/{cover_filename}.256.jpg"
                            )
                        break

                results.append(
                    MetadataSearchResult(
                        id=manga["id"],
                        title=title,
                        author=author,
                        description=description[:500] if description else "",
                        cover_url=cover_url,
                        source="mangadex",
                    )
                )

        return results

    async def _search_anilist(
        self,
        query: str,
        limit: int,
    ) -> list[MetadataSearchResult]:
        """Search AniList GraphQL API."""
        results: list[MetadataSearchResult] = []

        graphql_query = """
        query ($search: String, $perPage: Int) {
            Page(perPage: $perPage) {
                media(search: $search, type: MANGA) {
                    id
                    title {
                        english
                        romaji
                        native
                    }
                    description(asHtml: false)
                    coverImage {
                        large
                    }
                    staff(perPage: 1, sort: RELEVANCE) {
                        nodes {
                            name {
                                full
                            }
                        }
                    }
                }
            }
        }
        """

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.ANILIST_API,
                json={
                    "query": graphql_query,
                    "variables": {
                        "search": query,
                        "perPage": limit,
                    },
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            media_list = (
                data.get("data", {}).get("Page", {}).get("media", [])
            )

            for media in media_list:
                titles = media.get("title", {})
                title = (
                    titles.get("english")
                    or titles.get("romaji")
                    or titles.get("native")
                    or "Unknown"
                )

                # Get author from staff
                author = ""
                staff = media.get("staff", {}).get("nodes", [])
                if staff:
                    author = staff[0].get("name", {}).get("full", "")

                description = media.get("description") or ""
                # Clean HTML entities
                description = (
                    description.replace("<br>", "\n")
                    .replace("<br/>", "\n")
                    .replace("<i>", "")
                    .replace("</i>", "")
                )

                cover_url = media.get("coverImage", {}).get("large")

                results.append(
                    MetadataSearchResult(
                        id=f"anilist_{media['id']}",
                        title=title,
                        author=author,
                        description=description[:500],
                        cover_url=cover_url,
                        source="anilist",
                    )
                )

        return results

    async def get_cover_image(self, cover_url: str) -> Optional[bytes]:
        """Download a cover image from URL."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(cover_url, timeout=30.0)
                response.raise_for_status()
                return response.content
        except Exception as e:
            print(f"Failed to download cover: {e}")
            return None
