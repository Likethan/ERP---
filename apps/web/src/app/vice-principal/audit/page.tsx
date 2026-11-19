"use client";

import React, { useEffect, useState } from "react";
import { vicePrincipalService } from "@/services/vice-principal.service";
import { InstitutionalAuditLog } from "@/types/vice-principal";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  ShieldAlert,
  Search,
  Filter,
  Clock,
  User,
  ShieldCheck,
  History,
  RefreshCw,
} from "lucide-react";

export default function VicePrincipalAuditPage() {
  const [logs, setLogs] = useState<InstitutionalAuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    loadAuditTrail();
  }, []);

  const loadAuditTrail = async () => {
    setLoading(true);
    try {
      const res = await vicePrincipalService.getAuditTrail();
      if (res.success && res.data) {
        setLogs(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  const filteredLogs = logs.filter((log) => {
    return (
      log.action.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.actor.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.entity.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.details.toLowerCase().includes(searchQuery.toLowerCase())
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Institutional Statutory Activity & Audit Trail
          </h1>
          <p className="text-sm text-slate-600">
            Immutable, read-only chronological record of executive approvals,
            syllabus intervention sanctions, and circular dispatches.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge
            variant="outline"
            className="text-xs font-mono gap-1 text-slate-600"
          >
            <ShieldCheck className="h-3 w-3 text-emerald-600" />
            Append-Only Audit Journal
          </Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={loadAuditTrail}
            className="gap-1.5"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Refresh</span>
          </Button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="flex items-center rounded-xl border border-slate-200 bg-white p-3 shadow-xs">
        <Search className="h-4 w-4 text-slate-400 mr-2" />
        <input
          type="text"
          placeholder="Filter audit entries by actor, action type, entity or remarks..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full text-xs text-slate-900 placeholder:text-slate-400 focus:outline-hidden"
        />
      </div>

      {/* Audit Log Table */}
      <Card className="shadow-xs border-slate-200">
        <CardHeader className="border-b border-slate-100 pb-3">
          <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
            <History className="h-4 w-4 text-indigo-600" />
            Executive Action History
          </CardTitle>
          <CardDescription className="text-xs text-slate-500">
            Showing verified ledger entries matching compliance query
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-[10px] font-bold uppercase tracking-wider text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Timestamp</th>
                  <th className="px-3 py-3">Executive Actor</th>
                  <th className="px-3 py-3">Action Type</th>
                  <th className="px-3 py-3">Target Entity</th>
                  <th className="px-3 py-3">Decision / Operational Detail</th>
                  <th className="px-4 py-3 text-right">Host IP</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-sans">
                {filteredLogs.map((log) => (
                  <tr
                    key={log.id}
                    className="hover:bg-slate-50 transition-colors"
                  >
                    <td className="px-4 py-3 text-slate-500 font-mono text-[11px] whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-3 py-3 font-semibold text-slate-900">
                      {log.actor}
                    </td>
                    <td className="px-3 py-3">
                      <span className="rounded bg-indigo-50 border border-indigo-200 px-1.5 py-0.5 text-[10px] font-mono font-bold text-indigo-800">
                        {log.action}
                      </span>
                    </td>
                    <td className="px-3 py-3 font-bold text-slate-800">
                      {log.entity}
                    </td>
                    <td className="px-3 py-3 text-slate-600 max-w-md">
                      {log.details}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-[11px] text-slate-400">
                      {log.ip_address}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
