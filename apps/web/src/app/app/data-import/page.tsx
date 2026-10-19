"use client";

import React, { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type {
  ImportConflictModel,
  ImportExecutionPolicy,
  ImportJobModel,
  ImportJobStatus,
  ImportMappingDefinitionModel,
  ImportPreviewModel,
  ImportReconciliationModel,
  ImportTemplateModel,
  ImportValidationSummaryModel,
} from "@campusos/types";

export default function DataImportPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<"jobs" | "templates" | "new_job" | "conflicts">("jobs");

  const [templates, setTemplates] = useState<ImportTemplateModel[]>([]);
  const [jobs, setJobs] = useState<ImportJobModel[]>([]);
  const [conflicts, setConflicts] = useState<ImportConflictModel[]>([]);
  const [selectedJob, setSelectedJob] = useState<ImportJobModel | null>(null);

  // Job Detail Sub-states
  const [validationSummary, setValidationSummary] = useState<ImportValidationSummaryModel | null>(null);
  const [previewData, setPreviewData] = useState<ImportPreviewModel | null>(null);
  const [reconData, setReconData] = useState<ImportReconciliationModel | null>(null);

  // New Job Form
  const [newJobName, setNewJobName] = useState("");
  const [selectedTemplateCode, setSelectedTemplateCode] = useState("STUDENTS_BULK_IMPORT");
  const [newJobPolicy, setNewJobPolicy] = useState<ImportExecutionPolicy>("CREATE_NEW");
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  // States
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionNotice, setActionNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [tplRes, jobsRes] = await Promise.all([
        apiFetch<ImportTemplateModel[]>("/api/v1/data-import/templates").catch(() => ({ data: [] })),
        apiFetch<ImportJobModel[]>("/api/v1/data-import/jobs").catch(() => ({ data: [] })),
      ]);

      setTemplates(tplRes.data || []);
      setJobs(jobsRes.data || []);
    } catch (err: any) {
      setError(err?.message || "Failed to load import records");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateJob = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newJobName.trim() || !uploadFile) {
      setError("Please specify a job name and select a CSV/XLSX file to upload.");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      // 1. Create Job in DRAFT
      const createRes = await apiFetch<ImportJobModel>("/api/v1/data-import/jobs", {
        method: "POST",
        body: JSON.stringify({
          name: newJobName,
          template_code: selectedTemplateCode,
          execution_policy: newJobPolicy,
        }),
      });

      if (!createRes.data) throw new Error("Failed to create import job");
      const job = createRes.data;

      // 2. Upload Source File
      const formData = new FormData();
      formData.append("file", uploadFile);

      const uploadRes = await fetch(`/api/v1/data-import/jobs/${job.id}/upload`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("campusos_token") || ""}`,
        },
        body: formData,
      });

      if (!uploadRes.ok) {
        const errJson = await uploadRes.json().catch(() => ({}));
        throw new Error(errJson.detail || "Failed to upload file");
      }

      setActionNotice(`Import job '${job.name}' initialized and source file uploaded successfully.`);
      setNewJobName("");
      setUploadFile(null);
      setActiveTab("jobs");
      await loadData();
    } catch (err: any) {
      setError(err?.message || "Job creation failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRunValidation = async (jobId: string) => {
    try {
      setIsSubmitting(true);
      setError(null);
      const res = await apiFetch<ImportValidationSummaryModel>(`/api/v1/data-import/jobs/${jobId}/validate`, {
        method: "POST",
      });
      setValidationSummary(res.data);
      setActionNotice("Validation pipeline completed.");
      await loadData();
      if (selectedJob && selectedJob.id === jobId) {
        const refreshed = await apiFetch<ImportJobModel>(`/api/v1/data-import/jobs/${jobId}`);
        setSelectedJob(refreshed.data);
      }
    } catch (err: any) {
      setError(err?.message || "Validation failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFetchPreview = async (jobId: string) => {
    try {
      setIsSubmitting(true);
      setError(null);
      const res = await apiFetch<ImportPreviewModel>(`/api/v1/data-import/jobs/${jobId}/preview`);
      setPreviewData(res.data);
    } catch (err: any) {
      setError(err?.message || "Failed to load preview");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleApproveJob = async (jobId: string, approved: boolean) => {
    try {
      setIsSubmitting(true);
      setError(null);
      await apiFetch(`/api/v1/data-import/jobs/${jobId}/approve`, {
        method: "POST",
        body: JSON.stringify({ approved, notes: "Approved via Web Dashboard" }),
      });
      setActionNotice(approved ? "Job approved for execution." : "Job rejected.");
      await loadData();
      if (selectedJob && selectedJob.id === jobId) {
        const refreshed = await apiFetch<ImportJobModel>(`/api/v1/data-import/jobs/${jobId}`);
        setSelectedJob(refreshed.data);
      }
    } catch (err: any) {
      setError(err?.message || "Approval decision failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleExecuteJob = async (jobId: string) => {
    try {
      setIsSubmitting(true);
      setError(null);
      const res = await apiFetch<ImportJobModel>(`/api/v1/data-import/jobs/${jobId}/execute`, {
        method: "POST",
        body: JSON.stringify({ batch_size: 50, stop_on_first_error: false }),
      });
      setSelectedJob(res.data);
      setActionNotice(`Execution completed: ${res.data.created_record_count} created, ${res.data.failed_record_count} failed.`);
      await loadData();
    } catch (err: any) {
      setError(err?.message || "Execution failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReconcileJob = async (jobId: string) => {
    try {
      setIsSubmitting(true);
      setError(null);
      const res = await apiFetch<ImportReconciliationModel>(`/api/v1/data-import/jobs/${jobId}/reconcile`, {
        method: "POST",
      });
      setReconData(res.data);
      setActionNotice(`Reconciliation: ${res.data.reconciliation_status} (Diff=${res.data.unaccounted_difference})`);
      await loadData();
    } catch (err: any) {
      setError(err?.message || "Reconciliation failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDownloadBlankTemplate = (code: string) => {
    window.open(`/api/v1/data-import/templates/${code}/download-blank`, "_blank");
  };

  const handleDownloadErrorReport = (jobId: string) => {
    window.open(`/api/v1/data-import/jobs/${jobId}/error-report`, "_blank");
  };

  const getStatusBadge = (status: ImportJobStatus | string) => {
    const s = String(status).toUpperCase();
    if (s === "COMPLETED") return "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30";
    if (s === "READY_TO_EXECUTE") return "bg-blue-500/15 text-blue-400 border border-blue-500/30";
    if (s === "EXECUTION_RUNNING" || s === "VALIDATION_RUNNING") return "bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 animate-pulse";
    if (s === "AWAITING_APPROVAL") return "bg-amber-500/15 text-amber-400 border border-amber-500/30";
    if (s === "VALIDATION_FAILED" || s === "FAILED") return "bg-rose-500/15 text-rose-400 border border-rose-500/30";
    if (s === "PARTIALLY_COMPLETED") return "bg-yellow-500/15 text-yellow-400 border border-yellow-500/30";
    if (s === "CANCELLED") return "bg-slate-500/15 text-slate-400 border border-slate-500/30";
    return "bg-slate-800 text-slate-300 border border-slate-700";
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-br from-indigo-500/20 to-cyan-500/20 border border-indigo-500/30">
              <svg className="w-6 h-6 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                Enterprise Data Import & Migration
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-medium">
                  Step 40 Engine
                </span>
              </h1>
              <p className="text-sm text-slate-400">
                Governed bulk data onboarding, validation, resumable batch execution, and reconciliation.
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={() => setActiveTab("new_job")}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-medium text-sm transition-all shadow-lg shadow-indigo-600/20 flex items-center gap-2 self-start md:self-auto"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Import Job
        </button>
      </div>

      {/* Notifications */}
      {actionNotice && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span>{actionNotice}</span>
          </div>
          <button onClick={() => setActionNotice(null)} className="text-emerald-400/60 hover:text-emerald-400 font-bold">×</button>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-rose-400/60 hover:text-rose-400 font-bold">×</button>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-800 gap-2">
        {[
          { key: "jobs", label: "Import Jobs", count: jobs.length },
          { key: "templates", label: "Domain Templates", count: templates.length },
          { key: "new_job", label: "Create Job" },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-all flex items-center gap-2 ${
              activeTab === tab.key
                ? "border-indigo-500 text-white"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            {tab.label}
            {tab.count !== undefined && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab 1: Import Jobs */}
      {activeTab === "jobs" && (
        <div className="space-y-4">
          {loading ? (
            <div className="p-8 text-center text-slate-400 animate-pulse">Loading import jobs...</div>
          ) : jobs.length === 0 ? (
            <div className="p-12 text-center rounded-2xl bg-slate-900/50 border border-slate-800">
              <svg className="w-12 h-12 text-slate-600 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h3 className="text-lg font-semibold text-white">No Import Jobs Found</h3>
              <p className="text-sm text-slate-400 mt-1 max-w-md mx-auto">
                No institutional data imports have been initialized yet. Create your first import job to bulk migrate students, faculty, or courses.
              </p>
              <button
                onClick={() => setActiveTab("new_job")}
                className="mt-4 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium"
              >
                Start First Import
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {jobs.map((job) => (
                <div
                  key={job.id}
                  className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 hover:border-slate-700 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="space-y-2">
                    <div className="flex items-center gap-3">
                      <span className={`text-xs px-2.5 py-1 rounded-full font-semibold ${getStatusBadge(job.status)}`}>
                        {job.status}
                      </span>
                      <h3 className="text-base font-semibold text-white">{job.name}</h3>
                      <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                        {job.template_code}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-xs text-slate-400">
                      <span>Source: <strong className="text-slate-200">{job.source_filename || "Pending Upload"}</strong></span>
                      <span>Total: <strong className="text-slate-200">{job.source_record_count}</strong></span>
                      <span>Valid: <strong className="text-emerald-400">{job.valid_record_count}</strong></span>
                      <span>Created: <strong className="text-indigo-400">{job.created_record_count}</strong></span>
                      <span>Failed: <strong className="text-rose-400">{job.failed_record_count}</strong></span>
                      <span>Recon: <strong className="text-slate-200">{job.reconciliation_status}</strong></span>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    {/* Action buttons based on status */}
                    {job.status === "MAPPING_PENDING" && (
                      <button
                        onClick={() => handleRunValidation(job.id)}
                        disabled={isSubmitting}
                        className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-medium"
                      >
                        Run Validation
                      </button>
                    )}

                    {job.status === "VALIDATION_FAILED" && (
                      <>
                        <button
                          onClick={() => handleDownloadErrorReport(job.id)}
                          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-rose-400 border border-rose-500/30 rounded-lg text-xs font-medium"
                        >
                          Error Report (CSV)
                        </button>
                        <button
                          onClick={() => handleRunValidation(job.id)}
                          disabled={isSubmitting}
                          className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-medium"
                        >
                          Re-validate
                        </button>
                      </>
                    )}

                    {job.status === "AWAITING_APPROVAL" && (
                      <>
                        <button
                          onClick={() => handleFetchPreview(job.id)}
                          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium"
                        >
                          Preview
                        </button>
                        <button
                          onClick={() => handleApproveJob(job.id, true)}
                          disabled={isSubmitting}
                          className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-medium"
                        >
                          Approve Execution
                        </button>
                      </>
                    )}

                    {job.status === "READY_TO_EXECUTE" && (
                      <>
                        <button
                          onClick={() => handleFetchPreview(job.id)}
                          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium"
                        >
                          Preview
                        </button>
                        <button
                          onClick={() => handleExecuteJob(job.id)}
                          disabled={isSubmitting}
                          className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-medium shadow-md shadow-emerald-600/20"
                        >
                          Execute Import
                        </button>
                      </>
                    )}

                    {(job.status === "COMPLETED" || job.status === "PARTIALLY_COMPLETED") && (
                      <>
                        <button
                          onClick={() => handleReconcileJob(job.id)}
                          disabled={isSubmitting}
                          className="px-3 py-1.5 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 rounded-lg text-xs font-medium"
                        >
                          Reconcile
                        </button>
                        {job.failed_record_count > 0 && (
                          <button
                            onClick={() => handleDownloadErrorReport(job.id)}
                            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-rose-400 border border-rose-500/30 rounded-lg text-xs font-medium"
                          >
                            Errors ({job.failed_record_count})
                          </button>
                        )}
                      </>
                    )}

                    <button
                      onClick={() => {
                        setSelectedJob(job);
                        handleFetchPreview(job.id);
                      }}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium"
                    >
                      Details
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Inspection Drawer / Modal */}
          {selectedJob && (
            <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
              <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl">
                <div className="p-6 border-b border-slate-800 flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-bold text-white">{selectedJob.name}</h2>
                    <p className="text-xs text-slate-400">Template: {selectedJob.template_code} • Policy: {selectedJob.execution_policy}</p>
                  </div>
                  <button
                    onClick={() => {
                      setSelectedJob(null);
                      setPreviewData(null);
                      setValidationSummary(null);
                      setReconData(null);
                    }}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
                  >
                    ✕
                  </button>
                </div>

                <div className="p-6 overflow-y-auto space-y-6">
                  {/* Status & Metrics Bar */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
                    <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/50">
                      <div className="text-xs text-slate-400">Total Rows</div>
                      <div className="text-xl font-bold text-white">{selectedJob.source_record_count}</div>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/50">
                      <div className="text-xs text-slate-400">Valid</div>
                      <div className="text-xl font-bold text-emerald-400">{selectedJob.valid_record_count}</div>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/50">
                      <div className="text-xs text-slate-400">Created</div>
                      <div className="text-xl font-bold text-indigo-400">{selectedJob.created_record_count}</div>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/50">
                      <div className="text-xs text-slate-400">Failed / Errors</div>
                      <div className="text-xl font-bold text-rose-400">{selectedJob.failed_record_count || selectedJob.error_record_count}</div>
                    </div>
                  </div>

                  {/* Preview Breakdown */}
                  {previewData && (
                    <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                      <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">High-Impact Execution Preview</h4>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <span className="text-slate-400">Records to Create: <strong className="text-emerald-400">{previewData.records_to_create}</strong></span>
                        <span className="text-slate-400">Records to Update: <strong className="text-cyan-400">{previewData.records_to_update}</strong></span>
                        <span className="text-slate-400">Records to Skip: <strong className="text-amber-400">{previewData.records_to_skip}</strong></span>
                        <span className="text-slate-400">Blocking Errors: <strong className="text-rose-400">{previewData.records_blocking_execution}</strong></span>
                      </div>
                      {previewData.high_impact_summary.length > 0 && (
                        <div className="pt-2 border-t border-slate-800 text-xs text-amber-300 space-y-1">
                          {previewData.high_impact_summary.map((msg, i) => (
                            <div key={i}>• {msg}</div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Reconciliation Breakdown */}
                  {reconData && (
                    <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                      <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Post-Import Reconciliation</h4>
                      <div className="flex items-center justify-between text-xs">
                        <span>Status: <strong className={reconData.is_balanced ? "text-emerald-400" : "text-rose-400"}>{reconData.reconciliation_status}</strong></span>
                        <span>Diff: <strong className="text-white">{reconData.unaccounted_difference}</strong></span>
                      </div>
                    </div>
                  )}
                </div>

                <div className="p-6 border-t border-slate-800 flex justify-end gap-3">
                  <button
                    onClick={() => handleDownloadErrorReport(selectedJob.id)}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-sm font-medium"
                  >
                    Download Error Report (CSV)
                  </button>
                  {selectedJob.status === "READY_TO_EXECUTE" && (
                    <button
                      onClick={() => handleExecuteJob(selectedJob.id)}
                      disabled={isSubmitting}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium shadow-md shadow-emerald-600/20"
                    >
                      Execute Import
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Domain Templates */}
      {activeTab === "templates" && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {templates.map((tpl) => (
            <div
              key={tpl.id}
              className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between hover:border-slate-700 transition-all space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs px-2.5 py-1 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-medium">
                    {tpl.target_domain}
                  </span>
                  <span className="text-xs text-slate-500">v{tpl.version}</span>
                </div>
                <h3 className="text-base font-bold text-white">{tpl.name}</h3>
                <p className="text-xs text-slate-400 line-clamp-2">{tpl.description}</p>

                <div className="pt-2 border-t border-slate-800 text-xs text-slate-400 space-y-1">
                  <div>Required: <strong className="text-slate-200">{tpl.required_fields.length} fields</strong></div>
                  <div>Keys: <strong className="text-slate-200">{tpl.supported_matching_keys.join(", ")}</strong></div>
                  <div>Approval: <strong className="text-amber-400">&gt; {tpl.requires_approval_threshold} rows</strong></div>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-800 flex items-center justify-between gap-2">
                <button
                  onClick={() => handleDownloadBlankTemplate(tpl.code)}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-indigo-300 border border-indigo-500/30 rounded-lg text-xs font-medium flex items-center gap-1.5"
                >
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Download Blank CSV
                </button>
                <button
                  onClick={() => {
                    setSelectedTemplateCode(tpl.code);
                    setActiveTab("new_job");
                  }}
                  className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium"
                >
                  Use Template
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab 3: Create Job Wizard */}
      {activeTab === "new_job" && (
        <div className="max-w-2xl mx-auto p-6 md:p-8 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl space-y-6">
          <div>
            <h2 className="text-lg font-bold text-white">Create New Data Import Job</h2>
            <p className="text-xs text-slate-400 mt-1">Upload a structured CSV or XLSX file and configure the target domain mapping.</p>
          </div>

          <form onSubmit={handleCreateJob} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Import Job Title</label>
              <input
                type="text"
                value={newJobName}
                onChange={(e) => setNewJobName(e.target.value)}
                placeholder="e.g. AY 2026-27 Computer Science Batch Intake"
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white focus:outline-none focus:border-indigo-500"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Domain Template</label>
              <select
                value={selectedTemplateCode}
                onChange={(e) => setSelectedTemplateCode(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white focus:outline-none focus:border-indigo-500"
              >
                {templates.map((t) => (
                  <option key={t.code} value={t.code}>
                    {t.name} ({t.target_domain})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Execution Policy</label>
              <select
                value={newJobPolicy}
                onChange={(e) => setNewJobPolicy(e.target.value as any)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="CREATE_NEW">Create New Only (Fail on existing duplicates)</option>
                <option value="UPDATE_EXISTING">Update Existing Only</option>
                <option value="UPSERT">Upsert (Create new or update existing)</option>
                <option value="SKIP_CONFLICTS">Skip Conflicting Records</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Source File (CSV or XLSX)</label>
              <input
                type="file"
                accept=".csv, .xlsx, .xls"
                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-400 file:mr-4 file:py-1 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500"
                required
              />
              <p className="text-[11px] text-slate-500 mt-1">Maximum file size: 25 MB. Formula execution is strictly blocked.</p>
            </div>

            <div className="pt-4 border-t border-slate-800 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setActiveTab("jobs")}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-medium"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium shadow-md shadow-indigo-600/20 disabled:opacity-50"
              >
                {isSubmitting ? "Uploading & Initializing..." : "Create & Upload"}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
