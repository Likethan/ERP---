"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  certificateRequestsService,
  certificateTemplatesService,
} from "@/services";
import {
  CertificateRequest,
  CertificateRequestStatus,
  CertificateType,
  CertificateTemplate,
} from "@campusos/types";
import { CertificateRequestStatusBadge } from "@/components/documents/document-status-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Dialog } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import {
  Award,
  Search,
  Plus,
  ArrowLeft,
  Clock,
  CheckCircle2,
  XCircle,
  Eye,
  Filter,
} from "lucide-react";

export default function CertificateRequestsPage() {
  const [requests, setRequests] = useState<CertificateRequest[]>([]);
  const [templates, setTemplates] = useState<CertificateTemplate[]>([]);
  const [loading, setLoading] = useState(true);

  // Filter States
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [typeFilter, setTypeFilter] = useState("ALL");

  // New Request Modal State
  const [newRequestOpen, setNewRequestOpen] = useState(false);
  const [selectedTemplateId, setSelectedTemplateId] = useState("");
  const [requestPurpose, setRequestPurpose] = useState("");
  const [requiredByDate, setRequiredByDate] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    async function loadRequests() {
      try {
        setLoading(true);
        const [reqsRes, tmplsRes] = await Promise.all([
          certificateRequestsService.listRequests(),
          certificateTemplatesService.listTemplates(),
        ]);

        if (reqsRes.success && reqsRes.data) setRequests(reqsRes.data);
        if (tmplsRes.success && tmplsRes.data) {
          setTemplates(tmplsRes.data);
          if (tmplsRes.data.length > 0) {
            setSelectedTemplateId(tmplsRes.data[0].id);
          }
        }
      } catch (err) {
        console.error("Failed to load requests:", err);
      } finally {
        setLoading(false);
      }
    }

    loadRequests();
  }, []);

  const handleCreateRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!requestPurpose.trim()) {
      alert("Purpose of certificate request is mandatory.");
      return;
    }

    try {
      setCreating(true);
      const selectedTmpl = templates.find((t) => t.id === selectedTemplateId);
      const res = await certificateRequestsService.createRequest({
        studentId: "stu-001",
        studentName: "Aarav Patel",
        rollNumber: "24CSE0101",
        program: "B.Tech Computer Science & Engineering",
        department: "Computer Science & Engineering",
        templateId: selectedTemplateId,
        templateName:
          selectedTmpl?.templateName || "Institutional Bonafide Certificate",
        certificateType:
          selectedTmpl?.certificateType || CertificateType.BONAFIDE,
        purpose: requestPurpose,
        requiredByDate: requiredByDate || undefined,
      });

      if (res.success && res.data) {
        setRequests((prev) => [res.data!, ...prev]);
        setNewRequestOpen(false);
        setRequestPurpose("");
        alert(
          `Certificate Request ${res.data.requestId} submitted successfully!`,
        );
      }
    } catch (err) {
      console.error(err);
    } finally {
      setCreating(false);
    }
  };

  const filteredRequests = requests.filter((req) => {
    if (statusFilter !== "ALL" && req.status !== statusFilter) return false;
    if (typeFilter !== "ALL" && req.certificateType !== typeFilter)
      return false;

    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        req.requestId.toLowerCase().includes(q) ||
        req.studentName.toLowerCase().includes(q) ||
        req.rollNumber.toLowerCase().includes(q) ||
        req.templateName.toLowerCase().includes(q) ||
        req.purpose.toLowerCase().includes(q)
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
            <Link
              href="/app/documents/certificates"
              className="hover:underline flex items-center gap-1"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Certificate Center
            </Link>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-100">
            Certificate Requests Pipeline
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            End-to-end issuance workflow: Submission → Academic Validation →
            Review → Approval → Digital Issuance.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            size="sm"
            onClick={() => setNewRequestOpen(true)}
            className="text-xs gap-1.5 bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="w-4 h-4" />
            Submit Certificate Request
          </Button>
        </div>
      </div>

      {/* Filter Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 bg-slate-900 border border-slate-800 p-4 rounded-xl">
        <div className="sm:col-span-2 relative">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search request ID, student name, roll no..."
            className="pl-9 bg-slate-950 border-slate-800 text-xs"
          />
        </div>

        <div>
          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-950 border-slate-800 text-xs"
          >
            <option value="ALL">All Statuses ({requests.length})</option>
            {Object.values(CertificateRequestStatus).map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <Select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-slate-950 border-slate-800 text-xs"
          >
            <option value="ALL">All Certificate Types</option>
            {Object.values(CertificateType).map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </Select>
        </div>
      </div>

      {/* Pipeline Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        {loading ? (
          <div className="py-20 text-center text-xs text-slate-500">
            Loading request pipeline...
          </div>
        ) : filteredRequests.length === 0 ? (
          <div className="py-16 text-center text-xs text-slate-500">
            No certificate requests matched your search.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                  <th className="py-3.5 px-4">Request ID</th>
                  <th className="py-3.5 px-4">Student</th>
                  <th className="py-3.5 px-4">Certificate</th>
                  <th className="py-3.5 px-4">Requested Date</th>
                  <th className="py-3.5 px-4">Required By</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Reviewer</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80 text-slate-300">
                {filteredRequests.map((req) => (
                  <tr key={req.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3.5 px-4 font-mono font-semibold text-blue-400">
                      <Link
                        href={`/app/documents/certificates/requests/${req.id}`}
                        className="hover:underline"
                      >
                        {req.requestId}
                      </Link>
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-slate-200">
                        {req.studentName}
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono">
                        {req.rollNumber}
                      </div>
                    </td>

                    <td className="py-3.5 px-4">
                      <span className="font-medium text-slate-200">
                        {req.templateName}
                      </span>
                      <div className="text-[11px] text-amber-400/80 font-mono mt-0.5">
                        {req.certificateType}
                      </div>
                    </td>

                    <td className="py-3.5 px-4 text-slate-400">
                      {new Date(req.requestedDate).toLocaleDateString()}
                    </td>

                    <td className="py-3.5 px-4 text-slate-400">
                      {req.requiredByDate ? (
                        <span className="text-amber-400">
                          {req.requiredByDate}
                        </span>
                      ) : (
                        <span className="text-slate-500">Standard</span>
                      )}
                    </td>

                    <td className="py-3.5 px-4">
                      <CertificateRequestStatusBadge status={req.status} />
                    </td>

                    <td className="py-3.5 px-4 text-slate-400">
                      {req.reviewerName || "Unassigned"}
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <Link
                        href={`/app/documents/certificates/requests/${req.id}`}
                      >
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-xs h-7 gap-1"
                        >
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

      {/* NEW REQUEST MODAL */}
      <Dialog
        isOpen={newRequestOpen}
        onClose={() => setNewRequestOpen(false)}
        title="Submit Certificate Request"
      >
        <form onSubmit={handleCreateRequest} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-400 font-medium mb-1">
              Select Certificate Template{" "}
              <span className="text-rose-400">*</span>
            </label>
            <Select
              value={selectedTemplateId}
              onChange={(e) => setSelectedTemplateId(e.target.value)}
              className="bg-slate-950 border-slate-800 text-xs"
            >
              {templates.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.templateName} ({t.certificateType})
                </option>
              ))}
            </Select>
          </div>

          <div>
            <label className="block text-slate-400 font-medium mb-1">
              Purpose of Request <span className="text-rose-400">*</span>
            </label>
            <Textarea
              rows={3}
              value={requestPurpose}
              onChange={(e) => setRequestPurpose(e.target.value)}
              placeholder="e.g. Applying for Bank Education Loan Renewal at State Bank of India"
              className="bg-slate-950 border-slate-800 text-xs"
            />
          </div>

          <div>
            <label className="block text-slate-400 font-medium mb-1">
              Required By Date
            </label>
            <Input
              type="date"
              value={requiredByDate}
              onChange={(e) => setRequiredByDate(e.target.value)}
              className="bg-slate-950 border-slate-800 text-xs"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setNewRequestOpen(false)}
              className="text-xs"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={creating}
              className="text-xs bg-blue-600 hover:bg-blue-700"
            >
              {creating ? "Submitting..." : "Submit Request"}
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
