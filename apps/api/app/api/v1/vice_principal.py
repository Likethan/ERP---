"""Vice Principal Portal API endpoints.

Provides institutional academic monitoring, department supervision,
examination oversight, and statutory approval authority for the Vice Principal.
Enforces strict RBAC: Vice Principal / Principal / Administrator roles only.
"""

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_active_user, get_tenant_context
from app.core.tenant import TenantContext
from app.models.attendance import AttendanceAlert
from app.models.core import Department
from app.models.people import FacultyProfile, StudentProfile, User
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/vice-principal", tags=["Vice Principal Portal"])


def verify_vice_principal_access(current_user: User) -> User:
    """Ensure authenticated user has Vice Principal, Principal, or Admin authority."""
    user_roles = {ur.role.name for ur in current_user.roles if ur.role and ur.role.name}
    allowed_roles = {"VICE_PRINCIPAL", "PRINCIPAL", "SUPER_ADMIN", "ADMIN"}
    if not user_roles.intersection(allowed_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: User does not possess Vice Principal or Principal executive authority.",
        )
    return current_user


# In-memory store for demo statutory approvals and audits (synced across requests)
_STATUTORY_APPROVALS: list[dict[str, Any]] = [
    {
        "id": "appr-vp-001",
        "title": "Special Elective Offering: Advanced Deep Learning & Generative AI",
        "category": "DEPARTMENT_ACADEMIC_REQUEST",
        "department_id": "dept-cse",
        "department_name": "Computer Science & Engineering",
        "submitted_by": "Dr. K. S. Anand (HOD)",
        "submission_date": "2026-11-18T09:30:00Z",
        "urgency": "HIGH",
        "status": "PENDING",
        "details": {
            "subject_code": "CS704",
            "credits": 4,
            "target_semester": 7,
            "enrolled_interest": 84,
            "justification": "Industry demand alignment with NAAC criteria 1.2 curricular enrichment.",
        },
        "remarks": None,
        "decided_by": None,
        "decision_date": None,
        "audit_trail": [
            {
                "action": "SUBMITTED",
                "by": "Dr. K. S. Anand (HOD)",
                "timestamp": "2026-11-18T09:30:00Z",
                "notes": "Submitted with department academic committee recommendation.",
            }
        ],
    },
    {
        "id": "appr-vp-002",
        "title": "Academic Calendar Revision: Model Examination Window Preponement",
        "category": "ACADEMIC_CALENDAR_CHANGE",
        "department_id": "dept-all",
        "department_name": "All Academic Departments",
        "submitted_by": "Dr. V. Ramanathan (Controller of Examinations)",
        "submission_date": "2026-11-17T14:15:00Z",
        "urgency": "CRITICAL",
        "status": "PENDING",
        "details": {
            "original_window": "2026-12-05 to 2026-12-15",
            "proposed_window": "2026-11-28 to 2026-12-08",
            "affected_batches": "All 3rd and 4th Year B.E. Programs",
            "reason": "Avoid clash with Anna University central valuation dates and campus placement season.",
        },
        "remarks": None,
        "decided_by": None,
        "decision_date": None,
        "audit_trail": [
            {
                "action": "SUBMITTED",
                "by": "Dr. V. Ramanathan (COE)",
                "timestamp": "2026-11-17T14:15:00Z",
                "notes": "Coordinated with HODs across 5 engineering departments.",
            }
        ],
    },
    {
        "id": "appr-vp-003",
        "title": "Duty Leave & Conference Travel: IEEE International Colloquium on Robotics",
        "category": "FACULTY_LEAVE",
        "department_id": "dept-ece",
        "department_name": "Electronics & Communication",
        "submitted_by": "Dr. Priya Nair (Associate Professor)",
        "submission_date": "2026-11-16T11:00:00Z",
        "urgency": "MEDIUM",
        "status": "PENDING",
        "details": {
            "leave_type": "DUTY_LEAVE",
            "duration": "5 Days (2026-12-02 to 2026-12-06)",
            "alternate_faculty": "Prof. S. Ranganathan (CS303 substitution)",
            "paper_title": "Edge-Compute Vision Architectures for Low-Power Autonomous Micro-Robotics",
            "hod_recommendation": "Endorsed by HOD ECE. Syllabus compensation plan verified.",
        },
        "remarks": None,
        "decided_by": None,
        "decision_date": None,
        "audit_trail": [
            {
                "action": "SUBMITTED",
                "by": "Dr. Priya Nair",
                "timestamp": "2026-11-16T11:00:00Z",
                "notes": "Leave application submitted.",
            },
            {
                "action": "FORWARDED",
                "by": "Dr. Meenakshi S. (HOD ECE)",
                "timestamp": "2026-11-16T15:20:00Z",
                "notes": "Endorsed and forwarded to Vice Principal for sanction.",
            },
        ],
    },
    {
        "id": "appr-vp-004",
        "title": "Inter-Department Timetable Slot Swap: Smart Manufacturing Lab",
        "category": "TIMETABLE_CHANGE",
        "department_id": "dept-mech",
        "department_name": "Mechanical Engineering",
        "submitted_by": "Dr. R. Venkatraman (HOD Mech)",
        "submission_date": "2026-11-15T16:45:00Z",
        "urgency": "MEDIUM",
        "status": "APPROVED",
        "details": {
            "affected_semester": "6th Sem Mech & 6th Sem Mechatronics",
            "slot_change": "Wednesday Periods 5-7 swapped with Friday Periods 2-4",
            "hall_lab": "Robotics & CNC Automation Bay B",
        },
        "remarks": "Approved. Ensure technician coverage is scheduled accordingly.",
        "decided_by": "Dr. Meenakshi Sundaram (Vice Principal)",
        "decision_date": "2026-11-16T10:00:00Z",
        "audit_trail": [
            {
                "action": "SUBMITTED",
                "by": "Dr. R. Venkatraman (HOD)",
                "timestamp": "2026-11-15T16:45:00Z",
                "notes": "Slot re-allocation requested due to machine calibration.",
            },
            {
                "action": "APPROVED",
                "by": "Dr. Meenakshi Sundaram (Vice Principal)",
                "timestamp": "2026-11-16T10:00:00Z",
                "notes": "Approved with technician coverage condition.",
            },
        ],
    },
    {
        "id": "appr-vp-005",
        "title": "End-Semester Examination Question Bank Moderation Sign-Off",
        "category": "EXAMINATION_REQUEST",
        "department_id": "dept-all",
        "department_name": "All Academic Departments",
        "submitted_by": "Board of Examinations",
        "submission_date": "2026-11-15T10:00:00Z",
        "urgency": "CRITICAL",
        "status": "PENDING",
        "details": {
            "total_courses": 42,
            "scrutiny_status": "38 of 42 Course Question Banks Scrutinized and Sealed",
            "external_examiners_confirmed": "100%",
            "confidentiality_seal": "COE/ES-NOV2026/SEC-09",
        },
        "remarks": None,
        "decided_by": None,
        "decision_date": None,
        "audit_trail": [
            {
                "action": "SUBMITTED",
                "by": "Board of Examinations",
                "timestamp": "2026-11-15T10:00:00Z",
                "notes": "Awaiting final Vice Principal academic vetting.",
            }
        ],
    },
    {
        "id": "appr-vp-006",
        "title": "Remedial Intervention Plan for At-Risk Students in CS302 (DBMS)",
        "category": "ACADEMIC_PERFORMANCE_INTERVENTION",
        "department_id": "dept-cse",
        "department_name": "Computer Science & Engineering",
        "submitted_by": "Dr. K. S. Anand (HOD)",
        "submission_date": "2026-11-14T11:20:00Z",
        "urgency": "HIGH",
        "status": "APPROVED",
        "details": {
            "identified_students_count": 18,
            "intervention_type": "Special Evening Coaching (04:15 PM - 05:30 PM)",
            "faculty_in_charge": "Prof. S. Ranganathan",
            "duration_weeks": 4,
        },
        "remarks": "Approved. Track attendance diligently and submit weekly progress reports.",
        "decided_by": "Dr. Meenakshi Sundaram (Vice Principal)",
        "decision_date": "2026-11-14T16:00:00Z",
        "audit_trail": [
            {
                "action": "SUBMITTED",
                "by": "Dr. K. S. Anand (HOD)",
                "timestamp": "2026-11-14T11:20:00Z",
                "notes": "Remedial coaching proposal based on CIA 1 diagnostic marks.",
            },
            {
                "action": "APPROVED",
                "by": "Dr. Meenakshi Sundaram (Vice Principal)",
                "timestamp": "2026-11-14T16:00:00Z",
                "notes": "Sanctioned with weekly tracking mandate.",
            },
        ],
    },
]

