"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Bell,
  Calendar,
  CheckCircle2,
  Clock,
  ExternalLink,
  Eye,
  FileCheck,
  FileText,
  Filter,
  Gavel,
  History,
  Lock,
  Play,
  Plus,
  RefreshCw,
  Scale,
  Search,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Zap,
} from "lucide-react";
import { LegalNav } from "@/components/legal/legal-nav";
import { legalService } from "@/services/legal.service";
import { formatLegalDate } from "@/services/legal-calculator";
import { RenewalSweepResult } from "@/types/legal";

interface DeadlineItem {
  id: string;
  title: string;
  type: "CONTRACT_EXPIRATION" | "RENEWAL_WINDOW" | "OBLIGATION_DUE" | "COMPLIANCE_REVIEW" | "MATTER_MILESTONE";
  due_date: string;
  source_reference: string;
  responsible_owner: string;
  urgency: "OVERDUE" | "URGENT_7_DAYS" | "UPCOMING_30_DAYS" | "SCHEDULED_90_DAYS";
  link: string;
}

const MOCK_DEADLINES: DeadlineItem[] = [
  {
    id: "dl-01",
    title: "Enterprise High-Density Campus Wi-Fi 60-Day Renewal Notice Window",
    type: "RENEWAL_WINDOW",
    due_date: "2027-03-31",
    source_reference: "CON-2026-0042",
    responsible_owner: "Director of IT Network Services",
    urgency: "SCHEDULED_90_DAYS",
    link: "/app/legal/contracts",
  },
  {
    id: "dl-02",
    title: "SOC 2 Type II Security Compliance Deliverable Due",
    type: "OBLIGATION_DUE",
    due_date: "2026-11-15",
    source_reference: "OBL-2026-0042-1",
    responsible_owner: "Lead Infrastructure Architect",
    urgency: "UPCOMING_30_DAYS",
    link: "/app/legal/obligations",
  },
  {
    id: "dl-03",
    title: "Annual Campus Security & Fire Safety (Clery Act) Survey Filing",
    type: "COMPLIANCE_REVIEW",
    due_date: "2026-10-01",
    source_reference: "COMP-2026-CLERY",
    responsible_owner: "Director of Campus Safety & Legal Affairs",
    urgency: "OVERDUE",
    link: "/app/legal/compliance",
  },
  {
    id: "dl-04",
    title: "Cloud Services Provider Mediation Briefing Deadline",
    type: "MATTER_MILESTONE",
    due_date: "2026-11-05",
    source_reference: "MAT-2026-0012",
    responsible_owner: "Adv. Sarah Jenkins (External Counsel)",
    urgency: "URGENT_7_DAYS",
    link: "/app/legal/matters",
  },
  {
    id: "dl-05",
    title: "Institutional Generative AI & Data Policy Annual Review",
    type: "COMPLIANCE_REVIEW",
    due_date: "2027-01-15",
    source_reference: "POL-SEC-2026-001",
    responsible_owner: "Chief Information Security Officer",
    urgency: "SCHEDULED_90_DAYS",
    link: "/app/legal/policies",
  },
];

