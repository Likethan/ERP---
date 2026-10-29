"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { studentAffairsService } from "@/services/student-affairs.service";
import {
  GrievanceCategoryModel,
  GrievanceSubmissionForm,
  SAConfidentialityLevel,
  SASubmitterType,
} from "@/types/student-affairs";
import { StudentAffairsNav } from "@/components/student-affairs/student-affairs-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  FileEdit,
  ShieldCheck,
  AlertCircle,
  Paperclip,
  CheckCircle2,
  Lock,
  EyeOff,
  Send,
  ArrowLeft,
} from "lucide-react";

export default function SubmitGrievancePage() {
  const router = useRouter();
  const [categories, setCategories] = useState<GrievanceCategoryModel[]>([]);
  const [loading, setLoading] = useState(false);
  const [successCase, setSuccessCase] = useState<{
    caseNumber: string;
    targetResponse: string;
    isAnonymous: boolean;
  } | null>(null);

  const [form, setForm] = useState<GrievanceSubmissionForm>({
    categoryId: "",
    title: "",
    description: "",
    requestedResolution: "",
    campusId: "camp-001",
    isAnonymous: false,
    submitterType: SASubmitterType.STUDENT,
    confidentialityLevel: SAConfidentialityLevel.STANDARD,
    supportingDocuments: [],
  });

  const [docTitle, setDocTitle] = useState("");
  const [docUrl, setDocUrl] = useState("");

  useEffect(() => {
    async function init() {
      const cats = await studentAffairsService.getCategories();
      setCategories(cats);
      if (cats.length > 0) {
        setForm((prev) => ({ ...prev, categoryId: cats[0].id }));
      }
    }
    init();
  }, []);

  function handleAddDocument() {
    if (!docTitle) return;
    const newDoc = {
      title: docTitle,
      fileUrl: docUrl || `/storage/grievances/evidence_${Date.now()}.pdf`,
      fileSizeBytes: 1048576,
    };
    setForm((prev) => ({
      ...prev,
      supportingDocuments: [...(prev.supportingDocuments || []), newDoc],
    }));
    setDocTitle("");
    setDocUrl("");
  }

  function handleRemoveDoc(index: number) {
    setForm((prev) => ({
      ...prev,
      supportingDocuments: (prev.supportingDocuments || []).filter((_, i) => i !== index),
    }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.title || !form.description || !form.categoryId) {
      alert("Please fill out the required fields: Category, Title, and Detailed Description.");
      return;
    }

    setLoading(true);
    try {
      const created = await studentAffairsService.submitCase(form);
      setSuccessCase({
        caseNumber: created.case_number,
        targetResponse: created.target_response_date || "Within 48 hours",
        isAnonymous: created.is_anonymous,
      });
    } catch {
      alert("Submission error. Please verify input data.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <Breadcrumbs
        items={[
          { label: "Dashboard", href: "/app/dashboard" },
          { label: "Student Affairs", href: "/app/student-affairs" },
          { label: "Submit Grievance", href: "/app/student-affairs/submit" },
        ]}
      />

      <div className="border-b border-slate-800 pb-5">
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
          <FileEdit className="h-6 w-6 text-indigo-400" />
          Institutional Grievance & Incident Submission
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Submit formal grievances, service complaints, or confidential incident notifications with institutional procedural fairness.
        </p>
      </div>

      <StudentAffairsNav />

      {successCase ? (
        <Card className="p-8 border-emerald-500/30 bg-emerald-950/10 text-center space-y-5">
          <div className="mx-auto w-14 h-14 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
            <CheckCircle2 className="h-8 w-8" />
          </div>
          <div className="space-y-1">
            <h2 className="text-xl font-bold text-white">Grievance Successfully Registered</h2>
            <p className="text-sm text-slate-300">
              Your case has been securely recorded and assigned a unique institutional tracking identifier.
            </p>
          </div>

          <div className="max-w-md mx-auto p-4 rounded-xl border border-slate-800 bg-slate-900/60 text-left space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Tracking Reference:</span>
              <span className="font-mono font-bold text-indigo-400">{successCase.caseNumber}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Confidentiality Tier:</span>
              <span className="text-slate-200">
                {successCase.isAnonymous ? "Anonymous (Protected Identity)" : "Authenticated Submitter"}
              </span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">SLA Response Window:</span>
              <span className="text-emerald-400 font-medium">Within 24-48 Business Hours</span>
            </div>
          </div>

          <div className="flex justify-center gap-3 pt-2">
            <Link href="/app/student-affairs/my-cases">
              <Button className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs">
                View in My Cases
              </Button>
            </Link>
            <Button
              variant="outline"
              onClick={() => {
                setSuccessCase(null);
                setForm({
                  categoryId: categories[0]?.id || "",
                  title: "",
                  description: "",
                  requestedResolution: "",
                  campusId: "camp-001",
                  isAnonymous: false,
                  submitterType: SASubmitterType.STUDENT,
                  confidentialityLevel: SAConfidentialityLevel.STANDARD,
                  supportingDocuments: [],
                });
              }}
              className="border-slate-700 text-slate-300 text-xs"
            >
              Submit Another Case
            </Button>
          </div>
        </Card>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Institutional Safeguards Info Callout */}
          <div className="p-4 rounded-xl border border-indigo-500/20 bg-indigo-950/20 text-xs text-slate-300 space-y-2">
            <div className="flex items-center gap-2 font-semibold text-indigo-300">
              <ShieldCheck className="h-4 w-4" />
              Statutory Fairness & Non-Retaliation Assurance
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              CampusOS enforces strict protection against adverse retaliatory actions for bona fide grievance submissions.
              Submissions undergo intake triage by designated Case Officers under published UGC / Institute standards.
            </p>
          </div>

          {/* Core Case Information Card */}
          <Card className="p-6 border-slate-800 bg-slate-900/40 space-y-5">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              1. Grievance Classification
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Institutional Category <span className="text-rose-400">*</span>
                </label>
                <select
                  value={form.categoryId}
                  onChange={(e) => setForm({ ...form, categoryId: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  required
                >
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name} ({cat.case_type})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Campus Location
                </label>
                <select
                  value={form.campusId}
                  onChange={(e) => setForm({ ...form, campusId: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="camp-001">Main Technological Campus (Bangalore)</option>
                  <option value="camp-002">South Satellite Campus (Electronic City)</option>
                </select>
              </div>
            </div>

            <div className="border-t border-slate-800/80 pt-5 space-y-4">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
                2. Summary & Narrative
              </h2>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Concise Case Title <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  placeholder="e.g. Inoperative HVAC in Block D Thermodynamics Lab Room 304"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Detailed Grievance Narrative <span className="text-rose-400">*</span>
                </label>
                <textarea
                  rows={5}
                  placeholder="State the chronology of events, specific dates, affected parties, and procedural impacts..."
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Requested Remediation / Desired Resolution
                </label>
                <textarea
                  rows={2}
                  placeholder="What specific remedy, adjustment, repair, or policy clarification are you seeking?"
                  value={form.requestedResolution}
                  onChange={(e) => setForm({ ...form, requestedResolution: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            {/* Confidentiality & Anonymity Section */}
            <div className="border-t border-slate-800/80 pt-5 space-y-4">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Lock className="h-4 w-4 text-amber-400" />
                3. Privacy & Submitter Protection
              </h2>

              <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <label className="text-xs font-medium text-white flex items-center gap-2">
                      <EyeOff className="h-3.5 w-3.5 text-indigo-400" />
                      Anonymous Submission Mode
                    </label>
                    <p className="text-[11px] text-slate-400">
                      Omits your student profile and name from initial case distribution logs.
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={form.isAnonymous}
                    onChange={(e) => setForm({ ...form, isAnonymous: e.target.checked })}
                    className="w-4 h-4 rounded text-indigo-600 bg-slate-900 border-slate-700"
                  />
                </div>

                {form.isAnonymous && (
                  <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-300">
                    <strong>Notice on Anonymity:</strong> Anonymous submissions protect identity, but may limit the Committee&apos;s ability to seek clarification or provide personalized restitution where direct contact is required.
                  </div>
                )}

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">
                    Case Confidentiality Classification
                  </label>
                  <select
                    value={form.confidentialityLevel}
                    onChange={(e) => setForm({ ...form, confidentialityLevel: e.target.value as SAConfidentialityLevel })}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value={SAConfidentialityLevel.STANDARD}>STANDARD - General Operational Disciplinary Review</option>
                    <option value={SAConfidentialityLevel.CONFIDENTIAL}>CONFIDENTIAL - Restricted to Authorized Case Officers & Panel</option>
                    <option value={SAConfidentialityLevel.RESTRICTED}>RESTRICTED - High-Sensitivity Safeguarding / Anti-Harassment</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Supporting Evidence References */}
            <div className="border-t border-slate-800/80 pt-5 space-y-4">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Paperclip className="h-4 w-4 text-blue-400" />
                4. Supporting Documents & Evidence (Optional)
              </h2>

              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Document description (e.g. Sensor log screenshot, email thread)"
                  value={docTitle}
                  onChange={(e) => setDocTitle(e.target.value)}
                  className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleAddDocument}
                  className="border-slate-700 text-slate-200 text-xs"
                >
                  Add Attachment
                </Button>
              </div>

              {form.supportingDocuments && form.supportingDocuments.length > 0 && (
                <div className="space-y-2">
                  {form.supportingDocuments.map((doc, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-2.5 rounded-lg border border-slate-800 bg-slate-950/40 text-xs"
                    >
                      <div className="flex items-center gap-2 text-slate-300">
                        <Paperclip className="h-3.5 w-3.5 text-indigo-400" />
                        <span>{doc.title}</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleRemoveDoc(idx)}
                        className="text-slate-500 hover:text-red-400 text-xs"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Card>

          {/* Action Row */}
          <div className="flex items-center justify-between">
            <Link href="/app/student-affairs">
              <Button type="button" variant="ghost" className="text-slate-400 hover:text-slate-200 text-xs gap-1.5">
                <ArrowLeft className="h-4 w-4" />
                Cancel
              </Button>
            </Link>
            <Button
              type="submit"
              disabled={loading}
              className="bg-indigo-600 hover:bg-indigo-500 text-white gap-2 text-xs font-semibold px-6 shadow-lg shadow-indigo-600/20"
            >
              <Send className="h-4 w-4" />
              {loading ? "Recording Case..." : "Register Formal Grievance"}
            </Button>
          </div>
        </form>
      )}
    </div>
  );
}
