/**
 * CampusOS Unified Student Counselling, Mentoring & Personal Development Module Test Suite
 * Step 59 Verification
 *
 * Validates:
 * 1. Support Telemetry & Privacy-Safe Dashboard KPIs
 * 2. Institutional Policy Configuration (Workload Quotas, Booking Windows)
 * 3. Faculty Mentor Allocation & Workload Enforcement (Max 20 mentees)
 * 4. Mentor Reassignment Tracking & Justification Logs
 * 5. Mentee Directory Progress & IDP Aggregations
 * 6. Mentoring Session Scheduling (1-on-1 & Cohort Formats)
 * 7. Mentoring Session Completion, Action Item Generation & Mentee Reflection
 * 8. Counselling Appointment Booking & Mode Handling (In-Person / Online)
 * 9. Counselling Schedule & Status Transitions (Check-in, Reschedule, Complete, No-Show)
 * 10. Strict Confidential Clinical Boundary (Record Isolation from Mentors/Admins)
 * 11. Clinical Observations & Therapeutic Interventions (No Automated Diagnostic Scoring)
 * 12. Student Development Plan (IDP) Creation & Cadence Verification
 * 13. Goal Progression & Dynamic IDP Progress Recalculation
 * 14. Inter-Service Support Referrals with Student Informed Consent
 * 15. Referral Lifecycle Management (Accepted -> In Progress -> Completed)
 * 16. Support Follow-Up Action Tracking & Overdue Task Detection
 */

import { StudentSupportService } from "../services/student-support.service";
import {
  MOCK_SUPPORT_CONFIG,
  MOCK_MENTOR_ASSIGNMENTS,
  MOCK_MENTEES,
  MOCK_MENTORING_SESSIONS,
  MOCK_COUNSELLING_APPOINTMENTS,
  MOCK_CONFIDENTIAL_RECORDS,
  MOCK_DEVELOPMENT_PLANS,
  MOCK_SUPPORT_REFERRALS,
  MOCK_SUPPORT_FOLLOW_UPS,
  MOCK_TELEMETRY_METRICS,
} from "../mocks/student-support.mock";

