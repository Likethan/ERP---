"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { campusService } from "@/services/campus.service";
import { NotificationItem } from "@/types/campus";
import { useAuth } from "@/lib/auth-context";
import {
  Bell,
  ArrowLeft,
  ExternalLink,
  CheckCircle2,
  Archive,
  Calendar,
  DollarSign,
  Briefcase,
  GraduationCap,
  ShieldCheck,
  AlertTriangle,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface NotificationDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function NotificationDetailPage({
  params,
}: NotificationDetailPageProps) {
  const resolvedParams = use(params);
  const notificationId = resolvedParams.id;
  const { user } = useAuth();

  const [notification, setNotification] = useState<NotificationItem | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await campusService.getNotificationById(notificationId);
      if (res.success && res.data) {
        setNotification(res.data);
      } else {
        setError(res.error || "Notification not found");
      }
    } catch (e: any) {
      setError(e.message || "Failed to load notification");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [notificationId]);

  const handleMarkRead = async () => {
    if (!notification) return;
    await campusService.markNotificationRead(notification.id);
    setFeedback("Notification marked as read.");
    loadData();
  };

  const handleArchive = async () => {
    if (!notification) return;
    await campusService.archiveNotification(notification.id);
    setFeedback("Notification archived.");
    loadData();
  };

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-slate-400">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
          <span className="text-xs">Loading alert details...</span>
        </div>
      </div>
    );
  }

  if (error || !notification) {
    return (
      <div className="p-8 text-center space-y-4 rounded-2xl border border-slate-800 bg-slate-900/60 max-w-xl mx-auto my-12">
        <AlertTriangle className="h-10 w-10 text-rose-400 mx-auto" />
        <h2 className="text-base font-bold text-white">Alert Not Found</h2>
        <p className="text-xs text-slate-400">
          {error || "Requested notification does not exist."}
        </p>
        <Link href="/app/campus/notifications">
          <Button variant="outline" size="sm">
            Back to Notifications Inbox
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-3xl mx-auto pb-16">
      {/* Top Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <Link
          href="/app/campus/notifications"
          className="text-xs text-slate-400 hover:text-white inline-flex items-center gap-1.5 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Inbox
        </Link>

        <div className="flex items-center gap-2">
          {notification.status === "UNREAD" && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleMarkRead}
              leftIcon={<CheckCircle2 className="h-4 w-4 text-emerald-400" />}
              className="text-xs"
            >
              Mark Read
            </Button>
          )}
          {notification.status !== "ARCHIVED" && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleArchive}
              leftIcon={<Archive className="h-4 w-4" />}
              className="text-xs text-slate-400"
            >
              Archive
            </Button>
          )}
        </div>
      </div>

      {feedback && (
        <div className="p-3.5 rounded-xl border border-emerald-500/30 bg-emerald-950/20 text-emerald-300 text-xs flex items-center justify-between">
          <span>{feedback}</span>
          <button
            onClick={() => setFeedback(null)}
            className="text-emerald-400 hover:text-white"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Main Notification Card */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 sm:p-8 space-y-6">
        <div className="flex items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
              {notification.category}
            </span>
            <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              {notification.status}
            </span>
          </div>
          <span className="text-xs text-slate-500 font-mono">
            {notification.timestamp}
          </span>
        </div>

        <h1 className="text-xl font-bold text-white tracking-tight">
          {notification.title}
        </h1>

        <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-line">
          {notification.message}
        </p>

        {/* Target Entity Metadata & Action Link */}
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
          <span className="text-[10px] text-slate-500 uppercase font-mono block">
            Associated Institutional Entity
          </span>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <span className="text-xs font-bold text-white block">
                {notification.relatedEntityTitle || "Campus Operation Item"}
              </span>
              <span className="text-[11px] text-slate-400 font-mono">
                Type: {notification.relatedEntityType || "GENERAL"}
              </span>
            </div>

            {notification.actionUrl && (
              <Link
                href={notification.actionUrl}
                onClick={handleMarkRead}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-colors shadow-md shadow-indigo-600/30 self-start sm:self-auto"
              >
                Open Related Item <ExternalLink className="h-3.5 w-3.5" />
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
