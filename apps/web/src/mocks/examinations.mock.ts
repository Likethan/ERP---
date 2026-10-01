export interface AssessmentItem {
  id: string;
  code: string;
  title: string;
  type: "INTERNAL_TEST" | "MID_TERM" | "END_SEM" | "ASSIGNMENT" | "LAB_EXAM";
  academicYear: string;
  semester: number;
  totalMarks: number;
  weightagePercent: number;
  startDate: string;
  status: "SCHEDULED" | "MARKS_ENTRY_OPEN" | "COMPLETED" | "PUBLISHED";
}

export interface ExamScheduleItem {
  id: string;
  examName: string;
  subjectCode: string;
  subjectName: string;
  date: string;
  timeSlot: string;
  roomNumber: string;
  chiefInvigilator: string;
  totalCandidates: number;
  status: "CONFIRMED" | "DRAFT" | "RESCHEDULED";
}

export interface StudentResultItem {
  studentId: string;
  rollNumber: string;
  name: string;
  program: string;
  semester: number;
  sgpa: number;
  cgpa: number;
  backlogs: number;
  resultStatus: "DISTINCTION" | "FIRST_CLASS" | "PASS" | "FAIL";
  publishedDate: string;
}

export const MOCK_ASSESSMENTS: AssessmentItem[] = [
  {
    id: "asm-ia1-2026",
    code: "IA-01",
    title: "Continuous Internal Assessment 1 (Odd Sem)",
    type: "INTERNAL_TEST",
    academicYear: "2026-2027",
    semester: 5,
    totalMarks: 50,
    weightagePercent: 20,
    startDate: "2026-10-12",
    status: "SCHEDULED",
  },
  {
    id: "asm-mid-2026",
    code: "MID-SEM",
    title: "Mid-Semester Evaluation Exam",
    type: "MID_TERM",
    academicYear: "2026-2027",
    semester: 5,
    totalMarks: 100,
    weightagePercent: 30,
    startDate: "2026-11-05",
    status: "SCHEDULED",
  },
  {
    id: "asm-sem4-end",
    code: "ESE-SEM4",
    title: "End Semester Examinations (Even Sem 2025-26)",
    type: "END_SEM",
    academicYear: "2025-2026",
    semester: 4,
    totalMarks: 100,
    weightagePercent: 50,
    startDate: "2026-05-18",
    status: "PUBLISHED",
  },
];

export const MOCK_EXAM_SCHEDULES: ExamScheduleItem[] = [
  {
    id: "sch-01",
    examName: "Continuous Internal Assessment 1",
    subjectCode: "CS301",
    subjectName: "Data Structures & Algorithms",
    date: "2026-10-12",
    timeSlot: "10:00 AM - 11:30 AM",
    roomNumber: "Auditorium Hall A",
    chiefInvigilator: "Dr. Rajesh Sharma",
    totalCandidates: 133,
    status: "CONFIRMED",
  },
  {
    id: "sch-02",
    examName: "Continuous Internal Assessment 1",
    subjectCode: "CS302",
    subjectName: "Database Management Systems",
    date: "2026-10-13",
    timeSlot: "10:00 AM - 11:30 AM",
    roomNumber: "Auditorium Hall A",
    chiefInvigilator: "Dr. K. S. Anand",
    totalCandidates: 133,
    status: "CONFIRMED",
  },
  {
    id: "sch-03",
    examName: "Continuous Internal Assessment 1",
    subjectCode: "CS303",
    subjectName: "Operating Systems & Concurrency",
    date: "2026-10-14",
    timeSlot: "10:00 AM - 11:30 AM",
    roomNumber: "Auditorium Hall A",
    chiefInvigilator: "Prof. Meenakshi Sundaram",
    totalCandidates: 133,
    status: "CONFIRMED",
  },
];

export const MOCK_RESULTS: StudentResultItem[] = [
  {
    studentId: "stu-24cse0102",
    rollNumber: "24CSE0102",
    name: "Priya Sundaram",
    program: "B.Tech Computer Science & Engineering",
    semester: 4,
    sgpa: 9.60,
    cgpa: 9.42,
    backlogs: 0,
    resultStatus: "DISTINCTION",
    publishedDate: "2026-06-30",
  },
  {
    studentId: "stu-24ece0201",
    rollNumber: "24ECE0201",
    name: "Ananya Deshmukh",
    program: "B.Tech Electronics & Communication",
    semester: 4,
    sgpa: 9.35,
    cgpa: 9.18,
    backlogs: 0,
    resultStatus: "DISTINCTION",
    publishedDate: "2026-06-30",
  },
  {
    studentId: "stu-24cse0101",
    rollNumber: "24CSE0101",
    name: "Aarav Patel",
    program: "B.Tech Computer Science & Engineering",
    semester: 4,
    sgpa: 9.10,
    cgpa: 8.94,
    backlogs: 0,
    resultStatus: "FIRST_CLASS",
    publishedDate: "2026-06-30",
  },
  {
    studentId: "stu-24aiml0301",
    rollNumber: "24AI0301",
    name: "Vikramaditya Rao",
    program: "B.Tech AI & Machine Learning",
    semester: 4,
    sgpa: 8.80,
    cgpa: 8.72,
    backlogs: 0,
    resultStatus: "FIRST_CLASS",
    publishedDate: "2026-06-30",
  },
  {
    studentId: "stu-24cse0103",
    rollNumber: "24CSE0103",
    name: "Rohan Verghese",
    program: "B.Tech Computer Science & Engineering",
    semester: 4,
    sgpa: 7.80,
    cgpa: 7.65,
    backlogs: 0,
    resultStatus: "FIRST_CLASS",
    publishedDate: "2026-06-30",
  },
];
