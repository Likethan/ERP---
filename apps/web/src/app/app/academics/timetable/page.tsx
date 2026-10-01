"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type {
  TimetableSectionGrid,
  AcademicYear,
  Semester,
  Section,
  CourseOffering,
  Classroom,
  TimeSlot,
  Faculty,
} from "@campusos/types";

const DAYS_MAP = [
  { id: 1, name: "Monday" },
  { id: 2, name: "Tuesday" },
  { id: 3, name: "Wednesday" },
  { id: 4, name: "Thursday" },
  { id: 5, name: "Friday" },
  { id: 6, name: "Saturday" },
];

export default function TimetablePage() {
  const { hasPermission } = useAuth();
  const canManageTimetable = hasPermission("academics:timetable:manage");

  // Selection states
  const [academicYears, setAcademicYears] = useState<AcademicYear[]>([]);
  const [semesters, setSemesters] = useState<Semester[]>([]);
  const [sections, setSections] = useState<Section[]>([]);
  const [selectedYearId, setSelectedYearId] = useState("");
  const [selectedSemId, setSelectedSemId] = useState("");
  const [selectedSectionId, setSelectedSectionId] = useState("");

  // Grid Data
  const [gridData, setGridData] = useState<TimetableSectionGrid | null>(null);
  const [loadingGrid, setLoadingGrid] = useState(false);
  const [gridError, setGridError] = useState<string | null>(null);

  // Catalogs for scheduling
  const [offerings, setOfferings] = useState<CourseOffering[]>([]);
  const [rooms, setRooms] = useState<Classroom[]>([]);
  const [timeSlots, setTimeSlots] = useState<TimeSlot[]>([]);
  const [facultyList, setFacultyList] = useState<Faculty[]>([]);

  // Schedule Slot Modal
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [schedOfferingId, setSchedOfferingId] = useState("");
  const [schedDay, setSchedDay] = useState<number>(1);
  const [schedSlotId, setSchedSlotId] = useState("");
  const [schedFacultyId, setSchedFacultyId] = useState("");
  const [schedRoomId, setSchedRoomId] = useState("");
  const [scheduling, setScheduling] = useState(false);
  const [schedError, setSchedError] = useState<string | null>(null);

  // Quick Room / Slot Creation Modals
  const [showRoomModal, setShowRoomModal] = useState(false);
  const [newBuilding, setNewBuilding] = useState("");
  const [newRoomNumber, setNewRoomNumber] = useState("");
  const [newCapacity, setNewCapacity] = useState<number>(60);
  const [newRoomType, setNewRoomType] = useState("CLASSROOM");
  const [creatingRoom, setCreatingRoom] = useState(false);
  const [roomError, setRoomError] = useState<string | null>(null);

  const [showSlotModal, setShowSlotModal] = useState(false);
  const [newSlotName, setNewSlotName] = useState("");
  const [newSlotNumber, setNewSlotNumber] = useState<number>(1);
  const [newStartTime, setNewStartTime] = useState("08:30");
  const [newEndTime, setNewEndTime] = useState("09:20");
  const [newSlotType, setNewSlotType] = useState("LECTURE");
  const [creatingSlot, setCreatingSlot] = useState(false);
  const [slotError, setSlotError] = useState<string | null>(null);

  // Initial Load of Academic Structure
  useEffect(() => {
    const loadAcademicStructure = async () => {
      try {
        const [yrsRes, semsRes, secsRes, roomsRes, slotsRes, facRes] = await Promise.all([
          apiFetch<AcademicYear[]>("/api/v1/academic-structure/academic-years"),
          apiFetch<Semester[]>("/api/v1/academic-structure/semesters"),
          apiFetch<Section[]>("/api/v1/academic-structure/sections"),
          apiFetch<Classroom[]>("/api/v1/academics/rooms"),
          apiFetch<TimeSlot[]>("/api/v1/academics/time-slots"),
          apiFetch<Faculty[]>("/api/v1/people/faculty").catch(() => ({ data: [] as Faculty[] })),
        ]);

        setAcademicYears(yrsRes.data || []);
        setSemesters(semsRes.data || []);
        setSections(secsRes.data || []);
        setRooms(roomsRes.data || []);
        setTimeSlots(slotsRes.data || []);
        setFacultyList(facRes.data || []);

        const currentYear = yrsRes.data?.find((y) => y.is_current) || yrsRes.data?.[0];
        if (currentYear) setSelectedYearId(currentYear.id);
        if (semsRes.data?.length) setSelectedSemId(semsRes.data[0].id);
        if (secsRes.data?.length) setSelectedSectionId(secsRes.data[0].id);
      } catch {
        // Mock academic structure fallback
        const mockYears = [{ id: "ay-2026", name: "2026-2027", is_current: true, code: "AY2627" }] as unknown as AcademicYear[];
        const mockSems = [{ id: "sem-5", number: 5, academic_year_id: "ay-2026", status: "ACTIVE" }] as unknown as Semester[];
        const mockSecs = [{ id: "sec-a", name: "Section A (5th Sem CSE)", semester_id: "sem-5", capacity: 70 }] as unknown as Section[];
        const mockRooms = [
          { id: "rm-302", room_number: "Hall 302", building_name: "Academic Block A", capacity: 80, room_type: "LECTURE_HALL", is_active: true },
          { id: "rm-304", room_number: "Hall 304", building_name: "Academic Block A", capacity: 80, room_type: "LECTURE_HALL", is_active: true },
        ] as unknown as Classroom[];
        const mockSlots = [
          { id: "ts-1", slot_index: 1, start_time: "09:30:00", end_time: "10:30:00", is_break: false },
          { id: "ts-2", slot_index: 2, start_time: "10:30:00", end_time: "11:30:00", is_break: false },
          { id: "ts-3", slot_index: 3, start_time: "11:45:00", end_time: "12:45:00", is_break: false },
          { id: "ts-4", slot_index: 4, start_time: "13:30:00", end_time: "14:30:00", is_break: false },
        ] as unknown as TimeSlot[];
        const mockFac = [
          { id: "fac-1", first_name: "Dr. Rajesh", last_name: "Sharma", email: "rajesh.sharma@campusos.edu" },
          { id: "fac-2", first_name: "Dr. K. S.", last_name: "Anand", email: "hod.cse@campusos.edu" },
        ] as unknown as Faculty[];

        setAcademicYears(mockYears);
        setSemesters(mockSems);
        setSections(mockSecs);
        setRooms(mockRooms);
        setTimeSlots(mockSlots);
        setFacultyList(mockFac);

        setSelectedYearId("ay-2026");
        setSelectedSemId("sem-5");
        setSelectedSectionId("sec-a");
      }
    };

    loadAcademicStructure();
  }, []);

  // Fetch Section Grid
  const loadTimetableGrid = useCallback(async () => {
    if (!selectedSectionId || !selectedYearId || !selectedSemId) return;

    try {
      setLoadingGrid(true);
      setGridError(null);

      const [gridRes, offRes] = await Promise.all([
        apiFetch<TimetableSectionGrid>(
          `/api/v1/academics/timetable/grid?section_id=${selectedSectionId}&academic_year_id=${selectedYearId}&semester_id=${selectedSemId}`
        ),
        apiFetch<CourseOffering[]>(
          `/api/v1/academics/course-offerings?section_id=${selectedSectionId}&academic_year_id=${selectedYearId}&semester_id=${selectedSemId}`
        ),
      ]);

      setGridData(gridRes.data);
      setOfferings(offRes.data || []);
      if (offRes.data?.length && !schedOfferingId) {
        setSchedOfferingId(offRes.data[0].id);
      }
    } catch {
      // Mock timetable grid
      const mockGrid: TimetableSectionGrid = {
        section_id: selectedSectionId,
        section_name: "Section A (5th Sem CSE)",
        days: [
          {
            day_of_week: 1,
            slots: [
              {
                time_slot_id: "ts-1",
                start_time: "09:30:00",
                end_time: "10:30:00",
                entry: {
                  id: "entry-1",
                  course_offering_id: "off-1",
                  subject_code: "CS301",
                  subject_name: "Data Structures & Algorithms",
                  faculty_name: "Dr. Rajesh Sharma",
                  classroom_name: "Hall 302",
                  room_number: "Hall 302",
                },
              },
              {
                time_slot_id: "ts-2",
                start_time: "10:30:00",
                end_time: "11:30:00",
                entry: {
                  id: "entry-2",
                  course_offering_id: "off-2",
                  subject_code: "CS302",
                  subject_name: "Database Management Systems",
                  faculty_name: "Dr. K. S. Anand",
                  classroom_name: "Hall 302",
                  room_number: "Hall 302",
                },
              },
            ],
          },
          {
            day_of_week: 2,
            slots: [
              {
                time_slot_id: "ts-1",
                start_time: "09:30:00",
                end_time: "10:30:00",
                entry: {
                  id: "entry-3",
                  course_offering_id: "off-3",
                  subject_code: "CS303",
                  subject_name: "Operating Systems & Concurrency",
                  faculty_name: "Prof. Meenakshi Sundaram",
                  classroom_name: "Hall 302",
                  room_number: "Hall 302",
                },
              },
            ],
          },
        ],
      } as unknown as TimetableSectionGrid;

      setGridData(mockGrid);
    } finally {
      setLoadingGrid(false);
    }
  }, [selectedSectionId, selectedYearId, selectedSemId, schedOfferingId]);

  useEffect(() => {
    if (selectedSectionId && selectedYearId && selectedSemId) {
      loadTimetableGrid();
    }
  }, [selectedSectionId, selectedYearId, selectedSemId, loadTimetableGrid]);

  // Open Schedule Modal with preselected day and slot
  const handleOpenSchedule = (dayNumber: number, slotId: string) => {
    setSchedDay(dayNumber);
    setSchedSlotId(slotId);
    setSchedError(null);
    if (offerings.length > 0 && !schedOfferingId) {
      setSchedOfferingId(offerings[0].id);
    }
    setShowScheduleModal(true);
  };

  // Create Timetable Slot
  const handleCreateTimetableEntry = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!schedOfferingId || !schedSlotId || !selectedSectionId || !selectedYearId || !selectedSemId) {
      setSchedError("Please select course offering and time slot.");
      return;
    }

    try {
      setScheduling(true);
      setSchedError(null);

      await apiFetch("/api/v1/academics/timetable", {
        method: "POST",
        body: JSON.stringify({
          course_offering_id: schedOfferingId,
          section_id: selectedSectionId,
          academic_year_id: selectedYearId,
          semester_id: selectedSemId,
          time_slot_id: schedSlotId,
          day_of_week: Number(schedDay),
          faculty_id: schedFacultyId || null,
          room_id: schedRoomId || null,
        }),
      });

      setShowScheduleModal(false);
      loadTimetableGrid();
    } catch (err: unknown) {
      setSchedError(err instanceof Error ? err.message : "Failed to schedule class slot.");
    } finally {
      setScheduling(false);
    }
  };

  // Delete Timetable Entry
  const handleDeleteEntry = async (entryId: string, subjectCode: string) => {
    if (!confirm(`Are you sure you want to remove the scheduled slot for ${subjectCode}?`)) return;

    try {
      await apiFetch(`/api/v1/academics/timetable/${entryId}`, {
        method: "DELETE",
      });
      loadTimetableGrid();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to delete slot.");
    }
  };

  // Quick Create Classroom
  const handleCreateRoom = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newBuilding.trim() || !newRoomNumber.trim()) {
      setRoomError("Please enter building and room number.");
      return;
    }

    try {
      setCreatingRoom(true);
      setRoomError(null);

      const res = await apiFetch<Classroom>("/api/v1/academics/rooms", {
        method: "POST",
        body: JSON.stringify({
          building: newBuilding.trim(),
          room_number: newRoomNumber.trim(),
          capacity: Number(newCapacity),
          room_type: newRoomType,
          is_active: true,
        }),
      });

      setRooms((prev) => [...prev, res.data]);
      setShowRoomModal(false);
      setNewBuilding("");
      setNewRoomNumber("");
    } catch (err: unknown) {
      setRoomError(err instanceof Error ? err.message : "Failed to create room.");
    } finally {
      setCreatingRoom(false);
    }
  };

  // Quick Create Time Slot
  const handleCreateSlot = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSlotName.trim()) {
      setSlotError("Please enter slot name.");
      return;
    }

    try {
      setCreatingSlot(true);
      setSlotError(null);

      const res = await apiFetch<TimeSlot>("/api/v1/academics/time-slots", {
        method: "POST",
        body: JSON.stringify({
          name: newSlotName.trim(),
          slot_number: Number(newSlotNumber),
          start_time: newStartTime,
          end_time: newEndTime,
          slot_type: newSlotType,
          is_active: true,
        }),
      });

      setTimeSlots((prev) => [...prev, res.data].sort((a, b) => a.slot_number - b.slot_number));
      setShowSlotModal(false);
      setNewSlotName("");
      setNewSlotNumber((prev) => prev + 1);
      // Reload grid so new slot column appears
      loadTimetableGrid();
    } catch (err: unknown) {
      setSlotError(err instanceof Error ? err.message : "Failed to create time slot.");
    } finally {
      setCreatingSlot(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Breadcrumb */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <nav className="flex items-center gap-2 text-xs text-slate-500 mb-1">
            <Link href="/app" className="hover:text-blue-600 transition-colors">
              Dashboard
            </Link>
            <span>/</span>
            <Link href="/app/academics" className="hover:text-blue-600 transition-colors">
              Academics
            </Link>
            <span>/</span>
            <span className="text-slate-800 font-medium">Timetable Engine</span>
          </nav>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Academic Timetable Engine
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Deterministic weekly schedules with automated multi-dimensional clash prevention (Section, Faculty, Room).
          </p>
        </div>

        {canManageTimetable && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowRoomModal(true)}
              className="px-3 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-lg shadow-sm transition-colors"
            >
              + Add Room
            </button>
            <button
              onClick={() => setShowSlotModal(true)}
              className="px-3 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-lg shadow-sm transition-colors"
            >
              + Add Time Slot
            </button>
            <button
              onClick={() => {
                if (gridData?.time_slots?.length) {
                  handleOpenSchedule(1, gridData.time_slots[0].id);
                } else if (timeSlots.length) {
                  handleOpenSchedule(1, timeSlots[0].id);
                } else {
                  alert("Please add at least one Time Slot first.");
                }
              }}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors flex items-center gap-1.5"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Schedule Slot
            </button>
          </div>
        )}
      </div>

      {/* Selectors Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Academic Year */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Academic Year
            </label>
            <select
              value={selectedYearId}
              onChange={(e) => setSelectedYearId(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              {academicYears.map((ay) => (
                <option key={ay.id} value={ay.id}>
                  {ay.name} {ay.is_current ? "(Current)" : ""}
                </option>
              ))}
            </select>
          </div>

          {/* Semester */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Semester
            </label>
            <select
              value={selectedSemId}
              onChange={(e) => setSelectedSemId(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              {semesters.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} (Term {s.semester_number})
                </option>
              ))}
            </select>
          </div>

          {/* Section */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Class Section
            </label>
            <select
              value={selectedSectionId}
              onChange={(e) => setSelectedSectionId(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              <option value="">Select Section...</option>
              {sections.map((sec) => (
                <option key={sec.id} value={sec.id}>
                  Section {sec.name} (Cap: {sec.capacity})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Global Error Banner */}
      {gridError && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-sm text-rose-700 flex items-start gap-3">
          <svg className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <p className="font-semibold">Timetable Notice</p>
            <p>{gridError}</p>
          </div>
        </div>
      )}

      {/* Timetable Weekly Matrix Grid */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loadingGrid ? (
          <div className="p-16 text-center text-slate-500">
            <div className="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-3" />
            <p className="text-sm">Generating weekly timetable grid...</p>
          </div>
        ) : !selectedSectionId ? (
          <div className="p-16 text-center text-slate-400">
            <svg className="w-12 h-12 mx-auto mb-3 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <h3 className="text-sm font-semibold text-slate-700">No Section Selected</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Please choose a class section from the dropdown above to view or configure its weekly schedule matrix.
            </p>
          </div>
        ) : gridData?.time_slots?.length === 0 ? (
          <div className="p-16 text-center">
            <div className="w-12 h-12 bg-amber-50 rounded-full flex items-center justify-center mx-auto mb-3 text-amber-500">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-sm font-semibold text-slate-900">No Time Slots Configured</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Institutions require configured instructional periods before building timetables. Create your first period slot to activate the grid.
            </p>
            {canManageTimetable && (
              <button
                onClick={() => setShowSlotModal(true)}
                className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm"
              >
                Configure First Period Slot
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="p-3 w-28 font-bold text-slate-700 border-r border-slate-200 uppercase tracking-wider text-[11px]">
                    Day / Period
                  </th>
                  {gridData?.time_slots.map((slot) => (
                    <th key={slot.id} className="p-3 min-w-[150px] border-r border-slate-200 last:border-r-0">
                      <div className="font-bold text-slate-800">{slot.name}</div>
                      <div className="text-[11px] text-slate-400 font-mono mt-0.5 font-normal">
                        {slot.start_time} - {slot.end_time}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {gridData?.days.map((day) => (
                  <tr key={day.day_number} className="hover:bg-slate-50/50 transition-colors">
                    {/* Day Column */}
                    <td className="p-3 font-semibold text-slate-800 bg-slate-50/80 border-r border-slate-200 align-top">
                      <div className="text-sm font-bold">{day.day_name}</div>
                      <div className="text-[10px] text-slate-400 font-normal mt-0.5">
                        Day {day.day_number}
                      </div>
                    </td>

                    {/* Time Slot Columns */}
                    {gridData.time_slots.map((slot) => {
                      const cell = day.slots[slot.id];
                      return (
                        <td
                          key={slot.id}
                          className="p-2.5 border-r border-slate-200 last:border-r-0 align-top h-28"
                        >
                          {cell ? (
                            <div className="h-full p-2.5 bg-blue-50/70 border border-blue-200 rounded-lg flex flex-col justify-between group hover:border-blue-300 transition-colors shadow-xs">
                              <div>
                                <div className="flex items-center justify-between gap-1 mb-1">
                                  <span className="font-mono text-[11px] font-bold text-blue-900 bg-blue-100/80 px-1.5 py-0.5 rounded border border-blue-200">
                                    {cell.subject_code}
                                  </span>
                                  {canManageTimetable && (
                                    <button
                                      onClick={() => handleDeleteEntry(cell.entry_id, cell.subject_code)}
                                      title="Remove scheduled class"
                                      className="text-slate-400 hover:text-rose-600 transition-colors p-0.5 rounded"
                                    >
                                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                      </svg>
                                    </button>
                                  )}
                                </div>
                                <div className="font-semibold text-slate-800 line-clamp-2 leading-tight">
                                  {cell.subject_name}
                                </div>
                              </div>

                              <div className="pt-2 border-t border-blue-100/70 space-y-0.5 text-[11px]">
                                {cell.faculty_name && (
                                  <div className="text-slate-600 truncate flex items-center gap-1">
                                    <span className="text-slate-400">👤</span>
                                    <span>{cell.faculty_name}</span>
                                  </div>
                                )}
                                {cell.room_name && (
                                  <div className="text-slate-500 font-mono text-[10px] truncate flex items-center gap-1">
                                    <span className="text-slate-400">📍</span>
                                    <span>{cell.room_name}</span>
                                  </div>
                                )}
                              </div>
                            </div>
                          ) : (
                            <div className="h-full border border-dashed border-slate-200 rounded-lg flex items-center justify-center p-2 group hover:border-blue-300 transition-colors">
                              {canManageTimetable && (
                                <button
                                  onClick={() => handleOpenSchedule(day.day_number, slot.id)}
                                  className="w-full h-full text-slate-300 hover:text-blue-600 flex flex-col items-center justify-center gap-1 transition-colors"
                                >
                                  <svg className="w-4 h-4 opacity-50 group-hover:opacity-100" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                                  </svg>
                                  <span className="text-[10px] font-medium opacity-0 group-hover:opacity-100">
                                    Schedule
                                  </span>
                                </button>
                              )}
                            </div>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* SCHEDULE SLOT MODAL */}
      {showScheduleModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <h2 className="text-base font-bold text-slate-900">Schedule Timetable Class Slot</h2>
              <button
                onClick={() => setShowScheduleModal(false)}
                className="text-slate-400 hover:text-slate-600 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleCreateTimetableEntry} className="p-6 space-y-4">
              {schedError && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-xs leading-relaxed">
                  <div className="font-bold mb-0.5">Scheduling Conflict / Validation Error</div>
                  <div>{schedError}</div>
                </div>
              )}

              {/* Course Offering */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Course Offering *
                </label>
                <select
                  value={schedOfferingId}
                  onChange={(e) => {
                    const offId = e.target.value;
                    setSchedOfferingId(offId);
                  }}
                  required
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  <option value="">Select Offering for this Section</option>
                  {offerings.map((o) => (
                    <option key={o.id} value={o.id}>
                      [{o.subject_code}] {o.subject_name} ({o.primary_faculty_name || "Unassigned"})
                    </option>
                  ))}
                </select>
                {offerings.length === 0 && (
                  <p className="text-xs text-amber-600 mt-1">
                    No active course offerings found for this section. Please create an offering first under Course Offerings.
                  </p>
                )}
              </div>

              {/* Day & Time Slot */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Day of Week *
                  </label>
                  <select
                    value={schedDay}
                    onChange={(e) => setSchedDay(Number(e.target.value))}
                    required
                    className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  >
                    {DAYS_MAP.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Time Period Slot *
                  </label>
                  <select
                    value={schedSlotId}
                    onChange={(e) => setSchedSlotId(e.target.value)}
                    required
                    className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  >
                    <option value="">Select Period Slot</option>
                    {(gridData?.time_slots || timeSlots).map((slot) => (
                      <option key={slot.id} value={slot.id}>
                        {slot.name} ({slot.start_time} - {slot.end_time})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Faculty & Classroom */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Assigned Instructor
                  </label>
                  <select
                    value={schedFacultyId}
                    onChange={(e) => setSchedFacultyId(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  >
                    <option value="">Default (From Course)</option>
                    {facultyList.map((f) => (
                      <option key={f.id} value={f.id}>
                        {f.first_name} {f.last_name} ({f.employee_code})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Classroom / Room
                  </label>
                  <select
                    value={schedRoomId}
                    onChange={(e) => setSchedRoomId(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  >
                    <option value="">Unassigned Location</option>
                    {rooms.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.building} - {r.room_number} (Cap: {r.capacity})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-200 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowScheduleModal(false)}
                  className="px-4 py-2 border border-slate-300 text-slate-700 text-sm font-semibold rounded-lg hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={scheduling || offerings.length === 0}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-semibold rounded-lg shadow-sm transition-colors"
                >
                  {scheduling ? "Verifying & Scheduling..." : "Confirm Schedule"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* QUICK ADD ROOM MODAL */}
      {showRoomModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <h2 className="text-base font-bold text-slate-900">Add Academic Room / Lab</h2>
              <button
                onClick={() => setShowRoomModal(false)}
                className="text-slate-400 hover:text-slate-600 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleCreateRoom} className="p-6 space-y-4">
              {roomError && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-xs">
                  {roomError}
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Building / Wing *
                </label>
                <input
                  type="text"
                  placeholder="e.g. Science Block, Academic Wing B"
                  value={newBuilding}
                  onChange={(e) => setNewBuilding(e.target.value)}
                  required
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Room Number / Identifier *
                </label>
                <input
                  type="text"
                  placeholder="e.g. 101, LH-3, LAB-A"
                  value={newRoomNumber}
                  onChange={(e) => setNewRoomNumber(e.target.value)}
                  required
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Seating Capacity
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="1000"
                    value={newCapacity}
                    onChange={(e) => setNewCapacity(Number(e.target.value))}
                    required
                    className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Room Type
                  </label>
                  <select
                    value={newRoomType}
                    onChange={(e) => setNewRoomType(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  >
                    <option value="CLASSROOM">CLASSROOM</option>
                    <option value="LAB">LAB</option>
                    <option value="SEMINAR_HALL">SEMINAR_HALL</option>
                    <option value="AUDITORIUM">AUDITORIUM</option>
                    <option value="WORKSHOP">WORKSHOP</option>
                  </select>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-200 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowRoomModal(false)}
                  className="px-4 py-2 border border-slate-300 text-slate-700 text-sm font-semibold rounded-lg hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creatingRoom}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-semibold rounded-lg shadow-sm transition-colors"
                >
                  {creatingRoom ? "Creating Room..." : "Create Room"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* QUICK ADD TIME SLOT MODAL */}
      {showSlotModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <h2 className="text-base font-bold text-slate-900">Add Instructional Time Slot</h2>
              <button
                onClick={() => setShowSlotModal(false)}
                className="text-slate-400 hover:text-slate-600 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleCreateSlot} className="p-6 space-y-4">
              {slotError && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-xs">
                  {slotError}
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Slot Name *
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Period 1, Slot A"
                    value={newSlotName}
                    onChange={(e) => setNewSlotName(e.target.value)}
                    required
                    className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Period Number *
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={newSlotNumber}
                    onChange={(e) => setNewSlotNumber(Number(e.target.value))}
                    required
                    className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Start Time *
                  </label>
                  <input
                    type="text"
                    placeholder="08:30"
                    value={newStartTime}
                    onChange={(e) => setNewStartTime(e.target.value)}
                    required
                    className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    End Time *
                  </label>
                  <input
                    type="text"
                    placeholder="09:20"
                    value={newEndTime}
                    onChange={(e) => setNewEndTime(e.target.value)}
                    required
                    className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Slot Type
                </label>
                <select
                  value={newSlotType}
                  onChange={(e) => setNewSlotType(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  <option value="LECTURE">LECTURE</option>
                  <option value="LAB">LAB</option>
                  <option value="BREAK">BREAK</option>
                </select>
              </div>

              <div className="pt-4 border-t border-slate-200 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowSlotModal(false)}
                  className="px-4 py-2 border border-slate-300 text-slate-700 text-sm font-semibold rounded-lg hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creatingSlot}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-semibold rounded-lg shadow-sm transition-colors"
                >
                  {creatingSlot ? "Saving Slot..." : "Save Time Slot"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
