/**
 * CampusOS Enterprise Student Affairs, Grievance Redressal & Disciplinary Module Test Suite
 * Step 58 Verification
 *
 * Validates:
 * 1. Operations Telemetry & Dashboard KPIs
 * 2. Grievance Submission & Sequence Generation (GRV-2026-XXXX)
 * 3. Anonymous Reporting & Submitter Identity Safeguards
 * 4. Case Intake Triage, Priority Override & Officer Routing
 * 5. Conflict of Interest Declaration & Recusal Reassignment
 * 6. Disciplinary Proceedings & Presumption of Good Faith (No Automated AI Guilt)
 * 7. Committee Findings Recording & Procedural Milestones
 * 8. Proportional Sanctions Authorization & Appeal Window Activation
 * 9. Evidence Locker, Access Control Tiers & Redaction Derivative Safeguards
 * 10. Hearing Panel & Voluntary Mediation Scheduling (Recording Consent Guard)
 * 11. Corrective Actions & Multi-Issue Remediation Tracking
 * 12. Strict Separation of Duties on Appeals (Decision-Maker Blocked from Appellate Review)
 * 13. Independent Appellate Determination (Overturned / Relief Granted)
 * 14. Urgent Safeguarding & Anti-Ragging Escalation Triggers
 * 15. Confidential Participant Communications & Internal Committee Notes
 * 16. Pure Business Calculators: SLA Compliance, Appeal Timelines & Badge Styling
 */

import { studentAffairsService } from "../services/student-affairs.service";
import { StudentAffairsCalculator } from "../services/student-affairs-calculator";
import {
  SACaseType,
  SACaseStatus,
  SACasePriority,
  SAConfidentialityLevel,
  SASubmitterType,
  SAFindingStatus,
  SASanctionType,
  SADisciplinaryStage,
  SAEvidenceType,
  SAEvidenceAccessLevel,
  SAMeetingType,
  SAMeetingStatus,
  SAActionType,
  SAActionStatus,
  SAAppealGrounds,
  SAAppealStatus,
  SAEscalationLevel,
} from "@campusos/types";

