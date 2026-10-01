"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type {
  StudentOverallAttendanceSummary,
  AttendanceAlert,
  StudentCourseAttendanceSummary,
  AttendanceRecord,
} from "@campusos/types";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function StudentAttendanceDetailPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const studentId = resolvedParams.id;
  const { hasPermission } = useAuth();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<StudentOverallAttendanceSummary | null>(null);

  useEffect(() => {
    async function loadSummary() {
      try {
        setLoading(true);
        setError(null);

        const res = await apiFetch<StudentOverallAttendanceSummary>(
          `/api/v1/attendance/students/${studentId}/summary`
        );
        setSummary(res.data);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load student attendance summary.");
      } finally {
        setLoading(false);
      }
    }

    loadSummary();
  }, [studentId]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Link
              href="/app/attendance/students"
              className="text-xs font-medium text-slate-500 hover:text-indigo-600 dark:text-slate-400 dark:hover:text-indigo-400"
            >
              &larr; Risk Telemetry
            </Link>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            {summary?.student_name || "Student Attendance Profile"}
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Roll: <strong className="text-slate-700 dark:text-slate-300">{summary?.roll_number || "—"}</strong> •
            Admission: <strong className="text-slate-700 dark:text-slate-300">{summary?.admission_number}</strong> •
            Program: <strong className="text-slate-700 dark:text-slate-300">{summary?.program_name || "General"}</strong> •
            Section: <strong className="text-slate-700 dark:text-slate-300">{summary?.section_name || "A"}</strong>
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {hasPermission("leave:create") && (
            <Link
              href="/app/attendance/leaves"
              className="inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 transition"
            >
              Apply Leave
            </Link>
          )}
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300">
          {error}
        </div>
      )}

      {/* Top Telemetry KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Overall Percentage */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider dark:text-slate-400">
            Overall Attendance Rate
          </span>
          <div className="mt-2 flex items-baseline gap-2">
            <span
              className={`text-3xl font-extrabold ${
                (summary?.overall_percentage ?? 100) < 65
                  ? "text-rose-600 dark:text-rose-400"
                  : (summary?.overall_percentage ?? 100) < 75
                  ? "text-amber-500"
                  : "text-emerald-600 dark:text-emerald-400"
              }`}
            >
              {loading ? "..." : `${summary?.overall_percentage ?? 100}%`}
            </span>
            <span className="text-xs text-slate-400">
              (Min: {summary?.minimum_required_percentage ?? 75}%)
            </span>
          </div>
          <div className="mt-3 text-xs flex items-center justify-between text-slate-500 dark:text-slate-400 border-t border-slate-100 dark:border-slate-800 pt-2.5">
            <span>Status:</span>
            <span
              className={`font-bold uppercase text-[11px] px-2 py-0.5 rounded-full ${
                summary?.status === "CRITICAL"
                  ? "bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300"
                  : summary?.status === "WARNING"
                  ? "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300"
                  : "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
              }`}
            >
              {summary?.status || "NORMAL"}
            </span>
          </div>
        </div>

        {/* Sessions Attended */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider dark:text-slate-400">
            Sessions Attended
          </span>
          <div className="mt-2 text-3xl font-bold text-slate-900 dark:text-white">
            {loading ? "..." : summary?.total_attended_sessions ?? 0}
          </div>
          <p className="mt-1 text-xs text-slate-400">
            Present + Excused/Leave sessions
          </p>
        </div>

        {/* Total Sessions Conducted */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider dark:text-slate-400">
            Total Sessions Conducted
          </span>
          <div className="mt-2 text-3xl font-bold text-slate-900 dark:text-white">
            {loading ? "..." : summary?.total_conducted_sessions ?? 0}
          </div>
          <p className="mt-1 text-xs text-slate-400">Teaching hours recorded</p>
        </div>

        {/* Total Courses Enrolled */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider dark:text-slate-400">
            Enrolled Courses
          </span>
          <div className="mt-2 text-3xl font-bold text-slate-900 dark:text-white">
            {loading ? "..." : summary?.courses.length ?? 0}
          </div>
          <p className="mt-1 text-xs text-slate-400">Under active curriculum term</p>
        </div>
      </div>

      {/* Active Alerts (if any) */}
      {summary?.alerts && summary.alerts.length > 0 && (
        <div className="rounded-xl border border-rose-200 bg-rose-50/50 p-4 dark:border-rose-900/40 dark:bg-rose-950/20">
          <h3 className="text-xs font-bold uppercase tracking-wider text-rose-800 dark:text-rose-300">
            Active Attendance Alerts
          </h3>
          <div className="mt-2 space-y-2">
            {summary.alerts.map((al: AttendanceAlert) => (
              <div
                key={al.id}
                className="text-xs flex items-center justify-between text-rose-900 dark:text-rose-200"
              >
                <span>
                  • <strong>{al.course_name || "Course"}</strong>: {al.message}
                </span>
                <span className="font-mono text-[10px] uppercase font-bold">
                  {al.severity}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Subject-Wise Breakdown Table */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden dark:border-slate-800 dark:bg-slate-900">
        <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-800">
          <h2 className="text-base font-semibold text-slate-900 dark:text-white">
            Course-Wise Attendance Breakdown
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Individual course session metrics derived from authoritative teaching registers.
          </p>
        </div>

        {loading ? (
          <div className="py-12 text-center text-sm text-slate-400">Loading course breakdown...</div>
        ) : !summary?.courses || summary.courses.length === 0 ? (
          <div className="py-12 text-center">
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              No course attendance records found for this student.
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Ensure student has active course enrollments and sessions have been marked.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="bg-slate-50 text-xs uppercase text-slate-400 border-b border-slate-100 dark:bg-slate-800/50 dark:border-slate-800">
                <tr>
                  <th className="px-4 py-3">Subject / Course</th>
                  <th className="px-4 py-3">Faculty Instructor</th>
                  <th className="px-4 py-3 text-center">Conducted</th>
                  <th className="px-4 py-3 text-center">Attended</th>
                  <th className="px-4 py-3 text-center">Breakdown (P / A / L / E)</th>
                  <th className="px-4 py-3 text-right">Attendance %</th>
                  <th className="px-4 py-3 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {summary.courses.map((course: StudentCourseAttendanceSummary) => (
                  <tr key={course.course_offering_id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                    <td className="px-4 py-3.5">
                      <div className="font-semibold text-slate-900 dark:text-white">
                        {course.subject_code}
                      </div>
                      <div className="text-xs text-slate-400">{course.subject_name}</div>
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap text-xs text-slate-500 dark:text-slate-400">
                      {course.faculty_name || "Instructor"}
                    </td>
                    <td className="px-4 py-3.5 text-center font-medium text-slate-900 dark:text-white">
                      {course.total_conducted}
                    </td>
                    <td className="px-4 py-3.5 text-center font-bold text-slate-900 dark:text-white">
                      {course.attended_sessions}
                    </td>
                    <td className="px-4 py-3.5 text-center whitespace-nowrap text-xs">
                      <span className="text-emerald-600 font-semibold">{course.present_count}P</span> •{" "}
                      <span className="text-rose-600 font-semibold">{course.absent_count}A</span> •{" "}
                      <span className="text-amber-500 font-semibold">{course.late_count}L</span> •{" "}
                      <span className="text-blue-500 font-semibold">{course.excused_count + course.leave_count}E</span>
                    </td>
                    <td className="px-4 py-3.5 text-right whitespace-nowrap font-extrabold">
                      <span
                        className={
                          course.attendance_percentage < 65
                            ? "text-rose-600 dark:text-rose-400"
                            : course.attendance_percentage < 75
                            ? "text-amber-500"
                            : "text-emerald-600 dark:text-emerald-400"
                        }
                      >
                        {course.attendance_percentage}%
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-center whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                          course.status === "CRITICAL"
                            ? "bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300"
                            : course.status === "WARNING"
                            ? "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300"
                            : "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                        }`}
                      >
                        {course.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Recent Session Records Log */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden dark:border-slate-800 dark:bg-slate-900">
        <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-800">
          <h2 className="text-base font-semibold text-slate-900 dark:text-white">
            Recent Attendance History
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Log of teaching sessions marked for this student.
          </p>
        </div>

        {loading ? (
          <div className="py-8 text-center text-sm text-slate-400">Loading history...</div>
        ) : !summary?.recent_records || summary.recent_records.length === 0 ? (
          <div className="py-8 text-center">
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              No recent attendance records.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="bg-slate-50 text-xs uppercase text-slate-400 border-b border-slate-100 dark:bg-slate-800/50 dark:border-slate-800">
                <tr>
                  <th className="px-4 py-2.5">Date Marked</th>
                  <th className="px-4 py-2.5">Status</th>
                  <th className="px-4 py-2.5">Remarks / Reason</th>
                  <th className="px-4 py-2.5">Leave Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {summary.recent_records.map((rec: AttendanceRecord) => (
                  <tr key={rec.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                    <td className="px-4 py-2.5 text-xs font-medium text-slate-900 dark:text-white whitespace-nowrap">
                      {new Date(rec.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-2.5 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                          rec.status === "PRESENT"
                            ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                            : rec.status === "ABSENT"
                            ? "bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300"
                            : rec.status === "LATE"
                            ? "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300"
                            : rec.status === "ON_LEAVE"
                            ? "bg-purple-100 text-purple-800 dark:bg-purple-950/60 dark:text-purple-300"
                            : "bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300"
                        }`}
                      >
                        {rec.status}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-xs text-slate-500 dark:text-slate-400">
                      {rec.remarks || "—"}
                    </td>
                    <td className="px-4 py-2.5 text-xs whitespace-nowrap">
                      {rec.has_approved_leave ? (
                        <span className="text-purple-600 font-semibold">Excused by Leave</span>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
