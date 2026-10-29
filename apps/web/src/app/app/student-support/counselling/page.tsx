"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { StudentSupportService } from "@/services/student-support.service";
import {
  CounsellingAppointmentItem,
  SupportPolicyConfigItem,
} from "@/types/student-support";
import { StudentSupportNav } from "@/components/student-support/student-support-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Heart,
  Calendar,
  Clock,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Video,
  MapPin,
  XCircle,
  RotateCcw,
} from "lucide-react";

const CATEGORIES = [
  "ACADEMIC_STRESS",
  "CAREER_ANXIETY",
  "PERSONAL_WELLBEING",
  "PEER_RELATIONSHIPS",
  "TIME_MANAGEMENT",
  "OTHER",
];

export default function CounsellingBookingPage() {
  const [appointments, setAppointments] = useState<CounsellingAppointmentItem[]>([]);
  const [config, setConfig] = useState<SupportPolicyConfigItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Form State
  const [category, setCategory] = useState("ACADEMIC_STRESS");
  const [appointmentMode, setAppointmentMode] = useState<"IN_PERSON" | "ONLINE">("IN_PERSON");
  const [preferredDate, setPreferredDate] = useState("");
  const [preferredTime, setPreferredTime] = useState("");
  const [studentNotes, setStudentNotes] = useState("");

  // Reschedule / Cancel Modal State
  const [actionModalOpen, setActionModalOpen] = useState(false);
  const [actionType, setActionType] = useState<"RESCHEDULE" | "CANCEL">("CANCEL");
  const [selectedAppt, setSelectedAppt] = useState<CounsellingAppointmentItem | null>(null);
  const [actionReason, setActionReason] = useState("");
  const [rescheduleDate, setRescheduleDate] = useState("");
  const [rescheduleTime, setRescheduleTime] = useState("");
  const [processingAction, setProcessingAction] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [appts, polConfig] = await Promise.all([
        StudentSupportService.getCounsellingAppointments(),
        StudentSupportService.getPolicyConfig(),
      ]);
      setAppointments(appts);
      setConfig(polConfig);
    } catch (err) {
      console.error("Failed to load appointments:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleBookAppointment(e: React.FormEvent) {
    e.preventDefault();
    if (!preferredDate || !preferredTime) return;
    setSubmitting(true);
    setErrorMessage(null);
    try {
      const scheduledStart = new Date(`${preferredDate}T${preferredTime}:00Z`).toISOString();
      const scheduledEnd = new Date(new Date(scheduledStart).getTime() + 50 * 60000).toISOString();

      await StudentSupportService.createCounsellingAppointment({
        category,
        appointment_mode: appointmentMode,
        scheduled_start: scheduledStart,
        scheduled_end: scheduledEnd,
        location: appointmentMode === "IN_PERSON" ? "Student Wellness Centre, Suite 104" : "CampusOS Secure Video",
        virtual_meeting_link: appointmentMode === "ONLINE" ? "https://meet.campusos.edu/counsel-confidential" : undefined,
        reason_summary: studentNotes || "General guidance & consultation requested.",
      });

      setSuccessMessage("Your confidential counselling appointment has been requested. Confirmation will follow shortly.");
      setPreferredDate("");
      setPreferredTime("");
      setStudentNotes("");
      loadData();
    } catch (err) {
      console.error("Booking error:", err);
      setErrorMessage("Could not schedule appointment. Please ensure slot is at least 12 hours in advance and not in conflict.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleConfirmAction(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedAppt) return;
    setProcessingAction(true);
    try {
      if (actionType === "CANCEL") {
        await StudentSupportService.transitionCounsellingAppointment(selectedAppt.id, {
          status: "CANCELLED",
          cancellation_reason: actionReason || "Cancelled by student",
        });
        setSuccessMessage("Appointment has been cancelled.");
      } else {
        const newStart = new Date(`${rescheduleDate}T${rescheduleTime}:00Z`).toISOString();
        const newEnd = new Date(new Date(newStart).getTime() + 50 * 60000).toISOString();
        await StudentSupportService.transitionCounsellingAppointment(selectedAppt.id, {
          status: "RESCHEDULED",
          rescheduled_start: newStart,
          rescheduled_end: newEnd,
          reschedule_reason: actionReason,
        });
        setSuccessMessage("Appointment rescheduled successfully.");
      }
      setActionModalOpen(false);
      setSelectedAppt(null);
      setActionReason("");
      setRescheduleDate("");
      setRescheduleTime("");
      loadData();
    } catch (err) {
      console.error("Action error:", err);
      alert("Failed to update appointment. Please contact wellness office.");
    } finally {
      setProcessingAction(false);
    }
  }

  return (
    <div className="space-y-6 pb-12">
      <div>
        <Breadcrumbs
          items={[
            { label: "Dashboard", href: "/app/dashboard" },
            { label: "Student Support", href: "/app/student-support" },
            { label: "Book Counselling", href: "/app/student-support/counselling" },
          ]}
        />
        <div className="mt-2 flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <Heart className="h-6 w-6 text-rose-400" />
              Institutional Counselling Services
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Confidential, professional guidance for academic, emotional, and personal wellbeing.
            </p>
          </div>
          <Link href="/app/student-support/counselling/schedule">
            <Button variant="outline" className="border-slate-700 text-xs text-slate-200">
              <Calendar className="mr-1.5 h-3.5 w-3.5 text-indigo-400" />
              Counsellor Schedule View
            </Button>
          </Link>
        </div>
      </div>

      <StudentSupportNav />

      {/* Strict Privacy Guarantee Box */}
      <div className="rounded-xl border border-rose-900/40 bg-rose-950/20 p-4">
        <div className="flex items-start gap-3">
          <ShieldCheck className="h-5 w-5 text-rose-400 mt-0.5 shrink-0" />
          <div className="text-xs text-slate-300">
            <span className="font-semibold text-white">Confidentiality Guarantee:</span> Counselling sessions are strictly private. Session notes and personal discussions are never shared with academic mentors, professors, HODs, or recorded on academic transcripts.
          </div>
        </div>
      </div>

      {successMessage && (
        <div className="rounded-lg border border-emerald-800/50 bg-emerald-950/30 p-3 text-xs text-emerald-300 flex items-center justify-between">
          <span className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            {successMessage}
          </span>
          <button onClick={() => setSuccessMessage(null)} className="text-emerald-400 hover:text-emerald-200">
            Dismiss
          </button>
        </div>
      )}

      {errorMessage && (
        <div className="rounded-lg border border-rose-800/50 bg-rose-950/30 p-3 text-xs text-rose-300 flex items-center justify-between">
          <span className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4" />
            {errorMessage}
          </span>
          <button onClick={() => setErrorMessage(null)} className="text-rose-400 hover:text-rose-200">
            Dismiss
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Booking Form (Left Column) */}
        <Card className="border-slate-800 bg-slate-900/60 p-6 space-y-4">
          <div>
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <Calendar className="h-4 w-4 text-indigo-400" />
              Request an Appointment
            </h2>
            <p className="text-xs text-slate-400">Choose your consultation mode and category</p>
          </div>

          <form onSubmit={handleBookAppointment} className="space-y-4 text-xs">
            <div className="space-y-1">
              <label className="text-slate-400 font-medium">Category *</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-white"
              >
                {CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat.replace("_", " ")}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-slate-400 font-medium">Consultation Mode *</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setAppointmentMode("IN_PERSON")}
                  className={`flex items-center justify-center gap-2 p-2.5 rounded-lg border text-xs font-medium transition ${
                    appointmentMode === "IN_PERSON"
                      ? "border-indigo-500 bg-indigo-950/40 text-white"
                      : "border-slate-800 bg-slate-950 text-slate-400 hover:bg-slate-800"
                  }`}
                >
                  <MapPin className="h-3.5 w-3.5" />
                  In-Person
                </button>
                <button
                  type="button"
                  onClick={() => setAppointmentMode("ONLINE")}
                  className={`flex items-center justify-center gap-2 p-2.5 rounded-lg border text-xs font-medium transition ${
                    appointmentMode === "ONLINE"
                      ? "border-indigo-500 bg-indigo-950/40 text-white"
                      : "border-slate-800 bg-slate-950 text-slate-400 hover:bg-slate-800"
                  }`}
                >
                  <Video className="h-3.5 w-3.5" />
                  Secure Online
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Date *</label>
                <Input
                  required
                  type="date"
                  value={preferredDate}
                  onChange={(e) => setPreferredDate(e.target.value)}
                  className="bg-slate-950 border-slate-800 text-xs"
                />
              </div>
              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Time Slot *</label>
                <Input
                  required
                  type="time"
                  value={preferredTime}
                  onChange={(e) => setPreferredTime(e.target.value)}
                  className="bg-slate-950 border-slate-800 text-xs"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-slate-400 font-medium">Brief Note (Optional)</label>
              <Textarea
                placeholder="What topics or guidance would you like to focus on?"
                value={studentNotes}
                onChange={(e) => setStudentNotes(e.target.value)}
                className="bg-slate-950 border-slate-800 text-xs"
                rows={3}
              />
              <p className="text-[10px] text-slate-500">
                Please do not include clinical medical details in intake notes.
              </p>
            </div>

            <Button
              type="submit"
              disabled={submitting}
              className="w-full bg-rose-600 hover:bg-rose-700 text-xs text-white"
            >
              {submitting ? "Booking..." : "Submit Confidential Request"}
            </Button>
          </form>
        </Card>

        {/* Existing Appointments (Right 2 Columns) */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="border-slate-800 bg-slate-900/60 p-5">
            <h2 className="text-base font-semibold text-white mb-3">Your Counselling Appointments</h2>

            {loading ? (
              <div className="py-8 text-center text-xs text-slate-500">Loading appointments...</div>
            ) : appointments.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-500">
                You have no current or past counselling appointments booked.
              </div>
            ) : (
              <div className="space-y-3">
                {appointments.map((appt) => (
                  <div
                    key={appt.id}
                    className="p-4 rounded-xl border border-slate-800 bg-slate-950/40 space-y-3"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm text-white">{appt.appointment_number}</span>
                        <Badge
                          variant="outline"
                          className={
                            appt.status === "CONFIRMED"
                              ? "border-emerald-500/30 text-emerald-400 bg-emerald-500/10 text-[10px]"
                              : appt.status === "BOOKED"
                              ? "border-blue-500/30 text-blue-400 bg-blue-500/10 text-[10px]"
                              : appt.status === "COMPLETED"
                              ? "border-teal-500/30 text-teal-400 bg-teal-500/10 text-[10px]"
                              : appt.status === "CANCELLED"
                              ? "border-rose-500/30 text-rose-400 bg-rose-500/10 text-[10px]"
                              : "border-slate-700 text-slate-400 text-[10px]"
                          }
                        >
                          {appt.status}
                        </Badge>
                        <span className="text-[11px] text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                          {appt.category.replace("_", " ")}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400 flex items-center gap-2">
                        {appt.appointment_mode === "ONLINE" ? (
                          <span className="flex items-center gap-1 text-cyan-400">
                            <Video className="h-3.5 w-3.5" /> Virtual Meeting
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-indigo-400">
                            <MapPin className="h-3.5 w-3.5" /> In-Person Cabin
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-slate-400">
                      <div>
                        <span>Date & Time: </span>
                        <strong className="text-slate-200">
                          {new Date(appt.scheduled_start || appt.appointmentDate || "").toLocaleDateString()} at{" "}
                          {new Date(appt.scheduled_start || appt.appointmentDate || "").toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </strong>
                      </div>
                      <div>
                        <span>Counsellor: </span>
                        <strong className="text-slate-200">{appt.counsellor_name ?? "Assigned Professional"}</strong>
                      </div>
                    </div>

                    {appt.location && (
                      <div className="text-xs text-slate-400">
                        <span>Location / Connection: </span>
                        <span className="text-slate-300">{appt.location}</span>
                      </div>
                    )}

                    {/* Reschedule / Cancel action buttons if active */}
                    {(appt.status === "BOOKED" || appt.status === "CONFIRMED") && (
                      <div className="pt-2 flex justify-end gap-2 border-t border-slate-800/60">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSelectedAppt(appt);
                            setActionType("RESCHEDULE");
                            setActionModalOpen(true);
                          }}
                          className="text-xs text-indigo-400 hover:text-indigo-300"
                        >
                          <RotateCcw className="mr-1 h-3.5 w-3.5" />
                          Reschedule
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSelectedAppt(appt);
                            setActionType("CANCEL");
                            setActionModalOpen(true);
                          }}
                          className="text-xs text-rose-400 hover:text-rose-300"
                        >
                          <XCircle className="mr-1 h-3.5 w-3.5" />
                          Cancel
                        </Button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Reschedule / Cancel Modal */}
      <Dialog open={actionModalOpen} onOpenChange={setActionModalOpen}>
        <DialogContent className="max-w-md bg-slate-900 border-slate-800 text-white">
          <DialogHeader>
            <DialogTitle className="text-base font-bold flex items-center gap-2">
              {actionType === "CANCEL" ? (
                <>
                  <XCircle className="h-4 w-4 text-rose-400" />
                  Cancel Counselling Appointment
                </>
              ) : (
                <>
                  <RotateCcw className="h-4 w-4 text-indigo-400" />
                  Reschedule Appointment
                </>
              )}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleConfirmAction} className="space-y-4 pt-2 text-xs">
            {actionType === "RESCHEDULE" && (
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-slate-400">New Date *</label>
                  <Input
                    required
                    type="date"
                    value={rescheduleDate}
                    onChange={(e) => setRescheduleDate(e.target.value)}
                    className="bg-slate-950 border-slate-800 text-xs"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-slate-400">New Time *</label>
                  <Input
                    required
                    type="time"
                    value={rescheduleTime}
                    onChange={(e) => setRescheduleTime(e.target.value)}
                    className="bg-slate-950 border-slate-800 text-xs"
                  />
                </div>
              </div>
            )}

            <div className="space-y-1">
              <label className="text-slate-400">Reason for {actionType === "CANCEL" ? "Cancellation" : "Rescheduling"} *</label>
              <Input
                required
                placeholder="e.g. Schedule clash with lab exam"
                value={actionReason}
                onChange={(e) => setActionReason(e.target.value)}
                className="bg-slate-950 border-slate-800 text-xs"
              />
            </div>

            <DialogFooter className="pt-2">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setActionModalOpen(false)}
                className="text-xs text-slate-400"
              >
                Back
              </Button>
              <Button
                type="submit"
                disabled={processingAction}
                className={
                  actionType === "CANCEL"
                    ? "bg-rose-600 hover:bg-rose-700 text-xs text-white"
                    : "bg-indigo-600 hover:bg-indigo-700 text-xs text-white"
                }
              >
                {processingAction ? "Processing..." : `Confirm ${actionType === "CANCEL" ? "Cancellation" : "Reschedule"}`}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
