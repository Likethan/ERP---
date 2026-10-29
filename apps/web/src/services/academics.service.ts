import { ApiResponse } from "@campusos/types";
import {
  DepartmentItem,
  ProgramItem,
  SubjectItem,
  CurriculumSchemeItem,
  CourseOfferingItem,
  TimetableSlotItem,
  MOCK_DEPARTMENTS,
  MOCK_PROGRAMS,
  MOCK_SUBJECTS,
  MOCK_CURRICULA,
  MOCK_COURSE_OFFERINGS,
  MOCK_TIMETABLE,
  MOCK_ACADEMIC_SUBJECTS,
  MOCK_CURRICULUM_SCHEMES,
  MOCK_COURSE_OFFERING_DETAILS,
  MOCK_STUDENT_COURSE_ENROLLMENTS,
  MOCK_MASTER_TIME_SLOTS,
  MOCK_SCHEDULED_TIMETABLE,
  MOCK_TIMETABLE_CONFLICTS,
  MOCK_ACADEMIC_OPERATIONS_SUMMARY,
} from "@/mocks/academics.mock";
import {
  AcademicSubject,
  SubjectType,
  SubjectStatus,
  CurriculumScheme,
  CurriculumStatus,
  CurriculumSubject,
  ElectiveGroup,
  CourseOfferingDetail,
  CourseOfferingStatus,
  CourseFacultyAssignment,
  StudentCourseEnrollmentRecord,
  CourseEnrollmentStatus,
  MasterTimeSlot,
  ScheduledTimetableEntry,
  TimetableConflict,
  DayOfWeek,
  AcademicOperationsSummary,
} from "@/types/academics";

class AcademicsService {
  // Legacy collections for backwards compatibility
  private departments: DepartmentItem[] = [...MOCK_DEPARTMENTS];
  private programs: ProgramItem[] = [...MOCK_PROGRAMS];
  private subjects: SubjectItem[] = [...MOCK_SUBJECTS];
  private curricula: CurriculumSchemeItem[] = [...MOCK_CURRICULA];
  private offerings: CourseOfferingItem[] = [...MOCK_COURSE_OFFERINGS];
  private timetable: TimetableSlotItem[] = [...MOCK_TIMETABLE];

  // Canonical Domain collections
  private academicSubjects: AcademicSubject[] = [...MOCK_ACADEMIC_SUBJECTS];
  private curriculumSchemes: CurriculumScheme[] = [...MOCK_CURRICULUM_SCHEMES];
  private courseOfferingDetails: CourseOfferingDetail[] = [
    ...MOCK_COURSE_OFFERING_DETAILS,
  ];
  private studentEnrollments: StudentCourseEnrollmentRecord[] = [
    ...MOCK_STUDENT_COURSE_ENROLLMENTS,
  ];
  private masterTimeSlots: MasterTimeSlot[] = [...MOCK_MASTER_TIME_SLOTS];
  private scheduledTimetable: ScheduledTimetableEntry[] = [
    ...MOCK_SCHEDULED_TIMETABLE,
  ];
  private conflicts: TimetableConflict[] = [...MOCK_TIMETABLE_CONFLICTS];
  private summary: AcademicOperationsSummary = {
    ...MOCK_ACADEMIC_OPERATIONS_SUMMARY,
  };

  // ==========================================
  // Summary & Department / Program Methods
  // ==========================================

  async getSummaryMetrics(): Promise<ApiResponse<AcademicOperationsSummary>> {
    await new Promise((r) => setTimeout(r, 30));
    // Dynamically calculate accurate counts from local state
    const activeSubjects = this.academicSubjects.filter(
      (s) => s.status === "ACTIVE",
    ).length;
    const activeOfferings = this.courseOfferingDetails.filter(
      (o) => o.status === "ACTIVE" || o.status === "OPEN",
    ).length;
    const unassigned = this.courseOfferingDetails.filter(
      (o) => o.facultyAssignments.length === 0,
    ).length;
    const activeCurricula = this.curriculumSchemes.filter(
      (c) => c.status === "PUBLISHED" || c.status === "APPROVED",
    ).length;

    const dynamicSummary: AcademicOperationsSummary = {
      ...this.summary,
      activeSubjectsCount: activeSubjects,
      activeOfferingsCount: activeOfferings,
      enrolledStudentsCount: this.studentEnrollments.length,
      unassignedOfferingsCount: unassigned,
      timetableConflictsCount: this.conflicts.length,
      activeCurriculaCount: activeCurricula,
    };
    return { success: true, data: dynamicSummary };
  }

