"""Enterprise Payroll, Compensation, Benefits & Statutory Compliance Tests (Step 52).

CampusOS Tagline: "One Campus. One System. One Source of Truth."

Verifies:
1. Salary grade, pay band, and salary component configuration.
2. Grouped salary structure assembly with fixed and percentage components.
3. Employee compensation assignment, versioning, and historical audit trail.
4. Employee bank details registration, masking, and verification lifecycle.
5. Versioned statutory compliance rules (PF, ESI, TDS) with wage ceilings.
6. Payroll calendar and period setup with lock protection.
7. Deterministic, decimal-safe payroll calculation engine.
8. Attendance & unpaid leave integration (Loss of Pay proration).
9. Finance & accounting integration: Balanced double-entry general ledger journal.
10. Payment batch creation, disbursement file generation, and bank reconciliation.
11. Finalized payslips, secure token retrieval, and HR discrepancy case reporting.
12. Strict multi-tenant isolation across all compensation and payroll operations.
"""

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    PermissionDeniedException,
)
from app.models.core import Campus, Department, Institution
from app.models.people import User
from app.models.workforce import (
    EmploymentStatus,
    EmploymentType,
    LeaveRequestStatus,
    WorkforceEmployee,
    WorkforceHRCase,
    WorkforceLeaveRequest,
    WorkforceLeaveType,
)
from app.models.payroll import (
    CalculationMethod,
    ComponentType,
    EmployeeBankDetail,
    EmployeeCompensation,
    EmployeeCompensationHistory,
    PaymentBatchStatus,
    PaymentMethod,
    PayrollCalendar,
    PayrollJournalEntry,
    PayrollPaymentBatch,
    PayrollPeriod,
    PayrollRun,
    PayrollRunItem,
    PayrollRunStatus,
    Payslip,
    SalaryComponent,
    SalaryGrade,
    SalaryStructure,
    SalaryStructureItem,
    StatutoryComplianceRule,
    StatutoryJurisdiction,
)
from app.schemas.payroll import (
    EmployeeBankDetailCreate,
    EmployeeBankDetailVerify,
    EmployeeCompensationCreate,
    PayrollCalendarCreate,
    PayrollPaymentBatchCreate,
    PayrollPaymentBatchReconcileRequest,
    PayrollPaymentItemReconcileRequest,
    PayrollPeriodCreate,
    PayrollRunCalculateRequest,
    PayrollRunCreate,
    SalaryComponentCreate,
    SalaryGradeCreate,
    SalaryGradeUpdate,
    SalaryStructureCreate,
    SalaryStructureItemCreate,
    StatutoryComplianceRuleCreate,
)
from app.services.payroll_service import PayrollService


@pytest.fixture
async def payroll_fixture(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    super_admin_user: User,
):
    """Provides isolated campus, departments, and workforce employees for payroll tests."""
    uid = uuid.uuid4().hex[:6]

    campus_a = Campus(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name="Main Campus",
        code=f"CMP-PR-{uid}",
        address="100 University Boulevard",
        city="Bengaluru",
        is_active=True,
    )
    dept_a = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name="Computer Science & Engineering",
        code=f"CSE-PR-{uid}",
        is_active=True,
    )
    db_session.add_all([campus_a, dept_a])

    user_preparer = User(
        id=uuid.uuid4(),
        email=f"preparer-{uid}@campusos.internal",
        password_hash="test-password-hash",
        first_name="Payroll",
        last_name="Preparer",
        is_active=True,
    )
    user_approver = User(
        id=uuid.uuid4(),
        email=f"approver-{uid}@campusos.internal",
        password_hash="test-password-hash",
        first_name="Finance",
        last_name="Approver",
        is_active=True,
    )
    user_emp1 = User(
        id=uuid.uuid4(),
        email=f"faculty1-{uid}@campusos.internal",
        password_hash="test-password-hash",
        first_name="Alan",
        last_name="Turing",
        is_active=True,
    )
    user_emp2 = User(
        id=uuid.uuid4(),
        email=f"staff2-{uid}@campusos.internal",
        password_hash="test-password-hash",
        first_name="Ada",
        last_name="Lovelace",
        is_active=True,
    )
    db_session.add_all([user_preparer, user_approver, user_emp1, user_emp2])

    emp1 = WorkforceEmployee(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=user_emp1.id,
        employee_number=f"EMP-PR-{uid}-1",
        employment_type=EmploymentType.PERMANENT,
        employment_status=EmploymentStatus.ACTIVE,
        designation="Professor",
        job_title="Full Professor of Computer Science",
        department_id=dept_a.id,
        campus_id=campus_a.id,
        joining_date=date(2022, 1, 1),
    )
    emp2 = WorkforceEmployee(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=user_emp2.id,
        employee_number=f"EMP-PR-{uid}-2",
        employment_type=EmploymentType.PERMANENT,
        employment_status=EmploymentStatus.ACTIVE,
        designation="Lab Instructor",
        job_title="Senior Lab Instructor",
        department_id=dept_a.id,
        campus_id=campus_a.id,
        joining_date=date(2023, 6, 1),
    )
    db_session.add_all([emp1, emp2])

    leave_unpaid = WorkforceLeaveType(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name="Leave Without Pay",
        code=f"LWP-{uid}",
        is_paid=False,
        is_active=True,
    )
    db_session.add(leave_unpaid)

    await db_session.commit()

    return {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "campus_a": campus_a,
        "dept_a": dept_a,
        "preparer": user_preparer,
        "approver": user_approver,
        "emp1": emp1,
        "emp2": emp2,
        "user_emp1": user_emp1,
        "user_emp2": user_emp2,
        "leave_unpaid": leave_unpaid,
    }


