"""Enterprise Data Import, Bulk Migration, Reconciliation & Interoperability Domain Service (Step 40).

Central service managing:
- Governed import templates for Students, Faculty, Departments, Programs, Courses
- 14-state import job lifecycle with immutable transition histories
- Secure CSV and XLSX intake via DocumentStorage and DataImportParser
- Column mapping configuration, type transformations, and system field protection
- Multi-tier validation pipeline (file, record, and domain integrity)
- Pre-execution change previews and administrative approval gating
- Bounded batch execution engine with progress checkpoints and idempotency
- Discrepancy conflict detection and resolution workflow
- Post-import data reconciliation with discrepancy accounting
- Downloadable formula-escaped CSV error reports
"""

import io
import logging
import re
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import AuditEventCategory, build_audit_entry
from app.core.exceptions import (
    BadRequestException,
    ImportApprovalRequiredException,
    ImportJobNotFoundException,
    ImportTemplateNotFoundException,
    ImportValidationFailedException,
    InvalidImportStateException,
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
)
from app.core.storage import get_document_storage
from app.models.academics import Subject
from app.models.core import Batch, Department, Program, Regulation
from app.models.data_import import (
    ConflictResolutionAction,
    ImportConflictRecord,
    ImportConflictType,
    ImportExecutionPolicy,
    ImportJob,
    ImportJobStateHistory,
    ImportJobStatus,
    ImportMappingDefinition,
    ImportRecordResult,
    ImportRecordStatus,
    ImportTemplate,
    ReconciliationStatus,
)
from app.models.people import FacultyProfile, StudentProfile, User
from app.schemas.data_import import (
    ImportApprovalRequest,
    ImportConflictResolutionRequest,
    ImportExecutionRequest,
    ImportJobCreateRequest,
    ImportMappingUpdateRequest,
)
from app.services.data_import_parser import DataImportParser

logger = logging.getLogger("campusos.services.data_import")

# Protected system fields that must NEVER be mapped or modified via generic import
PROTECTED_SYSTEM_FIELDS = {
    "id",
    "tenant_id",
    "created_at",
    "updated_at",
    "deleted_at",
    "password_hash",
    "is_superuser",
    "failed_login_attempts",
    "locked_until",
}


def _parse_date_safe(val: Any) -> date | None:
    """Parse string or datetime to date safely."""
    if not val:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    val_str = str(val).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(val_str, fmt).date()
        except ValueError:
            continue
    return None


