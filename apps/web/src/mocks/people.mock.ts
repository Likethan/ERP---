import {
  GuardianRecord,
  PersonDocument,
  AcademicMilestone,
  FacultyWorkloadSummary,
  FacultyPublication,
  StaffShiftItem,
  StaffLeaveRequest,
  PeopleSummaryMetrics,
  DepartmentPeopleDistribution,
} from "@/types/people";
import { StaffDetailView } from "@/types/domain";

// ==========================================
// 1. Guardians Pool
// ==========================================

export const MOCK_GUARDIANS_POOL: Record<string, GuardianRecord[]> = {
  "stu-24cse0101": [
    {
      id: "grd-101-1",
      name: "Suresh Patel",
      relation: "FATHER",
      relationLabel: "Father",
      phone: "+91 98450 99881",
      email: "suresh.patel@gmail.com",
      occupation: "Senior Telecom Systems Engineer",
      annualIncome: "₹ 18,50,000",
      isPrimary: true,
      isEmergencyContact: true,
      address: {
        street: "42, Shanti Nagar, 4th Cross",
        city: "Bengaluru",
        state: "Karnataka",
        pincode: "560027",
      },
    },
    {
      id: "grd-101-2",
      name: "Meenakshi Patel",
      relation: "MOTHER",
      relationLabel: "Mother",
      phone: "+91 98450 99882",
      email: "meenakshi.patel@outlook.com",
      occupation: "High School Mathematics Educator",
      annualIncome: "₹ 8,20,000",
      isPrimary: false,
      isEmergencyContact: true,
    },
  ],
  "stu-24cse0102": [
    {
      id: "grd-102-1",
      name: "K. Sundaram",
      relation: "FATHER",
      relationLabel: "Father",
      phone: "+91 94481 22334",
      email: "k.sundaram@gmail.com",
      occupation: "Chartered Accountant & Financial Auditor",
      annualIncome: "₹ 24,00,000",
      isPrimary: true,
      isEmergencyContact: true,
      address: {
        street: "18, 7th Main, Malleshwaram",
        city: "Bengaluru",
        state: "Karnataka",
        pincode: "560003",
      },
    },
  ],
  "stu-24cse0103": [
    {
      id: "grd-103-1",
      name: "Mathew Verghese",
      relation: "FATHER",
      relationLabel: "Father",
      phone: "+91 97401 55443",
      email: "m.verghese@kerala-plantations.com",
      occupation: "Estate Manager & Planter",
      annualIncome: "₹ 14,00,000",
      isPrimary: true,
      isEmergencyContact: true,
    },
    {
      id: "grd-103-2",
      name: "George Verghese",
      relation: "GUARDIAN",
      relationLabel: "Local Guardian (Uncle)",
      phone: "+91 98801 11223",
      email: "george.verghese@bengaluru-it.in",
      occupation: "IT Project Director",
      isPrimary: false,
      isEmergencyContact: true,
    },
  ],
};

// ==========================================
// 2. Student Documents Vault
// ==========================================

