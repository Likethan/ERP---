"use client";

import React, { useEffect, useState, useMemo, useCallback } from "react";
import Link from "next/link";
import { academicsService } from "@/services/academics.service";
import {
  MasterTimeSlot,
  ScheduledTimetableEntry,
  TimetableConflict,
  DayOfWeek,
  CourseOfferingDetail,
} from "@/types/academics";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatCard } from "@/components/ui/stat-card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { TableSkeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { useAuth } from "@/lib/auth-context";
import {
  Calendar,
  Clock,
  Users,
  Building,
  Plus,
  Trash2,
  Edit2,
  AlertTriangle,
  CheckCircle2,
  GraduationCap,
  Sparkles,
  BookOpen,
  Eye,
  Filter,
} from "lucide-react";

const DAYS_OF_WEEK: DayOfWeek[] = [
  "MONDAY",
  "TUESDAY",
  "WEDNESDAY",
  "THURSDAY",
  "FRIDAY",
  "SATURDAY",
];

export default function MasterTimetableManagementPage() {
  const { showToast } = useToast();
  const { activePersona } = useAuth();

  const [timeSlots, setTimeSlots] = useState<MasterTimeSlot[]>([]);
  const [scheduledEntries, setScheduledEntries] = useState<ScheduledTimetableEntry[]>([]);
  const [conflicts, setConflicts] = useState<TimetableConflict[]>([]);
  const [offerings, setOfferings] = useState<CourseOfferingDetail[]>([]);
  const [loading, setLoading] = useState(true);

  // View Mode: 'week' | 'day' | 'section' | 'faculty' | 'room'
  const [viewMode, setViewMode] = useState<"week" | "day" | "section" | "faculty" | "room">("week");
  const [selectedDay, setSelectedDay] = useState<DayOfWeek>("MONDAY");
  const [selectedSection, setSelectedSection] = useState("A");
  const [selectedFaculty, setSelectedFaculty] = useState("Dr. V. Ramanathan");
  const [selectedRoom, setSelectedRoom] = useState("Room A-204");

  // Create / Edit Timetable Entry Modal
  const [entryModalOpen, setEntryModalOpen] = useState(false);
  const [editingEntryId, setEditingEntryId] = useState<string | null>(null);
  const [formDay, setFormDay] = useState<DayOfWeek>("MONDAY");
  const [formTimeSlotId, setFormTimeSlotId] = useState("ts-1");
  const [formOfferingId, setFormOfferingId] = useState("");
  const [formRoomNumber, setFormRoomNumber] = useState("Room A-204");
  const [formBuilding, setFormBuilding] = useState("Turing Block");
  const [formEntryType, setFormEntryType] = useState<"THEORY" | "LAB" | "TUTORIAL">("THEORY");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Delete confirmation
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [slotsRes, entriesRes, confRes, offRes] = await Promise.all([
        academicsService.getMasterTimeSlots(),
        academicsService.getScheduledTimetable(),
        academicsService.getTimetableConflicts(),
        academicsService.getCourseOfferingDetails(),
      ]);
      setTimeSlots(slotsRes.data);
      setScheduledEntries(entriesRes.data);
      setConflicts(confRes.data);
      setOfferings(offRes.data);
      if (offRes.data.length > 0 && !formOfferingId) {
        setFormOfferingId(offRes.data[0].id);
      }
    } catch (err) {
      console.error("Failed to load timetable data:", err);
      showToast({ title: "Failed to load timetable", type: "error" });
    } finally {
      setLoading(false);
    }
  }, [showToast, formOfferingId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Distinct lists for filters
  const distinctSections = useMemo(() => {
    return Array.from(new Set(scheduledEntries.map((e) => e.section)));
  }, [scheduledEntries]);

  const distinctFaculty = useMemo(() => {
    return Array.from(new Set(scheduledEntries.map((e) => e.facultyName)));
  }, [scheduledEntries]);

  const distinctRooms = useMemo(() => {
    return Array.from(new Set(scheduledEntries.map((e) => e.roomNumber)));
  }, [scheduledEntries]);

  // Active entries filtered by viewMode
  const visibleEntries = useMemo(() => {
    if (viewMode === "day") {
      return scheduledEntries.filter((e) => e.day === selectedDay);
    }
    if (viewMode === "section") {
      return scheduledEntries.filter((e) => e.section === selectedSection);
    }
    if (viewMode === "faculty") {
      return scheduledEntries.filter((e) => e.facultyName === selectedFaculty);
    }
    if (viewMode === "room") {
      return scheduledEntries.filter((e) => e.roomNumber === selectedRoom);
    }
    // Week view shows for current selected section
    return scheduledEntries.filter((e) => e.section === selectedSection);
  }, [scheduledEntries, viewMode, selectedDay, selectedSection, selectedFaculty, selectedRoom]);

  // Check if an entry has an active conflict
  const isConflicting = (entryId: string) => {
    return conflicts.some((c) => c.conflictingEntryIds.includes(entryId));
  };

  // Open Create Modal
  const openCreateModal = (day?: DayOfWeek, timeSlotId?: string) => {
    setEditingEntryId(null);
    if (day) setFormDay(day);
    if (timeSlotId) setFormTimeSlotId(timeSlotId);
    setEntryModalOpen(true);
  };

  // Open Edit Modal
  const openEditModal = (entry: ScheduledTimetableEntry) => {
    setEditingEntryId(entry.id);
    setFormDay(entry.day);
    setFormTimeSlotId(entry.timeSlotId);
    setFormOfferingId(entry.courseOfferingId);
    setFormRoomNumber(entry.roomNumber);
    setFormBuilding(entry.building);
    setFormEntryType(entry.entryType as any);
    setEntryModalOpen(true);
  };

  // Submit Entry Form
  const handleSubmitEntry = async (e: React.FormEvent) => {
    e.preventDefault();
    const offObj = offerings.find((o) => o.id === formOfferingId);
    const slotObj = timeSlots.find((s) => s.id === formTimeSlotId);
    if (!offObj || !slotObj) return;

    const primaryFac = offObj.facultyAssignments[0];
    const facId = primaryFac ? primaryFac.facultyId : "fac-default";
    const facName = primaryFac ? primaryFac.facultyName : "Unassigned";

    try {
      setIsSubmitting(true);
      if (editingEntryId) {
        await academicsService.updateTimetableEntry(editingEntryId, {
          day: formDay,
          timeSlotId: formTimeSlotId,
          startTime: slotObj.startTime,
          endTime: slotObj.endTime,
          roomNumber: formRoomNumber,
          building: formBuilding,
          entryType: formEntryType,
        });
        showToast({ title: "Timetable Slot Updated", type: "success" });
      } else {
        await academicsService.createTimetableEntry({
          courseOfferingId: offObj.id,
          subjectCode: offObj.subjectCode,
          subjectName: offObj.subjectName,
          facultyId: facId,
          facultyName: facName,
          department: offObj.department,
          semester: offObj.semester,
          section: offObj.section,
          roomNumber: formRoomNumber,
          building: formBuilding,
          day: formDay,
          timeSlotId: formTimeSlotId,
          startTime: slotObj.startTime,
          endTime: slotObj.endTime,
          entryType: formEntryType,
        });
        showToast({ title: "Timetable Slot Scheduled", type: "success" });
      }
      setEntryModalOpen(false);
      loadData();
    } catch (err: any) {
      showToast({ title: "Operation failed", message: err.message, type: "error" });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Delete Entry
  const handleDeleteEntry = async (id: string) => {
    try {
      await academicsService.deleteTimetableEntry(id);
      showToast({ title: "Period Removed from Timetable", type: "info" });
      setDeleteConfirmId(null);
      loadData();
    } catch (err: any) {
      showToast({ title: "Failed to delete slot", message: err.message, type: "error" });
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-24 bg-slate-900/60 rounded-xl animate-pulse" />
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 bg-slate-900/60 rounded-xl animate-pulse" />
          ))}
        </div>
        <TableSkeleton rows={6} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Link href="/app/academics" className="hover:text-white transition-colors">
              Academics
            </Link>
            <span>/</span>
            <span className="text-white">Master Timetable</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Master Timetable & Collision Engine
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Weekly section schedules, faculty contact allocations, classroom double-booking audits, and conflict detection.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="primary"
            size="sm"
            leftIcon={<Plus className="h-4 w-4" />}
            onClick={() => openCreateModal()}
          >
            Schedule Period
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Weekly Scheduled Periods"
          value={scheduledEntries.length}
          description="Active teaching periods"
          variant="indigo"
          icon={<Calendar className="h-4 w-4" />}
        />
        <StatCard
          label="Detected Conflicts"
          value={conflicts.length}
          description={conflicts.length === 0 ? "0 collisions found" : "Requires schedule adjustment"}
          variant={conflicts.length > 0 ? "amber" : "emerald"}
          icon={<AlertTriangle className="h-4 w-4" />}
        />
        <StatCard
          label="Active Classrooms"
          value={distinctRooms.length}
          description="Lecture halls & laboratories"
          variant="sky"
          icon={<Building className="h-4 w-4" />}
        />
        <StatCard
          label="Faculty Teaching Load"
          value={`${distinctFaculty.length} Instructors`}
          description="Active teaching roster"
          variant="emerald"
          icon={<GraduationCap className="h-4 w-4" />}
        />
      </div>

      {/* Conflict Notice Banner */}
      {conflicts.length > 0 && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 space-y-2">
          <div className="flex items-center gap-2 text-amber-300 font-semibold text-xs">
            <AlertTriangle className="h-4 w-4" />
            Timetable Collision Detected ({conflicts.length})
          </div>
          <div className="space-y-1">
            {conflicts.map((c) => (
              <div key={c.id} className="text-xs text-amber-200/90 flex items-start gap-2">
                <span className="font-mono font-bold text-amber-400">[{c.conflictType.replace("_", " ")}]</span>
                <span>{c.description}</span>
                <span className="font-mono text-slate-400">({c.day} • {c.timeSlot})</span>
              </div>
            ))}
          </div>
          <div className="text-[10px] text-amber-400/80 pt-1">
            * Note: Frontend collision detection acts as an operational convenience; academic council policy remains authoritative.
          </div>
        </div>
      )}

      {/* View Switcher Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 rounded-xl border border-slate-800 bg-slate-900/60 p-3">
        <div className="flex flex-wrap items-center gap-1.5 text-xs">
          {[
            { id: "week", label: "Week View" },
            { id: "day", label: "Day View" },
            { id: "section", label: "Section View" },
            { id: "faculty", label: "Faculty Schedule" },
            { id: "room", label: "Room Utilization" },
          ].map((mode) => (
            <button
              key={mode.id}
              onClick={() => setViewMode(mode.id as any)}
              className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
                viewMode === mode.id
                  ? "bg-indigo-600 text-white font-semibold"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
              }`}
            >
              {mode.label}
            </button>
          ))}
        </div>

        {/* View Specific Selectors */}
        <div className="flex items-center gap-2">
          {viewMode === "day" && (
            <select
              value={selectedDay}
              onChange={(e) => setSelectedDay(e.target.value as DayOfWeek)}
              className="h-8 rounded-lg border border-slate-700 bg-slate-900 px-2.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
            >
              {DAYS_OF_WEEK.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          )}

          {(viewMode === "week" || viewMode === "section") && (
            <select
              value={selectedSection}
              onChange={(e) => setSelectedSection(e.target.value)}
              className="h-8 rounded-lg border border-slate-700 bg-slate-900 px-2.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
            >
              {["A", "B", "C"].map((sec) => (
                <option key={sec} value={sec}>
                  Section {sec}
                </option>
              ))}
            </select>
          )}

          {viewMode === "faculty" && (
            <select
              value={selectedFaculty}
              onChange={(e) => setSelectedFaculty(e.target.value)}
              className="h-8 rounded-lg border border-slate-700 bg-slate-900 px-2.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
            >
              {distinctFaculty.map((fac) => (
                <option key={fac} value={fac}>
                  {fac}
                </option>
              ))}
            </select>
          )}

          {viewMode === "room" && (
            <select
              value={selectedRoom}
              onChange={(e) => setSelectedRoom(e.target.value)}
              className="h-8 rounded-lg border border-slate-700 bg-slate-900 px-2.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
            >
              {distinctRooms.map((rm) => (
                <option key={rm} value={rm}>
                  {rm}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* Timetable Weekly Matrix Grid */}
      {viewMode === "week" && (
        <Card className="overflow-hidden">
          <CardHeader className="py-3 px-4 bg-slate-900/80 border-b border-slate-800 flex flex-row items-center justify-between">
            <CardTitle className="text-xs">
              Weekly Master Timetable (Section {selectedSection} • Semester 5)
            </CardTitle>
            <span className="text-[11px] font-mono text-slate-400">
              Odd Semester AY 2026-2027
            </span>
          </CardHeader>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-slate-200 border-collapse">
              <thead>
                <tr className="bg-slate-950/80 border-b border-slate-800 text-[11px] font-semibold text-slate-400 uppercase">
                  <th className="p-3 w-28 text-left border-r border-slate-800">Day / Slot</th>
                  {timeSlots.map((ts) => (
                    <th key={ts.id} className="p-2.5 text-center min-w-[130px] border-r border-slate-800 last:border-r-0">
                      <div>{ts.label}</div>
                      <div className="text-[10px] text-slate-500 font-mono font-normal">
                        {ts.startTime} - {ts.endTime}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {DAYS_OF_WEEK.map((day) => (
                  <tr key={day} className="hover:bg-slate-900/30">
                    <td className="p-3 font-semibold text-white bg-slate-900/40 border-r border-slate-800 font-mono text-xs">
                      {day}
                    </td>
                    {timeSlots.map((ts) => {
                      const entry = scheduledEntries.find(
                        (e) => e.day === day && e.timeSlotId === ts.id && e.section === selectedSection
                      );
                      const hasConflict = entry ? isConflicting(entry.id) : false;

                      return (
                        <td
                          key={ts.id}
                          className="p-1.5 border-r border-slate-800 last:border-r-0 align-top"
                        >
                          {entry ? (
                            <div
                              className={`p-2.5 rounded-lg border text-xs space-y-1 relative group transition-all ${
                                hasConflict
                                  ? "border-red-500/80 bg-red-500/10 ring-1 ring-red-500/40"
                                  : entry.entryType === "LAB"
                                  ? "border-emerald-500/40 bg-emerald-500/10"
                                  : "border-indigo-500/40 bg-indigo-500/10"
                              }`}
                            >
                              <div className="flex items-center justify-between">
                                <span className="font-mono font-bold text-white">{entry.subjectCode}</span>
                                <Badge variant={entry.entryType === "LAB" ? "success" : "info"} className="text-[9px] px-1 py-0">
                                  {entry.entryType}
                                </Badge>
                              </div>
                              <div className="text-[11px] text-slate-300 line-clamp-1">{entry.subjectName}</div>
                              <div className="text-[10px] text-slate-400 font-mono flex items-center justify-between pt-1 border-t border-slate-800/60">
                                <span>{entry.roomNumber}</span>
                                <span className="text-indigo-300 font-sans">{entry.facultyName}</span>
                              </div>

                              {/* Hover actions */}
                              <div className="absolute top-1 right-1 hidden group-hover:flex items-center gap-1 bg-slate-900/90 rounded p-0.5 border border-slate-700">
                                <button
                                  onClick={() => openEditModal(entry)}
                                  className="p-1 text-slate-300 hover:text-indigo-400"
                                  title="Edit slot"
                                >
                                  <Edit2 className="h-3 w-3" />
                                </button>
                                <button
                                  onClick={() => setDeleteConfirmId(entry.id)}
                                  className="p-1 text-slate-300 hover:text-red-400"
                                  title="Delete slot"
                                >
                                  <Trash2 className="h-3 w-3" />
                                </button>
                              </div>
                            </div>
                          ) : (
                            <button
                              onClick={() => openCreateModal(day, ts.id)}
                              className="w-full h-16 rounded border border-dashed border-slate-800 hover:border-indigo-500/50 hover:bg-slate-800/20 text-slate-600 hover:text-indigo-400 flex items-center justify-center transition-all group"
                              title="Assign Period"
                            >
                              <Plus className="h-4 w-4 opacity-40 group-hover:opacity-100" />
                            </button>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* List / Card Layout for Day, Section, Faculty, Room views */}
      {viewMode !== "week" && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>
                {viewMode === "day" && `${selectedDay} Schedule`}
                {viewMode === "section" && `Section ${selectedSection} Schedule`}
                {viewMode === "faculty" && `${selectedFaculty} Workload & Timetable`}
                {viewMode === "room" && `${selectedRoom} Utilization Timeline`}
              </CardTitle>
              <CardDescription>
                {visibleEntries.length} scheduled periods mapped
              </CardDescription>
            </div>
            <Button
              variant="primary"
              size="sm"
              leftIcon={<Plus className="h-3.5 w-3.5" />}
              onClick={() => openCreateModal()}
            >
              Add Entry
            </Button>
          </CardHeader>
          <CardContent className="p-0">
            {visibleEntries.length === 0 ? (
              <div className="p-12 text-center text-xs text-slate-400">
                No scheduled periods found for this filter.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left text-slate-300">
                  <thead className="bg-slate-950/60 text-[11px] font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="px-5 py-3">Day & Time</th>
                      <th className="px-4 py-3">Subject & Code</th>
                      <th className="px-4 py-3">Section</th>
                      <th className="px-4 py-3">Instructor</th>
                      <th className="px-4 py-3">Classroom</th>
                      <th className="px-4 py-3">Type</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {visibleEntries.map((slot) => {
                      const hasConflict = isConflicting(slot.id);
                      return (
                        <tr key={slot.id} className="hover:bg-slate-800/40 transition-colors">
                          <td className="px-5 py-3.5 font-medium text-white">
                            <div>{slot.day}</div>
                            <div className="text-[11px] text-indigo-400 font-mono">
                              {slot.startTime} – {slot.endTime}
                            </div>
                          </td>
                          <td className="px-4 py-3.5">
                            <span className="font-mono font-semibold text-white">{slot.subjectCode}</span>
                            <span className="block text-[11px] text-slate-400">{slot.subjectName}</span>
                          </td>
                          <td className="px-4 py-3.5 font-mono text-slate-300">
                            Sem {slot.semester} • Sec {slot.section}
                          </td>
                          <td className="px-4 py-3.5 text-slate-200">{slot.facultyName}</td>
                          <td className="px-4 py-3.5 text-slate-200">
                            <div>{slot.roomNumber}</div>
                            <div className="text-[10px] text-slate-500">{slot.building}</div>
                          </td>
                          <td className="px-4 py-3.5">
                            <Badge variant={slot.entryType === "LAB" ? "success" : "info"}>
                              {slot.entryType}
                            </Badge>
                          </td>
                          <td className="px-4 py-3.5 text-right">
                            <div className="flex items-center justify-end gap-1">
                              <button
                                onClick={() => openEditModal(slot)}
                                className="p-1 text-slate-400 hover:text-indigo-400 transition-colors"
                              >
                                <Edit2 className="h-4 w-4" />
                              </button>
                              <button
                                onClick={() => setDeleteConfirmId(slot.id)}
                                className="p-1 text-slate-400 hover:text-red-400 transition-colors"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Schedule Entry Modal */}
      <Dialog
        open={entryModalOpen}
        onClose={() => setEntryModalOpen(false)}
        title={editingEntryId ? "Edit Timetable Period" : "Schedule New Period in Master Timetable"}
      >
        <form onSubmit={handleSubmitEntry} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Day of Week</label>
              <select
                value={formDay}
                onChange={(e) => setFormDay(e.target.value as DayOfWeek)}
                className="w-full h-9 rounded-lg border border-slate-700 bg-slate-900 px-3 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
              >
                {DAYS_OF_WEEK.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Time Slot Period</label>
              <select
                value={formTimeSlotId}
                onChange={(e) => setFormTimeSlotId(e.target.value)}
                className="w-full h-9 rounded-lg border border-slate-700 bg-slate-900 px-3 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
              >
                {timeSlots.map((ts) => (
                  <option key={ts.id} value={ts.id}>
                    {ts.label} ({ts.startTime} - {ts.endTime})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Course Offering <span className="text-red-400">*</span>
            </label>
            <select
              value={formOfferingId}
              onChange={(e) => setFormOfferingId(e.target.value)}
              className="w-full h-9 rounded-lg border border-slate-700 bg-slate-900 px-3 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
            >
              {offerings.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.subjectCode} - {o.subjectName} (Sem {o.semester} Sec {o.section})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Classroom / Lab</label>
              <Input
                value={formRoomNumber}
                onChange={(e) => setFormRoomNumber(e.target.value)}
                placeholder="e.g. Room A-204"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Building</label>
              <Input
                value={formBuilding}
                onChange={(e) => setFormBuilding(e.target.value)}
                placeholder="e.g. Turing Block"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Period Session Type</label>
            <select
              value={formEntryType}
              onChange={(e) => setFormEntryType(e.target.value as any)}
              className="w-full h-9 rounded-lg border border-slate-700 bg-slate-900 px-3 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
            >
              <option value="THEORY">Theory Lecture</option>
              <option value="LAB">Laboratory Session</option>
              <option value="TUTORIAL">Tutorial Period</option>
            </select>
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setEntryModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={isSubmitting}
            >
              {editingEntryId ? "Save Changes" : "Confirm Schedule"}
            </Button>
          </div>
        </form>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={Boolean(deleteConfirmId)}
        onClose={() => setDeleteConfirmId(null)}
        title="Confirm Removal from Timetable"
      >
        <div className="space-y-3 text-xs text-slate-300">
          <p>
            Are you sure you want to remove this scheduled period from the master timetable?
          </p>
          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setDeleteConfirmId(null)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => deleteConfirmId && handleDeleteEntry(deleteConfirmId)}
            >
              Delete Period
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
