"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Sparkles,
  AlertTriangle,
  AlertCircle,
  Users,
  Calendar,
  GraduationCap,
  IndianRupee,
  Briefcase,
  Building,
  FileText,
  Activity,
  ArrowRight,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Search,
  BookOpen,
  CheckCircle2,
  Clock,
  ShieldCheck,
} from "lucide-react";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { intelligenceService } from "@/services/intelligence.service";
import { aiInsightsService } from "@/services/ai-insights.service";
import { aiAlertsService } from "@/services/ai-alerts.service";
import { aiActivityService } from "@/services/ai-activity.service";
import {
  IntelligenceOverviewSummary,
  CampusHealthMetric,
  Insight,
  Alert,
  AIActivity,
  IntelligenceDomain,
} from "@campusos/types";
import { InsightCard } from "@/components/intelligence/insight-card";
import { AlertCard } from "@/components/intelligence/alert-card";
import { DomainBadge } from "@/components/intelligence/intelligence-badge";

export default function IntelligenceOverviewPage() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const [summary, setSummary] = useState<IntelligenceOverviewSummary | null>(
    null,
  );
  const [healthMetrics, setHealthMetrics] = useState<CampusHealthMetric[]>([]);
  const [recentInsights, setRecentInsights] = useState<Insight[]>([]);
  const [recentAlerts, setRecentAlerts] = useState<Alert[]>([]);
  const [recentActivities, setRecentActivities] = useState<AIActivity[]>([]);

  const loadData = async (isManual = false) => {
    try {
      if (isManual) setRefreshing(true);
      else setLoading(true);

      const [sumRes, healthRes, insRes, altRes, actRes] = await Promise.all([
        intelligenceService.getOverviewSummary(),
        intelligenceService.getCampusHealthMetrics(),
        aiInsightsService.listInsights(),
        aiAlertsService.listAlerts(),
        aiActivityService.listAIActivity(),
      ]);

      if (sumRes.success && sumRes.data) setSummary(sumRes.data);
      if (healthRes.success && healthRes.data) setHealthMetrics(healthRes.data);
      if (insRes.success && insRes.data)
        setRecentInsights(insRes.data.slice(0, 4));
      if (altRes.success && altRes.data)
        setRecentAlerts(altRes.data.slice(0, 4));
      if (actRes.success && actRes.data)
        setRecentActivities(actRes.data.slice(0, 5));

      if (isManual) {
        toast({
          title: "Intelligence Telemetry Refreshed",
          description:
            "All cross-module signals, health indices, and alerts synchronized.",
          variant: "success",
        });
      }
    } catch {
      toast({
        title: "Telemetry Update Warning",
        description: "Operating with resilient local cache.",
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

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header & Breadcrumbs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Breadcrumbs
            items={[
              { label: "Dashboard", href: "/app/dashboard" },
              { label: "Intelligence", href: "/app/intelligence" },
              { label: "Overview" },
            ]}
          />
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">
            CampusOS Intelligence
          </h1>
          <p className="text-sm text-slate-500">
            Unified executive operational telemetry, early-warning risk radar,
            and cross-domain insights.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => loadData(true)}
            disabled={refreshing}
            className="gap-1.5 text-xs"
          >
            <RefreshCw
              className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`}
            />
            Refresh Signals
          </Button>

          <Link href="/app/intelligence/assistant">
            <Button
              size="sm"
              className="gap-1.5 font-semibold text-xs shadow-sm bg-blue-600 hover:bg-blue-700 text-white"
            >
              <Sparkles className="w-3.5 h-3.5" />
              Launch AI Assistant
            </Button>
          </Link>
        </div>
      </div>

      {/* Intelligence KPIs (8 required KPIs) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
        {loading || !summary ? (
          Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full rounded-xl" />
          ))
        ) : (
          <>
            <StatCard
              title="Active Insights"
              value={summary.activeInsights}
              subtitle="Operational recommendations"
              variant="indigo"
              icon={<Sparkles className="w-4 h-4" />}
            />
            <StatCard
              title="Critical Alerts"
              value={summary.criticalAlerts}
              subtitle="Action required immediately"
              variant="amber"
              icon={<AlertCircle className="w-4 h-4" />}
            />
            <StatCard
              title="Attention Needed"
              value={summary.studentsRequiringAttention}
              subtitle="Students in risk cohort"
              variant="amber"
              icon={<Users className="w-4 h-4" />}
            />
            <StatCard
              title="Attendance Risk"
              value={summary.attendanceRiskCases}
              subtitle="Below 75% threshold"
              variant="amber"
              icon={<Calendar className="w-4 h-4" />}
            />
            <StatCard
              title="Academic Risk"
              value={summary.academicRiskCases}
              subtitle="Backlogs & marginal GPA"
              variant="sky"
              icon={<GraduationCap className="w-4 h-4" />}
            />
            <StatCard
              title="Finance Risk"
              value={summary.financeRiskCases}
              subtitle="Overdue fee invoices"
              variant="emerald"
              icon={<IndianRupee className="w-4 h-4" />}
            />
            <StatCard
              title="Placement Drives"
              value={summary.placementOpportunities}
              subtitle="Active corporate funnels"
              variant="purple"
              icon={<Briefcase className="w-4 h-4" />}
            />
            <StatCard
              title="Infrastructure Issues"
              value={summary.infrastructureIssues}
              subtitle="Open facility tickets"
              variant="default"
              icon={<Building className="w-4 h-4" />}
            />
          </>
        )}
      </div>

      {/* AI Assistant Quick Launcher Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 p-6 text-white shadow-md relative overflow-hidden">
        <div className="relative z-10 max-w-2xl space-y-2">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-blue-500/20 text-blue-300 text-xs font-semibold border border-blue-400/30">
            <Sparkles className="w-3.5 h-3.5" />
            Natural-Language Campus Intelligence
          </div>
          <h2 className="text-xl font-bold tracking-tight">
            What do you want to understand about your campus?
          </h2>
          <p className="text-xs text-blue-200/90 leading-relaxed">
            Ask complex queries across student attendance, academic progression,
            fee collections, corporate placements, and digital records with full
            explainability.
          </p>
          <div className="pt-2 flex flex-wrap items-center gap-2">
            <Link href="/app/intelligence/assistant">
              <Button
                size="sm"
                className="bg-white hover:bg-slate-100 text-blue-900 font-semibold text-xs gap-1.5"
              >
                Open Assistant Console <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            </Link>
            <Link href="/app/intelligence/analytics">
              <Button
                size="sm"
                variant="outline"
                className="text-white border-white/30 hover:bg-white/10 text-xs"
              >
                Cross-Domain Analytics
              </Button>
            </Link>
          </div>
        </div>
        <div className="absolute right-0 top-0 bottom-0 w-96 opacity-10 bg-gradient-to-l from-white to-transparent pointer-events-none" />
      </div>

      {/* Domain Intelligence Grid (Section 4 - All 8 canonical domains) */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-base font-semibold text-slate-900">
              Domain Operational Health
            </h2>
            <p className="text-xs text-slate-500">
              Autonomous health scoring and alert summaries across campus
              subsystems
            </p>
          </div>
          <Link href="/app/intelligence/analytics">
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-blue-600 gap-1"
            >
              Explore Analytics <ArrowRight className="w-3 h-3" />
            </Button>
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {loading || !summary?.domainSummaries
            ? Array.from({ length: 8 }).map((_, i) => (
                <Skeleton key={i} className="h-32 w-full rounded-xl" />
              ))
            : Object.entries(summary.domainSummaries).map(([domain, data]) => (
                <div
                  key={domain}
                  className="p-4 rounded-xl border border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold text-xs text-slate-900">
                        {domain}
                      </span>
                      <Badge
                        variant={
                          data.status === "EXCELLENT"
                            ? "success"
                            : data.status === "GOOD"
                              ? "info"
                              : "warning"
                        }
                        className="text-[10px]"
                      >
                        {data.healthScore}/100 • {data.status}
                      </Badge>
                    </div>
                    <p className="text-xs font-medium text-slate-700 mb-1">
                      {data.primaryMetric}
                    </p>
                    <p className="text-[11px] text-slate-500 line-clamp-2">
                      {data.summary}
                    </p>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-slate-100 mt-2 text-[11px]">
                    <span className="text-slate-500">
                      {data.activeAlerts > 0 ? (
                        <span className="text-amber-700 font-medium">
                          {data.activeAlerts} active alert
                        </span>
                      ) : (
                        <span className="text-emerald-700 font-medium">
                          No alerts
                        </span>
                      )}
                    </span>
                    <Link
                      href={`/app/intelligence/analytics?domain=${domain.toUpperCase()}`}
                      className="text-blue-600 hover:text-blue-800 font-medium flex items-center gap-0.5"
                    >
                      View <ArrowRight className="w-3 h-3" />
                    </Link>
                  </div>
                </div>
              ))}
        </div>
      </div>

      {/* Dual Column: Active Insights & Critical Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Insights */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-slate-900 flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-blue-600" />
                Active Insights & Recommendations
              </h2>
              <p className="text-xs text-slate-500">
                Actionable operational suggestions based on cross-module
                correlations
              </p>
            </div>
            <Link href="/app/intelligence/insights">
              <Button
                variant="ghost"
                size="sm"
                className="text-xs text-blue-600 gap-1"
              >
                View All <ArrowRight className="w-3 h-3" />
              </Button>
            </Link>
          </div>

          <div className="space-y-3">
            {loading ? (
              Array.from({ length: 2 }).map((_, i) => (
                <Skeleton key={i} className="h-40 w-full rounded-xl" />
              ))
            ) : recentInsights.length === 0 ? (
              <div className="p-8 text-center bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-500">
                No active insights detected. All campus metrics normal.
              </div>
            ) : (
              recentInsights.map((insight) => (
                <InsightCard key={insight.id} insight={insight} />
              ))
            )}
          </div>
        </div>

        {/* Operational Alerts */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-slate-900 flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                Operational Early-Warning Alerts
              </h2>
              <p className="text-xs text-slate-500">
                Threshold breaches and immediate institutional SLA tasks
              </p>
            </div>
            <Link href="/app/intelligence/alerts">
              <Button
                variant="ghost"
                size="sm"
                className="text-xs text-blue-600 gap-1"
              >
                Alert Center <ArrowRight className="w-3 h-3" />
              </Button>
            </Link>
          </div>

          <div className="space-y-3">
            {loading ? (
              Array.from({ length: 2 }).map((_, i) => (
                <Skeleton key={i} className="h-40 w-full rounded-xl" />
              ))
            ) : recentAlerts.length === 0 ? (
              <div className="p-8 text-center bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-500">
                No active operational alerts.
              </div>
            ) : (
              recentAlerts.map((alert) => (
                <AlertCard key={alert.id} alert={alert} />
              ))
            )}
          </div>
        </div>
      </div>

      {/* Intelligence Activity Audit Feed (Section 4) */}
      <Card>
        <CardHeader className="py-3 px-4 border-b border-slate-100 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-sm font-semibold text-slate-900 flex items-center gap-1.5">
              <Activity className="w-4 h-4 text-slate-500" />
              Recent Intelligence Audit & Query Activity
            </CardTitle>
            <p className="text-xs text-slate-500">
              Live operational ledger of AI tool invocations and user queries
            </p>
          </div>
          <Link href="/app/intelligence/activity">
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-blue-600 gap-1"
            >
              Full Activity Log <ArrowRight className="w-3 h-3" />
            </Button>
          </Link>
        </CardHeader>
        <CardContent className="p-0">
          <div className="divide-y divide-slate-100">
            {loading ? (
              <div className="p-4 space-y-2">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
              </div>
            ) : recentActivities.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-500">
                No recent activity recorded.
              </div>
            ) : (
              recentActivities.map((act) => (
                <div
                  key={act.id}
                  className="p-3 sm:px-4 flex items-center justify-between text-xs hover:bg-slate-50 transition-colors"
                >
                  <div className="space-y-0.5 pr-2">
                    <p className="font-semibold text-slate-800 line-clamp-1">
                      {act.query}
                    </p>
                    <div className="flex flex-wrap items-center gap-2 text-slate-500 text-[11px]">
                      <span>
                        {act.userName} ({act.userRole})
                      </span>
                      <span>•</span>
                      <span className="font-mono text-slate-600">
                        {act.toolsInvoked.join(", ")}
                      </span>
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <Badge variant="neutral" className="text-[10px]">
                      {act.durationMs}ms
                    </Badge>
                    <p className="text-[10px] text-slate-400 mt-0.5">
                      {new Date(act.timestamp).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
