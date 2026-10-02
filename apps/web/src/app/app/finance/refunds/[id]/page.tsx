"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  RotateCcw,
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Clock,
  DollarSign,
  User,
  FileText,
  CreditCard,
  ShieldCheck,
  Send,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useToast, ToastType } from "@/components/ui/toast";
import { useAuth } from "@/lib/auth-context";
import { financeService } from "@/services/finance.service";
import { formatMoney } from "@/services/financial-calculator";
import { Refund } from "@/types/finance";

export default function RefundDetailPage() {
  const params = useParams();
  const refundId = params?.id as string;
  const { hasPermission } = useAuth();
  const { showToast } = useToast();
  const notify = (title: string, type: ToastType = "info") => showToast({ title, type });

  const [refund, setRefund] = useState<Refund | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Review Dialog State
  const [actionType, setActionType] = useState<"APPROVE" | "REJECT" | null>(null);
  const [reviewNotes, setReviewNotes] = useState("");
  const [approvedAmount, setApprovedAmount] = useState<number>(0);
  const [submitting, setSubmitting] = useState(false);

  const canApprove = hasPermission("finance.approve_refunds") || hasPermission("refunds:approve");
  const canProcess = hasPermission("finance.manage_refunds") || hasPermission("refunds:process");

  const loadData = async () => {
    if (!refundId) return;
    try {
      setLoading(true);
      setError(null);
      const res = await financeService.getRefundById(refundId);
      setRefund(res.data);
      setApprovedAmount(res.data.requestedAmount);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Refund petition not found.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [refundId]);

  const handleReviewAction = async () => {
    if (!refund || !actionType) return;
    if (!reviewNotes.trim()) {
      notify("Audit review justification notes are required.", "error");
      return;
    }
    if (actionType === "APPROVE" && (approvedAmount <= 0 || approvedAmount > refund.requestedAmount)) {
      notify(`Approved amount must be between ₹1 and ${formatMoney(refund.requestedAmount)}.`, "error");
      return;
    }

    try {
      setSubmitting(true);
      await financeService.reviewRefund(
        refund.id,
        actionType,
        reviewNotes.trim(),
        actionType === "APPROVE" ? Number(approvedAmount) : undefined
      );

      notify(
        actionType === "APPROVE" ? "Refund approved successfully!" : "Refund petition rejected.",
        "success"
      );
      setActionType(null);
      setReviewNotes("");
      loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to review refund.";
      notify(msg, "error");
    } finally {
      setSubmitting(false);
    }
  };

  const handleProcessDisbursement = async () => {
    if (!refund) return;
    try {
      setSubmitting(true);
      await financeService.processRefund(refund.id);
      notify("Electronic bank reimbursement issued successfully!", "success");
      loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to process disbursement.";
      notify(msg, "error");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-sm text-slate-500">Loading refund petition profile...</div>
      </div>
    );
  }

  if (error || !refund) {
    return (
      <div className="space-y-4">
        <Link href="/app/finance/refunds">
          <Button variant="ghost" size="sm" className="gap-1.5 text-xs">
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Refunds Ledger
          </Button>
        </Link>
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-6 text-center text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-300">
          <h2 className="text-lg font-bold">Petition Not Found</h2>
          <p className="mt-1 text-sm">{error || "Requested refund petition does not exist."}</p>
        </div>
      </div>
    );
  }

  const isPending = refund.status === "REQUESTED" || refund.status === "UNDER_REVIEW";
  const isApproved = refund.status === "APPROVED";

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 mb-1">
            <Link href="/app/finance" className="hover:text-emerald-600 transition">
              Finance Hub
            </Link>
            <span>/</span>
            <Link href="/app/finance/refunds" className="hover:text-emerald-600 transition">
              Refunds
            </Link>
            <span>/</span>
            <span className="font-semibold text-slate-700 dark:text-slate-300">
              {refund.refundNumber}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Petition {refund.refundNumber}
            </h1>
            <span
              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                refund.status === "PROCESSED"
                  ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                  : refund.status === "APPROVED"
                  ? "bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300"
                  : refund.status === "REJECTED"
                  ? "bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300"
                  : "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300"
              }`}
            >
              {refund.status.replace("_", " ")}
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Registered on {new Date(refund.requestedAt).toLocaleString()} by {refund.requestedBy}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {isPending && canApprove && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setActionType("REJECT")}
                className="gap-1.5 text-xs text-rose-600 hover:text-rose-700 border-rose-200"
              >
                <XCircle className="w-3.5 h-3.5" />
                Reject
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => setActionType("APPROVE")}
                className="gap-1.5 text-xs bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                Approve Refund
              </Button>
            </>
          )}

          {isApproved && canProcess && (
            <Button
              variant="primary"
              size="sm"
              onClick={handleProcessDisbursement}
              disabled={submitting}
              className="gap-1.5 text-xs bg-emerald-600 hover:bg-emerald-700 text-white"
            >
              <Send className="w-3.5 h-3.5" />
              {submitting ? "Disbursing..." : "Disburse Funds Electronically"}
            </Button>
          )}
        </div>
      </div>

      {/* Main Grid Info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left 2 Cols: Amounts & Audit Timeline */}
        <div className="md:col-span-2 space-y-6">
          {/* Financial Overview Card */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
              Refund Financial Evaluation
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pb-4 border-b border-slate-100 dark:border-slate-800">
              <div>
                <div className="text-xs text-slate-500">Original Invoice Payment</div>
                <div className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                  {formatMoney(refund.originalPaymentAmount)}
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-500">Requested Refund Amount</div>
                <div className="text-2xl font-bold text-amber-600 dark:text-amber-400 mt-1">
                  {formatMoney(refund.requestedAmount)}
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-500">Sanctioned Payout Amount</div>
                <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
                  {refund.approvedAmount ? formatMoney(refund.approvedAmount) : "Pending"}
                </div>
              </div>
            </div>

            <div className="mt-4 text-xs space-y-2">
              <div>
                <span className="font-semibold text-slate-700 dark:text-slate-300">
                  Justification Rationale:
                </span>
                <p className="mt-1 text-slate-600 dark:text-slate-400 bg-slate-50 p-3 rounded-lg border border-slate-100 dark:bg-slate-800 dark:border-slate-700">
                  {refund.reason}
                </p>
              </div>

              {refund.reviewerNotes && (
                <div className="pt-2">
                  <span className="font-semibold text-slate-700 dark:text-slate-300">
                    Committee Review Decision Notes:
                  </span>
                  <p className="mt-1 text-slate-600 dark:text-slate-400 bg-emerald-50/50 p-3 rounded-lg border border-emerald-100 dark:bg-emerald-950/20 dark:border-emerald-800">
                    {refund.reviewerNotes}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Audit Timeline */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
              Lifecycle Governance Timeline
            </h2>
            <div className="space-y-4">
              {refund.timeline && refund.timeline.length > 0 ? (
                refund.timeline.map((item, idx) => (
                  <div key={item.id || idx} className="flex items-start gap-3 text-xs">
                    <div className="mt-0.5 p-1 rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    </div>
                    <div>
                      <div className="font-semibold text-slate-900 dark:text-white">
                        {item.action.replace("_", " ")}
                      </div>
                      <div className="text-slate-500">
                        By {item.actor} • {new Date(item.timestamp).toLocaleString()}
                      </div>
                      {item.notes && (
                        <div className="mt-1 text-slate-700 dark:text-slate-300 bg-slate-50 p-2 rounded border border-slate-100 dark:bg-slate-800 dark:border-slate-700">
                          {item.notes}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-xs text-slate-500">Timeline unavailable.</div>
              )}
            </div>
          </div>
        </div>

        {/* Right Col: Metadata and Linked Entities */}
        <div className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:bg-slate-900 dark:border-slate-800 text-xs space-y-3">
            <h3 className="font-bold uppercase tracking-wider text-slate-400">
              Beneficiary Candidate
            </h3>
            <div className="flex items-center gap-3 pt-1">
              <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center font-bold text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
                <User className="w-5 h-5" />
              </div>
              <div>
                <p className="font-semibold text-slate-900 dark:text-white text-sm">
                  {refund.studentName}
                </p>
                <p className="font-mono text-slate-500">{refund.rollNumber}</p>
              </div>
            </div>

            <div className="pt-2 border-t border-slate-100 dark:border-slate-800 space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-500">Associated Invoice:</span>
                <Link
                  href={`/app/finance/invoices/${refund.invoiceId}`}
                  className="font-mono font-medium text-blue-600 hover:underline dark:text-blue-400"
                >
                  {refund.invoiceNumber}
                </Link>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-emerald-200 bg-emerald-50/70 p-5 shadow-xs text-xs space-y-2 dark:bg-emerald-950/30 dark:border-emerald-800">
            <div className="flex items-center gap-1.5 font-bold text-emerald-900 dark:text-emerald-300">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              Zero-Mutation Audit Policy
            </div>
            <p className="text-emerald-800/90 dark:text-emerald-400 leading-relaxed">
              Approved refunds do not silently erase past receipts. A dedicated counter-credit and electronic disbursement voucher are logged into the general register.
            </p>
          </div>
        </div>
      </div>

      {/* Review Dialog */}
      <Dialog open={actionType !== null} onOpenChange={(open) => !open && setActionType(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-lg font-bold">
              {actionType === "APPROVE" ? (
                <>
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                  Approve Refund Sanction
                </>
              ) : (
                <>
                  <XCircle className="w-5 h-5 text-rose-600" />
                  Reject Refund Petition
                </>
              )}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 pt-2">
            {actionType === "APPROVE" && (
              <div>
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Approved Amount (₹) <span className="text-rose-500">*</span>
                </label>
                <Input
                  type="number"
                  min={1}
                  max={refund.requestedAmount}
                  value={approvedAmount || ""}
                  onChange={(e) => setApprovedAmount(Number(e.target.value))}
                  className="mt-1 font-bold"
                  required
                />
                <p className="text-[11px] text-slate-500 mt-1">
                  Requested amount: {formatMoney(refund.requestedAmount)}
                </p>
              </div>
            )}

            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                {actionType === "APPROVE" ? "Sanction Audit Notes" : "Rejection Rationale"}{" "}
                <span className="text-rose-500">*</span>
              </label>
              <Input
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                placeholder={
                  actionType === "APPROVE"
                    ? "e.g. Approved per hostel vacate clearance certificate"
                    : "e.g. Non-refundable institutional tuition policy"
                }
                className="mt-1"
                required
              />
            </div>

            <DialogFooter className="pt-3">
              <Button
                type="button"
                variant="outline"
                onClick={() => setActionType(null)}
                disabled={submitting}
              >
                Cancel
              </Button>
              <Button
                type="button"
                variant="primary"
                onClick={handleReviewAction}
                disabled={submitting || !reviewNotes.trim()}
                className={
                  actionType === "APPROVE"
                    ? "bg-emerald-600 hover:bg-emerald-700 text-white"
                    : "bg-rose-600 hover:bg-rose-700 text-white"
                }
              >
                {submitting
                  ? "Committing..."
                  : actionType === "APPROVE"
                  ? "Confirm Approval"
                  : "Confirm Rejection"}
              </Button>
            </DialogFooter>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
