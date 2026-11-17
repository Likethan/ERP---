import React from "react";
import {
  GraduationCap,
  ShieldCheck,
  Landmark,
  UserCheck,
  Building,
  DollarSign,
  Briefcase,
  BedDouble,
  Bus,
  BookOpen,
  ShieldAlert,
  Wrench,
  Users,
} from "lucide-react";

export type PrimaryPortalKey =
  "STUDENT" | "ADMIN" | "VICE_PRINCIPAL" | "FACULTY" | "HOD";

export type ExtendedPortalKey =
  | "ACCOUNTS"
  | "PLACEMENT"
  | "WARDEN"
  | "TRANSPORT"
  | "LIBRARIAN"
  | "SECURITY"
  | "FACILITY"
  | "STAFF";

export type PortalKey = PrimaryPortalKey | ExtendedPortalKey;

export interface PortalConfig {
  key: PortalKey;
  canonicalRole: string;
  allowedRoles: string[];
  label: string;
  shortTitle: string;
  description: string;
  supportingText: string;
  identifierLabel: string;
  identifierPlaceholder: string;
  identifierHint: string;
  demoEmail: string;
  demoPassword: string;
  demoPersonaId: string;
  badgeText: string;
  accent: {
    tabActive: string;
    tabText: string;
    badgeBg: string;
    badgeText: string;
    badgeBorder: string;
    glow: string;
  };
}

