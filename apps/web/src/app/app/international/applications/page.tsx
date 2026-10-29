"use client";

import { useEffect, useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  BookOpen,
  Calendar,
  CheckCircle2,
  Clock,
  Compass,
  FileEdit,
  FileText,
  Filter,
  Globe,
  Plus,
  Search,
  ShieldCheck,
  User,
  X,
} from "lucide-react";
import { InternationalNav } from "@/components/international/international-nav";
import { internationalService } from "@/services/international.service";
import { MobilityApplication, MobilityProgram } from "@/types/international";

function ApplicationsContent() {
  const searchParams = useSearchParams();
  const preselectedProgramId = searchParams.get("program_id");

  const [applications, setApplications] = useState<MobilityApplication[]>([]);
  const [programs, setPrograms] = useState<MobilityProgram[]>([]);
  const [loading, setLoading] = useState(true);
  const [showApplyModal, setShowApplyModal] = useState(Boolean(preselectedProgramId));

  // Form State
  const [form, setForm] = useState({
    program_id: preselectedProgramId || "",
    statement_of_purpose: "",
    emergency_contact_name: "",
    emergency_contact_phone: "",
    emergency_contact_relationship: "Parent",
    proposed_courses_str: "CS501: Advanced Algorithms (4 Credits)\nCS520: Distributed Cloud Systems (4 Credits)",
    submit_now: true,
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [apps, progs] = await Promise.all([
        internationalService.getApplications(),
        internationalService.getPrograms({ open_only: true }),
      ]);
      setApplications(apps);
      setPrograms(progs);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleApply(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const courses = form.proposed_courses_str
        .split("\n")
        .filter((l) => l.trim())
        .map((l) => ({ code: l.split(":")[0]?.trim() || "CRS", title: l.trim(), credits: 4 }));

      const prog = programs.find((p) => p.id === form.program_id);

      const res = await internationalService.createApplication({
        program_id: form.program_id,
        statement_of_purpose: form.statement_of_purpose,
        emergency_contact_name: form.emergency_contact_name,
        emergency_contact_phone: form.emergency_contact_phone,
        emergency_contact_relationship: form.emergency_contact_relationship,
        proposed_courses: courses,
        program_title: prog?.program_title || prog?.title || "Exchange Program",
        partner_name: prog?.partner_name || prog?.partnerName || "Partner University",
        partner_country: prog?.partner_country || prog?.partnerCountry || "International",
      });

      setApplications([res, ...applications]);
      setShowApplyModal(false);
      alert("Application submitted successfully! It is now pending departmental review.");
    } catch (err) {
      console.error(err);
      alert("Failed to submit application");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <InternationalNav />

      <main className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <FileEdit className="h-5 w-5 text-cyan-400" />
              Student Mobility Applications
            </h2>
            <p className="text-xs text-slate-400">
              Track multi-stage application progression from Department Review to Partner Nomination
            </p>
          </div>
          <button
            onClick={() => setShowApplyModal(true)}
            className="px-3.5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md shadow-cyan-900/30 flex items-center gap-2 transition-all self-start sm:self-auto"
          >
            <Plus className="h-4 w-4" />
            New Mobility Application
          </button>
        </div>

        {/* Applications List */}
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-500">Loading student applications...</div>
        ) : applications.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500 bg-slate-900/40 rounded-xl border border-slate-800">
            No mobility applications found. Click &quot;New Mobility Application&quot; to apply.
          </div>
        ) : (
          <div className="space-y-4">
            {applications.map((app) => (
              <div
                key={app.id}
                className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-cyan-500/40 transition-all space-y-4"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold font-mono px-2 py-0.5 rounded bg-slate-800 text-cyan-400 border border-slate-700">
                        {app.application_reference_number || app.applicationReferenceNumber}
                      </span>
                      <span
                        className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase ${
                          app.status === "APPROVED" || app.status === "PARTNER_ACCEPTED" || app.status === "ACTIVE_MOBILITY"
                            ? "bg-emerald-500/10 text-emerald-300 border border-emerald-500/30"
                            : app.status === "ELIGIBILITY_REVIEW"
                            ? "bg-rose-500/10 text-rose-300 border border-rose-500/30"
                            : app.status === "PARTNER_NOMINATED"
                            ? "bg-purple-500/10 text-purple-300 border border-purple-500/30"
                            : "bg-cyan-500/10 text-cyan-300 border border-cyan-500/30"
                        }`}
                      >
                        {app.status}
                      </span>
                    </div>

                    <h3 className="text-base font-bold text-white mt-1.5">
                      {app.program_title || app.programTitle || "Mobility Program"}
                    </h3>

                    <p className="text-xs text-slate-400 flex items-center gap-2 mt-0.5">
                      <Globe className="h-3.5 w-3.5 text-cyan-400" />
                      <span>{app.partner_name || app.partnerName}</span>
                      {app.partner_country && <span>({app.partner_country})</span>}
                    </p>
                  </div>

                  <div className="text-right sm:self-start">
                    <span className="text-[11px] text-slate-500 block">Submitted At</span>
                    <span className="text-xs text-slate-300 font-mono">
                      {app.submitted_at ? new Date(app.submitted_at).toLocaleDateString() : "Draft"}
                    </span>
                  </div>
                </div>

                {/* Eligibility Flag Warning if failed */}
                {!app.eligibility_check_passed && (
                  <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-start gap-2.5 text-xs text-rose-300">
                    <AlertTriangle className="h-4 w-4 text-rose-400 mt-0.5 shrink-0" />
                    <div>
                      <span className="font-semibold block">Automatic Eligibility Flag Raised:</span>
                      <p className="mt-0.5 text-rose-300/80">
                        {app.eligibility_check_details?.cgpa_error ||
                          "Student CGPA or credit prerequisites were not satisfied. Application held for Dean Committee waiver."}
                      </p>
                    </div>
                  </div>
                )}

                {/* Workflow Stepper Bar */}
                <div className="pt-2">
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-center text-[10px]">
                    <div className="p-2 rounded bg-slate-950 border border-emerald-500/30 text-emerald-300 font-medium">
                      ✓ 1. Submitted
                    </div>
                    <div
                      className={`p-2 rounded border ${
                        app.status === "DEPARTMENT_REVIEW"
                          ? "bg-cyan-950 border-cyan-500/50 text-cyan-300 font-bold"
                          : ["INTERNATIONAL_OFFICE_REVIEW", "APPROVED", "PARTNER_NOMINATED", "PARTNER_ACCEPTED", "ACTIVE_MOBILITY"].includes(app.status)
                          ? "bg-slate-950 border-emerald-500/30 text-emerald-300"
                          : "bg-slate-950 border-slate-800 text-slate-500"
                      }`}
                    >
                      2. Dept Review
                    </div>
                    <div
                      className={`p-2 rounded border ${
                        app.status === "INTERNATIONAL_OFFICE_REVIEW"
                          ? "bg-cyan-950 border-cyan-500/50 text-cyan-300 font-bold"
                          : ["APPROVED", "PARTNER_NOMINATED", "PARTNER_ACCEPTED", "ACTIVE_MOBILITY"].includes(app.status)
                          ? "bg-slate-950 border-emerald-500/30 text-emerald-300"
                          : "bg-slate-950 border-slate-800 text-slate-500"
                      }`}
                    >
                      3. Intl Office
                    </div>
                    <div
                      className={`p-2 rounded border ${
                        app.status === "PARTNER_NOMINATED"
                          ? "bg-purple-950 border-purple-500/50 text-purple-300 font-bold"
                          : ["PARTNER_ACCEPTED", "ACTIVE_MOBILITY"].includes(app.status)
                          ? "bg-slate-950 border-emerald-500/30 text-emerald-300"
                          : "bg-slate-950 border-slate-800 text-slate-500"
                      }`}
                    >
                      4. Partner Nomination
                    </div>
                    <div
                      className={`p-2 rounded border ${
                        ["PARTNER_ACCEPTED", "ACTIVE_MOBILITY"].includes(app.status)
                          ? "bg-emerald-950 border-emerald-500 text-emerald-300 font-bold"
                          : "bg-slate-950 border-slate-800 text-slate-500"
                      }`}
                    >
                      5. Mobility Active
                    </div>
                  </div>
                </div>

                {/* SOP and Proposed Courses Preview */}
                <div className="pt-2 border-t border-slate-800/80 flex flex-col md:flex-row gap-4 text-xs">
                  <div className="flex-1">
                    <span className="text-slate-500 block mb-1">Statement of Purpose:</span>
                    <p className="text-slate-300 line-clamp-2 italic bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
                      &quot;{app.statement_of_purpose || app.statementOfPurpose}&quot;
                    </p>
                  </div>
                  <div className="w-full md:w-72">
                    <span className="text-slate-500 block mb-1">Proposed Course Load:</span>
                    <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800 space-y-1">
                      {app.proposed_courses && app.proposed_courses.length > 0 ? (
                        app.proposed_courses.map((c, i) => (
                          <div key={i} className="flex justify-between text-slate-300 text-[11px]">
                            <span>{c.code || c.title}</span>
                            <span className="text-slate-500">{c.credits} Cr</span>
                          </div>
                        ))
                      ) : (
                        <span className="text-slate-500 text-[11px]">Standard curriculum</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* New Application Modal */}
        {showApplyModal && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 shadow-2xl relative max-h-[90vh] overflow-y-auto">
              <button
                onClick={() => setShowApplyModal(false)}
                className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>

              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Compass className="h-4 w-4 text-cyan-400" />
                Submit Mobility Program Application
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Your CGPA and credit records will be automatically evaluated against host university prerequisites
              </p>

              <form onSubmit={handleApply} className="mt-5 space-y-4">
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Target Exchange Program *</label>
                  <select
                    required
                    value={form.program_id}
                    onChange={(e) => setForm({ ...form, program_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="">Select published mobility program...</option>
                    {programs.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.program_title || p.title} — {p.partner_name || p.partnerName} ({p.term_type || p.termType})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">
                    Statement of Academic Purpose (Min. 30 words) *
                  </label>
                  <textarea
                    required
                    rows={4}
                    placeholder="Describe your academic rationale, research interests, and career objectives for studying at this host university..."
                    value={form.statement_of_purpose}
                    onChange={(e) => setForm({ ...form, statement_of_purpose: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">
                    Proposed Host Courses & Credits (One per line)
                  </label>
                  <textarea
                    rows={3}
                    placeholder="e.g. IN2106: Advanced Computer Architecture (6 Credits)&#10;IN2041: Cloud Information Systems (5 Credits)"
                    value={form.proposed_courses_str}
                    onChange={(e) => setForm({ ...form, proposed_courses_str: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500 font-mono text-[11px]"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Emergency Contact Name *</label>
                    <input
                      required
                      type="text"
                      placeholder="e.g. Ramesh Kumar"
                      value={form.emergency_contact_name}
                      onChange={(e) => setForm({ ...form, emergency_contact_name: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Emergency Phone *</label>
                    <input
                      required
                      type="text"
                      placeholder="+91 9876543210"
                      value={form.emergency_contact_phone}
                      onChange={(e) => setForm({ ...form, emergency_contact_phone: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Relationship</label>
                    <select
                      value={form.emergency_contact_relationship}
                      onChange={(e) => setForm({ ...form, emergency_contact_relationship: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    >
                      <option value="Parent">Parent / Guardian</option>
                      <option value="Spouse">Spouse</option>
                      <option value="Sibling">Sibling</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>
                </div>

                <div className="mt-6 flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setShowApplyModal(false)}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md shadow-cyan-900/30 disabled:opacity-50"
                  >
                    {submitting ? "Submitting..." : "Submit Application"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default function ApplicationsPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-slate-500">Loading applications...</div>}>
      <ApplicationsContent />
    </Suspense>
  );
}

