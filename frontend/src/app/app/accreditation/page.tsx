"use client";

import React, { useEffect, useState, useMemo } from "react";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import {
  Award,
  CheckCircle2,
  AlertTriangle,
  Clock,
  FileText,
  ChevronRight,
  Plus,
  Search,
  Filter,
  Layers,
  ShieldCheck,
  Scale,
  RefreshCw,
  BookOpen,
  Sparkles,
  TrendingUp,
  Send,
  Check,
  X,
  Lock,
  Calendar,
  Users,
  ExternalLink,
  AlertCircle,
  FileCheck,
  ShieldAlert,
  BarChart3,
  ClipboardList,
  Target,
  ArrowRight,
  CheckSquare,
} from "lucide-react";
import type {
  AccreditationDashboardSummaryModel,
  AccreditationFrameworkModel,
  AccreditationCriterionModel,
  AccreditationAssessmentCycleModel,
  AccreditationCriterionAssessmentModel,
  AccreditationEvidenceModel,
  QualityIndicatorModel,
  QualityAuditProgramModel,
  QualityFindingModel,
  QualityCorrectiveActionModel,
  QualityImprovementPlanModel,
  AccreditationReadinessSnapshotModel,
} from "@campusos/types";
import {
  AccreditationFrameworkType,
  AccreditationFrameworkStatus,
  AccreditationAssessmentStatus,
  AccreditationMaturityLevel,
  AccreditationEvidenceCategory,
  AccreditationEvidenceVerificationStatus,
  QualityIndicatorCategory,
  QualityDataQualityStatus,
  QualityAuditStatus,
  QualityAuditType,
  QualityFindingSeverity,
  QualityFindingStatus,
  QualityCAPAType,
  QualityCAPAStatus,
  QualityImprovementStatus,
  AccreditationReadinessCategory,
} from "@campusos/types";

