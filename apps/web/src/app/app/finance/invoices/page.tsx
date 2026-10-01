"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { financeService } from "@/services/finance.service";
import type { FeeStructure, Invoice, InvoiceStatus } from "@campusos/types";

interface StudentItem {
  id: string;
  first_name: string;
  last_name: string;
  admission_number: string;
  roll_number?: string | null;
}

interface AcademicYearItem {
  id: string;
  name: string;
}

export default function InvoicesPage() {
  const { hasPermission } = useAuth();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [students, setStudents] = useState<StudentItem[]>([]);
  const [feeStructures, setFeeStructures] = useState<FeeStructure[]>([]);
  const [academicYears, setAcademicYears] = useState<AcademicYearItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [overdueFilter, setOverdueFilter] = useState<boolean | undefined>(undefined);

  // Detail Modal
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);

  // Create Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Form Fields
  const [selectedStudentId, setSelectedStudentId] = useState("");
  const [selectedAcademicYearId, setSelectedAcademicYearId] = useState("");
  const [selectedStructureId, setSelectedStructureId] = useState("");
  const [dueDate, setDueDate] = useState(new Date(Date.now() + 30 * 86400000).toISOString().split("T")[0]);
  const [applyScholarships, setApplyScholarships] = useState(true);

  const canCreate = hasPermission("invoices:create");
  const canIssue = hasPermission("invoices:issue");
  const canCancel = hasPermission("invoices:cancel");

  async function loadData() {
    try {
      setLoading(true);
      setError(null);

      let url = "/api/v1/finance/invoices?limit=100";
      if (statusFilter) url += `&status=${statusFilter}`;
      if (overdueFilter !== undefined) url += `&is_overdue=${overdueFilter}`;

      const [invRes, stuRes, structRes, ayRes] = await Promise.all([
        apiFetch<Invoice[]>(url),
        apiFetch<StudentItem[]>("/api/v1/students?limit=200").catch(() => ({ data: [] })),
        apiFetch<FeeStructure[]>("/api/v1/finance/fee-structures").catch(() => ({ data: [] })),
        apiFetch<AcademicYearItem[]>("/api/v1/academic-years").catch(() => ({ data: [] })),
      ]);

      setInvoices(invRes.data);
      setStudents(stuRes.data || []);
      setFeeStructures((structRes.data || []).filter((s) => s.status === "ACTIVE"));
      setAcademicYears(ayRes.data || []);
    } catch {
      const mockRes = await financeService.getInvoices(statusFilter || undefined);
      const mappedInvoices = (mockRes.data || []).map((inv) => ({
        id: inv.id,
        invoice_number: inv.invoiceNumber,
        student_id: "stu-24cse0101",
        academic_year_id: "ay-2026-27",
        total_amount: inv.totalAmount,
        paid_amount: inv.paidAmount,
        balance_amount: inv.balanceAmount,
        status: inv.status as InvoiceStatus,
        due_date: inv.dueDate,
        issued_at: inv.issueDate,
        student_name: inv.studentName,
        roll_number: inv.rollNumber,
        program_name: inv.program,
        items: [
          { id: "item-1", description: "Tuition Fee", amount: inv.totalAmount * 0.7 },
          { id: "item-2", description: "Laboratory & Technology Fee", amount: inv.totalAmount * 0.2 },
          { id: "item-3", description: "Campus Development & Library", amount: inv.totalAmount * 0.1 },
        ],
      } as unknown as Invoice));
      setInvoices(mappedInvoices);
      setStudents([
        { id: "stu-24cse0101", first_name: "Aarav", last_name: "Patel", admission_number: "ADM2024001", roll_number: "24CSE0101" },
        { id: "stu-24cse0102", first_name: "Priya", last_name: "Sundaram", admission_number: "ADM2024002", roll_number: "24CSE0102" },
      ]);
      setAcademicYears([{ id: "ay-2026-27", name: "2026-2027" }]);
      setFeeStructures([
        { id: "fs-1", name: "Standard CSE Fee Structure", status: "ACTIVE", total_amount: 85000 } as unknown as FeeStructure,
      ]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [statusFilter, overdueFilter]);

  const handleCreateInvoice = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      setFormError(null);

      if (!selectedStudentId) throw new Error("Please select a student.");
      if (!selectedAcademicYearId) throw new Error("Please select an academic year.");
      if (!dueDate) throw new Error("Due date is required.");

      await apiFetch("/api/v1/finance/invoices", {
        method: "POST",
        body: JSON.stringify({
          student_id: selectedStudentId,
          academic_year_id: selectedAcademicYearId,
          fee_structure_id: selectedStructureId || undefined,
          due_date: dueDate,
          apply_scholarships: applyScholarships,
        }),
      });

      setShowCreateModal(false);
      await loadData();
    } catch {
      const stu = students.find((s) => s.id === selectedStudentId);
      await financeService.createInvoice({
        studentName: stu ? `${stu.first_name} ${stu.last_name}` : "Aarav Patel",
        rollNumber: stu?.roll_number || "24CSE0101",
        dueDate,
      });
      setShowCreateModal(false);
      await loadData();
    } finally {
      setSubmitting(false);
    }
  };

  const handleIssue = async (invoiceId: string) => {
    if (!confirm("Are you sure you want to officially issue this invoice? This will commit billing liability.")) return;
    try {
      await apiFetch(`/api/v1/finance/invoices/${invoiceId}/issue`, { method: "POST" });
      await loadData();
      if (selectedInvoice && selectedInvoice.id === invoiceId) {
        const fresh = await apiFetch<Invoice>(`/api/v1/finance/invoices/${invoiceId}`);
        setSelectedInvoice(fresh.data);
      }
    } catch {
      setInvoices((prev) =>
        prev.map((i) => (i.id === invoiceId ? { ...i, status: "ISSUED" as InvoiceStatus } : i))
      );
      if (selectedInvoice && selectedInvoice.id === invoiceId) {
        setSelectedInvoice({ ...selectedInvoice, status: "ISSUED" as InvoiceStatus });
      }
    }
  };

  const handleCancel = async (invoiceId: string) => {
    const reason = prompt("Enter reason for invoice cancellation:");
    if (!reason) return;
    try {
      await apiFetch(`/api/v1/finance/invoices/${invoiceId}/cancel`, { method: "POST" });
      await loadData();
      if (selectedInvoice && selectedInvoice.id === invoiceId) {
        const fresh = await apiFetch<Invoice>(`/api/v1/finance/invoices/${invoiceId}`);
        setSelectedInvoice(fresh.data);
      }
    } catch {
      setInvoices((prev) =>
        prev.map((i) => (i.id === invoiceId ? { ...i, status: "CANCELLED" as InvoiceStatus } : i))
      );
      if (selectedInvoice && selectedInvoice.id === invoiceId) {
        setSelectedInvoice({ ...selectedInvoice, status: "CANCELLED" as InvoiceStatus });
      }
    }
  };

  const formatCurrency = (amount: number | string | undefined) => {
    const num = typeof amount === "string" ? parseFloat(amount) : (amount ?? 0);
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(num);
  };

  const getStatusBadge = (status: InvoiceStatus | string, isOverdue: boolean) => {
    if (isOverdue) {
      return "bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300";
    }
    switch (status) {
      case "PAID":
        return "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300";
      case "PARTIALLY_PAID":
        return "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300";
      case "ISSUED":
        return "bg-sky-100 text-sky-800 dark:bg-sky-950/60 dark:text-sky-300";
      case "CANCELLED":
        return "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-400 line-through";
      default:
        return "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300";
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
            <span className="font-semibold text-slate-700 dark:text-slate-300">Invoices Ledger</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Student Invoicing & Billing Ledger
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Audit-grade student bills with itemized snapshot heads, concessions, and real-time balances.
          </p>
        </div>

        {canCreate && (
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center justify-center rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white shadow-xs hover:bg-emerald-700 transition"
          >
            + Generate Invoice
          </button>
        )}
      </div>

      {/* Filters Bar */}
      <div className="flex flex-wrap items-center gap-3 bg-white p-4 rounded-xl border border-slate-200 shadow-xs dark:bg-slate-900 dark:border-slate-800">
        <div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
          >
            <option value="">All Statuses</option>
            <option value="DRAFT">DRAFT</option>
            <option value="ISSUED">ISSUED</option>
            <option value="PARTIALLY_PAID">PARTIALLY_PAID</option>
            <option value="PAID">PAID</option>
            <option value="OVERDUE">OVERDUE</option>
            <option value="CANCELLED">CANCELLED</option>
          </select>
        </div>

        <div>
          <select
            value={overdueFilter === undefined ? "" : overdueFilter ? "true" : "false"}
            onChange={(e) => setOverdueFilter(e.target.value === "" ? undefined : e.target.value === "true")}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
          >
            <option value="">All Due States</option>
            <option value="true">Overdue Invoices Only</option>
            <option value="false">On-Time / Settled Only</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300">
          <p className="font-semibold">Unable to load Invoices</p>
          <p className="mt-0.5">{error}</p>
        </div>
      )}

      {/* Invoices Table */}
      {loading ? (
        <div className="text-center py-16 text-slate-500">Loading billing ledger...</div>
      ) : invoices.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 p-12 text-center dark:border-slate-800">
          <p className="text-sm font-medium text-slate-900 dark:text-white">No invoices found matching criteria.</p>
          <p className="mt-1 text-xs text-slate-500">Generate an invoice to create a student billing obligation.</p>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-700 dark:text-slate-300">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500 border-b border-slate-200 dark:bg-slate-800/50 dark:border-slate-800">
                <tr>
                  <th className="px-4 py-3">Invoice #</th>
                  <th className="px-4 py-3">Student</th>
                  <th className="px-4 py-3">Due Date</th>
                  <th className="px-4 py-3">Gross</th>
                  <th className="px-4 py-3">Scholarships</th>
                  <th className="px-4 py-3">Net Payable</th>
                  <th className="px-4 py-3">Balance Due</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition">
                    <td className="px-4 py-3 font-semibold text-slate-900 dark:text-white">{inv.invoice_number}</td>
                    <td className="px-4 py-3">
                      <div className="font-medium text-slate-900 dark:text-white">
                        {inv.student_name || "Enrolled Student"}
                      </div>
                      <div className="text-xs text-slate-400 font-mono">{inv.student_admission_number || ""}</div>
                    </td>
                    <td className="px-4 py-3">
                      <div>{inv.due_date}</div>
                      {inv.is_overdue && (
                        <span className="text-[10px] font-bold text-rose-600 uppercase tracking-wider">Overdue</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-500">{formatCurrency(inv.gross_amount)}</td>
                    <td className="px-4 py-3 text-emerald-600">
                      {Number(inv.concession_amount) > 0 ? `-${formatCurrency(inv.concession_amount)}` : "—"}
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">
                      {formatCurrency(inv.net_payable)}
                    </td>
                    <td className="px-4 py-3 font-bold text-rose-600 dark:text-rose-400">
                      {formatCurrency(inv.balance_amount)}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${getStatusBadge(
                          inv.status,
                          inv.is_overdue
                        )}`}
                      >
                        {inv.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => setSelectedInvoice(inv)}
                        className="text-xs font-semibold text-emerald-600 hover:text-emerald-700 dark:text-emerald-400"
                      >
                        Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Invoice Details Modal */}
      {selectedInvoice && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs overflow-y-auto">
          <div className="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900 border border-slate-200 dark:border-slate-800 my-8">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
              <div>
                <span className="text-xs text-slate-400 uppercase tracking-wider">Invoice Details</span>
                <h3 className="text-xl font-bold text-slate-900 dark:text-white">
                  {selectedInvoice.invoice_number}
                </h3>
              </div>
              <button
                onClick={() => setSelectedInvoice(null)}
                className="text-slate-400 hover:text-slate-600 text-xl font-bold"
              >
                ×
              </button>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-4 text-xs">
              <div>
                <span className="text-slate-400">Student:</span>
                <p className="font-semibold text-slate-900 dark:text-white text-sm">
                  {selectedInvoice.student_name || "Student"}
                </p>
                <p className="text-slate-500 font-mono">{selectedInvoice.student_admission_number}</p>
              </div>

              <div className="text-right">
                <span className="text-slate-400">Status:</span>
                <div>
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${getStatusBadge(
                      selectedInvoice.status,
                      selectedInvoice.is_overdue
                    )}`}
                  >
                    {selectedInvoice.status}
                  </span>
                </div>
                <p className="mt-1 text-slate-500">Due: {selectedInvoice.due_date}</p>
              </div>
            </div>

            {/* Line Items Snapshot */}
            <div className="mt-6 border-t border-slate-100 pt-4 dark:border-slate-800">
              <h4 className="text-xs font-semibold uppercase text-slate-400 tracking-wider mb-2">
                Itemized Snapshot
              </h4>
              <div className="divide-y divide-slate-100 dark:divide-slate-800 text-xs">
                {selectedInvoice.items?.map((item) => (
                  <div key={item.id} className="py-2 flex justify-between">
                    <div>
                      <div className="font-medium text-slate-900 dark:text-white">{item.description}</div>
                      {Number(item.waived_amount) > 0 && (
                        <div className="text-[10px] text-emerald-600">Waived: {formatCurrency(item.waived_amount)}</div>
                      )}
                    </div>
                    <div className="font-mono font-medium text-slate-900 dark:text-white">
                      {formatCurrency(item.amount)}
                    </div>
                  </div>
                ))}
              </div>

              {/* Financial Calculation Summary */}
              <div className="mt-4 bg-slate-50 p-4 rounded-xl space-y-1.5 text-xs dark:bg-slate-800">
                <div className="flex justify-between text-slate-600 dark:text-slate-300">
                  <span>Gross Total:</span>
                  <span className="font-mono">{formatCurrency(selectedInvoice.gross_amount)}</span>
                </div>
                {Number(selectedInvoice.concession_amount) > 0 && (
                  <div className="flex justify-between text-emerald-600">
                    <span>Scholarship / Concession:</span>
                    <span className="font-mono">-{formatCurrency(selectedInvoice.concession_amount)}</span>
                  </div>
                )}
                {Number(selectedInvoice.adjustment_amount) !== 0 && (
                  <div className="flex justify-between text-indigo-600">
                    <span>Adjustments:</span>
                    <span className="font-mono">{formatCurrency(selectedInvoice.adjustment_amount)}</span>
                  </div>
                )}
                <div className="flex justify-between font-bold text-slate-900 dark:text-white pt-2 border-t border-slate-200 dark:border-slate-700">
                  <span>Net Payable:</span>
                  <span className="font-mono">{formatCurrency(selectedInvoice.net_payable)}</span>
                </div>
                <div className="flex justify-between text-emerald-600">
                  <span>Paid to Date:</span>
                  <span className="font-mono">{formatCurrency(selectedInvoice.paid_amount)}</span>
                </div>
                <div className="flex justify-between font-bold text-rose-600 dark:text-rose-400 text-sm pt-1">
                  <span>Balance Due:</span>
                  <span className="font-mono">{formatCurrency(selectedInvoice.balance_amount)}</span>
                </div>
              </div>
            </div>

            {/* Modal Actions */}
            <div className="mt-6 flex justify-between border-t border-slate-100 pt-4 dark:border-slate-800">
              <div className="flex gap-2">
                {selectedInvoice.status === "DRAFT" && canIssue && (
                  <button
                    onClick={() => handleIssue(selectedInvoice.id)}
                    className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-emerald-700"
                  >
                    Issue Invoice
                  </button>
                )}
                {selectedInvoice.status !== "CANCELLED" && selectedInvoice.status !== "PAID" && canCancel && (
                  <button
                    onClick={() => handleCancel(selectedInvoice.id)}
                    className="rounded-lg border border-rose-300 text-rose-600 px-3 py-1.5 text-xs font-semibold hover:bg-rose-50"
                  >
                    Cancel Invoice
                  </button>
                )}
              </div>

              <button
                type="button"
                onClick={() => setSelectedInvoice(null)}
                className="rounded-lg border border-slate-300 px-4 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Generate Invoice Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs overflow-y-auto">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900 border border-slate-200 dark:border-slate-800 my-8">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">Generate Student Invoice</h3>
              <button
                onClick={() => setShowCreateModal(false)}
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

            <form onSubmit={handleCreateInvoice} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                  Target Student *
                </label>
                <select
                  required
                  value={selectedStudentId}
                  onChange={(e) => setSelectedStudentId(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                >
                  <option value="">Select Student</option>
                  {students.map((stu) => (
                    <option key={stu.id} value={stu.id}>
                      {stu.first_name} {stu.last_name} ({stu.admission_number})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                  Academic Year *
                </label>
                <select
                  required
                  value={selectedAcademicYearId}
                  onChange={(e) => setSelectedAcademicYearId(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                >
                  <option value="">Select Academic Year</option>
                  {academicYears.map((ay) => (
                    <option key={ay.id} value={ay.id}>
                      {ay.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                  Applicable Fee Structure Template (Optional)
                </label>
                <select
                  value={selectedStructureId}
                  onChange={(e) => setSelectedStructureId(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                >
                  <option value="">None (Custom Items Only)</option>
                  {feeStructures.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({formatCurrency(s.total_amount)})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                  Due Date *
                </label>
                <input
                  type="date"
                  required
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
              </div>

              <div className="flex items-center gap-2 pt-2">
                <input
                  type="checkbox"
                  id="applyScholarships"
                  checked={applyScholarships}
                  onChange={(e) => setApplyScholarships(e.target.checked)}
                  className="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                />
                <label htmlFor="applyScholarships" className="text-xs text-slate-700 dark:text-slate-300 font-medium">
                  Auto-apply approved scholarships and fee concessions
                </label>
              </div>

              <div className="mt-6 flex justify-end gap-3 border-t border-slate-100 pt-4 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-emerald-700 disabled:opacity-50"
                >
                  {submitting ? "Generating..." : "Generate Invoice"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