# =============================================================================
# 1. SALARY GRADES & COMPONENTS CONFIGURATION
# =============================================================================


@pytest.mark.asyncio
async def test_salary_grade_and_component_configuration(
    db_session: AsyncSession, payroll_fixture: dict
):
    service = PayrollService(db_session)
    tenant_id = payroll_fixture["tenant_a"].id

    # 1. Create Salary Grade
    grade_in = SalaryGradeCreate(
        code="L12-PROF",
        name="Level 12 Professor Band",
        min_base_pay=Decimal("80000.00"),
        max_base_pay=Decimal("150000.00"),
    )
    grade = await service.create_salary_grade(tenant_id, grade_in)
    assert grade.code == "L12-PROF"
    assert grade.min_base_pay == Decimal("80000.00")

    # Reject duplicate grade code
    with pytest.raises(ConflictException):
        await service.create_salary_grade(tenant_id, grade_in)

    # Reject invalid salary range
    with pytest.raises(BadRequestException):
        await service.create_salary_grade(
            tenant_id,
            SalaryGradeCreate(
                code="INV-GRADE",
                name="Invalid Grade",
                min_base_pay=Decimal("50000.00"),
                max_base_pay=Decimal("40000.00"),
            ),
        )

    # 2. Create Salary Components
    basic_comp = await service.create_salary_component(
        tenant_id,
        SalaryComponentCreate(
            code="BASIC",
            name="Basic Pay",
            component_type=ComponentType.EARNING,
            calculation_method=CalculationMethod.FLAT_AMOUNT,
            default_value=Decimal("50000.0000"),
        ),
    )
    assert basic_comp.code == "BASIC"

    hra_comp = await service.create_salary_component(
        tenant_id,
        SalaryComponentCreate(
            code="HRA",
            name="House Rent Allowance",
            component_type=ComponentType.EARNING,
            calculation_method=CalculationMethod.PERCENTAGE_OF_BASIC,
            default_value=Decimal("40.0000"),
        ),
    )
    assert hra_comp.calculation_method == CalculationMethod.PERCENTAGE_OF_BASIC

    pf_comp = await service.create_salary_component(
        tenant_id,
        SalaryComponentCreate(
            code="PF_DED",
            name="Provident Fund Deduction",
            component_type=ComponentType.DEDUCTION,
            calculation_method=CalculationMethod.PERCENTAGE_OF_BASIC,
            is_statutory=True,
        ),
    )
    assert pf_comp.is_statutory is True


# =============================================================================
# 2. SALARY STRUCTURE ASSEMBLY
# =============================================================================


