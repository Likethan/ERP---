"use client";

import React, { useEffect, useState } from "react";
import { vicePrincipalService } from "@/services/vice-principal.service";
import { InstitutionalAnnouncement } from "@/types/vice-principal";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Bell,
  Send,
  Pin,
  Clock,
  User,
  Plus,
  RefreshCw,
  CheckCircle2,
} from "lucide-react";
import { useToast } from "@/components/ui/toast";

export default function VicePrincipalAnnouncementsPage() {
  const { showToast } = useToast();
  const [announcements, setAnnouncements] = useState<
    InstitutionalAnnouncement[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);

  // Form State
  const [title, setTitle] = useState("");
  const [audience, setAudience] = useState("ALL_HODS_AND_FACULTY");
  const [priority, setPriority] = useState<"ROUTINE" | "HIGH" | "CRITICAL">(
    "HIGH",
  );
  const [summary, setSummary] = useState("");
  const [pinned, setPinned] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadAnnouncements();
  }, []);

  const loadAnnouncements = async () => {
    setLoading(true);
    try {
      const res = await vicePrincipalService.getAnnouncements();
      if (res.success && res.data) {
        setAnnouncements(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !summary.trim()) {
      showToast({
        title: "Incomplete Announcement",
        message: "Please provide both title and circular directives.",
        type: "error",
      });
      return;
    }

    setSubmitting(true);
    try {
      await vicePrincipalService.createAnnouncement({
        title,
        target_audience: audience,
        priority,
        summary,
        pinned,
      });
      showToast({
        title: "Executive Circular Dispatched",
        message: `Broadcast successfully dispatched to ${audience}.`,
        type: "success",
      });
      setTitle("");
      setSummary("");
      setModalOpen(false);
      loadAnnouncements();
    } catch {
      showToast({
        title: "Dispatch Error",
        message: "Unable to publish circular.",
        type: "error",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Institutional Directives & Executive Circulars
          </h1>
          <p className="text-sm text-slate-600">
            Broadcast academic circulars, syllabus completion mandates, and
            examination instructions to Heads of Departments and faculty.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={() => setModalOpen(true)}
            className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs gap-1.5"
          >
            <Plus className="h-4 w-4" />
            <span>Publish Circular</span>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={loadAnnouncements}
            className="gap-1.5"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Refresh</span>
          </Button>
        </div>
      </div>

      {/* Announcements Stream */}
      <div className="space-y-4">
        {announcements.map((item) => (
          <Card
            key={item.id}
            className={`shadow-xs transition-colors ${
              item.pinned
                ? "border-indigo-300 bg-white"
                : "border-slate-200 bg-slate-50/50"
            }`}
          >
            <CardHeader className="pb-2">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    {item.pinned && (
                      <span className="inline-flex items-center gap-1 rounded bg-indigo-50 border border-indigo-200 px-2 py-0.5 text-[10px] font-bold text-indigo-700">
                        <Pin className="h-2.5 w-2.5" /> Pinned Directive
                      </span>
                    )}
                    <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-700 uppercase">
                      Audience: {item.target_audience.replace(/_/g, " ")}
                    </span>
                    <Badge
                      variant={
                        item.priority === "CRITICAL"
                          ? "destructive"
                          : item.priority === "HIGH"
                            ? "warning"
                            : "default"
                      }
                      className="text-[10px]"
                    >
                      {item.priority} PRIORITY
                    </Badge>
                  </div>
                  <CardTitle className="text-base font-bold text-slate-900 pt-1">
                    {item.title}
                  </CardTitle>
                </div>
                <div className="text-right text-[11px] text-slate-400 font-mono shrink-0">
                  {new Date(item.published_at).toLocaleString()}
                </div>
              </div>
            </CardHeader>

            <CardContent className="pt-2">
              <p className="text-xs text-slate-700 leading-relaxed font-sans">
                {item.summary}
              </p>
              <div className="mt-3 flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-100">
                <span className="flex items-center gap-1">
                  <User className="h-3 w-3 text-slate-400" />
                  Authorized by: <b>{item.author}</b>
                </span>
                <span className="font-mono text-[10px] text-slate-400">
                  REF: {item.id}
                </span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Publish Circular Dialog */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Bell className="h-5 w-5 text-indigo-600" />
                <h3 className="text-base font-bold text-slate-900">
                  Publish Institutional Executive Circular
                </h3>
              </div>
              <button
                onClick={() => setModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Circular Title
                </label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g., Mandatory Mid-Semester Lesson Plan Review Directive"
                  className="w-full rounded-lg border border-slate-200 p-2 text-xs text-slate-900 focus:outline-hidden focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Target Audience
                  </label>
                  <select
                    value={audience}
                    onChange={(e) => setAudience(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 bg-white p-2 text-xs text-slate-900 focus:outline-hidden"
                  >
                    <option value="ALL_HODS">All Heads of Department</option>
                    <option value="ALL_FACULTY">All Teaching Faculty</option>
                    <option value="ALL_HODS_AND_FACULTY">
                      All HODs & Teaching Faculty
                    </option>
                    <option value="BOARD_OF_EXAMINERS">
                      Board of Examiners
                    </option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Priority Level
                  </label>
                  <select
                    value={priority}
                    onChange={(e) =>
                      setPriority(
                        e.target.value as "ROUTINE" | "HIGH" | "CRITICAL",
                      )
                    }
                    className="w-full rounded-lg border border-slate-200 bg-white p-2 text-xs text-slate-900 focus:outline-hidden"
                  >
                    <option value="ROUTINE">Routine Notice</option>
                    <option value="HIGH">High Priority</option>
                    <option value="CRITICAL">
                      Critical Mandatory Directive
                    </option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Circular Directives & Full Text
                </label>
                <textarea
                  required
                  rows={4}
                  value={summary}
                  onChange={(e) => setSummary(e.target.value)}
                  placeholder="State the academic policy, compliance requirements, deadlines, or action items..."
                  className="w-full rounded-lg border border-slate-200 p-2.5 text-xs text-slate-900 focus:outline-hidden focus:border-indigo-500"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="pinNotice"
                  checked={pinned}
                  onChange={(e) => setPinned(e.target.checked)}
                  className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                />
                <label
                  htmlFor="pinNotice"
                  className="text-xs font-medium text-slate-700 cursor-pointer"
                >
                  Pin this circular at top of institutional notice board
                </label>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setModalOpen(false)}
                  disabled={submitting}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={submitting}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs gap-1"
                >
                  <Send className="h-3.5 w-3.5" />
                  <span>
                    {submitting ? "Broadcasting..." : "Broadcast Circular"}
                  </span>
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
