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
        label: "Teaching Timetable",
        href: "/app/academics/timetable",
        icon: <CalendarDays className="h-4 w-4" />,
      },
      {
        label: "Student Directory",
        href: "/app/students",
        icon: <GraduationCap className="h-4 w-4" />,
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
        label: "Student Leave Approvals",
        href: "/app/attendance/leaves",
        icon: <Calendar className="h-4 w-4" />,
      },
      {
        label: "Apply for Faculty Leave",
        href: "/app/attendance/leaves",
        icon: <CalendarDays className="h-4 w-4" />,
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
        label: "Exam Schedules",
        href: "/app/examinations/schedules",
        icon: <CalendarDays className="h-4 w-4" />,
      },
      {
        label: "Published Results",
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
    title: "RESEARCH & ACADEMIC LIFE",
    items: [
      {
        label: "Research Grants & Projects",
        href: "/app/research",
        badge: "2 Grants",
        icon: <FlaskConical className="h-4 w-4" />,
      },
      {
        label: "Faculty Colleagues",
        href: "/app/workforce",
        icon: <Briefcase className="h-4 w-4" />,
      },
      {
        label: "Campus Events",
        href: "/app/events",
        icon: <PartyPopper className="h-4 w-4" />,
      },
      {
        label: "Announcements",
        href: "/app/announcements",
        icon: <Bell className="h-4 w-4" />,
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
        label: "Dashboard",
        href: "/app/dashboard",
        icon: <LayoutDashboard className="h-4 w-4" />,
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
    title: "EXECUTIVE OVERVIEW",
    items: [
      {
        label: "Dashboard",
        href: "/app/dashboard",
        icon: <LayoutDashboard className="h-4 w-4" />,
      },
      {
        label: "Institutional Intelligence",
        href: "/app/intelligence",
        badge: "Live KPIs",
        icon: <BarChart3 className="h-4 w-4" />,
      },
      {
        label: "Campus AI Assistant",
        href: "/app/ai",
        icon: <Bot className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "INSTITUTIONAL GOVERNANCE",
    items: [
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
        label: "Campuses Directory",
        href: "/app/campuses",
        icon: <Building className="h-4 w-4" />,
      },
      {
        label: "Institutional Hierarchy",
        href: "/app/institution",
        icon: <Landmark className="h-4 w-4" />,
      },
      {
        label: "Academic Departments",
        href: "/app/departments",
        badge: "5 Depts",
        icon: <Layers className="h-4 w-4" />,
      },
      {
        label: "Degree Programs",
        href: "/app/programs",
        icon: <Award className="h-4 w-4" />,
      },
      {
        label: "Institutional Curricula",
        href: "/app/academics/curricula",
        icon: <BookOpen className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "FACULTY & ACADEMIC OVERSIGHT",
    items: [
      {
        label: "Faculty Registry & Workloads",
        href: "/app/faculty",
        badge: "Workload",
        icon: <UserCheck className="h-4 w-4" />,
      },
      {
        label: "Total Student Body",
        href: "/app/students",
        icon: <GraduationCap className="h-4 w-4" />,
      },
      {
        label: "Attendance Policies",
        href: "/app/attendance/policies",
        icon: <ShieldAlert className="h-4 w-4" />,
      },
      {
        label: "Institutional Attendance",
        href: "/app/attendance/reports",
        badge: "88.4%",
        icon: <BarChart3 className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "STATUTORY EXAMINATIONS",
    items: [
      {
        label: "Question Bank & Publications",
        href: "/app/examinations/publications",
        badge: "Approvals",
        icon: <ShieldCheck className="h-4 w-4" />,
      },
      {
        label: "Exam Master Schedules",
        href: "/app/examinations/schedules",
        icon: <Calendar className="h-4 w-4" />,
      },
      {
        label: "Institutional Results",
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
    title: "QUALITY, SECURITY & OPERATIONS",
    items: [
      {
        label: "Accreditation & NAAC/NIRF",
        href: "/app/accreditation",
        badge: "3.62",
        icon: <Award className="h-4 w-4" />,
      },
      {
        label: "Research Grants & Patents",
        href: "/app/research",
        icon: <FlaskConical className="h-4 w-4" />,
      },
      {
        label: "Corporate Placements",
        href: "/app/placement",
        badge: "92.5%",
        icon: <Briefcase className="h-4 w-4" />,
      },
      {
        label: "Campus Security Operations",
        href: "/app/campus-security",
        icon: <ShieldAlert className="h-4 w-4" />,
      },
      {
        label: "Sustainability & ESG",
        href: "/app/sustainability",
        icon: <Leaf className="h-4 w-4" />,
      },
      {
        label: "Statutory Documents & Certs",
        href: "/app/documents",
        icon: <FileText className="h-4 w-4" />,
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

  return {
    title: "Student Portal",
    badge: "STUDENT",
    badgeClass: "bg-yellow-100 text-yellow-950 border-yellow-300 font-bold",
    glowClass: "from-yellow-400/20",
  };
}
