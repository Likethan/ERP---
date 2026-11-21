import { ApiResponse } from "@campusos/types";
import { apiFetch } from "../lib/api-client";
import {
  VicePrincipalDashboardData,
  DepartmentMonitoringItem,
  AcademicMonitoringData,
  FacultySupervisionData,
  StudentSupervisionData,
  StatutoryApprovalItem,
  ExaminationsOversightData,
  InstitutionalReportsData,
  InstitutionalAnnouncement,
  InstitutionalAuditLog,
  StatutoryApprovalStatus,
} from "../types/vice-principal";

// Default Mock Data for Client-Side / Standalone / Demo execution
const MOCK_DASHBOARD: VicePrincipalDashboardData = {
  academic_year: "2026-2027",
  semester_filter: null,
  kpis: {
    total_departments: 5,
    total_students: 2620,
    total_faculty: 184,
    overall_student_attendance: 88.4,
    faculty_attendance: 96.2,
    syllabus_completion_rate: 81.4,
    examination_readiness: 92.0,
    pending_approvals_count: 4,
    critical_academic_alerts: 3,
  },
  department_metrics: [
    {
      id: "dept-cse",
      name: "Computer Science & Engineering",
      code: "CSE",
      hod: "Dr. K. S. Anand",
      students: 720,
      faculty: 36,
      faculty_ratio: "1:20",
      attendance_rate: 91.4,
      syllabus_progress: 86,
      accreditation_score: 3.78,
      status: "EXEMPLARY",
      pending_approvals: 2,
    },
    {
      id: "dept-ece",
      name: "Electronics & Communication Engineering",
      code: "ECE",
      hod: "Dr. Meenakshi S.",
      students: 640,
      faculty: 32,
      faculty_ratio: "1:20",
      attendance_rate: 89.2,
      syllabus_progress: 84,
      accreditation_score: 3.65,
      status: "ON_TRACK",
      pending_approvals: 1,
    },
    {
      id: "dept-mech",
      name: "Mechanical Engineering",
      code: "MECH",
      hod: "Dr. R. Venkatraman",
      students: 480,
      faculty: 26,
      faculty_ratio: "1:18",
      attendance_rate: 85.8,
      syllabus_progress: 79,
      accreditation_score: 3.52,
      status: "ON_TRACK",
      pending_approvals: 0,
    },
    {
      id: "dept-civil",
      name: "Civil Engineering",
      code: "CIVIL",
      hod: "Dr. P. Balaji",
      students: 360,
      faculty: 20,
      faculty_ratio: "1:18",
      attendance_rate: 87.1,
      syllabus_progress: 82,
      accreditation_score: 3.58,
      status: "ON_TRACK",
      pending_approvals: 0,
    },
    {
      id: "dept-eee",
      name: "Electrical & Electronics Engineering",
      code: "EEE",
      hod: "Dr. S. Gayathri",
      students: 420,
      faculty: 22,
      faculty_ratio: "1:19",
      attendance_rate: 84.3,
      syllabus_progress: 76,
      accreditation_score: 3.48,
      status: "ATTENTION_NEEDED",
      pending_approvals: 1,
    },
  ],
  critical_alerts: [
    {
      id: "alt-01",
      severity: "CRITICAL",
      department: "Electrical & Electronics Engineering",
      title: "Syllabus Lag in EE502 (Control Systems)",
      detail:
        "Teaching velocity is 14% behind scheduled lesson plan. Semester exam window in 24 days.",
    },
    {
      id: "alt-02",
      severity: "HIGH",
      department: "Mechanical Engineering",
      title: "Attendance Shortage Spike in 5th Sem Sec B",
      detail:
        "18 students crossed into sub-75% bracket following industrial visit leave reconciliation.",
    },
    {
      id: "alt-03",
      severity: "MEDIUM",
      department: "Computer Science & Engineering",
      title: "Question Bank Scrutiny Due",
      detail:
        "4 specialized elective question papers awaiting Board of Scrutiny sign-off.",
    },
  ],
  recent_institutional_activities: [
    {
      id: "act-1",
      timestamp: "2026-11-18T11:30:00Z",
      category: "Curriculum",
      title: "Board of Studies Revision Approved",
      department: "CSE",
    },
    {
      id: "act-2",
      timestamp: "2026-11-17T16:00:00Z",
      category: "Examinations",
      title: "CIA 1 Moderation Reports Locked",
      department: "All Departments",
    },
    {
      id: "act-3",
      timestamp: "2026-11-16T14:10:00Z",
      category: "Accreditation",
      title: "NAAC SSR Criterion 2 Verification Completed",
      department: "IQAC",
    },
  ],
};

