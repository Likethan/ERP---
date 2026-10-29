"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Calendar,
  CheckCircle2,
  Clock,
  Compass,
  Filter,
  Globe,
  GraduationCap,
  Plus,
  Search,
  Sparkles,
  Users,
  X,
} from "lucide-react";
import { InternationalNav } from "@/components/international/international-nav";
import { internationalService } from "@/services/international.service";
import { InternationalPartner, MobilityProgram, MobilityProgramType, MobilityTermType } from "@/types/international";

export default function ProgramsPage() {
  const [programs, setPrograms] = useState<MobilityProgram[]>([]);
  const [partners, setPartners] = useState<InternationalPartner[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [termFilter, setTermFilter] = useState("ALL");
  const [showCreateModal, setShowCreateModal] = useState(false);

  // New Program Form
  const [form, setForm] = useState({
    partner_id: "",
    program_title: "",
    program_type: "SEMESTER_EXCHANGE" as MobilityProgramType,
    term_type: "FALL_SEMESTER" as MobilityTermType,
    academic_year: "2026-2027",
    total_seats: 5,
    min_cgpa_requirement: 7.5,
    min_credits_completed: 40,
    application_start_date: new Date().toISOString().split("T")[0],
    application_deadline: new Date(Date.now() + 60 * 86400000).toISOString().split("T")[0],
    expected_start_date: new Date(Date.now() + 180 * 86400000).toISOString().split("T")[0],
    expected_end_date: new Date(Date.now() + 360 * 86400000).toISOString().split("T")[0],
    is_published: true,
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadPrograms();
  }, []);

  async function loadPrograms() {
    setLoading(true);
    try {
      const [progs, pts] = await Promise.all([
        internationalService.getPrograms(),
        internationalService.getPartners(),
      ]);
      setPrograms(progs);
      setPartners(pts);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateProgram(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const partner = partners.find((p) => p.id === form.partner_id);
      const res = await internationalService.createProgram({
        ...form,
        partner_name: partner?.partner_name || partner?.name || "Partner",
        partner_country: partner?.country_name || partner?.country || "International",
      });
      setPrograms([res, ...programs]);
      setShowCreateModal(false);
    } catch (err) {
      console.error(err);
      alert("Failed to publish program");
    } finally {
      setSubmitting(false);
    }
  }

  const filtered = programs.filter((p) => {
    const text = `${p.program_title || p.title} ${p.program_code || p.programCode} ${p.partner_name || ""}`.toLowerCase();
    const matchesSearch = text.includes(search.toLowerCase());
    const matchesTerm = termFilter === "ALL" || (p.term_type || p.termType) === termFilter;
    return matchesSearch && matchesTerm;
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <InternationalNav />

      <main className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <Compass className="h-5 w-5 text-cyan-400" />
              Published Mobility Programs & Exchange Tracks
            </h2>
            <p className="text-xs text-slate-400">
              Browse bilateral student exchange, summer research fellowships, and global articulation programs
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-3.5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md shadow-cyan-900/30 flex items-center gap-2 transition-all self-start sm:self-auto"
          >
            <Plus className="h-4 w-4" />
            Publish Mobility Program
          </button>
        </div>

        {/* Filters */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col md:flex-row items-center gap-4">
          <div className="relative flex-1 w-full">
            <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search by program title, code, or host university..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <select
            value={termFilter}
            onChange={(e) => setTermFilter(e.target.value)}
            className="px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-cyan-500 w-full md:w-auto"
          >
            <option value="ALL">All Academic Terms</option>
            <option value="FALL_SEMESTER">Fall Semester</option>
            <option value="SPRING_SEMESTER">Spring Semester</option>
            <option value="FULL_ACADEMIC_YEAR">Full Academic Year</option>
            <option value="SUMMER_TERM">Summer Term</option>
          </select>
        </div>

        {/* Programs Grid */}
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-500">Loading exchange programs...</div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500 bg-slate-900/40 rounded-xl border border-slate-800">
            No mobility programs found matching your search.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filtered.map((prog) => (
              <div
                key={prog.id}
                className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-cyan-500/50 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold tracking-wider px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 uppercase">
                      {prog.academic_year || prog.academicYear}
                    </span>
                    <span className="text-xs text-slate-400 flex items-center gap-1">
                      <Users className="h-3.5 w-3.5 text-slate-500" />
                      {prog.total_seats || prog.totalSeats} seats
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-white mt-3 line-clamp-1">
                    {prog.program_title || prog.title}
                  </h3>

                  <p className="text-xs text-slate-400 mt-1 flex items-center gap-1.5">
                    <Globe className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
                    <span>
                      {prog.partner_name || prog.partnerName} ({prog.partner_country || prog.partnerCountry})
                    </span>
                  </p>

                  <div className="mt-4 pt-3 border-t border-slate-800/80 space-y-1 text-xs text-slate-300">
                    <p className="flex items-center justify-between">
                      <span className="text-slate-500">Eligibility Min CGPA:</span>
                      <span className="font-semibold text-slate-200">
                        {prog.min_cgpa_requirement || prog.minCgpaRequirement || "7.0"}
                      </span>
                    </p>
                    <p className="flex items-center justify-between">
                      <span className="text-slate-500">Academic Term:</span>
                      <span>{prog.term_type || prog.termType}</span>
                    </p>
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-slate-800 flex items-center justify-between">
                  <span className="text-[11px] text-amber-400/90 flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {prog.application_deadline || prog.applicationDeadline}
                  </span>

                  <Link
                    href={`/app/international/programs/${prog.id}`}
                    className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium transition-colors"
                  >
                    View & Apply &rarr;
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Create Program Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 shadow-2xl relative max-h-[90vh] overflow-y-auto">
              <button
                onClick={() => setShowCreateModal(false)}
                className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>

              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Compass className="h-4 w-4 text-cyan-400" />
                Publish Mobility Program
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Announce an exchange program cycle with automated eligibility CGPA and credit prerequisites
              </p>

              <form onSubmit={handleCreateProgram} className="mt-5 space-y-4">
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Host Partner Institution *</label>
                  <select
                    required
                    value={form.partner_id}
                    onChange={(e) => setForm({ ...form, partner_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="">Select partner university...</option>
                    {partners.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.partner_name || p.name} ({p.country_name || p.country || p.country_code})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Program Title *</label>
                  <input
                    required
                    type="text"
                    placeholder="e.g. TUM Informatics Fall Exchange 2026-27"
                    value={form.program_title}
                    onChange={(e) => setForm({ ...form, program_title: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Program Type</label>
                    <select
                      value={form.program_type}
                      onChange={(e) => setForm({ ...form, program_type: e.target.value as MobilityProgramType })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    >
                      <option value="SEMESTER_EXCHANGE">Semester Exchange</option>
                      <option value="YEAR_LONG_EXCHANGE">Year-long Exchange</option>
                      <option value="SUMMER_WINTER_SCHOOL">Summer/Winter School</option>
                      <option value="RESEARCH_INTERNSHIP">Research Internship</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Academic Term</label>
                    <select
                      value={form.term_type}
                      onChange={(e) => setForm({ ...form, term_type: e.target.value as MobilityTermType })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    >
                      <option value="FALL_SEMESTER">Fall Semester</option>
                      <option value="SPRING_SEMESTER">Spring Semester</option>
                      <option value="FULL_ACADEMIC_YEAR">Full Academic Year</option>
                      <option value="SUMMER_TERM">Summer Term</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Academic Year</label>
                    <input
                      type="text"
                      value={form.academic_year}
                      onChange={(e) => setForm({ ...form, academic_year: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Total Available Seats</label>
                    <input
                      type="number"
                      min={1}
                      value={form.total_seats}
                      onChange={(e) => setForm({ ...form, total_seats: Number(e.target.value) })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Minimum CGPA (0-10)</label>
                    <input
                      type="number"
                      step="0.1"
                      min={0}
                      max={10}
                      value={form.min_cgpa_requirement}
                      onChange={(e) => setForm({ ...form, min_cgpa_requirement: Number(e.target.value) })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Min Credits Completed</label>
                    <input
                      type="number"
                      min={0}
                      value={form.min_credits_completed}
                      onChange={(e) => setForm({ ...form, min_credits_completed: Number(e.target.value) })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Application Deadline *</label>
                    <input
                      required
                      type="date"
                      value={form.application_deadline}
                      onChange={(e) => setForm({ ...form, application_deadline: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Expected Start Date *</label>
                    <input
                      required
                      type="date"
                      value={form.expected_start_date}
                      onChange={(e) => setForm({ ...form, expected_start_date: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                </div>

                <div className="mt-6 flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md shadow-cyan-900/30 disabled:opacity-50"
                  >
                    {submitting ? "Publishing..." : "Publish Opportunity"}
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
