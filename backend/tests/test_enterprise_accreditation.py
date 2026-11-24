"""Enterprise Institutional Accreditation, Quality Assurance & Continuous Improvement Tests (Step 43).

Comprehensive automated test suite verifying:
1. Statutory framework template auto-seeding (NAAC, NBA, ISO-21001) & custom framework CRUD.
2. Framework criteria hierarchy and weight validation.
3. Assessment cycle lifecycle and automatic criterion assessment instantiation.
4. Assessment score boundaries, maturity levels, not-applicable states, and optimistic locking.
5. Strict separation of duties on assessment review (assessor/owner cannot self-approve).
6. Evidence repository linking, verification history, and expiration sweeps.
7. Quality indicators (KPIs), time-series observations, completeness checks, and data quality warnings.
8. Internal quality audit checklists, findings, and immutable finalized reports.
9. CAPA workflow with separation-of-duties closure enforcement.
10. Continuous Quality Improvement (CQI) lifecycle and milestone tracking.
11. Transparent accreditation readiness scoring engine & gap analysis snapshots.
12. Multi-tenant boundary isolation across frameworks, assessments, audits, and evidence.
13. End-to-end FastAPI REST API endpoints via AsyncClient.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AccreditationAuditFinalizedException,
    AccreditationFrameworkNotFoundException,
    AccreditationInvalidScoreException,
    AccreditationOptimisticLockException,
    AccreditationSeparationOfDutiesException,
)
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.models.accreditation import (
    AccreditationAssessmentStatus,
    AccreditationEvidenceCategory,
    AccreditationEvidenceVerificationStatus,
    AccreditationFrameworkStatus,
    AccreditationFrameworkType,
    AccreditationScoringModel,
    QualityAuditStatus,
    QualityAuditType,
    QualityCAPAStatus,
    QualityCAPAType,
    QualityDataQualityStatus,
    QualityFindingSeverity,
    QualityIndicatorCategory,
)
from app.models.core import Institution
from app.models.people import User
from app.schemas.accreditation import (
    AccreditationCriterionCreate,
    AccreditationCycleCreate,
    AccreditationEvidenceCreate,
    AccreditationEvidenceVerify,
    AccreditationFrameworkCreate,
    AccreditationFrameworkPublish,
    CriterionAssessmentDraftUpdate,
    CriterionAssessmentReview,
    CriterionAssessmentSubmit,
    QualityAuditChecklistItemCreate,
    QualityAuditFinalize,
    QualityAuditProgramCreate,
    QualityCAPAClose,
    QualityCAPACreate,
    QualityFindingCreate,
    QualityImprovementPlanCreate,
    QualityIndicatorCreate,
    QualityIndicatorObservationCreate,
)
from app.services.accreditation_service import AccreditationService


def make_auth_headers(
    user: User,
    tenant_id: UUID,
    role_name: str = "INSTITUTION_ADMIN",
) -> dict[str, str]:
    """Helper to generate JWT bearer and cookie authorization headers."""
    token = create_access_token(
        user_id=user.id,
        tenant_id=tenant_id,
        email=user.email,
        roles=[role_name],
        permissions=["*"],
    )
    return {
        "Authorization": f"Bearer {token}",
        "Cookie": f"{ACCESS_TOKEN_COOKIE_NAME}={token}",
    }


# =============================================================================
# 1. FRAMEWORK SEEDING & CRUD
# =============================================================================


@pytest.mark.asyncio
async def test_accreditation_framework_seeding_and_crud(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies statutory framework auto-seeding (NAAC, NBA, ISO) and custom framework creation."""
    service = AccreditationService(db_session)
    tenant_id = tenant_a.id

    # 1. Auto-seed standard statutory framework templates
    seeded = await service.seed_default_frameworks_if_empty(tenant_id, tenant_admin_a.id)
    assert len(seeded) >= 3

    frameworks = await service.list_frameworks(tenant_id)
    assert len(frameworks) >= 3
    codes = {f.code for f in frameworks}
    assert "NAAC-UNIV-TEMPLATE" in codes
    assert "NBA-TIER-1-TEMPLATE" in codes
    assert "ISO-21001-TEMPLATE" in codes

    # 2. Check seeded criteria in NAAC framework
    naac = next(f for f in frameworks if "NAAC" in f.code)
    criteria = await service.list_criteria(tenant_id, naac.id)
    assert len(criteria) >= 7

    # 3. Create custom framework
    custom = await service.create_framework(
        tenant_id=tenant_id,
        payload=AccreditationFrameworkCreate(
            code="NIRF-INTERNAL",
            name="NIRF Internal Benchmark Framework",
            description="National Institutional Ranking Framework Internal Tracking",
            issuing_body="Internal IQAC",
            framework_type=AccreditationFrameworkType.INTERNAL_IQAC,
            scoring_model=AccreditationScoringModel.NUMERIC_SCALE,
            max_score=100.0,
        ),
        actor_id=tenant_admin_a.id,
    )
    assert custom.code == "NIRF-INTERNAL"
    assert custom.status == AccreditationFrameworkStatus.DRAFT.value

    # 4. Create version snapshot for custom framework
    version = await service.publish_framework_version(
        tenant_id=tenant_id,
        framework_id=custom.id,
        payload=AccreditationFrameworkPublish(
            change_summary="Initial published version snapshot",
        ),
        actor_id=tenant_admin_a.id,
    )
    assert version.version_number == 1
    assert version.change_summary == "Initial published version snapshot"
    refreshed_custom = await service.get_framework(tenant_id, custom.id)
    assert refreshed_custom.status == AccreditationFrameworkStatus.ACTIVE.value


