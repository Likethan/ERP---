"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  CreditCard,
  ArrowLeft,
  Printer,
  DollarSign,
  Receipt,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Ban,
  Calendar,
  Gift,
  History,
  Building,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/toast";
import { financeService } from "@/services/finance.service";
import { formatMoney } from "@/services/financial-calculator";
import { Invoice, PaymentMethod, InvoiceStatus } from "@/types/finance";

export default function InvoiceDetailPage() {
  const params = useParams();
  const { showToast } = useToast();
  const invoiceId = params.id as string;

  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [loading, setLoading] = useState(true);

  // Record Payment Modal State
  const [payModalOpen, setPayModalOpen] = useState(false);
  const [payAmount, setPayAmount] = useState<number>(0);
  const [payMethod, setPayMethod] = useState<PaymentMethod>("UPI");
  const [payReference, setPayReference] = useState("");
  const [payNotes, setPayNotes] = useState("");
  const [recordingPay, setRecordingPay] = useState(false);

  // Cancel Invoice Modal State
  const [cancelModalOpen, setCancelModalOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState("");
  const [cancelling, setCancelling] = useState(false);

  const loadData = async () => {
    if (!invoiceId) return;
    try {
      setLoading(true);
      const res = await financeService.getInvoiceById(invoiceId);
      setInvoice(res.data);
      if (res.data) {
        setPayAmount(res.data.outstandingAmount);
      }
    } catch (err: unknown) {
      showToast({
        title: "Error Loading Invoice",
        message: err instanceof Error ? err.message : "Unable to retrieve invoice",
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [invoiceId]);

  const handleRecordPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!invoice) return;

    if (payAmount <= 0) {
      showToast({ title: "Validation Error", message: "Enter a positive amount.", type: "error" });
      return;
    }

    if (payAmount > invoice.outstandingAmount) {
      showToast({
        title: "Validation Error",
        message: `Amount cannot exceed outstanding balance of ${formatMoney(invoice.outstandingAmount)}.`,
        type: "error",
      });
      return;
    }

    try {
      setRecordingPay(true);
      const res = await financeService.recordPayment({
        invoiceId: invoice.id,
        amount: payAmount,
        paymentMethod: payMethod,
        referenceNumber: payReference,
        notes: payNotes,
      });

      showToast({
        title: "Payment Recorded",
        message: `₹${res.data.payment.amount.toLocaleString()} received via ${res.data.payment.paymentMethod}. Issued receipt ${res.data.receipt.receiptNumber}.`,
        type: "success",
      });
      setPayModalOpen(false);
      loadData();
    } catch (err: unknown) {
      showToast({
        title: "Payment Failed",
        message: err instanceof Error ? err.message : "Unable to record payment",
        type: "error",
      });
    } finally {
      setRecordingPay(false);
    }
  };

  const handleCancelInvoice = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!invoice) return;

    if (!cancelReason.trim()) {
      showToast({ title: "Validation Error", message: "Provide reason for cancellation.", type: "error" });
      return;
    }

    try {
      setCancelling(true);
      await financeService.cancelInvoice(invoice.id, cancelReason.trim());
      showToast({ title: "Invoice Cancelled", message: "Invoice status marked as CANCELLED.", type: "info" });
      setCancelModalOpen(false);
      loadData();
    } catch (err: unknown) {
      showToast({
        title: "Cancellation Blocked",
        message: err instanceof Error ? err.message : "Error cancelling invoice",
        type: "error",
      });
    } finally {
      setCancelling(false);
    }
  };

  if (loading) {
    return (
      <div className="py-20 text-center text-slate-400">
        <p className="text-sm">Retrieving invoice details...</p>
      </div>
    );
  }

  if (!invoice) {
    return (
      <div className="py-20 text-center space-y-3">
        <p className="text-base font-semibold text-slate-200">Invoice Not Found</p>
        <Link href="/app/finance/invoices">
          <Button variant="outline" size="sm">
            Back to Invoices
          </Button>
        </Link>
      </div>
    );
  }

  const getStatusBadge = (status: InvoiceStatus) => {
    switch (status) {
      case "PAID":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">PAID IN FULL</span>;
      case "PARTIALLY_PAID":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">PARTIALLY PAID</span>;
      case "ISSUED":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">ISSUED</span>;
      case "OVERDUE":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">OVERDUE</span>;
      case "DRAFT":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700/60">DRAFT</span>;
      case "CANCELLED":
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-500 border border-slate-700/60 line-through">CANCELLED</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-5 print:hidden">
        <div>
          <Link
            href="/app/finance/invoices"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-slate-200 mb-2"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Invoices Ledger
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <CreditCard className="h-6 w-6 text-indigo-400" />
              Invoice {invoice.invoiceNumber}
            </h1>
            {getStatusBadge(invoice.status)}
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.print()}
            className="gap-1.5 text-xs text-slate-300"
          >
            <Printer className="h-3.5 w-3.5" />
            Print Preview
          </Button>

          {invoice.status !== "PAID" && invoice.status !== "CANCELLED" && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                setPayAmount(invoice.outstandingAmount);
                setPayModalOpen(true);
              }}
              className="gap-1.5 text-xs"
            >
              <DollarSign className="h-3.5 w-3.5" />
              Record Payment
            </Button>
          )}

          {invoice.receiptIds.length > 0 && (
            <Link href={`/app/finance/receipts/${invoice.receiptIds[0]}`}>
              <Button variant="outline" size="sm" className="gap-1.5 text-xs text-emerald-400 border-emerald-500/30">
                <Receipt className="h-3.5 w-3.5" />
                View Receipt
              </Button>
            </Link>
          )}

          {invoice.paidAmount === 0 && invoice.status !== "CANCELLED" && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setCancelModalOpen(true)}
              className="text-xs text-rose-400 hover:text-rose-300 hover:bg-rose-500/10"
            >
              <Ban className="h-3.5 w-3.5 mr-1" />
              Cancel Invoice
            </Button>
          )}
        </div>
      </div>

      {/* Official Print-Ready Invoice Sheet */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6 shadow-xl print:border-none print:shadow-none print:bg-white print:text-black">
        {/* Institutional Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start border-b border-slate-800 pb-6 print:border-black">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Building className="h-6 w-6 text-indigo-400 print:text-black" />
              <h2 className="text-xl font-bold tracking-tight text-white print:text-black">
                CampusOS Institute of Technology
              </h2>
            </div>
            <p className="text-xs text-slate-400 print:text-gray-600">
              Autonomous Engineering College • Affiliated with University Board
            </p>
            <p className="text-xs text-slate-400 print:text-gray-600">
              Campus Road, Technology Park, Bengaluru 560100
            </p>
          </div>

          <div className="mt-4 sm:mt-0 text-left sm:text-right space-y-1">
            <h3 className="text-sm font-bold uppercase tracking-wider text-indigo-400 print:text-black">
              FEE INVOICE
            </h3>
            <p className="font-mono text-base font-bold text-white print:text-black">{invoice.invoiceNumber}</p>
            <p className="text-xs text-slate-400 print:text-gray-600">Issued Date: {invoice.issueDate}</p>
            <p className="text-xs font-semibold text-rose-400 print:text-black">Due Date: {invoice.dueDate}</p>
          </div>
        </div>

        {/* Student & Billing Section */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 print:bg-gray-50 print:border-gray-300">
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Billed To (Candidate):</h4>
            <p className="text-sm font-bold text-white print:text-black">{invoice.studentName}</p>
            <p className="text-xs font-mono text-indigo-400 print:text-black">Roll No: {invoice.rollNumber}</p>
            <p className="text-xs text-slate-300 print:text-gray-700 mt-1">{invoice.program}</p>
            <p className="text-xs text-slate-400 print:text-gray-600">{invoice.department}</p>
          </div>

          <div className="space-y-1 text-xs sm:text-right">
            <h4 className="font-bold uppercase tracking-wider text-slate-400 mb-2">Billing Term:</h4>
            <p className="text-slate-300 print:text-gray-700">Academic Year: {invoice.academicYear}</p>
            <p className="text-slate-300 print:text-gray-700">Semester Term: Semester {invoice.semester}</p>
            <div className="pt-2">
              <span className="text-slate-400 mr-2">Current Status:</span>
              <span className="font-bold text-white print:text-black">{invoice.status}</span>
            </div>
          </div>
        </div>

        {/* Line Items Table */}
        <div className="rounded-xl border border-slate-800 overflow-hidden print:border-gray-300">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 font-semibold print:bg-gray-100 print:text-black">
              <tr>
                <th className="py-2.5 px-4">#</th>
                <th className="py-2.5 px-4">Fee Head / Description</th>
                <th className="py-2.5 px-4">Category</th>
                <th className="py-2.5 px-4 text-center">Qty</th>
                <th className="py-2.5 px-4 text-right">Unit Rate</th>
                <th className="py-2.5 px-4 text-right">Total Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 print:divide-gray-200">
              {invoice.lines.map((line, idx) => (
                <tr key={line.id} className="hover:bg-slate-800/30 print:hover:bg-transparent">
                  <td className="py-2.5 px-4 font-mono text-slate-500">{idx + 1}</td>
                  <td className="py-2.5 px-4 font-medium text-slate-200 print:text-black">{line.title}</td>
                  <td className="py-2.5 px-4 text-slate-400 print:text-gray-600">{line.categoryName}</td>
                  <td className="py-2.5 px-4 text-center text-slate-300 print:text-black">{line.quantity}</td>
                  <td className="py-2.5 px-4 text-right font-mono text-slate-300 print:text-black">{formatMoney(line.unitAmount)}</td>
                  <td className="py-2.5 px-4 text-right font-mono font-semibold text-slate-200 print:text-black">
                    {formatMoney(line.totalAmount)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Financial Calculation Summary Breakdown */}
        <div className="flex flex-col sm:flex-row justify-between items-start gap-6 pt-2">
          <div className="text-xs text-slate-400 space-y-1 max-w-sm">
            <p className="font-semibold text-slate-300 print:text-black">Payment Terms & Notes:</p>
            <p className="text-[11px] leading-relaxed">
              1. Fee settlement must be realized prior to due date to avoid semester registration hold.
              2. For fee concessions, verified scholarship entitlement order must be endorsed by Dean Office.
            </p>
          </div>

          <div className="w-full sm:w-80 space-y-2 bg-slate-950/60 p-4 rounded-xl border border-slate-800 text-xs print:bg-transparent print:border-gray-300">
            <div className="flex justify-between py-1">
              <span className="text-slate-400 print:text-gray-600">Gross Fee Total:</span>
              <span className="font-mono text-slate-200 print:text-black">{formatMoney(invoice.grossAmount)}</span>
            </div>

            {invoice.scholarshipAmount > 0 && (
              <div className="flex justify-between py-1 text-cyan-400 print:text-black">
                <span>Scholarship Concession:</span>
                <span className="font-mono">-{formatMoney(invoice.scholarshipAmount)}</span>
              </div>
            )}

            {invoice.discountAmount > 0 && (
              <div className="flex justify-between py-1 text-cyan-400 print:text-black">
                <span>Institutional Waiver / Discount:</span>
                <span className="font-mono">-{formatMoney(invoice.discountAmount)}</span>
              </div>
            )}

            {invoice.adjustmentAmount !== 0 && (
              <div className="flex justify-between py-1 text-slate-400">
                <span>Adjustments:</span>
                <span className="font-mono">{formatMoney(invoice.adjustmentAmount)}</span>
              </div>
            )}

            <div className="flex justify-between py-1.5 border-t border-slate-800 font-semibold text-sm">
              <span className="text-white print:text-black">Net Amount Payable:</span>
              <span className="font-mono text-slate-100 print:text-black">{formatMoney(invoice.netPayable)}</span>
            </div>

            <div className="flex justify-between py-1 text-emerald-400 print:text-black">
              <span>Total Paid & Cleared:</span>
              <span className="font-mono font-semibold">{formatMoney(invoice.paidAmount)}</span>
            </div>

            <div className="flex justify-between py-2 border-t border-slate-800 font-bold text-sm">
              <span className="text-rose-400 print:text-black">Outstanding Balance Due:</span>
              <span className="font-mono text-rose-400 print:text-black text-base">
                {formatMoney(invoice.outstandingAmount)}
              </span>
            </div>
          </div>
        </div>

        {/* Audit History Timeline */}
        <div className="pt-4 border-t border-slate-800 print:hidden space-y-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <History className="h-4 w-4" />
            Invoice Transaction & Lifecycle Audit Trail
          </h4>

          <div className="space-y-2">
            {invoice.history.map((h) => (
              <div
                key={h.id}
                className="flex items-center justify-between p-2 rounded-lg bg-slate-950 border border-slate-800/80 text-xs"
              >
                <div>
                  <span className="font-semibold text-slate-200">{h.action}</span>
                  <span className="text-slate-500 mx-2">•</span>
                  <span className="text-slate-400">{h.notes || `Processed by ${h.actor}`}</span>
                </div>
                <span className="text-[11px] text-slate-500 font-mono">
                  {new Date(h.timestamp).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Record Payment Dialog */}
      <Dialog open={payModalOpen} onOpenChange={setPayModalOpen}>
        <DialogContent className="max-w-md bg-slate-900 border-slate-800 text-slate-200">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold text-white flex items-center gap-2">
              <DollarSign className="h-5 w-5 text-emerald-400" />
              Record Student Payment
            </DialogTitle>
          </DialogHeader>

          <form onSubmit={handleRecordPayment} className="space-y-4 py-2">
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-1">
              <div className="flex justify-between">
                <span className="text-slate-400">Student:</span>
                <span className="font-medium text-slate-200">{invoice.studentName} ({invoice.rollNumber})</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Invoice:</span>
                <span className="font-mono text-indigo-400">{invoice.invoiceNumber}</span>
              </div>
              <div className="flex justify-between font-bold pt-1 border-t border-slate-800">
                <span className="text-slate-300">Remaining Balance:</span>
                <span className="font-mono text-rose-400">{formatMoney(invoice.outstandingAmount)}</span>
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Payment Amount (₹) <span className="text-rose-400">*</span>
              </label>
              <Input
                type="number"
                min="1"
                max={invoice.outstandingAmount}
                required
                value={payAmount.toString()}
                onChange={(e) => setPayAmount(parseFloat(e.target.value) || 0)}
                className="h-8 text-xs font-mono bg-slate-950 border-slate-800 text-emerald-400 font-bold"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Payment Channel / Mode <span className="text-rose-400">*</span>
              </label>
              <Select
                value={payMethod}
                onChange={(e) => setPayMethod(e.target.value as PaymentMethod)}
                className="h-8 text-xs bg-slate-950 border-slate-800"
              >
                <option value="UPI">UPI (Google Pay, PhonePe, Paytm)</option>
                <option value="BANK_TRANSFER">Bank Transfer / NEFT / RTGS</option>
                <option value="CARD">Debit / Credit Card Counter</option>
                <option value="CASH">Institutional Cash Counter</option>
                <option value="CHEQUE">Cheque / Demand Draft</option>
              </Select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Transaction Reference / Receipt ID
              </label>
              <Input
                placeholder="UTR number, cheque number, or counter receipt"
                value={payReference}
                onChange={(e) => setPayReference(e.target.value)}
                className="h-8 text-xs font-mono bg-slate-950 border-slate-800"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Cashier Remarks
              </label>
              <Textarea
                rows={2}
                value={payNotes}
                onChange={(e) => setPayNotes(e.target.value)}
                placeholder="Receipt notes, installment agreement, etc."
                className="text-xs bg-slate-950 border-slate-800"
              />
            </div>

            <DialogFooter className="pt-3 border-t border-slate-800">
              <Button type="button" variant="outline" size="sm" onClick={() => setPayModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm" disabled={recordingPay}>
                {recordingPay ? "Committing..." : `Confirm Payment (${formatMoney(payAmount)})`}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Cancel Invoice Dialog */}
      <Dialog open={cancelModalOpen} onOpenChange={setCancelModalOpen}>
        <DialogContent className="max-w-md bg-slate-900 border-slate-800 text-slate-200">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold text-white flex items-center gap-2">
              <Ban className="h-5 w-5 text-rose-400" />
              Cancel Invoice {invoice.invoiceNumber}
            </DialogTitle>
          </DialogHeader>

          <form onSubmit={handleCancelInvoice} className="space-y-4 py-2">
            <p className="text-xs text-slate-400">
              Cancelling this invoice will permanently withdraw it from the candidate's account and void any outstanding balance.
            </p>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Reason for Cancellation <span className="text-rose-400">*</span>
              </label>
              <Textarea
                required
                rows={3}
                value={cancelReason}
                onChange={(e) => setCancelReason(e.target.value)}
                placeholder="e.g. Duplicate billing, course withdrawal, quota re-assignment..."
                className="text-xs bg-slate-950 border-slate-800"
              />
            </div>

            <DialogFooter className="pt-3 border-t border-slate-800">
              <Button type="button" variant="outline" size="sm" onClick={() => setCancelModalOpen(false)}>
                Go Back
              </Button>
              <Button type="submit" variant="destructive" size="sm" disabled={cancelling}>
                {cancelling ? "Cancelling..." : "Confirm Cancellation"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
