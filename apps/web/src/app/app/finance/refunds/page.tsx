"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type { PaymentTransaction, RefundStatus, RefundTransaction } from "@campusos/types";

export default function RefundsPage() {
  const { hasPermission } = useAuth();
  const [refunds, setRefunds] = useState<RefundTransaction[]>([]);
  const [payments, setPayments] = useState<PaymentTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Form Fields
  const [paymentId, setPaymentId] = useState("");
  const [refundAmount, setRefundAmount] = useState<number | string>("");
  const [reason, setReason] = useState("");

  const canCreate = hasPermission("refunds:create");
  const canApprove = hasPermission("refunds:approve");
  const canProcess = hasPermission("refunds:process");

  async function loadData() {
    try {
      setLoading(true);
      setError(null);
      const [refRes, payRes] = await Promise.all([
        apiFetch<RefundTransaction[]>("/api/v1/finance/refunds?limit=100"),
        apiFetch<PaymentTransaction[]>("/api/v1/finance/payments?limit=100").catch(() => ({ data: [] })),
      ]);

      setRefunds(refRes.data);
      setPayments((payRes.data || []).filter((p) => p.status === "SUCCESS"));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load refund transactions.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const handleRequestRefund = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      setFormError(null);

      const amountNum = Number(refundAmount);
      if (!paymentId) throw new Error("Please select the original payment transaction.");
      if (isNaN(amountNum) || amountNum <= 0) throw new Error("Refund amount must be greater than zero.");
      if (!reason.trim()) throw new Error("Reason for refund is required.");

      const selectedPay = payments.find((p) => p.id === paymentId);
      if (selectedPay && amountNum > Number(selectedPay.amount)) {
        throw new Error(`Refund amount cannot exceed payment amount (₹${selectedPay.amount}).`);
      }

      await apiFetch("/api/v1/finance/refunds", {
        method: "POST",
        body: JSON.stringify({
          payment_id: paymentId,
          refund_amount: amountNum,
          reason: reason.trim(),
        }),
      });

      setShowModal(false);
      setPaymentId("");
      setRefundAmount("");
      setReason("");
      await loadData();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to request refund.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleApprove = async (id: string) => {
    if (!confirm("Are you sure you want to approve this refund request?")) return;
    try {
      await apiFetch(`/api/v1/finance/refunds/${id}/approve`, { method: "POST" });
      await loadData();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to approve refund.");
    }
  };

  const handleProcess = async (id: string) => {
    const reference = prompt("Enter bank disbursal reference (e.g. NEFT/IMPS UTR):");
    if (!reference) return;
    try {
      await apiFetch(`/api/v1/finance/refunds/${id}/process`, {
        method: "POST",
        body: JSON.stringify({
          refund_mode: "BANK_TRANSFER",
          refund_reference: reference,
        }),
      });
      await loadData();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to process refund disbursal.");
    }
  };

  const formatCurrency = (amountVal: number | string | undefined) => {
    const num = typeof amountVal === "string" ? parseFloat(amountVal) : (amountVal ?? 0);
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(num);
  };

  const getStatusBadge = (status: RefundStatus | string) => {
    switch (status) {
      case "PROCESSED":
        return "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300";
      case "APPROVED":
        return "bg-sky-100 text-sky-800 dark:bg-sky-950/60 dark:text-sky-300";
      case "REJECTED":
        return "bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300";
      default:
        return "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300";
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 mb-1">
            <Link href="/app/finance" className="hover:text-emerald-600 transition">
              Finance Hub
            </Link>
            <span>/</span>
            <span className="font-semibold text-slate-700 dark:text-slate-300">Refunds</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Fee Refunds & Accounting Reversals
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Multi-stage refund authorization and outward disbursal tracking without historical data loss.
          </p>
        </div>

        {canCreate && (
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center justify-center rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white shadow-xs hover:bg-emerald-700 transition"
          >
            + Request Refund
          </button>
        )}
      </div>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300">
          <p className="font-semibold">Unable to load Refunds</p>
          <p className="mt-0.5">{error}</p>
        </div>
      )}

      {/* Table */}
      {loading ? (
        <div className="text-center py-16 text-slate-500">Loading refunds journal...</div>
      ) : refunds.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 p-12 text-center dark:border-slate-800">
          <p className="text-sm font-medium text-slate-900 dark:text-white">No refund transactions recorded.</p>
          <p className="mt-1 text-xs text-slate-500">Refund requests are authorized through a dual-control approval protocol.</p>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-700 dark:text-slate-300">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500 border-b border-slate-200 dark:bg-slate-800/50 dark:border-slate-800">
                <tr>
                  <th className="px-4 py-3">Student</th>
                  <th className="px-4 py-3">Payment #</th>
                  <th className="px-4 py-3">Refund Amount</th>
                  <th className="px-4 py-3">Reason</th>
                  <th className="px-4 py-3">Disbursal Ref</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {refunds.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition">
                    <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">
                      {r.student_name || "Enrolled Student"}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-600 dark:text-slate-400">
                      {r.payment_number || "Payment"}
                    </td>
                    <td className="px-4 py-3 font-bold text-rose-600 dark:text-rose-400">
                      {formatCurrency(r.refund_amount)}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-600 dark:text-slate-300">{r.reason}</td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-500">
                      {r.refund_reference ? `${r.refund_mode}: ${r.refund_reference}` : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${getStatusBadge(
                          r.status
                        )}`}
                      >
                        {r.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      {r.status === "REQUESTED" && canApprove && (
                        <button
                          onClick={() => handleApprove(r.id)}
                          className="text-xs font-semibold text-sky-600 hover:text-sky-700 mr-2"
                        >
                          Approve
                        </button>
                      )}
                      {r.status === "APPROVED" && canProcess && (
                        <button
                          onClick={() => handleProcess(r.id)}
                          className="text-xs font-semibold text-emerald-600 hover:text-emerald-700"
                        >
                          Disburse
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

      {/* Request Refund Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs overflow-y-auto">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900 border border-slate-200 dark:border-slate-800 my-8">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">Request Payment Refund</h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-slate-600 text-xl font-bold"
              >
                ×
              </button>
            </div>

            {formError && (
              <div className="mt-4 rounded-lg bg-rose-50 p-3 text-xs text-rose-700 dark:bg-rose-950/50 dark:text-rose-300">
                {formError}
              </div>
            )}

            <form onSubmit={handleRequestRefund} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                  Original Payment Voucher *
                </label>
                <select
                  required
                  value={paymentId}
                  onChange={(e) => setPaymentId(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                >
                  <option value="">Select Payment</option>
                  {payments.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.payment_number} • {p.student_name} ({formatCurrency(p.amount)}) - Ref: {p.transaction_reference}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                  Refund Amount (₹) *
                </label>
                <input
                  type="number"
                  required
                  min="1"
                  step="0.01"
                  placeholder="e.g. 10000"
                  value={refundAmount}
                  onChange={(e) => setRefundAmount(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                  Justification / Refund Reason *
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="Provide audit justification (e.g. Admission withdrawal, duplicate transfer)"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
              </div>

              <div className="mt-6 flex justify-end gap-3 border-t border-slate-100 pt-4 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-emerald-700 disabled:opacity-50"
                >
                  {submitting ? "Submitting..." : "Submit Refund Request"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
