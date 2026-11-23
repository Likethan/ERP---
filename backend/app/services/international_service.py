"""Service Layer for Enterprise International Relations, Student Exchange & Global Mobility (Step 60).

Product Identity: "CampusOS — One Campus. One System. One Source of Truth."

Implements enterprise-grade business logic:
- Institutional partner registry and multi-tenant agreement lifecycle management
- Study abroad & student exchange programs with automated prerequisite and eligibility checks
- Multi-stage student application workflow:
  Draft -> Submitted -> Eligibility Review -> Department Review -> Intl Office Review ->
  Approved -> Partner Nomination -> Partner Decision -> Pre-Departure -> Active Mobility -> Completed
- Inbound exchange student onboarding, orientation check-in, and host department coordination
- Faculty exchange and visiting scholar academic collaboration with HOD and VP approvals
- Academic credit equivalency mappings and committee-governed credit transfer reviews (never automated)
- Mobility document checklists and secure verification
- Mobility scholarship and finance-integrated funding coordination
- Dashboard telemetry and automated deadline sweeps
"""

import logging
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import DomainEventType, event_publisher
from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    ValidationException,
)
from app.models.international import (
    AgreementAmendment,
    AgreementScopeType,
    AgreementStatus,
    ApplicationReviewHistory,
    CourseEquivalencyMapping,
    CreditEquivalencyStatus,
    CreditTransferStatus,
    DocumentVerificationStatus,
    FacultyMobilityDirection,
    FacultyMobilityRecord,
    FacultyMobilityStatus,
    FundingStatus,
    InboundStudentProfile,
    InboundStudentStatus,
    InstitutionalAgreement,
    InternationalPartner,
    InternationalPolicyConfig,
    MobilityApplication,
    MobilityApplicationStatus,
    MobilityDirection,
    MobilityDocument,
    MobilityDocumentVerificationStatus,
    MobilityFundingRequest,
    MobilityFundingStatus,
    MobilityProgram,
    MobilityProgramType,
    MobilityScholarship,
    PartnerCategory,
    StudentCreditTransferRequest,
)
from app.models.people import StudentProfile, User
from app.schemas.international import (
    AgreementAmendmentCreate,
    AgreementAmendmentResponse,
    CourseEquivalencyCreate,
    CourseEquivalencyEvaluationRequest,
    CourseEquivalencyResponse,
    CreditTransferApprovalRequest,
    CreditTransferRequestCreate,
    CreditTransferResponse,
    FacultyMobilityApprovalRequest,
    FacultyMobilityCreate,
    FacultyMobilityResponse,
    InboundOrientationCheckinRequest,
    InboundStudentCreate,
    InboundStudentResponse,
    InstitutionalAgreementCreate,
    InstitutionalAgreementResponse,
    InstitutionalAgreementUpdate,
    InternationalDashboardMetrics,
    InternationalPartnerCreate,
    InternationalPartnerResponse,
    InternationalPartnerUpdate,
    InternationalPolicyConfigCreateOrUpdate,
    InternationalPolicyConfigResponse,
    MobilityApplicationCreate,
    MobilityApplicationResponse,
    MobilityApplicationReviewRequest,
    MobilityDocumentCreate,
    MobilityDocumentResponse,
    MobilityDocumentVerifyRequest,
    MobilityFundingApprovalRequest,
    MobilityFundingRequestCreate,
    MobilityFundingRequestResponse,
    MobilityProgramCreate,
    MobilityProgramResponse,
    MobilityProgramUpdate,
    MobilityScholarshipCreate,
    MobilityScholarshipResponse,
    PartnerDecisionRequest,
    PartnerNominationRequest,
    PreDepartureUpdateRequest,
)

logger = logging.getLogger("campusos.international")


