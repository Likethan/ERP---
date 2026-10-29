"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  DollarSign,
  CreditCard,
  Building2,
  FileText,
  Clock,
  AlertTriangle,
  CheckCircle2,
  Users,
  Award,
  RotateCcw,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  Receipt as ReceiptIcon,
  BarChart3,
  Calendar,
  Layers,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/ui/stat-card";
import { useAuth } from "@/lib/auth-context";
import {
  financeService,
  StudentFeeStatement,
} from "@/services/finance.service";
import { formatMoney } from "@/services/financial-calculator";
import {
  FinanceDashboardSummary,
  StudentScholarship,
  Refund,
} from "@/types/finance";

export default function FinanceDashboardPage() {
  const { hasRole, hasPermission, user } = useAuth();
  const [summary, setSummary] = useState<FinanceDashboardSummary | null>(null);
  const [studentStatement, setStudentStatement] =
    useState<StudentFeeStatement | null>(null);
  const [studentScholarships, setStudentScholarships] = useState<
    StudentScholarship[]
  >([]);
  const [studentRefunds, setStudentRefunds] = useState<Refund[]>([]);
  const [loading, setLoading] = useState(true);

  const isStudent = hasRole("STUDENT");
  const isHOD = hasRole("HOD");
  const canRecord =
    hasPermission("finance.record_payments") ||
    hasPermission("payments:create");
  const canInvoice =
    hasPermission("finance.manage_invoices") ||
    hasPermission("invoices:create");

  useEffect(() => {
    async function loadDashboard() {
      try {
        setLoading(true);
        if (isStudent) {
          const [stmtRes, schRes, refRes] = await Promise.all([
            financeService.getStudentStatement(),
            financeService.getStudentScholarships("std-001"),
            financeService.getRefunds(),
          ]);
          setStudentStatement(stmtRes.data);
          setStudentScholarships(schRes.data);
          setStudentRefunds(
            refRes.data.filter((r) => r.studentId === "std-001"),
          );
        } else {
          const res = await financeService.getDashboardSummary();
          setSummary(res.data);
        }
      } catch (err) {
        console.error("Failed to load finance dashboard", err);
      } finally {
        setLoading(false);
      }
    }
    loadDashboard();
  }, [isStudent]);

  // =========================================================================
  // 1. STUDENT VIEW: "My Finance & Fee Ledger"
  // =========================================================================
  if (isStudent) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5 dark:border-slate-800">
          <div>
            <div className="flex items-center gap-2 text-xs text-slate-500 mb-1">
              <span>CampusOS Portal</span>
              <span>/</span>
              <span className="font-semibold text-slate-700 dark:text-slate-300">
                My Finance
              </span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Student Fee Ledger & Billing Statement
            </h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Personal academic fee account, invoice breakdown, paid receipts,
              and scholarship grants.
            </p>
          </div>
        </div>

        {/* Student KPIs */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Total Billed"
            value={formatMoney(studentStatement?.total_billed || 0)}
            description="Institutional tuition & campus fee dues"
            icon={<DollarSign className="w-5 h-5 text-slate-600" />}
          />
          <StatCard
            title="Paid to Date"
            value={formatMoney(studentStatement?.total_paid || 0)}
            description="Settled fee payments with receipts"
            icon={<CheckCircle2 className="w-5 h-5 text-emerald-600" />}
          />
          <StatCard
            title="Outstanding Payable"
            value={formatMoney(studentStatement?.total_due || 0)}
            description="Pending settlement for current term"
            icon={<Clock className="w-5 h-5 text-amber-600" />}
          />
          <StatCard
            title="Active Scholarships"
            value={`${studentScholarships.length} Schemes`}
            description="Institutional merit/means grant waivers"
            icon={<Award className="w-5 h-5 text-teal-600" />}
          />
        </div>

        {/* Current Invoices & Receipts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Current Invoices */}
          <div className="rounded-xl border border-slate-200 bg-white shadow-xs dark:bg-slate-900 dark:border-slate-800 overflow-hidden">
            <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-slate-900 dark:text-white">
                  My Academic Invoices
                </h2>
                <p className="text-xs text-slate-500">
                  Official fee demand vouchers
                </p>
              </div>
            </div>

            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              {studentStatement?.invoices &&
              studentStatement.invoices.length > 0 ? (
                studentStatement.invoices.map((inv) => (
                  <div
                    key={inv.id}
                    className="p-4 flex items-center justify-between hover:bg-slate-50/50 dark:hover:bg-slate-800/40"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <Link
                          href={`/app/finance/invoices/${inv.id}`}
                          className="font-mono text-xs font-bold text-blue-600 hover:underline dark:text-blue-400"
                        >
                          {inv.invoiceNumber}
                        </Link>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            inv.status === "PAID"
                              ? "bg-emerald-100 text-emerald-800"
                              : inv.status === "OVERDUE"
                                ? "bg-rose-100 text-rose-800"
                                : "bg-amber-100 text-amber-800"
                          }`}
                        >
                          {inv.status}
                        </span>
                      </div>
                      <div className="text-xs text-slate-500 mt-1">
                        Due: {inv.dueDate} • Semester {inv.semester}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-bold text-slate-900 dark:text-white">
                        {formatMoney(inv.netPayable)}
                      </div>
                      <div className="text-xs text-slate-500">
                        {inv.outstandingAmount > 0 ? (
                          <span className="text-amber-600 font-semibold">
                            Due: {formatMoney(inv.outstandingAmount)}
                          </span>
                        ) : (
                          <span className="text-emerald-600 font-medium">
                            Fully Settled
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-8 text-center text-xs text-slate-500">
                  No invoices issued.
                </div>
              )}
            </div>
          </div>

          {/* Payment Receipts */}
          <div className="rounded-xl border border-slate-200 bg-white shadow-xs dark:bg-slate-900 dark:border-slate-800 overflow-hidden">
            <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-slate-900 dark:text-white">
                  Verified Receipts
                </h2>
                <p className="text-xs text-slate-500">
                  Official proof of payment vouchers
                </p>
              </div>
            </div>

            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              {studentStatement?.receipts &&
              studentStatement.receipts.length > 0 ? (
                studentStatement.receipts.map((rec) => (
                  <div
                    key={rec.id}
                    className="p-4 flex items-center justify-between hover:bg-slate-50/50 dark:hover:bg-slate-800/40"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <Link
                          href={`/app/finance/receipts/${rec.id}`}
                          className="font-mono text-xs font-bold text-emerald-600 hover:underline dark:text-emerald-400"
                        >
                          {rec.receiptNumber}
                        </Link>
                        <span className="text-[10px] bg-slate-100 px-2 py-0.5 rounded text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                          {rec.paymentMethod}
                        </span>
                      </div>
                      <div className="text-xs text-slate-500 mt-1 font-mono">
                        {rec.transactionRef}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-bold text-emerald-700 dark:text-emerald-400">
                        {formatMoney(rec.amount)}
                      </div>
                      <Link
                        href={`/app/finance/receipts/${rec.id}`}
                        className="text-xs text-slate-500 hover:text-slate-900 underline mt-0.5 inline-block"
                      >
                        Download PDF Voucher
                      </Link>
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-8 text-center text-xs text-slate-500">
                  No payment receipts yet.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Scholarships & Assistance */}
        {studentScholarships.length > 0 && (
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs dark:bg-slate-900 dark:border-slate-800">
            <h2 className="text-sm font-bold text-slate-900 dark:text-white mb-3">
              Approved Fee Concessions & Scholarships
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {studentScholarships.map((s) => (
                <div
                  key={s.id}
                  className="rounded-lg border border-emerald-100 bg-emerald-50/50 p-4 text-xs dark:bg-emerald-950/20 dark:border-emerald-800"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="font-bold text-emerald-950 text-sm dark:text-emerald-300">
                        {s.scholarshipName}
                      </span>
                      <p className="text-emerald-800/80 mt-0.5">
                        Awarded on {s.grantedDate}
                      </p>
                    </div>
                    <span className="font-black text-emerald-700 text-sm dark:text-emerald-400">
                      -{formatMoney(s.discountAmount)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // =========================================================================
  // 2. INSTITUTIONAL VIEW: Accounts / HOD / Admin Operations Dashboard
  // =========================================================================
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 mb-1">
            <span>CampusOS Core</span>
            <span>/</span>
            <span className="font-semibold text-slate-700 dark:text-slate-300">
              {isHOD ? "Departmental Finance" : "Institutional Finance"}
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Finance & Revenue Operations Dashboard
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {isHOD
              ? "Department student billing oversight, collection tracking, and outstanding recovery queues."
              : "Institutional billing lifecycle, fee structures, receipts ledger, multi-invoice allocations, and debt recovery."}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {canInvoice && (
            <Link href="/app/finance/invoices">
              <Button variant="outline" size="sm" className="gap-1.5 text-xs">
                <FileText className="w-3.5 h-3.5" />
                Invoices Ledger
              </Button>
            </Link>
          )}
          {canRecord && (
            <Link href="/app/finance/payments">
              <Button
                variant="primary"
                size="sm"
                className="gap-1.5 text-xs bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                <CreditCard className="w-3.5 h-3.5" />
                Record Payment
              </Button>
            </Link>
          )}
        </div>
      </div>

      {/* Primary KPI Overview Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Invoiced"
          value={formatMoney(summary?.totalBilled || 0)}
          description="Gross fee demand raised across programs"
          icon={<DollarSign className="w-5 h-5 text-slate-600" />}
        />
        <StatCard
          title="Total Realized Collections"
          value={formatMoney(summary?.totalCollected || 0)}
          description={`${summary?.collectionRatePercent || 0}% realization efficiency`}
          icon={<CheckCircle2 className="w-5 h-5 text-emerald-600" />}
        />
        <StatCard
          title="Outstanding Balance"
          value={formatMoney(summary?.totalOutstanding || 0)}
          description="Active student account receivables"
          icon={<Clock className="w-5 h-5 text-amber-600" />}
        />
        <StatCard
          title="Overdue Arrears"
          value={formatMoney(summary?.totalOverdue || 0)}
          description="Past due date requiring debt collection"
          icon={<AlertTriangle className="w-5 h-5 text-rose-600" />}
        />
      </div>

      {/* Operational Action Queues */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">
              Operational Action Queues
            </h2>
            <p className="text-xs text-slate-500">
              Pending tasks requiring finance officer intervention
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <Link
            href="/app/finance/payments"
            className="p-3 rounded-lg border border-slate-200 bg-slate-50/70 hover:border-emerald-500 transition text-xs dark:bg-slate-800/40 dark:border-slate-700"
          >
            <div className="text-slate-500">Pending Payments</div>
            <div className="text-xl font-bold text-slate-900 dark:text-white mt-1">
              {summary?.operationalQueues.pendingPaymentsCount || 0}
            </div>
            <div className="text-[10px] text-slate-400 mt-1">
              Unconfirmed txns
            </div>
          </Link>

          <Link
            href="/app/finance/invoices?status=OVERDUE"
            className="p-3 rounded-lg border border-rose-200 bg-rose-50/50 hover:border-rose-400 transition text-xs dark:bg-rose-950/20 dark:border-rose-900"
          >
            <div className="text-rose-700 dark:text-rose-400">
              Overdue Invoices
            </div>
            <div className="text-xl font-bold text-rose-800 dark:text-rose-300 mt-1">
              {summary?.operationalQueues.overdueInvoicesCount || 0}
            </div>
            <div className="text-[10px] text-rose-600/70 mt-1">
              Debt recovery queue
            </div>
          </Link>

          <Link
            href="/app/finance/refunds"
            className="p-3 rounded-lg border border-amber-200 bg-amber-50/50 hover:border-amber-400 transition text-xs dark:bg-amber-950/20 dark:border-amber-900"
          >
            <div className="text-amber-700 dark:text-amber-400">
              Refund Petitions
            </div>
            <div className="text-xl font-bold text-amber-800 dark:text-amber-300 mt-1">
              {summary?.operationalQueues.refundRequestsCount || 0}
            </div>
            <div className="text-[10px] text-amber-600/70 mt-1">
              Awaiting audit
            </div>
          </Link>

          <Link
            href="/app/finance/scholarships"
            className="p-3 rounded-lg border border-slate-200 bg-slate-50/70 hover:border-emerald-500 transition text-xs dark:bg-slate-800/40 dark:border-slate-700"
          >
            <div className="text-slate-500">Scholarship Approvals</div>
            <div className="text-xl font-bold text-slate-900 dark:text-white mt-1">
              {summary?.operationalQueues.scholarshipApprovalsCount || 0}
            </div>
            <div className="text-[10px] text-slate-400 mt-1">
              Committee review
            </div>
          </Link>

          <Link
            href="/app/finance/payments"
            className="p-3 rounded-lg border border-slate-200 bg-slate-50/70 hover:border-emerald-500 transition text-xs dark:bg-slate-800/40 dark:border-slate-700"
          >
            <div className="text-slate-500">Unallocated Float</div>
            <div className="text-xl font-bold text-slate-900 dark:text-white mt-1">
              {summary?.operationalQueues.unallocatedPaymentsCount || 0}
            </div>
            <div className="text-[10px] text-slate-400 mt-1">
              Unlinked payments
            </div>
          </Link>

          <Link
            href="/app/finance/receipts"
            className="p-3 rounded-lg border border-emerald-200 bg-emerald-50/50 hover:border-emerald-400 transition text-xs dark:bg-emerald-950/20 dark:border-emerald-900"
          >
            <div className="text-emerald-700 dark:text-emerald-400">
              Receipts Issued
            </div>
            <div className="text-xl font-bold text-emerald-800 dark:text-emerald-300 mt-1">
              {summary?.operationalQueues.recentlyIssuedReceiptsCount || 0}
            </div>
            <div className="text-[10px] text-emerald-600/70 mt-1">
              Archived vouchers
            </div>
          </Link>
        </div>
      </div>

      {/* Collection Intelligence & Overdue Aging */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Overdue Aging Analysis */}
        <div className="lg:col-span-2 rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-slate-900 dark:text-white">
                Arrears Debt Aging Analysis
              </h2>
              <p className="text-xs text-slate-500">
                Breakdown of outstanding balance by delinquency duration
              </p>
            </div>
            <Link
              href="/app/finance/reports"
              className="text-xs font-semibold text-emerald-600 hover:underline flex items-center gap-1"
            >
              Full Aging Report
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-4">
            {summary?.agingBuckets && summary.agingBuckets.length > 0 ? (
              summary.agingBuckets.map((bucket) => {
                const totalOut = summary.totalOutstanding || 1;
                const pct = Math.min(
                  100,
                  Math.round((bucket.amount / totalOut) * 100),
                );
                return (
                  <div key={bucket.bucket} className="space-y-1.5 text-xs">
                    <div className="flex justify-between font-medium">
                      <span className="text-slate-700 dark:text-slate-300">
                        {bucket.label} ({bucket.invoiceCount} invoices)
                      </span>
                      <span className="font-bold text-slate-900 dark:text-white">
                        {formatMoney(bucket.amount)} ({pct}%)
                      </span>
                    </div>
                    <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden dark:bg-slate-800">
                      <div
                        className={`h-full rounded-full transition-all ${
                          bucket.bucket === "CURRENT"
                            ? "bg-emerald-500"
                            : bucket.bucket === "DAYS_1_30"
                              ? "bg-amber-500"
                              : bucket.bucket === "DAYS_31_60"
                                ? "bg-orange-500"
                                : "bg-rose-500"
                        }`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="text-xs text-slate-500">
                Aging data unavailable.
              </div>
            )}
          </div>
        </div>

        {/* Right Col: Navigation Matrix */}
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800 flex flex-col justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-900 dark:text-white mb-1">
              Finance Management Hub
            </h2>
            <p className="text-xs text-slate-500 mb-4">
              Quick access to submodules
            </p>

            <div className="space-y-2 text-xs">
              <Link
                href="/app/finance/fee-categories"
                className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 hover:bg-slate-50 transition dark:border-slate-800 dark:hover:bg-slate-800/50"
              >
                <span className="font-medium text-slate-800 dark:text-slate-200">
                  1. Fee Categories
                </span>
                <ChevronRight className="w-4 h-4 text-slate-400" />
              </Link>
              <Link
                href="/app/finance/fee-structures"
                className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 hover:bg-slate-50 transition dark:border-slate-800 dark:hover:bg-slate-800/50"
              >
                <span className="font-medium text-slate-800 dark:text-slate-200">
                  2. Fee Structures Matrix
                </span>
                <ChevronRight className="w-4 h-4 text-slate-400" />
              </Link>
              <Link
                href="/app/finance/assignments"
                className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 hover:bg-slate-50 transition dark:border-slate-800 dark:hover:bg-slate-800/50"
              >
                <span className="font-medium text-slate-800 dark:text-slate-200">
                  3. Fee Assignments Ledger
                </span>
                <ChevronRight className="w-4 h-4 text-slate-400" />
              </Link>
              <Link
                href="/app/finance/invoices"
                className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 hover:bg-slate-50 transition dark:border-slate-800 dark:hover:bg-slate-800/50"
              >
                <span className="font-medium text-slate-800 dark:text-slate-200">
                  4. Invoicing & Billing
                </span>
                <ChevronRight className="w-4 h-4 text-slate-400" />
              </Link>
              <Link
                href="/app/finance/payments"
                className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 hover:bg-slate-50 transition dark:border-slate-800 dark:hover:bg-slate-800/50"
              >
                <span className="font-medium text-slate-800 dark:text-slate-200">
                  5. Payments & Collections
                </span>
                <ChevronRight className="w-4 h-4 text-slate-400" />
              </Link>
              <Link
                href="/app/finance/receipts"
                className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 hover:bg-slate-50 transition dark:border-slate-800 dark:hover:bg-slate-800/50"
              >
                <span className="font-medium text-slate-800 dark:text-slate-200">
                  6. Official Receipts
                </span>
                <ChevronRight className="w-4 h-4 text-slate-400" />
              </Link>
              <Link
                href="/app/finance/scholarships"
                className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 hover:bg-slate-50 transition dark:border-slate-800 dark:hover:bg-slate-800/50"
              >
                <span className="font-medium text-slate-800 dark:text-slate-200">
                  7. Scholarships & Waivers
                </span>
                <ChevronRight className="w-4 h-4 text-slate-400" />
              </Link>
              <Link
                href="/app/finance/refunds"
                className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 hover:bg-slate-50 transition dark:border-slate-800 dark:hover:bg-slate-800/50"
              >
                <span className="font-medium text-slate-800 dark:text-slate-200">
                  8. Refund Workflow
                </span>
                <ChevronRight className="w-4 h-4 text-slate-400" />
              </Link>
              <Link
                href="/app/finance/reports"
                className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 hover:bg-slate-50 transition dark:border-slate-800 dark:hover:bg-slate-800/50"
              >
                <span className="font-medium text-slate-800 dark:text-slate-200">
                  9. Intelligence Reports
                </span>
                <ChevronRight className="w-4 h-4 text-slate-400" />
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Live Financial Timeline */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:bg-slate-900 dark:border-slate-800">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
          Live Real-time Financial Activity Stream
        </h2>
        <div className="space-y-3">
          {summary?.recentActivities && summary.recentActivities.length > 0 ? (
            summary.recentActivities.map((act) => (
              <div
                key={act.id}
                className="flex items-center justify-between text-xs p-3 rounded-lg bg-slate-50 border border-slate-100 dark:bg-slate-800/50 dark:border-slate-700"
              >
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-emerald-500" />
                  <div>
                    <span className="font-semibold text-slate-900 dark:text-white">
                      {act.title}
                    </span>
                    <span className="text-slate-500 ml-2">
                      {act.description}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  {act.amount !== undefined && (
                    <span className="font-bold text-slate-900 dark:text-white">
                      {formatMoney(act.amount)}
                    </span>
                  )}
                  <span className="text-slate-400">{act.timestamp}</span>
                </div>
              </div>
            ))
          ) : (
            <div className="text-xs text-slate-500">
              No recent transactions recorded.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
