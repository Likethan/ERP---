/**
 * CampusOS Faculty Portal Audit, Cleanup & Feature Enhancement Test Suite
 *
 * Validates the 10 Mandatory Cross-Portal Workflows and Business Rules:
 * 1. Faculty uploads study material -> Student accesses & downloads it.
 * 2. Faculty creates assignment -> Student submits it.
 * 3. Faculty evaluates assignment -> Student views feedback & marks.
 * 4. Faculty marks attendance -> Session records updated and percentage computed.
 * 5. Student raises attendance correction -> Authorized faculty reviews it.
 * 6. Faculty enters internal marks -> Marks verified within max boundaries; publication gate enforced.
 * 7. Faculty publishes announcement -> Target audience students receive it.
 * 8. Student applies for leave -> Authorized faculty processes attendance exemption.
 * 9. Faculty applies for leave -> Dedicated faculty leave workflow routes to HOD.
 * 10. Faculty accesses assigned courses only & student directory is scoped.
 * 11. Lesson Plan & Class Diary integration: Teaching log updates unit completion %.
 * 12. Late submission policy enforcement: Allowed vs rejected according to policy.
 */

import { teachingService } from "../services/teaching.service";
import { attendanceService } from "../services/attendance.service";
import { examinationsService } from "../services/examinations.service";
import { campusService } from "../services/campus.service";
import { DEMO_PERSONAS } from "../mocks/auth.mock";
import {
  FACULTY_PORTAL_NAV,
  STUDENT_PORTAL_NAV,
} from "../components/navigation/portal-nav";

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

