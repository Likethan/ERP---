"""Enterprise Student Admissions, Enrollment & Onboarding Orchestration Tests (Step 48).

Comprehensive automated tests covering:
1. Admissions cycle configuration, deadlines, and validation.
2. Applicant registration, duplicate detection, and profile merging.
3. Application lifecycle: draft, auto score calculation, submission, correction windows, and withdrawal.
4. Document requirement checklists, applicant uploads, and reviewer verification workflows.
5. Versioned eligibility evaluation engine with explainable criteria and academic reviews.
6. Seat allocation limits, capacity guards, merit rankings, and selection runs.
7. Offer issuance, seat reservations, acceptance, decline, and seat release.
8. Idempotent enrollment orchestration connecting accepted offers to canonical StudentProfile and User.
9. Post-enrollment institutional onboarding checklists, task verifications, and completion milestones.
10. Multi-tenant isolation and aggregate admissions funnel analytics.
"""

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token, get_password_hash
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
    ReviewStage,
    SeatAllocation,
    SelectionResult,
    SelectionRun,
    SelectionStatus,
)
from app.models.core import AcademicYear, Batch, Campus, Department, Institution, Program, Regulation, Semester
from app.models.people import Role, StudentProfile, User, UserRoleAssignment
from app.schemas.admissions import (
    AdmissionApplicationCreate,
    AdmissionApplicationUpdate,
    AdmissionCycleCreate,
    AdmissionCycleUpdate,
    AdmissionOfferCreate,
    AdmissionOfferRespond,
    AdmissionOfferRevoke,
    ApplicantMergeRequest,
    ApplicantProfileCreate,
    ApplicantProfileUpdate,
    ApplicationDocumentRequirementCreate,
    ApplicationDocumentUpload,
    ApplicationDocumentVerify,
    ApplicationReviewCreate,
    ApplicationStatusTransition,
    EligibilityEvaluationRequest,
    EligibilityRuleCreate,
    EnrollmentWorkflowInitiate,
    OnboardingTaskUpdate,
    SeatAllocationCreate,
    SeatAllocationUpdate,
    SelectionRunCreate,
)
from app.services.admissions_service import AdmissionsService


def make_auth_headers(
    user: User,
    tenant_id: uuid.UUID,
    role_name: str = "INSTITUTION_ADMIN",
    permissions: list[str] | None = None,
) -> dict[str, str]:
    """Helper to generate JWT bearer and cookie authorization headers."""
    perms = permissions if permissions is not None else ["*"]
    token = create_access_token(
        user_id=user.id,
        tenant_id=tenant_id,
        roles=[role_name],
        permissions=perms,
    )
    return {
        "Authorization": f"Bearer {token}",
        "Cookie": f"{ACCESS_TOKEN_COOKIE_NAME}={token}",
        "X-Tenant-ID": str(tenant_id),
    }


@pytest.fixture
async def admissions_fixture(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    tenant_b: Institution,
    tenant_admin_b: User,
):
    """Fixture providing two isolated tenants with academic years, departments, programs, and batches."""
    uid = uuid.uuid4().hex[:6]

    campus_a = Campus(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name="Main Technology Campus",
        code=f"MTC-{uid}",
        address="123 Campus Way",
        city="Coimbatore",
        is_active=True,
    )
    db_session.add(campus_a)

    ay_a = AcademicYear(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name=f"AY 2026-2027 {uid}",
        start_date=date(2026, 7, 1),
        end_date=date(2027, 6, 30),
        is_current=True,
    )
    db_session.add(ay_a)

    dept_a = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        campus_id=campus_a.id,
        name="School of Computing",
        code=f"SOC-{uid}",
        is_active=True,
    )
    db_session.add(dept_a)

    prog_a = Program(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        department_id=dept_a.id,
        name="B.Tech Computer Science and Engineering",
        code=f"BTCSE-{uid}",
        degree_level="UNDERGRADUATE",
        duration_years=4,
        total_semesters=8,
        is_active=True,
    )
    db_session.add(prog_a)

    reg_a = Regulation(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code=f"REG-2026-{uid}",
        title="Regulation 2026",
        effective_year=2026,
        is_active=True,
    )
    db_session.add(reg_a)

    batch_a = Batch(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        program_id=prog_a.id,
        regulation_id=reg_a.id,
        name=f"Class of 2030 {uid}",
        admission_year=2026,
        graduation_year=2030,
        is_active=True,
    )
    db_session.add(batch_a)

    # Ensure STUDENT role exists
    role_res = await db_session.execute(
        select(Role).where(Role.name == "STUDENT")
    )
    student_role = role_res.scalars().first()
    if not student_role:
        student_role = Role(
            id=uuid.uuid4(),
            tenant_id=None,
            name="STUDENT",
            display_name="Student",
            description="Enrolled student role",
            is_system=True,
        )
        db_session.add(student_role)

    await db_session.commit()

    return {
        "tenant_a": tenant_a,
        "admin_a": tenant_admin_a,
        "campus_a": campus_a,
        "ay_a": ay_a,
        "prog_a": prog_a,
        "batch_a": batch_a,
        "tenant_b": tenant_b,
        "admin_b": tenant_admin_b,
    }


