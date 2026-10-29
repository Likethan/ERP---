"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { studentAffairsService } from "@/services/student-affairs.service";
import { StudentAffairsCalculator } from "@/services/student-affairs-calculator";
import { GrievanceCaseModel, SACaseStatus, SACasePriority } from "@/types/student-affairs";
import { StudentAffairsNav } from "@/components/student-affairs/student-affairs-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Inbox,
  Clock,
  UserCheck,
  CheckCircle2,
  ChevronRight,
  Filter,
  AlertTriangle,
  ArrowRight,
} from "lucide-react";

export default function CaseIntakeQueuePage() {
  const [cases, setCases] = useState<GrievanceCaseModel[]>([]);
  const [filter, setFilter] = useState<"PENDING" | "UNASSIGNED" | "CRITICAL" | "ALL">("PENDING");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadIntakeQueue();
  }, []);

  async function loadIntakeQueue() {
    setLoading(true);
    const data = await studentAffairsService.getCases();
    setCases(data);
    setLoading(false);
  }

  const filtered = cases.filter((c) => {
    if (filter === "PENDING") {
      return c.status === SACaseStatus.SUBMITTED;
    }
    if (filter === "UNASSIGNED") {
      return !c.assigned_officer_id;
    }
    if (filter === "CRITICAL") {
      return c.priority === SACasePriority.CRITICAL_URGENT || c.is_escalated;
    }
    return true;
  });

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: "Dashboard", href: "/app/dashboard" },
          { label: "Student Affairs", href: "/app/student-affairs" },
          { label: "Intake Queue", href: "/app/student-affairs/intake" },
        ]}
      />

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-5 gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <Inbox className="h-6 w-6 text-indigo-400" />
            Case Intake, Triage & Prioritization Queue
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Review incoming submissions, validate procedural jurisdiction, adjust priority, and route to authorized officers.
          </p>
        </div>
      </div>

      <StudentAffairsNav />

      {/* Filter Chips */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setFilter("PENDING")}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
            filter === "PENDING"
              ? "bg-indigo-600/20 text-indigo-400 border border-indigo-500/30"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Pending Intake ({cases.filter((c) => c.status === "SUBMITTED").length})
        </button>
        <button
          onClick={() => setFilter("UNASSIGNED")}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
            filter === "UNASSIGNED"
              ? "bg-indigo-600/20 text-indigo-400 border border-indigo-500/30"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Unassigned Officers ({cases.filter((c) => !c.assigned_officer_id).length})
        </button>
        <button
          onClick={() => setFilter("CRITICAL")}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
            filter === "CRITICAL"
              ? "bg-rose-600/20 text-rose-400 border border-rose-500/30"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Critical / Urgent ({cases.filter((c) => c.priority === "CRITICAL_URGENT" || c.is_escalated).length})
        </button>
        <button
          onClick={() => setFilter("ALL")}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
            filter === "ALL"
              ? "bg-slate-800 text-white border border-slate-700"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          All ({cases.length})
        </button>
      </div>

      {/* Queue Table */}
      <Card className="border-slate-800 bg-slate-900/40 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400">
                <th className="py-3 px-4 font-medium">Tracking Ref</th>
                <th className="py-3 px-4 font-medium">Subject & Category</th>
                <th className="py-3 px-4 font-medium">SLA Triage Countdown</th>
                <th className="py-3 px-4 font-medium">Priority</th>
                <th className="py-3 px-4 font-medium">Assigned Officer</th>
                <th className="py-3 px-4 font-medium text-right">Triage Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filtered.map((c) => {
                const priorityBadge = StudentAffairsCalculator.getPriorityBadge(c.priority);
                const sla = StudentAffairsCalculator.calculateSlaStatus(c.target_response_date, c.status);

                return (
                  <tr key={c.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-mono font-semibold text-indigo-400">
                        {c.case_number}
                      </div>
                      <div className="text-[10px] text-slate-500">
                        {new Date(c.created_at).toLocaleDateString()}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-medium text-slate-200 max-w-sm truncate">
                        {c.title}
                      </div>
                      <div className="text-[10px] text-slate-400">
                        {c.category?.name} • {c.confidentiality_level}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`text-[11px] font-mono font-medium ${sla.statusLabel === "BREACHED" ? "text-rose-400 font-bold" : "text-emerald-400"}`}>
                        {sla.statusLabel === "RESOLVED" ? "Acknowledged" : `${sla.hoursRemaining}h remaining`}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] border ${priorityBadge.className}`}>
                        {priorityBadge.label}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-300">
                      {c.assigned_officer_id ? (
                        <span className="text-emerald-400">Assigned</span>
                      ) : (
                        <span className="text-amber-400 italic">Unassigned</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link href={`/app/student-affairs/assignments?caseId=${c.id}`}>
                        <Button size="sm" className="h-7 text-xs bg-indigo-600 hover:bg-indigo-500 text-white gap-1 px-3">
                          Assign & Triage
                          <ArrowRight className="h-3 w-3" />
                        </Button>
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
