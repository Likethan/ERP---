import { ApiResponse, PaginatedResponse } from "@campusos/types";
import { apiFetch } from "@/lib/api-client";
import { StudentComprehensiveDetail } from "@/types/domain";
import {
  GuardianRecord,
  PersonDocument,
  AcademicMilestone,
} from "@/types/people";
import { MOCK_STUDENTS } from "@/mocks/students.mock";
import {
  MOCK_GUARDIANS_POOL,
  MOCK_STUDENT_DOCUMENTS,
  MOCK_ACADEMIC_MILESTONES,
} from "@/mocks/people.mock";

export interface StudentFilterParams {
  search?: string;
  programId?: string;
  program?: string;
  department?: string;
  semester?: number;
  section?: string;
  status?: string;
  gender?: string;
  academicYear?: string;
  batch?: string;
  quota?: string;
  page?: number;
  pageSize?: number;
}

class StudentsService {
  private students: StudentComprehensiveDetail[] = [...MOCK_STUDENTS];
  private guardiansPool: Record<string, GuardianRecord[]> = {
    ...MOCK_GUARDIANS_POOL,
  };
  private documentsPool: Record<string, PersonDocument[]> = {
    ...MOCK_STUDENT_DOCUMENTS,
  };
  private milestonesPool: Record<string, AcademicMilestone[]> = {
    ...MOCK_ACADEMIC_MILESTONES,
  };