export const PORTALS: Record<PortalKey, PortalConfig> = {
  ADMIN: {
    key: "ADMIN",
    canonicalRole: "SUPER_ADMIN",
    allowedRoles: ["SUPER_ADMIN", "ADMIN", "INSTITUTION_ADMIN"],
    label: "Administrator Portal",
    shortTitle: "Admin",
    description: "Institution administration and system management.",
    supportingText: "Manage your institution with confidence.",
    identifierLabel: "Institutional Administrator Email",
    identifierPlaceholder: "e.g. registrar@campusos.edu or admin@campusos.edu",
    identifierHint:
      "Enter your authorized registrar or institutional administrator email.",
    demoEmail: "registrar@campusos.edu",
    demoPassword: "SuperSecret123!",
    demoPersonaId: "user-super-admin-01",
    badgeText: "Governance & Master System Config",
    accent: {
      tabActive:
        "bg-yellow-400 border-yellow-500 text-slate-950 shadow-xs font-bold",
      tabText: "text-slate-950",
      badgeBg: "bg-emerald-50",
      badgeText: "text-emerald-900 font-semibold",
      badgeBorder: "border-emerald-200",
      glow: "from-emerald-400/10",
    },
  },
  VICE_PRINCIPAL: {
    key: "VICE_PRINCIPAL",
    canonicalRole: "PRINCIPAL",
    allowedRoles: ["PRINCIPAL", "SUPER_ADMIN"],
    label: "Vice Principal Portal",
    shortTitle: "Vice Principal",
    description: "Institutional oversight and academic monitoring.",
    supportingText:
      "Oversee academic operations and institutional performance.",
    identifierLabel: "Executive / Vice Principal Email",
    identifierPlaceholder: "e.g. vp.academics@campusos.edu",
    identifierHint: "Enter your executive academic operations credentials.",
    demoEmail: "vp.academics@campusos.edu",
    demoPassword: "ExecutiveSecret123!",
    demoPersonaId: "user-vice-principal-01",
    badgeText: "Academic Oversight & Approvals",
    accent: {
      tabActive:
        "bg-yellow-400 border-yellow-500 text-slate-950 shadow-xs font-bold",
      tabText: "text-slate-950",
      badgeBg: "bg-yellow-100",
      badgeText: "text-yellow-950 font-semibold",
      badgeBorder: "border-yellow-300",
      glow: "from-yellow-400/20",
    },
  },
  HOD: {
    key: "HOD",
    canonicalRole: "HOD",
    allowedRoles: ["HOD"],
    label: "Head of Department Portal",
    shortTitle: "HOD",
    description: "Department administration and academic coordination.",
    supportingText:
      "Coordinate departmental academics, faculty, and student outcomes.",
    identifierLabel: "Department Head Institutional Email",
    identifierPlaceholder: "e.g. hod.cse@campusos.edu",
    identifierHint: "Enter your authorized department head credentials.",
    demoEmail: "hod.cse@campusos.edu",
    demoPassword: "HodSecret123!",
    demoPersonaId: "user-hod-cse-01",
    badgeText: "Departmental Leadership & Workloads",
    accent: {
      tabActive:
        "bg-yellow-400 border-yellow-500 text-slate-950 shadow-xs font-bold",
      tabText: "text-slate-950",
      badgeBg: "bg-purple-50",
      badgeText: "text-purple-900 font-semibold",
      badgeBorder: "border-purple-200",
      glow: "from-purple-400/10",
    },
  },
  FACULTY: {
    key: "FACULTY",
    canonicalRole: "FACULTY",
    allowedRoles: ["FACULTY", "PROFESSOR"],
    label: "Faculty Portal",
    shortTitle: "Faculty",
    description: "Teaching, attendance and academic activities.",
    supportingText:
      "Manage teaching, attendance, assessments, and student progress.",
    identifierLabel: "Faculty ID or Institutional Email",
    identifierPlaceholder: "e.g. rajesh.sharma@campusos.edu or FAC-CSE-108",
    identifierHint:
      "Enter your faculty employee ID or academic department email.",
    demoEmail: "rajesh.sharma@campusos.edu",
    demoPassword: "FacultySecret123!",
    demoPersonaId: "user-faculty-01",
    badgeText: "Teaching, Grading & Coursework",
    accent: {
      tabActive:
        "bg-yellow-400 border-yellow-500 text-slate-950 shadow-xs font-bold",
      tabText: "text-slate-950",
      badgeBg: "bg-sky-50",
      badgeText: "text-sky-900 font-semibold",
      badgeBorder: "border-sky-200",
      glow: "from-sky-400/10",
    },
  },
  STUDENT: {
    key: "STUDENT",
    canonicalRole: "STUDENT",
    allowedRoles: ["STUDENT"],
    label: "Student Portal",
    shortTitle: "Student",
    description: "Personal academics and student services.",
    supportingText: "Access your academic life in one place.",
    identifierLabel: "Student ID / Roll No. or Email",
    identifierPlaceholder:
      "e.g. aarav.patel@student.campusos.edu or 2024-CSE-042",
    identifierHint: "Use your university roll number or student email.",
    demoEmail: "aarav.patel@student.campusos.edu",
    demoPassword: "StudentSecret123!",
    demoPersonaId: "user-student-01",
    badgeText: "Academic Lifecycle & Courses",
    accent: {
      tabActive:
        "bg-yellow-400 border-yellow-500 text-slate-950 shadow-xs font-bold",
      tabText: "text-slate-950",
      badgeBg: "bg-yellow-100",
      badgeText: "text-yellow-950 font-semibold",
      badgeBorder: "border-yellow-300",
      glow: "from-yellow-400/20",
    },
  },
  ACCOUNTS: {
    key: "ACCOUNTS",
    canonicalRole: "ACCOUNTS",
    allowedRoles: ["ACCOUNTS", "BURSAR", "FINANCE", "SUPER_ADMIN"],
    label: "Finance & Accounts Portal",
    shortTitle: "Accounts",
    description:
      "Student fee invoicing, receipts, billing ledgers, and scholarships.",
    supportingText:
      "Student fee invoicing, receipts, billing ledgers, and scholarships.",
    identifierLabel: "Finance Office Email / Employee ID",
    identifierPlaceholder: "e.g. finance.bursar@campusos.edu or ACC-201",
    identifierHint: "Enter your institutional finance or bursar credentials.",
    demoEmail: "finance.bursar@campusos.edu",
    demoPassword: "FinanceSecret123!",
    demoPersonaId: "user-accounts-01",
    badgeText: "Fee Billing, Ledgers & Scholarships",
    accent: {
      tabActive:
        "bg-yellow-400 border-yellow-500 text-slate-950 shadow-xs font-bold",
      tabText: "text-slate-950",
      badgeBg: "bg-emerald-50",
      badgeText: "text-emerald-900 font-semibold",
      badgeBorder: "border-emerald-200",
      glow: "from-emerald-400/10",
    },
  },
  PLACEMENT: {
    key: "PLACEMENT",
    canonicalRole: "PLACEMENT_OFFICER",
    allowedRoles: ["PLACEMENT_OFFICER", "PLACEMENT", "SUPER_ADMIN"],
    label: "Corporate Placement Portal",
    shortTitle: "Placement",
    description:
      "Corporate relations, recruitment drives, job offers, and student talent pool.",
    supportingText:
      "Corporate relations, recruitment drives, job offers, and student talent pool.",
    identifierLabel: "Corporate Relations Email / ID",
    identifierPlaceholder: "e.g. placement.dean@campusos.edu or TPO-104",
    identifierHint: "Enter your Training & Placement Officer credentials.",
    demoEmail: "placement.dean@campusos.edu",
    demoPassword: "PlacementSecret123!",
    demoPersonaId: "user-placement-01",
    badgeText: "Drives, Corporate Directory & Offers",
    accent: {
      tabActive:
        "bg-yellow-400 border-yellow-500 text-slate-950 shadow-xs font-bold",
      tabText: "text-slate-950",
      badgeBg: "bg-blue-50",
      badgeText: "text-blue-900 font-semibold",
      badgeBorder: "border-blue-200",
      glow: "from-blue-400/10",
    },
  },
  WARDEN: {
    key: "WARDEN",
    canonicalRole: "WARDEN",
    allowedRoles: ["WARDEN", "HOSTEL_WARDEN", "SUPER_ADMIN"],
    label: "Hostel Warden Portal",
    shortTitle: "Warden",
    description:
      "Hostel room allocation, bed capacity, resident welfare, and leave passes.",
    supportingText:
      "Hostel room allocation, bed capacity, resident welfare, and leave passes.",
    identifierLabel: "Hostel Warden Email / ID",
    identifierPlaceholder: "e.g. warden.raman@campusos.edu or WRD-01",
    identifierHint: "Enter your residential hostel administration credentials.",
    demoEmail: "warden.raman@campusos.edu",
    demoPassword: "WardenSecret123!",
    demoPersonaId: "user-warden-01",
    badgeText: "Hostel Blocks, Rooms & Leave Approvals",
    accent: {
      tabActive:
        "bg-yellow-400 border-yellow-500 text-slate-950 shadow-xs font-bold",
      tabText: "text-slate-950",
      badgeBg: "bg-amber-50",
      badgeText: "text-amber-900 font-semibold",
      badgeBorder: "border-amber-200",
      glow: "from-amber-400/10",
    },
  },
  TRANSPORT: {
    key: "TRANSPORT",
    canonicalRole: "TRANSPORT_OFFICER",
    allowedRoles: ["TRANSPORT_OFFICER", "TRANSPORT", "SUPER_ADMIN"],
    label: "Transport & Fleet Portal",
    shortTitle: "Transport",
    description:
      "Bus fleet management, route scheduling, driver rosters, and student passes.",
    supportingText:
      "Bus fleet management, route scheduling, driver rosters, and student passes.",
    identifierLabel: "Transport Operations Email / ID",
    identifierPlaceholder: "e.g. transport.officer@campusos.edu or TRP-01",
    identifierHint: "Enter your fleet and transport management credentials.",
    demoEmail: "transport.officer@campusos.edu",
    demoPassword: "TransportSecret123!",
    demoPersonaId: "user-transport-01",
    badgeText: "Routes, Vehicles & Bus Passes",
    accent: {
      tabActive:
        "bg-yellow-400 border-yellow-500 text-slate-950 shadow-xs font-bold",
      tabText: "text-slate-950",
      badgeBg: "bg-cyan-50",
      badgeText: "text-cyan-900 font-semibold",
      badgeBorder: "border-cyan-200",
      glow: "from-cyan-400/10",
    },
  },
  LIBRARIAN: {
    key: "LIBRARIAN",
    canonicalRole: "LIBRARIAN",
    allowedRoles: ["LIBRARIAN", "LIBRARY", "SUPER_ADMIN"],
    label: "Library Portal",
    shortTitle: "Librarian",
    description:
      "Catalogue search, circulation, book loans, and institutional knowledge assets.",
    supportingText:
      "Catalogue search, circulation, book loans, and institutional knowledge assets.",
    identifierLabel: "Library Operations Email / ID",
    identifierPlaceholder: "e.g. librarian@campusos.edu or LIB-01",
    identifierHint: "Enter your institutional library management credentials.",
    demoEmail: "librarian@campusos.edu",
    demoPassword: "LibrarySecret123!",
    demoPersonaId: "user-librarian-01",
    badgeText: "Catalogue, Circulation & Journals",
    accent: {
      tabActive:
        "bg-yellow-400 border-yellow-500 text-slate-950 shadow-xs font-bold",
      tabText: "text-slate-950",
      badgeBg: "bg-teal-50",
      badgeText: "text-teal-900 font-semibold",
      badgeBorder: "border-teal-200",
      glow: "from-teal-400/10",
    },
  },
  SECURITY: {
    key: "SECURITY",
    canonicalRole: "SECURITY_HEAD",
    allowedRoles: [
      "SECURITY_HEAD",
      "SECURITY_OFFICER",
      "SECURITY",
      "SUPER_ADMIN",
    ],
    label: "Campus Security Portal",
    shortTitle: "Security",
    description:
      "Gate access control, visitor logs, surveillance checkpoints, and emergency response.",
    supportingText:
      "Gate access control, visitor logs, surveillance checkpoints, and emergency response.",
    identifierLabel: "Campus Security Email / ID",
    identifierPlaceholder: "e.g. security.chief@campusos.edu or SEC-01",
    identifierHint: "Enter your campus security operations credentials.",
    demoEmail: "security.chief@campusos.edu",
    demoPassword: "SecuritySecret123!",
    demoPersonaId: "user-security-01",
    badgeText: "Gate Pass, Access Grants & Incidents",
    accent: {
      tabActive:
        "bg-yellow-400 border-yellow-500 text-slate-950 shadow-xs font-bold",
      tabText: "text-slate-950",
      badgeBg: "bg-rose-50",
      badgeText: "text-rose-900 font-semibold",
      badgeBorder: "border-rose-200",
      glow: "from-rose-400/10",
    },
  },
  FACILITY: {
    key: "FACILITY",
    canonicalRole: "FACILITY_OFFICER",
    allowedRoles: ["FACILITY_OFFICER", "FACILITY", "ESTATE", "SUPER_ADMIN"],
    label: "Estate & Facilities Portal",
    shortTitle: "Facilities",
    description:
      "Campus physical estate, preventive maintenance, and utility infrastructure.",
    supportingText:
      "Campus physical estate, preventive maintenance, and utility infrastructure.",
    identifierLabel: "Estate Operations Email / ID",
    identifierPlaceholder: "e.g. facilities.estate@campusos.edu or FAC-01",
    identifierHint:
      "Enter your physical plant and estate operations credentials.",
    demoEmail: "facilities.estate@campusos.edu",
    demoPassword: "FacilitySecret123!",
    demoPersonaId: "user-facility-01",
    badgeText: "Estate, Maintenance & Work Orders",
    accent: {
      tabActive:
        "bg-yellow-400 border-yellow-500 text-slate-950 shadow-xs font-bold",
      tabText: "text-slate-950",
      badgeBg: "bg-lime-50",
      badgeText: "text-lime-900 font-semibold",
      badgeBorder: "border-lime-200",
      glow: "from-lime-400/10",
    },
  },
  STAFF: {
    key: "STAFF",
    canonicalRole: "STAFF",
    allowedRoles: ["STAFF", "SUPER_ADMIN"],
    label: "Staff Portal",
    shortTitle: "Staff",
    description:
      "General employee self-service, attendance check-in, leaves, and documents.",
    supportingText:
      "General employee self-service, attendance check-in, leaves, and documents.",
    identifierLabel: "Staff Employee Email / ID",
    identifierPlaceholder: "e.g. staff.member@campusos.edu or STF-101",
    identifierHint: "Enter your institutional staff employee ID or email.",
    demoEmail: "staff.member@campusos.edu",
    demoPassword: "StaffSecret123!",
    demoPersonaId: "user-staff-01",
    badgeText: "Staff Self-Service & Attendance",
    accent: {
      tabActive:
        "bg-yellow-400 border-yellow-500 text-slate-950 shadow-xs font-bold",
      tabText: "text-slate-950",
      badgeBg: "bg-slate-100",
      badgeText: "text-slate-900 font-semibold",
      badgeBorder: "border-slate-300",
      glow: "from-slate-400/10",
    },
  },
};

