export interface DepartmentItem {
  id: string;
  code: string;
  name: string;
  hodName: string;
  hodEmail: string;
  facultyCount: number;
  studentCount: number;
  programsCount: number;
  status: "ACTIVE" | "INACTIVE";
}

export interface ProgramItem {
  id: string;
  code: string;
  name: string;
  degreeType: "UG" | "PG" | "DOCTORAL" | "DIPLOMA";
  department: string;
  durationYears: number;
  totalSemesters: number;
  totalCredits: number;
  intakeCapacity: number;
  status: "ACTIVE" | "INACTIVE";
}

export interface SubjectItem {
  id: string;
  code: string;
  name: string;
  department: string;
  credits: number;
  type: "THEORY" | "LAB" | "INTEGRATED" | "PROJECT" | "ELECTIVE";
  lectureHours: number;
  tutorialHours: number;
  practicalHours: number;
  status: "ACTIVE" | "ARCHIVED";
}

export interface CurriculumSchemeItem {
  id: string;
  name: string;
  regulationYear: string;
  program: string;
  totalCredits: number;
  status: "PUBLISHED" | "DRAFT" | "REVISION";
  semestersCount: number;
  subjectsCount: number;
}

export interface CourseOfferingItem {
  id: string;
  subjectCode: string;
  subjectName: string;
  academicYear: string;
  semester: number;
  section: string;
  department: string;
  credits: number;
  facultyName: string;
  enrolledStudents: number;
  status: "ACTIVE" | "COMPLETED" | "DRAFT";
}

export interface TimetableSlotItem {
  id: string;
  day: "MONDAY" | "TUESDAY" | "WEDNESDAY" | "THURSDAY" | "FRIDAY" | "SATURDAY";
  timeSlot: string;
  subjectCode: string;
  subjectName: string;
  facultyName: string;
  roomNumber: string;
  section: string;
}

export const MOCK_DEPARTMENTS: DepartmentItem[] = [
  {
    id: "dept-cse",
    code: "CSE",
    name: "Computer Science & Engineering",
    hodName: "Dr. K. S. Anand",
    hodEmail: "hod.cse@campusos.edu",
    facultyCount: 28,
    studentCount: 720,
    programsCount: 3,
    status: "ACTIVE",
  },
  {
    id: "dept-ece",
    code: "ECE",
    name: "Electronics & Communication Engineering",
    hodName: "Dr. Ananya Mukherjee",
    hodEmail: "ananya.m@campusos.edu",
    facultyCount: 22,
    studentCount: 540,
    programsCount: 2,
    status: "ACTIVE",
  },
  {
    id: "dept-me",
    code: "ME",
    name: "Mechanical Engineering",
    hodName: "Dr. S. K. Patil",
    hodEmail: "sk.patil@campusos.edu",
    facultyCount: 18,
    studentCount: 360,
    programsCount: 2,
    status: "ACTIVE",
  },
  {
    id: "dept-it",
    code: "IT",
    name: "Information Technology",
    hodName: "Dr. Geeta Pillai",
    hodEmail: "geeta.p@campusos.edu",
    facultyCount: 16,
    studentCount: 420,
    programsCount: 1,
    status: "ACTIVE",
  },
  {
    id: "dept-mba",
    code: "MBA",
    name: "Management Studies",
    hodName: "Dr. R. Ramanathan",
    hodEmail: "r.raman@campusos.edu",
    facultyCount: 12,
    studentCount: 240,
    programsCount: 1,
    status: "ACTIVE",
  },
];

export const MOCK_PROGRAMS: ProgramItem[] = [
  {
    id: "prog-cse-btech",
    code: "BTECH-CSE",
    name: "Bachelor of Technology in Computer Science & Engineering",
    degreeType: "UG",
    department: "Computer Science & Engineering",
    durationYears: 4,
    totalSemesters: 8,
    totalCredits: 160,
    intakeCapacity: 180,
    status: "ACTIVE",
  },
  {
    id: "prog-ece-btech",
    code: "BTECH-ECE",
    name: "Bachelor of Technology in Electronics & Communication",
    degreeType: "UG",
    department: "Electronics & Communication Engineering",
    durationYears: 4,
    totalSemesters: 8,
    totalCredits: 160,
    intakeCapacity: 120,
    status: "ACTIVE",
  },
  {
    id: "prog-aiml-btech",
    code: "BTECH-AIML",
    name: "Bachelor of Technology in AI & Machine Learning",
    degreeType: "UG",
    department: "Computer Science & Engineering",
    durationYears: 4,
    totalSemesters: 8,
    totalCredits: 160,
    intakeCapacity: 60,
    status: "ACTIVE",
  },
  {
    id: "prog-me-btech",
    code: "BTECH-ME",
    name: "Bachelor of Technology in Mechanical Engineering",
    degreeType: "UG",
    department: "Mechanical Engineering",
    durationYears: 4,
    totalSemesters: 8,
    totalCredits: 160,
    intakeCapacity: 90,
    status: "ACTIVE",
  },
];

