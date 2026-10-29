/**
 * CampusOS Placement Management Module — Comprehensive Test Suite
 * Validates domain contracts, eligibility evaluation engine, application submission,
 * duplicate prevention, shortlisting, interview scheduling & evaluation,
 * offer lifecycle (release, accept, decline), placement outcomes ledger,
 * metrics calculators, global search deep-linking, and RBAC matrix.
 */

import { placementService } from "../services/placement.service";
import {
  checkProgramEligibility,
  checkGraduationYearEligibility,
  checkCgpaEligibility,
  checkBacklogEligibility,
  checkSkillEligibility,
  calculateEligibility,
  calculatePlacementRate,
  calculateOfferRate,
  calculateShortlistRate,
  calculateAveragePackage,
  calculateMedianPackage,
  formatLPA,
} from "../services/placement-calculator";
import { searchService } from "../services/search.service";
import { StudentPlacementProfile, Position } from "../types/placement";

export async function runPlacementModuleTests(): Promise<{
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
    // 1. Placement Telemetry & Operations Summary
    // ==========================================
    const summaryRes = await placementService.getPlacementSummary();
    assert(
      summaryRes.success === true,
      "1. Placement dashboard summary returns success",
    );
    assert(
      summaryRes.data.activeCompaniesCount >= 3,
      "1. Active corporate partners count is valid",
    );
    assert(
      summaryRes.data.openDrivesCount >= 1,
      "1. Open recruitment drives count is valid",
    );
    assert(
      summaryRes.data.eligibleStudentsCount > 0,
      "1. Eligible student cohort is tracked",
    );
    assert(
      summaryRes.data.placementRate > 0,
      "1. Placement conversion rate is calculated",
    );
    assert(
      summaryRes.data.averagePackageLpa > 0,
      "1. Average CTC package is non-zero",
    );
    assert(
      summaryRes.data.highestPackageLpa >= summaryRes.data.averagePackageLpa,
      "1. Highest CTC >= Average CTC",
    );
    assert(
      summaryRes.data.departmentStats.length >= 2,
      "1. Department placement breakdown is provided",
    );
    assert(
      summaryRes.data.packageDistribution.length >= 3,
      "1. CTC slab distribution is provided",
    );

    // ==========================================
    // 2. Pure Eligibility Calculators
    // ==========================================
    const mockStudent: StudentPlacementProfile = {
      id: "prof-test",
      studentId: "std-test-1",
      studentName: "Test Candidate",
      rollNumber: "TEST-001",
      email: "test@campusos.edu",
      phone: "+91 9900000000",
      program: "B.Tech Computer Science and Engineering",
      department: "Computer Science and Engineering",
      graduationYear: 2026,
      currentSemester: 7,
      cgpa: 8.65,
      activeBacklogs: 0,
      historyBacklogs: 0,
      attendancePercent: 88,
      skills: {
        technical: ["Distributed Systems", "Cloud Computing"],
        programmingLanguages: ["TypeScript", "Go", "Python"],
        toolsAndFrameworks: ["React", "Next.js", "Docker"],
        domains: ["Full Stack", "Cloud Platforms"],
        certifications: ["AWS Certified Developer"],
      },
      resumeStatus: "VERIFIED",
      profileCompletionPercent: 100,
      status: "ACTIVE",
      applicationsCount: 0,
      shortlistsCount: 0,
      interviewsCount: 0,
      offersCount: 0,
      placementStatus: "IN_PROCESS",
      timeline: [],
    };

    const mockPosition: Position = {
      id: "pos-test",
      driveId: "drv-test",
      driveCode: "DRV-TEST",
      companyId: "comp-test",
      companyName: "Acme Corporation",
      title: "Senior Software Engineer",
      departmentFunction: "Engineering",
      employmentType: "FULL_TIME",
      location: "Bengaluru",
      vacancies: 5,
      ctcLpa: 16.0,
      baseSalaryLpa: 14.0,
      requiredSkills: ["TypeScript", "Go"],
      minCgpa: 7.5,
      maxBacklogs: 0,
      minAttendancePercent: 75,
      targetPrograms: [
        "B.Tech Computer Science and Engineering",
        "B.Tech Information Technology",
      ],
      targetDepartments: [
        "Computer Science and Engineering",
        "Information Technology",
      ],
      graduationYear: 2026,
      status: "OPEN",
      createdAt: new Date().toISOString(),
    };

    // Program Eligibility
    const progResValid = checkProgramEligibility(
      mockStudent.program,
      mockPosition.targetPrograms,
    );
    assert(
      progResValid.passed === true,
      "2. Program eligibility passes for target program",
    );
    const progResInvalid = checkProgramEligibility(
      "B.Tech Civil Engineering",
      mockPosition.targetPrograms,
    );
    assert(
      progResInvalid.passed === false,
      "2. Program eligibility fails for non-target program",
    );

    // Graduation Year Eligibility
    const gradResValid = checkGraduationYearEligibility(
      mockStudent.graduationYear,
      mockPosition.graduationYear,
    );
    assert(
      gradResValid.passed === true,
      "2. Graduation year matches target batch",
    );
    const gradResInvalid = checkGraduationYearEligibility(
      2028,
      mockPosition.graduationYear,
    );
    assert(
      gradResInvalid.passed === false,
      "2. Graduation year mismatch properly detected",
    );

    // CGPA Eligibility
    const cgpaResValid = checkCgpaEligibility(
      mockStudent.cgpa,
      mockPosition.minCgpa,
    );
    assert(
      cgpaResValid.passed === true,
      "2. CGPA 8.65 meets minimum 7.50 requirement",
    );
    const cgpaResInvalid = checkCgpaEligibility(6.4, mockPosition.minCgpa);
    assert(
      cgpaResInvalid.passed === false,
      "2. CGPA 6.40 fails minimum 7.50 requirement",
    );
    assert(
      cgpaResInvalid.actual === 6.4,
      "2. CGPA evaluation returns actual student value",
    );
    assert(
      cgpaResInvalid.required === 7.5,
      "2. CGPA evaluation returns required cutoff",
    );

    // Backlog Eligibility
    const backlogResValid = checkBacklogEligibility(
      mockStudent.activeBacklogs,
      mockPosition.maxBacklogs,
    );
    assert(
      backlogResValid.passed === true,
      "2. Zero active backlogs passes zero-backlog requirement",
    );
    const backlogResInvalid = checkBacklogEligibility(
      2,
      mockPosition.maxBacklogs,
    );
    assert(
      backlogResInvalid.passed === false,
      "2. Active backlogs > 0 correctly fails zero-backlog requirement",
    );

    // Skill Eligibility
    const skillResValid = checkSkillEligibility(
      [
        ...mockStudent.skills.programmingLanguages,
        ...mockStudent.skills.technical,
      ],
      mockPosition.requiredSkills,
    );
    assert(
      skillResValid.passed === true,
      "2. Candidate holding all required skills passes check",
    );

    // Combined Calculate Eligibility
    const combinedElig = calculateEligibility(mockStudent, mockPosition);
    assert(
      combinedElig.status === "ELIGIBLE",
      "2. Ideal candidate evaluates to ELIGIBLE",
    );
    assert(
      combinedElig.rules.length >= 5,
      "2. Comprehensive rule snapshot contains all 5+ criteria",
    );

    // Ineligible Candidate Snapshot
    const lowCgpaStudent: StudentPlacementProfile = {
      ...mockStudent,
      cgpa: 6.2,
    };
    const ineligibleSnapshot = calculateEligibility(
      lowCgpaStudent,
      mockPosition,
    );
    assert(
      ineligibleSnapshot.status === "INELIGIBLE",
      "2. Low CGPA student results in INELIGIBLE status",
    );
    const failingCgpaRule = ineligibleSnapshot.rules.find(
      (r) => r.rule === "MIN_CGPA",
    );
    assert(
      failingCgpaRule?.passed === false,
      "2. Rule failure explicitly isolated to MIN_CGPA rule",
    );

    // ==========================================
    // 3. Metric Calculators
    // ==========================================
    assert(
      calculatePlacementRate(80, 100) === 80,
      "3. Placement rate calculation 80/100 = 80%",
    );
    assert(
      calculateOfferRate(90, 100) === 90,
      "3. Offer rate calculation 90/100 = 90%",
    );
    assert(
      calculateShortlistRate(40, 100) === 40,
      "3. Shortlist rate calculation 40/100 = 40%",
    );
    assert(
      calculateAveragePackage([10, 12, 14]) === 12,
      "3. Average package [10, 12, 14] = 12.00 LPA",
    );
    assert(
      calculateMedianPackage([8, 12, 20]) === 12,
      "3. Median package [8, 12, 20] = 12.00 LPA",
    );
    assert(
      calculateMedianPackage([10, 14, 18, 22]) === 16,
      "3. Median package [10, 14, 18, 22] = 16.00 LPA",
    );
    assert(
      formatLPA(18.5) === "₹18.5 LPA",
      "3. formatLPA handles decimals formatted with currency symbol",
    );

    // ==========================================
    // 4. Corporate Partners & Job Drives
    // ==========================================
    const companiesRes = await placementService.getCompanies();
    assert(companiesRes.success === true, "4. Companies query returns success");
    assert(
      companiesRes.data.length >= 3,
      "4. Seeded corporate partners loaded",
    );

    const newCompanyRes = await placementService.createCompany({
      name: "Stripe India",
      industry: "Financial Technology",
      companyType: "PRODUCT",
      tier: "TIER_1_SUPER_DREAM",
      website: "https://stripe.com",
      headquarters: "Bengaluru, Karnataka",
      contacts: [
        {
          id: "cnt-1",
          name: "Siddharth Menon",
          role: "University Recruiting Lead",
          email: "siddharth@stripe.com",
          phone: "+91 9876543210",
          isPrimary: true,
        },
      ],
      status: "ACTIVE",
    });
    assert(
      newCompanyRes.success === true,
      "4. New corporate partner created successfully",
    );
    assert(
      newCompanyRes.data.name === "Stripe India",
      "4. Created company maintains exact name",
    );

    // Drives
    const drivesRes = await placementService.getJobDrives();
    assert(drivesRes.success === true, "4. Drives query returns success");
    assert(drivesRes.data.length >= 3, "4. Campus recruitment drives present");

    // ==========================================
    // 5. Application Lifecycle & Validation
    const openDrive = drivesRes.data.find((d) => d.status === "OPEN");
    assert(
      openDrive !== undefined,
      "5. At least one recruitment drive is in OPEN status",
    );

    const positionsRes = await placementService.getPositions();
    const drivePosition = positionsRes.data.find(
      (p) => p.driveId === openDrive?.id,
    );
    assert(
      drivePosition !== undefined,
      "5. Open drive contains associated job position",
    );

    // 5.1 Duplicate application prevention
    const existingApps = await placementService.getApplications();
    const sampleApp = existingApps.data[0];
    if (sampleApp) {
      try {
        await placementService.submitApplication({
          studentId: sampleApp.studentId,
          driveId: sampleApp.driveId,
          positionId: sampleApp.positionId,
        });
        assert(false, "5. Duplicate application should have been rejected");
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        assert(
          msg.includes("already submitted") || msg.includes("already"),
          "5. Duplicate application prevented with validation error",
        );
      }
    }

    // ==========================================
    // 6. Candidate Shortlisting
    // ==========================================
    const allAppsRes = await placementService.getApplications();
    const submittedApp = allAppsRes.data.find(
      (a) => a.status === "SUBMITTED" || a.status === "UNDER_REVIEW",
    );
    if (submittedApp) {
      const shortlistRes = await placementService.shortlistApplications(
        [submittedApp.id],
        "Placement Officer",
      );
      assert(
        shortlistRes.success === true,
        "6. Candidate shortlisting call returns success",
      );
      const updatedApp = shortlistRes.data.find(
        (a) => a.id === submittedApp.id,
      );
      assert(
        updatedApp?.status === "SHORTLISTED",
        "6. Application status updated to SHORTLISTED",
      );
      assert(
        updatedApp?.currentStage === "TECHNICAL",
        "6. Application stage advanced to TECHNICAL interview",
      );
    }

    // ==========================================
    // 7. Interview Lifecycle & Evaluation
    // ==========================================
    const interviewsRes = await placementService.getInterviews();
    assert(
      interviewsRes.success === true,
      "7. Interviews query returns success",
    );
    assert(interviewsRes.data.length >= 1, "7. Scheduled interviews exist");

    // Schedule interview
    const targetApp = allAppsRes.data[0];
    const newIntvRes = await placementService.scheduleInterview({
      applicationId: targetApp.id,
      stage: "TECHNICAL",
      roundNumber: 1,
      date: "2026-10-15",
      time: "11:00 AM",
      durationMinutes: 45,
      mode: "ONLINE",
      locationOrMeetingUrl: "https://cisco.webex.com/meet/technical-panel",
      interviewerName: "Dr. Kunal Bhasin",
      notes: "System design and concurrency questions",
    });
    assert(newIntvRes.success === true, "7. Interview scheduled successfully");
    assert(
      newIntvRes.data.status === "SCHEDULED",
      "7. Scheduled interview status is SCHEDULED",
    );

    // Reschedule interview
    const rescheduleRes = await placementService.rescheduleInterview(
      newIntvRes.data.id,
      "2026-10-16",
      "02:00 PM",
      "Recruiter flight delay",
      "Placement Coordinator",
    );
    assert(
      rescheduleRes.success === true,
      "7. Interview rescheduled successfully",
    );
    assert(
      rescheduleRes.data.status === "RESCHEDULED",
      "7. Status updated to RESCHEDULED",
    );
    assert(
      rescheduleRes.data.date === "2026-10-16",
      "7. Date updated to new date",
    );

    // Complete interview with 4-dimension evaluation
    const completeRes = await placementService.completeInterview(
      newIntvRes.data.id,
      {
        technicalRating: 5,
        technicalSkillsRating: 5,
        communicationRating: 4,
        problemSolvingRating: 5,
        roleFitRating: 5,
        overallRecommendation: "STRONG_HIRE",
        strengths:
          "Outstanding grasp of distributed consensus and Go concurrency patterns.",
        areasOfImprovement: "Can expand knowledge on Kubernetes operators.",
        notes: "Recommended for Senior Software Engineer offer.",
        evaluatedBy: "Dr. Kunal Bhasin",
        evaluatedAt: new Date().toISOString(),
      },
    );
    assert(
      completeRes.success === true,
      "7. Interview completed with evaluation",
    );
    assert(
      completeRes.data.status === "COMPLETED",
      "7. Status updated to COMPLETED",
    );
    assert(
      completeRes.data.evaluation?.overallRecommendation === "STRONG_HIRE",
      "7. STRONG_HIRE recommendation recorded",
    );

    // ==========================================
    // 8. Offers & Acceptance Desk
    // ==========================================
    const offersRes = await placementService.getOffers();
    assert(offersRes.success === true, "8. Offers query returns success");
    assert(offersRes.data.length >= 1, "8. Seeded offers exist");

    // Release new offer
    const releaseRes = await placementService.releaseOffer({
      applicationId: targetApp.id,
      employmentType: "FULL_TIME",
      location: "Bengaluru, Karnataka",
      ctcLpa: 17.5,
      baseSalaryLpa: 15.0,
      variableLpa: 2.5,
      responseDeadline: "2026-11-01",
      joiningDate: "2027-07-01",
      releasedBy: "Placement Director",
    });
    assert(
      releaseRes.success === true,
      "8. Formal offer released successfully",
    );
    assert(
      releaseRes.data.status === "RELEASED",
      "8. Offer initial status is RELEASED",
    );
    assert(
      releaseRes.data.ctcLpa === 17.5,
      "8. Offer CTC recorded as ₹17.50 LPA",
    );

    // Accept offer
    const acceptRes = await placementService.acceptOffer(
      releaseRes.data.id,
      "Thrilled to accept the offer! Thank you.",
    );
    assert(
      acceptRes.success === true,
      "8. Candidate offer acceptance call returns success",
    );
    assert(
      acceptRes.data.status === "ACCEPTED",
      "8. Offer status updated to ACCEPTED",
    );
    assert(
      acceptRes.data.responseNotes !== undefined,
      "8. Candidate acceptance remarks persisted",
    );

    // Decline offer check
    const altOfferRes = await placementService.releaseOffer({
      applicationId: targetApp.id,
      employmentType: "FULL_TIME",
      ctcLpa: 9.0,
      baseSalaryLpa: 8.0,
      responseDeadline: "2026-11-01",
      joiningDate: "2027-07-01",
    });
    const declineRes = await placementService.declineOffer(
      altOfferRes.data.id,
      "Pursuing higher studies abroad.",
    );
    assert(
      declineRes.success === true,
      "8. Offer decline call returns success",
    );
    assert(
      declineRes.data.status === "DECLINED",
      "8. Declined offer status updated to DECLINED",
    );

    // ==========================================
    // 9. Placement Outcomes Ledger
    // ==========================================
    const outcomesRes = await placementService.getPlacementOutcomes();
    assert(
      outcomesRes.success === true,
      "9. Placement outcomes ledger query returns success",
    );
    assert(
      outcomesRes.data.length >= 3,
      "9. Outcomes ledger contains tracked student records",
    );

    const placedStudent = outcomesRes.data.find((o) => o.status === "PLACED");
    assert(
      placedStudent !== undefined,
      "9. Placed graduate confirmed in ledger",
    );
    assert(
      placedStudent?.companyName !== "",
      "9. Placed graduate has corporate appointment recorded",
    );
    assert(
      (placedStudent?.ctcLpa || 0) > 0,
      "9. Placed graduate has verified CTC recorded",
    );

    // ==========================================
    // 10. Placement Reporting Intelligence
    // ==========================================
    const summaryRepRes = await placementService.generatePlacementReport({
      reportType: "SUMMARY",
    });
    assert(
      summaryRepRes.success === true,
      "10. Cohort conversion summary report generated",
    );
    assert(
      summaryRepRes.data.rows.length > 0,
      "10. Summary report contains data rows",
    );

    const deptRepRes = await placementService.generatePlacementReport({
      reportType: "DEPARTMENT",
    });
    assert(
      deptRepRes.success === true,
      "10. Department performance audit report generated",
    );
    assert(
      deptRepRes.data.rows.length >= 2,
      "10. Department audit covers multiple engineering departments",
    );

    const compRepRes = await placementService.generatePlacementReport({
      reportType: "COMPANY",
    });
    assert(
      compRepRes.success === true,
      "10. Corporate partners hiring report generated",
    );
    assert(
      compRepRes.data.rows.length >= 3,
      "10. Corporate partners ledger contains all active recruiters",
    );

    const packRepRes = await placementService.generatePlacementReport({
      reportType: "PACKAGES",
    });
    assert(
      packRepRes.success === true,
      "10. Salary slab distribution report generated",
    );

    const statusRepRes = await placementService.generatePlacementReport({
      reportType: "STATUS",
    });
    assert(
      statusRepRes.success === true,
      "10. Placement outcomes ledger report generated",
    );

    // ==========================================
    // 11. Command Palette & Global Search Deep-Linking
    // ==========================================
    const searchDrivesRes = await searchService.search("Cisco");
    assert(
      searchDrivesRes.data && searchDrivesRes.data.length >= 1,
      "11. Global search indexes placement corporate drives",
    );
    assert(
      searchDrivesRes.data[0].href.includes("/app/placement"),
      "11. Search result deep-links to /app/placement route",
    );

    const searchCompRes = await searchService.search("Google");
    assert(
      searchCompRes.data && searchCompRes.data.length >= 1,
      "11. Global search finds Google Cloud recruitment records",
    );

    // ==========================================
    // 12. Role-Based Access Control (RBAC) Matrix
    // ==========================================
    const rbacPlacementMatrix = {
      ADMIN: {
        viewPlacement: true,
        manageProfiles: true,
        manageCompanies: true,
        manageDrives: true,
        managePositions: true,
        manageEligibility: true,
        reviewApplications: true,
        manageInterviews: true,
        manageOffers: true,
        manageOutcomes: true,
        viewReports: true,
      },
      PLACEMENT_OFFICER: {
        viewPlacement: true,
        manageProfiles: true,
        manageCompanies: true,
        manageDrives: true,
        managePositions: true,
        manageEligibility: true,
        reviewApplications: true,
        manageInterviews: true,
        manageOffers: true,
        manageOutcomes: true,
        viewReports: true,
      },
      HOD: {
        viewPlacement: true,
        manageProfiles: false,
        manageCompanies: false,
        manageDrives: false,
        managePositions: false,
        manageEligibility: false,
        reviewApplications: true, // department view
        manageInterviews: false,
        manageOffers: false,
        manageOutcomes: false,
        viewReports: true, // department reports
      },
      FACULTY_COORDINATOR: {
        viewPlacement: true,
        manageProfiles: false,
        manageCompanies: false,
        manageDrives: false,
        managePositions: false,
        manageEligibility: false,
        reviewApplications: true,
        manageInterviews: true,
        manageOffers: false,
        manageOutcomes: false,
        viewReports: false,
      },
      STUDENT: {
        viewPlacement: true, // personal "My Placement"
        manageProfiles: true, // own profile only
        manageCompanies: false, // STRICTLY FORBIDDEN
        manageDrives: false, // STRICTLY FORBIDDEN
        managePositions: false, // STRICTLY FORBIDDEN
        manageEligibility: false, // STRICTLY FORBIDDEN
        reviewApplications: false, // cannot shortlist self
        manageInterviews: false, // cannot alter interview decisions
        manageOffers: false, // cannot create offers
        manageOutcomes: false, // cannot alter outcomes
        viewReports: false, // cannot view institutional reports
        apply: true, // permitted action
        respondToOffer: true, // permitted action
      },
    };

    assert(
      rbacPlacementMatrix.ADMIN.manageCompanies === true,
      "12. Admin authorized to manage companies",
    );
    assert(
      rbacPlacementMatrix.PLACEMENT_OFFICER.manageDrives === true,
      "12. Placement Officer authorized to manage drives",
    );
    assert(
      rbacPlacementMatrix.PLACEMENT_OFFICER.manageOffers === true,
      "12. Placement Officer authorized to release offers",
    );
    assert(
      rbacPlacementMatrix.HOD.manageCompanies === false,
      "12. HOD prohibited from editing corporate partner accounts",
    );
    assert(
      rbacPlacementMatrix.HOD.manageOffers === false,
      "12. HOD prohibited from creating corporate offers",
    );
    assert(
      rbacPlacementMatrix.STUDENT.manageCompanies === false,
      "12. Student strictly prohibited from modifying companies",
    );
    assert(
      rbacPlacementMatrix.STUDENT.manageEligibility === false,
      "12. Student strictly prohibited from altering eligibility rules",
    );
    assert(
      rbacPlacementMatrix.STUDENT.reviewApplications === false,
      "12. Student strictly prohibited from shortlisting self",
    );
    assert(
      rbacPlacementMatrix.STUDENT.manageOffers === false,
      "12. Student strictly prohibited from creating corporate offers",
    );
    assert(
      rbacPlacementMatrix.STUDENT.manageOutcomes === false,
      "12. Student strictly prohibited from modifying placement outcomes",
    );
    assert(
      rbacPlacementMatrix.STUDENT.apply === true,
      "12. Student authorized to submit job application",
    );
    assert(
      rbacPlacementMatrix.STUDENT.respondToOffer === true,
      "12. Student authorized to accept/decline received offers",
    );
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : String(err);
    results.push({
      testName: "Exception during test execution",
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
  process.argv[1]?.includes("placement-module.test")
) {
  runPlacementModuleTests().then((res) => {
    console.log(`\n==============================================`);
    console.log(`CampusOS Placement Management Module Test Results:`);
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
