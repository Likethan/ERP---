"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { StudentSupportService } from "@/services/student-support.service";
import { CounsellingAppointmentItem } from "@/types/student-support";
import { StudentSupportNav } from "@/components/student-support/student-support-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Calendar,
  Clock,
  UserCheck,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Video,
  MapPin,
  Lock,
  Search,
} from "lucide-react";

export default function CounsellingSchedulePage() {
  const [appointments, setAppointments] = useState<CounsellingAppointmentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchDate, setSearchDate] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  useEffect(() => {
    loadSchedule();
  }, []);

  async function loadSchedule() {
    setLoading(true);
    try {
      const data = await StudentSupportService.getCounsellingAppointments();
      setAppointments(data);
    } catch (err) {
      console.error("Failed to load schedule:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleStatusTransition(
    apptId: string,
    newStatus: "CHECKED_IN" | "COMPLETED" | "NO_SHOW" | "CANCELLED"
  ) {
    setUpdatingId(apptId);
    try {
      await StudentSupportService.transitionCounsellingAppointment(apptId, {
        status: newStatus,
        cancellation_reason: newStatus === "NO_SHOW" ? "Student did not attend scheduled session" : undefined,
      });
      loadSchedule();
    } catch (err) {
      console.error("Failed to update status:", err);
      alert("Unable to update appointment status.");
    } finally {
      setUpdatingId(null);
    }
  }

  const filteredAppointments = appointments.filter((a) => {
    const matchesStatus = statusFilter === "ALL" || a.status === statusFilter;
    const matchesDate = !searchDate || (a.scheduled_start || a.appointmentDate || "").startsWith(searchDate);
    return matchesStatus && matchesDate;
  });

  return (
    <div className="space-y-6 pb-12">
      <div>
        <Breadcrumbs
          items={[
            { label: "Dashboard", href: "/app/dashboard" },
            { label: "Student Support", href: "/app/student-support" },
            { label: "Counselling Schedule", href: "/app/student-support/counselling/schedule" },
          ]}
        />
        <div className="mt-2 flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <Calendar className="h-6 w-6 text-indigo-400" />
              Counsellor Agenda & Daily Schedule
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Manage clinical appointments, check-ins, session completions, and transitions.
            </p>
          </div>
          <Link href="/app/student-support/counselling/workspace">
            <Button className="bg-amber-600 hover:bg-amber-700 text-xs text-white">
              <Lock className="mr-1.5 h-3.5 w-3.5" />
              Restricted Clinical Notes
            </Button>
          </Link>
        </div>
      </div>

      <StudentSupportNav />

      {/* Filter and Date Bar */}
      <Card className="border-slate-800 bg-slate-900/60 p-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 flex gap-2">
            <Input
              type="date"
              value={searchDate}
              onChange={(e) => setSearchDate(e.target.value)}
              className="bg-slate-950 border-slate-800 text-xs max-w-xs"
            />
            {searchDate && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSearchDate("")}
                className="text-xs text-slate-400"
              >
                Clear Date
              </Button>
            )}
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-xs text-slate-300"
          >
            <option value="ALL">All States</option>
            <option value="BOOKED">Booked</option>
            <option value="CONFIRMED">Confirmed</option>
            <option value="CHECKED_IN">Checked-In</option>
            <option value="COMPLETED">Completed</option>
            <option value="NO_SHOW">No-Show</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
        </div>
      </Card>

      {/* Appointment Cards / Schedule Agenda */}
      {loading ? (
        <div className="py-12 text-center text-sm text-slate-500">Loading daily appointments...</div>
      ) : filteredAppointments.length === 0 ? (
        <Card className="border-slate-800 bg-slate-900/60 p-8 text-center text-slate-400">
          No counselling appointments found for the selected filter.
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredAppointments.map((appt) => (
            <Card
              key={appt.id}
              className="border-slate-800 bg-slate-900/60 p-5 space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-white text-base">{appt.appointment_number}</span>
                    <Badge
                      variant="outline"
                      className={
                        appt.status === "COMPLETED"
                          ? "border-emerald-500/30 text-emerald-400 bg-emerald-500/10 text-xs"
                          : appt.status === "CONFIRMED"
                          ? "border-blue-500/30 text-blue-400 bg-blue-500/10 text-xs"
                          : appt.status === "CHECKED_IN"
                          ? "border-purple-500/30 text-purple-400 bg-purple-500/10 text-xs"
                          : appt.status === "NO_SHOW"
                          ? "border-amber-500/30 text-amber-400 bg-amber-500/10 text-xs"
                          : "border-slate-700 text-slate-400 text-xs"
                      }
                    >
                      {appt.status}
                    </Badge>
                    <span className="text-xs text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                      {appt.category.replace("_", " ")}
                    </span>
                  </div>
                  <div className="text-xs text-slate-400">
                    Student ID: <span className="text-slate-200">{appt.student_id}</span> • Assigned Counsellor:{" "}
                    <span className="text-slate-200">{appt.counsellor_name ?? "Clinical Counsellor"}</span>
                  </div>
                </div>

                <div className="text-right text-xs">
                  <div className="font-semibold text-indigo-300">
                    {new Date(appt.scheduled_start || appt.appointmentDate || "").toLocaleDateString()} at{" "}
                    {new Date(appt.scheduled_start || appt.appointmentDate || "").toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </div>
                  <div className="text-slate-400 flex items-center justify-end gap-1 mt-0.5">
                    {appt.appointment_mode === "ONLINE" ? (
                      <>
                        <Video className="h-3.5 w-3.5 text-cyan-400" />
                        <span>Online Consultation</span>
                      </>
                    ) : (
                      <>
                        <MapPin className="h-3.5 w-3.5 text-indigo-400" />
                        <span>{appt.location || "Wellness Centre"}</span>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* Status Actions */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
                <div className="text-xs text-slate-400">
                  {appt.check_in_time && (
                    <span className="text-purple-400">
                      Checked in: {new Date(appt.check_in_time).toLocaleTimeString()}
                    </span>
                  )}
                  {appt.completed_at && (
                    <span className="text-emerald-400">
                      Completed: {new Date(appt.completed_at).toLocaleTimeString()}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  {appt.status !== "COMPLETED" && appt.status !== "CANCELLED" && appt.status !== "NO_SHOW" && (
                    <>
                      {appt.status !== "CHECKED_IN" && (
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={updatingId === appt.id}
                          onClick={() => handleStatusTransition(appt.id, "CHECKED_IN")}
                          className="text-xs border-purple-800/40 text-purple-300 hover:bg-purple-950/40"
                        >
                          Check In
                        </Button>
                      )}
                      <Button
                        size="sm"
                        disabled={updatingId === appt.id}
                        onClick={() => handleStatusTransition(appt.id, "COMPLETED")}
                        className="text-xs bg-emerald-600 hover:bg-emerald-700 text-white"
                      >
                        <CheckCircle2 className="mr-1 h-3.5 w-3.5" />
                        Complete Session
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        disabled={updatingId === appt.id}
                        onClick={() => handleStatusTransition(appt.id, "NO_SHOW")}
                        className="text-xs text-amber-400 hover:bg-amber-950/40"
                      >
                        <AlertCircle className="mr-1 h-3.5 w-3.5" />
                        Mark No-Show
                      </Button>
                    </>
                  )}

                  <Link href={`/app/student-support/counselling/workspace?appointment_id=${appt.id}`}>
                    <Button size="sm" variant="outline" className="text-xs border-amber-900/40 text-amber-300 hover:bg-amber-950/40">
                      <Lock className="mr-1 h-3.5 w-3.5" />
                      Session Notes
                    </Button>
                  </Link>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
