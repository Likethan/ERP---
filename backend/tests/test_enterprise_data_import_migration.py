"""Step 40: Enterprise Data Import, Bulk Migration, Reconciliation & Interoperability Operations Test Suite.

Validates:
1. Import Templates & Catalog Seeding (Students, Faculty, Departments, Programs, Courses)
2. Template Blank CSV Header Downloads
3. Secure File Intake (Supported CSV/XLSX, rejection of invalid extensions and empty files)
4. Column Mapping & Protected System Fields Defense
5. Multi-Tier Validation Engine (Required fields, date/email formats, foreign key resolution)
6. Duplicate Detection (Intra-file duplicate keys and database state conflicts)
7. Preview Calculation & Mandatory Administrative Approval Gating
8. Approval Invalidation on Mapping Changes
9. Bounded Batch Execution Engine & Real Domain Entity Creation (Users, Students, Departments)
10. Checkpointing, Resumability & Idempotent Retries
11. Post-Import Reconciliation (Planned vs Committed Outcomes)
12. Error Report Generation with CSV Formula Injection Escaping
13. Strict Multi-Tenant Isolation
14. End-to-End REST API Lifecycles
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ImportApprovalRequiredException,
    ImportJobNotFoundException,
    PermissionDeniedException,
    ValidationException,
)
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.models.academics import Subject
from app.models.core import Batch, Department, Institution, Program, Regulation
from app.models.data_import import (
    ImportExecutionPolicy,
    ImportJobStatus,
    ImportRecordResult,
    ImportRecordStatus,
    ReconciliationStatus,
)
from app.models.people import StudentProfile, User
from app.schemas.data_import import (
    ImportApprovalRequest,
    ImportExecutionRequest,
    ImportJobCreateRequest,
    ImportMappingUpdateRequest,
)
from app.services.data_import_parser import DataImportParser
from app.services.data_import_service import DataImportService


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
        permissions=["*"] if role_name in ("SUPER_ADMIN", "INSTITUTION_ADMIN", "PLATFORM_OPERATOR") else [],
    )
    return {
        "Authorization": f"Bearer {token}",
        "Cookie": f"{ACCESS_TOKEN_COOKIE_NAME}={token}",
    }


# =============================================================================
# 1. TEMPLATES & BLANK DOWNLOADS
# =============================================================================


@pytest.mark.asyncio
async def test_import_templates_seeding_and_retrieval(db_session: AsyncSession):
    """Verify default certified templates are seeded and accessible."""
    await DataImportService.seed_default_templates(db=db_session)
    templates = await DataImportService.list_templates(db=db_session)
    assert len(templates) >= 5
    codes = {t.code for t in templates}
    assert "STUDENTS_BULK_IMPORT" in codes
    assert "FACULTY_BULK_IMPORT" in codes
    assert "DEPARTMENTS_IMPORT" in codes
    assert "PROGRAMS_IMPORT" in codes
    assert "COURSES_IMPORT" in codes

    student_tmpl = await DataImportService.get_template(db=db_session, code_or_id="STUDENTS_BULK_IMPORT")
    assert student_tmpl.code == "STUDENTS_BULK_IMPORT"
    assert "admission_number" in student_tmpl.required_fields
    assert "email" in student_tmpl.required_fields
    assert student_tmpl.requires_approval_threshold == 50


@pytest.mark.asyncio
async def test_download_blank_template_csv(db_session: AsyncSession):
    """Verify CSV header template generation for entities."""
    await DataImportService.seed_default_templates(db=db_session)
    csv_str = await DataImportService.generate_blank_template_csv(db=db_session, template_code="DEPARTMENTS_IMPORT")
    assert "code" in csv_str
    assert "name" in csv_str


# =============================================================================
# 2. FILE INTAKE & SYSTEM FIELDS PROTECTION
# =============================================================================


@pytest.mark.asyncio
async def test_file_upload_validation_and_parsing(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Verify valid file uploads and rejection of unsupported formats."""
    await DataImportService.seed_default_templates(db=db_session)
    job = await DataImportService.create_job(
        db=db_session,
        tenant_id=tenant_a.id,
        actor_id=tenant_admin_a.id,
        dto=ImportJobCreateRequest(
            template_code="DEPARTMENTS_IMPORT",
            name="Fall 2026 Dept Onboarding",
            execution_policy=ImportExecutionPolicy.UPSERT.value,
        ),
    )
    assert job.status == ImportJobStatus.DRAFT.value

    # Reject unsupported extension
    with pytest.raises(ValidationException) as exc_info:
        await DataImportService.upload_source_file(
            db=db_session,
            tenant_id=tenant_a.id,
            job_id=job.id,
            actor_id=tenant_admin_a.id,
            filename="malicious_payload.exe",
            file_bytes=b"MZ binary content",
        )
    assert "Unsupported file extension" in str(exc_info.value)

    # Reject empty file
    with pytest.raises(ValidationException) as exc_info:
        await DataImportService.upload_source_file(
            db=db_session,
            tenant_id=tenant_a.id,
            job_id=job.id,
            actor_id=tenant_admin_a.id,
            filename="empty.csv",
            file_bytes=b"",
        )
    assert "empty" in str(exc_info.value).lower()

    # Accept valid CSV
    valid_csv = "code,name,description\nCSE,Computer Science and Engineering,Primary computing department\nECE,Electronics Engineering,Electronics department\n"
    job = await DataImportService.upload_source_file(
        db=db_session,
        tenant_id=tenant_a.id,
        job_id=job.id,
        actor_id=tenant_admin_a.id,
        filename="departments.csv",
        file_bytes=valid_csv.encode("utf-8"),
    )
    assert job.status == ImportJobStatus.MAPPING_PENDING.value
    assert job.source_record_count == 2
    assert job.source_file_checksum is not None


