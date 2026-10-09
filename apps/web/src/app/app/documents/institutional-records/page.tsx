"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { institutionalRecordsService } from "@/services/institutional-records.service";
import {
  InstitutionalRecord,
  InstitutionalRecordStatus,
  ConfidentialityLevel,
} from "@campusos/types";
import { ConfidentialityBadge } from "@/components/documents/document-status-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import {
  Building,
  Search,
  Plus,
  ArrowRight,
  ShieldCheck,
  FileText,
  Calendar,
  Lock,
  Eye,
  Download,
} from "lucide-react";

export default function InstitutionalRecordsPage() {
  const [records, setRecords] = useState<InstitutionalRecord[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("ALL");
  const [confidentialityFilter, setConfidentialityFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");

  useEffect(() => {
    async function loadRecords() {
      try {
        setLoading(true);
        const res = await institutionalRecordsService.listRecords();
        if (res.success && res.data) {
          setRecords(res.data);
        }
      } catch (err) {
        console.error("Failed to load institutional records:", err);
      } finally {
        setLoading(false);
      }
    }

    loadRecords();
  }, []);

  const filteredRecords = records.filter((rec) => {
    if (categoryFilter !== "ALL" && rec.category !== categoryFilter) return false;
    if (confidentialityFilter !== "ALL" && rec.confidentiality !== confidentialityFilter)
      return false;
    if (statusFilter !== "ALL" && rec.status !== statusFilter) return false;

    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        rec.recordName.toLowerCase().includes(q) ||
        rec.code.toLowerCase().includes(q) ||
        rec.ownerDepartment.toLowerCase().includes(q) ||
        (rec.referenceNumber && rec.referenceNumber.toLowerCase().includes(q))
      );
    }
    return true;
  });

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-emerald-400 mb-1">
            <Building className="w-3.5 h-3.5" />
            <span>Institutional Governance Repository</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-100">
            Institutional Records & Gazettes
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Official statutory approvals, NBA/NAAC accreditations, institutional policies, and council minutes.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            size="sm"
            className="text-xs gap-1.5 bg-blue-600 hover:bg-blue-700"
            onClick={() => alert("Add Institutional Record Dialog")}
          >
            <Plus className="w-4 h-4" />
            Gazette New Record
          </Button>
        </div>
      </div>

      {/* Filter Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 bg-slate-900 border border-slate-800 p-4 rounded-xl">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search record name, code, dept..."
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
            <option value="Accreditation Records">Accreditation Records</option>
            <option value="Regulatory Approvals">Regulatory Approvals</option>
            <option value="Policies & Governance">Policies & Governance</option>
            <option value="Administrative Records">Administrative Records</option>
          </Select>
        </div>

        <div>
          <Select
            value={confidentialityFilter}
            onChange={(e) => setConfidentialityFilter(e.target.value)}
            className="bg-slate-950 border-slate-800 text-xs"
          >
            <option value="ALL">All Confidentiality Tiers</option>
            {Object.values(ConfidentialityLevel).map((lvl) => (
              <option key={lvl} value={lvl}>
                {lvl}
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
            {Object.values(InstitutionalRecordStatus).map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </Select>
        </div>
      </div>

      {/* Directory Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        {loading ? (
          <div className="py-20 text-center text-xs text-slate-500">Loading institutional records...</div>
        ) : filteredRecords.length === 0 ? (
          <div className="py-16 text-center text-xs text-slate-500">
            No institutional records matched your filters.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-3.5 px-4">Record Name & Code</th>
                  <th className="py-3.5 px-4">Category</th>
                  <th className="py-3.5 px-4">Owner Department</th>
                  <th className="py-3.5 px-4">Created Date</th>
                  <th className="py-3.5 px-4">Valid Until</th>
                  <th className="py-3.5 px-4">Confidentiality</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80 text-slate-300">
                {filteredRecords.map((rec) => (
                  <tr key={rec.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3.5 px-4">
                      <Link
                        href={`/app/documents/institutional-records/${rec.id}`}
                        className="font-semibold text-slate-100 hover:text-blue-400 transition"
                      >
                        {rec.recordName}
                      </Link>
                      <div className="text-[11px] text-blue-400 font-mono mt-0.5">
                        {rec.code} {rec.referenceNumber && `• Ref: ${rec.referenceNumber}`}
                      </div>
                    </td>

                    <td className="py-3.5 px-4 font-medium text-slate-200">
                      {rec.category}
                    </td>

                    <td className="py-3.5 px-4 text-slate-400">
                      {rec.ownerDepartment}
                    </td>

                    <td className="py-3.5 px-4 text-slate-400">
                      {rec.createdDate}
                    </td>

                    <td className="py-3.5 px-4">
                      {rec.validUntil ? (
                        <span className="text-amber-400">{rec.validUntil}</span>
                      ) : (
                        <span className="text-slate-500">Standing / Permanent</span>
                      )}
                    </td>

                    <td className="py-3.5 px-4">
                      <ConfidentialityBadge level={rec.confidentiality} />
                    </td>

                    <td className="py-3.5 px-4">
                      <span className="inline-flex px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {rec.status}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <Link href={`/app/documents/institutional-records/${rec.id}`}>
                        <Button size="sm" variant="outline" className="text-xs h-7 gap-1">
                          <Eye className="w-3.5 h-3.5" />
                          View 360
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
