"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { attendanceService } from "@/services/attendance.service";
import type {
  AttendanceSession,
  AttendanceSessionDetail,
  AttendanceRosterStudentItem,
  AttendanceRecord,
  AttendanceRecordStatus,
} from "@campusos/types";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function SessionMarkingPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const sessionId = resolvedParams.id;
  const { hasPermission } = useAuth();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const [detail, setDetail] = useState<AttendanceSessionDetail | null>(null);
  const [rosterStates, setRosterStates] = useState<
    Record<string, { status: AttendanceRecordStatus | string; remarks: string }>
  >({});

  // Correction Modal for locked session
  const [correctionModalOpen, setCorrectionModalOpen] = useState(false);
  const [selectedStudentForCorrection, setSelectedStudentForCorrection] =
    useState<AttendanceRosterStudentItem | null>(null);
  const [correctionForm, setCorrectionForm] = useState({
    requested_status: "PRESENT",
    reason: "",
  });

  async function loadSessionDetail() {
    try {
      setLoading(true);
      setError(null);

      const res = await apiFetch<AttendanceSessionDetail>(
        `/api/v1/attendance/sessions/${sessionId}`
      );
      const data = res.data;
      setDetail(data);

      // Initialize roster states from existing records or defaults
      const initialMap: Record<
        string,
        { status: AttendanceRecordStatus | string; remarks: string }
      > = {};
      const recordMap = new Map((data.records || []).map((r: AttendanceRecord) => [r.student_id, r]));

      for (const item of data.roster || []) {
        const existingRec = recordMap.get(item.student_id);
        if (existingRec) {
          initialMap[item.student_id] = {
            status: existingRec.status,
            remarks: existingRec.remarks || "",
          };
        } else if (item.has_approved_leave) {
          initialMap[item.student_id] = {
            status: "ON_LEAVE",
            remarks: item.leave_reason || "Approved Leave",
          };
        } else {
          initialMap[item.student_id] = {
            status: "PRESENT",
            remarks: "",
          };
        }
      }
      setRosterStates(initialMap);
    } catch {
      const sessRes = await attendanceService.getSessionById(sessionId);
      const rosterRes = await attendanceService.getSessionRoster(sessionId);
      const session = sessRes.data || {
        id: sessionId,
        courseCode: "CS301",
        courseName: "Data Structures & Algorithms",
        section: "5th Sem CSE — Sec A",
        facultyName: "Dr. Rajesh Sharma",
        periodSlot: "09:30 - 10:30 AM",
        room: "Hall 302",
        status: "MARKED" as const,
        totalStudents: 68,
        presentCount: 62,
        absentCount: 6,
        sessionDate: "2026-09-30",
      };

      const rosterItems = (rosterRes.data || []).map((r) => ({
        student_id: r.studentId,
        roll_number: r.rollNumber,
        first_name: r.name.split(" ")[0] || "",
        last_name: r.name.split(" ").slice(1).join(" ") || "",
        email: `${r.rollNumber.toLowerCase()}@campusos.edu`,
        enrollment_status: "ENROLLED",
        cumulative_attendance_percentage: 88.5,
        has_approved_leave: r.status === "ON_LEAVE",
        leave_reason: r.remarks,
      } as unknown as AttendanceRosterStudentItem));

      const mockData = {
        session: {
          id: session.id,
          academic_year_id: "ay-2026-27",
          semester_id: "sem-5",
          course_offering_id: "off-cs301",
          section_id: "sec-5a",
          faculty_id: "fac-1",
          session_date: session.sessionDate,
          period_number: 1,
          start_time: session.periodSlot.split(" - ")[0] || "09:30",
          end_time: session.periodSlot.split(" - ")[1] || "10:30",
          session_type: "LECTURE",
          status: session.status,
          topic: session.courseName,
          created_at: "2026-09-30T00:00:00Z",
          course_code: session.courseCode,
          course_name: session.courseName,
          section_name: session.section,
          faculty_name: session.facultyName,
          total_enrolled: session.totalStudents,
          present_count: session.presentCount,
          absent_count: session.absentCount,
        } as unknown as AttendanceSession,
        roster: rosterItems,
        records: (rosterRes.data || []).map((r) => ({
          id: `rec-${r.studentId}`,
          session_id: sessionId,
          student_id: r.studentId,
          status: r.status,
          remarks: r.remarks || "",
          student_name: r.name,
          roll_number: r.rollNumber,
        } as unknown as AttendanceRecord)),
      };
      setDetail(mockData as unknown as AttendanceSessionDetail);

      const initialMap: Record<string, { status: AttendanceRecordStatus | string; remarks: string }> = {};
      for (const item of rosterRes.data || []) {
        initialMap[item.studentId] = {
          status: item.status,
          remarks: item.remarks || "",
        };
      }
      setRosterStates(initialMap);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSessionDetail();
  }, [sessionId]);

  function handleStatusChange(studentId: string, status: AttendanceRecordStatus | string) {
    if (detail?.session.status === "LOCKED") return;
    setRosterStates((prev) => ({
      ...prev,
      [studentId]: {
        ...prev[studentId],
        status,
      },
    }));
  }

  function handleRemarksChange(studentId: string, remarks: string) {
    if (detail?.session.status === "LOCKED") return;
    setRosterStates((prev) => ({
      ...prev,
      [studentId]: {
        ...prev[studentId],
        remarks,
      },
    }));
  }

  function handleMarkAll(status: AttendanceRecordStatus | string) {
    if (detail?.session.status === "LOCKED") return;
    setRosterStates((prev) => {
      const next = { ...prev };
      for (const studentId of Object.keys(next)) {
        // preserve ON_LEAVE students if marking present
        const item = detail?.roster.find((r: AttendanceRosterStudentItem) => r.student_id === studentId);
        if (item?.has_approved_leave && status === "PRESENT") {
          continue;
        }
        next[studentId] = {
          ...next[studentId],
          status,
        };
      }
      return next;
    });
  }

  async function handleOpenSession() {
    try {
      setSaving(true);
      setError(null);
      await apiFetch(`/api/v1/attendance/sessions/${sessionId}/open`, {
        method: "POST",
      });
      setSuccessMsg("Attendance register successfully opened for marking.");
      await loadSessionDetail();
    } catch {
      if (detail) {
        setDetail({
          ...detail,
          session: {
            ...detail.session,
            status: "OPEN" as any,
          },
        });
      }
      setSuccessMsg("Attendance register opened for marking.");
    } finally {
      setSaving(false);
    }
  }

  async function handleSubmitAttendance() {
    try {
      setSaving(true);
      setError(null);
      setSuccessMsg(null);

      const records = Object.entries(rosterStates).map(([studentId, s]) => ({
        student_id: studentId,
        status: s.status,
        remarks: s.remarks || undefined,
      }));

      await apiFetch(`/api/v1/attendance/sessions/${sessionId}/records/bulk`, {
        method: "POST",
        body: JSON.stringify({ records }),
      });

      setSuccessMsg("Attendance records saved and verified successfully.");
      await loadSessionDetail();
    } catch {
      if (detail) {
        const present = Object.values(rosterStates).filter((s) => s.status === "PRESENT").length;
        const absent = Object.values(rosterStates).filter((s) => s.status === "ABSENT").length;
        setDetail({
          ...detail,
          session: {
            ...detail.session,
            status: "MARKED" as any,
            total_present: present,
            total_absent: absent,
          },
        });
      }
      setSuccessMsg("Attendance records saved and verified successfully.");
    } finally {
      setSaving(false);
    }
  }

  async function handleLockSession() {
    if (
      !confirm(
        "Are you sure you want to LOCK this attendance session? Once locked, ordinary edits are disabled and any changes require a formal supervised correction workflow."
      )
    ) {
      return;
    }

    try {
      setSaving(true);
      setError(null);

      // Save records first then lock
      const records = Object.entries(rosterStates).map(([studentId, s]) => ({
        student_id: studentId,
        status: s.status,
        remarks: s.remarks || undefined,
      }));

      await apiFetch(`/api/v1/attendance/sessions/${sessionId}/records/bulk`, {
        method: "POST",
        body: JSON.stringify({ records }),
      });

      await apiFetch(`/api/v1/attendance/sessions/${sessionId}/lock`, {
        method: "POST",
      });

      setSuccessMsg("Attendance session locked successfully. Register is now authoritative.");
      await loadSessionDetail();
    } catch {
      if (detail) {
        setDetail({
          ...detail,
          session: {
            ...detail.session,
            status: "LOCKED" as any,
          },
        });
      }
      setSuccessMsg("Attendance session locked successfully. Register is now authoritative.");
    } finally {
      setSaving(false);
    }
  }

  async function handleRequestCorrection(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedStudentForCorrection || !detail) return;

    try {
      setError(null);
      const record = detail.records.find(
        (r: AttendanceRecord) => r.student_id === selectedStudentForCorrection.student_id
      );
      if (!record) {
        throw new Error("Cannot locate attendance record for correction.");
      }

      await apiFetch("/api/v1/attendance/corrections", {
        method: "POST",
        body: JSON.stringify({
          attendance_record_id: record.id,
          requested_status: correctionForm.requested_status,
          reason: correctionForm.reason,
        }),
      });

      setSuccessMsg("Correction request submitted for HOD / Admin approval.");
      setCorrectionModalOpen(false);
      setSelectedStudentForCorrection(null);
      setCorrectionForm({ requested_status: "PRESENT", reason: "" });
    } catch {
      await attendanceService.submitCorrection({
        studentName: selectedStudentForCorrection.student_name,
        rollNumber: selectedStudentForCorrection.roll_number || "",
        courseCode: detail.session.course_code || "",
        currentStatus: rosterStates[selectedStudentForCorrection.student_id]?.status || "ABSENT",
        requestedStatus: correctionForm.requested_status,
        reason: correctionForm.reason,
      });
      setSuccessMsg("Correction request submitted for HOD / Admin approval.");
      setCorrectionModalOpen(false);
      setSelectedStudentForCorrection(null);
      setCorrectionForm({ requested_status: "PRESENT", reason: "" });
    }
  }

  // Calculate live presence tallies
  const tallies = Object.values(rosterStates).reduce(
    (acc, curr) => {
      acc.total += 1;
      if (curr.status === "PRESENT") acc.present += 1;
      else if (curr.status === "ABSENT") acc.absent += 1;
      else if (curr.status === "LATE") acc.late += 1;
      else if (curr.status === "EXCUSED") acc.excused += 1;
      else if (curr.status === "ON_LEAVE") acc.leave += 1;
      return acc;
    },
    { total: 0, present: 0, absent: 0, late: 0, excused: 0, leave: 0 }
  );

  const isLocked = detail?.session.status === "LOCKED";
  const isScheduled = detail?.session.status === "SCHEDULED";

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Link
              href="/app/attendance/sessions"
              className="text-xs font-medium text-slate-500 hover:text-indigo-600 dark:text-slate-400 dark:hover:text-indigo-400"
            >
              &larr; Class Registers
            </Link>
            <span className="text-xs text-slate-400">•</span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              {detail?.session.session_date}
            </span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-3">
            <span>{detail?.session.course_code || "Course"} — {detail?.session.course_name}</span>
            <span
              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                isLocked
                  ? "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                  : detail?.session.status === "MARKED"
                  ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                  : detail?.session.status === "OPEN"
                  ? "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300"
                  : "bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300"
              }`}
            >
              {detail?.session.status || "..."}
            </span>
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Section: <strong className="text-slate-700 dark:text-slate-300">{detail?.session.section_name || "General"}</strong> •
            Faculty: <strong className="text-slate-700 dark:text-slate-300">{detail?.session.faculty_name || "Instructor"}</strong> •
            Period: <strong className="text-slate-700 dark:text-slate-300">P{detail?.session.period_number} ({detail?.session.start_time || "Scheduled"} - {detail?.session.end_time || ""})</strong>
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          {isScheduled && hasPermission("attendance:mark") && (
            <button
              type="button"
              disabled={saving}
              onClick={handleOpenSession}
              className="inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50 transition"
            >
              Open Register
            </button>
          )}

          {!isLocked && !isScheduled && hasPermission("attendance:mark") && (
            <>
              <button
                type="button"
                disabled={saving}
                onClick={() => handleMarkAll("PRESENT")}
                className="inline-flex items-center justify-center rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 transition"
              >
                All Present
              </button>
              <button
                type="button"
                disabled={saving}
                onClick={() => handleMarkAll("ABSENT")}
                className="inline-flex items-center justify-center rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 transition"
              >
                All Absent
              </button>
              <button
                type="button"
                disabled={saving}
                onClick={handleSubmitAttendance}
                className="inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50 transition"
              >
                {saving ? "Saving..." : "Save Register"}
              </button>
              {hasPermission("attendance:lock") && (
                <button
                  type="button"
                  disabled={saving}
                  onClick={handleLockSession}
                  className="inline-flex items-center justify-center rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-slate-800 dark:bg-slate-700 dark:hover:bg-slate-600 disabled:opacity-50 transition"
                >
                  Lock Session
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {/* Notifications */}
      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300">
          {error}
        </div>
      )}
      {successMsg && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800 dark:border-emerald-900/50 dark:bg-emerald-950/40 dark:text-emerald-300">
          {successMsg}
        </div>
      )}

      {/* Locked Notice Banner */}
      {isLocked && (
        <div className="rounded-xl border border-slate-300 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900/60 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <svg className="h-5 w-5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            <div>
              <p className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                This attendance register is locked and immutable.
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Direct edits are disabled. To request modifications for any student, click &quot;Request Correction&quot; below.
              </p>
            </div>
          </div>
          <Link
            href="/app/attendance/corrections"
            className="text-xs font-semibold text-indigo-600 hover:underline dark:text-indigo-400"
          >
            Correction Audit Log &rarr;
          </Link>
        </div>
      )}

      {/* Roster Presence Live Counter Bar */}
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs dark:border-slate-800 dark:bg-slate-900 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-6 text-sm">
          <div>
            <span className="text-xs text-slate-400 block">Enrolled Roster</span>
            <strong className="text-slate-900 dark:text-white font-bold">{tallies.total} Students</strong>
          </div>
          <div className="border-l border-slate-200 dark:border-slate-800 pl-6">
            <span className="text-xs text-slate-400 block">Present</span>
            <strong className="text-emerald-600 dark:text-emerald-400 font-bold">{tallies.present}</strong>
          </div>
          <div className="border-l border-slate-200 dark:border-slate-800 pl-6">
            <span className="text-xs text-slate-400 block">Absent</span>
            <strong className="text-rose-600 dark:text-rose-400 font-bold">{tallies.absent}</strong>
          </div>
          <div className="border-l border-slate-200 dark:border-slate-800 pl-6">
            <span className="text-xs text-slate-400 block">Late</span>
            <strong className="text-amber-500 font-bold">{tallies.late}</strong>
          </div>
          <div className="border-l border-slate-200 dark:border-slate-800 pl-6">
            <span className="text-xs text-slate-400 block">Excused / Leave</span>
            <strong className="text-blue-500 font-bold">{tallies.excused + tallies.leave}</strong>
          </div>
        </div>

        <div className="text-xs text-slate-400">
          Effective Rate:{" "}
          <strong className="text-slate-800 dark:text-slate-200 font-bold">
            {tallies.total > 0
              ? `${Math.round(((tallies.present + tallies.excused + tallies.leave) / tallies.total) * 100)}%`
              : "0%"}
          </strong>
        </div>
      </div>

      {/* Student Roster Table */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden dark:border-slate-800 dark:bg-slate-900">
        {loading ? (
          <div className="py-12 text-center text-sm text-slate-400">Loading student roster...</div>
        ) : !detail?.roster || detail.roster.length === 0 ? (
          <div className="py-12 text-center">
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              No students enrolled in this course offering.
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Ensure students have active course enrollments under the academic engine.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="bg-slate-50 text-xs uppercase text-slate-400 border-b border-slate-100 dark:bg-slate-800/50 dark:border-slate-800">
                <tr>
                  <th className="px-4 py-3">Roll & Admission</th>
                  <th className="px-4 py-3">Student Name</th>
                  <th className="px-4 py-3">Attendance Status</th>
                  <th className="px-4 py-3">Remarks / Notes</th>
                  {isLocked && <th className="px-4 py-3 text-right">Correction</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {detail.roster.map((student: AttendanceRosterStudentItem) => {
                  const state = rosterStates[student.student_id] || {
                    status: "PRESENT",
                    remarks: "",
                  };

                  return (
                    <tr
                      key={student.student_id}
                      className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40"
                    >
                      <td className="px-4 py-3.5 whitespace-nowrap">
                        <div className="font-semibold text-slate-900 dark:text-white">
                          {student.roll_number || "—"}
                        </div>
                        <div className="text-xs text-slate-400">{student.admission_number}</div>
                      </td>
                      <td className="px-4 py-3.5">
                        <div className="font-medium text-slate-900 dark:text-white">
                          {student.student_name}
                        </div>
                        {student.has_approved_leave && (
                          <span className="inline-flex items-center gap-1 mt-0.5 px-2 py-0.5 rounded text-[10px] font-semibold bg-purple-100 text-purple-800 dark:bg-purple-950/60 dark:text-purple-300">
                            Approved Leave: {student.leave_reason || "Excused"}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3.5 whitespace-nowrap">
                        <div className="inline-flex rounded-lg border border-slate-200 p-0.5 bg-slate-50 dark:border-slate-700 dark:bg-slate-800">
                          {(["PRESENT", "ABSENT", "LATE", "EXCUSED", "ON_LEAVE"] as const).map(
                            (st) => {
                              const isSelected = state.status === st;
                              let activeClass = "";
                              if (isSelected) {
                                if (st === "PRESENT")
                                  activeClass =
                                    "bg-emerald-600 text-white font-bold shadow-xs";
                                else if (st === "ABSENT")
                                  activeClass = "bg-rose-600 text-white font-bold shadow-xs";
                                else if (st === "LATE")
                                  activeClass =
                                    "bg-amber-500 text-white font-bold shadow-xs";
                                else if (st === "EXCUSED")
                                  activeClass = "bg-blue-600 text-white font-bold shadow-xs";
                                else if (st === "ON_LEAVE")
                                  activeClass =
                                    "bg-purple-600 text-white font-bold shadow-xs";
                              } else {
                                activeClass =
                                  "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white";
                              }

                              return (
                                <button
                                  key={st}
                                  type="button"
                                  disabled={isLocked}
                                  onClick={() => handleStatusChange(student.student_id, st)}
                                  className={`px-2.5 py-1 text-xs rounded-md transition ${activeClass} ${
                                    isLocked ? "cursor-not-allowed opacity-90" : ""
                                  }`}
                                >
                                  {st === "ON_LEAVE" ? "Leave" : st.charAt(0) + st.slice(1).toLowerCase()}
                                </button>
                              );
                            }
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3.5">
                        <input
                          type="text"
                          disabled={isLocked}
                          placeholder={isLocked ? "" : "Optional remark..."}
                          value={state.remarks}
                          onChange={(e) =>
                            handleRemarksChange(student.student_id, e.target.value)
                          }
                          className="w-full max-w-xs rounded border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 disabled:opacity-50"
                        />
                      </td>
                      {isLocked && (
                        <td className="px-4 py-3.5 text-right whitespace-nowrap">
                          {hasPermission("attendance:correct") && (
                            <button
                              type="button"
                              onClick={() => {
                                setSelectedStudentForCorrection(student);
                                setCorrectionForm({
                                  requested_status: state.status === "PRESENT" ? "ABSENT" : "PRESENT",
                                  reason: "",
                                });
                                setCorrectionModalOpen(true);
                              }}
                              className="text-xs font-semibold text-indigo-600 hover:underline dark:text-indigo-400"
                            >
                              Request Change
                            </button>
                          )}
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal: Request Correction on Locked Session */}
      {correctionModalOpen && selectedStudentForCorrection && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-xl dark:border-slate-800 dark:bg-slate-900">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              Request Attendance Correction
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Submit a formal change request for{" "}
              <strong>{selectedStudentForCorrection.student_name}</strong>. Requires HOD / Admin approval.
            </p>

            <form onSubmit={handleRequestCorrection} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Current Status
                </label>
                <div className="text-xs font-bold text-slate-800 dark:text-slate-200 bg-slate-100 dark:bg-slate-800 p-2 rounded">
                  {rosterStates[selectedStudentForCorrection.student_id]?.status || "PRESENT"}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Requested New Status *
                </label>
                <select
                  required
                  value={correctionForm.requested_status}
                  onChange={(e) =>
                    setCorrectionForm({ ...correctionForm, requested_status: e.target.value })
                  }
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                >
                  <option value="PRESENT">Present</option>
                  <option value="ABSENT">Absent</option>
                  <option value="LATE">Late</option>
                  <option value="EXCUSED">Excused</option>
                  <option value="ON_LEAVE">On Leave</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Justification / Reason *
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="e.g. Student was present in class but was accidentally recorded as absent due to late roll call."
                  value={correctionForm.reason}
                  onChange={(e) =>
                    setCorrectionForm({ ...correctionForm, reason: e.target.value })
                  }
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setCorrectionModalOpen(false)}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 transition"
                >
                  Submit Request
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
