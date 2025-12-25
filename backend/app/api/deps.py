"""API dependencies."""

from app.services.extractor import ExtractorService
from app.services.converter import ConverterService
from app.services.file_manager import FileManager
from app.services.metadata_lookup import MetadataLookupService


def get_file_manager() -> FileManager:
    """Get file manager instance."""
    return FileManager()


def get_extractor() -> ExtractorService:
    """Get extractor service instance."""
    return ExtractorService()


def get_converter() -> ConverterService:
    """Get converter service instance."""
    return ConverterService()


def get_metadata_service() -> MetadataLookupService:
    """Get metadata lookup service instance."""
    return MetadataLookupService()
