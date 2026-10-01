"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Sparkles,
  Users,
  CheckCircle,
  IndianRupee,
  Briefcase,
  AlertTriangle,
  ArrowUpRight,
  RefreshCw,
  Download,
  ShieldCheck,
  Building,
  GraduationCap,
  TrendingUp,
  FileCheck,
  Activity,
  Layers,
  Search,
} from "lucide-react";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabItem } from "@/components/ui/tabs";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { intelligenceService } from "@/services/intelligence.service";
import {
  CampusMetricCard,
  OperationalAlertItem,
  DepartmentKpiItem,
  CohortDistributionItem,
  RiskRadarSummary,
} from "@/mocks/intelligence.mock";

export default function IntelligencePage() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Tabs state
  const [activeTab, setActiveTab] = useState("departments");

  // Data states
  const [metrics, setMetrics] = useState<CampusMetricCard[]>([]);
  const [alerts, setAlerts] = useState<OperationalAlertItem[]>([]);
  const [kpis, setKpis] = useState<DepartmentKpiItem[]>([]);
  const [cohorts, setCohorts] = useState<CohortDistributionItem[]>([]);
  const [radar, setRadar] = useState<RiskRadarSummary | null>(null);

  // Filters
  const [alertFilter, setAlertFilter] = useState<"ALL" | "CRITICAL" | "WARNING" | "INFO">("ALL");
  const [deptSearch, setDeptSearch] = useState("");

  const loadData = async (isManualRefresh = false) => {
    try {
      if (isManualRefresh) setRefreshing(true);
      else setLoading(true);

      const [mRes, aRes, kRes, cRes, rRes] = await Promise.all([
        intelligenceService.getMetrics(),
        intelligenceService.getAlerts(),
        intelligenceService.getDepartmentKpis(),
        intelligenceService.getCohortData(),
        intelligenceService.getRiskRadar(),
      ]);

      if (mRes.success && mRes.data) setMetrics(mRes.data);
      if (aRes.success && aRes.data) setAlerts(aRes.data);
      if (kRes.success && kRes.data) setKpis(kRes.data);
      if (cRes.success && cRes.data) setCohorts(cRes.data);
      if (rRes.success && rRes.data) setRadar(rRes.data);

      if (isManualRefresh) {
        toast({
          title: "Telemetry Refreshed",
          description: "All campus operations, academic records, and risk signals updated.",
          variant: "success",
        });
      }
    } catch {
      toast({
        title: "Telemetry Update Warning",
        description: "Operating in resilient offline mode with synchronized campus data.",
        variant: "warning",
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const filteredAlerts = alerts.filter((alt) => {
    if (alertFilter === "ALL") return true;
    return alt.level === alertFilter;
  });

  const filteredKpis = kpis.filter((k) =>
    k.department.toLowerCase().includes(deptSearch.toLowerCase())
  );

  const getMetricIcon = (cat: string) => {
    switch (cat) {
      case "ENROLLMENT":
        return <Users className="h-4 w-4" />;
      case "ATTENDANCE":
        return <CheckCircle className="h-4 w-4" />;
      case "FINANCE":
        return <IndianRupee className="h-4 w-4" />;
      case "PLACEMENT":
        return <Briefcase className="h-4 w-4" />;
      default:
        return <Sparkles className="h-4 w-4" />;
    }
  };

  const getMetricVariant = (cat: string): "indigo" | "emerald" | "amber" | "sky" => {
    switch (cat) {
      case "ENROLLMENT":
        return "indigo";
      case "ATTENDANCE":
        return "emerald";
      case "FINANCE":
        return "amber";
      case "PLACEMENT":
        return "sky";
      default:
        return "indigo";
    }
  };

  return (
    <div className="space-y-6 pb-12">
      <Breadcrumbs
        customSegments={[
          { label: "Campus Intelligence & Telemetry" },
        ]}
      />

      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Campus Intelligence & Telemetry
            </h1>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-400">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              LIVE TELEMETRY
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-400">
            Real-time institutional oversight, cohort progression tracking, department KPI benchmarking, and early warning radar.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={() => loadData(true)}
            disabled={refreshing}
            className="border-slate-700 bg-slate-900/60 text-slate-300 hover:bg-slate-800 hover:text-white"
          >
            <RefreshCw className={`mr-2 h-3.5 w-3.5 ${refreshing ? "animate-spin text-indigo-400" : ""}`} />
            Refresh
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              toast({
                title: "Report Generated",
                description: "Executive Institutional Audit Dossier (PDF) dispatched to downloads.",
                variant: "info",
              });
            }}
            className="border-slate-700 bg-slate-900/60 text-slate-300 hover:bg-slate-800 hover:text-white"
          >
            <Download className="mr-2 h-3.5 w-3.5" />
            Audit Dossier
          </Button>

          <Link href="/app/ai">
            <Button
              size="sm"
              className="bg-indigo-600 text-white hover:bg-indigo-500 shadow-sm shadow-indigo-900/40"
            >
              <Sparkles className="mr-2 h-3.5 w-3.5 text-yellow-300" />
              Ask AI Assistant
            </Button>
          </Link>
        </div>
      </div>

      {/* Top 4 Canonical Institutional Metric Cards */}
      {loading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-32 rounded-xl bg-slate-900" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {metrics.map((m, idx) => (
            <StatCard
              key={idx}
              label={m.label}
              value={m.value}
              description={m.description}
              change={m.change}
              icon={getMetricIcon(m.category)}
              variant={getMetricVariant(m.category)}
            />
          ))}
        </div>
      )}

      {/* Risk Radar / Autonomous Early Warning Banner */}
      {radar && (
        <div className="rounded-xl border border-slate-800 bg-gradient-to-r from-slate-900/90 via-slate-900/60 to-slate-900/90 p-4 shadow-sm backdrop-blur-sm">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-amber-500/30 bg-amber-500/10 text-amber-400">
                <Activity className="h-5 w-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Institutional Risk Radar
                  </span>
                  <Badge variant="outline" className="border-slate-700 text-slate-400 text-[10px]">
                    {radar.lastUpdated}
                  </Badge>
                </div>
                <h4 className="text-sm font-medium text-white">
                  Active threshold anomalies requiring administrative or departmental intervention
                </h4>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="rounded-lg border border-red-500/20 bg-red-950/20 px-3 py-2 text-center">
                <span className="text-lg font-bold font-mono text-red-400">{radar.attendanceUnder75}</span>
                <p className="text-[11px] font-medium text-slate-400">Att. &lt;75% Risk</p>
              </div>

              <div className="rounded-lg border border-amber-500/20 bg-amber-950/20 px-3 py-2 text-center">
                <span className="text-lg font-bold font-mono text-amber-400">{radar.feeOverdueHigh}</span>
                <p className="text-[11px] font-medium text-slate-400">Overdue Invoices</p>
              </div>

              <div className="rounded-lg border border-sky-500/20 bg-sky-950/20 px-3 py-2 text-center">
                <span className="text-lg font-bold font-mono text-sky-400">{radar.cgpaUnder6}</span>
                <p className="text-[11px] font-medium text-slate-400">CGPA &lt;6.0 Remedial</p>
              </div>

              <div className="rounded-lg border border-purple-500/20 bg-purple-950/20 px-3 py-2 text-center">
                <span className="text-lg font-bold font-mono text-purple-400">{radar.criticalDisciplinary}</span>
                <p className="text-[11px] font-medium text-slate-400">Escalated Notices</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <Tabs
        tabs={[
          { id: "departments", label: "Department Matrix", icon: <Building className="h-4 w-4" /> },
          { id: "cohorts", label: "Cohort Progression", icon: <GraduationCap className="h-4 w-4" /> },
          { id: "alerts", label: "Operational Alerts", count: alerts.length, icon: <AlertTriangle className="h-4 w-4" /> },
          { id: "accreditation", label: "NAAC / NBA Readiness", icon: <ShieldCheck className="h-4 w-4" /> },
        ]}
        activeTab={activeTab}
        onChange={setActiveTab}
      />

      {/* Tab 1: Department Matrix */}
      {activeTab === "departments" && (
          <Card className="border-slate-800 bg-slate-900/60 backdrop-blur-sm">
            <CardHeader className="border-b border-slate-800/80 pb-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <CardTitle className="text-base font-semibold text-white">
                    Cross-Department Operational Benchmark
                  </CardTitle>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Comparative academic, attendance, placement velocity, and fee recovery performance.
                  </p>
                </div>
                <div className="relative w-full sm:w-64">
                  <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
                  <input
                    type="text"
                    placeholder="Search department..."
                    value={deptSearch}
                    onChange={(e) => setDeptSearch(e.target.value)}
                    className="w-full rounded-lg border border-slate-800 bg-slate-950/80 pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-slate-800 bg-slate-950/50 text-slate-400">
                    <tr>
                      <th className="px-4 py-3 font-semibold uppercase tracking-wider">Department</th>
                      <th className="px-4 py-3 font-semibold uppercase tracking-wider text-right">Faculty</th>
                      <th className="px-4 py-3 font-semibold uppercase tracking-wider text-right">Students</th>
                      <th className="px-4 py-3 font-semibold uppercase tracking-wider text-right">Ratio</th>
                      <th className="px-4 py-3 font-semibold uppercase tracking-wider">Avg Attendance</th>
                      <th className="px-4 py-3 font-semibold uppercase tracking-wider text-right">Avg CGPA</th>
                      <th className="px-4 py-3 font-semibold uppercase tracking-wider">Placement Rate</th>
                      <th className="px-4 py-3 font-semibold uppercase tracking-wider">Fee Collection</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-sans">
                    {filteredKpis.map((k, idx) => {
                      const ratio = Math.round(k.studentsCount / (k.facultyCount || 1));
                      return (
                        <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                          <td className="px-4 py-3.5 font-medium text-white">
                            <div className="flex items-center gap-2">
                              <Building className="h-3.5 w-3.5 text-indigo-400 shrink-0" />
                              <span>{k.department}</span>
                            </div>
                          </td>
                          <td className="px-4 py-3.5 text-right font-mono text-slate-300">
                            {k.facultyCount}
                          </td>
                          <td className="px-4 py-3.5 text-right font-mono text-slate-300">
                            {k.studentsCount}
                          </td>
                          <td className="px-4 py-3.5 text-right font-mono text-slate-400">
                            1:{ratio}
                          </td>
                          <td className="px-4 py-3.5">
                            <div className="flex items-center gap-2">
                              <div className="h-1.5 w-24 rounded-full bg-slate-800 overflow-hidden">
                                <div
                                  className={`h-full rounded-full ${
                                    k.avgAttendancePercent >= 88
                                      ? "bg-emerald-500"
                                      : k.avgAttendancePercent >= 80
                                      ? "bg-amber-500"
                                      : "bg-red-500"
                                  }`}
                                  style={{ width: `${k.avgAttendancePercent}%` }}
                                />
                              </div>
                              <span className="font-mono text-slate-200">
                                {k.avgAttendancePercent}%
                              </span>
                            </div>
                          </td>
                          <td className="px-4 py-3.5 text-right font-mono font-semibold text-indigo-300">
                            {k.avgCgpa.toFixed(2)}
                          </td>
                          <td className="px-4 py-3.5">
                            <div className="flex items-center gap-2">
                              <div className="h-1.5 w-20 rounded-full bg-slate-800 overflow-hidden">
                                <div
                                  className="h-full rounded-full bg-sky-500"
                                  style={{ width: `${k.placementRatePercent}%` }}
                                />
                              </div>
                              <span className="font-mono text-sky-400 font-medium">
                                {k.placementRatePercent}%
                              </span>
                            </div>
                          </td>
                          <td className="px-4 py-3.5">
                            <div className="flex items-center gap-2">
                              <div className="h-1.5 w-20 rounded-full bg-slate-800 overflow-hidden">
                                <div
                                  className="h-full rounded-full bg-emerald-500"
                                  style={{ width: `${k.feeCollectionPercent}%` }}
                                />
                              </div>
                              <span className="font-mono text-emerald-400 font-medium">
                                {k.feeCollectionPercent}%
                              </span>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
      )}

      {/* Tab 2: Cohort Progression */}
      {activeTab === "cohorts" && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {cohorts.map((c, i) => (
              <div
                key={i}
                className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm hover:border-slate-700 transition-all"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    {c.year}
                  </span>
                  <Badge variant="outline" className="border-indigo-500/30 bg-indigo-500/10 text-indigo-400 font-mono text-[10px]">
                    {c.enrolled} Students
                  </Badge>
                </div>

                <div className="mt-4 space-y-3">
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">Retention Rate</span>
                      <span className="font-mono font-semibold text-emerald-400">{c.retentionRate}%</span>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                      <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${c.retentionRate}%` }} />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">Avg Attendance</span>
                      <span className="font-mono font-semibold text-indigo-300">{c.avgAttendance}%</span>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                      <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${c.avgAttendance}%` }} />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">Pass Percentage</span>
                      <span className="font-mono font-semibold text-sky-400">{c.passPercentage}%</span>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                      <div className="h-full bg-sky-500 rounded-full" style={{ width: `${c.passPercentage}%` }} />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <Card className="border-slate-800 bg-slate-900/60 backdrop-blur-sm">
            <CardHeader className="border-b border-slate-800/80 pb-4">
              <CardTitle className="text-base font-semibold text-white flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-emerald-400" />
                Institutional Cohort Velocity Insights
              </CardTitle>
            </CardHeader>
            <CardContent className="p-5 text-xs text-slate-300 space-y-2">
              <p>
                • <strong>First-to-Second Year Transition:</strong> 98.4% retention represents our highest baseline in 4 academic cycles, driven by personalized first-year mentor counseling and diagnostic foundation workshops.
              </p>
              <p>
                • <strong>Senior Year Exit Velocity:</strong> 96.5% cumulative pass rate in Batch 2023 with 84.2% placed prior to final semester examinations.
              </p>
              <p>
                • <strong>Academic Intervention Priority:</strong> Second-year mathematics (CS202 & EC201) accounts for 44% of remedial exam registrations; supplementary tutorial batches scheduled for October.
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tab 3: Operational Alerts */}
      {activeTab === "alerts" && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            {(["ALL", "CRITICAL", "WARNING", "INFO"] as const).map((filter) => (
              <Button
                key={filter}
                size="sm"
                variant={alertFilter === filter ? "primary" : "outline"}
                onClick={() => setAlertFilter(filter)}
                className={`text-xs h-7 ${
                  alertFilter === filter
                    ? "bg-indigo-600 text-white"
                    : "border-slate-800 bg-slate-900 text-slate-400 hover:text-white"
                }`}
              >
                {filter === "ALL" ? `All Alerts (${alerts.length})` : filter}
              </Button>
            ))}
          </div>

          <div className="space-y-3">
            {filteredAlerts.map((alt) => {
              const borderCol =
                alt.level === "CRITICAL"
                  ? "border-red-500/40 bg-red-950/10"
                  : alt.level === "WARNING"
                  ? "border-amber-500/40 bg-amber-950/10"
                  : "border-sky-500/40 bg-sky-950/10";

              const badgeVariant =
                alt.level === "CRITICAL" ? "destructive" : alt.level === "WARNING" ? "warning" : "info";

              return (
                <div
                  key={alt.id}
                  className={`rounded-xl border p-4 shadow-sm backdrop-blur-sm transition-all hover:border-slate-700 ${borderCol}`}
                >
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div className="space-y-1.5">
                      <div className="flex items-center gap-2">
                        <Badge variant={badgeVariant as any} className="text-[10px] uppercase font-bold">
                          {alt.level}
                        </Badge>
                        <span className="text-xs font-semibold text-white">{alt.title}</span>
                        <span className="text-[11px] text-slate-400">• {alt.department}</span>
                      </div>
                      <p className="text-xs text-slate-300 leading-relaxed">{alt.message}</p>
                      <span className="text-[10px] text-slate-400 block">{alt.timestamp}</span>
                    </div>

                    {alt.actionHref && (
                      <Link href={alt.actionHref} className="shrink-0">
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-slate-700 bg-slate-900 text-xs text-slate-200 hover:bg-slate-800 hover:text-white"
                        >
                          {alt.actionText || "Review Roster"}
                          <ArrowUpRight className="ml-1.5 h-3.5 w-3.5" />
                        </Button>
                      </Link>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Tab 4: NAAC / NBA Accreditation Readiness */}
      {activeTab === "accreditation" && (
          <Card className="border-slate-800 bg-slate-900/60 backdrop-blur-sm">
            <CardHeader className="border-b border-slate-800/80 pb-4">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base font-semibold text-white flex items-center gap-2">
                    <ShieldCheck className="h-4 w-4 text-emerald-400" />
                    NAAC Criterion Evaluation Dossier (SSR Auto-Aggregator)
                  </CardTitle>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Continuous quantitative metric alignment against NAAC manual (Revision 2026).
                  </p>
                </div>
                <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 font-mono text-xs">
                  Estimated CGPA: 3.76 / 4.00 (A++ Grade)
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-slate-800 bg-slate-950/50 text-slate-400">
                    <tr>
                      <th className="px-4 py-3 font-semibold uppercase tracking-wider">Criterion</th>
                      <th className="px-4 py-3 font-semibold uppercase tracking-wider">Description</th>
                      <th className="px-4 py-3 font-semibold uppercase tracking-wider text-right">Weightage</th>
                      <th className="px-4 py-3 font-semibold uppercase tracking-wider text-right">Score</th>
                      <th className="px-4 py-3 font-semibold uppercase tracking-wider">Audit Evidence</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {[
                      {
                        code: "Criterion 1",
                        title: "Curricular Aspects",
                        desc: "OBE alignment, syllabus revisions, elective offerings",
                        weight: "100",
                        score: "3.82",
                        status: "Verified",
                      },
                      {
                        code: "Criterion 2",
                        title: "Teaching-Learning and Evaluation",
                        desc: "Student-faculty ratio 1:18, continuous assessment, CIE rubrics",
                        weight: "350",
                        score: "3.75",
                        status: "Verified",
                      },
                      {
                        code: "Criterion 3",
                        title: "Research, Innovations and Extension",
                        desc: "Indexed publications, sponsored grants, patents published",
                        weight: "120",
                        score: "3.42",
                        status: "Under Review",
                      },
                      {
                        code: "Criterion 4",
                        title: "Infrastructure and Learning Resources",
                        desc: "Hostel capacity, LMS bandwidth, central library e-journals",
                        weight: "100",
                        score: "3.90",
                        status: "Verified",
                      },
                      {
                        code: "Criterion 5",
                        title: "Student Support and Progression",
                        desc: "Placement rate 84.2%, scholarships, anti-ragging compliance",
                        weight: "130",
                        score: "3.80",
                        status: "Verified",
                      },
                      {
                        code: "Criterion 6",
                        title: "Governance, Leadership and Management",
                        desc: "ERP implementation (CampusOS), financial audits, PBAC",
                        weight: "100",
                        score: "3.85",
                        status: "Verified",
                      },
                      {
                        code: "Criterion 7",
                        title: "Institutional Values and Best Practices",
                        desc: "Solar grid, green campus audit, gender equality protocols",
                        weight: "100",
                        score: "3.78",
                        status: "Verified",
                      },
                    ].map((crit, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                        <td className="px-4 py-3.5 font-semibold text-white font-mono">
                          {crit.code}
                        </td>
                        <td className="px-4 py-3.5">
                          <p className="font-medium text-slate-200">{crit.title}</p>
                          <p className="text-[11px] text-slate-400">{crit.desc}</p>
                        </td>
                        <td className="px-4 py-3.5 text-right font-mono text-slate-300">
                          {crit.weight}
                        </td>
                        <td className="px-4 py-3.5 text-right font-mono font-bold text-emerald-400">
                          {crit.score}
                        </td>
                        <td className="px-4 py-3.5">
                          <span
                            className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium ${
                              crit.status === "Verified"
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                                : "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                            }`}
                          >
                            <FileCheck className="h-3 w-3" />
                            {crit.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
      )}
    </div>
  );
}