const MOCK_APPROVALS: StatutoryApprovalItem[] = [
  {
    id: "appr-vp-001",
    title: "Special Elective Offering: Advanced Deep Learning & Generative AI",
    category: "DEPARTMENT_ACADEMIC_REQUEST",
    department_id: "dept-cse",
    department_name: "Computer Science & Engineering",
    submitted_by: "Dr. K. S. Anand (HOD)",
    submission_date: "2026-11-18T09:30:00Z",
    urgency: "HIGH",
    status: "PENDING",
    details: {
      subject_code: "CS704",
      credits: 4,
      target_semester: 7,
      enrolled_interest: 84,
      justification:
        "Industry demand alignment with NAAC criteria 1.2 curricular enrichment.",
    },
    audit_trail: [
      {
        action: "SUBMITTED",
        by: "Dr. K. S. Anand (HOD)",
        timestamp: "2026-11-18T09:30:00Z",
        notes: "Submitted with department academic committee recommendation.",
      },
    ],
  },
  {
    id: "appr-vp-002",
    title: "Academic Calendar Revision: Model Examination Window Preponement",
    category: "ACADEMIC_CALENDAR_CHANGE",
    department_id: "dept-all",
    department_name: "All Academic Departments",
    submitted_by: "Dr. V. Ramanathan (Controller of Examinations)",
    submission_date: "2026-11-17T14:15:00Z",
    urgency: "CRITICAL",
    status: "PENDING",
    details: {
      original_window: "2026-12-05 to 2026-12-15",
      proposed_window: "2026-11-28 to 2026-12-08",
      affected_batches: "All 3rd and 4th Year B.E. Programs",
      reason:
        "Avoid clash with Anna University central valuation dates and campus placement season.",
    },
    audit_trail: [
      {
        action: "SUBMITTED",
        by: "Dr. V. Ramanathan (COE)",
        timestamp: "2026-11-17T14:15:00Z",
        notes: "Coordinated with HODs across 5 engineering departments.",
      },
    ],
  },
  {
    id: "appr-vp-003",
    title:
      "Duty Leave & Conference Travel: IEEE International Colloquium on Robotics",
    category: "FACULTY_LEAVE",
    department_id: "dept-ece",
    department_name: "Electronics & Communication",
    submitted_by: "Dr. Priya Nair (Associate Professor)",
    submission_date: "2026-11-16T11:00:00Z",
    urgency: "MEDIUM",
    status: "PENDING",
    details: {
      leave_type: "DUTY_LEAVE",
      duration: "5 Days (2026-12-02 to 2026-12-06)",
      alternate_faculty: "Prof. S. Ranganathan (CS303 substitution)",
      paper_title:
        "Edge-Compute Vision Architectures for Low-Power Autonomous Micro-Robotics",
      hod_recommendation:
        "Endorsed by HOD ECE. Syllabus compensation plan verified.",
    },
    audit_trail: [
      {
        action: "SUBMITTED",
        by: "Dr. Priya Nair",
        timestamp: "2026-11-16T11:00:00Z",
        notes: "Leave application submitted.",
      },
      {
        action: "FORWARDED",
        by: "Dr. Meenakshi S. (HOD ECE)",
        timestamp: "2026-11-16T15:20:00Z",
        notes: "Endorsed and forwarded to Vice Principal for sanction.",
      },
    ],
  },
  {
    id: "appr-vp-004",
    title: "Inter-Department Timetable Slot Swap: Smart Manufacturing Lab",
    category: "TIMETABLE_CHANGE",
    department_id: "dept-mech",
    department_name: "Mechanical Engineering",
    submitted_by: "Dr. R. Venkatraman (HOD Mech)",
    submission_date: "2026-11-15T16:45:00Z",
    urgency: "MEDIUM",
    status: "APPROVED",
    details: {
      affected_semester: "6th Sem Mech & 6th Sem Mechatronics",
      slot_change: "Wednesday Periods 5-7 swapped with Friday Periods 2-4",
      hall_lab: "Robotics & CNC Automation Bay B",
    },
    remarks: "Approved. Ensure technician coverage is scheduled accordingly.",
    decided_by: "Dr. Meenakshi Sundaram (Vice Principal)",
    decision_date: "2026-11-16T10:00:00Z",
    audit_trail: [
      {
        action: "SUBMITTED",
        by: "Dr. R. Venkatraman (HOD)",
        timestamp: "2026-11-15T16:45:00Z",
        notes: "Slot re-allocation requested due to machine calibration.",
      },
      {
        action: "APPROVED",
        by: "Dr. Meenakshi Sundaram (Vice Principal)",
        timestamp: "2026-11-16T10:00:00Z",
        notes: "Approved with technician coverage condition.",
      },
    ],
  },
  {
    id: "appr-vp-005",
    title: "End-Semester Examination Question Bank Moderation Sign-Off",
    category: "EXAMINATION_REQUEST",
    department_id: "dept-all",
    department_name: "All Academic Departments",
    submitted_by: "Board of Examinations",
    submission_date: "2026-11-15T10:00:00Z",
    urgency: "CRITICAL",
    status: "PENDING",
    details: {
      total_courses: 42,
      scrutiny_status: "38 of 42 Course Question Banks Scrutinized and Sealed",
      external_examiners_confirmed: "100%",
      confidentiality_seal: "COE/ES-NOV2026/SEC-09",
    },
    audit_trail: [
      {
        action: "SUBMITTED",
        by: "Board of Examinations",
        timestamp: "2026-11-15T10:00:00Z",
        notes: "Awaiting final Vice Principal academic vetting.",
      },
    ],
  },
  {
    id: "appr-vp-006",
    title: "Remedial Intervention Plan for At-Risk Students in CS302 (DBMS)",
    category: "ACADEMIC_PERFORMANCE_INTERVENTION",
    department_id: "dept-cse",
    department_name: "Computer Science & Engineering",
    submitted_by: "Dr. K. S. Anand (HOD)",
    submission_date: "2026-11-14T11:20:00Z",
    urgency: "HIGH",
    status: "APPROVED",
    details: {
      identified_students_count: 18,
      intervention_type: "Special Evening Coaching (04:15 PM - 05:30 PM)",
      faculty_in_charge: "Prof. S. Ranganathan",
      duration_weeks: 4,
    },
    remarks:
      "Approved. Track attendance diligently and submit weekly progress reports.",
    decided_by: "Dr. Meenakshi Sundaram (Vice Principal)",
    decision_date: "2026-11-14T16:00:00Z",
    audit_trail: [
      {
        action: "SUBMITTED",
        by: "Dr. K. S. Anand (HOD)",
        timestamp: "2026-11-14T11:20:00Z",
        notes: "Remedial coaching proposal based on CIA 1 diagnostic marks.",
      },
      {
        action: "APPROVED",
        by: "Dr. Meenakshi Sundaram (Vice Principal)",
        timestamp: "2026-11-14T16:00:00Z",
        notes: "Sanctioned with weekly tracking mandate.",
      },
    ],
  },
  {
    id: "appr-vp-007",
    title: "National Conference on Green Computing & Sustainable AI Sanction",
    category: "ACADEMIC_EVENT",
    department_id: "dept-cse",
    department_name: "Computer Science & Engineering",
    submitted_by: "Dr. K. S. Anand (HOD)",
    submission_date: "2026-11-13T10:00:00Z",
    urgency: "HIGH",
    status: "PENDING",
    details: {
      proposed_dates: "2027-02-18 to 2027-02-19",
      expected_delegates: 150,
      invited_keynote: "Dr. P. Radhakrishnan (IISc Bangalore)",
      venue: "Main Institutional Auditorium",
    },
    remarks: null,
    decided_by: null,
    decision_date: null,
    audit_trail: [
      {
        action: "SUBMITTED",
        by: "Dr. K. S. Anand (HOD)",
        timestamp: "2026-11-13T10:00:00Z",
        notes: "Conference proposal endorsed by Department Research Committee.",
      },
    ],
  },
  {
    id: "appr-vp-008",
    title: "Civil Materials Testing Lab Modernization & Calibration Sanction",
    category: "DEPARTMENT_ADMIN_REQUEST",
    department_id: "dept-civil",
    department_name: "Civil Engineering",
    submitted_by: "Dr. P. Balaji (HOD)",
    submission_date: "2026-11-12T15:30:00Z",
    urgency: "MEDIUM",
    status: "PENDING",
    details: {
      laboratory: "Concrete & Highway Engineering Lab",
      equipment:
        "Universal Testing Machine Digital Calibration (NABL accredited)",
      budget_allocation: "INR 1,80,000",
      compliance_standard: "ISO/IEC 17025:2017",
    },
    remarks: null,
    decided_by: null,
    decision_date: null,
    audit_trail: [
      {
        action: "SUBMITTED",
        by: "Dr. P. Balaji (HOD)",
        timestamp: "2026-11-12T15:30:00Z",
        notes: "Submitted for Vice Principal statutory infrastructure vetting.",
      },
    ],
  },
  {
    id: "appr-vp-009",
    title: "Medical Attendance Condonation & Exam Eligibility Exception Review",
    category: "SPECIAL_ACADEMIC_PERMISSION",
    department_id: "dept-eee",
    department_name: "Electrical & Electronics Engineering",
    submitted_by: "Dr. S. Gayathri (HOD)",
    submission_date: "2026-11-11T12:00:00Z",
    urgency: "CRITICAL",
    status: "PENDING",
    details: {
      student_roll: "24EEE0018",
      student_name: "Meera Nair",
      semester: 5,
      actual_attendance_pct: 68.5,
      reason:
        "Dengue hospitalization (14 working days verified with hospital discharge summary)",
      statutory_rule:
        "Anna University Clause 7.1 Condonation for 65%-74% bracket on medical grounds",
    },
    remarks: null,
    decided_by: null,
    decision_date: null,
    audit_trail: [
      {
        action: "SUBMITTED",
        by: "Dr. S. Gayathri (HOD)",
        timestamp: "2026-11-11T12:00:00Z",
        notes: "Verified by Department Medical Advisory Committee.",
      },
    ],
  },
];

