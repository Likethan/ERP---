"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { examinationsService } from "@/services/examinations.service";
import type { ExaminationDashboard } from "@campusos/types";

export default function ExaminationHubPage() {
  const { hasPermission } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<ExaminationDashboard | null>(null);

  useEffect(() => {
    async function loadTelemetry() {
      try {
        setLoading(true);
        setError(null);
        const res = await apiFetch<ExaminationDashboard>("/api/v1/examinations/dashboard");
        setDashboard(res.data);
      } catch {
        const mockRes = await examinationsService.getDashboard();
        setDashboard(mockRes.data as unknown as ExaminationDashboard);
      } finally {
        setLoading(false);
      }
    }

    loadTelemetry();
  }, []);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300">
              CampusOS Engine
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">Step 7 Authoritative</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Examination & Assessment Engine
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Course assessment configurations, conflict-free exam timetables, bulk marks entry, grade calculations, and controlled result publication.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {hasPermission("marks:enter") && (
            <Link
              href="/app/examinations/marks"
              className="inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 transition"
            >
              + Enter Marks
            </Link>
          )}
          {hasPermission("examinations:create") && (
            <Link
              href="/app/examinations/schedules"
              className="inline-flex items-center justify-center rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 transition"
            >
              Schedule Exam
            </Link>
          )}
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300">
          <p className="font-semibold">Unable to load Examination Hub</p>
          <p className="mt-0.5">{error}</p>
        </div>
      )}

      {/* KPI Telemetry Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Active Terms */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider dark:text-slate-400">
              Active Exam Cycles
            </span>
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-900 dark:text-white">
              {loading ? "..." : (dashboard?.active_terms_count ?? 0)}
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">ongoing terms</span>
          </div>
        </div>

        {/* Assessments Pending Marks */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider dark:text-slate-400">
              Pending Marks Entry
            </span>
            <span className="h-2 w-2 rounded-full bg-amber-500" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-900 dark:text-white">
              {loading ? "..." : (dashboard?.assessments_pending_marks ?? 0)}
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">components open</span>
          </div>
        </div>

        {/* Results Awaiting Publication */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider dark:text-slate-400">
              Awaiting Publication
            </span>
            <span className="h-2 w-2 rounded-full bg-purple-500" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-900 dark:text-white">
              {loading ? "..." : (dashboard?.results_awaiting_publication_count ?? 0)}
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">finalized results</span>
          </div>
        </div>

        {/* Published Results Count */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider dark:text-slate-400">
              Published Results
            </span>
            <span className="h-2 w-2 rounded-full bg-blue-500" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-900 dark:text-white">
              {loading ? "..." : (dashboard?.total_published_results_count ?? 0)}
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">visible to students</span>
          </div>
        </div>
      </div>

      {/* Primary Subsystem Navigation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <Link
          href="/app/examinations/assessments"
          className="group rounded-xl border border-slate-200 bg-white p-5 shadow-xs hover:border-indigo-400 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900 dark:hover:border-indigo-600"
        >
          <div className="h-10 w-10 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-600 group-hover:bg-indigo-600 group-hover:text-white transition dark:bg-indigo-950/60 dark:text-indigo-400">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth="1.75" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 6a7.5 7.5 0 1 0 7.5 7.5h-7.5V6Z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 10.5H21A7.5 7.5 0 0 0 13.5 3v7.5Z" />
            </svg>
          </div>
          <h2 className="mt-4 font-semibold text-slate-900 dark:text-white">Assessment Schemes</h2>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Configure internal, practical, and end-semester components with weightage summing to 100%.
          </p>
          <div className="mt-4 flex items-center text-xs font-medium text-indigo-600 dark:text-indigo-400">
            Manage Schemes &rarr;
          </div>
        </Link>

        <Link
          href="/app/examinations/schedules"
          className="group rounded-xl border border-slate-200 bg-white p-5 shadow-xs hover:border-indigo-400 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900 dark:hover:border-indigo-600"
        >
          <div className="h-10 w-10 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-600 group-hover:bg-emerald-600 group-hover:text-white transition dark:bg-emerald-950/60 dark:text-emerald-400">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth="1.75" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5" />
            </svg>
          </div>
          <h2 className="mt-4 font-semibold text-slate-900 dark:text-white">Exam Timetable</h2>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Schedule papers with automatic conflict checks for room overlaps, student clashes, and invigilators.
          </p>
          <div className="mt-4 flex items-center text-xs font-medium text-emerald-600 dark:text-emerald-400">
            Schedule Timetable &rarr;
          </div>
        </Link>

        <Link
          href="/app/examinations/marks"
          className="group rounded-xl border border-slate-200 bg-white p-5 shadow-xs hover:border-indigo-400 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900 dark:hover:border-indigo-600"
        >
          <div className="h-10 w-10 rounded-lg bg-amber-50 flex items-center justify-center text-amber-600 group-hover:bg-amber-600 group-hover:text-white transition dark:bg-amber-950/60 dark:text-amber-400">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth="1.75" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25Z" />
            </svg>
          </div>
          <h2 className="mt-4 font-semibold text-slate-900 dark:text-white">Marks Entry Roster</h2>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            High-efficiency class roster entry, non-numeric statuses (ABSENT, MALPRACTICE), and draft saves.
          </p>
          <div className="mt-4 flex items-center text-xs font-medium text-amber-600 dark:text-amber-400">
            Open Marks Grid &rarr;
          </div>
        </Link>

        <Link
          href="/app/examinations/results"
          className="group rounded-xl border border-slate-200 bg-white p-5 shadow-xs hover:border-indigo-400 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900 dark:hover:border-indigo-600"
        >
          <div className="h-10 w-10 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition dark:bg-blue-950/60 dark:text-blue-400">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth="1.75" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.26 10.147a60.438 60.438 0 0 0-.491 6.347A48.62 48.62 0 0 1 12 20.904a48.62 48.62 0 0 1 8.232-4.41 60.46 60.46 0 0 0-.491-6.347m-15.482 0a50.636 50.636 0 0 0-2.658-.813A59.906 59.906 0 0 1 12 3.493a59.903 59.903 0 0 1 10.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.717 50.717 0 0 1 12 13.489a50.702 50.702 0 0 1 7.74-3.342" />
            </svg>
          </div>
          <h2 className="mt-4 font-semibold text-slate-900 dark:text-white">Results & Publication</h2>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Automated grade mapping, semester GPA computation, transcript generation, and controlled publication.
          </p>
          <div className="mt-4 flex items-center text-xs font-medium text-blue-600 dark:text-blue-400">
            View Results &rarr;
          </div>
        </Link>
      </div>

      {/* Operational Overviews */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Assessments */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800">
            <h3 className="text-base font-semibold text-slate-900 dark:text-white">Configured Assessments</h3>
            <Link href="/app/examinations/assessments" className="text-xs font-medium text-indigo-600 hover:text-indigo-700 dark:text-indigo-400">
              View all
            </Link>
          </div>

          <div className="mt-4 divide-y divide-slate-100 dark:divide-slate-800">
            {dashboard?.recent_assessments && dashboard.recent_assessments.length > 0 ? (
              dashboard.recent_assessments.map((a) => (
                <div key={a.id} className="py-3 flex items-center justify-between text-sm">
                  <div>
                    <p className="font-medium text-slate-900 dark:text-white">{a.title}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      {a.course_code ? `${a.course_code} • ` : ""}Weightage: {a.weightage_percent}% • Max: {a.max_marks}
                    </p>
                  </div>
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                      a.is_finalized
                        ? "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300"
                        : "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300"
                    }`}
                  >
                    {a.is_finalized ? "LOCKED" : a.status}
                  </span>
                </div>
              ))
            ) : (
              <p className="py-8 text-center text-sm text-slate-500 dark:text-slate-400">
                No assessments configured yet. Create one via Assessment Schemes.
              </p>
            )}
          </div>
        </div>

        {/* Upcoming Examination Schedules */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800">
            <h3 className="text-base font-semibold text-slate-900 dark:text-white">Upcoming Timetables</h3>
            <Link href="/app/examinations/schedules" className="text-xs font-medium text-indigo-600 hover:text-indigo-700 dark:text-indigo-400">
              Full schedule
            </Link>
          </div>

          <div className="mt-4 divide-y divide-slate-100 dark:divide-slate-800">
            {dashboard?.upcoming_schedules && dashboard.upcoming_schedules.length > 0 ? (
              dashboard.upcoming_schedules.map((s) => (
                <div key={s.id} className="py-3 flex items-center justify-between text-sm">
                  <div>
                    <p className="font-medium text-slate-900 dark:text-white">
                      {s.course_code ? `${s.course_code} - ` : ""}{s.assessment_title || "Examination Paper"}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      {s.exam_date} • {s.start_time} - {s.end_time} • Room: {s.room_identifier}
                    </p>
                  </div>
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300">
                    {s.status}
                  </span>
                </div>
              ))
            ) : (
              <p className="py-8 text-center text-sm text-slate-500 dark:text-slate-400">
                No examination schedules queued. Configure timetables in Exam Timetable.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
