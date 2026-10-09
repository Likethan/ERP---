"use client";

import React from "react";
import Link from "next/link";
import { Alert, AlertStatus } from "@campusos/types";
import { SeverityBadge, AlertStatusBadge, DomainBadge } from "./intelligence-badge";
import { ArrowRight, CheckCircle2, Eye, ShieldAlert, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";

interface AlertCardProps {
  alert: Alert;
  onAcknowledge?: (id: string) => void;
  onResolve?: (id: string) => void;
  onDismiss?: (id: string) => void;
}

export function AlertCard({
  alert,
  onAcknowledge,
  onResolve,
  onDismiss,
}: AlertCardProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 hover:border-slate-300 hover:shadow-sm transition-all flex flex-col justify-between group">
      <div>
        <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
          <div className="flex items-center gap-2">
            <SeverityBadge severity={alert.severity} />
            <DomainBadge domain={alert.domain} />
          </div>
          <AlertStatusBadge status={alert.status} />
        </div>

        <Link href={`/app/intelligence/alerts/${alert.id}`}>
          <h3 className="text-sm font-semibold text-slate-900 group-hover:text-blue-600 transition-colors line-clamp-1 mb-1">
            {alert.title}
          </h3>
        </Link>
        <p className="text-xs text-slate-600 line-clamp-2 mb-2">{alert.reason}</p>

        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 mb-3">
          <span className="font-medium">Source: {alert.sourceDomain}</span>
          <span>•</span>
          <span className="inline-flex items-center gap-1">
            <Clock className="w-3 h-3 text-slate-400" />
            {new Date(alert.detectedAt).toLocaleDateString([], { month: "short", day: "numeric" })}
          </span>
        </div>

        <div className="p-2.5 rounded-lg bg-amber-50/50 border border-amber-200/60 text-xs text-slate-700 mb-3">
          <span className="font-semibold text-amber-900 block mb-0.5">Recommended:</span>
          <p className="line-clamp-2 text-slate-700">{alert.recommendedAction}</p>
        </div>
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-slate-100 mt-2">
        <Link href={`/app/intelligence/alerts/${alert.id}`}>
          <Button variant="ghost" size="sm" className="text-xs gap-1 text-slate-600 hover:text-slate-900 px-2">
            <Eye className="w-3.5 h-3.5" /> View Alert
          </Button>
        </Link>

        <div className="flex items-center gap-1.5">
          {alert.status === AlertStatus.OPEN && onAcknowledge && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => onAcknowledge(alert.id)}
              className="text-xs px-2.5"
            >
              Acknowledge
            </Button>
          )}

          {alert.status === AlertStatus.ACKNOWLEDGED && onResolve && (
            <Button
              size="sm"
              variant="primary"
              onClick={() => onResolve(alert.id)}
              className="text-xs gap-1 px-2.5 bg-emerald-600 hover:bg-emerald-700 text-white"
            >
              <CheckCircle2 className="w-3 h-3" /> Resolve
            </Button>
          )}

          {alert.recommendedActionHref && (
            <Link href={alert.recommendedActionHref}>
              <Button size="sm" variant="outline" className="text-xs gap-1 px-2.5">
                Resolve in Module <ArrowRight className="w-3 h-3" />
              </Button>
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