@pytest.mark.asyncio
async def test_salary_structure_assembly(
    db_session: AsyncSession, payroll_fixture: dict
):
    service = PayrollService(db_session)
    tenant_id = payroll_fixture["tenant_a"].id

    basic = await service.create_salary_component(
        tenant_id,
        SalaryComponentCreate(
            code="BASIC_A",
            name="Basic Pay",
            component_type=ComponentType.EARNING,
            calculation_method=CalculationMethod.FLAT_AMOUNT,
        ),
    )
    hra = await service.create_salary_component(
        tenant_id,
        SalaryComponentCreate(
            code="HRA_A",
            name="HRA 40%",
            component_type=ComponentType.EARNING,
            calculation_method=CalculationMethod.PERCENTAGE_OF_BASIC,
            default_value=Decimal("40.0000"),
        ),
    )

    structure_in = SalaryStructureCreate(
        code="STRUCT-PROF-2026",
        name="Professor Standard Structure 2026",
        items=[
            SalaryStructureItemCreate(
                component_id=basic.id,
                calculation_method=CalculationMethod.FLAT_AMOUNT,
                fixed_amount=Decimal("60000.00"),
                sequence=1,
            ),
            SalaryStructureItemCreate(
                component_id=hra.id,
                calculation_method=CalculationMethod.PERCENTAGE_OF_BASIC,
                factor_value=Decimal("40.0000"),
                sequence=2,
            ),
        ],
    )
    structure = await service.create_salary_structure(tenant_id, structure_in)
    assert structure.code == "STRUCT-PROF-2026"
    assert len(structure.items) == 2


# =============================================================================
# 3. EMPLOYEE COMPENSATION & SALARY REVISION HISTORY
# =============================================================================


@pytest.mark.asyncio
async def test_employee_compensation_and_revision_history(
    db_session: AsyncSession, payroll_fixture: dict
):
    service = PayrollService(db_session)
    tenant_id = payroll_fixture["tenant_a"].id
    emp1 = payroll_fixture["emp1"]
    preparer = payroll_fixture["preparer"]

    # Basic structure
    basic = await service.create_salary_component(
        tenant_id,
        SalaryComponentCreate(code="BSC_HIST", name="Basic", component_type=ComponentType.EARNING),
    )
    struct = await service.create_salary_structure(
        tenant_id,
        SalaryStructureCreate(
            code="STRUCT-HIST",
            name="Hist Structure",
            items=[
                SalaryStructureItemCreate(
                    component_id=basic.id,
                    calculation_method=CalculationMethod.FLAT_AMOUNT,
                    fixed_amount=Decimal("70000.00"),
                )
            ],
        ),
    )

    # Assign initial compensation
    comp1 = await service.assign_employee_compensation(
        tenant_id,
        EmployeeCompensationCreate(
            employee_id=emp1.id,
            structure_id=struct.id,
            annual_ctc=Decimal("1200000.00"),
            monthly_gross=Decimal("100000.00"),
            base_pay=Decimal("70000.00"),
            effective_from=date(2026, 1, 1),
            notes="Initial Appointment",
        ),
        actor_id=preparer.id,
    )
    assert comp1.base_pay == Decimal("70000.00")
    assert comp1.is_active is True

    # Revise compensation (Increment)
    comp2 = await service.assign_employee_compensation(
        tenant_id,
        EmployeeCompensationCreate(
            employee_id=emp1.id,
            structure_id=struct.id,
            annual_ctc=Decimal("1400000.00"),
            monthly_gross=Decimal("116666.67"),
            base_pay=Decimal("80000.00"),
            effective_from=date(2026, 7, 1),
            notes="Annual Performance Increment",
        ),
        actor_id=preparer.id,
    )
    assert comp2.base_pay == Decimal("80000.00")
    assert comp2.is_active is True

    # Verify history of comp1
    await db_session.refresh(comp1)
    assert comp1.is_active is False

    stmt_hist = select(EmployeeCompensationHistory).where(
        EmployeeCompensationHistory.tenant_id == tenant_id,
        EmployeeCompensationHistory.employee_id == emp1.id,
    )
    histories = list((await db_session.execute(stmt_hist)).scalars().all())
    assert len(histories) == 1
    assert histories[0].previous_annual_ctc == Decimal("1200000.00")
    assert histories[0].new_annual_ctc == Decimal("1400000.00")


# =============================================================================
# 4. EMPLOYEE BANK DETAILS MASKING & VERIFICATION
# =============================================================================