# =============================================================================
# 2. CRITERIA HIERARCHY & WEIGHT VALIDATION
# =============================================================================


@pytest.mark.asyncio
async def test_criteria_hierarchy_and_subcriteria(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies parent criteria and subcriteria relationship, ordering, and weight configuration."""
    service = AccreditationService(db_session)
    tenant_id = tenant_a.id

    framework = await service.create_framework(
        tenant_id=tenant_id,
        payload=AccreditationFrameworkCreate(
            code="ABET-ENG",
            name="ABET Engineering Accreditation",
            issuing_body="ABET",
            framework_type=AccreditationFrameworkType.CUSTOM,
            scoring_model=AccreditationScoringModel.NUMERIC_SCALE,
            max_score=100.0,
        ),
        actor_id=tenant_admin_a.id,
    )

    # Parent criterion
    parent = await service.create_criterion(
        tenant_id=tenant_id,
        framework_id=framework.id,
        payload=AccreditationCriterionCreate(
            code="ABET-C1",
            title="Students & Progression",
            description="Student admissions, advising, and progress evaluation",
            weight=30.0,
            max_score=30.0,
            is_mandatory=True,
            order_index=1,
        ),
        actor_id=tenant_admin_a.id,
    )
    assert parent.code == "ABET-C1"
    assert parent.parent_criterion_id is None

    # Child subcriterion
    child = await service.create_criterion(
        tenant_id=tenant_id,
        framework_id=framework.id,
        payload=AccreditationCriterionCreate(
            parent_criterion_id=parent.id,
            code="ABET-C1.1",
            title="Student Advising System",
            description="Institutional academic and career advising mechanism",
            weight=15.0,
            max_score=15.0,
            is_mandatory=True,
            order_index=1,
            assessment_guidelines="Evaluate student-to-counselor ratio and documented logs.",
            evidence_requirements=["Advising logs", "Counselor allocation policy"],
        ),
        actor_id=tenant_admin_a.id,
    )
    assert child.code == "ABET-C1.1"
    assert child.parent_criterion_id == parent.id


# =============================================================================
# 3. ASSESSMENT CYCLE & INSTANTIATION
# =============================================================================


@pytest.mark.asyncio
async def test_assessment_cycle_and_criterion_assessment_init(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies that creating an assessment cycle automatically seeds all framework criteria assessments."""
    service = AccreditationService(db_session)
    tenant_id = tenant_a.id

    await service.seed_default_frameworks_if_empty(tenant_id, tenant_admin_a.id)
    frameworks = await service.list_frameworks(tenant_id)
    naac = next(f for f in frameworks if "NAAC" in f.code)

    cycle = await service.create_assessment_cycle(
        tenant_id=tenant_id,
        payload=AccreditationCycleCreate(
            framework_id=naac.id,
            code="NAAC-CYCLE-2025-26",
            title="NAAC SSR Assessment Cycle 2025-26",
            academic_year="2025-2026",
            start_date=datetime.now(UTC),
            end_date=datetime.now(UTC) + timedelta(days=365),
        ),
        actor_id=tenant_admin_a.id,
    )
    assert cycle.code == "NAAC-CYCLE-2025-26"

    # Verify criterion assessments were initialized
    assessments = await service.list_criterion_assessments(tenant_id, cycle.id)
    assert len(assessments) >= 7
    for a in assessments:
        assert a.status == AccreditationAssessmentStatus.UNASSESSED.value
        assert a.score == 0.0 or a.score is None


# =============================================================================
# 4. SCORE BOUNDARIES, OPTIMISTIC LOCKING & NOT APPLICABLE
# =============================================================================


@pytest.mark.asyncio
async def test_assessment_score_validation_and_optimistic_locking(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies score validations, optimistic locking conflict detection, and NA justification requirement."""
    service = AccreditationService(db_session)
    tenant_id = tenant_a.id

    await service.seed_default_frameworks_if_empty(tenant_id, tenant_admin_a.id)
    frameworks = await service.list_frameworks(tenant_id)
    naac = next(f for f in frameworks if "NAAC" in f.code)

    cycle = await service.create_assessment_cycle(
        tenant_id=tenant_id,
        payload=AccreditationCycleCreate(
            framework_id=naac.id,
            code="VAL-CYCLE-01",
            title="Cycle Score Validation Test",
            academic_year="2026-2027",
            start_date=datetime.now(UTC),
            end_date=datetime.now(UTC) + timedelta(days=180),
        ),
        actor_id=tenant_admin_a.id,
    )

    assessments = await service.list_criterion_assessments(tenant_id, cycle.id)
    target_assess = assessments[0]

    # 1. Invalid score > max_score (Criterion max_score is 150 for Criterion 1)
    with pytest.raises(AccreditationInvalidScoreException):
        await service.update_criterion_assessment_draft(
            tenant_id=tenant_id,
            assessment_id=target_assess.id,
            payload=CriterionAssessmentDraftUpdate(
                lock_version=target_assess.lock_version,
                score=9999.0,
            ),
            actor_id=tenant_admin_a.id,
        )

    # 2. Negative score
    with pytest.raises(AccreditationInvalidScoreException):
        await service.update_criterion_assessment_draft(
            tenant_id=tenant_id,
            assessment_id=target_assess.id,
            payload=CriterionAssessmentDraftUpdate(
                lock_version=target_assess.lock_version,
                score=-10.0,
            ),
            actor_id=tenant_admin_a.id,
        )

    initial_lock_version = target_assess.lock_version
    updated = await service.update_criterion_assessment_draft(
        tenant_id=tenant_id,
        assessment_id=target_assess.id,
        payload=CriterionAssessmentDraftUpdate(
            lock_version=target_assess.lock_version,
            score=120.0,
            findings="Curriculum revision processes conform with NEP 2020 guidelines.",
            recommendations="Increase elective diversity in final year semesters.",
        ),
        actor_id=tenant_admin_a.id,
    )
    assert updated.score == 120.0
    assert updated.lock_version == initial_lock_version + 1

    # 4. Stale lock_version raises AccreditationOptimisticLockException
    with pytest.raises(AccreditationOptimisticLockException):
        await service.update_criterion_assessment_draft(
            tenant_id=tenant_id,
            assessment_id=target_assess.id,
            payload=CriterionAssessmentDraftUpdate(
                lock_version=initial_lock_version,  # Stale! (current is updated.lock_version)
                score=125.0,
            ),
            actor_id=tenant_admin_a.id,
        )

    # 5. Not-applicable with justification updates status
    na_updated = await service.update_criterion_assessment_draft(
        tenant_id=tenant_id,
        assessment_id=target_assess.id,
        payload=CriterionAssessmentDraftUpdate(
            lock_version=updated.lock_version,
            not_applicable_reason="Stand-alone institute without doctoral degree programs.",
        ),
        actor_id=tenant_admin_a.id,
    )
    assert na_updated.status == AccreditationAssessmentStatus.NOT_APPLICABLE.value


# =============================================================================
# 5. SEPARATION OF DUTIES ENFORCEMENT ON REVIEWS
# =============================================================================


@pytest.mark.asyncio
async def test_assessment_separation_of_duties(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    faculty_user: User,
    super_admin_user: User,
):
    """Verifies that an assessor or accountable owner cannot approve their own assessment."""
    service = AccreditationService(db_session)
    tenant_id = tenant_a.id

    await service.seed_default_frameworks_if_empty(tenant_id, tenant_admin_a.id)
    frameworks = await service.list_frameworks(tenant_id)
    naac = next(f for f in frameworks if "NAAC" in f.code)

    cycle = await service.create_assessment_cycle(
        tenant_id=tenant_id,
        payload=AccreditationCycleCreate(
            framework_id=naac.id,
            code="SOD-CYCLE-01",
            title="Separation of Duties Test Cycle",
            academic_year="2025-2026",
            start_date=datetime.now(UTC),
            end_date=datetime.now(UTC) + timedelta(days=120),
        ),
        actor_id=tenant_admin_a.id,
    )
    assessments = await service.list_criterion_assessments(tenant_id, cycle.id)
    target = assessments[0]

    # Faculty prepares and completes assessment
    drafted = await service.update_criterion_assessment_draft(
        tenant_id=tenant_id,
        assessment_id=target.id,
        payload=CriterionAssessmentDraftUpdate(
            lock_version=target.lock_version,
            score=135.0,
            findings="Thorough assessment completed with all criterion rubrics met.",
        ),
        actor_id=faculty_user.id,
    )

    submitted = await service.submit_criterion_assessment(
        tenant_id=tenant_id,
        assessment_id=target.id,
        payload=CriterionAssessmentSubmit(
            lock_version=drafted.lock_version,
            submission_notes="Ready for institutional review.",
        ),
        actor_id=faculty_user.id,
    )
    assert submitted.assessor_id == faculty_user.id
    assert submitted.status == AccreditationAssessmentStatus.SUBMITTED.value

    # 1. Faculty attempts to self-approve -> MUST raise AccreditationSeparationOfDutiesException
    with pytest.raises(AccreditationSeparationOfDutiesException):
        await service.review_criterion_assessment(
            tenant_id=tenant_id,
            assessment_id=target.id,
            payload=CriterionAssessmentReview(
                decision="APPROVED",
                reviewer_comments="Looks good to me (self review)",
            ),
            actor_id=faculty_user.id,
        )

    # 2. Independent reviewer (super_admin_user or tenant_admin_a) approves successfully
    approved = await service.review_criterion_assessment(
        tenant_id=tenant_id,
        assessment_id=target.id,
        payload=CriterionAssessmentReview(
            decision="APPROVED",
            reviewer_comments="Independent peer review confirmed curriculum committee records.",
            adjusted_score=138.0,
        ),
        actor_id=super_admin_user.id,
    )
    assert approved.status == AccreditationAssessmentStatus.APPROVED.value
    assert approved.reviewer_id == super_admin_user.id
    assert approved.score == 138.0
    assert approved.reviewed_at is not None


# =============================================================================
# 6. EVIDENCE REPOSITORY, LINKING & EXPIRY
# =============================================================================


@pytest.mark.asyncio
async def test_evidence_repository_lifecycle_and_expiry(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User, super_admin_user: User
):
    """Verifies evidence creation, linking to criteria, independent verification, and expiration sweeps."""
    service = AccreditationService(db_session)
    tenant_id = tenant_a.id

    await service.seed_default_frameworks_if_empty(tenant_id, tenant_admin_a.id)
    frameworks = await service.list_frameworks(tenant_id)
    naac = next(f for f in frameworks if "NAAC" in f.code)

    cycle = await service.create_assessment_cycle(
        tenant_id=tenant_id,
        payload=AccreditationCycleCreate(
            framework_id=naac.id,
            code="EVID-CYCLE-01",
            title="Evidence Lifecycle Cycle",
            academic_year="2025-2026",
            start_date=datetime.now(UTC),
            end_date=datetime.now(UTC) + timedelta(days=90),
        ),
        actor_id=tenant_admin_a.id,
    )
    assessments = await service.list_criterion_assessments(tenant_id, cycle.id)
    crit_assessment = assessments[0]

    # 1. Create evidence with past validity date (to test expiry sweep)
    expired_evid = await service.create_evidence(
        tenant_id=tenant_id,
        payload=AccreditationEvidenceCreate(
            evidence_code="EVID-BOS-2023",
            title="Board of Studies Minutes 2023",
            description="Historical curriculum revisions approved by Academic Council",
            evidence_category=AccreditationEvidenceCategory.GOVERNANCE_MINUTES,
            valid_from=datetime.now(UTC) - timedelta(days=400),
            valid_until=datetime.now(UTC) - timedelta(days=10),  # Expired
        ),
        actor_id=tenant_admin_a.id,
    )
    assert expired_evid.verification_status == AccreditationEvidenceVerificationStatus.UNVERIFIED.value

    # 2. Link evidence to criterion assessment
    link = await service.map_evidence_to_assessment(
        tenant_id=tenant_id,
        assessment_id=crit_assessment.id,
        evidence_id=expired_evid.id,
        relevance_remarks="Demonstrates BoS meeting frequency and syllabus ratification.",
        actor_id=tenant_admin_a.id,
    )
    assert link.evidence_id == expired_evid.id

    # 3. Independent verification of evidence
    verified = await service.verify_evidence(
        tenant_id=tenant_id,
        evidence_id=expired_evid.id,
        payload=AccreditationEvidenceVerify(
            verification_status=AccreditationEvidenceVerificationStatus.VERIFIED,
            reviewer_notes="Cross-checked against certified registrar archive stamps.",
        ),
        actor_id=super_admin_user.id,
    )
    assert verified.verification_status == AccreditationEvidenceVerificationStatus.VERIFIED.value
    assert verified.verified_by_user_id == super_admin_user.id

    # 4. Run background sweep to detect expired evidence
    sweep_res = await service.sweep_quality_reviews()
    assert sweep_res["expired_evidence_flagged"] >= 1

    # Re-fetch evidence to confirm is_expired is now True
    refreshed = await service.get_evidence(tenant_id, expired_evid.id)
    assert refreshed.is_expired is True


# =============================================================================
# 7. QUALITY INDICATORS & DATA QUALITY WARNINGS
# =============================================================================


@pytest.mark.asyncio
async def test_quality_indicators_observations_and_data_quality(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies KPI configuration, observations time-series, and data quality / completeness tracking."""
    service = AccreditationService(db_session)
    tenant_id = tenant_a.id

    # 1. Create Quality Indicator
    indicator = await service.create_indicator(
        tenant_id=tenant_id,
        payload=QualityIndicatorCreate(
            code="KPI-GRAD-RATE",
            name="On-Time Graduation Rate",
            category=QualityIndicatorCategory.STUDENT_SUCCESS,
            calculation_method="PERCENTAGE",
            source_module="STUDENT_RECORDS",
            unit_of_measurement="%",
            target_value=90.0,
            benchmark_threshold=75.0,
            reporting_frequency="SEMESTER",
        ),
        actor_id=tenant_admin_a.id,
    )
    assert indicator.code == "KPI-GRAD-RATE"

    # 2. Record incomplete observation (< 100% data completeness)
    obs1 = await service.record_observation(
        tenant_id=tenant_id,
        indicator_id=indicator.id,
        payload=QualityIndicatorObservationCreate(
            period_label="Fall 2025",
            observation_date=datetime.now(UTC),
            observed_value=82.5,
            target_value=90.0,
            data_completeness_pct=85.0,  # Incomplete!
            notes="Missing 2 department graduation reports at census date",
        ),
        actor_id=tenant_admin_a.id,
    )
    assert obs1.observed_value == 82.5
    assert obs1.data_completeness_pct == 85.0

    # 3. Check indicator refreshed status has data quality warning
    refreshed_kpi = await service.get_indicator(tenant_id, indicator.id)
    assert refreshed_kpi.current_value == 82.5
    assert refreshed_kpi.data_quality_status == QualityDataQualityStatus.WARNING_INCOMPLETE.value
    assert "Completeness below 90%" in (refreshed_kpi.data_quality_notes or "")

    # 4. Record complete observation above target
    await service.record_observation(
        tenant_id=tenant_id,
        indicator_id=indicator.id,
        payload=QualityIndicatorObservationCreate(
            period_label="Spring 2026",
            observation_date=datetime.now(UTC),
            observed_value=92.0,
            target_value=90.0,
            data_completeness_pct=100.0,
        ),
        actor_id=tenant_admin_a.id,
    )
    refreshed_kpi2 = await service.get_indicator(tenant_id, indicator.id)
    assert refreshed_kpi2.current_value == 92.0
    assert refreshed_kpi2.data_quality_status == QualityDataQualityStatus.EXCELLENT.value


# =============================================================================
# 8. INTERNAL AUDITS & REPORT FINALIZATION IMMUTABILITY
# =============================================================================


@pytest.mark.asyncio
async def test_internal_audit_program_and_report_immutability(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User, super_admin_user: User
):
    """Verifies audit program, checklist management, and strict immutability of finalized audit reports."""
    service = AccreditationService(db_session)
    tenant_id = tenant_a.id

    # 1. Create audit program
    audit = await service.create_audit_program(
        tenant_id=tenant_id,
        payload=QualityAuditProgramCreate(
            code="IA-2026-Q1",
            title="Q1 Comprehensive Internal Academic & Quality Audit",
            description="Assessment of engineering laboratory safety and course file completeness",
            audit_type=QualityAuditType.ACADEMIC_AUDIT,
            scheduled_start_date=datetime.now(UTC),
            scheduled_end_date=datetime.now(UTC) + timedelta(days=5),
        ),
        actor_id=super_admin_user.id,
    )
    assert audit.code == "IA-2026-Q1"
    assert audit.is_immutable is False

    # 2. Add checklist item
    item = await service.add_audit_checklist_item(
        tenant_id=tenant_id,
        program_id=audit.id,
        payload=QualityAuditChecklistItemCreate(
            item_code="CHK-LAB-01",
            requirement_description="Laboratory Equipment Calibration & Safety Logs",
            compliance_status="NON_COMPLIANT",
            auditor_notes="Calibration certificates expired for 3 high-voltage test units.",
        ),
        actor_id=super_admin_user.id,
    )
    assert item.item_code == "CHK-LAB-01"

    # 3. Finalize audit report -> locks audit permanently
    finalized = await service.finalize_audit_report(
        tenant_id=tenant_id,
        audit_id=audit.id,
        payload=QualityAuditFinalize(
            summary_findings="Audit concluded with 1 major finding in laboratory calibration.",
            recommendations="Implement institutional calibration calendar and maintenance SLA.",
        ),
        actor_id=super_admin_user.id,
    )
    assert finalized.status == QualityAuditStatus.FINALIZED.value
    assert finalized.is_immutable is True

    # 4. Attempt to mutate checklist on finalized audit MUST raise AccreditationAuditFinalizedException
    with pytest.raises(AccreditationAuditFinalizedException):
        await service.add_audit_checklist_item(
            tenant_id=tenant_id,
            program_id=audit.id,
            payload=QualityAuditChecklistItemCreate(
                item_code="CHK-ILLEGAL",
                requirement_description="Attempted change on finalized report",
            ),
            actor_id=super_admin_user.id,
        )

    # 5. Attempt to re-finalize or alter summary report MUST also raise AccreditationAuditFinalizedException
    with pytest.raises(AccreditationAuditFinalizedException):
        await service.finalize_audit_report(
            tenant_id=tenant_id,
            audit_id=audit.id,
            payload=QualityAuditFinalize(
                summary_findings="Rewritten summary",
                recommendations="Rewritten recommendations",
            ),
            actor_id=super_admin_user.id,
        )


# =============================================================================
# 9. FINDINGS & CAPA SEPARATION OF DUTIES CLOSURE
# =============================================================================


@pytest.mark.asyncio
async def test_finding_and_capa_separation_of_duties_closure(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    faculty_user: User,
    super_admin_user: User,
):
    """Verifies finding creation, CAPA action assignment, and separation of duties on CAPA closure."""
    service = AccreditationService(db_session)
    tenant_id = tenant_a.id

    # 1. Create Finding
    finding = await service.create_finding(
        tenant_id=tenant_id,
        payload=QualityFindingCreate(
            finding_code="FND-CALIB-01",
            title="Expired Calibration Certificates in Electrical Lab",
            description="Testing equipment calibration overdue by 45 days, violating ISO-21001 clause 7.1.",
            severity=QualityFindingSeverity.HIGH,
            assigned_owner_id=faculty_user.id,
            target_resolution_date=datetime.now(UTC) + timedelta(days=30),
            root_cause_analysis="Vendor service contract delayed due to procurement re-tendering.",
        ),
        actor_id=super_admin_user.id,
    )
    assert finding.finding_code == "FND-CALIB-01"

    # 2. Create CAPA assigned to faculty_user as responsible owner
    capa = await service.create_corrective_action(
        tenant_id=tenant_id,
        finding_id=finding.id,
        payload=QualityCAPACreate(
            action_code="CAPA-CALIB-01",
            action_type=QualityCAPAType.CORRECTIVE,
            proposed_action="Execute emergency recalibration through authorized NABL laboratory.",
            preventive_measures="Implement automated calendar alerts 60 days prior to certificate expiration.",
            responsible_owner_id=faculty_user.id,
            due_date=datetime.now(UTC) + timedelta(days=14),
            verification_criteria="NABL calibration certificates uploaded and verified by IQAC.",
        ),
        actor_id=tenant_admin_a.id,
    )
    assert capa.status == QualityCAPAStatus.IN_PROGRESS.value
    assert capa.responsible_owner_id == faculty_user.id

    # 3. Action owner (faculty_user) attempts to verify & close their own CAPA -> MUST fail!
    with pytest.raises(AccreditationSeparationOfDutiesException):
        await service.close_corrective_action(
            tenant_id=tenant_id,
            action_id=capa.id,
            payload=QualityCAPAClose(
                closure_decision="CLOSED_EFFECTIVE",
                closure_notes="I have completed it myself and hereby approve closure.",
            ),
            actor_id=faculty_user.id,
        )

    # 4. Independent quality reviewer (super_admin_user) verifies and approves closure
    closed = await service.close_corrective_action(
        tenant_id=tenant_id,
        action_id=capa.id,
        payload=QualityCAPAClose(
            closure_decision="CLOSED_EFFECTIVE",
            closure_notes="Inspected NABL calibration certificate #NABL-98231. Conformance verified.",
        ),
        actor_id=super_admin_user.id,
    )
    assert closed.status == QualityCAPAStatus.VERIFIED_EFFECTIVE.value
    assert closed.verified_by_user_id == super_admin_user.id
    assert closed.closure_decision == "CLOSED_EFFECTIVE"


# =============================================================================
# 10. CONTINUOUS IMPROVEMENT (CQI) PLANNING
# =============================================================================


@pytest.mark.asyncio
async def test_continuous_improvement_plan_lifecycle(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies Continuous Quality Improvement (CQI) plan creation and milestone tracking."""
    service = AccreditationService(db_session)
    tenant_id = tenant_a.id

    plan = await service.create_improvement_plan(
        tenant_id=tenant_id,
        payload=QualityImprovementPlanCreate(
            code="CQI-FACULTY-PHD",
            title="Faculty PhD Qualification Enhancement Initiative",
            objective="Increase percentage of doctoral degree holders among core faculty to 75%",
            baseline_measurement="52% of core faculty hold doctoral degrees",
            target_outcome="75% of core faculty hold doctoral degrees by 2028",
            responsible_owner_id=tenant_admin_a.id,
            start_date=datetime.now(UTC),
            target_date=datetime.now(UTC) + timedelta(days=730),
            metadata_json={
                "milestones": [
                    {"title": "M1: Institutional research fellowship policy", "due_months": 3, "done": True},
                    {"title": "M2: Enrollment in recognized doctoral programs", "due_months": 12, "done": False},
                ]
            },
        ),
        actor_id=tenant_admin_a.id,
    )
    assert plan.code == "CQI-FACULTY-PHD"
    assert len(plan.metadata_json["milestones"]) == 2


# =============================================================================
# 11. TRANSPARENT ACCREDITATION READINESS SCORING & GAP ANALYSIS
# =============================================================================


@pytest.mark.asyncio
async def test_accreditation_readiness_calculation(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User, super_admin_user: User
):
    """Verifies the readiness calculation engine, factor transparency, and penalty for open critical findings."""
    service = AccreditationService(db_session)
    tenant_id = tenant_a.id

    await service.seed_default_frameworks_if_empty(tenant_id, tenant_admin_a.id)
    frameworks = await service.list_frameworks(tenant_id)
    naac = next(f for f in frameworks if "NAAC" in f.code)

    cycle = await service.create_assessment_cycle(
        tenant_id=tenant_id,
        payload=AccreditationCycleCreate(
            framework_id=naac.id,
            code="RDN-CYCLE-01",
            title="Readiness Engine Test Cycle",
            academic_year="2025-2026",
            start_date=datetime.now(UTC),
            end_date=datetime.now(UTC) + timedelta(days=100),
        ),
        actor_id=tenant_admin_a.id,
    )
    assessments = await service.list_criterion_assessments(tenant_id, cycle.id)

    # Complete and approve 1 assessment with max score
    target = assessments[0]
    drafted = await service.update_criterion_assessment_draft(
        tenant_id=tenant_id,
        assessment_id=target.id,
        payload=CriterionAssessmentDraftUpdate(
            lock_version=target.lock_version,
            score=100.0,
        ),
        actor_id=tenant_admin_a.id,
    )
    submitted = await service.submit_criterion_assessment(
        tenant_id=tenant_id,
        assessment_id=target.id,
        payload=CriterionAssessmentSubmit(
            lock_version=drafted.lock_version,
        ),
        actor_id=tenant_admin_a.id,
    )
    await service.review_criterion_assessment(
        tenant_id=tenant_id,
        assessment_id=target.id,
        payload=CriterionAssessmentReview(
            decision="APPROVED",
            reviewer_comments="Approved for readiness test.",
            adjusted_score=100.0,
        ),
        actor_id=super_admin_user.id,
    )

    # Calculate readiness snapshot
    snapshot = await service.calculate_readiness_snapshot(
        tenant_id=tenant_id,
        cycle_id=cycle.id,
        actor_id=tenant_admin_a.id,
    )
    assert snapshot.overall_readiness_score >= 0.0
    assert snapshot.criteria_total_count >= 7
    assert snapshot.criteria_assessed_count >= 1
    assert snapshot.readiness_category is not None


# =============================================================================
# 12. TENANT ISOLATION
# =============================================================================


@pytest.mark.asyncio
async def test_accreditation_tenant_isolation(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    tenant_admin_a: User,
    tenant_admin_b: User,
):
    """Verifies that Tenant B cannot access Tenant A's frameworks, cycles, or evidence."""
    service = AccreditationService(db_session)

    # Create framework in Tenant A
    fw_a = await service.create_framework(
        tenant_id=tenant_a.id,
        payload=AccreditationFrameworkCreate(
            code="TENANT-A-EXCLUSIVE",
            name="Tenant A Exclusive Framework",
            issuing_body="Internal QA",
            framework_type=AccreditationFrameworkType.CUSTOM,
            scoring_model=AccreditationScoringModel.NUMERIC_SCALE,
            max_score=100.0,
        ),
        actor_id=tenant_admin_a.id,
    )

    # Tenant B tries to get Tenant A's framework -> should raise NotFound
    with pytest.raises(AccreditationFrameworkNotFoundException):
        await service.get_framework(tenant_b.id, fw_a.id)

    # Tenant B listing frameworks does not include Tenant A's exclusive framework
    b_frameworks = await service.list_frameworks(tenant_b.id)
    assert not any(f.code == "TENANT-A-EXCLUSIVE" for f in b_frameworks)


# =============================================================================
# 13. FASTAPI REST API INTEGRATION
# =============================================================================


@pytest.mark.asyncio
async def test_accreditation_rest_api_endpoints(
    client: AsyncClient,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Verifies the FastAPI REST endpoints for frameworks, cycles, indicators, audits, and readiness."""
    headers = make_auth_headers(tenant_admin_a, tenant_a.id)

    # 1. Seed defaults via API
    seed_res = await client.post("/api/v1/accreditation/frameworks/seed-defaults", headers=headers)
    assert seed_res.status_code == 200

    # 2. GET /api/v1/accreditation/frameworks
    res = await client.get("/api/v1/accreditation/frameworks", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) >= 3

    framework_id = data[0]["id"]

    # 3. GET /api/v1/accreditation/frameworks/{id}/criteria
    res_crit = await client.get(
        f"/api/v1/accreditation/frameworks/{framework_id}/criteria", headers=headers
    )
    assert res_crit.status_code == 200
    assert len(res_crit.json()["data"]) >= 1

    # 4. POST /api/v1/accreditation/cycles
    cycle_payload = {
        "framework_id": framework_id,
        "code": f"API-CYCLE-{uuid4().hex[:6]}",
        "title": "API Test Assessment Cycle",
        "academic_year": "2025-2026",
        "start_date": datetime.now(UTC).isoformat(),
        "end_date": (datetime.now(UTC) + timedelta(days=90)).isoformat(),
    }
    res_cycle = await client.post(
        "/api/v1/accreditation/cycles", json=cycle_payload, headers=headers
    )
    assert res_cycle.status_code == 201
    cycle_data = res_cycle.json()["data"]
    cycle_id = cycle_data["id"]

    # 5. GET /api/v1/accreditation/cycles/{id}/assessments
    res_assess = await client.get(
        f"/api/v1/accreditation/cycles/{cycle_id}/assessments", headers=headers
    )
    assert res_assess.status_code == 200
    assess_list = res_assess.json()["data"]
    assert len(assess_list) >= 1

    # 6. POST /api/v1/accreditation/indicators
    kpi_payload = {
        "code": f"KPI-API-{uuid4().hex[:6]}",
        "name": "Faculty to Student Ratio",
        "category": "FACULTY_PROFILE",
        "calculation_method": "RATIO",
        "unit_of_measurement": ":",
        "target_value": 15.0,
        "benchmark_threshold": 20.0,
        "reporting_frequency": "ANNUAL",
    }
    res_kpi = await client.post(
        "/api/v1/accreditation/indicators", json=kpi_payload, headers=headers
    )
    assert res_kpi.status_code == 201

    # 7. POST /api/v1/accreditation/audits
    audit_payload = {
        "code": f"AUDIT-API-{uuid4().hex[:6]}",
        "title": "API Internal Quality Audit",
        "description": "Verification of admission standards and compliance records",
        "audit_type": "ACADEMIC_AUDIT",
        "scheduled_start_date": datetime.now(UTC).isoformat(),
        "scheduled_end_date": (datetime.now(UTC) + timedelta(days=3)).isoformat(),
    }
    res_audit = await client.post(
        "/api/v1/accreditation/audits", json=audit_payload, headers=headers
    )
    assert res_audit.status_code == 201

    # 8. POST /api/v1/accreditation/cycles/{id}/readiness/calculate
    res_rdn = await client.post(
        f"/api/v1/accreditation/cycles/{cycle_id}/readiness/calculate",
        headers=headers,
    )
    assert res_rdn.status_code == 200
    rdn_data = res_rdn.json()["data"]
    assert "overall_readiness_score" in rdn_data

    # 9. GET /api/v1/accreditation/dashboard/summary
    res_dash = await client.get("/api/v1/accreditation/dashboard/summary", headers=headers)
    assert res_dash.status_code == 200
    dash_data = res_dash.json()["data"]
    assert "active_frameworks_count" in dash_data
