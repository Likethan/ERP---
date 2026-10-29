"""System seed routine for standard roles, permissions, and initial mappings."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.core.permissions import ALL_PERMISSIONS, DEFAULT_ROLE_PERMISSIONS
from app.models.people import Permission, Role, RolePermission
from app.models.workflow import (
    WorkflowDefinition,
    WorkflowStatus,
    WorkflowTrigger,
    WorkflowTriggerType,
    WorkflowVersion,
)


async def seed_system_permissions_and_roles(db: AsyncSession) -> None:
    """Seed standard system permissions, roles, and default mappings idempotently."""
    logger.info("Verifying system permissions and roles...")

    # 1. Seed Permissions
    existing_perms_res = await db.execute(select(Permission))
    existing_perms = {p.code: p for p in existing_perms_res.scalars().all()}

    now = datetime.now(UTC)
    for perm_def in ALL_PERMISSIONS:
        if perm_def.code not in existing_perms:
            new_perm = Permission(
                id=uuid4(),
                code=perm_def.code,
                domain=perm_def.domain,
                description=perm_def.description,
                created_at=now,
            )
            db.add(new_perm)
            existing_perms[perm_def.code] = new_perm

    await db.flush()

    # 2. Seed System Roles
    existing_roles_res = await db.execute(select(Role).where(Role.is_system.is_(True)))
    existing_roles = {r.name: r for r in existing_roles_res.scalars().all()}

    for role_name, perm_codes in DEFAULT_ROLE_PERMISSIONS.items():
        if role_name not in existing_roles:
            role = Role(
                id=uuid4(),
                tenant_id=None,  # System roles are global templates
                name=role_name,
                display_name=role_name.replace("_", " ").title(),
                description=f"Standard institutional role for {role_name}.",
                is_system=True,
            )
            db.add(role)
            await db.flush()
            existing_roles[role_name] = role

        role = existing_roles[role_name]

        # 3. Seed Role-Permission Mappings
        existing_rp_res = await db.execute(
            select(RolePermission).where(RolePermission.role_id == role.id)
        )
        existing_rp_set = {rp.permission_id for rp in existing_rp_res.scalars().all()}

        for p_code in set(perm_codes):
            perm_obj = existing_perms.get(p_code)
            if perm_obj and perm_obj.id not in existing_rp_set:
                db.add(
                    RolePermission(
                        role_id=role.id,
                        permission_id=perm_obj.id,
                    )
                )
                existing_rp_set.add(perm_obj.id)

    # 3. Seed Platform API Catalog
    from app.platform_api.catalog import catalog_service

    await catalog_service.seed_catalog_idempotently(db)

    # 4. Seed Configuration Definitions & Dependencies (Step 23)
    await seed_configuration_defaults(db)

    # 5. Seed Master Data Definitions & Reference Data (Step 24)
    await seed_master_data_defaults(db)

    # 6. Seed Case Management, Work Queues & SLA Defaults (Step 25)
    await seed_case_management_defaults(db)

    # 7. Seed Enterprise Notifications, Templates & Rules Defaults (Step 26)
    await seed_notification_defaults(db)

    await db.commit()
    logger.info(
        "System permissions, roles, API catalog, config, master data, case operations, and notification orchestration synced successfully."
    )



async def seed_documents_master_data(db: AsyncSession, tenant_id) -> None:
    """Seed standard document categories, types, requirements, certificate templates, and records."""
    from app.models.documents import (
        CertificateTemplate,
        CertificateTemplateField,
        CertificateTemplateVersion,
        DocumentCategory,
        DocumentType,
        InstitutionalRecord,
    )

    logger.info(f"Seeding documents master data for tenant {tenant_id}...")

    # 1. Categories
    default_categories = [
        (
            "IDENTITY",
            "Identity Verification",
            "Government and institutional identity proofs",
            True,
            False,
        ),
        (
            "ACADEMIC",
            "Academic Records",
            "Transcripts, grade reports, and academic verifications",
            True,
            False,
        ),
        (
            "ADMISSION",
            "Admission Credentials",
            "Eligibility proofs, migration and transfer credentials",
            True,
            False,
        ),
        (
            "FINANCIAL",
            "Financial Documentation",
            "Income proofs, fee concessions, and scholarship awards",
            True,
            True,
        ),
        (
            "PLACEMENT",
            "Career & Placement",
            "Resumes, offer letters, and skill certifications",
            True,
            False,
        ),
        (
            "HOSTEL",
            "Hostel & Residence",
            "Room agreements, medical clearances, and resident passes",
            True,
            True,
        ),
        (
            "TRANSPORT",
            "Transport & Transit",
            "Pass applications and bus route compliance",
            False,
            True,
        ),
        (
            "CERTIFICATE",
            "Certificates & Credentials",
            "Institutional bonafide, conduct, and degrees",
            True,
            False,
        ),
        (
            "ADMINISTRATIVE",
            "Administrative Records",
            "Official institutional directives and notifications",
            True,
            False,
        ),
        ("MEDICAL", "Health & Medical", "Fitness certificates and medical disclosures", True, True),
        (
            "OTHER",
            "Other Institutional Records",
            "Supplementary documents and general records",
            False,
            False,
        ),
    ]

    cat_map = {}
    for code, name, desc, req_ver, req_exp in default_categories:
        existing = await db.scalar(
            select(DocumentCategory).where(
                DocumentCategory.tenant_id == tenant_id,
                DocumentCategory.code == code,
            )
        )
        if not existing:
            cat = DocumentCategory(
                id=uuid4(),
                tenant_id=tenant_id,
                code=code,
                name=name,
                description=desc,
                is_active=True,
                requires_verification=req_ver,
                requires_expiry=req_exp,
                applicable_roles=["STUDENT", "FACULTY", "STAFF"],
                applicable_document_types=["Standard Document"],
            )
            db.add(cat)
            await db.flush()
            cat_map[code] = cat
        else:
            cat_map[code] = existing

    # 2. Document Types
    default_types = [
        (
            "IDENTITY",
            "AADHAAR",
            "Aadhaar Card",
            "Unique Identification Authority of India (UIDAI) Card",
            True,
            False,
            True,
        ),
        ("IDENTITY", "PAN", "PAN Card", "Permanent Account Number Tax Card", False, False, True),
        (
            "IDENTITY",
            "PASSPORT",
            "Passport",
            "International Travel and Nationality Passport",
            False,
            True,
            True,
        ),
        (
            "ACADEMIC",
            "MARKSHEET_10TH",
            "10th Standard Marksheet",
            "Secondary School Leaving Certificate (SSLC/10th)",
            True,
            False,
            True,
        ),
        (
            "ACADEMIC",
            "MARKSHEET_12TH",
            "12th Standard Marksheet",
            "Higher Secondary Certificate (HSC/12th)",
            True,
            False,
            True,
        ),
        (
            "ACADEMIC",
            "DEGREE_CERTIFICATE",
            "Degree Certificate",
            "Official University Degree Award",
            False,
            False,
            True,
        ),
        (
            "ADMISSION",
            "TRANSFER_CERTIFICATE",
            "Transfer Certificate",
            "Institutional Migration and Transfer Certificate",
            True,
            False,
            True,
        ),
        (
            "ADMISSION",
            "COMMUNITY_CERTIFICATE",
            "Community / Caste Certificate",
            "Official State Reservation / Community Document",
            False,
            False,
            True,
        ),
        (
            "FINANCIAL",
            "INCOME_CERTIFICATE",
            "Income Certificate",
            "Annual Family Income Certificate for Fee Concession",
            False,
            True,
            True,
        ),
        (
            "PLACEMENT",
            "RESUME",
            "Student Placement Resume",
            "Curriculum Vitae for campus recruitment",
            False,
            False,
            False,
        ),
        (
            "PLACEMENT",
            "INTERNSHIP_CERTIFICATE",
            "Internship Completion Certificate",
            "Proof of industrial training or internship completion",
            False,
            False,
            True,
        ),
        (
            "HOSTEL",
            "HOSTEL_UNDERTAKING",
            "Hostel Rules Undertaking",
            "Signed student and parent residential rules undertaking",
            False,
            True,
            False,
        ),
        (
            "TRANSPORT",
            "TRANSPORT_PASS",
            "Bus / Transit Pass Application",
            "Institutional transportation registration card",
            False,
            True,
            False,
        ),
        (
            "OTHER",
            "GENERAL_RECORD",
            "General Institutional Record",
            "Miscellaneous supporting document",
            False,
            False,
            False,
        ),
    ]

    for cat_code, code, name, desc, req_def, req_exp, req_ver in default_types:
        cat = cat_map.get(cat_code)
        if not cat:
            continue
        existing_type = await db.scalar(
            select(DocumentType).where(
                DocumentType.tenant_id == tenant_id,
                DocumentType.code == code,
            )
        )
        if not existing_type:
            dt = DocumentType(
                id=uuid4(),
                tenant_id=tenant_id,
                category_id=cat.id,
                code=code,
                name=name,
                description=desc,
                is_required_by_default=req_def,
                requires_expiry=req_exp,
                requires_verification=req_ver,
                allowed_owner_types=["STUDENT", "FACULTY", "STAFF"],
                is_active=True,
            )
            db.add(dt)

    # 3. Certificate Templates
    templates = [
        (
            "BONAFIDE",
            "Institutional Student Bonafide Certificate",
            "BONAFIDE",
            "Official bonafide certificate for passport, loan, or external verifications",
        ),
        (
            "COURSE_COMPLETION",
            "Course Completion Certificate",
            "COURSE_COMPLETION",
            "Attests completion of prescribed curriculum and coursework",
        ),
        (
            "TRANSFER",
            "Transfer & Migration Certificate",
            "TRANSFER",
            "Official transfer certificate issued upon program departure",
        ),
        (
            "CONDUCT",
            "Student Conduct Certificate",
            "CONDUCT",
            "Testimonial verifying good conduct and institutional disciplinary standing",
        ),
        (
            "CHARACTER",
            "Character Testimonial",
            "CHARACTER",
            "Official moral and civic character endorsement",
        ),
        (
            "INTERNSHIP",
            "Internship Endorsement Letter",
            "INTERNSHIP",
            "Recommendation letter for off-campus summer internships",
        ),
        (
            "PARTICIPATION",
            "Extracurricular Participation Certificate",
            "PARTICIPATION",
            "Recognition of participation in institutional symposia or sports",
        ),
    ]

    for code, title, c_type, desc in templates:
        existing_tmpl = await db.scalar(
            select(CertificateTemplate).where(
                CertificateTemplate.tenant_id == tenant_id,
                CertificateTemplate.code == code,
            )
        )
        if not existing_tmpl:
            tmpl = CertificateTemplate(
                id=uuid4(),
                tenant_id=tenant_id,
                code=code,
                template_name=title,
                certificate_type=c_type,
                description=desc,
                applicable_audience=["STUDENT"],
                status="ACTIVE",
                current_version="1.0",
                template_body="""<div class="cert-body">
                    <h2>{{ institution_name }}</h2>
                    <h3>{{ template_name }}</h3>
                    <p>This is to certify that <strong>{{ student_name }}</strong> (Roll No: <strong>{{ roll_number }}</strong>) is a bona fide student of <strong>{{ department }}</strong>, enrolled in <strong>{{ program }}</strong>.</p>
                    <p>Issued on: {{ issue_date }} | Certificate No: {{ certificate_number }}</p>
                </div>""",
                usage_count=5,
            )
            db.add(tmpl)
            await db.flush()

            ver = CertificateTemplateVersion(
                id=uuid4(),
                tenant_id=tenant_id,
                template_id=tmpl.id,
                version_string="1.0",
                template_body=tmpl.template_body,
                changelog="Initial production layout",
                is_active=True,
            )
            db.add(ver)

            fields = [
                ("student_name", "Student Full Name", "SYSTEM_VARIABLE", "student.name"),
                ("roll_number", "Roll Number", "SYSTEM_VARIABLE", "student.roll_number"),
                ("program", "Degree Program", "SYSTEM_VARIABLE", "student.program"),
                ("department", "Department", "SYSTEM_VARIABLE", "student.department"),
            ]
            for fname, flabel, ftype, fmap in fields:
                f_obj = CertificateTemplateField(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    template_id=tmpl.id,
                    name=fname,
                    label=flabel,
                    field_type=ftype,
                    required=True,
                    system_variable_mapping=fmap,
                )
                db.add(f_obj)

    # 4. Institutional Governance Records
    inst_records = [
        (
            "REC-GOV-001",
            "NAAC Accreditation Certificate (Grade A++)",
            "Accreditations & Regulatory",
            "PUBLIC",
            "Office of Academic Excellence",
            "NAAC/2024/A++",
        ),
        (
            "REC-GOV-002",
            "Autonomous Institution Regulation Handbook 2026",
            "Policies & Regulations",
            "INTERNAL",
            "Academic Council",
            "AC/REG/2026/01",
        ),
        (
            "REC-GOV-003",
            "State AICTE Approval Order for New Engineering Programs",
            "Statutory Approvals",
            "PUBLIC",
            "Directorate of Technical Education",
            "AICTE/F-102/2026",
        ),
        (
            "REC-GOV-004",
            "Campus Security, Anti-Ragging & Cyber Protection Policy",
            "Campus Governance",
            "INTERNAL",
            "Office of the Dean (Student Affairs)",
            "DSA/SEC/2026",
        ),
        (
            "REC-GOV-005",
            "Governing Council Executive Committee Confidential Proceedings",
            "Governance Minutes",
            "RESTRICTED",
            "Board of Governors",
            "BOG/MIN/2026/02",
        ),
    ]

    for code, name, cat_name, conf, dept, ref_no in inst_records:
        existing_rec = await db.scalar(
            select(InstitutionalRecord).where(
                InstitutionalRecord.tenant_id == tenant_id,
                InstitutionalRecord.code == code,
            )
        )
        if not existing_rec:
            rec = InstitutionalRecord(
                id=uuid4(),
                tenant_id=tenant_id,
                record_name=name,
                code=code,
                category=cat_name,
                owner_department=dept,
                confidentiality=conf,
                status="ACTIVE",
                created_date=datetime.now(UTC),
                issuing_authority=dept,
                reference_number=ref_no,
                description=f"Institutional record for {name}",
                file_type="application/pdf",
                file_size="2.4 MB",
                related_documents=[],
            )
            db.add(rec)

    await db.commit()
    logger.info("Documents master data seeded successfully.")


async def seed_intelligence_master_data(
    db: AsyncSession,
    tenant_id,
    user_id=None,
) -> None:
    """Seed sample intelligence conversations, insights, alerts, saved views, and activity records."""
    from app.models.intelligence import (
        AIActivity,
        Alert,
        Conversation,
        Insight,
        Message,
        SavedInsight,
    )
    from app.models.people import User

    logger.info(f"Seeding intelligence master data for tenant {tenant_id}...")

    # 1. Resolve user if not provided
    target_user_id = user_id
    target_user_name = "System Admin"
    target_user_role = "ADMIN"
    if not target_user_id:
        user_res = await db.execute(select(User).where(User.tenant_id == tenant_id).limit(1))
        first_user = user_res.scalars().first()
        if first_user:
            target_user_id = first_user.id
            target_user_name = first_user.full_name or "System User"

    now = datetime.now(UTC)

    # 2. Seed Insights if none exist
    existing_insights = await db.execute(
        select(Insight).where(Insight.tenant_id == tenant_id).limit(1)
    )
    if not existing_insights.scalars().first():
        insights_to_seed = [
            Insight(
                id=uuid4(),
                tenant_id=tenant_id,
                title="Attendance Shortage Cluster in Engineering Term 5",
                type="ATTENDANCE",
                domain="ATTENDANCE",
                priority="HIGH",
                status="NEW",
                summary="14 students across Computer Science Semester 5 exhibit attendance lower than 75%, risking exam disqualification under Regulation 7.2.",
                affected_record_count=14,
                affected_records=[
                    {"id": "s-1", "name": "Aarav Patel", "type": "STUDENT", "href": "/students"}
                ],
                detected_at=now,
                recommended_action="Dispatch parent notifications and schedule mentor advising sessions before upcoming assessment cutoff.",
                recommended_action_href="/attendance/alerts",
                evidence=[
                    {"metric": "Average Cohort Attendance", "value": "71.2%", "baseline": "75.0%"}
                ],
                methodology="Calculated over 45 conducted sessions in current academic term.",
                is_saved=False,
                activity_timeline=[
                    {
                        "action": "System Detected",
                        "actor": "CampusOS Telemetry",
                        "timestamp": now.isoformat(),
                    }
                ],
            ),
            Insight(
                id=uuid4(),
                tenant_id=tenant_id,
                title="Strong Positive Placement Trajectory in Tech Tracks",
                type="PLACEMENT",
                domain="PLACEMENT",
                priority="LOW",
                status="NEW",
                summary="Computer Science & IT graduates recorded an 88.4% recruitment conversion with an average CTC increase of 14% year-over-year.",
                affected_record_count=286,
                detected_at=now,
                recommended_action="Review prospective Day-1 recruitment schedules to accommodate visiting MNCs.",
                recommended_action_href="/placement/drives",
                evidence=[{"metric": "Average CTC", "value": "₹7.8 LPA", "baseline": "₹6.8 LPA"}],
                is_saved=True,
            ),
            Insight(
                id=uuid4(),
                tenant_id=tenant_id,
                title="Approaching Transfer Certificate Expiration Horizon",
                type="DOCUMENT",
                domain="DOCUMENTS",
                priority="MEDIUM",
                status="NEW",
                summary="8 temporary admission transfer proofs expire within the next 30 days and require permanent submission.",
                affected_record_count=8,
                detected_at=now,
                recommended_action="Initiate bulk SMS reminder to affected admission candidates.",
                recommended_action_href="/documents",
                evidence=[
                    {"metric": "Expiring Documents", "value": "8 records", "baseline": "0 records"}
                ],
                is_saved=False,
            ),
        ]
        for ins in insights_to_seed:
            db.add(ins)

    # 3. Seed Alerts if none exist
    existing_alerts = await db.execute(select(Alert).where(Alert.tenant_id == tenant_id).limit(1))
    if not existing_alerts.scalars().first():
        alerts_to_seed = [
            Alert(
                id=uuid4(),
                tenant_id=tenant_id,
                title="Critical Attendance Shortage: 14 Engineering Students Below 75%",
                type="ATTENDANCE",
                domain="ATTENDANCE",
                severity="CRITICAL",
                status="OPEN",
                detected_at=now,
                affected_count=14,
                source_domain="Attendance Desk",
                reason="Cumulative attendance has dipped below university statutory threshold for semester assessments.",
                recommended_action="Notify students and academic counselors immediately before final eligibility cutoff.",
                recommended_action_href="/attendance/alerts",
                activity_timeline=[
                    {
                        "action": "Alert Triggered",
                        "actor": "Automated Rule Engine",
                        "timestamp": now.isoformat(),
                    }
                ],
            ),
            Alert(
                id=uuid4(),
                tenant_id=tenant_id,
                title="Outstanding Fee Balance Exceeds ₹2,500,000 in Final Year Cohort",
                type="FINANCE",
                domain="FINANCE",
                severity="WARNING",
                status="OPEN",
                detected_at=now,
                affected_count=48,
                source_domain="Finance Ledger",
                reason="Unsettled tuition dues remain open past scheduled remittance deadline.",
                recommended_action="Dispatch fee ledger reminders and offer installment payment schedules.",
                recommended_action_href="/finance/invoices",
            ),
            Alert(
                id=uuid4(),
                tenant_id=tenant_id,
                title="Hostel Block A Occupancy at 94% Capacity",
                type="INFRASTRUCTURE",
                domain="INFRASTRUCTURE",
                severity="INFO",
                status="OPEN",
                detected_at=now,
                affected_count=12,
                source_domain="Hostel Warden Desk",
                reason="Bed availability in Block A has reached critical threshold ahead of upcoming term intake.",
                recommended_action="Direct new allocations to Block C and PG Wing.",
                recommended_action_href="/infrastructure",
            ),
        ]
        for alt in alerts_to_seed:
            db.add(alt)

    # 4. Seed Conversation & Messages if user exists and no conversation exists
    if target_user_id:
        existing_convs = await db.execute(
            select(Conversation)
            .where(
                Conversation.tenant_id == tenant_id,
                Conversation.user_id == target_user_id,
            )
            .limit(1)
        )
        if not existing_convs.scalars().first():
            conv_id = uuid4()
            conv = Conversation(
                id=conv_id,
                tenant_id=tenant_id,
                user_id=target_user_id,
                title="Semester Attendance & Performance Analysis",
                domain="ATTENDANCE",
                status="ACTIVE",
                context_type="GLOBAL",
                message_count=2,
                last_message_snippet="Identified 14 students below statutory 75% attendance threshold.",
                last_message_at=now,
            )
            db.add(conv)

            user_msg = Message(
                id=uuid4(),
                tenant_id=tenant_id,
                conversation_id=conv_id,
                role="USER",
                status="COMPLETED",
                content="How many students are below 75% attendance?",
                created_at=now,
            )
            db.add(user_msg)

            assistant_msg = Message(
                id=uuid4(),
                tenant_id=tenant_id,
                conversation_id=conv_id,
                role="ASSISTANT",
                status="COMPLETED",
                content="Across the Computer Science department in the current academic semester, 14 students have cumulative attendance falling below the university mandatory 75% attendance threshold.",
                structured_response=[
                    {
                        "type": "METRIC",
                        "title": "Students Below Attendance Threshold",
                        "value": 14,
                        "unit": "Students",
                        "source_ids": ["attendance-threshold-audit"],
                    },
                    {
                        "type": "RECOMMENDATION",
                        "title": "Statutory Academic Advising",
                        "content": "Schedule mentor counseling sessions before final exam admit card release.",
                    },
                ],
                sources=[
                    {
                        "source_id": "attendance-threshold-audit",
                        "domain": "attendance",
                        "entity_type": "AttendanceRecord",
                        "label": "Semester Attendance Roster",
                        "retrieved_at": now.isoformat(),
                    }
                ],
                model="campusos-intelligence-mock",
                provider="mock",
                latency_ms=85,
                created_at=now,
            )
            db.add(assistant_msg)

            # Saved Insight
            saved = SavedInsight(
                id=uuid4(),
                tenant_id=tenant_id,
                user_id=target_user_id,
                title="CSE Semester 5 Low Attendance Cohort",
                type="AI_RESPONSE",
                domain="ATTENDANCE",
                content_snippet="14 students below 75% threshold in CSE Semester 5.",
                query="How many students are below 75% attendance?",
                response_snapshot={
                    "metric": 14,
                    "cohort": "CSE S5",
                },
                last_accessed_at=now,
            )
            db.add(saved)

            # Activity record
            activity = AIActivity(
                id=uuid4(),
                tenant_id=tenant_id,
                user_id=target_user_id,
                user_name=target_user_name,
                user_role=target_user_role,
                conversation_id=conv_id,
                query="How many students are below 75% attendance?",
                query_hash="hash-att-75",
                domain="ATTENDANCE",
                tools_invoked=["attendance.get_students_below_threshold"],
                result_summary="Identified 14 students below threshold.",
                duration_ms=85,
                status="COMPLETED",
                provider="mock",
                model="campusos-intelligence-mock",
            )
            db.add(activity)

    await db.commit()
    logger.info("Intelligence master data seeded successfully.")


async def seed_sample_workflows(db: AsyncSession, tenant_id: uuid4) -> None:
    """Seed development/staging sample workflows in DRAFT status (never auto-activated in prod)."""
    logger.info("Seeding development sample workflows for tenant %s...", tenant_id)
    now = datetime.now(UTC)

    sample_workflows = [
        {
            "name": "Daily Attendance Shortage Alert [Sample]",
            "description": "Daily automated scan for students whose attendance has fallen below policy threshold.",
            "domain": "ATTENDANCE",
            "trigger": {
                "trigger_type": WorkflowTriggerType.SCHEDULE,
                "schedule_time": "08:30",
                "days_of_week": [0, 1, 2, 3, 4],
            },
            "steps": [
                {
                    "id": "check_shortage",
                    "name": "Scan Attendance Shortages",
                    "step_type": "ACTION",
                    "action_type": "QUEUE_ATTENDANCE_ALERT_CHECK",
                    "parameters": {"threshold_percentage": 75.0},
                    "next_step_id": None,
                }
            ],
        },
        {
            "name": "Daily Overdue Fee Reminder [Sample]",
            "description": "Identifies outstanding overdue student fee invoices and creates reminder alerts.",
            "domain": "FINANCE",
            "trigger": {
                "trigger_type": WorkflowTriggerType.SCHEDULE,
                "schedule_time": "20:00",
            },
            "steps": [
                {
                    "id": "scan_invoices",
                    "name": "Identify Overdue Invoices",
                    "step_type": "ACTION",
                    "action_type": "QUEUE_FEE_REMINDER",
                    "parameters": {"days_overdue_threshold": 1, "min_amount": 100.0},
                    "next_step_id": None,
                }
            ],
        },
        {
            "name": "Document Expiry Reminder [Sample]",
            "description": "Scans mandatory verification documents approaching expiry within 30 days.",
            "domain": "DOCUMENTS",
            "trigger": {
                "trigger_type": WorkflowTriggerType.SCHEDULE,
                "schedule_time": "09:00",
            },
            "steps": [
                {
                    "id": "scan_docs",
                    "name": "Scan Expiring Documents",
                    "step_type": "ACTION",
                    "action_type": "QUEUE_DOCUMENT_EXPIRY_CHECK",
                    "parameters": {"days_threshold": 30},
                    "next_step_id": None,
                }
            ],
        },
        {
            "name": "Weekly Placement Summary [Sample]",
            "description": "Generates weekly placement and recruitment drive activity report.",
            "domain": "PLACEMENT",
            "trigger": {
                "trigger_type": WorkflowTriggerType.SCHEDULE,
                "schedule_time": "17:00",
                "days_of_week": [4],
            },
            "steps": [
                {
                    "id": "generate_summary",
                    "name": "Generate Weekly Drive Summary",
                    "step_type": "ACTION",
                    "action_type": "GENERATE_REPORT_SUMMARY",
                    "parameters": {"report_type": "PLACEMENT_WEEKLY"},
                    "next_step_id": None,
                }
            ],
        },
    ]

    for item in sample_workflows:
        # Check if already seeded
        existing = await db.execute(
            select(WorkflowDefinition).where(
                WorkflowDefinition.name == item["name"],
                WorkflowDefinition.tenant_id == tenant_id,
            )
        )
        if existing.scalar_one_or_none():
            continue

        wf_id = uuid4()
        ver_id = uuid4()
        wf = WorkflowDefinition(
            id=wf_id,
            tenant_id=tenant_id,
            name=item["name"],
            description=item["description"],
            domain=item["domain"],
            status=WorkflowStatus.DRAFT,  # Explicitly DRAFT
            is_system=False,
            active_version=1,
            current_version_id=ver_id,
            created_at=now,
            updated_at=now,
        )
        db.add(wf)

        ver = WorkflowVersion(
            id=ver_id,
            workflow_id=wf_id,
            version=1,
            is_active=True,
            change_summary="Initial staging seed",
            trigger_definition=item["trigger"],
            steps_definition=item["steps"],
            created_at=now,
        )
        db.add(ver)

        trg = WorkflowTrigger(
            id=uuid4(),
            workflow_id=wf_id,
            trigger_type=item["trigger"]["trigger_type"],
            schedule_time=item["trigger"].get("schedule_time"),
            days_of_week=item["trigger"].get("days_of_week"),
            is_enabled=False,  # Kept disabled in staging until activated
            created_at=now,
        )
        db.add(trg)

    await db.commit()
    logger.info("Sample workflows seeded successfully in DRAFT status.")


async def seed_configuration_defaults(db: AsyncSession, tenant_id: Any | None = None) -> None:
    """Seed standard system configuration definitions, dependencies, and default sequences idempotently."""
    from app.models.configuration import (
        ConfigurationDataType,
        ConfigurationDefinition,
        ConfigurationDependency,
        ConfigurationScope,
        ConfigurationSensitivity,
        DependencyCriticality,
        NumberingResetFrequency,
        NumberingSequence,
    )

    logger.info("Synchronizing standard configuration definitions and dependencies...")

    # 1. Configuration Definitions
    definitions_data = [
        {
            "key": "attendance.minimum_percentage",
            "name": "Minimum Attendance Requirement",
            "description": "Minimum percentage of attendance required for exam eligibility.",
            "category": "ATTENDANCE",
            "module": "ATTENDANCE",
            "data_type": ConfigurationDataType.PERCENTAGE,
            "default_value": 75,
            "validation_schema": {"min": 0, "max": 100},
            "sensitivity": ConfigurationSensitivity.INTERNAL,
            "scope": ConfigurationScope.TENANT,
        },
        {
            "key": "attendance.grace_percentage",
            "name": "Attendance Grace Margin",
            "description": "Allowed grace attendance percentage for medical/special dispensations.",
            "category": "ATTENDANCE",
            "module": "ATTENDANCE",
            "data_type": ConfigurationDataType.PERCENTAGE,
            "default_value": 5,
            "validation_schema": {"min": 0, "max": 20},
            "sensitivity": ConfigurationSensitivity.INTERNAL,
            "scope": ConfigurationScope.TENANT,
        },
        {
            "key": "finance.invoice.due_days",
            "name": "Invoice Payment Due Days",
            "description": "Default payment window in days before an invoice is marked overdue.",
            "category": "FINANCE",
            "module": "FINANCE",
            "data_type": ConfigurationDataType.INTEGER,
            "default_value": 15,
            "validation_schema": {"min": 1, "max": 365},
            "sensitivity": ConfigurationSensitivity.INTERNAL,
            "scope": ConfigurationScope.TENANT,
        },
        {
            "key": "finance.currency",
            "name": "Operating Currency",
            "description": "ISO 4217 currency code for billing and financial transactions.",
            "category": "FINANCE",
            "module": "FINANCE",
            "data_type": ConfigurationDataType.CURRENCY,
            "default_value": "INR",
            "sensitivity": ConfigurationSensitivity.PUBLIC,
            "scope": ConfigurationScope.TENANT,
        },
        {
            "key": "examination.result.passing_percentage",
            "name": "Examination Pass Percentage",
            "description": "Minimum percentage required to clear an academic assessment.",
            "category": "EXAMINATION",
            "module": "EXAMINATION",
            "data_type": ConfigurationDataType.PERCENTAGE,
            "default_value": 40,
            "validation_schema": {"min": 0, "max": 100},
            "sensitivity": ConfigurationSensitivity.INTERNAL,
            "scope": ConfigurationScope.TENANT,
        },
        {
            "key": "placement.application.max_active_applications",
            "name": "Max Active Placement Applications",
            "description": "Maximum number of simultaneous active placement drive applications per student.",
            "category": "PLACEMENT",
            "module": "PLACEMENT",
            "data_type": ConfigurationDataType.INTEGER,
            "default_value": 5,
            "validation_schema": {"min": 1, "max": 50},
            "sensitivity": ConfigurationSensitivity.INTERNAL,
            "scope": ConfigurationScope.TENANT,
        },
        {
            "key": "documents.default_retention_days",
            "name": "Document Retention Period",
            "description": "Default duration in days before document records are scheduled for archival.",
            "category": "DOCUMENTS",
            "module": "DOCUMENTS",
            "data_type": ConfigurationDataType.INTEGER,
            "default_value": 365,
            "validation_schema": {"min": 1, "max": 3650},
            "sensitivity": ConfigurationSensitivity.INTERNAL,
            "scope": ConfigurationScope.TENANT,
        },
        {
            "key": "notifications.digest.enabled",
            "name": "Notification Digest Enabled",
            "description": "Enable daily batched digests for low-priority notifications.",
            "category": "NOTIFICATIONS",
            "module": "CAMPUS",
            "data_type": ConfigurationDataType.BOOLEAN,
            "default_value": True,
            "sensitivity": ConfigurationSensitivity.INTERNAL,
            "scope": ConfigurationScope.TENANT,
        },
        {
            "key": "localization.timezone",
            "name": "Default Timezone",
            "description": "IANA timezone identifier for tenant schedule operations.",
            "category": "LOCALIZATION",
            "module": "SYSTEM",
            "data_type": ConfigurationDataType.STRING,
            "default_value": "Asia/Kolkata",
            "sensitivity": ConfigurationSensitivity.PUBLIC,
            "scope": ConfigurationScope.TENANT,
        },
        {
            "key": "localization.locale",
            "name": "Default Locale",
            "description": "Language and regional formatting locale.",
            "category": "LOCALIZATION",
            "module": "SYSTEM",
            "data_type": ConfigurationDataType.STRING,
            "default_value": "en-IN",
            "sensitivity": ConfigurationSensitivity.PUBLIC,
            "scope": ConfigurationScope.TENANT,
        },
        {
            "key": "branding.display_name",
            "name": "Institution Display Name",
            "description": "Display branding title for portals and outbound emails.",
            "category": "BRANDING",
            "module": "SYSTEM",
            "data_type": ConfigurationDataType.STRING,
            "default_value": "CampusOS Institution",
            "sensitivity": ConfigurationSensitivity.PUBLIC,
            "scope": ConfigurationScope.TENANT,
        },
        {
            "key": "branding.primary_color",
            "name": "Branding Primary Color",
            "description": "Primary brand theme hex color.",
            "category": "BRANDING",
            "module": "SYSTEM",
            "data_type": ConfigurationDataType.STRING,
            "default_value": "#1e40af",
            "sensitivity": ConfigurationSensitivity.PUBLIC,
            "scope": ConfigurationScope.TENANT,
        },
    ]

    existing_defs_res = await db.execute(select(ConfigurationDefinition.key))
    existing_keys = set(existing_defs_res.scalars().all())

    for item in definitions_data:
        if item["key"] not in existing_keys:
            defn = ConfigurationDefinition(
                key=item["key"],
                name=item["name"],
                description=item["description"],
                category=item["category"],
                module=item["module"],
                data_type=item["data_type"],
                default_value=item["default_value"],
                validation_schema=item.get("validation_schema"),
                sensitivity=item["sensitivity"],
                scope=item["scope"],
                is_editable=True,
                is_active=True,
            )
            db.add(defn)

    # 2. Configuration Dependencies (Impact Registry)
    dependencies_data = [
        {
            "key": "attendance.minimum_percentage",
            "module": "attendance.service",
            "component": "attendance_calculator",
            "impact": "Calculates course examination eligibility and triggers low attendance warnings.",
            "criticality": DependencyCriticality.HIGH,
        },
        {
            "key": "attendance.grace_percentage",
            "module": "attendance.service",
            "component": "dispensation_evaluator",
            "impact": "Applies administrative grace margins to borderline attendance cases.",
            "criticality": DependencyCriticality.MEDIUM,
        },
        {
            "key": "finance.invoice.due_days",
            "module": "finance.invoice_service",
            "component": "overdue_processor",
            "impact": "Determines invoice overdue status and calculates late fee penalty schedules.",
            "criticality": DependencyCriticality.HIGH,
        },
        {
            "key": "finance.currency",
            "module": "finance.billing_service",
            "component": "payment_gateway",
            "impact": "Formats monetary amounts across student invoices, receipts, and payment gateways.",
            "criticality": DependencyCriticality.CRITICAL,
        },
        {
            "key": "examination.result.passing_percentage",
            "module": "examination.assessment_service",
            "component": "grading_engine",
            "impact": "Determines student pass/fail outcome for semester courses.",
            "criticality": DependencyCriticality.HIGH,
        },
        {
            "key": "placement.application.max_active_applications",
            "module": "placement.application_service",
            "component": "job_apply_gateway",
            "impact": "Enforces student concurrent job application quotas.",
            "criticality": DependencyCriticality.MEDIUM,
        },
        {
            "key": "documents.default_retention_days",
            "module": "documents.retention_service",
            "component": "lifecycle_archiver",
            "impact": "Automates archival and purge scheduling for uploaded document records.",
            "criticality": DependencyCriticality.MEDIUM,
        },
        {
            "key": "notifications.digest.enabled",
            "module": "campus.notification_service",
            "component": "batch_dispatcher",
            "impact": "Controls batching of non-urgent notifications into daily digests.",
            "criticality": DependencyCriticality.LOW,
        },
    ]

    existing_deps_res = await db.execute(
        select(ConfigurationDependency.configuration_key, ConfigurationDependency.consumer_module)
    )
    existing_deps = {(row[0], row[1]) for row in existing_deps_res.all()}

    for dep in dependencies_data:
        if (dep["key"], dep["module"]) not in existing_deps:
            db.add(
                ConfigurationDependency(
                    configuration_key=dep["key"],
                    consumer_module=dep["module"],
                    consumer_component=dep["component"],
                    impact_description=dep["impact"],
                    criticality=dep["criticality"],
                    is_restart_required=False,
                )
            )

    # 3. If tenant_id supplied, seed default sequences
    if tenant_id:
        standard_sequences = [
            {
                "key": "ADMISSION_NUMBER",
                "name": "Student Admission Number",
                "prefix": "ADM-",
                "pattern": "{PREFIX}{YEAR}-{SEQ}",
                "padding": 5,
                "reset": NumberingResetFrequency.YEARLY,
            },
            {
                "key": "INVOICE_NUMBER",
                "name": "Fee Invoice Number",
                "prefix": "INV-",
                "pattern": "{PREFIX}{YYYY}-{SEQ}",
                "padding": 6,
                "reset": NumberingResetFrequency.YEARLY,
            },
            {
                "key": "RECEIPT_NUMBER",
                "name": "Fee Receipt Number",
                "prefix": "REC-",
                "pattern": "{PREFIX}{YYYY}-{SEQ}",
                "padding": 6,
                "reset": NumberingResetFrequency.YEARLY,
            },
            {
                "key": "CERTIFICATE_NUMBER",
                "name": "Official Certificate Number",
                "prefix": "CERT-",
                "pattern": "{PREFIX}{YEAR}-{SEQ}",
                "padding": 5,
                "reset": NumberingResetFrequency.YEARLY,
            },
            {
                "key": "DOCUMENT_REFERENCE_NUMBER",
                "name": "Document Reference Number",
                "prefix": "DOC-",
                "pattern": "{PREFIX}{YYYY}-{SEQ}",
                "padding": 6,
                "reset": NumberingResetFrequency.NEVER,
            },
        ]
        seq_res = await db.execute(
            select(NumberingSequence.sequence_key).where(NumberingSequence.tenant_id == tenant_id)
        )
        existing_seq_keys = set(seq_res.scalars().all())

        for s in standard_sequences:
            if s["key"] not in existing_seq_keys:
                db.add(
                    NumberingSequence(
                        tenant_id=tenant_id,
                        sequence_key=s["key"],
                        name=s["name"],
                        prefix=s["prefix"],
                        pattern=s["pattern"],
                        padding=s["padding"],
                        reset_frequency=s["reset"],
                        current_val=0,
                        step=1,
                        is_active=True,
                    )
                )

    await db.flush()
    logger.info("Configuration definitions, dependencies, and default sequences initialized.")


async def seed_master_data_defaults(db: AsyncSession, tenant_id: UUID | None = None) -> None:
    """Seed standard master data definitions, reference categories, and quality rules."""
    from app.models.master_data import (
        DataQualityRule,
        MasterDataDefinition,
        MasterDataSensitivity,
        MasterDataType,
        QualityRuleType,
        QualitySeverity,
        ReferenceDataDefinition,
        ReferenceDataValue,
    )

    definitions = [
        {
            "key": MasterDataType.STUDENT,
            "display_name": "Student Master",
            "description": "Canonical student profile and enrollment identity.",
            "owner_domain": "people",
            "steward_role": "STUDENT_ADMINISTRATOR",
            "sensitivity": MasterDataSensitivity.RESTRICTED,
            "duplicate_detection_enabled": True,
            "merge_supported": True,
            "archival_supported": True,
            "authoritative_source": "people_students",
            "canonical_table_name": "people_students",
            "canonical_id_column": "id",
        },
        {
            "key": MasterDataType.FACULTY,
            "display_name": "Faculty Master",
            "description": "Academic faculty profiles and departmental appointments.",
            "owner_domain": "people",
            "steward_role": "FACULTY_ADMINISTRATOR",
            "sensitivity": MasterDataSensitivity.RESTRICTED,
            "duplicate_detection_enabled": False,
            "merge_supported": False,
            "archival_supported": True,
            "authoritative_source": "people_faculty",
            "canonical_table_name": "people_faculty",
            "canonical_id_column": "id",
        },
        {
            "key": MasterDataType.STAFF,
            "display_name": "Staff Master",
            "description": "Administrative and operational staff personnel.",
            "owner_domain": "people",
            "steward_role": "STAFF_ADMINISTRATOR",
            "sensitivity": MasterDataSensitivity.RESTRICTED,
            "duplicate_detection_enabled": False,
            "merge_supported": False,
            "archival_supported": True,
            "authoritative_source": "people_staff",
            "canonical_table_name": "people_staff",
            "canonical_id_column": "id",
        },
        {
            "key": MasterDataType.DEPARTMENT,
            "display_name": "Department Master",
            "description": "Academic and organizational departments.",
            "owner_domain": "academics",
            "steward_role": "ACADEMIC_ADMINISTRATOR",
            "sensitivity": MasterDataSensitivity.INTERNAL,
            "duplicate_detection_enabled": True,
            "merge_supported": True,
            "archival_supported": True,
            "authoritative_source": "core_departments",
            "canonical_table_name": "core_departments",
            "canonical_id_column": "id",
        },
        {
            "key": MasterDataType.PROGRAM,
            "display_name": "Program Master",
            "description": "Academic degree programs and curricula.",
            "owner_domain": "academics",
            "steward_role": "ACADEMIC_ADMINISTRATOR",
            "sensitivity": MasterDataSensitivity.INTERNAL,
            "duplicate_detection_enabled": False,
            "merge_supported": False,
            "archival_supported": True,
            "authoritative_source": "academics_programs",
            "canonical_table_name": "academics_programs",
            "canonical_id_column": "id",
        },
        {
            "key": MasterDataType.COMPANY,
            "display_name": "Placement Company Master",
            "description": "Corporate recruiters and placement industry partners.",
            "owner_domain": "placement",
            "steward_role": "PLACEMENT_OFFICER",
            "sensitivity": MasterDataSensitivity.CONFIDENTIAL,
            "duplicate_detection_enabled": True,
            "merge_supported": True,
            "archival_supported": True,
            "authoritative_source": "placement_companies",
            "canonical_table_name": "placement_companies",
            "canonical_id_column": "id",
        },
        {
            "key": MasterDataType.FEE_CATEGORY,
            "display_name": "Fee Category Master",
            "description": "Institutional fee classification categories.",
            "owner_domain": "finance",
            "steward_role": "FINANCE_ADMINISTRATOR",
            "sensitivity": MasterDataSensitivity.INTERNAL,
            "duplicate_detection_enabled": False,
            "merge_supported": False,
            "archival_supported": True,
            "authoritative_source": "finance_fee_categories",
            "canonical_table_name": "finance_fee_categories",
            "canonical_id_column": "id",
        },
        {
            "key": MasterDataType.DOCUMENT_CATEGORY,
            "display_name": "Document Category Master",
            "description": "Controlled digital document classifications.",
            "owner_domain": "documents",
            "steward_role": "RECORDS_OFFICER",
            "sensitivity": MasterDataSensitivity.INTERNAL,
            "duplicate_detection_enabled": False,
            "merge_supported": False,
            "archival_supported": True,
            "authoritative_source": "document_categories",
            "canonical_table_name": "document_categories",
            "canonical_id_column": "id",
        },
    ]

    existing_defs_res = await db.execute(select(MasterDataDefinition.key))
    existing_keys = set(existing_defs_res.scalars().all())

    for item in definitions:
        if item["key"] not in existing_keys:
            db.add(
                MasterDataDefinition(
                    key=item["key"],
                    display_name=item["display_name"],
                    description=item["description"],
                    owner_domain=item["owner_domain"],
                    steward_role=item["steward_role"],
                    sensitivity=item["sensitivity"],
                    duplicate_detection_enabled=item["duplicate_detection_enabled"],
                    merge_supported=item["merge_supported"],
                    archival_supported=item["archival_supported"],
                    authoritative_source=item["authoritative_source"],
                    canonical_table_name=item["canonical_table_name"],
                    canonical_id_column=item["canonical_id_column"],
                    is_active=True,
                )
            )

    ref_definitions = [
        {
            "category": "PAYMENT_METHOD",
            "name": "Payment Methods",
            "description": "Institutional payment channels accepted for transactions.",
            "is_system": True,
        },
        {
            "category": "GENDER",
            "name": "Gender Classifications",
            "description": "Controlled identity gender categories.",
            "is_system": True,
        },
        {
            "category": "BLOOD_GROUP",
            "name": "Blood Group Types",
            "description": "Medical record blood group values.",
            "is_system": True,
        },
        {
            "category": "ACADEMIC_STATUS",
            "name": "Student Academic Statuses",
            "description": "Standing and progression status classifications.",
            "is_system": True,
        },
    ]

    existing_ref_defs_res = await db.execute(select(ReferenceDataDefinition.category))
    existing_cat_keys = set(existing_ref_defs_res.scalars().all())

    for item in ref_definitions:
        if item["category"] not in existing_cat_keys:
            db.add(
                ReferenceDataDefinition(
                    category=item["category"],
                    name=item["name"],
                    description=item["description"],
                    is_system=item["is_system"],
                    is_active=True,
                )
            )

    if tenant_id:
        standard_ref_values = [
            ("PAYMENT_METHOD", "CASH", "Cash Payment", 1),
            ("PAYMENT_METHOD", "UPI", "Unified Payments Interface (UPI)", 2),
            ("PAYMENT_METHOD", "CARD", "Credit / Debit Card", 3),
            ("PAYMENT_METHOD", "BANK_TRANSFER", "Direct Bank Transfer / NEFT", 4),
            ("PAYMENT_METHOD", "CHEQUE", "Cheque / Demand Draft", 5),
            ("GENDER", "MALE", "Male", 1),
            ("GENDER", "FEMALE", "Female", 2),
            ("GENDER", "OTHER", "Other / Non-Binary", 3),
            ("BLOOD_GROUP", "A_POS", "A+", 1),
            ("BLOOD_GROUP", "A_NEG", "A-", 2),
            ("BLOOD_GROUP", "B_POS", "B+", 3),
            ("BLOOD_GROUP", "B_NEG", "B-", 4),
            ("BLOOD_GROUP", "O_POS", "O+", 5),
            ("BLOOD_GROUP", "O_NEG", "O-", 6),
            ("BLOOD_GROUP", "AB_POS", "AB+", 7),
            ("BLOOD_GROUP", "AB_NEG", "AB-", 8),
            ("ACADEMIC_STATUS", "ACTIVE", "Active Enrolled", 1),
            ("ACADEMIC_STATUS", "GRADUATED", "Graduated", 2),
            ("ACADEMIC_STATUS", "SUSPENDED", "Suspended", 3),
            ("ACADEMIC_STATUS", "WITHDRAWN", "Withdrawn", 4),
        ]

        ref_vals_res = await db.execute(
            select(ReferenceDataValue.category, ReferenceDataValue.code).where(
                ReferenceDataValue.tenant_id == tenant_id
            )
        )
        existing_ref_vals = set(ref_vals_res.all())

        for cat, code, label, order in standard_ref_values:
            if (cat, code) not in existing_ref_vals:
                db.add(
                    ReferenceDataValue(
                        tenant_id=tenant_id,
                        category=cat,
                        code=code,
                        label=label,
                        display_order=order,
                        is_system=True,
                        is_active=True,
                    )
                )

        quality_rules_data = [
            {
                "master_type": MasterDataType.STUDENT,
                "rule_key": "student.email.required",
                "name": "Student Email Required",
                "field_name": "email",
                "rule_type": QualityRuleType.REQUIRED,
                "severity": QualitySeverity.ERROR,
                "weight": 1.0,
            },
            {
                "master_type": MasterDataType.STUDENT,
                "rule_key": "student.admission_number.unique",
                "name": "Student Admission Number Unique",
                "field_name": "admission_number",
                "rule_type": QualityRuleType.UNIQUE,
                "severity": QualitySeverity.CRITICAL,
                "weight": 1.5,
            },
            {
                "master_type": MasterDataType.DEPARTMENT,
                "rule_key": "department.code.unique",
                "name": "Department Code Unique",
                "field_name": "code",
                "rule_type": QualityRuleType.UNIQUE,
                "severity": QualitySeverity.CRITICAL,
                "weight": 1.5,
            },
            {
                "master_type": MasterDataType.DEPARTMENT,
                "rule_key": "department.name.required",
                "name": "Department Name Required",
                "field_name": "name",
                "rule_type": QualityRuleType.REQUIRED,
                "severity": QualitySeverity.ERROR,
                "weight": 1.0,
            },
            {
                "master_type": MasterDataType.COMPANY,
                "rule_key": "company.name.required",
                "name": "Placement Company Name Required",
                "field_name": "name",
                "rule_type": QualityRuleType.REQUIRED,
                "severity": QualitySeverity.ERROR,
                "weight": 1.0,
            },
        ]

        rules_res = await db.execute(
            select(DataQualityRule.rule_key).where(DataQualityRule.tenant_id == tenant_id)
        )
        existing_rule_keys = set(rules_res.scalars().all())

        for r in quality_rules_data:
            if r["rule_key"] not in existing_rule_keys:
                db.add(
                    DataQualityRule(
                        tenant_id=tenant_id,
                        master_type=r["master_type"],
                        rule_key=r["rule_key"],
                        name=r["name"],
                        field_name=r["field_name"],
                        rule_type=r["rule_type"],
                        severity=r["severity"],
                        weight=r["weight"],
                        is_active=True,
                        version=1,
                    )
                )

    await db.flush()
    logger.info("Master data definitions and reference categories initialized successfully.")


async def seed_case_management_defaults(
    db: AsyncSession, tenant_id: UUID | None = None
) -> None:
    """Seed standard case types, work queues, SLA policies, and numbering sequence (Step 25)."""
    from sqlalchemy import or_

    from app.models.case_management import CasePriority, CaseType, SlaPolicy, WorkQueue
    from app.models.configuration import NumberingResetFrequency, NumberingSequence

    logger.info("Initializing standard case management definitions and defaults...")

    case_types_data = [
        {
            "code": "DOCUMENT_VERIFICATION",
            "name": "Student Document Verification",
            "description": "Verification of academic certificates, identity cards, and admissions credentials.",
            "module": "DOCUMENTS",
            "default_priority": CasePriority.NORMAL,
            "sla_hours": 48,
        },
        {
            "code": "FEE_REFUND",
            "name": "Fee Refund & Adjustment Request",
            "description": "Student or sponsor claims for fee refund, balance withdrawal, or scholarship adjustment.",
            "module": "FINANCE",
            "default_priority": CasePriority.HIGH,
            "sla_hours": 24,
        },
        {
            "code": "ATTENDANCE_CORRECTION",
            "name": "Attendance Correction Request",
            "description": "Faculty or student attendance recalculation and leave reconciliation.",
            "module": "ATTENDANCE",
            "default_priority": CasePriority.NORMAL,
            "sla_hours": 48,
        },
        {
            "code": "EXAM_MARK_CORRECTION",
            "name": "Examination Mark Correction / Revaluation",
            "description": "Assessment rechecking, internal assessment updates, or grade corrections.",
            "module": "EXAMINATIONS",
            "default_priority": CasePriority.HIGH,
            "sla_hours": 24,
        },
        {
            "code": "HOSTEL_COMPLAINT",
            "name": "Hostel & Room Maintenance Complaint",
            "description": "Hostel living, plumbing, electrical, or room allocation matters.",
            "module": "HOSTEL",
            "default_priority": CasePriority.NORMAL,
            "sla_hours": 48,
        },
        {
            "code": "FACILITY_ISSUE",
            "name": "Campus Infrastructure & Facility Issue",
            "description": "Campus facilities, classroom projectors, laboratories, and grounds.",
            "module": "FACILITIES",
            "default_priority": CasePriority.NORMAL,
            "sla_hours": 72,
        },
        {
            "code": "PLACEMENT_REVIEW",
            "name": "Placement Eligibility & Offer Review",
            "description": "Corporate drive review, student interview disputes, or job offer verification.",
            "module": "PLACEMENT",
            "default_priority": CasePriority.HIGH,
            "sla_hours": 24,
        },
        {
            "code": "STUDENT_SUPPORT",
            "name": "General Student Support & Grievance",
            "description": "Counseling, welfare, academic guidance, and student support issues.",
            "module": "STUDENTS",
            "default_priority": CasePriority.NORMAL,
            "sla_hours": 48,
        },
        {
            "code": "GENERAL_ADMINISTRATION",
            "name": "General Institutional Operations Case",
            "description": "Cross-departmental administration, staff inquiries, and institutional reviews.",
            "module": "GENERAL",
            "default_priority": CasePriority.NORMAL,
            "sla_hours": 72,
        },
    ]

    existing_types_res = await db.execute(
        select(CaseType.code).where(
            or_(CaseType.tenant_id == tenant_id, CaseType.tenant_id.is_(None))
        )
    )
    existing_type_codes = set(existing_types_res.scalars().all())

    for ct in case_types_data:
        if ct["code"] not in existing_type_codes:
            db.add(
                CaseType(
                    tenant_id=tenant_id,
                    code=ct["code"],
                    name=ct["name"],
                    description=ct["description"],
                    module=ct["module"],
                    default_priority=ct["default_priority"],
                    sla_hours=ct["sla_hours"],
                    requires_decision=True,
                    is_active=True,
                    is_system=True if tenant_id is None else False,
                )
            )

    if tenant_id:
        # Work Queues
        queues_data = [
            ("ADMISSIONS_DESK", "Admissions & Enrollment Desk", "DOCUMENTS"),
            ("FINANCE_REVIEW", "Finance & Billing Review Desk", "FINANCE"),
            ("DOCUMENT_VERIFICATION", "Document Verification Desk", "DOCUMENTS"),
            ("EXAM_CORRECTIONS", "Examination Corrections Desk", "EXAMINATIONS"),
            ("HOSTEL_ADMIN", "Hostel Administration Desk", "HOSTEL"),
            ("PLACEMENT_OPS", "Placement Operations Desk", "PLACEMENT"),
        ]
        q_res = await db.execute(
            select(WorkQueue.key).where(WorkQueue.tenant_id == tenant_id)
        )
        existing_queues = set(q_res.scalars().all())

        for q_key, q_name, q_mod in queues_data:
            if q_key not in existing_queues:
                db.add(
                    WorkQueue(
                        tenant_id=tenant_id,
                        key=q_key,
                        name=q_name,
                        module=q_mod,
                        is_active=True,
                    )
                )

        # Standard SLA Policies
        sla_data = [
            ("URGENT_GENERAL", CasePriority.URGENT, 240),
            ("HIGH_GENERAL", CasePriority.HIGH, 480),
            ("NORMAL_GENERAL", CasePriority.NORMAL, 2880),
            ("LOW_GENERAL", CasePriority.LOW, 4320),
        ]
        sla_res = await db.execute(
            select(SlaPolicy.name).where(SlaPolicy.tenant_id == tenant_id)
        )
        existing_slas = set(sla_res.scalars().all())

        for s_name, s_prio, s_dur in sla_data:
            if s_name not in existing_slas:
                db.add(
                    SlaPolicy(
                        tenant_id=tenant_id,
                        name=s_name,
                        module="GENERAL",
                        priority=s_prio,
                        target_duration_minutes=s_dur,
                        warning_threshold_percentage=75,
                        business_hours_only=True,
                        is_active=True,
                    )
                )

        # Default Case numbering sequence
        seq_res = await db.execute(
            select(NumberingSequence).where(
                NumberingSequence.tenant_id == tenant_id,
                NumberingSequence.sequence_key == "case.number",
            )
        )
        if not seq_res.scalar_one_or_none():
            db.add(
                NumberingSequence(
                    tenant_id=tenant_id,
                    sequence_key="case.number",
                    name="Case Numbering Sequence",
                    prefix="CASE-",
                    pattern="{PREFIX}{YEAR}-{SEQ}",
                    padding=5,
                    current_val=0,
                    step=1,
                    reset_frequency=NumberingResetFrequency.YEARLY,
                    is_active=True,
                )
            )

    await db.flush()
    logger.info("Case management definitions and defaults initialized successfully.")


async def seed_notification_defaults(
    db: AsyncSession, tenant_id: UUID | None = None
) -> None:
    """Seed standard notification templates, versions, and rules idempotently (Step 26)."""
    from sqlalchemy import or_

    from app.models.notification import (
        NotificationChannel,
        NotificationRule,
        NotificationTemplate,
        NotificationTemplateVersion,
        RecipientStrategy,
        TemplateStatus,
    )

    logger.info("Initializing enterprise notification templates and rules defaults...")

    templates_data = [
        {
            "template_key": "attendance.low_threshold",
            "name": "Low Attendance Warning",
            "description": "Triggered when student attendance falls below the minimum required percentage.",
            "channel": NotificationChannel.EMAIL,
            "subject": "Alert: Low Attendance in {{course_code}}",
            "body": "Dear {{student_name}},\n\nYour attendance in {{course_code}} is currently {{attendance_percentage}}%, which is below the required {{threshold_percentage}}% threshold. Please meet your faculty advisor immediately.",
            "variables_schema": {
                "student_name": {"type": "string", "required": True},
                "course_code": {"type": "string", "required": True},
                "attendance_percentage": {"type": "number", "required": True},
                "threshold_percentage": {"type": "number", "required": True},
            },
            "recipient_strategy": RecipientStrategy.STUDENT,
            "priority": "HIGH",
        },
        {
            "template_key": "examination.result.published",
            "name": "Examination Result Published",
            "description": "Triggered when an examination result or grade sheet is published.",
            "channel": NotificationChannel.EMAIL,
            "subject": "Examination Results Published: {{exam_name}}",
            "body": "Dear {{student_name}},\n\nYour examination results for {{exam_name}} (Semester {{semester}}) have been officially published. Your GPA is {{gpa}}.\n\nLog in to your student portal to review the detailed grade breakdown.",
            "variables_schema": {
                "student_name": {"type": "string", "required": True},
                "exam_name": {"type": "string", "required": True},
                "semester": {"type": "string", "required": True},
                "gpa": {"type": "number", "required": True},
            },
            "recipient_strategy": RecipientStrategy.STUDENT,
            "priority": "NORMAL",
        },
        {
            "template_key": "finance.invoice.issued",
            "name": "Fee Invoice Issued",
            "description": "Triggered when a new institutional fee invoice is generated.",
            "channel": NotificationChannel.EMAIL,
            "subject": "Fee Invoice Issued: {{invoice_number}}",
            "body": "Dear {{student_name}},\n\nA new fee invoice {{invoice_number}} for {{amount}} {{currency}} has been issued for your academic account. Due date is {{due_date}}.\n\nPlease complete payment before the due date to prevent late penalties.",
            "variables_schema": {
                "student_name": {"type": "string", "required": True},
                "invoice_number": {"type": "string", "required": True},
                "amount": {"type": "number", "required": True},
                "currency": {"type": "string", "required": True},
                "due_date": {"type": "string", "required": True},
            },
            "recipient_strategy": RecipientStrategy.STUDENT,
            "priority": "HIGH",
        },
        {
            "template_key": "finance.payment.received",
            "name": "Payment Receipt Confirmation",
            "description": "Triggered when fee payment transaction is successfully received.",
            "channel": NotificationChannel.EMAIL,
            "subject": "Payment Receipt: {{receipt_number}}",
            "body": "Dear {{student_name}},\n\nWe have successfully received your payment of {{amount}} {{currency}} for invoice {{invoice_number}}.\nReceipt Number: {{receipt_number}}\nTransaction ID: {{transaction_id}}.",
            "variables_schema": {
                "student_name": {"type": "string", "required": True},
                "receipt_number": {"type": "string", "required": True},
                "amount": {"type": "number", "required": True},
                "currency": {"type": "string", "required": True},
                "invoice_number": {"type": "string", "required": True},
                "transaction_id": {"type": "string", "required": True},
            },
            "recipient_strategy": RecipientStrategy.STUDENT,
            "priority": "NORMAL",
        },
        {
            "template_key": "placement.interview.scheduled",
            "name": "Placement Interview Scheduled",
            "description": "Triggered when an on-campus or virtual corporate interview is scheduled.",
            "channel": NotificationChannel.EMAIL,
            "subject": "Interview Scheduled: {{company_name}} - {{role}}",
            "body": "Dear {{student_name}},\n\nYour interview with {{company_name}} for the position of {{role}} has been scheduled.\nDate/Time: {{interview_date}}\nVenue: {{venue}}\n\nPlease report on time in formal attire.",
            "variables_schema": {
                "student_name": {"type": "string", "required": True},
                "company_name": {"type": "string", "required": True},
                "role": {"type": "string", "required": True},
                "interview_date": {"type": "string", "required": True},
                "venue": {"type": "string", "required": True},
            },
            "recipient_strategy": RecipientStrategy.STUDENT,
            "priority": "HIGH",
        },
        {
            "template_key": "workflow.task.assigned",
            "name": "Workflow Task Assigned",
            "description": "Triggered when a task or case review is assigned to a user or role.",
            "channel": NotificationChannel.EMAIL,
            "subject": "Task Assigned: {{task_title}}",
            "body": "Hello {{assignee_name}},\n\nA new task '{{task_title}}' (Priority: {{priority}}) has been assigned to you.\nDue Date: {{due_date}}\n\nPlease review and action this item in CampusOS.",
            "variables_schema": {
                "assignee_name": {"type": "string", "required": True},
                "task_title": {"type": "string", "required": True},
                "priority": {"type": "string", "required": True},
                "due_date": {"type": "string", "required": True},
            },
            "recipient_strategy": RecipientStrategy.ASSIGNEE,
            "priority": "NORMAL",
        },
        {
            "template_key": "workflow.sla.breached",
            "name": "Workflow SLA Breached Alert",
            "description": "Triggered when a task or case breaches its configured SLA target.",
            "channel": NotificationChannel.EMAIL,
            "subject": "URGENT: SLA Breached - {{case_number}}",
            "body": "Attention: Case {{case_number}} ({{case_title}}) has exceeded its SLA target duration of {{sla_target_hours}} hours.\nAssigned Desk: {{desk_name}}\nCurrent Status: {{status}}\nImmediate action is required.",
            "variables_schema": {
                "case_number": {"type": "string", "required": True},
                "case_title": {"type": "string", "required": True},
                "sla_target_hours": {"type": "number", "required": True},
                "desk_name": {"type": "string", "required": True},
                "status": {"type": "string", "required": True},
            },
            "recipient_strategy": RecipientStrategy.ADMIN,
            "priority": "URGENT",
        },
    ]

    now = datetime.now(UTC)

    # Fetch existing templates
    existing_templates_res = await db.execute(
        select(NotificationTemplate.template_key).where(
            or_(
                NotificationTemplate.tenant_id == tenant_id,
                NotificationTemplate.tenant_id.is_(None),
            )
        )
    )
    existing_keys = set(existing_templates_res.scalars().all())

    for tdata in templates_data:
        tkey = tdata["template_key"]
        if tkey not in existing_keys:
            tmpl_id = uuid4()
            tmpl = NotificationTemplate(
                id=tmpl_id,
                tenant_id=tenant_id,
                template_key=tkey,
                name=tdata["name"],
                description=tdata["description"],
                channel=tdata["channel"],
                status=TemplateStatus.ACTIVE,
                created_at=now,
            )
            db.add(tmpl)

            # Create default published version 1
            ver = NotificationTemplateVersion(
                id=uuid4(),
                tenant_id=tenant_id,
                template_id=tmpl_id,
                version=1,
                status=TemplateStatus.ACTIVE,
                locale="en",
                subject=tdata["subject"],
                body_template=tdata["body"],
                variable_schema_json=tdata["variables_schema"],
                published_at=now,
                created_at=now,
            )
            db.add(ver)

            # Create corresponding default NotificationRule
            rule_key = f"rule.{tkey}"
            rule = NotificationRule(
                id=uuid4(),
                tenant_id=tenant_id,
                rule_key=rule_key,
                name=f"Default Rule: {tdata['name']}",
                description=f"Auto-dispatch notifications for {tkey}",
                event_type=tkey,
                is_enabled=True,
                module_scope=tkey.split(".")[0],
                priority=tdata["priority"],
                recipient_strategy=tdata["recipient_strategy"],
                channels_json=["IN_APP", "EMAIL"],
                template_key=tkey,
                created_at=now,
            )
            db.add(rule)

    await db.flush()
    logger.info("Enterprise notification templates and rules initialized successfully.")