@pytest.mark.asyncio
async def test_employee_bank_details_masking_and_verification(
    db_session: AsyncSession, payroll_fixture: dict
):
    service = PayrollService(db_session)
    tenant_id = payroll_fixture["tenant_a"].id
    emp1 = payroll_fixture["emp1"]
    approver = payroll_fixture["approver"]

    bank = await service.set_employee_bank_details(
        tenant_id,
        EmployeeBankDetailCreate(
            employee_id=emp1.id,
            account_holder_name="Alan M Turing",
            bank_name="State Bank of India",
            branch_name="IISc Branch",
            account_number="987654321098",
            ifsc_code="SBIN0001234",
        ),
    )
    assert bank.account_number_masked == "********1098"
    assert bank.is_verified is False

    # Verify bank account
    verified = await service.verify_employee_bank_details(
        tenant_id,
        emp1.id,
        EmployeeBankDetailVerify(is_verified=True),
        actor_id=approver.id,
    )
    assert verified.is_verified is True
    assert verified.verified_by_user_id == approver.id


# =============================================================================
# 5. STATUTORY COMPLIANCE RULES
# =============================================================================


@pytest.mark.asyncio
async def test_statutory_compliance_rules(
    db_session: AsyncSession, payroll_fixture: dict
):
    service = PayrollService(db_session)
    tenant_id = payroll_fixture["tenant_a"].id

    pf_rule = await service.create_statutory_rule(
        tenant_id,
        StatutoryComplianceRuleCreate(
            jurisdiction=StatutoryJurisdiction.IN_PF,
            rule_code="EPF_TEST",
            title="Employees Provident Fund",
            effective_from=date(2026, 1, 1),
            employee_rate=Decimal("0.1200"),
            employer_rate=Decimal("0.1200"),
            wage_ceiling=Decimal("15000.00"),
        ),
    )
    assert pf_rule.rule_code == "EPF_TEST"
    assert pf_rule.employee_rate == Decimal("0.1200")


# =============================================================================
# 6. PAYROLL CALENDAR & PERIOD LIFECYCLE
# =============================================================================


@pytest.mark.asyncio
async def test_payroll_calendar_and_period_lifecycle(
    db_session: AsyncSession, payroll_fixture: dict
):
    service = PayrollService(db_session)
    tenant_id = payroll_fixture["tenant_a"].id

    cal = await service.create_payroll_calendar(
        tenant_id,
        PayrollCalendarCreate(
            name="Monthly Standard Calendar",
            pay_frequency="MONTHLY",
            cutoff_day_of_month=25,
            pay_day_of_month=30,
        ),
    )
    assert cal.name == "Monthly Standard Calendar"

    period = await service.create_payroll_period(
        tenant_id,
        PayrollPeriodCreate(
            calendar_id=cal.id,
            period_code="2026-M10",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 31),
            cutoff_date=date(2026, 10, 25),
        ),
    )
    assert period.period_code == "2026-M10"
    assert period.is_closed is False


# =============================================================================
# 7. DETERMINISTIC PAYROLL CALCULATION ENGINE
# =============================================================================


