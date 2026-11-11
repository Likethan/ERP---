"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
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
  FileCheck2,
  DollarSign,
  Receipt,
  Briefcase,
  Building2,
  PartyPopper,
  Sparkles,
  BedDouble,
  Bus,
  FileText,
  ShieldCheck,
  Building,
  Layers,
  X,
  CreditCard,
  Gift,
  RotateCcw,
  Bot,
  Award,
  Globe,
  BarChart3,
  Bell,
  Wrench,
  DoorOpen,
  AlertCircle,
  Compass,
  MapPin,
  Truck,
  Bookmark,
  Activity,
  AlertTriangle,
  FlaskConical,
  Trophy,
  Dumbbell,
  Leaf,
  Zap,
  Droplets,
  Trash2,
  Sprout,
  Cpu,
  Timer,
  Medal,
  ShieldAlert,
  FileEdit,
  Inbox,
  Gavel,
  FolderLock,
  Scale,
  MessageSquare,
  Settings,
  Heart,
  Lock,
  Target,
  ArrowRightLeft,
  HandHeart,
  Users2,
  Clock,
  Home,
  Key,
  ClipboardCheck,
  Flame,
  Footprints,
} from "lucide-react";
import type { AuthenticatedUser } from "@campusos/types";
import { cn } from "@/lib/utils";
import {
  STUDENT_PORTAL_NAV,
  FACULTY_PORTAL_NAV,
  HOD_PORTAL_NAV,
  VICE_PRINCIPAL_PORTAL_NAV,
  ADMIN_PORTAL_NAV,
  getPortalNavSections,
  getPortalHeaderMeta,
  getNormalizedRoleSet,
  type NavLinkItem,
  type NavSection,
} from "./portal-nav";

export {
  STUDENT_PORTAL_NAV,
  FACULTY_PORTAL_NAV,
  HOD_PORTAL_NAV,
  VICE_PRINCIPAL_PORTAL_NAV,
  ADMIN_PORTAL_NAV,
  getPortalNavSections,
  getPortalHeaderMeta,
  getNormalizedRoleSet,
};
export type { NavLinkItem, NavSection };

