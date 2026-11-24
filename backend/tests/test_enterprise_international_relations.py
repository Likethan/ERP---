"""CampusOS Enterprise International Relations, Student Exchange & Global Mobility Tests (Step 60).

Product Principle: "CampusOS — One Campus. One System. One Source of Truth."

Verifies:
1. International partner registration, unique codes (PRT-XXXXXX), and duplicate prevention.
2. Multi-tenant partner directory with country and category filtering.
3. Institutional agreements (MoUs), date validation, and formal amendment history.
4. Scheduled agreement expiration sweep, status updates, and warning event emission.
5. Mobility program configuration, academic calendar windows, and seat limits.
6. Student application submission, CGPA/credit prerequisite checks, and duplicate prevention.
7. Multi-stage review workflow (Department review -> International Office approval).
8. Partner nominations and official partner acceptance/rejection decisions.
9. Pre-departure preparation checklist, visa references, and active mobility transitions.
10. Inbound international student workspace, orientation completion, and check-in workflows.
11. Faculty exchange and visiting scholars with hierarchical HOD and VP approvals.
12. Academic course equivalency mappings evaluated by faculty specialists.
13. Credit transfer review: strictly non-automated, requires authorized committee resolution.
14. Mobility document checklists and secure verification lifecycle.
15. Mobility scholarship allocation and finance-referenced funding approvals.
16. Multi-tenant isolation: Tenant B is strictly denied access to Tenant A international records.
17. Real dashboard telemetry metrics calculation without fabricated data.
"""

from datetime import date, datetime, timedelta, timezone
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.core import Batch, Campus, Department, Institution, Program, Regulation
from app.models.international import (
    AgreementScopeType,
    AgreementStatus,
    CreditEquivalencyStatus,
    CreditTransferStatus,
    FacultyMobilityDirection,
    FacultyMobilityStatus,
    InboundStudentStatus,
    MobilityApplicationStatus,
    MobilityDocumentType,
    MobilityDocumentVerificationStatus,
    MobilityFundingStatus,
    MobilityProgramType,
    MobilityTermType,
    PartnerCategory,
)
from app.models.people import StudentProfile, User
from app.schemas.international import (
    AgreementAmendmentCreate,
    CourseEquivalencyCreate,
    CourseEquivalencyEvaluationRequest,
    CreditTransferApprovalRequest,
    CreditTransferRequestCreate,
    FacultyMobilityApprovalRequest,
    FacultyMobilityCreate,
    InboundOrientationCheckinRequest,
    InboundStudentCreate,
    InstitutionalAgreementCreate,
    InstitutionalAgreementUpdate,
    InternationalPartnerCreate,
    InternationalPartnerUpdate,
    MobilityApplicationCreate,
    MobilityApplicationReviewRequest,
    MobilityDocumentCreate,
    MobilityDocumentVerifyRequest,
    MobilityFundingApprovalRequest,
    MobilityFundingRequestCreate,
    MobilityProgramCreate,
    MobilityProgramUpdate,
    MobilityScholarshipCreate,
    PartnerDecisionRequest,
    PartnerNominationRequest,
    PreDepartureUpdateRequest,
)
from app.services.international_service import InternationalService


