"""Admissions, Enrollment & Onboarding Domain Service Engine (Step 48).

Tagline: "One Campus. One System. One Source of Truth."

Implements:
- Configurable Admissions Cycle management and deadlines
- Applicant registration, duplicate detection, and merging
- Application management, program choices, and state transitions
- Document requirements and reviewer verification workflows
- Versioned eligibility evaluation engine with explainable criteria results
- Application multi-tier review with reviewer assignments and decisions
- Selection runs, merit list generation, and seat allocation with over-allocation guard
- Offer generation, expiry handling, and seat reservation
- Idempotent enrollment orchestration connecting accepted offers to canonical StudentProfile
- Post-enrollment institutional onboarding checklists and task verification
- Aggregate funnel and caseload analytics
"""

import logging
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import AuditEventCategory, record_audit_log
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)

BusinessRuleViolationException = BadRequestException
from app.core.security import get_password_hash
from app.models.admissions import (
    AdmissionApplication,
    AdmissionCycle,
    AdmissionCycleStatus,
    AdmissionOffer,
    ApplicantProfile,
    ApplicantVerificationStatus,
    ApplicationDocument,
    ApplicationDocumentRequirement,
    ApplicationProgramChoice,
    ApplicationReview,
    ApplicationStatus,
    DocumentVerificationStatus,
    EligibilityEvaluation,
    EligibilityRule,
    EnrollmentWorkflow,
    EnrollmentWorkflowStatus,
    OfferStatus,
    OnboardingChecklist,
    OnboardingStatus,
    OnboardingTask,
    OnboardingTaskCategory,
    ReviewDecision,
    SeatAllocation,
    SelectionResult,
    SelectionRun,
    SelectionStatus,
)
from app.models.core import Batch
from app.models.people import Role, StudentProfile, User, UserRoleAssignment
from app.schemas.admissions import (
    AdmissionApplicationCreate,
    AdmissionApplicationUpdate,
    AdmissionCycleCreate,
    AdmissionCycleUpdate,
    AdmissionOfferCreate,
    ApplicantProfileCreate,
    ApplicantProfileUpdate,
    ApplicationDocumentRequirementCreate,
    ApplicationDocumentUpload,
    ApplicationDocumentVerify,
    ApplicationReviewCreate,
    ApplicationStatusTransition,
    EligibilityRuleCreate,
    EligibilityRuleUpdate,
    EnrollmentWorkflowInitiate,
    OnboardingTaskUpdate,
    SeatAllocationCreate,
    SeatAllocationUpdate,
    SelectionRunCreate,
)

logger = logging.getLogger(__name__)