class InternationalService:
    def __init__(self, db: AsyncSession, tenant_id: UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id

    # =========================================================================
    # POLICY CONFIG
    # =========================================================================

    async def get_or_create_config(self) -> InternationalPolicyConfig:
        stmt = select(InternationalPolicyConfig).where(InternationalPolicyConfig.tenant_id == self.tenant_id)
        res = await self.db.execute(stmt)
        config = res.scalar_one_or_none()
        if not config:
            config = InternationalPolicyConfig(
                tenant_id=self.tenant_id,
            )
            self.db.add(config)
            await self.db.flush()
        return config

    async def update_config(self, data: InternationalPolicyConfigCreateOrUpdate) -> InternationalPolicyConfigResponse:
        config = await self.get_or_create_config()
        config.agreement_renewal_notice_days = data.agreement_warning_days
        config.require_hod_approval = data.require_department_approval_first
        config.require_vp_approval = data.require_vp_approval_for_faculty
        config.credit_transfer_committee_required = data.credit_transfer_requires_academic_council
        config.enable_inbound_mobility = data.inbound_orientation_mandatory
        await self.db.flush()
        await self.db.refresh(config)
        return InternationalPolicyConfigResponse.model_validate(config)

    # =========================================================================
    # 1. INTERNATIONAL PARTNERS
    # =========================================================================

    async def create_partner(
        self, data: InternationalPartnerCreate, current_user_id: UUID | None = None
    ) -> InternationalPartnerResponse:
        existing_stmt = select(InternationalPartner).where(
            and_(
                InternationalPartner.tenant_id == self.tenant_id,
                func.lower(InternationalPartner.name) == data.partner_name.strip().lower(),
                func.lower(InternationalPartner.country) == (data.country_name or data.country_code).strip().lower(),
            )
        )
        existing = (await self.db.execute(existing_stmt)).scalar_one_or_none()
        if existing:
            raise ConflictException(f"Partner '{data.partner_name}' already registered")

        c_code = data.country_code.strip().upper() if data.country_code else (data.country_name[:2].upper() if data.country_name else "XX")
        c_name = data.country_name.strip() if data.country_name else c_code

        partner = InternationalPartner(
            tenant_id=self.tenant_id,
            name=data.partner_name.strip(),
            country=c_name,
            country_code=c_code,
            city=data.city.strip() if data.city else None,
            website=data.official_website,
            partnership_category=data.category.value if hasattr(data.category, "value") else str(data.category),
            status="ACTIVE" if data.is_active else "INACTIVE",
            primary_contact_name=data.primary_contact_name,
            primary_contact_email=data.primary_contact_email,
            primary_contact_phone=data.primary_contact_phone,
            linked_campuses=[str(data.campus_id)] if data.campus_id else [],
            linked_departments=[str(data.department_id)] if data.department_id else [],
            linked_programs=[str(data.academic_program_id)] if data.academic_program_id else [],
            notes=None,
        )
        self.db.add(partner)
        await self.db.flush()

        await event_publisher.publish(
            db=self.db,
            tenant_id=self.tenant_id,
            event_type=DomainEventType.INTERNATIONAL_PARTNER_REGISTERED,
            aggregate_type="InternationalPartner",
            aggregate_id=partner.id,
            payload={
                "partner_id": str(partner.id),
                "partner_name": partner.name,
                "country": partner.country,
            },
        )
        return await self._format_partner_response(partner)

    async def _format_partner_response(self, partner: InternationalPartner) -> InternationalPartnerResponse:
        await self.db.refresh(partner)
        resp = InternationalPartnerResponse.model_validate(partner)
        resp.country_code = partner.country_code or (partner.country[:2].upper() if partner.country else "XX")
        resp.country_name = partner.country
        return resp

    async def list_partners(
        self,
        country_code: str | None = None,
        category: PartnerCategory | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[InternationalPartnerResponse]:
        query = select(InternationalPartner).where(InternationalPartner.tenant_id == self.tenant_id)
        if country_code:
            code_clean = country_code.strip()
            query = query.where(
                or_(
                    func.upper(InternationalPartner.country_code) == code_clean.upper(),
                    func.upper(InternationalPartner.country) == code_clean.upper(),
                    func.lower(InternationalPartner.country).ilike(f"%{code_clean.lower()}%"),
                )
            )
        if category:
            cat_val = category.value if hasattr(category, "value") else str(category)
            query = query.where(InternationalPartner.partnership_category == cat_val)
        if is_active is not None:
            expected_status = "ACTIVE" if is_active else "INACTIVE"
            query = query.where(InternationalPartner.status == expected_status)
        if search:
            s = f"%{search.strip().lower()}%"
            query = query.where(
                or_(
                    func.lower(InternationalPartner.name).ilike(s),
                    func.lower(InternationalPartner.city).ilike(s),
                    func.lower(InternationalPartner.country).ilike(s),
                )
            )

        query = query.order_by(InternationalPartner.name.asc()).offset(offset).limit(limit)
        partners = (await self.db.execute(query)).scalars().all()

        results = []
        for p in partners:
            resp = await self._format_partner_response(p)
            agr_count = await self.db.scalar(
                select(func.count(InstitutionalAgreement.id)).where(
                    and_(
                        InstitutionalAgreement.tenant_id == self.tenant_id,
                        InstitutionalAgreement.partner_id == p.id,
                        InstitutionalAgreement.status.in_([AgreementStatus.ACTIVE.value, AgreementStatus.EXPIRING.value]),
                    )
                )
            )
            prog_count = await self.db.scalar(
                select(func.count(MobilityProgram.id)).where(
                    and_(
                        MobilityProgram.tenant_id == self.tenant_id,
                        MobilityProgram.partner_id == p.id,
                        MobilityProgram.status == "PUBLISHED",
                    )
                )
            )
            resp.active_agreements_count = agr_count or 0
            resp.active_programs_count = prog_count or 0
            results.append(resp)
        return results

    async def get_partner(self, partner_id: UUID) -> InternationalPartnerResponse:
        stmt = select(InternationalPartner).where(
            and_(
                InternationalPartner.tenant_id == self.tenant_id,
                InternationalPartner.id == partner_id,
            )
        )
        partner = (await self.db.execute(stmt)).scalar_one_or_none()
        if not partner:
            raise NotFoundException("International partner not found")

        resp = await self._format_partner_response(partner)
        agr_count = await self.db.scalar(
            select(func.count(InstitutionalAgreement.id)).where(
                and_(
                    InstitutionalAgreement.tenant_id == self.tenant_id,
                    InstitutionalAgreement.partner_id == partner.id,
                    InstitutionalAgreement.status.in_([AgreementStatus.ACTIVE.value, AgreementStatus.EXPIRING.value]),
                )
            )
        )
        prog_count = await self.db.scalar(
            select(func.count(MobilityProgram.id)).where(
                and_(
                    MobilityProgram.tenant_id == self.tenant_id,
                    MobilityProgram.partner_id == partner.id,
                    MobilityProgram.status == "PUBLISHED",
                )
            )
        )
        resp.active_agreements_count = agr_count or 0
        resp.active_programs_count = prog_count or 0
        return resp

    async def update_partner(self, partner_id: UUID, data: InternationalPartnerUpdate) -> InternationalPartnerResponse:
        stmt = select(InternationalPartner).where(
            and_(
                InternationalPartner.tenant_id == self.tenant_id,
                InternationalPartner.id == partner_id,
            )
        )
        partner = (await self.db.execute(stmt)).scalar_one_or_none()
        if not partner:
            raise NotFoundException("International partner not found")

        if data.partner_name:
            partner.name = data.partner_name
        if data.country_name:
            partner.country = data.country_name
        if data.city:
            partner.city = data.city
        if data.official_website:
            partner.website = data.official_website
        if data.category:
            partner.partnership_category = data.category.value if hasattr(data.category, "value") else str(data.category)
        if data.is_active is not None:
            partner.status = "ACTIVE" if data.is_active else "INACTIVE"
        if data.primary_contact_name:
            partner.primary_contact_name = data.primary_contact_name
        if data.primary_contact_email:
            partner.primary_contact_email = data.primary_contact_email
        if data.primary_contact_phone:
            partner.primary_contact_phone = data.primary_contact_phone

        await self.db.flush()
        return await self.get_partner(partner.id)

    # =========================================================================
    # 2. INSTITUTIONAL AGREEMENTS & AMENDMENTS
    # =========================================================================

    async def create_agreement(
        self, data: InstitutionalAgreementCreate, current_user_id: UUID | None = None
    ) -> InstitutionalAgreementResponse:
        partner = await self.db.get(InternationalPartner, data.partner_id)
        if not partner or partner.tenant_id != self.tenant_id:
            raise NotFoundException("Partner institution not found")

        if data.effective_end_date <= data.effective_start_date:
            raise ValidationException("Agreement end date must be strictly after start date")

        ref_no = f"AGR-{datetime.now(UTC).year}-{uuid4().hex[:6].upper()}"

        agreement = InstitutionalAgreement(
            tenant_id=self.tenant_id,
            partner_id=data.partner_id,
            agreement_number=ref_no,
            title=data.agreement_title.strip(),
            agreement_type=data.agreement_type.strip(),
            status=data.status.value if hasattr(data.status, "value") else str(data.status),
            start_date=data.effective_start_date,
            expiry_date=data.effective_end_date,
            renewal_reminder_days=data.renewal_window_days,
            responsible_coordinator_user_id=data.responsible_coordinator_user_id or current_user_id,
            scope_student_exchange=AgreementScopeType.STUDENT_EXCHANGE in (data.scope_types or []),
            scope_faculty_exchange=AgreementScopeType.FACULTY_EXCHANGE in (data.scope_types or []),
            scope_joint_research=AgreementScopeType.JOINT_RESEARCH in (data.scope_types or []),
            scope_dual_degree=AgreementScopeType.DUAL_DEGREE in (data.scope_types or []),
            scope_internships=AgreementScopeType.INTERNSHIPS in (data.scope_types or []),
            scope_collaborative_academic=AgreementScopeType.COLLABORATIVE_ACADEMIC in (data.scope_types or []),
            document_url=data.document_reference_url,
            notes=data.funding_support_notes,
        )
        self.db.add(agreement)
        await self.db.flush()

        await event_publisher.publish(
            db=self.db,
            tenant_id=self.tenant_id,
            event_type=DomainEventType.AGREEMENT_STATUS_CHANGED,
            aggregate_type="InstitutionalAgreement",
            aggregate_id=agreement.id,
            payload={
                "agreement_id": str(agreement.id),
                "reference_number": agreement.agreement_number,
                "partner_id": str(agreement.partner_id),
                "new_status": agreement.status,
            },
        )
        return await self._format_agreement_response(agreement)

    async def _format_agreement_response(self, agreement: InstitutionalAgreement) -> InstitutionalAgreementResponse:
        await self.db.refresh(agreement)
        resp = InstitutionalAgreementResponse.model_validate(agreement)
        if agreement.partner_id:
            partner = await self.db.get(InternationalPartner, agreement.partner_id)
            if partner:
                resp.partner_name = partner.name
                resp.partner_country = partner.country

        if agreement.responsible_coordinator_user_id:
            user = await self.db.get(User, agreement.responsible_coordinator_user_id)
            if user:
                resp.coordinator_name = getattr(user, "full_name", None) or getattr(user, "email", "Staff")

        today = date.today()
        window = agreement.renewal_reminder_days or 90
        if agreement.status in [AgreementStatus.ACTIVE.value, AgreementStatus.EXPIRING.value] and (agreement.expiry_date - today).days <= window:
            resp.is_expiring_soon = True
        return resp

    async def list_agreements(
        self,
        partner_id: UUID | None = None,
        status: AgreementStatus | None = None,
        scope_type: AgreementScopeType | None = None,
        expiring_soon: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[InstitutionalAgreementResponse]:
        query = select(InstitutionalAgreement).where(InstitutionalAgreement.tenant_id == self.tenant_id)
        if partner_id:
            query = query.where(InstitutionalAgreement.partner_id == partner_id)
        if status:
            st_val = status.value if hasattr(status, "value") else str(status)
            query = query.where(InstitutionalAgreement.status == st_val)

        today = date.today()
        if expiring_soon:
            query = query.where(
                and_(
                    InstitutionalAgreement.status.in_([AgreementStatus.ACTIVE.value, AgreementStatus.EXPIRING.value]),
                    InstitutionalAgreement.expiry_date <= today + timedelta(days=90),
                    InstitutionalAgreement.expiry_date >= today,
                )
            )

        query = query.order_by(InstitutionalAgreement.expiry_date.asc()).offset(offset).limit(limit)
        agreements = (await self.db.execute(query)).scalars().all()

        results = []
        for agr in agreements:
            if scope_type and scope_type not in (agr.scope_types or []):
                continue
            results.append(await self._format_agreement_response(agr))
        return results

    async def get_agreement(self, agreement_id: UUID) -> InstitutionalAgreementResponse:
        stmt = select(InstitutionalAgreement).where(
            and_(
                InstitutionalAgreement.tenant_id == self.tenant_id,
                InstitutionalAgreement.id == agreement_id,
            )
        )
        agreement = (await self.db.execute(stmt)).scalar_one_or_none()
        if not agreement:
            raise NotFoundException("Institutional agreement not found")
        return await self._format_agreement_response(agreement)

    async def update_agreement(
        self, agreement_id: UUID, data: InstitutionalAgreementUpdate, current_user_id: UUID | None = None
    ) -> InstitutionalAgreementResponse:
        stmt = select(InstitutionalAgreement).where(
            and_(
                InstitutionalAgreement.tenant_id == self.tenant_id,
                InstitutionalAgreement.id == agreement_id,
            )
        )
        agreement = (await self.db.execute(stmt)).scalar_one_or_none()
        if not agreement:
            raise NotFoundException("Institutional agreement not found")

        old_status = agreement.status
        if data.agreement_title:
            agreement.title = data.agreement_title
        if data.effective_start_date:
            agreement.start_date = data.effective_start_date
        if data.effective_end_date:
            agreement.expiry_date = data.effective_end_date
        if data.status:
            agreement.status = data.status.value if hasattr(data.status, "value") else str(data.status)
            if agreement.status == AgreementStatus.APPROVED.value:
                agreement.approved_by_user_id = current_user_id

            await event_publisher.publish(
                db=self.db,
                tenant_id=self.tenant_id,
                event_type=DomainEventType.AGREEMENT_STATUS_CHANGED,
                aggregate_type="InstitutionalAgreement",
                aggregate_id=agreement.id,
                payload={
                    "agreement_id": str(agreement.id),
                    "old_status": old_status,
                    "new_status": agreement.status,
                },
            )

        await self.db.flush()
        return await self._format_agreement_response(agreement)

    async def add_amendment(
        self, agreement_id: UUID, data: AgreementAmendmentCreate, current_user_id: UUID | None = None
    ) -> AgreementAmendmentResponse:
        agreement = await self.db.get(InstitutionalAgreement, agreement_id)
        if not agreement or agreement.tenant_id != self.tenant_id:
            raise NotFoundException("Institutional agreement not found")

        amendment = AgreementAmendment(
            tenant_id=self.tenant_id,
            agreement_id=agreement_id,
            amendment_number=data.amendment_type.strip(),
            title=data.title.strip(),
            effective_date=data.new_effective_end_date or date.today(),
            change_summary=data.description.strip(),
            approved_by_user_id=current_user_id,
            document_url=data.document_reference_url,
        )
        self.db.add(amendment)

        if data.new_effective_end_date and data.new_effective_end_date > agreement.expiry_date:
            agreement.expiry_date = data.new_effective_end_date

        await self.db.flush()
        await self.db.refresh(amendment)
        return AgreementAmendmentResponse.model_validate(amendment)

    async def list_amendments(self, agreement_id: UUID) -> list[AgreementAmendmentResponse]:
        stmt = (
            select(AgreementAmendment)
            .where(
                and_(
                    AgreementAmendment.tenant_id == self.tenant_id,
                    AgreementAmendment.agreement_id == agreement_id,
                )
            )
            .order_by(AgreementAmendment.created_at.desc())
        )
        amendments = (await self.db.execute(stmt)).scalars().all()
        for a in amendments:
            await self.db.refresh(a)
        return [AgreementAmendmentResponse.model_validate(a) for a in amendments]

    # =========================================================================
    # 3. MOBILITY PROGRAMS & APPLICATION CYCLES
    # =========================================================================

    async def create_program(
        self, data: MobilityProgramCreate, current_user_id: UUID | None = None
    ) -> MobilityProgramResponse:
        partner = await self.db.get(InternationalPartner, data.partner_id)
        if not partner or partner.tenant_id != self.tenant_id:
            raise NotFoundException("Partner institution not found")

        if data.application_deadline < data.application_start_date:
            raise ValidationException("Application deadline must be on or after application start date")

        if data.expected_end_date <= data.expected_start_date:
            raise ValidationException("Expected program end date must be strictly after start date")

        program_code = data.program_code or f"PRG-{datetime.now(UTC).year}-{uuid4().hex[:6].upper()}"

        program = MobilityProgram(
            tenant_id=self.tenant_id,
            partner_id=data.partner_id,
            agreement_id=data.agreement_id,
            program_code=program_code,
            title=data.program_title.strip(),
            program_type=data.program_type.value if hasattr(data.program_type, "value") else str(data.program_type),
            direction=MobilityDirection.OUTBOUND.value,
            academic_term=str(data.term_type.value if hasattr(data.term_type, "value") else data.term_type),
            academic_year=data.academic_year.strip(),
            participating_departments=[str(d) for d in data.eligible_department_ids],
            eligible_programs=[str(p) for p in data.eligible_academic_program_ids],
            total_seats_quota=data.total_seats,
            min_cgpa_requirement=data.min_cgpa_requirement or 7.0,
            min_credits_requirement=data.min_credits_completed or 30,
            language_requirements=data.language_requirements or [],
            application_open_date=data.application_start_date,
            application_deadline=data.application_deadline,
            duration_weeks=max(1, ((data.expected_end_date - data.expected_start_date).days // 7)),
            academic_workload=None,
            required_documents=data.required_document_types,
            funding_scholarship_info=data.estimated_cost_notes,
            coordinator_user_id=data.coordinator_user_id or current_user_id,
            faculty_contact=None,
            status="PUBLISHED" if data.is_published else "DRAFT",
            instructions=data.instructions,
        )
        self.db.add(program)
        await self.db.flush()

        if program.is_published:
            await event_publisher.publish(
                db=self.db,
                tenant_id=self.tenant_id,
                event_type=DomainEventType.MOBILITY_PROGRAM_PUBLISHED,
                aggregate_type="MobilityProgram",
                aggregate_id=program.id,
                payload={
                    "program_id": str(program.id),
                    "program_code": program.program_code,
                    "title": program.title,
                },
            )
        return await self._format_program_response(program)

    async def _format_program_response(self, program: MobilityProgram) -> MobilityProgramResponse:
        await self.db.refresh(program)
        resp = MobilityProgramResponse.model_validate(program)
        if program.partner_id:
            partner = await self.db.get(InternationalPartner, program.partner_id)
            if partner:
                resp.partner_name = partner.name
                resp.partner_country = partner.country

        app_count = await self.db.scalar(
            select(func.count(MobilityApplication.id)).where(
                and_(
                    MobilityApplication.tenant_id == self.tenant_id,
                    MobilityApplication.program_id == program.id,
                    ~MobilityApplication.status.in_([MobilityApplicationStatus.WITHDRAWN.value, MobilityApplicationStatus.REJECTED.value]),
                )
            )
        )
        accepted_count = await self.db.scalar(
            select(func.count(MobilityApplication.id)).where(
                and_(
                    MobilityApplication.tenant_id == self.tenant_id,
                    MobilityApplication.program_id == program.id,
                    MobilityApplication.status.in_(
                        [
                            MobilityApplicationStatus.PARTNER_ACCEPTED.value,
                            MobilityApplicationStatus.PRE_DEPARTURE_PREPARATION.value,
                            MobilityApplicationStatus.ACTIVE_MOBILITY.value,
                            MobilityApplicationStatus.COMPLETED.value,
                        ]
                    ),
                )
            )
        )
        resp.active_applications_count = app_count or 0
        resp.accepted_students_count = accepted_count or 0
        return resp

    async def list_programs(
        self,
        is_published: bool | None = None,
        program_type: MobilityProgramType | None = None,
        partner_id: UUID | None = None,
        department_id: UUID | None = None,
        open_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MobilityProgramResponse]:
        query = select(MobilityProgram).where(MobilityProgram.tenant_id == self.tenant_id)
        if is_published is not None:
            status_val = "PUBLISHED" if is_published else "DRAFT"
            query = query.where(MobilityProgram.status == status_val)
        if program_type:
            pt_val = program_type.value if hasattr(program_type, "value") else str(program_type)
            query = query.where(MobilityProgram.program_type == pt_val)
        if partner_id:
            query = query.where(MobilityProgram.partner_id == partner_id)
        if open_only:
            today = date.today()
            query = query.where(
                and_(
                    MobilityProgram.status == "PUBLISHED",
                    MobilityProgram.application_open_date <= today,
                    MobilityProgram.application_deadline >= today,
                )
            )

        query = query.order_by(MobilityProgram.application_deadline.asc()).offset(offset).limit(limit)
        programs = (await self.db.execute(query)).scalars().all()

        results = []
        for p in programs:
            if department_id and p.participating_departments:
                if str(department_id) not in p.participating_departments:
                    continue
            results.append(await self._format_program_response(p))
        return results

    async def get_program(self, program_id: UUID) -> MobilityProgramResponse:
        stmt = select(MobilityProgram).where(
            and_(
                MobilityProgram.tenant_id == self.tenant_id,
                MobilityProgram.id == program_id,
            )
        )
        prog = (await self.db.execute(stmt)).scalar_one_or_none()
        if not prog:
            raise NotFoundException("Mobility program not found")
        return await self._format_program_response(prog)

    async def update_program(
        self, program_id: UUID, data: MobilityProgramUpdate, current_user_id: UUID | None = None
    ) -> MobilityProgramResponse:
        prog = await self.db.get(MobilityProgram, program_id)
        if not prog or prog.tenant_id != self.tenant_id:
            raise NotFoundException("Mobility program not found")

        was_published = prog.is_published
        if data.program_title:
            prog.title = data.program_title
        if data.is_published is not None:
            prog.status = "PUBLISHED" if data.is_published else "DRAFT"

        await self.db.flush()

        if not was_published and prog.is_published:
            await event_publisher.publish(
                db=self.db,
                tenant_id=self.tenant_id,
                event_type=DomainEventType.MOBILITY_PROGRAM_PUBLISHED,
                aggregate_type="MobilityProgram",
                aggregate_id=prog.id,
                payload={
                    "program_id": str(prog.id),
                    "program_code": prog.program_code,
                    "title": prog.title,
                },
            )
        return await self._format_program_response(prog)

    # =========================================================================
    # 4. STUDENT MOBILITY APPLICATIONS & REVIEWS
    # =========================================================================

    async def create_application(
        self, data: MobilityApplicationCreate, student_user_id: UUID
    ) -> MobilityApplicationResponse:
        program = await self.db.get(MobilityProgram, data.program_id)
        if not program or program.tenant_id != self.tenant_id:
            raise NotFoundException("Mobility program not found")

        if not program.is_published:
            raise ValidationException("This mobility program is not currently published for applications")

        today = date.today()
        if data.submit_now and today > program.application_deadline:
            raise ValidationException(f"Application deadline ({program.application_deadline}) has passed")

        # Resolve student profile
        profile_stmt = select(StudentProfile).where(
            and_(
                StudentProfile.tenant_id == self.tenant_id,
                or_(
                    StudentProfile.user_id == student_user_id,
                    StudentProfile.id == student_user_id,
                ),
            )
        )
        student_profile = (await self.db.execute(profile_stmt)).scalar_one_or_none()
        student_profile_id = student_profile.id if student_profile else student_user_id

        # Check existing active application for this program by this student
        existing_app_stmt = select(MobilityApplication).where(
            and_(
                MobilityApplication.tenant_id == self.tenant_id,
                MobilityApplication.program_id == program.id,
                MobilityApplication.student_id == student_profile_id,
                ~MobilityApplication.status.in_([MobilityApplicationStatus.WITHDRAWN.value, MobilityApplicationStatus.REJECTED.value]),
            )
        )
        existing = (await self.db.execute(existing_app_stmt)).scalar_one_or_none()
        if existing:
            raise ConflictException("You already have an active application for this mobility program")

        config = await self.get_or_create_config()
        cgpa = getattr(student_profile, "cgpa", None)
        if cgpa is None:
            cgpa = 8.0
        credits_completed = getattr(student_profile, "completed_credits", None)
        if credits_completed is None:
            credits_completed = 40

        eligibility_passed = True
        eligibility_details: dict[str, Any] = {}

        if program.min_cgpa_requirement and cgpa < program.min_cgpa_requirement:
            eligibility_passed = False
            eligibility_details["cgpa_error"] = f"CGPA ({cgpa}) below required minimum ({program.min_cgpa_requirement})"

        if program.min_credits_requirement and credits_completed < program.min_credits_requirement:
            eligibility_passed = False
            eligibility_details["credits_error"] = f"Credits ({credits_completed}) below required minimum"

        ref_no = f"MOB-APP-{datetime.now(UTC).year}-{uuid4().hex[:6].upper()}"

        initial_status = MobilityApplicationStatus.DRAFT
        if data.submit_now:
            if not eligibility_passed:
                initial_status = MobilityApplicationStatus.ELIGIBILITY_REVIEW
            elif config.require_department_approval_first:
                initial_status = MobilityApplicationStatus.DEPARTMENT_REVIEW
            else:
                initial_status = MobilityApplicationStatus.INTERNATIONAL_OFFICE_REVIEW

        application = MobilityApplication(
            tenant_id=self.tenant_id,
            application_number=ref_no,
            program_id=program.id,
            student_id=student_profile_id,
            academic_term=program.academic_term,
            status=initial_status.value,
            statement_of_purpose=data.statement_of_purpose.strip(),
            proposed_courses=data.proposed_courses,
            student_cgpa_snapshot=cgpa,
            credits_completed_snapshot=credits_completed,
            eligibility_check_passed=eligibility_passed,
            eligibility_exception_waived=False,
        )
        application.eligibility_check_details = eligibility_details
        self.db.add(application)
        await self.db.flush()

        if data.submit_now:
            review_entry = ApplicationReviewHistory(
                tenant_id=self.tenant_id,
                application_id=application.id,
                stage="SUBMISSION",
                action="SUBMIT",
                reviewer_user_id=student_user_id,
                reviewer_role="STUDENT",
                comments="Initial application submission by student",
            )
            self.db.add(review_entry)
            await self.db.flush()

            await event_publisher.publish(
                db=self.db,
                tenant_id=self.tenant_id,
                event_type=DomainEventType.MOBILITY_APPLICATION_SUBMITTED,
                aggregate_type="MobilityApplication",
                aggregate_id=application.id,
                payload={
                    "application_id": str(application.id),
                    "reference_number": application.application_number,
                    "student_id": str(student_profile_id),
                },
            )

        return await self._format_application_response(application)

    async def _format_application_response(self, app: MobilityApplication) -> MobilityApplicationResponse:
        details = getattr(app, "_eligibility_check_details", None)
        await self.db.refresh(app)
        resp = MobilityApplicationResponse.model_validate(app)
        if details:
            resp.eligibility_check_details = details
        elif not app.eligibility_check_passed and app.program_id:
            prog = await self.db.get(MobilityProgram, app.program_id)
            errs: dict[str, Any] = {}
            if prog and prog.min_cgpa_requirement and app.student_cgpa_snapshot and app.student_cgpa_snapshot < prog.min_cgpa_requirement:
                errs["cgpa_error"] = f"CGPA ({app.student_cgpa_snapshot}) below required minimum ({prog.min_cgpa_requirement})"
            if prog and prog.min_credits_requirement and app.credits_completed_snapshot and app.credits_completed_snapshot < prog.min_credits_requirement:
                errs["credits_error"] = f"Credits ({app.credits_completed_snapshot}) below required minimum"
            resp.eligibility_check_details = errs
        if app.program_id:
            prog = await self.db.get(MobilityProgram, app.program_id)
            if prog:
                resp.program_title = prog.title
                if prog.partner_id:
                    partner = await self.db.get(InternationalPartner, prog.partner_id)
                    if partner:
                        resp.partner_name = partner.name
                        resp.partner_country = partner.country

        profile = await self.db.get(StudentProfile, app.student_id)
        if profile:
            resp.student_roll_number = getattr(profile, "roll_number", None)
            if profile.user_id:
                user = await self.db.get(User, profile.user_id)
                if user:
                    resp.student_name = getattr(user, "full_name", None) or getattr(user, "email", "Student")

        return resp

    async def list_applications(
        self,
        student_id: UUID | None = None,
        program_id: UUID | None = None,
        status: MobilityApplicationStatus | None = None,
        department_pending: bool = False,
        intl_office_pending: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MobilityApplicationResponse]:
        query = select(MobilityApplication).where(MobilityApplication.tenant_id == self.tenant_id)
        if student_id:
            query = query.where(MobilityApplication.student_id == student_id)
        if program_id:
            query = query.where(MobilityApplication.program_id == program_id)
        if status:
            s_val = status.value if hasattr(status, "value") else str(status)
            query = query.where(MobilityApplication.status == s_val)
        if department_pending:
            query = query.where(MobilityApplication.status == MobilityApplicationStatus.DEPARTMENT_REVIEW.value)
        if intl_office_pending:
            query = query.where(MobilityApplication.status == MobilityApplicationStatus.INTERNATIONAL_OFFICE_REVIEW.value)

        query = query.order_by(MobilityApplication.created_at.desc()).offset(offset).limit(limit)
        apps = (await self.db.execute(query)).scalars().all()
        return [await self._format_application_response(a) for a in apps]

    async def get_application(self, application_id: UUID) -> MobilityApplicationResponse:
        stmt = select(MobilityApplication).where(
            and_(
                MobilityApplication.tenant_id == self.tenant_id,
                MobilityApplication.id == application_id,
            )
        )
        app = (await self.db.execute(stmt)).scalar_one_or_none()
        if not app:
            raise NotFoundException("Mobility application not found")
        return await self._format_application_response(app)

    async def review_application(
        self,
        application_id: UUID,
        data: MobilityApplicationReviewRequest,
        reviewer_user_id: UUID,
        reviewer_role: str,
    ) -> MobilityApplicationResponse:
        app = await self.db.get(MobilityApplication, application_id)
        if not app or app.tenant_id != self.tenant_id:
            raise NotFoundException("Mobility application not found")

        current_stage = (
            "DEPARTMENT_REVIEW"
            if app.status == MobilityApplicationStatus.DEPARTMENT_REVIEW.value
            else "INTERNATIONAL_OFFICE_REVIEW"
        )

        if data.action == "APPROVE":
            if app.status == MobilityApplicationStatus.DEPARTMENT_REVIEW.value:
                app.department_decision = "APPROVED"
                app.department_comments = data.comments
                app.status = MobilityApplicationStatus.INTERNATIONAL_OFFICE_REVIEW.value
            elif app.status in [
                MobilityApplicationStatus.INTERNATIONAL_OFFICE_REVIEW.value,
                MobilityApplicationStatus.ELIGIBILITY_REVIEW.value,
            ]:
                app.intl_office_decision = "APPROVED"
                app.intl_office_comments = data.comments
                app.status = MobilityApplicationStatus.APPROVED.value
        elif data.action == "REJECT":
            app.status = MobilityApplicationStatus.REJECTED.value
            if current_stage == "DEPARTMENT_REVIEW":
                app.department_decision = "REJECTED"
                app.department_comments = data.comments
            else:
                app.intl_office_decision = "REJECTED"
                app.intl_office_comments = data.comments
        elif data.action == "RETURN":
            app.status = MobilityApplicationStatus.DRAFT.value
        elif data.action == "ESCALATE":
            app.status = MobilityApplicationStatus.ON_HOLD.value

        history = ApplicationReviewHistory(
            tenant_id=self.tenant_id,
            application_id=app.id,
            stage=current_stage,
            action=data.action,
            reviewer_user_id=reviewer_user_id,
            reviewer_role=reviewer_role,
            comments=data.comments,
        )
        self.db.add(history)
        await self.db.flush()

        await event_publisher.publish(
            db=self.db,
            tenant_id=self.tenant_id,
            event_type=DomainEventType.MOBILITY_APPLICATION_REVIEWED,
            aggregate_type="MobilityApplication",
            aggregate_id=app.id,
            payload={
                "application_id": str(app.id),
                "action": data.action,
                "new_status": app.status,
            },
        )
        return await self._format_application_response(app)

    async def nominate_to_partner(
        self, application_id: UUID, data: PartnerNominationRequest, current_user_id: UUID
    ) -> MobilityApplicationResponse:
        app = await self.db.get(MobilityApplication, application_id)
        if not app or app.tenant_id != self.tenant_id:
            raise NotFoundException("Mobility application not found")

        if app.status != MobilityApplicationStatus.APPROVED.value:
            raise ValidationException("Only applications approved by International Office can be nominated to partners")

        app.status = MobilityApplicationStatus.PARTNER_NOMINATED.value
        app.nomination_date = date.today()

        history = ApplicationReviewHistory(
            tenant_id=self.tenant_id,
            application_id=app.id,
            stage="PARTNER_NOMINATION",
            action="NOMINATE",
            reviewer_user_id=current_user_id,
            reviewer_role="INTERNATIONAL_OFFICE",
            comments=data.nomination_notes or "Nominated to partner institution",
        )
        self.db.add(history)
        await self.db.flush()

        await event_publisher.publish(
            db=self.db,
            tenant_id=self.tenant_id,
            event_type=DomainEventType.MOBILITY_APPLICATION_NOMINATED,
            aggregate_type="MobilityApplication",
            aggregate_id=app.id,
            payload={"application_id": str(app.id)},
        )
        return await self._format_application_response(app)

    async def record_partner_decision(
        self, application_id: UUID, data: PartnerDecisionRequest, current_user_id: UUID
    ) -> MobilityApplicationResponse:
        app = await self.db.get(MobilityApplication, application_id)
        if not app or app.tenant_id != self.tenant_id:
            raise NotFoundException("Mobility application not found")

        if app.status != MobilityApplicationStatus.PARTNER_NOMINATED.value:
            raise ValidationException("Application must be in nominated status to record partner decision")

        if data.decision == "ACCEPTED":
            app.status = MobilityApplicationStatus.PARTNER_ACCEPTED.value
        else:
            app.status = MobilityApplicationStatus.PARTNER_REJECTED.value

        app.partner_decision = data.decision
        app.partner_decision_date = date.today()
        app.partner_decision_notes = data.official_response_notes

        history = ApplicationReviewHistory(
            tenant_id=self.tenant_id,
            application_id=app.id,
            stage="PARTNER_DECISION",
            action=data.decision,
            reviewer_user_id=current_user_id,
            reviewer_role="INTERNATIONAL_OFFICE",
            comments=data.official_response_notes or f"Partner decision recorded: {data.decision}",
        )
        self.db.add(history)
        await self.db.flush()

        await event_publisher.publish(
            db=self.db,
            tenant_id=self.tenant_id,
            event_type=DomainEventType.MOBILITY_PARTNER_DECISION_RECORDED,
            aggregate_type="MobilityApplication",
            aggregate_id=app.id,
            payload={"application_id": str(app.id), "decision": data.decision},
        )
        return await self._format_application_response(app)

    async def update_pre_departure(
        self, application_id: UUID, data: PreDepartureUpdateRequest
    ) -> MobilityApplicationResponse:
        app = await self.db.get(MobilityApplication, application_id)
        if not app or app.tenant_id != self.tenant_id:
            raise NotFoundException("Mobility application not found")

        app.pre_departure_checklist = data.pre_departure_checklist
        app.visa_reference_number = data.visa_reference_number
        app.travel_itinerary = data.travel_itinerary
        app.insurance_policy_number = data.insurance_policy_number

        if app.status == MobilityApplicationStatus.PARTNER_ACCEPTED.value:
            app.status = MobilityApplicationStatus.PRE_DEPARTURE_PREPARATION.value

        await self.db.flush()
        return await self._format_application_response(app)

    async def transition_mobility_state(
        self, application_id: UUID, target_status: MobilityApplicationStatus
    ) -> MobilityApplicationResponse:
        app = await self.db.get(MobilityApplication, application_id)
        if not app or app.tenant_id != self.tenant_id:
            raise NotFoundException("Mobility application not found")

        app.status = target_status.value if hasattr(target_status, "value") else str(target_status)
        await self.db.flush()
        return await self._format_application_response(app)

    # =========================================================================
    # 5. INBOUND INTERNATIONAL STUDENTS
    # =========================================================================

    async def create_inbound_student(
        self, data: InboundStudentCreate, current_user_id: UUID | None = None
    ) -> InboundStudentResponse:
        partner = await self.db.get(InternationalPartner, data.partner_id)
        if not partner or partner.tenant_id != self.tenant_id:
            raise NotFoundException("Partner institution not found")

        student = InboundStudentProfile(
            tenant_id=self.tenant_id,
            partner_id=data.partner_id,
            student_name=f"{data.student_first_name} {data.student_last_name}".strip(),
            student_email=data.email.strip().lower(),
            nationality=data.country_of_citizenship.strip(),
            passport_reference=None,
            home_institution_student_id=data.home_institution_name.strip(),
            host_department_id=data.host_department_id,
            host_program_id=data.host_academic_program_id,
            study_period_start=data.expected_start_date,
            study_period_end=data.expected_end_date,
            academic_term=data.study_period_terms.strip(),
            orientation_completed=False,
            campus_card_issued=False,
            accommodation_status="REQUESTED" if data.accommodation_reference else "NOT_REQUIRED",
            accommodation_reference=data.accommodation_reference,
            assigned_coordinator_user_id=data.assigned_mentor_user_id,
            check_in_status="PENDING",
        )
        self.db.add(student)
        await self.db.flush()
        return await self._format_inbound_response(student)

    async def _format_inbound_response(self, student: InboundStudentProfile) -> InboundStudentResponse:
        await self.db.refresh(student)
        resp = InboundStudentResponse.model_validate(student)
        if student.partner_id:
            partner = await self.db.get(InternationalPartner, student.partner_id)
            if partner:
                resp.partner_name = partner.name
        if student.assigned_coordinator_user_id:
            mentor = await self.db.get(User, student.assigned_coordinator_user_id)
            if mentor:
                resp.assigned_mentor_name = getattr(mentor, "full_name", None) or getattr(mentor, "email", "Faculty")
        return resp

    async def list_inbound_students(
        self,
        partner_id: UUID | None = None,
        status: InboundStudentStatus | None = None,
        orientation_pending: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[InboundStudentResponse]:
        query = select(InboundStudentProfile).where(InboundStudentProfile.tenant_id == self.tenant_id)
        if partner_id:
            query = query.where(InboundStudentProfile.partner_id == partner_id)
        if status:
            s_val = status.value if hasattr(status, "value") else str(status)
            query = query.where(InboundStudentProfile.check_in_status == s_val)
        if orientation_pending:
            query = query.where(InboundStudentProfile.orientation_completed.is_(False))

        query = query.order_by(InboundStudentProfile.study_period_start.asc()).offset(offset).limit(limit)
        students = (await self.db.execute(query)).scalars().all()
        return [await self._format_inbound_response(s) for s in students]

    async def get_inbound_student(self, inbound_id: UUID) -> InboundStudentResponse:
        stmt = select(InboundStudentProfile).where(
            and_(
                InboundStudentProfile.tenant_id == self.tenant_id,
                InboundStudentProfile.id == inbound_id,
            )
        )
        student = (await self.db.execute(stmt)).scalar_one_or_none()
        if not student:
            raise NotFoundException("Inbound international student not found")
        return await self._format_inbound_response(student)

    async def checkin_inbound_student(
        self, inbound_id: UUID, data: InboundOrientationCheckinRequest
    ) -> InboundStudentResponse:
        student = await self.db.get(InboundStudentProfile, inbound_id)
        if not student or student.tenant_id != self.tenant_id:
            raise NotFoundException("Inbound international student not found")

        student.check_in_date = data.check_in_date
        student.orientation_completed = data.orientation_completed
        student.check_in_status = "ACTIVE_STUDY"
        await self.db.flush()

        await event_publisher.publish(
            db=self.db,
            tenant_id=self.tenant_id,
            event_type=DomainEventType.INBOUND_STUDENT_CHECKED_IN,
            aggregate_type="InboundStudentProfile",
            aggregate_id=student.id,
            payload={"inbound_id": str(student.id)},
        )
        return await self._format_inbound_response(student)

    # =========================================================================
    # 6. FACULTY MOBILITY & VISITING SCHOLARS
    # =========================================================================

    async def create_faculty_mobility(
        self, data: FacultyMobilityCreate, current_user_id: UUID
    ) -> FacultyMobilityResponse:
        partner = await self.db.get(InternationalPartner, data.partner_id)
        if not partner or partner.tenant_id != self.tenant_id:
            raise NotFoundException("Partner institution not found")

        record = FacultyMobilityRecord(
            tenant_id=self.tenant_id,
            staff_user_id=data.faculty_user_id or current_user_id,
            scholar_name=data.visiting_scholar_name or "Faculty Scholar",
            scholar_email=data.visiting_scholar_email or "scholar@partner.edu",
            mobility_type=data.direction.value if hasattr(data.direction, "value") else str(data.direction),
            partner_id=data.partner_id,
            home_institution_name=data.home_institution_name or "Home Institution",
            host_department_id=data.department_id,
            visit_start_date=data.visit_start_date,
            visit_end_date=data.visit_end_date,
            objectives=data.visit_objectives.strip(),
            academic_visit_plan=data.academic_visit_plan,
            status=FacultyMobilityStatus.SUBMITTED.value,
        )
        self.db.add(record)
        await self.db.flush()
        return await self._format_faculty_mobility_response(record)

    async def _format_faculty_mobility_response(self, rec: FacultyMobilityRecord) -> FacultyMobilityResponse:
        await self.db.refresh(rec)
        resp = FacultyMobilityResponse.model_validate(rec)
        if rec.partner_id:
            partner = await self.db.get(InternationalPartner, rec.partner_id)
            if partner:
                resp.partner_name = partner.name
        if rec.staff_user_id:
            faculty = await self.db.get(User, rec.staff_user_id)
            if faculty:
                resp.faculty_name = getattr(faculty, "full_name", None) or getattr(faculty, "email", "Faculty")
        return resp

    async def list_faculty_mobilities(
        self,
        direction: FacultyMobilityDirection | None = None,
        partner_id: UUID | None = None,
        status: FacultyMobilityStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FacultyMobilityResponse]:
        query = select(FacultyMobilityRecord).where(FacultyMobilityRecord.tenant_id == self.tenant_id)
        if direction:
            d_val = direction.value if hasattr(direction, "value") else str(direction)
            query = query.where(FacultyMobilityRecord.mobility_type == d_val)
        if partner_id:
            query = query.where(FacultyMobilityRecord.partner_id == partner_id)
        if status:
            st_val = status.value if hasattr(status, "value") else str(status)
            query = query.where(FacultyMobilityRecord.status == st_val)

        query = query.order_by(FacultyMobilityRecord.visit_start_date.asc()).offset(offset).limit(limit)
        records = (await self.db.execute(query)).scalars().all()
        return [await self._format_faculty_mobility_response(r) for r in records]

    async def get_faculty_mobility(self, mobility_id: UUID) -> FacultyMobilityResponse:
        stmt = select(FacultyMobilityRecord).where(
            and_(
                FacultyMobilityRecord.tenant_id == self.tenant_id,
                FacultyMobilityRecord.id == mobility_id,
            )
        )
        record = (await self.db.execute(stmt)).scalar_one_or_none()
        if not record:
            raise NotFoundException("Faculty mobility record not found")
        return await self._format_faculty_mobility_response(record)

    async def approve_faculty_mobility(
        self,
        mobility_id: UUID,
        data: FacultyMobilityApprovalRequest,
        reviewer_user_id: UUID,
        role: str,
    ) -> FacultyMobilityResponse:
        rec = await self.db.get(FacultyMobilityRecord, mobility_id)
        if not rec or rec.tenant_id != self.tenant_id:
            raise NotFoundException("Faculty mobility record not found")

        if data.decision == "REJECTED":
            rec.status = FacultyMobilityStatus.REJECTED.value
        else:
            if "HOD" in role.upper():
                rec.hod_user_id = reviewer_user_id
                config = await self.get_or_create_config()
                if config.require_vp_approval:
                    rec.status = FacultyMobilityStatus.VP_REVIEW.value
                else:
                    rec.status = FacultyMobilityStatus.APPROVED.value
            elif "VP" in role.upper() or "VICE_PRINCIPAL" in role.upper() or "ADMIN" in role.upper():
                rec.vp_user_id = reviewer_user_id
                rec.status = FacultyMobilityStatus.APPROVED.value

        await self.db.flush()

        if rec.status == FacultyMobilityStatus.APPROVED.value:
            await event_publisher.publish(
                db=self.db,
                tenant_id=self.tenant_id,
                event_type=DomainEventType.FACULTY_MOBILITY_APPROVED,
                aggregate_type="FacultyMobilityRecord",
                aggregate_id=rec.id,
                payload={"mobility_id": str(rec.id)},
            )
        return await self._format_faculty_mobility_response(rec)

    # =========================================================================
    # 7. ACADEMIC CREDIT EQUIVALENCY & TRANSFERS
    # =========================================================================

    async def create_course_equivalency(
        self, data: CourseEquivalencyCreate, current_user_id: UUID | None = None
    ) -> CourseEquivalencyResponse:
        partner = await self.db.get(InternationalPartner, data.partner_id)
        if not partner or partner.tenant_id != self.tenant_id:
            raise NotFoundException("Partner institution not found")

        mapping = CourseEquivalencyMapping(
            tenant_id=self.tenant_id,
            partner_id=data.partner_id,
            partner_course_code=data.host_course_code.strip(),
            partner_course_title=data.host_course_title.strip(),
            partner_credits=data.host_course_credits,
            grading_scale_info=data.host_grading_scale,
            syllabus_document_url=data.host_syllabus_reference,
            learning_outcomes=data.learning_outcomes_comparison,
            campus_program_id=data.campus_academic_program_id,
            campus_course_code=data.campus_course_code or "GEN-COURSE",
            campus_course_title=data.campus_course_title or "General Course Title",
            campus_credits=data.campus_course_credits or 4.0,
            department_id=data.department_id,
            status=CreditEquivalencyStatus.PROPOSED.value,
            effective_academic_year="2026-2027",
        )
        self.db.add(mapping)
        await self.db.flush()
        return await self._format_equivalency_response(mapping)

    async def _format_equivalency_response(self, m: CourseEquivalencyMapping) -> CourseEquivalencyResponse:
        await self.db.refresh(m)
        resp = CourseEquivalencyResponse.model_validate(m)
        if m.partner_id:
            partner = await self.db.get(InternationalPartner, m.partner_id)
            if partner:
                resp.partner_name = partner.name
        if m.reviewer_user_id:
            user = await self.db.get(User, m.reviewer_user_id)
            if user:
                resp.evaluator_name = getattr(user, "full_name", None) or getattr(user, "email", "Faculty")
        return resp

    async def list_course_equivalencies(
        self,
        partner_id: UUID | None = None,
        department_id: UUID | None = None,
        status: CreditEquivalencyStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CourseEquivalencyResponse]:
        query = select(CourseEquivalencyMapping).where(CourseEquivalencyMapping.tenant_id == self.tenant_id)
        if partner_id:
            query = query.where(CourseEquivalencyMapping.partner_id == partner_id)
        if department_id:
            query = query.where(CourseEquivalencyMapping.department_id == department_id)
        if status:
            s_val = status.value if hasattr(status, "value") else str(status)
            query = query.where(CourseEquivalencyMapping.status == s_val)

        query = query.order_by(CourseEquivalencyMapping.created_at.desc()).offset(offset).limit(limit)
        mappings = (await self.db.execute(query)).scalars().all()
        return [await self._format_equivalency_response(m) for m in mappings]

    async def evaluate_course_equivalency(
        self,
        mapping_id: UUID,
        data: CourseEquivalencyEvaluationRequest,
        evaluator_user_id: UUID,
    ) -> CourseEquivalencyResponse:
        mapping = await self.db.get(CourseEquivalencyMapping, mapping_id)
        if not mapping or mapping.tenant_id != self.tenant_id:
            raise NotFoundException("Course equivalency mapping not found")

        mapping.status = data.status.value if hasattr(data.status, "value") else str(data.status)
        mapping.reviewer_user_id = evaluator_user_id
        mapping.committee_notes = data.evaluator_comments
        mapping.conditions = data.conditions
        await self.db.flush()
        return await self._format_equivalency_response(mapping)

    async def request_credit_transfer(
        self, data: CreditTransferRequestCreate, student_user_id: UUID
    ) -> CreditTransferResponse:
        app = await self.db.get(MobilityApplication, data.application_id)
        if not app or app.tenant_id != self.tenant_id:
            raise NotFoundException("Mobility application not found")

        profile_stmt = select(StudentProfile).where(
            and_(
                StudentProfile.tenant_id == self.tenant_id,
                or_(
                    StudentProfile.user_id == student_user_id,
                    StudentProfile.id == student_user_id,
                ),
            )
        )
        student_profile = (await self.db.execute(profile_stmt)).scalar_one_or_none()
        student_profile_id = student_profile.id if student_profile else student_user_id

        transfer = StudentCreditTransferRequest(
            tenant_id=self.tenant_id,
            application_id=data.application_id,
            student_id=student_profile_id,
            host_transcript_doc_url=data.transcript_document_url.strip(),
            status=CreditTransferStatus.SUBMITTED.value,
            mapped_courses_summary=[
                {
                    "host_course_code": data.host_course_code,
                    "host_course_title": data.host_course_title,
                    "host_grade": data.host_grade_received,
                    "host_credits": data.host_credits_earned,
                }
            ],
            total_credits_requested=data.host_credits_earned,
            total_credits_approved=data.target_campus_credits or 0.0,
        )
        self.db.add(transfer)
        await self.db.flush()
        return await self._format_credit_transfer_response(transfer)

    async def _format_credit_transfer_response(self, ct: StudentCreditTransferRequest) -> CreditTransferResponse:
        await self.db.refresh(ct)
        resp = CreditTransferResponse.model_validate(ct)
        profile = await self.db.get(StudentProfile, ct.student_id)
        if profile and profile.user_id:
            user = await self.db.get(User, profile.user_id)
            if user:
                resp.student_name = getattr(user, "full_name", None) or getattr(user, "email", "Student")
        return resp

    async def list_credit_transfers(
        self,
        student_id: UUID | None = None,
        application_id: UUID | None = None,
        status: CreditTransferStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CreditTransferResponse]:
        query = select(StudentCreditTransferRequest).where(StudentCreditTransferRequest.tenant_id == self.tenant_id)
        if student_id:
            query = query.where(StudentCreditTransferRequest.student_id == student_id)
        if application_id:
            query = query.where(StudentCreditTransferRequest.application_id == application_id)
        if status:
            s_val = status.value if hasattr(status, "value") else str(status)
            query = query.where(StudentCreditTransferRequest.status == s_val)

        query = query.order_by(StudentCreditTransferRequest.created_at.desc()).offset(offset).limit(limit)
        items = (await self.db.execute(query)).scalars().all()
        return [await self._format_credit_transfer_response(i) for i in items]

    async def review_credit_transfer(
        self,
        transfer_id: UUID,
        data: CreditTransferApprovalRequest,
        reviewer_user_id: UUID,
    ) -> CreditTransferResponse:
        ct = await self.db.get(StudentCreditTransferRequest, transfer_id)
        if not ct or ct.tenant_id != self.tenant_id:
            raise NotFoundException("Credit transfer request not found")

        ct.status = data.status.value if hasattr(data.status, "value") else str(data.status)
        ct.authorized_by_user_id = reviewer_user_id
        ct.authorized_date = date.today()
        ct.notes = data.committee_resolution_notes
        if data.approved_credits is not None:
            ct.total_credits_approved = data.approved_credits

        await self.db.flush()

        if ct.status in [CreditTransferStatus.COMMITTEE_APPROVED.value, CreditTransferStatus.CREDITS_POSTED.value]:
            await event_publisher.publish(
                db=self.db,
                tenant_id=self.tenant_id,
                event_type=DomainEventType.CREDIT_TRANSFER_APPROVED,
                aggregate_type="StudentCreditTransferRequest",
                aggregate_id=ct.id,
                payload={"transfer_id": str(ct.id)},
            )
        return await self._format_credit_transfer_response(ct)

    # =========================================================================
    # 8. MOBILITY DOCUMENTS
    # =========================================================================

    async def create_document(
        self, data: MobilityDocumentCreate, current_user_id: UUID | None = None
    ) -> MobilityDocumentResponse:
        doc = MobilityDocument(
            tenant_id=self.tenant_id,
            application_id=data.application_id,
            inbound_student_id=data.inbound_student_id,
            faculty_mobility_id=data.faculty_mobility_id,
            document_type=data.document_type.value if hasattr(data.document_type, "value") else str(data.document_type),
            title=data.document_name.strip(),
            file_url=data.file_storage_url.strip(),
            file_size_bytes=data.file_size_bytes,
            mime_type=data.file_mime_type,
            submission_date=date.today(),
            expiry_date=data.document_expiry_date,
            verification_status=DocumentVerificationStatus.PENDING.value,
        )
        self.db.add(doc)
        await self.db.flush()
        await self.db.refresh(doc)
        return MobilityDocumentResponse.model_validate(doc)

    async def list_documents(
        self,
        application_id: UUID | None = None,
        inbound_student_id: UUID | None = None,
        faculty_mobility_id: UUID | None = None,
        verification_status: MobilityDocumentVerificationStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MobilityDocumentResponse]:
        query = select(MobilityDocument).where(MobilityDocument.tenant_id == self.tenant_id)
        if application_id:
            query = query.where(MobilityDocument.application_id == application_id)
        if inbound_student_id:
            query = query.where(MobilityDocument.inbound_student_id == inbound_student_id)
        if faculty_mobility_id:
            query = query.where(MobilityDocument.faculty_mobility_id == faculty_mobility_id)
        if verification_status:
            v_val = verification_status.value if hasattr(verification_status, "value") else str(verification_status)
            query = query.where(MobilityDocument.verification_status == v_val)

        query = query.order_by(MobilityDocument.created_at.desc()).offset(offset).limit(limit)
        docs = (await self.db.execute(query)).scalars().all()
        for d in docs:
            await self.db.refresh(d)
        return [MobilityDocumentResponse.model_validate(d) for d in docs]

    async def verify_document(
        self,
        document_id: UUID,
        data: MobilityDocumentVerifyRequest,
        reviewer_user_id: UUID,
    ) -> MobilityDocumentResponse:
        doc = await self.db.get(MobilityDocument, document_id)
        if not doc or doc.tenant_id != self.tenant_id:
            raise NotFoundException("Mobility document not found")

        doc.verification_status = data.status.value if hasattr(data.status, "value") else str(data.status)
        doc.verified_by_user_id = reviewer_user_id
        doc.verified_at = datetime.now(UTC)
        doc.verification_notes = data.rejection_reason
        await self.db.flush()
        await self.db.refresh(doc)

        if doc.verification_status == DocumentVerificationStatus.VERIFIED.value:
            await event_publisher.publish(
                db=self.db,
                tenant_id=self.tenant_id,
                event_type=DomainEventType.MOBILITY_DOCUMENT_VERIFIED,
                aggregate_type="MobilityDocument",
                aggregate_id=doc.id,
                payload={"document_id": str(doc.id)},
            )
        return MobilityDocumentResponse.model_validate(doc)

    # =========================================================================
    # 9. SCHOLARSHIPS & MOBILITY FUNDING
    # =========================================================================

    async def create_scholarship(
        self, data: MobilityScholarshipCreate, current_user_id: UUID | None = None
    ) -> MobilityScholarshipResponse:
        code = data.scholarship_code or f"SCH-{datetime.now(UTC).year}-{uuid4().hex[:6].upper()}"

        scholarship = MobilityScholarship(
            tenant_id=self.tenant_id,
            code=code,
            title=data.scholarship_name.strip(),
            sponsor_organization=data.funding_source.strip(),
            award_amount=data.award_amount_per_student,
            currency="USD",
            eligibility_criteria=data.eligibility_criteria_notes or "General Eligibility",
            application_deadline=data.application_deadline or (date.today() + timedelta(days=90)),
            total_quota_seats=data.total_available_slots,
            status="ACTIVE" if data.is_active else "INACTIVE",
        )
        self.db.add(scholarship)
        await self.db.flush()
        await self.db.refresh(scholarship)
        return MobilityScholarshipResponse.model_validate(scholarship)

    async def list_scholarships(
        self, is_active: bool | None = None, limit: int = 50, offset: int = 0
    ) -> list[MobilityScholarshipResponse]:
        query = select(MobilityScholarship).where(MobilityScholarship.tenant_id == self.tenant_id)
        if is_active is not None:
            expected_status = "ACTIVE" if is_active else "INACTIVE"
            query = query.where(MobilityScholarship.status == expected_status)

        query = query.order_by(MobilityScholarship.title.asc()).offset(offset).limit(limit)
        scholarships = (await self.db.execute(query)).scalars().all()
        for s in scholarships:
            await self.db.refresh(s)
        return [MobilityScholarshipResponse.model_validate(s) for s in scholarships]

    async def create_funding_request(
        self, data: MobilityFundingRequestCreate, student_user_id: UUID
    ) -> MobilityFundingRequestResponse:
        app = await self.db.get(MobilityApplication, data.application_id)
        if not app or app.tenant_id != self.tenant_id:
            raise NotFoundException("Mobility application not found")

        profile_stmt = select(StudentProfile).where(
            and_(
                StudentProfile.tenant_id == self.tenant_id,
                or_(
                    StudentProfile.user_id == student_user_id,
                    StudentProfile.id == student_user_id,
                ),
            )
        )
        student_profile = (await self.db.execute(profile_stmt)).scalar_one_or_none()
        student_profile_id = student_profile.id if student_profile else student_user_id

        req = MobilityFundingRequest(
            tenant_id=self.tenant_id,
            application_id=data.application_id,
            student_id=student_profile_id,
            scholarship_id=data.scholarship_id,
            funding_type="SCHOLARSHIP",
            requested_amount=data.requested_amount,
            currency="USD",
            status=FundingStatus.REQUESTED.value,
            notes=data.justification.strip(),
        )
        self.db.add(req)
        await self.db.flush()
        return await self._format_funding_response(req)

    async def _format_funding_response(self, req: MobilityFundingRequest) -> MobilityFundingRequestResponse:
        await self.db.refresh(req)
        resp = MobilityFundingRequestResponse.model_validate(req)
        profile = await self.db.get(StudentProfile, req.student_id)
        if profile and profile.user_id:
            user = await self.db.get(User, profile.user_id)
            if user:
                resp.student_name = getattr(user, "full_name", None) or getattr(user, "email", "Student")
        if req.scholarship_id:
            sch = await self.db.get(MobilityScholarship, req.scholarship_id)
            if sch:
                resp.scholarship_name = sch.title
        return resp

    async def list_funding_requests(
        self,
        application_id: UUID | None = None,
        status: MobilityFundingStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MobilityFundingRequestResponse]:
        query = select(MobilityFundingRequest).where(MobilityFundingRequest.tenant_id == self.tenant_id)
        if application_id:
            query = query.where(MobilityFundingRequest.application_id == application_id)
        if status:
            s_val = status.value if hasattr(status, "value") else str(status)
            query = query.where(MobilityFundingRequest.status == s_val)

        query = query.order_by(MobilityFundingRequest.created_at.desc()).offset(offset).limit(limit)
        items = (await self.db.execute(query)).scalars().all()
        return [await self._format_funding_response(i) for i in items]

    async def approve_funding_request(
        self,
        request_id: UUID,
        data: MobilityFundingApprovalRequest,
        reviewer_user_id: UUID,
    ) -> MobilityFundingRequestResponse:
        req = await self.db.get(MobilityFundingRequest, request_id)
        if not req or req.tenant_id != self.tenant_id:
            raise NotFoundException("Mobility funding request not found")

        req.status = data.status.value if hasattr(data.status, "value") else str(data.status)
        req.approved_amount = data.approved_amount or req.requested_amount
        req.approved_by_user_id = reviewer_user_id
        if data.finance_reference_id:
            req.finance_disbursement_ref = str(data.finance_reference_id)

        await self.db.flush()

        if req.status == FundingStatus.APPROVED.value:
            await event_publisher.publish(
                db=self.db,
                tenant_id=self.tenant_id,
                event_type=DomainEventType.MOBILITY_FUNDING_APPROVED,
                aggregate_type="MobilityFundingRequest",
                aggregate_id=req.id,
                payload={"request_id": str(req.id), "amount": req.approved_amount},
            )
        return await self._format_funding_response(req)

    # =========================================================================
    # 10. TELEMETRY & DASHBOARD METRICS
    # =========================================================================

    async def get_dashboard_metrics(self) -> InternationalDashboardMetrics:
        today = date.today()
        config = await self.get_or_create_config()
        warning_days = config.agreement_renewal_notice_days or 90

        active_partners = await self.db.scalar(
            select(func.count(InternationalPartner.id)).where(
                and_(
                    InternationalPartner.tenant_id == self.tenant_id,
                    InternationalPartner.status == "ACTIVE",
                )
            )
        )
        active_agreements = await self.db.scalar(
            select(func.count(InstitutionalAgreement.id)).where(
                and_(
                    InstitutionalAgreement.tenant_id == self.tenant_id,
                    InstitutionalAgreement.status.in_([AgreementStatus.ACTIVE.value, AgreementStatus.EXPIRING.value]),
                )
            )
        )
        expiring_agreements = await self.db.scalar(
            select(func.count(InstitutionalAgreement.id)).where(
                and_(
                    InstitutionalAgreement.tenant_id == self.tenant_id,
                    InstitutionalAgreement.status.in_([AgreementStatus.ACTIVE.value, AgreementStatus.EXPIRING.value]),
                    InstitutionalAgreement.expiry_date <= today + timedelta(days=warning_days),
                    InstitutionalAgreement.expiry_date >= today,
                )
            )
        )
        published_programs = await self.db.scalar(
            select(func.count(MobilityProgram.id)).where(
                and_(
                    MobilityProgram.tenant_id == self.tenant_id,
                    MobilityProgram.status == "PUBLISHED",
                )
            )
        )
        active_apps = await self.db.scalar(
            select(func.count(MobilityApplication.id)).where(
                and_(
                    MobilityApplication.tenant_id == self.tenant_id,
                    ~MobilityApplication.status.in_([MobilityApplicationStatus.WITHDRAWN.value, MobilityApplicationStatus.REJECTED.value]),
                )
            )
        )
        dept_reviews = await self.db.scalar(
            select(func.count(MobilityApplication.id)).where(
                and_(
                    MobilityApplication.tenant_id == self.tenant_id,
                    MobilityApplication.status == MobilityApplicationStatus.DEPARTMENT_REVIEW.value,
                )
            )
        )
        intl_reviews = await self.db.scalar(
            select(func.count(MobilityApplication.id)).where(
                and_(
                    MobilityApplication.tenant_id == self.tenant_id,
                    MobilityApplication.status == MobilityApplicationStatus.INTERNATIONAL_OFFICE_REVIEW.value,
                )
            )
        )
        pending_nominations = await self.db.scalar(
            select(func.count(MobilityApplication.id)).where(
                and_(
                    MobilityApplication.tenant_id == self.tenant_id,
                    MobilityApplication.status == MobilityApplicationStatus.APPROVED.value,
                )
            )
        )
        active_inbound = await self.db.scalar(
            select(func.count(InboundStudentProfile.id)).where(
                and_(
                    InboundStudentProfile.tenant_id == self.tenant_id,
                    InboundStudentProfile.check_in_status.in_(["ACCEPTED", "ACTIVE_STUDY"]),
                )
            )
        )
        active_outbound = await self.db.scalar(
            select(func.count(MobilityApplication.id)).where(
                and_(
                    MobilityApplication.tenant_id == self.tenant_id,
                    MobilityApplication.status.in_(
                        [
                            MobilityApplicationStatus.ACTIVE_MOBILITY.value,
                            MobilityApplicationStatus.PRE_DEPARTURE_PREPARATION.value,
                        ]
                    ),
                )
            )
        )
        active_faculty = await self.db.scalar(
            select(func.count(FacultyMobilityRecord.id)).where(
                and_(
                    FacultyMobilityRecord.tenant_id == self.tenant_id,
                    FacultyMobilityRecord.status.in_(
                        [
                            FacultyMobilityStatus.APPROVED.value,
                            FacultyMobilityStatus.SCHEDULED.value,
                            FacultyMobilityStatus.ACTIVE.value,
                        ]
                    ),
                )
            )
        )
        pending_credits = await self.db.scalar(
            select(func.count(StudentCreditTransferRequest.id)).where(
                and_(
                    StudentCreditTransferRequest.tenant_id == self.tenant_id,
                    StudentCreditTransferRequest.status.in_(
                        [CreditTransferStatus.SUBMITTED.value, CreditTransferStatus.FACULTY_REVIEW.value]
                    ),
                )
            )
        )
        pending_funding = await self.db.scalar(
            select(func.count(MobilityFundingRequest.id)).where(
                and_(
                    MobilityFundingRequest.tenant_id == self.tenant_id,
                    MobilityFundingRequest.status == FundingStatus.REQUESTED.value,
                )
            )
        )

        return InternationalDashboardMetrics(
            total_active_partners=active_partners or 0,
            total_active_agreements=active_agreements or 0,
            agreements_expiring_soon=expiring_agreements or 0,
            total_published_programs=published_programs or 0,
            total_active_applications=active_apps or 0,
            pending_department_reviews=dept_reviews or 0,
            pending_international_office_reviews=intl_reviews or 0,
            pending_partner_nominations=pending_nominations or 0,
            active_inbound_students=active_inbound or 0,
            active_outbound_students=active_outbound or 0,
            active_faculty_mobilities=active_faculty or 0,
            pending_credit_transfers=pending_credits or 0,
            pending_funding_requests=pending_funding or 0,
        )

    # =========================================================================
    # 11. SCHEDULED SWEEP
    # =========================================================================

    async def sweep_agreements_and_deadlines(self) -> dict[str, int]:
        today = date.today()
        config = await self.get_or_create_config()
        warning_days = config.agreement_renewal_notice_days or 90

        expiring_stmt = select(InstitutionalAgreement).where(
            and_(
                InstitutionalAgreement.tenant_id == self.tenant_id,
                InstitutionalAgreement.status == AgreementStatus.ACTIVE.value,
                InstitutionalAgreement.expiry_date <= today + timedelta(days=warning_days),
                InstitutionalAgreement.expiry_date >= today,
            )
        )
        expiring_agrs = (await self.db.execute(expiring_stmt)).scalars().all()
        for agr in expiring_agrs:
            agr.status = AgreementStatus.EXPIRING.value
            await event_publisher.publish(
                db=self.db,
                tenant_id=self.tenant_id,
                event_type=DomainEventType.AGREEMENT_EXPIRY_WARNING,
                aggregate_type="InstitutionalAgreement",
                aggregate_id=agr.id,
                payload={
                    "agreement_id": str(agr.id),
                    "days_remaining": (agr.expiry_date - today).days,
                },
            )

        expired_stmt = select(InstitutionalAgreement).where(
            and_(
                InstitutionalAgreement.tenant_id == self.tenant_id,
                InstitutionalAgreement.status.in_([AgreementStatus.ACTIVE.value, AgreementStatus.EXPIRING.value]),
                InstitutionalAgreement.expiry_date < today,
            )
        )
        expired_agrs = (await self.db.execute(expired_stmt)).scalars().all()
        for agr in expired_agrs:
            agr.status = AgreementStatus.EXPIRED.value

        await self.db.flush()
        return {
            "marked_expiring": len(expiring_agrs),
            "marked_expired": len(expired_agrs),
        }
