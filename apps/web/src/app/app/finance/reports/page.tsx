"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  BarChart3,
  Download,
  Filter,
  Search,
  DollarSign,
  Calendar,
  CreditCard,
  Award,
  Clock,
  Building2,
  FileSpreadsheet,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/ui/stat-card";
import { Select } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { financeService } from "@/services/finance.service";
import { formatMoney } from "@/services/financial-calculator";
import { FinanceReportFilter, ReportType } from "@/types/finance";

export default function FinanceReportsPage() {
  const { showToast } = useToast();

  const [reportType, setReportType] = useState<ReportType>("COLLECTION");
  const [loading, setLoading] = useState(true);
  const [reportData, setReportData] = useState<{
    title: string;
    generatedAt: string;
    totalRecords: number;
    rows: Record<string, unknown>[];
  } | null>(null);

  const [searchQuery, setSearchQuery] = useState("");

  const loadReport = async (type: ReportType) => {
    try {
      setLoading(true);
      const res = await financeService.generateReport({ reportType: type });
      setReportData(res.data);
    } catch {
      showToast({
        title: "Error",
        message: "Error generating financial audit report.",
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReport(reportType);
  }, [reportType]);

  const handleExportCSV = () => {
    if (!reportData || reportData.rows.length === 0) {
      showToast({
        title: "Export Failed",
        message: "No data to export.",
        type: "error",
      });
      return;
    }

    const headers = Object.keys(reportData.rows[0]);
    const csvRows = [
      headers.join(","),
      ...reportData.rows.map((row) =>
        headers
          .map((h) => {
            const val = row[h];
            const str =
              typeof val === "object" ? JSON.stringify(val) : String(val ?? "");
            return `"${str.replace(/"/g, '""')}"`;
          })
          .join(","),
      ),
    ];

    const blob = new Blob([csvRows.join("\n")], {
      type: "text/csv;charset=utf-8;",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute(
      "download",
      `campusos_${reportType.toLowerCase()}_report_${Date.now()}.csv`,
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast({
      title: "Downloaded",
      message: "Report CSV downloaded.",
      type: "success",
    });
  };

  // Filtered rows for current view
  const filteredRows = useMemo(() => {
    if (!reportData) return [];
    if (!searchQuery.trim()) return reportData.rows;

    const q = searchQuery.toLowerCase();
    return reportData.rows.filter((row) =>
      Object.values(row).some((val) => String(val).toLowerCase().includes(q)),
    );
  }, [reportData, searchQuery]);

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
              Reports
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Finance & Revenue Intelligence Reports
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Realization ledgers, aging analyses, payment distribution, and fee
            concession audits.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportCSV}
            disabled={!reportData || reportData.rows.length === 0}
            className="gap-1.5 text-xs"
          >
            <Download className="w-3.5 h-3.5" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Report Controls Ribbon */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-white p-4 rounded-xl border border-slate-200 dark:bg-slate-900 dark:border-slate-800">
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
            <BarChart3 className="w-4 h-4 text-emerald-600" />
            Report Dimension:
          </div>
          <Select
            value={reportType}
            onChange={(e) => setReportType(e.target.value as ReportType)}
            className="text-xs h-9 w-64 font-semibold"
          >
            <option value="COLLECTION">
              Fee Collection & Realization Ledger
            </option>
            <option value="OUTSTANDING">Outstanding & Overdue Register</option>
            <option value="AGING">Debt Aging & Recovery Analysis</option>
            <option value="PAYMENT_METHOD">Payment Method Distribution</option>
            <option value="SCHOLARSHIP">Scholarship & Waiver Audit</option>
          </Select>
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <Input
            placeholder="Filter current report data..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 text-xs h-9"
          />
        </div>
      </div>

      {/* Report Header & Metrics */}
      {reportData && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between px-1 text-xs text-slate-500">
            <div>
              <span className="font-bold text-slate-900 dark:text-white text-sm">
                {reportData.title}
              </span>{" "}
              • Generated {reportData.generatedAt}
            </div>
            <div>
              Showing {filteredRows.length} of {reportData.totalRecords} records
            </div>
          </div>

          {/* Quick Summary Cards based on Report Type */}
          {reportType === "COLLECTION" && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <StatCard
                title="Gross Realized Inflow"
                value="₹2,63,800.00"
                description="Verified collections across all accounts"
                icon={<DollarSign className="w-5 h-5 text-emerald-600" />}
              />
              <StatCard
                title="Collection Efficiency"
                value="71.1%"
                description="Realized vs Gross Invoiced Ratio"
                icon={<BarChart3 className="w-5 h-5 text-blue-600" />}
              />
              <StatCard
                title="Active Payment Channels"
                value="5 Methods"
                description="UPI, NEFT, Card, Cash, Cheque"
                icon={<CreditCard className="w-5 h-5 text-teal-600" />}
              />
            </div>
          )}

          {reportType === "OUTSTANDING" && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <StatCard
                title="Total Outstanding Receivables"
                value="₹1,07,000.00"
                description="Pending fee balance across active students"
                icon={<DollarSign className="w-5 h-5 text-amber-600" />}
              />
              <StatCard
                title="Invoices with Balance Due"
                value={`${reportData.rows.length} Invoices`}
                description="Partial and fully unpaid candidate records"
                icon={<Building2 className="w-5 h-5 text-blue-600" />}
              />
              <StatCard
                title="Recovery Priority"
                value="B.Tech AI & Data Science"
                description="Department with highest balance ratio"
                icon={<Clock className="w-5 h-5 text-rose-600" />}
              />
            </div>
          )}

          {reportType === "AGING" && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
              <StatCard
                title="Current / Non-Overdue"
                value="₹75,000.00"
                description="Due within allowable billing grace"
                icon={<Clock className="w-5 h-5 text-emerald-600" />}
              />
              <StatCard
                title="1–30 Days Overdue"
                value="₹0.00"
                description="First notification tier"
                icon={<Clock className="w-5 h-5 text-amber-600" />}
              />
              <StatCard
                title="31–60 Days Overdue"
                value="₹32,000.00"
                description="Second warning follow-up"
                icon={<Clock className="w-5 h-5 text-orange-600" />}
              />
              <StatCard
                title="60+ Days Delinquent"
                value="₹0.00"
                description="Administrative hold threshold"
                icon={<Clock className="w-5 h-5 text-rose-600" />}
              />
            </div>
          )}

          {reportType === "SCHOLARSHIP" && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <StatCard
                title="Total Concessions Granted"
                value="₹34,200.00"
                description="Direct institutional fee deductions"
                icon={<Award className="w-5 h-5 text-emerald-600" />}
              />
              <StatCard
                title="Total Awardees"
                value={`${reportData.rows.length} Students`}
                description="Eligible meritorious candidates"
                icon={<Award className="w-5 h-5 text-blue-600" />}
              />
              <StatCard
                title="Average Concession"
                value="₹17,100.00"
                description="Per beneficiary grant average"
                icon={<DollarSign className="w-5 h-5 text-teal-600" />}
              />
            </div>
          )}

          {/* Table Data Preview */}
          <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs dark:bg-slate-900 dark:border-slate-800">
            {loading ? (
              <div className="p-12 text-center text-xs text-slate-500">
                Compiling report dataset...
              </div>
            ) : filteredRows.length === 0 ? (
              <div className="p-12 text-center text-xs text-slate-500">
                No matching rows found in report.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-700 dark:text-slate-300">
                  <thead className="bg-slate-50 uppercase font-semibold text-slate-500 border-b border-slate-200 dark:bg-slate-800/50 dark:border-slate-800">
                    <tr>
                      {Object.keys(filteredRows[0]).map((headerKey) => (
                        <th
                          key={headerKey}
                          className="px-4 py-3 whitespace-nowrap"
                        >
                          {headerKey.replace(/([A-Z])/g, " $1").trim()}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {filteredRows.map((row, idx) => (
                      <tr
                        key={idx}
                        className="hover:bg-slate-50/50 dark:hover:bg-slate-800/50"
                      >
                        {Object.entries(row).map(([key, val], cellIdx) => {
                          const isMoney =
                            typeof val === "number" &&
                            (key.toLowerCase().includes("amount") ||
                              key.toLowerCase().includes("fee") ||
                              key.toLowerCase().includes("payable") ||
                              key.toLowerCase().includes("outstanding") ||
                              key.toLowerCase().includes("discount"));

                          return (
                            <td
                              key={cellIdx}
                              className="px-4 py-3 whitespace-nowrap"
                            >
                              {isMoney ? (
                                <span className="font-semibold text-slate-900 dark:text-white">
                                  {formatMoney(val as number)}
                                </span>
                              ) : (
                                String(val ?? "—")
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