# =============================================================================
# 1. ADMISSIONS CYCLE TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_admissions_cycle_management_and_validation(
    db_session: AsyncSession, admissions_fixture: dict
):
    """Test admissions cycle creation, date constraint validation, updates, and retrieval."""
    tenant = admissions_fixture["tenant_a"]
    admin = admissions_fixture["admin_a"]
    ay = admissions_fixture["ay_a"]
    svc = AdmissionsService(db_session)
    uid = uuid.uuid4().hex[:4]

    # Valid cycle
    create_req = AdmissionCycleCreate(
        academic_year_id=ay.id,
        code=f"FALL2026-{uid}",
        name="Undergraduate Admissions Fall 2026",
        admission_term="FALL",
        application_start_date=date.today(),
        application_end_date=date.today() + timedelta(days=60),
        document_deadline=date.today() + timedelta(days=70),
        offer_acceptance_deadline=date.today() + timedelta(days=90),
    )
    cycle = await svc.create_cycle(tenant.id, create_req, admin.id)
    assert cycle.id is not None
    assert cycle.status == AdmissionCycleStatus.DRAFT
    assert cycle.total_applications_count == 0

    # Test invalid dates: end date before start date
    with pytest.raises(Exception):
        invalid_req = AdmissionCycleCreate(
            academic_year_id=ay.id,
            code=f"INV-{uid}",
            name="Invalid Cycle",
            application_start_date=date.today() + timedelta(days=30),
            application_end_date=date.today(),  # invalid
            document_deadline=date.today() + timedelta(days=35),
            offer_acceptance_deadline=date.today() + timedelta(days=40),
        )
        await svc.create_cycle(tenant.id, invalid_req, admin.id)

    # Update cycle status to PUBLISHED
    update_req = AdmissionCycleUpdate(status=AdmissionCycleStatus.PUBLISHED)
    updated = await svc.update_cycle(tenant.id, cycle.id, update_req, admin.id)
    assert updated.status == AdmissionCycleStatus.PUBLISHED

    # List cycles
    cycles = await svc.list_cycles(tenant.id)
    assert len(cycles) >= 1
    assert any(c.id == cycle.id for c in cycles)


# =============================================================================
# 2. APPLICANT PROFILES & DUPLICATE DETECTION TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_applicant_registration_duplicate_detection_and_merging(
    db_session: AsyncSession, admissions_fixture: dict
):
    """Test applicant registration, automatic duplicate detection by email, and profile merging."""
    tenant = admissions_fixture["tenant_a"]
    admin = admissions_fixture["admin_a"]
    svc = AdmissionsService(db_session)
    uid = uuid.uuid4().hex[:4]
    email = f"john.doe.{uid}@example.com"

    # Register initial applicant
    app_req_1 = ApplicantProfileCreate(
        first_name="John",
        last_name="Doe",
        email=email,
        phone_number="+919876543210",
        date_of_birth=date(2005, 5, 15),
        gender="MALE",
        city="Bengaluru",
    )
    applicant_1 = await svc.register_applicant(tenant.id, app_req_1, admin.id)
    assert applicant_1.applicant_number.startswith("APP-")
    assert applicant_1.is_duplicate is False
    assert applicant_1.verification_status == ApplicantVerificationStatus.PENDING_VERIFICATION

    # Register second applicant with SAME email -> auto-flagged duplicate
    app_req_2 = ApplicantProfileCreate(
        first_name="Johnny",
        last_name="Doe",
        email=email,
        phone_number="+919876543210",
        date_of_birth=date(2005, 5, 15),
        gender="MALE",
        city="Bengaluru",
    )
    applicant_2 = await svc.register_applicant(tenant.id, app_req_2, admin.id)
    assert applicant_2.is_duplicate is True
    assert applicant_2.verification_status == ApplicantVerificationStatus.FLAGGED_DUPLICATE
    assert applicant_2.merged_into_applicant_id == applicant_1.id

    # Test merge operation
    merged_target = await svc.merge_applicants(
        tenant.id,
        source_applicant_id=applicant_2.id,
        target_applicant_id=applicant_1.id,
        reason="Duplicate registration with identical identity evidence",
        author_id=admin.id,
    )
    assert merged_target.id == applicant_1.id

    # Refetch applicant 2 to verify merged state
    re_app2 = await svc.get_applicant(tenant.id, applicant_2.id)
    assert re_app2.is_duplicate is True
    assert re_app2.merged_into_applicant_id == applicant_1.id
    assert re_app2.merge_reason is not None