class VicePrincipalService {
  private approvalsState: StatutoryApprovalItem[] = [...MOCK_APPROVALS];
  private announcementsState: InstitutionalAnnouncement[] = [
    {
      id: "anc-vp-01",
      title:
        "Directive: Mandatory Mid-Semester Syllabus Completion & Verification Audit",
      target_audience: "ALL_HODS_AND_FACULTY",
      priority: "HIGH",
      published_at: "2026-11-18T10:00:00Z",
      author: "Dr. Meenakshi Sundaram (Vice Principal)",
      summary:
        "All academic departments must complete at least 70% of course syllabi prior to CIA 2. Department heads are requested to conduct lesson plan reviews by Friday.",
      pinned: true,
    },
    {
      id: "anc-vp-02",
      title:
        "Statutory Notice: Attendance Shortage Warning Letters Generation (<75%)",
      target_audience: "ALL_HODS",
      priority: "CRITICAL",
      published_at: "2026-11-17T09:00:00Z",
      author: "Dr. Meenakshi Sundaram (Vice Principal)",
      summary:
        "Formal warning notices must be dispatched to parents of students having cumulative attendance below 75% as per Anna University Regulation Clause 6.4.",
      pinned: true,
    },
    {
      id: "anc-vp-03",
      title: "Call for Research Seed Grant Proposals — Academic Year 2026-27",
      target_audience: "FACULTY",
      priority: "ROUTINE",
      published_at: "2026-11-12T14:30:00Z",
      author: "Office of Vice Principal & Dean (Research)",
      summary:
        "Applications are invited for institutional inter-disciplinary research seed grants up to INR 2.5 Lakhs per project.",
      pinned: false,
    },
  ];

