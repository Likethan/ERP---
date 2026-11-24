"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { vicePrincipalService } from "@/services/vice-principal.service";
import { VicePrincipalDashboardData } from "@/types/vice-principal";
import { StatCard } from "@/components/ui/stat-card";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Building2,
  Users,
  GraduationCap,
  CalendarCheck,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  BookOpen,
  ClipboardCheck,
  CheckCircle2,
  RefreshCw,
  Clock,
  Filter,
} from "lucide-react";
import { useToast } from "@/components/ui/toast";

export default function VicePrincipalDashboardPage() {
  const { showToast } = useToast();
  const [data, setData] = useState<VicePrincipalDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedDept, setSelectedDept] = useState<string>("ALL");
  const [academicYear, setAcademicYear] = useState<string>("2026-2027");
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await vicePrincipalService.getDashboard({
        department_id: selectedDept !== "ALL" ? selectedDept : undefined,
        academic_year: academicYear,
      });
      if (res.success && res.data) {
        setData(res.data);
      }
    } catch {
      showToast({
        title: "Load Error",
        message: "Failed to fetch dashboard metrics.",
        type: "error",
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedDept, academicYear]);

  const handleQuickApprove = async (approvalId: string, title: string) => {
    try {
      await vicePrincipalService.processApprovalAction(
        approvalId,
        "APPROVE",
        "Sanctioned by Vice Principal via Executive Dashboard.",
      );
      showToast({
        title: "Statutory Approval Executed",
        message: `Successfully approved "${title.substring(0, 40)}..."`,
        type: "success",
      });
      loadData();
    } catch {
      showToast({
        title: "Approval Error",
        message: "Unable to process approval.",
        type: "error",
      });
    }
  };

  if (loading && !data) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="h-8 w-8 animate-spin text-indigo-600" />
          <p className="text-sm font-semibold text-slate-600">
            Synthesizing institutional telemetry & department metrics...
          </p>
        </div>
      </div>
    );
  }

  const kpis = data?.kpis;

  return (
    <div className="space-y-6">
      {/* Header & Filter Controls */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Institutional Academic Supervision Dashboard
          </h1>
          <p className="text-sm text-slate-600">
            Multi-department academic velocity, statutory compliance, faculty
            allocations, and approval queues.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 shadow-xs">
            <Filter className="h-3.5 w-3.5 text-slate-400" />
            <select
              value={selectedDept}
              onChange={(e) => setSelectedDept(e.target.value)}
              className="text-xs font-semibold text-slate-700 bg-transparent focus:outline-hidden"
            >
              <option value="ALL">All Departments</option>
              <option value="dept-cse">Computer Science (CSE)</option>
              <option value="dept-ece">Electronics & Comm (ECE)</option>
              <option value="dept-mech">Mechanical Engg (MECH)</option>
              <option value="dept-civil">Civil Engineering (CIVIL)</option>
              <option value="dept-eee">Electrical & Electronics (EEE)</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 shadow-xs">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              AY:
            </span>
            <select
              value={academicYear}
              onChange={(e) => setAcademicYear(e.target.value)}
              className="text-xs font-semibold text-slate-700 bg-transparent focus:outline-hidden"
            >
              <option value="2026-2027">2026-2027 (Current)</option>
              <option value="2025-2026">2025-2026</option>
            </select>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setRefreshing(true);
              loadData();
            }}
            disabled={refreshing}
            className="gap-1.5"
          >
            <RefreshCw
              className={`h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`}
            />
            <span className="hidden sm:inline">Refresh</span>
          </Button>
        </div>
      </div>

      {/* Primary Institutional KPI Cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          title="Academic Departments"
          value={kpis?.total_departments ?? 5}
          icon={<Building2 className="h-5 w-5 text-indigo-600" />}
          description="Supervised Engineering Departments"
        />
        <StatCard
          title="Student Body Strength"
          value={(kpis?.total_students ?? 2620).toLocaleString()}
          icon={<GraduationCap className="h-5 w-5 text-blue-600" />}
          description="Enrolled across all cohorts"
        />
        <StatCard
          title="Faculty Workload"
          value={kpis?.total_faculty ?? 184}
          icon={<Users className="h-5 w-5 text-emerald-600" />}
          description="96.2% Present · 1:19 AICTE Ratio"
        />
        <StatCard
          title="Pending Approvals"
          value={kpis?.pending_approvals_count ?? 4}
          icon={<ShieldCheck className="h-5 w-5 text-amber-600" />}
          change={{
            value: "Action Required",
            trend: "neutral",
          }}
          description="Statutory & Academic Requests"
        />
      </div>

      {/* Secondary Metrics Row */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500">
              Institutional Student Attendance
            </span>
            <span className="text-xs font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded">
              Statutory 75% Rule
            </span>
          </div>
          <div className="text-2xl font-bold text-slate-900">
            {kpis?.overall_student_attendance ?? 88.4}%
          </div>
          <div className="mt-2 h-2 w-full rounded-full bg-slate-100 overflow-hidden">
            <div
              className="h-full rounded-full bg-indigo-600 transition-all duration-500"
              style={{ width: `${kpis?.overall_student_attendance ?? 88.4}%` }}
            />
          </div>
          <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500">
            <span>Threshold: 75.0%</span>
            <Link
              href="/vice-principal/students"
              className="font-semibold text-indigo-600 hover:underline flex items-center gap-0.5"
            >
              View &lt;75% Radar <ArrowRight className="h-2.5 w-2.5" />
            </Link>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500">
              Syllabus Completion Velocity
            </span>
            <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
              Mid-Term Target: 70%
            </span>
          </div>
          <div className="text-2xl font-bold text-slate-900">
            {kpis?.syllabus_completion_rate ?? 81.4}%
          </div>
          <div className="mt-2 h-2 w-full rounded-full bg-slate-100 overflow-hidden">
            <div
              className="h-full rounded-full bg-emerald-600 transition-all duration-500"
              style={{ width: `${kpis?.syllabus_completion_rate ?? 81.4}%` }}
            />
          </div>
          <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500">
            <span>Expected: 80.0%</span>
            <Link
              href="/vice-principal/academics"
              className="font-semibold text-emerald-600 hover:underline flex items-center gap-0.5"
            >
              Track Delays <ArrowRight className="h-2.5 w-2.5" />
            </Link>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500">
              Examination Readiness Index
            </span>
            <span className="text-xs font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded">
              CIA 2 in 5 Days
            </span>
          </div>
          <div className="text-2xl font-bold text-slate-900">
            {kpis?.examination_readiness ?? 92.0}%
          </div>
          <div className="mt-2 h-2 w-full rounded-full bg-slate-100 overflow-hidden">
            <div
              className="h-full rounded-full bg-blue-600 transition-all duration-500"
              style={{ width: `${kpis?.examination_readiness ?? 92.0}%` }}
            />
          </div>
          <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500">
            <span>40 of 42 QPs Moderated</span>
            <Link
              href="/vice-principal/examinations"
              className="font-semibold text-blue-600 hover:underline flex items-center gap-0.5"
            >
              Exam Oversight <ArrowRight className="h-2.5 w-2.5" />
            </Link>
          </div>
        </div>
      </div>

      {/* Main Grid: Department Matrix + Critical Alerts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Department Academic Health Matrix (2 cols) */}
        <Card className="lg:col-span-2 shadow-xs border-slate-200">
          <CardHeader className="flex flex-row items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <CardTitle className="text-base font-bold text-slate-900">
                Department Academic Health Matrix
              </CardTitle>
              <CardDescription className="text-xs text-slate-500">
                Comparative metrics across supervised academic departments
              </CardDescription>
            </div>
            <Link href="/vice-principal/departments">
              <Button variant="ghost" size="sm" className="gap-1 text-xs">
                <span>View Full Details</span>
                <ArrowRight className="h-3 w-3" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-[10px] font-bold uppercase tracking-wider text-slate-500 border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-3">Department</th>
                    <th className="px-3 py-3">HOD</th>
                    <th className="px-3 py-3">Students</th>
                    <th className="px-3 py-3">Attendance</th>
                    <th className="px-3 py-3">Syllabus</th>
                    <th className="px-3 py-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data?.department_metrics.map((dept) => (
                    <tr
                      key={dept.id}
                      className="hover:bg-slate-50/80 transition-colors"
                    >
                      <td className="px-4 py-3 font-semibold text-slate-900">
                        <div className="flex items-center gap-2">
                          <span className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[10px] text-slate-700">
                            {dept.code}
                          </span>
                          <span className="truncate max-w-[180px]">
                            {dept.name}
                          </span>
                        </div>
                      </td>
                      <td className="px-3 py-3 text-slate-600">{dept.hod}</td>
                      <td className="px-3 py-3 font-medium text-slate-900">
                        {dept.students}{" "}
                        <span className="text-[10px] text-slate-400">
                          ({dept.faculty_ratio})
                        </span>
                      </td>
                      <td className="px-3 py-3">
                        <span
                          className={`font-bold ${
                            dept.attendance_rate < 85
                              ? "text-amber-600"
                              : "text-slate-900"
                          }`}
                        >
                          {dept.attendance_rate}%
                        </span>
                      </td>
                      <td className="px-3 py-3">
                        <div className="flex items-center gap-2">
                          <div className="h-1.5 w-14 rounded-full bg-slate-100 overflow-hidden">
                            <div
                              className="h-full bg-emerald-600 rounded-full"
                              style={{ width: `${dept.syllabus_progress}%` }}
                            />
                          </div>
                          <span className="font-semibold text-slate-700">
                            {dept.syllabus_progress}%
                          </span>
                        </div>
                      </td>
                      <td className="px-3 py-3">
                        <Badge
                          variant={
                            dept.status === "EXEMPLARY"
                              ? "success"
                              : dept.status === "ON_TRACK"
                                ? "default"
                                : "warning"
                          }
                          className="text-[10px]"
                        >
                          {dept.status.replace("_", " ")}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Critical Academic Alerts (1 col) */}
        <Card className="shadow-xs border-slate-200">
          <CardHeader className="border-b border-slate-100 pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-rose-500" />
                Critical Alerts
              </CardTitle>
              <Badge variant="destructive" className="text-[10px]">
                {data?.critical_alerts.length ?? 0} Requiring Action
              </Badge>
            </div>
            <CardDescription className="text-xs text-slate-500">
              Department anomalies exceeding statutory tolerance
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 space-y-3">
            {data?.critical_alerts.map((alert) => (
              <div
                key={alert.id}
                className="rounded-lg border border-slate-200 p-3 bg-slate-50 hover:bg-white transition-colors"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                    {alert.department}
                  </span>
                  <span
                    className={`rounded px-1.5 py-0.2 text-[9px] font-bold ${
                      alert.severity === "CRITICAL"
                        ? "bg-rose-100 text-rose-800"
                        : alert.severity === "HIGH"
                          ? "bg-amber-100 text-amber-800"
                          : "bg-blue-100 text-blue-800"
                    }`}
                  >
                    {alert.severity}
                  </span>
                </div>
                <div className="text-xs font-bold text-slate-900">
                  {alert.title}
                </div>
                <p className="mt-1 text-[11px] text-slate-600 leading-relaxed">
                  {alert.detail}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Statutory Approvals Quick Action Section */}
      <Card className="shadow-xs border-slate-200">
        <CardHeader className="flex flex-row items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-indigo-600" />
              Statutory Approvals Requiring Vice Principal Sanction
            </CardTitle>
            <CardDescription className="text-xs text-slate-500">
              Department academic requests, faculty leaves, and timetable swaps
            </CardDescription>
          </div>
          <Link href="/vice-principal/approvals">
            <Button variant="outline" size="sm" className="gap-1 text-xs">
              <span>Approval Management Center</span>
              <ArrowRight className="h-3 w-3" />
            </Button>
          </Link>
        </CardHeader>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-slate-200 p-4 bg-white space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded">
                  Department Academic Request
                </span>
                <span className="text-xs font-semibold text-rose-600">
                  HIGH URGENCY
                </span>
              </div>
              <div>
                <div className="text-sm font-bold text-slate-900">
                  Special Elective: Advanced Deep Learning & Generative AI
                </div>
                <div className="text-xs text-slate-500 mt-0.5">
                  Computer Science & Engineering · Submitted by Dr. K. S. Anand
                  (HOD)
                </div>
              </div>
              <p className="text-xs text-slate-600">
                Industry demand alignment with NAAC criteria 1.2 curricular
                enrichment. 84 students opted for early enrollment.
              </p>
              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <Link href="/vice-principal/approvals">
                  <Button variant="ghost" size="sm" className="text-xs">
                    Inspect Full Dossier
                  </Button>
                </Link>
                <Button
                  size="sm"
                  onClick={() =>
                    handleQuickApprove(
                      "appr-vp-001",
                      "Special Elective: Advanced Deep Learning & Generative AI",
                    )
                  }
                  className="bg-indigo-600 hover:bg-indigo-700 text-xs gap-1"
                >
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Approve & Sanction
                </Button>
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 p-4 bg-white space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-blue-700 bg-blue-50 px-2 py-0.5 rounded">
                  Faculty Leave (Escalated)
                </span>
                <span className="text-xs font-semibold text-amber-600">
                  MEDIUM URGENCY
                </span>
              </div>
              <div>
                <div className="text-sm font-bold text-slate-900">
                  Duty Leave: IEEE Colloquium on Robotics Presentation
                </div>
                <div className="text-xs text-slate-500 mt-0.5">
                  Electronics & Communication · Dr. Priya Nair (Assoc. Prof)
                </div>
              </div>
              <p className="text-xs text-slate-600">
                5 Days duty leave sanctioned by HOD ECE. Syllabus compensation
                and alternate faculty assignment (Prof. S. Ranganathan)
                verified.
              </p>
              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <Link href="/vice-principal/approvals">
                  <Button variant="ghost" size="sm" className="text-xs">
                    Inspect Full Dossier
                  </Button>
                </Link>
                <Button
                  size="sm"
                  onClick={() =>
                    handleQuickApprove(
                      "appr-vp-003",
                      "Duty Leave: IEEE Colloquium on Robotics",
                    )
                  }
                  className="bg-indigo-600 hover:bg-indigo-700 text-xs gap-1"
                >
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Approve & Sanction
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