  async list(
    params?: StudentFilterParams,
  ): Promise<PaginatedResponse<StudentComprehensiveDetail>> {
    try {
      const qParams = new URLSearchParams();
      if (params?.page) qParams.append("page", params.page.toString());
      if (params?.pageSize)
        qParams.append("page_size", params.pageSize.toString());
      if (params?.search) qParams.append("search", params.search);
      if (params?.status && params.status !== "ALL")
        qParams.append("status", params.status);
      if (params?.programId) qParams.append("program_id", params.programId);

      const qs = qParams.toString();
      const res = await apiFetch<any[]>(
        `/api/v1/students${qs ? `?${qs}` : ""}`,
      );
      if (
        res &&
        res.success &&
        Array.isArray(res.data) &&
        res.data.length > 0
      ) {
        const liveStudents: StudentComprehensiveDetail[] = res.data.map(
          (b: any) => ({
            id: b.id,
            rollNumber: b.roll_number || b.admission_number || "REG-001",
            registrationNumber:
              b.registration_number || b.admission_number || "ADM-001",
            firstName: b.first_name,
            lastName: b.last_name,
            email: b.email,
            phone: b.phone_number || "+91 90000 00000",
            gender: b.gender || "Male",
            dateOfBirth: "2004-01-01",
            bloodGroup: "O+",
            status: (b.status as any) || "ACTIVE",
            admissionDate: "2023-08-01",
            program: {
              id: b.program_id || "prog-cse",
              code: b.program_code || "BTECH-CSE",
              name: b.program_name || "B.Tech Computer Science & Engineering",
              department: "Computer Science & Engineering",
            },
            academicYear: "2026-2027",
            currentSemester: 1,
            section: "A",
            batch: "2023-2027",
            quota: "MERIT",
            address: {
              street: "Campus Avenue",
              city: "Coimbatore",
              state: "Tamil Nadu",
              pincode: "641001",
            },
            guardian: {
              name: "Guardian",
              relation: "Parent",
              phone: "+91 90000 00001",
              email: "parent@example.com",
              occupation: "Professional",
            },
            academicStats: {
              cgpa: 8.2,
              totalCreditsEarned: 24,
              backlogs: 0,
              rank: 12,
            },
            attendanceSummary: {
              overallPercentage: 88.5,
              totalClasses: 120,
              attendedClasses: 106,
              status: "EXCELLENT",
            },
            financeSummary: {
              totalBilled: 125000,
              totalPaid: 125000,
              pendingDue: 0,
              status: "CLEAR",
            },
            placementSummary: {
              isEligible: true,
              appliedDrives: 0,
              interviewsScheduled: 0,
              offersReceived: 0,
            },
            enrolledCourses: [],
            recentActivity: [],
            documents: [],
          }),
        );

        const page = params?.page || 1;
        const pageSize = params?.pageSize || 10;
        const totalRecords = liveStudents.length;
        const totalPages = Math.ceil(totalRecords / pageSize) || 1;
        return {
          success: true,
          data: liveStudents,
          pagination: {
            page,
            pageSize,
            totalRecords,
            totalPages,
            page_size: pageSize,
            total_records: totalRecords,
            total_pages: totalPages,
            hasNext: page < totalPages,
            hasPrev: page > 1,
          },
        };
      }
    } catch {
      // Graceful fallback to local mock state when backend is unreachable or offline
    }

    let filtered = [...this.students];

    if (params?.search) {
      const q = params.search.toLowerCase().trim();
      filtered = filtered.filter(
        (s) =>
          s.firstName.toLowerCase().includes(q) ||
          s.lastName.toLowerCase().includes(q) ||
          s.rollNumber.toLowerCase().includes(q) ||
          s.registrationNumber.toLowerCase().includes(q) ||
          s.email.toLowerCase().includes(q),
      );
    }

    if (params?.department && params.department !== "ALL") {
      filtered = filtered.filter(
        (s) =>
          s.program.department.toLowerCase() ===
          params.department?.toLowerCase(),
      );
    }

    if (params?.program && params.program !== "ALL") {
      filtered = filtered.filter(
        (s) =>
          s.program.code === params.program ||
          s.program.name.includes(params.program!),
      );
    }

    if (params?.status && params.status !== "ALL") {
      filtered = filtered.filter((s) => s.status === params.status);
    }

    if (params?.gender && params.gender !== "ALL") {
      filtered = filtered.filter(
        (s) => s.gender.toLowerCase() === params.gender?.toLowerCase(),
      );
    }

    if (params?.section && params.section !== "ALL") {
      filtered = filtered.filter((s) => s.section === params.section);
    }

    if (params?.semester && !isNaN(Number(params.semester))) {
      filtered = filtered.filter(
        (s) => s.currentSemester === Number(params.semester),
      );
    }

    if (params?.academicYear && params.academicYear !== "ALL") {
      filtered = filtered.filter((s) => s.academicYear === params.academicYear);
    }

    const page = params?.page || 1;
    const pageSize = params?.pageSize || 10;
    const totalRecords = filtered.length;
    const totalPages = Math.ceil(totalRecords / pageSize) || 1;
    const startIndex = (page - 1) * pageSize;
    const paginatedItems = filtered.slice(startIndex, startIndex + pageSize);

    return {
      success: true,
      data: paginatedItems,
      pagination: {
        page,
        pageSize,
        totalRecords,
        totalPages,
        page_size: pageSize,
        total_records: totalRecords,
        total_pages: totalPages,
        hasNext: page < totalPages,
        hasPrev: page > 1,
      },
    };
  }