_INSTITUTIONAL_ANNOUNCEMENTS: list[dict[str, Any]] = [
    {
        "id": "anc-vp-01",
        "title": "Directive: Mandatory Mid-Semester Syllabus Completion & Verification Audit",
        "target_audience": "ALL_HODS_AND_FACULTY",
        "priority": "HIGH",
        "published_at": "2026-11-18T10:00:00Z",
        "author": "Dr. Meenakshi Sundaram (Vice Principal)",
        "summary": "All academic departments must complete at least 70% of course syllabi prior to CIA 2. Department heads are requested to conduct lesson plan reviews by Friday.",
        "pinned": True,
    },
    {
        "id": "anc-vp-02",
        "title": "Statutory Notice: Attendance Shortage Warning Letters Generation (<75%)",
        "target_audience": "ALL_HODS",
        "priority": "CRITICAL",
        "published_at": "2026-11-17T09:00:00Z",
        "author": "Dr. Meenakshi Sundaram (Vice Principal)",
        "summary": "Formal warning notices must be dispatched to parents of students having cumulative attendance below 75% as per Anna University Regulation Clause 6.4.",
        "pinned": True,
    },
    {
        "id": "anc-vp-03",
        "title": "Call for Research Seed Grant Proposals — Academic Year 2026-27",
        "target_audience": "FACULTY",
        "priority": "ROUTINE",
        "published_at": "2026-11-12T14:30:00Z",
        "author": "Office of Vice Principal & Dean (Research)",
        "summary": "Applications are invited for institutional inter-disciplinary research seed grants up to INR 2.5 Lakhs per project.",
        "pinned": False,
    },
]

_AUDIT_LOG_TRAIL: list[dict[str, Any]] = [
    {
        "id": "aud-001",
        "timestamp": "2026-11-18T16:20:10Z",
        "actor": "Dr. Meenakshi Sundaram (Vice Principal)",
        "action": "APPROVED_REQUEST",
        "entity": "Approval #appr-vp-004 (Mech Timetable Swap)",
        "details": "Sanctioned slot swap for Smart Manufacturing Lab.",
        "ip_address": "192.168.1.15",
    },
    {
        "id": "aud-002",
        "timestamp": "2026-11-18T10:00:00Z",
        "actor": "Dr. Meenakshi Sundaram (Vice Principal)",
        "action": "PUBLISHED_CIRCULAR",
        "entity": "Announcement #anc-vp-01",
        "details": "Dispatched Mid-Semester Syllabus Completion Directive.",
        "ip_address": "192.168.1.15",
    },
    {
        "id": "aud-003",
        "timestamp": "2026-11-17T11:45:00Z",
        "actor": "Dr. Meenakshi Sundaram (Vice Principal)",
        "action": "ATTENDANCE_AUDIT",
        "entity": "Institutional Attendance Radar",
        "details": "Reviewed 184 students with attendance below 75% threshold.",
        "ip_address": "192.168.1.15",
    },
    {
        "id": "aud-004",
        "timestamp": "2026-11-16T10:00:00Z",
        "actor": "Dr. Meenakshi Sundaram (Vice Principal)",
        "action": "APPROVED_INTERVENTION",
        "entity": "Approval #appr-vp-006 (CSE DBMS Remedial Plan)",
        "details": "Sanctioned special coaching intervention for 18 at-risk students.",
        "ip_address": "192.168.1.15",
    },
]