export const MOCK_STUDENT_DOCUMENTS: Record<string, PersonDocument[]> = {
  "stu-24cse0101": [
    {
      id: "doc-101-01",
      name: "National Identity Card (Aadhaar)",
      category: "IDENTITY",
      fileSize: "1.4 MB",
      mimeType: "application/pdf",
      uploadedAt: "2024-08-02",
      uploadedBy: "Aarav Patel (Self)",
      status: "VERIFIED",
      verifiedAt: "2024-08-05",
      verifiedBy: "Registrar Office (Verification Cell)",
    },
    {
      id: "doc-101-02",
      name: "Class XII Senior Secondary Board Transcript",
      category: "ACADEMIC",
      fileSize: "2.8 MB",
      mimeType: "application/pdf",
      uploadedAt: "2024-08-02",
      uploadedBy: "Aarav Patel (Self)",
      status: "VERIFIED",
      verifiedAt: "2024-08-06",
      verifiedBy: "Admissions Scrutiny Committee",
    },
    {
      id: "doc-101-03",
      name: "CET State Rank Allotment Letter",
      category: "ADMISSION",
      fileSize: "840 KB",
      mimeType: "application/pdf",
      uploadedAt: "2024-08-01",
      uploadedBy: "Aarav Patel (Self)",
      status: "VERIFIED",
      verifiedAt: "2024-08-03",
      verifiedBy: "Central Seat Allotment Board",
    },
    {
      id: "doc-101-04",
      name: "Institutional Medical Fitness & Blood Group Certificate",
      category: "MEDICAL",
      fileSize: "620 KB",
      mimeType: "image/jpeg",
      uploadedAt: "2024-08-04",
      uploadedBy: "Aarav Patel (Self)",
      status: "VERIFIED",
      verifiedAt: "2024-08-07",
      verifiedBy: "Campus Health Center",
    },
    {
      id: "doc-101-05",
      name: "Amazon AWS Certified Cloud Practitioner Badge",
      category: "CERTIFICATES",
      fileSize: "1.1 MB",
      mimeType: "application/pdf",
      uploadedAt: "2026-02-14",
      uploadedBy: "Aarav Patel (Self)",
      status: "UNDER_REVIEW",
    },
  ],
  "stu-24cse0102": [
    {
      id: "doc-102-01",
      name: "National Identity Card (Aadhaar)",
      category: "IDENTITY",
      fileSize: "1.2 MB",
      uploadedAt: "2024-08-02",
      uploadedBy: "Priya Sundaram",
      status: "VERIFIED",
      verifiedAt: "2024-08-04",
      verifiedBy: "Registrar Office",
    },
    {
      id: "doc-102-02",
      name: "Class X Secondary Education Certificate",
      category: "ACADEMIC",
      fileSize: "2.1 MB",
      uploadedAt: "2024-08-03",
      uploadedBy: "Priya Sundaram",
      status: "VERIFIED",
      verifiedAt: "2024-08-05",
      verifiedBy: "Admissions Cell",
    },
    {
      id: "doc-102-03",
      name: "Fee Concession / Merit Scholarship Sanction Order",
      category: "FINANCIAL",
      fileSize: "950 KB",
      uploadedAt: "2024-09-10",
      uploadedBy: "Accounts Directorate",
      status: "VERIFIED",
      verifiedAt: "2024-09-12",
      verifiedBy: "Finance Officer",
    },
  ],
};

// ==========================================
// 3. Academic Milestones Timeline
// ==========================================

export const MOCK_ACADEMIC_MILESTONES: Record<string, AcademicMilestone[]> = {
  "stu-24cse0101": [
    {
      id: "mls-101-1",
      title: "Admission Formally Completed & Verified",
      category: "ADMISSION",
      date: "2024-08-01",
      semester: 1,
      description:
        "Admitted to B.Tech CSE under Karnataka State Merit Quota with rank 1,420.",
      status: "COMPLETED",
      awardedBy: "Dean of Admissions",
    },
    {
      id: "mls-101-2",
      title: "First Year Engineering Foundation Cleared",
      category: "SEMESTER_PROGRESSION",
      date: "2025-06-20",
      semester: 2,
      description:
        "Successfully cleared all 10 foundation subjects with first-class distinction (CGPA: 8.85).",
      status: "COMPLETED",
    },
    {
      id: "mls-101-3",
      title: "Winner: National Smart Campus Hackathon",
      category: "ACHIEVEMENT",
      date: "2025-11-18",
      semester: 3,
      description:
        "1st Prize in AI & Edge Computing category with cash prize of ₹ 1,00,000.",
      status: "COMPLETED",
      awardedBy: "Ministry of Education Innovation Cell",
    },
    {
      id: "mls-101-4",
      title: "Semester 4 Summer Industrial Internship",
      category: "INTERNSHIP",
      date: "2026-07-15",
      semester: 4,
      description:
        "Completed 8-week Cloud Platform Engineering internship at Infosys Bangalore DC.",
      status: "COMPLETED",
      certificateRef: "CERT-INFY-2026-088",
    },
    {
      id: "mls-101-5",
      title: "Pre-Placement Super Dream Shortlist (Google)",
      category: "PLACEMENT",
      date: "2026-09-28",
      semester: 5,
      description:
        "Shortlisted for Round 2 Technical Assessments for SWE 2027 Campus Drive.",
      status: "IN_PROGRESS",
    },
    {
      id: "mls-101-6",
      title: "B.Tech Degree Conferment & Convocation",
      category: "GRADUATION",
      date: "2028-07-30",
      semester: 8,
      description:
        "Degree award upon successful completion of 160 university credits.",
      status: "UPCOMING",
    },
  ],
  "stu-24cse0102": [
    {
      id: "mls-102-1",
      title: "Institutional Admission via Merit Counseling",
      category: "ADMISSION",
      date: "2024-08-01",
      semester: 1,
      description:
        "Enrolled in B.Tech CSE with 96.4% in Senior Secondary Examinations.",
      status: "COMPLETED",
    },
    {
      id: "mls-102-2",
      title: "Dean's Honor List Distinction (Sem 1 & 2)",
      category: "ACHIEVEMENT",
      date: "2025-07-02",
      semester: 2,
      description: "Achieved semester GPA of 9.28 with zero backlogs.",
      status: "COMPLETED",
      awardedBy: "Dean of Academic Affairs",
    },
  ],
};

