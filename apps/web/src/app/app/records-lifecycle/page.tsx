"use client";

import React, { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type {
  RecordCategoryModel,
  RecordDispositionCertificateModel,
  RecordDispositionRequestModel,
  RecordLegalHoldModel,
  RecordLifecycleState,
  RecordRegistryEntryModel,
  RecordsLifecycleSummaryModel,
  RetentionEvaluationModel,
  RetentionPolicyModel,
} from "@campusos/types";

export default function RecordsLifecyclePage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<
    "overview" | "policies" | "registry" | "holds" | "disposition" | "archival"
  >("overview");

  // Summary KPIs
  const [summary, setSummary] = useState<RecordsLifecycleSummaryModel | null>(null);

  // Entities
  const [categories, setCategories] = useState<RecordCategoryModel[]>([]);
  const [policies, setPolicies] = useState<RetentionPolicyModel[]>([]);
  const [records, setRecords] = useState<RecordRegistryEntryModel[]>([]);
  const [holds, setHolds] = useState<RecordLegalHoldModel[]>([]);
  const [dispositions, setDispositions] = useState<RecordDispositionRequestModel[]>([]);

  // Selection & Details
  const [selectedRecord, setSelectedRecord] = useState<RecordRegistryEntryModel | null>(null);
  const [evaluation, setEvaluation] = useState<RetentionEvaluationModel | null>(null);

  // New Policy Form
  const [newPolCode, setNewPolCode] = useState("");
  const [newPolName, setNewPolName] = useState("");
  const [newPolCategory, setNewPolCategory] = useState("STUDENT_ACADEMIC");
  const [newPolDuration, setNewPolDuration] = useState(5);
  const [newPolUnit, setNewPolUnit] = useState<"DAYS" | "MONTHS" | "YEARS" | "PERMANENT">("YEARS");
  const [newPolTrigger, setNewPolTrigger] = useState<"CREATION" | "GRADUATION" | "TERMINATION" | "FY_CLOSE">("GRADUATION");
  const [newPolMethod, setNewPolMethod] = useState<"SECURE_DELETE" | "ANONYMIZE" | "PERMANENT_ARCHIVE">("ANONYMIZE");

  // New Hold Form
  const [newHoldName, setNewHoldName] = useState("");
  const [newHoldReason, setNewHoldReason] = useState("");
  const [newHoldScope, setNewHoldScope] = useState<"ALL" | "CATEGORY" | "MODULE">("CATEGORY");
  const [newHoldScopeValue, setNewHoldScopeValue] = useState("STUDENT_ACADEMIC");

  // Disposition Preview / Request Form
  const [dispCategory, setDispCategory] = useState("STUDENT_ACADEMIC");
  const [dispJustification, setDispJustification] = useState("");
  const [previewResult, setPreviewResult] = useState<any | null>(null);

  // States
  const [loading, setLoading] = useState(true);
  const [actionNotice, setActionNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [summaryRes, catsRes, polsRes, recsRes, holdsRes, dispRes] = await Promise.all([
        apiFetch<RecordsLifecycleSummaryModel>("/api/v1/records/dashboard/summary").catch(() => ({ data: null })),
        apiFetch<RecordCategoryModel[]>("/api/v1/records/categories").catch(() => ({ data: [] })),
        apiFetch<RetentionPolicyModel[]>("/api/v1/records/policies").catch(() => ({ data: [] })),
        apiFetch<RecordRegistryEntryModel[]>("/api/v1/records/registry?limit=100").catch(() => ({ data: [] })),
        apiFetch<RecordLegalHoldModel[]>("/api/v1/records/holds").catch(() => ({ data: [] })),
        apiFetch<RecordDispositionRequestModel[]>("/api/v1/records/dispositions").catch(() => ({ data: [] })),
      ]);

      setSummary(summaryRes.data);
      setCategories(catsRes.data || []);
      setPolicies(polsRes.data || []);
      setRecords(recsRes.data || []);
      setHolds(holdsRes.data || []);
      setDispositions(dispRes.data || []);
    } catch (err: any) {
      setError(err?.message || "Failed to load records lifecycle system data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreatePolicy = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPolCode.trim() || !newPolName.trim()) {
      setError("Please provide a valid policy code and policy name.");
      return;
    }

    try {
      setError(null);
      await apiFetch("/api/v1/records/policies", {
        method: "POST",
        body: JSON.stringify({
          code: newPolCode.trim().toUpperCase(),
          name: newPolName.trim(),
          category_code: newPolCategory,
          scope: "CATEGORY",
          retention_duration: Number(newPolDuration),
          retention_unit: newPolUnit,
          trigger_event: newPolTrigger,
          review_required: true,
          archive_required: true,
          disposition_method: newPolMethod,
          approval_required: true,
        }),
      });

      setActionNotice(`Policy '${newPolCode}' authored successfully.`);
      setNewPolCode("");
      setNewPolName("");
      loadData();
    } catch (err: any) {
      setError(err?.message || "Failed to create retention policy.");
    }
  };

  const handlePublishPolicy = async (policyId: string) => {
    try {
      setError(null);
      await apiFetch(`/api/v1/records/policies/${policyId}/publish`, {
        method: "POST",
        body: JSON.stringify({
          change_summary: "Formally approved and published by Institutional Compliance Officer.",
        }),
      });
      setActionNotice("Retention policy successfully published and activated.");
      loadData();
    } catch (err: any) {
      setError(err?.message || "Failed to publish retention policy.");
    }
  };

  const handleCreateHold = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newHoldName.trim() || !newHoldReason.trim()) {
      setError("Please provide a hold name and legal preservation reason.");
      return;
    }

    try {
      setError(null);
      await apiFetch("/api/v1/records/holds", {
        method: "POST",
        body: JSON.stringify({
          name: newHoldName.trim(),
          reason: newHoldReason.trim(),
          scope_type: newHoldScope,
          scope_value: newHoldScope === "ALL" ? null : newHoldScopeValue,
        }),
      });

      setActionNotice(`Legal hold '${newHoldName}' issued. Matching records placed in immutable preservation.`);
      setNewHoldName("");
      setNewHoldReason("");
      loadData();
    } catch (err: any) {
      setError(err?.message || "Failed to create legal hold.");
    }
  };

  const handleReleaseHold = async (holdId: string) => {
    const reason = prompt("Enter legal release justification / court order clearance:");
    if (!reason) return;

    try {
      setError(null);
      await apiFetch(`/api/v1/records/holds/${holdId}/release`, {
        method: "POST",
        body: JSON.stringify({ release_reason: reason }),
      });
      setActionNotice("Legal hold released. Affected records submitted for fresh statutory eligibility re-evaluation.");
      loadData();
    } catch (err: any) {
      setError(err?.message || "Failed to release legal hold.");
    }
  };

  const handleRunDispositionPreview = async () => {
    try {
      setError(null);
      const res = await apiFetch<any>("/api/v1/records/dispositions/preview", {
        method: "POST",
        body: JSON.stringify({
          category_code: dispCategory,
          disposition_method: "ANONYMIZE",
        }),
      });
      setPreviewResult(res.data);
      setActionNotice("Dry-run preview completed. Zero records modified.");
    } catch (err: any) {
      setError(err?.message || "Failed to evaluate disposition preview.");
    }
  };

  const handleRequestDisposition = async () => {
    if (!dispJustification.trim()) {
      setError("Please specify formal disposition justification.");
      return;
    }

    try {
      setError(null);
      await apiFetch("/api/v1/records/dispositions", {
        method: "POST",
        body: JSON.stringify({
          category_code: dispCategory,
          requested_disposition_method: "ANONYMIZE",
          justification: dispJustification,
        }),
      });
      setActionNotice("Disposition batch request queued for two-person administrative approval.");
      setDispJustification("");
      setPreviewResult(null);
      loadData();
    } catch (err: any) {
      setError(err?.message || "Failed to request disposition.");
    }
  };

  const handleApproveDisposition = async (requestId: string) => {
    try {
      setError(null);
      await apiFetch(`/api/v1/records/dispositions/${requestId}/approve`, {
        method: "POST",
        body: JSON.stringify({ approval_notes: "Institutional records governance compliance verified." }),
      });
      setActionNotice("Disposition request approved by second authorized officer.");
      loadData();
    } catch (err: any) {
      setError(err?.message || "Failed to approve disposition request.");
    }
  };

  const handleExecuteDisposition = async (requestId: string) => {
    try {
      setError(null);
      const certRes = await apiFetch<RecordDispositionCertificateModel>(
        `/api/v1/records/dispositions/${requestId}/execute`,
        { method: "POST" }
      );
      setActionNotice(
        `Disposition executed. Certificate issued: ${certRes.data?.certificate_number} (Hash: ${certRes.data?.manifest_hash_sha256?.substring(0, 16)}...)`
      );
      loadData();
    } catch (err: any) {
      setError(err?.message || "Failed to execute disposition.");
    }
  };

  const handleEvaluateRecord = async (record: RecordRegistryEntryModel) => {
    setSelectedRecord(record);
    try {
      const res = await apiFetch<RetentionEvaluationModel>(
        `/api/v1/records/registry/${record.id}/retention-evaluation`
      );
      setEvaluation(res.data);
    } catch (err: any) {
      setError(err?.message || "Failed to evaluate record retention status.");
    }
  };

  const handleTriggerSweep = async () => {
    try {
      setError(null);
      await apiFetch("/api/v1/records/scheduler/sweep", {
        method: "POST",
        body: JSON.stringify({ run_type: "ELIGIBILITY_RECALCULATION" }),
      });
      setActionNotice("Scheduled lifecycle batch recalculation triggered successfully.");
      loadData();
    } catch (err: any) {
      setError(err?.message || "Failed to trigger batch sweep.");
    }
  };

  const getStateBadgeClass = (state: RecordLifecycleState) => {
    switch (state) {
      case "ACTIVE":
      case "RETENTION_IN_PROGRESS":
        return "bg-emerald-100 text-emerald-800 border-emerald-300";
      case "LEGAL_HOLD":
        return "bg-rose-100 text-rose-800 border-rose-300";
      case "REVIEW_REQUIRED":
      case "REVIEW_BLOCKED":
        return "bg-amber-100 text-amber-800 border-amber-300";
      case "ARCHIVED":
        return "bg-blue-100 text-blue-800 border-blue-300";
      case "DISPOSITION_ELIGIBLE":
      case "DISPOSITION_PENDING_APPROVAL":
        return "bg-purple-100 text-purple-800 border-purple-300";
      case "DISPOSITION_COMPLETED":
        return "bg-zinc-100 text-zinc-800 border-zinc-300";
      default:
        return "bg-slate-100 text-slate-800 border-slate-300";
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Enterprise Records Lifecycle & Archival Engine
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Statutory retention governance, immutable archival manifests, legal hold preservation, and audited disposition.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleTriggerSweep}
            className="px-4 py-2 bg-indigo-50 border border-indigo-200 text-indigo-700 text-sm font-medium rounded-lg hover:bg-indigo-100 transition-colors shadow-sm"
          >
            Trigger Lifecycle Sweep
          </button>
          <button
            onClick={loadData}
            className="px-4 py-2 bg-slate-100 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-200 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Notifications */}
      {actionNotice && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm rounded-lg flex items-center justify-between">
          <span>{actionNotice}</span>
          <button onClick={() => setActionNotice(null)} className="text-emerald-600 font-bold ml-4">✕</button>
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 text-sm rounded-lg flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-rose-600 font-bold ml-4">✕</button>
        </div>
      )}

      {/* Summary KPI Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Records</span>
            <p className="text-2xl font-bold text-slate-900 mt-1">{summary.total_records_registered}</p>
          </div>
          <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">In Retention</span>
            <p className="text-2xl font-bold text-emerald-600 mt-1">{summary.active_retention_records}</p>
          </div>
          <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Legal Holds</span>
            <p className="text-2xl font-bold text-rose-600 mt-1">{summary.legal_held_records}</p>
          </div>
          <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Archived Cold</span>
            <p className="text-2xl font-bold text-blue-600 mt-1">{summary.archived_records}</p>
          </div>
          <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Disposition Eligible</span>
            <p className="text-2xl font-bold text-purple-600 mt-1">{summary.disposition_eligible_records}</p>
          </div>
          <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Review Queued</span>
            <p className="text-2xl font-bold text-amber-600 mt-1">{summary.review_required_records}</p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-slate-200 flex gap-6">
        <button
          onClick={() => setActiveTab("overview")}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "overview"
              ? "border-indigo-600 text-indigo-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Lifecycle Overview
        </button>
        <button
          onClick={() => setActiveTab("registry")}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "registry"
              ? "border-indigo-600 text-indigo-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Records Registry ({records.length})
        </button>
        <button
          onClick={() => setActiveTab("policies")}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "policies"
              ? "border-indigo-600 text-indigo-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Retention Schedules ({policies.length})
        </button>
        <button
          onClick={() => setActiveTab("holds")}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "holds"
              ? "border-indigo-600 text-indigo-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Legal Holds ({holds.length})
        </button>
        <button
          onClick={() => setActiveTab("disposition")}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "disposition"
              ? "border-indigo-600 text-indigo-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Disposition Approvals ({dispositions.length})
        </button>
      </div>

      {/* Tab 1: Overview & Categories */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs">
            <h2 className="text-base font-semibold text-slate-900 mb-2">Statutory Classification Authorities</h2>
            <p className="text-sm text-slate-500 mb-4">
              9 statutory institutional record categories configured per UGC, AICTE, and State Higher Education directives.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {categories.map((cat) => (
                <div key={cat.id} className="p-4 border border-slate-100 rounded-lg bg-slate-50">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                      {cat.code}
                    </span>
                    <span className="text-xs text-slate-500 font-medium">{cat.confidentiality}</span>
                  </div>
                  <h3 className="text-sm font-medium text-slate-900 mt-2">{cat.name}</h3>
                  <p className="text-xs text-slate-500 mt-1 line-clamp-2">{cat.description}</p>
                  <div className="mt-3 text-xs text-slate-600 font-medium">
                    Default Retention: <span className="text-slate-900 font-semibold">{cat.default_retention_years} yrs</span>
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5">{cat.statutory_authority}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Records Registry */}
      {activeTab === "registry" && (
        <div className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
            <div className="p-4 border-b border-slate-200 flex justify-between items-center">
              <div>
                <h2 className="text-base font-semibold text-slate-900">Registered Institutional Records</h2>
                <p className="text-xs text-slate-500">Zero sensitive contents duplicated. Authoritative domain pointers only.</p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-600">
                <thead className="bg-slate-50 text-xs uppercase text-slate-400 font-medium border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-3">Record Number</th>
                    <th className="px-4 py-3">Title & Source</th>
                    <th className="px-4 py-3">Category</th>
                    <th className="px-4 py-3">Lifecycle State</th>
                    <th className="px-4 py-3">Eligibility Date</th>
                    <th className="px-4 py-3">Hold Status</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {records.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-4 py-8 text-center text-slate-400">
                        No institutional records registered yet.
                      </td>
                    </tr>
                  ) : (
                    records.map((rec) => (
                      <tr key={rec.id} className="hover:bg-slate-50/70 transition-colors">
                        <td className="px-4 py-3 font-mono text-xs font-semibold text-slate-900">
                          {rec.record_number}
                        </td>
                        <td className="px-4 py-3">
                          <div className="font-medium text-slate-900">{rec.title}</div>
                          <div className="text-xs text-slate-400">
                            {rec.source_module} • {rec.source_reference || "No Ref"}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-xs font-mono text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
                            {rec.category_code}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`text-xs px-2.5 py-1 rounded-full border font-medium ${getStateBadgeClass(
                              rec.lifecycle_state
                            )}`}
                          >
                            {rec.lifecycle_state}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-xs">
                          {rec.calculated_eligibility_date
                            ? new Date(rec.calculated_eligibility_date).toLocaleDateString()
                            : "—"}
                        </td>
                        <td className="px-4 py-3 text-xs">
                          {rec.is_held ? (
                            <span className="text-xs font-bold text-rose-600 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
                              LOCKED ({rec.active_hold_count})
                            </span>
                          ) : (
                            <span className="text-xs text-slate-400">Clear</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => handleEvaluateRecord(rec)}
                            className="px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium rounded transition-colors"
                          >
                            Audit Status
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Record Evaluation Inspector */}
          {selectedRecord && evaluation && (
            <div className="p-6 bg-slate-50 border border-slate-200 rounded-xl space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-bold text-slate-900">
                  Compliance Audit: {selectedRecord.record_number} — {selectedRecord.title}
                </h3>
                <button onClick={() => setSelectedRecord(null)} className="text-xs text-slate-400 hover:text-slate-600">
                  Close
                </button>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                <div>
                  <span className="text-slate-400 block">Current State</span>
                  <span className="font-semibold text-slate-800">{evaluation.current_state}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Recommended State</span>
                  <span className="font-semibold text-indigo-700">{evaluation.recommended_state}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Preservation Hold</span>
                  <span className={evaluation.is_held ? "font-bold text-rose-600" : "font-medium text-slate-700"}>
                    {evaluation.is_held ? "ACTIVE HOLD" : "No Hold"}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block">Active Dependencies</span>
                  <span className={evaluation.has_dependency_block ? "font-bold text-amber-600" : "text-slate-700"}>
                    {evaluation.has_dependency_block ? "BLOCKED" : "Clear"}
                  </span>
                </div>
              </div>
              <div className="p-3 bg-white border border-slate-200 rounded-lg text-xs font-mono text-slate-700">
                {evaluation.evaluation_summary}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Retention Policies */}
      {activeTab === "policies" && (
        <div className="space-y-6">
          {/* Policy Creation Form */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs">
            <h2 className="text-base font-semibold text-slate-900 mb-4">Author Retention Policy Schedule</h2>
            <form onSubmit={handleCreatePolicy} className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Policy Code</label>
                <input
                  type="text"
                  value={newPolCode}
                  onChange={(e) => setNewPolCode(e.target.value)}
                  placeholder="e.g. POL_STUDENT_TRANSCRIPTS"
                  className="w-full text-xs p-2 border border-slate-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Policy Name</label>
                <input
                  type="text"
                  value={newPolName}
                  onChange={(e) => setNewPolName(e.target.value)}
                  placeholder="e.g. Academic Transcripts 35-Year UGC Schedule"
                  className="w-full text-xs p-2 border border-slate-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Record Category</label>
                <select
                  value={newPolCategory}
                  onChange={(e) => setNewPolCategory(e.target.value)}
                  className="w-full text-xs p-2 border border-slate-300 rounded-md"
                >
                  {categories.map((c) => (
                    <option key={c.id} value={c.code}>
                      {c.name} ({c.code})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Duration & Unit</label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    value={newPolDuration}
                    onChange={(e) => setNewPolDuration(Number(e.target.value))}
                    min={1}
                    className="w-20 text-xs p-2 border border-slate-300 rounded-md"
                  />
                  <select
                    value={newPolUnit}
                    onChange={(e: any) => setNewPolUnit(e.target.value)}
                    className="flex-1 text-xs p-2 border border-slate-300 rounded-md"
                  >
                    <option value="YEARS">YEARS</option>
                    <option value="MONTHS">MONTHS</option>
                    <option value="DAYS">DAYS</option>
                    <option value="PERMANENT">PERMANENT</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Trigger Event</label>
                <select
                  value={newPolTrigger}
                  onChange={(e: any) => setNewPolTrigger(e.target.value)}
                  className="w-full text-xs p-2 border border-slate-300 rounded-md"
                >
                  <option value="GRADUATION">GRADUATION</option>
                  <option value="CREATION">CREATION</option>
                  <option value="TERMINATION">TERMINATION</option>
                  <option value="FY_CLOSE">FY_CLOSE</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Disposition Method</label>
                <select
                  value={newPolMethod}
                  onChange={(e: any) => setNewPolMethod(e.target.value)}
                  className="w-full text-xs p-2 border border-slate-300 rounded-md"
                >
                  <option value="ANONYMIZE">ANONYMIZE</option>
                  <option value="SECURE_DELETE">SECURE_DELETE</option>
                  <option value="PERMANENT_ARCHIVE">PERMANENT_ARCHIVE</option>
                </select>
              </div>
              <div className="md:col-span-2 flex items-end">
                <button
                  type="submit"
                  className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium rounded-md shadow-sm transition-colors"
                >
                  Create Policy Draft
                </button>
              </div>
            </form>
          </div>

          {/* Policy List */}
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
            <div className="p-4 border-b border-slate-200">
              <h2 className="text-base font-semibold text-slate-900">Institutional Retention Schedules</h2>
            </div>
            <div className="divide-y divide-slate-100">
              {policies.map((pol) => (
                <div key={pol.id} className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-bold text-slate-900">{pol.code}</span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded font-medium ${
                          pol.status === "PUBLISHED"
                            ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                            : "bg-amber-50 text-amber-700 border border-amber-200"
                        }`}
                      >
                        {pol.status} (v{pol.current_version})
                      </span>
                    </div>
                    <h3 className="text-sm font-medium text-slate-900 mt-1">{pol.name}</h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Category: {pol.category_code} • Duration: {pol.retention_duration} {pol.retention_unit} after{" "}
                      {pol.trigger_event} • Action: {pol.disposition_method}
                    </p>
                  </div>
                  <div>
                    {pol.status === "DRAFT" ? (
                      <button
                        onClick={() => handlePublishPolicy(pol.id)}
                        className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-medium rounded shadow-xs transition-colors"
                      >
                        Publish & Activate
                      </button>
                    ) : (
                      <span className="text-xs font-medium text-slate-400">Active Regulatory Baseline</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Legal Holds */}
      {activeTab === "holds" && (
        <div className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs">
            <h2 className="text-base font-semibold text-slate-900 mb-2">Issue Preservation Legal Hold</h2>
            <p className="text-xs text-slate-500 mb-4">
              Precedence rule: Active legal holds unconditionally block automated and manual record disposition.
            </p>
            <form onSubmit={handleCreateHold} className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Hold Title</label>
                <input
                  type="text"
                  value={newHoldName}
                  onChange={(e) => setNewHoldName(e.target.value)}
                  placeholder="e.g. Audit Inquiry 2026-HC"
                  className="w-full text-xs p-2 border border-slate-300 rounded-md"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-xs font-medium text-slate-700 mb-1">Legal Preservation Reason</label>
                <input
                  type="text"
                  value={newHoldReason}
                  onChange={(e) => setNewHoldReason(e.target.value)}
                  placeholder="Statutory investigation or litigation preservation mandate"
                  className="w-full text-xs p-2 border border-slate-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Scope</label>
                <select
                  value={newHoldScope}
                  onChange={(e: any) => setNewHoldScope(e.target.value)}
                  className="w-full text-xs p-2 border border-slate-300 rounded-md"
                >
                  <option value="CATEGORY">CATEGORY</option>
                  <option value="ALL">ALL INSTITUTION RECORDS</option>
                  <option value="MODULE">MODULE</option>
                </select>
              </div>
              <div className="md:col-span-4 flex justify-end">
                <button
                  type="submit"
                  className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-medium rounded-md shadow-xs transition-colors"
                >
                  Issue Legal Hold
                </button>
              </div>
            </form>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
            <div className="p-4 border-b border-slate-200">
              <h2 className="text-base font-semibold text-slate-900">Active & Historical Legal Holds</h2>
            </div>
            <div className="divide-y divide-slate-100">
              {holds.length === 0 ? (
                <div className="p-6 text-center text-xs text-slate-400">No active legal holds found.</div>
              ) : (
                holds.map((h) => (
                  <div key={h.id} className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-bold text-slate-900">{h.hold_number}</span>
                        <span
                          className={`text-xs px-2 py-0.5 rounded font-bold ${
                            h.status === "ACTIVE"
                              ? "bg-rose-50 text-rose-700 border border-rose-200"
                              : "bg-slate-100 text-slate-600"
                          }`}
                        >
                          {h.status}
                        </span>
                      </div>
                      <h3 className="text-sm font-medium text-slate-900 mt-1">{h.name}</h3>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Scope: {h.scope_type} ({h.scope_value || "Global"}) • Reason: {h.reason}
                      </p>
                      <div className="text-xs text-slate-400 mt-1">
                        Effective: {new Date(h.effective_from).toLocaleDateString()} • Locked Records: {h.records_count}
                      </div>
                    </div>
                    <div>
                      {h.status === "ACTIVE" && (
                        <button
                          onClick={() => handleReleaseHold(h.id)}
                          className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium rounded transition-colors"
                        >
                          Release Hold
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab 5: Disposition Approvals & Certificates */}
      {activeTab === "disposition" && (
        <div className="space-y-6">
          {/* Dry Run Preview & Request Box */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
            <h2 className="text-base font-semibold text-slate-900">Disposition Review & Approval Queue</h2>
            <p className="text-xs text-slate-500">
              Requires dry-run preview and independent dual-person approval (requester cannot approve own batch).
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Target Category</label>
                <select
                  value={dispCategory}
                  onChange={(e) => setDispCategory(e.target.value)}
                  className="w-full text-xs p-2 border border-slate-300 rounded-md"
                >
                  {categories.map((c) => (
                    <option key={c.id} value={c.code}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="block text-xs font-medium text-slate-700 mb-1">Formal Justification</label>
                <input
                  type="text"
                  value={dispJustification}
                  onChange={(e) => setDispJustification(e.target.value)}
                  placeholder="e.g. UGC 35-year expiration maturity reached. Academic Senate resolution 44."
                  className="w-full text-xs p-2 border border-slate-300 rounded-md"
                />
              </div>
            </div>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={handleRunDispositionPreview}
                className="px-4 py-2 bg-indigo-50 border border-indigo-200 text-indigo-700 text-xs font-medium rounded-md hover:bg-indigo-100 transition-colors"
              >
                Run Dry-Run Preview
              </button>
              <button
                type="button"
                onClick={handleRequestDisposition}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium rounded-md shadow-xs transition-colors"
              >
                Submit Disposition Batch Request
              </button>
            </div>

            {previewResult && (
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-2">
                <span className="font-bold text-slate-800">Preview Results:</span>
                <div className="grid grid-cols-3 gap-2 text-slate-600">
                  <div>Evaluated: <span className="font-bold">{previewResult.records_evaluated}</span></div>
                  <div>Eligible: <span className="font-bold text-emerald-600">{previewResult.records_eligible}</span></div>
                  <div>Blocked by Holds: <span className="font-bold text-rose-600">{previewResult.records_blocked_by_holds}</span></div>
                </div>
              </div>
            )}
          </div>

          {/* Disposition Request List */}
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
            <div className="p-4 border-b border-slate-200">
              <h2 className="text-base font-semibold text-slate-900">Governance Requests & Certificates</h2>
            </div>
            <div className="divide-y divide-slate-100">
              {dispositions.length === 0 ? (
                <div className="p-6 text-center text-xs text-slate-400">No disposition requests in queue.</div>
              ) : (
                dispositions.map((req) => (
                  <div key={req.id} className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-bold text-slate-900">{req.request_number}</span>
                        <span
                          className={`text-xs px-2 py-0.5 rounded font-bold ${
                            req.status === "COMPLETED"
                              ? "bg-zinc-100 text-zinc-800"
                              : req.status === "APPROVED"
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                              : "bg-amber-50 text-amber-700 border border-amber-200"
                          }`}
                        >
                          {req.status}
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 mt-1">{req.justification}</p>
                      <div className="text-xs text-slate-400 mt-0.5">
                        Category: {req.category_code || "All"} • Records Count: {req.records_count} • Method:{" "}
                        {req.requested_disposition_method}
                      </div>
                      {req.certificate && (
                        <div className="mt-2 text-xs font-mono text-emerald-700 bg-emerald-50 p-2 rounded border border-emerald-200">
                          Certificate: {req.certificate.certificate_number} • Hash: {req.certificate.manifest_hash_sha256}
                        </div>
                      )}
                    </div>
                    <div className="flex gap-2">
                      {req.status === "PENDING_REVIEW" && (
                        <button
                          onClick={() => handleApproveDisposition(req.id)}
                          className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-medium rounded shadow-xs transition-colors"
                        >
                          Approve Request
                        </button>
                      )}
                      {req.status === "APPROVED" && (
                        <button
                          onClick={() => handleExecuteDisposition(req.id)}
                          className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white text-xs font-medium rounded shadow-xs transition-colors"
                        >
                          Execute Disposition
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
