"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { financeService } from "@/services/finance.service";
import type { FinanceDashboard, StudentFinancialSummary } from "@campusos/types";

export default function FinanceHubPage() {
  const { hasPermission, hasRole } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<FinanceDashboard | null>(null);
  const [studentSummary, setStudentSummary] = useState<StudentFinancialSummary | null>(null);

  const isStudent = hasRole("STUDENT");

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);

        if (isStudent) {
          const res = await apiFetch<StudentFinancialSummary>("/api/v1/finance/students/me/statement");
          setStudentSummary(res.data);
        } else {
          const res = await apiFetch<FinanceDashboard>("/api/v1/finance/dashboard");
          setDashboard(res.data);
        }
      } catch {
        if (isStudent) {
          const stmtRes = await financeService.getStudentStatement();
          setStudentSummary(stmtRes.data as unknown as StudentFinancialSummary);
        } else {
          const dashRes = await financeService.getDashboard();
          setDashboard(dashRes.data as unknown as FinanceDashboard);
        }
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [isStudent]);

  const formatCurrency = (amount: number | string | undefined) => {
    const num = typeof amount === "string" ? parseFloat(amount) : (amount ?? 0);
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(num);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
              CampusOS Engine
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">Step 8 Finance & Billing</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            {isStudent ? "My Financial Ledger & Fees" : "Finance, Fees & Billing Engine"}
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {isStudent
              ? "View outstanding fee balance, invoice snapshots, payment history, and download official receipts."
              : "Institutional fee structures, student billing assignments, payments, multi-invoice allocations, and refunds."}
          </p>
        </div>

        {!isStudent && (
          <div className="flex flex-wrap items-center gap-2.5">
            {hasPermission("invoices:create") && (
              <Link
                href="/app/finance/invoices"
                className="inline-flex items-center justify-center rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white shadow-xs hover:bg-emerald-700 transition"
              >
                + Generate Invoice
              </Link>
            )}
            {hasPermission("payments:create") && (
              <Link
                href="/app/finance/payments"
                className="inline-flex items-center justify-center rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-xs hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 transition"
              >
                Record Payment
              </Link>
            )}
          </div>
        )}
      </div>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300">
          <p className="font-semibold">Unable to load financial dashboard</p>
          <p className="mt-0.5">{error}</p>
        </div>
      )}

      {/* KPI Cards: Institutional View */}
      {!isStudent && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Total Billed */}
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider dark:text-slate-400">
                Total Billed
              </span>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-900 dark:text-white">
                  {loading ? "..." : formatCurrency(dashboard?.total_billed)}
                </span>
              </div>
              <p className="mt-1 text-xs text-slate-500">Gross billing across institutional invoices</p>
            </div>

            {/* Total Collected */}
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500 uppercase tracking-wider dark:text-slate-400">
                  Total Collected
                </span>
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                  {loading ? "..." : formatCurrency(dashboard?.total_collected)}
                </span>
              </div>
              <p className="mt-1 text-xs text-slate-500">Successfully reconciled inward payments</p>
            </div>

            {/* Total Outstanding */}
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider dark:text-slate-400">
                Outstanding Balance
              </span>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-amber-600 dark:text-amber-400">
                  {loading ? "..." : formatCurrency(dashboard?.total_outstanding)}
                </span>
              </div>
              <p className="mt-1 text-xs text-slate-500">Current receivables from active students</p>
            </div>

            {/* Overdue Total */}
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500 uppercase tracking-wider dark:text-slate-400">
                  Overdue Amount
                </span>
                <span className="h-2 w-2 rounded-full bg-rose-500" />
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-rose-600 dark:text-rose-400">
                  {loading ? "..." : formatCurrency(dashboard?.total_overdue)}
                </span>
              </div>
              <p className="mt-1 text-xs text-slate-500">Past due date requiring follow-up</p>
            </div>
          </div>

          {/* Navigation Matrix Subsections */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <Link
              href="/app/finance/fee-structures"
              className="group block rounded-xl border border-slate-200 bg-white p-6 shadow-xs hover:border-emerald-500 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900 dark:hover:border-emerald-500"
            >
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-slate-900 group-hover:text-emerald-600 transition dark:text-white dark:group-hover:text-emerald-400">
                  Fee Structures Matrix
                </h3>
                <span className="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded-full dark:bg-slate-800 dark:text-slate-300">
                  {dashboard?.active_fee_structures_count ?? 0} Active
                </span>
              </div>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                Configure program quotas, semester slabs, tuition and lab heads with version control.
              </p>
            </Link>

            <Link
              href="/app/finance/invoices"
              className="group block rounded-xl border border-slate-200 bg-white p-6 shadow-xs hover:border-emerald-500 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900 dark:hover:border-emerald-500"
            >
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-slate-900 group-hover:text-emerald-600 transition dark:text-white dark:group-hover:text-emerald-400">
                  Invoicing & Billing Ledger
                </h3>
                <span className="text-xs bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full dark:bg-emerald-950/60 dark:text-emerald-400">
                  Live Billing
                </span>
              </div>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                Generate student invoices, apply fee concessions, issue legally binding bills, and manage overdue statuses.
              </p>
            </Link>

            <Link
              href="/app/finance/payments"
              className="group block rounded-xl border border-slate-200 bg-white p-6 shadow-xs hover:border-emerald-500 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900 dark:hover:border-emerald-500"
            >
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-slate-900 group-hover:text-emerald-600 transition dark:text-white dark:group-hover:text-emerald-400">
                  Payment Collection & Allocation
                </h3>
                <span className="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded-full dark:bg-slate-800 dark:text-slate-300">
                  Multi-Invoice
                </span>
              </div>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                Record receipts across UPI, NEFT, Card, and Cash. Allocate across multiple invoices with instant receipt generation.
              </p>
            </Link>

            <Link
              href="/app/finance/receipts"
              className="group block rounded-xl border border-slate-200 bg-white p-6 shadow-xs hover:border-emerald-500 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900 dark:hover:border-emerald-500"
            >
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-slate-900 group-hover:text-emerald-600 transition dark:text-white dark:group-hover:text-emerald-400">
                  Receipts Archive
                </h3>
                <span className="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded-full dark:bg-slate-800 dark:text-slate-300">
                  Immutable
                </span>
              </div>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                Forensic payment acknowledgment vouchers with sequential numbering and student reference tracking.
              </p>
            </Link>

            <Link
              href="/app/finance/scholarships"
              className="group block rounded-xl border border-slate-200 bg-white p-6 shadow-xs hover:border-emerald-500 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900 dark:hover:border-emerald-500"
            >
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-slate-900 group-hover:text-emerald-600 transition dark:text-white dark:group-hover:text-emerald-400">
                  Scholarships & Concessions
                </h3>
                <span className="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded-full dark:bg-slate-800 dark:text-slate-300">
                  {dashboard?.approved_scholarships_count ?? 0} Approved
                </span>
              </div>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                Institutional merit waivers, need-based aid, sibling concessions, and sports quota reductions.
              </p>
            </Link>

            <Link
              href="/app/finance/refunds"
              className="group block rounded-xl border border-slate-200 bg-white p-6 shadow-xs hover:border-emerald-500 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900 dark:hover:border-emerald-500"
            >
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-slate-900 group-hover:text-emerald-600 transition dark:text-white dark:group-hover:text-emerald-400">
                  Refund Processing
                </h3>
                <span className="text-xs bg-rose-50 text-rose-700 px-2 py-0.5 rounded-full dark:bg-rose-950/60 dark:text-rose-400">
                  {dashboard?.pending_refunds_count ?? 0} Pending
                </span>
              </div>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                Authoritative multi-stage approval workflow for payment refunds with strict balance limits.
              </p>
            </Link>
          </div>

          {/* Recent Invoices & Payments Tables */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recent Invoices */}
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:border-slate-800 dark:bg-slate-900">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-slate-900 dark:text-white">Recent Invoices</h3>
                <Link href="/app/finance/invoices" className="text-xs text-emerald-600 hover:underline dark:text-emerald-400">
                  View all
                </Link>
              </div>
              {dashboard?.recent_invoices && dashboard.recent_invoices.length > 0 ? (
                <div className="divide-y divide-slate-100 dark:divide-slate-800 text-sm">
                  {dashboard.recent_invoices.map((inv) => (
                    <div key={inv.id} className="py-3 flex items-center justify-between">
                      <div>
                        <div className="font-medium text-slate-900 dark:text-white">{inv.invoice_number}</div>
                        <div className="text-xs text-slate-500">Due: {inv.due_date}</div>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold text-slate-900 dark:text-white">{formatCurrency(inv.net_payable)}</div>
                        <span
                          className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${
                            inv.status === "PAID"
                              ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                              : inv.status === "OVERDUE"
                              ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
                              : "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300"
                          }`}
                        >
                          {inv.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-sm text-slate-500">No invoices generated yet.</div>
              )}
            </div>

            {/* Recent Payments */}
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:border-slate-800 dark:bg-slate-900">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-slate-900 dark:text-white">Recent Payments</h3>
                <Link href="/app/finance/payments" className="text-xs text-emerald-600 hover:underline dark:text-emerald-400">
                  View all
                </Link>
              </div>
              {dashboard?.recent_payments && dashboard.recent_payments.length > 0 ? (
                <div className="divide-y divide-slate-100 dark:divide-slate-800 text-sm">
                  {dashboard.recent_payments.map((p) => (
                    <div key={p.id} className="py-3 flex items-center justify-between">
                      <div>
                        <div className="font-medium text-slate-900 dark:text-white">{p.payment_number}</div>
                        <div className="text-xs text-slate-500">
                          {p.payment_mode} • Ref: {p.transaction_reference}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold text-emerald-600 dark:text-emerald-400">
                          {formatCurrency(p.amount)}
                        </div>
                        <div className="text-xs text-slate-500">{new Date(p.payment_date).toLocaleDateString()}</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-sm text-slate-500">No payments recorded yet.</div>
              )}
            </div>
          </div>
        </>
      )}

      {/* Student Self-Service View */}
      {isStudent && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider dark:text-slate-400">
                Total Invoiced
              </span>
              <div className="mt-3 text-2xl font-bold text-slate-900 dark:text-white">
                {loading ? "..." : formatCurrency(studentSummary?.total_invoiced)}
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider dark:text-slate-400">
                Total Paid
              </span>
              <div className="mt-3 text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                {loading ? "..." : formatCurrency(studentSummary?.total_paid)}
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:border-slate-800 dark:bg-slate-900">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider dark:text-slate-400">
                Outstanding Due
              </span>
              <div className="mt-3 text-2xl font-bold text-rose-600 dark:text-rose-400">
                {loading ? "..." : formatCurrency(studentSummary?.total_outstanding)}
              </div>
            </div>
          </div>

          {/* Student Invoices Ledger */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:border-slate-800 dark:bg-slate-900">
            <h3 className="font-semibold text-slate-900 dark:text-white mb-4">My Invoices</h3>
            {studentSummary?.invoices && studentSummary.invoices.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-700 dark:text-slate-300">
                  <thead className="bg-slate-50 text-xs uppercase text-slate-500 dark:bg-slate-800/50">
                    <tr>
                      <th className="px-4 py-3">Invoice #</th>
                      <th className="px-4 py-3">Due Date</th>
                      <th className="px-4 py-3">Net Payable</th>
                      <th className="px-4 py-3">Paid</th>
                      <th className="px-4 py-3">Balance</th>
                      <th className="px-4 py-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {studentSummary.invoices.map((inv) => (
                      <tr key={inv.id}>
                        <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{inv.invoice_number}</td>
                        <td className="px-4 py-3">{inv.due_date}</td>
                        <td className="px-4 py-3">{formatCurrency(inv.net_payable)}</td>
                        <td className="px-4 py-3 text-emerald-600">{formatCurrency(inv.paid_amount)}</td>
                        <td className="px-4 py-3 font-semibold text-rose-600">{formatCurrency(inv.balance_amount)}</td>
                        <td className="px-4 py-3">
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 dark:bg-slate-800">
                            {inv.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8 text-sm text-slate-500">No invoices have been issued to you.</div>
            )}
          </div>

          {/* Student Receipts Archive */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:border-slate-800 dark:bg-slate-900">
            <h3 className="font-semibold text-slate-900 dark:text-white mb-4">Official Payment Receipts</h3>
            {studentSummary?.receipts && studentSummary.receipts.length > 0 ? (
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {studentSummary.receipts.map((rcp) => (
                  <div key={rcp.id} className="py-3 flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-slate-900 dark:text-white">{rcp.receipt_number}</div>
                      <div className="text-xs text-slate-500">
                        Date: {new Date(rcp.issued_at).toLocaleDateString()} • Mode: {rcp.payment_mode}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-emerald-600 dark:text-emerald-400">
                        {formatCurrency(rcp.amount_paid)}
                      </div>
                      <div className="text-xs text-slate-400 font-mono">Ref: {rcp.transaction_reference}</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-sm text-slate-500">No payment receipts available.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
