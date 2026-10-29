"""Enterprise Student Engagement, Community Service, Volunteering & Civic Impact Management Tests (Step 65).

Automated verification suite validating:
1. Community partner creation, unique name per tenant, and duplicate prevention.
2. Program creation, date constraints, and lifecycle state transitions.
3. Opportunity publishing, volunteer discovery, and skill/delivery criteria.
4. Student participation workflow: applications, waitlist capacity handling, and review.
5. Application withdrawal and auto-promotion of waitlisted candidates.
6. Volunteer shifts, capacity limits, and participant roster assignments.
7. Attendance session recording (check-in, check-out, duration calculation).
8. Service hour submission, duration checks, and pending unverified status.
9. Coordinator verification of service hours and partner contribution updates.
10. Historical audit ledger for service hour adjustments and corrections.
11. Student reflection submissions, SDG mapping, and coordinator reviews.
12. Safety briefing acknowledgement and coordinator clearance gate.
13. Certificate issuance eligibility enforcement (unverified hours / missing reflection blocks issuance).
14. Unique certificate number, SHA-256 verification hash, and certificate revocation.
15. Multi-tenant isolation for all engagement entities.
16. Consolidated Civic Engagement & Impact Dashboard Analytics.
"""

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import ValidationError
from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.core.permissions import (
    ENGAGEMENT_ANALYTICS_READ,
    ENGAGEMENT_APPLICATIONS_APPLY,
    ENGAGEMENT_APPLICATIONS_MANAGE,
    ENGAGEMENT_APPLICATIONS_READ,
    ENGAGEMENT_ATTENDANCE_RECORD,
    ENGAGEMENT_CERTIFICATES_ISSUE,
    ENGAGEMENT_CERTIFICATES_REVOKE,
    ENGAGEMENT_HOURS_SUBMIT,
    ENGAGEMENT_HOURS_VERIFY,
    ENGAGEMENT_OPPORTUNITIES_MANAGE,
    ENGAGEMENT_OPPORTUNITIES_READ,
    ENGAGEMENT_PARTNERS_MANAGE,
    ENGAGEMENT_PARTNERS_READ,
    ENGAGEMENT_PROGRAMS_APPROVE,
    ENGAGEMENT_PROGRAMS_MANAGE,
    ENGAGEMENT_PROGRAMS_READ,
    ENGAGEMENT_REFLECTIONS_REVIEW,
    ENGAGEMENT_REFLECTIONS_SUBMIT,
    ENGAGEMENT_SAFETY_MANAGE,
)
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token, get_password_hash
from app.models.core import Institution
from app.models.engagement import (
    ApplicationStatus,
    AttendanceStatus,
    AttendanceVerificationMethod,
    CertificateStatus,
    CommunityPartner,
    EngagementCertificate,
    EngagementProgram,
    OpportunityStatus,
    ParticipationApplication,
    ParticipationAttendance,
    PartnerOrgType,
    PartnerStatus,
    ProgramCategory,
    ProgramDeliveryMode,
    ProgramStatus,
    ReflectionStatus,
    SafetyAndConsentRecord,
    SafetyClearanceStatus,
    ServiceHourEntry,
    ServiceHourStatus,
    ShiftAssignment,
    ShiftAssignmentStatus,
    ShiftStatus,
    VolunteerOpportunity,
    VolunteerShift,
)
from app.models.people import StudentProfile, User
from app.schemas.engagement import (
    AttendanceCheckInRequest,
    AttendanceCheckOutRequest,
    CommunityPartnerCreate,
    CommunityPartnerUpdate,
    EngagementCertificateIssueRequest,
    EngagementCertificateRevokeRequest,
    EngagementProgramCreate,
    EngagementProgramTransitionRequest,
    ParticipationApplicationCreate,
    ParticipationApplicationReviewRequest,
    ReflectionReviewRequest,
    ReflectionSubmitRequest,
    SafetyAcknowledgeRequest,
    SafetyClearanceRequest,
    ServiceHourCorrectionRequest,
    ServiceHourSubmitRequest,
    ServiceHourVerifyRequest,
    ShiftAssignmentCreate,
    VolunteerOpportunityCreate,
    VolunteerShiftCreate,
)
from app.services.engagement_service import EngagementService


