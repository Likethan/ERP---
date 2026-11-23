"use client";

import React from "react";
import dynamic from "next/dynamic";
import { useAuth } from "@/lib/auth-context";

const AdminDashboard = dynamic(
  () =>
    import("@/components/dashboard/admin-dashboard").then(
      (m) => m.AdminDashboard,
    ),
  { ssr: false },
);
const StudentDashboard = dynamic(
  () =>
    import("@/components/dashboard/student-dashboard").then(
      (m) => m.StudentDashboard,
    ),
  { ssr: false },
);
const FacultyDashboard = dynamic(
  () =>
    import("@/components/dashboard/faculty-dashboard").then(
      (m) => m.FacultyDashboard,
    ),
  { ssr: false },
);
const HodDashboard = dynamic(
  () =>
    import("@/components/dashboard/hod-dashboard").then((m) => m.HodDashboard),
  { ssr: false },
);
const AccountsDashboard = dynamic(
  () =>
    import("@/components/dashboard/accounts-dashboard").then(
      (m) => m.AccountsDashboard,
    ),
  { ssr: false },
);
const PlacementDashboard = dynamic(
  () =>
    import("@/components/dashboard/placement-dashboard").then(
      (m) => m.PlacementDashboard,
    ),
  { ssr: false },
);
const VicePrincipalDashboard = dynamic(
  () =>
    import("@/components/dashboard/vice-principal-dashboard").then(
      (m) => m.VicePrincipalDashboard,
    ),
  { ssr: false },
);

export default function DashboardPage() {
  const { user, activePersona } = useAuth();

  // Primary effective role resolution: user roles take precedence, falling back to activePersona
  const effectiveRole = user?.roles?.[0]?.name || activePersona.role;

  switch (effectiveRole) {
    case "STUDENT":
      return <StudentDashboard />;
    case "FACULTY":
      return <FacultyDashboard />;
    case "HOD":
      return <HodDashboard />;
    case "PRINCIPAL":
      return <VicePrincipalDashboard />;
    case "ACCOUNTS":
      return <AccountsDashboard />;
    case "PLACEMENT_OFFICER":
      return <PlacementDashboard />;
    case "SUPER_ADMIN":
    case "ADMIN":
    case "STAFF":
    default:
      return <AdminDashboard />;
  }
}