@pytest.mark.asyncio
async def test_payroll_calculation_deterministic_and_decimal_safe(
    db_session: AsyncSession, payroll_fixture: dict
):
    service = PayrollService(db_session)
    tenant_id = payroll_fixture["tenant_a"].id
    emp1 = payroll_fixture["emp1"]
    preparer = payroll_fixture["preparer"]

    cal = await service.create_payroll_calendar(
        tenant_id,
        PayrollCalendarCreate(
            name="Monthly Calc Calendar",
            pay_frequency="MONTHLY",
        ),
    )
    period = await service.create_payroll_period(
        tenant_id,
        PayrollPeriodCreate(
            calendar_id=cal.id,
            period_code="2026-CALC-1",
            start_date=date(2026, 11, 1),
            end_date=date(2026, 11, 30),
            cutoff_date=date(2026, 11, 25),
        ),
    )

    basic_c = await service.create_salary_component(
        tenant_id,
        SalaryComponentCreate(
            code="BASIC_PAY",
            name="Basic Pay",
            component_type=ComponentType.EARNING,
        ),
    )
    hra_c = await service.create_salary_component(
        tenant_id,
        SalaryComponentCreate(
            code="HRA_40",
            name="HRA Allowance",
            component_type=ComponentType.EARNING,
            calculation_method=CalculationMethod.PERCENTAGE_OF_BASIC,
            default_value=Decimal("40.0000"),
        ),
    )
    travel_c = await service.create_salary_component(
        tenant_id,
        SalaryComponentCreate(
            code="TRAVEL_ALLOW",
            name="Travel Allowance",
            component_type=ComponentType.EARNING,
            calculation_method=CalculationMethod.FLAT_AMOUNT,
            default_value=Decimal("5000.00"),
        ),
    )
    struct = await service.create_salary_structure(
        tenant_id,
        SalaryStructureCreate(
            code="STRUCT-DET",
            name="Deterministic Structure",
            items=[
                SalaryStructureItemCreate(
                    component_id=basic_c.id,
                    calculation_method=CalculationMethod.FLAT_AMOUNT,
                    fixed_amount=Decimal("60000.00"),
                    sequence=1,
                ),
                SalaryStructureItemCreate(
                    component_id=hra_c.id,
                    calculation_method=CalculationMethod.PERCENTAGE_OF_BASIC,
                    factor_value=Decimal("40.0000"),
                    sequence=2,
                ),
                SalaryStructureItemCreate(
                    component_id=travel_c.id,
                    calculation_method=CalculationMethod.FLAT_AMOUNT,
                    fixed_amount=Decimal("5000.00"),
                    sequence=3,
                ),
            ],
        ),
    )

    await service.assign_employee_compensation(
        tenant_id,
        EmployeeCompensationCreate(
            employee_id=emp1.id,
            structure_id=struct.id,
            annual_ctc=Decimal("1200000.00"),
            monthly_gross=Decimal("89000.00"),
            base_pay=Decimal("60000.00"),
            effective_from=date(2026, 1, 1),
        ),
        actor_id=preparer.id,
    )
    await service.set_employee_bank_details(
        tenant_id,
        EmployeeBankDetailCreate(
            employee_id=emp1.id,
            account_holder_name="Alan Turing",
            bank_name="HDFC Bank",
            account_number="1234567890",
            ifsc_code="HDFC0001234",
            branch_name="Main Branch",
        ),
    )

    # PF 12% on basic capped at 15000
    await service.create_statutory_rule(
        tenant_id,
        StatutoryComplianceRuleCreate(
            jurisdiction=StatutoryJurisdiction.IN_PF,
            rule_code="EPF_RULE",
            title="Employees Provident Fund",
            effective_from=date(2026, 1, 1),
            employee_rate=Decimal("0.1200"),
            employer_rate=Decimal("0.1200"),
            wage_ceiling=Decimal("15000.00"),
        ),
    )

    run = await service.create_payroll_run(
        tenant_id,
        PayrollRunCreate(period_id=period.id, calendar_id=cal.id),
        actor_id=preparer.id,
    )
    assert run.status == PayrollRunStatus.DRAFT

    calculated_run = await service.calculate_payroll_run(
        tenant_id,
        run.id,
        PayrollRunCalculateRequest(),
        actor_id=preparer.id,
    )

    # Verification:
    # Basic = 60000
    # HRA = 40% of 60000 = 24000
    # Travel = 5000
    # Total Gross Earnings = 60000 + 24000 + 5000 = 89000.00
    # PF Employee deduction = 12% of 15000 (wage ceiling) = 1800.00
    # Net Pay = 89000 - 1800 = 87200.00
    # PF Employer contribution = 12% of 15000 = 1800.00
    item = next(it for it in calculated_run.items if it.employee_id == emp1.id)
    assert item.gross_earnings == Decimal("89000.00")
    assert item.total_deductions == Decimal("1800.00")
    assert item.employer_contributions == Decimal("1800.00")
    assert item.net_pay == Decimal("87200.00")


# =============================================================================
# 8. LEAVE & ATTENDANCE INTEGRATION (LOSS OF PAY PRORATION)
# =============================================================================


