"""Pydantic schemas for Admin User and Role Management (RBAC)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdminRoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    display_name: str
    description: str | None = None
    is_system: bool = False
    permissions_count: int = 0
    permissions: list[str] = Field(default_factory=list)


class AdminUserRoleInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID  # Assignment ID
    role_id: UUID
    role_name: str
    display_name: str
    campus_id: UUID | None = None
    department_id: UUID | None = None


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    first_name: str
    last_name: str
    phone_number: str | None = None
    status: str
    roles: list[AdminUserRoleInfo] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class AdminUserCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(default="Welcome@123", min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone_number: str | None = Field(None, max_length=32)
    role_id: UUID | None = None
    campus_id: UUID | None = None
    department_id: UUID | None = None


class AdminRoleAssignRequest(BaseModel):
    role_id: UUID
    campus_id: UUID | None = None
    department_id: UUID | None = None


class AdminUserStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(ACTIVE|SUSPENDED|INACTIVE)$")
    reason: str | None = None
