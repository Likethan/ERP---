"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import {
  Printer,
  ArrowLeft,
  CheckCircle2,
  FileText,
  CreditCard,
  Building2,
  ShieldCheck,
  QrCode,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { financeService } from "@/services/finance.service";
import { formatMoney } from "@/services/financial-calculator";
import { Receipt } from "@/types/finance";

export default function ReceiptDetailPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const receiptId = params?.id as string;
  const shouldPrint = searchParams?.get("print") === "true";

  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadReceipt() {
      if (!receiptId) return;
      try {
        setLoading(true);
        setError(null);
        const res = await financeService.getReceiptById(receiptId);
        setReceipt(res.data);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Receipt voucher not found.");
      } finally {
        setLoading(false);
      }
    }
    loadReceipt();
  }, [receiptId]);

  useEffect(() => {
    if (receipt && shouldPrint) {
      setTimeout(() => {
        window.print();
      }, 500);
    }
  }, [receipt, shouldPrint]);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-sm text-slate-500">Retrieving official fee receipt voucher...</div>
      </div>
    );
  }

  if (error || !receipt) {
    return (
      <div className="space-y-4">
        <Link href="/app/finance/receipts">
          <Button variant="ghost" size="sm" className="gap-1.5 text-xs">
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Receipts Archive
          </Button>
        </Link>
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-6 text-center text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-300">
          <h2 className="text-lg font-bold">Receipt Voucher Unavailable</h2>
          <p className="mt-1 text-sm">{error || "Receipt voucher not found."}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Top action toolbar (hidden during print) */}
      <div className="print:hidden flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 mb-1">
            <Link href="/app/finance" className="hover:text-emerald-600 transition">
              Finance Hub
            </Link>
            <span>/</span>
            <Link href="/app/finance/receipts" className="hover:text-emerald-600 transition">
              Receipts
            </Link>
            <span>/</span>
            <span className="font-semibold text-slate-700 dark:text-slate-300">
              {receipt.receiptNumber}
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Official Money Receipt
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Validated electronic receipt voucher with institutional security seal.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href={`/app/finance/invoices/${receipt.invoiceId}`}>
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              <FileText className="w-3.5 h-3.5" />
              View Invoice
            </Button>
          </Link>
          <Link href={`/app/finance/payments/${receipt.paymentId}`}>
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              <CreditCard className="w-3.5 h-3.5" />
              View Payment
            </Button>
          </Link>
          <Button
            variant="primary"
            size="sm"
            onClick={() => window.print()}
            className="gap-1.5 text-xs bg-emerald-600 hover:bg-emerald-700 text-white"
          >
            <Printer className="w-3.5 h-3.5" />
            Print Receipt
          </Button>
        </div>
      </div>

      {/* Print-Ready Official Receipt Card */}
      <div className="bg-white rounded-2xl border-2 border-slate-300 p-8 shadow-sm dark:bg-slate-900 dark:border-slate-700 print:border-none print:shadow-none print:p-0">
        {/* Header Institution Brand */}
        <div className="flex justify-between items-start border-b-2 border-slate-800 pb-6 dark:border-slate-200">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-xl bg-emerald-700 text-white flex items-center justify-center font-bold text-2xl shadow-sm print:border print:border-slate-800">
              COS
            </div>
            <div>
              <h2 className="text-xl font-black tracking-tight text-slate-900 uppercase dark:text-white">
                CampusOS Institute of Technology
              </h2>
              <p className="text-xs text-slate-600 dark:text-slate-400 font-medium">
                Deemed-to-be University • Accredited A++ Grade • Finance & Accounts Division
              </p>
              <p className="text-xs text-slate-500 mt-0.5">
                Campus Central Road, Knowledge City, Bangalore, KA 560064
              </p>
            </div>
          </div>

          <div className="text-right">
            <span className="inline-block bg-slate-900 text-white text-xs font-black uppercase tracking-wider px-3 py-1 rounded dark:bg-white dark:text-slate-900">
              Money Receipt Voucher
            </span>
            <div className="mt-2 text-sm font-mono font-bold text-emerald-700 dark:text-emerald-400">
              {receipt.receiptNumber}
            </div>
            <div className="text-xs text-slate-500 mt-0.5">Date: {receipt.date}</div>
          </div>
        </div>

        {/* Candidate & Transaction Meta Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 py-6 border-b border-slate-200 text-xs dark:border-slate-800">
          <div>
            <span className="text-slate-500 uppercase font-semibold text-[10px] tracking-wider">
              Student Name
            </span>
            <p className="text-sm font-bold text-slate-900 dark:text-white mt-0.5">
              {receipt.studentName}
            </p>
            <p className="text-slate-500 font-mono mt-0.5">{receipt.rollNumber}</p>
          </div>

          <div>
            <span className="text-slate-500 uppercase font-semibold text-[10px] tracking-wider">
              Academic Program
            </span>
            <p className="font-semibold text-slate-900 dark:text-white mt-0.5">
              {receipt.program}
            </p>
            <p className="text-slate-500 mt-0.5">{receipt.department}</p>
          </div>

          <div>
            <span className="text-slate-500 uppercase font-semibold text-[10px] tracking-wider">
              Transaction Ref / UTR
            </span>
            <p className="font-mono font-semibold text-slate-900 dark:text-white mt-0.5">
              {receipt.transactionRef}
            </p>
            <p className="text-slate-500 mt-0.5">Mode: {receipt.paymentMethod.replace("_", " ")}</p>
          </div>

          <div>
            <span className="text-slate-500 uppercase font-semibold text-[10px] tracking-wider">
              Settled Invoice
            </span>
            <p className="font-mono font-semibold text-blue-600 dark:text-blue-400 mt-0.5">
              {receipt.invoiceNumber}
            </p>
            <p className="text-slate-500 mt-0.5">Status: Verified</p>
          </div>
        </div>

        {/* Settlement Breakdown Table */}
        <div className="py-6 border-b border-slate-200 dark:border-slate-800">
          <table className="w-full text-xs text-left">
            <thead>
              <tr className="border-b border-slate-300 text-slate-500 uppercase font-bold text-[10px] dark:border-slate-700">
                <th className="py-2">Description / Particulars</th>
                <th className="py-2">Payment Instrument</th>
                <th className="py-2 text-right">Settled Amount (INR)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              <tr>
                <td className="py-3 font-medium text-slate-900 dark:text-white">
                  Institutional Fee Settlement against {receipt.invoiceNumber}
                  <div className="text-slate-500 text-[11px] mt-0.5">
                    {receipt.notes || "Official institutional fee payment"}
                  </div>
                </td>
                <td className="py-3 font-mono text-slate-700 dark:text-slate-300">
                  {receipt.paymentMethod.replace("_", " ")} ({receipt.transactionRef})
                </td>
                <td className="py-3 text-right font-bold text-slate-900 dark:text-white text-sm">
                  {formatMoney(receipt.amount)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Total Box */}
        <div className="flex flex-col sm:flex-row justify-between items-center py-6 border-b-2 border-slate-800 dark:border-slate-200 gap-4">
          <div className="text-xs text-slate-600 dark:text-slate-400">
            <span className="font-bold text-slate-900 dark:text-white uppercase">Amount in Words: </span>
            <span className="italic">
              Official electronic settlement voucher for institutional tuition and fee structure.
            </span>
          </div>

          <div className="bg-emerald-50 border-2 border-emerald-500 rounded-xl px-6 py-3 text-right dark:bg-emerald-950/40">
            <div className="text-[10px] uppercase font-bold tracking-wider text-emerald-800 dark:text-emerald-300">
              Net Amount Paid
            </div>
            <div className="text-2xl font-black text-emerald-700 dark:text-emerald-400">
              {formatMoney(receipt.amount)}
            </div>
          </div>
        </div>

        {/* Signatures & Security Stamp */}
        <div className="pt-10 flex flex-col sm:flex-row justify-between items-end gap-8 text-xs text-slate-500">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-emerald-600 font-semibold dark:text-emerald-400">
              <CheckCircle2 className="w-4 h-4" />
              Digitally Verified by CampusOS Finance Engine
            </div>
            <p className="text-[11px]">Recorded by: {receipt.recordedBy}</p>
            <p className="text-[11px]">Security Hash: SHA256-VOUCHER-{receipt.id.toUpperCase()}</p>
          </div>

          <div className="flex items-center gap-8">
            <div className="text-center">
              <div className="w-32 border-b border-slate-400 pb-1 mb-1 font-mono text-[10px] text-slate-400">
                [DIGITAL SEAL]
              </div>
              <p className="text-[11px] font-medium text-slate-700 dark:text-slate-300">
                Cashier / Accounts Officer
              </p>
            </div>

            <div className="p-2 border border-slate-300 rounded-lg dark:border-slate-700">
              <QrCode className="w-12 h-12 text-slate-700 dark:text-slate-300" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
