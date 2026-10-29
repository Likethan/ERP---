"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { studentAffairsService } from "@/services/student-affairs.service";
import {
  GrievanceCaseModel,
  SACasePriority,
} from "@/types/student-affairs";
import { StudentAffairsNav } from "@/components/student-affairs/student-affairs-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Users,
  UserCheck,
  CheckCircle2,
  Clock,
  ShieldAlert,
  ArrowRight,
  RotateCcw,
} from "lucide-react";

const MOCK_OFFICERS = [
  { id: "usr-off-001", name: "Dr. Vikram Sethi", office: "Dean of Student Affairs", caseload: 4 },
  { id: "usr-off-002", name: "Prof. Ananya Nair", office: "Academic Grievance Redressal", caseload: 2 },
  { id: "usr-ombuds-001", name: "Dr. Meenakshi Sundaram", office: "Institutional Ombudsperson", caseload: 1 },
  { id: "usr-icc-001", name: "Prof. Radhika Menon", office: "Safeguarding & Anti-Ragging", caseload: 3 },
];

function CaseAssignmentWorkspaceContent() {
  const searchParams = useSearchParams();
  const preselectedCaseId = searchParams?.get("caseId");

  const [cases, setCases] = useState<GrievanceCaseModel[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>(preselectedCaseId || "");
  const [selectedOfficerId, setSelectedOfficerId] = useState<string>(MOCK_OFFICERS[0].id);
  const [reassignmentReason, setReassignmentReason] = useState("");
  const [priority, setPriority] = useState<SACasePriority>(SACasePriority.MEDIUM);
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");

  useEffect(() => {
    async function load() {
      const data = await studentAffairsService.getCases();
      setCases(data);
      if (preselectedCaseId) {
        setSelectedCaseId(preselectedCaseId);
        const match = data.find((c) => c.id === preselectedCaseId);
        if (match) setPriority(match.priority as SACasePriority);
      } else if (data.length > 0) {
        setSelectedCaseId(data[0].id);
        setPriority(data[0].priority as SACasePriority);
      }
    }
    load();
  }, [preselectedCaseId]);

  const activeCase = cases.find((c) => c.id === selectedCaseId);

  async function handleAssign(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedCaseId || !selectedOfficerId) return;

    setLoading(true);
    try {
      await studentAffairsService.assignCase({
        caseId: selectedCaseId,
        officerId: selectedOfficerId,
        reassignmentReason: reassignmentReason || undefined,
        priority,
        targetResponseHours: 48,
      });
      setSuccessMessage("Case successfully assigned to designated case officer.");
      // Refresh
      const updated = await studentAffairsService.getCases();
      setCases(updated);
    } catch {
      alert("Error assigning case.");
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
          { label: "Assignment Workspace", href: "/app/student-affairs/assignments" },
        ]}
      />

      <div className="border-b border-slate-800 pb-5">
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
          <Users className="h-6 w-6 text-indigo-400" />
          Case Officer Assignment & Workload Governance
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Route cases to authorized officers, distribute institutional caseloads evenly, and record formal reassignment rationales.
        </p>
      </div>

      <StudentAffairsNav />

      {successMessage && (
        <div className="p-3.5 rounded-lg border border-emerald-500/30 bg-emerald-950/20 text-xs text-emerald-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            <span>{successMessage}</span>
          </div>
          <button onClick={() => setSuccessMessage("")} className="text-emerald-400 hover:text-white">
            Dismiss
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Form: 2 Cols */}
        <div className="lg:col-span-2">
          <form onSubmit={handleAssign}>
            <Card className="p-6 border-slate-800 bg-slate-900/40 space-y-5">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
                Assignment Configuration
              </h2>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Select Case Record <span className="text-rose-400">*</span>
                </label>
                <select
                  value={selectedCaseId}
                  onChange={(e) => {
                    setSelectedCaseId(e.target.value);
                    const match = cases.find((c) => c.id === e.target.value);
                    if (match) setPriority(match.priority as SACasePriority);
                  }}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  {cases.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.case_number} - {c.title} ({c.status})
                    </option>
                  ))}
                </select>
              </div>

              {activeCase && (
                <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/60 text-xs space-y-1.5">
                  <div className="flex justify-between text-slate-400">
                    <span>Category: <strong className="text-slate-200">{activeCase.category?.name}</strong></span>
                    <span>Confidentiality: <strong className="text-slate-200">{activeCase.confidentiality_level}</strong></span>
                  </div>
                  <p className="text-slate-300 line-clamp-2">{activeCase.description}</p>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">
                    Designated Case Officer <span className="text-rose-400">*</span>
                  </label>
                  <select
                    value={selectedOfficerId}
                    onChange={(e) => setSelectedOfficerId(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  >
                    {MOCK_OFFICERS.map((off) => (
                      <option key={off.id} value={off.id}>
                        {off.name} ({off.office}) - Caseload: {off.caseload}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">
                    Case Priority Override
                  </label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value as SACasePriority)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value={SACasePriority.LOW}>LOW</option>
                    <option value={SACasePriority.MEDIUM}>MEDIUM</option>
                    <option value={SACasePriority.HIGH}>HIGH</option>
                    <option value={SACasePriority.CRITICAL_URGENT}>CRITICAL URGENT</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Assignment / Reassignment Reason
                </label>
                <textarea
                  rows={3}
                  placeholder="State the institutional justification for assignment or reassignment (e.g. subject matter expertise, conflict recusal)..."
                  value={reassignmentReason}
                  onChange={(e) => setReassignmentReason(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex justify-end pt-2">
                <Button
                  type="submit"
                  disabled={loading}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs gap-2"
                >
                  <UserCheck className="h-4 w-4" />
                  {loading ? "Recording Assignment..." : "Confirm & Commit Assignment"}
                </Button>
              </div>
            </Card>
          </form>
        </div>

        {/* Officer Directory & Active Caseloads: 1 Col */}
        <div className="space-y-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            Authorized Case Officers
          </h2>
          <div className="space-y-3">
            {MOCK_OFFICERS.map((off) => (
              <Card key={off.id} className="p-4 border-slate-800 bg-slate-900/40 text-xs space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-white">{off.name}</span>
                  <Badge variant="outline" className="text-[10px] border-slate-700 text-slate-300">
                    {off.caseload} active cases
                  </Badge>
                </div>
                <p className="text-[11px] text-slate-400">{off.office}</p>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function CaseAssignmentWorkspacePage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-slate-500">Loading assignments...</div>}>
      <CaseAssignmentWorkspaceContent />
    </Suspense>
  );
}

