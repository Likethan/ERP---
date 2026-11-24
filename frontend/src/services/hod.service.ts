import { ApiResponse, PaginatedResponse } from "@campusos/types";
import { FacultyDetailView, StudentComprehensiveDetail } from "../types/domain";
import { facultyService } from "./faculty.service";
import { studentsService, StudentFilterParams } from "./students.service";
import { attendanceService } from "./attendance.service";
import { academicsService } from "./academics.service";
import { apiFetch } from "../lib/api-client";

export interface HodDashboardStats {
  department: {
    name: string;
    code: string;
    head: string;
  };
  statistics: {
    totalStudents: number;
    totalFaculty: number;
    totalSubjects: number;
    totalClasses: number;
    averageStudentAttendance: number;
    averageFacultyAttendance: number;
    studentsShortageCount: number;
    pendingApprovalRequests: number;
  };
  studentAnalytics: {
    yearWiseStrength: { year: string; strength: number; percentage: number }[];
    sectionDistribution: {
      section: string;
      students: number;
      attendance: number;
    }[];
  };
  facultyAnalytics: {
    total: number;
    presentToday: number;
    onLeave: number;
    averageWorkloadHours: number;
  };
  attendanceTrends: {
    daily: { day: string; rate: number }[];
    weekly: { week: string; rate: number }[];
    monthlyAverage: number;
    statutoryThreshold: number;
  };
  recentActivities: {
    id: string;
    type: "faculty" | "attendance" | "student" | "request";
    title: string;
    description: string;
    timestamp: string;
  }[];
}

export interface TimetablePeriod {
  period: number;
  time: string;
  isBreak?: boolean;
}

export interface TimetableScheduleItem {
  day: string;
  period: number;
  subjectCode: string;
  subjectName: string;
  facultyName: string;
  classroom: string;
  isLab?: boolean;
}

export interface FacultyWorkloadItem {
  facultyId: string;
  facultyName: string;
  designation: string;
  assignedSubjects: string[];
  weeklyHours: number;
  status: "OPTIMAL" | "HEAVY" | "UNDERLOAD";
}

class HodService {
  private defaultDept = "Computer Science & Engineering";

  async getDashboardStats(
    department: string = this.defaultDept,
  ): Promise<ApiResponse<HodDashboardStats>> {
    try {
      const res = await apiFetch<any>("/api/v1/hod/dashboard");
      if (res && res.data) {
        const d = res.data;
        return {
          success: true,
          data: {
            department: {
              name: d.department?.name || department,
              code: d.department?.code || "CSE",
              head: "Dr. K. S. Anand",
            },
            statistics: {
              totalStudents: d.statistics?.total_students || 720,
              totalFaculty: d.statistics?.total_faculty || 28,
              totalSubjects: d.statistics?.total_subjects || 42,
              totalClasses: d.statistics?.total_classes || 18,
              averageStudentAttendance:
                d.statistics?.average_student_attendance || 88.4,
              averageFacultyAttendance:
                d.statistics?.average_faculty_attendance || 96.2,
              studentsShortageCount:
                d.statistics?.attendance_shortage_count || 14,
              pendingApprovalRequests:
                d.statistics?.pending_approval_requests || 6,
            },
            studentAnalytics: {
              yearWiseStrength: d.student_analytics?.year_wise || [
                { year: "1st Year", strength: 180, percentage: 91.2 },
                { year: "2nd Year", strength: 180, percentage: 88.6 },
                { year: "3rd Year", strength: 180, percentage: 87.1 },
                { year: "4th Year", strength: 180, percentage: 86.8 },
              ],
              sectionDistribution: d.student_analytics
                ?.section_distribution || [
                { section: "CSE-A", students: 68, attendance: 89.2 },
                { section: "CSE-B", students: 65, attendance: 87.8 },
                { section: "CSE-C", students: 67, attendance: 88.1 },
              ],
            },
            facultyAnalytics: {
              total: d.faculty_analytics?.total || 28,
              presentToday: d.faculty_analytics?.present_today || 26,
              onLeave: d.faculty_analytics?.on_leave || 2,
              averageWorkloadHours:
                d.faculty_analytics?.average_workload_hours || 14.5,
            },
            attendanceTrends: {
              daily: d.attendance_trends?.daily || [
                { day: "Mon", rate: 89.5 },
                { day: "Tue", rate: 91.0 },
                { day: "Wed", rate: 88.2 },
                { day: "Thu", rate: 87.4 },
                { day: "Fri", rate: 86.9 },
              ],
              weekly: [
                { week: "Week 1", rate: 89.2 },
                { week: "Week 2", rate: 88.7 },
                { week: "Week 3", rate: 87.9 },
                { week: "Week 4", rate: 88.4 },
              ],
              monthlyAverage: d.attendance_trends?.monthly_average || 88.4,
              statutoryThreshold: 75.0,
            },
            recentActivities: [
              {
                id: "act-1",
                type: "attendance",
                title: "Attendance Finalized: CS301 (Sec A)",
                description:
                  "Dr. Rajesh Sharma finalized period 2 session. 64/68 present.",
                timestamp: "10 mins ago",
              },
              {
                id: "act-2",
                type: "request",
                title: "Leave Endorsement Pending",
                description:
                  "Dr. Priya Nair requested 2 days duty leave for IEEE conference.",
                timestamp: "45 mins ago",
              },
              {
                id: "act-3",
                type: "student",
                title: "Attendance Alert Dispatched",
                description:
                  "Warning SMS & email sent to parents of 14 students below 75%.",
                timestamp: "2 hours ago",
              },
              {
                id: "act-4",
                type: "faculty",
                title: "Course File Updated: CS501",
                description:
                  "Dr. K. S. Anand updated Unit 4 lesson plan & outcomes.",
                timestamp: "Yesterday",
              },
            ],
          },
        };
      }
    } catch {
      // Fallback to computed values from existing mock services
    }

    // Compute from mock data
    const facRes = await facultyService.list({ department });
    const totalFaculty = facRes.data?.length || 28;

    const stuRes = await studentsService.list({ department, pageSize: 100 });
    const totalStudents = stuRes.pagination?.totalRecords || 720;

    return {
      success: true,
      data: {
        department: {
          name: department,
          code: "CSE",
          head: "Dr. K. S. Anand",
        },
        statistics: {
          totalStudents,
          totalFaculty,
          totalSubjects: 42,
          totalClasses: 18,
          averageStudentAttendance: 88.4,
          averageFacultyAttendance: 96.2,
          studentsShortageCount: 14,
          pendingApprovalRequests: 6,
        },
        studentAnalytics: {
          yearWiseStrength: [
            { year: "1st Year", strength: 180, percentage: 91.2 },
            { year: "2nd Year", strength: 180, percentage: 88.6 },
            { year: "3rd Year", strength: 180, percentage: 87.1 },
            { year: "4th Year", strength: 180, percentage: 86.8 },
          ],
          sectionDistribution: [
            { section: "CSE-A", students: 68, attendance: 89.2 },
            { section: "CSE-B", students: 65, attendance: 87.8 },
            { section: "CSE-C", students: 67, attendance: 88.1 },
          ],
        },
        facultyAnalytics: {
          total: totalFaculty,
          presentToday: Math.max(0, totalFaculty - 2),
          onLeave: 2,
          averageWorkloadHours: 14.5,
        },
        attendanceTrends: {
          daily: [
            { day: "Mon", rate: 89.5 },
            { day: "Tue", rate: 91.0 },
            { day: "Wed", rate: 88.2 },
            { day: "Thu", rate: 87.4 },
            { day: "Fri", rate: 86.9 },
          ],
          weekly: [
            { week: "Week 1", rate: 89.2 },
            { week: "Week 2", rate: 88.7 },
            { week: "Week 3", rate: 87.9 },
            { week: "Week 4", rate: 88.4 },
          ],
          monthlyAverage: 88.4,
          statutoryThreshold: 75.0,
        },
        recentActivities: [
          {
            id: "act-1",
            type: "attendance",
            title: "Attendance Finalized: CS301 (Sec A)",
            description:
              "Dr. Rajesh Sharma finalized period 2 session. 64/68 present.",
            timestamp: "10 mins ago",
          },
          {
            id: "act-2",
            type: "request",
            title: "Leave Endorsement Pending",
            description:
              "Dr. Priya Nair requested 2 days duty leave for IEEE conference.",
            timestamp: "45 mins ago",
          },
          {
            id: "act-3",
            type: "student",
            title: "Attendance Alert Dispatched",
            description:
              "Warning notification sent to parents of 14 students below 75%.",
            timestamp: "2 hours ago",
          },
          {
            id: "act-4",
            type: "faculty",
            title: "Course File Updated: CS501",
            description:
              "Dr. K. S. Anand updated Unit 4 lesson plan & outcomes.",
            timestamp: "Yesterday",
          },
        ],
      },
    };
  }

  async getDepartmentFaculty(params?: {
    search?: string;
    designation?: string;
    department?: string;
  }): Promise<PaginatedResponse<FacultyDetailView>> {
    const dept = params?.department || this.defaultDept;
    try {
      const q = new URLSearchParams();
      if (params?.search) q.append("search", params.search);
      if (params?.designation && params.designation !== "ALL")
        q.append("designation", params.designation);
      const res = await apiFetch<any>(`/api/v1/hod/faculty?${q.toString()}`);
      if (res && res.data) {
        // Map backend response into FacultyDetailView shape
        const items: FacultyDetailView[] = res.data.map((f: any) => ({
          id: f.id,
          employeeCode: f.employee_code,
          firstName: f.first_name || f.name.split(" ")[0],
          lastName: f.last_name || f.name.split(" ").slice(1).join(" "),
          email: f.email,
          phone: f.phone,
          designation: f.designation,
          department: f.department || dept,
          qualification: f.qualification,
          specialization: f.specialization,
          joiningDate: f.joining_date,
          status: f.status || "ACTIVE",
          teachingLoadHours: f.teaching_hours || 14,
          assignedSubjects: [
            {
              id: "sub-1",
              code: "CS301",
              name: "Data Structures & Algorithms",
              semester: 5,
              section: "A",
              studentCount: 68,
            },
          ],
          todayClasses: [],
        }));
        return {
          success: true,
          data: items,
          pagination: {
            page: 1,
            pageSize: items.length,
            totalRecords: items.length,
            totalPages: 1,
          },
        };
      }
    } catch {
      // Fallback
    }

    // Scoped strictly to HOD's department
    return facultyService.list({
      department: dept,
      search: params?.search,
      designation: params?.designation,
    });
  }

  async getFacultyById(id: string): Promise<FacultyDetailView | null> {
    try {
      const res = await apiFetch<any>(`/api/v1/hod/faculty/${id}`);
      if (res && res.data) {
        const f = res.data;
        return {
          id: f.id,
          employeeCode: f.employee_code,
          firstName: f.first_name,
          lastName: f.last_name,
          email: f.email,
          phone: f.phone,
          designation: f.designation,
          department: f.department,
          qualification: f.qualification,
          specialization: f.specialization,
          joiningDate: f.joining_date,
          status: f.status,
          teachingLoadHours: f.teaching_hours,
          assignedSubjects: (f.assigned_subjects || []).map(
            (s: any, idx: number) => ({
              id: `sub-${idx}`,
              code: s.code,
              name: s.name,
              semester: s.semester,
              section: s.section,
              studentCount: s.students,
            }),
          ),
          stats: {
            coursesCount: (f.assigned_subjects || []).length,
            totalStudents: 180,
            averageAttendance: 88.4,
            pendingCorrections: 2,
          },
          todayClasses: [],
        };
      }
    } catch {
      // Fallback
    }
    const res = await facultyService.getById(id);
    return res.data;
  }

  async getDepartmentStudents(
    params?: StudentFilterParams,
    department: string = this.defaultDept,
  ): Promise<PaginatedResponse<StudentComprehensiveDetail>> {
    // Enforce department filter strictly
    const scopedParams: StudentFilterParams = {
      ...params,
      department,
    };
    return studentsService.list(scopedParams);
  }

  async getStudentById(id: string): Promise<StudentComprehensiveDetail | null> {
    const res = await apiFetch<StudentComprehensiveDetail>(`/api/v1/hod/students/${id}`);
    return res.data;
  }

  async getAttendanceOverview(department: string = this.defaultDept) {
    try {
      const res = await apiFetch<any>("/api/v1/hod/attendance");
      if (res && res.data) return res.data;
    } catch {
      // Fallback
    }
    const [summaryRes, alertsRes] = await Promise.all([
      attendanceService.getDashboardSummary(),
      attendanceService.getLowAttendanceAlerts(),
    ]);

    const alerts = (alertsRes.data || []).filter(
      (a) =>
        a.department.toLowerCase().includes("computer") ||
        a.department === "CSE",
    );

    return {
      department,
      overall_percentage: summaryRes.data?.overallAttendancePercentage || 88.4,
      present_today: 682,
      absent_today: 38,
      total_enrolled: 720,
      statutory_threshold: 75.0,
      shortage_count:
        alerts.length || summaryRes.data?.studentsBelowThresholdCount || 14,
      class_wise: [
        {
          class_name: "CSE 3rd Sem - Sec A",
          total: 68,
          present: 63,
          rate: 92.6,
        },
        {
          class_name: "CSE 3rd Sem - Sec B",
          total: 65,
          present: 58,
          rate: 89.2,
        },
        {
          class_name: "CSE 5th Sem - Sec A",
          total: 68,
          present: 61,
          rate: 89.7,
        },
        {
          class_name: "CSE 5th Sem - Sec B",
          total: 65,
          present: 56,
          rate: 86.1,
        },
        {
          class_name: "CSE 7th Sem - Sec A",
          total: 60,
          present: 50,
          rate: 83.3,
        },
      ],
      shortage_students:
        alerts.length > 0
          ? alerts
          : [
              {
                rollNumber: "24CSE0114",
                studentName: "Karthik Raja",
                semester: 5,
                section: "A",
                classesAttended: 108,
                totalClasses: 160,
                attendancePercentage: 67.5,
                threshold: 75.0,
              },
              {
                rollNumber: "24CSE0122",
                studentName: "Divya Bharathi",
                semester: 5,
                section: "B",
                classesAttended: 112,
                totalClasses: 160,
                attendancePercentage: 70.0,
                threshold: 75.0,
              },
            ],
    };
  }

  getTimetablePeriods(): TimetablePeriod[] {
    return [
      { period: 1, time: "09:00 - 09:50" },
      { period: 2, time: "09:50 - 10:40" },
      { period: 3, time: "11:00 - 11:50" },
      { period: 4, time: "11:50 - 12:40" },
      { period: 5, time: "01:30 - 02:20" },
      { period: 6, time: "02:20 - 03:10" },
      { period: 7, time: "03:10 - 04:00" },
    ];
  }

