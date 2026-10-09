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
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, TenantScopedModel

if TYPE_CHECKING:
    from app.models.people import FacultyProfile, StaffProfile, StudentProfile, User


class Institution(BaseModel):
    """Canonical tenant root entity representing a college or university system."""

    __tablename__ = "core_institutions"

    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    slug: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_name: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="ACTIVE", nullable=False, index=True
    )  # ACTIVE, TRIAL, SUSPENDED, ARCHIVED
    plan: Mapped[str] = mapped_column(
        String(32), default="ENTERPRISE", nullable=False
    )  # FREE, STARTER, PROFESSIONAL, ENTERPRISE
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(32), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="India")
    default_timezone: Mapped[str] = mapped_column(
        String(64), nullable=False, default="Asia/Kolkata"
    )
    currency_code: Mapped[str] = mapped_column(String(8), nullable=False, default="INR")
    locale: Mapped[str] = mapped_column(String(32), default="en-IN", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    @property
    def name(self) -> str:
        return self.short_name or self.legal_name

    @property
    def timezone(self) -> str:
        return self.default_timezone

    @property
    def currency(self) -> str:
        return self.currency_code

    # Relationships
    campuses: Mapped[list["Campus"]] = relationship(back_populates="institution")
    departments: Mapped[list["Department"]] = relationship(back_populates="institution")
    memberships: Mapped[list["TenantMembership"]] = relationship(back_populates="institution")


# Canonical alias for Institution in Multi-Tenant architecture
Tenant = Institution


class TenantMembership(BaseModel):
    """User membership and authorization scope within a specific institution tenant."""

    __tablename__ = "core_tenant_memberships"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_tenant_memberships_tenant_user"),
        Index("idx_tenant_membership_status", "tenant_id", "status"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32), default="ACTIVE", nullable=False
    )  # ACTIVE, INVITED, SUSPENDED, REMOVED
    role_scope: Mapped[str] = mapped_column(
        String(64), default="TENANT_MEMBER", nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    institution: Mapped["Institution"] = relationship(back_populates="memberships")



class Campus(TenantScopedModel):
    """Physical branch or campus site belonging to an institution."""

    __tablename__ = "core_campuses"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_campuses_tenant_code"),)

    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    institution: Mapped["Institution"] = relationship(back_populates="campuses")
    departments: Mapped[list["Department"]] = relationship(back_populates="campus")


class Department(TenantScopedModel):
    """Academic or administrative departmental unit."""

    __tablename__ = "core_departments"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_departments_tenant_code"),)

    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    department_type: Mapped[str] = mapped_column(String(32), default="ACADEMIC", nullable=False)
    hod_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    institution: Mapped["Institution"] = relationship(back_populates="departments")
    campus: Mapped["Campus | None"] = relationship(back_populates="departments")
    programs: Mapped[list["Program"]] = relationship(back_populates="department")
    hod: Mapped["User | None"] = relationship("User", foreign_keys=[hod_user_id])
    faculty_members: Mapped[list["FacultyProfile"]] = relationship(
        "FacultyProfile", back_populates="department"
    )
    staff_members: Mapped[list["StaffProfile"]] = relationship(
        "StaffProfile", back_populates="department"
    )


class Program(TenantScopedModel):
    """Formal degree/diploma program offered by an academic department."""

    __tablename__ = "core_programs"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_programs_tenant_code"),)

    department_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    degree_level: Mapped[str] = mapped_column(String(32), nullable=False)  # UG, PG, DOCTORAL
    duration_years: Mapped[Decimal] = mapped_column(Numeric(3, 1), default=4.0, nullable=False)
    total_semesters: Mapped[int] = mapped_column(default=8, nullable=False)
    required_credits: Mapped[int] = mapped_column(default=160, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    department: Mapped["Department"] = relationship(back_populates="programs")
    batches: Mapped[list["Batch"]] = relationship(back_populates="program")
    students: Mapped[list["StudentProfile"]] = relationship(
        "StudentProfile", back_populates="program"
    )


class Regulation(TenantScopedModel):
    """Statutory curriculum framework (e.g., Autonomous R2021, R2025 NEP)."""

    __tablename__ = "core_regulations"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_regulations_tenant_code"),)

    code: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    effective_year: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    batches: Mapped[list["Batch"]] = relationship(back_populates="regulation")


class Batch(TenantScopedModel):
    """Student cohort admitted for a program under a specific statutory regulation."""

    __tablename__ = "core_batches"
    __table_args__ = (
        UniqueConstraint("tenant_id", "program_id", "name", name="uq_batches_tenant_program_name"),
    )

    program_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_programs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    regulation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_regulations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. "CSE 2024-2028"
    admission_year: Mapped[int] = mapped_column(nullable=False)
    graduation_year: Mapped[int] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    program: Mapped["Program"] = relationship(back_populates="batches")
    regulation: Mapped["Regulation"] = relationship(back_populates="batches")
    sections: Mapped[list["Section"]] = relationship(back_populates="batch")
    students: Mapped[list["StudentProfile"]] = relationship(
        "StudentProfile", back_populates="batch"
    )


class AcademicYear(TenantScopedModel):
    """Calendar academic operational period (e.g. 2024-2025)."""

    __tablename__ = "core_academic_years"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_academic_years_tenant_name"),)

    name: Mapped[str] = mapped_column(String(32), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    semesters: Mapped[list["Semester"]] = relationship(back_populates="academic_year")


class Semester(TenantScopedModel):
    """Discrete instructional term within an academic year."""

    __tablename__ = "core_semesters"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "academic_year_id", "name", name="uq_semesters_tenant_year_name"
        ),
    )

    academic_year_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., "Odd Term 2024-25"
    semester_number: Mapped[int] = mapped_column(nullable=False)  # 1..10
    term_type: Mapped[str] = mapped_column(String(16), nullable=False)  # ODD, EVEN, SUMMER
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    academic_year: Mapped["AcademicYear"] = relationship(back_populates="semesters")
    sections: Mapped[list["Section"]] = relationship(back_populates="semester")


class Section(TenantScopedModel):
    """Classroom division within a semester cohort (e.g. Section A, Section B)."""

    __tablename__ = "core_sections"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "program_id",
            "batch_id",
            "semester_id",
            "name",
            name="uq_sections_tenant_composite",
        ),
    )

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
    semester_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_semesters.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    capacity: Mapped[int] = mapped_column(default=60, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    program: Mapped["Program"] = relationship()
    batch: Mapped["Batch"] = relationship(back_populates="sections")
    semester: Mapped["Semester"] = relationship(back_populates="sections")
