"use client";

import React from "react";
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
import { cn } from "@/lib/utils";

interface NavLinkItem {
  label: string;
  href: string;
  icon: React.ReactNode;
  badge?: string;
  roles?: string[];
}

interface NavSection {
  title: string;
  items: NavLinkItem[];
}

interface SidebarProps {
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export function Sidebar({ mobileOpen, onCloseMobile }: SidebarProps) {
  const pathname = usePathname();
  const { user } = useAuth();

  const NAV_SECTIONS: NavSection[] = [
    {
      title: "OVERVIEW",
      items: [
        {
          label: "Dashboard",
          href: "/app/dashboard",
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
          icon: <Users className="h-4 w-4" />,
        },
        {
          label: "Students",
          href: "/app/students",
          icon: <GraduationCap className="h-4 w-4" />,
        },
        {
          label: "Faculty",
          href: "/app/faculty",
          icon: <UserCheck className="h-4 w-4" />,
        },
        {
          label: "Staff",
          href: "/app/staff",
          icon: <Briefcase className="h-4 w-4" />,
        },
        {
          label: "Workforce & HR",
          href: "/app/workforce",
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
          icon: <Layers className="h-4 w-4" />,
        },
        {
          label: "Academic Structure",
          href: "/app/academic-structure",
          icon: <CalendarDays className="h-4 w-4" />,
        },
        {
          label: "Subjects",
          href: "/app/academics/subjects",
          icon: <BookOpen className="h-4 w-4" />,
        },
        {
          label: "Curricula",
          href: "/app/academics/curricula",
          icon: <FileSpreadsheet className="h-4 w-4" />,
        },
        {
          label: "Course Offerings",
          href: "/app/academics/course-offerings",
          icon: <CheckSquare className="h-4 w-4" />,
        },
        {
          label: "Course Enrollments",
          href: "/app/academics/enrollments",
          icon: <UserCheck className="h-4 w-4" />,
        },
        {
          label: "Timetable",
          href: "/app/academics/timetable",
          icon: <Calendar className="h-4 w-4" />,
        },
        {
          label: "Library & Learning",
          href: "/app/library",
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
          icon: <CheckSquare className="h-4 w-4" />,
        },
        {
          label: "Sessions",
          href: "/app/attendance/sessions",
          icon: <Calendar className="h-4 w-4" />,
        },
        {
          label: "Records Ledger",
          href: "/app/attendance/records",
          icon: <FileSpreadsheet className="h-4 w-4" />,
        },
        {
          label: "Student 360°",
          href: "/app/attendance/students",
          icon: <GraduationCap className="h-4 w-4" />,
        },
        {
          label: "Course Registers",
          href: "/app/attendance/courses",
          icon: <BookOpen className="h-4 w-4" />,
        },
        {
          label: "Leave Requests",
          href: "/app/attendance/leaves",
          icon: <FileCheck2 className="h-4 w-4" />,
        },
        {
          label: "Corrections",
          href: "/app/attendance/corrections",
          icon: <RotateCcw className="h-4 w-4" />,
        },
        {
          label: "Policies",
          href: "/app/attendance/policies",
          icon: <ShieldCheck className="h-4 w-4" />,
        },
        {
          label: "Reports & Audits",
          href: "/app/attendance/reports",
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
          icon: <Award className="h-4 w-4" />,
        },
        {
          label: "Assessments",
          href: "/app/examinations/assessments",
          icon: <FileText className="h-4 w-4" />,
        },
        {
          label: "Exam Schedules",
          href: "/app/examinations/schedules",
          icon: <Calendar className="h-4 w-4" />,
        },
        {
          label: "Eligibility",
          href: "/app/examinations/eligibility",
          icon: <ShieldCheck className="h-4 w-4" />,
        },
        {
          label: "Marks Entry",
          href: "/app/examinations/marks",
          icon: <FileSpreadsheet className="h-4 w-4" />,
        },
        {
          label: "Results & GPA",
          href: "/app/examinations/results",
          icon: <FileCheck2 className="h-4 w-4" />,
        },
        {
          label: "Publications",
          href: "/app/examinations/publications",
          icon: <Globe className="h-4 w-4" />,
        },
        {
          label: "Exam Reports",
          href: "/app/examinations/reports",
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
          icon: <DollarSign className="h-4 w-4" />,
        },
        {
          label: "Fee Categories",
          href: "/app/finance/fee-categories",
          icon: <FileText className="h-4 w-4" />,
        },
        {
          label: "Fee Structures",
          href: "/app/finance/fee-structures",
          icon: <Layers className="h-4 w-4" />,
        },
        {
          label: "Fee Assignments",
          href: "/app/finance/assignments",
          icon: <UserCheck className="h-4 w-4" />,
        },
        {
          label: "Invoices",
          href: "/app/finance/invoices",
          icon: <CreditCard className="h-4 w-4" />,
        },
        {
          label: "Payments",
          href: "/app/finance/payments",
          icon: <DollarSign className="h-4 w-4" />,
        },
        {
          label: "Receipts",
          href: "/app/finance/receipts",
          icon: <Receipt className="h-4 w-4" />,
        },
        {
          label: "Scholarships",
          href: "/app/finance/scholarships",
          icon: <Gift className="h-4 w-4" />,
        },
        {
          label: "Refunds",
          href: "/app/finance/refunds",
          icon: <RotateCcw className="h-4 w-4" />,
        },
        {
          label: "Finance Reports",
          href: "/app/finance/reports",
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
          icon: <Briefcase className="h-4 w-4" />,
        },
        {
          label: "Student Profiles",
          href: "/app/placement/students",
          icon: <Users className="h-4 w-4" />,
        },
        {
          label: "Corporate Partners",
          href: "/app/placement/companies",
          icon: <Building2 className="h-4 w-4" />,
        },
        {
          label: "Job Drives",
          href: "/app/placement/drives",
          icon: <CalendarDays className="h-4 w-4" />,
        },
        {
          label: "Positions",
          href: "/app/placement/positions",
          icon: <Layers className="h-4 w-4" />,
        },
        {
          label: "Applications & Shortlist",
          href: "/app/placement/applications",
          icon: <FileCheck2 className="h-4 w-4" />,
        },
        {
          label: "Interviews",
          href: "/app/placement/interviews",
          icon: <Calendar className="h-4 w-4" />,
        },
        {
          label: "Job Offers",
          href: "/app/placement/offers",
          icon: <Award className="h-4 w-4" />,
        },
        {
          label: "Placement Outcomes",
          href: "/app/placement/outcomes",
          icon: <ShieldCheck className="h-4 w-4" />,
        },
        {
          label: "Placement Reports",
          href: "/app/placement/reports",
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
          icon: <LayoutDashboard className="h-4 w-4" />,
        },
        {
          label: "Events & Fests",
          href: "/app/campus/events",
          icon: <PartyPopper className="h-4 w-4" />,
        },
        {
          label: "Registrations",
          href: "/app/campus/registrations",
          icon: <FileCheck2 className="h-4 w-4" />,
        },
        {
          label: "Event Attendance",
          href: "/app/campus/attendance",
          icon: <CheckSquare className="h-4 w-4" />,
        },
        {
          label: "Clubs & Orgs",
          href: "/app/campus/clubs",
          icon: <Building2 className="h-4 w-4" />,
        },
        {
          label: "Announcements",
          href: "/app/campus/announcements",
          icon: <FileText className="h-4 w-4" />,
        },
        {
          label: "Notifications",
          href: "/app/campus/notifications",
          icon: <Bell className="h-4 w-4" />,
        },
        {
          label: "Preferences",
          href: "/app/campus/preferences",
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
          icon: <HandHeart className="h-4 w-4" />,
        },
        {
          label: "Civic Programs",
          href: "/app/engagement/programs",
          icon: <Compass className="h-4 w-4" />,
        },
        {
          label: "Community Partners",
          href: "/app/engagement/partners",
          icon: <Users2 className="h-4 w-4" />,
        },
        {
          label: "Volunteering Roles",
          href: "/app/engagement/opportunities",
          icon: <Briefcase className="h-4 w-4" />,
        },
        {
          label: "Applications & Waitlist",
          href: "/app/engagement/applications",
          icon: <FileCheck2 className="h-4 w-4" />,
        },
        {
          label: "Shifts & Rosters",
          href: "/app/engagement/shifts",
          icon: <CalendarDays className="h-4 w-4" />,
        },
        {
          label: "Service Hours & Audit",
          href: "/app/engagement/service-hours",
          icon: <Clock className="h-4 w-4" />,
        },
        {
          label: "Reflections & SDGs",
          href: "/app/engagement/reflections",
          icon: <BookOpen className="h-4 w-4" />,
        },
        {
          label: "Verified Certificates",
          href: "/app/engagement/certificates",
          icon: <Award className="h-4 w-4" />,
        },
        {
          label: "Civic Analytics",
          href: "/app/engagement/analytics",
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
          icon: <Building2 className="h-4 w-4" />,
        },
        {
          label: "Properties",
          href: "/app/housing/properties",
          icon: <Home className="h-4 w-4" />,
        },
        {
          label: "Providers & Landlords",
          href: "/app/housing/providers",
          icon: <ShieldCheck className="h-4 w-4" />,
        },
        {
          label: "Units & Beds",
          href: "/app/housing/inventory",
          icon: <BedDouble className="h-4 w-4" />,
        },
        {
          label: "Housing Requests",
          href: "/app/housing/requests",
          icon: <FileText className="h-4 w-4" />,
        },
        {
          label: "Allocations & Offers",
          href: "/app/housing/allocations",
          icon: <Key className="h-4 w-4" />,
        },
        {
          label: "Leases & Agreements",
          href: "/app/housing/agreements",
          icon: <FileCheck2 className="h-4 w-4" />,
        },
        {
          label: "Check-In / Out",
          href: "/app/housing/check-in-out",
          icon: <ClipboardCheck className="h-4 w-4" />,
        },
        {
          label: "Safety & Inspections",
          href: "/app/housing/inspections",
          icon: <ShieldAlert className="h-4 w-4" />,
        },
        {
          label: "Maintenance Tickets",
          href: "/app/housing/maintenance",
          icon: <Wrench className="h-4 w-4" />,
        },
        {
          label: "Housing Analytics",
          href: "/app/housing/analytics",
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
          icon: <Leaf className="h-4 w-4 text-emerald-400" />,
        },
        {
          label: "Targets & Goals",
          href: "/app/sustainability/targets",
          icon: <Target className="h-4 w-4" />,
        },
        {
          label: "Energy & Grid",
          href: "/app/sustainability/energy",
          icon: <Zap className="h-4 w-4" />,
        },
        {
          label: "Water Resources",
          href: "/app/sustainability/water",
          icon: <Droplets className="h-4 w-4" />,
        },
        {
          label: "Waste & Circularity",
          href: "/app/sustainability/waste",
          icon: <Trash2 className="h-4 w-4" />,
        },
        {
          label: "Carbon Accounting",
          href: "/app/sustainability/carbon",
          icon: <Activity className="h-4 w-4" />,
        },
        {
          label: "Green Initiatives",
          href: "/app/sustainability/initiatives",
          icon: <Sprout className="h-4 w-4" />,
        },
        {
          label: "Statutory Compliance",
          href: "/app/sustainability/compliance",
          icon: <ShieldCheck className="h-4 w-4" />,
        },
        {
          label: "IoT Smart Meters",
          href: "/app/sustainability/iot-meters",
          icon: <Cpu className="h-4 w-4" />,
        },
        {
          label: "Invoice Reconciliation",
          href: "/app/sustainability/imports",
          icon: <FileSpreadsheet className="h-4 w-4" />,
        },
        {
          label: "Decarb Analytics",
          href: "/app/sustainability/analytics",
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
          icon: <ShieldAlert className="h-4 w-4 text-red-400" />,
        },
        {
          label: "Visitor Directory",
          href: "/app/campus-security/visitors",
          icon: <Users className="h-4 w-4" />,
        },
        {
          label: "Gate Operations",
          href: "/app/campus-security/gate-operations",
          icon: <DoorOpen className="h-4 w-4" />,
        },
        {
          label: "Contractor Access",
          href: "/app/campus-security/contractors",
          icon: <UserCheck className="h-4 w-4" />,
        },
        {
          label: "Security Zones",
          href: "/app/campus-security/zones",
          icon: <Layers className="h-4 w-4" />,
        },
        {
          label: "Access Grants",
          href: "/app/campus-security/access-grants",
          icon: <Key className="h-4 w-4" />,
        },
        {
          label: "Physical Incidents",
          href: "/app/campus-security/incidents",
          icon: <AlertTriangle className="h-4 w-4" />,
        },
        {
          label: "Emergency Response",
          href: "/app/campus-security/emergency",
          icon: <Flame className="h-4 w-4 text-amber-400" />,
        },
        {
          label: "Patrol Rounds",
          href: "/app/campus-security/patrols",
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
          icon: <Globe className="h-4 w-4 text-cyan-400" />,
        },
        {
          label: "Partner Institutions",
          href: "/app/international/partners",
          icon: <Building2 className="h-4 w-4" />,
        },
        {
          label: "MoUs & Agreements",
          href: "/app/international/agreements",
          icon: <FileText className="h-4 w-4" />,
        },
        {
          label: "Mobility Programs",
          href: "/app/international/programs",
          icon: <Compass className="h-4 w-4" />,
        },
        {
          label: "Student Applications",
          href: "/app/international/applications",
          icon: <FileEdit className="h-4 w-4" />,
        },
        {
          label: "Application Reviews",
          href: "/app/international/applications/review",
          icon: <ShieldCheck className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL", "HOD", "FACULTY", "INTERNATIONAL_OFFICER"],
        },
        {
          label: "Partner Nominations",
          href: "/app/international/nominations",
          icon: <CheckSquare className="h-4 w-4" />,
        },
        {
          label: "Inbound Scholars",
          href: "/app/international/inbound",
          icon: <DoorOpen className="h-4 w-4" />,
        },
        {
          label: "Outbound Mobility",
          href: "/app/international/outbound",
          icon: <MapPin className="h-4 w-4" />,
        },
        {
          label: "Faculty Exchange",
          href: "/app/international/faculty-exchange",
          icon: <UserCheck className="h-4 w-4" />,
        },
        {
          label: "Credit Transfer",
          href: "/app/international/credit-transfer",
          icon: <Scale className="h-4 w-4" />,
        },
        {
          label: "Travel Grants & Scholarships",
          href: "/app/international/scholarships",
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
          icon: <Trophy className="h-4 w-4 text-amber-400" />,
        },
        {
          label: "Departments",
          href: "/app/sports/departments",
          icon: <Building2 className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "SPORTS_OFFICER"],
        },
        {
          label: "Facilities & Courts",
          href: "/app/sports/facilities",
          icon: <DoorOpen className="h-4 w-4" />,
        },
        {
          label: "Facility Calendar",
          href: "/app/sports/calendar",
          icon: <Calendar className="h-4 w-4" />,
        },
        {
          label: "Student Athletes",
          href: "/app/sports/participants",
          icon: <Users className="h-4 w-4" />,
        },
        {
          label: "Teams & Rosters",
          href: "/app/sports/teams",
          icon: <ShieldCheck className="h-4 w-4 text-indigo-400" />,
        },
        {
          label: "Coaches & Officials",
          href: "/app/sports/coaches",
          icon: <UserCheck className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "SPORTS_OFFICER", "COACH"],
        },
        {
          label: "Training Programs",
          href: "/app/sports/training",
          icon: <Dumbbell className="h-4 w-4 text-emerald-400" />,
        },
        {
          label: "Training Schedule",
          href: "/app/sports/training/schedule",
          icon: <CalendarDays className="h-4 w-4" />,
        },
        {
          label: "Competitions",
          href: "/app/sports/competitions",
          icon: <Trophy className="h-4 w-4 text-amber-500" />,
        },
        {
          label: "Fixtures & Matches",
          href: "/app/sports/fixtures",
          icon: <Timer className="h-4 w-4 text-blue-400" />,
        },
        {
          label: "Results & Standings",
          href: "/app/sports/results",
          icon: <CheckSquare className="h-4 w-4 text-emerald-400" />,
        },
        {
          label: "Achievements",
          href: "/app/sports/achievements",
          icon: <Medal className="h-4 w-4 text-amber-400" />,
        },
        {
          label: "Equipment & Gear",
          href: "/app/sports/equipment",
          icon: <Wrench className="h-4 w-4" />,
        },
        {
          label: "Registrations & Fees",
          href: "/app/sports/fees",
          icon: <CreditCard className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "ACCOUNTS", "SPORTS_OFFICER"],
        },
        {
          label: "Sports Analytics",
          href: "/app/sports/reports",
          icon: <BarChart3 className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "SPORTS_OFFICER"],
        },
        {
          label: "Sports Policies",
          href: "/app/sports/config",
          icon: <BookOpen className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "SPORTS_OFFICER"],
        },
      ],
    },
    {
      title: "STUDENT AFFAIRS & GRIEVANCES",
      items: [
        {
          label: "Student Affairs Hub",
          href: "/app/student-affairs",
          icon: <ShieldAlert className="h-4 w-4" />,
        },
        {
          label: "Submit Grievance",
          href: "/app/student-affairs/submit",
          icon: <FileEdit className="h-4 w-4" />,
        },
        {
          label: "My Cases",
          href: "/app/student-affairs/my-cases",
          icon: <UserCheck className="h-4 w-4" />,
        },
        {
          label: "Case Intake Queue",
          href: "/app/student-affairs/intake",
          icon: <Inbox className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "STUDENT_AFFAIRS_ADMIN", "CASE_OFFICER"],
        },
        {
          label: "Assignments",
          href: "/app/student-affairs/assignments",
          icon: <Users className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "STUDENT_AFFAIRS_ADMIN", "CASE_OFFICER"],
        },
        {
          label: "Disciplinary Cases",
          href: "/app/student-affairs/disciplinary",
          icon: <Gavel className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "STUDENT_AFFAIRS_ADMIN", "CASE_OFFICER", "INVESTIGATOR"],
        },
        {
          label: "Evidence Review",
          href: "/app/student-affairs/evidence",
          icon: <FolderLock className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "STUDENT_AFFAIRS_ADMIN", "CASE_OFFICER", "INVESTIGATOR"],
        },
        {
          label: "Hearings & Calendar",
          href: "/app/student-affairs/meetings",
          icon: <Calendar className="h-4 w-4" />,
        },
        {
          label: "Resolutions & Actions",
          href: "/app/student-affairs/resolutions",
          icon: <CheckSquare className="h-4 w-4" />,
        },
        {
          label: "Appeals & Reviews",
          href: "/app/student-affairs/appeals",
          icon: <Scale className="h-4 w-4" />,
        },
        {
          label: "Communications",
          href: "/app/student-affairs/communications",
          icon: <MessageSquare className="h-4 w-4" />,
        },
        {
          label: "Urgent Escalations",
          href: "/app/student-affairs/escalations",
          icon: <AlertTriangle className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "STUDENT_AFFAIRS_ADMIN", "CASE_OFFICER"],
        },
        {
          label: "Policies & Standards",
          href: "/app/student-affairs/policies",
          icon: <BookOpen className="h-4 w-4" />,
        },
        {
          label: "Case Analytics",
          href: "/app/student-affairs/reports",
          icon: <BarChart3 className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "STUDENT_AFFAIRS_ADMIN"],
        },
        {
          label: "Affairs Config",
          href: "/app/student-affairs/config",
          icon: <Settings className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "STUDENT_AFFAIRS_ADMIN"],
        },
      ],
    },
    {
      title: "COUNSELLING & MENTORING",
      items: [
        {
          label: "Support Hub",
          href: "/app/student-support",
          icon: <LayoutDashboard className="h-4 w-4" />,
        },
        {
          label: "My Mentor",
          href: "/app/student-support/mentor",
          icon: <UserCheck className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "STUDENT"],
        },
        {
          label: "Mentor Allocations",
          href: "/app/student-support/assignments",
          icon: <Users className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL", "HOD", "STUDENT_SUPPORT_ADMIN"],
        },
        {
          label: "Mentee Directory",
          href: "/app/student-support/mentees",
          icon: <GraduationCap className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL", "HOD", "FACULTY", "STUDENT_SUPPORT_ADMIN"],
        },
        {
          label: "Book Counselling",
          href: "/app/student-support/counselling",
          icon: <Heart className="h-4 w-4" />,
        },
        {
          label: "Counselling Schedule",
          href: "/app/student-support/counselling/schedule",
          icon: <Calendar className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "COUNSELLOR", "STUDENT_SUPPORT_ADMIN"],
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
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL", "HOD", "FACULTY", "STUDENT", "STUDENT_SUPPORT_ADMIN"],
        },
        {
          label: "Development Plans",
          href: "/app/student-support/development-plans",
          icon: <Sparkles className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL", "HOD", "FACULTY", "STUDENT", "STUDENT_SUPPORT_ADMIN"],
        },
        {
          label: "Goals & Milestones",
          href: "/app/student-support/goals",
          icon: <Target className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL", "HOD", "FACULTY", "STUDENT", "STUDENT_SUPPORT_ADMIN"],
        },
        {
          label: "Support Referrals",
          href: "/app/student-support/referrals",
          icon: <ArrowRightLeft className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL", "HOD", "FACULTY", "COUNSELLOR", "STUDENT_SUPPORT_ADMIN"],
        },
        {
          label: "Guidance Timeline",
          href: "/app/student-support/guidance",
          icon: <BookOpen className="h-4 w-4" />,
        },
        {
          label: "Follow-Up Tasks",
          href: "/app/student-support/follow-ups",
          icon: <CheckSquare className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL", "HOD", "FACULTY", "COUNSELLOR", "STUDENT_SUPPORT_ADMIN"],
        },
        {
          label: "Support Analytics",
          href: "/app/student-support/analytics",
          icon: <BarChart3 className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "VICE_PRINCIPAL", "HOD", "STUDENT_SUPPORT_ADMIN"],
        },
        {
          label: "Support Policies",
          href: "/app/student-support/config",
          icon: <Settings className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "STUDENT_SUPPORT_ADMIN"],
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
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "HOD", "WARDEN"],
        },
        {
          label: "Rooms & Beds",
          href: "/app/infrastructure/hostel/rooms",
          icon: <DoorOpen className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "HOD", "WARDEN"],
        },
        {
          label: "Allocations",
          href: "/app/infrastructure/hostel/allocations",
          icon: <UserCheck className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "HOD", "WARDEN"],
        },
        {
          label: "Hostel Leaves",
          href: "/app/infrastructure/hostel/leaves",
          icon: <FileCheck2 className="h-4 w-4" />,
          roles: [
            "SUPER_ADMIN",
            "ADMIN",
            "PRINCIPAL",
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
          icon: <FileText className="h-4 w-4" />,
        },
        {
          label: "All Documents",
          href: "/app/documents/all",
          icon: <Layers className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "HOD"],
        },
        {
          label: "Verification Queue",
          href: "/app/documents/verification",
          icon: <ShieldCheck className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "HOD"],
        },
        {
          label: "Categories",
          href: "/app/documents/categories",
          icon: <Layers className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "HOD"],
        },
        {
          label: "Certificate Center",
          href: "/app/documents/certificates",
          icon: <Award className="h-4 w-4" />,
        },
        {
          label: "Certificate Templates",
          href: "/app/documents/certificates/templates",
          icon: <FileCheck2 className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "HOD"],
        },
        {
          label: "Certificate Requests",
          href: "/app/documents/certificates/requests",
          icon: <FileText className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "HOD", "STUDENT"],
        },
        {
          label: "Institutional Records",
          href: "/app/documents/institutional-records",
          icon: <Building className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "HOD"],
        },
        {
          label: "Document Reports",
          href: "/app/documents/reports",
          icon: <BarChart3 className="h-4 w-4" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "HOD"],
        },
        {
          label: "Knowledge & Policies",
          href: "/app/knowledge",
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
          icon: <Sparkles className="h-4 w-4 text-blue-500" />,
        },
        {
          label: "AI Assistant",
          href: "/app/intelligence/assistant",
          icon: <Bot className="h-4 w-4 text-indigo-500" />,
        },
        {
          label: "Insights",
          href: "/app/intelligence/insights",
          icon: <Sparkles className="h-4 w-4 text-amber-500" />,
        },
        {
          label: "Analytics",
          href: "/app/intelligence/analytics",
          icon: <BarChart3 className="h-4 w-4 text-emerald-500" />,
        },
        {
          label: "Alerts",
          href: "/app/intelligence/alerts",
          icon: <AlertTriangle className="h-4 w-4 text-rose-500" />,
        },
        {
          label: "Saved Insights",
          href: "/app/intelligence/saved",
          icon: <Bookmark className="h-4 w-4 text-purple-500" />,
        },
        {
          label: "AI Activity & Tools",
          href: "/app/intelligence/activity",
          icon: <Activity className="h-4 w-4 text-slate-500" />,
          roles: ["SUPER_ADMIN", "ADMIN", "PRINCIPAL", "HOD"],
        },
      ],
    },
    {
      title: "SYSTEM GOVERNANCE",
      items: [
        {
          label: "Institution",
          href: "/app/institution",
          icon: <Building className="h-4 w-4" />,
        },
        {
          label: "Campuses",
          href: "/app/campuses",
          icon: <Building2 className="h-4 w-4" />,
        },
        {
          label: "Departments",
          href: "/app/departments",
          icon: <Layers className="h-4 w-4" />,
        },
        {
          label: "Security & IAM",
          href: "/app/security",
          icon: <ShieldCheck className="h-4 w-4" />,
        },
        {
          label: "Accreditation & IQAC",
          href: "/app/accreditation",
          icon: <Award className="h-4 w-4 text-amber-400" />,
        },
        {
          label: "Research & Grants",
          href: "/app/research",
          icon: <FlaskConical className="h-4 w-4 text-emerald-400" />,
        },
      ],
    },
  ];

  const sidebarContent = (
    <div className="flex h-full flex-col bg-slate-950 border-r border-slate-800 text-slate-200">
      {/* Brand Header */}
      <div className="flex h-16 items-center justify-between px-6 border-b border-slate-800">
        <Link href="/app/dashboard" className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white font-black text-sm shadow-md shadow-indigo-600/30">
            C
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-base font-bold tracking-tight text-white">
                CampusOS
              </span>
              <span className="rounded bg-indigo-500/20 px-1.5 py-0.2 text-[9px] font-mono font-bold uppercase text-indigo-300 border border-indigo-500/30">
                ERP
              </span>
            </div>
            <div className="text-[10px] text-slate-500 tracking-wider uppercase font-semibold">
              Operating System
            </div>
          </div>
        </Link>
        {onCloseMobile && (
          <button
            onClick={onCloseMobile}
            className="lg:hidden rounded-lg p-1.5 text-slate-400 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Navigation Sections */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {NAV_SECTIONS.map((section) => {
          const userRoleNames = user?.roles?.map((r) => r.name) || ["SUPER_ADMIN"];
          const isSuperOrAdmin =
            userRoleNames.includes("SUPER_ADMIN") || userRoleNames.includes("ADMIN");
          const visibleItems = section.items.filter((item) => {
            if (!item.roles || item.roles.includes("*")) return true;
            if (isSuperOrAdmin) return true;
            return item.roles.some((role) => userRoleNames.includes(role));
          });

          if (visibleItems.length === 0) return null;

          return (
            <div key={section.title} className="space-y-1">
              <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1.5">
                {section.title}
              </div>
              {visibleItems.map((item) => {
                const isActive =
                  item.href === "/app/dashboard"
                    ? pathname === "/app/dashboard"
                    : pathname.startsWith(item.href);

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={onCloseMobile}
                    className={cn(
                      "flex items-center justify-between rounded-lg px-3 py-2 text-xs font-medium transition-colors group",
                      isActive
                        ? "bg-indigo-600 text-white shadow-sm font-semibold"
                        : "text-slate-400 hover:bg-slate-900 hover:text-slate-200",
                    )}
                  >
                    <div className="flex items-center gap-2.5">
                      <span
                        className={cn(
                          "transition-colors",
                          isActive
                            ? "text-white"
                            : "text-slate-500 group-hover:text-slate-300",
                        )}
                      >
                        {item.icon}
                      </span>
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span className="rounded-full bg-slate-800 px-1.5 py-0.2 text-[9px] font-mono text-slate-400">
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
      <div className="p-3.5 border-t border-slate-800 bg-slate-950/80">
        <div className="rounded-xl border border-slate-800/80 bg-slate-900/60 p-3">
          <div className="text-[10px] uppercase font-bold tracking-wider text-slate-500 mb-1 flex items-center justify-between">
            <span>Tenant Scope</span>
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          </div>
          <div className="text-xs font-semibold text-white truncate">
            {user?.tenant?.name || "Vidyasagar State University"}
          </div>
          <div className="text-[10px] text-slate-400 font-mono mt-0.5 truncate">
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
            className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm animate-fade-in"
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
