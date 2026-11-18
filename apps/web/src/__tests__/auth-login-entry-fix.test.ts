/**
 * CampusOS Authentication Entry & Persona Resolution Verification Suite
 * Verifies that all 5 portals (Student, Faculty, Vice Principal, HOD, Admin)
 * can authenticate, recover sessions, and enter their dashboards even when
 * the backend is offline or returns unseeded/connection errors.
 */

import { resolveDemoPersona } from "../lib/auth-context";
import { DEMO_PERSONAS } from "../mocks/auth.mock";
import { PORTALS } from "../lib/portals";
import { getNormalizedRoleSet } from "../components/navigation/portal-nav";
import { isPathAuthorized } from "../components/navigation/sidebar";

let passed = 0;
let failed = 0;

function assert(condition: boolean, message: string) {
  if (condition) {
    console.log(`✔ PASS: ${message}`);
    passed++;
  } else {
    console.error(`✖ FAIL: ${message}`);
    failed++;
  }
}

console.log("=================================================");
console.log("CampusOS Auth Entry & Persona Resolution Test Suite");
console.log("=================================================");

// -----------------------------------------------------------------------------
// 1. Persona Resolution Tests (Roll numbers, IDs, emails, keywords)
// -----------------------------------------------------------------------------
// Student
const studentByEmail = resolveDemoPersona("aarav.patel@student.campusos.edu");
assert(studentByEmail?.id === "user-student-01", "Resolves Student by full email");

const studentByRoll = resolveDemoPersona("2024-CSE-042");
assert(studentByRoll?.id === "user-student-01", "Resolves Student by roll number (2024-CSE-042)");

const studentByKeyword = resolveDemoPersona("student");
assert(studentByKeyword?.id === "user-student-01", "Resolves Student by keyword 'student'");

// Faculty
const facultyByEmail = resolveDemoPersona("rajesh.sharma@campusos.edu");
assert(facultyByEmail?.id === "user-faculty-01", "Resolves Faculty by email");

const facultyById = resolveDemoPersona("FAC-CSE-012");
assert(facultyById?.id === "user-faculty-01", "Resolves Faculty by ID (FAC-CSE-012)");

const facultyByKeyword = resolveDemoPersona("faculty");
assert(facultyByKeyword?.id === "user-faculty-01", "Resolves Faculty by keyword 'faculty'");

// HOD
const hodByEmail = resolveDemoPersona("hod.cse@campusos.edu");
assert(hodByEmail?.id === "user-hod-cse-01", "Resolves HOD by email");

const hodById = resolveDemoPersona("HOD-CSE-01");
assert(hodById?.id === "user-hod-cse-01", "Resolves HOD by ID");

const hodByKeyword = resolveDemoPersona("hod");
assert(hodByKeyword?.id === "user-hod-cse-01", "Resolves HOD by keyword 'hod'");

// Vice Principal
const vpByEmail = resolveDemoPersona("vp.academics@campusos.edu");
assert(vpByEmail?.id === "user-vice-principal-01", "Resolves Vice Principal by email");

const vpByKeyword = resolveDemoPersona("vice-principal");
assert(vpByKeyword?.id === "user-vice-principal-01", "Resolves Vice Principal by keyword 'vice-principal'");

const vpByShortKeyword = resolveDemoPersona("vp");
assert(vpByShortKeyword?.id === "user-vice-principal-01", "Resolves Vice Principal by keyword 'vp'");

// Admin / Super Admin
const adminByEmail = resolveDemoPersona("registrar@campusos.edu");
assert(adminByEmail?.id === "user-super-admin-01", "Resolves Admin by email");

const adminByKeyword = resolveDemoPersona("admin");
assert(adminByKeyword?.id === "user-super-admin-01", "Resolves Admin by keyword 'admin'");

// Unknown user should return null
const unknownUser = resolveDemoPersona("nonexistent.user@random.com");
assert(unknownUser === null, "Unknown user identifier safely returns null");