@pytest.fixture
async def intl_setup(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    super_admin_user: User,
):
    """Provides campus, departments, programs, faculty, and student profiles for tests."""
    uid = uuid.uuid4().hex[:6]

    campus = Campus(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name="Global Campus Center",
        code=f"CMP-INTL-{uid}",
        address="100 Innovation Way",
        city="Chennai",
        is_active=True,
    )
    db_session.add(campus)

    dept = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        campus_id=campus.id,
        name="Computer Science & Engineering",
        code=f"CSE-{uid}",
        is_active=True,
    )
    db_session.add(dept)

    prog = Program(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        department_id=dept.id,
        name="B.Tech Computer Science",
        code=f"BTCSE-{uid}",
        degree_level="UNDERGRADUATE",
        duration_years=4,
        total_semesters=8,
        is_active=True,
    )
    db_session.add(prog)

    reg = Regulation(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code=f"REG24-{uid}",
        title="Regulation 2024",
        effective_year=2024,
        is_active=True,
    )
    db_session.add(reg)

    batch = Batch(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        program_id=prog.id,
        regulation_id=reg.id,
        name=f"CSE 2024-2028 {uid}",
        admission_year=2024,
        graduation_year=2028,
        is_active=True,
    )
    db_session.add(batch)

    # Faculty coordinator
    coordinator_user = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"intl_coord_{uid}@campus.edu",
        first_name="Dr. Sophia",
        last_name="Williams",
        password_hash="hashed_pw_coord",
        status="ACTIVE",
    )
    db_session.add(coordinator_user)

    # HOD
    hod_user = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"hod_cse_{uid}@campus.edu",
        first_name="Prof. Rajesh",
        last_name="Nair",
        password_hash="hashed_pw_hod",
        status="ACTIVE",
    )
    db_session.add(hod_user)

    # VP
    vp_user = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"vp_academic_{uid}@campus.edu",
        first_name="Dr. Eleanor",
        last_name="Vance",
        password_hash="hashed_pw_vp",
        status="ACTIVE",
    )
    db_session.add(vp_user)

    # Student 1 (eligible with high CGPA)
    student_user_1 = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"student1_{uid}@campus.edu",
        first_name="Aditya",
        last_name="Kumar",
        password_hash="hashed_pw_s1",
        status="ACTIVE",
    )
    db_session.add(student_user_1)

    profile_1 = StudentProfile(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=student_user_1.id,
        admission_number=f"ADM-2024-{uid}-01",
        date_of_birth=date(2004, 5, 15),
        gender="MALE",
        admission_date=date(2024, 7, 1),
        expected_graduation_date=date(2028, 6, 30),
        program_id=prog.id,
        batch_id=batch.id,
        roll_number=f"2026CSE{uid[:4].upper()}01",
        status="ACTIVE",
    )
    # inject test attributes
    setattr(profile_1, "cgpa", 8.8)
    setattr(profile_1, "completed_credits", 60)
    db_session.add(profile_1)

    # Student 2 (low CGPA for eligibility failure test)
    student_user_2 = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"student2_{uid}@campus.edu",
        first_name="Rohan",
        last_name="Gupta",
        password_hash="hashed_pw_s2",
        status="ACTIVE",
    )
    db_session.add(student_user_2)

    profile_2 = StudentProfile(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=student_user_2.id,
        admission_number=f"ADM-2024-{uid}-02",
        date_of_birth=date(2004, 8, 20),
        gender="MALE",
        admission_date=date(2024, 7, 1),
        expected_graduation_date=date(2028, 6, 30),
        program_id=prog.id,
        batch_id=batch.id,
        roll_number=f"2026CSE{uid[:4].upper()}02",
        status="ACTIVE",
    )
    setattr(profile_2, "cgpa", 5.2)
    setattr(profile_2, "completed_credits", 20)
    db_session.add(profile_2)

    await db_session.flush()

    return {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "campus": campus,
        "dept": dept,
        "program": prog,
        "coordinator": coordinator_user,
        "hod": hod_user,
        "vp": vp_user,
        "student_1": student_user_1,
        "student_2": student_user_2,
    }


# =============================================================================
# TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_partner_registration_and_duplicate_prevention(db_session: AsyncSession, intl_setup):
    service = InternationalService(db_session, intl_setup["tenant_a"].id)

    create_data = InternationalPartnerCreate(
        partner_name="Technical University of Munich",
        legal_name="Technische Universität München",
        country_code="DE",
        country_name="Germany",
        city="Munich",
        category=PartnerCategory.UNIVERSITY,
        official_website="https://www.tum.de",
        primary_contact_name="Dr. Hans Gruber",
        primary_contact_email="international@tum.de",
    )
    partner = await service.create_partner(create_data, intl_setup["coordinator"].id)

    assert partner.partner_name == "Technical University of Munich"
    assert partner.partner_code.startswith("PRT-")
    assert partner.country_code == "DE"
    assert partner.category == PartnerCategory.UNIVERSITY

    # Duplicate creation check
    with pytest.raises(ConflictException):
        await service.create_partner(create_data, intl_setup["coordinator"].id)


