"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { attendanceService } from "@/services/attendance.service";
import { AttendanceStudentSummary, AttendanceRiskLevel } from "@/types/attendance";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/ui/stat-card";
import { useToast } from "@/components/ui/toast";
import {
  ArrowLeft,
  CalendarCheck,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  Clock,
  TrendingDown,
  TrendingUp,
  FileCheck2,
  ExternalLink,
  BookOpen,
} from "lucide-react";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function StudentAttendanceProfilePage({ params }: PageProps) {
  const resolvedParams = use(params);
  const studentId = resolvedParams.id;
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<AttendanceStudentSummary | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const res = await attendanceService.getStudentAttendanceSummary(studentId);
        if (res.success && res.data) {
          setSummary(res.data);
        }
      } catch (err) {
        console.error("Failed to load student attendance summary", err);
        showToast({ type: "error", title: "Load Error", message: "Failed to load student attendance summary." });
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [studentId]);

  if (loading && !summary) {
    return (
      <div className="flex items-center justify-center min-h-[300px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-12 text-center dark:border-slate-800 dark:bg-slate-900">
        <h3 className="text-base font-semibold text-slate-900 dark:text-white">Student Not Found</h3>
        <p className="mt-1 text-xs text-slate-500">Could not resolve attendance records for this student.</p>
        <Link href="/app/attendance/students" className="mt-4 inline-block">
          <Button variant="outline" size="sm">Back to Student Directory</Button>
        </Link>
      </div>
    );
  }

  const getRiskBadge = (risk: AttendanceRiskLevel) => {
    switch (risk) {
      case "HEALTHY":
        return <Badge variant="success">Healthy (&ge;80%)</Badge>;
      case "WARNING":
        return <Badge variant="warning">Warning (&lt;80%)</Badge>;
      case "CRITICAL":
        return <Badge variant="destructive">Critical Shortage (&lt;65%)</Badge>;
      default:
        return <Badge variant="outline">{risk}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5 dark:border-slate-800">
        <div className="flex items-center gap-3">
          <Link href="/app/attendance/students">
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
                {summary.studentName}
              </h1>
              {getRiskBadge(summary.riskLevel)}
            </div>
            <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
              Roll No: <strong className="text-slate-700 dark:text-slate-300">{summary.rollNumber}</strong> •{" "}
              {summary.program} • Semester {summary.semester}, Section {summary.section}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <Link href={`/app/students/${summary.studentId}`}>
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              <ExternalLink className="h-3.5 w-3.5" />
              Student 360° Profile
            </Button>
          </Link>
          <Link href="/app/attendance/leaves">
            <Button variant="primary" size="sm" className="gap-1.5 text-xs">
              <FileCheck2 className="h-3.5 w-3.5" />
              Apply Leave
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Overall Attendance"
          value={`${summary.percentage}%`}
          description={`${summary.attendedSessions} of ${summary.totalSessions} sessions attended`}
          icon={<CalendarCheck className="h-5 w-5 text-indigo-600" />}
        />
        <StatCard
          title="Present Sessions"
          value={String(summary.presentCount)}
          description="Full lecture attendance"
          icon={<CheckCircle2 className="h-5 w-5 text-emerald-600" />}
        />
        <StatCard
          title="Absences & Shortages"
          value={String(summary.absentCount)}
          description={`${summary.lateCount} late punches (0.5x credit)`}
          icon={<AlertTriangle className="h-5 w-5 text-rose-600" />}
        />
        <StatCard
          title="Excused Leave Sessions"
          value={String(summary.excusedCount)}
          description="Approved medical / on-duty events"
          icon={<Clock className="h-5 w-5 text-blue-600" />}
        />
      </div>

      {/* Two Column Layout: Weekly Trend & Course Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Trend Visualization */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900 lg:col-span-1">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                Semester Attendance Trend
              </h3>
              <p className="text-[11px] text-slate-500">Weekly progression curve</p>
            </div>
            {summary.percentage >= 80 ? (
              <span className="flex items-center gap-1 text-xs text-emerald-600 font-semibold">
                <TrendingUp className="h-3.5 w-3.5" /> Stable
              </span>
            ) : (
              <span className="flex items-center gap-1 text-xs text-rose-600 font-semibold">
                <TrendingDown className="h-3.5 w-3.5" /> Shortage
              </span>
            )}
          </div>

          <div className="mt-4 space-y-4">
            {summary.trend.map((w) => (
              <div key={w.period} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="font-medium text-slate-700 dark:text-slate-300">{w.period}</span>
                  <span className="font-bold text-slate-900 dark:text-white">
                    {w.percentage}% <span className="text-[10px] text-slate-400 font-normal">({w.present}/{w.total})</span>
                  </span>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      w.percentage >= 85
                        ? "bg-emerald-500"
                        : w.percentage >= 75
                        ? "bg-amber-500"
                        : "bg-rose-500"
                    }`}
                    style={{ width: `${w.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 pt-3 border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-500">
            <span className="font-semibold text-slate-700 dark:text-slate-300">Policy Note: </span>
            A minimum of 75% aggregate attendance is mandatory under University Autonomous Regulation 2026.
          </div>
        </div>

        {/* Right Column: Course Breakdown Table */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900 lg:col-span-2">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                Course Offering Attendance Breakdown
              </h3>
              <p className="text-[11px] text-slate-500">Subject-wise delivery and eligibility threshold</p>
            </div>
            <Badge variant="outline" className="text-xs">
              {summary.courseSummaries.length} Enrolled Courses
            </Badge>
          </div>

          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 dark:border-slate-800 dark:text-slate-400">
                  <th className="pb-3 font-semibold">Subject</th>
                  <th className="pb-3 font-semibold">Faculty Instructor</th>
                  <th className="pb-3 font-semibold text-center">Sessions</th>
                  <th className="pb-3 font-semibold text-center">Attendance Rate</th>
                  <th className="pb-3 font-semibold text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {summary.courseSummaries.map((c) => (
                  <tr key={c.courseOfferingId} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                    <td className="py-3">
                      <div className="font-semibold text-slate-900 dark:text-white">{c.courseCode}</div>
                      <div className="text-[11px] text-slate-500 truncate max-w-[200px]">{c.courseName}</div>
                    </td>
                    <td className="py-3 text-slate-600 dark:text-slate-400">
                      {c.facultyName}
                    </td>
                    <td className="py-3 text-center text-slate-600 dark:text-slate-400">
                      {c.presentCount} / {c.totalSessions}
                      <div className="text-[10px] text-slate-400">{c.absentCount} absent • {c.lateCount} late</div>
                    </td>
                    <td className="py-3 text-center">
                      <span
                        className={`font-bold text-sm ${
                          c.percentage >= 80
                            ? "text-emerald-600 dark:text-emerald-400"
                            : c.percentage >= 75
                            ? "text-amber-600 dark:text-amber-400"
                            : "text-rose-600 dark:text-rose-400"
                        }`}
                      >
                        {c.percentage}%
                      </span>
                      <div className="mt-1 h-1.5 w-16 mx-auto rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            c.percentage >= 80
                              ? "bg-emerald-500"
                              : c.percentage >= 75
                              ? "bg-amber-500"
                              : "bg-rose-500"
                          }`}
                          style={{ width: `${c.percentage}%` }}
                        />
                      </div>
                    </td>
                    <td className="py-3 text-right">
                      {getRiskBadge(c.riskLevel)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