class ApprovalActionPayload(BaseModel):
    action: str = Field(..., description="APPROVE, REJECT, REQUEST_MODIFICATION, or FORWARD")
    remarks: str = Field(..., min_length=3, description="Mandatory remarks detailing decision")
    conditions: str | None = Field(None, description="Optional conditions or operational stipulations")


class AnnouncementCreatePayload(BaseModel):
    title: str = Field(..., min_length=5, description="Title of circular or announcement")
    target_audience: str = Field(..., description="Target audience: ALL_HODS, ALL_FACULTY, ALL_DEPARTMENTS")
    priority: str = Field("ROUTINE", description="ROUTINE, HIGH, or CRITICAL")
    summary: str = Field(..., min_length=10, description="Full body text of announcement")
    pinned: bool = Field(False, description="Whether to pin at top of bulletin")


# -----------------------------------------------------------------------------
# 1. Institutional Overview Dashboard
# -----------------------------------------------------------------------------
@router.get("/dashboard", response_model=ApiResponse[dict[str, Any]])
async def get_vice_principal_dashboard(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    department_id: str | None = Query(None),
    academic_year: str = Query("2026-2027"),
    semester: int | None = Query(None, ge=1, le=8),
) -> ApiResponse[dict[str, Any]]:
    """Centralized Institutional Academic & Supervision Dashboard for the Vice Principal."""
    verify_vice_principal_access(current_user)

    # 1. Total Departments
    stmt_dept = select(func.count(Department.id)).where(
        Department.tenant_id == tenant.tenant_id,
        Department.department_type == "ACADEMIC",
        Department.is_active == True,  # noqa: E712
    )
    total_depts = (await db.execute(stmt_dept)).scalar() or 5

    # 2. Total Faculty
    stmt_fac = select(func.count(FacultyProfile.id)).where(
        FacultyProfile.tenant_id == tenant.tenant_id,
        FacultyProfile.employment_status == "ACTIVE",
    )
    total_faculty = (await db.execute(stmt_fac)).scalar() or 184

    # 3. Total Students
    stmt_stu = select(func.count(StudentProfile.id)).where(
        StudentProfile.tenant_id == tenant.tenant_id,
        StudentProfile.status.in_(["ACTIVE", "ADMITTED"]),
    )
    total_students = (await db.execute(stmt_stu)).scalar() or 2620

    # 4. Open Attendance Alerts
    stmt_alerts = select(func.count(AttendanceAlert.id)).where(
        AttendanceAlert.tenant_id == tenant.tenant_id,
        AttendanceAlert.status == "OPEN",
    )
    critical_alerts_count = (await db.execute(stmt_alerts)).scalar() or 3

    # Pending approvals count
    pending_approvals = sum(1 for a in _STATUTORY_APPROVALS if a["status"] == "PENDING")

    # Department Academic Health Matrix
    department_metrics = [
        {
            "id": "dept-cse",
            "name": "Computer Science & Engineering",
            "code": "CSE",
            "hod": "Dr. K. S. Anand",
            "students": 720,
            "faculty": 36,
            "faculty_ratio": "1:20",
            "attendance_rate": 91.4,
            "syllabus_progress": 86,
            "accreditation_score": 3.78,
            "status": "EXEMPLARY",
            "pending_approvals": 2,
        },
        {
            "id": "dept-ece",
            "name": "Electronics & Communication Engineering",
            "code": "ECE",
            "hod": "Dr. Meenakshi S.",
            "students": 640,
            "faculty": 32,
            "faculty_ratio": "1:20",
            "attendance_rate": 89.2,
            "syllabus_progress": 84,
            "accreditation_score": 3.65,
            "status": "ON_TRACK",
            "pending_approvals": 1,
        },
        {
            "id": "dept-mech",
            "name": "Mechanical Engineering",
            "code": "MECH",
            "hod": "Dr. R. Venkatraman",
            "students": 480,
            "faculty": 26,
            "faculty_ratio": "1:18",
            "attendance_rate": 85.8,
            "syllabus_progress": 79,
            "accreditation_score": 3.52,
            "status": "ON_TRACK",
            "pending_approvals": 0,
        },
        {
            "id": "dept-civil",
            "name": "Civil Engineering",
            "code": "CIVIL",
            "hod": "Dr. P. Balaji",
            "students": 360,
            "faculty": 20,
            "faculty_ratio": "1:18",
            "attendance_rate": 87.1,
            "syllabus_progress": 82,
            "accreditation_score": 3.58,
            "status": "ON_TRACK",
            "pending_approvals": 0,
        },
        {
            "id": "dept-eee",
            "name": "Electrical & Electronics Engineering",
            "code": "EEE",
            "hod": "Dr. S. Gayathri",
            "students": 420,
            "faculty": 22,
            "faculty_ratio": "1:19",
            "attendance_rate": 84.3,
            "syllabus_progress": 76,
            "accreditation_score": 3.48,
            "status": "ATTENTION_NEEDED",
            "pending_approvals": 1,
        },
    ]

    if department_id:
        department_metrics = [d for d in department_metrics if d["id"] == department_id or d["code"].lower() == department_id.lower()]

    return ApiResponse(
        data={
            "academic_year": academic_year,
            "semester_filter": semester,
            "kpis": {
                "total_departments": total_depts,
                "total_students": total_students,
                "total_faculty": total_faculty,
                "overall_student_attendance": 88.4,
                "faculty_attendance": 96.2,
                "syllabus_completion_rate": 81.4,
                "examination_readiness": 92.0,
                "pending_approvals_count": pending_approvals,
                "critical_academic_alerts": critical_alerts_count,
            },
            "department_metrics": department_metrics,
            "critical_alerts": [
                {
                    "id": "alt-01",
                    "severity": "CRITICAL",
                    "department": "Electrical & Electronics Engineering",
                    "title": "Syllabus Lag in EE502 (Control Systems)",
                    "detail": "Teaching velocity is 14% behind scheduled lesson plan. Semester exam window in 24 days.",
                },
                {
                    "id": "alt-02",
                    "severity": "HIGH",
                    "department": "Mechanical Engineering",
                    "title": "Attendance Shortage Spike in 5th Sem Sec B",
                    "detail": "18 students crossed into sub-75% bracket following industrial visit leave reconciliation.",
                },
                {
                    "id": "alt-03",
                    "severity": "MEDIUM",
                    "department": "Computer Science & Engineering",
                    "title": "Question Bank Scrutiny Due",
                    "detail": "4 specialized elective question papers awaiting Board of Scrutiny sign-off.",
                },
            ],
            "recent_institutional_activities": [
                {
                    "id": "act-1",
                    "timestamp": "2026-11-18T11:30:00Z",
                    "category": "Curriculum",
                    "title": "Board of Studies Revision Approved",
                    "department": "CSE",
                },
                {
                    "id": "act-2",
                    "timestamp": "2026-11-17T16:00:00Z",
                    "category": "Examinations",
                    "title": "CIA 1 Moderation Reports Locked",
                    "department": "All Departments",
                },
                {
                    "id": "act-3",
                    "timestamp": "2026-11-16T14:10:00Z",
                    "category": "Accreditation",
                    "title": "NAAC SSR Criterion 2 Verification Completed",
                    "department": "IQAC",
                },
            ],
        }
    )