export const MOCK_SUBJECTS: SubjectItem[] = [
  {
    id: "sub-cs301",
    code: "CS301",
    name: "Data Structures & Algorithms",
    department: "Computer Science & Engineering",
    credits: 4,
    type: "THEORY",
    lectureHours: 3,
    tutorialHours: 1,
    practicalHours: 0,
    status: "ACTIVE",
  },
  {
    id: "sub-cs302",
    code: "CS302",
    name: "Database Management Systems",
    department: "Computer Science & Engineering",
    credits: 4,
    type: "INTEGRATED",
    lectureHours: 3,
    tutorialHours: 0,
    practicalHours: 2,
    status: "ACTIVE",
  },
  {
    id: "sub-cs303",
    code: "CS303",
    name: "Operating Systems & Concurrency",
    department: "Computer Science & Engineering",
    credits: 3,
    type: "THEORY",
    lectureHours: 3,
    tutorialHours: 0,
    practicalHours: 0,
    status: "ACTIVE",
  },
  {
    id: "sub-cs304",
    code: "CS304",
    name: "Computer Networks & Security",
    department: "Computer Science & Engineering",
    credits: 3,
    type: "THEORY",
    lectureHours: 3,
    tutorialHours: 0,
    practicalHours: 0,
    status: "ACTIVE",
  },
  {
    id: "sub-cs305",
    code: "CS305",
    name: "Theory of Computation & Automata",
    department: "Computer Science & Engineering",
    credits: 3,
    type: "THEORY",
    lectureHours: 3,
    tutorialHours: 1,
    practicalHours: 0,
    status: "ACTIVE",
  },
  {
    id: "sub-cs306",
    code: "CS306",
    name: "Systems Software & Compilation",
    department: "Computer Science & Engineering",
    credits: 3,
    type: "ELECTIVE",
    lectureHours: 3,
    tutorialHours: 0,
    practicalHours: 0,
    status: "ACTIVE",
  },
];

export const MOCK_CURRICULA: CurriculumSchemeItem[] = [
  {
    id: "curr-2024-cse",
    name: "Outcome-Based Curriculum Scheme 2024 (CBCS)",
    regulationYear: "R-2024",
    program: "B.Tech Computer Science & Engineering",
    totalCredits: 160,
    status: "PUBLISHED",
    semestersCount: 8,
    subjectsCount: 46,
  },
  {
    id: "curr-2024-ece",
    name: "Autonomous Engineering Curriculum 2024",
    regulationYear: "R-2024",
    program: "B.Tech Electronics & Communication",
    totalCredits: 160,
    status: "PUBLISHED",
    semestersCount: 8,
    subjectsCount: 44,
  },
  {
    id: "curr-2026-draft",
    name: "Next-Gen AI & Embedded Systems Scheme 2026",
    regulationYear: "R-2026",
    program: "B.Tech AI & Machine Learning",
    totalCredits: 162,
    status: "DRAFT",
    semestersCount: 8,
    subjectsCount: 48,
  },
];

export const MOCK_COURSE_OFFERINGS: CourseOfferingItem[] = [
  {
    id: "off-cs301-a",
    subjectCode: "CS301",
    subjectName: "Data Structures & Algorithms",
    academicYear: "2026-2027",
    semester: 5,
    section: "A",
    department: "Computer Science & Engineering",
    credits: 4,
    facultyName: "Dr. Rajesh Sharma",
    enrolledStudents: 68,
    status: "ACTIVE",
  },
  {
    id: "off-cs301-b",
    subjectCode: "CS301",
    subjectName: "Data Structures & Algorithms",
    academicYear: "2026-2027",
    semester: 5,
    section: "B",
    department: "Computer Science & Engineering",
    credits: 4,
    facultyName: "Dr. Rajesh Sharma",
    enrolledStudents: 65,
    status: "ACTIVE",
  },
  {
    id: "off-cs302-a",
    subjectCode: "CS302",
    subjectName: "Database Management Systems",
    academicYear: "2026-2027",
    semester: 5,
    section: "A",
    department: "Computer Science & Engineering",
    credits: 4,
    facultyName: "Dr. K. S. Anand",
    enrolledStudents: 68,
    status: "ACTIVE",
  },
  {
    id: "off-cs303-a",
    subjectCode: "CS303",
    subjectName: "Operating Systems & Concurrency",
    academicYear: "2026-2027",
    semester: 5,
    section: "A",
    department: "Computer Science & Engineering",
    credits: 3,
    facultyName: "Prof. Meenakshi Sundaram",
    enrolledStudents: 68,
    status: "ACTIVE",
  },
];

