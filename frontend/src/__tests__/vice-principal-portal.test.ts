/**
 * CampusOS Vice Principal Portal — Comprehensive Verification Test Suite
 *
 * Validates the 10 Core Modules and Institutional Oversight Capabilities:
 * 1. Vice Principal Persona, Authentication & RBAC Isolation.
 * 2. Feature A: Institutional Overview Dashboard & KPIs.
 * 3. Feature B: Department Supervision & Comparative Matrix.
 * 4. Feature C: Academic Calendar & Syllabus Velocity Radar.
 * 5. Feature D: Faculty Workload Oversight (AICTE 12-18 hrs compliance).
 * 6. Feature E: Student Monitoring & Low Attendance Radar (<75%).
 * 7. Feature F: Statutory Approval Workflows & State Transitions (8+ Categories).
 * 8. Feature G: Examinations Oversight & CIA Lockout Monitoring.
 * 9. Feature H: Institutional Compliance Reports & Multi-format Export.
 * 10. Feature I: Executive Circular Dispatch & Multi-Audience Broadcasting.
 * 11. Feature J: Immutable Read-Only Institutional Audit Trail.
 */

import { vicePrincipalService } from "../services/vice-principal.service";
import { DEMO_PERSONAS } from "../mocks/auth.mock";
import { VICE_PRINCIPAL_PORTAL_NAV } from "../components/navigation/portal-nav";
import { isPathAuthorized } from "../components/navigation/sidebar";

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

