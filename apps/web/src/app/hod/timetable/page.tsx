"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import {
  hodService,
  TimetablePeriod,
  TimetableScheduleItem,
  FacultyWorkloadItem,
} from "@/services/hod.service";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/ui/stat-card";
import {
  Calendar,
  Clock,
  BookOpen,
  Users,
  Building,
  CheckCircle2,
  Printer,
  Download,
  AlertCircle,
  ShieldCheck,
  Layers,
} from "lucide-react";

export default function HodTimetablePage() {
  const { activePersona } = useAuth();
  const deptName = activePersona.department || "Computer Science & Engineering";

  const [semester, setSemester] = useState(5);
  const [section, setSection] = useState("A");
  const [viewMode, setViewMode] = useState<"grid" | "workload">("grid");

  const periods: TimetablePeriod[] = hodService.getTimetablePeriods();
  const schedule: TimetableScheduleItem[] = hodService.getDepartmentSchedule(
    semester,
    section,
  );
  const facultyWorkloads: FacultyWorkloadItem[] =
    hodService.getFacultyWorkloads();

  const days = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
  ];

  // Helper to find schedule entry for a given day and period
  const getCellItem = (day: string, periodNumber: number) => {
    return schedule.find((s) => s.day === day && s.period === periodNumber);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-yellow-100 text-yellow-950 border border-yellow-300">
              Department Academic Scheduling
            </span>
            <span className="text-xs text-slate-500 font-mono">
              • {deptName}
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">
            Timetable Management
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Read-only master timetable schedule, classroom allocations,
            laboratory blocks, and faculty teaching loads.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handlePrint}
            className="text-xs gap-1.5"
          >
            <Printer className="h-3.5 w-3.5 text-slate-500" />
            Print Schedule
          </Button>
          <div className="flex rounded-lg border border-slate-200 bg-white p-0.5 shadow-xs">
            <button
              onClick={() => setViewMode("grid")}
              className={`px-3 py-1.5 rounded-md text-xs font-bold transition-all cursor-pointer ${
                viewMode === "grid"
                  ? "bg-yellow-400 text-slate-950 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Weekly Grid
            </button>
            <button
              onClick={() => setViewMode("workload")}
              className={`px-3 py-1.5 rounded-md text-xs font-bold transition-all cursor-pointer ${
                viewMode === "workload"
                  ? "bg-yellow-400 text-slate-950 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Faculty Workloads
            </button>
          </div>
        </div>
      </div>

      {/* Filter and Cohort Selector */}
      <Card>
        <CardContent className="p-4 sm:p-5">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3 w-full sm:w-auto">
              <div>
                <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                  Academic Semester
                </label>
                <select
                  value={semester}
                  onChange={(e) => setSemester(Number(e.target.value))}
                  aria-label="Academic Semester"
                  className="h-9 text-xs rounded-lg border border-slate-200 bg-white px-3 font-semibold text-slate-800 cursor-pointer"
                >
                  {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                    <option key={s} value={s}>
                      Semester {s} (B.Tech CSE)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                  Section Cohort
                </label>
                <select
                  value={section}
                  onChange={(e) => setSection(e.target.value)}
                  aria-label="Section Cohort"
                  className="h-9 text-xs rounded-lg border border-slate-200 bg-white px-3 font-semibold text-slate-800 cursor-pointer"
                >
                  <option value="A">Section A (68 Students)</option>
                  <option value="B">Section B (65 Students)</option>
                  <option value="C">Section C (67 Students)</option>
                </select>
              </div>
            </div>

            {/* Timetable Integrity Indicator */}
            <div className="flex items-center gap-2 p-2 px-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 font-semibold w-full sm:w-auto justify-center">
              <ShieldCheck className="h-4 w-4 text-emerald-600 shrink-0" />
              <span>
                0 Scheduling Conflicts Detected (Faculty & Rooms Verified)
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* VIEW 1: Weekly Grid */}
      {viewMode === "grid" && (
        <Card>
          <CardHeader className="pb-3 border-b border-slate-100 flex flex-row items-center justify-between">
            <div>
              <CardTitle>
                Semester {semester} — Section {section} Master Timetable
              </CardTitle>
              <CardDescription>
                Monday through Saturday schedule with classrooms, faculty, and
                laboratory slots.
              </CardDescription>
            </div>
            <Badge variant="outline" className="font-mono text-xs">
              42 Instructional Hours / Week
            </Badge>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                    <th className="p-3 border-r border-slate-200 w-28 text-center uppercase tracking-wider text-[10px]">
                      Day / Period
                    </th>
                    {periods.map((p) => (
                      <th
                        key={p.period}
                        className="p-2.5 border-r border-slate-200 text-center min-w-[150px]"
                      >
                        <div className="font-bold text-slate-900">
                          Period {p.period}
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono font-normal mt-0.5">
                          {p.time}
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {days.map((day) => (
                    <tr
                      key={day}
                      className="hover:bg-yellow-50/20 transition-colors"
                    >
                      {/* Day Label */}
                      <td className="p-3 border-r border-slate-200 font-bold text-slate-800 bg-slate-50/70 text-center">
                        {day}
                      </td>

                      {/* Period Cells */}
                      {periods.map((p) => {
                        const item = getCellItem(day, p.period);

                        if (!item) {
                          return (
                            <td
                              key={p.period}
                              className="p-2 border-r border-slate-200 bg-slate-50/40 text-center text-slate-400"
                            >
                              <span className="text-[11px] font-mono">—</span>
                            </td>
                          );
                        }

                        return (
                          <td
                            key={p.period}
                            className={`p-2.5 border-r border-slate-200 align-top transition-colors ${
                              item.isLab
                                ? "bg-amber-50/70 border-l-2 border-l-amber-500"
                                : "bg-white hover:bg-yellow-50/50 border-l-2 border-l-yellow-400"
                            }`}
                          >
                            <div className="space-y-1">
                              <div className="flex items-center justify-between gap-1">
                                <span className="font-mono font-bold text-slate-900 text-[11px]">
                                  {item.subjectCode}
                                </span>
                                {item.isLab && (
                                  <Badge className="bg-amber-100 text-amber-900 border-amber-300 text-[8px] px-1 py-0 font-bold">
                                    LAB
                                  </Badge>
                                )}
                              </div>
                              <div className="font-semibold text-slate-800 text-[11px] leading-tight line-clamp-1">
                                {item.subjectName}
                              </div>
                              <div className="text-[10px] text-slate-600 truncate">
                                {item.facultyName}
                              </div>
                              <div className="text-[9px] text-slate-400 font-mono flex items-center gap-1 pt-0.5">
                                <Building className="h-2.5 w-2.5 text-slate-400" />
                                {item.classroom}
                              </div>
                            </div>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* VIEW 2: Faculty Workload Matrix */}
      {viewMode === "workload" && (
        <Card>
          <CardHeader className="pb-3 border-b border-slate-100">
            <CardTitle>Department Faculty Workload Distribution</CardTitle>
            <CardDescription>
              Teaching contact hours allocated across professors for current
              academic cycle.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="p-3.5">Faculty Name</th>
                    <th className="p-3.5">Designation</th>
                    <th className="p-3.5">Assigned Subjects & Sections</th>
                    <th className="p-3.5 text-center">Weekly Hours</th>
                    <th className="p-3.5 text-center">Workload Status</th>
                    <th className="p-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {facultyWorkloads.map((fw) => (
                    <tr key={fw.facultyId} className="hover:bg-yellow-50/30">
                      <td className="p-3.5 font-bold text-slate-900">
                        {fw.facultyName}
                      </td>
                      <td className="p-3.5 text-slate-600">{fw.designation}</td>
                      <td className="p-3.5">
                        <div className="flex flex-wrap gap-1">
                          {fw.assignedSubjects.map((sub, i) => (
                            <Badge
                              key={i}
                              variant="outline"
                              className="font-mono text-[10px]"
                            >
                              {sub}
                            </Badge>
                          ))}
                        </div>
                      </td>
                      <td className="p-3.5 text-center font-mono font-bold text-slate-900">
                        {fw.weeklyHours} hrs/wk
                      </td>
                      <td className="p-3.5 text-center">
                        <Badge
                          className={
                            fw.status === "OPTIMAL"
                              ? "bg-emerald-50 text-emerald-800 border-emerald-200 text-[10px]"
                              : "bg-amber-50 text-amber-800 border-amber-200 text-[10px]"
                          }
                        >
                          {fw.status}
                        </Badge>
                      </td>
                      <td className="p-3.5 text-right">
                        <Link href={`/hod/faculty/${fw.facultyId}`}>
                          <Button variant="ghost" size="sm" className="text-xs">
                            Profile
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Classroom Allocation Reference */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wider text-slate-500">
              Assigned Classrooms
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1.5 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-600">Hall 302 (Block A):</span>
              <span className="font-mono font-bold text-slate-900">
                CSE 5th Sem - Sec A
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-600">Hall 304 (Block A):</span>
              <span className="font-mono font-bold text-slate-900">
                CSE 5th Sem - Sec B
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-600">Hall 306 (Block A):</span>
              <span className="font-mono font-bold text-slate-900">
                CSE 5th Sem - Sec C
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wider text-slate-500">
              Department Laboratories
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1.5 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-600">CS Lab 1 (Programming):</span>
              <span className="font-mono font-bold text-emerald-700">
                60 Terminals (Active)
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-600">CS Lab 2 (Database/OS):</span>
              <span className="font-mono font-bold text-emerald-700">
                60 Terminals (Active)
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-600">CS Lab 3 (Networks/IoT):</span>
              <span className="font-mono font-bold text-emerald-700">
                45 Terminals (Active)
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wider text-slate-500">
              Scheduling Policy Notice
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-slate-500 leading-relaxed">
            Per institutional ERP governance rules, Master Timetable
            modifications are approved by the Vice Principal (Academics) and
            HOD. Timetable edits trigger automatic calendar synchronization for
            all enrolled students and faculty.
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
