"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  Receipt as ReceiptIcon,
  Search,
  Filter,
  Eye,
  Printer,
  FileText,
  DollarSign,
  CreditCard,
  Building2,
  Calendar,
} from "lucide-react";
import { DataGrid, ColumnDef } from "@/components/data-grid/data-grid";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/ui/stat-card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { useToast } from "@/components/ui/toast";
import { financeService } from "@/services/finance.service";
import { formatMoney } from "@/services/financial-calculator";
import { Receipt } from "@/types/finance";

export default function ReceiptsPage() {
  const { showToast } = useToast();
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [methodFilter, setMethodFilter] = useState<string>("ALL");

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await financeService.getReceipts();
      setReceipts(res.data);
    } catch {
      showToast({
        title: "Error",
        message: "Error loading official receipts",
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const totalReceiptsAmount = useMemo(() => {
    return receipts.reduce((sum, r) => sum + r.amount, 0);
  }, [receipts]);

  const filteredReceipts = useMemo(() => {
    return receipts.filter((r) => {
      const matchesSearch =
        searchQuery === "" ||
        r.receiptNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.studentName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.rollNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.transactionRef.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.invoiceNumber.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesMethod =
        methodFilter === "ALL" || r.paymentMethod === methodFilter;

      return matchesSearch && matchesMethod;
    });
  }, [receipts, searchQuery, methodFilter]);

  const columns: ColumnDef<Receipt>[] = [
    {
      id: "receiptNumber",
      header: "Receipt Voucher #",
      accessorKey: "receiptNumber",
      sortable: true,
      cell: ({ row }) => (
        <Link
          href={`/app/finance/receipts/${row.id}`}
          className="font-mono text-sm font-semibold text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 hover:underline"
        >
          {row.receiptNumber}
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
      header: "Billed Invoice",
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
      id: "paymentMethod",
      header: "Payment Method",
      accessorKey: "paymentMethod",
      cell: ({ row }) => (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
          {row.paymentMethod.replace("_", " ")}
        </span>
      ),
    },
    {
      id: "date",
      header: "Issued Date",
      accessorKey: "date",
      sortable: true,
      cell: ({ row }) => (
        <span className="text-xs text-slate-600 dark:text-slate-300">
          {row.date}
        </span>
      ),
    },
    {
      id: "amount",
      header: "Settled Amount",
      accessorKey: "amount",
      sortable: true,
      cell: ({ row }) => (
        <span className="font-bold text-slate-900 dark:text-white">
          {formatMoney(row.amount)}
        </span>
      ),
    },
    {
      id: "status",
      header: "Status",
      accessorKey: "status",
      cell: ({ row }) => (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
          {row.status}
        </span>
      ),
    },
    {
      id: "actions",
      header: "Actions",
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <Link href={`/app/finance/receipts/${row.id}`}>
            <Button variant="ghost" size="sm" className="h-8 px-2 text-xs">
              <Eye className="w-3.5 h-3.5 mr-1" />
              View
            </Button>
          </Link>
          <Link href={`/app/finance/receipts/${row.id}?print=true`}>
            <Button variant="outline" size="sm" className="h-8 px-2 text-xs">
              <Printer className="w-3.5 h-3.5 mr-1 text-slate-500" />
              Print
            </Button>
          </Link>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
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
              Receipts
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Official Receipts Archive & Vouchers
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Immutable financial payment vouchers with unique audit numbers and
            payment tracking.
          </p>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          title="Total Receipts Value"
          value={formatMoney(totalReceiptsAmount)}
          description="Cumulative institutional fee settlements"
          icon={<DollarSign className="w-5 h-5 text-emerald-600" />}
        />
        <StatCard
          title="Receipts Issued"
          value={receipts.length.toString()}
          description="Validated electronic fee vouchers"
          icon={<ReceiptIcon className="w-5 h-5 text-blue-600" />}
        />
        <StatCard
          title="Audit Integrity"
          value="100% Immutable"
          description="Direct double-entry ledger allocation"
          icon={<Building2 className="w-5 h-5 text-teal-600" />}
        />
      </div>

      {/* Filter and Search */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-white p-4 rounded-xl border border-slate-200 dark:bg-slate-900 dark:border-slate-800">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <Input
            placeholder="Search Receipt #, Student, UTR..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 text-sm"
          />
        </div>

        <div className="flex items-center gap-2.5 w-full sm:w-auto">
          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
            <Filter className="w-3.5 h-3.5" />
            Channel:
          </div>
          <Select
            value={methodFilter}
            onChange={(e) => setMethodFilter(e.target.value)}
            className="text-xs h-9 w-40"
          >
            <option value="ALL">All Methods</option>
            <option value="UPI">UPI</option>
            <option value="BANK_TRANSFER">Bank Transfer</option>
            <option value="CARD">Card</option>
            <option value="CASH">Cash</option>
            <option value="CHEQUE">Cheque</option>
            <option value="ONLINE">Online</option>
          </Select>
        </div>
      </div>

      {/* Main DataGrid */}
      <DataGrid
        columns={columns}
        data={filteredReceipts}
        loading={loading}
        keyExtractor={(row) => row.id}
        emptyMessage="No official receipts found matching the filters."
      />
    </div>
  );
}