async function runTests() {
  console.log(
    "\n================================================================================",
  );
  console.log("CampusOS Vice Principal Portal — Full Verification Test Suite");
  console.log(
    "================================================================================\n",
  );

  // ---------------------------------------------------------------------------
  // 1. Executive Persona, Role Mapping & RBAC
  // ---------------------------------------------------------------------------
  console.log("--- 1. Persona & Role Authorization ---");
  const vp = DEMO_PERSONAS.find(
    (p) => p.id === "user-vice-principal-01" || p.role === "VICE_PRINCIPAL",
  );
  assert(Boolean(vp), "Vice Principal persona exists in DEMO_PERSONAS");
  assert(
    vp?.email === "vp.academics@campusos.edu",
    "Vice Principal email matches vp.academics@campusos.edu",
  );
  assert(
    vp?.role === "VICE_PRINCIPAL" || vp?.role === "PRINCIPAL",
    "Vice Principal role is VICE_PRINCIPAL or PRINCIPAL",
  );
  assert(
    Boolean(vp?.permissions.includes("approvals:read")),
    "Vice Principal has approvals:read permission",
  );
  assert(
    Boolean(vp?.permissions.includes("approvals:approve")),
    "Vice Principal has approvals:approve permission",
  );
  assert(
    Boolean(vp?.permissions.includes("approvals:reject")),
    "Vice Principal has approvals:reject permission",
  );
  assert(
    Boolean(vp?.permissions.includes("academics:calendar:read")),
    "Vice Principal has academics:calendar:read permission",
  );
  assert(
    Boolean(vp?.permissions.includes("timetable:read")),
    "Vice Principal has timetable:read permission",
  );
  assert(
    Boolean(vp?.permissions.includes("leave:approve")),
    "Vice Principal has leave:approve permission",
  );
  assert(
    Boolean(vp?.permissions.includes("reports:institutional:read")),
    "Vice Principal has reports:institutional:read permission",
  );

  // Strict Scoping: Vice Principal does NOT have direct user management or financial execution
  assert(
    !vp?.permissions.includes("users:create"),
    "Vice Principal cannot directly create system users (Admin scope)",
  );
  assert(
    !vp?.permissions.includes("users:delete"),
    "Vice Principal cannot directly delete system users (Admin scope)",
  );
  assert(
    !vp?.permissions.includes("finance:payments:process"),
    "Vice Principal cannot execute raw payment disbursements (Accounts scope)",
  );
  assert(
    !vp?.permissions.includes("iam:system:configure"),
    "Vice Principal cannot reconfigure core IAM parameters (Super Admin scope)",
  );

  // Dedicated Route Authorization
  const vpUser: any = {
    id: "user-vice-principal-01",
    email: "vp.academics@campusos.edu",
    roles: [
      { id: "r-vp", name: "VICE_PRINCIPAL", display_name: "Vice Principal" },
    ],
  };
  assert(
    isPathAuthorized("/vice-principal/dashboard", vpUser),
    "Route /vice-principal/dashboard is authorized for Vice Principal",
  );
  assert(
    isPathAuthorized("/vice-principal/departments", vpUser),
    "Route /vice-principal/departments is authorized for Vice Principal",
  );
  assert(
    isPathAuthorized("/vice-principal/academics", vpUser),
    "Route /vice-principal/academics is authorized for Vice Principal",
  );
  assert(
    isPathAuthorized("/vice-principal/faculty", vpUser),
    "Route /vice-principal/faculty is authorized for Vice Principal",
  );
  assert(
    isPathAuthorized("/vice-principal/students", vpUser),
    "Route /vice-principal/students is authorized for Vice Principal",
  );
  assert(
    isPathAuthorized("/vice-principal/approvals", vpUser),
    "Route /vice-principal/approvals is authorized for Vice Principal",
  );
  assert(
    isPathAuthorized("/vice-principal/examinations", vpUser),
    "Route /vice-principal/examinations is authorized for Vice Principal",
  );
  assert(
    isPathAuthorized("/vice-principal/reports", vpUser),
    "Route /vice-principal/reports is authorized for Vice Principal",
  );
  assert(
    isPathAuthorized("/vice-principal/announcements", vpUser),
    "Route /vice-principal/announcements is authorized for Vice Principal",
  );
  assert(
    isPathAuthorized("/vice-principal/audit", vpUser),
    "Route /vice-principal/audit is authorized for Vice Principal",
  );

  // ---------------------------------------------------------------------------
  // 2. Feature A: Institutional Overview Dashboard
  // ---------------------------------------------------------------------------
  console.log("\n--- 2. Institutional Overview Dashboard (Feature A) ---");
  const dashRes = await vicePrincipalService.getDashboard();
  assert(dashRes.success === true, "Dashboard endpoint returns success: true");
  assert(
    dashRes.data?.kpis?.total_departments === 5,
    "Dashboard KPI reflects 5 institutional departments",
  );
  assert(
    (dashRes.data?.kpis?.total_students || 0) > 2000,
    "Dashboard KPI reflects complete student body (>2000 students)",
  );
  assert(
    (dashRes.data?.kpis?.total_faculty || 0) > 100,
    "Dashboard KPI reflects complete faculty body (>100 faculty)",
  );
  assert(
    (dashRes.data?.kpis?.overall_student_attendance || 0) >= 75.0,
    "Institutional average student attendance is tracked (>=75%)",
  );
  assert(
    (dashRes.data?.kpis?.syllabus_completion_rate || 0) > 70.0,
    "Institutional syllabus completion tracking rate is healthy (>70%)",
  );
  assert(
    (dashRes.data?.kpis?.pending_approvals_count || 0) > 0,
    "Pending approvals counter accurately surfaces awaiting governance requests",
  );
  assert(
    dashRes.data?.department_metrics?.length === 5,
    "Department health matrix includes all 5 departments",
  );

  // ---------------------------------------------------------------------------
  // 3. Feature B: Department Supervision & Comparisons
  // ---------------------------------------------------------------------------
  console.log("\n--- 3. Department Supervision (Feature B) ---");
  const deptsRes = await vicePrincipalService.getDepartments();
  assert(
    deptsRes.success === true,
    "Departments monitoring endpoint returns success",
  );
  assert(
    deptsRes.data.length === 5,
    "Monitors all 5 academic engineering departments",
  );
  const cseDept = deptsRes.data.find((d) => d.code === "CSE");
  assert(Boolean(cseDept), "CSE Department is present in supervision matrix");
  assert(
    Boolean(cseDept?.hod_name && cseDept?.hod_email),
    "HOD name and institutional contact email are surfaced",
  );
  assert(
    Boolean(cseDept?.student_count && cseDept?.faculty_count),
    "Student strength and faculty headcount are reported",
  );
  assert(
    Boolean(cseDept?.faculty_ratio),
    "AICTE faculty-to-student statutory ratio is calculated (e.g. 1:20)",
  );

  // ---------------------------------------------------------------------------
  // 4. Feature C: Academic Calendar & Syllabus Velocity
  // ---------------------------------------------------------------------------
  console.log("\n--- 4. Academic Calendar & Syllabus Velocity (Feature C) ---");
  const acadRes = await vicePrincipalService.getAcademicsMonitoring();
  assert(
    acadRes.success === true,
    "Academic monitoring endpoint returns success",
  );
  assert(
    acadRes.data.milestones.length >= 4,
    "Institutional academic calendar tracks required milestones",
  );
  const cia1 = acadRes.data.milestones.find((m) => m.event.includes("CIA 1"));
  assert(
    Boolean(cia1 && cia1.status === "COMPLETED"),
    "CIA 1 assessment status is COMPLETED",
  );
  assert(
    acadRes.data.syllabus_delay_tracking.length > 0,
    "Syllabus Delay Radar flags at-risk course modules",
  );
  const delayCourse = acadRes.data.syllabus_delay_tracking[0];
  assert(
    Boolean(delayCourse?.lag_days && delayCourse?.remedial_status),
    "Lag days and mandated remedial action are captured",
  );

  // ---------------------------------------------------------------------------
  // 5. Feature D: Faculty Workload Oversight (AICTE 12-18 hrs)
  // ---------------------------------------------------------------------------
  console.log("\n--- 5. Faculty Workload Oversight (Feature D) ---");
  const facRes = await vicePrincipalService.getFacultySupervision();
  assert(
    facRes.success === true,
    "Faculty supervision endpoint returns success",
  );
  const workload = facRes.data.workload_summary;
  assert(
    workload.statutory_min_hours === 12 && workload.statutory_max_hours === 18,
    "Statutory contact hour limits strictly follow AICTE norms (12-18 hrs/week)",
  );
  assert(
    workload.compliant_workload_count > 0,
    "Surfaces compliant faculty workloads within statutory range",
  );
  const overloaded = facRes.data.faculty.filter(
    (f) => f.status === "OVERLOADED",
  );
  assert(
    overloaded.length > 0,
    "Correctly flags faculty exceeding maximum 18 contact hours/week",
  );

  // ---------------------------------------------------------------------------
  // 6. Feature E: Student Attendance Radar (<75%) & Strength
  // ---------------------------------------------------------------------------
  console.log("\n--- 6. Student Monitoring & Attendance Radar (Feature E) ---");
  const stuRes = await vicePrincipalService.getStudentsSupervision({
    threshold: 75.0,
  });
  assert(
    stuRes.success === true,
    "Student supervision endpoint returns success",
  );
  assert(
    stuRes.data.low_attendance_radar.length > 0,
    "Low attendance radar detects students below 75% threshold",
  );
  const atRiskStudent = stuRes.data.low_attendance_radar[0];
  assert(
    atRiskStudent.attendance_percentage < 75.0,
    "Radar record reflects attendance strictly below 75%",
  );
  assert(
    Boolean(atRiskStudent.shortfall_sessions && atRiskStudent.mentor_name),
    "Shortfall sessions to 75% and faculty mentor are tracked",
  );
  assert(
    stuRes.data.institutional_strength.length === 5,
    "Institutional strength tracks all 5 departments across 4 academic years",
  );

  // ---------------------------------------------------------------------------
  // 7. Feature F: Statutory Approval Workflows (8+ Categories & State Transitions)
  // ---------------------------------------------------------------------------
  console.log("\n--- 7. Statutory Approvals & Workflows (Feature F) ---");
  const apprsRes = await vicePrincipalService.getApprovals();
  assert(apprsRes.success === true, "Approvals queue endpoint returns success");
  const categories = new Set(apprsRes.data.map((a) => a.category));
  assert(
    categories.has("DEPARTMENT_ACADEMIC_REQUEST"),
    "Approval category DEPARTMENT_ACADEMIC_REQUEST supported",
  );
  assert(
    categories.has("ACADEMIC_CALENDAR_CHANGE"),
    "Approval category ACADEMIC_CALENDAR_CHANGE supported",
  );
  assert(
    categories.has("FACULTY_LEAVE"),
    "Approval category FACULTY_LEAVE supported",
  );
  assert(
    categories.has("TIMETABLE_CHANGE"),
    "Approval category TIMETABLE_CHANGE supported",
  );
  assert(
    categories.has("EXAMINATION_REQUEST"),
    "Approval category EXAMINATION_REQUEST supported",
  );
  assert(
    categories.has("ACADEMIC_PERFORMANCE_INTERVENTION"),
    "Approval category ACADEMIC_PERFORMANCE_INTERVENTION supported",
  );

  // Workflow 1: APPROVE action
  const approveRes = await vicePrincipalService.processApprovalAction(
    "appr-vp-001",
    "APPROVE",
    "Approved in compliance with Board of Studies academic guidelines.",
  );
  assert(approveRes.success === true, "Workflow 1: APPROVE returns success");
  assert(
    approveRes.data.status === "APPROVED",
    "Workflow 1: Status transitions to APPROVED",
  );
  assert(
    Boolean(approveRes.data.decided_by && approveRes.data.decision_date),
    "Workflow 1: Decided by and decision timestamp recorded",
  );
  assert(
    approveRes.data.audit_trail.length >= 2,
    "Workflow 1: Audit trail captures full submission and approval steps",
  );

  // Workflow 2: REJECT action
  const rejectRes = await vicePrincipalService.processApprovalAction(
    "appr-vp-002",
    "REJECT",
    "Denied: Proposed dates conflict with University central valuation window.",
  );
  assert(rejectRes.success === true, "Workflow 2: REJECT returns success");
  assert(
    rejectRes.data.status === "REJECTED",
    "Workflow 2: Status transitions to REJECTED",
  );
  assert(
    Boolean(rejectRes.data.remarks?.includes("University central valuation")),
    "Workflow 2: Mandatory rejection reason is persisted",
  );

  // Workflow 3: REQUEST_MODIFICATION action
  const modRes = await vicePrincipalService.processApprovalAction(
    "appr-vp-003",
    "REQUEST_MODIFICATION",
    "Please attach written confirmation from substitute faculty for CS303.",
  );
  assert(
    modRes.success === true,
    "Workflow 3: REQUEST_MODIFICATION returns success",
  );
  assert(
    modRes.data.status === "MODIFICATION_REQUESTED",
    "Workflow 3: Status transitions to MODIFICATION_REQUESTED",
  );

  // ---------------------------------------------------------------------------
  // 8. Feature G: Examinations Oversight & CIA Lockout Monitoring
  // ---------------------------------------------------------------------------
  console.log("\n--- 8. Examinations Oversight (Feature G) ---");
  const examRes = await vicePrincipalService.getExaminationsOversight();
  assert(examRes.success === true, "Examinations oversight returns success");
  assert(
    examRes.data.schedules.length > 0,
    "Examination schedule is monitored",
  );
  assert(
    examRes.data.cia_mark_submissions.length === 5,
    "Continuous Internal Assessment submissions tracked for all 5 departments",
  );
  assert(
    examRes.data.results_analysis.overall_institutional_pass_pct > 90.0,
    "Overall institutional pass rate is tracked (>90%)",
  );
  assert(
    examRes.data.results_analysis.department_pass_ranking.length === 5,
    "Institutional department ranking on pass percentages is compiled",
  );

  // ---------------------------------------------------------------------------
  // 9. Feature H, I, J: Reports, Announcements & Immutable Audit Trail
  // ---------------------------------------------------------------------------
  console.log(
    "\n--- 9. Reports, Announcements & Audit Trail (Features H, I, J) ---",
  );
  const repsRes = await vicePrincipalService.getReports();
  assert(
    repsRes.success === true,
    "Compliance reports endpoint returns success",
  );
  assert(
    repsRes.data.available_reports.length >= 4,
    "At least 4 statutory institutional reports are available",
  );
  assert(
    repsRes.data.available_reports.every((r) => r.format.length > 0),
    "Every report specifies supported export formats (PDF, XLSX, CSV)",
  );

  // Announcement Broadcast
  const ancRes = await vicePrincipalService.createAnnouncement({
    title: "Directive: Mandatory Mid-Semester Audit Preparation",
    target_audience: "ALL_HODS",
    priority: "HIGH",
    summary: "Conduct departmental syllabus reviews before Friday.",
    pinned: true,
  });
  assert(
    ancRes.success === true,
    "Create executive announcement returns success",
  );
  assert(
    ancRes.data.title.includes("Mid-Semester Audit"),
    "Announcement title matches input payload",
  );

  // Immutable Audit Trail
  const audRes = await vicePrincipalService.getAuditTrail();
  assert(audRes.success === true, "Audit trail endpoint returns success");
  assert(
    audRes.data.length > 0,
    "Audit trail contains persistent institutional events",
  );
  const firstLog = audRes.data[0];
  assert(
    Boolean(
      firstLog.actor &&
      firstLog.action &&
      firstLog.entity &&
      firstLog.timestamp,
    ),
    "Audit record contains mandatory WHO, WHAT, WHEN, and AFFECTED ENTITY fields",
  );

  // ---------------------------------------------------------------------------
  // Test Summary
  // ---------------------------------------------------------------------------
  console.log(
    "\n================================================================================",
  );
  console.log(
    `Vice Principal Portal Verification: ${passed} Passed, ${failed} Failed`,
  );
  console.log(
    "================================================================================\n",
  );

  if (failed > 0) {
    process.exit(1);
  }
}

runTests().catch((err) => {
  console.error("Test execution fatal error:", err);
  process.exit(1);
});
