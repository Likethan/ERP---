"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { examinationsService } from "@/services/examinations.service";
import { ResultPublication, PublicationStatus } from "@/types/examinations";
import { DataGrid } from "@/components/data-grid/data-grid";
import { ColumnDef } from "@/components/data-grid/data-grid.types";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { StatCard } from "@/components/ui/stat-card";
import { useToast } from "@/components/ui/toast";
import {
  Globe,
  Plus,
  Lock,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Filter,
  Calendar,
  Layers,
  ArrowRight,
} from "lucide-react";

export default function ResultPublicationsPage() {
  const { hasPermission } = useAuth();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [publications, setPublications] = useState<ResultPublication[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // Create Batch Modal State
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [program, setProgram] = useState("B.Tech Computer Science & Engineering");
  const [department, setDepartment] = useState("Computer Science & Engineering");
  const [semester, setSemester] = useState(5);
  const [publicationDate, setPublicationDate] = useState(new Date().toISOString().split("T")[0]);
  const [notes, setNotes] = useState("");
  const [creating, setCreating] = useState(false);

  // Publish / Revoke Action State
  const [actionModalOpen, setActionModalOpen] = useState(false);
  const [selectedBatch, setSelectedBatch] = useState<ResultPublication | null>(null);
  const [actionType, setActionType] = useState<"PUBLISH" | "REVOKE">("PUBLISH");
  const [actionNotes, setActionNotes] = useState("");
  const [processing, setProcessing] = useState(false);

  const loadPublications = async () => {
    try {
      setLoading(true);
      const res = await examinationsService.getResultPublications({
        status: statusFilter !== "ALL" ? statusFilter : undefined,
      });
      setPublications(res.data);
    } catch {
      showToast({ title: "Error", message: "Failed to load publication batches", type: "error" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPublications();
  }, [statusFilter]);

  const handleCreateBatch = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setCreating(true);
      await examinationsService.createPublication({
        program,
        department,
        semester,
        publicationDate,
        notes,
      });
      showToast({ title: "Success", message: "Publication batch generated.", type: "success" });
      setCreateModalOpen(false);
      loadPublications();
    } catch (err: unknown) {
      showToast({
        title: "Error",
        message: err instanceof Error ? err.message : "Failed to create publication batch",
        type: "error",
      });
    } finally {
      setCreating(false);
    }
  };

  const handleExecuteAction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedBatch) return;

    try {
      setProcessing(true);
      if (actionType === "PUBLISH") {
        await examinationsService.publishResults(selectedBatch.id);
        showToast({ title: "Published", message: "Results published to student portal.", type: "success" });
      } else {
        await examinationsService.revokePublication(selectedBatch.id, actionNotes);
        showToast({ title: "Revoked", message: "Publication batch unpublished.", type: "info" });
      }
      setActionModalOpen(false);
      loadPublications();
    } catch (err: unknown) {
      showToast({
        title: "Error",
        message: err instanceof Error ? err.message : "Action failed",
        type: "error",
      });
    } finally {
      setProcessing(false);
    }
  };

  const publishedCount = publications.filter((p) => p.status === "PUBLISHED").length;
  const readyCount = publications.filter((p) => p.status === "READY").length;

  const columns: ColumnDef<ResultPublication>[] = useMemo(
    () => [
      {
        id: "batch",
        header: "Batch Identifier",
        cell: (row) => (
          <div>
            <span className="font-mono font-bold text-slate-900 dark:text-white">
              {row.batchNumber}
            </span>
            <div className="text-xs text-slate-500 mt-0.5">
              {row.examinationName}
            </div>
          </div>
        ),
      },
      {
        id: "cohort",
        header: "Program & Semester",
        cell: (row) => (
          <div className="text-xs">
            <span className="font-semibold text-slate-800 dark:text-slate-200">
              {row.program}
            </span>
            <p className="text-slate-500">Semester {row.semester} • AY {row.academicYear}</p>
          </div>
        ),
      },
      {
        id: "candidates",
        header: "Candidate Results",
        cell: (row) => (
          <div className="text-xs font-mono">
            <span className="font-bold text-slate-900 dark:text-white">
              {row.resultCount} records
            </span>
            <div className="text-[11px] text-slate-400">Target: {row.publicationDate}</div>
          </div>
        ),
      },
      {
        id: "status",
        header: "Status",
        cell: (row) => (
          <span
            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold ${
              row.status === "PUBLISHED"
                ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                : row.status === "READY"
                ? "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300"
                : row.status === "REVOKED"
                ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
                : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
            }`}
          >
            {row.status === "PUBLISHED" && <Globe className="h-3 w-3" />}
            {row.status}
          </span>
        ),
      },
      {
        id: "notes",
        header: "Audit Notes",
        cell: (row) => (
          <div className="text-xs text-slate-500 truncate max-w-xs" title={row.notes || "Ratified by examination board"}>
            {row.notes || "Ratified by examination board"}
          </div>
        ),
      },
      {
        id: "actions",
        header: "Actions",
        cell: (row) => (
          <div className="flex items-center gap-2">
            {row.status === "READY" && (
              <Button
                size="sm"
                variant="primary"
                onClick={() => {
                  setSelectedBatch(row);
                  setActionType("PUBLISH");
                  setActionModalOpen(true);
                }}
                className="h-7 text-xs"
              >
                Publish
              </Button>
            )}

            {row.status === "PUBLISHED" && (
              <Button
                size="sm"
                variant="destructive"
                onClick={() => {
                  setSelectedBatch(row);
                  setActionType("REVOKE");
                  setActionNotes("");
                  setActionModalOpen(true);
                }}
                className="h-7 text-xs"
              >
                Revoke
              </Button>
            )}
          </div>
        ),
      },
    ],
    []
  );

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-teal-100 text-teal-800 dark:bg-teal-950/60 dark:text-teal-300">
              Controlled Release
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">Student Portal Publications</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Result Publications Ledger
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Publish ratified exam results in deliberate, audited administrative batches to the public student portal.
          </p>
        </div>

        <Button variant="primary" className="gap-2" onClick={() => setCreateModalOpen(true)}>
          <Plus className="h-4 w-4" />
          Prepare Publication Batch
        </Button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Publication Batches"
          value={String(publications.length)}
          description="Institutional release records"
          icon={<Layers className="h-5 w-5 text-indigo-600" />}
        />
        <StatCard
          title="Active Published Batches"
          value={String(publishedCount)}
          description="Live on student dashboards"
          icon={<Globe className="h-5 w-5 text-emerald-600" />}
        />
        <StatCard
          title="Batches Ready to Release"
          value={String(readyCount)}
          description="Awaiting final controller sign-off"
          icon={<CheckCircle2 className="h-5 w-5 text-blue-600" />}
        />
        <StatCard
          title="Administrative Control"
          value="Audited"
          description="Zero unratified releases"
          icon={<Lock className="h-5 w-5 text-purple-600" />}
        />
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3 bg-slate-50/70 p-3 rounded-xl border border-slate-200 dark:bg-slate-900/60 dark:border-slate-800 text-xs">
        <div className="flex items-center gap-1.5 text-slate-500 font-medium">
          <Filter className="h-3.5 w-3.5" />
          Filter Batches:
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
        >
          <option value="ALL">All Statuses</option>
          <option value="READY">Ready for Release</option>
          <option value="PUBLISHED">Published</option>
          <option value="DRAFT">Draft Preparation</option>
          <option value="REVOKED">Revoked</option>
        </select>
      </div>

      {/* Enterprise DataGrid */}
      <DataGrid<ResultPublication>
        data={publications}
        columns={columns}
        keyExtractor={(row) => row.id}
        loading={loading}
        searchPlaceholder="Search publication batch by number, program, or session..."
        emptyTitle="No publication batches found"
        emptyDescription="Create a new release batch to publish ratified results."
      />

      {/* Create Batch Modal */}
      <Dialog open={createModalOpen} onClose={() => setCreateModalOpen(false)}>
        <form onSubmit={handleCreateBatch} className="p-6 space-y-4 max-w-md">
          <div className="border-b border-slate-200 pb-3 dark:border-slate-800">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">
              Prepare Publication Batch
            </h2>
            <p className="text-xs text-slate-500">Group finalized results for release</p>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Program *
              </label>
              <select
                value={program}
                onChange={(e) => setProgram(e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              >
                <option value="B.Tech Computer Science & Engineering">B.Tech Computer Science & Engineering</option>
                <option value="B.Tech Electronics & Communication">B.Tech Electronics & Communication</option>
                <option value="B.Tech AI & Machine Learning">B.Tech AI & Machine Learning</option>
              </select>
            </div>

            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Semester *
              </label>
              <select
                value={semester}
                onChange={(e) => setSemester(Number(e.target.value))}
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              >
                <option value={5}>Semester 5 (Current Odd Term)</option>
                <option value={4}>Semester 4 (Previous Even Term)</option>
              </select>
            </div>

            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Scheduled Publication Date *
              </label>
              <input
                type="date"
                required
                value={publicationDate}
                onChange={(e) => setPublicationDate(e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>

            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Ratification Resolution Notes
              </label>
              <textarea
                rows={2}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="e.g. Ratified by Board of Studies on Oct 1, 2026."
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
            <Button type="button" variant="outline" onClick={() => setCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={creating}>
              {creating ? "Generating..." : "Generate Batch"}
            </Button>
          </div>
        </form>
      </Dialog>

      {/* Publish or Revoke Confirmation Modal */}
      <Dialog open={actionModalOpen} onClose={() => setActionModalOpen(false)}>
        <form onSubmit={handleExecuteAction} className="p-6 space-y-4 max-w-md">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-full ${actionType === "PUBLISH" ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-700"}`}>
              {actionType === "PUBLISH" ? <Globe className="h-5 w-5" /> : <AlertTriangle className="h-5 w-5" />}
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                {actionType === "PUBLISH" ? "Publish Results to Students" : "Revoke Publication"}
              </h2>
              <p className="text-xs text-slate-500">Batch {selectedBatch?.batchNumber}</p>
            </div>
          </div>

          <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
            {actionType === "PUBLISH"
              ? "Publishing this batch will make marks, grades, and GPA statements visible to enrolled students on their portals."
              : "Revoking will immediately hide this batch from student portals for re-evaluation or moderation corrections."}
          </p>

          {actionType === "REVOKE" && (
            <div className="text-xs">
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Reason for Revocation *
              </label>
              <textarea
                rows={2}
                required
                value={actionNotes}
                onChange={(e) => setActionNotes(e.target.value)}
                placeholder="e.g. Moderation board review requested."
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>
          )}

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
            <Button type="button" variant="outline" onClick={() => setActionModalOpen(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant={actionType === "PUBLISH" ? "primary" : "destructive"}
              disabled={processing}
            >
              {processing ? "Processing..." : `Confirm ${actionType}`}
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
