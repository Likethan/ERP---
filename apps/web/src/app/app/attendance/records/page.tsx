"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { attendanceService } from "@/services/attendance.service";
import { AttendanceRecord, AttendanceStatus } from "@/types/attendance";
import { DataGrid } from "@/components/data-grid/data-grid";
import { ColumnDef } from "@/components/data-grid/data-grid.types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import {
  Layers,
  Calendar,
  User,
  BookOpen,
  Filter,
  CheckCircle2,
  XCircle,
  Clock,
  HelpCircle,
} from "lucide-react";

export default function AttendanceRecordsPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [records, setRecords] = useState<AttendanceRecord[]>([]);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [courseFilter, setCourseFilter] = useState<string>("ALL");
  const [sectionFilter, setSectionFilter] = useState<string>("ALL");

  const loadRecords = async () => {
    try {
      setLoading(true);
      const res = await attendanceService.getRecords({
        status: statusFilter !== "ALL" ? statusFilter : undefined,
        courseCode: courseFilter !== "ALL" ? courseFilter : undefined,
        section: sectionFilter !== "ALL" ? sectionFilter : undefined,
      });
      if (res.success) {
        setRecords(res.data);
      }
    } catch (err) {
      console.error("Failed to load records", err);
      showToast({
        type: "error",
        title: "Load Error",
        message: "Failed to load attendance records ledger.",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRecords();
  }, [statusFilter, courseFilter, sectionFilter]);

  const getStatusBadge = (status: AttendanceStatus) => {
    switch (status) {
      case "PRESENT":
        return <Badge variant="success">Present</Badge>;
      case "ABSENT":
        return <Badge variant="destructive">Absent</Badge>;
      case "LATE":
        return <Badge variant="warning">Late</Badge>;
      case "EXCUSED":
        return <Badge variant="info">Excused</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const columns: ColumnDef<AttendanceRecord>[] = useMemo(
    () => [
      {
        id: "student",
        header: "Student",
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
        id: "course",
        header: "Course & Section",
        cell: (row) => (
          <div>
            <div className="font-semibold text-slate-900 dark:text-white">
              {row.courseCode}
            </div>
            <div className="text-xs text-slate-500 truncate max-w-[180px]">
              {row.courseName}
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              {row.section}
            </div>
          </div>
        ),
        sortable: true,
      },
      {
        id: "status",
        header: "Marked Status",
        cell: (row) => getStatusBadge(row.status),
        sortable: true,
      },
      {
        id: "markedInfo",
        header: "Marked By & Time",
        cell: (row) => (
          <div>
            <div className="text-xs text-slate-800 dark:text-slate-200 font-medium">
              {row.markedBy}
            </div>
            <div className="text-[11px] text-slate-500">
              {new Date(row.markedAt).toLocaleDateString()} at{" "}
              {new Date(row.markedAt).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </div>
          </div>
        ),
      },
      {
        id: "remarks",
        header: "Remarks / Justification",
        cell: (row) => (
          <div className="text-xs text-slate-600 dark:text-slate-400 italic">
            {row.remarks || "—"}
          </div>
        ),
      },
      {
        id: "actions",
        header: "Actions",
        cell: (row) => (
          <div className="flex items-center gap-2">
            <Link href={`/app/attendance/students/${row.studentId}`}>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 px-2 text-xs text-indigo-600 hover:text-indigo-700"
              >
                Student 360°
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
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300">
              Master Ledger
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              Attendance Records
            </span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Comprehensive Attendance Records
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Immutable institutional record of individual student attendance
            across all class offerings and sections.
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 bg-slate-50/70 p-3 rounded-xl border border-slate-200 dark:bg-slate-900/60 dark:border-slate-800 text-xs">
        <div className="flex items-center gap-1.5 text-slate-500 font-medium">
          <Filter className="h-3.5 w-3.5" />
          Filter Records:
        </div>

        {/* Status Filter */}
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="ALL">All Statuses</option>
          <option value="PRESENT">Present</option>
          <option value="ABSENT">Absent</option>
          <option value="LATE">Late</option>
          <option value="EXCUSED">Excused</option>
        </select>

        {/* Course Filter */}
        <select
          value={courseFilter}
          onChange={(e) => setCourseFilter(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="ALL">All Courses</option>
          <option value="CS301">CS301 — Data Structures</option>
          <option value="CS302">CS302 — DBMS</option>
          <option value="CS303">CS303 — OS</option>
        </select>

        {/* Section Filter */}
        <select
          value={sectionFilter}
          onChange={(e) => setSectionFilter(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="ALL">All Sections</option>
          <option value="Sec A">Section A</option>
          <option value="Sec B">Section B</option>
        </select>

        {(statusFilter !== "ALL" ||
          courseFilter !== "ALL" ||
          sectionFilter !== "ALL") && (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              setStatusFilter("ALL");
              setCourseFilter("ALL");
              setSectionFilter("ALL");
            }}
            className="text-xs h-7 px-2 text-rose-600 hover:text-rose-700"
          >
            Clear Filters
          </Button>
        )}
      </div>

      {/* Enterprise DataGrid */}
      <DataGrid<AttendanceRecord>
        data={records}
        columns={columns}
        keyExtractor={(row) => row.id}
        loading={loading}
        searchPlaceholder="Search by student name, roll number, course code, or title..."
        emptyTitle="No attendance records found"
        emptyDescription="No attendance entries match your active filter criteria."
      />
    </div>
  );
}
