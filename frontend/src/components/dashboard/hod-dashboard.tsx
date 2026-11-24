"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/auth-context";
import { hodService, HodDashboardStats } from "@/services/hod.service";
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
  Building,
  Users,
  GraduationCap,
  CalendarCheck,
  Calendar,
  AlertTriangle,
  FileCheck2,
  BookOpen,
  ArrowRight,
  Clock,
  Layers,
  FileSpreadsheet,
  CheckCircle2,
  ShieldAlert,
  UserCheck,
  ExternalLink,
} from "lucide-react";

export function HodDashboard() {
  const { activePersona } = useAuth();
  const [data, setData] = useState<HodDashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  const deptName = activePersona.department || "Computer Science & Engineering";

  useEffect(() => {
    async function loadStats() {
      setLoading(true);
      try {
        const res = await hodService.getDashboardStats(deptName);
        if (res.success && res.data) {
          setData(res.data);
        }
      } catch (err) {
        console.error("HOD Dashboard load error:", err);
      } finally {
        setLoading(false);
      }
    }
    loadStats();
  }, [deptName]);

  if (loading || !data) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-28 rounded-2xl bg-white border border-slate-200 p-6" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <div
              key={i}
              className="h-28 rounded-xl bg-white border border-slate-200"
            />
          ))}
        </div>
      </div>
    );
  }

  const stats = data.statistics;

  return (
    <div className="space-y-6">
      {/* HOD Header Banner */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-7 shadow-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-l-4 border-l-yellow-400">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-semibold text-yellow-950 border border-yellow-300 mb-2">
            <span className="h-1.5 w-1.5 rounded-full bg-yellow-600" />
            Departmental Leadership Workspace • {data.department.code}
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
            {data.department.name}
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-slate-500">
            Head of Department: {data.department.head} • {stats.totalStudents}{" "}
            Students • {stats.totalFaculty} Faculty Members
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Link href="/hod/dashboard">
            <Button variant="primary" size="sm" className="gap-1.5">
              <ExternalLink className="h-3.5 w-3.5" />
              Open Dedicated HOD Portal
            </Button>
          </Link>
          <Link href="/hod/attendance">
            <Button variant="outline" size="sm" className="gap-1.5">
              <CalendarCheck className="h-3.5 w-3.5" />
              Attendance Trends
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Students"
          value={stats.totalStudents}
          description="B.Tech & M.Tech schemes"
          variant="indigo"
          icon={<GraduationCap className="h-4 w-4" />}
        />
        <StatCard
          label="Department Faculty"
          value={stats.totalFaculty}
          description="Ph.D. / M.Tech professors"
          variant="emerald"
          icon={<Users className="h-4 w-4" />}
        />
        <StatCard
          label="Total Subjects"
          value={stats.totalSubjects}
          description="Curriculum Offerings"
          variant="amber"
          icon={<BookOpen className="h-4 w-4" />}
        />
        <StatCard
          label="Total Classes"
          value={stats.totalClasses}
          description="Active cohorts"
          variant="sky"
          icon={<Layers className="h-4 w-4" />}
        />
        <StatCard
          label="Average Attendance"
          value={`${stats.averageStudentAttendance}%`}
          change={{ value: "+2.1% this week", trend: "up" }}
          description="Statutory threshold: 75%"
          variant="emerald"
          icon={<CheckCircle2 className="h-4 w-4" />}
        />
        <StatCard
          label="Faculty Attendance"
          value={`${stats.averageFacultyAttendance}%`}
          description="Biometric verified"
          variant="indigo"
          icon={<UserCheck className="h-4 w-4" />}
        />
        <StatCard
          label="Attendance Shortage"
          value={stats.studentsShortageCount}
          description="Students below 75%"
          variant="amber"
          icon={<ShieldAlert className="h-4 w-4 text-rose-600" />}
        />
        <StatCard
          label="Pending Approvals"
          value={stats.pendingApprovalRequests}
          description="Requests awaiting sign-off"
          variant="purple"
          icon={<FileCheck2 className="h-4 w-4 text-purple-600" />}
        />
      </div>

      {/* Quick Access to HOD Modules */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <Link
          href="/hod/students"
          className="p-4 rounded-xl border border-slate-200 bg-white hover:border-yellow-400 hover:bg-yellow-50/40 transition-all flex items-center justify-between group shadow-xs"
        >
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-yellow-100 text-yellow-900 flex items-center justify-center border border-yellow-300">
              <GraduationCap className="h-4 w-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-slate-900">
                Student Management
              </div>
              <div className="text-[10px] text-slate-500">
                Rosters, Academics & Details
              </div>
            </div>
          </div>
          <ArrowRight className="h-4 w-4 text-slate-400 group-hover:text-slate-900" />
        </Link>

        <Link
          href="/hod/faculty"
          className="p-4 rounded-xl border border-slate-200 bg-white hover:border-yellow-400 hover:bg-yellow-50/40 transition-all flex items-center justify-between group shadow-xs"
        >
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-yellow-100 text-yellow-900 flex items-center justify-center border border-yellow-300">
              <Users className="h-4 w-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-slate-900">
                Faculty Management
              </div>
              <div className="text-[10px] text-slate-500">
                Workload, Profile & Courses
              </div>
            </div>
          </div>
          <ArrowRight className="h-4 w-4 text-slate-400 group-hover:text-slate-900" />
        </Link>

        <Link
          href="/hod/attendance"
          className="p-4 rounded-xl border border-slate-200 bg-white hover:border-yellow-400 hover:bg-yellow-50/40 transition-all flex items-center justify-between group shadow-xs"
        >
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-yellow-100 text-yellow-900 flex items-center justify-center border border-yellow-300">
              <CalendarCheck className="h-4 w-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-slate-900">
                Attendance Hub
              </div>
              <div className="text-[10px] text-slate-500">
                Ledgers & Shortage Alerts
              </div>
            </div>
          </div>
          <ArrowRight className="h-4 w-4 text-slate-400 group-hover:text-slate-900" />
        </Link>

        <Link
          href="/hod/timetable"
          className="p-4 rounded-xl border border-slate-200 bg-white hover:border-yellow-400 hover:bg-yellow-50/40 transition-all flex items-center justify-between group shadow-xs"
        >
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-yellow-100 text-yellow-900 flex items-center justify-center border border-yellow-300">
              <Calendar className="h-4 w-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-slate-900">
                Timetable Grid
              </div>
              <div className="text-[10px] text-slate-500">
                Class & Lab Allocations
              </div>
            </div>
          </div>
          <ArrowRight className="h-4 w-4 text-slate-400 group-hover:text-slate-900" />
        </Link>
      </div>

      {/* Student Analytics & Faculty Workload */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle>Department Student Strength by Year</CardTitle>
              <CardDescription>
                B.Tech CSE enrolment distribution
              </CardDescription>
            </div>
            <Link href="/hod/students">
              <Button variant="ghost" size="sm" className="text-xs">
                View All <ArrowRight className="h-3 w-3 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="space-y-4">
            {data.studentAnalytics.yearWiseStrength.map((y) => (
              <div key={y.year} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-800">{y.year}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-slate-500 font-mono">
                      {y.strength} Students
                    </span>
                    <span className="font-bold text-slate-900 font-mono">
                      {y.percentage}% rate
                    </span>
                  </div>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-yellow-400"
                    style={{ width: `${y.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle>Attendance Radar & Alert Summary</CardTitle>
              <CardDescription>
                75% statutory compliance requirement
              </CardDescription>
            </div>
            <Link href="/hod/attendance">
              <Button variant="ghost" size="sm" className="text-xs">
                Manage Alerts <ArrowRight className="h-3 w-3 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-3.5 rounded-xl border border-rose-200 bg-rose-50/60 flex items-start gap-3">
              <ShieldAlert className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" />
              <div>
                <div className="text-xs font-bold text-rose-900">
                  {stats.studentsShortageCount} Students with Attendance
                  Shortage
                </div>
                <p className="text-[11px] text-rose-700 mt-0.5">
                  Action required: Issue parent advisories and review medical
                  exemptions before semester examination hall ticket lock.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-center">
              <div className="p-2.5 rounded-lg border border-slate-200 bg-slate-50">
                <div className="text-[10px] text-slate-500 font-semibold uppercase">
                  Monthly Avg Rate
                </div>
                <div className="text-lg font-bold font-mono text-slate-900 mt-0.5">
                  {data.attendanceTrends.monthlyAverage}%
                </div>
              </div>
              <div className="p-2.5 rounded-lg border border-slate-200 bg-slate-50">
                <div className="text-[10px] text-slate-500 font-semibold uppercase">
                  Statutory Cutoff
                </div>
                <div className="text-lg font-bold font-mono text-slate-900 mt-0.5">
                  {data.attendanceTrends.statutoryThreshold}%
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
