import React from "react";
import {
  GraduationCap,
  ShieldCheck,
  Landmark,
  UserCheck,
  Building,
} from "lucide-react";

export type PortalKey =
  "STUDENT" | "ADMIN" | "VICE_PRINCIPAL" | "FACULTY" | "HOD";

export interface PortalConfig {
  key: PortalKey;
  canonicalRole: string;
  allowedRoles: string[];
  label: string;
  shortTitle: string;
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
  STUDENT: {
    key: "STUDENT",
    canonicalRole: "STUDENT",
    allowedRoles: ["STUDENT"],
    label: "Student Portal",
    shortTitle: "Student",
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
  ADMIN: {
    key: "ADMIN",
    canonicalRole: "SUPER_ADMIN",
    allowedRoles: ["SUPER_ADMIN", "ADMIN", "INSTITUTION_ADMIN"],
    label: "Administrator Portal",
    shortTitle: "Admin",
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
  FACULTY: {
    key: "FACULTY",
    canonicalRole: "FACULTY",
    allowedRoles: ["FACULTY", "PROFESSOR"],
    label: "Faculty Portal",
    shortTitle: "Faculty",
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
  HOD: {
    key: "HOD",
    canonicalRole: "HOD",
    allowedRoles: ["HOD"],
    label: "Head of Department Portal",
    shortTitle: "HOD",
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
};

export const PORTAL_KEYS: PortalKey[] = [
  "STUDENT",
  "ADMIN",
  "VICE_PRINCIPAL",
  "FACULTY",
  "HOD",
];

export const REGULAR_PORTAL_KEYS: PortalKey[] = [
  "STUDENT",
  "FACULTY",
  "VICE_PRINCIPAL",
  "HOD",
];

export function getRoleIcon(portalKey: PortalKey, className = "h-4 w-4") {
  switch (portalKey) {
    case "STUDENT":
      return <GraduationCap className={className} />;
    case "ADMIN":
      return <ShieldCheck className={className} />;
    case "VICE_PRINCIPAL":
      return <Landmark className={className} />;
    case "FACULTY":
      return <UserCheck className={className} />;
    case "HOD":
      return <Building className={className} />;
  }
}
