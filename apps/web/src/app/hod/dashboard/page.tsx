"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
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
  TrendingUp,
  TrendingDown,
  Layers,
  FileSpreadsheet,
  CheckCircle2,
  ShieldAlert,
  UserCheck,
} from "lucide-react";

export default function HodDashboardPage() {
  const { activePersona } = useAuth();
  const [data, setData] = useState<HodDashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const deptName = activePersona.department || "Computer Science & Engineering";

  useEffect(() => {
    async function loadStats() {
      setLoading(true);
      setError(null);
      try {
        const res = await hodService.getDashboardStats(deptName);
        if (res.success && res.data) {
          setData(res.data);
        } else {
          setError("Failed to load department statistics.");
        }
      } catch (err) {
        console.error("HOD Dashboard load error:", err);
        setError("Unable to connect to departmental services.");
      } finally {
        setLoading(false);
      }
    }
    loadStats();
  }, [deptName]);

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-28 rounded-2xl bg-white border border-slate-200 p-6" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-28 rounded-xl bg-white border border-slate-200" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-64 rounded-xl bg-white border border-slate-200" />
          <div className="h-64 rounded-xl bg-white border border-slate-200" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8 text-center rounded-2xl border border-red-200 bg-red-50 text-red-900">
        <AlertTriangle className="h-8 w-8 mx-auto text-red-500 mb-2" />
        <h2 className="text-lg font-bold">Department Data Unavailable</h2>
        <p className="text-sm mt-1 text-red-700">{error || "Could not retrieve records."}</p>
        <Button
          variant="outline"
          size="sm"
          className="mt-4"
          onClick={() => window.location.reload()}
        >
          Retry
        </Button>
      </div>
    );
  }

  const stats = data.statistics;

  return (
    <div className="space-y-6">
      {/* Header Banner */}
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
            Head of Department: {data.department.head} • {stats.totalStudents} Students • {stats.totalFaculty} Faculty Members
          </p>
        </div>

        {/* Quick Action Navigation */}
        <div className="flex flex-wrap items-center gap-2">
          <Link href="/hod/students">
            <Button variant="outline" size="sm" className="gap-1.5">
              <GraduationCap className="h-3.5 w-3.5 text-slate-600" />
              Students
            </Button>
          </Link>
          <Link href="/hod/faculty">
            <Button variant="outline" size="sm" className="gap-1.5">
              <Users className="h-3.5 w-3.5 text-slate-600" />
              Faculty
            </Button>
          </Link>
          <Link href="/hod/attendance">
            <Button variant="primary" size="sm" className="gap-1.5">
              <CalendarCheck className="h-3.5 w-3.5" />
              Attendance Hub
            </Button>
          </Link>
        </div>
      </div>

      {/* SECTION A: Key Statistics Cards (8 cards grid) */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Students"
          value={stats.totalStudents}
          description="B.Tech & M.Tech batches"
          variant="indigo"
          icon={<GraduationCap className="h-4 w-4" />}
        />
        <StatCard
          label="Total Faculty"
          value={stats.totalFaculty}
          description="Teaching & Research Faculty"
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
          label="Total Classes / Sections"
          value={stats.totalClasses}
          description="Active instructional cohorts"
          variant="sky"
          icon={<Layers className="h-4 w-4" />}
        />
        <StatCard
          label="Avg Student Attendance"
          value={`${stats.averageStudentAttendance}%`}
          change={{ value: "+1.8% vs last week", trend: "up" }}
          description="Institution threshold: 75%"
          variant="emerald"
          icon={<CheckCircle2 className="h-4 w-4" />}
        />
        <StatCard
          label="Avg Faculty Attendance"
          value={`${stats.averageFacultyAttendance}%`}
          description="Present & biometric verified"
          variant="indigo"
          icon={<UserCheck className="h-4 w-4" />}
        />
        <StatCard
          label="Attendance Shortage"
          value={stats.studentsShortageCount}
          change={{ value: "Below 75% threshold", trend: "down" }}
          description="Requires immediate advisory"
          variant="amber"
          icon={<ShieldAlert className="h-4 w-4 text-rose-600" />}
        />
        <StatCard
          label="Pending Approvals"
          value={stats.pendingApprovalRequests}
          description="Leaves, exemptions, course files"
          variant="purple"
          icon={<FileCheck2 className="h-4 w-4 text-purple-600" />}
        />
      </div>

      {/* SECTION B & C: Student & Faculty Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Student Strength Analytics */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle>Student Strength & Cohorts</CardTitle>
              <CardDescription>
                Year-wise enrolment distribution and attendance rates
              </CardDescription>
            </div>
            <Link href="/hod/students">
              <Button variant="ghost" size="sm" className="text-xs">
                View Roster <ArrowRight className="h-3 w-3 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="space-y-4">
            {data.studentAnalytics.yearWiseStrength.map((y) => (
              <div key={y.year} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-800">{y.year}</span>
                  <div className="flex items-center gap-3">
                    <span className="text-slate-500 font-mono">{y.strength} students</span>
                    <span className="font-bold text-slate-900 font-mono">{y.percentage}% avg</span>
                  </div>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-yellow-400 transition-all"
                    style={{ width: `${y.percentage}%` }}
                  />
                </div>
              </div>
            ))}

            <div className="pt-2 border-t border-slate-100 grid grid-cols-3 gap-2 text-center">
              {data.studentAnalytics.sectionDistribution.map((sec) => (
                <div key={sec.section} className="p-2.5 rounded-lg bg-yellow-50/50 border border-yellow-200/50">
                  <div className="text-[10px] font-bold text-yellow-800 uppercase">{sec.section}</div>
                  <div className="text-sm font-bold text-slate-900 font-mono mt-0.5">{sec.students}</div>
                  <div className="text-[10px] text-slate-500 font-mono">{sec.attendance}% rate</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Faculty Analytics & Workload Summary */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle>Faculty Workload & Availability</CardTitle>
              <CardDescription>
                Teaching assignments, daily attendance, and hour distribution
              </CardDescription>
            </div>
            <Link href="/hod/faculty">
              <Button variant="ghost" size="sm" className="text-xs">
                Faculty Directory <ArrowRight className="h-3 w-3 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="p-3 rounded-xl border border-slate-200 bg-slate-50">
                <div className="text-xs font-medium text-slate-500">Total Faculty</div>
                <div className="text-2xl font-bold text-slate-900 font-mono mt-1">
                  {data.facultyAnalytics.total}
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">100% Ph.D./M.Tech</div>
              </div>
              <div className="p-3 rounded-xl border border-emerald-200 bg-emerald-50/50">
                <div className="text-xs font-medium text-emerald-800">Present Today</div>
                <div className="text-2xl font-bold text-emerald-900 font-mono mt-1">
                  {data.facultyAnalytics.presentToday}
                </div>
                <div className="text-[10px] text-emerald-700 mt-0.5">Verified biometric</div>
              </div>
              <div className="p-3 rounded-xl border border-amber-200 bg-amber-50/50">
                <div className="text-xs font-medium text-amber-800">On Duty / Leave</div>
                <div className="text-2xl font-bold text-amber-900 font-mono mt-1">
                  {data.facultyAnalytics.onLeave}
                </div>
                <div className="text-[10px] text-amber-700 mt-0.5">Approved requests</div>
              </div>
            </div>

            <div className="p-3.5 rounded-xl border border-slate-200 bg-white">
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="font-semibold text-slate-700">Average Department Teaching Load</span>
                <span className="font-bold font-mono text-slate-900">
                  {data.facultyAnalytics.averageWorkloadHours} hrs / week
                </span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                <div
                  className="h-full rounded-full bg-emerald-500"
                  style={{ width: `${(data.facultyAnalytics.averageWorkloadHours / 20) * 100}%` }}
                />
              </div>
              <p className="text-[10px] text-slate-500 mt-2">
                Statutory AICTE norm: 14–16 hrs/week for Associate/Professors, 16–18 hrs/week for Assistant Professors.
              </p>
            </div>

            <div className="flex items-center justify-between pt-1">
              <Link href="/hod/timetable" className="text-xs font-medium text-yellow-800 hover:text-yellow-950 flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5" />
                Inspect Department Timetable Grid
              </Link>
              <Badge variant="outline" className="font-mono text-[10px]">
                Semester 5 Allocation Active
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* SECTION D & E: Attendance Trends & Recent Activities */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Attendance Analytics (Daily & Weekly) */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle>Attendance Trends & Shortage Radar</CardTitle>
              <CardDescription>
                Day-by-day department compliance versus the 75% threshold
              </CardDescription>
            </div>
            <Link href="/hod/attendance">
              <Button variant="ghost" size="sm" className="text-xs">
                Detailed Log <ArrowRight className="h-3 w-3 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="text-xs font-semibold text-slate-700">Current Week Daily Rates:</div>
              <div className="grid grid-cols-5 gap-2">
                {data.attendanceTrends.daily.map((d) => (
                  <div key={d.day} className="p-2.5 rounded-lg border border-slate-200 bg-slate-50 text-center">
                    <div className="text-[11px] font-semibold text-slate-600">{d.day}</div>
                    <div className="text-base font-bold font-mono text-slate-900 mt-1">{d.rate}%</div>
                    <div className="text-[9px] text-emerald-600 font-semibold mt-0.5">Compliant</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-3.5 rounded-xl border border-rose-200 bg-rose-50/60 flex items-start gap-3">
              <ShieldAlert className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" />
              <div className="flex-1">
                <div className="text-xs font-bold text-rose-900">
                  {stats.studentsShortageCount} Students Flagged Below 75% Attendance
                </div>
                <p className="text-[11px] text-rose-700 mt-0.5">
                  University examination regulations require minimum 75% aggregate attendance. Automated advisory notices have been generated for parent communication.
                </p>
                <Link
                  href="/hod/attendance"
                  className="inline-flex items-center text-xs font-bold text-rose-900 hover:underline mt-2 gap-1"
                >
                  Review Shortage Roster & Issue Warnings <ArrowRight className="h-3 w-3" />
                </Link>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Recent Activities Feed */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle>Recent Departmental Activities</CardTitle>
              <CardDescription>
                Audit log of recent teaching, leaves, and attendance updates
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {data.recentActivities.map((act) => (
                <div
                  key={act.id}
                  className="flex items-start gap-3 p-2.5 rounded-lg border border-slate-100 hover:bg-yellow-50/30 transition-colors"
                >
                  <div className="h-8 w-8 rounded-lg bg-yellow-100 text-yellow-950 flex items-center justify-center shrink-0 border border-yellow-300">
                    {act.type === "attendance" && <CalendarCheck className="h-4 w-4" />}
                    {act.type === "faculty" && <UserCheck className="h-4 w-4" />}
                    {act.type === "student" && <GraduationCap className="h-4 w-4" />}
                    {act.type === "request" && <FileCheck2 className="h-4 w-4" />}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900 truncate">
                        {act.title}
                      </span>
                      <span className="text-[10px] text-slate-400 shrink-0 font-mono">
                        {act.timestamp}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-600 mt-0.5 leading-relaxed">
                      {act.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* SECTION F: Quick Actions Grid */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle>HOD Operational Quick Actions</CardTitle>
          <CardDescription>
            Direct links to department administration and monitoring workflows
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <Link
              href="/hod/students"
              className="flex items-center justify-between p-3.5 rounded-xl border border-slate-200 bg-white hover:border-yellow-400 hover:bg-yellow-50/50 shadow-xs transition-all group"
            >
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 rounded-lg bg-yellow-100 text-yellow-900 flex items-center justify-center group-hover:bg-yellow-400 group-hover:text-slate-950 transition-colors border border-yellow-300">
                  <GraduationCap className="h-4 w-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-900">Student Roster</div>
                  <div className="text-[10px] text-slate-500">720 CSE Students</div>
                </div>
              </div>
              <ArrowRight className="h-4 w-4 text-slate-400 group-hover:text-slate-900 transition-colors" />
            </Link>

            <Link
              href="/hod/faculty"
              className="flex items-center justify-between p-3.5 rounded-xl border border-slate-200 bg-white hover:border-yellow-400 hover:bg-yellow-50/50 shadow-xs transition-all group"
            >
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 rounded-lg bg-yellow-100 text-yellow-900 flex items-center justify-center group-hover:bg-yellow-400 group-hover:text-slate-950 transition-colors border border-yellow-300">
                  <Users className="h-4 w-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-900">Faculty Directory</div>
                  <div className="text-[10px] text-slate-500">28 Faculty Members</div>
                </div>
              </div>
              <ArrowRight className="h-4 w-4 text-slate-400 group-hover:text-slate-900 transition-colors" />
            </Link>

            <Link
              href="/hod/attendance"
              className="flex items-center justify-between p-3.5 rounded-xl border border-slate-200 bg-white hover:border-yellow-400 hover:bg-yellow-50/50 shadow-xs transition-all group"
            >
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 rounded-lg bg-yellow-100 text-yellow-900 flex items-center justify-center group-hover:bg-yellow-400 group-hover:text-slate-950 transition-colors border border-yellow-300">
                  <CalendarCheck className="h-4 w-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-900">Attendance Monitoring</div>
                  <div className="text-[10px] text-slate-500">88.4% Average Rate</div>
                </div>
              </div>
              <ArrowRight className="h-4 w-4 text-slate-400 group-hover:text-slate-900 transition-colors" />
            </Link>

            <Link
              href="/hod/timetable"
              className="flex items-center justify-between p-3.5 rounded-xl border border-slate-200 bg-white hover:border-yellow-400 hover:bg-yellow-50/50 shadow-xs transition-all group"
            >
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 rounded-lg bg-yellow-100 text-yellow-900 flex items-center justify-center group-hover:bg-yellow-400 group-hover:text-slate-950 transition-colors border border-yellow-300">
                  <Calendar className="h-4 w-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-900">Timetable Grid</div>
                  <div className="text-[10px] text-slate-500">Class & Lab Schedules</div>
                </div>
              </div>
              <ArrowRight className="h-4 w-4 text-slate-400 group-hover:text-slate-900 transition-colors" />
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