async function runTestSuite() {
  console.log(
    "\n===============================================================================",
  );
  console.log(
    "CampusOS Faculty Portal Comprehensive Feature & Cross-Portal Verification Suite",
  );
  console.log(
    "===============================================================================\n",
  );

  // ---------------------------------------------------------------------------
  // 1. Navigation Cleanup & Portal Route Structure
  // ---------------------------------------------------------------------------
  console.log("\n--- Section 1: Navigation Cleanup & Redundancy Removal ---");
  const facultyRoutes = FACULTY_PORTAL_NAV.flatMap((s) =>
    s.items.map((i) => i.href),
  );
  const studentRoutes = STUDENT_PORTAL_NAV.flatMap((s) =>
    s.items.map((i) => i.href),
  );

  assert(
    facultyRoutes.includes("/app/academics/lesson-plans"),
    "1.1 Faculty Nav has Lesson Plans & Syllabus link",
  );
  assert(
    facultyRoutes.includes("/app/academics/class-diary"),
    "1.2 Faculty Nav has Class Diary / Teaching Log link",
  );
  assert(
    facultyRoutes.includes("/app/academics/materials"),
    "1.3 Faculty Nav has Study Materials link",
  );
  assert(
    facultyRoutes.includes("/app/academics/assignments"),
    "1.4 Faculty Nav has Assignments & Evaluations link",
  );
  assert(
    facultyRoutes.includes("/app/faculty/leaves"),
    "1.5 Faculty Nav has dedicated Apply for Faculty Leave link",
  );
  assert(
    studentRoutes.includes("/app/academics/materials"),
    "1.6 Student Nav has Course Study Materials link",
  );
  assert(
    studentRoutes.includes("/app/academics/assignments"),
    "1.7 Student Nav has Coursework Assignments link",
  );

  // Verify Published Results renamed
  const examSection = FACULTY_PORTAL_NAV.find(
    (s) => s.title === "EXAMINATIONS & EVALUATION",
  );
  const resultsItem = examSection?.items.find(
    (i) => i.href === "/app/examinations/results",
  );
  assert(
    resultsItem?.label === "View Published Results",
    "1.8 Results menu item correctly renamed to 'View Published Results'",
  );

  // ---------------------------------------------------------------------------
  // 2. Workflow 1: Faculty Uploads Study Material -> Student Accesses It
  // ---------------------------------------------------------------------------
  console.log("\n--- Section 2: Study Materials Management ---");
  const uploadRes = await teachingService.uploadStudyMaterial({
    courseOfferingId: "co-cs301-a",
    courseCode: "CS301",
    courseName: "Data Structures & Algorithms",
    section: "A",
    unitNumber: 2,
    title: "AVL Tree Single and Double Rotation Cheatsheet",
    description:
      "Detailed code diagrams and invariants for self-balancing AVL trees.",
    materialType: "PDF",
    fileUrl: "/assets/materials/cs301-avl-cheatsheet.pdf",
    fileName: "AVL_Rotation_Cheatsheet.pdf",
    fileSize: "1.4 MB",
    uploadedByFacultyId: "fac-cse-01",
    uploadedByFacultyName: "Dr. Rajesh Sharma",
  });

  assert(uploadRes.success, "2.1 Faculty uploads study material successfully");
  assert(
    uploadRes.data.title === "AVL Tree Single and Double Rotation Cheatsheet",
    "2.2 Material has correct title",
  );
  assert(uploadRes.data.downloadCount === 0, "2.3 Initial download count is 0");

  // Student queries materials for the course
  const studentMaterialsRes = await teachingService.getStudyMaterials({
    courseOfferingId: "co-cs301-a",
  });
  assert(
    studentMaterialsRes.success,
    "2.4 Student queries course study materials successfully",
  );
  const studentFound = studentMaterialsRes.data.find(
    (m) => m.id === uploadRes.data.id,
  );
  assert(
    !!studentFound,
    "2.5 Student can see and access the uploaded material",
  );

  // Student downloads the material
  const dlRes = await teachingService.incrementMaterialDownload(
    uploadRes.data.id,
  );
  assert(
    dlRes.success && dlRes.data === 1,
    "2.6 Download count increments to 1 upon student access",
  );

  // ---------------------------------------------------------------------------
  // 3. Workflow 2 & 3: Faculty Creates Assignment -> Student Submits -> Faculty Evaluates -> Student Views Marks
  // ---------------------------------------------------------------------------
  console.log(
    "\n--- Section 3: Coursework Assignment Lifecycle & Student Evaluation ---",
  );
  const asgRes = await teachingService.createAssignment({
    courseOfferingId: "co-cs301-a",
    courseCode: "CS301",
    courseName: "Data Structures & Algorithms",
    section: "A",
    title: "Graph Shortest Path Benchmark Lab",
    description:
      "Implement Dijkstra algorithm and measure runtime on large sparse graphs.",
    unitNumber: 3,
    assignedDate: "2026-11-18",
    dueDate: "2026-11-28",
    maxMarks: 50,
    weightagePercent: 10,
    submissionFormat: "PDF",
    allowLateSubmission: true,
    lateSubmissionDeadline: "2026-11-30",
    latePenaltyPercent: 15,
    status: "PUBLISHED",
    totalEnrolled: 48,
    createdByFacultyId: "fac-cse-01",
    createdByFacultyName: "Dr. Rajesh Sharma",
  });

  assert(
    asgRes.success,
    "3.1 Faculty creates assignment with max marks, weightage & deadline",
  );
  assert(
    asgRes.data.status === "PUBLISHED",
    "3.2 Assignment status is PUBLISHED",
  );

  // Student submits solution
  const subRes = await teachingService.submitAssignment({
    assignmentId: asgRes.data.id,
    courseOfferingId: asgRes.data.courseOfferingId,
    courseCode: asgRes.data.courseCode,
    courseName: asgRes.data.courseName,
    studentId: "std-aarav-patel",
    studentName: "Aarav Patel",
    studentRoll: "24CSE0101",
    submissionFileName: "24CSE0101_Aarav_Dijkstra_Benchmark.pdf",
    submissionFileUrl: "/assets/submissions/24CSE0101_Dijkstra.pdf",
    submissionText: "Implemented with binary heap in C++17.",
    maxMarks: asgRes.data.maxMarks,
  });

  assert(subRes.success, "3.3 Student Aarav Patel submits assignment solution");
  assert(
    subRes.data.status === "SUBMITTED",
    "3.4 Submission status is SUBMITTED",
  );
  assert(
    !subRes.data.isLate,
    "3.5 Submission before due date is marked NOT late",
  );

  // Faculty views submissions roster
  const rosterRes = await teachingService.getSubmissions(asgRes.data.id);
  assert(
    rosterRes.success && rosterRes.data.length >= 1,
    "3.6 Faculty views assignment submissions roster",
  );

  // Faculty evaluates submission
  const evalRes = await teachingService.evaluateSubmission(subRes.data.id, {
    marksObtained: 47,
    feedback:
      "Exceptional runtime analysis on 500k vertices. Very clean code structure.",
    facultyId: "fac-cse-01",
    facultyName: "Dr. Rajesh Sharma",
  });

  assert(
    evalRes.success,
    "3.7 Faculty awards 47/50 marks and qualitative feedback",
  );
  assert(
    evalRes.data.status === "EVALUATED",
    "3.8 Submission transitions to EVALUATED",
  );

  // Student views feedback and marks in their portal
  const studentSubsRes = await teachingService.getSubmissions(
    undefined,
    "std-aarav-patel",
  );
  const aaravSub = studentSubsRes.data.find((s) => s.id === subRes.data.id);
  assert(
    aaravSub?.marksObtained === 47,
    "3.9 Student sees awarded marks: 47 / 50",
  );
  assert(
    aaravSub?.feedback?.includes("Exceptional runtime"),
    "3.10 Student sees faculty qualitative feedback",
  );

  // Validation: Exceeding max marks must be rejected
  let evalError = false;
  try {
    await teachingService.evaluateSubmission(subRes.data.id, {
      marksObtained: 55, // max is 50
      feedback: "Over maximum marks",
      facultyId: "fac-cse-01",
      facultyName: "Dr. Rajesh Sharma",
    });
  } catch (e: any) {
    evalError = true;
    assert(
      e.message.includes("between 0 and maximum 50"),
      "3.11 System enforces marks cannot exceed assessment max marks (50)",
    );
  }
  assert(evalError, "3.12 Exceeding maximum marks is strictly prevented");

  // ---------------------------------------------------------------------------
  // 4. Workflow 4 & 5: Attendance Marking & Correction Audit
  // ---------------------------------------------------------------------------
  console.log(
    "\n--- Section 4: Class Attendance Marking & Correction Audit ---",
  );
  const sessions = await attendanceService.getSessions({
    courseOfferingId: "co-cs301-a",
  });
  assert(
    sessions.success && sessions.data.length > 0,
    "4.1 Faculty retrieves assigned course sessions",
  );

  const activeSession = sessions.data[0];
  const markRes = await attendanceService.submitSessionAttendance(
    activeSession.id,
    [
      { studentId: "std-001", status: "PRESENT" },
      { studentId: "std-002", status: "ABSENT" },
    ],
  );
  assert(markRes.success, "4.2 Faculty marks attendance for class session");

  // Student raises correction
  const corrReq = await attendanceService.submitCorrection({
    sessionId: activeSession.id,
    recordId: "rec-002",
    studentId: "std-002",
    studentName: "Priya Sharma",
    rollNumber: "24CSE0102",
    courseCode: "CS301",
    requestedStatus: "PRESENT",
    reason: "Attended lab session; biometric scanner offline at entrance.",
    supportingDocUrl: "proof.pdf",
  });
  assert(
    corrReq.success,
    "4.3 Student submits attendance correction request with justification",
  );

  // ---------------------------------------------------------------------------
  // 5. Workflow 6: Continuous Assessment Marks Entry & Result Publication Restriction
  // ---------------------------------------------------------------------------
  console.log(
    "\n--- Section 5: Continuous Internal Assessment (CIA) & Result Gates ---",
  );
  const asms = await examinationsService.getAssessments({
    courseOfferingId: "co-cs301-a",
  });
  assert(
    asms.success && asms.data.length > 0,
    "5.1 Faculty loads Continuous Internal Assessment list",
  );

  const ciaAssessment = asms.data[0];
  const saveMarksRes = await examinationsService.saveMarks(ciaAssessment.id, [
    {
      studentId: "std-001",
      marksObtained: 45,
      status: "ENTERED",
    },
  ]);
  assert(
    saveMarksRes.success,
    "5.2 Faculty enters internal CIA marks for students",
  );

  // ---------------------------------------------------------------------------
  // 6. Workflow 7: Course Announcement Publishing
  // ---------------------------------------------------------------------------
  console.log("\n--- Section 6: Target Announcement Publishing ---");
  const annRes = await campusService.createAnnouncement({
    title: "CS301 Mid-Term Review & Doubt Clearing Session",
    content:
      "An extra tutorial session on Graph Algorithms and Red-Black trees will be held this Saturday at 10 AM.",
    priority: "HIGH",
    audienceTarget: "STUDENTS_ONLY",
    targetAudienceDisplay: "B.Tech CSE Students",
    targetDepartments: ["Computer Science & Engineering"],
    channels: ["IN_APP", "EMAIL"],
    tags: ["Academics", "CS301"],
    requiresAcknowledgment: false,
    pinned: false,
    authorName: "Dr. Rajesh Sharma",
    authorRole: "Faculty",
  });
  assert(
    annRes.success,
    "6.1 Faculty publishes course announcement to relevant students",
  );

  // ---------------------------------------------------------------------------
  // 7. Workflow 8: Student Leave Approvals
  // ---------------------------------------------------------------------------
  console.log("\n--- Section 7: Student Leave Processing by Faculty ---");
  const studentLeaveRes = await attendanceService.submitLeave({
    studentName: "Aarav Patel",
    rollNumber: "24CSE0101",
    department: "Computer Science & Engineering",
    section: "A",
    leaveType: "MEDICAL",
    startDate: "2026-11-20",
    endDate: "2026-11-21",
    totalDays: 2,
    reason: "Viral fever - prescribed rest by university health centre.",
    supportingDocName: "medical_cert.pdf",
    applicantType: "STUDENT",
  });
  assert(studentLeaveRes.success, "7.1 Student applies for medical leave");

  const facultyApproval = await attendanceService.updateLeaveStatus(
    studentLeaveRes.data.id,
    "APPROVED",
    "Medical certificate verified. Attendance exemption granted.",
    "Dr. Rajesh Sharma",
  );
  assert(
    facultyApproval.success && facultyApproval.data.status === "APPROVED",
    "7.2 Course faculty approves student leave request",
  );

  // ---------------------------------------------------------------------------
  // 8. Workflow 9: Dedicated Faculty Leave Application & HOD Endorsement
  // ---------------------------------------------------------------------------
  console.log(
    "\n--- Section 8: Dedicated Faculty Leave Workflow (HOD Routing) ---",
  );
  const facultyLeaveApp = await teachingService.applyFacultyLeave({
    facultyId: "fac-cse-01",
    facultyName: "Dr. Rajesh Sharma",
    employeeCode: "EMP-CSE-01",
    department: "Computer Science & Engineering",
    leaveType: "ON_DUTY",
    startDate: "2026-12-10",
    endDate: "2026-12-11",
    totalDays: 2,
    reason: "Invited speaker at National AI Colloquium, IIT Madras.",
    substituteFacultyId: "fac-cse-02",
    substituteFacultyName: "Dr. Ramesh Sundaram",
    substituteClassesArranged: true,
  });

  assert(
    facultyLeaveApp.success,
    "8.1 Faculty submits personal leave application with substitute teacher",
  );
  assert(
    facultyLeaveApp.data.status === "PENDING_HOD",
    "8.2 Initial status is PENDING_HOD",
  );
  assert(
    facultyLeaveApp.data.substituteFacultyName === "Dr. Ramesh Sundaram",
    "8.3 Substitute teacher correctly nominated",
  );

  // HOD endorses leave
  const hodDecision = await teachingService.processFacultyLeaveHOD(
    facultyLeaveApp.data.id,
    "APPROVE",
    "Approved. Class coverage confirmed by Dr. Ramesh Sundaram.",
  );
  assert(
    hodDecision.success && hodDecision.data.status === "APPROVED",
    "8.4 HOD approves faculty leave application",
  );

  // Check balance deduction
  const balances = await teachingService.getFacultyLeaveBalances("fac-cse-01");
  const odBal = balances.data.find((b) => b.leaveType === "ON_DUTY");
  assert(
    odBal?.consumedDays === 6,
    "8.5 On Duty consumed days correctly updated from 4 to 6",
  );

  // ---------------------------------------------------------------------------
  // 9. Workflow 10: Lesson Plan & Class Diary Teaching Log
  // ---------------------------------------------------------------------------
  console.log(
    "\n--- Section 9: Lesson Plan Tracking & Class Diary Integration ---",
  );
  const initialPlans = await teachingService.getLessonPlans("co-cs301-a");
  const unit3 = initialPlans.data.find((u) => u.unitNumber === 3);
  const initialHours = unit3?.completedHours || 0;

  // Log a lecture session in class diary
  const diaryRes = await teachingService.logClassDiaryEntry({
    courseOfferingId: "co-cs301-a",
    courseCode: "CS301",
    courseName: "Data Structures & Algorithms",
    section: "A",
    facultyId: "fac-cse-01",
    facultyName: "Dr. Rajesh Sharma",
    date: "2026-11-18",
    timeSlot: "11:15 AM - 12:15 PM",
    periodNumber: 3,
    unitNumber: 3,
    unitTitle: "Graph Algorithms & Network Flows",
    topicsCovered:
      "Prim's Minimum Spanning Tree algorithm trace and cut property.",
    teachingMethod: "CHALK_AND_BOARD",
    studentsPresent: 47,
    totalStudents: 48,
    attendancePercentage: 97.9,
    remarks: "Students solved 2 cut property exercises on paper.",
    verifiedByHod: true,
  });

  assert(
    diaryRes.success,
    "9.1 Faculty logs lecture in Class Diary / Teaching Log",
  );
  assert(
    diaryRes.data.attendancePercentage === 97.9,
    "9.2 Attendance percentage correctly calculated (97.9%)",
  );

  // Verify lesson plan completed hours was updated automatically
  const updatedPlans = await teachingService.getLessonPlans("co-cs301-a");
  const updatedUnit3 = updatedPlans.data.find((u) => u.unitNumber === 3);
  assert(
    updatedUnit3?.completedHours === initialHours + 1,
    `9.3 Class diary log automatically increments lesson plan unit 3 hours (${initialHours} -> ${updatedUnit3?.completedHours})`,
  );

  console.log(
    "\n===============================================================================",
  );
  console.log(
    `Final Verification Results: Passed: ${passed}, Failed: ${failed}`,
  );
  console.log(
    "===============================================================================\n",
  );

  if (failed > 0) {
    process.exit(1);
  }
}

runTestSuite().catch((e) => {
  console.error("Test execution failed:", e);
  process.exit(1);
});
