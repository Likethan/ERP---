"""Governance Business Service for CampusOS.

Orchestrates institutional data governance policies, immutable policy versioning,
administrative & legal holds, and regulatory access review campaigns.
"""

from datetime import UTC, datetime
import logging
import re
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import AuditEventCategory, build_audit_entry
from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.core.governance_registry import SENSITIVE_FIELD_REGISTRY
from app.models.governance import (
    AccessReview,
    AccessReviewDecisionType,
    AccessReviewItem,
    AccessReviewStatus,
    GovernanceHold,
    GovernancePolicy,
    GovernancePolicyCategory,
    GovernancePolicyStatus,
    GovernancePolicyVersion,
    HoldStatus,
    PrivacyRequest,
    PrivacyRequestStatus,
    RetentionPolicy,
)
from app.models.people import Role, User, UserRoleAssignment
from app.schemas.governance import (
    AccessReviewCreate,
    AccessReviewItemDecide,
    GovernanceHoldCreate,
    GovernanceHoldRelease,
    GovernancePolicyCreate,
    GovernancePolicyUpdate,
    GovernancePolicyVersionCreate,
    GovernanceSummaryRead,
)

logger = logging.getLogger("campusos.governance")


class GovernanceService:
    """Manages policies, holds, and access review campaigns with strict tenant scoping."""

    # =========================================================================
    # 1. POLICIES & POLICY VERSIONING
    # =========================================================================

    @classmethod
    async def create_policy(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        payload: GovernancePolicyCreate,
        actor_id: UUID | None = None,
    ) -> GovernancePolicy:
        """Create a new governance policy with an initial immutable Version 1."""
        slug = re.sub(r"[^a-zA-Z0-9_]", "_", payload.code.upper().strip())

        # Check uniqueness per tenant
        existing_stmt = select(GovernancePolicy).where(
            and_(
                GovernancePolicy.tenant_id == tenant_id,
                GovernancePolicy.code == slug,
            )
        )
        if (await db.execute(existing_stmt)).scalar_one_or_none():
            raise ConflictException(f"Governance policy with code '{slug}' already exists in this institution.")

        policy_id = uuid4()
        version_id = uuid4()
        now = datetime.now(UTC)

        policy = GovernancePolicy(
            id=policy_id,
            tenant_id=tenant_id,
            name=payload.name.strip(),
            code=slug,
            category=payload.category,
            description=payload.description,
            status=payload.status,
            is_system_default=False,
            active_version_id=version_id,
            created_by_user_id=actor_id,
            updated_by_user_id=actor_id,
            created_at=now,
            updated_at=now,
        )
        db.add(policy)

        version = GovernancePolicyVersion(
            id=version_id,
            tenant_id=tenant_id,
            policy_id=policy_id,
            version_number=1,
            status=GovernancePolicyStatus.ACTIVE,
            rules_json=payload.initial_rules,
            change_summary=payload.change_summary or "Initial policy rule configuration",
            effective_from=now,
            created_by_user_id=actor_id,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(version)
        policy.versions.append(version)

        # Audit
        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.POLICY_CHANGE,
                entity_type="GovernancePolicy",
                entity_id=policy_id,
                user_id=actor_id,
                new_values_json={"code": slug, "name": policy.name, "version": 1},
            )
        )

        await db.commit()
        return await cls.get_policy(db, tenant_id, policy_id)

    @classmethod
    async def get_policy(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        policy_id: UUID,
    ) -> GovernancePolicy:
        """Fetch policy by ID ensuring strict tenant scoping."""
        stmt = (
            select(GovernancePolicy)
            .options(selectinload(GovernancePolicy.versions))
            .where(
                and_(
                    GovernancePolicy.id == policy_id,
                    or_(
                        GovernancePolicy.tenant_id == tenant_id,
                        GovernancePolicy.is_system_default == True,
                    ),
                )
            )
        )
        policy = (await db.execute(stmt)).scalar_one_or_none()
        if not policy:
            raise NotFoundException("GovernancePolicy", policy_id)
        return policy

    @classmethod
    async def list_policies(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        category: str | None = None,
        status: str | None = None,
    ) -> list[GovernancePolicy]:
        """List institutional governance policies."""
        stmt = (
            select(GovernancePolicy)
            .options(selectinload(GovernancePolicy.versions))
            .where(
                and_(
                    or_(
                        GovernancePolicy.tenant_id == tenant_id,
                        GovernancePolicy.is_system_default == True,
                    ),
                    GovernancePolicy.category == category if category else True,
                    GovernancePolicy.status == status if status else True,
                )
            )
            .order_by(GovernancePolicy.created_at.desc())
        )
        return list((await db.execute(stmt)).scalars().all())

    @classmethod
    async def update_policy(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        policy_id: UUID,
        payload: GovernancePolicyUpdate,
        actor_id: UUID | None = None,
    ) -> GovernancePolicy:
        """Update top-level policy metadata."""
        policy = await cls.get_policy(db, tenant_id, policy_id)
        if policy.is_system_default:
            raise ForbiddenException("System default policies cannot be modified directly.")

        old_vals = {"name": policy.name, "status": policy.status}
        if payload.name is not None:
            policy.name = payload.name.strip()
        if payload.description is not None:
            policy.description = payload.description
        if payload.status is not None:
            policy.status = payload.status
        policy.updated_by_user_id = actor_id
        policy.updated_at = datetime.now(UTC)

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.POLICY_CHANGE,
                entity_type="GovernancePolicy",
                entity_id=policy.id,
                user_id=actor_id,
                old_values_json=old_vals,
                new_values_json={"name": policy.name, "status": policy.status},
            )
        )

        await db.commit()
        return await cls.get_policy(db, tenant_id, policy_id)

    @classmethod
    async def create_policy_version(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        policy_id: UUID,
        payload: GovernancePolicyVersionCreate,
        actor_id: UUID | None = None,
    ) -> GovernancePolicyVersion:
        """Create a new immutable version for an existing policy, bumping version number."""
        policy = await cls.get_policy(db, tenant_id, policy_id)
        if policy.is_system_default:
            raise ForbiddenException("Cannot version system default policies directly.")

        highest_v = max((v.version_number for v in policy.versions), default=0)
        next_v = highest_v + 1
        now = datetime.now(UTC)

        # Deactivate previous active version
        for v in policy.versions:
            if v.is_active:
                v.is_active = False
                v.effective_until = now

        version = GovernancePolicyVersion(
            id=uuid4(),
            tenant_id=tenant_id,
            policy_id=policy.id,
            version_number=next_v,
            status=GovernancePolicyStatus.ACTIVE,
            rules_json=payload.rules_json,
            change_summary=payload.change_summary or f"Version bump to v{next_v}",
            effective_from=payload.effective_from or now,
            effective_until=payload.effective_until,
            created_by_user_id=actor_id,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(version)
        policy.active_version_id = version.id
        policy.updated_by_user_id = actor_id
        policy.updated_at = now

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.POLICY_CHANGE,
                entity_type="GovernancePolicyVersion",
                entity_id=version.id,
                user_id=actor_id,
                new_values_json={"policy_id": str(policy.id), "version": next_v},
            )
        )

        await db.commit()
        await db.refresh(version)
        return version

    # =========================================================================
    # 2. LEGAL / GOVERNANCE HOLDS
    # =========================================================================

    @classmethod
    async def create_hold(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        payload: GovernanceHoldCreate,
        actor_id: UUID | None = None,
    ) -> GovernanceHold:
        """Place an administrative or legal hold preventing automated deletion or anonymization."""
        now = datetime.now(UTC)
        hold = GovernanceHold(
            id=uuid4(),
            tenant_id=tenant_id,
            name=payload.name.strip(),
            case_reference=payload.case_reference.strip() if payload.case_reference else None,
            target_entity_type=payload.target_entity_type.upper(),
            target_entity_id=payload.target_entity_id,
            reason=payload.reason.strip(),
            status=HoldStatus.ACTIVE,
            expires_at=payload.expires_at,
            created_by_user_id=actor_id,
            created_at=now,
            updated_at=now,
        )
        db.add(hold)

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.LEGAL_HOLD,
                entity_type="GovernanceHold",
                entity_id=hold.id,
                user_id=actor_id,
                new_values_json={
                    "name": hold.name,
                    "target_entity_type": hold.target_entity_type,
                    "target_entity_id": str(hold.target_entity_id) if hold.target_entity_id else None,
                    "status": "ACTIVE",
                },
            )
        )

        await db.commit()
        await db.refresh(hold)
        logger.info("Placed legal hold '%s' (ID: %s) for tenant %s", hold.name, hold.id, tenant_id)
        return hold

    @classmethod
    async def release_hold(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        hold_id: UUID,
        payload: GovernanceHoldRelease,
        actor_id: UUID | None = None,
    ) -> GovernanceHold:
        """Release an active hold with mandatory documented justification."""
        stmt = select(GovernanceHold).where(
            and_(
                GovernanceHold.id == hold_id,
                GovernanceHold.tenant_id == tenant_id,
            )
        )
        hold = (await db.execute(stmt)).scalar_one_or_none()
        if not hold:
            raise NotFoundException("GovernanceHold", hold_id)

        if hold.status != HoldStatus.ACTIVE:
            raise ConflictException(f"Governance hold is already {hold.status}.")

        now = datetime.now(UTC)
        hold.status = HoldStatus.RELEASED
        hold.released_by_user_id = actor_id
        hold.released_at = now
        hold.release_reason = payload.release_reason.strip()
        hold.updated_at = now

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.LEGAL_HOLD,
                entity_type="GovernanceHold",
                entity_id=hold.id,
                user_id=actor_id,
                new_values_json={"status": "RELEASED", "release_reason": hold.release_reason},
            )
        )

        await db.commit()
        await db.refresh(hold)
        logger.info("Released legal hold '%s' (ID: %s) for tenant %s", hold.name, hold.id, tenant_id)
        return hold

    @classmethod
    async def list_holds(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        status: str | None = None,
        entity_type: str | None = None,
    ) -> list[GovernanceHold]:
        """List active or historical holds in the institution."""
        stmt = (
            select(GovernanceHold)
            .where(
                and_(
                    GovernanceHold.tenant_id == tenant_id,
                    GovernanceHold.status == status if status else True,
                    GovernanceHold.target_entity_type == entity_type.upper() if entity_type else True,
                )
            )
            .order_by(GovernanceHold.created_at.desc())
        )
        return list((await db.execute(stmt)).scalars().all())

    @classmethod
    async def is_record_held(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        entity_type: str,
        entity_id: UUID,
    ) -> tuple[bool, str | None]:
        """Check whether a specific record or its entity type is blocked by an active legal hold."""
        clean_type = entity_type.upper().strip()
        now = datetime.now(UTC)

        stmt = select(GovernanceHold).where(
            and_(
                GovernanceHold.tenant_id == tenant_id,
                GovernanceHold.status == HoldStatus.ACTIVE,
                or_(
                    GovernanceHold.expires_at == None,  # noqa: E711
                    GovernanceHold.expires_at > now,
                ),
                or_(
                    GovernanceHold.target_entity_type == "ALL",
                    and_(
                        GovernanceHold.target_entity_type == clean_type,
                        or_(
                            GovernanceHold.target_entity_id == None,  # noqa: E711 - holds entire entity domain
                            GovernanceHold.target_entity_id == entity_id,
                        ),
                    ),
                ),
            )
        )
        matching_holds = (await db.execute(stmt)).scalars().all()
        for hold in matching_holds:
            if hold.is_active:
                return True, f"Active legal hold '{hold.name}' (Case: {hold.case_reference or 'N/A'}): {hold.reason}"

        return False, None

    # =========================================================================
    # 3. ACCESS REVIEWS
    # =========================================================================

    @classmethod
    async def create_access_review(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        payload: AccessReviewCreate,
        actor_id: UUID | None = None,
    ) -> AccessReview:
        """Create an access review campaign and populate privileged user items."""
        now = datetime.now(UTC)
        review_id = uuid4()

        review = AccessReview(
            id=review_id,
            tenant_id=tenant_id,
            title=payload.title.strip(),
            description=payload.description,
            review_type=payload.review_type,
            status=AccessReviewStatus.OPEN,
            due_date=payload.due_date,
            reviewer_user_id=actor_id,
            created_at=now,
            updated_at=now,
        )
        db.add(review)

        # Discover privileged role assignments in this tenant
        role_stmt = (
            select(UserRoleAssignment)
            .join(Role, UserRoleAssignment.role_id == Role.id)
            .where(UserRoleAssignment.tenant_id == tenant_id)
        )
        assignments = (await db.execute(role_stmt)).scalars().all()

        for a in assignments:
            item = AccessReviewItem(
                id=uuid4(),
                tenant_id=tenant_id,
                review_id=review_id,
                user_id=a.user_id,
                role_id=a.role_id,
                decision=AccessReviewDecisionType.PENDING,
                created_at=now,
                updated_at=now,
            )
            db.add(item)
            review.items.append(item)

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.ACCESS_REVIEW,
                entity_type="AccessReview",
                entity_id=review_id,
                user_id=actor_id,
                new_values_json={"title": review.title, "items_count": len(assignments)},
            )
        )

        await db.commit()
        return await cls.get_access_review(db, tenant_id, review_id)

    @classmethod
    async def get_access_review(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        review_id: UUID,
    ) -> AccessReview:
        """Fetch access review campaign with items."""
        stmt = (
            select(AccessReview)
            .options(selectinload(AccessReview.items))
            .where(
                and_(
                    AccessReview.id == review_id,
                    AccessReview.tenant_id == tenant_id,
                )
            )
        )
        review = (await db.execute(stmt)).scalar_one_or_none()
        if not review:
            raise NotFoundException("AccessReview", review_id)
        return review

    @classmethod
    async def list_access_reviews(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        status: str | None = None,
    ) -> list[AccessReview]:
        """List access reviews in tenant."""
        stmt = (
            select(AccessReview)
            .options(selectinload(AccessReview.items))
            .where(
                and_(
                    AccessReview.tenant_id == tenant_id,
                    AccessReview.status == status if status else True,
                )
            )
            .order_by(AccessReview.created_at.desc())
        )
        return list((await db.execute(stmt)).scalars().all())

    @classmethod
    async def decide_access_review_item(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        review_id: UUID,
        item_id: UUID,
        payload: AccessReviewItemDecide,
        actor_id: UUID | None = None,
    ) -> AccessReviewItem:
        """Record decision (RETAIN, REVOKE, MODIFY, ESCALATE) on an access review item."""
        stmt = select(AccessReviewItem).where(
            and_(
                AccessReviewItem.id == item_id,
                AccessReviewItem.review_id == review_id,
                AccessReviewItem.tenant_id == tenant_id,
            )
        )
        item = (await db.execute(stmt)).scalar_one_or_none()
        if not item:
            raise NotFoundException("AccessReviewItem", item_id)

        dec = payload.decision.upper()
        if dec not in (
            AccessReviewDecisionType.RETAIN,
            AccessReviewDecisionType.REVOKE,
            AccessReviewDecisionType.MODIFY,
            AccessReviewDecisionType.ESCALATE,
        ):
            raise ValidationException(f"Invalid decision '{payload.decision}'.")

        now = datetime.now(UTC)
        item.decision = dec
        item.decision_notes = payload.decision_notes
        item.decided_by_user_id = actor_id
        item.decided_at = now
        item.updated_at = now

        # If decision is REVOKE, immediately revoke role assignment if exists
        if dec == AccessReviewDecisionType.REVOKE and item.role_id:
            del_stmt = select(UserRoleAssignment).where(
                and_(
                    UserRoleAssignment.tenant_id == tenant_id,
                    UserRoleAssignment.user_id == item.user_id,
                    UserRoleAssignment.role_id == item.role_id,
                )
            )
            assignment = (await db.execute(del_stmt)).scalar_one_or_none()
            if assignment:
                await db.delete(assignment)
                logger.info(
                    "Revoked role %s from user %s as part of access review item %s",
                    item.role_id, item.user_id, item.id
                )

        await db.commit()
        await db.refresh(item)
        return item

    @classmethod
    async def complete_access_review(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        review_id: UUID,
        actor_id: UUID | None = None,
    ) -> AccessReview:
        """Mark access review campaign as completed."""
        review = await cls.get_access_review(db, tenant_id, review_id)
        now = datetime.now(UTC)
        review.status = AccessReviewStatus.COMPLETED
        review.completed_at = now
        review.updated_at = now

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.ACCESS_REVIEW,
                entity_type="AccessReview",
                entity_id=review.id,
                user_id=actor_id,
                new_values_json={"status": "COMPLETED", "completed_at": now.isoformat()},
            )
        )

        await db.commit()
        await db.refresh(review)
        return review

    # =========================================================================
    # 4. SUMMARY METRICS
    # =========================================================================

    @classmethod
    async def get_governance_summary(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> GovernanceSummaryRead:
        """Aggregates high-level governance and compliance indicators."""
        active_policies = await db.scalar(
            select(func.count(GovernancePolicy.id)).where(
                and_(
                    GovernancePolicy.tenant_id == tenant_id,
                    GovernancePolicy.status == GovernancePolicyStatus.ACTIVE,
                )
            )
        ) or 0

        active_holds = await db.scalar(
            select(func.count(GovernanceHold.id)).where(
                and_(
                    GovernanceHold.tenant_id == tenant_id,
                    GovernanceHold.status == HoldStatus.ACTIVE,
                )
            )
        ) or 0

        pending_privacy = await db.scalar(
            select(func.count(PrivacyRequest.id)).where(
                and_(
                    PrivacyRequest.tenant_id == tenant_id,
                    PrivacyRequest.status.in_([
                        PrivacyRequestStatus.SUBMITTED,
                        PrivacyRequestStatus.UNDER_REVIEW,
                        PrivacyRequestStatus.IN_PROGRESS,
                    ]),
                )
            )
        ) or 0

        open_reviews = await db.scalar(
            select(func.count(AccessReview.id)).where(
                and_(
                    AccessReview.tenant_id == tenant_id,
                    AccessReview.status.in_([AccessReviewStatus.OPEN, AccessReviewStatus.IN_REVIEW]),
                )
            )
        ) or 0

        retention_rules = await db.scalar(
            select(func.count(RetentionPolicy.id)).where(
                and_(
                    RetentionPolicy.tenant_id == tenant_id,
                    RetentionPolicy.is_active == True,
                )
            )
        ) or 0

        return GovernanceSummaryRead(
            tenant_id=tenant_id,
            active_policies_count=active_policies,
            active_holds_count=active_holds,
            pending_privacy_requests_count=pending_privacy,
            open_access_reviews_count=open_reviews,
            retention_rules_count=retention_rules,
            sensitive_fields_count=len(SENSITIVE_FIELD_REGISTRY),
        )
