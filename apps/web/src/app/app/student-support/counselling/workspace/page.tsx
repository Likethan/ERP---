"use client";

import React, { useState, useEffect } from "react";
import { StudentSupportService } from "@/services/student-support.service";
import {
  ConfidentialCounsellingRecordItem,
  CounsellingAppointmentItem,
} from "@/types/student-support";
import { StudentSupportNav } from "@/components/student-support/student-support-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import {
  Lock,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  FileText,
  AlertTriangle,
  History,
  EyeOff,
  UserCheck,
} from "lucide-react";

export default function RestrictedCounsellingWorkspacePage() {
  const [records, setRecords] = useState<ConfidentialCounsellingRecordItem[]>([]);
  const [appointments, setAppointments] = useState<CounsellingAppointmentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [permissionDenied, setPermissionDenied] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);

  // New Record Form State
  const [selectedApptId, setSelectedApptId] = useState("");
  const [clinicalNotes, setClinicalNotes] = useState("");
  const [interventions, setInterventions] = useState("");
  const [consentVerified, setConsentVerified] = useState(true);
  const [disclosePermittedSummary, setDisclosePermittedSummary] = useState(false);
  const [permittedSummary, setPermittedSummary] = useState("");
  const [followUpRecommended, setFollowUpRecommended] = useState(false);
  const [savingRecord, setSavingRecord] = useState(false);

  useEffect(() => {
    loadWorkspace();
  }, []);

  async function loadWorkspace() {
    setLoading(true);
    setPermissionDenied(false);
    try {
      const [allRecords, appts] = await Promise.all([
        StudentSupportService.getConfidentialRecords(),
        StudentSupportService.getCounsellingAppointments({ status: "COMPLETED" }),
      ]);
      setRecords(allRecords);
      setAppointments(appts);
      if (appts.length > 0) {
        setSelectedApptId(appts[0].id);
      }
    } catch (err: any) {
      console.error("Workspace access error:", err);
      if (err?.status === 403 || err?.message?.includes("403") || err?.message?.includes("Forbidden")) {
        setPermissionDenied(true);
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveClinicalRecord(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedApptId || !clinicalNotes.trim()) return;
    setSavingRecord(true);
    try {
      const selectedAppt = appointments.find((a) => a.id === selectedApptId);
      await StudentSupportService.createConfidentialRecord({
        appointment_id: selectedApptId,
        student_id: selectedAppt?.student_id ?? "student-record",
        session_observations: clinicalNotes,
        interventions_applied: interventions,
        consent_verified: consentVerified,
        disclose_to_student: disclosePermittedSummary,
        disclosed_summary: disclosePermittedSummary ? permittedSummary : undefined,
        follow_up_recommended: followUpRecommended,
      });

      setNotification("Confidential clinical session record sealed and encrypted in audit store.");
      setClinicalNotes("");
      setInterventions("");
      setPermittedSummary("");
      loadWorkspace();
    } catch (err) {
      console.error("Failed to save clinical record:", err);
      alert("Error sealing confidential record. Ensure you have COUNSELLING_CONFIDENTIAL_WRITE authorization.");
    } finally {
      setSavingRecord(false);
    }
  }

  if (permissionDenied) {
    return (
      <div className="space-y-6 pb-12">
        <Breadcrumbs
          items={[
            { label: "Dashboard", href: "/app/dashboard" },
            { label: "Student Support", href: "/app/student-support" },
            { label: "Restricted Workspace", href: "/app/student-support/counselling/workspace" },
          ]}
        />
        <StudentSupportNav />
        <Card className="border-amber-900/50 bg-amber-950/20 p-8 text-center max-w-xl mx-auto space-y-4">
          <ShieldAlert className="h-12 w-12 text-amber-400 mx-auto" />
          <h2 className="text-lg font-bold text-white">Confidential Clinical Boundary Enforced</h2>
          <p className="text-xs text-slate-300">
            Access to confidential counselling observations is strictly restricted to licensed counselling professionals and designated clinical staff. This record layer is isolated from institutional administration, HODs, faculty mentors, and academic transcripts.
          </p>
          <div className="pt-2">
            <Button
              onClick={() => window.history.back()}
              variant="outline"
              className="text-xs border-slate-700"
            >
              Return to Previous Screen
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      <div>
        <Breadcrumbs
          items={[
            { label: "Dashboard", href: "/app/dashboard" },
            { label: "Student Support", href: "/app/student-support" },
            { label: "Restricted Workspace", href: "/app/student-support/counselling/workspace" },
          ]}
        />
        <div className="mt-2 flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <Lock className="h-6 w-6 text-amber-400" />
              Restricted Counselling Clinical Workspace
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Protected clinical notes and observations. Strictly governed by professional counselling confidentiality protocols.
            </p>
          </div>
          <Badge variant="outline" className="border-amber-500/40 text-amber-400 bg-amber-500/10 text-xs px-3 py-1">
            <ShieldCheck className="mr-1.5 h-3.5 w-3.5" />
            End-to-End Audited Workspace
          </Badge>
        </div>
      </div>

      <StudentSupportNav />

      {/* Compliance Warning Banner */}
      <div className="rounded-xl border border-amber-900/50 bg-amber-950/30 p-4">
        <div className="flex items-start gap-3">
          <EyeOff className="h-5 w-5 text-amber-400 mt-0.5 shrink-0" />
          <div className="text-xs text-slate-300 space-y-1">
            <span className="font-semibold text-white">CampusOS Mental Health Confidentiality Standard:</span>
            <p>
              Under institutional privacy regulations, entries written in this workspace cannot be viewed by faculty mentors, academic departments, or senior leadership. Automated psychological diagnoses and automated risk algorithms are strictly prohibited.
            </p>
          </div>
        </div>
      </div>

      {notification && (
        <div className="rounded-lg border border-emerald-800/50 bg-emerald-950/30 p-3 text-xs text-emerald-300 flex items-center justify-between">
          <span className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            {notification}
          </span>
          <button onClick={() => setNotification(null)} className="text-emerald-400 hover:text-emerald-200">
            Dismiss
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Clinical Note Creator (Left 2 Columns) */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="border-slate-800 bg-slate-900/60 p-6 space-y-5">
            <div>
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <FileText className="h-4 w-4 text-indigo-400" />
                Record Clinical Observations
              </h2>
              <p className="text-xs text-slate-400">Document session interventions, coping strategies, and follow-up guidance</p>
            </div>

            <form onSubmit={handleSaveClinicalRecord} className="space-y-4 text-xs">
              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Associated Appointment *</label>
                {appointments.length > 0 ? (
                  <select
                    required
                    value={selectedApptId}
                    onChange={(e) => setSelectedApptId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-white"
                  >
                    {appointments.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.appointment_number || a.id} - {a.student_id || a.studentId} ({String(a.category).replace("_", " ")}) - {new Date(a.scheduled_start || a.appointmentDate || "").toLocaleDateString()}
                      </option>
                    ))}
                  </select>
                ) : (
                  <div className="p-3 bg-slate-950 border border-slate-800 rounded text-slate-400">
                    No completed appointments awaiting clinical notes.
                  </div>
                )}
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Session Observations & Progress *</label>
                <Textarea
                  required
                  placeholder="Record confidential practitioner observations, student affect, and session themes..."
                  value={clinicalNotes}
                  onChange={(e) => setClinicalNotes(e.target.value)}
                  className="bg-slate-950 border-slate-800 text-xs font-mono"
                  rows={4}
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Therapeutic Interventions Applied</label>
                <Textarea
                  placeholder="e.g. Cognitive reframing, sleep hygiene review, academic pacing schedule..."
                  value={interventions}
                  onChange={(e) => setInterventions(e.target.value)}
                  className="bg-slate-950 border-slate-800 text-xs"
                  rows={2}
                />
              </div>

              {/* Consent and Disclosure Toggles */}
              <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/60 space-y-3">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={consentVerified}
                    onChange={(e) => setConsentVerified(e.target.checked)}
                    className="rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-0"
                  />
                  <span className="text-slate-300">
                    Student informed consent and privacy parameters verified for this session
                  </span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={disclosePermittedSummary}
                    onChange={(e) => setDisclosePermittedSummary(e.target.checked)}
                    className="rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-0"
                  />
                  <span className="text-slate-300">
                    Provide privacy-safe takeaway summary to student (non-clinical)
                  </span>
                </label>

                {disclosePermittedSummary && (
                  <div className="pt-2">
                    <Textarea
                      placeholder="Enter student-facing non-clinical summary and action steps..."
                      value={permittedSummary}
                      onChange={(e) => setPermittedSummary(e.target.value)}
                      className="bg-slate-900 border-slate-700 text-xs"
                      rows={2}
                    />
                  </div>
                )}

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={followUpRecommended}
                    onChange={(e) => setFollowUpRecommended(e.target.checked)}
                    className="rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-0"
                  />
                  <span className="text-slate-300">
                    Recommend follow-up appointment within 14 calendar days
                  </span>
                </label>
              </div>

              <Button
                type="submit"
                disabled={savingRecord || !selectedApptId || !clinicalNotes.trim()}
                className="bg-amber-600 hover:bg-amber-700 text-xs text-white"
              >
                <Lock className="mr-1.5 h-3.5 w-3.5" />
                {savingRecord ? "Sealing Record..." : "Seal & Encrypt Clinical Record"}
              </Button>
            </form>
          </Card>
        </div>

        {/* Audit Log & Sealed Records List (Right 1 Column) */}
        <div className="space-y-6">
          <Card className="border-slate-800 bg-slate-900/60 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-white flex items-center gap-1.5">
                <History className="h-4 w-4 text-indigo-400" />
                Sealed Clinical History
              </h2>
              <span className="text-[11px] text-slate-500">{records.length} Records</span>
            </div>

            {loading ? (
              <div className="py-6 text-center text-xs text-slate-500">Loading audit log...</div>
            ) : records.length === 0 ? (
              <div className="py-6 text-center text-xs text-slate-500">No sealed records found in this vault.</div>
            ) : (
              <div className="space-y-3">
                {records.map((rec) => (
                  <div
                    key={rec.id}
                    className="p-3 rounded-lg border border-slate-800 bg-slate-950/60 space-y-2 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-200">Ref: {rec.id.slice(0, 8)}...</span>
                      <span className="text-[10px] text-emerald-400 bg-emerald-950/40 px-1.5 py-0.5 rounded border border-emerald-800/30">
                        Encrypted
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400">
                      <div>Student Ref: {rec.student_id || rec.studentId}</div>
                      <div>Sealed At: {new Date(rec.recorded_at || rec.createdAt || "").toLocaleDateString()}</div>
                      <div>Counsellor: {rec.counsellor_staff_id || rec.counsellorUserId}</div>
                    </div>
                    <div className="pt-1 text-[11px] text-slate-500 italic">
                      {rec.follow_up_recommended ? "• Follow-up flagged" : "• Routine completion"}
                      {rec.consent_verified && " • Consent logged"}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