  async getById(
    id: string,
  ): Promise<ApiResponse<StudentComprehensiveDetail | null>> {
    try {
      const res = await apiFetch<any>(`/api/v1/students/${id}`);
      if (res && res.success && res.data) {
        const b = res.data;
        const liveStudent: StudentComprehensiveDetail = {
          id: b.id,
          rollNumber: b.roll_number || b.admission_number || "REG-001",
          registrationNumber:
            b.registration_number || b.admission_number || "ADM-001",
          firstName: b.first_name,
          lastName: b.last_name,
          email: b.email,
          phone: b.phone_number || "+91 90000 00000",
          gender: b.gender || "Male",
          dateOfBirth: b.date_of_birth || "2004-01-01",
          bloodGroup: b.blood_group || "O+",
          status: (b.status as any) || "ACTIVE",
          admissionDate: b.admission_date || "2023-08-01",
          program: {
            id: b.program_id || "prog-cse",
            code: b.program_code || "BTECH-CSE",
            name: b.program_name || "B.Tech Computer Science & Engineering",
            department: "Computer Science & Engineering",
          },
          academicYear: "2026-2027",
          currentSemester: b.current_semester || 1,
          section: b.section_name || "A",
          batch: "2023-2027",
          quota: "MERIT",
          address: {
            street: "Campus Avenue",
            city: "Coimbatore",
            state: "Tamil Nadu",
            pincode: "641001",
          },
          guardian: {
            name: "Guardian",
            relation: "Parent",
            phone: "+91 90000 00001",
            email: "parent@example.com",
            occupation: "Professional",
          },
          academicStats: {
            cgpa: 8.2,
            totalCreditsEarned: 24,
            backlogs: 0,
            rank: 12,
          },
          attendanceSummary: {
            overallPercentage: 88.5,
            totalClasses: 120,
            attendedClasses: 106,
            status: "EXCELLENT",
          },
          financeSummary: {
            totalBilled: 145000,
            totalPaid: 145000,
            pendingDue: 0,
            status: "CLEAR",
          },
          placementSummary: {
            isEligible: true,
            appliedDrives: 0,
            interviewsScheduled: 0,
            offersReceived: 0,
          },
          enrolledCourses: [],
          recentActivity: [],
          documents: [],
          guardians: this.guardiansPool[b.id] || [],
          documentsVault: this.documentsPool[b.id] || [],
          milestones: this.milestonesPool[b.id] || [],
        };
        return { success: true, data: liveStudent };
      }
    } catch {
      // Fall through to local collection
    }

    const student = this.students.find(
      (s) => s.id === id || s.rollNumber.toLowerCase() === id.toLowerCase(),
    );

    if (!student) {
      return { success: true, data: null };
    }

    // Attach relational collections
    const fullStudent: StudentComprehensiveDetail = {
      ...student,
      guardians:
        this.guardiansPool[student.id] ||
        (student.guardian
          ? [
              {
                id: `grd-${student.id}-1`,
                name: student.guardian.name,
                relation: "FATHER",
                relationLabel: student.guardian.relation,
                phone: student.guardian.phone,
                email: student.guardian.email,
                occupation: student.guardian.occupation,
                isPrimary: true,
                isEmergencyContact: true,
              },
            ]
          : []),
      documentsVault: this.documentsPool[student.id] || [],
      milestones: this.milestonesPool[student.id] || [],
    };

    return {
      success: true,
      data: fullStudent,
    };
  }

  async create(
    data: Partial<StudentComprehensiveDetail>,
  ): Promise<ApiResponse<StudentComprehensiveDetail>> {
    const newStudent: StudentComprehensiveDetail = {
      id: `stu-${Date.now()}`,
      rollNumber: data.rollNumber || `24CSE0${this.students.length + 101}`,
      registrationNumber: `REG2024CS0${this.students.length + 101}`,
      firstName: data.firstName || "New",
      lastName: data.lastName || "Student",
      email: data.email || "new.student@student.campusos.edu",
      phone: data.phone || "+91 90000 00000",
      gender: data.gender || "Male",
      dateOfBirth: data.dateOfBirth || "2004-01-01",
      bloodGroup: data.bloodGroup || "O+",
      status: data.status || "ACTIVE",
      admissionDate:
        data.admissionDate || new Date().toISOString().split("T")[0],
      program: data.program || {
        id: "prog-cse-btech",
        code: "BTECH-CSE",
        name: "B.Tech Computer Science & Engineering",
        department: "Computer Science & Engineering",
      },
      academicYear: data.academicYear || "2026-2027",
      currentSemester: data.currentSemester || 1,
      section: data.section || "A",
      batch: data.batch || "2024-2028",
      quota: data.quota || "MERIT",
      address: data.address || {
        street: "University Campus Road",
        city: "Bengaluru",
        state: "Karnataka",
        pincode: "560001",
      },
      guardian: data.guardian || {
        name: "Guardian Name",
        relation: "Father",
        phone: "+91 98450 00000",
        email: "guardian@example.com",
        occupation: "Professional",
      },
      academicStats: {
        cgpa: 8.0,
        totalCreditsEarned: 24,
        backlogs: 0,
        rank: this.students.length + 1,
      },
      attendanceSummary: {
        overallPercentage: 85.0,
        totalClasses: 120,
        attendedClasses: 102,
        status: "EXCELLENT",
      },
      financeSummary: {
        totalBilled: 145000,
        totalPaid: 145000,
        pendingDue: 0,
        status: "CLEAR",
      },
      placementSummary: {
        isEligible: true,
        appliedDrives: 0,
        interviewsScheduled: 0,
        offersReceived: 0,
      },
      enrolledCourses: [],
      recentActivity: [
        {
          id: `act-${Date.now()}`,
          action:
            "Student record formally registered into CampusOS People Registry",
          timestamp: "Just now",
          domain: "Admissions",
          actor: "Registrar Office",
        },
      ],
      documents: [],
    };

    try {
      const res = await apiFetch<any>("/api/v1/students", {
        method: "POST",
        body: JSON.stringify({
          first_name: newStudent.firstName,
          last_name: newStudent.lastName,
          email: newStudent.email,
          phone_number: newStudent.phone,
          admission_number: newStudent.rollNumber,
          program_id: newStudent.program?.id,
        }),
      });
      if (res && res.success && res.data?.id) {
        newStudent.id = res.data.id;
      }
    } catch {
      // Graceful local fallback
    }

    this.students.unshift(newStudent);

    // Initialize collections
    this.guardiansPool[newStudent.id] = [
      {
        id: `grd-${newStudent.id}-1`,
        name: newStudent.guardian.name,
        relation: "FATHER",
        relationLabel: newStudent.guardian.relation,
        phone: newStudent.guardian.phone,
        email: newStudent.guardian.email,
        occupation: newStudent.guardian.occupation,
        isPrimary: true,
        isEmergencyContact: true,
      },
    ];

    this.milestonesPool[newStudent.id] = [
      {
        id: `mls-${newStudent.id}-1`,
        title: "Admission Formally Completed",
        category: "ADMISSION",
        date: newStudent.admissionDate,
        semester: 1,
        description: `Admitted to ${newStudent.program.name} under ${newStudent.quota} quota.`,
        status: "COMPLETED",
        awardedBy: "Dean of Admissions",
      },
    ];

    return {
      success: true,
      data: newStudent,
    };
  }