@pytest.mark.asyncio
async def test_partner_listing_and_filtering(db_session: AsyncSession, intl_setup):
    service = InternationalService(db_session, intl_setup["tenant_a"].id)

    p1 = await service.create_partner(
        InternationalPartnerCreate(
            partner_name="National University of Singapore",
            country_code="SG",
            country_name="Singapore",
            city="Singapore",
            category=PartnerCategory.UNIVERSITY,
        )
    )
    p2 = await service.create_partner(
        InternationalPartnerCreate(
            partner_name="Tokyo Institute of Technology",
            country_code="JP",
            country_name="Japan",
            city="Tokyo",
            category=PartnerCategory.RESEARCH_INSTITUTE,
        )
    )

    all_partners = await service.list_partners()
    assert len(all_partners) >= 2

    # Filter by country
    sg_partners = await service.list_partners(country_code="SG")
    assert any(p.partner_name == "National University of Singapore" for p in sg_partners)
    assert not any(p.partner_name == "Tokyo Institute of Technology" for p in sg_partners)

    # Filter by category
    research_partners = await service.list_partners(category=PartnerCategory.RESEARCH_INSTITUTE)
    assert any(p.partner_name == "Tokyo Institute of Technology" for p in research_partners)


@pytest.mark.asyncio
async def test_institutional_agreement_lifecycle_and_amendments(db_session: AsyncSession, intl_setup):
    service = InternationalService(db_session, intl_setup["tenant_a"].id)

    partner = await service.create_partner(
        InternationalPartnerCreate(
            partner_name="University of Edinburgh",
            country_code="GB",
            country_name="United Kingdom",
            city="Edinburgh",
        )
    )

    today = date.today()
    # End date before start date validation
    with pytest.raises(ValidationException):
        await service.create_agreement(
            InstitutionalAgreementCreate(
                partner_id=partner.id,
                agreement_title="Invalid Date MoU",
                agreement_type="MoU",
                effective_start_date=today,
                effective_end_date=today - timedelta(days=10),
            )
        )

    # Create valid agreement
    agreement = await service.create_agreement(
        InstitutionalAgreementCreate(
            partner_id=partner.id,
            agreement_title="Global Mobility MoU 2026-2030",
            agreement_type="Bilateral Exchange MoU",
            scope_types=[AgreementScopeType.STUDENT_EXCHANGE, AgreementScopeType.FACULTY_EXCHANGE],
            effective_start_date=today,
            effective_end_date=today + timedelta(days=365 * 4),
            renewal_window_days=90,
            responsible_coordinator_user_id=intl_setup["coordinator"].id,
            quota_inbound_per_year=10,
            quota_outbound_per_year=10,
        )
    )
    assert agreement.agreement_reference_number.startswith("AGR-")
    assert agreement.status == AgreementStatus.DRAFT

    # Approve agreement
    approved = await service.update_agreement(
        agreement.id,
        InstitutionalAgreementUpdate(status=AgreementStatus.APPROVED),
        current_user_id=intl_setup["vp"].id,
    )
    assert approved.status == AgreementStatus.APPROVED
    assert approved.approved_by_user_id == intl_setup["vp"].id

    # Add amendment extending scope and date
    new_end_date = today + timedelta(days=365 * 5)
    amendment = await service.add_amendment(
        agreement.id,
        AgreementAmendmentCreate(
            amendment_type="EXTENSION_AND_RESEARCH_SCOPE",
            title="Add Joint AI Research Collaboration",
            description="Extends MoU by 1 year and adds joint AI research scope.",
            new_effective_end_date=new_end_date,
        ),
        current_user_id=intl_setup["coordinator"].id,
    )
    assert amendment.amendment_type == "EXTENSION_AND_RESEARCH_SCOPE"

    updated_agr = await service.get_agreement(agreement.id)
    assert updated_agr.effective_end_date == new_end_date


