"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { attendanceService } from "@/services/attendance.service";
import { AttendanceSummary, LowAttendanceAlertItem } from "@/types/attendance";
import {
  CalendarCheck,
  AlertTriangle,
  FileCheck2,
  Clock,
  Layers,
  GraduationCap,
  BookOpen,
  Sliders,
  FileText,
  TrendingDown,
  ArrowRight,
  ShieldAlert,
  Building,
  CheckCircle2,
} from "lucide-react";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export default function AttendanceHubPage() {
  const { hasPermission } = useAuth();
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<AttendanceSummary | null>(null);
  const [alerts, setAlerts] = useState<LowAttendanceAlertItem[]>([]);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [sumRes, alertsRes] = await Promise.all([
          attendanceService.getDashboardSummary(),
          attendanceService.getLowAttendanceAlerts(),
        ]);
        if (sumRes.success) setSummary(sumRes.data);
        if (alertsRes.success) setAlerts(alertsRes.data);
      } catch (err) {
        console.error("Failed to load attendance dashboard data", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
              CampusOS Engine
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              Attendance Operations
            </span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Attendance Operations Hub
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Real-time registers, course attendance analytics, leave approvals,
            and policy compliance monitoring.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {hasPermission("attendance:record") && (
            <Link href="/app/attendance/sessions">
              <Button variant="primary" className="gap-2">
                <CalendarCheck className="h-4 w-4" />
                Take Attendance
              </Button>
            </Link>
          )}
          <Link href="/app/attendance/leaves">
            <Button variant="outline" className="gap-2">
              <FileCheck2 className="h-4 w-4" />
              Apply Leave
            </Button>
          </Link>
          <Link href="/app/attendance/reports">
            <Button variant="outline" className="gap-2">
              <FileText className="h-4 w-4" />
              Generate Reports
            </Button>
          </Link>
        </div>
      </div>

      {/* Critical Operational Banner if Students At Risk */}
      {alerts.length > 0 && (
        <div className="rounded-xl border border-rose-200 bg-rose-50/70 p-4 dark:border-rose-900/60 dark:bg-rose-950/30">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-rose-100 text-rose-700 dark:bg-rose-900/50 dark:text-rose-300">
              <ShieldAlert className="h-5 w-5" />
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-rose-900 dark:text-rose-200">
                Attendance Deficit Alert —{" "}
                {summary?.studentsBelowThresholdCount ?? alerts.length} Students
                Below Minimum 75% Requirement
              </h3>
              <p className="mt-0.5 text-xs text-rose-700 dark:text-rose-400">
                Action required: Send automated academic advisories or schedule
                counselor interventions before end-term hall tickets are
                blocked.
              </p>
            </div>
            <Link href="/app/attendance/students?riskLevel=CRITICAL">
              <Button
                size="sm"
                variant="outline"
                className="border-rose-300 text-rose-700 hover:bg-rose-100 dark:border-rose-800 dark:text-rose-300"
              >
                View At-Risk Roster
              </Button>
            </Link>
          </div>
        </div>
      )}

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Overall Attendance"
          value={
            loading ? "..." : `${summary?.overallAttendancePercentage ?? 88.6}%`
          }
          description="Cumulative across active terms"
          icon={<CalendarCheck className="h-5 w-5 text-indigo-600" />}
        />
        <StatCard
          title="Today's Sessions"
          value={
            loading
              ? "..."
              : `${summary?.todaySessionsCompleted ?? 4} / ${summary?.todaySessionsCount ?? 6}`
          }
          description={`${summary?.todaySessionsPending ?? 2} sessions pending marking`}
          icon={<Clock className="h-5 w-5 text-emerald-600" />}
        />
        <StatCard
          title="Students Below 75%"
          value={
            loading ? "..." : String(summary?.studentsBelowThresholdCount ?? 14)
          }
          description={`${summary?.studentsAtRiskCount ?? 32} in warning bracket (<80%)`}
          icon={<AlertTriangle className="h-5 w-5 text-rose-600" />}
        />
        <StatCard
          title="Pending Approvals"
          value={
            loading
              ? "..."
              : String(
                  (summary?.pendingLeaveRequestsCount ?? 0) +
                    (summary?.pendingCorrectionsCount ?? 0),
                )
          }
          description={`${summary?.pendingLeaveRequestsCount ?? 0} leaves, ${summary?.pendingCorrectionsCount ?? 0} corrections`}
          icon={<FileCheck2 className="h-5 w-5 text-amber-600" />}
        />
      </div>

      {/* Operations Quick Nav Hub */}
      <div>
        <h2 className="text-base font-semibold text-slate-900 dark:text-white mb-3">
          Attendance Modules & Registers
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link
            href="/app/attendance/sessions"
            className="group block rounded-xl border border-slate-200 bg-white p-4.5 hover:border-indigo-500 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="flex items-center justify-between">
              <div className="p-2.5 rounded-lg bg-indigo-50 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-400">
                <CalendarCheck className="h-5 w-5" />
              </div>
              <ArrowRight className="h-4 w-4 text-slate-400 group-hover:translate-x-1 group-hover:text-indigo-600 transition" />
            </div>
            <h3 className="mt-3 text-sm font-semibold text-slate-900 group-hover:text-indigo-600 dark:text-white dark:group-hover:text-indigo-400">
              Session Registers
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Daily timetable periods, lecture attendance marking, and session
              status rosters.
            </p>
          </Link>

          <Link
            href="/app/attendance/records"
            className="group block rounded-xl border border-slate-200 bg-white p-4.5 hover:border-indigo-500 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="flex items-center justify-between">
              <div className="p-2.5 rounded-lg bg-blue-50 text-blue-600 dark:bg-blue-950/60 dark:text-blue-400">
                <Layers className="h-5 w-5" />
              </div>
              <ArrowRight className="h-4 w-4 text-slate-400 group-hover:translate-x-1 group-hover:text-blue-600 transition" />
            </div>
            <h3 className="mt-3 text-sm font-semibold text-slate-900 group-hover:text-blue-600 dark:text-white dark:group-hover:text-blue-400">
              Attendance Records
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Comprehensive student attendance ledger across all sections,
              subjects, and dates.
            </p>
          </Link>

          <Link
            href="/app/attendance/students"
            className="group block rounded-xl border border-slate-200 bg-white p-4.5 hover:border-indigo-500 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="flex items-center justify-between">
              <div className="p-2.5 rounded-lg bg-emerald-50 text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-400">
                <GraduationCap className="h-5 w-5" />
              </div>
              <ArrowRight className="h-4 w-4 text-slate-400 group-hover:translate-x-1 group-hover:text-emerald-600 transition" />
            </div>
            <h3 className="mt-3 text-sm font-semibold text-slate-900 group-hover:text-emerald-600 dark:text-white dark:group-hover:text-emerald-400">
              Student Attendance 360°
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Individual percentage tracking, course breakdowns, and weekly
              attendance curves.
            </p>
          </Link>

          <Link
            href="/app/attendance/courses"
            className="group block rounded-xl border border-slate-200 bg-white p-4.5 hover:border-indigo-500 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="flex items-center justify-between">
              <div className="p-2.5 rounded-lg bg-purple-50 text-purple-600 dark:bg-purple-950/60 dark:text-purple-400">
                <BookOpen className="h-5 w-5" />
              </div>
              <ArrowRight className="h-4 w-4 text-slate-400 group-hover:translate-x-1 group-hover:text-purple-600 transition" />
            </div>
            <h3 className="mt-3 text-sm font-semibold text-slate-900 group-hover:text-purple-600 dark:text-white dark:group-hover:text-purple-400">
              Course Offering Registers
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Class-level statistics, faculty delivery logs, and low-attendance
              course alerts.
            </p>
          </Link>

          <Link
            href="/app/attendance/leaves"
            className="group block rounded-xl border border-slate-200 bg-white p-4.5 hover:border-indigo-500 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="flex items-center justify-between">
              <div className="p-2.5 rounded-lg bg-amber-50 text-amber-600 dark:bg-amber-950/60 dark:text-amber-400">
                <FileCheck2 className="h-5 w-5" />
              </div>
              <ArrowRight className="h-4 w-4 text-slate-400 group-hover:translate-x-1 group-hover:text-amber-600 transition" />
            </div>
            <h3 className="mt-3 text-sm font-semibold text-slate-900 group-hover:text-amber-600 dark:text-white dark:group-hover:text-amber-400">
              Leave Workflows
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Medical, on-duty, and sports leave applications with verification
              and approval timeline.
            </p>
          </Link>

          <Link
            href="/app/attendance/corrections"
            className="group block rounded-xl border border-slate-200 bg-white p-4.5 hover:border-indigo-500 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="flex items-center justify-between">
              <div className="p-2.5 rounded-lg bg-teal-50 text-teal-600 dark:bg-teal-950/60 dark:text-teal-400">
                <Clock className="h-5 w-5" />
              </div>
              <ArrowRight className="h-4 w-4 text-slate-400 group-hover:translate-x-1 group-hover:text-teal-600 transition" />
            </div>
            <h3 className="mt-3 text-sm font-semibold text-slate-900 group-hover:text-teal-600 dark:text-white dark:group-hover:text-teal-400">
              Attendance Corrections
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Audit-supervised attendance revisions with HOD sign-off and
              chronological logs.
            </p>
          </Link>

          <Link
            href="/app/attendance/policies"
            className="group block rounded-xl border border-slate-200 bg-white p-4.5 hover:border-indigo-500 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="flex items-center justify-between">
              <div className="p-2.5 rounded-lg bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                <Sliders className="h-5 w-5" />
              </div>
              <ArrowRight className="h-4 w-4 text-slate-400 group-hover:translate-x-1 group-hover:text-indigo-600 transition" />
            </div>
            <h3 className="mt-3 text-sm font-semibold text-slate-900 group-hover:text-indigo-600 dark:text-white dark:group-hover:text-indigo-400">
              Regulations & Policies
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Configurable 75% minimums, late-punch weights, and medical excuse
              thresholds.
            </p>
          </Link>

          <Link
            href="/app/attendance/reports"
            className="group block rounded-xl border border-slate-200 bg-white p-4.5 hover:border-indigo-500 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="flex items-center justify-between">
              <div className="p-2.5 rounded-lg bg-rose-50 text-rose-600 dark:bg-rose-950/60 dark:text-rose-400">
                <FileText className="h-5 w-5" />
              </div>
              <ArrowRight className="h-4 w-4 text-slate-400 group-hover:translate-x-1 group-hover:text-rose-600 transition" />
            </div>
            <h3 className="mt-3 text-sm font-semibold text-slate-900 group-hover:text-rose-600 dark:text-white dark:group-hover:text-rose-400">
              Reports & Audit Exports
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Student cohort rosters, department analytics, and exam eligibility
              export files.
            </p>
          </Link>
        </div>
      </div>

      {/* Two Column Layout: Analytics & At-Risk Roster */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Breakdown Analytics */}
        <div className="space-y-6 lg:col-span-1">
          {/* Department Breakdown */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <Building className="h-4 w-4 text-slate-500" />
                <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                  Department Breakdown
                </h3>
              </div>
              <Badge variant="outline" className="text-xs">
                Active Term
              </Badge>
            </div>
            <div className="mt-4 space-y-3.5">
              {summary?.departmentBreakdown.map((dept) => (
                <div key={dept.department} className="space-y-1.5">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-slate-700 dark:text-slate-300 truncate max-w-[180px]">
                      {dept.department}
                    </span>
                    <span className="text-slate-900 dark:text-white font-semibold">
                      {dept.percentage}%
                    </span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        dept.percentage >= 85
                          ? "bg-emerald-500"
                          : dept.percentage >= 75
                            ? "bg-amber-500"
                            : "bg-rose-500"
                      }`}
                      style={{ width: `${dept.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Semester Breakdown */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <Layers className="h-4 w-4 text-slate-500" />
                <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                  Semester Comparison
                </h3>
              </div>
              <Badge variant="outline" className="text-xs">
                Cumulative
              </Badge>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3">
              {summary?.semesterBreakdown.map((sem) => (
                <div
                  key={sem.semester}
                  className="rounded-lg border border-slate-100 bg-slate-50/50 p-3 dark:border-slate-800 dark:bg-slate-800/40"
                >
                  <span className="text-xs text-slate-500 dark:text-slate-400">
                    Semester {sem.semester}
                  </span>
                  <div className="mt-1 flex items-baseline gap-1.5">
                    <span className="text-lg font-bold text-slate-900 dark:text-white">
                      {sem.percentage}%
                    </span>
                    <span className="text-[10px] text-slate-400">avg</span>
                  </div>
                  <span className="text-[11px] text-slate-500 dark:text-slate-400">
                    {sem.studentCount} students
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Live Low Attendance & Risk Alerts */}
        <div className="lg:col-span-2 rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 border-b border-slate-100 dark:border-slate-800 gap-2">
            <div>
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-rose-500" />
                <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                  Low Attendance & Recovery Projections
                </h3>
              </div>
              <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                Calculates consecutive classes required to satisfy the
                institutional 75% threshold.
              </p>
            </div>
            <Link href="/app/attendance/students">
              <Button size="sm" variant="outline" className="text-xs">
                View All Students
              </Button>
            </Link>
          </div>

          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 dark:border-slate-800 dark:text-slate-400">
                  <th className="pb-3 font-semibold">Student</th>
                  <th className="pb-3 font-semibold">Course</th>
                  <th className="pb-3 font-semibold">Current %</th>
                  <th className="pb-3 font-semibold">Attended</th>
                  <th className="pb-3 font-semibold">Recovery Required</th>
                  <th className="pb-3 font-semibold">Status</th>
                  <th className="pb-3 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {alerts.map((alert) => (
                  <tr
                    key={`${alert.studentId}-${alert.courseCode}`}
                    className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40"
                  >
                    <td className="py-3">
                      <div className="font-medium text-slate-900 dark:text-white">
                        {alert.studentName}
                      </div>
                      <div className="text-[11px] text-slate-500">
                        {alert.rollNumber} • Sec {alert.section}
                      </div>
                    </td>
                    <td className="py-3">
                      <span className="font-semibold text-slate-700 dark:text-slate-300">
                        {alert.courseCode}
                      </span>
                      <div className="text-[11px] text-slate-500 truncate max-w-[140px]">
                        {alert.courseName}
                      </div>
                    </td>
                    <td className="py-3">
                      <span
                        className={`font-bold ${alert.attendancePercentage < 65 ? "text-rose-600" : "text-amber-600"}`}
                      >
                        {alert.attendancePercentage}%
                      </span>
                    </td>
                    <td className="py-3 text-slate-600 dark:text-slate-400">
                      {alert.sessionsAttended} / {alert.totalSessions}
                    </td>
                    <td className="py-3">
                      <span className="inline-flex items-center gap-1 font-semibold text-rose-700 dark:text-rose-400">
                        <TrendingDown className="h-3 w-3" />+
                        {alert.sessionsNeededToRecover} sessions
                      </span>
                    </td>
                    <td className="py-3">
                      <Badge
                        variant={
                          alert.riskLevel === "CRITICAL"
                            ? "destructive"
                            : "warning"
                        }
                        className="text-[10px]"
                      >
                        {alert.riskLevel}
                      </Badge>
                    </td>
                    <td className="py-3 text-right">
                      <Link
                        href={`/app/attendance/students/${alert.studentId}`}
                      >
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 px-2 text-xs text-indigo-600 hover:text-indigo-700"
                        >
                          Profile
                        </Button>
                      </Link>
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