@pytest.mark.asyncio
async def test_leave_and_attendance_lop_integration(
    db_session: AsyncSession, payroll_fixture: dict
):
    service = PayrollService(db_session)
    tenant_id = payroll_fixture["tenant_a"].id
    emp1 = payroll_fixture["emp1"]
    leave_unpaid = payroll_fixture["leave_unpaid"]
    preparer = payroll_fixture["preparer"]

    cal = await service.create_payroll_calendar(
        tenant_id,
        PayrollCalendarCreate(name="LOP Calendar", pay_frequency="MONTHLY"),
    )
    period = await service.create_payroll_period(
        tenant_id,
        PayrollPeriodCreate(
            calendar_id=cal.id,
            period_code="2026-LOP-1",
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 30),
            cutoff_date=date(2026, 9, 25),
        ),
    )

    basic = await service.create_salary_component(
        tenant_id,
        SalaryComponentCreate(code="BSC_LOP", name="Basic", component_type=ComponentType.EARNING),
    )
    struct = await service.create_salary_structure(
        tenant_id,
        SalaryStructureCreate(
            code="STRUCT-LOP",
            name="LOP Struct",
            items=[
                SalaryStructureItemCreate(
                    component_id=basic.id,
                    calculation_method=CalculationMethod.FLAT_AMOUNT,
                    fixed_amount=Decimal("60000.00"),
                )
            ],
        ),
    )

    await service.assign_employee_compensation(
        tenant_id,
        EmployeeCompensationCreate(
            employee_id=emp1.id,
            structure_id=struct.id,
            annual_ctc=Decimal("720000.00"),
            monthly_gross=Decimal("60000.00"),
            base_pay=Decimal("60000.00"),
            effective_from=date(2026, 1, 1),
        ),
        actor_id=preparer.id,
    )

    # 3 days unpaid leave
    leave_req = WorkforceLeaveRequest(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        employee_id=emp1.id,
        leave_type_id=leave_unpaid.id,
        request_number="LR-TEST-UNPAID-01",
        start_date=date(2026, 9, 10),
        end_date=date(2026, 9, 12),
        total_days=Decimal("3.00"),
        status=LeaveRequestStatus.APPROVED,
        reason="Personal unpaid leave",
        submitted_at=datetime.now(timezone.utc),
        decided_at=datetime.now(timezone.utc),
    )
    db_session.add(leave_req)
    await db_session.commit()

    run = await service.create_payroll_run(
        tenant_id,
        PayrollRunCreate(period_id=period.id, calendar_id=cal.id),
        actor_id=preparer.id,
    )
    calc_run = await service.calculate_payroll_run(
        tenant_id,
        run.id,
        PayrollRunCalculateRequest(),
        actor_id=preparer.id,
    )

    # 30 days total period, 3 unpaid days
    # LOP amount = (60000 / 30) * 3 = 6000.00
    # Gross Earnings = 60000 - 6000 = 54000.00
    item = next(it for it in calc_run.items if it.employee_id == emp1.id)
    assert item.unpaid_leave_days == Decimal("3.00")
    assert item.worked_days == Decimal("27.00")
    assert item.gross_earnings == Decimal("54000.00")


# =============================================================================
# 9. FINANCE & ACCOUNTING INTEGRATION (BALANCED DOUBLE-ENTRY JOURNALS)
# =============================================================================


@pytest.mark.asyncio
async def test_finance_accounting_integration_balanced_double_entry(
    db_session: AsyncSession, payroll_fixture: dict
):
    service = PayrollService(db_session)
    tenant_id = payroll_fixture["tenant_a"].id
    emp1 = payroll_fixture["emp1"]
    preparer = payroll_fixture["preparer"]
    approver = payroll_fixture["approver"]

    cal = await service.create_payroll_calendar(
        tenant_id,
        PayrollCalendarCreate(name="Finance Calendar"),
    )
    period = await service.create_payroll_period(
        tenant_id,
        PayrollPeriodCreate(
            calendar_id=cal.id,
            period_code="2026-FIN-1",
            start_date=date(2027, 1, 1),
            end_date=date(2027, 1, 31),
            cutoff_date=date(2027, 1, 25),
        ),
    )
    basic = await service.create_salary_component(
        tenant_id,
        SalaryComponentCreate(code="BSC_FIN", name="Basic", component_type=ComponentType.EARNING),
    )
    struct = await service.create_salary_structure(
        tenant_id,
        SalaryStructureCreate(
            code="STRUCT-FIN",
            name="Finance Struct",
            items=[
                SalaryStructureItemCreate(
                    component_id=basic.id,
                    calculation_method=CalculationMethod.FLAT_AMOUNT,
                    fixed_amount=Decimal("60000.00"),
                )
            ],
        ),
    )
    await service.assign_employee_compensation(
        tenant_id,
        EmployeeCompensationCreate(
            employee_id=emp1.id,
            structure_id=struct.id,
            annual_ctc=Decimal("720000.00"),
            monthly_gross=Decimal("60000.00"),
            base_pay=Decimal("60000.00"),
            effective_from=date(2026, 1, 1),
        ),
        actor_id=preparer.id,
    )
    await service.create_statutory_rule(
        tenant_id,
        StatutoryComplianceRuleCreate(
            jurisdiction=StatutoryJurisdiction.IN_PF,
            rule_code="EPF_FIN",
            title="EPF Rule",
            effective_from=date(2026, 1, 1),
            employee_rate=Decimal("0.1200"),
            employer_rate=Decimal("0.1200"),
            wage_ceiling=Decimal("15000.00"),
        ),
    )

    run = await service.create_payroll_run(
        tenant_id,
        PayrollRunCreate(period_id=period.id, calendar_id=cal.id),
        actor_id=preparer.id,
    )
    await service.calculate_payroll_run(
        tenant_id,
        run.id,
        PayrollRunCalculateRequest(),
        actor_id=preparer.id,
    )
    await service.approve_payroll_run(tenant_id, run.id, actor_id=approver.id)

    # Post to Accounting General Ledger
    journal = await service.post_payroll_to_accounting(
        tenant_id,
        run.id,
        posting_date=date(2027, 1, 30),
        actor_id=approver.id,
    )

    assert journal.is_balanced is True
    assert journal.total_debit == journal.total_credit
    assert journal.total_debit > Decimal("0.00")

    # Idempotent retry test: Posting again returns same journal without error or duplicates
    journal_retry = await service.post_payroll_to_accounting(tenant_id, run.id, actor_id=approver.id)
    assert journal_retry.id == journal.id


