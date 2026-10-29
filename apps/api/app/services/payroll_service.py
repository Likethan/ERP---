"""CampusOS Enterprise Payroll, Compensation, Benefits & Statutory Compliance Service (Step 52).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

import secrets
import uuid
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    PermissionDeniedException,
)
from app.models.payroll import (
    CalculationMethod,
    ComponentType,
    EmployeeBankDetail,
    EmployeeCompensation,
    EmployeeCompensationHistory,
    PaymentBatchStatus,
    PayrollCalendar,
    PayrollJournalEntry,
    PayrollJournalLine,
    PayrollPaymentBatch,
    PayrollPaymentItem,
    PayrollPeriod,
    PayrollRun,
    PayrollRunItem,
    PayrollRunItemDetail,
    PayrollRunStatus,
    Payslip,
    SalaryComponent,
    SalaryGrade,
    SalaryStructure,
    SalaryStructureItem,
    StatutoryComplianceRule,
)
from app.models.workforce import (
    EmploymentStatus,
    LeaveRequestStatus,
    WorkforceEmployee,
    WorkforceLeaveRequest,
)
from app.schemas.payroll import (
    EmployeeBankDetailCreate,
    EmployeeBankDetailVerify,
    EmployeeCompensationCreate,
    PayrollCalendarCreate,
    PayrollPaymentBatchCreate,
    PayrollPaymentBatchReconcileRequest,
    PayrollPeriodCreate,
    PayrollRunCalculateRequest,
    PayrollRunCreate,
    SalaryComponentCreate,
    SalaryComponentUpdate,
    SalaryGradeCreate,
    SalaryGradeUpdate,
    SalaryStructureCreate,
    StatutoryComplianceRuleCreate,
)

TWOPLACES = Decimal("0.01")


def _round_currency(amount: Decimal) -> Decimal:
    """Deterministic rounding of monetary quantities."""
    return amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


class PayrollService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # =========================================================================
    # 1. SALARY GRADES & BANDS
    # =========================================================================

    async def create_salary_grade(
        self, tenant_id: UUID, payload: SalaryGradeCreate, actor_id: UUID | None = None
    ) -> SalaryGrade:
        stmt = select(SalaryGrade).where(
            SalaryGrade.tenant_id == tenant_id,
            SalaryGrade.code == payload.code.strip().upper(),
        )
        if (await self.session.execute(stmt)).scalar_one_or_none():
            raise ConflictException(f"Salary grade code '{payload.code}' already exists for this tenant.")

        if payload.max_base_pay < payload.min_base_pay:
            raise BadRequestException("Maximum salary cannot be less than minimum salary.")

        grade = SalaryGrade(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            code=payload.code.strip().upper(),
            name=payload.name.strip(),
            description=payload.description,
            min_base_pay=payload.min_base_pay,
            max_base_pay=payload.max_base_pay,
            is_active=payload.is_active,
        )
        self.session.add(grade)
        await self.session.commit()
        await self.session.refresh(grade)
        return grade

    async def list_salary_grades(
        self, tenant_id: UUID, is_active: bool | None = None
    ) -> list[SalaryGrade]:
        stmt = select(SalaryGrade).where(SalaryGrade.tenant_id == tenant_id)
        if is_active is not None:
            stmt = stmt.where(SalaryGrade.is_active == is_active)
        stmt = stmt.order_by(SalaryGrade.min_base_pay.asc())
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_salary_grade(self, tenant_id: UUID, grade_id: UUID) -> SalaryGrade:
        stmt = select(SalaryGrade).where(
            SalaryGrade.tenant_id == tenant_id,
            SalaryGrade.id == grade_id,
        )
        grade = (await self.session.execute(stmt)).scalar_one_or_none()
        if not grade:
            raise NotFoundException(f"Salary grade with id '{grade_id}' not found.")
        return grade

    async def update_salary_grade(
        self, tenant_id: UUID, grade_id: UUID, payload: SalaryGradeUpdate, actor_id: UUID | None = None
    ) -> SalaryGrade:
        grade = await self.get_salary_grade(tenant_id, grade_id)
        if payload.name is not None:
            grade.name = payload.name.strip()
        if payload.description is not None:
            grade.description = payload.description
        if payload.min_base_pay is not None:
            grade.min_base_pay = payload.min_base_pay
        if payload.max_base_pay is not None:
            grade.max_base_pay = payload.max_base_pay
        if payload.is_active is not None:
            grade.is_active = payload.is_active

        if grade.max_base_pay < grade.min_base_pay:
            raise BadRequestException("Maximum salary cannot be less than minimum salary.")

        await self.session.commit()
        await self.session.refresh(grade)
        return grade

    # =========================================================================
    # 2. SALARY COMPONENTS
    # =========================================================================

    async def create_salary_component(
        self, tenant_id: UUID, payload: SalaryComponentCreate, actor_id: UUID | None = None
    ) -> SalaryComponent:
        stmt = select(SalaryComponent).where(
            SalaryComponent.tenant_id == tenant_id,
            SalaryComponent.code == payload.code.strip().upper(),
        )
        if (await self.session.execute(stmt)).scalar_one_or_none():
            raise ConflictException(f"Salary component code '{payload.code}' already exists.")

        component = SalaryComponent(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            code=payload.code.strip().upper(),
            name=payload.name.strip(),
            description=payload.description,
            component_type=payload.component_type,
            calculation_method=payload.calculation_method,
            default_value=payload.default_value,
            is_statutory=payload.is_statutory,
            taxability=payload.taxability,
            is_recurring=payload.is_recurring,
            is_active=payload.is_active,
        )
        self.session.add(component)
        await self.session.commit()
        await self.session.refresh(component)
        return component

    async def list_salary_components(
        self, tenant_id: UUID, component_type: str | None = None, is_active: bool | None = None
    ) -> list[SalaryComponent]:
        stmt = select(SalaryComponent).where(SalaryComponent.tenant_id == tenant_id)
        if component_type:
            stmt = stmt.where(SalaryComponent.component_type == component_type)
        if is_active is not None:
            stmt = stmt.where(SalaryComponent.is_active == is_active)
        stmt = stmt.order_by(SalaryComponent.code.asc())
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_salary_component(self, tenant_id: UUID, component_id: UUID) -> SalaryComponent:
        stmt = select(SalaryComponent).where(
            SalaryComponent.tenant_id == tenant_id,
            SalaryComponent.id == component_id,
        )
        comp = (await self.session.execute(stmt)).scalar_one_or_none()
        if not comp:
            raise NotFoundException(f"Salary component '{component_id}' not found.")
        return comp

    async def update_salary_component(
        self, tenant_id: UUID, component_id: UUID, payload: SalaryComponentUpdate
    ) -> SalaryComponent:
        comp = await self.get_salary_component(tenant_id, component_id)
        if payload.name is not None:
            comp.name = payload.name.strip()
        if payload.description is not None:
            comp.description = payload.description
        if payload.component_type is not None:
            comp.component_type = payload.component_type
        if payload.calculation_method is not None:
            comp.calculation_method = payload.calculation_method
        if payload.default_value is not None:
            comp.default_value = payload.default_value
        if payload.is_statutory is not None:
            comp.is_statutory = payload.is_statutory
        if payload.taxability is not None:
            comp.taxability = payload.taxability
        if payload.is_recurring is not None:
            comp.is_recurring = payload.is_recurring
        if payload.is_active is not None:
            comp.is_active = payload.is_active

        await self.session.commit()
        await self.session.refresh(comp)
        return comp

    # =========================================================================
    # 3. SALARY STRUCTURES
    # =========================================================================

    async def create_salary_structure(
        self, tenant_id: UUID, payload: SalaryStructureCreate, actor_id: UUID | None = None
    ) -> SalaryStructure:
        stmt = select(SalaryStructure).where(
            SalaryStructure.tenant_id == tenant_id,
            SalaryStructure.code == payload.code.strip().upper(),
        )
        if (await self.session.execute(stmt)).scalar_one_or_none():
            raise ConflictException(f"Salary structure code '{payload.code}' already exists.")

        structure = SalaryStructure(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            code=payload.code.strip().upper(),
            name=payload.name.strip(),
            description=payload.description,
            currency=payload.currency.upper(),
            pay_frequency=payload.pay_frequency,
            version=1,
            is_active=payload.is_active,
        )
        self.session.add(structure)

        # Add structure items
        seq = 1
        for item_in in payload.items:
            await self.get_salary_component(tenant_id, item_in.component_id)
            item = SalaryStructureItem(
                id=uuid.uuid4(),
                structure_id=structure.id,
                component_id=item_in.component_id,
                calculation_method=item_in.calculation_method,
                factor_value=item_in.factor_value,
                fixed_amount=item_in.fixed_amount,
                sequence=item_in.sequence or seq,
            )
            self.session.add(item)
            seq += 1

        await self.session.commit()
        return await self.get_salary_structure(tenant_id, structure.id)

    async def list_salary_structures(
        self, tenant_id: UUID, is_active: bool | None = None
    ) -> list[SalaryStructure]:
        stmt = (
            select(SalaryStructure)
            .options(
                selectinload(SalaryStructure.items).selectinload(SalaryStructureItem.component),
            )
            .where(SalaryStructure.tenant_id == tenant_id)
        )
        if is_active is not None:
            stmt = stmt.where(SalaryStructure.is_active == is_active)
        stmt = stmt.order_by(SalaryStructure.code.asc())
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_salary_structure(self, tenant_id: UUID, structure_id: UUID) -> SalaryStructure:
        stmt = (
            select(SalaryStructure)
            .options(
                selectinload(SalaryStructure.items).selectinload(SalaryStructureItem.component),
            )
            .where(
                SalaryStructure.tenant_id == tenant_id,
                SalaryStructure.id == structure_id,
            )
        )
        structure = (await self.session.execute(stmt)).scalar_one_or_none()
        if not structure:
            raise NotFoundException(f"Salary structure '{structure_id}' not found.")
        return structure

    # =========================================================================
    # 4. EMPLOYEE COMPENSATION & REVISIONS
    # =========================================================================

    async def assign_employee_compensation(
        self, tenant_id: UUID, payload: EmployeeCompensationCreate, actor_id: UUID | None = None
    ) -> EmployeeCompensation:
        stmt_emp = select(WorkforceEmployee).where(
            WorkforceEmployee.tenant_id == tenant_id,
            WorkforceEmployee.id == payload.employee_id,
        )
        emp = (await self.session.execute(stmt_emp)).scalar_one_or_none()
        if not emp:
            raise NotFoundException(f"Employee with id '{payload.employee_id}' not found.")

        # Check existing active compensation
        stmt_curr = select(EmployeeCompensation).where(
            EmployeeCompensation.tenant_id == tenant_id,
            EmployeeCompensation.employee_id == payload.employee_id,
            EmployeeCompensation.is_active == True,
        )
        current_comp = (await self.session.execute(stmt_curr)).scalar_one_or_none()

        if current_comp:
            current_comp.is_active = False
            current_comp.effective_to = payload.effective_from

            # Log to compensation history
            history_entry = EmployeeCompensationHistory(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                employee_id=emp.id,
                compensation_id=current_comp.id,
                effective_date=payload.effective_from,
                previous_annual_ctc=current_comp.annual_ctc,
                new_annual_ctc=payload.annual_ctc,
                previous_monthly_gross=current_comp.monthly_gross,
                new_monthly_gross=payload.monthly_gross,
                change_reason=payload.notes or "Salary revision",
                authorized_by_user_id=actor_id or emp.user_id,
            )
            self.session.add(history_entry)

        new_comp = EmployeeCompensation(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            employee_id=payload.employee_id,
            structure_id=payload.structure_id,
            salary_grade_id=payload.salary_grade_id,
            annual_ctc=payload.annual_ctc,
            monthly_gross=payload.monthly_gross,
            base_pay=payload.base_pay,
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
            currency=payload.currency.upper(),
            custom_components=payload.custom_components or {},
            notes=payload.notes,
            is_active=True,
        )
        self.session.add(new_comp)
        await self.session.commit()
        return await self.get_employee_compensation(tenant_id, new_comp.id)

    async def get_employee_compensation(
        self, tenant_id: UUID, compensation_id: UUID
    ) -> EmployeeCompensation:
        stmt = (
            select(EmployeeCompensation)
            .options(
                selectinload(EmployeeCompensation.employee).selectinload(WorkforceEmployee.user),
                selectinload(EmployeeCompensation.structure).selectinload(SalaryStructure.items).selectinload(SalaryStructureItem.component),
                selectinload(EmployeeCompensation.salary_grade),
            )
            .where(
                EmployeeCompensation.tenant_id == tenant_id,
                EmployeeCompensation.id == compensation_id,
            )
        )
        comp = (await self.session.execute(stmt)).scalar_one_or_none()
        if not comp:
            raise NotFoundException(f"Compensation record '{compensation_id}' not found.")
        return comp

    async def get_current_employee_compensation(
        self, tenant_id: UUID, employee_id: UUID
    ) -> EmployeeCompensation | None:
        stmt = (
            select(EmployeeCompensation)
            .options(
                selectinload(EmployeeCompensation.employee).selectinload(WorkforceEmployee.user),
                selectinload(EmployeeCompensation.structure).selectinload(SalaryStructure.items).selectinload(SalaryStructureItem.component),
                selectinload(EmployeeCompensation.salary_grade),
            )
            .where(
                EmployeeCompensation.tenant_id == tenant_id,
                EmployeeCompensation.employee_id == employee_id,
                EmployeeCompensation.is_active == True,
            )
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_employee_compensations(
        self, tenant_id: UUID, employee_id: UUID | None = None
    ) -> list[EmployeeCompensation]:
        stmt = (
            select(EmployeeCompensation)
            .options(
                selectinload(EmployeeCompensation.employee).selectinload(WorkforceEmployee.user),
                selectinload(EmployeeCompensation.structure),
                selectinload(EmployeeCompensation.salary_grade),
            )
            .where(EmployeeCompensation.tenant_id == tenant_id)
        )
        if employee_id:
            stmt = stmt.where(EmployeeCompensation.employee_id == employee_id)
        stmt = stmt.order_by(desc(EmployeeCompensation.is_active), desc(EmployeeCompensation.effective_from))
        return list((await self.session.execute(stmt)).scalars().all())

    # =========================================================================
    # 5. EMPLOYEE BANK DETAILS & PRIVACY CONTROLS
    # =========================================================================

    def _mask_account_number(self, account_no: str) -> str:
        clean = account_no.strip()
        if len(clean) <= 4:
            return "****" + clean
        return "*" * (len(clean) - 4) + clean[-4:]

    async def set_employee_bank_details(
        self, tenant_id: UUID, payload: EmployeeBankDetailCreate, actor_id: UUID | None = None
    ) -> EmployeeBankDetail:
        stmt = select(EmployeeBankDetail).where(
            EmployeeBankDetail.tenant_id == tenant_id,
            EmployeeBankDetail.employee_id == payload.employee_id,
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()

        masked = self._mask_account_number(payload.account_number)

        if existing:
            existing.account_holder_name = payload.account_holder_name.strip()
            existing.bank_name = payload.bank_name.strip()
            existing.account_number_masked = masked
            existing.account_number_encrypted = f"enc:{payload.account_number.strip()}"
            existing.ifsc_code = payload.ifsc_code.strip()
            existing.branch_name = payload.branch_name.strip()
            existing.is_primary = payload.is_primary
            existing.is_verified = False
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        else:
            bank_detail = EmployeeBankDetail(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                employee_id=payload.employee_id,
                account_holder_name=payload.account_holder_name.strip(),
                bank_name=payload.bank_name.strip(),
                account_number_masked=masked,
                account_number_encrypted=f"enc:{payload.account_number.strip()}",
                ifsc_code=payload.ifsc_code.strip(),
                branch_name=payload.branch_name.strip(),
                is_primary=payload.is_primary,
                is_verified=False,
            )
            self.session.add(bank_detail)
            await self.session.commit()
            await self.session.refresh(bank_detail)
            return bank_detail

    async def get_employee_bank_details(
        self, tenant_id: UUID, employee_id: UUID
    ) -> EmployeeBankDetail | None:
        stmt = select(EmployeeBankDetail).where(
            EmployeeBankDetail.tenant_id == tenant_id,
            EmployeeBankDetail.employee_id == employee_id,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def verify_employee_bank_details(
        self, tenant_id: UUID, employee_id: UUID, payload: EmployeeBankDetailVerify, actor_id: UUID | None = None
    ) -> EmployeeBankDetail:
        bank = await self.get_employee_bank_details(tenant_id, employee_id)
        if not bank:
            raise NotFoundException(f"Bank details for employee '{employee_id}' not found.")

        bank.is_verified = payload.is_verified
        bank.verified_by_user_id = actor_id
        bank.verified_at = datetime.now(UTC)

        await self.session.commit()
        await self.session.refresh(bank)
        return bank

    # =========================================================================
    # 6. STATUTORY COMPLIANCE RULES
    # =========================================================================

    async def create_statutory_rule(
        self, tenant_id: UUID, payload: StatutoryComplianceRuleCreate, actor_id: UUID | None = None
    ) -> StatutoryComplianceRule:
        stmt = select(StatutoryComplianceRule).where(
            StatutoryComplianceRule.tenant_id == tenant_id,
            StatutoryComplianceRule.rule_code == payload.rule_code.strip().upper(),
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing:
            # Update existing rule
            existing.title = payload.title.strip()
            existing.description = payload.description
            existing.employee_rate = payload.employee_rate
            existing.employer_rate = payload.employer_rate
            existing.wage_ceiling = payload.wage_ceiling
            existing.effective_from = payload.effective_from
            existing.effective_to = payload.effective_to
            existing.slab_configuration = payload.slab_configuration or []
            existing.is_active = payload.is_active
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

        rule = StatutoryComplianceRule(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            jurisdiction=payload.jurisdiction,
            rule_code=payload.rule_code.strip().upper(),
            title=payload.title.strip(),
            description=payload.description,
            employee_rate=payload.employee_rate,
            employer_rate=payload.employer_rate,
            wage_ceiling=payload.wage_ceiling,
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
            slab_configuration=payload.slab_configuration or [],
            is_active=payload.is_active,
        )
        self.session.add(rule)
        await self.session.commit()
        await self.session.refresh(rule)
        return rule

    async def list_statutory_rules(
        self, tenant_id: UUID, is_active: bool | None = None, jurisdiction: str | None = None
    ) -> list[StatutoryComplianceRule]:
        stmt = select(StatutoryComplianceRule).where(StatutoryComplianceRule.tenant_id == tenant_id)
        if is_active is not None:
            stmt = stmt.where(StatutoryComplianceRule.is_active == is_active)
        if jurisdiction:
            stmt = stmt.where(StatutoryComplianceRule.jurisdiction == jurisdiction)
        stmt = stmt.order_by(StatutoryComplianceRule.rule_code.asc())
        return list((await self.session.execute(stmt)).scalars().all())

    # =========================================================================
    # 7. PAYROLL CALENDARS & PERIODS
    # =========================================================================

    async def create_payroll_calendar(
        self, tenant_id: UUID, payload: PayrollCalendarCreate, actor_id: UUID | None = None
    ) -> PayrollCalendar:
        stmt = select(PayrollCalendar).where(
            PayrollCalendar.tenant_id == tenant_id,
            PayrollCalendar.name == payload.name.strip(),
        )
        if (await self.session.execute(stmt)).scalar_one_or_none():
            raise ConflictException(f"Payroll calendar '{payload.name}' already exists.")

        cal = PayrollCalendar(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            name=payload.name.strip(),
            pay_frequency=payload.pay_frequency,
            cutoff_day_of_month=payload.cutoff_day_of_month,
            pay_day_of_month=payload.pay_day_of_month,
            is_active=payload.is_active,
        )
        self.session.add(cal)
        await self.session.commit()
        await self.session.refresh(cal)
        return cal

    async def list_payroll_calendars(
        self, tenant_id: UUID, is_active: bool | None = None
    ) -> list[PayrollCalendar]:
        stmt = select(PayrollCalendar).where(PayrollCalendar.tenant_id == tenant_id)
        if is_active is not None:
            stmt = stmt.where(PayrollCalendar.is_active == is_active)
        stmt = stmt.order_by(PayrollCalendar.name.asc())
        return list((await self.session.execute(stmt)).scalars().all())

    async def create_payroll_period(
        self, tenant_id: UUID, payload: PayrollPeriodCreate, actor_id: UUID | None = None
    ) -> PayrollPeriod:
        cal_stmt = select(PayrollCalendar).where(
            PayrollCalendar.tenant_id == tenant_id,
            PayrollCalendar.id == payload.calendar_id,
        )
        if not (await self.session.execute(cal_stmt)).scalar_one_or_none():
            raise NotFoundException(f"Calendar '{payload.calendar_id}' not found.")

        stmt = select(PayrollPeriod).where(
            PayrollPeriod.tenant_id == tenant_id,
            PayrollPeriod.calendar_id == payload.calendar_id,
            PayrollPeriod.period_code == payload.period_code.strip().upper(),
        )
        if (await self.session.execute(stmt)).scalar_one_or_none():
            raise ConflictException(f"Period code '{payload.period_code}' already exists for this calendar.")

        period = PayrollPeriod(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            calendar_id=payload.calendar_id,
            period_code=payload.period_code.strip().upper(),
            start_date=payload.start_date,
            end_date=payload.end_date,
            cutoff_date=payload.cutoff_date,
            is_closed=False,
        )
        self.session.add(period)
        await self.session.commit()
        await self.session.refresh(period)
        return period

    async def list_payroll_periods(
        self, tenant_id: UUID, calendar_id: UUID | None = None
    ) -> list[PayrollPeriod]:
        stmt = (
            select(PayrollPeriod)
            .options(selectinload(PayrollPeriod.calendar))
            .where(PayrollPeriod.tenant_id == tenant_id)
        )
        if calendar_id:
            stmt = stmt.where(PayrollPeriod.calendar_id == calendar_id)
        stmt = stmt.order_by(desc(PayrollPeriod.start_date))
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_payroll_period(self, tenant_id: UUID, period_id: UUID) -> PayrollPeriod:
        stmt = (
            select(PayrollPeriod)
            .options(selectinload(PayrollPeriod.calendar))
            .where(
                PayrollPeriod.tenant_id == tenant_id,
                PayrollPeriod.id == period_id,
            )
        )
        p = (await self.session.execute(stmt)).scalar_one_or_none()
        if not p:
            raise NotFoundException(f"Payroll period '{period_id}' not found.")
        return p

    # =========================================================================
    # 8. PAYROLL RUNS & PROCESSING
    # =========================================================================

    async def create_payroll_run(
        self, tenant_id: UUID, payload: PayrollRunCreate, actor_id: UUID | None = None
    ) -> PayrollRun:
        period = await self.get_payroll_period(tenant_id, payload.period_id)
        if period.is_closed:
            raise BadRequestException("Cannot create a payroll run for a closed period.")

        stmt_dup = select(PayrollRun).where(
            PayrollRun.tenant_id == tenant_id,
            PayrollRun.period_id == payload.period_id,
            PayrollRun.status.not_in([PayrollRunStatus.CANCELLED]),
        )
        if payload.department_id:
            stmt_dup = stmt_dup.where(PayrollRun.department_id == payload.department_id)
        existing_run = (await self.session.execute(stmt_dup)).scalar_one_or_none()
        if existing_run:
            raise ConflictException(f"A payroll run ({existing_run.run_number}) already exists for this period.")

        run_number = payload.run_number or f"PR-{period.period_code}-{secrets.token_hex(2).upper()}"

        run = PayrollRun(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            period_id=payload.period_id,
            calendar_id=payload.calendar_id,
            run_number=run_number,
            status=PayrollRunStatus.DRAFT,
            is_locked=False,
            department_id=payload.department_id,
            campus_id=payload.campus_id,
            total_gross_pay=Decimal("0.00"),
            total_deductions=Decimal("0.00"),
            total_employer_contributions=Decimal("0.00"),
            total_net_pay=Decimal("0.00"),
            employee_count=0,
        )
        self.session.add(run)
        await self.session.commit()
        return await self.get_payroll_run(tenant_id, run.id)

    async def get_payroll_run(self, tenant_id: UUID, run_id: UUID) -> PayrollRun:
        stmt = (
            select(PayrollRun)
            .options(
                selectinload(PayrollRun.period).selectinload(PayrollPeriod.calendar),
                selectinload(PayrollRun.items).selectinload(PayrollRunItem.employee).selectinload(WorkforceEmployee.user),
                selectinload(PayrollRun.items).selectinload(PayrollRunItem.details),
            )
            .where(
                PayrollRun.tenant_id == tenant_id,
                PayrollRun.id == run_id,
            )
        )
        run = (await self.session.execute(stmt)).scalar_one_or_none()
        if not run:
            raise NotFoundException(f"Payroll run '{run_id}' not found.")
        return run

    async def calculate_payroll_run(
        self, tenant_id: UUID, run_id: UUID, payload: PayrollRunCalculateRequest, actor_id: UUID | None = None
    ) -> PayrollRun:
        run = await self.get_payroll_run(tenant_id, run_id)

        if run.is_locked or run.status in [PayrollRunStatus.APPROVED, PayrollRunStatus.POSTED, PayrollRunStatus.PAID]:
            raise BadRequestException(f"Cannot recalculate payroll run in state '{run.status}'.")

        run.status = PayrollRunStatus.CALCULATING
        await self.session.flush()

        # Delete existing items for recalculation
        for itm in list(run.items):
            await self.session.delete(itm)
        run.items.clear()
        await self.session.flush()

        # Query eligible employees
        stmt_emp = (
            select(WorkforceEmployee)
            .options(selectinload(WorkforceEmployee.user))
            .where(
                WorkforceEmployee.tenant_id == tenant_id,
                WorkforceEmployee.employment_status.in_([
                    EmploymentStatus.ACTIVE,
                    EmploymentStatus.ON_LEAVE,
                    EmploymentStatus.NOTICE_PERIOD,
                ]),
            )
        )
        if run.department_id:
            stmt_emp = stmt_emp.where(WorkforceEmployee.department_id == run.department_id)
        if run.campus_id:
            stmt_emp = stmt_emp.where(WorkforceEmployee.campus_id == run.campus_id)

        eligible_employees = list((await self.session.execute(stmt_emp)).scalars().all())

        # Load statutory rules
        stmt_rules = select(StatutoryComplianceRule).where(
            StatutoryComplianceRule.tenant_id == tenant_id,
            StatutoryComplianceRule.is_active == True,
            StatutoryComplianceRule.effective_from <= run.period.end_date,
            or_(StatutoryComplianceRule.effective_to.is_(None), StatutoryComplianceRule.effective_to >= run.period.start_date),
        )
        statutory_rules = list((await self.session.execute(stmt_rules)).scalars().all())

        period_days = (run.period.end_date - run.period.start_date).days + 1
        period_days_dec = Decimal(period_days) if period_days > 0 else Decimal(30)

        total_gross = Decimal("0.00")
        total_ded = Decimal("0.00")
        total_emp_contrib = Decimal("0.00")
        total_net = Decimal("0.00")
        processed_count = 0

        for emp in eligible_employees:
            comp = await self.get_current_employee_compensation(tenant_id, emp.id)
            if not comp or comp.base_pay <= Decimal("0.00"):
                continue

            # Query unpaid leave from Step 51 workforce module
            stmt_unpaid = select(func.coalesce(func.sum(WorkforceLeaveRequest.total_days), Decimal("0.00"))).where(
                WorkforceLeaveRequest.tenant_id == tenant_id,
                WorkforceLeaveRequest.employee_id == emp.id,
                WorkforceLeaveRequest.status == LeaveRequestStatus.APPROVED,
                WorkforceLeaveRequest.start_date <= run.period.end_date,
                WorkforceLeaveRequest.end_date >= run.period.start_date,
                WorkforceLeaveRequest.leave_type.has(is_paid=False),
            )
            unpaid_days = (await self.session.execute(stmt_unpaid)).scalar() or Decimal("0.00")
            unpaid_days = Decimal(str(unpaid_days))

            # Proration factor
            worked_days = max(Decimal("0.00"), period_days_dec - unpaid_days)
            proration_factor = _round_currency(worked_days / period_days_dec)

            base_pay = comp.base_pay
            lop_amount = Decimal("0.00")
            if unpaid_days > Decimal("0.00"):
                lop_amount = _round_currency((base_pay / period_days_dec) * unpaid_days)

            earned_base = max(Decimal("0.00"), base_pay - lop_amount)
            emp_earnings = Decimal("0.00")
            emp_deductions = Decimal("0.00")
            emp_contrib = Decimal("0.00")
            details: list[PayrollRunItemDetail] = []

            # Structure components
            has_basic_item = False
            if comp.structure and comp.structure.items:
                for s_item in comp.structure.items:
                    c = s_item.component
                    if not c or not c.is_active:
                        continue

                    amt = Decimal("0.00")
                    if s_item.calculation_method == CalculationMethod.FLAT_AMOUNT:
                        amt = s_item.fixed_amount
                        if "BASIC" in c.code.upper() or "BASIC" in c.name.upper() or s_item.fixed_amount == comp.base_pay:
                            amt = max(Decimal("0.00"), amt - lop_amount)
                            has_basic_item = True
                    elif s_item.calculation_method == CalculationMethod.PERCENTAGE_OF_BASIC:
                        amt = (earned_base * s_item.factor_value) / Decimal(100)
                    amt = _round_currency(amt)

                    if c.component_type == ComponentType.EARNING:
                        emp_earnings += amt
                        details.append(
                            PayrollRunItemDetail(
                                id=uuid.uuid4(),
                                component_id=c.id,
                                component_name=c.name,
                                component_type=c.component_type,
                                amount=amt,
                            )
                        )
                    elif c.component_type == ComponentType.DEDUCTION:
                        emp_deductions += amt
                        details.append(
                            PayrollRunItemDetail(
                                id=uuid.uuid4(),
                                component_id=c.id,
                                component_name=c.name,
                                component_type=c.component_type,
                                amount=amt,
                            )
                        )

            if not has_basic_item and (not comp.structure or not comp.structure.items):
                emp_earnings += earned_base

            # Statutory deductions (e.g. PF, ESI)
            for rule in statutory_rules:
                basis = earned_base
                if rule.wage_ceiling > Decimal("0.00") and basis > rule.wage_ceiling:
                    basis = rule.wage_ceiling

                if rule.employee_rate > Decimal("0.0000"):
                    ee_amt = _round_currency(basis * rule.employee_rate)
                    emp_deductions += ee_amt
                if rule.employer_rate > Decimal("0.0000"):
                    er_amt = _round_currency(basis * rule.employer_rate)
                    emp_contrib += er_amt

            net_pay = max(Decimal("0.00"), emp_earnings - emp_deductions)

            run_item = PayrollRunItem(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                payroll_run_id=run.id,
                employee_id=emp.id,
                compensation_id=comp.id,
                days_in_period=period_days,
                worked_days=worked_days,
                paid_leave_days=Decimal("0.00"),
                unpaid_leave_days=unpaid_days,
                proration_factor=proration_factor,
                gross_earnings=emp_earnings,
                total_deductions=emp_deductions,
                employer_contributions=emp_contrib,
                net_pay=net_pay,
                calculation_breakdown={
                    "base_pay": str(base_pay),
                    "unpaid_days": str(unpaid_days),
                    "lop": str(lop_amount),
                },
            )
            for d in details:
                d.run_item_id = run_item.id
                self.session.add(d)

            run.items.append(run_item)
            self.session.add(run_item)

            total_gross += emp_earnings
            total_ded += emp_deductions
            total_emp_contrib += emp_contrib
            total_net += net_pay
            processed_count += 1

        run.total_gross_pay = total_gross
        run.total_deductions = total_ded
        run.total_employer_contributions = total_emp_contrib
        run.total_net_pay = total_net
        run.employee_count = processed_count
        run.status = PayrollRunStatus.CALCULATED

        await self.session.commit()
        return await self.get_payroll_run(tenant_id, run_id)

    async def approve_payroll_run(
        self, tenant_id: UUID, run_id: UUID, actor_id: UUID | None = None, notes: str | None = None
    ) -> PayrollRun:
        run = await self.get_payroll_run(tenant_id, run_id)

        if run.status not in [PayrollRunStatus.CALCULATED, PayrollRunStatus.PENDING_APPROVAL]:
            raise BadRequestException(f"Payroll run in status '{run.status}' cannot be approved.")

        # Separation of duties: Preparer cannot approve their own run
        if actor_id and hasattr(run, "created_by_user_id") and actor_id == run.created_by_user_id:
            raise PermissionDeniedException(
                "Separation of duties violation: Payroll preparer cannot approve their own payroll calculation."
            )

        run.status = PayrollRunStatus.APPROVED
        run.approved_by_user_id = actor_id
        run.approved_at = datetime.now(UTC)
        run.is_locked = True

        await self.session.commit()
        return await self.get_payroll_run(tenant_id, run_id)

    async def cancel_payroll_run(
        self, tenant_id: UUID, run_id: UUID, reason: str, actor_id: UUID | None = None
    ) -> PayrollRun:
        run = await self.get_payroll_run(tenant_id, run_id)
        if run.status in [PayrollRunStatus.POSTED, PayrollRunStatus.PAID]:
            raise BadRequestException(f"Cannot cancel payroll run in state '{run.status}'.")

        run.status = PayrollRunStatus.CANCELLED
        run.rejection_reason = reason

        await self.session.commit()
        return await self.get_payroll_run(tenant_id, run_id)

    # =========================================================================
    # 9. FINANCE & ACCOUNTING INTEGRATION (BALANCED DOUBLE-ENTRY JOURNALS)
    # =========================================================================

    async def post_payroll_to_accounting(
        self, tenant_id: UUID, run_id: UUID, posting_date: date | None = None, actor_id: UUID | None = None
    ) -> PayrollJournalEntry:
        # Idempotency check first
        stmt_exist = select(PayrollJournalEntry).options(selectinload(PayrollJournalEntry.lines)).where(
            PayrollJournalEntry.tenant_id == tenant_id,
            PayrollJournalEntry.payroll_run_id == run_id,
        )
        existing = (await self.session.execute(stmt_exist)).scalar_one_or_none()
        if existing:
            return existing

        run = await self.get_payroll_run(tenant_id, run_id)

        if run.status != PayrollRunStatus.APPROVED:
            raise BadRequestException(f"Only APPROVED payroll runs can be posted to accounting (current: {run.status}).")

        p_date = posting_date or date.today()
        entry_number = f"JRN-PAY-{run.run_number}"

        journal = PayrollJournalEntry(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            payroll_run_id=run.id,
            entry_number=entry_number,
            entry_date=p_date,
            is_balanced=True,
            posted_by_user_id=actor_id or uuid.uuid4(),
            posted_at=datetime.now(UTC),
            total_debit=run.total_gross_pay + run.total_employer_contributions,
            total_credit=run.total_net_pay + run.total_deductions + run.total_employer_contributions,
        )
        self.session.add(journal)

        # Debit Lines
        line1 = PayrollJournalLine(
            id=uuid.uuid4(),
            journal_entry_id=journal.id,
            account_code="EXP-SALARIES",
            account_name="Salaries & Wages Expense",
            line_type="DEBIT",
            amount=run.total_gross_pay,
            description="Gross payroll expense",
        )
        line2 = PayrollJournalLine(
            id=uuid.uuid4(),
            journal_entry_id=journal.id,
            account_code="EXP-STATUTORY",
            account_name="Employer Statutory Expense",
            line_type="DEBIT",
            amount=run.total_employer_contributions,
            description="Employer statutory contributions",
        )
        # Credit Lines
        line3 = PayrollJournalLine(
            id=uuid.uuid4(),
            journal_entry_id=journal.id,
            account_code="LIA-NET-PAY",
            account_name="Salaries Payable (Net)",
            line_type="CREDIT",
            amount=run.total_net_pay,
            description="Net salaries payable to employees",
        )
        line4 = PayrollJournalLine(
            id=uuid.uuid4(),
            journal_entry_id=journal.id,
            account_code="LIA-DEDUCTIONS",
            account_name="Statutory Deductions & Contributions Payable",
            line_type="CREDIT",
            amount=run.total_deductions + run.total_employer_contributions,
            description="Withholdings & statutory liabilities",
        )
        self.session.add_all([line1, line2, line3, line4])

        run.status = PayrollRunStatus.POSTED
        run.posted_by_user_id = actor_id
        run.posted_at = datetime.now(UTC)

        # Generate Payslips upon posting
        await self._generate_payslips_for_run(tenant_id, run)

        await self.session.commit()
        return journal

    async def get_payroll_journal_entry(
        self, tenant_id: UUID, run_id: UUID
    ) -> PayrollJournalEntry:
        stmt = (
            select(PayrollJournalEntry)
            .options(selectinload(PayrollJournalEntry.lines))
            .where(
                PayrollJournalEntry.tenant_id == tenant_id,
                PayrollJournalEntry.payroll_run_id == run_id,
            )
        )
        journal = (await self.session.execute(stmt)).scalar_one_or_none()
        if not journal:
            raise NotFoundException(f"No journal entry found for payroll run '{run_id}'.")
        return journal

    # =========================================================================
    # 10. PAYMENT DISBURSEMENT & BANK RECONCILIATION
    # =========================================================================

    async def create_payment_batch(
        self, tenant_id: UUID, payload: PayrollPaymentBatchCreate, actor_id: UUID | None = None
    ) -> PayrollPaymentBatch:
        run = await self.get_payroll_run(tenant_id, payload.payroll_run_id)
        if run.status not in [PayrollRunStatus.APPROVED, PayrollRunStatus.POSTED]:
            raise BadRequestException("Payment batch can only be prepared for APPROVED or POSTED payroll runs.")

        batch_number = f"BAT-PAY-{run.run_number}"

        batch_id = uuid.uuid4()
        batch = PayrollPaymentBatch(
            id=batch_id,
            tenant_id=tenant_id,
            payroll_run_id=run.id,
            batch_number=batch_number,
            payment_method=payload.payment_method,
            status=PaymentBatchStatus.PREPARED,
            total_amount=run.total_net_pay,
            total_records=len(run.items),
            export_format=payload.export_format,
        )
        self.session.add(batch)

        for item in run.items:
            bank = await self.get_employee_bank_details(tenant_id, item.employee_id)
            pay_item = PayrollPaymentItem(
                id=uuid.uuid4(),
                batch_id=batch_id,
                employee_id=item.employee_id,
                run_item_id=item.id,
                amount=item.net_pay,
                bank_name=bank.bank_name if bank else "Manual Bank",
                account_number_masked=bank.account_number_masked if bank else "********0000",
                ifsc_code=bank.ifsc_code if bank else "MANUAL0001",
                status="PENDING",
            )
            batch.items.append(pay_item)
            self.session.add(pay_item)

        await self.session.commit()
        return await self.get_payment_batch(tenant_id, batch_id)

    async def get_payment_batch(self, tenant_id: UUID, batch_id: UUID) -> PayrollPaymentBatch:
        stmt = (
            select(PayrollPaymentBatch)
            .options(selectinload(PayrollPaymentBatch.items))
            .where(
                PayrollPaymentBatch.tenant_id == tenant_id,
                PayrollPaymentBatch.id == batch_id,
            )
        )
        batch = (await self.session.execute(stmt)).scalar_one_or_none()
        if not batch:
            raise NotFoundException(f"Payment batch '{batch_id}' not found.")
        return batch

    async def reconcile_payment_batch(
        self, tenant_id: UUID, batch_id: UUID, payload: PayrollPaymentBatchReconcileRequest, actor_id: UUID | None = None
    ) -> PayrollPaymentBatch:
        batch = await self.get_payment_batch(tenant_id, batch_id)

        all_reconciled = True
        for rec in payload.reconciled_items:
            stmt_item = select(PayrollPaymentItem).where(
                PayrollPaymentItem.id == rec.payment_item_id,
                PayrollPaymentItem.batch_id == batch_id,
            )
            item = (await self.session.execute(stmt_item)).scalar_one_or_none()
            if item:
                item.status = rec.status
                item.transaction_reference = rec.transaction_reference
                item.reconciled_at = datetime.now(UTC)
                if rec.status != "RECONCILED":
                    all_reconciled = False

        batch.status = PaymentBatchStatus.RECONCILED if all_reconciled else PaymentBatchStatus.PARTIALLY_RECONCILED

        run = await self.get_payroll_run(tenant_id, batch.payroll_run_id)
        if all_reconciled:
            run.status = PayrollRunStatus.PAID

        await self.session.commit()
        return await self.get_payment_batch(tenant_id, batch_id)

    # =========================================================================
    # 11. PAYSLIPS & EMPLOYEE SELF-SERVICE
    # =========================================================================

    async def _generate_payslips_for_run(self, tenant_id: UUID, run: PayrollRun) -> None:
        for item in run.items:
            stmt_exist = select(Payslip).where(Payslip.run_item_id == item.id)
            if (await self.session.execute(stmt_exist)).scalar_one_or_none():
                continue

            payslip_number = f"PS-{run.period.period_code}-{secrets.token_hex(3).upper()}"
            token = secrets.token_urlsafe(32)

            payslip = Payslip(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                payroll_run_id=run.id,
                run_item_id=item.id,
                employee_id=item.employee_id,
                payslip_number=payslip_number,
                period_code=run.period.period_code,
                gross_pay=item.gross_earnings,
                total_deductions=item.total_deductions,
                net_pay=item.net_pay,
                secure_token=token,
                storage_key=f"payslips/{run.period.period_code}/{payslip_number}.pdf",
                is_published=True,
            )
            self.session.add(payslip)

    async def list_employee_payslips(
        self, tenant_id: UUID, employee_id: UUID
    ) -> list[Payslip]:
        stmt = (
            select(Payslip)
            .where(
                Payslip.tenant_id == tenant_id,
                Payslip.employee_id == employee_id,
                Payslip.is_published == True,
            )
            .order_by(desc(Payslip.created_at))
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_payslip_by_token(self, token: str) -> Payslip:
        stmt = select(Payslip).where(Payslip.secure_token == token)
        payslip = (await self.session.execute(stmt)).scalar_one_or_none()
        if not payslip:
            raise NotFoundException("Payslip not found or invalid token.")
        return payslip