  getDepartmentSchedule(semester = 5, section = "A"): TimetableScheduleItem[] {
    return [
      // Monday
      {
        day: "Monday",
        period: 1,
        subjectCode: "CS301",
        subjectName: "Data Structures & Algorithms",
        facultyName: "Dr. Rajesh Sharma",
        classroom: "Hall 302",
      },
      {
        day: "Monday",
        period: 2,
        subjectCode: "CS302",
        subjectName: "Database Management Systems",
        facultyName: "Dr. Priya Nair",
        classroom: "Hall 302",
      },
      {
        day: "Monday",
        period: 3,
        subjectCode: "CS303",
        subjectName: "Computer Networks",
        facultyName: "Prof. S. Ranganathan",
        classroom: "Hall 302",
      },
      {
        day: "Monday",
        period: 4,
        subjectCode: "CS304",
        subjectName: "Operating Systems",
        facultyName: "Dr. K. S. Anand",
        classroom: "Hall 302",
      },
      {
        day: "Monday",
        period: 5,
        subjectCode: "CS305",
        subjectName: "Web Technology Lab",
        facultyName: "Prof. A. Meenakshi",
        classroom: "CS Lab 3",
        isLab: true,
      },
      {
        day: "Monday",
        period: 6,
        subjectCode: "CS305",
        subjectName: "Web Technology Lab",
        facultyName: "Prof. A. Meenakshi",
        classroom: "CS Lab 3",
        isLab: true,
      },
      {
        day: "Monday",
        period: 7,
        subjectCode: "CS308",
        subjectName: "Library / Mentoring",
        facultyName: "Mentor Committee",
        classroom: "Central Library",
      },

      // Tuesday
      {
        day: "Tuesday",
        period: 1,
        subjectCode: "CS302",
        subjectName: "Database Management Systems",
        facultyName: "Dr. Priya Nair",
        classroom: "Hall 302",
      },
      {
        day: "Tuesday",
        period: 2,
        subjectCode: "CS301",
        subjectName: "Data Structures & Algorithms",
        facultyName: "Dr. Rajesh Sharma",
        classroom: "Hall 302",
      },
      {
        day: "Tuesday",
        period: 3,
        subjectCode: "CS304",
        subjectName: "Operating Systems",
        facultyName: "Dr. K. S. Anand",
        classroom: "Hall 302",
      },
      {
        day: "Tuesday",
        period: 4,
        subjectCode: "MA301",
        subjectName: "Discrete Mathematics",
        facultyName: "Dr. R. Venkat",
        classroom: "Hall 302",
      },
      {
        day: "Tuesday",
        period: 5,
        subjectCode: "CS306",
        subjectName: "DBMS Laboratory",
        facultyName: "Dr. Priya Nair",
        classroom: "Database Lab",
        isLab: true,
      },
      {
        day: "Tuesday",
        period: 6,
        subjectCode: "CS306",
        subjectName: "DBMS Laboratory",
        facultyName: "Dr. Priya Nair",
        classroom: "Database Lab",
        isLab: true,
      },
      {
        day: "Tuesday",
        period: 7,
        subjectCode: "CS307",
        subjectName: "Seminar & Aptitude",
        facultyName: "Placement Cell",
        classroom: "Hall 302",
      },

      // Wednesday
      {
        day: "Wednesday",
        period: 1,
        subjectCode: "CS303",
        subjectName: "Computer Networks",
        facultyName: "Prof. S. Ranganathan",
        classroom: "Hall 302",
      },
      {
        day: "Wednesday",
        period: 2,
        subjectCode: "MA301",
        subjectName: "Discrete Mathematics",
        facultyName: "Dr. R. Venkat",
        classroom: "Hall 302",
      },
      {
        day: "Wednesday",
        period: 3,
        subjectCode: "CS301",
        subjectName: "Data Structures & Algorithms",
        facultyName: "Dr. Rajesh Sharma",
        classroom: "Hall 302",
      },
      {
        day: "Wednesday",
        period: 4,
        subjectCode: "CS302",
        subjectName: "Database Management Systems",
        facultyName: "Dr. Priya Nair",
        classroom: "Hall 302",
      },
      {
        day: "Wednesday",
        period: 5,
        subjectCode: "CS304",
        subjectName: "Operating Systems",
        facultyName: "Dr. K. S. Anand",
        classroom: "Hall 302",
      },
      {
        day: "Wednesday",
        period: 6,
        subjectCode: "OE301",
        subjectName: "Open Elective - IoT",
        facultyName: "Prof. T. Balaji",
        classroom: "Hall 204",
      },
      {
        day: "Wednesday",
        period: 7,
        subjectCode: "SP301",
        subjectName: "Sports & Extra-Curricular",
        facultyName: "Physical Director",
        classroom: "Sports Complex",
      },

      // Thursday
      {
        day: "Thursday",
        period: 1,
        subjectCode: "CS304",
        subjectName: "Operating Systems",
        facultyName: "Dr. K. S. Anand",
        classroom: "Hall 302",
      },
      {
        day: "Thursday",
        period: 2,
        subjectCode: "CS303",
        subjectName: "Computer Networks",
        facultyName: "Prof. S. Ranganathan",
        classroom: "Hall 302",
      },
      {
        day: "Thursday",
        period: 3,
        subjectCode: "MA301",
        subjectName: "Discrete Mathematics",
        facultyName: "Dr. R. Venkat",
        classroom: "Hall 302",
      },
      {
        day: "Thursday",
        period: 4,
        subjectCode: "CS301",
        subjectName: "Data Structures & Algorithms",
        facultyName: "Dr. Rajesh Sharma",
        classroom: "Hall 302",
      },
      {
        day: "Thursday",
        period: 5,
        subjectCode: "CS307",
        subjectName: "Networks Laboratory",
        facultyName: "Prof. S. Ranganathan",
        classroom: "Networks Lab",
        isLab: true,
      },
      {
        day: "Thursday",
        period: 6,
        subjectCode: "CS307",
        subjectName: "Networks Laboratory",
        facultyName: "Prof. S. Ranganathan",
        classroom: "Networks Lab",
        isLab: true,
      },
      {
        day: "Thursday",
        period: 7,
        subjectCode: "CS309",
        subjectName: "NPTEL / MOOCs",
        facultyName: "Online Coordinator",
        classroom: "E-Learning Center",
      },

      // Friday
      {
        day: "Friday",
        period: 1,
        subjectCode: "MA301",
        subjectName: "Discrete Mathematics",
        facultyName: "Dr. R. Venkat",
        classroom: "Hall 302",
      },
      {
        day: "Friday",
        period: 2,
        subjectCode: "CS302",
        subjectName: "Database Management Systems",
        facultyName: "Dr. Priya Nair",
        classroom: "Hall 302",
      },
      {
        day: "Friday",
        period: 3,
        subjectCode: "CS304",
        subjectName: "Operating Systems",
        facultyName: "Dr. K. S. Anand",
        classroom: "Hall 302",
      },
      {
        day: "Friday",
        period: 4,
        subjectCode: "CS303",
        subjectName: "Computer Networks",
        facultyName: "Prof. S. Ranganathan",
        classroom: "Hall 302",
      },
      {
        day: "Friday",
        period: 5,
        subjectCode: "OE301",
        subjectName: "Open Elective - IoT",
        facultyName: "Prof. T. Balaji",
        classroom: "Hall 204",
      },
      {
        day: "Friday",
        period: 6,
        subjectCode: "CS310",
        subjectName: "Project Phase-I Mentoring",
        facultyName: "Project Committee",
        classroom: "CS Lab 1",
      },
      {
        day: "Friday",
        period: 7,
        subjectCode: "CS310",
        subjectName: "Project Phase-I Mentoring",
        facultyName: "Project Committee",
        classroom: "CS Lab 1",
      },

      // Saturday
      {
        day: "Saturday",
        period: 1,
        subjectCode: "CS301",
        subjectName: "Data Structures (Tutorial)",
        facultyName: "Dr. Rajesh Sharma",
        classroom: "Hall 302",
      },
      {
        day: "Saturday",
        period: 2,
        subjectCode: "CS303",
        subjectName: "Networks (Tutorial)",
        facultyName: "Prof. S. Ranganathan",
        classroom: "Hall 302",
      },
      {
        day: "Saturday",
        period: 3,
        subjectCode: "CS302",
        subjectName: "DBMS (Tutorial)",
        facultyName: "Dr. Priya Nair",
        classroom: "Hall 302",
      },
      {
        day: "Saturday",
        period: 4,
        subjectCode: "CC301",
        subjectName: "Coding Club & Hackathon",
        facultyName: "Club Coordinators",
        classroom: "CS Center of Excellence",
      },
    ];
  }

  getFacultyWorkloads(): FacultyWorkloadItem[] {
    return [
      {
        facultyId: "fac-cse-01",
        facultyName: "Dr. Rajesh Sharma",
        designation: "Professor & Dean",
        assignedSubjects: ["CS301 (Sec A)", "CS301 (Sec B)", "CS501 (Sec A)"],
        weeklyHours: 14,
        status: "OPTIMAL",
      },
      {
        facultyId: "fac-cse-02",
        facultyName: "Dr. Priya Nair",
        designation: "Associate Professor",
        assignedSubjects: ["CS302 (Sec A)", "CS302 (Sec B)", "CS306 Lab"],
        weeklyHours: 16,
        status: "OPTIMAL",
      },
      {
        facultyId: "fac-cse-03",
        facultyName: "Prof. S. Ranganathan",
        designation: "Assistant Professor",
        assignedSubjects: ["CS303 (Sec A)", "CS303 (Sec B)", "CS307 Lab"],
        weeklyHours: 18,
        status: "HEAVY",
      },
      {
        facultyId: "fac-cse-04",
        facultyName: "Dr. K. S. Anand",
        designation: "Professor & HOD",
        assignedSubjects: ["CS304 (Sec A)", "CS304 (Sec B)"],
        weeklyHours: 10,
        status: "OPTIMAL",
      },
      {
        facultyId: "fac-cse-05",
        facultyName: "Prof. A. Meenakshi",
        designation: "Assistant Professor",
        assignedSubjects: ["CS305 Lab (Sec A)", "CS305 Lab (Sec B)", "OE301"],
        weeklyHours: 16,
        status: "OPTIMAL",
      },
      {
        facultyId: "fac-cse-06",
        facultyName: "Dr. R. Venkat",
        designation: "Associate Professor",
        assignedSubjects: ["MA301 (Sec A)", "MA301 (Sec B)"],
        weeklyHours: 12,
        status: "OPTIMAL",
      },
    ];
  }

  // =========================================================================
  // PHASE 2: ACADEMIC MANAGEMENT & DEPARTMENT APPROVALS
  // =========================================================================

  async getCurriculum(
    semester?: number,
  ): Promise<ApiResponse<HodCurriculumData>> {
    try {
      const url = semester
        ? `/api/v1/hod/curriculum?semester=${semester}`
        : "/api/v1/hod/curriculum";
      const res = await apiFetch<any>(url);
      if (res && res.data) {
        return { success: true, data: res.data };
      }
    } catch {
      // Fallback to department mock
    }
    return { success: true, data: this.getMockCurriculum(semester) };
  }

  async getLessonPlans(
    subjectCode?: string,
  ): Promise<ApiResponse<HodLessonPlansData>> {
    try {
      const url = subjectCode
        ? `/api/v1/hod/lesson-plans?subject_code=${subjectCode}`
        : "/api/v1/hod/lesson-plans";
      const res = await apiFetch<any>(url);
      if (res && res.data) {
        return { success: true, data: res.data };
      }
    } catch {
      // Fallback
    }
    return { success: true, data: this.getMockLessonPlans(subjectCode) };
  }

  async getExaminations(): Promise<ApiResponse<HodExaminationsData>> {
    try {
      const res = await apiFetch<any>("/api/v1/hod/examinations");
      if (res && res.data) {
        return { success: true, data: res.data };
      }
    } catch {
      // Fallback
    }
    return { success: true, data: this.getMockExaminations() };
  }

  async getInternalMarks(
    semester?: number,
    courseCode?: string,
  ): Promise<ApiResponse<HodInternalMarksData>> {
    try {
      const params = new URLSearchParams();
      if (semester) params.append("semester", String(semester));
      if (courseCode) params.append("course_code", courseCode);
      const url = `/api/v1/hod/internal-marks${params.toString() ? `?${params.toString()}` : ""}`;
      const res = await apiFetch<any>(url);
      if (res && res.data) {
        return { success: true, data: res.data };
      }
    } catch {
      // Fallback
    }
    return {
      success: true,
      data: this.getMockInternalMarks(semester, courseCode),
    };
  }

  async requestMarkCorrection(payload: {
    studentId: string;
    assessmentId: string;
    courseCode: string;
    originalMark: number;
    requestedMark: number;
    reason: string;
  }): Promise<ApiResponse<any>> {
    try {
      const res = await apiFetch<any>(
        "/api/v1/hod/internal-marks/correction-request",
        {
          method: "POST",
          body: JSON.stringify({
            student_id: payload.studentId,
            assessment_id: payload.assessmentId,
            course_code: payload.courseCode,
            original_mark: payload.originalMark,
            requested_mark: payload.requestedMark,
            reason: payload.reason,
          }),
        },
      );
      if (res && res.data) {
        return { success: true, data: res.data };
      }
    } catch {
      // Return simulated audit record
    }
    return {
      success: true,
      data: {
        correction_id: `corr-${Date.now()}`,
        status: "PENDING_AUDIT",
        message:
          "Mark correction request recorded in departmental audit ledger.",
        ...payload,
      },
    };
  }

  async getSemesterResults(
    semester?: number,
  ): Promise<ApiResponse<HodSemesterResultsData>> {
    try {
      const url = semester
        ? `/api/v1/hod/results?semester=${semester}`
        : "/api/v1/hod/results";
      const res = await apiFetch<any>(url);
      if (res && res.data) {
        return { success: true, data: res.data };
      }
    } catch {
      // Fallback
    }
    return { success: true, data: this.getMockSemesterResults() };
  }

  async getApprovals(
    category: string = "ALL",
    statusFilter: string = "ALL",
  ): Promise<ApiResponse<HodApprovalsData>> {
    try {
      const params = new URLSearchParams();
      if (category !== "ALL") params.append("category", category);
      if (statusFilter !== "ALL") params.append("status_filter", statusFilter);
      const url = `/api/v1/hod/approvals${params.toString() ? `?${params.toString()}` : ""}`;
      const res = await apiFetch<any>(url);
      if (res && res.data) {
        return { success: true, data: res.data };
      }
    } catch {
      // Fallback
    }
    return {
      success: true,
      data: this.getMockApprovals(category, statusFilter),
    };
  }

  async processApprovalAction(
    approvalId: string,
    action: "APPROVE" | "REJECT" | "REQUEST_INFO",
    remarks?: string,
  ): Promise<ApiResponse<HodApprovalItem>> {
    try {
      const res = await apiFetch<any>(
        `/api/v1/hod/approvals/${approvalId}/action`,
        {
          method: "POST",
          body: JSON.stringify({ action, remarks }),
        },
      );
      if (res && res.data) {
        return { success: true, data: res.data };
      }
    } catch {
      // Fallback locally
    }
    const target = this._mockApprovalsStore.find((a) => a.id === approvalId);
    if (target) {
      const statusMap = {
        APPROVE: "APPROVED" as const,
        REJECT: "REJECTED" as const,
        REQUEST_INFO: "INFO_REQUESTED" as const,
      };
      target.status = statusMap[action];
      target.remarks = remarks || `Action ${action} confirmed by HOD.`;
      target.decidedBy = "Dr. K. S. Anand (HOD)";
      target.decisionDate = new Date().toISOString();
      target.auditTrail.push({
        action: target.status,
        by: "Dr. K. S. Anand (HOD)",
        timestamp: new Date().toISOString(),
        notes: remarks || `Action ${action} rendered by HOD.`,
      });
      return { success: true, data: target };
    }
    throw new Error(`Approval item ${approvalId} not found`);
  }

  // --- Mock Generators for Phase 2 ---

  private getMockCurriculum(semester?: number): HodCurriculumData {
    const subjects: HodSubjectItem[] = [
      {
        id: "sub-cs201",
        code: "CS201",
        name: "Data Structures & Core Algorithms",
        shortName: "DSA",
        credits: 4,
        type: "THEORY_LAB",
        category: "CORE",
        semester: 3,
        regulation: "R-2026",
        academicYear: "2026-2027",
        assignedFaculty: "Dr. Rajesh Sharma",
        assignedFacultyId: "fac-001",
        sections: ["A", "B"],
        syllabusCompletion: 85,
        coCount: 5,
        poMapped: 10,
      },
      {
        id: "sub-cs202",
        code: "CS202",
        name: "Object Oriented Programming in Java & C++",
        shortName: "OOP",
        credits: 4,
        type: "THEORY_LAB",
        category: "CORE",
        semester: 3,
        regulation: "R-2026",
        academicYear: "2026-2027",
        assignedFaculty: "Dr. Priya Nair",
        assignedFacultyId: "fac-002",
        sections: ["A", "B"],
        syllabusCompletion: 82,
        coCount: 5,
        poMapped: 8,
      },
      {
        id: "sub-cs301",
        code: "CS301",
        name: "Advanced Data Structures & Analysis",
        shortName: "ADSA",
        credits: 4,
        type: "THEORY_LAB",
        category: "CORE",
        semester: 5,
        regulation: "R-2026",
        academicYear: "2026-2027",
        assignedFaculty: "Dr. Rajesh Sharma",
        assignedFacultyId: "fac-001",
        sections: ["A"],
        syllabusCompletion: 80,
        coCount: 5,
        poMapped: 11,
      },
      {
        id: "sub-cs302",
        code: "CS302",
        name: "Database Management Systems",
        shortName: "DBMS",
        credits: 4,
        type: "THEORY_LAB",
        category: "CORE",
        semester: 5,
        regulation: "R-2026",
        academicYear: "2026-2027",
        assignedFaculty: "Dr. Priya Nair",
        assignedFacultyId: "fac-002",
        sections: ["A"],
        syllabusCompletion: 86,
        coCount: 5,
        poMapped: 9,
      },
      {
        id: "sub-cs303",
        code: "CS303",
        name: "Computer Networks & Protocols",
        shortName: "CN",
        credits: 4,
        type: "THEORY_LAB",
        category: "CORE",
        semester: 5,
        regulation: "R-2026",
        academicYear: "2026-2027",
        assignedFaculty: "Prof. S. Ranganathan",
        assignedFacultyId: "fac-003",
        sections: ["A"],
        syllabusCompletion: 74,
        coCount: 5,
        poMapped: 10,
      },
      {
        id: "sub-cs304",
        code: "CS304",
        name: "Design & Analysis of Algorithms",
        shortName: "DAA",
        credits: 3,
        type: "THEORY",
        category: "CORE",
        semester: 5,
        regulation: "R-2026",
        academicYear: "2026-2027",
        assignedFaculty: "Prof. K. Meenakshi",
        assignedFacultyId: "fac-004",
        sections: ["A"],
        syllabusCompletion: 78,
        coCount: 5,
        poMapped: 9,
      },
      {
        id: "sub-cs401",
        code: "CS401",
        name: "Cloud Computing Architecture",
        shortName: "CCA",
        credits: 3,
        type: "THEORY",
        category: "ELECTIVE",
        semester: 7,
        regulation: "R-2026",
        academicYear: "2026-2027",
        assignedFaculty: "Dr. Rajesh Sharma",
        assignedFacultyId: "fac-001",
        sections: ["A"],
        syllabusCompletion: 90,
        coCount: 5,
        poMapped: 8,
      },
      {
        id: "sub-cs402",
        code: "CS402",
        name: "Deep Learning & Neural Networks",
        shortName: "DLNN",
        credits: 4,
        type: "THEORY_LAB",
        category: "ELECTIVE",
        semester: 7,
        regulation: "R-2026",
        academicYear: "2026-2027",
        assignedFaculty: "Dr. Priya Nair",
        assignedFacultyId: "fac-002",
        sections: ["A"],
        syllabusCompletion: 88,
        coCount: 5,
        poMapped: 12,
      },
    ];

    const filtered = semester
      ? subjects.filter((s) => s.semester === semester)
      : subjects;

    return {
      department: "Computer Science & Engineering",
      regulation: "R-2026 Autonomous",
      totalCredits: 164,
      subjects: filtered,
      allocationSummary: {
        totalSubjects: filtered.length,
        allocatedSubjects: filtered.length,
        unallocatedSubjects: 0,
        allocationConflicts: 0,
      },
      curriculumScheme: {
        program: "B.Tech Computer Science & Engineering",
        academicYear: "2026-2027",
        totalSemesters: 8,
        averageSyllabusCompletion: 82.8,
      },
      courseOutcomesSample: [
        {
          coCode: "CO1",
          description:
            "Analyze asymptotic complexity of iterative and recursive algorithms.",
          bloomLevel: "K4 (Analyze)",
        },
        {
          coCode: "CO2",
          description:
            "Design and implement self-balancing search trees and multidimensional indexes.",
          bloomLevel: "K3 (Apply)",
        },
        {
          coCode: "CO3",
          description:
            "Formulate dynamic programming and greedy strategies for optimization problems.",
          bloomLevel: "K4 (Analyze)",
        },
        {
          coCode: "CO4",
          description:
            "Develop graph traversal and network flow algorithms for real-world topologies.",
          bloomLevel: "K3 (Apply)",
        },
        {
          coCode: "CO5",
          description:
            "Evaluate P and NP completeness concepts in computational complexity.",
          bloomLevel: "K5 (Evaluate)",
        },
      ],
      coPoMatrix: [
        { co: "CO1", PO1: 3, PO2: 3, PO3: 2, PO4: 2, PO5: 1, PSO1: 3, PSO2: 2 },
        { co: "CO2", PO1: 3, PO2: 3, PO3: 3, PO4: 2, PO5: 2, PSO1: 3, PSO2: 2 },
        { co: "CO3", PO1: 3, PO2: 2, PO3: 3, PO4: 3, PO5: 2, PSO1: 3, PSO2: 3 },
        { co: "CO4", PO1: 2, PO2: 3, PO3: 2, PO4: 2, PO5: 2, PSO1: 2, PSO2: 3 },
        { co: "CO5", PO1: 3, PO2: 2, PO3: 1, PO4: 1, PO5: 1, PSO1: 2, PSO2: 1 },
      ],
    };
  }

