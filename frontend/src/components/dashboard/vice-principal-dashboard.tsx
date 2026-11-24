"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { vicePrincipalService } from "@/services/vice-principal.service";
import {
  VicePrincipalDashboardData,
  StatutoryApprovalItem,
} from "@/types/vice-principal";
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
  GraduationCap,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Building,
  Sparkles,
  BookOpen,
  Award,
  Clock,
  ShieldCheck,
  FileCheck,
  Users,
  LayoutDashboard,
  ExternalLink,
  RefreshCw,
} from "lucide-react";
import { useToast } from "@/components/ui/toast";

export function VicePrincipalDashboard() {
  const { showToast } = useToast();
  const [data, setData] = useState<VicePrincipalDashboardData | null>(null);
  const [approvals, setApprovals] = useState<StatutoryApprovalItem[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [dashRes, appRes] = await Promise.all([
        vicePrincipalService.getDashboard(),
        vicePrincipalService.getApprovals({ status: "PENDING" }),
      ]);
      if (dashRes.success && dashRes.data) {
        setData(dashRes.data);
      }
      if (appRes.success && appRes.data) {
        setApprovals(appRes.data);
      }
    } catch {
      // Fallback
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleQuickApprove = async (id: string, title: string) => {
    try {
      await vicePrincipalService.processApprovalAction(
        id,
        "APPROVE",
        "Sanctioned by Vice Principal via Dashboard.",
      );
      showToast({
        title: "Statutory Sanction Recorded",
        message: `Approved #${id}`,
        type: "success",
      });
      loadData();
    } catch {
      showToast({
        title: "Action Failed",
        message: "Unable to process approval.",
        type: "error",
      });
    }
  };

  const kpis = data?.kpis;
  const deptHealth = data?.department_metrics || [];

  return (
    <div className="space-y-6">
      {/* Executive Dedicated Portal Callout Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-linear-to-r from-indigo-900 via-indigo-800 to-slate-900 p-6 text-white shadow-md">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-1.5 rounded-full bg-indigo-500/30 px-3 py-1 text-xs font-semibold text-indigo-200 border border-indigo-400/30">
              <Sparkles className="h-3 w-3 text-indigo-300" />
              <span>CampusOS Executive Workspace</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
              Dedicated Vice Principal Portal Active
            </h2>
            <p className="text-xs sm:text-sm text-indigo-200/90 max-w-2xl leading-relaxed">
              Access the dedicated executive environment for multi-department
              supervision, timetable change verifications, low-attendance radar
              (&lt;75%), and statutory approval workflows.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <Link href="/vice-principal/dashboard">
              <Button
                size="sm"
                className="bg-white text-indigo-950 hover:bg-indigo-50 font-bold text-xs gap-1.5 shadow-sm"
              >
                <LayoutDashboard className="h-4 w-4" />
                <span>Launch Executive Workspace</span>
              </Button>
            </Link>
            <Link href="/vice-principal/approvals">
              <Button
                variant="outline"
                size="sm"
                className="border-indigo-400/40 text-white hover:bg-white/10 text-xs gap-1.5"
              >
                <ShieldCheck className="h-4 w-4 text-indigo-300" />
                <span>Approval Center ({approvals.length})</span>
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Header & Institutional Overview */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
            Academic Operations & Institutional Oversight
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-slate-500">
            Real-time curriculum delivery, teaching quality audits, faculty
            workloads, and statutory approvals for V.S.B. Engineering College.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link href="/vice-principal/academics">
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              <BookOpen className="h-3.5 w-3.5 text-indigo-600" />
              <span>Academic Milestones</span>
            </Button>
          </Link>
          <Link href="/vice-principal/approvals">
            <Button
              size="sm"
              className="bg-indigo-600 hover:bg-indigo-700 text-white gap-1.5 text-xs"
            >
              <ShieldCheck className="h-3.5 w-3.5" />
              <span>Statutory Approvals</span>
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
        <StatCard
          label="Institution Attendance Rate"
          value={`${kpis?.overall_student_attendance ?? 88.4}%`}
          change={{ value: "+2.1% MoM", trend: "up" }}
          description="Average across 5 departments and 2,620 active students"
          variant="indigo"
          icon={<CheckCircle2 className="h-4 w-4" />}
        />
        <StatCard
          label="Faculty Workload Compliance"
          value={`${kpis?.faculty_attendance ?? 96.2}%`}
          change={{ value: "Optimal", trend: "neutral" }}
          description="184 Faculty · AICTE 1:19 contact hours balanced"
          variant="emerald"
          icon={<Users className="h-4 w-4" />}
        />
        <StatCard
          label="Syllabus Completion Velocity"
          value={`${kpis?.syllabus_completion_rate ?? 81.4}%`}
          change={{ value: "Mid-Term Target: 70%", trend: "up" }}
          description="Even semester teaching ahead of exam cutoff"
          variant="sky"
          icon={<BookOpen className="h-4 w-4" />}
        />
        <StatCard
          label="Pending Statutory Approvals"
          value={`${approvals.length} Requests`}
          change={{ value: "Action Required", trend: "neutral" }}
          description="Faculty leaves, timetable swaps & academic requests"
          variant="amber"
          icon={<FileCheck className="h-4 w-4" />}
        />
      </div>

      {/* Main Split Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Department Academic Performance Matrix (2 Columns) */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="shadow-xs border-slate-200">
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <div>
                <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Building className="h-4 w-4 text-indigo-600" />
                  Department Academic Operations Matrix
                </CardTitle>
                <CardDescription className="text-xs text-slate-500">
                  Head of Department academic progress, attendance adherence,
                  and quality audits.
                </CardDescription>
              </div>
              <Link href="/vice-principal/departments">
                <Button variant="ghost" size="sm" className="gap-1 text-xs">
                  <span>View All Departments</span>
                  <ArrowRight className="h-3 w-3" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-slate-200 bg-slate-50 text-slate-700 uppercase tracking-wider font-semibold text-[10px]">
                    <tr>
                      <th className="px-4 py-3">Department & HOD</th>
                      <th className="px-3 py-3 text-center">Students</th>
                      <th className="px-3 py-3 text-center">Attendance</th>
                      <th className="px-3 py-3 text-center">Syllabus</th>
                      <th className="px-3 py-3 text-center">NAAC Score</th>
                      <th className="px-4 py-3 text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-medium">
                    {deptHealth.map((dept) => (
                      <tr
                        key={dept.name}
                        className="hover:bg-slate-50 transition-colors"
                      >
                        <td className="px-4 py-3">
                          <div className="font-semibold text-slate-900">
                            {dept.name}
                          </div>
                          <div className="text-[11px] text-slate-400">
                            {dept.hod} • Ratio {dept.faculty_ratio}
                          </div>
                        </td>
                        <td className="px-3 py-3 text-center text-slate-700 font-semibold">
                          {dept.students}
                        </td>
                        <td className="px-3 py-3 text-center">
                          <span
                            className={`font-semibold ${
                              dept.attendance_rate < 85
                                ? "text-amber-700"
                                : "text-emerald-700"
                            }`}
                          >
                            {dept.attendance_rate}%
                          </span>
                        </td>
                        <td className="px-3 py-3 text-center">
                          <span className="font-semibold text-sky-700">
                            {dept.syllabus_progress}%
                          </span>
                        </td>
                        <td className="px-3 py-3 text-center font-bold text-slate-800">
                          {dept.accreditation_score}
                        </td>
                        <td className="px-4 py-3 text-right">
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
                            {dept.status === "EXEMPLARY"
                              ? "Exemplary"
                              : dept.status === "ON_TRACK"
                                ? "On Track"
                                : "Review Needed"}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Pending Statutory & Executive Approvals Panel (1 Column) */}
        <div className="space-y-6">
          <Card className="shadow-xs border-slate-200">
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <div>
                <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <FileCheck className="h-4 w-4 text-indigo-600" />
                  Statutory Approvals
                </CardTitle>
                <CardDescription className="text-xs text-slate-500">
                  Submissions requiring Vice Principal sign-off.
                </CardDescription>
              </div>
              <Badge variant="warning" className="text-xs">
                {approvals.length} Pending
              </Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              {approvals.slice(0, 3).map((item) => (
                <div
                  key={item.id}
                  className="rounded-lg border border-slate-200 bg-white p-3 hover:border-indigo-300 hover:bg-slate-50/50 shadow-xs transition-all space-y-2"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="font-semibold text-xs text-slate-900 leading-tight">
                      {item.title}
                    </div>
                    <Badge
                      variant={
                        item.urgency === "CRITICAL"
                          ? "destructive"
                          : item.urgency === "HIGH"
                            ? "warning"
                            : "default"
                      }
                      className="text-[9px] shrink-0"
                    >
                      {item.urgency}
                    </Badge>
                  </div>
                  <div className="text-[11px] text-slate-500">
                    {item.department_name} · By <b>{item.submitted_by}</b>
                  </div>
                  <div className="flex items-center justify-between pt-1 border-t border-slate-100">
                    <span className="text-[10px] text-slate-400">
                      {new Date(item.submission_date).toLocaleDateString()}
                    </span>
                    <Button
                      size="sm"
                      onClick={() => handleQuickApprove(item.id, item.title)}
                      className="h-6 px-2 text-[10px] bg-emerald-600 hover:bg-emerald-700 text-white gap-1"
                    >
                      <CheckCircle2 className="h-3 w-3" />
                      Approve
                    </Button>
                  </div>
                </div>
              ))}

              <Link
                href="/vice-principal/approvals"
                className="block w-full pt-1"
              >
                <Button variant="outline" size="sm" className="w-full text-xs">
                  Open Approval Management Center
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* Quick Institutional Workspace Links */}
          <Card className="bg-white border-slate-200 shadow-xs">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Vice Principal Supervision Tools
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-1">
              <Link
                href="/vice-principal/students"
                className="flex items-center justify-between rounded-lg p-2 text-xs font-medium text-slate-700 hover:bg-indigo-50 hover:text-indigo-900 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <GraduationCap className="h-4 w-4 text-indigo-600" />
                  <span>Sub-75% Low-Attendance Radar</span>
                </div>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400" />
              </Link>

              <Link
                href="/vice-principal/faculty"
                className="flex items-center justify-between rounded-lg p-2 text-xs font-medium text-slate-700 hover:bg-indigo-50 hover:text-indigo-900 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-emerald-600" />
                  <span>Faculty Workload & Escalated Leaves</span>
                </div>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400" />
              </Link>

              <Link
                href="/vice-principal/examinations"
                className="flex items-center justify-between rounded-lg p-2 text-xs font-medium text-slate-700 hover:bg-indigo-50 hover:text-indigo-900 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-blue-600" />
                  <span>CIA Mark Lockouts & University Results</span>
                </div>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400" />
              </Link>

              <Link
                href="/vice-principal/reports"
                className="flex items-center justify-between rounded-lg p-2 text-xs font-medium text-slate-700 hover:bg-indigo-50 hover:text-indigo-900 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-amber-600" />
                  <span>Regulatory Compliance Reports</span>
                </div>
                <ArrowRight className="h-3.5 w-3.5 text-slate-400" />
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
