from datetime import UTC, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponseMeta(BaseModel):
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    request_id: str | None = None


class ApiResponse(BaseModel, Generic[T]):
    """Standard success API envelope matching TypeScript ApiResponse<T>."""
    success: bool = True
    data: T
    meta: ApiResponseMeta = Field(default_factory=ApiResponseMeta)


class PaginatedMeta(BaseModel):
    page: int
    page_size: int
    total_records: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated API envelope matching TypeScript PaginatedResponse<T>."""
    success: bool = True
    data: list[T]
    pagination: PaginatedMeta
    meta: ApiResponseMeta = Field(default_factory=ApiResponseMeta)


class ApiErrorDetail(BaseModel):
    field: str | None = None
    message: str
    code: str | None = None


class ApiErrorEnvelope(BaseModel):
    code: str
    message: str
    details: list[ApiErrorDetail] = Field(default_factory=list)
    request_id: str | None = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )


class ApiErrorResponse(BaseModel):
    """Standard error API envelope matching TypeScript ApiErrorResponse."""
    success: bool = False
    error: ApiErrorEnvelope


class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "campusos-api"
    version: str = "0.1.0"
    environment: str = "development"
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
