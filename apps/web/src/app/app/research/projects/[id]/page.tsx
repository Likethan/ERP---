"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { ResearchNav } from "@/components/research/research-nav";
import { ResearchService } from "@/services/research.service";
import { validateProjectTransition } from "@/services/research-calculator";
import {
  ResearchProjectDetailResponse,
  ResearchProjectStatus,
} from "@/types/research";
import {
  ArrowLeft,
  Calendar,
  DollarSign,
  Users,
  ShieldCheck,
  ShieldAlert,
  FileCheck2,
  Lightbulb,
  AlertTriangle,
  RefreshCw,
  Plus,
  CheckCircle2,
  Lock,
  ExternalLink,
  ChevronRight,
  TrendingUp,
} from "lucide-react";

export default function ProjectDetailWorkspacePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const projectId = resolvedParams.id;

  const [details, setDetails] = useState<ResearchProjectDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<
    "overview" | "team" | "milestones" | "budget" | "ethics" | "outputs" | "risks"
  >("overview");
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // Status transition state
  const [isTransitionModalOpen, setIsTransitionModalOpen] = useState(false);
  const [targetStatus, setTargetStatus] = useState<string>("ACTIVE");
  const [transitionReason, setTransitionReason] = useState("");

  // Add Member Modal
  const [isAddMemberModalOpen, setIsAddMemberModalOpen] = useState(false);
  const [memberForm, setMemberForm] = useState({
    role: "CO_INVESTIGATOR",
    external_collaborator_name: "",
    external_institution: "",
    contribution_description: "",
    start_date: new Date().toISOString().split("T")[0],
    access_scope: "FULL_READ_WRITE",
    workload_percentage: 20,
  });

  // Add Milestone Modal
  const [isAddMilestoneModalOpen, setIsAddMilestoneModalOpen] = useState(false);
  const [milestoneForm, setMilestoneForm] = useState({
    title: "",
    description: "",
    planned_date: new Date(Date.now() + 60 * 86400000).toISOString().split("T")[0],
    acceptance_criteria: "",
    is_mandatory_for_closure: true,
  });

  const loadDetails = async () => {
    setLoading(true);
    try {
      const data = await ResearchService.getProjectDetails(projectId);
      setDetails(data);
    } catch (err: any) {
      setFeedback({ type: "error", message: err.message || "Failed to load project details." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDetails();
  }, [projectId]);

  const handleTransition = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!details) return;

    // Validate transition locally
    const validation = validateProjectTransition(
      details.project.status,
      targetStatus,
      details.milestones,
      details.ethics_approvals,
      details.project.requires_ethics_approval
    );

    if (!validation.allowed) {
      setFeedback({ type: "error", message: validation.reason || "Transition blocked by policy rules." });
      return;
    }

    try {
      await ResearchService.transitionProjectStatus(projectId, targetStatus, transitionReason);
      setFeedback({ type: "success", message: `Project transitioned to ${targetStatus} successfully.` });
      setIsTransitionModalOpen(false);
      setTransitionReason("");
      loadDetails();
    } catch (err: any) {
      setFeedback({ type: "error", message: err.message || "Failed to execute transition." });
    }
  };

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await ResearchService.addTeamMember(projectId, memberForm as any);
      setFeedback({ type: "success", message: "Team member attached to project roster." });
      setIsAddMemberModalOpen(false);
      loadDetails();
    } catch (err: any) {
      setFeedback({ type: "error", message: err.message || "Failed to add team member." });
    }
  };

  const handleAddMilestone = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!milestoneForm.title.trim()) return;
    try {
      await ResearchService.createMilestone({
        project_id: projectId,
        ...milestoneForm,
      } as any);
      setFeedback({ type: "success", message: "Milestone registered on project roadmap." });
      setIsAddMilestoneModalOpen(false);
      loadDetails();
    } catch (err: any) {
      setFeedback({ type: "error", message: err.message || "Failed to create milestone." });
    }
  };

  const handleVerifyMilestone = async (milestoneId: string, decision: string) => {
    const notes = prompt("Enter independent verification notes:");
    if (!notes) return;
    try {
      await ResearchService.verifyMilestone(milestoneId, decision, notes);
      setFeedback({ type: "success", message: `Milestone verified as ${decision}.` });
      loadDetails();
    } catch (err: any) {
      setFeedback({ type: "error", message: err.message || "Failed to verify milestone." });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
        <ResearchNav />
        <div className="flex-1 flex items-center justify-center p-12">
          <RefreshCw className="h-8 w-8 animate-spin text-emerald-400" />
        </div>
      </div>
    );
  }

  if (!details) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
        <ResearchNav />
        <div className="flex-1 flex flex-col items-center justify-center p-12 space-y-4">
          <AlertTriangle className="h-10 w-10 text-rose-400" />
          <h2 className="text-xl font-bold">Research Project Not Found</h2>
          <Link href="/app/research/projects" className="text-emerald-400 underline text-sm">
            ← Return to Portfolio
          </Link>
        </div>
      </div>
    );
  }

  const { project, health, team_members, milestones, ethics_approvals, budget_plans, grant_awards, outputs, risks } =
    details;

  const healthColor =
    health.health_status === "HEALTHY"
      ? "text-emerald-400 border-emerald-500/30 bg-emerald-500/10"
      : health.health_status === "NEEDS_ATTENTION"
      ? "text-amber-400 border-amber-500/30 bg-amber-500/10"
      : "text-rose-400 border-rose-500/30 bg-rose-500/10";

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <ResearchNav />

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
        {/* Back Link & Title Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div className="space-y-1">
            <Link
              href="/app/research/projects"
              className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-emerald-400 transition-colors"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Back to Portfolio
            </Link>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl font-bold tracking-tight text-white">{project.title}</h1>
              <span className="font-mono text-xs px-2.5 py-0.5 rounded bg-slate-800 text-slate-300 font-semibold">
                {project.project_code}
              </span>
              <span className="text-xs px-2.5 py-0.5 rounded-full font-semibold border bg-slate-800 text-emerald-400 border-slate-700">
                {project.status}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Domain: <span className="text-slate-300">{project.research_domain}</span> | Category:{" "}
              <span className="text-slate-300">{project.research_category}</span> | Timeline:{" "}
              <span className="text-slate-300 font-mono">
                {project.start_date} → {project.planned_end_date}
              </span>
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsTransitionModalOpen(true)}
              className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
            >
              Change Status
            </button>
            <button
              onClick={loadDetails}
              className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Feedback Alert */}
        {feedback && (
          <div
            className={`p-4 rounded-xl border text-sm flex items-center justify-between ${
              feedback.type === "success"
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                : "bg-rose-500/10 border-rose-500/30 text-rose-300"
            }`}
          >
            <span>{feedback.message}</span>
            <button onClick={() => setFeedback(null)} className="text-xs underline ml-4">
              Dismiss
            </button>
          </div>
        )}

        {/* Explainable Project Health Diagnosis Card */}
        <div className={`p-5 rounded-2xl border backdrop-blur-sm ${healthColor} space-y-3`}>
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="text-3xl font-black font-mono tracking-tight">{health.health_score}</span>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-white">
                    Project Health: {health.health_status}
                  </h3>
                  <span className="text-[10px] px-2 py-0.2 rounded-full bg-slate-900/60 font-mono text-slate-300">
                    Rule-Based Deterministic Diagnosis
                  </span>
                </div>
                <p className="text-xs text-slate-300 mt-0.5">
                  Overdue milestones: <strong className="font-mono">{health.overdue_milestones_count}</strong> | Blocked:{" "}
                  <strong className="font-mono">{health.blocked_milestones_count}</strong> | Ethics Compliant:{" "}
                  <strong className="font-mono">{health.ethics_compliant ? "YES" : "NO (" + health.ethics_status + ")"}</strong> | High Risks:{" "}
                  <strong className="font-mono">{health.high_critical_risks_count}</strong>
                </p>
              </div>
            </div>

            <div className="text-right">
              <span className="text-xs text-slate-300">Authoritative Budget Burn Rate:</span>
              <div className="text-lg font-bold font-mono text-white">
                {health.financial_burn_rate_percent}%
              </div>
            </div>
          </div>

          <div className="border-t border-slate-800/40 pt-3 space-y-1">
            <span className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider">
              Diagnostic Reasons & Root Causes:
            </span>
            <ul className="text-xs space-y-1 text-slate-200">
              {health.diagnostic_reasons.map((reason, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-emerald-400 mt-0.5">•</span>
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Workspace Tab Navigation */}
        <div className="flex items-center gap-2 border-b border-slate-800 overflow-x-auto no-scrollbar pb-1">
          {[
            { id: "overview", label: "Overview", icon: <Calendar className="h-4 w-4" /> },
            { id: "team", label: `Team & Workload (${team_members.length})`, icon: <Users className="h-4 w-4" /> },
            { id: "milestones", label: `Milestones & Deliverables (${milestones.length})`, icon: <FileCheck2 className="h-4 w-4" /> },
            { id: "budget", label: "Budget & Reconciled Finances", icon: <DollarSign className="h-4 w-4" /> },
            { id: "ethics", label: `Ethics & Compliance (${ethics_approvals.length})`, icon: <ShieldCheck className="h-4 w-4" /> },
            { id: "outputs", label: `Outputs & IP (${outputs.length})`, icon: <Lightbulb className="h-4 w-4" /> },
            { id: "risks", label: `Risk Register (${risks.length})`, icon: <AlertTriangle className="h-4 w-4" /> },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-lg transition-all ${
                activeTab === tab.id
                  ? "bg-slate-800 text-emerald-400 border border-slate-700 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === "overview" && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-2 space-y-6">
              <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                <h3 className="text-base font-bold text-white">Abstract & Technical Scope</h3>
                <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">{project.abstract}</p>
              </div>

              <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                <h3 className="text-base font-bold text-white">Project Deliverables & Summary</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                    <span className="text-xl font-bold font-mono text-emerald-400">{milestones.length}</span>
                    <p className="text-[11px] text-slate-400 mt-1">Milestones</p>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                    <span className="text-xl font-bold font-mono text-blue-400">{team_members.length}</span>
                    <p className="text-[11px] text-slate-400 mt-1">Investigators</p>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                    <span className="text-xl font-bold font-mono text-purple-400">{outputs.length}</span>
                    <p className="text-[11px] text-slate-400 mt-1">Publications</p>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                    <span className="text-xl font-bold font-mono text-amber-400">{risks.length}</span>
                    <p className="text-[11px] text-slate-400 mt-1">Logged Risks</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Institutional Metadata</h3>
                <div className="space-y-3 text-xs">
                  <div className="flex justify-between border-b border-slate-800/60 pb-2">
                    <span className="text-slate-400">Total Budget:</span>
                    <span className="font-mono font-semibold text-emerald-400">
                      {project.currency} {Number(project.total_budget_allocated).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between border-b border-slate-800/60 pb-2">
                    <span className="text-slate-400">Ethics Approval:</span>
                    <span className={project.requires_ethics_approval ? "text-amber-400 font-semibold" : "text-slate-400"}>
                      {project.requires_ethics_approval ? "Mandatory" : "Not Required"}
                    </span>
                  </div>
                  <div className="flex justify-between border-b border-slate-800/60 pb-2">
                    <span className="text-slate-400">International:</span>
                    <span className="text-slate-300 font-medium">{project.is_international ? "Yes" : "Domestic"}</span>
                  </div>
                  <div className="flex justify-between border-b border-slate-800/60 pb-2">
                    <span className="text-slate-400">Created At:</span>
                    <span className="text-slate-300 font-mono text-[11px]">{project.created_at?.split("T")[0]}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "team" && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-base font-bold text-white">Assigned Research Investigators & Team Roster</h3>
              <button
                onClick={() => setIsAddMemberModalOpen(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white"
              >
                <Plus className="h-3.5 w-3.5" />
                Add Participant
              </button>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 text-slate-400 uppercase tracking-wider text-[10px] border-b border-slate-800">
                  <tr>
                    <th className="p-4">Participant</th>
                    <th className="p-4">Project Role</th>
                    <th className="p-4">Institution / Affiliation</th>
                    <th className="p-4">Workload Allocation</th>
                    <th className="p-4">Access Scope</th>
                    <th className="p-4">Period</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  {team_members.map((tm) => (
                    <tr key={tm.id} className="hover:bg-slate-800/30">
                      <td className="p-4">
                        <div className="font-semibold text-white">
                          {tm.user_name || tm.external_collaborator_name || "Campus Scholar"}
                        </div>
                        <div className="text-[11px] text-slate-500">{tm.user_email || "Authorized Member"}</div>
                      </td>
                      <td className="p-4 font-medium text-emerald-400">{tm.role}</td>
                      <td className="p-4 text-slate-400">{tm.external_institution || "Host Institution"}</td>
                      <td className="p-4 font-mono font-semibold">{tm.workload_percentage || 20}%</td>
                      <td className="p-4">
                        <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                          {tm.access_scope}
                        </span>
                      </td>
                      <td className="p-4 font-mono text-[11px] text-slate-400">
                        {tm.start_date} → {tm.end_date || "Present"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === "milestones" && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-base font-bold text-white">Execution Milestones & Verified Deliverables</h3>
              <button
                onClick={() => setIsAddMilestoneModalOpen(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white"
              >
                <Plus className="h-3.5 w-3.5" />
                Add Milestone
              </button>
            </div>

            <div className="space-y-3">
              {milestones.map((ms) => (
                <div
                  key={ms.id}
                  className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                        {ms.milestone_code}
                      </span>
                      <h4 className="text-sm font-semibold text-white">{ms.title}</h4>
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded-full border ${
                          ms.status === "ACCEPTED"
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                            : ms.status === "BLOCKED"
                            ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                            : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                        }`}
                      >
                        {ms.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400">{ms.description}</p>
                    <div className="text-[11px] text-slate-500 space-x-3">
                      <span>Planned Due: <strong className="font-mono text-slate-300">{ms.planned_completion_date}</strong></span>
                      <span>Acceptance Criteria: <strong className="text-slate-300">{ms.acceptance_criteria}</strong></span>
                      {ms.is_mandatory_for_closure && (
                        <span className="text-amber-400 font-semibold">• Mandatory for Project Closure</span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {ms.status !== "ACCEPTED" && (
                      <button
                        onClick={() => handleVerifyMilestone(ms.id, "ACCEPTED")}
                        className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white shadow-sm"
                      >
                        Verify & Accept
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === "budget" && (
          <div className="space-y-6">
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-emerald-400" />
                Authoritative Project Financial Reconciliation (Finance Source of Truth)
              </h3>
              <p className="text-xs text-slate-400">
                Expenditure numbers are synchronized directly with institutional general ledger disbursements. Research screens do not create a parallel accounting ledger.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-xs text-slate-500 uppercase">Approved Budget</span>
                  <div className="text-xl font-bold font-mono text-white mt-1">
                    {project.currency} {Number(project.total_budget_allocated).toLocaleString()}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-xs text-slate-500 uppercase">Committed</span>
                  <div className="text-xl font-bold font-mono text-blue-400 mt-1">
                    {project.currency}{" "}
                    {grant_awards
                      .reduce((s, a) => s + Number(a.committed_expenditure || 0), 0)
                      .toLocaleString()}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-xs text-slate-500 uppercase">Disbursed / Actual</span>
                  <div className="text-xl font-bold font-mono text-purple-400 mt-1">
                    {project.currency}{" "}
                    {grant_awards
                      .reduce((s, a) => s + Number(a.actual_expenditure || 0), 0)
                      .toLocaleString()}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <span className="text-xs text-slate-500 uppercase">Remaining Balance</span>
                  <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
                    {project.currency}{" "}
                    {Math.max(
                      0,
                      Number(project.total_budget_allocated) -
                        grant_awards.reduce((s, a) => s + Number(a.actual_expenditure || 0), 0)
                    ).toLocaleString()}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "ethics" && (
          <div className="space-y-4">
            <h3 className="text-base font-bold text-white">Institutional Review Board (IRB / IACUC / IBC) Protocols</h3>
            {ethics_approvals.length === 0 ? (
              <p className="text-xs text-slate-500">No ethics protocols currently recorded for this project.</p>
            ) : (
              ethics_approvals.map((eth) => (
                <div key={eth.id} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-semibold">
                      {eth.approval_code}
                    </span>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full border bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
                      {eth.status}
                    </span>
                  </div>
                  <h4 className="text-sm font-semibold text-white">{eth.review_committee_name}</h4>
                  <p className="text-xs text-slate-400">Policy Reference: {eth.governing_policy_reference}</p>
                  <p className="text-xs text-slate-400">Validity: {eth.submission_date} → Expiry: {eth.expiry_date || "Indefinite"}</p>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === "outputs" && (
          <div className="space-y-4">
            <h3 className="text-base font-bold text-white">Academic Outputs, Publications & Patents</h3>
            {outputs.length === 0 ? (
              <p className="text-xs text-slate-500">No academic publications attached to this project.</p>
            ) : (
              outputs.map((out) => (
                <div key={out.id} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                  <h4 className="text-sm font-semibold text-white">{out.title}</h4>
                  <p className="text-xs text-slate-400">Authors: {out.authors_string}</p>
                  <p className="text-xs text-slate-400">Venue: {out.publication_or_venue_name} | DOI: {out.doi || "Pending"}</p>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === "risks" && (
          <div className="space-y-4">
            <h3 className="text-base font-bold text-white">Project Risk & Dependency Register</h3>
            {risks.length === 0 ? (
              <p className="text-xs text-slate-500">No active risks registered on this project.</p>
            ) : (
              risks.map((r) => (
                <div key={r.id} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs text-slate-400">{r.risk_code}</span>
                    <span className="text-xs font-bold text-rose-400">{r.calculated_risk_level}</span>
                  </div>
                  <h4 className="text-sm font-semibold text-white">{r.title}</h4>
                  <p className="text-xs text-slate-400">Mitigation: {r.mitigation_plan}</p>
                </div>
              ))
            )}
          </div>
        )}
      </main>

      {/* Transition Modal */}
      {isTransitionModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Change Project Lifecycle Status</h3>
            <form onSubmit={handleTransition} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 font-medium mb-1">Target Status</label>
                <select
                  value={targetStatus}
                  onChange={(e) => setTargetStatus(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                >
                  <option value="PROPOSAL">PROPOSAL</option>
                  <option value="UNDER_REVIEW">UNDER_REVIEW</option>
                  <option value="APPROVED">APPROVED</option>
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="ON_HOLD">ON_HOLD</option>
                  <option value="COMPLETED">COMPLETED</option>
                  <option value="CLOSED">CLOSED</option>
                  <option value="CANCELLED">CANCELLED</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 font-medium mb-1">Reason / Justification</label>
                <textarea
                  rows={3}
                  value={transitionReason}
                  onChange={(e) => setTransitionReason(e.target.value)}
                  placeholder="Record formal justification for institutional audit log..."
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                  required
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsTransitionModalOpen(false)}
                  className="px-3 py-1.5 rounded-lg text-slate-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 font-semibold text-white"
                >
                  Apply Transition
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Member Modal */}
      {isAddMemberModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Add Team Member to Project</h3>
            <form onSubmit={handleAddMember} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Role</label>
                <select
                  value={memberForm.role}
                  onChange={(e) => setMemberForm({ ...memberForm, role: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                >
                  <option value="CO_INVESTIGATOR">Co-Investigator</option>
                  <option value="POSTDOC_RESEARCHER">Postdoc Researcher</option>
                  <option value="RESEARCH_SCHOLAR">Research Scholar</option>
                  <option value="STUDENT_RESEARCHER">Student Researcher</option>
                  <option value="INDUSTRY_COLLABORATOR">Industry Collaborator</option>
                </select>
              </div>
              <div>
                <label className="block text-slate-400 mb-1">External Collaborator Name (if applicable)</label>
                <input
                  type="text"
                  value={memberForm.external_collaborator_name}
                  onChange={(e) => setMemberForm({ ...memberForm, external_collaborator_name: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Institution</label>
                <input
                  type="text"
                  value={memberForm.external_institution}
                  onChange={(e) => setMemberForm({ ...memberForm, external_institution: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Workload Allocation %</label>
                <input
                  type="number"
                  value={memberForm.workload_percentage}
                  onChange={(e) => setMemberForm({ ...memberForm, workload_percentage: Number(e.target.value) })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsAddMemberModalOpen(false)}
                  className="px-3 py-1.5 rounded-lg text-slate-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 font-semibold text-white"
                >
                  Add Member
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Milestone Modal */}
      {isAddMilestoneModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Add Project Milestone</h3>
            <form onSubmit={handleAddMilestone} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Milestone Title</label>
                <input
                  type="text"
                  value={milestoneForm.title}
                  onChange={(e) => setMilestoneForm({ ...milestoneForm, title: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                  required
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Description</label>
                <textarea
                  rows={2}
                  value={milestoneForm.description}
                  onChange={(e) => setMilestoneForm({ ...milestoneForm, description: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Planned Completion Date</label>
                <input
                  type="date"
                  value={milestoneForm.planned_date}
                  onChange={(e) => setMilestoneForm({ ...milestoneForm, planned_date: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                  required
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Acceptance Criteria</label>
                <input
                  type="text"
                  value={milestoneForm.acceptance_criteria}
                  onChange={(e) => setMilestoneForm({ ...milestoneForm, acceptance_criteria: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200"
                  required
                />
              </div>
              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="closure_mand"
                  checked={milestoneForm.is_mandatory_for_closure}
                  onChange={(e) =>
                    setMilestoneForm({ ...milestoneForm, is_mandatory_for_closure: e.target.checked })
                  }
                  className="rounded bg-slate-950 border-slate-800 text-emerald-600"
                />
                <label htmlFor="closure_mand" className="text-slate-300">
                  Mandatory for Project Closure
                </label>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsAddMilestoneModalOpen(false)}
                  className="px-3 py-1.5 rounded-lg text-slate-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 font-semibold text-white"
                >
                  Save Milestone
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
