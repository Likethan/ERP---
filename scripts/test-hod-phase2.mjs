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
  console.log("\n===============================================================================");
  console.log("CampusOS HOD Portal Phase 2 — Academic Management & Approvals Test Suite");
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

  const { hodService } = jiti(path.resolve(rootDir, "frontend/src/services/hod.service.ts"));

  // 1. Module: Subjects & Curriculum Management
  console.log("--- 1. Module: Subject & Curriculum Management ---");
  const curRes = await hodService.getCurriculum();
  test("Curriculum API query succeeds", () => assert.strictEqual(curRes.success, true));
  test("Curriculum regulation is R-2026 Autonomous", () =>
    assert(curRes.data.regulation.includes("R-2026")));
  test("Total curriculum subjects returned", () => assert(curRes.data.subjects.length > 0));
  test("Core subjects include CS301 (DSA) and CS302 (DBMS)", () => {
    const codes = curRes.data.subjects.map((s) => s.code);
    assert(codes.includes("CS301") && codes.includes("CS302"));
  });
  test("All department subjects have assigned faculty", () => {
    assert(curRes.data.subjects.every((s) => Boolean(s.assignedFaculty)));
  });
  test("Subject allocation summary reports zero conflicts", () => {
    assert.strictEqual(curRes.data.allocationSummary.allocationConflicts, 0);
  });
  test("Course outcomes (CO) sample defines Bloom's taxonomy levels", () => {
    assert(curRes.data.courseOutcomesSample.length >= 5);
    assert(curRes.data.courseOutcomesSample.every((co) => Boolean(co.bloomLevel)));
  });
  test("CO-PO articulation matrix maps across PO1-PO5 and PSO1-PSO2", () => {
    assert(curRes.data.coPoMatrix.length >= 5);
    assert(curRes.data.coPoMatrix[0].PO1 > 0);
  });

  // 2. Module: Lesson Plan Monitoring
  console.log("\n--- 2. Module: Lesson Plan Monitoring ---");
  const lpRes = await hodService.getLessonPlans();
  test("Lesson plans API query succeeds", () => assert.strictEqual(lpRes.success, true));
  test("Lesson plans returned for monitored department courses", () =>
    assert(lpRes.data.lessonPlans.length >= 3));
  test("CS301 lesson plan contains 5 syllabus units", () => {
    const cs301 = lpRes.data.lessonPlans.find((p) => p.courseCode === "CS301");
    assert(cs301 && cs301.units.length === 5);
  });
  test("Unit-wise planned vs completed hours tracked", () => {
    const cs301 = lpRes.data.lessonPlans.find((p) => p.courseCode === "CS301");
    assert(cs301.totalPlannedHours === 45);
    assert(cs301.totalCompletedHours > 0);
  });
  test("Topic-wise completed checklist verified", () => {
    const cs301 = lpRes.data.lessonPlans.find((p) => p.courseCode === "CS301");
    assert(cs301.units[0].topics.every((t) => t.completed === true));
  });
  test("Average department syllabus completion is calculated", () => {
    assert(lpRes.data.summary.averageSyllabusCompletion >= 70);
  });

  // 3. Module: Examination Management
  console.log("\n--- 3. Module: Examination Management ---");
  const examRes = await hodService.getExaminations();
  test("Examinations API query succeeds", () => assert.strictEqual(examRes.success, true));
  test("Active assessment terms tracked (IA-1, IA-2, Model, ESE)", () => {
    assert(examRes.data.terms.length >= 4);
    assert(examRes.data.terms.some((t) => t.status === "COMPLETED"));
    assert(examRes.data.terms.some((t) => t.status === "ONGOING"));
  });
  test("Examination schedules include date, hall, and invigilator", () => {
    assert(examRes.data.schedules.length >= 4);
    assert(examRes.data.schedules.every((s) => Boolean(s.date) && Boolean(s.hallNumber)));
  });
  test("Marks submission progress monitors pending submissions", () => {
    assert(examRes.data.submissionProgress.length >= 3);
    const cs303 = examRes.data.submissionProgress.find((p) => p.courseCode === "CS303");
    assert(cs303 && cs303.missingMarks === 4);
  });
  test("Submission compliance rate calculated", () => {
    assert(examRes.data.summary.submissionComplianceRate >= 90.0);
  });

  // 4. Module: Internal Marks Management
  console.log("\n--- 4. Module: Internal Marks Management ---");
  const marksRes = await hodService.getInternalMarks();
  test("Internal marks API query succeeds", () => assert.strictEqual(marksRes.success, true));
  test("Marks ledger returns student records with roll numbers", () => {
    assert(marksRes.data.records.length > 0);
    assert(marksRes.data.records.every((r) => Boolean(r.rollNumber)));
  });
  test("Marks breakdown includes IA1, IA2, Model, Assignments, Attendance", () => {
    const r = marksRes.data.records[0];
    assert("ia1" in r && "ia2" in r && "ia3Model" in r && "assignments" in r && "attendanceScore" in r);
    assert(r.totalInternal <= r.maxInternal);
  });
  test("Attention radar identifies students below 50% threshold", () => {
    assert(marksRes.data.attentionList.length > 0);
    assert(marksRes.data.attentionList.every((s) => s.percentage < 50.0 || s.requiresAttention));
  });

  // 5. Audited Marks Correction Workflow
  console.log("\n--- 5. Audited Marks Correction Workflow ---");
  const corrRes = await hodService.requestMarkCorrection({
    studentId: "std-001",
    assessmentId: "asm-internal-2026",
    courseCode: "CS301",
    originalMark: 47.5,
    requestedMark: 49.0,
    reason: "Q4(b) answer script retotalling verification.",
  });
  test("Marks correction request accepted into audit ledger", () => {
    assert.strictEqual(corrRes.success, true);
    assert.strictEqual(corrRes.data.status, "PENDING_AUDIT");
  });

  // 6. Module: Semester Results & Performance Analytics
  console.log("\n--- 6. Module: Semester Results & Performance Analytics ---");
  const resultsRes = await hodService.getSemesterResults();
  test("Semester results API query succeeds", () => assert.strictEqual(resultsRes.success, true));
  test("Department overall pass rate is recorded (>90%)", () => {
    assert(resultsRes.data.overview.passPercentage >= 90.0);
    assert.strictEqual(resultsRes.data.overview.totalStudentsAppeared, 240);
  });
  test("Subject-wise pass percentages and grade points available", () => {
    assert(resultsRes.data.subjectResults.length >= 4);
    assert(resultsRes.data.subjectResults.every((s) => s.passPercentage >= 80.0));
  });
  test("Department toppers list identifies CGPA >= 8.5 achievers", () => {
    assert(resultsRes.data.toppers.length >= 3);
    assert(resultsRes.data.toppers[0].cgpa >= 9.0);
    assert.strictEqual(resultsRes.data.toppers[0].arrears, 0);
  });
  test("Students needing support tracked with remedial plans", () => {
    assert(resultsRes.data.studentsNeedingSupport.length > 0);
    assert(resultsRes.data.studentsNeedingSupport.every((s) => Boolean(s.supportPlan)));
  });
  test("Arrear analytics categorizes single, multiple, and repeated backlogs", () => {
    const a = resultsRes.data.arrearAnalytics;
    assert(a.singleArrearCount > 0 && a.multipleArrearsCount > 0 && a.repeatedArrearsCount > 0);
    assert(a.subjectWiseArrearBreakdown.length > 0);
  });

  // 7. Module: Leave & Department Approvals
  console.log("\n--- 7. Module: Leave & Department Approvals Management ---");
  const appRes = await hodService.getApprovals();
  test("Approvals queue API query succeeds", () => assert.strictEqual(appRes.success, true));
  test("Approvals stats track pending, approved, and total counts", () => {
    assert(appRes.data.stats.totalRequests >= 9);
    assert(appRes.data.stats.pending > 0);
  });
  test("Approval requests cover Faculty, Student, and Department categories", () => {
    const cats = new Set(appRes.data.requests.map((r) => r.category));
    assert(cats.has("FACULTY") && cats.has("STUDENT") && cats.has("DEPARTMENT"));
  });
  test("Each request maintains applicant identity, urgency, and audit history", () => {
    assert(appRes.data.requests.every((r) => Boolean(r.submittedBy) && Boolean(r.urgency)));
    assert(appRes.data.requests.every((r) => Array.isArray(r.auditTrail) && r.auditTrail.length > 0));
  });

  // 8. Approval Workflow Action Execution
  console.log("\n--- 8. HOD Statutory Decision Execution Workflow ---");
  const actionRes = await hodService.processApprovalAction(
    "appr-cse-001",
    "APPROVE",
    "Approved by HOD. Verified lecture coverage by substitute faculty."
  );
  test("HOD approval action executes successfully", () => {
    assert.strictEqual(actionRes.success, true);
    assert.strictEqual(actionRes.data.status, "APPROVED");
  });
  test("HOD remarks and decision timestamp recorded in audit trail", () => {
    const lastAudit = actionRes.data.auditTrail[actionRes.data.auditTrail.length - 1];
    assert.strictEqual(lastAudit.action, "APPROVED");
    assert(lastAudit.notes.includes("Approved by HOD"));
    assert(Boolean(actionRes.data.decisionDate));
  });

  console.log("\n===============================================================================");
  console.log(`Phase 2 Execution Summary: ${passed} PASSED, ${failed} FAILED`);
  console.log("===============================================================================\n");

  if (failed > 0) {
    process.exit(1);
  }
}

run().catch((err) => {
  console.error("Test execution failed:", err);
  process.exit(1);
});