interface SidebarProps {
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export const NAV_SECTIONS: NavSection[] = [
  {
    title: "OVERVIEW",
    items: [
      {
        label: "Dashboard",
        href: "/app/dashboard",
        roles: ["*"],
        icon: <LayoutDashboard className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "PEOPLE",
    items: [
      {
        label: "People Overview",
        href: "/app/people",
        roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL"],
        icon: <Users className="h-4 w-4" />,
      },
      {
        label: "Students",
        href: "/app/students",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
        ],
        icon: <GraduationCap className="h-4 w-4" />,
      },
      {
        label: "Faculty",
        href: "/app/faculty",
        roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL", "HOD"],
        icon: <UserCheck className="h-4 w-4" />,
      },
      {
        label: "Staff",
        href: "/app/staff",
        roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL", "HOD"],
        icon: <Briefcase className="h-4 w-4" />,
      },
      {
        label: "Workforce & HR",
        href: "/app/workforce",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "STAFF",
        ],
        icon: <Building2 className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "ACADEMICS",
    items: [
      {
        label: "Programs",
        href: "/app/programs",
        roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL", "HOD"],
        icon: <Layers className="h-4 w-4" />,
      },
      {
        label: "Academic Structure",
        href: "/app/academic-structure",
        roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL", "HOD"],
        icon: <CalendarDays className="h-4 w-4" />,
      },
      {
        label: "Subjects",
        href: "/app/academics/subjects",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
        ],
        icon: <BookOpen className="h-4 w-4" />,
      },
      {
        label: "Curricula",
        href: "/app/academics/curricula",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
        ],
        icon: <FileSpreadsheet className="h-4 w-4" />,
      },
      {
        label: "Course Offerings",
        href: "/app/academics/course-offerings",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "STUDENT",
        ],
        icon: <CheckSquare className="h-4 w-4" />,
      },
      {
        label: "Course Enrollments",
        href: "/app/academics/enrollments",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "STUDENT",
        ],
        icon: <UserCheck className="h-4 w-4" />,
      },
      {
        label: "Timetable",
        href: "/app/academics/timetable",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "STUDENT",
        ],
        icon: <Calendar className="h-4 w-4" />,
      },
      {
        label: "Library & Learning",
        href: "/app/library",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "STUDENT",
        ],
        icon: <BookOpen className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "ATTENDANCE",
    items: [
      {
        label: "Attendance Overview",
        href: "/app/attendance",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
        ],
        icon: <CheckSquare className="h-4 w-4" />,
      },
      {
        label: "Sessions",
        href: "/app/attendance/sessions",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
        ],
        icon: <Calendar className="h-4 w-4" />,
      },
      {
        label: "Records Ledger",
        href: "/app/attendance/records",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "STUDENT",
        ],
        icon: <FileSpreadsheet className="h-4 w-4" />,
      },
      {
        label: "Student 360°",
        href: "/app/attendance/students",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "STUDENT",
        ],
        icon: <GraduationCap className="h-4 w-4" />,
      },
      {
        label: "Course Registers",
        href: "/app/attendance/courses",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
        ],
        icon: <BookOpen className="h-4 w-4" />,
      },
      {
        label: "Leave Requests",
        href: "/app/attendance/leaves",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "STUDENT",
        ],
        icon: <FileCheck2 className="h-4 w-4" />,
      },
      {
        label: "Corrections",
        href: "/app/attendance/corrections",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "STUDENT",
        ],
        icon: <RotateCcw className="h-4 w-4" />,
      },
      {
        label: "Policies",
        href: "/app/attendance/policies",
        roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL", "HOD"],
        icon: <ShieldCheck className="h-4 w-4" />,
      },
      {
        label: "Reports & Audits",
        href: "/app/attendance/reports",
        roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL", "HOD"],
        icon: <FileText className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "EXAMINATIONS",
    items: [
      {
        label: "Overview",
        href: "/app/examinations",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
        ],
        icon: <Award className="h-4 w-4" />,
      },
      {
        label: "Assessments",
        href: "/app/examinations/assessments",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
        ],
        icon: <FileText className="h-4 w-4" />,
      },
      {
        label: "Exam Schedules",
        href: "/app/examinations/schedules",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "STUDENT",
        ],
        icon: <Calendar className="h-4 w-4" />,
      },
      {
        label: "Eligibility",
        href: "/app/examinations/eligibility",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "STUDENT",
        ],
        icon: <ShieldCheck className="h-4 w-4" />,
      },
      {
        label: "Marks Entry",
        href: "/app/examinations/marks",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
        ],
        icon: <FileSpreadsheet className="h-4 w-4" />,
      },
      {
        label: "Results & GPA",
        href: "/app/examinations/results",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "STUDENT",
        ],
        icon: <FileCheck2 className="h-4 w-4" />,
      },
      {
        label: "Publications",
        href: "/app/examinations/publications",
        roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL"],
        icon: <Globe className="h-4 w-4" />,
      },
      {
        label: "Exam Reports",
        href: "/app/examinations/reports",
        roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL", "HOD"],
        icon: <BarChart3 className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "FINANCE",
    items: [
      {
        label: "Finance Dashboard",
        href: "/app/finance",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "ACCOUNTS",
        ],
        icon: <DollarSign className="h-4 w-4" />,
      },
      {
        label: "Fee Categories",
        href: "/app/finance/fee-categories",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "ACCOUNTS",
        ],
        icon: <FileText className="h-4 w-4" />,
      },
      {
        label: "Fee Structures",
        href: "/app/finance/fee-structures",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "ACCOUNTS",
        ],
        icon: <Layers className="h-4 w-4" />,
      },
      {
        label: "Fee Assignments",
        href: "/app/finance/assignments",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "ACCOUNTS",
        ],
        icon: <UserCheck className="h-4 w-4" />,
      },
      {
        label: "Invoices",
        href: "/app/finance/invoices",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "ACCOUNTS",
          "STUDENT",
        ],
        icon: <CreditCard className="h-4 w-4" />,
      },
      {
        label: "Payments",
        href: "/app/finance/payments",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "ACCOUNTS",
          "STUDENT",
        ],
        icon: <DollarSign className="h-4 w-4" />,
      },
      {
        label: "Receipts",
        href: "/app/finance/receipts",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "ACCOUNTS",
          "STUDENT",
        ],
        icon: <Receipt className="h-4 w-4" />,
      },
      {
        label: "Scholarships",
        href: "/app/finance/scholarships",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "ACCOUNTS",
          "STUDENT",
        ],
        icon: <Gift className="h-4 w-4" />,
      },
      {
        label: "Refunds",
        href: "/app/finance/refunds",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "ACCOUNTS",
        ],
        icon: <RotateCcw className="h-4 w-4" />,
      },
      {
        label: "Finance Reports",
        href: "/app/finance/reports",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "ACCOUNTS",
        ],
        icon: <BarChart3 className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "PAYROLL & COMPENSATION",
    items: [
      {
        label: "Payroll Operations",
        href: "/app/payroll",
        roles: ["SUPER_ADMIN", "ADMIN", "ACCOUNTS"],
        icon: <DollarSign className="h-4 w-4 text-emerald-400" />,
      },
    ],
  },
  {
    title: "CAREER & PLACEMENT",
    items: [
      {
        label: "Operations Dashboard",
        href: "/app/placement",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "PLACEMENT_OFFICER",
          "STUDENT",
        ],
        icon: <Briefcase className="h-4 w-4" />,
      },
      {
        label: "Student Profiles",
        href: "/app/placement/students",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "PLACEMENT_OFFICER",
          "STUDENT",
        ],
        icon: <Users className="h-4 w-4" />,
      },
      {
        label: "Corporate Partners",
        href: "/app/placement/companies",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "PLACEMENT_OFFICER",
        ],
        icon: <Building2 className="h-4 w-4" />,
      },
      {
        label: "Job Drives",
        href: "/app/placement/drives",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "PLACEMENT_OFFICER",
          "STUDENT",
        ],
        icon: <CalendarDays className="h-4 w-4" />,
      },
      {
        label: "Positions",
        href: "/app/placement/positions",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "PLACEMENT_OFFICER",
          "STUDENT",
        ],
        icon: <Layers className="h-4 w-4" />,
      },
      {
        label: "Applications & Shortlist",
        href: "/app/placement/applications",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "PLACEMENT_OFFICER",
          "STUDENT",
        ],
        icon: <FileCheck2 className="h-4 w-4" />,
      },
      {
        label: "Interviews",
        href: "/app/placement/interviews",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "PLACEMENT_OFFICER",
          "STUDENT",
        ],
        icon: <Calendar className="h-4 w-4" />,
      },
      {
        label: "Job Offers",
        href: "/app/placement/offers",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "PLACEMENT_OFFICER",
          "STUDENT",
        ],
        icon: <Award className="h-4 w-4" />,
      },
      {
        label: "Placement Outcomes",
        href: "/app/placement/outcomes",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "PLACEMENT_OFFICER",
        ],
        icon: <ShieldCheck className="h-4 w-4" />,
      },
      {
        label: "Placement Reports",
        href: "/app/placement/reports",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "PLACEMENT_OFFICER",
        ],
        icon: <BarChart3 className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "CAMPUS ENGAGEMENT",
    items: [
      {
        label: "Campus Hub",
        href: "/app/campus",
        roles: ["*"],
        icon: <LayoutDashboard className="h-4 w-4" />,
      },
      {
        label: "Events & Fests",
        href: "/app/campus/events",
        roles: ["*"],
        icon: <PartyPopper className="h-4 w-4" />,
      },
      {
        label: "Registrations",
        href: "/app/campus/registrations",
        roles: ["*"],
        icon: <FileCheck2 className="h-4 w-4" />,
      },
      {
        label: "Event Attendance",
        href: "/app/campus/attendance",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
        ],
        icon: <CheckSquare className="h-4 w-4" />,
      },
      {
        label: "Clubs & Orgs",
        href: "/app/campus/clubs",
        roles: ["*"],
        icon: <Building2 className="h-4 w-4" />,
      },
      {
        label: "Announcements",
        href: "/app/campus/announcements",
        roles: ["*"],
        icon: <FileText className="h-4 w-4" />,
      },
      {
        label: "Notifications",
        href: "/app/campus/notifications",
        roles: ["*"],
        icon: <Bell className="h-4 w-4" />,
      },
      {
        label: "Preferences",
        href: "/app/campus/preferences",
        roles: ["*"],
        icon: <RotateCcw className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "COMMUNITY SERVICE & CIVIC IMPACT",
    items: [
      {
        label: "Civic Hub",
        href: "/app/engagement",
        roles: ["*"],
        icon: <HandHeart className="h-4 w-4" />,
      },
      {
        label: "Civic Programs",
        href: "/app/engagement/programs",
        roles: ["*"],
        icon: <Compass className="h-4 w-4" />,
      },
      {
        label: "Community Partners",
        href: "/app/engagement/partners",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "ENGAGEMENT_COORDINATOR",
        ],
        icon: <Users2 className="h-4 w-4" />,
      },
      {
        label: "Volunteering Roles",
        href: "/app/engagement/opportunities",
        roles: ["*"],
        icon: <Briefcase className="h-4 w-4" />,
      },
      {
        label: "Applications & Waitlist",
        href: "/app/engagement/applications",
        roles: ["*"],
        icon: <FileCheck2 className="h-4 w-4" />,
      },
      {
        label: "Shifts & Rosters",
        href: "/app/engagement/shifts",
        roles: ["*"],
        icon: <CalendarDays className="h-4 w-4" />,
      },
      {
        label: "Service Hours & Audit",
        href: "/app/engagement/service-hours",
        roles: ["*"],
        icon: <Clock className="h-4 w-4" />,
      },
      {
        label: "Reflections & SDGs",
        href: "/app/engagement/reflections",
        roles: ["*"],
        icon: <BookOpen className="h-4 w-4" />,
      },
      {
        label: "Verified Certificates",
        href: "/app/engagement/certificates",
        roles: ["*"],
        icon: <Award className="h-4 w-4" />,
      },
      {
        label: "Civic Analytics",
        href: "/app/engagement/analytics",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "STUDENT",
          "ENGAGEMENT_COORDINATOR",
        ],
        icon: <BarChart3 className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "HOUSING & OFF-CAMPUS ACCOMMODATION",
    items: [
      {
        label: "Housing Hub",
        href: "/app/housing",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "WARDEN",
          "STUDENT",
        ],
        icon: <Building2 className="h-4 w-4" />,
      },
      {
        label: "Properties",
        href: "/app/housing/properties",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "WARDEN",
          "STUDENT",
        ],
        icon: <Home className="h-4 w-4" />,
      },
      {
        label: "Providers & Landlords",
        href: "/app/housing/providers",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "WARDEN",
        ],
        icon: <ShieldCheck className="h-4 w-4" />,
      },
      {
        label: "Units & Beds",
        href: "/app/housing/inventory",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "WARDEN",
        ],
        icon: <BedDouble className="h-4 w-4" />,
      },
      {
        label: "Housing Requests",
        href: "/app/housing/requests",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "WARDEN",
          "STUDENT",
        ],
        icon: <FileText className="h-4 w-4" />,
      },
      {
        label: "Allocations & Offers",
        href: "/app/housing/allocations",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "WARDEN",
        ],
        icon: <Key className="h-4 w-4" />,
      },
      {
        label: "Leases & Agreements",
        href: "/app/housing/agreements",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "WARDEN",
          "STUDENT",
        ],
        icon: <FileCheck2 className="h-4 w-4" />,
      },
      {
        label: "Check-In / Out",
        href: "/app/housing/check-in-out",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "WARDEN",
        ],
        icon: <ClipboardCheck className="h-4 w-4" />,
      },
      {
        label: "Safety & Inspections",
        href: "/app/housing/inspections",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "WARDEN",
        ],
        icon: <ShieldAlert className="h-4 w-4" />,
      },
      {
        label: "Maintenance Tickets",
        href: "/app/housing/maintenance",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "WARDEN",
          "STUDENT",
        ],
        icon: <Wrench className="h-4 w-4" />,
      },
      {
        label: "Housing Analytics",
        href: "/app/housing/analytics",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "WARDEN",
        ],
        icon: <BarChart3 className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "SUSTAINABILITY & CARBON INTELLIGENCE",
    items: [
      {
        label: "Sustainability Hub",
        href: "/app/sustainability",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "SUSTAINABILITY_COORDINATOR",
        ],
        icon: <Leaf className="h-4 w-4 text-emerald-400" />,
      },
      {
        label: "Targets & Goals",
        href: "/app/sustainability/targets",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "SUSTAINABILITY_COORDINATOR",
        ],
        icon: <Target className="h-4 w-4" />,
      },
      {
        label: "Energy & Grid",
        href: "/app/sustainability/energy",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "SUSTAINABILITY_COORDINATOR",
        ],
        icon: <Zap className="h-4 w-4" />,
      },
      {
        label: "Water Resources",
        href: "/app/sustainability/water",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "SUSTAINABILITY_COORDINATOR",
        ],
        icon: <Droplets className="h-4 w-4" />,
      },
      {
        label: "Waste & Circularity",
        href: "/app/sustainability/waste",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "SUSTAINABILITY_COORDINATOR",
        ],
        icon: <Trash2 className="h-4 w-4" />,
      },
      {
        label: "Carbon Accounting",
        href: "/app/sustainability/carbon",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "SUSTAINABILITY_COORDINATOR",
        ],
        icon: <Activity className="h-4 w-4" />,
      },
      {
        label: "Green Initiatives",
        href: "/app/sustainability/initiatives",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "SUSTAINABILITY_COORDINATOR",
          "FACULTY",
          "STUDENT",
        ],
        icon: <Sprout className="h-4 w-4" />,
      },
      {
        label: "Statutory Compliance",
        href: "/app/sustainability/compliance",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "SUSTAINABILITY_COORDINATOR",
        ],
        icon: <ShieldCheck className="h-4 w-4" />,
      },
      {
        label: "IoT Smart Meters",
        href: "/app/sustainability/iot-meters",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "SUSTAINABILITY_COORDINATOR",
        ],
        icon: <Cpu className="h-4 w-4" />,
      },
      {
        label: "Invoice Reconciliation",
        href: "/app/sustainability/imports",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "ACCOUNTS",
          "SUSTAINABILITY_COORDINATOR",
        ],
        icon: <FileSpreadsheet className="h-4 w-4" />,
      },
      {
        label: "Decarb Analytics",
        href: "/app/sustainability/analytics",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "SUSTAINABILITY_COORDINATOR",
        ],
        icon: <BarChart3 className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "CAMPUS SECURITY & ACCESS CONTROL",
    items: [
      {
        label: "Security Command Hub",
        href: "/app/campus-security",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "SECURITY_OFFICER",
        ],
        icon: <ShieldAlert className="h-4 w-4 text-red-400" />,
      },
      {
        label: "Visitor Directory",
        href: "/app/campus-security/visitors",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "STUDENT",
          "SECURITY_OFFICER",
        ],
        icon: <Users className="h-4 w-4" />,
      },
      {
        label: "Gate Operations",
        href: "/app/campus-security/gate-operations",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "SECURITY_OFFICER",
        ],
        icon: <DoorOpen className="h-4 w-4" />,
      },
      {
        label: "Contractor Access",
        href: "/app/campus-security/contractors",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "SECURITY_OFFICER",
        ],
        icon: <UserCheck className="h-4 w-4" />,
      },
      {
        label: "Security Zones",
        href: "/app/campus-security/zones",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "SECURITY_OFFICER",
        ],
        icon: <Layers className="h-4 w-4" />,
      },
      {
        label: "Access Grants",
        href: "/app/campus-security/access-grants",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "SECURITY_OFFICER",
        ],
        icon: <Key className="h-4 w-4" />,
      },
      {
        label: "Physical Incidents",
        href: "/app/campus-security/incidents",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "STUDENT",
          "SECURITY_OFFICER",
        ],
        icon: <AlertTriangle className="h-4 w-4" />,
      },
      {
        label: "Emergency Response",
        href: "/app/campus-security/emergency",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "SECURITY_OFFICER",
        ],
        icon: <Flame className="h-4 w-4 text-amber-400" />,
      },
      {
        label: "Patrol Rounds",
        href: "/app/campus-security/patrols",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "SECURITY_OFFICER",
        ],
        icon: <Footprints className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "INTERNATIONAL & MOBILITY",
    items: [
      {
        label: "International Relations",
        href: "/app/international",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "INTERNATIONAL_OFFICER",
        ],
        icon: <Globe className="h-4 w-4 text-cyan-400" />,
      },
      {
        label: "Partner Institutions",
        href: "/app/international/partners",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "INTERNATIONAL_OFFICER",
        ],
        icon: <Building2 className="h-4 w-4" />,
      },
      {
        label: "MoUs & Agreements",
        href: "/app/international/agreements",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "INTERNATIONAL_OFFICER",
        ],
        icon: <FileText className="h-4 w-4" />,
      },
      {
        label: "Mobility Programs",
        href: "/app/international/programs",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "STUDENT",
          "INTERNATIONAL_OFFICER",
        ],
        icon: <Compass className="h-4 w-4" />,
      },
      {
        label: "Student Applications",
        href: "/app/international/applications",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "STUDENT",
          "INTERNATIONAL_OFFICER",
        ],
        icon: <FileEdit className="h-4 w-4" />,
      },
      {
        label: "Application Reviews",
        href: "/app/international/applications/review",
        icon: <ShieldCheck className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "INTERNATIONAL_OFFICER",
        ],
      },
      {
        label: "Partner Nominations",
        href: "/app/international/nominations",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "INTERNATIONAL_OFFICER",
        ],
        icon: <CheckSquare className="h-4 w-4" />,
      },
      {
        label: "Inbound Scholars",
        href: "/app/international/inbound",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "INTERNATIONAL_OFFICER",
        ],
        icon: <DoorOpen className="h-4 w-4" />,
      },
      {
        label: "Outbound Mobility",
        href: "/app/international/outbound",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "STUDENT",
          "FACULTY",
          "INTERNATIONAL_OFFICER",
        ],
        icon: <MapPin className="h-4 w-4" />,
      },
      {
        label: "Faculty Exchange",
        href: "/app/international/faculty-exchange",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "INTERNATIONAL_OFFICER",
        ],
        icon: <UserCheck className="h-4 w-4" />,
      },
      {
        label: "Credit Transfer",
        href: "/app/international/credit-transfer",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "STUDENT",
          "INTERNATIONAL_OFFICER",
        ],
        icon: <Scale className="h-4 w-4" />,
      },
      {
        label: "Travel Grants & Scholarships",
        href: "/app/international/scholarships",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "STUDENT",
          "FACULTY",
          "INTERNATIONAL_OFFICER",
        ],
        icon: <Award className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "SPORTS & ATHLETICS",
    items: [
      {
        label: "Sports Overview",
        href: "/app/sports",
        roles: ["*"],
        icon: <Trophy className="h-4 w-4 text-amber-400" />,
      },
      {
        label: "Departments",
        href: "/app/sports/departments",
        icon: <Building2 className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "SPORTS_OFFICER",
        ],
      },
      {
        label: "Facilities & Courts",
        href: "/app/sports/facilities",
        roles: ["*"],
        icon: <DoorOpen className="h-4 w-4" />,
      },
      {
        label: "Facility Calendar",
        href: "/app/sports/calendar",
        roles: ["*"],
        icon: <Calendar className="h-4 w-4" />,
      },
      {
        label: "Student Athletes",
        href: "/app/sports/participants",
        roles: ["*"],
        icon: <Users className="h-4 w-4" />,
      },
      {
        label: "Teams & Rosters",
        href: "/app/sports/teams",
        roles: ["*"],
        icon: <ShieldCheck className="h-4 w-4 text-indigo-400" />,
      },
      {
        label: "Coaches & Officials",
        href: "/app/sports/coaches",
        icon: <UserCheck className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "SPORTS_OFFICER",
          "COACH",
        ],
      },
      {
        label: "Training Programs",
        href: "/app/sports/training",
        roles: ["*"],
        icon: <Dumbbell className="h-4 w-4 text-emerald-400" />,
      },
      {
        label: "Training Schedule",
        href: "/app/sports/training/schedule",
        roles: ["*"],
        icon: <CalendarDays className="h-4 w-4" />,
      },
      {
        label: "Competitions",
        href: "/app/sports/competitions",
        roles: ["*"],
        icon: <Trophy className="h-4 w-4 text-amber-500" />,
      },
      {
        label: "Fixtures & Matches",
        href: "/app/sports/fixtures",
        roles: ["*"],
        icon: <Timer className="h-4 w-4 text-blue-400" />,
      },
      {
        label: "Results & Standings",
        href: "/app/sports/results",
        roles: ["*"],
        icon: <CheckSquare className="h-4 w-4 text-emerald-400" />,
      },
      {
        label: "Achievements",
        href: "/app/sports/achievements",
        roles: ["*"],
        icon: <Medal className="h-4 w-4 text-amber-400" />,
      },
      {
        label: "Equipment & Gear",
        href: "/app/sports/equipment",
        roles: ["*"],
        icon: <Wrench className="h-4 w-4" />,
      },
      {
        label: "Registrations & Fees",
        href: "/app/sports/fees",
        icon: <CreditCard className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "ACCOUNTS",
          "SPORTS_OFFICER",
        ],
      },
      {
        label: "Sports Analytics",
        href: "/app/sports/reports",
        icon: <BarChart3 className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "SPORTS_OFFICER",
        ],
      },
      {
        label: "Sports Policies",
        href: "/app/sports/config",
        icon: <BookOpen className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "SPORTS_OFFICER",
        ],
      },
    ],
  },
  {
    title: "STUDENT AFFAIRS & GRIEVANCES",
    items: [
      {
        label: "Student Affairs Hub",
        href: "/app/student-affairs",
        roles: ["*"],
        icon: <ShieldAlert className="h-4 w-4" />,
      },
      {
        label: "Submit Grievance",
        href: "/app/student-affairs/submit",
        roles: ["*"],
        icon: <FileEdit className="h-4 w-4" />,
      },
      {
        label: "My Cases",
        href: "/app/student-affairs/my-cases",
        roles: ["*"],
        icon: <UserCheck className="h-4 w-4" />,
      },
      {
        label: "Case Intake Queue",
        href: "/app/student-affairs/intake",
        icon: <Inbox className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "STUDENT_AFFAIRS_ADMIN",
          "CASE_OFFICER",
        ],
      },
      {
        label: "Assignments",
        href: "/app/student-affairs/assignments",
        icon: <Users className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "STUDENT_AFFAIRS_ADMIN",
          "CASE_OFFICER",
        ],
      },
      {
        label: "Disciplinary Cases",
        href: "/app/student-affairs/disciplinary",
        icon: <Gavel className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "STUDENT_AFFAIRS_ADMIN",
          "CASE_OFFICER",
          "INVESTIGATOR",
        ],
      },
      {
        label: "Evidence Review",
        href: "/app/student-affairs/evidence",
        icon: <FolderLock className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "STUDENT_AFFAIRS_ADMIN",
          "CASE_OFFICER",
          "INVESTIGATOR",
        ],
      },
      {
        label: "Hearings & Calendar",
        href: "/app/student-affairs/meetings",
        roles: ["*"],
        icon: <Calendar className="h-4 w-4" />,
      },
      {
        label: "Resolutions & Actions",
        href: "/app/student-affairs/resolutions",
        roles: ["*"],
        icon: <CheckSquare className="h-4 w-4" />,
      },
      {
        label: "Appeals & Reviews",
        href: "/app/student-affairs/appeals",
        roles: ["*"],
        icon: <Scale className="h-4 w-4" />,
      },
      {
        label: "Communications",
        href: "/app/student-affairs/communications",
        roles: ["*"],
        icon: <MessageSquare className="h-4 w-4" />,
      },
      {
        label: "Urgent Escalations",
        href: "/app/student-affairs/escalations",
        icon: <AlertTriangle className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "STUDENT_AFFAIRS_ADMIN",
          "CASE_OFFICER",
        ],
      },
      {
        label: "Policies & Standards",
        href: "/app/student-affairs/policies",
        roles: ["*"],
        icon: <BookOpen className="h-4 w-4" />,
      },
      {
        label: "Case Analytics",
        href: "/app/student-affairs/reports",
        icon: <BarChart3 className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "STUDENT_AFFAIRS_ADMIN",
        ],
      },
      {
        label: "Affairs Config",
        href: "/app/student-affairs/config",
        icon: <Settings className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "STUDENT_AFFAIRS_ADMIN",
        ],
      },
    ],
  },
  {
    title: "COUNSELLING & MENTORING",
    items: [
      {
        label: "Support Hub",
        href: "/app/student-support",
        roles: ["*"],
        icon: <LayoutDashboard className="h-4 w-4" />,
      },
      {
        label: "My Mentor",
        href: "/app/student-support/mentor",
        icon: <UserCheck className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "STUDENT",
        ],
      },
      {
        label: "Mentor Allocations",
        href: "/app/student-support/assignments",
        icon: <Users className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "STUDENT_SUPPORT_ADMIN",
        ],
      },
      {
        label: "Mentee Directory",
        href: "/app/student-support/mentees",
        icon: <GraduationCap className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "STUDENT_SUPPORT_ADMIN",
        ],
      },
      {
        label: "Book Counselling",
        href: "/app/student-support/counselling",
        roles: ["*"],
        icon: <Heart className="h-4 w-4" />,
      },
      {
        label: "Counselling Schedule",
        href: "/app/student-support/counselling/schedule",
        icon: <Calendar className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "COUNSELLOR",
          "STUDENT_SUPPORT_ADMIN",
        ],
      },
      {
        label: "Restricted Workspace",
        href: "/app/student-support/counselling/workspace",
        icon: <Lock className="h-4 w-4" />,
        badge: "Restricted",
        roles: ["COUNSELLOR", "STUDENT_SUPPORT_ADMIN"],
      },
      {
        label: "Mentoring Sessions",
        href: "/app/student-support/sessions",
        icon: <MessageSquare className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "STUDENT",
          "STUDENT_SUPPORT_ADMIN",
        ],
      },
      {
        label: "Development Plans",
        href: "/app/student-support/development-plans",
        icon: <Sparkles className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "STUDENT",
          "STUDENT_SUPPORT_ADMIN",
        ],
      },
      {
        label: "Goals & Milestones",
        href: "/app/student-support/goals",
        icon: <Target className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "STUDENT",
          "STUDENT_SUPPORT_ADMIN",
        ],
      },
      {
        label: "Support Referrals",
        href: "/app/student-support/referrals",
        icon: <ArrowRightLeft className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "COUNSELLOR",
          "STUDENT_SUPPORT_ADMIN",
        ],
      },
      {
        label: "Guidance Timeline",
        href: "/app/student-support/guidance",
        roles: ["*"],
        icon: <BookOpen className="h-4 w-4" />,
      },
      {
        label: "Follow-Up Tasks",
        href: "/app/student-support/follow-ups",
        icon: <CheckSquare className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "COUNSELLOR",
          "STUDENT_SUPPORT_ADMIN",
        ],
      },
      {
        label: "Support Analytics",
        href: "/app/student-support/analytics",
        icon: <BarChart3 className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "STUDENT_SUPPORT_ADMIN",
        ],
      },
      {
        label: "Support Policies",
        href: "/app/student-support/config",
        icon: <Settings className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "STUDENT_SUPPORT_ADMIN",
        ],
      },
    ],
  },
  {
    title: "INFRASTRUCTURE",
    items: [
      {
        label: "Infrastructure Overview",
        href: "/app/infrastructure",
        icon: <LayoutDashboard className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "WARDEN",
          "TRANSPORT_OFFICER",
          "FACILITY_OFFICER",
        ],
      },
      {
        label: "Hostel",
        href: "/app/infrastructure/hostel",
        icon: <BedDouble className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "WARDEN",
        ],
      },
      {
        label: "Rooms & Beds",
        href: "/app/infrastructure/hostel/rooms",
        icon: <DoorOpen className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "WARDEN",
        ],
      },
      {
        label: "Allocations",
        href: "/app/infrastructure/hostel/allocations",
        icon: <UserCheck className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "WARDEN",
        ],
      },
      {
        label: "Hostel Leaves",
        href: "/app/infrastructure/hostel/leaves",
        icon: <FileCheck2 className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "WARDEN",
          "STUDENT",
        ],
      },
      {
        label: "Complaints",
        href: "/app/infrastructure/hostel/complaints",
        icon: <AlertCircle className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "WARDEN",
          "STUDENT",
        ],
      },
      {
        label: "Transport",
        href: "/app/infrastructure/transport",
        icon: <Bus className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "TRANSPORT_OFFICER",
        ],
      },
      {
        label: "Routes",
        href: "/app/infrastructure/transport/routes",
        icon: <Compass className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "TRANSPORT_OFFICER",
        ],
      },
      {
        label: "Stops",
        href: "/app/infrastructure/transport/stops",
        icon: <MapPin className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "TRANSPORT_OFFICER",
        ],
      },
      {
        label: "Vehicles",
        href: "/app/infrastructure/transport/vehicles",
        icon: <Truck className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "TRANSPORT_OFFICER",
        ],
      },
      {
        label: "Drivers",
        href: "/app/infrastructure/transport/drivers",
        icon: <Users className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "TRANSPORT_OFFICER",
        ],
      },
      {
        label: "Transport Allocations",
        href: "/app/infrastructure/transport/allocations",
        icon: <CreditCard className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "TRANSPORT_OFFICER",
        ],
      },
      {
        label: "Facilities",
        href: "/app/infrastructure/facilities",
        icon: <Building2 className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACILITY_OFFICER",
        ],
      },
      {
        label: "Maintenance",
        href: "/app/infrastructure/maintenance",
        icon: <Wrench className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACILITY_OFFICER",
          "WARDEN",
          "STUDENT",
        ],
      },
      {
        label: "Infrastructure Reports",
        href: "/app/infrastructure/reports",
        icon: <BarChart3 className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "WARDEN",
          "TRANSPORT_OFFICER",
          "FACILITY_OFFICER",
        ],
      },
    ],
  },
  {
    title: "DOCUMENTS & DIGITAL RECORDS",
    items: [
      {
        label: "Operations Dashboard",
        href: "/app/documents",
        icon: <LayoutDashboard className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "WARDEN",
          "ACCOUNTS",
          "PLACEMENT_OFFICER",
          "TRANSPORT_OFFICER",
          "FACILITY_OFFICER",
        ],
      },
      {
        label: "My Documents",
        href: "/app/documents/my-documents",
        roles: ["*"],
        icon: <FileText className="h-4 w-4" />,
      },
      {
        label: "All Documents",
        href: "/app/documents/all",
        icon: <Layers className="h-4 w-4" />,
        roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL", "HOD"],
      },
      {
        label: "Verification Queue",
        href: "/app/documents/verification",
        icon: <ShieldCheck className="h-4 w-4" />,
        roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL", "HOD"],
      },
      {
        label: "Categories",
        href: "/app/documents/categories",
        icon: <Layers className="h-4 w-4" />,
        roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL", "HOD"],
      },
      {
        label: "Certificate Center",
        href: "/app/documents/certificates",
        roles: ["*"],
        icon: <Award className="h-4 w-4" />,
      },
      {
        label: "Certificate Templates",
        href: "/app/documents/certificates/templates",
        icon: <FileCheck2 className="h-4 w-4" />,
        roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL", "HOD"],
      },
      {
        label: "Certificate Requests",
        href: "/app/documents/certificates/requests",
        icon: <FileText className="h-4 w-4" />,
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "STUDENT",
        ],
      },
      {
        label: "Institutional Records",
        href: "/app/documents/institutional-records",
        icon: <Building className="h-4 w-4" />,
        roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL", "HOD"],
      },
      {
        label: "Document Reports",
        href: "/app/documents/reports",
        icon: <BarChart3 className="h-4 w-4" />,
        roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL", "HOD"],
      },
      {
        label: "Knowledge & Policies",
        href: "/app/knowledge",
        roles: ["*"],
        icon: <BookOpen className="h-4 w-4" />,
      },
    ],
  },
  {
    title: "INTELLIGENCE",
    items: [
      {
        label: "Overview",
        href: "/app/intelligence",
        roles: ["*"],
        icon: <Sparkles className="h-4 w-4 text-blue-500" />,
      },
      {
        label: "AI Assistant",
        href: "/app/intelligence/assistant",
        roles: ["*"],
        icon: <Bot className="h-4 w-4 text-indigo-500" />,
      },
      {
        label: "Insights",
        href: "/app/intelligence/insights",
        roles: ["*"],
        icon: <Sparkles className="h-4 w-4 text-amber-500" />,
      },
      {
        label: "Analytics",
        href: "/app/intelligence/analytics",
        roles: ["*"],
        icon: <BarChart3 className="h-4 w-4 text-emerald-500" />,
      },
      {
        label: "Alerts",
        href: "/app/intelligence/alerts",
        roles: ["*"],
        icon: <AlertTriangle className="h-4 w-4 text-rose-500" />,
      },
      {
        label: "Saved Insights",
        href: "/app/intelligence/saved",
        roles: ["*"],
        icon: <Bookmark className="h-4 w-4 text-purple-500" />,
      },
      {
        label: "AI Activity & Tools",
        href: "/app/intelligence/activity",
        icon: <Activity className="h-4 w-4 text-slate-500" />,
        roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL", "HOD"],
      },
    ],
  },
  {
    title: "SYSTEM GOVERNANCE",
    items: [
      {
        label: "Institution",
        href: "/app/institution",
        roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL"],
        icon: <Building className="h-4 w-4" />,
      },
      {
        label: "Campuses",
        href: "/app/campuses",
        roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL"],
        icon: <Building2 className="h-4 w-4" />,
      },
      {
        label: "Departments",
        href: "/app/departments",
        roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL", "HOD"],
        icon: <Layers className="h-4 w-4" />,
      },
      {
        label: "Security & IAM",
        href: "/app/security",
        roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL"],
        icon: <ShieldCheck className="h-4 w-4" />,
      },
      {
        label: "Accreditation & IQAC",
        href: "/app/accreditation",
        roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL", "HOD"],
        icon: <Award className="h-4 w-4 text-amber-400" />,
      },
      {
        label: "Research & Grants",
        href: "/app/research",
        roles: [
          "SUPER_ADMIN",
          "ADMIN",
          "PRINCIPAL",
          "VICE_PRINCIPAL",
          "HOD",
          "FACULTY",
          "STUDENT",
        ],
        icon: <FlaskConical className="h-4 w-4 text-emerald-400" />,
      },
    ],
  },
];