// ==========================================
// 4. Faculty Workload & Lab Designations
// ==========================================

export const MOCK_FACULTY_WORKLOADS: Record<string, FacultyWorkloadSummary> = {
  "fac-cse-001": {
    facultyId: "fac-cse-001",
    academicYear: "2026-2027",
    semester: 5,
    totalAssignedHours: 16,
    lectureHours: 10,
    labHours: 4,
    preparationHours: 2,
    weeklyTargetHours: 16,
    status: "BALANCED",
    assignments: [
      {
        id: "asg-01",
        code: "CS301",
        name: "Database Management Systems",
        semester: 5,
        section: "A",
        studentCount: 64,
        lectureHours: 3,
        labHours: 2,
        credits: 4,
      },
      {
        id: "asg-02",
        code: "CS301",
        name: "Database Management Systems",
        semester: 5,
        section: "B",
        studentCount: 62,
        lectureHours: 3,
        labHours: 2,
        credits: 4,
      },
      {
        id: "asg-03",
        code: "CS405",
        name: "Distributed Computing Architectures",
        semester: 7,
        section: "A",
        studentCount: 58,
        lectureHours: 4,
        labHours: 0,
        credits: 3,
      },
    ],
    labDesignations: [
      {
        id: "lab-des-01",
        labName: "Advanced DBMS & Big Data Laboratory",
        courseCode: "CS301-L",
        courseName: "DBMS Laboratory",
        section: "A-Batch 1",
        dayOfWeek: "Tuesday",
        timeSlot: "02:00 PM - 04:00 PM",
        roomNumber: "Lab 304, Turing Block",
        weeklyHours: 2,
        batchCapacity: 32,
      },
      {
        id: "lab-des-02",
        labName: "Advanced DBMS & Big Data Laboratory",
        courseCode: "CS301-L",
        courseName: "DBMS Laboratory",
        section: "B-Batch 2",
        dayOfWeek: "Thursday",
        timeSlot: "10:30 AM - 12:30 PM",
        roomNumber: "Lab 304, Turing Block",
        weeklyHours: 2,
        batchCapacity: 31,
      },
    ],
  },
  "fac-cse-002": {
    facultyId: "fac-cse-002",
    academicYear: "2026-2027",
    semester: 5,
    totalAssignedHours: 14,
    lectureHours: 8,
    labHours: 6,
    preparationHours: 2,
    weeklyTargetHours: 16,
    status: "UNDER_ALLOCATED",
    assignments: [
      {
        id: "asg-11",
        code: "CS304",
        name: "Design & Analysis of Algorithms",
        semester: 5,
        section: "A",
        studentCount: 64,
        lectureHours: 4,
        labHours: 3,
        credits: 4,
      },
      {
        id: "asg-12",
        code: "CS304",
        name: "Design & Analysis of Algorithms",
        semester: 5,
        section: "B",
        studentCount: 62,
        lectureHours: 4,
        labHours: 3,
        credits: 4,
      },
    ],
    labDesignations: [
      {
        id: "lab-des-11",
        labName: "Algorithms & Competitive Programming Lab",
        courseCode: "CS304-L",
        courseName: "Algorithms Lab",
        section: "A-All",
        dayOfWeek: "Wednesday",
        timeSlot: "09:00 AM - 12:00 PM",
        roomNumber: "Lab 201, Ramanujan Wing",
        weeklyHours: 3,
        batchCapacity: 64,
      },
    ],
  },
};

// ==========================================
// 5. Faculty Research & Publications
// ==========================================

