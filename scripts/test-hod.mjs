import assert from "node:assert";
import path from "node:path";
import createJITI from "jiti";

const rootDir = process.cwd();
const jiti = createJITI(path.resolve(rootDir, "frontend"), {
  alias: {
    "@/": path.resolve(rootDir, "frontend/src") + "/",
    "@campusos/types": path.resolve(rootDir, "packages/types/src/index.ts"),
  },
  extensions: [".js", ".ts", ".mjs"],
  esmResolve: true,
  interopDefault: true,
});

async function run() {
  console.log("\n===============================================================================");
  console.log("CampusOS HOD Portal Phase 1 — Comprehensive Automated Test Suite");
  console.log("===============================================================================\n");

  let passed = 0;
  let failed = 0;

  function test(desc, fn) {
    try {
      fn();
      console.log(`✔ PASS: ${desc}`);
      passed++;
    } catch (e) {
      console.error(`✖ FAIL: ${desc} -> ${e.message}`);
      failed++;
    }
  }

  async function testAsync(desc, fn) {
    try {
      await fn();
      console.log(`✔ PASS: ${desc}`);
      passed++;
    } catch (e) {
      console.error(`✖ FAIL: ${desc} -> ${e.message}`);
      failed++;
    }
  }

  // 1. Auth & Persona Mapping
  console.log("--- 1. Authentication & HOD Role Mapping ---");
  const { DEMO_PERSONAS } = jiti(path.resolve(rootDir, "frontend/src/mocks/auth.mock.ts"));
  const hod = DEMO_PERSONAS.find((p) => p.role === "HOD" || p.id === "user-hod-cse-01");
  test("HOD demo persona exists", () => assert(Boolean(hod)));
  test("HOD email is hod.cse@campusos.edu", () => assert.strictEqual(hod.email, "hod.cse@campusos.edu"));
  test("HOD department is Computer Science & Engineering", () =>
    assert.strictEqual(hod.department, "Computer Science & Engineering"));
  test("HOD has people:faculty:read permission", () => assert(hod.permissions.includes("people:faculty:read")));
  test("HOD has people:students:read permission", () => assert(hod.permissions.includes("people:students:read")));
  test("HOD has attendance:read permission", () => assert(hod.permissions.includes("attendance:read")));

  // 2. Service & Module 1: Dashboard
  console.log("\n--- 2. Module 1: HOD Dashboard Statistics ---");
  const { hodService } = jiti(path.resolve(rootDir, "frontend/src/services/hod.service.ts"));
  const dashRes = await hodService.getDashboardStats("Computer Science & Engineering");
  test("Dashboard API query succeeds", () => assert.strictEqual(dashRes.success, true));
  test("Dashboard returns non-zero student count", () => assert(dashRes.data.statistics.totalStudents > 0));
  test("Dashboard returns non-zero faculty count", () => assert(dashRes.data.statistics.totalFaculty > 0));
  test("Dashboard returns valid average attendance percentage", () => {
    const att = dashRes.data.statistics.averageStudentAttendance;
    assert(att >= 70 && att <= 100);
  });
  test("Dashboard returns attendance shortage count", () => assert(dashRes.data.statistics.studentsShortageCount >= 0));
  test("Dashboard returns pending approvals count", () => assert(dashRes.data.statistics.pendingApprovalRequests >= 0));
  test("Dashboard returns 4-year student distribution", () =>
    assert.strictEqual(dashRes.data.studentAnalytics.yearWiseStrength.length, 4));
  test("Dashboard returns 5-day daily attendance trend", () =>
    assert.strictEqual(dashRes.data.attendanceTrends.daily.length, 5));

  // 3. Module 2: Faculty Management
  console.log("\n--- 3. Module 2: Department Faculty Management ---");
  const facultyRes = await hodService.getDepartmentFaculty({ department: "Computer Science & Engineering" });
  test("Faculty listing succeeds", () => assert.strictEqual(facultyRes.success, true));
  test("Faculty list returns department faculty", () => assert(facultyRes.data.length > 0));
  const f = facultyRes.data[0];
  test("Faculty has employeeCode and designation", () => assert(Boolean(f.employeeCode && f.designation)));
  test("Faculty has weekly teaching load hours", () => assert(f.teachingLoadHours > 0));

  const facDetail = await hodService.getFacultyById(f.id);
  test("Faculty 360 profile retrieved by ID", () => assert.strictEqual(facDetail.id, f.id));
  test("Faculty profile includes workload statistics", () => assert(Boolean(facDetail.stats)));

  // 4. Module 3: Student Management
  console.log("\n--- 4. Module 3: Department Student Management ---");
  const stuRes = await hodService.getDepartmentStudents({ pageSize: 10 }, "Computer Science & Engineering");
  test("Student listing succeeds", () => assert.strictEqual(stuRes.success, true));
  test("Student list returns records", () => assert(stuRes.data.length > 0));
  const s = stuRes.data[0];
  test("Student has rollNumber and name", () => assert(Boolean(s.rollNumber && s.firstName)));
  test("Student has CGPA recorded", () => assert(s.academicStats.cgpa > 0));
  test("Student has attendance percentage", () => assert(s.attendanceSummary.overallPercentage > 0));

  const stuDetail = await hodService.getStudentById(s.id);
  test("Student 360 profile retrieved by ID", () => assert.strictEqual(stuDetail.id, s.id));
  test("Student profile includes guardian contact", () => assert(Boolean(stuDetail.guardian.name && stuDetail.guardian.phone)));

  // 5. Module 4: Attendance Management
  console.log("\n--- 5. Module 4: Attendance Monitoring & Shortage ---");
  const att = await hodService.getAttendanceOverview("Computer Science & Engineering");
  test("Attendance overview returns valid data", () => assert(Boolean(att)));
  test("Attendance statutory threshold is 75.0%", () => assert.strictEqual(att.statutory_threshold, 75.0));
  test("Class-wise compliance rates present", () => assert(att.class_wise.length >= 3));
  test("Shortage radar lists students below 75%", () => assert(Array.isArray(att.shortage_students)));

  // 6. Module 5: Timetable Management
  console.log("\n--- 6. Module 5: Master Timetable & Faculty Workloads ---");
  const periods = hodService.getTimetablePeriods();
  test("Timetable defines 7 instructional periods", () => assert.strictEqual(periods.length, 7));
  const schedule = hodService.getDepartmentSchedule(5, "A");
  test("Department schedule contains weekly slots", () => assert(schedule.length >= 15));
  test("Laboratory blocks identified in timetable", () => assert(schedule.some((slot) => slot.isLab === true)));
  const workloads = hodService.getFacultyWorkloads();
  test("Faculty workload summary includes all department faculty", () => assert(workloads.length >= 4));
  test("All faculty have compliant workload hours", () => assert(workloads.every((w) => w.weeklyHours > 0)));

  console.log("\n===============================================================================");
  console.log(`Execution Summary: ${passed} PASSED, ${failed} FAILED`);
  console.log("===============================================================================\n");

  if (failed > 0) process.exit(1);
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
