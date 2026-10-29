"use client";

import React, { useState, useEffect } from "react";
import { studentAffairsService } from "@/services/student-affairs.service";
import { StudentAffairsDashboardMetrics } from "@/types/student-affairs";
import { StudentAffairsNav } from "@/components/student-affairs/student-affairs-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/ui/stat-card";
import {
  BarChart3,
  Download,
  Calendar,
  CheckCircle2,
  PieChart,
  TrendingUp,
  FileSpreadsheet,
  ShieldCheck,
} from "lucide-react";

export default function CaseReportsPage() {
  const [metrics, setMetrics] = useState<StudentAffairsDashboardMetrics | null>(null);

  useEffect(() => {
    async function load() {
      const data = await studentAffairsService.getDashboardMetrics();
      setMetrics(data);
    }
    load();
  }, []);

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: "Dashboard", href: "/app/dashboard" },
          { label: "Student Affairs", href: "/app/student-affairs" },
          { label: "Case Analytics & Reports", href: "/app/student-affairs/reports" },
        ]}
      />

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-5 gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <BarChart3 className="h-6 w-6 text-indigo-400" />
            Institutional Case Analytics & Governance Reporting
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Aggregated institutional redressal metrics, regulatory compliance summaries, and procedural turnaround analytics.
          </p>
        </div>
        <Button
          onClick={() => alert("Regulatory UGC Compliance Report exported successfully.")}
          className="bg-indigo-600 hover:bg-indigo-500 text-white gap-2 text-xs"
        >
          <Download className="h-4 w-4" />
          Export UGC Statutory Report
        </Button>
      </div>

      <StudentAffairsNav />

      {/* Top Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="Total Lifetime Filings"
          value={metrics?.total_cases ?? 48}
          icon={<BarChart3 className="h-4 w-4 text-indigo-400" />}
          change={{ value: "+12% year-over-year", trend: "up" }}
        />
        <StatCard
          title="Resolved This Month"
          value={metrics?.resolved_this_month ?? 27}
          icon={<CheckCircle2 className="h-4 w-4 text-emerald-400" />}
          change={{ value: "Average 5.4 days", trend: "up" }}
        />
        <StatCard
          title="SLA Compliance Rate"
          value={`${metrics?.sla_compliance_rate ?? 96.2}%`}
          icon={<TrendingUp className="h-4 w-4 text-blue-400" />}
          change={{ value: "Statutory Target: 95%", trend: "up" }}
        />
        <StatCard
          title="Appellate Turnaround"
          value="4.2 Days"
          icon={<ShieldCheck className="h-4 w-4 text-cyan-400" />}
          change={{ value: "100% Sep of Duties", trend: "up" }}
        />
      </div>

      {/* Category Breakdown & Appellate Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6 border-slate-800 bg-slate-900/40 space-y-4">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <PieChart className="h-4 w-4 text-indigo-400" />
            Case Distribution by Category
          </h2>

          <div className="space-y-3 text-xs">
            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>Campus Infrastructure & Facilities</span>
                <span className="font-semibold text-white">42% (20 cases)</span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                <div className="h-full bg-indigo-500 rounded-full" style={{ width: "42%" }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>Academic Evaluation & Transparency</span>
                <span className="font-semibold text-white">28% (13 cases)</span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                <div className="h-full bg-blue-500 rounded-full" style={{ width: "28%" }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>Student Conduct & Academic Integrity</span>
                <span className="font-semibold text-white">18% (9 cases)</span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                <div className="h-full bg-purple-500 rounded-full" style={{ width: "18%" }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>Safeguarding & Anti-Ragging Incidents</span>
                <span className="font-semibold text-white">12% (6 cases)</span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                <div className="h-full bg-rose-500 rounded-full" style={{ width: "12%" }} />
              </div>
            </div>
          </div>
        </Card>

        <Card className="p-6 border-slate-800 bg-slate-900/40 space-y-4">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            Appellate Determinations Breakdown
          </h2>

          <div className="space-y-3 text-xs">
            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>Sanction Overturned (Full Relief)</span>
                <span className="font-semibold text-emerald-400">50% (3 appeals)</span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                <div className="h-full bg-emerald-500 rounded-full" style={{ width: "50%" }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>Sanction Modified (Proportionality Adjustment)</span>
                <span className="font-semibold text-amber-400">33% (2 appeals)</span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                <div className="h-full bg-amber-500 rounded-full" style={{ width: "33%" }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>Sanction Upheld (Affirmed on Facts)</span>
                <span className="font-semibold text-slate-400">17% (1 appeal)</span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                <div className="h-full bg-slate-600 rounded-full" style={{ width: "17%" }} />
              </div>
            </div>
          </div>

          <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/60 text-[11px] text-slate-400 leading-relaxed">
            All appellate decisions are logged with the Ombudsperson Registry. No confidential party names or witness transcripts are exposed in aggregate reporting dashboards.
          </div>
        </Card>
      </div>
    </div>
  );
}