  async getDashboard(params?: {
    department_id?: string;
    academic_year?: string;
    semester?: number;
  }): Promise<ApiResponse<VicePrincipalDashboardData>> {
    try {
      const q = new URLSearchParams();
      if (params?.department_id) q.set("department_id", params.department_id);
      if (params?.academic_year) q.set("academic_year", params.academic_year);
      if (params?.semester) q.set("semester", params.semester.toString());

      const res = await apiFetch<VicePrincipalDashboardData>(
        `/api/v1/vice-principal/dashboard?${q.toString()}`,
      );
      if (res && res.data) return res;
    } catch {
      // Backend unavailable or running client mock
    }

    let deptMetrics = MOCK_DASHBOARD.department_metrics;
    if (params?.department_id) {
      deptMetrics = deptMetrics.filter(
        (d) =>
          d.id === params.department_id ||
          d.code.toLowerCase() === params.department_id?.toLowerCase(),
      );
    }

    return {
      success: true,
      data: {
        ...MOCK_DASHBOARD,
        academic_year: params?.academic_year || MOCK_DASHBOARD.academic_year,
        semester_filter: params?.semester,
        department_metrics: deptMetrics,
      },
    };
  }

  async getDepartments(): Promise<ApiResponse<DepartmentMonitoringItem[]>> {
    try {
      const res = await apiFetch<DepartmentMonitoringItem[]>(
        "/api/v1/vice-principal/departments",
      );
      if (res && res.data) return res;
    } catch {
      // Fallback
    }

    return {
      success: true,
      data: [
        {
          id: "dept-cse",
          name: "Computer Science & Engineering",
          code: "CSE",
          hod_name: "Dr. K. S. Anand",
          hod_email: "hod.cse@campusos.edu",
          student_count: 720,
          faculty_count: 36,
          faculty_ratio: "1:20",
          student_attendance: 91.4,
          faculty_attendance: 97.2,
          syllabus_progress: 86,
          pending_approvals: 2,
          status: "EXEMPLARY",
          accreditation_score: 3.78,
          delay_alerts_count: 0,
          labs_count: 8,
          classrooms_count: 14,
        },
        {
          id: "dept-ece",
          name: "Electronics & Communication Engineering",
          code: "ECE",
          hod_name: "Dr. Meenakshi S.",
          hod_email: "hod.ece@campusos.edu",
          student_count: 640,
          faculty_count: 32,
          faculty_ratio: "1:20",
          student_attendance: 89.2,
          faculty_attendance: 95.8,
          syllabus_progress: 84,
          pending_approvals: 1,
          status: "ON_TRACK",
          accreditation_score: 3.65,
          delay_alerts_count: 1,
          labs_count: 6,
          classrooms_count: 12,
        },
        {
          id: "dept-mech",
          name: "Mechanical Engineering",
          code: "MECH",
          hod_name: "Dr. R. Venkatraman",
          hod_email: "hod.mech@campusos.edu",
          student_count: 480,
          faculty_count: 26,
          faculty_ratio: "1:18",
          student_attendance: 85.8,
          faculty_attendance: 94.6,
          syllabus_progress: 79,
          pending_approvals: 0,
          status: "ON_TRACK",
          accreditation_score: 3.52,
          delay_alerts_count: 1,
          labs_count: 7,
          classrooms_count: 10,
        },
        {
          id: "dept-civil",
          name: "Civil Engineering",
          code: "CIVIL",
          hod_name: "Dr. P. Balaji",
          hod_email: "hod.civil@campusos.edu",
          student_count: 360,
          faculty_count: 20,
          faculty_ratio: "1:18",
          student_attendance: 87.1,
          faculty_attendance: 96.5,
          syllabus_progress: 82,
          pending_approvals: 0,
          status: "ON_TRACK",
          accreditation_score: 3.58,
          delay_alerts_count: 0,
          labs_count: 5,
          classrooms_count: 8,
        },
        {
          id: "dept-eee",
          name: "Electrical & Electronics Engineering",
          code: "EEE",
          hod_name: "Dr. S. Gayathri",
          hod_email: "hod.eee@campusos.edu",
          student_count: 420,
          faculty_count: 22,
          faculty_ratio: "1:19",
          student_attendance: 84.3,
          faculty_attendance: 93.8,
          syllabus_progress: 76,
          pending_approvals: 1,
          status: "ATTENTION_NEEDED",
          accreditation_score: 3.48,
          delay_alerts_count: 2,
          labs_count: 5,
          classrooms_count: 8,
        },
      ],
    };
  }