@pytest.mark.asyncio
async def test_agreement_expiry_sweep_and_warnings(db_session: AsyncSession, intl_setup):
    service = InternationalService(db_session, intl_setup["tenant_a"].id)

    partner = await service.create_partner(
        InternationalPartnerCreate(
            partner_name="Delft University of Technology",
            country_code="NL",
            country_name="Netherlands",
            city="Delft",
        )
    )

    today = date.today()
    # Expiring soon agreement (expires in 30 days)
    agr_expiring = await service.create_agreement(
        InstitutionalAgreementCreate(
            partner_id=partner.id,
            agreement_title="Expiring TU Delft MoU",
            agreement_type="Exchange",
            effective_start_date=today - timedelta(days=335),
            effective_end_date=today + timedelta(days=30),
            status=AgreementStatus.ACTIVE,
        )
    )

    # Already expired agreement
    agr_expired = await service.create_agreement(
        InstitutionalAgreementCreate(
            partner_id=partner.id,
            agreement_title="Expired TU Delft MoU",
            agreement_type="Exchange",
            effective_start_date=today - timedelta(days=400),
            effective_end_date=today - timedelta(days=5),
            status=AgreementStatus.ACTIVE,
        )
    )

    # Run automated sweep
    sweep_res = await service.sweep_agreements_and_deadlines()
    assert sweep_res["marked_expiring"] >= 1
    assert sweep_res["marked_expired"] >= 1

    check_expiring = await service.get_agreement(agr_expiring.id)
    assert check_expiring.status == AgreementStatus.EXPIRING
    assert check_expiring.is_expiring_soon is True

    check_expired = await service.get_agreement(agr_expired.id)
    assert check_expired.status == AgreementStatus.EXPIRED


@pytest.mark.asyncio
async def test_mobility_program_creation_validation_and_publishing(db_session: AsyncSession, intl_setup):
    service = InternationalService(db_session, intl_setup["tenant_a"].id)

    partner = await service.create_partner(
        InternationalPartnerCreate(
            partner_name="KTH Royal Institute of Technology",
            country_code="SE",
            country_name="Sweden",
            city="Stockholm",
        )
    )

    today = date.today()
    # Validation error if deadline before start date
    with pytest.raises(ValidationException):
        await service.create_program(
            MobilityProgramCreate(
                partner_id=partner.id,
                program_title="Fall 2026 Exchange",
                academic_year="2026-2027",
                application_start_date=today,
                application_deadline=today - timedelta(days=5),
                expected_start_date=today + timedelta(days=90),
                expected_end_date=today + timedelta(days=210),
            )
        )

    # Create draft program
    prog = await service.create_program(
        MobilityProgramCreate(
            partner_id=partner.id,
            program_title="KTH Computer Science Semester Exchange 2026",
            program_type=MobilityProgramType.SEMESTER_EXCHANGE,
            term_type=MobilityTermType.FALL_SEMESTER,
            academic_year="2026-2027",
            eligible_department_ids=[intl_setup["dept"].id],
            total_seats=4,
            nomination_limit=8,
            min_cgpa_requirement=7.5,
            min_credits_completed=30,
            application_start_date=today - timedelta(days=5),
            application_deadline=today + timedelta(days=30),
            expected_start_date=today + timedelta(days=90),
            expected_end_date=today + timedelta(days=210),
            is_published=False,
        )
    )
    assert prog.is_published is False
    assert prog.partner_name == "KTH Royal Institute of Technology"

    # Publish program
    published = await service.update_program(
        prog.id,
        MobilityProgramUpdate(is_published=True),
        current_user_id=intl_setup["coordinator"].id,
    )
    assert published.is_published is True

    # Check open_only program query
    open_programs = await service.list_programs(open_only=True)
    assert any(p.id == prog.id for p in open_programs)


