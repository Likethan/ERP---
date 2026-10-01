"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type { CampusEvent, EventCategory, EventVenue, EventRegistration } from "@campusos/types";

export default function CampusEventsHubPage() {
  const { hasPermission } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [events, setEvents] = useState<CampusEvent[]>([]);
  const [categories, setCategories] = useState<EventCategory[]>([]);
  const [venues, setVenues] = useState<EventVenue[]>([]);
  const [myRegistrations, setMyRegistrations] = useState<EventRegistration[]>([]);

  // Filters
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [activeTab, setActiveTab] = useState<"catalog" | "my_events">("catalog");

  // Create Event Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    title: "",
    category_id: "",
    venue_id: "",
    description: "",
    start_at: "",
    end_at: "",
    registration_open_at: "",
    registration_close_at: "",
    capacity: 100,
    visibility: "CAMPUS",
    requires_registration: true,
    requires_attendance: true,
  });

  const canCreateEvent = hasPermission("events:create");

  const loadEvents = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (search) params.append("search", search);
      if (selectedCategory !== "ALL") params.append("category_id", selectedCategory);
      if (selectedStatus !== "ALL") params.append("status", selectedStatus);

      const [eventsRes, catsRes, venuesRes, myRegRes] = await Promise.all([
        apiFetch<{ items: CampusEvent[]; total: number }>(`/api/v1/events?${params.toString()}`),
        apiFetch<EventCategory[]>("/api/v1/event-categories"),
        apiFetch<EventVenue[]>("/api/v1/event-venues"),
        apiFetch<{ items: EventRegistration[] }>("/api/v1/events/my-registrations").catch(() => ({ data: { items: [] } })),
      ]);

      setEvents(eventsRes.data.items || []);
      setCategories(catsRes.data || []);
      setVenues(venuesRes.data || []);
      setMyRegistrations(myRegRes.data?.items || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load events data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
  }, [selectedCategory, selectedStatus]);

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setFormError(null);

    try {
      const payload: Record<string, unknown> = {
        title: formData.title,
        description: formData.description || null,
        category_id: formData.category_id || null,
        venue_id: formData.venue_id || null,
        start_at: new Date(formData.start_at).toISOString(),
        end_at: new Date(formData.end_at).toISOString(),
        capacity: Number(formData.capacity) || null,
        visibility: formData.visibility,
        requires_registration: formData.requires_registration,
        requires_attendance: formData.requires_attendance,
      };

      if (formData.registration_open_at) {
        payload.registration_open_at = new Date(formData.registration_open_at).toISOString();
      }
      if (formData.registration_close_at) {
        payload.registration_close_at = new Date(formData.registration_close_at).toISOString();
      }

      await apiFetch("/api/v1/events", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setShowCreateModal(false);
      setFormData({
        title: "",
        category_id: "",
        venue_id: "",
        description: "",
        start_at: "",
        end_at: "",
        registration_open_at: "",
        registration_close_at: "",
        capacity: 100,
        visibility: "CAMPUS",
        requires_registration: true,
        requires_attendance: true,
      });
      loadEvents();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to create event. Check venue conflict or parameters.");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-indigo-950/80 text-indigo-400 border border-indigo-800/60">
              CampusOS Engine
            </span>
            <span className="text-xs text-slate-400">Step 10 Active</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-white">
            Campus Events & Activities
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Institutional symposiums, hackathons, guest lectures, club workshops, and attendance rosters.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {canCreateEvent && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 transition-colors"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              Schedule Event
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-4 border-b border-slate-800">
        <button
          onClick={() => setActiveTab("catalog")}
          className={`pb-3 text-sm font-medium transition-colors border-b-2 ${
            activeTab === "catalog"
              ? "border-indigo-500 text-indigo-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          All Campus Events ({events.length})
        </button>
        <button
          onClick={() => setActiveTab("my_events")}
          className={`pb-3 text-sm font-medium transition-colors border-b-2 ${
            activeTab === "my_events"
              ? "border-indigo-500 text-indigo-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          My Registrations ({myRegistrations.length})
        </button>
      </div>

      {activeTab === "catalog" ? (
        <>
          {/* Filter Bar */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <svg className="absolute left-3.5 top-3 h-4 w-4 text-slate-500" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
              </svg>
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && loadEvents()}
                placeholder="Search events by title, keyword, or venue..."
                className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="ALL">All Categories</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>

            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="PUBLISHED">Published</option>
              <option value="REGISTRATION_OPEN">Registration Open</option>
              <option value="REGISTRATION_CLOSED">Registration Closed</option>
              <option value="ONGOING">Ongoing</option>
              <option value="COMPLETED">Completed</option>
            </select>
          </div>

          {/* Content */}
          {loading ? (
            <div className="py-20 text-center text-slate-500 text-sm">
              <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-r-transparent mb-2" />
              <p>Loading scheduled campus events...</p>
            </div>
          ) : error ? (
            <div className="p-4 rounded-lg bg-rose-950/40 border border-rose-800/60 text-sm text-rose-300">
              {error}
            </div>
          ) : events.length === 0 ? (
            <div className="py-20 text-center rounded-xl border border-dashed border-slate-800 bg-slate-900/30">
              <svg className="mx-auto h-12 w-12 text-slate-600 mb-3" fill="none" viewBox="0 0 24 24" strokeWidth="1" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5" />
              </svg>
              <p className="text-base font-medium text-slate-300">No events found</p>
              <p className="text-xs text-slate-500 mt-1">Try relaxing filters or schedule an event if you have staff permissions.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {events.map((evt) => {
                const isRegOpen = evt.status === "REGISTRATION_OPEN";
                const isOngoing = evt.status === "ONGOING";
                const isCompleted = evt.status === "COMPLETED";

                return (
                  <div
                    key={evt.id}
                    className="flex flex-col justify-between rounded-xl border border-slate-800 bg-slate-900/50 p-5 hover:border-slate-700 transition-all hover:shadow-lg"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-3">
                        <span className="text-[11px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                          {evt.category_name || "General Event"}
                        </span>
                        <span
                          className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded ${
                            isRegOpen
                              ? "bg-emerald-950/70 text-emerald-400 border border-emerald-800/60"
                              : isOngoing
                              ? "bg-amber-950/70 text-amber-400 border border-amber-800/60"
                              : isCompleted
                              ? "bg-slate-800 text-slate-400"
                              : "bg-indigo-950/70 text-indigo-400 border border-indigo-800/60"
                          }`}
                        >
                          {evt.status.replace("_", " ")}
                        </span>
                      </div>

                      <h3 className="text-base font-semibold text-white line-clamp-1">
                        {evt.title}
                      </h3>
                      {evt.description && (
                        <p className="text-xs text-slate-400 line-clamp-2 mt-1">
                          {evt.description}
                        </p>
                      )}

                      <div className="mt-4 space-y-2 text-xs text-slate-300">
                        <div className="flex items-center gap-2">
                          <svg className="h-4 w-4 text-slate-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                          </svg>
                          <span>{new Date(evt.start_at).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" })}</span>
                        </div>

                        <div className="flex items-center gap-2">
                          <svg className="h-4 w-4 text-slate-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1 1 15 0Z" />
                          </svg>
                          <span className="truncate">{evt.venue_name || "Campus Facility"}</span>
                        </div>

                        <div className="flex items-center gap-2">
                          <svg className="h-4 w-4 text-slate-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
                          </svg>
                          <span>
                            {evt.registered_count} {evt.capacity ? `/ ${evt.capacity}` : ""} Registered
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="mt-5 pt-3 border-t border-slate-800/80 flex items-center justify-between">
                      {evt.user_registration_status ? (
                        <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-400">
                          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                          {evt.user_registration_status}
                        </span>
                      ) : (
                        <span className="text-xs text-slate-500">
                          {evt.requires_registration ? "Registration Required" : "Open Attendance"}
                        </span>
                      )}

                      <Link
                        href={`/app/events/${evt.id}`}
                        className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                      >
                        Details & Console →
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      ) : (
        /* My Registrations Tab */
        <div className="space-y-4">
          {myRegistrations.length === 0 ? (
            <div className="py-20 text-center rounded-xl border border-dashed border-slate-800 bg-slate-900/30">
              <p className="text-base font-medium text-slate-300">You have no active registrations</p>
              <p className="text-xs text-slate-500 mt-1">Browse the catalog to register for upcoming college activities.</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-800 rounded-xl border border-slate-800 bg-slate-900/50">
              {myRegistrations.map((reg) => (
                <div key={reg.id} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <span className="text-xs font-mono font-semibold text-indigo-400 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-900/50">
                      {reg.registration_code}
                    </span>
                    <h4 className="text-sm font-semibold text-white mt-1">{reg.event_title}</h4>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Registered on {new Date(reg.registered_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span
                      className={`text-xs font-semibold px-2.5 py-1 rounded ${
                        reg.attended
                          ? "bg-emerald-950/70 text-emerald-400 border border-emerald-800/60"
                          : reg.status === "REGISTERED"
                          ? "bg-indigo-950/70 text-indigo-400 border border-indigo-800/60"
                          : "bg-slate-800 text-slate-400"
                      }`}
                    >
                      {reg.attended ? "ATTENDED" : reg.status}
                    </span>
                    <Link
                      href={`/app/events/${reg.event_id}`}
                      className="px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-white transition-colors"
                    >
                      View Event
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Create Event Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="w-full max-w-xl max-h-[90vh] overflow-y-auto rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <h2 className="text-lg font-bold text-white">Schedule New Campus Event</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            {formError && (
              <div className="mt-4 p-3 rounded-lg bg-rose-950/50 border border-rose-800/60 text-xs text-rose-300">
                {formError}
              </div>
            )}

            <form onSubmit={handleCreateSubmit} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Event Title *
                </label>
                <input
                  type="text"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="e.g. National Hackathon 2026"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Event Category
                  </label>
                  <select
                    value={formData.category_id}
                    onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  >
                    <option value="">Select Category</option>
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Physical Venue
                  </label>
                  <select
                    value={formData.venue_id}
                    onChange={(e) => setFormData({ ...formData, venue_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  >
                    <option value="">Select Venue</option>
                    {venues.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.name} ({v.building} - Cap: {v.capacity})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Description
                </label>
                <textarea
                  rows={3}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Brief synopsis, agenda, and guidelines..."
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Start Time *
                  </label>
                  <input
                    type="datetime-local"
                    required
                    value={formData.start_at}
                    onChange={(e) => setFormData({ ...formData, start_at: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    End Time *
                  </label>
                  <input
                    type="datetime-local"
                    required
                    value={formData.end_at}
                    onChange={(e) => setFormData({ ...formData, end_at: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Registration Opens
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.registration_open_at}
                    onChange={(e) => setFormData({ ...formData, registration_open_at: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Registration Closes
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.registration_close_at}
                    onChange={(e) => setFormData({ ...formData, registration_close_at: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Participant Capacity
                  </label>
                  <input
                    type="number"
                    min={1}
                    value={formData.capacity}
                    onChange={(e) => setFormData({ ...formData, capacity: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Audience Visibility
                  </label>
                  <select
                    value={formData.visibility}
                    onChange={(e) => setFormData({ ...formData, visibility: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  >
                    <option value="CAMPUS">Campus Wide</option>
                    <option value="INSTITUTION">All Campuses</option>
                    <option value="DEPARTMENT">Department Only</option>
                    <option value="PUBLIC">Public</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center gap-6 pt-2">
                <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.requires_registration}
                    onChange={(e) => setFormData({ ...formData, requires_registration: e.target.checked })}
                    className="rounded border-slate-800 bg-slate-950 text-indigo-600 focus:ring-indigo-500"
                  />
                  Requires Prior Registration
                </label>

                <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.requires_attendance}
                    onChange={(e) => setFormData({ ...formData, requires_attendance: e.target.checked })}
                    className="rounded border-slate-800 bg-slate-950 text-indigo-600 focus:ring-indigo-500"
                  />
                  Requires Check-in Attendance
                </label>
              </div>

              <div className="pt-4 border-t border-slate-800 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-lg border border-slate-800 bg-slate-950 text-xs font-medium text-slate-300 hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-2 rounded-lg bg-indigo-600 text-xs font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
                >
                  {creating ? "Checking Conflicts & Scheduling..." : "Schedule Event"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
