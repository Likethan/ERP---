from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseModel, TenantScopedModel

if TYPE_CHECKING:
    from app.models.core import AcademicYear, Batch, Department, Program, Section, Semester


class User(BaseModel):
    """Canonical authentication and login entity across the platform."""

    __tablename__ = "people_users"

    primary_tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_storage_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="ACTIVE", nullable=False
    )  # INVITED, ACTIVE, SUSPENDED, LOCKED, DISABLED
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    password_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def tenant_id(self) -> UUID | None:
        """Convenience alias for primary_tenant_id."""
        return self.primary_tenant_id

    @tenant_id.setter
    def tenant_id(self, value: UUID | None) -> None:
        self.primary_tenant_id = value

    # Relationships to profiles
    student_profile: Mapped["StudentProfile | None"] = relationship(
        back_populates="user", uselist=False
    )
    faculty_profile: Mapped["FacultyProfile | None"] = relationship(
        back_populates="user", uselist=False
    )
    staff_profile: Mapped["StaffProfile | None"] = relationship(
        back_populates="user", uselist=False
    )
    guardian_profile: Mapped["GuardianProfile | None"] = relationship(
        back_populates="user", uselist=False
    )
    roles: Mapped[list["UserRoleAssignment"]] = relationship(back_populates="user")
    sessions: Mapped[list["UserSession"]] = relationship(back_populates="user")
    reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(back_populates="user")


class Role(BaseModel):
    """Named role containing bundles of permissions."""

    __tablename__ = "people_roles"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_roles_tenant_name"),)

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    permissions: Mapped[list["RolePermission"]] = relationship(back_populates="role")
    user_assignments: Mapped[list["UserRoleAssignment"]] = relationship(back_populates="role")


class Permission(Base):
    """Atomic capability definition string (e.g. domain:resource:action)."""

    __tablename__ = "people_permissions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    code: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    roles: Mapped[list["RolePermission"]] = relationship(back_populates="permission")


class RolePermission(Base):
    """Many-to-many junction binding roles to permissions."""

    __tablename__ = "people_role_permissions"

    role_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_roles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    permission_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_permissions.id", ondelete="CASCADE"),
        primary_key=True,
    )

    role: Mapped["Role"] = relationship(back_populates="permissions")
    permission: Mapped["Permission"] = relationship(back_populates="roles")


class UserRoleAssignment(TenantScopedModel):
    """User-role assignment with optional hierarchical campus/department scope."""

    __tablename__ = "people_user_roles"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "user_id",
            "role_id",
            "campus_id",
            "department_id",
            name="uq_user_roles_scoped",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="CASCADE"),
        nullable=True,
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="CASCADE"),
        nullable=True,
    )

    user: Mapped["User"] = relationship(back_populates="roles")
    role: Mapped["Role"] = relationship(back_populates="user_assignments")


class StudentProfile(TenantScopedModel):
    """Canonical single-source-of-truth profile for a student."""

    __tablename__ = "people_students"
    __table_args__ = (
        UniqueConstraint("tenant_id", "admission_number", name="uq_students_tenant_admission"),
        UniqueConstraint("tenant_id", "registration_number", name="uq_students_tenant_reg"),
        Index("idx_perf_students_tenant_prog_status", "tenant_id", "program_id", "status"),
        Index("idx_perf_students_tenant_batch", "tenant_id", "batch_id"),
        Index("idx_perf_students_tenant_roll", "tenant_id", "roll_number"),
        Index("idx_perf_students_tenant_created", "tenant_id", "status", "created_at"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    admission_number: Mapped[str] = mapped_column(String(64), nullable=False)
    registration_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    roll_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(16), nullable=False)  # MALE, FEMALE, OTHER
    blood_group: Mapped[str | None] = mapped_column(String(8), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="ADMITTED", nullable=False
    )  # APPLIED, ADMITTED, ACTIVE, SUSPENDED, ON_LEAVE, GRADUATED, WITHDRAWN, ALUMNI
    admission_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_graduation_date: Mapped[date] = mapped_column(Date, nullable=False)
    actual_graduation_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    program_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_programs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    batch_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_batches.id", ondelete="RESTRICT"),
        nullable=False,
    )
    current_semester_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_semesters.id", ondelete="RESTRICT"),
        nullable=True,
    )
    current_section_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_sections.id", ondelete="RESTRICT"),
        nullable=True,
    )

    emergency_contact_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)

    user: Mapped["User"] = relationship(back_populates="student_profile")
    program: Mapped["Program"] = relationship("Program", back_populates="students")
    batch: Mapped["Batch"] = relationship("Batch", back_populates="students")
    current_semester: Mapped["Semester | None"] = relationship(
        "Semester", foreign_keys=[current_semester_id]
    )
    current_section: Mapped["Section | None"] = relationship(
        "Section", foreign_keys=[current_section_id]
    )
    guardians: Mapped[list["StudentGuardianRelationship"]] = relationship(back_populates="student")
    enrollment_history: Mapped[list["StudentEnrollmentHistory"]] = relationship(
        back_populates="student"
    )
    status_history: Mapped[list["StudentStatusHistory"]] = relationship(back_populates="student")

    @property
    def first_name(self) -> str:
        if "user" in self.__dict__ and self.user is not None:
            return self.user.first_name
        return ""

    @property
    def last_name(self) -> str:
        if "user" in self.__dict__ and self.user is not None:
            return self.user.last_name
        return ""