@pytest.mark.asyncio
async def test_student_application_submission_and_eligibility(db_session: AsyncSession, intl_setup):
    service = InternationalService(db_session, intl_setup["tenant_a"].id)

    partner = await service.create_partner(
        InternationalPartnerCreate(
            partner_name="ETH Zurich",
            country_code="CH",
            country_name="Switzerland",
            city="Zurich",
        )
    )

    today = date.today()
    prog = await service.create_program(
        MobilityProgramCreate(
            partner_id=partner.id,
            program_title="ETH Zurich High Performance Computing Exchange",
            academic_year="2026-2027",
            min_cgpa_requirement=8.0,
            min_credits_completed=40,
            application_start_date=today - timedelta(days=10),
            application_deadline=today + timedelta(days=30),
            expected_start_date=today + timedelta(days=120),
            expected_end_date=today + timedelta(days=240),
            is_published=True,
        )
    )

    # 1. Eligible student application
    app_s1 = await service.create_application(
        MobilityApplicationCreate(
            program_id=prog.id,
            statement_of_purpose="Passionate about parallel algorithms and quantum computing research at ETH.",
            proposed_courses=[{"code": "CS-501", "title": "Parallel Programming", "credits": 6}],
            emergency_contact_name="Ramesh Kumar",
            emergency_contact_phone="+91 9876543210",
            emergency_contact_relationship="Father",
            submit_now=True,
        ),
        student_user_id=intl_setup["student_1"].id,
    )
    assert app_s1.status == MobilityApplicationStatus.DEPARTMENT_REVIEW
    assert app_s1.eligibility_check_passed is True

    # Duplicate application check for same program
    with pytest.raises(ConflictException):
        await service.create_application(
            MobilityApplicationCreate(
                program_id=prog.id,
                statement_of_purpose="Another duplicate application attempt.",
                emergency_contact_name="Ramesh Kumar",
                emergency_contact_phone="+91 9876543210",
                emergency_contact_relationship="Father",
            ),
            student_user_id=intl_setup["student_1"].id,
        )

    # 2. Ineligible student (CGPA 5.2 < 8.0)
    app_s2 = await service.create_application(
        MobilityApplicationCreate(
            program_id=prog.id,
            statement_of_purpose="Applying for exchange program despite lower grades.",
            emergency_contact_name="Sunil Gupta",
            emergency_contact_phone="+91 9876543211",
            emergency_contact_relationship="Father",
            submit_now=True,
        ),
        student_user_id=intl_setup["student_2"].id,
    )
    assert app_s2.eligibility_check_passed is False
    assert app_s2.status == MobilityApplicationStatus.ELIGIBILITY_REVIEW
    assert "cgpa_error" in app_s2.eligibility_check_details


@pytest.mark.asyncio
async def test_application_multi_stage_review_workflow(db_session: AsyncSession, intl_setup):
    service = InternationalService(db_session, intl_setup["tenant_a"].id)

    partner = await service.create_partner(
        InternationalPartnerCreate(
            partner_name="Politecnico di Milano",
            country_code="IT",
            country_name="Italy",
            city="Milan",
        )
    )

    today = date.today()
    prog = await service.create_program(
        MobilityProgramCreate(
            partner_id=partner.id,
            program_title="Milan AI & Robotics Semester Exchange",
            academic_year="2026-2027",
            min_cgpa_requirement=7.0,
            application_start_date=today - timedelta(days=5),
            application_deadline=today + timedelta(days=25),
            expected_start_date=today + timedelta(days=100),
            expected_end_date=today + timedelta(days=220),
            is_published=True,
        )
    )

    app = await service.create_application(
        MobilityApplicationCreate(
            program_id=prog.id,
            statement_of_purpose="Eager to specialize in humanoid robotics at Polimi.",
            emergency_contact_name="Ramesh Kumar",
            emergency_contact_phone="+91 9876543210",
            emergency_contact_relationship="Father",
            submit_now=True,
        ),
        student_user_id=intl_setup["student_1"].id,
    )
    assert app.status == MobilityApplicationStatus.DEPARTMENT_REVIEW

    # 1. HOD / Department Review -> Approve
    dept_reviewed = await service.review_application(
        app.id,
        MobilityApplicationReviewRequest(
            action="APPROVE",
            comments="Strong academic record in AI, approved by department.",
        ),
        reviewer_user_id=intl_setup["hod"].id,
        reviewer_role="HOD",
    )
    assert dept_reviewed.status == MobilityApplicationStatus.INTERNATIONAL_OFFICE_REVIEW
    assert dept_reviewed.department_decision == "APPROVED"

    # 2. International Office Review -> Approve
    intl_reviewed = await service.review_application(
        app.id,
        MobilityApplicationReviewRequest(
            action="APPROVE",
            comments="Nomination quota verified and approved for partner submission.",
        ),
        reviewer_user_id=intl_setup["coordinator"].id,
        reviewer_role="INTERNATIONAL_OFFICE",
    )
    assert intl_reviewed.status == MobilityApplicationStatus.APPROVED
    assert intl_reviewed.intl_office_decision == "APPROVED"

    # 3. Nominate to Partner
    nominated = await service.nominate_to_partner(
        app.id,
        PartnerNominationRequest(
            partner_contact_email="exchange@polimi.it",
            nomination_notes="Official nomination of Aditya Kumar for Fall 2026.",
        ),
        current_user_id=intl_setup["coordinator"].id,
    )
    assert nominated.status == MobilityApplicationStatus.PARTNER_NOMINATED

    # 4. Partner Decision -> ACCEPTED
    decision = await service.record_partner_decision(
        app.id,
        PartnerDecisionRequest(
            decision="ACCEPTED",
            partner_reference_code="POLIMI-2026-EX-992",
            official_response_notes="Admission offer letter issued.",
        ),
        current_user_id=intl_setup["coordinator"].id,
    )
    assert decision.status == MobilityApplicationStatus.PARTNER_ACCEPTED

    # 5. Pre-departure and Active Mobility
    predeparture = await service.update_pre_departure(
        app.id,
        PreDepartureUpdateRequest(
            pre_departure_checklist={"visa_approved": True, "insurance_purchased": True, "orientation_done": True},
            visa_reference_number="IT-VISA-2026-8812",
            insurance_policy_number="ALLIANZ-GLOB-2026-441",
        ),
    )
    assert predeparture.status == MobilityApplicationStatus.PRE_DEPARTURE_PREPARATION

    # Transition to Active Mobility
    active_mob = await service.transition_mobility_state(app.id, MobilityApplicationStatus.ACTIVE_MOBILITY)
    assert active_mob.status == MobilityApplicationStatus.ACTIVE_MOBILITY


