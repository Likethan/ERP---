"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { attendanceService } from "@/services/attendance.service";
import {
  AttendanceSession,
  AttendanceRecord,
  AttendanceStatus,
} from "@/types/attendance";
import { calculateAttendancePercentage } from "@/services/attendance-calculator";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { useToast } from "@/components/ui/toast";
import {
  Calendar,
  Clock,
  MapPin,
  User,
  BookOpen,
  ArrowLeft,
  Save,
  CheckCircle2,
  XCircle,
  AlertCircle,
  HelpCircle,
  Search,
  History,
  AlertTriangle,
  RotateCcw,
  Sparkles,
} from "lucide-react";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function SessionDetailPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const sessionId = resolvedParams.id;
  const router = useRouter();
  const { hasPermission } = useAuth();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [session, setSession] = useState<AttendanceSession | null>(null);
  const [roster, setRoster] = useState<AttendanceRecord[]>([]);

  // Working state for active attendance marking: studentId -> { status, remarks }
  const [studentStates, setStudentStates] = useState<
    Record<string, { status: AttendanceStatus; remarks: string }>
  >({});
  const [initialStates, setInitialStates] = useState<
    Record<string, { status: AttendanceStatus; remarks: string }>
  >({});
  const [isDirty, setIsDirty] = useState(false);

  // Search & Filter
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState<string>("ALL");

  // Correction Modal
  const [correctionModalOpen, setCorrectionModalOpen] = useState(false);
  const [selectedStudentForCorrection, setSelectedStudentForCorrection] =
    useState<AttendanceRecord | null>(null);
  const [correctionReason, setCorrectionReason] = useState("");
  const [requestedStatus, setRequestedStatus] =
    useState<AttendanceStatus>("PRESENT");
  const [submittingCorrection, setSubmittingCorrection] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [sessRes, rosterRes] = await Promise.all([
        attendanceService.getSessionById(sessionId),
        attendanceService.getSessionRoster(sessionId),
      ]);

      if (sessRes.success && sessRes.data) {
        setSession(sessRes.data);
      }
      if (rosterRes.success) {
        setRoster(rosterRes.data);
        const map: Record<
          string,
          { status: AttendanceStatus; remarks: string }
        > = {};
        rosterRes.data.forEach((r) => {
          map[r.studentId] = { status: r.status, remarks: r.remarks || "" };
        });
        setStudentStates(map);
        setInitialStates(map);
        setIsDirty(false);
      }
    } catch (err) {
      console.error("Failed to load session details", err);
      showToast({
        type: "error",
        title: "Load Error",
        message: "Failed to load session roster.",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [sessionId]);

  // Unsaved changes alert before unloading page
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [isDirty]);

  const updateStudentStatus = (studentId: string, status: AttendanceStatus) => {
    setStudentStates((prev) => {
      const updated = {
        ...prev,
        [studentId]: { ...prev[studentId], status },
      };
      setIsDirty(true);
      return updated;
    });
  };

  const handleMarkAll = (status: AttendanceStatus) => {
    setStudentStates((prev) => {
      const updated = { ...prev };
      roster.forEach((r) => {
        updated[r.studentId] = { ...updated[r.studentId], status };
      });
      setIsDirty(true);
      return updated;
    });
    showToast({
      type: "info",
      title: "Batch Action",
      message: `All ${roster.length} students marked as ${status}.`,
    });
  };

  const handleReset = () => {
    setStudentStates({ ...initialStates });
    setIsDirty(false);
    showToast({
      type: "info",
      title: "Reset Complete",
      message: "Restored initial roster state.",
    });
  };

  const handleSaveAttendance = async () => {
    try {
      setSaving(true);
      const recordsToSubmit = roster.map((r) => ({
        studentId: r.studentId,
        status: studentStates[r.studentId]?.status || "PRESENT",
        remarks: studentStates[r.studentId]?.remarks,
      }));

      const res = await attendanceService.submitSessionAttendance(
        sessionId,
        recordsToSubmit,
      );
      if (res.success) {
        showToast({
          type: "success",
          title: "Attendance Saved",
          message: `Successfully recorded attendance for ${res.data.updatedCount} students.`,
        });
        setIsDirty(false);
        await loadData();
      }
    } catch (err) {
      console.error("Failed to save attendance", err);
      showToast({
        type: "error",
        title: "Save Error",
        message: "Unable to persist attendance records.",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleRequestCorrection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedStudentForCorrection || !session) return;
    try {
      setSubmittingCorrection(true);
      const res = await attendanceService.submitCorrection({
        sessionId: session.id,
        recordId: selectedStudentForCorrection.id,
        studentId: selectedStudentForCorrection.studentId,
        studentName: selectedStudentForCorrection.studentName,
        rollNumber: selectedStudentForCorrection.rollNumber,
        courseCode: session.courseCode,
        courseName: session.courseName,
        sessionDate: session.date,
        originalStatus:
          studentStates[selectedStudentForCorrection.studentId]?.status ||
          selectedStudentForCorrection.status,
        requestedStatus,
        reason: correctionReason,
        requestedBy: session.facultyName,
        requestedRole: "FACULTY",
      });

      if (res.success) {
        showToast({
          type: "success",
          title: "Correction Requested",
          message: "Request submitted to HOD for formal review and sign-off.",
        });
        setCorrectionModalOpen(false);
        setCorrectionReason("");
      }
    } catch (err) {
      console.error("Failed to submit correction", err);
      showToast({
        type: "error",
        title: "Request Failed",
        message: "Could not submit correction request.",
      });
    } finally {
      setSubmittingCorrection(false);
    }
  };

  // Filtered Roster
  const filteredRoster = roster.filter((r) => {
    const currentState = studentStates[r.studentId]?.status || r.status;
    const matchesStatus =
      filterStatus === "ALL" || currentState === filterStatus;
    const matchesSearch =
      r.studentName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.rollNumber.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  // Dynamic Live Metrics based on working state
  const totalInRoster = roster.length;
  const currentPresent = Object.values(studentStates).filter(
    (s) => s.status === "PRESENT",
  ).length;
  const currentAbsent = Object.values(studentStates).filter(
    (s) => s.status === "ABSENT",
  ).length;
  const currentLate = Object.values(studentStates).filter(
    (s) => s.status === "LATE",
  ).length;
  const currentExcused = Object.values(studentStates).filter(
    (s) => s.status === "EXCUSED",
  ).length;
  const livePercentage = calculateAttendancePercentage({
    present: currentPresent,
    absent: currentAbsent,
    late: currentLate,
    excused: currentExcused,
    total: totalInRoster,
  });

  if (loading && !session) {
    return (
      <div className="flex items-center justify-center min-h-[300px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    );
  }

  if (!session) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-12 text-center dark:border-slate-800 dark:bg-slate-900">
        <h3 className="text-base font-semibold text-slate-900 dark:text-white">
          Session Not Found
        </h3>
        <p className="mt-1 text-xs text-slate-500">
          The requested attendance session does not exist.
        </p>
        <Link href="/app/attendance/sessions" className="mt-4 inline-block">
          <Button variant="outline" size="sm">
            Back to Sessions
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-4 dark:border-slate-800">
        <div className="flex items-center gap-3">
          <Link href="/app/attendance/sessions">
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-900 dark:text-white text-lg">
                {session.courseCode}: {session.courseName}
              </span>
              <Badge
                variant={session.status === "COMPLETED" ? "success" : "info"}
              >
                {session.status}
              </Badge>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {session.section} • {session.sessionType} Lecture Register
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isDirty && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleReset}
              className="gap-1.5 text-xs"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              Discard
            </Button>
          )}
          <Button
            variant="primary"
            size="sm"
            onClick={handleSaveAttendance}
            disabled={saving}
            className="gap-1.5 text-xs"
          >
            <Save className="h-3.5 w-3.5" />
            {saving ? "Saving..." : "Save Attendance"}
          </Button>
        </div>
      </div>

      {/* Unsaved Changes Banner */}
      {isDirty && (
        <div className="rounded-xl border border-amber-300 bg-amber-50 p-3.5 flex items-center justify-between dark:border-amber-900/60 dark:bg-amber-950/40">
          <div className="flex items-center gap-2.5 text-xs text-amber-900 dark:text-amber-200">
            <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0" />
            <span>
              <strong>You have unsaved changes.</strong> Any modifications to
              attendance will be lost if you leave this page without saving.
            </span>
          </div>
          <Button
            size="sm"
            variant="primary"
            onClick={handleSaveAttendance}
            disabled={saving}
            className="h-7 text-xs bg-amber-600 hover:bg-amber-700"
          >
            Save Changes
          </Button>
        </div>
      )}

      {/* Session Metadata & Live Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900 md:col-span-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2.5">
            Session Details
          </h3>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
              <Calendar className="h-4 w-4 text-slate-400" />
              <span>{session.date}</span>
            </div>
            <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
              <Clock className="h-4 w-4 text-slate-400" />
              <span>
                {session.startTime} — {session.endTime}
              </span>
            </div>
            <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
              <User className="h-4 w-4 text-slate-400" />
              <span>{session.facultyName}</span>
            </div>
            <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
              <MapPin className="h-4 w-4 text-slate-400" />
              <span>{session.room}</span>
            </div>
          </div>
          {session.topicCovered && (
            <div className="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800 text-xs">
              <span className="font-medium text-slate-500">Topic: </span>
              <span className="text-slate-800 dark:text-slate-200">
                {session.topicCovered}
              </span>
            </div>
          )}
        </div>

        {/* Live Attendance Rate Card */}
        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900 flex flex-col justify-between">
          <div>
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
              Attendance Rate
            </h3>
            <div className="flex items-baseline gap-2 mt-2">
              <span className="text-3xl font-extrabold text-slate-900 dark:text-white">
                {livePercentage}%
              </span>
              <span className="text-xs text-slate-500">effective</span>
            </div>
          </div>
          <div className="mt-3">
            <div className="h-2 w-full rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
              <div
                className={`h-full rounded-full ${
                  livePercentage >= 85
                    ? "bg-emerald-500"
                    : livePercentage >= 75
                      ? "bg-amber-500"
                      : "bg-rose-500"
                }`}
                style={{ width: `${livePercentage}%` }}
              />
            </div>
          </div>
        </div>

        {/* Headcount Breakdown */}
        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Roster Headcount
          </h3>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="rounded-lg bg-emerald-50 p-2 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300">
              <div className="font-bold text-base">{currentPresent}</div>
              <div className="text-[10px] text-emerald-600">Present</div>
            </div>
            <div className="rounded-lg bg-rose-50 p-2 text-rose-800 dark:bg-rose-950/40 dark:text-rose-300">
              <div className="font-bold text-base">{currentAbsent}</div>
              <div className="text-[10px] text-rose-600">Absent</div>
            </div>
            <div className="rounded-lg bg-amber-50 p-2 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300">
              <div className="font-bold text-base">{currentLate}</div>
              <div className="text-[10px] text-amber-600">Late (0.5x)</div>
            </div>
            <div className="rounded-lg bg-blue-50 p-2 text-blue-800 dark:bg-blue-950/40 dark:text-blue-300">
              <div className="font-bold text-base">{currentExcused}</div>
              <div className="text-[10px] text-blue-600">Excused</div>
            </div>
          </div>
        </div>
      </div>

      {/* Roster Controls: Search, Quick Mark All, Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 bg-slate-50/70 p-3 rounded-xl border border-slate-200 dark:bg-slate-900/60 dark:border-slate-800 text-xs">
        <div className="flex items-center gap-2 flex-1 max-w-sm">
          <div className="relative w-full">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search student by name or roll number..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white pl-8 pr-3 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Status filter */}
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="ALL">All ({roster.length})</option>
            <option value="PRESENT">Present only</option>
            <option value="ABSENT">Absent only</option>
            <option value="LATE">Late only</option>
            <option value="EXCUSED">Excused only</option>
          </select>

          {/* Quick Mark All Buttons */}
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleMarkAll("PRESENT")}
            className="text-xs h-7 text-emerald-700 border-emerald-300 hover:bg-emerald-50 dark:border-emerald-800 dark:text-emerald-300"
          >
            Mark All Present
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleMarkAll("ABSENT")}
            className="text-xs h-7 text-rose-700 border-rose-300 hover:bg-rose-50 dark:border-rose-800 dark:text-rose-300"
          >
            Mark All Absent
          </Button>
        </div>
      </div>

      {/* Main Student Roster Table (Optimized for speed & keyboard navigation) */}
      <div className="rounded-xl border border-slate-200 bg-white overflow-hidden dark:border-slate-800 dark:bg-slate-900">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 dark:bg-slate-800/50 dark:border-slate-800 dark:text-slate-400">
                <th className="py-3 px-4 font-semibold w-12 text-center">#</th>
                <th className="py-3 px-4 font-semibold">
                  Student Name & Roll Number
                </th>
                <th className="py-3 px-4 font-semibold text-center">
                  Attendance Marking
                </th>
                <th className="py-3 px-4 font-semibold">Remarks</th>
                <th className="py-3 px-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {filteredRoster.map((record, index) => {
                const currentStatus =
                  studentStates[record.studentId]?.status || record.status;
                const remarks = studentStates[record.studentId]?.remarks || "";

                return (
                  <tr
                    key={record.studentId}
                    className="hover:bg-slate-50/70 transition dark:hover:bg-slate-800/40"
                  >
                    <td className="py-3 px-4 text-center text-slate-400 font-medium">
                      {index + 1}
                    </td>

                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-900 dark:text-white">
                        {record.studentName}
                      </div>
                      <div className="text-[11px] text-slate-500">
                        {record.rollNumber}
                      </div>
                    </td>

                    {/* Quick Button Group: [Present] [Absent] [Late] [Excused] */}
                    <td className="py-3 px-4 text-center">
                      <div className="inline-flex rounded-lg border border-slate-200 bg-slate-100/70 p-0.5 dark:border-slate-700 dark:bg-slate-800">
                        <button
                          type="button"
                          onClick={() =>
                            updateStudentStatus(record.studentId, "PRESENT")
                          }
                          className={`px-3 py-1 text-xs font-semibold rounded-md transition ${
                            currentStatus === "PRESENT"
                              ? "bg-emerald-600 text-white shadow-xs"
                              : "text-slate-600 hover:text-slate-900 dark:text-slate-300"
                          }`}
                        >
                          Present
                        </button>
                        <button
                          type="button"
                          onClick={() =>
                            updateStudentStatus(record.studentId, "ABSENT")
                          }
                          className={`px-3 py-1 text-xs font-semibold rounded-md transition ${
                            currentStatus === "ABSENT"
                              ? "bg-rose-600 text-white shadow-xs"
                              : "text-slate-600 hover:text-slate-900 dark:text-slate-300"
                          }`}
                        >
                          Absent
                        </button>
                        <button
                          type="button"
                          onClick={() =>
                            updateStudentStatus(record.studentId, "LATE")
                          }
                          className={`px-3 py-1 text-xs font-semibold rounded-md transition ${
                            currentStatus === "LATE"
                              ? "bg-amber-600 text-white shadow-xs"
                              : "text-slate-600 hover:text-slate-900 dark:text-slate-300"
                          }`}
                        >
                          Late
                        </button>
                        <button
                          type="button"
                          onClick={() =>
                            updateStudentStatus(record.studentId, "EXCUSED")
                          }
                          className={`px-3 py-1 text-xs font-semibold rounded-md transition ${
                            currentStatus === "EXCUSED"
                              ? "bg-blue-600 text-white shadow-xs"
                              : "text-slate-600 hover:text-slate-900 dark:text-slate-300"
                          }`}
                        >
                          Excused
                        </button>
                      </div>
                    </td>

                    <td className="py-3 px-4">
                      <input
                        type="text"
                        placeholder="Optional remarks..."
                        value={remarks}
                        onChange={(e) => {
                          const val = e.target.value;
                          setStudentStates((prev) => ({
                            ...prev,
                            [record.studentId]: {
                              ...prev[record.studentId],
                              remarks: val,
                            },
                          }));
                          setIsDirty(true);
                        }}
                        className="w-full rounded-md border border-slate-200 bg-transparent px-2 py-1 text-xs text-slate-800 dark:border-slate-700 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      />
                    </td>

                    <td className="py-3 px-4 text-right">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          setSelectedStudentForCorrection(record);
                          setRequestedStatus(
                            currentStatus === "ABSENT" ? "PRESENT" : "EXCUSED",
                          );
                          setCorrectionModalOpen(true);
                        }}
                        className="h-7 text-xs text-slate-500 hover:text-indigo-600"
                      >
                        Request Correction
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Audit Timeline */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center gap-2 mb-3">
          <History className="h-4 w-4 text-slate-500" />
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
            Session Audit Log
          </h3>
        </div>
        <div className="space-y-3 text-xs">
          <div className="flex items-start gap-3">
            <div className="h-2 w-2 rounded-full bg-indigo-500 mt-1.5" />
            <div>
              <div className="font-medium text-slate-900 dark:text-white">
                Session Scheduled & Timetable Synced
              </div>
              <div className="text-[11px] text-slate-500">
                Created on {new Date(session.createdAt).toLocaleString()} by
                Academic Timetable Engine
              </div>
            </div>
          </div>
          {session.submittedAt && (
            <div className="flex items-start gap-3">
              <div className="h-2 w-2 rounded-full bg-emerald-500 mt-1.5" />
              <div>
                <div className="font-medium text-slate-900 dark:text-white">
                  Attendance Register Recorded & Signed
                </div>
                <div className="text-[11px] text-slate-500">
                  Submitted on {new Date(session.submittedAt).toLocaleString()}{" "}
                  by {session.facultyName}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Attendance Correction Modal */}
      <Dialog
        open={correctionModalOpen}
        onClose={() => setCorrectionModalOpen(false)}
        title="Request Attendance Correction"
      >
        <form onSubmit={handleRequestCorrection} className="space-y-4 text-xs">
          <p className="text-slate-500">
            Attendance records cannot be silently overwritten once marked.
            Submit a justification for HOD scrutiny.
          </p>

          <div className="rounded-lg bg-slate-50 p-3 border border-slate-200 dark:bg-slate-800 dark:border-slate-700">
            <div className="font-semibold text-slate-900 dark:text-white">
              {selectedStudentForCorrection?.studentName} (
              {selectedStudentForCorrection?.rollNumber})
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">
              Course: {session.courseCode} • Date: {session.date}
            </div>
          </div>

          <div>
            <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
              Requested Corrected Status
            </label>
            <select
              value={requestedStatus}
              onChange={(e) =>
                setRequestedStatus(e.target.value as AttendanceStatus)
              }
              className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            >
              <option value="PRESENT">PRESENT</option>
              <option value="EXCUSED">EXCUSED (On-Duty / Medical)</option>
              <option value="LATE">LATE</option>
              <option value="ABSENT">ABSENT</option>
            </select>
          </div>

          <div>
            <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
              Justification / Reason
            </label>
            <textarea
              required
              rows={3}
              value={correctionReason}
              onChange={(e) => setCorrectionReason(e.target.value)}
              placeholder="e.g. Student was present in lecture hall; biometric card scanner failure verified by faculty."
              className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            />
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              onClick={() => setCorrectionModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={submittingCorrection}
            >
              {submittingCorrection ? "Submitting..." : "Submit for HOD Review"}
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
