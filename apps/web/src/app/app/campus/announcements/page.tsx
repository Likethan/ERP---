"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { campusService } from "@/services/campus.service";
import {
  AnnouncementItem,
  AnnouncementPriority,
  AnnouncementStatus,
  EventAudienceTarget,
} from "@/types/campus";
import { useAuth } from "@/lib/auth-context";
import { DataGrid, ColumnDef } from "@/components/data-grid/data-grid";
import { AudienceBuilder } from "@/components/campus/audience-builder";
import {
  FileText,
  Plus,
  Calendar,
  Users,
  Eye,
  CheckCircle2,
  Archive,
  AlertTriangle,
  Pin,
  Clock,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";

const ALL_PRIORITIES: AnnouncementPriority[] = ["LOW", "NORMAL", "HIGH", "URGENT"];
const ALL_STATUSES: AnnouncementStatus[] = ["DRAFT", "SCHEDULED", "PUBLISHED", "EXPIRED", "ARCHIVED"];

export default function CampusAnnouncementsCenterPage() {
  const { user, hasPermission } = useAuth();
  const [announcements, setAnnouncements] = useState<AnnouncementItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [priorityFilter, setPriorityFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Create Announcement Modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newSummary, setNewSummary] = useState("");
  const [newContent, setNewContent] = useState("");
  const [newCategory, setNewCategory] = useState<"ACADEMIC" | "EXAMINATION" | "HOSTEL" | "GENERAL" | "URGENT">("ACADEMIC");
  const [newPriority, setNewPriority] = useState<AnnouncementPriority>("NORMAL");
  const [newExpiry, setNewExpiry] = useState("2026-11-01");
  const [newAudience, setNewAudience] = useState<EventAudienceTarget>({
    type: "ALL_STUDENTS",
    estimatedCount: 4200,
  });

  // Feedback & Action
  const [feedback, setFeedback] = useState<string | null>(null);

  const canCreate = hasPermission("campus.create_announcements") || hasPermission("*");

  const loadAnnouncements = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await campusService.getAnnouncements();
      if (res.success && res.data) {
        setAnnouncements(res.data);
      } else {
        setError(res.error || "Failed to load announcements");
      }
    } catch (e: any) {
      setError(e.message || "An unexpected error occurred");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnnouncements();
  }, []);

  const handleCreateAnnouncement = async (asPublished = false) => {
    if (!newTitle.trim() || !newContent.trim()) {
      alert("Title and content are required.");
      return;
    }

    try {
      setCreating(true);
      const res = await campusService.createAnnouncement({
        title: newTitle,
        summary: newSummary || newContent.slice(0, 100),
        content: newContent,
        category: newCategory,
        priority: newPriority,
        publisher: user?.first_name ? `${user.first_name} ${user.last_name}` : "Administration",
        publisherRole: "Institutional Communications Officer",
        audience: {
          type: newAudience.type as any,
          departmentName: newAudience.departmentName,
          programName: newAudience.programName,
          semester: newAudience.semester,
          section: newAudience.section,
          clubName: newAudience.clubName,
          estimatedRecipientCount: newAudience.estimatedCount,
          description: `Targeting ${newAudience.type} (~${newAudience.estimatedCount} users)`,
        },
        isPinned: newPriority === "URGENT" || newPriority === "HIGH",
        publishDate: new Date().toLocaleString(),
        expiryDate: newExpiry,
      }, user?.first_name || "Administrator");

      if (res.success && res.data) {
        if (asPublished) {
          await campusService.publishAnnouncement(res.data.id, user?.first_name || "Administrator");
          setFeedback(`Announcement published and dispatched to ${res.data.audience.estimatedRecipientCount} users!`);
        } else {
          setFeedback(`Announcement draft saved successfully.`);
        }
        setCreateModalOpen(false);
        setNewTitle("");
        setNewContent("");
        setNewSummary("");
        loadAnnouncements();
      }
    } finally {
      setCreating(false);
    }
  };

  const handlePublish = async (id: string) => {
    await campusService.publishAnnouncement(id, user?.first_name || "Administrator");
    setFeedback("Announcement published.");
    loadAnnouncements();
  };

  const handleArchive = async (id: string) => {
    await campusService.archiveAnnouncement(id, user?.first_name || "Administrator");
    setFeedback("Announcement archived.");
    loadAnnouncements();
  };

  const filteredAnnouncements = useMemo(() => {
    return announcements.filter((a) => {
      const matchPri = priorityFilter === "ALL" || a.priority === priorityFilter;
      const matchStatus = statusFilter === "ALL" || a.status === statusFilter;
      const matchSearch =
        searchQuery === "" ||
        a.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        a.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
        a.publisher.toLowerCase().includes(searchQuery.toLowerCase());
      return matchPri && matchStatus && matchSearch;
    });
  }, [announcements, priorityFilter, statusFilter, searchQuery]);

  const columns: ColumnDef<AnnouncementItem>[] = [
    {
      id: "title",
      header: "Title & Content",
      accessorFn: (row: AnnouncementItem) => row.title,
      sortable: true,
      cell: (row) => (
        <div className="space-y-1 max-w-md">
          <div className="flex items-center gap-1.5">
            {row.isPinned && <Pin className="h-3 w-3 text-amber-400 shrink-0 fill-amber-400" />}
            <Link
              href={`/app/campus/announcements/${row.id}`}
              className="font-bold text-white text-xs hover:text-indigo-400 transition-colors truncate block"
            >
              {row.title}
            </Link>
          </div>
          <p className="text-[11px] text-slate-400 line-clamp-1">{row.summary || row.content}</p>
        </div>
      ),
    },
    {
      id: "category",
      header: "Category",
      accessorFn: (row: AnnouncementItem) => row.category,
      sortable: true,
      cell: (row) => (
        <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
          {row.category}
        </span>
      ),
    },
    {
      id: "audience",
      header: "Target Audience",
      accessorFn: (row: AnnouncementItem) => row.audience.type,
      cell: (row) => (
        <div className="text-xs">
          <span className="text-slate-300 block font-medium truncate max-w-[140px]">
            {row.audience.type.replace("_", " ")}
          </span>
          <span className="text-[10px] text-slate-500 font-mono">
            ~{row.audience.estimatedRecipientCount?.toLocaleString() || 150} users
          </span>
        </div>
      ),
    },
    {
      id: "publisher",
      header: "Publisher",
      accessorFn: (row: AnnouncementItem) => row.publisher,
      sortable: true,
      cell: (row) => (
        <div className="text-xs text-slate-300">
          <div className="font-medium text-white">{row.publisher}</div>
          <div className="text-[10px] text-slate-500">{row.publisherRole}</div>
        </div>
      ),
    },
    {
      id: "publishedDate",
      header: "Published Date",
      accessorFn: (row: AnnouncementItem) => row.publishDate,
      sortable: true,
      cell: (row) => <span className="text-xs text-slate-400 font-mono">{row.publishDate}</span>,
    },
    {
      id: "priority",
      header: "Priority",
      accessorFn: (row: AnnouncementItem) => row.priority,
      sortable: true,
      cell: (row) => {
        const colors: Record<AnnouncementPriority, string> = {
          URGENT: "bg-rose-500/20 text-rose-300 border-rose-500/30 font-black",
          HIGH: "bg-amber-500/20 text-amber-300 border-amber-500/30 font-bold",
          NORMAL: "bg-blue-500/20 text-blue-300 border-blue-500/30",
          LOW: "bg-slate-800 text-slate-400 border-slate-700",
        };
        return (
          <span className={`px-2 py-0.5 rounded text-[10px] border ${colors[row.priority]}`}>
            {row.priority}
          </span>
        );
      },
    },
    {
      id: "status",
      header: "Status",
      accessorFn: (row: AnnouncementItem) => row.status,
      sortable: true,
      cell: (row) => (
        <span
          className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
            row.status === "PUBLISHED"
              ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
              : row.status === "SCHEDULED"
              ? "bg-purple-500/20 text-purple-300 border-purple-500/30"
              : "bg-slate-800 text-slate-400 border-slate-700"
          }`}
        >
          {row.status}
        </span>
      ),
    },
    {
      id: "actions",
      header: "Actions",
      cell: (row) => (
        <div className="flex items-center gap-1.5">
          <Link
            href={`/app/campus/announcements/${row.id}`}
            className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800"
            title="View Details"
          >
            <Eye className="h-4 w-4" />
          </Link>
          {row.status === "DRAFT" && (
            <button
              onClick={() => handlePublish(row.id)}
              className="p-1 rounded text-emerald-400 hover:bg-emerald-950/40"
              title="Publish"
            >
              <CheckCircle2 className="h-4 w-4" />
            </button>
          )}
          {row.status === "PUBLISHED" && (
            <button
              onClick={() => handleArchive(row.id)}
              className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800"
              title="Archive"
            >
              <Archive className="h-4 w-4" />
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6 animate-fade-in pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <Link href="/app/campus" className="text-xs text-slate-400 hover:text-indigo-400">
              Campus Hub
            </Link>
            <span className="text-slate-600">/</span>
            <span className="text-xs text-slate-200 font-semibold">Announcements</span>
          </div>
          <h1 className="mt-1 text-2xl font-black tracking-tight text-white flex items-center gap-2.5">
            <FileText className="h-6 w-6 text-blue-400" />
            Institutional Announcements Center
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Publish official circulars, examination timetables, emergency advisories, and targeted cohort notices.
          </p>
        </div>

        {canCreate && (
          <Button
            variant="primary"
            size="sm"
            onClick={() => setCreateModalOpen(true)}
            leftIcon={<Plus className="h-4 w-4" />}
            className="bg-indigo-600 hover:bg-indigo-500 shadow-md shadow-indigo-600/30"
          >
            Compose Announcement
          </Button>
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

      {/* Filter Bar */}
      <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-slate-400">Priority:</span>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-white"
            >
              <option value="ALL">All Priorities</option>
              {ALL_PRIORITIES.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-xs text-slate-400">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-white"
            >
              <option value="ALL">All Statuses</option>
              {ALL_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          {(priorityFilter !== "ALL" || statusFilter !== "ALL" || searchQuery !== "") && (
            <button
              onClick={() => {
                setPriorityFilter("ALL");
                setStatusFilter("ALL");
                setSearchQuery("");
              }}
              className="text-xs text-rose-400 hover:text-rose-300 ml-2"
            >
              Clear Filters
            </button>
          )}
        </div>

        <div className="text-xs text-slate-400 font-mono">
          Showing <strong>{filteredAnnouncements.length}</strong> of {announcements.length} notices
        </div>
      </div>

      {/* Announcements DataGrid */}
      <DataGrid
        data={filteredAnnouncements}
        columns={columns}
        keyExtractor={(item) => item.id}
        loading={loading}
        error={error}
        onRetry={loadAnnouncements}
        searchPlaceholder="Search announcement title, publisher, or content..."
        onSearchChange={setSearchQuery}
        exportFileName="campus-announcements"
        enableExport={true}
        enableDensityToggle={true}
        emptyTitle="No announcements found"
        emptyDescription="There are no announcements matching your query criteria."
      />

      {/* Compose Announcement Modal Dialog */}
      <Dialog
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Compose Official Announcement"
      >
        <div className="space-y-4 max-h-[75vh] overflow-y-auto pr-1">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">
              Title <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="e.g. Schedule for Continuous Internal Assessment (CIA-1) Published"
              className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-indigo-500 font-medium"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Category</label>
              <select
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value as any)}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2 text-xs text-white"
              >
                <option value="ACADEMIC">ACADEMIC</option>
                <option value="EXAMINATION">EXAMINATION</option>
                <option value="HOSTEL">HOSTEL</option>
                <option value="GENERAL">GENERAL</option>
                <option value="URGENT">URGENT</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Priority</label>
              <select
                value={newPriority}
                onChange={(e) => setNewPriority(e.target.value as any)}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2 text-xs text-white font-bold"
              >
                <option value="LOW">LOW</option>
                <option value="NORMAL">NORMAL</option>
                <option value="HIGH">HIGH</option>
                <option value="URGENT">URGENT</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Summary (1-2 sentences)</label>
            <input
              type="text"
              value={newSummary}
              onChange={(e) => setNewSummary(e.target.value)}
              placeholder="Concise summary displayed in push notifications and feeds..."
              className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2 text-xs text-white"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">
              Full Content Body <span className="text-rose-400">*</span>
            </label>
            <textarea
              rows={4}
              value={newContent}
              onChange={(e) => setNewContent(e.target.value)}
              placeholder="Detailed announcement content with instructions, links, and deadlines..."
              className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-white"
            />
          </div>

          {/* Reusable AudienceBuilder component */}
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-2">Audience Targeting Scope</label>
            <AudienceBuilder value={newAudience} onChange={setNewAudience} />
          </div>

          {/* Explicit Confirmation Notice */}
          <div className="p-3 rounded-xl bg-indigo-950/20 border border-indigo-500/30 text-xs text-slate-300 space-y-1">
            <span className="font-bold text-white block">Pre-Publication Confirmation:</span>
            <span>Target Audience: <strong>{newAudience.type}</strong> (~{newAudience.estimatedCount} users)</span>
            <div>Priority: <strong className="text-indigo-400">{newPriority}</strong></div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
            <Button variant="ghost" size="sm" onClick={() => setCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="outline"
              size="sm"
              isLoading={creating}
              onClick={() => handleCreateAnnouncement(false)}
            >
              Save as Draft
            </Button>
            <Button
              variant="primary"
              size="sm"
              isLoading={creating}
              onClick={() => handleCreateAnnouncement(true)}
              className="bg-emerald-600 hover:bg-emerald-500 font-bold"
            >
              Publish Now
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