  async update(
    id: string,
    data: Partial<StudentComprehensiveDetail>,
  ): Promise<ApiResponse<StudentComprehensiveDetail>> {
    try {
      await apiFetch<any>(`/api/v1/students/${id}`, {
        method: "PUT",
        body: JSON.stringify({
          first_name: data.firstName,
          last_name: data.lastName,
          phone_number: data.phone,
        }),
      });
    } catch {
      // Graceful local fallback
    }

    const idx = this.students.findIndex(
      (s) => s.id === id || s.rollNumber.toLowerCase() === id.toLowerCase(),
    );
    if (idx === -1) {
      throw new Error(`Student not found with ID ${id}`);
    }
    this.students[idx] = { ...this.students[idx], ...data };
    return {
      success: true,
      data: this.students[idx],
    };
  }

  // ==========================================
  // Guardian Sub-Service Methods
  // ==========================================

  async getGuardians(
    studentId: string,
  ): Promise<ApiResponse<GuardianRecord[]>> {
    return {
      success: true,
      data: this.guardiansPool[studentId] || [],
    };
  }

  async addGuardian(
    studentId: string,
    data: Partial<GuardianRecord>,
  ): Promise<ApiResponse<GuardianRecord>> {
    const newGrd: GuardianRecord = {
      id: `grd-${Date.now()}`,
      name: data.name || "Guardian Name",
      relation: data.relation || "GUARDIAN",
      relationLabel: data.relationLabel || "Guardian",
      phone: data.phone || "+91 90000 00000",
      email: data.email || "guardian@example.com",
      occupation: data.occupation || "Employed",
      annualIncome: data.annualIncome || "₹ 10,00,000",
      isPrimary: Boolean(data.isPrimary),
      isEmergencyContact: Boolean(data.isEmergencyContact),
      address: data.address,
    };

    if (!this.guardiansPool[studentId]) {
      this.guardiansPool[studentId] = [];
    }
    this.guardiansPool[studentId].push(newGrd);
    return { success: true, data: newGrd };
  }

