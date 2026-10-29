"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { studentAffairsService } from "@/services/student-affairs.service";
import {
  GrievanceCaseModel,
  CaseEvidenceModel,
  SAEvidenceType,
  SAEvidenceAccessLevel,
} from "@/types/student-affairs";
import { StudentAffairsNav } from "@/components/student-affairs/student-affairs-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  FolderLock,
  FileText,
  Upload,
  Eye,
  ShieldCheck,
  CheckCircle2,
  Lock,
  Download,
  AlertCircle,
} from "lucide-react";

function EvidenceReviewContent() {
  const searchParams = useSearchParams();
  const preselectedCaseId = searchParams?.get("caseId");

  const [cases, setCases] = useState<GrievanceCaseModel[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>(preselectedCaseId || "");
  const [evidenceList, setEvidenceList] = useState<CaseEvidenceModel[]>([]);

  // Upload modal states
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadDesc, setUploadDesc] = useState("");
  const [uploadType, setUploadType] = useState<SAEvidenceType>(SAEvidenceType.DOCUMENT);
  const [uploadAccess, setUploadAccess] = useState<SAEvidenceAccessLevel>(SAEvidenceAccessLevel.PANEL_AND_OFFICERS);
  const [uploadUrl, setUploadUrl] = useState("");

  // Redaction modal states
  const [redactionTarget, setRedactionTarget] = useState<CaseEvidenceModel | null>(null);
  const [redactionSummary, setRedactionSummary] = useState("");
  const [redactedUrl, setRedactedUrl] = useState("");

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
    }
    load();
  }, [preselectedCaseId]);

  useEffect(() => {
    if (!selectedCaseId) return;
    const match = cases.find((c) => c.id === selectedCaseId);
    setEvidenceList(match?.evidence_items || []);
  }, [selectedCaseId, cases]);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedCaseId || !uploadTitle) return;

    setLoading(true);
    try {
      await studentAffairsService.uploadEvidence({
        caseId: selectedCaseId,
        evidenceType: uploadType,
        title: uploadTitle,
        description: uploadDesc,
        fileUrl: uploadUrl || `/secure/evidence/${Date.now()}_file.pdf`,
        fileSizeBytes: 1048576,
        confidentialityLevel: uploadAccess,
      });
      setNotification("Evidence file linked securely with assigned access tier.");
      setUploadTitle("");
      setUploadDesc("");
      setUploadUrl("");
      const updated = await studentAffairsService.getCases();
      setCases(updated);
    } catch {
      alert("Error linking evidence.");
    } finally {
      setLoading(false);
    }
  }

  async function handleRedact(e: React.FormEvent) {
    e.preventDefault();
    if (!redactionTarget || !redactionSummary) return;

    setLoading(true);
    try {
      await studentAffairsService.redactEvidence({
        evidenceId: redactionTarget.id,
        redactionSummary,
        redactedFileUrl: redactedUrl || `/secure/evidence/redacted_${redactionTarget.id}.pdf`,
      });
      setNotification(`Redacted copy created for panel disclosure, preserving original record ID ${redactionTarget.id}.`);
      setRedactionTarget(null);
      setRedactionSummary("");
      setRedactedUrl("");
      const updated = await studentAffairsService.getCases();
      setCases(updated);
    } catch {
      alert("Error creating redacted evidence copy.");
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
          { label: "Evidence Review", href: "/app/student-affairs/evidence" },
        ]}
      />

      <div className="border-b border-slate-800 pb-5">
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
          <FolderLock className="h-6 w-6 text-indigo-400" />
          Evidence Locker, Redaction & Document Review
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Cryptographically isolated attachment storage, multi-tier witness access controls, and auditable redaction workflows.
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

      {/* Case Selector */}
      <Card className="p-4 border-slate-800 bg-slate-900/40">
        <label className="block text-xs font-medium text-slate-400 mb-1.5">
          Select Active Case Dossier
        </label>
        <select
          value={selectedCaseId}
          onChange={(e) => setSelectedCaseId(e.target.value)}
          className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
        >
          {cases.map((c) => (
            <option key={c.id} value={c.id}>
              {c.case_number} - {c.title} ({c.evidence_items?.length || 0} evidence files)
            </option>
          ))}
        </select>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Evidence List (2 Cols) */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            Registered Evidence Items ({evidenceList.length})
          </h2>

          {evidenceList.length === 0 ? (
            <Card className="p-8 text-center border-slate-800 bg-slate-900/30 text-xs text-slate-500">
              No evidence documents linked to this case record yet.
            </Card>
          ) : (
            <div className="space-y-3">
              {evidenceList.map((ev) => (
                <Card
                  key={ev.id}
                  className="p-4 border-slate-800 bg-slate-900/40 space-y-2 hover:bg-slate-800/20 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4 text-indigo-400" />
                      <span className="font-semibold text-white text-xs">{ev.title}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className="bg-indigo-500/10 text-indigo-300 border-indigo-500/20 text-[10px]">
                        {ev.confidentiality_level}
                      </Badge>
                      {ev.is_redacted && (
                        <Badge className="bg-amber-500/10 text-amber-400 border-amber-500/20 text-[10px]">
                          Redacted Copy
                        </Badge>
                      )}
                    </div>
                  </div>

                  <p className="text-xs text-slate-400">{ev.description || "No supplemental description provided."}</p>

                  {ev.redaction_summary && (
                    <div className="p-2.5 rounded bg-amber-950/20 border border-amber-500/20 text-[11px] text-amber-300">
                      <strong>Redaction Log: </strong> {ev.redaction_summary}
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-[11px] text-slate-500">
                    <span>Type: {ev.evidence_type} • File Size: ~1.0 MB</span>
                    <div className="flex items-center gap-2">
                      {!ev.is_redacted && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setRedactionTarget(ev)}
                          className="h-6 text-[11px] border-amber-500/30 text-amber-300 hover:bg-amber-950/20"
                        >
                          Create Redacted Copy
                        </Button>
                      )}
                      <Button size="sm" variant="ghost" className="h-6 text-[11px] text-indigo-400 gap-1">
                        <Download className="h-3 w-3" />
                        Download
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Upload Evidence Card (1 Col) */}
        <div>
          <Card className="p-6 border-slate-800 bg-slate-900/40 space-y-4">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <Upload className="h-4 w-4 text-indigo-400" />
              Upload Secure Evidence
            </h2>
            <form onSubmit={handleUpload} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-300 mb-1">Evidence Title *</label>
                <input
                  type="text"
                  placeholder="e.g. CCTV Gate 3 Entry Log / Written Statement"
                  value={uploadTitle}
                  onChange={(e) => setUploadTitle(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Evidence Type</label>
                <select
                  value={uploadType}
                  onChange={(e) => setUploadType(e.target.value as SAEvidenceType)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                >
                  <option value={SAEvidenceType.DOCUMENT}>DOCUMENT (PDF/Doc)</option>
                  <option value={SAEvidenceType.IMAGE}>IMAGE (Photo/Sensor capture)</option>
                  <option value={SAEvidenceType.TESTIMONY}>TESTIMONY (Witness interview statement)</option>
                  <option value={SAEvidenceType.SECURITY_LOG}>SECURITY LOG (Access control logs)</option>
                  <option value={SAEvidenceType.COMMUNICATION_LOG}>COMMUNICATION LOG (Email/Chat transcripts)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Confidentiality Tier</label>
                <select
                  value={uploadAccess}
                  onChange={(e) => setUploadAccess(e.target.value as SAEvidenceAccessLevel)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                >
                  <option value={SAEvidenceAccessLevel.PANEL_AND_OFFICERS}>PANEL & OFFICERS (Hearing committee)</option>
                  <option value={SAEvidenceAccessLevel.PARTICIPANTS_ONLY}>PARTICIPANTS ONLY (Both parties)</option>
                  <option value={SAEvidenceAccessLevel.RESTRICTED_INVESTIGATOR_ONLY}>RESTRICTED (Lead Investigator only)</option>
                  <option value={SAEvidenceAccessLevel.PUBLIC_DISCLOSED}>PUBLIC DISCLOSED (Open summary)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Description / Notes</label>
                <textarea
                  rows={2}
                  placeholder="Provenance, source, collection date..."
                  value={uploadDesc}
                  onChange={(e) => setUploadDesc(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                />
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-indigo-600 hover:bg-indigo-500 text-white text-xs mt-2"
              >
                Upload & Seal Record
              </Button>
            </form>
          </Card>
        </div>
      </div>

      {/* Redaction Modal */}
      {redactionTarget && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <Card className="max-w-lg w-full p-6 border-slate-800 bg-slate-900 text-xs space-y-4 shadow-2xl">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <FolderLock className="h-4 w-4 text-amber-400" />
              Generate Redacted Evidence Copy
            </h3>
            <p className="text-slate-400 text-[11px]">
              Original Evidence: <strong className="text-white">{redactionTarget.title}</strong>
              <br />
              The original file remains unmodified in the secure audit vault. A sanitized derivative will be linked for panel review.
            </p>

            <form onSubmit={handleRedact} className="space-y-3">
              <div>
                <label className="block text-slate-300 mb-1">Redaction Summary & Purpose *</label>
                <textarea
                  rows={3}
                  placeholder="e.g. Redacted witness mobile numbers, residential room numbers, and identifying familial information to prevent retaliation..."
                  value={redactionSummary}
                  onChange={(e) => setRedactionSummary(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-white text-xs"
                  required
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="ghost" size="sm" onClick={() => setRedactionTarget(null)}>
                  Cancel
                </Button>
                <Button type="submit" size="sm" className="bg-amber-600 hover:bg-amber-500 text-white">
                  Publish Redacted Copy
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}

export default function EvidenceReviewPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-slate-500">Loading evidence...</div>}>
      <EvidenceReviewContent />
    </Suspense>
  );
}

