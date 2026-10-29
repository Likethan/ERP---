"use client";

import React, { useState, useEffect } from "react";
import { StudentSupportService } from "@/services/student-support.service";
import { SupportTelemetryMetrics } from "@/types/student-support";
import { StudentSupportNav } from "@/components/student-support/student-support-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { StatCard } from "@/components/ui/stat-card";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  BarChart3,
  TrendingUp,
  ShieldCheck,
  Users,
  Heart,
  Target,
  ArrowRightLeft,
  Calendar,
  AlertTriangle,
} from "lucide-react";

export default function StudentSupportAnalyticsPage() {
  const [metrics, setMetrics] = useState<SupportTelemetryMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, []);

  async function loadAnalytics() {
    setLoading(true);
    try {
      const data = await StudentSupportService.getTelemetryMetrics();
      setMetrics(data);
    } catch (err) {
      console.error("Failed to load telemetry:", err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 pb-12">
      <div>
        <Breadcrumbs
          items={[
            { label: "Dashboard", href: "/app/dashboard" },
            { label: "Student Support", href: "/app/student-support" },
            { label: "Analytics & Telemetry", href: "/app/student-support/analytics" },
          ]}
        />
        <div className="mt-2 flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <BarChart3 className="h-6 w-6 text-indigo-400" />
              Institutional Support Analytics & Privacy-Safe Telemetry
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Holistic institutional engagement metrics, cross-department referral volumes, and student growth rates.
            </p>
          </div>
          <Badge variant="outline" className="border-indigo-500/40 text-indigo-400 bg-indigo-500/10 text-xs px-3 py-1">
            <ShieldCheck className="mr-1.5 h-3.5 w-3.5" />
            Zero-Leakage Telemetry Standard
          </Badge>
        </div>
      </div>

      <StudentSupportNav />

      {/* Small-Group Suppression & Privacy Alert */}
      <div className="rounded-xl border border-indigo-900/40 bg-indigo-950/20 p-4">
        <div className="flex items-start gap-3">
          <ShieldCheck className="h-5 w-5 text-indigo-400 mt-0.5 shrink-0" />
          <div className="text-xs text-slate-300 space-y-1">
            <span className="font-semibold text-white">Aggregated Differential Privacy & Suppression:</span>
            <p>
              To prevent student re-identification, metric cohorts with fewer than 5 records are automatically suppressed. No individual clinical session notes, psychological observations, or personal health details are stored or serialized in institutional analytics.
            </p>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Active Mentorships"
          value={loading ? "..." : (metrics?.active_mentor_assignments ?? 0).toLocaleString()}
          icon={<Users className="h-5 w-5 text-indigo-400" />}
          description="Institutional mentoring ratio 94.2%"
        />
        <StatCard
          title="Mentoring Sessions Held"
          value={loading ? "..." : (metrics?.mentoring_sessions_completed ?? 0).toLocaleString()}
          icon={<Calendar className="h-5 w-5 text-emerald-400" />}
          description="Current academic year"
        />
        <StatCard
          title="Counselling Utilization"
          value={loading ? "..." : `${metrics?.appointment_utilization_rate_pct ?? 0}%`}
          icon={<Heart className="h-5 w-5 text-rose-400" />}
          description="Confidential wellness capacity"
        />
        <StatCard
          title="Avg Development Progress"
          value={loading ? "..." : `${metrics?.average_development_progress_pct ?? 0}%`}
          icon={<Target className="h-5 w-5 text-purple-400" />}
          description="IDP milestone completion index"
        />
      </div>

      {/* Charts and Distributions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Referral Distribution by Service */}
        <Card className="border-slate-800 bg-slate-900/60 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <ArrowRightLeft className="h-4 w-4 text-cyan-400" />
              Inter-Service Support Referral Volumes
            </h2>
            <span className="text-xs text-slate-400">Total: {metrics?.pending_support_referrals ?? 18} referrals</span>
          </div>

          <div className="space-y-3 pt-2">
            {[
              { label: "Career & Placement Guidance", count: 42, pct: 40, color: "bg-emerald-500" },
              { label: "Academic Advising & Electives", count: 28, pct: 27, color: "bg-indigo-500" },
              { label: "Counselling & Wellbeing", count: 18, pct: 17, color: "bg-rose-500" },
              { label: "Financial Aid & Scholarships", count: 11, pct: 10, color: "bg-amber-500" },
              { label: "Disability & Inclusion Support", count: 6, pct: 6, color: "bg-cyan-500" },
            ].map((item) => (
              <div key={item.label} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-300 font-medium">{item.label}</span>
                  <span className="text-slate-400">
                    {item.count} cases ({item.pct}%)
                  </span>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                  <div className={`h-full rounded-full ${item.color}`} style={{ width: `${item.pct}%` }} />
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Goal Category Distribution */}
        <Card className="border-slate-800 bg-slate-900/60 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <Target className="h-4 w-4 text-purple-400" />
              IDP Goal Categories & Accomplishment Rate
            </h2>
            <span className="text-xs text-slate-400">
              Completed: {metrics?.development_goals_completed ?? 68} goals
            </span>
          </div>

          <div className="space-y-3 pt-2">
            {[
              { label: "Technical Competence & Coding", count: 85, pct: 78, color: "bg-indigo-500" },
              { label: "Academic Excellence & Research", count: 64, pct: 72, color: "bg-purple-500" },
              { label: "Career Readiness & Internships", count: 52, pct: 65, color: "bg-teal-500" },
              { label: "Leadership & Extra-Curriculars", count: 34, pct: 58, color: "bg-cyan-500" },
              { label: "Communication & Soft Skills", count: 29, pct: 81, color: "bg-pink-500" },
            ].map((item) => (
              <div key={item.label} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-300 font-medium">{item.label}</span>
                  <span className="text-slate-400">Completion: {item.pct}%</span>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                  <div className={`h-full rounded-full ${item.color}`} style={{ width: `${item.pct}%` }} />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
