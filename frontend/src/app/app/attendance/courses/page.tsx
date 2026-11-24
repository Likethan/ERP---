"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { attendanceService } from "@/services/attendance.service";
import { AttendanceCourseSummary } from "@/types/attendance";
import { DataGrid } from "@/components/data-grid/data-grid";
import { ColumnDef } from "@/components/data-grid/data-grid.types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/ui/stat-card";
import { useToast } from "@/components/ui/toast";
import {
  BookOpen,
  ArrowRight,
  Filter,
  CheckCircle2,
  AlertTriangle,
  User,
  MapPin,
  CalendarCheck,
} from "lucide-react";

export default function CourseAttendanceDirectoryPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [courses, setCourses] = useState<AttendanceCourseSummary[]>([]);
  const [riskFilter, setRiskFilter] = useState<string>("ALL");
  const [sectionFilter, setSectionFilter] = useState<string>("ALL");

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await attendanceService.listCourseSummaries({
        riskLevel: riskFilter !== "ALL" ? riskFilter : undefined,
        section: sectionFilter !== "ALL" ? sectionFilter : undefined,
      });
      if (res.success) {
        setCourses(res.data);
      }
    } catch (err) {
      console.error("Failed to load course summaries", err);
      showToast({
        type: "error",
        title: "Load Error",
        message: "Failed to load course attendance summaries.",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [riskFilter, sectionFilter]);

  const columns: ColumnDef<AttendanceCourseSummary>[] = useMemo(
    () => [
      {
        id: "course",
        header: "Course & Title",
        cell: (row) => (
          <div>
            <div className="font-semibold text-slate-900 dark:text-white">
              {row.courseCode}
            </div>
            <div className="text-xs text-slate-500 truncate max-w-[200px]">
              {row.courseName}
            </div>
            <span className="inline-block mt-1 px-1.5 py-0.5 text-[10px] font-medium rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
              Section {row.section}
            </span>
          </div>
        ),
        sortable: true,
      },
      {
        id: "faculty",
        header: "Instructor",
        cell: (row) => (
          <div className="text-xs text-slate-800 dark:text-slate-200 font-medium">
            {row.facultyName}
          </div>
        ),
        sortable: true,
      },
      {
        id: "sessions",
        header: "Sessions Delivered",
        cell: (row) => (
          <div className="text-xs font-semibold text-slate-900 dark:text-white">
            {row.totalSessions} Lectures
          </div>
        ),
        sortable: true,
      },
      {
        id: "attendance",
        header: "Class Average %",
        cell: (row) => (
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-xs text-slate-900 dark:text-white">
                {row.percentage}%
              </span>
            </div>
            <div className="mt-1 h-1.5 w-20 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
              <div
                className={`h-full rounded-full ${
                  row.percentage >= 85
                    ? "bg-emerald-500"
                    : row.percentage >= 75
                      ? "bg-amber-500"
                      : "bg-rose-500"
                }`}
                style={{ width: `${row.percentage}%` }}
              />
            </div>
          </div>
        ),
        sortable: true,
      },
      {
        id: "atRisk",
        header: "Students At Risk",
        cell: (row) => (
          <div>
            <span
              className={`font-semibold text-xs ${row.studentsBelowThresholdCount ? "text-rose-600" : "text-emerald-600"}`}
            >
              {row.studentsBelowThresholdCount || 0} students (&lt;75%)
            </span>
            <div className="text-[10px] text-slate-400">
              {row.studentsAtRiskCount || 0} in warning zone
            </div>
          </div>
        ),
      },
      {
        id: "actions",
        header: "Actions",
        cell: (row) => (
          <Link href={`/app/attendance/courses/${row.courseOfferingId}`}>
            <Button size="sm" variant="outline" className="h-7 text-xs gap-1">
              Class Telemetry
              <ArrowRight className="h-3 w-3" />
            </Button>
          </Link>
        ),
      },
    ],
    [],
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-purple-100 text-purple-800 dark:bg-purple-950/60 dark:text-purple-300">
              Curriculum Cohorts
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              Course Offering Attendance
            </span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Course Offering Registers
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Monitor class delivery averages, identify low-attendance courses,
            and inspect student rosters.
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          title="Active Course Registers"
          value={loading ? "..." : String(courses.length)}
          description="Subject offerings with scheduled sessions"
          icon={<BookOpen className="h-5 w-5 text-indigo-600" />}
        />
        <StatCard
          title="Institutional Average Rate"
          value="88.9%"
          description="Aggregate across all courses"
          icon={<CalendarCheck className="h-5 w-5 text-emerald-600" />}
        />
        <StatCard
          title="Flagged Shortage Courses"
          value="2"
          description="Courses with &gt;3 students below 75%"
          icon={<AlertTriangle className="h-5 w-5 text-rose-600" />}
        />
      </div>

      {/* Filters Bar */}
      <div className="flex flex-wrap items-center gap-3 bg-slate-50/70 p-3 rounded-xl border border-slate-200 dark:bg-slate-900/60 dark:border-slate-800 text-xs">
        <div className="flex items-center gap-1.5 text-slate-500 font-medium">
          <Filter className="h-3.5 w-3.5" />
          Filter Courses:
        </div>

        <select
          value={sectionFilter}
          onChange={(e) => setSectionFilter(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="ALL">All Sections</option>
          <option value="A">Section A</option>
          <option value="B">Section B</option>
        </select>

        <select
          value={riskFilter}
          onChange={(e) => setRiskFilter(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="ALL">All Statuses</option>
          <option value="HEALTHY">Healthy</option>
          <option value="WARNING">Warning</option>
        </select>
      </div>

      {/* Enterprise DataGrid */}
      <DataGrid<AttendanceCourseSummary>
        data={courses}
        columns={columns}
        keyExtractor={(row) => row.courseOfferingId}
        loading={loading}
        searchPlaceholder="Search courses by code, title, or faculty instructor..."
        emptyTitle="No course offerings found"
        emptyDescription="No course offerings match your filter criteria."
      />
    </div>
  );
}
