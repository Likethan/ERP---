"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { campusService } from "@/services/campus.service";
import { NotificationItem, NotificationCategory, NotificationStatus } from "@/types/campus";
import { useAuth } from "@/lib/auth-context";
import {
  Bell,
  CheckCheck,
  Archive,
  ExternalLink,
  Calendar,
  DollarSign,
  Briefcase,
  GraduationCap,
  ShieldCheck,
  Filter,
  CheckCircle2,
  Trash2,
  SlidersHorizontal,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const ALL_CATEGORIES: NotificationCategory[] = [
  "ACADEMIC",
  "FINANCE",
  "PLACEMENT",
  "EVENT",
  "CLUB",
  "SYSTEM",
  "GENERAL",
];

export default function CampusNotificationsInboxPage() {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<"ALL" | "UNREAD" | "READ" | "ARCHIVED">("ALL");
  const [categoryFilter, setCategoryFilter] = useState<string>("ALL");
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const res = await campusService.getNotifications();
      if (res.success && res.data) {
        setNotifications(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifications();
  }, []);

  const handleMarkRead = async (id: string) => {
    await campusService.markNotificationRead(id);
    loadNotifications();
  };

  const handleMarkAllRead = async () => {
    const res = await campusService.markAllNotificationsRead();
    setActionMessage(`Marked ${res.data.count} notifications as read.`);
    loadNotifications();
  };

  const handleArchive = async (id: string) => {
    await campusService.archiveNotification(id);
    loadNotifications();
  };

  const filteredNotifications = useMemo(() => {
    return notifications.filter((n) => {
      const matchStatus = statusFilter === "ALL" || n.status === statusFilter;
      const matchCat = categoryFilter === "ALL" || n.category === categoryFilter;
      return matchStatus && matchCat;
    });
  }, [notifications, statusFilter, categoryFilter]);

  const unreadCount = notifications.filter((n) => n.status === "UNREAD").length;

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "EVENT":
        return <Calendar className="h-4 w-4 text-pink-400" />;
      case "CLUB":
        return <ShieldCheck className="h-4 w-4 text-cyan-400" />;
      case "FINANCE":
        return <DollarSign className="h-4 w-4 text-emerald-400" />;
      case "PLACEMENT":
        return <Briefcase className="h-4 w-4 text-blue-400" />;
      case "ACADEMIC":
        return <GraduationCap className="h-4 w-4 text-amber-400" />;
      case "SYSTEM":
        return <ShieldCheck className="h-4 w-4 text-rose-400" />;
      default:
        return <Bell className="h-4 w-4 text-slate-400" />;
    }
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-5xl mx-auto pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <Link href="/app/campus" className="text-xs text-slate-400 hover:text-indigo-400">
              Campus Hub
            </Link>
            <span className="text-slate-600">/</span>
            <span className="text-xs text-slate-200 font-semibold">Notifications</span>
          </div>
          <h1 className="mt-1 text-2xl font-black tracking-tight text-white flex items-center gap-2.5">
            <Bell className="h-6 w-6 text-indigo-400" />
            Notification Center & Inbox
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Real-time feed of academic notices, fee invoices, job drive updates, and event reminders.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={handleMarkAllRead}
            disabled={unreadCount === 0}
            leftIcon={<CheckCheck className="h-4 w-4" />}
            className="border-slate-700 bg-slate-900 text-xs"
          >
            Mark All as Read ({unreadCount})
          </Button>

          <Link href="/app/campus/preferences">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<SlidersHorizontal className="h-4 w-4" />}
              className="border-slate-700 bg-slate-900 text-xs"
            >
              Delivery Preferences
            </Button>
          </Link>
        </div>
      </div>

      {actionMessage && (
        <div className="p-3.5 rounded-xl border border-emerald-500/30 bg-emerald-950/20 text-emerald-300 text-xs flex items-center justify-between">
          <span>{actionMessage}</span>
          <button onClick={() => setActionMessage(null)} className="text-emerald-400 hover:text-white">
            Dismiss
          </button>
        </div>
      )}

      {/* Filter Toolbar */}
      <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Status Pills */}
        <div className="flex items-center gap-2">
          {(["ALL", "UNREAD", "READ", "ARCHIVED"] as const).map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors cursor-pointer",
                statusFilter === s
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "bg-slate-950 text-slate-400 hover:text-white border border-slate-800"
              )}
            >
              {s === "UNREAD" ? `Unread (${unreadCount})` : s}
            </button>
          ))}
        </div>

        {/* Category Filter */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Category:</span>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white"
          >
            <option value="ALL">All Categories</option>
            {ALL_CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Notifications List */}
      <div className="space-y-3">
        {filteredNotifications.length === 0 ? (
          <div className="p-12 text-center rounded-2xl border border-slate-800 bg-slate-900/40 space-y-2">
            <Bell className="h-8 w-8 text-slate-600 mx-auto" />
            <div className="text-sm font-semibold text-white">No notifications found</div>
            <p className="text-xs text-slate-400">You are all caught up on your campus alerts!</p>
          </div>
        ) : (
          filteredNotifications.map((notif) => {
            const isUnread = notif.status === "UNREAD";
            return (
              <div
                key={notif.id}
                className={cn(
                  "p-4 rounded-xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4",
                  isUnread
                    ? "border-indigo-900/60 bg-indigo-950/20 text-slate-200 shadow-sm"
                    : "border-slate-800/80 bg-slate-900/40 text-slate-400"
                )}
              >
                <div className="flex items-start gap-3.5 flex-1">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-800 border border-slate-700/60 shrink-0 mt-0.5">
                    {getCategoryIcon(notif.category)}
                  </div>

                  <div className="space-y-1 flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={cn("text-xs font-bold", isUnread ? "text-white" : "text-slate-300")}>
                        {notif.title}
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.2 rounded bg-slate-800 text-slate-400">
                        {notif.category}
                      </span>
                      {notif.priority === "URGENT" && (
                        <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30">
                          URGENT
                        </span>
                      )}
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed max-w-3xl">
                      {notif.message}
                    </p>

                    <div className="text-[10px] text-slate-500 font-mono flex items-center gap-2 pt-0.5">
                      <span>{notif.timestamp}</span>
                      {notif.relatedEntityTitle && (
                        <>
                          <span>•</span>
                          <span className="text-slate-400">Entity: {notif.relatedEntityTitle}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                  {notif.actionUrl && (
                    <Link
                      href={notif.actionUrl}
                      onClick={() => {
                        if (isUnread) handleMarkRead(notif.id);
                      }}
                      className="px-3 py-1.5 rounded-lg bg-indigo-600/30 text-indigo-300 hover:bg-indigo-600/50 text-xs font-medium inline-flex items-center gap-1.5 border border-indigo-500/40"
                    >
                      Inspect <ExternalLink className="h-3 w-3" />
                    </Link>
                  )}

                  <Link
                    href={`/app/campus/notifications/${notif.id}`}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 text-xs"
                    title="View details"
                  >
                    View
                  </Link>

                  {isUnread && (
                    <button
                      onClick={() => handleMarkRead(notif.id)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-emerald-400 hover:bg-slate-800"
                      title="Mark as read"
                    >
                      <CheckCircle2 className="h-4 w-4" />
                    </button>
                  )}

                  {notif.status !== "ARCHIVED" && (
                    <button
                      onClick={() => handleArchive(notif.id)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                      title="Archive alert"
                    >
                      <Archive className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
