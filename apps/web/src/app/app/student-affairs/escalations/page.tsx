"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { studentAffairsService } from "@/services/student-affairs.service";
import {
  GrievanceCaseModel,
  CaseEscalationModel,
  SAEscalationLevel,
  SAEscalationStatus,
} from "@/types/student-affairs";
import { StudentAffairsNav } from "@/components/student-affairs/student-affairs-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  AlertTriangle,
  ShieldAlert,
  CheckCircle2,
  Clock,
  User,
  PhoneCall,
  PlusCircle,
} from "lucide-react";

function EscalationQueueContent() {
  const searchParams = useSearchParams();
  const preselectedCaseId = searchParams?.get("caseId");

  const [cases, setCases] = useState<GrievanceCaseModel[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>(preselectedCaseId || "");
  const [escalations, setEscalations] = useState<CaseEscalationModel[]>([]);

  // Trigger form
  const [level, setLevel] = useState<SAEscalationLevel>(SAEscalationLevel.LEVEL_2_DIRECTOR);
  const [triggerReason, setTriggerReason] = useState("");
  const [safeguardingLeadId, setSafeguardingLeadId] = useState("usr-icc-001");
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState("");

  useEffect(() => {
    async function load() {
      const allCases = await studentAffairsService.getCases();
      setCases(allCases);
      if (preselectedCaseId) {
        setSelectedCaseId(preselectedCaseId);
      } else if (allCases.length > 0) {
        setSelectedCaseId(allCases[0].id);
      }

      // Collect mock escalations
      const activeEscCases = allCases.filter((c) => c.is_escalated);
      const generated: CaseEscalationModel[] = activeEscCases.map((c, i) => ({
        id: `esc-live-${i}`,
        tenant_id: c.tenant_id,
        case_id: c.id,
        escalation_level: SAEscalationLevel.LEVEL_2_DIRECTOR,
        status: SAEscalationStatus.ACTIVE,
        trigger_reason: c.escalation_reason || "Urgent safeguarding report flagged for immediate review.",
        escalated_by_id: "usr-current-officer",
        safeguarding_lead_id: "usr-icc-001",
        created_at: c.created_at,
        updated_at: c.updated_at,
      }));
      setEscalations(generated);
    }
    load();
  }, [preselectedCaseId]);

  async function handleTriggerEscalation(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedCaseId || !triggerReason) return;

    setLoading(true);
    try {
      const created = await studentAffairsService.triggerEscalation({
        caseId: selectedCaseId,
        escalationLevel: level,
        triggerReason,
        safeguardingLeadId,
      });
      setNotification(`Case escalated to ${level}. Priority elevated to Critical Urgent.`);
      setEscalations((prev) => [created, ...prev]);
      setTriggerReason("");
    } catch {
      alert("Error escalating case.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: "Dashboard", href: "/app/dashboard" },
          { label: "Student Affairs", href: "/app/student-affairs" },
          { label: "Escalation Queue", href: "/app/student-affairs/escalations" },
        ]}
      />

      <div className="border-b border-slate-800 pb-5">
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
          <AlertTriangle className="h-6 w-6 text-rose-400" />
          Urgent Safeguarding & Executive Escalation Queue
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          High-priority incident dispatch for anti-ragging, safety threats, acute harassment, and Dean-level intervention.
        </p>
      </div>

      <StudentAffairsNav />

      {/* Emergency Disclaimer */}
      <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-950/20 text-xs text-rose-200 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <PhoneCall className="h-5 w-5 text-rose-400 shrink-0" />
          <div>
            <strong>Campus Security Emergency Hotlines:</strong> Extension 100 / Mobile +91 80 2345 6799
            <p className="text-[11px] text-rose-300/70 mt-0.5">
              This digital workflow manages administrative safeguarding. In immediate danger or medical crises, contact local emergency services immediately.
            </p>
          </div>
        </div>
      </div>

      {notification && (
        <div className="p-3.5 rounded-lg border border-emerald-500/30 bg-emerald-950/20 text-xs text-emerald-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            <span>{notification}</span>
          </div>
          <button onClick={() => setNotification("")} className="text-emerald-400 hover:text-white">
            Dismiss
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Active Escalations (2 Cols) */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            Active Safeguarding Incidents ({escalations.length})
          </h2>

          {escalations.length === 0 ? (
            <Card className="p-8 text-center border-slate-800 bg-slate-900/30 text-xs text-slate-500">
              No active safeguarding incidents currently escalated.
            </Card>
          ) : (
            <div className="space-y-3">
              {escalations.map((esc) => (
                <Card
                  key={esc.id}
                  className="p-5 border-rose-500/20 bg-slate-900/40 space-y-3 hover:bg-slate-800/20 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-bold text-rose-400">
                        Incident #{esc.id.slice(0, 10)}
                      </span>
                      <Badge className="bg-rose-500/10 text-rose-400 border-rose-500/20 text-[10px]">
                        {esc.escalation_level}
                      </Badge>
                    </div>
                    <Badge variant="outline" className="border-slate-700 text-slate-300 text-[10px]">
                      {esc.status}
                    </Badge>
                  </div>

                  <p className="text-xs text-slate-300 font-medium">{esc.trigger_reason}</p>

                  <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/60">
                    <span>Designated Lead: <strong className="text-slate-200">Prof. Radhika Menon (ICC)</strong></span>
                    <span>Flagged on: {new Date(esc.created_at).toLocaleDateString()}</span>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Trigger Escalation Form (1 Col) */}
        <div>
          <Card className="p-6 border-slate-800 bg-slate-900/40 space-y-4">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <PlusCircle className="h-4 w-4 text-rose-400" />
              Elevate Case to Escalation
            </h2>

            <form onSubmit={handleTriggerEscalation} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-300 mb-1">Target Case Ref *</label>
                <select
                  value={selectedCaseId}
                  onChange={(e) => setSelectedCaseId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                >
                  {cases.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.case_number} - {c.title}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Escalation Tier *</label>
                <select
                  value={level}
                  onChange={(e) => setLevel(e.target.value as SAEscalationLevel)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                >
                  <option value={SAEscalationLevel.LEVEL_1_LEAD}>LEVEL 1 - Department Head / Lead Officer</option>
                  <option value={SAEscalationLevel.LEVEL_2_DIRECTOR}>LEVEL 2 - Dean / Safeguarding Director</option>
                  <option value={SAEscalationLevel.LEVEL_3_EXECUTIVE_SAFEGUARDING}>LEVEL 3 - Executive Syndicate / Anti-Ragging Council</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Trigger Rationale & Threats *</label>
                <textarea
                  rows={4}
                  placeholder="State the safety threat, pattern of harassment, or non-responsive deadline..."
                  value={triggerReason}
                  onChange={(e) => setTriggerReason(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                  required
                />
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold mt-2"
              >
                Trigger Priority Escalation
              </Button>
            </form>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default function EscalationQueuePage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-slate-400">Loading escalation queue...</div>}>
      <EscalationQueueContent />
    </Suspense>
  );
}

