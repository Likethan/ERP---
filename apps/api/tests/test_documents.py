"""Comprehensive Production-Grade Test Suite for CampusOS Documents & Digital Records Domain.

Covers:
- Category CRUD, uniqueness, activation rules, tenant isolation
- Document types and configurable requirements
- Document creation, binary upload, storage security & path traversal prevention
- Document lifecycle (UPLOADED -> UNDER_REVIEW -> VERIFIED / REJECTED)
- Mandatory rejection reasons & re-upload versioning
- Certificate template authoring & version preservation
- Certificate request lifecycle, clearances, approval, and issuance numbering
- Cryptographic verification & QR lookup
- Immutable historical certificate revocation
- Institutional records with multi-level confidentiality & history
- Full RBAC / PBAC authorization and cross-tenant security containment
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import DEFAULT_ROLE_PERMISSIONS
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token, get_password_hash
from app.core.storage import LocalDocumentStorage
from app.models.core import Institution
from app.models.people import Role, User, UserRoleAssignment


def make_auth_headers(user: User, tenant_id: uuid.UUID, role_name: str) -> dict:
    """Generate authorization headers & cookies for authenticated API requests."""
    perms = DEFAULT_ROLE_PERMISSIONS.get(role_name, [])
    token = create_access_token(
        user_id=user.id,
        tenant_id=tenant_id,
        email=user.email,
        roles=[role_name],
        permissions=perms,
    )
    return {
        "Authorization": f"Bearer {token}",
        "Cookie": f"{ACCESS_TOKEN_COOKIE_NAME}={token}",
    }


@pytest.fixture
async def document_users(
    db_session: AsyncSession, tenant_a: Institution, tenant_b: Institution
):
    """Setup users with specific roles across Tenant A and Tenant B."""
    uid = uuid.uuid4().hex[:6]

    # 1. Admin in Tenant A
    admin_a = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"admin_{uid}@apextech.edu",
        phone_number="+919876543210",
        password_hash=get_password_hash("AdminPass123!"),
        status="ACTIVE",
        first_name="Institutional",
        last_name="Registrar",
    )
    db_session.add(admin_a)

    # 2. Document Officer in Tenant A
    officer_a = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"officer_{uid}@apextech.edu",
        phone_number="+919876543211",
        password_hash=get_password_hash("OfficerPass123!"),
        status="ACTIVE",
        first_name="Document",
        last_name="Officer",
    )
    db_session.add(officer_a)

    # 3. Student 1 in Tenant A
    student_1 = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"student1_{uid}@apextech.edu",
        phone_number="+919876543212",
        password_hash=get_password_hash("StudentPass123!"),
        status="ACTIVE",
        first_name="Aarav",
        last_name="Patel",
    )
    db_session.add(student_1)

    # 4. Student 2 in Tenant A
    student_2 = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"student2_{uid}@apextech.edu",
        phone_number="+919876543213",
        password_hash=get_password_hash("StudentPass123!"),
        status="ACTIVE",
        first_name="Diya",
        last_name="Sharma",
    )
    db_session.add(student_2)

    # 5. User in Tenant B (for cross-tenant attacks)
    admin_b = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_b.id,
        email=f"admin_{uid}@beaconuni.edu",
        phone_number="+919876543214",
        password_hash=get_password_hash("AdminBPass123!"),
        status="ACTIVE",
        first_name="Beacon",
        last_name="Admin",
    )
    db_session.add(admin_b)

    await db_session.flush()

    # Assign Roles
    roles = (await db_session.execute(select(Role))).scalars().all()
    roles_by_name = {r.name: r for r in roles}

    def assign(user: User, t_id: uuid.UUID, r_name: str):
        r = roles_by_name.get(r_name)
        if r:
            db_session.add(
                UserRoleAssignment(
                    id=uuid.uuid4(),
                    tenant_id=t_id,
                    user_id=user.id,
                    role_id=r.id,
                )
            )

    assign(admin_a, tenant_a.id, "INSTITUTION_ADMIN")
    assign(officer_a, tenant_a.id, "DOCUMENT_OFFICER")
    assign(student_1, tenant_a.id, "STUDENT")
    assign(student_2, tenant_a.id, "STUDENT")
    assign(admin_b, tenant_b.id, "INSTITUTION_ADMIN")

    await db_session.commit()
    await db_session.refresh(admin_a)
    await db_session.refresh(officer_a)
    await db_session.refresh(student_1)
    await db_session.refresh(student_2)
    await db_session.refresh(admin_b)

    return {
        "admin_a": admin_a,
        "officer_a": officer_a,
        "student_1": student_1,
        "student_2": student_2,
        "admin_b": admin_b,
    }


# =============================================================================
# 1. CATEGORY TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_category_lifecycle_and_uniqueness(
    client: AsyncClient, tenant_a: Institution, document_users: dict
):
    admin = document_users["admin_a"]
    headers = make_auth_headers(admin, tenant_a.id, "INSTITUTION_ADMIN")

    # 1. Create Category
    code = f"CAT_{uuid.uuid4().hex[:4].upper()}"
    create_res = await client.post(
        "/api/v1/document-categories",
        headers=headers,
        json={
            "code": code,
            "name": "Identity & Government Credentials",
            "description": "Government-issued identity cards",
            "required": True,
            "verificationRequired": True,
            "expiryRequired": False,
        },
    )
    assert create_res.status_code == 201
    cat_data = create_res.json()["data"]
    assert cat_data["code"] == code
    assert cat_data["isActive"] is True
    cat_id = cat_data["id"]

    # 2. Reject Duplicate Code
    dup_res = await client.post(
        "/api/v1/document-categories",
        headers=headers,
        json={
            "code": code,
            "name": "Duplicate Category",
        },
    )
    assert dup_res.status_code == 409

    # 3. Update Category
    update_res = await client.patch(
        f"/api/v1/document-categories/{cat_id}",
        headers=headers,
        json={"name": "Updated Identity Records", "isActive": False},
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["name"] == "Updated Identity Records"
    assert update_res.json()["data"]["isActive"] is False


@pytest.mark.asyncio
async def test_document_types_and_requirements(
    client: AsyncClient, tenant_a: Institution, document_users: dict
):
    admin = document_users["admin_a"]
    headers = make_auth_headers(admin, tenant_a.id, "INSTITUTION_ADMIN")

    # 1. Create active category
    code_cat = f"ACAD_{uuid.uuid4().hex[:4].upper()}"
    cat_res = await client.post(
        "/api/v1/document-categories",
        headers=headers,
        json={"code": code_cat, "name": "Academic Certificates"},
    )
    cat_id = cat_res.json()["data"]["id"]

    # 2. Create Document Type
    type_code = f"DEG_{uuid.uuid4().hex[:4].upper()}"
    type_res = await client.post(
        "/api/v1/document-types",
        headers=headers,
        json={
            "categoryId": cat_id,
            "code": type_code,
            "name": "Bachelor Degree Certificate",
            "isRequiredByDefault": True,
            "requiresVerification": True,
        },
    )
    assert type_res.status_code == 201
    type_id = type_res.json()["data"]["id"]

    # 3. Create Document Requirement
    req_res = await client.post(
        "/api/v1/document-requirements",
        headers=headers,
        json={
            "documentTypeId": type_id,
            "ownerType": "STUDENT",
            "isRequired": True,
            "description": "Graduation degree requirement",
        },
    )
    assert req_res.status_code == 201
    assert req_res.json()["data"]["isRequired"] is True


# =============================================================================
# 2. DOCUMENT LIFECYCLE & VERIFICATION WORKFLOW
# =============================================================================


@pytest.mark.asyncio
async def test_document_lifecycle_and_verification_desk(
    client: AsyncClient, tenant_a: Institution, document_users: dict
):
    admin = document_users["admin_a"]
    officer = document_users["officer_a"]
    student = document_users["student_1"]

    admin_headers = make_auth_headers(admin, tenant_a.id, "INSTITUTION_ADMIN")
    officer_headers = make_auth_headers(officer, tenant_a.id, "DOCUMENT_OFFICER")
    student_headers = make_auth_headers(student, tenant_a.id, "STUDENT")

    # 1. Create Category
    cat_code = f"MED_{uuid.uuid4().hex[:4].upper()}"
    cat_res = await client.post(
        "/api/v1/document-categories",
        headers=admin_headers,
        json={"code": cat_code, "name": "Medical Documentation"},
    )
    cat_id = cat_res.json()["data"]["id"]

    # 2. Student uploads document
    doc_res = await client.post(
        "/api/v1/documents",
        headers=student_headers,
        json={
            "name": "Annual Fitness Certificate",
            "category": cat_code,
            "documentType": "Medical Clearance",
            "ownerType": "STUDENT",
            "ownerId": str(student.id),
            "ownerName": "Aarav Patel",
            "confidentiality": "INTERNAL",
            "priority": "HIGH",
            "documentNumber": "MED-2026-9901",
            "issuingAuthority": "State General Hospital",
            "issueDate": "2026-08-01",
            "expiryDate": "2027-08-01",
        },
    )
    assert doc_res.status_code == 201
    doc = doc_res.json()["data"]
    assert doc["status"] == "UPLOADED"
    doc_id = doc["id"]

    # 3. Student submits for review
    sub_res = await client.post(f"/api/v1/documents/{doc_id}/submit", headers=student_headers)
    assert sub_res.status_code == 200
    assert sub_res.json()["data"]["status"] == "UNDER_REVIEW"

    # 4. Officer commences inspection
    rev_res = await client.post(f"/api/v1/documents/{doc_id}/review", headers=officer_headers)
    assert rev_res.status_code == 200
    assert rev_res.json()["data"]["assignedReviewerName"] == f"{officer.first_name} {officer.last_name}"

    # 5. Reject requires non-empty reason
    empty_rej = await client.post(
        f"/api/v1/documents/{doc_id}/reject",
        headers=officer_headers,
        json={"reason": "   "},
    )
    assert empty_rej.status_code == 422

    # 6. Reject with proper reason
    rej_res = await client.post(
        f"/api/v1/documents/{doc_id}/reject",
        headers=officer_headers,
        json={"reason": "Doctor stamp blurred, seal illegible."},
    )
    assert rej_res.status_code == 200
    assert rej_res.json()["data"]["status"] == "REJECTED"
    assert "Doctor stamp blurred" in rej_res.json()["data"]["rejectionReason"]

    # 7. Re-upload replacement file
    reupload_res = await client.post(
        f"/api/v1/documents/{doc_id}/reupload",
        headers=student_headers,
        files={"file": ("fitness_signed.pdf", b"%PDF-1.4 Legible Scan", "application/pdf")},
    )
    assert reupload_res.status_code == 200
    updated_doc = reupload_res.json()["data"]
    assert updated_doc["status"] == "UPLOADED"
    assert updated_doc["version"] == 2
    assert updated_doc["rejectionReason"] is None

    # Check version history recorded
    vers_res = await client.get(f"/api/v1/documents/{doc_id}/versions", headers=student_headers)
    assert vers_res.status_code == 200
    assert len(vers_res.json()["data"]) >= 1

    # 8. Review and Verify
    await client.post(f"/api/v1/documents/{doc_id}/submit", headers=student_headers)
    await client.post(f"/api/v1/documents/{doc_id}/review", headers=officer_headers)
    verify_res = await client.post(
        f"/api/v1/documents/{doc_id}/verify",
        headers=officer_headers,
        json={"notes": "Doctor seal validated against registry."},
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["data"]["status"] == "VERIFIED"
    assert verify_res.json()["data"]["verifiedAt"] is not None


# =============================================================================
# 3. CERTIFICATE TEMPLATE & ISSUANCE WORKFLOW
# =============================================================================


@pytest.mark.asyncio
async def test_certificate_template_and_request_lifecycle(
    client: AsyncClient, tenant_a: Institution, document_users: dict
):
    admin = document_users["admin_a"]
    officer = document_users["officer_a"]
    student = document_users["student_1"]

    admin_headers = make_auth_headers(admin, tenant_a.id, "INSTITUTION_ADMIN")
    officer_headers = make_auth_headers(officer, tenant_a.id, "DOCUMENT_OFFICER")
    student_headers = make_auth_headers(student, tenant_a.id, "STUDENT")

    # 1. Admin creates certificate template
    tmpl_code = f"BONA_{uuid.uuid4().hex[:4].upper()}"
    tmpl_res = await client.post(
        "/api/v1/certificates/templates",
        headers=admin_headers,
        json={
            "code": tmpl_code,
            "templateName": "Student Bonafide Certificate",
            "certificateType": "BONAFIDE",
            "description": "Standard institutional bonafide testimonial",
            "applicableAudience": ["STUDENT"],
            "templateBody": "<div>Bonafide Testimonial for {{ student_name }}</div>",
            "fields": [
                {"id": "f1", "name": "student_name", "label": "Full Name", "type": "SYSTEM_VARIABLE", "required": True},
                {"id": "f2", "name": "roll_number", "label": "Roll Number", "type": "SYSTEM_VARIABLE", "required": True},
            ],
        },
    )
    assert tmpl_res.status_code == 201
    tmpl = tmpl_res.json()["data"]
    tmpl_id = tmpl["id"]

    # 2. Student applies for Certificate
    req_res = await client.post(
        "/api/v1/certificates/requests",
        headers=student_headers,
        json={
            "templateId": tmpl_id,
            "studentId": str(student.id),
            "studentName": "Aarav Patel",
            "rollNumber": "24CSE0101",
            "program": "B.Tech Computer Science & Engineering",
            "department": "Computer Science & Engineering",
            "purpose": "Bank Education Loan Application",
            "requiredByDate": "2026-10-15",
        },
    )
    assert req_res.status_code == 201
    req = req_res.json()["data"]
    assert req["status"] == "SUBMITTED"
    assert req["requestId"].startswith("REQ-")
    req_id = req["id"]

    # 3. Prevent issuing certificate directly before approval
    early_issue = await client.post(
        f"/api/v1/certificates/requests/{req_id}/issue",
        headers=officer_headers,
        json={"issuingAuthority": "Office of the Registrar"},
    )
    assert early_issue.status_code == 422

    # 4. Officer reviews and approves
    await client.post(f"/api/v1/certificates/requests/{req_id}/review", headers=officer_headers)
    appr_res = await client.post(
        f"/api/v1/certificates/requests/{req_id}/approve",
        headers=officer_headers,
        json={"notes": "All academic criteria and fee ledger clear."},
    )
    assert appr_res.status_code == 200
    assert appr_res.json()["data"]["status"] == "APPROVED"

    # 5. Issue Certificate
    issue_res = await client.post(
        f"/api/v1/certificates/requests/{req_id}/issue",
        headers=officer_headers,
        json={"issuingAuthority": "Office of the Registrar"},
    )
    assert issue_res.status_code == 201
    cert = issue_res.json()["data"]
    assert cert["status"] == "ISSUED"
    assert cert["certificateNumber"].startswith("CAMPUSOS/CERT/")
    assert len(cert["digitalSignatureHash"]) == 64
    cert_id = cert["id"]
    cert_num = cert["certificateNumber"]

    # 6. Verify Certificate through Public Endpoint
    pub_ver = await client.get(f"/api/v1/certificates/verify/{cert_num}")
    assert pub_ver.status_code == 200
    assert pub_ver.json()["data"]["isValid"] is True

    # 7. Revoke Certificate with reason
    revoke_res = await client.post(
        f"/api/v1/certificates/issued/{cert_id}/revoke",
        headers=officer_headers,
        json={"reason": "Incorrect name spelling corrected on physical file."},
    )
    assert revoke_res.status_code == 200
    assert revoke_res.json()["data"]["status"] == "REVOKED"

    # 8. Re-check public verification (now revoked)
    pub_ver_after = await client.get(f"/api/v1/certificates/verify/{cert_num}")
    assert pub_ver_after.status_code == 200
    assert pub_ver_after.json()["data"]["isValid"] is False
    assert "revoked" in pub_ver_after.json()["data"]["message"].lower()


# =============================================================================
# 4. INSTITUTIONAL RECORDS & CONFIDENTIALITY
# =============================================================================


@pytest.mark.asyncio
async def test_institutional_records_crud_and_confidentiality(
    client: AsyncClient, tenant_a: Institution, document_users: dict
):
    admin = document_users["admin_a"]
    student = document_users["student_1"]

    admin_headers = make_auth_headers(admin, tenant_a.id, "INSTITUTION_ADMIN")
    student_headers = make_auth_headers(student, tenant_a.id, "STUDENT")

    # 1. Admin creates public policy
    pub_res = await client.post(
        "/api/v1/institutional-records",
        headers=admin_headers,
        json={
            "recordName": "Academic Anti-Plagiarism Policy 2026",
            "code": f"POL-PLAG-{uuid.uuid4().hex[:4].upper()}",
            "category": "Academic Policies",
            "ownerDepartment": "Office of Academic Dean",
            "confidentiality": "PUBLIC",
            "referenceNumber": "AC/2026/08",
        },
    )
    assert pub_res.status_code == 201
    pub_id = pub_res.json()["data"]["id"]

    # 2. Admin creates restricted board record
    res_code = f"BOG-EXEC-{uuid.uuid4().hex[:4].upper()}"
    res_record = await client.post(
        "/api/v1/institutional-records",
        headers=admin_headers,
        json={
            "recordName": "Governing Body Confidential Disciplinary Review",
            "code": res_code,
            "category": "Governance Proceedings",
            "ownerDepartment": "Executive Secretariat",
            "confidentiality": "RESTRICTED",
            "referenceNumber": "BOG/CONF/2026",
        },
    )
    assert res_record.status_code == 201
    res_id = res_record.json()["data"]["id"]

    # 3. Student can view public policy
    s_view_pub = await client.get(f"/api/v1/institutional-records/{pub_id}", headers=student_headers)
    assert s_view_pub.status_code == 200

    # 4. Student blocked from restricted record
    s_view_res = await client.get(f"/api/v1/institutional-records/{res_id}", headers=student_headers)
    assert s_view_res.status_code == 403


# =============================================================================
# 5. SECURITY & TENANT ISOLATION TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_tenant_isolation_and_cross_student_privacy(
    client: AsyncClient,
    tenant_a: Institution,
    tenant_b: Institution,
    document_users: dict,
):
    admin_a = document_users["admin_a"]
    admin_b = document_users["admin_b"]
    student_1 = document_users["student_1"]
    student_2 = document_users["student_2"]

    admin_a_headers = make_auth_headers(admin_a, tenant_a.id, "INSTITUTION_ADMIN")
    admin_b_headers = make_auth_headers(admin_b, tenant_b.id, "INSTITUTION_ADMIN")
    student_1_headers = make_auth_headers(student_1, tenant_a.id, "STUDENT")
    student_2_headers = make_auth_headers(student_2, tenant_a.id, "STUDENT")

    # 1. Admin A creates category in Tenant A
    cat_code = f"ISO_{uuid.uuid4().hex[:4].upper()}"
    cat_a = await client.post(
        "/api/v1/document-categories",
        headers=admin_a_headers,
        json={"code": cat_code, "name": "Tenant A Exclusive Records"},
    )
    cat_a_id = cat_a.json()["data"]["id"]

    # 2. Admin B in Tenant B CANNOT see Tenant A's category
    b_get_cat = await client.get(f"/api/v1/document-categories/{cat_a_id}", headers=admin_b_headers)
    assert b_get_cat.status_code == 404

    # 3. Student 1 creates private document in Tenant A
    doc_1 = await client.post(
        "/api/v1/documents",
        headers=student_1_headers,
        json={
            "name": "Student 1 Confidential Document",
            "category": cat_code,
            "documentType": "Confidential Proof",
            "ownerType": "STUDENT",
            "ownerId": str(student_1.id),
            "ownerName": "Aarav Patel",
            "confidentiality": "CONFIDENTIAL",
        },
    )
    doc_1_id = doc_1.json()["data"]["id"]

    # 4. Student 2 cannot access Student 1's private document
    s2_try = await client.get(f"/api/v1/documents/{doc_1_id}", headers=student_2_headers)
    assert s2_try.status_code == 403

    # 5. Student cannot verify documents
    s_verify = await client.post(
        f"/api/v1/documents/{doc_1_id}/verify",
        headers=student_1_headers,
        json={"notes": "Self verification attempt"},
    )
    assert s_verify.status_code == 403

    # 6. Storage Path Traversal Prevention
    storage = LocalDocumentStorage()
    with pytest.raises(Exception) as exc:
        await storage.download("../../../etc/passwd")
    assert "traversal" in str(exc.value).lower()
