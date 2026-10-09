"""Platform Administration Router: Multi-tenant SaaS lifecycle and management APIs.

Restricted exclusively to Platform Super Administrators.
Tenant Administrators have NO access to these endpoints.
"""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import require_platform_admin
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.models.core import Institution
from app.models.people import User
from app.schemas.core import (
    TenantCreateRequest,
    TenantResponse,
    TenantStatusUpdateRequest,
)

router = APIRouter(prefix="/platform/tenants", tags=["Platform Administration"])

VALID_TENANT_STATUSES = {"ACTIVE", "TRIAL", "SUSPENDED", "ARCHIVED"}


@router.get("", response_model=list[TenantResponse])
async def list_all_tenants(
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[TenantResponse]:
    """List all institutions/tenants across the entire SaaS platform."""
    stmt = select(Institution)
    if status_filter:
        stmt = stmt.where(Institution.status == status_filter.upper())
    stmt = stmt.order_by(Institution.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant_by_id(
    tenant_id: UUID,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TenantResponse:
    """Retrieve details for a specific tenant across the platform."""
    stmt = select(Institution).where(Institution.id == tenant_id)
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise NotFoundException("Tenant", tenant_id)
    return tenant


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    data: TenantCreateRequest,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TenantResponse:
    """Transactionally provision a new SaaS institution tenant with default configuration."""
    # Check code uniqueness
    existing_code = await db.execute(
        select(Institution).where(func.lower(Institution.code) == data.code.lower())
    )
    if existing_code.scalar_one_or_none():
        raise ConflictException(f"Tenant with code '{data.code}' already exists.")

    # Check slug uniqueness if provided
    slug_val = data.slug or data.code.lower().replace("_", "-")
    existing_slug = await db.execute(
        select(Institution).where(func.lower(Institution.slug) == slug_val.lower())
    )
    if existing_slug.scalar_one_or_none():
        raise ConflictException(f"Tenant with slug '{slug_val}' already exists.")

    tenant = Institution(
        code=data.code.upper(),
        slug=slug_val.lower(),
        legal_name=data.legal_name,
        short_name=data.short_name,
        plan=data.plan.upper(),
        status="ACTIVE",
        contact_email=data.contact_email,
        contact_phone=data.contact_phone,
        address_line1=data.address_line1,
        city=data.city,
        state=data.state,
        postal_code=data.postal_code,
        country=data.country,
        default_timezone=data.default_timezone,
        currency_code=data.currency_code.upper(),
        locale=data.locale,
        is_active=True,
    )
    db.add(tenant)
    await db.flush()
    await db.refresh(tenant)

    # Audit tenant provisioning
    from app.core.audit import AuditEventCategory, build_audit_entry

    db.add(
        build_audit_entry(
            tenant_id=tenant.id,
            action=AuditEventCategory.TENANT_CREATED,
            entity_type="Tenant",
            entity_id=tenant.id,
            user_id=_admin.id,
            business_context=f"Tenant '{tenant.code}' provisioned with plan '{tenant.plan}'.",
        )
    )

    return tenant


@router.patch("/{tenant_id}/status", response_model=TenantResponse)
async def update_tenant_status(
    tenant_id: UUID,
    payload: TenantStatusUpdateRequest,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TenantResponse:
    """Transition a tenant's operational status (ACTIVE, TRIAL, SUSPENDED, ARCHIVED)."""
    target_status = payload.status.upper()
    if target_status not in VALID_TENANT_STATUSES:
        raise BadRequestException(
            f"Invalid status '{payload.status}'. Must be one of: {', '.join(sorted(VALID_TENANT_STATUSES))}"
        )

    stmt = select(Institution).where(Institution.id == tenant_id)
    result = await db.execute(stmt)
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise NotFoundException("Tenant", tenant_id)

    old_status = tenant.status
    tenant.status = target_status
    now = datetime.now(timezone.utc)

    if target_status == "SUSPENDED":
        tenant.suspended_at = now
    elif target_status == "ARCHIVED":
        tenant.deleted_at = now
        tenant.is_active = False
    elif target_status in ("ACTIVE", "TRIAL"):
        tenant.suspended_at = None
        tenant.is_active = True

    await db.flush()
    await db.refresh(tenant)

    # Audit status transition
    from app.core.audit import AuditEventCategory, build_audit_entry

    action = (
        AuditEventCategory.TENANT_SUSPENDED
        if target_status == "SUSPENDED"
        else AuditEventCategory.TENANT_ARCHIVED
        if target_status == "ARCHIVED"
        else "TENANT_STATUS_UPDATED"
    )
    db.add(
        build_audit_entry(
            tenant_id=tenant.id,
            action=action,
            entity_type="Tenant",
            entity_id=tenant.id,
            user_id=_admin.id,
            old_values_json={"status": old_status},
            new_values_json={"status": target_status},
            business_context=f"Tenant status changed from {old_status} to {target_status}.",
        )
    )

    return tenant

