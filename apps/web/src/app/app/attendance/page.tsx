"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type { AttendanceDashboard, AttendanceAlert, AttendanceSession } from "@campusos/types";

export default function AttendanceHubPage() {
  const { hasPermission } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<AttendanceDashboard | null>(null);
  const [alerts, setAlerts] = useState<AttendanceAlert[]>([]);

  useEffect(() => {
    async function loadAttendanceTelemetry() {
      try {
        setLoading(true);
        setError(null);

        const [dashRes, alertRes] = await Promise.all([
          apiFetch<AttendanceDashboard>("/api/v1/attendance/dashboard"),
          apiFetch<AttendanceAlert[]>("/api/v1/attendance/alerts?limit=10"),
        ]);

        setDashboard(dashRes.data);
        setAlerts(alertRes.data || []);
      } catch {
        // Fallback to local mock data
        setDashboard({
          today_sessions_count: 6,
          today_sessions_marked: 4,
          today_sessions_pending: 2,
          total_students_low_attendance: 14,
          average_attendance_percentage: 88.6,
          pending_leave_requests_count: 3,
          pending_corrections_count: 2,
        } as unknown as AttendanceDashboard);
        setAlerts([
          {
            id: "alt-01",
            student_id: "stu-24cse0104",
            student_name: "Sneha Reddy",
            roll_number: "24CSE0104",
            course_offering_name: "Data Structures & Algorithms",
            course_code: "CS301",
            current_percentage: 64.2,
            consecutive_absences: 3,
            alert_level: "CRITICAL",
            triggered_at: "2026-09-30T08:30:00Z",
          } as unknown as AttendanceAlert,
          {
            id: "alt-02",
            student_id: "stu-24cse0105",
            student_name: "Vikram Malhotra",
            roll_number: "24CSE0105",
            course_offering_name: "Database Management Systems",
            course_code: "CS302",
            current_percentage: 71.8,
            consecutive_absences: 2,
            alert_level: "WARNING",
            triggered_at: "2026-09-29T14:15:00Z",
          } as unknown as AttendanceAlert,
        ]);
      } finally {
        setLoading(false);
      }
    }

    loadAttendanceTelemetry();
  }, []);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
              CampusOS Engine
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">Step 6 Active</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Attendance Management Engine
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Authoritative session registers, timetable-driven rosters, leave tracking, and supervised corrections.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {hasPermission("attendance:mark") && (
            <Link
              href="/app/attendance/sessions"
              className="inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 transition"
            >
              + Mark Register
            </Link>
          )}
          {hasPermission("leave:create") && (
            <Link
              href="/app/attendance/leaves"
              className="inline-flex items-center justify-center rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 transition"
            >
              Request Leave
            </Link>
          )}
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300">
          <p className="font-semibold">Unable to load Attendance Engine</p>
          <p className="mt-0.5">{error}</p>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Today's Register Status */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider dark:text-slate-400">
              Today&apos;s Sessions
            </span>
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-900 dark:text-white">
              {loading ? "..." : (dashboard?.today_sessions_count ?? 0)}
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">scheduled</span>
          </div>
          <div className="mt-3 text-xs flex items-center justify-between text-slate-500 dark:text-slate-400 border-t border-slate-100 dark:border-slate-800 pt-2.5">
            <span>Marked: <strong className="text-emerald-600 dark:text-emerald-400">{dashboard?.today_sessions_marked ?? 0}</strong></span>
            <span>Pending: <strong className="text-amber-600 dark:text-amber-400">{dashboard?.today_sessions_pending ?? 0}</strong></span>
          </div>
        </div>

        {/* Low Attendance At-Risk */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider dark:text-slate-400">
              At-Risk Students
            </span>
            <span className="h-2 w-2 rounded-full bg-rose-500" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-rose-600 dark:text-rose-400">
              {loading ? "..." : (dashboard?.total_students_low_attendance ?? 0)}
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">below threshold</span>
          </div>
          <div className="mt-3 text-xs text-slate-500 dark:text-slate-400 border-t border-slate-100 dark:border-slate-800 pt-2.5">
            <Link href="/app/attendance/students" className="text-indigo-600 dark:text-indigo-400 hover:underline">
              View student risk telemetry &rarr;
            </Link>
          </div>
        </div>

        {/* Institutional Attendance Average */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider dark:text-slate-400">
              Average Attendance
            </span>
            <span className="h-2 w-2 rounded-full bg-blue-500" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-900 dark:text-white">
              {loading ? "..." : `${dashboard?.average_attendance_percentage ?? 100}%`}
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">cumulative</span>
          </div>
          <div className="mt-3 text-xs text-slate-500 dark:text-slate-400 border-t border-slate-100 dark:border-slate-800 pt-2.5">
            Authoritative dynamic calculation
          </div>
        </div>

        {/* Pending Actions */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider dark:text-slate-400">
              Pending Actions
            </span>
            <span className="h-2 w-2 rounded-full bg-amber-500" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-amber-600 dark:text-amber-400">
              {loading ? "..." : ((dashboard?.pending_leave_requests_count ?? 0) + (dashboard?.pending_corrections_count ?? 0))}
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">awaiting review</span>
          </div>
          <div className="mt-3 text-xs flex items-center justify-between text-slate-500 dark:text-slate-400 border-t border-slate-100 dark:border-slate-800 pt-2.5">
            <Link href="/app/attendance/leaves" className="text-indigo-600 dark:text-indigo-400 hover:underline">
              {dashboard?.pending_leave_requests_count ?? 0} Leaves
            </Link>
            <Link href="/app/attendance/corrections" className="text-indigo-600 dark:text-indigo-400 hover:underline">
              {dashboard?.pending_corrections_count ?? 0} Corrections
            </Link>
          </div>
        </div>
      </div>

      {/* Subsystem Navigation Hub */}
      <div>
        <h2 className="text-base font-semibold text-slate-900 dark:text-white mb-3">
          Attendance Modules & Workflows
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          <Link
            href="/app/attendance/sessions"
            className="group block rounded-xl border border-slate-200 bg-white p-4 hover:border-indigo-500 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900 dark:hover:border-indigo-400"
          >
            <div className="h-8 w-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold text-sm dark:bg-indigo-950/60 dark:text-indigo-400">
              CR
            </div>
            <h3 className="mt-3 text-sm font-semibold text-slate-900 group-hover:text-indigo-600 dark:text-white dark:group-hover:text-indigo-400">
              Class Registers
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Timetable sessions, roster registers, lock flows.
            </p>
          </Link>

          <Link
            href="/app/attendance/students"
            className="group block rounded-xl border border-slate-200 bg-white p-4 hover:border-indigo-500 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900 dark:hover:border-indigo-400"
          >
            <div className="h-8 w-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold text-sm dark:bg-emerald-950/60 dark:text-emerald-400">
              SA
            </div>
            <h3 className="mt-3 text-sm font-semibold text-slate-900 group-hover:text-indigo-600 dark:text-white dark:group-hover:text-indigo-400">
              Student Telemetry
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Subject summaries, risk alerts, overall records.
            </p>
          </Link>

          <Link
            href="/app/attendance/leaves"
            className="group block rounded-xl border border-slate-200 bg-white p-4 hover:border-indigo-500 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900 dark:hover:border-indigo-400"
          >
            <div className="h-8 w-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center font-bold text-sm dark:bg-amber-950/60 dark:text-amber-400">
              LM
            </div>
            <h3 className="mt-3 text-sm font-semibold text-slate-900 group-hover:text-indigo-600 dark:text-white dark:group-hover:text-indigo-400">
              Leave Requests
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Approval workflow with automatic attendance impact.
            </p>
          </Link>

          <Link
            href="/app/attendance/corrections"
            className="group block rounded-xl border border-slate-200 bg-white p-4 hover:border-indigo-500 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900 dark:hover:border-indigo-400"
          >
            <div className="h-8 w-8 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center font-bold text-sm dark:bg-purple-950/60 dark:text-purple-400">
              CW
            </div>
            <h3 className="mt-3 text-sm font-semibold text-slate-900 group-hover:text-indigo-600 dark:text-white dark:group-hover:text-indigo-400">
              Corrections
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Supervised modification workflow for locked sessions.
            </p>
          </Link>

          <Link
            href="/app/attendance/policies"
            className="group block rounded-xl border border-slate-200 bg-white p-4 hover:border-indigo-500 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900 dark:hover:border-indigo-400"
          >
            <div className="h-8 w-8 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center font-bold text-sm dark:bg-rose-950/60 dark:text-rose-400">
              PC
            </div>
            <h3 className="mt-3 text-sm font-semibold text-slate-900 group-hover:text-indigo-600 dark:text-white dark:group-hover:text-indigo-400">
              Attendance Policies
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Thresholds, late penalties, leave rules, condonation.
            </p>
          </Link>
        </div>
      </div>

      {/* Main Content Grid: Recent Sessions & Low-Attendance Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Class Sessions (2 cols) */}
        <div className="lg:col-span-2 rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h2 className="text-base font-semibold text-slate-900 dark:text-white">
                Recent Teaching Sessions
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Authoritative course sessions & execution status
              </p>
            </div>
            <Link
              href="/app/attendance/sessions"
              className="text-xs font-medium text-indigo-600 hover:underline dark:text-indigo-400"
            >
              View all &rarr;
            </Link>
          </div>

          <div className="mt-4">
            {loading ? (
              <div className="py-8 text-center text-sm text-slate-400">Loading session telemetry...</div>
            ) : !dashboard?.recent_sessions || dashboard.recent_sessions.length === 0 ? (
              <div className="py-8 text-center">
                <p className="text-sm font-medium text-slate-700 dark:text-slate-300">No attendance sessions recorded yet.</p>
                <p className="text-xs text-slate-400 mt-1">Sessions generated from timetable or created manually will appear here.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
                  <thead className="bg-slate-50 text-xs uppercase text-slate-400 dark:bg-slate-800/50">
                    <tr>
                      <th className="px-3 py-2.5">Date & Slot</th>
                      <th className="px-3 py-2.5">Course / Subject</th>
                      <th className="px-3 py-2.5">Section</th>
                      <th className="px-3 py-2.5">Faculty</th>
                      <th className="px-3 py-2.5">Status</th>
                      <th className="px-3 py-2.5 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {dashboard.recent_sessions.map((sess: AttendanceSession) => (
                      <tr key={sess.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                        <td className="px-3 py-3 font-medium text-slate-900 dark:text-white whitespace-nowrap">
                          <div>{sess.session_date}</div>
                          <div className="text-xs text-slate-400">P{sess.period_number} • {sess.start_time || "Scheduled"}</div>
                        </td>
                        <td className="px-3 py-3">
                          <div className="font-semibold text-slate-900 dark:text-white">{sess.course_code || "Course"}</div>
                          <div className="text-xs text-slate-400 truncate max-w-[180px]">{sess.course_name}</div>
                        </td>
                        <td className="px-3 py-3 whitespace-nowrap">
                          {sess.section_name || "General"}
                        </td>
                        <td className="px-3 py-3 whitespace-nowrap text-xs text-slate-500 dark:text-slate-400">
                          {sess.faculty_name || "Instructor"}
                        </td>
                        <td className="px-3 py-3 whitespace-nowrap">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                              sess.status === "LOCKED"
                                ? "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                                : sess.status === "MARKED"
                                ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                                : sess.status === "OPEN"
                                ? "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300"
                                : "bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300"
                            }`}
                          >
                            {sess.status}
                          </span>
                        </td>
                        <td className="px-3 py-3 text-right whitespace-nowrap">
                          <Link
                            href={`/app/attendance/sessions/${sess.id}`}
                            className="inline-flex items-center text-xs font-semibold text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 dark:hover:text-indigo-300"
                          >
                            {sess.status === "LOCKED" ? "View Register" : "Mark &rarr;"}
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Unresolved Low-Attendance Alerts (1 col) */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h2 className="text-base font-semibold text-slate-900 dark:text-white">
                Active Attendance Alerts
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Automated threshold breaches
              </p>
            </div>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300">
              {alerts.length} Active
            </span>
          </div>

          <div className="mt-4 space-y-3">
            {loading ? (
              <div className="py-8 text-center text-sm text-slate-400">Loading alerts...</div>
            ) : alerts.length === 0 ? (
              <div className="py-8 text-center">
                <svg className="mx-auto h-8 w-8 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
                <p className="mt-2 text-sm font-medium text-slate-700 dark:text-slate-300">No active attendance alerts</p>
                <p className="text-xs text-slate-400 mt-0.5">All student attendance complies with institutional thresholds.</p>
              </div>
            ) : (
              alerts.slice(0, 5).map((alert) => (
                <div
                  key={alert.id}
                  className={`rounded-lg border p-3 text-xs ${
                    alert.severity === "CRITICAL"
                      ? "border-rose-200 bg-rose-50/50 dark:border-rose-900/40 dark:bg-rose-950/20 text-rose-900 dark:text-rose-200"
                      : "border-amber-200 bg-amber-50/50 dark:border-amber-900/40 dark:bg-amber-950/20 text-amber-900 dark:text-amber-200"
                  }`}
                >
                  <div className="flex items-center justify-between font-semibold">
                    <span>{alert.student_name || "Student"}</span>
                    <span className="uppercase text-[10px] px-1.5 py-0.5 rounded font-bold bg-white/80 dark:bg-slate-900/80">
                      {alert.severity}
                    </span>
                  </div>
                  <p className="mt-1">{alert.message}</p>
                  <div className="mt-2 flex items-center justify-between text-[11px] opacity-80 pt-1.5 border-t border-slate-200/50 dark:border-slate-800">
                    <span>{alert.course_name || "Course"}</span>
                    <Link
                      href={`/app/attendance/students/${alert.student_id}`}
                      className="font-bold underline hover:opacity-100"
                    >
                      Audit Student &rarr;
                    </Link>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
