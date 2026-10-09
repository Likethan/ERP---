"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Bookmark,
  BookmarkCheck,
  Search,
  Filter,
  Trash2,
  ExternalLink,
  Sparkles,
  Calendar,
  Layers,
  ArrowRight,
  Clock,
  User,
} from "lucide-react";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { useToast } from "@/components/ui/toast";
import { aiSavedService } from "@/services/ai-saved.service";
import { SavedInsight, IntelligenceDomain } from "@campusos/types";
import { DomainBadge } from "@/components/intelligence/intelligence-badge";

export default function SavedInsightsPage() {
  const { toast } = useToast();
  const [savedItems, setSavedItems] = useState<SavedInsight[]>([]);
  const [loading, setLoading] = useState(true);

  const [domainFilter, setDomainFilter] = useState("ALL");
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [search, setSearch] = useState("");

  const loadSaved = async () => {
    setLoading(true);
    try {
      const res = await aiSavedService.listSavedInsights({
        domain: domainFilter,
        type: typeFilter,
        search,
      });
      if (res.success && res.data) {
        setSavedItems(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSaved();
  }, [domainFilter, typeFilter, search]);

  const handleRemove = async (id: string) => {
    const res = await aiSavedService.removeSavedInsight(id);
    if (res.success) {
      setSavedItems((prev) => prev.filter((s) => s.id !== id));
      toast({
        title: "Saved Item Removed",
        description: "Removed from your saved portfolio.",
        variant: "neutral",
      });
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
              { label: "Saved Insights" },
            ]}
          />
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">
            Saved Insights & Responses
          </h1>
          <p className="text-sm text-slate-500">
            Bookmarked AI responses, strategic operational insights, and customized analytics views.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/app/intelligence/assistant">
            <Button size="sm" className="gap-1.5 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white">
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
              placeholder="Search saved items by title or content..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-lg border border-slate-200 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-blue-500"
            >
              <option value="ALL">All Types</option>
              <option value="AI_RESPONSE">AI Response</option>
              <option value="INSIGHT">Insight</option>
              <option value="ANALYTICS_VIEW">Analytics View</option>
              <option value="REPORT">Report</option>
            </select>

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
            </select>
          </div>
        </div>
      </div>

      {/* Saved Items List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-40 rounded-xl bg-slate-100 animate-pulse" />
          ))
        ) : savedItems.length === 0 ? (
          <div className="col-span-full p-12 text-center bg-white rounded-xl border border-slate-200 text-xs text-slate-500 space-y-3">
            <Bookmark className="w-8 h-8 text-slate-300 mx-auto" />
            <p>No saved insights or responses found.</p>
            <Link href="/app/intelligence/insights">
              <Button size="sm" variant="outline" className="text-xs">
                Browse Insights
              </Button>
            </Link>
          </div>
        ) : (
          savedItems.map((item) => (
            <div
              key={item.id}
              className="p-4 rounded-xl border border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-1.5">
                    <DomainBadge domain={item.domain} />
                    <Badge variant="neutral" className="text-[10px] font-mono">
                      {item.type.replace("_", " ")}
                    </Badge>
                  </div>
                  <button
                    onClick={() => handleRemove(item.id)}
                    className="p-1 rounded text-slate-400 hover:text-rose-600 transition-colors"
                    title="Remove from Saved"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>

                <Link href={item.href}>
                  <h3 className="text-sm font-semibold text-slate-900 hover:text-blue-600 transition-colors line-clamp-1 mb-1">
                    {item.title}
                  </h3>
                </Link>
                <p className="text-xs text-slate-600 line-clamp-2 mb-3">
                  {item.contentSnippet}
                </p>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-[11px] text-slate-400 mt-2">
                <span>Saved on {new Date(item.savedAt).toLocaleDateString([], { month: "short", day: "numeric" })}</span>
                <Link href={item.href}>
                  <Button variant="ghost" size="sm" className="text-xs text-blue-600 gap-1 p-0 h-auto hover:bg-transparent">
                    Open <ArrowRight className="w-3 h-3" />
                  </Button>
                </Link>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