# =============================================================================
# 3. APPLICATION WORKFLOW & CORRECTION WINDOWS
# =============================================================================


@pytest.mark.asyncio
async def test_application_lifecycle_submission_and_correction_window(
    db_session: AsyncSession, admissions_fixture: dict
):
    """Test application drafting, auto score computation, submission, correction window enforcement, and withdrawal."""
    tenant = admissions_fixture["tenant_a"]
    admin = admissions_fixture["admin_a"]
    prog = admissions_fixture["prog_a"]
    ay = admissions_fixture["ay_a"]
    svc = AdmissionsService(db_session)
    uid = uuid.uuid4().hex[:4]

    cycle = await svc.create_cycle(
        tenant.id,
        AdmissionCycleCreate(
            academic_year_id=ay.id,
            code=f"APP-CYC-{uid}",
            name="UG Cycle 2026",
            application_start_date=date.today() - timedelta(days=5),
            application_end_date=date.today() + timedelta(days=30),
            document_deadline=date.today() + timedelta(days=35),
            offer_acceptance_deadline=date.today() + timedelta(days=40),
        ),
        admin.id,
    )

    applicant = await svc.register_applicant(
        tenant.id,
        ApplicantProfileCreate(
            first_name="Alice",
            last_name="Smith",
            email=f"alice.{uid}@test.edu",
            phone_number="+919876543211",
            date_of_birth=date(2005, 8, 20),
            gender="FEMALE",
        ),
        admin.id,
    )

    # 1. Create draft application with scores
    app_req = AdmissionApplicationCreate(
        cycle_id=cycle.id,
        applicant_id=applicant.id,
        program_id=prog.id,
        admission_category="GENERAL",
        qualifying_exam_name="12th Grade CBSE",
        qualifying_exam_score=Decimal("450.00"),
        qualifying_exam_max_score=Decimal("500.00"),
    )
    application = await svc.create_application(tenant.id, app_req, admin.id)
    assert application.status == ApplicationStatus.DRAFT
    # Check percentage auto-calculated: 450/500 = 90%
    assert application.qualifying_percentage == Decimal("90.00")

    # 2. Submit application
    submitted_app = await svc.submit_application(tenant.id, application.id, admin.id)
    assert submitted_app.status == ApplicationStatus.SUBMITTED
    assert submitted_app.submitted_at is not None

    # Verify cycle application counter incremented
    re_cycle = await svc.get_cycle(tenant.id, cycle.id)
    assert re_cycle.total_applications_count == 1

    # 3. Attempt edit after submission without correction window -> fails
    with pytest.raises(Exception):
        await svc.update_application(
            tenant.id,
            application.id,
            AdmissionApplicationUpdate(notes="Attempted edit"),
            admin.id,
        )

    # 4. Admin reopens application with 48h correction window
    reopened = await svc.reopen_application(
        tenant.id,
        application.id,
        reason="Applicant requested document re-upload correction",
        correction_hours=48,
        author_id=admin.id,
    )
    assert reopened.correction_window_end is not None

    # Now edit succeeds
    updated = await svc.update_application(
        tenant.id,
        application.id,
        AdmissionApplicationUpdate(notes="Corrected during window"),
        admin.id,
    )
    assert updated.notes == "Corrected during window"

    # 5. Withdraw application
    withdrawn = await svc.withdraw_application(
        tenant.id, application.id, reason="Joining another university", author_id=admin.id
    )
    assert withdrawn.status == ApplicationStatus.WITHDRAWN
    assert withdrawn.withdrawal_reason == "Joining another university"


# =============================================================================
# 4. DOCUMENT REQUIREMENTS & VERIFICATION
# =============================================================================