  private getMockLessonPlans(subjectCode?: string): HodLessonPlansData {
    const plans: HodLessonPlanItem[] = [
      {
        id: "lp-cs301",
        courseCode: "CS301",
        courseName: "Advanced Data Structures & Analysis",
        section: "A",
        facultyName: "Dr. Rajesh Sharma",
        facultyDesignation: "Professor & Dean",
        totalPlannedHours: 45,
        totalCompletedHours: 36,
        overallCompletionPercentage: 80.0,
        status: "IN_PROGRESS",
        pendingPlansCount: 0,
        units: [
          {
            unitNumber: 1,
            title: "Linear Data Structures & Complexity Analysis",
            plannedHours: 9,
            completedHours: 9,
            status: "COMPLETED",
            completionPercentage: 100,
            topics: [
              {
                topic: "Asymptotic notations & Big-O complexity",
                completed: true,
              },
              {
                topic: "Amortized complexity of dynamic tables",
                completed: true,
              },
              {
                topic: "Singly and doubly linked lists operations",
                completed: true,
              },
              { topic: "Stack and queue memory abstractions", completed: true },
            ],
          },
          {
            unitNumber: 2,
            title: "Hierarchical Structures & Balanced Trees",
            plannedHours: 10,
            completedHours: 10,
            status: "COMPLETED",
            completionPercentage: 100,
            topics: [
              {
                topic: "Binary search trees insertion and deletion",
                completed: true,
              },
              {
                topic: "AVL Tree single and double rotations",
                completed: true,
              },
              { topic: "Red-Black Tree coloring invariants", completed: true },
              {
                topic: "B-Trees and B+ Trees for secondary storage indexing",
                completed: true,
              },
            ],
          },
          {
            unitNumber: 3,
            title: "Heaps & Disjoint Set Forests",
            plannedHours: 8,
            completedHours: 8,
            status: "COMPLETED",
            completionPercentage: 100,
            topics: [
              { topic: "Min/Max Binary Heaps and Heapify", completed: true },
              { topic: "Binomial Heaps and merge operations", completed: true },
              {
                topic: "Fibonacci Heaps and amortized extract-min",
                completed: true,
              },
              {
                topic: "Disjoint set union by rank and path compression",
                completed: true,
              },
            ],
          },
          {
            unitNumber: 4,
            title: "Graph Algorithms & Shortest Paths",
            plannedHours: 10,
            completedHours: 7,
            status: "IN_PROGRESS",
            completionPercentage: 70,
            topics: [
              {
                topic: "Breadth-first and depth-first traversals",
                completed: true,
              },
              {
                topic: "Dijkstra algorithm with priority queues",
                completed: true,
              },
              {
                topic: "Bellman-Ford and negative cycle detection",
                completed: true,
              },
              {
                topic: "All-pairs shortest paths: Floyd-Warshall",
                completed: false,
              },
              {
                topic: "Network maximum flow: Ford-Fulkerson",
                completed: false,
              },
            ],
          },
          {
            unitNumber: 5,
            title: "NP-Completeness & Approximation Algorithms",
            plannedHours: 8,
            completedHours: 2,
            status: "IN_PROGRESS",
            completionPercentage: 25,
            topics: [
              {
                topic: "Polynomial time reductions and Turing reductions",
                completed: true,
              },
              {
                topic: "Classes P, NP, NP-Hard, and NP-Complete",
                completed: false,
              },
              { topic: "Cook-Levin theorem overview", completed: false },
              {
                topic: "Vertex cover and Traveling Salesperson approximations",
                completed: false,
              },
            ],
          },
        ],
      },
      {
        id: "lp-cs302",
        courseCode: "CS302",
        courseName: "Database Management Systems",
        section: "A",
        facultyName: "Dr. Priya Nair",
        facultyDesignation: "Associate Professor",
        totalPlannedHours: 45,
        totalCompletedHours: 39,
        overallCompletionPercentage: 86.6,
        status: "IN_PROGRESS",
        pendingPlansCount: 0,
        units: [
          {
            unitNumber: 1,
            title: "Relational Data Model & SQL Queries",
            plannedHours: 9,
            completedHours: 9,
            status: "COMPLETED",
            completionPercentage: 100,
            topics: [
              {
                topic: "ER Modeling and relational schema translation",
                completed: true,
              },
              { topic: "Relational algebra operations", completed: true },
              {
                topic: "Complex SQL joins and aggregate groupings",
                completed: true,
              },
            ],
          },
          {
            unitNumber: 2,
            title: "Normalization & Functional Dependencies",
            plannedHours: 9,
            completedHours: 9,
            status: "COMPLETED",
            completionPercentage: 100,
            topics: [
              { topic: "1NF, 2NF, 3NF, BCNF decomposition", completed: true },
              {
                topic: "Lossless join and dependency preservation",
                completed: true,
              },
            ],
          },
          {
            unitNumber: 3,
            title: "Transaction Processing & Concurrency Control",
            plannedHours: 10,
            completedHours: 10,
            status: "COMPLETED",
            completionPercentage: 100,
            topics: [
              {
                topic: "ACID properties and serializability schedules",
                completed: true,
              },
              { topic: "Two-phase locking protocol (2PL)", completed: true },
              { topic: "Timestamp-based ordering protocols", completed: true },
            ],
          },
          {
            unitNumber: 4,
            title: "Query Processing & Optimization",
            plannedHours: 9,
            completedHours: 8,
            status: "IN_PROGRESS",
            completionPercentage: 88,
            topics: [
              {
                topic: "Query tree generation and heuristic optimization",
                completed: true,
              },
              {
                topic: "Cost-based execution plan estimation",
                completed: true,
              },
            ],
          },
          {
            unitNumber: 5,
            title: "Distributed Databases & NoSQL Storage",
            plannedHours: 8,
            completedHours: 3,
            status: "IN_PROGRESS",
            completionPercentage: 37,
            topics: [
              { topic: "CAP Theorem and BASE architecture", completed: true },
              {
                topic: "Document-oriented databases (MongoDB)",
                completed: false,
              },
              {
                topic: "Columnar stores and distributed sharding",
                completed: false,
              },
            ],
          },
        ],
      },
      {
        id: "lp-cs303",
        courseCode: "CS303",
        courseName: "Computer Networks & Protocols",
        section: "A",
        facultyName: "Prof. S. Ranganathan",
        facultyDesignation: "Assistant Professor",
        totalPlannedHours: 45,
        totalCompletedHours: 33,
        overallCompletionPercentage: 73.3,
        status: "IN_PROGRESS",
        pendingPlansCount: 1,
        units: [
          {
            unitNumber: 1,
            title: "Physical Layer & Media Access Control",
            plannedHours: 9,
            completedHours: 9,
            status: "COMPLETED",
            completionPercentage: 100,
            topics: [
              { topic: "OSI and TCP/IP protocol layering", completed: true },
              {
                topic: "Ethernet 802.3 and CSMA/CD protocols",
                completed: true,
              },
            ],
          },
          {
            unitNumber: 2,
            title: "Network Layer & IPv4/IPv6 Routing",
            plannedHours: 10,
            completedHours: 10,
            status: "COMPLETED",
            completionPercentage: 100,
            topics: [
              { topic: "CIDR subnetting and supernetting", completed: true },
              { topic: "OSPF Link-State and BGP Path-Vector", completed: true },
            ],
          },
          {
            unitNumber: 3,
            title: "Transport Layer & Congestion Control",
            plannedHours: 9,
            completedHours: 8,
            status: "IN_PROGRESS",
            completionPercentage: 88,
            topics: [
              {
                topic: "TCP three-way handshake and connection teardown",
                completed: true,
              },
              {
                topic: "TCP Reno and Cubic congestion window scaling",
                completed: true,
              },
            ],
          },
          {
            unitNumber: 4,
            title: "Application Layer & Network Security",
            plannedHours: 9,
            completedHours: 5,
            status: "IN_PROGRESS",
            completionPercentage: 55,
            topics: [
              {
                topic: "DNS hierarchy and iterative resolution",
                completed: true,
              },
              { topic: "TLS 1.3 cryptographic handshakes", completed: false },
            ],
          },
          {
            unitNumber: 5,
            title: "Software Defined Networking (SDN)",
            plannedHours: 8,
            completedHours: 1,
            status: "IN_PROGRESS",
            completionPercentage: 12,
            topics: [
              {
                topic: "Separation of control and data planes",
                completed: true,
              },
              {
                topic: "OpenFlow protocol and centralized controllers",
                completed: false,
              },
            ],
          },
        ],
      },
    ];

    const filtered = subjectCode
      ? plans.filter(
          (p) => p.courseCode.toUpperCase() === subjectCode.toUpperCase(),
        )
      : plans;

    return {
      department: "Computer Science & Engineering",
      lessonPlans: filtered,
      summary: {
        totalMonitoredCourses: filtered.length,
        averageSyllabusCompletion:
          filtered.length > 0
            ? Math.round(
                (filtered.reduce(
                  (acc, p) => acc + p.overallCompletionPercentage,
                  0,
                ) /
                  filtered.length) *
                  10,
              ) / 10
            : 0,
        coursesBehindSchedule: filtered.filter(
          (p) => p.overallCompletionPercentage < 75.0,
        ).length,
        pendingLessonPlans: filtered.reduce(
          (acc, p) => acc + p.pendingPlansCount,
          0,
        ),
      },
    };
  }

  private getMockExaminations(): HodExaminationsData {
    return {
      department: "Computer Science & Engineering",
      terms: [
        {
          id: "term-ia1",
          name: "Internal Assessment Test 1 (IA-1)",
          academicYear: "2026-2027",
          status: "COMPLETED",
          startDate: "2026-09-15",
          endDate: "2026-09-22",
          marksSubmissionDeadline: "2026-09-28",
          submissionStatus: "COMPLETED (100%)",
        },
        {
          id: "term-ia2",
          name: "Internal Assessment Test 2 (IA-2)",
          academicYear: "2026-2027",
          status: "COMPLETED",
          startDate: "2026-10-20",
          endDate: "2026-10-27",
          marksSubmissionDeadline: "2026-11-04",
          submissionStatus: "PENDING_VERIFICATION (92%)",
        },
        {
          id: "term-model",
          name: "Model Examination Nov 2026",
          academicYear: "2026-2027",
          status: "ONGOING",
          startDate: "2026-11-18",
          endDate: "2026-11-26",
          marksSubmissionDeadline: "2026-12-02",
          submissionStatus: "IN_PROGRESS",
        },
        {
          id: "term-ese",
          name: "End Semester Autonomous Theory Examinations",
          academicYear: "2026-2027",
          status: "UPCOMING",
          startDate: "2026-12-08",
          endDate: "2026-12-22",
          marksSubmissionDeadline: "2027-01-05",
          submissionStatus: "SCHEDULED",
        },
      ],
      schedules: [
        {
          id: "sch-001",
          date: "2026-11-18",
          time: "10:00 AM - 01:00 PM",
          duration: "3 Hours",
          courseCode: "CS301",
          courseName: "Advanced Data Structures & Analysis",
          semester: 5,
          section: "A",
          examType: "MODEL_EXAMINATION",
          hallNumber: "EXAM-HALL-301",
          chiefInvigilator: "Dr. Rajesh Sharma",
          totalCandidates: 68,
        },
        {
          id: "sch-002",
          date: "2026-11-20",
          time: "10:00 AM - 01:00 PM",
          duration: "3 Hours",
          courseCode: "CS302",
          courseName: "Database Management Systems",
          semester: 5,
          section: "A",
          examType: "MODEL_EXAMINATION",
          hallNumber: "EXAM-HALL-302",
          chiefInvigilator: "Dr. Priya Nair",
          totalCandidates: 68,
        },
        {
          id: "sch-003",
          date: "2026-11-22",
          time: "10:00 AM - 01:00 PM",
          duration: "3 Hours",
          courseCode: "CS303",
          courseName: "Computer Networks & Protocols",
          semester: 5,
          section: "A",
          examType: "MODEL_EXAMINATION",
          hallNumber: "EXAM-HALL-303",
          chiefInvigilator: "Prof. S. Ranganathan",
          totalCandidates: 68,
        },
        {
          id: "sch-004",
          date: "2026-11-24",
          time: "10:00 AM - 01:00 PM",
          duration: "3 Hours",
          courseCode: "CS304",
          courseName: "Design & Analysis of Algorithms",
          semester: 5,
          section: "A",
          examType: "MODEL_EXAMINATION",
          hallNumber: "EXAM-HALL-304",
          chiefInvigilator: "Prof. K. Meenakshi",
          totalCandidates: 68,
        },
      ],
      submissionProgress: [
        {
          courseCode: "CS301",
          courseName: "Advanced Data Structures & Analysis",
          facultyName: "Dr. Rajesh Sharma",
          ia1Status: "SUBMITTED",
          ia2Status: "SUBMITTED",
          modelStatus: "PENDING_EVALUATION",
          pendingCount: 0,
          missingMarks: 0,
        },
        {
          courseCode: "CS302",
          courseName: "Database Management Systems",
          facultyName: "Dr. Priya Nair",
          ia1Status: "SUBMITTED",
          ia2Status: "SUBMITTED",
          modelStatus: "PENDING_EVALUATION",
          pendingCount: 0,
          missingMarks: 0,
        },
        {
          courseCode: "CS303",
          courseName: "Computer Networks & Protocols",
          facultyName: "Prof. S. Ranganathan",
          ia1Status: "SUBMITTED",
          ia2Status: "PARTIAL (64/68)",
          modelStatus: "NOT_STARTED",
          pendingCount: 4,
          missingMarks: 4,
        },
      ],
      summary: {
        totalScheduledExams: 4,
        ongoingExams: 1,
        completedTerms: 2,
        missingMarksTotal: 4,
        submissionComplianceRate: 95.6,
      },
    };
  }

