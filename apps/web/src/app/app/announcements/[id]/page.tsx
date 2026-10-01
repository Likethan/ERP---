"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type { Announcement } from "@campusos/types";

export default function AnnouncementDetailPage() {
  const params = useParams();
  const router = useRouter();
  const annId = params.id as string;
  const { hasPermission } = useAuth();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [ann, setAnn] = useState<Announcement | null>(null);

  const canArchive = hasPermission("announcements:archive");

  const loadAnnouncement = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiFetch<Announcement>(`/api/v1/announcements/${annId}`);
      setAnn(res.data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load announcement.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (annId) {
      loadAnnouncement();
    }
  }, [annId]);

  if (loading) {
    return (
      <div className="py-20 text-center text-slate-500 text-sm">
        <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-r-transparent mb-2" />
        <p>Loading circular document...</p>
      </div>
    );
  }

  if (error || !ann) {
    return (
      <div className="space-y-4">
        <Link href="/app/announcements" className="text-xs text-indigo-400 hover:text-indigo-300">
          ← Back to Announcements
        </Link>
        <div className="p-4 rounded-lg bg-rose-950/40 border border-rose-800/60 text-sm text-rose-300">
          {error || "Circular not found."}
        </div>
      </div>
    );
  }

  const isUrgent = ann.priority === "URGENT";
  const isHigh = ann.priority === "HIGH";

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Top Navigation */}
      <div className="flex items-center justify-between">
        <Link
          href="/app/announcements"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
          </svg>
          Back to Circulars Bulletin
        </Link>
      </div>

      {/* Official Circular Container */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-8 shadow-xl space-y-6">
        {/* Header Metadata */}
        <div className="border-b border-slate-800 pb-6 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              {ann.is_pinned && (
                <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400 bg-amber-950/70 border border-amber-800/60 px-2 py-0.5 rounded">
                  📌 Pinned Circular
                </span>
              )}
              <span
                className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                  isUrgent
                    ? "bg-rose-950 text-rose-300 border border-rose-800"
                    : isHigh
                    ? "bg-amber-950 text-amber-300 border border-amber-800"
                    : "bg-slate-800 text-slate-400"
                }`}
              >
                {ann.priority} Priority
              </span>
              <span className="text-xs text-slate-500 font-mono">
                CIRCULAR ID: {ann.id.slice(0, 8).toUpperCase()}
              </span>
            </div>

            <div className="text-xs text-slate-400">
              Published on {new Date(ann.publish_at).toLocaleDateString(undefined, {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </div>
          </div>

          <h1 className="text-2xl font-bold text-white tracking-tight">
            {ann.title}
          </h1>

          {ann.summary && (
            <p className="text-sm font-medium text-slate-300 italic">
              {ann.summary}
            </p>
          )}

          {/* Target Audience Badges */}
          <div className="flex flex-wrap items-center gap-2 pt-2 text-xs">
            <span className="text-slate-500">Distribution Audience:</span>
            {ann.audiences?.map((aud, i) => (
              <span
                key={i}
                className="px-2 py-0.5 rounded bg-slate-800 text-indigo-400 font-semibold text-[11px]"
              >
                {aud.target_type.replace("_", " ")}
              </span>
            ))}
          </div>
        </div>

        {/* Circular Body Content */}
        <div className="prose prose-invert max-w-none text-sm text-slate-200 leading-relaxed whitespace-pre-line py-2">
          {ann.content}
        </div>

        {/* Footer Authority Sign-off */}
        <div className="pt-6 border-t border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between text-xs text-slate-500 gap-2">
          <div>
            Authorized by: <strong className="text-slate-300">{ann.published_by_name || "Institutional Administration"}</strong>
          </div>
          <div>
            CampusOS Institutional Communication System
          </div>
        </div>
      </div>
    </div>
  );
}