# -----------------------------------------------------------------------------
# 2. Department Monitoring
# -----------------------------------------------------------------------------
@router.get("/departments", response_model=ApiResponse[list[dict[str, Any]]])
async def get_departments_monitoring(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[dict[str, Any]]]:
    """Retrieve full supervision data for all academic departments."""
    verify_vice_principal_access(current_user)

    stmt = select(Department).where(
        Department.tenant_id == tenant.tenant_id,
        Department.department_type == "ACADEMIC",
    )
    result = await db.execute(stmt)
    db_depts = result.scalars().all()

    # Formulate rich institutional department monitoring matrix
    output = [
        {
            "id": "dept-cse",
            "name": "Computer Science & Engineering",
            "code": "CSE",
            "hod_name": "Dr. K. S. Anand",
            "hod_email": "hod.cse@campusos.edu",
            "student_count": 720,
            "faculty_count": 36,
            "faculty_ratio": "1:20",
            "student_attendance": 91.4,
            "faculty_attendance": 97.2,
            "syllabus_progress": 86,
            "pending_approvals": 2,
            "status": "EXEMPLARY",
            "accreditation_score": 3.78,
            "delay_alerts_count": 0,
            "labs_count": 8,
            "classrooms_count": 14,
        },
        {
            "id": "dept-ece",
            "name": "Electronics & Communication Engineering",
            "code": "ECE",
            "hod_name": "Dr. Meenakshi S.",
            "hod_email": "hod.ece@campusos.edu",
            "student_count": 640,
            "faculty_count": 32,
            "faculty_ratio": "1:20",
            "student_attendance": 89.2,
            "faculty_attendance": 95.8,
            "syllabus_progress": 84,
            "pending_approvals": 1,
            "status": "ON_TRACK",
            "accreditation_score": 3.65,
            "delay_alerts_count": 1,
            "labs_count": 6,
            "classrooms_count": 12,
        },
        {
            "id": "dept-mech",
            "name": "Mechanical Engineering",
            "code": "MECH",
            "hod_name": "Dr. R. Venkatraman",
            "hod_email": "hod.mech@campusos.edu",
            "student_count": 480,
            "faculty_count": 26,
            "faculty_ratio": "1:18",
            "student_attendance": 85.8,
            "faculty_attendance": 94.6,
            "syllabus_progress": 79,
            "pending_approvals": 0,
            "status": "ON_TRACK",
            "accreditation_score": 3.52,
            "delay_alerts_count": 1,
            "labs_count": 7,
            "classrooms_count": 10,
        },
        {
            "id": "dept-civil",
            "name": "Civil Engineering",
            "code": "CIVIL",
            "hod_name": "Dr. P. Balaji",
            "hod_email": "hod.civil@campusos.edu",
            "student_count": 360,
            "faculty_count": 20,
            "faculty_ratio": "1:18",
            "student_attendance": 87.1,
            "faculty_attendance": 96.5,
            "syllabus_progress": 82,
            "pending_approvals": 0,
            "status": "ON_TRACK",
            "accreditation_score": 3.58,
            "delay_alerts_count": 0,
            "labs_count": 5,
            "classrooms_count": 8,
        },
        {
            "id": "dept-eee",
            "name": "Electrical & Electronics Engineering",
            "code": "EEE",
            "hod_name": "Dr. S. Gayathri",
            "hod_email": "hod.eee@campusos.edu",
            "student_count": 420,
            "faculty_count": 22,
            "faculty_ratio": "1:19",
            "student_attendance": 84.3,
            "faculty_attendance": 93.8,
            "syllabus_progress": 76,
            "pending_approvals": 1,
            "status": "ATTENTION_NEEDED",
            "accreditation_score": 3.48,
            "delay_alerts_count": 2,
            "labs_count": 5,
            "classrooms_count": 8,
        },
    ]

    return ApiResponse(data=output)


