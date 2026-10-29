"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { studentAffairsService } from "@/services/student-affairs.service";
import { StudentAffairsCalculator } from "@/services/student-affairs-calculator";
import {
  GrievanceCaseModel,
  AppealRecordModel,
  SAAppealGrounds,
  SAAppealStatus,
} from "@/types/student-affairs";
import { StudentAffairsNav } from "@/components/student-affairs/student-affairs-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Scale,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  FileText,
  Clock,
  ArrowRight,
} from "lucide-react";

function AppealsContent() {
  const searchParams = useSearchParams();
  const preselectedCaseId = searchParams?.get("caseId");

  const [cases, setCases] = useState<GrievanceCaseModel[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>(preselectedCaseId || "");
  const [appealsList, setAppealsList] = useState<AppealRecordModel[]>([]);

  // File appeal form
  const [appealGrounds, setAppealGrounds] = useState<SAAppealGrounds>(SAAppealGrounds.NEW_EVIDENCE);
  const [groundsStatement, setGroundsStatement] = useState("");

  // Review form
  const [selectedAppealId, setSelectedAppealId] = useState<string>("");
  const [reviewerId, setReviewerId] = useState("usr-ombuds-001");
  const [reviewStatus, setReviewStatus] = useState<SAAppealStatus>(SAAppealStatus.OVERTURNED);
  const [outcomeSummary, setOutcomeSummary] = useState("");

  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    async function load() {
      const allCases = await studentAffairsService.getCases();
      setCases(allCases);
      if (preselectedCaseId) {
        setSelectedCaseId(preselectedCaseId);
      } else if (allCases.length > 0) {
        setSelectedCaseId(allCases[0].id);
      }

      const allApps: AppealRecordModel[] = [];
      allCases.forEach((c) => {
        if (c.appeals) allApps.push(...c.appeals);
      });
      setAppealsList(allApps);
      if (allApps.length > 0) {
        setSelectedAppealId(allApps[0].id);
      }
    }
    load();
  }, [preselectedCaseId]);

  const activeCase = cases.find((c) => c.id === selectedCaseId);
  const isAppealWindowValid = StudentAffairsCalculator.isAppealWindowActive(
    activeCase?.disciplinary_proceeding?.appeal_deadline
  );

  async function handleFileAppeal(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedCaseId || !groundsStatement) return;

    setLoading(true);
    setErrorMessage("");
    try {
      const created = await studentAffairsService.fileAppeal({
        caseId: selectedCaseId,
        appealGrounds,
        groundsStatement,
      });
      setNotification("Statutory appeal record formally lodged with independent review panel.");
      setAppealsList((prev) => [...prev, created]);
      setGroundsStatement("");
    } catch (err: any) {
      setErrorMessage(err?.message || "Failed to lodge appeal.");
    } finally {
      setLoading(false);
    }
  }

  async function handleReviewAppeal(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedAppealId || !outcomeSummary) return;

    // Client-side separation of duties validation
    const appealMatch = appealsList.find((a) => a.id === selectedAppealId);
    const relatedCase = cases.find((c) => c.id === appealMatch?.case_id);
    const originalDecisionMaker = relatedCase?.disciplinary_proceeding?.decision_maker_id;

    const sod = StudentAffairsCalculator.validateSeparationOfDuties(
      originalDecisionMaker,
      reviewerId
    );
    if (!sod.isValid) {
      setErrorMessage(sod.errorMessage || "Separation of Duties Violation");
      return;
    }

    setLoading(true);
    setErrorMessage("");
    try {
      await studentAffairsService.reviewAppeal({
        appealId: selectedAppealId,
        assignedReviewerId: reviewerId,
        reviewStatus,
        outcomeSummary,
      });
      setNotification("Appellate determination recorded and case status updated.");
      setOutcomeSummary("");
      const updated = await studentAffairsService.getCases();
      setCases(updated);
    } catch (err: any) {
      setErrorMessage(err?.message || "Error reviewing appeal.");
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
          { label: "Appeals & Reviews", href: "/app/student-affairs/appeals" },
        ]}
      />

      <div className="border-b border-slate-800 pb-5">
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
          <Scale className="h-6 w-6 text-cyan-400" />
          Statutory Appeals, Reviews & Separation of Duties
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Independent appellate review workflow upholding procedural fairness and institutional separation between decision-maker and reviewer.
        </p>
      </div>

      <StudentAffairsNav />

      {/* Separation of Duties Rule Banner */}
      <div className="p-4 rounded-xl border border-cyan-500/20 bg-cyan-950/20 text-xs text-slate-300 space-y-1.5">
        <div className="flex items-center gap-2 font-semibold text-cyan-300">
          <ShieldCheck className="h-4 w-4 text-emerald-400" />
          UGC Mandated Separation of Duties Enforcement
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          The original decision-maker who imposed a disciplinary sanction is barred by institutional policy from acting as the appellate reviewer.
          Appeals are heard independently by the Institutional Ombudsperson or Standing Appellate Council.
        </p>
      </div>

      {notification && (
        <div className="p-3.5 rounded-lg border border-emerald-500/30 bg-emerald-950/20 text-xs text-emerald-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            <span>{notification}</span>
          </div>
          <button onClick={() => setNotification("")} className="text-emerald-400 hover:text-white">
            Dismiss
          </button>
        </div>
      )}

      {errorMessage && (
        <div className="p-3.5 rounded-lg border border-rose-500/30 bg-rose-950/20 text-xs text-rose-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-rose-400" />
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage("")} className="text-rose-400 hover:text-white">
            Dismiss
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Form 1: File an Appeal */}
        <Card className="p-6 border-slate-800 bg-slate-900/40 space-y-4">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <FileText className="h-4 w-4 text-cyan-400" />
            1. Lodge Formal Appeal
          </h2>

          <form onSubmit={handleFileAppeal} className="space-y-4 text-xs">
            <div>
              <label className="block text-slate-300 mb-1">Select Sanctioned Case *</label>
              <select
                value={selectedCaseId}
                onChange={(e) => setSelectedCaseId(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
              >
                {cases.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.case_number} - {c.title}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-slate-300 mb-1">Recognized Grounds for Appeal *</label>
              <select
                value={appealGrounds}
                onChange={(e) => setAppealGrounds(e.target.value as SAAppealGrounds)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
              >
                <option value={SAAppealGrounds.NEW_EVIDENCE}>NEW EVIDENCE (Material not available during inquiry)</option>
                <option value={SAAppealGrounds.PROCEDURAL_IRREGULARITY}>PROCEDURAL IRREGULARITY (Failure of due process)</option>
                <option value={SAAppealGrounds.DISPROPORTIONATE_SANCTION}>DISPROPORTIONATE SANCTION (Excessive penalty)</option>
                <option value={SAAppealGrounds.BIAS_CONFLICT_OF_INTEREST}>BIAS / CONFLICT (Unrecused panel bias)</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-300 mb-1">Grounds Narrative & New Facts *</label>
              <textarea
                rows={4}
                placeholder="State the factual basis for the appeal, citing specific procedural gaps or newly discovered evidence..."
                value={groundsStatement}
                onChange={(e) => setGroundsStatement(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                required
              />
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold"
            >
              Lodge Formal Appeal
            </Button>
          </form>
        </Card>

        {/* Form 2: Review & Determine Appeal */}
        <Card className="p-6 border-slate-800 bg-slate-900/40 space-y-4">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Scale className="h-4 w-4 text-purple-400" />
            2. Appellate Determination (Independent Reviewer)
          </h2>

          <form onSubmit={handleReviewAppeal} className="space-y-4 text-xs">
            <div>
              <label className="block text-slate-300 mb-1">Select Pending Appeal *</label>
              <select
                value={selectedAppealId}
                onChange={(e) => setSelectedAppealId(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
              >
                {appealsList.map((app) => (
                  <option key={app.id} value={app.id}>
                    Appeal #{app.id.slice(0, 8)} - {app.appeal_grounds} ({app.review_status})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-slate-300 mb-1">Assigned Independent Reviewer *</label>
              <select
                value={reviewerId}
                onChange={(e) => setReviewerId(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
              >
                <option value="usr-ombuds-001">Dr. Meenakshi Sundaram (Independent Ombudsperson)</option>
                <option value="usr-appellate-lead">Prof. R. Sengupta (Appellate Tribunal Chair)</option>
                <option value="usr-dean-001">Dr. Vikram Sethi (ORIGINAL DECISION MAKER - VIOLATION TEST)</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-300 mb-1">Appellate Ruling Determination *</label>
              <select
                value={reviewStatus}
                onChange={(e) => setReviewStatus(e.target.value as SAAppealStatus)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
              >
                <option value={SAAppealStatus.OVERTURNED}>OVERTURNED (Sanction revoked, record expunged)</option>
                <option value={SAAppealStatus.UPHELD}>UPHELD (Original decision affirmed)</option>
                <option value={SAAppealStatus.SANCTION_MODIFIED}>SANCTION MODIFIED (Reduced penalty applied)</option>
                <option value={SAAppealStatus.REMANDED}>REMANDED (Returned for re-inquiry)</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-300 mb-1">Appellate Outcome Rationale *</label>
              <textarea
                rows={3}
                placeholder="State the formal reasoning of the Ombudsperson / Appellate Board..."
                value={outcomeSummary}
                onChange={(e) => setOutcomeSummary(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                required
              />
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
            >
              Issue Final Appellate Ruling
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
}

export default function AppealsPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-slate-500">Loading appeals...</div>}>
      <AppealsContent />
    </Suspense>
  );
}

