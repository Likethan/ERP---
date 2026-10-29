"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { studentAffairsService } from "@/services/student-affairs.service";
import {
  GrievanceCaseModel,
  ResolutionActionModel,
  SAActionType,
  SAActionStatus,
} from "@/types/student-affairs";
import { StudentAffairsNav } from "@/components/student-affairs/student-affairs-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  CheckSquare,
  PlusCircle,
  CheckCircle2,
  Clock,
  Wrench,
  FileCheck,
  AlertCircle,
  Building,
} from "lucide-react";

function ResolutionsContent() {
  const searchParams = useSearchParams();
  const preselectedCaseId = searchParams?.get("caseId");

  const [cases, setCases] = useState<GrievanceCaseModel[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>(preselectedCaseId || "");
  const [actionsList, setActionsList] = useState<ResolutionActionModel[]>([]);

  // Action form
  const [desc, setDesc] = useState("");
  const [actionType, setActionType] = useState<SAActionType>(SAActionType.FACILITY_REPAIR);
  const [dueDate, setDueDate] = useState("");
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
      // Consolidate actions
      const allAct: ResolutionActionModel[] = [];
      allCases.forEach((c) => {
        if (c.resolution_actions) allAct.push(...c.resolution_actions);
      });
      setActionsList(allAct);
    }
    load();
  }, [preselectedCaseId]);

  async function handleAddAction(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedCaseId || !desc) return;

    setLoading(true);
    try {
      const created = await studentAffairsService.addResolutionAction({
        caseId: selectedCaseId,
        description: desc,
        actionType,
        dueDate: dueDate || undefined,
      });
      setNotification("Corrective resolution action item logged.");
      setActionsList((prev) => [...prev, created]);
      setDesc("");
      setDueDate("");
    } catch {
      alert("Error logging action item.");
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
          { label: "Resolutions & Actions", href: "/app/student-affairs/resolutions" },
        ]}
      />

      <div className="border-b border-slate-800 pb-5">
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
          <CheckSquare className="h-6 w-6 text-emerald-400" />
          Grievance Resolutions & Corrective Action Tracking
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Monitor assigned institutional remediations, facility engineering repairs, academic adjustments, and closure approvals.
        </p>
      </div>

      <StudentAffairsNav />

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
        {/* Left Column: Actions Table (2 Cols) */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            Active Institutional Corrective Items ({actionsList.length})
          </h2>

          {actionsList.length === 0 ? (
            <Card className="p-8 text-center border-slate-800 bg-slate-900/30 text-xs text-slate-500">
              No active corrective actions recorded.
            </Card>
          ) : (
            <div className="space-y-3">
              {actionsList.map((act) => (
                <Card key={act.id} className="p-4 border-slate-800 bg-slate-900/40 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-white text-xs">{act.description}</span>
                    <Badge className={act.status === "COMPLETED" ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-400"}>
                      {act.status}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
                    <span>Remediation Type: <strong className="text-slate-300">{act.action_type}</strong></span>
                    <span>Target Due Date: {act.due_date || "Open"}</span>
                  </div>
                  {act.completion_notes && (
                    <div className="p-2 rounded bg-emerald-950/20 border border-emerald-500/20 text-[11px] text-emerald-300">
                      <strong>Completion Certification: </strong> {act.completion_notes}
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Add Action Item (1 Col) */}
        <div>
          <Card className="p-6 border-slate-800 bg-slate-900/40 space-y-4">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <PlusCircle className="h-4 w-4 text-emerald-400" />
              Add Corrective Action
            </h2>
            <form onSubmit={handleAddAction} className="space-y-3.5 text-xs">
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
                <label className="block text-slate-300 mb-1">Action Description *</label>
                <textarea
                  rows={3}
                  placeholder="e.g. Replace HEPA air filtration system and re-certify lab airflow velocity..."
                  value={desc}
                  onChange={(e) => setDesc(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Remediation Category</label>
                <select
                  value={actionType}
                  onChange={(e) => setActionType(e.target.value as SAActionType)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                >
                  <option value={SAActionType.FACILITY_REPAIR}>FACILITY REPAIR (Infrastructure / equipment)</option>
                  <option value={SAActionType.GRADE_RECHECK}>GRADE RECHECK (Academic exam verification)</option>
                  <option value={SAActionType.POLICY_REVISION}>POLICY REVISION (Institutional rule amendment)</option>
                  <option value={SAActionType.MEDIATED_AGREEMENT}>MEDIATED AGREEMENT (Peer conciliation pact)</option>
                  <option value={SAActionType.APOLOGY}>FORMAL APOLOGY (Written conciliation)</option>
                  <option value={SAActionType.RESTITUTION}>RESTITUTION (Compensation)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Completion Deadline</label>
                <input
                  type="date"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                />
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-emerald-600 hover:bg-emerald-500 text-white text-xs mt-2"
              >
                Log Corrective Action
              </Button>
            </form>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default function ResolutionsPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-slate-500">Loading resolutions...</div>}>
      <ResolutionsContent />
    </Suspense>
  );
}