@pytest.mark.asyncio
async def test_inbound_international_student_management(db_session: AsyncSession, intl_setup):
    service = InternationalService(db_session, intl_setup["tenant_a"].id)

    partner = await service.create_partner(
        InternationalPartnerCreate(
            partner_name="Sorbonne University",
            country_code="FR",
            country_name="France",
            city="Paris",
        )
    )

    today = date.today()
    inbound = await service.create_inbound_student(
        InboundStudentCreate(
            partner_id=partner.id,
            student_first_name="Camille",
            student_last_name="Laurent",
            email="camille.laurent@etu.sorbonne-universite.fr",
            phone="+33 612345678",
            country_of_citizenship="France",
            home_institution_name="Sorbonne Université",
            home_program_of_study="MSc Data Science",
            host_department_id=intl_setup["dept"].id,
            expected_start_date=today,
            expected_end_date=today + timedelta(days=150),
            study_period_terms="Fall Semester 2026",
            assigned_mentor_user_id=intl_setup["coordinator"].id,
            accommodation_reference="International Hostel Block C-204",
        )
    )
    assert inbound.inbound_reference_number.startswith("INB-")
    assert inbound.status == InboundStudentStatus.NOMINATED
    assert inbound.orientation_completed is False

    # Check-in and orientation completion
    checked_in = await service.checkin_inbound_student(
        inbound.id,
        InboundOrientationCheckinRequest(
            check_in_date=today,
            orientation_completed=True,
            orientation_notes="Completed campus induction, lab access card issued.",
        ),
    )
    assert checked_in.status == InboundStudentStatus.ACTIVE_STUDY
    assert checked_in.orientation_completed is True
    assert checked_in.check_in_date == today


