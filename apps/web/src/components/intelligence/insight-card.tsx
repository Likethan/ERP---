"use client";

import React from "react";
import Link from "next/link";
import { Insight } from "@campusos/types";
import {
  PriorityBadge,
  InsightStatusBadge,
  DomainBadge,
} from "./intelligence-badge";
import {
  Sparkles,
  ArrowRight,
  Bookmark,
  BookmarkCheck,
  CheckCircle,
  Eye,
  XCircle,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface InsightCardProps {
  insight: Insight;
  onSave?: (id: string) => void;
  onDismiss?: (id: string) => void;
  onAction?: (id: string) => void;
}

export function InsightCard({
  insight,
  onSave,
  onDismiss,
  onAction,
}: InsightCardProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 hover:border-slate-300 hover:shadow-sm transition-all flex flex-col justify-between group">
      <div>
        <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
          <div className="flex items-center gap-2">
            <DomainBadge domain={insight.domain} />
            <PriorityBadge priority={insight.priority} />
          </div>
          <div className="flex items-center gap-1.5">
            <InsightStatusBadge status={insight.status} />
            {onSave && (
              <button
                type="button"
                onClick={() => onSave(insight.id)}
                className="p-1 rounded text-slate-400 hover:text-blue-600 transition-colors"
                title={insight.isSaved ? "Saved" : "Save Insight"}
              >
                {insight.isSaved ? (
                  <BookmarkCheck className="w-4 h-4 text-blue-600" />
                ) : (
                  <Bookmark className="w-4 h-4" />
                )}
              </button>
            )}
          </div>
        </div>

        <Link href={`/app/intelligence/insights/${insight.id}`}>
          <h3 className="text-sm font-semibold text-slate-900 group-hover:text-blue-600 transition-colors line-clamp-1 mb-1">
            {insight.title}
          </h3>
        </Link>
        <p className="text-xs text-slate-600 line-clamp-2 mb-3">{insight.summary}</p>

        {/* Affected & Metrics */}
        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 mb-3">
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-50 border border-slate-200 font-medium">
            <Users className="w-3 h-3 text-slate-400" />
            Affected: {insight.affectedRecordCount} records
          </span>
          {insight.evidence && insight.evidence[0] && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-blue-50 text-blue-800 border border-blue-200 font-medium truncate max-w-full">
              {insight.evidence[0].metric}: {insight.evidence[0].value}
            </span>
          )}
        </div>

        {/* Recommendation Snippet */}
        <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/80 text-xs text-slate-700 mb-3">
          <span className="font-semibold text-slate-900 block mb-0.5">Recommended:</span>
          <p className="line-clamp-2 text-slate-600">{insight.recommendedAction}</p>
        </div>
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-slate-100 mt-2">
        <Link href={`/app/intelligence/insights/${insight.id}`}>
          <Button variant="ghost" size="sm" className="text-xs gap-1 text-slate-600 hover:text-slate-900 px-2">
            <Eye className="w-3.5 h-3.5" /> View Details
          </Button>
        </Link>

        <div className="flex items-center gap-1">
          {onDismiss && insight.status !== "DISMISSED" && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onDismiss(insight.id)}
              className="text-xs text-slate-500 hover:text-slate-800 px-2"
            >
              Dismiss
            </Button>
          )}

          {insight.recommendedActionHref && (
            <Link href={insight.recommendedActionHref}>
              <Button size="sm" variant="outline" className="text-xs gap-1 px-2.5">
                Take Action <ArrowRight className="w-3 h-3" />
              </Button>
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