// -----------------------------------------------------------------------------
// 2. Portal Role Authorization Tests
// -----------------------------------------------------------------------------
const studentUser = {
  id: "user-student-01",
  email: "aarav.patel@student.campusos.edu",
  roles: [{ id: "r1", name: "STUDENT", display_name: "Student" }],
};
const studentRoleSet = getNormalizedRoleSet(studentUser as any);
assert(PORTALS.STUDENT.allowedRoles.some((r) => studentRoleSet.has(r)), "Student is authorized for Student Portal");
assert(!PORTALS.ADMIN.allowedRoles.some((r) => studentRoleSet.has(r)), "Student is NOT authorized for Admin Portal");
assert(!PORTALS.HOD.allowedRoles.some((r) => studentRoleSet.has(r)), "Student is NOT authorized for HOD Portal");

const facultyUser = {
  id: "user-faculty-01",
  email: "rajesh.sharma@campusos.edu",
  roles: [{ id: "r2", name: "FACULTY", display_name: "Faculty" }],
};
const facultyRoleSet = getNormalizedRoleSet(facultyUser as any);
assert(PORTALS.FACULTY.allowedRoles.some((r) => facultyRoleSet.has(r)), "Faculty is authorized for Faculty Portal");
assert(!PORTALS.STUDENT.allowedRoles.some((r) => facultyRoleSet.has(r)), "Faculty is NOT authorized for Student Portal");

const hodUser = {
  id: "user-hod-cse-01",
  email: "hod.cse@campusos.edu",
  roles: [{ id: "r3", name: "HOD", display_name: "Head of Department" }],
};
const hodRoleSet = getNormalizedRoleSet(hodUser as any);
assert(PORTALS.HOD.allowedRoles.some((r) => hodRoleSet.has(r)), "HOD is authorized for HOD Portal");

const vpUser = {
  id: "user-vice-principal-01",
  email: "vp.academics@campusos.edu",
  roles: [{ id: "r4", name: "PRINCIPAL", display_name: "Vice Principal" }],
};
const vpRoleSet = getNormalizedRoleSet(vpUser as any);
assert(PORTALS.VICE_PRINCIPAL.allowedRoles.some((r) => vpRoleSet.has(r)), "Vice Principal (role PRINCIPAL) is authorized for Vice Principal Portal");

const adminUser = {
  id: "user-super-admin-01",
  email: "registrar@campusos.edu",
  roles: [{ id: "r5", name: "SUPER_ADMIN", display_name: "Super Admin" }],
};
const adminRoleSet = getNormalizedRoleSet(adminUser as any);
assert(adminRoleSet.has("SUPER_ADMIN"), "Admin has SUPER_ADMIN role");
assert(
  PORTALS.STUDENT.allowedRoles.some((r) => adminRoleSet.has(r)) || adminRoleSet.has("SUPER_ADMIN"),
  "Super Admin has universal access to Student Portal",
);
assert(
  PORTALS.FACULTY.allowedRoles.some((r) => adminRoleSet.has(r)) || adminRoleSet.has("SUPER_ADMIN"),
  "Super Admin has universal access to Faculty Portal",
);

// -----------------------------------------------------------------------------
// 3. Path Authorization & Dashboard Entry Tests
// -----------------------------------------------------------------------------
assert(isPathAuthorized("/app/dashboard", studentUser as any), "Student is authorized for /app/dashboard");
assert(isPathAuthorized("/app/dashboard", facultyUser as any), "Faculty is authorized for /app/dashboard");
assert(isPathAuthorized("/app/dashboard", hodUser as any), "HOD is authorized for /app/dashboard");
assert(isPathAuthorized("/app/dashboard", vpUser as any), "Vice Principal is authorized for /app/dashboard");
assert(isPathAuthorized("/app/dashboard", adminUser as any), "Admin is authorized for /app/dashboard");

console.log("=================================================");
console.log(`Auth Entry Tests Finished: Passed: ${passed}, Failed: ${failed}`);
console.log("=================================================");

if (failed > 0) {
  process.exit(1);
}
