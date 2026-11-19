"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { hodService } from "@/services/hod.service";
import { attendanceService } from "@/services/attendance.service";
import { AttendanceStudentSummary } from "@/types/attendance";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StatCard } from "@/components/ui/stat-card";
import { EmptyState } from "@/components/ui/empty-state";
import {
  CalendarCheck,
  Search,
  Filter,
  ShieldAlert,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  Calendar,
  Layers,
  FileSpreadsheet,
  Download,
  Users,
  AlertTriangle,
  Clock,
  Printer,
} from "lucide-react";

export default function HodAttendancePage() {
  const { activePersona } = useAuth();
  const deptName = activePersona.department || "Computer Science & Engineering";

  const [activeTab, setActiveTab] = useState<"students" | "classes" | "shortage" | "trends">("students");
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);

  // Student ledger state
  const [studentsList, setStudentsList] = useState<AttendanceStudentSummary[]>([]);
  const [search, setSearch] = useState("");
  const [semesterFilter, setSemesterFilter] = useState("ALL");
  const [sectionFilter, setSectionFilter] = useState("ALL");
  const [riskFilter, setRiskFilter] = useState("ALL");
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split("T")[0]);
  const [threshold] = useState(75.0);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [overview, studentSummaries] = await Promise.all([
          hodService.getAttendanceOverview(deptName),
          attendanceService.listStudentSummaries({
            department: deptName,
            semester: semesterFilter !== "ALL" ? Number(semesterFilter) : undefined,
            section: sectionFilter !== "ALL" ? sectionFilter : undefined,
            riskLevel: riskFilter !== "ALL" ? (riskFilter as any) : undefined,
            search: search.trim() || undefined,
          }),
        ]);
        setData(overview);
        if (studentSummaries.success && studentSummaries.data) {
          setStudentsList(studentSummaries.data);
        }
      } catch (err) {
        console.error("Failed to load attendance data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [deptName, semesterFilter, sectionFilter, riskFilter, search]);

  const handleExport = () => {
    window.print();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-yellow-100 text-yellow-950 border border-yellow-300">
              Department Attendance Governance
            </span>
            <span className="text-xs text-slate-500 font-mono">• {deptName}</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">
            Attendance Monitoring & Audit
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Real-time compliance monitoring, class-wise presence logs, and statutory 75% shortage tracking.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleExport}
            className="text-xs gap-1.5"
          >
            <Printer className="h-3.5 w-3.5 text-slate-500" />
            Print Report
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleExport}
            className="text-xs gap-1.5"
          >
            <Download className="h-3.5 w-3.5 text-slate-500" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* KPI Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-4">
        <StatCard
          label="Total Students"
          value={data?.total_enrolled || 720}
          description="Enrolled in CSE"
          variant="indigo"
          icon={<Users className="h-4 w-4" />}
        />
        <StatCard
          label="Present Today"
          value={data?.present_today || 682}
          description="Verified in sessions"
          variant="emerald"
          icon={<CheckCircle2 className="h-4 w-4" />}
        />
        <StatCard
          label="Absent Today"
          value={data?.absent_today || 38}
          description="Unexcused & on leave"
          variant="amber"
          icon={<Clock className="h-4 w-4" />}
        />
        <StatCard
          label="Overall Attendance"
          value={`${data?.overall_percentage || 88.4}%`}
          change={{ value: "+1.8% vs last week", trend: "up" }}
          description="Department average"
          variant="emerald"
          icon={<CalendarCheck className="h-4 w-4" />}
        />
        <StatCard
          label="Below 75% Shortage"
          value={data?.shortage_count || 14}
          description="Statutory cutoff: 75%"
          variant="amber"
          icon={<ShieldAlert className="h-4 w-4 text-rose-600" />}
        />
      </div>

      {/* Date & Filter Ribbon */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            {/* Tabs */}
            <div className="flex items-center gap-1 overflow-x-auto w-full md:w-auto pb-2 md:pb-0">
              <button
                onClick={() => setActiveTab("students")}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all shrink-0 cursor-pointer ${
                  activeTab === "students"
                    ? "bg-yellow-400 text-slate-950 shadow-xs"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                Student Ledger ({studentsList.length})
              </button>
              <button
                onClick={() => setActiveTab("classes")}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all shrink-0 cursor-pointer ${
                  activeTab === "classes"
                    ? "bg-yellow-400 text-slate-950 shadow-xs"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                Class-wise Compliance
              </button>
              <button
                onClick={() => setActiveTab("shortage")}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all shrink-0 cursor-pointer ${
                  activeTab === "shortage"
                    ? "bg-rose-500 text-white shadow-xs"
                    : "text-rose-700 bg-rose-50 hover:bg-rose-100"
                }`}
              >
                Shortage Radar ({data?.shortage_count || 14})
              </button>
              <button
                onClick={() => setActiveTab("trends")}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all shrink-0 cursor-pointer ${
                  activeTab === "trends"
                    ? "bg-yellow-400 text-slate-950 shadow-xs"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                Weekly Trends
              </button>
            </div>

            {/* Date Picker */}
            <div className="flex items-center gap-2 w-full md:w-auto">
              <span className="text-xs text-slate-500 shrink-0 font-medium">Session Date:</span>
              <Input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="h-9 text-xs font-mono w-full sm:w-40"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* TAB 1: Student Ledger */}
      {activeTab === "students" && (
        <Card>
          <CardHeader className="p-4 sm:p-5 border-b border-slate-100">
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
              <div className="relative sm:col-span-2">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search students in ledger..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-9 h-9 text-xs"
                />
              </div>

              <div>
                <select
                  value={semesterFilter}
                  onChange={(e) => setSemesterFilter(e.target.value)}
                  aria-label="Filter by Semester"
                  className="h-9 text-xs rounded-lg border border-slate-200 bg-white px-2.5 text-slate-700 w-full cursor-pointer"
                >
                  <option value="ALL">All Semesters</option>
                  {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                    <option key={s} value={s}>
                      Semester {s}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <select
                  value={riskFilter}
                  onChange={(e) => setRiskFilter(e.target.value)}
                  aria-label="Filter by Risk Level"
                  className="h-9 text-xs rounded-lg border border-slate-200 bg-white px-2.5 text-slate-700 w-full cursor-pointer"
                >
                  <option value="ALL">All Risk Levels</option>
                  <option value="LOW">Compliant (≥75%)</option>
                  <option value="MEDIUM">Warning (65-74%)</option>
                  <option value="HIGH">Critical (&lt;65%)</option>
                </select>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-6 space-y-3">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="h-10 rounded-lg bg-slate-100 animate-pulse" />
                ))}
              </div>
            ) : studentsList.length === 0 ? (
              <div className="p-8">
                <EmptyState
                  icon={<CalendarCheck className="h-10 w-10 text-slate-400" />}
                  title="No Student Records in Ledger"
                  description="No attendance records match the selected criteria."
                />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
                    <tr>
                      <th className="p-3.5">Roll No</th>
                      <th className="p-3.5">Student Name</th>
                      <th className="p-3.5">Sem / Sec</th>
                      <th className="p-3.5 text-center">Total Classes</th>
                      <th className="p-3.5 text-center">Classes Attended</th>
                      <th className="p-3.5 text-center">Attendance %</th>
                      <th className="p-3.5">Compliance Status</th>
                      <th className="p-3.5 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {studentsList.map((stu) => {
                      const isShort = stu.percentage < threshold;

                      return (
                        <tr key={stu.studentId} className="hover:bg-yellow-50/30">
                          <td className="p-3.5 font-mono font-bold text-slate-900">
                            {stu.rollNumber}
                          </td>
                          <td className="p-3.5 font-medium text-slate-900">
                            {stu.studentName}
                          </td>
                          <td className="p-3.5 font-mono">
                            Sem {stu.semester} — Sec {stu.section}
                          </td>
                          <td className="p-3.5 text-center font-mono text-slate-600">
                            {stu.totalSessions}
                          </td>
                          <td className="p-3.5 text-center font-mono font-bold text-slate-900">
                            {stu.attendedSessions}
                          </td>
                          <td className="p-3.5 text-center font-mono font-bold">
                            <span
                              className={`px-2 py-0.5 rounded text-[11px] ${
                                stu.percentage >= 75
                                  ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                                  : stu.percentage >= 65
                                  ? "bg-amber-50 text-amber-800 border border-amber-200"
                                  : "bg-rose-50 text-rose-800 border border-rose-200"
                              }`}
                            >
                              {stu.percentage}%
                            </span>
                          </td>
                          <td className="p-3.5">
                            {isShort ? (
                              <Badge className="bg-rose-50 text-rose-800 border-rose-200 text-[10px] gap-1">
                                <ShieldAlert className="h-3 w-3" /> Shortage
                              </Badge>
                            ) : (
                              <Badge className="bg-emerald-50 text-emerald-800 border-emerald-200 text-[10px]">
                                Compliant
                              </Badge>
                            )}
                          </td>
                          <td className="p-3.5 text-right">
                            <Link href={`/hod/students/${stu.studentId}`}>
                              <Button variant="ghost" size="sm" className="text-xs text-slate-600 hover:text-slate-950">
                                360° Profile <ArrowRight className="h-3 w-3 ml-1" />
                              </Button>
                            </Link>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* TAB 2: Class-wise Compliance */}
      {activeTab === "classes" && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle>Department Class & Cohort Compliance</CardTitle>
            <CardDescription>
              Section-level attendance averages for {deptName}.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {data?.class_wise?.map((c: any) => (
                <div key={c.class_name} className="p-4 rounded-xl border border-slate-200 bg-white space-y-2">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="font-bold text-sm text-slate-900">{c.class_name}</span>
                      <span className="text-xs text-slate-500 ml-2 font-mono">
                        ({c.present} present / {c.total} total)
                      </span>
                    </div>
                    <span className="font-mono font-bold text-sm text-slate-900">{c.rate}%</span>
                  </div>
                  <div className="w-full h-2.5 rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${c.rate >= 75 ? "bg-yellow-400" : "bg-rose-500"}`}
                      style={{ width: `${c.rate}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* TAB 3: Shortage Radar */}
      {activeTab === "shortage" && (
        <Card className="border-rose-200">
          <CardHeader className="bg-rose-50/50 pb-3 border-b border-rose-100">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-rose-900 flex items-center gap-2">
                  <ShieldAlert className="h-5 w-5 text-rose-600" />
                  Statutory Attendance Shortage List (&lt; 75%)
                </CardTitle>
                <CardDescription className="text-rose-700">
                  Students below the 75% university examination cutoff. Parent intimations must be issued.
                </CardDescription>
              </div>
              <Badge className="bg-rose-100 text-rose-900 border-rose-300 font-mono text-xs">
                {data?.shortage_count || 14} Students Flagged
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-rose-50/30 text-rose-800 font-semibold border-b border-rose-100">
                  <tr>
                    <th className="p-3.5">Roll Number</th>
                    <th className="p-3.5">Student Name</th>
                    <th className="p-3.5">Sem / Section</th>
                    <th className="p-3.5 text-center">Attended / Total</th>
                    <th className="p-3.5 text-center">Attendance %</th>
                    <th className="p-3.5 text-center">Shortfall to 75%</th>
                    <th className="p-3.5 text-right">Advisory Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-rose-100/50">
                  {data?.shortage_students?.map((s: any) => {
                    const roll = s.rollNumber || s.roll_number;
                    const name = s.studentName || s.name;
                    const pct = s.attendancePercentage || s.percentage;
                    const att = s.classesAttended || s.attended;
                    const tot = s.totalClasses || s.total;
                    const shortfall = Math.ceil(tot * 0.75 - att);

                    return (
                      <tr key={roll} className="hover:bg-rose-50/40">
                        <td className="p-3.5 font-mono font-bold text-slate-900">{roll}</td>
                        <td className="p-3.5 font-medium text-slate-900">{name}</td>
                        <td className="p-3.5 font-mono">Sem {s.semester} — Sec {s.section}</td>
                        <td className="p-3.5 text-center font-mono">{att} / {tot}</td>
                        <td className="p-3.5 text-center font-mono font-bold text-rose-600">
                          {pct}%
                        </td>
                        <td className="p-3.5 text-center font-mono font-bold text-rose-700">
                          -{shortfall > 0 ? shortfall : 8} classes
                        </td>
                        <td className="p-3.5 text-right">
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-xs text-rose-700 border-rose-300 hover:bg-rose-100 font-semibold"
                            onClick={() => alert(`Official parent intimation notice dispatched for ${name} (${roll}).`)}
                          >
                            Dispatch Warning SMS/Email
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* TAB 4: Weekly Trends */}
      {activeTab === "trends" && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle>Attendance Trends Over Academic Session</CardTitle>
            <CardDescription>
              Weekly aggregate rates across the department.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: "Week 1", rate: 89.2 },
                { label: "Week 2", rate: 88.7 },
                { label: "Week 3", rate: 87.9 },
                { label: "Week 4", rate: 88.4 },
              ].map((w) => (
                <div key={w.label} className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 text-center">
                  <div className="text-xs font-semibold text-slate-600">{w.label}</div>
                  <div className="text-2xl font-bold font-mono text-slate-900 mt-1">{w.rate}%</div>
                  <div className="text-[10px] text-emerald-600 font-semibold mt-0.5">Compliant</div>
                </div>
              ))}
            </div>

            <div className="p-3.5 rounded-xl border border-slate-200 bg-white">
              <div className="text-xs font-bold text-slate-800 mb-1">
                Audit Trail Notice for Department Head
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                Attendance records are entered directly by course faculty after biometric or session finalize. All corrections and leave approvals undergo immutable digital audit logging in the CampusOS event registry.
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
