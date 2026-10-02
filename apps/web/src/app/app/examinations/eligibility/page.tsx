"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { examinationsService } from "@/services/examinations.service";
import { ExamEligibility, EligibilityStatus } from "@/types/examinations";
import { DataGrid } from "@/components/data-grid/data-grid";
import { ColumnDef } from "@/components/data-grid/data-grid.types";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { StatCard } from "@/components/ui/stat-card";
import { useToast } from "@/components/ui/toast";
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Filter,
  Users,
  Award,
  ArrowRight,
  ExternalLink,
} from "lucide-react";

export default function ExamEligibilityPage() {
  const { hasPermission } = useAuth();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [eligibilityList, setEligibilityList] = useState<ExamEligibility[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [selectedDept, setSelectedDept] = useState<string>("ALL");

  // Review Modal State
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState<ExamEligibility | null>(null);
  const [actionType, setActionType] = useState<"APPROVE_EXCEPTION" | "REJECT_EXCEPTION" | "FLAG_FOR_REVIEW">("APPROVE_EXCEPTION");
  const [reviewReason, setReviewReason] = useState("");
  const [reviewing, setReviewing] = useState(false);

  const loadEligibility = async () => {
    try {
      setLoading(true);
      const res = await examinationsService.getEligibility({
        status: statusFilter !== "ALL" ? (statusFilter as EligibilityStatus) : undefined,
        department: selectedDept !== "ALL" ? selectedDept : undefined,
      });
      setEligibilityList(res.data);
    } catch {
      showToast({ title: "Error", message: "Failed to load eligibility evaluations", type: "error" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEligibility();
  }, [statusFilter, selectedDept]);

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRecord) return;

    try {
      setReviewing(true);
      await examinationsService.reviewEligibility(
        selectedRecord.id,
        actionType,
        reviewReason || "HOD Academic Council discretionary review."
      );
      showToast({ title: "Updated", message: "Eligibility evaluation successfully updated.", type: "success" });
      setReviewModalOpen(false);
      setReviewReason("");
      loadEligibility();
    } catch (err: unknown) {
      showToast({
        title: "Error",
        message: err instanceof Error ? err.message : "Failed to review eligibility",
        type: "error",
      });
    } finally {
      setReviewing(false);
    }
  };

  const eligibleCount = eligibilityList.filter((e) => e.eligibilityStatus === "ELIGIBLE").length;
  const ineligibleCount = eligibilityList.filter((e) => e.eligibilityStatus === "INELIGIBLE").length;
  const condCount = eligibilityList.filter((e) => e.eligibilityStatus === "CONDITIONALLY_ELIGIBLE").length;

  const columns: ColumnDef<ExamEligibility>[] = useMemo(
    () => [
      {
        id: "student",
        header: "Student Candidate",
        cell: (row) => (
          <div>
            <Link
              href={`/app/students/${row.studentId}`}
              className="font-semibold text-slate-900 hover:text-indigo-600 dark:text-white dark:hover:text-indigo-400"
            >
              {row.studentName}
            </Link>
            <div className="flex items-center gap-2 mt-0.5 text-xs text-slate-500">
              <span className="font-mono font-medium text-slate-600 dark:text-slate-300">
                {row.rollNumber}
              </span>
              <span>•</span>
              <span>{row.program}</span>
            </div>
          </div>
        ),
      },
      {
        id: "course",
        header: "Subject & Offering",
        cell: (row) => (
          <div className="text-xs">
            <span className="font-semibold text-slate-800 dark:text-slate-200">
              {row.courseCode}
            </span>
            <p className="text-slate-500">{row.courseName}</p>
          </div>
        ),
      },
      {
        id: "attendance",
        header: "Attendance Gate",
        cell: (row) => {
          const isBelow = row.attendancePercentage < row.minimumRequirement;
          return (
            <div className="text-xs">
              <div className="flex items-center gap-1.5 font-bold">
                <span className={isBelow ? "text-rose-600 dark:text-rose-400" : "text-emerald-600 dark:text-emerald-400"}>
                  {row.attendancePercentage}%
                </span>
                <span className="text-slate-400 font-normal">
                  (Req: {row.minimumRequirement}%)
                </span>
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">
                Evaluated: {row.evaluatedDate}
              </div>
            </div>
          );
        },
      },
      {
        id: "status",
        header: "Eligibility Status",
        cell: (row) => {
          const isEligible = row.eligibilityStatus === "ELIGIBLE";
          const isCond = row.eligibilityStatus === "CONDITIONALLY_ELIGIBLE";
          return (
            <div>
              <span
                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold ${
                  isEligible
                    ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                    : isCond
                    ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                    : "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
                }`}
              >
                {isEligible ? <CheckCircle2 className="h-3 w-3" /> : <AlertTriangle className="h-3 w-3" />}
                {row.eligibilityStatus}
              </span>
              {row.isOverridden && (
                <div className="text-[10px] text-amber-600 dark:text-amber-400 mt-0.5 font-medium">
                  Condonation Granted
                </div>
              )}
            </div>
          );
        },
      },
      {
        id: "reason",
        header: "Audit Rationale",
        cell: (row) => (
          <div className="text-xs text-slate-500 max-w-xs truncate" title={row.reason || row.overrideReason || "Meets minimum attendance requirement"}>
            {row.reason || row.overrideReason || "Meets minimum attendance requirement"}
          </div>
        ),
      },
      {
        id: "actions",
        header: "Actions",
        cell: (row) => (
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant={row.eligibilityStatus === "INELIGIBLE" ? "primary" : "outline"}
              onClick={() => {
                setSelectedRecord(row);
                setActionType(row.eligibilityStatus === "INELIGIBLE" ? "APPROVE_EXCEPTION" : "REJECT_EXCEPTION");
                setReviewModalOpen(true);
              }}
              className="h-7 text-xs"
            >
              Review Standing
            </Button>
          </div>
        ),
      },
    ],
    []
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300">
              Exam Attendance Gate
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">75% Minimum Bar Rule</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Student Examination Eligibility
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Automated eligibility evaluation consuming attendance service registers with HOD condonation exception workflows.
          </p>
        </div>

        <Link href="/app/attendance/leaves">
          <Button variant="outline" size="sm" className="gap-1.5 text-xs">
            <ExternalLink className="h-3.5 w-3.5" />
            View Attendance Leaves
          </Button>
        </Link>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Evaluated Candidates"
          value={String(eligibilityList.length)}
          description="Semester 5 candidate roster"
          icon={<Users className="h-5 w-5 text-indigo-600" />}
        />
        <StatCard
          title="Eligible Candidates"
          value={String(eligibleCount)}
          description="Qualified for hall ticket"
          icon={<CheckCircle2 className="h-5 w-5 text-emerald-600" />}
        />
        <StatCard
          title="Ineligible / Debarred"
          value={String(ineligibleCount)}
          description="Below 75% attendance"
          icon={<ShieldAlert className="h-5 w-5 text-rose-600" />}
        />
        <StatCard
          title="Conditional / Condoned"
          value={String(condCount)}
          description="Granted medical exception"
          icon={<ShieldCheck className="h-5 w-5 text-amber-600" />}
        />
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3 bg-slate-50/70 p-3 rounded-xl border border-slate-200 dark:bg-slate-900/60 dark:border-slate-800 text-xs">
        <div className="flex items-center gap-1.5 text-slate-500 font-medium">
          <Filter className="h-3.5 w-3.5" />
          Filter Standing:
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
        >
          <option value="ALL">All Evaluation Statuses</option>
          <option value="ELIGIBLE">Eligible (≥ 75%)</option>
          <option value="INELIGIBLE">Ineligible (&lt; 75%)</option>
          <option value="CONDITIONALLY_ELIGIBLE">Conditionally Eligible</option>
          <option value="PENDING_REVIEW">Pending Review</option>
        </select>

        <select
          value={selectedDept}
          onChange={(e) => setSelectedDept(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
        >
          <option value="ALL">All Departments</option>
          <option value="Computer Science & Engineering">Computer Science & Engineering</option>
          <option value="Electronics & Communication">Electronics & Communication</option>
        </select>
      </div>

      {/* Enterprise DataGrid */}
      <DataGrid<ExamEligibility>
        data={eligibilityList}
        columns={columns}
        keyExtractor={(row) => row.id}
        loading={loading}
        searchPlaceholder="Search candidate by name, roll number, or subject..."
        emptyTitle="No eligibility records found"
        emptyDescription="All students satisfy current examination attendance criteria."
      />

      {/* Review Standing & Condonation Modal */}
      <Dialog open={reviewModalOpen} onClose={() => setReviewModalOpen(false)}>
        <form onSubmit={handleReviewSubmit} className="p-6 space-y-5 max-w-lg">
          <div className="border-b border-slate-200 pb-3 dark:border-slate-800">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">
              Review Candidate Examination Eligibility
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Grant formal medical condonation exception or confirm debarment from hall ticket.
            </p>
          </div>

          {selectedRecord && (
            <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900/60 text-xs space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-400">Candidate:</span>
                <span className="font-semibold text-slate-900 dark:text-white">
                  {selectedRecord.studentName} ({selectedRecord.rollNumber})
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Subject:</span>
                <span className="font-medium text-slate-800 dark:text-slate-200">
                  {selectedRecord.courseCode} - {selectedRecord.courseName}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Recorded Attendance:</span>
                <span className="font-bold text-rose-600 dark:text-rose-400">
                  {selectedRecord.attendancePercentage}% (Min Required: {selectedRecord.minimumRequirement}%)
                </span>
              </div>
            </div>
          )}

          <div className="space-y-4 text-xs">
            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Administrative Action *
              </label>
              <select
                value={actionType}
                onChange={(e) => setActionType(e.target.value as any)}
                className="w-full rounded-lg border border-slate-300 bg-white p-2.5 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              >
                <option value="APPROVE_EXCEPTION">Grant Condonation Exception (Make Conditionally Eligible)</option>
                <option value="REJECT_EXCEPTION">Confirm Debarment (Mark Ineligible)</option>
                <option value="FLAG_FOR_REVIEW">Flag for Academic Council Review</option>
              </select>
            </div>

            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Justification & Decision Notes *
              </label>
              <textarea
                rows={3}
                required
                value={reviewReason}
                onChange={(e) => setReviewReason(e.target.value)}
                placeholder="e.g. Condonation sanctioned on medical certificate prescription and hospital discharge slip."
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
            <Button type="button" variant="outline" onClick={() => setReviewModalOpen(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant={actionType === "REJECT_EXCEPTION" ? "destructive" : "primary"}
              disabled={reviewing}
            >
              {reviewing ? "Processing..." : "Confirm Decision"}
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
