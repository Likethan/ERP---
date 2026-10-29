"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { studentAffairsService } from "@/services/student-affairs.service";
import {
  GrievanceCaseModel,
  CaseMeetingModel,
  SAMeetingType,
  SAMeetingStatus,
} from "@/types/student-affairs";
import { StudentAffairsNav } from "@/components/student-affairs/student-affairs-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Calendar,
  Clock,
  MapPin,
  Users,
  CheckCircle2,
  PlusCircle,
  Video,
  FileText,
  AlertCircle,
  ShieldCheck,
} from "lucide-react";

function MeetingsHearingsContent() {
  const searchParams = useSearchParams();
  const preselectedCaseId = searchParams?.get("caseId");

  const [cases, setCases] = useState<GrievanceCaseModel[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>(preselectedCaseId || "");
  const [meetings, setMeetings] = useState<CaseMeetingModel[]>([]);

  // Schedule modal
  const [title, setTitle] = useState("");
  const [meetingType, setMeetingType] = useState<SAMeetingType>(SAMeetingType.HEARING_PANEL);
  const [startDateTime, setStartDateTime] = useState("");
  const [endDateTime, setEndDateTime] = useState("");
  const [venueOrUrl, setVenueOrUrl] = useState("Administrative Block Room 204");
  const [facilitatorId, setFacilitatorId] = useState("usr-dean-001");
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState("");

  useEffect(() => {
    async function load() {
      const allCases = await studentAffairsService.getCases();
      setCases(allCases);
      if (preselectedCaseId) {
        setSelectedCaseId(preselectedCaseId);
      } else if (allCases.length > 0) {
        setSelectedCaseId(allCases[0].id);
      }
      // Gather all meetings across cases
      const allM: CaseMeetingModel[] = [];
      allCases.forEach((c) => {
        if (c.meetings) allM.push(...c.meetings);
      });
      setMeetings(allM);
    }
    load();
  }, [preselectedCaseId]);

  async function handleSchedule(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedCaseId || !title || !startDateTime) return;

    setLoading(true);
    try {
      const scheduled = await studentAffairsService.scheduleMeeting({
        caseId: selectedCaseId,
        title,
        meetingType,
        scheduledStart: new Date(startDateTime).toISOString(),
        scheduledEnd: endDateTime ? new Date(endDateTime).toISOString() : new Date(Date.now() + 3600000).toISOString(),
        venueOrUrl,
        facilitatorId,
      });
      setNotification(`Meeting "${title}" scheduled and invitations dispatched.`);
      setMeetings((prev) => [...prev, scheduled]);
      setTitle("");
      setStartDateTime("");
      setEndDateTime("");
    } catch {
      alert("Error scheduling meeting.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: "Dashboard", href: "/app/dashboard" },
          { label: "Student Affairs", href: "/app/student-affairs" },
          { label: "Meetings & Hearings", href: "/app/student-affairs/meetings" },
        ]}
      />

      <div className="border-b border-slate-800 pb-5">
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
          <Calendar className="h-6 w-6 text-blue-400" />
          Meetings, Committee Hearings & Mediation Sessions
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Coordinate grievance resolution conferences, witness inquiry panels, and voluntary peer mediation sessions with privacy-safe notices.
        </p>
      </div>

      <StudentAffairsNav />

      {notification && (
        <div className="p-3.5 rounded-lg border border-emerald-500/30 bg-emerald-950/20 text-xs text-emerald-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            <span>{notification}</span>
          </div>
          <button onClick={() => setNotification("")} className="text-emerald-400 hover:text-white">
            Dismiss
          </button>
        </div>
      )}

      {/* Recording Safeguard Notice */}
      <div className="p-3.5 rounded-lg border border-slate-800 bg-slate-950/40 text-xs text-slate-300 flex items-center gap-2">
        <ShieldCheck className="h-4 w-4 text-emerald-400 shrink-0" />
        <span>
          <strong>Privacy Policy:</strong> Automatic audio/video recording is disabled. Any formal recording requires explicit multi-party consent under institutional governance standards.
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Scheduled Sessions List (2 Cols) */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            Upcoming Hearings & Conciliation Sessions ({meetings.length})
          </h2>

          {meetings.length === 0 ? (
            <Card className="p-8 text-center border-slate-800 bg-slate-900/30 text-xs text-slate-500">
              No meetings or hearing sessions currently scheduled.
            </Card>
          ) : (
            <div className="space-y-3">
              {meetings.map((m) => (
                <Card key={m.id} className="p-4 border-slate-800 bg-slate-900/40 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-white text-xs">{m.title}</span>
                    <Badge className="bg-blue-500/10 text-blue-400 border-blue-500/20 text-[10px]">
                      {m.meeting_type}
                    </Badge>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-slate-400">
                    <div className="flex items-center gap-1.5">
                      <Clock className="h-3.5 w-3.5 text-slate-500" />
                      <span>{new Date(m.scheduled_start).toLocaleString()}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <MapPin className="h-3.5 w-3.5 text-slate-500" />
                      <span>{m.venue_or_url || "Campus Boardroom"}</span>
                    </div>
                  </div>

                  {m.agreed_actions && (
                    <div className="p-2 rounded bg-emerald-950/20 border border-emerald-500/20 text-[11px] text-emerald-300">
                      <strong>Agreed Outcomes: </strong> {m.agreed_actions}
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-[11px] text-slate-500">
                    <span>Status: <strong className="text-slate-300">{m.status}</strong></span>
                    <Button size="sm" variant="ghost" className="h-6 text-[10px] text-indigo-400">
                      Record Minutes
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Schedule Hearing Form (1 Col) */}
        <div>
          <Card className="p-6 border-slate-800 bg-slate-900/40 space-y-4">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <PlusCircle className="h-4 w-4 text-indigo-400" />
              Schedule Inquiry / Hearing
            </h2>
            <form onSubmit={handleSchedule} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-300 mb-1">Target Case Ref *</label>
                <select
                  value={selectedCaseId}
                  onChange={(e) => setSelectedCaseId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                >
                  {cases.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.case_number} - {c.title}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Session Title *</label>
                <input
                  type="text"
                  placeholder="e.g. Formal Hearing Panel / Mediation Session"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Meeting Type</label>
                <select
                  value={meetingType}
                  onChange={(e) => setMeetingType(e.target.value as SAMeetingType)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                >
                  <option value={SAMeetingType.HEARING_PANEL}>HEARING PANEL (Formal disciplinary inquiry)</option>
                  <option value={SAMeetingType.INTAKE_INTERVIEW}>INTAKE INTERVIEW (Preliminary grievance intake)</option>
                  <option value={SAMeetingType.MEDIATION_SESSION}>MEDIATION SESSION (Voluntary dispute resolution)</option>
                  <option value={SAMeetingType.RESOLUTION_CONFERENCE}>RESOLUTION CONFERENCE (Informal conciliation)</option>
                  <option value={SAMeetingType.APPEAL_HEARING}>APPEAL HEARING (Appellate panel review)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Date & Time *</label>
                <input
                  type="datetime-local"
                  value={startDateTime}
                  onChange={(e) => setStartDateTime(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1">Venue or Video URL</label>
                <input
                  type="text"
                  value={venueOrUrl}
                  onChange={(e) => setVenueOrUrl(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white"
                />
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-500 text-white text-xs mt-2"
              >
                Schedule & Notify Participants
              </Button>
            </form>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default function MeetingsHearingsPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-slate-500">Loading hearings...</div>}>
      <MeetingsHearingsContent />
    </Suspense>
  );
}

