"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { campusService } from "@/services/campus.service";
import {
  CampusEventItem,
  EventAttendanceItem,
  EventAttendanceStatus,
  EventAttendanceSummary,
} from "@/types/campus";
import { useAuth } from "@/lib/auth-context";
import { calculateEventAttendanceRate } from "@/services/campus-calculator";
import {
  CheckSquare,
  Users,
  Search,
  CheckCircle2,
  XCircle,
  Clock,
  Save,
  AlertCircle,
  Filter,
  CheckCheck,
  Calendar,
  MapPin,
  HelpCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";

export default function CampusEventAttendancePage() {
  const { user, hasPermission } = useAuth();
  const [events, setEvents] = useState<CampusEventItem[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Local Attendance State
  const [roster, setRoster] = useState<EventAttendanceItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  const canManageAttendance =
    hasPermission("campus.manage_event_attendance") ||
    hasPermission("campus.manage_events") ||
    hasPermission("*");

  // Load events list first
  useEffect(() => {
    async function init() {
      try {
        setLoading(true);
        const res = await campusService.getEvents();
        if (res.success && res.data) {
          // Filter to events that track attendance
          const trackingEvents = res.data.filter((e) => e.requiresAttendance);
          setEvents(trackingEvents);
          if (trackingEvents.length > 0) {
            setSelectedEventId(trackingEvents[0].id);
          }
        }
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  // Load attendance when selectedEventId changes
  useEffect(() => {
    if (!selectedEventId) return;
    async function loadRoster() {
      try {
        setLoading(true);
        setSaveSuccess(false);
        const res = await campusService.getEventAttendance(selectedEventId);
        if (res.success && res.data) {
          setRoster(res.data.items);
        }
      } finally {
        setLoading(false);
      }
    }
    loadRoster();
  }, [selectedEventId]);

  const selectedEvent = events.find((e) => e.id === selectedEventId);

  // Status Counts and Centralized Calculation
  const presentCount = roster.filter((r) => r.status === "PRESENT").length;
  const absentCount = roster.filter((r) => r.status === "ABSENT").length;
  const excusedCount = roster.filter((r) => r.status === "EXCUSED").length;
  const pendingCount = roster.filter((r) => r.status === "PENDING").length;

  const attendanceRate = calculateEventAttendanceRate(presentCount, roster.length);

  // Interactive marking handler
  const setAttendeeStatus = (studentId: string, status: EventAttendanceStatus) => {
    setRoster((prev) =>
      prev.map((item) =>
        item.studentId === studentId
          ? {
              ...item,
              status,
              markedAt: new Date().toLocaleTimeString(),
              markedBy: user?.first_name || "Coordinator",
            }
          : item
      )
    );
    setSaveSuccess(false);
  };

  // Bulk actions
  const handleBulkMark = (status: EventAttendanceStatus) => {
    setRoster((prev) =>
      prev.map((item) => ({
        ...item,
        status,
        markedAt: new Date().toLocaleTimeString(),
        markedBy: user?.first_name || "Coordinator",
      }))
    );
    setSaveSuccess(false);
  };

  // Save changes to service
  const handleSave = async () => {
    if (!selectedEventId) return;
    try {
      setSaving(true);
      setError(null);
      const updates = roster.map((r) => ({
        studentId: r.studentId,
        status: r.status,
        remarks: r.remarks,
      }));

      const res = await campusService.markEventAttendance(
        selectedEventId,
        updates,
        user?.first_name || "Coordinator"
      );

      if (res.success) {
        setSaveSuccess(true);
      } else {
        setError(res.error || "Failed to save attendance.");
      }
    } catch (e: any) {
      setError(e.message || "An unexpected error occurred.");
    } finally {
      setSaving(false);
    }
  };

  // Filtered Roster
  const filteredRoster = useMemo(() => {
    return roster.filter((r) => {
      const matchStatus = statusFilter === "ALL" || r.status === statusFilter;
      const matchSearch =
        searchQuery === "" ||
        r.studentName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.rollNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.department.toLowerCase().includes(searchQuery.toLowerCase());
      return matchStatus && matchSearch;
    });
  }, [roster, statusFilter, searchQuery]);

  return (
    <div className="space-y-6 animate-fade-in pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <Link href="/app/campus" className="text-xs text-slate-400 hover:text-indigo-400">
              Campus Hub
            </Link>
            <span className="text-slate-600">/</span>
            <span className="text-xs text-slate-200 font-semibold">Event Attendance</span>
          </div>
          <h1 className="mt-1 text-2xl font-black tracking-tight text-white flex items-center gap-2.5">
            <CheckSquare className="h-6 w-6 text-indigo-400" />
            Event Attendance Management
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Interactive verification console for event coordinators. Mark physical hall attendance and audit participant yields.
          </p>
        </div>

        {canManageAttendance && (
          <Button
            variant="primary"
            size="sm"
            isLoading={saving}
            onClick={handleSave}
            leftIcon={<Save className="h-4 w-4" />}
            className="bg-indigo-600 hover:bg-indigo-500 shadow-md shadow-indigo-600/30"
          >
            Save Attendance Ledger
          </Button>
        )}
      </div>

      {saveSuccess && (
        <div className="p-3.5 rounded-xl border border-emerald-500/30 bg-emerald-950/20 text-emerald-300 text-xs flex items-center justify-between">
          <span className="flex items-center gap-2 font-medium">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            Attendance ledger has been recorded and synchronized with participant profiles.
          </span>
          <button onClick={() => setSaveSuccess(false)} className="text-emerald-400 hover:text-white">
            Dismiss
          </button>
        </div>
      )}

      {error && (
        <div className="p-3.5 rounded-xl border border-rose-500/30 bg-rose-950/20 text-rose-300 text-xs flex items-center gap-2 font-medium">
          <AlertCircle className="h-4 w-4 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Event Selection Bar */}
      <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex-1 max-w-lg">
          <label className="text-xs font-semibold text-slate-300 block mb-1">Select Event:</label>
          <select
            value={selectedEventId}
            onChange={(e) => setSelectedEventId(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500 font-medium"
          >
            {events.map((e) => (
              <option key={e.id} value={e.id}>
                {e.title} ({e.startDate} • {e.venue})
              </option>
            ))}
          </select>
        </div>

        {selectedEvent && (
          <div className="flex items-center gap-4 text-xs text-slate-400 pt-2 md:pt-0">
            <div className="flex items-center gap-1.5">
              <Calendar className="h-4 w-4 text-slate-500" />
              <span>{selectedEvent.startDate}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <MapPin className="h-4 w-4 text-slate-500" />
              <span>{selectedEvent.venue}</span>
            </div>
          </div>
        )}
      </div>

      {/* Centralized Attendance Rate Summary Banner (Section 12) */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60">
          <span className="text-[10px] text-slate-500 uppercase font-mono">Registered</span>
          <div className="text-2xl font-bold font-mono text-white mt-1">{roster.length}</div>
          <span className="text-[10px] text-slate-400 mt-1 block">Total enrolled roster</span>
        </div>

        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60">
          <span className="text-[10px] text-slate-500 uppercase font-mono">Present</span>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">{presentCount}</div>
          <span className="text-[10px] text-slate-400 mt-1 block">Verified in hall</span>
        </div>

        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60">
          <span className="text-[10px] text-slate-500 uppercase font-mono">Absent</span>
          <div className="text-2xl font-bold font-mono text-rose-400 mt-1">{absentCount}</div>
          <span className="text-[10px] text-slate-400 mt-1 block">Unexcused / Missing</span>
        </div>

        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60">
          <span className="text-[10px] text-slate-500 uppercase font-mono">Attendance Rate</span>
          <div className="text-2xl font-bold font-mono text-indigo-400 mt-1">{attendanceRate}%</div>
          <span className="text-[10px] text-slate-400 mt-1 block">calculateEventAttendanceRate()</span>
        </div>
      </div>

      {/* Interactive Controls & Bulk Marking Toolbar */}
      <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3 flex-1">
          {/* Search box */}
          <div className="relative w-full sm:w-64">
            <Search className="h-3.5 w-3.5 text-slate-500 absolute left-3 top-3" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search participant or roll number..."
              className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-slate-400">Filter:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-white"
            >
              <option value="ALL">All Statuses</option>
              <option value="PRESENT">Present ({presentCount})</option>
              <option value="ABSENT">Absent ({absentCount})</option>
              <option value="EXCUSED">Excused ({excusedCount})</option>
              <option value="PENDING">Pending ({pendingCount})</option>
            </select>
          </div>
        </div>

        {/* Bulk Action Buttons for Coordinator */}
        {canManageAttendance && (
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => handleBulkMark("PRESENT")}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-600/30 transition-colors flex items-center gap-1.5"
            >
              <CheckCheck className="h-3.5 w-3.5" /> Mark All Present
            </button>
            <button
              onClick={() => handleBulkMark("ABSENT")}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-rose-600/20 text-rose-300 border border-rose-500/30 hover:bg-rose-600/30 transition-colors flex items-center gap-1.5"
            >
              <XCircle className="h-3.5 w-3.5" /> Mark All Absent
            </button>
            <button
              onClick={() => handleBulkMark("PENDING")}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 text-slate-400 hover:text-white transition-colors"
            >
              Clear
            </button>
          </div>
        )}
      </div>

      {/* Participant Roster Table */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/50 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="p-3.5">Participant</th>
                <th className="p-3.5">Roll Number</th>
                <th className="p-3.5">Department</th>
                <th className="p-3.5">Current Status</th>
                <th className="p-3.5">Marked Details</th>
                <th className="p-3.5 text-right">Quick Toggle</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredRoster.map((item) => (
                <tr key={item.studentId} className="hover:bg-slate-800/30 transition-colors">
                  <td className="p-3.5 font-bold text-white">{item.studentName}</td>
                  <td className="p-3.5 font-mono text-slate-300">{item.rollNumber}</td>
                  <td className="p-3.5 text-slate-400">{item.department}</td>
                  <td className="p-3.5">
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                        item.status === "PRESENT"
                          ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                          : item.status === "ABSENT"
                          ? "bg-rose-500/20 text-rose-300 border-rose-500/30"
                          : item.status === "EXCUSED"
                          ? "bg-purple-500/20 text-purple-300 border-purple-500/30"
                          : "bg-slate-800 text-slate-400 border-slate-700"
                      }`}
                    >
                      {item.status}
                    </span>
                  </td>
                  <td className="p-3.5 text-slate-500 font-mono text-[11px]">
                    {item.markedAt ? `${item.markedAt} (${item.markedBy || "Admin"})` : "—"}
                  </td>
                  <td className="p-3.5 text-right">
                    {canManageAttendance ? (
                      <div className="inline-flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
                        <button
                          type="button"
                          onClick={() => setAttendeeStatus(item.studentId, "PRESENT")}
                          className={`px-2 py-1 rounded text-[10px] font-bold transition-colors cursor-pointer ${
                            item.status === "PRESENT"
                              ? "bg-emerald-600 text-white"
                              : "text-slate-400 hover:text-emerald-300 hover:bg-slate-900"
                          }`}
                        >
                          Present
                        </button>
                        <button
                          type="button"
                          onClick={() => setAttendeeStatus(item.studentId, "ABSENT")}
                          className={`px-2 py-1 rounded text-[10px] font-bold transition-colors cursor-pointer ${
                            item.status === "ABSENT"
                              ? "bg-rose-600 text-white"
                              : "text-slate-400 hover:text-rose-300 hover:bg-slate-900"
                          }`}
                        >
                          Absent
                        </button>
                        <button
                          type="button"
                          onClick={() => setAttendeeStatus(item.studentId, "EXCUSED")}
                          className={`px-2 py-1 rounded text-[10px] font-bold transition-colors cursor-pointer ${
                            item.status === "EXCUSED"
                              ? "bg-purple-600 text-white"
                              : "text-slate-400 hover:text-purple-300 hover:bg-slate-900"
                          }`}
                        >
                          Excused
                        </button>
                      </div>
                    ) : (
                      <span className="text-slate-600 text-[11px]">Read only</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