export function isPathAuthorized(
  pathname: string,
  user: AuthenticatedUser | null,
): boolean {
  if (!user) return true; // Let layout handle redirect to login
  const roleSet = getNormalizedRoleSet(user);
  if (roleSet.has("SUPER_ADMIN") || roleSet.has("ADMIN")) return true;
  if (pathname === "/app/dashboard") return true;

  // Standalone admin-only modules
  const adminOnlyPrefixes = [
    "/app/marketplace",
    "/app/adoption",
    "/app/subscriptions",
    "/app/data-import",
    "/app/records-lifecycle",
    "/app/legal",
  ];
  if (
    adminOnlyPrefixes.some(
      (p) => pathname === p || pathname.startsWith(p + "/"),
    )
  ) {
    return false;
  }

  // Find matching nav item: match exact href first, then longest matching prefix for subroutes
  const allItems: NavLinkItem[] = [];
  for (const section of NAV_SECTIONS) {
    for (const item of section.items) {
      allItems.push(item);
    }
  }

  const exactMatch = allItems.find((item) => item.href === pathname);
  if (exactMatch) {
    if (!exactMatch.roles || exactMatch.roles.includes("*")) return true;
    return exactMatch.roles.some((r) => roleSet.has(r));
  }

  const prefixMatches = allItems
    .filter((item) => pathname.startsWith(item.href + "/"))
    .sort((a, b) => b.href.length - a.href.length);

  if (prefixMatches.length > 0) {
    const bestMatch = prefixMatches[0];
    if (!bestMatch.roles || bestMatch.roles.includes("*")) return true;
    return bestMatch.roles.some((r) => roleSet.has(r));
  }

  return true;
}