  async getAcademicsMonitoring(params?: {
    academic_year?: string;
    semester_type?: string;
  }): Promise<ApiResponse<AcademicMonitoringData>> {
    try {
      const q = new URLSearchParams();
      if (params?.academic_year) q.set("academic_year", params.academic_year);
      if (params?.semester_type) q.set("semester_type", params.semester_type);

      const res = await apiFetch<AcademicMonitoringData>(
        `/api/v1/vice-principal/academics?${q.toString()}`,
      );
      if (res && res.data) return res;
    } catch {
      // Fallback
    }

    return {
      success: true,
      data: {
        academic_year: params?.academic_year || "2026-2027",
        semester_type: params?.semester_type || "ODD",
        milestones: [
          {
            id: "ms-01",
            event: "Commencement of Classes (3rd, 5th, 7th Sem)",
            scheduled_date: "2026-08-03",
            actual_date: "2026-08-03",
            status: "COMPLETED",
            variance_days: 0,
          },
          {
            id: "ms-02",
            event: "Continuous Internal Assessment (CIA) 1",
            scheduled_date: "2026-09-22",
            actual_date: "2026-09-22",
            status: "COMPLETED",
            variance_days: 0,
          },
          {
            id: "ms-03",
            event: "CIA 1 Result Moderation & Parent Communication",
            scheduled_date: "2026-10-05",
            actual_date: "2026-10-06",
            status: "COMPLETED",
            variance_days: 1,
          },
          {
            id: "ms-04",
            event: "Continuous Internal Assessment (CIA) 2",
            scheduled_date: "2026-11-24",
            actual_date: null,
            status: "UPCOMING",
            variance_days: 0,
          },
          {
            id: "ms-05",
            event: "Practical & Laboratory Model Examinations",
            scheduled_date: "2026-12-04",
            actual_date: null,
            status: "UPCOMING",
            variance_days: 0,
          },
          {
            id: "ms-06",
            event: "Last Working Day & Attendance Condonation Committee",
            scheduled_date: "2026-12-12",
            actual_date: null,
            status: "UPCOMING",
            variance_days: 0,
          },
          {
            id: "ms-07",
            event: "University End-Semester Theory Examinations",
            scheduled_date: "2026-12-18",
            actual_date: null,
            status: "UPCOMING",
            variance_days: 0,
          },
        ],
        syllabus_delay_tracking: [
          {
            subject_code: "EE502",
            subject_name: "Control Systems Engineering",
            department: "EEE",
            semester: 5,
            faculty_name: "Prof. G. Murugan",
            planned_topics: 38,
            completed_topics: 27,
            completion_percentage: 71.0,
            expected_percentage: 85.0,
            lag_days: 9,
            remedial_status: "EXTRA_CLASSES_MANDATED",
          },
          {
            subject_code: "ME504",
            subject_name: "Design of Machine Elements",
            department: "MECH",
            semester: 5,
            faculty_name: "Dr. R. Venkatraman",
            planned_topics: 36,
            completed_topics: 28,
            completion_percentage: 77.7,
            expected_percentage: 85.0,
            lag_days: 5,
            remedial_status: "SATURDAY_SESSIONS_SCHEDULED",
          },
          {
            subject_code: "EC702",
            subject_name: "Optical Communication & Networks",
            department: "ECE",
            semester: 7,
            faculty_name: "Prof. T. Sundar",
            planned_topics: 34,
            completed_topics: 27,
            completion_percentage: 79.4,
            expected_percentage: 85.0,
            lag_days: 4,
            remedial_status: "MONITORING",
          },
        ],
        timetable_coverage: {
          total_scheduled_hours_weekly: 1420,
          classes_conducted_on_schedule_pct: 97.4,
          faculty_substitution_rate_pct: 2.1,
          unassigned_lecture_slots: 0,
        },
      },
    };
  }

  async getFacultySupervision(params?: {
    department?: string;
  }): Promise<ApiResponse<FacultySupervisionData>> {
    try {
      const q = new URLSearchParams();
      if (params?.department) q.set("department", params.department);

      const res = await apiFetch<FacultySupervisionData>(
        `/api/v1/vice-principal/faculty?${q.toString()}`,
      );
      if (res && res.data) return res;
    } catch {
      // Fallback
    }

    let faculty = [
      {
        id: "fac-01",
        name: "Dr. K. S. Anand",
        employee_code: "FAC-CSE-001",
        designation: "Professor & HOD",
        department: "Computer Science & Engineering",
        email: "hod.cse@campusos.edu",
        weekly_teaching_hours: 12,
        assigned_subjects: ["CS701 Distributed Computing"],
        status: "NORMAL" as const,
        attendance_rate: 98.0,
        active_leaves: 0,
      },
      {
        id: "fac-02",
        name: "Dr. Rajesh Sharma",
        employee_code: "FAC-CSE-002",
        designation: "Professor & Dean",
        department: "Computer Science & Engineering",
        email: "rajesh.sharma@campusos.edu",
        weekly_teaching_hours: 14,
        assigned_subjects: ["CS301 Data Structures"],
        status: "NORMAL" as const,
        attendance_rate: 97.5,
        active_leaves: 0,
      },
      {
        id: "fac-03",
        name: "Dr. Priya Nair",
        employee_code: "FAC-ECE-005",
        designation: "Associate Professor",
        department: "Electronics & Communication",
        email: "priya.nair@campusos.edu",
        weekly_teaching_hours: 18,
        assigned_subjects: [
          "EC302 Digital Signal Processing",
          "EC504 Microcontrollers Lab",
        ],
        status: "OVERLOADED" as const,
        attendance_rate: 96.0,
        active_leaves: 1,
      },
      {
        id: "fac-04",
        name: "Prof. S. Ranganathan",
        employee_code: "FAC-CSE-008",
        designation: "Assistant Professor",
        department: "Computer Science & Engineering",
        email: "s.ranganathan@campusos.edu",
        weekly_teaching_hours: 18,
        assigned_subjects: ["CS303 Computer Networks", "CS505 Networks Lab"],
        status: "OVERLOADED" as const,
        attendance_rate: 98.5,
        active_leaves: 0,
      },
      {
        id: "fac-05",
        name: "Dr. R. Venkatraman",
        employee_code: "FAC-MECH-001",
        designation: "Professor & HOD",
        department: "Mechanical Engineering",
        email: "hod.mech@campusos.edu",
        weekly_teaching_hours: 12,
        assigned_subjects: ["ME504 Design of Machine Elements"],
        status: "NORMAL" as const,
        attendance_rate: 95.0,
        active_leaves: 0,
      },
      {
        id: "fac-06",
        name: "Prof. G. Murugan",
        employee_code: "FAC-EEE-003",
        designation: "Assistant Professor",
        department: "Electrical & Electronics Engineering",
        email: "g.murugan@campusos.edu",
        weekly_teaching_hours: 16,
        assigned_subjects: ["EE502 Control Systems Engineering"],
        status: "NORMAL" as const,
        attendance_rate: 94.0,
        active_leaves: 0,
      },
      {
        id: "fac-07",
        name: "Prof. Kavitha Raman",
        employee_code: "FAC-CIVIL-004",
        designation: "Assistant Professor",
        department: "Civil Engineering",
        email: "kavitha.raman@campusos.edu",
        weekly_teaching_hours: 10,
        assigned_subjects: ["CE301 Structural Analysis"],
        status: "UNDERLOADED" as const,
        attendance_rate: 96.2,
        active_leaves: 0,
      },
    ];

    if (params?.department) {
      faculty = faculty.filter((f) =>
        f.department.toLowerCase().includes(params.department!.toLowerCase()),
      );
    }

    return {
      success: true,
      data: {
        workload_summary: {
          total_faculty: faculty.length,
          compliant_workload_count: faculty.filter((f) => f.status === "NORMAL")
            .length,
          overloaded_count: faculty.filter((f) => f.status === "OVERLOADED")
            .length,
          underloaded_count: faculty.filter((f) => f.status === "UNDERLOADED")
            .length,
          average_teaching_hours: 14.3,
          statutory_min_hours: 12,
          statutory_max_hours: 18,
        },
        faculty,
      },
    };
  }

