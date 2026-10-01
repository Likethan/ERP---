"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Drawer } from "@/components/ui/drawer";
import { campusService } from "@/services/campus.service";
import { NotificationItem } from "@/mocks/campus.mock";
import { Bell, CheckCheck, ExternalLink, Calendar, DollarSign, Briefcase, GraduationCap, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface NotificationDrawerProps {
  open: boolean;
  onClose: () => void;
}

export function NotificationDrawer({ open, onClose }: NotificationDrawerProps) {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [filter, setFilter] = useState<"ALL" | "UNREAD">("ALL");

  const loadNotifications = async () => {
    const res = await campusService.getNotifications();
    setNotifications(res.data);
  };

  useEffect(() => {
    if (open) {
      loadNotifications();
    }
  }, [open]);

  const handleMarkAllRead = async () => {
    await campusService.markAllNotificationsAsRead();
    loadNotifications();
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "ATTENDANCE":
        return <Calendar className="h-4 w-4 text-purple-400" />;
      case "FINANCE":
        return <DollarSign className="h-4 w-4 text-emerald-400" />;
      case "PLACEMENT":
        return <Briefcase className="h-4 w-4 text-blue-400" />;
      case "ACADEMIC":
        return <GraduationCap className="h-4 w-4 text-amber-400" />;
      case "SECURITY":
        return <ShieldCheck className="h-4 w-4 text-rose-400" />;
      default:
        return <Bell className="h-4 w-4 text-slate-400" />;
    }
  };

  const displayedNotifications =
    filter === "UNREAD" ? notifications.filter((n) => !n.isRead) : notifications;

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title="Notification Center"
      description="System alerts, academic dispatches, and corporate drive updates"
      size="md"
      footer={
        <div className="flex items-center justify-between w-full">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleMarkAllRead}
            leftIcon={<CheckCheck className="h-4 w-4" />}
            className="text-xs text-slate-400 hover:text-white"
          >
            Mark all as read
          </Button>
          <Link
            href="/app/notifications"
            onClick={onClose}
            className="text-xs text-indigo-400 hover:text-indigo-300 font-medium inline-flex items-center gap-1"
          >
            Preferences <ExternalLink className="h-3 w-3" />
          </Link>
        </div>
      }
    >
      <div className="space-y-4">
        {/* Filter Pills */}
        <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
          <button
            onClick={() => setFilter("ALL")}
            className={cn(
              "px-3 py-1 rounded-full text-xs font-medium transition-colors",
              filter === "ALL"
                ? "bg-indigo-600 text-white"
                : "bg-slate-800 text-slate-400 hover:text-slate-200"
            )}
          >
            All ({notifications.length})
          </button>
          <button
            onClick={() => setFilter("UNREAD")}
            className={cn(
              "px-3 py-1 rounded-full text-xs font-medium transition-colors",
              filter === "UNREAD"
                ? "bg-indigo-600 text-white"
                : "bg-slate-800 text-slate-400 hover:text-slate-200"
            )}
          >
            Unread ({notifications.filter((n) => !n.isRead).length})
          </button>
        </div>

        {/* Notifications List */}
        <div className="space-y-2">
          {displayedNotifications.map((notif) => (
            <div
              key={notif.id}
              className={cn(
                "p-3.5 rounded-xl border transition-all text-left",
                notif.isRead
                  ? "border-slate-800/60 bg-slate-900/40 text-slate-400"
                  : "border-indigo-900/60 bg-indigo-950/20 text-slate-200 shadow-sm"
              )}
            >
              <div className="flex items-start gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-800 border border-slate-700/60 shrink-0 mt-0.5">
                  {getCategoryIcon(notif.category)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-semibold text-white truncate">
                      {notif.title}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono shrink-0">
                      {notif.timestamp}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-slate-400 leading-relaxed">
                    {notif.message}
                  </p>
                  {notif.link && (
                    <div className="mt-2">
                      <Link
                        href={notif.link}
                        onClick={onClose}
                        className="text-[11px] font-medium text-indigo-400 hover:text-indigo-300 inline-flex items-center gap-1"
                      >
                        Inspect details <ExternalLink className="h-3 w-3" />
                      </Link>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Drawer>
  );
}
