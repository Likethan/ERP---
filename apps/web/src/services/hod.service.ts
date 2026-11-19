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
    sectionDistribution: { section: string; students: number; attendance: number }[];
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

  async getDashboardStats(department: string = this.defaultDept): Promise<ApiResponse<HodDashboardStats>> {
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
              averageStudentAttendance: d.statistics?.average_student_attendance || 88.4,
              averageFacultyAttendance: d.statistics?.average_faculty_attendance || 96.2,
              studentsShortageCount: d.statistics?.attendance_shortage_count || 14,
              pendingApprovalRequests: d.statistics?.pending_approval_requests || 6,
            },
            studentAnalytics: {
              yearWiseStrength: d.student_analytics?.year_wise || [
                { year: "1st Year", strength: 180, percentage: 91.2 },
                { year: "2nd Year", strength: 180, percentage: 88.6 },
                { year: "3rd Year", strength: 180, percentage: 87.1 },
                { year: "4th Year", strength: 180, percentage: 86.8 },
              ],
              sectionDistribution: d.student_analytics?.section_distribution || [
                { section: "CSE-A", students: 68, attendance: 89.2 },
                { section: "CSE-B", students: 65, attendance: 87.8 },
                { section: "CSE-C", students: 67, attendance: 88.1 },
              ],
            },
            facultyAnalytics: {
              total: d.faculty_analytics?.total || 28,
              presentToday: d.faculty_analytics?.present_today || 26,
              onLeave: d.faculty_analytics?.on_leave || 2,
              averageWorkloadHours: d.faculty_analytics?.average_workload_hours || 14.5,
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
                description: "Dr. Rajesh Sharma finalized period 2 session. 64/68 present.",
                timestamp: "10 mins ago",
              },
              {
                id: "act-2",
                type: "request",
                title: "Leave Endorsement Pending",
                description: "Dr. Priya Nair requested 2 days duty leave for IEEE conference.",
                timestamp: "45 mins ago",
              },
              {
                id: "act-3",
                type: "student",
                title: "Attendance Alert Dispatched",
                description: "Warning SMS & email sent to parents of 14 students below 75%.",
                timestamp: "2 hours ago",
              },
              {
                id: "act-4",
                type: "faculty",
                title: "Course File Updated: CS501",
                description: "Dr. K. S. Anand updated Unit 4 lesson plan & outcomes.",
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
            description: "Dr. Rajesh Sharma finalized period 2 session. 64/68 present.",
            timestamp: "10 mins ago",
          },
          {
            id: "act-2",
            type: "request",
            title: "Leave Endorsement Pending",
            description: "Dr. Priya Nair requested 2 days duty leave for IEEE conference.",
            timestamp: "45 mins ago",
          },
          {
            id: "act-3",
            type: "student",
            title: "Attendance Alert Dispatched",
            description: "Warning notification sent to parents of 14 students below 75%.",
            timestamp: "2 hours ago",
          },
          {
            id: "act-4",
            type: "faculty",
            title: "Course File Updated: CS501",
            description: "Dr. K. S. Anand updated Unit 4 lesson plan & outcomes.",
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
      if (params?.designation && params.designation !== "ALL") q.append("designation", params.designation);
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
          assignedSubjects: (f.assigned_subjects || []).map((s: any, idx: number) => ({
            id: `sub-${idx}`,
            code: s.code,
            name: s.name,
            semester: s.semester,
            section: s.section,
            studentCount: s.students,
          })),
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
    const res = await studentsService.getById(id);
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
      (a) => a.department.toLowerCase().includes("computer") || a.department === "CSE",
    );

    return {
      department,
      overall_percentage: summaryRes.data?.overallAttendancePercentage || 88.4,
      present_today: 682,
      absent_today: 38,
      total_enrolled: 720,
      statutory_threshold: 75.0,
      shortage_count: alerts.length || summaryRes.data?.studentsBelowThresholdCount || 14,
      class_wise: [
        { class_name: "CSE 3rd Sem - Sec A", total: 68, present: 63, rate: 92.6 },
        { class_name: "CSE 3rd Sem - Sec B", total: 65, present: 58, rate: 89.2 },
        { class_name: "CSE 5th Sem - Sec A", total: 68, present: 61, rate: 89.7 },
        { class_name: "CSE 5th Sem - Sec B", total: 65, present: 56, rate: 86.1 },
        { class_name: "CSE 7th Sem - Sec A", total: 60, present: 50, rate: 83.3 },
      ],
      shortage_students: alerts.length > 0 ? alerts : [
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
      { day: "Monday", period: 1, subjectCode: "CS301", subjectName: "Data Structures & Algorithms", facultyName: "Dr. Rajesh Sharma", classroom: "Hall 302" },
      { day: "Monday", period: 2, subjectCode: "CS302", subjectName: "Database Management Systems", facultyName: "Dr. Priya Nair", classroom: "Hall 302" },
      { day: "Monday", period: 3, subjectCode: "CS303", subjectName: "Computer Networks", facultyName: "Prof. S. Ranganathan", classroom: "Hall 302" },
      { day: "Monday", period: 4, subjectCode: "CS304", subjectName: "Operating Systems", facultyName: "Dr. K. S. Anand", classroom: "Hall 302" },
      { day: "Monday", period: 5, subjectCode: "CS305", subjectName: "Web Technology Lab", facultyName: "Prof. A. Meenakshi", classroom: "CS Lab 3", isLab: true },
      { day: "Monday", period: 6, subjectCode: "CS305", subjectName: "Web Technology Lab", facultyName: "Prof. A. Meenakshi", classroom: "CS Lab 3", isLab: true },
      { day: "Monday", period: 7, subjectCode: "CS308", subjectName: "Library / Mentoring", facultyName: "Mentor Committee", classroom: "Central Library" },

      // Tuesday
      { day: "Tuesday", period: 1, subjectCode: "CS302", subjectName: "Database Management Systems", facultyName: "Dr. Priya Nair", classroom: "Hall 302" },
      { day: "Tuesday", period: 2, subjectCode: "CS301", subjectName: "Data Structures & Algorithms", facultyName: "Dr. Rajesh Sharma", classroom: "Hall 302" },
      { day: "Tuesday", period: 3, subjectCode: "CS304", subjectName: "Operating Systems", facultyName: "Dr. K. S. Anand", classroom: "Hall 302" },
      { day: "Tuesday", period: 4, subjectCode: "MA301", subjectName: "Discrete Mathematics", facultyName: "Dr. R. Venkat", classroom: "Hall 302" },
      { day: "Tuesday", period: 5, subjectCode: "CS306", subjectName: "DBMS Laboratory", facultyName: "Dr. Priya Nair", classroom: "Database Lab", isLab: true },
      { day: "Tuesday", period: 6, subjectCode: "CS306", subjectName: "DBMS Laboratory", facultyName: "Dr. Priya Nair", classroom: "Database Lab", isLab: true },
      { day: "Tuesday", period: 7, subjectCode: "CS307", subjectName: "Seminar & Aptitude", facultyName: "Placement Cell", classroom: "Hall 302" },

      // Wednesday
      { day: "Wednesday", period: 1, subjectCode: "CS303", subjectName: "Computer Networks", facultyName: "Prof. S. Ranganathan", classroom: "Hall 302" },
      { day: "Wednesday", period: 2, subjectCode: "MA301", subjectName: "Discrete Mathematics", facultyName: "Dr. R. Venkat", classroom: "Hall 302" },
      { day: "Wednesday", period: 3, subjectCode: "CS301", subjectName: "Data Structures & Algorithms", facultyName: "Dr. Rajesh Sharma", classroom: "Hall 302" },
      { day: "Wednesday", period: 4, subjectCode: "CS302", subjectName: "Database Management Systems", facultyName: "Dr. Priya Nair", classroom: "Hall 302" },
      { day: "Wednesday", period: 5, subjectCode: "CS304", subjectName: "Operating Systems", facultyName: "Dr. K. S. Anand", classroom: "Hall 302" },
      { day: "Wednesday", period: 6, subjectCode: "OE301", subjectName: "Open Elective - IoT", facultyName: "Prof. T. Balaji", classroom: "Hall 204" },
      { day: "Wednesday", period: 7, subjectCode: "SP301", subjectName: "Sports & Extra-Curricular", facultyName: "Physical Director", classroom: "Sports Complex" },

      // Thursday
      { day: "Thursday", period: 1, subjectCode: "CS304", subjectName: "Operating Systems", facultyName: "Dr. K. S. Anand", classroom: "Hall 302" },
      { day: "Thursday", period: 2, subjectCode: "CS303", subjectName: "Computer Networks", facultyName: "Prof. S. Ranganathan", classroom: "Hall 302" },
      { day: "Thursday", period: 3, subjectCode: "MA301", subjectName: "Discrete Mathematics", facultyName: "Dr. R. Venkat", classroom: "Hall 302" },
      { day: "Thursday", period: 4, subjectCode: "CS301", subjectName: "Data Structures & Algorithms", facultyName: "Dr. Rajesh Sharma", classroom: "Hall 302" },
      { day: "Thursday", period: 5, subjectCode: "CS307", subjectName: "Networks Laboratory", facultyName: "Prof. S. Ranganathan", classroom: "Networks Lab", isLab: true },
      { day: "Thursday", period: 6, subjectCode: "CS307", subjectName: "Networks Laboratory", facultyName: "Prof. S. Ranganathan", classroom: "Networks Lab", isLab: true },
      { day: "Thursday", period: 7, subjectCode: "CS309", subjectName: "NPTEL / MOOCs", facultyName: "Online Coordinator", classroom: "E-Learning Center" },

      // Friday
      { day: "Friday", period: 1, subjectCode: "MA301", subjectName: "Discrete Mathematics", facultyName: "Dr. R. Venkat", classroom: "Hall 302" },
      { day: "Friday", period: 2, subjectCode: "CS302", subjectName: "Database Management Systems", facultyName: "Dr. Priya Nair", classroom: "Hall 302" },
      { day: "Friday", period: 3, subjectCode: "CS304", subjectName: "Operating Systems", facultyName: "Dr. K. S. Anand", classroom: "Hall 302" },
      { day: "Friday", period: 4, subjectCode: "CS303", subjectName: "Computer Networks", facultyName: "Prof. S. Ranganathan", classroom: "Hall 302" },
      { day: "Friday", period: 5, subjectCode: "OE301", subjectName: "Open Elective - IoT", facultyName: "Prof. T. Balaji", classroom: "Hall 204" },
      { day: "Friday", period: 6, subjectCode: "CS310", subjectName: "Project Phase-I Mentoring", facultyName: "Project Committee", classroom: "CS Lab 1" },
      { day: "Friday", period: 7, subjectCode: "CS310", subjectName: "Project Phase-I Mentoring", facultyName: "Project Committee", classroom: "CS Lab 1" },

      // Saturday
      { day: "Saturday", period: 1, subjectCode: "CS301", subjectName: "Data Structures (Tutorial)", facultyName: "Dr. Rajesh Sharma", classroom: "Hall 302" },
      { day: "Saturday", period: 2, subjectCode: "CS303", subjectName: "Networks (Tutorial)", facultyName: "Prof. S. Ranganathan", classroom: "Hall 302" },
      { day: "Saturday", period: 3, subjectCode: "CS302", subjectName: "DBMS (Tutorial)", facultyName: "Dr. Priya Nair", classroom: "Hall 302" },
      { day: "Saturday", period: 4, subjectCode: "CC301", subjectName: "Coding Club & Hackathon", facultyName: "Club Coordinators", classroom: "CS Center of Excellence" },
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
}

export const hodService = new HodService();
