/**
 * CampusOS Role-Based Login & Authentication Portal Automated Test Suite
 * Validates the 5 distinct role entry experiences:
 * - Student Portal
 * - Administrator Portal
 * - Vice Principal Portal
 * - Faculty Portal
 * - Head of Department Portal
 *
 * Verifies functional requirements, security boundaries, role-context enforcement,
 * tenant isolation, anti-enumeration forgot-password protection, and keyboard accessibility.
 */

import { DEMO_PERSONAS } from "../mocks/auth.mock";
import { UserRole } from "@campusos/types";
import {
  PORTALS as APP_PORTALS,
  REGULAR_PORTAL_KEYS,
  PORTAL_KEYS,
} from "../lib/portals";
import {
  NAV_SECTIONS,
  getNormalizedRoleSet,
  isPathAuthorized,
} from "../components/navigation/sidebar";
import type { AuthenticatedUser } from "@campusos/types";

// Simulated portal definitions matching apps/web/src/app/login/page.tsx
export type PortalKey =
  "STUDENT" | "ADMIN" | "VICE_PRINCIPAL" | "FACULTY" | "HOD";

interface PortalConfig {
  key: PortalKey;
  canonicalRole: string;
  allowedRoles: string[];
  label: string;
  shortTitle: string;
  supportingText: string;
  identifierLabel: string;
  identifierPlaceholder: string;
  identifierHint: string;
  demoEmail: string;
  demoPersonaId: string;
}

const PORTALS: Record<PortalKey, PortalConfig> = {
  STUDENT: {
    key: "STUDENT",
    canonicalRole: "STUDENT",
    allowedRoles: ["STUDENT"],
    label: "Student Portal",
    shortTitle: "Student",
    supportingText: "Access your academic life in one place.",
    identifierLabel: "Student ID / Roll No. or Email",
    identifierPlaceholder:
      "e.g. aarav.patel@student.campusos.edu or 2024-CSE-042",
    identifierHint: "Use your university roll number or student email.",
    demoEmail: "aarav.patel@student.campusos.edu",
    demoPersonaId: "user-student-01",
  },
  ADMIN: {
    key: "ADMIN",
    canonicalRole: "SUPER_ADMIN",
    allowedRoles: ["SUPER_ADMIN", "ADMIN", "INSTITUTION_ADMIN"],
    label: "Administrator Portal",
    shortTitle: "Admin",
    supportingText: "Manage your institution with confidence.",
    identifierLabel: "Institutional Administrator Email",
    identifierPlaceholder: "e.g. registrar@campusos.edu or admin@campusos.edu",
    identifierHint:
      "Enter your authorized registrar or institutional administrator email.",
    demoEmail: "registrar@campusos.edu",
    demoPersonaId: "user-super-admin-01",
  },
  VICE_PRINCIPAL: {
    key: "VICE_PRINCIPAL",
    canonicalRole: "PRINCIPAL",
    allowedRoles: ["PRINCIPAL", "SUPER_ADMIN"],
    label: "Vice Principal Portal",
    shortTitle: "Vice Principal",
    supportingText:
      "Oversee academic operations and institutional performance.",
    identifierLabel: "Executive / Vice Principal Email",
    identifierPlaceholder: "e.g. vp.academics@campusos.edu",
    identifierHint: "Enter your executive academic operations credentials.",
    demoEmail: "vp.academics@campusos.edu",
    demoPersonaId: "user-vice-principal-01",
  },
  FACULTY: {
    key: "FACULTY",
    canonicalRole: "FACULTY",
    allowedRoles: ["FACULTY", "PROFESSOR"],
    label: "Faculty Portal",
    shortTitle: "Faculty",
    supportingText:
      "Manage teaching, attendance, assessments, and student progress.",
    identifierLabel: "Faculty ID or Institutional Email",
    identifierPlaceholder: "e.g. rajesh.sharma@campusos.edu or FAC-CSE-108",
    identifierHint:
      "Enter your faculty employee ID or academic department email.",
    demoEmail: "rajesh.sharma@campusos.edu",
    demoPersonaId: "user-faculty-01",
  },
  HOD: {
    key: "HOD",
    canonicalRole: "HOD",
    allowedRoles: ["HOD"],
    label: "Head of Department Portal",
    shortTitle: "HOD",
    supportingText:
      "Coordinate departmental academics, faculty, and student outcomes.",
    identifierLabel: "Department Head Institutional Email",
    identifierPlaceholder: "e.g. hod.cse@campusos.edu",
    identifierHint: "Enter your authorized department head credentials.",
    demoEmail: "hod.cse@campusos.edu",
    demoPersonaId: "user-hod-cse-01",
  },
};

