"""File management service."""

import shutil
import uuid
from pathlib import Path

from app.config import settings
from app.models.schemas import FileInfo


class FileManager:
    """Manages file uploads and storage."""

    def __init__(self) -> None:
        self.upload_dir = settings.upload_dir
        self.output_dir = settings.output_dir

    def create_session(self) -> str:
        """Create a new upload session."""
        session_id = str(uuid.uuid4())
        session_dir = self.upload_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_id

    def get_session_dir(self, session_id: str) -> Path:
        """Get the directory for a session."""
        return self.upload_dir / session_id

    def get_output_dir(self, session_id: str) -> Path:
        """Get the output directory for a session."""
        output_path = self.output_dir / session_id
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path

    async def save_file(
        self,
        session_id: str,
        filename: str,
        content: bytes,
    ) -> FileInfo:
        """Save an uploaded file."""
        session_dir = self.get_session_dir(session_id)
        if not session_dir.exists():
            session_dir.mkdir(parents=True, exist_ok=True)

        file_id = str(uuid.uuid4())
        extension = Path(filename).suffix.lower()
        file_path = session_dir / f"{file_id}{extension}"

        file_path.write_bytes(content)

        return FileInfo(
            id=file_id,
            original_name=filename,
            size=len(content),
            extension=extension,
        )

    def get_file_path(self, session_id: str, file_id: str, extension: str) -> Path:
        """Get the path to a stored file."""
        return self.get_session_dir(session_id) / f"{file_id}{extension}"

    def list_files(self, session_id: str) -> list[Path]:
        """List all files in a session."""
        session_dir = self.get_session_dir(session_id)
        if not session_dir.exists():
            return []
        return list(session_dir.iterdir())

    def cleanup_session(self, session_id: str) -> None:
        """Remove all files for a session."""
        session_dir = self.get_session_dir(session_id)
        if session_dir.exists():
            shutil.rmtree(session_dir)

        output_session = self.output_dir / session_id
        if output_session.exists():
            shutil.rmtree(output_session)

    def get_output_file(self, session_id: str, filename: str) -> Path | None:
        """Get an output file path."""
        file_path = self.output_dir / session_id / filename
        if file_path.exists():
            return file_path
        return None
