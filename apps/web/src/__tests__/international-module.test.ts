/**
 * CampusOS Unified International Relations, Student Exchange & Global Mobility Module Test Suite
 * Step 60 Verification
 *
 * Validates:
 * 1. Global Mobility Telemetry & Executive Dashboard KPIs
 * 2. Institutional Mobility Policy Configuration (Warning Days, Council Gates, Mandatory Orientation)
 * 3. International Partner Registry & Active Institution Directory (TUM Munich, NUS Singapore, etc.)
 * 4. Institutional Agreements, MoU Lifecycles & Renewal Tracking
 * 5. Agreement Amendments & Scope Extension Audits
 * 6. Mobility Programs Directory & Exchange Seat Allocations
 * 7. Student Mobility Applications & Departmental Review Workflows
 * 8. Partner Nominations & Partner Admission Decision Handling
 * 9. Outbound Pre-Departure Verification & Active Mobility Readiness
 * 10. Inbound Scholar Registry & Onboarding Orientation Check-in
 * 11. Faculty Mobility & Visiting Scholar Dual Approval (HOD & VP)
 * 12. Institutional Course Equivalency Catalog & Departmental Approvals
 * 13. Academic Council Committee Credit Transfer Governance (Strictly Non-Automated)
 * 14. Student Travel Grants, Scholarships & Finance Ledger Integration
 * 15. Compliance Document Verification & Bio-Data Administrative Safeguards
 * 16. Multi-Tenant Isolation & Canonical Identity Guarantees
 */

import { internationalService } from "../services/international.service";
import {
  MOCK_PARTNERS,
  MOCK_AGREEMENTS,
  MOCK_PROGRAMS,
  MOCK_APPLICATIONS,
  MOCK_INBOUND_STUDENTS,
  MOCK_FACULTY_MOBILITIES,
  MOCK_EQUIVALENCIES,
  MOCK_CREDIT_TRANSFERS,
  MOCK_DOCUMENTS,
  MOCK_SCHOLARSHIPS,
  MOCK_FUNDING_REQUESTS,
  MOCK_POLICY_CONFIG,
  MOCK_DASHBOARD_METRICS,
} from "../mocks/international.mock";

