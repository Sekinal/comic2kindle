"""API dependencies."""

from app.services.converter import ConverterService
from app.services.epub_reader import EpubReaderService
from app.services.extractor import ExtractorService
from app.services.file_manager import FileManager
from app.services.filename_parser import FilenameParserService
from app.services.merger import MergerService
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


def get_epub_reader() -> EpubReaderService:
    """Get EPUB reader service instance."""
    return EpubReaderService()


def get_merger() -> MergerService:
    """Get merger service instance."""
    return MergerService()


def get_filename_parser() -> FilenameParserService:
    """Get filename parser service instance."""
    return FilenameParserService()