  async getDepartments(): Promise<ApiResponse<DepartmentItem[]>> {
    await new Promise((r) => setTimeout(r, 30));
    return { success: true, data: this.departments };
  }

  async getPrograms(): Promise<ApiResponse<ProgramItem[]>> {
    await new Promise((r) => setTimeout(r, 30));
    return { success: true, data: this.programs };
  }

  // ==========================================
  // Academic Subjects Methods
  // ==========================================

  async getAcademicSubjects(params?: {
    department?: string;
    type?: SubjectType;
    status?: SubjectStatus;
    search?: string;
  }): Promise<ApiResponse<AcademicSubject[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.academicSubjects];

    if (params?.department && params.department !== "ALL") {
      items = items.filter(
        (s) =>
          s.departmentName
            .toLowerCase()
            .includes(params.department!.toLowerCase()) ||
          s.departmentId.toLowerCase() === params.department!.toLowerCase(),
      );
    }
    if (params?.type && (params.type as string) !== "ALL") {
      items = items.filter((s) => s.type === params.type);
    }
    if (params?.status && (params.status as string) !== "ALL") {
      items = items.filter((s) => s.status === params.status);
    }
    if (params?.search) {
      const q = params.search.toLowerCase();
      items = items.filter(
        (s) =>
          s.code.toLowerCase().includes(q) ||
          s.name.toLowerCase().includes(q) ||
          s.shortName.toLowerCase().includes(q) ||
          s.departmentName.toLowerCase().includes(q),
      );
    }

