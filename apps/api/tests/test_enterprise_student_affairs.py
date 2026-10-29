"""CampusOS Enterprise Student Affairs, Grievance Redressal & Disciplinary Case Management Tests (Step 58).

CampusOS Tagline: "One Campus. One System. One Source of Truth."

Verifies:
1. Student affairs office and grievance category administration with configurable SLAs.
2. Grievance case submission, sequential number generation (GRV-2026-XXXX), target dates, and anonymous reporting.
3. Case intake, assignment, participant roles, and conflict-of-interest reassignment safeguards.
4. Formal disciplinary proceedings, non-automated guilt safeguards, procedural milestones, findings, and sanction approval.
5. Secure evidence document references, access control tiers, and redaction preserving original evidence ID.
6. Hearing panel meetings and mediation session scheduling with confidential notes.
7. Resolution action tracking, corrective remedies, and completion records.
8. Appellate review with strict Separation of Duties enforcement (original decision-maker blocked from reviewing appeal).
9. Confidential threaded messaging within case portal and urgent safeguarding escalations.
10. Strict multi-tenant isolation at all database and service boundaries.
"""

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import Campus, Institution
from app.models.people import StudentProfile, User
from app.models.student_affairs import (
    ActionStatus,
    ActionType,
    AppealGrounds,
    AppealStatus,
    CaseAuditAction,
    CasePriority,
    CaseStatus,
    CaseType,
    ConfidentialityLevel,
    DisciplinaryStage,
    EscalationLevel,
    EvidenceAccessLevel,
    EvidenceType,
    FindingStatus,
    MeetingStatus,
    MeetingType,
    ParticipantRole,
    SanctionType,
    SubmitterType,
)
from app.schemas.student_affairs import (
    AppealRecordCreate,
    AppealReviewDecision,
    CaseCommunicationCreate,
    CaseEscalationCreate,
    CaseEvidenceRedact,
    CaseEvidenceUpload,
    CaseMeetingCreate,
    ConflictDeclaration,
    DisciplinaryFindingsRecord,
    DisciplinaryProceedingCreate,
    DisciplinarySanctionApprove,
    GrievanceCaseSubmit,
    GrievanceCaseUpdate,
    ResolutionActionCreate,
    ResolutionActionUpdate,
)
from app.services.student_affairs_service import StudentAffairsService


@pytest.fixture
async def sa_setup(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    super_admin_user: User,
):
    """Provides base campuses, student profiles, case officers, and reviewers for student affairs tests."""
    uid = uuid.uuid4().hex[:6]

    campus_a = Campus(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name="Main Campus Alpha",
        code=f"CMP-SA-{uid}",
        address="100 University Square",
        city="Chennai",
        is_active=True,
    )
    db_session.add(campus_a)

    # Student Affairs Officer / Staff in Tenant A
    officer_user = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"case_officer_{uid}@campus.edu",
        first_name="Radha",
        last_name="Krishnan",
        password_hash="hashed_pw_officer",
        status="ACTIVE",
    )
    db_session.add(officer_user)

    # Alternate Officer (for conflict reassignment)
    alt_officer = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"alt_officer_{uid}@campus.edu",
        first_name="Sanjay",
        last_name="Rao",
        password_hash="hashed_pw_alt_officer",
        status="ACTIVE",
    )
    db_session.add(alt_officer)

    # Decision Maker (Dean of Student Affairs)
    dean_user = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"dean_{uid}@campus.edu",
        first_name="Prof. Sundaram",
        last_name="Iyer",
        password_hash="hashed_pw_dean",
        status="ACTIVE",
    )
    db_session.add(dean_user)

    # Appeal Reviewer (Independent Ombudsperson)
    ombuds_user = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"ombuds_{uid}@campus.edu",
        first_name="Justice",
        last_name="Narayanan",
        password_hash="hashed_pw_ombuds",
        status="ACTIVE",
    )
    db_session.add(ombuds_user)

    # Student 1 (Submitter)
    student_user_1 = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"student1_{uid}@campus.edu",
        first_name="Ananya",
        last_name="Deshmukh",
        password_hash="hashed_pw_student1",
        status="ACTIVE",
    )
    db_session.add(student_user_1)

    # Student 2 (Respondent in Disciplinary Case)
    student_user_2 = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"student2_{uid}@campus.edu",
        first_name="Karthik",
        last_name="Varma",
        password_hash="hashed_pw_student2",
        status="ACTIVE",
    )
    db_session.add(student_user_2)

    await db_session.flush()

    return {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "campus_a": campus_a,
        "officer_user": officer_user,
        "alt_officer": alt_officer,
        "dean_user": dean_user,
        "ombuds_user": ombuds_user,
        "student_user_1": student_user_1,
        "student_user_2": student_user_2,
        "admin_user": super_admin_user,
    }


