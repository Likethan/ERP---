"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { campusService } from "@/services/campus.service";
import {
  CampusEventItem,
  EventRegistrationItem,
  EventAttendanceItem,
  EventAttendanceSummary,
  AnnouncementItem,
} from "@/types/campus";
import { useAuth } from "@/lib/auth-context";
import { calculateEventAttendanceRate } from "@/services/campus-calculator";
import {
  PartyPopper,
  Calendar,
  Clock,
  MapPin,
  Users,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ArrowLeft,
  ChevronRight,
  FileText,
  History,
  ShieldCheck,
  UserCheck,
  Download,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";

interface EventDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function EventDetailPage({ params }: EventDetailPageProps) {
  const resolvedParams = use(params);
  const eventId = resolvedParams.id;
  const { user, hasPermission } = useAuth();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [event, setEvent] = useState<CampusEventItem | null>(null);
  const [registrations, setRegistrations] = useState<EventRegistrationItem[]>(
    [],
  );
  const [attendance, setAttendance] = useState<{
    items: EventAttendanceItem[];
    summary: EventAttendanceSummary;
  } | null>(null);
  const [announcements, setAnnouncements] = useState<AnnouncementItem[]>([]);

  const [activeTab, setActiveTab] = useState<
    | "overview"
    | "schedule"
    | "audience"
    | "registrations"
    | "attendance"
    | "announcements"
    | "timeline"
  >("overview");

  // Actions
  const [publishing, setPublishing] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [cancelModalOpen, setCancelModalOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState("");
  const [registering, setRegistering] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const canPublish =
    hasPermission("campus.publish_events") || hasPermission("*");
  const canManage = hasPermission("campus.manage_events") || hasPermission("*");

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [evRes, regRes, attRes, ancRes] = await Promise.all([
        campusService.getEventById(eventId),
        campusService.getEventRegistrations(eventId),
        campusService.getEventAttendance(eventId),
        campusService.getAnnouncements(),
      ]);

      if (evRes.success && evRes.data) {
        setEvent(evRes.data);
      } else {
        setError(evRes.error || "Event not found");
      }

      if (regRes.success && regRes.data) {
        setRegistrations(regRes.data);
      }

      if (attRes.success && attRes.data) {
        setAttendance(attRes.data);
      }

      if (ancRes.success && ancRes.data) {
        setAnnouncements(
          ancRes.data.filter(
            (a) =>
              a.title
                .toLowerCase()
                .includes(evRes.data?.title.toLowerCase() || "") ||
              a.category === "CLUB",
          ),
        );
      }
    } catch (e: any) {
      setError(e.message || "Failed to load event data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [eventId]);

  const handlePublish = async () => {
    try {
      setPublishing(true);
      await campusService.publishEvent(
        eventId,
        user?.first_name || "Administrator",
      );
      setActionMessage(
        "Event has been published and registrations are active!",
      );
      loadData();
    } finally {
      setPublishing(false);
    }
  };

  const handleCancelEvent = async () => {
    try {
      setCancelling(true);
      await campusService.cancelEvent(
        eventId,
        cancelReason,
        user?.first_name || "Administrator",
      );
      setCancelModalOpen(false);
      setActionMessage("Event has been cancelled.");
      loadData();
    } finally {
      setCancelling(false);
    }
  };

  const handleStudentRegister = async () => {
    if (!user) return;
    try {
      setRegistering(true);
      const res = await campusService.registerForEvent(eventId, {
        id: user.id,
        name: `${user.first_name} ${user.last_name}`,
        rollNumber: "CS23B101",
        email: user.email,
        department: "Computer Science & Engineering",
        program: "B.Tech Computer Science",
        semester: 5,
      });

      if (res.success) {
        setActionMessage(
          `Registration Confirmed! Your Pass is #${res.data.ticketCode}`,
        );
        loadData();
      } else {
        alert(res.error || "Registration failed");
      }
    } finally {
      setRegistering(false);
    }
  };

  const handleMarkAttendanceQuick = async (
    studentId: string,
    status: "PRESENT" | "ABSENT",
  ) => {
    await campusService.markEventAttendance(
      eventId,
      [{ studentId, status }],
      user?.first_name || "Coordinator",
    );
    loadData();
  };

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-slate-400">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
          <span className="text-xs">Loading event specifications...</span>
        </div>
      </div>
    );
  }

  if (error || !event) {
    return (
      <div className="p-8 text-center space-y-4 rounded-2xl border border-slate-800 bg-slate-900/60 max-w-xl mx-auto my-12">
        <AlertTriangle className="h-10 w-10 text-rose-400 mx-auto" />
        <h2 className="text-base font-bold text-white">Event Not Found</h2>
        <p className="text-xs text-slate-400">
          {error || "Requested event does not exist."}
        </p>
        <Link href="/app/campus/events">
          <Button variant="outline" size="sm">
            Back to Events Directory
          </Button>
        </Link>
      </div>
    );
  }

  const isUserRegistered = registrations.some(
    (r) => r.studentId === user?.id && r.status !== "CANCELLED",
  );

  const confirmedCount = registrations.filter(
    (r) => r.status === "CONFIRMED" || r.status === "ATTENDED",
  ).length;
  const waitlistedCount = registrations.filter(
    (r) => r.status === "WAITLISTED",
  ).length;
  const cancelledCount = registrations.filter(
    (r) => r.status === "CANCELLED",
  ).length;

  const attendanceRate = attendance
    ? calculateEventAttendanceRate(
        attendance.summary.presentCount,
        attendance.summary.totalRegistered,
      )
    : 0;

  return (
    <div className="space-y-6 animate-fade-in pb-16">
      {/* Breadcrumb & Navigation */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <Link
          href="/app/campus/events"
          className="text-xs text-slate-400 hover:text-white inline-flex items-center gap-1.5 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Events DataGrid
        </Link>

        <div className="flex items-center gap-2">
          {event.status === "REGISTRATION_OPEN" && !isUserRegistered && (
            <Button
              variant="primary"
              size="sm"
              isLoading={registering}
              onClick={handleStudentRegister}
              className="bg-emerald-600 hover:bg-emerald-500 shadow-md shadow-emerald-600/30"
            >
              Register for Event
            </Button>
          )}

          {isUserRegistered && (
            <span className="text-xs font-semibold px-3 py-1 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5" /> Registered
            </span>
          )}

          {canPublish &&
            (event.status === "DRAFT" ||
              event.status === "PENDING_APPROVAL") && (
              <Button
                variant="primary"
                size="sm"
                isLoading={publishing}
                onClick={handlePublish}
                className="bg-indigo-600 hover:bg-indigo-500"
              >
                Publish Event
              </Button>
            )}

          {canManage &&
            event.status !== "CANCELLED" &&
            event.status !== "COMPLETED" && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCancelModalOpen(true)}
                className="border-rose-900/60 text-rose-400 hover:bg-rose-950/40"
              >
                Cancel Event
              </Button>
            )}
        </div>
      </div>

      {actionMessage && (
        <div className="p-3.5 rounded-xl border border-emerald-500/30 bg-emerald-950/20 text-emerald-300 text-xs flex items-center justify-between">
          <span>{actionMessage}</span>
          <button
            onClick={() => setActionMessage(null)}
            className="text-emerald-400 hover:text-white"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Polish Event Header Card */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded bg-indigo-500/20 px-2.5 py-0.5 text-xs font-mono font-bold text-indigo-300 border border-indigo-500/30">
            {event.category}
          </span>
          <span
            className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold border ${
              event.status === "REGISTRATION_OPEN"
                ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                : event.status === "CANCELLED"
                  ? "bg-rose-950/40 text-rose-400 border-rose-900/50"
                  : "bg-slate-800 text-slate-300 border-slate-700"
            }`}
          >
            {event.status.replace("_", " ")}
          </span>
          <span className="text-slate-600">•</span>
          <span className="text-xs text-slate-400">
            Organized by{" "}
            <strong className="text-slate-200">{event.organizer}</strong>
          </span>
        </div>

        <h1 className="text-xl sm:text-2xl font-black text-white tracking-tight">
          {event.title}
        </h1>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 text-xs text-slate-300">
          <div className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
            <Calendar className="h-4 w-4 text-indigo-400 shrink-0" />
            <div>
              <span className="text-slate-500 block text-[10px]">Date</span>
              <span>
                {event.startDate} to {event.endDate}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
            <Clock className="h-4 w-4 text-indigo-400 shrink-0" />
            <div>
              <span className="text-slate-500 block text-[10px]">Time</span>
              <span>
                {event.startTime} - {event.endTime}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80">
            <MapPin className="h-4 w-4 text-indigo-400 shrink-0" />
            <div className="truncate">
              <span className="text-slate-500 block text-[10px]">Venue</span>
              <span className="truncate">{event.venue}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 7 Tabs Bar */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-800 pb-3">
        {[
          { id: "overview", label: "Overview" },
          { id: "schedule", label: "Schedule" },
          { id: "audience", label: "Audience" },
          {
            id: "registrations",
            label: `Registrations (${registrations.length})`,
          },
          { id: "attendance", label: "Attendance" },
          {
            id: "announcements",
            label: `Announcements (${announcements.length})`,
          },
          { id: "timeline", label: "Audit Timeline" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-3.5 py-1.5 text-xs font-semibold rounded-xl transition-all cursor-pointer ${
              activeTab === tab.id
                ? "bg-indigo-600 text-white shadow-sm shadow-indigo-600/30"
                : "bg-slate-900/60 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB: OVERVIEW */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-5">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 space-y-3">
              <h3 className="text-sm font-bold text-white">Event Synopsis</h3>
              <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">
                {event.description}
              </p>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 space-y-4">
              <h3 className="text-sm font-bold text-white">
                Venue Infrastructure Details
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase">
                    Building
                  </span>
                  <div className="font-bold text-white mt-0.5">
                    {event.venueDetails?.building || "Main Campus"}
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase">
                    Room
                  </span>
                  <div className="font-bold text-white mt-0.5">
                    {event.venueDetails?.roomNumber || "SAC-01"}
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase">
                    Certified Capacity
                  </span>
                  <div className="font-bold text-white mt-0.5">
                    {event.capacity} seats
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase">
                    A/V & Projection
                  </span>
                  <div className="font-bold text-emerald-400 mt-0.5">
                    Equipped
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-5">
            {/* Quick Registration Status Card */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 space-y-3">
              <h3 className="text-sm font-bold text-white">
                Capacity & Registration
              </h3>
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Total Capacity</span>
                  <span className="font-mono font-bold text-white">
                    {event.capacity}
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Registered</span>
                  <span className="font-mono font-bold text-indigo-400">
                    {event.registeredCount}
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Waitlist</span>
                  <span className="font-mono font-bold text-amber-400">
                    {event.waitlistCount}
                  </span>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className="h-full bg-indigo-500 rounded-full"
                    style={{
                      width: `${Math.min(100, Math.round((event.registeredCount / event.capacity) * 100))}%`,
                    }}
                  />
                </div>
                <span className="text-[11px] text-slate-500 block text-right">
                  {Math.round((event.registeredCount / event.capacity) * 100)}%
                  capacity allocated
                </span>
              </div>
            </div>

            {/* Attendance Snapshot */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-5 space-y-3">
              <h3 className="text-sm font-bold text-white">
                Attendance Snapshot
              </h3>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-400">Requires Attendance</span>
                  <span className="font-bold text-emerald-400">
                    {event.requiresAttendance ? "YES" : "NO"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Verified Attendees</span>
                  <span className="font-mono font-bold text-white">
                    {event.attendedCount}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Attendance Yield</span>
                  <span className="font-mono font-bold text-emerald-400">
                    {attendanceRate}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB: SCHEDULE */}
      {activeTab === "schedule" && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 space-y-4">
          <h3 className="text-sm font-bold text-white">
            Full Event Schedule Breakdown
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-mono">
                Start Time
              </span>
              <div className="text-base font-bold text-white mt-1">
                {event.startDate}
              </div>
              <div className="text-slate-400">{event.startTime}</div>
            </div>
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-mono">
                End Time
              </span>
              <div className="text-base font-bold text-white mt-1">
                {event.endDate}
              </div>
              <div className="text-slate-400">{event.endTime}</div>
            </div>
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-mono">
                Registration Window
              </span>
              <div className="text-base font-bold text-white mt-1">
                {event.registrationOpenDate || "Open"}
              </div>
              <div className="text-slate-400">
                Closes: {event.registrationCloseDate || "N/A"}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB: AUDIENCE */}
      {activeTab === "audience" && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 space-y-4">
          <h3 className="text-sm font-bold text-white">
            Target Audience Scope
          </h3>
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Audience Classification:</span>
              <span className="font-bold text-white font-mono">
                {event.targetAudience.type}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Estimated Reach:</span>
              <span className="font-bold text-indigo-400 font-mono">
                ~{event.targetAudience.estimatedCount} users
              </span>
            </div>
            {event.targetAudience.customDescription && (
              <p className="text-slate-400 pt-2 border-t border-slate-800">
                {event.targetAudience.customDescription}
              </p>
            )}
          </div>
        </div>
      )}

      {/* TAB: REGISTRATIONS */}
      {activeTab === "registrations" && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
            <div>
              <h3 className="text-sm font-bold text-white">
                Registered Participants Roster
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Confirmed: {confirmedCount} • Waitlisted: {waitlistedCount} •
                Cancelled: {cancelledCount}
              </p>
            </div>
            <Link
              href="/app/campus/registrations"
              className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold"
            >
              All Campus Registrations →
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                  <th className="p-3">Participant</th>
                  <th className="p-3">Roll No</th>
                  <th className="p-3">Department</th>
                  <th className="p-3">Ticket Pass</th>
                  <th className="p-3">Registration Date</th>
                  <th className="p-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {registrations.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-800/30">
                    <td className="p-3 font-semibold text-white">
                      {r.studentName}
                    </td>
                    <td className="p-3 font-mono text-slate-300">
                      {r.rollNumber}
                    </td>
                    <td className="p-3 text-slate-400">{r.department}</td>
                    <td className="p-3 font-mono text-indigo-400 font-bold">
                      {r.ticketCode}
                    </td>
                    <td className="p-3 text-slate-500 font-mono">
                      {r.registrationDate}
                    </td>
                    <td className="p-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                          r.status === "CONFIRMED"
                            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                            : r.status === "WAITLISTED"
                              ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                              : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {r.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB: ATTENDANCE */}
      {activeTab === "attendance" && (
        <div className="space-y-6">
          {/* Summary Box */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60">
              <span className="text-[10px] text-slate-500 uppercase font-mono">
                Registered
              </span>
              <div className="text-xl font-bold font-mono text-white mt-1">
                {attendance?.summary.totalRegistered || 0}
              </div>
            </div>
            <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60">
              <span className="text-[10px] text-slate-500 uppercase font-mono">
                Present
              </span>
              <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
                {attendance?.summary.presentCount || 0}
              </div>
            </div>
            <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60">
              <span className="text-[10px] text-slate-500 uppercase font-mono">
                Absent
              </span>
              <div className="text-xl font-bold font-mono text-rose-400 mt-1">
                {attendance?.summary.absentCount || 0}
              </div>
            </div>
            <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60">
              <span className="text-[10px] text-slate-500 uppercase font-mono">
                Attendance Rate
              </span>
              <div className="text-xl font-bold font-mono text-indigo-400 mt-1">
                {attendance?.summary.attendanceRate || 0}%
              </div>
            </div>
          </div>

          {/* Attendee Roster */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white">
                Event Attendance Roster
              </h3>
              <Link
                href="/app/campus/attendance"
                className="text-xs text-indigo-400 hover:text-indigo-300"
              >
                Open Full Attendance Console →
              </Link>
            </div>

            <div className="divide-y divide-slate-800">
              {attendance?.items.map((item) => (
                <div
                  key={item.id}
                  className="py-3 flex items-center justify-between gap-4 text-xs"
                >
                  <div>
                    <span className="font-semibold text-white block">
                      {item.studentName}
                    </span>
                    <span className="text-slate-500 font-mono text-[11px]">
                      {item.rollNumber} • {item.department}
                    </span>
                  </div>

                  <div className="flex items-center gap-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        item.status === "PRESENT"
                          ? "bg-emerald-500/20 text-emerald-300"
                          : item.status === "ABSENT"
                            ? "bg-rose-500/20 text-rose-300"
                            : "bg-slate-800 text-slate-400"
                      }`}
                    >
                      {item.status}
                    </span>

                    {canManage && (
                      <div className="flex items-center gap-1.5">
                        <button
                          onClick={() =>
                            handleMarkAttendanceQuick(item.studentId, "PRESENT")
                          }
                          className="px-2 py-1 rounded bg-emerald-600/30 text-emerald-300 hover:bg-emerald-600/50 text-[10px] font-semibold"
                        >
                          Present
                        </button>
                        <button
                          onClick={() =>
                            handleMarkAttendanceQuick(item.studentId, "ABSENT")
                          }
                          className="px-2 py-1 rounded bg-rose-600/30 text-rose-300 hover:bg-rose-600/50 text-[10px] font-semibold"
                        >
                          Absent
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB: ANNOUNCEMENTS */}
      {activeTab === "announcements" && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 space-y-4">
          <h3 className="text-sm font-bold text-white">
            Linked Announcements & Advisories
          </h3>
          <div className="space-y-3">
            {announcements.length > 0 ? (
              announcements.map((a) => (
                <Link
                  key={a.id}
                  href={`/app/campus/announcements/${a.id}`}
                  className="block p-4 rounded-xl border border-slate-800 bg-slate-950/60 hover:border-slate-700 transition-colors"
                >
                  <div className="text-xs font-bold text-white">{a.title}</div>
                  <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                    {a.content}
                  </p>
                  <div className="mt-2 text-[10px] text-slate-500 font-mono">
                    Published: {a.publishDate} by {a.publisher}
                  </div>
                </Link>
              ))
            ) : (
              <div className="text-xs text-slate-500 py-6 text-center">
                No specific announcements linked to this event yet.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB: TIMELINE */}
      {activeTab === "timeline" && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <History className="h-4 w-4 text-indigo-400" />
            Audit & Governance Timeline
          </h3>

          <div className="space-y-4 border-l border-slate-800 ml-3 pl-4">
            {event.timeline.map((entry) => (
              <div key={entry.id} className="relative space-y-1 text-xs">
                <div className="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full bg-indigo-500 ring-4 ring-slate-950" />
                <div className="font-bold text-white">{entry.action}</div>
                <div className="text-slate-400">Actor: {entry.actor}</div>
                {entry.details && (
                  <p className="text-slate-400 text-[11px]">{entry.details}</p>
                )}
                <div className="text-[10px] text-slate-500 font-mono">
                  {entry.timestamp}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cancel Modal */}
      <Dialog
        open={cancelModalOpen}
        onClose={() => setCancelModalOpen(false)}
        title="Cancel Event Formal Notice"
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-300">
            Please enter a formal reason for cancelling this event:
          </p>
          <textarea
            value={cancelReason}
            onChange={(e) => setCancelReason(e.target.value)}
            rows={3}
            placeholder="Cancellation details..."
            className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-white"
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setCancelModalOpen(false)}
            >
              Back
            </Button>
            <Button
              variant="destructive"
              size="sm"
              isLoading={cancelling}
              onClick={handleCancelEvent}
            >
              Confirm Cancellation
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
