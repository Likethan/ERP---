"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  Calendar as CalendarIcon,
  CheckCircle2,
  Clock,
  Compass,
  DoorOpen,
  FileText,
  Globe,
  MapPin,
} from "lucide-react";
import { InternationalNav } from "@/components/international/international-nav";
import { internationalService } from "@/services/international.service";
import { InstitutionalAgreement, InboundStudentProfile, MobilityProgram } from "@/types/international";

interface CalendarEvent {
  id: string;
  date: string;
  title: string;
  category: "DEADLINE" | "DEPARTURE" | "ARRIVAL" | "ORIENTATION" | "MOU_EXPIRY";
  description: string;
  badge: string;
}

export default function MobilityCalendarPage() {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [progs, agrs, inbounds] = await Promise.all([
          internationalService.getPrograms(),
          internationalService.getAgreements(),
          internationalService.getInboundStudents(),
        ]);

        const evts: CalendarEvent[] = [];

        // Program deadlines
        progs.forEach((p) => {
          if (p.application_deadline || p.applicationDeadline) {
            evts.push({
              id: `dl-${p.id}`,
              date: p.application_deadline || p.applicationDeadline || "",
              title: `Application Deadline: ${p.program_title || p.title}`,
              category: "DEADLINE",
              description: `Deadline to apply for ${p.partner_name || "Partner"} exchange seats.`,
              badge: "Application Cutoff",
            });
          }
          if (p.expected_start_date || p.expectedStartDate) {
            evts.push({
              id: `st-${p.id}`,
              date: p.expected_start_date || p.expectedStartDate || "",
              title: `Semester Begins: ${p.partner_name || "Host University"}`,
              category: "DEPARTURE",
              description: `Outbound student arrivals and semester orientation abroad.`,
              badge: "Outbound Start",
            });
          }
        });

        // Inbound arrivals
        inbounds.forEach((s) => {
          if (s.study_period_start) {
            evts.push({
              id: `arr-${s.id}`,
              date: s.study_period_start,
              title: `Inbound Scholar Arrival: ${s.first_name} ${s.last_name}`,
              category: "ARRIVAL",
              description: `Host Department welcoming and campus dorm check-in.`,
              badge: "Inbound Check-in",
            });
          }
        });

        // MoU Expiries
        agrs.forEach((a) => {
          if (a.effective_end_date || a.expiry_date) {
            evts.push({
              id: `exp-${a.id}`,
              date: a.effective_end_date || a.expiry_date || "",
              title: `MoU Validity Expiration: ${a.agreement_title || a.title}`,
              category: "MOU_EXPIRY",
              description: `Treaty validity expiration date. Formal renewal required.`,
              badge: "Treaty Renewal",
            });
          }
        });

        // Sort ascending by date
        evts.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
        setEvents(evts);
      } catch (err) {
        console.error("Failed to load mobility calendar", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <InternationalNav />

      <main className="p-6 max-w-5xl mx-auto space-y-6">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <CalendarIcon className="h-5 w-5 text-cyan-400" />
            Global Mobility & Treaty Operational Calendar
          </h2>
          <p className="text-xs text-slate-400">
            Chronological milestones for student applications, overseas semester dates, inbound arrivals, and MoU renewal notice windows
          </p>
        </div>

        {/* Timeline View */}
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-500">Loading chronological milestones...</div>
        ) : events.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500 bg-slate-900/40 rounded-xl border border-slate-800">
            No scheduled mobility milestones found.
          </div>
        ) : (
          <div className="space-y-4">
            {events.map((evt, idx) => (
              <div
                key={evt.id}
                className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div className="flex items-start gap-4">
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-center shrink-0 w-16">
                    <span className="text-[10px] text-slate-500 font-bold uppercase block">
                      {new Date(evt.date).toLocaleString("default", { month: "short" })}
                    </span>
                    <span className="text-xl font-extrabold text-white block mt-0.5">
                      {new Date(evt.date).getDate() || 1}
                    </span>
                    <span className="text-[9px] text-slate-500 font-mono block">
                      {new Date(evt.date).getFullYear()}
                    </span>
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                          evt.category === "DEADLINE"
                            ? "bg-amber-500/10 text-amber-300 border border-amber-500/30"
                            : evt.category === "MOU_EXPIRY"
                            ? "bg-rose-500/10 text-rose-300 border border-rose-500/30"
                            : evt.category === "ARRIVAL"
                            ? "bg-purple-500/10 text-purple-300 border border-purple-500/30"
                            : "bg-emerald-500/10 text-emerald-300 border border-emerald-500/30"
                        }`}
                      >
                        {evt.badge}
                      </span>
                    </div>

                    <h4 className="text-sm font-bold text-white">{evt.title}</h4>
                    <p className="text-xs text-slate-400">{evt.description}</p>
                  </div>
                </div>

                <div className="text-right sm:self-center shrink-0">
                  <span className="text-xs font-mono text-slate-400 bg-slate-950 px-2.5 py-1 rounded border border-slate-800">
                    {evt.date}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