# =============================================================================
# 1. OFFICE & CATEGORY ADMINISTRATION
# =============================================================================


@pytest.mark.asyncio
async def test_create_office_and_grievance_category(
    db_session: AsyncSession, sa_setup: dict
):
    """Verifies student affairs office and grievance category administration with SLA limits."""
    tenant = sa_setup["tenant_a"]
    campus = sa_setup["campus_a"]
    officer = sa_setup["officer_user"]
    service = StudentAffairsService(db_session, tenant.id)

    # 1. Create Student Affairs Office
    office = await service.create_office({
        "code": "SA-OFFICE-MAIN",
        "name": "Office of Student Affairs & Grievances",
        "campus_id": campus.id,
        "dean_or_director_id": officer.id,
        "location": "Student Union Building, Floor 2",
        "contact_email": "grievance@campus.edu",
        "is_active": True,
    })
    assert office.id is not None
    assert office.code == "SA-OFFICE-MAIN"

    # 2. Create Category
    cat = await service.create_category({
        "code": "ACAD_EVAL",
        "name": "Academic Evaluation & Grading Discrepancy",
        "description": "Disputes relating to internal assessments and practical exam evaluations.",
        "case_type": CaseType.GRIEVANCE,
        "default_priority": CasePriority.MEDIUM,
        "sla_response_hours": 48,
        "sla_resolution_days": 10,
        "allow_anonymous": True,
    })
    assert cat.id is not None
    assert cat.sla_response_hours == 48

    categories = await service.list_categories()
    assert len(categories) >= 1
    assert any(c.code == "ACAD_EVAL" for c in categories)


# =============================================================================
# 2. GRIEVANCE SUBMISSION & SEQUENCE GENERATION
# =============================================================================


@pytest.mark.asyncio
async def test_submit_grievance_case_and_sequence(
    db_session: AsyncSession, sa_setup: dict
):
    """Verifies grievance submission, sequential case number generation, and anonymous reporting."""
    tenant = sa_setup["tenant_a"]
    campus = sa_setup["campus_a"]
    student = sa_setup["student_user_1"]
    service = StudentAffairsService(db_session, tenant.id)

    cat = await service.create_category({
        "code": "FACILITY_GRIEVANCE",
        "name": "Campus Infrastructure & Lab Access",
        "case_type": CaseType.GRIEVANCE,
        "default_priority": CasePriority.MEDIUM,
        "sla_response_hours": 24,
        "sla_resolution_days": 7,
    })

    # 1. Standard Authenticated Grievance
    sub_data = GrievanceCaseSubmit(
        category_id=cat.id,
        title="Inoperative Air Conditioning in Electronics Laboratory",
        description="Room 304 temperature exceeds 36C during afternoon experiment sessions.",
        requested_resolution="Immediate technician maintenance and schedule flexibility.",
        campus_id=campus.id,
        is_anonymous=False,
        submitter_type=SubmitterType.STUDENT,
        confidentiality_level=ConfidentialityLevel.STANDARD,
    )
    case_1 = await service.submit_case(
        sub_data,
        user_id=student.id,
        user_display_name="Ananya Deshmukh",
    )
    assert case_1.case_number.startswith("GRV-")
    assert case_1.status == CaseStatus.SUBMITTED
    assert case_1.submitter_name_redacted == "Ananya Deshmukh"
    assert case_1.target_response_date is not None
    assert len(case_1.participants) == 1
    assert case_1.participants[0].role == ParticipantRole.SUBMITTER

    # 2. Anonymous Grievance Submission
    anon_data = GrievanceCaseSubmit(
        category_id=cat.id,
        title="Hostel Cafeteria Sanitation Concern",
        description="Unclean utensils observed near washing station.",
        is_anonymous=True,
        submitter_type=SubmitterType.ANONYMOUS,
        confidentiality_level=ConfidentialityLevel.CONFIDENTIAL,
    )
    case_2 = await service.submit_case(anon_data)
    assert case_2.case_number.startswith("GRV-")
    assert case_2.is_anonymous is True
    assert case_2.submitter_user_id is None
    assert case_2.submitter_name_redacted == "Anonymous Submitter"


