"""Master Data Service Orchestrator (Step 24).

Central control plane for governed Master Data Definitions, Controlled Reference Data,
Data Quality Scoring, Stewardship Queue, Corrections, Lineage, and Quality Analytics.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventCategory, build_audit_entry
from app.core.exceptions import (
    MasterDataCorrectionNotFoundException,
    MasterDataDefinitionNotFoundException,
    MasterDataRecordNotFoundException,
    ReferenceDataConflictException,
    ReferenceDataNotFoundException,
)
from app.models.core import Department
from app.models.master_data import (
    CorrectionStatus,
    DataQualityIssue,
    DataQualityResult,
    DataQualityRule,
    DuplicateCandidate,
    LineageSource,
    MasterDataCorrection,
    MasterDataDefinition,
    MasterDataLineage,
    MasterDataType,
    QualityIssueStatus,
    ReferenceDataDefinition,
    ReferenceDataValue,
)
from app.models.people import StudentProfile
from app.models.placement import Company
from app.repositories.master_data_repository import MasterDataRepository
from app.schemas.master_data import (
    DataQualityRuleCreate,
    DataQualityRuleUpdate,
    DataQualitySummaryResponse,
    DataQualityValidateResponse,
    MasterDataCorrectionCreate,
    MasterDataDefinitionCreate,
    MasterDataDefinitionUpdate,
    MasterDataLineageCreate,
    ReferenceDataDefinitionCreate,
    ReferenceDataValueCreate,
    ReferenceDataValueUpdate,
)
from app.services.quality_rule_evaluator import QualityRuleEvaluator


class MasterDataService:
    """Enterprise service orchestrating Master Data and Data Quality governance."""

    # -------------------------------------------------------------------------
    # 1. Definitions
    # -------------------------------------------------------------------------

    @classmethod
    async def get_definition(cls, db: AsyncSession, key: str) -> MasterDataDefinition:
        repo = MasterDataRepository(db)
        defn = await repo.get_definition_by_key(key)
        if not defn:
            raise MasterDataDefinitionNotFoundException(key)
        return defn

    @classmethod
    async def list_definitions(
        cls, db: AsyncSession, is_active: bool | None = None
    ) -> list[MasterDataDefinition]:
        repo = MasterDataRepository(db)
        return await repo.list_definitions(is_active=is_active)

    @classmethod
    async def create_definition(
        cls, db: AsyncSession, dto: MasterDataDefinitionCreate, actor_id: UUID | None = None
    ) -> MasterDataDefinition:
        repo = MasterDataRepository(db)
        existing = await repo.get_definition_by_key(dto.key)
        if existing:
            raise MasterDataDefinitionNotFoundException(
                f"Master data definition '{dto.key}' already exists."
            )

        defn = MasterDataDefinition(
            key=dto.key.upper(),
            display_name=dto.display_name,
            description=dto.description,
            owner_domain=dto.owner_domain,
            steward_role=dto.steward_role,
            sensitivity=dto.sensitivity,
            duplicate_detection_enabled=dto.duplicate_detection_enabled,
            merge_supported=dto.merge_supported,
            archival_supported=dto.archival_supported,
            authoritative_source=dto.authoritative_source,
            canonical_table_name=dto.canonical_table_name,
            canonical_id_column=dto.canonical_id_column,
            is_active=dto.is_active,
        )
        created = await repo.create_definition(defn)
        return created

    @classmethod
    async def update_definition(
        cls,
        db: AsyncSession,
        key: str,
        dto: MasterDataDefinitionUpdate,
        actor_id: UUID | None = None,
    ) -> MasterDataDefinition:
        defn = await cls.get_definition(db, key)
        if dto.display_name is not None:
            defn.display_name = dto.display_name
        if dto.description is not None:
            defn.description = dto.description
        if dto.steward_role is not None:
            defn.steward_role = dto.steward_role
        if dto.sensitivity is not None:
            defn.sensitivity = dto.sensitivity
        if dto.duplicate_detection_enabled is not None:
            defn.duplicate_detection_enabled = dto.duplicate_detection_enabled
        if dto.merge_supported is not None:
            defn.merge_supported = dto.merge_supported
        if dto.archival_supported is not None:
            defn.archival_supported = dto.archival_supported
        if dto.is_active is not None:
            defn.is_active = dto.is_active

        repo = MasterDataRepository(db)
        return await repo.update_definition(defn)

    # -------------------------------------------------------------------------
    # 2. Reference Data
    # -------------------------------------------------------------------------

    @classmethod
    async def create_reference_definition(
        cls, db: AsyncSession, dto: ReferenceDataDefinitionCreate
    ) -> ReferenceDataDefinition:
        repo = MasterDataRepository(db)
        existing = await repo.get_ref_definition(dto.category)
        if existing:
            raise ReferenceDataConflictException(
                f"Reference category '{dto.category}' already exists."
            )

        ref_def = ReferenceDataDefinition(
            category=dto.category.upper(),
            name=dto.name,
            description=dto.description,
            is_system=dto.is_system,
            is_active=dto.is_active,
        )
        return await repo.create_ref_definition(ref_def)

    @classmethod
    async def list_reference_definitions(
        cls, db: AsyncSession, is_active: bool | None = None
    ) -> list[ReferenceDataDefinition]:
        repo = MasterDataRepository(db)
        return await repo.list_ref_definitions(is_active=is_active)

    @classmethod
    async def create_reference_value(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        dto: ReferenceDataValueCreate,
        actor_id: UUID | None = None,
    ) -> ReferenceDataValue:
        repo = MasterDataRepository(db)
        existing = await repo.get_ref_value(tenant_id, dto.category, dto.code)
        if existing:
            raise ReferenceDataConflictException(
                f"Reference code '{dto.code}' already exists in category '{dto.category}'."
            )

        val = ReferenceDataValue(
            tenant_id=tenant_id,
            category=dto.category.upper(),
            code=dto.code.upper(),
            label=dto.label,
            description=dto.description,
            display_order=dto.display_order,
            metadata_json=dto.metadata_json,
            effective_from=dto.effective_from,
            effective_until=dto.effective_until,
            is_active=dto.is_active,
            is_system=False,
            created_by=actor_id,
        )
        created = await repo.create_ref_value(val)

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.REFERENCE_DATA_CREATED,
            entity_type="reference_data_value",
            entity_id=created.id,
            user_id=actor_id,
            business_context=f"Reference value '{dto.category}:{dto.code}' created.",
        )
        db.add(audit)
        await db.flush()

        return created

    @classmethod
    async def list_reference_values(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        category: str | None = None,
        is_active: bool | None = None,
    ) -> list[ReferenceDataValue]:
        repo = MasterDataRepository(db)
        return await repo.list_ref_values(tenant_id, category=category, is_active=is_active)

    @classmethod
    async def update_reference_value(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        value_id: UUID,
        dto: ReferenceDataValueUpdate,
        actor_id: UUID | None = None,
    ) -> ReferenceDataValue:
        repo = MasterDataRepository(db)
        val = await repo.get_ref_value_by_id(value_id, tenant_id)
        if not val:
            raise ReferenceDataNotFoundException(str(value_id))

        if dto.label is not None:
            val.label = dto.label
        if dto.description is not None:
            val.description = dto.description
        if dto.display_order is not None:
            val.display_order = dto.display_order
        if dto.metadata_json is not None:
            val.metadata_json = dto.metadata_json
        if dto.effective_from is not None:
            val.effective_from = dto.effective_from
        if dto.effective_until is not None:
            val.effective_until = dto.effective_until
        if dto.is_active is not None:
            val.is_active = dto.is_active
        val.updated_by = actor_id

        await db.flush()
        return val

    @classmethod
    async def delete_reference_value(
        cls, db: AsyncSession, tenant_id: UUID, value_id: UUID, actor_id: UUID | None = None
    ) -> bool:
        repo = MasterDataRepository(db)
        val = await repo.get_ref_value_by_id(value_id, tenant_id)
        if not val:
            raise ReferenceDataNotFoundException(str(value_id))
        if val.is_system:
            raise ReferenceDataConflictException(
                "System-critical reference data values cannot be deleted. Deactivate instead."
            )

        val.is_active = False
        val.updated_by = actor_id
        await db.flush()
        return True

    # -------------------------------------------------------------------------
    # 3. Quality Rules
    # -------------------------------------------------------------------------

    @classmethod
    async def create_quality_rule(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        dto: DataQualityRuleCreate,
        actor_id: UUID | None = None,
    ) -> DataQualityRule:
        repo = MasterDataRepository(db)
        rule = DataQualityRule(
            tenant_id=tenant_id,
            master_type=dto.master_type.upper(),
            rule_key=dto.rule_key,
            name=dto.name,
            description=dto.description,
            field_name=dto.field_name,
            rule_type=dto.rule_type,
            severity=dto.severity,
            parameters_json=dto.parameters_json,
            weight=dto.weight,
            is_active=dto.is_active,
            version=1,
        )
        created = await repo.create_rule(rule)
        return created

    @classmethod
    async def list_quality_rules(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        master_type: str | None = None,
        is_active: bool | None = None,
    ) -> list[DataQualityRule]:
        repo = MasterDataRepository(db)
        return await repo.list_rules(tenant_id, master_type=master_type, is_active=is_active)

    @classmethod
    async def update_quality_rule(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        rule_id: UUID,
        dto: DataQualityRuleUpdate,
        actor_id: UUID | None = None,
    ) -> DataQualityRule:
        repo = MasterDataRepository(db)
        rule = await repo.get_rule_by_id(rule_id, tenant_id)
        if not rule:
            raise ReferenceDataNotFoundException(f"Quality rule {rule_id}")

        if dto.name is not None:
            rule.name = dto.name
        if dto.description is not None:
            rule.description = dto.description
        if dto.field_name is not None:
            rule.field_name = dto.field_name
        if dto.severity is not None:
            rule.severity = dto.severity
        if dto.parameters_json is not None:
            rule.parameters_json = dto.parameters_json
        if dto.weight is not None:
            rule.weight = dto.weight
        if dto.is_active is not None:
            rule.is_active = dto.is_active
        rule.version += 1

        await db.flush()
        return rule

    # -------------------------------------------------------------------------
    # 4. Evaluation & Quality Score Calculation
    # -------------------------------------------------------------------------

    @classmethod
    async def validate_record(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        master_type: str,
        payload: dict[str, Any],
        record_id: UUID | None = None,
    ) -> DataQualityValidateResponse:
        """Evaluate active quality rules against a data payload and compute scores."""
        repo = MasterDataRepository(db)
        rules = await repo.list_rules(tenant_id, master_type=master_type, is_active=True)
        overall, dims, evaluations = QualityRuleEvaluator.evaluate_all(rules, payload)

        passed_count = sum(1 for e in evaluations if e.passed)
        failed_count = sum(1 for e in evaluations if not e.passed)

        # If evaluating a persisted record, persist snapshot and track issues
        if record_id is not None:
            res_entry = DataQualityResult(
                tenant_id=tenant_id,
                master_type=master_type.upper(),
                record_id=record_id,
                overall_score=overall,
                dimension_scores_json=dims,
                rule_results_json=[e.model_dump() for e in evaluations],
            )
            await repo.create_quality_result(res_entry)

            # Record failed evaluations as open issues
            for ev in evaluations:
                if not ev.passed:
                    rule_obj = next((r for r in rules if r.rule_key == ev.rule_key), None)
                    issue = DataQualityIssue(
                        tenant_id=tenant_id,
                        master_type=master_type.upper(),
                        record_id=record_id,
                        rule_id=rule_obj.id if rule_obj else None,
                        rule_key=ev.rule_key,
                        severity=ev.severity,
                        status=QualityIssueStatus.OPEN,
                        issue_message=ev.message or f"Rule {ev.rule_name} failed.",
                        field_name=ev.field_name,
                    )
                    await repo.create_quality_issue(issue)

        return DataQualityValidateResponse(
            master_type=master_type.upper(),
            overall_score=overall,
            dimension_scores=dims,
            passed_rules_count=passed_count,
            failed_rules_count=failed_count,
            rule_evaluations=evaluations,
        )

    # -------------------------------------------------------------------------
    # 5. Quality Issues Management
    # -------------------------------------------------------------------------

    @classmethod
    async def list_quality_issues(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        master_type: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[DataQualityIssue], int]:
        repo = MasterDataRepository(db)
        return await repo.list_quality_issues(
            tenant_id,
            master_type=master_type,
            status=status,
            severity=severity,
            limit=limit,
            offset=offset,
        )

    @classmethod
    async def get_quality_issue(
        cls, db: AsyncSession, tenant_id: UUID, issue_id: UUID
    ) -> DataQualityIssue:
        repo = MasterDataRepository(db)
        issue = await repo.get_quality_issue(issue_id, tenant_id)
        if not issue:
            raise MasterDataRecordNotFoundException("data_quality_issue", str(issue_id))
        return issue

    @classmethod
    async def get_duplicate_candidate(
        cls, db: AsyncSession, tenant_id: UUID, candidate_id: UUID
    ) -> DuplicateCandidate:
        repo = MasterDataRepository(db)
        cand = await repo.get_duplicate_candidate(candidate_id, tenant_id)
        if not cand:
            raise MasterDataRecordNotFoundException("duplicate_candidate", str(candidate_id))
        return cand

    @classmethod
    async def update_quality_issue(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        issue_id: UUID,
        status: QualityIssueStatus | None = None,
        assigned_to: UUID | None = None,
        notes: str | None = None,
        actor_id: UUID | None = None,
        dto: Any | None = None,
    ) -> DataQualityIssue:
        repo = MasterDataRepository(db)
        issue = await repo.get_quality_issue(issue_id, tenant_id)
        if not issue:
            raise MasterDataRecordNotFoundException("data_quality_issue", str(issue_id))

        if dto is not None:
            if getattr(dto, "status", None) is not None:
                status = dto.status
            if getattr(dto, "assigned_to", None) is not None:
                assigned_to = dto.assigned_to
            if getattr(dto, "resolution_notes", None) is not None:
                notes = dto.resolution_notes

        if status is not None:
            issue.status = status
            if status == QualityIssueStatus.RESOLVED:
                issue.resolved_at = datetime.now(UTC)
        if assigned_to is not None:
            issue.assigned_to = assigned_to
        if notes is not None:
            issue.resolution_notes = notes

        await db.flush()
        return issue

    @classmethod
    async def list_duplicate_candidates(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        master_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Any], int]:
        repo = MasterDataRepository(db)
        return await repo.list_duplicate_candidates(
            tenant_id, master_type=master_type, status=status, limit=limit, offset=offset
        )

    @classmethod
    async def review_duplicate_candidate(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        candidate_id: UUID,
        reviewer_id: UUID,
        dto: Any,
    ) -> Any:
        from app.services.duplicate_detection_service import DuplicateDetectionService

        return await DuplicateDetectionService.review_candidate(
            db=db,
            tenant_id=tenant_id,
            candidate_id=candidate_id,
            status=dto.status,
            reviewer_id=reviewer_id,
            notes=getattr(dto, "notes", None) or getattr(dto, "review_notes", None),
        )

    # -------------------------------------------------------------------------
    # 6. Quality Summary & Analytics Dashboard
    # -------------------------------------------------------------------------

    @classmethod
    async def get_quality_summary(
        cls, db: AsyncSession, tenant_id: UUID
    ) -> DataQualitySummaryResponse:
        """Compute aggregate quality summary metrics across all governed master domains."""
        repo = MasterDataRepository(db)

        # Count records across domains
        student_cnt = (
            await db.execute(
                select(func.count())
                .select_from(StudentProfile)
                .where(StudentProfile.tenant_id == tenant_id, StudentProfile.status != "MERGED")
            )
        ).scalar() or 0

        dept_cnt = (
            await db.execute(
                select(func.count())
                .select_from(Department)
                .where(
                    Department.tenant_id == tenant_id,
                    Department.is_active == True,  # noqa: E712
                )
            )
        ).scalar() or 0

        comp_cnt = (
            await db.execute(
                select(func.count())
                .select_from(Company)
                .where(Company.tenant_id == tenant_id, Company.status != "MERGED")
            )
        ).scalar() or 0

        total_governed = student_cnt + dept_cnt + comp_cnt

        # Open issues counts
        open_issues_count = (
            await db.execute(
                select(func.count())
                .select_from(DataQualityIssue)
                .where(
                    DataQualityIssue.tenant_id == tenant_id,
                    DataQualityIssue.status.in_(
                        [QualityIssueStatus.OPEN, QualityIssueStatus.IN_PROGRESS]
                    ),
                )
            )
        ).scalar() or 0

        resolved_issues_count = (
            await db.execute(
                select(func.count())
                .select_from(DataQualityIssue)
                .where(
                    DataQualityIssue.tenant_id == tenant_id,
                    DataQualityIssue.status == QualityIssueStatus.RESOLVED,
                )
            )
        ).scalar() or 0

        severity_counts = await repo.count_open_issues_by_severity(tenant_id)
        critical_cnt = severity_counts.get("CRITICAL", 0)
        error_cnt = severity_counts.get("ERROR", 0)
        warning_cnt = severity_counts.get("WARNING", 0)

        pending_dups = await repo.count_pending_duplicates(tenant_id)

        # Average quality score from results
        avg_score_res = await db.execute(
            select(func.avg(DataQualityResult.overall_score)).where(
                DataQualityResult.tenant_id == tenant_id
            )
        )
        avg_score = float(avg_score_res.scalar() or 95.0)

        dimension_averages = {
            "completeness": round(avg_score, 1),
            "validity": round(avg_score, 1),
            "consistency": 100.0 if critical_cnt == 0 else 90.0,
            "uniqueness": 100.0 if pending_dups == 0 else max(80.0, 100.0 - pending_dups * 2.0),
            "timeliness": 100.0,
        }

        breakdown = {
            "STUDENT": {"count": student_cnt, "status": "GOVERNED"},
            "DEPARTMENT": {"count": dept_cnt, "status": "GOVERNED"},
            "COMPANY": {"count": comp_cnt, "status": "GOVERNED"},
        }

        return DataQualitySummaryResponse(
            total_governed_records=total_governed,
            records_with_critical_issues=critical_cnt,
            records_with_errors=error_cnt,
            records_with_warnings=warning_cnt,
            open_quality_issues=open_issues_count,
            open_issues_count=open_issues_count,
            resolved_quality_issues=resolved_issues_count,
            pending_duplicate_candidates=pending_dups,
            duplicate_candidates_count=pending_dups,
            average_quality_score=round(avg_score, 1),
            dimension_averages=dimension_averages,
            breakdown_by_master_type=breakdown,
        )

    # -------------------------------------------------------------------------
    # 7. Corrections
    # -------------------------------------------------------------------------

    @classmethod
    async def create_correction(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        dto: MasterDataCorrectionCreate,
        actor_id: UUID | None = None,
        requester_id: UUID | None = None,
    ) -> MasterDataCorrection:
        user_id = requester_id or actor_id
        repo = MasterDataRepository(db)
        corr = MasterDataCorrection(
            tenant_id=tenant_id,
            master_type=dto.master_type.upper(),
            record_id=dto.record_id,
            field_name=dto.field_name,
            proposed_value=dto.proposed_value,
            reason=dto.reason,
            status=CorrectionStatus.PENDING_REVIEW,
            requester_id=user_id,
        )
        created = await repo.create_correction(corr)
        return created

    propose_correction = create_correction

    @classmethod
    async def review_correction(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        correction_id: UUID,
        decision: CorrectionStatus,
        notes: str | None = None,
        reviewer_id: UUID | None = None,
    ) -> MasterDataCorrection:
        repo = MasterDataRepository(db)
        corr = await repo.get_correction(correction_id, tenant_id)
        if not corr:
            raise MasterDataCorrectionNotFoundException(str(correction_id))

        corr.status = decision
        corr.reviewer_id = reviewer_id
        corr.reviewed_at = datetime.now(UTC)
        if decision == CorrectionStatus.REJECTED:
            corr.rejection_reason = notes
        elif decision == CorrectionStatus.APPROVED:
            # Apply update to underlying domain record
            await cls._apply_correction_to_record(
                db,
                tenant_id,
                corr.master_type,
                corr.record_id,
                corr.field_name,
                corr.proposed_value,
            )
            corr.status = CorrectionStatus.APPLIED
            corr.applied_at = datetime.now(UTC)

            # Record lineage
            lineage = MasterDataLineage(
                tenant_id=tenant_id,
                master_type=corr.master_type,
                record_id=corr.record_id,
                source=LineageSource.MANUAL,
                modified_by=reviewer_id,
                modification_source="CORRECTION_WORKFLOW",
                details_json={"field": corr.field_name, "value": corr.proposed_value},
            )
            await repo.create_lineage(lineage)

        # Audit
        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.MASTER_DATA_CORRECTED,
            entity_type="master_data_correction",
            entity_id=corr.id,
            user_id=reviewer_id,
            business_context=(
                f"Correction {correction_id} on {corr.master_type}:{corr.field_name} {decision}."
            ),
        )
        db.add(audit)
        await db.flush()

        return corr

    @classmethod
    async def _apply_correction_to_record(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        master_type: str,
        record_id: UUID,
        field: str,
        value: str,
    ) -> None:
        m_type = master_type.upper()
        if m_type == MasterDataType.STUDENT:
            if hasattr(StudentProfile, field):
                await db.execute(
                    update(StudentProfile)
                    .where(StudentProfile.id == record_id, StudentProfile.tenant_id == tenant_id)
                    .values({field: value})
                )
        elif m_type == MasterDataType.COMPANY:
            if hasattr(Company, field):
                await db.execute(
                    update(Company)
                    .where(Company.id == record_id, Company.tenant_id == tenant_id)
                    .values({field: value})
                )
        elif m_type == MasterDataType.DEPARTMENT:
            if hasattr(Department, field):
                await db.execute(
                    update(Department)
                    .where(Department.id == record_id, Department.tenant_id == tenant_id)
                    .values({field: value})
                )
        await db.flush()

    # -------------------------------------------------------------------------
    # 8. Lineage
    # -------------------------------------------------------------------------

    @classmethod
    async def record_lineage(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        dto: MasterDataLineageCreate | None = None,
        actor_id: UUID | None = None,
        master_type: str | None = None,
        record_id: UUID | None = None,
        source: LineageSource = LineageSource.MANUAL,
        source_record_id: str | None = None,
        imported_at: datetime | None = None,
        last_verified_at: datetime | None = None,
        modified_by: UUID | None = None,
        modification_source: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> MasterDataLineage:
        repo = MasterDataRepository(db)
        if dto is not None:
            master_type = dto.master_type
            record_id = dto.record_id
            source = dto.source
            source_record_id = dto.source_record_id
            imported_at = dto.imported_at
            last_verified_at = dto.last_verified_at
            modification_source = dto.modification_source
            details = dto.details_json

        lineage = MasterDataLineage(
            tenant_id=tenant_id,
            master_type=str(master_type).upper() if master_type else "UNKNOWN",
            record_id=record_id or uuid4(),
            source=source,
            source_record_id=source_record_id,
            imported_at=imported_at or datetime.now(UTC),
            last_verified_at=last_verified_at or datetime.now(UTC),
            modified_by=actor_id or modified_by,
            modification_source=modification_source,
            details_json=details,
        )
        created = await repo.create_lineage(lineage)
        return created

    @classmethod
    async def get_lineage(
        cls, db: AsyncSession, tenant_id: UUID, master_type: str, record_id: UUID
    ) -> list[MasterDataLineage]:
        repo = MasterDataRepository(db)
        return await repo.list_lineage_for_record(tenant_id, master_type.upper(), record_id)

    get_lineage_history = get_lineage
