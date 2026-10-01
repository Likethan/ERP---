"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import type { LowAttendanceStudentItem, CourseOffering } from "@campusos/types";

export default function LowAttendanceStudentsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [students, setStudents] = useState<LowAttendanceStudentItem[]>([]);
  const [courseOfferings, setCourseOfferings] = useState<CourseOffering[]>([]);

  // Filter states
  const [threshold, setThreshold] = useState<number>(75);
  const [selectedCourse, setSelectedCourse] = useState<string>("");

  async function loadData() {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (threshold) params.append("threshold", threshold.toString());
      if (selectedCourse) params.append("course_offering_id", selectedCourse);

      const [stuRes, offRes] = await Promise.all([
        apiFetch<LowAttendanceStudentItem[]>(
          `/api/v1/attendance/low-attendance?${params.toString()}`
        ),
        apiFetch<CourseOffering[]>("/api/v1/academics/course-offerings"),
      ]);

      setStudents(stuRes.data || []);
      setCourseOfferings(offRes.data || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load low-attendance students.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [threshold, selectedCourse]);

  const criticalCount = students.filter((s) => s.status === "CRITICAL").length;
  const warningCount = students.filter((s) => s.status === "WARNING").length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Link
              href="/app/attendance"
              className="text-xs font-medium text-slate-500 hover:text-indigo-600 dark:text-slate-400 dark:hover:text-indigo-400"
            >
              &larr; Attendance Engine
            </Link>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Low Attendance Risk Telemetry
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Real-time threshold evaluation identifying students at risk of attendance shortage or condonation penalty.
          </p>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300">
          {error}
        </div>
      )}

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider dark:text-slate-400">
            Total Flagged Students
          </span>
          <div className="mt-2 text-3xl font-bold text-slate-900 dark:text-white">
            {loading ? "..." : students.length}
          </div>
          <p className="mt-1 text-xs text-slate-400">Below configured evaluation threshold</p>
        </div>

        <div className="rounded-xl border border-rose-200 bg-rose-50/50 p-5 shadow-xs dark:border-rose-900/40 dark:bg-rose-950/20">
          <span className="text-xs font-semibold text-rose-700 uppercase tracking-wider dark:text-rose-300">
            Critical Threshold Breaches
          </span>
          <div className="mt-2 text-3xl font-bold text-rose-600 dark:text-rose-400">
            {loading ? "..." : criticalCount}
          </div>
          <p className="mt-1 text-xs text-rose-600/80 dark:text-rose-400/80">Severe shortage (&lt;65%)</p>
        </div>

        <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-5 shadow-xs dark:border-amber-900/40 dark:bg-amber-950/20">
          <span className="text-xs font-semibold text-amber-700 uppercase tracking-wider dark:text-amber-300">
            Warning Threshold Breaches
          </span>
          <div className="mt-2 text-3xl font-bold text-amber-600 dark:text-amber-400">
            {loading ? "..." : warningCount}
          </div>
          <p className="mt-1 text-xs text-amber-600/80 dark:text-amber-400/80">At risk of falling below minimum</p>
        </div>
      </div>

      {/* Threshold & Course Filter Controls */}
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs dark:border-slate-800 dark:bg-slate-900 flex flex-wrap gap-4 items-center justify-between">
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Minimum Threshold: {threshold}%
            </label>
            <div className="flex items-center gap-2">
              <input
                type="range"
                min="50"
                max="90"
                step="5"
                value={threshold}
                onChange={(e) => setThreshold(parseInt(e.target.value))}
                className="w-40 cursor-pointer"
              />
              <span className="text-xs font-bold text-slate-700 dark:text-slate-300">
                {threshold}%
              </span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Filter by Course Offering
            </label>
            <select
              value={selectedCourse}
              onChange={(e) => setSelectedCourse(e.target.value)}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white max-w-xs"
            >
              <option value="">All Courses</option>
              {courseOfferings.map((co) => (
                <option key={co.id} value={co.id}>
                  {co.subject_code} - {co.subject_name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <button
          type="button"
          onClick={() => {
            setThreshold(75);
            setSelectedCourse("");
          }}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800 transition"
        >
          Reset Filters
        </button>
      </div>

      {/* Low Attendance Table */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden dark:border-slate-800 dark:bg-slate-900">
        {loading ? (
          <div className="py-12 text-center text-sm text-slate-400">
            Evaluating student attendance against policy thresholds...
          </div>
        ) : students.length === 0 ? (
          <div className="py-12 text-center">
            <svg
              className="mx-auto h-10 w-10 text-emerald-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="mt-2 text-sm font-semibold text-slate-800 dark:text-slate-200">
              No students are below the configured attendance threshold.
            </p>
            <p className="text-xs text-slate-400 mt-1">
              All students have attendance equal to or greater than {threshold}%.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="bg-slate-50 text-xs uppercase text-slate-400 border-b border-slate-100 dark:bg-slate-800/50 dark:border-slate-800">
                <tr>
                  <th className="px-4 py-3">Student Name & Roll</th>
                  <th className="px-4 py-3">Course / Subject</th>
                  <th className="px-4 py-3">Program & Section</th>
                  <th className="px-4 py-3">Sessions Attended</th>
                  <th className="px-4 py-3">Current %</th>
                  <th className="px-4 py-3">Threshold</th>
                  <th className="px-4 py-3">Risk Level</th>
                  <th className="px-4 py-3 text-right">Audit</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {students.map((item, idx) => (
                  <tr
                    key={`${item.student_id}-${item.course_offering_id}-${idx}`}
                    className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40"
                  >
                    <td className="px-4 py-3.5 whitespace-nowrap">
                      <div className="font-semibold text-slate-900 dark:text-white">
                        {item.student_name}
                      </div>
                      <div className="text-xs text-slate-400">
                        {item.roll_number || item.admission_number}
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="font-medium text-slate-900 dark:text-white">
                        {item.course_code}
                      </div>
                      <div className="text-xs text-slate-400 truncate max-w-xs">
                        {item.course_name}
                      </div>
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap text-xs text-slate-500 dark:text-slate-400">
                      <div>{item.program_name || "Program"}</div>
                      <div className="text-[11px] text-slate-400">{item.section_name || "Section"}</div>
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap">
                      <span className="font-semibold text-slate-800 dark:text-slate-200">
                        {item.attended_sessions}
                      </span>{" "}
                      <span className="text-xs text-slate-400">/ {item.total_conducted}</span>
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap font-bold text-rose-600 dark:text-rose-400">
                      {item.attendance_percentage}%
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap text-xs text-slate-500 dark:text-slate-400">
                      {item.threshold_percentage}%
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold uppercase ${
                          item.status === "CRITICAL"
                            ? "bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300"
                            : "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300"
                        }`}
                      >
                        {item.status}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-right whitespace-nowrap">
                      <Link
                        href={`/app/attendance/students/${item.student_id}`}
                        className="text-xs font-semibold text-indigo-600 hover:underline dark:text-indigo-400"
                      >
                        Student Profile &rarr;
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
  );
}
