/**
 * CampusOS Campus Operations & Engagement Module — Comprehensive Test Suite
 * Validates domain contracts, event lifecycles (create draft, publish, open registration, cancel),
 * registration capacity validation, attendance marking & centralized calculators,
 * club membership approval/rejection workflows, role assignment,
 * targeted announcements & audience calculations, notification inbox & preference updates,
 * global search integration, and RBAC matrix.
 */

import { campusService } from "../services/campus.service";
import {
  calculateEventAttendanceRate,
  calculateEventCapacityUsage,
  calculateRegistrationRate,
  calculateClubMembershipCount,
  calculateUnreadNotificationCount,
  calculateAudienceSize,
  calculateDeliveryRate,
} from "../services/campus-calculator";
import { searchService } from "../services/search.service";
import { DEMO_PERSONAS } from "../mocks/auth.mock";

export async function runCampusModuleTests(): Promise<{
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
    // 1. Campus Dashboard & Telemetry
    // ==========================================
    const summaryRes = await campusService.getCampusSummary();
    assert(
      summaryRes.success === true,
      "1. Campus dashboard summary returns success",
    );
    assert(
      summaryRes.data.activeEventsCount >= 3,
      "1. Active events count is valid",
    );
    assert(
      summaryRes.data.activeClubsCount >= 5,
      "1. Active clubs count is tracked",
    );
    assert(
      summaryRes.data.registeredParticipantsCount > 0,
      "1. Registered participants tracked",
    );
    assert(
      summaryRes.data.unreadNotificationsCount >= 0,
      "1. Unread notifications tracked",
    );

    // ==========================================
    // 2. Centralized Pure Calculators
    // ==========================================
    const attRate1 = calculateEventAttendanceRate(126, 150);
    assert(
      attRate1 === 84,
      `2. calculateEventAttendanceRate(126, 150) = 84% (got ${attRate1})`,
    );

    const attRateZero = calculateEventAttendanceRate(0, 100);
    assert(
      attRateZero === 0,
      "2. calculateEventAttendanceRate handles zero present",
    );

    const capUsage = calculateEventCapacityUsage(180, 200);
    assert(
      capUsage === 90,
      `2. calculateEventCapacityUsage(180, 200) = 90% (got ${capUsage})`,
    );

    const regRate = calculateRegistrationRate(50, 100);
    assert(
      regRate === 50,
      `2. calculateRegistrationRate(50, 100) = 50% (got ${regRate})`,
    );

    const audAll = calculateAudienceSize({ type: "ALL_USERS" });
    assert(
      audAll === 4750,
      `2. calculateAudienceSize(ALL_USERS) = 4750 (got ${audAll})`,
    );

    const audDept = calculateAudienceSize({
      type: "SPECIFIC_DEPARTMENT",
      departmentName: "CSE",
    });
    assert(
      audDept === 525,
      `2. calculateAudienceSize(SPECIFIC_DEPARTMENT) = 525 (got ${audDept})`,
    );

    const delivRate = calculateDeliveryRate(980, 1000);
    assert(
      delivRate === 98,
      `2. calculateDeliveryRate(980, 1000) = 98% (got ${delivRate})`,
    );

    const mockClubMembers = [
      {
        id: "1",
        clubId: "c",
        studentId: "s1",
        studentName: "A",
        rollNumber: "1",
        email: "",
        department: "",
        program: "",
        semester: 1,
        role: "MEMBER" as const,
        status: "ACTIVE" as const,
        joinedDate: "",
        timeline: [],
      },
      {
        id: "2",
        clubId: "c",
        studentId: "s2",
        studentName: "B",
        rollNumber: "2",
        email: "",
        department: "",
        program: "",
        semester: 1,
        role: "MEMBER" as const,
        status: "ACTIVE" as const,
        joinedDate: "",
        timeline: [],
      },
      {
        id: "3",
        clubId: "c",
        studentId: "s3",
        studentName: "C",
        rollNumber: "3",
        email: "",
        department: "",
        program: "",
        semester: 1,
        role: "MEMBER" as const,
        status: "PENDING" as const,
        joinedDate: "",
        timeline: [],
      },
    ];
    const memberStats = calculateClubMembershipCount(mockClubMembers);
    assert(
      memberStats.active === 2,
      "2. Club membership calculator counts active",
    );
    assert(
      memberStats.pending === 1,
      "2. Club membership calculator counts pending",
    );
    assert(
      memberStats.total === 3,
      "2. Club membership calculator counts total",
    );

    // ==========================================
    // 3. Event Creation Workflow (Save as DRAFT)
    // ==========================================
    const newEventRes = await campusService.createEvent({
      title: "Autonomous Drone Swarm Challenge",
      category: "Technical",
      description: "Inter-collegiate autonomous drone fleet obstacle course.",
      organizer: "Autonomous Robotics & Embedded Systems Club",
      organizerType: "CLUB",
      clubId: "club-robotics",
      startDate: "2026-11-12",
      endDate: "2026-11-12",
      startTime: "10:00 AM",
      endTime: "05:00 PM",
      venue: "Main Indoor Sports Complex & CS Arena",
      venueId: "ven-03",
      capacity: 100,
      requiresRegistration: true,
      registrationOpenDate: "2026-10-20",
      registrationCloseDate: "2026-11-10",
      allowWaitlist: true,
      requiresAttendance: true,
      targetAudience: {
        type: "ALL_STUDENTS",
        estimatedCount: 4200,
      },
      createdBy: "Dr. Ananya Mukherjee",
    });

    assert(newEventRes.success === true, "3. Event creation returns success");
    assert(
      newEventRes.data.status === "DRAFT",
      "3. Event strictly created in DRAFT status",
    );
    assert(
      newEventRes.data.timeline.length >= 1,
      "3. Audit timeline entry recorded for creation",
    );

    // ==========================================
    // 4. Event Publication Lifecycle
    // ==========================================
    const pubRes = await campusService.publishEvent(
      newEventRes.data.id,
      "Dean Academics",
    );
    assert(pubRes.success === true, "4. Event publication returns success");
    assert(
      pubRes.data.status === "REGISTRATION_OPEN",
      "4. Event status transitioned to REGISTRATION_OPEN",
    );
    assert(
      pubRes.data.publishedAt !== undefined,
      "4. Published timestamp recorded",
    );

    // ==========================================
    // 5. Event Registration & Capacity Validation
    // ==========================================
    const testStudent = {
      id: "stu-test-99",
      name: "Tanya Sen",
      rollNumber: "CS24B099",
      email: "tanya.sen@student.campusos.edu",
      department: "Computer Science & Engineering",
      program: "B.Tech Computer Science",
      semester: 3,
    };

    const regRes = await campusService.registerForEvent(
      newEventRes.data.id,
      testStudent,
    );
    assert(
      regRes.success === true,
      "5. Student registers for event successfully",
    );
    assert(
      regRes.data.status === "CONFIRMED",
      "5. Registration initial status is CONFIRMED",
    );
    assert(
      regRes.data.ticketCode.startsWith("TKT-"),
      "5. Entry ticket code generated",
    );

    // Duplicate Registration Prevention
    const dupRegRes = await campusService.registerForEvent(
      newEventRes.data.id,
      testStudent,
    );
    assert(
      dupRegRes.success === false,
      "5. Duplicate registration rejected with error",
    );

    // Event Cancellation
    const cancelEvtRes = await campusService.cancelEvent(
      newEventRes.data.id,
      "Weather hazard",
      "Dean Academics",
    );
    assert(cancelEvtRes.success === true, "5. Event cancellation succeeds");
    assert(
      cancelEvtRes.data.status === "CANCELLED",
      "5. Event status is CANCELLED",
    );

    // Registration closure on cancelled event
    const regOnCancelled = await campusService.registerForEvent(
      newEventRes.data.id,
      {
        ...testStudent,
        id: "stu-test-100",
      },
    );
    assert(
      regOnCancelled.success === false,
      "5. Registration closed on cancelled event",
    );

    // ==========================================
    // 6. Event Attendance Marking
    // ==========================================
    const attListRes = await campusService.getEventAttendance("evt-06");
    assert(
      attListRes.success === true,
      "6. getEventAttendance returns success",
    );
    assert(
      attListRes.data.summary.totalRegistered > 0,
      "6. Attendance summary contains registered count",
    );
    assert(
      attListRes.data.summary.attendanceRate > 0,
      "6. Attendance rate calculated in summary",
    );

    // Mark present
    const markRes = await campusService.markEventAttendance(
      "evt-06",
      [{ studentId: "stu-001", status: "PRESENT", remarks: "Verified" }],
      "Coordinator",
    );
    assert(
      markRes.success === true,
      "6. Mark event attendance returns success",
    );
    assert(markRes.data.updatedCount === 1, "6. Exactly 1 record marked");

    // Bulk attendance marking
    const bulkRes = await campusService.bulkMarkAttendance(
      "evt-06",
      "PRESENT",
      ["stu-001", "stu-002"],
      "Chief Coordinator",
    );
    assert(bulkRes.success === true, "6. Bulk attendance marking succeeds");

    // ==========================================
    // 7. Clubs & Membership Workflows
    // ==========================================
    const clubsRes = await campusService.getClubs();
    assert(clubsRes.success === true, "7. getClubs returns success");
    assert(clubsRes.data.length >= 5, "7. Active clubs loaded in directory");

    const clubDetail = await campusService.getClubById("club-ace");
    assert(clubDetail.success === true, "7. getClubById returns success");
    assert(clubDetail.data?.club.code === "ACE", "7. ACE Club detail loaded");
    assert(
      (clubDetail.data?.members.length ?? 0) > 0,
      "7. Club member roster loaded",
    );
    assert(
      (clubDetail.data?.events.length ?? 0) > 0,
      "7. Club referenced events loaded",
    );

    // Student Requests Membership
    const joinRes = await campusService.requestMembership("club-robotics", {
      id: "stu-join-01",
      name: "Pranav Pillai",
      rollNumber: "EC24B019",
      email: "pranav.p@student.campusos.edu",
      department: "ECE",
      program: "B.Tech ECE",
      semester: 3,
    });
    assert(joinRes.success === true, "7. Membership request submitted");
    assert(
      joinRes.data.status === "PENDING",
      "7. Student join request initially PENDING",
    );

    // Coordinator Approves Membership
    const approveRes = await campusService.approveMembership(
      "club-robotics",
      joinRes.data.id,
      "Dr. Ananya Mukherjee",
    );
    assert(approveRes.success === true, "7. Coordinator approves membership");
    assert(
      approveRes.data.status === "ACTIVE",
      "7. Membership status updated to ACTIVE",
    );

    // Coordinator Reassigns / Elevates Role
    const roleRes = await campusService.updateMemberRole(
      "club-robotics",
      joinRes.data.id,
      "SECRETARY",
      "Advisor",
    );
    assert(roleRes.success === true, "7. Member role elevated successfully");
    assert(roleRes.data.role === "SECRETARY", "7. Member role is SECRETARY");

    // Student Leaves Club
    const leaveRes = await campusService.leaveClub(
      "club-robotics",
      joinRes.data.id,
      "Pranav Pillai",
    );
    assert(leaveRes.success === true, "7. Member leaves club successfully");
    assert(leaveRes.data.status === "LEFT", "7. Status updated to LEFT");

    // ==========================================
    // 8. Announcements & Targeted Communication
    // ==========================================
    const ancRes = await campusService.getAnnouncements();
    assert(ancRes.success === true, "8. getAnnouncements returns success");
    assert(ancRes.data.length >= 3, "8. Announcements present on board");

    const newAnc = await campusService.createAnnouncement({
      title: "Campus Wi-Fi Maintenance Window Notice",
      summary: "High-speed optical network upgrades this Friday.",
      content:
        "All campus network access points in Academic Blocks A & B will be migrated to 10Gbps fiber.",
      category: "GENERAL",
      priority: "NORMAL",
      publisher: "Network Operations Center",
      publisherRole: "IT Directorate",
      audience: {
        type: "ALL_USERS",
        estimatedRecipientCount: 4750,
        description: "Entire campus community",
      },
      isPinned: false,
      publishDate: "2026-10-18 10:00 AM",
    });
    assert(newAnc.success === true, "8. Announcement creation returns success");
    assert(newAnc.data.status === "DRAFT", "8. Announcement created as DRAFT");

    // Publish announcement
    const pubAnc = await campusService.publishAnnouncement(
      newAnc.data.id,
      "Registrar",
    );
    assert(pubAnc.success === true, "8. Publish announcement returns success");
    assert(
      pubAnc.data.status === "PUBLISHED",
      "8. Announcement status is PUBLISHED",
    );

    // Archive announcement
    const arcAnc = await campusService.archiveAnnouncement(
      newAnc.data.id,
      "Registrar",
    );
    assert(arcAnc.success === true, "8. Archive announcement returns success");
    assert(
      arcAnc.data.status === "ARCHIVED",
      "8. Announcement status is ARCHIVED",
    );

    // ==========================================
    // 9. Notification Inbox & Deep Links
    // ==========================================
    const notifs = await campusService.getNotifications();
    assert(notifs.success === true, "9. getNotifications returns success");
    assert(notifs.data.length >= 4, "9. Notifications inbox loaded");

    const unreadBefore = calculateUnreadNotificationCount(notifs.data);
    assert(unreadBefore >= 1, "9. Unread notifications exist in dataset");

    // Mark single notification read
    const firstUnread = notifs.data.find((n) => n.status === "UNREAD");
    if (firstUnread) {
      const readRes = await campusService.markNotificationRead(firstUnread.id);
      assert(
        readRes.success === true,
        "9. markNotificationRead returns success",
      );
      assert(readRes.data.status === "READ", "9. Notification status is READ");
    }

    // Mark all read
    const markAllRes = await campusService.markAllNotificationsRead();
    assert(
      markAllRes.success === true,
      "9. markAllNotificationsRead returns success",
    );
    assert(
      markAllRes.data.count >= 0,
      "9. Count of marked notifications returned",
    );

    // Deep link verification
    const invoiceNotif = notifs.data.find(
      (n) => n.relatedEntityType === "INVOICE",
    );
    assert(
      invoiceNotif !== undefined &&
        invoiceNotif.actionUrl?.includes("/app/finance"),
      "9. Finance notification deep-links to /app/finance",
    );

    const eventNotif = notifs.data.find((n) => n.relatedEntityType === "EVENT");
    assert(
      eventNotif !== undefined &&
        eventNotif.actionUrl?.includes("/app/campus/events"),
      "9. Event notification deep-links to /app/campus/events",
    );

    // ==========================================
    // 10. Communication Preferences & History
    // ==========================================
    const prefRes = await campusService.getNotificationPreferences();
    assert(
      prefRes.success === true,
      "10. getNotificationPreferences returns success",
    );
    assert(
      prefRes.data.length >= 6,
      "10. All communication categories covered",
    );

    const updatedPrefs = prefRes.data.map((p) =>
      p.category === "EVENT" ? { ...p, sms: true } : p,
    );
    const savePrefRes =
      await campusService.updateNotificationPreferences(updatedPrefs);
    assert(
      savePrefRes.success === true,
      "10. updateNotificationPreferences returns success",
    );
    assert(
      savePrefRes.data.find((p) => p.category === "EVENT")?.sms === true,
      "10. Preference toggle persisted in memory",
    );

    const histRes = await campusService.getCommunicationHistory();
    assert(
      histRes.success === true,
      "10. getCommunicationHistory returns success",
    );
    assert(
      histRes.data.length >= 3,
      "10. Communication records tracked with channel breakdown",
    );

    // ==========================================
    // 11. Global Search Deep Links
    // ==========================================
    const searchRes = await searchService.search("HackCampus");
    assert(
      searchRes.success === true,
      "11. Global search for HackCampus returns success",
    );
    assert(
      searchRes.data.some((item) => item.href.includes("/app/campus/events")),
      "11. Search result deep-links to /app/campus/events route",
    );

    const clubSearch = await searchService.search("ACE");
    assert(
      clubSearch.data.some((item) => item.href.includes("/app/campus/clubs")),
      "11. Club search deep-links to /app/campus/clubs route",
    );

    // ==========================================
    // 12. Permissions Matrix Verification (Section 38 & 45)
    // ==========================================
    const superAdmin = DEMO_PERSONAS.find((p) => p.role === "SUPER_ADMIN");
    const hod = DEMO_PERSONAS.find((p) => p.role === "HOD");
    const faculty = DEMO_PERSONAS.find((p) => p.role === "FACULTY");
    const student = DEMO_PERSONAS.find((p) => p.role === "STUDENT");

    assert(
      superAdmin?.permissions.includes("*"),
      "12. Super Admin holds wildcard permissions",
    );
    assert(
      hod?.permissions.includes("campus.publish_events"),
      "12. HOD authorized to publish events",
    );
    assert(
      faculty?.permissions.includes("campus.manage_event_attendance"),
      "12. Faculty authorized to mark attendance",
    );

    // Student constraints
    assert(
      student?.permissions.includes("campus.register_events"),
      "12. Student authorized to register for events",
    );
    assert(
      !student?.permissions.includes("campus.publish_events"),
      "12. Student strictly prohibited from publishing events",
    );
    assert(
      !student?.permissions.includes("campus.manage_event_attendance"),
      "12. Student strictly prohibited from marking attendance",
    );
    assert(
      !student?.permissions.includes("campus.publish_announcements"),
      "12. Student strictly prohibited from publishing announcements",
    );
  } catch (err: any) {
    results.push({
      testName: "Global Execution Catch",
      passed: false,
      message: err.message,
    });
  }

  const passed = results.filter((r) => r.passed).length;
  const failed = results.filter((r) => !r.passed).length;

  return { passed, failed, results };
}

if (
  typeof process !== "undefined" &&
  process.argv[1]?.includes("campus-module.test")
) {
  runCampusModuleTests().then((res) => {
    console.log(`\n==============================================`);
    console.log(`CampusOS Campus Management Module Test Results:`);
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
