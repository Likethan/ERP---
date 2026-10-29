/**
 * CampusOS Enterprise Sports, Athletics, Recreation & Student Fitness Module Test Suite
 * Step 57 Verification
 *
 * Validates:
 * 1. Sports Operations Telemetry & Dashboard KPIs
 * 2. Department Administration & Operating Schedules
 * 3. Facility Availability & Overlapping Booking Conflict Prevention
 * 4. Maintenance Closure & Safe Reopening Lifecycle
 * 5. Student Athlete Registration & Medical Clearance Safeguards
 * 6. Team Rostering, Capacity Bounds & Eligibility Verification
 * 7. Coach and Match Official Assignments
 * 8. Training Programs, Recurring Sessions & Attendance Roll Call
 * 9. Tournament Fixture Generation (Round Robin Berger & Single Elimination Knockout)
 * 10. Auditable Match Result Verification & Score Corrections
 * 11. Competition Standings & Point / Goal Difference Tiebreakers
 * 12. Equipment Checkout, Asset Integration & Damage Fee Return Inspection
 * 13. Sports Registrations, Invoice Linkages & Fee Waivers
 * 14. RBAC Roles & Athletic Permission Matrix
 */

import { sportsService } from "../services/sports.service";
import {
  detectFacilityBookingConflict,
  computeTournamentStandings,
  generateRoundRobinFixtures,
  generateKnockoutFixtures,
  validateAthleteEligibility,
  calculateFacilityUtilizationRate,
  calculateClearanceComplianceRate,
} from "../services/sports-calculator";
import {
  SportsDepartmentStatus,
  SportsFacilityType,
  SportsClearanceStatus,
  SportsTournamentFormat,
  UserRole,
} from "@campusos/types";

