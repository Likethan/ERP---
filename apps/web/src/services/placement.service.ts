/**
 * CampusOS Placement Management — Reactive Service Interface & Mock Adapter
 * Simulates future FastAPI endpoints with in-memory persistence and cross-entity relational synchronization.
 */

import { ApiResponse } from "@campusos/types";
import {
  StudentPlacementProfile,
  Company,
  JobDrive,
  Position,
  EligibilitySnapshot,
  EligibilityStatus,
  Application,
  Interview,
  InterviewEvaluation,
  Offer,
  PlacementOutcome,
  PlacementDashboardSummary,
  PlacementReportFilter,
  ResumeStatus,
  StudentSkillsProfile,
} from "@/types/placement";
import {
  MOCK_PLACEMENT_PROFILES,
  MOCK_COMPANIES,
  MOCK_JOB_DRIVES,
  MOCK_POSITIONS,
  MOCK_APPLICATIONS,
  MOCK_INTERVIEWS,
  MOCK_OFFERS,
  MOCK_PLACEMENT_OUTCOMES,
  MOCK_PLACEMENT_DASHBOARD,
} from "@/mocks/placement.mock";
import { calculateEligibility } from "./placement-calculator";

class PlacementService {
  private profiles: StudentPlacementProfile[] = [...MOCK_PLACEMENT_PROFILES];
  private companies: Company[] = [...MOCK_COMPANIES];
  private drives: JobDrive[] = [...MOCK_JOB_DRIVES];
  private positions: Position[] = [...MOCK_POSITIONS];
  private applications: Application[] = [...MOCK_APPLICATIONS];
  private interviews: Interview[] = [...MOCK_INTERVIEWS];
  private offers: Offer[] = [...MOCK_OFFERS];
  private outcomes: PlacementOutcome[] = [...MOCK_PLACEMENT_OUTCOMES];
  private dashboard: PlacementDashboardSummary = { ...MOCK_PLACEMENT_DASHBOARD };

  // ==========================================
  // 1. Dashboard
  // ==========================================

