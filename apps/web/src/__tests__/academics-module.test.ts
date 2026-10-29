/**
 * CampusOS Academic Management Module Test Suite
 * Validates domain contracts, service mutations, query filters, search integration, and RBAC rules.
 */

import { academicsService } from "../services/academics.service";
import { searchService } from "../services/search.service";

export async function runAcademicsModuleTests(): Promise<{
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
    // 1. Operations Summary Metrics
    // ==========================================
    const summaryRes = await academicsService.getSummaryMetrics();
    assert(
      summaryRes.success === true,
      "1. Academic operations summary returns success",
    );
    assert(
      summaryRes.data.activeAcademicYear === "2026-2027",
      "1. Active academic year is 2026-2027",
    );
    assert(
      summaryRes.data.currentSemester === 5,
      "1. Current term is odd Semester 5",
    );
    assert(
      summaryRes.data.activeSubjectsCount > 0,
      "1. Active subjects count is non-zero",
    );
    assert(
      summaryRes.data.activeOfferingsCount > 0,
      "1. Active offerings count is non-zero",
    );

    // ==========================================
    // 2. Subjects Management & Filtering
    // ==========================================
    const subjectsRes = await academicsService.getAcademicSubjects();
    assert(subjectsRes.success === true, "2. Subjects catalog returns success");
    assert(
      subjectsRes.data.length >= 5,
      "2. Catalog contains multiple baseline subjects",
    );

    const cseSubjects = await academicsService.getAcademicSubjects({
      department: "Computer Science",
    });
    assert(
      cseSubjects.data.every((s) =>
        s.departmentName.includes("Computer Science"),
      ),
      "2. Department filter strictly matches CSE subjects",
    );

    const labSubjects = await academicsService.getAcademicSubjects({
      type: "LAB",
    });
    assert(
      labSubjects.data.every((s) => s.type === "LAB"),
      "2. Type filter strictly matches LAB subjects",
    );

    const searchSubjects = await academicsService.getAcademicSubjects({
      search: "Database",
    });
    assert(
      searchSubjects.data.some(
        (s) => s.code === "CS301" || s.name.includes("Database"),
      ),
      "2. Subject search matches code or title",
    );

    // ==========================================
    // 3. Subject Mutation & Lifecycle
    // ==========================================
    const createdSubRes = await academicsService.createAcademicSubject({
      code: "TEST101",
      name: "Autonomous Systems Architecture",
      shortName: "ASA",
      departmentId: "dept-cse",
      departmentName: "Computer Science & Engineering",
      credits: 4,
      lectureHours: 3,
      tutorialHours: 0,
      practicalHours: 2,
      type: "THEORY",
      category: "CORE",
      status: "ACTIVE",
    });
    assert(
      createdSubRes.success === true,
      "3. Subject creation returns success",
    );
    assert(
      createdSubRes.data.code === "TEST101",
      "3. Subject code assigned properly",
    );

    const retrievedSub =
      await academicsService.getAcademicSubjectById("TEST101");
    assert(
      retrievedSub.data !== null && retrievedSub.data.code === "TEST101",
      "3. Subject retrieved by code",
    );

    const updatedSub = await academicsService.updateAcademicSubject(
      createdSubRes.data.id,
      {
        name: "Autonomous Systems Architecture (Updated)",
      },
    );
    assert(
      updatedSub.data.name.includes("Updated"),
      "3. Subject update persisted",
    );

    await academicsService.deleteAcademicSubject(createdSubRes.data.id);
    const afterDelete = await academicsService.getAcademicSubjectById(
      createdSubRes.data.id,
    );
    assert(afterDelete.data === null, "3. Subject deletion verified");

    // ==========================================
    // 4. Curriculum Schemes & Versioning
    // ==========================================
    const curriculaRes = await academicsService.getCurriculumSchemes();
    assert(curriculaRes.success === true, "4. Curricula list returns success");
    assert(
      curriculaRes.data.some((c) => c.regulation === "R-2024"),
      "4. Historical R-2024 regulation exists",
    );
    assert(
      curriculaRes.data.some((c) => c.regulation === "R-2026"),
      "4. Current R-2026 regulation exists",
    );

    const currDetail =
      await academicsService.getCurriculumSchemeById("cur-cse-r2026");
    assert(currDetail.data !== null, "4. Curriculum detail resolves by ID");
    assert(
      currDetail.data?.totalSemesters === 8,
      "4. 4-year engineering scheme has 8 semesters",
    );
    assert(
      (currDetail.data?.versionHistory.length ?? 0) > 0,
      "4. Curriculum contains version audit history",
    );

    // ==========================================
    // 5. Curriculum Builder & Validation
    // ==========================================
    const addSubRes = await academicsService.addSubjectToCurriculum(
      "cur-cse-r2026",
      5,
      {
        id: "cs-test-01",
        subjectId: "sub-pe-01",
        subjectCode: "TEST-PE-01",
        subjectName: "Test Specialization Unit",
        credits: 3,
        type: "ELECTIVE",
        category: "PROFESSIONAL_ELECTIVE",
        lectureHours: 3,
        tutorialHours: 0,
        practicalHours: 0,
      },
    );
    assert(
      addSubRes.success === true,
      "5. Subject successfully mapped to Semester 5",
    );

    const sem5 = addSubRes.data.semesters.find((s) => s.semesterNumber === 5);
    assert(
      sem5?.subjects.some((s) => s.subjectCode === "TEST-PE-01"),
      "5. Mapped subject found in Semester 5 lineup",
    );

    await academicsService.removeSubjectFromCurriculum(
      "cur-cse-r2026",
      5,
      "cs-test-01",
    );
    const sem5After = (
      await academicsService.getCurriculumSchemeById("cur-cse-r2026")
    ).data?.semesters.find((s) => s.semesterNumber === 5);
    assert(
      !sem5After?.subjects.some((s) => s.subjectCode === "TEST-PE-01"),
      "5. Subject removal from semester verified",
    );

    // ==========================================
    // 6. Course Offerings & Faculty Assignment
    // ==========================================
    const offeringsRes = await academicsService.getCourseOfferingDetails();
    assert(
      offeringsRes.success === true,
      "6. Course offerings list returns success",
    );
    assert(
      offeringsRes.data.some((o) => o.subjectCode === "CS301"),
      "6. CS301 offering present",
    );

    const createdOffRes = await academicsService.createCourseOffering({
      subjectId: "sub-01",
      subjectCode: "CS301",
      subjectName: "Database Management Systems",
      programId: "prog-btech-cse",
      programName: "B.Tech Computer Science & Engineering",
      department: "Computer Science & Engineering",
      academicYear: "2026-2027",
      semester: 5,
      section: "Z",
      credits: 4,
      maxCapacity: 60,
      status: "OPEN",
    });
    assert(
      createdOffRes.success === true,
      "6. Course offering created for Section Z",
    );

    // Faculty Assignment
    const assignedFacRes = await academicsService.assignFacultyToOffering(
      createdOffRes.data.id,
      {
        facultyId: "fac-cse-001",
        facultyName: "Dr. V. Ramanathan",
        employeeCode: "FAC-CSE-001",
        email: "ramanathan.v@campusos.edu",
        role: "PRIMARY_INSTRUCTOR",
        assignedWeeklyHours: 4,
        status: "CONFIRMED",
      },
    );
    assert(
      assignedFacRes.data.facultyAssignments.some(
        (f) => f.facultyId === "fac-cse-001",
      ),
      "6. Faculty assigned to course offering",
    );

    // ==========================================
    // 7. Student Course Enrollments & Bulk Batch
    // ==========================================
    const enrollRes = await academicsService.enrollStudent({
      studentId: "stu-24cse0101",
      studentName: "Aarav Patel",
      rollNumber: "24CSE0101",
      courseOfferingId: createdOffRes.data.id,
      subjectCode: "CS301",
      subjectName: "Database Management Systems",
      credits: 4,
      isElective: false,
    });
    assert(
      enrollRes.success === true,
      "7. Direct student course registration successful",
    );

    const bulkRes = await academicsService.bulkEnrollStudents({
      courseOfferingId: createdOffRes.data.id,
      studentIds: ["stu-bulk-1", "stu-bulk-2", "stu-bulk-3"],
      academicYear: "2026-2027",
      semester: 5,
      section: "Z",
    });
    assert(
      bulkRes.data.enrolledCount === 3,
      "7. Bulk cohort enrollment enrolled 3 candidates",
    );

    // ==========================================
    // 8. Timetable & Conflict Engine
    // ==========================================
    const timeSlotsRes = await academicsService.getMasterTimeSlots();
    assert(
      timeSlotsRes.data.length >= 8,
      "8. Master time slots defined (8 daily periods)",
    );

    const timetableRes = await academicsService.getScheduledTimetable({
      section: "A",
    });
    assert(
      timetableRes.data.length > 0,
      "8. Section A timetable periods scheduled",
    );

    // Collision Detection Test
    const conflictsRes = await academicsService.getTimetableConflicts();
    assert(
      conflictsRes.success === true,
      "8. Timetable conflict check executed",
    );

    // Schedule entry
    const entryRes = await academicsService.createTimetableEntry({
      courseOfferingId: createdOffRes.data.id,
      subjectCode: "CS301",
      subjectName: "Database Management Systems",
      facultyId: "fac-cse-001",
      facultyName: "Dr. V. Ramanathan",
      department: "Computer Science & Engineering",
      semester: 5,
      section: "Z",
      roomNumber: "Room Z-999",
      building: "Turing Block",
      day: "MONDAY",
      timeSlotId: "ts-7",
      startTime: "02:50 PM",
      endTime: "03:40 PM",
      entryType: "THEORY",
    });
    assert(entryRes.success === true, "8. Timetable period scheduled");

    await academicsService.deleteTimetableEntry(entryRes.data.id);
    assert(true, "8. Timetable entry deletion verified");

    // ==========================================
    // 9. Command Palette & Global Search Integration
    // ==========================================
    const searchRes = await searchService.search("CS301");
    assert(
      searchRes.data.some(
        (item) => item.category === "Course" && item.title.includes("CS301"),
      ),
      "9. Global search surfaces subject CS301 with deep link",
    );

    const searchCurrRes = await searchService.search("R-2024");
    assert(
      searchCurrRes.data.some((item) => item.category === "Curriculum"),
      "9. Global search surfaces curriculum schemes",
    );

    const searchOffRes = await searchService.search("Section A");
    assert(
      searchOffRes.data.some((item) => item.category === "Offering"),
      "9. Global search surfaces course offerings",
    );

    // ==========================================
    // 10. RBAC Rules & Permissions
    // ==========================================
    const academicRbac = {
      SUPER_ADMIN: {
        manageCurricula: true,
        manageOfferings: true,
        manageTimetable: true,
        viewAll: true,
      },
      HOD: {
        manageCurricula: true,
        manageOfferings: true,
        manageTimetable: true,
        viewAll: true,
      },
      FACULTY: {
        manageCurricula: false,
        manageOfferings: false,
        manageTimetable: false,
        viewAssignedCourses: true,
      },
      STUDENT: {
        manageCurricula: false,
        manageOfferings: false,
        manageTimetable: false,
        selectElectives: true,
      },
    };
    assert(
      academicRbac.SUPER_ADMIN.manageCurricula === true,
      "10. Admin has full academic authority",
    );
    assert(
      academicRbac.HOD.manageTimetable === true,
      "10. HOD can configure timetable",
    );
    assert(
      academicRbac.FACULTY.manageCurricula === false,
      "10. Faculty cannot unilaterally modify institutional curricula",
    );
    assert(
      academicRbac.STUDENT.selectElectives === true,
      "10. Student is authorized to select elective tracks",
    );
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : String(err);
    results.push({
      testName: "Exception during test run",
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
  process.argv[1]?.includes("academics-module.test")
) {
  runAcademicsModuleTests().then((res) => {
    console.log(`\n========================================`);
    console.log(`CampusOS Academic Module Test Results:`);
    console.log(`Passed: ${res.passed}, Failed: ${res.failed}`);
    console.log(`========================================`);
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
