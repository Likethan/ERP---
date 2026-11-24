"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  AlertCircle,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  RefreshCw,
  ArrowRight,
  ShieldAlert,
} from "lucide-react";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/toast";
import { aiAlertsService } from "@/services/ai-alerts.service";
import {
  Alert,
  AlertStatus,
  AlertSeverity,
  IntelligenceDomain,
} from "@campusos/types";
import { AlertCard } from "@/components/intelligence/alert-card";

export default function AlertsCenterPage() {
  const { toast } = useToast();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [severityFilter, setSeverityFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [domainFilter, setDomainFilter] = useState("ALL");
  const [search, setSearch] = useState("");

  const loadAlerts = async () => {
    setLoading(true);
    try {
      const res = await aiAlertsService.listAlerts({
        severity: severityFilter,
        status: statusFilter,
        domain: domainFilter,
        search,
      });
      if (res.success && res.data) {
        setAlerts(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, [severityFilter, statusFilter, domainFilter, search]);

  const handleAcknowledge = async (id: string) => {
    const res = await aiAlertsService.acknowledgeAlert(id, "Administrator");
    if (res.success && res.data) {
      setAlerts((prev) =>
        prev.map((a) =>
          a.id === id ? { ...a, status: AlertStatus.ACKNOWLEDGED } : a,
        ),
      );
      toast({ title: "Alert Acknowledged", variant: "warning" });
    }
  };

  const handleResolve = async (id: string) => {
    const res = await aiAlertsService.resolveAlert(
      id,
      "Administrator",
      "Operational correction verified",
    );
    if (res.success && res.data) {
      setAlerts((prev) =>
        prev.map((a) =>
          a.id === id ? { ...a, status: AlertStatus.RESOLVED } : a,
        ),
      );
      toast({ title: "Alert Resolved", variant: "success" });
    }
  };

  const handleDismiss = async (id: string) => {
    const res = await aiAlertsService.dismissAlert(id, "Administrator");
    if (res.success && res.data) {
      setAlerts((prev) =>
        prev.map((a) =>
          a.id === id ? { ...a, status: AlertStatus.DISMISSED } : a,
        ),
      );
      toast({ title: "Alert Dismissed", variant: "neutral" });
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
              { label: "Alerts" },
            ]}
          />
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">
            Operational Alert Center
          </h1>
          <p className="text-sm text-slate-500">
            Real-time threshold breaches, statutory deadlines, and risk signals
            across campus operations.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/app/intelligence">
            <Button variant="outline" size="sm" className="gap-1.5 text-xs">
              Overview Dashboard
            </Button>
          </Link>
          <Link href="/app/intelligence/assistant">
            <Button
              size="sm"
              className="gap-1.5 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white"
            >
              Investigate with AI
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
              placeholder="Search alerts by title, domain, or reason..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-lg border border-slate-200 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Severity Filter */}
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-blue-500"
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="WARNING">Warning</option>
              <option value="INFO">Info</option>
            </select>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-blue-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="OPEN">Open</option>
              <option value="ACKNOWLEDGED">Acknowledged</option>
              <option value="RESOLVED">Resolved</option>
              <option value="DISMISSED">Dismissed</option>
            </select>

            {/* Domain Filter */}
            <select
              value={domainFilter}
              onChange={(e) => setDomainFilter(e.target.value)}
              className="bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-blue-500"
            >
              <option value="ALL">All Domains</option>
              <option value="ATTENDANCE">Attendance</option>
              <option value="EXAMINATIONS">Examinations</option>
              <option value="FINANCE">Finance</option>
              <option value="PLACEMENT">Placement</option>
              <option value="INFRASTRUCTURE">Infrastructure</option>
              <option value="DOCUMENTS">Documents</option>
            </select>
          </div>
        </div>
      </div>

      {/* Alerts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="h-44 rounded-xl bg-slate-100 animate-pulse"
            />
          ))
        ) : alerts.length === 0 ? (
          <div className="col-span-full p-12 text-center bg-white rounded-xl border border-slate-200 text-xs text-slate-500">
            No alerts match your selected filters. All operational parameters
            normal.
          </div>
        ) : (
          alerts.map((alert) => (
            <AlertCard
              key={alert.id}
              alert={alert}
              onAcknowledge={handleAcknowledge}
              onResolve={handleResolve}
              onDismiss={handleDismiss}
            />
          ))
        )}
      </div>
    </div>
  );
}