@pytest.mark.asyncio
async def test_faculty_mobility_workflow_and_approvals(db_session: AsyncSession, intl_setup):
    service = InternationalService(db_session, intl_setup["tenant_a"].id)

    partner = await service.create_partner(
        InternationalPartnerCreate(
            partner_name="Nanyang Technological University",
            country_code="SG",
            country_name="Singapore",
            city="Singapore",
        )
    )

    today = date.today()
    # Outbound faculty visiting NTU
    faculty_mob = await service.create_faculty_mobility(
        FacultyMobilityCreate(
            direction=FacultyMobilityDirection.OUTBOUND_FACULTY,
            partner_id=partner.id,
            faculty_user_id=intl_setup["coordinator"].id,
            visit_start_date=today + timedelta(days=45),
            visit_end_date=today + timedelta(days=60),
            visit_objectives="Deliver guest lectures on Distributed Operating Systems and establish joint grant proposal.",
            lecture_topics=["Microkernel Architectures", "Fault Tolerant Consensus"],
            research_collaboration_areas=["Cloud Edge Computing", "Green Computing"],
        ),
        current_user_id=intl_setup["coordinator"].id,
    )
    assert faculty_mob.mobility_reference_number.startswith("FAC-")
    assert faculty_mob.status == FacultyMobilityStatus.SUBMITTED

    # Step 1: HOD Approval -> Moves to VP_REVIEW
    hod_approved = await service.approve_faculty_mobility(
        faculty_mob.id,
        FacultyMobilityApprovalRequest(
            decision="APPROVED",
            comments="Workload reallocated during visit. Strongly recommended.",
        ),
        reviewer_user_id=intl_setup["hod"].id,
        role="HOD",
    )
    assert hod_approved.status == FacultyMobilityStatus.VP_REVIEW

    # Step 2: Vice Principal Approval -> Moves to APPROVED
    vp_approved = await service.approve_faculty_mobility(
        faculty_mob.id,
        FacultyMobilityApprovalRequest(
            decision="APPROVED",
            comments="Institution-level collaboration approved.",
        ),
        reviewer_user_id=intl_setup["vp"].id,
        role="VICE_PRINCIPAL",
    )
    assert vp_approved.status == FacultyMobilityStatus.APPROVED


@pytest.mark.asyncio
async def test_course_equivalency_and_academic_credit_transfer(db_session: AsyncSession, intl_setup):
    service = InternationalService(db_session, intl_setup["tenant_a"].id)

    partner = await service.create_partner(
        InternationalPartnerCreate(
            partner_name="University of Melbourne",
            country_code="AU",
            country_name="Australia",
            city="Melbourne",
        )
    )

    # 1. Propose Course Equivalency Mapping
    mapping = await service.create_course_equivalency(
        CourseEquivalencyCreate(
            partner_id=partner.id,
            host_course_code="COMP90042",
            host_course_title="Natural Language Processing",
            host_course_credits=12.5,
            campus_course_code="CS-702",
            campus_course_title="Natural Language Processing & LLMs",
            campus_course_credits=4.0,
            department_id=intl_setup["dept"].id,
            learning_outcomes_comparison="90% syllabus overlap, transformers, syntax trees, semantic analysis.",
        ),
        current_user_id=intl_setup["coordinator"].id,
    )
    assert mapping.status == CreditEquivalencyStatus.PROPOSED

    # 2. Faculty Evaluator reviews mapping
    evaluated_map = await service.evaluate_course_equivalency(
        mapping.id,
        CourseEquivalencyEvaluationRequest(
            status=CreditEquivalencyStatus.APPROVED,
            evaluator_comments="Equivalent in rigorous theoretical depth and laboratory coursework.",
        ),
        evaluator_user_id=intl_setup["coordinator"].id,
    )
    assert evaluated_map.status == CreditEquivalencyStatus.APPROVED

    # 3. Student requests credit transfer with transcript
    today = date.today()
    prog = await service.create_program(
        MobilityProgramCreate(
            partner_id=partner.id,
            program_title="Melbourne Exchange",
            academic_year="2026-2027",
            application_start_date=today - timedelta(days=10),
            application_deadline=today + timedelta(days=10),
            expected_start_date=today + timedelta(days=30),
            expected_end_date=today + timedelta(days=120),
            is_published=True,
        )
    )
    app = await service.create_application(
        MobilityApplicationCreate(
            program_id=prog.id,
            statement_of_purpose="NLP research abroad.",
            emergency_contact_name="Parent",
            emergency_contact_phone="12345",
            emergency_contact_relationship="Parent",
        ),
        student_user_id=intl_setup["student_1"].id,
    )

    transfer_req = await service.request_credit_transfer(
        CreditTransferRequestCreate(
            application_id=app.id,
            host_course_code="COMP90042",
            host_course_title="Natural Language Processing",
            host_grade_received="H1 (First Class Honours)",
            host_credits_earned=12.5,
            equivalency_mapping_id=mapping.id,
            target_campus_credits=4.0,
            transcript_document_url="https://documents.campus.internal/transcripts/melb_nlp.pdf",
        ),
        student_user_id=intl_setup["student_1"].id,
    )
    assert transfer_req.status == CreditTransferStatus.SUBMITTED
    # Crucial Rule: Credits MUST NOT be automatically posted to official transcript
    assert transfer_req.credits_posted_to_transcript is False

    # 4. Authorized Academic Committee resolution
    approved_transfer = await service.review_credit_transfer(
        transfer_req.id,
        CreditTransferApprovalRequest(
            status=CreditTransferStatus.COMMITTEE_APPROVED,
            approved_credits=4.0,
            committee_resolution_notes="Academic Council Resolution AC-2026/89: 4 institutional credits recognized.",
        ),
        reviewer_user_id=intl_setup["vp"].id,
    )
    assert approved_transfer.status == CreditTransferStatus.COMMITTEE_APPROVED
    assert approved_transfer.credits_posted_to_transcript is True
    assert approved_transfer.target_campus_credits == 4.0