export const PRIMARY_PORTAL_KEYS: PrimaryPortalKey[] = [
  "ADMIN",
  "VICE_PRINCIPAL",
  "HOD",
  "FACULTY",
  "STUDENT",
];

export const PORTAL_KEYS: PrimaryPortalKey[] = [
  "STUDENT",
  "ADMIN",
  "VICE_PRINCIPAL",
  "FACULTY",
  "HOD",
];

export const REGULAR_PORTAL_KEYS: PrimaryPortalKey[] = [
  "STUDENT",
  "FACULTY",
  "VICE_PRINCIPAL",
  "HOD",
];

export const EXTENDED_PORTAL_KEYS: ExtendedPortalKey[] = [
  "ACCOUNTS",
  "PLACEMENT",
  "WARDEN",
  "TRANSPORT",
  "LIBRARIAN",
  "SECURITY",
  "FACILITY",
  "STAFF",
];

export const ALL_PORTAL_KEYS: PortalKey[] = [
  ...PORTAL_KEYS,
  ...EXTENDED_PORTAL_KEYS,
];

export function getRoleIcon(portalKey: PortalKey, className = "h-4 w-4") {
  switch (portalKey) {
    case "STUDENT":
      return <BookOpen className={className} />;
    case "ADMIN":
      return <ShieldCheck className={className} />;
    case "VICE_PRINCIPAL":
      return <GraduationCap className={className} />;
    case "FACULTY":
      return <Users className={className} />;
    case "HOD":
      return <Building className={className} />;
    case "ACCOUNTS":
      return <DollarSign className={className} />;
    case "PLACEMENT":
      return <Briefcase className={className} />;
    case "WARDEN":
      return <BedDouble className={className} />;
    case "TRANSPORT":
      return <Bus className={className} />;
    case "LIBRARIAN":
      return <BookOpen className={className} />;
    case "SECURITY":
      return <ShieldAlert className={className} />;
    case "FACILITY":
      return <Wrench className={className} />;
    case "STAFF":
      return <Users className={className} />;
    default:
      return <UserCheck className={className} />;
  }
}