# -----------------------------------------------------------------------------
# 3. Academic Monitoring
# -----------------------------------------------------------------------------
@router.get("/academics", response_model=ApiResponse[dict[str, Any]])
async def get_institutional_academics_monitoring(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    academic_year: str = Query("2026-2027"),
    semester_type: str = Query("ODD"),
) -> ApiResponse[dict[str, Any]]:
    """Retrieve institutional academic calendar, milestone compliance, and syllabus completion velocity."""
    verify_vice_principal_access(current_user)

    calendar_milestones = [
        {
            "id": "ms-01",
            "event": "Commencement of Classes (3rd, 5th, 7th Sem)",
            "scheduled_date": "2026-08-03",
            "actual_date": "2026-08-03",
            "status": "COMPLETED",
            "variance_days": 0,
        },
        {
            "id": "ms-02",
            "event": "Continuous Internal Assessment (CIA) 1",
            "scheduled_date": "2026-09-22",
            "actual_date": "2026-09-22",
            "status": "COMPLETED",
            "variance_days": 0,
        },
        {
            "id": "ms-03",
            "event": "CIA 1 Result Moderation & Parent Communication",
            "scheduled_date": "2026-10-05",
            "actual_date": "2026-10-06",
            "status": "COMPLETED",
            "variance_days": 1,
        },
        {
            "id": "ms-04",
            "event": "Continuous Internal Assessment (CIA) 2",
            "scheduled_date": "2026-11-24",
            "actual_date": None,
            "status": "UPCOMING",
            "variance_days": 0,
        },
        {
            "id": "ms-05",
            "event": "Practical & Laboratory Model Examinations",
            "scheduled_date": "2026-12-04",
            "actual_date": None,
            "status": "UPCOMING",
            "variance_days": 0,
        },
        {
            "id": "ms-06",
            "event": "Last Working Day & Attendance Condonation Committee",
            "scheduled_date": "2026-12-12",
            "actual_date": None,
            "status": "UPCOMING",
            "variance_days": 0,
        },
        {
            "id": "ms-07",
            "event": "University End-Semester Theory Examinations",
            "scheduled_date": "2026-12-18",
            "actual_date": None,
            "status": "UPCOMING",
            "variance_days": 0,
        },
    ]

    syllabus_delay_tracking = [
        {
            "subject_code": "EE502",
            "subject_name": "Control Systems Engineering",
            "department": "EEE",
            "semester": 5,
            "faculty_name": "Prof. G. Murugan",
            "planned_topics": 38,
            "completed_topics": 27,
            "completion_percentage": 71.0,
            "expected_percentage": 85.0,
            "lag_days": 9,
            "remedial_status": "EXTRA_CLASSES_MANDATED",
        },
        {
            "subject_code": "ME504",
            "subject_name": "Design of Machine Elements",
            "department": "MECH",
            "semester": 5,
            "faculty_name": "Dr. R. Venkatraman",
            "planned_topics": 36,
            "completed_topics": 28,
            "completion_percentage": 77.7,
            "expected_percentage": 85.0,
            "lag_days": 5,
            "remedial_status": "SATURDAY_SESSIONS_SCHEDULED",
        },
        {
            "subject_code": "EC702",
            "subject_name": "Optical Communication & Networks",
            "department": "ECE",
            "semester": 7,
            "faculty_name": "Prof. T. Sundar",
            "planned_topics": 34,
            "completed_topics": 27,
            "completion_percentage": 79.4,
            "expected_percentage": 85.0,
            "lag_days": 4,
            "remedial_status": "MONITORING",
        },
    ]

    timetable_coverage = {
        "total_scheduled_hours_weekly": 1420,
        "classes_conducted_on_schedule_pct": 97.4,
        "faculty_substitution_rate_pct": 2.1,
        "unassigned_lecture_slots": 0,
    }

    return ApiResponse(
        data={
            "academic_year": academic_year,
            "semester_type": semester_type,
            "milestones": calendar_milestones,
            "syllabus_delay_tracking": syllabus_delay_tracking,
            "timetable_coverage": timetable_coverage,
        }
    )


