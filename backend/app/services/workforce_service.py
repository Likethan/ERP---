"""CampusOS Enterprise Workforce Management, Staff Lifecycle, Leave & Workload Administration Service (Step 51).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.models.academics import CourseOffering
from app.models.core import Campus, Department
from app.models.people import FacultyProfile, User
from app.models.timetable import TimetableSession
from app.models.workforce import (
    AvailabilityStatus,
    EmploymentChangeType,
    EmploymentStatus,
    HRCaseStatus,
    LeaveAccrualFrequency,
    LeaveRequestStatus,
    LeaveTransactionType,
    LifecycleCaseStatus,
    LifecycleCaseType,
    LifecycleTaskCategory,
    LifecycleTaskStatus,
    WorkforceAvailabilityConflict,
    WorkforceEmployee,
    WorkforceEmploymentHistory,
    WorkforceHRCase,
    WorkforceLeaveApprovalStep,
    WorkforceLeaveBalance,
    WorkforceLeaveBalanceTransaction,
    WorkforceLeavePolicy,
    WorkforceLeaveRequest,
    WorkforceLeaveType,
    WorkforceLifecycleCase,
    WorkforceLifecycleTask,
    WorkforceWorkloadAdjustment,
    WorkforceWorkloadExpectation,
)
from app.schemas.workforce import (
    WorkforceAvailabilityCheckResponse,
    WorkforceCapacityReport,
    WorkforceEmployeeCreate,
    WorkforceEmployeeResponse,
    WorkforceEmployeeTransitionRequest,
    WorkforceEmployeeUpdate,
    WorkforceEmploymentHistoryResponse,
    WorkforceHeadcountReport,
    WorkforceHRCaseCreate,
    WorkforceHRCaseResponse,
    WorkforceHRCaseUpdate,
    WorkforceLeaveApprovalStepResponse,
    WorkforceLeaveBalanceAdjustRequest,
    WorkforceLeaveBalanceResponse,
    WorkforceLeaveCalendarEntry,
    WorkforceLeavePolicyCreate,
    WorkforceLeavePolicyResponse,
    WorkforceLeaveRequestCreate,
    WorkforceLeaveRequestResponse,
    WorkforceLeaveTypeCreate,
    WorkforceLeaveTypeResponse,
    WorkforceLeaveUtilizationReport,
    WorkforceLifecycleCaseCreate,
    WorkforceLifecycleCaseResponse,
    WorkforceLifecycleTaskResponse,
    WorkforceLifecycleTaskUpdate,
    WorkforceSeparationInitiateRequest,
    WorkforceWorkloadAdjustmentCreate,
    WorkforceWorkloadAdjustmentResponse,
    WorkforceWorkloadExpectationCreate,
    WorkforceWorkloadExpectationResponse,
    WorkforceWorkloadSummaryResponse,
)


class WorkforceService:
    """Service layer for Enterprise Workforce Management and Staff Administration."""

    # =========================================================================
    # 1. EMPLOYEE MASTER & EMPLOYMENT RECORDS
    # =========================================================================

    async def create_employee(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: WorkforceEmployeeCreate,
        author_user_id: UUID,
    ) -> WorkforceEmployeeResponse:
        """Create a new workforce employee record linked to canonical user."""
        # 1. Verify user exists
        user_res = await db.execute(select(User).where(User.id == payload.user_id))
        user = user_res.scalar_one_or_none()
        if not user:
            raise NotFoundException("User", payload.user_id)

        # 2. Verify unique employee per user in tenant
        existing_res = await db.execute(
            select(WorkforceEmployee).where(
                WorkforceEmployee.tenant_id == tenant_id,
                WorkforceEmployee.user_id == payload.user_id,
            )
        )
        if existing_res.scalar_one_or_none():
            raise ConflictException("Employee record for this user already exists in this institution")

        # 3. Handle employee number uniqueness
        emp_number = payload.employee_number
        if not emp_number:
            uid_suffix = uuid.uuid4().hex[:6].upper()
            emp_number = f"EMP-{payload.joining_date.year}-{uid_suffix}"
        else:
            code_res = await db.execute(
                select(WorkforceEmployee).where(
                    WorkforceEmployee.tenant_id == tenant_id,
                    WorkforceEmployee.employee_number == emp_number,
                )
            )
            if code_res.scalar_one_or_none():
                raise ConflictException("WorkforceEmployee", "employee_number", emp_number)

        # 4. Verify department and campus if provided
        if payload.department_id:
            dept_res = await db.execute(
                select(Department).where(
                    Department.id == payload.department_id,
                    Department.tenant_id == tenant_id,
                )
            )
            if not dept_res.scalar_one_or_none():
                raise NotFoundException("Department", payload.department_id)

        if payload.campus_id:
            campus_res = await db.execute(
                select(Campus).where(
                    Campus.id == payload.campus_id,
                    Campus.tenant_id == tenant_id,
                )
            )
            if not campus_res.scalar_one_or_none():
                raise NotFoundException("Campus", payload.campus_id)

        # 5. Create employee
        employee = WorkforceEmployee(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=payload.user_id,
            employee_number=emp_number,
            employment_type=payload.employment_type,
            employment_status=payload.employment_status,
            designation=payload.designation,
            job_title=payload.job_title,
            department_id=payload.department_id,
            campus_id=payload.campus_id,
            reporting_manager_id=payload.reporting_manager_id,
            work_location=payload.work_location,
            joining_date=payload.joining_date,
            probation_end_date=payload.probation_end_date,
            confirmation_date=payload.confirmation_date,
            contract_start_date=payload.contract_start_date,
            contract_end_date=payload.contract_end_date,
            notice_period_days=payload.notice_period_days,
            qualifications=payload.qualifications,
            certifications=payload.certifications,
            metadata_properties=payload.metadata_properties,
            is_active=True,
        )
        db.add(employee)

        # 6. Audit initial employment record in history
        history = WorkforceEmploymentHistory(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            employee_id=employee.id,
            change_type=EmploymentChangeType.JOINING,
            effective_date=payload.joining_date,
            previous_values={},
            new_values={
                "employment_type": payload.employment_type,
                "employment_status": payload.employment_status,
                "designation": payload.designation,
                "job_title": payload.job_title,
            },
            reason="Initial employment appointment",
            authorized_by_user_id=author_user_id,
        )
        db.add(history)

        # 7. If ONBOARDING status, automatically initialize onboarding lifecycle case
        if payload.employment_status == EmploymentStatus.ONBOARDING:
            case_number = f"ONB-{payload.joining_date.year}-{uuid.uuid4().hex[:6].upper()}"
            onb_case = WorkforceLifecycleCase(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                employee_id=employee.id,
                case_number=case_number,
                case_type=LifecycleCaseType.ONBOARDING,
                status=LifecycleCaseStatus.IN_PROGRESS,
                target_date=payload.joining_date + timedelta(days=14),
                initiator_user_id=author_user_id,
                notes="Standard institutional staff onboarding case",
                metadata_json={},
            )
            db.add(onb_case)

            # Add default onboarding tasks
            default_tasks = [
                ("Verify Educational & Identification Credentials", LifecycleTaskCategory.HR, True),
                ("Execute Institutional Employment Agreement & NDA", LifecycleTaskCategory.HR, True),
                ("Provision Enterprise Email & Identity Credentials", LifecycleTaskCategory.IT, True),
                ("Issue Smart RFID Badge & Campus Parking Permit", LifecycleTaskCategory.FACILITIES, True),
                ("Department Workstation Allocation & Staff Orientation", LifecycleTaskCategory.DEPARTMENT, True),
            ]
            for task_name, category, mandatory in default_tasks:
                db.add(
                    WorkforceLifecycleTask(
                        id=uuid.uuid4(),
                        tenant_id=tenant_id,
                        case_id=onb_case.id,
                        task_name=task_name,
                        task_category=category,
                        is_mandatory=mandatory,
                        status=LifecycleTaskStatus.PENDING,
                        due_date=onb_case.target_date,
                    )
                )

        await db.commit()
        return await self.get_employee_response(db, tenant_id, employee.id)

    async def get_employee_by_user_id(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
    ) -> WorkforceEmployee | None:
        """Fetch employee by linked user identity within tenant."""
        stmt = select(WorkforceEmployee).where(
            WorkforceEmployee.tenant_id == tenant_id,
            WorkforceEmployee.user_id == user_id,
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_employee_response(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        employee_id: UUID,
    ) -> WorkforceEmployeeResponse:
        """Fetch employee with resolved user, department, and campus labels."""
        stmt = (
            select(WorkforceEmployee)
            .options(
                selectinload(WorkforceEmployee.user),
                selectinload(WorkforceEmployee.department),
                selectinload(WorkforceEmployee.campus),
                selectinload(WorkforceEmployee.reporting_manager),
            )
            .where(
                WorkforceEmployee.id == employee_id,
                WorkforceEmployee.tenant_id == tenant_id,
            )
        )
        res = await db.execute(stmt)
        emp = res.scalar_one_or_none()
        if not emp:
            raise NotFoundException("WorkforceEmployee", employee_id)

        mgr_name = None
        mgr_code = None
        if emp.reporting_manager:
            mgr_user_res = await db.execute(select(User).where(User.id == emp.reporting_manager.user_id))
            mgr_u = mgr_user_res.scalar_one_or_none()
            mgr_name = f"{mgr_u.first_name} {mgr_u.last_name}" if mgr_u else None
            mgr_code = emp.reporting_manager.employee_number

        return WorkforceEmployeeResponse(
            id=emp.id,
            tenant_id=emp.tenant_id,
            user_id=emp.user_id,
            employee_number=emp.employee_number,
            employment_type=emp.employment_type,
            employment_status=emp.employment_status,
            designation=emp.designation,
            job_title=emp.job_title,
            department_id=emp.department_id,
            department_name=emp.department.name if emp.department else None,
            campus_id=emp.campus_id,
            campus_name=emp.campus.name if emp.campus else None,
            reporting_manager_id=emp.reporting_manager_id,
            reporting_manager_name=mgr_name,
            reporting_manager_employee_number=mgr_code,
            work_location=emp.work_location,
            joining_date=emp.joining_date,
            probation_end_date=emp.probation_end_date,
            confirmation_date=emp.confirmation_date,
            contract_start_date=emp.contract_start_date,
            contract_end_date=emp.contract_end_date,
            separation_date=emp.separation_date,
            separation_reason=emp.separation_reason,
            notice_period_days=emp.notice_period_days,
            qualifications=emp.qualifications,
            certifications=emp.certifications,
            metadata_properties=emp.metadata_properties,
            is_active=emp.is_active,
            first_name=emp.user.first_name if emp.user else "",
            last_name=emp.user.last_name if emp.user else "",
            email=emp.user.email if emp.user else "",
            phone_number=emp.user.phone_number if emp.user else None,
            created_at=emp.created_at,
            updated_at=emp.updated_at,
        )

    async def list_employees(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        search: str | None = None,
        department_id: UUID | None = None,
        campus_id: UUID | None = None,
        status: str | None = None,
        employment_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[WorkforceEmployeeResponse], int]:
        """Query employees with filtering and pagination."""
        query = (
            select(WorkforceEmployee)
            .options(
                selectinload(WorkforceEmployee.user),
                selectinload(WorkforceEmployee.department),
                selectinload(WorkforceEmployee.campus),
                selectinload(WorkforceEmployee.reporting_manager),
            )
            .where(WorkforceEmployee.tenant_id == tenant_id)
        )

        if department_id:
            query = query.where(WorkforceEmployee.department_id == department_id)
        if campus_id:
            query = query.where(WorkforceEmployee.campus_id == campus_id)
        if status and status != "ALL":
            query = query.where(WorkforceEmployee.employment_status == status)
        if employment_type and employment_type != "ALL":
            query = query.where(WorkforceEmployee.employment_type == employment_type)

        if search:
            q = f"%{search.strip().lower()}%"
            query = query.join(WorkforceEmployee.user).where(
                or_(
                    func.lower(WorkforceEmployee.employee_number).like(q),
                    func.lower(WorkforceEmployee.designation).like(q),
                    func.lower(WorkforceEmployee.job_title).like(q),
                    func.lower(User.first_name).like(q),
                    func.lower(User.last_name).like(q),
                    func.lower(User.email).like(q),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(query.order_by(None).subquery())
        total_res = await db.execute(count_stmt)
        total = total_res.scalar_one()

        # Paginate
        query = query.order_by(WorkforceEmployee.joining_date.desc()).offset((page - 1) * page_size).limit(page_size)
        res = await db.execute(query)
        employees = res.scalars().all()

        responses = []
        for emp in employees:
            mgr_name = None
            if emp.reporting_manager:
                mgr_u_res = await db.execute(select(User).where(User.id == emp.reporting_manager.user_id))
                mgr_u = mgr_u_res.scalar_one_or_none()
                mgr_name = f"{mgr_u.first_name} {mgr_u.last_name}" if mgr_u else None

            responses.append(
                WorkforceEmployeeResponse(
                    id=emp.id,
                    tenant_id=emp.tenant_id,
                    user_id=emp.user_id,
                    employee_number=emp.employee_number,
                    employment_type=emp.employment_type,
                    employment_status=emp.employment_status,
                    designation=emp.designation,
                    job_title=emp.job_title,
                    department_id=emp.department_id,
                    department_name=emp.department.name if emp.department else None,
                    campus_id=emp.campus_id,
                    campus_name=emp.campus.name if emp.campus else None,
                    reporting_manager_id=emp.reporting_manager_id,
                    reporting_manager_name=mgr_name,
                    reporting_manager_employee_number=emp.reporting_manager.employee_number if emp.reporting_manager else None,
                    work_location=emp.work_location,
                    joining_date=emp.joining_date,
                    probation_end_date=emp.probation_end_date,
                    confirmation_date=emp.confirmation_date,
                    contract_start_date=emp.contract_start_date,
                    contract_end_date=emp.contract_end_date,
                    separation_date=emp.separation_date,
                    separation_reason=emp.separation_reason,
                    notice_period_days=emp.notice_period_days,
                    qualifications=emp.qualifications,
                    certifications=emp.certifications,
                    metadata_properties=emp.metadata_properties,
                    is_active=emp.is_active,
                    first_name=emp.user.first_name if emp.user else "",
                    last_name=emp.user.last_name if emp.user else "",
                    email=emp.user.email if emp.user else "",
                    phone_number=emp.user.phone_number if emp.user else None,
                    created_at=emp.created_at,
                    updated_at=emp.updated_at,
                )
            )

        return responses, total

    async def update_employee(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        employee_id: UUID,
        payload: WorkforceEmployeeUpdate,
        author_user_id: UUID,
    ) -> WorkforceEmployeeResponse:
        """Update permitted workforce attributes and audit changes."""
        emp_res = await db.execute(
            select(WorkforceEmployee).where(
                WorkforceEmployee.id == employee_id,
                WorkforceEmployee.tenant_id == tenant_id,
            )
        )
        emp = emp_res.scalar_one_or_none()
        if not emp:
            raise NotFoundException("WorkforceEmployee", employee_id)

        prev_values = {
            "designation": emp.designation,
            "job_title": emp.job_title,
            "department_id": str(emp.department_id) if emp.department_id else None,
            "employment_type": emp.employment_type,
            "reporting_manager_id": str(emp.reporting_manager_id) if emp.reporting_manager_id else None,
        }

        changes = {}
        for field, val in payload.model_dump(exclude_unset=True).items():
            if getattr(emp, field) != val:
                changes[field] = val
                setattr(emp, field, val)

        if changes:
            history = WorkforceEmploymentHistory(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                employee_id=emp.id,
                change_type=EmploymentChangeType.TRANSFER if "department_id" in changes else EmploymentChangeType.DESIGNATION_CHANGE,
                effective_date=date.today(),
                previous_values=prev_values,
                new_values=changes,
                reason="Workforce profile attributes modification",
                authorized_by_user_id=author_user_id,
            )
            db.add(history)

        await db.commit()
        return await self.get_employee_response(db, tenant_id, emp.id)

    async def transition_employee_status(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        employee_id: UUID,
        payload: WorkforceEmployeeTransitionRequest,
        author_user_id: UUID,
    ) -> WorkforceEmployeeResponse:
        """Transition employee lifecycle status with validation."""
        emp_res = await db.execute(
            select(WorkforceEmployee).where(
                WorkforceEmployee.id == employee_id,
                WorkforceEmployee.tenant_id == tenant_id,
            )
        )
        emp = emp_res.scalar_one_or_none()
        if not emp:
            raise NotFoundException("WorkforceEmployee", employee_id)

        current_status = emp.employment_status
        new_status = payload.new_status

        # Valid transition rules
        valid_transitions = {
            EmploymentStatus.DRAFT: [EmploymentStatus.ONBOARDING, EmploymentStatus.ACTIVE, EmploymentStatus.ARCHIVED],
            EmploymentStatus.ONBOARDING: [EmploymentStatus.ACTIVE, EmploymentStatus.ARCHIVED],
            EmploymentStatus.ACTIVE: [EmploymentStatus.ON_LEAVE, EmploymentStatus.SUSPENDED, EmploymentStatus.NOTICE_PERIOD, EmploymentStatus.ARCHIVED],
            EmploymentStatus.ON_LEAVE: [EmploymentStatus.ACTIVE],
            EmploymentStatus.SUSPENDED: [EmploymentStatus.ACTIVE, EmploymentStatus.NOTICE_PERIOD, EmploymentStatus.SEPARATED],
            EmploymentStatus.NOTICE_PERIOD: [EmploymentStatus.SEPARATED, EmploymentStatus.ACTIVE],
            EmploymentStatus.SEPARATED: [EmploymentStatus.ARCHIVED],
            EmploymentStatus.ARCHIVED: [],
        }

        if new_status not in valid_transitions.get(current_status, []):
            raise BadRequestException(f"Invalid employment status transition from '{current_status}' to '{new_status}'.")

        # Gate: ONBOARDING -> ACTIVE requires all mandatory onboarding tasks to be completed!
        if current_status == EmploymentStatus.ONBOARDING and new_status == EmploymentStatus.ACTIVE:
            tasks_res = await db.execute(
                select(WorkforceLifecycleTask)
                .join(WorkforceLifecycleCase, WorkforceLifecycleTask.case_id == WorkforceLifecycleCase.id)
                .where(
                    WorkforceLifecycleCase.employee_id == employee_id,
                    WorkforceLifecycleCase.case_type == LifecycleCaseType.ONBOARDING,
                    WorkforceLifecycleTask.is_mandatory.is_(True),
                    WorkforceLifecycleTask.status != LifecycleTaskStatus.COMPLETED,
                    WorkforceLifecycleTask.status != LifecycleTaskStatus.WAIVED,
                )
            )
            incomplete = tasks_res.scalars().all()
            if incomplete:
                task_names = ", ".join(f"'{t.task_name}'" for t in incomplete)
                raise BadRequestException(f"Cannot activate employment: Mandatory onboarding tasks ({task_names}) are not completed.")

        prev_status = emp.employment_status
        emp.employment_status = new_status
        if new_status == EmploymentStatus.ACTIVE and not emp.confirmation_date:
            emp.confirmation_date = payload.effective_date

        history = WorkforceEmploymentHistory(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            employee_id=emp.id,
            change_type=EmploymentChangeType.STATUS_CHANGE,
            effective_date=payload.effective_date,
            previous_values={"employment_status": prev_status},
            new_values={"employment_status": new_status},
            reason=payload.reason,
            authorized_by_user_id=author_user_id,
            reference_document_id=payload.reference_document_id,
        )
        db.add(history)

        await db.commit()
        return await self.get_employee_response(db, tenant_id, emp.id)

    async def get_employment_history(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        employee_id: UUID,
    ) -> list[WorkforceEmploymentHistoryResponse]:
        """Fetch audit trail of an employee's organizational progression."""
        stmt = (
            select(WorkforceEmploymentHistory)
            .options(selectinload(WorkforceEmploymentHistory.authorized_by))
            .where(
                WorkforceEmploymentHistory.employee_id == employee_id,
                WorkforceEmploymentHistory.tenant_id == tenant_id,
            )
            .order_by(WorkforceEmploymentHistory.effective_date.desc(), WorkforceEmploymentHistory.created_at.desc())
        )
        res = await db.execute(stmt)
        records = res.scalars().all()

        return [
            WorkforceEmploymentHistoryResponse(
                id=r.id,
                tenant_id=r.tenant_id,
                employee_id=r.employee_id,
                change_type=r.change_type,
                effective_date=r.effective_date,
                previous_values=r.previous_values,
                new_values=r.new_values,
                reason=r.reason,
                authorized_by_user_id=r.authorized_by_user_id,
                authorized_by_name=f"{r.authorized_by.first_name} {r.authorized_by.last_name}" if r.authorized_by else None,
                reference_document_id=r.reference_document_id,
                created_at=r.created_at,
            )
            for r in records
        ]

    # =========================================================================
    # 2. STAFF LIFECYCLE: ONBOARDING & OFFBOARDING
    # =========================================================================

    async def create_lifecycle_case(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: WorkforceLifecycleCaseCreate,
        author_user_id: UUID,
    ) -> WorkforceLifecycleCaseResponse:
        """Create a lifecycle case (onboarding/offboarding) with checklist tasks."""
        emp_res = await db.execute(
            select(WorkforceEmployee).where(
                WorkforceEmployee.id == payload.employee_id,
                WorkforceEmployee.tenant_id == tenant_id,
            )
        )
        emp = emp_res.scalar_one_or_none()
        if not emp:
            raise NotFoundException("WorkforceEmployee", payload.employee_id)

        case_prefix = "ONB" if payload.case_type == LifecycleCaseType.ONBOARDING else "OFF"
        case_number = f"{case_prefix}-{date.today().year}-{uuid.uuid4().hex[:6].upper()}"

        case = WorkforceLifecycleCase(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            employee_id=payload.employee_id,
            case_number=case_number,
            case_type=payload.case_type,
            status=LifecycleCaseStatus.IN_PROGRESS,
            target_date=payload.target_date,
            initiator_user_id=author_user_id,
            notes=payload.notes,
            metadata_json=payload.metadata_json,
        )
        db.add(case)

        # Populate custom tasks or default tasks
        if payload.custom_tasks:
            for t in payload.custom_tasks:
                db.add(
                    WorkforceLifecycleTask(
                        id=uuid.uuid4(),
                        tenant_id=tenant_id,
                        case_id=case.id,
                        task_name=t.task_name,
                        task_category=t.task_category,
                        assigned_role=t.assigned_role,
                        assigned_user_id=t.assigned_user_id,
                        is_mandatory=t.is_mandatory,
                        status=LifecycleTaskStatus.PENDING,
                        due_date=t.due_date or payload.target_date,
                    )
                )
        else:
            default_tasks = (
                [
                    ("Verify Educational & Identification Credentials", LifecycleTaskCategory.HR, True),
                    ("Execute Institutional Employment Agreement & NDA", LifecycleTaskCategory.HR, True),
                    ("Provision Enterprise Email & Identity Credentials", LifecycleTaskCategory.IT, True),
                    ("Issue Smart RFID Badge & Campus Parking Permit", LifecycleTaskCategory.FACILITIES, True),
                    ("Department Workstation Allocation & Staff Orientation", LifecycleTaskCategory.DEPARTMENT, True),
                ]
                if payload.case_type == LifecycleCaseType.ONBOARDING
                else [
                    ("Departmental Knowledge Transfer & Project Handover", LifecycleTaskCategory.DEPARTMENT, True),
                    ("Surrender Institutional Laptop & IT Hardware", LifecycleTaskCategory.IT, True),
                    ("Revoke System Credentials & Enterprise SSO Access", LifecycleTaskCategory.IT, True),
                    ("Surrender RFID Badge, Office Keys & Parking Permit", LifecycleTaskCategory.FACILITIES, True),
                    ("Finance Settlement & No Dues Certificate", LifecycleTaskCategory.FINANCE, True),
                    ("HR Exit Interview & Service Certificate Issuance", LifecycleTaskCategory.HR, True),
                ]
            )
            for task_name, category, mandatory in default_tasks:
                db.add(
                    WorkforceLifecycleTask(
                        id=uuid.uuid4(),
                        tenant_id=tenant_id,
                        case_id=case.id,
                        task_name=task_name,
                        task_category=category,
                        is_mandatory=mandatory,
                        status=LifecycleTaskStatus.PENDING,
                        due_date=payload.target_date,
                    )
                )

        await db.commit()
        return await self.get_lifecycle_case(db, tenant_id, case.id)

    async def get_lifecycle_case(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        case_id: UUID,
    ) -> WorkforceLifecycleCaseResponse:
        """Fetch lifecycle case with tasks and actors."""
        stmt = (
            select(WorkforceLifecycleCase)
            .options(
                selectinload(WorkforceLifecycleCase.employee).selectinload(WorkforceEmployee.user),
                selectinload(WorkforceLifecycleCase.initiator),
                selectinload(WorkforceLifecycleCase.tasks).selectinload(WorkforceLifecycleTask.assigned_user),
                selectinload(WorkforceLifecycleCase.tasks).selectinload(WorkforceLifecycleTask.completed_by),
            )
            .where(
                WorkforceLifecycleCase.id == case_id,
                WorkforceLifecycleCase.tenant_id == tenant_id,
            )
        )
        res = await db.execute(stmt)
        c = res.scalar_one_or_none()
        if not c:
            raise NotFoundException("WorkforceLifecycleCase", case_id)

        task_responses = [
            WorkforceLifecycleTaskResponse(
                id=t.id,
                tenant_id=t.tenant_id,
                case_id=t.case_id,
                task_name=t.task_name,
                task_category=t.task_category,
                assigned_role=t.assigned_role,
                assigned_user_id=t.assigned_user_id,
                assigned_user_name=f"{t.assigned_user.first_name} {t.assigned_user.last_name}" if t.assigned_user else None,
                is_mandatory=t.is_mandatory,
                status=t.status,
                due_date=t.due_date,
                completed_at=t.completed_at,
                completed_by_user_id=t.completed_by_user_id,
                completed_by_name=f"{t.completed_by.first_name} {t.completed_by.last_name}" if t.completed_by else None,
                completion_evidence=t.completion_evidence,
                blocker_reason=t.blocker_reason,
                created_at=t.created_at,
            )
            for t in c.tasks
        ]

        emp_name = f"{c.employee.user.first_name} {c.employee.user.last_name}" if c.employee and c.employee.user else None

        return WorkforceLifecycleCaseResponse(
            id=c.id,
            tenant_id=c.tenant_id,
            employee_id=c.employee_id,
            employee_name=emp_name,
            employee_number=c.employee.employee_number if c.employee else None,
            case_number=c.case_number,
            case_type=c.case_type,
            status=c.status,
            target_date=c.target_date,
            completion_date=c.completion_date,
            initiator_user_id=c.initiator_user_id,
            initiator_name=f"{c.initiator.first_name} {c.initiator.last_name}" if c.initiator else None,
            notes=c.notes,
            metadata_json=c.metadata_json,
            tasks=task_responses,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )

    async def list_lifecycle_cases(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        employee_id: UUID | None = None,
        case_type: str | None = None,
        status: str | None = None,
    ) -> list[WorkforceLifecycleCaseResponse]:
        """List lifecycle cases with optional filters."""
        query = (
            select(WorkforceLifecycleCase)
            .options(
                selectinload(WorkforceLifecycleCase.employee).selectinload(WorkforceEmployee.user),
                selectinload(WorkforceLifecycleCase.initiator),
                selectinload(WorkforceLifecycleCase.tasks).selectinload(WorkforceLifecycleTask.assigned_user),
                selectinload(WorkforceLifecycleCase.tasks).selectinload(WorkforceLifecycleTask.completed_by),
            )
            .where(WorkforceLifecycleCase.tenant_id == tenant_id)
        )

        if employee_id:
            query = query.where(WorkforceLifecycleCase.employee_id == employee_id)
        if case_type:
            query = query.where(WorkforceLifecycleCase.case_type == case_type)
        if status:
            query = query.where(WorkforceLifecycleCase.status == status)

        query = query.order_by(WorkforceLifecycleCase.created_at.desc())
        res = await db.execute(query)
        cases = res.scalars().all()

        results = []
        for c in cases:
            task_responses = [
                WorkforceLifecycleTaskResponse(
                    id=t.id,
                    tenant_id=t.tenant_id,
                    case_id=t.case_id,
                    task_name=t.task_name,
                    task_category=t.task_category,
                    assigned_role=t.assigned_role,
                    assigned_user_id=t.assigned_user_id,
                    assigned_user_name=f"{t.assigned_user.first_name} {t.assigned_user.last_name}" if t.assigned_user else None,
                    is_mandatory=t.is_mandatory,
                    status=t.status,
                    due_date=t.due_date,
                    completed_at=t.completed_at,
                    completed_by_user_id=t.completed_by_user_id,
                    completed_by_name=f"{t.completed_by.first_name} {t.completed_by.last_name}" if t.completed_by else None,
                    completion_evidence=t.completion_evidence,
                    blocker_reason=t.blocker_reason,
                    created_at=t.created_at,
                )
                for t in c.tasks
            ]
            emp_name = f"{c.employee.user.first_name} {c.employee.user.last_name}" if c.employee and c.employee.user else None
            results.append(
                WorkforceLifecycleCaseResponse(
                    id=c.id,
                    tenant_id=c.tenant_id,
                    employee_id=c.employee_id,
                    employee_name=emp_name,
                    employee_number=c.employee.employee_number if c.employee else None,
                    case_number=c.case_number,
                    case_type=c.case_type,
                    status=c.status,
                    target_date=c.target_date,
                    completion_date=c.completion_date,
                    initiator_user_id=c.initiator_user_id,
                    initiator_name=f"{c.initiator.first_name} {c.initiator.last_name}" if c.initiator else None,
                    notes=c.notes,
                    metadata_json=c.metadata_json,
                    tasks=task_responses,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                )
            )
        return results

    async def update_lifecycle_task(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        task_id: UUID,
        payload: WorkforceLifecycleTaskUpdate,
        user_id: UUID,
    ) -> WorkforceLifecycleTaskResponse:
        """Update lifecycle checklist task and check case completion."""
        stmt = (
            select(WorkforceLifecycleTask)
            .options(
                selectinload(WorkforceLifecycleTask.case).selectinload(WorkforceLifecycleCase.tasks),
                selectinload(WorkforceLifecycleTask.assigned_user),
                selectinload(WorkforceLifecycleTask.completed_by),
            )
            .where(
                WorkforceLifecycleTask.id == task_id,
                WorkforceLifecycleTask.tenant_id == tenant_id,
            )
        )
        res = await db.execute(stmt)
        task = res.scalar_one_or_none()
        if not task:
            raise NotFoundException("WorkforceLifecycleTask", task_id)

        task.status = payload.status
        if payload.status == LifecycleTaskStatus.COMPLETED:
            task.completed_at = datetime.now(UTC)
            task.completed_by_user_id = user_id
            task.completion_evidence = payload.completion_evidence
            task.blocker_reason = None
        elif payload.status == LifecycleTaskStatus.BLOCKED:
            task.blocker_reason = payload.blocker_reason
        else:
            task.completed_at = None
            task.completed_by_user_id = None

        # Check if all tasks in case are completed
        case = task.case
        all_completed = all(
            t.status in (LifecycleTaskStatus.COMPLETED, LifecycleTaskStatus.WAIVED)
            for t in case.tasks
        )
        if all_completed and case.status != LifecycleCaseStatus.COMPLETED:
            case.status = LifecycleCaseStatus.COMPLETED
            case.completion_date = date.today()

        await db.commit()
        return WorkforceLifecycleTaskResponse(
            id=task.id,
            tenant_id=task.tenant_id,
            case_id=task.case_id,
            task_name=task.task_name,
            task_category=task.task_category,
            assigned_role=task.assigned_role,
            assigned_user_id=task.assigned_user_id,
            assigned_user_name=f"{task.assigned_user.first_name} {task.assigned_user.last_name}" if task.assigned_user else None,
            is_mandatory=task.is_mandatory,
            status=task.status,
            due_date=task.due_date,
            completed_at=task.completed_at,
            completed_by_user_id=task.completed_by_user_id,
            completed_by_name=f"{task.completed_by.first_name} {task.completed_by.last_name}" if task.completed_by else None,
            completion_evidence=task.completion_evidence,
            blocker_reason=task.blocker_reason,
            created_at=task.created_at,
        )

    async def initiate_offboarding(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: WorkforceSeparationInitiateRequest,
        author_user_id: UUID,
    ) -> WorkforceLifecycleCaseResponse:
        """Initiate staff separation and clearance checklist."""
        emp_res = await db.execute(
            select(WorkforceEmployee).where(
                WorkforceEmployee.id == payload.employee_id,
                WorkforceEmployee.tenant_id == tenant_id,
            )
        )
        emp = emp_res.scalar_one_or_none()
        if not emp:
            raise NotFoundException("WorkforceEmployee", payload.employee_id)

        # Transition status to NOTICE_PERIOD
        emp.employment_status = EmploymentStatus.NOTICE_PERIOD
        emp.separation_date = payload.separation_date
        emp.separation_reason = payload.separation_reason
        emp.notice_period_days = payload.notice_period_days

        history = WorkforceEmploymentHistory(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            employee_id=emp.id,
            change_type=EmploymentChangeType.STATUS_CHANGE,
            effective_date=date.today(),
            previous_values={"employment_status": EmploymentStatus.ACTIVE},
            new_values={
                "employment_status": EmploymentStatus.NOTICE_PERIOD,
                "separation_date": str(payload.separation_date),
                "separation_reason": payload.separation_reason,
            },
            reason=f"Separation initiated: {payload.separation_reason}",
            authorized_by_user_id=author_user_id,
        )
        db.add(history)

        # Create offboarding case
        case_in = WorkforceLifecycleCaseCreate(
            employee_id=payload.employee_id,
            case_type=LifecycleCaseType.OFFBOARDING,
            target_date=payload.separation_date,
            notes=payload.notes,
        )
        return await self.create_lifecycle_case(db, tenant_id, case_in, author_user_id)

    # =========================================================================
    # 3. LEAVE ENGINE: TYPES & POLICIES
    # =========================================================================

    async def create_leave_type(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: WorkforceLeaveTypeCreate,
    ) -> WorkforceLeaveTypeResponse:
        """Register an institutional leave type."""
        code_res = await db.execute(
            select(WorkforceLeaveType).where(
                WorkforceLeaveType.tenant_id == tenant_id,
                WorkforceLeaveType.code == payload.code.upper(),
            )
        )
        if code_res.scalar_one_or_none():
            raise ConflictException("WorkforceLeaveType", "code", payload.code)

        lt = WorkforceLeaveType(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            code=payload.code.upper(),
            name=payload.name,
            description=payload.description,
            is_paid=payload.is_paid,
            is_active=payload.is_active,
        )
        db.add(lt)
        await db.commit()
        return WorkforceLeaveTypeResponse.model_validate(lt)

    async def list_leave_types(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        active_only: bool = True,
    ) -> list[WorkforceLeaveTypeResponse]:
        """List leave types in tenant."""
        stmt = select(WorkforceLeaveType).where(WorkforceLeaveType.tenant_id == tenant_id)
        if active_only:
            stmt = stmt.where(WorkforceLeaveType.is_active.is_(True))
        stmt = stmt.order_by(WorkforceLeaveType.code.asc())
        res = await db.execute(stmt)
        return [WorkforceLeaveTypeResponse.model_validate(lt) for lt in res.scalars().all()]

    async def create_leave_policy(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: WorkforceLeavePolicyCreate,
    ) -> WorkforceLeavePolicyResponse:
        """Create versioned leave entitlement policy."""
        lt_res = await db.execute(
            select(WorkforceLeaveType).where(
                WorkforceLeaveType.id == payload.leave_type_id,
                WorkforceLeaveType.tenant_id == tenant_id,
            )
        )
        lt = lt_res.scalar_one_or_none()
        if not lt:
            raise NotFoundException("WorkforceLeaveType", payload.leave_type_id)

        pol = WorkforceLeavePolicy(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            leave_type_id=payload.leave_type_id,
            policy_code=payload.policy_code,
            name=payload.name,
            version=1,
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
            applicable_employment_types=payload.applicable_employment_types,
            applicable_departments=payload.applicable_departments,
            annual_entitlement=payload.annual_entitlement,
            accrual_frequency=payload.accrual_frequency,
            accrual_rate=payload.accrual_rate,
            carry_forward_max=payload.carry_forward_max,
            expiry_months=payload.expiry_months,
            max_consecutive_days=payload.max_consecutive_days,
            requires_document=payload.requires_document,
            document_mandatory_after_days=payload.document_mandatory_after_days,
            allow_half_day=payload.allow_half_day,
            is_active=payload.is_active,
        )
        db.add(pol)
        await db.commit()
        return WorkforceLeavePolicyResponse(
            id=pol.id,
            tenant_id=pol.tenant_id,
            leave_type_id=pol.leave_type_id,
            leave_type_name=lt.name,
            policy_code=pol.policy_code,
            name=pol.name,
            version=pol.version,
            effective_from=pol.effective_from,
            effective_to=pol.effective_to,
            applicable_employment_types=pol.applicable_employment_types,
            applicable_departments=pol.applicable_departments,
            annual_entitlement=pol.annual_entitlement,
            accrual_frequency=pol.accrual_frequency,
            accrual_rate=pol.accrual_rate,
            carry_forward_max=pol.carry_forward_max,
            expiry_months=pol.expiry_months,
            max_consecutive_days=pol.max_consecutive_days,
            requires_document=pol.requires_document,
            document_mandatory_after_days=pol.document_mandatory_after_days,
            allow_half_day=pol.allow_half_day,
            is_active=pol.is_active,
            created_at=pol.created_at,
        )

    async def list_leave_policies(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        leave_type_id: UUID | None = None,
    ) -> list[WorkforceLeavePolicyResponse]:
        """List leave policies."""
        stmt = (
            select(WorkforceLeavePolicy)
            .options(selectinload(WorkforceLeavePolicy.leave_type))
            .where(WorkforceLeavePolicy.tenant_id == tenant_id)
        )
        if leave_type_id:
            stmt = stmt.where(WorkforceLeavePolicy.leave_type_id == leave_type_id)
        stmt = stmt.order_by(WorkforceLeavePolicy.effective_from.desc())
        res = await db.execute(stmt)
        return [
            WorkforceLeavePolicyResponse(
                id=p.id,
                tenant_id=p.tenant_id,
                leave_type_id=p.leave_type_id,
                leave_type_name=p.leave_type.name if p.leave_type else None,
                policy_code=p.policy_code,
                name=p.name,
                version=p.version,
                effective_from=p.effective_from,
                effective_to=p.effective_to,
                applicable_employment_types=p.applicable_employment_types,
                applicable_departments=p.applicable_departments,
                annual_entitlement=p.annual_entitlement,
                accrual_frequency=p.accrual_frequency,
                accrual_rate=p.accrual_rate,
                carry_forward_max=p.carry_forward_max,
                expiry_months=p.expiry_months,
                max_consecutive_days=p.max_consecutive_days,
                requires_document=p.requires_document,
                document_mandatory_after_days=p.document_mandatory_after_days,
                allow_half_day=p.allow_half_day,
                is_active=p.is_active,
                created_at=p.created_at,
            )
            for p in res.scalars().all()
        ]

    # =========================================================================
    # 4. LEAVE BALANCES & TRANSACTIONS
    # =========================================================================

    async def get_or_create_leave_balance(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        employee_id: UUID,
        leave_type_id: UUID,
        calendar_year: int,
        author_user_id: UUID,
    ) -> WorkforceLeaveBalance:
        """Fetch balance or initialize with annual entitlement from active policy."""
        stmt = select(WorkforceLeaveBalance).where(
            WorkforceLeaveBalance.tenant_id == tenant_id,
            WorkforceLeaveBalance.employee_id == employee_id,
            WorkforceLeaveBalance.leave_type_id == leave_type_id,
            WorkforceLeaveBalance.calendar_year == calendar_year,
        )
        res = await db.execute(stmt)
        balance = res.scalar_one_or_none()
        if balance:
            return balance

        # Lookup employee and matching policy
        emp_res = await db.execute(select(WorkforceEmployee).where(WorkforceEmployee.id == employee_id))
        emp = emp_res.scalar_one_or_none()
        if not emp:
            raise NotFoundException("WorkforceEmployee", employee_id)

        pol_res = await db.execute(
            select(WorkforceLeavePolicy).where(
                WorkforceLeavePolicy.tenant_id == tenant_id,
                WorkforceLeavePolicy.leave_type_id == leave_type_id,
                WorkforceLeavePolicy.is_active.is_(True),
            )
        )
        policy = pol_res.scalars().first()
        entitlement = policy.annual_entitlement if policy else Decimal("12.00")
        initial_accrual = entitlement if (not policy or policy.accrual_frequency == LeaveAccrualFrequency.ANNUAL) else Decimal("0.00")

        balance = WorkforceLeaveBalance(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            employee_id=employee_id,
            leave_type_id=leave_type_id,
            calendar_year=calendar_year,
            entitled_days=entitlement,
            accrued_days=initial_accrual,
            carried_forward_days=Decimal("0.00"),
            used_days=Decimal("0.00"),
            pending_days=Decimal("0.00"),
            adjusted_days=Decimal("0.00"),
            expired_days=Decimal("0.00"),
        )
        db.add(balance)

        # Record initial grant ledger entry
        tx = WorkforceLeaveBalanceTransaction(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            balance_id=balance.id,
            transaction_type=LeaveTransactionType.ANNUAL_GRANT,
            amount=initial_accrual,
            running_balance=initial_accrual,
            reference_type="ANNUAL_INITIALIZATION",
            reference_id=str(calendar_year),
            reason=f"Annual leave entitlement initialization for year {calendar_year}",
            created_by_user_id=author_user_id,
        )
        db.add(tx)
        await db.commit()
        return balance

    async def list_leave_balances(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        employee_id: UUID | None = None,
        calendar_year: int | None = None,
    ) -> list[WorkforceLeaveBalanceResponse]:
        """List leave balances with calculation."""
        year = calendar_year or date.today().year
        stmt = (
            select(WorkforceLeaveBalance)
            .options(
                selectinload(WorkforceLeaveBalance.employee).selectinload(WorkforceEmployee.user),
                selectinload(WorkforceLeaveBalance.leave_type),
            )
            .where(
                WorkforceLeaveBalance.tenant_id == tenant_id,
                WorkforceLeaveBalance.calendar_year == year,
            )
        )
        if employee_id:
            stmt = stmt.where(WorkforceLeaveBalance.employee_id == employee_id)

        res = await db.execute(stmt)
        balances = res.scalars().all()

        return [
            WorkforceLeaveBalanceResponse(
                id=b.id,
                tenant_id=b.tenant_id,
                employee_id=b.employee_id,
                employee_name=f"{b.employee.user.first_name} {b.employee.user.last_name}" if b.employee and b.employee.user else None,
                employee_number=b.employee.employee_number if b.employee else None,
                leave_type_id=b.leave_type_id,
                leave_type_code=b.leave_type.code if b.leave_type else None,
                leave_type_name=b.leave_type.name if b.leave_type else None,
                calendar_year=b.calendar_year,
                entitled_days=b.entitled_days,
                accrued_days=b.accrued_days,
                carried_forward_days=b.carried_forward_days,
                used_days=b.used_days,
                pending_days=b.pending_days,
                adjusted_days=b.adjusted_days,
                expired_days=b.expired_days,
                available_days=b.available_days,
            )
            for b in balances
        ]

    async def adjust_leave_balance(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: WorkforceLeaveBalanceAdjustRequest,
        author_user_id: UUID,
    ) -> WorkforceLeaveBalanceResponse:
        """Manual balance adjustment with mandatory reason and immutable audit transaction."""
        balance = await self.get_or_create_leave_balance(
            db,
            tenant_id,
            payload.employee_id,
            payload.leave_type_id,
            payload.calendar_year,
            author_user_id,
        )

        balance.adjusted_days += payload.adjustment_days
        new_available = balance.available_days

        tx = WorkforceLeaveBalanceTransaction(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            balance_id=balance.id,
            transaction_type=LeaveTransactionType.ADJUSTMENT,
            amount=payload.adjustment_days,
            running_balance=new_available,
            reference_type="MANUAL_ADJUSTMENT",
            reference_id=str(uuid.uuid4()),
            reason=payload.reason,
            created_by_user_id=author_user_id,
        )
        db.add(tx)
        await db.commit()

        # Reload with relationships
        bal_res = await db.execute(
            select(WorkforceLeaveBalance)
            .options(
                selectinload(WorkforceLeaveBalance.employee).selectinload(WorkforceEmployee.user),
                selectinload(WorkforceLeaveBalance.leave_type),
            )
            .where(WorkforceLeaveBalance.id == balance.id)
        )
        b = bal_res.scalar_one()

        return WorkforceLeaveBalanceResponse(
            id=b.id,
            tenant_id=b.tenant_id,
            employee_id=b.employee_id,
            employee_name=f"{b.employee.user.first_name} {b.employee.user.last_name}" if b.employee and b.employee.user else None,
            employee_number=b.employee.employee_number if b.employee else None,
            leave_type_id=b.leave_type_id,
            leave_type_code=b.leave_type.code if b.leave_type else None,
            leave_type_name=b.leave_type.name if b.leave_type else None,
            calendar_year=b.calendar_year,
            entitled_days=b.entitled_days,
            accrued_days=b.accrued_days,
            carried_forward_days=b.carried_forward_days,
            used_days=b.used_days,
            pending_days=b.pending_days,
            adjusted_days=b.adjusted_days,
            expired_days=b.expired_days,
            available_days=b.available_days,
        )

    # =========================================================================
    # 5. LEAVE REQUESTS, APPROVALS & WORKFLOWS
    # =========================================================================

    async def submit_leave_request(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: WorkforceLeaveRequestCreate,
        current_user: User,
    ) -> WorkforceLeaveRequestResponse:
        """Submit employee leave application with concurrency and balance validation."""
        # 1. Resolve employee
        if payload.employee_id:
            emp_res = await db.execute(
                select(WorkforceEmployee).where(
                    WorkforceEmployee.id == payload.employee_id,
                    WorkforceEmployee.tenant_id == tenant_id,
                )
            )
            emp = emp_res.scalar_one_or_none()
        else:
            emp_res = await db.execute(
                select(WorkforceEmployee).where(
                    WorkforceEmployee.user_id == current_user.id,
                    WorkforceEmployee.tenant_id == tenant_id,
                )
            )
            emp = emp_res.scalar_one_or_none()

        if not emp:
            raise NotFoundException("WorkforceEmployee record for applicant not found")

        # 2. Date validation
        if payload.end_date < payload.start_date:
            raise BadRequestException("End date cannot be earlier than start date.")

        if payload.is_half_day:
            total_days = Decimal("0.50")
        else:
            diff_days = (payload.end_date - payload.start_date).days + 1
            total_days = Decimal(diff_days)

        # 3. Check for overlapping requests
        overlap_stmt = select(WorkforceLeaveRequest).where(
            WorkforceLeaveRequest.tenant_id == tenant_id,
            WorkforceLeaveRequest.employee_id == emp.id,
            WorkforceLeaveRequest.status.in_([LeaveRequestStatus.SUBMITTED, LeaveRequestStatus.APPROVED]),
            WorkforceLeaveRequest.start_date <= payload.end_date,
            WorkforceLeaveRequest.end_date >= payload.start_date,
        )
        overlap_res = await db.execute(overlap_stmt)
        if overlap_res.scalar_one_or_none():
            raise ConflictException("Employee already has an active or submitted leave request overlapping these dates.")

        # 4. Check & reserve balance
        balance = await self.get_or_create_leave_balance(
            db,
            tenant_id,
            emp.id,
            payload.leave_type_id,
            payload.start_date.year,
            current_user.id,
        )

        if balance.available_days < total_days:
            raise BadRequestException(
                f"Insufficient leave balance. Available: {balance.available_days} days, Requested: {total_days} days."
            )

        # Reserve balance
        balance.pending_days += total_days

        # 5. Create leave request
        request_number = f"LR-{payload.start_date.year}-{uuid.uuid4().hex[:6].upper()}"
        req = WorkforceLeaveRequest(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            employee_id=emp.id,
            leave_type_id=payload.leave_type_id,
            request_number=request_number,
            start_date=payload.start_date,
            end_date=payload.end_date,
            is_half_day=payload.is_half_day,
            half_day_session=payload.half_day_session,
            total_days=total_days,
            reason=payload.reason,
            supporting_document_url=payload.supporting_document_url,
            status=LeaveRequestStatus.SUBMITTED,
            submitted_at=datetime.now(UTC),
        )
        db.add(req)

        # 6. Add approval step (reporting manager or HOD)
        approver_id = None
        if emp.reporting_manager:
            approver_id = emp.reporting_manager.user_id

        step = WorkforceLeaveApprovalStep(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            request_id=req.id,
            step_number=1,
            approver_user_id=approver_id,
            approver_role="REPORTING_MANAGER" if approver_id else "HR_ADMIN",
            status=LifecycleTaskStatus.PENDING,
        )
        db.add(step)

        # 7. Check Timetable Conflicts for Instructional Faculty
        has_conflicts = False
        fac_res = await db.execute(select(FacultyProfile).where(FacultyProfile.user_id == emp.user_id))
        faculty = fac_res.scalar_one_or_none()
        if faculty:
            # Query sessions
            sessions_stmt = select(TimetableSession).where(
                TimetableSession.tenant_id == tenant_id,
                TimetableSession.faculty_id == faculty.id,
            )
            sess_res = await db.execute(sessions_stmt)
            sessions = sess_res.scalars().all()

            # Find matching days
            cur = payload.start_date
            while cur <= payload.end_date:
                weekday_num = cur.isoweekday()  # 1 = Mon ... 7 = Sun
                for s in sessions:
                    if s.day_of_week == weekday_num:
                        has_conflicts = True
                        db.add(
                            WorkforceAvailabilityConflict(
                                id=uuid.uuid4(),
                                tenant_id=tenant_id,
                                employee_id=emp.id,
                                leave_request_id=req.id,
                                conflict_date=cur,
                                timetable_session_id=s.id,
                                conflict_type="LEAVE_VS_TIMETABLE_SESSION",
                                severity="WARNING",
                            )
                        )
                cur += timedelta(days=1)

        await db.commit()
        return await self.get_leave_request_response(db, tenant_id, req.id)

    async def get_leave_request_response(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        request_id: UUID,
    ) -> WorkforceLeaveRequestResponse:
        """Fetch request details with approval steps and conflict indicator."""
        stmt = (
            select(WorkforceLeaveRequest)
            .options(
                selectinload(WorkforceLeaveRequest.employee).selectinload(WorkforceEmployee.user),
                selectinload(WorkforceLeaveRequest.employee).selectinload(WorkforceEmployee.department),
                selectinload(WorkforceLeaveRequest.leave_type),
                selectinload(WorkforceLeaveRequest.decided_by),
                selectinload(WorkforceLeaveRequest.approval_steps).selectinload(WorkforceLeaveApprovalStep.approver_user),
                selectinload(WorkforceLeaveRequest.conflicts),
            )
            .where(
                WorkforceLeaveRequest.id == request_id,
                WorkforceLeaveRequest.tenant_id == tenant_id,
            )
        )
        res = await db.execute(stmt)
        req = res.scalar_one_or_none()
        if not req:
            raise NotFoundException("WorkforceLeaveRequest", request_id)

        step_responses = [
            WorkforceLeaveApprovalStepResponse(
                id=s.id,
                tenant_id=s.tenant_id,
                request_id=s.request_id,
                step_number=s.step_number,
                approver_user_id=s.approver_user_id,
                approver_name=f"{s.approver_user.first_name} {s.approver_user.last_name}" if s.approver_user else None,
                approver_role=s.approver_role,
                status=s.status,
                comments=s.comments,
                decided_at=s.decided_at,
            )
            for s in req.approval_steps
        ]

        emp = req.employee
        return WorkforceLeaveRequestResponse(
            id=req.id,
            tenant_id=req.tenant_id,
            employee_id=req.employee_id,
            employee_name=f"{emp.user.first_name} {emp.user.last_name}" if emp and emp.user else None,
            employee_number=emp.employee_number if emp else None,
            department_name=emp.department.name if emp and emp.department else None,
            leave_type_id=req.leave_type_id,
            leave_type_code=req.leave_type.code if req.leave_type else None,
            leave_type_name=req.leave_type.name if req.leave_type else None,
            request_number=req.request_number,
            start_date=req.start_date,
            end_date=req.end_date,
            is_half_day=req.is_half_day,
            half_day_session=req.half_day_session,
            total_days=req.total_days,
            reason=req.reason,
            supporting_document_url=req.supporting_document_url,
            status=req.status,
            decision_reason=req.decision_reason,
            submitted_at=req.submitted_at,
            decided_at=req.decided_at,
            decided_by_user_id=req.decided_by_user_id,
            decided_by_name=f"{req.decided_by.first_name} {req.decided_by.last_name}" if req.decided_by else None,
            has_timetable_conflicts=len(req.conflicts) > 0,
            approval_steps=step_responses,
            created_at=req.created_at,
        )

    async def list_leave_requests(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        employee_id: UUID | None = None,
        status: str | None = None,
        department_id: UUID | None = None,
    ) -> list[WorkforceLeaveRequestResponse]:
        """List leave requests with optional filters."""
        query = (
            select(WorkforceLeaveRequest)
            .options(
                selectinload(WorkforceLeaveRequest.employee).selectinload(WorkforceEmployee.user),
                selectinload(WorkforceLeaveRequest.employee).selectinload(WorkforceEmployee.department),
                selectinload(WorkforceLeaveRequest.leave_type),
                selectinload(WorkforceLeaveRequest.decided_by),
                selectinload(WorkforceLeaveRequest.approval_steps).selectinload(WorkforceLeaveApprovalStep.approver_user),
                selectinload(WorkforceLeaveRequest.conflicts),
            )
            .where(WorkforceLeaveRequest.tenant_id == tenant_id)
        )

        if employee_id:
            query = query.where(WorkforceLeaveRequest.employee_id == employee_id)
        if status and status != "ALL":
            query = query.where(WorkforceLeaveRequest.status == status)
        if department_id:
            query = query.join(WorkforceLeaveRequest.employee).where(WorkforceEmployee.department_id == department_id)

        query = query.order_by(WorkforceLeaveRequest.submitted_at.desc())
        res = await db.execute(query)
        requests = res.scalars().all()

        results = []
        for req in requests:
            step_responses = [
                WorkforceLeaveApprovalStepResponse(
                    id=s.id,
                    tenant_id=s.tenant_id,
                    request_id=s.request_id,
                    step_number=s.step_number,
                    approver_user_id=s.approver_user_id,
                    approver_name=f"{s.approver_user.first_name} {s.approver_user.last_name}" if s.approver_user else None,
                    approver_role=s.approver_role,
                    status=s.status,
                    comments=s.comments,
                    decided_at=s.decided_at,
                )
                for s in req.approval_steps
            ]
            emp = req.employee
            results.append(
                WorkforceLeaveRequestResponse(
                    id=req.id,
                    tenant_id=req.tenant_id,
                    employee_id=req.employee_id,
                    employee_name=f"{emp.user.first_name} {emp.user.last_name}" if emp and emp.user else None,
                    employee_number=emp.employee_number if emp else None,
                    department_name=emp.department.name if emp and emp.department else None,
                    leave_type_id=req.leave_type_id,
                    leave_type_code=req.leave_type.code if req.leave_type else None,
                    leave_type_name=req.leave_type.name if req.leave_type else None,
                    request_number=req.request_number,
                    start_date=req.start_date,
                    end_date=req.end_date,
                    is_half_day=req.is_half_day,
                    half_day_session=req.half_day_session,
                    total_days=req.total_days,
                    reason=req.reason,
                    supporting_document_url=req.supporting_document_url,
                    status=req.status,
                    decision_reason=req.decision_reason,
                    submitted_at=req.submitted_at,
                    decided_at=req.decided_at,
                    decided_by_user_id=req.decided_by_user_id,
                    decided_by_name=f"{req.decided_by.first_name} {req.decided_by.last_name}" if req.decided_by else None,
                    has_timetable_conflicts=len(req.conflicts) > 0,
                    approval_steps=step_responses,
                    created_at=req.created_at,
                )
            )
        return results

    async def approve_leave_request(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        request_id: UUID,
        comments: str | None,
        author_user_id: UUID,
    ) -> WorkforceLeaveRequestResponse:
        """Approve leave request, consume balance, and record transaction."""
        req_res = await db.execute(
            select(WorkforceLeaveRequest)
            .options(
                selectinload(WorkforceLeaveRequest.employee),
                selectinload(WorkforceLeaveRequest.approval_steps),
            )
            .where(
                WorkforceLeaveRequest.id == request_id,
                WorkforceLeaveRequest.tenant_id == tenant_id,
            )
        )
        req = req_res.scalar_one_or_none()
        if not req:
            raise NotFoundException("WorkforceLeaveRequest", request_id)

        if req.status != LeaveRequestStatus.SUBMITTED:
            raise BadRequestException(f"Leave request is in status '{req.status}' and cannot be approved.")

        # Separation of duties: Prevent self-approval!
        if req.employee.user_id == author_user_id:
            raise BadRequestException("Self-approval is forbidden by institutional workforce policy.")

        # Consume balance: move from pending to used
        bal_stmt = select(WorkforceLeaveBalance).where(
            WorkforceLeaveBalance.tenant_id == tenant_id,
            WorkforceLeaveBalance.employee_id == req.employee_id,
            WorkforceLeaveBalance.leave_type_id == req.leave_type_id,
            WorkforceLeaveBalance.calendar_year == req.start_date.year,
        )
        bal_res = await db.execute(bal_stmt)
        balance = bal_res.scalar_one_or_none()
        if not balance:
            raise NotFoundException("Leave balance record not found for request year")

        balance.pending_days = max(Decimal("0.00"), balance.pending_days - req.total_days)
        balance.used_days += req.total_days

        # Record CONSUMPTION transaction
        tx = WorkforceLeaveBalanceTransaction(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            balance_id=balance.id,
            transaction_type=LeaveTransactionType.CONSUMPTION,
            amount=-req.total_days,
            running_balance=balance.available_days,
            reference_type="LEAVE_REQUEST",
            reference_id=str(req.id),
            reason=f"Leave consumption for request {req.request_number}",
            created_by_user_id=author_user_id,
        )
        db.add(tx)

        # Update steps and request
        for s in req.approval_steps:
            if s.status == LifecycleTaskStatus.PENDING:
                s.status = "APPROVED"
                s.comments = comments
                s.decided_at = datetime.now(UTC)

        req.status = LeaveRequestStatus.APPROVED
        req.decision_reason = comments
        req.decided_at = datetime.now(UTC)
        req.decided_by_user_id = author_user_id

        await db.commit()
        return await self.get_leave_request_response(db, tenant_id, req.id)

    async def reject_leave_request(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        request_id: UUID,
        reason: str,
        author_user_id: UUID,
    ) -> WorkforceLeaveRequestResponse:
        """Reject leave application and release reserved balance."""
        req_res = await db.execute(
            select(WorkforceLeaveRequest)
            .options(
                selectinload(WorkforceLeaveRequest.employee),
                selectinload(WorkforceLeaveRequest.approval_steps),
            )
            .where(
                WorkforceLeaveRequest.id == request_id,
                WorkforceLeaveRequest.tenant_id == tenant_id,
            )
        )
        req = req_res.scalar_one_or_none()
        if not req:
            raise NotFoundException("WorkforceLeaveRequest", request_id)

        if req.status != LeaveRequestStatus.SUBMITTED:
            raise BadRequestException(f"Leave request is in status '{req.status}' and cannot be rejected.")

        # Release reserved pending days
        bal_stmt = select(WorkforceLeaveBalance).where(
            WorkforceLeaveBalance.tenant_id == tenant_id,
            WorkforceLeaveBalance.employee_id == req.employee_id,
            WorkforceLeaveBalance.leave_type_id == req.leave_type_id,
            WorkforceLeaveBalance.calendar_year == req.start_date.year,
        )
        bal_res = await db.execute(bal_stmt)
        balance = bal_res.scalar_one_or_none()
        if balance:
            balance.pending_days = max(Decimal("0.00"), balance.pending_days - req.total_days)

        # Update steps and request
        for s in req.approval_steps:
            if s.status == LifecycleTaskStatus.PENDING:
                s.status = "REJECTED"
                s.comments = reason
                s.decided_at = datetime.now(UTC)

        req.status = LeaveRequestStatus.REJECTED
        req.decision_reason = reason
        req.decided_at = datetime.now(UTC)
        req.decided_by_user_id = author_user_id

        await db.commit()
        return await self.get_leave_request_response(db, tenant_id, req.id)

    async def cancel_or_withdraw_leave_request(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        request_id: UUID,
        reason: str,
        author_user_id: UUID,
    ) -> WorkforceLeaveRequestResponse:
        """Cancel an approved leave or withdraw a pending application."""
        req_res = await db.execute(
            select(WorkforceLeaveRequest).where(
                WorkforceLeaveRequest.id == request_id,
                WorkforceLeaveRequest.tenant_id == tenant_id,
            )
        )
        req = req_res.scalar_one_or_none()
        if not req:
            raise NotFoundException("WorkforceLeaveRequest", request_id)

        bal_stmt = select(WorkforceLeaveBalance).where(
            WorkforceLeaveBalance.tenant_id == tenant_id,
            WorkforceLeaveBalance.employee_id == req.employee_id,
            WorkforceLeaveBalance.leave_type_id == req.leave_type_id,
            WorkforceLeaveBalance.calendar_year == req.start_date.year,
        )
        bal_res = await db.execute(bal_stmt)
        balance = bal_res.scalar_one_or_none()

        if req.status == LeaveRequestStatus.SUBMITTED:
            # Release pending days
            if balance:
                balance.pending_days = max(Decimal("0.00"), balance.pending_days - req.total_days)
            req.status = LeaveRequestStatus.WITHDRAWN
        elif req.status == LeaveRequestStatus.APPROVED:
            # Reverse consumption
            if balance:
                balance.used_days = max(Decimal("0.00"), balance.used_days - req.total_days)
                tx = WorkforceLeaveBalanceTransaction(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    balance_id=balance.id,
                    transaction_type=LeaveTransactionType.REVERSAL,
                    amount=req.total_days,
                    running_balance=balance.available_days,
                    reference_type="LEAVE_CANCELLATION",
                    reference_id=str(req.id),
                    reason=f"Leave cancelled: {reason}",
                    created_by_user_id=author_user_id,
                )
                db.add(tx)
            req.status = LeaveRequestStatus.CANCELLED
        else:
            raise BadRequestException(f"Cannot cancel or withdraw request in '{req.status}' state.")

        req.decision_reason = reason
        await db.commit()
        return await self.get_leave_request_response(db, tenant_id, req.id)

    async def get_leave_calendar(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        start_date: date,
        end_date: date,
        department_id: UUID | None = None,
        campus_id: UUID | None = None,
    ) -> list[WorkforceLeaveCalendarEntry]:
        """Authorized privacy-preserving absence calendar."""
        query = (
            select(WorkforceLeaveRequest)
            .options(
                selectinload(WorkforceLeaveRequest.employee).selectinload(WorkforceEmployee.user),
                selectinload(WorkforceLeaveRequest.employee).selectinload(WorkforceEmployee.department),
                selectinload(WorkforceLeaveRequest.leave_type),
            )
            .where(
                WorkforceLeaveRequest.tenant_id == tenant_id,
                WorkforceLeaveRequest.status == LeaveRequestStatus.APPROVED,
                WorkforceLeaveRequest.start_date <= end_date,
                WorkforceLeaveRequest.end_date >= start_date,
            )
        )

        if department_id:
            query = query.join(WorkforceLeaveRequest.employee).where(WorkforceEmployee.department_id == department_id)
        if campus_id:
            query = query.join(WorkforceLeaveRequest.employee).where(WorkforceEmployee.campus_id == campus_id)

        res = await db.execute(query)
        requests = res.scalars().all()

        entries = []
        for req in requests:
            cur = max(start_date, req.start_date)
            term = min(end_date, req.end_date)
            while cur <= term:
                entries.append(
                    WorkforceLeaveCalendarEntry(
                        date=cur,
                        employee_id=req.employee_id,
                        employee_name=f"{req.employee.user.first_name} {req.employee.user.last_name}" if req.employee and req.employee.user else "Staff Member",
                        department_name=req.employee.department.name if req.employee and req.employee.department else None,
                        leave_type_code=req.leave_type.code,
                        leave_type_name=req.leave_type.name,
                        is_half_day=req.is_half_day,
                        half_day_session=req.half_day_session,
                        status=req.status,
                    )
                )
                cur += timedelta(days=1)

        return entries

    # =========================================================================
    # 6. WORKFORCE AVAILABILITY & TIMETABLE CONFLICTS
    # =========================================================================

    async def check_availability(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        employee_id: UUID,
        start_date: date,
        end_date: date,
    ) -> WorkforceAvailabilityCheckResponse:
        """Check employee absence and academic timetable scheduling conflicts."""
        emp_res = await db.execute(
            select(WorkforceEmployee)
            .options(selectinload(WorkforceEmployee.user))
            .where(
                WorkforceEmployee.id == employee_id,
                WorkforceEmployee.tenant_id == tenant_id,
            )
        )
        emp = emp_res.scalar_one_or_none()
        if not emp:
            raise NotFoundException("WorkforceEmployee", employee_id)

        # 1. Approved & pending leaves
        leaves_stmt = select(WorkforceLeaveRequest).where(
            WorkforceLeaveRequest.tenant_id == tenant_id,
            WorkforceLeaveRequest.employee_id == employee_id,
            WorkforceLeaveRequest.status.in_([LeaveRequestStatus.SUBMITTED, LeaveRequestStatus.APPROVED]),
            WorkforceLeaveRequest.start_date <= end_date,
            WorkforceLeaveRequest.end_date >= start_date,
        )
        leaves_res = await db.execute(leaves_stmt)
        leaves = leaves_res.scalars().all()

        approved_days: set[date] = set()
        pending_days: set[date] = set()
        for l in leaves:
            c = max(start_date, l.start_date)
            t = min(end_date, l.end_date)
            while c <= t:
                if l.status == LeaveRequestStatus.APPROVED:
                    approved_days.add(c)
                else:
                    pending_days.add(c)
                c += timedelta(days=1)

        # 2. Timetable conflicts
        conflicts = []
        fac_res = await db.execute(select(FacultyProfile).where(FacultyProfile.user_id == emp.user_id))
        faculty = fac_res.scalar_one_or_none()
        if faculty:
            sessions_stmt = (
                select(TimetableSession)
                .options(selectinload(TimetableSession.course_offering).selectinload(CourseOffering.subject))
                .where(
                    TimetableSession.tenant_id == tenant_id,
                    TimetableSession.faculty_id == faculty.id,
                )
            )
            sess_res = await db.execute(sessions_stmt)
            sessions = sess_res.scalars().all()

            cur = start_date
            while cur <= end_date:
                if cur in approved_days or cur in pending_days:
                    w = cur.isoweekday()
                    for s in sessions:
                        if s.day_of_week == w:
                            course_code = "CLASS"
                            if s.course_offering and getattr(s.course_offering, "subject", None):
                                course_code = s.course_offering.subject.code
                            conflicts.append(
                                {
                                    "conflict_date": cur.isoformat(),
                                    "timetable_session_id": str(s.id),
                                    "course_code": course_code,
                                    "start_time": s.start_time.isoformat(),
                                    "end_time": s.end_time.isoformat(),
                                    "conflict_type": "LEAVE_VS_TIMETABLE_SESSION",
                                }
                            )
                cur += timedelta(days=1)

        is_available = len(approved_days) == 0 and len(conflicts) == 0
        status_label = (
            AvailabilityStatus.AVAILABLE
            if is_available
            else (
                AvailabilityStatus.SCHEDULING_CONFLICT
                if len(conflicts) > 0
                else AvailabilityStatus.ON_LEAVE
            )
        )

        emp_name = f"{emp.user.first_name} {emp.user.last_name}" if emp.user else "Employee"
        return WorkforceAvailabilityCheckResponse(
            employee_id=emp.id,
            employee_name=emp_name,
            status=status_label,
            is_available=is_available,
            approved_leave_days=sorted(list(approved_days)),
            pending_leave_days=sorted(list(pending_days)),
            timetable_session_conflicts=conflicts,
        )

    # =========================================================================
    # 7. WORKLOAD & WORKFORCE PLANNING
    # =========================================================================

    async def get_workload_summary(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        employee_id: UUID,
        academic_year_id: UUID | None = None,
        semester_id: UUID | None = None,
    ) -> WorkforceWorkloadSummaryResponse:
        """Calculate teaching duties from timetable sessions and compare with target workload."""
        emp_res = await db.execute(
            select(WorkforceEmployee)
            .options(
                selectinload(WorkforceEmployee.user),
                selectinload(WorkforceEmployee.department),
            )
            .where(
                WorkforceEmployee.id == employee_id,
                WorkforceEmployee.tenant_id == tenant_id,
            )
        )
        emp = emp_res.scalar_one_or_none()
        if not emp:
            raise NotFoundException("WorkforceEmployee", employee_id)

        # 1. Fetch expectation
        exp_stmt = select(WorkforceWorkloadExpectation).where(
            WorkforceWorkloadExpectation.tenant_id == tenant_id,
            WorkforceWorkloadExpectation.employee_id == employee_id,
        )
        if academic_year_id:
            exp_stmt = exp_stmt.where(WorkforceWorkloadExpectation.academic_year_id == academic_year_id)
        exp_res = await db.execute(exp_stmt)
        expectation = exp_res.scalars().first()
        expected_hours = expectation.total_expected_hours_per_week if expectation else Decimal("34.00")

        # 2. Fetch scheduled teaching hours from timetable_sessions
        teaching_hours = Decimal("0.00")
        sessions_count = 0
        fac_res = await db.execute(select(FacultyProfile).where(FacultyProfile.user_id == emp.user_id))
        faculty = fac_res.scalar_one_or_none()
        if faculty:
            sess_stmt = select(TimetableSession).where(
                TimetableSession.tenant_id == tenant_id,
                TimetableSession.faculty_id == faculty.id,
            )
            sess_res = await db.execute(sess_stmt)
            sessions = sess_res.scalars().all()
            sessions_count = len(sessions)

            for s in sessions:
                # Calculate hours from start_time and end_time
                duration_minutes = (s.end_time.hour * 60 + s.end_time.minute) - (s.start_time.hour * 60 + s.start_time.minute)
                teaching_hours += Decimal(duration_minutes) / Decimal(60)

        # 3. Fetch adjustments
        adj_stmt = select(WorkforceWorkloadAdjustment).where(
            WorkforceWorkloadAdjustment.tenant_id == tenant_id,
            WorkforceWorkloadAdjustment.employee_id == employee_id,
        )
        adj_res = await db.execute(adj_stmt)
        adjustments = adj_res.scalars().all()
        adj_hours = sum((a.adjusted_hours_per_week for a in adjustments), Decimal("0.00"))

        # Other base expectations (research + admin) if expectation exists
        other_hours = (expectation.research_hours_per_week + expectation.admin_hours_per_week) if expectation else Decimal("14.00")
        total_actual = teaching_hours + other_hours + adj_hours
        variance = total_actual - expected_hours

        if total_actual > expected_hours + Decimal("4.00"):
            load_status = "OVERLOAD"
        elif total_actual < expected_hours - Decimal("4.00"):
            load_status = "UNDER_ALLOCATED"
        else:
            load_status = "BALANCED"

        emp_name = f"{emp.user.first_name} {emp.user.last_name}" if emp.user else "Employee"
        return WorkforceWorkloadSummaryResponse(
            employee_id=emp.id,
            employee_name=emp_name,
            employee_number=emp.employee_number,
            department_name=emp.department.name if emp.department else None,
            academic_year_id=academic_year_id,
            semester_id=semester_id,
            expected_hours=expected_hours.quantize(Decimal("0.01")),
            scheduled_teaching_hours=teaching_hours.quantize(Decimal("0.01")),
            adjusted_hours=adj_hours.quantize(Decimal("0.01")),
            total_actual_hours=total_actual.quantize(Decimal("0.01")),
            variance_hours=variance.quantize(Decimal("0.01")),
            load_status=load_status,
            sessions_count=sessions_count,
        )

    async def create_workload_expectation(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: WorkforceWorkloadExpectationCreate,
    ) -> WorkforceWorkloadExpectationResponse:
        """Create workload target."""
        total = (
            payload.teaching_hours_per_week
            + payload.research_hours_per_week
            + payload.admin_hours_per_week
            + payload.exam_hours_per_week
        )
        exp = WorkforceWorkloadExpectation(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            employee_id=payload.employee_id,
            academic_year_id=payload.academic_year_id,
            semester_id=payload.semester_id,
            teaching_hours_per_week=payload.teaching_hours_per_week,
            research_hours_per_week=payload.research_hours_per_week,
            admin_hours_per_week=payload.admin_hours_per_week,
            exam_hours_per_week=payload.exam_hours_per_week,
            total_expected_hours_per_week=total,
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
            notes=payload.notes,
        )
        db.add(exp)
        await db.commit()
        return WorkforceWorkloadExpectationResponse(
            id=exp.id,
            tenant_id=exp.tenant_id,
            employee_id=exp.employee_id,
            academic_year_id=exp.academic_year_id,
            semester_id=exp.semester_id,
            teaching_hours_per_week=exp.teaching_hours_per_week,
            research_hours_per_week=exp.research_hours_per_week,
            admin_hours_per_week=exp.admin_hours_per_week,
            exam_hours_per_week=exp.exam_hours_per_week,
            total_expected_hours_per_week=exp.total_expected_hours_per_week,
            effective_from=exp.effective_from,
            effective_to=exp.effective_to,
            notes=exp.notes,
            created_at=exp.created_at,
        )

    create_or_update_workload_expectation = create_workload_expectation

    async def create_workload_adjustment(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: WorkforceWorkloadAdjustmentCreate,
        author_user_id: UUID,
    ) -> WorkforceWorkloadAdjustmentResponse:
        """Record authorized workload concession or duty credit."""
        adj = WorkforceWorkloadAdjustment(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            employee_id=payload.employee_id,
            category=payload.category,
            adjusted_hours_per_week=payload.adjusted_hours_per_week,
            reason=payload.reason,
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
            authorized_by_user_id=author_user_id,
        )
        db.add(adj)
        await db.commit()
        return WorkforceWorkloadAdjustmentResponse(
            id=adj.id,
            tenant_id=adj.tenant_id,
            employee_id=adj.employee_id,
            category=adj.category,
            adjusted_hours_per_week=adj.adjusted_hours_per_week,
            reason=adj.reason,
            effective_from=adj.effective_from,
            effective_to=adj.effective_to,
            authorized_by_user_id=adj.authorized_by_user_id,
            created_at=adj.created_at,
        )

    # =========================================================================
    # 8. EMPLOYEE SELF-SERVICE & HR CASES
    # =========================================================================

    async def create_hr_case(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: WorkforceHRCaseCreate,
        current_user: User,
    ) -> WorkforceHRCaseResponse:
        """Submit HR service request or profile update approval."""
        if payload.employee_id:
            emp_id = payload.employee_id
        else:
            emp_res = await db.execute(
                select(WorkforceEmployee).where(
                    WorkforceEmployee.user_id == current_user.id,
                    WorkforceEmployee.tenant_id == tenant_id,
                )
            )
            emp = emp_res.scalar_one_or_none()
            if not emp:
                raise NotFoundException("WorkforceEmployee record for current user not found")
            emp_id = emp.id

        case_number = f"HRC-{date.today().year}-{uuid.uuid4().hex[:6].upper()}"
        hr_case = WorkforceHRCase(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            employee_id=emp_id,
            case_number=case_number,
            category=payload.category,
            priority=payload.priority,
            status=HRCaseStatus.OPEN,
            subject=payload.subject,
            description=payload.description,
            proposed_changes=payload.proposed_changes,
            is_confidential=payload.is_confidential,
        )
        db.add(hr_case)
        await db.commit()
        return await self.get_hr_case(db, tenant_id, hr_case.id)

    async def get_hr_case(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        case_id: UUID,
    ) -> WorkforceHRCaseResponse:
        """Get single HR case."""
        stmt = (
            select(WorkforceHRCase)
            .options(
                selectinload(WorkforceHRCase.employee).selectinload(WorkforceEmployee.user),
                selectinload(WorkforceHRCase.assigned_to),
            )
            .where(
                WorkforceHRCase.id == case_id,
                WorkforceHRCase.tenant_id == tenant_id,
            )
        )
        res = await db.execute(stmt)
        c = res.scalar_one_or_none()
        if not c:
            raise NotFoundException("WorkforceHRCase", case_id)

        emp = c.employee
        return WorkforceHRCaseResponse(
            id=c.id,
            tenant_id=c.tenant_id,
            employee_id=c.employee_id,
            employee_name=f"{emp.user.first_name} {emp.user.last_name}" if emp and emp.user else None,
            employee_number=emp.employee_number if emp else None,
            case_number=c.case_number,
            category=c.category,
            priority=c.priority,
            status=c.status,
            subject=c.subject,
            description=c.description,
            proposed_changes=c.proposed_changes,
            is_confidential=c.is_confidential,
            assigned_to_user_id=c.assigned_to_user_id,
            assigned_to_name=f"{c.assigned_to.first_name} {c.assigned_to.last_name}" if c.assigned_to else None,
            resolution=c.resolution,
            resolved_at=c.resolved_at,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )

    async def list_hr_cases(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        employee_id: UUID | None = None,
        category: str | None = None,
        status: str | None = None,
    ) -> list[WorkforceHRCaseResponse]:
        """List HR cases."""
        query = (
            select(WorkforceHRCase)
            .options(
                selectinload(WorkforceHRCase.employee).selectinload(WorkforceEmployee.user),
                selectinload(WorkforceHRCase.assigned_to),
            )
            .where(WorkforceHRCase.tenant_id == tenant_id)
        )
        if employee_id:
            query = query.where(WorkforceHRCase.employee_id == employee_id)
        if category:
            query = query.where(WorkforceHRCase.category == category)
        if status:
            query = query.where(WorkforceHRCase.status == status)

        query = query.order_by(WorkforceHRCase.created_at.desc())
        res = await db.execute(query)
        cases = res.scalars().all()

        return [
            WorkforceHRCaseResponse(
                id=c.id,
                tenant_id=c.tenant_id,
                employee_id=c.employee_id,
                employee_name=f"{c.employee.user.first_name} {c.employee.user.last_name}" if c.employee and c.employee.user else None,
                employee_number=c.employee.employee_number if c.employee else None,
                case_number=c.case_number,
                category=c.category,
                priority=c.priority,
                status=c.status,
                subject=c.subject,
                description=c.description,
                proposed_changes=c.proposed_changes,
                is_confidential=c.is_confidential,
                assigned_to_user_id=c.assigned_to_user_id,
                assigned_to_name=f"{c.assigned_to.first_name} {c.assigned_to.last_name}" if c.assigned_to else None,
                resolution=c.resolution,
                resolved_at=c.resolved_at,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in cases
        ]

    async def update_hr_case(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        case_id: UUID,
        payload: WorkforceHRCaseUpdate,
        author_user_id: UUID,
    ) -> WorkforceHRCaseResponse:
        """Update or resolve HR service case."""
        stmt = select(WorkforceHRCase).where(
            WorkforceHRCase.id == case_id,
            WorkforceHRCase.tenant_id == tenant_id,
        )
        res = await db.execute(stmt)
        c = res.scalar_one_or_none()
        if not c:
            raise NotFoundException("WorkforceHRCase", case_id)

        if payload.status:
            c.status = payload.status
            if payload.status in (HRCaseStatus.RESOLVED, HRCaseStatus.CLOSED):
                c.resolved_at = datetime.now(UTC)
                c.resolution = payload.resolution or c.resolution
        if payload.priority:
            c.priority = payload.priority
        if payload.assigned_to_user_id is not None:
            c.assigned_to_user_id = payload.assigned_to_user_id
        if payload.resolution:
            c.resolution = payload.resolution

        await db.commit()
        return await self.get_hr_case(db, tenant_id, c.id)

    # =========================================================================
    # 9. REPORTING & ANALYTICS
    # =========================================================================

    async def get_headcount_report(
        self,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> WorkforceHeadcountReport:
        """Aggregate workforce composition metrics."""
        stmt = (
            select(WorkforceEmployee)
            .options(selectinload(WorkforceEmployee.department))
            .where(WorkforceEmployee.tenant_id == tenant_id)
        )
        res = await db.execute(stmt)
        employees = res.scalars().all()

        total = len(employees)
        active = sum(1 for e in employees if e.employment_status == EmploymentStatus.ACTIVE)
        onboarding = sum(1 for e in employees if e.employment_status == EmploymentStatus.ONBOARDING)
        on_leave = sum(1 for e in employees if e.employment_status == EmploymentStatus.ON_LEAVE)
        notice = sum(1 for e in employees if e.employment_status == EmploymentStatus.NOTICE_PERIOD)
        separated = sum(1 for e in employees if e.employment_status == EmploymentStatus.SEPARATED)

        # By department
        dept_counts: dict[str, int] = {}
        for e in employees:
            d_name = e.department.name if e.department else "Unassigned"
            dept_counts[d_name] = dept_counts.get(d_name, 0) + 1

        by_dept = [{"department": k, "headcount": v} for k, v in dept_counts.items()]

        # By type
        type_counts: dict[str, int] = {}
        for e in employees:
            type_counts[e.employment_type] = type_counts.get(e.employment_type, 0) + 1
        by_type = [{"employment_type": k, "count": v} for k, v in type_counts.items()]

        # By status
        status_counts: dict[str, int] = {}
        for e in employees:
            status_counts[e.employment_status] = status_counts.get(e.employment_status, 0) + 1
        by_status = [{"status": k, "count": v} for k, v in status_counts.items()]

        return WorkforceHeadcountReport(
            total_headcount=total,
            active_count=active,
            onboarding_count=onboarding,
            on_leave_count=on_leave,
            notice_period_count=notice,
            separated_count=separated,
            by_department=by_dept,
            by_employment_type=by_type,
            by_status=by_status,
        )

    async def get_leave_utilization_report(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        calendar_year: int | None = None,
    ) -> WorkforceLeaveUtilizationReport:
        """Aggregate leave utilization."""
        year = calendar_year or date.today().year

        stmt = (
            select(WorkforceLeaveRequest)
            .options(
                selectinload(WorkforceLeaveRequest.leave_type),
                selectinload(WorkforceLeaveRequest.employee).selectinload(WorkforceEmployee.department),
            )
            .where(
                WorkforceLeaveRequest.tenant_id == tenant_id,
            )
        )
        res = await db.execute(stmt)
        requests = res.scalars().all()

        total_days = Decimal("0.00")
        pending_count = 0
        type_utilization: dict[str, Decimal] = {}
        dept_utilization: dict[str, Decimal] = {}

        for r in requests:
            if r.status == LeaveRequestStatus.SUBMITTED:
                pending_count += 1
            elif r.status == LeaveRequestStatus.APPROVED:
                total_days += r.total_days
                t_name = r.leave_type.name if r.leave_type else "Leave"
                type_utilization[t_name] = type_utilization.get(t_name, Decimal("0.00")) + r.total_days
                d_name = r.employee.department.name if r.employee and r.employee.department else "General"
                dept_utilization[d_name] = dept_utilization.get(d_name, Decimal("0.00")) + r.total_days

        return WorkforceLeaveUtilizationReport(
            total_leave_days_taken=total_days,
            pending_approval_count=pending_count,
            by_leave_type=[{"leave_type": k, "days_consumed": v} for k, v in type_utilization.items()],
            by_department=[{"department": k, "days_consumed": v} for k, v in dept_utilization.items()],
        )

    async def get_capacity_report(
        self,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> WorkforceCapacityReport:
        """Workload capacity and staffing gap analysis."""
        emp_stmt = select(WorkforceEmployee).where(
            WorkforceEmployee.tenant_id == tenant_id,
            WorkforceEmployee.employment_status == EmploymentStatus.ACTIVE,
        )
        emp_res = await db.execute(emp_stmt)
        employees = emp_res.scalars().all()

        overloaded = 0
        balanced = 0
        underutilized = 0

        dept_metrics: dict[str, dict[str, Any]] = {}

        for emp in employees:
            summary = await self.get_workload_summary(db, tenant_id, emp.id)
            if summary.load_status == "OVERLOAD":
                overloaded += 1
            elif summary.load_status == "UNDER_ALLOCATED":
                underutilized += 1
            else:
                balanced += 1

            d_name = summary.department_name or "General"
            if d_name not in dept_metrics:
                dept_metrics[d_name] = {
                    "department": d_name,
                    "staff_count": 0,
                    "total_expected_hours": Decimal("0.00"),
                    "total_scheduled_hours": Decimal("0.00"),
                }
            dept_metrics[d_name]["staff_count"] += 1
            dept_metrics[d_name]["total_expected_hours"] += summary.expected_hours
            dept_metrics[d_name]["total_scheduled_hours"] += summary.scheduled_teaching_hours

        return WorkforceCapacityReport(
            total_workforce_evaluated=len(employees),
            overloaded_staff_count=overloaded,
            balanced_staff_count=balanced,
            underutilized_staff_count=underutilized,
            department_metrics=list(dept_metrics.values()),
        )


workforce_service = WorkforceService()
