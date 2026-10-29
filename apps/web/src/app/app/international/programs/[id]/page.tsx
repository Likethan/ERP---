"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Calendar,
  CheckCircle2,
  Clock,
  Compass,
  FileCheck2,
  FileText,
  Globe,
  GraduationCap,
  ShieldAlert,
  Users,
} from "lucide-react";
import { InternationalNav } from "@/components/international/international-nav";
import { internationalService } from "@/services/international.service";
import { MobilityProgram } from "@/types/international";

export default function ProgramDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const programId = resolvedParams.id;

  const [program, setProgram] = useState<MobilityProgram | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const prog = await internationalService.getProgram(programId);
        setProgram(prog);
      } catch (err) {
        console.error("Failed to load program", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [programId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100">
        <InternationalNav />
        <div className="p-12 text-center text-xs text-slate-500">Loading mobility program specifications...</div>
      </div>
    );
  }

  if (!program) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100">
        <InternationalNav />
        <div className="p-12 text-center text-xs text-rose-400">Mobility program not found.</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <InternationalNav />

      <main className="p-6 max-w-5xl mx-auto space-y-6">
        <Link
          href="/app/international/programs"
          className="text-xs text-cyan-400 hover:text-cyan-300 font-medium inline-flex items-center gap-1.5"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to Mobility Programs
        </Link>

        {/* Program Hero Card */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md relative overflow-hidden">
          <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 font-semibold tracking-wider uppercase">
                  {program.term_type || program.termType} · {program.academic_year || program.academicYear}
                </span>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">
                  {program.program_code || program.programCode}
                </span>
              </div>

              <h2 className="text-2xl font-bold text-white tracking-tight">
                {program.program_title || program.title}
              </h2>

              <p className="text-xs text-slate-400 flex items-center gap-2">
                <Globe className="h-4 w-4 text-cyan-400 shrink-0" />
                <span className="font-semibold text-slate-200">
                  {program.partner_name || program.partnerName}
                </span>
                <span>({program.partner_country || program.partnerCountry})</span>
              </p>
            </div>

            <div className="flex flex-col gap-2 shrink-0">
              <Link
                href={`/app/international/applications?program_id=${program.id}`}
                className="px-5 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold shadow-lg shadow-cyan-900/40 text-center transition-all flex items-center justify-center gap-2"
              >
                <Compass className="h-4 w-4" />
                Apply for this Exchange
              </Link>
              <span className="text-[11px] text-amber-400/90 text-center flex items-center justify-center gap-1">
                <Clock className="h-3 w-3" />
                Deadline: {program.application_deadline || program.applicationDeadline}
              </span>
            </div>
          </div>

          {/* Quick Metrics Bar */}
          <div className="mt-6 pt-5 border-t border-slate-800 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div>
              <span className="text-slate-500 block">Total Quota Seats</span>
              <span className="text-base font-bold text-slate-200 mt-0.5 block">
                {program.total_seats || program.totalSeats} Students
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">Minimum CGPA</span>
              <span className="text-base font-bold text-slate-200 mt-0.5 block">
                {program.min_cgpa_requirement || program.minCgpaRequirement || "7.0"} / 10.0
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">Min Completed Credits</span>
              <span className="text-base font-bold text-slate-200 mt-0.5 block">
                {program.min_credits_completed || program.minCreditsCompleted || "30"} Credits
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">Exchange Duration</span>
              <span className="text-base font-bold text-slate-200 mt-0.5 block">
                1 Semester (~16 Weeks)
              </span>
            </div>
          </div>
        </div>

        {/* Requirements & Instructions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              Eligibility & Academic Prerequisites
            </h3>
            <ul className="space-y-2 text-xs text-slate-300">
              <li className="flex items-start gap-2">
                <span className="text-cyan-400 font-bold">•</span>
                <span>
                  Enrolled as a full-time undergraduate or master’s student in accredited departments.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-cyan-400 font-bold">•</span>
                <span>
                  Cumulative CGPA strictly verified at or above{" "}
                  <strong>{program.min_cgpa_requirement || program.minCgpaRequirement || 7.0}</strong> at time of application.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-cyan-400 font-bold">•</span>
                <span>
                  No active standing academic disciplinary sanctions or examination backlogs.
                </span>
              </li>
              {program.language_requirements && program.language_requirements.length > 0 && (
                <li className="flex items-start gap-2">
                  <span className="text-cyan-400 font-bold">•</span>
                  <span>
                    Language Proficiency: {program.language_requirements.join(", ")}.
                  </span>
                </li>
              )}
            </ul>
          </div>

          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <FileCheck2 className="h-4 w-4 text-cyan-400" />
              Required Documentation Checklist
            </h3>
            <p className="text-xs text-slate-400">
              Ensure high-resolution PDF scans are prepared before opening the application:
            </p>
            <ul className="space-y-2 text-xs text-slate-300">
              <li className="flex items-center gap-2">
                <span className="text-cyan-400 font-bold">•</span>
                <span>Valid International Passport (Bio-page with &gt; 6 months validity)</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="text-cyan-400 font-bold">•</span>
                <span>Official CampusOS Academic Transcript of Records</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="text-cyan-400 font-bold">•</span>
                <span>Statement of Purpose detailing proposed courses and academic goals</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="text-cyan-400 font-bold">•</span>
                <span>Preliminary Learning Agreement with proposed subject mappings</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Application Callout Footer */}
        <div className="p-5 rounded-xl bg-cyan-950/30 border border-cyan-800/40 flex items-center justify-between gap-4">
          <div>
            <h4 className="text-sm font-bold text-cyan-200">Ready to expand your global horizons?</h4>
            <p className="text-xs text-cyan-300/80">
              Applications are reviewed continuously by Department Faculty Coordinators and the International Office.
            </p>
          </div>
          <Link
            href={`/app/international/applications?program_id=${program.id}`}
            className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold transition-all shadow-md shrink-0"
          >
            Start Application &rarr;
          </Link>
        </div>
      </main>
    </div>
  );
}