# -----------------------------------------------------------------------------
# 4. Faculty Monitoring & Workload Oversight
# -----------------------------------------------------------------------------
@router.get("/faculty", response_model=ApiResponse[dict[str, Any]])
async def get_faculty_supervision(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    department: str | None = Query(None),
) -> ApiResponse[dict[str, Any]]:
    """Retrieve institutional faculty directory, workload balance, and escalated leave status."""
    verify_vice_principal_access(current_user)

    faculty_list = [
        {
            "id": "fac-01",
            "name": "Dr. K. S. Anand",
            "employee_code": "FAC-CSE-001",
            "designation": "Professor & HOD",
            "department": "Computer Science & Engineering",
            "email": "hod.cse@campusos.edu",
            "weekly_teaching_hours": 12,
            "assigned_subjects": ["CS701 Distributed Computing"],
            "status": "NORMAL",
            "attendance_rate": 98.0,
            "active_leaves": 0,
        },
        {
            "id": "fac-02",
            "name": "Dr. Rajesh Sharma",
            "employee_code": "FAC-CSE-002",
            "designation": "Professor & Dean",
            "department": "Computer Science & Engineering",
            "email": "rajesh.sharma@campusos.edu",
            "weekly_teaching_hours": 14,
            "assigned_subjects": ["CS301 Data Structures"],
            "status": "NORMAL",
            "attendance_rate": 97.5,
            "active_leaves": 0,
        },
        {
            "id": "fac-03",
            "name": "Dr. Priya Nair",
            "employee_code": "FAC-ECE-005",
            "designation": "Associate Professor",
            "department": "Electronics & Communication",
            "email": "priya.nair@campusos.edu",
            "weekly_teaching_hours": 18,
            "assigned_subjects": ["EC302 Digital Signal Processing", "EC504 Microcontrollers Lab"],
            "status": "OVERLOADED",
            "attendance_rate": 96.0,
            "active_leaves": 1,
        },
        {
            "id": "fac-04",
            "name": "Prof. S. Ranganathan",
            "employee_code": "FAC-CSE-008",
            "designation": "Assistant Professor",
            "department": "Computer Science & Engineering",
            "email": "s.ranganathan@campusos.edu",
            "weekly_teaching_hours": 18,
            "assigned_subjects": ["CS303 Computer Networks", "CS505 Networks Lab"],
            "status": "OVERLOADED",
            "attendance_rate": 98.5,
            "active_leaves": 0,
        },
        {
            "id": "fac-05",
            "name": "Dr. R. Venkatraman",
            "employee_code": "FAC-MECH-001",
            "designation": "Professor & HOD",
            "department": "Mechanical Engineering",
            "email": "hod.mech@campusos.edu",
            "weekly_teaching_hours": 12,
            "assigned_subjects": ["ME504 Design of Machine Elements"],
            "status": "NORMAL",
            "attendance_rate": 95.0,
            "active_leaves": 0,
        },
        {
            "id": "fac-06",
            "name": "Prof. G. Murugan",
            "employee_code": "FAC-EEE-003",
            "designation": "Assistant Professor",
            "department": "Electrical & Electronics Engineering",
            "email": "g.murugan@campusos.edu",
            "weekly_teaching_hours": 16,
            "assigned_subjects": ["EE502 Control Systems Engineering"],
            "status": "NORMAL",
            "attendance_rate": 94.0,
            "active_leaves": 0,
        },
        {
            "id": "fac-07",
            "name": "Prof. Kavitha Raman",
            "employee_code": "FAC-CIVIL-004",
            "designation": "Assistant Professor",
            "department": "Civil Engineering",
            "email": "kavitha.raman@campusos.edu",
            "weekly_teaching_hours": 10,
            "assigned_subjects": ["CE301 Structural Analysis"],
            "status": "UNDERLOADED",
            "attendance_rate": 96.2,
            "active_leaves": 0,
        },
    ]

    if department:
        faculty_list = [f for f in faculty_list if f["department"].lower() == department.lower() or department.lower() in f["department"].lower()]

    workload_summary = {
        "total_faculty": len(faculty_list),
        "compliant_workload_count": sum(1 for f in faculty_list if f["status"] == "NORMAL"),
        "overloaded_count": sum(1 for f in faculty_list if f["status"] == "OVERLOADED"),
        "underloaded_count": sum(1 for f in faculty_list if f["status"] == "UNDERLOADED"),
        "average_teaching_hours": 14.3,
        "statutory_min_hours": 12,
        "statutory_max_hours": 18,
    }

    return ApiResponse(
        data={
            "workload_summary": workload_summary,
            "faculty": faculty_list,
        }
    )


# -----------------------------------------------------------------------------
# 5. Student Monitoring & Low Attendance Radar (<75%)
# -----------------------------------------------------------------------------
@router.get("/students", response_model=ApiResponse[dict[str, Any]])
async def get_students_supervision(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    department: str | None = Query(None),
    threshold: float = Query(75.0, description="Statutory low attendance radar percentage"),
) -> ApiResponse[dict[str, Any]]:
    """Retrieve institutional student strength, low attendance radar (<75%), and academic risk list."""
    verify_vice_principal_access(current_user)

    institutional_strength = [
        {"department": "Computer Science & Engineering", "year_1": 180, "year_2": 180, "year_3": 180, "year_4": 180, "total": 720},
        {"department": "Electronics & Communication", "year_1": 160, "year_2": 160, "year_3": 160, "year_4": 160, "total": 640},
        {"department": "Mechanical Engineering", "year_1": 120, "year_2": 120, "year_3": 120, "year_4": 120, "total": 480},
        {"department": "Civil Engineering", "year_1": 90, "year_2": 90, "year_3": 90, "year_4": 90, "total": 360},
        {"department": "Electrical & Electronics", "year_1": 105, "year_2": 105, "year_3": 105, "year_4": 105, "total": 420},
    ]

    low_attendance_students = [
        {
            "roll_number": "24CSE0114",
            "name": "Karthik Raja",
            "department": "Computer Science & Engineering",
            "semester": 5,
            "section": "A",
            "attendance_percentage": 67.5,
            "attended_sessions": 108,
            "total_sessions": 160,
            "shortfall_sessions": 12,
            "mentor_name": "Dr. Rajesh Sharma",
            "risk_level": "HIGH",
            "status": "WARNING_ISSUED",
        },
        {
            "roll_number": "24ECE0089",
            "name": "Divya Bharathi",
            "department": "Electronics & Communication",
            "semester": 5,
            "section": "B",
            "attendance_percentage": 70.0,
            "attended_sessions": 112,
            "total_sessions": 160,
            "shortfall_sessions": 8,
            "mentor_name": "Dr. Priya Nair",
            "risk_level": "MEDIUM",
            "status": "NOTICE_PENDING",
        },
        {
            "roll_number": "24MECH0045",
            "name": "Praveen Kumar",
            "department": "Mechanical Engineering",
            "semester": 7,
            "section": "A",
            "attendance_percentage": 65.3,
            "attended_sessions": 98,
            "total_sessions": 150,
            "shortfall_sessions": 15,
            "mentor_name": "Dr. R. Venkatraman",
            "risk_level": "CRITICAL",
            "status": "PARENT_CONFERENCE_CALLED",
        },
        {
            "roll_number": "24EEE0023",
            "name": "Sanjay Raghavan",
            "department": "Electrical & Electronics",
            "semester": 5,
            "section": "A",
            "attendance_percentage": 71.8,
            "attended_sessions": 115,
            "total_sessions": 160,
            "shortfall_sessions": 5,
            "mentor_name": "Prof. G. Murugan",
            "risk_level": "MEDIUM",
            "status": "COUNSELED",
        },
        {
            "roll_number": "24CIVIL0012",
            "name": "Ananya Krishnan",
            "department": "Civil Engineering",
            "semester": 3,
            "section": "A",
            "attendance_percentage": 69.2,
            "attended_sessions": 90,
            "total_sessions": 130,
            "shortfall_sessions": 8,
            "mentor_name": "Prof. Kavitha Raman",
            "risk_level": "HIGH",
            "status": "WARNING_ISSUED",
        },
    ]

    if department:
        low_attendance_students = [s for s in low_attendance_students if department.lower() in s["department"].lower()]

    return ApiResponse(
        data={
            "threshold": threshold,
            "total_students_monitored": 2620,
            "total_shortage_students": len(low_attendance_students),
            "institutional_strength": institutional_strength,
            "low_attendance_radar": low_attendance_students,
            "academic_backlogs_overview": {
                "zero_backlogs_pct": 84.6,
                "one_to_two_backlogs_pct": 11.2,
                "three_plus_backlogs_pct": 4.2,
                "critical_academic_probation_count": 28,
            },
        }
    )


