"""Controlled Master Data Merge Service & Survivorship Engine (Step 24).

Implements transactional, auditable duplicate merges for supported entities:
Student, Company, and Department.
Applies survivorship policies, reassigns downstream domain relationships,
maintains forensic lineage, and supports reversible rollbacks.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventCategory, build_audit_entry
from app.core.exceptions import (
    MasterDataMergeConflictException,
    MasterDataMergeUnsupportedException,
    MasterDataRecordNotFoundException,
    MasterDataRollbackNotAllowedException,
)
from app.models.academics import Subject
from app.models.attendance import AttendanceRecord, StudentLeaveRequest
from app.models.core import Department, Program
from app.models.examination import StudentAssessmentMark
from app.models.finance import Invoice
from app.models.master_data import (
    DuplicateStatus,
    MasterDataMergeOperation,
    MasterDataType,
    SurvivorshipRule,
)
from app.models.people import FacultyProfile, StudentProfile
from app.models.placement import Company, CompanyContact, JobDrive
from app.repositories.master_data_repository import MasterDataRepository


class MergeService:
    """Orchestrates safe duplicate merges, survivorship rules, and relationship reassignment."""

    SUPPORTED_MERGE_TYPES = {
        MasterDataType.STUDENT,
        MasterDataType.COMPANY,
        MasterDataType.DEPARTMENT,
    }

    @classmethod
    async def execute_merge(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        master_type: str,
        survivor_record_id: UUID | None = None,
        merged_record_id: UUID | None = None,
        survivorship_rule: SurvivorshipRule = SurvivorshipRule.KEEP_CANONICAL,
        field_decisions: dict[str, Any] | None = None,
        reason: str = "",
        actor_id: UUID | None = None,
        survivor_id: UUID | None = None,
        merged_id: UUID | None = None,
    ) -> MasterDataMergeOperation:
        """Execute transactional merge of a duplicate record into a canonical survivor."""
        survivor_record_id = survivor_record_id or survivor_id
        merged_record_id = merged_record_id or merged_id
        if not survivor_record_id or not merged_record_id:
            raise MasterDataMergeConflictException(
                "Both survivor and merged record IDs are required."
            )

        m_type = master_type.upper()
        if m_type not in cls.SUPPORTED_MERGE_TYPES:
            raise MasterDataMergeUnsupportedException(m_type)

        if survivor_record_id == merged_record_id:
            raise MasterDataMergeConflictException("Cannot merge a record into itself.")

        repo = MasterDataRepository(db)
        reassigned_counts: dict[str, int] = {}

        if m_type == MasterDataType.STUDENT:
            reassigned_counts = await cls._merge_students(
                db,
                tenant_id,
                survivor_record_id,
                merged_record_id,
                survivorship_rule,
                field_decisions,
            )
        elif m_type == MasterDataType.COMPANY:
            reassigned_counts = await cls._merge_companies(
                db,
                tenant_id,
                survivor_record_id,
                merged_record_id,
                survivorship_rule,
                field_decisions,
            )
        elif m_type == MasterDataType.DEPARTMENT:
            reassigned_counts = await cls._merge_departments(
                db,
                tenant_id,
                survivor_record_id,
                merged_record_id,
                survivorship_rule,
                field_decisions,
            )

        # Update any pending duplicate candidate pair to MERGED
        cand = await repo.get_duplicate_candidate_by_pair(
            tenant_id, m_type, survivor_record_id, merged_record_id
        )
        if cand:
            cand.status = DuplicateStatus.MERGED
            cand.reviewed_by = actor_id
            cand.reviewed_at = datetime.now(UTC)
            cand.review_notes = f"Merged via operation: {reason}"

        # Create forensic merge ledger
        merge_op = MasterDataMergeOperation(
            tenant_id=tenant_id,
            master_type=m_type,
            survivor_record_id=survivor_record_id,
            merged_record_id=merged_record_id,
            actor_id=actor_id,
            reason=reason,
            survivorship_rule=survivorship_rule,
            field_decisions_json=field_decisions,
            reassigned_counts_json=reassigned_counts,
            status="COMPLETED",
            is_reversible=True,
        )
        await repo.create_merge_operation(merge_op)

        # Audit
        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.MASTER_DATA_MERGED,
            entity_type="master_data_merge",
            entity_id=merge_op.id,
            user_id=actor_id,
            business_context=(
                f"Merged {m_type} {merged_record_id} into survivor {survivor_record_id}. "
                f"Reassigned: {reassigned_counts}"
            ),
        )
        db.add(audit)
        await db.flush()

        return merge_op

    @classmethod
    async def _merge_students(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        survivor_id: UUID,
        merged_id: UUID,
        rule: SurvivorshipRule,
        field_decisions: dict[str, Any] | None,
    ) -> dict[str, int]:
        s_res = await db.execute(
            select(StudentProfile).where(
                StudentProfile.id == survivor_id, StudentProfile.tenant_id == tenant_id
            )
        )
        survivor = s_res.scalar_one_or_none()

        m_res = await db.execute(
            select(StudentProfile).where(
                StudentProfile.id == merged_id, StudentProfile.tenant_id == tenant_id
            )
        )
        merged = m_res.scalar_one_or_none()

        if not survivor:
            raise MasterDataRecordNotFoundException(MasterDataType.STUDENT, str(survivor_id))
        if not merged:
            raise MasterDataRecordNotFoundException(MasterDataType.STUDENT, str(merged_id))

        # Apply survivorship
        if rule == SurvivorshipRule.KEEP_NON_EMPTY:
            if not survivor.blood_group and merged.blood_group:
                survivor.blood_group = merged.blood_group
            if not survivor.emergency_contact_phone and merged.emergency_contact_phone:
                survivor.emergency_contact_phone = merged.emergency_contact_phone
            if not survivor.emergency_contact_name and merged.emergency_contact_name:
                survivor.emergency_contact_name = merged.emergency_contact_name
        elif rule == SurvivorshipRule.EXPLICIT_FIELD_SELECTION and field_decisions:
            for field, val in field_decisions.items():
                if hasattr(survivor, field):
                    setattr(survivor, field, val)

        # Reassign relationships
        # 1. Attendance Records
        att_res = await db.execute(
            update(AttendanceRecord)
            .where(AttendanceRecord.student_id == merged.id)
            .values(student_id=survivor.id)
        )
        att_count = int(getattr(att_res, "rowcount", 0) or 0)

        # 2. Leave Requests
        leave_res = await db.execute(
            update(StudentLeaveRequest)
            .where(StudentLeaveRequest.student_id == merged.id)
            .values(student_id=survivor.id)
        )
        leave_count = int(getattr(leave_res, "rowcount", 0) or 0)

        # 3. Assessment Marks
        marks_res = await db.execute(
            update(StudentAssessmentMark)
            .where(StudentAssessmentMark.student_id == merged.id)
            .values(student_id=survivor.id)
        )
        marks_count = int(getattr(marks_res, "rowcount", 0) or 0)

        # 4. Invoices
        inv_res = await db.execute(
            update(Invoice).where(Invoice.student_id == merged.id).values(student_id=survivor.id)
        )
        inv_count = int(getattr(inv_res, "rowcount", 0) or 0)

        # Mark merged student profile as inactive/merged
        merged.status = "MERGED"

        return {
            "attendance_records": att_count,
            "leave_requests": leave_count,
            "assessment_marks": marks_count,
            "invoices": inv_count,
        }

    @classmethod
    async def _merge_companies(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        survivor_id: UUID,
        merged_id: UUID,
        rule: SurvivorshipRule,
        field_decisions: dict[str, Any] | None,
    ) -> dict[str, int]:
        c_surv = await db.execute(
            select(Company).where(Company.id == survivor_id, Company.tenant_id == tenant_id)
        )
        survivor = c_surv.scalar_one_or_none()

        c_merg = await db.execute(
            select(Company).where(Company.id == merged_id, Company.tenant_id == tenant_id)
        )
        merged = c_merg.scalar_one_or_none()

        if not survivor:
            raise MasterDataRecordNotFoundException(MasterDataType.COMPANY, str(survivor_id))
        if not merged:
            raise MasterDataRecordNotFoundException(MasterDataType.COMPANY, str(merged_id))

        if rule == SurvivorshipRule.KEEP_NON_EMPTY:
            if not survivor.website and merged.website:
                survivor.website = merged.website
            if not survivor.description and merged.description:
                survivor.description = merged.description
        elif rule == SurvivorshipRule.EXPLICIT_FIELD_SELECTION and field_decisions:
            for field, val in field_decisions.items():
                if hasattr(survivor, field):
                    setattr(survivor, field, val)

        # Reassign Job Drives
        jd_res = await db.execute(
            update(JobDrive).where(JobDrive.company_id == merged.id).values(company_id=survivor.id)
        )
        jd_count = int(getattr(jd_res, "rowcount", 0) or 0)

        # Reassign Company Contacts
        cc_res = await db.execute(
            update(CompanyContact)
            .where(CompanyContact.company_id == merged.id)
            .values(company_id=survivor.id)
        )
        cc_count = int(getattr(cc_res, "rowcount", 0) or 0)

        merged.status = "MERGED"

        return {
            "job_drives": jd_count,
            "company_contacts": cc_count,
        }

    @classmethod
    async def _merge_departments(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        survivor_id: UUID,
        merged_id: UUID,
        rule: SurvivorshipRule,
        field_decisions: dict[str, Any] | None,
    ) -> dict[str, int]:
        d_surv = await db.execute(
            select(Department).where(
                Department.id == survivor_id, Department.tenant_id == tenant_id
            )
        )
        survivor = d_surv.scalar_one_or_none()

        d_merg = await db.execute(
            select(Department).where(Department.id == merged_id, Department.tenant_id == tenant_id)
        )
        merged = d_merg.scalar_one_or_none()

        if not survivor:
            raise MasterDataRecordNotFoundException(MasterDataType.DEPARTMENT, str(survivor_id))
        if not merged:
            raise MasterDataRecordNotFoundException(MasterDataType.DEPARTMENT, str(merged_id))

        if rule == SurvivorshipRule.EXPLICIT_FIELD_SELECTION and field_decisions:
            for field, val in field_decisions.items():
                if hasattr(survivor, field):
                    setattr(survivor, field, val)

        # Reassign Programs
        prog_res = await db.execute(
            update(Program)
            .where(Program.department_id == merged.id)
            .values(department_id=survivor.id)
        )
        prog_count = int(getattr(prog_res, "rowcount", 0) or 0)

        # Reassign Subjects
        subj_res = await db.execute(
            update(Subject)
            .where(Subject.department_id == merged.id)
            .values(department_id=survivor.id)
        )
        subj_count = int(getattr(subj_res, "rowcount", 0) or 0)

        # Reassign Faculty Members
        fac_res = await db.execute(
            update(FacultyProfile)
            .where(FacultyProfile.department_id == merged.id)
            .values(department_id=survivor.id)
        )
        fac_count = int(getattr(fac_res, "rowcount", 0) or 0)

        merged.is_active = False

        return {
            "programs": prog_count,
            "subjects": subj_count,
            "faculty_members": fac_count,
        }

    @classmethod
    async def rollback_merge(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        operation_id: UUID,
        reason: str = "",
        actor_id: UUID | None = None,
        rollback_reason: str | None = None,
    ) -> MasterDataMergeOperation:
        """Roll back a previous duplicate merge operation where feasible."""
        reason = rollback_reason or reason
        repo = MasterDataRepository(db)
        op = await repo.get_merge_operation(operation_id, tenant_id)
        if not op:
            raise MasterDataRecordNotFoundException(
                "master_data_merge_operation", str(operation_id)
            )

        if op.status == "ROLLED_BACK":
            raise MasterDataRollbackNotAllowedException("Operation is already rolled back.")
        if not op.is_reversible:
            raise MasterDataRollbackNotAllowedException(
                "This merge operation has been marked as irreversible."
            )

        # Restore merged record status
        if op.master_type == MasterDataType.STUDENT:
            await db.execute(
                update(StudentProfile)
                .where(StudentProfile.id == op.merged_record_id)
                .values(status="ACTIVE")
            )
        elif op.master_type == MasterDataType.COMPANY:
            await db.execute(
                update(Company).where(Company.id == op.merged_record_id).values(status="ACTIVE")
            )
        elif op.master_type == MasterDataType.DEPARTMENT:
            await db.execute(
                update(Department)
                .where(Department.id == op.merged_record_id)
                .values(is_active=True)
            )

        op.status = "ROLLED_BACK"
        op.rolled_back_at = datetime.now(UTC)
        op.rolled_back_by = actor_id
        op.rollback_reason = reason

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.MASTER_DATA_MERGE_REVERSED,
            entity_type="master_data_merge",
            entity_id=op.id,
            user_id=actor_id,
            business_context=f"Rolled back merge operation {op.id}: {reason}",
        )
        db.add(audit)
        await db.flush()

        return op