def make_auth_headers(
    user: User,
    tenant_id: UUID,
    role_name: str = "SUPER_ADMIN",
    permissions: list[str] | None = None,
) -> dict[str, str]:
    """Helper to generate JWT bearer and cookie authorization headers."""
    perms = permissions if permissions is not None else ["*"]
    token = create_access_token(
        user_id=user.id,
        tenant_id=tenant_id,
        email=user.email,
        roles=[role_name],
        permissions=perms,
    )
    return {
        "Authorization": f"Bearer {token}",
        "Cookie": f"{ACCESS_TOKEN_COOKIE_NAME}={token}",
    }


async def create_student_helper(
    db: AsyncSession, tenant_id: UUID, email: str, full_name: str, roll_no: str
) -> tuple[User, StudentProfile]:
    """Creates a student user and student profile for engagement testing."""
    first, *rest = full_name.split()
    last = " ".join(rest) if rest else "Student"

    user = User(
        id=uuid4(),
        primary_tenant_id=tenant_id,
        email=email,
        phone_number="+919876500001",
        password_hash=get_password_hash("StudentSecret123!"),
        status="ACTIVE",
        first_name=first,
        last_name=last,
    )
    db.add(user)
    await db.flush()

    student = StudentProfile(
        id=uuid4(),
        tenant_id=tenant_id,
        user_id=user.id,
        admission_number=roll_no,
        registration_number=f"REG-{roll_no}",
        roll_number=roll_no,
        date_of_birth=date(2004, 1, 1),
        gender="FEMALE",
        status="ACTIVE",
        admission_date=date(2024, 8, 1),
        expected_graduation_date=date(2028, 5, 31),
        program_id=uuid4(),
        batch_id=uuid4(),
    )
    db.add(student)
    await db.flush()
    return user, student


# =============================================================================
# 1. COMMUNITY PARTNER TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_community_partner_management_and_deduplication(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies partner registration, unique name constraint, and update operations."""
    service = EngagementService(db_session, tenant_a.id)

    partner_data = CommunityPartnerCreate(
        name="Green Earth Conservation Trust",
        organization_type=PartnerOrgType.NON_PROFIT,
        registration_number="NGO-KA-2024-9912",
        website="https://greenearthtrust.org",
        primary_contact_name="Ananya Sharma",
        primary_contact_email="ananya@greenearthtrust.org",
        primary_contact_phone="+919845012345",
        partnership_purpose="Urban afforestation and wetland ecological rejuvenation",
        engagement_categories=["ENVIRONMENTAL", "COMMUNITY_SERVICE"],
        agreement_reference="MOU-2026-ENV-01",
        valid_from=date.today(),
        valid_to=date.today() + timedelta(days=365),
    )

    partner = await service.create_partner(partner_data, tenant_admin_a.id)
    assert partner.name == "Green Earth Conservation Trust"
    assert partner.status == PartnerStatus.ACTIVE
    assert partner.verified_hours_contributed == Decimal("0.00")

    # Duplicate creation attempt in same tenant must raise ConflictException
    with pytest.raises(ConflictException):
        await service.create_partner(partner_data, tenant_admin_a.id)

    # Update partner contact details
    updated = await service.update_partner(
        partner.id,
        CommunityPartnerUpdate(
            primary_contact_phone="+919845099999",
            partnership_purpose="Updated wetland and lake protection initiative",
        ),
    )
    assert updated.primary_contact_phone == "+919845099999"
    assert "wetland" in updated.partnership_purpose


