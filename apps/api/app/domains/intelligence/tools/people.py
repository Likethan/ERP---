"""People domain tools for Intelligence Engine.

Provides controlled access to student profiles, department rosters,
faculty summaries, and staff directories.
"""

from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException, PermissionDeniedException
from app.domains.intelligence.tools.base import ToolDefinition, ToolParameter
from app.models.core import Program
from app.models.people import FacultyProfile, StaffProfile, StudentProfile, User


async def get_student_handler(
    db: AsyncSession, tenant_id: UUID, user: User, params: dict[str, Any]
) -> dict[str, Any]:
    """Retrieve individual student details by ID or roll number."""
    identifier = params.get("identifier") or params.get("student_id") or params.get("roll_number")
    if not identifier:
        # Default to current user if student
        stmt = (
            select(StudentProfile)
            .options(selectinload(StudentProfile.user), selectinload(StudentProfile.program))
            .where(StudentProfile.tenant_id == tenant_id, StudentProfile.user_id == user.id)
        )
        student = await db.scalar(stmt)
        if not student:
            return {"error": "Student identifier required and user is not an enrolled student."}
    else:
        stmt = (
            select(StudentProfile)
            .options(selectinload(StudentProfile.user), selectinload(StudentProfile.program))
            .where(StudentProfile.tenant_id == tenant_id)
        )
        try:
            u_id = UUID(str(identifier))
            stmt = stmt.where(or_(StudentProfile.id == u_id, StudentProfile.user_id == u_id))
        except ValueError:
            stmt = stmt.where(
                or_(
                    StudentProfile.roll_number == str(identifier),
                    StudentProfile.admission_number == str(identifier),
                    StudentProfile.registration_number == str(identifier),
                )
            )
        student = await db.scalar(stmt)
        if not student:
            raise NotFoundException("Student", identifier)

    # Privacy check: If user is student, can only view self
    user_roles = {ur.role.name for ur in user.roles if ur.role}
    if "STUDENT" in user_roles and not {
        "SUPER_ADMIN",
        "INSTITUTION_ADMIN",
        "FACULTY",
        "HOD",
    }.intersection(user_roles):
        if student.user_id != user.id:
            raise PermissionDeniedException("students:read_other_denied")

    u = student.user
    prog = student.program
    return {
        "student_id": str(student.id),
        "user_id": str(student.user_id),
        "name": f"{u.first_name} {u.last_name}" if u else "Unknown",
        "roll_number": student.roll_number or student.admission_number,
        "email": u.email if u else None,
        "program": prog.name if prog else "Unassigned",
        "status": student.status,
        "gender": student.gender,
        "admission_date": student.admission_date.isoformat() if student.admission_date else None,
    }


async def search_students_handler(
    db: AsyncSession, tenant_id: UUID, user: User, params: dict[str, Any]
) -> dict[str, Any]:
    """Search students with filters (max 50)."""
    q_str = params.get("query", "").strip()
    program = params.get("program")
    limit = min(int(params.get("limit", 20)), 50)

    stmt = (
        select(StudentProfile)
        .join(User, StudentProfile.user_id == User.id)
        .options(selectinload(StudentProfile.user), selectinload(StudentProfile.program))
        .where(StudentProfile.tenant_id == tenant_id)
    )
    if q_str:
        like_q = f"%{q_str}%"
        stmt = stmt.where(
            or_(
                User.first_name.ilike(like_q),
                User.last_name.ilike(like_q),
                User.email.ilike(like_q),
                StudentProfile.roll_number.ilike(like_q),
            )
        )
    if program:
        stmt = stmt.join(Program, StudentProfile.program_id == Program.id).where(
            Program.code == program
        )

    stmt = stmt.limit(limit)
    res = await db.execute(stmt)
    students = res.scalars().all()

    items = []
    for s in students:
        u = s.user
        items.append(
            {
                "id": str(s.id),
                "name": f"{u.first_name} {u.last_name}" if u else "Student",
                "roll_number": s.roll_number or s.admission_number,
                "program": s.program.name if s.program else "General",
                "status": s.status,
            }
        )
    return {"total_found": len(items), "students": items}


async def get_faculty_summary_handler(
    db: AsyncSession, tenant_id: UUID, user: User, params: dict[str, Any]
) -> dict[str, Any]:
    """Faculty headcount and departmental breakdown."""
    total = (
        await db.scalar(
            select(func.count(FacultyProfile.id)).where(FacultyProfile.tenant_id == tenant_id)
        )
        or 0
    )
    active = (
        await db.scalar(
            select(func.count(FacultyProfile.id)).where(
                FacultyProfile.tenant_id == tenant_id, FacultyProfile.status == "ACTIVE"
            )
        )
        or 0
    )
    return {
        "total_faculty": total,
        "active_faculty": active,
        "on_leave": total - active,
        "summary": f"{active} active instructional faculty members in institutional directory.",
    }


async def get_staff_summary_handler(
    db: AsyncSession, tenant_id: UUID, user: User, params: dict[str, Any]
) -> dict[str, Any]:
    """Staff headcount and operational distribution."""
    total = (
        await db.scalar(
            select(func.count(StaffProfile.id)).where(StaffProfile.tenant_id == tenant_id)
        )
        or 0
    )
    active = (
        await db.scalar(
            select(func.count(StaffProfile.id)).where(
                StaffProfile.tenant_id == tenant_id, StaffProfile.status == "ACTIVE"
            )
        )
        or 0
    )
    return {
        "total_staff": total,
        "active_staff": active,
        "summary": f"{active} administrative and operational staff active across campus services.",
    }


PEOPLE_TOOLS: list[ToolDefinition] = [
    ToolDefinition(
        name="people.get_student",
        domain="PEOPLE",
        description="Retrieve profile details for a specific student by ID, roll number, or current session",
        required_permissions=["students:read"],
        handler=get_student_handler,
        parameters=[
            ToolParameter(
                "identifier", "string", False, "Roll number, registration number, or student UUID"
            ),
        ],
    ),
    ToolDefinition(
        name="people.search_students",
        domain="PEOPLE",
        description="Search students by name, roll number, or program filter",
        required_permissions=["students:read"],
        handler=search_students_handler,
        parameters=[
            ToolParameter("query", "string", False, "Name, roll number, or email substring"),
            ToolParameter("program", "string", False, "Program code e.g. CSE"),
            ToolParameter("limit", "integer", False, "Max students to return (capped at 50)", 20),
        ],
    ),
    ToolDefinition(
        name="people.get_faculty_summary",
        domain="PEOPLE",
        description="Headcount, department distribution, and employment status of faculty",
        required_permissions=["faculty:read"],
        handler=get_faculty_summary_handler,
    ),
    ToolDefinition(
        name="people.get_staff_summary",
        domain="PEOPLE",
        description="Administrative and operational staff staffing numbers",
        required_permissions=["people_staff:read"],
        handler=get_staff_summary_handler,
    ),
]
