"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { examinationsService } from "@/services/examinations.service";
import {
  ExamSchedule,
  Examination,
  ExamConflictCheck,
  ExamScheduleStatus,
} from "@/types/examinations";
import { DataGrid } from "@/components/data-grid/data-grid";
import { ColumnDef } from "@/components/data-grid/data-grid.types";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { useToast } from "@/components/ui/toast";
import {
  Calendar,
  Clock,
  MapPin,
  User,
  Plus,
  Filter,
  AlertTriangle,
  CheckCircle2,
  Layers,
  ArrowRight,
  ShieldAlert,
} from "lucide-react";

export default function ExamSchedulesPage() {
  const { hasPermission } = useAuth();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [schedules, setSchedules] = useState<ExamSchedule[]>([]);
  const [examinations, setExaminations] = useState<Examination[]>([]);
  const [selectedExam, setSelectedExam] = useState<string>("ALL");
  const [selectedDept, setSelectedDept] = useState<string>("ALL");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");

  // Multi-step Scheduling Modal Wizard
  const [modalOpen, setModalOpen] = useState(false);
  const [step, setStep] = useState(1);
  const [saving, setSaving] = useState(false);

  // Wizard state
  const [examId, setExamId] = useState("exam-2026-ese");
  const [courseOfferingId, setCourseOfferingId] = useState("co-cs301-a");
  const [date, setDate] = useState("2026-11-25");
  const [startTime, setStartTime] = useState("10:00 AM");
  const [endTime, setEndTime] = useState("01:00 PM");
  const [room, setRoom] = useState("CS-LH-201");
  const [facultyId, setFacultyId] = useState("fac-001");
  const [invigilatorNotes, setInvigilatorNotes] = useState("");

  // Conflict Check State
  const [conflictChecking, setConflictChecking] = useState(false);
  const [conflictResult, setConflictResult] = useState<ExamConflictCheck | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [schRes, examRes] = await Promise.all([
        examinationsService.getSchedules({
          examinationId: selectedExam !== "ALL" ? selectedExam : undefined,
          department: selectedDept !== "ALL" ? selectedDept : undefined,
          status: selectedStatus !== "ALL" ? selectedStatus : undefined,
        }),
        examinationsService.getExaminations(),
      ]);
      setSchedules(schRes.data);
      setExaminations(examRes.data);
    } catch {
      showToast({ title: "Error", message: "Failed to load examination schedules", type: "error" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedExam, selectedDept, selectedStatus]);

  // Real-time conflict checking when parameters change in Wizard
  useEffect(() => {
    if (!modalOpen || step < 3) return;

    async function runConflictCheck() {
      setConflictChecking(true);
      try {
        const res = await examinationsService.checkScheduleConflicts({
          date,
          startTime,
          endTime,
          room,
          section: courseOfferingId === "co-cs301-a" ? "A" : "B",
          facultyId,
        });
        setConflictResult(res.data);
      } catch {
        setConflictResult(null);
      } finally {
        setConflictChecking(false);
      }
    }

    runConflictCheck();
  }, [date, startTime, endTime, room, facultyId, courseOfferingId, modalOpen, step]);

  const handleCreateSchedule = async () => {
    if (conflictResult?.hasConflict) {
      showToast({
        title: "Conflict Detected",
        message: conflictResult.message || "Cannot schedule due to overlap.",
        type: "error",
      });
      return;
    }

    try {
      setSaving(true);
      const selectedExamObj = examinations.find((e) => e.id === examId);

      await examinationsService.createSchedule({
        examinationId: examId,
        examinationName: selectedExamObj?.name || "End Semester Examinations",
        courseOfferingId,
        courseCode: courseOfferingId === "co-cs301-a" ? "CS301" : courseOfferingId === "co-cs302-a" ? "CS302" : "CS303",
        courseName:
          courseOfferingId === "co-cs301-a"
            ? "Data Structures & Algorithms"
            : courseOfferingId === "co-cs302-a"
            ? "Database Management Systems"
            : "Operating Systems & Concurrency",
        program: "B.Tech Computer Science & Engineering",
        department: "Computer Science & Engineering",
        semester: 5,
        section: "A",
        date,
        startTime,
        endTime,
        room,
        facultyId,
        facultyName: facultyId === "fac-001" ? "Dr. Ramesh Sundaram" : facultyId === "fac-002" ? "Dr. Anita Roy" : "Prof. Meenakshi Sundaram",
        totalCandidates: 68,
        status: "CONFIRMED",
        invigilatorNotes,
      });

      showToast({ title: "Success", message: "Exam timetable period scheduled successfully.", type: "success" });
      setModalOpen(false);
      setStep(1);
      loadData();
    } catch (err: unknown) {
      showToast({
        title: "Error",
        message: err instanceof Error ? err.message : "Failed to create exam schedule",
        type: "error",
      });
    } finally {
      setSaving(false);
    }
  };

  const columns: ColumnDef<ExamSchedule>[] = useMemo(
    () => [
      {
        id: "date",
        header: "Date & Time",
        cell: (row) => (
          <div>
            <div className="font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
              <Calendar className="h-3.5 w-3.5 text-indigo-600" />
              {row.date}
            </div>
            <div className="flex items-center gap-1.5 text-xs text-slate-500 mt-0.5">
              <Clock className="h-3 w-3 text-slate-400" />
              {row.startTime} - {row.endTime}
            </div>
          </div>
        ),
      },
      {
        id: "course",
        header: "Subject & Course",
        cell: (row) => (
          <div>
            <div className="font-semibold text-slate-900 dark:text-white">
              {row.courseCode} - {row.courseName}
            </div>
            <div className="text-xs text-slate-500">
              {row.program} • Sec {row.section}
            </div>
          </div>
        ),
      },
      {
        id: "venue",
        header: "Room & Venue",
        cell: (row) => (
          <div className="flex items-center gap-1.5 text-xs text-slate-700 dark:text-slate-200">
            <MapPin className="h-3.5 w-3.5 text-slate-400" />
            <span className="font-medium">{row.room}</span>
            <span className="text-slate-400">({row.totalCandidates} seats)</span>
          </div>
        ),
      },
      {
        id: "faculty",
        header: "Chief Invigilator",
        cell: (row) => (
          <div className="flex items-center gap-1.5 text-xs text-slate-700 dark:text-slate-200">
            <User className="h-3.5 w-3.5 text-slate-400" />
            <span>{row.facultyName}</span>
          </div>
        ),
      },
      {
        id: "status",
        header: "Status",
        cell: (row) => (
          <span
            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
              row.status === "CONFIRMED"
                ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                : row.status === "IN_PROGRESS"
                ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                : "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300"
            }`}
          >
            {row.status}
          </span>
        ),
      },
      {
        id: "actions",
        header: "Actions",
        cell: (row) => (
          <Link href={`/app/examinations/schedules/${row.id}`}>
            <Button size="sm" variant="outline" className="h-7 text-xs gap-1">
              Details
              <ArrowRight className="h-3 w-3" />
            </Button>
          </Link>
        ),
      },
    ],
    []
  );

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
              Examination Timetable
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">Conflict-Free Hall Allotment</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Examination Schedules & Timetables
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Schedule centralized exam dates, hall allocations, and faculty invigilation assignments with automated collision detection.
          </p>
        </div>

        <Button variant="primary" className="gap-2" onClick={() => { setStep(1); setModalOpen(true); }}>
          <Plus className="h-4 w-4" />
          Schedule Paper
        </Button>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3 bg-slate-50/70 p-3 rounded-xl border border-slate-200 dark:bg-slate-900/60 dark:border-slate-800 text-xs">
        <div className="flex items-center gap-1.5 text-slate-500 font-medium">
          <Filter className="h-3.5 w-3.5" />
          Filters:
        </div>

        <select
          value={selectedExam}
          onChange={(e) => setSelectedExam(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
        >
          <option value="ALL">All Exam Cycles</option>
          {examinations.map((ex) => (
            <option key={ex.id} value={ex.id}>{ex.name}</option>
          ))}
        </select>

        <select
          value={selectedDept}
          onChange={(e) => setSelectedDept(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
        >
          <option value="ALL">All Departments</option>
          <option value="Computer Science & Engineering">Computer Science & Engineering</option>
          <option value="Electronics & Communication">Electronics & Communication</option>
        </select>

        <select
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
        >
          <option value="ALL">All Statuses</option>
          <option value="CONFIRMED">Confirmed</option>
          <option value="IN_PROGRESS">In Progress</option>
          <option value="SCHEDULED">Scheduled</option>
        </select>
      </div>

      {/* Enterprise DataGrid */}
      <DataGrid<ExamSchedule>
        data={schedules}
        columns={columns}
        keyExtractor={(row) => row.id}
        loading={loading}
        searchPlaceholder="Search timetable by course code, name, room, or invigilator..."
        emptyTitle="No exam schedules found"
        emptyDescription="Schedule an examination paper using the wizard."
      />

      {/* 6-Step Guided Scheduling Wizard Modal */}
      <Dialog open={modalOpen} onClose={() => setModalOpen(false)}>
        <div className="p-6 space-y-5 max-w-xl">
          <div className="border-b border-slate-200 pb-3 dark:border-slate-800 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                Exam Scheduling Wizard
              </h2>
              <p className="text-xs text-slate-500">Step {step} of 6</p>
            </div>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div
                  key={i}
                  className={`h-1.5 w-6 rounded-full ${
                    step >= i ? "bg-indigo-600" : "bg-slate-200 dark:bg-slate-700"
                  }`}
                />
              ))}
            </div>
          </div>

          {/* Step 1: Select Examination */}
          {step === 1 && (
            <div className="space-y-4 text-xs">
              <label className="block font-medium text-slate-700 dark:text-slate-300">
                1. Select Examination Cycle *
              </label>
              <select
                value={examId}
                onChange={(e) => setExamId(e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white p-2.5 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              >
                {examinations.map((ex) => (
                  <option key={ex.id} value={ex.id}>{ex.name} ({ex.type})</option>
                ))}
              </select>
              <p className="text-slate-500">
                This timetable period will be linked to the institutional examination session.
              </p>
            </div>
          )}

          {/* Step 2: Select Course Offering */}
          {step === 2 && (
            <div className="space-y-4 text-xs">
              <label className="block font-medium text-slate-700 dark:text-slate-300">
                2. Select Course Offering *
              </label>
              <select
                value={courseOfferingId}
                onChange={(e) => setCourseOfferingId(e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white p-2.5 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              >
                <option value="co-cs301-a">CS301 - Data Structures & Algorithms (Sec A)</option>
                <option value="co-cs302-a">CS302 - Database Management Systems (Sec A)</option>
                <option value="co-cs303-a">CS303 - Operating Systems & Concurrency (Sec A)</option>
              </select>
            </div>
          )}

          {/* Step 3: Date & Time */}
          {step === 3 && (
            <div className="space-y-4 text-xs">
              <label className="block font-medium text-slate-700 dark:text-slate-300">
                3. Date and Time Slot *
              </label>
              <div className="grid grid-cols-2 gap-3">
                <div className="col-span-2">
                  <span className="text-slate-400">Examination Date</span>
                  <input
                    type="date"
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white mt-1"
                  />
                </div>
                <div>
                  <span className="text-slate-400">Start Time</span>
                  <input
                    type="text"
                    value={startTime}
                    onChange={(e) => setStartTime(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white mt-1"
                  />
                </div>
                <div>
                  <span className="text-slate-400">End Time</span>
                  <input
                    type="text"
                    value={endTime}
                    onChange={(e) => setEndTime(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white mt-1"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Room Allocation */}
          {step === 4 && (
            <div className="space-y-4 text-xs">
              <label className="block font-medium text-slate-700 dark:text-slate-300">
                4. Hall / Room Allocation *
              </label>
              <select
                value={room}
                onChange={(e) => setRoom(e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white p-2.5 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              >
                <option value="CS-LH-201">Lecture Hall CS-LH-201 (Capacity 70)</option>
                <option value="CS-LH-202">Lecture Hall CS-LH-202 (Capacity 70)</option>
                <option value="Auditorium Hall A">Auditorium Hall A (Capacity 250)</option>
                <option value="Auditorium Hall B">Auditorium Hall B (Capacity 250)</option>
              </select>
            </div>
          )}

          {/* Step 5: Invigilation */}
          {step === 5 && (
            <div className="space-y-4 text-xs">
              <label className="block font-medium text-slate-700 dark:text-slate-300">
                5. Chief Invigilator Assignment *
              </label>
              <select
                value={facultyId}
                onChange={(e) => setFacultyId(e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white p-2.5 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              >
                <option value="fac-001">Dr. Ramesh Sundaram (CSE)</option>
                <option value="fac-002">Dr. Anita Roy (CSE)</option>
                <option value="fac-003">Prof. Meenakshi Sundaram (ECE)</option>
              </select>
              <div>
                <span className="text-slate-400">Invigilation Guidelines / Notes</span>
                <input
                  type="text"
                  value={invigilatorNotes}
                  onChange={(e) => setInvigilatorNotes(e.target.value)}
                  placeholder="e.g. Standard closed-book rules; non-programmable calculators allowed."
                  className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white mt-1"
                />
              </div>
            </div>
          )}

          {/* Step 6: Review & Conflict Detection Visualizer */}
          {step === 6 && (
            <div className="space-y-4 text-xs">
              <h3 className="font-semibold text-slate-900 dark:text-white">
                6. Review Schedule & Conflict Verification
              </h3>

              {/* Conflict Status Visualizer */}
              {conflictResult?.hasConflict ? (
                <div className="rounded-xl border border-rose-300 bg-rose-50 p-3.5 dark:border-rose-900/60 dark:bg-rose-950/40 text-rose-900 dark:text-rose-200 space-y-1">
                  <div className="flex items-center gap-2 font-bold text-rose-700 dark:text-rose-300">
                    <ShieldAlert className="h-4 w-4" />
                    Conflict Detected: {conflictResult.conflictType}
                  </div>
                  <p className="text-xs">{conflictResult.message}</p>
                </div>
              ) : (
                <div className="rounded-xl border border-emerald-300 bg-emerald-50 p-3 dark:border-emerald-900/60 dark:bg-emerald-950/40 text-emerald-900 dark:text-emerald-200 flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                  <span>No timetable collisions. Room and invigilator are clear for this time slot.</span>
                </div>
              )}

              <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900/60 space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-400">Exam:</span>
                  <span className="font-medium text-slate-800 dark:text-slate-200">
                    {examinations.find((e) => e.id === examId)?.name}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Course Offering:</span>
                  <span className="font-medium text-slate-800 dark:text-slate-200">
                    {courseOfferingId}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Date & Time:</span>
                  <span className="font-medium text-slate-800 dark:text-slate-200">
                    {date} ({startTime} - {endTime})
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Room:</span>
                  <span className="font-medium text-slate-800 dark:text-slate-200">{room}</span>
                </div>
              </div>
            </div>
          )}

          {/* Navigation Controls */}
          <div className="flex justify-between pt-3 border-t border-slate-200 dark:border-slate-800">
            {step > 1 ? (
              <Button type="button" variant="outline" onClick={() => setStep(step - 1)}>
                Back
              </Button>
            ) : (
              <div />
            )}

            {step < 6 ? (
              <Button type="button" variant="primary" onClick={() => setStep(step + 1)}>
                Continue
              </Button>
            ) : (
              <Button
                type="button"
                variant="primary"
                onClick={handleCreateSchedule}
                disabled={saving || Boolean(conflictResult?.hasConflict)}
              >
                {saving ? "Scheduling..." : "Confirm Schedule"}
              </Button>
            )}
          </div>
        </div>
      </Dialog>
    </div>
  );
}
