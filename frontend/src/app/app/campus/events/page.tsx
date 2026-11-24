"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { campusService } from "@/services/campus.service";
import { CampusEventItem, EventCategory, EventStatus } from "@/types/campus";
import { useAuth } from "@/lib/auth-context";
import { DataGrid, ColumnDef } from "@/components/data-grid/data-grid";
import {
  PartyPopper,
  Plus,
  Calendar,
  Clock,
  MapPin,
  Users,
  Eye,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Download,
  Filter,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";

const ALL_CATEGORIES: EventCategory[] = [
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

const ALL_STATUSES: EventStatus[] = [
  "DRAFT",
  "PENDING_APPROVAL",
  "PUBLISHED",
  "REGISTRATION_OPEN",
  "REGISTRATION_CLOSED",
  "ONGOING",
  "COMPLETED",
  "CANCELLED",
];

export default function CampusEventsListPage() {
  const { user, hasPermission } = useAuth();
  const [events, setEvents] = useState<CampusEventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [categoryFilter, setCategoryFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Action Modals
  const [publishEventId, setPublishEventId] = useState<string | null>(null);
  const [cancelEventId, setCancelEventId] = useState<string | null>(null);
  const [cancelReason, setCancelReason] = useState("");
  const [registerEvent, setRegisterEvent] = useState<CampusEventItem | null>(
    null,
  );
  const [actionLoading, setActionLoading] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  const canCreate = hasPermission("campus.manage_events") || hasPermission("*");
  const canPublish =
    hasPermission("campus.publish_events") || hasPermission("*");

  const loadEvents = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await campusService.getEvents();
      if (res.success && res.data) {
        setEvents(res.data);
      } else {
        setError(res.error || "Failed to load events");
      }
    } catch (e: any) {
      setError(e.message || "An unexpected error occurred");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
  }, []);

  const handlePublish = async () => {
    if (!publishEventId) return;
    try {
      setActionLoading(true);
      await campusService.publishEvent(
        publishEventId,
        user?.first_name || "Administrator",
      );
      setPublishEventId(null);
      setFeedbackMessage("Event has been successfully published!");
      loadEvents();
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!cancelEventId) return;
    try {
      setActionLoading(true);
      await campusService.cancelEvent(
        cancelEventId,
        cancelReason,
        user?.first_name || "Administrator",
      );
      setCancelEventId(null);
      setCancelReason("");
      setFeedbackMessage("Event has been cancelled.");
      loadEvents();
    } finally {
      setActionLoading(false);
    }
  };

  const handleStudentRegister = async () => {
    if (!registerEvent || !user) return;
    try {
      setActionLoading(true);
      const res = await campusService.registerForEvent(registerEvent.id, {
        id: user.id,
        name: `${user.first_name} ${user.last_name}`,
        rollNumber: "CS23B101",
        email: user.email,
        department: "Computer Science & Engineering",
        program: "B.Tech Computer Science",
        semester: 5,
      });

      if (res.success) {
        setFeedbackMessage(`Registered! Your Pass is #${res.data.ticketCode}`);
        setRegisterEvent(null);
        loadEvents();
      } else {
        alert(res.error || "Registration failed");
      }
    } finally {
      setActionLoading(false);
    }
  };

  // Filtered dataset
  const filteredEvents = useMemo(() => {
    return events.filter((e) => {
      const matchCat =
        categoryFilter === "ALL" || e.category === categoryFilter;
      const matchStatus = statusFilter === "ALL" || e.status === statusFilter;
      const matchSearch =
        searchQuery === "" ||
        e.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        e.organizer.toLowerCase().includes(searchQuery.toLowerCase()) ||
        e.venue.toLowerCase().includes(searchQuery.toLowerCase());
      return matchCat && matchStatus && matchSearch;
    });
  }, [events, categoryFilter, statusFilter, searchQuery]);

  // Enterprise DataGrid Columns
  const columns: ColumnDef<CampusEventItem>[] = [
    {
      id: "title",
      header: "Event",
      accessorFn: (row: CampusEventItem) => row.title,
      sortable: true,
      cell: (row) => (
        <div className="space-y-1">
          <Link
            href={`/app/campus/events/${row.id}`}
            className="text-xs font-bold text-white hover:text-indigo-400 transition-colors block"
          >
            {row.title}
          </Link>
          <div className="text-[11px] text-slate-400 line-clamp-1">
            {row.description}
          </div>
        </div>
      ),
    },
    {
      id: "category",
      header: "Category",
      accessorFn: (row: CampusEventItem) => row.category,
      sortable: true,
      cell: (row) => (
        <span className="rounded bg-indigo-500/20 px-2 py-0.5 text-[10px] font-mono font-semibold text-indigo-300 border border-indigo-500/30 whitespace-nowrap">
          {row.category}
        </span>
      ),
    },
    {
      id: "organizer",
      header: "Organizer",
      accessorFn: (row: CampusEventItem) => row.organizer,
      sortable: true,
      cell: (row) => (
        <div className="text-xs text-slate-300">
          <span className="font-medium block truncate max-w-[160px]">
            {row.organizer}
          </span>
          <span className="text-[10px] text-slate-500 capitalize">
            {row.organizerType.toLowerCase()}
          </span>
        </div>
      ),
    },
    {
      id: "schedule",
      header: "Date & Time",
      accessorFn: (row: CampusEventItem) => row.startDate,
      sortable: true,
      cell: (row) => (
        <div className="text-xs space-y-0.5 whitespace-nowrap">
          <div className="text-white font-mono flex items-center gap-1.5">
            <Calendar className="h-3 w-3 text-slate-500" />
            {row.startDate}
          </div>
          <div className="text-[11px] text-slate-400 flex items-center gap-1.5">
            <Clock className="h-3 w-3 text-slate-500" />
            {row.startTime} - {row.endTime}
          </div>
        </div>
      ),
    },
    {
      id: "venue",
      header: "Venue",
      accessorFn: (row: CampusEventItem) => row.venue,
      sortable: true,
      cell: (row) => (
        <div
          className="text-xs text-slate-300 max-w-[140px] truncate"
          title={row.venue}
        >
          <div className="flex items-center gap-1 truncate">
            <MapPin className="h-3 w-3 text-slate-500 shrink-0" />
            <span className="truncate">{row.venue}</span>
          </div>
          <span className="text-[10px] text-slate-500 block">
            Cap: {row.capacity}
          </span>
        </div>
      ),
    },
    {
      id: "audience",
      header: "Audience",
      accessorFn: (row: CampusEventItem) => row.targetAudience.type,
      cell: (row) => (
        <span className="text-[11px] text-slate-400 block max-w-[120px] truncate">
          {row.targetAudience.departmentName ||
            row.targetAudience.type.replace("_", " ")}
        </span>
      ),
    },
    {
      id: "registrations",
      header: "Registrations",
      accessorFn: (row: CampusEventItem) => row.registeredCount,
      sortable: true,
      cell: (row) => {
        const usage = Math.round((row.registeredCount / row.capacity) * 100);
        return (
          <div className="text-xs space-y-1">
            <div className="flex items-center justify-between font-mono text-[11px]">
              <span className="text-white font-bold">
                {row.registeredCount}
              </span>
              <span className="text-slate-500">/ {row.capacity}</span>
            </div>
            <div className="h-1.5 w-20 rounded-full bg-slate-800 overflow-hidden">
              <div
                className={`h-full ${
                  usage >= 100
                    ? "bg-rose-500"
                    : usage >= 80
                      ? "bg-amber-500"
                      : "bg-indigo-500"
                }`}
                style={{ width: `${Math.min(100, usage)}%` }}
              />
            </div>
          </div>
        );
      },
    },
    {
      id: "attendance",
      header: "Attendance",
      accessorFn: (row: CampusEventItem) => row.attendedCount,
      sortable: true,
      cell: (row) => {
        if (!row.requiresAttendance) {
          return <span className="text-[10px] text-slate-600">N/A</span>;
        }
        return (
          <div className="text-xs font-mono">
            <span className="text-emerald-400 font-bold">
              {row.attendedCount}
            </span>
            {row.registeredCount > 0 && (
              <span className="text-[10px] text-slate-500 ml-1">
                ({Math.round((row.attendedCount / row.registeredCount) * 100)}%)
              </span>
            )}
          </div>
        );
      },
    },
    {
      id: "status",
      header: "Status",
      accessorFn: (row: CampusEventItem) => row.status,
      sortable: true,
      cell: (row) => {
        const statusColors: Record<EventStatus, string> = {
          DRAFT: "bg-slate-800 text-slate-400 border-slate-700",
          PENDING_APPROVAL:
            "bg-amber-500/20 text-amber-300 border-amber-500/30",
          PUBLISHED: "bg-blue-500/20 text-blue-300 border-blue-500/30",
          REGISTRATION_OPEN:
            "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
          REGISTRATION_CLOSED:
            "bg-purple-500/20 text-purple-300 border-purple-500/30",
          ONGOING:
            "bg-rose-500/20 text-rose-300 border-rose-500/30 animate-pulse",
          COMPLETED: "bg-slate-800/80 text-slate-300 border-slate-700",
          CANCELLED: "bg-rose-950/40 text-rose-400 border-rose-900/50",
        };

        return (
          <span
            className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold border ${
              statusColors[row.status] || "bg-slate-800 text-slate-400"
            }`}
          >
            {row.status.replace("_", " ")}
          </span>
        );
      },
    },
    {
      id: "actions",
      header: "Actions",
      cell: (row) => (
        <div className="flex items-center gap-1.5">
          <Link
            href={`/app/campus/events/${row.id}`}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            title="View Details"
          >
            <Eye className="h-4 w-4" />
          </Link>

          {row.status === "REGISTRATION_OPEN" && (
            <button
              onClick={() => setRegisterEvent(row)}
              className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 hover:bg-emerald-600/50 transition-colors"
            >
              Register
            </button>
          )}

          {canPublish &&
            (row.status === "DRAFT" || row.status === "PENDING_APPROVAL") && (
              <button
                onClick={() => setPublishEventId(row.id)}
                className="p-1 rounded-lg text-emerald-400 hover:bg-emerald-950/50 transition-colors"
                title="Publish Event"
              >
                <CheckCircle2 className="h-4 w-4" />
              </button>
            )}

          {canCreate &&
            row.status !== "CANCELLED" &&
            row.status !== "COMPLETED" && (
              <button
                onClick={() => setCancelEventId(row.id)}
                className="p-1 rounded-lg text-rose-400 hover:bg-rose-950/50 transition-colors"
                title="Cancel Event"
              >
                <XCircle className="h-4 w-4" />
              </button>
            )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <Link
              href="/app/campus"
              className="text-xs text-slate-400 hover:text-indigo-400 transition-colors"
            >
              Campus Hub
            </Link>
            <span className="text-slate-600">/</span>
            <span className="text-xs text-slate-200 font-semibold">
              Events Directory
            </span>
          </div>
          <h1 className="mt-1 text-2xl font-black tracking-tight text-white flex items-center gap-2.5">
            <PartyPopper className="h-6 w-6 text-indigo-400" />
            University Events Management
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Enterprise DataGrid controlling university event lifecycles,
            capacities, and registrations.
          </p>
        </div>

        {canCreate && (
          <Link href="/app/campus/events/create">
            <Button
              variant="primary"
              size="sm"
              leftIcon={<Plus className="h-4 w-4" />}
              className="bg-indigo-600 hover:bg-indigo-500 shadow-md shadow-indigo-600/30"
            >
              Create New Event
            </Button>
          </Link>
        )}
      </div>

      {/* Feedback Alert */}
      {feedbackMessage && (
        <div className="flex items-center justify-between p-3.5 rounded-xl border border-emerald-500/30 bg-emerald-950/20 text-emerald-300 text-xs font-medium">
          <span>{feedbackMessage}</span>
          <button
            onClick={() => setFeedbackMessage(null)}
            className="text-emerald-400 hover:text-white"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Filter Toolbar Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 p-4 rounded-xl border border-slate-800 bg-slate-900/60">
        <div className="flex flex-wrap items-center gap-2.5 flex-1">
          {/* Category Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-slate-400">Category:</span>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="ALL">All Categories</option>
              {ALL_CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-slate-400">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="ALL">All Statuses</option>
              {ALL_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s.replace("_", " ")}
                </option>
              ))}
            </select>
          </div>

          {(categoryFilter !== "ALL" ||
            statusFilter !== "ALL" ||
            searchQuery !== "") && (
            <button
              onClick={() => {
                setCategoryFilter("ALL");
                setStatusFilter("ALL");
                setSearchQuery("");
              }}
              className="text-xs text-rose-400 hover:text-rose-300 font-medium ml-2 cursor-pointer"
            >
              Reset Filters
            </button>
          )}
        </div>

        <div className="text-xs text-slate-400 font-mono">
          Showing{" "}
          <span className="font-bold text-white">{filteredEvents.length}</span>{" "}
          of <span className="font-bold text-white">{events.length}</span>{" "}
          events
        </div>
      </div>

      {/* Enterprise DataGrid */}
      <DataGrid
        data={filteredEvents}
        columns={columns}
        keyExtractor={(item) => item.id}
        loading={loading}
        error={error}
        onRetry={loadEvents}
        searchPlaceholder="Search event title, organizer, or venue..."
        onSearchChange={setSearchQuery}
        exportFileName="campus-events-export"
        enableExport={true}
        enableDensityToggle={true}
        enableColumnVisibility={true}
        emptyTitle="No campus events found"
        emptyDescription="There are no events matching your filter criteria. Try adjusting the category or status filter."
      />

      {/* Publish Confirmation Dialog */}
      <Dialog
        open={Boolean(publishEventId)}
        onClose={() => setPublishEventId(null)}
        title="Confirm Event Publication"
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-300 leading-relaxed">
            Publishing this event will transition its status to{" "}
            <strong>REGISTRATION_OPEN</strong>, generate student notifications,
            and add the event to the university calendar.
          </p>
          <div className="flex justify-end gap-2 pt-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setPublishEventId(null)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              isLoading={actionLoading}
              onClick={handlePublish}
              className="bg-emerald-600 hover:bg-emerald-500"
            >
              Publish Now
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Cancel Event Dialog */}
      <Dialog
        open={Boolean(cancelEventId)}
        onClose={() => setCancelEventId(null)}
        title="Cancel Event"
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-300">
            Please provide a cancellation rationale for the audit record:
          </p>
          <textarea
            value={cancelReason}
            onChange={(e) => setCancelReason(e.target.value)}
            rows={3}
            placeholder="e.g. Inclement weather / faculty unavailability"
            className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-rose-500"
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setCancelEventId(null)}
            >
              Abort
            </Button>
            <Button
              variant="destructive"
              size="sm"
              isLoading={actionLoading}
              onClick={handleCancel}
            >
              Confirm Cancellation
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Student Quick Register Dialog */}
      <Dialog
        open={Boolean(registerEvent)}
        onClose={() => setRegisterEvent(null)}
        title="Confirm Event Registration"
      >
        {registerEvent && (
          <div className="space-y-4">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1">
              <div className="font-bold text-white">{registerEvent.title}</div>
              <div className="text-slate-400">Venue: {registerEvent.venue}</div>
              <div className="text-slate-400">
                Date: {registerEvent.startDate} ({registerEvent.startTime})
              </div>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Register as{" "}
              <strong>
                {user?.first_name} {user?.last_name}
              </strong>{" "}
              ({user?.email})? Your entry ticket code will be generated
              immediately.
            </p>
            <div className="flex justify-end gap-2 pt-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setRegisterEvent(null)}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                isLoading={actionLoading}
                onClick={handleStudentRegister}
                className="bg-indigo-600 hover:bg-indigo-500"
              >
                Complete Registration
              </Button>
            </div>
          </div>
        )}
      </Dialog>
    </div>
  );
}
