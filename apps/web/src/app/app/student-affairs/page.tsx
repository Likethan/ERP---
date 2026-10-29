"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { studentAffairsService } from "@/services/student-affairs.service";
import { StudentAffairsCalculator } from "@/services/student-affairs-calculator";
import {
  GrievanceCaseModel,
  StudentAffairsDashboardMetrics,
} from "@/types/student-affairs";
import { StudentAffairsNav } from "@/components/student-affairs/student-affairs-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  ShieldAlert,
  FileEdit,
  Inbox,
  Gavel,
  Scale,
  AlertTriangle,
  Clock,
  Calendar,
  CheckCircle2,
  ChevronRight,
  ShieldCheck,
  Search,
} from "lucide-react";

export default function StudentAffairsDashboardPage() {
  const [metrics, setMetrics] = useState<StudentAffairsDashboardMetrics | null>(null);
  const [recentCases, setRecentCases] = useState<GrievanceCaseModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(false);
    const m = await studentAffairsService.getDashboardMetrics();
    const cases = await studentAffairsService.getCases();
    setMetrics(m);
    setRecentCases(cases);
  }

  const filteredCases = recentCases.filter((c) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      c.case_number.toLowerCase().includes(q) ||
      c.title.toLowerCase().includes(q) ||
      c.category?.name.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: "Dashboard", href: "/app/dashboard" },
          { label: "Student Affairs & Grievances", href: "/app/student-affairs" },
        ]}
      />

      {/* Header Banner */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Student Affairs & Case Governance
            </h1>
            <Badge className="bg-indigo-500/10 text-indigo-400 border-indigo-500/20">
              UGC / Institutional Fairness
            </Badge>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Confidential student grievance redressal, formal disciplinary proceedings, hearing panels & appellate review.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <Link href="/app/student-affairs/submit">
            <Button className="bg-indigo-600 hover:bg-indigo-500 text-white gap-2 text-xs font-semibold shadow-lg shadow-indigo-600/20">
              <FileEdit className="h-4 w-4" />
              Submit Grievance
            </Button>
          </Link>
          <Link href="/app/student-affairs/intake">
            <Button variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800 gap-2 text-xs">
              <Inbox className="h-4 w-4 text-indigo-400" />
              Intake Queue
            </Button>
          </Link>
        </div>
      </div>

      <StudentAffairsNav />

      {/* Metric Cards Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        <StatCard
          title="Active Grievances"
          value={metrics?.active_grievances ?? 0}
          icon={<FileEdit className="h-4 w-4 text-indigo-400" />}
          change={{ value: "+2 this week", trend: "neutral" }}
        />
        <StatCard
          title="Disciplinary Inquiries"
          value={metrics?.active_disciplinary ?? 0}
          icon={<Gavel className="h-4 w-4 text-purple-400" />}
          change={{ value: "3 in hearings", trend: "neutral" }}
        />
        <StatCard
          title="Pending Triage"
          value={metrics?.pending_intake ?? 0}
          icon={<Inbox className="h-4 w-4 text-amber-400" />}
          change={{ value: "SLA < 24h", trend: "up" }}
        />
        <StatCard
          title="Hearings Scheduled"
          value={metrics?.hearings_scheduled ?? 0}
          icon={<Calendar className="h-4 w-4 text-blue-400" />}
          change={{ value: "This week", trend: "neutral" }}
        />
        <StatCard
          title="Pending Appeals"
          value={metrics?.appeals_pending ?? 0}
          icon={<Scale className="h-4 w-4 text-cyan-400" />}
          change={{ value: "Sep of Duties", trend: "neutral" }}
        />
        <StatCard
          title="Urgent Escalations"
          value={metrics?.urgent_escalations ?? 0}
          icon={<AlertTriangle className="h-4 w-4 text-rose-400" />}
          change={{ value: "Safeguarding", trend: metrics?.urgent_escalations ? "down" : "up" }}
        />
        <StatCard
          title="SLA Compliance"
          value={`${metrics?.sla_compliance_rate ?? 95}%`}
          icon={<CheckCircle2 className="h-4 w-4 text-emerald-400" />}
          change={{ value: "Target: 95%", trend: "up" }}
        />
      </div>

      {/* Urgent Safeguarding Alert Banner */}
      {metrics && metrics.urgent_escalations > 0 && (
        <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-950/20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-rose-500/20 text-rose-400">
              <AlertTriangle className="h-5 w-5 animate-pulse" />
            </div>
            <div>
              <p className="text-sm font-semibold text-rose-200">
                1 Case Under Urgent Safeguarding Escalation
              </p>
              <p className="text-xs text-rose-300/70">
                Protected report flagged for priority review by Dean & Internal Complaints Committee.
              </p>
            </div>
          </div>
          <Link href="/app/student-affairs/escalations">
            <Button size="sm" className="bg-rose-600 hover:bg-rose-500 text-white text-xs">
              View Escalation Queue
            </Button>
          </Link>
        </div>
      )}

      {/* Main Grid: Active Cases & Procedural Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Recent Cases Table (2 cols) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-indigo-400" />
              Institutional Case Roster
            </h2>
            <div className="relative w-full sm:w-64">
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search case number or subject..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <Card className="border-slate-800 bg-slate-900/50 backdrop-blur overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400">
                    <th className="py-3 px-4 font-medium">Case Reference</th>
                    <th className="py-3 px-4 font-medium">Type & Category</th>
                    <th className="py-3 px-4 font-medium">Status & SLA</th>
                    <th className="py-3 px-4 font-medium">Priority</th>
                    <th className="py-3 px-4 font-medium">Confidentiality</th>
                    <th className="py-3 px-4 font-medium text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredCases.map((c) => {
                    const sla = StudentAffairsCalculator.calculateSlaStatus(
                      c.target_response_date,
                      c.status
                    );
                    const statusBadge = StudentAffairsCalculator.getStatusBadge(c.status);
                    const priorityBadge = StudentAffairsCalculator.getPriorityBadge(c.priority);

                    return (
                      <tr key={c.id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-3 px-4">
                          <div className="font-semibold text-indigo-300">
                            {c.case_number}
                          </div>
                          <div className="text-[11px] text-slate-400 truncate max-w-[200px]">
                            {c.title}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <span className="font-medium text-slate-200">
                            {c.case_type}
                          </span>
                          <div className="text-[10px] text-slate-500 truncate max-w-[140px]">
                            {c.category?.name || "General"}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex flex-col gap-1 items-start">
                            <span className={`px-2 py-0.5 rounded text-[10px] border ${statusBadge.className}`}>
                              {statusBadge.label}
                            </span>
                            <span className={`text-[10px] font-mono ${sla.statusLabel === "BREACHED" ? "text-red-400" : "text-slate-400"}`}>
                              {sla.statusLabel === "RESOLVED"
                                ? "Completed"
                                : `${sla.hoursRemaining}h remaining`}
                            </span>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-0.5 rounded text-[10px] border ${priorityBadge.className}`}>
                            {priorityBadge.label}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <Badge variant="outline" className="border-slate-700 text-slate-300 text-[10px]">
                            {c.confidentiality_level}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <Link href={`/app/student-affairs/cases/${c.id}`}>
                            <Button size="sm" variant="ghost" className="h-7 px-2 text-indigo-400 hover:text-indigo-300 hover:bg-indigo-950/30 text-xs">
                              Details
                              <ChevronRight className="h-3 w-3 ml-1" />
                            </Button>
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Card>
        </div>

        {/* Right Column: Institutional Safeguards & Next Hearings (1 col) */}
        <div className="space-y-5">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            Institutional Governance Principles
          </h2>

          <Card className="p-4 border-slate-800 bg-slate-900/40 space-y-3">
            <div className="text-xs text-slate-300 space-y-2">
              <div className="p-2.5 rounded-lg bg-indigo-950/30 border border-indigo-500/20">
                <p className="font-semibold text-indigo-300">Presumption of Good Faith</p>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Grievance submissions and misconduct allegations are not treated as proven facts until verified through formal inquiry.
                </p>
              </div>
              <div className="p-2.5 rounded-lg bg-emerald-950/30 border border-emerald-500/20">
                <p className="font-semibold text-emerald-300">Separation of Duties</p>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Original sanctioning authorities are barred from reviewing appellate filings under UGC statutory fairness standards.
                </p>
              </div>
              <div className="p-2.5 rounded-lg bg-amber-950/30 border border-amber-500/20">
                <p className="font-semibold text-amber-300">Protected Identity</p>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Confidential submitter identities and witness statements require authorized redaction before hearing panel disclosure.
                </p>
              </div>
            </div>
          </Card>

          <Card className="p-4 border-slate-800 bg-slate-900/40">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
              <Calendar className="h-3.5 w-3.5 text-blue-400" />
              Upcoming Inquiry & Hearing Panels
            </h3>
            <div className="space-y-3">
              <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/60 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-200">Hearing: DIS-2026-0019</span>
                  <Badge className="bg-pink-500/10 text-pink-400 border-pink-500/20 text-[9px]">Panel</Badge>
                </div>
                <p className="text-slate-400 text-[11px] mt-1">Mid-Term 1 Academic Integrity Review</p>
                <div className="flex items-center gap-2 mt-2 text-[10px] text-slate-500">
                  <Clock className="h-3 w-3" />
                  <span>Oct 26, 2:30 PM • Admin Conf Room B</span>
                </div>
              </div>
              <Link href="/app/student-affairs/meetings">
                <Button variant="outline" size="sm" className="w-full text-xs border-slate-800 text-slate-300 hover:bg-slate-800 mt-2">
                  View Full Hearing Calendar
                </Button>
              </Link>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
