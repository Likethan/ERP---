"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { attendanceService } from "@/services/attendance.service";
import { AttendanceSession, AttendanceSessionStatus, SessionType } from "@/types/attendance";
import { DataGrid } from "@/components/data-grid/data-grid";
import { ColumnDef } from "@/components/data-grid/data-grid.types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { useToast } from "@/components/ui/toast";
import {
  CalendarCheck,
  Plus,
  Clock,
  MapPin,
  User,
  BookOpen,
  Calendar,
  Layers,
  ArrowRight,
  Filter,
} from "lucide-react";

export default function AttendanceSessionsPage() {
  const { hasPermission } = useAuth();
  const router = useRouter();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [sessions, setSessions] = useState<AttendanceSession[]>([]);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [departmentFilter, setDepartmentFilter] = useState<string>("ALL");
  const [sectionFilter, setSectionFilter] = useState<string>("ALL");
  const [dateFilter, setDateFilter] = useState<string>("");

  // Create Modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    courseOfferingId: "off-cs301-a",
    courseCode: "CS301",
    courseName: "Data Structures & Algorithms",
    section: "5th Sem CSE — Sec A",
    department: "Computer Science & Engineering",
    facultyName: "Dr. Rajesh Sharma",
    date: new Date().toISOString().split("T")[0],
    startTime: "09:30 AM",
    endTime: "10:30 AM",
    room: "Hall 302, Academic Block A",
    sessionType: "THEORY" as SessionType,
    totalStudents: 68,
    topicCovered: "",
  });

  const loadSessions = async () => {
    try {
      setLoading(true);
      const res = await attendanceService.getSessions({
        date: dateFilter || undefined,
        department: departmentFilter !== "ALL" ? departmentFilter : undefined,
        section: sectionFilter !== "ALL" ? sectionFilter : undefined,
        status: statusFilter !== "ALL" ? statusFilter : undefined,
      });
      if (res.success) {
        setSessions(res.data);
      }
    } catch (err) {
      console.error("Failed to load sessions", err);
      showToast({ type: "error", title: "Load Error", message: "Unable to retrieve attendance sessions." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, [statusFilter, departmentFilter, sectionFilter, dateFilter]);

  const handleCreateSession = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      const res = await attendanceService.createSession(formData);
      if (res.success) {
        showToast({ type: "success", title: "Session Created", message: `Session for ${res.data.courseCode} scheduled successfully.` });
        setCreateModalOpen(false);
        await loadSessions();
        router.push(`/app/attendance/sessions/${res.data.id}`);
      }
    } catch (err) {
      console.error("Failed to create session", err);
      showToast({ type: "error", title: "Creation Failed", message: "Could not schedule session." });
    } finally {
      setSaving(false);
    }
  };

  const getStatusBadge = (status: AttendanceSessionStatus) => {
    switch (status) {
      case "COMPLETED":
        return <Badge variant="success">Completed</Badge>;
      case "OPEN":
        return <Badge variant="info">Open for Marking</Badge>;
      case "SCHEDULED":
        return <Badge variant="secondary">Scheduled</Badge>;
      case "CANCELLED":
        return <Badge variant="destructive">Cancelled</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const columns: ColumnDef<AttendanceSession>[] = useMemo(
    () => [
      {
        id: "date",
        header: "Date & Period",
        cell: (row) => (
          <div>
            <div className="font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
              <Calendar className="h-3.5 w-3.5 text-slate-400" />
              {row.date}
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1 mt-0.5">
              <Clock className="h-3 w-3 text-slate-400" />
              {row.startTime} — {row.endTime}
            </div>
          </div>
        ),
        sortable: true,
      },
      {
        id: "subject",
        header: "Course & Type",
        cell: (row) => (
          <div>
            <div className="font-semibold text-slate-900 dark:text-white">
              {row.courseCode}
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400 truncate max-w-[200px]">
              {row.courseName}
            </div>
            <span className="inline-block mt-1 px-1.5 py-0.5 text-[10px] font-medium rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
              {row.sessionType}
            </span>
          </div>
        ),
        sortable: true,
      },
      {
        id: "section",
        header: "Section & Venue",
        cell: (row) => (
          <div>
            <div className="font-medium text-slate-800 dark:text-slate-200">
              {row.section}
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1 mt-0.5">
              <MapPin className="h-3 w-3 text-slate-400" />
              {row.room}
            </div>
          </div>
        ),
      },
      {
        id: "faculty",
        header: "Instructor",
        cell: (row) => (
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-full bg-slate-100 text-slate-700 font-semibold flex items-center justify-center text-xs dark:bg-slate-800 dark:text-slate-300">
              {row.facultyName.charAt(0)}
            </div>
            <div>
              <div className="font-medium text-slate-900 dark:text-white text-xs">
                {row.facultyName}
              </div>
              <div className="text-[11px] text-slate-500">{row.department}</div>
            </div>
          </div>
        ),
      },
      {
        id: "attendanceSummary",
        header: "Attendance",
        cell: (row) => {
          if (row.status !== "COMPLETED") {
            return (
              <span className="text-xs text-slate-400 italic">Not marked</span>
            );
          }
          return (
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-xs text-slate-900 dark:text-white">
                  {row.attendancePercentage}%
                </span>
                <span className="text-[11px] text-slate-500">
                  ({row.presentCount}P / {row.absentCount}A)
                </span>
              </div>
              <div className="mt-1 h-1.5 w-24 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    row.attendancePercentage >= 85
                      ? "bg-emerald-500"
                      : row.attendancePercentage >= 75
                      ? "bg-amber-500"
                      : "bg-rose-500"
                  }`}
                  style={{ width: `${row.attendancePercentage}%` }}
                />
              </div>
            </div>
          );
        },
      },
      {
        id: "status",
        header: "Status",
        cell: (row) => getStatusBadge(row.status),
      },
      {
        id: "actions",
        header: "Actions",
        cell: (row) => (
          <div className="flex items-center gap-2">
            <Link href={`/app/attendance/sessions/${row.id}`}>
              <Button
                size="sm"
                variant={row.status === "OPEN" ? "primary" : "outline"}
                className="h-8 gap-1.5 text-xs"
              >
                {row.status === "OPEN" ? "Mark Attendance" : "View Register"}
                <ArrowRight className="h-3 w-3" />
              </Button>
            </Link>
          </div>
        ),
      },
    ],
    []
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300">
              Timetable Registers
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">Class Attendance</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Attendance Sessions & Rosters
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Schedule lecture periods, open real-time biometric or manual student rosters, and audit signed registers.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="primary"
            className="gap-2"
            onClick={() => setCreateModalOpen(true)}
          >
            <Plus className="h-4 w-4" />
            Schedule New Session
          </Button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3 bg-slate-50/70 p-3 rounded-xl border border-slate-200 dark:bg-slate-900/60 dark:border-slate-800 text-xs">
        <div className="flex items-center gap-1.5 text-slate-500 font-medium">
          <Filter className="h-3.5 w-3.5" />
          Filters:
        </div>

        {/* Date Filter */}
        <div>
          <input
            type="date"
            value={dateFilter}
            onChange={(e) => setDateFilter(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>

        {/* Status Filter */}
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="ALL">All Statuses</option>
          <option value="OPEN">Open for Marking</option>
          <option value="COMPLETED">Completed</option>
          <option value="SCHEDULED">Scheduled</option>
          <option value="CANCELLED">Cancelled</option>
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
          <option value="Mechanical">Mechanical</option>
          <option value="Artificial Intelligence">AI & Data Science</option>
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

        {(statusFilter !== "ALL" || departmentFilter !== "ALL" || sectionFilter !== "ALL" || dateFilter !== "") && (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              setStatusFilter("ALL");
              setDepartmentFilter("ALL");
              setSectionFilter("ALL");
              setDateFilter("");
            }}
            className="text-xs h-7 px-2 text-rose-600 hover:text-rose-700"
          >
            Clear Filters
          </Button>
        )}
      </div>

      {/* Enterprise DataGrid */}
      <DataGrid<AttendanceSession>
        data={sessions}
        columns={columns}
        keyExtractor={(row) => row.id}
        loading={loading}
        searchPlaceholder="Search sessions by subject code, title, section, or faculty..."
        emptyTitle="No attendance sessions found"
        emptyDescription="Schedule a new lecture period to open a register."
      />

      {/* Schedule New Session Modal */}
      <Dialog
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Schedule New Attendance Session"
      >
        <form onSubmit={handleCreateSession} className="space-y-4">
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Connect an academic course offering with a timetable slot and classroom venue.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Course Offering
              </label>
              <select
                value={formData.courseCode}
                onChange={(e) => {
                  const val = e.target.value;
                  if (val === "CS301") {
                    setFormData({
                      ...formData,
                      courseOfferingId: "off-cs301-a",
                      courseCode: "CS301",
                      courseName: "Data Structures & Algorithms",
                      facultyName: "Dr. Rajesh Sharma",
                    });
                  } else if (val === "CS302") {
                    setFormData({
                      ...formData,
                      courseOfferingId: "off-cs302-a",
                      courseCode: "CS302",
                      courseName: "Database Management Systems",
                      facultyName: "Dr. K. S. Anand",
                    });
                  } else if (val === "CS303") {
                    setFormData({
                      ...formData,
                      courseOfferingId: "off-cs303-a",
                      courseCode: "CS303",
                      courseName: "Operating Systems & Concurrency",
                      facultyName: "Prof. Meenakshi Sundaram",
                    });
                  }
                }}
                className="w-full rounded-lg border border-slate-300 bg-white p-2 text-xs dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              >
                <option value="CS301">CS301 — Data Structures & Algorithms</option>
                <option value="CS302">CS302 — Database Management Systems</option>
                <option value="CS303">CS303 — Operating Systems & Concurrency</option>
              </select>
            </div>

            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Target Section
              </label>
              <select
                value={formData.section}
                onChange={(e) => setFormData({ ...formData, section: e.target.value })}
                className="w-full rounded-lg border border-slate-300 bg-white p-2 text-xs dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              >
                <option value="5th Sem CSE — Sec A">5th Sem CSE — Sec A</option>
                <option value="5th Sem CSE — Sec B">5th Sem CSE — Sec B</option>
              </select>
            </div>

            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Date
              </label>
              <input
                type="date"
                required
                value={formData.date}
                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                className="w-full rounded-lg border border-slate-300 bg-white p-2 text-xs dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              >
              </input>
            </div>

            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Session Type
              </label>
              <select
                value={formData.sessionType}
                onChange={(e) => setFormData({ ...formData, sessionType: e.target.value as SessionType })}
                className="w-full rounded-lg border border-slate-300 bg-white p-2 text-xs dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              >
                <option value="THEORY">Theory Lecture</option>
                <option value="LAB">Practical / Laboratory</option>
                <option value="TUTORIAL">Tutorial Session</option>
                <option value="SEMINAR">Seminar / Workshop</option>
              </select>
            </div>

            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Start Time
              </label>
              <input
                type="text"
                value={formData.startTime}
                onChange={(e) => setFormData({ ...formData, startTime: e.target.value })}
                placeholder="09:30 AM"
                className="w-full rounded-lg border border-slate-300 bg-white p-2 text-xs dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>

            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                End Time
              </label>
              <input
                type="text"
                value={formData.endTime}
                onChange={(e) => setFormData({ ...formData, endTime: e.target.value })}
                placeholder="10:30 AM"
                className="w-full rounded-lg border border-slate-300 bg-white p-2 text-xs dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Room / Venue
              </label>
              <input
                type="text"
                value={formData.room}
                onChange={(e) => setFormData({ ...formData, room: e.target.value })}
                placeholder="Hall 302, Academic Block A"
                className="w-full rounded-lg border border-slate-300 bg-white p-2 text-xs dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Topic Planned / Delivered
              </label>
              <input
                type="text"
                value={formData.topicCovered}
                onChange={(e) => setFormData({ ...formData, topicCovered: e.target.value })}
                placeholder="e.g. Red-Black Trees Insertion and Balancing Operations"
                className="w-full rounded-lg border border-slate-300 bg-white p-2 text-xs dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              onClick={() => setCreateModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={saving}>
              {saving ? "Scheduling..." : "Schedule & Open Session"}
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