@pytest.mark.asyncio
async def test_document_requirements_upload_and_verification(
    db_session: AsyncSession, admissions_fixture: dict
):
    """Test document requirements definition, applicant file uploads, and reviewer verification."""
    tenant = admissions_fixture["tenant_a"]
    admin = admissions_fixture["admin_a"]
    prog = admissions_fixture["prog_a"]
    ay = admissions_fixture["ay_a"]
    svc = AdmissionsService(db_session)
    uid = uuid.uuid4().hex[:4]

    cycle = await svc.create_cycle(
        tenant.id,
        AdmissionCycleCreate(
            academic_year_id=ay.id,
            code=f"DOC-CYC-{uid}",
            name="Document Cycle",
            application_start_date=date.today(),
            application_end_date=date.today() + timedelta(days=20),
            document_deadline=date.today() + timedelta(days=25),
            offer_acceptance_deadline=date.today() + timedelta(days=30),
        ),
        admin.id,
    )

    req = await svc.create_document_requirement(
        tenant.id,
        ApplicationDocumentRequirementCreate(
            cycle_id=cycle.id,
            program_id=prog.id,
            document_name="High School Marksheet",
            document_code="HS_MARKSHEET",
            is_mandatory=True,
        ),
        admin.id,
    )
    assert req.id is not None
    assert req.is_mandatory is True

    # Register applicant and create application
    applicant = await svc.register_applicant(
        tenant.id,
        ApplicantProfileCreate(
            first_name="Bob",
            last_name="Johnson",
            email=f"bob.{uid}@test.edu",
            phone_number="+919876543212",
            date_of_birth=date(2005, 3, 10),
            gender="MALE",
        ),
        admin.id,
    )
    app = await svc.create_application(
        tenant.id,
        AdmissionApplicationCreate(cycle_id=cycle.id, applicant_id=applicant.id, program_id=prog.id),
        admin.id,
    )

    # Upload document
    doc = await svc.upload_document(
        tenant.id,
        app.id,
        ApplicationDocumentUpload(
            requirement_id=req.id,
            document_name="High School Marksheet",
            file_name="marksheet_grade12.pdf",
            file_size_bytes=1024500,
            mime_type="application/pdf",
            storage_key=f"admissions/{tenant.id}/{app.id}/marksheet.pdf",
        ),
        admin.id,
    )
    assert doc.verification_status == DocumentVerificationStatus.PENDING

    # Reviewer verifies document
    verified = await svc.verify_document(
        tenant.id,
        doc.id,
        ApplicationDocumentVerify(verification_status=DocumentVerificationStatus.VERIFIED),
        admin.id,
    )
    assert verified.verification_status == DocumentVerificationStatus.VERIFIED
    assert verified.verified_by_user_id == admin.id
    assert verified.verified_at is not None


# =============================================================================
# 5. ELIGIBILITY EVALUATION & REVIEWS
# =============================================================================


@pytest.mark.asyncio
async def test_eligibility_rule_evaluation_and_academic_reviews(
    db_session: AsyncSession, admissions_fixture: dict
):
    """Test versioned eligibility evaluation engine and multi-stage academic reviews."""
    tenant = admissions_fixture["tenant_a"]
    admin = admissions_fixture["admin_a"]
    prog = admissions_fixture["prog_a"]
    ay = admissions_fixture["ay_a"]
    svc = AdmissionsService(db_session)
    uid = uuid.uuid4().hex[:4]

    cycle = await svc.create_cycle(
        tenant.id,
        AdmissionCycleCreate(
            academic_year_id=ay.id,
            code=f"ELG-CYC-{uid}",
            name="Eligibility Test Cycle",
            application_start_date=date.today(),
            application_end_date=date.today() + timedelta(days=20),
            document_deadline=date.today() + timedelta(days=25),
            offer_acceptance_deadline=date.today() + timedelta(days=30),
        ),
        admin.id,
    )

    # Create eligibility rule requiring minimum 65%
    rule = await svc.create_eligibility_rule(
        tenant.id,
        EligibilityRuleCreate(
            cycle_id=cycle.id,
            program_id=prog.id,
            code="BTECH_CSE_MIN65",
            name="B.Tech CSE Minimum Qualifying Cutoff",
            min_score_percentage=Decimal("65.00"),
        ),
        admin.id,
    )
    assert rule.min_score_percentage == Decimal("65.00")
    assert rule.rule_version == 1

    # Applicant 1: 82% (Eligible)
    app1 = await svc.register_applicant(
        tenant.id,
        ApplicantProfileCreate(
            first_name="High",
            last_name="Scorer",
            email=f"high.{uid}@test.edu",
            phone_number="+919876543213",
            date_of_birth=date(2005, 1, 1),
            gender="MALE",
        ),
        admin.id,
    )
    app_adm1 = await svc.create_application(
        tenant.id,
        AdmissionApplicationCreate(
            cycle_id=cycle.id,
            applicant_id=app1.id,
            program_id=prog.id,
            qualifying_percentage=Decimal("82.00"),
        ),
        admin.id,
    )
    eval1 = await svc.evaluate_eligibility(tenant.id, app_adm1.id, rule.id, admin.id)
    assert eval1.is_eligible is True
    re_app1 = await svc.get_application(tenant.id, app_adm1.id)
    assert re_app1.status == ApplicationStatus.ELIGIBLE

    # Applicant 2: 54% (Ineligible)
    app2 = await svc.register_applicant(
        tenant.id,
        ApplicantProfileCreate(
            first_name="Low",
            last_name="Scorer",
            email=f"low.{uid}@test.edu",
            phone_number="+919876543214",
            date_of_birth=date(2005, 2, 2),
            gender="FEMALE",
        ),
        admin.id,
    )
    app_adm2 = await svc.create_application(
        tenant.id,
        AdmissionApplicationCreate(
            cycle_id=cycle.id,
            applicant_id=app2.id,
            program_id=prog.id,
            qualifying_percentage=Decimal("54.00"),
        ),
        admin.id,
    )
    eval2 = await svc.evaluate_eligibility(tenant.id, app_adm2.id, rule.id, admin.id)
    assert eval2.is_eligible is False
    re_app2 = await svc.get_application(tenant.id, app_adm2.id)
    assert re_app2.status == ApplicationStatus.INELIGIBLE

    # Create academic review for eligible applicant
    rev = await svc.create_application_review(
        tenant.id,
        app_adm1.id,
        ApplicationReviewCreate(
            reviewer_user_id=admin.id,
            review_stage=ReviewStage.ACADEMIC_REVIEW,
            score=Decimal("85.00"),
            decision=ReviewDecision.RECOMMEND_ADMIT,
            decision_reason="Strong mathematics and science background",
            is_completed=True,
        ),
        admin.id,
    )
    assert rev.decision == ReviewDecision.RECOMMEND_ADMIT
    re_app1_post = await svc.get_application(tenant.id, app_adm1.id)
    assert re_app1_post.status == ApplicationStatus.SHORTLISTED


