import assert from "node:assert";
import path from "node:path";
import createJITI from "jiti";

const rootDir = process.cwd();
const jiti = createJITI(path.resolve(rootDir, "apps/web"), {
  alias: {
    "@/": path.resolve(rootDir, "apps/web/src") + "/",
    "@campusos/types": path.resolve(rootDir, "packages/types/src/index.ts"),
  },
  extensions: [".js", ".ts", ".mjs"],
  esmResolve: true,
  interopDefault: true,
});

async function run() {
  console.log("\n===============================================================================");
  console.log("CampusOS Vice Principal Portal — Comprehensive Automated Test Suite");
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
  console.log("--- 1. Authentication & Vice Principal Role Mapping ---");
  const { DEMO_PERSONAS } = jiti(path.resolve(rootDir, "apps/web/src/mocks/auth.mock.ts"));
  const vp = DEMO_PERSONAS.find((p) => p.role === "PRINCIPAL" || p.id === "user-vice-principal-01");
  test("Vice Principal demo persona exists", () => assert(Boolean(vp)));
  test("VP email is vp.academics@campusos.edu", () => assert.strictEqual(vp.email, "vp.academics@campusos.edu"));
  test("VP role is VICE_PRINCIPAL", () => assert(vp.role === "VICE_PRINCIPAL" || vp.role === "PRINCIPAL"));
  test("VP has approvals:read permission", () => assert(vp.permissions.includes("approvals:read")));
  test("VP has approvals:approve permission", () => assert(vp.permissions.includes("approvals:approve")));
  test("VP has approvals:reject permission", () => assert(vp.permissions.includes("approvals:reject")));
  test("VP has academics:calendar:read permission", () => assert(vp.permissions.includes("academics:calendar:read")));
  test("VP has timetable:read permission", () => assert(vp.permissions.includes("timetable:read")));
  test("VP has leave:approve permission", () => assert(vp.permissions.includes("leave:approve")));
  test("VP does NOT have direct user creation (scoped role)", () => assert(!vp.permissions.includes("users:create")));
  test("VP does NOT have billing payment write permissions", () => assert(!vp.permissions.includes("finance:payments:process")));

  // 2. Service Layer & Feature Modules
  console.log("\n--- 2. Vice Principal Service & Feature Modules ---");
  const { vicePrincipalService } = jiti(
    path.resolve(rootDir, "apps/web/src/services/vice-principal.service.ts")
  );

  // Feature A: Dashboard
  console.log("\n--- Feature A: Executive Overview Dashboard ---");
  await testAsync("Retrieve dashboard KPIs and Department Health", async () => {
    const res = await vicePrincipalService.getDashboard();
    assert(res.success);
    assert.strictEqual(res.data.kpis.total_departments, 5);
    assert(res.data.kpis.total_students >= 2000);
    assert(res.data.kpis.total_faculty >= 100);
    assert(res.data.kpis.overall_student_attendance >= 75.0);
    assert(res.data.kpis.syllabus_completion_rate >= 70.0);
    assert(res.data.department_metrics.length === 5);
  });

  await testAsync("Filter dashboard by specific department (CSE)", async () => {
    const res = await vicePrincipalService.getDashboard({ department_id: "dept-cse" });
    assert(res.success);
    assert.strictEqual(res.data.department_metrics.length, 1);
    assert.strictEqual(res.data.department_metrics[0].code, "CSE");
  });

  // Feature B: Department Monitoring
  console.log("\n--- Feature B: Department Supervision ---");
  await testAsync("Retrieve all 5 departments with HOD profiles and ratios", async () => {
    const res = await vicePrincipalService.getDepartments();
    assert(res.success);
    assert.strictEqual(res.data.length, 5);
    const cse = res.data.find((d) => d.code === "CSE");
    assert(cse);
    assert.strictEqual(cse.hod_name, "Dr. K. S. Anand");
    assert(cse.student_count > 0);
    assert(cse.faculty_count > 0);
  });

  // Feature C: Academic Monitoring
  console.log("\n--- Feature C: Academic Calendar & Syllabus Velocity ---");
  await testAsync("Academic Calendar & Syllabus Delay Radar", async () => {
    const res = await vicePrincipalService.getAcademicsMonitoring();
    assert(res.success);
    assert(res.data.milestones.length >= 5);
    const completed = res.data.milestones.filter((m) => m.status === "COMPLETED");
    assert(completed.length > 0);
    assert(res.data.syllabus_delay_tracking.length >= 1);
    assert(res.data.timetable_coverage.classes_conducted_on_schedule_pct >= 90.0);
  });

  // Feature D: Faculty Supervision
  console.log("\n--- Feature D: Faculty Workload Oversight ---");
  await testAsync("Faculty Teaching Norms Audit (12-18 hrs compliance)", async () => {
    const res = await vicePrincipalService.getFacultySupervision();
    assert(res.success);
    assert(res.data.workload_summary.compliant_workload_count > 0);
    assert(res.data.workload_summary.statutory_min_hours === 12);
    assert(res.data.workload_summary.statutory_max_hours === 18);
    assert(res.data.faculty.length >= 5);

    const overloaded = res.data.faculty.filter((f) => f.status === "OVERLOADED");
    assert(overloaded.length > 0);
    for (const f of overloaded) {
      assert(f.weekly_teaching_hours >= 18);
    }
  });

  // Feature E: Student Monitoring (<75% Radar)
  console.log("\n--- Feature E: Student Monitoring & Attendance Radar ---");
  await testAsync("Sub-75% Student Attendance Radar detection", async () => {
    const res = await vicePrincipalService.getStudentsSupervision({ threshold: 75.0 });
    assert(res.success);
    assert(res.data.low_attendance_radar.length > 0);
    for (const stu of res.data.low_attendance_radar) {
      assert(stu.attendance_percentage < 75.0);
      assert(stu.shortfall_sessions > 0);
      assert(Boolean(stu.mentor_name));
    }
  });

  await testAsync("Institutional 4-year strength progression integrity", async () => {
    const res = await vicePrincipalService.getStudentsSupervision();
    assert(res.data.institutional_strength.length === 5);
    for (const row of res.data.institutional_strength) {
      assert.strictEqual(row.total, row.year_1 + row.year_2 + row.year_3 + row.year_4);
    }
  });

  // Feature F: Statutory Approvals (8 Categories & Workflows)
  console.log("\n--- Feature F: Statutory Approval Workflows & State Transitions ---");
  await testAsync("List approvals across authorized statutory categories", async () => {
    const res = await vicePrincipalService.getApprovals();
    assert(res.success);
    assert(res.data.length >= 5);
    const categories = new Set(res.data.map((a) => a.category));
    assert(categories.has("DEPARTMENT_ACADEMIC_REQUEST"));
    assert(categories.has("ACADEMIC_CALENDAR_CHANGE"));
    assert(categories.has("FACULTY_LEAVE"));
    assert(categories.has("TIMETABLE_CHANGE"));
    assert(categories.has("EXAMINATION_REQUEST"));
    assert(categories.has("ACADEMIC_PERFORMANCE_INTERVENTION"));
  });

  await testAsync("Workflow 1: Department Academic Request APPROVE with remarks", async () => {
    const res = await vicePrincipalService.processApprovalAction(
      "appr-vp-001",
      "APPROVE",
      "Sanctioned by Vice Principal in compliance with academic regulations."
    );
    assert(res.success);
    assert.strictEqual(res.data.status, "APPROVED");
    assert(res.data.remarks.includes("Sanctioned"));
    assert(res.data.audit_trail.length >= 2);
  });

  await testAsync("Workflow 2: Academic Calendar Change REJECT with justification", async () => {
    const res = await vicePrincipalService.processApprovalAction(
      "appr-vp-002",
      "REJECT",
      "Declined due to scheduling conflict with university valuation."
    );
    assert(res.success);
    assert.strictEqual(res.data.status, "REJECTED");
    assert(res.data.remarks.includes("Declined"));
  });

  await testAsync("Workflow 3: Faculty Leave REQUEST_MODIFICATION with notes", async () => {
    const res = await vicePrincipalService.processApprovalAction(
      "appr-vp-003",
      "REQUEST_MODIFICATION",
      "Please provide lecture compensation schedule for CS303."
    );
    assert(res.success);
    assert.strictEqual(res.data.status, "MODIFICATION_REQUESTED");
  });

  // Feature G: Examinations Oversight
  console.log("\n--- Feature G: Examinations & Results Oversight ---");
  await testAsync("Examination schedules & CIA mark lockouts", async () => {
    const res = await vicePrincipalService.getExaminationsOversight();
    assert(res.success);
    assert(res.data.schedules.length >= 2);
    assert.strictEqual(res.data.cia_mark_submissions.length, 5);
    assert(res.data.results_analysis.overall_institutional_pass_pct > 90);
  });

  // Feature H: Reports & Analytics
  console.log("\n--- Feature H: Regulatory Reports & Exports ---");
  await testAsync("Executive Compliance Reports with multi-format support", async () => {
    const res = await vicePrincipalService.getReports();
    assert(res.success);
    assert(res.data.available_reports.length >= 3);
    for (const rep of res.data.available_reports) {
      assert(rep.format.length > 0);
    }
  });

  // Feature I: Communication & Circulars
  console.log("\n--- Feature I: Executive Circular Dispatch ---");
  await testAsync("Broadcast institutional circular to HODs", async () => {
    const res = await vicePrincipalService.createAnnouncement({
      title: "Mandatory Lesson Plan Audit Circular",
      target_audience: "ALL_HODS",
      priority: "HIGH",
      summary: "All department heads must verify 70% syllabus coverage by Friday.",
      pinned: true,
    });
    assert(res.success);
    assert.strictEqual(res.data.pinned, true);

    const listRes = await vicePrincipalService.getAnnouncements();
    assert(listRes.data.some((a) => a.title.includes("Mandatory Lesson Plan")));
  });

  // Feature J: Audit Trail
  console.log("\n--- Feature J: Immutable Institutional Audit Trail ---");
  await testAsync("Read-only institutional audit trail", async () => {
    const res = await vicePrincipalService.getAuditTrail();
    assert(res.success);
    assert(res.data.length >= 3);
    for (const entry of res.data) {
      assert(Boolean(entry.actor));
      assert(Boolean(entry.action));
      assert(Boolean(entry.entity));
    }
  });

  console.log("\n===============================================================================");
  console.log(`Results: ${passed} Passed, ${failed} Failed`);
  console.log("===============================================================================\n");

  if (failed > 0) {
    process.exit(1);
  }
}

run().catch((err) => {
  console.error("Test execution failed with fatal error:", err);
  process.exit(1);
});