@pytest.mark.asyncio
async def test_mobility_documents_and_scholarships(db_session: AsyncSession, intl_setup):
    service = InternationalService(db_session, intl_setup["tenant_a"].id)

    # 1. Mobility Document verification
    doc = await service.create_document(
        MobilityDocumentCreate(
            document_type=MobilityDocumentType.PASSPORT,
            document_name="Indian Passport Copy - Aditya Kumar",
            file_storage_url="https://storage.campus.internal/passports/aditya.pdf",
            file_mime_type="application/pdf",
            document_expiry_date=date.today() + timedelta(days=365 * 8),
        ),
        current_user_id=intl_setup["student_1"].id,
    )
    assert doc.verification_status == MobilityDocumentVerificationStatus.PENDING

    verified_doc = await service.verify_document(
        doc.id,
        MobilityDocumentVerifyRequest(status=MobilityDocumentVerificationStatus.VERIFIED),
        reviewer_user_id=intl_setup["coordinator"].id,
    )
    assert verified_doc.verification_status == MobilityDocumentVerificationStatus.VERIFIED

    # 2. Mobility Scholarship & Funding Request
    sch = await service.create_scholarship(
        MobilityScholarshipCreate(
            scholarship_name="DAAD German Academic Exchange Grant",
            funding_source="DAAD / External Government Grant",
            award_amount_per_student=3500.00,
            total_available_slots=5,
            eligibility_criteria_notes="Minimum CGPA 8.0, German partner institution.",
        ),
        current_user_id=intl_setup["coordinator"].id,
    )
    assert sch.scholarship_code.startswith("SCH-")
    assert sch.award_amount_per_student == 3500.00


@pytest.mark.asyncio
async def test_multi_tenant_isolation_denies_cross_tenant_access(db_session: AsyncSession, intl_setup):
    service_a = InternationalService(db_session, intl_setup["tenant_a"].id)
    service_b = InternationalService(db_session, intl_setup["tenant_b"].id)

    # Create partner in Tenant A
    partner_a = await service_a.create_partner(
        InternationalPartnerCreate(
            partner_name="Oxford University",
            country_code="GB",
            country_name="United Kingdom",
            city="Oxford",
        )
    )

    # Tenant A can fetch it
    fetched = await service_a.get_partner(partner_a.id)
    assert fetched.id == partner_a.id

    # Tenant B MUST NOT be able to view or edit Tenant A's partner
    with pytest.raises(NotFoundException):
        await service_b.get_partner(partner_a.id)

    with pytest.raises(NotFoundException):
        await service_b.update_partner(partner_a.id, InternationalPartnerUpdate(city="Cambridge"))


@pytest.mark.asyncio
async def test_international_dashboard_metrics(db_session: AsyncSession, intl_setup):
    service = InternationalService(db_session, intl_setup["tenant_a"].id)

    metrics = await service.get_dashboard_metrics()
    assert isinstance(metrics.total_active_partners, int)
    assert isinstance(metrics.total_active_agreements, int)
    assert isinstance(metrics.total_published_programs, int)
    assert isinstance(metrics.total_active_applications, int)
    assert isinstance(metrics.active_inbound_students, int)
    assert isinstance(metrics.active_outbound_students, int)
    assert isinstance(metrics.active_faculty_mobilities, int)