  async getStudentsSupervision(params?: {
    department?: string;
    threshold?: number;
  }): Promise<ApiResponse<StudentSupervisionData>> {
    try {
      const q = new URLSearchParams();
      if (params?.department) q.set("department", params.department);
      if (params?.threshold) q.set("threshold", params.threshold.toString());

      const res = await apiFetch<StudentSupervisionData>(
        `/api/v1/vice-principal/students?${q.toString()}`,
      );
      if (res && res.data) return res;
    } catch {
      // Fallback
    }

    let radar = [
      {
        roll_number: "24CSE0114",
        name: "Karthik Raja",
        department: "Computer Science & Engineering",
        semester: 5,
        section: "A",
        attendance_percentage: 67.5,
        attended_sessions: 108,
        total_sessions: 160,
        shortfall_sessions: 12,
        mentor_name: "Dr. Rajesh Sharma",
        risk_level: "HIGH" as const,
        status: "WARNING_ISSUED",
      },
      {
        roll_number: "24ECE0089",
        name: "Divya Bharathi",
        department: "Electronics & Communication",
        semester: 5,
        section: "B",
        attendance_percentage: 70.0,
        attended_sessions: 112,
        total_sessions: 160,
        shortfall_sessions: 8,
        mentor_name: "Dr. Priya Nair",
        risk_level: "MEDIUM" as const,
        status: "NOTICE_PENDING",
      },
      {
        roll_number: "24MECH0045",
        name: "Praveen Kumar",
        department: "Mechanical Engineering",
        semester: 7,
        section: "A",
        attendance_percentage: 65.3,
        attended_sessions: 98,
        total_sessions: 150,
        shortfall_sessions: 15,
        mentor_name: "Dr. R. Venkatraman",
        risk_level: "CRITICAL" as const,
        status: "PARENT_CONFERENCE_CALLED",
      },
      {
        roll_number: "24EEE0023",
        name: "Sanjay Raghavan",
        department: "Electrical & Electronics",
        semester: 5,
        section: "A",
        attendance_percentage: 71.8,
        attended_sessions: 115,
        total_sessions: 160,
        shortfall_sessions: 5,
        mentor_name: "Prof. G. Murugan",
        risk_level: "MEDIUM" as const,
        status: "COUNSELED",
      },
      {
        roll_number: "24CIVIL0012",
        name: "Ananya Krishnan",
        department: "Civil Engineering",
        semester: 3,
        section: "A",
        attendance_percentage: 69.2,
        attended_sessions: 90,
        total_sessions: 130,
        shortfall_sessions: 8,
        mentor_name: "Prof. Kavitha Raman",
        risk_level: "HIGH" as const,
        status: "WARNING_ISSUED",
      },
    ];

    if (params?.department) {
      radar = radar.filter((s) =>
        s.department.toLowerCase().includes(params.department!.toLowerCase()),
      );
    }

    return {
      success: true,
      data: {
        threshold: params?.threshold || 75.0,
        total_students_monitored: 2620,
        total_shortage_students: radar.length,
        institutional_strength: [
          {
            department: "Computer Science & Engineering",
            year_1: 180,
            year_2: 180,
            year_3: 180,
            year_4: 180,
            total: 720,
          },
          {
            department: "Electronics & Communication",
            year_1: 160,
            year_2: 160,
            year_3: 160,
            year_4: 160,
            total: 640,
          },
          {
            department: "Mechanical Engineering",
            year_1: 120,
            year_2: 120,
            year_3: 120,
            year_4: 120,
            total: 480,
          },
          {
            department: "Civil Engineering",
            year_1: 90,
            year_2: 90,
            year_3: 90,
            year_4: 90,
            total: 360,
          },
          {
            department: "Electrical & Electronics",
            year_1: 105,
            year_2: 105,
            year_3: 105,
            year_4: 105,
            total: 420,
          },
        ],
        low_attendance_radar: radar,
        academic_backlogs_overview: {
          zero_backlogs_pct: 84.6,
          one_to_two_backlogs_pct: 11.2,
          three_plus_backlogs_pct: 4.2,
          critical_academic_probation_count: 28,
        },
      },
    };
  }

