"use client";

import dynamic from "next/dynamic";

const FacultyDashboard = dynamic(
  () =>
    import("@/components/dashboard/faculty-dashboard").then(
      (m) => m.FacultyDashboard,
    ),
  { ssr: false },
);

export default function FacultyDashboardPage() {
  return <FacultyDashboard />;
}
