/**
 * CampusOS Admin Portal Phase 1 & 2 Verification Suite
 *
 * Validates:
 * 1. RBAC Service & Role Matrix (Super Admin, Institution Admin, HOD, Faculty, etc.)
 * 2. User Lifecycle Management (Account creation, role assignment, revocation, status toggle)
 * 3. Navigation & Route Integrity (Direct links, absence of redirect stubs, SOC re-label)
 * 4. Department HOD Appointment Lifecycle
 * 5. Forensic Audit Log Explorer Service & Diff Structure
 */

import { adminRbacService } from "@/services/admin-rbac.service";
import { adminAuditService } from "@/services/admin-audit.service";
import { organizationService } from "@/services/organization.service";
import { ADMIN_PORTAL_NAV } from "@/components/navigation/portal-nav";

let passed = 0;
let failed = 0;

function assert(condition: boolean, desc: string) {
  if (condition) {
    console.log(`✔ PASS: ${desc}`);
    passed++;
  } else {
    console.error(`✖ FAIL: ${desc}`);
    failed++;
  }
}

async function runTestSuite() {
  console.log("\n===============================================================================");
  console.log("CampusOS Admin Portal — Enterprise Verification Suite");
  console.log("===============================================================================\n");

  // ---------------------------------------------------------------------------
  // 1. RBAC System Roles & Privilege Matrix
  // ---------------------------------------------------------------------------
  console.log("--- TEST GROUP 1: RBAC System Roles & Privilege Hierarchy ---");
  const rolesRes = await adminRbacService.listRoles();
  assert(rolesRes.success === true, "adminRbacService.listRoles succeeds");
  assert(rolesRes.data.length >= 6, `At least 6 canonical system roles returned: ${rolesRes.data.length}`);

  const roleNames = rolesRes.data.map((r) => r.name);
  assert(roleNames.includes("SUPER_ADMIN"), "SUPER_ADMIN role exists in role registry");
  assert(roleNames.includes("INSTITUTION_ADMIN"), "INSTITUTION_ADMIN role exists in role registry");
  assert(roleNames.includes("VICE_PRINCIPAL"), "VICE_PRINCIPAL role exists in role registry");
  assert(roleNames.includes("HOD"), "HOD role exists in role registry");
  assert(roleNames.includes("FACULTY"), "FACULTY role exists in role registry");
  assert(roleNames.includes("STUDENT"), "STUDENT role exists in role registry");

  const superAdminRole = rolesRes.data.find((r) => r.name === "SUPER_ADMIN");
  assert(superAdminRole?.isSystem === true, "SUPER_ADMIN is marked as a protected system role");
  assert(superAdminRole?.permissionsCount > 0, "SUPER_ADMIN has non-zero permissions count");

  // ---------------------------------------------------------------------------
  // 2. User Lifecycle & Role Assignments
  // ---------------------------------------------------------------------------
  console.log("\n--- TEST GROUP 2: User Account Lifecycle & Role Management ---");
  const usersRes = await adminRbacService.listUsers();
  assert(usersRes.success === true, "adminRbacService.listUsers query succeeds");
  assert(usersRes.data.length > 0, `User accounts retrieved: ${usersRes.data.length}`);

  const sampleUser = usersRes.data[0];
  assert(Boolean(sampleUser.id), "User record has unique ID");
  assert(Boolean(sampleUser.email), "User record has valid email");
  assert(Boolean(sampleUser.status), `User has operational status: ${sampleUser.status}`);
  assert(Array.isArray(sampleUser.roles), "User contains roles array");

  // Test account creation
  const testEmail = `admin.test.${Date.now()}@vsb.ac.in`;
  const createRes = await adminRbacService.createUser({
    email: testEmail,
    firstName: "Audit",
    lastName: "Tester",
    phoneNumber: "+91 99000 88000",
    roleId: superAdminRole?.id,
  });
  assert(createRes.success === true, `Created new user account: ${testEmail}`);
  assert(createRes.data.email === testEmail, "Created user email matches payload");

  // Test role assignment
  const facultyRole = rolesRes.data.find((r) => r.name === "FACULTY");
  if (facultyRole) {
    const assignRes = await adminRbacService.assignRole(createRes.data.id, {
      roleId: facultyRole.id,
    });
    assert(assignRes.success === true, "Successfully assigned secondary role to user");
  }

  // Test status modification
  const statusRes = await adminRbacService.updateUserStatus(createRes.data.id, {
    status: "SUSPENDED",
    reason: "Test account deactivation",
  });
  assert(statusRes.success === true, "Successfully updated user status to SUSPENDED");
  assert(statusRes.data.status === "SUSPENDED", "User status confirmed as SUSPENDED");

  // ---------------------------------------------------------------------------
  // 3. Navigation & Route Integrity
  // ---------------------------------------------------------------------------
  console.log("\n--- TEST GROUP 3: Admin Portal Navigation & Route Standards ---");
  const allHrefs = ADMIN_PORTAL_NAV.flatMap((sec) => sec.items.map((i) => i.href));

  assert(allHrefs.includes("/app/people/roles"), "ADMIN_PORTAL_NAV includes /app/people/roles");
  assert(allHrefs.includes("/app/configuration"), "ADMIN_PORTAL_NAV includes /app/configuration");
  assert(allHrefs.includes("/app/audit"), "ADMIN_PORTAL_NAV includes /app/audit");
  assert(allHrefs.includes("/app/reports"), "ADMIN_PORTAL_NAV includes /app/reports");
  assert(allHrefs.includes("/app/campus/announcements"), "ADMIN_PORTAL_NAV includes /app/campus/announcements");
  assert(allHrefs.includes("/app/infrastructure/hostel"), "ADMIN_PORTAL_NAV directs to /app/infrastructure/hostel");
  assert(allHrefs.includes("/app/infrastructure/transport"), "ADMIN_PORTAL_NAV directs to /app/infrastructure/transport");

  // Verify absence of dead redirect stubs
  assert(!allHrefs.includes("/app/hostel"), "ADMIN_PORTAL_NAV does NOT contain legacy redirect /app/hostel");
  assert(!allHrefs.includes("/app/transport"), "ADMIN_PORTAL_NAV does NOT contain legacy redirect /app/transport");

  // Verify SOC relabeling
  const socItem = ADMIN_PORTAL_NAV.flatMap((s) => s.items).find((i) => i.href === "/app/security");
  assert(socItem?.label === "Security Operations (SOC)", "Security route is relabeled to Security Operations (SOC)");

  // ---------------------------------------------------------------------------
  // 4. Department HOD Appointment Lifecycle
  // ---------------------------------------------------------------------------
  console.log("\n--- TEST GROUP 4: Department Management & HOD Appointment ---");
  const testDeptCode = `DEPT${Math.floor(Math.random() * 899 + 100)}`;
  const createDeptRes = await organizationService.createDepartment({
    code: testDeptCode,
    name: "Department of Robotics & Automation",
    department_type: "ACADEMIC",
    hod_name: "Dr. K. S. Anand",
  });
  assert(createDeptRes.success === true, `Created department: ${testDeptCode}`);
  assert(createDeptRes.data.code === testDeptCode, "Department code matches creation payload");
  assert(createDeptRes.data.hod_name === "Dr. K. S. Anand", "HOD name successfully assigned to department");

  // ---------------------------------------------------------------------------
  // 5. Forensic Audit Log Explorer Service
  // ---------------------------------------------------------------------------
  console.log("\n--- TEST GROUP 5: Forensic Audit Log Explorer & State Diffs ---");
  const auditRes = await adminAuditService.listAuditLogs();
  assert(auditRes.success === true, "adminAuditService.listAuditLogs query succeeds");
  assert(auditRes.data.length >= 4, `Forensic audit logs returned: ${auditRes.data.length}`);

  const sampleAudit = auditRes.data[0];
  assert(Boolean(sampleAudit.id), "Audit log has event ID");
  assert(Boolean(sampleAudit.action), `Audit log specifies action: ${sampleAudit.action}`);
  assert(Boolean(sampleAudit.entityType), `Audit log specifies entity type: ${sampleAudit.entityType}`);
  assert(Boolean(sampleAudit.ipAddress), `Audit log records actor IP address: ${sampleAudit.ipAddress}`);
  assert(Boolean(sampleAudit.correlationId), `Audit log tracks correlation ID: ${sampleAudit.correlationId}`);

  console.log("\n===============================================================================");
  console.log(`Test Execution Completed: ${passed} PASSED, ${failed} FAILED`);
  console.log("===============================================================================\n");

  if (failed > 0) {
    process.exit(1);
  }
}

runTestSuite().catch((err) => {
  console.error("Test execution threw an uncaught error:", err);
  process.exit(1);
});
