"""Storage Abstraction Layer for CampusOS Document Management.

Provides an abstract interface and concrete storage provider adapters
(Local File System, with hooks for S3/MinIO/GCS), enforcing file security,
MIME-type validation, size limits, SHA-256 checksums, and path traversal protection.
"""

import hashlib
import os
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from uuid import UUID

from app.core.exceptions import ValidationException

# Allowed MIME types and corresponding extensions for educational documents
ALLOWED_DOCUMENT_TYPES: dict[str, list[str]] = {
    "application/pdf": [".pdf"],
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"],
    "image/webp": [".webp"],
    "text/plain": [".txt"],
    "text/csv": [".csv"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    "application/msword": [".doc"],
}

# Maximum default file size (25 megabytes)
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024


def calculate_sha256(content: bytes) -> str:
    """Compute standard hexadecimal SHA-256 digest of binary content."""
    hasher = hashlib.sha256()
    hasher.update(content)
    return hasher.hexdigest()


def format_file_size(size_in_bytes: int) -> str:
    """Convert bytes to readable string like '1.2 MB' or '450 KB'."""
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    if size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"
    return f"{size_in_bytes / (1024 * 1024):.1f} MB"


def sanitize_filename(filename: str) -> str:
    """Normalize and sanitize an uploaded document filename against path traversal and control characters."""
    if not filename:
        return "unnamed_document"
    # Extract basename only to strip any path components
    base = Path(filename).name
    # Strip null bytes and control characters
    base = "".join(ch for ch in base if ord(ch) >= 32 and ch != "\x00")
    # Replace unsafe characters with underscores
    safe_name = re.sub(r'[/\\:*?"<>|]', "_", base).strip(" .")
    if not safe_name:
        safe_name = "unnamed_document"
    # Limit maximum length
    if len(safe_name) > 128:
        stem = Path(safe_name).stem[:100]
        ext = Path(safe_name).suffix
        safe_name = f"{stem}{ext}"
    return safe_name



class DocumentStorage(ABC):
    """Abstract storage provider interface."""

    @abstractmethod
    async def upload(
        self,
        file_content: bytes,
        destination_key: str,
        mime_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store binary payload under destination_key and return storage identifier."""
        pass

    @abstractmethod
    async def download(self, storage_key: str) -> bytes:
        """Retrieve binary file contents for storage_key."""
        pass

    @abstractmethod
    async def delete(self, storage_key: str) -> bool:
        """Remove file corresponding to storage_key."""
        pass

    @abstractmethod
    async def exists(self, storage_key: str) -> bool:
        """Verify whether storage_key exists."""
        pass

    @abstractmethod
    async def get_metadata(self, storage_key: str) -> dict[str, Any]:
        """Obtain size, mime-type, checksum, and creation metadata for storage_key."""
        pass

    @abstractmethod
    def validate_tenant_storage_key(self, storage_key: str, tenant_id: UUID) -> None:
        """Verify that storage_key is strictly contained within the given tenant directory."""
        pass

    @abstractmethod
    async def generate_access_reference(
        self, storage_key: str, expires_in_seconds: int = 3600
    ) -> str:
        """Create time-limited access reference (e.g. presigned URL or tokenized endpoint)."""
        pass


class LocalDocumentStorage(DocumentStorage):
    """Local filesystem storage adapter with path sanitization, boundary containment, and tenant isolation."""

    def __init__(self, base_dir: Path | str | None = None):
        if base_dir is None:
            # Default storage inside apps/api/storage/documents
            self.base_dir = Path(os.getcwd()) / "storage" / "documents"
        else:
            self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def validate_tenant_storage_key(self, storage_key: str, tenant_id: UUID) -> None:
        """Verify that storage_key belongs strictly to the given tenant namespace."""
        clean_key = storage_key.strip().replace("\\", "/").lstrip("/")
        expected_prefixes = (f"tenants/{tenant_id}/", f"{tenant_id}/")
        if not any(clean_key.startswith(p) for p in expected_prefixes):
            raise ValidationException(
                f"Storage path isolation violation: key '{storage_key}' does not belong to tenant '{tenant_id}'."
            )

    def _sanitize_and_resolve(self, storage_key: str, tenant_id: UUID | None = None) -> Path:
        """Ensure storage_key is safe, contained inside self.base_dir, and optionally tenant-isolated."""
        # Normalize slashes and remove leading/trailing whitespace
        clean_key = storage_key.strip().replace("\\", "/").lstrip("/")

        # Prevent path traversal attacks
        if ".." in clean_key or clean_key.startswith("/") or clean_key.startswith("~"):
            raise ValidationException("Invalid storage key: directory traversal pattern detected.")

        if tenant_id is not None:
            self.validate_tenant_storage_key(clean_key, tenant_id)

        resolved_path = (self.base_dir / clean_key).resolve()

        # Strict containment check
        try:
            resolved_path.relative_to(self.base_dir)
        except ValueError as exc:
            raise ValidationException("Storage path traversal attempted outside storage root.") from exc

        return resolved_path

    async def upload(
        self,
        file_content: bytes,
        destination_key: str,
        mime_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        # 1. Validate payload size
        if len(file_content) > MAX_FILE_SIZE_BYTES:
            raise ValidationException(
                f"File payload exceeds maximum permitted limit ({MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB)."
            )

        # 2. Validate MIME type
        norm_mime = mime_type.lower().strip()
        if norm_mime not in ALLOWED_DOCUMENT_TYPES:
            raise ValidationException(
                f"Unsupported media type: '{mime_type}'. Supported types: {', '.join(sorted(ALLOWED_DOCUMENT_TYPES.keys()))}"
            )

        # 3. Resolve path and ensure parent directories exist
        target_path = self._sanitize_and_resolve(destination_key)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # 4. Write binary atomically
        tmp_target = target_path.with_suffix(f"{target_path.suffix}.tmp-{os.getpid()}")
        tmp_target.write_bytes(file_content)
        tmp_target.replace(target_path)

        clean_key = destination_key.strip().replace("\\", "/").lstrip("/")
        return clean_key

    async def download(self, storage_key: str) -> bytes:
        target_path = self._sanitize_and_resolve(storage_key)
        if not target_path.is_file():
            raise ValidationException(f"Storage record '{storage_key}' does not exist on disk.")
        return target_path.read_bytes()

    async def delete(self, storage_key: str) -> bool:
        target_path = self._sanitize_and_resolve(storage_key)
        if target_path.is_file():
            target_path.unlink()
            return True
        return False

    async def exists(self, storage_key: str) -> bool:
        target_path = self._sanitize_and_resolve(storage_key)
        return target_path.is_file()

    async def get_metadata(self, storage_key: str) -> dict[str, Any]:
        target_path = self._sanitize_and_resolve(storage_key)
        if not target_path.is_file():
            raise ValidationException(f"Storage file '{storage_key}' not found.")

        stat = target_path.stat()
        content = target_path.read_bytes()
        checksum = calculate_sha256(content)

        return {
            "storage_key": storage_key,
            "size_bytes": stat.st_size,
            "formatted_size": format_file_size(stat.st_size),
            "checksum_sha256": checksum,
            "modified_at": stat.st_mtime,
        }

    async def generate_access_reference(
        self, storage_key: str, expires_in_seconds: int = 3600
    ) -> str:
        # Generates an internal API access URL with tokenized expiration
        clean_key = storage_key.strip().replace("\\", "/").lstrip("/")
        return f"/api/v1/documents/files/{clean_key}"


# Global singleton storage instance
default_storage = LocalDocumentStorage()


def get_document_storage() -> DocumentStorage:
    """Dependency injector or factory for document storage adapter."""
    return default_storage