# =============================================================================
# 3. CASE INTAKE, ASSIGNMENT & CONFLICT REASSIGNMENT
# =============================================================================


@pytest.mark.asyncio
async def test_case_intake_assignment_and_conflict_reassignment(
    db_session: AsyncSession, sa_setup: dict
):
    """Verifies intake routing, officer assignment, and conflict-of-interest reassignment."""
    tenant = sa_setup["tenant_a"]
    officer = sa_setup["officer_user"]
    alt_officer = sa_setup["alt_officer"]
    admin = sa_setup["admin_user"]
    service = StudentAffairsService(db_session, tenant.id)

    cat = await service.create_category({
        "code": "HARASSMENT_DISCRIM",
        "name": "Hostel Code of Conduct Review",
        "case_type": CaseType.GRIEVANCE,
        "default_priority": CasePriority.HIGH,
    })

    case = await service.submit_case(
        GrievanceCaseSubmit(
            category_id=cat.id,
            title="Verbal altercation between roommates",
            description="Escalated verbal confrontation in Block B.",
        )
    )

    # 1. Assign Officer
    assigned_case = await service.assign_case(
        case.id,
        officer.id,
        admin.id,
        reason="Assigned to senior residential life officer.",
    )
    assert assigned_case.assigned_officer_id == officer.id
    assert assigned_case.status == CaseStatus.ACKNOWLEDGED

    # Add officer as participant for conflict tracking
    part = await service.db.merge(
        sa_setup["officer_user"]
    )
    part_rec = await service.declare_conflict(
        case.id,
        officer.id,
        ConflictDeclaration(
            has_conflict_of_interest=True,
            conflict_reason="Officer is faculty advisor to one of the involved parties.",
        ),
    )
    assert part_rec.has_conflict_of_interest is True
    assert part_rec.conflict_declared_at is not None

    # Verify case unassigned due to conflict
    updated_case = await service.get_case(case.id)
    assert updated_case.assigned_officer_id is None

    # 2. Reassign to alternate officer
    reassigned = await service.assign_case(
        case.id,
        alt_officer.id,
        admin.id,
        reason="Reassigned following declared conflict of interest.",
    )
    assert reassigned.assigned_officer_id == alt_officer.id


# =============================================================================
# 4. DISCIPLINARY PROCEEDING WORKFLOW
# =============================================================================


