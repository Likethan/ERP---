"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  Calendar,
  CheckCircle2,
  Compass,
  FileCheck2,
  Globe,
  MapPin,
  Plane,
  Search,
  ShieldCheck,
  User,
  X,
} from "lucide-react";
import { InternationalNav } from "@/components/international/international-nav";
import { internationalService } from "@/services/international.service";
import { MobilityApplication } from "@/types/international";

export default function OutboundTrackingPage() {
  const [applications, setApplications] = useState<MobilityApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedAppForPreDeparture, setSelectedAppForPreDeparture] = useState<MobilityApplication | null>(null);

  // Pre-departure form
  const [visaRef, setVisaRef] = useState("");
  const [insuranceNumber, setInsuranceNumber] = useState("");
  const [checklist, setChecklist] = useState({
    medical_clearance: true,
    housing_secured: true,
    learning_agreement_signed: true,
    emergency_briefing_attended: true,
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const data = await internationalService.getApplications();
      // Outbound students accepted or actively in mobility
      setApplications(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handlePreDepartureSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedAppForPreDeparture) return;
    setSubmitting(true);
    try {
      await internationalService.updatePreDeparture(
        selectedAppForPreDeparture.id,
        checklist,
        visaRef,
        insuranceNumber
      );
      alert("Pre-departure checklist committed! Status transitioned to Active Mobility.");
      setSelectedAppForPreDeparture(null);
      loadData();
    } catch (err) {
      console.error(err);
      alert("Failed to update pre-departure record");
    } finally {
      setSubmitting(false);
    }
  }

  const filtered = applications.filter((a) => {
    const text = `${a.student_name || ""} ${a.program_title || ""} ${a.partner_name || ""}`.toLowerCase();
    return text.includes(search.toLowerCase());
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <InternationalNav />

      <main className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <MapPin className="h-5 w-5 text-emerald-400" />
              Outbound Student Mobility & Pre-Departure Tracking
            </h2>
            <p className="text-xs text-slate-400">
              Manage international visas, health coverage, pre-departure clearances, and overseas student safety
            </p>
          </div>
        </div>

        {/* Search Toolbar */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="relative w-full">
            <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search outbound student by name, destination country, or program..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>
        </div>

        {/* Outbound Students Table */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider text-[10px] border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Student Scholar</th>
                  <th className="py-3 px-4">Host Institution & Country</th>
                  <th className="py-3 px-4">Program Track</th>
                  <th className="py-3 px-4">Mobility Stage</th>
                  <th className="py-3 px-4">Pre-Departure Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-500">
                      Loading outbound student records...
                    </td>
                  </tr>
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-500">
                      No outbound mobility students found.
                    </td>
                  </tr>
                ) : (
                  filtered.map((app) => (
                    <tr key={app.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-white">
                          {app.student_name || app.studentName || "Student Scholar"}
                        </div>
                        <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                          {app.student_roll_number || app.application_reference_number}
                        </div>
                      </td>

                      <td className="py-3.5 px-4 font-medium text-slate-200">
                        <div>{app.partner_name || app.partnerName}</div>
                        <div className="text-[11px] text-cyan-400">{app.partner_country || "International"}</div>
                      </td>

                      <td className="py-3.5 px-4 text-slate-300">
                        {app.program_title || app.programTitle}
                      </td>

                      <td className="py-3.5 px-4">
                        <span
                          className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase ${
                            app.status === "ACTIVE_MOBILITY"
                              ? "bg-emerald-500/10 text-emerald-300 border border-emerald-500/30"
                              : "bg-cyan-500/10 text-cyan-300 border border-cyan-500/30"
                          }`}
                        >
                          {app.status}
                        </span>
                      </td>

                      <td className="py-3.5 px-4">
                        {app.status === "ACTIVE_MOBILITY" ? (
                          <span className="text-emerald-400 font-medium flex items-center gap-1 text-xs">
                            <CheckCircle2 className="h-3.5 w-3.5" />
                            Cleared & Departed
                          </span>
                        ) : (
                          <span className="text-amber-400/90 font-medium text-xs">
                            Checklist Pending
                          </span>
                        )}
                      </td>

                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={() => {
                            setSelectedAppForPreDeparture(app);
                            setVisaRef(app.pre_departure_checklist?.visa_reference_number || "");
                            setInsuranceNumber(app.pre_departure_checklist?.insurance_policy_number || "");
                          }}
                          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs font-medium transition-colors"
                        >
                          Checklist & Clearance
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pre-Departure Checklist Modal */}
        {selectedAppForPreDeparture && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
              <button
                onClick={() => setSelectedAppForPreDeparture(null)}
                className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>

              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Plane className="h-4 w-4 text-emerald-400" />
                Pre-Departure Checklist & Travel Clearance
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Verify mandatory travel documents, health insurance, and emergency contacts before departure
              </p>

              <form onSubmit={handlePreDepartureSubmit} className="mt-5 space-y-4">
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">
                    Student Visa Reference Number *
                  </label>
                  <input
                    required
                    type="text"
                    placeholder="e.g. DE-STUDENT-VISA-2026-991"
                    value={visaRef}
                    onChange={(e) => setVisaRef(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">
                    International Health Insurance Policy Number *
                  </label>
                  <input
                    required
                    type="text"
                    placeholder="e.g. BUPA-GLOBAL-INTL-441829"
                    value={insuranceNumber}
                    onChange={(e) => setInsuranceNumber(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-2 text-xs text-slate-300">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={checklist.medical_clearance}
                      onChange={(e) => setChecklist({ ...checklist, medical_clearance: e.target.checked })}
                      className="rounded text-emerald-500"
                    />
                    <span>Medical and vaccination clearance verified</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={checklist.housing_secured}
                      onChange={(e) => setChecklist({ ...checklist, housing_secured: e.target.checked })}
                      className="rounded text-emerald-500"
                    />
                    <span>Overseas accommodation / campus dorm confirmed</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={checklist.learning_agreement_signed}
                      onChange={(e) => setChecklist({ ...checklist, learning_agreement_signed: e.target.checked })}
                      className="rounded text-emerald-500"
                    />
                    <span>Learning Agreement approved by Academic Council</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={checklist.emergency_briefing_attended}
                      onChange={(e) => setChecklist({ ...checklist, emergency_briefing_attended: e.target.checked })}
                      className="rounded text-emerald-500"
                    />
                    <span>Pre-departure international orientation attended</span>
                  </label>
                </div>

                <div className="mt-6 flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setSelectedAppForPreDeparture(null)}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-900/30 disabled:opacity-50"
                  >
                    {submitting ? "Saving..." : "Commit Clearance & Activate"}
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