  async updateGuardian(
    studentId: string,
    guardianId: string,
    data: Partial<GuardianRecord>,
  ): Promise<ApiResponse<GuardianRecord>> {
    const list = this.guardiansPool[studentId] || [];
    const idx = list.findIndex((g) => g.id === guardianId);
    if (idx === -1) throw new Error("Guardian record not found");
    list[idx] = { ...list[idx], ...data };
    return { success: true, data: list[idx] };
  }

  async deleteGuardian(
    studentId: string,
    guardianId: string,
  ): Promise<ApiResponse<boolean>> {
    if (this.guardiansPool[studentId]) {
      this.guardiansPool[studentId] = this.guardiansPool[studentId].filter(
        (g) => g.id !== guardianId,
      );
    }
    return { success: true, data: true };
  }

  // ==========================================
  // Document Vault Sub-Service Methods
  // ==========================================

  async getDocuments(
    studentId: string,
  ): Promise<ApiResponse<PersonDocument[]>> {
    return {
      success: true,
      data: this.documentsPool[studentId] || [],
    };
  }

  async uploadDocument(
    studentId: string,
    data: Partial<PersonDocument>,
  ): Promise<ApiResponse<PersonDocument>> {
    const newDoc: PersonDocument = {
      id: `doc-${Date.now()}`,
      name: data.name || "Uploaded Certificate",
      category: data.category || "ACADEMIC",
      fileSize: data.fileSize || "1.2 MB",
      mimeType: data.mimeType || "application/pdf",
      uploadedAt: new Date().toISOString().split("T")[0],
      uploadedBy: data.uploadedBy || "Student (Portal)",
      status: "UNDER_REVIEW",
    };

    if (!this.documentsPool[studentId]) {
      this.documentsPool[studentId] = [];
    }
    this.documentsPool[studentId].unshift(newDoc);
    return { success: true, data: newDoc };
  }

  async verifyDocument(
    studentId: string,
    documentId: string,
    verifierName = "Verification Officer",
  ): Promise<ApiResponse<PersonDocument>> {
    const list = this.documentsPool[studentId] || [];
    const doc = list.find((d) => d.id === documentId);
    if (!doc) throw new Error("Document not found");
    doc.status = "VERIFIED";
    doc.verifiedAt = new Date().toISOString().split("T")[0];
    doc.verifiedBy = verifierName;
    return { success: true, data: doc };
  }

  async rejectDocument(
    studentId: string,
    documentId: string,
    reason: string,
  ): Promise<ApiResponse<PersonDocument>> {
    const list = this.documentsPool[studentId] || [];
    const doc = list.find((d) => d.id === documentId);
    if (!doc) throw new Error("Document not found");
    doc.status = "REJECTED";
    doc.rejectionReason = reason;
    return { success: true, data: doc };
  }

  async deleteDocument(
    studentId: string,
    documentId: string,
  ): Promise<ApiResponse<boolean>> {
    if (this.documentsPool[studentId]) {
      this.documentsPool[studentId] = this.documentsPool[studentId].filter(
        (d) => d.id !== documentId,
      );
    }
    return { success: true, data: true };
  }

  // ==========================================
  // Milestone Timeline Sub-Service Methods
  // ==========================================

  async getMilestones(
    studentId: string,
  ): Promise<ApiResponse<AcademicMilestone[]>> {
    return {
      success: true,
      data: this.milestonesPool[studentId] || [],
    };
  }

  async addMilestone(
    studentId: string,
    data: Partial<AcademicMilestone>,
  ): Promise<ApiResponse<AcademicMilestone>> {
    const newMls: AcademicMilestone = {
      id: `mls-${Date.now()}`,
      title: data.title || "Academic Achievement",
      category: data.category || "ACHIEVEMENT",
      date: data.date || new Date().toISOString().split("T")[0],
      semester: data.semester || 1,
      description:
        data.description || "Official milestone recorded in CampusOS Registry.",
      status: data.status || "COMPLETED",
      awardedBy: data.awardedBy,
      certificateRef: data.certificateRef,
    };

    if (!this.milestonesPool[studentId]) {
      this.milestonesPool[studentId] = [];
    }
    this.milestonesPool[studentId].unshift(newMls);
    return { success: true, data: newMls };
  }
}

export const studentsService = new StudentsService();