# =============================================================================
# 6. SEAT ALLOCATION & SELECTION RUN
# =============================================================================


@pytest.mark.asyncio
async def test_seat_allocation_merit_ranking_and_selection_run(
    db_session: AsyncSession, admissions_fixture: dict
):
    """Test seat allocations, merit ranking ordering by score DESC, and selection cutoffs."""
    tenant = admissions_fixture["tenant_a"]
    admin = admissions_fixture["admin_a"]
    prog = admissions_fixture["prog_a"]
    ay = admissions_fixture["ay_a"]
    svc = AdmissionsService(db_session)
    uid = uuid.uuid4().hex[:4]

    cycle = await svc.create_cycle(
        tenant.id,
        AdmissionCycleCreate(
            academic_year_id=ay.id,
            code=f"SEL-CYC-{uid}",
            name="Selection Run Cycle",
            application_start_date=date.today(),
            application_end_date=date.today() + timedelta(days=20),
            document_deadline=date.today() + timedelta(days=25),
            offer_acceptance_deadline=date.today() + timedelta(days=30),
        ),
        admin.id,
    )

    # Capacity = 2
    alloc = await svc.create_seat_allocation(
        tenant.id,
        SeatAllocationCreate(
            cycle_id=cycle.id,
            program_id=prog.id,
            admission_category="GENERAL",
            total_capacity=2,
            waitlist_capacity=5,
        ),
        admin.id,
    )
    assert alloc.total_capacity == 2

    # Create 3 candidates: scores 95%, 85%, 72%
    scores = [Decimal("95.00"), Decimal("85.00"), Decimal("72.00")]
    for i, s in enumerate(scores):
        appl = await svc.register_applicant(
            tenant.id,
            ApplicantProfileCreate(
                first_name=f"Applicant_{i}",
                last_name="Rank",
                email=f"rank_{i}_{uid}@test.edu",
                phone_number=f"+9198765432{i}0",
                date_of_birth=date(2005, 4, 1),
                gender="OTHER",
            ),
            admin.id,
        )
        app_rec = await svc.create_application(
            tenant.id,
            AdmissionApplicationCreate(
                cycle_id=cycle.id,
                applicant_id=appl.id,
                program_id=prog.id,
                qualifying_percentage=s,
            ),
            admin.id,
        )
        await svc.submit_application(tenant.id, app_rec.id, admin.id)

    # Execute selection run
    run = await svc.create_selection_run(
        tenant.id,
        SelectionRunCreate(
            cycle_id=cycle.id,
            program_id=prog.id,
            name="Round 1 Merit List",
        ),
        admin.id,
    )
    assert run.total_selected == 2
    assert run.total_waitlisted == 1

    # Approve and publish
    published_run = await svc.approve_and_publish_selection(tenant.id, run.id, admin.id)
    assert published_run.is_approved is True
    assert published_run.is_published is True