  private getMockInternalMarks(
    semester?: number,
    courseCode?: string,
  ): HodInternalMarksData {
    const records: HodInternalMarkRecord[] = [
      {
        id: "im-001",
        studentId: "std-001",
        studentName: "Aarav Patel",
        rollNumber: "24CSE0101",
        semester: 5,
        section: "A",
        courseCode: "CS301",
        courseName: "Advanced Data Structures & Analysis",
        facultyName: "Dr. Rajesh Sharma",
        ia1: 24,
        ia2: 23,
        ia3Model: 46,
        assignments: 19,
        attendanceScore: 10,
        totalInternal: 47.5,
        maxInternal: 50.0,
        percentage: 95.0,
        status: "FINALIZED",
        requiresAttention: false,
      },
      {
        id: "im-002",
        studentId: "std-002",
        studentName: "Diya Sharma",
        rollNumber: "24CSE0102",
        semester: 5,
        section: "A",
        courseCode: "CS301",
        courseName: "Advanced Data Structures & Analysis",
        facultyName: "Dr. Rajesh Sharma",
        ia1: 22,
        ia2: 21,
        ia3Model: 43,
        assignments: 18,
        attendanceScore: 8,
        totalInternal: 44.0,
        maxInternal: 50.0,
        percentage: 88.0,
        status: "FINALIZED",
        requiresAttention: false,
      },
      {
        id: "im-003",
        studentId: "std-003",
        studentName: "Rohan Iyer",
        rollNumber: "24CSE0103",
        semester: 5,
        section: "A",
        courseCode: "CS301",
        courseName: "Advanced Data Structures & Analysis",
        facultyName: "Dr. Rajesh Sharma",
        ia1: 15,
        ia2: 14,
        ia3Model: 28,
        assignments: 12,
        attendanceScore: 6,
        totalInternal: 29.5,
        maxInternal: 50.0,
        percentage: 59.0,
        status: "VERIFIED",
        requiresAttention: false,
      },
      {
        id: "im-004",
        studentId: "std-004",
        studentName: "Ananya Reddy",
        rollNumber: "24CSE0104",
        semester: 5,
        section: "A",
        courseCode: "CS301",
        courseName: "Advanced Data Structures & Analysis",
        facultyName: "Dr. Rajesh Sharma",
        ia1: 24,
        ia2: 24,
        ia3Model: 48,
        assignments: 19,
        attendanceScore: 9,
        totalInternal: 48.0,
        maxInternal: 50.0,
        percentage: 96.0,
        status: "FINALIZED",
        requiresAttention: false,
      },
      {
        id: "im-005",
        studentId: "std-005",
        studentName: "Karthik Raja",
        rollNumber: "24CSE0105",
        semester: 5,
        section: "A",
        courseCode: "CS303",
        courseName: "Computer Networks & Protocols",
        facultyName: "Prof. S. Ranganathan",
        ia1: 11,
        ia2: 10,
        ia3Model: 20,
        assignments: 10,
        attendanceScore: 5,
        totalInternal: 21.0,
        maxInternal: 50.0,
        percentage: 42.0,
        status: "ENTERED",
        requiresAttention: true,
      },
    ];

    let filtered = records;
    if (semester) filtered = filtered.filter((r) => r.semester === semester);
    if (courseCode)
      filtered = filtered.filter(
        (r) => r.courseCode.toUpperCase() === courseCode.toUpperCase(),
      );

    const attentionList = filtered.filter(
      (r) => r.requiresAttention || r.percentage < 50.0,
    );

    return {
      department: "Computer Science & Engineering",
      records: filtered,
      attentionList,
      summary: {
        totalRecords: filtered.length,
        averagePercentage:
          filtered.length > 0
            ? Math.round(
                (filtered.reduce((acc, r) => acc + r.percentage, 0) /
                  filtered.length) *
                  10,
              ) / 10
            : 0,
        studentsRequiringAttention: attentionList.length,
        missingMarksCount: 1,
      },
    };
  }

  private getMockSemesterResults(): HodSemesterResultsData {
    return {
      department: "Computer Science & Engineering",
      overview: {
        academicYear: "2026-2027",
        examination:
          "Autonomous End Semester Examinations (Previous Academic Term)",
        totalStudentsAppeared: 240,
        totalStudentsPassed: 218,
        totalStudentsFailed: 22,
        passPercentage: 90.8,
        previousSemesterPassPercentage: 88.5,
        percentageDelta: "+2.3%",
      },
      subjectResults: [
        {
          courseCode: "CS301",
          courseName: "Advanced Data Structures & Analysis",
          faculty: "Dr. Rajesh Sharma",
          appeared: 68,
          passed: 64,
          failed: 4,
          passPercentage: 94.1,
          averageGradePoint: 8.3,
        },
        {
          courseCode: "CS302",
          courseName: "Database Management Systems",
          faculty: "Dr. Priya Nair",
          appeared: 68,
          passed: 63,
          failed: 5,
          passPercentage: 92.6,
          averageGradePoint: 8.1,
        },
        {
          courseCode: "CS303",
          courseName: "Computer Networks & Protocols",
          faculty: "Prof. S. Ranganathan",
          appeared: 68,
          passed: 58,
          failed: 10,
          passPercentage: 85.3,
          averageGradePoint: 7.4,
        },
        {
          courseCode: "CS304",
          courseName: "Design & Analysis of Algorithms",
          faculty: "Prof. K. Meenakshi",
          appeared: 68,
          passed: 61,
          failed: 7,
          passPercentage: 89.7,
          averageGradePoint: 7.8,
        },
      ],
      toppers: [
        {
          rank: 1,
          rollNumber: "24CSE0101",
          name: "Aarav Patel",
          semester: 5,
          cgpa: 9.42,
          sgpa: 9.6,
          totalCredits: 104,
          arrears: 0,
          status: "FIRST_CLASS_DISTINCTION",
        },
        {
          rank: 2,
          rollNumber: "24CSE0104",
          name: "Ananya Reddy",
          semester: 5,
          cgpa: 9.15,
          sgpa: 9.3,
          totalCredits: 104,
          arrears: 0,
          status: "FIRST_CLASS_DISTINCTION",
        },
        {
          rank: 3,
          rollNumber: "24CSE0102",
          name: "Diya Sharma",
          semester: 5,
          cgpa: 8.84,
          sgpa: 8.9,
          totalCredits: 104,
          arrears: 0,
          status: "FIRST_CLASS_DISTINCTION",
        },
      ],
      studentsNeedingSupport: [
        {
          rollNumber: "24CSE0103",
          name: "Rohan Iyer",
          semester: 5,
          cgpa: 6.12,
          sgpa: 5.8,
          arrears: 1,
          arrearSubjects: ["CS303 Computer Networks"],
          supportPlan:
            "Peer tutoring and Saturday remedial coaching scheduled.",
        },
        {
          rollNumber: "24CSE0105",
          name: "Karthik Raja",
          semester: 5,
          cgpa: 5.94,
          sgpa: 5.5,
          arrears: 2,
          arrearSubjects: ["CS303 Computer Networks", "CS304 DAA"],
          supportPlan:
            "Parent-Teacher meeting scheduled; faculty mentor assigned.",
        },
      ],
      arrearAnalytics: {
        totalStudentsWithArrears: 22,
        singleArrearCount: 16,
        multipleArrearsCount: 6,
        repeatedArrearsCount: 3,
        subjectWiseArrearBreakdown: [
          {
            courseCode: "CS303",
            subject: "Computer Networks",
            arrearCount: 10,
          },
          {
            courseCode: "CS304",
            subject: "Design & Analysis of Algorithms",
            arrearCount: 7,
          },
          { courseCode: "CS302", subject: "Database Systems", arrearCount: 5 },
          {
            courseCode: "CS301",
            subject: "Advanced Data Structures",
            arrearCount: 4,
          },
        ],
      },
    };
  }

  private _mockApprovalsStore: HodApprovalItem[] = [
    {
      id: "appr-cse-001",
      title: "Faculty Medical Leave Application (3 Days)",
      category: "FACULTY",
      subCategory: "FACULTY_LEAVE",
      departmentId: "dept-cse",
      departmentName: "Computer Science & Engineering",
      submittedBy: "Dr. Priya Nair",
      submittedByRole: "Associate Professor",
      applicantId: "fac-002",
      submissionDate: "2026-11-18T10:15:00Z",
      urgency: "HIGH",
      status: "PENDING",
      description:
        "Medical leave required for acute throat infection and vocal cord rest as advised by physician.",
      details: {
        leaveType: "MEDICAL",
        startDate: "2026-11-20",
        endDate: "2026-11-22",
        totalDays: 3,
        substituteFaculty: "Prof. S. Ranganathan",
        classesRearranged: true,
        affectedCourses: ["CS302 Database Management Systems (Sec A & B)"],
      },
      attachments: [
        { name: "Medical_Certificate_Apollo.pdf", size: "1.2 MB", type: "PDF" },
      ],
      remarks: undefined,
      decidedBy: undefined,
      decisionDate: undefined,
      auditTrail: [
        {
          action: "SUBMITTED",
          by: "Dr. Priya Nair",
          timestamp: "2026-11-18T10:15:00Z",
          notes: "Alternate lecture coverage scheduled with Prof. Ranganathan.",
        },
      ],
    },
    {
      id: "appr-cse-002",
      title:
        "Faculty On-Duty (OD): IEEE International Conference Paper Presentation",
      category: "FACULTY",
      subCategory: "FACULTY_ON_DUTY",
      departmentId: "dept-cse",
      departmentName: "Computer Science & Engineering",
      submittedBy: "Prof. S. Ranganathan",
      submittedByRole: "Assistant Professor",
      applicantId: "fac-003",
      submissionDate: "2026-11-17T14:30:00Z",
      urgency: "MEDIUM",
      status: "PENDING",
      description:
        "Presenting accepted research paper 'SDN Orchestration in High-Throughput Campus Fabrics' at IEEE ICET 2026, IIT Madras.",
      details: {
        eventName:
          "IEEE International Conference on Emerging Technologies (ICET)",
        venue: "IIT Madras Research Park, Chennai",
        startDate: "2026-12-04",
        endDate: "2026-12-06",
        totalDays: 3,
        paperId: "IEEE-ICET-2026-9482",
        fundingRequested: "Rs. 8,500 (Registration & Travel)",
        alternateFaculty: "Dr. Rajesh Sharma",
      },
      attachments: [
        { name: "IEEE_Acceptance_Letter.pdf", size: "840 KB", type: "PDF" },
        { name: "Registration_Receipt.pdf", size: "410 KB", type: "PDF" },
      ],
      remarks: undefined,
      decidedBy: undefined,
      decisionDate: undefined,
      auditTrail: [
        {
          action: "SUBMITTED",
          by: "Prof. S. Ranganathan",
          timestamp: "2026-11-17T14:30:00Z",
          notes: "Recommended by Department Research & Development Committee.",
        },
      ],
    },
    {
      id: "appr-cse-003",
      title: "Timetable Class Swap: CS301 (DSA) & CS302 (DBMS) Period Exchange",
      category: "FACULTY",
      subCategory: "TIMETABLE_CHANGE",
      departmentId: "dept-cse",
      departmentName: "Computer Science & Engineering",
      submittedBy: "Dr. Rajesh Sharma",
      submittedByRole: "Professor & Dean",
      applicantId: "fac-001",
      submissionDate: "2026-11-16T16:00:00Z",
      urgency: "LOW",
      status: "APPROVED",
      description:
        "Exchange Wednesday Period 2 and Period 5 for 3rd Year Section A to accommodate visiting industry lab session.",
      details: {
        course1: "CS301 Data Structures (Period 2 -> Period 5)",
        course2: "CS302 Database Systems (Period 5 -> Period 2)",
        effectiveDate: "2026-11-25",
        classroom: "LH-201",
        consentObtained:
          "Both faculty members and student class representative agreed.",
      },
      attachments: [],
      remarks:
        "Approved. Academic timetable coordinator notified to update physical display board.",
      decidedBy: "Dr. K. S. Anand (HOD)",
      decisionDate: "2026-11-17T09:00:00Z",
      auditTrail: [
        {
          action: "SUBMITTED",
          by: "Dr. Rajesh Sharma",
          timestamp: "2026-11-16T16:00:00Z",
          notes: "Coordinated mutual swap.",
        },
        {
          action: "APPROVED",
          by: "Dr. K. S. Anand (HOD)",
          timestamp: "2026-11-17T09:00:00Z",
          notes: "Approved without curriculum disruption.",
        },
      ],
    },
    {
      id: "appr-cse-004",
      title: "Biometric Attendance Correction / Regularization",
      category: "FACULTY",
      subCategory: "ATTENDANCE_CORRECTION",
      departmentId: "dept-cse",
      departmentName: "Computer Science & Engineering",
      submittedBy: "Prof. S. Ranganathan",
      submittedByRole: "Assistant Professor",
      applicantId: "fac-003",
      submissionDate: "2026-11-15T11:20:00Z",
      urgency: "LOW",
      status: "APPROVED",
      description:
        "Punch-in biometric scanner timeout at Main Academic Block Entrance B on 14-Nov-2026.",
      details: {
        punchDate: "2026-11-14",
        recordedTime: "MISSING",
        actualArrival: "08:52 AM",
        witness: "Security Inspector P. Murugan",
        conductedClasses: "CS303 Lecture (09:00 - 09:50 AM)",
      },
      attachments: [],
      remarks: "Verified with daily gate register log.",
      decidedBy: "Dr. K. S. Anand (HOD)",
      decisionDate: "2026-11-15T14:00:00Z",
      auditTrail: [
        {
          action: "SUBMITTED",
          by: "Prof. S. Ranganathan",
          timestamp: "2026-11-15T11:20:00Z",
          notes: "Request submitted.",
        },
        {
          action: "APPROVED",
          by: "Dr. K. S. Anand (HOD)",
          timestamp: "2026-11-15T14:00:00Z",
          notes: "Verified against gate log.",
        },
      ],
    },
    {
      id: "appr-cse-005",
      title:
        "Student Academic On-Duty (OD): Smart India Hackathon (SIH 2026) Grand Finale",
      category: "STUDENT",
      subCategory: "STUDENT_ON_DUTY",
      departmentId: "dept-cse",
      departmentName: "Computer Science & Engineering",
      submittedBy: "Aarav Patel (24CSE0101)",
      submittedByRole: "3rd Year Student (Team Lead)",
      applicantId: "std-001",
      submissionDate: "2026-11-18T11:00:00Z",
      urgency: "HIGH",
      status: "PENDING",
      description:
        "Selected for Ministry of Education Smart India Hackathon Grand Finale at PIET Nodal Centre, Jaipur.",
      details: {
        teamName: "AlgoKnights",
        members: [
          "Aarav Patel (24CSE0101)",
          "Diya Sharma (24CSE0102)",
          "Rohan Iyer (24CSE0103)",
        ],
        dates: "2026-11-26 to 2026-11-30 (5 Days)",
        facultyMentor: "Dr. Rajesh Sharma",
        problemStatement: "AI-Powered Real-time Traffic Congestion Mitigation",
      },
      attachments: [
        {
          name: "SIH_2026_Finalist_Call_Letter.pdf",
          size: "950 KB",
          type: "PDF",
        },
      ],
      remarks: undefined,
      decidedBy: undefined,
      decisionDate: undefined,
      auditTrail: [
        {
          action: "SUBMITTED",
          by: "Aarav Patel",
          timestamp: "2026-11-18T11:00:00Z",
          notes: "Endorsed by Innovation & Incubation Cell.",
        },
      ],
    },
    {
      id: "appr-cse-006",
      title: "Student Medical Leave Exemption: Hospitalization Certificate",
      category: "STUDENT",
      subCategory: "STUDENT_LEAVE",
      departmentId: "dept-cse",
      departmentName: "Computer Science & Engineering",
      submittedBy: "Diya Sharma (24CSE0102)",
      submittedByRole: "3rd Year Student",
      applicantId: "std-002",
      submissionDate: "2026-11-17T09:45:00Z",
      urgency: "MEDIUM",
      status: "PENDING",
      description:
        "Absence exemption requested for 4 instructional days due to severe dengue fever hospitalization.",
      details: {
        hospital: "Kauvery Hospital, Trichy",
        admissionDate: "2026-11-10",
        dischargeDate: "2026-11-14",
        missedClasses: 18,
        currentAttendance: "72.4%",
        restoredAttendance: "78.2% upon medical approval",
      },
      attachments: [
        { name: "Medical_Discharge_Summary.pdf", size: "1.8 MB", type: "PDF" },
      ],
      remarks: undefined,
      decidedBy: undefined,
      decisionDate: undefined,
      auditTrail: [
        {
          action: "SUBMITTED",
          by: "Diya Sharma",
          timestamp: "2026-11-17T09:45:00Z",
          notes: "Parent Dr. Sharma verified over telephone by Proctor.",
        },
      ],
    },
    {
      id: "appr-cse-007",
      title: "Internal Assessment Mark Re-totalling / Discrepancy Review",
      category: "STUDENT",
      subCategory: "MARKS_CORRECTION",
      departmentId: "dept-cse",
      departmentName: "Computer Science & Engineering",
      submittedBy: "Rohan Iyer (24CSE0103)",
      submittedByRole: "3rd Year Student",
      applicantId: "std-003",
      submissionDate: "2026-11-16T15:10:00Z",
      urgency: "MEDIUM",
      status: "PENDING",
      description:
        "Question 4(b) in CS301 (Data Structures) IA-1 totaling error: 8 marks in answer booklet recorded as 4 in portal.",
      details: {
        courseCode: "CS301",
        courseName: "Data Structures & Core Algorithms",
        faculty: "Dr. Rajesh Sharma",
        originalMark: 84,
        requestedMark: 88,
        assessmentName: "Internal Assessment 1",
      },
      attachments: [
        {
          name: "Evaluated_Answer_Script_Scan.pdf",
          size: "2.4 MB",
          type: "PDF",
        },
      ],
      remarks: undefined,
      decidedBy: undefined,
      decisionDate: undefined,
      auditTrail: [
        {
          action: "SUBMITTED",
          by: "Rohan Iyer",
          timestamp: "2026-11-16T15:10:00Z",
          notes: "Faculty Dr. Sharma confirmed arithmetic omission.",
        },
      ],
    },
    {
      id: "appr-cse-008",
      title:
        "Department Technical Symposium: 'CYBERFEST 2026' Organization & Budget",
      category: "DEPARTMENT",
      subCategory: "EVENT_APPROVAL",
      departmentId: "dept-cse",
      departmentName: "Computer Science & Engineering",
      submittedBy: "Dr. K. S. Anand (HOD)",
      submittedByRole: "Head of Department",
      applicantId: "fac-001",
      submissionDate: "2026-11-15T12:00:00Z",
      urgency: "HIGH",
      status: "APPROVED",
      description:
        "Annual National Level Student Technical Symposium CYBERFEST 2026 featuring 8 technical events and hackathon.",
      details: {
        proposedDates: "2027-01-22 to 2027-01-23 (2 Days)",
        expectedParticipants: 650,
        totalBudget: "Rs. 1,80,000",
        sponsorshipSecured: "Rs. 95,000 (Zoho Corp & Cognizant)",
        collegeContribution: "Rs. 85,000",
        facultyCoordinators: ["Dr. Priya Nair", "Prof. S. Ranganathan"],
      },
      attachments: [
        { name: "Cyberfest_Event_Brochure.pdf", size: "3.1 MB", type: "PDF" },
        {
          name: "Detailed_Budget_Estimate.xlsx",
          size: "540 KB",
          type: "EXCEL",
        },
      ],
      remarks:
        "Approved by HOD and forwarded to Vice Principal for institutional finance release.",
      decidedBy: "Dr. K. S. Anand (HOD)",
      decisionDate: "2026-11-16T10:00:00Z",
      auditTrail: [
        {
          action: "SUBMITTED",
          by: "Dr. K. S. Anand",
          timestamp: "2026-11-15T12:00:00Z",
          notes: "Submitted with CSE Department Student Association committee.",
        },
        {
          action: "APPROVED",
          by: "Dr. K. S. Anand (HOD)",
          timestamp: "2026-11-16T10:00:00Z",
          notes: "Approved departmental charter.",
        },
      ],
    },
    {
      id: "appr-cse-009",
      title:
        "Laboratory Infrastructure Upgrade: NVIDIA RTX Workstations for AI Lab",
      category: "DEPARTMENT",
      subCategory: "LAB_REQUIREMENT",
      departmentId: "dept-cse",
      departmentName: "Computer Science & Engineering",
      submittedBy: "Dr. Rajesh Sharma (Lab In-charge)",
      submittedByRole: "Professor & Dean",
      applicantId: "fac-001",
      submissionDate: "2026-11-14T10:00:00Z",
      urgency: "CRITICAL",
      status: "PENDING",
      description:
        "Procurement of 12 NVIDIA RTX 4080 (16GB VRAM) compute workstations for AI/Deep Learning Laboratory.",
      details: {
        labName: "Advanced Computing & Artificial Intelligence Lab (Lab 4)",
        quantity: 12,
        estimatedCost: "Rs. 18,50,000",
        justification:
          "Required for Final Year B.Tech project training and NBA criteria 6 facility compliance.",
        preferredVendor: "Dell Commercial Enterprises India",
      },
      attachments: [
        { name: "Vendor_Quotes_Dell_HP.pdf", size: "2.1 MB", type: "PDF" },
      ],
      remarks: undefined,
      decidedBy: undefined,
      decisionDate: undefined,
      auditTrail: [
        {
          action: "SUBMITTED",
          by: "Dr. Rajesh Sharma",
          timestamp: "2026-11-14T10:00:00Z",
          notes: "Endorsed with NBA compliance documentation.",
        },
      ],
    },
  ];

