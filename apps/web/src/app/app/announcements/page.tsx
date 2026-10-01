"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type { Announcement, AudiencePreview } from "@campusos/types";

export default function AnnouncementsBulletinPage() {
  const { hasPermission } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);

  // Filters
  const [priorityFilter, setPriorityFilter] = useState("ALL");
  const [search, setSearch] = useState("");

  // Create Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Audience Preview state
  const [previewing, setPreviewing] = useState(false);
  const [previewData, setPreviewData] = useState<AudiencePreview | null>(null);

  const [formData, setFormData] = useState({
    title: "",
    summary: "",
    content: "",
    priority: "NORMAL",
    is_pinned: false,
    status: "PUBLISHED",
    target_type: "ALL_USERS",
  });

  const canCreateAnnouncement = hasPermission("announcements:create");

  const loadAnnouncements = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (search) params.append("search", search);
      if (priorityFilter !== "ALL") params.append("priority", priorityFilter);

      const res = await apiFetch<{ items: Announcement[]; total: number }>(`/api/v1/announcements?${params.toString()}`);
      setAnnouncements(res.data.items || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load announcements.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnnouncements();
  }, [priorityFilter]);

  const handleAudiencePreview = async () => {
    try {
      setPreviewing(true);
      const res = await apiFetch<AudiencePreview>("/api/v1/announcements/audience-preview", {
        method: "POST",
        body: JSON.stringify({
          audiences: [{ target_type: formData.target_type }],
        }),
      });
      setPreviewData(res.data);
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to compute audience preview.");
    } finally {
      setPreviewing(false);
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setFormError(null);

    try {
      await apiFetch("/api/v1/announcements", {
        method: "POST",
        body: JSON.stringify({
          title: formData.title.trim(),
          summary: formData.summary.trim() || null,
          content: formData.content.trim(),
          priority: formData.priority,
          is_pinned: formData.is_pinned,
          status: formData.status,
          audiences: [{ target_type: formData.target_type }],
        }),
      });

      setShowCreateModal(false);
      setFormData({
        title: "",
        summary: "",
        content: "",
        priority: "NORMAL",
        is_pinned: false,
        status: "PUBLISHED",
        target_type: "ALL_USERS",
      });
      setPreviewData(null);
      loadAnnouncements();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to broadcast announcement.");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-indigo-950/80 text-indigo-400 border border-indigo-800/60">
              CampusOS Engine
            </span>
            <span className="text-xs text-slate-400">Step 10 Active</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-white">
            Institutional Announcements & Circulars
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Authoritative campus broadcasts, semester circulars, holiday notifications, and emergency alerts.
          </p>
        </div>

        <div>
          {canCreateAnnouncement && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 transition-colors"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              Publish Circular
            </button>
          )}
        </div>
      </div>

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
            onKeyDown={(e) => e.key === "Enter" && loadAnnouncements()}
            placeholder="Search circulars by subject, keyword, or author..."
            className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>

        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="ALL">All Priorities</option>
          <option value="URGENT">Urgent Alerts</option>
          <option value="HIGH">High Priority</option>
          <option value="NORMAL">Normal</option>
          <option value="LOW">Low</option>
        </select>
      </div>

      {/* Feed */}
      {loading ? (
        <div className="py-20 text-center text-slate-500 text-sm">
          <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-r-transparent mb-2" />
          <p>Loading circulars bulletin...</p>
        </div>
      ) : error ? (
        <div className="p-4 rounded-lg bg-rose-950/40 border border-rose-800/60 text-sm text-rose-300">
          {error}
        </div>
      ) : announcements.length === 0 ? (
        <div className="py-20 text-center rounded-xl border border-dashed border-slate-800 bg-slate-900/30">
          <p className="text-base font-medium text-slate-300">No announcements posted</p>
          <p className="text-xs text-slate-500 mt-1">Check back later for official institutional circulars.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {announcements.map((ann) => {
            const isUrgent = ann.priority === "URGENT";
            const isHigh = ann.priority === "HIGH";

            return (
              <div
                key={ann.id}
                className={`rounded-xl border p-5 transition-all hover:border-slate-700 ${
                  ann.is_pinned
                    ? "border-indigo-800/80 bg-indigo-950/20"
                    : "border-slate-800 bg-slate-900/50"
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                  <div className="space-y-1.5 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      {ann.is_pinned && (
                        <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-amber-400 bg-amber-950/70 border border-amber-800/60 px-2 py-0.5 rounded">
                          📌 Pinned Circular
                        </span>
                      )}
                      <span
                        className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                          isUrgent
                            ? "bg-rose-950 text-rose-300 border border-rose-800 animate-pulse"
                            : isHigh
                            ? "bg-amber-950 text-amber-300 border border-amber-800"
                            : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {ann.priority} Priority
                      </span>
                      <span className="text-xs text-slate-500">
                        Published {new Date(ann.publish_at).toLocaleDateString()}
                      </span>
                    </div>

                    <Link
                      href={`/app/announcements/${ann.id}`}
                      className="text-base font-bold text-white hover:text-indigo-400 transition-colors block"
                    >
                      {ann.title}
                    </Link>

                    <p className="text-xs text-slate-300 line-clamp-2">
                      {ann.summary || ann.content}
                    </p>

                    <div className="flex flex-wrap items-center gap-2 pt-2 text-[11px] text-slate-400">
                      <span>Target:</span>
                      {ann.audiences?.map((aud, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 rounded bg-slate-800 font-mono text-[10px] text-slate-300"
                        >
                          {aud.target_type.replace("_", " ")}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-start gap-2">
                    <Link
                      href={`/app/announcements/${ann.id}`}
                      className="px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors"
                    >
                      Read Full Circular →
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Announcement Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="w-full max-w-xl max-h-[90vh] overflow-y-auto rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <h2 className="text-lg font-bold text-white">Broadcast Campus Circular</h2>
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
                  Circular Title *
                </label>
                <input
                  type="text"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="e.g. Schedule for End-Semester Examinations — Dec 2026"
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Executive Summary
                </label>
                <input
                  type="text"
                  value={formData.summary}
                  onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
                  placeholder="Short one-line headline for inbox notifications..."
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Full Announcement Content *
                </label>
                <textarea
                  required
                  rows={5}
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  placeholder="Full circular text, guidelines, instructions..."
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Priority Level
                  </label>
                  <select
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  >
                    <option value="LOW">Low</option>
                    <option value="NORMAL">Normal</option>
                    <option value="HIGH">High Priority</option>
                    <option value="URGENT">Urgent (Bypasses non-critical filters)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Target Audience Group
                  </label>
                  <select
                    value={formData.target_type}
                    onChange={(e) => {
                      setFormData({ ...formData, target_type: e.target.value });
                      setPreviewData(null);
                    }}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  >
                    <option value="ALL_USERS">All Campus Users (Faculty, Students, Staff)</option>
                    <option value="ALL_STUDENTS">All Enrolled Students Only</option>
                    <option value="ALL_FACULTY">All Instructional Faculty Only</option>
                    <option value="ALL_STAFF">All Administrative Staff Only</option>
                  </select>
                </div>
              </div>

              {/* Real-time Audience Preview Box */}
              <div className="p-3.5 rounded-lg border border-slate-800 bg-slate-950/70 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-300">
                    Target Audience Calculator
                  </span>
                  <button
                    type="button"
                    onClick={handleAudiencePreview}
                    disabled={previewing}
                    className="text-[11px] font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                  >
                    {previewing ? "Computing..." : "Calculate Audience Impact"}
                  </button>
                </div>

                {previewData ? (
                  <div className="text-xs space-y-1 pt-1 border-t border-slate-800/80">
                    <p className="font-semibold text-white">
                      Estimated Recipients: <span className="text-indigo-400">{previewData.total_recipients}</span> users
                    </p>
                    <p className="text-[11px] text-slate-400">
                      Students: {previewData.students_count} • Faculty: {previewData.faculty_count} • Staff: {previewData.staff_count}
                    </p>
                  </div>
                ) : (
                  <p className="text-[11px] text-slate-500">
                    Click &quot;Calculate Audience Impact&quot; to resolve exact backend recipient counts before dispatching.
                  </p>
                )}
              </div>

              <div className="flex items-center gap-4 pt-1">
                <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_pinned}
                    onChange={(e) => setFormData({ ...formData, is_pinned: e.target.checked })}
                    className="rounded border-slate-800 bg-slate-950 text-indigo-600 focus:ring-indigo-500"
                  />
                  Pin to Top of Bulletin
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
                  {creating ? "Broadcasting..." : "Publish & Broadcast"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