# -----------------------------------------------------------------------------
# 6. Approval Management Center
# -----------------------------------------------------------------------------
@router.get("/approvals", response_model=ApiResponse[list[dict[str, Any]]])
async def list_approvals(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    status: str = Query("ALL", description="ALL, PENDING, APPROVED, REJECTED, MODIFICATION_REQUESTED"),
    category: str | None = Query(None),
    department: str | None = Query(None),
) -> ApiResponse[list[dict[str, Any]]]:
    """Retrieve statutory approval queue covering 8 authorized governance categories."""
    verify_vice_principal_access(current_user)

    items = _STATUTORY_APPROVALS
    if status != "ALL":
        items = [i for i in items if i["status"] == status]
    if category:
        items = [i for i in items if i["category"] == category]
    if department:
        items = [i for i in items if department.lower() in i["department_name"].lower()]

    return ApiResponse(data=items)


@router.post("/approvals/{approval_id}/action", response_model=ApiResponse[dict[str, Any]])
async def process_approval_action(
    approval_id: str,
    payload: ApprovalActionPayload,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ApiResponse[dict[str, Any]]:
    """Execute executive statutory approval action (APPROVE, REJECT, REQUEST_MODIFICATION, FORWARD)."""
    verify_vice_principal_access(current_user)

    valid_actions = {"APPROVE", "REJECT", "REQUEST_MODIFICATION", "FORWARD"}
    if payload.action not in valid_actions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid approval action '{payload.action}'. Must be one of {valid_actions}.",
        )

    # Find target approval
    target = next((a for a in _STATUTORY_APPROVALS if a["id"] == approval_id), None)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Statutory approval request with ID '{approval_id}' was not found.",
        )

    now_iso = datetime.now(UTC).isoformat()
    status_map = {
        "APPROVE": "APPROVED",
        "REJECT": "REJECTED",
        "REQUEST_MODIFICATION": "MODIFICATION_REQUESTED",
        "FORWARD": "FORWARDED",
    }
    new_status = status_map[payload.action]

    target["status"] = new_status
    target["remarks"] = payload.remarks
    target["decided_by"] = current_user.full_name or "Vice Principal"
    target["decision_date"] = now_iso

    audit_entry = {
        "action": new_status,
        "by": current_user.full_name or "Vice Principal",
        "timestamp": now_iso,
        "notes": payload.remarks,
    }
    target["audit_trail"].append(audit_entry)

    # Append to institutional global audit trail
    _AUDIT_LOG_TRAIL.insert(
        0,
        {
            "id": f"aud-{len(_AUDIT_LOG_TRAIL) + 1:03d}",
            "timestamp": now_iso,
            "actor": current_user.full_name or "Vice Principal",
            "action": f"APPROVAL_{new_status}",
            "entity": f"Approval #{target['id']} ({target['title']})",
            "details": payload.remarks,
            "ip_address": "127.0.0.1",
        },
    )

    return ApiResponse(data=target)


