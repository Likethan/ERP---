"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { documentsService } from "@/services/documents.service";
import { DocumentItem, DocumentCategoryCode, DocumentStatus } from "@campusos/types";
import { DocumentStatusBadge } from "@/components/documents/document-status-badge";
import { DocumentCard } from "@/components/documents/document-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import {
  FileText,
  Upload,
  Search,
  LayoutGrid,
  List,
  Filter,
  ShieldCheck,
  Calendar,
  Clock,
  ArrowRight,
  Eye,
  FileCheck,
  Award,
} from "lucide-react";
import { getDocumentExpiryStatus } from "@/services/document-calculator";
import { ExpiryStatusBadge } from "@/components/documents/document-status-badge";

export default function MyDocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<"table" | "card">("table");

  // Filters
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [activeTab, setActiveTab] = useState<"ALL" | "VERIFIED" | "PENDING" | "REJECTED">("ALL");

  useEffect(() => {
    async function loadMyDocuments() {
      try {
        setLoading(true);
        // By default, current logged-in demo student is Aarav Patel ("stu-001")
        const res = await documentsService.getDocumentsByOwner("stu-001");
        if (res.success && res.data) {
          setDocuments(res.data);
        }
      } catch (err) {
        console.error("Failed to load personal documents:", err);
      } finally {
        setLoading(false);
      }
    }

    loadMyDocuments();
  }, []);

  const filteredDocs = documents.filter((doc) => {
    if (activeTab === "VERIFIED" && doc.status !== DocumentStatus.VERIFIED) return false;
    if (
      activeTab === "PENDING" &&
      doc.status !== DocumentStatus.UPLOADED &&
      doc.status !== DocumentStatus.UNDER_REVIEW
    )
      return false;
    if (activeTab === "REJECTED" && doc.status !== DocumentStatus.REJECTED) return false;

    if (categoryFilter !== "ALL" && doc.category !== categoryFilter) return false;
    if (statusFilter !== "ALL" && doc.status !== statusFilter) return false;

    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        doc.name.toLowerCase().includes(q) ||
        doc.category.toLowerCase().includes(q) ||
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
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-blue-400 mb-1">
            <FileCheck className="w-3.5 h-3.5" />
            <span>Personal Records Center</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-100">My Document Vault</h1>
          <p className="text-sm text-slate-400 mt-1">
            View your verified academic credentials, proof of identity, fee receipts, and career certificates.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link href="/app/documents/certificates">
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              <Award className="w-4 h-4 text-amber-400" />
              Certificate Requests
            </Button>
          </Link>
          <Link href="/app/documents/upload">
            <Button size="sm" className="gap-1.5 text-xs bg-blue-600 hover:bg-blue-700">
              <Upload className="w-4 h-4" />
              Upload Document
            </Button>
          </Link>
        </div>
      </div>

      {/* Tabs Row */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          {(["ALL", "VERIFIED", "PENDING", "REJECTED"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                activeTab === tab
                  ? "bg-blue-600/20 text-blue-400 border border-blue-500/30 font-semibold"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              {tab === "ALL" && `All Documents (${documents.length})`}
              {tab === "VERIFIED" &&
                `Verified (${documents.filter((d) => d.status === DocumentStatus.VERIFIED).length})`}
              {tab === "PENDING" &&
                `In Review (${
                  documents.filter(
                    (d) =>
                      d.status === DocumentStatus.UPLOADED || d.status === DocumentStatus.UNDER_REVIEW
                  ).length
                })`}
              {tab === "REJECTED" &&
                `Rejected / Re-upload (${
                  documents.filter((d) => d.status === DocumentStatus.REJECTED).length
                })`}
            </button>
          ))}
        </div>

        {/* View Switcher Toggle */}
        <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 rounded-lg p-0.5">
          <button
            onClick={() => setViewMode("table")}
            className={`p-1.5 rounded text-xs transition ${
              viewMode === "table" ? "bg-slate-800 text-slate-100 shadow" : "text-slate-400 hover:text-slate-200"
            }`}
            title="Table View"
          >
            <List className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewMode("card")}
            className={`p-1.5 rounded text-xs transition ${
              viewMode === "card" ? "bg-slate-800 text-slate-100 shadow" : "text-slate-400 hover:text-slate-200"
            }`}
            title="Card View"
          >
            <LayoutGrid className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <div className="md:col-span-2 relative">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by document title or classification..."
            className="pl-9 bg-slate-900 border-slate-800 text-xs"
          />
        </div>

        <div>
          <Select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="bg-slate-900 border-slate-800 text-xs"
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
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-900 border-slate-800 text-xs"
          >
            <option value="ALL">All Statuses</option>
            {Object.values(DocumentStatus).map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </Select>
        </div>
      </div>

      {/* Content Area: Table vs Cards */}
      {loading ? (
        <div className="py-20 text-center text-xs text-slate-500">Loading your document vault...</div>
      ) : filteredDocs.length === 0 ? (
        <div className="py-16 text-center bg-slate-900 border border-slate-800 rounded-xl p-8">
          <FileText className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-slate-300">No documents found</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            No records matched your search filters. Click upload below to submit a new file.
          </p>
          <Link href="/app/documents/upload" className="inline-block mt-4">
            <Button size="sm" className="text-xs bg-blue-600 hover:bg-blue-700">
              Upload Document Now
            </Button>
          </Link>
        </div>
      ) : viewMode === "card" ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredDocs.map((doc) => (
            <DocumentCard key={doc.id} document={doc} />
          ))}
        </div>
      ) : (
        /* Desktop Table View */
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-3.5 px-4">Document Title</th>
                  <th className="py-3.5 px-4">Category</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Uploaded Date</th>
                  <th className="py-3.5 px-4">Expiry Date</th>
                  <th className="py-3.5 px-4">Verified By</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80 text-slate-300">
                {filteredDocs.map((doc) => {
                  const expStatus = getDocumentExpiryStatus(doc.expiryDate);
                  return (
                    <tr key={doc.id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-slate-100 hover:text-blue-400 transition">
                          <Link href={`/app/documents/${doc.id}`}>{doc.name}</Link>
                        </div>
                        <div className="text-[11px] text-slate-500 mt-0.5">
                          {doc.documentType} • {doc.fileSize}
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <span className="font-medium text-blue-400">{doc.category}</span>
                      </td>

                      <td className="py-3.5 px-4">
                        <DocumentStatusBadge status={doc.status} />
                      </td>

                      <td className="py-3.5 px-4 text-slate-400">
                        {new Date(doc.uploadedAt).toLocaleDateString()}
                      </td>

                      <td className="py-3.5 px-4">
                        <ExpiryStatusBadge status={expStatus} />
                      </td>

                      <td className="py-3.5 px-4">
                        {doc.verifiedBy ? (
                          <span className="text-emerald-400 flex items-center gap-1 font-medium">
                            <ShieldCheck className="w-3.5 h-3.5" />
                            {doc.verifiedBy.split(" ")[0]} {doc.verifiedBy.split(" ")[1] || ""}
                          </span>
                        ) : (
                          <span className="text-slate-500 italic">Pending</span>
                        )}
                      </td>

                      <td className="py-3.5 px-4 text-right">
                        <Link href={`/app/documents/${doc.id}`}>
                          <Button size="sm" variant="outline" className="text-xs h-7 gap-1">
                            <Eye className="w-3.5 h-3.5" />
                            Details
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