  async getApprovals(params?: {
    status?: string;
    category?: string;
    department?: string;
  }): Promise<ApiResponse<StatutoryApprovalItem[]>> {
    try {
      const q = new URLSearchParams();
      if (params?.status) q.set("status", params.status);
      if (params?.category) q.set("category", params.category);
      if (params?.department) q.set("department", params.department);

      const res = await apiFetch<StatutoryApprovalItem[]>(
        `/api/v1/vice-principal/approvals?${q.toString()}`,
      );
      if (res && res.data) return res;
    } catch {
      // Fallback to local state
    }

    let items = [...this.approvalsState];
    if (params?.status && params.status !== "ALL") {
      items = items.filter((i) => i.status === params.status);
    }
    if (params?.category) {
      items = items.filter((i) => i.category === params.category);
    }
    if (params?.department) {
      items = items.filter((i) =>
        i.department_name
          .toLowerCase()
          .includes(params.department!.toLowerCase()),
      );
    }

    return {
      success: true,
      data: items,
    };
  }

  async processApprovalAction(
    id: string,
    action: "APPROVE" | "REJECT" | "REQUEST_MODIFICATION" | "FORWARD",
    remarks: string,
    conditions?: string,
  ): Promise<ApiResponse<StatutoryApprovalItem>> {
    try {
      const res = await apiFetch<StatutoryApprovalItem>(
        `/api/v1/vice-principal/approvals/${id}/action`,
        {
          method: "POST",
          body: JSON.stringify({ action, remarks, conditions }),
        },
      );
      if (res && res.data) {
        // Synchronize in-memory cache
        const idx = this.approvalsState.findIndex((a) => a.id === id);
        if (idx >= 0) this.approvalsState[idx] = res.data;
        return res;
      }
    } catch {
      // Local execution fallback
    }

    const item = this.approvalsState.find((a) => a.id === id);
    if (!item) {
      throw new Error(`Approval item with ID ${id} not found.`);
    }

    const statusMap: Record<string, StatutoryApprovalStatus> = {
      APPROVE: "APPROVED",
      REJECT: "REJECTED",
      REQUEST_MODIFICATION: "MODIFICATION_REQUESTED",
      FORWARD: "FORWARDED",
    };
    const newStatus = statusMap[action] || "APPROVED";
    const nowIso = new Date().toISOString();

    item.status = newStatus;
    item.remarks = remarks;
    item.decided_by = "Office of the Vice Principal";
    item.decision_date = nowIso;
    item.audit_trail.push({
      action: newStatus,
      by: "Office of the Vice Principal",
      timestamp: nowIso,
      notes: remarks,
    });

    return {
      success: true,
      data: { ...item },
    };
  }

  async getExaminationsOversight(): Promise<
    ApiResponse<ExaminationsOversightData>
  > {
    try {
      const res = await apiFetch<ExaminationsOversightData>(
        "/api/v1/vice-principal/examinations",
      );
      if (res && res.data) return res;
    } catch {
      // Fallback
    }

    return {
      success: true,
      data: {
        schedules: [
          {
            id: "exam-01",
            name: "Continuous Internal Assessment (CIA) 2",
            date_range: "2026-11-24 to 2026-11-28",
            type: "INTERNAL",
            status: "CONFIRMED",
            question_papers_moderated: 40,
            question_papers_total: 42,
            seating_plan_published: true,
          },
          {
            id: "exam-02",
            name: "End Semester Laboratory Practical Examinations",
            date_range: "2026-12-04 to 2026-12-10",
            type: "PRACTICAL",
            status: "EXAMINERS_APPOINTED",
            external_examiners_count: 28,
            batches_scheduled: 64,
            seating_plan_published: false,
          },
          {
            id: "exam-03",
            name: "University End-Semester Theory Examinations",
            date_range: "2026-12-18 to 2027-01-08",
            type: "THEORY",
            status: "HALL_ALLOCATIONS_FINALIZED",
            total_halls: 32,
            chief_superintendent: "Dr. Meenakshi Sundaram (VP)",
            seating_plan_published: false,
          },
        ],
        cia_mark_submissions: [
          {
            department: "Computer Science & Engineering",
            total_courses: 42,
            submitted: 42,
            locked: 42,
            pending: 0,
            status: "COMPLETED",
          },
          {
            department: "Electronics & Communication",
            total_courses: 38,
            submitted: 38,
            locked: 38,
            pending: 0,
            status: "COMPLETED",
          },
          {
            department: "Mechanical Engineering",
            total_courses: 32,
            submitted: 32,
            locked: 30,
            pending: 2,
            status: "LOCK_PENDING",
          },
          {
            department: "Civil Engineering",
            total_courses: 26,
            submitted: 26,
            locked: 26,
            pending: 0,
            status: "COMPLETED",
          },
          {
            department: "Electrical & Electronics",
            total_courses: 28,
            submitted: 26,
            locked: 24,
            pending: 2,
            status: "SUBMISSION_OVERDUE",
          },
        ],
        results_analysis: {
          overall_institutional_pass_pct: 92.4,
          first_class_with_distinction_pct: 34.6,
          first_class_pct: 48.2,
          arrear_rate_pct: 7.6,
          department_pass_ranking: [
            { rank: 1, department: "CSE", pass_pct: 96.1 },
            { rank: 2, department: "ECE", pass_pct: 94.2 },
            { rank: 3, department: "CIVIL", pass_pct: 91.8 },
            { rank: 4, department: "MECH", pass_pct: 89.5 },
            { rank: 5, department: "EEE", pass_pct: 88.4 },
          ],
        },
      },
    };
  }