# =============================================================================
# 7. ADMISSION OFFERS & SEAT RESERVATION
# =============================================================================


@pytest.mark.asyncio
async def test_admission_offer_issuance_acceptance_decline_and_capacity_guard(
    db_session: AsyncSession, admissions_fixture: dict
):
    """Test offer issuance with seat reservation, capacity enforcement, acceptance, and decline release."""
    tenant = admissions_fixture["tenant_a"]
    admin = admissions_fixture["admin_a"]
    prog = admissions_fixture["prog_a"]
    ay = admissions_fixture["ay_a"]
    svc = AdmissionsService(db_session)
    uid = uuid.uuid4().hex[:4]

    cycle = await svc.create_cycle(
        tenant.id,
        AdmissionCycleCreate(
            academic_year_id=ay.id,
            code=f"OFR-CYC-{uid}",
            name="Offer Cycle",
            application_start_date=date.today(),
            application_end_date=date.today() + timedelta(days=20),
            document_deadline=date.today() + timedelta(days=25),
            offer_acceptance_deadline=date.today() + timedelta(days=30),
        ),
        admin.id,
    )

    # Seat allocation: capacity = 1
    await svc.create_seat_allocation(
        tenant.id,
        SeatAllocationCreate(
            cycle_id=cycle.id,
            program_id=prog.id,
            admission_category="GENERAL",
            total_capacity=1,
            waitlist_capacity=2,
        ),
        admin.id,
    )

    # Create 2 applicants
    app1 = await svc.register_applicant(
        tenant.id,
        ApplicantProfileCreate(
            first_name="Candidate",
            last_name="One",
            email=f"cand1.{uid}@test.edu",
            phone_number="+919876543221",
            date_of_birth=date(2005, 5, 1),
            gender="FEMALE",
        ),
        admin.id,
    )
    appl1 = await svc.create_application(
        tenant.id,
        AdmissionApplicationCreate(cycle_id=cycle.id, applicant_id=app1.id, program_id=prog.id),
        admin.id,
    )

    app2 = await svc.register_applicant(
        tenant.id,
        ApplicantProfileCreate(
            first_name="Candidate",
            last_name="Two",
            email=f"cand2.{uid}@test.edu",
            phone_number="+919876543222",
            date_of_birth=date(2005, 6, 1),
            gender="MALE",
        ),
        admin.id,
    )
    appl2 = await svc.create_application(
        tenant.id,
        AdmissionApplicationCreate(cycle_id=cycle.id, applicant_id=app2.id, program_id=prog.id),
        admin.id,
    )

    # Issue offer 1: reserves the 1 available seat
    offer1 = await svc.issue_admission_offer(
        tenant.id,
        AdmissionOfferCreate(
            application_id=appl1.id,
            expiry_date=date.today() + timedelta(days=10),
            deposit_required=Decimal("50000.00"),
        ),
        admin.id,
    )
    assert offer1.offer_number.startswith("OFR-")
    assert offer1.status == OfferStatus.ISSUED

    # Check reserved seat
    alloc_check = await svc.get_seat_allocation(tenant.id, cycle.id, prog.id)
    assert alloc_check.reserved_seats == 1

    # Attempt to issue offer 2: capacity reached!
    with pytest.raises(Exception):
        await svc.issue_admission_offer(
            tenant.id,
            AdmissionOfferCreate(
                application_id=appl2.id,
                expiry_date=date.today() + timedelta(days=10),
            ),
            admin.id,
        )

    # Candidate 1 declines offer -> seat reservation released
    declined_offer = await svc.respond_to_offer(
        tenant.id,
        offer1.id,
        accept=False,
        decline_reason="Personal reasons",
        author_id=admin.id,
    )
    assert declined_offer.status == OfferStatus.DECLINED

    # Check reserved seat released back to 0
    alloc_released = await svc.get_seat_allocation(tenant.id, cycle.id, prog.id)
    assert alloc_released.reserved_seats == 0

    # Now offer 2 can be issued successfully!
    offer2 = await svc.issue_admission_offer(
        tenant.id,
        AdmissionOfferCreate(
            application_id=appl2.id,
            expiry_date=date.today() + timedelta(days=10),
        ),
        admin.id,
    )
    assert offer2.status == OfferStatus.ISSUED

    # Candidate 2 accepts offer
    accepted_offer = await svc.respond_to_offer(
        tenant.id, offer2.id, accept=True, decline_reason=None, author_id=admin.id
    )
    assert accepted_offer.status == OfferStatus.ACCEPTED


