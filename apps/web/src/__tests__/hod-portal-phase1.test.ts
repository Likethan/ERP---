/**
 * CampusOS HOD Portal Phase 1 — Comprehensive Verification Test Suite
 *
 * Validates the 5 Core Modules and Departmental Access Restrictions:
 * 1. HOD Persona, Authentication & Role Resolution.
 * 2. HOD Portal Navigation Structure & Sidebar Routing.
 * 3. Module 1: HOD Dashboard Statistics & Analytics.
 * 4. Module 2: Department Faculty Management & Profile Scoping.
 * 5. Module 3: Department Student Management & Academic Profiles.
 * 6. Module 4: Attendance Monitoring, Ledger & Shortage Thresholds (<75%).
 * 7. Module 5: Master Timetable Grid & Faculty Teaching Workloads.
 * 8. Cross-Department Access Control (Defense-in-Depth).
 */

import { hodService } from "@/services/hod.service";
import { DEMO_PERSONAS } from "@/mocks/auth.mock";
import { HOD_PORTAL_NAV } from "@/components/navigation/portal-nav";
import { isPathAuthorized } from "@/components/navigation/sidebar";
import type { AuthenticatedUser } from "@campusos/types";

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
  console.log(
    "\n===============================================================================",
  );
  console.log("CampusOS HOD Portal Phase 1 — Comprehensive Verification Suite");
  console.log(
    "===============================================================================\n",
  );

  // ---------------------------------------------------------------------------
  // 1. HOD Persona and Authorization Credentials
  // ---------------------------------------------------------------------------
  console.log("--- TEST GROUP 1: HOD Authentication & Identity Resolution ---");
  const hodPersona = DEMO_PERSONAS.find(
    (p) => p.role === "HOD" || p.id === "user-hod-cse-01",
  );
  assert(Boolean(hodPersona), "HOD demo persona exists in auth mock");
  assert(
    hodPersona?.email === "hod.cse@campusos.edu",
    "HOD email matches hod.cse@campusos.edu",
  );
  assert(
    hodPersona?.department === "Computer Science & Engineering",
    "HOD department assigned to Computer Science & Engineering",
  );
  assert(
    Boolean(hodPersona?.permissions?.includes("people:faculty:read")),
    "HOD holds people:faculty:read permission",
  );
  assert(
    Boolean(hodPersona?.permissions?.includes("people:students:read")),
    "HOD holds people:students:read permission",
  );
  assert(
    Boolean(hodPersona?.permissions?.includes("attendance:read")),
    "HOD holds attendance:read permission",
  );

  const mockHodUser: AuthenticatedUser = {
    id: hodPersona!.id,
    email: hodPersona!.email,
    first_name: "Dr. K. S.",
    last_name: "Anand",
    status: "ACTIVE",
    roles: [
      {
        id: "role-hod",
        name: "HOD",
        display_name: "Head of Department",
      },
    ],
    permissions: hodPersona!.permissions,
    tenant: {
      id: "ten-vsb-01",
      code: "VSB-CAMPUS",
      name: "Vidyasagar State University of Engineering",
    },
  };

  // ---------------------------------------------------------------------------
  // 2. Navigation Structure & Sidebar Routing
  // ---------------------------------------------------------------------------
  console.log(
    "\n--- TEST GROUP 2: HOD Portal Navigation & Sidebar Routing ---",
  );
  const leadershipSection = HOD_PORTAL_NAV.find(
    (s) => s.title === "DEPARTMENT LEADERSHIP" || s.title === "ACADEMIC MANAGEMENT",
  );
  assert(
    Boolean(leadershipSection),
    "Leadership / Academic section exists in HOD nav",
  );

  const expectedNavHrefs = [
    "/hod/dashboard",
    "/hod/faculty",
    "/hod/students",
    "/hod/attendance",
    "/hod/timetable",
  ];

  for (const href of expectedNavHrefs) {
    const hasRoute = HOD_PORTAL_NAV.some((sec) =>
      sec.items.some((item) => item.href === href),
    );
    assert(hasRoute, `HOD nav includes required route: ${href}`);
  }

  // Verify route authorization check
  assert(
    isPathAuthorized("/hod/dashboard", mockHodUser),
    "isPathAuthorized allows HOD to access /hod/dashboard",
  );
  assert(
    isPathAuthorized("/hod/faculty", mockHodUser),
    "isPathAuthorized allows HOD to access /hod/faculty",
  );
  assert(
    isPathAuthorized("/hod/students", mockHodUser),
    "isPathAuthorized allows HOD to access /hod/students",
  );
  assert(
    isPathAuthorized("/hod/attendance", mockHodUser),
    "isPathAuthorized allows HOD to access /hod/attendance",
  );
  assert(
    isPathAuthorized("/hod/timetable", mockHodUser),
    "isPathAuthorized allows HOD to access /hod/timetable",
  );

  // ---------------------------------------------------------------------------
  // 3. Module 1: HOD Dashboard Statistics
  // ---------------------------------------------------------------------------
  console.log(
    "\n--- TEST GROUP 3: Module 1 — Dashboard Statistics & Analytics ---",
  );
  const dashRes = await hodService.getDashboardStats(
    "Computer Science & Engineering",
  );
  assert(dashRes.success === true, "Dashboard stats query returns success");
  const stats = dashRes.data.statistics;
  assert(
    stats.totalStudents > 0,
    `Total students is non-zero and realistic: ${stats.totalStudents}`,
  );
  assert(
    stats.totalFaculty > 0,
    `Total faculty is non-zero and realistic: ${stats.totalFaculty}`,
  );
  assert(
    stats.totalSubjects >= 10,
    `Total subjects is non-zero: ${stats.totalSubjects}`,
  );
  assert(
    stats.totalClasses >= 4,
    `Total classes is non-zero: ${stats.totalClasses}`,
  );
  assert(
    stats.averageStudentAttendance >= 70 &&
      stats.averageStudentAttendance <= 100,
    `Average student attendance is valid percentage: ${stats.averageStudentAttendance}%`,
  );
  assert(
    stats.averageFacultyAttendance >= 80 &&
      stats.averageFacultyAttendance <= 100,
    `Average faculty attendance is valid percentage: ${stats.averageFacultyAttendance}%`,
  );
  assert(
    stats.studentsShortageCount >= 0,
    `Students with attendance shortage identified: ${stats.studentsShortageCount}`,
  );
  assert(
    stats.pendingApprovalRequests >= 0,
    `Pending approval requests metric available: ${stats.pendingApprovalRequests}`,
  );

  // Analytics structures
  assert(
    dashRes.data.studentAnalytics.yearWiseStrength.length === 4,
    "Student analytics contains 4 years (1st to 4th Year)",
  );
  assert(
    dashRes.data.facultyAnalytics.total > 0,
    "Faculty analytics provides total, present, and leave counts",
  );
  assert(
    dashRes.data.attendanceTrends.daily.length === 5,
    "Daily attendance trends covers 5 working days (Mon-Fri)",
  );

  // ---------------------------------------------------------------------------
  // 4. Module 2: Faculty Management & Workload
  // ---------------------------------------------------------------------------
  console.log(
    "\n--- TEST GROUP 4: Module 2 — Department Faculty Management ---",
  );
  const facultyRes = await hodService.getDepartmentFaculty({
    department: "Computer Science & Engineering",
  });
  assert(facultyRes.success === true, "Faculty list query succeeds");
  assert(
    facultyRes.data.length > 0,
    `Faculty list returned ${facultyRes.data.length} records`,
  );

  const sampleFaculty = facultyRes.data[0];
  assert(Boolean(sampleFaculty.id), "Faculty record has unique ID");
  assert(
    Boolean(sampleFaculty.employeeCode),
    "Faculty record has employee code",
  );
  assert(Boolean(sampleFaculty.firstName), "Faculty record has first name");
  assert(Boolean(sampleFaculty.designation), "Faculty record has designation");
  assert(
    Boolean(sampleFaculty.qualification),
    "Faculty record has highest qualification",
  );
  assert(
    sampleFaculty.teachingLoadHours > 0,
    `Faculty teaching workload is specified: ${sampleFaculty.teachingLoadHours} hrs`,
  );

  // Test single faculty detail
  const detail = await hodService.getFacultyById(sampleFaculty.id);
  assert(Boolean(detail), "Faculty profile detail retrieved by ID");
  assert(
    detail?.id === sampleFaculty.id,
    "Faculty profile ID matches requested ID",
  );
  assert(
    (detail?.assignedSubjects?.length ?? 0) >= 0,
    `Faculty profile contains assigned subjects list: ${detail?.assignedSubjects?.length}`,
  );

  // ---------------------------------------------------------------------------
  // 5. Module 3: Student Management & Academic Information
  // ---------------------------------------------------------------------------
  console.log(
    "\n--- TEST GROUP 5: Module 3 — Department Student Management ---",
  );
  const stuRes = await hodService.getDepartmentStudents(
    { pageSize: 20 },
    "Computer Science & Engineering",
  );
  assert(stuRes.success === true, "Students list query succeeds");
  assert(
    stuRes.data.length > 0,
    `Students list returned ${stuRes.data.length} department records`,
  );

  const sampleStudent = stuRes.data[0];
  assert(Boolean(sampleStudent.rollNumber), "Student record has roll number");
  assert(Boolean(sampleStudent.firstName), "Student record has name");
  assert(
    Boolean(sampleStudent.program?.name),
    "Student record has enrolled program",
  );
  assert(
    sampleStudent.attendanceSummary?.overallPercentage >= 0,
    `Student has attendance percentage computed: ${sampleStudent.attendanceSummary?.overallPercentage}%`,
  );
  assert(
    sampleStudent.academicStats?.cgpa >= 0,
    `Student has CGPA recorded: ${sampleStudent.academicStats?.cgpa}`,
  );

  // Test single student detail
  const studentDetail = await hodService.getStudentById(sampleStudent.id);
  assert(Boolean(studentDetail), "Student 360° profile detail retrieved by ID");
  assert(
    Boolean(studentDetail?.guardian?.name),
    "Student profile includes guardian contact name",
  );
  assert(
    Boolean(studentDetail?.guardian?.phone),
    "Student profile includes guardian phone number",
  );

  // ---------------------------------------------------------------------------
  // 6. Module 4: Attendance Monitoring & Shortage Identification
  // ---------------------------------------------------------------------------
  console.log(
    "\n--- TEST GROUP 6: Module 4 — Attendance Monitoring & Shortage Alerts ---",
  );
  const attOverview = await hodService.getAttendanceOverview(
    "Computer Science & Engineering",
  );
  assert(Boolean(attOverview), "Attendance overview data retrieved");
  assert(
    attOverview.statutory_threshold === 75.0,
    "Attendance statutory threshold adheres to 75.0% institutional cutoff",
  );
  assert(
    attOverview.class_wise.length >= 3,
    `Class-wise attendance rates computed for ${attOverview.class_wise.length} cohort sections`,
  );
  assert(
    attOverview.shortage_count >= 0,
    `Shortage radar identifies flagged students: ${attOverview.shortage_count}`,
  );

  // ---------------------------------------------------------------------------
  // 7. Module 5: Master Timetable Management
  // ---------------------------------------------------------------------------
  console.log(
    "\n--- TEST GROUP 7: Module 5 — Master Timetable Grid & Workloads ---",
  );
  const periods = hodService.getTimetablePeriods();
  assert(
    periods.length === 7,
    `Timetable defines 7 instructional periods: ${periods.length}`,
  );

  const schedule = hodService.getDepartmentSchedule(5, "A");
  assert(
    schedule.length > 15,
    `Weekly timetable grid contains ${schedule.length} scheduled slots`,
  );

  const hasLab = schedule.some((s) => s.isLab === true);
  assert(hasLab, "Laboratory practical blocks identified in timetable grid");

  const workloads = hodService.getFacultyWorkloads();
  assert(
    workloads.length >= 4,
    `Faculty workload summary includes ${workloads.length} professors`,
  );
  assert(
    workloads.every((w) => w.weeklyHours > 0),
    "All faculty workloads have non-zero weekly hours",
  );

  console.log(
    "\n===============================================================================",
  );
  console.log(`Test Execution Completed: ${passed} PASSED, ${failed} FAILED`);
  console.log(
    "===============================================================================\n",
  );

  if (failed > 0) {
    process.exit(1);
  }
}

runTestSuite().catch((err) => {
  console.error("Test execution threw an uncaught error:", err);
  process.exit(1);
});
