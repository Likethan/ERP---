"use client";

import React, { useEffect, useState } from "react";
import {
  Siren,
  AlertTriangle,
  Flame,
  CheckCircle2,
  Clock,
  Radio,
  FileCheck2,
  Plus,
  ShieldCheck,
  Building2,
  Users,
  Compass,
  ListTodo,
} from "lucide-react";
import { SecurityNav } from "@/components/campus-security/security-nav";
import { CampusSecurityService } from "@/services/campus-security.service";
import {
  EmergencyEvent,
  EmergencyEventType,
  EmergencyResponseTask,
  EmergencySeverity,
  EmergencyStatus,
} from "@/types/campus-security";

export default function EmergencyResponsePage() {
  const [events, setEvents] = useState<EmergencyEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);

  // Modals
  const [isInitiateModalOpen, setIsInitiateModalOpen] = useState(false);
  const [initiating, setInitiating] = useState(false);

  const [completingTask, setCompletingTask] = useState<EmergencyResponseTask | null>(null);
  const [taskNotes, setTaskNotes] = useState("");
  const [taskSubmitting, setTaskSubmitting] = useState(false);

  const [isAarModalOpen, setIsAarModalOpen] = useState(false);
  const [aarReport, setAarReport] = useState("");
  const [aarSubmitting, setAarSubmitting] = useState(false);

  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // Form for new event
  const [eventForm, setEventForm] = useState({
    title: "",
    event_type: "FIRE_ALARM" as EmergencyEventType,
    severity: "EMERGENCY" as EmergencySeverity,
    affected_campus_areas: "Block B & Engineering Concourse",
    coordinator_name: "Chief Safety Officer",
    emergency_broadcast_message: "Code Amber: Evacuate Block B immediately to Assembly Point 2.",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await CampusSecurityService.listEmergencyEvents();
      setEvents(data);
      if (data.length > 0 && !selectedEventId) {
        // Default select first active or first event
        const active = data.find((e) => e.status === "ACTIVE" || e.status === "CONTAINED");
        setSelectedEventId(active ? active.id : data[0].id);
      }
    } catch (err) {
      console.error("Failed to load emergency events:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleInitiateEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!eventForm.title || !eventForm.affected_campus_areas) return;

    try {
      setInitiating(true);
      const newEvent = await CampusSecurityService.initiateEmergencyEvent({
        title: eventForm.title,
        event_type: eventForm.event_type,
        severity: eventForm.severity,
        affected_campus_areas: eventForm.affected_campus_areas,
        coordinator_name: eventForm.coordinator_name,
        emergency_broadcast_message: eventForm.emergency_broadcast_message,
      });

      setNotification({
        type: "success",
        message: `EMERGENCY ALERT BROADCASTED: "${eventForm.title}". Emergency protocols activated.`,
      });
      setIsInitiateModalOpen(false);
      setSelectedEventId(newEvent.id);
      await loadData();
    } catch {
      setNotification({
        type: "error",
        message: "Failed to broadcast emergency event.",
      });
    } finally {
      setInitiating(false);
    }
  };

  const handleCompleteTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!completingTask) return;

    try {
      setTaskSubmitting(true);
      await CampusSecurityService.completeEmergencyTask(completingTask.id, taskNotes);
      setNotification({
        type: "success",
        message: `Task "${completingTask.task_title}" marked as COMPLETED.`,
      });
      setCompletingTask(null);
      setTaskNotes("");
      await loadData();
    } catch {
      setNotification({
        type: "error",
        message: "Failed to update emergency task.",
      });
    } finally {
      setTaskSubmitting(false);
    }
  };

  const handleSubmitAar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEventId || !aarReport) return;

    try {
      setAarSubmitting(true);
      await CampusSecurityService.submitAfterActionReport(selectedEventId, aarReport);
      setNotification({
        type: "success",
        message: "After-Action Report (AAR) successfully archived into institutional audit records.",
      });
      setIsAarModalOpen(false);
      setAarReport("");
      await loadData();
    } catch {
      setNotification({
        type: "error",
        message: "Failed to submit After-Action Report.",
      });
    } finally {
      setAarSubmitting(false);
    }
  };

  const handleCloseEvent = async (eventId: string) => {
    try {
      await CampusSecurityService.closeEmergencyEvent(eventId);
      setNotification({
        type: "success",
        message: "Emergency event safely closed. Normal campus operations restored.",
      });
      await loadData();
    } catch {
      setNotification({
        type: "error",
        message: "Failed to close emergency event.",
      });
    }
  };

  const selectedEvent = events.find((e) => e.id === selectedEventId) || events[0];
  const activeEvents = events.filter((e) => e.status === "ACTIVE" || e.status === "CONTAINED");

  const getSeverityBadge = (severity: EmergencySeverity) => {
    switch (severity) {
      case "CATASTROPHIC":
      case "EMERGENCY":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-bold bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300 border border-red-300 dark:border-red-800 animate-pulse">
            <Flame className="w-3.5 h-3.5 text-red-600" /> {severity}
          </span>
        );
      case "WARNING":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" /> WARNING
          </span>
        );
      case "ADVISORY":
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300">
            ADVISORY
          </span>
        );
    }
  };

  const getStatusBadge = (status: EmergencyStatus) => {
    switch (status) {
      case "ACTIVE":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300 border border-red-300 animate-pulse">
            <Siren className="w-3.5 h-3.5 text-red-600" /> ACTIVE CRISIS
          </span>
        );
      case "CONTAINED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300 border border-amber-300">
            CONTAINED
          </span>
        );
      case "ALL_CLEAR":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300 border border-emerald-300">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> ALL CLEAR
          </span>
        );
      case "CLOSED":
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
            CLOSED & ARCHIVED
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-4 md:p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Emergency Response & Crisis Operations
            </h1>
            <span className="px-2.5 py-0.5 text-xs font-medium rounded-full bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300 border border-red-200 dark:border-red-800">
              Crisis Command
            </span>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Institutional broadcast alerts, evacuation coordination, first-responder checklist tracking, and after-action reporting.
          </p>
        </div>

        <button
          onClick={() => setIsInitiateModalOpen(true)}
          className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-bold shadow-sm transition-colors"
        >
          <Siren className="w-4 h-4 animate-bounce" />
          Initiate Emergency Event
        </button>
      </div>

      {/* Nav */}
      <SecurityNav />

      {/* Notification banner */}
      {notification && (
        <div
          className={`p-4 rounded-lg flex items-center justify-between text-sm ${
            notification.type === "success"
              ? "bg-emerald-50 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-200 border border-emerald-200 dark:border-emerald-800"
              : "bg-red-50 text-red-800 dark:bg-red-950/50 dark:text-red-200 border border-red-200 dark:border-red-800"
          }`}
        >
          <span>{notification.message}</span>
          <button
            onClick={() => setNotification(null)}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-xs font-bold"
          >
            DISMISS
          </button>
        </div>
      )}

      {/* Active Crisis Banner if active events exist */}
      {activeEvents.length > 0 && (
        <div className="p-5 bg-gradient-to-r from-red-600 to-rose-700 text-white rounded-xl shadow-lg border border-red-500 space-y-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2 font-bold text-lg">
              <Siren className="w-6 h-6 animate-pulse" />
              <span>ACTIVE CRISIS IN PROGRESS — EMERGENCY PROTOCOLS ENGAGED</span>
            </div>
            <span className="px-3 py-1 bg-white/20 rounded-full text-xs font-semibold uppercase tracking-wider backdrop-blur-sm">
              {activeEvents.length} Active Event{activeEvents.length > 1 ? "s" : ""}
            </span>
          </div>

          <div className="bg-white/10 rounded-lg p-3 text-sm backdrop-blur-sm">
            <div className="font-semibold text-white/90">
              Primary Threat: {activeEvents[0].title} ({activeEvents[0].event_type})
            </div>
            <div className="text-white/80 text-xs mt-1">
              Affected Areas: <strong>{activeEvents[0].affected_campus_areas}</strong> | Incident Coordinator:{" "}
              <strong>{activeEvents[0].coordinator_name}</strong>
            </div>
            {activeEvents[0].emergency_broadcast_message && (
              <div className="mt-2 text-xs bg-black/20 p-2 rounded text-white font-mono flex items-center gap-2">
                <Radio className="w-4 h-4 shrink-0 text-red-300 animate-pulse" />
                <span>Broadcast: "{activeEvents[0].emergency_broadcast_message}"</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Events List */}
        <div className="lg:col-span-1 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Emergency Events ({events.length})
            </h2>
          </div>

          <div className="space-y-3">
            {loading ? (
              <div className="p-8 text-center text-slate-400 text-sm bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800">
                Loading crisis records...
              </div>
            ) : events.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-sm bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800">
                No emergency events recorded.
              </div>
            ) : (
              events.map((ev) => (
                <div
                  key={ev.id}
                  onClick={() => setSelectedEventId(ev.id)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    selectedEventId === ev.id
                      ? "bg-white dark:bg-slate-900 border-indigo-500 shadow-md ring-1 ring-indigo-500"
                      : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-indigo-600 dark:text-indigo-400">
                      {ev.event_code}
                    </span>
                    {getStatusBadge(ev.status)}
                  </div>
                  <h3 className="font-bold text-slate-900 dark:text-white mt-1 text-sm">{ev.title}</h3>
                  <div className="flex items-center gap-2 mt-2 text-xs text-slate-500">
                    <span>{ev.event_type.replace(/_/g, " ")}</span>
                    <span>•</span>
                    {getSeverityBadge(ev.severity)}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-2 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(ev.initiated_at).toLocaleString()}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Selected Event Detail, Tasks & After-Action Report */}
        <div className="lg:col-span-2 space-y-6">
          {selectedEvent ? (
            <>
              {/* Event Details Card */}
              <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800 pb-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-xl font-bold text-slate-900 dark:text-white">{selectedEvent.title}</h2>
                      {getStatusBadge(selectedEvent.status)}
                    </div>
                    <div className="font-mono text-xs text-slate-500 mt-0.5">
                      Code: {selectedEvent.event_code} | Initiated: {new Date(selectedEvent.initiated_at).toLocaleString()}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {selectedEvent.status !== "CLOSED" && (
                      <button
                        onClick={() => handleCloseEvent(selectedEvent.id)}
                        className="px-3 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 rounded-lg transition-colors"
                      >
                        Declare All-Clear & Close
                      </button>
                    )}
                    <button
                      onClick={() => setIsAarModalOpen(true)}
                      className="px-3 py-1.5 text-xs font-semibold text-indigo-700 dark:text-indigo-300 bg-indigo-50 dark:bg-indigo-950/50 hover:bg-indigo-100 rounded-lg border border-indigo-200 dark:border-indigo-800 transition-colors"
                    >
                      File AAR Report
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs bg-slate-50 dark:bg-slate-800/40 p-4 rounded-lg">
                  <div>
                    <span className="text-slate-500 uppercase font-semibold">Affected Campus Areas:</span>
                    <div className="font-medium text-slate-900 dark:text-slate-200 mt-0.5">
                      {selectedEvent.affected_campus_areas}
                    </div>
                  </div>
                  <div>
                    <span className="text-slate-500 uppercase font-semibold">Incident Commander:</span>
                    <div className="font-medium text-slate-900 dark:text-slate-200 mt-0.5">
                      {selectedEvent.coordinator_name}
                    </div>
                  </div>
                </div>

                {selectedEvent.emergency_broadcast_message && (
                  <div className="p-3 bg-red-50 dark:bg-red-950/30 rounded-lg border border-red-200 dark:border-red-900/40 text-xs">
                    <span className="font-bold text-red-800 dark:text-red-300 flex items-center gap-1 mb-1">
                      <Radio className="w-3.5 h-3.5" /> Broadcast Message
                    </span>
                    <p className="text-red-700 dark:text-red-200 font-mono">
                      "{selectedEvent.emergency_broadcast_message}"
                    </p>
                  </div>
                )}

                {/* After-Action Report summary if exists */}
                {selectedEvent.after_action_report && (
                  <div className="p-4 bg-emerald-50 dark:bg-emerald-950/30 rounded-lg border border-emerald-200 dark:border-emerald-900/40 text-xs space-y-1">
                    <div className="font-bold text-emerald-800 dark:text-emerald-300 flex items-center gap-1.5">
                      <FileCheck2 className="w-4 h-4 text-emerald-600" />
                      After-Action Report (AAR) Archival
                    </div>
                    <p className="text-emerald-700 dark:text-emerald-200 whitespace-pre-line mt-1">
                      {selectedEvent.after_action_report}
                    </p>
                  </div>
                )}
              </div>

              {/* Response Tasks Section */}
              <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
                  <div className="flex items-center gap-2">
                    <ListTodo className="w-5 h-5 text-indigo-600" />
                    <h3 className="font-bold text-slate-900 dark:text-white text-base">
                      Response Tasks & Execution Checklist
                    </h3>
                  </div>
                  <span className="text-xs text-slate-500">
                    {selectedEvent.tasks?.filter((t) => t.status === "COMPLETED").length || 0} of{" "}
                    {selectedEvent.tasks?.length || 0} Tasks Completed
                  </span>
                </div>

                <div className="space-y-3">
                  {!selectedEvent.tasks || selectedEvent.tasks.length === 0 ? (
                    <div className="text-center py-6 text-slate-400 text-xs">
                      No response checklist tasks generated for this emergency event.
                    </div>
                  ) : (
                    selectedEvent.tasks.map((task) => (
                      <div
                        key={task.id}
                        className={`p-4 rounded-lg border transition-all ${
                          task.status === "COMPLETED"
                            ? "bg-slate-50/50 dark:bg-slate-800/30 border-slate-200 dark:border-slate-800 opacity-80"
                            : "bg-white dark:bg-slate-800/60 border-indigo-100 dark:border-indigo-900/40 shadow-sm"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <span
                                className={`font-semibold text-sm ${
                                  task.status === "COMPLETED"
                                    ? "line-through text-slate-500"
                                    : "text-slate-900 dark:text-white"
                                }`}
                              >
                                {task.task_title}
                              </span>
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                                  task.priority === "URGENT"
                                    ? "bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300"
                                    : "bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300"
                                }`}
                              >
                                {task.priority}
                              </span>
                            </div>

                            <div className="text-xs text-slate-500 flex items-center gap-2">
                              <span>Role: {task.assigned_to_role || "Incident Command"}</span>
                              {task.completed_at && (
                                <span>• Completed: {new Date(task.completed_at).toLocaleTimeString()}</span>
                              )}
                            </div>

                            {task.notes && (
                              <div className="text-xs text-slate-600 dark:text-slate-300 italic bg-white dark:bg-slate-900 p-2 rounded border border-slate-100 dark:border-slate-800 mt-1">
                                Note: {task.notes}
                              </div>
                            )}
                          </div>

                          {task.status !== "COMPLETED" && (
                            <button
                              onClick={() => setCompletingTask(task)}
                              className="px-3 py-1.5 text-xs font-semibold text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/50 hover:bg-emerald-100 rounded-lg border border-emerald-200 dark:border-emerald-800 shrink-0"
                            >
                              Complete Task
                            </button>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="p-12 text-center text-slate-400 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800">
              Select an emergency event to view crisis coordination details.
            </div>
          )}
        </div>
      </div>

      {/* Initiate Event Modal */}
      {isInitiateModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 w-full max-w-lg shadow-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <h2 className="text-lg font-bold text-red-600 dark:text-red-400 flex items-center gap-2">
                <Siren className="w-5 h-5 animate-pulse" />
                Initiate Campus Emergency Protocol
              </h2>
              <button
                onClick={() => setIsInitiateModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleInitiateEvent} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                  Emergency Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Chemical Fume Alert in Chemistry Complex"
                  value={eventForm.title}
                  onChange={(e) => setEventForm({ ...eventForm, title: e.target.value })}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                    Event Type *
                  </label>
                  <select
                    value={eventForm.event_type}
                    onChange={(e) => setEventForm({ ...eventForm, event_type: e.target.value as any })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                  >
                    <option value="FIRE_ALARM">Fire Alarm / Smoke</option>
                    <option value="SEVERE_WEATHER">Severe Weather / Storm</option>
                    <option value="MEDICAL_EMERGENCY">Medical Emergency</option>
                    <option value="ACTIVE_THREAT">Active Security Threat</option>
                    <option value="INFRASTRUCTURE_FAILURE">Power / Infrastructure Failure</option>
                    <option value="HAZMAT_LEAK">Hazardous Materials Leak</option>
                    <option value="NATURAL_DISASTER">Earthquake / Flood</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                    Severity Level *
                  </label>
                  <select
                    value={eventForm.severity}
                    onChange={(e) => setEventForm({ ...eventForm, severity: e.target.value as any })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                  >
                    <option value="ADVISORY">ADVISORY</option>
                    <option value="WARNING">WARNING</option>
                    <option value="EMERGENCY">EMERGENCY</option>
                    <option value="CATASTROPHIC">CATASTROPHIC</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                    Affected Campus Areas *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. North Quad, Library Wing"
                    value={eventForm.affected_campus_areas}
                    onChange={(e) => setEventForm({ ...eventForm, affected_campus_areas: e.target.value })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                    Incident Coordinator *
                  </label>
                  <input
                    type="text"
                    required
                    value={eventForm.coordinator_name}
                    onChange={(e) => setEventForm({ ...eventForm, coordinator_name: e.target.value })}
                    className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                  Public Broadcast Alert Message *
                </label>
                <textarea
                  rows={3}
                  required
                  placeholder="Immediate instruction sent to digital signage, PA loudspeakers, and mobile notifications..."
                  value={eventForm.emergency_broadcast_message}
                  onChange={(e) => setEventForm({ ...eventForm, emergency_broadcast_message: e.target.value })}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white font-mono"
                />
              </div>

              <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsInitiateModalOpen(false)}
                  className="px-4 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={initiating}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-bold disabled:opacity-50"
                >
                  {initiating ? "Activating..." : "Broadcast & Activate Protocol"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Complete Task Modal */}
      {completingTask && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 w-full max-w-md shadow-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                Sign Off Task Execution
              </h2>
              <button
                onClick={() => setCompletingTask(null)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCompleteTask} className="p-6 space-y-4">
              <p className="text-sm font-semibold text-slate-900 dark:text-white">
                Task: {completingTask.task_title}
              </p>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                  Execution Notes / Observations
                </label>
                <textarea
                  rows={3}
                  placeholder="e.g. All occupants successfully marshaled at Assembly Point 2 with zero injuries..."
                  value={taskNotes}
                  onChange={(e) => setTaskNotes(e.target.value)}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                />
              </div>

              <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setCompletingTask(null)}
                  className="px-4 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={taskSubmitting}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-medium disabled:opacity-50"
                >
                  {taskSubmitting ? "Completing..." : "Confirm Task Completion"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* After-Action Report Modal */}
      {isAarModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 w-full max-w-lg shadow-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <FileCheck2 className="w-5 h-5 text-indigo-600" />
                Submit After-Action Report (AAR)
              </h2>
              <button
                onClick={() => setIsAarModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmitAar} className="p-6 space-y-4">
              <p className="text-xs text-slate-500">
                The After-Action Report is permanently archived for institutional accreditation, regulatory compliance, and security drill assessment.
              </p>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
                  Incident Review, Timeline & Lessons Learned *
                </label>
                <textarea
                  rows={6}
                  required
                  placeholder="Detail trigger time, emergency response time, inter-agency communication, evacuation duration, identified deficiencies, and preventative mitigation..."
                  value={aarReport}
                  onChange={(e) => setAarReport(e.target.value)}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-white"
                />
              </div>

              <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsAarModalOpen(false)}
                  className="px-4 py-2 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={aarSubmitting}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium disabled:opacity-50"
                >
                  {aarSubmitting ? "Archiving..." : "Archive AAR Report"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