export const MOCK_TIMETABLE: TimetableSlotItem[] = [
  {
    id: "tt-mon-1",
    day: "MONDAY",
    timeSlot: "09:30 - 10:30 AM",
    subjectCode: "CS301",
    subjectName: "Data Structures & Algorithms",
    facultyName: "Dr. Rajesh Sharma",
    roomNumber: "Hall 302, Academic Block A",
    section: "5th Sem CSE — Sec A",
  },
  {
    id: "tt-mon-2",
    day: "MONDAY",
    timeSlot: "10:30 - 11:30 AM",
    subjectCode: "CS302",
    subjectName: "Database Management Systems",
    facultyName: "Dr. K. S. Anand",
    roomNumber: "Hall 302, Academic Block A",
    section: "5th Sem CSE — Sec A",
  },
  {
    id: "tt-mon-3",
    day: "MONDAY",
    timeSlot: "11:45 - 12:45 PM",
    subjectCode: "CS304",
    subjectName: "Computer Networks & Security",
    facultyName: "Prof. Suresh Venkatesh",
    roomNumber: "Hall 302, Academic Block A",
    section: "5th Sem CSE — Sec A",
  },
  {
    id: "tt-mon-4",
    day: "MONDAY",
    timeSlot: "01:30 - 02:30 PM",
    subjectCode: "CS303",
    subjectName: "Operating Systems & Concurrency",
    facultyName: "Prof. Meenakshi Sundaram",
    roomNumber: "Hall 302, Academic Block A",
    section: "5th Sem CSE — Sec A",
  },
  {
    id: "tt-mon-5",
    day: "MONDAY",
    timeSlot: "02:30 - 04:30 PM",
    subjectCode: "CS302L",
    subjectName: "DBMS & SQL Laboratory",
    facultyName: "Dr. K. S. Anand",
    roomNumber: "Computer Lab 4 (Turing Hall)",
    section: "5th Sem CSE — Sec A",
  },
  {
    id: "tt-tue-1",
    day: "TUESDAY",
    timeSlot: "09:30 - 10:30 AM",
    subjectCode: "CS305",
    subjectName: "Theory of Computation & Automata",
    facultyName: "Dr. Rajesh Sharma",
    roomNumber: "Hall 302, Academic Block A",
    section: "5th Sem CSE — Sec A",
  },
  {
    id: "tt-tue-2",
    day: "TUESDAY",
    timeSlot: "10:30 - 11:30 AM",
    subjectCode: "CS301",
    subjectName: "Data Structures & Algorithms",
    facultyName: "Dr. Rajesh Sharma",
    roomNumber: "Hall 302, Academic Block A",
    section: "5th Sem CSE — Sec A",
  },
  {
    id: "tt-wed-1",
    day: "WEDNESDAY",
    timeSlot: "09:30 - 10:30 AM",
    subjectCode: "CS303",
    subjectName: "Operating Systems & Concurrency",
    facultyName: "Prof. Meenakshi Sundaram",
    roomNumber: "Hall 302, Academic Block A",
    section: "5th Sem CSE — Sec A",
  },
];

export interface SectionItem {
  id: string;
  name: string;
  code: string;
  department: string;
  semester: number;
  capacity: number;
  status: "ACTIVE" | "INACTIVE";
}

export const MOCK_SECTIONS: SectionItem[] = [
  { id: "sec-a", name: "Section A", code: "SEC-A", department: "Computer Science & Engineering", semester: 5, capacity: 70, status: "ACTIVE" },
  { id: "sec-b", name: "Section B", code: "SEC-B", department: "Computer Science & Engineering", semester: 5, capacity: 70, status: "ACTIVE" },
  { id: "sec-c", name: "Section C", code: "SEC-C", department: "Computer Science & Engineering", semester: 3, capacity: 70, status: "ACTIVE" },
  { id: "sec-ece-a", name: "Section A", code: "SEC-ECE-A", department: "Electronics & Communication Engineering", semester: 5, capacity: 60, status: "ACTIVE" },
];

