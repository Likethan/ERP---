"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { examinationsService } from "@/services/examinations.service";
import { ExamDashboardSummary } from "@/types/examinations";
import { StatCard } from "@/components/ui/stat-card";
import { Button } from "@/components/ui/button";
import {
  FileText,
  Calendar,
  FileSpreadsheet,
  Award,
  Globe,
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  BarChart3,
  CheckCircle2,
  Clock,
  Sparkles,
  Layers,
  GraduationCap,
} from "lucide-react";

export default function ExaminationHubPage() {
  const { hasPermission } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<ExamDashboardSummary | null>(null);

  useEffect(() => {
    async function loadTelemetry() {
      try {
        setLoading(true);
        setError(null);
        const res = await examinationsService.getDashboardSummary();
        setSummary(res.data);
      } catch (err: unknown) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load examination operations summary",
        );
      } finally {
        setLoading(false);
      }
    }

    loadTelemetry();
  }, []);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300">
              Controller of Examinations
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              Semester 5 • Evaluation Engine
            </span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Examination & Assessment Hub
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Course assessment configurations, timetable schedules, attendance
            eligibility gates, marks rosters, and ratified results publication.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <Link href="/app/examinations/marks">
            <Button variant="primary" size="sm" className="gap-1.5 text-xs">
              <FileSpreadsheet className="h-3.5 w-3.5" />
              Enter Marks
            </Button>
          </Link>
          <Link href="/app/examinations/schedules">
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              <Calendar className="h-3.5 w-3.5" />
              Schedule Exam
            </Button>
          </Link>
          <Link href="/app/examinations/reports">
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              <BarChart3 className="h-3.5 w-3.5" />
              Exam Reports
            </Button>
          </Link>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300">
          <p className="font-semibold">
            Unable to load Examination Operations Summary
          </p>
          <p className="mt-0.5">{error}</p>
        </div>
      )}

      {/* Critical Eligibility Attention Banner */}
      {summary && summary.ineligibleStudentsCount > 0 && (
        <div className="rounded-xl border border-amber-300 bg-amber-50/80 p-4 dark:border-amber-900/60 dark:bg-amber-950/40 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start sm:items-center gap-3">
            <div className="p-2 rounded-lg bg-amber-100 text-amber-800 dark:bg-amber-900/60 dark:text-amber-300 shrink-0">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-amber-950 dark:text-amber-200">
                Attendance Eligibility Bar: {summary.ineligibleStudentsCount}{" "}
                Students Ineligible
              </h2>
              <p className="text-xs text-amber-800 dark:text-amber-300/90 mt-0.5">
                Students below the 75% attendance threshold are debarred from
                the End Semester Examination pending formal HOD condonation
                review.
              </p>
            </div>
          </div>
          <Link href="/app/examinations/eligibility">
            <Button
              size="sm"
              variant="outline"
              className="text-xs whitespace-nowrap bg-white dark:bg-slate-900"
            >
              Review Eligibility Register
            </Button>
          </Link>
        </div>
      )}

      {/* Service-Derived Primary Operational KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Examination Cycles"
          value={
            loading ? "..." : String(summary?.activeExaminationsCount ?? 0)
          }
          description={`${summary?.upcomingExamsCount ?? 0} papers scheduled this cycle`}
          icon={<Calendar className="h-5 w-5 text-indigo-600" />}
        />
        <StatCard
          title="Configured Assessments"
          value={loading ? "..." : String(summary?.totalAssessmentsCount ?? 0)}
          description={`${summary?.pendingMarksCount ?? 0} rosters pending marks`}
          icon={<FileText className="h-5 w-5 text-blue-600" />}
        />
        <StatCard
          title="Marks Corrections Pending"
          value={
            loading ? "..." : String(summary?.marksAwaitingReviewCount ?? 0)
          }
          description="Awaiting HOD verification"
          icon={<Clock className="h-5 w-5 text-amber-600" />}
        />
        <StatCard
          title="Published Results"
          value={loading ? "..." : String(summary?.publishedResultsCount ?? 0)}
          description={`${summary?.resultsAwaitingPublicationCount ?? 0} batches ready to publish`}
          icon={<Award className="h-5 w-5 text-emerald-600" />}
        />
      </div>

      {/* Subsystem Navigation Grid (8 Modules) */}
      <div>
        <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
          Examination Operations Subsystems
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* 1. Assessment Schemes */}
          <Link
            href="/app/examinations/assessments"
            className="group rounded-xl border border-slate-200 bg-white p-5 shadow-xs hover:border-indigo-400 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="h-10 w-10 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-600 group-hover:bg-indigo-600 group-hover:text-white transition dark:bg-indigo-950/60 dark:text-indigo-400">
              <FileText className="h-5 w-5" />
            </div>
            <h3 className="mt-3.5 font-semibold text-slate-900 dark:text-white">
              Assessment Schemes
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 line-clamp-2">
              Configure course internal tests, lab practicals, quizzes, and
              end-semester weightage summing to 100%.
            </p>
            <div className="mt-3.5 flex items-center text-xs font-medium text-indigo-600 dark:text-indigo-400">
              Manage Schemes <ArrowRight className="h-3.5 w-3.5 ml-1" />
            </div>
          </Link>

          {/* 2. Exam Schedules */}
          <Link
            href="/app/examinations/schedules"
            className="group rounded-xl border border-slate-200 bg-white p-5 shadow-xs hover:border-indigo-400 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="h-10 w-10 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-600 group-hover:bg-emerald-600 group-hover:text-white transition dark:bg-emerald-950/60 dark:text-emerald-400">
              <Calendar className="h-5 w-5" />
            </div>
            <h3 className="mt-3.5 font-semibold text-slate-900 dark:text-white">
              Exam Timetable
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 line-clamp-2">
              Timetable schedules with conflict detection across room bookings,
              student clash, and invigilator rosters.
            </p>
            <div className="mt-3.5 flex items-center text-xs font-medium text-emerald-600 dark:text-emerald-400">
              View Schedules <ArrowRight className="h-3.5 w-3.5 ml-1" />
            </div>
          </Link>

          {/* 3. Student Eligibility */}
          <Link
            href="/app/examinations/eligibility"
            className="group rounded-xl border border-slate-200 bg-white p-5 shadow-xs hover:border-indigo-400 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="h-10 w-10 rounded-lg bg-amber-50 flex items-center justify-center text-amber-600 group-hover:bg-amber-600 group-hover:text-white transition dark:bg-amber-950/60 dark:text-amber-400">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <h3 className="mt-3.5 font-semibold text-slate-900 dark:text-white">
              Student Eligibility
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 line-clamp-2">
              Attendance-linked eligibility gates, debarment registers, and HOD
              medical condonation review.
            </p>
            <div className="mt-3.5 flex items-center text-xs font-medium text-amber-600 dark:text-amber-400">
              Check Eligibility <ArrowRight className="h-3.5 w-3.5 ml-1" />
            </div>
          </Link>

          {/* 4. Marks Entry */}
          <Link
            href="/app/examinations/marks"
            className="group rounded-xl border border-slate-200 bg-white p-5 shadow-xs hover:border-indigo-400 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="h-10 w-10 rounded-lg bg-purple-50 flex items-center justify-center text-purple-600 group-hover:bg-purple-600 group-hover:text-white transition dark:bg-purple-950/60 dark:text-purple-400">
              <FileSpreadsheet className="h-5 w-5" />
            </div>
            <h3 className="mt-3.5 font-semibold text-slate-900 dark:text-white">
              Marks Entry Roster
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 line-clamp-2">
              Keyboard-friendly class marks scoring, absent/malpractice flags,
              draft auto-saves, and finalization.
            </p>
            <div className="mt-3.5 flex items-center text-xs font-medium text-purple-600 dark:text-purple-400">
              Open Marks Matrix <ArrowRight className="h-3.5 w-3.5 ml-1" />
            </div>
          </Link>

          {/* 5. Results & GPA */}
          <Link
            href="/app/examinations/results"
            className="group rounded-xl border border-slate-200 bg-white p-5 shadow-xs hover:border-indigo-400 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="h-10 w-10 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition dark:bg-blue-950/60 dark:text-blue-400">
              <Award className="h-5 w-5" />
            </div>
            <h3 className="mt-3.5 font-semibold text-slate-900 dark:text-white">
              Results & GPA
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 line-clamp-2">
              Automated 10-point CBCS grade point assignment, component score
              weighting, and pass/fail classification.
            </p>
            <div className="mt-3.5 flex items-center text-xs font-medium text-blue-600 dark:text-blue-400">
              Explore Results <ArrowRight className="h-3.5 w-3.5 ml-1" />
            </div>
          </Link>

          {/* 6. Result Publications */}
          <Link
            href="/app/examinations/publications"
            className="group rounded-xl border border-slate-200 bg-white p-5 shadow-xs hover:border-indigo-400 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="h-10 w-10 rounded-lg bg-teal-50 flex items-center justify-center text-teal-600 group-hover:bg-teal-600 group-hover:text-white transition dark:bg-teal-950/60 dark:text-teal-400">
              <Globe className="h-5 w-5" />
            </div>
            <h3 className="mt-3.5 font-semibold text-slate-900 dark:text-white">
              Publications Ledger
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 line-clamp-2">
              Controlled batch publishing to student portals, audit stamping,
              and formal revocation controls.
            </p>
            <div className="mt-3.5 flex items-center text-xs font-medium text-teal-600 dark:text-teal-400">
              Manage Batches <ArrowRight className="h-3.5 w-3.5 ml-1" />
            </div>
          </Link>

          {/* 7. Grade Scale Rules */}
          <Link
            href="/app/examinations/results"
            className="group rounded-xl border border-slate-200 bg-white p-5 shadow-xs hover:border-indigo-400 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="h-10 w-10 rounded-lg bg-rose-50 flex items-center justify-center text-rose-600 group-hover:bg-rose-600 group-hover:text-white transition dark:bg-rose-950/60 dark:text-rose-400">
              <GraduationCap className="h-5 w-5" />
            </div>
            <h3 className="mt-3.5 font-semibold text-slate-900 dark:text-white">
              Grade Scale Rules
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 line-clamp-2">
              UGC 10-point CBCS scale definition, minimum pass thresholds, and
              grade point conversion parameters.
            </p>
            <div className="mt-3.5 flex items-center text-xs font-medium text-rose-600 dark:text-rose-400">
              View Grade Scales <ArrowRight className="h-3.5 w-3.5 ml-1" />
            </div>
          </Link>

          {/* 8. Audit Reports */}
          <Link
            href="/app/examinations/reports"
            className="group rounded-xl border border-slate-200 bg-white p-5 shadow-xs hover:border-indigo-400 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="h-10 w-10 rounded-lg bg-cyan-50 flex items-center justify-center text-cyan-600 group-hover:bg-cyan-600 group-hover:text-white transition dark:bg-cyan-950/60 dark:text-cyan-400">
              <BarChart3 className="h-5 w-5" />
            </div>
            <h3 className="mt-3.5 font-semibold text-slate-900 dark:text-white">
              Examination Reports
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 line-clamp-2">
              Comprehensive marks rosters, timetable matrices, eligibility
              audits, and instant CSV data export.
            </p>
            <div className="mt-3.5 flex items-center text-xs font-medium text-cyan-600 dark:text-cyan-400">
              Compile Reports <ArrowRight className="h-3.5 w-3.5 ml-1" />
            </div>
          </Link>
        </div>
      </div>

      {/* Operational Visualizations: Grade Distribution & Department Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Grade Distribution Bar Chart */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800">
            <div>
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                Grade Distribution (Semester 5 Results)
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                10-Point UGC Choice Based Credit System outcome
              </p>
            </div>
            <span className="text-xs font-medium px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
              96.2% Pass Rate
            </span>
          </div>

          <div className="mt-5 space-y-3">
            {summary?.gradeDistribution.map((item) => (
              <div key={item.grade} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-700 dark:text-slate-200 w-8">
                    {item.grade}
                  </span>
                  <span className="text-slate-500 dark:text-slate-400">
                    {item.count} students ({item.percentage}%)
                  </span>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      item.grade === "A+"
                        ? "bg-indigo-600"
                        : item.grade === "A"
                          ? "bg-blue-600"
                          : item.grade === "B+"
                            ? "bg-emerald-500"
                            : item.grade === "B"
                              ? "bg-teal-500"
                              : item.grade === "C"
                                ? "bg-amber-500"
                                : item.grade === "D"
                                  ? "bg-orange-500"
                                  : "bg-rose-500"
                    }`}
                    style={{ width: `${Math.max(item.percentage, 2)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Department Academic Performance */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800">
            <div>
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                Department Performance Benchmarks
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Passing percentage by engineering department
              </p>
            </div>
            <Link
              href="/app/examinations/results"
              className="text-xs font-medium text-indigo-600 dark:text-indigo-400 hover:underline"
            >
              View all results &rarr;
            </Link>
          </div>

          <div className="mt-5 space-y-4">
            {summary?.departmentPerformance.map((dept) => (
              <div
                key={dept.department}
                className="p-3.5 rounded-lg border border-slate-100 bg-slate-50/60 dark:border-slate-800 dark:bg-slate-800/40"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                    {dept.department}
                  </span>
                  <span className="text-xs font-bold text-indigo-600 dark:text-indigo-400">
                    {dept.passRate}% pass
                  </span>
                </div>
                <div className="mt-2 h-2 w-full rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-indigo-600 transition-all duration-500"
                    style={{ width: `${dept.passRate}%` }}
                  />
                </div>
                <p className="mt-1.5 text-[11px] text-slate-400">
                  {dept.studentCount} enrolled candidates evaluated in current
                  term
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
