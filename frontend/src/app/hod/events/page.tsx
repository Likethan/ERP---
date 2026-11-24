"use client";

import React, { useEffect, useState } from "react";
import {
  PartyPopper,
  Calendar,
  Clock,
  MapPin,
  Users,
  DollarSign,
  FileText,
  Plus,
  CheckCircle2,
  AlertCircle,
  Search,
  Filter,
  Download,
  Upload,
  ExternalLink,
  X,
  ChevronRight,
  Sparkles,
} from "lucide-react";
import {
  hodService,
  HodEventItem,
  HodEventsData,
  HodEventCreatePayload,
  HodEventReportPayload,
} from "@/services/hod.service";
import { useToast } from "@/components/ui/toast";

export default function HodEventsPage() {
  const { addToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<HodEventsData | null>(null);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [categoryFilter, setCategoryFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedEvent, setSelectedEvent] = useState<HodEventItem | null>(null);

  // New Event Modal State
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newCategory, setNewCategory] = useState("Workshop");
  const [newDate, setNewDate] = useState("");
  const [newVenue, setNewVenue] = useState("");
  const [newFacCoord, setNewFacCoord] = useState("Dr. Priya Nair");
  const [newStudCoord, setNewStudCoord] = useState("");
  const [newTarget, setNewTarget] = useState("All CSE Students");
  const [newExpected, setNewExpected] = useState("80");
  const [newBudget, setNewBudget] = useState("25000");

  // Report Modal State
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [submittingReport, setSubmittingReport] = useState(false);
  const [actualParticipants, setActualParticipants] = useState("");
  const [outcomes, setOutcomes] = useState("");
  const [photosCount, setPhotosCount] = useState("10");
  const [completionRemarks, setCompletionRemarks] = useState("");

  const loadEvents = async () => {
    try {
      setLoading(true);
      const res = await hodService.getDepartmentEvents(
        statusFilter,
        categoryFilter,
      );
      if (res.data) {
        setData(res.data);
      }
    } catch {
      addToast({
        title: "Error Loading Events",
        description: "Failed to retrieve department events data.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
  }, [statusFilter, categoryFilter]);

  const handleCreateEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newDate || !newVenue.trim()) {
      addToast({
        title: "Required Fields Missing",
        description: "Please enter event title, date, and venue.",
        variant: "destructive",
      });
      return;
    }

    try {
      setCreating(true);
      const payload: HodEventCreatePayload = {
        title: newTitle.trim(),
        description: newDesc.trim() || "Department academic event.",
        category: newCategory,
        startDate: newDate,
        venue: newVenue.trim(),
        facultyCoordinator: newFacCoord,
        studentCoordinator: newStudCoord.trim() || undefined,
        targetAudience: newTarget,
        expectedParticipants: parseInt(newExpected, 10) || 50,
        budget: parseFloat(newBudget) || 0,
      };

      const res = await hodService.createDepartmentEvent(payload);
      if (res.success && res.data) {
        addToast({
          title: "Event Scheduled",
          description: `"${res.data.title}" has been registered into the academic calendar.`,
          variant: "success",
        });
        setCreateModalOpen(false);
        resetCreateForm();
        loadEvents();
      }
    } catch {
      addToast({
        title: "Creation Failed",
        description: "Unable to schedule new event.",
        variant: "destructive",
      });
    } finally {
      setCreating(false);
    }
  };

  const resetCreateForm = () => {
    setNewTitle("");
    setNewDesc("");
    setNewCategory("Workshop");
    setNewDate("");
    setNewVenue("");
    setNewStudCoord("");
    setNewExpected("80");
    setNewBudget("25000");
  };

  const handleSubmitReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEvent) return;
    if (!actualParticipants || !outcomes.trim()) {
      addToast({
        title: "Report Incomplete",
        description: "Please specify actual participants count and outcomes.",
        variant: "destructive",
      });
      return;
    }

    try {
      setSubmittingReport(true);
      const payload: HodEventReportPayload = {
        actualParticipants: parseInt(actualParticipants, 10) || 0,
        outcomes: outcomes.trim(),
        photosCount: parseInt(photosCount, 10) || 0,
        completionRemarks:
          completionRemarks.trim() || "Event completed successfully.",
      };

      const res = await hodService.submitEventReport(selectedEvent.id, payload);
      if (res.success && res.data) {
        addToast({
          title: "Completion Report Submitted",
          description: `Event "${selectedEvent.title}" marked COMPLETED with audit documentation.`,
          variant: "success",
        });
        setReportModalOpen(false);
        setSelectedEvent(res.data);
        loadEvents();
      }
    } catch {
      addToast({
        title: "Report Submission Failed",
        description: "Could not submit event completion report.",
        variant: "destructive",
      });
    } finally {
      setSubmittingReport(false);
    }
  };

  const filteredEvents = (data?.events || []).filter((event) => {
    if (!searchQuery.trim()) return true;
    const query = searchQuery.toLowerCase();
    return (
      event.title.toLowerCase().includes(query) ||
      event.category.toLowerCase().includes(query) ||
      event.facultyCoordinator.toLowerCase().includes(query) ||
      event.venue.toLowerCase().includes(query)
    );
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "COMPLETED":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="h-3 w-3" /> Completed
          </span>
        );
      case "UPCOMING":
      case "SCHEDULED":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-semibold text-blue-700 border border-blue-200">
            <Calendar className="h-3 w-3" /> Upcoming
          </span>
        );
      case "ONGOING":
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-700 border border-amber-200 animate-pulse">
            <Sparkles className="h-3 w-3" /> In Progress
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600 border border-slate-200">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 p-6">
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Department Events & Activities
            </h1>
            <span className="rounded-md bg-yellow-100 px-2.5 py-0.5 text-xs font-bold text-yellow-800 border border-yellow-300">
              CSE Co-Curricular Hub
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Monitor symposia, national hackathons, technical workshops, FDPs,
            and industrial visits.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setCreateModalOpen(true)}
            className="inline-flex items-center gap-2 rounded-lg bg-yellow-400 px-4 py-2.5 text-sm font-semibold text-slate-950 shadow-xs hover:bg-yellow-300 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Schedule New Event
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">
              Total Events
            </span>
            <PartyPopper className="h-4 w-4 text-slate-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">
            {data?.summary.totalEvents || 5}
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            Academic Year 2025-26
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">Upcoming</span>
            <Calendar className="h-4 w-4 text-blue-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-blue-600">
            {data?.summary.upcomingEvents || 2}
          </div>
          <div className="mt-1 text-[11px] text-blue-600/80 font-medium">
            Active in calendar
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">
              Completed & Documented
            </span>
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-emerald-600">
            {data?.summary.completedEvents || 3}
          </div>
          <div className="mt-1 text-[11px] text-emerald-600/80 font-medium">
            With submitted reports
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">
              Total Beneficiaries
            </span>
            <Users className="h-4 w-4 text-purple-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">
            {data?.summary.totalParticipants || 396}
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            Students & Faculty
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">
              Sanctioned Budget
            </span>
            <DollarSign className="h-4 w-4 text-amber-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">
            ₹{((data?.summary.totalBudget || 177000) / 1000).toFixed(0)}k
          </div>
          <div className="mt-1 text-[11px] text-slate-500">
            Total grant allocated
          </div>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-xs sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search events by title, coordinator, category, venue..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-slate-200 pl-9 pr-4 py-2 text-sm focus:border-yellow-400 focus:outline-hidden focus:ring-1 focus:ring-yellow-400"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-700 focus:outline-hidden"
          >
            <option value="ALL">All Categories</option>
            <option value="Hackathon">Hackathon</option>
            <option value="Workshop">Workshop</option>
            <option value="Guest Lecture">Guest Lecture</option>
            <option value="Industrial Visit">Industrial Visit</option>
            <option value="Faculty Development Program">FDP</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-700 focus:outline-hidden"
          >
            <option value="ALL">All Statuses</option>
            <option value="UPCOMING">Upcoming</option>
            <option value="SCHEDULED">Scheduled</option>
            <option value="COMPLETED">Completed</option>
          </select>
        </div>
      </div>

      {/* Events Roster Table */}
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xs">
        <div className="border-b border-slate-200 px-5 py-3.5 flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900">
            Registered Department Events ({filteredEvents.length})
          </h2>
          <span className="text-xs text-slate-500 font-mono">
            Department: Computer Science & Engineering
          </span>
        </div>

        {loading ? (
          <div className="p-8 text-center text-sm text-slate-500">
            Loading department events...
          </div>
        ) : filteredEvents.length === 0 ? (
          <div className="p-8 text-center text-sm text-slate-500">
            No events match your criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold text-[11px]">
                <tr>
                  <th className="px-5 py-3">Event Title & Category</th>
                  <th className="px-4 py-3">Date & Venue</th>
                  <th className="px-4 py-3">Coordinators</th>
                  <th className="px-4 py-3 text-center">Participation</th>
                  <th className="px-4 py-3 text-right">Budget</th>
                  <th className="px-4 py-3 text-center">Status</th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredEvents.map((evt) => (
                  <tr
                    key={evt.id}
                    className="hover:bg-yellow-50/40 transition-colors"
                  >
                    <td className="px-5 py-3.5">
                      <div className="font-semibold text-slate-900 text-sm">
                        {evt.title}
                      </div>
                      <div className="flex items-center gap-2 mt-0.5 text-slate-500">
                        <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-700 border border-slate-200">
                          {evt.category}
                        </span>
                        <span className="text-[11px] text-slate-400">
                          ID: {evt.id}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="flex items-center gap-1.5 font-medium text-slate-800">
                        <Calendar className="h-3.5 w-3.5 text-slate-400" />
                        {evt.startDate}
                      </div>
                      <div className="flex items-center gap-1.5 mt-0.5 text-slate-500">
                        <MapPin className="h-3.5 w-3.5 text-slate-400" />
                        <span className="truncate max-w-[160px]">
                          {evt.venue}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="font-medium text-slate-900">
                        {evt.facultyCoordinator}
                      </div>
                      {evt.studentCoordinator && (
                        <div className="text-[11px] text-slate-500">
                          Student: {evt.studentCoordinator}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3.5 text-center">
                      <span className="font-bold text-slate-900">
                        {evt.actualParticipants > 0
                          ? evt.actualParticipants
                          : evt.expectedParticipants}
                      </span>
                      <span className="text-slate-400 text-[10px] block">
                        {evt.actualParticipants > 0 ? "Attended" : "Expected"}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-right font-mono font-medium text-slate-900">
                      ₹{evt.budget.toLocaleString()}
                    </td>
                    <td className="px-4 py-3.5 text-center">
                      {getStatusBadge(evt.status)}
                    </td>
                    <td className="px-5 py-3.5 text-right space-x-2">
                      <button
                        onClick={() => setSelectedEvent(evt)}
                        className="rounded-md border border-slate-200 px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-100 transition-colors"
                      >
                        Details
                      </button>
                      {evt.status !== "COMPLETED" && (
                        <button
                          onClick={() => {
                            setSelectedEvent(evt);
                            setActualParticipants(
                              evt.expectedParticipants.toString(),
                            );
                            setReportModalOpen(true);
                          }}
                          className="rounded-md bg-yellow-400 px-2.5 py-1 text-xs font-semibold text-slate-950 hover:bg-yellow-300 transition-colors"
                        >
                          Submit Report
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Event Details Drawer/Modal */}
      {selectedEvent && !reportModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-xl border border-slate-200 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <span className="text-xs font-mono text-slate-400">
                  {selectedEvent.id}
                </span>
                <h3 className="text-lg font-bold text-slate-900">
                  {selectedEvent.title}
                </h3>
              </div>
              <button
                onClick={() => setSelectedEvent(null)}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="mt-4 space-y-4 text-xs text-slate-700">
              <p className="text-sm text-slate-600">
                {selectedEvent.description}
              </p>

              <div className="grid grid-cols-2 gap-3 rounded-xl bg-slate-50 p-4 border border-slate-100">
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">
                    Category
                  </span>
                  <span className="font-semibold text-slate-900">
                    {selectedEvent.category}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">
                    Target Audience
                  </span>
                  <span className="font-semibold text-slate-900">
                    {selectedEvent.targetAudience}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">
                    Date & Time
                  </span>
                  <span className="font-semibold text-slate-900">
                    {selectedEvent.startDate} ({selectedEvent.startTime} -{" "}
                    {selectedEvent.endTime})
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">
                    Venue
                  </span>
                  <span className="font-semibold text-slate-900">
                    {selectedEvent.venue}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">
                    Faculty Coordinator
                  </span>
                  <span className="font-semibold text-slate-900">
                    {selectedEvent.facultyCoordinator}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">
                    Budget
                  </span>
                  <span className="font-mono font-semibold text-slate-900">
                    ₹{selectedEvent.budget.toLocaleString()}
                  </span>
                </div>
              </div>

              {selectedEvent.report ? (
                <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-4">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-emerald-900 flex items-center gap-1.5">
                      <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                      Audited Completion Report
                    </span>
                    <span className="text-[10px] text-emerald-700 font-mono">
                      {selectedEvent.report.submittedAt}
                    </span>
                  </div>
                  <p className="mt-2 text-emerald-800">
                    <strong>Outcomes:</strong> {selectedEvent.report.outcomes}
                  </p>
                  <div className="mt-2 flex items-center gap-4 text-[11px] text-emerald-700 font-medium">
                    <span>
                      Actual Participants: {selectedEvent.actualParticipants}
                    </span>
                    <span>
                      Photos Documented: {selectedEvent.report.photosCount}
                    </span>
                    <a
                      href="#"
                      className="underline flex items-center gap-1 hover:text-emerald-900"
                    >
                      View Report PDF <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                </div>
              ) : (
                <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-3 flex items-center justify-between">
                  <span className="text-amber-800 font-medium flex items-center gap-1.5">
                    <AlertCircle className="h-4 w-4 text-amber-600" />
                    Completion report pending submission.
                  </span>
                  <button
                    onClick={() => {
                      setActualParticipants(
                        selectedEvent.expectedParticipants.toString(),
                      );
                      setReportModalOpen(true);
                    }}
                    className="rounded bg-yellow-400 px-3 py-1 font-semibold text-slate-950 text-xs hover:bg-yellow-300"
                  >
                    Submit Report
                  </button>
                </div>
              )}

              {selectedEvent.attachments.length > 0 && (
                <div>
                  <h4 className="font-bold text-slate-900 text-xs mb-2">
                    Supporting Documents
                  </h4>
                  <div className="space-y-1.5">
                    {selectedEvent.attachments.map((att, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between rounded-lg border border-slate-200 p-2 text-xs"
                      >
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 text-slate-400" />
                          <span className="font-medium text-slate-800">
                            {att.name}
                          </span>
                        </div>
                        <span className="text-slate-400 text-[10px]">
                          {att.size}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setSelectedEvent(null)}
                className="rounded-lg border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Schedule Event Modal */}
      {createModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900">
                Schedule Department Event
              </h3>
              <button
                onClick={() => setCreateModalOpen(false)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-100"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form
              onSubmit={handleCreateEvent}
              className="mt-4 space-y-3.5 text-xs"
            >
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Event Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. National Symposium on Quantum Computing"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs focus:border-yellow-400 focus:ring-1 focus:ring-yellow-400"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Category *
                  </label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"
                  >
                    <option value="Workshop">Workshop</option>
                    <option value="Hackathon">Hackathon</option>
                    <option value="Guest Lecture">Guest Lecture</option>
                    <option value="Industrial Visit">Industrial Visit</option>
                    <option value="Faculty Development Program">FDP</option>
                    <option value="Symposium">Technical Symposium</option>
                    <option value="Conference">Conference</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Event Date *
                  </label>
                  <input
                    type="date"
                    required
                    value={newDate}
                    onChange={(e) => setNewDate(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Venue / Lab *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Turing Hall / Lab 4"
                  value={newVenue}
                  onChange={(e) => setNewVenue(e.target.value)}
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Faculty Coordinator *
                  </label>
                  <input
                    type="text"
                    required
                    value={newFacCoord}
                    onChange={(e) => setNewFacCoord(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Student Coordinator
                  </label>
                  <input
                    type="text"
                    placeholder="Name & Roll Number"
                    value={newStudCoord}
                    onChange={(e) => setNewStudCoord(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Expected Participants
                  </label>
                  <input
                    type="number"
                    value={newExpected}
                    onChange={(e) => setNewExpected(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Budget (₹)
                  </label>
                  <input
                    type="number"
                    value={newBudget}
                    onChange={(e) => setNewBudget(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Description & Objectives
                </label>
                <textarea
                  rows={2}
                  placeholder="Outline key learning objectives and delivery plan..."
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"
                />
              </div>

              <div className="mt-5 flex justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setCreateModalOpen(false)}
                  className="rounded-lg border border-slate-200 px-4 py-2 font-medium text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="rounded-lg bg-yellow-400 px-4 py-2 font-semibold text-slate-950 hover:bg-yellow-300 disabled:opacity-50"
                >
                  {creating ? "Scheduling..." : "Confirm & Schedule"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Submit Report Modal */}
      {reportModalOpen && selectedEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900">
                  Submit Event Completion Report
                </h3>
                <span className="text-xs text-slate-500 font-medium">
                  {selectedEvent.title}
                </span>
              </div>
              <button
                onClick={() => setReportModalOpen(false)}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-100"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form
              onSubmit={handleSubmitReport}
              className="mt-4 space-y-3.5 text-xs"
            >
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Actual Participants *
                  </label>
                  <input
                    type="number"
                    required
                    value={actualParticipants}
                    onChange={(e) => setActualParticipants(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Photos Documented
                  </label>
                  <input
                    type="number"
                    value={photosCount}
                    onChange={(e) => setPhotosCount(e.target.value)}
                    className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Key Outcomes & Deliverables *
                </label>
                <textarea
                  rows={3}
                  required
                  placeholder="Detail attendee feedback, project deliverables, internships or seed grants awarded..."
                  value={outcomes}
                  onChange={(e) => setOutcomes(e.target.value)}
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  HOD Remarks & Audit Conclusion
                </label>
                <textarea
                  rows={2}
                  placeholder="Remarks on successful delivery..."
                  value={completionRemarks}
                  onChange={(e) => setCompletionRemarks(e.target.value)}
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"
                />
              </div>

              <div className="mt-5 flex justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setReportModalOpen(false)}
                  className="rounded-lg border border-slate-200 px-4 py-2 font-medium text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingReport}
                  className="rounded-lg bg-yellow-400 px-4 py-2 font-semibold text-slate-950 hover:bg-yellow-300 disabled:opacity-50"
                >
                  {submittingReport ? "Submitting..." : "Submit Report & Close"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
