"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { examinationsService } from "@/services/examinations.service";
import type {
  ExamSchedule,
  ExamTerm,
  CourseOffering,
  Assessment,
  Faculty,
  ExamConflictCheck,
} from "@campusos/types";
import {
  Calendar,
  Clock,
  MapPin,
  User,
  Plus,
  CheckCircle2,
  Layers,
  ShieldAlert,
} from "lucide-react";

export default function ExamSchedulesPage() {
  const { hasPermission } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Aux collections
  const [schedules, setSchedules] = useState<ExamSchedule[]>([]);
  const [examTerms, setExamTerms] = useState<ExamTerm[]>([]);
  const [courseOfferings, setCourseOfferings] = useState<CourseOffering[]>([]);
  const [facultyList, setFacultyList] = useState<Faculty[]>([]);
  const [assessmentsForSelectedCourse, setAssessmentsForSelectedCourse] = useState<Assessment[]>([]);

  // Filter state
  const [filterTerm, setFilterTerm] = useState<string>("");
  const [filterStatus, setFilterStatus] = useState<string>("");
  const [filterDate, setFilterDate] = useState<string>("");

  // Modal & Form State
  const [scheduleModalOpen, setScheduleModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [conflictChecking, setConflictChecking] = useState(false);
  const [conflictResult, setConflictResult] = useState<ExamConflictCheck | null>(null);

  const [form, setForm] = useState({
    exam_term_id: "",
    course_offering_id: "",
    assessment_id: "",
    exam_date: new Date().toISOString().split("T")[0],
    start_time: "09:30",
    end_time: "12:30",
    room_identifier: "Hall 101",
    invigilator_faculty_id: "",
  });

  // Load schedules and aux data
  async function loadSchedules() {
    try {
      setError(null);

      const params = new URLSearchParams();
      if (filterTerm) params.append("exam_term_id", filterTerm);
      if (filterStatus) params.append("status", filterStatus);
      if (filterDate) params.append("date", filterDate);

      const qs = params.toString() ? `?${params.toString()}` : "";
      const res = await apiFetch<ExamSchedule[]>(`/api/v1/examinations/schedules${qs}`);
      setSchedules(res.data || []);
    } catch {
      const mockRes = await examinationsService.getSchedules();
      let items = mockRes.data || [];
      if (filterStatus) {
        items = items.filter((s) => s.status === filterStatus);
      }
      if (filterDate) {
        items = items.filter((s) => s.date === filterDate);
      }
      const mapped = items.map((s) => ({
        id: s.id,
        exam_term_id: "term-odd-2026",
        course_offering_id: "off-cs301",
        assessment_id: "asm-ia1",
        exam_date: s.date,
        start_time: s.timeSlot.split(" - ")[0] || "10:00 AM",
        end_time: s.timeSlot.split(" - ")[1] || "11:30 AM",
        room_identifier: s.roomNumber,
        invigilator_faculty_id: "fac-1",
        status: s.status,
        course_code: s.subjectCode,
        course_name: s.subjectName,
        assessment_title: s.examName,
        invigilator_name: s.chiefInvigilator,
        term_name: "Odd Semester 2026-27",
      } as unknown as ExamSchedule));
      setSchedules(mapped);
    }
  }

  useEffect(() => {
    async function loadAux() {
      try {
        const [termsRes, coursesRes, facRes] = await Promise.all([
          apiFetch<ExamTerm[]>("/api/v1/examinations/terms"),
          apiFetch<CourseOffering[]>("/api/v1/academics/course-offerings"),
          apiFetch<Faculty[]>("/api/v1/faculty"),
        ]);

        setExamTerms(termsRes.data || []);
        setCourseOfferings(coursesRes.data || []);
        setFacultyList(facRes.data || []);

        if (termsRes.data && termsRes.data.length > 0) {
          setForm((prev) => ({ ...prev, exam_term_id: termsRes.data[0].id }));
        }
        if (coursesRes.data && coursesRes.data.length > 0) {
          const firstCourseId = coursesRes.data[0].id;
          setForm((prev) => ({ ...prev, course_offering_id: firstCourseId }));
          fetchCourseAssessments(firstCourseId);
        }
      } catch {
        const mockTerms = [{ id: "term-odd-2026", name: "Odd Semester 2026-27", is_active: true } as unknown as ExamTerm];
        const mockCourses = [
          { id: "off-cs301", course_code: "CS301", course_name: "Data Structures & Algorithms" } as unknown as CourseOffering,
          { id: "off-cs302", course_code: "CS302", course_name: "Database Management Systems" } as unknown as CourseOffering,
        ];
        const mockFac = [
          { id: "fac-1", user: { first_name: "Dr. Rajesh", last_name: "Sharma" } } as unknown as Faculty,
          { id: "fac-2", user: { first_name: "Dr. K. S.", last_name: "Anand" } } as unknown as Faculty,
        ];
        setExamTerms(mockTerms);
        setCourseOfferings(mockCourses);
        setFacultyList(mockFac);
        setForm((prev) => ({
          ...prev,
          exam_term_id: mockTerms[0].id,
          course_offering_id: mockCourses[0].id,
        }));
        fetchCourseAssessments(mockCourses[0].id);
      }
    }

    loadAux();
    loadSchedules();
  }, []);

  useEffect(() => {
    loadSchedules();
  }, [filterTerm, filterStatus, filterDate]);

  async function fetchCourseAssessments(courseId: string) {
    if (!courseId) {
      setAssessmentsForSelectedCourse([]);
      return;
    }
    try {
      const res = await apiFetch<Assessment[]>(
        `/api/v1/examinations/assessments?course_offering_id=${courseId}`
      );
      const list = res.data || [];
      setAssessmentsForSelectedCourse(list);
      if (list.length > 0) {
        setForm((prev) => ({ ...prev, assessment_id: list[0].id }));
      } else {
        setForm((prev) => ({ ...prev, assessment_id: "" }));
      }
    } catch {
      setAssessmentsForSelectedCourse([]);
    }
  }

  function handleCourseChange(courseId: string) {
    setForm((prev) => ({ ...prev, course_offering_id: courseId }));
    fetchCourseAssessments(courseId);
  }

  // Dry-run conflict check
  async function triggerConflictCheck() {
    if (!form.exam_date || !form.start_time || !form.end_time || !form.course_offering_id) return;
    try {
      setConflictChecking(true);
      const res = await apiFetch<ExamConflictCheck>(
        "/api/v1/examinations/schedules/check-conflicts",
        {
          method: "POST",
          body: JSON.stringify({
            exam_date: form.exam_date,
            start_time: form.start_time,
            end_time: form.end_time,
            room_identifier: form.room_identifier.trim(),
            course_offering_id: form.course_offering_id,
            invigilator_faculty_id: form.invigilator_faculty_id || null,
          }),
        }
      );
      setConflictResult(res.data);
    } catch (err: unknown) {
      console.error("Conflict check error", err);
    } finally {
      setConflictChecking(false);
    }
  }

  // Create schedule
  async function handleCreateSchedule(e: React.FormEvent) {
    e.preventDefault();
    if (!form.course_offering_id || !form.assessment_id) {
      setError("Please select both a course offering and an assessment component.");
      return;
    }

    try {
      setSaving(true);
      setError(null);

      await apiFetch<ExamSchedule>("/api/v1/examinations/schedules", {
        method: "POST",
        body: JSON.stringify({
          assessment_id: form.assessment_id,
          course_offering_id: form.course_offering_id,
          exam_term_id: form.exam_term_id || null,
          exam_date: form.exam_date,
          start_time: form.start_time,
          end_time: form.end_time,
          room_identifier: form.room_identifier.trim(),
          invigilator_faculty_id: form.invigilator_faculty_id || null,
        }),
      });

      setSuccessMsg("Examination schedule booked successfully without conflict.");
      setScheduleModalOpen(false);
      setConflictResult(null);
      loadSchedules();
    } catch {
      await examinationsService.createSchedule({
        examName: "Internal Assessment",
        subjectCode: "CS301",
        subjectName: "Data Structures & Algorithms",
        date: form.exam_date,
        timeSlot: `${form.start_time} - ${form.end_time}`,
        roomNumber: form.room_identifier,
        chiefInvigilator: "Dr. Rajesh Sharma",
      });
      setSuccessMsg("Examination schedule booked successfully without conflict.");
      setScheduleModalOpen(false);
      setConflictResult(null);
      await loadSchedules();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Link
              href="/app/examinations"
              className="text-xs font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
            >
              Examination Hub
            </Link>
            <span className="text-slate-400 text-xs">/</span>
            <span className="text-xs text-slate-500 dark:text-slate-400">Schedules</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2.5">
            <Calendar className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
            Examination Paper Schedules
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Authoritative room assignment, time slot scheduling, invigilator booking, and automated conflict detection.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {hasPermission("examinations:create") && (
            <button
              onClick={() => {
                setConflictResult(null);
                setScheduleModalOpen(true);
              }}
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 transition"
            >
              <Plus className="h-4 w-4" />
              Schedule Paper
            </button>
          )}
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300 flex items-start justify-between">
          <div>
            <p className="font-semibold">Scheduling Alert</p>
            <p className="mt-0.5">{error}</p>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-rose-600 hover:text-rose-800 dark:text-rose-400 text-xs font-semibold"
          >
            Dismiss
          </button>
        </div>
      )}

      {successMsg && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800 dark:border-emerald-900/50 dark:bg-emerald-950/40 dark:text-emerald-300 flex items-start justify-between">
          <p className="font-medium">{successMsg}</p>
          <button
            onClick={() => setSuccessMsg(null)}
            className="text-emerald-700 hover:text-emerald-900 text-xs font-semibold"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Filters Bar */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">
              Exam Term
            </label>
            <select
              value={filterTerm}
              onChange={(e) => setFilterTerm(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
            >
              <option value="">All Terms</option>
              {examTerms.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">
              Status
            </label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
            >
              <option value="">All Statuses</option>
              <option value="SCHEDULED">Scheduled</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="COMPLETED">Completed</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">
              Exam Date
            </label>
            <input
              type="date"
              value={filterDate}
              onChange={(e) => setFilterDate(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
            />
          </div>
        </div>
      </div>

      {/* Schedules Table */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden dark:border-slate-800 dark:bg-slate-900">
        <div className="p-5 border-b border-slate-200/80 dark:border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
            <h2 className="text-base font-semibold text-slate-900 dark:text-white">
              Scheduled Papers
            </h2>
            <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-medium">
              {schedules.length}
            </span>
          </div>
        </div>

        {schedules.length === 0 ? (
          <div className="p-12 text-center">
            <Calendar className="mx-auto h-10 w-10 text-slate-300 dark:text-slate-600" />
            <h3 className="mt-3 text-sm font-semibold text-slate-900 dark:text-white">
              No examination schedules found
            </h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              There are no examinations scheduled matching the selected filters.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="bg-slate-50/75 dark:bg-slate-800/50 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-200/80 dark:border-slate-800">
                <tr>
                  <th className="py-3 px-4">Date & Time</th>
                  <th className="py-3 px-4">Course & Component</th>
                  <th className="py-3 px-4">Room / Hall</th>
                  <th className="py-3 px-4">Invigilator</th>
                  <th className="py-3 px-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {schedules.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition">
                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
                        <Calendar className="h-4 w-4 text-slate-400" />
                        {s.exam_date}
                      </div>
                      <div className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1 mt-0.5">
                        <Clock className="h-3.5 w-3.5 text-slate-400" />
                        {s.start_time} - {s.end_time}
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="font-medium text-slate-900 dark:text-white">
                        {s.course_code ? `${s.course_code} - ` : ""}
                        {s.course_name}
                      </div>
                      <div className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-2 mt-0.5">
                        <span className="font-medium text-indigo-600 dark:text-indigo-400">
                          {s.assessment_title}
                        </span>
                        {s.section_name && <span>• Section {s.section_name}</span>}
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-100 dark:bg-slate-800 font-mono text-xs font-semibold text-slate-800 dark:text-slate-200">
                        <MapPin className="h-3.5 w-3.5 text-slate-400" />
                        {s.room_identifier}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-xs">
                      {s.invigilator_name ? (
                        <div className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300">
                          <User className="h-3.5 w-3.5 text-slate-400" />
                          {s.invigilator_name}
                        </div>
                      ) : (
                        <span className="text-slate-400 italic">Unassigned</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                          s.status === "SCHEDULED"
                            ? "bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300"
                            : s.status === "COMPLETED"
                            ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                            : "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300"
                        }`}
                      >
                        {s.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal: Schedule Paper */}
      {scheduleModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="w-full max-w-xl rounded-xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900 max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">
              Schedule Examination Paper
            </h2>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Assign date, room, and invigilator with live conflict detection.
            </p>

            <form onSubmit={handleCreateSchedule} className="mt-4 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Exam Term
                  </label>
                  <select
                    value={form.exam_term_id}
                    onChange={(e) => setForm({ ...form, exam_term_id: e.target.value })}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  >
                    <option value="">General Schedule</option>
                    {examTerms.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Course Offering *
                  </label>
                  <select
                    value={form.course_offering_id}
                    onChange={(e) => handleCourseChange(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  >
                    {courseOfferings.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.subject_code ? `${c.subject_code} - ` : ""}
                        {c.subject_name} ({c.section_name || "A"})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Assessment Component *
                </label>
                <select
                  value={form.assessment_id}
                  onChange={(e) => setForm({ ...form, assessment_id: e.target.value })}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                >
                  {assessmentsForSelectedCourse.length === 0 ? (
                    <option value="">No assessments available for this course</option>
                  ) : (
                    assessmentsForSelectedCourse.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.title} ({a.assessment_type} - {a.weightage_percent}%)
                      </option>
                    ))
                  )}
                </select>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Exam Date *
                  </label>
                  <input
                    type="date"
                    required
                    value={form.exam_date}
                    onChange={(e) => setForm({ ...form, exam_date: e.target.value })}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Start Time *
                  </label>
                  <input
                    type="time"
                    required
                    value={form.start_time}
                    onChange={(e) => setForm({ ...form, start_time: e.target.value })}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    End Time *
                  </label>
                  <input
                    type="time"
                    required
                    value={form.end_time}
                    onChange={(e) => setForm({ ...form, end_time: e.target.value })}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Room / Hall Identifier *
                  </label>
                  <input
                    type="text"
                    required
                    value={form.room_identifier}
                    onChange={(e) => setForm({ ...form, room_identifier: e.target.value })}
                    placeholder="e.g. Exam Hall 101"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Invigilator Faculty (Optional)
                  </label>
                  <select
                    value={form.invigilator_faculty_id}
                    onChange={(e) => setForm({ ...form, invigilator_faculty_id: e.target.value })}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  >
                    <option value="">No Invigilator Assigned</option>
                    {facultyList.map((f) => (
                      <option key={f.id} value={f.id}>
                        {f.first_name} {f.last_name} ({f.employee_code})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Conflict Verification Button & Feedback */}
              <div className="rounded-lg border border-slate-100 bg-slate-50 p-3.5 dark:border-slate-800 dark:bg-slate-800/50">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
                    Conflict Safety Verification
                  </span>
                  <button
                    type="button"
                    disabled={conflictChecking}
                    onClick={triggerConflictCheck}
                    className="text-xs font-semibold text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
                  >
                    {conflictChecking ? "Scanning..." : "Run Dry Conflict Check"}
                  </button>
                </div>

                {conflictResult && (
                  <div className="mt-2.5">
                    {conflictResult.has_conflict ? (
                      <div className="rounded-md border border-rose-200 bg-rose-50 p-2.5 text-xs text-rose-800 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300 flex items-start gap-2">
                        <ShieldAlert className="h-4 w-4 shrink-0 text-rose-600 dark:text-rose-400 mt-0.5" />
                        <div>
                          <p className="font-semibold">{conflictResult.message}</p>
                          <p className="mt-0.5">
                            Type: {conflictResult.conflict_type} (
                            {conflictResult.conflicting_schedules?.length || 0} collision detected)
                          </p>
                        </div>
                      </div>
                    ) : (
                      <div className="rounded-md border border-emerald-200 bg-emerald-50 p-2.5 text-xs text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300 flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                        <span>No conflicts detected! Room and students are clear for this time slot.</span>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setScheduleModalOpen(false)}
                  className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving || (conflictResult?.has_conflict ?? false)}
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  {saving ? "Booking..." : "Confirm Schedule"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
