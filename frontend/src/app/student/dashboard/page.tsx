"use client";

import dynamic from "next/dynamic";

const StudentDashboard = dynamic(
  () =>
    import("@/components/dashboard/student-dashboard").then(
      (m) => m.StudentDashboard,
    ),
  { ssr: false },
);

export default function StudentDashboardPage() {
  return <StudentDashboard />;
}
