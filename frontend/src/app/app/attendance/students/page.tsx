"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { attendanceService } from "@/services/attendance.service";
import {
  AttendanceStudentSummary,
  AttendanceRiskLevel,
} from "@/types/attendance";
import { DataGrid } from "@/components/data-grid/data-grid";
import { ColumnDef } from "@/components/data-grid/data-grid.types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/ui/stat-card";
import { useToast } from "@/components/ui/toast";
import {
  GraduationCap,
  AlertTriangle,
  CheckCircle2,
  TrendingDown,
  Filter,
  ArrowRight,
  ShieldAlert,
} from "lucide-react";

export default function StudentAttendanceDirectoryPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [summaries, setSummaries] = useState<AttendanceStudentSummary[]>([]);

  // Filters
  const [riskFilter, setRiskFilter] = useState<string>("ALL");
  const [departmentFilter, setDepartmentFilter] = useState<string>("ALL");
  const [sectionFilter, setSectionFilter] = useState<string>("ALL");

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await attendanceService.listStudentSummaries({
        riskLevel: riskFilter !== "ALL" ? riskFilter : undefined,
        department: departmentFilter !== "ALL" ? departmentFilter : undefined,
        section: sectionFilter !== "ALL" ? sectionFilter : undefined,
      });
      if (res.success) {
        setSummaries(res.data);
      }
    } catch (err) {
      console.error("Failed to load student summaries", err);
      showToast({
        type: "error",
        title: "Load Error",
        message: "Failed to load student attendance directory.",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [riskFilter, departmentFilter, sectionFilter]);

  const healthyCount = summaries.filter(
    (s) => s.riskLevel === "HEALTHY",
  ).length;
  const warningCount = summaries.filter(
    (s) => s.riskLevel === "WARNING",
  ).length;
  const criticalCount = summaries.filter(
    (s) => s.riskLevel === "CRITICAL",
  ).length;

  const getRiskBadge = (risk: AttendanceRiskLevel) => {
    switch (risk) {
      case "HEALTHY":
        return <Badge variant="success">Healthy (&ge;80%)</Badge>;
      case "WARNING":
        return <Badge variant="warning">Warning (&lt;80%)</Badge>;
      case "CRITICAL":
        return <Badge variant="destructive">Critical (&lt;65%)</Badge>;
      default:
        return <Badge variant="outline">{risk}</Badge>;
    }
  };

  const columns: ColumnDef<AttendanceStudentSummary>[] = useMemo(
    () => [
      {
        id: "student",
        header: "Student Name & Roll No.",
        cell: (row) => (
          <div>
            <div className="font-semibold text-slate-900 dark:text-white">
              {row.studentName}
            </div>
            <div className="text-xs text-slate-500">{row.rollNumber}</div>
          </div>
        ),
        sortable: true,
      },
      {
        id: "program",
        header: "Program & Section",
        cell: (row) => (
          <div>
            <div className="font-medium text-slate-800 dark:text-slate-200 text-xs">
              {row.program}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">
              Sem {row.semester} • Section {row.section}
            </div>
          </div>
        ),
      },
      {
        id: "sessions",
        header: "Attendance Ratio",
        cell: (row) => (
          <div>
            <div className="font-semibold text-xs text-slate-900 dark:text-white">
              {row.attendedSessions} / {row.totalSessions} Sessions
            </div>
            <div className="text-[11px] text-slate-500">
              {row.presentCount}P • {row.absentCount}A • {row.lateCount}L
            </div>
          </div>
        ),
        sortable: true,
      },
      {
        id: "percentage",
        header: "Attendance %",
        cell: (row) => (
          <div>
            <div className="flex items-center gap-2">
              <span
                className={`font-bold text-sm ${
                  row.percentage >= 80
                    ? "text-emerald-600 dark:text-emerald-400"
                    : row.percentage >= 75
                      ? "text-amber-600 dark:text-amber-400"
                      : "text-rose-600 dark:text-rose-400"
                }`}
              >
                {row.percentage}%
              </span>
            </div>
            <div className="mt-1 h-1.5 w-20 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
              <div
                className={`h-full rounded-full ${
                  row.percentage >= 80
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
        id: "riskLevel",
        header: "Status",
        cell: (row) => getRiskBadge(row.riskLevel),
        sortable: true,
      },
      {
        id: "actions",
        header: "Actions",
        cell: (row) => (
          <div className="flex items-center gap-2">
            <Link href={`/app/attendance/students/${row.studentId}`}>
              <Button size="sm" variant="outline" className="h-7 text-xs gap-1">
                360° Profile
                <ArrowRight className="h-3 w-3" />
              </Button>
            </Link>
          </div>
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
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
              Student Directory
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              Attendance Monitoring
            </span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Student Attendance Directory
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Track student attendance percentages, detect shortage risks, and
            audit subject-level delivery compliance.
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          title="Healthy Attendance (&ge;80%)"
          value={loading ? "..." : String(healthyCount)}
          description="Eligible for examinations without condonation"
          icon={<CheckCircle2 className="h-5 w-5 text-emerald-600" />}
        />
        <StatCard
          title="Warning Shortage (75%–79.9%)"
          value={loading ? "..." : String(warningCount)}
          description="Requires academic counselor advisory"
          icon={<AlertTriangle className="h-5 w-5 text-amber-600" />}
        />
        <StatCard
          title="Critical Shortage (&lt;65%)"
          value={loading ? "..." : String(criticalCount)}
          description="At risk of hall ticket debarment"
          icon={<ShieldAlert className="h-5 w-5 text-rose-600" />}
        />
      </div>

      {/* Filters Bar */}
      <div className="flex flex-wrap items-center gap-3 bg-slate-50/70 p-3 rounded-xl border border-slate-200 dark:bg-slate-900/60 dark:border-slate-800 text-xs">
        <div className="flex items-center gap-1.5 text-slate-500 font-medium">
          <Filter className="h-3.5 w-3.5" />
          Filter Cohort:
        </div>

        {/* Risk Level Filter */}
        <select
          value={riskFilter}
          onChange={(e) => setRiskFilter(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="ALL">All Risk Levels</option>
          <option value="HEALTHY">Healthy (&ge;80%)</option>
          <option value="WARNING">Warning (&lt;80%)</option>
          <option value="CRITICAL">Critical (&lt;65%)</option>
        </select>

        {/* Department Filter */}
        <select
          value={departmentFilter}
          onChange={(e) => setDepartmentFilter(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="ALL">All Departments</option>
          <option value="Computer Science">Computer Science</option>
          <option value="Electronics">Electronics</option>
        </select>

        {/* Section Filter */}
        <select
          value={sectionFilter}
          onChange={(e) => setSectionFilter(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="ALL">All Sections</option>
          <option value="A">Section A</option>
          <option value="B">Section B</option>
        </select>

        {(riskFilter !== "ALL" ||
          departmentFilter !== "ALL" ||
          sectionFilter !== "ALL") && (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              setRiskFilter("ALL");
              setDepartmentFilter("ALL");
              setSectionFilter("ALL");
            }}
            className="text-xs h-7 px-2 text-rose-600 hover:text-rose-700"
          >
            Clear Filters
          </Button>
        )}
      </div>

      {/* Enterprise DataGrid */}
      <DataGrid<AttendanceStudentSummary>
        data={summaries}
        columns={columns}
        keyExtractor={(row) => row.studentId}
        loading={loading}
        searchPlaceholder="Search student by name, roll number, or program..."
        emptyTitle="No student records found"
        emptyDescription="No student matches the active attendance filter."
      />
    </div>
  );
}