export default function DeadlinesCalendarPage() {
  const [deadlines, setDeadlines] = useState<DeadlineItem[]>(MOCK_DEADLINES);
  const [selectedFilter, setSelectedFilter] = useState<string>("ALL");
  const [isSweeping, setIsSweeping] = useState(false);
  const [sweepResult, setSweepResult] = useState<RenewalSweepResult | null>(null);
  const [isSweepResultOpen, setIsSweepResultOpen] = useState(false);

  async function handleTriggerSweep() {
    setIsSweeping(true);
    try {
      const result = await legalService.triggerRenewalSweep();
      setSweepResult(result);
      setIsSweepResultOpen(true);
    } catch (err: any) {
      alert("Failed to run renewal sweep: " + err.message);
    } finally {
      setIsSweeping(false);
    }
  }

  const filteredDeadlines = deadlines.filter((d) => {
    if (selectedFilter !== "ALL" && d.urgency !== selectedFilter) return false;
    return true;
  });

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      <LegalNav />

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
              <Calendar className="h-6 w-6 text-indigo-600" /> Legal Deadlines, Expirations & Renewal Automation
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Aggregated institutional timetable for contract renewal windows, contractual obligations, statutory filings, and case milestones.
            </p>
          </div>
          <button
            onClick={handleTriggerSweep}
            disabled={isSweeping}
            className="px-4 py-2.5 rounded-xl bg-indigo-600 text-white font-medium text-sm hover:bg-indigo-700 transition-colors shadow-sm flex items-center gap-2"
          >
            {isSweeping ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <Zap className="h-4 w-4 text-amber-300" />
            )}
            Run Automated Renewal & Expiry Sweep
          </button>
        </div>

        {/* Filter Bar */}
        <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-4">
          <button
            onClick={() => setSelectedFilter("ALL")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              selectedFilter === "ALL"
                ? "bg-indigo-600 text-white"
                : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200"
            }`}
          >
            All Deadlines ({deadlines.length})
          </button>
          <button
            onClick={() => setSelectedFilter("OVERDUE")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              selectedFilter === "OVERDUE"
                ? "bg-rose-600 text-white"
                : "bg-rose-50 dark:bg-rose-950 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-900"
            }`}
          >
            Overdue
          </button>
          <button
            onClick={() => setSelectedFilter("URGENT_7_DAYS")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              selectedFilter === "URGENT_7_DAYS"
                ? "bg-amber-600 text-white"
                : "bg-amber-50 dark:bg-amber-950 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-900"
            }`}
          >
            Urgent (Next 7 Days)
          </button>
          <button
            onClick={() => setSelectedFilter("UPCOMING_30_DAYS")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              selectedFilter === "UPCOMING_30_DAYS"
                ? "bg-indigo-600 text-white"
                : "bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-900"
            }`}
          >
            Next 30 Days
          </button>
          <button
            onClick={() => setSelectedFilter("SCHEDULED_90_DAYS")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              selectedFilter === "SCHEDULED_90_DAYS"
                ? "bg-slate-700 text-white"
                : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
            }`}
          >
            Scheduled (90+ Days)
          </button>
        </div>

        {/* Timeline Grid */}
        <div className="space-y-4">
          {filteredDeadlines.map((item) => (
            <div
              key={item.id}
              className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-slate-300 dark:hover:border-slate-700 transition-all"
            >
              <div className="flex items-start gap-4">
                <span
                  className={`p-3 rounded-xl shrink-0 ${
                    item.urgency === "OVERDUE"
                      ? "bg-rose-50 dark:bg-rose-950 text-rose-600 border border-rose-200 dark:border-rose-900"
                      : item.urgency === "URGENT_7_DAYS"
                      ? "bg-amber-50 dark:bg-amber-950 text-amber-600 border border-amber-200 dark:border-amber-900"
                      : "bg-indigo-50 dark:bg-indigo-950 text-indigo-600 border border-indigo-200 dark:border-indigo-900"
                  }`}
                >
                  <Calendar className="h-5 w-5" />
                </span>

                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-xs px-2.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                      {item.source_reference}
                    </span>
                    <span className="text-xs font-semibold text-slate-500">
                      {item.type.replace(/_/g, " ")}
                    </span>
                    {item.urgency === "OVERDUE" && (
                      <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-rose-100 dark:bg-rose-950 text-rose-700 dark:text-rose-300">
                        OVERDUE
                      </span>
                    )}
                  </div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white">{item.title}</h3>
                  <p className="text-xs text-slate-500">
                    Responsible: <strong className="text-slate-700 dark:text-slate-300">{item.responsible_owner}</strong>
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-4 shrink-0">
                <div className="text-right">
                  <span className="text-xs text-slate-400 block">Due / Target Date</span>
                  <strong className="text-sm font-mono text-slate-900 dark:text-white">
                    {formatLegalDate(item.due_date)}
                  </strong>
                </div>

                <Link
                  href={item.link}
                  className="px-3 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium text-xs hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors flex items-center gap-1.5"
                >
                  View Record <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      </main>

      {/* SWEEP RESULT MODAL */}
      {isSweepResultOpen && sweepResult && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-md w-full p-6 border border-slate-200 dark:border-slate-800 shadow-xl space-y-4">
            <div className="flex items-center gap-3">
              <span className="p-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-950 text-emerald-600 border border-emerald-200 dark:border-emerald-800">
                <CheckCircle2 className="h-6 w-6" />
              </span>
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Renewal & Expiry Sweep Completed
                </h3>
                <p className="text-xs text-slate-500">Scheduled Automation Engine Execution</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-100 dark:border-slate-800">
              <div>
                <span className="text-slate-400 block">Contracts Evaluated</span>
                <strong className="text-base font-bold text-slate-900 dark:text-white">
                  {sweepResult.contracts_evaluated ?? sweepResult.contracts_flagged_expiring}
                </strong>
              </div>
              <div>
                <span className="text-slate-400 block">Flagged Expiring</span>
                <strong className="text-base font-bold text-amber-600">
                  {sweepResult.contracts_flagged_expiring}
                </strong>
              </div>
              <div>
                <span className="text-slate-400 block">Auto-Expired</span>
                <strong className="text-base font-bold text-rose-600">
                  {sweepResult.contracts_auto_expired ?? 0}
                </strong>
              </div>
              <div>
                <span className="text-slate-400 block">Obligations Overdue</span>
                <strong className="text-base font-bold text-rose-600">
                  {sweepResult.obligations_flagged_overdue}
                </strong>
              </div>
              <div className="col-span-2 pt-2 border-t border-slate-200 dark:border-slate-700">
                <span className="text-slate-400 block">Notifications Dispatched</span>
                <strong className="text-sm font-semibold text-emerald-600 flex items-center gap-1 mt-0.5">
                  <Bell className="h-3.5 w-3.5" /> {sweepResult.notifications_dispatched} Alerts Sent
                </strong>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setIsSweepResultOpen(false)}
                className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-medium hover:bg-indigo-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
