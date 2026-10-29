"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  FileCheck2,
  User,
  Building2,
  Briefcase,
  Calendar,
  Award,
  ChevronLeft,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  ShieldCheck,
  Check,
  X,
  FileText,
  Edit3,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/toast";
import { placementService } from "@/services/placement.service";
import {
  Application,
  EligibilitySnapshot,
  EligibilityStatus,
  InterviewStage,
  ApplicationStatus,
} from "@/types/placement";

export default function ApplicationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { showToast } = useToast();
  const applicationId = params?.id as string;

  const [application, setApplication] = useState<Application | null>(null);
  const [snapshot, setSnapshot] = useState<EligibilitySnapshot | null>(null);
  const [loading, setLoading] = useState(true);

  // Override modal
  const [showOverrideModal, setShowOverrideModal] = useState(false);
  const [overrideStatus, setOverrideStatus] =
    useState<EligibilityStatus>("ELIGIBLE");
  const [overrideReason, setOverrideReason] = useState("");

  const loadData = async () => {
    try {
      setLoading(true);
      const appRes = await placementService.getApplicationById(applicationId);
      if (!appRes.data) {
        showToast({
          title: "Not Found",
          message: "Application record not found",
          type: "error",
        });
        router.push("/app/placement/applications");
        return;
      }

      setApplication(appRes.data);

      // Evaluate eligibility snapshot
      const snapRes = await placementService.evaluateEligibility(
        appRes.data.studentId,
        appRes.data.positionId,
      );
      setSnapshot(snapRes.data);
    } catch {
      showToast({
        title: "Error",
        message: "Failed to load application details",
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (applicationId) {
      loadData();
    }
  }, [applicationId]);

  const handleShortlist = async () => {
    if (!application) return;
    try {
      await placementService.shortlistApplications(
        [application.id],
        "Placement Officer",
      );
      showToast({
        title: "Shortlisted",
        message: "Candidate advanced to interview pipeline",
        type: "success",
      });
      loadData();
    } catch {
      showToast({
        title: "Error",
        message: "Failed to shortlist application",
        type: "error",
      });
    }
  };

  const handleConfirmOverride = async () => {
    if (!snapshot || !overrideReason.trim()) {
      showToast({
        title: "Validation Error",
        message: "Override reason is mandatory",
        type: "error",
      });
      return;
    }

    try {
      const res = await placementService.overrideEligibility(
        snapshot,
        overrideStatus,
        overrideReason,
        "Dr. Ramesh (Dean Placement)",
      );
      setSnapshot(res.data);
      showToast({
        title: "Eligibility Overridden",
        message: `Status updated to ${overrideStatus}. Audit record created.`,
        type: "info",
      });
      setShowOverrideModal(false);
      setOverrideReason("");
    } catch {
      showToast({
        title: "Error",
        message: "Failed to override eligibility",
        type: "error",
      });
    }
  };

  if (loading || !application) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-500">
            Loading candidate application dossier...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back button */}
      <div>
        <Link
          href="/app/placement/applications"
          className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-900 dark:hover:text-slate-200 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          Back to Applications Ledger
        </Link>
      </div>

      {/* Header Profile Card */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-xl shadow-md">
              <FileCheck2 className="w-7 h-7" />
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                  Application {application.applicationCode}
                </h1>
                <Badge
                  variant={
                    application.status === "SELECTED"
                      ? "success"
                      : application.status === "SHORTLISTED"
                        ? "info"
                        : application.status === "REJECTED"
                          ? "destructive"
                          : "secondary"
                  }
                  dot
                >
                  {application.status}
                </Badge>
                <Badge variant="outline">
                  Stage: {application.currentStage}
                </Badge>
              </div>

              <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 dark:text-slate-400 mt-1.5">
                <Link
                  href={`/app/placement/students/${application.studentId}`}
                  className="font-semibold text-slate-900 dark:text-slate-200 hover:underline"
                >
                  {application.studentName} ({application.rollNumber})
                </Link>
                <span>•</span>
                <span>{application.program}</span>
                <span>•</span>
                <span className="font-semibold text-indigo-600 dark:text-indigo-400">
                  {application.positionTitle} @ {application.companyName}
                </span>
                <span>•</span>
                <span>Applied: {application.appliedDate.split("T")[0]}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {application.status === "SUBMITTED" && (
              <Button
                variant="primary"
                size="sm"
                onClick={handleShortlist}
                className="gap-1.5 text-xs"
              >
                <Check className="w-3.5 h-3.5" />
                Shortlist Candidate
              </Button>
            )}
            <Link href={`/app/placement/interviews`}>
              <Button variant="outline" size="sm" className="gap-1.5 text-xs">
                <Calendar className="w-3.5 h-3.5" />
                Schedule Interview
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Main Grid: Eligibility Snapshot (Left 2 cols) & Timeline (Right 1 col) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          {/* Eligibility Snapshot Card */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-indigo-500" />
                <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                  Automated Eligibility Snapshot
                </h2>
              </div>

              <div className="flex items-center gap-2">
                <Badge
                  variant={
                    snapshot?.status === "ELIGIBLE"
                      ? "success"
                      : snapshot?.status === "CONDITIONALLY_ELIGIBLE"
                        ? "warning"
                        : "destructive"
                  }
                  dot
                >
                  {snapshot?.status}
                </Badge>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowOverrideModal(true)}
                  className="h-7 text-xs gap-1"
                >
                  <Edit3 className="w-3 h-3" />
                  Override
                </Button>
              </div>
            </div>

            {/* Overridden Callout */}
            {snapshot?.isOverridden && (
              <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 dark:bg-amber-950/30 dark:border-amber-800 dark:text-amber-200 text-xs">
                <strong>Manual Administrative Override:</strong> Overridden to{" "}
                <strong>{snapshot.status}</strong> by {snapshot.overriddenBy} on{" "}
                {new Date(snapshot.overriddenAt || "").toLocaleString()}.
                <p className="mt-0.5 italic">"{snapshot.overrideReason}"</p>
              </div>
            )}

            {/* Evaluated Rules List */}
            <div className="space-y-3">
              {snapshot?.rules.map((rule, idx) => (
                <div
                  key={idx}
                  className={`p-3.5 rounded-xl border flex items-start justify-between gap-4 text-xs ${
                    rule.passed
                      ? "bg-slate-50 border-slate-200 dark:bg-slate-800/40 dark:border-slate-700"
                      : "bg-rose-50/50 border-rose-200 dark:bg-rose-950/20 dark:border-rose-800"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5">
                      {rule.passed ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                      ) : (
                        <XCircle className="w-4 h-4 text-rose-500 shrink-0" />
                      )}
                    </div>
                    <div>
                      <span className="font-bold text-slate-900 dark:text-white">
                        {rule.ruleName}
                      </span>
                      <p className="text-slate-600 dark:text-slate-400 mt-0.5">
                        {rule.message}
                      </p>
                    </div>
                  </div>

                  <div className="text-right shrink-0">
                    <div className="text-[11px] text-slate-500">
                      Required:{" "}
                      <strong>
                        {Array.isArray(rule.required)
                          ? rule.required.join(", ")
                          : String(rule.required)}
                      </strong>
                    </div>
                    <div className="text-[11px] text-slate-600 dark:text-slate-300 mt-0.5">
                      Actual:{" "}
                      <strong>
                        {Array.isArray(rule.actual)
                          ? rule.actual.join(", ")
                          : String(rule.actual)}
                      </strong>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Internal Notes & Rejection Reason */}
          {application.rejectionReason && (
            <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 dark:bg-rose-950/20 dark:border-rose-800">
              <h4 className="text-xs font-bold text-rose-800 dark:text-rose-300">
                Application Rejection Reason
              </h4>
              <p className="text-xs text-rose-700 dark:text-rose-400 mt-1">
                {application.rejectionReason}
              </p>
            </div>
          )}
        </div>

        {/* Right Col: Timeline & Details */}
        <div className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4">
              Recruitment Lifecycle
            </h3>
            <div className="relative pl-6 border-l-2 border-slate-200 dark:border-slate-800 space-y-4">
              {application.timeline.map((entry) => (
                <div key={entry.id} className="relative">
                  <div className="absolute -left-[31px] top-0 w-4 h-4 rounded-full bg-indigo-500 border-2 border-white dark:border-slate-900" />
                  <div className="text-xs font-semibold text-slate-900 dark:text-white">
                    {entry.action}
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">
                    By {entry.actor} •{" "}
                    {new Date(entry.timestamp).toLocaleDateString()}
                  </div>
                  {entry.details && (
                    <div className="text-[11px] text-slate-600 dark:text-slate-300 mt-1 bg-slate-50 dark:bg-slate-800 p-2 rounded">
                      {entry.details}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Manual Eligibility Override Modal */}
      {showOverrideModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-white">
              Manual Eligibility Override
            </h3>
            <p className="text-xs text-slate-400">
              Placement officers may override automated eligibility flags with
              documented academic or administrative justification.
            </p>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-slate-300 font-medium">
                  New Eligibility Status *
                </label>
                <select
                  value={overrideStatus}
                  onChange={(e) =>
                    setOverrideStatus(e.target.value as EligibilityStatus)
                  }
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-800 p-2 text-white"
                >
                  <option value="ELIGIBLE">ELIGIBLE (Full Clearance)</option>
                  <option value="CONDITIONALLY_ELIGIBLE">
                    CONDITIONALLY ELIGIBLE (Pending Re-test)
                  </option>
                  <option value="INELIGIBLE">INELIGIBLE (Disqualified)</option>
                </select>
              </div>

              <div>
                <label className="text-slate-300 font-medium">
                  Justification & Regulatory Authority *
                </label>
                <textarea
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  placeholder="e.g. Cleared backlogs during supplementary evaluation; sanctioned by Academic Dean."
                  rows={3}
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-800 p-2 text-white"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowOverrideModal(false)}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleConfirmOverride}
              >
                Sign & Authorize Override
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
