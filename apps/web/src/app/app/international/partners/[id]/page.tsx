"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Building2,
  Calendar,
  CheckCircle2,
  Clock,
  Compass,
  ExternalLink,
  FileText,
  Globe,
  Mail,
  MapPin,
  Phone,
  Plus,
  ShieldCheck,
  Users,
} from "lucide-react";
import { InternationalNav } from "@/components/international/international-nav";
import { internationalService } from "@/services/international.service";
import { InstitutionalAgreement, InternationalPartner, MobilityProgram } from "@/types/international";

export default function PartnerDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const partnerId = resolvedParams.id;

  const [partner, setPartner] = useState<InternationalPartner | null>(null);
  const [agreements, setAgreements] = useState<InstitutionalAgreement[]>([]);
  const [programs, setPrograms] = useState<MobilityProgram[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [p, a, prog] = await Promise.all([
          internationalService.getPartner(partnerId),
          internationalService.getAgreements({ partner_id: partnerId }),
          internationalService.getPrograms({ partner_id: partnerId }),
        ]);
        setPartner(p);
        setAgreements(a);
        setPrograms(prog);
      } catch (err) {
        console.error("Failed to load partner details", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [partnerId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100">
        <InternationalNav />
        <div className="p-12 text-center text-xs text-slate-500">Loading partner institution profile...</div>
      </div>
    );
  }

  if (!partner) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100">
        <InternationalNav />
        <div className="p-12 text-center text-xs text-rose-400">Partner institution not found.</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <InternationalNav />

      <main className="p-6 max-w-7xl mx-auto space-y-6">
        <Link
          href="/app/international/partners"
          className="text-xs text-cyan-400 hover:text-cyan-300 font-medium inline-flex items-center gap-1.5"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to Partner Registry
        </Link>

        {/* Institution Overview Card */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md relative overflow-hidden">
          <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 font-semibold tracking-wider uppercase">
                  {partner.category || partner.partnership_category || "UNIVERSITY"}
                </span>
                <span
                  className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                    partner.is_active || partner.status === "ACTIVE"
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : "bg-slate-800 text-slate-400"
                  }`}
                >
                  {partner.is_active || partner.status === "ACTIVE" ? "Active Partnership" : "Inactive"}
                </span>
              </div>

              <h2 className="text-2xl font-bold text-white tracking-tight">
                {partner.partner_name || partner.name}
              </h2>

              <p className="text-xs text-slate-400 flex items-center gap-2">
                <MapPin className="h-4 w-4 text-cyan-400 shrink-0" />
                <span>
                  {partner.city ? `${partner.city}, ` : ""}
                  {partner.country_name || partner.country || partner.country_code}
                </span>
                {partner.country_code && (
                  <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-slate-800 text-slate-300">
                    {partner.country_code}
                  </span>
                )}
              </p>
            </div>

            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
              {partner.official_website && (
                <a
                  href={partner.official_website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-medium border border-slate-700 transition-colors flex items-center justify-center gap-2"
                >
                  <ExternalLink className="h-3.5 w-3.5 text-cyan-400" />
                  Official Website
                </a>
              )}
              <Link
                href={`/app/international/agreements?partner_id=${partner.id}`}
                className="px-3.5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md shadow-cyan-900/30 transition-colors flex items-center justify-center gap-1.5"
              >
                <Plus className="h-4 w-4" />
                Add MoU
              </Link>
            </div>
          </div>

          <div className="mt-6 pt-5 border-t border-slate-800 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div>
              <span className="text-slate-500 block">Primary Contact Person</span>
              <span className="font-semibold text-slate-200 mt-0.5 block">
                {partner.primary_contact_name || "Not designated"}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">Official Email</span>
              <span className="font-semibold text-slate-200 mt-0.5 block truncate">
                {partner.primary_contact_email || "N/A"}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block">Contact Telephone</span>
              <span className="font-semibold text-slate-200 mt-0.5 block">
                {partner.primary_contact_phone || "N/A"}
              </span>
            </div>
          </div>
        </div>

        {/* Agreements Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <FileText className="h-4 w-4 text-emerald-400" />
                Institutional Agreements & MoUs ({agreements.length})
              </h3>
              <p className="text-xs text-slate-400">
                Formal legal covenants, exchange protocols, and renewal tracking
              </p>
            </div>
          </div>

          {agreements.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500 bg-slate-900/40 rounded-xl border border-slate-800">
              No formal agreements recorded for this institution yet.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {agreements.map((agr) => (
                <div
                  key={agr.id}
                  className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                        {agr.agreement_type || agr.agreementType}
                      </span>
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                          agr.is_expiring_soon || agr.status === "EXPIRING"
                            ? "bg-amber-500/10 text-amber-300 border border-amber-500/20"
                            : agr.status === "ACTIVE"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {agr.is_expiring_soon ? "Expiring Soon" : agr.status}
                      </span>
                    </div>

                    <h4 className="text-sm font-bold text-white mt-2.5">
                      {agr.agreement_title || agr.agreementTitle || agr.title}
                    </h4>
                    <p className="text-xs text-slate-400 mt-1">
                      Ref: {agr.agreement_reference_number || agr.agreementReferenceNumber}
                    </p>

                    <div className="mt-3.5 pt-3 border-t border-slate-800/80 space-y-1 text-xs text-slate-300">
                      <p className="flex items-center justify-between">
                        <span className="text-slate-500">Effective Duration:</span>
                        <span>
                          {agr.effective_start_date || agr.start_date} to {agr.effective_end_date || agr.expiry_date}
                        </span>
                      </p>
                      {agr.coordinator_name && (
                        <p className="flex items-center justify-between">
                          <span className="text-slate-500">Coordinator:</span>
                          <span>{agr.coordinator_name}</span>
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between">
                    <span className="text-[11px] text-slate-400">
                      {agr.amendments_count || 0} Amendment(s)
                    </span>
                    <Link
                      href="/app/international/agreements"
                      className="text-xs text-cyan-400 hover:underline"
                    >
                      Manage Agreement &rarr;
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Mobility Programs Section */}
        <div className="space-y-4">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Compass className="h-4 w-4 text-cyan-400" />
              Active Mobility Programs ({programs.length})
            </h3>
            <p className="text-xs text-slate-400">
              Exchange tracks and study abroad opportunities offered through this partnership
            </p>
          </div>

          {programs.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500 bg-slate-900/40 rounded-xl border border-slate-800">
              No active mobility programs published for this institution.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {programs.map((prog) => (
                <div
                  key={prog.id}
                  className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between"
                >
                  <div>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                      {prog.academic_year || prog.academicYear}
                    </span>
                    <h4 className="text-sm font-bold text-white mt-2">
                      {prog.program_title || prog.title}
                    </h4>
                    <p className="text-xs text-slate-400 mt-1">Code: {prog.program_code || prog.programCode}</p>
                    <div className="mt-3 text-xs text-slate-300 space-y-1">
                      <p>Seats: {prog.total_seats || prog.totalSeats}</p>
                      <p>Min CGPA: {prog.min_cgpa_requirement || prog.minCgpaRequirement || "7.0"}</p>
                    </div>
                  </div>
                  <div className="mt-4 pt-3 border-t border-slate-800">
                    <Link
                      href={`/app/international/programs/${prog.id}`}
                      className="w-full py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-medium text-center block transition-colors"
                    >
                      View Details
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
