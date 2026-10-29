"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Building2,
  Calendar,
  CheckCircle2,
  Compass,
  DoorOpen,
  Mail,
  MapPin,
  Plus,
  Search,
  ShieldCheck,
  User,
  UserCheck,
  X,
} from "lucide-react";
import { InternationalNav } from "@/components/international/international-nav";
import { internationalService } from "@/services/international.service";
import { InboundStudentProfile, InternationalPartner } from "@/types/international";

export default function InboundStudentsPage() {
  const [students, setStudents] = useState<InboundStudentProfile[]>([]);
  const [partners, setPartners] = useState<InternationalPartner[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedStudentForCheckin, setSelectedStudentForCheckin] = useState<InboundStudentProfile | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);

  // New Inbound Student Form
  const [newForm, setNewForm] = useState({
    partner_id: "",
    first_name: "",
    last_name: "",
    email: "",
    home_institution_student_id: "",
    host_department_id: "dept-cse",
    study_period_start: new Date().toISOString().split("T")[0],
    study_period_end: new Date(Date.now() + 120 * 86400000).toISOString().split("T")[0],
    passport_number: "",
    visa_reference_number: "",
  });
  const [submittingNew, setSubmittingNew] = useState(false);

  // Checkin Form
  const [checkinNotes, setCheckinNotes] = useState("");
  const [submittingCheckin, setSubmittingCheckin] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [stus, pts] = await Promise.all([
        internationalService.getInboundStudents(),
        internationalService.getPartners(),
      ]);
      setStudents(stus);
      setPartners(pts);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleAddStudent(e: React.FormEvent) {
    e.preventDefault();
    setSubmittingNew(true);
    try {
      const partner = partners.find((p) => p.id === newForm.partner_id);
      const res = await internationalService.createInboundStudent({
        ...newForm,
        partner_name: partner?.partner_name || partner?.name || "Partner University",
      });
      setStudents([res, ...students]);
      setShowAddModal(false);
      alert("Inbound exchange student registered successfully!");
    } catch (err) {
      console.error(err);
      alert("Failed to register student");
    } finally {
      setSubmittingNew(false);
    }
  }

  async function handleCheckin(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedStudentForCheckin) return;
    setSubmittingCheckin(true);
    try {
      await internationalService.checkinInboundStudent(selectedStudentForCheckin.id, checkinNotes);
      alert("Orientation check-in completed! Status updated to Orientation Completed.");
      setSelectedStudentForCheckin(null);
      setCheckinNotes("");
      loadData();
    } catch (err) {
      console.error(err);
      alert("Failed to complete check-in");
    } finally {
      setSubmittingCheckin(false);
    }
  }

  const filtered = students.filter((s) => {
    const text = `${s.first_name} ${s.last_name} ${s.email} ${s.partner_name || ""}`.toLowerCase();
    return text.includes(search.toLowerCase());
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <InternationalNav />

      <main className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <DoorOpen className="h-5 w-5 text-purple-400" />
              Inbound International Scholars & Exchange Students
            </h2>
            <p className="text-xs text-slate-400">
              Arrival coordination, institutional onboarding, campus housing, and mandatory orientation check-in
            </p>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-3.5 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md shadow-purple-900/30 flex items-center gap-2 transition-all self-start sm:self-auto"
          >
            <Plus className="h-4 w-4" />
            Register Inbound Scholar
          </button>
        </div>

        {/* Search Toolbar */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="relative w-full">
            <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search inbound scholar by name, email, or sending institution..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>
        </div>

        {/* Inbound Students Cards */}
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-500">Loading inbound student roster...</div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500 bg-slate-900/40 rounded-xl border border-slate-800">
            No inbound international scholars found.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filtered.map((s) => (
              <div
                key={s.id}
                className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-purple-500/40 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/20">
                      ID: {s.home_institution_student_id}
                    </span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-semibold uppercase ${
                        s.orientation_completed
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-amber-500/10 text-amber-300 border border-amber-500/20"
                      }`}
                    >
                      {s.orientation_completed ? "Orientation Complete" : s.check_in_status}
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-white mt-3">
                    {s.first_name} {s.last_name}
                  </h3>

                  <p className="text-xs text-slate-400 mt-1 flex items-center gap-1.5">
                    <Building2 className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
                    <span>{s.partner_name || "Sending University"}</span>
                  </p>

                  <div className="mt-4 pt-3 border-t border-slate-800/80 space-y-1.5 text-xs text-slate-300">
                    <p className="flex items-center justify-between">
                      <span className="text-slate-500">Host Department:</span>
                      <span className="text-slate-200">{s.host_department_name || "Computer Science"}</span>
                    </p>
                    <p className="flex items-center justify-between">
                      <span className="text-slate-500">Assigned Mentor:</span>
                      <span className="text-slate-200">{s.assigned_mentor_name || "Faculty Coordinator"}</span>
                    </p>
                    <p className="flex items-center justify-between">
                      <span className="text-slate-500">Exchange Period:</span>
                      <span className="text-slate-400 text-[11px]">
                        {s.study_period_start} to {s.study_period_end}
                      </span>
                    </p>
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-slate-800 flex items-center justify-between">
                  <span className="text-xs text-slate-400 truncate max-w-[150px]">{s.email}</span>
                  {!s.orientation_completed ? (
                    <button
                      onClick={() => setSelectedStudentForCheckin(s)}
                      className="px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-sm transition-colors"
                    >
                      Check-in / Orient
                    </button>
                  ) : (
                    <span className="text-xs text-emerald-400 font-medium flex items-center gap-1">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      Active Student
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Orientation Check-in Modal */}
        {selectedStudentForCheckin && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl relative">
              <button
                onClick={() => setSelectedStudentForCheckin(null)}
                className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>

              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-purple-400" />
                Conduct Campus Orientation Check-In
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Scholar:{" "}
                <strong className="text-slate-200">
                  {selectedStudentForCheckin.first_name} {selectedStudentForCheckin.last_name}
                </strong>{" "}
                from {selectedStudentForCheckin.partner_name}
              </p>

              <form onSubmit={handleCheckin} className="mt-5 space-y-4">
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-2 text-xs text-slate-300">
                  <div className="flex items-center gap-2">
                    <input type="checkbox" defaultChecked disabled className="rounded text-cyan-500" />
                    <span>Passport & Visa validity verified</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" defaultChecked disabled className="rounded text-cyan-500" />
                    <span>Campus ID Card & Security Access badge activated</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" defaultChecked disabled className="rounded text-cyan-500" />
                    <span>Host Department faculty mentor introduced</span>
                  </div>
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Orientation Notes / Housing Reference</label>
                  <textarea
                    rows={3}
                    placeholder="e.g. Assigned to International Hostel Wing B, Room 204. Lab safety induction completed."
                    value={checkinNotes}
                    onChange={(e) => setCheckinNotes(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div className="mt-6 flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setSelectedStudentForCheckin(null)}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submittingCheckin}
                    className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md shadow-purple-900/30 disabled:opacity-50"
                  >
                    {submittingCheckin ? "Confirming..." : "Confirm Orientation Complete"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Register Inbound Student Modal */}
        {showAddModal && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 shadow-2xl relative max-h-[90vh] overflow-y-auto">
              <button
                onClick={() => setShowAddModal(false)}
                className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>

              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <DoorOpen className="h-4 w-4 text-purple-400" />
                Register Incoming Exchange Scholar
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Create an inbound foreign student record to enable campus access, course registration, and orientation
              </p>

              <form onSubmit={handleAddStudent} className="mt-5 space-y-4">
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Sending Partner Institution *</label>
                  <select
                    required
                    value={newForm.partner_id}
                    onChange={(e) => setNewForm({ ...newForm, partner_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="">Select sending foreign university...</option>
                    {partners.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.partner_name || p.name} ({p.country_name || p.country || p.country_code})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">First Name *</label>
                    <input
                      required
                      type="text"
                      placeholder="e.g. Lukas"
                      value={newForm.first_name}
                      onChange={(e) => setNewForm({ ...newForm, first_name: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Last Name *</label>
                    <input
                      required
                      type="text"
                      placeholder="e.g. Mueller"
                      value={newForm.last_name}
                      onChange={(e) => setNewForm({ ...newForm, last_name: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Email Address *</label>
                    <input
                      required
                      type="email"
                      placeholder="lukas.mueller@tum.de"
                      value={newForm.email}
                      onChange={(e) => setNewForm({ ...newForm, email: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Home Institution Student ID *</label>
                    <input
                      required
                      type="text"
                      placeholder="e.g. TUM-039129"
                      value={newForm.home_institution_student_id}
                      onChange={(e) => setNewForm({ ...newForm, home_institution_student_id: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Study Period Start *</label>
                    <input
                      required
                      type="date"
                      value={newForm.study_period_start}
                      onChange={(e) => setNewForm({ ...newForm, study_period_start: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Study Period End *</label>
                    <input
                      required
                      type="date"
                      value={newForm.study_period_end}
                      onChange={(e) => setNewForm({ ...newForm, study_period_end: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                </div>

                <div className="mt-6 flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submittingNew}
                    className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md shadow-purple-900/30 disabled:opacity-50"
                  >
                    {submittingNew ? "Registering..." : "Register Scholar"}
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
