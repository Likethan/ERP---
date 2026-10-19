"""Step 37: Enterprise Product Adoption, Training, In-App Guidance & Change Management Test Suite.

Validates:
1. Role-Aware Onboarding Journeys & Ordered Step Execution
2. Persistent User Journey Progress Across Sessions and Devices
3. Modular Training Programs, Assignments, and Certification
4. Overdue Training Deadline Sweeper and Notifications
5. Route-Based Contextual In-App Guidance and Impression Tracking
6. Product Announcements, Targeted Change Notices & Mandatory Acknowledgements
7. Feature Adoption Targets and Server-Validated Milestones
8. Strict Multi-Tenant Isolation & Zero-Trust Authorization
9. Enablement Analytics, Drop-Off Funnels, and Aggregate Dashboards
10. REST API Endpoints with Role-Based Access Controls
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.models.adoption import (
    AdoptionJourneyDefinition,
    AdoptionJourneyStep,
    AdoptionMilestoneType,
    AdoptionTargetStatus,
    AnnouncementCategory,
    AnnouncementPriority,
    AnnouncementStatus,
    ContextualGuidance,
    FeatureAdoptionMilestone,
    FeatureAdoptionTarget,
    GuidanceStatus,
    GuidanceType,
    JourneyStatus,
    ProductAnnouncement,
    StepCompletionCriteria,
    TrainingAssignment,
    TrainingAssignmentStatus,
    TrainingModule,
    TrainingModuleContentType,
    TrainingProgram,
    TrainingProgramStatus,
    UserAnnouncementReceipt,
    UserGuidanceAction,
    UserGuidanceState,
    UserJourneyProgress,
    UserJourneyState,
)
from app.models.campus import Notification
from app.models.core import Institution
from app.models.people import User
from app.schemas.adoption import (
    AdoptionJourneyCreateRequest,
    AdoptionJourneyUpdateRequest,
    AnnouncementAcknowledgeRequest,
    ContextualGuidanceCreateRequest,
    FeatureAdoptionMilestoneRecordRequest,
    FeatureAdoptionTargetCreateRequest,
    JourneyStepCreateRequest,
    ProductAnnouncementCreateRequest,
    TrainingAssignRequest,
    TrainingModuleCreateRequest,
    TrainingProgramCreateRequest,
    UserGuidanceActionRequest,
    UserJourneyStepCompleteRequest,
)
from app.services.adoption_service import AdoptionService


def make_auth_headers(
    user: User,
    tenant_id: uuid.UUID,
    role_name: str = "INSTITUTION_ADMIN",
) -> dict[str, str]:
    """Helper to generate JWT bearer and cookie authorization headers."""
    token = create_access_token(
        user_id=user.id,
        tenant_id=tenant_id,
        email=user.email,
        roles=[role_name],
        permissions=["*"] if role_name in ("SUPER_ADMIN", "INSTITUTION_ADMIN") else [],
    )
    return {
        "Authorization": f"Bearer {token}",
        "Cookie": f"{ACCESS_TOKEN_COOKIE_NAME}={token}",
    }


# =============================================================================
# 1. ONBOARDING JOURNEYS & STEPS
# =============================================================================


@pytest.mark.asyncio
async def test_journey_creation_and_steps(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Verify journey creation with ordered steps and draft lifecycle status."""
    journey_req = AdoptionJourneyCreateRequest(
        code="STUDENT_INITIATION",
        title="Student Initiation Journey",
        description="Getting started on CampusOS",
        target_roles=["STUDENT"],
        product_version="v2.0",
        is_mandatory=True,
        steps=[
            JourneyStepCreateRequest(
                step_order=1,
                step_key="PROFILE_CONFIRM",
                title="Confirm Contact Info",
                completion_criteria="CONFIRM_CHECKLIST",
                route_path="/profile",
                estimated_duration_minutes=3,
                is_required=True,
            ),
            JourneyStepCreateRequest(
                step_order=2,
                step_key="TIMETABLE_VIEW",
                title="View Timetable",
                completion_criteria="VIEW_RESOURCE",
                route_path="/academics/timetable",
                estimated_duration_minutes=5,
                is_required=True,
            ),
            JourneyStepCreateRequest(
                step_order=3,
                step_key="EXPLORE_CLUBS",
                title="Browse Campus Clubs",
                completion_criteria="ACTION_COMPLETED",
                route_path="/campus/clubs",
                estimated_duration_minutes=10,
                is_required=False,
            ),
        ],
    )

    journey = await AdoptionService.create_journey(
        db=db_session,
        tenant_id=tenant_a.id,
        data=journey_req,
        current_user=tenant_admin_a,
    )
    await db_session.commit()

    assert journey.id is not None
    assert journey.code == "STUDENT_INITIATION"
    assert journey.status == JourneyStatus.DRAFT.value
    assert len(journey.steps) == 3
    assert journey.steps[0].step_key == "PROFILE_CONFIRM"
    assert journey.steps[1].step_order == 2
    assert not journey.steps[2].is_required