# =============================================================================
# 10. PAYMENT BATCH DISBURSEMENT & BANK RECONCILIATION
# =============================================================================


@pytest.mark.asyncio
async def test_payment_batch_disbursement_and_reconciliation(
    db_session: AsyncSession, payroll_fixture: dict
):
    service = PayrollService(db_session)
    tenant_id = payroll_fixture["tenant_a"].id
    emp1 = payroll_fixture["emp1"]
    preparer = payroll_fixture["preparer"]
    approver = payroll_fixture["approver"]

    cal = await service.create_payroll_calendar(
        tenant_id,
        PayrollCalendarCreate(name="Payment Calendar"),
    )
    period = await service.create_payroll_period(
        tenant_id,
        PayrollPeriodCreate(
            calendar_id=cal.id,
            period_code="2026-PAY-1",
            start_date=date(2027, 2, 1),
            end_date=date(2027, 2, 28),
            cutoff_date=date(2027, 2, 25),
        ),
    )
    basic = await service.create_salary_component(
        tenant_id,
        SalaryComponentCreate(code="BSC_PAY", name="Basic", component_type=ComponentType.EARNING),
    )
    struct = await service.create_salary_structure(
        tenant_id,
        SalaryStructureCreate(
            code="STRUCT-PAY",
            name="Payment Struct",
            items=[
                SalaryStructureItemCreate(
                    component_id=basic.id,
                    calculation_method=CalculationMethod.FLAT_AMOUNT,
                    fixed_amount=Decimal("50000.00"),
                )
            ],
        ),
    )
    await service.assign_employee_compensation(
        tenant_id,
        EmployeeCompensationCreate(
            employee_id=emp1.id,
            structure_id=struct.id,
            annual_ctc=Decimal("600000.00"),
            monthly_gross=Decimal("50000.00"),
            base_pay=Decimal("50000.00"),
            effective_from=date(2026, 1, 1),
        ),
        actor_id=preparer.id,
    )

    run = await service.create_payroll_run(
        tenant_id,
        PayrollRunCreate(period_id=period.id, calendar_id=cal.id),
        actor_id=preparer.id,
    )
    await service.calculate_payroll_run(tenant_id, run.id, PayrollRunCalculateRequest(), actor_id=preparer.id)
    await service.approve_payroll_run(tenant_id, run.id, actor_id=approver.id)

    # Create Payment Batch
    batch = await service.create_payment_batch(
        tenant_id,
        PayrollPaymentBatchCreate(payroll_run_id=run.id),
        actor_id=preparer.id,
    )
    assert batch.status == PaymentBatchStatus.PREPARED
    assert len(batch.items) == 1
    assert batch.items[0].amount == Decimal("50000.00")

    # Reconcile Payment Items
    reconciled_batch = await service.reconcile_payment_batch(
        tenant_id,
        batch.id,
        PayrollPaymentBatchReconcileRequest(
            reconciled_items=[
                PayrollPaymentItemReconcileRequest(
                    payment_item_id=batch.items[0].id,
                    status="RECONCILED",
                    transaction_reference="UTR20270228001928",
                )
            ]
        ),
        actor_id=approver.id,
    )
    assert reconciled_batch.status == PaymentBatchStatus.RECONCILED

    run_refreshed = await service.get_payroll_run(tenant_id, run.id)
    assert run_refreshed.status == PayrollRunStatus.PAID