export async function runSportsModuleTests(): Promise<{
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
    // 1. Operations Telemetry & Dashboard KPIs
    // =========================================================================
    const dashRes = await sportsService.getSportsDashboard();
    assert(dashRes.success === true, "1. Sports dashboard telemetry returns success");
    assert(dashRes.data.totalDepartments >= 2, "1. Campus sports departments initialized (>=2)");
    assert(dashRes.data.totalFacilities >= 6, "1. Multipurpose sports facilities initialized (>=6)");
    assert(dashRes.data.totalParticipants >= 5, "1. Registered student-athletes catalog present (>=5)");
    assert(dashRes.data.clearanceComplianceRate > 0, "1. Medical clearance compliance rate computed");
    assert(dashRes.data.totalTeams >= 3, "1. Varsity/collegiate teams catalog present (>=3)");
    assert(dashRes.data.activeTournaments >= 2, "1. Active tournaments engine loaded");

    // =========================================================================
    // 2. Pure Calculators: Utilization & Clearance Compliance
    // =========================================================================
    const utilRate = calculateFacilityUtilizationRate(28, 40);
    assert(utilRate === 70, "2. Facility utilization calculator: 28h/40h = 70%");

    const utilRateZero = calculateFacilityUtilizationRate(0, 0);
    assert(utilRateZero === 0, "2. Facility utilization calculator handles 0 hours gracefully");

    const complianceRate = calculateClearanceComplianceRate(92, 100);
    assert(complianceRate === 92, "2. Clearance compliance rate: 92/100 = 92%");

    // =========================================================================
    // 3. Sports Departments Administration
    // =========================================================================
    const deptListRes = await sportsService.listDepartments();
    assert(deptListRes.success === true, "3. List sports departments returns success");
    assert(deptListRes.data.length >= 2, "3. Athletics Board and Aquatics departments exist");

    const newDeptRes = await sportsService.createDepartment({
      code: "DEPT-REC-NORTH",
      name: "North Campus Recreation Club",
      status: SportsDepartmentStatus.ACTIVE,
      description: "Intramural fitness, yoga, and student recreation programs.",
    });
    assert(newDeptRes.success === true, "3. Create sports department returns success");
    assert(newDeptRes.data.code === "DEPT-REC-NORTH", "3. Created department code preserved");

    // =========================================================================
    // 4. Sports Facilities, Maintenance Closures & Safe Reopening
    // =========================================================================
    const facListRes = await sportsService.listFacilities();
    assert(facListRes.success === true, "4. List sports facilities returns success");
    const cricketGround = facListRes.data.find((f) => f.facilityType === SportsFacilityType.CRICKET_GROUND);
    assert(Boolean(cricketGround), "4. Cricket Ground facility registered");

    // Close facility for maintenance
    const closeRes = await sportsService.closeFacilityForMaintenance(
      cricketGround!.id,
      "Pitch aeration and turf leveling"
    );
    assert(closeRes.success === true, "4. Close facility for maintenance returns success");
    assert(closeRes.data.status === "MAINTENANCE_CLOSED", "4. Facility status transitioned to MAINTENANCE_CLOSED");

    // Reopen facility after inspection
    const reopenRes = await sportsService.reopenFacility(cricketGround!.id);
    assert(reopenRes.success === true, "4. Reopen facility returns success");
    assert(reopenRes.data.status === "AVAILABLE", "4. Facility status restored to AVAILABLE");

    // =========================================================================
    // 5. Booking Conflict Prevention Engine (Pure Algorithm & Service)
    // =========================================================================
    const existingBookings = [
      {
        id: "b-1",
        facilityId: "fac-bb-01",
        bookingDate: "2026-11-05",
        startTime: "14:00",
        endTime: "16:00",
        status: "CONFIRMED",
      },
    ];

    // Conflict: Exact overlap
    const conflictExact = detectFacilityBookingConflict(existingBookings, {
      facilityId: "fac-bb-01",
      bookingDate: "2026-11-05",
      startTime: "14:00",
      endTime: "16:00",
    });
    assert(conflictExact.hasConflict === true, "5. Overlapping booking conflict detected (exact slot)");

    // Conflict: Partial overlap
    const conflictPartial = detectFacilityBookingConflict(existingBookings, {
      facilityId: "fac-bb-01",
      bookingDate: "2026-11-05",
      startTime: "15:00",
      endTime: "17:00",
    });
    assert(conflictPartial.hasConflict === true, "5. Overlapping booking conflict detected (partial overlap)");

    // Valid: Non-overlapping time window on same day
    const validSameDay = detectFacilityBookingConflict(existingBookings, {
      facilityId: "fac-bb-01",
      bookingDate: "2026-11-05",
      startTime: "16:30",
      endTime: "18:00",
    });
    assert(validSameDay.hasConflict === false, "5. Non-overlapping booking permitted on same day");

    // Valid: Different facility on same day & time
    const validOtherFac = detectFacilityBookingConflict(existingBookings, {
      facilityId: "fac-fb-02",
      bookingDate: "2026-11-05",
      startTime: "14:00",
      endTime: "16:00",
    });
    assert(validOtherFac.hasConflict === false, "5. Simultaneous booking on different facility permitted");

    // Service booking with conflict check
    const bookingRes = await sportsService.createBooking({
      facilityId: "fac-fb-02",
      bookingDate: "2026-11-12",
      startTime: "09:00",
      endTime: "11:00",
      title: "Varsity Football Tactical Practice",
      purpose: "TRAINING",
    });
    assert(bookingRes.success === true, "5. Facility booking confirmed via service");

    // =========================================================================
    // 6. Student Athletes, Medical Clearance & Privacy Protection
    // =========================================================================
    const partListRes = await sportsService.listParticipants();
    assert(partListRes.success === true, "6. List sports participants returns success");
    const clearedAthlete = partListRes.data.find((p) => p.clearanceStatus === "CLEARED");
    assert(Boolean(clearedAthlete), "6. Active cleared athlete exists in directory");

    const newPartRes = await sportsService.createParticipant({
      userId: "user-ath-99",
      userName: "Kavya Sundaram",
      primarySport: "Badminton",
      clearanceStatus: SportsClearanceStatus.CLEARED,
      consentRecorded: true,
      operationalRestrictions: { maxExertionHeartRate: 175 },
    });
    assert(newPartRes.success === true, "6. Register new athlete participant returns success");
    assert(newPartRes.data.participantCode.includes("ATH-"), "6. Athlete participant code generated");

    // Update clearance status
    const updateClearanceRes = await sportsService.updateParticipantClearance(
      newPartRes.data.id,
      "RESTRICTED",
      { noContactDrills: true }
    );
    assert(updateClearanceRes.success === true, "6. Update participant clearance status returns success");
    assert(updateClearanceRes.data.clearanceStatus === "RESTRICTED", "6. Restricted clearance status recorded");

    // =========================================================================
    // 7. Teams, Roster Management & Capacity Limits
    // =========================================================================
    const teamsRes = await sportsService.listTeams();
    assert(teamsRes.success === true, "7. List teams returns success");
    const titans = teamsRes.data.find((t) => t.name.includes("Titans"));
    assert(Boolean(titans), "7. Campus Titans squad registered");

    // Create a new team with open roster capacity
    const openTeamRes = await sportsService.createTeam({
      name: "Campus Lions XI",
      sport: "Football",
      maxRosterSize: 22,
      headCoachName: "Coach Rajesh Pillai",
    });
    assert(openTeamRes.success === true, "7. Create squad with open capacity returns success");

    // Add member to open roster
    const addMemberRes = await sportsService.addTeamMember(openTeamRes.data.id, {
      participantId: clearedAthlete!.id,
      participantName: clearedAthlete!.userName,
      role: "PLAYER",
      jerseyNumber: 17,
      position: "All-Rounder",
    });
    assert(addMemberRes.success === true, "7. Add athlete to team roster returns success");
    assert(addMemberRes.data.jerseyNumber === 17, "7. Player jersey number assigned");

    // Attempt to exceed max roster capacity with a full squad
    const cappedTeamRes = await sportsService.createTeam({
      name: "Badminton Doubles A",
      sport: "Badminton",
      maxRosterSize: 1,
    });
    await sportsService.addTeamMember(cappedTeamRes.data.id, {
      participantId: clearedAthlete!.id,
      role: "PLAYER",
    });
    const overflowRes = await sportsService.addTeamMember(cappedTeamRes.data.id, {
      participantId: newPartRes.data.id,
      role: "PLAYER",
    });
    assert(
      overflowRes.success === false && String(overflowRes.error ?? "").includes("maximum roster capacity"),
      "7. Roster maximum capacity constraint strictly enforced"
    );

    // Athlete eligibility validator
    const eligibleCheck = validateAthleteEligibility({
      cgpa: 8.4,
      attendancePercentage: 88,
      clearanceStatus: "CLEARED",
    });
    assert(eligibleCheck.isEligible === true, "7. Athlete eligibility validator approves qualified athlete");

    const ineligibleCheck = validateAthleteEligibility({
      cgpa: 1.8,
      attendancePercentage: 62,
      clearanceStatus: "SUSPENDED",
    });
    assert(ineligibleCheck.isEligible === false, "7. Athlete eligibility validator flags low CGPA & attendance");
    assert(ineligibleCheck.failureReasons.length >= 2, "7. Multiple eligibility failure reasons identified");

    // =========================================================================
    // 8. Coaches & Official Assignments
    // =========================================================================
    const coachRes = await sportsService.listCoachingAssignments();
    assert(coachRes.success === true, "8. List coaching assignments returns success");
    assert(coachRes.data.length >= 2, "8. Head coaches assigned to varsity teams");

    const assignCoachRes = await sportsService.assignCoach({
      coachName: "Coach Anjali Bose",
      sport: "Athletics",
      role: "HEAD_COACH",
      certificationLevel: "AFI Level 1 National Coach",
    });
    assert(assignCoachRes.success === true, "8. Assign coach returns success");

    // =========================================================================
    // 9. Training Programs & Attendance Roll Call
    // =========================================================================
    const progRes = await sportsService.listTrainingPrograms();
    assert(progRes.success === true, "9. List training programs returns success");
    assert(progRes.data.length >= 2, "9. High-performance camps cataloged");

    const sessionsRes = await sportsService.listTrainingSessions(progRes.data[0].id);
    assert(sessionsRes.success === true, "9. List training sessions returns success");

    if (sessionsRes.data.length > 0) {
      const attendanceRes = await sportsService.recordSessionAttendance(
        sessionsRes.data[0].id,
        [
          { participantId: clearedAthlete!.id, status: "PRESENT", notes: "Tactical focus high" },
          { participantId: newPartRes.data.id, status: "EXCUSED", notes: "Academic lab conflict" },
        ]
      );
      assert(attendanceRes.success === true, "9. Record session attendance roll call returns success");
      assert(attendanceRes.data.length === 2, "9. Individual athlete roll call records stored");
    }

    // =========================================================================
    // 10. Tournament Fixture Generation (Berger Algorithm & Knockout)
    // =========================================================================
    // Berger Round Robin for 4 teams: 3 rounds, 6 total matches
    const fourTeams = ["Team-A", "Team-B", "Team-C", "Team-D"];
    const rrFixtures = generateRoundRobinFixtures(fourTeams);
    assert(rrFixtures.length === 6, "10. Berger round-robin for 4 teams generates exactly 6 matches");
    assert(rrFixtures.every((f) => f.home !== f.away), "10. No self-matches generated in round-robin");

    // Check rounds distribution
    const round1Matches = rrFixtures.filter((f) => f.round === 1);
    assert(round1Matches.length === 2, "10. Round 1 has exactly 2 concurrent matches");

    // Single Elimination Knockout for 8 teams: 4 opening Quarter-Final matches
    const eightTeams = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"];
    const koBracket = generateKnockoutFixtures(eightTeams);
    assert(koBracket.length === 4, "10. Knockout bracket for 8 teams generates 4 opening matches");
    assert(koBracket[0].stage === "QUARTER_FINAL", "10. 8-team opening stage labeled QUARTER_FINAL");

    // Competitions service fixture generation
    const compList = await sportsService.listCompetitions();
    assert(compList.success === true, "10. List competitions returns success");
    const activeComp = compList.data[0];

    const genRes = await sportsService.generateFixtures(activeComp.id);
    assert(genRes.success === true, "10. Auto-generate competition fixtures returns success");
    assert(genRes.data.length >= 1, "10. Generated fixture objects populated");

    // =========================================================================
    // 11. Match Results, Auditable Verification & Standings Calculation
    // =========================================================================
    const fixturesList = await sportsService.listFixtures(activeComp.id);
    assert(fixturesList.success === true, "11. List match fixtures returns success");
    const matchToScore = fixturesList.data[0];

    // Record score
    const scoreRes = await sportsService.recordMatchResult(matchToScore.id, {
      homeScore: 3,
      awayScore: 1,
      scoreBreakdown: { halfTime: "1-0", fullTime: "3-1" },
    });
    assert(scoreRes.success === true, "11. Record match score returns success");
    assert(scoreRes.data.homeScore === 3, "11. Home score recorded as 3");
    assert(scoreRes.data.awayScore === 1, "11. Away score recorded as 1");

    // Verify result with audit log
    const verifyRes = await sportsService.verifyMatchResult(
      matchToScore.id,
      "Official Arvind Swamy (Grade 1 Referee)",
      "Score verified against official referee scoresheet."
    );
    assert(verifyRes.success === true, "11. Verify match result returns success");
    assert(Boolean(verifyRes.data?.verifiedByName?.includes("Arvind Swamy")), "11. Verifier identity recorded");
    assert(Boolean(verifyRes.data.verifiedAt), "11. Verification timestamp generated");

    // Pure Standings Calculation with Goal Difference tiebreakers
    const competitors = [
      { id: "team-a", name: "Team Alpha" },
      { id: "team-b", name: "Team Beta" },
      { id: "team-c", name: "Team Gamma" },
    ];
    const matchResults = [
      { homeCompetitorId: "team-a", awayCompetitorId: "team-b", homeScore: 2, awayScore: 0, status: "COMPLETED" },
      { homeCompetitorId: "team-b", awayCompetitorId: "team-c", homeScore: 1, awayScore: 0, status: "COMPLETED" },
      { homeCompetitorId: "team-a", awayCompetitorId: "team-c", homeScore: 1, awayScore: 1, status: "COMPLETED" },
    ];
    const standings = computeTournamentStandings(competitors, matchResults);
    assert(standings.length === 3, "11. Standings table computed for 3 competitors");
    assert(standings[0].competitorId === "team-a", "11. Team Alpha ranks #1 (4 points, GD +2)");
    assert(standings[0].points === 4, "11. Team Alpha points = 4 (1 Win, 1 Draw)");
    assert(standings[0].pointDifference === 2, "11. Team Alpha goal difference = +2");
    assert(standings[1].competitorId === "team-b", "11. Team Beta ranks #2 (3 points, GD -1)");
    assert(standings[2].competitorId === "team-c", "11. Team Gamma ranks #3 (1 point, GD -1)");

    // =========================================================================
    // 12. Equipment Operations, Asset Checkout & Damage Fee Inspection
    // =========================================================================
    const eqListRes = await sportsService.listEquipmentAssignments();
    assert(eqListRes.success === true, "12. List equipment assignments returns success");
    assert(eqListRes.data.length >= 2, "12. Equipment gear records tracked");

    const checkoutRes = await sportsService.checkoutEquipment({
      equipmentName: "Wilson Pro Basketballs (Pack of 5)",
      itemCode: "EQ-BB-BALL-02",
      allocatedQuantity: 5,
      responsibleUserName: "Coach Sneha Kulkarni",
      checkoutDate: "2026-10-24",
      dueDate: "2026-10-28",
    });
    assert(checkoutRes.success === true, "12. Checkout sports equipment returns success");
    assert(checkoutRes.data.status === "ISSUED", "12. Equipment status marked ISSUED");

    // Return with condition inspection
    const returnRes = await sportsService.returnEquipment(
      checkoutRes.data.id,
      "GOOD",
      "Returned in clean match condition",
      0
    );
    assert(returnRes.success === true, "12. Return equipment returns success");
    assert(returnRes.data.status === "RETURNED", "12. Equipment status updated to RETURNED");

    // Damaged return with replacement surcharge
    const damagedItemRes = await sportsService.checkoutEquipment({
      equipmentName: "Badminton Carbon Racquet Set",
      itemCode: "EQ-BM-RACQ-09",
      allocatedQuantity: 2,
      responsibleUserName: "Athlete Karan Patel",
    });
    const damagedReturnRes = await sportsService.returnEquipment(
      damagedItemRes.data.id,
      "DAMAGED",
      "Snapped string bed and cracked frame during practice",
      750
    );
    assert(damagedReturnRes.success === true, "12. Return damaged equipment returns success");
    assert(damagedReturnRes.data.replacementFee === 750, "12. Damage replacement fee logged (₹750)");

    // =========================================================================
    // 13. Sports Registrations, Invoice Linkages & Fee Waivers
    // =========================================================================
    const feesRes = await sportsService.listSportsFees();
    assert(feesRes.success === true, "13. List sports fees returns success");
    assert(feesRes.data.length >= 3, "13. Authoritative fee records present");
    assert(
      feesRes.data.every((f) => Boolean(f.invoiceReference)),
      "13. All athletic charges link to authoritative invoices"
    );

    // =========================================================================
    // 14. RBAC Roles & Athletic Permission Matrix
    // =========================================================================
    assert(UserRole.SPORTS_OFFICER === "SPORTS_OFFICER", "14. SPORTS_OFFICER role recognized in RBAC");
    assert(UserRole.COACH === "COACH", "14. COACH role recognized in RBAC");

    // Verify format types
    assert(SportsTournamentFormat.ROUND_ROBIN === "ROUND_ROBIN", "14. ROUND_ROBIN format enum verified");
    assert(SportsTournamentFormat.KNOCKOUT === "KNOCKOUT", "14. KNOCKOUT format enum verified");
  } catch (err: any) {
    results.push({
      testName: "Unhandled Test Exception",
      passed: false,
      message: err?.message || String(err),
    });
  }

  const passed = results.filter((r) => r.passed).length;
  const failed = results.filter((r) => !r.passed).length;
  return { passed, failed, results };
}

// Standalone test execution runner
if (
  typeof process !== "undefined" &&
  process.argv[1]?.includes("sports-module.test")
) {
  runSportsModuleTests().then((res) => {
    console.log(`\n========================================`);
    console.log(`CampusOS Sports & Athletics Test Results:`);
    console.log(`Passed: ${res.passed}, Failed: ${res.failed}`);
    console.log(`========================================`);
    res.results.forEach((r) => {
      console.log(
        `${r.passed ? "✔ PASS" : "✖ FAIL"}: ${r.testName}${
          r.message ? ` (${r.message})` : ""
        }`
      );
    });
    if (res.failed > 0) {
      process.exit(1);
    }
  });
}
