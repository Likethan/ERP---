"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Sparkles,
  BarChart3,
  TrendingUp,
  Filter,
  Download,
  Calendar,
  Layers,
  Search,
  RefreshCw,
  Table as TableIcon,
  PieChart as PieIcon,
  ArrowRight,
} from "lucide-react";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/toast";
import { aiAnalyticsService } from "@/services/ai-analytics.service";
import {
  AnalyticsQuery,
  AnalyticsResult,
  IntelligenceDomain,
} from "@campusos/types";

export default function AnalyticsConsolePage() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);

  // Analytics Builder States
  const [domain, setDomain] = useState<IntelligenceDomain>(IntelligenceDomain.ATTENDANCE);
  const [metric, setMetric] = useState("Average Attendance");
  const [dimension, setDimension] = useState("Department");
  const [timeRange, setTimeRange] = useState("Current Semester");

  // Global filters
  const [deptFilter, setDeptFilter] = useState("ALL");
  const [analyticsResult, setAnalyticsResult] = useState<AnalyticsResult | null>(null);

  const runQuery = async () => {
    setLoading(true);
    try {
      const res = await aiAnalyticsService.runAnalyticsQuery({
        domain,
        metric,
        dimension,
        timeRange,
        filters: deptFilter !== "ALL" ? { department: deptFilter } : undefined,
      });

      if (res.success && res.data) {
        setAnalyticsResult(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runQuery();
  }, [domain]);

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Breadcrumbs
            items={[
              { label: "Dashboard", href: "/app/dashboard" },
              { label: "Intelligence", href: "/app/intelligence" },
              { label: "Analytics" },
            ]}
          />
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">
            Cross-Domain Campus Analytics
          </h1>
          <p className="text-sm text-slate-500">
            Multidimensional analytics builder and comparative performance telemetry.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              toast({
                title: "Report Export Dispatched",
                description: "Generating CSV spreadsheet export of current telemetry.",
                variant: "success",
              });
            }}
            className="gap-1.5 text-xs"
          >
            <Download className="w-3.5 h-3.5" />
            Export Dataset
          </Button>

          <Link href="/app/intelligence/assistant">
            <Button size="sm" className="gap-1.5 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white">
              <Sparkles className="w-3.5 h-3.5" />
              Ask AI Assistant
            </Button>
          </Link>
        </div>
      </div>

      {/* Analytics Builder Surface (Section 22) */}
      <Card className="border-blue-200/80 bg-slate-50/50 shadow-sm">
        <CardHeader className="py-3 px-4 border-b border-slate-200/80 flex flex-row items-center justify-between">
          <CardTitle className="text-sm font-semibold text-slate-900 flex items-center gap-1.5">
            <BarChart3 className="w-4 h-4 text-blue-600" />
            Analytics Builder
          </CardTitle>
          <Badge variant="info" className="text-[10px]">Interactive Configurator</Badge>
        </CardHeader>
        <CardContent className="p-4 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {/* Domain */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-600">Subsystem Domain</label>
              <select
                value={domain}
                onChange={(e) => setDomain(e.target.value as IntelligenceDomain)}
                className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-800 focus:outline-none focus:border-blue-500"
              >
                <option value={IntelligenceDomain.ATTENDANCE}>Attendance Telemetry</option>
                <option value={IntelligenceDomain.FINANCE}>Finance & Revenues</option>
                <option value={IntelligenceDomain.PLACEMENT}>Corporate Placements</option>
                <option value={IntelligenceDomain.INFRASTRUCTURE}>Infrastructure & Assets</option>
                <option value={IntelligenceDomain.ALL}>Cross-Campus Overview</option>
              </select>
            </div>

            {/* Metric */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-600">Metric</label>
              <select
                value={metric}
                onChange={(e) => setMetric(e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-800 focus:outline-none focus:border-blue-500"
              >
                {domain === IntelligenceDomain.ATTENDANCE && (
                  <>
                    <option value="Average Attendance">Average Attendance (%)</option>
                    <option value="Risk Cohort (<75%)">Students Below 75% Threshold</option>
                  </>
                )}
                {domain === IntelligenceDomain.FINANCE && (
                  <>
                    <option value="Billed vs Realized">Billed vs Realized Collections</option>
                    <option value="Aging Receivables">Overdue Aging Buckets</option>
                  </>
                )}
                {domain === IntelligenceDomain.PLACEMENT && (
                  <>
                    <option value="Offers Released">Offers Released per Drive</option>
                    <option value="CTC Distribution">Average Package (CTC)</option>
                  </>
                )}
                {domain === IntelligenceDomain.INFRASTRUCTURE && (
                  <>
                    <option value="Occupancy Rate">Hostel Bed Utilization</option>
                    <option value="Complaint Resolution SLA">Resolution Time (Hours)</option>
                  </>
                )}
                {domain === IntelligenceDomain.ALL && (
                  <option value="Composite Health">Overall Subsystem Health Index</option>
                )}
              </select>
            </div>

            {/* Dimension */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-600">Dimension / Grouping</label>
              <select
                value={dimension}
                onChange={(e) => setDimension(e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-800 focus:outline-none focus:border-blue-500"
              >
                <option value="Department">By Department</option>
                <option value="Academic Year">By Academic Cohort / Year</option>
                <option value="Semester">By Semester Section</option>
              </select>
            </div>

            {/* Time Range */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-600">Time Range</label>
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-800 focus:outline-none focus:border-blue-500"
              >
                <option value="Current Semester">Current Semester (2026-27)</option>
                <option value="Past 30 Days">Past 30 Days</option>
                <option value="Full Academic Year">Full Academic Year 2026-27</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-200">
            <Button
              size="sm"
              onClick={runQuery}
              disabled={loading}
              className="gap-1.5 font-semibold text-xs bg-blue-600 hover:bg-blue-700 text-white"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              Run Analytics Query
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Analytics Results Surface */}
      {loading ? (
        <div className="space-y-4">
          <div className="h-64 rounded-xl bg-slate-100 animate-pulse" />
          <div className="h-48 rounded-xl bg-slate-100 animate-pulse" />
        </div>
      ) : analyticsResult ? (
        <div className="space-y-6">
          {/* Visual Chart Card */}
          <Card>
            <CardHeader className="py-3 px-4 border-b border-slate-100 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base font-bold text-slate-900">
                  {analyticsResult.title}
                </CardTitle>
                <p className="text-xs text-slate-500 mt-0.5">{analyticsResult.summary}</p>
              </div>
              <Badge variant="neutral" className="text-xs capitalize font-medium">
                {analyticsResult.chartType} View
              </Badge>
            </CardHeader>
            <CardContent className="p-6">
              {/* Responsive Bar / Metric Chart Representation */}
              <div className="space-y-4">
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
                  {analyticsResult.labels.map((label, idx) => {
                    const primaryDataset = analyticsResult.datasets[0];
                    const val = primaryDataset?.data[idx] ?? 0;
                    return (
                      <div key={idx} className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 text-center">
                        <span className="text-[11px] font-semibold text-slate-500 block truncate">
                          {label}
                        </span>
                        <p className="text-base font-bold text-slate-900 mt-1">{val}</p>
                        <div className="w-full bg-slate-200 h-1.5 rounded-full mt-2 overflow-hidden">
                          <div
                            className="bg-blue-600 h-full rounded-full transition-all"
                            style={{
                              width: `${Math.min(100, typeof val === "number" ? val : 70)}%`,
                            }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Tabular Dataset Card */}
          {analyticsResult.tableData && (
            <Card>
              <CardHeader className="py-3 px-4 border-b border-slate-100">
                <CardTitle className="text-sm font-semibold text-slate-900 flex items-center gap-1.5">
                  <TableIcon className="w-4 h-4 text-slate-500" />
                  Granular Tabular Telemetry
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                      <tr>
                        {analyticsResult.tableData.headers.map((h, hIdx) => (
                          <th key={hIdx} className="px-4 py-2.5">
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {analyticsResult.tableData.rows.map((row, rIdx) => (
                        <tr key={rIdx} className="hover:bg-slate-50/60">
                          {row.map((cell, cIdx) => (
                            <td key={cIdx} className="px-4 py-2.5 font-medium text-slate-800">
                              {cell}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      ) : null}
    </div>
  );
}
