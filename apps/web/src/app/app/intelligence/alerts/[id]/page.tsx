"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Clock,
  ShieldAlert,
  Users,
  ExternalLink,
  Activity,
  Layers,
} from "lucide-react";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { aiAlertsService } from "@/services/ai-alerts.service";
import { Alert, AlertStatus } from "@campusos/types";
import {
  SeverityBadge,
  AlertStatusBadge,
  DomainBadge,
} from "@/components/intelligence/intelligence-badge";

export default function AlertDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const id = params?.id as string;

  const [alert, setAlert] = useState<Alert | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAlert = async () => {
      setLoading(true);
      try {
        const res = await aiAlertsService.getAlertById(id);
        if (res.success && res.data) {
          setAlert(res.data);
        }
      } finally {
        setLoading(false);
      }
    };
    if (id) fetchAlert();
  }, [id]);

  const handleAcknowledge = async () => {
    if (!alert) return;
    const res = await aiAlertsService.acknowledgeAlert(alert.id, "Administrator");
    if (res.success && res.data) {
      setAlert(res.data);
      toast({ title: "Alert Acknowledged", variant: "warning" });
    }
  };

  const handleResolve = async () => {
    if (!alert) return;
    const res = await aiAlertsService.resolveAlert(alert.id, "Administrator", "Verified operational fix");
    if (res.success && res.data) {
      setAlert(res.data);
      toast({ title: "Alert Resolved Successfully", variant: "success" });
    }
  };

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-64 w-full rounded-xl" />
      </div>
    );
  }

  if (!alert) {
    return (
      <div className="p-12 text-center bg-white rounded-xl border border-slate-200 space-y-4">
        <p className="text-sm text-slate-500">Alert record not found.</p>
        <Link href="/app/intelligence/alerts">
          <Button size="sm" variant="outline">
            Return to Alert Center
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12 max-w-5xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Breadcrumbs
            items={[
              { label: "Dashboard", href: "/app/dashboard" },
              { label: "Intelligence", href: "/app/intelligence" },
              { label: "Alerts", href: "/app/intelligence/alerts" },
              { label: alert.title },
            ]}
          />
          <div className="flex items-center gap-2 mt-1">
            <Link href="/app/intelligence/alerts">
              <Button variant="ghost" size="sm" className="p-1 h-7 w-7 text-slate-500">
                <ArrowLeft className="w-4 h-4" />
              </Button>
            </Link>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">
              {alert.title}
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {alert.status === AlertStatus.OPEN && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleAcknowledge}
              className="gap-1.5 text-xs"
            >
              Acknowledge Alert
            </Button>
          )}

          {alert.status === AlertStatus.ACKNOWLEDGED && (
            <Button
              size="sm"
              onClick={handleResolve}
              className="gap-1.5 text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              Mark Resolved
            </Button>
          )}

          {alert.recommendedActionHref && (
            <Link href={alert.recommendedActionHref}>
              <Button size="sm" className="gap-1.5 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white">
                Open in Module <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            </Link>
          )}
        </div>
      </div>

      {/* Badges Banner */}
      <div className="flex flex-wrap items-center gap-2.5 p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
        <SeverityBadge severity={alert.severity} />
        <DomainBadge domain={alert.domain} />
        <AlertStatusBadge status={alert.status} />
        <span className="text-slate-400">•</span>
        <span className="text-slate-600">Source: {alert.sourceDomain}</span>
        <span className="text-slate-400">•</span>
        <span className="text-slate-600">
          Detected: {new Date(alert.detectedAt).toLocaleString([], { dateStyle: "medium", timeStyle: "short" })}
        </span>
      </div>

      {/* Detail Layout */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          {/* Reason & Cause */}
          <Card>
            <CardHeader className="py-3 px-4 border-b border-slate-100">
              <CardTitle className="text-sm font-semibold text-slate-900">
                1. Operational Cause & Root Reason
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 text-xs leading-relaxed text-slate-700">
              <p>{alert.reason}</p>
            </CardContent>
          </Card>

          {/* Affected Records */}
          {alert.affectedRecords && alert.affectedRecords.length > 0 && (
            <Card>
              <CardHeader className="py-3 px-4 border-b border-slate-100">
                <CardTitle className="text-sm font-semibold text-slate-900 flex items-center gap-1.5">
                  <Users className="w-4 h-4 text-slate-600" />
                  2. Impacted Records ({alert.affectedRecords.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="divide-y divide-slate-100">
                  {alert.affectedRecords.map((rec) => (
                    <div key={rec.id} className="p-3 px-4 flex items-center justify-between hover:bg-slate-50 text-xs">
                      <div>
                        <p className="font-semibold text-slate-800">{rec.name}</p>
                        <p className="text-[11px] text-slate-500">{rec.type} • ID: {rec.id}</p>
                      </div>
                      <Link href={rec.href}>
                        <Button variant="ghost" size="sm" className="text-xs text-blue-600 gap-1">
                          Inspect Record <ExternalLink className="w-3.5 h-3.5" />
                        </Button>
                      </Link>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right Sidebar: Recommendation & Audit Timeline */}
        <div className="space-y-6">
          <Card className="border-amber-200 bg-amber-50/40">
            <CardHeader className="py-3 px-4 border-b border-amber-100">
              <CardTitle className="text-sm font-semibold text-amber-900 flex items-center gap-1.5">
                <ShieldAlert className="w-4 h-4 text-amber-600" />
                Required Resolution
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 space-y-3 text-xs text-slate-800">
              <p className="leading-relaxed font-medium">{alert.recommendedAction}</p>

              {alert.recommendedActionHref && (
                <Link href={alert.recommendedActionHref} className="block pt-2">
                  <Button size="sm" className="w-full text-xs font-semibold bg-amber-600 hover:bg-amber-700 text-white gap-1">
                    Resolve in Module <ArrowRight className="w-3 h-3" />
                  </Button>
                </Link>
              )}
            </CardContent>
          </Card>

          {/* Audit History */}
          <Card>
            <CardHeader className="py-3 px-4 border-b border-slate-100">
              <CardTitle className="text-sm font-semibold text-slate-900 flex items-center gap-1.5">
                <Activity className="w-4 h-4 text-slate-600" />
                Alert Lifecycle History
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 text-xs space-y-3">
              <div className="relative pl-4 border-l-2 border-slate-200 space-y-3">
                <div className="relative">
                  <span className="w-2 h-2 rounded-full bg-rose-500 absolute -left-[21px] top-1" />
                  <p className="font-semibold text-slate-800">Alert Triggered</p>
                  <p className="text-[11px] text-slate-500">Autonomous SLA threshold breach</p>
                  <span className="text-[10px] text-slate-400">
                    {new Date(alert.detectedAt).toLocaleDateString([], { month: "short", day: "numeric" })}
                  </span>
                </div>

                {alert.acknowledgedAt && (
                  <div className="relative">
                    <span className="w-2 h-2 rounded-full bg-amber-500 absolute -left-[21px] top-1" />
                    <p className="font-semibold text-slate-800">Acknowledged</p>
                    <p className="text-[11px] text-slate-500">By {alert.acknowledgedBy || "Officer"}</p>
                    <span className="text-[10px] text-slate-400">
                      {new Date(alert.acknowledgedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                  </div>
                )}

                {alert.resolvedAt && (
                  <div className="relative">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 absolute -left-[21px] top-1" />
                    <p className="font-semibold text-slate-800">Resolved</p>
                    <p className="text-[11px] text-slate-500">By {alert.resolvedBy || "Officer"}</p>
                    <span className="text-[10px] text-slate-400">
                      {new Date(alert.resolvedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
