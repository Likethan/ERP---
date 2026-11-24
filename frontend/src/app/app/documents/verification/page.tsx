"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { documentVerificationService } from "@/services/document-verification.service";
import {
  DocumentItem,
  DocumentCategoryCode,
  DocumentStatus,
  DocumentOwnerType,
  VerificationPriority,
} from "@campusos/types";
import { DocumentStatusBadge } from "@/components/documents/document-status-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import {
  ShieldCheck,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  Clock,
  Eye,
  ArrowRight,
  AlertTriangle,
  User,
  Layers,
} from "lucide-react";

export default function VerificationQueuePage() {
  const [queue, setQueue] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("ALL");
  const [priorityFilter, setPriorityFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [ownerTypeFilter, setOwnerTypeFilter] = useState("ALL");

  useEffect(() => {
    async function loadQueue() {
      try {
        setLoading(true);
        const res = await documentVerificationService.listVerificationQueue();
        if (res.success && res.data) {
          setQueue(res.data);
        }
      } catch (err) {
        console.error("Failed to load verification queue:", err);
      } finally {
        setLoading(false);
      }
    }

    loadQueue();
  }, []);

  const filteredQueue = queue.filter((doc) => {
    if (categoryFilter !== "ALL" && doc.category !== categoryFilter)
      return false;
    if (priorityFilter !== "ALL" && doc.priority !== priorityFilter)
      return false;
    if (statusFilter !== "ALL" && doc.status !== statusFilter) return false;
    if (ownerTypeFilter !== "ALL" && doc.ownerType !== ownerTypeFilter)
      return false;

    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        doc.name.toLowerCase().includes(q) ||
        doc.ownerName.toLowerCase().includes(q) ||
        (doc.ownerRollNumber &&
          doc.ownerRollNumber.toLowerCase().includes(q)) ||
        doc.documentType.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-amber-400 mb-1">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Administrative Compliance Review Desk</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-100">
            Document Verification Queue
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Review uploaded student and staff credentials, verify regulatory
            authenticity, or request re-uploads.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg">
          <Clock className="w-4 h-4 text-amber-400" />
          <span>
            Active Review Items:{" "}
            <strong className="text-slate-100 font-mono">
              {filteredQueue.length}
            </strong>
          </span>
        </div>
      </div>

      {/* Filter Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 bg-slate-900 border border-slate-800 p-4 rounded-xl">
        <div className="lg:col-span-2 relative">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search candidate, roll no, or document title..."
            className="pl-9 bg-slate-950 border-slate-800 text-xs"
          />
        </div>

        <div>
          <Select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="bg-slate-950 border-slate-800 text-xs"
          >
            <option value="ALL">All Categories</option>
            {Object.values(DocumentCategoryCode).map((code) => (
              <option key={code} value={code}>
                {code}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <Select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="bg-slate-950 border-slate-800 text-xs"
          >
            <option value="ALL">All Priorities</option>
            {Object.values(VerificationPriority).map((p) => (
              <option key={p} value={p}>
                {p} Priority
              </option>
            ))}
          </Select>
        </div>

        <div>
          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-950 border-slate-800 text-xs"
          >
            <option value="ALL">All Statuses</option>
            <option value={DocumentStatus.UPLOADED}>
              Uploaded (Unassigned)
            </option>
            <option value={DocumentStatus.UNDER_REVIEW}>
              Under Active Review
            </option>
            <option value={DocumentStatus.REJECTED}>
              Rejected / Pending Re-upload
            </option>
          </Select>
        </div>
      </div>

      {/* Verification Queue Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        {loading ? (
          <div className="py-20 text-center text-xs text-slate-500">
            Loading verification queue...
          </div>
        ) : filteredQueue.length === 0 ? (
          <div className="py-16 text-center text-xs text-slate-500">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
            No documents currently require verification. All queues cleared!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-3.5 px-4">Document Title</th>
                  <th className="py-3.5 px-4">Owner / Candidate</th>
                  <th className="py-3.5 px-4">Category</th>
                  <th className="py-3.5 px-4">Uploaded</th>
                  <th className="py-3.5 px-4">Priority</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Assigned Reviewer</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80 text-slate-300">
                {filteredQueue.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3.5 px-4">
                      <Link
                        href={`/app/documents/verification/${doc.id}`}
                        className="font-semibold text-slate-100 hover:text-blue-400 transition"
                      >
                        {doc.name}
                      </Link>
                      <div className="text-[11px] text-slate-500 mt-0.5">
                        {doc.documentType} • {doc.fileSize}
                      </div>
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="font-medium text-slate-200">
                        {doc.ownerName}
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono">
                        {doc.ownerRollNumber || doc.ownerType}
                      </div>
                    </td>

                    <td className="py-3.5 px-4">
                      <span className="font-medium text-blue-400">
                        {doc.category}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-slate-400">
                      {new Date(doc.uploadedAt).toLocaleDateString()}
                    </td>

                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold ${
                          doc.priority === VerificationPriority.URGENT
                            ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                            : doc.priority === VerificationPriority.HIGH
                              ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                              : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {doc.priority || "NORMAL"}
                      </span>
                    </td>

                    <td className="py-3.5 px-4">
                      <DocumentStatusBadge status={doc.status} />
                    </td>

                    <td className="py-3.5 px-4">
                      <span className="text-slate-300">
                        {doc.assignedReviewerName || "Unassigned"}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <Link href={`/app/documents/verification/${doc.id}`}>
                        <Button
                          size="sm"
                          className="text-xs h-7 gap-1 bg-blue-600 hover:bg-blue-700"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          Review Workspace
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
