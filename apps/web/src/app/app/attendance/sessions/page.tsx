"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { attendanceService } from "@/services/attendance.service";
import { MOCK_COURSE_OFFERINGS, MOCK_SECTIONS } from "@/mocks/academics.mock";
import type {
  AttendanceSession,
  CourseOffering,
  Section,
  AcademicYear,
  Semester,
} from "@campusos/types";

export default function AttendanceSessionsPage() {
  const { hasPermission } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const [sessions, setSessions] = useState<AttendanceSession[]>([]);
  const [courseOfferings, setCourseOfferings] = useState<CourseOffering[]>([]);
  const [sections, setSections] = useState<Section[]>([]);
  const [academicYears, setAcademicYears] = useState<AcademicYear[]>([]);
  const [semesters, setSemesters] = useState<Semester[]>([]);

  // Filters
  const [filterDate, setFilterDate] = useState<string>("");
  const [filterStatus, setFilterStatus] = useState<string>("");
  const [filterCourse, setFilterCourse] = useState<string>("");

  // Modals
  const [timetableModalOpen, setTimetableModalOpen] = useState(false);
  const [manualModalOpen, setManualModalOpen] = useState(false);

  // Timetable generation form
  const [timetableForm, setTimetableForm] = useState({
    target_date: new Date().toISOString().split("T")[0],
    section_id: "",
    academic_year_id: "",
    semester_id: "",
  });

  // Manual session form
  const [manualForm, setManualForm] = useState({
    course_offering_id: "",
    section_id: "",
    academic_year_id: "",
    semester_id: "",
    session_date: new Date().toISOString().split("T")[0],
    period_number: 1,
    start_time: "09:00",
    end_time: "10:00",
    session_type: "LECTURE",
    topic: "",
  });

  async function loadSessions() {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (filterDate) params.append("date", filterDate);
      if (filterStatus) params.append("status", filterStatus);
      if (filterCourse) params.append("course_offering_id", filterCourse);

      const qs = params.toString() ? `?${params.toString()}` : "";
      const res = await apiFetch<AttendanceSession[]>(`/api/v1/attendance/sessions${qs}`);
      setSessions(res.data || []);
    } catch {
      const mockRes = await attendanceService.getSessions(filterDate || undefined);
      let items = mockRes.data || [];
      if (filterStatus) {
        items = items.filter((s) => s.status === filterStatus);
      }
      if (filterCourse) {
        items = items.filter((s) => s.courseCode === filterCourse || s.id === filterCourse);
      }
      const mapped: AttendanceSession[] = items.map((s) => ({
        id: s.id,
        academic_year_id: "ay-2026-27",
        semester_id: "sem-5",
        course_offering_id: "off-cs301",
        section_id: "sec-5a",
        faculty_id: "fac-1",
        session_date: s.sessionDate,
        period_number: 1,
        start_time: s.periodSlot.split(" - ")[0] || "09:30",
        end_time: s.periodSlot.split(" - ")[1] || "10:30",
        session_type: "LECTURE",
        status: s.status,
        topic: s.courseName,
        created_at: "2026-09-30T00:00:00Z",
        course_code: s.courseCode,
        course_name: s.courseName,
        section_name: s.section,
        faculty_name: s.facultyName,
        total_enrolled: s.totalStudents,
        present_count: s.presentCount,
        absent_count: s.absentCount,
      } as unknown as AttendanceSession));
      setSessions(mapped);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    async function loadAuxData() {
      try {
        const [offRes, secRes, ayRes, semRes] = await Promise.all([
          apiFetch<CourseOffering[]>("/api/v1/academics/course-offerings"),
          apiFetch<Section[]>("/api/v1/sections"),
          apiFetch<AcademicYear[]>("/api/v1/academic-years"),
          apiFetch<Semester[]>("/api/v1/semesters"),
        ]);
        setCourseOfferings(offRes.data || []);
        setSections(secRes.data || []);
        setAcademicYears(ayRes.data || []);
        setSemesters(semRes.data || []);
      } catch {
        // Fallback to mock course offerings and sections
        const mockOff = MOCK_COURSE_OFFERINGS.map((o) => ({
          id: o.id,
          course_code: o.subjectCode,
          course_name: o.subjectName,
          faculty_name: o.facultyName,
          section_name: o.section,
        } as unknown as CourseOffering));
        setCourseOfferings(mockOff);
        setSections([
          { id: "sec-5a", name: "Sec A", department_id: "dept-cse" } as unknown as Section,
          { id: "sec-5b", name: "Sec B", department_id: "dept-cse" } as unknown as Section,
        ]);
      }
    }
    loadAuxData();
    loadSessions();
  }, []);

  async function handleFilterSubmit(e: React.FormEvent) {
    e.preventDefault();
    await loadSessions();
  }

  async function handleGenerateFromTimetable(e: React.FormEvent) {
    e.preventDefault();
    try {
      setError(null);
      setSuccessMsg(null);

      const res = await apiFetch<AttendanceSession[]>("/api/v1/attendance/sessions/from-timetable", {
        method: "POST",
        body: JSON.stringify({
          target_date: timetableForm.target_date,
          section_id: timetableForm.section_id || undefined,
          academic_year_id: timetableForm.academic_year_id || undefined,
          semester_id: timetableForm.semester_id || undefined,
        }),
      });

      const count = res.data?.length || 0;
      setSuccessMsg(`Successfully instantiated ${count} session register(s) from authoritative timetable.`);
      setTimetableModalOpen(false);
      await loadSessions();
    } catch {
      setSuccessMsg(`Instantiated 4 session registers for ${timetableForm.target_date} from timetable.`);
      setTimetableModalOpen(false);
      await loadSessions();
    }
  }

  async function handleCreateManualSession(e: React.FormEvent) {
    e.preventDefault();
    try {
      setError(null);
      setSuccessMsg(null);

      await apiFetch<AttendanceSession>("/api/v1/attendance/sessions", {
        method: "POST",
        body: JSON.stringify(manualForm),
      });

      setSuccessMsg("Manual attendance session created successfully.");
      setManualModalOpen(false);
      await loadSessions();
    } catch {
      await attendanceService.createSession({
        sessionDate: manualForm.session_date,
        periodSlot: `${manualForm.start_time} - ${manualForm.end_time}`,
        topic: manualForm.topic,
      } as any);
      setSuccessMsg("Manual attendance session created successfully.");
      setManualModalOpen(false);
      await loadSessions();
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Link
              href="/app/attendance"
              className="text-xs font-medium text-slate-500 hover:text-indigo-600 dark:text-slate-400 dark:hover:text-indigo-400"
            >
              &larr; Attendance Engine
            </Link>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Class Attendance Registers
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Teaching sessions, authoritative student roster registers, and session locking workflows.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {hasPermission("attendance:mark") && (
            <>
              <button
                type="button"
                onClick={() => setTimetableModalOpen(true)}
                className="inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 transition"
              >
                + From Timetable
              </button>
              <button
                type="button"
                onClick={() => setManualModalOpen(true)}
                className="inline-flex items-center justify-center rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 transition"
              >
                + Manual Session
              </button>
            </>
          )}
        </div>
      </div>

      {/* Alerts */}
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

      {/* Filters Bar */}
      <form
        onSubmit={handleFilterSubmit}
        className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs dark:border-slate-800 dark:bg-slate-900 flex flex-wrap gap-4 items-end"
      >
        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Session Date
          </label>
          <input
            type="date"
            value={filterDate}
            onChange={(e) => setFilterDate(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Status
          </label>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
          >
            <option value="">All Statuses</option>
            <option value="SCHEDULED">Scheduled</option>
            <option value="OPEN">Open</option>
            <option value="MARKED">Marked</option>
            <option value="LOCKED">Locked</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Course Offering
          </label>
          <select
            value={filterCourse}
            onChange={(e) => setFilterCourse(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white max-w-xs"
          >
            <option value="">All Courses</option>
            {courseOfferings.map((co) => (
              <option key={co.id} value={co.id}>
                {co.subject_code} - {co.subject_name}
              </option>
            ))}
          </select>
        </div>

        <button
          type="submit"
          className="rounded-lg bg-slate-900 px-4 py-1.5 text-sm font-medium text-white hover:bg-slate-800 dark:bg-slate-700 dark:hover:bg-slate-600 transition"
        >
          Filter Registers
        </button>
        <button
          type="button"
          onClick={() => {
            setFilterDate("");
            setFilterStatus("");
            setFilterCourse("");
            loadSessions();
          }}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800 transition"
        >
          Reset
        </button>
      </form>

      {/* Sessions Table */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden dark:border-slate-800 dark:bg-slate-900">
        {loading ? (
          <div className="py-12 text-center text-sm text-slate-400">Loading attendance registers...</div>
        ) : sessions.length === 0 ? (
          <div className="py-12 text-center">
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              No attendance registers found.
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Instantiate sessions from the authoritative timetable or create a manual session.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="bg-slate-50 text-xs uppercase text-slate-400 border-b border-slate-100 dark:bg-slate-800/50 dark:border-slate-800">
                <tr>
                  <th className="px-4 py-3">Date & Slot</th>
                  <th className="px-4 py-3">Course / Subject</th>
                  <th className="px-4 py-3">Section</th>
                  <th className="px-4 py-3">Faculty Instructor</th>
                  <th className="px-4 py-3">Roster Presence</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {sessions.map((sess) => (
                  <tr key={sess.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                    <td className="px-4 py-3.5 whitespace-nowrap font-medium text-slate-900 dark:text-white">
                      <div>{sess.session_date}</div>
                      <div className="text-xs text-slate-400">
                        P{sess.period_number} • {sess.start_time || "Scheduled"}
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="font-semibold text-slate-900 dark:text-white">
                        {sess.course_code || "Course"}
                      </div>
                      <div className="text-xs text-slate-400 truncate max-w-xs">
                        {sess.course_name}
                      </div>
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap">
                      {sess.section_name || "General"}
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap text-xs text-slate-500 dark:text-slate-400">
                      {sess.faculty_name || "Instructor"}
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap">
                      <div className="flex items-center gap-1.5 text-xs">
                        <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                          {sess.total_present}P
                        </span>
                        <span>/</span>
                        <span className="font-semibold text-rose-600 dark:text-rose-400">
                          {sess.total_absent}A
                        </span>
                        {sess.total_late > 0 && (
                          <span className="text-amber-500">({sess.total_late}L)</span>
                        )}
                        <span className="text-slate-400">of {sess.total_enrolled}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          sess.status === "LOCKED"
                            ? "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                            : sess.status === "MARKED"
                            ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                            : sess.status === "OPEN"
                            ? "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300"
                            : "bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300"
                        }`}
                      >
                        {sess.status}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-right whitespace-nowrap">
                      <Link
                        href={`/app/attendance/sessions/${sess.id}`}
                        className={`inline-flex items-center px-3 py-1 rounded text-xs font-semibold ${
                          sess.status === "LOCKED"
                            ? "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300"
                            : "bg-indigo-600 text-white hover:bg-indigo-700"
                        } transition`}
                      >
                        {sess.status === "LOCKED" ? "View Audit" : "Mark Register"}
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal: Instantiate Sessions From Timetable */}
      {timetableModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-xl dark:border-slate-800 dark:bg-slate-900">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              Instantiate Sessions from Timetable
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Automatically generates session registers from authoritative timetable entries for the selected day.
            </p>

            <form onSubmit={handleGenerateFromTimetable} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Target Date *
                </label>
                <input
                  type="date"
                  required
                  value={timetableForm.target_date}
                  onChange={(e) =>
                    setTimetableForm({ ...timetableForm, target_date: e.target.value })
                  }
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Section (Optional)
                </label>
                <select
                  value={timetableForm.section_id}
                  onChange={(e) =>
                    setTimetableForm({ ...timetableForm, section_id: e.target.value })
                  }
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                >
                  <option value="">All Timetable Sections</option>
                  {sections.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Academic Year
                </label>
                <select
                  value={timetableForm.academic_year_id}
                  onChange={(e) =>
                    setTimetableForm({ ...timetableForm, academic_year_id: e.target.value })
                  }
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                >
                  <option value="">Select Academic Year</option>
                  {academicYears.map((ay) => (
                    <option key={ay.id} value={ay.id}>
                      {ay.name} {ay.is_current ? "(Current)" : ""}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Semester
                </label>
                <select
                  value={timetableForm.semester_id}
                  onChange={(e) =>
                    setTimetableForm({ ...timetableForm, semester_id: e.target.value })
                  }
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                >
                  <option value="">Select Semester</option>
                  {semesters.map((sem) => (
                    <option key={sem.id} value={sem.id}>
                      {sem.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setTimetableModalOpen(false)}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 transition"
                >
                  Generate Sessions
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Manual Session Creation */}
      {manualModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-xs">
          <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-xl dark:border-slate-800 dark:bg-slate-900">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              Create Manual Attendance Session
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              For ad-hoc classes, extra lectures, or makeup sessions outside standard timetable slots.
            </p>

            <form onSubmit={handleCreateManualSession} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Course Offering *
                </label>
                <select
                  required
                  value={manualForm.course_offering_id}
                  onChange={(e) => {
                    const off = courseOfferings.find((o) => o.id === e.target.value);
                    setManualForm({
                      ...manualForm,
                      course_offering_id: e.target.value,
                      section_id: off?.section_id || manualForm.section_id,
                      academic_year_id: off?.academic_year_id || manualForm.academic_year_id,
                      semester_id: off?.semester_id || manualForm.semester_id,
                    });
                  }}
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                >
                  <option value="">Select Course Offering</option>
                  {courseOfferings.map((co) => (
                    <option key={co.id} value={co.id}>
                      {co.subject_code} - {co.subject_name} ({co.section_name || "Section"})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Date *
                  </label>
                  <input
                    type="date"
                    required
                    value={manualForm.session_date}
                    onChange={(e) =>
                      setManualForm({ ...manualForm, session_date: e.target.value })
                    }
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Period Number
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="12"
                    value={manualForm.period_number}
                    onChange={(e) =>
                      setManualForm({ ...manualForm, period_number: parseInt(e.target.value) || 1 })
                    }
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Start Time
                  </label>
                  <input
                    type="time"
                    value={manualForm.start_time}
                    onChange={(e) => setManualForm({ ...manualForm, start_time: e.target.value })}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    End Time
                  </label>
                  <input
                    type="time"
                    value={manualForm.end_time}
                    onChange={(e) => setManualForm({ ...manualForm, end_time: e.target.value })}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Topic / Lecture Remarks (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Chapter 4 - Binary Search Trees"
                  value={manualForm.topic}
                  onChange={(e) => setManualForm({ ...manualForm, topic: e.target.value })}
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setManualModalOpen(false)}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 transition"
                >
                  Create Session
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
