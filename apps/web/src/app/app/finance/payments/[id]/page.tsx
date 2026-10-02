"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  CreditCard,
  ArrowLeft,
  Calendar,
  CheckCircle2,
  Clock,
  Building2,
  FileText,
  User,
  ShieldCheck,
  Receipt as ReceiptIcon,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { financeService } from "@/services/finance.service";
import { formatMoney } from "@/services/financial-calculator";
import { Payment } from "@/types/finance";

export default function PaymentDetailPage() {
  const params = useParams();
  const paymentId = params?.id as string;

  const [payment, setPayment] = useState<Payment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadPayment() {
      if (!paymentId) return;
      try {
        setLoading(true);
        setError(null);
        const res = await financeService.getPaymentById(paymentId);
        setPayment(res.data);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Payment record not found.");
      } finally {
        setLoading(false);
      }
    }
    loadPayment();
  }, [paymentId]);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-sm text-slate-500">Retrieving payment transaction details...</div>
      </div>
    );
  }

  if (error || !payment) {
    return (
      <div className="space-y-4">
        <Link href="/app/finance/payments">
          <Button variant="ghost" size="sm" className="gap-1.5 text-xs">
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Payments Ledger
          </Button>
        </Link>
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-6 text-center text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-300">
          <h2 className="text-lg font-bold">Transaction Record Unavailable</h2>
          <p className="mt-1 text-sm">{error || "Payment record not found."}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Navigation & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 mb-1">
            <Link href="/app/finance" className="hover:text-emerald-600 transition">
              Finance Hub
            </Link>
            <span>/</span>
            <Link href="/app/finance/payments" className="hover:text-emerald-600 transition">
              Payments
            </Link>
            <span>/</span>
            <span className="font-semibold text-slate-700 dark:text-slate-300">
              {payment.transactionRef}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Transaction {payment.transactionRef}
            </h1>
            <span
              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                payment.status === "SUCCESS"
                  ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                  : "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300"
              }`}
            >
              {payment.status}
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Recorded on {payment.paymentDate} by {payment.recordedBy}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href={`/app/finance/invoices/${payment.invoiceId}`}>
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              <FileText className="w-3.5 h-3.5" />
              View Invoice
            </Button>
          </Link>
          <Link href={`/app/finance/receipts`}>
            <Button variant="primary" size="sm" className="gap-1.5 text-xs bg-emerald-600 hover:bg-emerald-700 text-white">
              <ReceiptIcon className="w-3.5 h-3.5" />
              View Official Receipt
            </Button>
          </Link>
        </div>
      </div>

      {/* Main Grid Info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left 2 Cols: Financial Breakdown & Allocation */}
        <div className="md:col-span-2 space-y-6">
          {/* Amount Card */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
              Financial Summary
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pb-4 border-b border-slate-100 dark:border-slate-800">
              <div>
                <div className="text-xs text-slate-500">Total Payment Amount</div>
                <div className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                  {formatMoney(payment.amount)}
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-500">Allocated to Invoices</div>
                <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
                  {formatMoney(payment.allocatedAmount)}
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-500">Unallocated Float</div>
                <div className="text-2xl font-bold text-slate-600 dark:text-slate-400 mt-1">
                  {formatMoney(payment.unallocatedAmount)}
                </div>
              </div>
            </div>

            {/* Payment Instrument Details */}
            <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
              <div>
                <span className="text-slate-500">Payment Channel:</span>
                <p className="font-semibold text-slate-900 dark:text-white mt-0.5">
                  {payment.paymentMethod.replace("_", " ")}
                </p>
              </div>
              <div>
                <span className="text-slate-500">Transaction / UTR Ref:</span>
                <p className="font-mono font-medium text-slate-900 dark:text-white mt-0.5">
                  {payment.transactionRef}
                </p>
              </div>
              <div>
                <span className="text-slate-500">Receipt Voucher #:</span>
                <p className="font-mono font-medium text-emerald-600 dark:text-emerald-400 mt-0.5">
                  {payment.receiptNumber}
                </p>
              </div>
              {payment.bankName && (
                <div>
                  <span className="text-slate-500">Bank Name:</span>
                  <p className="font-medium text-slate-900 dark:text-white mt-0.5">
                    {payment.bankName}
                  </p>
                </div>
              )}
              {payment.chequeNumber && (
                <div>
                  <span className="text-slate-500">Cheque / DD No:</span>
                  <p className="font-mono font-medium text-slate-900 dark:text-white mt-0.5">
                    {payment.chequeNumber}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Allocation Table */}
          <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs dark:bg-slate-900 dark:border-slate-800">
            <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-slate-900 dark:text-white">
                  Invoice Allocation Register
                </h2>
                <p className="text-xs text-slate-500">
                  Direct ledger mapping of this transaction against student billing documents.
                </p>
              </div>
            </div>

            <table className="w-full text-left text-xs text-slate-700 dark:text-slate-300">
              <thead className="bg-slate-50 font-semibold uppercase text-slate-500 border-b border-slate-200 dark:bg-slate-800/50 dark:border-slate-800">
                <tr>
                  <th className="px-4 py-3">Allocation ID</th>
                  <th className="px-4 py-3">Invoice Number</th>
                  <th className="px-4 py-3 text-right">Allocated Amount</th>
                  <th className="px-4 py-3">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {payment.allocations && payment.allocations.length > 0 ? (
                  payment.allocations.map((alloc) => (
                    <tr key={alloc.id}>
                      <td className="px-4 py-3 font-mono text-slate-500">{alloc.id}</td>
                      <td className="px-4 py-3">
                        <Link
                          href={`/app/finance/invoices/${alloc.invoiceId}`}
                          className="font-mono font-medium text-blue-600 hover:underline dark:text-blue-400"
                        >
                          {alloc.invoiceNumber}
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-right font-semibold text-emerald-600 dark:text-emerald-400">
                        {formatMoney(alloc.allocatedAmount)}
                      </td>
                      <td className="px-4 py-3 text-slate-500">
                        {new Date(alloc.allocatedAt).toLocaleDateString()}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td className="px-4 py-3 font-mono text-slate-500">{payment.id}-all</td>
                    <td className="px-4 py-3">
                      <Link
                        href={`/app/finance/invoices/${payment.invoiceId}`}
                        className="font-mono font-medium text-blue-600 hover:underline dark:text-blue-400"
                      >
                        {payment.invoiceNumber}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-right font-semibold text-emerald-600 dark:text-emerald-400">
                      {formatMoney(payment.allocatedAmount)}
                    </td>
                    <td className="px-4 py-3 text-slate-500">{payment.paymentDate}</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Audit Timeline */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
              Transaction Audit Trail
            </h2>
            <div className="space-y-4">
              {payment.history && payment.history.length > 0 ? (
                payment.history.map((h, idx) => (
                  <div key={h.id || idx} className="flex items-start gap-3 text-xs">
                    <div className="mt-0.5 p-1 rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    </div>
                    <div>
                      <div className="font-semibold text-slate-900 dark:text-white">
                        {h.action}
                      </div>
                      <div className="text-slate-500">
                        By {h.actor} • {new Date(h.timestamp).toLocaleString()}
                      </div>
                      {h.notes && (
                        <div className="mt-1 text-slate-700 dark:text-slate-300 bg-slate-50 p-2 rounded border border-slate-100 dark:bg-slate-800 dark:border-slate-700">
                          {h.notes}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="flex items-start gap-3 text-xs">
                  <div className="mt-0.5 p-1 rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <div className="font-semibold text-slate-900 dark:text-white">
                      PAYMENT_RECORDED
                    </div>
                    <div className="text-slate-500">
                      By {payment.recordedBy} • {payment.paymentDate}
                    </div>
                    <div className="mt-1 text-slate-700 dark:text-slate-300 bg-slate-50 p-2 rounded border border-slate-100 dark:bg-slate-800 dark:border-slate-700">
                      {payment.notes || "Official institutional fee settlement."}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Col: Student Identity & Security Check */}
        <div className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:bg-slate-900 dark:border-slate-800 text-xs space-y-3">
            <h3 className="font-bold uppercase tracking-wider text-slate-400">
              Student Information
            </h3>
            <div className="flex items-center gap-3 pt-1">
              <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center font-bold text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
                <User className="w-5 h-5" />
              </div>
              <div>
                <p className="font-semibold text-slate-900 dark:text-white text-sm">
                  {payment.studentName}
                </p>
                <p className="font-mono text-slate-500">{payment.rollNumber}</p>
              </div>
            </div>
            <div className="pt-2 border-t border-slate-100 dark:border-slate-800 space-y-1.5">
              <div className="flex justify-between">
                <span className="text-slate-500">Student ID:</span>
                <span className="font-mono text-slate-700 dark:text-slate-300">
                  {payment.studentId}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Billed Invoice:</span>
                <span className="font-mono text-slate-700 dark:text-slate-300">
                  {payment.invoiceNumber}
                </span>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-emerald-200 bg-emerald-50/70 p-5 shadow-xs text-xs space-y-2 dark:bg-emerald-950/30 dark:border-emerald-800">
            <div className="flex items-center gap-1.5 font-bold text-emerald-900 dark:text-emerald-300">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              Institutional Audit Guarantee
            </div>
            <p className="text-emerald-800/90 dark:text-emerald-400 leading-relaxed">
              This transaction is an immutable audit record tied to receipt{" "}
              <span className="font-mono font-bold">{payment.receiptNumber}</span>. Reversals or adjustments require authorized refund approval workflow.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