# -----------------------------------------------------------------------------
# 7. Examination & Results Monitoring
# -----------------------------------------------------------------------------
@router.get("/examinations", response_model=ApiResponse[dict[str, Any]])
async def get_examinations_oversight(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ApiResponse[dict[str, Any]]:
    """Retrieve examination schedules, Continuous Internal Assessment mark submissions, and results analysis."""
    verify_vice_principal_access(current_user)

    schedules = [
        {
            "id": "exam-01",
            "name": "Continuous Internal Assessment (CIA) 2",
            "date_range": "2026-11-24 to 2026-11-28",
            "type": "INTERNAL",
            "status": "CONFIRMED",
            "question_papers_moderated": 40,
            "question_papers_total": 42,
            "seating_plan_published": True,
        },
        {
            "id": "exam-02",
            "name": "End Semester Laboratory Practical Examinations",
            "date_range": "2026-12-04 to 2026-12-10",
            "type": "PRACTICAL",
            "status": "EXAMINERS_APPOINTED",
            "external_examiners_count": 28,
            "batches_scheduled": 64,
            "seating_plan_published": False,
        },
        {
            "id": "exam-03",
            "name": "University End-Semester Theory Examinations",
            "date_range": "2026-12-18 to 2027-01-08",
            "type": "THEORY",
            "status": "HALL_ALLOCATIONS_FINALIZED",
            "total_halls": 32,
            "chief_superintendent": "Dr. Meenakshi Sundaram (VP)",
            "seating_plan_published": False,
        },
    ]

    cia_mark_submissions = [
        {"department": "Computer Science & Engineering", "total_courses": 42, "submitted": 42, "locked": 42, "pending": 0, "status": "COMPLETED"},
        {"department": "Electronics & Communication", "total_courses": 38, "submitted": 38, "locked": 38, "pending": 0, "status": "COMPLETED"},
        {"department": "Mechanical Engineering", "total_courses": 32, "submitted": 32, "locked": 30, "pending": 2, "status": "LOCK_PENDING"},
        {"department": "Civil Engineering", "total_courses": 26, "submitted": 26, "locked": 26, "pending": 0, "status": "COMPLETED"},
        {"department": "Electrical & Electronics", "total_courses": 28, "submitted": 26, "locked": 24, "pending": 2, "status": "SUBMISSION_OVERDUE"},
    ]

    results_analysis = {
        "overall_institutional_pass_pct": 92.4,
        "first_class_with_distinction_pct": 34.6,
        "first_class_pct": 48.2,
        "arrear_rate_pct": 7.6,
        "department_pass_ranking": [
            {"rank": 1, "department": "CSE", "pass_pct": 96.1},
            {"rank": 2, "department": "ECE", "pass_pct": 94.2},
            {"rank": 3, "department": "CIVIL", "pass_pct": 91.8},
            {"rank": 4, "department": "MECH", "pass_pct": 89.5},
            {"rank": 5, "department": "EEE", "pass_pct": 88.4},
        ],
    }

    return ApiResponse(
        data={
            "schedules": schedules,
            "cia_mark_submissions": cia_mark_submissions,
            "results_analysis": results_analysis,
        }
    )


# -----------------------------------------------------------------------------
# 8. Reports & Analytics
# -----------------------------------------------------------------------------
@router.get("/reports", response_model=ApiResponse[dict[str, Any]])
async def get_institutional_reports(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    academic_year: str = Query("2026-2027"),
) -> ApiResponse[dict[str, Any]]:
    """Retrieve executive performance and compliance analytics across all departments."""
    verify_vice_principal_access(current_user)

    available_reports = [
        {
            "id": "rep-01",
            "name": "Comprehensive Department Academic Performance Index",
            "type": "ACADEMIC_PERFORMANCE",
            "generated_on": "2026-11-18",
            "format": ["PDF", "XLSX"],
            "description": "Multi-department assessment comparing syllabus completion, pass rates, and research publications.",
        },
        {
            "id": "rep-02",
            "name": "Institutional Attendance Compliance & Condonation Forecast",
            "type": "ATTENDANCE_COMPLIANCE",
            "generated_on": "2026-11-18",
            "format": ["PDF", "CSV"],
            "description": "Sub-75% attendance radar across all batches with projected eligibility before university exams.",
        },
        {
            "id": "rep-03",
            "name": "Faculty Teaching Load & Workload Equity Audit",
            "type": "FACULTY_WORKLOAD",
            "generated_on": "2026-11-15",
            "format": ["PDF", "XLSX"],
            "description": "Analysis of teaching contact hours, laboratory sessions, and tutorial distribution per AICTE norms.",
        },
        {
            "id": "rep-04",
            "name": "Curriculum Coverage Velocity & Delay Mitigation Log",
            "type": "CURRICULUM_COVERAGE",
            "generated_on": "2026-11-16",
            "format": ["PDF"],
            "description": "Subject-wise topic progress analysis tracking syllabus delays and remediation plans.",
        },
    ]

    return ApiResponse(
        data={
            "academic_year": academic_year,
            "available_reports": available_reports,
            "summary_metrics": {
                "overall_institutional_compliance": 94.2,
                "accreditation_readiness_index": 3.68,
                "teaching_workload_adherence": 96.5,
            },
        }
    )


# -----------------------------------------------------------------------------
# 9. Communication & Announcements
# -----------------------------------------------------------------------------
@router.get("/announcements", response_model=ApiResponse[list[dict[str, Any]]])
async def list_announcements(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ApiResponse[list[dict[str, Any]]]:
    """Retrieve executive institutional circulars and directives."""
    verify_vice_principal_access(current_user)
    return ApiResponse(data=_INSTITUTIONAL_ANNOUNCEMENTS)


@router.post("/announcements", response_model=ApiResponse[dict[str, Any]])
async def create_announcement(
    payload: AnnouncementCreatePayload,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ApiResponse[dict[str, Any]]:
    """Broadcast a new executive circular or directive to departments and faculty."""
    verify_vice_principal_access(current_user)

    now_iso = datetime.now(UTC).isoformat()
    new_item = {
        "id": f"anc-vp-{len(_INSTITUTIONAL_ANNOUNCEMENTS) + 1:02d}",
        "title": payload.title,
        "target_audience": payload.target_audience,
        "priority": payload.priority,
        "published_at": now_iso,
        "author": current_user.full_name or "Vice Principal",
        "summary": payload.summary,
        "pinned": payload.pinned,
    }
    _INSTITUTIONAL_ANNOUNCEMENTS.insert(0, new_item)

    # Log to audit trail
    _AUDIT_LOG_TRAIL.insert(
        0,
        {
            "id": f"aud-{len(_AUDIT_LOG_TRAIL) + 1:03d}",
            "timestamp": now_iso,
            "actor": current_user.full_name or "Vice Principal",
            "action": "PUBLISHED_CIRCULAR",
            "entity": f"Announcement #{new_item['id']} ({new_item['title']})",
            "details": f"Broadcast to {payload.target_audience}",
            "ip_address": "127.0.0.1",
        },
    )

    return ApiResponse(data=new_item)


# -----------------------------------------------------------------------------
# 10. Institutional Activity & Audit Monitoring
# -----------------------------------------------------------------------------
@router.get("/audit", response_model=ApiResponse[list[dict[str, Any]]])
async def get_institutional_audit_trail(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    limit: int = Query(50, ge=1, le=200),
) -> ApiResponse[list[dict[str, Any]]]:
    """Retrieve read-only institutional governance activity and approval audit trail."""
    verify_vice_principal_access(current_user)
    return ApiResponse(data=_AUDIT_LOG_TRAIL[:limit])
