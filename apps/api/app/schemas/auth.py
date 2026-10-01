"""Authentication and identity request/response Pydantic schemas."""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Institutional email address")
    password: str = Field(..., min_length=1, description="Account password")


class AuthRoleInfo(BaseModel):
    id: UUID
    name: str
    display_name: str
    campus_id: UUID | None = None
    department_id: UUID | None = None


class AuthTenantInfo(BaseModel):
    id: UUID
    code: str
    name: str


class CurrentUserResponse(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    status: str
    roles: list[AuthRoleInfo] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    tenant: AuthTenantInfo | None = None


# Alias for backward-compatibility and unified API contract
UserResponse = CurrentUserResponse


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., description="Existing account password")
    new_password: str = Field(..., min_length=8, description="New compliant password")
    confirm_password: str = Field(..., min_length=8, description="Confirmation of new password")


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Registered user email address")


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Password reset one-time token")
    new_password: str = Field(..., min_length=8, description="New compliant password")
    confirm_password: str = Field(..., min_length=8, description="Confirmation of new password")


class MessageResponse(BaseModel):
    message: str
