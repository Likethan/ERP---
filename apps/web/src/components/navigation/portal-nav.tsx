import React from "react";
import {
  LayoutDashboard,
  Users,
  GraduationCap,
  UserCheck,
  BookOpen,
  CalendarDays,
  Calendar,
  CheckSquare,
  FileSpreadsheet,
  DollarSign,
  Receipt,
  Briefcase,
  Building2,
  PartyPopper,
  BedDouble,
  Bus,
  FileText,
  ShieldCheck,
  Building,
  Layers,
  CreditCard,
  Award,
  BarChart3,
  Bell,
  Activity,
  FlaskConical,
  Trophy,
  Leaf,
  ShieldAlert,
  FileEdit,
  FolderLock,
  Scale,
  Heart,
  Target,
  ArrowRightLeft,
  HandHeart,
  Users2,
  Clock,
  Landmark,
  Bot,
  ClipboardCheck,
  Wrench,
} from "lucide-react";
import type { AuthenticatedUser } from "@campusos/types";

export interface NavLinkItem {
  label: string;
  href: string;
  icon: React.ReactNode;
  badge?: string;
  roles?: string[];
}

export interface NavSection {
  title: string;
  items: NavLinkItem[];
}

export function getNormalizedRoleSet(
  user: AuthenticatedUser | null,
): Set<string> {
  if (!user) return new Set();
  const rawRoles = (user?.roles?.map((r) => r.name) || []).concat(
    (user as any)?.role ? [(user as any).role] : [],
  );
  const set = new Set<string>(rawRoles);
  if (set.has("PRINCIPAL")) set.add("VICE_PRINCIPAL");
  if (set.has("VICE_PRINCIPAL")) set.add("PRINCIPAL");
  if (set.has("SUPER_ADMIN")) set.add("ADMIN");
  if (set.has("ADMIN")) set.add("SUPER_ADMIN");
  if (set.has("BURSAR") || set.has("FINANCE")) set.add("ACCOUNTS");
  if (set.has("ACCOUNTS")) {
    set.add("BURSAR");
    set.add("FINANCE");
  }
  if (set.has("PLACEMENT")) set.add("PLACEMENT_OFFICER");
  if (set.has("PLACEMENT_OFFICER")) set.add("PLACEMENT");
  if (set.has("HOSTEL_WARDEN")) set.add("WARDEN");
  if (set.has("WARDEN")) set.add("HOSTEL_WARDEN");
  if (set.has("TRANSPORT")) set.add("TRANSPORT_OFFICER");
  if (set.has("TRANSPORT_OFFICER")) set.add("TRANSPORT");
  if (set.has("LIBRARY")) set.add("LIBRARIAN");
  if (set.has("LIBRARIAN")) set.add("LIBRARY");
  if (set.has("SECURITY") || set.has("SECURITY_HEAD"))
    set.add("SECURITY_OFFICER");
  if (set.has("SECURITY_OFFICER")) {
    set.add("SECURITY");
    set.add("SECURITY_HEAD");
  }
  if (set.has("FACILITY") || set.has("ESTATE")) set.add("FACILITY_OFFICER");
  if (set.has("FACILITY_OFFICER")) {
    set.add("FACILITY");
    set.add("ESTATE");
  }
  return set;
}