export const MOCK_FACULTY_PUBLICATIONS: Record<string, FacultyPublication[]> = {
  "fac-cse-001": [
    {
      id: "pub-001",
      title:
        "Optimized Consensus in Permissioned Distributed Ledgers for High-Throughput Academic Credential Verification",
      publicationType: "JOURNAL",
      venueName: "IEEE Transactions on Cloud & Services Computing",
      publicationYear: 2025,
      authors: ["Dr. V. Ramanathan", "A. Sharma", "P. Sundaram"],
      doi: "10.1109/TCSC.2025.319082",
      status: "PUBLISHED",
      citationCount: 14,
      url: "https://doi.org/10.1109/TCSC.2025.319082",
      abstractSummary:
        "Proposes an asynchronous zero-overhead consensus protocol achieving 18,000 tx/sec with millisecond finality.",
    },
    {
      id: "pub-002",
      title:
        "Multi-Tenant Scalability Patterns in Next-Generation Higher Education ERP Architectures",
      publicationType: "CONFERENCE",
      venueName:
        "ACM International Conference on Software Engineering (ICSE 2026)",
      publicationYear: 2026,
      authors: ["Dr. V. Ramanathan", "K. J. Likethan"],
      status: "ACCEPTED",
      citationCount: 3,
      url: "https://dl.acm.org/proc/icse2026/ramanathan",
    },
    {
      id: "pub-003",
      title:
        "Zero-Knowledge Proof Verification for Decentralized Student Identity Records",
      publicationType: "PATENT",
      venueName: "Indian Patent Office (Application No. 202541098231)",
      publicationYear: 2025,
      authors: ["Dr. V. Ramanathan"],
      status: "SUBMITTED",
      abstractSummary:
        "Cryptographic protocol ensuring privacy-preserving biometric validation in university attendance nodes.",
    },
  ],
  "fac-cse-002": [
    {
      id: "pub-010",
      title:
        "Approximation Algorithms for Multi-Resource Fair Scheduling in Heterogeneous GPU Clusters",
      publicationType: "JOURNAL",
      venueName: "Journal of Parallel and Distributed Computing (Elsevier)",
      publicationYear: 2024,
      authors: ["Prof. Anita Sharma", "M. B. Rao"],
      doi: "10.1016/j.jpdc.2024.104812",
      status: "PUBLISHED",
      citationCount: 22,
    },
  ],
};

// ==========================================
// 6. Non-Teaching Staff Shifts & Roster
// ==========================================

export const MOCK_STAFF_SHIFTS: StaffShiftItem[] = [
  {
    id: "shf-morning",
    shiftCode: "SHF-MORN",
    shiftName: "Morning Operations Shift",
    shiftType: "MORNING",
    startTime: "07:30 AM",
    endTime: "03:30 PM",
    assignedStaffCount: 8,
    department: "Transport, Hostels & Security",
    description:
      "Covers early student transport arrival, breakfast kitchen oversight, and morning registration desk.",
  },
  {
    id: "shf-general",
    shiftCode: "SHF-GEN",
    shiftName: "General Academic Day Shift",
    shiftType: "GENERAL",
    startTime: "09:00 AM",
    endTime: "05:30 PM",
    assignedStaffCount: 24,
    department: "Administration, Academic Offices & Central Labs",
    description:
      "Standard daytime administrative support, laboratory assistance, and student affairs desks.",
  },
  {
    id: "shf-evening",
    shiftCode: "SHF-EVE",
    shiftName: "Evening & Extended Lab Shift",
    shiftType: "EVENING",
    startTime: "01:30 PM",
    endTime: "09:30 PM",
    assignedStaffCount: 6,
    department: "Digital Library, Research Computing & Sports",
    description:
      "Supervises extended reading rooms, sports complexes, and after-hours research compute facilities.",
  },
  {
    id: "shf-night",
    shiftCode: "SHF-NGT",
    shiftName: "Night Vigilance & Facility Security",
    shiftType: "NIGHT",
    startTime: "09:30 PM",
    endTime: "06:00 AM",
    assignedStaffCount: 5,
    department: "Campus Security & Residential Caretakers",
    description:
      "Campus perimeter surveillance, hostel night-entry desk, and emergency medical ambulance dispatch.",
  },
];

