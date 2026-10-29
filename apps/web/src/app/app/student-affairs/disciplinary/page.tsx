"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { studentAffairsService } from "@/services/student-affairs.service";
import { StudentAffairsCalculator } from "@/services/student-affairs-calculator";
import {
  GrievanceCaseModel,
  DisciplinaryProceedingModel,
  SAFindingStatus,
  SASanctionType,
  SADisciplinaryStage,
} from "@/types/student-affairs";
import { StudentAffairsNav } from "@/components/student-affairs/student-affairs-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Gavel,
  ShieldCheck,
  Scale,
  CheckCircle2,
  Calendar,
  AlertCircle,
  FileCheck2,
  Clock,
} from "lucide-react";

function DisciplinaryWorkspaceContent() {
  const searchParams = useSearchParams();
  const preselectedCaseId = searchParams?.get("caseId");

  const [cases, setCases] = useState<GrievanceCaseModel[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>(preselectedCaseId || "");
  const [findingStatus, setFindingStatus] = useState<SAFindingStatus>(SAFindingStatus.SUBSTANTIATED);
  const [findingsSummary, setFindingsSummary] = useState("");
  const [sanctionType, setSanctionType] = useState<SASanctionType>(SASanctionType.FORMAL_WARNING);
  const [sanctionDetails, setSanctionDetails] = useState("");
  const [decisionMakerId, setDecisionMakerId] = useState("usr-dean-001");
  const [appealDays, setAppealDays] = useState(14);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");

  useEffect(() => {
    async function load() {
      const allCases = await studentAffairsService.getCases();
      // Filter for disciplinary cases or all if none
      const dispCases = allCases.filter(
        (c) => c.case_type === "DISCIPLINARY" || c.disciplinary_proceeding
      );
      setCases(dispCases.length > 0 ? dispCases : allCases);
      if (preselectedCaseId) {
        setSelectedCaseId(preselectedCaseId);
      } else if (dispCases.length > 0) {
        setSelectedCaseId(dispCases[0].id);
      }
    }
    load();
  }, [preselectedCaseId]);

  const activeCase = cases.find((c) => c.id === selectedCaseId);
  const proceeding = activeCase?.disciplinary_proceeding;
  const milestones = StudentAffairsCalculator.evaluateProceduralMilestones(proceeding);

  async function handleRecordFindings(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedCaseId || !findingsSummary) {
      alert("Please provide the findings summary.");
      return;
    }
    setLoading(true);
    try {
      await studentAffairsService.recordFindings(selectedCaseId, {
        findingsSummary,
        findingStatus,
        proceduralStage: SADisciplinaryStage.FINDINGS_RECORDED,
      });
      setStatusMessage("Formal findings documented under committee review.");
      const updated = await studentAffairsService.getCases();
      setCases(updated);
    } catch {
      alert("Error recording findings.");
    } finally {
      setLoading(false);
    }
  }

  async function handleApproveSanction(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedCaseId || !sanctionDetails) {
      alert("Please provide the sanction details.");
      return;
    }
    setLoading(true);
    try {
      await studentAffairsService.approveSanction(selectedCaseId, {
        sanctionType,
        sanctionDetails,
        decisionMakerId,
        appealDeadlineDays: appealDays,
      });
      setStatusMessage("Sanction officially approved and communicated. Appeal window activated.");
      const updated = await studentAffairsService.getCases();
      setCases(updated);
    } catch {
      alert("Error approving sanction.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: "Dashboard", href: "/app/dashboard" },
          { label: "Student Affairs", href: "/app/student-affairs" },
          { label: "Disciplinary Proceedings", href: "/app/student-affairs/disciplinary" },
        ]}
      />

      <div className="border-b border-slate-800 pb-5">
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
          <Gavel className="h-6 w-6 text-purple-400" />
          Formal Disciplinary Proceedings & Sanction Governance
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Manage code of conduct investigations, evidence evaluation, committee findings, and sanction authorization under due process.
        </p>
      </div>

      <StudentAffairsNav />

      {/* Fair Process Safeguard Callout */}
      <div className="p-4 rounded-xl border border-purple-500/20 bg-purple-950/20 text-xs text-slate-300 space-y-1.5">
        <div className="flex items-center gap-2 font-semibold text-purple-300">
          <ShieldCheck className="h-4 w-4 text-emerald-400" />
          Institutional Due Process Safeguards
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          Complaints and invigilator referrals are never treated as proven misconduct until committee inquiry findings are formally entered.
          AI algorithms and opaque scoring are strictly prohibited from determining student penalties.
        </p>
      </div>

      {statusMessage && (
        <div className="p-3.5 rounded-lg border border-emerald-500/30 bg-emerald-950/20 text-xs text-emerald-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            <span>{statusMessage}</span>
          </div>
          <button onClick={() => setStatusMessage("")} className="text-emerald-400 hover:text-white">
            Dismiss
          </button>
        </div>
      )}

      {/* Case Selector */}
      <Card className="p-4 border-slate-800 bg-slate-900/40">
        <label className="block text-xs font-medium text-slate-400 mb-1.5">
          Select Disciplinary Case Proceeding
        </label>
        <select
          value={selectedCaseId}
          onChange={(e) => setSelectedCaseId(e.target.value)}
          className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
        >
          {cases.map((c) => (
            <option key={c.id} value={c.id}>
              {c.case_number} - {c.title} ({c.status})
            </option>
          ))}
        </select>
      </Card>

      {/* Procedural Milestone Stepper */}
      <Card className="p-6 border-slate-800 bg-slate-900/40 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Procedural Stage Milestones ({milestones.completionPercentage}% Complete)
          </h2>
          <Badge variant="outline" className="text-[10px] border-purple-500/30 text-purple-400">
            {proceeding?.procedural_stage || "INTAKE"}
          </Badge>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2">
          {milestones.milestones.map((m, idx) => (
            <div
              key={idx}
              className={`p-2.5 rounded-lg border text-center text-xs transition-colors ${
                m.isComplete
                  ? "border-emerald-500/30 bg-emerald-950/20 text-emerald-300"
                  : m.isCurrent
                  ? "border-purple-500 bg-purple-950/40 text-purple-200 font-semibold ring-1 ring-purple-500"
                  : "border-slate-800 bg-slate-950/40 text-slate-500"
              }`}
            >
              <div className="text-[10px] opacity-75">Step {idx + 1}</div>
              <div className="text-[11px] font-medium mt-0.5">{m.label}</div>
            </div>
          ))}
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Form 1: Record Committee Findings */}
        <Card className="p-6 border-slate-800 bg-slate-900/40 space-y-4">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <FileCheck2 className="h-4 w-4 text-indigo-400" />
            1. Document Formal Inquiry Findings
          </h2>
          <form onSubmit={handleRecordFindings} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Finding Determination <span className="text-rose-400">*</span>
              </label>
              <select
                value={findingStatus}
                onChange={(e) => setFindingStatus(e.target.value as SAFindingStatus)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
              >
                <option value={SAFindingStatus.PENDING}>PENDING (Inquiry in progress)</option>
                <option value={SAFindingStatus.SUBSTANTIATED}>SUBSTANTIATED (Misconduct established by evidence)</option>
                <option value={SAFindingStatus.UNSUBSTANTIATED}>UNSUBSTANTIATED (Allegation not supported)</option>
                <option value={SAFindingStatus.INCONCLUSIVE}>INCONCLUSIVE (Insufficient verification)</option>
                <option value={SAFindingStatus.DISMISSED}>DISMISSED (Outside institutional jurisdiction)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Committee Findings Summary <span className="text-rose-400">*</span>
              </label>
              <textarea
                rows={4}
                placeholder="State the evidence considered, statements taken, and formal committee conclusion..."
                value={findingsSummary}
                onChange={(e) => setFindingsSummary(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                required
              />
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 hover:bg-indigo-500 text-white text-xs"
            >
              Commit Formal Findings
            </Button>
          </form>
        </Card>

        {/* Form 2: Sanction Authorization & Appeal Window */}
        <Card className="p-6 border-slate-800 bg-slate-900/40 space-y-4">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Scale className="h-4 w-4 text-purple-400" />
            2. Authorize Proportional Sanction & Notice
          </h2>
          <form onSubmit={handleApproveSanction} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Sanction Type <span className="text-rose-400">*</span>
              </label>
              <select
                value={sanctionType}
                onChange={(e) => setSanctionType(e.target.value as SASanctionType)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
              >
                <option value={SASanctionType.FORMAL_WARNING}>FORMAL WARNING (Written reprimand)</option>
                <option value={SASanctionType.DISCIPLINARY_PROBATION}>DISCIPLINARY PROBATION (Semester-long review)</option>
                <option value={SASanctionType.COMMUNITY_SERVICE}>COMMUNITY SERVICE (Campus welfare contribution)</option>
                <option value={SASanctionType.RESTITUTION}>RESTITUTION (Repair / compensation)</option>
                <option value={SASanctionType.FACILITY_RESTRICTION}>FACILITY RESTRICTION (Lab / hostel limitation)</option>
                <option value={SASanctionType.COUNSELING_REFERRAL}>COUNSELING REFERRAL (Student support service)</option>
                <option value={SASanctionType.SUSPENSION}>SUSPENSION (Temporary exclusion)</option>
                <option value={SASanctionType.EXPULSION}>EXPULSION (Permanent termination)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Sanction Specifics & Corrective Terms <span className="text-rose-400">*</span>
              </label>
              <textarea
                rows={3}
                placeholder="Specify sanction conditions, duration, or academic grade impacts..."
                value={sanctionDetails}
                onChange={(e) => setSanctionDetails(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Sanctioning Authority
                </label>
                <input
                  type="text"
                  value="Dr. Meenakshi Sundaram (Dean)"
                  disabled
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-400"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Appeal Window (Days)
                </label>
                <input
                  type="number"
                  value={appealDays}
                  onChange={(e) => setAppealDays(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-500"
                  min={7}
                  max={30}
                />
              </div>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold"
            >
              Approve Sanction & Issue Formal Notice
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
}

export default function DisciplinaryWorkspacePage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-slate-500">Loading disciplinary workspace...</div>}>
      <DisciplinaryWorkspaceContent />
    </Suspense>
  );
}