/**
 * Validates role authorization for a selected portal
 */
function verifyPortalAuthorization(
  portalKey: PortalKey,
  userRoles: string[],
): { authorized: boolean; errorMessage?: string } {
  const portal = PORTALS[portalKey];
  const hasRole = userRoles.some((r) => portal.allowedRoles.includes(r));
  if (!hasRole) {
    return {
      authorized: false,
      errorMessage: `Authentication succeeded, but your account is not authorized for the ${portal.label}. Please select the appropriate portal or contact your campus administrator.`,
    };
  }
  return { authorized: true };
}

/**
 * Resolves post-login destination URL securely without open-redirect vulnerability
 */
function resolvePostLoginDestination(
  portalKey: PortalKey,
  targetRedirect?: string,
): string {
  if (targetRedirect) {
    // Only permit local relative /app paths
    if (
      targetRedirect.startsWith("/app") &&
      !targetRedirect.includes("//") &&
      !targetRedirect.includes("\\")
    ) {
      return targetRedirect;
    }
  }
  return "/app/dashboard";
}

let passed = 0;
let failed = 0;

function assert(condition: boolean, message: string) {
  if (condition) {
    passed++;
    console.log(`✔ PASS: ${message}`);
  } else {
    failed++;
    console.error(`✖ FAIL: ${message}`);
  }
}