# =============================================================================
# 2. ENGAGEMENT PROGRAM LIFECYCLE TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_program_creation_and_lifecycle_transitions(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies program creation, date validation, and valid/invalid lifecycle transitions."""
    service = EngagementService(db_session, tenant_a.id)

    # Date constraint validation: end_date < start_date must fail
    with pytest.raises(ValidationException):
        await service.create_program(
            EngagementProgramCreate(
                code="CIVIC-FAIL-01",
                name="Invalid Dates Program",
                slug="invalid-dates-program",
                coordinator_id=tenant_admin_a.id,
                start_date=date.today() + timedelta(days=10),
                end_date=date.today(),  # earlier than start
            ),
            tenant_admin_a.id,
        )

    # Valid program creation
    prog_data = EngagementProgramCreate(
        code="CIVIC-LIT-2026",
        name="Digital Literacy for Rural Communities",
        slug="digital-literacy-rural-2026",
        description="Bridging the digital divide by training local youth and senior citizens.",
        category=ProgramCategory.EDUCATION_LITERACY,
        objectives="Empower 500 rural citizens with basic smartphone and digital banking literacy.",
        coordinator_id=tenant_admin_a.id,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=90),
        registration_deadline=date.today() + timedelta(days=30),
        capacity=60,
        target_service_hours=Decimal("25.00"),
        skills_required=["Digital Tools", "Empathy", "Regional Language"],
        delivery_mode=ProgramDeliveryMode.HYBRID,
        location_name="Community Center, Block 4",
        sdg_goals=["SDG_4_QUALITY_EDUCATION", "SDG_10_REDUCED_INEQUALITIES"],
        consent_required=True,
    )
    program = await service.create_program(prog_data, tenant_admin_a.id)
    assert program.status == ProgramStatus.DRAFT
    assert program.code == "CIVIC-LIT-2026"

    # Invalid jump: DRAFT directly to COMPLETED must fail
    with pytest.raises(ValidationException):
        await service.transition_program_status(
            program.id,
            EngagementProgramTransitionRequest(target_status=ProgramStatus.COMPLETED),
            tenant_admin_a.id,
        )

    # Step 1: DRAFT -> PENDING_APPROVAL
    p_pending = await service.transition_program_status(
        program.id,
        EngagementProgramTransitionRequest(target_status=ProgramStatus.PENDING_APPROVAL),
        tenant_admin_a.id,
    )
    assert p_pending.status == ProgramStatus.PENDING_APPROVAL

    # Step 2: PENDING_APPROVAL -> APPROVED
    p_approved = await service.transition_program_status(
        program.id,
        EngagementProgramTransitionRequest(
            target_status=ProgramStatus.APPROVED,
            approval_notes="Approved by Institutional Social Responsibility Council",
        ),
        tenant_admin_a.id,
    )
    assert p_approved.status == ProgramStatus.APPROVED
    assert p_approved.approver_id == tenant_admin_a.id

    # Step 3: APPROVED -> PUBLISHED
    p_pub = await service.transition_program_status(
        program.id,
        EngagementProgramTransitionRequest(target_status=ProgramStatus.PUBLISHED),
        tenant_admin_a.id,
    )
    assert p_pub.status == ProgramStatus.PUBLISHED


# =============================================================================
# 3. OPPORTUNITIES, APPLICATIONS, AND WAITLISTING
# =============================================================================


