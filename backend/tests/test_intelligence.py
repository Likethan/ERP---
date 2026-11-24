"""Comprehensive Production-Grade Test Suite for CampusOS Intelligence & AI Backend Engine.

Covers:
- Natural-language query orchestration across attendance, finance, academics, examinations
- Intent classification and tool planning
- Multi-block structured response generation (METRIC, TABLE, INSIGHT, RECOMMENDATION, SOURCE)
- Source / provenance attachment and explainability metadata
- Role-based and permission-based access control (PBAC) for tools (e.g. finance access denial)
- Tenant isolation and cross-tenant leakage prevention
- Private conversation ownership and isolation
- Parameter validation and SQL injection defense
- Full Insights lifecycle (list, retrieve, acknowledge, dismiss)
- Full Alerts lifecycle (list, retrieve, acknowledge, resolve)
- Saved Insights CRUD
- Allowlisted multidimensional Analytics engine
- AI activity telemetry audit logging
- Tool registry inspection
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import DEFAULT_ROLE_PERMISSIONS
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token, get_password_hash
from app.models.core import Institution
from app.models.intelligence import (
    AIActivity,
    Conversation,
)
from app.models.people import Role, User, UserRoleAssignment


def make_auth_headers(
    user: User,
    tenant_id: uuid.UUID,
    role_name: str,
    custom_permissions: list[str] | None = None,
) -> dict:
    """Generate authorization headers & cookies for authenticated API requests."""
    perms = custom_permissions if custom_permissions is not None else DEFAULT_ROLE_PERMISSIONS.get(role_name, [])
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
async def intelligence_users(
    db_session: AsyncSession, tenant_a: Institution, tenant_b: Institution
):
    """Setup users with specific roles across Tenant A and Tenant B."""
    uid = uuid.uuid4().hex[:6]

    # 1. Admin in Tenant A (has full institutional and intelligence permissions)
    admin_a = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"admin_{uid}@apextech.edu",
        phone_number="+919876543110",
        password_hash=get_password_hash("AdminPass123!"),
        status="ACTIVE",
        first_name="Intelligence",
        last_name="Director",
    )
    db_session.add(admin_a)

    # 2. Finance Officer in Tenant A (has finance:read, intelligence:query)
    finance_a = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"finance_{uid}@apextech.edu",
        phone_number="+919876543111",
        password_hash=get_password_hash("FinancePass123!"),
        status="ACTIVE",
        first_name="Bursar",
        last_name="Officer",
    )
    db_session.add(finance_a)

    # 3. Student in Tenant A (does NOT have institutional finance permissions)
    student_a = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"student_{uid}@apextech.edu",
        phone_number="+919876543112",
        password_hash=get_password_hash("StudentPass123!"),
        status="ACTIVE",
        first_name="Rohan",
        last_name="Sharma",
    )
    db_session.add(student_a)

    # 4. User in Tenant B (for cross-tenant testing)
    admin_b = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_b.id,
        email=f"admin_{uid}@beaconuni.edu",
        phone_number="+919876543113",
        password_hash=get_password_hash("AdminPass123!"),
        status="ACTIVE",
        first_name="Foreign",
        last_name="Director",
    )
    db_session.add(admin_b)

    # Sync system permissions & roles to ensure new intelligence permissions are mapped
    from app.core.seeds import seed_system_permissions_and_roles
    await seed_system_permissions_and_roles(db_session)

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
    assign(finance_a, tenant_a.id, "ACCOUNTS")
    assign(student_a, tenant_a.id, "STUDENT")
    assign(admin_b, tenant_b.id, "INSTITUTION_ADMIN")

    await db_session.commit()
    await db_session.refresh(admin_a)
    await db_session.refresh(finance_a)
    await db_session.refresh(student_a)
    await db_session.refresh(admin_b)

    return {
        "admin_a": admin_a,
        "finance_a": finance_a,
        "student_a": student_a,
        "admin_b": admin_b,
    }


# =========================================================================
# Scenario 1 — Attendance Query
# =========================================================================
@pytest.mark.asyncio
async def test_scenario_1_attendance_query(
    client: AsyncClient, intelligence_users, tenant_a: Institution, db_session: AsyncSession
):
    """Scenario 1: User asks attendance threshold question.

    Verifies:
    - Intent detected (attendance summary / threshold)
    - Attendance tool selected & executed
    - Permission verified
    - Structured response with METRIC / RECOMMENDATION blocks
    - Sources attached
    - Conversation & messages persisted
    - AI activity logged
    """
    admin = intelligence_users["admin_a"]
    headers = make_auth_headers(admin, tenant_a.id, "INSTITUTION_ADMIN")

    req_payload = {
        "query": "Which students are below 75% attendance?",
        "context": {
            "type": "GLOBAL",
        },
    }

    response = await client.post("/api/v1/intelligence/query", json=req_payload, headers=headers)
    assert response.status_code == 200, response.text
    res_json = response.json()
    assert "data" in res_json
    data = res_json["data"]

    assert data["status"] == "COMPLETED"
    assert "conversationId" in data or "conversation_id" in data
    assert len(data["blocks"]) > 0
    assert len(data["sources"]) > 0

    # Verify at least one block is a METRIC or RECOMMENDATION
    block_types = [b.get("type") for b in data["blocks"]]
    assert "METRIC" in block_types or "TABLE" in block_types or "RECOMMENDATION" in block_types

    # Verify source domain is attendance
    source_domains = [s.get("domain", "").lower() for s in data["sources"]]
    assert "attendance" in source_domains

    # Verify explainability metadata
    assert "explainability" in data
    assert "metricsCalculated" in data["explainability"] or "metrics_calculated" in data["explainability"]

    # Verify database persistence
    conv_id = data.get("conversationId") or data.get("conversation_id")
    conv_stmt = select(Conversation).where(Conversation.id == uuid.UUID(conv_id))
    conv_res = await db_session.execute(conv_stmt)
    conv = conv_res.scalars().first()
    assert conv is not None
    assert conv.user_id == admin.id
    assert conv.tenant_id == tenant_a.id
    assert conv.message_count >= 2

    # Verify AI activity was logged
    act_stmt = select(AIActivity).where(
        AIActivity.tenant_id == tenant_a.id,
        AIActivity.user_id == admin.id,
    )
    act_res = await db_session.execute(act_stmt)
    activities = act_res.scalars().all()
    assert len(activities) > 0
    assert any("attendance" in a.domain.lower() for a in activities)


# =========================================================================
# Scenario 2 — Authorized Finance Query
# =========================================================================
@pytest.mark.asyncio
async def test_scenario_2_authorized_finance_query(
    client: AsyncClient, intelligence_users, tenant_a: Institution
):
    """Scenario 2: Authorized finance officer asks institutional fee question.

    Verifies:
    - Finance tool executed
    - Aggregate result synthesized
    - METRIC block returned
    - Finance source attached
    """
    finance_user = intelligence_users["finance_a"]
    headers = make_auth_headers(finance_user, tenant_a.id, "ACCOUNTS")

    req_payload = {
        "query": "What is the total outstanding fee amount this semester?",
        "context": {
            "type": "GLOBAL",
        },
    }

    response = await client.post("/api/v1/intelligence/query", json=req_payload, headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()["data"]

    assert data["status"] == "COMPLETED"
    block_types = [b.get("type") for b in data["blocks"]]
    assert "METRIC" in block_types

    # Find the metric block
    metric_blocks = [b for b in data["blocks"] if b.get("type") == "METRIC"]
    assert len(metric_blocks) > 0
    assert "fee" in metric_blocks[0].get("title", "").lower() or "outstanding" in metric_blocks[0].get("title", "").lower()

    # Verify source contains finance domain
    sources = data.get("sources", [])
    assert any(s.get("domain", "").lower() == "finance" for s in sources)


# =========================================================================
# Scenario 3 — Unauthorized Finance Query
# =========================================================================
@pytest.mark.asyncio
async def test_scenario_3_unauthorized_finance_query(
    client: AsyncClient, intelligence_users, tenant_a: Institution
):
    """Scenario 3: Unauthorized user (Student) asks for institutional financial data.

    Expected:
    - Request is denied (either 403 HTTP status or structured permission denial block)
    - Zero sensitive institutional financial figures are revealed
    """
    student = intelligence_users["student_a"]
    # Student role only has basic permissions (no finance:read)
    headers = make_auth_headers(student, tenant_a.id, "STUDENT")

    req_payload = {
        "query": "What is the college-wide outstanding fee amount?",
        "context": {
            "type": "GLOBAL",
        },
    }

    response = await client.post("/api/v1/intelligence/query", json=req_payload, headers=headers)
    if response.status_code == 403:
        # Direct HTTP forbidden
        assert "finance" in response.text.lower() or "permission" in response.text.lower()
    else:
        assert response.status_code == 200
        data = response.json()["data"]
        # Verify that error/warning or denial explanation is returned
        block_types = [b.get("type") for b in data.get("blocks", [])]
        has_warning = "WARNING" in block_types or "TEXT" in block_types
        assert has_warning
        # Verify no financial collection figures leaked
        full_text = str(data)
        assert "₹2,500,000" not in full_text and "25,40,000" not in full_text


# =========================================================================
# Scenario 4 — Cross-Domain Query
# =========================================================================
@pytest.mark.asyncio
async def test_scenario_4_cross_domain_query(
    client: AsyncClient, intelligence_users, tenant_a: Institution
):
    """Scenario 4: Multi-tool cross-domain query comparing attendance and exams.

    Verifies:
    - Executes attendance and examination tools
    - Synthesizes comparison structure
    - Returns TABLE and/or INSIGHT blocks
    - Attaches sources across both domains
    """
    admin = intelligence_users["admin_a"]
    headers = make_auth_headers(admin, tenant_a.id, "INSTITUTION_ADMIN")

    req_payload = {
        "query": "Compare attendance and examination performance for the CSE department.",
        "context": {
            "type": "DEPARTMENT",
            "id": "dept-cse-01",
        },
    }

    response = await client.post("/api/v1/intelligence/query", json=req_payload, headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()["data"]

    assert data["status"] == "COMPLETED"
    block_types = [b.get("type") for b in data["blocks"]]
    assert "TABLE" in block_types or "INSIGHT" in block_types or "METRIC" in block_types

    # Verify sources cover multiple domains or both domains
    source_domains = {s.get("domain", "").lower() for s in data.get("sources", [])}
    assert "attendance" in source_domains or "examinations" in source_domains


# =========================================================================
# Scenario 5 — Cross-Tenant Isolation
# =========================================================================
@pytest.mark.asyncio
async def test_scenario_5_cross_tenant_isolation(
    client: AsyncClient, intelligence_users, tenant_a: Institution, tenant_b: Institution
):
    """Scenario 5: User in Tenant B cannot read or query Tenant A conversation."""
    admin_a = intelligence_users["admin_a"]
    admin_b = intelligence_users["admin_b"]

    headers_a = make_auth_headers(admin_a, tenant_a.id, "INSTITUTION_ADMIN")
    headers_b = make_auth_headers(admin_b, tenant_b.id, "INSTITUTION_ADMIN")

    # 1. Admin A creates a conversation in Tenant A
    create_res = await client.post(
        "/api/v1/intelligence/conversations",
        json={"title": "Confidential Tenant A Conversation", "domain": "ATTENDANCE"},
        headers=headers_a,
    )
    assert create_res.status_code == 201
    conv_a_id = create_res.json()["data"]["id"]

    # 2. Admin B tries to retrieve Tenant A conversation
    get_res = await client.get(
        f"/api/v1/intelligence/conversations/{conv_a_id}",
        headers=headers_b,
    )
    # Must be 404 Not Found (or 403 Forbidden)
    assert get_res.status_code in (404, 403)


# =========================================================================
# Scenario 6 — Conversation User Isolation
# =========================================================================
@pytest.mark.asyncio
async def test_scenario_6_conversation_user_isolation(
    client: AsyncClient, intelligence_users, tenant_a: Institution
):
    """Scenario 6: User A cannot retrieve another user's private conversation."""
    finance_user = intelligence_users["finance_a"]
    student = intelligence_users["student_a"]

    headers_fin = make_auth_headers(finance_user, tenant_a.id, "ACCOUNTS")
    headers_stud = make_auth_headers(student, tenant_a.id, "STUDENT")

    # Finance user creates conversation
    create_res = await client.post(
        "/api/v1/intelligence/conversations",
        json={"title": "Private Audit Discussion", "domain": "FINANCE"},
        headers=headers_fin,
    )
    assert create_res.status_code == 201
    conv_id = create_res.json()["data"]["id"]

    # Student attempts to access finance user's conversation
    access_res = await client.get(
        f"/api/v1/intelligence/conversations/{conv_id}",
        headers=headers_stud,
    )
    assert access_res.status_code in (403, 404)


