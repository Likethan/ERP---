"""Enterprise Institutional Accreditation, Quality Assurance & Continuous Improvement Service (Step 43).

Encapsulates complete domain logic for:
- Pre-seeding statutory accreditation templates (NAAC, NBA, ISO-21001)
- Managing configurable frameworks, criteria hierarchies, and version snapshots
- Coordinating assessment cycles, criterion-level evaluations, and independent review
- Enforcing Separation of Duties on assessment reviews and CAPA closures
- Managing traceable evidence links, verification, and expiration sweeps
- Calculating quality indicators (KPIs) with data quality status validation
- Conducting internal quality audits with immutable finalized reports
- Managing compliance findings, corrective actions (CAPA), and CQI continuous improvement
- Computing transparent accreditation readiness scores and gap analysis
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import delete, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventCategory, create_audit_entry
from app.core.exceptions import (
    AccreditationAuditFinalizedException,
    AccreditationAuditNotFoundException,
    AccreditationAssessmentNotFoundException,
    AccreditationCAPAClosureDeniedException,
    AccreditationCAPANotFoundException,
    AccreditationCriterionNotFoundException,
    AccreditationCycleNotFoundException,
    AccreditationEvidenceNotFoundException,
    AccreditationFindingNotFoundException,
    AccreditationFrameworkNotFoundException,
    AccreditationImprovementNotFoundException,
    AccreditationIndicatorNotFoundException,
    AccreditationInvalidScoreException,
    AccreditationOptimisticLockException,
    AccreditationSeparationOfDutiesException,
)
from app.models.accreditation import (
    AccreditationAssessmentCycle,
    AccreditationAssessmentStatus,
    AccreditationCriterion,
    AccreditationCriterionAssessment,
    AccreditationCriterionEvidenceMap,
    AccreditationCriterionType,
    AccreditationEvidence,
    AccreditationEvidenceCategory,
    AccreditationEvidenceVerificationStatus,
    AccreditationFramework,
    AccreditationFrameworkStatus,
    AccreditationFrameworkType,
    AccreditationFrameworkVersion,
    AccreditationMaturityLevel,
    AccreditationReadinessCategory,
    AccreditationReadinessSnapshot,
    AccreditationScoringModel,
    QualityAuditChecklistItem,
    QualityAuditProgram,
    QualityAuditStatus,
    QualityAuditType,
    QualityCAPAStatus,
    QualityCAPAType,
    QualityCorrectiveAction,
    QualityDataQualityStatus,
    QualityFinding,
    QualityFindingSeverity,
    QualityFindingStatus,
    QualityImprovementPlan,
    QualityImprovementStatus,
    QualityIndicator,
    QualityIndicatorCategory,
    QualityIndicatorObservation,
)
from app.models.people import User
from app.schemas.accreditation import (
    AccreditationCriterionCreate,
    AccreditationCriterionUpdate,
    AccreditationCycleCreate,
    AccreditationCycleUpdate,
    AccreditationDashboardSummary,
    AccreditationEvidenceCreate,
    AccreditationEvidenceVerify,
    AccreditationFrameworkCreate,
    AccreditationFrameworkPublish,
    AccreditationFrameworkUpdate,
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
    QualityImprovementPlanUpdate,
    QualityIndicatorCreate,
    QualityIndicatorObservationCreate,
    QualityIndicatorUpdate,
)


class AccreditationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # 1. STATUTORY FRAMEWORK SEEDING
    # =========================================================================

    async def seed_default_frameworks_if_empty(self, tenant_id: UUID, actor_id: UUID) -> list[AccreditationFramework]:
        """Auto-seed standard NAAC, NBA, and ISO template frameworks if tenant has none."""
        existing_res = await self.db.execute(
            select(func.count()).select_from(AccreditationFramework).where(AccreditationFramework.tenant_id == tenant_id)
        )
        if (existing_res.scalar_one() or 0) > 0:
            return []

        templates = [
            {
                "code": "NAAC-UNIV-TEMPLATE",
                "name": "NAAC Revised Accreditation Framework (University Manual)",
                "description": "Standard 7-criteria quality assurance framework established by NAAC for universities and autonomous colleges.",
                "issuing_body": "National Assessment and Accreditation Council (NAAC)",
                "framework_type": AccreditationFrameworkType.NAAC,
                "scoring_model": AccreditationScoringModel.NUMERIC_SCALE,
                "max_score": 1000.0,
                "criteria": [
                    {"code": "CRITERION_1", "title": "Curricular Aspects", "weight": 150.0, "max_score": 150.0, "order": 1},
                    {"code": "CRITERION_2", "title": "Teaching-Learning and Evaluation", "weight": 200.0, "max_score": 200.0, "order": 2},
                    {"code": "CRITERION_3", "title": "Research, Innovations and Extension", "weight": 250.0, "max_score": 250.0, "order": 3},
                    {"code": "CRITERION_4", "title": "Infrastructure and Learning Resources", "weight": 100.0, "max_score": 100.0, "order": 4},
                    {"code": "CRITERION_5", "title": "Student Support and Progression", "weight": 100.0, "max_score": 100.0, "order": 5},
                    {"code": "CRITERION_6", "title": "Governance, Leadership and Management", "weight": 100.0, "max_score": 100.0, "order": 6},
                    {"code": "CRITERION_7", "title": "Institutional Values and Best Practices", "weight": 100.0, "max_score": 100.0, "order": 7},
                ],
            },
            {
                "code": "NBA-TIER-1-TEMPLATE",
                "name": "NBA Tier-1 Undergraduate Engineering Accreditation",
                "description": "Outcome-Based Education (OBE) evaluation framework by the National Board of Accreditation under Washington Accord.",
                "issuing_body": "National Board of Accreditation (NBA)",
                "framework_type": AccreditationFrameworkType.NBA,
                "scoring_model": AccreditationScoringModel.NUMERIC_SCALE,
                "max_score": 1000.0,
                "criteria": [
                    {"code": "NBA_CRIT_1", "title": "Vision, Mission and Program Educational Objectives", "weight": 60.0, "max_score": 60.0, "order": 1},
                    {"code": "NBA_CRIT_2", "title": "Program Curriculum and Teaching-Learning Processes", "weight": 120.0, "max_score": 120.0, "order": 2},
                    {"code": "NBA_CRIT_3", "title": "Course Outcomes and Program Outcomes Attainment", "weight": 120.0, "max_score": 120.0, "order": 3},
                    {"code": "NBA_CRIT_4", "title": "Students' Performance and Progression", "weight": 150.0, "max_score": 150.0, "order": 4},
                    {"code": "NBA_CRIT_5", "title": "Faculty Information and Contributions", "weight": 200.0, "max_score": 200.0, "order": 5},
                    {"code": "NBA_CRIT_6", "title": "Facilities and Technical Support", "weight": 80.0, "max_score": 80.0, "order": 6},
                    {"code": "NBA_CRIT_7", "title": "Continuous Improvement", "weight": 50.0, "max_score": 50.0, "order": 7},
                ],
            },
            {
                "code": "ISO-21001-TEMPLATE",
                "name": "ISO 21001:2018 Educational Organizations Management Systems",
                "description": "International standard for educational management systems ensuring learner-centric quality excellence.",
                "issuing_body": "International Organization for Standardization (ISO)",
                "framework_type": AccreditationFrameworkType.ISO_21001,
                "scoring_model": AccreditationScoringModel.MATURITY_LEVEL,
                "max_score": 5.0,
                "criteria": [
                    {"code": "ISO_CLAUSE_4", "title": "Context of the Organization & Learner Needs", "weight": 1.0, "max_score": 5.0, "order": 1},
                    {"code": "ISO_CLAUSE_5", "title": "Leadership & Commitment to Educational Quality", "weight": 1.0, "max_score": 5.0, "order": 2},
                    {"code": "ISO_CLAUSE_6", "title": "Planning & Educational Risk Management", "weight": 1.0, "max_score": 5.0, "order": 3},
                    {"code": "ISO_CLAUSE_7", "title": "Support, Infrastructure & Academic Competence", "weight": 1.0, "max_score": 5.0, "order": 4},
                    {"code": "ISO_CLAUSE_8", "title": "Educational Operation & Curriculum Delivery", "weight": 1.0, "max_score": 5.0, "order": 5},
                    {"code": "ISO_CLAUSE_9", "title": "Performance Evaluation, Internal Audits & Metrics", "weight": 1.0, "max_score": 5.0, "order": 6},
                    {"code": "ISO_CLAUSE_10", "title": "Continual Improvement & Non-Conformity Management", "weight": 1.0, "max_score": 5.0, "order": 7},
                ],
            },
        ]

        seeded_frameworks: list[AccreditationFramework] = []
        for tpl in templates:
            fw = AccreditationFramework(
                id=uuid4(),
                tenant_id=tenant_id,
                code=tpl["code"],
                name=tpl["name"],
                description=tpl["description"],
                issuing_body=tpl["issuing_body"],
                framework_type=tpl["framework_type"],
                scope_type="INSTITUTION",
                status=AccreditationFrameworkStatus.ACTIVE,
                current_version_number=1,
                effective_from=datetime.now(UTC),
                owner_user_id=actor_id,
                scoring_model=tpl["scoring_model"],
                max_score=tpl["max_score"],
                weighting_supported=True,
                metadata_json={"is_system_template": True},
            )
            self.db.add(fw)
            seeded_frameworks.append(fw)

            # Add criteria
            for c_data in tpl["criteria"]:
                crit = AccreditationCriterion(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    framework_id=fw.id,
                    code=c_data["code"],
                    title=c_data["title"],
                    description=f"Standard benchmark assessment criterion for {c_data['title']}.",
                    criterion_type=AccreditationCriterionType.QUALITATIVE,
                    weight=c_data["weight"],
                    max_score=c_data["max_score"],
                    is_mandatory=True,
                    assessment_guidelines="Adhere to statutory evaluative metrics and provide verified institutional documentation.",
                    evidence_requirements=["Institutional Policy / SOP", "Verification Minutes / Approvals"],
                    order_index=c_data["order"],
                    is_active=True,
                )
                self.db.add(crit)

        await self.db.commit()
        for fw in seeded_frameworks:
            await self.db.refresh(fw)
        return seeded_frameworks

    # =========================================================================
    # 2. FRAMEWORK & VERSION MANAGEMENT
    # =========================================================================

    async def list_frameworks(
        self,
        tenant_id: UUID,
        status: str | None = None,
        framework_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AccreditationFramework]:
        stmt = select(AccreditationFramework).where(AccreditationFramework.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(AccreditationFramework.status == status)
        if framework_type:
            stmt = stmt.where(AccreditationFramework.framework_type == framework_type)
        stmt = stmt.order_by(desc(AccreditationFramework.created_at)).limit(limit).offset(offset)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_framework(self, tenant_id: UUID, framework_id: UUID) -> AccreditationFramework:
        stmt = select(AccreditationFramework).where(
            AccreditationFramework.tenant_id == tenant_id,
            AccreditationFramework.id == framework_id,
        )
        res = await self.db.execute(stmt)
        fw = res.scalar_one_or_none()
        if not fw:
            raise AccreditationFrameworkNotFoundException(framework_id)
        return fw

    async def create_framework(
        self, tenant_id: UUID, payload: AccreditationFrameworkCreate, actor_id: UUID
    ) -> AccreditationFramework:
        fw = AccreditationFramework(
            id=uuid4(),
            tenant_id=tenant_id,
            code=payload.code.strip().upper(),
            name=payload.name.strip(),
            description=payload.description,
            issuing_body=payload.issuing_body.strip(),
            framework_type=payload.framework_type,
            scope_type=payload.scope_type,
            campus_id=payload.campus_id,
            department_id=payload.department_id,
            status=AccreditationFrameworkStatus.DRAFT,
            current_version_number=1,
            effective_from=payload.effective_from or datetime.now(UTC),
            effective_until=payload.effective_until,
            review_by_date=payload.review_by_date,
            owner_user_id=actor_id,
            scoring_model=payload.scoring_model,
            max_score=payload.max_score,
            weighting_supported=payload.weighting_supported,
            metadata_json=payload.metadata_json or {},
        )
        self.db.add(fw)
        await self.db.commit()
        await self.db.refresh(fw)

        await create_audit_entry(
            db=self.db,
            tenant_id=tenant_id,
            action=AuditEventCategory.ACCREDITATION_FRAMEWORK_CREATED,
            entity_type="AccreditationFramework",
            entity_id=fw.id,
            user_id=actor_id,
            business_context=f"Created accreditation framework '{fw.code}'",
        )
        await self.db.commit()
        return fw

    async def update_framework(
        self, tenant_id: UUID, framework_id: UUID, payload: AccreditationFrameworkUpdate, actor_id: UUID
    ) -> AccreditationFramework:
        fw = await self.get_framework(tenant_id, framework_id)
        if payload.name is not None:
            fw.name = payload.name.strip()
        if payload.description is not None:
            fw.description = payload.description
        if payload.issuing_body is not None:
            fw.issuing_body = payload.issuing_body.strip()
        if payload.scope_type is not None:
            fw.scope_type = payload.scope_type
        if payload.effective_from is not None:
            fw.effective_from = payload.effective_from
        if payload.effective_until is not None:
            fw.effective_until = payload.effective_until
        if payload.review_by_date is not None:
            fw.review_by_date = payload.review_by_date
        if payload.max_score is not None:
            fw.max_score = payload.max_score
        if payload.weighting_supported is not None:
            fw.weighting_supported = payload.weighting_supported
        if payload.metadata_json is not None:
            fw.metadata_json = payload.metadata_json

        await self.db.commit()
        await self.db.refresh(fw)
        return fw

    async def publish_framework_version(
        self, tenant_id: UUID, framework_id: UUID, payload: AccreditationFrameworkPublish, actor_id: UUID
    ) -> AccreditationFrameworkVersion:
        """Publish an immutable snapshot of current framework definitions and increment version."""
        fw = await self.get_framework(tenant_id, framework_id)

        # Fetch criteria to snapshot
        crit_res = await self.db.execute(
            select(AccreditationCriterion).where(
                AccreditationCriterion.tenant_id == tenant_id,
                AccreditationCriterion.framework_id == framework_id,
                AccreditationCriterion.is_active.is_(True),
            ).order_by(AccreditationCriterion.order_index)
        )
        criteria = crit_res.scalars().all()
        criteria_snapshot = [
            {
                "id": str(c.id),
                "code": c.code,
                "title": c.title,
                "criterion_type": c.criterion_type,
                "weight": c.weight,
                "max_score": c.max_score,
                "order_index": c.order_index,
            }
            for c in criteria
        ]

        version_record = AccreditationFrameworkVersion(
            id=uuid4(),
            tenant_id=tenant_id,
            framework_id=fw.id,
            version_number=fw.current_version_number,
            title=f"{fw.name} v{fw.current_version_number}.0",
            description=fw.description,
            rules_snapshot_json={
                "scoring_model": fw.scoring_model,
                "max_score": fw.max_score,
                "weighting_supported": fw.weighting_supported,
                "scope_type": fw.scope_type,
            },
            criteria_snapshot_json=criteria_snapshot,
            change_summary=payload.change_summary.strip(),
            published_by_user_id=actor_id,
            published_at=datetime.now(UTC),
        )
        self.db.add(version_record)

        fw.status = AccreditationFrameworkStatus.ACTIVE
        fw.current_version_number += 1
        await self.db.commit()
        await self.db.refresh(version_record)

        await create_audit_entry(
            db=self.db,
            tenant_id=tenant_id,
            action=AuditEventCategory.ACCREDITATION_FRAMEWORK_PUBLISHED,
            entity_type="AccreditationFrameworkVersion",
            entity_id=version_record.id,
            user_id=actor_id,
            business_context=f"Published framework version v{version_record.version_number} for '{fw.code}'",
        )
        await self.db.commit()
        return version_record

    # =========================================================================
    # 3. CRITERIA HIERARCHY MANAGEMENT
    # =========================================================================

    async def list_criteria(
        self, tenant_id: UUID, framework_id: UUID, parent_id: UUID | None = None
    ) -> list[AccreditationCriterion]:
        stmt = select(AccreditationCriterion).where(
            AccreditationCriterion.tenant_id == tenant_id,
            AccreditationCriterion.framework_id == framework_id,
        )
        if parent_id is not None:
            stmt = stmt.where(AccreditationCriterion.parent_criterion_id == parent_id)
        stmt = stmt.order_by(AccreditationCriterion.order_index)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_criterion(self, tenant_id: UUID, criterion_id: UUID) -> AccreditationCriterion:
        stmt = select(AccreditationCriterion).where(
            AccreditationCriterion.tenant_id == tenant_id,
            AccreditationCriterion.id == criterion_id,
        )
        res = await self.db.execute(stmt)
        crit = res.scalar_one_or_none()
        if not crit:
            raise AccreditationCriterionNotFoundException(criterion_id)
        return crit

    async def create_criterion(
        self, tenant_id: UUID, framework_id: UUID, payload: AccreditationCriterionCreate, actor_id: UUID
    ) -> AccreditationCriterion:
        await self.get_framework(tenant_id, framework_id)
        crit = AccreditationCriterion(
            id=uuid4(),
            tenant_id=tenant_id,
            framework_id=framework_id,
            parent_criterion_id=payload.parent_criterion_id,
            code=payload.code.strip().upper(),
            title=payload.title.strip(),
            description=payload.description,
            criterion_type=payload.criterion_type,
            weight=payload.weight,
            max_score=payload.max_score,
            is_mandatory=payload.is_mandatory,
            assessment_guidelines=payload.assessment_guidelines,
            evidence_requirements=payload.evidence_requirements or [],
            order_index=payload.order_index,
            is_active=payload.is_active,
            metadata_json=payload.metadata_json or {},
        )
        self.db.add(crit)
        await self.db.commit()
        await self.db.refresh(crit)
        return crit

    async def update_criterion(
        self, tenant_id: UUID, criterion_id: UUID, payload: AccreditationCriterionUpdate, actor_id: UUID
    ) -> AccreditationCriterion:
        crit = await self.get_criterion(tenant_id, criterion_id)
        if payload.title is not None:
            crit.title = payload.title.strip()
        if payload.description is not None:
            crit.description = payload.description
        if payload.criterion_type is not None:
            crit.criterion_type = payload.criterion_type
        if payload.weight is not None:
            crit.weight = payload.weight
        if payload.max_score is not None:
            crit.max_score = payload.max_score
        if payload.is_mandatory is not None:
            crit.is_mandatory = payload.is_mandatory
        if payload.assessment_guidelines is not None:
            crit.assessment_guidelines = payload.assessment_guidelines
        if payload.evidence_requirements is not None:
            crit.evidence_requirements = payload.evidence_requirements
        if payload.order_index is not None:
            crit.order_index = payload.order_index
        if payload.is_active is not None:
            crit.is_active = payload.is_active
        if payload.metadata_json is not None:
            crit.metadata_json = payload.metadata_json

        await self.db.commit()
        await self.db.refresh(crit)
        return crit

    # =========================================================================
    # 4. ASSESSMENT CYCLES & CRITERION ASSESSMENTS
    # =========================================================================

    async def create_assessment_cycle(
        self, tenant_id: UUID, payload: AccreditationCycleCreate, actor_id: UUID
    ) -> AccreditationAssessmentCycle:
        fw = await self.get_framework(tenant_id, payload.framework_id)
        cycle = AccreditationAssessmentCycle(
            id=uuid4(),
            tenant_id=tenant_id,
            framework_id=fw.id,
            code=payload.code.strip().upper(),
            title=payload.title.strip(),
            academic_year=payload.academic_year.strip(),
            start_date=payload.start_date,
            end_date=payload.end_date,
            target_submission_date=payload.target_submission_date,
            status="ACTIVE",
            overall_score=None,
            readiness_percentage=0.0,
            lead_coordinator_id=actor_id,
            metadata_json=payload.metadata_json or {},
        )
        self.db.add(cycle)

        # Auto-initialize criterion assessment records for all active criteria
        crit_res = await self.db.execute(
            select(AccreditationCriterion).where(
                AccreditationCriterion.tenant_id == tenant_id,
                AccreditationCriterion.framework_id == fw.id,
                AccreditationCriterion.is_active.is_(True),
            )
        )
        criteria = crit_res.scalars().all()
        for c in criteria:
            assess = AccreditationCriterionAssessment(
                id=uuid4(),
                tenant_id=tenant_id,
                cycle_id=cycle.id,
                criterion_id=c.id,
                department_id=None,
                accountable_owner_id=actor_id,
                status=AccreditationAssessmentStatus.UNASSESSED,
                score=None,
                target_score=c.max_score,
                lock_version=1,
            )
            self.db.add(assess)

        await self.db.commit()
        await self.db.refresh(cycle)
        return cycle

    async def get_assessment_cycle(self, tenant_id: UUID, cycle_id: UUID) -> AccreditationAssessmentCycle:
        stmt = select(AccreditationAssessmentCycle).where(
            AccreditationAssessmentCycle.tenant_id == tenant_id,
            AccreditationAssessmentCycle.id == cycle_id,
        )
        res = await self.db.execute(stmt)
        cycle = res.scalar_one_or_none()
        if not cycle:
            raise AccreditationCycleNotFoundException(cycle_id)
        return cycle

    async def list_assessment_cycles(
        self, tenant_id: UUID, framework_id: UUID | None = None
    ) -> list[AccreditationAssessmentCycle]:
        stmt = select(AccreditationAssessmentCycle).where(AccreditationAssessmentCycle.tenant_id == tenant_id)
        if framework_id:
            stmt = stmt.where(AccreditationAssessmentCycle.framework_id == framework_id)
        stmt = stmt.order_by(desc(AccreditationAssessmentCycle.created_at))
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_criterion_assessment(
        self, tenant_id: UUID, assessment_id: UUID
    ) -> AccreditationCriterionAssessment:
        stmt = select(AccreditationCriterionAssessment).where(
            AccreditationCriterionAssessment.tenant_id == tenant_id,
            AccreditationCriterionAssessment.id == assessment_id,
        )
        res = await self.db.execute(stmt)
        assess = res.scalar_one_or_none()
        if not assess:
            raise AccreditationAssessmentNotFoundException(assessment_id)
        return assess

    async def list_criterion_assessments(
        self, tenant_id: UUID, cycle_id: UUID, status: str | None = None
    ) -> list[AccreditationCriterionAssessment]:
        stmt = select(AccreditationCriterionAssessment).where(
            AccreditationCriterionAssessment.tenant_id == tenant_id,
            AccreditationCriterionAssessment.cycle_id == cycle_id,
        )
        if status:
            stmt = stmt.where(AccreditationCriterionAssessment.status == status)
        stmt = stmt.order_by(AccreditationCriterionAssessment.created_at)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def update_criterion_assessment_draft(
        self, tenant_id: UUID, assessment_id: UUID, payload: CriterionAssessmentDraftUpdate, actor_id: UUID
    ) -> AccreditationCriterionAssessment:
        """Update draft assessment with optimistic concurrency lock verification."""
        assess = await self.get_criterion_assessment(tenant_id, assessment_id)
        if assess.lock_version != payload.lock_version:
            raise AccreditationOptimisticLockException(
                identifier=str(assess.id),
                current_lock_version=assess.lock_version,
                provided_lock_version=payload.lock_version,
            )

        crit = await self.get_criterion(tenant_id, assess.criterion_id)
        if payload.score is not None:
            if payload.score < 0 or payload.score > crit.max_score:
                raise AccreditationInvalidScoreException(
                    f"Score {payload.score} is invalid. Must be between 0 and criterion max score ({crit.max_score})."
                )
            assess.score = payload.score

        if payload.maturity_level is not None:
            assess.maturity_level = payload.maturity_level
        if payload.not_applicable_reason is not None:
            assess.not_applicable_reason = payload.not_applicable_reason.strip()
            if assess.not_applicable_reason:
                assess.status = AccreditationAssessmentStatus.NOT_APPLICABLE
        if payload.target_score is not None:
            assess.target_score = payload.target_score
        if payload.executive_summary is not None:
            assess.executive_summary = payload.executive_summary
        if payload.findings is not None:
            assess.findings = payload.findings
        if payload.strengths is not None:
            assess.strengths = payload.strengths
        if payload.weaknesses is not None:
            assess.weaknesses = payload.weaknesses
        if payload.recommendations is not None:
            assess.recommendations = payload.recommendations
        if payload.department_id is not None:
            assess.department_id = payload.department_id

        if assess.status not in (AccreditationAssessmentStatus.NOT_APPLICABLE, AccreditationAssessmentStatus.APPROVED):
            assess.status = AccreditationAssessmentStatus.IN_PROGRESS

        assess.assessor_id = actor_id
        assess.assessed_at = datetime.now(UTC)
        assess.lock_version += 1

        await self.db.commit()
        await self.db.refresh(assess)
        return assess

    async def submit_criterion_assessment(
        self, tenant_id: UUID, assessment_id: UUID, payload: CriterionAssessmentSubmit, actor_id: UUID
    ) -> AccreditationCriterionAssessment:
        assess = await self.get_criterion_assessment(tenant_id, assessment_id)
        if assess.lock_version != payload.lock_version:
            raise AccreditationOptimisticLockException(
                identifier=str(assess.id),
                current_lock_version=assess.lock_version,
                provided_lock_version=payload.lock_version,
            )

        assess.status = AccreditationAssessmentStatus.SUBMITTED
        assess.assessor_id = actor_id
        assess.assessed_at = datetime.now(UTC)
        assess.lock_version += 1
        await self.db.commit()
        await self.db.refresh(assess)

        await create_audit_entry(
            db=self.db,
            tenant_id=tenant_id,
            action=AuditEventCategory.ACCREDITATION_ASSESSMENT_SUBMITTED,
            entity_type="AccreditationCriterionAssessment",
            entity_id=assess.id,
            user_id=actor_id,
            business_context="Submitted criterion assessment for independent review",
        )
        await self.db.commit()
        return assess

    async def review_criterion_assessment(
        self, tenant_id: UUID, assessment_id: UUID, payload: CriterionAssessmentReview, actor_id: UUID
    ) -> AccreditationCriterionAssessment:
        """Conduct independent review of criterion assessment with strict Separation of Duties."""
        assess = await self.get_criterion_assessment(tenant_id, assessment_id)

        # Separation of Duties check: Assessor / Accountable Owner cannot review their own assessment
        if assess.assessor_id == actor_id or assess.accountable_owner_id == actor_id:
            raise AccreditationSeparationOfDutiesException(
                "approve their own criterion assessment submission"
            )

        if payload.decision == "APPROVED":
            assess.status = AccreditationAssessmentStatus.APPROVED
            if payload.adjusted_score is not None:
                crit = await self.get_criterion(tenant_id, assess.criterion_id)
                if payload.adjusted_score < 0 or payload.adjusted_score > crit.max_score:
                    raise AccreditationInvalidScoreException(
                        f"Adjusted score {payload.adjusted_score} exceeds max allowed ({crit.max_score})."
                    )
                assess.score = payload.adjusted_score
        elif payload.decision == "CHANGES_REQUESTED":
            assess.status = AccreditationAssessmentStatus.CHANGES_REQUESTED
        elif payload.decision == "NON_COMPLIANT":
            assess.status = AccreditationAssessmentStatus.NON_COMPLIANT
        else:
            raise AccreditationInvalidScoreException(f"Unsupported review decision '{payload.decision}'.")

        assess.reviewer_id = actor_id
        assess.reviewed_at = datetime.now(UTC)
        assess.recommendations = (
            f"Review Note: {payload.reviewer_comments}\n" + (assess.recommendations or "")
        )
        assess.lock_version += 1

        await self.db.commit()
        await self.db.refresh(assess)

        await create_audit_entry(
            db=self.db,
            tenant_id=tenant_id,
            action=AuditEventCategory.ACCREDITATION_ASSESSMENT_APPROVED,
            entity_type="AccreditationCriterionAssessment",
            entity_id=assess.id,
            user_id=actor_id,
            business_context=f"Assessment decision recorded: {payload.decision}",
        )
        await self.db.commit()
        return assess

    # =========================================================================
    # 5. EVIDENCE REPOSITORY & TRACEABILITY
    # =========================================================================

    async def create_evidence(
        self, tenant_id: UUID, payload: AccreditationEvidenceCreate, actor_id: UUID
    ) -> AccreditationEvidence:
        evid = AccreditationEvidence(
            id=uuid4(),
            tenant_id=tenant_id,
            evidence_code=payload.evidence_code.strip().upper(),
            title=payload.title.strip(),
            description=payload.description,
            evidence_category=payload.evidence_category,
            source_type=payload.source_type,
            document_id=payload.document_id,
            knowledge_item_id=payload.knowledge_item_id,
            record_id=payload.record_id,
            external_uri=payload.external_uri,
            campus_id=payload.campus_id,
            department_id=payload.department_id,
            owner_user_id=actor_id,
            valid_from=payload.valid_from,
            valid_until=payload.valid_until,
            is_expired=False,
            confidentiality=payload.confidentiality,
            verification_status=AccreditationEvidenceVerificationStatus.UNVERIFIED,
            integrity_hash_sha256=payload.integrity_hash_sha256,
            metadata_json=payload.metadata_json or {},
        )
        self.db.add(evid)
        await self.db.commit()
        await self.db.refresh(evid)

        await create_audit_entry(
            db=self.db,
            tenant_id=tenant_id,
            action=AuditEventCategory.ACCREDITATION_EVIDENCE_ATTACHED,
            entity_type="AccreditationEvidence",
            entity_id=evid.id,
            user_id=actor_id,
            business_context=f"Created evidence item '{evid.evidence_code}'",
        )
        await self.db.commit()
        return evid

    async def get_evidence(self, tenant_id: UUID, evidence_id: UUID) -> AccreditationEvidence:
        stmt = select(AccreditationEvidence).where(
            AccreditationEvidence.tenant_id == tenant_id,
            AccreditationEvidence.id == evidence_id,
        )
        res = await self.db.execute(stmt)
        evid = res.scalar_one_or_none()
        if not evid:
            raise AccreditationEvidenceNotFoundException(evidence_id)
        return evid

    async def list_evidences(
        self,
        tenant_id: UUID,
        category: str | None = None,
        verification_status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AccreditationEvidence]:
        stmt = select(AccreditationEvidence).where(AccreditationEvidence.tenant_id == tenant_id)
        if category:
            stmt = stmt.where(AccreditationEvidence.evidence_category == category)
        if verification_status:
            stmt = stmt.where(AccreditationEvidence.verification_status == verification_status)
        stmt = stmt.order_by(desc(AccreditationEvidence.created_at)).limit(limit).offset(offset)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def verify_evidence(
        self, tenant_id: UUID, evidence_id: UUID, payload: AccreditationEvidenceVerify, actor_id: UUID
    ) -> AccreditationEvidence:
        evid = await self.get_evidence(tenant_id, evidence_id)
        evid.verification_status = payload.verification_status
        evid.reviewer_notes = payload.reviewer_notes.strip()
        evid.verified_by_user_id = actor_id
        evid.verified_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(evid)

        await create_audit_entry(
            db=self.db,
            tenant_id=tenant_id,
            action=AuditEventCategory.ACCREDITATION_EVIDENCE_VERIFIED,
            entity_type="AccreditationEvidence",
            entity_id=evid.id,
            user_id=actor_id,
            business_context=f"Verified evidence status: {payload.verification_status}",
        )
        await self.db.commit()
        return evid

    async def map_evidence_to_assessment(
        self, tenant_id: UUID, assessment_id: UUID, evidence_id: UUID, relevance_remarks: str | None, actor_id: UUID
    ) -> AccreditationCriterionEvidenceMap:
        await self.get_criterion_assessment(tenant_id, assessment_id)
        await self.get_evidence(tenant_id, evidence_id)

        mapping = AccreditationCriterionEvidenceMap(
            id=uuid4(),
            tenant_id=tenant_id,
            assessment_id=assessment_id,
            evidence_id=evidence_id,
            relevance_remarks=relevance_remarks,
            mapped_by_user_id=actor_id,
        )
        self.db.add(mapping)
        await self.db.commit()
        await self.db.refresh(mapping)
        return mapping

    # =========================================================================
    # 6. QUALITY INDICATORS & OBSERVATIONS
    # =========================================================================

    async def create_indicator(
        self, tenant_id: UUID, payload: QualityIndicatorCreate, actor_id: UUID
    ) -> QualityIndicator:
        qi = QualityIndicator(
            id=uuid4(),
            tenant_id=tenant_id,
            code=payload.code.strip().upper(),
            name=payload.name.strip(),
            description=payload.description,
            category=payload.category,
            source_module=payload.source_module,
            calculation_method=payload.calculation_method.strip(),
            reporting_frequency=payload.reporting_frequency,
            unit_of_measurement=payload.unit_of_measurement,
            target_value=payload.target_value,
            benchmark_threshold=payload.benchmark_threshold,
            data_quality_status=QualityDataQualityStatus.EXCELLENT,
            owner_user_id=actor_id,
            is_active=True,
            metadata_json=payload.metadata_json or {},
        )
        self.db.add(qi)
        await self.db.commit()
        await self.db.refresh(qi)
        return qi

    async def get_indicator(self, tenant_id: UUID, indicator_id: UUID) -> QualityIndicator:
        stmt = select(QualityIndicator).where(
            QualityIndicator.tenant_id == tenant_id,
            QualityIndicator.id == indicator_id,
        )
        res = await self.db.execute(stmt)
        qi = res.scalar_one_or_none()
        if not qi:
            raise AccreditationIndicatorNotFoundException(indicator_id)
        return qi

    async def list_indicators(
        self, tenant_id: UUID, category: str | None = None
    ) -> list[QualityIndicator]:
        stmt = select(QualityIndicator).where(QualityIndicator.tenant_id == tenant_id)
        if category:
            stmt = stmt.where(QualityIndicator.category == category)
        stmt = stmt.order_by(QualityIndicator.code)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def record_observation(
        self, tenant_id: UUID, indicator_id: UUID, payload: QualityIndicatorObservationCreate, actor_id: UUID
    ) -> QualityIndicatorObservation:
        qi = await self.get_indicator(tenant_id, indicator_id)
        obs = QualityIndicatorObservation(
            id=uuid4(),
            tenant_id=tenant_id,
            indicator_id=qi.id,
            period_label=payload.period_label.strip(),
            observation_date=payload.observation_date,
            observed_value=payload.observed_value,
            target_value=payload.target_value,
            data_source_mode=payload.data_source_mode,
            is_verified=payload.is_verified,
            data_completeness_pct=payload.data_completeness_pct,
            outlier_flag=payload.outlier_flag,
            notes=payload.notes,
            observed_by_user_id=actor_id,
        )
        self.db.add(obs)

        # Update current value on indicator
        qi.current_value = payload.observed_value
        qi.last_calculated_at = datetime.now(UTC)
        if payload.data_completeness_pct < 90.0:
            qi.data_quality_status = QualityDataQualityStatus.WARNING_INCOMPLETE
            qi.data_quality_notes = f"Completeness below 90%: Observation for {obs.period_label} has only {payload.data_completeness_pct}% completeness."
        elif payload.outlier_flag:
            qi.data_quality_status = QualityDataQualityStatus.WARNING_STALE
            qi.data_quality_notes = f"Outlier detected for {obs.period_label}: value {payload.observed_value}."
        else:
            qi.data_quality_status = QualityDataQualityStatus.EXCELLENT
            qi.data_quality_notes = None

        await self.db.commit()
        await self.db.refresh(obs)

        await create_audit_entry(
            db=self.db,
            tenant_id=tenant_id,
            action=AuditEventCategory.ACCREDITATION_INDICATOR_COMPUTED,
            entity_type="QualityIndicatorObservation",
            entity_id=obs.id,
            user_id=actor_id,
            business_context=f"Recorded observation for {qi.code} ({obs.period_label}): {obs.observed_value}",
        )
        await self.db.commit()
        return obs

    # =========================================================================
    # 7. INTERNAL QUALITY AUDITS
    # =========================================================================

    async def create_audit_program(
        self, tenant_id: UUID, payload: QualityAuditProgramCreate, actor_id: UUID
    ) -> QualityAuditProgram:
        prog = QualityAuditProgram(
            id=uuid4(),
            tenant_id=tenant_id,
            code=payload.code.strip().upper(),
            title=payload.title.strip(),
            description=payload.description,
            audit_type=payload.audit_type,
            scope=payload.scope,
            campus_id=payload.campus_id,
            department_id=payload.department_id,
            lead_auditor_id=actor_id,
            co_auditors_json=payload.co_auditors_json or [],
            scheduled_start_date=payload.scheduled_start_date,
            scheduled_end_date=payload.scheduled_end_date,
            status=QualityAuditStatus.PLANNED,
            conflict_of_interest_declared=payload.conflict_of_interest_declared,
            is_immutable=False,
            metadata_json=payload.metadata_json or {},
        )
        self.db.add(prog)
        await self.db.commit()
        await self.db.refresh(prog)

        await create_audit_entry(
            db=self.db,
            tenant_id=tenant_id,
            action=AuditEventCategory.ACCREDITATION_AUDIT_SCHEDULED,
            entity_type="QualityAuditProgram",
            entity_id=prog.id,
            user_id=actor_id,
            business_context=f"Scheduled audit program '{prog.code}'",
        )
        await self.db.commit()
        return prog

    async def get_audit_program(self, tenant_id: UUID, program_id: UUID) -> QualityAuditProgram:
        stmt = select(QualityAuditProgram).where(
            QualityAuditProgram.tenant_id == tenant_id,
            QualityAuditProgram.id == program_id,
        )
        res = await self.db.execute(stmt)
        prog = res.scalar_one_or_none()
        if not prog:
            raise AccreditationAuditNotFoundException(program_id)
        return prog

    async def list_audit_programs(
        self, tenant_id: UUID, status: str | None = None
    ) -> list[QualityAuditProgram]:
        stmt = select(QualityAuditProgram).where(QualityAuditProgram.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(QualityAuditProgram.status == status)
        stmt = stmt.order_by(desc(QualityAuditProgram.scheduled_start_date))
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def add_audit_checklist_item(
        self, tenant_id: UUID, program_id: UUID, payload: QualityAuditChecklistItemCreate, actor_id: UUID
    ) -> QualityAuditChecklistItem:
        prog = await self.get_audit_program(tenant_id, program_id)
        if prog.is_immutable:
            raise AccreditationAuditFinalizedException(prog.code)

        item = QualityAuditChecklistItem(
            id=uuid4(),
            tenant_id=tenant_id,
            audit_program_id=prog.id,
            criterion_id=payload.criterion_id,
            item_code=payload.item_code.strip().upper(),
            requirement_description=payload.requirement_description.strip(),
            compliance_status=payload.compliance_status,
            auditor_notes=payload.auditor_notes,
            evidence_reference=payload.evidence_reference,
            order_index=payload.order_index,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def finalize_audit_report(
        self,
        tenant_id: UUID,
        program_id: UUID | None = None,
        payload: QualityAuditFinalize | None = None,
        actor_id: UUID | None = None,
        audit_id: UUID | None = None,
    ) -> QualityAuditProgram:
        pid = program_id or audit_id
        if not pid:
            raise ValueError("Either program_id or audit_id must be provided")
        if payload is None or actor_id is None:
            raise ValueError("payload and actor_id must be provided")

        prog = await self.get_audit_program(tenant_id, pid)
        if prog.is_immutable:
            raise AccreditationAuditFinalizedException(prog.code)

        prog.summary_findings = payload.summary_findings.strip()
        prog.recommendations = payload.recommendations.strip()
        prog.status = QualityAuditStatus.FINALIZED
        prog.finalized_at = datetime.now(UTC)
        prog.actual_completion_date = datetime.now(UTC)
        prog.finalized_by_user_id = actor_id
        prog.is_immutable = True  # Permanently immutable

        await self.db.commit()
        await self.db.refresh(prog)

        await create_audit_entry(
            db=self.db,
            tenant_id=tenant_id,
            action=AuditEventCategory.ACCREDITATION_AUDIT_FINALIZED,
            entity_type="QualityAuditProgram",
            entity_id=prog.id,
            user_id=actor_id,
            business_context=f"Finalized and locked audit report '{prog.code}'",
        )
        await self.db.commit()
        return prog

    # =========================================================================
    # 8. FINDINGS & CORRECTIVE ACTIONS (CAPA)
    # =========================================================================

    async def create_finding(
        self, tenant_id: UUID, payload: QualityFindingCreate, actor_id: UUID
    ) -> QualityFinding:
        finding = QualityFinding(
            id=uuid4(),
            tenant_id=tenant_id,
            finding_code=payload.finding_code.strip().upper(),
            source_type=payload.source_type,
            audit_program_id=payload.audit_program_id,
            criterion_id=payload.criterion_id,
            department_id=payload.department_id,
            title=payload.title.strip(),
            description=payload.description.strip(),
            root_cause_analysis=payload.root_cause_analysis,
            severity=payload.severity,
            status=QualityFindingStatus.OPEN,
            identified_by_user_id=actor_id,
            assigned_owner_id=payload.assigned_owner_id,
            target_resolution_date=payload.target_resolution_date,
            metadata_json=payload.metadata_json or {},
        )
        self.db.add(finding)
        await self.db.commit()
        await self.db.refresh(finding)
        return finding

    async def get_finding(self, tenant_id: UUID, finding_id: UUID) -> QualityFinding:
        stmt = select(QualityFinding).where(
            QualityFinding.tenant_id == tenant_id,
            QualityFinding.id == finding_id,
        )
        res = await self.db.execute(stmt)
        finding = res.scalar_one_or_none()
        if not finding:
            raise AccreditationFindingNotFoundException(finding_id)
        return finding

    async def list_findings(
        self, tenant_id: UUID, status: str | None = None, severity: str | None = None
    ) -> list[QualityFinding]:
        stmt = select(QualityFinding).where(QualityFinding.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(QualityFinding.status == status)
        if severity:
            stmt = stmt.where(QualityFinding.severity == severity)
        stmt = stmt.order_by(desc(QualityFinding.created_at))
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create_corrective_action(
        self, tenant_id: UUID, finding_id: UUID, payload: QualityCAPACreate, actor_id: UUID
    ) -> QualityCorrectiveAction:
        finding = await self.get_finding(tenant_id, finding_id)
        capa = QualityCorrectiveAction(
            id=uuid4(),
            tenant_id=tenant_id,
            finding_id=finding.id,
            action_code=payload.action_code.strip().upper(),
            action_type=payload.action_type,
            proposed_action=payload.proposed_action.strip(),
            preventive_measures=payload.preventive_measures,
            responsible_owner_id=payload.responsible_owner_id,
            status=QualityCAPAStatus.IN_PROGRESS,
            due_date=payload.due_date,
            verification_criteria=payload.verification_criteria.strip(),
            metadata_json=payload.metadata_json or {},
        )
        self.db.add(capa)
        finding.status = QualityFindingStatus.IN_PROGRESS
        await self.db.commit()
        await self.db.refresh(capa)

        await create_audit_entry(
            db=self.db,
            tenant_id=tenant_id,
            action=AuditEventCategory.ACCREDITATION_CAPA_CREATED,
            entity_type="QualityCorrectiveAction",
            entity_id=capa.id,
            user_id=actor_id,
            business_context=f"Created CAPA '{capa.action_code}' for finding '{finding.finding_code}'",
        )
        await self.db.commit()
        return capa

    async def get_corrective_action(self, tenant_id: UUID, action_id: UUID) -> QualityCorrectiveAction:
        stmt = select(QualityCorrectiveAction).where(
            QualityCorrectiveAction.tenant_id == tenant_id,
            QualityCorrectiveAction.id == action_id,
        )
        res = await self.db.execute(stmt)
        capa = res.scalar_one_or_none()
        if not capa:
            raise AccreditationCAPANotFoundException(action_id)
        return capa

    async def close_corrective_action(
        self, tenant_id: UUID, action_id: UUID, payload: QualityCAPAClose, actor_id: UUID
    ) -> QualityCorrectiveAction:
        """Verify and close corrective action enforcing strict Separation of Duties."""
        capa = await self.get_corrective_action(tenant_id, action_id)

        # Separation of Duties: Action owner cannot verify their own closure
        if capa.responsible_owner_id == actor_id:
            raise AccreditationSeparationOfDutiesException(
                "verify and close their own corrective action (CAPA)"
            )

        if payload.closure_decision == "CLOSED_EFFECTIVE":
            capa.status = QualityCAPAStatus.VERIFIED_EFFECTIVE
            capa.closure_decision = "CLOSED_EFFECTIVE"
            capa.completed_at = datetime.now(UTC)
            # Check finding closure
            finding = await self.get_finding(tenant_id, capa.finding_id)
            finding.status = QualityFindingStatus.CLOSED
            finding.resolved_at = datetime.now(UTC)
        elif payload.closure_decision == "REJECTED_FURTHER_ACTION":
            capa.status = QualityCAPAStatus.REJECTED
            capa.closure_decision = "REJECTED_FURTHER_ACTION"
        else:
            raise AccreditationCAPAClosureDeniedException(
                f"Unsupported closure decision '{payload.closure_decision}'."
            )

        capa.closure_notes = payload.closure_notes.strip()
        capa.evidence_notes = payload.evidence_notes
        capa.evidence_document_id = payload.evidence_document_id
        capa.verified_by_user_id = actor_id
        capa.verified_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(capa)

        await create_audit_entry(
            db=self.db,
            tenant_id=tenant_id,
            action=AuditEventCategory.ACCREDITATION_CAPA_CLOSED,
            entity_type="QualityCorrectiveAction",
            entity_id=capa.id,
            user_id=actor_id,
            business_context=f"CAPA closure recorded: {payload.closure_decision}",
        )
        await self.db.commit()
        return capa

    # =========================================================================
    # 9. CONTINUOUS QUALITY IMPROVEMENT (CQI)
    # =========================================================================

    async def create_improvement_plan(
        self, tenant_id: UUID, payload: QualityImprovementPlanCreate, actor_id: UUID
    ) -> QualityImprovementPlan:
        plan = QualityImprovementPlan(
            id=uuid4(),
            tenant_id=tenant_id,
            code=payload.code.strip().upper(),
            title=payload.title.strip(),
            objective=payload.objective.strip(),
            baseline_measurement=payload.baseline_measurement.strip(),
            target_outcome=payload.target_outcome.strip(),
            linked_indicator_id=payload.linked_indicator_id,
            responsible_owner_id=payload.responsible_owner_id,
            start_date=payload.start_date,
            target_date=payload.target_date,
            status=QualityImprovementStatus.ACTIVE,
            metadata_json=payload.metadata_json or {},
        )
        self.db.add(plan)
        await self.db.commit()
        await self.db.refresh(plan)
        return plan

    async def list_improvement_plans(
        self, tenant_id: UUID, status: str | None = None
    ) -> list[QualityImprovementPlan]:
        stmt = select(QualityImprovementPlan).where(QualityImprovementPlan.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(QualityImprovementPlan.status == status)
        stmt = stmt.order_by(desc(QualityImprovementPlan.created_at))
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    # =========================================================================
    # 10. ACCREDITATION READINESS & GAP ANALYSIS ENGINE
    # =========================================================================

    async def calculate_readiness_snapshot(
        self, tenant_id: UUID, cycle_id: UUID, actor_id: UUID
    ) -> AccreditationReadinessSnapshot:
        """Execute transparent readiness assessment and gap analysis for an assessment cycle."""
        cycle = await self.get_assessment_cycle(tenant_id, cycle_id)
        fw = await self.get_framework(tenant_id, cycle.framework_id)

        # 1. Criteria evaluation
        assessments_res = await self.db.execute(
            select(AccreditationCriterionAssessment, AccreditationCriterion).join(
                AccreditationCriterion,
                AccreditationCriterionAssessment.criterion_id == AccreditationCriterion.id,
            ).where(
                AccreditationCriterionAssessment.tenant_id == tenant_id,
                AccreditationCriterionAssessment.cycle_id == cycle_id,
            )
        )
        assess_pairs = assessments_res.all()
        criteria_total = len(assess_pairs)
        criteria_assessed = 0
        total_projected_score = 0.0
        total_max_score = 0.0
        gap_items: list[dict[str, Any]] = []

        for assess, crit in assess_pairs:
            total_max_score += crit.max_score
            if assess.status == AccreditationAssessmentStatus.APPROVED:
                criteria_assessed += 1
                total_projected_score += (assess.score or 0.0)
            elif assess.status == AccreditationAssessmentStatus.NOT_APPLICABLE:
                criteria_assessed += 1
            else:
                gap_items.append({
                    "criterion_id": str(crit.id),
                    "criterion_code": crit.code,
                    "title": crit.title,
                    "status": assess.status,
                    "missing": "Assessment not yet approved or completed",
                    "weight": crit.weight,
                })

        # 2. Evidence evaluation
        evid_maps_res = await self.db.execute(
            select(AccreditationCriterionEvidenceMap, AccreditationEvidence).join(
                AccreditationEvidence,
                AccreditationCriterionEvidenceMap.evidence_id == AccreditationEvidence.id,
            ).where(
                AccreditationCriterionEvidenceMap.tenant_id == tenant_id,
            )
        )
        evid_pairs = evid_maps_res.all()
        evidence_required_count = criteria_total * 2  # Benchmark: 2 pieces of verified evidence per criterion
        evidence_verified_count = sum(
            1 for _, evid in evid_pairs if evid.verification_status == AccreditationEvidenceVerificationStatus.VERIFIED
        )

        # 3. Open high risk findings
        findings_res = await self.db.execute(
            select(func.count()).select_from(QualityFinding).where(
                QualityFinding.tenant_id == tenant_id,
                QualityFinding.status != QualityFindingStatus.CLOSED,
                QualityFinding.severity.in_([QualityFindingSeverity.HIGH, QualityFindingSeverity.CRITICAL]),
            )
        )
        open_high_risk = findings_res.scalar_one() or 0

        # 4. Transparent formula
        crit_coverage_pct = (criteria_assessed / criteria_total * 100.0) if criteria_total > 0 else 0.0
        evid_coverage_pct = (
            min(evidence_verified_count / max(evidence_required_count, 1), 1.0) * 100.0
        )
        score_proj_pct = (
            (total_projected_score / total_max_score * 100.0) if total_max_score > 0 else 0.0
        )

        # Readiness composite: 40% criteria completion + 30% evidence + 30% projected score - (5% per open critical finding)
        penalty = open_high_risk * 5.0
        overall_readiness = max(
            0.0,
            min(
                100.0,
                (0.4 * crit_coverage_pct) + (0.3 * evid_coverage_pct) + (0.3 * score_proj_pct) - penalty,
            ),
        )

        if overall_readiness >= 85.0:
            category = AccreditationReadinessCategory.HIGH_READINESS
        elif overall_readiness >= 70.0:
            category = AccreditationReadinessCategory.SUBSTANTIAL_PROGRESS
        elif overall_readiness >= 50.0:
            category = AccreditationReadinessCategory.SIGNIFICANT_GAPS
        else:
            category = AccreditationReadinessCategory.CRITICAL_REMEDIATION_NEEDED

        snapshot = AccreditationReadinessSnapshot(
            id=uuid4(),
            tenant_id=tenant_id,
            cycle_id=cycle.id,
            framework_id=fw.id,
            overall_readiness_score=round(overall_readiness, 2),
            criteria_assessed_count=criteria_assessed,
            criteria_total_count=criteria_total,
            evidence_verified_count=evidence_verified_count,
            evidence_required_count=evidence_required_count,
            open_high_risk_findings_count=open_high_risk,
            score_projected=round(total_projected_score, 2),
            score_maximum=round(total_max_score, 2),
            readiness_category=category,
            gap_summary_json=gap_items[:20],  # Top 20 priority gaps
            department_readiness_json={
                "criteria_coverage_pct": round(crit_coverage_pct, 2),
                "evidence_coverage_pct": round(evid_coverage_pct, 2),
                "score_projection_pct": round(score_proj_pct, 2),
            },
            calculated_by_user_id=actor_id,
        )
        self.db.add(snapshot)

        # Update cycle readiness
        cycle.readiness_percentage = round(overall_readiness, 2)
        cycle.overall_score = round(total_projected_score, 2)

        await self.db.commit()
        await self.db.refresh(snapshot)

        await create_audit_entry(
            db=self.db,
            tenant_id=tenant_id,
            action=AuditEventCategory.ACCREDITATION_READINESS_EVALUATED,
            entity_type="AccreditationReadinessSnapshot",
            entity_id=snapshot.id,
            user_id=actor_id,
            business_context=f"Computed readiness for cycle '{cycle.code}': {snapshot.overall_readiness_score}%",
        )
        await self.db.commit()
        return snapshot

    # =========================================================================
    # 11. DASHBOARD SUMMARY & BACKGROUND SWEEP
    # =========================================================================

    async def get_dashboard_summary(self, tenant_id: UUID) -> AccreditationDashboardSummary:
        fw_count = (await self.db.execute(
            select(func.count()).select_from(AccreditationFramework).where(
                AccreditationFramework.tenant_id == tenant_id,
                AccreditationFramework.status == AccreditationFrameworkStatus.ACTIVE,
            )
        )).scalar_one() or 0

        cycle_count = (await self.db.execute(
            select(func.count()).select_from(AccreditationAssessmentCycle).where(
                AccreditationAssessmentCycle.tenant_id == tenant_id,
                AccreditationAssessmentCycle.status == "ACTIVE",
            )
        )).scalar_one() or 0

        crit_count = (await self.db.execute(
            select(func.count()).select_from(AccreditationCriterion).where(
                AccreditationCriterion.tenant_id == tenant_id,
                AccreditationCriterion.is_active.is_(True),
            )
        )).scalar_one() or 0

        assessed_count = (await self.db.execute(
            select(func.count()).select_from(AccreditationCriterionAssessment).where(
                AccreditationCriterionAssessment.tenant_id == tenant_id,
                AccreditationCriterionAssessment.status.in_([
                    AccreditationAssessmentStatus.APPROVED,
                    AccreditationAssessmentStatus.NOT_APPLICABLE,
                ]),
            )
        )).scalar_one() or 0

        total_evid = (await self.db.execute(
            select(func.count()).select_from(AccreditationEvidence).where(
                AccreditationEvidence.tenant_id == tenant_id,
            )
        )).scalar_one() or 0

        verified_evid = (await self.db.execute(
            select(func.count()).select_from(AccreditationEvidence).where(
                AccreditationEvidence.tenant_id == tenant_id,
                AccreditationEvidence.verification_status == AccreditationEvidenceVerificationStatus.VERIFIED,
            )
        )).scalar_one() or 0

        open_findings = (await self.db.execute(
            select(func.count()).select_from(QualityFinding).where(
                QualityFinding.tenant_id == tenant_id,
                QualityFinding.status != QualityFindingStatus.CLOSED,
            )
        )).scalar_one() or 0

        crit_findings = (await self.db.execute(
            select(func.count()).select_from(QualityFinding).where(
                QualityFinding.tenant_id == tenant_id,
                QualityFinding.status != QualityFindingStatus.CLOSED,
                QualityFinding.severity == QualityFindingSeverity.CRITICAL,
            )
        )).scalar_one() or 0

        active_audits = (await self.db.execute(
            select(func.count()).select_from(QualityAuditProgram).where(
                QualityAuditProgram.tenant_id == tenant_id,
                QualityAuditProgram.status.in_([QualityAuditStatus.PLANNED, QualityAuditStatus.IN_PROGRESS]),
            )
        )).scalar_one() or 0

        active_cqi = (await self.db.execute(
            select(func.count()).select_from(QualityImprovementPlan).where(
                QualityImprovementPlan.tenant_id == tenant_id,
                QualityImprovementPlan.status == QualityImprovementStatus.ACTIVE,
            )
        )).scalar_one() or 0

        avg_readiness = (await self.db.execute(
            select(func.avg(AccreditationAssessmentCycle.readiness_percentage)).where(
                AccreditationAssessmentCycle.tenant_id == tenant_id,
                AccreditationAssessmentCycle.status == "ACTIVE",
            )
        )).scalar_one() or 0.0

        return AccreditationDashboardSummary(
            active_frameworks_count=fw_count,
            active_cycles_count=cycle_count,
            total_criteria_count=crit_count,
            assessed_criteria_count=assessed_count,
            verified_evidences_count=verified_evid,
            total_evidences_count=total_evid,
            open_findings_count=open_findings,
            critical_findings_count=crit_findings,
            active_audits_count=active_audits,
            active_cqi_plans_count=active_cqi,
            overall_readiness_avg_pct=round(float(avg_readiness), 2),
        )

    async def sweep_quality_reviews(self) -> dict[str, Any]:
        """Scheduled task to flag expired evidence, overdue findings, and overdue CAPAs across all tenants."""
        now = datetime.now(UTC)

        # 1. Flag expired evidence
        exp_res = await self.db.execute(
            select(AccreditationEvidence).where(
                AccreditationEvidence.valid_until.is_not(None),
                AccreditationEvidence.valid_until < now,
                AccreditationEvidence.is_expired.is_(False),
            )
        )
        expired_evidences = exp_res.scalars().all()
        for evid in expired_evidences:
            evid.is_expired = True
            evid.verification_status = AccreditationEvidenceVerificationStatus.EXPIRED

        # 2. Flag overdue findings
        f_res = await self.db.execute(
            select(QualityFinding).where(
                QualityFinding.target_resolution_date < now,
                QualityFinding.status.in_([QualityFindingStatus.OPEN, QualityFindingStatus.ASSIGNED, QualityFindingStatus.IN_PROGRESS]),
            )
        )
        overdue_findings = f_res.scalars().all()
        for f in overdue_findings:
            f.status = QualityFindingStatus.OVERDUE

        # 3. Flag overdue CAPAs
        capa_res = await self.db.execute(
            select(QualityCorrectiveAction).where(
                QualityCorrectiveAction.due_date < now,
                QualityCorrectiveAction.status == QualityCAPAStatus.IN_PROGRESS,
            )
        )
        overdue_capas = capa_res.scalars().all()
        for c in overdue_capas:
            c.status = QualityCAPAStatus.PROPOSED  # requires escalation review

        await self.db.commit()
        return {
            "expired_evidences_flagged": len(expired_evidences),
            "expired_evidence_flagged": len(expired_evidences),
            "overdue_findings_flagged": len(overdue_findings),
            "overdue_finding_flagged": len(overdue_findings),
            "overdue_capas_flagged": len(overdue_capas),
            "overdue_capa_flagged": len(overdue_capas),
            "executed_at": now.isoformat(),
        }