# =============================================================================
# 8. ENROLLMENT ORCHESTRATION & IDEMPOTENCY
# =============================================================================


@pytest.mark.asyncio
async def test_idempotent_enrollment_orchestration_and_student_record_creation(
    db_session: AsyncSession, admissions_fixture: dict
):
    """Test enrollment workflow creating StudentProfile, converting reserved seat to confirmed, and idempotency."""
    tenant = admissions_fixture["tenant_a"]
    admin = admissions_fixture["admin_a"]
    prog = admissions_fixture["prog_a"]
    batch = admissions_fixture["batch_a"]
    ay = admissions_fixture["ay_a"]
    svc = AdmissionsService(db_session)
    uid = uuid.uuid4().hex[:4]

    cycle = await svc.create_cycle(
        tenant.id,
        AdmissionCycleCreate(
            academic_year_id=ay.id,
            code=f"ENR-CYC-{uid}",
            name="Enrollment Cycle",
            application_start_date=date.today(),
            application_end_date=date.today() + timedelta(days=20),
            document_deadline=date.today() + timedelta(days=25),
            offer_acceptance_deadline=date.today() + timedelta(days=30),
        ),
        admin.id,
    )

    await svc.create_seat_allocation(
        tenant.id,
        SeatAllocationCreate(
            cycle_id=cycle.id,
            program_id=prog.id,
            admission_category="GENERAL",
            total_capacity=10,
            waitlist_capacity=5,
        ),
        admin.id,
    )

    applicant = await svc.register_applicant(
        tenant.id,
        ApplicantProfileCreate(
            first_name="Diana",
            last_name="Prince",
            email=f"diana.{uid}@themyscira.edu",
            phone_number="+919876543230",
            date_of_birth=date(2005, 7, 20),
            gender="FEMALE",
            emergency_contact_name="Hippolyta",
            emergency_contact_phone="+919876543231",
        ),
        admin.id,
    )
    app = await svc.create_application(
        tenant.id,
        AdmissionApplicationCreate(cycle_id=cycle.id, applicant_id=applicant.id, program_id=prog.id),
        admin.id,
    )
    offer = await svc.issue_admission_offer(
        tenant.id,
        AdmissionOfferCreate(
            application_id=app.id,
            expiry_date=date.today() + timedelta(days=15),
            deposit_required=Decimal("25000.00"),
        ),
        admin.id,
    )
    await svc.respond_to_offer(tenant.id, offer.id, accept=True, decline_reason=None, author_id=admin.id)

    # Initiate enrollment workflow
    idemp_key = f"IDEMP-ENR-{uid}"
    enr_payload = EnrollmentWorkflowInitiate(
        application_id=app.id,
        offer_id=offer.id,
        batch_id=batch.id,
        idempotency_key=idemp_key,
    )
    workflow = await svc.orchestrate_enrollment(tenant.id, enr_payload, admin.id)
    assert workflow.status == EnrollmentWorkflowStatus.COMPLETED
    assert workflow.student_id is not None
    assert workflow.created_student_admission_number is not None

    # Verify student profile created
    std_stmt = select(StudentProfile).where(StudentProfile.id == workflow.student_id)
    student = (await db_session.execute(std_stmt)).scalar_one()
    assert student.admission_number == workflow.created_student_admission_number
    assert student.program_id == prog.id
    assert student.batch_id == batch.id

    # Verify seat allocation converted: reserved -> confirmed
    alloc = await svc.get_seat_allocation(tenant.id, cycle.id, prog.id)
    assert alloc.confirmed_seats == 1
    assert alloc.reserved_seats == 0

    # Verify cycle enrolled counter incremented
    re_cycle = await svc.get_cycle(tenant.id, cycle.id)
    assert re_cycle.total_enrolled_count == 1

    # Test idempotency: re-running with the SAME idempotency key returns existing workflow without duplicate
    wf_retry = await svc.orchestrate_enrollment(tenant.id, enr_payload, admin.id)
    assert wf_retry.id == workflow.id
    assert wf_retry.student_id == workflow.student_id

    # Verify no duplicate student profiles were created
    all_students_stmt = select(StudentProfile).where(
        StudentProfile.tenant_id == tenant.id,
        StudentProfile.emergency_contact_name == "Hippolyta",
    )
    students = (await db_session.execute(all_students_stmt)).scalars().all()
    assert len(students) == 1


# =============================================================================
# 9. POST-ENROLLMENT ONBOARDING CHECKLISTS & TASKS
# =============================================================================


