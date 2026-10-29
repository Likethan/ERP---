"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  Layers,
  ArrowLeft,
  CheckCircle2,
  Clock,
  Send,
  Lock,
  Power,
  FileCheck2,
  DollarSign,
  Users,
  ShieldCheck,
  History,
  FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/ui/stat-card";
import { Tabs } from "@/components/ui/tabs";
import { useToast } from "@/components/ui/toast";
import { financeService } from "@/services/finance.service";
import { formatMoney } from "@/services/financial-calculator";
import { FeeStructure, StudentFeeAssignment } from "@/types/finance";

export default function FeeStructureDetailPage() {
  const params = useParams();
  const { showToast } = useToast();
  const structureId = params.id as string;

  const [structure, setStructure] = useState<FeeStructure | null>(null);
  const [assignments, setAssignments] = useState<StudentFeeAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");

  const loadData = async () => {
    if (!structureId) return;
    try {
      setLoading(true);
      const [fsRes, assignRes] = await Promise.all([
        financeService.getFeeStructureById(structureId),
        financeService.getFeeAssignments(),
      ]);
      setStructure(fsRes.data);
      setAssignments(
        assignRes.data.filter((a) => a.feeStructureId === structureId),
      );
    } catch (err: unknown) {
      showToast({
        title: "Error Loading Details",
        message:
          err instanceof Error
            ? err.message
            : "Unable to retrieve fee structure",
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [structureId]);

  const handleSubmitApproval = async () => {
    if (!structure) return;
    try {
      setUpdating(true);
      const res = await financeService.submitFeeStructureForApproval(
        structure.id,
      );
      setStructure(res.data);
      showToast({
        title: "Submitted",
        message: "Fee structure submitted for Academic Senate approval.",
        type: "success",
      });
    } catch (err: unknown) {
      showToast({
        title: "Submission Failed",
        message: err instanceof Error ? err.message : "Error",
        type: "error",
      });
    } finally {
      setUpdating(false);
    }
  };

  const handleApprove = async () => {
    if (!structure) return;
    try {
      setUpdating(true);
      const res = await financeService.approveFeeStructure(structure.id);
      setStructure(res.data);
      showToast({
        title: "Approved",
        message: "Fee structure approved by council.",
        type: "success",
      });
    } catch (err: unknown) {
      showToast({
        title: "Approval Failed",
        message: err instanceof Error ? err.message : "Error",
        type: "error",
      });
    } finally {
      setUpdating(false);
    }
  };

  const handleActivate = async () => {
    if (!structure) return;
    try {
      setUpdating(true);
      const res = await financeService.activateFeeStructure(structure.id);
      setStructure(res.data);
      showToast({
        title: "Activated",
        message: "Fee structure is now active for student billing.",
        type: "success",
      });
    } catch (err: unknown) {
      showToast({
        title: "Activation Failed",
        message: err instanceof Error ? err.message : "Error",
        type: "error",
      });
    } finally {
      setUpdating(false);
    }
  };

  const handleRetire = async () => {
    if (!structure) return;
    try {
      setUpdating(true);
      const res = await financeService.retireFeeStructure(structure.id);
      setStructure(res.data);
      showToast({
        title: "Retired",
        message: "Fee structure retired.",
        type: "info",
      });
    } catch (err: unknown) {
      showToast({
        title: "Retire Failed",
        message: err instanceof Error ? err.message : "Error",
        type: "error",
      });
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="py-20 text-center text-slate-400">
        <p className="text-sm">Loading fee structure specifications...</p>
      </div>
    );
  }

  if (!structure) {
    return (
      <div className="py-20 text-center space-y-3">
        <p className="text-base font-semibold text-slate-200">
          Fee Structure Not Found
        </p>
        <Link href="/app/finance/fee-structures">
          <Button variant="outline" size="sm">
            Back to Directory
          </Button>
        </Link>
      </div>
    );
  }

  const tabs = [
    {
      id: "overview",
      label: "Overview",
      content: (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Scheme Metadata
            </h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Scheme Code:</span>
                <span className="font-mono font-bold text-indigo-400">
                  {structure.code}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Academic Program:</span>
                <span className="text-slate-200 font-medium">
                  {structure.program}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Department:</span>
                <span className="text-slate-200">{structure.department}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Semester / Term:</span>
                <span className="text-slate-200 font-medium">
                  Semester {structure.semester}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Academic Session:</span>
                <span className="text-slate-200">{structure.academicYear}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Effective Date:</span>
                <span className="text-slate-200">
                  {structure.effectiveDate}
                </span>
              </div>
              <div className="flex justify-between py-1 pt-2 font-bold text-sm">
                <span className="text-white">Gross Scheme Total:</span>
                <span className="font-mono text-emerald-400">
                  {formatMoney(structure.grossTotal)}
                </span>
              </div>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Governance & Approval
            </h3>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Approval Status:</span>
                <span className="font-semibold text-slate-200">
                  {structure.status}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Ratified By:</span>
                <span className="text-slate-200">
                  {structure.approvedBy || "Pending Review"}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Ratified Date:</span>
                <span className="text-slate-200">
                  {structure.approvedAt
                    ? new Date(structure.approvedAt).toLocaleDateString()
                    : "N/A"}
                </span>
              </div>
              <div className="pt-2">
                <span className="text-slate-400 block mb-1">
                  Administrative Notes:
                </span>
                <p className="p-2.5 rounded bg-slate-950 border border-slate-800 text-slate-300 text-[11px] leading-relaxed">
                  {structure.notes || "Standard university fee schedule."}
                </p>
              </div>
            </div>
          </div>
        </div>
      ),
    },
    {
      id: "items",
      label: `Fee Items (${structure.components.length})`,
      content: (
        <div className="rounded-xl bg-slate-900/60 border border-slate-800 overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 font-semibold">
              <tr>
                <th className="py-2.5 px-3">#</th>
                <th className="py-2.5 px-3">Fee Head Title</th>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3">Applicability</th>
                <th className="py-2.5 px-3 text-right">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {structure.components.map((comp, idx) => (
                <tr key={comp.id} className="hover:bg-slate-800/30">
                  <td className="py-2 px-3 font-mono text-slate-500">
                    {idx + 1}
                  </td>
                  <td className="py-2 px-3 font-medium text-slate-200">
                    {comp.title}
                  </td>
                  <td className="py-2 px-3 text-slate-400">
                    {comp.categoryName}
                  </td>
                  <td className="py-2 px-3">
                    <span
                      className={`px-1.5 py-0.5 rounded text-[11px] font-medium ${
                        comp.isMandatory
                          ? "bg-slate-800 text-slate-300 border border-slate-700/60"
                          : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                      }`}
                    >
                      {comp.isMandatory ? "Mandatory" : "Optional"}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right font-mono font-semibold text-slate-200">
                    {formatMoney(comp.amount)}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-slate-950 border-t border-slate-800 font-bold">
              <tr>
                <td
                  colSpan={4}
                  className="py-2.5 px-3 text-right text-slate-400"
                >
                  Total Annual / Semester Fee:
                </td>
                <td className="py-2.5 px-3 text-right font-mono text-emerald-400 text-sm">
                  {formatMoney(structure.grossTotal)}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      ),
    },
    {
      id: "students",
      label: `Assigned Students (${assignments.length})`,
      content: (
        <div className="rounded-xl bg-slate-900/60 border border-slate-800 overflow-hidden">
          {assignments.length === 0 ? (
            <div className="py-12 text-center text-slate-500">
              <Users className="mx-auto h-8 w-8 text-slate-600 mb-1" />
              <p className="text-xs">
                No students currently assigned to this fee structure.
              </p>
            </div>
          ) : (
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 font-semibold">
                <tr>
                  <th className="py-2.5 px-3">Roll No.</th>
                  <th className="py-2.5 px-3">Candidate</th>
                  <th className="py-2.5 px-3 text-right">Net Payable</th>
                  <th className="py-2.5 px-3 text-right">Paid</th>
                  <th className="py-2.5 px-3 text-right">Outstanding</th>
                  <th className="py-2.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {assignments.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-800/30">
                    <td className="py-2 px-3 font-mono font-medium text-indigo-400">
                      {a.rollNumber}
                    </td>
                    <td className="py-2 px-3 text-slate-200">
                      {a.studentName}
                    </td>
                    <td className="py-2 px-3 text-right font-mono text-slate-300">
                      {formatMoney(a.netPayable)}
                    </td>
                    <td className="py-2 px-3 text-right font-mono text-emerald-400">
                      {formatMoney(a.paidAmount)}
                    </td>
                    <td className="py-2 px-3 text-right font-mono text-rose-400">
                      {formatMoney(a.outstandingAmount)}
                    </td>
                    <td className="py-2 px-3">
                      <span className="px-1.5 py-0.5 rounded text-[11px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {a.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      ),
    },
    {
      id: "history",
      label: "Lifecycle History",
      content: (
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="relative pl-6 space-y-4 border-l border-slate-800">
            {structure.history.map((h) => (
              <div key={h.id} className="relative group">
                <span className="absolute -left-[31px] top-1 h-3.5 w-3.5 rounded-full bg-slate-800 ring-4 ring-slate-900 border border-indigo-500/40" />
                <div className="flex items-baseline justify-between gap-4">
                  <p className="text-xs font-semibold text-slate-200">
                    {h.action}
                  </p>
                  <span className="text-[11px] text-slate-500">
                    {new Date(h.timestamp).toLocaleString()}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  By {h.actor}
                </p>
                {h.notes && (
                  <p className="text-[11px] text-slate-500 mt-1 italic">
                    {h.notes}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <Link
            href="/app/finance/fee-structures"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-slate-200 mb-2"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Fee Structures Directory
          </Link>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              {structure.name}
            </h1>
            <span className="font-mono text-xs font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
              {structure.code}
            </span>
            <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              {structure.status}
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-400">
            {structure.program} • Semester {structure.semester} (
            {structure.academicYear})
          </p>
        </div>

        {/* Lifecycle Actions */}
        <div className="flex items-center gap-2">
          {structure.status === "DRAFT" && (
            <Button
              variant="primary"
              size="sm"
              onClick={handleSubmitApproval}
              disabled={updating}
              className="gap-1.5 text-xs"
            >
              <Send className="h-3.5 w-3.5" />
              Submit for Approval
            </Button>
          )}

          {structure.status === "PENDING_APPROVAL" && (
            <Button
              variant="primary"
              size="sm"
              onClick={handleApprove}
              disabled={updating}
              className="gap-1.5 text-xs"
            >
              <CheckCircle2 className="h-3.5 w-3.5" />
              Approve Structure
            </Button>
          )}

          {structure.status === "APPROVED" && (
            <Button
              variant="primary"
              size="sm"
              onClick={handleActivate}
              disabled={updating}
              className="gap-1.5 text-xs bg-emerald-600 hover:bg-emerald-500 text-white"
            >
              <Power className="h-3.5 w-3.5" />
              Activate Structure
            </Button>
          )}

          {structure.status === "ACTIVE" && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleRetire}
              disabled={updating}
              className="gap-1.5 text-xs text-rose-400 border-rose-500/30 hover:bg-rose-500/10"
            >
              <Lock className="h-3.5 w-3.5" />
              Retire Structure
            </Button>
          )}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          title="Gross Structure Total"
          value={formatMoney(structure.grossTotal)}
          description="Cumulative billing amount"
          icon={<DollarSign className="h-5 w-5 text-emerald-400" />}
        />
        <StatCard
          title="Fee Components"
          value={`${structure.components.length} Heads`}
          description="Instructional and campus levies"
          icon={<Layers className="h-5 w-5 text-indigo-400" />}
        />
        <StatCard
          title="Assigned Cohort"
          value={`${assignments.length} Enrolled`}
          description="Students mapped to this scheme"
          icon={<Users className="h-5 w-5 text-cyan-400" />}
        />
      </div>

      {/* Tabs */}
      <Tabs
        tabs={tabs.map((t) => ({ id: t.id, label: t.label }))}
        activeTab={activeTab}
        onChange={setActiveTab}
      />
      <div className="mt-4">
        {tabs.find((t) => t.id === activeTab)?.content}
      </div>
    </div>
  );
}