  private getMockApprovals(
    category: string,
    statusFilter: string,
  ): HodApprovalsData {
    let items = this._mockApprovalsStore;
    if (category !== "ALL") {
      items = items.filter(
        (i) => i.category.toUpperCase() === category.toUpperCase(),
      );
    }
    if (statusFilter !== "ALL") {
      items = items.filter(
        (i) => i.status.toUpperCase() === statusFilter.toUpperCase(),
      );
    }

    return {
      department: "Computer Science & Engineering",
      stats: {
        totalRequests: this._mockApprovalsStore.length,
        pending: this._mockApprovalsStore.filter((i) => i.status === "PENDING")
          .length,
        approved: this._mockApprovalsStore.filter(
          (i) => i.status === "APPROVED",
        ).length,
        rejected: this._mockApprovalsStore.filter(
          (i) => i.status === "REJECTED",
        ).length,
        infoRequested: this._mockApprovalsStore.filter(
          (i) => i.status === "INFO_REQUESTED",
        ).length,
      },
      requests: items,
    };
  }

  // ---------------------------------------------------------------------------
  // Phase 3: Department Operations, Reports & Advanced Analytics Methods
  // ---------------------------------------------------------------------------

  async getDepartmentEvents(
    statusFilter: string = "ALL",
    categoryFilter: string = "ALL",
  ): Promise<ApiResponse<HodEventsData>> {
    try {
      const params = new URLSearchParams();
      if (statusFilter !== "ALL") params.append("status", statusFilter);
      if (categoryFilter !== "ALL") params.append("category", categoryFilter);
      const url = `/api/v1/hod/events${params.toString() ? `?${params.toString()}` : ""}`;
      const res = await apiFetch<any>(url);
      if (res && res.data) {
        return { success: true, data: res.data };
      }
    } catch {
      // Fallback
    }
    return {
      success: true,
      data: this.getMockEvents(statusFilter, categoryFilter),
    };
  }

