"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { documentsService } from "@/services/documents.service";
import {
  DocumentItem,
  DocumentCategoryCode,
  DocumentStatus,
  DocumentOwnerType,
} from "@campusos/types";
import { DocumentStatusBadge, ConfidentialityBadge } from "@/components/documents/document-status-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import {
  FileText,
  Search,
  Filter,
  Download,
  Eye,
  ShieldCheck,
  User,
  Building,
  Upload,
  Layers,
} from "lucide-react";
import { getDocumentExpiryStatus } from "@/services/document-calculator";
import { ExpiryStatusBadge } from "@/components/documents/document-status-badge";

export default function AllDocumentsDirectoryPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [ownerTypeFilter, setOwnerTypeFilter] = useState("ALL");

  useEffect(() => {
    async function loadAllDocuments() {
      try {
        setLoading(true);
        const res = await documentsService.listDocuments();
        if (res.success && res.data) {
          setDocuments(res.data);
        }
      } catch (err) {
        console.error("Failed to load all documents:", err);
      } finally {
        setLoading(false);
      }
    }

    loadAllDocuments();
  }, []);

  const filteredDocs = documents.filter((doc) => {
    if (categoryFilter !== "ALL" && doc.category !== categoryFilter) return false;
    if (statusFilter !== "ALL" && doc.status !== statusFilter) return false;
    if (ownerTypeFilter !== "ALL" && doc.ownerType !== ownerTypeFilter) return false;

    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        doc.name.toLowerCase().includes(q) ||
        doc.ownerName.toLowerCase().includes(q) ||
        (doc.ownerRollNumber && doc.ownerRollNumber.toLowerCase().includes(q)) ||
        (doc.documentNumber && doc.documentNumber.toLowerCase().includes(q)) ||
        doc.documentType.toLowerCase().includes(q) ||
        doc.category.toLowerCase().includes(q)
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
            <Layers className="w-3.5 h-3.5" />
            <span>Master Institutional Repository</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-100">All Campus Documents</h1>
          <p className="text-sm text-slate-400 mt-1">
            Master register of all verified, under-review, and archived records across students, faculty, and departments.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            className="text-xs gap-1.5"
            onClick={() => alert(`Exporting ${filteredDocs.length} document records to CSV...`)}
          >
            <Download className="w-4 h-4" />
            Export CSV
          </Button>
          <Link href="/app/documents/upload">
            <Button size="sm" className="text-xs gap-1.5 bg-blue-600 hover:bg-blue-700">
              <Upload className="w-4 h-4" />
              Upload Record
            </Button>
          </Link>
        </div>
      </div>

      {/* Filter Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 bg-slate-900 border border-slate-800 p-4 rounded-xl">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name, owner, roll no..."
            className="pl-9 bg-slate-950 border-slate-800 text-xs"
          />
        </div>

        <div>
          <Select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="bg-slate-950 border-slate-800 text-xs"
          >
            <option value="ALL">All Categories ({documents.length})</option>
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
            className="bg-slate-950 border-slate-800 text-xs"
          >
            <option value="ALL">All Statuses</option>
            {Object.values(DocumentStatus).map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <Select
            value={ownerTypeFilter}
            onChange={(e) => setOwnerTypeFilter(e.target.value)}
            className="bg-slate-950 border-slate-800 text-xs"
          >
            <option value="ALL">All Owner Types</option>
            {Object.values(DocumentOwnerType).map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </Select>
        </div>
      </div>

      {/* Directory Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <span>
            Showing <strong className="text-slate-200">{filteredDocs.length}</strong> registered documents
          </span>
          <span>Security classification enforced via ACL</span>
        </div>

        {loading ? (
          <div className="py-20 text-center text-xs text-slate-500">Loading master directory...</div>
        ) : filteredDocs.length === 0 ? (
          <div className="py-16 text-center text-xs text-slate-500">No documents matched your criteria.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-3.5 px-4">Document Title</th>
                  <th className="py-3.5 px-4">Owner & ID</th>
                  <th className="py-3.5 px-4">Category</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Confidentiality</th>
                  <th className="py-3.5 px-4">Expiry</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80 text-slate-300">
                {filteredDocs.map((doc) => {
                  const expStatus = getDocumentExpiryStatus(doc.expiryDate);
                  return (
                    <tr key={doc.id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3.5 px-4">
                        <Link
                          href={`/app/documents/${doc.id}`}
                          className="font-semibold text-slate-100 hover:text-blue-400 transition"
                        >
                          {doc.name}
                        </Link>
                        <div className="text-[11px] text-slate-500 mt-0.5">
                          {doc.documentType} • {doc.fileSize}
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="font-medium text-slate-200">{doc.ownerName}</div>
                        <div className="text-[11px] text-slate-400 font-mono">
                          {doc.ownerRollNumber || doc.ownerType}
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <span className="font-medium text-blue-400">{doc.category}</span>
                      </td>

                      <td className="py-3.5 px-4">
                        <DocumentStatusBadge status={doc.status} />
                      </td>

                      <td className="py-3.5 px-4">
                        <ConfidentialityBadge level={doc.confidentiality} />
                      </td>

                      <td className="py-3.5 px-4">
                        <ExpiryStatusBadge status={expStatus} />
                      </td>

                      <td className="py-3.5 px-4 text-right">
                        <Link href={`/app/documents/${doc.id}`}>
                          <Button size="sm" variant="outline" className="text-xs h-7 gap-1">
                            <Eye className="w-3.5 h-3.5" />
                            View 360
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
