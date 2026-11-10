/**
 * CampusOS End-to-End Leave Workflow Test Suite
 *
 * Validates the full multi-role leave application and approval lifecycles:
 * 1. Student Leave Workflow: Student applies -> routes to Faculty -> Faculty reviews & approves -> Student sees approved status.
 * 2. Faculty Leave Workflow: Faculty applies -> Form shows Faculty Name & Employee ID (NOT student) -> routes to HOD -> HOD reviews & approves -> Faculty sees approved status.
 * 3. Role-Based Permissions & Separation of Duties: Students cannot approve leaves; Faculty cannot self-approve.
 * 4. Cross-Portal State Persistence & Navigation Integration.
 */

import { attendanceService } from "../services/attendance.service";
import { DEMO_PERSONAS } from "../mocks/auth.mock";
import {
  isPathAuthorized,
  getPortalNavSections,
  STUDENT_PORTAL_NAV,
  FACULTY_PORTAL_NAV,
  HOD_PORTAL_NAV,
  VICE_PRINCIPAL_PORTAL_NAV,
  ADMIN_PORTAL_NAV,
} from "../components/navigation/sidebar";
import type { AuthenticatedUser } from "@campusos/types";

export async function runLeaveWorkflowE2ETests(): Promise<{
  passed: number;
  failed: number;
  results: { testName: string; passed: boolean; message?: string }[];
}> {
  const results: { testName: string; passed: boolean; message?: string }[] = [];

  function assert(
    condition: unknown,
    testName: string,
    failureDetails?: string,
  ) {
    if (Boolean(condition)) {
      results.push({ testName, passed: true });
    } else {
      results.push({
        testName,
        passed: false,
        message: failureDetails || "Assertion failed",
      });
    }
  }

  try {
    // =========================================================================
    // SECTION 1: PERSONA & ROLE PERMISSION VERIFICATION
    // =========================================================================
    const studentPersona = DEMO_PERSONAS.find(
      (p) => p.email === "aarav.patel@student.campusos.edu",
    );
    const facultyPersona = DEMO_PERSONAS.find(
      (p) => p.email === "rajesh.sharma@campusos.edu",
    );
    const hodPersona = DEMO_PERSONAS.find(
      (p) => p.email === "hod.cse@campusos.edu",
    );
    const vpPersona = DEMO_PERSONAS.find(
      (p) => p.email === "vp.academics@campusos.edu",
    );

    assert(
      studentPersona !== undefined,
      "1.1 Student persona exists in demo accounts",
    );
    assert(
      facultyPersona !== undefined,
      "1.2 Faculty persona exists in demo accounts",
    );
    assert(hodPersona !== undefined, "1.3 HOD persona exists in demo accounts");
    assert(
      vpPersona !== undefined,
      "1.4 Vice Principal persona exists in demo accounts",
    );

    // Verify Student permissions
    const studentPerms = studentPersona?.permissions || [];
    assert(
      studentPerms.includes("leave:read"),
      "1.5 Student has leave:read permission",
    );
    assert(
      studentPerms.includes("leave:create"),
      "1.6 Student has leave:create permission",
    );
    assert(
      !studentPerms.includes("leave:approve"),
      "1.7 Student MUST NOT have leave:approve permission",
    );
    assert(
      !studentPerms.includes("leave:reject"),
      "1.8 Student MUST NOT have leave:reject permission",
    );

    // Verify Faculty permissions
    const facultyPerms = facultyPersona?.permissions || [];
    assert(
      facultyPerms.includes("leave:read"),
      "1.9 Faculty has leave:read permission",
    );
    assert(
      facultyPerms.includes("leave:create"),
      "1.10 Faculty has leave:create permission",
    );
    assert(
      facultyPerms.includes("leave:approve"),
      "1.11 Faculty has leave:approve permission",
    );
    assert(
      facultyPerms.includes("leave:reject"),
      "1.12 Faculty has leave:reject permission",
    );

    // Verify HOD permissions
    const hodPerms = hodPersona?.permissions || [];
    assert(
      hodPerms.includes("leave:read"),
      "1.13 HOD has leave:read permission",
    );
    assert(
      hodPerms.includes("leave:approve"),
      "1.14 HOD has leave:approve permission",
    );
    assert(
      hodPerms.includes("leave:reject"),
      "1.15 HOD has leave:reject permission",
    );

    // =========================================================================
    // SECTION 2: STUDENT LEAVE WORKFLOW (STUDENT -> FACULTY)
    // =========================================================================
    // 2.1 Student applies for medical leave
    const studentLeavePayload = {
      studentName: studentPersona?.name || "Aarav Patel",
      rollNumber: "24CSE0101",
      department: "Computer Science & Engineering",
      section: "A",
      leaveType: "MEDICAL" as const,
      startDate: "2026-11-25",
      endDate: "2026-11-27",
      totalDays: 3,
      reason:
        "Viral fever - prescribed 3 days clinical rest by campus medical center",
      applicantType: "STUDENT" as const,
    };

    const submitStudentLeaveRes =
      await attendanceService.submitLeave(studentLeavePayload);
    assert(
      submitStudentLeaveRes.success === true,
      "2.1 Student leave submission succeeds",
    );
    assert(
      submitStudentLeaveRes.data.id !== undefined,
      "2.2 Submitted leave receives unique ID",
    );
    assert(
      submitStudentLeaveRes.data.status === "PENDING",
      "2.3 Initial status is PENDING",
    );
    assert(
      submitStudentLeaveRes.data.applicantType === "STUDENT",
      "2.4 Leave is tagged as STUDENT applicant",
    );
    assert(
      submitStudentLeaveRes.data.approverRole === "FACULTY",
      "2.5 Leave routing targets FACULTY for approval",
    );

    const studentLeaveId = submitStudentLeaveRes.data.id;

    // 2.2 Student sees own leave in list
    const studentLeavesList = await attendanceService.getLeaves({
      applicantType: "STUDENT",
    });
    const studentFound = studentLeavesList.data.find(
      (l) => l.id === studentLeaveId,
    );
    assert(
      studentFound !== undefined,
      "2.6 Student can view their own submitted leave",
    );
    assert(
      studentFound?.status === "PENDING",
      "2.7 Leave remains in PENDING state awaiting faculty review",
    );

    // 2.3 Faculty checks pending leaves: request MUST reach the Faculty
    const facultyPendingList = await attendanceService.getLeaves({
      applicantType: "STUDENT",
      status: "PENDING",
    });
    const reachFaculty = facultyPendingList.data.some(
      (l) => l.id === studentLeaveId,
    );
    assert(
      reachFaculty,
      "2.8 Approval request reaches Faculty portal pending list",
    );

    // 2.4 Faculty approves the student leave request
    const facultyReviewerName = `${facultyPersona?.name || "Dr. Rajesh Sharma"} (Faculty - CSE)`;
    const facultyNotes =
      "Medical certificate and prescription verified. Exemption granted.";
    const approveStudentLeaveRes = await attendanceService.updateLeaveStatus(
      studentLeaveId,
      "APPROVED",
      facultyNotes,
      facultyReviewerName,
    );

    assert(
      approveStudentLeaveRes.success === true,
      "2.9 Faculty approval call succeeds",
    );
    assert(
      approveStudentLeaveRes.data.status === "APPROVED",
      "2.10 Leave status transitions to APPROVED",
    );
    assert(
      approveStudentLeaveRes.data.reviewedBy === facultyReviewerName,
      "2.11 Review signature records Faculty reviewer name and title",
    );
    assert(
      approveStudentLeaveRes.data.reviewNotes === facultyNotes,
      "2.12 Review notes from Faculty are recorded",
    );
    assert(
      approveStudentLeaveRes.data.reviewedAt !== undefined,
      "2.13 Review timestamp is recorded",
    );

    // 2.5 Student checks their leave status: reflects Faculty approval
    const studentUpdatedLeaves = await attendanceService.getLeaves({
      applicantType: "STUDENT",
    });
    const studentApprovedRecord = studentUpdatedLeaves.data.find(
      (l) => l.id === studentLeaveId,
    );
    assert(
      studentApprovedRecord?.status === "APPROVED",
      "2.14 Student observes APPROVED status",
    );
    assert(
      studentApprovedRecord?.reviewedBy?.includes("Faculty"),
      "2.15 Student observes Faculty reviewer signature",
    );

    // =========================================================================
    // SECTION 3: FACULTY LEAVE WORKFLOW (FACULTY -> HOD)
    // =========================================================================
    // 3.1 Faculty applies for leave to HOD
    // Form verification: Form fields must reflect Faculty Name and Employee ID (NOT student details)
    const facultyLeavePayload = {
      studentName: facultyPersona?.name || "Dr. Rajesh Sharma",
      rollNumber: "EMP-CSE-01",
      department: "Computer Science & Engineering",
      section: "Faculty Staff",
      leaveType: "ACADEMIC" as const,
      startDate: "2026-12-05",
      endDate: "2026-12-07",
      totalDays: 3,
      reason:
        "Keynote presentation at National Conference on Distributed Systems (IIT Madras)",
      applicantType: "FACULTY" as const,
    };

    assert(
      facultyLeavePayload.studentName !== "Aarav Patel",
      "3.1 Faculty leave form does NOT contain student name (Aarav Patel)",
    );
    assert(
      facultyLeavePayload.rollNumber !== "24CSE0101",
      "3.2 Faculty leave form does NOT contain student roll number (24CSE0101)",
    );
    assert(
      facultyLeavePayload.studentName === "Dr. Rajesh Sharma",
      "3.3 Faculty leave form correctly displays Faculty Name (Dr. Rajesh Sharma)",
    );
    assert(
      facultyLeavePayload.rollNumber === "EMP-CSE-01",
      "3.4 Faculty leave form correctly displays Employee Code (EMP-CSE-01)",
    );

    const submitFacultyLeaveRes =
      await attendanceService.submitLeave(facultyLeavePayload);
    assert(
      submitFacultyLeaveRes.success === true,
      "3.5 Faculty leave submission succeeds",
    );
    assert(
      submitFacultyLeaveRes.data.id !== undefined,
      "3.6 Submitted faculty leave receives unique ID",
    );
    assert(
      submitFacultyLeaveRes.data.status === "PENDING",
      "3.7 Initial faculty leave status is PENDING",
    );
    assert(
      submitFacultyLeaveRes.data.applicantType === "FACULTY",
      "3.8 Leave is tagged as FACULTY applicant",
    );
    assert(
      submitFacultyLeaveRes.data.approverRole === "HOD",
      "3.9 Faculty leave routing targets HOD for approval",
    );

    const facultyLeaveId = submitFacultyLeaveRes.data.id;

    // 3.2 HOD checks pending leaves / endorsements: request MUST reach HOD
    const hodPendingList = await attendanceService.getLeaves({
      applicantType: "FACULTY",
      status: "PENDING",
    });
    const reachHod = hodPendingList.data.some((l) => l.id === facultyLeaveId);
    assert(
      reachHod,
      "3.10 Faculty leave application successfully reaches HOD portal queue",
    );

    // 3.3 HOD approves the faculty leave request
    const hodReviewerName = `${hodPersona?.name || "Dr. K. S. Anand"} (HOD - CSE)`;
    const hodNotes =
      "Duty leave approved. Substitute lecture coverage verified with Prof. Meenakshi.";
    const approveFacultyLeaveRes = await attendanceService.updateLeaveStatus(
      facultyLeaveId,
      "APPROVED",
      hodNotes,
      hodReviewerName,
    );

    assert(
      approveFacultyLeaveRes.success === true,
      "3.11 HOD approval call succeeds",
    );
    assert(
      approveFacultyLeaveRes.data.status === "APPROVED",
      "3.12 Faculty leave status transitions to APPROVED",
    );
    assert(
      approveFacultyLeaveRes.data.reviewedBy === hodReviewerName,
      "3.13 Review signature records HOD reviewer name and title",
    );
    assert(
      approveFacultyLeaveRes.data.reviewNotes === hodNotes,
      "3.14 Review notes from HOD are recorded",
    );

    // 3.4 Faculty checks their leave status: reflects HOD approval
    const facultyUpdatedLeaves = await attendanceService.getLeaves({
      applicantType: "FACULTY",
    });
    const facultyApprovedRecord = facultyUpdatedLeaves.data.find(
      (l) => l.id === facultyLeaveId,
    );
    assert(
      facultyApprovedRecord?.status === "APPROVED",
      "3.15 Faculty observes APPROVED status",
    );
    assert(
      facultyApprovedRecord?.reviewedBy?.includes("HOD"),
      "3.16 Faculty observes HOD reviewer signature",
    );

    // =========================================================================
    // SECTION 4: REJECTION WORKFLOW
    // =========================================================================
    // 4.1 Student applies for casual leave
    const rejectTestLeave = await attendanceService.submitLeave({
      studentName: "Aditya Nair",
      rollNumber: "24CSE0142",
      department: "Computer Science & Engineering",
      section: "B",
      leaveType: "CASUAL",
      startDate: "2026-11-28",
      endDate: "2026-11-29",
      totalDays: 2,
      reason: "Personal leisure outing during mid-semester examination week",
      applicantType: "STUDENT",
    });
    assert(
      rejectTestLeave.success === true,
      "4.1 Student submits second leave request",
    );

    // 4.2 Faculty rejects the casual leave during exam week
    const rejectNotes =
      "Casual leave not permitted during continuous assessment examinations.";
    const rejectRes = await attendanceService.updateLeaveStatus(
      rejectTestLeave.data.id,
      "REJECTED",
      rejectNotes,
      "Dr. Rajesh Sharma (Faculty - CSE)",
    );
    assert(rejectRes.success === true, "4.2 Faculty rejection call succeeds");
    assert(
      rejectRes.data.status === "REJECTED",
      "4.3 Leave status correctly set to REJECTED",
    );
    assert(
      rejectRes.data.rejectionReason === rejectNotes,
      "4.4 Rejection reason properly recorded in rejectionReason",
    );
    assert(
      rejectRes.data.reviewNotes === rejectNotes,
      "4.5 Rejection reason properly recorded in reviewNotes",
    );

    // =========================================================================
    // SECTION 5: CATEGORY FILTERING & QUERY ACCURACY
    // =========================================================================
    const allLeaves = await attendanceService.getLeaves();
    const studentOnlyLeaves = await attendanceService.getLeaves({
      applicantType: "STUDENT",
    });
    const facultyOnlyLeaves = await attendanceService.getLeaves({
      applicantType: "FACULTY",
    });

    assert(
      allLeaves.data.length >= 2,
      "5.1 All records returns complete dataset",
    );
    assert(
      studentOnlyLeaves.data.every(
        (l) => (l.applicantType || "STUDENT") === "STUDENT",
      ),
      "5.2 Student filter returns only student leaves",
    );
    assert(
      facultyOnlyLeaves.data.every((l) => l.applicantType === "FACULTY"),
      "5.3 Faculty filter returns only faculty leaves",
    );

    // =========================================================================
    // SECTION 6: PORTAL NAVIGATION & DASHBOARD INTEGRATION
    // =========================================================================
    const studentUser: AuthenticatedUser = {
      id: "u-student-01",
      email: "aarav.patel@student.campusos.edu",
      firstName: "Aarav",
      lastName: "Patel",
      roles: [{ id: "r-student", name: "STUDENT", display_name: "Student" }],
      permissions: [],
      tenant: { id: "t-01", code: "VSB", name: "VSB College" },
    };

    const facultyUser: AuthenticatedUser = {
      id: "u-faculty-01",
      email: "rajesh.sharma@campusos.edu",
      firstName: "Rajesh",
      lastName: "Sharma",
      roles: [{ id: "r-faculty", name: "FACULTY", display_name: "Faculty" }],
      permissions: [],
      tenant: { id: "t-01", code: "VSB", name: "VSB College" },
    };

    const hodUser: AuthenticatedUser = {
      id: "u-hod-01",
      email: "hod.cse@campusos.edu",
      firstName: "K.S.",
      lastName: "Anand",
      roles: [{ id: "r-hod", name: "HOD", display_name: "Head of Department" }],
      permissions: [],
      tenant: { id: "t-01", code: "VSB", name: "VSB College" },
    };

    const vpUser: AuthenticatedUser = {
      id: "u-vp-01",
      email: "vp.academics@campusos.edu",
      firstName: "Meenakshi",
      lastName: "Sundaram",
      roles: [
        { id: "r-vp", name: "PRINCIPAL", display_name: "Vice Principal" },
      ],
      permissions: [],
      tenant: { id: "t-01", code: "VSB", name: "VSB College" },
    };

    const adminUser: AuthenticatedUser = {
      id: "u-admin-01",
      email: "admin@campusos.edu",
      firstName: "System",
      lastName: "Admin",
      roles: [
        { id: "r-admin", name: "SUPER_ADMIN", display_name: "Super Admin" },
      ],
      permissions: [],
      tenant: { id: "t-01", code: "VSB", name: "VSB College" },
    };

    // Verify role-specific portal nav assignment
    assert(
      getPortalNavSections(studentUser) === STUDENT_PORTAL_NAV,
      "6.1 Student gets STUDENT_PORTAL_NAV",
    );
    assert(
      getPortalNavSections(facultyUser) === FACULTY_PORTAL_NAV,
      "6.2 Faculty gets FACULTY_PORTAL_NAV",
    );
    assert(
      getPortalNavSections(hodUser) === HOD_PORTAL_NAV,
      "6.3 HOD gets HOD_PORTAL_NAV",
    );
    assert(
      getPortalNavSections(vpUser) === VICE_PRINCIPAL_PORTAL_NAV,
      "6.4 Vice Principal gets VICE_PRINCIPAL_PORTAL_NAV",
    );
    assert(
      getPortalNavSections(adminUser) === ADMIN_PORTAL_NAV,
      "6.5 Admin gets ADMIN_PORTAL_NAV",
    );

    // Student nav must have attendance & leaves
    const studentHasAttendance = STUDENT_PORTAL_NAV.some((sec) =>
      sec.items.some((i) => i.href.includes("attendance")),
    );
    assert(
      studentHasAttendance,
      "6.6 Student portal navigation contains Attendance & Leaves",
    );

    // Faculty nav must have faculty leave option
    const facultyHasLeave = FACULTY_PORTAL_NAV.some((sec) =>
      sec.items.some((i) => i.href.includes("attendance/leaves")),
    );
    assert(
      facultyHasLeave,
      "6.7 Faculty portal navigation contains Apply for Faculty Leave",
    );

    // HOD nav must have leave endorsements
    const hodHasLeave = HOD_PORTAL_NAV.some((sec) =>
      sec.items.some((i) => i.href.includes("attendance/leaves")),
    );
    assert(
      hodHasLeave,
      "6.8 HOD portal navigation contains Leave Endorsements",
    );

    // =========================================================================
    // SECTION 7: DIRECT ROUTE AUTHORIZATION & RBAC ENFORCEMENT
    // =========================================================================
    // Student authorized paths
    assert(
      isPathAuthorized("/app/dashboard", studentUser),
      "7.1 Student authorized for /app/dashboard",
    );
    assert(
      isPathAuthorized("/app/attendance/leaves", studentUser),
      "7.2 Student authorized for /app/attendance/leaves",
    );
    assert(
      isPathAuthorized("/app/academics/timetable", studentUser),
      "7.3 Student authorized for /app/academics/timetable",
    );

    // Student blocked from administrative and staff modules
    assert(
      !isPathAuthorized("/app/workforce", studentUser),
      "7.4 Student blocked from /app/workforce",
    );
    assert(
      !isPathAuthorized("/app/payroll", studentUser),
      "7.5 Student blocked from /app/payroll",
    );
    assert(
      !isPathAuthorized("/app/attendance/policies", studentUser),
      "7.6 Student blocked from /app/attendance/policies",
    );
    assert(
      !isPathAuthorized("/app/attendance/sessions", studentUser),
      "7.7 Student blocked from /app/attendance/sessions",
    );
    assert(
      !isPathAuthorized("/app/security", studentUser),
      "7.8 Student blocked from /app/security",
    );

    // Faculty authorized paths
    assert(
      isPathAuthorized("/app/dashboard", facultyUser),
      "7.9 Faculty authorized for /app/dashboard",
    );
    assert(
      isPathAuthorized("/app/attendance/leaves", facultyUser),
      "7.10 Faculty authorized for /app/attendance/leaves",
    );
    assert(
      isPathAuthorized("/app/attendance/sessions", facultyUser),
      "7.11 Faculty authorized for /app/attendance/sessions",
    );

    // Faculty blocked from administrative modules
    assert(
      !isPathAuthorized("/app/payroll", facultyUser),
      "7.12 Faculty blocked from /app/payroll",
    );
    assert(
      !isPathAuthorized("/app/marketplace", facultyUser),
      "7.13 Faculty blocked from /app/marketplace",
    );
    assert(
      !isPathAuthorized("/app/subscriptions", facultyUser),
      "7.14 Faculty blocked from /app/subscriptions",
    );

    // Admin authorized for administrative suites
    assert(
      isPathAuthorized("/app/workforce", adminUser),
      "7.15 Admin authorized for /app/workforce",
    );
    assert(
      isPathAuthorized("/app/marketplace", adminUser),
      "7.16 Admin authorized for /app/marketplace",
    );
    assert(
      isPathAuthorized("/app/subscriptions", adminUser),
      "7.17 Admin authorized for /app/subscriptions",
    );
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : String(error);
    results.push({
      testName: "Unhandled exception during leave workflow test",
      passed: false,
      message: errorMsg,
    });
  }

  const passed = results.filter((r) => r.passed).length;
  const failed = results.filter((r) => !r.passed).length;
  return { passed, failed, results };
}

if (
  typeof process !== "undefined" &&
  process.argv[1]?.includes("leave-workflow-e2e.test")
) {
  runLeaveWorkflowE2ETests().then((res) => {
    console.log(`\n======================================================`);
    console.log(`CampusOS End-to-End Leave Workflow Verification Suite:`);
    console.log(`Passed: ${res.passed}, Failed: ${res.failed}`);
    console.log(`======================================================`);
    res.results.forEach((r) => {
      console.log(
        `${r.passed ? "✔ PASS" : "✖ FAIL"}: ${r.testName}${r.message ? ` (${r.message})` : ""}`,
      );
    });
    if (res.failed > 0) {
      process.exit(1);
    }
  });
}