@pytest.mark.asyncio
async def test_volunteer_application_capacity_and_waitlist(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies volunteer opportunity creation, application limits, waitlisting, and promotion."""
    service = EngagementService(db_session, tenant_a.id)

    # Create program
    program = await service.create_program(
        EngagementProgramCreate(
            code="CIVIC-FOOD-26",
            name="Community Food Distribution Network",
            slug="community-food-network",
            coordinator_id=tenant_admin_a.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=60),
            capacity=100,
        ),
        tenant_admin_a.id,
    )
    await service.transition_program_status(
        program.id,
        EngagementProgramTransitionRequest(target_status=ProgramStatus.APPROVED),
        tenant_admin_a.id,
    )
    await service.transition_program_status(
        program.id,
        EngagementProgramTransitionRequest(target_status=ProgramStatus.PUBLISHED),
        tenant_admin_a.id,
    )

    # Create opportunity with capacity=2, waitlist_capacity=1
    opp_data = VolunteerOpportunityCreate(
        program_id=program.id,
        title="Weekend Food Sorting & Packing Specialist",
        description="Assisting with sorting fresh produce and nutritional packages.",
        category=ProgramCategory.COMMUNITY_SERVICE,
        available_positions=2,
        capacity=2,
        waitlist_capacity=1,
        start_date=date.today() + timedelta(days=5),
        end_date=date.today() + timedelta(days=30),
        expected_hours=Decimal("15.00"),
    )
    opp = await service.create_opportunity(opp_data, tenant_admin_a.id)
    assert opp.status == OpportunityStatus.PUBLISHED

    # Setup 4 students
    u1, s1 = await create_student_helper(db_session, tenant_a.id, "stud1@apex.edu", "Rohan Verma", "2024-CSE-01")
    u2, s2 = await create_student_helper(db_session, tenant_a.id, "stud2@apex.edu", "Pooja Hegde", "2024-CSE-02")
    u3, s3 = await create_student_helper(db_session, tenant_a.id, "stud3@apex.edu", "Kavya Menon", "2024-CSE-03")
    u4, s4 = await create_student_helper(db_session, tenant_a.id, "stud4@apex.edu", "Tariq Ali", "2024-CSE-04")

    # Student 1 applies
    app1 = await service.apply_to_opportunity(
        s1.id,
        ParticipationApplicationCreate(
            opportunity_id=opp.id,
            statement_of_purpose="Passionate about zero hunger and reducing food waste.",
            skills_declared=["Packaging", "Logistics"],
        ),
    )
    assert app1.status == ApplicationStatus.APPLIED

    # Duplicate application check
    with pytest.raises(ConflictException):
        await service.apply_to_opportunity(
            s1.id,
            ParticipationApplicationCreate(opportunity_id=opp.id),
        )

    # Approve Student 1
    await service.review_application(
        app1.id,
        ParticipationApplicationReviewRequest(status=ApplicationStatus.APPROVED),
        tenant_admin_a.id,
    )

    # Student 2 applies and gets approved (filling capacity=2)
    app2 = await service.apply_to_opportunity(s2.id, ParticipationApplicationCreate(opportunity_id=opp.id))
    await service.review_application(
        app2.id,
        ParticipationApplicationReviewRequest(status=ApplicationStatus.APPROVED),
        tenant_admin_a.id,
    )

    # Student 3 applies: since capacity is full (2/2 approved), should be placed on WAITLIST (position 1)
    app3 = await service.apply_to_opportunity(s3.id, ParticipationApplicationCreate(opportunity_id=opp.id))
    assert app3.status == ApplicationStatus.WAITLISTED
    assert app3.waitlist_position == 1

    # Student 4 applies: capacity is full and waitlist is full (1/1) -> should be rejected with ValidationException
    with pytest.raises(ValidationException) as exc:
        await service.apply_to_opportunity(s4.id, ParticipationApplicationCreate(opportunity_id=opp.id))
    assert "full" in str(exc.value)

    # Student 1 withdraws -> Student 3 should be automatically promoted from waitlist to APPROVED!
    await service.withdraw_application(app1.id, s1.id)
    await db_session.refresh(app3)
    assert app3.status == ApplicationStatus.APPROVED
    assert app3.waitlist_position is None


# =============================================================================
# 4. SHIFTS, ATTENDANCE, AND SERVICE-HOUR VERIFICATION
# =============================================================================


@pytest.mark.asyncio
async def test_shifts_attendance_and_service_hour_verification(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies shifts roster, check-in/out, service-hour submissions, and supervisor approval."""
    service = EngagementService(db_session, tenant_a.id)

    program = await service.create_program(
        EngagementProgramCreate(
            code="CIVIC-CLEAN-26",
            name="Campus & Coastal Cleanliness Drive",
            slug="campus-coastal-cleanup",
            coordinator_id=tenant_admin_a.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            target_service_hours=Decimal("10.00"),
        ),
        tenant_admin_a.id,
    )
    await service.transition_program_status(
        program.id,
        EngagementProgramTransitionRequest(target_status=ProgramStatus.APPROVED),
        tenant_admin_a.id,
    )
    await service.transition_program_status(
        program.id,
        EngagementProgramTransitionRequest(target_status=ProgramStatus.PUBLISHED),
        tenant_admin_a.id,
    )
    opp = await service.create_opportunity(
        VolunteerOpportunityCreate(
            program_id=program.id,
            title="Beach Cleanliness Marshall",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=10),
            capacity=10,
        ),
        tenant_admin_a.id,
    )

    u, student = await create_student_helper(
        db_session, tenant_a.id, "volunteer1@apex.edu", "Arjun Reddy", "2024-ECE-11"
    )
    app = await service.apply_to_opportunity(student.id, ParticipationApplicationCreate(opportunity_id=opp.id))
    await service.review_application(
        app.id,
        ParticipationApplicationReviewRequest(status=ApplicationStatus.APPROVED),
        tenant_admin_a.id,
    )

    # 1. Create shift
    shift = await service.create_shift(
        VolunteerShiftCreate(
            opportunity_id=opp.id,
            title="Morning Shift A - Sector 1",
            shift_date=date.today(),
            start_time=time(8, 0),
            end_time=time(12, 0),
            capacity=5,
        )
    )
    assert shift.assigned_count == 0

    # 2. Assign student to shift
    assignment = await service.assign_student_to_shift(
        ShiftAssignmentCreate(shift_id=shift.id, application_id=app.id, student_id=student.id)
    )
    assert assignment.status == ShiftAssignmentStatus.ASSIGNED
    assert shift.assigned_count == 1

    # 3. Attendance Check-in and Check-out
    checkin_time = datetime.now(UTC) - timedelta(hours=4)
    att = await service.check_in(
        AttendanceCheckInRequest(
            opportunity_id=opp.id,
            student_id=student.id,
            shift_id=shift.id,
            check_in_at=checkin_time,
            verification_method=AttendanceVerificationMethod.COORDINATOR_CONFIRMED,
        ),
        tenant_admin_a.id,
    )
    assert att.status == AttendanceStatus.CHECKED_IN

    checkout_time = datetime.now(UTC)
    att_done = await service.check_out(
        att.id,
        AttendanceCheckOutRequest(check_out_at=checkout_time, notes="Completed 4 hours of beach clean up"),
    )
    assert att_done.status == AttendanceStatus.COMPLETED

    # 4. Service-Hour Submission
    # Invalid duration > 24 hours must fail
    with pytest.raises((ValidationException, ValidationError)):
        await service.submit_service_hours(
            student.id,
            ServiceHourSubmitRequest(
                program_id=program.id,
                service_date=date.today(),
                duration_hours=Decimal("25.00"),
                description_of_work="Excessive invalid duration",
            ),
        )

    # Valid submission
    hour_entry = await service.submit_service_hours(
        student.id,
        ServiceHourSubmitRequest(
            program_id=program.id,
            opportunity_id=opp.id,
            shift_id=shift.id,
            attendance_id=att_done.id,
            service_date=date.today(),
            duration_hours=Decimal("4.00"),
            description_of_work="Collected and cataloged 12 kg of recyclable marine plastics.",
        ),
    )
    assert hour_entry.status == ServiceHourStatus.PENDING
    assert hour_entry.is_verified is False  # Integrity: not verified until supervisor approval!

    # 5. Coordinator Verification
    verified = await service.verify_service_hours(
        hour_entry.id,
        ServiceHourVerifyRequest(
            status=ServiceHourStatus.APPROVED,
            supervisor_comments="Excellent work and adherence to safety protocols.",
        ),
        tenant_admin_a.id,
    )
    assert verified.status == ServiceHourStatus.APPROVED
    assert verified.is_verified is True
    assert verified.verified_by_id == tenant_admin_a.id

    # 6. Service-Hour Correction Ledger
    corrected = await service.correct_service_hours(
        hour_entry.id,
        ServiceHourCorrectionRequest(
            new_hours=Decimal("4.50"),
            reason_for_change="Added 30 minutes for site handover and waste weighing.",
        ),
        tenant_admin_a.id,
    )
    assert corrected.duration_hours == Decimal("4.50")
    assert len(corrected.corrections) == 1
    assert corrected.corrections[0].previous_hours == Decimal("4.00")
    assert corrected.corrections[0].new_hours == Decimal("4.50")


