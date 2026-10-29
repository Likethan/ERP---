"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { studentAffairsService } from "@/services/student-affairs.service";
import {
  GrievanceCaseModel,
} from "@/types/student-affairs";
import { StudentAffairsNav } from "@/components/student-affairs/student-affairs-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Lock,
  ShieldAlert,
  AlertTriangle,
  Eye,
  FileText,
  UserCheck,
  ShieldCheck,
  ArrowLeft,
  CheckCircle2,
} from "lucide-react";

export default function ConfidentialCaseDetailPage() {
  const params = useParams();
  const caseId = params?.id as string;
  const [caseItem, setCaseItem] = useState<GrievanceCaseModel | null>(null);
  const [loading, setLoading] = useState(true);
  const [auditConfirmed, setAuditConfirmed] = useState(true);

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

  if (loading) {
    return <div className="p-8 text-center text-slate-400 text-xs">Accessing confidential vault...</div>;
  }

  if (!caseItem) {
    return <div className="p-8 text-center text-slate-400 text-xs">Confidential record not found.</div>;
  }

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: "Dashboard", href: "/app/dashboard" },
          { label: "Student Affairs", href: "/app/student-affairs" },
          { label: caseItem.case_number, href: `/app/student-affairs/cases/${caseItem.id}` },
          { label: "Confidential Record", href: `/app/student-affairs/cases/${caseItem.id}/confidential` },
        ]}
      />

      {/* Red Banner: Restricted Access Vault */}
      <div className="p-4 rounded-xl border border-amber-500/40 bg-amber-950/20 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-amber-500/20 text-amber-400">
            <Lock className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white flex items-center gap-2">
              Confidential & Restricted Vault: {caseItem.case_number}
              <Badge className="bg-amber-500/10 text-amber-400 border-amber-500/20 text-[10px]">
                Audited View
              </Badge>
            </h1>
            <p className="text-xs text-amber-300/80">
              Authorized personnel only. Your access event has been written to the permanent institutional case audit log.
            </p>
          </div>
        </div>
        <Link href={`/app/student-affairs/cases/${caseItem.id}`}>
          <Button variant="outline" size="sm" className="border-amber-500/30 text-amber-200 text-xs gap-1">
            <ArrowLeft className="h-3.5 w-3.5" />
            Standard View
          </Button>
        </Link>
      </div>

      <StudentAffairsNav />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Unredacted Case Details */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="p-6 border-slate-800 bg-slate-900/40 space-y-4">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Unredacted Submitter Identity & Profile
            </h2>
            <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800 text-xs space-y-2">
              <div className="flex justify-between py-1 border-b border-slate-800/80">
                <span className="text-slate-400">Registered Persona:</span>
                <span className="text-white font-medium">{caseItem.submitter_name_redacted}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/80">
                <span className="text-slate-400">Submitter Type:</span>
                <span className="text-slate-200">{caseItem.submitter_type}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/80">
                <span className="text-slate-400">Anonymity Flag:</span>
                <span className={caseItem.is_anonymous ? "text-amber-400 font-semibold" : "text-emerald-400"}>
                  {caseItem.is_anonymous ? "Protected Identity (Restricted from public logs)" : "Standard Submitter"}
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Confidentiality Tier:</span>
                <span className="text-indigo-400 font-semibold">{caseItem.confidentiality_level}</span>
              </div>
            </div>
          </Card>

          {/* Sensitive Evidence & Statements */}
          <Card className="p-6 border-slate-800 bg-slate-900/40 space-y-4">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <FileText className="h-4 w-4 text-indigo-400" />
              Restricted Witness Statements & Evidence
            </h2>
            {caseItem.evidence_items && caseItem.evidence_items.length > 0 ? (
              <div className="space-y-3">
                {caseItem.evidence_items.map((ev) => (
                  <div
                    key={ev.id}
                    className="p-3.5 rounded-lg border border-slate-800 bg-slate-950/60 text-xs space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-white">{ev.title}</span>
                      <Badge className={ev.is_redacted ? "bg-amber-500/10 text-amber-400" : "bg-purple-500/10 text-purple-400"}>
                        {ev.confidentiality_level}
                      </Badge>
                    </div>
                    <p className="text-slate-400 text-[11px]">{ev.description}</p>
                    <div className="flex items-center justify-between pt-1 border-t border-slate-800/60 text-[10px] text-slate-500">
                      <span>Status: {ev.is_redacted ? "Redacted copy available" : "Original Unredacted Evidence"}</span>
                      <Link href={`/app/student-affairs/evidence?caseId=${caseItem.id}`}>
                        <Button size="sm" variant="ghost" className="h-6 text-[10px] text-indigo-400">
                          Redact for Panel
                        </Button>
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic">No evidence items recorded in vault.</p>
            )}
          </Card>
        </div>

        {/* Right Col: Safeguarding & Escalation Triggers */}
        <div className="space-y-5">
          <Card className="p-5 border-slate-800 bg-slate-900/40 space-y-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Safeguarding Controls
            </h3>
            <div className="space-y-2">
              <Link href={`/app/student-affairs/escalations?caseId=${caseItem.id}`} className="block">
                <Button className="w-full text-xs bg-rose-600 hover:bg-rose-500 text-white gap-2 justify-start">
                  <AlertTriangle className="h-4 w-4" />
                  Trigger Urgent Escalation
                </Button>
              </Link>
              <Link href={`/app/student-affairs/evidence?caseId=${caseItem.id}`} className="block">
                <Button variant="outline" className="w-full text-xs border-slate-700 text-slate-200 justify-start gap-2">
                  <FileText className="h-4 w-4 text-indigo-400" />
                  Redaction Workspace
                </Button>
              </Link>
            </div>
          </Card>

          <Card className="p-5 border-slate-800 bg-slate-900/40 text-xs space-y-2">
            <h3 className="font-semibold text-slate-300 flex items-center gap-1.5">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              Privacy Compliance
            </h3>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Unredacted records must remain confidential within the committee. Any disclosure to unauthorized staff or external parties violates institutional privacy policy.
            </p>
          </Card>
        </div>
      </div>
    </div>
  );
}
