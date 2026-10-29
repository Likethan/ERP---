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
  AlertTriangle,
  CheckCircle2,
  DollarSign,
  FileText,
  Clock,
  Ban,
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
import { useToast } from "@/components/ui/toast";
import { useAuth } from "@/lib/auth-context";
import { financeService } from "@/services/finance.service";
import { formatMoney } from "@/services/financial-calculator";
import { Invoice, InvoiceStatus, FeeStructure } from "@/types/finance";
import { MOCK_STUDENTS } from "@/mocks/students.mock";

export default function InvoicesPage() {
  const { hasPermission } = useAuth();
  const { showToast } = useToast();

  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [structures, setStructures] = useState<FeeStructure[]>([]);
  const [loading, setLoading] = useState(true);

  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [programFilter, setProgramFilter] = useState<string>("ALL");

  // Create Invoice Modal State
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [selectedStudentId, setSelectedStudentId] = useState(
    MOCK_STUDENTS[0]?.id || "",
  );
  const [selectedStructureId, setSelectedStructureId] = useState("");
  const [customGross, setCustomGross] = useState(76000);
  const [dueDate, setDueDate] = useState(
    new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split("T")[0],
  );
  const [creating, setCreating] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [invRes, fsRes] = await Promise.all([
        financeService.getInvoices(),
        financeService.getFeeStructures(),
      ]);
      setInvoices(invRes.data);
      setStructures(fsRes.data);
      if (fsRes.data.length > 0 && !selectedStructureId) {
        setSelectedStructureId(fsRes.data[0].id);
        setCustomGross(fsRes.data[0].grossTotal);
      }
    } catch (err: unknown) {
      showToast({
        title: "Error Loading Invoices",
        message:
          err instanceof Error
            ? err.message
            : "Unable to load student invoices",
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateInvoice = async (e: React.FormEvent) => {
    e.preventDefault();
    const student = MOCK_STUDENTS.find((s) => s.id === selectedStudentId);
    const fs = structures.find((f) => f.id === selectedStructureId);

    if (!student) {
      showToast({
        title: "Validation Error",
        message: "Select a valid student.",
        type: "error",
      });
      return;
    }

    try {
      setCreating(true);
      const res = await financeService.createInvoice({
        studentId: student.id,
        studentName: `${student.firstName} ${student.lastName}`,
        program: student.program?.name || "Engineering",
        department: student.program?.department || "Engineering",
        semester: fs?.semester || 5,
        grossAmount: customGross,
        dueDate,
      });

      showToast({
        title: "Invoice Dispatched",
        message: `Generated ${res.data.invoiceNumber} for ${res.data.studentName}.`,
        type: "success",
      });
      setCreateModalOpen(false);
      loadData();
    } catch (err: unknown) {
      showToast({
        title: "Invoice Creation Failed",
        message:
          err instanceof Error ? err.message : "Error generating invoice",
        type: "error",
      });
    } finally {
      setCreating(false);
    }
  };

  const filteredInvoices = useMemo(() => {
    return invoices.filter((inv) => {
      const matchesSearch =
        inv.invoiceNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
        inv.studentName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        inv.rollNumber.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus =
        statusFilter === "ALL" || inv.status === statusFilter;
      const matchesProgram =
        programFilter === "ALL" || inv.program.includes(programFilter);
      return matchesSearch && matchesStatus && matchesProgram;
    });
  }, [invoices, searchQuery, statusFilter, programFilter]);

  const totalBilled = invoices.reduce((acc, i) => acc + i.netPayable, 0);
  const totalCollected = invoices.reduce((acc, i) => acc + i.paidAmount, 0);
  const totalOutstanding = invoices.reduce(
    (acc, i) => acc + i.outstandingAmount,
    0,
  );

  const getStatusBadge = (status: InvoiceStatus) => {
    switch (status) {
      case "PAID":
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            Paid
          </span>
        );
      case "PARTIALLY_PAID":
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            Partially Paid
          </span>
        );
      case "ISSUED":
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
            Issued
          </span>
        );
      case "OVERDUE":
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            Overdue
          </span>
        );
      case "DRAFT":
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700/60">
            Draft
          </span>
        );
      case "CANCELLED":
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-500 border border-slate-700/60 line-through">
            Cancelled
          </span>
        );
    }
  };

  const columns: ColumnDef<Invoice>[] = [
    {
      id: "invoiceNumber",
      header: "Invoice No.",
      accessorKey: "invoiceNumber",
      sortable: true,
      cell: (row) => (
        <Link
          href={`/app/finance/invoices/${row.id}`}
          className="font-mono text-xs font-bold text-indigo-400 hover:text-indigo-300 transition-colors"
        >
          {row.invoiceNumber}
        </Link>
      ),
    },
    {
      id: "student",
      header: "Candidate",
      accessorKey: "studentName",
      sortable: true,
      cell: (row) => (
        <div>
          <p className="font-medium text-slate-200">{row.studentName}</p>
          <p className="font-mono text-xs text-slate-400">{row.rollNumber}</p>
        </div>
      ),
    },
    {
      id: "program",
      header: "Program / Sem",
      cell: (row) => (
        <span className="text-xs text-slate-300">
          {row.program} (Sem {row.semester})
        </span>
      ),
    },
    {
      id: "dates",
      header: "Issue / Due Date",
      cell: (row) => (
        <div className="text-xs">
          <p className="text-slate-400">Due: {row.dueDate}</p>
          <p className="text-[11px] text-slate-500">Issued: {row.issueDate}</p>
        </div>
      ),
    },
    {
      id: "net",
      header: "Net Payable",
      accessorKey: "netPayable",
      sortable: true,
      cell: (row) => (
        <span className="font-mono text-xs font-semibold text-slate-200">
          {formatMoney(row.netPayable)}
        </span>
      ),
    },
    {
      id: "paid",
      header: "Paid",
      accessorKey: "paidAmount",
      sortable: true,
      cell: (row) => (
        <span className="font-mono text-xs font-semibold text-emerald-400">
          {formatMoney(row.paidAmount)}
        </span>
      ),
    },
    {
      id: "outstanding",
      header: "Outstanding",
      accessorKey: "outstandingAmount",
      sortable: true,
      cell: (row) => (
        <span
          className={`font-mono text-xs font-semibold ${
            row.outstandingAmount > 0 ? "text-rose-400" : "text-slate-400"
          }`}
        >
          {formatMoney(row.outstandingAmount)}
        </span>
      ),
    },
    {
      id: "status",
      header: "Status",
      accessorKey: "status",
      sortable: true,
      cell: (row) => getStatusBadge(row.status),
    },
    {
      id: "actions",
      header: "Actions",
      cell: (row) => (
        <div className="flex items-center gap-1.5">
          <Link href={`/app/finance/invoices/${row.id}`}>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 text-xs text-slate-300 hover:text-white"
            >
              <Eye className="h-3.5 w-3.5 mr-1" />
              View
            </Button>
          </Link>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-medium text-slate-400 mb-1">
            <Link
              href="/app/finance"
              className="hover:text-slate-200 transition-colors"
            >
              Finance
            </Link>
            <span>/</span>
            <span className="text-slate-200">Invoices</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <CreditCard className="h-6 w-6 text-indigo-400" />
            Billing Invoices Ledger
          </h1>
          <p className="mt-1 text-xs text-slate-400 max-w-2xl">
            Centralized billing documents across tuition, laboratory, hostel,
            and institutional services with real-time settlement tracking.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="primary"
            size="sm"
            onClick={() => setCreateModalOpen(true)}
            className="gap-1.5 text-xs"
          >
            <Plus className="h-3.5 w-3.5" />
            Create Invoice
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          title="Total Invoiced Net"
          value={formatMoney(totalBilled)}
          description="Cumulative net billings"
          icon={<DollarSign className="h-5 w-5 text-indigo-400" />}
        />
        <StatCard
          title="Collected Realization"
          value={formatMoney(totalCollected)}
          description="Verified bank/counter credits"
          icon={<CheckCircle2 className="h-5 w-5 text-emerald-400" />}
        />
        <StatCard
          title="Outstanding Receivable"
          value={formatMoney(totalOutstanding)}
          description="Student balances due"
          icon={<AlertTriangle className="h-5 w-5 text-rose-400" />}
        />
      </div>

      {/* Filters Toolbar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <Input
            placeholder="Search invoice number, student, roll number..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 h-9 text-xs bg-slate-950/60 border-slate-800 text-slate-200"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Select
            value={programFilter}
            onChange={(e) => setProgramFilter(e.target.value)}
            className="h-9 text-xs w-48 bg-slate-950/60 border-slate-800 text-slate-200"
          >
            <option value="ALL">All Academic Programs</option>
            <option value="Computer Science">Computer Science</option>
            <option value="Electronics">Electronics</option>
            <option value="AI">AI & Data Science</option>
          </Select>

          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="h-9 text-xs w-36 bg-slate-950/60 border-slate-800 text-slate-200"
          >
            <option value="ALL">All Statuses</option>
            <option value="PAID">Paid</option>
            <option value="PARTIALLY_PAID">Partially Paid</option>
            <option value="ISSUED">Issued</option>
            <option value="OVERDUE">Overdue</option>
            <option value="CANCELLED">Cancelled</option>
          </Select>
        </div>
      </div>

      {/* Invoices DataGrid */}
      <DataGrid
        data={filteredInvoices}
        columns={columns}
        keyExtractor={(row) => row.id}
        loading={loading}
        emptyState={
          <div className="py-12 text-center">
            <CreditCard className="mx-auto h-10 w-10 text-slate-600 mb-2" />
            <p className="text-sm font-semibold text-slate-300">
              No Invoices Found
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Try clearing filters or generate a new student billing invoice.
            </p>
          </div>
        }
      />

      {/* Create Invoice Dialog */}
      <Dialog open={createModalOpen} onOpenChange={setCreateModalOpen}>
        <DialogContent className="max-w-md bg-slate-900 border-slate-800 text-slate-200">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold text-white flex items-center gap-2">
              <CreditCard className="h-5 w-5 text-indigo-400" />
              Dispatch New Billing Invoice
            </DialogTitle>
          </DialogHeader>

          <form onSubmit={handleCreateInvoice} className="space-y-4 py-2">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Select Candidate <span className="text-rose-400">*</span>
              </label>
              <Select
                value={selectedStudentId}
                onChange={(e) => setSelectedStudentId(e.target.value)}
                className="h-8 text-xs bg-slate-950 border-slate-800"
              >
                {MOCK_STUDENTS.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.firstName} {s.lastName} ({s.rollNumber})
                  </option>
                ))}
              </Select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Reference Fee Scheme
              </label>
              <Select
                value={selectedStructureId}
                onChange={(e) => {
                  setSelectedStructureId(e.target.value);
                  const found = structures.find((f) => f.id === e.target.value);
                  if (found) setCustomGross(found.grossTotal);
                }}
                className="h-8 text-xs bg-slate-950 border-slate-800"
              >
                {structures.map((fs) => (
                  <option key={fs.id} value={fs.id}>
                    {fs.name} ({formatMoney(fs.grossTotal)})
                  </option>
                ))}
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Gross Amount (₹) <span className="text-rose-400">*</span>
                </label>
                <Input
                  type="number"
                  min="1"
                  required
                  value={customGross.toString()}
                  onChange={(e) =>
                    setCustomGross(parseFloat(e.target.value) || 0)
                  }
                  className="h-8 text-xs font-mono bg-slate-950 border-slate-800"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Due Date <span className="text-rose-400">*</span>
                </label>
                <Input
                  type="date"
                  required
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="h-8 text-xs bg-slate-950 border-slate-800"
                />
              </div>
            </div>

            <DialogFooter className="pt-3 border-t border-slate-800">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setCreateModalOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                disabled={creating}
              >
                {creating ? "Generating..." : "Generate Invoice"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