export default function AccreditationQualityConsolePage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<
    | "overview"
    | "frameworks"
    | "assessment"
    | "evidence"
    | "kpi"
    | "audits"
    | "readiness"
  >("overview");

  // Summary & Master Data
  const [summary, setSummary] =
    useState<AccreditationDashboardSummaryModel | null>(null);
  const [frameworks, setFrameworks] = useState<AccreditationFrameworkModel[]>(
    [],
  );
  const [cycles, setCycles] = useState<AccreditationAssessmentCycleModel[]>([]);
  const [selectedCycleId, setSelectedCycleId] = useState<string>("");
  const [assessments, setAssessments] = useState<
    AccreditationCriterionAssessmentModel[]
  >([]);
  const [criteria, setCriteria] = useState<AccreditationCriterionModel[]>([]);
  const [evidences, setEvidences] = useState<AccreditationEvidenceModel[]>([]);
  const [indicators, setIndicators] = useState<QualityIndicatorModel[]>([]);
  const [audits, setAudits] = useState<QualityAuditProgramModel[]>([]);
  const [findings, setFindings] = useState<QualityFindingModel[]>([]);
  const [capas, setCapas] = useState<QualityCorrectiveActionModel[]>([]);
  const [cqiPlans, setCqiPlans] = useState<QualityImprovementPlanModel[]>([]);
  const [readinessSnapshot, setReadinessSnapshot] =
    useState<AccreditationReadinessSnapshotModel | null>(null);

  // Filter States
  const [searchQuery, setSearchQuery] = useState("");
  const [assessmentStatusFilter, setAssessmentStatusFilter] = useState("ALL");
  const [evidenceCategoryFilter, setEvidenceCategoryFilter] = useState("ALL");
  const [evidenceStatusFilter, setEvidenceStatusFilter] = useState("ALL");

  // Modals & Action States
  const [isAssessmentModalOpen, setIsAssessmentModalOpen] = useState(false);
  const [selectedAssessment, setSelectedAssessment] =
    useState<AccreditationCriterionAssessmentModel | null>(null);
  const [editScore, setEditScore] = useState<number | "">("");
  const [editMaturity, setEditMaturity] = useState<string>(
    AccreditationMaturityLevel.LEVEL_3_DEFINED,
  );
  const [editSummary, setEditSummary] = useState("");
  const [editFindings, setEditFindings] = useState("");
  const [editStrengths, setEditStrengths] = useState("");
  const [editWeaknesses, setEditWeaknesses] = useState("");
  const [editRecommendations, setEditRecommendations] = useState("");
  const [isNotApplicable, setIsNotApplicable] = useState(false);
  const [notApplicableReason, setNotApplicableReason] = useState("");

  // Review Modal
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);
  const [reviewDecision, setReviewDecision] = useState<
    "APPROVED" | "CHANGES_REQUESTED"
  >("APPROVED");
  const [reviewComments, setReviewComments] = useState("");
  const [adjustedScore, setAdjustedScore] = useState<number | "">("");

  // Create Evidence Modal
  const [isEvidenceModalOpen, setIsEvidenceModalOpen] = useState(false);
  const [evCode, setEvCode] = useState("");
  const [evTitle, setEvTitle] = useState("");
  const [evCategory, setEvCategory] = useState<string>(
    AccreditationEvidenceCategory.POLICY_SOP,
  );
  const [evValidFrom, setEvValidFrom] = useState("");
  const [evValidUntil, setEvValidUntil] = useState("");

  // Finalize Audit Modal
  const [isFinalizeModalOpen, setIsFinalizeModalOpen] = useState(false);
  const [finalizeAuditId, setFinalizeAuditId] = useState("");
  const [finalizeFindings, setFinalizeFindings] = useState("");
  const [finalizeRecommendations, setFinalizeRecommendations] = useState("");

  // Close CAPA Modal
  const [isCloseCapaModalOpen, setIsCloseCapaModalOpen] = useState(false);
  const [selectedCapa, setSelectedCapa] =
    useState<QualityCorrectiveActionModel | null>(null);
  const [capaDecision, setCapaDecision] = useState<
    "CLOSED_EFFECTIVE" | "REJECTED_FURTHER_ACTION"
  >("CLOSED_EFFECTIVE");
  const [capaNotes, setCapaNotes] = useState("");

  // UI state
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 1. Load Primary Data
  const loadConsoleData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [sumRes, fwRes, cycRes, evRes, indRes, audRes, findRes, cqiRes] =
        await Promise.all([
          apiFetch<AccreditationDashboardSummaryModel>(
            "/api/v1/accreditation/dashboard/summary",
          ).catch(() => ({ data: null })),
          apiFetch<AccreditationFrameworkModel[]>(
            "/api/v1/accreditation/frameworks",
          ).catch(() => ({ data: [] })),
          apiFetch<AccreditationAssessmentCycleModel[]>(
            "/api/v1/accreditation/cycles",
          ).catch(() => ({ data: [] })),
          apiFetch<AccreditationEvidenceModel[]>(
            "/api/v1/accreditation/evidences",
          ).catch(() => ({ data: [] })),
          apiFetch<QualityIndicatorModel[]>(
            "/api/v1/accreditation/indicators",
          ).catch(() => ({ data: [] })),
          apiFetch<QualityAuditProgramModel[]>(
            "/api/v1/accreditation/audits",
          ).catch(() => ({ data: [] })),
          apiFetch<QualityFindingModel[]>(
            "/api/v1/accreditation/findings",
          ).catch(() => ({ data: [] })),
          apiFetch<QualityImprovementPlanModel[]>(
            "/api/v1/accreditation/cqi-plans",
          ).catch(() => ({ data: [] })),
        ]);

      setSummary(sumRes.data);
      const fwList = fwRes.data || [];
      setFrameworks(fwList);
      const cycList = cycRes.data || [];
      setCycles(cycList);
      setEvidences(evRes.data || []);
      setIndicators(indRes.data || []);
      setAudits(audRes.data || []);
      setFindings(findRes.data || []);
      setCqiPlans(cqiRes.data || []);

      if (cycList.length > 0) {
        const initialCycle = cycList[0].id;
        setSelectedCycleId(initialCycle);
        await loadCycleAssessments(initialCycle);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load accreditation quality data");
    } finally {
      setLoading(false);
    }
  };

  // 2. Load Criterion Assessments for Selected Cycle
  const loadCycleAssessments = async (cycleId: string) => {
    try {
      const [assessRes, snapshotRes] = await Promise.all([
        apiFetch<AccreditationCriterionAssessmentModel[]>(
          `/api/v1/accreditation/cycles/${cycleId}/assessments`,
        ),
        apiFetch<AccreditationReadinessSnapshotModel>(
          `/api/v1/accreditation/cycles/${cycleId}/readiness`,
        ).catch(() => ({ data: null })),
      ]);
      setAssessments(assessRes.data || []);
      setReadinessSnapshot(snapshotRes.data);
    } catch {
      // silently handle
    }
  };

  useEffect(() => {
    loadConsoleData();
  }, []);

  const handleCycleChange = async (cycleId: string) => {
    setSelectedCycleId(cycleId);
    await loadCycleAssessments(cycleId);
  };

  // Seed Default Frameworks
  const handleSeedTemplates = async () => {
    try {
      setLoading(true);
      await apiFetch("/api/v1/accreditation/frameworks/seed-defaults", {
        method: "POST",
      });
      setNotice(
        "Statutory accreditation frameworks (NAAC, NBA, ISO-21001) successfully initialized.",
      );
      await loadConsoleData();
    } catch (err: any) {
      setError(err?.message || "Failed to seed default frameworks");
    } finally {
      setLoading(false);
    }
  };

  // Run Scheduled Sweep
  const handleRunSweep = async () => {
    try {
      const res = await apiFetch<any>("/api/v1/accreditation/scheduler/sweep", {
        method: "POST",
      });
      setNotice(
        `Quality Compliance Sweep completed: ${res.data?.expired_evidence_flagged ?? 0} expired evidences flagged, ${res.data?.overdue_findings_flagged ?? 0} overdue findings escalated.`,
      );
      await loadConsoleData();
    } catch (err: any) {
      setError(err?.message || "Sweep failed to execute");
    }
  };

  // Open Assessment Draft Modal
  const openAssessmentEditor = (
    assessment: AccreditationCriterionAssessmentModel,
  ) => {
    setSelectedAssessment(assessment);
    setEditScore(assessment.score ?? "");
    setEditMaturity(
      assessment.maturity_level || AccreditationMaturityLevel.LEVEL_3_DEFINED,
    );
    setEditSummary(assessment.executive_summary || "");
    setEditFindings(assessment.findings || "");
    setEditStrengths(assessment.strengths || "");
    setEditWeaknesses(assessment.weaknesses || "");
    setEditRecommendations(assessment.recommendations || "");
    setIsNotApplicable(
      assessment.status === AccreditationAssessmentStatus.NOT_APPLICABLE,
    );
    setNotApplicableReason(assessment.not_applicable_reason || "");
    setIsAssessmentModalOpen(true);
  };

  // Save Assessment Draft
  const handleSaveDraft = async () => {
    if (!selectedAssessment) return;
    try {
      const payload: any = {
        lock_version: selectedAssessment.lock_version,
        score: editScore === "" ? null : Number(editScore),
        maturity_level: editMaturity,
        executive_summary: editSummary,
        findings: editFindings,
        strengths: editStrengths,
        weaknesses: editWeaknesses,
        recommendations: editRecommendations,
      };

      if (isNotApplicable) {
        if (!notApplicableReason.trim()) {
          setError(
            "A comprehensive statutory justification is required when marking a criterion Not Applicable.",
          );
          return;
        }
        payload.not_applicable_reason = notApplicableReason.trim();
      }

      await apiFetch(
        `/api/v1/accreditation/assessments/${selectedAssessment.id}/draft`,
        {
          method: "PUT",
          body: JSON.stringify(payload),
        },
      );

      setNotice(`Assessment draft for criterion updated successfully.`);
      setIsAssessmentModalOpen(false);
      if (selectedCycleId) await loadCycleAssessments(selectedCycleId);
    } catch (err: any) {
      setError(err?.message || "Failed to update assessment draft");
    }
  };

  // Submit Assessment for Review
  const handleSubmitAssessment = async (
    assessment: AccreditationCriterionAssessmentModel,
  ) => {
    try {
      await apiFetch(
        `/api/v1/accreditation/assessments/${assessment.id}/submit`,
        {
          method: "POST",
          body: JSON.stringify({
            lock_version: assessment.lock_version,
            submission_notes:
              "Submitted for independent institutional peer review.",
          }),
        },
      );
      setNotice("Criterion assessment submitted for independent peer review.");
      if (selectedCycleId) await loadCycleAssessments(selectedCycleId);
    } catch (err: any) {
      setError(err?.message || "Failed to submit assessment");
    }
  };

  // Open Review Dialog
  const openReviewDialog = (
    assessment: AccreditationCriterionAssessmentModel,
  ) => {
    setSelectedAssessment(assessment);
    setAdjustedScore(assessment.score ?? "");
    setReviewDecision("APPROVED");
    setReviewComments("");
    setIsReviewModalOpen(true);
  };

  // Submit Peer Review Decision
  const handleReviewDecision = async () => {
    if (!selectedAssessment) return;
    try {
      await apiFetch(
        `/api/v1/accreditation/assessments/${selectedAssessment.id}/review`,
        {
          method: "POST",
          body: JSON.stringify({
            decision: reviewDecision,
            reviewer_comments: reviewComments,
            adjusted_score:
              adjustedScore === "" ? undefined : Number(adjustedScore),
          }),
        },
      );
      setNotice(`Assessment review recorded: ${reviewDecision}.`);
      setIsReviewModalOpen(false);
      if (selectedCycleId) await loadCycleAssessments(selectedCycleId);
    } catch (err: any) {
      setError(err?.message || "Failed to record review decision");
    }
  };

  // Finalize Audit Report
  const handleFinalizeAudit = async () => {
    if (!finalizeAuditId) return;
    try {
      await apiFetch(
        `/api/v1/accreditation/audits/${finalizeAuditId}/finalize`,
        {
          method: "POST",
          body: JSON.stringify({
            summary_findings: finalizeFindings,
            recommendations: finalizeRecommendations,
          }),
        },
      );
      setNotice(
        "Audit report finalized and permanently locked as an immutable quality record.",
      );
      setIsFinalizeModalOpen(false);
      await loadConsoleData();
    } catch (err: any) {
      setError(err?.message || "Failed to finalize audit report");
    }
  };

  // Close CAPA Action
  const handleCloseCapa = async () => {
    if (!selectedCapa) return;
    try {
      await apiFetch(`/api/v1/accreditation/capa/${selectedCapa.id}/close`, {
        method: "POST",
        body: JSON.stringify({
          closure_decision: capaDecision,
          closure_notes: capaNotes,
        }),
      });
      setNotice(`Corrective Action decision registered: ${capaDecision}.`);
      setIsCloseCapaModalOpen(false);
      await loadConsoleData();
    } catch (err: any) {
      setError(err?.message || "Failed to register CAPA closure decision");
    }
  };

  // Filtered Assessments
  const filteredAssessments = useMemo(() => {
    return assessments.filter((a) => {
      const matchesSearch =
        searchQuery === "" ||
        a.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (a.executive_summary &&
          a.executive_summary
            .toLowerCase()
            .includes(searchQuery.toLowerCase()));
      const matchesStatus =
        assessmentStatusFilter === "ALL" || a.status === assessmentStatusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [assessments, searchQuery, assessmentStatusFilter]);

  // Filtered Evidences
  const filteredEvidences = useMemo(() => {
    return evidences.filter((e) => {
      const matchesSearch =
        searchQuery === "" ||
        e.evidence_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
        e.title.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesCat =
        evidenceCategoryFilter === "ALL" ||
        e.evidence_category === evidenceCategoryFilter;
      const matchesStatus =
        evidenceStatusFilter === "ALL" ||
        e.verification_status === evidenceStatusFilter;
      return matchesSearch && matchesCat && matchesStatus;
    });
  }, [evidences, searchQuery, evidenceCategoryFilter, evidenceStatusFilter]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6">
      {/* 1. Header & Title Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-amber-400">
            <Award className="h-4 w-4" />
            <span>Governance & Quality Assurance</span>
          </div>
          <h1 className="text-2xl font-black tracking-tight text-white mt-1">
            Institutional Accreditation & Continuous Improvement Engine
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            End-to-end statutory compliance, multi-criteria rubrics, verifiable
            evidence provenance, internal audits, and CAPA.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={handleRunSweep}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800 hover:text-white transition"
          >
            <Clock className="h-3.5 w-3.5 text-amber-400" />
            <span>Compliance Sweep</span>
          </button>
          <button
            onClick={handleSeedTemplates}
            className="flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-amber-600 hover:bg-amber-500 text-white shadow-lg shadow-amber-600/20 transition"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>Seed Standard Templates</span>
          </button>
        </div>
      </div>

      {/* Global Alerts / Notices */}
      {notice && (
        <div className="flex items-center justify-between p-3.5 rounded-xl bg-emerald-950/60 border border-emerald-800/80 text-emerald-200 text-xs">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
            <span>{notice}</span>
          </div>
          <button
            onClick={() => setNotice(null)}
            className="text-emerald-400 hover:text-emerald-100"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {error && (
        <div className="flex items-center justify-between p-3.5 rounded-xl bg-rose-950/60 border border-rose-800/80 text-rose-200 text-xs">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-rose-400 hover:text-rose-100"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* 2. Primary KPI Ribbon */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 text-[10px] uppercase font-bold tracking-wider">
            <span>Frameworks</span>
            <Award className="h-3.5 w-3.5 text-indigo-400" />
          </div>
          <div className="text-xl font-black text-white mt-1">
            {summary?.active_frameworks_count ?? frameworks.length}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            Statutory & Custom
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 text-[10px] uppercase font-bold tracking-wider">
            <span>Active Cycles</span>
            <Layers className="h-3.5 w-3.5 text-blue-400" />
          </div>
          <div className="text-xl font-black text-white mt-1">
            {summary?.active_cycles_count ?? cycles.length}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            SSR / Assessment
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 text-[10px] uppercase font-bold tracking-wider">
            <span>Evaluated Criteria</span>
            <CheckSquare className="h-3.5 w-3.5 text-emerald-400" />
          </div>
          <div className="text-xl font-black text-emerald-400 mt-1">
            {summary?.assessed_criteria_count ?? 0}
            <span className="text-xs font-normal text-slate-500">
              {" "}
              / {summary?.total_criteria_count ?? 0}
            </span>
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            Submissions & Approvals
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 text-[10px] uppercase font-bold tracking-wider">
            <span>Verified Evidence</span>
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
          </div>
          <div className="text-xl font-black text-white mt-1">
            {summary?.verified_evidences_count ?? 0}
            <span className="text-xs font-normal text-slate-500">
              {" "}
              / {summary?.total_evidences_count ?? 0}
            </span>
          </div>
          <div className="text-[10px] text-emerald-500 mt-0.5">
            Peer-Audited Provenance
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 text-[10px] uppercase font-bold tracking-wider">
            <span>Open Findings</span>
            <AlertCircle className="h-3.5 w-3.5 text-rose-400" />
          </div>
          <div className="text-xl font-black text-rose-400 mt-1">
            {summary?.open_findings_count ??
              findings.filter((f) => f.status !== "CLOSED").length}
          </div>
          <div className="text-[10px] text-rose-500/80 mt-0.5">
            {summary?.critical_findings_count ?? 0} Critical Risk
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-gradient-to-br from-amber-950/40 via-slate-900/90 to-indigo-950/40 border border-amber-800/40">
          <div className="flex items-center justify-between text-amber-300 text-[10px] uppercase font-bold tracking-wider">
            <span>Readiness Score</span>
            <Target className="h-3.5 w-3.5 text-amber-400" />
          </div>
          <div className="text-xl font-black text-amber-400 mt-1">
            {summary?.overall_readiness_avg_pct ?? 0}%
          </div>
          <div className="text-[10px] text-amber-300/80 mt-0.5">
            Weighted Institutional Index
          </div>
        </div>
      </div>

      {/* 3. Navigation Tabs */}
      <div className="flex items-center gap-1.5 border-b border-slate-800 pb-2 overflow-x-auto">
        {[
          { id: "overview", label: "Dashboard & Status", icon: BarChart3 },
          { id: "frameworks", label: "Frameworks & Standards", icon: Award },
          {
            id: "assessment",
            label: "Assessment Workspace",
            icon: ClipboardList,
          },
          { id: "evidence", label: "Evidence Repository", icon: ShieldCheck },
          { id: "kpi", label: "Quality Indicators (KPIs)", icon: TrendingUp },
          { id: "audits", label: "Internal Audits & CAPA", icon: Scale },
          { id: "readiness", label: "Readiness & Gap Analysis", icon: Target },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-lg transition whitespace-nowrap ${
                isActive
                  ? "bg-amber-500/10 text-amber-300 border border-amber-500/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* 4. Tab Contents */}

      {/* TAB 1: OVERVIEW */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: Active Frameworks Summary */}
            <div className="lg:col-span-2 space-y-4">
              <div className="rounded-xl bg-slate-900/60 border border-slate-800 p-5">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-sm font-bold text-white">
                      Statutory Frameworks & Standards
                    </h3>
                    <p className="text-xs text-slate-400">
                      Institutional quality assurance benchmarks in effect
                    </p>
                  </div>
                  <button
                    onClick={() => setActiveTab("frameworks")}
                    className="text-xs font-medium text-amber-400 hover:text-amber-300 flex items-center gap-1"
                  >
                    <span>View all</span>
                    <ChevronRight className="h-3.5 w-3.5" />
                  </button>
                </div>

                <div className="space-y-3">
                  {frameworks.length === 0 ? (
                    <div className="text-center py-8 text-xs text-slate-500">
                      No frameworks configured yet. Click "Seed Standard
                      Templates" above to load NAAC, NBA, and ISO-21001.
                    </div>
                  ) : (
                    frameworks.map((fw) => (
                      <div
                        key={fw.id}
                        className="p-3.5 rounded-lg bg-slate-950/70 border border-slate-800/80 flex items-center justify-between hover:border-slate-700 transition"
                      >
                        <div className="flex items-center gap-3">
                          <div className="h-8 w-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
                            <Award className="h-4 w-4" />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-xs text-white">
                                {fw.name}
                              </span>
                              <span className="px-1.5 py-0.2 text-[9px] font-mono rounded bg-slate-800 text-slate-300">
                                {fw.code}
                              </span>
                            </div>
                            <div className="text-[11px] text-slate-400">
                              Issuing Body: {fw.issuing_body} • Scoring:{" "}
                              {fw.scoring_model} (Max {fw.max_score})
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <span
                            className={`px-2 py-0.5 text-[10px] font-bold rounded-full uppercase ${
                              fw.status === "ACTIVE"
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                            }`}
                          >
                            {fw.status}
                          </span>
                          <span className="text-[10px] text-slate-500 font-mono">
                            v{fw.current_version_number}.0
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Assessment Cycles */}
              <div className="rounded-xl bg-slate-900/60 border border-slate-800 p-5">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-sm font-bold text-white">
                      Active Assessment Cycles
                    </h3>
                    <p className="text-xs text-slate-400">
                      Self-Study Reports (SSR) and cyclical accreditations
                    </p>
                  </div>
                  <button
                    onClick={() => setActiveTab("assessment")}
                    className="text-xs font-medium text-amber-400 hover:text-amber-300 flex items-center gap-1"
                  >
                    <span>Open Workspace</span>
                    <ChevronRight className="h-3.5 w-3.5" />
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {cycles.map((cyc) => (
                    <div
                      key={cyc.id}
                      onClick={() => {
                        setSelectedCycleId(cyc.id);
                        loadCycleAssessments(cyc.id);
                        setActiveTab("assessment");
                      }}
                      className="p-3.5 rounded-lg bg-slate-950/70 border border-slate-800 hover:border-amber-500/40 cursor-pointer transition"
                    >
                      <div className="flex items-center justify-between text-xs font-bold text-white">
                        <span>{cyc.title}</span>
                        <span className="text-[10px] text-amber-400 font-mono">
                          {cyc.academic_year}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-400 mt-1">
                        {cyc.code}
                      </div>
                      <div className="mt-3 flex items-center justify-between text-[11px]">
                        <span className="text-slate-500">
                          Readiness Progress:
                        </span>
                        <span className="font-bold text-amber-400">
                          {cyc.readiness_percentage ?? 0}%
                        </span>
                      </div>
                      <div className="w-full bg-slate-800 h-1.5 rounded-full mt-1.5 overflow-hidden">
                        <div
                          className="bg-amber-500 h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${Math.min(100, cyc.readiness_percentage ?? 0)}%`,
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right: Critical Findings & Alerts */}
            <div className="space-y-4">
              <div className="rounded-xl bg-slate-900/60 border border-slate-800 p-5">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-rose-400" />
                    <span>Compliance Attention Required</span>
                  </h3>
                  <span className="text-[10px] font-mono rounded-full px-2 py-0.5 bg-rose-500/10 text-rose-400 border border-rose-500/20">
                    {
                      findings.filter(
                        (f) =>
                          f.severity === "CRITICAL" || f.severity === "HIGH",
                      ).length
                    }{" "}
                    Urgent
                  </span>
                </div>

                <div className="space-y-2.5">
                  {findings.length === 0 ? (
                    <div className="text-center py-6 text-xs text-slate-500">
                      No open findings recorded. Conformance across internal
                      quality audits is clear.
                    </div>
                  ) : (
                    findings.slice(0, 4).map((f) => (
                      <div
                        key={f.id}
                        className="p-3 rounded-lg bg-slate-950/80 border border-rose-900/30 text-xs space-y-1"
                      >
                        <div className="flex items-center justify-between font-semibold text-rose-200">
                          <span>{f.title}</span>
                          <span className="text-[9px] uppercase px-1.5 py-0.2 rounded bg-rose-950 text-rose-400 border border-rose-800/40">
                            {f.severity}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-400 line-clamp-2">
                          {f.description}
                        </div>
                        <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
                          <span>Code: {f.finding_code}</span>
                          <span className="text-amber-400">
                            Due: {f.target_resolution_date?.split("T")[0]}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* CQI Continuous Improvement Plans */}
              <div className="rounded-xl bg-slate-900/60 border border-slate-800 p-5">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-emerald-400" />
                    <span>Continuous Improvement (CQI)</span>
                  </h3>
                  <span className="text-xs text-slate-500">
                    {cqiPlans.length} Initiatives
                  </span>
                </div>

                <div className="space-y-2.5">
                  {cqiPlans.map((plan) => (
                    <div
                      key={plan.id}
                      className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-xs"
                    >
                      <div className="font-bold text-white">{plan.title}</div>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        {plan.objective}
                      </div>
                      <div className="mt-2 text-[10px] text-emerald-400 flex items-center justify-between">
                        <span>Target: {plan.target_outcome}</span>
                        <span className="px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-300 font-semibold">
                          {plan.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: FRAMEWORKS & STANDARDS */}
      {activeTab === "frameworks" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-white">
                Accreditation Standards & Versioning
              </h2>
              <p className="text-xs text-slate-400">
                Manage criteria trees, scoring models, and publish formal
                revision snapshots
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleSeedTemplates}
                className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white"
              >
                Re-sync System Templates
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {frameworks.map((fw) => (
              <div
                key={fw.id}
                className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 text-[9px] font-mono rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                    {fw.code}
                  </span>
                  <span
                    className={`px-2 py-0.5 text-[9px] font-bold rounded-full uppercase ${
                      fw.status === "ACTIVE"
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                    }`}
                  >
                    {fw.status}
                  </span>
                </div>

                <div>
                  <h4 className="text-sm font-bold text-white">{fw.name}</h4>
                  <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                    {fw.description}
                  </p>
                </div>

                <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-400 space-y-1">
                  <div>
                    Issuing Body:{" "}
                    <span className="text-white font-medium">
                      {fw.issuing_body}
                    </span>
                  </div>
                  <div>
                    Scoring:{" "}
                    <span className="text-white font-medium">
                      {fw.scoring_model} (Max: {fw.max_score})
                    </span>
                  </div>
                  <div>
                    Version:{" "}
                    <span className="text-amber-400 font-mono">
                      v{fw.current_version_number}.0 (Snapshot)
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: ASSESSMENT WORKSPACE */}
      {activeTab === "assessment" && (
        <div className="space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl bg-slate-900/70 border border-slate-800">
            <div className="flex items-center gap-3">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                Assessment Cycle:
              </label>
              <select
                value={selectedCycleId}
                onChange={(e) => handleCycleChange(e.target.value)}
                className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-amber-500"
              >
                {cycles.map((cyc) => (
                  <option key={cyc.id} value={cyc.id}>
                    {cyc.title} ({cyc.academic_year})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="h-3.5 w-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Filter criteria or notes..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8 pr-3 py-1.5 text-xs rounded-lg bg-slate-950 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:border-amber-500"
                />
              </div>

              <select
                value={assessmentStatusFilter}
                onChange={(e) => setAssessmentStatusFilter(e.target.value)}
                className="px-2.5 py-1.5 text-xs rounded-lg bg-slate-950 border border-slate-800 text-slate-300 focus:outline-none"
              >
                <option value="ALL">All Statuses</option>
                <option value="UNASSESSED">UNASSESSED</option>
                <option value="IN_PROGRESS">IN_PROGRESS</option>
                <option value="SUBMITTED">SUBMITTED</option>
                <option value="APPROVED">APPROVED</option>
                <option value="NOT_APPLICABLE">NOT_APPLICABLE</option>
              </select>
            </div>
          </div>

          {/* Criteria Evaluation Cards */}
          <div className="space-y-3">
            {filteredAssessments.length === 0 ? (
              <div className="text-center py-12 rounded-xl bg-slate-900/40 border border-slate-800 text-slate-500 text-xs">
                No assessments found for the selected cycle and filter.
              </div>
            ) : (
              filteredAssessments.map((item, idx) => (
                <div
                  key={item.id}
                  className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-slate-700 transition"
                >
                  <div className="space-y-1.5 flex-1">
                    <div className="flex items-center gap-2.5">
                      <span className="px-2 py-0.5 text-[9px] font-mono rounded bg-slate-800 text-slate-300 font-bold">
                        Criterion #{idx + 1}
                      </span>
                      <span
                        className={`px-2 py-0.5 text-[9px] font-bold rounded-full uppercase ${
                          item.status === "APPROVED"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : item.status === "SUBMITTED"
                              ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                              : item.status === "NOT_APPLICABLE"
                                ? "bg-slate-700 text-slate-400"
                                : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                        }`}
                      >
                        {item.status}
                      </span>
                      <span className="text-[10px] font-mono text-slate-500">
                        Lock v{item.lock_version}
                      </span>
                    </div>

                    <div className="text-xs font-semibold text-white">
                      {item.findings ||
                        item.executive_summary ||
                        "Criterion assessment in progress. Findings pending entry."}
                    </div>

                    {item.not_applicable_reason && (
                      <div className="text-[11px] text-amber-300/90 italic">
                        N/A Justification: {item.not_applicable_reason}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="text-sm font-black text-white">
                        {item.score !== null ? `${item.score}` : "—"}
                      </div>
                      <div className="text-[10px] text-slate-500">
                        Maturity: {item.maturity_level ?? "N/A"}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => openAssessmentEditor(item)}
                        className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition"
                      >
                        Edit Draft
                      </button>

                      {item.status !== "SUBMITTED" &&
                        item.status !== "APPROVED" && (
                          <button
                            onClick={() => handleSubmitAssessment(item)}
                            className="px-3 py-1.5 text-xs font-medium rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition flex items-center gap-1"
                          >
                            <Send className="h-3 w-3" />
                            <span>Submit</span>
                          </button>
                        )}

                      {item.status === "SUBMITTED" && (
                        <button
                          onClick={() => openReviewDialog(item)}
                          className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition flex items-center gap-1"
                        >
                          <ShieldCheck className="h-3 w-3" />
                          <span>Review & Approve</span>
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* TAB 4: EVIDENCE REPOSITORY */}
      {activeTab === "evidence" && (
        <div className="space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl bg-slate-900/70 border border-slate-800">
            <div>
              <h3 className="text-sm font-bold text-white">
                Institutional Evidence Repository
              </h3>
              <p className="text-xs text-slate-400">
                Verifiable document provenance, BoS minutes, accreditation
                artifacts & lifecycle
              </p>
            </div>

            <div className="flex items-center gap-2">
              <select
                value={evidenceCategoryFilter}
                onChange={(e) => setEvidenceCategoryFilter(e.target.value)}
                className="px-2.5 py-1.5 text-xs rounded-lg bg-slate-950 border border-slate-800 text-slate-300 focus:outline-none"
              >
                <option value="ALL">All Categories</option>
                <option value="POLICY_SOP">POLICY_SOP</option>
                <option value="GOVERNANCE_MINUTES">GOVERNANCE_MINUTES</option>
                <option value="EXAM_RECORD">EXAM_RECORD</option>
                <option value="FACULTY_CREDENTIAL">FACULTY_CREDENTIAL</option>
                <option value="INFRASTRUCTURE_AUDIT">
                  INFRASTRUCTURE_AUDIT
                </option>
              </select>

              <select
                value={evidenceStatusFilter}
                onChange={(e) => setEvidenceStatusFilter(e.target.value)}
                className="px-2.5 py-1.5 text-xs rounded-lg bg-slate-950 border border-slate-800 text-slate-300 focus:outline-none"
              >
                <option value="ALL">All Verification Statuses</option>
                <option value="VERIFIED">VERIFIED</option>
                <option value="UNVERIFIED">UNVERIFIED</option>
                <option value="REJECTED">REJECTED</option>
                <option value="EXPIRED">EXPIRED</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {filteredEvidences.map((ev) => (
              <div
                key={ev.id}
                className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2.5"
              >
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 text-[9px] font-mono rounded bg-slate-800 text-amber-300">
                    {ev.evidence_code}
                  </span>
                  <span
                    className={`px-2 py-0.5 text-[9px] font-bold rounded-full uppercase ${
                      ev.verification_status === "VERIFIED"
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        : ev.verification_status === "EXPIRED" || ev.is_expired
                          ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                          : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                    }`}
                  >
                    {ev.is_expired ? "EXPIRED" : ev.verification_status}
                  </span>
                </div>

                <div>
                  <h4 className="text-xs font-bold text-white">{ev.title}</h4>
                  <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-2">
                    {ev.description}
                  </p>
                </div>

                <div className="pt-2 border-t border-slate-800 text-[10px] text-slate-500 flex items-center justify-between">
                  <span>Category: {ev.evidence_category}</span>
                  {ev.valid_until && (
                    <span
                      className={
                        ev.is_expired
                          ? "text-rose-400 font-bold"
                          : "text-slate-400"
                      }
                    >
                      Valid to: {ev.valid_until.split("T")[0]}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 5: QUALITY INDICATORS (KPIS) */}
      {activeTab === "kpi" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-white">
                Quality Indicators & Measurable Outcomes
              </h2>
              <p className="text-xs text-slate-400">
                Institutional KPI tracking, data quality guarantees &
                completeness warnings
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {indicators.map((ind) => (
              <div
                key={ind.id}
                className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 text-[9px] font-mono rounded bg-slate-800 text-slate-300">
                    {ind.code}
                  </span>
                  <span
                    className={`px-2 py-0.5 text-[9px] font-bold rounded-full uppercase ${
                      ind.data_quality_status === "EXCELLENT"
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        : ind.data_quality_status === "WARNING_INCOMPLETE"
                          ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                          : "bg-slate-700 text-slate-300"
                    }`}
                  >
                    {ind.data_quality_status}
                  </span>
                </div>

                <div>
                  <h4 className="text-xs font-bold text-white">{ind.name}</h4>
                  <div className="text-[10px] text-slate-500 uppercase mt-0.5">
                    {ind.category}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 p-2.5 rounded-lg bg-slate-950 text-center">
                  <div>
                    <div className="text-[10px] text-slate-500">
                      Current Value
                    </div>
                    <div className="text-sm font-black text-amber-400 mt-0.5">
                      {ind.current_value !== null
                        ? `${ind.current_value}${ind.unit_of_measurement}`
                        : "Pending"}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-500">Target</div>
                    <div className="text-sm font-bold text-white mt-0.5">
                      {ind.target_value}
                      {ind.unit_of_measurement}
                    </div>
                  </div>
                </div>

                {ind.data_quality_notes && (
                  <div className="text-[10px] text-amber-300/80 p-2 rounded bg-amber-950/30 border border-amber-800/40">
                    {ind.data_quality_notes}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 6: INTERNAL AUDITS & CAPA */}
      {activeTab === "audits" && (
        <div className="space-y-6">
          {/* Internal Audits List */}
          <div className="rounded-xl bg-slate-900/60 border border-slate-800 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white">
                  Internal Quality Audits
                </h3>
                <p className="text-xs text-slate-400">
                  Scheduled audits with checklist conformance and immutable
                  final reports
                </p>
              </div>
            </div>

            <div className="space-y-3">
              {audits.map((aud) => (
                <div
                  key={aud.id}
                  className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-xs text-white">
                        {aud.title}
                      </span>
                      <span className="px-1.5 py-0.2 text-[9px] font-mono rounded bg-slate-800 text-slate-300">
                        {aud.code}
                      </span>
                      {aud.is_immutable && (
                        <span className="flex items-center gap-1 px-2 py-0.5 text-[9px] font-bold rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800/40">
                          <Lock className="h-2.5 w-2.5" />
                          <span>FINALIZED & IMMUTABLE</span>
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] text-slate-400">
                      Type: {aud.audit_type} • Scheduled:{" "}
                      {aud.scheduled_start_date?.split("T")[0]}
                    </div>
                    {aud.summary_findings && (
                      <div className="text-[11px] text-slate-300 pt-1">
                        Findings Summary: {aud.summary_findings}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    {!aud.is_immutable && (
                      <button
                        onClick={() => {
                          setFinalizeAuditId(aud.id);
                          setFinalizeFindings("");
                          setFinalizeRecommendations("");
                          setIsFinalizeModalOpen(true);
                        }}
                        className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-amber-600 hover:bg-amber-500 text-white transition flex items-center gap-1.5"
                      >
                        <Lock className="h-3 w-3" />
                        <span>Finalize Report</span>
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Corrective Actions (CAPA) */}
          <div className="rounded-xl bg-slate-900/60 border border-slate-800 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white">
                  Corrective & Preventive Actions (CAPA)
                </h3>
                <p className="text-xs text-slate-400">
                  Accountable root-cause resolution with separation-of-duties
                  verification
                </p>
              </div>
            </div>

            <div className="space-y-3">
              {findings.map((finding) => (
                <div
                  key={finding.id}
                  className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-white">
                      {finding.title}
                    </span>
                    <span className="text-[10px] uppercase font-bold text-rose-400 bg-rose-950 px-2 py-0.5 rounded border border-rose-800/40">
                      {finding.severity}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400">
                    {finding.description}
                  </div>
                  {finding.root_cause_analysis && (
                    <div className="text-[11px] text-amber-300/90 italic">
                      Root Cause: {finding.root_cause_analysis}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 7: READINESS & GAP ANALYSIS */}
      {activeTab === "readiness" && (
        <div className="space-y-6">
          <div className="rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 p-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-2">
              <span className="px-2.5 py-0.5 text-[10px] font-bold rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30 uppercase">
                {readinessSnapshot?.readiness_category ||
                  "ASSESSMENT_IN_PROGRESS"}
              </span>
              <h2 className="text-xl font-black text-white">
                Accreditation Readiness & SSR Preparedness Index
              </h2>
              <p className="text-xs text-slate-400 max-w-xl">
                Multi-dimensional readiness scoring calculated from evaluated
                criteria completion, verified evidence ratio, internal audit
                compliance, and critical findings penalty.
              </p>
            </div>

            <div className="text-center p-6 rounded-2xl bg-slate-950/80 border border-amber-500/30 shrink-0">
              <div className="text-3xl font-black text-amber-400">
                {readinessSnapshot?.overall_readiness_score ??
                  summary?.overall_readiness_avg_pct ??
                  0}
                %
              </div>
              <div className="text-[10px] uppercase font-bold text-slate-400 mt-1">
                Readiness Index
              </div>
            </div>
          </div>

          {/* Gap Summaries */}
          <div className="rounded-xl bg-slate-900/60 border border-slate-800 p-5 space-y-3">
            <h3 className="text-sm font-bold text-white">
              Identified Compliance Gaps
            </h3>
            {readinessSnapshot?.gap_summary_json &&
            readinessSnapshot.gap_summary_json.length > 0 ? (
              <div className="space-y-2">
                {readinessSnapshot.gap_summary_json.map(
                  (gap: any, i: number) => (
                    <div
                      key={i}
                      className="p-3 rounded-lg bg-slate-950 border border-amber-900/40 text-xs flex items-center justify-between"
                    >
                      <div>
                        <div className="font-semibold text-white">
                          {gap.description || gap.gap_title}
                        </div>
                        <div className="text-[10px] text-slate-400">
                          Criterion: {gap.criterion_code || "General"}
                        </div>
                      </div>
                      <span className="px-2 py-0.5 text-[9px] font-bold rounded uppercase bg-amber-950 text-amber-300">
                        {gap.severity || "MEDIUM"}
                      </span>
                    </div>
                  ),
                )}
              </div>
            ) : (
              <div className="text-xs text-slate-500 py-6 text-center">
                No high-risk compliance gaps detected for this cycle.
              </div>
            )}
          </div>
        </div>
      )}

      {/* MODAL: ASSESSMENT DRAFT EDITOR */}
      {isAssessmentModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-sm font-bold text-white">
                Criterion Evaluation & Rubrics Draft
              </h3>
              <button
                onClick={() => setIsAssessmentModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-medium text-slate-400">
                    Score
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={editScore}
                    onChange={(e) =>
                      setEditScore(
                        e.target.value === "" ? "" : Number(e.target.value),
                      )
                    }
                    className="w-full px-3 py-2 text-xs rounded-lg bg-slate-950 border border-slate-800 text-white mt-1 focus:outline-none focus:border-amber-500"
                    placeholder="Enter numeric score"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-medium text-slate-400">
                    Maturity Level
                  </label>
                  <select
                    value={editMaturity}
                    onChange={(e) => setEditMaturity(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-lg bg-slate-950 border border-slate-800 text-white mt-1 focus:outline-none"
                  >
                    <option value={AccreditationMaturityLevel.LEVEL_1_INITIAL}>
                      Level 1: Initial
                    </option>
                    <option
                      value={AccreditationMaturityLevel.LEVEL_2_DEVELOPING}
                    >
                      Level 2: Developing
                    </option>
                    <option value={AccreditationMaturityLevel.LEVEL_3_DEFINED}>
                      Level 3: Defined
                    </option>
                    <option value={AccreditationMaturityLevel.LEVEL_4_MANAGED}>
                      Level 4: Managed
                    </option>
                    <option
                      value={AccreditationMaturityLevel.LEVEL_5_OPTIMIZING}
                    >
                      Level 5: Optimizing
                    </option>
                  </select>
                </div>
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="na_check"
                  checked={isNotApplicable}
                  onChange={(e) => setIsNotApplicable(e.target.checked)}
                  className="rounded bg-slate-950 border-slate-800 text-amber-500 focus:ring-0"
                />
                <label
                  htmlFor="na_check"
                  className="text-xs text-slate-300 font-medium"
                >
                  Mark Criterion as Not Applicable (Statutory Justification
                  Required)
                </label>
              </div>

              {isNotApplicable && (
                <div>
                  <label className="text-[11px] font-medium text-amber-400">
                    Not Applicable Justification
                  </label>
                  <textarea
                    rows={2}
                    value={notApplicableReason}
                    onChange={(e) => setNotApplicableReason(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-lg bg-slate-950 border border-amber-800/60 text-white mt-1 focus:outline-none"
                    placeholder="Provide explicit institutional exemption ground..."
                  />
                </div>
              )}

              <div>
                <label className="text-[11px] font-medium text-slate-400">
                  Executive Summary
                </label>
                <textarea
                  rows={2}
                  value={editSummary}
                  onChange={(e) => setEditSummary(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-lg bg-slate-950 border border-slate-800 text-white mt-1 focus:outline-none"
                  placeholder="Summary of criterion evaluation..."
                />
              </div>

              <div>
                <label className="text-[11px] font-medium text-slate-400">
                  Findings & Evidence Conformance
                </label>
                <textarea
                  rows={2}
                  value={editFindings}
                  onChange={(e) => setEditFindings(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-lg bg-slate-950 border border-slate-800 text-white mt-1 focus:outline-none"
                  placeholder="Details of audit findings..."
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-medium text-slate-400">
                    Institutional Strengths
                  </label>
                  <textarea
                    rows={2}
                    value={editStrengths}
                    onChange={(e) => setEditStrengths(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-lg bg-slate-950 border border-slate-800 text-white mt-1 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-medium text-slate-400">
                    Areas for Improvement / Weaknesses
                  </label>
                  <textarea
                    rows={2}
                    value={editWeaknesses}
                    onChange={(e) => setEditWeaknesses(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-lg bg-slate-950 border border-slate-800 text-white mt-1 focus:outline-none"
                  />
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-800">
              <button
                onClick={() => setIsAssessmentModalOpen(false)}
                className="px-3.5 py-2 text-xs text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveDraft}
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-amber-600 hover:bg-amber-500 text-white"
              >
                Save Evaluation Draft
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: SEPARATION OF DUTIES INDEPENDENT REVIEW */}
      {isReviewModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                <ShieldCheck className="h-4 w-4 text-emerald-400" />
                <span>Independent Peer Review</span>
              </h3>
              <button
                onClick={() => setIsReviewModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-200">
              Quality Assurance policy strictly enforces Separation of Duties:
              the primary assessor cannot review or approve their own assessment
              submission.
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-[11px] font-medium text-slate-400">
                  Review Decision
                </label>
                <select
                  value={reviewDecision}
                  onChange={(e) => setReviewDecision(e.target.value as any)}
                  className="w-full px-3 py-2 text-xs rounded-lg bg-slate-950 border border-slate-800 text-white mt-1 focus:outline-none"
                >
                  <option value="APPROVED">APPROVED</option>
                  <option value="CHANGES_REQUESTED">CHANGES_REQUESTED</option>
                </select>
              </div>

              <div>
                <label className="text-[11px] font-medium text-slate-400">
                  Adjusted Score (Optional)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={adjustedScore}
                  onChange={(e) =>
                    setAdjustedScore(
                      e.target.value === "" ? "" : Number(e.target.value),
                    )
                  }
                  className="w-full px-3 py-2 text-xs rounded-lg bg-slate-950 border border-slate-800 text-white mt-1 focus:outline-none"
                  placeholder="Leave blank to maintain assessor score"
                />
              </div>

              <div>
                <label className="text-[11px] font-medium text-slate-400">
                  Reviewer Observations & Justification
                </label>
                <textarea
                  rows={3}
                  value={reviewComments}
                  onChange={(e) => setReviewComments(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-lg bg-slate-950 border border-slate-800 text-white mt-1 focus:outline-none"
                  placeholder="Record independent evaluation remarks..."
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
              <button
                onClick={() => setIsReviewModalOpen(false)}
                className="px-3.5 py-2 text-xs text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleReviewDecision}
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white"
              >
                Submit Review
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: FINALIZE AUDIT REPORT */}
      {isFinalizeModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                <Lock className="h-4 w-4 text-amber-400" />
                <span>Finalize Internal Audit Report</span>
              </h3>
              <button
                onClick={() => setIsFinalizeModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-[11px] text-rose-200">
              Finalization locks the audit permanently into an immutable record.
              No further checklist mutations will be permitted.
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-[11px] font-medium text-slate-400">
                  Summary Findings
                </label>
                <textarea
                  rows={3}
                  value={finalizeFindings}
                  onChange={(e) => setFinalizeFindings(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-lg bg-slate-950 border border-slate-800 text-white mt-1 focus:outline-none"
                  placeholder="Executive summary of audit findings..."
                />
              </div>

              <div>
                <label className="text-[11px] font-medium text-slate-400">
                  Institutional Recommendations
                </label>
                <textarea
                  rows={3}
                  value={finalizeRecommendations}
                  onChange={(e) => setFinalizeRecommendations(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-lg bg-slate-950 border border-slate-800 text-white mt-1 focus:outline-none"
                  placeholder="Key corrective priorities and recommendations..."
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
              <button
                onClick={() => setIsFinalizeModalOpen(false)}
                className="px-3.5 py-2 text-xs text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleFinalizeAudit}
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-amber-600 hover:bg-amber-500 text-white"
              >
                Lock & Finalize Audit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