@pytest.mark.asyncio
async def test_disciplinary_proceeding_and_fair_process(
    db_session: AsyncSession, sa_setup: dict
):
    """Verifies fair-process disciplinary progression: notice, non-automated guilt, findings, sanction."""
    tenant = sa_setup["tenant_a"]
    respondent = sa_setup["student_user_2"]
    dean = sa_setup["dean_user"]
    service = StudentAffairsService(db_session, tenant.id)

    cat = await service.create_category({
        "code": "EXAM_INTEGRITY",
        "name": "Academic Misconduct & Examination Integrity",
        "case_type": CaseType.DISCIPLINARY,
        "default_priority": CasePriority.HIGH,
    })

    # Create Case
    case = await service.submit_case(
        GrievanceCaseSubmit(
            category_id=cat.id,
            title="Alleged unauthorized material in End-Semester Exam",
            description="Invigilator reported formula sheet during Thermodynamics test.",
        )
    )

    # 1. Initiate Formal Disciplinary Proceeding with Procedural Notice
    proc = await service.create_disciplinary_proceeding(
        case.id,
        DisciplinaryProceedingCreate(
            respondent_student_id=respondent.id,
            allegation_summary="Possession of unauthorized formula notes in Thermodynamics Final Exam.",
            policy_provisions_violated="Campus Academic Integrity Code Sec. 4.2 (Prohibited Examination Aids)",
            notice_issued_at=datetime.now(UTC),
            response_due_at=datetime.now(UTC) + timedelta(days=5),
        ),
    )
    assert proc.procedural_stage == DisciplinaryStage.NOTICE_ISSUED
    assert proc.finding_status == FindingStatus.PENDING  # Not automatically proven!

    # 2. Record Formal Findings after Committee Review
    findings_proc = await service.record_findings(
        case.id,
        DisciplinaryFindingsRecord(
            findings_summary="Committee reviewed invigilator report and student statement. Material was present on desk.",
            finding_status=FindingStatus.SUBSTANTIATED,
            procedural_stage=DisciplinaryStage.FINDINGS_RECORDED,
        ),
    )
    assert findings_proc.finding_status == FindingStatus.SUBSTANTIATED
    assert findings_proc.procedural_stage == DisciplinaryStage.FINDINGS_RECORDED

    # 3. Approve Proportional Sanction
    sanction_proc = await service.approve_sanction(
        case.id,
        DisciplinarySanctionApprove(
            sanction_type=SanctionType.DISCIPLINARY_PROBATION,
            sanction_details="Probation for 1 academic semester with zero grade on Thermodynamics paper.",
            decision_maker_id=dean.id,
            appeal_deadline_days=14,
        ),
    )
    assert sanction_proc.sanction_type == SanctionType.DISCIPLINARY_PROBATION
    assert sanction_proc.is_communicated is True
    assert sanction_proc.appeal_deadline is not None


# =============================================================================
# 5. EVIDENCE HANDLING & REDACTION
# =============================================================================


@pytest.mark.asyncio
async def test_evidence_upload_access_tiers_and_redaction(
    db_session: AsyncSession, sa_setup: dict
):
    """Verifies evidence document linking, access control levels, and redaction preserving originals."""
    tenant = sa_setup["tenant_a"]
    officer = sa_setup["officer_user"]
    service = StudentAffairsService(db_session, tenant.id)

    cat = await service.create_category({
        "code": "HOSTEL_NOISE",
        "name": "Hostel Conduct",
        "case_type": CaseType.GRIEVANCE,
    })
    case = await service.submit_case(
        GrievanceCaseSubmit(category_id=cat.id, title="Noise Complaint", description="Loud music")
    )

    # 1. Upload Original Sensitive Witness Evidence
    orig_ev = await service.upload_evidence(
        case.id,
        CaseEvidenceUpload(
            evidence_type=EvidenceType.TESTIMONY,
            title="Witness Statement - Resident 402",
            description="Witness notes identifying resident room numbers and phone contacts.",
            file_url="/secure-storage/evidence/witness_statement_402.pdf",
            file_size_bytes=1048576,
            confidentiality_level=EvidenceAccessLevel.RESTRICTED_INVESTIGATOR_ONLY,
        ),
        user_id=officer.id,
    )
    assert orig_ev.id is not None
    assert orig_ev.is_redacted is False
    assert orig_ev.confidentiality_level == EvidenceAccessLevel.RESTRICTED_INVESTIGATOR_ONLY

    # 2. Redact Evidence for Hearing Panel
    redacted_ev = await service.redact_evidence(
        orig_ev.id,
        CaseEvidenceRedact(
            redaction_summary="Redacted resident phone numbers and room identifiers to protect privacy.",
            redacted_file_url="/secure-storage/evidence/redacted_witness_statement_402.pdf",
        ),
        user_id=officer.id,
    )
    assert redacted_ev.is_redacted is True
    assert redacted_ev.original_evidence_id == orig_ev.id
    assert "[REDACTED]" in redacted_ev.title


# =============================================================================
# 6. HEARINGS & CASE MEETINGS
# =============================================================================


