"""Multi-Factor Authentication (MFA) & TOTP Endpoints (Step 22)."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_active_user, get_tenant_context
from app.core.tenant import TenantContext
from app.identity.mfa_service import MfaService
from app.identity.policy_service import TenantIdentityPolicyService
from app.identity.schemas import (
    MfaChallengeResponse,
    MfaChallengeVerifyRequest,
    MfaStatusResponse,
    TotpEnrollResponse,
    TotpVerifyEnrollRequest,
)
from app.models.people import User
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/mfa", tags=["Multi-Factor Authentication"])


@router.get("/status", response_model=ApiResponse[MfaStatusResponse])
async def get_mfa_status(
    current_user: Annotated[User, Depends(get_current_active_user)],
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[MfaStatusResponse]:
    """Retrieve MFA enrollment status and tenant policy requirement for the user."""
    policy = await TenantIdentityPolicyService.get_policy(db, tenant_context.tenant_id)
    status_data = await MfaService.get_user_mfa_status(db, current_user, policy=policy)
    return ApiResponse(
        success=True,
        data=MfaStatusResponse.model_validate(status_data),
    )


@router.post("/enroll", response_model=ApiResponse[TotpEnrollResponse])
async def enroll_totp(
    current_user: Annotated[User, Depends(get_current_active_user)],
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[TotpEnrollResponse]:
    """Initiate TOTP enrollment. Returns Base32 secret, QR URI, and emergency recovery codes."""
    enroll_data = await MfaService.initiate_totp_enrollment(
        db, current_user, tenant_id=tenant_context.tenant_id
    )
    return ApiResponse(
        success=True,
        data=TotpEnrollResponse.model_validate(enroll_data),
        message=enroll_data["instructions"],
    )


@router.post("/verify", response_model=ApiResponse[dict[str, str]])
async def verify_totp_enrollment(
    payload: TotpVerifyEnrollRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[dict[str, str]]:
    """Verify code from authenticator app to activate TOTP multi-factor protection."""
    await MfaService.verify_totp_enrollment(
        db,
        user_id=current_user.id,
        factor_id=payload.factor_id,
        code=payload.code,
    )
    return ApiResponse(
        success=True,
        data={"status": "ACTIVATED"},
        message="TOTP multi-factor authentication successfully enabled.",
    )


@router.post("/challenge/verify", response_model=ApiResponse[dict[str, str]])
async def verify_mfa_challenge(
    payload: MfaChallengeVerifyRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[dict[str, str]]:
    """Verify an active MFA challenge using a TOTP code or emergency recovery code."""
    user_id = await MfaService.verify_mfa_challenge(
        db,
        challenge_token=payload.challenge_token,
        code=payload.code,
    )
    await db.commit()
    return ApiResponse(
        success=True,
        data={"status": "VERIFIED", "user_id": str(user_id)},
        message="MFA challenge successfully verified.",
    )


@router.post("/disable", response_model=ApiResponse[dict[str, str]])
async def disable_mfa(
    code: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[dict[str, str]]:
    """Disable MFA factors after validating with current TOTP or recovery code."""
    await MfaService.disable_mfa(db, user_id=current_user.id, verification_code=code)
    return ApiResponse(
        success=True,
        data={"status": "DISABLED"},
        message="MFA protection disabled for account.",
    )
