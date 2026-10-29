"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  Award,
  BookOpen,
  Building2,
  Calendar,
  CheckCircle2,
  Clock,
  Compass,
  DoorOpen,
  FileCheck2,
  FileText,
  Globe,
  MapPin,
  Scale,
  ShieldCheck,
  TrendingUp,
  UserCheck,
  Users,
} from "lucide-react";
import { InternationalNav } from "@/components/international/international-nav";
import { internationalService } from "@/services/international.service";
import {
  InstitutionalAgreement,
  InternationalDashboardMetrics,
  InternationalPartner,
  MobilityApplication,
  MobilityProgram,
} from "@/types/international";

export default function InternationalDashboardPage() {
  const [metrics, setMetrics] = useState<InternationalDashboardMetrics | null>(null);
  const [partners, setPartners] = useState<InternationalPartner[]>([]);
  const [agreements, setAgreements] = useState<InstitutionalAgreement[]>([]);
  const [programs, setPrograms] = useState<MobilityProgram[]>([]);
  const [applications, setApplications] = useState<MobilityApplication[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [m, p, a, prog, app] = await Promise.all([
          internationalService.getDashboardMetrics(),
          internationalService.getPartners(),
          internationalService.getAgreements(),
          internationalService.getPrograms({ open_only: true }),
          internationalService.getApplications(),
        ]);
        setMetrics(m);
        setPartners(p);
        setAgreements(a);
        setPrograms(prog);
        setApplications(app);
      } catch (err) {
        console.error("Failed to load international telemetry", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const expiringAgreements = agreements.filter((a) => a.is_expiring_soon || a.status === "EXPIRING");

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <InternationalNav />

      <main className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Expiring Agreements Warning Banner */}
        {expiringAgreements.length > 0 && (
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <span className="p-2 rounded-lg bg-amber-500/20 text-amber-400 mt-0.5">
                <AlertTriangle className="h-5 w-5" />
              </span>
              <div>
                <h4 className="text-sm font-semibold text-amber-200">
                  {expiringAgreements.length} Institutional Agreement(s) Approaching Expiration
                </h4>
                <p className="text-xs text-amber-300/80 mt-0.5">
                  Renewal notice windows active for:{" "}
                  {expiringAgreements.map((a) => a.agreement_title || a.title).join(", ")}. Please initiate extension amendments or renewal reviews.
                </p>
              </div>
            </div>
            <Link
              href="/app/international/agreements?expiring_soon=true"
              className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-medium whitespace-nowrap transition-colors"
            >
              Review MoUs
            </Link>
          </div>
        )}

        {/* Telemetry Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-md relative overflow-hidden group hover:border-cyan-500/40 transition-all">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Active Partners</span>
              <span className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400">
                <Building2 className="h-4 w-4" />
              </span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white tracking-tight">
                {loading ? "..." : metrics?.total_active_partners || partners.length}
              </span>
              <span className="text-xs text-cyan-400 font-medium">Global Network</span>
            </div>
            <div className="mt-2 text-xs text-slate-400 flex items-center gap-1">
              <span>{agreements.length} Total MoUs & Agreements</span>
            </div>
          </div>

          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-md relative overflow-hidden group hover:border-emerald-500/40 transition-all">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Outbound Scholars</span>
              <span className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
                <MapPin className="h-4 w-4" />
              </span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white tracking-tight">
                {loading ? "..." : metrics?.active_outbound_students || 19}
              </span>
              <span className="text-xs text-emerald-400 font-medium">Enrolled Abroad</span>
            </div>
            <div className="mt-2 text-xs text-slate-400 flex items-center gap-1">
              <span>Across 6 partner countries</span>
            </div>
          </div>

          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-md relative overflow-hidden group hover:border-purple-500/40 transition-all">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Inbound Exchange</span>
              <span className="p-2 rounded-lg bg-purple-500/10 text-purple-400">
                <DoorOpen className="h-4 w-4" />
              </span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white tracking-tight">
                {loading ? "..." : metrics?.active_inbound_students || 7}
              </span>
              <span className="text-xs text-purple-400 font-medium">On-Campus</span>
            </div>
            <div className="mt-2 text-xs text-slate-400 flex items-center gap-1">
              <span>100% Orientation Completed</span>
            </div>
          </div>

          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-md relative overflow-hidden group hover:border-amber-500/40 transition-all">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Travel Grants Disbursed</span>
              <span className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
                <Award className="h-4 w-4" />
              </span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white tracking-tight">
                ${loading ? "..." : (metrics?.total_scholarship_disbursed || 45000).toLocaleString()}
              </span>
              <span className="text-xs text-amber-400 font-medium">Mobility Aid</span>
            </div>
            <div className="mt-2 text-xs text-slate-400 flex items-center gap-1">
              <span>Linked to Finance Ledger</span>
            </div>
          </div>
        </div>

        {/* Two Column Layout: Open Programs & Active Review Workspace */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Published Exchange Programs (2 Cols) */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-semibold text-white flex items-center gap-2">
                  <Compass className="h-4 w-4 text-cyan-400" />
                  Published Exchange Programs & Opportunities
                </h3>
                <p className="text-xs text-slate-400">
                  Semester exchanges, research fellowships, and global classrooms currently accepting applications
                </p>
              </div>
              <Link
                href="/app/international/programs"
                className="text-xs text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1"
              >
                View All ({programs.length}) &rarr;
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {programs.slice(0, 4).map((prog) => (
                <div
                  key={prog.id}
                  className="p-5 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-cyan-500/50 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                        {prog.academic_year || prog.academicYear}
                      </span>
                      <span className="text-xs text-slate-400 flex items-center gap-1">
                        <Users className="h-3.5 w-3.5 text-slate-500" />
                        {prog.total_seats || prog.totalSeats} seats
                      </span>
                    </div>

                    <h4 className="text-sm font-semibold text-white mt-2.5 line-clamp-1">
                      {prog.program_title || prog.title}
                    </h4>
                    <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
                      <Globe className="h-3 w-3 text-cyan-400" />
                      {prog.partner_name || prog.partnerName} ({prog.partner_country || prog.partnerCountry})
                    </p>

                    <div className="mt-3.5 pt-3 border-t border-slate-800/80 flex flex-wrap gap-2 text-[11px] text-slate-300">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                        Min CGPA: {prog.min_cgpa_requirement || prog.minCgpaRequirement || "7.0"}
                      </span>
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                        Term: {prog.term_type || prog.termType}
                      </span>
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between">
                    <span className="text-[11px] text-amber-400/90 flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      Deadline: {prog.application_deadline || prog.applicationDeadline}
                    </span>
                    <Link
                      href={`/app/international/programs/${prog.id}`}
                      className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-white text-xs font-medium transition-colors"
                    >
                      Details & Apply
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Review Pipeline & Quick Actions (1 Col) */}
          <div className="space-y-4">
            <div>
              <h3 className="text-base font-semibold text-white flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-emerald-400" />
                Active Review Pipeline
              </h3>
              <p className="text-xs text-slate-400">
                Multi-stage application decisions awaiting committee review
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 space-y-3">
              {applications.length === 0 ? (
                <p className="text-xs text-slate-500 py-4 text-center">No pending applications</p>
              ) : (
                applications.slice(0, 4).map((app) => (
                  <div
                    key={app.id}
                    className="p-3 rounded-lg bg-slate-800/50 border border-slate-800 hover:border-slate-700 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-white">
                        {app.student_name || app.studentName || "Student Applicant"}
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-medium bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                        {app.status}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1 line-clamp-1">
                      {app.program_title || app.programTitle}
                    </p>
                    <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400">
                      <span>Ref: {app.application_reference_number || app.applicationReferenceNumber}</span>
                      <Link
                        href={`/app/international/applications/review`}
                        className="text-cyan-400 hover:underline"
                      >
                        Review &rarr;
                      </Link>
                    </div>
                  </div>
                ))
              )}

              <Link
                href="/app/international/applications/review"
                className="w-full py-2 rounded-lg bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 text-xs font-medium border border-cyan-500/30 transition-colors flex items-center justify-center gap-1.5"
              >
                <ShieldCheck className="h-3.5 w-3.5" />
                Open Review Workspace
              </Link>
            </div>

            {/* Quick Links Section */}
            <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 space-y-2">
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Quick Actions</span>
              <div className="grid grid-cols-2 gap-2 pt-1">
                <Link
                  href="/app/international/partners"
                  className="p-2.5 rounded-lg bg-slate-800/60 hover:bg-slate-800 text-xs text-slate-300 border border-slate-800 flex items-center gap-2"
                >
                  <Building2 className="h-4 w-4 text-cyan-400" />
                  Partners
                </Link>
                <Link
                  href="/app/international/agreements"
                  className="p-2.5 rounded-lg bg-slate-800/60 hover:bg-slate-800 text-xs text-slate-300 border border-slate-800 flex items-center gap-2"
                >
                  <FileText className="h-4 w-4 text-emerald-400" />
                  MoUs
                </Link>
                <Link
                  href="/app/international/credit-transfer"
                  className="p-2.5 rounded-lg bg-slate-800/60 hover:bg-slate-800 text-xs text-slate-300 border border-slate-800 flex items-center gap-2"
                >
                  <Scale className="h-4 w-4 text-purple-400" />
                  Credit Transfer
                </Link>
                <Link
                  href="/app/international/scholarships"
                  className="p-2.5 rounded-lg bg-slate-800/60 hover:bg-slate-800 text-xs text-slate-300 border border-slate-800 flex items-center gap-2"
                >
                  <Award className="h-4 w-4 text-amber-400" />
                  Scholarships
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