class AdmissionsService:
    """Domain service for Admissions, Enrollment & Onboarding orchestration."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # 1. ADMISSION CYCLES
    # =========================================================================

    async def create_cycle(
        self, tenant_id: UUID, payload: AdmissionCycleCreate, author_id: UUID
    ) -> AdmissionCycle:
        # Check code uniqueness
        stmt = select(AdmissionCycle).where(
            AdmissionCycle.tenant_id == tenant_id, AdmissionCycle.code == payload.code
        )
        res = await self.db.execute(stmt)
        if res.scalar_one_or_none():
            raise ConflictException(f"Admission cycle with code '{payload.code}' already exists")

        if payload.application_end_date < payload.application_start_date:
            raise BusinessRuleViolationException("Application end date cannot be before start date")

        cycle = AdmissionCycle(
            id=uuid4(),
            tenant_id=tenant_id,
            academic_year_id=payload.academic_year_id,
            code=payload.code,
            name=payload.name,
            admission_term=payload.admission_term,
            status=AdmissionCycleStatus.DRAFT,
            application_start_date=payload.application_start_date,
            application_end_date=payload.application_end_date,
            document_deadline=payload.document_deadline,
            offer_acceptance_deadline=payload.offer_acceptance_deadline,
            publication_date=payload.publication_date,
            is_active=True,
            settings=payload.settings,
        )
        self.db.add(cycle)
        await self.db.flush()

        await record_audit_log(
            self.db,
            tenant_id=tenant_id,
            action=AuditEventCategory.ADMISSION_CYCLE_CREATED,
            entity_type="AdmissionCycle",
            entity_id=cycle.id,
            user_id=author_id,
            new_values_json={"code": cycle.code, "name": cycle.name},
        )
        await self.db.commit()
        await self.db.refresh(cycle)
        return cycle

    async def update_cycle(
        self, tenant_id: UUID, cycle_id: UUID, payload: AdmissionCycleUpdate, author_id: UUID
    ) -> AdmissionCycle:
        cycle = await self.get_cycle(tenant_id, cycle_id)
        old_data = {"name": cycle.name, "status": cycle.status}

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(cycle, field, value)

        await record_audit_log(
            self.db,
            tenant_id=tenant_id,
            action=AuditEventCategory.ADMISSION_CYCLE_UPDATED,
            entity_type="AdmissionCycle",
            entity_id=cycle.id,
            user_id=author_id,
            old_values_json=old_data,
            new_values_json={"name": cycle.name, "status": str(cycle.status)},
        )
        await self.db.commit()
        await self.db.refresh(cycle)
        return cycle

    async def get_cycle(self, tenant_id: UUID, cycle_id: UUID) -> AdmissionCycle:
        stmt = select(AdmissionCycle).where(
            AdmissionCycle.tenant_id == tenant_id, AdmissionCycle.id == cycle_id
        )
        res = await self.db.execute(stmt)
        cycle = res.scalar_one_or_none()
        if not cycle:
            raise NotFoundException("AdmissionCycle", cycle_id)
        return cycle

    async def list_cycles(
        self, tenant_id: UUID, status: str | None = None
    ) -> list[AdmissionCycle]:
        stmt = select(AdmissionCycle).where(AdmissionCycle.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(AdmissionCycle.status == status)
        stmt = stmt.order_by(AdmissionCycle.application_start_date.desc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    # =========================================================================
    # 2. APPLICANT PROFILES & IDENTITY
    # =========================================================================

    async def register_applicant(
        self, tenant_id: UUID, payload: ApplicantProfileCreate, author_id: UUID | None = None
    ) -> ApplicantProfile:
        # Check duplicate by email
        stmt = select(ApplicantProfile).where(
            ApplicantProfile.tenant_id == tenant_id,
            func.lower(ApplicantProfile.email) == payload.email.lower(),
            ApplicantProfile.is_duplicate.is_(False),
        )
        res = await self.db.execute(stmt)
        existing = res.scalar_one_or_none()

        applicant_num = f"APP-{datetime.now(UTC).strftime('%Y')}-{uuid4().hex[:6].upper()}"

        applicant = ApplicantProfile(
            id=uuid4(),
            tenant_id=tenant_id,
            applicant_number=applicant_num,
            user_id=payload.user_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email.lower(),
            phone_number=payload.phone_number,
            date_of_birth=payload.date_of_birth,
            gender=payload.gender,
            nationality=payload.nationality,
            address_line1=payload.address_line1,
            city=payload.city,
            state=payload.state,
            postal_code=payload.postal_code,
            country=payload.country,
            emergency_contact_name=payload.emergency_contact_name,
            emergency_contact_phone=payload.emergency_contact_phone,
            verification_status=(
                ApplicantVerificationStatus.FLAGGED_DUPLICATE
                if existing
                else ApplicantVerificationStatus.PENDING_VERIFICATION
            ),
            is_duplicate=bool(existing),
            merged_into_applicant_id=existing.id if existing else None,
        )
        self.db.add(applicant)
        await self.db.flush()

        await record_audit_log(
            self.db,
            tenant_id=tenant_id,
            action=AuditEventCategory.ADMISSION_APPLICANT_REGISTERED,
            entity_type="ApplicantProfile",
            entity_id=applicant.id,
            user_id=author_id or payload.user_id,
            new_values_json={"applicant_number": applicant.applicant_number, "email": applicant.email},
        )
        await self.db.commit()
        await self.db.refresh(applicant)
        return applicant

    async def get_applicant(self, tenant_id: UUID, applicant_id: UUID) -> ApplicantProfile:
        stmt = select(ApplicantProfile).where(
            ApplicantProfile.tenant_id == tenant_id, ApplicantProfile.id == applicant_id
        )
        res = await self.db.execute(stmt)
        applicant = res.scalar_one_or_none()
        if not applicant:
            raise NotFoundException("ApplicantProfile", applicant_id)
        return applicant

    async def list_applicants(
        self, tenant_id: UUID, search: str | None = None
    ) -> list[ApplicantProfile]:
        stmt = select(ApplicantProfile).where(ApplicantProfile.tenant_id == tenant_id)
        if search:
            s = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(ApplicantProfile.first_name).like(s),
                    func.lower(ApplicantProfile.last_name).like(s),
                    func.lower(ApplicantProfile.email).like(s),
                    func.lower(ApplicantProfile.applicant_number).like(s),
                )
            )
        stmt = stmt.order_by(ApplicantProfile.created_at.desc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def update_applicant(
        self, tenant_id: UUID, applicant_id: UUID, payload: ApplicantProfileUpdate, author_id: UUID
    ) -> ApplicantProfile:
        applicant = await self.get_applicant(tenant_id, applicant_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(applicant, field, value)
        await self.db.commit()
        await self.db.refresh(applicant)
        return applicant

    async def merge_applicants(
        self,
        tenant_id: UUID,
        source_applicant_id: UUID,
        target_applicant_id: UUID,
        reason: str,
        author_id: UUID,
    ) -> ApplicantProfile:
        source = await self.get_applicant(tenant_id, source_applicant_id)
        target = await self.get_applicant(tenant_id, target_applicant_id)

        if source.id == target.id:
            raise BusinessRuleViolationException("Cannot merge an applicant profile into itself")

        # Re-link applications from source to target
        stmt = select(AdmissionApplication).where(
            AdmissionApplication.tenant_id == tenant_id,
            AdmissionApplication.applicant_id == source.id,
        )
        res = await self.db.execute(stmt)
        apps = res.scalars().all()
        for app in apps:
            app.applicant_id = target.id

        source.is_duplicate = True
        source.merged_into_applicant_id = target.id
        source.merge_reason = reason
        source.merged_at = datetime.now(UTC)

        await record_audit_log(
            self.db,
            tenant_id=tenant_id,
            action=AuditEventCategory.ADMISSION_APPLICANT_MERGED,
            entity_type="ApplicantProfile",
            entity_id=source.id,
            user_id=author_id,
            new_values_json={"target_applicant_id": str(target.id), "reason": reason},
        )
        await self.db.commit()
        await self.db.refresh(target)
        return target

    # =========================================================================
    # 3. APPLICATION WORKFLOW
    # =========================================================================

    async def create_application(
        self, tenant_id: UUID, payload: AdmissionApplicationCreate, author_id: UUID | None = None
    ) -> AdmissionApplication:
        cycle = await self.get_cycle(tenant_id, payload.cycle_id)
        applicant = await self.get_applicant(tenant_id, payload.applicant_id)

        # Calculate percentage if score and max score provided
        perc = payload.qualifying_percentage
        if perc is None and payload.qualifying_exam_score and payload.qualifying_exam_max_score:
            if payload.qualifying_exam_max_score > 0:
                perc = Decimal(
                    str(
                        round(
                            (payload.qualifying_exam_score / payload.qualifying_exam_max_score)
                            * 100,
                            2,
                        )
                    )
                )

        app_num = f"ADM-{datetime.now(UTC).strftime('%Y')}-{uuid4().hex[:6].upper()}"

        application = AdmissionApplication(
            id=uuid4(),
            tenant_id=tenant_id,
            cycle_id=cycle.id,
            applicant_id=applicant.id,
            application_number=app_num,
            program_id=payload.program_id,
            campus_id=payload.campus_id,
            admission_category=payload.admission_category,
            status=ApplicationStatus.DRAFT,
            qualifying_exam_name=payload.qualifying_exam_name,
            qualifying_exam_score=payload.qualifying_exam_score,
            qualifying_exam_max_score=payload.qualifying_exam_max_score,
            qualifying_percentage=perc,
            notes=payload.notes,
        )
        self.db.add(application)
        await self.db.flush()

        # Add program choices if supplied
        if payload.program_choices:
            for choice in payload.program_choices:
                p_choice = ApplicationProgramChoice(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    application_id=application.id,
                    program_id=choice.program_id,
                    campus_id=choice.campus_id,
                    preference_rank=choice.preference_rank,
                    is_active=True,
                )
                self.db.add(p_choice)

        await self.db.commit()
        await self.db.refresh(application)
        return application

    async def get_application(self, tenant_id: UUID, application_id: UUID) -> AdmissionApplication:
        stmt = (
            select(AdmissionApplication)
            .where(
                AdmissionApplication.tenant_id == tenant_id,
                AdmissionApplication.id == application_id,
            )
            .options(
                selectinload(AdmissionApplication.program_choices),
                selectinload(AdmissionApplication.documents),
                selectinload(AdmissionApplication.reviews),
                selectinload(AdmissionApplication.offers),
                selectinload(AdmissionApplication.applicant),
            )
        )
        res = await self.db.execute(stmt)
        application = res.scalar_one_or_none()
        if not application:
            raise NotFoundException("AdmissionApplication", application_id)
        return application

    async def list_applications(
        self,
        tenant_id: UUID,
        cycle_id: UUID | None = None,
        program_id: UUID | None = None,
        status: str | None = None,
    ) -> list[AdmissionApplication]:
        stmt = select(AdmissionApplication).where(AdmissionApplication.tenant_id == tenant_id)
        if cycle_id:
            stmt = stmt.where(AdmissionApplication.cycle_id == cycle_id)
        if program_id:
            stmt = stmt.where(AdmissionApplication.program_id == program_id)
        if status:
            stmt = stmt.where(AdmissionApplication.status == status)
        stmt = stmt.order_by(AdmissionApplication.created_at.desc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def update_application(
        self,
        tenant_id: UUID,
        application_id: UUID,
        payload: AdmissionApplicationUpdate,
        author_id: UUID,
    ) -> AdmissionApplication:
        application = await self.get_application(tenant_id, application_id)

        # Check if editable: allowed if DRAFT or within correction window
        if application.status != ApplicationStatus.DRAFT:
            window_end = application.correction_window_end
            if window_end is not None and window_end.tzinfo is None:
                window_end = window_end.replace(tzinfo=UTC)
            now_utc = datetime.now(UTC)
            if not window_end or now_utc > window_end:
                raise BusinessRuleViolationException(
                    f"Application is in status '{application.status}' and correction window has closed."
                )

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(application, field, value)

        # Recalculate percentage if updated
        if application.qualifying_exam_score and application.qualifying_exam_max_score:
            if application.qualifying_exam_max_score > 0:
                application.qualifying_percentage = Decimal(
                    str(
                        round(
                            (
                                application.qualifying_exam_score
                                / application.qualifying_exam_max_score
                            )
                            * 100,
                            2,
                        )
                    )
                )

        await self.db.commit()
        await self.db.refresh(application)
        return application

    async def submit_application(
        self, tenant_id: UUID, application_id: UUID, author_id: UUID
    ) -> AdmissionApplication:
        application = await self.get_application(tenant_id, application_id)
        cycle = await self.get_cycle(tenant_id, application.cycle_id)

        if application.status != ApplicationStatus.DRAFT:
            raise BusinessRuleViolationException(
                f"Application already submitted or in status '{application.status}'"
            )

        # Check application window
        today = date.today()
        if today > cycle.application_end_date:
            raise BusinessRuleViolationException(
                f"Application window for cycle '{cycle.name}' closed on {cycle.application_end_date}"
            )

        application.status = ApplicationStatus.SUBMITTED
        application.submitted_at = datetime.now(UTC)
        cycle.total_applications_count += 1

        await record_audit_log(
            self.db,
            tenant_id=tenant_id,
            action=AuditEventCategory.ADMISSION_APPLICATION_SUBMITTED,
            entity_type="AdmissionApplication",
            entity_id=application.id,
            user_id=author_id,
            new_values_json={"application_number": application.application_number},
        )
        await self.db.commit()
        await self.db.refresh(application)
        return application

    async def transition_application_status(
        self,
        tenant_id: UUID,
        application_id: UUID,
        payload: ApplicationStatusTransition,
        author_id: UUID,
    ) -> AdmissionApplication:
        application = await self.get_application(tenant_id, application_id)
        old_status = application.status
        application.status = payload.to_status
        if payload.notes:
            application.notes = (
                f"{application.notes or ''}\n[{datetime.now(UTC).isoformat()}] {payload.notes}"
            )

        await record_audit_log(
            self.db,
            tenant_id=tenant_id,
            action=AuditEventCategory.ADMISSION_APPLICATION_STATUS_CHANGED,
            entity_type="AdmissionApplication",
            entity_id=application.id,
            user_id=author_id,
            old_values_json={"status": old_status},
            new_values_json={"status": str(payload.to_status)},
        )
        await self.db.commit()
        await self.db.refresh(application)
        return application

    async def withdraw_application(
        self, tenant_id: UUID, application_id: UUID, reason: str, author_id: UUID
    ) -> AdmissionApplication:
        application = await self.get_application(tenant_id, application_id)
        if application.status in (ApplicationStatus.ENROLLED, ApplicationStatus.WITHDRAWN):
            raise BusinessRuleViolationException(
                f"Cannot withdraw application in status '{application.status}'"
            )

        application.status = ApplicationStatus.WITHDRAWN
        application.withdrawal_reason = reason
        await self.db.commit()
        await self.db.refresh(application)
        return application

    async def reopen_application(
        self,
        tenant_id: UUID,
        application_id: UUID,
        reason: str,
        correction_hours: int,
        author_id: UUID,
    ) -> AdmissionApplication:
        application = await self.get_application(tenant_id, application_id)
        application.status = ApplicationStatus.UNDER_REVIEW
        application.reopened_at = datetime.now(UTC)
        application.reopened_by_user_id = author_id
        application.reopening_reason = reason
        application.correction_window_end = datetime.now(UTC) + timedelta(hours=correction_hours)

        await self.db.commit()
        await self.db.refresh(application)
        return application

    # =========================================================================
    # 4. DOCUMENTS & EVIDENCE VERIFICATION
    # =========================================================================

    async def create_document_requirement(
        self, tenant_id: UUID, payload: ApplicationDocumentRequirementCreate, author_id: UUID
    ) -> ApplicationDocumentRequirement:
        req = ApplicationDocumentRequirement(
            id=uuid4(),
            tenant_id=tenant_id,
            cycle_id=payload.cycle_id,
            program_id=payload.program_id,
            document_name=payload.document_name,
            document_code=payload.document_code,
            is_mandatory=payload.is_mandatory,
            description=payload.description,
            is_active=True,
        )
        self.db.add(req)
        await self.db.commit()
        await self.db.refresh(req)
        return req

    async def list_document_requirements(
        self, tenant_id: UUID, cycle_id: UUID | None = None, program_id: UUID | None = None
    ) -> list[ApplicationDocumentRequirement]:
        stmt = select(ApplicationDocumentRequirement).where(
            ApplicationDocumentRequirement.tenant_id == tenant_id,
            ApplicationDocumentRequirement.is_active.is_(True),
        )
        if cycle_id:
            stmt = stmt.where(
                or_(
                    ApplicationDocumentRequirement.cycle_id == cycle_id,
                    ApplicationDocumentRequirement.cycle_id.is_(None),
                )
            )
        if program_id:
            stmt = stmt.where(
                or_(
                    ApplicationDocumentRequirement.program_id == program_id,
                    ApplicationDocumentRequirement.program_id.is_(None),
                )
            )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def upload_document(
        self,
        tenant_id: UUID,
        application_id: UUID,
        payload: ApplicationDocumentUpload,
        author_id: UUID,
    ) -> ApplicationDocument:
        application = await self.get_application(tenant_id, application_id)

        doc = ApplicationDocument(
            id=uuid4(),
            tenant_id=tenant_id,
            application_id=application.id,
            requirement_id=payload.requirement_id,
            document_name=payload.document_name,
            file_name=payload.file_name,
            file_size_bytes=payload.file_size_bytes,
            mime_type=payload.mime_type,
            storage_key=payload.storage_key,
            verification_status=DocumentVerificationStatus.PENDING,
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def verify_document(
        self,
        tenant_id: UUID,
        document_id: UUID,
        payload: ApplicationDocumentVerify,
        reviewer_id: UUID,
    ) -> ApplicationDocument:
        stmt = select(ApplicationDocument).where(
            ApplicationDocument.tenant_id == tenant_id, ApplicationDocument.id == document_id
        )
        res = await self.db.execute(stmt)
        doc = res.scalar_one_or_none()
        if not doc:
            raise NotFoundException("ApplicationDocument", document_id)

        doc.verification_status = payload.verification_status
        doc.rejection_reason = payload.rejection_reason
        doc.verified_by_user_id = reviewer_id
        doc.verified_at = datetime.now(UTC)

        await record_audit_log(
            self.db,
            tenant_id=tenant_id,
            action=AuditEventCategory.ADMISSION_DOCUMENT_VERIFIED,
            entity_type="ApplicationDocument",
            entity_id=doc.id,
            user_id=reviewer_id,
            new_values_json={"status": str(doc.verification_status)},
        )
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    # =========================================================================
    # 5. ELIGIBILITY & REVIEWS
    # =========================================================================

    async def create_eligibility_rule(
        self, tenant_id: UUID, payload: EligibilityRuleCreate, author_id: UUID
    ) -> EligibilityRule:
        rule = EligibilityRule(
            id=uuid4(),
            tenant_id=tenant_id,
            cycle_id=payload.cycle_id,
            program_id=payload.program_id,
            code=payload.code,
            name=payload.name,
            min_score_percentage=payload.min_score_percentage,
            required_qualification=payload.required_qualification,
            rule_version=1,
            is_active=True,
            criteria_json=payload.criteria_json,
        )
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def update_eligibility_rule(
        self, tenant_id: UUID, rule_id: UUID, payload: EligibilityRuleUpdate, author_id: UUID
    ) -> EligibilityRule:
        stmt = select(EligibilityRule).where(
            EligibilityRule.tenant_id == tenant_id, EligibilityRule.id == rule_id
        )
        res = await self.db.execute(stmt)
        rule = res.scalar_one_or_none()
        if not rule:
            raise NotFoundException("EligibilityRule", rule_id)

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(rule, field, value)
        rule.rule_version += 1

        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def list_eligibility_rules(
        self, tenant_id: UUID, cycle_id: UUID | None = None, program_id: UUID | None = None
    ) -> list[EligibilityRule]:
        stmt = select(EligibilityRule).where(
            EligibilityRule.tenant_id == tenant_id, EligibilityRule.is_active.is_(True)
        )
        if cycle_id:
            stmt = stmt.where(
                or_(EligibilityRule.cycle_id == cycle_id, EligibilityRule.cycle_id.is_(None))
            )
        if program_id:
            stmt = stmt.where(
                or_(EligibilityRule.program_id == program_id, EligibilityRule.program_id.is_(None))
            )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def evaluate_eligibility(
        self,
        tenant_id: UUID,
        application_id: UUID,
        rule_id: UUID,
        evaluator_id: UUID | None = None,
    ) -> EligibilityEvaluation:
        application = await self.get_application(tenant_id, application_id)
        stmt = select(EligibilityRule).where(
            EligibilityRule.tenant_id == tenant_id, EligibilityRule.id == rule_id
        )
        res = await self.db.execute(stmt)
        rule = res.scalar_one_or_none()
        if not rule:
            raise NotFoundException("EligibilityRule", rule_id)

        observed = application.qualifying_percentage
        is_eligible = False
        summary = ""

        if observed is None:
            summary = "Ineligible: Qualifying percentage not provided on application."
        elif observed >= rule.min_score_percentage:
            is_eligible = True
            summary = (
                f"Eligible: Observed score {observed}% meets minimum cutoff {rule.min_score_percentage}%"
            )
        else:
            summary = (
                f"Ineligible: Observed score {observed}% is below minimum cutoff {rule.min_score_percentage}%"
            )

        evaluation = EligibilityEvaluation(
            id=uuid4(),
            tenant_id=tenant_id,
            application_id=application.id,
            rule_id=rule.id,
            rule_version=rule.rule_version,
            is_eligible=is_eligible,
            observed_percentage=observed,
            evaluation_summary=summary,
            evaluated_by_user_id=evaluator_id,
        )
        self.db.add(evaluation)

        # Update application status
        if is_eligible:
            application.status = ApplicationStatus.ELIGIBLE
        else:
            application.status = ApplicationStatus.INELIGIBLE

        await record_audit_log(
            self.db,
            tenant_id=tenant_id,
            action=AuditEventCategory.ADMISSION_ELIGIBILITY_EVALUATED,
            entity_type="EligibilityEvaluation",
            entity_id=evaluation.id,
            user_id=evaluator_id,
            new_values_json={"is_eligible": is_eligible, "observed": float(observed or 0)},
        )
        await self.db.commit()
        await self.db.refresh(evaluation)
        return evaluation

    async def create_application_review(
        self, tenant_id: UUID, application_id: UUID, payload: ApplicationReviewCreate, author_id: UUID
    ) -> ApplicationReview:
        application = await self.get_application(tenant_id, application_id)

        review = ApplicationReview(
            id=uuid4(),
            tenant_id=tenant_id,
            application_id=application.id,
            reviewer_user_id=payload.reviewer_user_id,
            review_stage=payload.review_stage,
            score=payload.score,
            decision=payload.decision,
            decision_reason=payload.decision_reason,
            reviewer_notes=payload.reviewer_notes,
            is_completed=payload.is_completed,
            reviewed_at=datetime.now(UTC) if payload.is_completed else None,
        )
        self.db.add(review)

        if payload.decision == ReviewDecision.RECOMMEND_ADMIT:
            application.status = ApplicationStatus.SHORTLISTED
        elif payload.decision == ReviewDecision.RECOMMEND_REJECT:
            application.status = ApplicationStatus.REJECTED

        await record_audit_log(
            self.db,
            tenant_id=tenant_id,
            action=AuditEventCategory.ADMISSION_REVIEW_RECORDED,
            entity_type="ApplicationReview",
            entity_id=review.id,
            user_id=author_id,
            new_values_json={"decision": str(review.decision), "score": float(review.score or 0)},
        )
        await self.db.commit()
        await self.db.refresh(review)
        return review

    # =========================================================================
    # 6. SEAT ALLOCATION & MERIT SELECTION
    # =========================================================================

    async def create_seat_allocation(
        self, tenant_id: UUID, payload: SeatAllocationCreate, author_id: UUID
    ) -> SeatAllocation:
        stmt = select(SeatAllocation).where(
            SeatAllocation.tenant_id == tenant_id,
            SeatAllocation.cycle_id == payload.cycle_id,
            SeatAllocation.program_id == payload.program_id,
            SeatAllocation.campus_id == payload.campus_id,
            SeatAllocation.admission_category == payload.admission_category,
        )
        res = await self.db.execute(stmt)
        if res.scalar_one_or_none():
            raise ConflictException("Seat allocation already configured for this combination")

        allocation = SeatAllocation(
            id=uuid4(),
            tenant_id=tenant_id,
            cycle_id=payload.cycle_id,
            program_id=payload.program_id,
            campus_id=payload.campus_id,
            admission_category=payload.admission_category,
            total_capacity=payload.total_capacity,
            reserved_seats=0,
            confirmed_seats=0,
            waitlist_capacity=payload.waitlist_capacity,
        )
        self.db.add(allocation)
        await self.db.commit()
        await self.db.refresh(allocation)
        return allocation

    async def get_seat_allocation(
        self,
        tenant_id: UUID,
        cycle_id: UUID,
        program_id: UUID,
        campus_id: UUID | None = None,
        admission_category: str = "GENERAL",
    ) -> SeatAllocation:
        stmt = select(SeatAllocation).where(
            SeatAllocation.tenant_id == tenant_id,
            SeatAllocation.cycle_id == cycle_id,
            SeatAllocation.program_id == program_id,
            SeatAllocation.campus_id == campus_id,
            SeatAllocation.admission_category == admission_category,
        )
        res = await self.db.execute(stmt)
        allocation = res.scalar_one_or_none()
        if not allocation:
            raise NotFoundException(
                "SeatAllocation", f"{cycle_id}/{program_id}/{admission_category}"
            )
        return allocation

    async def update_seat_allocation(
        self, tenant_id: UUID, allocation_id: UUID, payload: SeatAllocationUpdate, author_id: UUID
    ) -> SeatAllocation:
        stmt = select(SeatAllocation).where(
            SeatAllocation.tenant_id == tenant_id, SeatAllocation.id == allocation_id
        )
        res = await self.db.execute(stmt)
        alloc = res.scalar_one_or_none()
        if not alloc:
            raise NotFoundException("SeatAllocation", allocation_id)

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(alloc, field, value)

        await self.db.commit()
        await self.db.refresh(alloc)
        return alloc

    async def create_selection_run(
        self, tenant_id: UUID, payload: SelectionRunCreate, author_id: UUID
    ) -> SelectionRun:
        cycle = await self.get_cycle(tenant_id, payload.cycle_id)

        # Get seat allocation capacity
        alloc_stmt = select(SeatAllocation).where(
            SeatAllocation.tenant_id == tenant_id,
            SeatAllocation.cycle_id == payload.cycle_id,
            SeatAllocation.program_id == payload.program_id,
        )
        alloc_res = await self.db.execute(alloc_stmt)
        allocation = alloc_res.scalar_one_or_none()
        capacity = allocation.total_capacity if allocation else 50

        # Query eligible applications ordered by percentage DESC
        stmt = (
            select(AdmissionApplication)
            .where(
                AdmissionApplication.tenant_id == tenant_id,
                AdmissionApplication.cycle_id == payload.cycle_id,
                AdmissionApplication.program_id == payload.program_id,
                AdmissionApplication.status.in_(
                    [ApplicationStatus.SUBMITTED, ApplicationStatus.ELIGIBLE, ApplicationStatus.SHORTLISTED]
                ),
            )
            .order_by(AdmissionApplication.qualifying_percentage.desc().nullslast())
        )
        apps_res = await self.db.execute(stmt)
        ranked_apps = apps_res.scalars().all()

        run = SelectionRun(
            id=uuid4(),
            tenant_id=tenant_id,
            cycle_id=payload.cycle_id,
            program_id=payload.program_id,
            name=payload.name,
            cutoff_score=payload.cutoff_score,
            total_selected=0,
            total_waitlisted=0,
            is_approved=False,
            is_published=False,
        )
        self.db.add(run)
        await self.db.flush()

        rank = 1
        waitlist_rank = 1
        selected_count = 0
        waitlisted_count = 0

        for app in ranked_apps:
            score = app.qualifying_percentage or Decimal("0.00")
            if selected_count < capacity:
                sel_status = SelectionStatus.SELECTED
                wl_rank = None
                selected_count += 1
                app.status = ApplicationStatus.SHORTLISTED
            else:
                sel_status = SelectionStatus.WAITLISTED
                wl_rank = waitlist_rank
                waitlist_rank += 1
                waitlisted_count += 1
                app.status = ApplicationStatus.WAITLISTED

            res_item = SelectionResult(
                id=uuid4(),
                tenant_id=tenant_id,
                selection_run_id=run.id,
                application_id=app.id,
                applicant_id=app.applicant_id,
                merit_rank=rank,
                merit_score=score,
                status=sel_status,
                waitlist_rank=wl_rank,
                seat_offered=False,
            )
            self.db.add(res_item)
            rank += 1

        run.total_selected = selected_count
        run.total_waitlisted = waitlisted_count

        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def approve_and_publish_selection(
        self, tenant_id: UUID, run_id: UUID, author_id: UUID
    ) -> SelectionRun:
        stmt = select(SelectionRun).where(
            SelectionRun.tenant_id == tenant_id, SelectionRun.id == run_id
        )
        res = await self.db.execute(stmt)
        run = res.scalar_one_or_none()
        if not run:
            raise NotFoundException("SelectionRun", run_id)

        run.is_approved = True
        run.approved_by_user_id = author_id
        run.approved_at = datetime.now(UTC)
        run.is_published = True
        run.published_at = datetime.now(UTC)

        await record_audit_log(
            self.db,
            tenant_id=tenant_id,
            action=AuditEventCategory.ADMISSION_SELECTION_PUBLISHED,
            entity_type="SelectionRun",
            entity_id=run.id,
            user_id=author_id,
            new_values_json={"total_selected": run.total_selected},
        )
        await self.db.commit()
        await self.db.refresh(run)
        return run

    # =========================================================================
    # 7. ADMISSION OFFERS & SEAT RESERVATION
    # =========================================================================

    async def issue_admission_offer(
        self, tenant_id: UUID, payload: AdmissionOfferCreate, author_id: UUID
    ) -> AdmissionOffer:
        application = await self.get_application(tenant_id, payload.application_id)

        # Check existing active offer
        active_offer_stmt = select(AdmissionOffer).where(
            AdmissionOffer.tenant_id == tenant_id,
            AdmissionOffer.application_id == application.id,
            AdmissionOffer.status.in_([OfferStatus.ISSUED, OfferStatus.ACCEPTED]),
        )
        existing_offer = (await self.db.execute(active_offer_stmt)).scalar_one_or_none()
        if existing_offer:
            raise ConflictException("An active admission offer already exists for this application")

        # Concurrency-safe seat reservation check
        alloc_stmt = (
            select(SeatAllocation)
            .where(
                SeatAllocation.tenant_id == tenant_id,
                SeatAllocation.cycle_id == application.cycle_id,
                SeatAllocation.program_id == application.program_id,
            )
            .with_for_update()
        )
        alloc_res = await self.db.execute(alloc_stmt)
        allocation = alloc_res.scalar_one_or_none()

        if allocation:
            total_allocated = allocation.reserved_seats + allocation.confirmed_seats
            if total_allocated >= allocation.total_capacity:
                raise BusinessRuleViolationException(
                    f"Program capacity reached ({allocation.total_capacity} seats allocated). Cannot issue new offer."
                )
            allocation.reserved_seats += 1

        offer_num = f"OFR-{datetime.now(UTC).strftime('%Y')}-{uuid4().hex[:6].upper()}"

        offer = AdmissionOffer(
            id=uuid4(),
            tenant_id=tenant_id,
            application_id=application.id,
            applicant_id=application.applicant_id,
            program_id=application.program_id,
            cycle_id=application.cycle_id,
            offer_number=offer_num,
            offer_date=date.today(),
            expiry_date=payload.expiry_date,
            deposit_required=payload.deposit_required,
            conditions_text=payload.conditions_text,
            status=OfferStatus.ISSUED,
        )
        self.db.add(offer)

        application.status = ApplicationStatus.OFFERED

        await record_audit_log(
            self.db,
            tenant_id=tenant_id,
            action=AuditEventCategory.ADMISSION_OFFER_ISSUED,
            entity_type="AdmissionOffer",
            entity_id=offer.id,
            user_id=author_id,
            new_values_json={"offer_number": offer.offer_number, "expiry_date": str(offer.expiry_date)},
        )
        await self.db.commit()
        await self.db.refresh(offer)
        return offer

    async def respond_to_offer(
        self,
        tenant_id: UUID,
        offer_id: UUID,
        accept: bool,
        decline_reason: str | None,
        author_id: UUID,
    ) -> AdmissionOffer:
        stmt = select(AdmissionOffer).where(
            AdmissionOffer.tenant_id == tenant_id, AdmissionOffer.id == offer_id
        )
        res = await self.db.execute(stmt)
        offer = res.scalar_one_or_none()
        if not offer:
            raise NotFoundException("AdmissionOffer", offer_id)

        if offer.status != OfferStatus.ISSUED:
            raise BusinessRuleViolationException(f"Offer is not in ISSUED state (current: {offer.status})")

        # Check expiry
        if date.today() > offer.expiry_date:
            offer.status = OfferStatus.EXPIRED
            await self._release_reserved_seat(tenant_id, offer.cycle_id, offer.program_id)
            await self.db.commit()
            raise BusinessRuleViolationException(f"Offer expired on {offer.expiry_date}")

        application = await self.get_application(tenant_id, offer.application_id)

        if accept:
            offer.status = OfferStatus.ACCEPTED
            offer.response_date = datetime.now(UTC)
            application.status = ApplicationStatus.OFFER_ACCEPTED
            audit_action = AuditEventCategory.ADMISSION_OFFER_ACCEPTED
        else:
            offer.status = OfferStatus.DECLINED
            offer.response_date = datetime.now(UTC)
            offer.decline_reason = decline_reason
            application.status = ApplicationStatus.OFFER_DECLINED
            # Release seat reservation
            await self._release_reserved_seat(tenant_id, offer.cycle_id, offer.program_id)
            audit_action = AuditEventCategory.ADMISSION_OFFER_DECLINED

        await record_audit_log(
            self.db,
            tenant_id=tenant_id,
            action=audit_action,
            entity_type="AdmissionOffer",
            entity_id=offer.id,
            user_id=author_id,
            new_values_json={"status": str(offer.status)},
        )
        await self.db.commit()
        await self.db.refresh(offer)
        return offer

    async def revoke_offer(
        self, tenant_id: UUID, offer_id: UUID, reason: str, author_id: UUID
    ) -> AdmissionOffer:
        stmt = select(AdmissionOffer).where(
            AdmissionOffer.tenant_id == tenant_id, AdmissionOffer.id == offer_id
        )
        res = await self.db.execute(stmt)
        offer = res.scalar_one_or_none()
        if not offer:
            raise NotFoundException("AdmissionOffer", offer_id)

        offer.status = OfferStatus.REVOKED
        offer.revocation_reason = reason
        offer.revoked_by_user_id = author_id

        # Release seat
        await self._release_reserved_seat(tenant_id, offer.cycle_id, offer.program_id)

        application = await self.get_application(tenant_id, offer.application_id)
        application.status = ApplicationStatus.CANCELLED

        await self.db.commit()
        await self.db.refresh(offer)
        return offer

    async def _release_reserved_seat(self, tenant_id: UUID, cycle_id: UUID, program_id: UUID) -> None:
        alloc_stmt = (
            select(SeatAllocation)
            .where(
                SeatAllocation.tenant_id == tenant_id,
                SeatAllocation.cycle_id == cycle_id,
                SeatAllocation.program_id == program_id,
            )
            .with_for_update()
        )
        res = await self.db.execute(alloc_stmt)
        alloc = res.scalar_one_or_none()
        if alloc and alloc.reserved_seats > 0:
            alloc.reserved_seats -= 1

    # =========================================================================
    # 8. ENROLLMENT ORCHESTRATION (IDEMPOTENT)
    # =========================================================================

    async def orchestrate_enrollment(
        self, tenant_id: UUID, payload: EnrollmentWorkflowInitiate, author_id: UUID
    ) -> EnrollmentWorkflow:
        # Check idempotency first
        existing_stmt = select(EnrollmentWorkflow).where(
            EnrollmentWorkflow.tenant_id == tenant_id,
            EnrollmentWorkflow.idempotency_key == payload.idempotency_key,
        )
        res = await self.db.execute(existing_stmt)
        existing_wf = res.scalar_one_or_none()
        if existing_wf and existing_wf.status == EnrollmentWorkflowStatus.COMPLETED:
            logger.info("Enrollment workflow already completed for idempotency key %s", payload.idempotency_key)
            return existing_wf

        offer_stmt = select(AdmissionOffer).where(
            AdmissionOffer.tenant_id == tenant_id, AdmissionOffer.id == payload.offer_id
        )
        offer = (await self.db.execute(offer_stmt)).scalar_one_or_none()
        if not offer:
            raise NotFoundException("AdmissionOffer", payload.offer_id)

        if offer.status != OfferStatus.ACCEPTED:
            raise BusinessRuleViolationException(
                f"Offer must be in ACCEPTED status to initiate enrollment (current: {offer.status})"
            )

        application = await self.get_application(tenant_id, payload.application_id)
        applicant = await self.get_applicant(tenant_id, offer.applicant_id)

        # Batch validation
        batch_stmt = select(Batch).where(
            Batch.tenant_id == tenant_id, Batch.id == payload.batch_id
        )
        batch = (await self.db.execute(batch_stmt)).scalar_one_or_none()
        if not batch:
            raise NotFoundException("Batch", payload.batch_id)

        wf_number = f"ENR-{datetime.now(UTC).strftime('%Y')}-{uuid4().hex[:6].upper()}"

        workflow = existing_wf or EnrollmentWorkflow(
            id=uuid4(),
            tenant_id=tenant_id,
            application_id=application.id,
            offer_id=offer.id,
            applicant_id=applicant.id,
            workflow_number=wf_number,
            batch_id=batch.id,
            current_semester_id=payload.current_semester_id,
            current_section_id=payload.current_section_id,
            status=EnrollmentWorkflowStatus.INITIATED,
            idempotency_key=payload.idempotency_key,
        )
        if not existing_wf:
            self.db.add(workflow)
        await self.db.flush()

        try:
            workflow.status = EnrollmentWorkflowStatus.IDENTITY_VALIDATED

            # Check if canonical student already exists for this user / applicant email
            student_stmt = (
                select(StudentProfile)
                .join(User, StudentProfile.user_id == User.id)
                .where(
                    StudentProfile.tenant_id == tenant_id,
                    or_(
                        StudentProfile.user_id == applicant.user_id,
                        func.lower(User.email) == applicant.email.lower(),
                    ),
                )
            )
            student_res = await self.db.execute(student_stmt)
            student = student_res.scalar_one_or_none()

            if not student:
                # Find or create User
                user_stmt = select(User).where(
                    User.primary_tenant_id == tenant_id,
                    func.lower(User.email) == applicant.email.lower(),
                )
                user = (await self.db.execute(user_stmt)).scalar_one_or_none()
                if not user:
                    user = User(
                        id=uuid4(),
                        primary_tenant_id=tenant_id,
                        email=applicant.email.lower(),
                        phone_number=applicant.phone_number,
                        password_hash=get_password_hash("CampusOS@Student2026"),
                        first_name=applicant.first_name,
                        last_name=applicant.last_name,
                        is_active=True,
                        is_verified=True,
                        status="ACTIVE",
                    )
                    self.db.add(user)
                    await self.db.flush()

                    # Assign student role
                    role_stmt = select(Role).where(
                        Role.name == "STUDENT",
                        or_(Role.tenant_id == tenant_id, Role.tenant_id.is_(None)),
                    )
                    role = (await self.db.execute(role_stmt)).scalars().first()
                    if role:
                        user_role = UserRoleAssignment(
                            id=uuid4(),
                            tenant_id=tenant_id,
                            user_id=user.id,
                            role_id=role.id,
                        )
                        self.db.add(user_role)

                # Generate unique admission number
                adm_num = f"STD-{datetime.now(UTC).strftime('%Y')}-{uuid4().hex[:5].upper()}"
                reg_num = f"REG-{datetime.now(UTC).strftime('%Y')}-{uuid4().hex[:5].upper()}"

                # Compute expected graduation date based on batch graduation year
                grad_year = batch.graduation_year or (date.today().year + 4)
                expected_grad = date(grad_year, 5, 31)

                student = StudentProfile(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    user_id=user.id,
                    admission_number=adm_num,
                    registration_number=reg_num,
                    roll_number=adm_num,
                    date_of_birth=applicant.date_of_birth,
                    gender=applicant.gender,
                    status="ADMITTED",
                    admission_date=date.today(),
                    expected_graduation_date=expected_grad,
                    program_id=application.program_id,
                    batch_id=batch.id,
                    current_semester_id=payload.current_semester_id,
                    current_section_id=payload.current_section_id,
                    emergency_contact_name=applicant.emergency_contact_name,
                    emergency_contact_phone=applicant.emergency_contact_phone,
                )
                self.db.add(student)
                await self.db.flush()

            workflow.student_id = student.id
            workflow.created_student_admission_number = student.admission_number
            workflow.status = EnrollmentWorkflowStatus.STUDENT_RECORD_CREATED

            # Update Seat Allocation: transfer reserved seat to confirmed seat
            alloc_stmt = (
                select(SeatAllocation)
                .where(
                    SeatAllocation.tenant_id == tenant_id,
                    SeatAllocation.cycle_id == application.cycle_id,
                    SeatAllocation.program_id == application.program_id,
                )
                .with_for_update()
            )
            alloc_res = await self.db.execute(alloc_stmt)
            alloc = alloc_res.scalar_one_or_none()
            if alloc:
                if alloc.reserved_seats > 0:
                    alloc.reserved_seats -= 1
                alloc.confirmed_seats += 1

            # Update Application status to ENROLLED
            application.status = ApplicationStatus.ENROLLED

            # Update Cycle aggregate enrolled counter
            cycle = await self.get_cycle(tenant_id, application.cycle_id)
            cycle.total_enrolled_count += 1

            # Create default Onboarding Checklist and standard tasks
            chk_stmt = select(OnboardingChecklist).where(
                OnboardingChecklist.tenant_id == tenant_id,
                OnboardingChecklist.student_id == student.id,
            )
            existing_chk = (await self.db.execute(chk_stmt)).scalar_one_or_none()
            if not existing_chk:
                checklist = OnboardingChecklist(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    student_id=student.id,
                    enrollment_workflow_id=workflow.id,
                    title=f"Onboarding Checklist - {student.admission_number}",
                    status=OnboardingStatus.IN_PROGRESS,
                    total_tasks=5,
                    completed_tasks=0,
                    target_completion_date=date.today() + timedelta(days=30),
                )
                self.db.add(checklist)
                await self.db.flush()

                default_tasks = [
                    ("Complete Emergency Contact & Medical Profile", OnboardingTaskCategory.PROFILE_VERIFICATION, True),
                    ("Submit Original Certificates for Physical Verification", OnboardingTaskCategory.DOCUMENT_SUBMISSION, True),
                    ("Institutional Fee Clearance & Deposit Reconciliation", OnboardingTaskCategory.FINANCE_SETTLEMENT, True),
                    ("New Student Orientation Attendance", OnboardingTaskCategory.ORIENTATION, True),
                    ("Initial Academic Advisor Meeting", OnboardingTaskCategory.ACADEMIC_ADVISING, False),
                ]
                for title, cat, mand in default_tasks:
                    task = OnboardingTask(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        checklist_id=checklist.id,
                        title=title,
                        task_category=cat,
                        is_mandatory=mand,
                        due_date=date.today() + timedelta(days=14),
                        status=OnboardingStatus.PENDING,
                    )
                    self.db.add(task)

            workflow.status = EnrollmentWorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now(UTC)

            await record_audit_log(
                self.db,
                tenant_id=tenant_id,
                action=AuditEventCategory.ADMISSION_ENROLLMENT_COMPLETED,
                entity_type="EnrollmentWorkflow",
                entity_id=workflow.id,
                user_id=author_id,
                new_values_json={"admission_number": student.admission_number, "student_id": str(student.id)},
            )
            await self.db.commit()
            await self.db.refresh(workflow)
            return workflow

        except Exception as exc:
            workflow.status = EnrollmentWorkflowStatus.FAILED
            workflow.failure_stage = workflow.status
            workflow.failure_reason = str(exc)
            workflow.retry_count += 1
            await self.db.commit()
            logger.error("Enrollment failed for workflow %s: %s", workflow.id, exc, exc_info=True)
            raise

    # =========================================================================
    # 9. ONBOARDING CHECKLIST & TASKS
    # =========================================================================

    async def get_student_onboarding(
        self, tenant_id: UUID, student_id: UUID
    ) -> OnboardingChecklist:
        stmt = (
            select(OnboardingChecklist)
            .where(
                OnboardingChecklist.tenant_id == tenant_id,
                OnboardingChecklist.student_id == student_id,
            )
            .options(selectinload(OnboardingChecklist.tasks))
        )
        res = await self.db.execute(stmt)
        checklist = res.scalar_one_or_none()
        if not checklist:
            raise NotFoundException("OnboardingChecklist", student_id)
        return checklist

    async def update_onboarding_task(
        self, tenant_id: UUID, task_id: UUID, payload: OnboardingTaskUpdate, author_id: UUID
    ) -> OnboardingTask:
        stmt = select(OnboardingTask).where(
            OnboardingTask.tenant_id == tenant_id, OnboardingTask.id == task_id
        )
        res = await self.db.execute(stmt)
        task = res.scalar_one_or_none()
        if not task:
            raise NotFoundException("OnboardingTask", task_id)

        task.status = payload.status
        task.verification_notes = payload.verification_notes
        if payload.status == OnboardingStatus.COMPLETED:
            task.completed_at = datetime.now(UTC)
            task.verified_by_user_id = author_id

        # Update checklist counters
        chk_stmt = (
            select(OnboardingChecklist)
            .where(OnboardingChecklist.id == task.checklist_id)
            .options(selectinload(OnboardingChecklist.tasks))
        )
        chk = (await self.db.execute(chk_stmt)).scalar_one()
        all_tasks = chk.tasks
        completed = sum(1 for t in all_tasks if t.status == OnboardingStatus.COMPLETED)
        chk.completed_tasks = completed
        if completed == chk.total_tasks and chk.total_tasks > 0:
            chk.status = OnboardingStatus.COMPLETED
            chk.completed_at = datetime.now(UTC)

        await record_audit_log(
            self.db,
            tenant_id=tenant_id,
            action=AuditEventCategory.ADMISSION_ONBOARDING_TASK_COMPLETED,
            entity_type="OnboardingTask",
            entity_id=task.id,
            user_id=author_id,
            new_values_json={"status": str(task.status)},
        )
        await self.db.commit()
        await self.db.refresh(task)
        return task

    # =========================================================================
    # 10. AGGREGATE ANALYTICS
    # =========================================================================

    async def get_admissions_analytics(self, tenant_id: UUID) -> dict[str, Any]:
        # Count applicants
        app_cnt_stmt = select(func.count(ApplicantProfile.id)).where(
            ApplicantProfile.tenant_id == tenant_id, ApplicantProfile.is_duplicate.is_(False)
        )
        total_applicants = (await self.db.execute(app_cnt_stmt)).scalar() or 0

        # Applications by status
        total_apps_stmt = select(func.count(AdmissionApplication.id)).where(
            AdmissionApplication.tenant_id == tenant_id
        )
        total_applications = (await self.db.execute(total_apps_stmt)).scalar() or 0

        submitted_stmt = select(func.count(AdmissionApplication.id)).where(
            AdmissionApplication.tenant_id == tenant_id,
            AdmissionApplication.status.in_([ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_REVIEW]),
        )
        submitted = (await self.db.execute(submitted_stmt)).scalar() or 0

        eligible_stmt = select(func.count(AdmissionApplication.id)).where(
            AdmissionApplication.tenant_id == tenant_id,
            AdmissionApplication.status.in_([ApplicationStatus.ELIGIBLE, ApplicationStatus.SHORTLISTED]),
        )
        eligible = (await self.db.execute(eligible_stmt)).scalar() or 0

        offered_stmt = select(func.count(AdmissionOffer.id)).where(
            AdmissionOffer.tenant_id == tenant_id
        )
        total_offers = (await self.db.execute(offered_stmt)).scalar() or 0

        accepted_stmt = select(func.count(AdmissionOffer.id)).where(
            AdmissionOffer.tenant_id == tenant_id, AdmissionOffer.status == OfferStatus.ACCEPTED
        )
        accepted_offers = (await self.db.execute(accepted_stmt)).scalar() or 0

        enrolled_stmt = select(func.count(EnrollmentWorkflow.id)).where(
            EnrollmentWorkflow.tenant_id == tenant_id,
            EnrollmentWorkflow.status == EnrollmentWorkflowStatus.COMPLETED,
        )
        enrolled_students = (await self.db.execute(enrolled_stmt)).scalar() or 0

        # Missing documents
        missing_docs_stmt = select(func.count(ApplicationDocument.id)).where(
            ApplicationDocument.tenant_id == tenant_id,
            ApplicationDocument.verification_status == DocumentVerificationStatus.PENDING,
        )
        missing_docs = (await self.db.execute(missing_docs_stmt)).scalar() or 0

        # Capacities
        cap_stmt = select(
            func.coalesce(func.sum(SeatAllocation.total_capacity), 0),
            func.coalesce(func.sum(SeatAllocation.confirmed_seats), 0),
        ).where(SeatAllocation.tenant_id == tenant_id)
        cap_res = (await self.db.execute(cap_stmt)).first()
        total_cap, confirmed = cap_res if cap_res else (0, 0)

        seat_utilization = Decimal("0.00")
        if total_cap > 0:
            seat_utilization = Decimal(str(round((confirmed / total_cap) * 100, 2)))

        conversion_rate = Decimal("0.00")
        if total_applications > 0:
            conversion_rate = Decimal(str(round((enrolled_students / total_applications) * 100, 2)))

        return {
            "total_applicants": total_applicants,
            "total_applications": total_applications,
            "submitted_applications": submitted,
            "under_review_applications": submitted,
            "eligible_applications": eligible,
            "offered_applications": total_offers,
            "accepted_offers": accepted_offers,
            "enrolled_students": enrolled_students,
            "conversion_rate_percentage": conversion_rate,
            "seat_utilization_percentage": seat_utilization,
            "missing_documents_count": missing_docs,
        }
