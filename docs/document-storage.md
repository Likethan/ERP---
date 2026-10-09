# CampusOS — Document Storage Abstraction & File Security Model

## 1. Architectural Philosophy

CampusOS documents and credentials represent sensitive student dossiers, financial ledgers, and institutional governance records. Under zero-trust principles:
1. **No Direct Filesystem / Public S3 Exposure**: Documents are never exposed via unauthenticated public URLs or unrestricted web directories.
2. **Pluggable Storage Abstraction**: Domain services interact strictly with an abstract interface (`DocumentStorage`), decoupling business logic from the underlying storage provider.
3. **Defense-in-Depth Validation**: File integrity, MIME typing, payload size, and filename safety are validated server-side prior to persistence.

---

## 2. Storage Interface (`DocumentStorage`)

Located at `app/core/storage.py`, the storage interface defines standard async operations:

```python
class DocumentStorage(ABC):
    @abstractmethod
    async def upload(self, file_content: bytes, destination_key: str, mime_type: str) -> str:
        """Persist binary stream and return unique storage reference key."""

    @abstractmethod
    async def download(self, storage_key: str) -> bytes:
        """Retrieve binary stream for the given storage reference key."""

    @abstractmethod
    async def delete(self, storage_key: str) -> bool:
        """Remove binary object from storage."""

    @abstractmethod
    async def exists(self, storage_key: str) -> bool:
        """Check whether object exists in storage."""

    @abstractmethod
    async def get_metadata(self, storage_key: str) -> dict[str, Any]:
        """Obtain size, MIME type, and checksum metadata."""

    @abstractmethod
    async def generate_access_reference(self, storage_key: str, expires_in_seconds: int = 3600) -> str:
        """Generate short-lived, authorized access reference."""
```

---

## 3. Storage Adapters

### 3.1 Local Storage Adapter (`LocalDocumentStorage`)
The primary developer and on-premise adapter stores assets in a sandboxed, configurable root directory (`settings.STORAGE_LOCAL_ROOT` or `apps/api/storage`):
- Automatically creates tenant-isolated directory trees.
- Validates canonical paths against root sandbox to prevent jailbreaks.
- Uses SHA-256 hashing for content verification.

### 3.2 Cloud Object Storage Architecture (AWS S3 / Azure Blob / GCS)
Production deployments swap `LocalDocumentStorage` with cloud providers using environment configuration (`STORAGE_BACKEND=s3`):

```text
                  DocumentStorage (ABC)
                     /            \
                    /              \
    LocalDocumentStorage          S3DocumentStorage
    (Filesystem Sandbox)          (Boto3 / MinIO SDK)
                                         |
                                  Pre-Signed URLs
                                  Server-Side KMS (AES-256)
```

The cloud adapter implements `generate_access_reference` using short-lived pre-signed GET URLs (typically 15–60 minutes expiry) signed with IAM credentials.

---

## 4. Security & Compliance Controls

### 4.1 Path Traversal Prevention
Storage keys are sanitized to strictly prevent path traversal attacks (`../`, `..\\`, absolute root paths, or null-byte injections):
```python
if ".." in storage_key or storage_key.startswith("/") or "\\" in storage_key:
    raise ValidationException("Invalid storage key: directory traversal pattern detected.")
```

### 4.2 MIME Whitelisting & Size Verification
The storage layer rejects unauthorized executable formats or oversized payloads:
- **Allowed MIME Types**: `application/pdf`, `image/jpeg`, `image/png`, `image/webp`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **Max File Size**: Default limit 25 MB (`26,214,400 bytes`). Payloads exceeding this raise `ValidationException` (HTTP 422/413).

### 4.3 Checksum Verification
Every uploaded file is hashed with SHA-256 during ingress. The digest is persisted alongside the document record and version history, allowing downstream verification desks to verify bit-level file integrity.

### 4.4 Tenant Isolation Pattern
Storage keys partition assets by tenant UUID:
```text
{tenant_id}/docs/{random_hex}_{sanitized_filename}
```
Cross-tenant access attempts are blocked at both the router layer and storage verification checks.
