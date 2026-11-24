import assert from "node:assert";
import path from "node:path";
import { fileURLToPath } from "node:url";
import createJITI from "jiti";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, "..");
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
  console.log(
    "\n===============================================================================",
  );
  console.log(
    "CampusOS HOD Portal Phase 3 — Operations, Reports & Analytics Test Suite",
  );
  console.log(
    "===============================================================================\n",
  );

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

  const { hodService } = jiti("./src/services/hod.service.ts");

  // ---------------------------------------------------------------------------
  // 1. Module: Department Events & Activities
  // ---------------------------------------------------------------------------
  console.log("--- 1. Module: Department Events & Activities ---");
  const eventsRes = await hodService.getDepartmentEvents("ALL", "ALL");
  test("Department events API query succeeds", () => {
    assert.strictEqual(eventsRes.success, true);
  });
  test("Department events registry returns multi-category events", () => {
    assert(eventsRes.data.events.length >= 5);
  });

  const hackathonEvent = eventsRes.data.events.find(
    (e) => e.category === "Hackathon",
  );
  test("National Level Hackathon (CodeCraft 2026) is registered", () => {
    assert(!!hackathonEvent);
  });
  test("Hackathon participation tracked with actual attendance", () => {
    assert(hackathonEvent.actualParticipants > 100);
  });
  test("Completed hackathon has audited completion report", () => {
    assert(!!hackathonEvent.report);
  });

  const upcomingEventsRes = await hodService.getDepartmentEvents(
    "UPCOMING",
    "ALL",
  );
  test("Status filter restricts events to upcoming", () => {
    assert(
      upcomingEventsRes.data.events.every(
        (e) => e.status === "UPCOMING" || e.status === "SCHEDULED",
      ),
    );
  });

  const newEvtRes = await hodService.createDepartmentEvent({
    title: "International Symposium on Green Cloud Computing",
    description: "Annual technical symposium with IEEE student chapter.",
    category: "Symposium",
    startDate: "2026-12-15",
    venue: "Main Auditorium",
    facultyCoordinator: "Dr. Priya Nair",
    targetAudience: "All CSE Students",
    expectedParticipants: 200,
    budget: 50000,
  });
  test("HOD event creation succeeds with generated ID", () => {
    assert.strictEqual(newEvtRes.success, true);
    assert(newEvtRes.data.id.startsWith("evt-cse-"));
  });
  test("New event initialized with UPCOMING status", () => {
    assert.strictEqual(newEvtRes.data.status, "UPCOMING");
  });

  const reportRes = await hodService.submitEventReport(newEvtRes.data.id, {
    actualParticipants: 188,
    outcomes:
      "14 technical papers presented and 3 industry project collaborations initiated.",
    photosCount: 22,
    completionRemarks: "Conducted with outstanding student engagement.",
  });
  test("Event completion report marks event as COMPLETED", () => {
    assert.strictEqual(reportRes.success, true);
    assert.strictEqual(reportRes.data.status, "COMPLETED");
  });
  test("Event actual participants recorded in report", () => {
    assert.strictEqual(reportRes.data.actualParticipants, 188);
  });

  // ---------------------------------------------------------------------------
  // 2. Module: Placement & Internship Monitoring
  // ---------------------------------------------------------------------------
  console.log("\n--- 2. Module: Placement & Internship Monitoring ---");
  const placementOvRes = await hodService.getPlacementOverview();
  test("Placement overview API query succeeds", () => {
    assert.strictEqual(placementOvRes.success, true);
  });
  test("Department placement rate meets institutional target (>85%)", () => {
    assert(placementOvRes.data.placementPercentage >= 85.0);
  });
  test("Highest salary package tracked (>= 20 LPA)", () => {
    assert(placementOvRes.data.highestPackageLpa >= 20.0);
  });
  test("Top corporate recruiters identified (TCS, Infosys, Zoho, etc.)", () => {
    assert(placementOvRes.data.topRecruiters.length >= 5);
  });
  test("Paid internship participation tracked", () => {
    assert(placementOvRes.data.internshipParticipants > 100);
  });

  const placementStudentsRes = await hodService.getPlacementStudents(
    "ALL",
    "ALL",
    "ALL",
  );
  test("Student placement roster returns individual student records", () => {
    assert.strictEqual(placementStudentsRes.success, true);
    assert(placementStudentsRes.data.students.length > 0);
  });

  const placedSample = placementStudentsRes.data.students.find(
    (s) => s.placementStatus === "PLACED",
  );
  test("Placed student record contains verified company and CTC package", () => {
    assert(!!placedSample);
    assert(!!placedSample.company);
    assert(placedSample.packageLpa > 0);
  });

  // ---------------------------------------------------------------------------
  // 3. Module: Department Reports & Exports Engine
  // ---------------------------------------------------------------------------
  console.log("\n--- 3. Module: Department Reports & Exports ---");
  const reportCatsRes = await hodService.getReportCategories();
  test("Report categories registry API query succeeds", () => {
    assert.strictEqual(reportCatsRes.success, true);
  });
  test("Registry covers all 7 statutory categories (Student, Faculty, Attendance, Academic, Timetable, Placement, Events)", () => {
    assert.strictEqual(reportCatsRes.data.categories.length, 7);
  });

  const studentRepRes = await hodService.generateDepartmentReport({
    category: "STUDENT",
    reportType: "Department Student Strength Summary",
    academicYear: "2025-2026",
    semester: "ODD",
    section: "ALL",
  });
  test("Student report generation succeeds", () => {
    assert.strictEqual(studentRepRes.success, true);
  });
  test("Student report defines demographic columns", () => {
    assert(studentRepRes.data.columns.some((c) => c.key === "enrolled"));
  });
  test("Student report aggregates cohort rows across 4 years", () => {
    assert(studentRepRes.data.rows.length >= 10);
  });
  test("Report metadata captures HOD author and generation timestamp", () => {
    assert(!!studentRepRes.data.generatedBy);
    assert(!!studentRepRes.data.generatedAt);
  });

  const facRepRes = await hodService.generateDepartmentReport({
    category: "FACULTY",
    reportType: "Weekly Instructional Workload Audit",
    academicYear: "2025-2026",
  });
  test("Faculty workload report generation succeeds", () => {
    assert.strictEqual(facRepRes.success, true);
  });
  test("Faculty report tracks instructional hours", () => {
    assert(facRepRes.data.columns.some((c) => c.key === "load_hrs"));
  });

  // ---------------------------------------------------------------------------
  // 4. Module: Department Performance Analytics
  // ---------------------------------------------------------------------------
  console.log("\n--- 4. Module: Department Performance Analytics ---");
  const analyticsRes = await hodService.getPerformanceAnalytics();
  test("Performance analytics API query succeeds", () => {
    assert.strictEqual(analyticsRes.success, true);
  });
  test("Semester pass rates tracked across Semesters 1 to 6", () => {
    assert.strictEqual(
      analyticsRes.data.academicTrends.semesterPassRates.length,
      6,
    );
  });
  test("Year-wise performance aggregates 4 cohorts", () => {
    assert.strictEqual(
      analyticsRes.data.academicTrends.yearWisePerformance.length,
      4,
    );
  });
  test("Arrear clearance velocity monitored", () => {
    assert(
      analyticsRes.data.academicTrends.arrearResolutionVelocity.length >= 3,
    );
  });
  test("Attendance-academic correlation metrics established", () => {
    assert.strictEqual(
      analyticsRes.data.academicTrends.attendancePerformanceCorrelation.length,
      3,
    );
  });
  test("Faculty analytics reports total cadre count", () => {
    assert.strictEqual(analyticsRes.data.facultyAnalytics.totalFaculty, 28);
  });
  test("4-year longitudinal placement growth tracked", () => {
    assert(analyticsRes.data.departmentGrowth.placementRateGrowth.length >= 4);
  });

  // ---------------------------------------------------------------------------
  // 5. Module: Achievements & Honors Ledger
  // ---------------------------------------------------------------------------
  console.log("\n--- 5. Module: Department Achievements & Honors ---");
  const achRes = await hodService.getDepartmentAchievements(
    "ALL",
    "ALL",
    "ALL",
  );
  test("Achievements API query succeeds", () => {
    assert.strictEqual(achRes.success, true);
  });
  test("Achievements registry returns verified department honors", () => {
    assert(achRes.data.achievements.length >= 6);
  });
  test("Achievements ledger tracks both student and faculty honors", () => {
    assert(achRes.data.summary.studentAchievements > 0);
    assert(achRes.data.summary.facultyAchievements > 0);
  });

  const newAchRes = await hodService.recordDepartmentAchievement({
    title: "Finalist — Microsoft Imagine Cup 2026",
    description:
      "AI healthcare diagnosis application selected among top 10 national finalists.",
    category: "HACKATHON",
    recipientName: "Karthik Raja & Team",
    recipientType: "STUDENT",
    recipientId: "714021104042",
    achievementDate: "2026-03-12",
    academicYear: "2025-2026",
    eventOrOrganization: "Microsoft Corporation",
  });
  test("New achievement recorded and verified in honors ledger", () => {
    assert.strictEqual(newAchRes.success, true);
    assert.strictEqual(newAchRes.data.verificationStatus, "VERIFIED");
  });

  // ---------------------------------------------------------------------------
  // 6. Module: Accreditation & Quality Documentation (NBA / NAAC)
  // ---------------------------------------------------------------------------
  console.log("\n--- 6. Module: Accreditation & Documentation ---");
  const accOvRes = await hodService.getAccreditationOverview();
  test("Accreditation overview API query succeeds", () => {
    assert.strictEqual(accOvRes.success, true);
  });
  test("Accreditation framework covers Criteria 1 through 5", () => {
    assert.strictEqual(accOvRes.data.criteria.length, 5);
  });
  test("NBA Tier-1 readiness index exceeds 90%", () => {
    assert(accOvRes.data.readinessPercentage >= 90.0);
  });

  const docsRes = await hodService.getAccreditationDocuments(
    "ALL",
    "ALL",
    "ALL",
  );
  test("Accreditation document vault returns evidence artifacts", () => {
    assert.strictEqual(docsRes.success, true);
    assert(docsRes.data.documents.length >= 5);
  });

  const uploadDocRes = await hodService.uploadAccreditationDocument({
    title: "Faculty Industry Internship & Sabbatical Certifications",
    criterion: "CRITERION_5",
    academicYear: "2025-2026",
    description: "Proof of summer industrial immersion for CSE core faculty.",
    fileName: "Faculty_Industry_Immersion_2026.pdf",
    fileType: "PDF",
    fileSizeKb: 2150,
  });
  test("Accreditation document registered into review queue", () => {
    assert.strictEqual(uploadDocRes.success, true);
    assert.strictEqual(uploadDocRes.data.reviewStatus, "UNDER_REVIEW");
  });

  // ---------------------------------------------------------------------------
  // Summary
  // ---------------------------------------------------------------------------
  console.log(
    "\n===============================================================================",
  );
  console.log(`Phase 3 Execution Summary: ${passed} PASSED, ${failed} FAILED`);
  console.log(
    "===============================================================================\n",
  );

  if (failed > 0) {
    process.exit(1);
  }
}

run().catch((err) => {
  console.error("Test execution threw exception:", err);
  process.exit(1);
});
