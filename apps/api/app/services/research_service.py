"""Enterprise Institutional Research, Innovation, Grants & IP Management Service (Step 44).

Encapsulates complete domain logic for:
- Research project registry and lifecycle state machine with validation
- Research team composition, internal/external collaborator attribution
- Funding opportunity directory and eligibility tracking
- Grant application workflow, separation of duties, and confirmed external submission
- Grant awards, financial allocation, and authoritative expenditure reconciliation
- Itemized budget planning, versioning, and formal budget revisions
- Milestone tracking, independent verification, and closure blocking
- Ethics and compliance reviews with active-project safety blocking
- Academic publications and research outputs with DOI duplicate prevention
- Intellectual property and invention disclosures with role-based confidentiality
- Specialized research facilities and infrastructure tracking
- Project risks and calculated risk level monitoring
- Research analytics aggregation and scheduled compliance sweeps
"""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import String, cast, delete, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventCategory, create_audit_entry
from app.core.exceptions import (
    ResearchAwardNotFoundException,
    ResearchBudgetExceededException,
    ResearchBudgetNotFoundException,
    ResearchConfidentialAccessDeniedException,
    ResearchEthicsApprovalRequiredException,
    ResearchEthicsNotFoundException,
    ResearchGrantApplicationNotFoundException,
    ResearchGrantSubmissionDeniedException,
    ResearchIPNotFoundException,
    ResearchMilestoneNotFoundException,
    ResearchOpportunityNotFoundException,
    ResearchOutputDuplicateException,
    ResearchOutputNotFoundException,
    ResearchProjectClosureBlockedException,
    ResearchProjectInvalidTransitionException,
    ResearchProjectNotFoundException,
    ResearchRiskNotFoundException,
    ResearchSeparationOfDutiesException,
    ResearchTeamMemberNotFoundException,
)
from app.models.people import User
from app.models.research import (
    ResearchAwardStatus,
    ResearchBudgetPlan,
    ResearchBudgetPlanStatus,
    ResearchEthicsApproval,
    ResearchEthicsApprovalStatus,
    ResearchExternalSubmissionStatus,
    ResearchFacilityReference,
    ResearchFundingOpportunity,
    ResearchGrantApplication,
    ResearchGrantAward,
    ResearchGrantInternalReviewStatus,
    ResearchInventionDisclosure,
    ResearchIPConfidentiality,
    ResearchMilestone,
    ResearchMilestoneStatus,
    ResearchOpportunityStatus,
    ResearchOutput,
    ResearchOutputStatus,
    ResearchProject,
    ResearchProjectRisk,
    ResearchProjectRiskLevel,
    ResearchProjectRiskStatus,
    ResearchProjectStatus,
    ResearchProjectStatusHistory,
    ResearchTeamMember,
    ResearchTeamRole,
)
from app.schemas.research import (
    ResearchAnalyticsSummaryResponse,
    ResearchBudgetPlanCreate,
    ResearchBudgetRevisionRequest,
    ResearchDeadlineSweepResponse,
    ResearchEthicsApprovalCreate,
    ResearchEthicsApprovalDecision,
    ResearchFacilityReferenceCreate,
    ResearchFundingOpportunityCreate,
    ResearchFundingOpportunityUpdate,
    ResearchGrantApplicationCreate,
    ResearchGrantApplicationUpdate,
    ResearchGrantAwardCreate,
    ResearchGrantAwardUpdate,
    ResearchGrantExternalSubmissionConfirm,
    ResearchGrantInternalReview,
    ResearchInventionDisclosureCreate,
    ResearchInventionDisclosureUpdate,
    ResearchMilestoneCreate,
    ResearchMilestoneUpdate,
    ResearchMilestoneVerify,
    ResearchOutputCreate,
    ResearchOutputUpdate,
    ResearchOutputVerify,
    ResearchProjectCreate,
    ResearchProjectRiskCreate,
    ResearchProjectRiskUpdate,
    ResearchProjectTransition,
    ResearchProjectUpdate,
    ResearchTeamMemberCreate,
    ResearchTeamMemberUpdate,
)