export function Sidebar({ mobileOpen, onCloseMobile }: SidebarProps) {
  const pathname = usePathname();
  const { user } = useAuth();
  const portalSections = getPortalNavSections(user);
  const portalMeta = getPortalHeaderMeta(user);

  const sidebarContent = (
    <div className="flex h-full flex-col bg-white border-r border-slate-200 text-slate-800">
      {/* Brand Header with Role-Specific Portal Identity */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-slate-200">
        <Link href="/app/dashboard" className="flex items-center gap-3 min-w-0">
          <div className="relative h-10 w-10 shrink-0">
            <Image
              src="/college-logo.jpg"
              alt="V.S.B. Engineering College"
              fill
              className="object-contain rounded-md"
              priority
            />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="text-sm font-bold tracking-tight text-slate-900 truncate">
                CampusOS
              </span>
              <span
                suppressHydrationWarning
                className={cn(
                  "rounded px-1.5 py-0.2 text-[9px] font-mono font-bold uppercase border shrink-0",
                  portalMeta.badgeClass,
                )}
              >
                {portalMeta.badge}
              </span>
            </div>
            <div
              suppressHydrationWarning
              className="text-[10px] text-slate-500 tracking-wider uppercase font-semibold truncate"
            >
              {portalMeta.title}
            </div>
          </div>
        </Link>
        {onCloseMobile && (
          <button
            onClick={onCloseMobile}
            className="lg:hidden rounded-lg p-1.5 text-slate-400 hover:text-slate-800 hover:bg-yellow-50"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Role-Specific Portal Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {portalSections.map((section, sIdx) => {
          if (!section.items || section.items.length === 0) return null;

          return (
            <div key={section.title || sIdx} className="space-y-1">
              <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                {section.title}
              </div>
              {section.items.map((item, itemIdx) => {
                const isActive =
                  item.href === "/app/dashboard"
                    ? pathname === "/app/dashboard"
                    : pathname.startsWith(item.href);

                return (
                  <Link
                    key={`${section.title}-${item.href}-${item.label || itemIdx}`}
                    href={item.href}
                    prefetch={false}
                    onClick={onCloseMobile}
                    className={cn(
                      "flex items-center justify-between rounded-lg px-3 py-2 text-xs font-medium transition-colors group",
                      isActive
                        ? "bg-yellow-400 text-slate-950 shadow-xs font-bold"
                        : "text-slate-600 hover:bg-yellow-50 hover:text-slate-950",
                    )}
                  >
                    <div className="flex items-center gap-2.5">
                      <span
                        className={cn(
                          "transition-colors",
                          isActive
                            ? "text-slate-950"
                            : "text-slate-400 group-hover:text-slate-800",
                        )}
                      >
                        {item.icon}
                      </span>
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span
                        className={cn(
                          "rounded-full px-1.5 py-0.2 text-[9px] font-mono",
                          isActive
                            ? "bg-yellow-500/30 text-slate-950 border border-yellow-600/30 font-semibold"
                            : "bg-slate-100 text-slate-600 border border-slate-200",
                        )}
                      >
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          );
        })}
      </nav>

      {/* Tenant Context Footer */}
      <div className="p-3.5 border-t border-slate-200 bg-yellow-50/40">
        <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-xs">
          <div className="text-[10px] uppercase font-bold tracking-wider text-slate-500 mb-1 flex items-center justify-between">
            <span>Tenant Scope</span>
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          </div>
          <div className="text-xs font-semibold text-slate-900 truncate">
            {user?.tenant?.name || "Vidyasagar State University"}
          </div>
          <div className="text-[10px] text-slate-500 font-mono mt-0.5 truncate">
            CODE: {user?.tenant?.code || "VSB-CAMPUS"}
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <aside className="hidden lg:block w-64 shrink-0 h-screen sticky top-0 overflow-hidden z-20">
        {sidebarContent}
      </aside>

      {/* Mobile Drawer Sidebar */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="fixed inset-0 bg-slate-950/40 backdrop-blur-xs animate-fade-in"
            onClick={onCloseMobile}
          />
          <div className="fixed inset-y-0 left-0 w-72 max-w-[85vw] shadow-2xl animate-slide-right z-10">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
}