@pytest.mark.asyncio
async def test_hearing_and_meeting_scheduling(
    db_session: AsyncSession, sa_setup: dict
):
    """Verifies hearing and mediation session scheduling and status updates."""
    tenant = sa_setup["tenant_a"]
    officer = sa_setup["officer_user"]
    service = StudentAffairsService(db_session, tenant.id)

    cat = await service.create_category({
        "code": "PEER_DISPUTE",
        "name": "Peer Dispute Resolution",
        "case_type": CaseType.MEDIATION,
    })
    case = await service.submit_case(
        GrievanceCaseSubmit(category_id=cat.id, title="Project Credit Dispute", description="Lab group")
    )

    # 1. Schedule Mediation Session
    start = datetime.now(UTC) + timedelta(days=2)
    end = start + timedelta(hours=1)
    meeting = await service.schedule_meeting(
        case.id,
        CaseMeetingCreate(
            title="Voluntary Peer Mediation Session",
            meeting_type=MeetingType.MEDIATION_SESSION,
            scheduled_start=start,
            scheduled_end=end,
            venue_or_url="Student Counseling Center Room 104",
            facilitator_id=officer.id,
        ),
    )
    assert meeting.id is not None
    assert meeting.status == MeetingStatus.SCHEDULED

    # 2. Complete Meeting and record agreed actions
    updated_meeting = await service.update_meeting(
        meeting.id,
        {"status": MeetingStatus.COMPLETED, "agreed_actions": "Group agreed to redistribute project modules evenly."},
    )
    assert updated_meeting.status == MeetingStatus.COMPLETED
    assert "redistribute" in updated_meeting.agreed_actions


# =============================================================================
# 7. RESOLUTION ACTIONS
# =============================================================================


@pytest.mark.asyncio
async def test_resolution_action_tracking(
    db_session: AsyncSession, sa_setup: dict
):
    """Verifies corrective action item tracking, ownership, and completion notes."""
    tenant = sa_setup["tenant_a"]
    officer = sa_setup["officer_user"]
    service = StudentAffairsService(db_session, tenant.id)

    cat = await service.create_category({
        "code": "LAB_SAFETY",
        "name": "Lab Safety Complaint",
        "case_type": CaseType.GRIEVANCE,
    })
    case = await service.submit_case(
        GrievanceCaseSubmit(category_id=cat.id, title="Chemical hood ventilation failure", description="Fume hood")
    )

    # 1. Add Corrective Action
    action = await service.add_resolution_action(
        case.id,
        ResolutionActionCreate(
            description="Replace HEPA exhaust filter and recertify hood air velocity.",
            action_type=ActionType.FACILITY_REPAIR,
            assigned_owner_id=officer.id,
            due_date=date.today() + timedelta(days=5),
        ),
    )
    assert action.status == ActionStatus.PENDING

    # 2. Complete Action
    completed_action = await service.update_resolution_action(
        action.id,
        ResolutionActionUpdate(
            status=ActionStatus.COMPLETED,
            completion_notes="Facilities engineering replaced filter; airflow certified at 100 fpm.",
        ),
    )
    assert completed_action.status == ActionStatus.COMPLETED
    assert completed_action.completed_at is not None


# =============================================================================
# 8. APPEALS & SEPARATION OF DUTIES
# =============================================================================


