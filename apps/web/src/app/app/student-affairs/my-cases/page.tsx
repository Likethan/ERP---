"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { studentAffairsService } from "@/services/student-affairs.service";
import { StudentAffairsCalculator } from "@/services/student-affairs-calculator";
import { GrievanceCaseModel, SACaseStatus } from "@/types/student-affairs";
import { StudentAffairsNav } from "@/components/student-affairs/student-affairs-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  UserCheck,
  FileEdit,
  Clock,
  ChevronRight,
  MessageSquare,
  Scale,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

export default function MyCasesPage() {
  const [cases, setCases] = useState<GrievanceCaseModel[]>([]);
  const [activeTab, setActiveTab] = useState<"ALL" | "ACTIVE" | "RESOLVED" | "APPEALS">("ALL");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMyCases();
  }, []);

  async function loadMyCases() {
    setLoading(true);
    const data = await studentAffairsService.getCases();
    setCases(data);
    setLoading(false);
  }

  const filtered = cases.filter((c) => {
    if (activeTab === "ACTIVE") {
      return c.status !== SACaseStatus.RESOLVED && c.status !== SACaseStatus.CLOSED;
    }
    if (activeTab === "RESOLVED") {
      return c.status === SACaseStatus.RESOLVED || c.status === SACaseStatus.CLOSED;
    }
    if (activeTab === "APPEALS") {
      return (c.appeals && c.appeals.length > 0) || c.case_type === "APPEAL";
    }
    return true;
  });

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: "Dashboard", href: "/app/dashboard" },
          { label: "Student Affairs", href: "/app/student-affairs" },
          { label: "My Cases", href: "/app/student-affairs/my-cases" },
        ]}
      />

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-5 gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <UserCheck className="h-6 w-6 text-indigo-400" />
            My Registered Grievances & Case Filings
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Personal portal for tracking your submitted grievances, formal notices, hearings, and appellate determinations.
          </p>
        </div>
        <Link href="/app/student-affairs/submit">
          <Button className="bg-indigo-600 hover:bg-indigo-500 text-white gap-2 text-xs">
            <FileEdit className="h-4 w-4" />
            New Submission
          </Button>
        </Link>
      </div>

      <StudentAffairsNav />

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-800 pb-2">
        {(["ALL", "ACTIVE", "RESOLVED", "APPEALS"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              activeTab === tab
                ? "bg-slate-800 text-white border border-slate-700"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {tab === "ALL" && `All Cases (${cases.length})`}
            {tab === "ACTIVE" && `Active (${cases.filter((c) => c.status !== "RESOLVED" && c.status !== "CLOSED").length})`}
            {tab === "RESOLVED" && `Resolved (${cases.filter((c) => c.status === "RESOLVED" || c.status === "CLOSED").length})`}
            {tab === "APPEALS" && `Appeals (${cases.filter((c) => (c.appeals && c.appeals.length > 0) || c.case_type === "APPEAL").length})`}
          </button>
        ))}
      </div>

      {/* Case Cards List */}
      {filtered.length === 0 ? (
        <Card className="p-12 text-center border-slate-800 bg-slate-900/30 space-y-3">
          <div className="mx-auto w-12 h-12 rounded-full bg-slate-800 text-slate-400 flex items-center justify-center">
            <CheckCircle2 className="h-6 w-6" />
          </div>
          <h3 className="text-sm font-semibold text-white">No cases found in this category</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            You do not currently have any cases matching the selected filter.
          </p>
        </Card>
      ) : (
        <div className="space-y-3">
          {filtered.map((c) => {
            const statusBadge = StudentAffairsCalculator.getStatusBadge(c.status);
            const sla = StudentAffairsCalculator.calculateSlaStatus(c.target_response_date, c.status);

            return (
              <Card
                key={c.id}
                className="p-5 border-slate-800 bg-slate-900/40 hover:bg-slate-800/20 transition-colors space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/60 pb-3">
                  <div className="flex items-center gap-2.5">
                    <span className="font-mono text-sm font-bold text-indigo-400">
                      {c.case_number}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[10px] border ${statusBadge.className}`}>
                      {statusBadge.label}
                    </span>
                    <Badge variant="outline" className="border-slate-700 text-slate-300 text-[10px]">
                      {c.case_type}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-400 font-mono">
                    <Clock className="h-3.5 w-3.5 text-slate-500" />
                    <span>Logged on: {new Date(c.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-white">{c.title}</h3>
                  <p className="text-xs text-slate-400 mt-1 line-clamp-2">{c.description}</p>
                </div>

                {c.resolution_summary && (
                  <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-500/20 text-xs">
                    <span className="font-semibold text-emerald-400">Resolution Determination: </span>
                    <span className="text-slate-300">{c.resolution_summary}</span>
                  </div>
                )}

                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
                  <div className="text-xs text-slate-400">
                    Category: <span className="text-slate-300 font-medium">{c.category?.name || "General"}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Link href={`/app/student-affairs/cases/${c.id}`}>
                      <Button size="sm" variant="outline" className="border-slate-700 text-slate-200 text-xs gap-1">
                        View Details
                        <ChevronRight className="h-3 w-3" />
                      </Button>
                    </Link>
                    <Link href={`/app/student-affairs/communications?caseId=${c.id}`}>
                      <Button size="sm" variant="ghost" className="text-indigo-400 hover:text-indigo-300 text-xs gap-1">
                        <MessageSquare className="h-3 w-3" />
                        Messages
                      </Button>
                    </Link>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