// -----------------------------------------------------------------------------
// 1. Student Portal Dedicated Navigation
// -----------------------------------------------------------------------------
export const STUDENT_PORTAL_NAV: NavSection[] = [
  {
    title: "STUDENT OVERVIEW",
    items: [
      {
        label: "Dashboard",
        href: "/app/dashboard",
        icon: <LayoutDashboard className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "MY ACADEMICS",
    items: [
      {
        label: "My Enrollments",
        href: "/app/academics/enrollments",
        badge: "Active",
        icon: <BookOpen className="h-4 w-4" />,
      },
      {
        label: "Class Timetable",
        href: "/app/academics/timetable",
        icon: <CalendarDays className="h-4 w-4" />,
      },
      {
        label: "Course Study Materials",
        href: "/app/academics/materials",
        icon: <FileText className="h-4 w-4" />,
      },
      {
        label: "Assignments & Grades",
        href: "/app/academics/assignments",
        badge: "Homework",
        icon: <ClipboardCheck className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "MY ATTENDANCE",
    items: [
      {
        label: "Attendance Records",
        href: "/app/attendance/records",
        badge: "92.4%",
        icon: <CheckSquare className="h-4 w-4" />,
      },
      {
        label: "Apply for Leave",
        href: "/app/attendance/leaves",
        icon: <Calendar className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "MY EXAMINATIONS",
    items: [
      {
        label: "Exam Schedules",
        href: "/app/examinations/schedules",
        icon: <Calendar className="h-4 w-4" />,
      },
      {
        label: "Results & GPA Card",
        href: "/app/examinations/results",
        badge: "8.84",
        icon: <GraduationCap className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "FINANCE & DUES",
    items: [
      {
        label: "Tuition Invoices",
        href: "/app/finance/invoices",
        badge: "Clear",
        icon: <Receipt className="h-4 w-4" />,
      },
      {
        label: "Payment Receipts",
        href: "/app/finance/payments",
        icon: <CreditCard className="h-4 w-4" />,
      },
      {
        label: "Scholarships",
        href: "/app/finance/scholarships",
        icon: <Award className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "CAMPUS LIVING & SERVICES",
    items: [
      {
        label: "Hostel Allocation",
        href: "/app/hostel",
        badge: "B3-204",
        icon: <BedDouble className="h-4 w-4" />,
      },
      {
        label: "Campus Transport Fleet",
        href: "/app/transport",
        badge: "Route 7",
        icon: <Bus className="h-4 w-4" />,
      },
      {
        label: "Campus Events",
        href: "/app/events",
        icon: <PartyPopper className="h-4 w-4" />,
      },
      {
        label: "Student Clubs",
        href: "/app/clubs",
        icon: <Users2 className="h-4 w-4" />,
      },
      {
        label: "Announcements",
        href: "/app/announcements",
        icon: <Bell className="h-4 w-4" />,
      },
      {
        label: "Library Catalog",
        href: "/app/library",
        icon: <BookOpen className="h-4 w-4" />,
      },
      {
        label: "Sports & Athletics",
        href: "/app/sports",
        icon: <Trophy className="h-4 w-4" />,
      },
      {
        label: "Alumni Network",
        href: "/app/engagement",
        icon: <HandHeart className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "STUDENT CARE & CAREER",
    items: [
      {
        label: "Faculty Mentor",
        href: "/app/student-support/mentor",
        icon: <Heart className="h-4 w-4" />,
      },
      {
        label: "Student Counselling",
        href: "/app/student-support/counselling",
        icon: <HandHeart className="h-4 w-4" />,
      },
      {
        label: "Placement Drives",
        href: "/app/placement",
        badge: "1 Offer",
        icon: <Briefcase className="h-4 w-4" />,
      },
      {
        label: "My Documents Vault",
        href: "/app/documents/my-documents",
        icon: <FileText className="h-4 w-4" />,
      },
    ],
  },
];

// -----------------------------------------------------------------------------
// 2. Faculty Portal Dedicated Navigation
// -----------------------------------------------------------------------------
export const FACULTY_PORTAL_NAV: NavSection[] = [
  {
    title: "FACULTY OVERVIEW",
    items: [
      {
        label: "Dashboard",
        href: "/app/dashboard",
        icon: <LayoutDashboard className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "TEACHING & CLASSROOM",
    items: [
      {
        label: "My Teaching Subjects",
        href: "/app/academics/subjects",
        badge: "3 Courses",
        icon: <BookOpen className="h-4 w-4" />,
      },
      {
        label: "Lesson Plans & Syllabus",
        href: "/app/academics/lesson-plans",
        icon: <Layers className="h-4 w-4" />,
      },
      {
        label: "Class Diary / Teaching Log",
        href: "/app/academics/class-diary",
        icon: <Calendar className="h-4 w-4" />,
      },
      {
        label: "Teaching Timetable",
        href: "/app/academics/timetable",
        icon: <CalendarDays className="h-4 w-4" />,
      },
      {
        label: "Curricula Schemes",
        href: "/app/academics/curricula",
        icon: <FileSpreadsheet className="h-4 w-4" />,
      },
      {
        label: "Student Directory",
        href: "/app/students",
        icon: <GraduationCap className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "STUDY MATERIALS & ASSIGNMENTS",
    items: [
      {
        label: "Study Materials",
        href: "/app/academics/materials",
        icon: <FileText className="h-4 w-4" />,
      },
      {
        label: "Assignments & Evaluations",
        href: "/app/academics/assignments",
        badge: "Evaluations",
        icon: <ClipboardCheck className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "ATTENDANCE ENGINE",
    items: [
      {
        label: "Mark Class Attendance",
        href: "/app/attendance/sessions",
        badge: "Action",
        icon: <CheckSquare className="h-4 w-4" />,
      },
      {
        label: "Course Attendance Registers",
        href: "/app/attendance/courses",
        icon: <FileSpreadsheet className="h-4 w-4" />,
      },
      {
        label: "Student Attendance Logs",
        href: "/app/attendance/records",
        icon: <Activity className="h-4 w-4" />,
      },
      {
        label: "Attendance Corrections",
        href: "/app/attendance/corrections",
        icon: <Clock className="h-4 w-4" />,
      },
      {
        label: "Student Leave Approvals",
        href: "/app/attendance/leaves",
        icon: <Calendar className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "EXAMINATIONS & EVALUATION",
    items: [
      {
        label: "Continuous Assessments",
        href: "/app/examinations/assessments",
        icon: <FileEdit className="h-4 w-4" />,
      },
      {
        label: "Enter Marks & CIA",
        href: "/app/examinations/marks",
        badge: "CIA Entry",
        icon: <ClipboardCheck className="h-4 w-4" />,
      },
      {
        label: "Exam Schedules & Duties",
        href: "/app/examinations/schedules",
        icon: <CalendarDays className="h-4 w-4" />,
      },
      {
        label: "View Published Results",
        href: "/app/examinations/results",
        icon: <Award className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "STUDENT MENTORING",
    items: [
      {
        label: "Assigned Mentees",
        href: "/app/student-support/mentees",
        badge: "15 Mentees",
        icon: <Users2 className="h-4 w-4" />,
      },
      {
        label: "Mentoring Sessions",
        href: "/app/student-support/sessions",
        icon: <Clock className="h-4 w-4" />,
      },
      {
        label: "Student Goals",
        href: "/app/student-support/goals",
        icon: <Target className="h-4 w-4" />,
      },
      {
        label: "Support Referrals",
        href: "/app/student-support/referrals",
        icon: <ArrowRightLeft className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "FACULTY ADMINISTRATION",
    items: [
      {
        label: "Apply for Faculty Leave",
        href: "/app/faculty/leaves",
        badge: "Leave",
        icon: <CalendarDays className="h-4 w-4" />,
      },
      {
        label: "Faculty Workload & Staff",
        href: "/app/workforce",
        icon: <Briefcase className="h-4 w-4" />,
      },
      {
        label: "Research Grants & Projects",
        href: "/app/research",
        badge: "2 Grants",
        icon: <FlaskConical className="h-4 w-4" />,
      },
      {
        label: "Campus Announcements",
        href: "/app/campus/announcements",
        icon: <Bell className="h-4 w-4" />,
      },
      {
        label: "Campus Events",
        href: "/app/events",
        icon: <PartyPopper className="h-4 w-4" />,
      },
      {
        label: "My Documents Vault",
        href: "/app/documents/my-documents",
        icon: <FileText className="h-4 w-4" />,
      },
    ],
  },
];

// -----------------------------------------------------------------------------
// 3. Head of Department (HOD) Portal Dedicated Navigation
// -----------------------------------------------------------------------------
export const HOD_PORTAL_NAV: NavSection[] = [
  {
    title: "DEPARTMENT LEADERSHIP",
    items: [
      {
        label: "HOD Dedicated Portal",
        href: "/hod/dashboard",
        badge: "Phase 1",
        icon: <Building className="h-4 w-4" />,
      },
      {
        label: "Dashboard",
        href: "/app/dashboard",
        icon: <LayoutDashboard className="h-4 w-4" />,
      },
      {
        label: "Faculty Management",
        href: "/hod/faculty",
        badge: "28 Faculty",
        icon: <UserCheck className="h-4 w-4" />,
      },
      {
        label: "Student Management",
        href: "/hod/students",
        badge: "720 Enrolled",
        icon: <GraduationCap className="h-4 w-4" />,
      },
      {
        label: "Attendance Management",
        href: "/hod/attendance",
        badge: "88.4%",
        icon: <CheckSquare className="h-4 w-4" />,
      },
      {
        label: "Timetable Management",
        href: "/hod/timetable",
        badge: "Master Grid",
        icon: <CalendarDays className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "DEPARTMENTAL ACADEMICS",
    items: [
      {
        label: "Department Faculty Workloads",
        href: "/app/faculty",
        badge: "28 Faculty",
        icon: <UserCheck className="h-4 w-4" />,
      },
      {
        label: "Department Students Roster",
        href: "/app/students",
        badge: "720 Enrolled",
        icon: <GraduationCap className="h-4 w-4" />,
      },
      {
        label: "Academic Structure",
        href: "/app/academic-structure",
        icon: <Building className="h-4 w-4" />,
      },
      {
        label: "Department Programs",
        href: "/app/programs",
        icon: <Award className="h-4 w-4" />,
      },
      {
        label: "Curricula Schemes",
        href: "/app/academics/curricula",
        icon: <FileSpreadsheet className="h-4 w-4" />,
      },
      {
        label: "Course Offerings",
        href: "/app/academics/course-offerings",
        icon: <Layers className="h-4 w-4" />,
      },
      {
        label: "Master Timetable",
        href: "/app/academics/timetable",
        icon: <CalendarDays className="h-4 w-4" />,
      },
      {
        label: "Academic Departments",
        href: "/app/departments",
        icon: <Building2 className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "ATTENDANCE GOVERNANCE",
    items: [
      {
        label: "Attendance Sessions",
        href: "/app/attendance/sessions",
        icon: <CheckSquare className="h-4 w-4" />,
      },
      {
        label: "Course Compliance Registers",
        href: "/app/attendance/courses",
        icon: <FileSpreadsheet className="h-4 w-4" />,
      },
      {
        label: "Attendance Regulations",
        href: "/app/attendance/policies",
        icon: <ShieldAlert className="h-4 w-4" />,
      },
      {
        label: "Department Attendance Reports",
        href: "/app/attendance/reports",
        badge: "88.4%",
        icon: <BarChart3 className="h-4 w-4" />,
      },
      {
        label: "Leave Endorsements",
        href: "/app/attendance/leaves",
        icon: <Calendar className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "EXAMINATION OVERSIGHT",
    items: [
      {
        label: "Assessment Governance",
        href: "/app/examinations/assessments",
        icon: <FileEdit className="h-4 w-4" />,
      },
      {
        label: "Marks & CIA Moderation",
        href: "/app/examinations/marks",
        badge: "Pending",
        icon: <ClipboardCheck className="h-4 w-4" />,
      },
      {
        label: "Department Exam Schedules",
        href: "/app/examinations/schedules",
        icon: <Calendar className="h-4 w-4" />,
      },
      {
        label: "Results & Performance",
        href: "/app/examinations/results",
        icon: <GraduationCap className="h-4 w-4" />,
      },
      {
        label: "Examinations Reports",
        href: "/app/examinations/reports",
        icon: <BarChart3 className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "MENTORSHIP & ACCREDITATION",
    items: [
      {
        label: "Faculty Mentor Assignments",
        href: "/app/student-support/assignments",
        icon: <Users2 className="h-4 w-4" />,
      },
      {
        label: "Department Mentee Records",
        href: "/app/student-support/mentees",
        icon: <Clock className="h-4 w-4" />,
      },
      {
        label: "Department Accreditation",
        href: "/app/accreditation",
        badge: "3.78",
        icon: <Award className="h-4 w-4" />,
      },
      {
        label: "Department Research",
        href: "/app/research",
        icon: <FlaskConical className="h-4 w-4" />,
      },
      {
        label: "Announcements",
        href: "/app/announcements",
        icon: <Bell className="h-4 w-4" />,
      },
    ],
  },
];

// -----------------------------------------------------------------------------
// 4. Vice Principal Portal Dedicated Navigation (Internal Role: PRINCIPAL)
// -----------------------------------------------------------------------------
export const VICE_PRINCIPAL_PORTAL_NAV: NavSection[] = [
  {
    title: "EXECUTIVE WORKSPACE",
    items: [
      {
        label: "Executive Dashboard",
        href: "/vice-principal/dashboard",
        icon: <LayoutDashboard className="h-4 w-4" />,
      },
      {
        label: "Institutional Overview",
        href: "/app/dashboard",
        icon: <BarChart3 className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "DEPARTMENT SUPERVISION",
    items: [
      {
        label: "Department Monitoring",
        href: "/vice-principal/departments",
        badge: "5 Depts",
        icon: <Building2 className="h-4 w-4" />,
      },
      {
        label: "Academic Monitoring",
        href: "/vice-principal/academics",
        badge: "Milestones",
        icon: <Calendar className="h-4 w-4" />,
      },
      {
        label: "Faculty Oversight & Workload",
        href: "/vice-principal/faculty",
        badge: "Workload",
        icon: <UserCheck className="h-4 w-4" />,
      },
      {
        label: "Student Monitoring (<75% Radar)",
        href: "/vice-principal/students",
        badge: "Radar",
        icon: <GraduationCap className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "STATUTORY APPROVALS & EXAMS",
    items: [
      {
        label: "Approval Management Center",
        href: "/vice-principal/approvals",
        badge: "4 Pending",
        icon: <ShieldCheck className="h-4 w-4" />,
      },
      {
        label: "Examinations & CIA Oversight",
        href: "/vice-principal/examinations",
        icon: <ClipboardCheck className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "INTELLIGENCE, AUDIT & DISPATCH",
    items: [
      {
        label: "Reports & Analytics",
        href: "/vice-principal/reports",
        icon: <FileSpreadsheet className="h-4 w-4" />,
      },
      {
        label: "Institutional Circulars",
        href: "/vice-principal/announcements",
        icon: <Bell className="h-4 w-4" />,
      },
      {
        label: "Institutional Audit Trail",
        href: "/vice-principal/audit",
        badge: "Read-Only",
        icon: <ShieldAlert className="h-4 w-4" />,
      },
    ],
  },
];

// -----------------------------------------------------------------------------
// 5. Administrator Portal Dedicated Navigation
// -----------------------------------------------------------------------------
export const ADMIN_PORTAL_NAV: NavSection[] = [
  {
    title: "ADMIN DASHBOARD",
    items: [
      {
        label: "Dashboard",
        href: "/app/dashboard",
        icon: <LayoutDashboard className="h-4 w-4" />,
      },
      {
        label: "People Overview",
        href: "/app/people",
        icon: <Users className="h-4 w-4" />,
      },
      {
        label: "Academic Structure",
        href: "/app/academic-structure",
        icon: <Building2 className="h-4 w-4" />,
      },
      {
        label: "Campuses & Sites",
        href: "/app/campuses",
        icon: <Building className="h-4 w-4" />,
      },
      {
        label: "Institution Profile",
        href: "/app/institution",
        icon: <Landmark className="h-4 w-4" />,
      },
      {
        label: "Departments",
        href: "/app/departments",
        icon: <Layers className="h-4 w-4" />,
      },
      {
        label: "Degree Programs",
        href: "/app/programs",
        icon: <Award className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "PEOPLE & WORKFORCE",
    items: [
      {
        label: "Student Master Registry",
        href: "/app/students",
        icon: <GraduationCap className="h-4 w-4" />,
      },
      {
        label: "Faculty Directory",
        href: "/app/faculty",
        icon: <UserCheck className="h-4 w-4" />,
      },
      {
        label: "Staff Directory",
        href: "/app/staff",
        icon: <Users className="h-4 w-4" />,
      },
      {
        label: "Workforce & HR",
        href: "/app/workforce",
        icon: <Building2 className="h-4 w-4" />,
      },
      {
        label: "Payroll Administration",
        href: "/app/payroll",
        badge: "Admin Only",
        icon: <DollarSign className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "FINANCIAL LEDGER & BILLING",
    items: [
      {
        label: "Financial Overview",
        href: "/app/finance",
        icon: <Landmark className="h-4 w-4" />,
      },
      {
        label: "Fee Structures",
        href: "/app/finance/fee-structures",
        icon: <Layers className="h-4 w-4" />,
      },
      {
        label: "Invoices & Billing",
        href: "/app/finance/invoices",
        icon: <Receipt className="h-4 w-4" />,
      },
      {
        label: "Payments & Collections",
        href: "/app/finance/payments",
        icon: <CreditCard className="h-4 w-4" />,
      },
      {
        label: "Scholarships & Concessions",
        href: "/app/finance/scholarships",
        icon: <Award className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "ACADEMICS, ATTENDANCE & EXAMS",
    items: [
      {
        label: "Curricula Schemes",
        href: "/app/academics/curricula",
        icon: <FileSpreadsheet className="h-4 w-4" />,
      },
      {
        label: "Subject Catalog",
        href: "/app/academics/subjects",
        icon: <BookOpen className="h-4 w-4" />,
      },
      {
        label: "Course Offerings",
        href: "/app/academics/course-offerings",
        icon: <Layers className="h-4 w-4" />,
      },
      {
        label: "Master Timetable",
        href: "/app/academics/timetable",
        icon: <CalendarDays className="h-4 w-4" />,
      },
      {
        label: "Attendance Engine",
        href: "/app/attendance",
        icon: <CheckSquare className="h-4 w-4" />,
      },
      {
        label: "Examinations System",
        href: "/app/examinations",
        icon: <GraduationCap className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "INFRASTRUCTURE, SERVICES & AUDIT",
    items: [
      {
        label: "Hostel Management",
        href: "/app/hostel",
        icon: <BedDouble className="h-4 w-4" />,
      },
      {
        label: "Fleet & Transport",
        href: "/app/transport",
        icon: <Bus className="h-4 w-4" />,
      },
      {
        label: "Document Vault",
        href: "/app/documents",
        icon: <FileText className="h-4 w-4" />,
      },
      {
        label: "Corporate Placements",
        href: "/app/placement",
        icon: <Briefcase className="h-4 w-4" />,
      },
      {
        label: "Accreditation & Audits",
        href: "/app/accreditation",
        icon: <Award className="h-4 w-4" />,
      },
      {
        label: "Research Grants",
        href: "/app/research",
        icon: <FlaskConical className="h-4 w-4" />,
      },
      {
        label: "Campus Security Operations",
        href: "/app/campus-security",
        icon: <ShieldCheck className="h-4 w-4" />,
      },
      {
        label: "Sustainability ESG",
        href: "/app/sustainability",
        icon: <Leaf className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "PLATFORM GOVERNANCE & SECURITY",
    items: [
      {
        label: "Security & RBAC Policies",
        href: "/app/security",
        icon: <ShieldCheck className="h-4 w-4" />,
      },
      {
        label: "Records Lifecycle Retention",
        href: "/app/records-lifecycle",
        icon: <FolderLock className="h-4 w-4" />,
      },
      {
        label: "Legal Affairs & Contracts",
        href: "/app/legal",
        icon: <Scale className="h-4 w-4" />,
      },
      {
        label: "Batch Data Import",
        href: "/app/data-import",
        icon: <FileSpreadsheet className="h-4 w-4" />,
      },
      {
        label: "Marketplace & Add-ons",
        href: "/app/marketplace",
        icon: <Layers className="h-4 w-4" />,
      },
      {
        label: "SaaS Quota & Subscriptions",
        href: "/app/subscriptions",
        icon: <Layers className="h-4 w-4" />,
      },
    ],
  },
];

// -----------------------------------------------------------------------------
// 6. Finance & Accounts Portal Dedicated Navigation
// -----------------------------------------------------------------------------
export const ACCOUNTS_PORTAL_NAV: NavSection[] = [
  {
    title: "ACCOUNTS OVERVIEW",
    items: [
      {
        label: "Dashboard",
        href: "/app/dashboard",
        icon: <LayoutDashboard className="h-4 w-4" />,
      },
      {
        label: "Financial Overview",
        href: "/app/finance",
        icon: <Landmark className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "FEES & BILLING",
    items: [
      {
        label: "Fee Structures",
        href: "/app/finance/fee-structures",
        icon: <Layers className="h-4 w-4" />,
      },
      {
        label: "Student Invoices",
        href: "/app/finance/invoices",
        icon: <Receipt className="h-4 w-4" />,
      },
      {
        label: "Fee Categories",
        href: "/app/finance/fee-categories",
        icon: <FileSpreadsheet className="h-4 w-4" />,
      },
      {
        label: "Fee Assignments",
        href: "/app/finance/assignments",
        icon: <CheckSquare className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "COLLECTIONS & PAYMENTS",
    items: [
      {
        label: "Payment Ledger",
        href: "/app/finance/payments",
        icon: <CreditCard className="h-4 w-4" />,
      },
      {
        label: "Receipts Registry",
        href: "/app/finance/receipts",
        icon: <FileText className="h-4 w-4" />,
      },
      {
        label: "Refunds & Adjustments",
        href: "/app/finance/refunds",
        icon: <ArrowRightLeft className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "AID & FINANCIAL AUDIT",
    items: [
      {
        label: "Scholarships & Concessions",
        href: "/app/finance/scholarships",
        icon: <Award className="h-4 w-4" />,
      },
      {
        label: "Financial Reports",
        href: "/app/finance/reports",
        icon: <BarChart3 className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "STUDENTS & WORKFORCE",
    items: [
      {
        label: "Student Master Registry",
        href: "/app/students",
        icon: <GraduationCap className="h-4 w-4" />,
      },
      {
        label: "Workforce & Payroll",
        href: "/app/payroll",
        icon: <DollarSign className="h-4 w-4" />,
      },
    ],
  },
];

// -----------------------------------------------------------------------------
// 7. Corporate Placement Portal Dedicated Navigation
// -----------------------------------------------------------------------------
export const PLACEMENT_PORTAL_NAV: NavSection[] = [
  {
    title: "PLACEMENT OVERVIEW",
    items: [
      {
        label: "Dashboard",
        href: "/app/dashboard",
        icon: <LayoutDashboard className="h-4 w-4" />,
      },
      {
        label: "Corporate Relations Hub",
        href: "/app/placement",
        icon: <Briefcase className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "CORPORATE PARTNERS",
    items: [
      {
        label: "Partner Companies",
        href: "/app/placement/companies",
        icon: <Building2 className="h-4 w-4" />,
      },
      {
        label: "Job Positions & Roles",
        href: "/app/placement/positions",
        icon: <Layers className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "RECRUITMENT DRIVES",
    items: [
      {
        label: "Campus Drives",
        href: "/app/placement/drives",
        icon: <Calendar className="h-4 w-4" />,
      },
      {
        label: "Interview Schedules",
        href: "/app/placement/interviews",
        icon: <CalendarDays className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "APPLICATIONS & OUTCOMES",
    items: [
      {
        label: "Student Applications",
        href: "/app/placement/applications",
        icon: <FileSpreadsheet className="h-4 w-4" />,
      },
      {
        label: "Job Offers & CTC",
        href: "/app/placement/offers",
        icon: <Award className="h-4 w-4" />,
      },
      {
        label: "Placement Outcomes",
        href: "/app/placement/outcomes",
        icon: <Trophy className="h-4 w-4" />,
      },
      {
        label: "Placement Reports",
        href: "/app/placement/reports",
        icon: <BarChart3 className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "TALENT POOL",
    items: [
      {
        label: "Candidate Pool",
        href: "/app/placement/students",
        icon: <GraduationCap className="h-4 w-4" />,
      },
    ],
  },
];

// -----------------------------------------------------------------------------
// 8. Hostel Warden Portal Dedicated Navigation
// -----------------------------------------------------------------------------
export const WARDEN_PORTAL_NAV: NavSection[] = [
  {
    title: "RESIDENTIAL OVERVIEW",
    items: [
      {
        label: "Dashboard",
        href: "/app/dashboard",
        icon: <LayoutDashboard className="h-4 w-4" />,
      },
      {
        label: "Hostel Administration",
        href: "/app/hostel",
        icon: <BedDouble className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "BLOCKS & ALLOCATIONS",
    items: [
      {
        label: "Hostel Blocks & Rooms",
        href: "/app/infrastructure/hostel",
        icon: <Building2 className="h-4 w-4" />,
      },
      {
        label: "Bed Capacity & Housing",
        href: "/app/housing",
        icon: <Layers className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "RESIDENT WELFARE & LEAVES",
    items: [
      {
        label: "Student Residents",
        href: "/app/students",
        icon: <GraduationCap className="h-4 w-4" />,
      },
      {
        label: "Outing & Leave Approvals",
        href: "/app/attendance/leaves",
        icon: <Calendar className="h-4 w-4" />,
      },
      {
        label: "Facility Maintenance Orders",
        href: "/app/infrastructure/maintenance",
        icon: <Wrench className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "SAFETY & INCIDENTS",
    items: [
      {
        label: "Incident Log",
        href: "/app/campus-security/incidents",
        icon: <ShieldAlert className="h-4 w-4" />,
      },
      {
        label: "Gate Checkpoints",
        href: "/app/campus-security/gate-operations",
        icon: <ShieldCheck className="h-4 w-4" />,
      },
    ],
  },
];

// -----------------------------------------------------------------------------
// 9. Transport & Fleet Portal Dedicated Navigation
// -----------------------------------------------------------------------------
export const TRANSPORT_PORTAL_NAV: NavSection[] = [
  {
    title: "TRANSPORT OVERVIEW",
    items: [
      {
        label: "Dashboard",
        href: "/app/dashboard",
        icon: <LayoutDashboard className="h-4 w-4" />,
      },
      {
        label: "Fleet Hub",
        href: "/app/transport",
        icon: <Bus className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "ROUTES & OPERATIONS",
    items: [
      {
        label: "Transport Routes",
        href: "/app/infrastructure/transport",
        icon: <Bus className="h-4 w-4" />,
      },
      {
        label: "Fleet Maintenance & Repairs",
        href: "/app/infrastructure/maintenance",
        icon: <Wrench className="h-4 w-4" />,
      },
      {
        label: "Operations Reports",
        href: "/app/infrastructure/reports",
        icon: <BarChart3 className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "PASSENGERS & COMMUTE",
    items: [
      {
        label: "Student Commuters",
        href: "/app/students",
        icon: <GraduationCap className="h-4 w-4" />,
      },
      {
        label: "Staff Commuters",
        href: "/app/staff",
        icon: <Users className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "SAFETY & EMERGENCY",
    items: [
      {
        label: "Transit Safety Incidents",
        href: "/app/campus-security/incidents",
        icon: <ShieldAlert className="h-4 w-4" />,
      },
    ],
  },
];

// -----------------------------------------------------------------------------
// 10. Library Portal Dedicated Navigation
// -----------------------------------------------------------------------------
export const LIBRARY_PORTAL_NAV: NavSection[] = [
  {
    title: "LIBRARY OVERVIEW",
    items: [
      {
        label: "Dashboard",
        href: "/app/dashboard",
        icon: <LayoutDashboard className="h-4 w-4" />,
      },
      {
        label: "Library Catalogue",
        href: "/app/library",
        icon: <BookOpen className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "KNOWLEDGE & REPOSITORIES",
    items: [
      {
        label: "Institutional Knowledge",
        href: "/app/knowledge",
        icon: <FileSpreadsheet className="h-4 w-4" />,
      },
      {
        label: "Digital Documents",
        href: "/app/documents",
        icon: <FileText className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "CIRCULATION PATRONS",
    items: [
      {
        label: "Student Borrowers",
        href: "/app/students",
        icon: <GraduationCap className="h-4 w-4" />,
      },
      {
        label: "Faculty Borrowers",
        href: "/app/faculty",
        icon: <UserCheck className="h-4 w-4" />,
      },
      {
        label: "Staff Directory",
        href: "/app/staff",
        icon: <Users className="h-4 w-4" />,
      },
    ],
  },
];

// -----------------------------------------------------------------------------
// 11. Campus Security Portal Dedicated Navigation
// -----------------------------------------------------------------------------
export const SECURITY_PORTAL_NAV: NavSection[] = [
  {
    title: "SECURITY OVERVIEW",
    items: [
      {
        label: "Dashboard",
        href: "/app/dashboard",
        icon: <LayoutDashboard className="h-4 w-4" />,
      },
      {
        label: "Security Command",
        href: "/app/security",
        icon: <ShieldAlert className="h-4 w-4 text-red-500" />,
      },
      {
        label: "Campus Security Hub",
        href: "/app/campus-security",
        icon: <ShieldCheck className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "GATES & ACCESS CONTROL",
    items: [
      {
        label: "Gate Operations",
        href: "/app/campus-security/gate-operations",
        icon: <Building2 className="h-4 w-4" />,
      },
      {
        label: "Access Grants & Badges",
        href: "/app/campus-security/access-grants",
        icon: <CheckSquare className="h-4 w-4" />,
      },
      {
        label: "Security Checkpoints & Zones",
        href: "/app/campus-security/zones",
        icon: <Layers className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "VISITORS & CONTRACTORS",
    items: [
      {
        label: "Visitor Log",
        href: "/app/campus-security/visitors",
        icon: <Users className="h-4 w-4" />,
      },
      {
        label: "Contractor Access",
        href: "/app/campus-security/contractors",
        icon: <UserCheck className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "INCIDENTS & PATROLS",
    items: [
      {
        label: "Security Incidents",
        href: "/app/campus-security/incidents",
        icon: <ShieldAlert className="h-4 w-4" />,
      },
      {
        label: "Patrol Rounds",
        href: "/app/campus-security/patrols",
        icon: <Activity className="h-4 w-4" />,
      },
      {
        label: "Emergency Protocol",
        href: "/app/campus-security/emergency",
        icon: <Bell className="h-4 w-4 text-red-400" />,
      },
    ],
  },
];

// -----------------------------------------------------------------------------
// 12. Estate & Facilities Portal Dedicated Navigation
// -----------------------------------------------------------------------------
export const FACILITY_PORTAL_NAV: NavSection[] = [
  {
    title: "ESTATE OVERVIEW",
    items: [
      {
        label: "Dashboard",
        href: "/app/dashboard",
        icon: <LayoutDashboard className="h-4 w-4" />,
      },
      {
        label: "Infrastructure Hub",
        href: "/app/infrastructure",
        icon: <Building className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "FACILITIES & BUILDINGS",
    items: [
      {
        label: "Physical Facilities",
        href: "/app/infrastructure/facilities",
        icon: <Building2 className="h-4 w-4" />,
      },
      {
        label: "Hostel Blocks",
        href: "/app/infrastructure/hostel",
        icon: <BedDouble className="h-4 w-4" />,
      },
      {
        label: "Campuses & Sites",
        href: "/app/campuses",
        icon: <Landmark className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "MAINTENANCE & ASSETS",
    items: [
      {
        label: "Work Orders & Repairs",
        href: "/app/infrastructure/maintenance",
        icon: <Wrench className="h-4 w-4" />,
      },
      {
        label: "Infrastructure Reports",
        href: "/app/infrastructure/reports",
        icon: <BarChart3 className="h-4 w-4" />,
      },
      {
        label: "Green Campus & Sustainability",
        href: "/app/sustainability",
        icon: <Leaf className="h-4 w-4 text-emerald-500" />,
      },
    ],
  },
];

// -----------------------------------------------------------------------------
// 13. Staff Portal Dedicated Navigation
// -----------------------------------------------------------------------------
export const STAFF_PORTAL_NAV: NavSection[] = [
  {
    title: "STAFF OVERVIEW",
    items: [
      {
        label: "Dashboard",
        href: "/app/dashboard",
        icon: <LayoutDashboard className="h-4 w-4" />,
      },
      {
        label: "Staff Directory",
        href: "/app/staff",
        icon: <Users className="h-4 w-4" />,
      },
      {
        label: "Workforce & HR",
        href: "/app/workforce",
        icon: <Building2 className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "TIME & ATTENDANCE",
    items: [
      {
        label: "My Attendance",
        href: "/app/attendance",
        icon: <CheckSquare className="h-4 w-4" />,
      },
      {
        label: "Apply for Leave",
        href: "/app/attendance/leaves",
        icon: <Calendar className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "CAMPUS & COMMUNICATIONS",
    items: [
      {
        label: "Announcements",
        href: "/app/announcements",
        icon: <Bell className="h-4 w-4" />,
      },
      {
        label: "Documents & Policies",
        href: "/app/documents",
        icon: <FileText className="h-4 w-4" />,
      },
      {
        label: "Knowledge Base",
        href: "/app/knowledge",
        icon: <BookOpen className="h-4 w-4" />,
      },
    ],
  },
];

// -----------------------------------------------------------------------------
// Portal Navigation Resolver & Role Context Helpers
// -----------------------------------------------------------------------------
export function getPortalNavSections(
  user: AuthenticatedUser | null,
): NavSection[] {
  if (!user) return STUDENT_PORTAL_NAV;
  const roleSet = getNormalizedRoleSet(user);

  if (roleSet.has("SUPER_ADMIN") || roleSet.has("ADMIN")) {
    return ADMIN_PORTAL_NAV;
  }
  if (roleSet.has("PRINCIPAL") || roleSet.has("VICE_PRINCIPAL")) {
    return VICE_PRINCIPAL_PORTAL_NAV;
  }
  if (roleSet.has("HOD")) {
    return HOD_PORTAL_NAV;
  }
  if (roleSet.has("FACULTY")) {
    return FACULTY_PORTAL_NAV;
  }
  if (roleSet.has("ACCOUNTS")) {
    return ACCOUNTS_PORTAL_NAV;
  }
  if (roleSet.has("PLACEMENT_OFFICER")) {
    return PLACEMENT_PORTAL_NAV;
  }
  if (roleSet.has("WARDEN")) {
    return WARDEN_PORTAL_NAV;
  }
  if (roleSet.has("TRANSPORT_OFFICER")) {
    return TRANSPORT_PORTAL_NAV;
  }
  if (roleSet.has("LIBRARIAN")) {
    return LIBRARY_PORTAL_NAV;
  }
  if (roleSet.has("SECURITY_OFFICER")) {
    return SECURITY_PORTAL_NAV;
  }
  if (roleSet.has("FACILITY_OFFICER")) {
    return FACILITY_PORTAL_NAV;
  }
  if (roleSet.has("STAFF")) {
    return STAFF_PORTAL_NAV;
  }
  if (roleSet.has("STUDENT")) {
    return STUDENT_PORTAL_NAV;
  }

  // Fallback for special personnel: default to student view
  return STUDENT_PORTAL_NAV;
}

export interface PortalHeaderMeta {
  title: string;
  badge: string;
  badgeClass: string;
  glowClass: string;
}

export function getPortalHeaderMeta(
  user: AuthenticatedUser | null,
): PortalHeaderMeta {
  if (!user) {
    return {
      title: "Student Portal",
      badge: "STUDENT",
      badgeClass: "bg-yellow-100 text-yellow-950 border-yellow-300 font-bold",
      glowClass: "from-yellow-400/20",
    };
  }

  const roleSet = getNormalizedRoleSet(user);

  if (roleSet.has("SUPER_ADMIN") || roleSet.has("ADMIN")) {
    return {
      title: "Administrator Portal",
      badge: "ADMIN",
      badgeClass: "bg-emerald-50 text-emerald-900 border-emerald-300 font-bold",
      glowClass: "from-emerald-400/20",
    };
  }
  if (roleSet.has("PRINCIPAL") || roleSet.has("VICE_PRINCIPAL")) {
    return {
      title: "Vice Principal Portal",
      badge: "VICE PRINCIPAL",
      badgeClass: "bg-amber-100 text-amber-950 border-amber-300 font-bold",
      glowClass: "from-amber-400/20",
    };
  }
  if (roleSet.has("HOD")) {
    return {
      title: "Head of Dept Portal",
      badge: "HOD",
      badgeClass: "bg-purple-50 text-purple-900 border-purple-300 font-bold",
      glowClass: "from-purple-400/20",
    };
  }
  if (roleSet.has("FACULTY")) {
    return {
      title: "Faculty Portal",
      badge: "FACULTY",
      badgeClass: "bg-sky-50 text-sky-900 border-sky-300 font-bold",
      glowClass: "from-sky-400/20",
    };
  }
  if (roleSet.has("ACCOUNTS")) {
    return {
      title: "Finance & Accounts Portal",
      badge: "ACCOUNTS",
      badgeClass:
        "bg-emerald-100 text-emerald-950 border-emerald-300 font-bold",
      glowClass: "from-emerald-400/20",
    };
  }
  if (roleSet.has("PLACEMENT_OFFICER")) {
    return {
      title: "Corporate Placement Portal",
      badge: "PLACEMENT",
      badgeClass: "bg-blue-100 text-blue-950 border-blue-300 font-bold",
      glowClass: "from-blue-400/20",
    };
  }
  if (roleSet.has("WARDEN")) {
    return {
      title: "Hostel Warden Portal",
      badge: "WARDEN",
      badgeClass: "bg-amber-100 text-amber-950 border-amber-300 font-bold",
      glowClass: "from-amber-400/20",
    };
  }
  if (roleSet.has("TRANSPORT_OFFICER")) {
    return {
      title: "Transport & Fleet Portal",
      badge: "TRANSPORT",
      badgeClass: "bg-cyan-100 text-cyan-950 border-cyan-300 font-bold",
      glowClass: "from-cyan-400/20",
    };
  }
  if (roleSet.has("LIBRARIAN")) {
    return {
      title: "Library Portal",
      badge: "LIBRARIAN",
      badgeClass: "bg-teal-100 text-teal-950 border-teal-300 font-bold",
      glowClass: "from-teal-400/20",
    };
  }
  if (roleSet.has("SECURITY_OFFICER")) {
    return {
      title: "Campus Security Portal",
      badge: "SECURITY",
      badgeClass: "bg-rose-100 text-rose-950 border-rose-300 font-bold",
      glowClass: "from-rose-400/20",
    };
  }
  if (roleSet.has("FACILITY_OFFICER")) {
    return {
      title: "Estate & Facilities Portal",
      badge: "FACILITIES",
      badgeClass: "bg-lime-100 text-lime-950 border-lime-300 font-bold",
      glowClass: "from-lime-400/20",
    };
  }
  if (roleSet.has("STAFF")) {
    return {
      title: "Staff Portal",
      badge: "STAFF",
      badgeClass: "bg-slate-100 text-slate-900 border-slate-300 font-bold",
      glowClass: "from-slate-400/20",
    };
  }

  return {
    title: "Student Portal",
    badge: "STUDENT",
    badgeClass: "bg-yellow-100 text-yellow-950 border-yellow-300 font-bold",
    glowClass: "from-yellow-400/20",
  };
}