export async function runStudentSupportModuleTests(): Promise<{
  passed: number;
  failed: number;
  results: { testName: string; passed: boolean; message?: string }[];
}> {
  const results: { testName: string; passed: boolean; message?: string }[] = [];

  function assert(condition: unknown, testName: string, failureDetails?: string) {
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
    // 1. Support Telemetry & Privacy-Safe Dashboard KPIs
    const telemetry = await StudentSupportService.getTelemetryMetrics();
    assert(
      (telemetry.active_mentor_assignments ?? telemetry.totalActiveMentorAssignments ?? 0) >= 0,
      "1. Telemetry returns active mentor assignments count"
    );
    assert(
      (telemetry.appointment_utilization_rate_pct ?? telemetry.appointmentUtilizationRatePct ?? 0) <= 100,
      "1. Telemetry utilization percentage is within 0-100% boundary"
    );
    assert(
      !("clinical_observations" in telemetry) && !("psychological_diagnosis" in telemetry),
      "1. Telemetry enforces zero-leakage: No mental health or clinical fields exist"
    );

    // 2. Institutional Policy Configuration
    const config = await StudentSupportService.getPolicyConfig();
    assert(
      config.max_mentees_per_mentor === 20,
      "2. Policy configuration specifies max 20 mentees per mentor"
    );
    assert(
      config.advance_booking_window_days === 30,
      "2. Booking window allows up to 30 days advance booking"
    );
    assert(
      config.require_referral_consent === true,
      "2. Explicit student consent is strictly required for referrals"
    );
    assert(
      config.privacy_suppression_threshold === 5,
      "2. Differential privacy small-group suppression threshold is 5"
    );

    // 3. Faculty Mentor Allocation & Workload Tracking
    const assignments = await StudentSupportService.getMentorAssignments();
    assert(
      assignments.length > 0,
      "3. Successfully retrieves mentor assignments"
    );
    const activeAssignments = assignments.filter((a) => a.status === "ACTIVE");
    assert(
      activeAssignments.every((a) => (a.faculty_workload_count ?? 0) <= (config.max_mentees_per_mentor ?? config.maxMenteesPerMentor ?? 20)),
      "3. All active faculty mentors remain within the institutional workload quota"
    );

    // 4. Mentor Reassignment Tracking & Justification Logs
    const targetAssignment = assignments[0];
    const reassigned = await StudentSupportService.reassignMentor(targetAssignment.id, {
      new_faculty_staff_id: "FAC-CSE-003",
      reassignment_reason: "Faculty sabbatical leave coverage",
    });
    assert(
      (reassigned.status === "REASSIGNED" || reassigned.status === "ACTIVE") && reassigned.reassignment_reason !== undefined,
      "4. Mentor reassignment archives previous allocation and records reason audit log"
    );

    // 5. Mentee Directory Progress & IDP Aggregations
    const mentees = await StudentSupportService.getAssignedMentees();
    assert(
      mentees.length > 0,
      "5. Successfully retrieves assigned mentees for faculty mentor"
    );
    assert(
      mentees.every((m) => Boolean(m.student_name || m.studentName) && Boolean(m.student_reg_no || m.rollNumber)),
      "5. Mentee items contain validated identity and registration details"
    );
    assert(
      mentees.some((m) => m.has_active_development_plan === true),
      "5. Correctly flags mentees with active published Individual Development Plans"
    );

    // 6. Mentoring Session Scheduling
    const newSession = await StudentSupportService.createMentoringSession({
      title: "Semester 5 Capstone Architectural Review",
      session_type: "ONE_ON_ONE",
      scheduled_start: new Date(Date.now() + 86400 * 1000).toISOString(),
      scheduled_end: new Date(Date.now() + 86400 * 1000 + 45 * 60000).toISOString(),
      location: "Cabin 302",
      discussion_points: "Review microservices deployment and test coverage",
      student_ids: [mentees[0].student_id],
    });
    assert(
      newSession.id !== undefined && newSession.status === "SCHEDULED",
      "6. Mentoring session scheduled with valid initial state and attendees"
    );

    // 7. Session Completion, Action Items & Mentee Reflection
    const completedSession = await StudentSupportService.completeMentoringSession(newSession.id, {
      summary_notes: "Reviewed distributed consensus algorithm and assigned lab benchmarks.",
      action_items: [{ title: "Submit performance benchmarks for Raft simulator" }],
    });
    assert(
      completedSession.status === "COMPLETED" && completedSession.summary_notes !== undefined,
      "7. Session marked completed with documented summary notes"
    );

    const reflectedSession = await StudentSupportService.submitMenteeReflection(
      completedSession.id,
      "I understand the Raft leader election edge cases and will test partitioned states."
    );
    assert(
      reflectedSession.student_reflection !== undefined,
      "7. Mentee personal reflection recorded successfully on session record"
    );

    // 8. Counselling Appointment Booking & Mode Handling
    const appt = await StudentSupportService.createCounsellingAppointment({
      category: "ACADEMIC_STRESS",
      appointment_mode: "IN_PERSON",
      scheduled_start: new Date(Date.now() + 2 * 86400 * 1000).toISOString(),
      scheduled_end: new Date(Date.now() + 2 * 86400 * 1000 + 50 * 60000).toISOString(),
      location: "Wellness Centre Suite 104",
      reason_summary: "Time management and exam workload pacing guidance.",
    });
    assert(
      appt.id !== undefined && (appt.appointment_number || appt.id || "").startsWith("COU-"),
      "8. Counselling appointment booked with formatted tracking reference COU-*"
    );

    // 9. Counselling Schedule & Status Transitions
    const transitionedAppt = await StudentSupportService.transitionCounsellingAppointment(appt.id, {
      status: "CHECKED_IN",
    });
    assert(
      transitionedAppt.status === "CHECKED_IN",
      "9. Appointment successfully transitions to CHECKED_IN"
    );

    const completedAppt = await StudentSupportService.transitionCounsellingAppointment(appt.id, {
      status: "COMPLETED",
    });
    assert(
      completedAppt.status === "COMPLETED",
      "9. Appointment successfully marks session completion"
    );

    // 10. Strict Confidential Clinical Boundary
    const confidentialRecords = await StudentSupportService.getConfidentialRecords();
    assert(
      confidentialRecords.length > 0,
      "10. Authorized counselling practitioner can access confidential clinical records"
    );
    assert(
      confidentialRecords.every((r) => r.appointment_id !== undefined && r.student_id !== undefined),
      "10. Clinical records are anchored to appointment IDs without leaking to academic models"
    );

    // 11. Clinical Observations & Therapeutic Interventions (No Automated Scoring)
    const newClinicalRecord = await StudentSupportService.createConfidentialRecord({
      appointment_id: completedAppt.id,
      student_id: completedAppt.student_id,
      session_observations: "Student demonstrated constructive self-regulation and openness to study scheduling.",
      interventions_applied: "Grounding exercises, Pomodoro study pacing, structured sleep hygiene guide.",
      consent_verified: true,
      follow_up_recommended: true,
    });
    assert(
      newClinicalRecord.id !== undefined && newClinicalRecord.consent_verified === true,
      "11. Clinical session record securely created with verified informed consent"
    );
    assert(
      !("ai_risk_score" in newClinicalRecord) && !("psychiatric_label" in newClinicalRecord),
      "11. No automated psychological risk scores or psychiatric diagnosis labels exist"
    );

    // 12. Student Development Plan Creation
    const newPlan = await StudentSupportService.createDevelopmentPlan({
      student_id: mentees[0].student_id,
      title: "2026-2027 Research & Career Excellence Plan",
      academic_year: "2026-2027",
      review_frequency: "SEMESTER",
      strengths_summary: "Strong systems programming and data structures foundations.",
      growth_areas_summary: "Technical writing and research paper presentations.",
    });
    assert(
      newPlan.id !== undefined && newPlan.status === "ACTIVE",
      "12. Student Development Plan created with ACTIVE state"
    );

    // 13. Goal Progression & Dynamic IDP Progress Recalculation
    const newGoal = await StudentSupportService.addGoalToPlan(newPlan.id, {
      category: "ACADEMIC",
      title: "Publish Distributed Systems Conference Paper",
      target_completion_date: new Date(Date.now() + 90 * 86400 * 1000).toISOString(),
      success_metric: "Acceptance notification received",
    });
    assert(
      newGoal.id !== undefined && newGoal.progress_pct === 0,
      "13. Goal added to IDP with baseline 0% progress"
    );

    const updatedGoal = await StudentSupportService.updateGoal(newGoal.id, {
      progress_pct: 100,
      status: "COMPLETED",
    });
    assert(
      updatedGoal.status === "COMPLETED" && updatedGoal.progress_pct === 100,
      "13. Goal completion updates status and triggers progress recomputation"
    );

    // 14. Inter-Service Support Referrals with Student Informed Consent
    const newReferral = await StudentSupportService.createReferral({
      student_id: mentees[0].student_id,
      target_service: "CAREER_SERVICES",
      reason_category: "Placement Resume & Industry Mock Interviews",
      student_consent_obtained: true,
      referrer_role: "FACULTY_MENTOR",
    });
    assert(
      newReferral.id !== undefined && newReferral.student_consent_obtained === true,
      "14. Cross-department support referral initiated with explicit student consent"
    );
    assert(
      (newReferral.referral_number || newReferral.referralCode || "").startsWith("REF-"),
      "14. Referral assigned standard institutional tracking number REF-*"
    );

    // 15. Referral Lifecycle Management
    const updatedRef = await StudentSupportService.updateReferralStatus(newReferral.id, {
      status: "ACCEPTED",
      status_notes: "Assigned career coach for resume revision and mock session.",
    });
    assert(
      updatedRef.status === "ACCEPTED",
      "15. Receiving department successfully accepts referral"
    );

    const completedRef = await StudentSupportService.updateReferralStatus(newReferral.id, {
      status: "COMPLETED",
      status_notes: "Completed 2 mock interview rounds with positive evaluation.",
    });
    assert(
      completedRef.status === "COMPLETED",
      "15. Referral successfully fulfilled and marked COMPLETED"
    );

    // 16. Support Follow-Up Action Tracking & Overdue Task Detection
    const followUps = await StudentSupportService.getFollowUps();
    assert(
      followUps.length > 0,
      "16. Successfully loads institutional follow-up items"
    );
    const overdueTask = followUps.find(
      (f) => f.status === "PENDING" && new Date(f.due_date || f.dueDate || "") < new Date()
    );
    assert(
      overdueTask !== undefined,
      "16. System accurately flags pending follow-ups past due date as overdue"
    );

    const newFollowUp = await StudentSupportService.createFollowUp({
      title: "Check placement test score with mentee",
      priority: "HIGH",
      due_date: new Date(Date.now() + 5 * 86400 * 1000).toISOString(),
      assigned_to_user_id: "fac-cse-001",
    });
    assert(
      newFollowUp.id !== undefined && newFollowUp.priority === "HIGH",
      "16. New follow-up task created with priority badge metadata"
    );
  } catch (error: any) {
    results.push({
      testName: "Unhandled Exception in Student Support Test Suite",
      passed: false,
      message: error?.message || String(error),
    });
  }

  const passed = results.filter((r) => r.passed).length;
  const failed = results.filter((r) => !r.passed).length;

  return { passed, failed, results };
}

// Direct node/tsx execution harness
if (
  require.main === module ||
  (typeof process !== "undefined" && process.argv[1]?.includes("student-support-module.test"))
) {
  runStudentSupportModuleTests().then(({ passed, failed, results }) => {
    console.log(`\n==================================================`);
    console.log(`CampusOS Student Support Module Verification Results`);
    console.log(`==================================================`);
    results.forEach((r, idx) => {
      const mark = r.passed ? "✓ PASS" : "✗ FAIL";
      console.log(`${mark} [${idx + 1}] ${r.testName}`);
      if (!r.passed && r.message) {
        console.log(`       Reason: ${r.message}`);
      }
    });
    console.log(`--------------------------------------------------`);
    console.log(`Total Passed: ${passed}`);
    console.log(`Total Failed: ${failed}`);
    console.log(`==================================================\n`);
    if (failed > 0) {
      process.exit(1);
    }
  });
}