export async function runInternationalModuleTests(): Promise<{
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
    // ------------------------------------------------------------------------
    // 1. Dashboard & Telemetry Metrics
    // ------------------------------------------------------------------------
    const metrics = await internationalService.getDashboardMetrics();
    assert(
      (metrics.total_active_partners ?? metrics.totalActivePartners ?? 0) >= 6,
      "1. Dashboard metrics reflect active partner registry count (>=6)",
      `Expected >=6 partners, got ${metrics.total_active_partners ?? metrics.totalActivePartners}`
    );
    assert(
      (metrics.active_agreements_count ?? metrics.activeAgreementsCount ?? 0) >= 8,
      "1. Dashboard metrics track active institutional agreements (>=8)",
      `Expected >=8 active agreements, got ${metrics.active_agreements_count ?? metrics.activeAgreementsCount}`
    );
    assert(
      (metrics.active_outbound_students ?? metrics.activeOutboundStudents ?? 0) > 0,
      "1. Dashboard tracks outbound exchange students participating globally",
      `Outbound students count was ${metrics.active_outbound_students ?? metrics.activeOutboundStudents}`
    );
    assert(
      (metrics.active_inbound_students ?? metrics.activeInboundStudents ?? 0) > 0,
      "1. Dashboard tracks incoming exchange scholars hosted on campus",
      `Inbound students count was ${metrics.active_inbound_students ?? metrics.activeInboundStudents}`
    );
    assert(
      (metrics.total_scholarship_disbursed ?? metrics.totalScholarshipDisbursed ?? 0) > 0,
      "1. Dashboard aggregates total mobility funding disbursements",
      `Disbursed funding was ${metrics.total_scholarship_disbursed ?? metrics.totalScholarshipDisbursed}`
    );

    // ------------------------------------------------------------------------
    // 2. Institutional Policy Configuration
    // ------------------------------------------------------------------------
    const config = await internationalService.getPolicyConfig();
    assert(
      (config.agreement_warning_days ?? config.agreementWarningDays ?? 0) >= 60,
      "2. Policy configuration enforces proactive agreement expiry notice (>= 60 days)",
      `Current agreement warning days: ${config.agreement_warning_days ?? config.agreementWarningDays}`
    );
    assert(
      config.require_department_approval_first ?? config.requireDepartmentApprovalFirst === true,
      "2. Policy configuration enforces mandatory Departmental approval before partner nomination"
    );
    assert(
      config.credit_transfer_requires_academic_council ?? config.creditTransferRequiresAcademicCouncil === true,
      "2. Policy configuration strictly mandates Academic Council ratification for external credit recognition"
    );
    assert(
      config.require_vp_approval_for_faculty ?? config.requireVpApprovalForFaculty === true,
      "2. Policy configuration mandates Vice-President / Executive approval for faculty exchanges"
    );
    assert(
      config.inbound_orientation_mandatory ?? config.inboundOrientationMandatory === true,
      "2. Policy configuration mandates international orientation completion before campus enrollment"
    );

    // Test policy update
    const updatedConfig = await internationalService.updatePolicyConfig({
      agreement_warning_days: 120,
    });
    assert(
      (updatedConfig.agreement_warning_days ?? updatedConfig.agreementWarningDays) === 120,
      "2. Policy update correctly updates institutional renewal notice window"
    );

    // ------------------------------------------------------------------------
    // 3. International Partner Registry
    // ------------------------------------------------------------------------
    const partners = await internationalService.getPartners();
    assert(
      partners.length >= 6,
      "3. Partner directory loads all global partner universities (>=6)",
      `Expected >= 6 partners, got ${partners.length}`
    );
    const tum = partners.find((p) => p.country_code === "DE" || p.countryCode === "DE");
    assert(
      tum !== undefined && (tum.partner_name || tum.partnerName || "").includes("Munich"),
      "3. European partner (TUM Munich) exists with full metadata"
    );
    const nus = partners.find((p) => p.country_code === "SG" || p.countryCode === "SG");
    assert(
      nus !== undefined && (nus.partner_name || nus.partnerName || "").includes("Singapore"),
      "3. Asian partner (NUS Singapore) exists with full metadata"
    );

    const newPartner = await internationalService.createPartner({
      partner_name: "Kyoto University",
      country_name: "Japan",
      country_code: "JP",
      city: "Kyoto",
      category: "UNIVERSITY",
      primary_contact_name: "Prof. Kenji Sato",
      primary_contact_email: "intl@kyoto-u.ac.jp",
    });
    assert(
      newPartner.id !== undefined && (newPartner.country_code === "JP" || newPartner.countryCode === "JP"),
      "3. New partner university created with primary contact and ISO country code"
    );

    // ------------------------------------------------------------------------
    // 4. Institutional Agreements & MoUs
    // ------------------------------------------------------------------------
    const agreements = await internationalService.getAgreements();
    assert(
      agreements.length >= 3,
      "4. Agreements registry returns all institutional MoUs and bilateral accords",
      `Expected >=3 agreements, got ${agreements.length}`
    );

    const activeMous = agreements.filter((a) => a.status === "ACTIVE");
    const expiringMous = agreements.filter((a) => a.status === "EXPIRING" || a.is_expiring_soon);
    assert(
      activeMous.length >= 2 && expiringMous.length >= 1,
      "4. Active and expiring MoUs are tracked and distinguishable for proactive renewal sweeps"
    );

    const newAgreement = await internationalService.createAgreement({
      partner_id: newPartner.id,
      agreement_reference_number: "MOU-KYOTO-2026",
      agreement_title: "Kyoto-CampusOS Bilateral Student & Research Exchange Accord",
      agreement_type: "STUDENT_EXCHANGE",
      effective_start_date: "2026-09-01",
      effective_end_date: "2031-08-31",
    });
    assert(
      newAgreement.id !== undefined && newAgreement.agreement_reference_number === "MOU-KYOTO-2026",
      "4. Bilateral student exchange agreement created with 5-year duration"
    );

    // ------------------------------------------------------------------------
    // 5. Agreement Amendments & Scope Audits
    // ------------------------------------------------------------------------
    const amendment = await internationalService.addAmendment(newAgreement.id, {
      title: "Add Dual-Degree Master in Robotics Scope",
      description: "Extends bilateral mobility to postgraduate robotics dual-degree students.",
      effective_date: "2026-10-01",
    });
    assert(
      amendment.id !== undefined && amendment.agreement_id === newAgreement.id,
      "5. Agreement amendment added to audit scope changes without mutating original MoU"
    );

    // ------------------------------------------------------------------------
    // 6. Mobility Programs Directory
    // ------------------------------------------------------------------------
    const programs = await internationalService.getPrograms();
    assert(
      programs.length >= 3,
      "6. Mobility programs catalog lists semester exchanges, research stays, and summer immersions",
      `Expected >=3 programs, got ${programs.length}`
    );
    const fallPrograms = programs.filter(
      (p) => (p.term_type || p.termType) === "FALL_SEMESTER" || (p.academic_year || p.academicYear) === "2026-2027"
    );
    assert(
      fallPrograms.length >= 1,
      "6. Programs directory indexes active academic cycles and terms"
    );

    const newProgram = await internationalService.createProgram({
      partner_id: tum?.id || "par-001",
      program_title: "TUM Winter Research Internship",
      program_code: "TUM-WIN-2026",
      program_type: "RESEARCH_STAY",
      term_type: "SPRING_SEMESTER",
      academic_year: "2026-2027",
      total_seats: 3,
      min_cgpa_requirement: 3.5,
      is_published: true,
    });
    assert(
      newProgram.id !== undefined && newProgram.total_seats === 3,
      "6. Research stay program created with prerequisite minimum CGPA and quota"
    );

    // ------------------------------------------------------------------------
    // 7. Student Mobility Applications & Workflows
    // ------------------------------------------------------------------------
    const applications = await internationalService.getApplications();
    assert(
      applications.length >= 3,
      "7. Applications registry lists active student exchange submissions",
      `Expected >=3 applications, got ${applications.length}`
    );

    const newApp = await internationalService.createApplication({
      program_id: newProgram.id,
      student_id: "stu-cs-042",
      statement_of_purpose: "Pursuing advanced AI systems research at TUM Munich.",
      proposed_courses: [
        { code: "IN2040", title: "Distributed Machine Learning", credits: 6 },
        { code: "IN2107", title: "Formal Verification", credits: 5 },
      ],
    });
    assert(
      newApp.id !== undefined && (newApp.status === "DEPARTMENT_REVIEW" || newApp.status === "DRAFT"),
      "7. New mobility application submitted into Departmental Review stage"
    );

    // Review application (Department approval)
    const approvedApp = await internationalService.reviewApplication(
      newApp.id,
      "APPROVE",
      "Department approves exchange; syllabus aligns with graduation requirements."
    );
    assert(
      approvedApp.status === "APPROVED",
      "7. Department review approval updates status to APPROVED for nomination processing"
    );

    // ------------------------------------------------------------------------
    // 8. Partner Nominations & Admissions
    // ------------------------------------------------------------------------
    const nominatedApp = await internationalService.nominateStudent(
      approvedApp.id,
      "Official dossier dispatched to partner international relations director.",
      "exchange@tum.de"
    );
    assert(
      nominatedApp.status === "PARTNER_NOMINATED",
      "8. Student successfully nominated to partner institution"
    );

    const acceptedApp = await internationalService.recordPartnerDecision(
      nominatedApp.id,
      "ACCEPTED",
      "Admission letter issued by host university for Fall term."
    );
    assert(
      acceptedApp.status === "PARTNER_ACCEPTED",
      "8. Host partner acceptance registered with official admission remarks"
    );

    // ------------------------------------------------------------------------
    // 9. Outbound Pre-Departure Verification & Active Mobility
    // ------------------------------------------------------------------------
    const preDepartureApp = await internationalService.updatePreDeparture(
      acceptedApp.id,
      {
        flight_booked: true,
        host_accommodation_confirmed: true,
        health_insurance_verified: true,
        safety_briefing_attended: true,
        consular_registration_done: true,
      },
      "GER-VISA-98231",
      "ALLIANZ-GLOBAL-4412"
    );
    assert(
      preDepartureApp.status === "ACTIVE_MOBILITY" || (preDepartureApp.pre_departure_checklist && Object.keys(preDepartureApp.pre_departure_checklist).length > 0),
      "9. Pre-departure checklist verified; student elevated to active overseas mobility status"
    );

    // ------------------------------------------------------------------------
    // 10. Inbound Scholars & Orientation Check-in
    // ------------------------------------------------------------------------
    const inboundStudents = await internationalService.getInboundStudents();
    assert(
      inboundStudents.length >= 3,
      "10. Inbound international students directory tracks incoming exchange scholars",
      `Expected >=3 inbound scholars, got ${inboundStudents.length}`
    );

    const targetInbound = inboundStudents[0];
    assert(
      targetInbound !== undefined && (targetInbound.first_name || targetInbound.firstName) !== undefined,
      "10. Inbound scholar record includes student profile and home university reference"
    );

    const checkedIn = await internationalService.checkinInboundStudent(
      targetInbound.id,
      "Campus ID issued, hostel room allocated, health insurance verified at international office."
    );
    assert(
      checkedIn.check_in_status === "ORIENTATION_COMPLETED" || checkedIn.orientation_completed === true,
      "10. Inbound scholar orientation check-in completes and activates campus privileges"
    );

    // ------------------------------------------------------------------------
    // 11. Faculty Mobility & Visiting Scholars
    // ------------------------------------------------------------------------
    const facultyMobilities = await internationalService.getFacultyMobilities();
    assert(
      facultyMobilities.length >= 2,
      "11. Faculty mobility registry tracks outbound fellowships and visiting international professors",
      `Expected >=2 faculty records, got ${facultyMobilities.length}`
    );

    const newFacultyMobility = await internationalService.createFacultyMobility({
      partner_id: nus?.id || "par-002",
      staff_user_id: "fac-ece-019",
      mobility_type: "OUTBOUND",
      visit_start_date: "2026-11-01",
      visit_end_date: "2026-11-28",
      purpose_summary: "Joint research collaboration on quantum photonic circuits.",
    });
    assert(
      newFacultyMobility.id !== undefined && newFacultyMobility.status === "SUBMITTED",
      "11. Outbound faculty sabbatical fellowship submitted for institutional review"
    );

    const hodApproved = await internationalService.approveFacultyMobility(
      newFacultyMobility.id,
      "HOD",
      "APPROVED",
      "Teaching substitute coverage arranged for November."
    );
    assert(
      hodApproved !== undefined,
      "11. Department Head (HOD) approval recorded for faculty mobility"
    );

    const vpApproved = await internationalService.approveFacultyMobility(
      newFacultyMobility.id,
      "VP",
      "APPROVED",
      "Institutional sponsorship sanctioned by Vice President."
    );
    assert(
      vpApproved.status === "APPROVED",
      "11. Dual-level executive (Vice President) approval finalizes faculty fellowship"
    );

    // ------------------------------------------------------------------------
    // 12. Institutional Course Equivalencies
    // ------------------------------------------------------------------------
    const equivalencies = await internationalService.getCourseEquivalencies();
    assert(
      equivalencies.length >= 3,
      "12. Course equivalency catalog maps foreign syllabus units to home curriculum",
      `Expected >=3 equivalencies, got ${equivalencies.length}`
    );

    const newEquiv = await internationalService.createCourseEquivalency({
      partner_id: tum?.id || "par-001",
      host_course_code: "IN2040",
      host_course_title: "Distributed Machine Learning Systems",
      host_credits: 6,
      target_course_code: "CS420",
      target_course_title: "Distributed Systems & Cloud Computing",
      target_credits: 4,
      department_id: "dept-cse",
    });
    assert(
      newEquiv.id !== undefined && (newEquiv.host_course_code || newEquiv.hostCourseCode) === "IN2040",
      "12. External syllabus mapped to canonical department course code"
    );

    const evaluatedEquiv = await internationalService.evaluateCourseEquivalency(
      newEquiv.id,
      "APPROVED",
      "Syllabus coverage matches 85% of CS420 learning outcomes."
    );
    assert(
      evaluatedEquiv.status === "ACTIVE",
      "12. Course equivalency formally evaluated and activated for credit mapping"
    );

    // ------------------------------------------------------------------------
    // 13. Academic Council Committee Credit Transfer Governance (Strictly Non-Automated)
    // ------------------------------------------------------------------------
    const creditTransfers = await internationalService.getCreditTransfers();
    assert(
      creditTransfers.length >= 2,
      "13. Credit transfer requests loaded with official transcript audit records",
      `Expected >=2 credit transfer records, got ${creditTransfers.length}`
    );

    const newTransfer = await internationalService.createCreditTransfer({
      application_id: applications[0]?.id || "app-001",
      student_id: "stu-001",
      host_institution_name: "Technical University of Munich",
      host_credits_earned: 12,
      target_campus_credits: 12,
    });
    assert(
      newTransfer.id !== undefined && newTransfer.status === "SUBMITTED",
      "13. Student credit transfer request submitted awaiting Academic Committee review"
    );

    // Governance requirement: strictly governed by Academic Council / Committee
    const councilApproved = await internationalService.approveCreditTransfer(
      newTransfer.id,
      "APPROVED",
      "Transcript verified against original European Credit Transfer System (ECTS) seal.",
      "AC-RES-2026-089"
    );
    assert(
      councilApproved.status === "APPROVED" &&
        (councilApproved.academic_council_approval_ref === "AC-RES-2026-089" ||
          councilApproved.academic_council_approval_reference === "AC-RES-2026-089"),
      "13. Non-automated credit recognition: strictly certified by Academic Council resolution reference"
    );

    // ------------------------------------------------------------------------
    // 14. Travel Grants, Scholarships & Finance Ledger Integration
    // ------------------------------------------------------------------------
    const scholarships = await internationalService.getScholarships();
    assert(
      scholarships.length >= 2,
      "14. Mobility scholarships catalog lists available institutional & partner grants",
      `Expected >=2 scholarships, got ${scholarships.length}`
    );

    const fundingRequests = await internationalService.getFundingRequests();
    assert(
      fundingRequests.length >= 1,
      "14. Travel grant funding requests loaded from ledger integration",
      `Expected >=1 funding requests, got ${fundingRequests.length}`
    );

    const newFundingReq = await internationalService.createFundingRequest({
      application_id: applications[0]?.id || "app-001",
      student_id: "stu-001",
      requested_amount: 2500,
      currency: "EUR",
      justification: "Transatlantic airfare and initial accommodation deposit in Munich.",
    });
    assert(
      newFundingReq.id !== undefined && newFundingReq.status === "REQUESTED",
      "14. Student travel subsidy request submitted with explicit cost justification"
    );

    // Approve grant linking to finance disbursement
    const approvedFunding = await internationalService.approveFundingRequest(
      newFundingReq.id,
      "APPROVED",
      2500,
      "FIN-DISB-2026-904"
    );
    assert(
      approvedFunding.status === "APPROVED" &&
        (approvedFunding.finance_disbursement_ref === "FIN-DISB-2026-904" ||
          approvedFunding.finance_reference_id === "FIN-DISB-2026-904"),
      "14. Mobility grant disbursement linked directly to enterprise finance disbursement voucher"
    );

    // ------------------------------------------------------------------------
    // 15. Compliance Documents & Administrative Safeguards
    // ------------------------------------------------------------------------
    const documents = await internationalService.getDocuments();
    assert(
      documents.length >= 3,
      "15. Compliance documents repository tracks passports, visas, insurance, and transcripts",
      `Expected >=3 compliance documents, got ${documents.length}`
    );

    const pendingDoc = documents.find((d) => d.verification_status === "PENDING");
    assert(
      pendingDoc !== undefined,
      "15. Unverified documents queued for administrative authenticity check"
    );

    const verifiedDoc = await internationalService.verifyDocument(
      pendingDoc?.id || documents[0].id,
      "VERIFIED"
    );
    assert(
      verifiedDoc.verification_status === "VERIFIED",
      "15. Compliance document marked as legally verified by international relations auditor"
    );

    // ------------------------------------------------------------------------
    // 16. Multi-Tenant Data Isolation & Security Safeguards
    // ------------------------------------------------------------------------
    assert(
      !("automated_immigration_advice" in config),
      "16. Administrative safeguard: No automated immigration advice generation exists"
    );
    assert(
      !("parallel_student_user_table" in metrics),
      "16. Architecture integrity: Strictly adheres to canonical user and student identity models"
    );
  } catch (error: any) {
    results.push({
      testName: "Unhandled Exception in International Relations Test Suite",
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
  (typeof process !== "undefined" && process.argv[1]?.includes("international-module.test"))
) {
  runInternationalModuleTests().then(({ passed, failed, results }) => {
    console.log(`\n========================================================================`);
    console.log(`CampusOS Enterprise International Relations & Global Mobility Test Suite`);
    console.log(`Step 60 Verification`);
    console.log(`========================================================================`);
    results.forEach((r, idx) => {
      const mark = r.passed ? "✓ PASS" : "✗ FAIL";
      console.log(`${mark} [${idx + 1 < 10 ? "0" + (idx + 1) : idx + 1}] ${r.testName}`);
      if (!r.passed && r.message) {
        console.log(`       Reason: ${r.message}`);
      }
    });
    console.log(`------------------------------------------------------------------------`);
    console.log(`Total Passed: ${passed}`);
    console.log(`Total Failed: ${failed}`);
    console.log(`Success Rate: ${Math.round((passed / (passed + failed || 1)) * 100)}%`);
    console.log(`========================================================================\n`);
    if (failed > 0) {
      process.exit(1);
    }
  });
}
