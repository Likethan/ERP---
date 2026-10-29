"use client";

import React from "react";
import { useAuth } from "@/lib/auth-context";
import { AdminDashboard } from "@/components/dashboard/admin-dashboard";
import { StudentDashboard } from "@/components/dashboard/student-dashboard";
import { FacultyDashboard } from "@/components/dashboard/faculty-dashboard";
import { HodDashboard } from "@/components/dashboard/hod-dashboard";
import { AccountsDashboard } from "@/components/dashboard/accounts-dashboard";
import { PlacementDashboard } from "@/components/dashboard/placement-dashboard";
import { VicePrincipalDashboard } from "@/components/dashboard/vice-principal-dashboard";

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
