"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import type { NotificationItem } from "@campusos/types";

export default function NotificationCenterPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [selectedModule, setSelectedModule] = useState("ALL");
  const [actionLoading, setActionLoading] = useState(false);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (unreadOnly) params.append("unread_only", "true");
      if (selectedModule !== "ALL") params.append("module", selectedModule);
      params.append("limit", "50");

      const res = await apiFetch<{ items: NotificationItem[]; total: number }>(
        `/api/v1/notifications?${params.toString()}`
      );
      setNotifications(res.data.items || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load notification center.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifications();
  }, [unreadOnly, selectedModule]);

  const handleMarkAsRead = async (notifId: string) => {
    try {
      await apiFetch(`/api/v1/notifications/${notifId}/read`, { method: "POST" });
      setNotifications((prev) =>
        prev.map((n) => (n.id === notifId ? { ...n, is_read: true } : n))
      );
    } catch {
      // silent fallback
    }
  };

  const handleMarkAllRead = async () => {
    try {
      setActionLoading(true);
      await apiFetch("/api/v1/notifications/read-all", { method: "POST" });
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch {
      // silent fallback
    } finally {
      setActionLoading(false);
    }
  };

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
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
            Unified Notification Center
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Real-time multi-subsystem alerts, circular distributions, event reminders, and standing updates.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/app/notifications/preferences"
            className="px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 text-xs font-semibold text-slate-300 transition-colors"
          >
            Preferences
          </Link>
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllRead}
              disabled={actionLoading}
              className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white transition-colors"
            >
              Mark All Read
            </button>
          )}
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setUnreadOnly(false)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              !unreadOnly
                ? "bg-indigo-600 text-white"
                : "bg-slate-900 border border-slate-800 text-slate-400 hover:text-white"
            }`}
          >
            All Alerts ({notifications.length})
          </button>
          <button
            onClick={() => setUnreadOnly(true)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              unreadOnly
                ? "bg-indigo-600 text-white"
                : "bg-slate-900 border border-slate-800 text-slate-400 hover:text-white"
            }`}
          >
            Unread Only ({unreadCount})
          </button>
        </div>

        <select
          value={selectedModule}
          onChange={(e) => setSelectedModule(e.target.value)}
          className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="ALL">All Modules</option>
          <option value="EVENTS">Events</option>
          <option value="CLUBS">Clubs</option>
          <option value="ANNOUNCEMENTS">Announcements</option>
          <option value="ATTENDANCE">Attendance</option>
          <option value="EXAMINATION">Examinations</option>
          <option value="FINANCE">Finance</option>
          <option value="SYSTEM">System Alerts</option>
        </select>
      </div>

      {/* Notifications Feed */}
      {loading ? (
        <div className="py-20 text-center text-slate-500 text-sm">
          <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-r-transparent mb-2" />
          <p>Loading notification center...</p>
        </div>
      ) : error ? (
        <div className="p-4 rounded-lg bg-rose-950/40 border border-rose-800/60 text-sm text-rose-300">
          {error}
        </div>
      ) : notifications.length === 0 ? (
        <div className="py-20 text-center rounded-xl border border-dashed border-slate-800 bg-slate-900/30">
          <svg className="mx-auto h-12 w-12 text-slate-600 mb-3" fill="none" viewBox="0 0 24 24" strokeWidth="1" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
          </svg>
          <p className="text-base font-medium text-slate-300">Your inbox is clear</p>
          <p className="text-xs text-slate-500 mt-1">No unread alerts or notifications waiting for your attention.</p>
        </div>
      ) : (
        <div className="divide-y divide-slate-800/80 rounded-xl border border-slate-800 bg-slate-900/50 overflow-hidden">
          {notifications.map((notif) => {
            const isUnread = !notif.is_read;
            const isUrgent = notif.priority === "URGENT";

            return (
              <div
                key={notif.id}
                className={`p-4 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                  isUnread ? "bg-indigo-950/20" : "hover:bg-slate-900/80"
                }`}
              >
                <div className="flex items-start gap-3 flex-1">
                  <div className="pt-0.5">
                    {isUnread ? (
                      <span className="block h-2 w-2 rounded-full bg-indigo-500 ring-4 ring-indigo-500/20" />
                    ) : (
                      <span className="block h-2 w-2 rounded-full bg-slate-700" />
                    )}
                  </div>

                  <div className="space-y-1 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400 bg-indigo-950/70 border border-indigo-900/60 px-1.5 py-0.5 rounded">
                        {notif.source_module}
                      </span>
                      {isUrgent && (
                        <span className="text-[10px] font-bold uppercase tracking-wider text-rose-300 bg-rose-950/80 border border-rose-800/70 px-1.5 py-0.5 rounded">
                          Urgent
                        </span>
                      )}
                      <span className="text-xs font-semibold text-white">
                        {notif.title}
                      </span>
                      <span className="text-[11px] text-slate-500">
                        • {new Date(notif.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })},{" "}
                        {new Date(notif.created_at).toLocaleDateString([], { month: "short", day: "numeric" })}
                      </span>
                    </div>

                    <p className="text-xs text-slate-300">
                      {notif.message}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 pl-5 sm:pl-0">
                  {notif.action_url && (
                    <Link
                      href={notif.action_url}
                      onClick={() => handleMarkAsRead(notif.id)}
                      className="text-xs font-semibold text-indigo-400 hover:text-indigo-300"
                    >
                      View Source →
                    </Link>
                  )}

                  {isUnread && (
                    <button
                      onClick={() => handleMarkAsRead(notif.id)}
                      className="text-[11px] font-medium text-slate-400 hover:text-white px-2 py-1 rounded bg-slate-800 hover:bg-slate-700"
                    >
                      Mark read
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
