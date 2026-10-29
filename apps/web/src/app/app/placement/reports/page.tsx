"use client";

import React, { useEffect, useState, useMemo } from "react";
import {
  FileText,
  Download,
  Building2,
  Users,
  DollarSign,
  TrendingUp,
  Award,
  Filter,
  RefreshCw,
  Search,
  CheckCircle2,
  Layers,
  PieChart,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { placementService } from "@/services/placement.service";
import { PlacementReportFilter } from "@/types/placement";

export default function PlacementReportsPage() {
  const { showToast } = useToast();
  const [reportType, setReportType] = useState<
    "SUMMARY" | "DEPARTMENT" | "COMPANY" | "PACKAGES" | "STATUS"
  >("SUMMARY");
  const [department, setDepartment] = useState("ALL");
  const [graduationYear, setGraduationYear] = useState(2026);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);

  const [reportData, setReportData] = useState<{
    title: string;
    generatedAt: string;
    totalRecords: number;
    rows: Record<string, unknown>[];
  } | null>(null);

  const loadReport = async () => {
    try {
      setLoading(true);
      const filter: PlacementReportFilter = {
        reportType,
        department: department === "ALL" ? undefined : department,
        graduationYear,
      };

      const res = await placementService.generatePlacementReport(filter);
      if (res.success && res.data) {
        setReportData(res.data);
      }
    } catch {
      showToast({
        title: "Report Generation Error",
        message: "Failed to generate requested placement report",
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReport();
  }, [reportType, department, graduationYear]);

  // Client search within generated rows
  const filteredRows = useMemo(() => {
    if (!reportData || !reportData.rows) return [];
    if (!searchQuery.trim()) return reportData.rows;
    const q = searchQuery.toLowerCase();
    return reportData.rows.filter((row) =>
      Object.values(row).some((val) => String(val).toLowerCase().includes(q)),
    );
  }, [reportData, searchQuery]);

  // Dynamic columns based on row keys
  const tableHeaders = useMemo(() => {
    if (!reportData || reportData.rows.length === 0) return [];
    return Object.keys(reportData.rows[0]);
  }, [reportData]);

  // Export RFC 4180 CSV
  const handleExportCSV = () => {
    if (!reportData || reportData.rows.length === 0) {
      showToast({
        title: "No Data",
        message: "No report rows available to export",
        type: "warning",
      });
      return;
    }

    const headers = Object.keys(reportData.rows[0]);
    const csvRows = [
      headers.join(","),
      ...reportData.rows.map((row) =>
        headers
          .map((h) => {
            const val =
              row[h] !== undefined && row[h] !== null ? String(row[h]) : "";
            return `"${val.replace(/"/g, '""')}"`;
          })
          .join(","),
      ),
    ];

    const blob = new Blob([csvRows.join("\n")], {
      type: "text/csv;charset=utf-8;",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute(
      "download",
      `CampusOS_Placement_${reportType}_Report_${new Date().toISOString().split("T")[0]}.csv`,
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    showToast({
      title: "Export Succeeded",
      message: `${reportData.title} exported to CSV`,
      type: "success",
    });
  };

  return (
    <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Placement Intelligence & Reporting
            </h1>
            <Badge variant="outline" className="text-xs font-mono">
              Phase I
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">
            Operational and executive audit reports for institutional
            stakeholders, recruiters, and statutory compliance.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadReport}
            disabled={loading}
            className="gap-1.5 text-xs h-9"
          >
            <RefreshCw
              className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
          <Button
            onClick={handleExportCSV}
            className="gap-2 bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm text-xs h-9"
          >
            <Download className="w-4 h-4" />
            Export Report (CSV)
          </Button>
        </div>
      </div>

      {/* Report Navigation Tabs */}
      <div className="flex flex-wrap gap-2 border-b pb-3">
        {[
          { id: "SUMMARY", label: "Cohort Summary", icon: Users },
          { id: "DEPARTMENT", label: "Department Audit", icon: Layers },
          { id: "COMPANY", label: "Corporate Partners", icon: Building2 },
          { id: "PACKAGES", label: "Salary Distribution", icon: DollarSign },
          { id: "STATUS", label: "Placement Outcomes", icon: CheckCircle2 },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = reportType === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() =>
                setReportType(
                  tab.id as
                    | "SUMMARY"
                    | "DEPARTMENT"
                    | "COMPANY"
                    | "PACKAGES"
                    | "STATUS",
                )
              }
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "bg-card border text-muted-foreground hover:text-foreground hover:bg-muted/50"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Filter Toolbar */}
      <div className="bg-card border rounded-xl p-4 shadow-sm flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search within report dataset..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 h-9 text-xs"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Filter className="w-3.5 h-3.5" />
            <span>Filters:</span>
          </div>

          <Select
            value={department}
            onChange={(e) => setDepartment(e.target.value)}
            className="w-44 h-9 text-xs"
            options={[
              { value: "ALL", label: "All Departments" },
              {
                value: "Computer Science and Engineering",
                label: "Computer Science",
              },
              {
                value: "Electronics & Communication Engineering",
                label: "Electronics",
              },
              { value: "Mechanical Engineering", label: "Mechanical" },
              { value: "Information Technology", label: "Information Tech" },
            ]}
          />

          <Select
            value={graduationYear.toString()}
            onChange={(e) => setGraduationYear(parseInt(e.target.value))}
            className="w-32 h-9 text-xs"
            options={[
              { value: "2026", label: "Batch 2026" },
              { value: "2027", label: "Batch 2027" },
            ]}
          />
        </div>
      </div>

      {/* Report Container */}
      <div className="bg-card border rounded-xl shadow-sm overflow-hidden space-y-4">
        <div className="p-4 border-b flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 bg-muted/20">
          <div>
            <h2 className="text-base font-bold text-foreground">
              {reportData?.title || "Placement Report"}
            </h2>
            <p className="text-xs text-muted-foreground">
              Generated on{" "}
              {reportData?.generatedAt
                ? new Date(reportData.generatedAt).toLocaleString()
                : ""}{" "}
              • Showing {filteredRows.length} of {reportData?.totalRecords || 0}{" "}
              records
            </p>
          </div>
          <Badge variant="outline" className="text-xs">
            Batch of {graduationYear}
          </Badge>
        </div>

        {loading ? (
          <div className="p-12 flex flex-col items-center justify-center gap-3">
            <div className="w-7 h-7 border-3 border-primary border-t-transparent rounded-full animate-spin" />
            <p className="text-xs text-muted-foreground">
              Compiling placement analytics...
            </p>
          </div>
        ) : filteredRows.length === 0 ? (
          <div className="p-12 text-center space-y-2">
            <FileText className="w-10 h-10 text-muted-foreground mx-auto" />
            <p className="text-sm font-medium text-foreground">
              No records found
            </p>
            <p className="text-xs text-muted-foreground">
              No data matches your search query or filter selection.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-muted/40 border-b">
                <tr>
                  {tableHeaders.map((header) => (
                    <th
                      key={header}
                      className="px-4 py-3 font-semibold text-muted-foreground uppercase tracking-wider text-[11px]"
                    >
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredRows.map((row, idx) => (
                  <tr key={idx} className="hover:bg-muted/30 transition-colors">
                    {tableHeaders.map((header) => {
                      const val = String(row[header] ?? "");
                      const isStatus =
                        header.toLowerCase().includes("status") ||
                        header.toLowerCase().includes("tier");
                      const isCtc =
                        header.toLowerCase().includes("ctc") ||
                        header.toLowerCase().includes("package");

                      return (
                        <td
                          key={header}
                          className="px-4 py-3 whitespace-nowrap text-foreground"
                        >
                          {isStatus ? (
                            <Badge
                              variant="outline"
                              className={`text-[11px] ${
                                val === "PLACED" ||
                                val === "TIER_1" ||
                                val === "ACTIVE"
                                  ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/20"
                                  : val === "IN_PROCESS" || val === "RELEASED"
                                    ? "bg-blue-500/10 text-blue-600 border-blue-500/20"
                                    : val === "NOT_PLACED" || val === "DECLINED"
                                      ? "bg-amber-500/10 text-amber-600 border-amber-500/20"
                                      : ""
                              }`}
                            >
                              {val}
                            </Badge>
                          ) : isCtc ? (
                            <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                              {val}
                            </span>
                          ) : (
                            val
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
  );
}
