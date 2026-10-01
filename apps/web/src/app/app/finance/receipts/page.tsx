"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { financeService } from "@/services/finance.service";
import type { Receipt } from "@campusos/types";

export default function ReceiptsPage() {
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedReceipt, setSelectedReceipt] = useState<Receipt | null>(null);

  async function loadReceipts() {
    try {
      setLoading(true);
      setError(null);
      const res = await apiFetch<Receipt[]>("/api/v1/finance/receipts?limit=100");
      setReceipts(res.data);
    } catch {
      const mockRes = await financeService.getPayments();
      const mapped: Receipt[] = (mockRes.data || []).map((p) => ({
        id: p.id,
        receipt_number: p.receiptNumber,
        transaction_reference: p.transactionRef,
        amount_paid: p.amount,
        payment_mode: p.paymentMode,
        issued_at: new Date().toISOString(),
        student_name: p.studentName,
        student_admission_number: p.rollNumber,
        student_roll_number: p.rollNumber,
        invoice_number: p.invoiceNumber,
      } as unknown as Receipt));
      setReceipts(mapped);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReceipts();
  }, []);

  const formatCurrency = (amount: number | string | undefined) => {
    const num = typeof amount === "string" ? parseFloat(amount) : (amount ?? 0);
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(num);
  };

  const handlePrint = () => {
    window.print();
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
            <span className="font-semibold text-slate-700 dark:text-slate-300">Receipts</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Official Receipts Archive & Vouchers
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Immutable financial payment vouchers with unique audit numbers and payment tracking.
          </p>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300">
          <p className="font-semibold">Unable to load Receipts</p>
          <p className="mt-0.5">{error}</p>
        </div>
      )}

      {/* Receipts Table */}
      {loading ? (
        <div className="text-center py-16 text-slate-500">Loading receipts archive...</div>
      ) : receipts.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 p-12 text-center dark:border-slate-800">
          <p className="text-sm font-medium text-slate-900 dark:text-white">No payment receipts issued yet.</p>
          <p className="mt-1 text-xs text-slate-500">Receipts are automatically generated when payments are recorded.</p>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-700 dark:text-slate-300">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500 border-b border-slate-200 dark:bg-slate-800/50 dark:border-slate-800">
                <tr>
                  <th className="px-4 py-3">Receipt #</th>
                  <th className="px-4 py-3">Student</th>
                  <th className="px-4 py-3">Date & Time</th>
                  <th className="px-4 py-3">Amount</th>
                  <th className="px-4 py-3">Payment Mode</th>
                  <th className="px-4 py-3">Transaction Reference</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {receipts.map((rcp) => (
                  <tr key={rcp.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition">
                    <td className="px-4 py-3 font-mono font-semibold text-emerald-600 dark:text-emerald-400">
                      {rcp.receipt_number}
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-medium text-slate-900 dark:text-white">
                        {rcp.student_name || "Student"}
                      </div>
                      <div className="text-xs text-slate-400 font-mono">{rcp.student_admission_number || ""}</div>
                    </td>
                    <td className="px-4 py-3 text-slate-500">{new Date(rcp.issued_at).toLocaleString()}</td>
                    <td className="px-4 py-3 font-bold text-slate-900 dark:text-white">
                      {formatCurrency(rcp.amount_paid)}
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 dark:bg-slate-800">
                        {rcp.payment_mode}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-500">{rcp.transaction_reference}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => setSelectedReceipt(rcp)}
                        className="text-xs font-semibold text-emerald-600 hover:text-emerald-700 dark:text-emerald-400"
                      >
                        View Voucher
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Official Receipt Voucher Modal */}
      {selectedReceipt && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs overflow-y-auto">
          <div className="w-full max-w-xl rounded-2xl bg-white p-8 shadow-2xl dark:bg-slate-900 border border-slate-200 dark:border-slate-800 my-8">
            {/* Printable Voucher Card */}
            <div id="printable-voucher" className="border-2 border-slate-900/10 dark:border-slate-700 p-6 rounded-xl bg-slate-50/50 dark:bg-slate-800/40">
              {/* Institution Header */}
              <div className="text-center border-b border-slate-200 pb-4 dark:border-slate-700">
                <h2 className="text-lg font-bold tracking-tight text-slate-900 dark:text-white uppercase">
                  {selectedReceipt.institution_legal_name || "CampusOS Academic Institution"}
                </h2>
                <p className="text-xs text-slate-500">{selectedReceipt.institution_address || "Central Campus"}</p>
                <div className="mt-2 inline-block rounded-full bg-emerald-100 px-3 py-0.5 text-xs font-bold text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                  OFFICIAL PAYMENT RECEIPT
                </div>
              </div>

              {/* Receipt Metadata */}
              <div className="mt-4 grid grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-slate-400">Receipt No:</span>
                  <p className="font-mono font-bold text-slate-900 dark:text-white text-sm">
                    {selectedReceipt.receipt_number}
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-slate-400">Date Issued:</span>
                  <p className="font-medium text-slate-900 dark:text-white">
                    {new Date(selectedReceipt.issued_at).toLocaleDateString()}
                  </p>
                </div>
              </div>

              {/* Student Particulars */}
              <div className="mt-4 border-t border-slate-200/80 pt-3 dark:border-slate-700 text-xs">
                <span className="text-slate-400">Received With Thanks From:</span>
                <p className="font-bold text-slate-900 dark:text-white text-sm mt-0.5">
                  {selectedReceipt.student_name || "Enrolled Student"}
                </p>
                <p className="text-slate-500 font-mono">Admission No: {selectedReceipt.student_admission_number || "—"}</p>
              </div>

              {/* Payment Details */}
              <div className="mt-4 bg-white p-4 rounded-lg border border-slate-200 dark:bg-slate-800 dark:border-slate-700 space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-500">Amount Paid:</span>
                  <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400 text-base">
                    {formatCurrency(selectedReceipt.amount_paid)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Payment Mode:</span>
                  <span className="font-medium text-slate-900 dark:text-white">{selectedReceipt.payment_mode}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Transaction Reference:</span>
                  <span className="font-mono text-slate-700 dark:text-slate-300">{selectedReceipt.transaction_reference}</span>
                </div>
                {selectedReceipt.payment_number && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Payment Voucher:</span>
                    <span className="font-mono text-slate-700 dark:text-slate-300">{selectedReceipt.payment_number}</span>
                  </div>
                )}
              </div>

              {/* Signatures & Seal */}
              <div className="mt-8 pt-4 border-t border-dashed border-slate-300 dark:border-slate-700 flex justify-between items-end text-[10px] text-slate-400">
                <div>
                  <p>Computer Generated Forensic Receipt</p>
                  <p>CampusOS Finance Core v8.0</p>
                </div>
                <div className="text-center">
                  <div className="w-28 border-b border-slate-400 mb-1" />
                  <p className="font-semibold text-slate-600 dark:text-slate-300">Authorized Signatory</p>
                </div>
              </div>
            </div>

            {/* Modal Buttons */}
            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={handlePrint}
                className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-emerald-700"
              >
                Print / Save PDF
              </button>
              <button
                type="button"
                onClick={() => setSelectedReceipt(null)}
                className="rounded-lg border border-slate-300 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