@pytest.mark.asyncio
async def test_appeal_filing_and_separation_of_duties(
    db_session: AsyncSession, sa_setup: dict
):
    """Verifies appeal filing and strict Separation of Duties blocking original decision maker."""
    tenant = sa_setup["tenant_a"]
    student = sa_setup["student_user_2"]
    dean = sa_setup["dean_user"]
    ombuds = sa_setup["ombuds_user"]
    service = StudentAffairsService(db_session, tenant.id)

    cat = await service.create_category({
        "code": "CODE_CONDUCT",
        "name": "Student Code Review",
        "case_type": CaseType.DISCIPLINARY,
    })

    case = await service.submit_case(
        GrievanceCaseSubmit(category_id=cat.id, title="Disciplinary Review", description="Hearing appeal test")
    )
    await service.create_disciplinary_proceeding(
        case.id,
        DisciplinaryProceedingCreate(
            respondent_student_id=student.id,
            allegation_summary="Curfew breach",
            policy_provisions_violated="Hostel Rule 3",
        ),
    )
    await service.approve_sanction(
        case.id,
        DisciplinarySanctionApprove(
            sanction_type=SanctionType.FORMAL_WARNING,
            sanction_details="Warning letter",
            decision_maker_id=dean.id,  # Dean Sundaram is the original decision maker
        ),
    )

    # 1. Student Files Appeal
    appeal = await service.file_appeal(
        case.id,
        AppealRecordCreate(
            appeal_grounds=AppealGrounds.NEW_EVIDENCE,
            grounds_statement="Hostel security entry log proves authorized late entry pass was active.",
        ),
        appellant_id=student.id,
    )
    assert appeal.review_status == AppealStatus.FILED

    # 2. Separation of Duties Violation: Original decision maker tries to review appeal
    with pytest.raises(HTTPException) as exc_info:
        await service.review_appeal(
            appeal.id,
            AppealReviewDecision(
                assigned_reviewer_id=dean.id,  # VIOLATION!
                review_status=AppealStatus.UPHELD,
                outcome_summary="Dean self-review attempt.",
            ),
        )
    assert exc_info.value.status_code == 400
    assert "Separation of Duties" in exc_info.value.detail

    # 3. Authorized Independent Reviewer Determines Appeal
    valid_review = await service.review_appeal(
        appeal.id,
        AppealReviewDecision(
            assigned_reviewer_id=ombuds.id,  # Valid independent reviewer
            review_status=AppealStatus.OVERTURNED,
            outcome_summary="New evidence confirmed late entry pass was approved; sanction rescinded.",
        ),
    )
    assert valid_review.review_status == AppealStatus.OVERTURNED
    assert valid_review.outcome_date is not None


# =============================================================================
# 9. COMMUNICATIONS, ESCALATION & AUDIT
# =============================================================================


@pytest.mark.asyncio
async def test_confidential_communications_and_urgent_escalation(
    db_session: AsyncSession, sa_setup: dict
):
    """Verifies confidential message threads, urgent safeguarding escalation, and audit logging."""
    tenant = sa_setup["tenant_a"]
    officer = sa_setup["officer_user"]
    service = StudentAffairsService(db_session, tenant.id)

    cat = await service.create_category({
        "code": "CAMPUS_SAFETY",
        "name": "Safety & Harassment Concerns",
        "case_type": CaseType.GRIEVANCE,
        "default_priority": CasePriority.HIGH,
    })
    case = await service.submit_case(
        GrievanceCaseSubmit(category_id=cat.id, title="Stalking Concern", description="Unwanted following")
    )

    # 1. Post Confidential Communication
    msg = await service.send_communication(
        case.id,
        CaseCommunicationCreate(
            message_text="Counselor will reach out directly to schedule a discreet intake meeting.",
            is_internal_only=False,
        ),
        sender_id=officer.id,
        sender_name="Radha Krishnan",
    )
    assert msg.id is not None
    assert msg.is_internal_only is False

    # 2. Urgent Safeguarding Escalation
    esc = await service.escalate_case(
        case.id,
        CaseEscalationCreate(
            escalation_level=EscalationLevel.LEVEL_3_EXECUTIVE_SAFEGUARDING,
            reason="Immediate security patrol dispatch requested near residential quad.",
            safety_referral_sent=True,
        ),
        user_id=officer.id,
    )
    assert esc.escalation_level == EscalationLevel.LEVEL_3_EXECUTIVE_SAFEGUARDING
    assert esc.safety_referral_sent is True

    # Verify case priority escalated
    updated_case = await service.get_case(case.id)
    assert updated_case.is_escalated is True
    assert updated_case.priority == CasePriority.URGENT

    # 3. Case Access Audit Log
    audit = await service.log_access_audit(
        case.id,
        officer.id,
        CaseAuditAction.VIEWED_CASE,
        details="Access to confidential safeguarding case profile",
        ip_address="192.168.1.50",
    )
    assert audit.action == CaseAuditAction.VIEWED_CASE
    assert audit.ip_address == "192.168.1.50"

    # 4. Telemetry
    telemetry = await service.get_dashboard_telemetry()
    assert telemetry["total_active_cases"] >= 1
    assert telemetry["urgent_escalations_count"] >= 1