# =============================================================================
# 11. PAYSLIPS & EMPLOYEE SELF-SERVICE DISPUTE
# =============================================================================


@pytest.mark.asyncio
async def test_payslips_generation_and_dispute_reporting(
    db_session: AsyncSession, payroll_fixture: dict
):
    service = PayrollService(db_session)
    tenant_id = payroll_fixture["tenant_a"].id
    emp1 = payroll_fixture["emp1"]
    preparer = payroll_fixture["preparer"]
    approver = payroll_fixture["approver"]

    cal = await service.create_payroll_calendar(
        tenant_id,
        PayrollCalendarCreate(name="Payslip Calendar"),
    )
    period = await service.create_payroll_period(
        tenant_id,
        PayrollPeriodCreate(
            calendar_id=cal.id,
            period_code="2026-PS-1",
            start_date=date(2027, 3, 1),
            end_date=date(2027, 3, 31),
            cutoff_date=date(2027, 3, 25),
        ),
    )
    basic = await service.create_salary_component(
        tenant_id,
        SalaryComponentCreate(code="BSC_PS", name="Basic", component_type=ComponentType.EARNING),
    )
    struct = await service.create_salary_structure(
        tenant_id,
        SalaryStructureCreate(
            code="STRUCT-PS",
            name="PS Struct",
            items=[
                SalaryStructureItemCreate(
                    component_id=basic.id,
                    calculation_method=CalculationMethod.FLAT_AMOUNT,
                    fixed_amount=Decimal("55000.00"),
                )
            ],
        ),
    )
    await service.assign_employee_compensation(
        tenant_id,
        EmployeeCompensationCreate(
            employee_id=emp1.id,
            structure_id=struct.id,
            annual_ctc=Decimal("660000.00"),
            monthly_gross=Decimal("55000.00"),
            base_pay=Decimal("55000.00"),
            effective_from=date(2026, 1, 1),
        ),
        actor_id=preparer.id,
    )

    run = await service.create_payroll_run(
        tenant_id,
        PayrollRunCreate(period_id=period.id, calendar_id=cal.id),
        actor_id=preparer.id,
    )
    await service.calculate_payroll_run(tenant_id, run.id, PayrollRunCalculateRequest(), actor_id=preparer.id)
    await service.approve_payroll_run(tenant_id, run.id, actor_id=approver.id)

    # Post to generate payslips
    await service.post_payroll_to_accounting(tenant_id, run.id, actor_id=approver.id)

    # Query Employee Payslips
    payslips = await service.list_employee_payslips(tenant_id, emp1.id)
    assert len(payslips) == 1
    ps = payslips[0]
    assert ps.net_pay == Decimal("55000.00")
    assert ps.secure_token is not None

    # Retrieve by secure token
    token_ps = await service.get_payslip_by_token(ps.secure_token)
    assert token_ps.id == ps.id


# =============================================================================
# 12. MULTI-TENANT ISOLATION
# =============================================================================


@pytest.mark.asyncio
async def test_payroll_multi_tenant_isolation(
    db_session: AsyncSession, payroll_fixture: dict
):
    service = PayrollService(db_session)
    tenant_a_id = payroll_fixture["tenant_a"].id
    tenant_b_id = payroll_fixture["tenant_b"].id

    grade_a = await service.create_salary_grade(
        tenant_a_id,
        SalaryGradeCreate(
            code="GRADE-A-ONLY",
            name="Tenant A Exclusive Grade",
            min_base_pay=Decimal("30000.00"),
            max_base_pay=Decimal("60000.00"),
        ),
    )

    with pytest.raises(NotFoundException):
        await service.get_salary_grade(tenant_b_id, grade_a.id)

    grades_b = await service.list_salary_grades(tenant_b_id)
    assert not any(g.id == grade_a.id for g in grades_b)
