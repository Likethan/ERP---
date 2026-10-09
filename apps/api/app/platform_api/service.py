"""Platform API Management & Developer Service (Step 21).

Coordinates:
- Application lifecycle state machines (Draft -> Submitted -> Approved -> Active -> Suspended -> Revoked -> Archived).
- Credential issuance, one-time secret returns, overlapping grace rotations, and revocations.
- Capability scope request gating and approval audits.
- Full tenant boundary enforcement and owner/administrator authorization.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
)
from app.platform_api.auth import (
    generate_api_key_credentials,
)
from app.platform_api.models import (
    ApiChangelog,
    ApiProduct,
    ApplicationApprovalAudit,
    ApplicationCredential,
    ApplicationEnvironment,
    ApplicationScopeGrant,
    ApplicationStatus,
    CredentialStatus,
    DeveloperApplication,
    ScopeGrantStatus,
)
from app.platform_api.schemas import (
    ApplicationCreate,
    ApplicationUpdate,
    CredentialCreate,
)
from app.platform_api.scopes import API_SCOPE_REGISTRY, scope_resolver


class PlatformApiService:
    """Core domain service for the Enterprise API Platform."""

    # -------------------------------------------------------------------------
    # 1. Developer Applications
    # -------------------------------------------------------------------------

    @classmethod
    async def create_application(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        owner_id: UUID,
        data: ApplicationCreate,
    ) -> DeveloperApplication:
        """Register a new developer application in DRAFT status."""
        # Enforce unique application name within the tenant
        stmt = select(DeveloperApplication).where(
            DeveloperApplication.tenant_id == tenant_id,
            DeveloperApplication.name == data.name.strip(),
        )
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ConflictException("Application", "name", data.name)

        # For development environment, application can become ACTIVE immediately;
        # For PRODUCTION, it starts in DRAFT requiring approval.
        initial_status = (
            ApplicationStatus.ACTIVE.value
            if data.environment.upper() == ApplicationEnvironment.DEVELOPMENT.value
            else ApplicationStatus.DRAFT.value
        )

        app = DeveloperApplication(
            tenant_id=tenant_id,
            name=data.name.strip(),
            description=data.description,
            application_type=data.application_type.upper(),
            owner_id=owner_id,
            status=initial_status,
            environment=data.environment.upper(),
            rate_limit_tier=data.rate_limit_tier.upper(),
            quota_tier=data.quota_tier.upper(),
            allowed_ips=data.allowed_ips,
            callback_urls=data.callback_urls,
        )
        db.add(app)
        await db.flush()
        return app

    @classmethod
    async def list_applications(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        owner_id: UUID | None = None,
        is_admin: bool = False,
    ) -> list[DeveloperApplication]:
        """List developer applications for the tenant. Non-admins only see their own."""
        stmt = select(DeveloperApplication).where(DeveloperApplication.tenant_id == tenant_id)
        if not is_admin and owner_id:
            stmt = stmt.where(DeveloperApplication.owner_id == owner_id)
        stmt = stmt.order_by(DeveloperApplication.created_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def get_application(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        application_id: UUID,
        owner_id: UUID | None = None,
        is_admin: bool = False,
    ) -> DeveloperApplication:
        """Fetch developer application enforcing tenant boundary and ownership."""
        stmt = select(DeveloperApplication).where(
            DeveloperApplication.tenant_id == tenant_id,
            DeveloperApplication.id == application_id,
        )
        res = await db.execute(stmt)
        app = res.scalar_one_or_none()
        if not app:
            raise NotFoundException("DeveloperApplication", application_id)

        if not is_admin and owner_id and app.owner_id != owner_id:
            raise PermissionDeniedException(
                "You do not have permission to inspect this application."
            )

        return app

    @classmethod
    async def update_application(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        application_id: UUID,
        data: ApplicationUpdate,
        user_id: UUID,
        is_admin: bool = False,
    ) -> DeveloperApplication:
        """Update mutable configuration of an application."""
        app = await cls.get_application(db, tenant_id, application_id, user_id, is_admin)

        if data.name and data.name.strip() != app.name:
            # Check unique name within tenant
            stmt = select(DeveloperApplication).where(
                DeveloperApplication.tenant_id == tenant_id,
                DeveloperApplication.name == data.name.strip(),
                DeveloperApplication.id != application_id,
            )
            res = await db.execute(stmt)
            if res.scalar_one_or_none():
                raise ConflictException("Application", "name", data.name)
            app.name = data.name.strip()

        if data.description is not None:
            app.description = data.description
        if data.allowed_ips is not None:
            app.allowed_ips = data.allowed_ips
        if data.callback_urls is not None:
            app.callback_urls = data.callback_urls

        # Tier modifications require institutional admin privileges
        if data.rate_limit_tier:
            if not is_admin:
                raise PermissionDeniedException("Only administrators can modify rate limit tiers.")
            app.rate_limit_tier = data.rate_limit_tier.upper()

        if data.quota_tier:
            if not is_admin:
                raise PermissionDeniedException("Only administrators can modify quota tiers.")
            app.quota_tier = data.quota_tier.upper()

        await db.flush()
        return app

    @classmethod
    async def submit_application(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        application_id: UUID,
        user_id: UUID,
        notes: str | None = None,
    ) -> DeveloperApplication:
        """Submit a DRAFT application for review and approval."""
        app = await cls.get_application(db, tenant_id, application_id, user_id, is_admin=False)
        if app.status not in (ApplicationStatus.DRAFT.value, ApplicationStatus.REVOKED.value):
            raise ValidationException(f"Cannot submit application in status '{app.status}'.")

        prev_status = app.status
        app.status = ApplicationStatus.PENDING_APPROVAL.value
        app.submitted_at = datetime.now(UTC)
        app.approval_notes = notes

        audit = ApplicationApprovalAudit(
            application_id=app.id,
            reviewer_id=user_id,
            action="SUBMITTED",
            reason=notes,
            previous_status=prev_status,
            new_status=app.status,
        )
        db.add(audit)
        await db.flush()
        return app

    @classmethod
    async def approve_application(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        application_id: UUID,
        reviewer_id: UUID,
        notes: str | None = None,
    ) -> DeveloperApplication:
        """Administrator approves a PENDING_APPROVAL application into ACTIVE state."""
        app = await cls.get_application(db, tenant_id, application_id, is_admin=True)
        if app.status != ApplicationStatus.PENDING_APPROVAL.value:
            raise ValidationException(f"Cannot approve application with status '{app.status}'.")

        prev_status = app.status
        app.status = ApplicationStatus.ACTIVE.value
        app.approved_by = reviewer_id
        app.approved_at = datetime.now(UTC)
        app.approval_notes = notes
        app.rejection_reason = None

        audit = ApplicationApprovalAudit(
            application_id=app.id,
            reviewer_id=reviewer_id,
            action="APPROVED",
            reason=notes,
            previous_status=prev_status,
            new_status=app.status,
        )
        db.add(audit)
        await db.flush()
        return app

    @classmethod
    async def reject_application(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        application_id: UUID,
        reviewer_id: UUID,
        reason: str | None = None,
    ) -> DeveloperApplication:
        """Administrator rejects an application."""
        app = await cls.get_application(db, tenant_id, application_id, is_admin=True)
        if app.status != ApplicationStatus.PENDING_APPROVAL.value:
            raise ValidationException(f"Cannot reject application with status '{app.status}'.")

        prev_status = app.status
        app.status = ApplicationStatus.DRAFT.value
        app.rejection_reason = reason or "Application submission was rejected during review."

        audit = ApplicationApprovalAudit(
            application_id=app.id,
            reviewer_id=reviewer_id,
            action="REJECTED",
            reason=reason,
            previous_status=prev_status,
            new_status=app.status,
        )
        db.add(audit)
        await db.flush()
        return app

    @classmethod
    async def suspend_application(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        application_id: UUID,
        reviewer_id: UUID,
        reason: str | None = None,
    ) -> DeveloperApplication:
        """Administrator suspends an application and blocks its traffic."""
        app = await cls.get_application(db, tenant_id, application_id, is_admin=True)
        prev_status = app.status
        app.status = ApplicationStatus.SUSPENDED.value

        audit = ApplicationApprovalAudit(
            application_id=app.id,
            reviewer_id=reviewer_id,
            action="SUSPENDED",
            reason=reason,
            previous_status=prev_status,
            new_status=app.status,
        )
        db.add(audit)
        await db.flush()
        return app

    @classmethod
    async def archive_application(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        application_id: UUID,
        user_id: UUID,
        is_admin: bool = False,
    ) -> DeveloperApplication:
        """Retire/archive an application and revoke all its active credentials."""
        app = await cls.get_application(db, tenant_id, application_id, user_id, is_admin)
        prev_status = app.status
        app.status = ApplicationStatus.ARCHIVED.value

        # Revoke all credentials
        cred_stmt = select(ApplicationCredential).where(
            ApplicationCredential.application_id == app.id,
            ApplicationCredential.status.in_(
                [CredentialStatus.ACTIVE.value, CredentialStatus.ROTATING.value]
            ),
        )
        cred_res = await db.execute(cred_stmt)
        for cred in cred_res.scalars().all():
            cred.status = CredentialStatus.REVOKED.value
            cred.revoked_at = datetime.now(UTC)
            cred.revoked_by = user_id
            cred.revocation_reason = "Application archived."

        audit = ApplicationApprovalAudit(
            application_id=app.id,
            reviewer_id=user_id,
            action="ARCHIVED",
            reason="Application decommissioned.",
            previous_status=prev_status,
            new_status=app.status,
        )
        db.add(audit)
        await db.flush()
        return app

    # -------------------------------------------------------------------------
    # 2. Application Credentials
    # -------------------------------------------------------------------------

    @classmethod
    async def create_credential(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        application_id: UUID,
        data: CredentialCreate,
        user_id: UUID,
        is_admin: bool = False,
    ) -> tuple[ApplicationCredential, str]:
        """Issue a new API credential. Returns (credential, raw_secret).

        The raw_secret is only accessible once during creation and NEVER saved in plaintext.
        """
        app = await cls.get_application(db, tenant_id, application_id, user_id, is_admin)

        # Enforce environment matching: credentials cannot target an environment higher than the application
        if (
            app.environment == ApplicationEnvironment.DEVELOPMENT.value
            and data.environment.upper() == ApplicationEnvironment.PRODUCTION.value
        ):
            raise ValidationException(
                "Cannot issue PRODUCTION credentials for a DEVELOPMENT application."
            )

        client_id, raw_secret, key_prefix, secret_hash = generate_api_key_credentials(
            data.environment.upper()
        )

        now = datetime.now(UTC)
        expires_at = now + timedelta(days=data.expires_in_days) if data.expires_in_days else None

        credential = ApplicationCredential(
            tenant_id=tenant_id,
            application_id=application_id,
            name=data.name.strip(),
            credential_type=data.credential_type.upper(),
            client_id=client_id,
            key_prefix=key_prefix,
            secret_hash=secret_hash,
            environment=data.environment.upper(),
            status=CredentialStatus.ACTIVE.value,
            expires_at=expires_at,
        )
        db.add(credential)
        await db.flush()
        return credential, raw_secret

    @classmethod
    async def list_credentials(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        application_id: UUID,
        user_id: UUID,
        is_admin: bool = False,
    ) -> list[ApplicationCredential]:
        """List credentials for an application. Plaintext secrets are NEVER present."""
        await cls.get_application(db, tenant_id, application_id, user_id, is_admin)
        stmt = (
            select(ApplicationCredential)
            .where(
                ApplicationCredential.tenant_id == tenant_id,
                ApplicationCredential.application_id == application_id,
            )
            .order_by(ApplicationCredential.created_at.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def rotate_credential(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        application_id: UUID,
        credential_id: UUID,
        overlap_hours: int,
        user_id: UUID,
        is_admin: bool = False,
    ) -> tuple[ApplicationCredential, ApplicationCredential, str]:
        """Safely rotate a credential with an overlap window.

        Flow:
        1. Current key transitions to ROTATING with grace_period_expires_at = now + overlap_hours.
        2. New key created with status ACTIVE.
        3. Returns (retiring_cred, active_cred, raw_new_secret).
        """
        await cls.get_application(db, tenant_id, application_id, user_id, is_admin)

        stmt = select(ApplicationCredential).where(
            ApplicationCredential.tenant_id == tenant_id,
            ApplicationCredential.application_id == application_id,
            ApplicationCredential.id == credential_id,
        )
        res = await db.execute(stmt)
        old_cred = res.scalar_one_or_none()
        if not old_cred:
            raise NotFoundException("ApplicationCredential", credential_id)

        if old_cred.status not in (CredentialStatus.ACTIVE.value, CredentialStatus.ROTATING.value):
            raise ValidationException(f"Cannot rotate credential in status '{old_cred.status}'.")

        now = datetime.now(UTC)
        grace_expires = now + timedelta(hours=overlap_hours)

        old_cred.status = CredentialStatus.ROTATING.value
        old_cred.grace_period_expires_at = grace_expires

        # Generate replacement key with identical environment & type
        client_id, raw_secret, key_prefix, secret_hash = generate_api_key_credentials(
            old_cred.environment
        )

        new_cred = ApplicationCredential(
            tenant_id=tenant_id,
            application_id=application_id,
            name=f"{old_cred.name} (Rotated)",
            credential_type=old_cred.credential_type,
            client_id=client_id,
            key_prefix=key_prefix,
            secret_hash=secret_hash,
            environment=old_cred.environment,
            status=CredentialStatus.ACTIVE.value,
            expires_at=old_cred.expires_at,
        )
        db.add(new_cred)
        await db.flush()

        return old_cred, new_cred, raw_secret

    @classmethod
    async def revoke_credential(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        application_id: UUID,
        credential_id: UUID,
        reason: str | None,
        user_id: UUID,
        is_admin: bool = False,
    ) -> ApplicationCredential:
        """Immediately revoke an API credential."""
        await cls.get_application(db, tenant_id, application_id, user_id, is_admin)

        stmt = select(ApplicationCredential).where(
            ApplicationCredential.tenant_id == tenant_id,
            ApplicationCredential.application_id == application_id,
            ApplicationCredential.id == credential_id,
        )
        res = await db.execute(stmt)
        cred = res.scalar_one_or_none()
        if not cred:
            raise NotFoundException("ApplicationCredential", credential_id)

        cred.status = CredentialStatus.REVOKED.value
        cred.revoked_at = datetime.now(UTC)
        cred.revoked_by = user_id
        cred.revocation_reason = reason or "Revoked by user/admin."

        await db.flush()
        return cred

    # -------------------------------------------------------------------------
    # 3. Scope Grants & Approvals
    # -------------------------------------------------------------------------

    @classmethod
    async def request_scopes(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        application_id: UUID,
        scope_codes: list[str],
        user_id: UUID,
        justification: str | None = None,
        is_admin: bool = False,
    ) -> list[ApplicationScopeGrant]:
        """Request capability scopes for an application.

        High-risk scopes are placed in PENDING_APPROVAL unless user is administrator.
        """
        await cls.get_application(db, tenant_id, application_id, user_id, is_admin)
        high_risk_set = scope_resolver.get_high_risk_scopes()
        grants = []

        for code in scope_codes:
            code_str = code.strip()
            if code_str not in API_SCOPE_REGISTRY:
                raise ValidationException(f"Invalid capability scope '{code_str}'.")

            # Check existing grant
            stmt = select(ApplicationScopeGrant).where(
                ApplicationScopeGrant.application_id == application_id,
                ApplicationScopeGrant.scope_code == code_str,
            )
            res = await db.execute(stmt)
            existing = res.scalar_one_or_none()

            # Auto-grant for non-high-risk scopes or when granted by administrator
            is_high_risk = code_str in high_risk_set
            initial_status = (
                ScopeGrantStatus.GRANTED.value
                if (not is_high_risk or is_admin)
                else ScopeGrantStatus.PENDING_APPROVAL.value
            )

            if existing:
                if existing.status in (
                    ScopeGrantStatus.REVOKED.value,
                    ScopeGrantStatus.REJECTED.value,
                ):
                    existing.status = initial_status
                    existing.review_notes = justification
                    existing.granted_by = user_id if is_admin else None
                    grants.append(existing)
            else:
                grant = ApplicationScopeGrant(
                    tenant_id=tenant_id,
                    application_id=application_id,
                    scope_code=code_str,
                    status=initial_status,
                    granted_by=user_id if is_admin else None,
                    review_notes=justification,
                )
                db.add(grant)
                grants.append(grant)

        await db.flush()
        return grants

    @classmethod
    async def list_scopes(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        application_id: UUID,
        user_id: UUID,
        is_admin: bool = False,
    ) -> list[ApplicationScopeGrant]:
        """List scope grants for an application."""
        await cls.get_application(db, tenant_id, application_id, user_id, is_admin)
        stmt = (
            select(ApplicationScopeGrant)
            .where(
                ApplicationScopeGrant.tenant_id == tenant_id,
                ApplicationScopeGrant.application_id == application_id,
            )
            .order_by(ApplicationScopeGrant.created_at.asc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def approve_scope(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        application_id: UUID,
        grant_id: UUID,
        reviewer_id: UUID,
        notes: str | None = None,
    ) -> ApplicationScopeGrant:
        """Administrative approval of a high-risk capability scope grant."""
        await cls.get_application(db, tenant_id, application_id, is_admin=True)

        stmt = select(ApplicationScopeGrant).where(
            ApplicationScopeGrant.tenant_id == tenant_id,
            ApplicationScopeGrant.application_id == application_id,
            ApplicationScopeGrant.id == grant_id,
        )
        res = await db.execute(stmt)
        grant = res.scalar_one_or_none()
        if not grant:
            raise NotFoundException("ApplicationScopeGrant", grant_id)

        grant.status = ScopeGrantStatus.GRANTED.value
        grant.granted_by = reviewer_id
        grant.granted_at = datetime.now(UTC)
        grant.review_notes = notes

        await db.flush()
        return grant

    @classmethod
    async def revoke_scope(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        application_id: UUID,
        grant_id: UUID,
        reviewer_id: UUID,
    ) -> ApplicationScopeGrant:
        """Revoke a capability scope grant."""
        await cls.get_application(db, tenant_id, application_id, is_admin=True)

        stmt = select(ApplicationScopeGrant).where(
            ApplicationScopeGrant.tenant_id == tenant_id,
            ApplicationScopeGrant.application_id == application_id,
            ApplicationScopeGrant.id == grant_id,
        )
        res = await db.execute(stmt)
        grant = res.scalar_one_or_none()
        if not grant:
            raise NotFoundException("ApplicationScopeGrant", grant_id)

        grant.status = ScopeGrantStatus.REVOKED.value
        grant.revoked_at = datetime.now(UTC)

        await db.flush()
        return grant

    # -------------------------------------------------------------------------
    # 4. Catalog & Changelog Exploration
    # -------------------------------------------------------------------------

    @classmethod
    async def list_catalog(cls, db: AsyncSession) -> list[ApiProduct]:
        """Fetch all exposed API products with their operations."""
        stmt = (
            select(ApiProduct)
            .options(selectinload(ApiProduct.operations))
            .order_by(ApiProduct.name.asc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def get_catalog_product(cls, db: AsyncSession, code: str) -> ApiProduct:
        """Fetch single catalog product by code."""
        stmt = (
            select(ApiProduct)
            .where(ApiProduct.code == code)
            .options(selectinload(ApiProduct.operations))
        )
        res = await db.execute(stmt)
        prod = res.scalar_one_or_none()
        if not prod:
            raise NotFoundException("ApiProduct", code)
        return prod

    @classmethod
    async def list_changelogs(cls, db: AsyncSession) -> list[ApiChangelog]:
        """Fetch version history and changelogs."""
        stmt = select(ApiChangelog).order_by(ApiChangelog.release_date.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())


platform_service = PlatformApiService()