    return { success: true, data: items };
  }

  async getAcademicSubjectById(
    id: string,
  ): Promise<ApiResponse<AcademicSubject | null>> {
    await new Promise((r) => setTimeout(r, 30));
    const sub = this.academicSubjects.find(
      (s) => s.id === id || s.code.toLowerCase() === id.toLowerCase(),
    );
    return { success: true, data: sub || null };
  }

  async createAcademicSubject(
    data: Partial<AcademicSubject>,
  ): Promise<ApiResponse<AcademicSubject>> {
    await new Promise((r) => setTimeout(r, 60));
    const newSubject: AcademicSubject = {
      id: `subj-${Date.now()}`,
      code: data.code || `SUB${Math.floor(100 + Math.random() * 900)}`,
      name: data.name || "Untitled Course",
      shortName: data.shortName || data.code || "SUB",
      departmentId: data.departmentId || "dept-cse",
      departmentName: data.departmentName || "Computer Science & Engineering",
      credits: Number(data.credits) || 3,
      lectureHours: Number(data.lectureHours) || 3,
      tutorialHours: Number(data.tutorialHours) || 0,
      practicalHours: Number(data.practicalHours) || 0,
      type: data.type || "THEORY",
      category: data.category || "CORE",
      description:
        data.description || "Course syllabus and learning objectives.",
      status: data.status || "ACTIVE",
      prerequisites: data.prerequisites || [],
      curriculumCount: 1,
      offeringsCount: 0,
    };

    this.academicSubjects.unshift(newSubject);
    return { success: true, data: newSubject };
  }

  async updateAcademicSubject(
    id: string,
    data: Partial<AcademicSubject>,
  ): Promise<ApiResponse<AcademicSubject>> {
    await new Promise((r) => setTimeout(r, 50));
    const idx = this.academicSubjects.findIndex((s) => s.id === id);
    if (idx === -1) {
      throw new Error(`Subject ${id} not found`);
    }
    const updated = { ...this.academicSubjects[idx], ...data };
    this.academicSubjects[idx] = updated;
    return { success: true, data: updated };
  }

  async deleteAcademicSubject(id: string): Promise<ApiResponse<boolean>> {
    await new Promise((r) => setTimeout(r, 40));
    this.academicSubjects = this.academicSubjects.filter((s) => s.id !== id);
    return { success: true, data: true };
  }

  // Legacy getSubjects / createSubject for backward compatibility
  async getSubjects(department?: string): Promise<ApiResponse<SubjectItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.subjects];
    if (department) {
      items = items.filter((s) => s.department === department);
    }
    return { success: true, data: items };
  }

  async createSubject(
    data: Partial<SubjectItem>,
  ): Promise<ApiResponse<SubjectItem>> {
    await new Promise((r) => setTimeout(r, 60));
    const newSub: SubjectItem = {
      id: `sub-${Date.now()}`,
      code: data.code || `CS${this.subjects.length + 301}`,
      name: data.name || "New Subject",
      department: data.department || "Computer Science & Engineering",
      credits: data.credits || 3,
      type: data.type || "THEORY",
      lectureHours: data.lectureHours || 3,
      tutorialHours: data.tutorialHours || 0,
      practicalHours: data.practicalHours || 0,
      status: "ACTIVE",
    };
    this.subjects.push(newSub);
    return { success: true, data: newSub };
  }

  // ==========================================
  // Curriculum Schemes & Builder Methods
  // ==========================================

  async getCurriculumSchemes(params?: {
    department?: string;
    status?: CurriculumStatus;
    search?: string;
  }): Promise<ApiResponse<CurriculumScheme[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.curriculumSchemes];

    if (params?.department && params.department !== "ALL") {
      items = items.filter((c) =>
        c.department.toLowerCase().includes(params.department!.toLowerCase()),
      );
    }
    if (params?.status && (params.status as string) !== "ALL") {
      items = items.filter((c) => c.status === params.status);
    }
    if (params?.search) {
      const q = params.search.toLowerCase();
      items = items.filter(
        (c) =>
          c.programName.toLowerCase().includes(q) ||
          c.regulation.toLowerCase().includes(q) ||
          c.department.toLowerCase().includes(q),
      );
    }

    return { success: true, data: items };
  }

  async getCurriculumSchemeById(
    id: string,
  ): Promise<ApiResponse<CurriculumScheme | null>> {
    await new Promise((r) => setTimeout(r, 30));
    const scheme = this.curriculumSchemes.find((c) => c.id === id);
    return { success: true, data: scheme || null };
  }

  async createCurriculumScheme(
    data: Partial<CurriculumScheme>,
  ): Promise<ApiResponse<CurriculumScheme>> {
    await new Promise((r) => setTimeout(r, 60));
    const newScheme: CurriculumScheme = {
      id: `curr-${Date.now()}`,
      programId: data.programId || "prog-btech-cse",
      programName: data.programName || "B.Tech Computer Science & Engineering",
      programCode: data.programCode || "B.Tech CSE",
      department: data.department || "Computer Science & Engineering",
      regulation: data.regulation || "R-2026",
      version: data.version || "v1.0",
      academicYear: data.academicYear || "2026-2027",
      effectiveDate: data.effectiveDate || "July 2026",
      totalCredits: data.totalCredits || 160,
      totalSemesters: data.totalSemesters || 8,
      status: data.status || "DRAFT",
      isActiveVersion: false,
      semesters: data.semesters || [
        { semesterNumber: 1, totalCredits: 20, subjects: [] },
        { semesterNumber: 2, totalCredits: 20, subjects: [] },
      ],
      versionHistory: [
        {
          version: data.version || "v1.0",
          date: new Date().toISOString().split("T")[0],
          author: "Academic Council",
          notes: "Initial Draft Creation",
          status: "DRAFT",
        },
      ],
    };

    this.curriculumSchemes.unshift(newScheme);
    return { success: true, data: newScheme };
  }

  async updateCurriculumScheme(
    id: string,
    data: Partial<CurriculumScheme>,
  ): Promise<ApiResponse<CurriculumScheme>> {
    await new Promise((r) => setTimeout(r, 50));
    const idx = this.curriculumSchemes.findIndex((c) => c.id === id);
    if (idx === -1) {
      throw new Error(`Curriculum ${id} not found`);
    }
    const updated = { ...this.curriculumSchemes[idx], ...data };
    this.curriculumSchemes[idx] = updated;
    return { success: true, data: updated };
  }

  async publishCurriculumScheme(
    id: string,
  ): Promise<ApiResponse<CurriculumScheme>> {
    await new Promise((r) => setTimeout(r, 50));
    const idx = this.curriculumSchemes.findIndex((c) => c.id === id);
    if (idx === -1) {
      throw new Error(`Curriculum ${id} not found`);
    }
    const curr = this.curriculumSchemes[idx];
    curr.status = "PUBLISHED";
    curr.isActiveVersion = true;
    curr.versionHistory.unshift({
      version: curr.version,
      date: new Date().toISOString().split("T")[0],
      author: "Dean of Academics",
      notes: "Officially published & gazetted for current cohorts.",
      status: "PUBLISHED",
    });
    return { success: true, data: curr };
  }

  async addSubjectToCurriculum(
    curriculumId: string,
    semesterNumber: number,
    subject: CurriculumSubject,
  ): Promise<ApiResponse<CurriculumScheme>> {
    await new Promise((r) => setTimeout(r, 40));
    const curr = this.curriculumSchemes.find((c) => c.id === curriculumId);
    if (!curr) throw new Error("Curriculum not found");

    let sem = curr.semesters.find((s) => s.semesterNumber === semesterNumber);
    if (!sem) {
      sem = { semesterNumber, totalCredits: 0, subjects: [] };
      curr.semesters.push(sem);
      curr.semesters.sort((a, b) => a.semesterNumber - b.semesterNumber);
    }

    sem.subjects.push(subject);
    sem.totalCredits = sem.subjects.reduce((sum, s) => sum + s.credits, 0);
    curr.totalCredits = curr.semesters.reduce(
      (sum, s) => sum + s.totalCredits,
      0,
    );

    return { success: true, data: curr };
  }

  async removeSubjectFromCurriculum(
    curriculumId: string,
    semesterNumber: number,
    subjectId: string,
  ): Promise<ApiResponse<CurriculumScheme>> {
    await new Promise((r) => setTimeout(r, 40));
    const curr = this.curriculumSchemes.find((c) => c.id === curriculumId);
    if (!curr) throw new Error("Curriculum not found");

    const sem = curr.semesters.find((s) => s.semesterNumber === semesterNumber);
    if (sem) {
      sem.subjects = sem.subjects.filter(
        (s) => s.id !== subjectId && s.subjectId !== subjectId,
      );
      sem.totalCredits = sem.subjects.reduce((sum, s) => sum + s.credits, 0);
      curr.totalCredits = curr.semesters.reduce(
        (sum, s) => sum + s.totalCredits,
        0,
      );
    }

    return { success: true, data: curr };
  }

  async createElectiveGroup(
    curriculumId: string,
    semesterNumber: number,
    group: ElectiveGroup,
  ): Promise<ApiResponse<CurriculumScheme>> {
    await new Promise((r) => setTimeout(r, 40));
    const curr = this.curriculumSchemes.find((c) => c.id === curriculumId);
    if (!curr) throw new Error("Curriculum not found");

    const sem = curr.semesters.find((s) => s.semesterNumber === semesterNumber);
    if (sem) {
      if (!sem.electiveGroups) sem.electiveGroups = [];
      sem.electiveGroups.push(group);
    }
    return { success: true, data: curr };
  }

  async getCurricula(): Promise<ApiResponse<CurriculumSchemeItem[]>> {
    await new Promise((r) => setTimeout(r, 30));
    return { success: true, data: this.curricula };
  }

  // ==========================================
  // Course Offerings & Faculty Assignment
  // ==========================================

  async getCourseOfferingDetails(params?: {
    academicYear?: string;
    semester?: number;
    department?: string;
    section?: string;
    status?: CourseOfferingStatus;
    search?: string;
  }): Promise<ApiResponse<CourseOfferingDetail[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.courseOfferingDetails];

    if (params?.academicYear && params.academicYear !== "ALL") {
      items = items.filter((o) => o.academicYear === params.academicYear);
    }
    if (params?.semester && (params.semester as unknown as string) !== "ALL") {
      items = items.filter((o) => o.semester === Number(params.semester));
    }
    if (params?.department && params.department !== "ALL") {
      items = items.filter((o) =>
        o.department.toLowerCase().includes(params.department!.toLowerCase()),
      );
    }
    if (params?.section && params.section !== "ALL") {
      items = items.filter(
        (o) => o.section.toLowerCase() === params.section!.toLowerCase(),
      );
    }
    if (params?.status && (params.status as string) !== "ALL") {
      items = items.filter((o) => o.status === params.status);
    }
    if (params?.search) {
      const q = params.search.toLowerCase();
      items = items.filter(
        (o) =>
          o.subjectCode.toLowerCase().includes(q) ||
          o.subjectName.toLowerCase().includes(q) ||
          o.facultyAssignments.some((f) =>
            f.facultyName.toLowerCase().includes(q),
          ),
      );
    }

    return { success: true, data: items };
  }

  async getCourseOfferingDetailById(
    id: string,
  ): Promise<ApiResponse<CourseOfferingDetail | null>> {
    await new Promise((r) => setTimeout(r, 30));
    const offering = this.courseOfferingDetails.find((o) => o.id === id);
    return { success: true, data: offering || null };
  }

  async createCourseOffering(
    data: Partial<CourseOfferingDetail>,
  ): Promise<ApiResponse<CourseOfferingDetail>> {
    await new Promise((r) => setTimeout(r, 60));
    const newOffering: CourseOfferingDetail = {
      id: `off-${Date.now()}`,
      subjectId: data.subjectId || "sub-01",
      subjectCode: data.subjectCode || "CS301",
      subjectName: data.subjectName || "Database Management Systems",
      programId: data.programId || "prog-btech-cse",
      programName: data.programName || "B.Tech Computer Science & Engineering",
      department: data.department || "Computer Science & Engineering",
      academicYear: data.academicYear || "2026-2027",
      semester: Number(data.semester) || 5,
      section: data.section || "A",
      credits: Number(data.credits) || 4,
      type: data.type || "THEORY",
      lectureHours: Number(data.lectureHours) || 3,
      labHours: Number(data.labHours) || 2,
      facultyAssignments: data.facultyAssignments || [],
      enrolledCount: 0,
      maxCapacity: Number(data.maxCapacity) || 60,
      status: data.status || "OPEN",
      syllabusCoveragePercentage: 0,
    };

    this.courseOfferingDetails.unshift(newOffering);
    return { success: true, data: newOffering };
  }

  async updateCourseOffering(
    id: string,
    data: Partial<CourseOfferingDetail>,
  ): Promise<ApiResponse<CourseOfferingDetail>> {
    await new Promise((r) => setTimeout(r, 50));
    const idx = this.courseOfferingDetails.findIndex((o) => o.id === id);
    if (idx === -1) {
      throw new Error(`Course offering ${id} not found`);
    }
    const updated = { ...this.courseOfferingDetails[idx], ...data };
    this.courseOfferingDetails[idx] = updated;
    return { success: true, data: updated };
  }

  async assignFacultyToOffering(
    offeringId: string,
    assignment: Omit<CourseFacultyAssignment, "id">,
  ): Promise<ApiResponse<CourseOfferingDetail>> {
    await new Promise((r) => setTimeout(r, 40));
    const offering = this.courseOfferingDetails.find(
      (o) => o.id === offeringId,
    );
    if (!offering) throw new Error("Course offering not found");

    const newAssignment: CourseFacultyAssignment = {
      ...assignment,
      id: `fa-${Date.now()}`,
    };
    offering.facultyAssignments.push(newAssignment);
    return { success: true, data: offering };
  }

  async removeFacultyFromOffering(
    offeringId: string,
    assignmentId: string,
  ): Promise<ApiResponse<CourseOfferingDetail>> {
    await new Promise((r) => setTimeout(r, 40));
    const offering = this.courseOfferingDetails.find(
      (o) => o.id === offeringId,
    );
    if (!offering) throw new Error("Course offering not found");

    offering.facultyAssignments = offering.facultyAssignments.filter(
      (f) => f.id !== assignmentId,
    );
    return { success: true, data: offering };
  }

  // Legacy getCourseOfferings for backwards compatibility
  async getCourseOfferings(params?: {
    semester?: number;
    department?: string;
  }): Promise<ApiResponse<CourseOfferingItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.offerings];
    if (params?.semester) {
      items = items.filter((o) => o.semester === Number(params.semester));
    }
    if (params?.department) {
      items = items.filter((o) => o.department === params.department);
    }
    return { success: true, data: items };
  }

  // ==========================================
  // Student Course Enrollments & Electives
  // ==========================================

  async getStudentCourseEnrollments(params?: {
    courseOfferingId?: string;
    studentId?: string;
    semester?: number;
    section?: string;
    status?: CourseEnrollmentStatus;
    search?: string;
  }): Promise<ApiResponse<StudentCourseEnrollmentRecord[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.studentEnrollments];

    if (params?.courseOfferingId && params.courseOfferingId !== "ALL") {
      items = items.filter(
        (e) => e.courseOfferingId === params.courseOfferingId,
      );
    }
    if (params?.studentId) {
      items = items.filter(
        (e) =>
          e.studentId === params.studentId || e.rollNumber === params.studentId,
      );
    }
    if (params?.semester && (params.semester as unknown as string) !== "ALL") {
      items = items.filter((e) => e.semester === Number(params.semester));
    }
    if (params?.section && params.section !== "ALL") {
      items = items.filter((e) => e.section === params.section);
    }
    if (params?.status && (params.status as string) !== "ALL") {
      items = items.filter((e) => e.status === params.status);
    }
    if (params?.search) {
      const q = params.search.toLowerCase();
      items = items.filter(
        (e) =>
          e.studentName.toLowerCase().includes(q) ||
          e.rollNumber.toLowerCase().includes(q) ||
          e.subjectCode.toLowerCase().includes(q) ||
          e.subjectName.toLowerCase().includes(q),
      );
    }

    return { success: true, data: items };
  }

  async enrollStudent(
    data: Partial<StudentCourseEnrollmentRecord>,
  ): Promise<ApiResponse<StudentCourseEnrollmentRecord>> {
    await new Promise((r) => setTimeout(r, 50));
    const newEnrollment: StudentCourseEnrollmentRecord = {
      id: `enr-${Date.now()}`,
      studentId: data.studentId || "std-001",
      studentName: data.studentName || "John Doe",
      rollNumber: data.rollNumber || "24CSE999",
      program: data.program || "B.Tech Computer Science & Engineering",
      department: data.department || "Computer Science & Engineering",
      academicYear: data.academicYear || "2026-2027",
      semester: Number(data.semester) || 5,
      section: data.section || "A",
      courseOfferingId: data.courseOfferingId || "off-cs301-a",
      subjectCode: data.subjectCode || "CS301",
      subjectName: data.subjectName || "Database Management Systems",
      credits: Number(data.credits) || 4,
      isElective: Boolean(data.isElective),
      electiveGroup: data.electiveGroup,
      status: "ENROLLED",
      enrolledDate: new Date().toISOString().split("T")[0],
      attendanceRate: 100,
    };

    this.studentEnrollments.unshift(newEnrollment);

    // Update offering enrolled count
    const offering = this.courseOfferingDetails.find(
      (o) => o.id === newEnrollment.courseOfferingId,
    );
    if (offering) {
      offering.enrolledCount += 1;
    }

    return { success: true, data: newEnrollment };
  }

  async bulkEnrollStudents(data: {
    courseOfferingId: string;
    studentIds: string[];
    academicYear: string;
    semester: number;
    section: string;
  }): Promise<ApiResponse<{ enrolledCount: number }>> {
    await new Promise((r) => setTimeout(r, 80));
    const offering = this.courseOfferingDetails.find(
      (o) => o.id === data.courseOfferingId,
    );
    const subCode = offering ? offering.subjectCode : "CS301";
    const subName = offering ? offering.subjectName : "Course";
    const credits = offering ? offering.credits : 3;

    let count = 0;
    for (const sid of data.studentIds) {
      const exists = this.studentEnrollments.some(
        (e) =>
          e.studentId === sid && e.courseOfferingId === data.courseOfferingId,
      );
      if (!exists) {
        this.studentEnrollments.push({
          id: `enr-bulk-${Date.now()}-${count}`,
          studentId: sid,
          studentName: `Student ${sid}`,
          rollNumber: `24CSE${Math.floor(100 + Math.random() * 900)}`,
          program: "B.Tech Computer Science & Engineering",
          department: "Computer Science & Engineering",
          academicYear: data.academicYear,
          semester: data.semester,
          section: data.section,
          courseOfferingId: data.courseOfferingId,
          subjectCode: subCode,
          subjectName: subName,
          credits: credits,
          isElective: false,
          status: "ENROLLED",
          enrolledDate: new Date().toISOString().split("T")[0],
          attendanceRate: 100,
        });
        count++;
      }
    }

    if (offering) {
      offering.enrolledCount += count;
    }

    return { success: true, data: { enrolledCount: count } };
  }

  async updateEnrollmentStatus(
    id: string,
    status: CourseEnrollmentStatus,
  ): Promise<ApiResponse<boolean>> {
    await new Promise((r) => setTimeout(r, 40));
    const enr = this.studentEnrollments.find((e) => e.id === id);
    if (!enr) throw new Error("Enrollment not found");
    enr.status = status;
    return { success: true, data: true };
  }

  async dropEnrollment(id: string): Promise<ApiResponse<boolean>> {
    return this.updateEnrollmentStatus(id, "DROPPED");
  }

  // ==========================================
  // Master Time Slots & Timetable Scheduling
  // ==========================================

  async getMasterTimeSlots(): Promise<ApiResponse<MasterTimeSlot[]>> {
    await new Promise((r) => setTimeout(r, 20));
    return { success: true, data: this.masterTimeSlots };
  }

  async getScheduledTimetable(params?: {
    day?: DayOfWeek;
    section?: string;
    facultyId?: string;
    roomNumber?: string;
  }): Promise<ApiResponse<ScheduledTimetableEntry[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.scheduledTimetable];

    if (params?.day && (params.day as string) !== "ALL") {
      items = items.filter((t) => t.day === params.day);
    }
    if (params?.section && params.section !== "ALL") {
      items = items.filter(
        (t) => t.section.toLowerCase() === params.section!.toLowerCase(),
      );
    }
    if (params?.facultyId && params.facultyId !== "ALL") {
      items = items.filter(
        (t) =>
          t.facultyId === params.facultyId ||
          t.facultyName.includes(params.facultyId!),
      );
    }
    if (params?.roomNumber && params.roomNumber !== "ALL") {
      items = items.filter((t) =>
        t.roomNumber.toLowerCase().includes(params.roomNumber!.toLowerCase()),
      );
    }

    return { success: true, data: items };
  }

  async getTimetableEntryById(
    id: string,
  ): Promise<ApiResponse<ScheduledTimetableEntry | null>> {
    await new Promise((r) => setTimeout(r, 20));
    const entry = this.scheduledTimetable.find((t) => t.id === id);
    return { success: true, data: entry || null };
  }

  async createTimetableEntry(
    data: Omit<ScheduledTimetableEntry, "id">,
  ): Promise<ApiResponse<ScheduledTimetableEntry>> {
    await new Promise((r) => setTimeout(r, 60));
    const newEntry: ScheduledTimetableEntry = {
      ...data,
      id: `tt-${Date.now()}`,
    };
    this.scheduledTimetable.push(newEntry);
    this.recalculateConflicts();
    return { success: true, data: newEntry };
  }

  async updateTimetableEntry(
    id: string,
    data: Partial<ScheduledTimetableEntry>,
  ): Promise<ApiResponse<ScheduledTimetableEntry>> {
    await new Promise((r) => setTimeout(r, 50));
    const idx = this.scheduledTimetable.findIndex((t) => t.id === id);
    if (idx === -1) throw new Error("Timetable entry not found");
    this.scheduledTimetable[idx] = { ...this.scheduledTimetable[idx], ...data };
    this.recalculateConflicts();
    return { success: true, data: this.scheduledTimetable[idx] };
  }

  async deleteTimetableEntry(id: string): Promise<ApiResponse<boolean>> {
    await new Promise((r) => setTimeout(r, 40));
    this.scheduledTimetable = this.scheduledTimetable.filter(
      (t) => t.id !== id,
    );
    this.recalculateConflicts();
    return { success: true, data: true };
  }

  async getTimetableConflicts(): Promise<ApiResponse<TimetableConflict[]>> {
    await new Promise((r) => setTimeout(r, 30));
    return { success: true, data: this.conflicts };
  }

  private recalculateConflicts(): void {
    const list: TimetableConflict[] = [];

    // Detect direct collisions: same day & timeslot
    for (let i = 0; i < this.scheduledTimetable.length; i++) {
      for (let j = i + 1; j < this.scheduledTimetable.length; j++) {
        const a = this.scheduledTimetable[i];
        const b = this.scheduledTimetable[j];

        if (a.day === b.day && a.timeSlotId === b.timeSlotId) {
          // 1. Faculty conflict
          if (a.facultyId === b.facultyId) {
            list.push({
              id: `cnf-fac-${a.id}-${b.id}`,
              conflictType: "FACULTY_CONFLICT",
              severity: "ERROR",
              title: "Faculty Schedule Clash",
              description: `${a.facultyName} is scheduled in both Section ${a.section} (${a.roomNumber}) and Section ${b.section} (${b.roomNumber}) at ${a.startTime}.`,
              conflictingEntryIds: [a.id, b.id],
              day: a.day,
              timeSlot: `${a.startTime} - ${a.endTime}`,
              resourceName: a.facultyName,
            });
          }
          // 2. Room conflict
          if (a.roomNumber === b.roomNumber) {
            list.push({
              id: `cnf-room-${a.id}-${b.id}`,
              conflictType: "ROOM_CONFLICT",
              severity: "ERROR",
              title: "Classroom Double-Booking",
              description: `${a.roomNumber} is simultaneously booked for ${a.subjectCode} (Sec ${a.section}) and ${b.subjectCode} (Sec ${b.section}).`,
              conflictingEntryIds: [a.id, b.id],
              day: a.day,
              timeSlot: `${a.startTime} - ${a.endTime}`,
              resourceName: a.roomNumber,
            });
          }
          // 3. Section conflict
          if (a.section === b.section && a.semester === b.semester) {
            list.push({
              id: `cnf-sec-${a.id}-${b.id}`,
              conflictType: "SECTION_CONFLICT",
              severity: "ERROR",
              title: "Section Overlap Conflict",
              description: `Section ${a.section} (Sem ${a.semester}) has two concurrent periods: ${a.subjectCode} and ${b.subjectCode}.`,
              conflictingEntryIds: [a.id, b.id],
              day: a.day,
              timeSlot: `${a.startTime} - ${a.endTime}`,
              resourceName: `Section ${a.section}`,
            });
          }
        }
      }
    }

    this.conflicts = list;
  }

  // Legacy getTimetable for backwards compatibility
  async getTimetable(
    day?: string,
    section?: string,
  ): Promise<ApiResponse<TimetableSlotItem[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let items = [...this.timetable];
    if (day) {
      items = items.filter((t) => t.day.toLowerCase() === day.toLowerCase());
    }
    if (section) {
      items = items.filter(
        (t) => t.section.toLowerCase() === section.toLowerCase(),
      );
    }
    return { success: true, data: items };
  }
}

export const academicsService = new AcademicsService();
