"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type {
  Institution,
  OnboardingChecklistItemModel,
  OnboardingLifecycleState,
  OnboardingMigrationJobModel,
  OnboardingUATScenarioModel,
  OnboardingApprovalModel,
  ReadinessEvaluationResult,
  TenantOnboardingPlanModel,
} from "@campusos/types";

export default function TenantOnboardingPage() {
  const { hasPermission } = useAuth();
  const [institution, setInstitution] = useState<Institution | null>(null);
  const [plan, setPlan] = useState<TenantOnboardingPlanModel | null>(null);
  const [checklist, setChecklist] = useState<OnboardingChecklistItemModel[]>(
    [],
  );
  const [readiness, setReadiness] = useState<ReadinessEvaluationResult | null>(
    null,
  );
  const [migrations, setMigrations] = useState<OnboardingMigrationJobModel[]>(
    [],
  );
  const [uatScenarios, setUatScenarios] = useState<
    OnboardingUATScenarioModel[]
  >([]);
  const [approvals, setApprovals] = useState<OnboardingApprovalModel[]>([]);

  const [activeTab, setActiveTab] = useState<
    "readiness" | "migration" | "uat" | "approvals" | "golive"
  >("readiness");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Category filter
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");

  const canManage =
    hasPermission("core:institutions:manage") ||
    hasPermission("platform:tenants:manage") ||
    true;

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const instRes = await apiFetch<Institution>("/api/v1/institutions");
      setInstitution(instRes.data);

      if (instRes.data?.id) {
        // Fetch or create onboarding plan
        const planRes = await apiFetch<TenantOnboardingPlanModel>(
          `/api/v1/onboarding/plans/${instRes.data.id}`,
        ).catch(async () => {
          // If not created yet, create it
          return await apiFetch<TenantOnboardingPlanModel>(
            "/api/v1/onboarding/plans",
            {
              method: "POST",
              body: JSON.stringify({ tenant_id: instRes.data.id }),
            },
          );
        });

        setPlan(planRes.data);

        // Fetch checklist, readiness, migration, uat, approvals
        const [chkRes, readyRes, migRes, uatRes, appRes] = await Promise.all([
          apiFetch<OnboardingChecklistItemModel[]>(
            `/api/v1/onboarding/plans/${instRes.data.id}/checklist`,
          ),
          apiFetch<ReadinessEvaluationResult>(
            `/api/v1/onboarding/plans/${instRes.data.id}/readiness`,
          ),
          apiFetch<OnboardingMigrationJobModel[]>(
            `/api/v1/onboarding/plans/${instRes.data.id}/migration`,
          ),
          apiFetch<OnboardingUATScenarioModel[]>(
            `/api/v1/onboarding/plans/${instRes.data.id}/uat`,
          ),
          apiFetch<OnboardingApprovalModel[]>(
            `/api/v1/onboarding/plans/${instRes.data.id}/approvals`,
          ),
        ]);

        setChecklist(chkRes.data || []);
        setReadiness(readyRes.data);
        setMigrations(migRes.data || []);
        setUatScenarios(uatRes.data || []);
        setApprovals(appRes.data || []);
      }
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load onboarding orchestration data",
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleUpdateChecklist = async (itemCode: string, newStatus: string) => {
    if (!institution) return;
    try {
      await apiFetch(
        `/api/v1/onboarding/plans/${institution.id}/checklist/${itemCode}`,
        {
          method: "PATCH",
          body: JSON.stringify({
            status: newStatus,
            evidence_ref: `manual_attestation:${new Date().toISOString()}`,
            responsible_owner: "institution_admin",
          }),
        },
      );
      setActionSuccess(
        `Checklist criterion ${itemCode} updated to ${newStatus}`,
      );
      await loadData();
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to update checklist item",
      );
    }
  };

  const handleExecuteGoLive = async (isDryRun: boolean) => {
    if (!institution) return;
    const confirmed = window.confirm(
      isDryRun
        ? "Execute dry-run simulation of the 10-step go-live launch sequence?"
        : "CRITICAL: You are about to certify and activate this institution LIVE. Proceed?",
    );
    if (!confirmed) return;

    try {
      await apiFetch(
        `/api/v1/onboarding/plans/${institution.id}/golive/execute`,
        {
          method: "POST",
          body: JSON.stringify({
            is_dry_run: isDryRun,
            idempotency_key: `launch_${Date.now()}`,
          }),
        },
      );
      setActionSuccess(
        isDryRun
          ? "Dry-run launch sequence validated successfully."
          : "Institution ACTIVATED LIVE! Hypercare initiated.",
      );
      await loadData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Go-live execution failed");
    }
  };

  const handleRollback = async () => {
    if (!institution) return;
    const reason = window.prompt(
      "Enter documented reason for initiating emergency rollback:",
    );
    if (!reason || reason.trim().length < 10) {
      alert(
        "Rollback requires a documented reason with at least 10 characters.",
      );
      return;
    }

    try {
      await apiFetch(`/api/v1/onboarding/plans/${institution.id}/rollback`, {
        method: "POST",
        body: JSON.stringify({
          rollback_reason: reason.trim(),
          preserve_imported_data: true,
        }),
      });
      setActionSuccess(
        "Emergency rollback executed. Tenant suspended safely and data preserved.",
      );
      await loadData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Rollback failed");
    }
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-sm text-slate-400">
          Loading onboarding and go-live status...
        </div>
      </div>
    );
  }

  const filteredChecklist =
    selectedCategory === "ALL"
      ? checklist
      : checklist.filter((item) => item.category === selectedCategory);

  return (
    <div className="space-y-8">
      {/* Navigation Breadcrumb & Header */}
      <div>
        <div className="flex items-center gap-2 text-xs text-slate-400 mb-2">
          <Link href="/app/institution" className="hover:text-indigo-400">
            Institution
          </Link>
          <span>/</span>
          <span className="text-slate-200">Go-Live Orchestration</span>
        </div>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold tracking-tight text-white">
                {institution?.legal_name || "Institution"} — Go-Live
                Orchestration
              </h1>
              <span className="rounded-md bg-indigo-500/10 px-2.5 py-1 text-xs font-semibold text-indigo-400 border border-indigo-500/20">
                {plan?.current_state || "DRAFT"}
              </span>
            </div>
            <p className="mt-1 text-sm text-slate-400">
              Controlled onboarding, explainable readiness certification, data
              migration reconciliation, and launch orchestration.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => handleExecuteGoLive(true)}
              className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs font-medium text-slate-200 hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              Simulate Dry-Run
            </button>
            <button
              type="button"
              onClick={() => handleExecuteGoLive(false)}
              disabled={!readiness?.can_progress_to_next_stage}
              className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-medium text-white hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              Authorize Go-Live
            </button>
            <button
              type="button"
              onClick={handleRollback}
              className="rounded-lg border border-rose-800 bg-rose-950/40 px-3 py-2 text-xs font-medium text-rose-300 hover:bg-rose-900/60 focus:outline-none focus:ring-2 focus:ring-rose-500"
            >
              Rollback
            </button>
          </div>
        </div>
      </div>

      {actionSuccess && (
        <div className="rounded-lg border border-emerald-800 bg-emerald-950/40 p-4 text-sm text-emerald-300">
          {actionSuccess}
        </div>
      )}
      {error && (
        <div className="rounded-lg border border-rose-800 bg-rose-950/40 p-4 text-sm text-rose-300">
          {error}
        </div>
      )}

      {/* Readiness Evaluator Diagnostics Banner */}
      {readiness && (
        <div
          className={`rounded-xl border p-5 ${
            readiness.overall_status === "READY"
              ? "border-emerald-800 bg-emerald-950/20"
              : readiness.overall_status === "BLOCKED"
                ? "border-rose-800 bg-rose-950/20"
                : "border-amber-800 bg-amber-950/20"
          }`}
        >
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Readiness Assessment:
                </span>
                <span
                  className={`text-sm font-bold ${
                    readiness.overall_status === "READY"
                      ? "text-emerald-400"
                      : readiness.overall_status === "BLOCKED"
                        ? "text-rose-400"
                        : "text-amber-400"
                  }`}
                >
                  {readiness.overall_status}
                </span>
                <span className="text-xs text-slate-400">
                  ({readiness.passed_checks}/{readiness.total_checks} criteria
                  verified, {readiness.waived_checks} waived)
                </span>
              </div>
              <p className="mt-1 text-sm text-slate-300">
                {readiness.can_progress_to_next_stage
                  ? "All mandatory prerequisites, data reconciliations, and governance sign-offs are satisfied. Ready for live launch."
                  : "Go-live progression is blocked until outstanding requirements and sign-offs are resolved."}
              </p>
            </div>
            <div className="text-right">
              <span className="text-xs text-slate-400">
                Current Lifecycle Stage:
              </span>
              <div className="text-sm font-semibold text-white">
                {readiness.current_state}
              </div>
            </div>
          </div>

          {readiness.blocking_reasons.length > 0 && (
            <div className="mt-4 border-t border-slate-800/80 pt-3">
              <h4 className="text-xs font-semibold uppercase text-rose-400 tracking-wider">
                Active Blockers ({readiness.blocking_reasons.length}):
              </h4>
              <ul className="mt-1.5 list-disc pl-5 text-xs text-slate-300 space-y-1">
                {readiness.blocking_reasons.map(
                  (reason: string, idx: number) => (
                    <li key={idx}>{reason}</li>
                  ),
                )}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Tabs Navigation */}
      <div className="border-b border-slate-800 flex gap-6 text-sm font-medium">
        <button
          type="button"
          onClick={() => setActiveTab("readiness")}
          className={`pb-3 border-b-2 transition-colors ${
            activeTab === "readiness"
              ? "border-indigo-500 text-indigo-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Readiness Checklist ({checklist.length})
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("migration")}
          className={`pb-3 border-b-2 transition-colors ${
            activeTab === "migration"
              ? "border-indigo-500 text-indigo-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Data Migration & Reconciliation ({migrations.length})
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("uat")}
          className={`pb-3 border-b-2 transition-colors ${
            activeTab === "uat"
              ? "border-indigo-500 text-indigo-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          User Acceptance Testing ({uatScenarios.length})
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("approvals")}
          className={`pb-3 border-b-2 transition-colors ${
            activeTab === "approvals"
              ? "border-indigo-500 text-indigo-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Approval Matrix ({approvals.length})
        </button>
      </div>

      {/* Tab 1: Readiness Checklist */}
      {activeTab === "readiness" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex gap-2">
              {[
                "ALL",
                "PLATFORM_SETUP",
                "IDENTITY_ACCESS",
                "ACADEMIC_CONFIG",
                "FINANCE",
                "DATA_MIGRATION",
                "INTEGRATIONS_COMMS",
                "SECURITY_OPERATIONS",
              ].map((cat) => (
                <button
                  key={cat}
                  type="button"
                  onClick={() => setSelectedCategory(cat)}
                  className={`rounded-md px-2.5 py-1 text-xs font-medium border transition-colors ${
                    selectedCategory === cat
                      ? "border-indigo-500 bg-indigo-500/10 text-indigo-400"
                      : "border-slate-800 bg-slate-900/50 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {cat.replace("_", " ")}
                </button>
              ))}
            </div>
          </div>

          <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/40">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/60 text-xs font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">Code</th>
                  <th className="px-4 py-3">Criterion & Description</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Verification</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredChecklist.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/20">
                    <td className="px-4 py-3 font-mono text-xs font-semibold text-slate-200">
                      {item.item_code}
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-medium text-white flex items-center gap-2">
                        {item.title}
                        {item.is_required && (
                          <span className="rounded bg-rose-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-rose-400 border border-rose-500/20">
                            Required
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-slate-400 mt-0.5">
                        {item.description}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400">
                      {item.category}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`rounded-md px-2 py-0.5 text-xs font-medium border ${
                          item.status === "PASSED"
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                            : item.status === "WAIVED"
                              ? "bg-purple-500/10 text-purple-400 border-purple-500/20"
                              : item.status === "FAILED"
                                ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                                : item.status === "BLOCKED"
                                  ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                                  : "bg-slate-500/10 text-slate-400 border-slate-500/20"
                        }`}
                      >
                        {item.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400">
                      {item.verification_method}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {item.status !== "PASSED" && (
                        <button
                          type="button"
                          onClick={() =>
                            handleUpdateChecklist(item.item_code, "PASSED")
                          }
                          className="rounded bg-indigo-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-indigo-500"
                        >
                          Verify & Pass
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Data Migration & Reconciliation */}
      {activeTab === "migration" && (
        <div className="space-y-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
            <h3 className="text-sm font-semibold text-white">
              Migration Reconciliation Log
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Deterministic reconciliation between uploaded source files and
              operational records. Discrepancy count must equal 0.
            </p>
          </div>

          <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/40">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/60 text-xs font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">Domain</th>
                  <th className="px-4 py-3">Source File</th>
                  <th className="px-4 py-3">Records</th>
                  <th className="px-4 py-3">Accepted / Rejected</th>
                  <th className="px-4 py-3">Discrepancy</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {migrations.length === 0 ? (
                  <tr>
                    <td
                      colSpan={6}
                      className="px-4 py-8 text-center text-xs text-slate-500"
                    >
                      No data migration jobs recorded yet.
                    </td>
                  </tr>
                ) : (
                  migrations.map((job) => (
                    <tr key={job.id} className="hover:bg-slate-800/20">
                      <td className="px-4 py-3 font-semibold text-white">
                        {job.domain_name}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-300">
                        {job.source_filename}
                      </td>
                      <td className="px-4 py-3 text-xs">
                        {job.source_record_count}
                      </td>
                      <td className="px-4 py-3 text-xs">
                        <span className="text-emerald-400">
                          {job.accepted_record_count}
                        </span>{" "}
                        /{" "}
                        <span className="text-rose-400">
                          {job.rejected_record_count}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs font-semibold">
                        {job.reconciliation_diff_count === 0 ? (
                          <span className="text-emerald-400">0 (Match)</span>
                        ) : (
                          <span className="text-rose-400">
                            {job.reconciliation_diff_count} diff
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className="rounded bg-indigo-500/10 px-2 py-0.5 text-xs font-medium text-indigo-400 border border-indigo-500/20">
                          {job.status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: User Acceptance Testing */}
      {activeTab === "uat" && (
        <div className="space-y-4">
          <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/40">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/60 text-xs font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">Scenario</th>
                  <th className="px-4 py-3">Module & Outcome</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Defect</th>
                  <th className="px-4 py-3">Sign-off</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {uatScenarios.map((sc) => (
                  <tr key={sc.id} className="hover:bg-slate-800/20">
                    <td className="px-4 py-3 font-mono text-xs font-semibold text-slate-200">
                      {sc.scenario_code}
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-medium text-white">{sc.title}</div>
                      <div className="text-xs text-slate-400">
                        {sc.expected_outcome}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`rounded-md px-2 py-0.5 text-xs font-medium border ${
                          sc.status === "PASSED"
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                            : sc.status === "FAILED"
                              ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                              : "bg-slate-500/10 text-slate-400 border-slate-500/20"
                        }`}
                      >
                        {sc.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400">
                      {sc.defect_severity !== "NONE" ? (
                        <span className="text-rose-400 font-semibold">
                          {sc.defect_severity}
                        </span>
                      ) : (
                        "None"
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400">
                      {sc.sign_off_by || "Pending"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 4: Approvals Matrix */}
      {activeTab === "approvals" && (
        <div className="space-y-4">
          <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/40">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/60 text-xs font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">Governance Role</th>
                  <th className="px-4 py-3">Decision</th>
                  <th className="px-4 py-3">Approver Email</th>
                  <th className="px-4 py-3">Decision Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {approvals.map((app) => (
                  <tr key={app.id} className="hover:bg-slate-800/20">
                    <td className="px-4 py-3 font-semibold text-white">
                      {app.role.replace(/_/g, " ")}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`rounded-md px-2 py-0.5 text-xs font-medium border ${
                          app.decision === "APPROVED"
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                            : app.decision === "REJECTED"
                              ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                              : app.decision === "INVALIDATED"
                                ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                                : "bg-slate-500/10 text-slate-400 border-slate-500/20"
                        }`}
                      >
                        {app.decision}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-300">
                      {app.approver_email || "Pending Assignment"}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400">
                      {app.decision_at
                        ? new Date(app.decision_at).toLocaleString()
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
