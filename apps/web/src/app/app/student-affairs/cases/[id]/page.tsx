"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { studentAffairsService } from "@/services/student-affairs.service";
import { StudentAffairsCalculator } from "@/services/student-affairs-calculator";
import {
  GrievanceCaseModel,
  SACaseStatus,
  SACasePriority,
} from "@/types/student-affairs";
import { StudentAffairsNav } from "@/components/student-affairs/student-affairs-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  ShieldAlert,
  Clock,
  User,
  Paperclip,
  Calendar,
  Scale,
  MessageSquare,
  AlertTriangle,
  Lock,
  CheckCircle2,
  AlertCircle,
  FileText,
  ChevronRight,
  ShieldCheck,
} from "lucide-react";

export default function CaseDetailsPage() {
  const params = useParams();
  const caseId = params?.id as string;
  const [caseItem, setCaseItem] = useState<GrievanceCaseModel | null>(null);
  const [loading, setLoading] = useState(true);
  const [conflictModalOpen, setConflictModalOpen] = useState(false);
  const [conflictReason, setConflictReason] = useState("");

  useEffect(() => {
    async function load() {
      if (!caseId) return;
      setLoading(true);
      const data = await studentAffairsService.getCaseById(caseId);
      setCaseItem(data);
      setLoading(false);
    }
    load();
  }, [caseId]);

  async function handleDeclareConflict() {
    if (!caseItem || !conflictReason) return;
    await studentAffairsService.declareConflict({
      caseId: caseItem.id,
      reason: conflictReason,
    });
    setConflictModalOpen(false);
    alert("Conflict of interest declared. Case has been flagged for reassignment.");
    // Reload
    const updated = await studentAffairsService.getCaseById(caseItem.id);
    setCaseItem(updated);
  }

  if (loading) {
    return (
      <div className="p-8 text-center text-slate-400 text-xs">
        Loading case record...
      </div>
    );
  }

  if (!caseItem) {
    return (
      <div className="p-8 text-center text-slate-400 text-xs">
        Case record not found.
      </div>
    );
  }

  const statusBadge = StudentAffairsCalculator.getStatusBadge(caseItem.status);
  const priorityBadge = StudentAffairsCalculator.getPriorityBadge(caseItem.priority);
  const sla = StudentAffairsCalculator.calculateSlaStatus(
    caseItem.target_response_date,
    caseItem.status
  );

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: "Dashboard", href: "/app/dashboard" },
          { label: "Student Affairs", href: "/app/student-affairs" },
          { label: caseItem.case_number, href: `/app/student-affairs/cases/${caseItem.id}` },
        ]}
      />

      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-5 gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="font-mono text-xl font-bold text-indigo-400">
              {caseItem.case_number}
            </span>
            <span className={`px-2 py-0.5 rounded text-xs border ${statusBadge.className}`}>
              {statusBadge.label}
            </span>
            <span className={`px-2 py-0.5 rounded text-xs border ${priorityBadge.className}`}>
              {priorityBadge.label}
            </span>
            <Badge variant="outline" className="border-slate-700 text-slate-300 text-xs">
              {caseItem.confidentiality_level}
            </Badge>
          </div>
          <h1 className="text-xl font-bold text-white mt-2">{caseItem.title}</h1>
        </div>

        <div className="flex items-center gap-2">
          <Link href={`/app/student-affairs/cases/${caseItem.id}/confidential`}>
            <Button variant="outline" className="border-amber-500/30 text-amber-300 hover:bg-amber-950/20 text-xs gap-1.5">
              <Lock className="h-3.5 w-3.5 text-amber-400" />
              Confidential View
            </Button>
          </Link>
          <Link href={`/app/student-affairs/communications?caseId=${caseItem.id}`}>
            <Button className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs gap-1.5">
              <MessageSquare className="h-3.5 w-3.5" />
              Case Thread
            </Button>
          </Link>
        </div>
      </div>

      <StudentAffairsNav />

      {/* SLA & Governance Summary Strip */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 p-4 rounded-xl border border-slate-800 bg-slate-900/60 text-xs">
        <div>
          <span className="text-slate-400">Institutional Category:</span>
          <p className="font-semibold text-slate-200 mt-0.5">{caseItem.category?.name || "General"}</p>
        </div>
        <div>
          <span className="text-slate-400">Submitter Persona:</span>
          <p className="font-semibold text-slate-200 mt-0.5">{caseItem.submitter_name_redacted}</p>
        </div>
        <div>
          <span className="text-slate-400">SLA Response Window:</span>
          <p className={`font-semibold mt-0.5 ${sla.statusLabel === "BREACHED" ? "text-red-400" : "text-emerald-400"}`}>
            {sla.statusLabel === "RESOLVED" ? "Completed on Time" : `${sla.hoursRemaining} hours remaining`}
          </p>
        </div>
        <div>
          <span className="text-slate-400">Procedural Stage:</span>
          <p className="font-semibold text-indigo-300 mt-0.5">
            {caseItem.disciplinary_proceeding?.procedural_stage || caseItem.status}
          </p>
        </div>
      </div>

      {/* Main Details Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Description & Case Records */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="p-6 border-slate-800 bg-slate-900/40 space-y-4">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Grievance Narrative & Context
            </h2>
            <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">
              {caseItem.description}
            </p>

            {caseItem.requested_resolution && (
              <div className="mt-4 p-3.5 rounded-lg bg-indigo-950/20 border border-indigo-500/20 text-xs">
                <span className="font-semibold text-indigo-300">Requested Remediation: </span>
                <span className="text-slate-300">{caseItem.requested_resolution}</span>
              </div>
            )}
          </Card>

          {/* Evidence Attachments */}
          <Card className="p-6 border-slate-800 bg-slate-900/40 space-y-3">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <Paperclip className="h-4 w-4 text-blue-400" />
              Attached Records & Evidence ({caseItem.evidence_items?.length || 0})
            </h2>

            {caseItem.evidence_items && caseItem.evidence_items.length > 0 ? (
              <div className="space-y-2">
                {caseItem.evidence_items.map((ev) => (
                  <div
                    key={ev.id}
                    className="flex items-center justify-between p-3 rounded-lg border border-slate-800 bg-slate-950/50 text-xs"
                  >
                    <div className="space-y-0.5">
                      <span className="font-medium text-slate-200">{ev.title}</span>
                      <p className="text-[10px] text-slate-500">
                        {ev.evidence_type} • Access Level: {ev.confidentiality_level} {ev.is_redacted && "• Redacted Copy"}
                      </p>
                    </div>
                    <Badge variant="outline" className="border-slate-700 text-indigo-400 text-[10px]">
                      Secure Storage
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic">No supporting documents attached to this submission.</p>
            )}
          </Card>

          {/* Corrective Actions */}
          {caseItem.resolution_actions && caseItem.resolution_actions.length > 0 && (
            <Card className="p-6 border-slate-800 bg-slate-900/40 space-y-3">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Resolution & Corrective Actions
              </h2>
              <div className="space-y-2">
                {caseItem.resolution_actions.map((act) => (
                  <div
                    key={act.id}
                    className="p-3 rounded-lg border border-slate-800 bg-slate-950/40 text-xs flex items-center justify-between"
                  >
                    <div>
                      <span className="font-medium text-slate-200">{act.description}</span>
                      <p className="text-[10px] text-slate-500">Due: {act.due_date || "Pending"}</p>
                    </div>
                    <Badge className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 text-[10px]">
                      {act.status}
                    </Badge>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>

        {/* Right 1 Col: Procedural Actions & Conflict Officer Panel */}
        <div className="space-y-5">
          <Card className="p-5 border-slate-800 bg-slate-900/40 space-y-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Procedural Actions
            </h3>
            <div className="space-y-2">
              <Link href={`/app/student-affairs/assignments?caseId=${caseItem.id}`} className="block">
                <Button variant="outline" size="sm" className="w-full text-xs border-slate-700 text-slate-200 justify-start gap-2">
                  <User className="h-3.5 w-3.5 text-indigo-400" />
                  Assign / Reassign Officer
                </Button>
              </Link>
              <Link href={`/app/student-affairs/meetings?caseId=${caseItem.id}`} className="block">
                <Button variant="outline" size="sm" className="w-full text-xs border-slate-700 text-slate-200 justify-start gap-2">
                  <Calendar className="h-3.5 w-3.5 text-blue-400" />
                  Schedule Hearing / Inquiry
                </Button>
              </Link>
              <Link href={`/app/student-affairs/disciplinary?caseId=${caseItem.id}`} className="block">
                <Button variant="outline" size="sm" className="w-full text-xs border-slate-700 text-slate-200 justify-start gap-2">
                  <Scale className="h-3.5 w-3.5 text-purple-400" />
                  Disciplinary Proceedings
                </Button>
              </Link>
              <Link href={`/app/student-affairs/appeals?caseId=${caseItem.id}`} className="block">
                <Button variant="outline" size="sm" className="w-full text-xs border-slate-700 text-slate-200 justify-start gap-2">
                  <Scale className="h-3.5 w-3.5 text-cyan-400" />
                  Appellate Review
                </Button>
              </Link>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setConflictModalOpen(true)}
                className="w-full text-xs border-amber-500/30 text-amber-300 hover:bg-amber-950/20 justify-start gap-2"
              >
                <AlertCircle className="h-3.5 w-3.5 text-amber-400" />
                Declare Conflict of Interest
              </Button>
            </div>
          </Card>

          {/* Institutional Compliance Card */}
          <Card className="p-5 border-slate-800 bg-slate-900/40 text-xs space-y-2">
            <div className="font-semibold text-slate-300 flex items-center gap-1.5">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              Auditable Integrity
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Every status change, assignment adjustment, and evidence access event is recorded in the immutable audit log under tenant isolation.
            </p>
          </Card>
        </div>
      </div>

      {/* Conflict Modal */}
      {conflictModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
          <Card className="max-w-md w-full p-6 border-slate-800 bg-slate-900 text-xs space-y-4 shadow-2xl">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-amber-400" />
              Declare Conflict of Interest
            </h3>
            <p className="text-slate-400 text-[11px]">
              Institutional fairness requires officers with personal or academic connections to either party to recuse themselves.
            </p>
            <textarea
              rows={3}
              placeholder="State the nature of the relationship or potential conflict..."
              value={conflictReason}
              onChange={(e) => setConflictReason(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-xs text-white"
            />
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="ghost" size="sm" onClick={() => setConflictModalOpen(false)}>
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={handleDeclareConflict}
                className="bg-amber-600 hover:bg-amber-500 text-white"
              >
                Submit Conflict & Reassign
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
