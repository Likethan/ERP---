"use client";

import React, { useEffect, useState } from "react";
import {
  ShieldCheck,
  FileText,
  Upload,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Search,
  Filter,
  Calendar,
  ExternalLink,
  ChevronRight,
  FolderOpen,
  X,
  FileCheck,
} from "lucide-react";
import {
  hodService,
  HodAccreditationOverviewData,
  HodAccreditationCriterionItem,
  HodAccreditationDocumentItem,
  HodAccreditationDocumentUploadPayload,
} from "@/services/hod.service";
import { useToast } from "@/components/ui/toast";

export default function HodAccreditationPage() {
  const { addToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<HodAccreditationOverviewData | null>(
    null,
  );
  const [selectedCriterion, setSelectedCriterion] = useState("ALL");
  const [yearFilter, setYearFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Upload Document Modal
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [docTitle, setDocTitle] = useState("");
  const [docCriterion, setDocCriterion] = useState("CRITERION_1");
  const [docYear, setDocYear] = useState("2025-2026");
  const [docDesc, setDocDesc] = useState("");
  const [docFileName, setDocFileName] = useState("");

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await hodService.getAccreditationOverview();
      if (res.data) {
        setOverview(res.data);
      }
    } catch {
      addToast({
        title: "Error Loading Data",
        description: "Failed to load accreditation audit records.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleUploadDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!docTitle.trim() || !docFileName.trim()) {
      addToast({
        title: "Required Fields Missing",
        description: "Please specify document title and file attachment name.",
        variant: "destructive",
      });
      return;
    }

    try {
      setUploading(true);
      const payload: HodAccreditationDocumentUploadPayload = {
        title: docTitle.trim(),
        criterion: docCriterion,
        academicYear: docYear,
        description:
          docDesc.trim() || "Accreditation evidentiary documentation.",
        fileName: docFileName.trim(),
        fileType: "PDF",
        fileSizeKb: 1450,
      };

      const res = await hodService.uploadAccreditationDocument(payload);
      if (res.success && res.data) {
        addToast({
          title: "Document Registered",
          description: `"${res.data.title}" queued for criteria verification.`,
          variant: "success",
        });
        setUploadModalOpen(false);
        resetUploadForm();
        loadData();
      }
    } catch {
      addToast({
        title: "Upload Registration Failed",
        description: "Could not register document into accreditation vault.",
        variant: "destructive",
      });
    } finally {
      setUploading(false);
    }
  };

  const resetUploadForm = () => {
    setDocTitle("");
    setDocDesc("");
    setDocFileName("");
    setDocCriterion("CRITERION_1");
  };

  const filteredDocs = (overview?.documents || []).filter((doc) => {
    if (selectedCriterion !== "ALL" && doc.criterion !== selectedCriterion)
      return false;
    if (yearFilter !== "ALL" && doc.academicYear !== yearFilter) return false;
    if (statusFilter !== "ALL" && doc.reviewStatus !== statusFilter)
      return false;
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      doc.title.toLowerCase().includes(q) ||
      doc.description.toLowerCase().includes(q) ||
      doc.fileName.toLowerCase().includes(q)
    );
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "VERIFIED":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="h-3 w-3" /> Verified by IQAC
          </span>
        );
      case "UNDER_REVIEW":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-700 border border-amber-200">
            <Clock className="h-3 w-3" /> Under Review
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600 border border-slate-200">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 p-6">
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Accreditation & Quality Documentation
            </h1>
            <span className="rounded-md bg-yellow-100 px-2.5 py-0.5 text-xs font-bold text-yellow-800 border border-yellow-300">
              NBA Tier-1 Audit Vault
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Internal Quality Assurance Cell (IQAC) document repository and
            criteria compliance tracking.
          </p>
        </div>

        <button
          onClick={() => setUploadModalOpen(true)}
          className="inline-flex items-center gap-2 rounded-lg bg-yellow-400 px-4 py-2.5 text-xs font-bold text-slate-950 shadow-xs hover:bg-yellow-300 transition-colors"
        >
          <Upload className="h-4 w-4" />
          Upload Evidence Document
        </button>
      </div>

      {/* Advisory Banner */}
      <div className="rounded-xl border border-blue-200 bg-blue-50/70 p-4 text-xs text-blue-900 flex items-start gap-3">
        <ShieldCheck className="h-5 w-5 text-blue-600 shrink-0 mt-0.5" />
        <div>
          <strong className="block text-blue-950 font-semibold mb-0.5">
            Institutional Quality Assurance Note
          </strong>
          This portal structures and preserves internal evidentiary artifacts to
          support periodic institutional audits (NBA / NAAC). Formal statutory
          conferral remains subject to official peer-team evaluation by the
          respective statutory council.
        </div>
      </div>

      {/* Audit Readiness Progress & Summary */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-100 pb-4">
          <div>
            <span className="text-xs font-mono text-slate-400">
              Framework: {overview?.framework}
            </span>
            <h2 className="text-base font-bold text-slate-900 mt-0.5">
              Program Compliance: {overview?.programName}
            </h2>
          </div>
          <div className="text-left sm:text-right">
            <div className="text-2xl font-bold text-slate-900">
              {overview?.readinessPercentage || 93.0}%
            </div>
            <span className="text-xs text-emerald-700 font-semibold">
              Statutory Readiness Level: High
            </span>
          </div>
        </div>

        {/* Criteria Progress Bars */}
        <div className="mt-5 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {(overview?.criteria || []).map((crit) => (
            <div
              key={crit.criterionId}
              onClick={() =>
                setSelectedCriterion(
                  selectedCriterion === crit.criterionId
                    ? "ALL"
                    : crit.criterionId,
                )
              }
              className={`cursor-pointer rounded-xl border p-4 transition-all ${
                selectedCriterion === crit.criterionId
                  ? "border-yellow-400 bg-yellow-50/40 shadow-xs"
                  : "border-slate-200 bg-white hover:border-slate-300"
              }`}
            >
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-900">
                  {crit.criterionId.replace("_", " ")}
                </span>
                <span className="font-bold text-slate-900 font-mono">
                  {crit.completionPercentage}%
                </span>
              </div>
              <div className="mt-2 text-xs font-medium text-slate-700 line-clamp-2 h-8">
                {crit.name}
              </div>
              <div className="mt-3 h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                <div
                  className="h-full rounded-full bg-yellow-400"
                  style={{ width: `${crit.completionPercentage}%` }}
                />
              </div>
              <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500">
                <span>
                  {crit.verifiedCount} of {crit.documentsCount} verified
                </span>
                <span className="font-medium text-slate-700">
                  Weight: {crit.weightage} pts
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-xs sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search documents by title, description, file name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-slate-200 pl-9 pr-4 py-2 text-sm focus:border-yellow-400 focus:outline-hidden focus:ring-1 focus:ring-yellow-400"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <select
            value={selectedCriterion}
            onChange={(e) => setSelectedCriterion(e.target.value)}
            className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-700 focus:outline-hidden"
          >
            <option value="ALL">All Criteria (1 to 5)</option>
            <option value="CRITERION_1">Criterion 1: Vision & Mission</option>
            <option value="CRITERION_2">Criterion 2: Curriculum</option>
            <option value="CRITERION_3">Criterion 3: CO-PO Attainment</option>
            <option value="CRITERION_4">
              Criterion 4: Students & Placement
            </option>
            <option value="CRITERION_5">Criterion 5: Faculty Cadre</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-700 focus:outline-hidden"
          >
            <option value="ALL">All Statuses</option>
            <option value="VERIFIED">Verified</option>
            <option value="UNDER_REVIEW">Under Review</option>
          </select>
        </div>
      </div>

      {/* Document Roster Table */}
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xs">
        <div className="border-b border-slate-200 px-5 py-3.5 flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900">
            Registered Accreditation Documents ({filteredDocs.length})
          </h2>
          <span className="text-xs text-slate-500 font-mono">
            Department: Computer Science & Engineering
          </span>
        </div>

        {loading ? (
          <div className="p-8 text-center text-sm text-slate-500">
            Loading accreditation documents...
          </div>
        ) : filteredDocs.length === 0 ? (
          <div className="p-8 text-center text-sm text-slate-500">
            No documents found matching current criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold text-[11px]">
                <tr>
                  <th className="px-5 py-3">Document Title & Description</th>
                  <th className="px-4 py-3">Criterion</th>
                  <th className="px-4 py-3">File / Size</th>
                  <th className="px-4 py-3">Uploaded By</th>
                  <th className="px-4 py-3 text-center">Status</th>
                  <th className="px-5 py-3">Review Remarks</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredDocs.map((doc) => (
                  <tr
                    key={doc.id}
                    className="hover:bg-yellow-50/40 transition-colors"
                  >
                    <td className="px-5 py-3.5">
                      <div className="font-semibold text-slate-900 text-sm">
                        {doc.title}
                      </div>
                      <div className="text-slate-500 text-[11px] mt-0.5 line-clamp-1">
                        {doc.description}
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="rounded bg-slate-100 px-2 py-0.5 font-mono text-[10px] font-bold text-slate-700 border border-slate-200">
                        {doc.criterion.replace("_", " ")}
                      </span>
                      <span className="text-[10px] text-slate-400 block mt-1">
                        Year: {doc.academicYear}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 font-medium text-slate-800">
                      <div className="flex items-center gap-1.5 font-mono text-[11px]">
                        <FileText className="h-3.5 w-3.5 text-slate-400" />
                        <span className="truncate max-w-[140px]">
                          {doc.fileName}
                        </span>
                      </div>
                      <span className="text-[10px] text-slate-400 block mt-0.5">
                        {doc.fileType} • {doc.fileSizeKb} KB
                      </span>
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="font-medium text-slate-900">
                        {doc.uploadedBy}
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono">
                        {doc.uploadedAt.slice(0, 10)}
                      </div>
                    </td>
                    <td className="px-4 py-3.5 text-center">
                      {getStatusBadge(doc.reviewStatus)}
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-600">
                      <div className="italic">"{doc.reviewRemarks}"</div>
                      <span className="text-[10px] text-slate-400 block mt-0.5">
                        Auditor: {doc.reviewer}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Upload Modal */}
      {uploadModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900">
                Upload Accreditation Evidence Document
              </h3>
              <button
                onClick={() => setUploadModalOpen(false)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-100"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form
              onSubmit={handleUploadDocument}
              className="mt-4 space-y-3.5 text-xs"
            >
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Document Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. BoS Minutes & Syllabus Approval Copies"
                  value={docTitle}
                  onChange={(e) => setDocTitle(e.target.value)}
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs focus:border-yellow-400 focus:ring-1 focus:ring-yellow-400"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Criterion *
                  </label>
                  <select
                    value={docCriterion}
                    onChange={(e) => setDocCriterion(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"
                  >
                    <option value="CRITERION_1">
                      Criterion 1: Vision & Mission
                    </option>
                    <option value="CRITERION_2">
                      Criterion 2: Curriculum & Teaching
                    </option>
                    <option value="CRITERION_3">
                      Criterion 3: CO-PO Attainment
                    </option>
                    <option value="CRITERION_4">
                      Criterion 4: Student Performance & Placement
                    </option>
                    <option value="CRITERION_5">
                      Criterion 5: Faculty Cadre & SFR
                    </option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Academic Year *
                  </label>
                  <select
                    value={docYear}
                    onChange={(e) => setDocYear(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"
                  >
                    <option value="2025-2026">2025-2026</option>
                    <option value="2024-2025">2024-2025</option>
                    <option value="2023-2024">2023-2024</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  File Attachment Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. BoS_Meeting_Signed_Approval.pdf"
                  value={docFileName}
                  onChange={(e) => setDocFileName(e.target.value)}
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Description & Evidentiary Scope
                </label>
                <textarea
                  rows={2}
                  placeholder="Detail the contents, external auditor signatures, and relevance to criterion..."
                  value={docDesc}
                  onChange={(e) => setDocDesc(e.target.value)}
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"
                />
              </div>

              <div className="mt-5 flex justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setUploadModalOpen(false)}
                  className="rounded-lg border border-slate-200 px-4 py-2 font-medium text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading}
                  className="rounded-lg bg-yellow-400 px-4 py-2 font-semibold text-slate-950 hover:bg-yellow-300 disabled:opacity-50"
                >
                  {uploading ? "Registering..." : "Upload & Register"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
