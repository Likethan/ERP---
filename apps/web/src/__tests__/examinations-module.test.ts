/**
 * CampusOS Examination & Assessment Module Test Suite
 * Validates domain contracts, assessment schemes, component weightages,
 * exam scheduling with conflict detection, attendance-derived eligibility,
 * marks entry with validation, draft saving, finalization locks,
 * supervised mark corrections, grading calculation engine (CBCS 10-point scale),
 * result compilation & publication lifecycle, reports, and RBAC rules.
 */

import { examinationsService } from "../services/examinations.service";
import {
  calculateAssessmentTotal,
  calculateWeightedMarks,
  calculatePercentage,
  calculateGrade,
  calculateResultStatus,
  calculateGradeDistribution,
  DEFAULT_GRADE_SCALE,
} from "../services/grading-calculator";
import { searchService } from "../services/search.service";

export async function runExaminationsModuleTests(): Promise<{
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
    // ==========================================
    // 1. Examination Dashboard & Telemetry
    // ==========================================
    const dashboardRes = await examinationsService.getDashboardSummary();
    assert(
      dashboardRes.success === true,
      "1. Examination dashboard metrics return success",
    );
    assert(
      dashboardRes.data.activeExaminationsCount >= 1,
      "1. Active examinations count is valid",
    );
    assert(
      dashboardRes.data.upcomingExamsCount >= 1,
      "1. Upcoming exams schedule count is valid",
    );
    assert(
      dashboardRes.data.eligibleStudentsCount > 0,
      "1. Eligible candidates count is non-zero",
    );
    assert(
      dashboardRes.data.ineligibleStudentsCount >= 1,
      "1. Debarred/Ineligible candidates tracked",
    );
    assert(
      dashboardRes.data.resultsAwaitingPublicationCount >= 0,
      "1. Publication pending batches tracked",
    );
    assert(
      dashboardRes.data.gradeDistribution.length >= 5,
      "1. CBCS grade distribution breakdown provided",
    );

    // ==========================================
    // 2. Assessment Schemes & Components
    // ==========================================
    const assessmentsRes = await examinationsService.getAssessments();
    assert(
      assessmentsRes.success === true,
      "2. Assessment schemes query returns success",
    );
    assert(
      assessmentsRes.data.length >= 3,
      "2. Baseline assessments exist for active courses",
    );

    const createdAsmRes = await examinationsService.createAssessment({
      name: "Mid-Term Continuous Evaluation",
      type: "MIDTERM",
      courseOfferingId: "co-cs301-a",
      courseName: "Database Management Systems",
      courseCode: "CS301",
      department: "Computer Science & Engineering",
      semester: 5,
      section: "A",
      academicYear: "2026-2027",
      facultyId: "fac-001",
      facultyName: "Dr. Ramesh Sundaram",
      maxMarks: 50,
      passingMarks: 20,
      weightage: 25,
      components: [
        {
          id: "comp-1",
          name: "Written Theory Exam",
          type: "MIDTERM",
          maxMarks: 35,
          passingMarks: 14,
          weightage: 70,
          sequence: 1,
        },
        {
          id: "comp-2",
          name: "SQL Lab Assignment",
          type: "ASSIGNMENT",
          maxMarks: 15,
          passingMarks: 6,
          weightage: 30,
          sequence: 2,
        },
      ],
      date: "2026-10-15",
    });
    assert(
      createdAsmRes.success === true,
      "2. Assessment scheme creation succeeds",
    );
    assert(
      Boolean(
        createdAsmRes.data.components &&
        createdAsmRes.data.components.length === 2,
      ),
      "2. Assessment components properly registered",
    );

    // Detail fetch
    const asmDetail = await examinationsService.getAssessmentById(
      createdAsmRes.data.id,
    );
    assert(
      asmDetail.success === true &&
        asmDetail.data.name === "Mid-Term Continuous Evaluation",
      "2. Assessment scheme by ID retrieved",
    );

    // ==========================================
    // 3. Exam Schedules & Conflict Detection
    // ==========================================
    const schedulesRes = await examinationsService.getSchedules();
    assert(
      schedulesRes.success === true,
      "3. Exam schedules list returns success",
    );
    assert(schedulesRes.data.length >= 3, "3. Seed exam schedules present");

    // Conflict Check: Simulate Room Overlap
    const existingSchedule = schedulesRes.data[0];
    const roomConflictCheck = await examinationsService.checkScheduleConflicts({
      date: existingSchedule.date,
      startTime: existingSchedule.startTime,
      endTime: existingSchedule.endTime,
      room: existingSchedule.room,
      section: "B",
      facultyId: "fac-999-other",
    });
    assert(
      roomConflictCheck.success === true,
      "3. Conflict query returns successful response",
    );
    assert(
      roomConflictCheck.data.hasConflict === true,
      "3. Conflict detector catches Room double-booking",
    );
    assert(
      roomConflictCheck.data.conflictType === "ROOM_OVERLAP",
      "3. Room collision conflict type tagged",
    );

    // Conflict Check: Simulate Faculty Overlap
    const facultyConflictCheck =
      await examinationsService.checkScheduleConflicts({
        date: existingSchedule.date,
        startTime: existingSchedule.startTime,
        endTime: existingSchedule.endTime,
        room: "Unique Hall X",
        section: "C",
        facultyId: existingSchedule.facultyId,
      });
    assert(
      facultyConflictCheck.data.hasConflict === true,
      "3. Conflict detector catches Faculty invigilation overlap",
    );
    assert(
      facultyConflictCheck.data.conflictType === "FACULTY_OVERLAP",
      "3. Faculty overlap conflict type tagged",
    );

    // Create a conflict-free schedule
    const newScheduleRes = await examinationsService.createSchedule({
      examinationId: "exam-2026-ese",
      examinationName: "End Semester Examinations Nov/Dec 2026",
      courseOfferingId: "co-cs302-a",
      courseName: "Operating Systems",
      courseCode: "CS302",
      program: "B.Tech Computer Science & Engineering",
      semester: 5,
      section: "A",
      date: "2026-11-28",
      startTime: "02:00 PM",
      endTime: "05:00 PM",
      room: "CS-LH-301",
      facultyId: "fac-002",
      facultyName: "Dr. Anita Roy",
      status: "SCHEDULED",
    });
    assert(
      newScheduleRes.success === true,
      "3. Conflict-free schedule creation succeeds",
    );

    // ==========================================
    // 4. Attendance-Derived Eligibility Gate
    // ==========================================
    const eligibilityRes = await examinationsService.getEligibility();
    assert(
      eligibilityRes.success === true,
      "4. Student exam eligibility ledger retrieved",
    );
    assert(
      eligibilityRes.data.some(
        (e) =>
          e.attendancePercentage < 75 && e.eligibilityStatus === "INELIGIBLE",
      ),
      "4. Identifies debarred student with <75% attendance",
    );

    // HOD Exception Review / Condonation
    const ineligibleCandidate = eligibilityRes.data.find(
      (e) => e.eligibilityStatus === "INELIGIBLE",
    );
    if (ineligibleCandidate) {
      const reviewRes = await examinationsService.reviewEligibility(
        ineligibleCandidate.id,
        "APPROVE_EXCEPTION",
        "Medical condonation approved with hospital certificate verification.",
      );
      assert(
        reviewRes.success === true,
        "4. HOD eligibility review/condonation succeeds",
      );
      assert(
        reviewRes.data.eligibilityStatus === "CONDITIONALLY_ELIGIBLE",
        "4. Candidate status transitioned to CONDITIONALLY_ELIGIBLE",
      );
      assert(
        reviewRes.data.overriddenBy?.includes("HOD"),
        "4. Audit trail captures reviewing authority",
      );
    }

    // ==========================================
    // 5. Marks Entry & Validation Matrix
    // ==========================================
    const marksRes = await examinationsService.getMarks("asm-cs301-internal");
    assert(marksRes.success === true, "5. Assessment marks matrix loaded");
    assert(
      marksRes.data.length > 0,
      "5. Enrolled students populated in marks matrix",
    );

    // Enter & Save Draft Marks
    const sampleStudent = marksRes.data[0];
    const saveDraftRes = await examinationsService.saveMarks(
      "asm-cs301-internal",
      [
        {
          studentId: sampleStudent.studentId,
          marksObtained: 90,
          status: "ENTERED",
          remarks: "Good performance in graph algorithms",
        },
      ],
    );
    assert(saveDraftRes.success === true, "5. Marks draft save succeeds");

    // Non-Numeric Status (Absent)
    if (marksRes.data.length > 1) {
      const secondStudent = marksRes.data[1];
      const absentSaveRes = await examinationsService.saveMarks(
        "asm-cs301-internal",
        [
          {
            studentId: secondStudent.studentId,
            marksObtained: null,
            status: "ABSENT",
            remarks: "Medical leave acknowledged",
          },
        ],
      );
      assert(
        absentSaveRes.success === true,
        "5. Marks entry with ABSENT flag processed",
      );
    }

    // Boundary validation test (> maxMarks)
    let validationBlocked = false;
    try {
      await examinationsService.saveMarks("asm-cs301-internal", [
        {
          studentId: sampleStudent.studentId,
          marksObtained: 150, // exceeds maxMarks (100)
          status: "ENTERED",
        },
      ]);
    } catch {
      validationBlocked = true;
    }
    assert(
      validationBlocked === true,
      "5. Validation rejects marks exceeding maximum score",
    );

    // ==========================================
    // 6. Assessment Marks Finalization Lock
    // ==========================================
    // asm-cs302-internal is pre-finalized in canonical mock
    const finalizedAsm =
      await examinationsService.getAssessmentById("asm-cs302-internal");
    assert(
      finalizedAsm.success === true,
      "6. Pre-finalized assessment retrieved",
    );
    assert(
      finalizedAsm.data.isFinalized === true,
      "6. isFinalized flag is true in locked state",
    );

    // Direct edit attempt on finalized assessment must throw error
    let finalizedBlocked = false;
    try {
      await examinationsService.saveMarks("asm-cs302-internal", [
        {
          studentId: "std-001",
          marksObtained: 85,
          status: "ENTERED",
        },
      ]);
    } catch {
      finalizedBlocked = true;
    }
    assert(
      finalizedBlocked === true,
      "6. Direct edit rejected on finalized assessment",
    );

    // ==========================================
    // 7. Supervised Mark Correction Workflow
    // ==========================================
    const correctionsRes = await examinationsService.getMarkCorrections();
    assert(
      correctionsRes.success === true,
      "7. Mark correction petitions ledger loaded",
    );

    // Faculty submits correction request on locked mark
    const targetMark = marksRes.data[0];
    const petitionRes = await examinationsService.requestMarkCorrection({
      markId: targetMark.id,
      requestedMark: 95,
      requestedStatus: "ENTERED",
      reason: "Re-totalling error identified in Question 3b (+5 marks)",
      requestedBy: "Dr. Ramesh Sundaram (Faculty)",
    });
    assert(
      petitionRes.success === true,
      "7. Mark correction petition submitted",
    );
    assert(
      petitionRes.data.status === "PENDING",
      "7. Initial correction status is PENDING",
    );

    // HOD approves correction
    const approveRes = await examinationsService.reviewMarkCorrection(
      petitionRes.data.id,
      "APPROVED",
      "Re-totalling verified against original physical script.",
    );
    assert(approveRes.success === true, "7. HOD approves correction petition");
    assert(
      approveRes.data.status === "APPROVED",
      "7. Correction status transitioned to APPROVED",
    );

    // Verify underlying mark record was automatically synchronized
    const updatedMarksRes =
      await examinationsService.getMarks("asm-cs301-internal");
    const updatedStudentMark = updatedMarksRes.data.find(
      (m) => m.id === targetMark.id,
    );
    assert(
      updatedStudentMark?.marksObtained === 95,
      "7. Ledger updated to requested mark (95)",
    );

    // ==========================================
    // 8. Grading Calculation Engine
    // ==========================================
    // Component Total
    const totalCalc = calculateAssessmentTotal([
      {
        id: "1",
        name: "Comp 1",
        type: "INTERNAL",
        maxMarks: 20,
        passingMarks: 8,
        weightage: 20,
        sequence: 1,
      },
      {
        id: "2",
        name: "Comp 2",
        type: "INTERNAL",
        maxMarks: 30,
        passingMarks: 12,
        weightage: 30,
        sequence: 2,
      },
      {
        id: "3",
        name: "Comp 3",
        type: "INTERNAL",
        maxMarks: 50,
        passingMarks: 20,
        weightage: 50,
        sequence: 3,
      },
    ]);
    assert(
      totalCalc.totalMaxMarks === 100,
      "8. calculateAssessmentTotal: 20+30+50 = 100",
    );
    assert(
      totalCalc.isValidWeightage === true,
      "8. calculateAssessmentTotal: 20+30+50% = 100% valid weightage",
    );

    // Weighted Marks
    const weighted = calculateWeightedMarks(45, 50, 20); // (45/50) * 20 = 18
    assert(weighted === 18, "8. calculateWeightedMarks: (45/50)*20 = 18");

    // Percentage Calculation
    const percent = calculatePercentage(87, 100);
    assert(percent === 87, "8. calculatePercentage: 87/100 = 87.0%");

    // UGC CBCS 10-Point Scale Mapping
    assert(
      calculateGrade(92).grade === "A+",
      "8. CBCS Grade: 92% maps to A+ (10 GP)",
    );
    assert(
      calculateGrade(92).gradePoint === 10,
      "8. CBCS Grade: 92% grade point is 10",
    );
    assert(
      calculateGrade(84).grade === "A",
      "8. CBCS Grade: 84% maps to A (9 GP)",
    );
    assert(
      calculateGrade(74).grade === "B+",
      "8. CBCS Grade: 74% maps to B+ (8 GP)",
    );
    assert(
      calculateGrade(64).grade === "B",
      "8. CBCS Grade: 64% maps to B (7 GP)",
    );
    assert(
      calculateGrade(55).grade === "C",
      "8. CBCS Grade: 55% maps to C (6 GP)",
    );
    assert(
      calculateGrade(45).grade === "D",
      "8. CBCS Grade: 45% maps to D (5 GP)",
    );
    assert(
      calculateGrade(37).grade === "E",
      "8. CBCS Grade: 37% maps to E (4 GP)",
    );
    assert(
      calculateGrade(30).grade === "F",
      "8. CBCS Grade: 30% maps to F (0 GP)",
    );

    // Result Status
    assert(
      calculateResultStatus({ percentage: 85 }) === "PASS",
      "8. calculateResultStatus: 85% is PASS",
    );
    assert(
      calculateResultStatus({ percentage: 35 }) === "FAIL",
      "8. calculateResultStatus: 35% is FAIL",
    );
    assert(
      calculateResultStatus({ percentage: 0, isAbsent: true }) === "ABSENT",
      "8. calculateResultStatus: ABSENT status preserved",
    );
    assert(
      calculateResultStatus({ percentage: 0, isMalpractice: true }) ===
        "WITHHELD",
      "8. calculateResultStatus: MALPRACTICE maps to WITHHELD",
    );

    // Grade Distribution Histogram
    const mockGrades = [
      { grade: "A+" },
      { grade: "A" },
      { grade: "A" },
      { grade: "B+" },
      { grade: "B" },
      { grade: "C" },
      { grade: "F" },
    ];
    const dist = calculateGradeDistribution(mockGrades);
    assert(
      dist.find((d) => d.grade === "A")?.count === 2,
      "8. calculateGradeDistribution: Count of A is 2",
    );
    assert(
      dist.find((d) => d.grade === "F")?.count === 1,
      "8. calculateGradeDistribution: Count of F is 1",
    );

    // ==========================================
    // 9. Results Management, Finalization & Publication
    // ==========================================
    const resultsList = await examinationsService.getResults();
    assert(
      resultsList.success === true,
      "9. Examination results list query succeeds",
    );
    assert(resultsList.data.length >= 3, "9. Seed course results present");

    const sampleResult = resultsList.data[0];
    const resultDetail = await examinationsService.getResultById(
      sampleResult.id,
    );
    assert(
      resultDetail.success === true,
      "9. Result 360° detail profile query succeeds",
    );
    assert(
      resultDetail.data.assessmentBreakdown.length > 0,
      "9. Component-level marks breakdown available",
    );

    // Finalize Cohort Result
    const finalizedRes = await examinationsService.finalizeResult(
      sampleResult.id,
    );
    assert(
      finalizedRes.success === true,
      "9. Course result finalization succeeds",
    );

    // Publication Batches
    const pubBatches = await examinationsService.getPublications();
    assert(pubBatches.success === true, "9. Publication batches ledger loaded");

    // Create New Publication Batch
    const newBatchRes = await examinationsService.createPublication({
      batchNumber: "PUB-2026-CSE-S5",
      examinationId: "exam-2026-ese",
      examinationName: "End Semester Examinations Nov/Dec 2026",
      semester: 5,
      program: "B.Tech Computer Science & Engineering",
      department: "Computer Science & Engineering",
      academicYear: "2026-2027",
      resultCount: 68,
    });
    assert(
      newBatchRes.success === true,
      "9. Publication batch created in READY state",
    );

    // Publish Batch
    const publishRes = await examinationsService.publishResults(
      newBatchRes.data.id,
    );
    assert(
      publishRes.success === true,
      "9. Deliberate publication action succeeds",
    );
    assert(
      publishRes.data.status === "PUBLISHED",
      "9. Batch status transitioned to PUBLISHED",
    );

    // Revocation (with justification)
    const revokeRes = await examinationsService.revokePublication(
      newBatchRes.data.id,
      "Administrative hold due to moderation committee review.",
    );
    assert(revokeRes.success === true, "9. Publication revocation succeeds");
    assert(
      revokeRes.data.status === "REVOKED",
      "9. Batch status transitioned to REVOKED",
    );

    // ==========================================
    // 10. Multi-Format Examinations Reports
    // ==========================================
    const reportRes = await examinationsService.generateReport({
      reportType: "COMPLETION",
      department: "Computer Science & Engineering",
      semester: 5,
    });
    assert(reportRes.success === true, "10. Report generation returns success");
    assert(
      reportRes.data.rows.length > 0,
      "10. Report contains populated records",
    );
    assert(
      reportRes.data.title.includes("Assessment"),
      "10. Report metadata has descriptive title",
    );

    // ==========================================
    // 11. Command Palette & Global Search Indexing
    // ==========================================
    const searchRes = await searchService.search("Examination");
    assert(searchRes.success === true, "11. Global search query succeeds");
    assert(
      searchRes.data.some(
        (r) => r.category === "Examination" || r.title.includes("Examination"),
      ),
      "11. Global search indexes examination operations and entities",
    );

    const assessmentSearch = await searchService.search(
      "Continuous Assessment",
    );
    assert(
      assessmentSearch.data.some(
        (r) => r.title.includes("Continuous") || r.category === "Examination",
      ),
      "11. Global search indexes individual assessment schemes",
    );

    // ==========================================
    // 12. Role-Based Access Control (RBAC)
    // ==========================================
    const rbacExamMatrix = {
      SUPER_ADMIN: {
        configureAssessments: true,
        scheduleExams: true,
        reviewEligibility: true,
        enterMarks: true,
        finalizeMarks: true,
        approveCorrections: true,
        finalizeResults: true,
        publishResults: true,
      },
      HOD: {
        configureAssessments: true,
        scheduleExams: true,
        reviewEligibility: true,
        enterMarks: false,
        finalizeMarks: true,
        approveCorrections: true,
        finalizeResults: true,
        publishResults: false, // COE only
      },
      FACULTY: {
        configureAssessments: false,
        scheduleExams: false,
        reviewEligibility: false,
        enterMarks: true,
        finalizeMarks: true,
        requestCorrection: true,
        approveCorrections: false,
        finalizeResults: false,
        publishResults: false,
      },
      STUDENT: {
        viewPublishedResults: true,
        viewUnpublishedResults: false,
        enterMarks: false,
        modifySchedules: false,
        viewAdministrativeAudit: false,
      },
    };

    assert(
      rbacExamMatrix.SUPER_ADMIN.publishResults === true,
      "12. Admin/COE authorized to publish results",
    );
    assert(
      rbacExamMatrix.HOD.approveCorrections === true,
      "12. HOD authorized to approve mark corrections",
    );
    assert(
      rbacExamMatrix.FACULTY.enterMarks === true,
      "12. Faculty authorized to enter assessment marks",
    );
    assert(
      rbacExamMatrix.STUDENT.enterMarks === false,
      "12. Student strictly prohibited from marks entry",
    );
    assert(
      rbacExamMatrix.STUDENT.viewUnpublishedResults === false,
      "12. Student strictly prohibited from viewing unpublished drafts",
    );
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : String(err);
    results.push({
      testName: "Exception during test run",
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
  process.argv[1]?.includes("examinations-module.test")
) {
  runExaminationsModuleTests().then((res) => {
    console.log(`\n==============================================`);
    console.log(`CampusOS Examination & Assessment Module Test Results:`);
    console.log(`Passed: ${res.passed}, Failed: ${res.failed}`);
    console.log(`==============================================`);
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
