"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { StatCard } from "@/components/ui/stat-card";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { financeService } from "@/services/finance.service";
import { InvoiceItem, PaymentTransactionItem } from "@/mocks/finance.mock";
import {
  DollarSign,
  CreditCard,
  Receipt,
  Gift,
  ArrowRight,
  TrendingUp,
  AlertCircle,
  Plus,
} from "lucide-react";

export function AccountsDashboard() {
  const [invoices, setInvoices] = useState<InvoiceItem[]>([]);
  const [payments, setPayments] = useState<PaymentTransactionItem[]>([]);

  useEffect(() => {
    financeService.getInvoices().then((res) => setInvoices(res.data));
    financeService.getPayments().then((res) => setPayments(res.data));
  }, []);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900 via-slate-900/90 to-emerald-950/40 p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-400 border border-emerald-500/20 mb-2">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            Finance & Bursar Comptroller Office
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Institutional Accounts & Treasury
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Tuition fee schedules, student billing, online UPI/bank receipts, and scholarships.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/app/finance/invoices">
            <Button variant="primary" size="sm" leftIcon={<CreditCard className="h-3.5 w-3.5" />}>
              Issue Fee Invoices
            </Button>
          </Link>
          <Link href="/app/finance/receipts">
            <Button variant="outline" size="sm" leftIcon={<Receipt className="h-3.5 w-3.5" />}>
              Official Receipts
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Annual Billed"
          value="₹31.2 Cr"
          description="Academic & hostel fees combined"
          variant="indigo"
          icon={<DollarSign className="h-4 w-4" />}
        />
        <StatCard
          label="Total Cleared & Realized"
          value="₹28.64 Cr"
          change={{ value: "91.8% rate", trend: "up" }}
          description="Verified bank & counter receipts"
          variant="emerald"
          icon={<Receipt className="h-4 w-4" />}
        />
        <StatCard
          label="Outstanding Receivables"
          value="₹2.56 Cr"
          change={{ value: "84 overdue invoices", trend: "down" }}
          description="Awaiting 2nd installment clearance"
          variant="amber"
          icon={<CreditCard className="h-4 w-4" />}
        />
        <StatCard
          label="Merit Scholarships Disbursed"
          value="₹45.0 L"
          description="Awarded across 32 deserving scholars"
          variant="sky"
          icon={<Gift className="h-4 w-4" />}
        />
      </div>

      {/* Recent Transactions & Overdue Invoices Split */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Payment Transactions */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Recent Verified Receipts</CardTitle>
              <CardDescription>Real-time fee reconciliations via UPI & Net Banking.</CardDescription>
            </div>
            <Link href="/app/finance/payments">
              <Button variant="ghost" size="sm" className="text-xs text-slate-400 hover:text-white">
                All Transactions <ArrowRight className="h-3 w-3 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="space-y-3">
            {payments.map((p) => (
              <div
                key={p.id}
                className="flex items-center justify-between p-3 rounded-lg border border-slate-800 bg-slate-950/40 text-xs"
              >
                <div>
                  <div className="font-semibold text-white">
                    {p.studentName} ({p.rollNumber})
                  </div>
                  <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                    {p.receiptNumber} • {p.paymentMode}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-mono font-bold text-emerald-400 text-sm">
                    +₹{p.amount.toLocaleString()}
                  </div>
                  <div className="text-[10px] text-slate-500">{p.paymentDate}</div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Student Invoices Roster */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Student Invoices & Dues</CardTitle>
              <CardDescription>Installment statuses for Odd Semester 2026-27.</CardDescription>
            </div>
            <Link href="/app/finance/invoices">
              <Button variant="ghost" size="sm" className="text-xs text-slate-400 hover:text-white">
                Invoices Ledger <ArrowRight className="h-3 w-3 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="space-y-3">
            {invoices.map((inv) => (
              <div
                key={inv.id}
                className="flex items-center justify-between p-3 rounded-lg border border-slate-800 bg-slate-950/40 text-xs"
              >
                <div>
                  <div className="font-semibold text-white">
                    {inv.studentName} ({inv.rollNumber})
                  </div>
                  <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                    {inv.invoiceNumber} • Due: {inv.dueDate}
                  </div>
                </div>
                <div className="text-right flex items-center gap-3">
                  <div>
                    <div className="font-mono font-bold text-white">
                      ₹{inv.totalAmount.toLocaleString()}
                    </div>
                    {inv.balanceAmount > 0 && (
                      <div className="text-[10px] text-red-400 font-mono font-medium">
                        Due: ₹{inv.balanceAmount.toLocaleString()}
                      </div>
                    )}
                  </div>
                  <Badge variant={inv.status === "PAID" ? "success" : "warning"} dot>
                    {inv.status}
                  </Badge>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
