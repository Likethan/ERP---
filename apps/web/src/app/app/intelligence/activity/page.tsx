"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Activity,
  Wrench,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  Sparkles,
  ShieldCheck,
  Eye,
  Database,
  Calendar,
  Layers,
  User,
  ArrowRight,
} from "lucide-react";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Tabs, TabItem } from "@/components/ui/tabs";
import { aiActivityService } from "@/services/ai-activity.service";
import { aiToolsService } from "@/services/ai-tools.service";
import { AIActivity, AITool, IntelligenceDomain } from "@campusos/types";
import { DomainBadge } from "@/components/intelligence/intelligence-badge";

export default function AiActivityPage() {
  const [activeTab, setActiveTab] = useState("activity");
  const [activities, setActivities] = useState<AIActivity[]>([]);
  const [tools, setTools] = useState<AITool[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState("");
  const [domainFilter, setDomainFilter] = useState("ALL");

  // Selected Activity detail dialog
  const [selectedActivity, setSelectedActivity] = useState<AIActivity | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [actRes, toolsRes] = await Promise.all([
          aiActivityService.listAIActivity({
            domain: domainFilter,
            search,
          }),
          aiToolsService.listAITools({
            domain: domainFilter,
            search,
          }),
        ]);

        if (actRes.success && actRes.data) setActivities(actRes.data);
        if (toolsRes.success && toolsRes.data) setTools(toolsRes.data);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [domainFilter, search]);

  const tabs: TabItem[] = [
    { id: "activity", label: `Audit Log (${activities.length})` },
    { id: "tools", label: `Tool Registry (${tools.length})` },
  ];

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Breadcrumbs
            items={[
              { label: "Dashboard", href: "/app/dashboard" },
              { label: "Intelligence", href: "/app/intelligence" },
              { label: "AI Activity & Tools" },
            ]}
          />
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">
            AI Tool Registry & Audit Activity
          </h1>
          <p className="text-sm text-slate-500">
            Operational governance ledger, model tool definitions, and query execution audit trails.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/app/intelligence/assistant">
            <Button size="sm" className="gap-1.5 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white">
              <Sparkles className="w-3.5 h-3.5" />
              Open Assistant
            </Button>
          </Link>
        </div>
      </div>

      {/* Tabs */}
      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {/* Search & Domain Filter */}
      <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-3">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder={activeTab === "activity" ? "Search activity by query, user, or tool..." : "Search tools by name or description..."}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 rounded-lg border border-slate-200 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="flex items-center gap-2">
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
        </div>
      </div>

      {/* Tab 1: AI Activity Audit Log */}
      {activeTab === "activity" && (
        <Card>
          <CardHeader className="py-3 px-4 border-b border-slate-100">
            <CardTitle className="text-sm font-semibold text-slate-900 flex items-center gap-1.5">
              <Activity className="w-4 h-4 text-blue-600" />
              Intelligence Invocations & Query Execution Audit
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="px-4 py-2.5">Time</th>
                    <th className="px-4 py-2.5">User & Role</th>
                    <th className="px-4 py-2.5">Natural Language Query</th>
                    <th className="px-4 py-2.5">Domain</th>
                    <th className="px-4 py-2.5">Tool(s) Invoked</th>
                    <th className="px-4 py-2.5">Duration</th>
                    <th className="px-4 py-2.5">Status</th>
                    <th className="px-4 py-2.5 text-right">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {loading ? (
                    <tr>
                      <td colSpan={8} className="p-8 text-center text-slate-400">Loading audit records...</td>
                    </tr>
                  ) : activities.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="p-8 text-center text-slate-400">No activity matching filter.</td>
                    </tr>
                  ) : (
                    activities.map((act) => (
                      <tr key={act.id} className="hover:bg-slate-50/60">
                        <td className="px-4 py-3 text-slate-500 whitespace-nowrap">
                          {new Date(act.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </td>
                        <td className="px-4 py-3">
                          <p className="font-semibold text-slate-800">{act.userName}</p>
                          <span className="text-[10px] text-slate-400">{act.userRole}</span>
                        </td>
                        <td className="px-4 py-3 font-medium text-slate-900 max-w-xs truncate">
                          "{act.query}"
                        </td>
                        <td className="px-4 py-3">
                          <DomainBadge domain={act.domain} />
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap gap-1">
                            {act.toolsInvoked.map((t, idx) => (
                              <span
                                key={idx}
                                className="px-1.5 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-700 font-mono text-[10px]"
                              >
                                {t}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-slate-600 font-mono">
                          {act.durationMs}ms
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant="success" className="text-[10px]">
                            {act.status}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setSelectedActivity(act)}
                            className="p-1 h-7 w-7 text-slate-500 hover:text-blue-600"
                            title="Inspect Activity"
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tab 2: AI Tool Registry (Section 15 - All 14 tools) */}
      {activeTab === "tools" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {loading ? (
            Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-40 rounded-xl bg-slate-100 animate-pulse" />
            ))
          ) : tools.length === 0 ? (
            <div className="col-span-full p-12 text-center bg-white rounded-xl border border-slate-200 text-xs text-slate-500">
              No tools found matching criteria.
            </div>
          ) : (
            tools.map((tool) => (
              <div
                key={tool.name}
                className="p-4 rounded-xl border border-slate-200 bg-white hover:border-slate-300 shadow-sm transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-1.5">
                      <Wrench className="w-4 h-4 text-blue-600" />
                      <span className="font-mono font-bold text-xs text-slate-900">{tool.name}</span>
                    </div>
                    <Badge variant="success" className="text-[10px] font-medium">
                      {tool.status}
                    </Badge>
                  </div>

                  <p className="text-xs text-slate-600 mb-3">{tool.description}</p>

                  <div className="grid grid-cols-2 gap-2 p-2.5 rounded-lg bg-slate-50 border border-slate-200/80 text-[11px] mb-3">
                    <div>
                      <span className="text-slate-400 block">Domain:</span>
                      <span className="font-medium text-slate-800">{tool.domain}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Security Scope:</span>
                      <span className="font-medium text-slate-800">{tool.permissionRequirement}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-[11px] text-slate-400">
                  <span>Executions: <strong className="text-slate-700">{tool.executionCount}</strong></span>
                  <span>Last used: {tool.lastUsed}</span>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Activity Detail Dialog */}
      <Dialog
        open={Boolean(selectedActivity)}
        onOpenChange={(open) => !open && setSelectedActivity(null)}
        title="AI Query Execution Detail"
      >
        {selectedActivity && (
          <div className="space-y-4 pt-2 text-xs text-slate-700">
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                User Query
              </span>
              <p className="font-semibold text-slate-900 text-sm">"{selectedActivity.query}"</p>
              <p className="text-[11px] text-slate-500">
                Executed by {selectedActivity.userName} ({selectedActivity.userRole}) at{" "}
                {new Date(selectedActivity.timestamp).toLocaleString()}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                  Domain Scope
                </span>
                <DomainBadge domain={selectedActivity.domain} />
              </div>
              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                  Execution Latency
                </span>
                <span className="font-mono text-slate-900 font-semibold">{selectedActivity.durationMs}ms</span>
              </div>
            </div>

            <div>
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                Domain Tools Invoked
              </span>
              <div className="flex flex-wrap gap-1">
                {selectedActivity.toolsInvoked.map((t, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 rounded bg-blue-50 border border-blue-200 text-blue-800 font-mono text-[11px]"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                Connected Data Sources
              </span>
              <div className="flex flex-wrap gap-1">
                {selectedActivity.dataSources.map((ds, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-700 font-mono text-[11px]"
                  >
                    {ds}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                Synthesized Result Summary
              </span>
              <p className="p-2.5 rounded bg-slate-50 border border-slate-200 text-slate-800">
                {selectedActivity.resultSummary}
              </p>
            </div>

            <div className="flex justify-end pt-2">
              <Button size="sm" variant="outline" onClick={() => setSelectedActivity(null)}>
                Close Detail
              </Button>
            </div>
          </div>
        )}
      </Dialog>
    </div>
  );
}