@pytest.mark.asyncio
async def test_journey_publication_and_archival(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Verify publishing transitions state and sets timestamp, then archival."""
    journey_req = AdoptionJourneyCreateRequest(
        code="FACULTY_START",
        title="Faculty Fast Start",
        target_roles=["FACULTY"],
        steps=[
            JourneyStepCreateRequest(
                step_order=1,
                step_key="FACULTY_PROFILE",
                title="Complete Teaching Profile",
            ),
        ],
    )
    journey = await AdoptionService.create_journey(
        db=db_session,
        tenant_id=tenant_a.id,
        data=journey_req,
        current_user=tenant_admin_a,
    )
    await db_session.commit()

    published = await AdoptionService.publish_journey(
        db=db_session,
        journey_id=journey.id,
        tenant_id=tenant_a.id,
        current_user=tenant_admin_a,
    )
    await db_session.commit()

    assert published.status == JourneyStatus.PUBLISHED.value
    assert published.published_at is not None

    archived = await AdoptionService.archive_journey(
        db=db_session,
        journey_id=journey.id,
        tenant_id=tenant_a.id,
        current_user=tenant_admin_a,
    )
    await db_session.commit()
    assert archived.status == JourneyStatus.ARCHIVED.value


@pytest.mark.asyncio
async def test_user_journey_progress_and_step_completion(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    faculty_user: User,
):
    """Verify progression tracking, percent recalculation, and journey completion."""
    journey_req = AdoptionJourneyCreateRequest(
        code="FACULTY_SETUP",
        title="Faculty Academic Setup",
        target_roles=["FACULTY"],
        steps=[
            JourneyStepCreateRequest(step_order=1, step_key="STEP_1", title="Step 1", is_required=True),
            JourneyStepCreateRequest(step_order=2, step_key="STEP_2", title="Step 2", is_required=True),
            JourneyStepCreateRequest(step_order=3, step_key="STEP_3", title="Step 3", is_required=False),
        ],
    )
    journey = await AdoptionService.create_journey(
        db=db_session,
        tenant_id=tenant_a.id,
        data=journey_req,
        current_user=tenant_admin_a,
    )
    await AdoptionService.publish_journey(db_session, journey.id, tenant_a.id, tenant_admin_a)
    await db_session.commit()

    # User initializes progress
    progress = await AdoptionService.get_or_initialize_user_progress(
        db=db_session,
        tenant_id=tenant_a.id,
        user_id=faculty_user.id,
        journey_id=journey.id,
    )
    await db_session.commit()

    assert progress.status == UserJourneyState.IN_PROGRESS.value
    assert progress.progress_pct == 0.0

    # User completes step 1
    prog_1 = await AdoptionService.complete_journey_step(
        db=db_session,
        tenant_id=tenant_a.id,
        user_id=faculty_user.id,
        journey_id=journey.id,
        step_key="STEP_1",
    )
    await db_session.commit()

    assert "STEP_1" in prog_1.completed_step_keys
    assert prog_1.progress_pct == 50.0  # 1 of 2 required steps completed
    assert prog_1.current_step_order == 2

    # User completes step 2 (all required steps done)
    prog_2 = await AdoptionService.complete_journey_step(
        db=db_session,
        tenant_id=tenant_a.id,
        user_id=faculty_user.id,
        journey_id=journey.id,
        step_key="STEP_2",
    )
    await db_session.commit()

    assert prog_2.progress_pct == 100.0
    assert prog_2.status == UserJourneyState.COMPLETED.value
    assert prog_2.completed_at is not None


@pytest.mark.asyncio
async def test_seed_default_onboarding_journeys(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Verify seeding standard onboarding journeys for Student, Faculty, and Admin."""
    seeded = await AdoptionService.seed_default_journeys(
        db=db_session,
        tenant_id=tenant_a.id,
        current_user=tenant_admin_a,
    )
    await db_session.commit()

    assert len(seeded) >= 3
    codes = {j.code for j in seeded}
    assert "STUDENT_ONBOARDING" in codes
    assert "FACULTY_ONBOARDING" in codes
    assert "ADMIN_OPERATIONS" in codes


# =============================================================================
# 2. TRAINING PROGRAMS & LEARNING ASSIGNMENTS
# =============================================================================


@pytest.mark.asyncio
async def test_training_program_creation_and_assignment(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    faculty_user: User,
):
    """Verify modular training program creation, publication, and notification dispatch upon assignment."""
    prog_req = TrainingProgramCreateRequest(
        code="CYBER_SECURITY_101",
        title="Campus Security & Privacy Essentials",
        description="Mandatory annual security awareness training",
        category="COMPLIANCE",
        target_roles=["FACULTY", "STAFF"],
        estimated_duration_minutes=45,
        is_mandatory=True,
        completion_rule="ALL_MODULES",
        modules=[
            TrainingModuleCreateRequest(
                module_order=1,
                module_key="MOD_PASSWORDS",
                title="Strong Credentials & MFA",
                content_type="TEXT_INSTRUCTION",
                content_body="Guidelines for choosing secure passwords...",
                estimated_duration_minutes=15,
                is_required=True,
            ),
            TrainingModuleCreateRequest(
                module_order=2,
                module_key="MOD_PHISHING",
                title="Recognizing Phishing Attacks",
                content_type="EXTERNAL_LINK",
                external_url="https://training.campusos.org/phishing-guide",
                estimated_duration_minutes=30,
                is_required=True,
            ),
        ],
    )

    program = await AdoptionService.create_training_program(
        db=db_session,
        tenant_id=tenant_a.id,
        data=prog_req,
        current_user=tenant_admin_a,
    )
    await AdoptionService.publish_training_program(db_session, program.id, tenant_a.id, tenant_admin_a)
    await db_session.commit()

    assert program.status == TrainingProgramStatus.PUBLISHED.value
    assert len(program.modules) == 2

    # Assign program to faculty user
    due_date = datetime.now(UTC) + timedelta(days=14)
    assign_req = TrainingAssignRequest(
        program_id=program.id,
        user_ids=[faculty_user.id],
        due_date=due_date,
    )
    assignments = await AdoptionService.assign_training_program(
        db=db_session,
        tenant_id=tenant_a.id,
        data=assign_req,
        current_user=tenant_admin_a,
    )
    await db_session.commit()

    assert len(assignments) == 1
    assert assignments[0].user_id == faculty_user.id
    assert assignments[0].status == TrainingAssignmentStatus.ASSIGNED.value

    # Verify notification created for assigned user
    notif_stmt = select(Notification).where(
        Notification.recipient_user_id == faculty_user.id,
        Notification.type == "TRAINING_ASSIGNED",
    )
    notif = (await db_session.execute(notif_stmt)).scalar_one_or_none()
    assert notif is not None
    assert "Campus Security & Privacy Essentials" in notif.title


@pytest.mark.asyncio
async def test_training_module_completion_and_certification(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    faculty_user: User,
):
    """Verify completing modules triggers progress percentage updates and generates a certificate."""
    prog_req = TrainingProgramCreateRequest(
        code="EXAM_CONDUCT",
        title="Examination Invigilation Protocol",
        target_roles=["FACULTY"],
        modules=[
            TrainingModuleCreateRequest(module_order=1, module_key="INVIG_RULES", title="Rules & Protocol"),
        ],
    )
    program = await AdoptionService.create_training_program(
        db=db_session,
        tenant_id=tenant_a.id,
        data=prog_req,
        current_user=tenant_admin_a,
    )
    await AdoptionService.publish_training_program(db_session, program.id, tenant_a.id, tenant_admin_a)
    await db_session.commit()

    # Complete the module
    assignment = await AdoptionService.complete_training_module(
        db=db_session,
        tenant_id=tenant_a.id,
        user_id=faculty_user.id,
        program_id=program.id,
        module_key="INVIG_RULES",
        notes="Understood all protocols",
    )
    await db_session.commit()

    assert assignment.status == TrainingAssignmentStatus.COMPLETED.value
    assert assignment.progress_pct == 100.0
    assert assignment.certificate_reference is not None
    assert assignment.certificate_reference.startswith("CERT-CAMPUSOS-EXAM_CONDUCT")


@pytest.mark.asyncio
async def test_training_overdue_sweep(
    db_session: AsyncSession,
    tenant_a: Institution,
    faculty_user: User,
):
    """Verify past-deadline training assignments are swept to OVERDUE and notifications sent."""
    # Create an assigned training program past due date
    program = TrainingProgram(
        tenant_id=tenant_a.id,
        code="SAFETY_SWEEP",
        title="Fire Safety & Evacuation",
        status=TrainingProgramStatus.PUBLISHED.value,
        version=1,
    )
    db_session.add(program)
    await db_session.flush()

    past_due = datetime.now(UTC) - timedelta(days=2)
    assignment = TrainingAssignment(
        tenant_id=tenant_a.id,
        program_id=program.id,
        user_id=faculty_user.id,
        status=TrainingAssignmentStatus.ASSIGNED.value,
        due_date=past_due,
        completed_module_keys=[],
        module_progress_json={},
        progress_pct=0.0,
    )
    db_session.add(assignment)
    await db_session.commit()

    # Run sweeper
    res = await AdoptionService.evaluate_training_deadlines_and_reminders(db_session)
    await db_session.commit()

    assert res["overdue_processed"] >= 1
    await db_session.refresh(assignment)
    assert assignment.status == TrainingAssignmentStatus.OVERDUE.value

    # Verify overdue notification
    notif_stmt = select(Notification).where(
        Notification.recipient_user_id == faculty_user.id,
        Notification.type == "TRAINING_OVERDUE",
    )
    notif = (await db_session.execute(notif_stmt)).scalar_one_or_none()
    assert notif is not None
    assert notif.priority == "HIGH"


# =============================================================================
# 3. CONTEXTUAL IN-APP GUIDANCE
# =============================================================================


@pytest.mark.asyncio
async def test_contextual_guidance_routing_and_dismissal(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    faculty_user: User,
):
    """Verify route-based contextual guidance retrieval and optional dismissal logic."""
    guidance_req = ContextualGuidanceCreateRequest(
        guidance_key="ATTENDANCE_TUTORIAL",
        title="Quick Attendance Marking",
        content="Select the timetable session and mark students Present or Absent.",
        guidance_type="TOOLTIP",
        route_path="/academics/attendance",
        step_order=1,
        is_mandatory=False,
        target_roles=["FACULTY"],
    )
    guidance = await AdoptionService.create_contextual_guidance(
        db=db_session,
        tenant_id=tenant_a.id,
        data=guidance_req,
        current_user=tenant_admin_a,
    )
    await db_session.commit()

    # Query guidance on attendance route for faculty
    items = await AdoptionService.get_guidance_for_route(
        db=db_session,
        tenant_id=tenant_a.id,
        user_id=faculty_user.id,
        user_roles=["FACULTY"],
        route_path="/academics/attendance",
    )
    assert len(items) == 1
    assert items[0].guidance_key == "ATTENDANCE_TUTORIAL"

    # User dismisses guidance
    state = await AdoptionService.record_guidance_action(
        db=db_session,
        tenant_id=tenant_a.id,
        user_id=faculty_user.id,
        guidance_id=guidance.id,
        action="DISMISSED",
    )
    await db_session.commit()
    assert state.status == "DISMISSED"

    # Query again: dismissed optional guidance should now be excluded
    items_after = await AdoptionService.get_guidance_for_route(
        db=db_session,
        tenant_id=tenant_a.id,
        user_id=faculty_user.id,
        user_roles=["FACULTY"],
        route_path="/academics/attendance",
    )
    assert len(items_after) == 0


# =============================================================================
# 4. PRODUCT ANNOUNCEMENTS & CHANGE NOTICES
# =============================================================================


@pytest.mark.asyncio
async def test_announcement_publication_and_acknowledgement(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    faculty_user: User,
):
    """Verify product announcement creation, targeted visibility, and mandatory acknowledgement."""
    ann_req = ProductAnnouncementCreateRequest(
        announcement_code="POLICY_REV_2026",
        title="Updated Examination Grading Scale Policy",
        summary="Changes to relative grading thresholds",
        content="Please review the newly updated grading policy approved by the Academic Council.",
        category="POLICY_UPDATE",
        priority="HIGH",
        requires_acknowledgement=True,
        target_roles=["FACULTY"],
    )

    announcement = await AdoptionService.create_announcement(
        db=db_session,
        tenant_id=tenant_a.id,
        data=ann_req,
        current_user=tenant_admin_a,
    )
    await AdoptionService.publish_announcement(db_session, announcement.id, tenant_a.id, tenant_admin_a)
    await db_session.commit()

    # Faculty lists announcements
    user_announcements = await AdoptionService.list_user_announcements(
        db=db_session,
        tenant_id=tenant_a.id,
        user_id=faculty_user.id,
        user_roles=["FACULTY"],
    )
    assert len(user_announcements) == 1
    assert user_announcements[0].announcement_code == "POLICY_REV_2026"
    assert not user_announcements[0].user_is_acknowledged

    # Faculty acknowledges announcement
    receipt = await AdoptionService.acknowledge_announcement(
        db=db_session,
        tenant_id=tenant_a.id,
        user_id=faculty_user.id,
        announcement_id=announcement.id,
        notes="Read and understood",
    )
    await db_session.commit()

    assert receipt.is_acknowledged is True
    assert receipt.is_read is True
    assert receipt.acknowledged_at is not None


# =============================================================================
# 5. FEATURE ADOPTION TARGETS & MILESTONES
# =============================================================================


@pytest.mark.asyncio
async def test_feature_adoption_targets_and_milestones(
    db_session: AsyncSession,
    tenant_a: Institution,
    faculty_user: User,
):
    """Verify setting feature adoption targets and recording server-validated milestones."""
    start_date = datetime.now(UTC) - timedelta(days=1)
    end_date = datetime.now(UTC) + timedelta(days=30)

    target_req = FeatureAdoptionTargetCreateRequest(
        feature_key="DIGITAL_GRADEBOOK",
        feature_name="Interactive Digital Gradebook",
        target_roles=["FACULTY"],
        target_adoption_pct=75.0,
        window_start_date=start_date,
        window_end_date=end_date,
    )
    target = await AdoptionService.create_adoption_target(
        db=db_session,
        tenant_id=tenant_a.id,
        data=target_req,
    )
    await db_session.commit()

    assert target.feature_key == "DIGITAL_GRADEBOOK"
    assert target.target_adoption_pct == 75.0

    # Record first-use milestone
    ms_req = FeatureAdoptionMilestoneRecordRequest(
        feature_key="DIGITAL_GRADEBOOK",
        milestone_type="FIRST_USE",
        metadata={"course_id": str(uuid.uuid4())},
    )
    ms = await AdoptionService.record_adoption_milestone(
        db=db_session,
        tenant_id=tenant_a.id,
        user_id=faculty_user.id,
        data=ms_req,
    )
    await db_session.commit()

    assert ms.milestone_type == "FIRST_USE"

    # Idempotent re-recording should not duplicate
    ms_dup = await AdoptionService.record_adoption_milestone(
        db=db_session,
        tenant_id=tenant_a.id,
        user_id=faculty_user.id,
        data=ms_req,
    )
    await db_session.commit()
    assert ms_dup.id == ms.id


# =============================================================================
# 6. MULTI-TENANT ISOLATION
# =============================================================================


@pytest.mark.asyncio
async def test_multi_tenant_isolation_boundary(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    tenant_admin_a: User,
    tenant_admin_b: User,
):
    """Verify strict tenant isolation: Tenant B cannot access Tenant A's adoption content."""
    from fastapi import HTTPException

    # Create journey in Tenant A
    journey_req = AdoptionJourneyCreateRequest(
        code="ISOLATION_TEST",
        title="Tenant A Private Journey",
        steps=[JourneyStepCreateRequest(step_order=1, step_key="STEP_A", title="Step A")],
    )
    journey = await AdoptionService.create_journey(
        db=db_session,
        tenant_id=tenant_a.id,
        data=journey_req,
        current_user=tenant_admin_a,
    )
    await db_session.commit()

    # Tenant B tries to fetch Tenant A journey -> Forbidden
    with pytest.raises(HTTPException) as exc_info:
        await AdoptionService.get_journey_by_id(
            db=db_session,
            journey_id=journey.id,
            tenant_id=tenant_b.id,
        )
    assert exc_info.value.status_code == 403


# =============================================================================
# 7. ADOPTION ANALYTICS & DASHBOARD METRICS
# =============================================================================


@pytest.mark.asyncio
async def test_adoption_metrics_and_dashboard(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    faculty_user: User,
):
    """Verify drop-off calculations, completion rates, and summary dashboard KPIs."""
    # Create journey with 2 steps
    journey_req = AdoptionJourneyCreateRequest(
        code="METRICS_JOURNEY",
        title="Metrics Evaluation Journey",
        steps=[
            JourneyStepCreateRequest(step_order=1, step_key="METRIC_1", title="Metric 1", is_required=True),
            JourneyStepCreateRequest(step_order=2, step_key="METRIC_2", title="Metric 2", is_required=True),
        ],
    )
    journey = await AdoptionService.create_journey(db_session, tenant_a.id, journey_req, tenant_admin_a)
    await AdoptionService.publish_journey(db_session, journey.id, tenant_a.id, tenant_admin_a)

    # Faculty completes only step 1
    await AdoptionService.complete_journey_step(db_session, tenant_a.id, faculty_user.id, journey.id, "METRIC_1")
    await db_session.commit()

    metrics = await AdoptionService.get_journey_metrics(db_session, tenant_a.id, journey.id)
    assert metrics.started_count == 1
    assert metrics.completed_count == 0
    assert metrics.completion_rate_pct == 0.0
    assert len(metrics.step_metrics) == 2
    assert metrics.step_metrics[0].completed_users_count == 1
    assert metrics.step_metrics[1].completed_users_count == 0
    assert metrics.step_metrics[1].dropoff_rate_pct == 100.0

    # Summary dashboard
    summary = await AdoptionService.get_dashboard_summary(db_session, tenant_a.id)
    assert summary.active_journeys_count >= 1
    assert summary.tenant_id == tenant_a.id


# =============================================================================
# 8. REST API ENDPOINTS & RBAC CONTROLS
# =============================================================================


@pytest.mark.asyncio
async def test_adoption_rest_api_user_and_admin_flows(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    faculty_user: User,
):
    """Verify REST API: Admin creates and seeds; faculty user executes steps and views guidance."""
    admin_headers = make_auth_headers(tenant_admin_a, tenant_a.id, "INSTITUTION_ADMIN")
    faculty_headers = make_auth_headers(faculty_user, tenant_a.id, "FACULTY")

    # 1. Admin seeds default journeys
    seed_resp = await client.post("/api/v1/adoption/admin/journeys/seed-defaults", headers=admin_headers)
    assert seed_resp.status_code == 200
    seed_data = seed_resp.json()
    assert len(seed_data) >= 3

    # 2. Faculty retrieves journeys
    journeys_resp = await client.get("/api/v1/adoption/journeys", headers=faculty_headers)
    assert journeys_resp.status_code == 200
    journeys = journeys_resp.json()
    assert len(journeys) >= 1

    target_journey = journeys[0]
    journey_id = target_journey["id"]

    # 3. Faculty completes first step
    first_step_key = target_journey["steps"][0]["step_key"]
    comp_resp = await client.post(
        f"/api/v1/adoption/journeys/{journey_id}/steps/complete",
        headers=faculty_headers,
        json={"step_key": first_step_key, "notes": "Done via REST"},
    )
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()
    assert first_step_key in comp_data["completed_step_keys"]

    # 4. Faculty records feature milestone
    ms_resp = await client.post(
        "/api/v1/adoption/milestones",
        headers=faculty_headers,
        json={"feature_key": "ATTENDANCE_TRACKER", "milestone_type": "FIRST_USE"},
    )
    assert ms_resp.status_code == 201

    # 5. Non-admin forbidden from administrative endpoints
    forbidden_resp = await client.post(
        "/api/v1/adoption/admin/journeys",
        headers=faculty_headers,
        json={"code": "HACK_JOURNEY", "title": "Unauthorized"},
    )
    assert forbidden_resp.status_code == 403
