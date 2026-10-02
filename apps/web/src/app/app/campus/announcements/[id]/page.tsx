"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { campusService } from "@/services/campus.service";
import { AnnouncementItem } from "@/types/campus";
import { useAuth } from "@/lib/auth-context";
import {
  FileText,
  Calendar,
  Users,
  Clock,
  ArrowLeft,
  CheckCircle2,
  Archive,
  History,
  AlertTriangle,
  Pin,
  Share2,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface AnnouncementDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function AnnouncementDetailPage({ params }: AnnouncementDetailPageProps) {
  const resolvedParams = use(params);
  const announcementId = resolvedParams.id;
  const { user, hasPermission } = useAuth();

  const [announcement, setAnnouncement] = useState<AnnouncementItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const canManage = hasPermission("campus.create_announcements") || hasPermission("*");

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await campusService.getAnnouncementById(announcementId);
      if (res.success && res.data) {
        setAnnouncement(res.data);
      } else {
        setError(res.error || "Announcement not found");
      }
    } catch (e: any) {
      setError(e.message || "Failed to load announcement");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [announcementId]);

  const handlePublish = async () => {
    try {
      setActionLoading(true);
      await campusService.publishAnnouncement(announcementId, user?.first_name || "Administrator");
      setFeedback("Announcement published successfully.");
      loadData();
    } finally {
      setActionLoading(false);
    }
  };

  const handleArchive = async () => {
    try {
      setActionLoading(true);
      await campusService.archiveAnnouncement(announcementId, user?.first_name || "Administrator");
      setFeedback("Announcement archived.");
      loadData();
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-slate-400">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
          <span className="text-xs">Loading announcement dispatch...</span>
        </div>
      </div>
    );
  }

  if (error || !announcement) {
    return (
      <div className="p-8 text-center space-y-4 rounded-2xl border border-slate-800 bg-slate-900/60 max-w-xl mx-auto my-12">
        <AlertTriangle className="h-10 w-10 text-rose-400 mx-auto" />
        <h2 className="text-base font-bold text-white">Announcement Not Found</h2>
        <p className="text-xs text-slate-400">{error || "Requested announcement does not exist."}</p>
        <Link href="/app/campus/announcements">
          <Button variant="outline" size="sm">
            Back to Announcement Board
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl mx-auto pb-16">
      {/* Top Action Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <Link
          href="/app/campus/announcements"
          className="text-xs text-slate-400 hover:text-white inline-flex items-center gap-1.5 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Announcements
        </Link>

        {canManage && (
          <div className="flex items-center gap-2">
            {announcement.status === "DRAFT" && (
              <Button
                variant="primary"
                size="sm"
                isLoading={actionLoading}
                onClick={handlePublish}
                className="bg-emerald-600 hover:bg-emerald-500 text-xs"
              >
                Publish Now
              </Button>
            )}
            {announcement.status === "PUBLISHED" && (
              <Button
                variant="outline"
                size="sm"
                isLoading={actionLoading}
                onClick={handleArchive}
                className="border-slate-800 text-slate-400 hover:text-white text-xs"
              >
                Archive
              </Button>
            )}
          </div>
        )}
      </div>

      {feedback && (
        <div className="p-3.5 rounded-xl border border-emerald-500/30 bg-emerald-950/20 text-emerald-300 text-xs flex items-center justify-between">
          <span>{feedback}</span>
          <button onClick={() => setFeedback(null)} className="text-emerald-400 hover:text-white">
            Dismiss
          </button>
        </div>
      )}

      {/* Main Announcement Document Body */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 sm:p-8 space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold px-2.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
              {announcement.category}
            </span>
            <span
              className={`text-[11px] font-bold px-2 py-0.5 rounded-full border ${
                announcement.priority === "URGENT"
                  ? "bg-rose-500/20 text-rose-300 border-rose-500/30 font-black"
                  : announcement.priority === "HIGH"
                  ? "bg-amber-500/20 text-amber-300 border-amber-500/30"
                  : "bg-blue-500/20 text-blue-300 border-blue-500/30"
              }`}
            >
              Priority: {announcement.priority}
            </span>
            {announcement.isPinned && (
              <span className="flex items-center gap-1 text-[11px] font-semibold text-amber-400 bg-amber-950/30 px-2 py-0.5 rounded border border-amber-900/40">
                <Pin className="h-3 w-3 fill-amber-400" /> Pinned
              </span>
            )}
          </div>

          <div className="text-xs text-slate-400 font-mono">
            Status: <span className="font-bold text-white uppercase">{announcement.status}</span>
          </div>
        </div>

        <h1 className="text-2xl font-black text-white tracking-tight leading-snug">
          {announcement.title}
        </h1>

        {/* Metadata Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-4 rounded-xl bg-slate-950/80 border border-slate-800 text-xs">
          <div>
            <span className="text-[10px] text-slate-500 uppercase font-mono block">Published By</span>
            <span className="font-bold text-white mt-0.5 block">{announcement.publisher}</span>
            <span className="text-[11px] text-slate-400">{announcement.publisherRole}</span>
          </div>

          <div>
            <span className="text-[10px] text-slate-500 uppercase font-mono block">Target Audience</span>
            <span className="font-bold text-indigo-400 mt-0.5 block">
              {announcement.audience.type.replace("_", " ")}
            </span>
            <span className="text-[11px] text-slate-400">
              ~{announcement.audience.estimatedRecipientCount?.toLocaleString() || 150} verified recipients
            </span>
          </div>

          <div>
            <span className="text-[10px] text-slate-500 uppercase font-mono block">Timeline</span>
            <span className="font-mono text-slate-300 mt-0.5 block">{announcement.publishDate}</span>
            <span className="text-[11px] text-slate-500">
              Expires: {announcement.expiryDate || "Indefinite"}
            </span>
          </div>
        </div>

        {/* Content */}
        <div className="prose prose-invert max-w-none text-slate-200 text-sm leading-relaxed space-y-4 pt-2 whitespace-pre-line">
          {announcement.content}
        </div>

        {/* Delivery Summary Banner */}
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-950 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
            <span className="text-slate-300">
              Delivered across <strong>In-App</strong> and <strong>Email</strong> to{" "}
              <strong className="text-white">{announcement.deliveredCount.toLocaleString()}</strong> users.
            </span>
          </div>
          <span className="text-slate-500 font-mono text-[11px]">
            {announcement.viewCount} views tracked
          </span>
        </div>
      </div>

      {/* Audit Timeline Section */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-4">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <History className="h-4 w-4 text-indigo-400" />
          Publication & Audit Log
        </h3>

        <div className="space-y-4 border-l border-slate-800 ml-3 pl-4">
          {announcement.timeline.map((entry) => (
            <div key={entry.id} className="relative space-y-1 text-xs">
              <div className="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full bg-indigo-500 ring-4 ring-slate-950" />
              <div className="font-bold text-white">{entry.action}</div>
              <div className="text-slate-400">Actor: {entry.actor}</div>
              {entry.details && <div className="text-slate-400 text-[11px]">{entry.details}</div>}
              <div className="text-[10px] text-slate-500 font-mono">{entry.timestamp}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