export async function runStudentAffairsModuleTests(): Promise<{
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
    // =========================================================================
    // 1. Operations Telemetry & Dashboard Metrics
    // =========================================================================
    const metrics = await studentAffairsService.getDashboardMetrics();
    assert(metrics.total_cases >= 3, "1. Total cases metric initialized (>=3)");
    assert(metrics.sla_compliance_rate >= 90, "1. SLA compliance rate computed (>=90%)");
    assert(metrics.resolved_this_month >= 20, "1. Monthly resolution volume computed");

    // =========================================================================
    // 2. Grievance Submission with Sequential Case Identifier
    // =========================================================================
    const categories = await studentAffairsService.getCategories();
    assert(categories.length >= 4, "2. Institutional grievance categories catalog loaded (>=4)");

    const subCase = await studentAffairsService.submitCase({
      categoryId: categories[1].id,
      title: "Faulty Projector in Lecture Hall 102",
      description: "Projector bulb flickers and shuts down during morning engineering lectures.",
      requestedResolution: "Replace bulb or projector unit.",
      campusId: "camp-001",
      isAnonymous: false,
      submitterType: SASubmitterType.STUDENT,
      confidentialityLevel: SAConfidentialityLevel.STANDARD,
    });
    assert(subCase.case_number.startsWith("GRV-"), "2. Case reference formatted with GRV- prefix");
    assert(subCase.status === SACaseStatus.SUBMITTED, "2. Initial state is SUBMITTED");
    assert(subCase.submitter_name_redacted === "Student Submitter", "2. Submitter name recorded");
    assert(subCase.target_response_date !== null, "2. Target response deadline computed");

    // =========================================================================
    // 3. Anonymous Submissions & Privacy Protection
    // =========================================================================
    const anonCase = await studentAffairsService.submitCase({
      categoryId: categories[3].id,
      title: "Hostel Entry Gate Verbal Intimidation",
      description: "Report of unauthorized verbal harassment near north perimeter wall.",
      requestedResolution: "Security patrol inspection.",
      campusId: "camp-001",
      isAnonymous: true,
      submitterType: SASubmitterType.ANONYMOUS,
      confidentialityLevel: SAConfidentialityLevel.RESTRICTED,
    });
    assert(anonCase.is_anonymous === true, "3. Anonymous flag recorded true");
    assert(anonCase.submitter_user_id === null, "3. Submitter user ID withheld from record");
    assert(
      anonCase.submitter_name_redacted.includes("Anonymous"),
      "3. Display persona sanitized to Anonymous Submitter"
    );

    // =========================================================================
    // 4. Case Intake, Triage & Officer Assignment
    // =========================================================================
    const assigned = await studentAffairsService.assignCase({
      caseId: subCase.id,
      officerId: "usr-off-001",
      reassignmentReason: "Assigned to Lead Case Officer for facilities triage",
      priority: SACasePriority.HIGH,
      targetResponseHours: 24,
    });
    assert(assigned.assigned_officer_id === "usr-off-001", "4. Officer usr-off-001 assigned");
    assert(assigned.priority === SACasePriority.HIGH, "4. Case priority elevated to HIGH");
    assert(assigned.status === SACaseStatus.ACKNOWLEDGED, "4. Status advanced to ACKNOWLEDGED");

    // =========================================================================
    // 5. Conflict of Interest Declaration & Recusal
    // =========================================================================
    await studentAffairsService.declareConflict({
      caseId: assigned.id,
      reason: "Officer Vikram Sethi has departmental affiliation with the facility vendor.",
      requestedReassignmentToOfficerId: "usr-off-002",
    });
    const reloadedConflictCase = await studentAffairsService.getCaseById(assigned.id);
    assert(
      reloadedConflictCase?.assigned_officer_id === "usr-off-002",
      "5. Case reassigned to independent officer usr-off-002 upon conflict declaration"
    );

    // =========================================================================
    // 6. Disciplinary Proceeding & Presumption of Good Faith
    // =========================================================================
    const discCase = await studentAffairsService.submitCase({
      categoryId: categories[2].id, // Academic Integrity / Disciplinary
      title: "Allegation of Formula Notes in Paper CE401",
      description: "Invigilator report alleging notes on desk during fluid mechanics exam.",
      requestedResolution: "",
      isAnonymous: false,
      submitterType: SASubmitterType.FACULTY,
      confidentialityLevel: SAConfidentialityLevel.CONFIDENTIAL,
    });

    const proc = await studentAffairsService.createDisciplinaryProceeding({
      caseId: discCase.id,
      respondentStudentId: "usr-std-009",
      allegationSummary: "Possession of unauthorized handwritten formula sheet",
      policyProvisionsViolated: "Student Code of Conduct Sec 4.2",
      investigatorId: "usr-inv-002",
    });
    assert(
      proc.finding_status === SAFindingStatus.PENDING,
      "6. Fair-process rule: Misconduct is NOT automatically assumed proven (finding_status=PENDING)"
    );
    assert(
      proc.procedural_stage === SADisciplinaryStage.INTAKE_ASSESSMENT,
      "6. Proceeding stage initialized to INTAKE_ASSESSMENT"
    );

    // =========================================================================
    // 7. Committee Findings & Procedural Stage Progression
    // =========================================================================
    const updatedFindings = await studentAffairsService.recordFindings(discCase.id, {
      findingsSummary: "Committee verified formula sheet was present on student desk during session.",
      findingStatus: SAFindingStatus.SUBSTANTIATED,
      proceduralStage: SADisciplinaryStage.FINDINGS_RECORDED,
    });
    assert(
      updatedFindings.finding_status === SAFindingStatus.SUBSTANTIATED,
      "7. Formal committee findings recorded as SUBSTANTIATED"
    );
    assert(
      updatedFindings.procedural_stage === SADisciplinaryStage.FINDINGS_RECORDED,
      "7. Procedural milestone advanced to FINDINGS_RECORDED"
    );

    // =========================================================================
    // 8. Sanction Authorization & Appeal Window
    // =========================================================================
    const sanctioned = await studentAffairsService.approveSanction(discCase.id, {
      sanctionType: SASanctionType.DISCIPLINARY_PROBATION,
      sanctionDetails: "Disciplinary probation for 1 semester with zero grade on Paper CE401.",
      decisionMakerId: "usr-dean-001", // Dr. Vikram Sethi (Original Decision Maker)
      appealDeadlineDays: 14,
    });
    assert(
      sanctioned.sanction_type === SASanctionType.DISCIPLINARY_PROBATION,
      "8. Sanction approved as DISCIPLINARY_PROBATION"
    );
    assert(sanctioned.decision_maker_id === "usr-dean-001", "8. Decision maker recorded as Dean");
    assert(sanctioned.appeal_deadline !== undefined, "8. Statutory 14-day appeal window activated");
    assert(sanctioned.is_communicated === true, "8. Decision marked as officially communicated");

    // =========================================================================
    // 9. Evidence Locker, Confidentiality Tiers & Redaction
    // =========================================================================
    const evOrig = await studentAffairsService.uploadEvidence({
      caseId: discCase.id,
      evidenceType: SAEvidenceType.TESTIMONY,
      title: "Confidential Witness Statement - Invigilator Assistant",
      description: "Detailed witness narrative with mobile numbers and dorm room identifiers.",
      fileUrl: "/secure/storage/testimony_orig.pdf",
      fileSizeBytes: 2048576,
      confidentialityLevel: SAEvidenceAccessLevel.RESTRICTED_INVESTIGATOR_ONLY,
    });
    assert(evOrig.id !== undefined, "9. Original evidence sealed in secure storage");
    assert(evOrig.is_redacted === false, "9. Original evidence marked unredacted");
    assert(
      evOrig.confidentiality_level === SAEvidenceAccessLevel.RESTRICTED_INVESTIGATOR_ONLY,
      "9. Restricted access tier applied"
    );

    const evRedacted = await studentAffairsService.redactEvidence({
      evidenceId: evOrig.id,
      redactionSummary: "Sanitized witness phone numbers and room coordinates to protect safety.",
      redactedFileUrl: "/secure/storage/testimony_redacted.pdf",
    });
    assert(evRedacted.is_redacted === true, "9. Redacted evidence derivative marked is_redacted=true");
    assert(
      evRedacted.original_evidence_id === evOrig.id,
      "9. Redacted evidence retains pointer to original immutable evidence ID"
    );
    assert(evRedacted.title.includes("[REDACTED]"), "9. Redacted evidence title prefixed with [REDACTED]");

    // =========================================================================
    // 10. Hearing & Mediation Scheduling
    // =========================================================================
    const meeting = await studentAffairsService.scheduleMeeting({
      caseId: discCase.id,
      title: "Standing Committee Disciplinary Hearing",
      meetingType: SAMeetingType.HEARING_PANEL,
      scheduledStart: new Date(Date.now() + 86400000).toISOString(),
      scheduledEnd: new Date(Date.now() + 90000000).toISOString(),
      venueOrUrl: "Admin Boardroom Room 204",
      facilitatorId: "usr-dean-001",
    });
    assert(meeting.id !== undefined, "10. Hearing panel meeting scheduled");
    assert(meeting.status === SAMeetingStatus.SCHEDULED, "10. Meeting status is SCHEDULED");

    // =========================================================================
    // 11. Resolution Corrective Actions
    // =========================================================================
    const action = await studentAffairsService.addResolutionAction({
      caseId: subCase.id,
      description: "Facilities HVAC team to replace air compressor in Lab 304",
      actionType: SAActionType.FACILITY_REPAIR,
      dueDate: "2026-10-31",
    });
    assert(action.id !== undefined, "11. Resolution action created");
    assert(action.status === SAActionStatus.PENDING, "11. Action status is PENDING");

    // =========================================================================
    // 12. Strict Separation of Duties on Appeals
    // =========================================================================
    const appeal = await studentAffairsService.fileAppeal({
      caseId: discCase.id,
      appealGrounds: SAAppealGrounds.NEW_EVIDENCE,
      groundsStatement: "Medical clearance demonstrates student was on prescribed migraine treatment.",
    });
    assert(appeal.review_status === SAAppealStatus.FILED, "12. Appeal status is FILED");

    // Separation of Duties Test: The original decision maker (usr-dean-001) MUST NOT review this appeal!
    let sodBlocked = false;
    try {
      await studentAffairsService.reviewAppeal({
        appealId: appeal.id,
        assignedReviewerId: "usr-dean-001", // VIOLATION: Dean was original decision maker
        reviewStatus: SAAppealStatus.UPHELD,
        outcomeSummary: "Attempted self-review",
      });
    } catch (err: any) {
      if (err?.message?.includes("Separation of Duties")) {
        sodBlocked = true;
      }
    }
    assert(
      sodBlocked === true,
      "12. UGC Separation of Duties rule: Original decision-maker is strictly BLOCKED from reviewing appeal"
    );

    // =========================================================================
    // 13. Independent Appellate Determination
    // =========================================================================
    const appealReview = await studentAffairsService.reviewAppeal({
      appealId: appeal.id,
      assignedReviewerId: "usr-ombuds-001", // Valid independent reviewer (Ombudsperson)
      reviewStatus: SAAppealStatus.OVERTURNED,
      outcomeSummary: "Appellate Council reviewed medical prescription and overturned disciplinary probation.",
    });
    assert(
      appealReview.review_status === SAAppealStatus.OVERTURNED,
      "13. Independent Ombudsperson overturns sanction upon reviewing new evidence"
    );

    // =========================================================================
    // 14. Urgent Safeguarding Escalation Triggers
    // =========================================================================
    const esc = await studentAffairsService.triggerEscalation({
      caseId: anonCase.id,
      escalationLevel: SAEscalationLevel.LEVEL_2_DIRECTOR,
      triggerReason: "Repeated perimeter security breach requires immediate executive dispatch.",
      safeguardingLeadId: "usr-icc-001",
    });
    assert(esc.id !== undefined, "14. Urgent escalation record registered");
    assert(esc.escalation_level === SAEscalationLevel.LEVEL_2_DIRECTOR, "14. Escalation tier set to LEVEL_2_DIRECTOR");

    // =========================================================================
    // 15. Confidential Case Communications
    // =========================================================================
    const msg = await studentAffairsService.sendConfidentialMessage({
      caseId: subCase.id,
      messageBody: "Engineering technician has inspected the lab cooling coils.",
      isInternalOnly: false,
    });
    assert(msg.id !== undefined, "15. Confidential message transmitted in case thread");

    // =========================================================================
    // 16. Pure Calculators & Safeguards
    // =========================================================================
    const futureDate = new Date(Date.now() + 48 * 3600 * 1000).toISOString();
    const slaOnTrack = StudentAffairsCalculator.calculateSlaStatus(futureDate, SACaseStatus.SUBMITTED);
    assert(slaOnTrack.statusLabel === "ON_TRACK", "16. SLA status for +48h is ON_TRACK");

    const pastDate = new Date(Date.now() - 5 * 3600 * 1000).toISOString();
    const slaBreached = StudentAffairsCalculator.calculateSlaStatus(pastDate, SACaseStatus.SUBMITTED);
    assert(slaBreached.statusLabel === "BREACHED", "16. SLA status for overdue case is BREACHED");

    const futureAppeal = new Date(Date.now() + 7 * 86400 * 1000).toISOString();
    assert(
      StudentAffairsCalculator.isAppealWindowActive(futureAppeal) === true,
      "16. Appeal window active for future deadline"
    );

    const pastAppeal = new Date(Date.now() - 1000).toISOString();
    assert(
      StudentAffairsCalculator.isAppealWindowActive(pastAppeal) === false,
      "16. Appeal window expired for past deadline"
    );

    const milestonesCalc = StudentAffairsCalculator.evaluateProceduralMilestones(proc);
    assert(milestonesCalc.milestones.length === 7, "16. Evaluates all 7 procedural stages");
  } catch (error: any) {
    results.push({
      testName: "Unhandled Exception in Student Affairs Test Suite",
      passed: false,
      message: error?.message || String(error),
    });
  }

  const passed = results.filter((r) => r.passed).length;
  const failed = results.filter((r) => !r.passed).length;

  return { passed, failed, results };
}

// Direct node/tsx execution harness
if (require.main === module || (typeof process !== "undefined" && process.argv[1]?.includes("student-affairs-module.test"))) {
  runStudentAffairsModuleTests().then(({ passed, failed, results }) => {
    console.log(`\n==================================================`);
    console.log(`CampusOS Student Affairs Module Verification Test Results`);
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