class ResearchService:
    """Production service for Enterprise Research, Innovation, Grants, and IP Management."""

    # =========================================================================
    # 1. RESEARCH PROJECT REGISTRY & LIFECYCLE
    # =========================================================================

    @classmethod
    async def create_project(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: ResearchProjectCreate,
        current_user_id: UUID,
    ) -> ResearchProject:
        """Create a new research project and assign the principal investigator."""
        # Check project code uniqueness in tenant
        existing = await db.scalar(
            select(ResearchProject).where(
                ResearchProject.tenant_id == tenant_id,
                ResearchProject.project_code == data.project_code,
            )
        )
        if existing:
            raise ResearchProjectInvalidTransitionException(
                current_status="NONE",
                requested_status="DRAFT",
                reason=f"Project code '{data.project_code}' already exists in this institution.",
            )

        cat_val = data.research_category.value if hasattr(data.research_category, "value") else str(data.research_category)
        dept_id = getattr(data, "department_id", None) or getattr(data, "lead_department_id", None)
        campus_id = getattr(data, "campus_id", None) or getattr(data, "lead_campus_id", None)
        planned_dt = getattr(data, "planned_completion_date", None) or getattr(data, "planned_end_date", None) or (date.today() + timedelta(days=365))
        budget_val = getattr(data, "proposed_budget", None)
        if budget_val is None:
            budget_val = getattr(data, "total_budget_allocated", 0.0)

        meta = dict(data.metadata_json or {})
        meta["actual_expenditure"] = 0.0

        project = ResearchProject(
            tenant_id=tenant_id,
            project_code=data.project_code,
            title=data.title,
            abstract=data.abstract or "Research Project",
            description=data.description,
            research_objectives=getattr(data, "research_objectives", []) or [],
            category=cat_val,
            research_domain=data.research_domain,
            principal_investigator_id=data.principal_investigator_id,
            lead_department_id=dept_id,
            lead_campus_id=campus_id,
            start_date=data.start_date or date.today(),
            planned_completion_date=planned_dt,
            status=ResearchProjectStatus.DRAFT.value if hasattr(ResearchProjectStatus.DRAFT, "value") else str(ResearchProjectStatus.DRAFT),
            total_budget_allocated=Decimal(str(budget_val or 0.0)),
            currency=data.currency or "USD",
            requires_ethics_approval=bool(data.requires_ethics_approval),
            ethics_approval_status=getattr(data, "ethics_approval_status", "NOT_REQUIRED") or "NOT_REQUIRED",
            risks_summary=data.risks_summary,
            metadata_json=meta,
        )
        db.add(project)
        await db.flush()

        # Add initial status history
        history = ResearchProjectStatusHistory(
            tenant_id=tenant_id,
            project_id=project.id,
            from_status="NONE",
            to_status=ResearchProjectStatus.DRAFT.value if hasattr(ResearchProjectStatus.DRAFT, "value") else str(ResearchProjectStatus.DRAFT),
            changed_by_user_id=current_user_id,
            reason="Initial project registration",
            decision_notes=None,
            transition_date=datetime.now(UTC),
        )
        db.add(history)

        # Automatically assign PI to team
        pi_member = ResearchTeamMember(
            tenant_id=tenant_id,
            project_id=project.id,
            user_id=data.principal_investigator_id,
            external_collaborator_name=None,
            external_institution=None,
            role=ResearchTeamRole.PRINCIPAL_INVESTIGATOR.value if hasattr(ResearchTeamRole.PRINCIPAL_INVESTIGATOR, "value") else str(ResearchTeamRole.PRINCIPAL_INVESTIGATOR),
            contribution_description="Principal Investigator and Project Lead",
            access_scope="PROJECT_LEAD",
            is_active=True,
            start_date=data.start_date or date.today(),
            end_date=None,
        )
        db.add(pi_member)

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.RESEARCH_PROJECT_CREATED,
            entity_type="research_project",
            entity_id=project.id,
            user_id=current_user_id,
            new_values_json={"project_code": project.project_code, "title": project.title},
        )
        await db.commit()
        await db.refresh(project)
        return project

    @classmethod
    async def list_projects(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        status: ResearchProjectStatus | None = None,
        category: str | None = None,
        domain: str | None = None,
        department_id: UUID | None = None,
        campus_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ResearchProject], int]:
        """List tenant research projects with filtering and total count."""
        stmt = select(ResearchProject).where(ResearchProject.tenant_id == tenant_id)
        if status:
            s_val = status.value if hasattr(status, "value") else str(status)
            stmt = stmt.where(ResearchProject.status == s_val)
        if category:
            c_val = category.value if hasattr(category, "value") else str(category)
            stmt = stmt.where(ResearchProject.category == c_val)
        if domain:
            stmt = stmt.where(ResearchProject.research_domain.ilike(f"%{domain}%"))
        if department_id:
            stmt = stmt.where(ResearchProject.lead_department_id == department_id)
        if campus_id:
            stmt = stmt.where(ResearchProject.lead_campus_id == campus_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await db.scalar(count_stmt) or 0

        projects = (
            await db.scalars(
                stmt.order_by(desc(ResearchProject.created_at)).limit(limit).offset(offset)
            )
        ).all()
        return list(projects), total

    @classmethod
    async def get_project(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        project_id: UUID,
    ) -> ResearchProject:
        """Fetch project by ID with tenant isolation."""
        project = await db.scalar(
            select(ResearchProject).where(
                ResearchProject.tenant_id == tenant_id,
                ResearchProject.id == project_id,
            )
        )
        if not project:
            raise ResearchProjectNotFoundException(project_id)
        return project

    @classmethod
    async def update_project(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        project_id: UUID,
        data: ResearchProjectUpdate,
        current_user_id: UUID,
    ) -> ResearchProject:
        """Update research project fields."""
        project = await cls.get_project(db, tenant_id, project_id)
        old_data = {"title": project.title, "domain": project.research_domain}

        update_dict = data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(project, field, value)

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.RESEARCH_PROJECT_UPDATED,
            entity_type="research_project",
            entity_id=project.id,
            user_id=current_user_id,
            old_values_json=old_data,
            new_values_json=update_dict,
        )
        await db.commit()
        await db.refresh(project)
        return project

    @classmethod
    async def transition_project_status(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        project_id: UUID,
        data: ResearchProjectTransition,
        current_user_id: UUID,
    ) -> ResearchProject:
        """Perform validated lifecycle status transition."""
        project = await cls.get_project(db, tenant_id, project_id)
        current_status = project.status
        target_status = data.to_status

        curr_str = current_status.value if hasattr(current_status, "value") else str(current_status)
        target_str = target_status.value if hasattr(target_status, "value") else str(target_status)

        # Valid transitions graph
        valid_transitions: dict[str, set[str]] = {
            "DRAFT": {"SUBMITTED", "CLOSED"},
            "SUBMITTED": {"UNDER_REVIEW", "DRAFT"},
            "UNDER_REVIEW": {"APPROVED", "REJECTED", "DRAFT"},
            "APPROVED": {"ACTIVE", "DRAFT"},
            "ACTIVE": {"ON_HOLD", "AT_RISK", "COMPLETED"},
            "ON_HOLD": {"ACTIVE", "CLOSED"},
            "AT_RISK": {"ACTIVE", "ON_HOLD", "CLOSED"},
            "COMPLETED": {"CLOSED"},
            "CLOSED": {"ACTIVE"},
            "REJECTED": {"DRAFT"},
        }

        allowed = valid_transitions.get(curr_str, set())
        if target_str not in allowed:
            raise ResearchProjectInvalidTransitionException(
                current_status=curr_str,
                requested_status=target_str,
                reason=f"Transition from '{curr_str}' to '{target_str}' is not permitted.",
            )

        # Precondition check 1: Active transition requires valid ethics approval if configured
        if target_str == "ACTIVE" and project.requires_ethics_approval:
            active_ethics = await db.scalar(
                select(ResearchEthicsApproval).where(
                    ResearchEthicsApproval.tenant_id == tenant_id,
                    ResearchEthicsApproval.project_id == project.id,
                    ResearchEthicsApproval.status.in_([
                        ResearchEthicsApprovalStatus.APPROVED.value,
                        "APPROVED",
                        ResearchEthicsApprovalStatus.CONDITIONAL_APPROVAL.value,
                        "CONDITIONAL_APPROVAL",
                    ]),
                    or_(
                        ResearchEthicsApproval.expiry_date.is_(None),
                        ResearchEthicsApproval.expiry_date >= date.today(),
                    ),
                )
            )
            if not active_ethics:
                raise ResearchEthicsApprovalRequiredException(
                    project.project_code,
                    "Cannot activate project without an approved, non-expired ethics approval record.",
                )

        # Precondition check 2: Completed or Closed transition blocks if mandatory milestones are unaccepted
        if target_str in ("COMPLETED", "CLOSED"):
            unmet_milestone = await db.scalar(
                select(ResearchMilestone).where(
                    ResearchMilestone.tenant_id == tenant_id,
                    ResearchMilestone.project_id == project.id,
                    ResearchMilestone.is_mandatory_for_closure.is_(True),
                    ResearchMilestone.status != ResearchMilestoneStatus.ACCEPTED.value,
                    ResearchMilestone.status != "ACCEPTED",
                )
            )
            if unmet_milestone:
                raise ResearchProjectClosureBlockedException(
                    project.project_code,
                    f"Mandatory milestone '{unmet_milestone.title}' is in status '{unmet_milestone.status}' (must be ACCEPTED).",
                )

        # Apply extension date if requested
        if data.extension_date:
            project.planned_end_date = data.extension_date

        if target_str in ("COMPLETED", "CLOSED"):
            project.actual_end_date = date.today()

        project.status = target_str

        history = ResearchProjectStatusHistory(
            tenant_id=tenant_id,
            project_id=project.id,
            from_status=curr_str,
            to_status=target_str,
            changed_by_user_id=current_user_id,
            reason=data.reason,
            decision_notes=None,
            transition_date=datetime.now(UTC),
        )
        db.add(history)

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.RESEARCH_PROJECT_TRANSITION,
            entity_type="research_project",
            entity_id=project.id,
            user_id=current_user_id,
            old_values_json={"status": curr_str},
            new_values_json={"status": target_str, "reason": data.reason},
        )
        await db.commit()
        await db.refresh(project)
        return project

    @classmethod
    async def list_project_status_history(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        project_id: UUID,
    ) -> list[ResearchProjectStatusHistory]:
        """Retrieve full audited lifecycle transition history for a project."""
        await cls.get_project(db, tenant_id, project_id)
        history = (
            await db.scalars(
                select(ResearchProjectStatusHistory)
                .where(
                    ResearchProjectStatusHistory.tenant_id == tenant_id,
                    ResearchProjectStatusHistory.project_id == project_id,
                )
                .order_by(desc(ResearchProjectStatusHistory.transition_date))
            )
        ).all()
        return list(history)

    # =========================================================================
    # 2. RESEARCH TEAM & COLLABORATORS
    # =========================================================================

    @classmethod
    async def add_team_member(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        project_id: UUID,
        data: ResearchTeamMemberCreate,
        current_user_id: UUID,
    ) -> ResearchTeamMember:
        """Add an internal or external researcher to a project team."""
        project = await cls.get_project(db, tenant_id, project_id)

        # If internal, verify user belongs to tenant
        if not data.is_external and data.user_id:
            user = await db.scalar(
                select(User).where(User.tenant_id == tenant_id, User.id == data.user_id)
            )
            if not user:
                raise ResearchTeamMemberNotFoundException(data.user_id)

        ext_name = getattr(data, "external_collaborator_name", None) or getattr(data, "external_name", None)
        role_val = data.role.value if hasattr(data.role, "value") else str(data.role)
        is_ext = getattr(data, "is_external", False) or bool(ext_name)

        member = ResearchTeamMember(
            tenant_id=tenant_id,
            project_id=project.id,
            user_id=data.user_id if not is_ext else None,
            external_collaborator_name=ext_name,
            external_institution=data.external_institution,
            role=role_val,
            contribution_description=data.contribution_description,
            access_scope=getattr(data, "access_scope", "FULL_READ_WRITE") or "FULL_READ_WRITE",
            is_active=True,
            start_date=data.start_date or date.today(),
            end_date=data.end_date,
        )
        db.add(member)
        await db.flush()
        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.RESEARCH_TEAM_MEMBER_ADDED,
            entity_type="research_team_member",
            entity_id=member.id,
            user_id=current_user_id,
            new_values_json={"role": member.role, "is_external": member.is_external},
        )
        await db.commit()
        await db.refresh(member)
        return member

    @classmethod
    async def list_team_members(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        project_id: UUID,
    ) -> list[ResearchTeamMember]:
        """List active and historical team members for a project."""
        await cls.get_project(db, tenant_id, project_id)
        members = (
            await db.scalars(
                select(ResearchTeamMember)
                .where(
                    ResearchTeamMember.tenant_id == tenant_id,
                    ResearchTeamMember.project_id == project_id,
                )
                .order_by(ResearchTeamMember.is_active.desc(), ResearchTeamMember.created_at)
            )
        ).all()
        return list(members)

    @classmethod
    async def update_team_member(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        member_id: UUID,
        data: ResearchTeamMemberUpdate,
        current_user_id: UUID,
    ) -> ResearchTeamMember:
        """Update role, contribution or scope of a team member."""
        member = await db.scalar(
            select(ResearchTeamMember).where(
                ResearchTeamMember.tenant_id == tenant_id,
                ResearchTeamMember.id == member_id,
            )
        )
        if not member:
            raise ResearchTeamMemberNotFoundException(member_id)

        update_dict = data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(member, field, value)

        await db.commit()
        await db.refresh(member)
        return member

    @classmethod
    async def remove_team_member(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        member_id: UUID,
        current_user_id: UUID,
    ) -> ResearchTeamMember:
        """Soft-deactivate a team member to preserve historical attribution."""
        member = await db.scalar(
            select(ResearchTeamMember).where(
                ResearchTeamMember.tenant_id == tenant_id,
                ResearchTeamMember.id == member_id,
            )
        )
        if not member:
            raise ResearchTeamMemberNotFoundException(member_id)

        member.is_active = False
        member.end_date = date.today()

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.RESEARCH_TEAM_MEMBER_REMOVED,
            entity_type="research_team_member",
            entity_id=member.id,
            user_id=current_user_id,
            old_values_json={"is_active": True},
            new_values_json={"is_active": False, "end_date": str(member.end_date)},
        )
        await db.commit()
        await db.refresh(member)
        return member

    # =========================================================================
    # 3. RESEARCH FUNDING OPPORTUNITIES REGISTRY
    # =========================================================================

    @classmethod
    async def create_funding_opportunity(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: ResearchFundingOpportunityCreate,
        current_user_id: UUID,
    ) -> ResearchFundingOpportunity:
        """Register a verified funding opportunity."""
        code_val = getattr(data, "code", None) or getattr(data, "opportunity_code", None)
        existing = await db.scalar(
            select(ResearchFundingOpportunity).where(
                ResearchFundingOpportunity.tenant_id == tenant_id,
                ResearchFundingOpportunity.code == code_val,
            )
        )
        if existing:
            raise ResearchProjectInvalidTransitionException(
                "NONE", "ACTIVE", f"Funding opportunity code '{code_val}' already exists."
            )

        agency_name = getattr(data, "funding_agency_name", None) or getattr(data, "funding_organization", "Funding Agency")
        min_amt = getattr(data, "min_funding_amount", None) or getattr(data, "min_amount", None)
        max_amt = getattr(data, "max_funding_amount", None) or getattr(data, "max_amount", None)
        app_url = getattr(data, "application_procedure_url", None) or getattr(data, "opportunity_url", None)
        owner_id = getattr(data, "internal_opportunity_owner_id", None) or getattr(data, "internal_contact_user_id", None)

        opp = ResearchFundingOpportunity(
            tenant_id=tenant_id,
            code=code_val,
            title=data.title,
            description=data.description or data.title or "Funding Opportunity",
            funding_agency_name=agency_name,
            category=data.category if isinstance(data.category, str) else data.category.value,
            research_domains=data.research_domains or [],
            eligibility_criteria=data.eligibility_criteria or "Standard institutional eligibility",
            opening_date=getattr(data, "opening_date", None) or date.today(),
            closing_date=data.closing_date,
            min_funding_amount=Decimal(str(min_amt)) if min_amt is not None else None,
            max_funding_amount=Decimal(str(max_amt)) if max_amt is not None else None,
            currency=data.currency or "USD",
            application_procedure_url=app_url,
            internal_opportunity_owner_id=owner_id,
            visibility_scope=getattr(data, "visibility_scope", "INSTITUTION_WIDE") or "INSTITUTION_WIDE",
            campus_id=data.campus_id,
            department_id=data.department_id,
            status=ResearchOpportunityStatus.OPEN.value if hasattr(ResearchOpportunityStatus.OPEN, "value") else str(ResearchOpportunityStatus.OPEN),
            metadata_json=data.metadata_json or {},
        )
        db.add(opp)
        await db.flush()
        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.RESEARCH_OPPORTUNITY_CREATED,
            entity_type="research_funding_opportunity",
            entity_id=opp.id,
            user_id=current_user_id,
            new_values_json={"code": opp.code, "title": opp.title},
        )
        await db.commit()
        await db.refresh(opp)
        return opp

    @classmethod
    async def list_funding_opportunities(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        status: ResearchOpportunityStatus | None = None,
        category: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ResearchFundingOpportunity], int]:
        """List opportunities with total count."""
        stmt = select(ResearchFundingOpportunity).where(ResearchFundingOpportunity.tenant_id == tenant_id)
        if status:
            s_val = status.value if hasattr(status, "value") else str(status)
            stmt = stmt.where(ResearchFundingOpportunity.status == s_val)
        if category:
            c_val = category.value if hasattr(category, "value") else str(category)
            stmt = stmt.where(ResearchFundingOpportunity.category == c_val)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await db.scalar(count_stmt) or 0

        opps = (
            await db.scalars(
                stmt.order_by(desc(ResearchFundingOpportunity.created_at)).limit(limit).offset(offset)
            )
        ).all()
        return list(opps), total

    @classmethod
    async def get_funding_opportunity(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        opportunity_id: UUID,
    ) -> ResearchFundingOpportunity:
        """Fetch funding opportunity by ID."""
        opp = await db.scalar(
            select(ResearchFundingOpportunity).where(
                ResearchFundingOpportunity.tenant_id == tenant_id,
                ResearchFundingOpportunity.id == opportunity_id,
            )
        )
        if not opp:
            raise ResearchOpportunityNotFoundException(opportunity_id)
        return opp

    @classmethod
    async def update_funding_opportunity(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        opportunity_id: UUID,
        data: ResearchFundingOpportunityUpdate,
        current_user_id: UUID,
    ) -> ResearchFundingOpportunity:
        """Update funding opportunity details."""
        opp = await cls.get_funding_opportunity(db, tenant_id, opportunity_id)
        update_dict = data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(opp, field, value)

        await db.commit()
        await db.refresh(opp)
        return opp

    # =========================================================================
    # 4. GRANT APPLICATIONS & INTERNAL REVIEW
    # =========================================================================

    @classmethod
    async def create_grant_application(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: ResearchGrantApplicationCreate,
        current_user_id: UUID,
    ) -> ResearchGrantApplication:
        """Create a new grant application draft."""
        existing = await db.scalar(
            select(ResearchGrantApplication).where(
                ResearchGrantApplication.tenant_id == tenant_id,
                ResearchGrantApplication.application_code == data.application_code,
            )
        )
        if existing:
            raise ResearchProjectInvalidTransitionException(
                "NONE", "DRAFT", f"Application code '{data.application_code}' already exists."
            )

        opp_id = getattr(data, "funding_opportunity_id", None) or getattr(data, "opportunity_id", None)
        proposal_summary = getattr(data, "research_proposal_summary", None) or getattr(data, "proposal_abstract", "Proposal summary")
        objs = getattr(data, "objectives_json", None) or getattr(data, "research_objectives", []) or []
        methodology = getattr(data, "methodology_summary", None) or getattr(data, "methodology", None)

        app = ResearchGrantApplication(
            tenant_id=tenant_id,
            application_code=data.application_code,
            funding_opportunity_id=opp_id,
            project_id=data.project_id,
            title=data.title,
            principal_investigator_id=data.principal_investigator_id,
            research_proposal_summary=proposal_summary,
            objectives_json=objs,
            methodology_summary=methodology,
            work_packages_json=data.work_packages_json or [],
            proposed_budget=Decimal(str(data.proposed_budget or 0.0)),
            currency=data.currency or "USD",
            internal_review_status=ResearchGrantInternalReviewStatus.DRAFT.value if hasattr(ResearchGrantInternalReviewStatus.DRAFT, "value") else str(ResearchGrantInternalReviewStatus.DRAFT),
            external_submission_status=ResearchExternalSubmissionStatus.NOT_SUBMITTED.value if hasattr(ResearchExternalSubmissionStatus.NOT_SUBMITTED, "value") else str(ResearchExternalSubmissionStatus.NOT_SUBMITTED),
            external_reference_number=None,
            external_submitted_at=None,
            submitted_by_user_id=current_user_id,
            internal_approved_by_id=None,
            internal_approved_at=None,
            rejection_reason=None,
            submission_readiness_checklist_json={},
            metadata_json=data.metadata_json or {},
        )
        db.add(app)
        await db.flush()
        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.RESEARCH_GRANT_APPLICATION_CREATED,
            entity_type="research_grant_application",
            entity_id=app.id,
            user_id=current_user_id,
            new_values_json={"code": app.application_code, "title": app.title},
        )
        await db.commit()
        await db.refresh(app)
        return app

    @classmethod
    async def list_grant_applications(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        project_id: UUID | None = None,
        internal_status: ResearchGrantInternalReviewStatus | None = None,
        external_status: ResearchExternalSubmissionStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ResearchGrantApplication], int]:
        """List grant applications with filtering."""
        stmt = select(ResearchGrantApplication).where(ResearchGrantApplication.tenant_id == tenant_id)
        if project_id:
            stmt = stmt.where(ResearchGrantApplication.project_id == project_id)
        if internal_status:
            i_val = internal_status.value if hasattr(internal_status, "value") else str(internal_status)
            stmt = stmt.where(ResearchGrantApplication.internal_review_status == i_val)
        if external_status:
            e_val = external_status.value if hasattr(external_status, "value") else str(external_status)
            stmt = stmt.where(ResearchGrantApplication.external_submission_status == e_val)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await db.scalar(count_stmt) or 0

        apps = (
            await db.scalars(
                stmt.order_by(desc(ResearchGrantApplication.created_at)).limit(limit).offset(offset)
            )
        ).all()
        return list(apps), total

    @classmethod
    async def get_grant_application(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        application_id: UUID,
    ) -> ResearchGrantApplication:
        """Fetch grant application by ID."""
        app = await db.scalar(
            select(ResearchGrantApplication).where(
                ResearchGrantApplication.tenant_id == tenant_id,
                ResearchGrantApplication.id == application_id,
            )
        )
        if not app:
            raise ResearchGrantApplicationNotFoundException(application_id)
        return app

    @classmethod
    async def update_grant_application(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        application_id: UUID,
        data: ResearchGrantApplicationUpdate,
        current_user_id: UUID,
    ) -> ResearchGrantApplication:
        """Update grant proposal content."""
        app = await cls.get_grant_application(db, tenant_id, application_id)
        update_dict = data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(app, field, value)

        await db.commit()
        await db.refresh(app)
        return app

    @classmethod
    async def review_grant_application(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        application_id: UUID,
        data: ResearchGrantInternalReview,
        current_user_id: UUID,
    ) -> ResearchGrantApplication:
        """Record formal internal institutional review decision with separation of duties."""
        app = await cls.get_grant_application(db, tenant_id, application_id)

        # Separation of duties: PI cannot review their own application
        if app.principal_investigator_id == current_user_id:
            raise ResearchSeparationOfDutiesException("review or approve their own grant application")

        dec_val = data.decision.value if hasattr(data.decision, "value") else str(data.decision)
        app.internal_review_status = dec_val
        app.internal_approved_by_id = current_user_id
        app.internal_approved_at = datetime.now(UTC)
        app.rejection_reason = data.comments

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.RESEARCH_GRANT_APPLICATION_REVIEWED,
            entity_type="research_grant_application",
            entity_id=app.id,
            user_id=current_user_id,
            new_values_json={"decision": dec_val, "comments": data.comments},
        )
        await db.commit()
        await db.refresh(app)
        return app

    @classmethod
    async def confirm_external_submission(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        application_id: UUID,
        data: ResearchGrantExternalSubmissionConfirm,
        current_user_id: UUID,
    ) -> ResearchGrantApplication:
        """Record verified external grant submission."""
        app = await cls.get_grant_application(db, tenant_id, application_id)

        # Precondition: Must be institutionally approved internally before external submission
        if (
            app.internal_review_status != ResearchGrantInternalReviewStatus.INSTITUTIONALLY_APPROVED.value
            and app.internal_review_status != "INSTITUTIONALLY_APPROVED"
        ):
            raise ResearchGrantSubmissionDeniedException(
                f"Grant application '{app.application_code}' is in status '{app.internal_review_status}'. "
                "Only applications marked INSTITUTIONALLY_APPROVED may be confirmed for external submission."
            )

        ref_val = getattr(data, "external_submission_reference", None) or getattr(data, "external_reference_number", "EXT-REF")
        app.external_submission_status = ResearchExternalSubmissionStatus.SUBMITTED_EXTERNAL.value if hasattr(ResearchExternalSubmissionStatus.SUBMITTED_EXTERNAL, "value") else str(ResearchExternalSubmissionStatus.SUBMITTED_EXTERNAL)
        app.external_reference_number = ref_val
        app.external_submitted_at = datetime.now(UTC)
        app.submitted_by_user_id = current_user_id

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.RESEARCH_GRANT_APPLICATION_CONFIRMED,
            entity_type="research_grant_application",
            entity_id=app.id,
            user_id=current_user_id,
            new_values_json={
                "external_ref": data.external_submission_reference,
                "submission_date": str(data.submission_date),
            },
        )
        await db.commit()
        await db.refresh(app)
        return app

    # =========================================================================
    # 5. GRANT AWARDS & FINANCIAL RECONCILIATION
    # =========================================================================

    @classmethod
    async def create_grant_award(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: ResearchGrantAwardCreate,
        current_user_id: UUID,
    ) -> ResearchGrantAward:
        """Create a research grant award record and update linked project budget."""
        project = await cls.get_project(db, tenant_id, data.project_id)

        award_code = getattr(data, "award_number", None) or getattr(data, "award_code", None)
        existing = await db.scalar(
            select(ResearchGrantAward).where(
                ResearchGrantAward.tenant_id == tenant_id,
                ResearchGrantAward.award_number == award_code,
            )
        )
        if existing:
            raise ResearchProjectInvalidTransitionException(
                "NONE", "AWARDED", f"Award code '{award_code}' already registered."
            )

        app_id = getattr(data, "grant_application_id", None) or getattr(data, "application_id", None)
        start_dt = getattr(data, "start_date", None) or getattr(data, "period_start_date", None) or date.today()
        end_dt = getattr(data, "end_date", None) or getattr(data, "period_end_date", None) or (date.today() + timedelta(days=365))
        fin_mgr = getattr(data, "financial_owner_id", None) or getattr(data, "financial_manager_id", None) or current_user_id
        conditions = getattr(data, "spending_conditions", None) or getattr(data, "conditions_and_restrictions", None)
        award_amt = Decimal(str(data.award_amount))

        award = ResearchGrantAward(
            tenant_id=tenant_id,
            award_number=award_code,
            grant_application_id=app_id,
            project_id=project.id,
            funding_organization=data.funding_organization,
            award_amount=award_amt,
            currency=data.currency or "INR",
            award_date=data.award_date or date.today(),
            start_date=start_dt,
            end_date=end_dt,
            approved_budget_json=getattr(data, "approved_budget_json", {}) or {},
            disbursement_schedule_json=getattr(data, "disbursement_schedule_json", []) or [],
            spending_conditions=conditions,
            reporting_deadlines_json=getattr(data, "reporting_deadlines_json", []) or [],
            financial_owner_id=fin_mgr,
            received_amount=award_amt,
            allocated_amount=Decimal("0.00"),
            committed_expenditure=Decimal("0.00"),
            actual_expenditure=Decimal("0.00"),
            remaining_budget=award_amt,
            status=ResearchAwardStatus.ACTIVE.value if hasattr(ResearchAwardStatus.ACTIVE, "value") else str(ResearchAwardStatus.ACTIVE),
            metadata_json=data.metadata_json or {},
        )
        db.add(award)
        await db.flush()

        # Update project approved budget
        project.total_budget_allocated += award_amt

        # Update application external status if linked
        if app_id:
            app = await db.scalar(
                select(ResearchGrantApplication).where(
                    ResearchGrantApplication.tenant_id == tenant_id,
                    ResearchGrantApplication.id == app_id,
                )
            )
            if app:
                app.external_submission_status = ResearchExternalSubmissionStatus.AWARDED.value if hasattr(ResearchExternalSubmissionStatus.AWARDED, "value") else str(ResearchExternalSubmissionStatus.AWARDED)

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.RESEARCH_AWARD_CREATED,
            entity_type="research_grant_award",
            entity_id=award.id,
            user_id=current_user_id,
            new_values_json={"code": award.award_code, "amount": float(award.award_amount)},
        )
        await db.commit()
        await db.refresh(award)
        return award

    @classmethod
    async def list_grant_awards(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        project_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ResearchGrantAward], int]:
        """List grant awards with filtering."""
        stmt = select(ResearchGrantAward).where(ResearchGrantAward.tenant_id == tenant_id)
        if project_id:
            stmt = stmt.where(ResearchGrantAward.project_id == project_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await db.scalar(count_stmt) or 0

        awards = (
            await db.scalars(
                stmt.order_by(desc(ResearchGrantAward.award_date)).limit(limit).offset(offset)
            )
        ).all()
        return list(awards), total

    @classmethod
    async def get_grant_award(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        award_id: UUID,
    ) -> ResearchGrantAward:
        """Fetch grant award by ID."""
        award = await db.scalar(
            select(ResearchGrantAward).where(
                ResearchGrantAward.tenant_id == tenant_id,
                ResearchGrantAward.id == award_id,
            )
        )
        if not award:
            raise ResearchAwardNotFoundException(award_id)
        return award

    @classmethod
    async def reconcile_award_expenditure(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        award_id: UUID,
    ) -> ResearchGrantAward:
        """Reconcile spent and allocated totals against budget items and project."""
        award = await cls.get_grant_award(db, tenant_id, award_id)

        # Sum allocated and spent from budget plans
        budget_items = (
            await db.scalars(
                select(ResearchBudgetPlan).where(
                    ResearchBudgetPlan.tenant_id == tenant_id,
                    ResearchBudgetPlan.award_id == award.id,
                )
            )
        ).all()

        total_allocated = sum(Decimal(str(item.total_budget)) for item in budget_items)
        total_spent = sum(Decimal(str(item.actual_expenditure)) for item in budget_items)

        award.allocated_amount = total_allocated
        award.actual_expenditure = total_spent
        award.remaining_budget = max(Decimal("0.00"), award.award_amount - total_spent)

        # Sync project actual expenditure
        project = await cls.get_project(db, tenant_id, award.project_id)
        all_project_plans = (
            await db.scalars(
                select(ResearchBudgetPlan).where(
                    ResearchBudgetPlan.tenant_id == tenant_id,
                    ResearchBudgetPlan.project_id == project.id,
                )
            )
        ).all()
        project.actual_expenditure = sum(float(p.actual_expenditure) for p in all_project_plans)

        await db.commit()
        await db.refresh(award)
        return award

    # =========================================================================
    # 6. RESEARCH BUDGET PLANNING & REVISIONS
    # =========================================================================

    @classmethod
    async def create_budget_plan(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: ResearchBudgetPlanCreate,
        current_user_id: UUID,
    ) -> ResearchBudgetPlan:
        """Create an itemized project budget allocation."""
        await cls.get_project(db, tenant_id, data.project_id)

        alloc_amt = getattr(data, "total_budget", None)
        if alloc_amt is None or alloc_amt == 0.0:
            alloc_amt = getattr(data, "allocated_amount", 0.0)

        if data.award_id:
            award = await cls.get_grant_award(db, tenant_id, data.award_id)
            if alloc_amt > award.remaining_balance:
                raise ResearchBudgetExceededException(
                    category=data.category,
                    requested=alloc_amt,
                    allocated=award.remaining_balance,
                )

        meta = dict(data.metadata_json or {})
        meta["category"] = getattr(data, "category", "PERSONNEL")
        meta["item_description"] = getattr(data, "item_description", "Budget Line Item")
        meta["actual_expenditure"] = 0.0

        plan = ResearchBudgetPlan(
            tenant_id=tenant_id,
            project_id=data.project_id,
            award_id=data.award_id,
            version_number=1,
            status=ResearchBudgetPlanStatus.APPROVED.value if alloc_amt > 0 else ResearchBudgetPlanStatus.PROPOSED.value,
            personnel_costs=Decimal(str(getattr(data, "personnel_costs", 0.0) or 0.0)),
            equipment_costs=Decimal(str(getattr(data, "equipment_costs", 0.0) or 0.0)),
            consumables_materials_costs=Decimal(str(getattr(data, "consumables_materials_costs", 0.0) or 0.0)),
            travel_fieldwork_costs=Decimal(str(getattr(data, "travel_fieldwork_costs", 0.0) or 0.0)),
            computing_software_costs=Decimal(str(getattr(data, "computing_software_costs", 0.0) or 0.0)),
            publication_dissemination_costs=Decimal(str(getattr(data, "publication_dissemination_costs", 0.0) or 0.0)),
            external_services_costs=Decimal(str(getattr(data, "external_services_costs", 0.0) or 0.0)),
            institutional_overheads=Decimal(str(getattr(data, "institutional_overheads", 0.0) or 0.0)),
            contingency_costs=Decimal(str(getattr(data, "contingency_costs", 0.0) or 0.0)),
            total_budget=Decimal(str(alloc_amt or 0.0)),
            currency=data.currency or "INR",
            approved_by_id=current_user_id,
            approved_at=datetime.now(UTC),
            approval_notes=getattr(data, "approval_notes", None) or getattr(data, "justification", None),
            metadata_json=meta,
        )
        db.add(plan)
        await db.flush()

        if data.award_id:
            await cls.reconcile_award_expenditure(db, tenant_id, data.award_id)

        await db.commit()
        await db.refresh(plan)
        return plan

    @classmethod
    async def list_budget_plans(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        project_id: UUID,
        award_id: UUID | None = None,
    ) -> list[ResearchBudgetPlan]:
        """List all itemized budget plans for a project."""
        await cls.get_project(db, tenant_id, project_id)
        stmt = select(ResearchBudgetPlan).where(
            ResearchBudgetPlan.tenant_id == tenant_id,
            ResearchBudgetPlan.project_id == project_id,
        )
        if award_id:
            stmt = stmt.where(ResearchBudgetPlan.award_id == award_id)

        plans = (await db.scalars(stmt.order_by(ResearchBudgetPlan.created_at))).all()
        return list(plans)

    @classmethod
    async def revise_budget_plan(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        plan_id: UUID,
        data: ResearchBudgetRevisionRequest,
        current_user_id: UUID,
    ) -> ResearchBudgetPlan:
        """Conduct an audited budget revision with reallocation checks."""
        plan = await db.scalar(
            select(ResearchBudgetPlan).where(
                ResearchBudgetPlan.tenant_id == tenant_id,
                ResearchBudgetPlan.id == plan_id,
            )
        )
        if not plan:
            raise ResearchBudgetNotFoundException(plan_id)

        old_allocated = plan.allocated_amount

        # Check award constraint if award attached
        if plan.award_id:
            award = await cls.get_grant_award(db, tenant_id, plan.award_id)
            sibling_plans = (
                await db.scalars(
                    select(ResearchBudgetPlan).where(
                        ResearchBudgetPlan.tenant_id == tenant_id,
                        ResearchBudgetPlan.award_id == plan.award_id,
                        ResearchBudgetPlan.id != plan.id,
                    )
                )
            ).all()
            other_allocated = sum(float(p.allocated_amount) for p in sibling_plans)
            total_proposed = other_allocated + data.revised_allocated_amount
            award_total = float(award.award_amount)
            delta = data.revised_allocated_amount - old_allocated

            if total_proposed > award_total or (delta > 0 and delta > award.remaining_balance):
                raise ResearchBudgetExceededException(
                    category=plan.category,
                    requested=data.revised_allocated_amount,
                    allocated=max(0.0, award_total - other_allocated),
                )

        plan.total_budget = Decimal(str(data.revised_allocated_amount))
        plan.version_number += 1
        plan.approval_notes = data.revision_reason
        plan.approved_by_id = current_user_id
        plan.approved_at = datetime.now(UTC)

        if plan.award_id:
            await cls.reconcile_award_expenditure(db, tenant_id, plan.award_id)

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.RESEARCH_BUDGET_REVISED,
            entity_type="research_budget_plan",
            entity_id=plan.id,
            user_id=current_user_id,
            old_values_json={"allocated": old_allocated},
            new_values_json={
                "allocated": data.revised_allocated_amount,
                "reason": data.revision_reason,
            },
        )
        await db.commit()
        await db.refresh(plan)
        return plan

    # =========================================================================
    # 7. RESEARCH MILESTONES & DELIVERABLES
    # =========================================================================

    @classmethod
    async def create_milestone(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: ResearchMilestoneCreate,
        current_user_id: UUID,
    ) -> ResearchMilestone:
        """Create a trackable research milestone."""
        await cls.get_project(db, tenant_id, data.project_id)

        code = getattr(data, "milestone_code", None) or f"MS-{uuid4().hex[:6].upper()}"
        start_dt = getattr(data, "planned_start_date", None) or date.today()
        comp_dt = getattr(data, "planned_completion_date", None) or getattr(data, "planned_date", None) or date.today()
        owner_id = getattr(data, "responsible_owner_id", None) or getattr(data, "responsible_user_id", None) or current_user_id

        milestone = ResearchMilestone(
            tenant_id=tenant_id,
            project_id=data.project_id,
            milestone_code=code,
            title=data.title,
            description=data.description or "Milestone deliverable",
            sequence_number=1,
            planned_start_date=start_dt,
            planned_completion_date=comp_dt,
            actual_completion_date=None,
            responsible_owner_id=owner_id,
            dependencies_json=getattr(data, "dependencies_json", []) or [],
            acceptance_criteria=data.acceptance_criteria or "Verification required",
            completion_percentage=0.0,
            status=ResearchMilestoneStatus.PLANNED.value if hasattr(ResearchMilestoneStatus.PLANNED, "value") else str(ResearchMilestoneStatus.PLANNED),
            is_mandatory_for_closure=bool(data.is_mandatory_for_closure),
            deliverable_reference=data.deliverable_reference,
            evidence_document_id=None,
            verified_by_user_id=None,
            verified_at=None,
            verification_notes=None,
        )
        db.add(milestone)
        await db.commit()
        await db.refresh(milestone)
        return milestone

    @classmethod
    async def list_milestones(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        project_id: UUID,
    ) -> list[ResearchMilestone]:
        """List milestones for a project."""
        await cls.get_project(db, tenant_id, project_id)
        milestones = (
            await db.scalars(
                select(ResearchMilestone)
                .where(
                    ResearchMilestone.tenant_id == tenant_id,
                    ResearchMilestone.project_id == project_id,
                )
                .order_by(ResearchMilestone.planned_completion_date)
            )
        ).all()
        return list(milestones)

    @classmethod
    async def update_milestone(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        milestone_id: UUID,
        data: ResearchMilestoneUpdate,
        current_user_id: UUID,
    ) -> ResearchMilestone:
        """Update progress on milestone."""
        milestone = await db.scalar(
            select(ResearchMilestone).where(
                ResearchMilestone.tenant_id == tenant_id,
                ResearchMilestone.id == milestone_id,
            )
        )
        if not milestone:
            raise ResearchMilestoneNotFoundException(milestone_id)

        update_dict = data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            if field == "planned_date":
                milestone.planned_completion_date = value
            elif field == "actual_date":
                milestone.actual_completion_date = value
            elif field == "responsible_user_id":
                milestone.responsible_owner_id = value
            elif hasattr(milestone, field):
                setattr(milestone, field, value)

        if milestone.completion_percentage >= 100.0 and milestone.status in (ResearchMilestoneStatus.PLANNED, "PLANNED"):
            milestone.status = ResearchMilestoneStatus.UNDER_REVIEW.value if hasattr(ResearchMilestoneStatus.UNDER_REVIEW, "value") else str(ResearchMilestoneStatus.UNDER_REVIEW)
            milestone.actual_completion_date = date.today()

        await db.commit()
        await db.refresh(milestone)
        return milestone

    @classmethod
    async def verify_milestone(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        milestone_id: UUID,
        data: ResearchMilestoneVerify,
        current_user_id: UUID,
    ) -> ResearchMilestone:
        """Perform formal independent acceptance verification of milestone."""
        milestone = await db.scalar(
            select(ResearchMilestone).where(
                ResearchMilestone.tenant_id == tenant_id,
                ResearchMilestone.id == milestone_id,
            )
        )
        if not milestone:
            raise ResearchMilestoneNotFoundException(milestone_id)

        dec_val = data.decision.value if hasattr(data.decision, "value") else str(data.decision)
        milestone.status = dec_val
        milestone.verified_by_user_id = current_user_id
        milestone.verified_at = datetime.now(UTC)
        milestone.verification_notes = data.verification_notes

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.RESEARCH_MILESTONE_ACCEPTED,
            entity_type="research_milestone",
            entity_id=milestone.id,
            user_id=current_user_id,
            new_values_json={"decision": dec_val, "notes": data.verification_notes},
        )
        await db.commit()
        await db.refresh(milestone)
        return milestone

    # =========================================================================
    # 8. ETHICS & COMPLIANCE APPROVALS
    # =========================================================================

    @classmethod
    async def create_ethics_approval(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: ResearchEthicsApprovalCreate,
        current_user_id: UUID,
    ) -> ResearchEthicsApproval:
        """Register a formal ethics/compliance application."""
        await cls.get_project(db, tenant_id, data.project_id)

        code = getattr(data, "approval_code", None) or getattr(data, "application_reference", None) or f"ETH-{uuid4().hex[:6].upper()}"
        gov_pol = getattr(data, "governing_policy_reference", None) or getattr(data, "governing_policy", "IRB-POL-2026")
        comm_name = getattr(data, "review_committee_name", None) or getattr(data, "committee_name", "Institutional Review Board")
        type_val = data.approval_type.value if hasattr(data.approval_type, "value") else str(data.approval_type)

        approval = ResearchEthicsApproval(
            tenant_id=tenant_id,
            project_id=data.project_id,
            approval_code=code,
            approval_type=type_val,
            governing_policy_reference=gov_pol,
            review_committee_name=comm_name,
            reviewer_user_id=None,
            submission_date=getattr(data, "submission_date", None) or date.today(),
            decision_date=None,
            status=ResearchEthicsApprovalStatus.UNDER_REVIEW.value if hasattr(ResearchEthicsApprovalStatus.UNDER_REVIEW, "value") else str(ResearchEthicsApprovalStatus.UNDER_REVIEW),
            conditions_and_restrictions=getattr(data, "conditions_and_restrictions", None),
            expiry_date=None,
            evidence_document_id=getattr(data, "document_id", None),
            decision_rationale=getattr(data, "confidential_notes", None),
            is_confidential=False,
        )
        db.add(approval)
        await db.commit()
        await db.refresh(approval)
        return approval

    @classmethod
    async def list_ethics_approvals(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        project_id: UUID,
    ) -> list[ResearchEthicsApproval]:
        """List ethics approval requests for a project."""
        await cls.get_project(db, tenant_id, project_id)
        approvals = (
            await db.scalars(
                select(ResearchEthicsApproval)
                .where(
                    ResearchEthicsApproval.tenant_id == tenant_id,
                    ResearchEthicsApproval.project_id == project_id,
                )
                .order_by(desc(ResearchEthicsApproval.submission_date))
            )
        ).all()
        return list(approvals)

    @classmethod
    async def decide_ethics_approval(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        approval_id: UUID,
        data: ResearchEthicsApprovalDecision,
        current_user_id: UUID,
    ) -> ResearchEthicsApproval:
        """Record formal ethics review board decision."""
        approval = await db.scalar(
            select(ResearchEthicsApproval).where(
                ResearchEthicsApproval.tenant_id == tenant_id,
                ResearchEthicsApproval.id == approval_id,
            )
        )
        if not approval:
            raise ResearchEthicsNotFoundException(approval_id)

        dec_val = data.decision.value if hasattr(data.decision, "value") else str(data.decision)
        approval.status = dec_val
        approval.decision_date = data.approval_date
        approval.expiry_date = data.expiry_date
        approval.reviewer_user_id = current_user_id
        approval.decision_rationale = data.decision_rationale
        if data.conditions_and_restrictions:
            approval.conditions_and_restrictions = data.conditions_and_restrictions

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.RESEARCH_ETHICS_DECIDED,
            entity_type="research_ethics_approval",
            entity_id=approval.id,
            user_id=current_user_id,
            new_values_json={
                "decision": dec_val,
                "expiry": str(data.expiry_date) if data.expiry_date else None,
            },
        )
        await db.commit()
        await db.refresh(approval)
        return approval

    # =========================================================================
    # 9. RESEARCH PUBLICATIONS & OUTPUTS
    # =========================================================================

    @classmethod
    async def create_research_output(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: ResearchOutputCreate,
        current_user_id: UUID,
    ) -> ResearchOutput:
        """Register a research publication or intellectual output with DOI uniqueness."""
        if data.doi_or_urn:
            clean_doi = data.doi_or_urn.strip().lower()
            existing = await db.scalar(
                select(ResearchOutput).where(
                    ResearchOutput.tenant_id == tenant_id,
                    func.lower(ResearchOutput.doi_or_urn) == clean_doi,
                )
            )
            if existing:
                raise ResearchOutputDuplicateException("DOI/URN", data.doi_or_urn)

        venue = getattr(data, "publisher_or_venue", None) or getattr(data, "publication_venue", "Academic Press")
        funder = getattr(data, "funding_acknowledgement", None) or getattr(data, "funding_acknowledgements", None)
        out_type = data.output_type.value if hasattr(data.output_type, "value") else str(data.output_type)

        output = ResearchOutput(
            tenant_id=tenant_id,
            project_id=data.project_id,
            output_type=out_type,
            title=data.title,
            abstract=data.abstract or "Scholarly publication abstract",
            authors_json=data.authors_json or [],
            lead_author_user_id=getattr(data, "lead_author_user_id", None),
            publication_date=data.publication_date or date.today(),
            publisher_or_venue=venue,
            doi_or_urn=data.doi_or_urn,
            issn_isbn=getattr(data, "issn_isbn", None),
            citation_count=data.citation_count or 0,
            research_domain=getattr(data, "research_domain", "Multidisciplinary"),
            peer_review_status="PEER_REVIEWED",
            open_access_type="GOLD_OA" if getattr(data, "open_access_status", False) else "CLOSED",
            funding_acknowledgement=funder,
            evidence_document_id=getattr(data, "document_id", None),
            verification_status="UNVERIFIED",
            verified_by_user_id=None,
            verified_at=None,
            verification_notes=None,
        )
        db.add(output)
        await db.flush()
        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.RESEARCH_OUTPUT_REGISTERED,
            entity_type="research_output",
            entity_id=output.id,
            user_id=current_user_id,
            new_values_json={"title": output.title, "type": out_type},
        )
        await db.commit()
        await db.refresh(output)
        return output

    @classmethod
    async def list_research_outputs(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        project_id: UUID | None = None,
        output_type: str | None = None,
        is_verified: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ResearchOutput], int]:
        """List publications with filters."""
        stmt = select(ResearchOutput).where(ResearchOutput.tenant_id == tenant_id)
        if project_id:
            stmt = stmt.where(ResearchOutput.project_id == project_id)
        if output_type:
            stmt = stmt.where(ResearchOutput.output_type == output_type)
        if is_verified is not None:
            v_status = "VERIFIED" if is_verified else "UNVERIFIED"
            stmt = stmt.where(ResearchOutput.verification_status == v_status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await db.scalar(count_stmt) or 0

        outputs = (
            await db.scalars(
                stmt.order_by(desc(ResearchOutput.publication_date)).limit(limit).offset(offset)
            )
        ).all()
        return list(outputs), total

    @classmethod
    async def get_research_output(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        output_id: UUID,
    ) -> ResearchOutput:
        """Fetch research output by ID."""
        output = await db.scalar(
            select(ResearchOutput).where(
                ResearchOutput.tenant_id == tenant_id,
                ResearchOutput.id == output_id,
            )
        )
        if not output:
            raise ResearchOutputNotFoundException(output_id)
        return output

    @classmethod
    async def verify_research_output(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        output_id: UUID,
        data: ResearchOutputVerify,
        current_user_id: UUID,
    ) -> ResearchOutput:
        """Verify publication validity against indexing source."""
        output = await cls.get_research_output(db, tenant_id, output_id)

        output.verification_status = "VERIFIED" if data.is_verified else "REJECTED"
        output.verified_by_user_id = current_user_id
        output.verified_at = datetime.now(UTC)
        output.verification_notes = data.verification_notes

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.RESEARCH_OUTPUT_VERIFIED,
            entity_type="research_output",
            entity_id=output.id,
            user_id=current_user_id,
            new_values_json={"is_verified": data.is_verified, "notes": data.verification_notes},
        )
        await db.commit()
        await db.refresh(output)
        return output

    # =========================================================================
    # 10. INTELLECTUAL PROPERTY & INVENTION DISCLOSURES
    # =========================================================================

    @classmethod
    async def create_invention_disclosure(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: ResearchInventionDisclosureCreate,
        current_user_id: UUID,
    ) -> ResearchInventionDisclosure:
        """Register a confidential invention disclosure."""
        existing = await db.scalar(
            select(ResearchInventionDisclosure).where(
                ResearchInventionDisclosure.tenant_id == tenant_id,
                ResearchInventionDisclosure.disclosure_code == data.disclosure_code,
            )
        )
        if existing:
            raise ResearchProjectInvalidTransitionException(
                "NONE", "DISCLOSED", f"Invention disclosure code '{data.disclosure_code}' already exists."
            )

        inv_title = getattr(data, "invention_title", None) or getattr(data, "title", "Invention Disclosure")
        tech_abs = getattr(data, "technical_abstract", None) or getattr(data, "technical_description", "Technical Description")
        conf_lvl = data.confidentiality_level.value if hasattr(data.confidentiality_level, "value") else str(data.confidentiality_level)
        pat_status = data.patent_status.value if hasattr(data.patent_status, "value") else str(data.patent_status)
        owner_pct = Decimal(str(getattr(data, "institutional_ownership_pct", None) or getattr(data, "institutional_ownership_percentage", 100.0) or 100.0))
        rev_amt = Decimal(str(getattr(data, "commercialization_revenue", 0.0) or 0.0))

        disclosure = ResearchInventionDisclosure(
            tenant_id=tenant_id,
            project_id=data.project_id,
            award_id=data.award_id,
            disclosure_code=data.disclosure_code,
            invention_title=inv_title,
            technical_abstract=tech_abs,
            detailed_description=getattr(data, "detailed_description", None),
            inventors_json=data.inventors_json or [],
            submission_date=getattr(data, "submission_date", None) or date.today(),
            confidentiality_level=conf_lvl,
            institutional_ownership_pct=owner_pct,
            evaluation_status="SUBMITTED",
            evaluated_by_user_id=None,
            evaluation_date=None,
            evaluation_notes=None,
            patent_application_number=data.patent_application_number,
            patent_jurisdiction=data.patent_jurisdiction,
            patent_filing_date=data.patent_filing_date,
            patent_status=pat_status,
            patent_grant_date=None,
            patent_number=None,
            commercialization_status="NOT_MARKETED",
            licensee_organization=None,
            license_revenue_total=rev_amt,
            evidence_document_id=getattr(data, "document_id", None),
            metadata_json=data.metadata_json or {},
        )
        db.add(disclosure)
        await db.flush()
        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.RESEARCH_IP_DISCLOSED,
            entity_type="research_invention_disclosure",
            entity_id=disclosure.id,
            user_id=current_user_id,
            new_values_json={
                "code": disclosure.disclosure_code,
                "title": disclosure.invention_title,
                "confidentiality": conf_lvl,
            },
        )
        await db.commit()
        await db.refresh(disclosure)
        return disclosure

    @classmethod
    async def list_invention_disclosures(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        current_user_id: UUID,
        has_confidential_permission: bool,
        project_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ResearchInventionDisclosure], int]:
        """List disclosures with RBAC confidentiality restrictions."""
        stmt = select(ResearchInventionDisclosure).where(
            ResearchInventionDisclosure.tenant_id == tenant_id
        )
        if project_id:
            stmt = stmt.where(ResearchInventionDisclosure.project_id == project_id)

        # Non-IP managers can only see PUBLIC or disclosures where they are inventor
        if not has_confidential_permission:
            stmt = stmt.where(
                or_(
                    ResearchInventionDisclosure.confidentiality_level == "PUBLIC",
                    cast(ResearchInventionDisclosure.inventors_json, String).ilike(f"%{current_user_id}%"),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await db.scalar(count_stmt) or 0

        items = (
            await db.scalars(
                stmt.order_by(desc(ResearchInventionDisclosure.created_at)).limit(limit).offset(offset)
            )
        ).all()
        return list(items), total

    @classmethod
    async def get_invention_disclosure(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        disclosure_id: UUID,
        current_user_id: UUID,
        has_confidential_permission: bool,
    ) -> ResearchInventionDisclosure:
        """Fetch invention disclosure with confidentiality access enforcement."""
        disclosure = await db.scalar(
            select(ResearchInventionDisclosure).where(
                ResearchInventionDisclosure.tenant_id == tenant_id,
                ResearchInventionDisclosure.id == disclosure_id,
            )
        )
        if not disclosure:
            raise ResearchIPNotFoundException(disclosure_id)

        if (
            disclosure.confidentiality_level != "PUBLIC"
            and not has_confidential_permission
        ):
            # Check if current user is one of the inventors
            inventor_ids = [str(inv.get("user_id")) for inv in disclosure.inventors_json if isinstance(inv, dict)]
            if str(current_user_id) not in inventor_ids:
                raise ResearchConfidentialAccessDeniedException(
                    "Access to confidential invention disclosure is restricted to inventors and authorized IP officers."
                )

        return disclosure

    @classmethod
    async def update_invention_disclosure(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        disclosure_id: UUID,
        data: ResearchInventionDisclosureUpdate,
        current_user_id: UUID,
        has_confidential_permission: bool,
    ) -> ResearchInventionDisclosure:
        """Update invention disclosure and patent milestones."""
        disclosure = await cls.get_invention_disclosure(
            db, tenant_id, disclosure_id, current_user_id, has_confidential_permission
        )

        update_dict = data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            if field == "title":
                disclosure.invention_title = value
            elif field == "technical_description":
                disclosure.technical_abstract = value
            elif field == "patent_filing_status":
                disclosure.patent_status = value.value if hasattr(value, "value") else str(value)
            elif field == "commercialization_revenue":
                disclosure.license_revenue_total = Decimal(str(value))
            elif hasattr(disclosure, field):
                setattr(disclosure, field, value)

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.RESEARCH_IP_UPDATED,
            entity_type="research_invention_disclosure",
            entity_id=disclosure.id,
            user_id=current_user_id,
            new_values_json={"patent_status": disclosure.patent_status},
        )
        await db.commit()
        await db.refresh(disclosure)
        return disclosure

    # =========================================================================
    # 11. RESEARCH FACILITY REFERENCES & PROJECT RISKS
    # =========================================================================

    @classmethod
    async def add_facility_reference(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: ResearchFacilityReferenceCreate,
        current_user_id: UUID,
    ) -> ResearchFacilityReference:
        """Reference laboratory or research equipment usage."""
        await cls.get_project(db, tenant_id, data.project_id)

        eq_id = getattr(data, "equipment_identifier", None) or getattr(data, "asset_reference_id", None)
        book_ref = getattr(data, "booking_reference_id", None) or getattr(data, "booking_reference", None)
        hours = float(getattr(data, "usage_hours_consumed", None) or getattr(data, "usage_hours", 0.0) or 0.0)

        ref = ResearchFacilityReference(
            tenant_id=tenant_id,
            project_id=data.project_id,
            facility_name=data.facility_name,
            facility_type=data.facility_type,
            campus_id=None,
            department_id=None,
            equipment_identifier=eq_id,
            equipment_name=None,
            booking_reference_id=book_ref,
            usage_hours_allocated=0.0,
            usage_hours_consumed=hours,
            is_active=True,
            notes=data.notes,
        )
        db.add(ref)
        await db.commit()
        await db.refresh(ref)
        return ref

    @classmethod
    async def list_facility_references(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        project_id: UUID,
    ) -> list[ResearchFacilityReference]:
        """List infrastructure references for a project."""
        await cls.get_project(db, tenant_id, project_id)
        refs = (
            await db.scalars(
                select(ResearchFacilityReference).where(
                    ResearchFacilityReference.tenant_id == tenant_id,
                    ResearchFacilityReference.project_id == project_id,
                )
            )
        ).all()
        return list(refs)

    @classmethod
    async def create_project_risk(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: ResearchProjectRiskCreate,
        current_user_id: UUID,
    ) -> ResearchProjectRisk:
        """Log a research risk with automated risk level calculation."""
        await cls.get_project(db, tenant_id, data.project_id)

        score = int(data.likelihood) * int(data.impact)
        if score >= 16:
            level = ResearchProjectRiskLevel.CRITICAL
        elif score >= 10:
            level = ResearchProjectRiskLevel.HIGH
        elif score >= 5:
            level = ResearchProjectRiskLevel.MEDIUM
        else:
            level = ResearchProjectRiskLevel.LOW

        code = getattr(data, "risk_code", None) or f"RSK-{uuid4().hex[:6].upper()}"
        title = getattr(data, "title", None) or getattr(data, "risk_title", "Project Risk")
        cat = getattr(data, "category", None) or getattr(data, "risk_category", "TECHNICAL")
        owner_id = getattr(data, "responsible_owner_id", None) or getattr(data, "owner_user_id", None) or current_user_id
        target_dt = getattr(data, "target_resolution_date", None) or (date.today() + timedelta(days=90))

        risk = ResearchProjectRisk(
            tenant_id=tenant_id,
            project_id=data.project_id,
            risk_code=code,
            title=title,
            category=cat,
            likelihood=str(data.likelihood),
            impact=str(data.impact),
            calculated_risk_level=level.value if hasattr(level, "value") else str(level),
            responsible_owner_id=owner_id,
            mitigation_plan=data.mitigation_plan or "Mitigation plan established",
            target_resolution_date=target_dt,
            status="IDENTIFIED",
            resolution_notes=None,
        )
        db.add(risk)
        await db.flush()
        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.RESEARCH_RISK_LOGGED,
            entity_type="research_project_risk",
            entity_id=risk.id,
            user_id=current_user_id,
            new_values_json={"title": risk.title, "level": str(level)},
        )
        await db.commit()
        await db.refresh(risk)
        return risk

    @classmethod
    async def list_project_risks(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        project_id: UUID,
    ) -> list[ResearchProjectRisk]:
        """List risks logged for a project."""
        await cls.get_project(db, tenant_id, project_id)
        risks = (
            await db.scalars(
                select(ResearchProjectRisk)
                .where(
                    ResearchProjectRisk.tenant_id == tenant_id,
                    ResearchProjectRisk.project_id == project_id,
                )
                .order_by(desc(ResearchProjectRisk.created_at))
            )
        ).all()
        return list(risks)

    @classmethod
    async def update_project_risk(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        risk_id: UUID,
        data: ResearchProjectRiskUpdate,
        current_user_id: UUID,
    ) -> ResearchProjectRisk:
        """Update risk status and resolution."""
        risk = await db.scalar(
            select(ResearchProjectRisk).where(
                ResearchProjectRisk.tenant_id == tenant_id,
                ResearchProjectRisk.id == risk_id,
            )
        )
        if not risk:
            raise ResearchRiskNotFoundException(risk_id)

        update_dict = data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            if field in ("likelihood", "impact"):
                setattr(risk, field, str(value))
            elif hasattr(risk, field):
                setattr(risk, field, value)

        # Recalculate if likelihood or impact changed
        try:
            l_val = int(risk.likelihood)
            i_val = int(risk.impact)
            score = l_val * i_val
            if score >= 16:
                risk.calculated_risk_level = ResearchProjectRiskLevel.CRITICAL.value if hasattr(ResearchProjectRiskLevel.CRITICAL, "value") else str(ResearchProjectRiskLevel.CRITICAL)
            elif score >= 10:
                risk.calculated_risk_level = ResearchProjectRiskLevel.HIGH.value if hasattr(ResearchProjectRiskLevel.HIGH, "value") else str(ResearchProjectRiskLevel.HIGH)
            elif score >= 5:
                risk.calculated_risk_level = ResearchProjectRiskLevel.MEDIUM.value if hasattr(ResearchProjectRiskLevel.MEDIUM, "value") else str(ResearchProjectRiskLevel.MEDIUM)
            else:
                risk.calculated_risk_level = ResearchProjectRiskLevel.LOW.value if hasattr(ResearchProjectRiskLevel.LOW, "value") else str(ResearchProjectRiskLevel.LOW)
        except (ValueError, TypeError):
            pass

        await db.commit()
        await db.refresh(risk)
        return risk

    # =========================================================================
    # 12. RESEARCH ANALYTICS & SCHEDULED COMPLIANCE SWEEPS
    # =========================================================================

    @classmethod
    async def get_analytics_summary(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> ResearchAnalyticsSummaryResponse:
        """Aggregate institutional research metrics and performance indicators."""
        projects = (
            await db.scalars(select(ResearchProject).where(ResearchProject.tenant_id == tenant_id))
        ).all()
        total_projects = len(projects)
        active_projects = sum(1 for p in projects if p.status in (ResearchProjectStatus.ACTIVE, "ACTIVE"))
        completed_projects = sum(1 for p in projects if p.status in (ResearchProjectStatus.COMPLETED, "COMPLETED"))
        under_review_projects = sum(1 for p in projects if p.status in (ResearchProjectStatus.UNDER_REVIEW, "UNDER_REVIEW"))

        total_proposed_budget = sum(float(p.proposed_budget) for p in projects)
        total_awarded_funding = sum(float(p.approved_budget) for p in projects)
        total_actual_expenditure = sum(float(p.actual_expenditure) for p in projects)

        budget_utilization_rate = (
            round((total_actual_expenditure / total_awarded_funding) * 100.0, 2)
            if total_awarded_funding > 0
            else 0.0
        )

        total_funding_opportunities = (
            await db.scalar(
                select(func.count()).where(ResearchFundingOpportunity.tenant_id == tenant_id)
            )
            or 0
        )
        applications = (
            await db.scalars(
                select(ResearchGrantApplication).where(ResearchGrantApplication.tenant_id == tenant_id)
            )
        ).all()
        total_grant_applications = len(applications)
        approved_grant_applications = sum(
            1
            for a in applications
            if a.internal_review_status in (ResearchGrantInternalReviewStatus.INSTITUTIONALLY_APPROVED, "INSTITUTIONALLY_APPROVED")
        )
        grant_success_rate = (
            round((approved_grant_applications / total_grant_applications) * 100.0, 2)
            if total_grant_applications > 0
            else 0.0
        )

        milestones = (
            await db.scalars(select(ResearchMilestone).where(ResearchMilestone.tenant_id == tenant_id))
        ).all()
        total_milestones = len(milestones)
        today = date.today()
        overdue_milestones = sum(
            1
            for m in milestones
            if m.planned_completion_date < today and m.status not in (ResearchMilestoneStatus.ACCEPTED, "ACCEPTED", ResearchMilestoneStatus.REJECTED, "REJECTED")
        )

        ethics = (
            await db.scalars(
                select(ResearchEthicsApproval).where(ResearchEthicsApproval.tenant_id == tenant_id)
            )
        ).all()
        ethics_approvals_count = len(ethics)
        expiring_ethics_approvals = sum(
            1
            for e in ethics
            if e.expiry_date and e.expiry_date <= today + timedelta(days=30)
        )

        pubs = (
            await db.scalars(select(ResearchOutput).where(ResearchOutput.tenant_id == tenant_id))
        ).all()
        total_publications = len(pubs)
        verified_publications = sum(1 for pb in pubs if pb.is_verified)
        total_citations = sum(pb.citation_count for pb in pubs)

        ips = (
            await db.scalars(
                select(ResearchInventionDisclosure).where(ResearchInventionDisclosure.tenant_id == tenant_id)
            )
        ).all()
        total_invention_disclosures = len(ips)
        patents_filed_or_granted = sum(
            1
            for ip in ips
            if ip.patent_status in ("FILED", "EXAMINATION", "GRANTED", "PROVISIONAL_FILED")
        )
        commercialization_revenue = sum(float(ip.commercialization_revenue) for ip in ips)

        return ResearchAnalyticsSummaryResponse(
            total_projects=total_projects,
            active_projects=active_projects,
            completed_projects=completed_projects,
            under_review_projects=under_review_projects,
            total_proposed_budget=total_proposed_budget,
            total_awarded_funding=total_awarded_funding,
            total_actual_expenditure=total_actual_expenditure,
            budget_utilization_rate=budget_utilization_rate,
            total_funding_opportunities=total_funding_opportunities,
            total_grant_applications=total_grant_applications,
            approved_grant_applications=approved_grant_applications,
            grant_success_rate=grant_success_rate,
            total_milestones=total_milestones,
            overdue_milestones=overdue_milestones,
            ethics_approvals_count=ethics_approvals_count,
            expiring_ethics_approvals=expiring_ethics_approvals,
            total_publications=total_publications,
            verified_publications=verified_publications,
            total_citations=total_citations,
            total_invention_disclosures=total_invention_disclosures,
            patents_filed_or_granted=patents_filed_or_granted,
            commercialization_revenue=commercialization_revenue,
        )

    @classmethod
    async def sweep_deadlines_and_compliance(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> ResearchDeadlineSweepResponse:
        """Scheduled operation to flag expiring ethics approvals and overdue deliverables."""
        today = date.today()

        expiring_ethics = (
            await db.scalars(
                select(ResearchEthicsApproval).where(
                    ResearchEthicsApproval.tenant_id == tenant_id,
                    ResearchEthicsApproval.status.in_([ResearchEthicsApprovalStatus.APPROVED, "APPROVED"]),
                    ResearchEthicsApproval.expiry_date.is_not(None),
                    ResearchEthicsApproval.expiry_date <= today + timedelta(days=30),
                )
            )
        ).all()

        for eth in expiring_ethics:
            if eth.expiry_date and eth.expiry_date < today:
                eth.status = ResearchEthicsApprovalStatus.EXPIRED.value if hasattr(ResearchEthicsApprovalStatus.EXPIRED, "value") else str(ResearchEthicsApprovalStatus.EXPIRED)

        overdue_milestones = (
            await db.scalars(
                select(ResearchMilestone).where(
                    ResearchMilestone.tenant_id == tenant_id,
                    ResearchMilestone.planned_completion_date < today,
                    ResearchMilestone.status.in_([
                        ResearchMilestoneStatus.PLANNED,
                        "PLANNED",
                        ResearchMilestoneStatus.IN_PROGRESS,
                        "IN_PROGRESS",
                    ]),
                )
            )
        ).all()
        for m in overdue_milestones:
            m.status = ResearchMilestoneStatus.BLOCKED.value if hasattr(ResearchMilestoneStatus.BLOCKED, "value") else str(ResearchMilestoneStatus.BLOCKED)
            if not m.blocker_notes:
                m.blocker_notes = f"Automatically flagged as overdue by scheduled compliance sweep on {today}."

        closing_opps = (
            await db.scalars(
                select(ResearchFundingOpportunity).where(
                    ResearchFundingOpportunity.tenant_id == tenant_id,
                    ResearchFundingOpportunity.status.in_([ResearchOpportunityStatus.OPEN, "OPEN"]),
                    ResearchFundingOpportunity.closing_date.is_not(None),
                    ResearchFundingOpportunity.closing_date < today,
                )
            )
        ).all()
        for op in closing_opps:
            op.status = ResearchOpportunityStatus.CLOSED.value if hasattr(ResearchOpportunityStatus.CLOSED, "value") else str(ResearchOpportunityStatus.CLOSED)

        await db.commit()

        return ResearchDeadlineSweepResponse(
            processed_at=datetime.now(UTC),
            expiring_ethics_approvals_flagged=len(expiring_ethics),
            overdue_milestones_flagged=len(overdue_milestones),
            closing_opportunities_flagged=len(closing_opps),
        )