class DataImportService:
    """Central domain service orchestrating the institutional data migration pipeline."""

    # -------------------------------------------------------------------------
    # 1. Template Seeding & Retrieval
    # -------------------------------------------------------------------------

    @classmethod
    async def seed_default_templates(cls, db: AsyncSession) -> list[ImportTemplate]:
        """Seed standard CampusOS enterprise import templates if they do not exist."""
        templates_def = [
            {
                "code": "STUDENTS_BULK_IMPORT",
                "name": "Students & Profiles Bulk Import",
                "target_domain": "STUDENTS",
                "target_entity": "StudentProfile",
                "description": "Comprehensive student admissions, institutional roll numbers, biodata, and program enrollments.",
                "required_fields": [
                    "email",
                    "first_name",
                    "last_name",
                    "admission_number",
                    "date_of_birth",
                    "gender",
                    "admission_date",
                    "expected_graduation_date",
                    "program_code",
                    "batch_name",
                ],
                "optional_fields": [
                    "registration_number",
                    "roll_number",
                    "phone_number",
                    "blood_group",
                    "status",
                    "emergency_contact_name",
                    "emergency_contact_phone",
                ],
                "field_definitions": {
                    "email": {"type": "email", "description": "Student institutional email"},
                    "first_name": {"type": "string", "maxLength": 100},
                    "last_name": {"type": "string", "maxLength": 100},
                    "admission_number": {"type": "string", "maxLength": 64},
                    "date_of_birth": {"type": "date", "format": "YYYY-MM-DD"},
                    "gender": {"type": "enum", "allowed": ["MALE", "FEMALE", "OTHER"]},
                    "admission_date": {"type": "date", "format": "YYYY-MM-DD"},
                    "expected_graduation_date": {"type": "date", "format": "YYYY-MM-DD"},
                    "program_code": {"type": "foreign_key", "target": "Program.code"},
                    "batch_name": {"type": "foreign_key", "target": "Batch.name"},
                },
                "supported_matching_keys": ["admission_number", "registration_number", "roll_number", "email"],
                "supported_policies": ["CREATE_NEW", "UPDATE_EXISTING", "UPSERT", "SKIP_CONFLICTS"],
                "requires_approval_threshold": 50,
            },
            {
                "code": "FACULTY_BULK_IMPORT",
                "name": "Faculty & Instructors Bulk Import",
                "target_domain": "FACULTY",
                "target_entity": "FacultyProfile",
                "description": "Academic faculty records, employee identification codes, designations, and departmental affiliations.",
                "required_fields": [
                    "email",
                    "first_name",
                    "last_name",
                    "employee_code",
                    "department_code",
                    "designation",
                    "highest_qualification",
                    "joining_date",
                ],
                "optional_fields": [
                    "phone_number",
                    "specialization",
                    "is_hod",
                    "employment_status",
                ],
                "field_definitions": {
                    "email": {"type": "email"},
                    "employee_code": {"type": "string", "maxLength": 64},
                    "department_code": {"type": "foreign_key", "target": "Department.code"},
                    "designation": {"type": "string", "maxLength": 128},
                    "highest_qualification": {"type": "string", "maxLength": 128},
                    "joining_date": {"type": "date", "format": "YYYY-MM-DD"},
                },
                "supported_matching_keys": ["employee_code", "email"],
                "supported_policies": ["CREATE_NEW", "UPDATE_EXISTING", "UPSERT", "SKIP_CONFLICTS"],
                "requires_approval_threshold": 25,
            },
            {
                "code": "DEPARTMENTS_IMPORT",
                "name": "Academic & Administrative Departments Import",
                "target_domain": "CORE",
                "target_entity": "Department",
                "description": "Organizational departments, departmental codes, and faculty units.",
                "required_fields": ["code", "name"],
                "optional_fields": ["department_type"],
                "field_definitions": {
                    "code": {"type": "string", "maxLength": 32},
                    "name": {"type": "string", "maxLength": 255},
                    "department_type": {"type": "enum", "allowed": ["ACADEMIC", "ADMINISTRATIVE"]},
                },
                "supported_matching_keys": ["code"],
                "supported_policies": ["CREATE_NEW", "UPDATE_EXISTING", "UPSERT"],
                "requires_approval_threshold": 100,
            },
            {
                "code": "PROGRAMS_IMPORT",
                "name": "Academic Degree Programs Import",
                "target_domain": "CORE",
                "target_entity": "Program",
                "description": "Degree programs, duration in years, semesters, and degree levels.",
                "required_fields": ["code", "name", "department_code", "degree_level"],
                "optional_fields": ["duration_years", "total_semesters", "required_credits"],
                "field_definitions": {
                    "code": {"type": "string", "maxLength": 32},
                    "name": {"type": "string", "maxLength": 255},
                    "department_code": {"type": "foreign_key", "target": "Department.code"},
                    "degree_level": {"type": "enum", "allowed": ["UG", "PG", "DOCTORAL"]},
                },
                "supported_matching_keys": ["code"],
                "supported_policies": ["CREATE_NEW", "UPDATE_EXISTING", "UPSERT"],
                "requires_approval_threshold": 50,
            },
            {
                "code": "COURSES_IMPORT",
                "name": "Course & Subject Catalog Import",
                "target_domain": "ACADEMICS",
                "target_entity": "Subject",
                "description": "Master academic course catalog, credits, theory/practical breakdown, and subject types.",
                "required_fields": ["code", "name", "department_code"],
                "optional_fields": ["credits", "lecture_hours", "tutorial_hours", "practical_hours", "subject_type", "description"],
                "field_definitions": {
                    "code": {"type": "string", "maxLength": 32},
                    "name": {"type": "string", "maxLength": 255},
                    "department_code": {"type": "foreign_key", "target": "Department.code"},
                    "credits": {"type": "numeric"},
                },
                "supported_matching_keys": ["code"],
                "supported_policies": ["CREATE_NEW", "UPDATE_EXISTING", "UPSERT"],
                "requires_approval_threshold": 100,
            },
        ]

        seeded = []
        for d in templates_def:
            stmt = select(ImportTemplate).where(ImportTemplate.code == d["code"])
            res = await db.execute(stmt)
            tpl = res.scalar_one_or_none()
            if not tpl:
                tpl = ImportTemplate(
                    code=d["code"],
                    name=d["name"],
                    target_domain=d["target_domain"],
                    target_entity=d["target_entity"],
                    description=d["description"],
                    version=1,
                    required_fields=d["required_fields"],
                    optional_fields=d["optional_fields"],
                    field_definitions=d["field_definitions"],
                    supported_matching_keys=d["supported_matching_keys"],
                    supported_policies=d["supported_policies"],
                    requires_approval_threshold=d["requires_approval_threshold"],
                    is_system_template=True,
                    is_active=True,
                )
                db.add(tpl)
                seeded.append(tpl)
            else:
                seeded.append(tpl)

        await db.flush()
        return seeded

    @classmethod
    async def list_templates(
        cls,
        db: AsyncSession,
        domain: str | None = None,
    ) -> list[ImportTemplate]:
        """List active import templates with optional domain filtering."""
        stmt = select(ImportTemplate).where(ImportTemplate.is_active.is_(True))
        if domain:
            stmt = stmt.where(ImportTemplate.target_domain == domain.upper())
        stmt = stmt.order_by(ImportTemplate.name.asc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def get_template(
        cls,
        db: AsyncSession,
        code_or_id: str | UUID,
    ) -> ImportTemplate:
        """Fetch template by code or UUID."""
        if isinstance(code_or_id, UUID) or (isinstance(code_or_id, str) and len(code_or_id) == 36 and "-" in code_or_id):
            uid = UUID(str(code_or_id))
            stmt = select(ImportTemplate).where(ImportTemplate.id == uid)
        else:
            stmt = select(ImportTemplate).where(ImportTemplate.code == str(code_or_id))
        res = await db.execute(stmt)
        tpl = res.scalar_one_or_none()
        if not tpl:
            raise ImportTemplateNotFoundException(code_or_id)
        return tpl

    @classmethod
    async def generate_blank_template_csv(
        cls,
        db: AsyncSession,
        template_code: str,
    ) -> str:
        """Generate a downloadable blank CSV with standard headers."""
        tpl = await cls.get_template(db, template_code)
        headers = list(tpl.required_fields) + list(tpl.optional_fields)
        output = io.StringIO()
        output.write(",".join(headers) + "\n")
        return output.getvalue()

    # -------------------------------------------------------------------------
    # 2. Import Job Lifecycle Management
    # -------------------------------------------------------------------------

    @classmethod
    async def create_job(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        actor_id: UUID,
        dto: ImportJobCreateRequest,
    ) -> ImportJob:
        """Create a new import job in DRAFT state."""
        tpl = await cls.get_template(db, dto.template_code)

        matching_key = dto.matching_key or (tpl.supported_matching_keys[0] if tpl.supported_matching_keys else None)
        if matching_key and matching_key not in tpl.supported_matching_keys:
            raise BadRequestException(
                f"Matching key '{matching_key}' is not supported for template '{tpl.code}'. "
                f"Supported keys: {', '.join(tpl.supported_matching_keys)}."
            )

        job = ImportJob(
            tenant_id=tenant_id,
            template_id=tpl.id,
            template_code=tpl.code,
            name=dto.name,
            target_domain=tpl.target_domain,
            target_entity=tpl.target_entity,
            status=ImportJobStatus.DRAFT.value,
            execution_policy=dto.execution_policy,
            matching_key=matching_key,
            created_by_id=actor_id,
        )
        db.add(job)
        await db.flush()

        # Add initial lifecycle state history
        history = ImportJobStateHistory(
            tenant_id=tenant_id,
            job_id=job.id,
            from_status="NONE",
            to_status=ImportJobStatus.DRAFT.value,
            actor_id=actor_id,
            reason="Import job initialized",
        )
        db.add(history)

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.IMPORT_JOB_CREATED,
                entity_type="ImportJob",
                entity_id=job.id,
                user_id=actor_id,
                business_context=f"Created import job '{job.name}' ({tpl.code}) in DRAFT status",
            )
        )
        await db.flush()
        await db.refresh(job)
        return job

    @classmethod
    async def get_job(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        job_id: UUID,
    ) -> ImportJob:
        """Fetch import job with tenant isolation."""
        stmt = (
            select(ImportJob)
            .options(selectinload(ImportJob.mapping))
            .where(ImportJob.id == job_id, ImportJob.tenant_id == tenant_id)
        )
        res = await db.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            raise ImportJobNotFoundException(job_id)
        return job

    @classmethod
    async def list_jobs(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ImportJob]:
        """List tenant import jobs with pagination and optional status filter."""
        stmt = select(ImportJob).where(ImportJob.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(ImportJob.status == status.upper())
        stmt = stmt.order_by(desc(ImportJob.created_at)).offset(offset).limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def _transition_state(
        cls,
        db: AsyncSession,
        job: ImportJob,
        new_status: ImportJobStatus,
        actor_id: UUID | None = None,
        reason: str | None = None,
    ) -> None:
        """Transition import job state with history tracking and audit logging."""
        old_status = job.status
        job.status = new_status.value

        history = ImportJobStateHistory(
            tenant_id=job.tenant_id,
            job_id=job.id,
            from_status=old_status,
            to_status=new_status.value,
            actor_id=actor_id,
            reason=reason,
        )
        db.add(history)
        await db.flush()

    # -------------------------------------------------------------------------
    # 3. File Intake & Storage
    # -------------------------------------------------------------------------

    @classmethod
    async def upload_source_file(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        job_id: UUID,
        actor_id: UUID,
        filename: str,
        file_bytes: bytes,
    ) -> ImportJob:
        """Store untrusted source file, extract metadata, and parse headers."""
        job = await cls.get_job(db, tenant_id, job_id)

        # Allow upload only in DRAFT, FILE_UPLOADED, or MAPPING_PENDING
        if job.status not in (
            ImportJobStatus.DRAFT.value,
            ImportJobStatus.FILE_UPLOADED.value,
            ImportJobStatus.MAPPING_PENDING.value,
            ImportJobStatus.VALIDATION_FAILED.value,
        ):
            raise InvalidImportStateException(
                job.status,
                "upload_source_file",
                [ImportJobStatus.DRAFT.value, ImportJobStatus.FILE_UPLOADED.value, ImportJobStatus.MAPPING_PENDING.value],
            )

        # Validate file extension
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in ("csv", "xlsx", "xls"):
            raise ValidationException(f"Unsupported file extension '{ext}'. Only CSV and XLSX are allowed.")

        file_format = "XLSX" if ext in ("xlsx", "xls") else "CSV"
        mime_type = "text/csv" if file_format == "CSV" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        # Validate file size & parse headers/records
        headers, records = DataImportParser.parse_file(file_bytes, file_format)

        # Compute SHA-256 checksum
        import hashlib
        checksum = hashlib.sha256(file_bytes).hexdigest()

        # Store file in tenant-isolated document storage
        storage = get_document_storage()
        storage_key = f"tenants/{tenant_id}/imports/{job_id}/{filename}"
        await storage.upload(file_bytes, storage_key, mime_type)

        job.source_filename = filename
        job.source_file_storage_key = storage_key
        job.source_file_checksum = checksum
        job.source_file_size_bytes = len(file_bytes)
        job.source_file_format = file_format
        job.source_record_count = len(records)

        # Auto-generate mapping suggestion if no mapping exists
        tpl = await cls.get_template(db, job.template_code)
        target_fields = set(tpl.required_fields + tpl.optional_fields)

        suggested_mappings = {}
        for h in headers:
            normalized_h = re.sub(r"[^a-zA-Z0-9_]", "_", h.lower().strip())
            # Check direct match
            for tf in target_fields:
                if normalized_h == tf.lower() or normalized_h.replace("_", "") == tf.lower().replace("_", ""):
                    suggested_mappings[h] = tf
                    break

        # Persist or update mapping definition
        stmt = select(ImportMappingDefinition).where(ImportMappingDefinition.job_id == job.id)
        m_res = await db.execute(stmt)
        mapping = m_res.scalar_one_or_none()
        if not mapping:
            mapping = ImportMappingDefinition(
                tenant_id=tenant_id,
                job_id=job.id,
                template_code=job.template_code,
                column_mappings=suggested_mappings,
                transformations={},
                default_values={},
                is_validated=False,
            )
            db.add(mapping)
        else:
            mapping.column_mappings = suggested_mappings
            mapping.is_validated = False

        await cls._transition_state(
            db,
            job,
            ImportJobStatus.MAPPING_PENDING,
            actor_id=actor_id,
            reason=f"Uploaded source file '{filename}' with {len(records)} records",
        )

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.IMPORT_FILE_UPLOADED,
                entity_type="ImportJob",
                entity_id=job.id,
                user_id=actor_id,
                business_context=f"Uploaded file '{filename}' ({len(records)} rows, {len(file_bytes)} bytes) for import job '{job.name}'",
            )
        )
        await db.flush()
        await db.refresh(job)
        return job

    # -------------------------------------------------------------------------
    # 4. Column Mapping & Transformations
    # -------------------------------------------------------------------------

    @classmethod
    async def update_mapping(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        job_id: UUID,
        actor_id: UUID,
        dto: ImportMappingUpdateRequest,
    ) -> ImportMappingDefinition:
        """Configure source column to target field mapping with system field protection."""
        job = await cls.get_job(db, tenant_id, job_id)
        tpl = await cls.get_template(db, job.template_code)

        # Invalidate approval if job was already approved
        if job.requires_approval and job.approved_at is not None:
            job.approved_at = None
            job.approved_by_id = None
            job.approval_notes = "Approval invalidated due to column mapping modification."

        allowed_target_fields = set(tpl.required_fields + tpl.optional_fields)

        # Validate mapped targets
        for src_col, target_field in dto.column_mappings.items():
            if not target_field:
                continue
            # Security: reject system fields
            if target_field.lower() in PROTECTED_SYSTEM_FIELDS:
                raise PermissionDeniedException(
                    f"Mapping to protected system field '{target_field}' is strictly prohibited."
                )
            if target_field not in allowed_target_fields:
                raise ValidationException(
                    f"Unknown target field '{target_field}' for template '{tpl.code}'. "
                    f"Allowed fields: {', '.join(sorted(allowed_target_fields))}."
                )

        stmt = select(ImportMappingDefinition).where(ImportMappingDefinition.job_id == job.id)
        m_res = await db.execute(stmt)
        mapping = m_res.scalar_one_or_none()
        if not mapping:
            mapping = ImportMappingDefinition(
                tenant_id=tenant_id,
                job_id=job.id,
                template_code=job.template_code,
                column_mappings=dto.column_mappings,
                transformations=dto.transformations,
                default_values=dto.default_values,
                is_validated=False,
            )
            db.add(mapping)
        else:
            mapping.column_mappings = dto.column_mappings
            mapping.transformations = dto.transformations
            mapping.default_values = dto.default_values
            mapping.version += 1
            mapping.is_validated = False

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.IMPORT_MAPPING_CONFIGURED,
                entity_type="ImportMappingDefinition",
                entity_id=mapping.id,
                user_id=actor_id,
                business_context=f"Configured column mapping v{mapping.version} for import job '{job.name}'",
            )
        )
        await db.flush()
        await db.refresh(mapping)
        return mapping

    # -------------------------------------------------------------------------
    # 5. Validation Pipeline
    # -------------------------------------------------------------------------

    @classmethod
    async def run_validation(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        job_id: UUID,
        actor_id: UUID,
    ) -> dict[str, Any]:
        """Execute multi-tier validation: File, Record, and Domain checks."""
        job = await cls.get_job(db, tenant_id, job_id)
        tpl = await cls.get_template(db, job.template_code)

        if not job.source_file_storage_key:
            raise BadRequestException("Cannot run validation without an uploaded source file.")

        stmt = select(ImportMappingDefinition).where(ImportMappingDefinition.job_id == job.id)
        m_res = await db.execute(stmt)
        mapping = m_res.scalar_one_or_none()
        if not mapping or not mapping.column_mappings:
            raise BadRequestException("Column mapping has not been configured.")

        await cls._transition_state(db, job, ImportJobStatus.VALIDATION_RUNNING, actor_id, "Validation started")

        # Load file bytes from storage
        storage = get_document_storage()
        file_bytes = await storage.download(job.source_file_storage_key)
        headers, raw_records = DataImportParser.parse_file(file_bytes, job.source_file_format or "CSV")

        # Verify all required template fields are mapped or have default values
        mapped_targets = {v: k for k, v in mapping.column_mappings.items() if v}
        missing_required = []
        for req in tpl.required_fields:
            if req not in mapped_targets and req not in mapping.default_values:
                missing_required.append(req)

        if missing_required:
            await cls._transition_state(
                db, job, ImportJobStatus.VALIDATION_FAILED, actor_id, f"Missing required mappings: {', '.join(missing_required)}"
            )
            raise ImportValidationFailedException(
                f"Validation failed: required template fields are not mapped: {', '.join(missing_required)}.",
                error_count=len(missing_required),
                errors=[{"field": f, "code": "REQUIRED_FIELD_UNMAPPED", "message": f"Field '{f}' is required."} for f in missing_required],
            )

        # Clear any prior validation records
        del_records_stmt = select(ImportRecordResult).where(ImportRecordResult.job_id == job.id)
        r_res = await db.execute(del_records_stmt)
        for r in r_res.scalars().all():
            await db.delete(r)

        del_conflicts_stmt = select(ImportConflictRecord).where(ImportConflictRecord.job_id == job.id)
        c_res = await db.execute(del_conflicts_stmt)
        for c in c_res.scalars().all():
            await db.delete(c)

        await db.flush()

        # Cache reference data for domain FK validation
        cached_departments = {
            d.code.upper(): d.id
            for d in (await db.execute(select(Department).where(Department.tenant_id == tenant_id))).scalars().all()
        }
        cached_programs = {
            p.code.upper(): p.id
            for p in (await db.execute(select(Program).where(Program.tenant_id == tenant_id))).scalars().all()
        }
        cached_batches = {
            b.name.upper(): b.id
            for b in (await db.execute(select(Batch).where(Batch.tenant_id == tenant_id))).scalars().all()
        }

        # Cache existing student matching keys
        existing_admission_numbers = set(
            (
                await db.execute(
                    select(StudentProfile.admission_number).where(StudentProfile.tenant_id == tenant_id)
                )
            ).scalars().all()
        )
        existing_faculty_codes = set(
            (
                await db.execute(
                    select(FacultyProfile.employee_code).where(FacultyProfile.tenant_id == tenant_id)
                )
            ).scalars().all()
        )
        existing_subject_codes = set(
            (
                await db.execute(
                    select(Subject.code).where(Subject.tenant_id == tenant_id)
                )
            ).scalars().all()
        )

        matching_key_attr = job.matching_key or "admission_number"
        seen_file_keys: set[str] = set()

        valid_count = 0
        error_count = 0
        warning_count = 0
        errors_by_field: dict[str, int] = {}
        sample_errors: list[dict[str, Any]] = []

        for rec in raw_records:
            row_num = rec["row_number"]
            row_raw = rec["data"]

            # Transform raw row based on column mapping
            transformed: dict[str, Any] = {}
            row_errors: list[dict[str, Any]] = []
            row_warnings: list[dict[str, Any]] = []

            for src_h, val in row_raw.items():
                target_f = mapping.column_mappings.get(src_h)
                if target_f:
                    # Apply basic string sanitization
                    cleaned_val = str(val).strip() if val is not None else ""
                    # Apply configured transformations
                    tf_rule = mapping.transformations.get(target_f)
                    if tf_rule == "UPPER":
                        cleaned_val = cleaned_val.upper()
                    elif tf_rule == "LOWER":
                        cleaned_val = cleaned_val.lower()
                    elif tf_rule == "TRIM":
                        cleaned_val = cleaned_val.strip()

                    transformed[target_f] = cleaned_val

            # Apply defaults for empty mapped fields
            for df_key, df_val in mapping.default_values.items():
                if not transformed.get(df_key):
                    transformed[df_key] = df_val

            # 1. Required field checks
            for req in tpl.required_fields:
                if not transformed.get(req):
                    err = {"field": req, "code": "REQUIRED_FIELD_EMPTY", "message": f"Field '{req}' cannot be empty."}
                    row_errors.append(err)
                    errors_by_field[req] = errors_by_field.get(req, 0) + 1

            # 2. Type & Format validation
            # Email validation
            if "email" in transformed and transformed["email"]:
                email_val = transformed["email"]
                if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email_val):
                    err = {"field": "email", "code": "INVALID_EMAIL_FORMAT", "message": f"'{email_val}' is not a valid email address."}
                    row_errors.append(err)
                    errors_by_field["email"] = errors_by_field.get("email", 0) + 1

            # Date validations
            for date_field in ("date_of_birth", "admission_date", "expected_graduation_date", "joining_date"):
                if date_field in transformed and transformed[date_field]:
                    parsed_d = _parse_date_safe(transformed[date_field])
                    if not parsed_d:
                        err = {"field": date_field, "code": "INVALID_DATE_FORMAT", "message": f"Date '{transformed[date_field]}' must be in YYYY-MM-DD format."}
                        row_errors.append(err)
                        errors_by_field[date_field] = errors_by_field.get(date_field, 0) + 1

            # Enum validations
            if "gender" in transformed and transformed["gender"]:
                if transformed["gender"].upper() not in ("MALE", "FEMALE", "OTHER"):
                    err = {"field": "gender", "code": "INVALID_ENUM_VALUE", "message": "Gender must be MALE, FEMALE, or OTHER."}
                    row_errors.append(err)
                    errors_by_field["gender"] = errors_by_field.get("gender", 0) + 1

            # 3. Foreign Key Reference Integrity
            if "program_code" in transformed and transformed["program_code"]:
                p_code = transformed["program_code"].upper()
                if p_code not in cached_programs:
                    err = {"field": "program_code", "code": "FOREIGN_KEY_NOT_FOUND", "message": f"Program code '{p_code}' does not exist in institution."}
                    row_errors.append(err)
                    errors_by_field["program_code"] = errors_by_field.get("program_code", 0) + 1

            if "department_code" in transformed and transformed["department_code"]:
                d_code = transformed["department_code"].upper()
                if d_code not in cached_departments:
                    err = {"field": "department_code", "code": "FOREIGN_KEY_NOT_FOUND", "message": f"Department code '{d_code}' does not exist in institution."}
                    row_errors.append(err)
                    errors_by_field["department_code"] = errors_by_field.get("department_code", 0) + 1

            # 4. Duplicate checks
            matching_val = transformed.get(matching_key_attr, "")
            if matching_val:
                # Intra-file duplicate check
                if matching_val in seen_file_keys:
                    err = {"field": matching_key_attr, "code": "DUPLICATE_IN_FILE", "message": f"Duplicate matching key '{matching_val}' appears multiple times in source file."}
                    row_errors.append(err)
                    errors_by_field[matching_key_attr] = errors_by_field.get(matching_key_attr, 0) + 1
                else:
                    seen_file_keys.add(matching_val)

                # Database collision check
                is_db_duplicate = False
                if tpl.code == "STUDENTS_BULK_IMPORT" and matching_val in existing_admission_numbers:
                    is_db_duplicate = True
                elif tpl.code == "FACULTY_BULK_IMPORT" and matching_val in existing_faculty_codes:
                    is_db_duplicate = True
                elif tpl.code in ("COURSES_IMPORT", "DEPARTMENTS_IMPORT", "PROGRAMS_IMPORT") and matching_val in existing_subject_codes:
                    is_db_duplicate = True

                if is_db_duplicate:
                    if job.execution_policy == ImportExecutionPolicy.CREATE_NEW.value:
                        err = {
                            "field": matching_key_attr,
                            "code": "EXISTING_RECORD_CONFLICT",
                            "message": f"Record with '{matching_key_attr}={matching_val}' already exists in tenant database.",
                        }
                        row_errors.append(err)
                        errors_by_field[matching_key_attr] = errors_by_field.get(matching_key_attr, 0) + 1

                    # Log conflict record
                    conflict = ImportConflictRecord(
                        tenant_id=tenant_id,
                        job_id=job.id,
                        row_number=row_num,
                        matching_key=matching_key_attr,
                        matching_value=matching_val,
                        conflict_type=ImportConflictType.EXISTING_RECORD_MATCH.value,
                        source_payload=transformed,
                        existing_payload={"status": "EXISTING_IN_DB"},
                        discrepancies_json={"matching_key": matching_val},
                        resolution=ConflictResolutionAction.PENDING.value,
                    )
                    db.add(conflict)

            # Determine row status
            if row_errors:
                row_status = ImportRecordStatus.INVALID.value
                error_count += 1
                if len(sample_errors) < 20:
                    sample_errors.append({"row_number": row_num, "errors": row_errors})
            else:
                row_status = ImportRecordStatus.VALID.value
                valid_count += 1

            record_res = ImportRecordResult(
                tenant_id=tenant_id,
                job_id=job.id,
                row_number=row_num,
                matching_key_value=matching_val,
                status=row_status,
                source_data_json=row_raw,
                transformed_data_json=transformed,
                errors_json=row_errors,
                warnings_json=row_warnings,
            )
            db.add(record_res)

        mapping.is_validated = True
        job.valid_record_count = valid_count
        job.error_record_count = error_count
        job.warning_record_count = warning_count

        # Check approval requirement
        requires_approval = (
            valid_count >= tpl.requires_approval_threshold
            or tpl.target_domain in ("FACULTY", "FINANCE")
        )
        job.requires_approval = requires_approval

        if error_count > 0:
            next_status = ImportJobStatus.VALIDATION_FAILED
        elif requires_approval and not job.approved_at:
            next_status = ImportJobStatus.AWAITING_APPROVAL
        else:
            next_status = ImportJobStatus.READY_TO_EXECUTE

        await cls._transition_state(
            db,
            job,
            next_status,
            actor_id=actor_id,
            reason=f"Validation completed: {valid_count} valid, {error_count} errors, {warning_count} warnings",
        )

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.IMPORT_VALIDATION_COMPLETED if error_count == 0 else AuditEventCategory.IMPORT_VALIDATION_FAILED,
                entity_type="ImportJob",
                entity_id=job.id,
                user_id=actor_id,
                business_context=f"Validation completed for '{job.name}': {valid_count} valid, {error_count} errors (status: {next_status.value})",
            )
        )
        await db.flush()

        return {
            "job_id": job.id,
            "status": next_status.value,
            "total_records": len(raw_records),
            "valid_records": valid_count,
            "error_records": error_count,
            "warning_records": warning_count,
            "errors_by_field": errors_by_field,
            "sample_errors": sample_errors,
            "can_execute": next_status == ImportJobStatus.READY_TO_EXECUTE,
            "requires_approval": requires_approval,
        }

    # -------------------------------------------------------------------------
    # 6. Preview & Approval Management
    # -------------------------------------------------------------------------

    @classmethod
    async def get_preview(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        job_id: UUID,
    ) -> dict[str, Any]:
        """Generate high-impact preview of records to create, update, skip, or fail."""
        job = await cls.get_job(db, tenant_id, job_id)

        # Fetch sample transformed records
        stmt = (
            select(ImportRecordResult)
            .where(ImportRecordResult.job_id == job.id)
            .order_by(ImportRecordResult.row_number.asc())
            .limit(10)
        )
        res = await db.execute(stmt)
        sample_results = list(res.scalars().all())

        # Count conflicts
        c_stmt = select(func.count(ImportConflictRecord.id)).where(ImportConflictRecord.job_id == job.id)
        conflict_res = await db.execute(c_stmt)
        conflict_count = conflict_res.scalar() or 0

        policy = job.execution_policy
        if policy == ImportExecutionPolicy.CREATE_NEW.value:
            records_to_create = job.valid_record_count
            records_to_update = 0
            records_to_skip = 0
        elif policy == ImportExecutionPolicy.UPDATE_EXISTING.value:
            records_to_create = 0
            records_to_update = job.valid_record_count
            records_to_skip = 0
        elif policy == ImportExecutionPolicy.UPSERT.value:
            records_to_create = max(0, job.valid_record_count - conflict_count)
            records_to_update = conflict_count
            records_to_skip = 0
        elif policy == ImportExecutionPolicy.SKIP_CONFLICTS.value:
            records_to_create = max(0, job.valid_record_count - conflict_count)
            records_to_update = 0
            records_to_skip = conflict_count
        else:
            records_to_create = 0
            records_to_update = 0
            records_to_skip = job.valid_record_count

        high_impact = []
        if job.valid_record_count > 100:
            high_impact.append(f"Large volume import: {job.valid_record_count} records to be committed.")
        if conflict_count > 0:
            high_impact.append(f"{conflict_count} potential database duplicate conflicts identified.")
        if job.requires_approval:
            high_impact.append("Requires formal administrative approval prior to execution.")

        return {
            "job_id": job.id,
            "execution_policy": job.execution_policy,
            "matching_key": job.matching_key,
            "total_source_records": job.source_record_count,
            "records_to_create": records_to_create,
            "records_to_update": records_to_update,
            "records_to_skip": records_to_skip,
            "records_with_warnings": job.warning_record_count,
            "records_blocking_execution": job.error_record_count,
            "potential_duplicate_matches": conflict_count,
            "high_impact_summary": high_impact,
            "sample_transformed_records": [r.transformed_data_json for r in sample_results],
        }

    @classmethod
    async def approve_job(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        job_id: UUID,
        actor_id: UUID,
        dto: ImportApprovalRequest,
    ) -> ImportJob:
        """Formally approve or reject an import job awaiting approval."""
        job = await cls.get_job(db, tenant_id, job_id)

        if job.status != ImportJobStatus.AWAITING_APPROVAL.value:
            raise InvalidImportStateException(
                job.status, "approve_job", [ImportJobStatus.AWAITING_APPROVAL.value]
            )

        if dto.approved:
            job.approved_by_id = actor_id
            job.approved_at = datetime.now(UTC)
            job.approval_notes = dto.notes

            await cls._transition_state(
                db,
                job,
                ImportJobStatus.READY_TO_EXECUTE,
                actor_id=actor_id,
                reason=f"Approved by administrator: {dto.notes or 'No notes provided'}",
            )
            audit_action = AuditEventCategory.IMPORT_APPROVED
        else:
            job.rejection_reason = dto.rejection_reason or "Rejected by administrator."
            await cls._transition_state(
                db,
                job,
                ImportJobStatus.CANCELLED,
                actor_id=actor_id,
                reason=f"Rejected: {job.rejection_reason}",
            )
            audit_action = AuditEventCategory.IMPORT_REJECTED

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=audit_action,
                entity_type="ImportJob",
                entity_id=job.id,
                user_id=actor_id,
                business_context=f"Administrative approval decision for '{job.name}': approved={dto.approved}",
            )
        )
        await db.flush()
        await db.refresh(job)
        return job

    # -------------------------------------------------------------------------
    # 7. Reliable Bounded Batch Execution Engine
    # -------------------------------------------------------------------------

    @classmethod
    async def execute_import(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        job_id: UUID,
        actor_id: UUID,
        request: ImportExecutionRequest | None = None,
    ) -> ImportJob:
        """Execute validated import records in bounded batches using domain entities."""
        job = await cls.get_job(db, tenant_id, job_id)

        # Allow execution only when READY_TO_EXECUTE or PARTIALLY_COMPLETED (for retry/resume)
        if job.status not in (
            ImportJobStatus.READY_TO_EXECUTE.value,
            ImportJobStatus.PARTIALLY_COMPLETED.value,
        ):
            if job.status == ImportJobStatus.AWAITING_APPROVAL.value:
                raise ImportApprovalRequiredException()
            raise InvalidImportStateException(
                job.status,
                "execute_import",
                [ImportJobStatus.READY_TO_EXECUTE.value, ImportJobStatus.PARTIALLY_COMPLETED.value],
            )

        batch_size = request.batch_size if request else 50
        stop_on_first_error = request.stop_on_first_error if request else False

        job.started_at = datetime.now(UTC)
        await cls._transition_state(db, job, ImportJobStatus.EXECUTION_RUNNING, actor_id, "Execution started")

        # Pre-load reference maps
        dept_map = {
            d.code.upper(): d.id
            for d in (await db.execute(select(Department).where(Department.tenant_id == tenant_id))).scalars().all()
        }
        prog_map = {
            p.code.upper(): p.id
            for p in (await db.execute(select(Program).where(Program.tenant_id == tenant_id))).scalars().all()
        }

        # Query all records marked VALID starting from last_processed_row
        stmt = (
            select(ImportRecordResult)
            .where(
                ImportRecordResult.job_id == job.id,
                ImportRecordResult.status == ImportRecordStatus.VALID.value,
                ImportRecordResult.row_number > job.last_processed_row,
            )
            .order_by(ImportRecordResult.row_number.asc())
        )
        res = await db.execute(stmt)
        pending_records = list(res.scalars().all())

        created_in_run = 0
        updated_in_run = 0
        skipped_in_run = 0
        failed_in_run = 0

        # Execute in bounded batches
        for i in range(0, len(pending_records), batch_size):
            batch = pending_records[i : i + batch_size]
            for rec in batch:
                data = rec.transformed_data_json
                try:
                    target_id = None
                    if job.template_code == "STUDENTS_BULK_IMPORT":
                        target_id = await cls._execute_student_row(db, tenant_id, data, prog_map)
                        created_in_run += 1
                        rec.status = ImportRecordStatus.CREATED.value
                    elif job.template_code == "FACULTY_BULK_IMPORT":
                        target_id = await cls._execute_faculty_row(db, tenant_id, data, dept_map)
                        created_in_run += 1
                        rec.status = ImportRecordStatus.CREATED.value
                    elif job.template_code == "DEPARTMENTS_IMPORT":
                        target_id = await cls._execute_department_row(db, tenant_id, data)
                        created_in_run += 1
                        rec.status = ImportRecordStatus.CREATED.value
                    elif job.template_code == "PROGRAMS_IMPORT":
                        target_id = await cls._execute_program_row(db, tenant_id, data, dept_map)
                        created_in_run += 1
                        rec.status = ImportRecordStatus.CREATED.value
                    elif job.template_code == "COURSES_IMPORT":
                        target_id = await cls._execute_course_row(db, tenant_id, data, dept_map)
                        created_in_run += 1
                        rec.status = ImportRecordStatus.CREATED.value
                    else:
                        raise BadRequestException(f"Unsupported template code '{job.template_code}'.")

                    rec.target_entity_id = target_id
                    rec.executed_at = datetime.now(UTC)

                except Exception as exc:
                    logger.error(f"Row {rec.row_number} failed during import execution: {str(exc)}")
                    rec.status = ImportRecordStatus.FAILED.value
                    rec.errors_json = [{"field": "execution", "code": "EXECUTION_EXCEPTION", "message": str(exc)}]
                    failed_in_run += 1
                    if stop_on_first_error:
                        job.last_processed_row = rec.row_number
                        break

                job.last_processed_row = rec.row_number

            # Commit batch checkpoint
            await db.flush()

        job.created_record_count += created_in_run
        job.updated_record_count += updated_in_run
        job.skipped_record_count += skipped_in_run
        job.failed_record_count += failed_in_run
        job.processed_record_count = (
            job.created_record_count + job.updated_record_count + job.skipped_record_count + job.failed_record_count
        )
        job.completed_at = datetime.now(UTC)

        # Determine terminal state
        if job.failed_record_count == 0 and job.processed_record_count >= job.valid_record_count:
            final_status = ImportJobStatus.COMPLETED
        elif job.created_record_count > 0 or job.updated_record_count > 0:
            final_status = ImportJobStatus.PARTIALLY_COMPLETED
        else:
            final_status = ImportJobStatus.FAILED

        await cls._transition_state(
            db,
            job,
            final_status,
            actor_id=actor_id,
            reason=f"Execution finished: {job.created_record_count} created, {job.updated_record_count} updated, {job.failed_record_count} failed",
        )

        # Automatic post-import reconciliation
        await cls.run_reconciliation(db, tenant_id, job.id)

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.IMPORT_EXECUTION_COMPLETED if final_status == ImportJobStatus.COMPLETED else AuditEventCategory.IMPORT_EXECUTION_FAILED,
                entity_type="ImportJob",
                entity_id=job.id,
                user_id=actor_id,
                business_context=f"Executed import job '{job.name}': {job.created_record_count} created, {job.failed_record_count} failed",
            )
        )
        await db.flush()
        await db.refresh(job)
        return job

    # -------------------------------------------------------------------------
    # 7a. Individual Entity Row Executors
    # -------------------------------------------------------------------------

    @classmethod
    async def _execute_student_row(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: dict[str, Any],
        prog_map: dict[str, UUID],
    ) -> UUID:
        """Create or update User and StudentProfile."""
        email = data["email"].lower().strip()
        u_stmt = select(User).where(User.email == email)
        u_res = await db.execute(u_stmt)
        user = u_res.scalar_one_or_none()
        if not user:
            user = User(
                email=email,
                first_name=data["first_name"],
                last_name=data["last_name"],
                primary_tenant_id=tenant_id,
                password_hash="IMPORT_PENDING_ACTIVATION",
                phone_number=data.get("phone_number"),
                is_active=True,
                status="ACTIVE",
            )
            db.add(user)
            await db.flush()

        prog_id = prog_map.get(data["program_code"].upper())
        if not prog_id:
            # Re-fetch or create fallback program
            p_stmt = select(Program).where(Program.tenant_id == tenant_id, Program.code == data["program_code"])
            p_res = await db.execute(p_stmt)
            prog = p_res.scalar_one_or_none()
            if not prog:
                raise ValidationException(f"Program '{data['program_code']}' not found.")
            prog_id = prog.id

        # Batch lookup or create
        b_name = data["batch_name"]
        b_stmt = select(Batch).where(Batch.tenant_id == tenant_id, Batch.name == b_name)
        b_res = await db.execute(b_stmt)
        batch = b_res.scalar_one_or_none()
        if not batch:
            reg_stmt = select(Regulation).where(Regulation.tenant_id == tenant_id)
            reg_res = await db.execute(reg_stmt)
            reg = reg_res.scalars().first()
            if not reg:
                reg = Regulation(
                    tenant_id=tenant_id,
                    code="REG_DEF",
                    title="Default Curriculum Framework",
                    effective_year=2026,
                )
                db.add(reg)
                await db.flush()

            batch = Batch(
                tenant_id=tenant_id,
                program_id=prog_id,
                regulation_id=reg.id,
                name=b_name,
                admission_year=2026,
                graduation_year=2030,
            )
            db.add(batch)
            await db.flush()

        dob = _parse_date_safe(data["date_of_birth"]) or date(2005, 1, 1)
        adm_date = _parse_date_safe(data["admission_date"]) or date.today()
        grad_date = _parse_date_safe(data["expected_graduation_date"]) or date(2030, 5, 31)

        student = StudentProfile(
            tenant_id=tenant_id,
            user_id=user.id,
            admission_number=data["admission_number"],
            registration_number=data.get("registration_number"),
            roll_number=data.get("roll_number"),
            date_of_birth=dob,
            gender=data["gender"].upper(),
            blood_group=data.get("blood_group"),
            status=data.get("status", "ADMITTED").upper(),
            admission_date=adm_date,
            expected_graduation_date=grad_date,
            program_id=prog_id,
            batch_id=batch.id,
            emergency_contact_name=data.get("emergency_contact_name"),
            emergency_contact_phone=data.get("emergency_contact_phone"),
        )
        db.add(student)
        await db.flush()
        return student.id

    @classmethod
    async def _execute_faculty_row(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: dict[str, Any],
        dept_map: dict[str, UUID],
    ) -> UUID:
        """Create User and FacultyProfile."""
        email = data["email"].lower().strip()
        u_stmt = select(User).where(User.email == email)
        u_res = await db.execute(u_stmt)
        user = u_res.scalar_one_or_none()
        if not user:
            user = User(
                email=email,
                first_name=data["first_name"],
                last_name=data["last_name"],
                primary_tenant_id=tenant_id,
                password_hash="IMPORT_PENDING_ACTIVATION",
                phone_number=data.get("phone_number"),
                is_active=True,
                status="ACTIVE",
            )
            db.add(user)
            await db.flush()

        dept_id = dept_map.get(data["department_code"].upper())
        if not dept_id:
            d_stmt = select(Department).where(Department.tenant_id == tenant_id, Department.code == data["department_code"])
            d_res = await db.execute(d_stmt)
            dept = d_res.scalar_one_or_none()
            if not dept:
                raise ValidationException(f"Department '{data['department_code']}' not found.")
            dept_id = dept.id

        joining_d = _parse_date_safe(data["joining_date"]) or date.today()

        faculty = FacultyProfile(
            tenant_id=tenant_id,
            user_id=user.id,
            employee_code=data["employee_code"],
            department_id=dept_id,
            designation=data["designation"],
            highest_qualification=data["highest_qualification"],
            specialization=data.get("specialization"),
            joining_date=joining_d,
            is_hod=bool(data.get("is_hod", False)),
            employment_status=data.get("employment_status", "ACTIVE").upper(),
        )
        db.add(faculty)
        await db.flush()
        return faculty.id

    @classmethod
    async def _execute_department_row(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: dict[str, Any],
    ) -> UUID:
        """Create Department."""
        dept = Department(
            tenant_id=tenant_id,
            code=data["code"].upper(),
            name=data["name"],
            department_type=data.get("department_type", "ACADEMIC").upper(),
            is_active=True,
        )
        db.add(dept)
        await db.flush()
        return dept.id

    @classmethod
    async def _execute_program_row(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: dict[str, Any],
        dept_map: dict[str, UUID],
    ) -> UUID:
        """Create Program."""
        dept_id = dept_map.get(data["department_code"].upper())
        if not dept_id:
            raise ValidationException(f"Department code '{data['department_code']}' does not exist.")

        prog = Program(
            tenant_id=tenant_id,
            department_id=dept_id,
            code=data["code"].upper(),
            name=data["name"],
            degree_level=data["degree_level"].upper(),
            duration_years=Decimal(str(data.get("duration_years", 4.0))),
            total_semesters=int(data.get("total_semesters", 8)),
            required_credits=int(data.get("required_credits", 160)),
            is_active=True,
        )
        db.add(prog)
        await db.flush()
        return prog.id

    @classmethod
    async def _execute_course_row(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: dict[str, Any],
        dept_map: dict[str, UUID],
    ) -> UUID:
        """Create Subject/Course."""
        dept_id = dept_map.get(data["department_code"].upper())
        if not dept_id:
            raise ValidationException(f"Department code '{data['department_code']}' does not exist.")

        subject = Subject(
            tenant_id=tenant_id,
            department_id=dept_id,
            code=data["code"].upper(),
            name=data["name"],
            credits=Decimal(str(data.get("credits", 3.0))),
            lecture_hours=int(data.get("lecture_hours", 3)),
            tutorial_hours=int(data.get("tutorial_hours", 0)),
            practical_hours=int(data.get("practical_hours", 0)),
            subject_type=data.get("subject_type", "THEORY").upper(),
            description=data.get("description"),
            is_active=True,
        )
        db.add(subject)
        await db.flush()
        return subject.id

    # -------------------------------------------------------------------------
    # 8. Post-Import Data Reconciliation
    # -------------------------------------------------------------------------

    @classmethod
    async def run_reconciliation(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        job_id: UUID,
    ) -> dict[str, Any]:
        """Verify actual committed database operations against planned outcomes."""
        job = await cls.get_job(db, tenant_id, job_id)

        # Count records by status from ImportRecordResult
        stmt = (
            select(ImportRecordResult.status, func.count(ImportRecordResult.id))
            .where(ImportRecordResult.job_id == job.id)
            .group_by(ImportRecordResult.status)
        )
        res = await db.execute(stmt)
        status_counts = dict(res.all())

        created = status_counts.get(ImportRecordStatus.CREATED.value, 0)
        updated = status_counts.get(ImportRecordStatus.UPDATED.value, 0)
        skipped = status_counts.get(ImportRecordStatus.SKIPPED.value, 0)
        failed = status_counts.get(ImportRecordStatus.FAILED.value, 0)
        invalid = status_counts.get(ImportRecordStatus.INVALID.value, 0)

        # Expected source total vs accounted records
        accounted = created + updated + skipped + failed + invalid
        diff = max(0, job.source_record_count - accounted)

        is_balanced = (diff == 0) and (failed == 0)
        recon_status = (
            ReconciliationStatus.MATCHED.value
            if is_balanced
            else ReconciliationStatus.DISCREPANCY_DETECTED.value
        )

        job.reconciliation_status = recon_status
        job.reconciliation_diff_count = diff
        job.reconciliation_summary = {
            "source_records": job.source_record_count,
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "failed": failed,
            "invalid": invalid,
            "unaccounted_difference": diff,
            "is_balanced": is_balanced,
            "reconciled_at": datetime.now(UTC).isoformat(),
        }

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.IMPORT_RECONCILIATION_COMPLETED,
                entity_type="ImportJob",
                entity_id=job.id,
                business_context=f"Reconciliation completed for '{job.name}': status={recon_status}, diff={diff}",
            )
        )
        await db.flush()

        return {
            "job_id": job.id,
            "reconciliation_status": recon_status,
            "source_record_count": job.source_record_count,
            "valid_record_count": job.valid_record_count,
            "created_record_count": created,
            "updated_record_count": updated,
            "skipped_record_count": skipped,
            "failed_record_count": failed,
            "unaccounted_difference": diff,
            "is_balanced": is_balanced,
            "discrepancy_details": job.reconciliation_summary,
        }

    # -------------------------------------------------------------------------
    # 9. Conflict Resolution & Error Reports
    # -------------------------------------------------------------------------

    @classmethod
    async def list_conflicts(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        job_id: UUID,
    ) -> list[ImportConflictRecord]:
        """List detected conflicts for an import job."""
        stmt = (
            select(ImportConflictRecord)
            .where(ImportConflictRecord.job_id == job_id, ImportConflictRecord.tenant_id == tenant_id)
            .order_by(ImportConflictRecord.row_number.asc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def resolve_conflict(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        conflict_id: UUID,
        actor_id: UUID,
        dto: ImportConflictResolutionRequest,
    ) -> ImportConflictRecord:
        """Resolve a specific import conflict."""
        stmt = select(ImportConflictRecord).where(
            ImportConflictRecord.id == conflict_id,
            ImportConflictRecord.tenant_id == tenant_id,
        )
        res = await db.execute(stmt)
        conflict = res.scalar_one_or_none()
        if not conflict:
            raise NotFoundException("ImportConflictRecord", conflict_id)

        conflict.resolution = dto.resolution.upper()
        conflict.resolved_by_id = actor_id
        conflict.resolved_at = datetime.now(UTC)

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.IMPORT_CONFLICT_RESOLVED,
                entity_type="ImportConflictRecord",
                entity_id=conflict.id,
                user_id=actor_id,
                business_context=f"Resolved conflict for row {conflict.row_number} ({conflict.matching_key}={conflict.matching_value}) as {dto.resolution}",
            )
        )
        await db.flush()
        await db.refresh(conflict)
        return conflict

    @classmethod
    async def cancel_job(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        job_id: UUID,
        actor_id: UUID,
        reason: str | None = None,
    ) -> ImportJob:
        """Cancel an eligible in-flight or pending import job."""
        job = await cls.get_job(db, tenant_id, job_id)

        if job.status in (ImportJobStatus.COMPLETED.value, ImportJobStatus.CANCELLED.value):
            raise InvalidImportStateException(
                job.status, "cancel_job", ["DRAFT", "VALIDATION_RUNNING", "AWAITING_APPROVAL", "READY_TO_EXECUTE"]
            )

        await cls._transition_state(
            db,
            job,
            ImportJobStatus.CANCELLED,
            actor_id=actor_id,
            reason=reason or "Job cancelled by administrator",
        )

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.IMPORT_JOB_CANCELLED,
                entity_type="ImportJob",
                entity_id=job.id,
                user_id=actor_id,
                business_context=f"Cancelled import job '{job.name}' ({reason or 'Admin cancellation'})",
            )
        )
        await db.flush()
        await db.refresh(job)
        return job

    @classmethod
    async def generate_error_report(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        job_id: UUID,
    ) -> str:
        """Generate a formula-injection escaped CSV error report for a job."""
        job = await cls.get_job(db, tenant_id, job_id)

        stmt = (
            select(ImportRecordResult)
            .where(
                ImportRecordResult.job_id == job.id,
                ImportRecordResult.status.in_([ImportRecordStatus.INVALID.value, ImportRecordStatus.FAILED.value]),
            )
            .order_by(ImportRecordResult.row_number.asc())
        )
        res = await db.execute(stmt)
        failed_records = list(res.scalars().all())

        report_data = []
        for r in failed_records:
            report_data.append({
                "row_number": r.row_number,
                "matching_key": r.matching_key_value or "",
                "status": r.status,
                "errors": r.errors_json or [],
            })

        csv_content = DataImportParser.generate_error_report_csv(report_data)
        return csv_content