  async getReports(params?: {
    academic_year?: string;
  }): Promise<ApiResponse<InstitutionalReportsData>> {
    try {
      const q = new URLSearchParams();
      if (params?.academic_year) q.set("academic_year", params.academic_year);

      const res = await apiFetch<InstitutionalReportsData>(
        `/api/v1/vice-principal/reports?${q.toString()}`,
      );
      if (res && res.data) return res;
    } catch {
      // Fallback
    }

    return {
      success: true,
      data: {
        academic_year: params?.academic_year || "2026-2027",
        available_reports: [
          {
            id: "rep-01",
            name: "Comprehensive Department Academic Performance Index",
            type: "ACADEMIC_PERFORMANCE",
            generated_on: "2026-11-18",
            format: ["PDF", "XLSX"],
            description:
              "Multi-department assessment comparing syllabus completion, pass rates, and research publications.",
          },
          {
            id: "rep-02",
            name: "Institutional Attendance Compliance & Condonation Forecast",
            type: "ATTENDANCE_COMPLIANCE",
            generated_on: "2026-11-18",
            format: ["PDF", "CSV"],
            description:
              "Sub-75% attendance radar across all batches with projected eligibility before university exams.",
          },
          {
            id: "rep-03",
            name: "Faculty Teaching Load & Workload Equity Audit",
            type: "FACULTY_WORKLOAD",
            generated_on: "2026-11-15",
            format: ["PDF", "XLSX"],
            description:
              "Analysis of teaching contact hours, laboratory sessions, and tutorial distribution per AICTE norms.",
          },
          {
            id: "rep-04",
            name: "Curriculum Coverage Velocity & Delay Mitigation Log",
            type: "CURRICULUM_COVERAGE",
            generated_on: "2026-11-16",
            format: ["PDF"],
            description:
              "Subject-wise topic progress analysis tracking syllabus delays and remediation plans.",
          },
        ],
        summary_metrics: {
          overall_institutional_compliance: 94.2,
          accreditation_readiness_index: 3.68,
          teaching_workload_adherence: 96.5,
        },
      },
    };
  }

  async getAnnouncements(): Promise<ApiResponse<InstitutionalAnnouncement[]>> {
    try {
      const res = await apiFetch<InstitutionalAnnouncement[]>(
        "/api/v1/vice-principal/announcements",
      );
      if (res && res.data) return res;
    } catch {
      // Fallback
    }

    return {
      success: true,
      data: [...this.announcementsState],
    };
  }

  async createAnnouncement(payload: {
    title: string;
    target_audience: string;
    priority: "ROUTINE" | "HIGH" | "CRITICAL";
    summary: string;
    pinned: boolean;
  }): Promise<ApiResponse<InstitutionalAnnouncement>> {
    try {
      const res = await apiFetch<InstitutionalAnnouncement>(
        "/api/v1/vice-principal/announcements",
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
      );
      if (res && res.data) {
        this.announcementsState.unshift(res.data);
        return res;
      }
    } catch {
      // Fallback
    }

    const newItem: InstitutionalAnnouncement = {
      id: `anc-vp-${Date.now()}`,
      title: payload.title,
      target_audience: payload.target_audience,
      priority: payload.priority,
      published_at: new Date().toISOString(),
      author: "Office of the Vice Principal",
      summary: payload.summary,
      pinned: payload.pinned,
    };

    this.announcementsState.unshift(newItem);

    return {
      success: true,
      data: newItem,
    };
  }

  async getAuditTrail(): Promise<ApiResponse<InstitutionalAuditLog[]>> {
    try {
      const res = await apiFetch<InstitutionalAuditLog[]>(
        "/api/v1/vice-principal/audit",
      );
      if (res && res.data) return res;
    } catch {
      // Fallback
    }

    return {
      success: true,
      data: [
        {
          id: "aud-001",
          timestamp: "2026-11-18T16:20:10Z",
          actor: "Dr. Meenakshi Sundaram (Vice Principal)",
          action: "APPROVED_REQUEST",
          entity: "Approval #appr-vp-004 (Mech Timetable Swap)",
          details: "Sanctioned slot swap for Smart Manufacturing Lab.",
          ip_address: "192.168.1.15",
        },
        {
          id: "aud-002",
          timestamp: "2026-11-18T10:00:00Z",
          actor: "Dr. Meenakshi Sundaram (Vice Principal)",
          action: "PUBLISHED_CIRCULAR",
          entity: "Announcement #anc-vp-01",
          details: "Dispatched Mid-Semester Syllabus Completion Directive.",
          ip_address: "192.168.1.15",
        },
        {
          id: "aud-003",
          timestamp: "2026-11-17T11:45:00Z",
          actor: "Dr. Meenakshi Sundaram (Vice Principal)",
          action: "ATTENDANCE_AUDIT",
          entity: "Institutional Attendance Radar",
          details: "Reviewed 184 students with attendance below 75% threshold.",
          ip_address: "192.168.1.15",
        },
        {
          id: "aud-004",
          timestamp: "2026-11-16T10:00:00Z",
          actor: "Dr. Meenakshi Sundaram (Vice Principal)",
          action: "APPROVED_INTERVENTION",
          entity: "Approval #appr-vp-006 (CSE DBMS Remedial Plan)",
          details:
            "Sanctioned special coaching intervention for 18 at-risk students.",
          ip_address: "192.168.1.15",
        },
      ],
    };
  }
}

export const vicePrincipalService = new VicePrincipalService();