export const MOCK_STAFF_ROSTER: StaffDetailView[] = [
  {
    id: "stf-001",
    employeeCode: "STF-ADM-001",
    firstName: "Rajesh",
    lastName: "Sharma",
    email: "rajesh.sharma@campusos.edu",
    phone: "+91 94480 11001",
    department: "Academic Administration",
    role: "Assistant Registrar (Academics & Admissions)",
    designation: "Assistant Registrar",
    employmentType: "PERMANENT",
    joiningDate: "2018-06-15",
    status: "ACTIVE",
    shift: MOCK_STAFF_SHIFTS[1],
    leaveBalance: { casual: 8, sick: 10, earned: 24 },
  },
  {
    id: "stf-002",
    employeeCode: "STF-FIN-002",
    firstName: "Kavita",
    lastName: "Iyer",
    email: "kavita.iyer@campusos.edu",
    phone: "+91 94480 11002",
    department: "Accounts & Financial Services",
    role: "Senior Accounts Officer & Bursar",
    designation: "Accounts Officer",
    employmentType: "PERMANENT",
    joiningDate: "2020-03-01",
    status: "ACTIVE",
    shift: MOCK_STAFF_SHIFTS[1],
    leaveBalance: { casual: 5, sick: 12, earned: 18 },
  },
  {
    id: "stf-003",
    employeeCode: "STF-SYS-003",
    firstName: "Mohammed",
    lastName: "Tariq",
    email: "mohammed.tariq@campusos.edu",
    phone: "+91 94480 11003",
    department: "Information Technology & Networks",
    role: "Senior Systems & Network Infrastructure Engineer",
    designation: "System Administrator",
    employmentType: "PERMANENT",
    joiningDate: "2019-11-10",
    status: "ACTIVE",
    shift: MOCK_STAFF_SHIFTS[1],
    leaveBalance: { casual: 10, sick: 8, earned: 30 },
  },
  {
    id: "stf-004",
    employeeCode: "STF-LAB-004",
    firstName: "Sunil",
    lastName: "Kumar",
    email: "sunil.kumar@campusos.edu",
    phone: "+91 94480 11004",
    department: "Computer Science Laboratories",
    role: "Lead Hardware & Systems Laboratory Technician",
    designation: "Senior Lab Technician",
    employmentType: "PERMANENT",
    joiningDate: "2021-08-20",
    status: "ACTIVE",
    shift: MOCK_STAFF_SHIFTS[0],
    leaveBalance: { casual: 7, sick: 11, earned: 15 },
  },
  {
    id: "stf-005",
    employeeCode: "STF-HST-005",
    firstName: "Manjunath",
    lastName: "Gowda",
    email: "manjunath.gowda@campusos.edu",
    phone: "+91 94480 11005",
    department: "Student Hostels & Residential Affairs",
    role: "Chief Residential Warden & Caretaker",
    designation: "Chief Warden",
    employmentType: "PERMANENT",
    joiningDate: "2017-04-12",
    status: "ACTIVE",
    shift: MOCK_STAFF_SHIFTS[2],
    leaveBalance: { casual: 4, sick: 9, earned: 21 },
  },
  {
    id: "stf-006",
    employeeCode: "STF-LIB-006",
    firstName: "Arun",
    lastName: "Prasad",
    email: "arun.prasad@campusos.edu",
    phone: "+91 94480 11006",
    department: "Central Digital Library",
    role: "Assistant Librarian & E-Resources Manager",
    designation: "Assistant Librarian",
    employmentType: "CONTRACT",
    joiningDate: "2022-09-01",
    status: "ACTIVE",
    shift: MOCK_STAFF_SHIFTS[2],
    leaveBalance: { casual: 6, sick: 6, earned: 10 },
  },
  {
    id: "stf-007",
    employeeCode: "STF-TRN-007",
    firstName: "Nagaraj",
    lastName: "V.",
    email: "nagaraj.v@campusos.edu",
    phone: "+91 94480 11007",
    department: "Transport & Logistics",
    role: "Chief Transport Fleet Supervisor",
    designation: "Fleet Supervisor",
    employmentType: "PERMANENT",
    joiningDate: "2016-02-15",
    status: "ACTIVE",
    shift: MOCK_STAFF_SHIFTS[0],
    leaveBalance: { casual: 9, sick: 14, earned: 26 },
  },
  {
    id: "stf-008",
    employeeCode: "STF-SEC-008",
    firstName: "Bhaskar",
    lastName: "Reddy",
    email: "bhaskar.reddy@campusos.edu",
    phone: "+91 94480 11008",
    department: "Campus Safety & Security",
    role: "Chief Security Officer & Night Commander",
    designation: "Security Officer",
    employmentType: "PERMANENT",
    joiningDate: "2019-01-10",
    status: "ACTIVE",
    shift: MOCK_STAFF_SHIFTS[3],
    leaveBalance: { casual: 6, sick: 8, earned: 22 },
  },
];