  async createDepartmentEvent(
    payload: HodEventCreatePayload,
  ): Promise<ApiResponse<HodEventItem>> {
    try {
      const res = await apiFetch<any>("/api/v1/hod/events", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      if (res && res.data) {
        return { success: true, data: res.data };
      }
    } catch {
      // Fallback
    }
    const newEvent: HodEventItem = {
      id: `evt-cse-${Date.now().toString().slice(-3)}`,
      title: payload.title,
      description: payload.description,
      category: payload.category,
      startDate: payload.startDate,
      endDate: payload.endDate || payload.startDate,
      startTime: payload.startTime || "09:30 AM",
      endTime: payload.endTime || "04:30 PM",
      venue: payload.venue,
      organizer: "Department of Computer Science & Engineering",
      facultyCoordinator: payload.facultyCoordinator,
      studentCoordinator: payload.studentCoordinator || null,
      targetAudience: payload.targetAudience,
      expectedParticipants: payload.expectedParticipants,
      actualParticipants: 0,
      budget: payload.budget,
      status: "UPCOMING",
      approvalStatus: "APPROVED",
      report: null,
      attachments: [],
    };
    this._mockEventsStore.unshift(newEvent);
    return { success: true, data: newEvent };
  }

  async getDepartmentEventDetails(
    eventId: string,
  ): Promise<ApiResponse<{ department: string; event: HodEventItem }>> {
    try {
      const res = await apiFetch<any>(`/api/v1/hod/events/${eventId}`);
      if (res && res.data) {
        return { success: true, data: res.data };
      }
    } catch {
      // Fallback
    }
    const found =
      this._mockEventsStore.find((e) => e.id === eventId) ||
      this._mockEventsStore[0];
    return {
      success: true,
      data: {
        department: this.defaultDept,
        event: found,
      },
    };
  }

  async submitEventReport(
    eventId: string,
    payload: HodEventReportPayload,
  ): Promise<ApiResponse<HodEventItem>> {
    try {
      const res = await apiFetch<any>(`/api/v1/hod/events/${eventId}/report`, {
        method: "POST",
        body: JSON.stringify({
          actual_participants: payload.actualParticipants,
          outcomes: payload.outcomes,
          photos_count: payload.photosCount,
          report_url: payload.reportUrl,
          completion_remarks: payload.completionRemarks,
        }),
      });
      if (res && res.data) {
        return { success: true, data: res.data };
      }
    } catch {
      // Fallback
    }
    const target =
      this._mockEventsStore.find((e) => e.id === eventId) ||
      this._mockEventsStore[0];
    target.status = "COMPLETED";
    target.actualParticipants = payload.actualParticipants;
    target.report = {
      submittedAt: new Date().toISOString(),
      outcomes: payload.outcomes,
      photosCount: payload.photosCount,
      reportUrl: payload.reportUrl || `/reports/events/${eventId}-report.pdf`,
      remarks: payload.completionRemarks,
    };
    return { success: true, data: target };
  }

  async getPlacementOverview(): Promise<ApiResponse<HodPlacementOverview>> {
    try {
      const res = await apiFetch<any>("/api/v1/hod/placements/overview");
      if (res && res.data) {
        return { success: true, data: res.data };
      }
    } catch {
      // Fallback
    }
    return {
      success: true,
      data: this.getMockPlacementOverview(),
    };
  }

  async getPlacementStudents(
    statusFilter: string = "ALL",
    sectionFilter: string = "ALL",
    companyFilter: string = "ALL",
  ): Promise<ApiResponse<HodPlacementsData>> {
    try {
      const params = new URLSearchParams();
      if (statusFilter !== "ALL") params.append("status", statusFilter);
      if (sectionFilter !== "ALL") params.append("section", sectionFilter);
      if (companyFilter !== "ALL") params.append("company", companyFilter);
      const url = `/api/v1/hod/placements/students${params.toString() ? `?${params.toString()}` : ""}`;
      const res = await apiFetch<any>(url);
      if (res && res.data) {
        return { success: true, data: res.data };
      }
    } catch {
      // Fallback
    }
    return {
      success: true,
      data: this.getMockPlacementStudents(
        statusFilter,
        sectionFilter,
        companyFilter,
      ),
    };
  }

  async getReportCategories(): Promise<ApiResponse<HodReportCategoriesData>> {
    try {
      const res = await apiFetch<any>("/api/v1/hod/reports/categories");
      if (res && res.data) {
        return { success: true, data: res.data };
      }
    } catch {
      // Fallback
    }
    return {
      success: true,
      data: {
        department: this.defaultDept,
        categories: this.getMockReportCategories(),
      },
    };
  }

  async generateDepartmentReport(
    payload: HodReportGeneratePayload,
  ): Promise<ApiResponse<HodReportResult>> {
    try {
      const res = await apiFetch<any>("/api/v1/hod/reports/generate", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      if (res && res.data) {
        return { success: true, data: res.data };
      }
    } catch {
      // Fallback
    }
    return {
      success: true,
      data: this.getMockReportResult(payload),
    };
  }

  async getPerformanceAnalytics(): Promise<
    ApiResponse<HodPerformanceAnalyticsData>
  > {
    try {
      const res = await apiFetch<any>("/api/v1/hod/analytics/performance");
      if (res && res.data) {
        return { success: true, data: res.data };
      }
    } catch {
      // Fallback
    }
    return {
      success: true,
      data: this.getMockPerformanceAnalytics(),
    };
  }

  async getDepartmentAchievements(
    category: string = "ALL",
    recipientType: string = "ALL",
    academicYear: string = "ALL",
  ): Promise<ApiResponse<HodAchievementsData>> {
    try {
      const params = new URLSearchParams();
      if (category !== "ALL") params.append("category", category);
      if (recipientType !== "ALL")
        params.append("recipient_type", recipientType);
      if (academicYear !== "ALL") params.append("academic_year", academicYear);
      const url = `/api/v1/hod/achievements${params.toString() ? `?${params.toString()}` : ""}`;
      const res = await apiFetch<any>(url);
      if (res && res.data) {
        return { success: true, data: res.data };
      }
    } catch {
      // Fallback
    }
    return {
      success: true,
      data: this.getMockAchievements(category, recipientType, academicYear),
    };
  }

  async recordDepartmentAchievement(
    payload: HodAchievementCreatePayload,
  ): Promise<ApiResponse<HodAchievementItem>> {
    try {
      const res = await apiFetch<any>("/api/v1/hod/achievements", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      if (res && res.data) {
        return { success: true, data: res.data };
      }
    } catch {
      // Fallback
    }
    const newAch: HodAchievementItem = {
      id: `ach-cse-${Date.now().toString().slice(-3)}`,
      title: payload.title,
      description: payload.description,
      category: payload.category,
      recipientName: payload.recipientName,
      recipientType: payload.recipientType,
      recipientId: payload.recipientId,
      achievementDate: payload.achievementDate,
      academicYear: payload.academicYear,
      eventOrOrganization: payload.eventOrOrganization,
      certificateUrl:
        payload.certificateUrl || "/certificates/default-achievement.pdf",
      verificationStatus: "VERIFIED",
      verifiedBy: "Dr. K. S. Anand (HOD)",
    };
    this._mockAchievementsStore.unshift(newAch);
    return { success: true, data: newAch };
  }

  async getAccreditationOverview(): Promise<
    ApiResponse<HodAccreditationOverviewData>
  > {
    try {
      const res = await apiFetch<any>("/api/v1/hod/accreditation/overview");
      if (res && res.data) {
        return { success: true, data: res.data };
      }
    } catch {
      // Fallback
    }
    return {
      success: true,
      data: this.getMockAccreditationOverview(),
    };
  }

  async getAccreditationDocuments(
    criterion: string = "ALL",
    academicYear: string = "ALL",
    statusFilter: string = "ALL",
  ): Promise<ApiResponse<HodAccreditationDocumentsData>> {
    try {
      const params = new URLSearchParams();
      if (criterion !== "ALL") params.append("criterion", criterion);
      if (academicYear !== "ALL") params.append("academic_year", academicYear);
      if (statusFilter !== "ALL") params.append("status", statusFilter);
      const url = `/api/v1/hod/accreditation/documents${params.toString() ? `?${params.toString()}` : ""}`;
      const res = await apiFetch<any>(url);
      if (res && res.data) {
        return { success: true, data: res.data };
      }
    } catch {
      // Fallback
    }
    return {
      success: true,
      data: this.getMockAccreditationDocuments(
        criterion,
        academicYear,
        statusFilter,
      ),
    };
  }

  async uploadAccreditationDocument(
    payload: HodAccreditationDocumentUploadPayload,
  ): Promise<ApiResponse<HodAccreditationDocumentItem>> {
    try {
      const res = await apiFetch<any>("/api/v1/hod/accreditation/documents", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      if (res && res.data) {
        return { success: true, data: res.data };
      }
    } catch {
      // Fallback
    }
    const newDoc: HodAccreditationDocumentItem = {
      id: `doc-acc-${Date.now().toString().slice(-3)}`,
      title: payload.title,
      criterion: payload.criterion,
      academicYear: payload.academicYear,
      description: payload.description,
      fileName: payload.fileName,
      fileType: payload.fileType || "PDF",
      fileSizeKb: payload.fileSizeKb || 1200,
      uploadedBy: payload.uploadedBy || "Dr. K. S. Anand (HOD)",
      uploadedAt: new Date().toISOString(),
      reviewStatus: "UNDER_REVIEW",
      reviewer: "IQAC Lead Auditor",
      reviewRemarks: "Uploaded and queued for criteria verification.",
    };
    this._mockAccreditationDocsStore.unshift(newDoc);
    return { success: true, data: newDoc };
  }

  // Private Mock Data Stores & Generators for Phase 3
  private _mockEventsStore: HodEventItem[] = [
    {
      id: "evt-cse-001",
      title: "National Level Hackathon — CodeCraft 2026",
      description:
        "36-hour non-stop algorithmic innovation hackathon focusing on AI agents and sustainable computing solutions.",
      category: "Hackathon",
      startDate: "2026-10-15",
      endDate: "2026-10-16",
      startTime: "09:00 AM",
      endTime: "09:00 PM",
      venue: "Alan Turing Innovation Lab & CSE Systems Hub",
      organizer: "Department of Computer Science & Engineering",
      facultyCoordinator: "Dr. Priya Nair (Associate Professor)",
      studentCoordinator: "Arvind Kumar (714022104018)",
      targetAudience: "2nd, 3rd, 4th Year CSE & IT Students",
      expectedParticipants: 120,
      actualParticipants: 142,
      budget: 45000,
      status: "COMPLETED",
      approvalStatus: "APPROVED",
      report: {
        submittedAt: "2026-10-18T14:30:00Z",
        outcomes:
          "38 working prototypes developed; 4 projects shortlisted for institutional incubation seed grant.",
        photosCount: 24,
        reportUrl: "/reports/events/evt-cse-001-final-summary.pdf",
      },
      attachments: [
        { name: "CodeCraft2026_Brochure.pdf", size: "2.4 MB", type: "PDF" },
        { name: "Event_Report_Signed.pdf", size: "1.8 MB", type: "PDF" },
      ],
    },
    {
      id: "evt-cse-002",
      title: "Hands-on Workshop: Generative AI & LLM Deployment",
      description:
        "Deep-dive session covering transformer architectures, fine-tuning Llama models, and deploying via vLLM on Kubernetes.",
      category: "Workshop",
      startDate: "2026-11-28",
      endDate: "2026-11-29",
      startTime: "09:30 AM",
      endTime: "04:30 PM",
      venue: "Computing Centre Lab 3",
      organizer: "CSE AI Research Interest Group",
      facultyCoordinator: "Prof. S. Ranganathan (Assistant Professor)",
      studentCoordinator: "Sneha Murali (714022104085)",
      targetAudience: "3rd & 4th Year B.E. CSE",
      expectedParticipants: 80,
      actualParticipants: 0,
      budget: 25000,
      status: "UPCOMING",
      approvalStatus: "APPROVED",
      report: null,
      attachments: [
        { name: "GenAI_Workshop_Syllabus.pdf", size: "850 KB", type: "PDF" },
      ],
    },
    {
      id: "evt-cse-003",
      title: "Distinguished Guest Lecture: Scalable Microservices at Amazon",
      description:
        "Keynote and interactive AMA by industry leader on distributed event-driven systems and high-throughput AWS architectures.",
      category: "Guest Lecture",
      startDate: "2026-11-05",
      endDate: "2026-11-05",
      startTime: "02:00 PM",
      endTime: "04:30 PM",
      venue: "Dr. A.P.J. Abdul Kalam Memorial Auditorium",
      organizer: "CSE Department Industry-Institute Interaction Cell",
      facultyCoordinator: "Dr. M. Kavitha (Associate Professor)",
      studentCoordinator: "Karthik Raja (714021104042)",
      targetAudience: "All B.E. Computer Science & Engineering Students",
      expectedParticipants: 180,
      actualParticipants: 210,
      budget: 12000,
      status: "COMPLETED",
      approvalStatus: "APPROVED",
      report: {
        submittedAt: "2026-11-06T11:00:00Z",
        outcomes:
          "High engagement session; 3 internship referrals granted to department students by guest speaker.",
        photosCount: 18,
        reportUrl: "/reports/events/guest-lecture-amazon-2026.pdf",
      },
      attachments: [
        {
          name: "Speaker_Profile_Karthik_Amazon.pdf",
          size: "420 KB",
          type: "PDF",
        },
      ],
    },
    {
      id: "evt-cse-004",
      title: "Industrial Visit to Infosys Mysore Development Campus",
      description:
        "Full-day experiential tour of Global Education Centre, enterprise cloud operations, and corporate sustainability infrastructure.",
      category: "Industrial Visit",
      startDate: "2026-12-08",
      endDate: "2026-12-08",
      startTime: "06:00 AM",
      endTime: "09:00 PM",
      venue: "Infosys GEC & Tech Hub, Mysore",
      organizer: "Department of Computer Science & Engineering",
      facultyCoordinator: "Prof. T. Selvaraj (Assistant Professor)",
      studentCoordinator: "Pooja V. (714022104072)",
      targetAudience: "B.E. CSE 3rd Year (Sem 5) Students",
      expectedParticipants: 65,
      actualParticipants: 0,
      budget: 60000,
      status: "SCHEDULED",
      approvalStatus: "APPROVED",
      report: null,
      attachments: [
        {
          name: "Infosys_Visit_Permission_Letter.pdf",
          size: "1.1 MB",
          type: "PDF",
        },
      ],
    },
    {
      id: "evt-cse-005",
      title: "Faculty Development Program: Cloud-Native Microservices & DevOps",
      description:
        "One-week AICTE-ISTE sponsored national FDP covering Docker, Kubernetes, CI/CD automation, and observability.",
      category: "Faculty Development Program",
      startDate: "2026-09-10",
      endDate: "2026-09-15",
      startTime: "09:00 AM",
      endTime: "05:00 PM",
      venue: "Department Seminar Hall",
      organizer: "Department of Computer Science & Engineering",
      facultyCoordinator: "Dr. K. S. Anand (HOD)",
      studentCoordinator: null,
      targetAudience: "Faculty Members & Research Scholars",
      expectedParticipants: 40,
      actualParticipants: 44,
      budget: 35000,
      status: "COMPLETED",
      approvalStatus: "APPROVED",
      report: {
        submittedAt: "2026-09-17T09:30:00Z",
        outcomes:
          "All 44 participants certified; 8 joint research proposals formulated.",
        photosCount: 32,
        reportUrl: "/reports/events/fdp-cloud-native-report.pdf",
      },
      attachments: [
        {
          name: "FDP_Schedule_Resource_Persons.pdf",
          size: "1.5 MB",
          type: "PDF",
        },
      ],
    },
  ];

  private getMockEvents(
    statusFilter: string,
    categoryFilter: string,
  ): HodEventsData {
    let items = [...this._mockEventsStore];
    if (statusFilter !== "ALL")
      items = items.filter((e) => e.status === statusFilter);
    if (categoryFilter !== "ALL")
      items = items.filter(
        (e) => e.category.toLowerCase() === categoryFilter.toLowerCase(),
      );

    const completed = this._mockEventsStore.filter(
      (e) => e.status === "COMPLETED",
    ).length;
    const upcoming = this._mockEventsStore.filter(
      (e) => e.status === "UPCOMING" || e.status === "SCHEDULED",
    ).length;
    const totalParticipants = this._mockEventsStore.reduce(
      (acc, e) => acc + e.actualParticipants,
      0,
    );
    const totalBudget = this._mockEventsStore.reduce(
      (acc, e) => acc + e.budget,
      0,
    );

    return {
      department: this.defaultDept,
      events: items,
      summary: {
        totalEvents: this._mockEventsStore.length,
        upcomingEvents: upcoming,
        completedEvents: completed,
        totalParticipants,
        totalBudget,
      },
    };
  }

  private getMockPlacementOverview(): HodPlacementOverview {
    return {
      department: this.defaultDept,
      totalStudents: 720,
      finalYearStudents: 180,
      placementEligible: 172,
      studentsPlaced: 151,
      studentsUnplaced: 21,
      inTraining: 180,
      internshipParticipants: 138,
      placementPercentage: 87.8,
      highestPackageLpa: 24.5,
      averagePackageLpa: 6.8,
      medianPackageLpa: 5.5,
      topRecruiters: [
        {
          company: "Tata Consultancy Services (TCS)",
          offers: 34,
          tier: "Enterprise Service",
        },
        {
          company: "Infosys Technologies",
          offers: 28,
          tier: "Enterprise Service",
        },
        {
          company: "Cognizant Technology Solutions",
          offers: 22,
          tier: "Enterprise Service",
        },
        {
          company: "Zoho Corporation",
          offers: 19,
          tier: "Product Engineering",
        },
        {
          company: "Kaar Technologies",
          offers: 14,
          tier: "Enterprise Product",
        },
        {
          company: "Hexaware Technologies",
          offers: 16,
          tier: "Digital Solutions",
        },
        { company: "Wipro Limited", offers: 14, tier: "Enterprise Service" },
        {
          company: "Amazon Web Services (AWS)",
          offers: 4,
          tier: "Tier-1 Product",
        },
      ],
      packageRanges: [
        { range: "Above 15 LPA", count: 6, percentage: 4.0 },
        { range: "8 - 15 LPA", count: 28, percentage: 18.5 },
        { range: "5 - 8 LPA", count: 68, percentage: 45.0 },
        { range: "3.5 - 5 LPA", count: 49, percentage: 32.5 },
      ],
    };
  }

  private getMockPlacementStudents(
    statusFilter: string,
    sectionFilter: string,
    companyFilter: string,
  ): HodPlacementsData {
    const raw: HodStudentPlacementItem[] = [
      {
        registerNumber: "714021104001",
        name: "Abinaya Sundaram",
        academicYear: "2025-2026",
        year: "4th Year",
        section: "A",
        cgpa: 8.92,
        placementStatus: "PLACED",
        company: "Amazon Web Services (AWS)",
        role: "Cloud Support Associate",
        packageLpa: 24.5,
        selectionDate: "2026-09-12",
        internshipStatus: "INTERNSHIP_COMPLETED",
        internshipCompany: "Amazon India",
        internshipDuration: "6 Months",
        stipendMonthly: 60000,
      },
      {
        registerNumber: "714021104008",
        name: "Arvind Kumar",
        academicYear: "2025-2026",
        year: "4th Year",
        section: "A",
        cgpa: 9.15,
        placementStatus: "PLACED",
        company: "Zoho Corporation",
        role: "Member Technical Staff (MTS)",
        packageLpa: 12.0,
        selectionDate: "2026-08-25",
        internshipStatus: "INTERNSHIP_ONGOING",
        internshipCompany: "Zoho Corporation",
        internshipDuration: "6 Months",
        stipendMonthly: 25000,
      },
      {
        registerNumber: "714021104022",
        name: "Dinesh Babu",
        academicYear: "2025-2026",
        year: "4th Year",
        section: "A",
        cgpa: 7.84,
        placementStatus: "PLACED",
        company: "Tata Consultancy Services (TCS)",
        role: "System Engineer (Digital)",
        packageLpa: 7.2,
        selectionDate: "2026-09-04",
        internshipStatus: "NOT_STARTED",
        internshipCompany: null,
        internshipDuration: null,
        stipendMonthly: null,
      },
      {
        registerNumber: "714021104035",
        name: "Harini Venkat",
        academicYear: "2025-2026",
        year: "4th Year",
        section: "B",
        cgpa: 8.45,
        placementStatus: "PLACED",
        company: "Kaar Technologies",
        role: "SAP Consultant Associate",
        packageLpa: 8.5,
        selectionDate: "2026-09-20",
        internshipStatus: "INTERNSHIP_ONGOING",
        internshipCompany: "Kaar Technologies",
        internshipDuration: "4 Months",
        stipendMonthly: 18000,
      },
      {
        registerNumber: "714021104049",
        name: "Karthik Raja",
        academicYear: "2025-2026",
        year: "4th Year",
        section: "B",
        cgpa: 6.95,
        placementStatus: "INTERVIEW",
        company: "Hexaware Technologies",
        role: "Graduate Engineer Trainee",
        packageLpa: 5.0,
        selectionDate: null,
        internshipStatus: "TRAINING",
        internshipCompany: null,
        internshipDuration: null,
        stipendMonthly: null,
      },
      {
        registerNumber: "714021104058",
        name: "Monisha Rajesh",
        academicYear: "2025-2026",
        year: "4th Year",
        section: "B",
        cgpa: 8.78,
        placementStatus: "PLACED",
        company: "Cognizant Technology Solutions",
        role: "GenC Elevate Associate",
        packageLpa: 6.5,
        selectionDate: "2026-09-18",
        internshipStatus: "INTERNSHIP_COMPLETED",
        internshipCompany: "Cognizant",
        internshipDuration: "3 Months",
        stipendMonthly: 15000,
      },
      {
        registerNumber: "714021104064",
        name: "Naveen Prakash",
        academicYear: "2025-2026",
        year: "4th Year",
        section: "C",
        cgpa: 6.42,
        placementStatus: "ELIGIBLE",
        company: null,
        role: null,
        packageLpa: null,
        selectionDate: null,
        internshipStatus: "TRAINING",
        internshipCompany: null,
        internshipDuration: null,
        stipendMonthly: null,
      },
    ];

    let items = [...raw];
    if (statusFilter !== "ALL")
      items = items.filter((s) => s.placementStatus === statusFilter);
    if (sectionFilter !== "ALL")
      items = items.filter((s) => s.section === sectionFilter);
    if (companyFilter !== "ALL")
      items = items.filter(
        (s) =>
          s.company &&
          s.company.toLowerCase().includes(companyFilter.toLowerCase()),
      );

    return {
      department: this.defaultDept,
      total: items.length,
      students: items,
    };
  }

  private getMockReportCategories(): HodReportCategoryItem[] {
    return [
      {
        category: "STUDENT",
        title: "Student Reports",
        description:
          "Statutory enrollment rosters, year-wise distributions, and cohort demographics.",
        types: [
          {
            code: "STUDENT_STRENGTH",
            name: "Department Student Strength Summary",
            format: ["PDF", "CSV", "XLSX"],
          },
          {
            code: "STUDENT_YEARWISE",
            name: "Year-wise & Section-wise Distribution",
            format: ["PDF", "CSV"],
          },
          {
            code: "STUDENT_STATUS",
            name: "Active / Detained / Transferred Ledger",
            format: ["PDF", "CSV"],
          },
        ],
      },
      {
        category: "FACULTY",
        title: "Faculty Reports",
        description:
          "Faculty cadres, teaching workloads, attendance summaries, and subject allocations.",
        types: [
          {
            code: "FACULTY_STRENGTH",
            name: "Faculty Cadre & Qualification Report",
            format: ["PDF", "CSV"],
          },
          {
            code: "FACULTY_WORKLOAD",
            name: "Weekly Instructional Workload Audit",
            format: ["PDF", "CSV", "XLSX"],
          },
          {
            code: "FACULTY_ATTENDANCE",
            name: "Monthly Biometric Faculty Attendance",
            format: ["PDF", "CSV"],
          },
          {
            code: "FACULTY_ALLOCATION",
            name: "Subject & Laboratory Allocation Schedule",
            format: ["PDF", "CSV"],
          },
        ],
      },
      {
        category: "ATTENDANCE",
        title: "Attendance Reports",
        description:
          "Statutory biometric compliance, daily digests, and shortage radars (<75%).",
        types: [
          {
            code: "ATTENDANCE_DAILY",
            name: "Daily Department Attendance Digest",
            format: ["PDF", "CSV"],
          },
          {
            code: "ATTENDANCE_MONTHLY",
            name: "Monthly Cumulative Attendance Ledger",
            format: ["PDF", "CSV", "XLSX"],
          },
          {
            code: "ATTENDANCE_SHORTAGE",
            name: "Statutory Shortage Radar (<75% Risk)",
            format: ["PDF", "CSV"],
          },
          {
            code: "ATTENDANCE_SUBJECTWISE",
            name: "Subject-wise & Class-wise Attendance",
            format: ["PDF", "CSV"],
          },
        ],
      },
      {
        category: "ACADEMIC",
        title: "Academic Performance Reports",
        description:
          "Continuous Internal Assessment (CIA), semester examination results, and arrear diagnostics.",
        types: [
          {
            code: "ACADEMIC_IA_LEDGER",
            name: "Internal Assessment Marks Register",
            format: ["PDF", "CSV", "XLSX"],
          },
          {
            code: "ACADEMIC_RESULTS",
            name: "Semester Examination Comprehensive Results",
            format: ["PDF", "CSV", "XLSX"],
          },
          {
            code: "ACADEMIC_PASS_PERCENTAGE",
            name: "Subject-wise Pass Percentage & SGPA Analysis",
            format: ["PDF", "CSV"],
          },
          {
            code: "ACADEMIC_ARREAR",
            name: "Arrear Analysis & Remedial Action List",
            format: ["PDF", "CSV"],
          },
        ],
      },
      {
        category: "TIMETABLE",
        title: "Timetable Reports",
        description:
          "Class schedules, room allocations, faculty slots, and laboratory utilization matrices.",
        types: [
          {
            code: "TIMETABLE_MASTER",
            name: "Department Master Instructional Timetable",
            format: ["PDF", "CSV"],
          },
          {
            code: "TIMETABLE_FACULTY",
            name: "Individual Faculty Schedule Card",
            format: ["PDF"],
          },
          {
            code: "TIMETABLE_LABS",
            name: "Laboratory Infrastructure Utilization Schedule",
            format: ["PDF", "CSV"],
          },
        ],
      },
      {
        category: "PLACEMENT",
        title: "Placement & Internship Reports",
        description:
          "Recruitment statistics, package distribution, company recruitment breakdown, and internships.",
        types: [
          {
            code: "PLACEMENT_SUMMARY",
            name: "Annual Placement & Recruitment Statistics",
            format: ["PDF", "CSV", "XLSX"],
          },
          {
            code: "PLACEMENT_COMPANYWISE",
            name: "Company-wise Offers & CTC Breakdown",
            format: ["PDF", "CSV"],
          },
          {
            code: "PLACEMENT_INTERNSHIP",
            name: "Paid Internship & Stipend Compliance Roster",
            format: ["PDF", "CSV"],
          },
        ],
      },
      {
        category: "EVENTS",
        title: "Events & Activities Reports",
        description:
          "Department symposia, hackathons, workshops, industrial visits, and participant engagement.",
        types: [
          {
            code: "EVENTS_ANNUAL",
            name: "Annual Co-Curricular & Extracurricular Report",
            format: ["PDF", "CSV", "XLSX"],
          },
          {
            code: "EVENTS_WORKSHOPS",
            name: "Technical Workshops & Seminars Summary",
            format: ["PDF", "CSV"],
          },
          {
            code: "EVENTS_IV",
            name: "Industrial Visit & Experiential Learning Report",
            format: ["PDF", "CSV"],
          },
        ],
      },
    ];
  }

  private getMockReportResult(
    payload: HodReportGeneratePayload,
  ): HodReportResult {
    let columns = [
      { key: "indicator", label: "Key Performance Dimension" },
      { key: "baseline", label: "Target" },
      { key: "achieved", label: "Achieved Value" },
      { key: "variance", label: "Variance" },
      { key: "status", label: "Status" },
    ];
    let rows: Record<string, any>[] = [
      {
        indicator: "Overall Department Pass Percentage",
        baseline: "85.0%",
        achieved: "90.8%",
        variance: "+5.8%",
        status: "EXCEEDS_TARGET",
      },
      {
        indicator: "Graduating Student Placement Rate",
        baseline: "80.0%",
        achieved: "87.8%",
        variance: "+7.8%",
        status: "EXCEEDS_TARGET",
      },
      {
        indicator: "Paid Internship Conversion Rate",
        baseline: "65.0%",
        achieved: "76.7%",
        variance: "+11.7%",
        status: "EXCEEDS_TARGET",
      },
      {
        indicator: "Syllabus Delivery Completion Rate",
        baseline: "80.0%",
        achieved: "82.8%",
        variance: "+2.8%",
        status: "COMPLIANT",
      },
      {
        indicator: "Statutory Attendance Shortage Risk",
        baseline: "<5.0%",
        achieved: "4.4%",
        variance: "-0.6%",
        status: "OPTIMAL",
      },
    ];

    if (payload.category === "STUDENT") {
      columns = [
        { key: "year", label: "Academic Year" },
        { key: "section", label: "Section" },
        { key: "enrolled", label: "Enrolled Count" },
        { key: "male", label: "Male" },
        { key: "female", label: "Female" },
        { key: "status", label: "Compliance Status" },
      ];
      rows = [
        {
          year: "1st Year (2025-2029)",
          section: "A",
          enrolled: 60,
          male: 34,
          female: 26,
          status: "VERIFIED",
        },
        {
          year: "1st Year (2025-2029)",
          section: "B",
          enrolled: 60,
          male: 32,
          female: 28,
          status: "VERIFIED",
        },
        {
          year: "1st Year (2025-2029)",
          section: "C",
          enrolled: 60,
          male: 35,
          female: 25,
          status: "VERIFIED",
        },
        {
          year: "2nd Year (2024-2028)",
          section: "A",
          enrolled: 60,
          male: 31,
          female: 29,
          status: "VERIFIED",
        },
        {
          year: "2nd Year (2024-2028)",
          section: "B",
          enrolled: 60,
          male: 33,
          female: 27,
          status: "VERIFIED",
        },
        {
          year: "2nd Year (2024-2028)",
          section: "C",
          enrolled: 60,
          male: 36,
          female: 24,
          status: "VERIFIED",
        },
        {
          year: "3rd Year (2023-2027)",
          section: "A",
          enrolled: 60,
          male: 32,
          female: 28,
          status: "VERIFIED",
        },
        {
          year: "3rd Year (2023-2027)",
          section: "B",
          enrolled: 60,
          male: 30,
          female: 30,
          status: "VERIFIED",
        },
        {
          year: "3rd Year (2023-2027)",
          section: "C",
          enrolled: 60,
          male: 35,
          female: 25,
          status: "VERIFIED",
        },
        {
          year: "4th Year (2022-2026)",
          section: "A",
          enrolled: 60,
          male: 33,
          female: 27,
          status: "VERIFIED",
        },
        {
          year: "4th Year (2022-2026)",
          section: "B",
          enrolled: 60,
          male: 34,
          female: 26,
          status: "VERIFIED",
        },
        {
          year: "4th Year (2022-2026)",
          section: "C",
          enrolled: 60,
          male: 31,
          female: 29,
          status: "VERIFIED",
        },
      ];
    } else if (payload.category === "FACULTY") {
      columns = [
        { key: "emp_code", label: "Employee Code" },
        { key: "name", label: "Faculty Name" },
        { key: "designation", label: "Designation" },
        { key: "load_hrs", label: "Weekly Workload (Hrs)" },
        { key: "subjects", label: "Assigned Courses" },
        { key: "attendance_pct", label: "Biometric Compliance" },
      ];
      rows = [
        {
          emp_code: "FAC-CSE-001",
          name: "Dr. K. S. Anand",
          designation: "Professor & HOD",
          load_hrs: 14,
          subjects: "CS301 (DSA)",
          attendance_pct: "98.5%",
        },
        {
          emp_code: "FAC-CSE-002",
          name: "Dr. Priya Nair",
          designation: "Associate Professor",
          load_hrs: 18,
          subjects: "CS302 (DBMS)",
          attendance_pct: "96.2%",
        },
        {
          emp_code: "FAC-CSE-003",
          name: "Prof. S. Ranganathan",
          designation: "Assistant Professor",
          load_hrs: 20,
          subjects: "CS303 (OS), CS306 (Lab)",
          attendance_pct: "97.4%",
        },
        {
          emp_code: "FAC-CSE-004",
          name: "Dr. M. Kavitha",
          designation: "Associate Professor",
          load_hrs: 16,
          subjects: "CS304 (Networks)",
          attendance_pct: "95.8%",
        },
        {
          emp_code: "FAC-CSE-005",
          name: "Prof. T. Selvaraj",
          designation: "Assistant Professor",
          load_hrs: 21,
          subjects: "CS305 (TOC), CS307 (Lab)",
          attendance_pct: "94.6%",
        },
      ];
    }

    return {
      reportId: `rep-${Date.now().toString().slice(-6)}`,
      title: `Department of Computer Science & Engineering — ${payload.reportType || "Statutory Report"}`,
      category: payload.category,
      academicYear: payload.academicYear,
      generatedBy: "Dr. K. S. Anand (HOD)",
      generatedAt: new Date().toISOString(),
      filtersApplied: {
        semester: payload.semester || "ODD",
        section: payload.section || "ALL",
        startDate: payload.startDate,
        endDate: payload.endDate,
      },
      columns,
      rows,
      totalRecords: rows.length,
    };
  }

  private getMockPerformanceAnalytics(): HodPerformanceAnalyticsData {
    return {
      department: this.defaultDept,
      academicTrends: {
        semesterPassRates: [
          { semester: "Sem 1", passRate: 88.4, appeared: 180, passed: 159 },
          { semester: "Sem 2", passRate: 89.1, appeared: 180, passed: 160 },
          { semester: "Sem 3", passRate: 91.2, appeared: 180, passed: 164 },
          { semester: "Sem 4", passRate: 90.5, appeared: 180, passed: 163 },
          { semester: "Sem 5", passRate: 93.1, appeared: 180, passed: 168 },
          { semester: "Sem 6", passRate: 90.8, appeared: 180, passed: 163 },
        ],
        yearWisePerformance: [
          {
            year: "1st Year",
            passPercentage: 88.7,
            averageCgpa: 7.42,
            toppersCount: 22,
          },
          {
            year: "2nd Year",
            passPercentage: 90.8,
            averageCgpa: 7.68,
            toppersCount: 26,
          },
          {
            year: "3rd Year",
            passPercentage: 92.4,
            averageCgpa: 7.91,
            toppersCount: 31,
          },
          {
            year: "4th Year",
            passPercentage: 94.1,
            averageCgpa: 8.15,
            toppersCount: 38,
          },
        ],
        arrearResolutionVelocity: [
          { stage: "Cleared in 1st Attempt", percentage: 78.5, count: 44 },
          { stage: "Cleared in 2nd Attempt", percentage: 15.5, count: 9 },
          { stage: "Persistent Backlog", percentage: 6.0, count: 3 },
        ],
        attendancePerformanceCorrelation: [
          { attendanceTier: "Above 85%", averageCgpa: 8.42, students: 490 },
          { attendanceTier: "75% - 85%", averageCgpa: 7.35, students: 198 },
          { attendanceTier: "Below 75%", averageCgpa: 6.12, students: 32 },
        ],
      },
      facultyAnalytics: {
        totalFaculty: 28,
        cadreDistribution: [
          { cadre: "Professors", count: 4, percentage: 14.3 },
          { cadre: "Associate Professors", count: 8, percentage: 28.6 },
          { cadre: "Assistant Professors", count: 16, percentage: 57.1 },
        ],
        workloadCompliance: [
          { range: "14 - 18 Hours (Optimal)", count: 22, percentage: 78.6 },
          { range: "19 - 21 Hours (Heavy)", count: 5, percentage: 17.8 },
          { range: "Under 14 Hours (Light)", count: 1, percentage: 3.6 },
        ],
        lessonPlanDeliveryAverage: 82.8,
        averageMonthlyAttendance: 96.2,
      },
      departmentGrowth: {
        yearlyIntake: [
          { academicYear: "2022-2023", enrolled: 160, graduated: 152 },
          { academicYear: "2023-2024", enrolled: 170, graduated: 162 },
          { academicYear: "2024-2025", enrolled: 180, graduated: 174 },
          { academicYear: "2025-2026", enrolled: 180, graduated: 151 },
        ],
        placementRateGrowth: [
          { year: "2023", rate: 81.2 },
          { year: "2024", rate: 84.5 },
          { year: "2025", rate: 86.0 },
          { year: "2026", rate: 87.8 },
        ],
        researchPapersPublished: 34,
        patentsFiled: 7,
        fundedProjectsAmountLakhs: 42.5,
      },
    };
  }

  private _mockAchievementsStore: HodAchievementItem[] = [
    {
      id: "ach-cse-001",
      title: "First Prize — Smart India Hackathon (SIH 2025)",
      description:
        "Student team 'ByteCrafters' designed an automated AI emergency dispatch triage system and secured national 1st place with ₹1,00,000 cash grant.",
      category: "HACKATHON",
      recipientName: "Arvind Kumar & Team",
      recipientType: "STUDENT",
      recipientId: "714022104018",
      achievementDate: "2025-12-22",
      academicYear: "2025-2026",
      eventOrOrganization: "Ministry of Education & AICTE",
      certificateUrl: "/certificates/sih-2025-first-prize.pdf",
      verificationStatus: "VERIFIED",
      verifiedBy: "Dr. K. S. Anand (HOD)",
    },
    {
      id: "ach-cse-002",
      title:
        "Best Research Paper Award — IEEE International Conference on AI & Robotics",
      description:
        "Paper titled 'Energy-Efficient Resource Allocation in Heterogeneous Edge Fog Networks' awarded Best Technical Paper in Track 1.",
      category: "RESEARCH",
      recipientName: "Dr. Priya Nair",
      recipientType: "FACULTY",
      recipientId: "fac-002",
      achievementDate: "2026-01-14",
      academicYear: "2025-2026",
      eventOrOrganization: "IEEE Computer Society",
      certificateUrl: "/certificates/ieee-best-paper-priya.pdf",
      verificationStatus: "VERIFIED",
      verifiedBy: "Dr. K. S. Anand (HOD)",
    },
    {
      id: "ach-cse-003",
      title:
        "Patent Published: Real-Time Crop Disease Identification using Edge Vision",
      description:
        "Indian Patent Application No. 202641009872 published in the official Patent Office Journal.",
      category: "INNOVATION",
      recipientName: "Prof. S. Ranganathan & Dr. K. S. Anand",
      recipientType: "FACULTY",
      recipientId: "fac-003",
      achievementDate: "2026-02-18",
      academicYear: "2025-2026",
      eventOrOrganization:
        "Intellectual Property India (Controller General of Patents)",
      certificateUrl: "/certificates/patent-publication-journal.pdf",
      verificationStatus: "VERIFIED",
      verifiedBy: "Dr. K. S. Anand (HOD)",
    },
    {
      id: "ach-cse-004",
      title: "Top 1% Global Rank — Google Kick Start Round G",
      description:
        "Solved 4/4 advanced algorithmic problems under timed constraints, securing Global Rank 84 out of 11,200 international competitive programmers.",
      category: "TECHNICAL_COMPETITION",
      recipientName: "Rahul Sharma",
      recipientType: "STUDENT",
      recipientId: "714022104079",
      achievementDate: "2025-10-30",
      academicYear: "2025-2026",
      eventOrOrganization: "Google Developers",
      certificateUrl: "/certificates/kickstart-rank-84.pdf",
      verificationStatus: "VERIFIED",
      verifiedBy: "Dr. K. S. Anand (HOD)",
    },
    {
      id: "ach-cse-005",
      title: "AWS Certified Solutions Architect — Professional",
      description:
        "Demonstrated advanced technical expertise in designing enterprise-grade, fault-tolerant distributed solutions on AWS.",
      category: "CERTIFICATION",
      recipientName: "Dr. M. Kavitha",
      recipientType: "FACULTY",
      recipientId: "fac-004",
      achievementDate: "2026-03-05",
      academicYear: "2025-2026",
      eventOrOrganization: "Amazon Web Services",
      certificateUrl: "/certificates/aws-sap-cert.pdf",
      verificationStatus: "VERIFIED",
      verifiedBy: "Dr. K. S. Anand (HOD)",
    },
    {
      id: "ach-cse-006",
      title: "Anna University Inter-Zonal Badminton Championship — Gold Medal",
      description:
        "Represented collegiate badminton team and secured gold medal in women singles tournament.",
      category: "SPORTS",
      recipientName: "Divya R.",
      recipientType: "STUDENT",
      recipientId: "714023104031",
      achievementDate: "2026-02-04",
      academicYear: "2025-2026",
      eventOrOrganization: "Anna University Sports Board",
      certificateUrl: "/certificates/badminton-gold.pdf",
      verificationStatus: "VERIFIED",
      verifiedBy: "Dr. K. S. Anand (HOD)",
    },
  ];

  private getMockAchievements(
    category: string,
    recipientType: string,
    academicYear: string,
  ): HodAchievementsData {
    let items = [...this._mockAchievementsStore];
    if (category !== "ALL")
      items = items.filter((a) => a.category === category);
    if (recipientType !== "ALL")
      items = items.filter((a) => a.recipientType === recipientType);
    if (academicYear !== "ALL")
      items = items.filter((a) => a.academicYear === academicYear);

    const studentCount = this._mockAchievementsStore.filter(
      (a) => a.recipientType === "STUDENT",
    ).length;
    const facultyCount = this._mockAchievementsStore.filter(
      (a) => a.recipientType === "FACULTY",
    ).length;

    return {
      department: this.defaultDept,
      achievements: items,
      summary: {
        totalAchievements: this._mockAchievementsStore.length,
        studentAchievements: studentCount,
        facultyAchievements: facultyCount,
        researchPapers: 34,
        patents: 7,
        hackathonWins: 12,
      },
    };
  }

  private _mockAccreditationDocsStore: HodAccreditationDocumentItem[] = [
    {
      id: "doc-acc-001",
      title: "Department Vision, Mission, PEO and PSO Statutory Documentation",
      criterion: "CRITERION_1",
      academicYear: "2025-2026",
      description:
        "Stakeholder consultation minutes, PEO revision approvals, and governing body endorsement.",
      fileName: "CSE_PEO_PSO_Endorsement_2026.pdf",
      fileType: "PDF",
      fileSizeKb: 1420,
      uploadedBy: "Dr. K. S. Anand (HOD)",
      uploadedAt: "2026-08-10T11:00:00Z",
      reviewStatus: "VERIFIED",
      reviewer: "Internal Quality Assurance Cell (IQAC)",
      reviewRemarks: "Fully compliant with NBA Tier-1 guidelines.",
    },
    {
      id: "doc-acc-002",
      title: "Curriculum Scheme R-2026 Syllabus & Regulation Document",
      criterion: "CRITERION_2",
      academicYear: "2025-2026",
      description:
        "Board of Studies (BoS) approved syllabus copies for Semesters 1 through 8.",
      fileName: "R2026_CSE_Curriculum_Regulation.pdf",
      fileType: "PDF",
      fileSizeKb: 4820,
      uploadedBy: "Dr. Priya Nair",
      uploadedAt: "2026-08-15T14:20:00Z",
      reviewStatus: "VERIFIED",
      reviewer: "IQAC Lead Auditor",
      reviewRemarks: "Approved by Academic Council.",
    },
    {
      id: "doc-acc-003",
      title:
        "Direct & Indirect CO-PO Attainment Calculation Sheets (2021-2025 Batch)",
      criterion: "CRITERION_3",
      academicYear: "2025-2026",
      description:
        "Continuous assessment data, end-semester grades, and exit survey correlation matrix.",
      fileName: "CO_PO_Attainment_Batch2025.xlsx",
      fileType: "XLSX",
      fileSizeKb: 2250,
      uploadedBy: "Prof. S. Ranganathan",
      uploadedAt: "2026-10-02T16:45:00Z",
      reviewStatus: "UNDER_REVIEW",
      reviewer: "IQAC Technical Committee",
      reviewRemarks: "Verification of indirect survey weights in progress.",
    },
    {
      id: "doc-acc-004",
      title: "Placement & Higher Studies Statutory Evidence Dossier",
      criterion: "CRITERION_4",
      academicYear: "2025-2026",
      description:
        "Offer letters, company recruitment summaries, and higher studies admission confirmations.",
      fileName: "CSE_Placement_Verification_Dossier.pdf",
      fileType: "PDF",
      fileSizeKb: 8940,
      uploadedBy: "Dr. M. Kavitha",
      uploadedAt: "2026-10-25T10:30:00Z",
      reviewStatus: "VERIFIED",
      reviewer: "Principal & IQAC Director",
      reviewRemarks:
        "100% offer letters cross-verified with institutional records.",
    },
    {
      id: "doc-acc-005",
      title: "Faculty Retention, PhD Cadre Ratio, and Workload Audit Report",
      criterion: "CRITERION_5",
      academicYear: "2025-2026",
      description:
        "Cadre ratio compliance, SFR calculation (1:15), and faculty publication citations report.",
      fileName: "Faculty_SFR_Cadre_Audit_2026.pdf",
      fileType: "PDF",
      fileSizeKb: 1820,
      uploadedBy: "Dr. K. S. Anand (HOD)",
      uploadedAt: "2026-11-01T09:15:00Z",
      reviewStatus: "VERIFIED",
      reviewer: "IQAC Lead Auditor",
      reviewRemarks: "Cadre ratio 1:2:4 and SFR 1:15 satisfied.",
    },
  ];

  private getMockAccreditationOverview(): HodAccreditationOverviewData {
    return {
      department: this.defaultDept,
      framework: "National Board of Accreditation (NBA) Tier-1 Autonomous",
      programName: "B.E. Computer Science & Engineering",
      academicYear: "2025-2026",
      readinessPercentage: 93.0,
      criteria: [
        {
          criterionId: "CRITERION_1",
          name: "Criterion 1: Vision, Mission & Program Educational Objectives (PEOs)",
          weightage: 50,
          completionPercentage: 100.0,
          documentsCount: 14,
          verifiedCount: 14,
          status: "COMPLETED",
        },
        {
          criterionId: "CRITERION_2",
          name: "Criterion 2: Program Curriculum & Teaching-Learning Processes",
          weightage: 100,
          completionPercentage: 92.0,
          documentsCount: 30,
          verifiedCount: 28,
          status: "IN_PROGRESS",
        },
        {
          criterionId: "CRITERION_3",
          name: "Criterion 3: Course Outcomes (CO) & Program Outcomes (PO) Attainment",
          weightage: 175,
          completionPercentage: 88.0,
          documentsCount: 25,
          verifiedCount: 22,
          status: "IN_PROGRESS",
        },
        {
          criterionId: "CRITERION_4",
          name: "Criterion 4: Students' Performance & Placement Progression",
          weightage: 100,
          completionPercentage: 95.0,
          documentsCount: 35,
          verifiedCount: 35,
          status: "COMPLETED",
        },
        {
          criterionId: "CRITERION_5",
          name: "Criterion 5: Faculty Information, Workloads & Contributions",
          weightage: 200,
          completionPercentage: 90.0,
          documentsCount: 28,
          verifiedCount: 25,
          status: "IN_PROGRESS",
        },
      ],
      documents: this._mockAccreditationDocsStore,
    };
  }

  private getMockAccreditationDocuments(
    criterion: string,
    academicYear: string,
    statusFilter: string,
  ): HodAccreditationDocumentsData {
    let items = [...this._mockAccreditationDocsStore];
    if (criterion !== "ALL")
      items = items.filter((d) => d.criterion === criterion);
    if (academicYear !== "ALL")
      items = items.filter((d) => d.academicYear === academicYear);
    if (statusFilter !== "ALL")
      items = items.filter((d) => d.reviewStatus === statusFilter);

    return {
      department: this.defaultDept,
      totalDocuments: items.length,
      documents: items,
    };
  }
}

export const hodService = new HodService();

// -----------------------------------------------------------------------------
// Phase 2 Type Definitions
// -----------------------------------------------------------------------------

export interface HodSubjectItem {
  id: string;
  code: string;
  name: string;
  shortName: string;
  credits: number;
  type: string;
  category: string;
  semester: number;
  regulation: string;
  academicYear: string;
  assignedFaculty: string;
  assignedFacultyId: string;
  sections: string[];
  syllabusCompletion: number;
  coCount: number;
  poMapped: number;
}

export interface HodCurriculumData {
  department: string;
  regulation: string;
  totalCredits: number;
  subjects: HodSubjectItem[];
  allocationSummary: {
    totalSubjects: number;
    allocatedSubjects: number;
    unallocatedSubjects: number;
    allocationConflicts: number;
  };
  curriculumScheme: {
    program: string;
    academicYear: string;
    totalSemesters: number;
    averageSyllabusCompletion: number;
  };
  courseOutcomesSample: {
    coCode: string;
    description: string;
    bloomLevel: string;
  }[];
  coPoMatrix: Record<string, any>[];
}

export interface HodLessonPlanTopic {
  topic: string;
  completed: boolean;
}

export interface HodLessonPlanUnit {
  unitNumber: number;
  title: string;
  plannedHours: number;
  completedHours: number;
  status: "COMPLETED" | "IN_PROGRESS" | "NOT_STARTED";
  completionPercentage: number;
  topics: HodLessonPlanTopic[];
}

export interface HodLessonPlanItem {
  id: string;
  courseCode: string;
  courseName: string;
  section: string;
  facultyName: string;
  facultyDesignation: string;
  totalPlannedHours: number;
  totalCompletedHours: number;
  overallCompletionPercentage: number;
  status: "COMPLETED" | "IN_PROGRESS" | "NOT_STARTED";
  pendingPlansCount: number;
  units: HodLessonPlanUnit[];
}

export interface HodLessonPlansData {
  department: string;
  lessonPlans: HodLessonPlanItem[];
  summary: {
    totalMonitoredCourses: number;
    averageSyllabusCompletion: number;
    coursesBehindSchedule: number;
    pendingLessonPlans: number;
  };
}

export interface HodExamTerm {
  id: string;
  name: string;
  academicYear: string;
  status: string;
  startDate: string;
  endDate: string;
  marksSubmissionDeadline: string;
  submissionStatus: string;
}

export interface HodExamSchedule {
  id: string;
  date: string;
  time: string;
  duration: string;
  courseCode: string;
  courseName: string;
  semester: number;
  section: string;
  examType: string;
  hallNumber: string;
  chiefInvigilator: string;
  totalCandidates: number;
}

export interface HodExamSubmissionProgress {
  courseCode: string;
  courseName: string;
  facultyName: string;
  ia1Status: string;
  ia2Status: string;
  modelStatus: string;
  pendingCount: number;
  missingMarks: number;
}

export interface HodExaminationsData {
  department: string;
  terms: HodExamTerm[];
  schedules: HodExamSchedule[];
  submissionProgress: HodExamSubmissionProgress[];
  summary: {
    totalScheduledExams: number;
    ongoingExams: number;
    completedTerms: number;
    missingMarksTotal: number;
    submissionComplianceRate: number;
  };
}

export interface HodInternalMarkRecord {
  id: string;
  studentId: string;
  studentName: string;
  rollNumber: string;
  semester: number;
  section: string;
  courseCode: string;
  courseName: string;
  facultyName: string;
  ia1: number;
  ia2: number;
  ia3Model: number;
  assignments: number;
  attendanceScore: number;
  totalInternal: number;
  maxInternal: number;
  percentage: number;
  status: "ENTERED" | "VERIFIED" | "FINALIZED";
  requiresAttention: boolean;
}

export interface HodInternalMarksData {
  department: string;
  records: HodInternalMarkRecord[];
  attentionList: HodInternalMarkRecord[];
  summary: {
    totalRecords: number;
    averagePercentage: number;
    studentsRequiringAttention: number;
    missingMarksCount: number;
  };
}

export interface HodSemesterResultsData {
  department: string;
  overview: {
    academicYear: string;
    examination: string;
    totalStudentsAppeared: number;
    totalStudentsPassed: number;
    totalStudentsFailed: number;
    passPercentage: number;
    previousSemesterPassPercentage: number;
    percentageDelta: string;
  };
  subjectResults: {
    courseCode: string;
    courseName: string;
    faculty: string;
    appeared: number;
    passed: number;
    failed: number;
    passPercentage: number;
    averageGradePoint: number;
  }[];
  toppers: {
    rank: number;
    rollNumber: string;
    name: string;
    semester: number;
    cgpa: number;
    sgpa: number;
    totalCredits: number;
    arrears: number;
    status: string;
  }[];
  studentsNeedingSupport: {
    rollNumber: string;
    name: string;
    semester: number;
    cgpa: number;
    sgpa: number;
    arrears: number;
    arrearSubjects: string[];
    supportPlan: string;
  }[];
  arrearAnalytics: {
    totalStudentsWithArrears: number;
    singleArrearCount: number;
    multipleArrearsCount: number;
    repeatedArrearsCount: number;
    subjectWiseArrearBreakdown: {
      courseCode: string;
      subject: string;
      arrearCount: number;
    }[];
  };
}

export interface HodApprovalAttachment {
  name: string;
  size: string;
  type: string;
}

export interface HodApprovalAudit {
  action: string;
  by: string;
  timestamp: string;
  notes: string;
}

export interface HodApprovalItem {
  id: string;
  title: string;
  category: "FACULTY" | "STUDENT" | "DEPARTMENT";
  subCategory: string;
  departmentId: string;
  departmentName: string;
  submittedBy: string;
  submittedByRole: string;
  applicantId: string;
  submissionDate: string;
  urgency: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  status: "PENDING" | "APPROVED" | "REJECTED" | "INFO_REQUESTED";
  description: string;
  details: Record<string, any>;
  attachments: HodApprovalAttachment[];
  remarks?: string;
  decidedBy?: string;
  decisionDate?: string;
  auditTrail: HodApprovalAudit[];
}

export interface HodApprovalsData {
  department: string;
  stats: {
    totalRequests: number;
    pending: number;
    approved: number;
    rejected: number;
    infoRequested: number;
  };
  requests: HodApprovalItem[];
}

// -----------------------------------------------------------------------------
// Phase 3 Type Definitions: Operations, Reports & Advanced Analytics
// -----------------------------------------------------------------------------

export interface HodEventReport {
  submittedAt: string;
  outcomes: string;
  photosCount: number;
  reportUrl: string;
  remarks?: string;
}

export interface HodEventAttachment {
  name: string;
  size: string;
  type: string;
}

export interface HodEventItem {
  id: string;
  title: string;
  description: string;
  category: string;
  startDate: string;
  endDate?: string;
  startTime?: string;
  endTime?: string;
  venue: string;
  organizer: string;
  facultyCoordinator: string;
  studentCoordinator?: string | null;
  targetAudience: string;
  expectedParticipants: number;
  actualParticipants: number;
  budget: number;
  status: "UPCOMING" | "SCHEDULED" | "ONGOING" | "COMPLETED" | "CANCELLED";
  approvalStatus: "APPROVED" | "PENDING" | "REJECTED";
  report?: HodEventReport | null;
  attachments: HodEventAttachment[];
}

export interface HodEventCreatePayload {
  title: string;
  description: string;
  category: string;
  startDate: string;
  endDate?: string;
  startTime?: string;
  endTime?: string;
  venue: string;
  facultyCoordinator: string;
  studentCoordinator?: string;
  targetAudience: string;
  expectedParticipants: number;
  budget: number;
}

export interface HodEventReportPayload {
  actualParticipants: number;
  outcomes: string;
  photosCount: number;
  reportUrl?: string;
  completionRemarks: string;
}

export interface HodEventsData {
  department: string;
  events: HodEventItem[];
  summary: {
    totalEvents: number;
    upcomingEvents: number;
    completedEvents: number;
    totalParticipants: number;
    totalBudget: number;
  };
}

export interface HodPlacementRecruiter {
  company: string;
  offers: number;
  tier: string;
}

export interface HodPlacementPackageRange {
  range: string;
  count: number;
  percentage: number;
}

export interface HodPlacementOverview {
  department: string;
  totalStudents: number;
  finalYearStudents: number;
  placementEligible: number;
  studentsPlaced: number;
  studentsUnplaced: number;
  inTraining: number;
  internshipParticipants: number;
  placementPercentage: number;
  highestPackageLpa: number;
  averagePackageLpa: number;
  medianPackageLpa: number;
  topRecruiters: HodPlacementRecruiter[];
  packageRanges: HodPlacementPackageRange[];
}

export interface HodStudentPlacementItem {
  registerNumber: string;
  name: string;
  academicYear: string;
  year: string;
  section: string;
  cgpa: number;
  placementStatus:
    | "NOT_REGISTERED"
    | "ELIGIBLE"
    | "APPLIED"
    | "ASSESSMENT"
    | "INTERVIEW"
    | "SELECTED"
    | "PLACED"
    | "NOT_SELECTED"
    | "INTERNSHIP"
    | "INTERNSHIP_COMPLETED";
  company?: string | null;
  role?: string | null;
  packageLpa?: number | null;
  selectionDate?: string | null;
  internshipStatus: string;
  internshipCompany?: string | null;
  internshipDuration?: string | null;
  stipendMonthly?: number | null;
}

export interface HodPlacementsData {
  department: string;
  total: number;
  students: HodStudentPlacementItem[];
}

export interface HodReportTypeItem {
  code: string;
  name: string;
  format: string[];
}

export interface HodReportCategoryItem {
  category: string;
  title: string;
  description: string;
  types: HodReportTypeItem[];
}

export interface HodReportCategoriesData {
  department: string;
  categories: HodReportCategoryItem[];
}

export interface HodReportGeneratePayload {
  category: string;
  reportType: string;
  academicYear: string;
  semester?: string;
  section?: string;
  startDate?: string;
  endDate?: string;
}

export interface HodReportResult {
  reportId: string;
  title: string;
  category: string;
  academicYear: string;
  generatedBy: string;
  generatedAt: string;
  filtersApplied: Record<string, any>;
  columns: { key: string; label: string }[];
  rows: Record<string, any>[];
  totalRecords: number;
}

export interface HodPerformanceAnalyticsData {
  department: string;
  academicTrends: {
    semesterPassRates: {
      semester: string;
      passRate: number;
      appeared: number;
      passed: number;
    }[];
    yearWisePerformance: {
      year: string;
      passPercentage: number;
      averageCgpa: number;
      toppersCount: number;
    }[];
    arrearResolutionVelocity: {
      stage: string;
      percentage: number;
      count: number;
    }[];
    attendancePerformanceCorrelation: {
      attendanceTier: string;
      averageCgpa: number;
      students: number;
    }[];
  };
  facultyAnalytics: {
    totalFaculty: number;
    cadreDistribution: {
      cadre: string;
      count: number;
      percentage: number;
    }[];
    workloadCompliance: {
      range: string;
      count: number;
      percentage: number;
    }[];
    lessonPlanDeliveryAverage: number;
    averageMonthlyAttendance: number;
  };
  departmentGrowth: {
    yearlyIntake: {
      academicYear: string;
      enrolled: number;
      graduated: number;
    }[];
    placementRateGrowth: {
      year: string;
      rate: number;
    }[];
    researchPapersPublished: number;
    patentsFiled: number;
    fundedProjectsAmountLakhs: number;
  };
}

export interface HodAchievementItem {
  id: string;
  title: string;
  description: string;
  category: string;
  recipientName: string;
  recipientType: "STUDENT" | "FACULTY";
  recipientId: string;
  achievementDate: string;
  academicYear: string;
  eventOrOrganization: string;
  certificateUrl?: string;
  verificationStatus: "VERIFIED" | "PENDING_VERIFICATION";
  verifiedBy?: string;
}

export interface HodAchievementCreatePayload {
  title: string;
  description: string;
  category: string;
  recipientName: string;
  recipientType: "STUDENT" | "FACULTY";
  recipientId: string;
  achievementDate: string;
  academicYear: string;
  eventOrOrganization: string;
  certificateUrl?: string;
}

export interface HodAchievementsData {
  department: string;
  achievements: HodAchievementItem[];
  summary: {
    totalAchievements: number;
    studentAchievements: number;
    facultyAchievements: number;
    researchPapers: number;
    patents: number;
    hackathonWins: number;
  };
}

export interface HodAccreditationCriterionItem {
  criterionId: string;
  name: string;
  weightage: number;
  completionPercentage: number;
  documentsCount: number;
  verifiedCount: number;
  status: "COMPLETED" | "IN_PROGRESS" | "PENDING";
}

export interface HodAccreditationDocumentItem {
  id: string;
  title: string;
  criterion: string;
  academicYear: string;
  description: string;
  fileName: string;
  fileType: string;
  fileSizeKb: number;
  uploadedBy: string;
  uploadedAt: string;
  reviewStatus: "VERIFIED" | "UNDER_REVIEW" | "DRAFT";
  reviewer: string;
  reviewRemarks?: string;
}

export interface HodAccreditationDocumentUploadPayload {
  title: string;
  criterion: string;
  academicYear: string;
  description: string;
  fileName: string;
  fileType: string;
  fileSizeKb: number;
  uploadedBy?: string;
}

export interface HodAccreditationOverviewData {
  department: string;
  framework: string;
  programName: string;
  academicYear: string;
  readinessPercentage: number;
  criteria: HodAccreditationCriterionItem[];
  documents: HodAccreditationDocumentItem[];
}

export interface HodAccreditationDocumentsData {
  department: string;
  totalDocuments: number;
  documents: HodAccreditationDocumentItem[];
}
