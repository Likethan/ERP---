"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type { CampusEvent, EventRegistration, EventQRToken } from "@campusos/types";

export default function EventDetailPage() {
  const params = useParams();
  const router = useRouter();
  const eventId = params.id as string;
  const { hasPermission } = useAuth();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [event, setEvent] = useState<CampusEvent | null>(null);
  const [attendees, setAttendees] = useState<EventRegistration[]>([]);
  const [qrTokenData, setQrTokenData] = useState<EventQRToken | null>(null);

  // Actions
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Check-in input
  const [checkInCode, setCheckInCode] = useState("");

  const canManageEvent = hasPermission("events:update");
  const canManageAttendance = hasPermission("events:manage_attendance");

  const loadEventData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [evtRes, attRes] = await Promise.all([
        apiFetch<CampusEvent>(`/api/v1/events/${eventId}`),
        canManageAttendance
          ? apiFetch<{ items: EventRegistration[] }>(`/api/v1/events/${eventId}/attendees`).catch(() => ({ data: { items: [] } }))
          : Promise.resolve({ data: { items: [] } }),
      ]);

      setEvent(evtRes.data);
      setAttendees(attRes.data.items || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load event.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (eventId) {
      loadEventData();
    }
  }, [eventId]);

  const handleRegister = async () => {
    try {
      setActionLoading(true);
      setActionError(null);
      await apiFetch(`/api/v1/events/${eventId}/register`, { method: "POST" });
      setActionSuccess("Successfully registered for this event!");
      loadEventData();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : "Failed to register for event.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancelRegistration = async () => {
    if (!confirm("Are you sure you want to cancel your event registration?")) return;
    try {
      setActionLoading(true);
      setActionError(null);
      await apiFetch(`/api/v1/events/${eventId}/cancel-registration`, { method: "POST" });
      setActionSuccess("Registration cancelled.");
      loadEventData();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : "Failed to cancel registration.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleCheckIn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!checkInCode.trim()) return;

    try {
      setActionLoading(true);
      setActionError(null);
      await apiFetch(`/api/v1/events/${eventId}/check-in`, {
        method: "POST",
        body: JSON.stringify({ registration_code: checkInCode.trim() }),
      });
      setActionSuccess(`Check-in recorded for code: ${checkInCode.trim()}`);
      setCheckInCode("");
      loadEventData();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : "Check-in failed. Verify registration code.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleGenerateQRToken = async () => {
    try {
      setActionLoading(true);
      const res = await apiFetch<EventQRToken>(`/api/v1/events/${eventId}/qr-token?duration_seconds=600`);
      setQrTokenData(res.data);
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : "Failed to generate QR token.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleStatusTransition = async (newStatus: string) => {
    if (!confirm(`Are you sure you want to change status to ${newStatus}?`)) return;
    try {
      setActionLoading(true);
      setActionError(null);
      await apiFetch(`/api/v1/events/${eventId}/status`, {
        method: "POST",
        body: JSON.stringify({ status: newStatus }),
      });
      setActionSuccess(`Event status changed to ${newStatus}`);
      loadEventData();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : "Failed to change status.");
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="py-20 text-center text-slate-500 text-sm">
        <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-r-transparent mb-2" />
        <p>Loading event dossier...</p>
      </div>
    );
  }

  if (error || !event) {
    return (
      <div className="space-y-4">
        <Link href="/app/events" className="text-xs text-indigo-400 hover:text-indigo-300">
          ← Back to Events
        </Link>
        <div className="p-4 rounded-lg bg-rose-950/40 border border-rose-800/60 text-sm text-rose-300">
          {error || "Event not found"}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Breadcrumb & Navigation */}
      <div className="flex items-center justify-between">
        <Link
          href="/app/events"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
          </svg>
          Back to Events Catalog
        </Link>

        {canManageEvent && (
          <div className="flex items-center gap-2">
            {event.status === "DRAFT" && (
              <button
                onClick={() => handleStatusTransition("PUBLISHED")}
                className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white"
              >
                Publish Event
              </button>
            )}
            {event.status === "PUBLISHED" && (
              <button
                onClick={() => handleStatusTransition("REGISTRATION_OPEN")}
                className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white"
              >
                Open Registration
              </button>
            )}
            {event.status === "REGISTRATION_OPEN" && (
              <button
                onClick={() => handleStatusTransition("REGISTRATION_CLOSED")}
                className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-xs font-semibold text-white"
              >
                Close Registration
              </button>
            )}
            {["PUBLISHED", "REGISTRATION_OPEN", "REGISTRATION_CLOSED", "ONGOING"].includes(event.status) && (
              <button
                onClick={() => handleStatusTransition("CANCELLED")}
                className="px-3 py-1.5 rounded-lg bg-rose-950 border border-rose-800 hover:bg-rose-900 text-xs font-semibold text-rose-300"
              >
                Cancel Event
              </button>
            )}
          </div>
        )}
      </div>

      {actionError && (
        <div className="p-3 rounded-lg bg-rose-950/50 border border-rose-800/60 text-xs text-rose-300">
          {actionError}
        </div>
      )}
      {actionSuccess && (
        <div className="p-3 rounded-lg bg-emerald-950/50 border border-emerald-800/60 text-xs text-emerald-300">
          {actionSuccess}
        </div>
      )}

      {/* Main Dossier Header */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="space-y-2 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[11px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                {event.category_name || "Campus Event"}
              </span>
              <span className="text-[11px] font-semibold uppercase px-2 py-0.5 rounded bg-indigo-950/70 text-indigo-400 border border-indigo-800/60">
                {event.visibility}
              </span>
              <span
                className={`text-[11px] font-semibold uppercase px-2 py-0.5 rounded ${
                  event.status === "REGISTRATION_OPEN"
                    ? "bg-emerald-950/70 text-emerald-400 border border-emerald-800/60"
                    : event.status === "ONGOING"
                    ? "bg-amber-950/70 text-amber-400 border border-amber-800/60"
                    : "bg-slate-800 text-slate-300"
                }`}
              >
                {event.status.replace("_", " ")}
              </span>
            </div>

            <h1 className="text-2xl font-bold text-white">{event.title}</h1>
            {event.description && (
              <p className="text-sm text-slate-300 whitespace-pre-line pt-1">
                {event.description}
              </p>
            )}
          </div>

          {/* Registration / Student Interaction Card */}
          <div className="w-full md:w-72 rounded-xl border border-slate-800 bg-slate-950 p-5 flex flex-col justify-between">
            <div>
              <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
                Participation Status
              </div>
              <div className="mt-2 flex items-center justify-between">
                <span className="text-xs text-slate-400">Total Registered</span>
                <span className="text-sm font-bold text-white">
                  {event.registered_count} {event.capacity ? `/ ${event.capacity}` : ""}
                </span>
              </div>
              {event.capacity && (
                <div className="mt-1.5 w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-indigo-500 h-1.5 rounded-full"
                    style={{
                      width: `${Math.min(100, (event.registered_count / event.capacity) * 100)}%`,
                    }}
                  />
                </div>
              )}
            </div>

            <div className="mt-6 pt-4 border-t border-slate-800">
              {event.user_registration_status ? (
                <div className="space-y-3">
                  <div className="rounded-lg bg-emerald-950/40 border border-emerald-800/50 p-3 text-center">
                    <span className="text-[10px] uppercase font-bold text-emerald-400">
                      Confirmed Registration
                    </span>
                    <div className="text-xs font-mono font-bold text-white mt-1">
                      Status: {event.user_registration_status}
                    </div>
                  </div>
                  {event.status === "REGISTRATION_OPEN" && (
                    <button
                      onClick={handleCancelRegistration}
                      disabled={actionLoading}
                      className="w-full py-2 rounded-lg border border-slate-800 bg-slate-900 hover:bg-rose-950 hover:border-rose-900 hover:text-rose-300 text-xs font-semibold text-slate-400 transition-colors"
                    >
                      Cancel Registration
                    </button>
                  )}
                </div>
              ) : event.status === "REGISTRATION_OPEN" ? (
                <button
                  onClick={handleRegister}
                  disabled={actionLoading}
                  className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white shadow-md transition-colors disabled:opacity-50"
                >
                  {actionLoading ? "Registering..." : "Register Now"}
                </button>
              ) : (
                <div className="text-center text-xs text-slate-500 py-1">
                  Registration is currently {event.status.toLowerCase().replace("_", " ")}.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Event Schedule and Location Metrics */}
        <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4 pt-6 border-t border-slate-800/80 text-xs text-slate-300">
          <div className="rounded-lg bg-slate-950/60 border border-slate-800/60 p-3">
            <span className="text-[11px] text-slate-500 uppercase font-semibold">Event Time</span>
            <p className="text-sm font-semibold text-white mt-1">
              {new Date(event.start_at).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}
            </p>
            <p className="text-xs text-slate-400 mt-0.5">
              {new Date(event.start_at).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })} -{" "}
              {new Date(event.end_at).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })}
            </p>
          </div>

          <div className="rounded-lg bg-slate-950/60 border border-slate-800/60 p-3">
            <span className="text-[11px] text-slate-500 uppercase font-semibold">Venue & Facility</span>
            <p className="text-sm font-semibold text-white mt-1">
              {event.venue_name || "On-Campus Facility"}
            </p>
            <p className="text-xs text-slate-400 mt-0.5">
              {event.venue_details ? `${event.venue_details.building} • Floor ${event.venue_details.floor || "G"}` : "Physical venue"}
            </p>
          </div>

          <div className="rounded-lg bg-slate-950/60 border border-slate-800/60 p-3">
            <span className="text-[11px] text-slate-500 uppercase font-semibold">Registration Window</span>
            <p className="text-sm font-semibold text-white mt-1">
              {event.registration_open_at
                ? new Date(event.registration_open_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })
                : "Open immediately"}
            </p>
            <p className="text-xs text-slate-400 mt-0.5">
              Closes: {event.registration_close_at ? new Date(event.registration_close_at).toLocaleDateString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "Until start"}
            </p>
          </div>
        </div>
      </div>

      {/* Staff / Event Attendance Console */}
      {canManageAttendance && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div>
              <h2 className="text-base font-bold text-white">Event Attendance & Check-In Console</h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Scan attendee registration codes, mark physical presence, or display dynamic QR tokens.
              </p>
            </div>

            <button
              onClick={handleGenerateQRToken}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-white transition-colors"
            >
              <svg className="h-4 w-4 text-indigo-400" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 4.875c0-.621.504-1.125 1.125-1.125h4.5c.621 0 1.125.504 1.125 1.125v4.5c0 .621-.504 1.125-1.125 1.125h-4.5A1.125 1.125 0 0 1 3.75 9.375v-4.5ZM3.75 14.625c0-.621.504-1.125 1.125-1.125h4.5c.621 0 1.125.504 1.125 1.125v4.5c0 .621-.504 1.125-1.125 1.125h-4.5a1.125 1.125 0 0 1-1.125-1.125v-4.5ZM13.5 4.875c0-.621.504-1.125 1.125-1.125h4.5c.621 0 1.125.504 1.125 1.125v4.5c0 .621-.504 1.125-1.125 1.125h-4.5A1.125 1.125 0 0 1 13.5 9.375v-4.5Z" />
              </svg>
              Generate Hall QR Token
            </button>
          </div>

          {/* QR Display Modal Banner if active */}
          {qrTokenData && (
            <div className="p-4 rounded-xl border border-indigo-800/80 bg-indigo-950/30 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div>
                <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-400 bg-indigo-900/60 px-2 py-0.5 rounded">
                  Active Venue QR Token
                </span>
                <p className="text-xs text-slate-300 mt-1 font-mono break-all max-w-xl">
                  Token: {qrTokenData.qr_token}
                </p>
                <p className="text-[11px] text-slate-400 mt-1">
                  Valid for {qrTokenData.valid_duration_seconds}s (Expires at {new Date(qrTokenData.expires_at).toLocaleTimeString()})
                </p>
              </div>
              <button
                onClick={() => setQrTokenData(null)}
                className="px-3 py-1 rounded bg-slate-800 text-xs text-slate-300 hover:text-white"
              >
                Dismiss
              </button>
            </div>
          )}

          {/* Manual Code Check-in Form */}
          <form onSubmit={handleCheckIn} className="flex gap-3 max-w-md">
            <input
              type="text"
              required
              value={checkInCode}
              onChange={(e) => setCheckInCode(e.target.value)}
              placeholder="Enter Registration Code (e.g. REG-A1B2C3)..."
              className="flex-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            <button
              type="submit"
              disabled={actionLoading}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white rounded-lg transition-colors disabled:opacity-50"
            >
              Check In
            </button>
          </form>

          {/* Attendee Roster Table */}
          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-4">Code</th>
                  <th className="py-2.5 px-4">Student</th>
                  <th className="py-2.5 px-4">Roll Number</th>
                  <th className="py-2.5 px-4">Registered At</th>
                  <th className="py-2.5 px-4">Status</th>
                  <th className="py-2.5 px-4 text-right">Attendance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 bg-slate-900/20 text-slate-300">
                {attendees.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-6 text-center text-slate-500">
                      No registrations recorded yet.
                    </td>
                  </tr>
                ) : (
                  attendees.map((att) => (
                    <tr key={att.id} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-4 font-mono font-semibold text-indigo-400">
                        {att.registration_code}
                      </td>
                      <td className="py-2.5 px-4 font-medium text-white">
                        {att.student_name || "Enrolled Student"}
                      </td>
                      <td className="py-2.5 px-4 font-mono text-slate-400">
                        {att.student_roll_number || "—"}
                      </td>
                      <td className="py-2.5 px-4 text-slate-400">
                        {new Date(att.registered_at).toLocaleDateString()}
                      </td>
                      <td className="py-2.5 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            att.status === "REGISTERED"
                              ? "bg-indigo-950 text-indigo-400"
                              : att.status === "ATTENDED"
                              ? "bg-emerald-950 text-emerald-400"
                              : "bg-slate-800 text-slate-400"
                          }`}
                        >
                          {att.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-right">
                        {att.attended ? (
                          <span className="inline-flex items-center gap-1 text-emerald-400 font-semibold text-xs">
                            ✓ Present
                          </span>
                        ) : (
                          <button
                            onClick={() => {
                              setCheckInCode(att.registration_code);
                            }}
                            className="text-indigo-400 hover:text-indigo-300 font-medium"
                          >
                            Mark Check-in
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
