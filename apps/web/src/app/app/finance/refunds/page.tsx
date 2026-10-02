"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  RotateCcw,
  Plus,
  Search,
  Filter,
  Eye,
  CheckCircle2,
  Clock,
  DollarSign,
  AlertTriangle,
  ShieldCheck,
  Building2,
} from "lucide-react";
import { DataGrid, ColumnDef } from "@/components/data-grid";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/ui/stat-card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { useToast, ToastType } from "@/components/ui/toast";
import { useAuth } from "@/lib/auth-context";
import { financeService } from "@/services/finance.service";
import { formatMoney } from "@/services/financial-calculator";
import { Refund, RefundStatus, Invoice } from "@/types/finance";
import { MOCK_STUDENTS } from "@/mocks/students.mock";

export default function RefundsPage() {
  const { hasPermission } = useAuth();
  const { showToast } = useToast();
  const notify = (title: string, type: ToastType = "info") => showToast({ title, type });

  const [refunds, setRefunds] = useState<Refund[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedStudentId, setSelectedStudentId] = useState("");
  const [selectedInvoiceId, setSelectedInvoiceId] = useState("");
  const [requestedAmount, setRequestedAmount] = useState<number>(0);
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const canManage = hasPermission("finance.manage_refunds") || hasPermission("refunds:create");

  const loadData = async () => {
    try {
      setLoading(true);
      const [refRes, invRes] = await Promise.all([
        financeService.getRefunds(),
        financeService.getInvoices(),
      ]);
      setRefunds(refRes.data);
      setInvoices(invRes.data);
    } catch {
      notify("Error loading refund petitions", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Invoices for student with paid amount > 0
  const eligibleInvoices = useMemo(() => {
    if (!selectedStudentId) return [];
    return invoices.filter(
      (inv) =>
        (inv.studentId === selectedStudentId ||
          inv.studentName.toLowerCase().includes(selectedStudentId.toLowerCase())) &&
        inv.paidAmount > 0
    );
  }, [selectedStudentId, invoices]);

  const selectedInvoice = useMemo(() => {
    return invoices.find((inv) => inv.id === selectedInvoiceId);
  }, [selectedInvoiceId, invoices]);

  const handleStudentSelect = (studentId: string) => {
    setSelectedStudentId(studentId);
    const eligible = invoices.filter(
      (inv) =>
        (inv.studentId === studentId ||
          inv.studentName.toLowerCase().includes(studentId.toLowerCase())) &&
        inv.paidAmount > 0
    );
    if (eligible.length > 0) {
      setSelectedInvoiceId(eligible[0].id);
      setRequestedAmount(eligible[0].paidAmount);
    } else {
      setSelectedInvoiceId("");
      setRequestedAmount(0);
    }
  };

  const handleInvoiceSelect = (invId: string) => {
    setSelectedInvoiceId(invId);
    const target = invoices.find((inv) => inv.id === invId);
    if (target) {
      setRequestedAmount(target.paidAmount);
    }
  };

  const handleCreateRefund = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedInvoice) {
      notify("Please pick a settled invoice to petition refund against.", "error");
      return;
    }
    if (requestedAmount <= 0) {
      notify("Refund amount must be greater than zero.", "error");
      return;
    }
    if (requestedAmount > selectedInvoice.paidAmount) {
      notify(
        `Requested refund (${formatMoney(requestedAmount)}) cannot exceed total settled amount (${formatMoney(selectedInvoice.paidAmount)}).`,
        "error"
      );
      return;
    }
    if (!reason.trim()) {
      notify("A detailed refund justification is mandatory.", "error");
      return;
    }

    try {
      setSubmitting(true);
      await financeService.requestRefund({
        studentId: selectedInvoice.studentId,
        invoiceId: selectedInvoice.id,
        requestedAmount: Number(requestedAmount),
        reason: reason.trim(),
        requestedBy: "Accounts Desk",
      });

      notify("Refund petition registered for audit review.", "success");
      setModalOpen(false);
      setSelectedStudentId("");
      setSelectedInvoiceId("");
      setRequestedAmount(0);
      setReason("");
      loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to petition refund.";
      notify(msg, "error");
    } finally {
      setSubmitting(false);
    }
  };

  // Metrics
  const pendingCount = useMemo(() => {
    return refunds.filter((r) => r.status === "REQUESTED" || r.status === "UNDER_REVIEW").length;
  }, [refunds]);

  const approvedCount = useMemo(() => {
    return refunds.filter((r) => r.status === "APPROVED").length;
  }, [refunds]);

  const totalProcessed = useMemo(() => {
    return refunds
      .filter((r) => r.status === "PROCESSED")
      .reduce((sum, r) => sum + (r.approvedAmount || r.requestedAmount), 0);
  }, [refunds]);

  const filteredRefunds = useMemo(() => {
    return refunds.filter((r) => {
      const matchesSearch =
        searchQuery === "" ||
        r.refundNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.studentName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.rollNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.invoiceNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.reason.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesStatus = statusFilter === "ALL" || r.status === statusFilter;

      return matchesSearch && matchesStatus;
    });
  }, [refunds, searchQuery, statusFilter]);

  const columns: ColumnDef<Refund>[] = [
    {
      id: "refundNumber",
      header: "Refund Petition #",
      accessorKey: "refundNumber",
      sortable: true,
      cell: ({ row }) => (
        <Link
          href={`/app/finance/refunds/${row.id}`}
          className="font-mono text-sm font-semibold text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 hover:underline"
        >
          {row.refundNumber}
        </Link>
      ),
    },
    {
      id: "student",
      header: "Student",
      accessorKey: "studentName",
      sortable: true,
      cell: ({ row }) => (
        <div>
          <div className="font-semibold text-slate-900 dark:text-white">{row.studentName}</div>
          <div className="text-xs text-slate-500 font-mono">{row.rollNumber}</div>
        </div>
      ),
    },
    {
      id: "invoiceNumber",
      header: "Invoice Reference",
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
      id: "requestedAmount",
      header: "Requested Amount",
      accessorKey: "requestedAmount",
      sortable: true,
      cell: ({ row }) => (
        <span className="font-semibold text-slate-900 dark:text-white">
          {formatMoney(row.requestedAmount)}
        </span>
      ),
    },
    {
      id: "approvedAmount",
      header: "Approved Amount",
      cell: ({ row }) => (
        <span className="font-bold text-emerald-600 dark:text-emerald-400">
          {row.approvedAmount ? formatMoney(row.approvedAmount) : "—"}
        </span>
      ),
    },
    {
      id: "status",
      header: "Status",
      accessorKey: "status",
      cell: ({ row }) => {
        const badges: Record<string, string> = {
          REQUESTED: "bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300",
          UNDER_REVIEW: "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300",
          APPROVED: "bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300",
          PROCESSED: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300",
          REJECTED: "bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300",
        };
        return (
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
              badges[row.status] || "bg-slate-100 text-slate-700"
            }`}
          >
            {row.status.replace("_", " ")}
          </span>
        );
      },
    },
    {
      id: "actions",
      header: "Actions",
      cell: ({ row }) => (
        <Link href={`/app/finance/refunds/${row.id}`}>
          <Button variant="ghost" size="sm" className="h-8 px-2 text-xs">
            <Eye className="w-3.5 h-3.5 mr-1" />
            Review
          </Button>
        </Link>
      ),
    },
  ];

  return (
    <div className="space-y-6">
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
            Refunds & Disbursement Workflow
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Multi-stage audit verification, authorization committee review, and electronic reimbursement.
          </p>
        </div>

        {canManage && (
          <Button
            variant="primary"
            onClick={() => setModalOpen(true)}
            className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs"
          >
            <Plus className="w-4 h-4" />
            Petition Refund
          </Button>
        )}
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          title="Pending Audit Review"
          value={pendingCount.toString()}
          description="Requests awaiting committee deliberation"
          icon={<Clock className="w-5 h-5 text-amber-600" />}
        />
        <StatCard
          title="Approved for Payout"
          value={approvedCount.toString()}
          description="Awaiting electronic treasury release"
          icon={<CheckCircle2 className="w-5 h-5 text-indigo-600" />}
        />
        <StatCard
          title="Total Disbursed"
          value={formatMoney(totalProcessed)}
          description="Completed electronic reimbursements"
          icon={<DollarSign className="w-5 h-5 text-emerald-600" />}
        />
      </div>

      {/* Filter and Search */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-white p-4 rounded-xl border border-slate-200 dark:bg-slate-900 dark:border-slate-800">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <Input
            placeholder="Search Petition #, Student, Invoice..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 text-sm"
          />
        </div>

        <div className="flex items-center gap-2.5 w-full sm:w-auto">
          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
            <Filter className="w-3.5 h-3.5" />
            Status:
          </div>
          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs h-9 w-40"
          >
            <option value="ALL">All Status</option>
            <option value="REQUESTED">Requested</option>
            <option value="UNDER_REVIEW">Under Review</option>
            <option value="APPROVED">Approved</option>
            <option value="PROCESSED">Processed</option>
            <option value="REJECTED">Rejected</option>
          </Select>
        </div>
      </div>

      {/* Main DataGrid */}
      <DataGrid
        columns={columns}
        data={filteredRefunds}
        loading={loading}
        keyExtractor={(row) => row.id}
        emptyMessage="No refund petitions found matching the filters."
      />

      {/* Petition Refund Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-lg font-bold">
              <RotateCcw className="w-5 h-5 text-emerald-600" />
              Petition Student Fee Refund
            </DialogTitle>
          </DialogHeader>

          <form onSubmit={handleCreateRefund} className="space-y-4 pt-2">
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
                    {s.firstName} {s.lastName} ({s.rollNumber})
                  </option>
                ))}
              </Select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Settled Invoice <span className="text-rose-500">*</span>
              </label>
              {eligibleInvoices.length > 0 ? (
                <Select
                  value={selectedInvoiceId}
                  onChange={(e) => handleInvoiceSelect(e.target.value)}
                  className="mt-1"
                >
                  {eligibleInvoices.map((inv) => (
                    <option key={inv.id} value={inv.id}>
                      {inv.invoiceNumber} — Paid: {formatMoney(inv.paidAmount)}
                    </option>
                  ))}
                </Select>
              ) : (
                <div className="mt-1 p-3 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-600 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-400">
                  {selectedStudentId
                    ? "Selected student has no settled payments available for refund."
                    : "Pick a student to view eligible payment transactions."}
                </div>
              )}
            </div>

            {selectedInvoice && (
              <div>
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Refund Requested Amount (₹) <span className="text-rose-500">*</span>
                </label>
                <Input
                  type="number"
                  min={1}
                  max={selectedInvoice.paidAmount}
                  value={requestedAmount || ""}
                  onChange={(e) => setRequestedAmount(Number(e.target.value))}
                  className="mt-1"
                  required
                />
                <p className="text-[11px] text-slate-500 mt-1">
                  Maximum allowable refund for this invoice: {formatMoney(selectedInvoice.paidAmount)}
                </p>
              </div>
            )}

            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Audit Justification & Reason <span className="text-rose-500">*</span>
              </label>
              <Input
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="e.g. Caution deposit refund post clearance, double debit adjustment"
                className="mt-1"
                required
              />
            </div>

            <DialogFooter className="pt-3">
              <Button type="button" variant="outline" onClick={() => setModalOpen(false)}>
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={!selectedInvoice || requestedAmount <= 0 || !reason.trim() || submitting}
                className="bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                {submitting ? "Submitting..." : "Submit Petition"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
