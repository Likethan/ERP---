"""Persistence Repository Layer for Enterprise Master Data Management & Data Quality (Step 24)."""

from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.master_data import (
    DataQualityIssue,
    DataQualityResult,
    DataQualityRule,
    DuplicateCandidate,
    DuplicateStatus,
    MasterDataCorrection,
    MasterDataDefinition,
    MasterDataLineage,
    MasterDataMergeOperation,
    QualityIssueStatus,
    ReferenceDataDefinition,
    ReferenceDataValue,
)


class MasterDataRepository:
    """Repository handling persistence for Master Data, Quality, Duplicates, and Reference Data."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # -------------------------------------------------------------------------
    # 1. Master Data Definitions
    # -------------------------------------------------------------------------

    async def get_definition_by_key(self, key: str) -> MasterDataDefinition | None:
        stmt = select(MasterDataDefinition).where(MasterDataDefinition.key == key.upper())
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_definitions(self, is_active: bool | None = None) -> list[MasterDataDefinition]:
        stmt = select(MasterDataDefinition)
        if is_active is not None:
            stmt = stmt.where(MasterDataDefinition.is_active == is_active)
        stmt = stmt.order_by(MasterDataDefinition.key)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create_definition(self, definition: MasterDataDefinition) -> MasterDataDefinition:
        self.db.add(definition)
        await self.db.flush()
        return definition

    async def update_definition(self, definition: MasterDataDefinition) -> MasterDataDefinition:
        await self.db.flush()
        return definition

    # -------------------------------------------------------------------------
    # 2. Reference Data Definitions & Values
    # -------------------------------------------------------------------------

    async def get_ref_definition(self, category: str) -> ReferenceDataDefinition | None:
        stmt = select(ReferenceDataDefinition).where(
            ReferenceDataDefinition.category == category.upper()
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_ref_definitions(
        self, is_active: bool | None = None
    ) -> list[ReferenceDataDefinition]:
        stmt = select(ReferenceDataDefinition)
        if is_active is not None:
            stmt = stmt.where(ReferenceDataDefinition.is_active == is_active)
        stmt = stmt.order_by(ReferenceDataDefinition.category)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create_ref_definition(
        self, ref_def: ReferenceDataDefinition
    ) -> ReferenceDataDefinition:
        self.db.add(ref_def)
        await self.db.flush()
        return ref_def

    async def get_ref_value_by_id(
        self, value_id: UUID, tenant_id: UUID
    ) -> ReferenceDataValue | None:
        stmt = select(ReferenceDataValue).where(
            ReferenceDataValue.id == value_id,
            ReferenceDataValue.tenant_id == tenant_id,
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_reference_value_by_id(
        self, id_or_tenant: UUID, id_or_tenant_2: UUID
    ) -> ReferenceDataValue | None:
        stmt = select(ReferenceDataValue).where(
            (
                (ReferenceDataValue.id == id_or_tenant)
                & (ReferenceDataValue.tenant_id == id_or_tenant_2)
            )
            | (
                (ReferenceDataValue.id == id_or_tenant_2)
                & (ReferenceDataValue.tenant_id == id_or_tenant)
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_ref_value(
        self, tenant_id: UUID, category: str, code: str
    ) -> ReferenceDataValue | None:
        stmt = select(ReferenceDataValue).where(
            ReferenceDataValue.tenant_id == tenant_id,
            ReferenceDataValue.category == category.upper(),
            ReferenceDataValue.code == code.upper(),
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_ref_values(
        self,
        tenant_id: UUID,
        category: str | None = None,
        is_active: bool | None = None,
    ) -> list[ReferenceDataValue]:
        stmt = select(ReferenceDataValue).where(ReferenceDataValue.tenant_id == tenant_id)
        if category:
            stmt = stmt.where(ReferenceDataValue.category == category.upper())
        if is_active is not None:
            stmt = stmt.where(ReferenceDataValue.is_active == is_active)
        stmt = stmt.order_by(ReferenceDataValue.category, ReferenceDataValue.display_order)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create_ref_value(self, ref_val: ReferenceDataValue) -> ReferenceDataValue:
        self.db.add(ref_val)
        await self.db.flush()
        return ref_val

    async def delete_ref_value(self, value_id: UUID, tenant_id: UUID) -> bool:
        stmt = delete(ReferenceDataValue).where(
            ReferenceDataValue.id == value_id,
            ReferenceDataValue.tenant_id == tenant_id,
        )
        res = await self.db.execute(stmt)
        rowcount = int(getattr(res, "rowcount", 0) or 0)
        return rowcount > 0

    # -------------------------------------------------------------------------
    # 3. Data Quality Rules
    # -------------------------------------------------------------------------

    async def get_rule_by_id(self, rule_id: UUID, tenant_id: UUID) -> DataQualityRule | None:
        stmt = select(DataQualityRule).where(
            DataQualityRule.id == rule_id,
            DataQualityRule.tenant_id == tenant_id,
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_rule_by_key(self, tenant_id: UUID, rule_key: str) -> DataQualityRule | None:
        stmt = select(DataQualityRule).where(
            DataQualityRule.tenant_id == tenant_id,
            DataQualityRule.rule_key == rule_key,
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_rules(
        self,
        tenant_id: UUID,
        master_type: str | None = None,
        is_active: bool | None = None,
    ) -> list[DataQualityRule]:
        stmt = select(DataQualityRule).where(DataQualityRule.tenant_id == tenant_id)
        if master_type:
            stmt = stmt.where(DataQualityRule.master_type == master_type.upper())
        if is_active is not None:
            stmt = stmt.where(DataQualityRule.is_active == is_active)
        stmt = stmt.order_by(DataQualityRule.master_type, DataQualityRule.rule_key)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create_rule(self, rule: DataQualityRule) -> DataQualityRule:
        self.db.add(rule)
        await self.db.flush()
        return rule

    create_quality_rule = create_rule

    # -------------------------------------------------------------------------
    # 4. Data Quality Results & Issues
    # -------------------------------------------------------------------------

    async def create_quality_result(self, result: DataQualityResult) -> DataQualityResult:
        self.db.add(result)
        await self.db.flush()
        return result

    async def get_latest_quality_result(
        self, tenant_id: UUID, master_type: str, record_id: UUID
    ) -> DataQualityResult | None:
        stmt = (
            select(DataQualityResult)
            .where(
                DataQualityResult.tenant_id == tenant_id,
                DataQualityResult.master_type == master_type.upper(),
                DataQualityResult.record_id == record_id,
            )
            .order_by(DataQualityResult.evaluated_at.desc())
            .limit(1)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_quality_results(
        self, tenant_id: UUID, master_type: str | None = None, limit: int = 100
    ) -> list[DataQualityResult]:
        stmt = select(DataQualityResult).where(DataQualityResult.tenant_id == tenant_id)
        if master_type:
            stmt = stmt.where(DataQualityResult.master_type == master_type.upper())
        stmt = stmt.order_by(DataQualityResult.evaluated_at.desc()).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create_quality_issue(self, issue: DataQualityIssue) -> DataQualityIssue:
        self.db.add(issue)
        await self.db.flush()
        return issue

    async def get_quality_issue(self, issue_id: UUID, tenant_id: UUID) -> DataQualityIssue | None:
        stmt = select(DataQualityIssue).where(
            DataQualityIssue.id == issue_id,
            DataQualityIssue.tenant_id == tenant_id,
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_quality_issues(
        self,
        tenant_id: UUID,
        master_type: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[DataQualityIssue], int]:
        stmt = select(DataQualityIssue).where(DataQualityIssue.tenant_id == tenant_id)
        count_stmt = (
            select(func.count())
            .select_from(DataQualityIssue)
            .where(DataQualityIssue.tenant_id == tenant_id)
        )

        if master_type:
            stmt = stmt.where(DataQualityIssue.master_type == master_type.upper())
            count_stmt = count_stmt.where(DataQualityIssue.master_type == master_type.upper())
        if status:
            stmt = stmt.where(DataQualityIssue.status == status)
            count_stmt = count_stmt.where(DataQualityIssue.status == status)
        if severity:
            stmt = stmt.where(DataQualityIssue.severity == severity)
            count_stmt = count_stmt.where(DataQualityIssue.severity == severity)

        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar() or 0

        stmt = stmt.order_by(DataQualityIssue.detected_at.desc()).offset(offset).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all()), total

    async def count_open_issues_by_severity(
        self, tenant_id: UUID, master_type: str | None = None
    ) -> dict[str, int]:
        stmt = select(DataQualityIssue.severity, func.count()).where(
            DataQualityIssue.tenant_id == tenant_id,
            DataQualityIssue.status.in_([QualityIssueStatus.OPEN, QualityIssueStatus.IN_PROGRESS]),
        )
        if master_type:
            stmt = stmt.where(DataQualityIssue.master_type == master_type.upper())
        stmt = stmt.group_by(DataQualityIssue.severity)
        res = await self.db.execute(stmt)
        return {row[0]: row[1] for row in res.all()}

    # -------------------------------------------------------------------------
    # 5. Duplicate Candidates
    # -------------------------------------------------------------------------

    async def create_duplicate_candidate(self, candidate: DuplicateCandidate) -> DuplicateCandidate:
        self.db.add(candidate)
        await self.db.flush()
        return candidate

    async def get_duplicate_candidate(
        self, candidate_id: UUID, tenant_id: UUID
    ) -> DuplicateCandidate | None:
        stmt = select(DuplicateCandidate).where(
            DuplicateCandidate.id == candidate_id,
            DuplicateCandidate.tenant_id == tenant_id,
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_duplicate_candidate_by_pair(
        self,
        tenant_id: UUID,
        master_type: str,
        record_a_id: UUID,
        record_b_id: UUID,
    ) -> DuplicateCandidate | None:
        stmt = select(DuplicateCandidate).where(
            DuplicateCandidate.tenant_id == tenant_id,
            DuplicateCandidate.master_type == master_type.upper(),
            or_(
                (DuplicateCandidate.record_a_id == record_a_id)
                & (DuplicateCandidate.record_b_id == record_b_id),
                (DuplicateCandidate.record_a_id == record_b_id)
                & (DuplicateCandidate.record_b_id == record_a_id),
            ),
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_duplicate_candidates(
        self,
        tenant_id: UUID,
        master_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[DuplicateCandidate], int]:
        stmt = select(DuplicateCandidate).where(DuplicateCandidate.tenant_id == tenant_id)
        count_stmt = (
            select(func.count())
            .select_from(DuplicateCandidate)
            .where(DuplicateCandidate.tenant_id == tenant_id)
        )

        if master_type:
            stmt = stmt.where(DuplicateCandidate.master_type == master_type.upper())
            count_stmt = count_stmt.where(DuplicateCandidate.master_type == master_type.upper())
        if status:
            stmt = stmt.where(DuplicateCandidate.status == status)
            count_stmt = count_stmt.where(DuplicateCandidate.status == status)

        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar() or 0

        stmt = stmt.order_by(DuplicateCandidate.match_score.desc()).offset(offset).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all()), total

    async def count_pending_duplicates(
        self, tenant_id: UUID, master_type: str | None = None
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(DuplicateCandidate)
            .where(
                DuplicateCandidate.tenant_id == tenant_id,
                DuplicateCandidate.status == DuplicateStatus.PENDING,
            )
        )
        if master_type:
            stmt = stmt.where(DuplicateCandidate.master_type == master_type.upper())
        res = await self.db.execute(stmt)
        return res.scalar() or 0

    # -------------------------------------------------------------------------
    # 6. Master Data Merge Operations
    # -------------------------------------------------------------------------

    async def create_merge_operation(
        self, op: MasterDataMergeOperation
    ) -> MasterDataMergeOperation:
        self.db.add(op)
        await self.db.flush()
        return op

    async def get_merge_operation(
        self, op_id: UUID, tenant_id: UUID
    ) -> MasterDataMergeOperation | None:
        stmt = select(MasterDataMergeOperation).where(
            MasterDataMergeOperation.id == op_id,
            MasterDataMergeOperation.tenant_id == tenant_id,
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_merge_operations(
        self, tenant_id: UUID, master_type: str | None = None
    ) -> list[MasterDataMergeOperation]:
        stmt = select(MasterDataMergeOperation).where(
            MasterDataMergeOperation.tenant_id == tenant_id
        )
        if master_type:
            stmt = stmt.where(MasterDataMergeOperation.master_type == master_type.upper())
        stmt = stmt.order_by(MasterDataMergeOperation.created_at.desc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    # -------------------------------------------------------------------------
    # 7. Lineage
    # -------------------------------------------------------------------------

    async def create_lineage(self, lineage: MasterDataLineage) -> MasterDataLineage:
        self.db.add(lineage)
        await self.db.flush()
        return lineage

    async def list_lineage_for_record(
        self, tenant_id: UUID, master_type: str, record_id: UUID
    ) -> list[MasterDataLineage]:
        stmt = (
            select(MasterDataLineage)
            .where(
                MasterDataLineage.tenant_id == tenant_id,
                MasterDataLineage.master_type == master_type.upper(),
                MasterDataLineage.record_id == record_id,
            )
            .order_by(MasterDataLineage.created_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    # -------------------------------------------------------------------------
    # 8. Corrections
    # -------------------------------------------------------------------------

    async def create_correction(self, corr: MasterDataCorrection) -> MasterDataCorrection:
        self.db.add(corr)
        await self.db.flush()
        return corr

    async def get_correction(self, corr_id: UUID, tenant_id: UUID) -> MasterDataCorrection | None:
        stmt = select(MasterDataCorrection).where(
            MasterDataCorrection.id == corr_id,
            MasterDataCorrection.tenant_id == tenant_id,
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_corrections(
        self,
        tenant_id: UUID,
        master_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[MasterDataCorrection], int]:
        stmt = select(MasterDataCorrection).where(MasterDataCorrection.tenant_id == tenant_id)
        count_stmt = (
            select(func.count())
            .select_from(MasterDataCorrection)
            .where(MasterDataCorrection.tenant_id == tenant_id)
        )

        if master_type:
            stmt = stmt.where(MasterDataCorrection.master_type == master_type.upper())
            count_stmt = count_stmt.where(MasterDataCorrection.master_type == master_type.upper())
        if status:
            stmt = stmt.where(MasterDataCorrection.status == status)
            count_stmt = count_stmt.where(MasterDataCorrection.status == status)

        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar() or 0

        stmt = stmt.order_by(MasterDataCorrection.created_at.desc()).offset(offset).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all()), total
