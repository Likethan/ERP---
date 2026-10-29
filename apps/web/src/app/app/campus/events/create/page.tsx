"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { campusService } from "@/services/campus.service";
import {
  EventCategory,
  EventAudienceTarget,
  EventVenueInfo,
} from "@/types/campus";
import { useAuth } from "@/lib/auth-context";
import { AudienceBuilder } from "@/components/campus/audience-builder";
import {
  PartyPopper,
  ArrowRight,
  ArrowLeft,
  Calendar,
  Clock,
  MapPin,
  Users,
  CheckCircle2,
  AlertTriangle,
  Info,
  ShieldAlert,
  Save,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { MOCK_VENUES } from "@/mocks/campus.mock";

const STEPS = [
  { step: 1, title: "Basic Information", desc: "Title, category & organizer" },
  { step: 2, title: "Schedule", desc: "Dates and operational times" },
  { step: 3, title: "Venue Selection", desc: "Facility, room & capacity" },
  { step: 4, title: "Target Audience", desc: "Eligibility & cohort scope" },
  {
    step: 5,
    title: "Registration Rules",
    desc: "Capacities, deadlines & waitlist",
  },
  { step: 6, title: "Attendance Tracking", desc: "Verification policy" },
  { step: 7, title: "Review & Save", desc: "Draft confirmation" },
];

const CATEGORIES: EventCategory[] = [
  "Academic",
  "Technical",
  "Cultural",
  "Sports",
  "Workshop",
  "Seminar",
  "Hackathon",
  "Symposium",
  "Club Activity",
  "Placement",
  "Orientation",
  "Institutional",
];

export default function CreateEventWizardPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [currentStep, setCurrentStep] = useState(1);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Form State
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState<EventCategory>("Technical");
  const [organizer, setOrganizer] = useState(
    "Association of Computer Engineers (ACE)",
  );
  const [organizerType, setOrganizerType] = useState<
    "DEPARTMENT" | "CLUB" | "INSTITUTION"
  >("CLUB");

  // Step 2 — Schedule
  const [startDate, setStartDate] = useState("2026-10-25");
  const [endDate, setEndDate] = useState("2026-10-25");
  const [startTime, setStartTime] = useState("10:00 AM");
  const [endTime, setEndTime] = useState("04:00 PM");

  // Step 3 — Venue
  const [selectedVenueId, setSelectedVenueId] = useState<string>(
    MOCK_VENUES[0].id,
  );

  // Step 4 — Audience
  const [targetAudience, setTargetAudience] = useState<EventAudienceTarget>({
    type: "ALL_STUDENTS",
    estimatedCount: 4200,
  });

  // Step 5 — Registration
  const [requiresRegistration, setRequiresRegistration] = useState(true);
  const [regOpenDate, setRegOpenDate] = useState("2026-10-10");
  const [regCloseDate, setRegCloseDate] = useState("2026-10-24");
  const [capacity, setCapacity] = useState(250);
  const [allowWaitlist, setAllowWaitlist] = useState(true);

  // Step 6 — Attendance
  const [requiresAttendance, setRequiresAttendance] = useState(true);

  const selectedVenue =
    MOCK_VENUES.find((v) => v.id === selectedVenueId) || MOCK_VENUES[0];

  // Venue Conflict Simulation
  const hasCapacityWarning = capacity > selectedVenue.capacity;
  const isSimulatedConflict =
    selectedVenue.name.includes("Auditorium") && startDate === "2026-10-22";

  const handleNext = () => {
    setFormError(null);
    if (currentStep === 1) {
      if (!title.trim()) {
        setFormError("Event name is required.");
        return;
      }
      if (!description.trim()) {
        setFormError("Event description is required.");
        return;
      }
    }
    if (currentStep === 2) {
      if (!startDate || !endDate) {
        setFormError("Start and End dates are required.");
        return;
      }
    }
    setCurrentStep((prev) => Math.min(STEPS.length, prev + 1));
  };

  const handleBack = () => {
    setFormError(null);
    setCurrentStep((prev) => Math.max(1, prev - 1));
  };

  const handleSaveDraft = async () => {
    try {
      setSaving(true);
      setFormError(null);

      const res = await campusService.createEvent({
        title,
        category,
        description,
        organizer,
        organizerType,
        startDate,
        endDate,
        startTime,
        endTime,
        venue: selectedVenue.name,
        venueId: selectedVenue.id,
        venueDetails: selectedVenue,
        capacity,
        requiresRegistration,
        registrationOpenDate: requiresRegistration ? regOpenDate : undefined,
        registrationCloseDate: requiresRegistration ? regCloseDate : undefined,
        allowWaitlist,
        requiresAttendance,
        targetAudience,
        createdBy: `${user?.first_name || "Coordinator"} ${user?.last_name || ""}`,
      });

      if (res.success && res.data) {
        router.push(`/app/campus/events/${res.data.id}`);
      } else {
        setFormError(res.error || "Failed to save event draft");
      }
    } catch (e: any) {
      setFormError(e.message || "Failed to save event");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in max-w-4xl mx-auto pb-16">
      {/* Header */}
      <div className="border-b border-slate-800 pb-5">
        <div className="flex items-center gap-2">
          <Link
            href="/app/campus"
            className="text-xs text-slate-400 hover:text-indigo-400"
          >
            Campus Hub
          </Link>
          <span className="text-slate-600">/</span>
          <Link
            href="/app/campus/events"
            className="text-xs text-slate-400 hover:text-indigo-400"
          >
            Events
          </Link>
          <span className="text-slate-600">/</span>
          <span className="text-xs text-slate-200 font-semibold">
            New Event Creation
          </span>
        </div>
        <h1 className="mt-1 text-2xl font-black tracking-tight text-white flex items-center gap-2.5">
          <PartyPopper className="h-6 w-6 text-indigo-400" />
          Guided Event Proposal Workflow
        </h1>
        <p className="mt-1 text-xs text-slate-400">
          Propose an institutional event, configure capacity quotas, venue
          selection, and participant targeting.
        </p>
      </div>

      {/* Stepper Progress Bar */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
          {STEPS.map((s) => {
            const isCompleted = currentStep > s.step;
            const isCurrent = currentStep === s.step;
            return (
              <div
                key={s.step}
                className={`p-2.5 rounded-xl border transition-all text-left ${
                  isCurrent
                    ? "bg-indigo-600/20 border-indigo-500 text-white"
                    : isCompleted
                      ? "bg-emerald-950/20 border-emerald-500/40 text-emerald-300"
                      : "bg-slate-950/40 border-slate-800/80 text-slate-500"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-bold">
                    Step {s.step}
                  </span>
                  {isCompleted && (
                    <CheckCircle2 className="h-3 w-3 text-emerald-400" />
                  )}
                </div>
                <div className="text-xs font-semibold mt-0.5 truncate">
                  {s.title}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Form Error Banner */}
      {formError && (
        <div className="flex items-center gap-2.5 p-3.5 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs">
          <AlertTriangle className="h-4 w-4 shrink-0 text-rose-400" />
          <span>{formError}</span>
        </div>
      )}

      {/* STEP 1: BASIC INFORMATION */}
      {currentStep === 1 && (
        <div className="space-y-5 rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
          <div className="border-b border-slate-800 pb-3">
            <h2 className="text-sm font-bold text-white">
              Step 1 — Basic Event Information
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Define core identifiers and classification.
            </p>
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-300">
                Event Name <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. HackCampus 2026: 36-Hour National Autonomous Hackathon"
                className="mt-1 w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-300">
                  Event Category
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value as EventCategory)}
                  className="mt-1 w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300">
                  Organizer Entity Type
                </label>
                <select
                  value={organizerType}
                  onChange={(e) => setOrganizerType(e.target.value as any)}
                  className="mt-1 w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="CLUB">Student Club / Guild</option>
                  <option value="DEPARTMENT">Academic Department</option>
                  <option value="INSTITUTION">
                    Central University Directorate
                  </option>
                </select>
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300">
                Organizer Organization / Name{" "}
                <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                value={organizer}
                onChange={(e) => setOrganizer(e.target.value)}
                placeholder="e.g. Association of Computer Engineers (ACE)"
                className="mt-1 w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300">
                Detailed Description <span className="text-rose-400">*</span>
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={4}
                placeholder="Describe event objectives, agenda, keynote speakers, and judging criteria..."
                className="mt-1 w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>
        </div>
      )}

      {/* STEP 2: SCHEDULE */}
      {currentStep === 2 && (
        <div className="space-y-5 rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
          <div className="border-b border-slate-800 pb-3">
            <h2 className="text-sm font-bold text-white">
              Step 2 — Dates & Operational Schedule
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Set the execution dates and daily timetable.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-semibold text-slate-300">
                Start Date
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="mt-1 w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300">
                End Date
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="mt-1 w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-semibold text-slate-300">
                Start Time
              </label>
              <input
                type="text"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                placeholder="e.g. 09:30 AM"
                className="mt-1 w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300">
                End Time
              </label>
              <input
                type="text"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                placeholder="e.g. 05:00 PM"
                className="mt-1 w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>
        </div>
      )}

      {/* STEP 3: VENUE SELECTION & CONFLICT WARNINGS */}
      {currentStep === 3 && (
        <div className="space-y-5 rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
          <div className="border-b border-slate-800 pb-3">
            <h2 className="text-sm font-bold text-white">
              Step 3 — Venue & Infrastructure Selection
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Choose campus auditorium, lab or seminar hall.
            </p>
          </div>

          {/* Conflict Warning simulation */}
          {isSimulatedConflict && (
            <div className="p-3.5 rounded-xl border border-rose-500/40 bg-rose-950/20 text-rose-300 text-xs flex items-start gap-2.5">
              <ShieldAlert className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">
                  Simulated Scheduling Conflict:{" "}
                </span>
                This venue is already allocated to "National Symposium" on{" "}
                {startDate}. You may still proceed with draft creation.
              </div>
            </div>
          )}

          {hasCapacityWarning && (
            <div className="p-3.5 rounded-xl border border-amber-500/40 bg-amber-950/20 text-amber-300 text-xs flex items-start gap-2.5">
              <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">Capacity Exceeded Notice: </span>
                Target capacity ({capacity}) exceeds the venue's certified
                seating limit ({selectedVenue.capacity}).
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {MOCK_VENUES.map((v) => {
              const isSelected = selectedVenueId === v.id;
              return (
                <div
                  key={v.id}
                  onClick={() => setSelectedVenueId(v.id)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    isSelected
                      ? "border-indigo-500 bg-indigo-950/20 text-white shadow-md shadow-indigo-500/10"
                      : "border-slate-800 bg-slate-950/60 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold">{v.name}</span>
                    {isSelected && (
                      <CheckCircle2 className="h-4 w-4 text-indigo-400" />
                    )}
                  </div>
                  <div className="mt-1 text-[11px] text-slate-400">
                    {v.building} • Room {v.roomNumber}
                  </div>
                  <div className="mt-2 flex items-center justify-between text-[11px] pt-2 border-t border-slate-800/60 font-mono">
                    <span className="text-slate-300">
                      Capacity: {v.capacity} seats
                    </span>
                    <span className="text-emerald-400">Available</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* STEP 4: AUDIENCE TARGETING */}
      {currentStep === 4 && (
        <AudienceBuilder value={targetAudience} onChange={setTargetAudience} />
      )}

      {/* STEP 5: REGISTRATION CONFIGURATION */}
      {currentStep === 5 && (
        <div className="space-y-5 rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
          <div className="border-b border-slate-800 pb-3">
            <h2 className="text-sm font-bold text-white">
              Step 5 — Registration Rules & Capacity
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Configure participant limits and registration timeline.
            </p>
          </div>

          <div className="space-y-4">
            <label className="flex items-center gap-3 p-3 rounded-xl border border-slate-800 bg-slate-950/60 cursor-pointer">
              <input
                type="checkbox"
                checked={requiresRegistration}
                onChange={(e) => setRequiresRegistration(e.target.checked)}
                className="h-4 w-4 rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-0"
              />
              <div>
                <span className="text-xs font-bold text-white block">
                  Requires Registration
                </span>
                <span className="text-[11px] text-slate-400">
                  Participants must register online and receive entry ticket
                  codes
                </span>
              </div>
            </label>

            {requiresRegistration && (
              <div className="space-y-4 pt-2">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-semibold text-slate-300">
                      Registration Opens Date
                    </label>
                    <input
                      type="date"
                      value={regOpenDate}
                      onChange={(e) => setRegOpenDate(e.target.value)}
                      className="mt-1 w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-white"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-slate-300">
                      Registration Closes Date
                    </label>
                    <input
                      type="date"
                      value={regCloseDate}
                      onChange={(e) => setRegCloseDate(e.target.value)}
                      className="mt-1 w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-white"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-semibold text-slate-300">
                      Participant Capacity Limit
                    </label>
                    <input
                      type="number"
                      value={capacity}
                      onChange={(e) =>
                        setCapacity(parseInt(e.target.value, 10) || 100)
                      }
                      className="mt-1 w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-white font-mono"
                    />
                  </div>

                  <div className="flex items-center pt-5">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={allowWaitlist}
                        onChange={(e) => setAllowWaitlist(e.target.checked)}
                        className="h-4 w-4 rounded border-slate-700 bg-slate-900 text-indigo-600"
                      />
                      <span className="text-xs text-slate-300 font-medium">
                        Enable Automatic Waitlist when Full
                      </span>
                    </label>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* STEP 6: ATTENDANCE TRACKING */}
      {currentStep === 6 && (
        <div className="space-y-5 rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
          <div className="border-b border-slate-800 pb-3">
            <h2 className="text-sm font-bold text-white">
              Step 6 — Event Attendance Configuration
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Specify whether physical attendance will be audited.
            </p>
          </div>

          <div className="space-y-3">
            <label className="flex items-center gap-3 p-4 rounded-xl border border-slate-800 bg-slate-950/60 cursor-pointer">
              <input
                type="checkbox"
                checked={requiresAttendance}
                onChange={(e) => setRequiresAttendance(e.target.checked)}
                className="h-4 w-4 rounded border-slate-700 bg-slate-900 text-indigo-600"
              />
              <div>
                <span className="text-xs font-bold text-white block">
                  Track Event Attendance & Physical Verification
                </span>
                <span className="text-[11px] text-slate-400">
                  Event coordinators will have access to live hall rosters to
                  mark Present, Absent or Excused.
                </span>
              </div>
            </label>

            <div className="p-3.5 rounded-xl bg-slate-950/40 border border-slate-800 text-[11px] text-slate-400 flex items-center gap-2">
              <Info className="h-4 w-4 text-indigo-400 shrink-0" />
              <span>
                Attendance statistics are calculated using centralized
                enterprise formula.
              </span>
            </div>
          </div>
        </div>
      )}

      {/* STEP 7: REVIEW & SAVE AS DRAFT */}
      {currentStep === 7 && (
        <div className="space-y-5 rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
          <div className="border-b border-slate-800 pb-3">
            <h2 className="text-sm font-bold text-white">
              Step 7 — Review Event Summary
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Review all parameters. Event will be saved strictly as{" "}
              <strong>DRAFT</strong>.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <span className="text-[10px] text-slate-500 uppercase font-mono">
                Event Name
              </span>
              <div className="font-bold text-white">{title}</div>
              <div className="text-indigo-400 font-medium">{category}</div>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <span className="text-[10px] text-slate-500 uppercase font-mono">
                Organizer
              </span>
              <div className="font-bold text-white">{organizer}</div>
              <div className="text-slate-400">{organizerType}</div>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <span className="text-[10px] text-slate-500 uppercase font-mono">
                Schedule & Venue
              </span>
              <div className="font-bold text-white">
                {startDate} • {startTime} - {endTime}
              </div>
              <div className="text-slate-400">
                {selectedVenue.name} ({selectedVenue.roomNumber})
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <span className="text-[10px] text-slate-500 uppercase font-mono">
                Capacity & Audience
              </span>
              <div className="font-bold text-white">
                {capacity} maximum participants
              </div>
              <div className="text-slate-400">
                Audience: {targetAudience.type} (~
                {targetAudience.estimatedCount} estimated reach)
              </div>
            </div>
          </div>

          <div className="p-3.5 rounded-xl border border-indigo-500/30 bg-indigo-950/20 text-indigo-300 text-xs flex items-center gap-2">
            <Info className="h-4 w-4 shrink-0 text-indigo-400" />
            <span>
              <strong>Administrative Rule:</strong> Events are created as{" "}
              <strong>DRAFT</strong>. Approval and publication can be done from
              the event detail screen.
            </span>
          </div>
        </div>
      )}

      {/* Navigation Controls */}
      <div className="flex items-center justify-between border-t border-slate-800 pt-5">
        <Button
          variant="outline"
          size="sm"
          onClick={handleBack}
          disabled={currentStep === 1 || saving}
          leftIcon={<ArrowLeft className="h-4 w-4" />}
          className="border-slate-700 bg-slate-900"
        >
          Previous
        </Button>

        {currentStep < STEPS.length ? (
          <Button
            variant="primary"
            size="sm"
            onClick={handleNext}
            rightIcon={<ArrowRight className="h-4 w-4" />}
            className="bg-indigo-600 hover:bg-indigo-500"
          >
            Continue
          </Button>
        ) : (
          <Button
            variant="primary"
            size="sm"
            isLoading={saving}
            onClick={handleSaveDraft}
            leftIcon={<Save className="h-4 w-4" />}
            className="bg-emerald-600 hover:bg-emerald-500 shadow-md shadow-emerald-600/30"
          >
            Save as Draft
          </Button>
        )}
      </div>
    </div>
  );
}
