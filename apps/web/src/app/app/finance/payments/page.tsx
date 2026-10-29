"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  CreditCard,
  Plus,
  Search,
  Filter,
  ArrowRight,
  Eye,
  Calendar,
  CheckCircle2,
  DollarSign,
  FileText,
  Clock,
  Ban,
  Building2,
  ShieldCheck,
  Receipt as ReceiptIcon,
} from "lucide-react";
import { DataGrid, ColumnDef } from "@/components/data-grid/data-grid";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/ui/stat-card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { useToast, ToastType } from "@/components/ui/toast";
import { useAuth } from "@/lib/auth-context";
import { financeService } from "@/services/finance.service";
import { formatMoney } from "@/services/financial-calculator";
import { Payment, PaymentMethod, Invoice } from "@/types/finance";
import { MOCK_STUDENTS } from "@/mocks/students.mock";

export default function PaymentsPage() {
  const { hasPermission } = useAuth();
  const { showToast } = useToast();
  const notify = (title: string, type: ToastType = "info") =>
    showToast({ title, type });

  const [payments, setPayments] = useState<Payment[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [methodFilter, setMethodFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // Record Payment Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedStudentId, setSelectedStudentId] = useState("");
  const [selectedInvoiceId, setSelectedInvoiceId] = useState("");
  const [paymentAmount, setPaymentAmount] = useState<number>(0);
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("UPI");
  const [referenceNumber, setReferenceNumber] = useState("");
  const [bankName, setBankName] = useState("");
  const [chequeNumber, setChequeNumber] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);

  const canRecord =
    hasPermission("finance.record_payments") ||
    hasPermission("payments:create");

  const loadData = async () => {
    try {
      setLoading(true);
      const [payRes, invRes] = await Promise.all([
        financeService.getPayments(),
        financeService.getInvoices(),
      ]);
      setPayments(payRes.data);
      setInvoices(invRes.data);
    } catch {
      notify("Error loading payment transaction ledger", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Filtered unpaid invoices for selected student in modal
  const studentPayableInvoices = useMemo(() => {
    if (!selectedStudentId) return [];
    return invoices.filter(
      (inv) =>
        (inv.studentId === selectedStudentId ||
          inv.studentName
            .toLowerCase()
            .includes(selectedStudentId.toLowerCase())) &&
        inv.outstandingAmount > 0 &&
        inv.status !== "CANCELLED",
    );
  }, [selectedStudentId, invoices]);

  const selectedInvoice = useMemo(() => {
    return invoices.find((inv) => inv.id === selectedInvoiceId);
  }, [selectedInvoiceId, invoices]);

  // When selected student changes, pick their first unpaid invoice
  const handleStudentSelect = (studentId: string) => {
    setSelectedStudentId(studentId);
    const payable = invoices.filter(
      (inv) =>
        (inv.studentId === studentId ||
          inv.studentName.toLowerCase().includes(studentId.toLowerCase())) &&
        inv.outstandingAmount > 0 &&
        inv.status !== "CANCELLED",
    );
    if (payable.length > 0) {
      setSelectedInvoiceId(payable[0].id);
      setPaymentAmount(payable[0].outstandingAmount);
    } else {
      setSelectedInvoiceId("");
      setPaymentAmount(0);
    }
  };

  const handleInvoiceSelect = (invId: string) => {
    setSelectedInvoiceId(invId);
    const target = invoices.find((inv) => inv.id === invId);
    if (target) {
      setPaymentAmount(target.outstandingAmount);
    }
  };

  // Submit payment
  const handleRecordPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedInvoice) {
      notify("Please choose an invoice to allocate payment against.", "error");
      return;
    }
    if (paymentAmount <= 0) {
      notify("Payment amount must be greater than zero.", "error");
      return;
    }
    if (paymentAmount > selectedInvoice.outstandingAmount) {
      notify(
        `Amount (${formatMoney(paymentAmount)}) exceeds invoice outstanding balance of ${formatMoney(selectedInvoice.outstandingAmount)}.`,
        "error",
      );
      return;
    }
    if (!referenceNumber.trim()) {
      notify("Transaction reference / UTR is required.", "error");
      return;
    }

    try {
      setSubmitting(true);
      await financeService.recordPayment({
        invoiceId: selectedInvoice.id,
        amount: Number(paymentAmount),
        paymentMethod,
        referenceNumber: referenceNumber.trim(),
        bankName: bankName.trim() || undefined,
        chequeNumber: chequeNumber.trim() || undefined,
        notes: notes.trim() || undefined,
        recordedBy: "Accounts Cashier",
      });

      notify(
        `Payment of ${formatMoney(paymentAmount)} recorded successfully!`,
        "success",
      );
      setModalOpen(false);
      setIsConfirming(false);
      setSelectedStudentId("");
      setSelectedInvoiceId("");
      setPaymentAmount(0);
      setReferenceNumber("");
      setBankName("");
      setChequeNumber("");
      setNotes("");
      loadData();
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Failed to record payment.";
      notify(msg, "error");
    } finally {
      setSubmitting(false);
    }
  };

  // Computed metrics
  const totalCollected = useMemo(() => {
    return payments
      .filter((p) => p.status === "SUCCESS")
      .reduce((sum, p) => sum + p.amount, 0);
  }, [payments]);

  const upiCollected = useMemo(() => {
    return payments
      .filter((p) => p.status === "SUCCESS" && p.paymentMethod === "UPI")
      .reduce((sum, p) => sum + p.amount, 0);
  }, [payments]);

  const bankWireCollected = useMemo(() => {
    return payments
      .filter(
        (p) => p.status === "SUCCESS" && p.paymentMethod === "BANK_TRANSFER",
      )
      .reduce((sum, p) => sum + p.amount, 0);
  }, [payments]);

  const cashChequeCollected = useMemo(() => {
    return payments
      .filter(
        (p) =>
          p.status === "SUCCESS" &&
          (p.paymentMethod === "CASH" || p.paymentMethod === "CHEQUE"),
      )
      .reduce((sum, p) => sum + p.amount, 0);
  }, [payments]);

  // Filtered rows
  const filteredPayments = useMemo(() => {
    return payments.filter((p) => {
      const matchesSearch =
        searchQuery === "" ||
        p.transactionRef.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.studentName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.rollNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.invoiceNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.receiptNumber.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesMethod =
        methodFilter === "ALL" || p.paymentMethod === methodFilter;
      const matchesStatus = statusFilter === "ALL" || p.status === statusFilter;

      return matchesSearch && matchesMethod && matchesStatus;
    });
  }, [payments, searchQuery, methodFilter, statusFilter]);

  const columns: ColumnDef<Payment>[] = [
    {
      id: "transactionRef",
      header: "Transaction Ref / UTR",
      accessorKey: "transactionRef",
      sortable: true,
      cell: ({ row }) => (
        <div>
          <Link
            href={`/app/finance/payments/${row.id}`}
            className="font-mono text-sm font-semibold text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 hover:underline"
          >
            {row.transactionRef}
          </Link>
          <div className="text-xs text-slate-500 font-mono">
            Rec: {row.receiptNumber}
          </div>
        </div>
      ),
    },
    {
      id: "student",
      header: "Student",
      accessorKey: "studentName",
      sortable: true,
      cell: ({ row }) => (
        <div>
          <div className="font-medium text-slate-900 dark:text-white">
            {row.studentName}
          </div>
          <div className="text-xs text-slate-500 font-mono">
            {row.rollNumber}
          </div>
        </div>
      ),
    },
    {
      id: "invoiceNumber",
      header: "Invoice",
      accessorKey: "invoiceNumber",
      sortable: true,
      cell: ({ row }) => (
        <Link
          href={`/app/finance/invoices/${row.invoiceId}`}
          className="text-xs font-mono font-medium text-blue-600 hover:underline dark:text-blue-400"
        >
          {row.invoiceNumber}
        </Link>
      ),
    },
    {
      id: "paymentDate",
      header: "Date & Time",
      accessorKey: "paymentDate",
      sortable: true,
      cell: ({ row }) => (
        <span className="text-xs text-slate-600 dark:text-slate-300">
          {row.paymentDate}
        </span>
      ),
    },
    {
      id: "paymentMethod",
      header: "Method",
      accessorKey: "paymentMethod",
      cell: ({ row }) => {
        const colors: Record<string, string> = {
          UPI: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/50 dark:text-emerald-300",
          BANK_TRANSFER:
            "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/50 dark:text-blue-300",
          CARD: "bg-indigo-50 text-indigo-700 border-indigo-200 dark:bg-indigo-950/50 dark:text-indigo-300",
          CASH: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/50 dark:text-amber-300",
          CHEQUE:
            "bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/50 dark:text-purple-300",
          ONLINE:
            "bg-teal-50 text-teal-700 border-teal-200 dark:bg-teal-950/50 dark:text-teal-300",
          OTHER:
            "bg-slate-50 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300",
        };
        return (
          <span
            className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border ${
              colors[row.paymentMethod] || "bg-slate-100 text-slate-700"
            }`}
          >
            {row.paymentMethod.replace("_", " ")}
          </span>
        );
      },
    },
    {
      id: "amount",
      header: "Amount",
      accessorKey: "amount",
      sortable: true,
      cell: ({ row }) => (
        <span className="font-semibold text-slate-900 dark:text-white">
          {formatMoney(row.amount)}
        </span>
      ),
    },
    {
      id: "allocation",
      header: "Allocation",
      cell: ({ row }) => (
        <div className="text-xs">
          <span className="font-medium text-emerald-700 dark:text-emerald-400">
            {formatMoney(row.allocatedAmount)}
          </span>
          {row.unallocatedAmount > 0 && (
            <span className="ml-1.5 text-amber-600 dark:text-amber-400">
              ({formatMoney(row.unallocatedAmount)} unallocated)
            </span>
          )}
        </div>
      ),
    },
    {
      id: "status",
      header: "Status",
      accessorKey: "status",
      cell: ({ row }) => {
        const badges: Record<string, string> = {
          SUCCESS:
            "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300",
          PENDING:
            "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300",
          FAILED:
            "bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300",
          REVERSED:
            "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300",
        };
        return (
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
              badges[row.status] || "bg-slate-100 text-slate-700"
            }`}
          >
            {row.status}
          </span>
        );
      },
    },
    {
      id: "actions",
      header: "Actions",
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <Link href={`/app/finance/payments/${row.id}`}>
            <Button variant="ghost" size="sm" className="h-8 px-2 text-xs">
              <Eye className="w-3.5 h-3.5 mr-1" />
              Audit
            </Button>
          </Link>
          <Link href={`/app/finance/receipts`}>
            <Button variant="outline" size="sm" className="h-8 px-2 text-xs">
              <ReceiptIcon className="w-3.5 h-3.5 mr-1 text-slate-500" />
              Receipt
            </Button>
          </Link>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 mb-1">
            <Link
              href="/app/finance"
              className="hover:text-emerald-600 transition"
            >
              Finance Hub
            </Link>
            <span>/</span>
            <span className="font-semibold text-slate-700 dark:text-slate-300">
              Payments
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Payments & Collections Ledger
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Real-time institutional collections registry, allocation audit, and
            bank transaction vouchers.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {canRecord && (
            <Button
              variant="primary"
              onClick={() => {
                setModalOpen(true);
                if (MOCK_STUDENTS[0]) {
                  handleStudentSelect(MOCK_STUDENTS[0].id);
                }
              }}
              className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs"
            >
              <Plus className="w-4 h-4" />
              Record Payment
            </Button>
          )}
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Realized Collections"
          value={formatMoney(totalCollected)}
          description={`${payments.filter((p) => p.status === "SUCCESS").length} verified bank/cash receipts`}
          icon={<DollarSign className="w-5 h-5 text-emerald-600" />}
        />
        <StatCard
          title="UPI / QR Payments"
          value={formatMoney(upiCollected)}
          description="Instant bank-to-bank settlement"
          icon={<CreditCard className="w-5 h-5 text-teal-600" />}
        />
        <StatCard
          title="NEFT / RTGS / Bank Wire"
          value={formatMoney(bankWireCollected)}
          description="Direct treasury account deposits"
          icon={<Building2 className="w-5 h-5 text-blue-600" />}
        />
        <StatCard
          title="Counter Cash & Cheques"
          value={formatMoney(cashChequeCollected)}
          description="Campus cashier counter collection"
          icon={<FileText className="w-5 h-5 text-amber-600" />}
        />
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-white p-4 rounded-xl border border-slate-200 dark:bg-slate-900 dark:border-slate-800">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <Input
            placeholder="Search Ref, Student, Roll No, Inv..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 text-sm"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2.5 w-full sm:w-auto">
          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
            <Filter className="w-3.5 h-3.5" />
            Mode:
          </div>
          <Select
            value={methodFilter}
            onChange={(e) => setMethodFilter(e.target.value)}
            className="text-xs h-9 w-36"
          >
            <option value="ALL">All Methods</option>
            <option value="UPI">UPI</option>
            <option value="BANK_TRANSFER">Bank Transfer</option>
            <option value="CARD">Card</option>
            <option value="CASH">Cash</option>
            <option value="CHEQUE">Cheque</option>
            <option value="ONLINE">Online</option>
          </Select>

          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs h-9 w-32"
          >
            <option value="ALL">All Status</option>
            <option value="SUCCESS">Success</option>
            <option value="PENDING">Pending</option>
            <option value="FAILED">Failed</option>
            <option value="REVERSED">Reversed</option>
          </Select>
        </div>
      </div>

      {/* Main DataGrid */}
      <DataGrid
        columns={columns}
        data={filteredPayments}
        loading={loading}
        keyExtractor={(row) => row.id}
        emptyMessage="No payments match the selected criteria."
      />

      {/* Guided Record Payment Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-lg font-bold">
              <CreditCard className="w-5 h-5 text-emerald-600" />
              {isConfirming
                ? "Confirm Payment Recording"
                : "Record Student Fee Payment"}
            </DialogTitle>
          </DialogHeader>

          {!isConfirming ? (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                setIsConfirming(true);
              }}
              className="space-y-4 pt-2"
            >
              {/* Step 1: Select Student */}
              <div>
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Select Student <span className="text-rose-500">*</span>
                </label>
                <Select
                  value={selectedStudentId}
                  onChange={(e) => handleStudentSelect(e.target.value)}
                  className="mt-1"
                >
                  <option value="">-- Choose Candidate --</option>
                  {MOCK_STUDENTS.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.firstName} {s.lastName} ({s.rollNumber}) —{" "}
                      {s.program.code}
                    </option>
                  ))}
                </Select>
              </div>

              {/* Step 2: Target Unpaid Invoice */}
              <div>
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Select Invoice to Settle{" "}
                  <span className="text-rose-500">*</span>
                </label>
                {studentPayableInvoices.length > 0 ? (
                  <Select
                    value={selectedInvoiceId}
                    onChange={(e) => handleInvoiceSelect(e.target.value)}
                    className="mt-1"
                  >
                    {studentPayableInvoices.map((inv) => (
                      <option key={inv.id} value={inv.id}>
                        {inv.invoiceNumber} — {inv.program} Sem {inv.semester}{" "}
                        (Due: {formatMoney(inv.outstandingAmount)})
                      </option>
                    ))}
                  </Select>
                ) : (
                  <div className="mt-1 p-3 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-600 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-400">
                    {selectedStudentId
                      ? "This student has no outstanding invoices requiring settlement."
                      : "Please pick a student to view their billable invoices."}
                  </div>
                )}
              </div>

              {/* Outstanding Summary Callout */}
              {selectedInvoice && (
                <div className="bg-emerald-50/70 border border-emerald-200 rounded-lg p-3 text-xs dark:bg-emerald-950/30 dark:border-emerald-800">
                  <div className="flex justify-between font-semibold text-emerald-900 dark:text-emerald-300">
                    <span>Invoice Net Payable:</span>
                    <span>{formatMoney(selectedInvoice.netPayable)}</span>
                  </div>
                  <div className="flex justify-between text-emerald-800/80 mt-1 dark:text-emerald-400">
                    <span>Already Settled:</span>
                    <span>{formatMoney(selectedInvoice.paidAmount)}</span>
                  </div>
                  <div className="flex justify-between font-bold text-emerald-950 border-t border-emerald-200 pt-1.5 mt-1.5 dark:border-emerald-800 dark:text-white">
                    <span>Remaining Balance:</span>
                    <span className="text-emerald-700 dark:text-emerald-400">
                      {formatMoney(selectedInvoice.outstandingAmount)}
                    </span>
                  </div>
                </div>
              )}

              {/* Step 3: Payment Amount */}
              <div>
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Payment Amount (₹) <span className="text-rose-500">*</span>
                </label>
                <Input
                  type="number"
                  min={1}
                  max={
                    selectedInvoice
                      ? selectedInvoice.outstandingAmount
                      : 1000000
                  }
                  value={paymentAmount || ""}
                  onChange={(e) => setPaymentAmount(Number(e.target.value))}
                  placeholder="Enter amount in ₹"
                  className="mt-1"
                  required
                />
              </div>

              {/* Step 4: Mode & Reference */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Payment Channel <span className="text-rose-500">*</span>
                  </label>
                  <Select
                    value={paymentMethod}
                    onChange={(e) =>
                      setPaymentMethod(e.target.value as PaymentMethod)
                    }
                    className="mt-1"
                  >
                    <option value="UPI">UPI / QR Transfer</option>
                    <option value="BANK_TRANSFER">
                      Bank Wire / NEFT / RTGS
                    </option>
                    <option value="CARD">Debit / Credit Card</option>
                    <option value="CASH">Counter Cash</option>
                    <option value="CHEQUE">Cheque / Demand Draft</option>
                    <option value="ONLINE">Campus Payment Gateway</option>
                  </Select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Transaction Ref / UTR{" "}
                    <span className="text-rose-500">*</span>
                  </label>
                  <Input
                    value={referenceNumber}
                    onChange={(e) => setReferenceNumber(e.target.value)}
                    placeholder="e.g. UTR-2026-987654"
                    className="mt-1"
                    required
                  />
                </div>
              </div>

              {/* Extra Details for Bank/Cheque */}
              {(paymentMethod === "BANK_TRANSFER" ||
                paymentMethod === "CHEQUE") && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Bank Name
                    </label>
                    <Input
                      value={bankName}
                      onChange={(e) => setBankName(e.target.value)}
                      placeholder="e.g. State Bank of India"
                      className="mt-1"
                    />
                  </div>
                  {paymentMethod === "CHEQUE" && (
                    <div>
                      <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                        Cheque / DD Number
                      </label>
                      <Input
                        value={chequeNumber}
                        onChange={(e) => setChequeNumber(e.target.value)}
                        placeholder="e.g. CHQ-445892"
                        className="mt-1"
                      />
                    </div>
                  )}
                </div>
              )}

              {/* Remarks */}
              <div>
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Audit Notes / Cashier Remarks
                </label>
                <Input
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Optional audit memo"
                  className="mt-1"
                />
              </div>

              <DialogFooter className="pt-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  disabled={
                    !selectedInvoice ||
                    paymentAmount <= 0 ||
                    !referenceNumber.trim()
                  }
                  className="bg-emerald-600 hover:bg-emerald-700 text-white"
                >
                  Proceed to Review
                </Button>
              </DialogFooter>
            </form>
          ) : (
            <div className="space-y-4 pt-2">
              <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-4 text-xs text-amber-900 dark:bg-amber-950/40 dark:border-amber-800 dark:text-amber-200">
                <p className="font-bold flex items-center gap-1.5 text-sm">
                  <ShieldCheck className="w-4 h-4 text-amber-600" />
                  Irreversible Cashier Ledger Action
                </p>
                <p className="mt-1 text-slate-600 dark:text-slate-300">
                  Recording this transaction will immediately credit the invoice
                  balance and automatically generate an immutable student fee
                  receipt voucher.
                </p>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 space-y-2 text-xs dark:bg-slate-800/50 dark:border-slate-700">
                <div className="flex justify-between">
                  <span className="text-slate-500">Student:</span>
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {selectedInvoice?.studentName} (
                    {selectedInvoice?.rollNumber})
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Target Invoice:</span>
                  <span className="font-mono font-medium text-slate-900 dark:text-white">
                    {selectedInvoice?.invoiceNumber}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Payment Amount:</span>
                  <span className="font-bold text-emerald-600 text-sm">
                    {formatMoney(paymentAmount)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Payment Method:</span>
                  <span className="font-medium text-slate-900 dark:text-white">
                    {paymentMethod}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Transaction Reference:</span>
                  <span className="font-mono text-slate-900 dark:text-white">
                    {referenceNumber}
                  </span>
                </div>
                {bankName && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Issuing Bank:</span>
                    <span className="text-slate-900 dark:text-white">
                      {bankName}
                    </span>
                  </div>
                )}
                <div className="flex justify-between border-t border-slate-200 pt-2 font-semibold">
                  <span className="text-slate-600">
                    Remaining Balance Post Payment:
                  </span>
                  <span className="text-slate-900 dark:text-white">
                    {formatMoney(
                      (selectedInvoice?.outstandingAmount || 0) - paymentAmount,
                    )}
                  </span>
                </div>
              </div>

              <DialogFooter className="pt-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsConfirming(false)}
                  disabled={submitting}
                >
                  Back to Edit
                </Button>
                <Button
                  type="button"
                  variant="primary"
                  onClick={handleRecordPayment}
                  disabled={submitting}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white"
                >
                  {submitting ? "Committing..." : "Confirm & Issue Receipt"}
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