export const MOCK_STAFF_LEAVES: StaffLeaveRequest[] = [
  {
    id: "lv-001",
    staffId: "stf-004",
    staffName: "Sunil Kumar",
    department: "Computer Science Laboratories",
    leaveType: "CASUAL",
    startDate: "2026-10-06",
    endDate: "2026-10-07",
    totalDays: 2,
    reason: "Family festive function at hometown (Mysuru).",
    status: "APPROVED",
    requestedAt: "2026-09-29",
    reviewedBy: "Dr. V. Ramanathan (HOD CSE)",
    reviewedAt: "2026-09-30",
    reviewRemarks: "Lab maintenance duties handed over to Asst. Tech Praveen.",
  },
  {
    id: "lv-002",
    staffId: "stf-002",
    staffName: "Kavita Iyer",
    department: "Accounts & Financial Services",
    leaveType: "EARNED",
    startDate: "2026-10-12",
    endDate: "2026-10-16",
    totalDays: 5,
    reason: "Pre-scheduled personal family pilgrimage.",
    status: "PENDING",
    requestedAt: "2026-10-01",
  },
  {
    id: "lv-003",
    staffId: "stf-003",
    staffName: "Mohammed Tariq",
    department: "Information Technology & Networks",
    leaveType: "DUTY",
    startDate: "2026-10-08",
    endDate: "2026-10-09",
    totalDays: 2,
    reason:
      "Deputation to NKN (National Knowledge Network) High-Speed Internet peering workshop.",
    status: "APPROVED",
    requestedAt: "2026-09-27",
    reviewedBy: "Registrar Office",
    reviewedAt: "2026-09-28",
  },
];

// ==========================================
// 7. People Aggregation Metrics
// ==========================================

export const MOCK_PEOPLE_METRICS: PeopleSummaryMetrics = {
  totalStudents: 1420,
  activeStudents: 1385,
  recentlyAdmittedStudents: 420,
  graduatingStudents: 310,
  totalFaculty: 84,
  activeFaculty: 81,
  phdFacultyCount: 56,
  totalStaff: 48,
  activeStaff: 46,
  staffOnDutyToday: 38,
  pendingLeaveApprovals: 3,
  pendingDocumentVerifications: 14,
  totalDepartments: 6,
  totalPrograms: 12,
};

export const MOCK_DEPARTMENT_DISTRIBUTION: DepartmentPeopleDistribution[] = [
  {
    departmentId: "dept-cse",
    departmentName: "Computer Science & Engineering",
    departmentCode: "CSE",
    studentCount: 480,
    facultyCount: 28,
    staffCount: 12,
    hodName: "Dr. V. Ramanathan",
  },
  {
    departmentId: "dept-ece",
    departmentName: "Electronics & Communication Engineering",
    departmentCode: "ECE",
    studentCount: 360,
    facultyCount: 22,
    staffCount: 10,
    hodName: "Dr. K. S. Venkatesh",
  },
  {
    departmentId: "dept-me",
    departmentName: "Mechanical Engineering",
    departmentCode: "ME",
    studentCount: 280,
    facultyCount: 18,
    staffCount: 14,
    hodName: "Dr. Anand Kulkarni",
  },
  {
    departmentId: "dept-ai",
    departmentName: "Artificial Intelligence & Data Science",
    departmentCode: "AI-DS",
    studentCount: 300,
    facultyCount: 16,
    staffCount: 12,
    hodName: "Dr. Preethi Balakrishnan",
  },
];

// Key aliases for seamless lookup across ID formats
MOCK_FACULTY_WORKLOADS["fac-cse-01"] = MOCK_FACULTY_WORKLOADS["fac-cse-001"];
MOCK_FACULTY_WORKLOADS["fac-cse-02"] = MOCK_FACULTY_WORKLOADS["fac-cse-002"];
MOCK_FACULTY_PUBLICATIONS["fac-cse-01"] =
  MOCK_FACULTY_PUBLICATIONS["fac-cse-001"];
MOCK_FACULTY_PUBLICATIONS["fac-cse-02"] =
  MOCK_FACULTY_PUBLICATIONS["fac-cse-002"];
