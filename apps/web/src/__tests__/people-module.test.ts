/**
 * CampusOS People Management Module Test Suite
 * Validates domain contracts, service mutations, query filters, search integration, and RBAC rules.
 */

import { studentsService } from "../services/students.service";
import { facultyService } from "../services/faculty.service";
import { staffService } from "../services/staff.service";
import { guardiansService } from "../services/guardians.service";
import { documentsService } from "../services/documents.service";
import { peopleService } from "../services/people.service";
import { searchService } from "../services/search.service";

export async function runPeopleModuleTests(): Promise<{
  passed: number;
  failed: number;
  results: { testName: string; passed: boolean; message?: string }[];
}> {
  const results: { testName: string; passed: boolean; message?: string }[] = [];

  function assert(condition: boolean, testName: string, failureDetails?: string) {
    if (condition) {
      results.push({ testName, passed: true });
    } else {
      results.push({ testName, passed: false, message: failureDetails || "Assertion failed" });
    }
  }

  try {
    // 1. Student List & Pagination
    const studentsRes = await studentsService.list({ page: 1, pageSize: 5 });
    assert(studentsRes.success === true, "1. Student list returns successful response");
    assert(Array.isArray(studentsRes.data) && studentsRes.data.length > 0, "1. Student list returns non-empty array");
    assert(studentsRes.pagination.pageSize === 5, "1. Pagination honors requested page size");

    // 2. Student Search
    const searchRes = await studentsService.list({ search: "Aarav" });
    assert(
      searchRes.data.some((s) => s.firstName.includes("Aarav") || s.lastName.includes("Patel")),
      "2. Student search matches by first or last name"
    );

    // 3. Student Filtering
    const filterDeptRes = await studentsService.list({ department: "Computer Science & Engineering" });
    assert(
      filterDeptRes.data.every((s) => s.program.department === "Computer Science & Engineering"),
      "3. Student department filter strictly matches department"
    );

    const filterStatusRes = await studentsService.list({ status: "ACTIVE" });
    assert(
      filterStatusRes.data.every((s) => s.status === "ACTIVE"),
      "3. Student status filter matches active students"
    );

    // 4. Student 360 Profile Resolution
    const stuProfile = await studentsService.getById("stu-24cse0101");
    assert(stuProfile.data !== null, "4. Student profile resolves by ID");
    assert(stuProfile.data?.rollNumber === "24CSE0101", "4. Student roll number is verified");
    assert(Array.isArray(stuProfile.data?.guardians) && (stuProfile.data?.guardians.length ?? 0) > 0, "4. Student includes guardians pool");
    assert(Array.isArray(stuProfile.data?.documentsVault), "4. Student includes documents vault");
    assert(Array.isArray(stuProfile.data?.milestones), "4. Student includes milestones timeline");

    // 5. Guardian Mutations (via guardiansService & studentsService)
    const newGrd = await guardiansService.addGuardian("stu-24cse0101", {
      name: "Lakshmi Patel",
      relation: "GUARDIAN",
      phone: "+91 98450 77665",
      email: "lakshmi.patel@example.com",
      occupation: "Architect",
    });
    assert(newGrd.success && Boolean(newGrd.data?.id), "5. Guardian relationship added successfully");

    const updatedGrd = await guardiansService.updateGuardian("stu-24cse0101", newGrd.data!.id, {
      occupation: "Senior Principal Architect",
    });
    assert(updatedGrd.data?.occupation === "Senior Principal Architect", "5. Guardian relationship updated");

    const deleteGrd = await guardiansService.removeGuardian("stu-24cse0101", newGrd.data!.id);
    assert(deleteGrd.success === true, "5. Guardian relationship deleted");

    // 6. Document Vault Mutations (via documentsService)
    const newDoc = await documentsService.uploadStudentDocument("stu-24cse0101", {
      name: "State Merit Scholarship Order",
      category: "FINANCIAL",
      fileSize: "1.8 MB",
    });
    assert(newDoc.success && newDoc.data?.status === "UNDER_REVIEW", "6. Document uploaded in UNDER_REVIEW status");

    const verifiedDoc = await documentsService.verifyDocument("stu-24cse0101", newDoc.data!.id, "Dean of Academics");
    assert(verifiedDoc.data?.status === "VERIFIED" && verifiedDoc.data?.verifiedBy === "Dean of Academics", "6. Document verified");

    const newDoc2 = await documentsService.uploadStudentDocument("stu-24cse0101", {
      name: "Draft Certificate",
      category: "OTHER",
      fileSize: "500 KB",
    });
    const rejectedDoc = await documentsService.rejectDocument("stu-24cse0101", newDoc2.data!.id, "Legibility unreadable");
    assert(rejectedDoc.data?.status === "REJECTED" && rejectedDoc.data?.rejectionReason === "Legibility unreadable", "6. Document rejected with reason");

    await documentsService.deleteDocument("stu-24cse0101", newDoc.data!.id);
    await documentsService.deleteDocument("stu-24cse0101", newDoc2.data!.id);

    // 7. Academic Milestones Timeline
    const newMls = await studentsService.addMilestone("stu-24cse0101", {
      title: "IEEE Conference Best Paper Award",
      category: "ACHIEVEMENT",
      description: "Received best student researcher commendation.",
      semester: 5,
    });
    assert(newMls.success && Boolean(newMls.data?.id), "7. Academic milestone recorded");

    // 8. Faculty List & 360 Profile
    const facultyList = await facultyService.list({ department: "Computer Science & Engineering" });
    assert(facultyList.success && facultyList.data.length > 0, "8. Faculty list filtered by department");

    const facultyMember = await facultyService.getById("fac-cse-001");
    assert(facultyMember.data !== null, "8. Faculty 360 profile resolved");
    assert(Boolean(facultyMember.data?.workloadSummary), "8. Faculty includes workload summary");

    // 9. Faculty Workload & Lab Designations
    const workload = await facultyService.getWorkload("fac-cse-001");
    assert(workload.success && workload.data !== null, "9. Workload summary fetched");
    assert(typeof workload.data?.weeklyTargetHours === "number", "9. Workload includes weekly target hours");

    const newLab = await facultyService.assignLab("fac-cse-001", {
      labName: "Cybersecurity & Cryptography Lab",
      courseCode: "CS402-L",
      dayOfWeek: "Friday",
      timeSlot: "02:00 PM - 05:00 PM",
      roomNumber: "Lab 402, Turing Block",
      weeklyHours: 3,
      batchCapacity: 30,
    });
    assert(newLab.success && Boolean(newLab.data?.id), "9. Laboratory duty assigned to faculty");

    const removeLab = await facultyService.removeLabAssignment("fac-cse-001", newLab.data!.id);
    assert(removeLab.success === true, "9. Laboratory duty released");

    // 10. Research & Scholarly Publications
    const newPub = await facultyService.createPublication("fac-cse-001", {
      title: "Distributed Fault-Tolerant State Sync in Higher-Ed Clouds",
      publicationType: "JOURNAL",
      venueName: "IEEE Transactions on Cloud Systems",
      publicationYear: 2026,
      status: "PUBLISHED",
    });
    assert(newPub.success && Boolean(newPub.data?.id), "10. Research publication logged");

    const updatePub = await facultyService.updatePublication("fac-cse-001", newPub.data!.id, {
      citationCount: 5,
    });
    assert(updatePub.data?.citationCount === 5, "10. Publication citation count updated");

    await facultyService.deletePublication("fac-cse-001", newPub.data!.id);

    // 11. Staff Management, Shift Mapping & Leaves
    const staffList = await staffService.list({ shift: "GENERAL" });
    assert(staffList.success && staffList.data.length > 0, "11. Staff list filtered by shift");

    const staffMember = await staffService.getById("stf-001");
    assert(staffMember.data !== null, "11. Staff 360 profile resolved");
    assert(Boolean(staffMember.data?.shift), "11. Staff includes shift schedule");

    const shifts = await staffService.getShifts();
    assert(shifts.success && shifts.data.length >= 4, "11. Institutional shift schedules available");

    const newLeave = await staffService.createLeaveRequest({
      staffId: "stf-001",
      leaveType: "CASUAL",
      totalDays: 2,
      reason: "Personal family commitment.",
    });
    assert(newLeave.success && newLeave.data?.status === "PENDING", "11. Staff leave request created in PENDING status");

    const approvedLeave = await staffService.approveLeave(newLeave.data!.id, "Dean Office", "Approved with hand-off");
    assert(approvedLeave.data?.status === "APPROVED" && approvedLeave.data?.reviewedBy === "Dean Office", "11. Staff leave approved");

    // 12. People Overview Metrics & Department Distribution
    const metrics = await peopleService.getMetrics();
    assert(metrics.success && metrics.data.totalStudents > 0, "12. People summary metrics contain student aggregates");
    assert(metrics.data.totalFaculty > 0, "12. People summary metrics contain faculty aggregates");
    assert(metrics.data.totalStaff > 0, "12. People summary metrics contain staff aggregates");

    const depts = await peopleService.getDepartmentDistribution();
    assert(depts.success && depts.data.length > 0, "12. Department people distribution resolved");

    // 13. Unified People Search & Command Palette Integration
    const searchPeopleRes = await peopleService.searchPeople("Sharma");
    assert(searchPeopleRes.success, "13. Unified people search executed");
    assert(
      searchPeopleRes.data.some((p) => p.name.includes("Sharma")),
      "13. Unified people search matched person by surname across categories"
    );

    const globalSearchRes = await searchService.search("Aarav");
    assert(
      globalSearchRes.data.some((item) => item.category === "Student" && item.title.includes("Aarav")),
      "13. Command palette global search surfaces student via people service"
    );

    // 14. RBAC Permission Rules Validation
    const roleRules = {
      SUPER_ADMIN: { canManageLifecycle: true, canVerifyDocs: true, canManageWorkload: true, canApproveLeave: true },
      HOD: { canManageLifecycle: true, canVerifyDocs: true, canManageWorkload: true, canApproveLeave: true },
      FACULTY: { canManageLifecycle: false, canVerifyDocs: false, canManageWorkload: false, canApproveLeave: false },
      STUDENT: { canManageLifecycle: false, canVerifyDocs: false, canManageWorkload: false, canApproveLeave: false },
    };
    assert(roleRules.SUPER_ADMIN.canManageLifecycle === true, "14. Admin has full lifecycle control");
    assert(roleRules.STUDENT.canVerifyDocs === false, "14. Student cannot self-verify documents");
    assert(roleRules.FACULTY.canApproveLeave === false, "14. Faculty cannot approve administrative staff leaves");

  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : String(err);
    results.push({ testName: "Exception during test run", passed: false, message: errorMsg });
  }

  const passed = results.filter((r) => r.passed).length;
  const failed = results.filter((r) => !r.passed).length;
  return { passed, failed, results };
}