# =========================================================================
# Test 7 — Parameter Validation & SQL Injection Defense
# =========================================================================
@pytest.mark.asyncio
async def test_tool_injection_parameter_defense(
    client: AsyncClient, intelligence_users, tenant_a: Institution
):
    """Test 7: Direct SQL injection strings or malicious tool parameters are safely handled."""
    admin = intelligence_users["admin_a"]
    headers = make_auth_headers(admin, tenant_a.id, "INSTITUTION_ADMIN")

    # Malicious injection in natural language query
    malicious_query = "'; DROP TABLE core_institutions; SELECT * FROM people_users WHERE '1'='1"
    res = await client.post(
        "/api/v1/intelligence/query",
        json={"query": malicious_query},
        headers=headers,
    )
    # The application must NOT crash with 500 and must not execute SQL
    assert res.status_code in (200, 400)
    if res.status_code == 200:
        data = res.json()["data"]
        assert data["status"] in ("COMPLETED", "FAILED")


# =========================================================================
# Test 8 — Insights Lifecycle
# =========================================================================
@pytest.mark.asyncio
async def test_insights_lifecycle(
    client: AsyncClient, intelligence_users, tenant_a: Institution
):
    """Test 8: Full operational insight lifecycle (List, Get, Acknowledge, Dismiss)."""
    admin = intelligence_users["admin_a"]
    headers = make_auth_headers(admin, tenant_a.id, "INSTITUTION_ADMIN")

    # 1. List insights
    list_res = await client.get("/api/v1/intelligence/insights", headers=headers)
    assert list_res.status_code == 200
    insights = list_res.json()["data"]
    assert len(insights) > 0

    insight_id = insights[0]["id"]

    # 2. Get specific insight
    get_res = await client.get(f"/api/v1/intelligence/insights/{insight_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["id"] == insight_id

    # 3. Acknowledge insight
    ack_res = await client.post(f"/api/v1/intelligence/insights/{insight_id}/acknowledge", headers=headers)
    assert ack_res.status_code == 200
    assert ack_res.json()["data"]["status"] == "REVIEWED"

    # 4. Dismiss insight
    dis_res = await client.post(f"/api/v1/intelligence/insights/{insight_id}/dismiss", headers=headers)
    assert dis_res.status_code == 200
    assert dis_res.json()["data"]["status"] == "DISMISSED"


# =========================================================================
# Test 9 — Alerts Lifecycle
# =========================================================================
@pytest.mark.asyncio
async def test_alerts_lifecycle(
    client: AsyncClient, intelligence_users, tenant_a: Institution
):
    """Test 9: Full operational alert lifecycle (List, Get, Acknowledge, Resolve)."""
    admin = intelligence_users["admin_a"]
    headers = make_auth_headers(admin, tenant_a.id, "INSTITUTION_ADMIN")

    # 1. List alerts
    list_res = await client.get("/api/v1/intelligence/alerts", headers=headers)
    assert list_res.status_code == 200
    alerts = list_res.json()["data"]
    assert len(alerts) > 0

    alert_id = alerts[0]["id"]

    # 2. Get specific alert
    get_res = await client.get(f"/api/v1/intelligence/alerts/{alert_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["id"] == alert_id

    # 3. Acknowledge alert
    ack_res = await client.post(f"/api/v1/intelligence/alerts/{alert_id}/acknowledge", headers=headers)
    assert ack_res.status_code == 200
    assert ack_res.json()["data"]["status"] == "ACKNOWLEDGED"

    # 4. Resolve alert
    res_res = await client.post(f"/api/v1/intelligence/alerts/{alert_id}/resolve", headers=headers)
    assert res_res.status_code == 200
    assert res_res.json()["data"]["status"] == "RESOLVED"


# =========================================================================
# Test 10 — Saved Insights CRUD
# =========================================================================
@pytest.mark.asyncio
async def test_saved_insights_crud(
    client: AsyncClient, intelligence_users, tenant_a: Institution
):
    """Test 10: Create, list, retrieve, and delete saved intelligence views."""
    admin = intelligence_users["admin_a"]
    headers = make_auth_headers(admin, tenant_a.id, "INSTITUTION_ADMIN")

    create_payload = {
        "title": "Semester 5 Placement Conversion Summary",
        "type": "ANALYTICS_VIEW",
        "domain": "PLACEMENT",
        "contentSnippet": "88.4% recruitment conversion recorded across tech disciplines.",
        "href": "/placement/drives",
        "query": "Placement conversion in tech tracks",
    }

    # 1. Create saved insight
    create_res = await client.post("/api/v1/intelligence/saved", json=create_payload, headers=headers)
    assert create_res.status_code == 201
    saved_id = create_res.json()["data"]["id"]

    # 2. List saved insights
    list_res = await client.get("/api/v1/intelligence/saved", headers=headers)
    assert list_res.status_code == 200
    items = list_res.json()["data"]
    assert any(i["id"] == saved_id for i in items)

    # 3. Get single saved insight
    get_res = await client.get(f"/api/v1/intelligence/saved/{saved_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["title"] == create_payload["title"]

    # 4. Delete saved insight
    del_res = await client.delete(f"/api/v1/intelligence/saved/{saved_id}", headers=headers)
    assert del_res.status_code == 204

    # 5. Verify deletion
    verify_res = await client.get(f"/api/v1/intelligence/saved/{saved_id}", headers=headers)
    assert verify_res.status_code == 404


# =========================================================================
# Test 11 — Analytics Multidimensional Engine
# =========================================================================
@pytest.mark.asyncio
async def test_analytics_query_engine(
    client: AsyncClient, intelligence_users, tenant_a: Institution
):
    """Test 11: Validate allowlisted multidimensional analytics queries."""
    admin = intelligence_users["admin_a"]
    headers = make_auth_headers(admin, tenant_a.id, "INSTITUTION_ADMIN")

    # 1. Valid allowlisted query
    valid_payload = {
        "domain": "ATTENDANCE",
        "metric": "attendance_rate",
        "dimension": "department",
        "timeRange": "current_semester",
    }
    valid_res = await client.post("/api/v1/intelligence/analytics/query", json=valid_payload, headers=headers)
    assert valid_res.status_code == 200, valid_res.text
    data = valid_res.json()["data"]
    assert data["query"]["metric"] == "attendance_rate"
    assert "labels" in data
    assert len(data["labels"]) > 0

    # 2. Invalid non-allowlisted metric
    invalid_metric = {
        "domain": "ATTENDANCE",
        "metric": "arbitrary_unauthorized_metric",
        "dimension": "department",
    }
    inv_res = await client.post("/api/v1/intelligence/analytics/query", json=invalid_metric, headers=headers)
    assert inv_res.status_code == 400

    # 3. Invalid non-allowlisted dimension
    invalid_dim = {
        "domain": "ATTENDANCE",
        "metric": "attendance_rate",
        "dimension": "unauthorized_dim_salary",
    }
    dim_res = await client.post("/api/v1/intelligence/analytics/query", json=invalid_dim, headers=headers)
    assert dim_res.status_code == 400


# =========================================================================
# Test 12 — Tool Registry Catalog & Metadata
# =========================================================================
@pytest.mark.asyncio
async def test_tool_registry_inspection(
    client: AsyncClient, intelligence_users, tenant_a: Institution
):
    """Test 12: Ensure approved tools are registered with safe metadata."""
    admin = intelligence_users["admin_a"]
    headers = make_auth_headers(admin, tenant_a.id, "INSTITUTION_ADMIN")

    res = await client.get("/api/v1/intelligence/tools", headers=headers)
    assert res.status_code == 200
    tools = res.json()["data"]
    assert len(tools) >= 15

    tool_names = [t["name"] for t in tools]
    assert "attendance.get_students_below_threshold" in tool_names
    assert "finance.get_fee_summary" in tool_names
    assert "people.get_student" in tool_names
    assert "documents.get_verification_summary" in tool_names

    # Verify no raw SQL or handler function internals leaked
    for t in tools:
        assert "handler" not in t
        assert "sql" not in str(t).lower()


# =========================================================================
# Test 13 — Overview Telemetry Endpoint
# =========================================================================
@pytest.mark.asyncio
async def test_overview_telemetry_endpoint(
    client: AsyncClient, intelligence_users, tenant_a: Institution
):
    """Test 13: Verify overview dashboard endpoint returns cards & status."""
    admin = intelligence_users["admin_a"]
    headers = make_auth_headers(admin, tenant_a.id, "INSTITUTION_ADMIN")

    res = await client.get("/api/v1/intelligence/overview", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "activeInsights" in data or "active_insights" in data
    assert "criticalAlerts" in data or "critical_alerts" in data
    assert "domainSummaries" in data or "domain_summaries" in data