class FacultyProfile(TenantScopedModel):
    """Canonical instructional profile for academic faculty."""

    __tablename__ = "people_faculty"
    __table_args__ = (UniqueConstraint("tenant_id", "employee_code", name="uq_faculty_emp_code"),)

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    employee_code: Mapped[str] = mapped_column(String(64), nullable=False)
    department_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    designation: Mapped[str] = mapped_column(String(128), nullable=False)
    highest_qualification: Mapped[str] = mapped_column(String(128), nullable=False)
    specialization: Mapped[str | None] = mapped_column(Text, nullable=True)
    joining_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_hod: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    employment_status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)

    user: Mapped["User"] = relationship(back_populates="faculty_profile")
    department: Mapped["Department"] = relationship(
        "Department", back_populates="faculty_members"
    )

    @property
    def first_name(self) -> str:
        if "user" in self.__dict__ and self.user is not None:
            return self.user.first_name
        return ""

    @property
    def last_name(self) -> str:
        if "user" in self.__dict__ and self.user is not None:
            return self.user.last_name
        return ""


class StaffProfile(TenantScopedModel):
    """Canonical operational profile for non-teaching administrative staff."""

    __tablename__ = "people_staff"
    __table_args__ = (UniqueConstraint("tenant_id", "employee_code", name="uq_staff_emp_code"),)

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    employee_code: Mapped[str] = mapped_column(String(64), nullable=False)
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="RESTRICT"),
        nullable=True,
    )
    designation: Mapped[str] = mapped_column(String(128), nullable=False)
    employment_type: Mapped[str] = mapped_column(String(32), default="FULL_TIME", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped["User"] = relationship(back_populates="staff_profile")
    department: Mapped["Department | None"] = relationship(
        "Department", back_populates="staff_members"
    )


class GuardianProfile(TenantScopedModel):
    """Parent or legal guardian profile."""

    __tablename__ = "people_guardians"

    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(32), nullable=False)
    occupation: Mapped[str | None] = mapped_column(String(128), nullable=True)
    annual_income: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User | None"] = relationship(back_populates="guardian_profile")
    students: Mapped[list["StudentGuardianRelationship"]] = relationship(back_populates="guardian")


class StudentGuardianRelationship(Base):
    """Junction linking students to guardians with authorization attributes."""

    __tablename__ = "people_student_guardians"

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="CASCADE"),
        primary_key=True,
    )
    guardian_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_guardians.id", ondelete="CASCADE"),
        primary_key=True,
    )
    relationship_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # FATHER, MOTHER, LEGAL_GUARDIAN, SPONSOR
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_pickup: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    student: Mapped["StudentProfile"] = relationship(back_populates="guardians")
    guardian: Mapped["GuardianProfile"] = relationship(back_populates="students")


class StudentEnrollmentHistory(TenantScopedModel):
    """Non-destructive historical ledger of student semester progressions and section placements."""

    __tablename__ = "people_student_semester_enrollments"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "student_id", "semester_id", name="uq_student_enrollments_term"
        ),
    )

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    academic_year_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
        nullable=False,
    )
    semester_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_semesters.id", ondelete="RESTRICT"),
        nullable=False,
    )
    section_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_sections.id", ondelete="RESTRICT"),
        nullable=False,
    )
    roll_number_snapshot: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="ENROLLED", nullable=False
    )  # ENROLLED, PROMOTED, DETAINED, COMPLETED, WITHDRAWN
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    student: Mapped["StudentProfile"] = relationship(back_populates="enrollment_history")
    academic_year: Mapped["AcademicYear"] = relationship("AcademicYear")
    semester: Mapped["Semester"] = relationship("Semester")
    section: Mapped["Section"] = relationship("Section")


class StudentStatusHistory(TenantScopedModel):
    """Immutable audit log of student lifecycle transitions."""

    __tablename__ = "people_student_status_history"

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    from_status: Mapped[str] = mapped_column(String(32), nullable=False)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    authorized_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)

    student: Mapped["StudentProfile"] = relationship(back_populates="status_history")


class UserSession(BaseModel):
    """Active user authentication session for cookie/token tracking."""

    __tablename__ = "people_user_sessions"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    refresh_token_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship(back_populates="sessions")


class PasswordResetToken(BaseModel):
    """Time-limited one-time password reset token."""

    __tablename__ = "people_password_reset_tokens"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship(back_populates="reset_tokens")
