"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Sparkles,
  Search,
  Filter,
  RefreshCw,
  Plus,
  Bookmark,
  CheckCircle,
  Clock,
  ArrowRight,
} from "lucide-react";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/toast";
import { aiInsightsService } from "@/services/ai-insights.service";
import {
  Insight,
  IntelligenceDomain,
  InsightPriority,
  InsightStatus,
} from "@campusos/types";
import { InsightCard } from "@/components/intelligence/insight-card";

export default function InsightsFeedPage() {
  const { toast } = useToast();
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [domainFilter, setDomainFilter] = useState("ALL");
  const [priorityFilter, setPriorityFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [search, setSearch] = useState("");

  const loadInsights = async () => {
    setLoading(true);
    try {
      const res = await aiInsightsService.listInsights({
        domain: domainFilter,
        priority: priorityFilter,
        status: statusFilter,
        search,
      });
      if (res.success && res.data) {
        setInsights(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInsights();
  }, [domainFilter, priorityFilter, statusFilter, search]);

  const handleSave = async (id: string) => {
    const res = await aiInsightsService.toggleSaveInsight(id);
    if (res.success && res.data) {
      setInsights((prev) =>
        prev.map((i) =>
          i.id === id ? { ...i, isSaved: res.data!.isSaved } : i,
        ),
      );
      toast({
        title: res.data.isSaved ? "Insight Saved" : "Insight Unsaved",
        variant: "neutral",
      });
    }
  };

  const handleDismiss = async (id: string) => {
    const res = await aiInsightsService.dismissInsight(id);
    if (res.success && res.data) {
      setInsights((prev) =>
        prev.map((i) =>
          i.id === id ? { ...i, status: InsightStatus.DISMISSED } : i,
        ),
      );
      toast({ title: "Insight Dismissed", variant: "neutral" });
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Breadcrumbs
            items={[
              { label: "Dashboard", href: "/app/dashboard" },
              { label: "Intelligence", href: "/app/intelligence" },
              { label: "Insights" },
            ]}
          />
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">
            Intelligence Insights
          </h1>
          <p className="text-sm text-slate-500">
            Automated institutional observations and prioritized operational
            recommendations.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/app/intelligence/saved">
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              <Bookmark className="w-3.5 h-3.5 text-blue-600" />
              Saved Insights
            </Button>
          </Link>
          <Link href="/app/intelligence/assistant">
            <Button
              size="sm"
              className="gap-1.5 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white"
            >
              <Sparkles className="w-3.5 h-3.5" />
              Ask AI Assistant
            </Button>
          </Link>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="relative flex-1 min-w-[240px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search insights by title, summary, or recommendation..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-lg border border-slate-200 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Domain Filter */}
            <select
              value={domainFilter}
              onChange={(e) => setDomainFilter(e.target.value)}
              className="bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-blue-500"
            >
              <option value="ALL">All Domains</option>
              <option value="ATTENDANCE">Attendance</option>
              <option value="FINANCE">Finance</option>
              <option value="PLACEMENT">Placement</option>
              <option value="ACADEMICS">Academics</option>
              <option value="INFRASTRUCTURE">Infrastructure</option>
              <option value="DOCUMENTS">Documents</option>
            </select>

            {/* Priority Filter */}
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-blue-500"
            >
              <option value="ALL">All Priorities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-blue-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="NEW">New</option>
              <option value="REVIEWED">Reviewed</option>
              <option value="ACTIONED">Actioned</option>
              <option value="DISMISSED">Dismissed</option>
            </select>
          </div>
        </div>
      </div>

      {/* Insights Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="h-44 rounded-xl bg-slate-100 animate-pulse"
            />
          ))
        ) : insights.length === 0 ? (
          <div className="col-span-full p-12 text-center bg-white rounded-xl border border-slate-200 text-xs text-slate-500">
            No insights match your selected filter criteria.
          </div>
        ) : (
          insights.map((insight) => (
            <InsightCard
              key={insight.id}
              insight={insight}
              onSave={handleSave}
              onDismiss={handleDismiss}
            />
          ))
        )}
      </div>
    </div>
  );
}