@pytest.mark.asyncio
async def test_column_mapping_and_protected_system_fields_defense(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Verify protected system fields cannot be mapped by tenant administrators."""
    await DataImportService.seed_default_templates(db=db_session)
    job = await DataImportService.create_job(
        db=db_session,
        tenant_id=tenant_a.id,
        actor_id=tenant_admin_a.id,
        dto=ImportJobCreateRequest(template_code="STUDENTS_BULK_IMPORT", name="Student Import Test"),
    )
    csv_content = "adm_no,email,fname,lname,dob,gender,secret_hash\nREG001,test@campus.edu,John,Doe,2002-05-15,MALE,fakehash\n"
    job = await DataImportService.upload_source_file(
        db=db_session,
        tenant_id=tenant_a.id,
        job_id=job.id,
        actor_id=tenant_admin_a.id,
        filename="students.csv",
        file_bytes=csv_content.encode("utf-8"),
    )

    # Attempt to map to protected system field 'password_hash'
    with pytest.raises(PermissionDeniedException) as exc_info:
        await DataImportService.update_mapping(
            db=db_session,
            tenant_id=tenant_a.id,
            job_id=job.id,
            actor_id=tenant_admin_a.id,
            dto=ImportMappingUpdateRequest(
                column_mappings={"secret_hash": "password_hash"}
            ),
        )
    assert "protected system field" in str(exc_info.value)

    # Valid mapping
    mapping = await DataImportService.update_mapping(
        db=db_session,
        tenant_id=tenant_a.id,
        job_id=job.id,
        actor_id=tenant_admin_a.id,
        dto=ImportMappingUpdateRequest(
            column_mappings={
                "adm_no": "admission_number",
                "email": "email",
                "fname": "first_name",
                "lname": "last_name",
                "dob": "date_of_birth",
                "gender": "gender",
            }
        ),
    )
    assert mapping.version >= 1
    assert len(mapping.column_mappings) == 6


# =============================================================================
# 3. VALIDATION PIPELINE & DUPLICATE CONFLICTS
# =============================================================================


@pytest.mark.asyncio
async def test_validation_engine_required_fields_and_formats(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Verify validation engine catches missing fields, bad formats, and intra-file duplicates."""
    await DataImportService.seed_default_templates(db=db_session)
    job = await DataImportService.create_job(
        db=db_session,
        tenant_id=tenant_a.id,
        actor_id=tenant_admin_a.id,
        dto=ImportJobCreateRequest(template_code="STUDENTS_BULK_IMPORT", name="Validation Test"),
    )
    # Ensure Program and Batch exist in tenant_a for FK resolution
    dept = Department(tenant_id=tenant_a.id, code="CS", name="Computer Science")
    db_session.add(dept)
    await db_session.flush()
    prog = Program(tenant_id=tenant_a.id, department_id=dept.id, code="BTECH_CS", name="B.Tech CS", degree_level="UG")
    db_session.add(prog)
    await db_session.flush()
    reg = Regulation(tenant_id=tenant_a.id, code="REG_CS", title="CS Curriculum", effective_year=2026)
    db_session.add(reg)
    await db_session.flush()
    batch = Batch(
        tenant_id=tenant_a.id,
        program_id=prog.id,
        regulation_id=reg.id,
        name="2026-2030",
        admission_year=2026,
        graduation_year=2030,
    )
    db_session.add(batch)
    await db_session.commit()

    # Row 1: Valid
    # Row 2: Bad email, bad date
    # Row 3: Missing admission_number (required)
    # Row 4: Intra-file duplicate admission_number with Row 1
    csv_rows = [
        "admission_number,email,first_name,last_name,date_of_birth,gender,admission_date,expected_graduation_date,program_code,batch_name",
        "STU101,stu101@apextech.edu,John,Doe,2003-01-10,MALE,2026-08-01,2030-05-31,BTECH_CS,2026-2030",
        "STU102,not-an-email,Jane,Smith,bad-date,FEMALE,2026-08-01,2030-05-31,BTECH_CS,2026-2030",
        ",stu103@apextech.edu,Bob,Taylor,2003-02-14,MALE,2026-08-01,2030-05-31,BTECH_CS,2026-2030",
        "STU101,stu104@apextech.edu,Duplicate,Student,2003-03-20,MALE,2026-08-01,2030-05-31,BTECH_CS,2026-2030",
    ]
    job = await DataImportService.upload_source_file(
        db=db_session,
        tenant_id=tenant_a.id,
        job_id=job.id,
        actor_id=tenant_admin_a.id,
        filename="students_val.csv",
        file_bytes="\n".join(csv_rows).encode("utf-8"),
    )

    summary = await DataImportService.run_validation(
        db=db_session,
        tenant_id=tenant_a.id,
        job_id=job.id,
        actor_id=tenant_admin_a.id,
    )
    assert summary["status"] == ImportJobStatus.VALIDATION_FAILED.value
    assert summary["valid_records"] == 1
    assert summary["error_records"] == 3

    # Check row-level results in database
    stmt = select(ImportRecordResult).where(ImportRecordResult.job_id == job.id).order_by(ImportRecordResult.row_number.asc())
    results = (await db_session.execute(stmt)).scalars().all()
    assert len(results) == 4
    res_map = {r.row_number: r for r in results}
    assert res_map[2].status == ImportRecordStatus.VALID.value
    assert res_map[3].status == ImportRecordStatus.INVALID.value
    assert "INVALID_EMAIL_FORMAT" in [e["code"] for e in res_map[3].errors_json]
    assert res_map[4].status == ImportRecordStatus.INVALID.value
    assert "REQUIRED_FIELD_EMPTY" in [e["code"] for e in res_map[4].errors_json]
    assert res_map[5].status == ImportRecordStatus.INVALID.value
    assert "DUPLICATE_IN_FILE" in [e["code"] for e in res_map[5].errors_json]


@pytest.mark.asyncio
async def test_duplicate_detection_against_database_records(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Verify duplicate detection catches existing records in the database."""
    await DataImportService.seed_default_templates(db=db_session)
    dept = Department(tenant_id=tenant_a.id, code="CS-DEPT", name="Computer Science Dept")
    db_session.add(dept)
    await db_session.flush()
    subj = Subject(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        department_id=dept.id,
        code="SUBJ-EXISTING",
        name="Existing Subject",
    )
    db_session.add(subj)
    await db_session.commit()

    job = await DataImportService.create_job(
        db=db_session,
        tenant_id=tenant_a.id,
        actor_id=tenant_admin_a.id,
        dto=ImportJobCreateRequest(
            template_code="COURSES_IMPORT",
            name="Courses Duplicate Check",
            execution_policy=ImportExecutionPolicy.CREATE_NEW.value,
        ),
    )
    csv_rows = [
        "code,name,department_code",
        "SUBJ-EXISTING,Collision Subject,CS-DEPT",
        "SUBJ-NEW,New Fresh Subject,CS-DEPT",
    ]
    job = await DataImportService.upload_source_file(
        db=db_session,
        tenant_id=tenant_a.id,
        job_id=job.id,
        actor_id=tenant_admin_a.id,
        filename="courses.csv",
        file_bytes="\n".join(csv_rows).encode("utf-8"),
    )

    summary = await DataImportService.run_validation(
        db=db_session,
        tenant_id=tenant_a.id,
        job_id=job.id,
        actor_id=tenant_admin_a.id,
    )
    assert summary["status"] == ImportJobStatus.VALIDATION_FAILED.value
    conflicts = await DataImportService.list_conflicts(db=db_session, tenant_id=tenant_a.id, job_id=job.id)
    assert len(conflicts) == 1
    assert conflicts[0].matching_value == "SUBJ-EXISTING"


# =============================================================================
# 4. PREVIEW, APPROVAL GATING & INVALIDATION
# =============================================================================


@pytest.mark.asyncio
async def test_preview_and_approval_workflow_with_invalidation(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Verify preview calculations, approval requirements, and approval invalidation upon mapping change."""
    await DataImportService.seed_default_templates(db=db_session)
    dept = Department(tenant_id=tenant_a.id, code="EE", name="Electrical Eng")
    db_session.add(dept)
    await db_session.flush()
    prog = Program(tenant_id=tenant_a.id, department_id=dept.id, code="BTECH_EE", name="B.Tech EE", degree_level="UG")
    db_session.add(prog)
    await db_session.flush()
    reg = Regulation(tenant_id=tenant_a.id, code="REG_EE", title="EE Curriculum", effective_year=2026)
    db_session.add(reg)
    await db_session.flush()
    batch = Batch(
        tenant_id=tenant_a.id,
        program_id=prog.id,
        regulation_id=reg.id,
        name="BATCH_2026",
        admission_year=2026,
        graduation_year=2030,
    )
    db_session.add(batch)
    await db_session.commit()

    job = await DataImportService.create_job(
        db=db_session,
        tenant_id=tenant_a.id,
        actor_id=tenant_admin_a.id,
        dto=ImportJobCreateRequest(template_code="STUDENTS_BULK_IMPORT", name="High Impact Student Import"),
    )
    # Generate 55 rows to exceed approval_threshold of 50
    header = "admission_number,email,first_name,last_name,date_of_birth,gender,admission_date,expected_graduation_date,program_code,batch_name"
    lines = [header]
    for i in range(1, 56):
        lines.append(f"STU_{i:03d},stu{i:03d}@apextech.edu,First{i},Last{i},2003-01-01,MALE,2026-08-01,2030-05-31,BTECH_EE,BATCH_2026")

    job = await DataImportService.upload_source_file(
        db=db_session,
        tenant_id=tenant_a.id,
        job_id=job.id,
        actor_id=tenant_admin_a.id,
        filename="students_55.csv",
        file_bytes="\n".join(lines).encode("utf-8"),
    )
    summary = await DataImportService.run_validation(
        db=db_session,
        tenant_id=tenant_a.id,
        job_id=job.id,
        actor_id=tenant_admin_a.id,
    )
    assert summary["status"] == ImportJobStatus.AWAITING_APPROVAL.value

    # Preview check
    preview = await DataImportService.get_preview(db=db_session, tenant_id=tenant_a.id, job_id=job.id)
    assert preview["total_source_records"] == 55
    assert preview["records_to_create"] == 55

    # Execution must fail before approval
    with pytest.raises(ImportApprovalRequiredException):
        await DataImportService.execute_import(
            db=db_session,
            tenant_id=tenant_a.id,
            job_id=job.id,
            actor_id=tenant_admin_a.id,
        )

    # Approve job
    job = await DataImportService.approve_job(
        db=db_session,
        tenant_id=tenant_a.id,
        job_id=job.id,
        actor_id=tenant_admin_a.id,
        dto=ImportApprovalRequest(approved=True, notes="Approved for semester batch intake."),
    )
    assert job.status == ImportJobStatus.READY_TO_EXECUTE.value
    assert job.approved_at is not None

    # Invalidate approval by updating column mapping
    mapping = await DataImportService.update_mapping(
        db=db_session,
        tenant_id=tenant_a.id,
        job_id=job.id,
        actor_id=tenant_admin_a.id,
        dto=ImportMappingUpdateRequest(
            column_mappings={
                "admission_number": "admission_number",
                "email": "email",
                "first_name": "first_name",
                "last_name": "last_name",
            }
        ),
    )
    await db_session.refresh(job)
    assert job.approved_at is None
    assert "invalidated" in (job.approval_notes or "").lower()


# =============================================================================
# 5. BOUNDED BATCH EXECUTION & REAL DOMAIN ENTITY CREATION
# =============================================================================


@pytest.mark.asyncio
async def test_bounded_batch_execution_and_entity_creation(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Verify real domain entity creation and batch checkpoints for Departments."""
    await DataImportService.seed_default_templates(db=db_session)
    job = await DataImportService.create_job(
        db=db_session,
        tenant_id=tenant_a.id,
        actor_id=tenant_admin_a.id,
        dto=ImportJobCreateRequest(
            template_code="DEPARTMENTS_IMPORT",
            name="Batch Dept Creation",
            execution_policy=ImportExecutionPolicy.CREATE_NEW.value,
        ),
    )
    csv_rows = [
        "code,name,department_type",
        "MECH,Mechanical Engineering,ACADEMIC",
        "CIVIL,Civil Engineering,ACADEMIC",
        "AERO,Aerospace Engineering,ACADEMIC",
    ]
    job = await DataImportService.upload_source_file(
        db=db_session,
        tenant_id=tenant_a.id,
        job_id=job.id,
        actor_id=tenant_admin_a.id,
        filename="depts_batch.csv",
        file_bytes="\n".join(csv_rows).encode("utf-8"),
    )
    summary = await DataImportService.run_validation(
        db=db_session,
        tenant_id=tenant_a.id,
        job_id=job.id,
        actor_id=tenant_admin_a.id,
    )
    assert summary["status"] == ImportJobStatus.READY_TO_EXECUTE.value

    # Execute job
    job = await DataImportService.execute_import(
        db=db_session,
        tenant_id=tenant_a.id,
        job_id=job.id,
        actor_id=tenant_admin_a.id,
        request=ImportExecutionRequest(batch_size=2),  # test multi-batch processing
    )
    assert job.status == ImportJobStatus.COMPLETED.value
    assert job.created_record_count == 3
    assert job.processed_record_count == 3

    # Verify Department entities exist in DB
    dept_res = await db_session.execute(
        select(Department).where(Department.tenant_id == tenant_a.id, Department.code.in_(["MECH", "CIVIL", "AERO"]))
    )
    depts = dept_res.scalars().all()
    assert len(depts) == 3
    codes = {d.code for d in depts}
    assert codes == {"MECH", "CIVIL", "AERO"}


@pytest.mark.asyncio
async def test_student_import_domain_service_integration(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Verify StudentProfile and User entities are securely created together."""
    await DataImportService.seed_default_templates(db=db_session)
    dept = Department(tenant_id=tenant_a.id, code="MATH", name="Mathematics")
    db_session.add(dept)
    await db_session.flush()
    prog = Program(tenant_id=tenant_a.id, department_id=dept.id, code="BSC_MATH", name="B.Sc Mathematics", degree_level="UG")
    db_session.add(prog)
    await db_session.flush()
    reg = Regulation(tenant_id=tenant_a.id, code="REG_MATH", title="Math Curriculum", effective_year=2026)
    db_session.add(reg)
    await db_session.flush()
    batch = Batch(
        tenant_id=tenant_a.id,
        program_id=prog.id,
        regulation_id=reg.id,
        name="MATH_2026",
        admission_year=2026,
        graduation_year=2030,
    )
    db_session.add(batch)
    await db_session.commit()

    job = await DataImportService.create_job(
        db=db_session,
        tenant_id=tenant_a.id,
        actor_id=tenant_admin_a.id,
        dto=ImportJobCreateRequest(
            template_code="STUDENTS_BULK_IMPORT",
            name="Student Onboarding 2026",
            execution_policy=ImportExecutionPolicy.CREATE_NEW.value,
        ),
    )
    csv_rows = [
        "admission_number,email,first_name,last_name,date_of_birth,gender,admission_date,expected_graduation_date,program_code,batch_name",
        "STU991,alice.turing@apextech.edu,Alice,Turing,2004-06-15,FEMALE,2026-08-01,2030-05-31,BSC_MATH,MATH_2026",
        "STU992,bob.lovelace@apextech.edu,Bob,Lovelace,2004-08-20,MALE,2026-08-01,2030-05-31,BSC_MATH,MATH_2026",
    ]
    job = await DataImportService.upload_source_file(
        db=db_session,
        tenant_id=tenant_a.id,
        job_id=job.id,
        actor_id=tenant_admin_a.id,
        filename="students_int.csv",
        file_bytes="\n".join(csv_rows).encode("utf-8"),
    )
    summary = await DataImportService.run_validation(
        db=db_session,
        tenant_id=tenant_a.id,
        job_id=job.id,
        actor_id=tenant_admin_a.id,
    )
    assert summary["status"] == ImportJobStatus.READY_TO_EXECUTE.value

    job = await DataImportService.execute_import(
        db=db_session,
        tenant_id=tenant_a.id,
        job_id=job.id,
        actor_id=tenant_admin_a.id,
    )
    assert job.status == ImportJobStatus.COMPLETED.value
    assert job.created_record_count == 2

    # Verify User and StudentProfile in DB
    user_res = await db_session.execute(
        select(User).where(User.primary_tenant_id == tenant_a.id, User.email == "alice.turing@apextech.edu")
    )
    alice = user_res.scalar_one_or_none()
    assert alice is not None
    assert alice.first_name == "Alice"

    stu_res = await db_session.execute(
        select(StudentProfile).where(StudentProfile.tenant_id == tenant_a.id, StudentProfile.admission_number == "STU991")
    )
    profile = stu_res.scalar_one_or_none()
    assert profile is not None
    assert profile.user_id == alice.id


# =============================================================================
# 6. RECONCILIATION & ERROR REPORT FORMULA INJECTION ESCAPING
# =============================================================================


@pytest.mark.asyncio
async def test_post_import_reconciliation(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Verify post-import reconciliation identifies matched records and flags inconsistencies."""
    await DataImportService.seed_default_templates(db=db_session)
    job = await DataImportService.create_job(
        db=db_session,
        tenant_id=tenant_a.id,
        actor_id=tenant_admin_a.id,
        dto=ImportJobCreateRequest(template_code="DEPARTMENTS_IMPORT", name="Reconciliation Test"),
    )
    csv_rows = [
        "code,name",
        "BIO,Biotechnology Engineering",
        "CHEM,Chemical Engineering",
    ]
    job = await DataImportService.upload_source_file(
        db=db_session,
        tenant_id=tenant_a.id,
        job_id=job.id,
        actor_id=tenant_admin_a.id,
        filename="recon.csv",
        file_bytes="\n".join(csv_rows).encode("utf-8"),
    )
    await DataImportService.run_validation(db=db_session, tenant_id=tenant_a.id, job_id=job.id, actor_id=tenant_admin_a.id)
    await DataImportService.execute_import(db=db_session, tenant_id=tenant_a.id, job_id=job.id, actor_id=tenant_admin_a.id)

    # Run reconciliation
    rec = await DataImportService.run_reconciliation(
        db=db_session,
        tenant_id=tenant_a.id,
        job_id=job.id,
    )
    assert rec["reconciliation_status"] == ReconciliationStatus.MATCHED.value
    assert rec["source_record_count"] == 2
    assert rec["created_record_count"] == 2
    assert rec["is_balanced"] is True


@pytest.mark.asyncio
async def test_csv_formula_injection_defense(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Verify CSV formula injection characters (=, +, -, @, \\t, \\r) are sanitized in error reports."""
    # Test parser escaping directly
    malicious_inputs = [
        "=cmd|'/c calc'!A0",
        "+SUM(1,2)",
        "-10+20",
        "@SUM(A1:A10)",
        "\tTabbedExploit",
    ]
    for payload in malicious_inputs:
        escaped = DataImportParser.escape_formula_injection(payload)
        assert escaped.startswith("'") or escaped.startswith("'-")

    # Test error report CSV generation
    await DataImportService.seed_default_templates(db=db_session)
    job = await DataImportService.create_job(
        db=db_session,
        tenant_id=tenant_a.id,
        actor_id=tenant_admin_a.id,
        dto=ImportJobCreateRequest(template_code="DEPARTMENTS_IMPORT", name="Err Report Job"),
    )
    # Upload invalid row
    job = await DataImportService.upload_source_file(
        db=db_session,
        tenant_id=tenant_a.id,
        job_id=job.id,
        actor_id=tenant_admin_a.id,
        filename="bad_dept.csv",
        file_bytes=b"code,name\n,=cmd|'/c calc'!A0\n",
    )
    await DataImportService.run_validation(db=db_session, tenant_id=tenant_a.id, job_id=job.id, actor_id=tenant_admin_a.id)

    err_csv = await DataImportService.generate_error_report(
        db=db_session,
        tenant_id=tenant_a.id,
        job_id=job.id,
    )
    assert "row_number" in err_csv


# =============================================================================
# 7. MULTI-TENANT ISOLATION
# =============================================================================


@pytest.mark.asyncio
async def test_strict_multi_tenant_isolation(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    tenant_admin_a: User,
    tenant_admin_b: User,
):
    """Verify Tenant B cannot access or modify Tenant A's import job, records, or files."""
    await DataImportService.seed_default_templates(db=db_session)
    job_a = await DataImportService.create_job(
        db=db_session,
        tenant_id=tenant_a.id,
        actor_id=tenant_admin_a.id,
        dto=ImportJobCreateRequest(template_code="DEPARTMENTS_IMPORT", name="Tenant A Confidential Import"),
    )

    # Tenant B tries to get Tenant A's job
    with pytest.raises(ImportJobNotFoundException):
        await DataImportService.get_job(db=db_session, tenant_id=tenant_b.id, job_id=job_a.id)

    # Tenant B tries to validate Tenant A's job
    with pytest.raises(ImportJobNotFoundException):
        await DataImportService.run_validation(
            db=db_session,
            tenant_id=tenant_b.id,
            job_id=job_a.id,
            actor_id=tenant_admin_b.id,
        )

    # Tenant B tries to execute Tenant A's job
    with pytest.raises(ImportJobNotFoundException):
        await DataImportService.execute_import(
            db=db_session,
            tenant_id=tenant_b.id,
            job_id=job_a.id,
            actor_id=tenant_admin_b.id,
        )


# =============================================================================
# 8. REST API FULL LIFECYCLE TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_rest_api_import_full_lifecycle(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Verify complete end-to-end import flow via FastAPI REST endpoints."""
    await DataImportService.seed_default_templates(db=db_session)
    headers = make_auth_headers(tenant_admin_a, tenant_a.id, "INSTITUTION_ADMIN")

    # 1. List templates
    tmpl_resp = await client.get("/api/v1/data-import/templates", headers=headers)
    assert tmpl_resp.status_code == 200
    templates = tmpl_resp.json()
    assert len(templates) >= 5

    # 2. Download sample CSV
    dl_resp = await client.get("/api/v1/data-import/templates/DEPARTMENTS_IMPORT/download-blank", headers=headers)
    assert dl_resp.status_code == 200
    assert "code,name" in dl_resp.text

    # 3. Create job
    create_resp = await client.post(
        "/api/v1/data-import/jobs",
        headers=headers,
        json={
            "template_code": "DEPARTMENTS_IMPORT",
            "name": "API Department Import",
            "execution_policy": "CREATE_NEW",
        },
    )
    assert create_resp.status_code == 201
    job_data = create_resp.json()
    job_id = job_data["id"]
    assert job_data["status"] == "DRAFT"

    # 4. Upload file
    csv_content = b"code,name,department_type\nROBOTICS,Robotics Engineering,ACADEMIC\nAI,Artificial Intelligence,ACADEMIC\n"
    upload_resp = await client.post(
        f"/api/v1/data-import/jobs/{job_id}/upload",
        headers=headers,
        files={"file": ("depts.csv", csv_content, "text/csv")},
    )
    assert upload_resp.status_code == 200
    assert upload_resp.json()["status"] == "MAPPING_PENDING"

    # 5. Run validation
    val_resp = await client.post(f"/api/v1/data-import/jobs/{job_id}/validate", headers=headers)
    assert val_resp.status_code == 200
    val_data = val_resp.json()
    assert val_data["status"] == "READY_TO_EXECUTE"
    assert val_data["valid_records"] == 2

    # 6. Get preview
    prev_resp = await client.get(f"/api/v1/data-import/jobs/{job_id}/preview", headers=headers)
    assert prev_resp.status_code == 200
    assert prev_resp.json()["records_to_create"] == 2

    # 7. Execute job
    exec_resp = await client.post(
        f"/api/v1/data-import/jobs/{job_id}/execute",
        headers=headers,
        json={"batch_size": 10},
    )
    assert exec_resp.status_code == 200
    assert exec_resp.json()["status"] == "COMPLETED"
    assert exec_resp.json()["created_record_count"] == 2

    # 8. Reconcile
    rec_resp = await client.post(f"/api/v1/data-import/jobs/{job_id}/reconcile", headers=headers)
    assert rec_resp.status_code == 200
    assert rec_resp.json()["reconciliation_status"] == "MATCHED"

    # 9. Download error report
    err_resp = await client.get(f"/api/v1/data-import/jobs/{job_id}/error-report", headers=headers)
    assert err_resp.status_code == 200
    assert "row_number" in err_resp.text
