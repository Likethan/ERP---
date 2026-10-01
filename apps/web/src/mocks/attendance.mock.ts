export interface AttendanceSessionItem {
  id: string;
  sessionDate: string;
  courseCode: string;
  courseName: string;
  section: string;
  facultyName: string;
  periodSlot: string;
  room: string;
  totalStudents: number;
  presentCount: number;
  absentCount: number;
  status: "MARKED" | "SCHEDULED" | "LOCKED" | "PENDING";
}

export interface StudentAttendanceSheetEntry {
  studentId: string;
  rollNumber: string;
  name: string;
  status: "PRESENT" | "ABSENT" | "ON_LEAVE" | "ON_DUTY" | "LATE";
  remarks?: string;
}

export interface StudentLeaveRequestItem {
  id: string;
  studentId: string;
  studentName: string;
  rollNumber: string;
  leaveType: "MEDICAL" | "ON_DUTY" | "CASUAL" | "SPORTS";
  startDate: string;
  endDate: string;
  totalDays: number;
  reason: string;
  status: "PENDING" | "APPROVED" | "REJECTED";
  submittedOn: string;
}

export interface AttendanceCorrectionItem {
  id: string;
  studentName: string;
  rollNumber: string;
  courseCode: string;
  sessionDate: string;
  currentStatus: string;
  requestedStatus: string;
  reason: string;
  status: "PENDING" | "APPROVED" | "REJECTED";
}

export const MOCK_ATTENDANCE_SESSIONS: AttendanceSessionItem[] = [
  {
    id: "att-sess-01",
    sessionDate: "2026-09-30",
    courseCode: "CS301",
    courseName: "Data Structures & Algorithms",
    section: "5th Sem CSE — Sec A",
    facultyName: "Dr. Rajesh Sharma",
    periodSlot: "09:30 - 10:30 AM",
    room: "Hall 302",
    totalStudents: 68,
    presentCount: 62,
    absentCount: 6,
    status: "MARKED",
  },
  {
    id: "att-sess-02",
    sessionDate: "2026-09-30",
    courseCode: "CS302",
    courseName: "Database Management Systems",
    section: "5th Sem CSE — Sec A",
    facultyName: "Dr. K. S. Anand",
    periodSlot: "10:30 - 11:30 AM",
    room: "Hall 302",
    totalStudents: 68,
    presentCount: 65,
    absentCount: 3,
    status: "MARKED",
  },
  {
    id: "att-sess-03",
    sessionDate: "2026-09-30",
    courseCode: "CS303",
    courseName: "Operating Systems & Concurrency",
    section: "5th Sem CSE — Sec A",
    facultyName: "Prof. Meenakshi Sundaram",
    periodSlot: "01:30 - 02:30 PM",
    room: "Hall 302",
    totalStudents: 68,
    presentCount: 0,
    absentCount: 0,
    status: "SCHEDULED",
  },
  {
    id: "att-sess-04",
    sessionDate: "2026-09-29",
    courseCode: "CS301",
    courseName: "Data Structures & Algorithms",
    section: "5th Sem CSE — Sec B",
    facultyName: "Dr. Rajesh Sharma",
    periodSlot: "11:45 - 12:45 PM",
    room: "Hall 304",
    totalStudents: 65,
    presentCount: 58,
    absentCount: 7,
    status: "LOCKED",
  },
];

export const MOCK_LEAVE_REQUESTS: StudentLeaveRequestItem[] = [
  {
    id: "leave-01",
    studentId: "stu-24cse0103",
    studentName: "Rohan Verghese",
    rollNumber: "24CSE0103",
    leaveType: "MEDICAL",
    startDate: "2026-10-02",
    endDate: "2026-10-04",
    totalDays: 3,
    reason: "Viral fever diagnosed by campus medical officer. Hospital prescription attached.",
    status: "PENDING",
    submittedOn: "2026-09-29",
  },
  {
    id: "leave-02",
    studentId: "stu-24cse0101",
    studentName: "Aarav Patel",
    rollNumber: "24CSE0101",
    leaveType: "ON_DUTY",
    startDate: "2026-10-06",
    endDate: "2026-10-07",
    totalDays: 2,
    reason: "Representing university at Smart India Hackathon Regional Finals (IIT Madras).",
    status: "APPROVED",
    submittedOn: "2026-09-25",
  },
];

export const MOCK_ATTENDANCE_CORRECTIONS: AttendanceCorrectionItem[] = [
  {
    id: "corr-01",
    studentName: "Rohan Verghese",
    rollNumber: "24CSE0103",
    courseCode: "CS301",
    sessionDate: "2026-09-24",
    currentStatus: "ABSENT",
    requestedStatus: "ON_DUTY",
    reason: "Participated in departmental coding symposium with Dean permission.",
    status: "PENDING",
  },
];
