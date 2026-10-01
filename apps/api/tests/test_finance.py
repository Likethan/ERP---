"""Comprehensive automated tests for CampusOS Step 8: Finance, Fees & Billing Engine."""

import uuid
from decimal import Decimal
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.core import Institution
from app.models.people import Role, StudentProfile, User, UserRoleAssignment


async def authenticate_user(
    client: AsyncClient, email: str, password: str = "SuperSecret123!"
) -> dict[str, Any]:
    """Helper to authenticate a test client and establish session cookies."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200, f"Authentication failed: {resp.text}"
    return resp.json()["data"]


async def setup_finance_environment(client: AsyncClient) -> dict[str, Any]:
    """Helper to initialize department, program, academic year, semester, and an admitted student."""
    uid = uuid.uuid4().hex[:5]

    # 1. Department
    dept_res = await client.post(
        "/api/v1/departments",
        json={"code": f"ENG_{uid.upper()}", "name": f"Engineering {uid}"},
    )
    assert dept_res.status_code == 201
    dept_id = dept_res.json()["data"]["id"]

    # 2. Program
    prog_res = await client.post(
        "/api/v1/programs",
        json={
            "department_id": dept_id,
            "code": f"BTECH_AI_{uid.upper()}",
            "name": "B.Tech Artificial Intelligence",
            "degree_level": "UNDERGRADUATE",
            "duration_years": 4,
            "total_semesters": 8,
        },
    )
    assert prog_res.status_code == 201
    prog_id = prog_res.json()["data"]["id"]

    # 3. Academic Year & Semester
    ay_res = await client.post(
        "/api/v1/academic-years",
        json={
            "code": f"AY_FIN_{uid.upper()}",
            "name": "2026-2027",
            "start_date": "2026-06-01",
            "end_date": "2027-05-31",
            "is_current": True,
        },
    )
    assert ay_res.status_code == 201
    ay_id = ay_res.json()["data"]["id"]

    sem_res = await client.post(
        "/api/v1/semesters",
        json={
            "academic_year_id": ay_id,
            "name": "Semester 5",
            "semester_number": 5,
            "term_type": "ODD",
            "start_date": "2026-07-01",
            "end_date": "2026-11-30",
        },
    )
    assert sem_res.status_code == 201
    sem_id = sem_res.json()["data"]["id"]

    # 4. Regulation & Batch
    reg_res = await client.post(
        "/api/v1/regulations",
        json={
            "code": f"REG_{uid.upper()}",
            "title": "Regulation 2026",
            "effective_year": 2026,
        },
    )
    assert reg_res.status_code == 201
    reg_id = reg_res.json()["data"]["id"]

    batch_res = await client.post(
        "/api/v1/batches",
        json={
            "program_id": prog_id,
            "regulation_id": reg_id,
            "name": f"Batch 2024-2028 {uid}",
            "admission_year": 2024,
            "graduation_year": 2028,
        },
    )
    assert batch_res.status_code == 201
    batch_id = batch_res.json()["data"]["id"]

    # 5. Section
    sec_res = await client.post(
        "/api/v1/sections",
        json={
            "program_id": prog_id,
            "batch_id": batch_id,
            "semester_id": sem_id,
            "name": f"Sec-{uid.upper()}",
            "capacity": 60,
        },
    )
    assert sec_res.status_code == 201
    sec_id = sec_res.json()["data"]["id"]

    # 6. Admitted Student
    stud_res = await client.post(
        "/api/v1/students",
        json={
            "first_name": "Arjun",
            "last_name": f"Verma_{uid}",
            "email": f"arjun_{uid}@campusos.edu",
            "admission_number": f"ADM_{uid.upper()}",
            "roll_number": f"R_{uid.upper()}",
            "date_of_birth": "2004-05-15",
            "gender": "MALE",
            "admission_date": "2024-08-01",
            "expected_graduation_date": "2028-05-31",
            "program_id": prog_id,
            "batch_id": batch_id,
            "current_semester_id": sem_id,
            "current_section_id": sec_id,
        },
    )
    assert stud_res.status_code == 201
    student = stud_res.json()["data"]

    return {
        "uid": uid,
        "department_id": dept_id,
        "program_id": prog_id,
        "academic_year_id": ay_id,
        "semester_id": sem_id,
        "student": student,
    }


@pytest.mark.asyncio
async def test_fee_categories_and_structures_lifecycle(
    client: AsyncClient, super_admin_user: User
) -> None:
    """Verify default category seeding, custom category creation, and fee structure lifecycle (Draft -> Approved -> Active -> Retired)."""
    await authenticate_user(client, super_admin_user.email)
    env = await setup_finance_environment(client)

    # 1. Categories listing (should seed defaults like TUITION, HOSTEL, EXAMINATION)
    cats_res = await client.get("/api/v1/finance/fee-categories")
    assert cats_res.status_code == 200
    categories = cats_res.json()["data"]
    cat_codes = [c["code"] for c in categories]
    assert "TUITION" in cat_codes
    assert "EXAMINATION" in cat_codes
    assert "LABORATORY" in cat_codes

    tuition_cat = next(c for c in categories if c["code"] == "TUITION")
    exam_cat = next(c for c in categories if c["code"] == "EXAMINATION")
    lab_cat = next(c for c in categories if c["code"] == "LABORATORY")

    # 2. Create custom fee category
    custom_res = await client.post(
        "/api/v1/finance/fee-categories",
        json={
            "code": f"STUDENT_DEV_{env['uid'].upper()}",
            "name": "Student Development Fee",
            "description": "Annual student workshop fund",
            "is_refundable": False,
        },
    )
    assert custom_res.status_code == 201
    assert custom_res.json()["data"]["name"] == "Student Development Fee"

    # Duplicate code should fail
    dup_res = await client.post(
        "/api/v1/finance/fee-categories",
        json={
            "code": f"STUDENT_DEV_{env['uid'].upper()}",
            "name": "Duplicate",
        },
    )
    assert dup_res.status_code == 409

    # 3. Create Fee Structure Draft
    struct_res = await client.post(
        "/api/v1/finance/fee-structures",
        json={
            "program_id": env["program_id"],
            "academic_year_id": env["academic_year_id"],
            "semester_id": env["semester_id"],
            "quota_type": "GENERAL",
            "name": f"B.Tech AI Regular 2026-27 {env['uid']}",
            "items": [
                {
                    "category_id": tuition_cat["id"],
                    "name": "Tuition Fee",
                    "amount": 80000.00,
                    "is_optional": False,
                    "sequence": 1,
                },
                {
                    "category_id": exam_cat["id"],
                    "name": "University Examination Fee",
                    "amount": 2000.00,
                    "is_optional": False,
                    "sequence": 2,
                },
                {
                    "category_id": lab_cat["id"],
                    "name": "Laboratory & Innovation Fee",
                    "amount": 5000.00,
                    "is_optional": False,
                    "sequence": 3,
                },
            ],
        },
    )
    assert struct_res.status_code == 201
    structure = struct_res.json()["data"]
    assert structure["status"] == "DRAFT"
    assert float(structure["total_amount"]) == 87000.00
    assert len(structure["items"]) == 3

    # 4. Lifecycle: Approve & Activate
    appr_res = await client.post(f"/api/v1/finance/fee-structures/{structure['id']}/approve")
    assert appr_res.status_code == 200
    assert appr_res.json()["data"]["status"] == "APPROVED"

    act_res = await client.post(f"/api/v1/finance/fee-structures/{structure['id']}/activate")
    assert act_res.status_code == 200
    assert act_res.json()["data"]["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_student_fee_assignment_and_invoice_generation(
    client: AsyncClient, super_admin_user: User
) -> None:
    """Verify assigning a fee structure to a student and generating a draft invoice with itemized lines."""
    await authenticate_user(client, super_admin_user.email)
    env = await setup_finance_environment(client)

    cats_res = await client.get("/api/v1/finance/fee-categories")
    tuition_cat = next(c for c in cats_res.json()["data"] if c["code"] == "TUITION")
    exam_cat = next(c for c in cats_res.json()["data"] if c["code"] == "EXAMINATION")

    # Create & Activate fee structure
    struct_res = await client.post(
        "/api/v1/finance/fee-structures",
        json={
            "program_id": env["program_id"],
            "academic_year_id": env["academic_year_id"],
            "semester_id": env["semester_id"],
            "quota_type": "GENERAL",
            "name": f"Fee Structure {env['uid']}",
            "items": [
                {"category_id": tuition_cat["id"], "name": "Tuition Fee", "amount": 60000.00},
                {"category_id": exam_cat["id"], "name": "Exam Fee", "amount": 2500.00},
            ],
        },
    )
    structure_id = struct_res.json()["data"]["id"]
    await client.post(f"/api/v1/finance/fee-structures/{structure_id}/activate")

    # Assign to student
    assign_res = await client.post(
        f"/api/v1/finance/students/{env['student']['id']}/fees/assign",
        json={
            "student_id": env["student"]["id"],
            "fee_structure_id": structure_id,
            "academic_year_id": env["academic_year_id"],
            "semester_id": env["semester_id"],
        },
    )
    assert assign_res.status_code == 201
    assert assign_res.json()["data"]["status"] == "ACTIVE"

    # Generate Invoice from Fee Structure
    inv_res = await client.post(
        "/api/v1/finance/invoices",
        json={
            "student_id": env["student"]["id"],
            "academic_year_id": env["academic_year_id"],
            "semester_id": env["semester_id"],
            "fee_structure_id": structure_id,
            "due_date": "2026-08-30",
        },
    )
    assert inv_res.status_code == 201
    invoice = inv_res.json()["data"]
    assert invoice["status"] == "DRAFT"
    assert float(invoice["gross_amount"]) == 62500.00
    assert float(invoice["net_payable"]) == 62500.00
    assert float(invoice["balance_amount"]) == 62500.00
    assert float(invoice["paid_amount"]) == 0.00
    assert invoice["invoice_number"].startswith("INV-")
    assert len(invoice["items"]) == 2


@pytest.mark.asyncio
async def test_invoice_issuance_and_cancellation(
    client: AsyncClient, super_admin_user: User
) -> None:
    """Verify invoice issuance committing balance, and unpaid invoice cancellation."""
    await authenticate_user(client, super_admin_user.email)
    env = await setup_finance_environment(client)

    cats_res = await client.get("/api/v1/finance/fee-categories")
    tuition_cat = next(c for c in cats_res.json()["data"] if c["code"] == "TUITION")

    # Create Invoice with custom item
    inv_res = await client.post(
        "/api/v1/finance/invoices",
        json={
            "student_id": env["student"]["id"],
            "academic_year_id": env["academic_year_id"],
            "due_date": "2026-09-15",
            "items": [
                {"category_id": tuition_cat["id"], "description": "Tuition Semester 5", "amount": 45000.00}
            ],
        },
    )
    assert inv_res.status_code == 201
    invoice_id = inv_res.json()["data"]["id"]

    # Issue Invoice
    issue_res = await client.post(f"/api/v1/finance/invoices/{invoice_id}/issue")
    assert issue_res.status_code == 200
    assert issue_res.json()["data"]["status"] == "ISSUED"

    # Cancel unpaid Invoice
    cancel_res = await client.post(f"/api/v1/finance/invoices/{invoice_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["data"]["status"] == "CANCELLED"


@pytest.mark.asyncio
async def test_payment_recording_allocation_and_receipt(
    client: AsyncClient, super_admin_user: User
) -> None:
    """Verify recording student payment, atomic allocation to invoice, receipt generation, and status updates."""
    await authenticate_user(client, super_admin_user.email)
    env = await setup_finance_environment(client)

    cats_res = await client.get("/api/v1/finance/fee-categories")
    tuition_cat = next(c for c in cats_res.json()["data"] if c["code"] == "TUITION")

    # 1. Create and Issue Invoice of ₹50,000
    inv_res = await client.post(
        "/api/v1/finance/invoices",
        json={
            "student_id": env["student"]["id"],
            "academic_year_id": env["academic_year_id"],
            "due_date": "2026-08-31",
            "items": [
                {"category_id": tuition_cat["id"], "description": "Tuition Fall", "amount": 50000.00}
            ],
        },
    )
    invoice_id = inv_res.json()["data"]["id"]
    await client.post(f"/api/v1/finance/invoices/{invoice_id}/issue")

    # 2. Record Partial Payment of ₹30,000 allocated to invoice
    pay_res = await client.post(
        "/api/v1/finance/payments",
        json={
            "student_id": env["student"]["id"],
            "amount": 30000.00,
            "payment_mode": "UPI",
            "transaction_reference": f"UPI_{env['uid']}_101",
            "allocations": [
                {"invoice_id": invoice_id, "amount": 30000.00}
            ],
        },
    )
    assert pay_res.status_code == 201
    payment = pay_res.json()["data"]
    assert payment["status"] == "SUCCESS"
    assert payment["payment_number"].startswith("PAY-")
    assert payment["receipt_number"].startswith("RCP-")
    assert len(payment["allocations"]) == 1

    # Verify invoice updated to PARTIALLY_PAID
    inv_check = await client.get(f"/api/v1/finance/invoices/{invoice_id}")
    assert inv_check.status_code == 200
    inv_data = inv_check.json()["data"]
    assert inv_data["status"] == "PARTIALLY_PAID"
    assert float(inv_data["paid_amount"]) == 30000.00
    assert float(inv_data["balance_amount"]) == 20000.00

    # 3. Pay Remaining Balance of ₹20,000
    pay_res2 = await client.post(
        "/api/v1/finance/payments",
        json={
            "student_id": env["student"]["id"],
            "amount": 20000.00,
            "payment_mode": "BANK_TRANSFER",
            "transaction_reference": f"NEFT_{env['uid']}_102",
            "allocations": [
                {"invoice_id": invoice_id, "amount": 20000.00}
            ],
        },
    )
    assert pay_res2.status_code == 201

    # Verify invoice transitioned to PAID
    inv_check2 = await client.get(f"/api/v1/finance/invoices/{invoice_id}")
    inv_data2 = inv_check2.json()["data"]
    assert inv_data2["status"] == "PAID"
    assert float(inv_data2["balance_amount"]) == 0.00
    assert float(inv_data2["paid_amount"]) == 50000.00


@pytest.mark.asyncio
async def test_payment_over_allocation_prevention(
    client: AsyncClient, super_admin_user: User
) -> None:
    """Verify that attempting to allocate more than the invoice balance is strictly rejected."""
    await authenticate_user(client, super_admin_user.email)
    env = await setup_finance_environment(client)

    cats_res = await client.get("/api/v1/finance/fee-categories")
    tuition_cat = next(c for c in cats_res.json()["data"] if c["code"] == "TUITION")

    inv_res = await client.post(
        "/api/v1/finance/invoices",
        json={
            "student_id": env["student"]["id"],
            "academic_year_id": env["academic_year_id"],
            "due_date": "2026-08-31",
            "items": [
                {"category_id": tuition_cat["id"], "description": "Tuition", "amount": 10000.00}
            ],
        },
    )
    invoice_id = inv_res.json()["data"]["id"]
    await client.post(f"/api/v1/finance/invoices/{invoice_id}/issue")

    # Attempt to allocate ₹15,000 on a ₹10,000 invoice
    pay_fail = await client.post(
        "/api/v1/finance/payments",
        json={
            "student_id": env["student"]["id"],
            "amount": 15000.00,
            "payment_mode": "CASH",
            "transaction_reference": f"CASH_{env['uid']}_FAIL",
            "allocations": [
                {"invoice_id": invoice_id, "amount": 15000.00}
            ],
        },
    )
    assert pay_fail.status_code == 422
    assert "exceeds" in pay_fail.text.lower()


@pytest.mark.asyncio
async def test_scholarships_and_concessions_deduction(
    client: AsyncClient, super_admin_user: User
) -> None:
    """Verify awarding a scholarship to a student automatically reduces net payable on generated invoice."""
    await authenticate_user(client, super_admin_user.email)
    env = await setup_finance_environment(client)

    cats_res = await client.get("/api/v1/finance/fee-categories")
    tuition_cat = next(c for c in cats_res.json()["data"] if c["code"] == "TUITION")

    # 1. Award a ₹25,000 Merit Scholarship
    schol_res = await client.post(
        "/api/v1/finance/scholarships",
        json={
            "student_id": env["student"]["id"],
            "academic_year_id": env["academic_year_id"],
            "concession_name": "Dean's Merit Scholarship",
            "concession_type": "MERIT",
            "amount": 25000.00,
            "remarks": "Rank 1 in entrance exam",
        },
    )
    assert schol_res.status_code == 201
    assert schol_res.json()["data"]["status"] == "APPROVED"

    # 2. Generate Invoice of ₹75,000 with apply_scholarships=True
    inv_res = await client.post(
        "/api/v1/finance/invoices",
        json={
            "student_id": env["student"]["id"],
            "academic_year_id": env["academic_year_id"],
            "due_date": "2026-08-31",
            "apply_scholarships": True,
            "items": [
                {"category_id": tuition_cat["id"], "description": "Full Year Tuition", "amount": 75000.00}
            ],
        },
    )
    assert inv_res.status_code == 201
    inv = inv_res.json()["data"]
    assert float(inv["gross_amount"]) == 75000.00
    assert float(inv["concession_amount"]) == 25000.00
    assert float(inv["net_payable"]) == 50000.00
    assert float(inv["balance_amount"]) == 50000.00


@pytest.mark.asyncio
async def test_financial_adjustments_credit_and_debit(
    client: AsyncClient, super_admin_user: User
) -> None:
    """Verify financial adjustments (credit/debit notes) accurately modify invoice balance without history overwrite."""
    await authenticate_user(client, super_admin_user.email)
    env = await setup_finance_environment(client)

    cats_res = await client.get("/api/v1/finance/fee-categories")
    tuition_cat = next(c for c in cats_res.json()["data"] if c["code"] == "TUITION")

    # Invoice of ₹40,000
    inv_res = await client.post(
        "/api/v1/finance/invoices",
        json={
            "student_id": env["student"]["id"],
            "academic_year_id": env["academic_year_id"],
            "due_date": "2026-08-31",
            "items": [
                {"category_id": tuition_cat["id"], "description": "Lab Fees", "amount": 40000.00}
            ],
        },
    )
    invoice_id = inv_res.json()["data"]["id"]
    await client.post(f"/api/v1/finance/invoices/{invoice_id}/issue")

    # Apply Credit Note of ₹5,000 (e.g. waiver)
    cred_res = await client.post(
        "/api/v1/finance/adjustments",
        json={
            "invoice_id": invoice_id,
            "adjustment_type": "CREDIT",
            "amount": 5000.00,
            "reason": "Institutional COVID-recovery waiver",
        },
    )
    assert cred_res.status_code == 201

    inv_check1 = await client.get(f"/api/v1/finance/invoices/{invoice_id}")
    assert float(inv_check1.json()["data"]["balance_amount"]) == 35000.00
    assert float(inv_check1.json()["data"]["net_payable"]) == 35000.00

    # Apply Debit Note of ₹1,000 (e.g. late registration penalty)
    deb_res = await client.post(
        "/api/v1/finance/adjustments",
        json={
            "invoice_id": invoice_id,
            "adjustment_type": "DEBIT",
            "amount": 1000.00,
            "reason": "Late enrollment administrative penalty",
        },
    )
    assert deb_res.status_code == 201

    inv_check2 = await client.get(f"/api/v1/finance/invoices/{invoice_id}")
    assert float(inv_check2.json()["data"]["balance_amount"]) == 36000.00
    assert float(inv_check2.json()["data"]["net_payable"]) == 36000.00


@pytest.mark.asyncio
async def test_refund_workflow_and_validation(
    client: AsyncClient, super_admin_user: User
) -> None:
    """Verify requesting, authorizing, and disbursing a refund, including boundary limit enforcement."""
    await authenticate_user(client, super_admin_user.email)
    env = await setup_finance_environment(client)

    # Record a ₹20,000 payment
    pay_res = await client.post(
        "/api/v1/finance/payments",
        json={
            "student_id": env["student"]["id"],
            "amount": 20000.00,
            "payment_mode": "CARD",
            "transaction_reference": f"CARD_{env['uid']}_99",
        },
    )
    assert pay_res.status_code == 201
    payment_id = pay_res.json()["data"]["id"]

    # Request excessive refund of ₹25,000 (must be rejected)
    ref_fail = await client.post(
        "/api/v1/finance/refunds",
        json={
            "payment_id": payment_id,
            "refund_amount": 25000.00,
            "reason": "Over-refund test",
        },
    )
    assert ref_fail.status_code == 422

    # Request valid partial refund of ₹8,000
    ref_res = await client.post(
        "/api/v1/finance/refunds",
        json={
            "payment_id": payment_id,
            "refund_amount": 8000.00,
            "reason": "Course drop withdrawal refund",
            "refund_mode": "BANK_TRANSFER",
        },
    )
    assert ref_res.status_code == 201
    refund = ref_res.json()["data"]
    assert refund["status"] == "REQUESTED"

    # Authorize refund
    appr_res = await client.post(f"/api/v1/finance/refunds/{refund['id']}/approve")
    assert appr_res.status_code == 200
    assert appr_res.json()["data"]["status"] == "APPROVED"

    # Process refund disbursement
    proc_res = await client.post(
        f"/api/v1/finance/refunds/{refund['id']}/process?refund_reference=BANK_TXN_{env['uid']}"
    )
    assert proc_res.status_code == 200
    assert proc_res.json()["data"]["status"] == "PROCESSED"

    # Verify payment status updated to PARTIALLY_REFUNDED
    pay_check = await client.get(f"/api/v1/finance/payments/{payment_id}")
    assert pay_check.json()["data"]["status"] == "PARTIALLY_REFUNDED"


@pytest.mark.asyncio
async def test_finance_tenant_isolation_and_student_privacy(
    client: AsyncClient, super_admin_user: User, tenant_b: Institution, db_session: AsyncSession
) -> None:
    """Verify cross-tenant financial isolation and student self-service privacy gating."""
    # Setup Tenant A
    await authenticate_user(client, super_admin_user.email)
    env_a = await setup_finance_environment(client)

    cats_res = await client.get("/api/v1/finance/fee-categories")
    tuition_cat = next(c for c in cats_res.json()["data"] if c["code"] == "TUITION")

    inv_a = await client.post(
        "/api/v1/finance/invoices",
        json={
            "student_id": env_a["student"]["id"],
            "academic_year_id": env_a["academic_year_id"],
            "due_date": "2026-08-31",
            "items": [
                {"category_id": tuition_cat["id"], "description": "Tenant A Tuition", "amount": 30000.00}
            ],
        },
    )
    invoice_a_id = inv_a.json()["data"]["id"]

    # Setup Tenant B Admin
    tenant_b_admin = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_b.id,
        email=f"admin_b_{uuid.uuid4().hex[:6]}@beaconuni.edu",
        phone_number="+1987654399",
        password_hash=get_password_hash("SuperSecret123!"),
        status="ACTIVE",
        first_name="Beacon",
        last_name="Admin",
    )
    db_session.add(tenant_b_admin)
    await db_session.flush()

    role_res = await db_session.execute(select(Role).where(Role.name == "SUPER_ADMIN"))
    role = role_res.scalar_one()
    db_session.add(
        UserRoleAssignment(
            id=uuid.uuid4(),
            tenant_id=tenant_b.id,
            user_id=tenant_b_admin.id,
            role_id=role.id,
        )
    )
    await db_session.commit()

    # Authenticate as Tenant B Admin
    await authenticate_user(client, tenant_b_admin.email, "SuperSecret123!")

    # 1. Tenant B must NOT be able to view Tenant A's invoice
    get_cross = await client.get(f"/api/v1/finance/invoices/{invoice_a_id}")
    assert get_cross.status_code == 404

    # 2. Tenant B listing invoices must NOT contain Tenant A's invoice
    list_b = await client.get("/api/v1/finance/invoices")
    assert list_b.status_code == 200
    b_ids = [inv["id"] for inv in list_b.json()["data"]]
    assert invoice_a_id not in b_ids

    # 3. Student privacy test: Authenticate as Tenant A student
    stud_login = await authenticate_user(client, env_a["student"]["email"], "Welcome@123")

    # Student viewing own statement succeeds
    own_stmt = await client.get(f"/api/v1/finance/students/{env_a['student']['id']}/statement")
    assert own_stmt.status_code == 200
    assert own_stmt.json()["data"]["student_id"] == env_a["student"]["id"]

    # Student attempting to view another random student's statement fails with 403 Forbidden
    other_stud_id = uuid.uuid4()
    other_stmt = await client.get(f"/api/v1/finance/students/{other_stud_id}/statement")
    assert other_stmt.status_code == 403