@pytest.mark.asyncio
async def test_onboarding_checklist_and_task_lifecycle(
    db_session: AsyncSession, admissions_fixture: dict
):
    """Test automatic onboarding checklist generation upon enrollment and task completions."""
    tenant = admissions_fixture["tenant_a"]
    admin = admissions_fixture["admin_a"]
    prog = admissions_fixture["prog_a"]
    batch = admissions_fixture["batch_a"]
    ay = admissions_fixture["ay_a"]
    svc = AdmissionsService(db_session)
    uid = uuid.uuid4().hex[:4]

    cycle = await svc.create_cycle(
        tenant.id,
        AdmissionCycleCreate(
            academic_year_id=ay.id,
            code=f"ONB-CYC-{uid}",
            name="Onboarding Cycle",
            application_start_date=date.today(),
            application_end_date=date.today() + timedelta(days=20),
            document_deadline=date.today() + timedelta(days=25),
            offer_acceptance_deadline=date.today() + timedelta(days=30),
        ),
        admin.id,
    )

    applicant = await svc.register_applicant(
        tenant.id,
        ApplicantProfileCreate(
            first_name="Bruce",
            last_name="Wayne",
            email=f"bruce.{uid}@wayne.edu",
            phone_number="+919876543240",
            date_of_birth=date(2005, 2, 19),
            gender="MALE",
        ),
        admin.id,
    )
    app = await svc.create_application(
        tenant.id,
        AdmissionApplicationCreate(cycle_id=cycle.id, applicant_id=applicant.id, program_id=prog.id),
        admin.id,
    )
    offer = await svc.issue_admission_offer(
        tenant.id,
        AdmissionOfferCreate(
            application_id=app.id,
            expiry_date=date.today() + timedelta(days=15),
        ),
        admin.id,
    )
    await svc.respond_to_offer(tenant.id, offer.id, accept=True, decline_reason=None, author_id=admin.id)

    # Enroll student
    wf = await svc.orchestrate_enrollment(
        tenant.id,
        EnrollmentWorkflowInitiate(
            application_id=app.id,
            offer_id=offer.id,
            batch_id=batch.id,
            idempotency_key=f"IDEMP-ONB-{uid}",
        ),
        admin.id,
    )

    # Fetch onboarding checklist for student
    chk = await svc.get_student_onboarding(tenant.id, wf.student_id)
    assert chk.total_tasks == 5
    assert chk.completed_tasks == 0
    assert chk.status == OnboardingStatus.IN_PROGRESS
    assert len(chk.tasks) == 5

    # Complete tasks one by one
    for task in chk.tasks:
        updated_task = await svc.update_onboarding_task(
            tenant.id,
            task.id,
            OnboardingTaskUpdate(
                status=OnboardingStatus.COMPLETED,
                verification_notes="Verified by admissions office",
            ),
            admin.id,
        )
        assert updated_task.status == OnboardingStatus.COMPLETED

    # Refetch checklist to verify overall status is COMPLETED
    completed_chk = await svc.get_student_onboarding(tenant.id, wf.student_id)
    assert completed_chk.completed_tasks == 5
    assert completed_chk.status == OnboardingStatus.COMPLETED
    assert completed_chk.completed_at is not None


# =============================================================================
# 10. MULTI-TENANT ISOLATION & ANALYTICS
# =============================================================================


@pytest.mark.asyncio
async def test_multi_tenant_isolation_and_analytics(
    db_session: AsyncSession, admissions_fixture: dict
):
    """Test cross-tenant data isolation and funnel analytics metrics."""
    tenant_a = admissions_fixture["tenant_a"]
    admin_a = admissions_fixture["admin_a"]
    tenant_b = admissions_fixture["tenant_b"]
    ay_a = admissions_fixture["ay_a"]
    svc = AdmissionsService(db_session)
    uid = uuid.uuid4().hex[:4]

    # Create cycle in Tenant A
    cycle_a = await svc.create_cycle(
        tenant_a.id,
        AdmissionCycleCreate(
            academic_year_id=ay_a.id,
            code=f"ISO-A-{uid}",
            name="Tenant A Cycle",
            application_start_date=date.today(),
            application_end_date=date.today() + timedelta(days=20),
            document_deadline=date.today() + timedelta(days=25),
            offer_acceptance_deadline=date.today() + timedelta(days=30),
        ),
        admin_a.id,
    )

    # Tenant B cannot access Tenant A's cycle
    with pytest.raises(Exception):
        await svc.get_cycle(tenant_b.id, cycle_a.id)

    # Test Analytics for Tenant A
    analytics = await svc.get_admissions_analytics(tenant_a.id)
    assert "total_applicants" in analytics
    assert "total_applications" in analytics
    assert "conversion_rate_percentage" in analytics
    assert "seat_utilization_percentage" in analytics
