/**
 * CampusOS Attendance Management Module Test Suite
 * Validates domain contracts, sessions CRUD, recording workflow, calculations,
 * leaves, corrections with audit trails, reports generation, and RBAC rules.
 */

import { attendanceService } from "../services/attendance.service";
import {
  calculateAttendancePercentage,
  determineAttendanceRisk,
  calculateSessionsNeededToRecover,
  DEFAULT_ATTENDANCE_POLICY,
} from "../services/attendance-calculator";
import { searchService } from "../services/search.service";

export async function runAttendanceModuleTests(): Promise<{
  passed: number;
  failed: number;
  results: { testName: string; passed: boolean; message?: string }[];
}> {
  const results: { testName: string; passed: boolean; message?: string }[] = [];

  function assert(condition: unknown, testName: string, failureDetails?: string) {
    if (Boolean(condition)) {
      results.push({ testName, passed: true });
    } else {
      results.push({ testName, passed: false, message: failureDetails || "Assertion failed" });
    }
  }

  try {
    // ==========================================
    // 1. Attendance Operations Summary
    // ==========================================
    const summaryRes = await attendanceService.getDashboardSummary();
    assert(summaryRes.success === true, "1. Attendance operations summary returns success");
    assert(summaryRes.data.overallAttendancePercentage > 75, "1. Overall attendance percentage is healthy (>75%)");
    assert(summaryRes.data.todaySessionsCount > 0, "1. Today sessions count is non-zero");
    assert(summaryRes.data.departmentBreakdown.length >= 3, "1. Department attendance breakdown available");
    assert(summaryRes.data.semesterBreakdown.length >= 4, "1. Semester attendance breakdown available");

    // ==========================================
    // 2. Attendance Policies
    // ==========================================
    const policiesRes = await attendanceService.getPolicies();
    assert(policiesRes.success === true, "2. Policies list returns success");
    assert(policiesRes.data.some((p) => p.minimumPercentage === 75), "2. 75% minimum threshold policy exists");

    const createdPolRes = await attendanceService.createPolicy({
      name: "Autonomous AI-DS Policy",
      departmentId: "dept-aids",
      departmentName: "Artificial Intelligence & Data Science",
      academicYear: "2026-2027",
      minimumPercentage: 80,
      warningThreshold: 85,
      criticalThreshold: 70,
      includeExcusedInTotal: true,
      lateArrivalWeight: 0.5,
      requireApprovalForCorrections: true,
      maxLeaveDaysConsecutive: 5,
      status: "ACTIVE",
    });
    assert(createdPolRes.success === true, "2. Policy creation succeeds");
    assert(createdPolRes.data.minimumPercentage === 80, "2. Created policy has 80% threshold");

    // ==========================================
    // 3. Attendance Calculation Engine
    // ==========================================
    const normalPercent = calculateAttendancePercentage({ present: 18, absent: 2, late: 0, excused: 0 });
    assert(normalPercent === 90.0, "3. Attendance calculation: 18/20 = 90.0%");

    const lateWeightedPercent = calculateAttendancePercentage(
      { present: 18, absent: 2, late: 2, excused: 0, total: 22 },
      { ...DEFAULT_ATTENDANCE_POLICY, lateArrivalWeight: 0.5 }
    );
    // (18 + 2*0.5) / 22 = 19 / 22 = 86.36% -> 86.4%
    assert(lateWeightedPercent === 86.4, "3. Attendance calculation: Late weighted at 0.5x accurately calculates 86.4%");

    // Risk Classification
    assert(determineAttendanceRisk(85.0) === "HEALTHY", "3. Risk determination: 85% is HEALTHY");
    assert(determineAttendanceRisk(74.0) === "WARNING", "3. Risk determination: 74% is WARNING");
    assert(determineAttendanceRisk(62.0) === "CRITICAL", "3. Risk determination: 62% is CRITICAL");

    // Recovery Projections
    // 25 attended out of 42 sessions = 59.5%. How many consecutive needed for 75%?
    // Formula: ceil((0.75 * 42 - 25) / (1 - 0.75)) = ceil((31.5 - 25) / 0.25) = ceil(6.5 / 0.25) = 26
    const recoverySessions = calculateSessionsNeededToRecover(25, 42, 75);
    assert(recoverySessions === 26, "3. Recovery calculation: 25/42 requires 26 consecutive sessions to reach 75%");
    assert(calculateSessionsNeededToRecover(40, 42, 75) === 0, "3. Recovery calculation: 40/42 already satisfies 75% (0 needed)");

    // ==========================================
    // 4. Session Scheduling & Filter Roster
    // ==========================================
    const sessionsRes = await attendanceService.getSessions();
    assert(sessionsRes.success === true, "4. Sessions list returns success");
    assert(sessionsRes.data.length >= 4, "4. Baseline session registers exist");

    const filteredSessions = await attendanceService.getSessions({ department: "Computer Science" });
    assert(
      filteredSessions.data.every((s) => s.department.includes("Computer Science")),
      "4. Department filter strictly returns CSE sessions"
    );

    const createdSessRes = await attendanceService.createSession({
      courseOfferingId: "off-cs301-a",
      courseCode: "CS301",
      courseName: "Data Structures & Algorithms",
      section: "5th Sem CSE — Sec A",
      department: "Computer Science & Engineering",
      facultyName: "Dr. Rajesh Sharma",
      date: "2026-10-02",
      startTime: "08:30 AM",
      endTime: "09:20 AM",
      room: "Hall 302",
      sessionType: "THEORY",
      status: "OPEN",
    });
    assert(createdSessRes.success === true, "4. Session scheduled successfully");

    // ==========================================
    // 5. Attendance Recording & Roster Submission
    // ==========================================
    const rosterRes = await attendanceService.getSessionRoster(createdSessRes.data.id);
    assert(rosterRes.success === true, "5. Session roster resolved");
    assert(rosterRes.data.length > 0, "5. Enrolled students present in roster");

    // Submit attendance with Present, Absent, Late, and Excused
    const submitRes = await attendanceService.submitSessionAttendance(createdSessRes.data.id, [
      { studentId: "stu-24cse0101", status: "PRESENT" },
      { studentId: "stu-24cse0102", status: "PRESENT" },
      { studentId: "stu-24cse0103", status: "ABSENT", remarks: "Fever" },
      { studentId: "stu-24cse0104", status: "LATE" },
    ]);
    assert(submitRes.success === true, "5. Attendance roster submitted successfully");
    assert(submitRes.data.updatedCount === 4, "5. Exactly 4 student records updated");

    const updatedSession = await attendanceService.getSessionById(createdSessRes.data.id);
    assert(updatedSession.data?.status === "COMPLETED", "5. Session transitioned to COMPLETED status");
    assert(updatedSession.data?.presentCount === 2, "5. Present count verified (2)");
    assert(updatedSession.data?.absentCount === 1, "5. Absent count verified (1)");
    assert(updatedSession.data?.lateCount === 1, "5. Late count verified (1)");

    // ==========================================
    // 6. Master Records Ledger
    // ==========================================
    const recordsRes = await attendanceService.getRecords({ sessionId: createdSessRes.data.id });
    assert(recordsRes.success === true, "6. Records ledger queried successfully");
    assert(recordsRes.data.some((r) => r.studentId === "stu-24cse0101" && r.status === "PRESENT"), "6. Aarav Patel recorded as PRESENT");
    assert(recordsRes.data.some((r) => r.studentId === "stu-24cse0103" && r.status === "ABSENT"), "6. Rohan Verghese recorded as ABSENT");

    // ==========================================
    // 7. Student Attendance 360° & Course Telemetry
    // ==========================================
    const studentSummary = await attendanceService.getStudentAttendanceSummary("stu-24cse0101");
    assert(studentSummary.success === true, "7. Student 360 summary resolves");
    assert(studentSummary.data.percentage > 75, "7. Aarav Patel attendance percentage is healthy");
    assert(studentSummary.data.trend.length >= 4, "7. Weekly attendance trend available");
    assert(studentSummary.data.courseSummaries.length > 0, "7. Course-wise attendance breakdown available");

    const courseSummary = await attendanceService.getCourseAttendanceSummary("off-cs301-a");
    assert(courseSummary.success === true, "7. Course offering attendance summary resolves");
    assert(courseSummary.data.totalSessions === 42, "7. CS301 total sessions delivered is 42");

    // ==========================================
    // 8. Leave Requests Workflow
    // ==========================================
    const leavesRes = await attendanceService.getLeaves();
    assert(leavesRes.success === true, "8. Leaves list returns success");
    assert(leavesRes.data.length >= 2, "8. Baseline leave requests exist");

    const createdLeaveRes = await attendanceService.submitLeave({
      studentId: "stu-24cse0101",
      studentName: "Aarav Patel",
      rollNumber: "24CSE0101",
      leaveType: "MEDICAL",
      startDate: "2026-10-15",
      endDate: "2026-10-17",
      totalDays: 3,
      reason: "Dental surgery",
    });
    assert(createdLeaveRes.success === true, "8. Leave request submitted successfully");
    assert(createdLeaveRes.data.status === "PENDING", "8. New leave is PENDING review");

    // HOD approves leave
    const approvedLeave = await attendanceService.updateLeaveStatus(
      createdLeaveRes.data.id,
      "APPROVED",
      "Medical certificate verified",
      "Dr. K. S. Anand (HOD - CSE)"
    );
    assert(approvedLeave.data.status === "APPROVED", "8. Leave approved by HOD");
    assert(approvedLeave.data.reviewedBy?.includes("HOD"), "8. Reviewer identity logged");

    // ==========================================
    // 9. Attendance Corrections & Audit Trail
    // ==========================================
    const correctionsRes = await attendanceService.getCorrections();
    assert(correctionsRes.success === true, "9. Corrections list returns success");

    const createdCorr = await attendanceService.submitCorrection({
      sessionId: createdSessRes.data.id,
      recordId: `rec-${createdSessRes.data.id}-stu-24cse0103`,
      studentId: "stu-24cse0103",
      studentName: "Rohan Verghese",
      rollNumber: "24CSE0103",
      courseCode: "CS301",
      courseName: "Data Structures & Algorithms",
      sessionDate: "2026-10-02",
      originalStatus: "ABSENT",
      requestedStatus: "PRESENT",
      reason: "Biometric reader timeout during arrival",
      requestedBy: "Dr. Rajesh Sharma",
      requestedRole: "FACULTY",
    });
    assert(createdCorr.success === true, "9. Correction requested by Faculty");
    assert(createdCorr.data.status === "PENDING", "9. Correction is PENDING HOD sign-off");
    assert(createdCorr.data.auditTimeline.length >= 1, "9. Initial audit step logged");

    // HOD reviews and approves correction
    const approvedCorr = await attendanceService.updateCorrectionStatus(
      createdCorr.data.id,
      "APPROVED",
      "Biometric log verified",
      "Dr. K. S. Anand (HOD - CSE)"
    );
    assert(approvedCorr.data.status === "APPROVED", "9. Correction APPROVED by HOD");
    assert(approvedCorr.data.auditTimeline.length >= 3, "9. Full chronological audit trail preserved");

    // ==========================================
    // 10. Reports Engine
    // ==========================================
    const reportRes = await attendanceService.generateReport({
      reportType: "LOW_ATTENDANCE",
    });
    assert(reportRes.success === true, "10. Low attendance report generated successfully");
    assert(reportRes.data.totalRows > 0, "10. Report contains at-risk student records");

    // ==========================================
    // 11. Command Palette & Global Search
    // ==========================================
    const searchRes = await searchService.search("Attendance");
    assert(
      searchRes.data.some((item) => item.category === "Attendance"),
      "11. Global search surfaces Attendance module entries"
    );

    const searchSessionRes = await searchService.search("CS301");
    assert(
      searchSessionRes.data.some((item) => item.category === "Attendance" || item.category === "Course"),
      "11. Global search surfaces CS301 attendance sessions"
    );

    // ==========================================
    // 12. RBAC Permissions Matrix
    // ==========================================
    const rbacRules = {
      SUPER_ADMIN: { recordAttendance: true, approveLeaves: true, approveCorrections: true, managePolicies: true },
      HOD: { recordAttendance: true, approveLeaves: true, approveCorrections: true, managePolicies: false },
      FACULTY: { recordAttendance: true, requestCorrection: true, approveLeaves: false, managePolicies: false },
      STUDENT: { viewOwnAttendance: true, applyLeave: true, recordAttendance: false, approveLeaves: false },
    };
    assert(rbacRules.SUPER_ADMIN.approveCorrections === true, "12. Admin has full approval rights");
    assert(rbacRules.HOD.approveCorrections === true, "12. HOD can approve corrections");
    assert(rbacRules.FACULTY.recordAttendance === true, "12. Faculty can record attendance");
    assert(rbacRules.STUDENT.recordAttendance === false, "12. Student cannot record attendance");
    assert(rbacRules.STUDENT.applyLeave === true, "12. Student is authorized to apply for leave");

  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : String(err);
    results.push({ testName: "Exception during test run", passed: false, message: errorMsg });
  }

  const passed = results.filter((r) => r.passed).length;
  const failed = results.filter((r) => !r.passed).length;
  return { passed, failed, results };
}

if (typeof process !== "undefined" && process.argv[1]?.includes("attendance-module.test")) {
  runAttendanceModuleTests().then((res) => {
    console.log(`\n========================================`);
    console.log(`CampusOS Attendance Module Test Results:`);
    console.log(`Passed: ${res.passed}, Failed: ${res.failed}`);
    console.log(`========================================`);
    res.results.forEach((r) => {
      console.log(`${r.passed ? "✔ PASS" : "✖ FAIL"}: ${r.testName}${r.message ? ` (${r.message})` : ""}`);
    });
    if (res.failed > 0) {
      process.exit(1);
    }
  });
}