  async getPlacementSummary(): Promise<ApiResponse<PlacementDashboardSummary>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: this.dashboard };
  }

  // ==========================================
  // 2. Student Placement Profiles
  // ==========================================

  async getPlacementStudents(): Promise<ApiResponse<StudentPlacementProfile[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: [...this.profiles] };
  }

  async getPlacementStudentById(id: string): Promise<ApiResponse<StudentPlacementProfile | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const prof = this.profiles.find((p) => p.id === id || p.studentId === id) || null;
    return { success: true, data: prof };
  }

  async updateStudentSkills(
    studentId: string,
    skills: StudentSkillsProfile
  ): Promise<ApiResponse<StudentPlacementProfile>> {
    await new Promise((r) => setTimeout(r, 60));
    const idx = this.profiles.findIndex((p) => p.studentId === studentId || p.id === studentId);
    if (idx === -1) throw new Error("Student placement profile not found");

    this.profiles[idx] = {
      ...this.profiles[idx],
      skills,
      updatedAt: new Date().toISOString(),
    };
    return { success: true, data: this.profiles[idx] };
  }

  async updateResumeStatus(
    studentId: string,
    status: ResumeStatus,
    notes?: string
  ): Promise<ApiResponse<StudentPlacementProfile>> {
    await new Promise((r) => setTimeout(r, 60));
    const idx = this.profiles.findIndex((p) => p.studentId === studentId || p.id === studentId);
    if (idx === -1) throw new Error("Student placement profile not found");

    this.profiles[idx] = {
      ...this.profiles[idx],
      resumeStatus: status,
      resumeNotes: notes,
      resumeUpdatedAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    this.profiles[idx].timeline.push({
      id: `tl-${Date.now()}`,
      action: `Resume status updated to ${status}`,
      actor: "Placement Officer",
      timestamp: new Date().toISOString(),
      details: notes,
    });
    return { success: true, data: this.profiles[idx] };
  }

  // ==========================================
  // 3. Corporate Partners / Companies
  // ==========================================

  async getCompanies(): Promise<ApiResponse<Company[]>> {
    await new Promise((r) => setTimeout(r, 40));
    return { success: true, data: [...this.companies] };
  }

  async getCompanyById(id: string): Promise<ApiResponse<Company | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const comp = this.companies.find((c) => c.id === id || c.code === id) || null;
    return { success: true, data: comp };
  }

  async createCompany(data: Partial<Company>): Promise<ApiResponse<Company>> {
    await new Promise((r) => setTimeout(r, 80));
    const newComp: Company = {
      id: `comp-${Date.now()}`,
      code: (data.code || data.name?.replace(/\s+/g, "").toUpperCase() || "COMP").slice(0, 10),
      name: data.name || "Corporate Partner",
      legalName: data.legalName || data.name,
      industry: data.industry || "Information Technology",
      companyType: data.companyType || "PRODUCT",
      tier: data.tier || "TIER_2_DREAM",
      website: data.website || "https://example.com",
      headquarters: data.headquarters || "Bengaluru, Karnataka",
      locations: data.locations || ["Bengaluru"],
      contacts: data.contacts || [],
      status: "ACTIVE",
      activeDrivesCount: 0,
      totalHiredCount: 0,
      averageCtcLpa: data.averageCtcLpa || 10.0,
      highestCtcLpa: data.highestCtcLpa || 12.0,
      relationshipStatus: "NEW",
      notes: data.notes,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      timeline: [
        {
          id: `ctl-${Date.now()}`,
          action: "Company Onboarded",
          actor: "Placement Officer",
          timestamp: new Date().toISOString(),
        },
      ],
    };
    this.companies.unshift(newComp);
    return { success: true, data: newComp };
  }

  async updateCompany(id: string, data: Partial<Company>): Promise<ApiResponse<Company>> {
    await new Promise((r) => setTimeout(r, 60));
    const idx = this.companies.findIndex((c) => c.id === id);
    if (idx === -1) throw new Error("Company not found");

    this.companies[idx] = {
      ...this.companies[idx],
      ...data,
      updatedAt: new Date().toISOString(),
    };
    return { success: true, data: this.companies[idx] };
  }

  // ==========================================
  // 4. Job Drives
  // ==========================================

  async getJobDrives(status?: string): Promise<ApiResponse<JobDrive[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let list = [...this.drives];
    if (status && status !== "ALL") {
      list = list.filter((d) => d.status === status);
    }
    return { success: true, data: list };
  }

  async getJobDriveById(id: string): Promise<ApiResponse<JobDrive | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const drive = this.drives.find((d) => d.id === id || d.code === id) || null;
    return { success: true, data: drive };
  }

  async createJobDrive(data: Partial<JobDrive>): Promise<ApiResponse<JobDrive>> {
    await new Promise((r) => setTimeout(r, 80));
    const company = this.companies.find((c) => c.id === data.companyId);
    const newDrive: JobDrive = {
      id: `drv-${Date.now()}`,
      code: `DRV-2026-${(data.companyName || "CAMPUS").replace(/\s+/g, "").toUpperCase().slice(0, 6)}`,
      title: data.title || "Campus Recruitment Drive 2026",
      companyId: data.companyId || "comp-cisco",
      companyName: company?.name || data.companyName || "Corporate Partner",
      companyTier: company?.tier || "TIER_2_DREAM",
      driveType: data.driveType || "ON_CAMPUS",
      driveDate: data.driveDate || new Date(Date.now() + 14 * 86400000).toISOString().split("T")[0],
      applicationDeadline: data.applicationDeadline || new Date(Date.now() + 7 * 86400000).toISOString().split("T")[0],
      location: data.location || "Campus Auditorium",
      academicYear: data.academicYear || "2026-2027",
      batchGraduationYear: data.batchGraduationYear || 2026,
      positionsCount: 1,
      eligibleStudentsCount: 100,
      applicantsCount: 0,
      shortlistedCount: 0,
      interviewsCount: 0,
      offersCount: 0,
      status: "DRAFT",
      description: data.description || "Recruitment drive",
      guidelines: data.guidelines,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      timeline: [
        {
          id: `dtl-${Date.now()}`,
          action: "Drive Created as DRAFT",
          actor: "Placement Officer",
          timestamp: new Date().toISOString(),
        },
      ],
    };
    this.drives.unshift(newDrive);
    return { success: true, data: newDrive };
  }

  async publishJobDrive(id: string): Promise<ApiResponse<JobDrive>> {
    await new Promise((r) => setTimeout(r, 60));
    const idx = this.drives.findIndex((d) => d.id === id);
    if (idx === -1) throw new Error("Job drive not found");

    this.drives[idx] = {
      ...this.drives[idx],
      status: "OPEN",
      updatedAt: new Date().toISOString(),
    };
    this.drives[idx].timeline.push({
      id: `dtl-${Date.now()}`,
      action: "Drive Published & Applications Opened",
      actor: "Placement Officer",
      timestamp: new Date().toISOString(),
    });
    return { success: true, data: this.drives[idx] };
  }

  async closeJobDrive(id: string): Promise<ApiResponse<JobDrive>> {
    await new Promise((r) => setTimeout(r, 60));
    const idx = this.drives.findIndex((d) => d.id === id);
    if (idx === -1) throw new Error("Job drive not found");

    this.drives[idx] = {
      ...this.drives[idx],
      status: "CLOSED",
      updatedAt: new Date().toISOString(),
    };
    this.drives[idx].timeline.push({
      id: `dtl-${Date.now()}`,
      action: "Applications Closed",
      actor: "Placement Officer",
      timestamp: new Date().toISOString(),
    });
    return { success: true, data: this.drives[idx] };
  }

  // ==========================================
  // 5. Positions
  // ==========================================

  async getPositions(driveId?: string): Promise<ApiResponse<Position[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let list = [...this.positions];
    if (driveId) {
      list = list.filter((p) => p.driveId === driveId);
    }
    return { success: true, data: list };
  }

  async getPositionById(id: string): Promise<ApiResponse<Position | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const pos = this.positions.find((p) => p.id === id) || null;
    return { success: true, data: pos };
  }

  async createPosition(data: Partial<Position>): Promise<ApiResponse<Position>> {
    await new Promise((r) => setTimeout(r, 60));
    const drive = this.drives.find((d) => d.id === data.driveId);
    const newPos: Position = {
      id: `pos-${Date.now()}`,
      driveId: data.driveId || "drv-cisco-2026",
      driveCode: drive?.code || "DRV-2026",
      companyId: drive?.companyId || data.companyId || "comp-cisco",
      companyName: drive?.companyName || data.companyName || "Corporate Partner",
      title: data.title || "Associate Software Engineer",
      departmentFunction: data.departmentFunction || "Engineering",
      employmentType: data.employmentType || "FULL_TIME",
      location: data.location || "Bengaluru",
      vacancies: data.vacancies || 5,
      ctcLpa: data.ctcLpa || 10.0,
      baseSalaryLpa: data.baseSalaryLpa || 8.5,
      variableLpa: data.variableLpa || 1.5,
      stipendMonthly: data.stipendMonthly,
      bondMonths: data.bondMonths || 0,
      requiredSkills: data.requiredSkills || ["Problem Solving"],
      minCgpa: data.minCgpa || 7.0,
      maxBacklogs: data.maxBacklogs || 0,
      minAttendancePercent: data.minAttendancePercent || 75,
      targetPrograms: data.targetPrograms || ["B.Tech Computer Science & Engineering"],
      targetDepartments: data.targetDepartments || ["Computer Science & Engineering"],
      graduationYear: data.graduationYear || 2026,
      status: "OPEN",
      description: data.description,
      responsibilities: data.responsibilities,
      createdAt: new Date().toISOString(),
    };
    this.positions.push(newPos);
    return { success: true, data: newPos };
  }

  // ==========================================
  // 6. Eligibility Engine
  // ==========================================

  async evaluateEligibility(
    studentId: string,
    positionId: string
  ): Promise<ApiResponse<EligibilitySnapshot>> {
    await new Promise((r) => setTimeout(r, 30));
    const student = this.profiles.find((p) => p.studentId === studentId || p.id === studentId);
    const position = this.positions.find((p) => p.id === positionId);

    if (!student || !position) {
      throw new Error("Student or Position record not found for evaluation");
    }

    const snapshot = calculateEligibility(student, position);
    return { success: true, data: snapshot };
  }

  async overrideEligibility(
    snapshot: EligibilitySnapshot,
    newStatus: EligibilityStatus,
    reason: string,
    authority: string
  ): Promise<ApiResponse<EligibilitySnapshot>> {
    await new Promise((r) => setTimeout(r, 60));
    const updated: EligibilitySnapshot = {
      ...snapshot,
      status: newStatus,
      isOverridden: true,
      overrideReason: reason,
      overriddenBy: authority,
      overriddenAt: new Date().toISOString(),
    };
    return { success: true, data: updated };
  }

  // ==========================================
  // 7. Applications & Shortlisting
  // ==========================================

  async getApplications(filters?: {
    studentId?: string;
    driveId?: string;
    status?: string;
  }): Promise<ApiResponse<Application[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let list = [...this.applications];
    if (filters?.studentId) {
      list = list.filter((a) => a.studentId === filters.studentId);
    }
    if (filters?.driveId) {
      list = list.filter((a) => a.driveId === filters.driveId);
    }
    if (filters?.status && filters.status !== "ALL") {
      list = list.filter((a) => a.status === filters.status);
    }
    return { success: true, data: list };
  }

  async getApplicationById(id: string): Promise<ApiResponse<Application | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const app = this.applications.find((a) => a.id === id || a.applicationCode === id) || null;
    return { success: true, data: app };
  }

  async submitApplication(data: {
    studentId: string;
    driveId: string;
    positionId: string;
    resumeVersion?: string;
  }): Promise<ApiResponse<Application>> {
    await new Promise((r) => setTimeout(r, 80));

    // Prevent duplicate application
    const existing = this.applications.find(
      (a) =>
        a.studentId === data.studentId &&
        a.positionId === data.positionId &&
        a.status !== "WITHDRAWN"
    );
    if (existing) {
      throw new Error("Student has already applied to this position.");
    }

    const student = this.profiles.find((p) => p.studentId === data.studentId || p.id === data.studentId);
    const drive = this.drives.find((d) => d.id === data.driveId);
    const position = this.positions.find((p) => p.id === data.positionId);

    if (!student || !drive || !position) {
      throw new Error("Invalid student, drive, or position reference.");
    }

    // Verify drive is open
    if (drive.status !== "OPEN") {
      throw new Error(`Drive is not open for applications (Current status: ${drive.status}).`);
    }

    // Evaluate eligibility
    const snapshot = calculateEligibility(student, position);
    if (snapshot.status === "INELIGIBLE") {
      throw new Error("Application rejected: Candidate does not meet mandatory eligibility requirements.");
    }

    const newApp: Application = {
      id: `app-${Date.now()}`,
      applicationCode: `APP-2026-${(this.applications.length + 1).toString().padStart(3, "0")}`,
      driveId: drive.id,
      driveName: drive.title,
      positionId: position.id,
      positionTitle: position.title,
      companyId: position.companyId,
      companyName: position.companyName,
      studentId: student.studentId,
      studentName: student.studentName,
      rollNumber: student.rollNumber,
      program: student.program,
      department: student.department,
      cgpa: student.cgpa,
      appliedDate: new Date().toISOString(),
      status: "SUBMITTED",
      currentStage: "APPLICATION",
      eligibilityStatus: snapshot.status,
      resumeVersion: data.resumeVersion || "v1.0",
      timeline: [
        {
          id: `atl-${Date.now()}`,
          action: "Application Submitted",
          actor: student.studentName,
          timestamp: new Date().toISOString(),
          details: `Position: ${position.title}`,
        },
      ],
    };

    this.applications.unshift(newApp);
    drive.applicantsCount += 1;
    student.applicationsCount += 1;

    return { success: true, data: newApp };
  }

  async shortlistApplications(
    applicationIds: string[],
    reviewer: string
  ): Promise<ApiResponse<Application[]>> {
    await new Promise((r) => setTimeout(r, 70));
    const modified: Application[] = [];

    this.applications = this.applications.map((app) => {
      if (applicationIds.includes(app.id)) {
        const updated: Application = {
          ...app,
          status: "SHORTLISTED",
          currentStage: "TECHNICAL",
        };
        updated.timeline.push({
          id: `atl-${Date.now()}-${Math.random()}`,
          action: "Candidate Shortlisted",
          actor: reviewer,
          timestamp: new Date().toISOString(),
        });
        modified.push(updated);

        // Update student profile count
        const prof = this.profiles.find((p) => p.studentId === app.studentId);
        if (prof) prof.shortlistsCount += 1;

        return updated;
      }
      return app;
    });

    return { success: true, data: modified };
  }

  async rejectApplication(
    applicationId: string,
    reason: string,
    reviewer: string
  ): Promise<ApiResponse<Application>> {
    await new Promise((r) => setTimeout(r, 60));
    const idx = this.applications.findIndex((a) => a.id === applicationId);
    if (idx === -1) throw new Error("Application not found");

    this.applications[idx] = {
      ...this.applications[idx],
      status: "REJECTED",
      rejectionReason: reason,
    };
    this.applications[idx].timeline.push({
      id: `atl-${Date.now()}`,
      action: "Application Rejected",
      actor: reviewer,
      timestamp: new Date().toISOString(),
      details: reason,
    });
    return { success: true, data: this.applications[idx] };
  }

  async withdrawApplication(
    applicationId: string,
    reason?: string
  ): Promise<ApiResponse<Application>> {
    await new Promise((r) => setTimeout(r, 60));
    const idx = this.applications.findIndex((a) => a.id === applicationId);
    if (idx === -1) throw new Error("Application not found");

    this.applications[idx] = {
      ...this.applications[idx],
      status: "WITHDRAWN",
    };
    this.applications[idx].timeline.push({
      id: `atl-${Date.now()}`,
      action: "Application Withdrawn by Candidate",
      actor: this.applications[idx].studentName,
      timestamp: new Date().toISOString(),
      details: reason,
    });
    return { success: true, data: this.applications[idx] };
  }

  // ==========================================
  // 8. Interviews & Evaluations
  // ==========================================

  async getInterviews(filters?: {
    studentId?: string;
    stage?: string;
    status?: string;
  }): Promise<ApiResponse<Interview[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let list = [...this.interviews];
    if (filters?.studentId) {
      list = list.filter((i) => i.studentId === filters.studentId);
    }
    if (filters?.stage && filters.stage !== "ALL") {
      list = list.filter((i) => i.stage === filters.stage);
    }
    if (filters?.status && filters.status !== "ALL") {
      list = list.filter((i) => i.status === filters.status);
    }
    return { success: true, data: list };
  }

  async getInterviewById(id: string): Promise<ApiResponse<Interview | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const intv = this.interviews.find((i) => i.id === id || i.interviewCode === id) || null;
    return { success: true, data: intv };
  }

  async scheduleInterview(data: Partial<Interview>): Promise<ApiResponse<Interview>> {
    await new Promise((r) => setTimeout(r, 70));
    const app = this.applications.find((a) => a.id === data.applicationId);
    if (!app) throw new Error("Application record not found");

    const newIntv: Interview = {
      id: `int-${Date.now()}`,
      interviewCode: `INT-2026-${(this.interviews.length + 1).toString().padStart(3, "0")}`,
      applicationId: app.id,
      studentId: app.studentId,
      studentName: app.studentName,
      rollNumber: app.rollNumber,
      companyId: app.companyId,
      companyName: app.companyName,
      positionId: app.positionId,
      positionTitle: app.positionTitle,
      stage: data.stage || "TECHNICAL",
      roundNumber: data.roundNumber || 1,
      date: data.date || new Date().toISOString().split("T")[0],
      time: data.time || "10:00 AM",
      durationMinutes: data.durationMinutes || 60,
      mode: data.mode || "ONLINE",
      locationOrMeetingUrl: data.locationOrMeetingUrl || "https://meet.google.com/xyz",
      interviewerName: data.interviewerName || "Technical Panel Member",
      interviewerEmail: data.interviewerEmail,
      status: "SCHEDULED",
      notes: data.notes,
      timeline: [
        {
          id: `itl-${Date.now()}`,
          action: "Interview Scheduled",
          actor: "Placement Coordinator",
          timestamp: new Date().toISOString(),
          details: `${data.stage || "TECHNICAL"} Round`,
        },
      ],
    };

    this.interviews.unshift(newIntv);
    const prof = this.profiles.find((p) => p.studentId === app.studentId);
    if (prof) prof.interviewsCount += 1;

    return { success: true, data: newIntv };
  }

  async rescheduleInterview(
    id: string,
    date: string,
    time: string,
    reason: string,
    actor: string
  ): Promise<ApiResponse<Interview>> {
    await new Promise((r) => setTimeout(r, 60));
    const idx = this.interviews.findIndex((i) => i.id === id);
    if (idx === -1) throw new Error("Interview not found");

    this.interviews[idx] = {
      ...this.interviews[idx],
      date,
      time,
      status: "RESCHEDULED",
    };
    this.interviews[idx].timeline.push({
      id: `itl-${Date.now()}`,
      action: "Interview Rescheduled",
      actor,
      timestamp: new Date().toISOString(),
      details: `New Time: ${date} ${time}. Reason: ${reason}`,
    });
    return { success: true, data: this.interviews[idx] };
  }

  async completeInterview(
    id: string,
    evaluation: InterviewEvaluation
  ): Promise<ApiResponse<Interview>> {
    await new Promise((r) => setTimeout(r, 60));
    const idx = this.interviews.findIndex((i) => i.id === id);
    if (idx === -1) throw new Error("Interview not found");

    this.interviews[idx] = {
      ...this.interviews[idx],
      status: "COMPLETED",
      evaluation,
    };
    this.interviews[idx].timeline.push({
      id: `itl-${Date.now()}`,
      action: "Evaluation Submitted & Interview Completed",
      actor: evaluation.evaluatedBy,
      timestamp: new Date().toISOString(),
      details: `Recommendation: ${evaluation.overallRecommendation}`,
    });
    return { success: true, data: this.interviews[idx] };
  }

  // ==========================================
  // 9. Offers & Acceptance
  // ==========================================

  async getOffers(filters?: {
    studentId?: string;
    status?: string;
  }): Promise<ApiResponse<Offer[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let list = [...this.offers];
    if (filters?.studentId) {
      list = list.filter((o) => o.studentId === filters.studentId);
    }
    if (filters?.status && filters.status !== "ALL") {
      list = list.filter((o) => o.status === filters.status);
    }
    return { success: true, data: list };
  }

  async getOfferById(id: string): Promise<ApiResponse<Offer | null>> {
    await new Promise((r) => setTimeout(r, 40));
    const offer = this.offers.find((o) => o.id === id || o.offerCode === id) || null;
    return { success: true, data: offer };
  }

  async releaseOffer(data: Partial<Offer>): Promise<ApiResponse<Offer>> {
    await new Promise((r) => setTimeout(r, 80));
    const app = this.applications.find((a) => a.id === data.applicationId);
    if (!app) throw new Error("Application record not found");

    const newOffer: Offer = {
      id: `ofr-${Date.now()}`,
      offerCode: `OFR-2026-${(this.offers.length + 1).toString().padStart(3, "0")}`,
      applicationId: app.id,
      studentId: app.studentId,
      studentName: app.studentName,
      rollNumber: app.rollNumber,
      companyId: app.companyId,
      companyName: app.companyName,
      positionId: app.positionId,
      positionTitle: app.positionTitle,
      employmentType: data.employmentType || "FULL_TIME",
      location: data.location || "Bengaluru",
      ctcLpa: data.ctcLpa || 10.0,
      baseSalaryLpa: data.baseSalaryLpa || 8.0,
      variableLpa: data.variableLpa,
      stipendMonthly: data.stipendMonthly,
      offerDate: new Date().toISOString().split("T")[0],
      responseDeadline: data.responseDeadline || new Date(Date.now() + 10 * 86400000).toISOString().split("T")[0],
      joiningDate: data.joiningDate || "2027-07-01",
      status: "RELEASED",
      releasedBy: data.releasedBy || "Placement Officer",
      timeline: [
        {
          id: `otl-${Date.now()}`,
          action: "Formal Offer Released",
          actor: data.releasedBy || "Placement Officer",
          timestamp: new Date().toISOString(),
          details: `CTC: ₹${data.ctcLpa || 10.0} LPA`,
        },
      ],
    };

    this.offers.unshift(newOffer);
    app.status = "SELECTED";
    app.currentStage = "OFFER";

    const prof = this.profiles.find((p) => p.studentId === app.studentId);
    if (prof) prof.offersCount += 1;

    return { success: true, data: newOffer };
  }

  async acceptOffer(id: string, studentNotes?: string): Promise<ApiResponse<Offer>> {
    await new Promise((r) => setTimeout(r, 70));
    const idx = this.offers.findIndex((o) => o.id === id);
    if (idx === -1) throw new Error("Offer not found");

    const offer = this.offers[idx];
    if (offer.status !== "RELEASED") {
      throw new Error(`Cannot accept offer with status ${offer.status}`);
    }

    this.offers[idx] = {
      ...offer,
      status: "ACCEPTED",
      responseNotes: studentNotes,
    };
    this.offers[idx].timeline.push({
      id: `otl-${Date.now()}`,
      action: "Offer Accepted by Candidate",
      actor: offer.studentName,
      timestamp: new Date().toISOString(),
      details: studentNotes || "Accepted through student placement portal",
    });

    // Automatically transition placement outcome
    const prof = this.profiles.find((p) => p.studentId === offer.studentId);
    if (prof) {
      prof.placementStatus = "PLACED";
      prof.placedCompany = offer.companyName;
      prof.placedPackageLpa = offer.ctcLpa;
      prof.timeline.push({
        id: `ptl-${Date.now()}`,
        action: `Placement Confirmed at ${offer.companyName}`,
        actor: "System",
        timestamp: new Date().toISOString(),
        details: `CTC: ₹${offer.ctcLpa} LPA`,
      });
    }

    const outIdx = this.outcomes.findIndex((o) => o.studentId === offer.studentId);
    if (outIdx !== -1) {
      this.outcomes[outIdx] = {
        ...this.outcomes[outIdx],
        status: "PLACED",
        companyId: offer.companyId,
        companyName: offer.companyName,
        positionId: offer.positionId,
        positionTitle: offer.positionTitle,
        offerId: offer.id,
        ctcLpa: offer.ctcLpa,
        joiningDate: offer.joiningDate,
        confirmedAt: new Date().toISOString(),
        confirmedBy: "Student Acceptance",
      };
    } else {
      this.outcomes.push({
        id: `out-${Date.now()}`,
        studentId: offer.studentId,
        studentName: offer.studentName,
        rollNumber: offer.rollNumber,
        program: prof?.program || "B.Tech",
        department: prof?.department || "Engineering",
        graduationYear: prof?.graduationYear || 2026,
        companyId: offer.companyId,
        companyName: offer.companyName,
        positionId: offer.positionId,
        positionTitle: offer.positionTitle,
        offerId: offer.id,
        ctcLpa: offer.ctcLpa,
        joiningDate: offer.joiningDate,
        placementYear: "2026-2027",
        status: "PLACED",
        confirmedAt: new Date().toISOString(),
        confirmedBy: "Student Acceptance",
        timeline: [],
      });
    }

    return { success: true, data: this.offers[idx] };
  }

  async declineOffer(id: string, reason: string): Promise<ApiResponse<Offer>> {
    await new Promise((r) => setTimeout(r, 60));
    const idx = this.offers.findIndex((o) => o.id === id);
    if (idx === -1) throw new Error("Offer not found");

    const offer = this.offers[idx];
    this.offers[idx] = {
      ...offer,
      status: "DECLINED",
      responseNotes: reason,
    };
    this.offers[idx].timeline.push({
      id: `otl-${Date.now()}`,
      action: "Offer Declined by Candidate",
      actor: offer.studentName,
      timestamp: new Date().toISOString(),
      details: reason,
    });
    return { success: true, data: this.offers[idx] };
  }

  // ==========================================
  // 10. Placement Outcomes
  // ==========================================

  async getPlacementOutcomes(filters?: {
    department?: string;
    status?: string;
  }): Promise<ApiResponse<PlacementOutcome[]>> {
    await new Promise((r) => setTimeout(r, 40));
    let list = [...this.outcomes];
    if (filters?.department && filters.department !== "ALL") {
      list = list.filter((o) => o.department === filters.department);
    }
    if (filters?.status && filters.status !== "ALL") {
      list = list.filter((o) => o.status === filters.status);
    }
    return { success: true, data: list };
  }

  async getPlacementOutcomeByStudent(
    studentId: string
  ): Promise<ApiResponse<PlacementOutcome | null>> {
    await new Promise((r) => setTimeout(r, 30));
    const out = this.outcomes.find((o) => o.studentId === studentId) || null;
    return { success: true, data: out };
  }

  async confirmPlacementOutcome(
    data: Partial<PlacementOutcome>
  ): Promise<ApiResponse<PlacementOutcome>> {
    await new Promise((r) => setTimeout(r, 60));
    const idx = this.outcomes.findIndex((o) => o.studentId === data.studentId);
    if (idx !== -1) {
      this.outcomes[idx] = {
        ...this.outcomes[idx],
        ...data,
        confirmedAt: new Date().toISOString(),
      };
      return { success: true, data: this.outcomes[idx] };
    }

    const newOutcome: PlacementOutcome = {
      id: `out-${Date.now()}`,
      studentId: data.studentId || "std-001",
      studentName: data.studentName || "Student",
      rollNumber: data.rollNumber || "ROLL",
      program: data.program || "B.Tech",
      department: data.department || "Engineering",
      graduationYear: data.graduationYear || 2026,
      companyId: data.companyId || "",
      companyName: data.companyName || "",
      positionId: data.positionId || "",
      positionTitle: data.positionTitle || "",
      offerId: data.offerId || "",
      ctcLpa: data.ctcLpa || 0,
      joiningDate: data.joiningDate || "",
      placementYear: "2026-2027",
      status: data.status || "PLACED",
      confirmedAt: new Date().toISOString(),
      confirmedBy: data.confirmedBy || "Placement Director",
      notes: data.notes,
      timeline: [],
    };
    this.outcomes.push(newOutcome);
    return { success: true, data: newOutcome };
  }

  // ==========================================
  // 11. Reports & Intelligence
  // ==========================================

  async generatePlacementReport(filter: PlacementReportFilter): Promise<
    ApiResponse<{
      title: string;
      generatedAt: string;
      totalRecords: number;
      rows: Record<string, unknown>[];
    }>
  > {
    await new Promise((r) => setTimeout(r, 80));

    let title = "Placement Report";
    let rows: Record<string, unknown>[] = [];

    switch (filter.reportType) {
      case "SUMMARY":
        title = "Placement Operations & Cohort Conversion Summary";
        rows = this.profiles.map((p) => ({
          "Student ID": p.studentId,
          Name: p.studentName,
          Roll: p.rollNumber,
          Department: p.department,
          Program: p.program,
          CGPA: p.cgpa,
          Backlogs: p.activeBacklogs,
          Applications: p.applicationsCount,
          Shortlists: p.shortlistsCount,
          Interviews: p.interviewsCount,
          Offers: p.offersCount,
          "Placement Status": p.placementStatus,
          Company: p.placedCompany || "N/A",
          "CTC (LPA)": p.placedPackageLpa ? `₹${p.placedPackageLpa} LPA` : "N/A",
        }));
        break;

      case "DEPARTMENT":
        title = "Department-wise Placement Performance Audit";
        rows = this.dashboard.departmentStats.map((ds) => ({
          Department: ds.department,
          "Eligible Students": ds.totalStudents,
          "Placed Students": ds.placedStudents,
          "Placement Rate": `${ds.placementRate}%`,
          "Average CTC": `₹${ds.averageCtcLpa} LPA`,
          "Highest CTC": `₹${ds.highestCtcLpa} LPA`,
        }));
        break;

      case "COMPANY":
        title = "Corporate Partners Hiring Ledger";
        rows = this.companies.map((c) => ({
          Company: c.name,
          Industry: c.industry,
          Tier: c.tier,
          "Active Drives": c.activeDrivesCount,
          "Total Alumni Hired": c.totalHiredCount,
          "Average Package": `₹${c.averageCtcLpa} LPA`,
          "Highest Package": `₹${c.highestCtcLpa} LPA`,
          Status: c.status,
        }));
        break;

      case "PACKAGES":
        title = "Compensation & Salary Slab Distribution Report";
        rows = this.dashboard.packageDistribution.map((pd) => ({
          "Salary Slab": pd.range,
          "Min LPA": `₹${pd.minLpa} LPA`,
          "Max LPA": `₹${pd.maxLpa} LPA`,
          "Number of Offers": pd.count,
          "Offer Share": `${pd.percentage}%`,
        }));
        break;

      case "STATUS":
        title = "Candidate Placement Outcomes Ledger";
        rows = this.outcomes.map((o) => ({
          "Student ID": o.studentId,
          Name: o.studentName,
          Roll: o.rollNumber,
          Department: o.department,
          Company: o.companyName || "Unassigned",
          Role: o.positionTitle || "N/A",
          "CTC (LPA)": o.ctcLpa > 0 ? `₹${o.ctcLpa} LPA` : "N/A",
          "Joining Date": o.joiningDate || "N/A",
          Status: o.status,
          Confirmed: o.confirmedAt,
        }));
        break;
    }

    return {
      success: true,
      data: {
        title,
        generatedAt: new Date().toISOString(),
        totalRecords: rows.length,
        rows,
      },
    };
  }
}

export const placementService = new PlacementService();