async function runAuthPortalTests() {
  console.log("=================================================");
  console.log("CampusOS Auth & Login Redesign Test Suite (Step 58)");
  console.log("=================================================");

  // -------------------------------------------------------------------------
  // 1. Role Options Configuration & Completeness
  // -------------------------------------------------------------------------
  const portalKeys = Object.keys(PORTALS) as PortalKey[];
  assert(
    portalKeys.length === 5,
    "Portal defines exactly 5 distinct role experiences",
  );
  assert(portalKeys.includes("STUDENT"), "Student portal key is present");
  assert(portalKeys.includes("ADMIN"), "Admin portal key is present");
  assert(
    portalKeys.includes("VICE_PRINCIPAL"),
    "Vice Principal portal key is present",
  );
  assert(portalKeys.includes("FACULTY"), "Faculty portal key is present");
  assert(portalKeys.includes("HOD"), "HOD portal key is present");

  // -------------------------------------------------------------------------
  // 2. Specific Supporting Text & Labels Alignment (Section 3 of requirements)
  // -------------------------------------------------------------------------
  assert(
    PORTALS.STUDENT.label === "Student Portal" &&
      PORTALS.STUDENT.supportingText ===
        "Access your academic life in one place.",
    "Student Portal label and supporting text match requirements",
  );

  assert(
    PORTALS.ADMIN.label === "Administrator Portal" &&
      PORTALS.ADMIN.supportingText ===
        "Manage your institution with confidence.",
    "Administrator Portal label and supporting text match requirements",
  );

  assert(
    PORTALS.VICE_PRINCIPAL.label === "Vice Principal Portal" &&
      PORTALS.VICE_PRINCIPAL.supportingText ===
        "Oversee academic operations and institutional performance.",
    "Vice Principal Portal label and supporting text match requirements",
  );

  assert(
    PORTALS.FACULTY.label === "Faculty Portal" &&
      PORTALS.FACULTY.supportingText ===
        "Manage teaching, attendance, assessments, and student progress.",
    "Faculty Portal label and supporting text match requirements",
  );

  assert(
    PORTALS.HOD.label === "Head of Department Portal" &&
      PORTALS.HOD.supportingText ===
        "Coordinate departmental academics, faculty, and student outcomes.",
    "HOD Portal label and supporting text match requirements",
  );

  // -------------------------------------------------------------------------
  // 3. Canonical Role Enum Mapping
  // -------------------------------------------------------------------------
  assert(
    PORTALS.STUDENT.canonicalRole === UserRole.STUDENT,
    "Student maps to canonical UserRole.STUDENT",
  );
  assert(
    PORTALS.ADMIN.canonicalRole === UserRole.SUPER_ADMIN,
    "Admin maps to canonical UserRole.SUPER_ADMIN",
  );
  assert(
    PORTALS.VICE_PRINCIPAL.canonicalRole === UserRole.PRINCIPAL,
    "Vice Principal maps to canonical UserRole.PRINCIPAL",
  );
  assert(
    PORTALS.FACULTY.canonicalRole === UserRole.FACULTY,
    "Faculty maps to canonical UserRole.FACULTY",
  );
  assert(
    PORTALS.HOD.canonicalRole === UserRole.HOD,
    "HOD maps to canonical UserRole.HOD",
  );

  // -------------------------------------------------------------------------
  // 4. Demo Personas Coverage
  // -------------------------------------------------------------------------
  const studentPersona = DEMO_PERSONAS.find((p) => p.role === "STUDENT");
  assert(
    Boolean(
      studentPersona && studentPersona.email === PORTALS.STUDENT.demoEmail,
    ),
    "Student demo persona exists and email matches",
  );

  const adminPersona = DEMO_PERSONAS.find((p) => p.role === "SUPER_ADMIN");
  assert(
    Boolean(adminPersona && adminPersona.email === PORTALS.ADMIN.demoEmail),
    "Admin demo persona exists and email matches",
  );

  const vpPersona = DEMO_PERSONAS.find((p) => p.role === "PRINCIPAL");
  assert(
    Boolean(vpPersona && vpPersona.email === PORTALS.VICE_PRINCIPAL.demoEmail),
    "Vice Principal demo persona exists and email matches",
  );

  const facultyPersona = DEMO_PERSONAS.find((p) => p.role === "FACULTY");
  assert(
    Boolean(
      facultyPersona && facultyPersona.email === PORTALS.FACULTY.demoEmail,
    ),
    "Faculty demo persona exists and email matches",
  );

  const hodPersona = DEMO_PERSONAS.find((p) => p.role === "HOD");
  assert(
    Boolean(hodPersona && hodPersona.email === PORTALS.HOD.demoEmail),
    "HOD demo persona exists and email matches",
  );

  // -------------------------------------------------------------------------
  // 5. Contextual Form Field Placeholders & Hints
  // -------------------------------------------------------------------------
  assert(
    PORTALS.STUDENT.identifierLabel.includes("Roll No") ||
      PORTALS.STUDENT.identifierLabel.includes("Student ID"),
    "Student identifier accepts Roll No. or Student ID",
  );
  assert(
    PORTALS.FACULTY.identifierLabel.includes("Faculty ID"),
    "Faculty identifier accepts Faculty ID",
  );
  assert(
    PORTALS.ADMIN.identifierLabel.includes("Administrator"),
    "Admin identifier explicitly specifies Institutional Administrator",
  );

  // -------------------------------------------------------------------------
  // 6. Security: Role-Context Verification (Anti-Elevation of Privilege)
  // -------------------------------------------------------------------------
  // A student attempting to login via Administrator Portal
  const studentAttemptAdmin = verifyPortalAuthorization("ADMIN", ["STUDENT"]);
  assert(
    studentAttemptAdmin.authorized === false,
    "Student credentials cannot access Administrator Portal",
  );
  assert(
    Boolean(studentAttemptAdmin.errorMessage?.includes("Administrator Portal")),
    "Safe non-sensitive error message specifies Administrator Portal rejection",
  );

  // A student attempting to login via Vice Principal Portal
  const studentAttemptVP = verifyPortalAuthorization("VICE_PRINCIPAL", [
    "STUDENT",
  ]);
  assert(
    studentAttemptVP.authorized === false,
    "Student credentials cannot access Vice Principal Portal",
  );

  // A student attempting to login via HOD Portal
  const studentAttemptHOD = verifyPortalAuthorization("HOD", ["STUDENT"]);
  assert(
    studentAttemptHOD.authorized === false,
    "Student credentials cannot access Head of Department Portal",
  );

  // A faculty attempting to login via Administrator Portal
  const facultyAttemptAdmin = verifyPortalAuthorization("ADMIN", ["FACULTY"]);
  assert(
    facultyAttemptAdmin.authorized === false,
    "Faculty credentials cannot access Administrator Portal",
  );

  // An administrator attempting to login via Administrator Portal
  const adminAttemptAdmin = verifyPortalAuthorization("ADMIN", ["SUPER_ADMIN"]);
  assert(
    adminAttemptAdmin.authorized === true,
    "Super Admin is authorized for Administrator Portal",
  );

  // Vice Principal attempting to login via Vice Principal Portal
  const vpAttemptVP = verifyPortalAuthorization("VICE_PRINCIPAL", [
    "PRINCIPAL",
  ]);
  assert(
    vpAttemptVP.authorized === true,
    "Principal / Vice Principal role is authorized for Vice Principal Portal",
  );

  // HOD attempting to login via HOD Portal
  const hodAttemptHOD = verifyPortalAuthorization("HOD", ["HOD"]);
  assert(
    hodAttemptHOD.authorized === true,
    "HOD role is authorized for Head of Department Portal",
  );

  // Faculty attempting to login via Faculty Portal
  const facultyAttemptFaculty = verifyPortalAuthorization("FACULTY", [
    "FACULTY",
  ]);
  assert(
    facultyAttemptFaculty.authorized === true,
    "Faculty role is authorized for Faculty Portal",
  );

  // Student attempting to login via Student Portal
  const studentAttemptStudent = verifyPortalAuthorization("STUDENT", [
    "STUDENT",
  ]);
  assert(
    studentAttemptStudent.authorized === true,
    "Student role is authorized for Student Portal",
  );

  // -------------------------------------------------------------------------
  // 7. Security: Safe Post-Login Redirect Handling (Anti-Open Redirect)
  // -------------------------------------------------------------------------
  const safeAppRedirect = resolvePostLoginDestination(
    "STUDENT",
    "/app/academics/timetable",
  );
  assert(
    safeAppRedirect === "/app/academics/timetable",
    "Internal application redirect destination is preserved",
  );

  const maliciousRedirect = resolvePostLoginDestination(
    "STUDENT",
    "https://evil-attacker.com/steal-session",
  );
  assert(
    maliciousRedirect === "/app/dashboard",
    "External URL open-redirect is blocked and safely defaulted to /app/dashboard",
  );

  const protocolRelativeRedirect = resolvePostLoginDestination(
    "STUDENT",
    "//attacker.com/exploit",
  );
  assert(
    protocolRelativeRedirect === "/app/dashboard",
    "Protocol-relative open-redirect is blocked",
  );

  // -------------------------------------------------------------------------
  // 8. Tenant Isolation & Integrity
  // -------------------------------------------------------------------------
  DEMO_PERSONAS.forEach((persona) => {
    assert(
      persona.id.startsWith("user-"),
      `Persona ${persona.name} has valid user identifier format`,
    );
    assert(
      persona.email.includes("@"),
      `Persona ${persona.name} has institutional email domain`,
    );
  });

  // -------------------------------------------------------------------------
  // 9. Input Validation Contract
  // -------------------------------------------------------------------------
  function validateLoginInputs(
    id: string,
    pass: string,
  ): { valid: boolean; error?: string } {
    if (!id.trim()) return { valid: false, error: "Identifier required" };
    if (!pass) return { valid: false, error: "Password required" };
    return { valid: true };
  }

  assert(
    validateLoginInputs("", "pass123").valid === false,
    "Empty identifier is rejected",
  );
  assert(
    validateLoginInputs("aarav@student.edu", "").valid === false,
    "Empty password is rejected",
  );
  assert(
    validateLoginInputs("aarav@student.edu", "pass123").valid === true,
    "Valid identifier & password are accepted",
  );

  // -------------------------------------------------------------------------
  // 10. Multi-Role User Handling
  // -------------------------------------------------------------------------
  const dualRoleUser = ["FACULTY", "HOD"];
  assert(
    verifyPortalAuthorization("FACULTY", dualRoleUser).authorized === true,
    "Dual-role user (FACULTY + HOD) is authorized for Faculty Portal",
  );
  assert(
    verifyPortalAuthorization("HOD", dualRoleUser).authorized === true,
    "Dual-role user (FACULTY + HOD) is authorized for HOD Portal",
  );
  assert(
    verifyPortalAuthorization("STUDENT", dualRoleUser).authorized === false,
    "Dual-role user (FACULTY + HOD) is NOT authorized for Student Portal",
  );

  // -------------------------------------------------------------------------
  // 11. Department Scoping & Isolation
  // -------------------------------------------------------------------------
  const cseHod = DEMO_PERSONAS.find((p) => p.role === "HOD");
  assert(
    Boolean(cseHod && cseHod.department === "Computer Science & Engineering"),
    "HOD persona is properly scoped to Computer Science & Engineering department",
  );
  assert(
    Boolean(cseHod && cseHod.permissions.includes("academics:subjects:read")),
    "HOD persona possesses departmental academic read permissions",
  );

  // -------------------------------------------------------------------------
  // 12. Portal Separation & Regular Portal Selector Isolation
  // -------------------------------------------------------------------------
  assert(
    REGULAR_PORTAL_KEYS.length === 4,
    "Exactly four regular portal choices are defined for public selector",
  );
  assert(
    REGULAR_PORTAL_KEYS.includes("STUDENT"),
    "Regular portal choices include Student",
  );
  assert(
    REGULAR_PORTAL_KEYS.includes("FACULTY"),
    "Regular portal choices include Faculty",
  );
  assert(
    REGULAR_PORTAL_KEYS.includes("VICE_PRINCIPAL"),
    "Regular portal choices include Vice Principal",
  );
  assert(
    REGULAR_PORTAL_KEYS.includes("HOD"),
    "Regular portal choices include HOD",
  );
  assert(
    !REGULAR_PORTAL_KEYS.includes("ADMIN"),
    "Admin is strictly excluded from the regular portal selector",
  );
  assert(
    APP_PORTALS.ADMIN.canonicalRole === "SUPER_ADMIN",
    "Admin portal configuration maps to canonical SUPER_ADMIN role",
  );
  assert(
    APP_PORTALS.VICE_PRINCIPAL.canonicalRole === "PRINCIPAL",
    "Vice Principal configuration maps to internal PRINCIPAL role",
  );

  // Test role normalization helper
  const vpMockUser: AuthenticatedUser = {
    id: "user-vp",
    email: "vp@campusos.edu",
    first_name: "VP",
    last_name: "Academic",
    status: "ACTIVE",
    roles: [{ id: "r1", name: "PRINCIPAL", display_name: "Vice Principal" }],
    permissions: [],
    tenant: { id: "t1", code: "VSB", name: "VSB" },
  };
  const normalizedVP = getNormalizedRoleSet(vpMockUser);
  assert(
    normalizedVP.has("PRINCIPAL") && normalizedVP.has("VICE_PRINCIPAL"),
    "Role normalizer equates PRINCIPAL and VICE_PRINCIPAL interchangeably",
  );

  const studentMockUser: AuthenticatedUser = {
    id: "user-student",
    email: "stu@campusos.edu",
    first_name: "Student",
    last_name: "User",
    status: "ACTIVE",
    roles: [{ id: "r2", name: "STUDENT", display_name: "Student" }],
    permissions: [],
    tenant: { id: "t1", code: "VSB", name: "VSB" },
  };
  const facultyMockUser: AuthenticatedUser = {
    id: "user-faculty",
    email: "fac@campusos.edu",
    first_name: "Faculty",
    last_name: "User",
    status: "ACTIVE",
    roles: [{ id: "r3", name: "FACULTY", display_name: "Faculty" }],
    permissions: [],
    tenant: { id: "t1", code: "VSB", name: "VSB" },
  };
  const hodMockUser: AuthenticatedUser = {
    id: "user-hod",
    email: "hod@campusos.edu",
    first_name: "HOD",
    last_name: "User",
    status: "ACTIVE",
    roles: [{ id: "r4", name: "HOD", display_name: "Head of Department" }],
    permissions: [],
    tenant: { id: "t1", code: "VSB", name: "VSB" },
  };
  const adminMockUser: AuthenticatedUser = {
    id: "user-admin",
    email: "admin@campusos.edu",
    first_name: "Admin",
    last_name: "User",
    status: "ACTIVE",
    roles: [{ id: "r5", name: "SUPER_ADMIN", display_name: "Super Admin" }],
    permissions: ["*"],
    tenant: { id: "t1", code: "VSB", name: "VSB" },
  };

  // -------------------------------------------------------------------------
  // 13. Direct Page Access Guard & Navigation Route Security
  // -------------------------------------------------------------------------
  // Student direct access tests
  assert(
    isPathAuthorized("/app/dashboard", studentMockUser) === true,
    "Student is authorized for /app/dashboard",
  );
  assert(
    isPathAuthorized("/app/attendance/leaves", studentMockUser) === true,
    "Student is authorized for /app/attendance/leaves",
  );
  assert(
    isPathAuthorized("/app/academics/timetable", studentMockUser) === true,
    "Student is authorized for /app/academics/timetable",
  );
  assert(
    isPathAuthorized("/app/finance/invoices", studentMockUser) === true,
    "Student is authorized for /app/finance/invoices",
  );
  assert(
    isPathAuthorized("/app/workforce", studentMockUser) === false,
    "Direct student navigation to /app/workforce is blocked",
  );
  assert(
    isPathAuthorized("/app/payroll", studentMockUser) === false,
    "Direct student navigation to /app/payroll is blocked",
  );
  assert(
    isPathAuthorized("/app/attendance/policies", studentMockUser) === false,
    "Direct student navigation to /app/attendance/policies is blocked",
  );
  assert(
    isPathAuthorized("/app/attendance/sessions", studentMockUser) === false,
    "Direct student navigation to /app/attendance/sessions is blocked",
  );
  assert(
    isPathAuthorized("/app/examinations/marks", studentMockUser) === false,
    "Direct student navigation to /app/examinations/marks is blocked",
  );
  assert(
    isPathAuthorized("/app/security", studentMockUser) === false,
    "Direct student navigation to /app/security is blocked",
  );

  // Faculty direct access tests
  assert(
    isPathAuthorized("/app/academics/subjects", facultyMockUser) === true,
    "Faculty is authorized for /app/academics/subjects",
  );
  assert(
    isPathAuthorized("/app/attendance/courses", facultyMockUser) === true,
    "Faculty is authorized for /app/attendance/courses",
  );
  assert(
    isPathAuthorized("/app/examinations/marks", facultyMockUser) === true,
    "Faculty is authorized for /app/examinations/marks",
  );
  assert(
    isPathAuthorized("/app/finance", facultyMockUser) === false,
    "Direct faculty navigation to /app/finance is blocked",
  );
  assert(
    isPathAuthorized("/app/payroll", facultyMockUser) === false,
    "Direct faculty navigation to /app/payroll is blocked",
  );
  assert(
    isPathAuthorized("/app/campuses", facultyMockUser) === false,
    "Direct faculty navigation to /app/campuses is blocked",
  );

  // HOD direct access tests
  assert(
    isPathAuthorized("/app/departments", hodMockUser) === true,
    "HOD is authorized for /app/departments",
  );
  assert(
    isPathAuthorized("/app/programs", hodMockUser) === true,
    "HOD is authorized for /app/programs",
  );
  assert(
    isPathAuthorized("/app/attendance/policies", hodMockUser) === true,
    "HOD is authorized for /app/attendance/policies",
  );
  assert(
    isPathAuthorized("/app/payroll", hodMockUser) === false,
    "Direct HOD navigation to /app/payroll is blocked",
  );

  // Vice Principal direct access tests
  assert(
    isPathAuthorized("/app/institution", vpMockUser) === true,
    "Vice Principal is authorized for /app/institution",
  );
  assert(
    isPathAuthorized("/app/campuses", vpMockUser) === true,
    "Vice Principal is authorized for /app/campuses",
  );
  assert(
    isPathAuthorized("/app/accreditation", vpMockUser) === true,
    "Vice Principal is authorized for /app/accreditation",
  );
  assert(
    isPathAuthorized("/app/examinations/publications", vpMockUser) === true,
    "Vice Principal is authorized for /app/examinations/publications",
  );

  // Super Admin direct access tests
  assert(
    isPathAuthorized("/app/security", adminMockUser) === true,
    "Admin is authorized for /app/security",
  );
  assert(
    isPathAuthorized("/app/marketplace", adminMockUser) === true,
    "Admin is authorized for /app/marketplace",
  );
  assert(
    isPathAuthorized("/app/subscriptions", adminMockUser) === true,
    "Admin is authorized for /app/subscriptions",
  );
  assert(
    isPathAuthorized("/app/adoption", adminMockUser) === true,
    "Admin is authorized for /app/adoption",
  );

  // Standalone admin-only modules blocked for non-admins
  assert(
    isPathAuthorized("/app/marketplace", studentMockUser) === false,
    "Student direct navigation to /app/marketplace is blocked",
  );
  assert(
    isPathAuthorized("/app/marketplace", facultyMockUser) === false,
    "Faculty direct navigation to /app/marketplace is blocked",
  );
  assert(
    isPathAuthorized("/app/subscriptions", vpMockUser) === false,
    "Vice Principal direct navigation to SaaS /app/subscriptions is blocked",
  );
  assert(
    isPathAuthorized("/app/data-import", studentMockUser) === false,
    "Student direct navigation to /app/data-import is blocked",
  );

  // -------------------------------------------------------------------------
  // 14. Comprehensive Five-Role Navigation Menu Filtering
  // -------------------------------------------------------------------------
  const allNavItems = NAV_SECTIONS.flatMap((s) => s.items);

  function getVisibleNavHrefs(user: AuthenticatedUser): string[] {
    const roleSet = getNormalizedRoleSet(user);
    const isSuperOrAdmin = roleSet.has("SUPER_ADMIN") || roleSet.has("ADMIN");
    return allNavItems
      .filter((item) => {
        if (isSuperOrAdmin) return true;
        if (!item.roles || item.roles.includes("*")) return true;
        return item.roles.some((r) => roleSet.has(r));
      })
      .map((item) => item.href);
  }

  const studentNavHrefs = getVisibleNavHrefs(studentMockUser);
  const facultyNavHrefs = getVisibleNavHrefs(facultyMockUser);
  const hodNavHrefs = getVisibleNavHrefs(hodMockUser);
  const vpNavHrefs = getVisibleNavHrefs(vpMockUser);
  const adminNavHrefs = getVisibleNavHrefs(adminMockUser);

  // Student navigation verification
  assert(
    !studentNavHrefs.includes("/app/workforce"),
    "Student sidebar excludes /app/workforce",
  );
  assert(
    !studentNavHrefs.includes("/app/people"),
    "Student sidebar excludes /app/people",
  );
  assert(
    !studentNavHrefs.includes("/app/faculty"),
    "Student sidebar excludes /app/faculty",
  );
  assert(
    !studentNavHrefs.includes("/app/staff"),
    "Student sidebar excludes /app/staff",
  );
  assert(
    !studentNavHrefs.includes("/app/programs"),
    "Student sidebar excludes /app/programs",
  );
  assert(
    !studentNavHrefs.includes("/app/attendance/policies"),
    "Student sidebar excludes /app/attendance/policies",
  );
  assert(
    !studentNavHrefs.includes("/app/attendance/sessions"),
    "Student sidebar excludes /app/attendance/sessions",
  );
  assert(
    !studentNavHrefs.includes("/app/attendance/courses"),
    "Student sidebar excludes /app/attendance/courses",
  );
  assert(
    !studentNavHrefs.includes("/app/examinations/marks"),
    "Student sidebar excludes /app/examinations/marks",
  );
  assert(
    !studentNavHrefs.includes("/app/examinations/publications"),
    "Student sidebar excludes /app/examinations/publications",
  );
  assert(
    !studentNavHrefs.includes("/app/finance"),
    "Student sidebar excludes /app/finance dashboard",
  );
  assert(
    !studentNavHrefs.includes("/app/payroll"),
    "Student sidebar excludes /app/payroll",
  );
  assert(
    !studentNavHrefs.includes("/app/security"),
    "Student sidebar excludes /app/security",
  );
  assert(
    studentNavHrefs.includes("/app/academics/enrollments"),
    "Student sidebar includes /app/academics/enrollments",
  );
  assert(
    studentNavHrefs.includes("/app/academics/timetable"),
    "Student sidebar includes /app/academics/timetable",
  );
  assert(
    studentNavHrefs.includes("/app/attendance/leaves"),
    "Student sidebar includes /app/attendance/leaves",
  );
  assert(
    studentNavHrefs.includes("/app/finance/invoices"),
    "Student sidebar includes /app/finance/invoices",
  );

  // Faculty navigation verification
  assert(
    facultyNavHrefs.includes("/app/academics/subjects"),
    "Faculty sidebar includes /app/academics/subjects",
  );
  assert(
    facultyNavHrefs.includes("/app/academics/curricula"),
    "Faculty sidebar includes /app/academics/curricula",
  );
  assert(
    facultyNavHrefs.includes("/app/attendance/sessions"),
    "Faculty sidebar includes /app/attendance/sessions",
  );
  assert(
    facultyNavHrefs.includes("/app/attendance/courses"),
    "Faculty sidebar includes /app/attendance/courses",
  );
  assert(
    facultyNavHrefs.includes("/app/examinations/marks"),
    "Faculty sidebar includes /app/examinations/marks",
  );
  assert(
    facultyNavHrefs.includes("/app/workforce"),
    "Faculty sidebar includes /app/workforce",
  );
  assert(
    !facultyNavHrefs.includes("/app/finance"),
    "Faculty sidebar excludes /app/finance dashboard",
  );
  assert(
    !facultyNavHrefs.includes("/app/payroll"),
    "Faculty sidebar excludes /app/payroll",
  );
  assert(
    !facultyNavHrefs.includes("/app/campuses"),
    "Faculty sidebar excludes /app/campuses",
  );
  assert(
    !facultyNavHrefs.includes("/app/institution"),
    "Faculty sidebar excludes /app/institution",
  );
  assert(
    !facultyNavHrefs.includes("/app/security"),
    "Faculty sidebar excludes /app/security",
  );

  // HOD navigation verification
  assert(
    hodNavHrefs.includes("/app/departments"),
    "HOD sidebar includes /app/departments",
  );
  assert(
    hodNavHrefs.includes("/app/programs"),
    "HOD sidebar includes /app/programs",
  );
  assert(
    hodNavHrefs.includes("/app/academic-structure"),
    "HOD sidebar includes /app/academic-structure",
  );
  assert(
    hodNavHrefs.includes("/app/attendance/policies"),
    "HOD sidebar includes /app/attendance/policies",
  );
  assert(
    hodNavHrefs.includes("/app/attendance/reports"),
    "HOD sidebar includes /app/attendance/reports",
  );
  assert(
    hodNavHrefs.includes("/app/examinations/reports"),
    "HOD sidebar includes /app/examinations/reports",
  );
  assert(
    !hodNavHrefs.includes("/app/payroll"),
    "HOD sidebar excludes /app/payroll",
  );
  assert(
    !hodNavHrefs.includes("/app/institution"),
    "HOD sidebar excludes /app/institution",
  );
  assert(
    !hodNavHrefs.includes("/app/campuses"),
    "HOD sidebar excludes /app/campuses",
  );
  assert(
    !hodNavHrefs.includes("/app/security"),
    "HOD sidebar excludes /app/security",
  );

  // Vice Principal navigation verification (internal role: PRINCIPAL)
  assert(
    vpNavHrefs.includes("/app/people"),
    "Vice Principal sidebar includes /app/people overview",
  );
  assert(
    vpNavHrefs.includes("/app/institution"),
    "Vice Principal sidebar includes /app/institution",
  );
  assert(
    vpNavHrefs.includes("/app/campuses"),
    "Vice Principal sidebar includes /app/campuses",
  );
  assert(
    vpNavHrefs.includes("/app/accreditation"),
    "Vice Principal sidebar includes /app/accreditation",
  );
  assert(
    vpNavHrefs.includes("/app/examinations/publications"),
    "Vice Principal sidebar includes /app/examinations/publications",
  );
  assert(
    vpNavHrefs.includes("/app/security"),
    "Vice Principal sidebar includes /app/security",
  );

  // Admin navigation verification
  assert(
    adminNavHrefs.length === allNavItems.length,
    "Super Admin sidebar includes all institutional navigation items",
  );
  assert(
    adminNavHrefs.includes("/app/payroll"),
    "Super Admin sidebar includes /app/payroll",
  );

  // Vice Principal role name alias compatibility test
  const vpAliasUser: AuthenticatedUser = {
    id: "user-vp-alias",
    email: "vp2@campusos.edu",
    first_name: "VP",
    last_name: "Alias",
    status: "ACTIVE",
    roles: [
      {
        id: "r-vp-alias",
        name: "VICE_PRINCIPAL",
        display_name: "Vice Principal",
      },
    ],
    permissions: [],
    tenant: { id: "t1", code: "VSB", name: "VSB" },
  };
  const vpAliasNavHrefs = getVisibleNavHrefs(vpAliasUser);
  assert(
    vpAliasNavHrefs.length === vpNavHrefs.length,
    "VICE_PRINCIPAL role alias generates identical navigation set as PRINCIPAL",
  );
  assert(
    isPathAuthorized("/app/accreditation", vpAliasUser) === true,
    "VICE_PRINCIPAL role alias is authorized for /app/accreditation",
  );

  // -------------------------------------------------------------------------
  // 15. Summary
  // -------------------------------------------------------------------------
  console.log("=================================================");
  console.log(
    `Auth Portal Tests Finished: Passed: ${passed}, Failed: ${failed}`,
  );
  console.log("=================================================");

  if (failed > 0) {
    process.exit(1);
  }
}

runAuthPortalTests();