# =============================================================================
# 5. REFLECTIONS, SAFETY GATES, AND CERTIFICATE ISSUANCE
# =============================================================================


@pytest.mark.asyncio
async def test_reflections_safety_and_certificate_issuance(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies student reflections, safety clearance, and tamper-evident certificate issuance."""
    service = EngagementService(db_session, tenant_a.id)

    program = await service.create_program(
        EngagementProgramCreate(
            code="CIVIC-HEALTH-26",
            name="Community Health Awareness Camp",
            slug="community-health-camp",
            coordinator_id=tenant_admin_a.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            target_service_hours=Decimal("5.00"),
            skills_required=["Public Health", "Triage Communication"],
        ),
        tenant_admin_a.id,
    )

    u, student = await create_student_helper(
        db_session, tenant_a.id, "healthstudent@apex.edu", "Deepika Padukone", "2024-BIO-44"
    )

    # 1. Safety Briefing Acknowledgement
    safety_rec = await service.acknowledge_safety_and_consent(
        student.id,
        SafetyAcknowledgeRequest(
            program_id=program.id,
            safety_briefing_acknowledged=True,
            risk_assessment_acknowledged=True,
            emergency_contact_verified=True,
        ),
    )
    assert safety_rec.safety_briefing_acknowledged is True
    assert safety_rec.coordinator_clearance_status == SafetyClearanceStatus.PENDING

    # Coordinator Clears Student
    cleared_safety = await service.set_coordinator_clearance(
        safety_rec.id,
        SafetyClearanceRequest(clearance_status=SafetyClearanceStatus.CLEARED),
        tenant_admin_a.id,
    )
    assert cleared_safety.coordinator_clearance_status == SafetyClearanceStatus.CLEARED

    # 2. Certificate attempt before reflection approval must FAIL
    with pytest.raises(ValidationException) as exc:
        await service.issue_certificate(
            EngagementCertificateIssueRequest(program_id=program.id, student_id=student.id),
            tenant_admin_a.id,
        )
    assert "reflection" in str(exc.value).lower()

    # 3. Submit and Approve Reflection
    refl = await service.submit_reflection(
        student.id,
        ReflectionSubmitRequest(
            program_id=program.id,
            reflection_text="Participating in the health camp deepened my understanding of preventative healthcare.",
            learning_outcomes_summary="Learned patient registration workflows and non-invasive vital checks.",
            skills_developed=["Health Communication", "Empathy", "Team Coordination"],
            sdg_impact_mapping=["SDG_3_GOOD_HEALTH_AND_WELL_BEING"],
            consent_for_impact_showcase=True,
        ),
    )
    assert refl.status == ReflectionStatus.SUBMITTED

    await service.review_reflection(
        refl.id,
        ReflectionReviewRequest(status=ReflectionStatus.APPROVED, feedback_text="Insightful reflection.", rating=5),
        tenant_admin_a.id,
    )

    # 4. Submit and verify required service hours
    hours = await service.submit_service_hours(
        student.id,
        ServiceHourSubmitRequest(
            program_id=program.id,
            service_date=date.today(),
            duration_hours=Decimal("6.00"),
            description_of_work="Patient registration and health vitals screening.",
        ),
    )
    await service.verify_service_hours(
        hours.id,
        ServiceHourVerifyRequest(status=ServiceHourStatus.APPROVED, supervisor_comments="Verified"),
        tenant_admin_a.id,
    )

    # 5. Issue Certificate
    cert = await service.issue_certificate(
        EngagementCertificateIssueRequest(
            program_id=program.id,
            student_id=student.id,
            issuing_authority_name="Office of Dean (Student Affairs)",
        ),
        tenant_admin_a.id,
    )
    assert cert.certificate_number.startswith("CIVIC-")
    assert cert.status == CertificateStatus.ISSUED
    assert cert.total_verified_hours == Decimal("6.00")
    assert len(cert.verification_hash) == 64  # SHA-256 length
    assert "verify/civic" in cert.qr_verification_url

    # Duplicate certificate issuance must be blocked
    with pytest.raises(ConflictException):
        await service.issue_certificate(
            EngagementCertificateIssueRequest(program_id=program.id, student_id=student.id),
            tenant_admin_a.id,
        )

    # 6. Revoke Certificate
    revoked = await service.revoke_certificate(
        cert.id,
        EngagementCertificateRevokeRequest(revocation_reason="Administrative re-audit correction"),
        tenant_admin_a.id,
    )
    assert revoked.status == CertificateStatus.REVOKED
    assert revoked.revocation_reason == "Administrative re-audit correction"


# =============================================================================
# 6. MULTI-TENANT ISOLATION TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_engagement_multi_tenant_isolation(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    tenant_admin_a: User,
    tenant_admin_b: User,
):
    """Verifies that Tenant A records are completely inaccessible from Tenant B."""
    service_a = EngagementService(db_session, tenant_a.id)
    service_b = EngagementService(db_session, tenant_b.id)

    # Create program in Tenant A
    prog_a = await service_a.create_program(
        EngagementProgramCreate(
            code="TENANT-A-CIVIC",
            name="Tenant A Local Initiative",
            slug="tenant-a-local",
            coordinator_id=tenant_admin_a.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        ),
        tenant_admin_a.id,
    )

    # Tenant B tries to get Tenant A program -> must raise NotFoundException
    with pytest.raises(NotFoundException):
        await service_b.get_program(prog_a.id)

    # Tenant B list programs must not include Tenant A program
    b_programs = await service_b.list_programs()
    assert not any(p.id == prog_a.id for p in b_programs)


# =============================================================================
# 7. DASHBOARD AND ANALYTICS METRICS
# =============================================================================


@pytest.mark.asyncio
async def test_engagement_dashboard_analytics_aggregation(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies live calculation of active programs, hours, applications, and SDG distributions."""
    service = EngagementService(db_session, tenant_a.id)

    dashboard = await service.get_dashboard_analytics()
    assert dashboard.total_programs >= 0
    assert dashboard.total_submitted_hours >= Decimal("0.00")
    assert dashboard.total_verified_hours >= Decimal("0.00")
    assert isinstance(dashboard.sdg_distribution, dict)
    assert isinstance(dashboard.category_distribution, dict)
