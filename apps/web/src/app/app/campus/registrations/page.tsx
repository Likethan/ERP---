"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { campusService } from "@/services/campus.service";
import { EventRegistrationItem, RegistrationStatus } from "@/types/campus";
import { useAuth } from "@/lib/auth-context";
import { DataGrid, ColumnDef } from "@/components/data-grid/data-grid";
import {
  CheckSquare,
  Calendar,
  Ticket,
  Users,
  Eye,
  XCircle,
  AlertCircle,
  Filter,
  CheckCircle2,
  Clock,
  MapPin,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";

const ALL_STATUSES: RegistrationStatus[] = [
  "REGISTERED",
  "CONFIRMED",
  "WAITLISTED",
  "CANCELLED",
  "ATTENDED",
  "ABSENT",
];

export default function CampusRegistrationsPage() {
  const { user, hasRole } = useAuth();
  const isStudent = hasRole("STUDENT");

  const [registrations, setRegistrations] = useState<EventRegistrationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [activeTab, setActiveTab] = useState<"all" | "my_registrations">(
    isStudent ? "my_registrations" : "all"
  );
  const [mySubTab, setMySubTab] = useState<"upcoming" | "completed" | "cancelled">("upcoming");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Cancel Registration Modal
  const [cancelRegId, setCancelRegId] = useState<string | null>(null);
  const [cancelReason, setCancelReason] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await campusService.getRegistrations();
      if (res.success && res.data) {
        setRegistrations(res.data);
      } else {
        setError(res.error || "Failed to load registrations");
      }
    } catch (e: any) {
      setError(e.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCancelRegistration = async () => {
    if (!cancelRegId) return;
    try {
      setActionLoading(true);
      const res = await campusService.cancelRegistration(
        cancelRegId,
        cancelReason,
        `${user?.first_name || "User"} (${user?.email})`
      );
      if (res.success) {
        setFeedback("Registration successfully cancelled.");
        setCancelRegId(null);
        setCancelReason("");
        loadData();
      }
    } finally {
      setActionLoading(false);
    }
  };

  // Student Registrations Filter
  const myRegistrations = useMemo(() => {
    return registrations.filter((r) => r.studentId === user?.id || r.email === user?.email);
  }, [registrations, user]);

  const filteredMyRegistrations = useMemo(() => {
    if (mySubTab === "upcoming") {
      return myRegistrations.filter(
        (r) => r.status === "CONFIRMED" || r.status === "REGISTERED" || r.status === "WAITLISTED"
      );
    }
    if (mySubTab === "completed") {
      return myRegistrations.filter((r) => r.status === "ATTENDED" || r.status === "ABSENT");
    }
    return myRegistrations.filter((r) => r.status === "CANCELLED");
  }, [myRegistrations, mySubTab]);

  // All Registrations Filtered
  const filteredAllRegistrations = useMemo(() => {
    return registrations.filter((r) => {
      const matchStatus = statusFilter === "ALL" || r.status === statusFilter;
      const matchSearch =
        searchQuery === "" ||
        r.studentName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.rollNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.eventTitle.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.ticketCode.toLowerCase().includes(searchQuery.toLowerCase());
      return matchStatus && matchSearch;
    });
  }, [registrations, statusFilter, searchQuery]);

  const columns: ColumnDef<EventRegistrationItem>[] = [
    {
      id: "participant",
      header: "Participant",
      accessorFn: (row: EventRegistrationItem) => row.studentName,
      sortable: true,
      cell: (row) => (
        <div>
          <div className="font-bold text-white text-xs">{row.studentName}</div>
          <div className="text-[11px] text-slate-400 font-mono">
            {row.rollNumber} • {row.department} (Sem {row.semester})
          </div>
        </div>
      ),
    },
    {
      id: "event",
      header: "Event",
      accessorFn: (row: EventRegistrationItem) => row.eventTitle,
      sortable: true,
      cell: (row) => (
        <div>
          <Link
            href={`/app/campus/events/${row.eventId}`}
            className="text-xs font-bold text-indigo-400 hover:text-indigo-300 transition-colors block"
          >
            {row.eventTitle}
          </Link>
          <div className="text-[11px] text-slate-500 flex items-center gap-1.5 mt-0.5">
            <Calendar className="h-3 w-3" /> {row.eventDate} ({row.eventTime})
          </div>
        </div>
      ),
    },
    {
      id: "ticket",
      header: "Pass Ticket",
      accessorFn: (row: EventRegistrationItem) => row.ticketCode,
      sortable: true,
      cell: (row) => (
        <span className="font-mono text-xs font-bold text-white bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
          {row.ticketCode}
        </span>
      ),
    },
    {
      id: "registrationDate",
      header: "Registration Date",
      accessorFn: (row: EventRegistrationItem) => row.registrationDate,
      sortable: true,
      cell: (row) => <span className="text-xs font-mono text-slate-400">{row.registrationDate}</span>,
    },
    {
      id: "status",
      header: "Status",
      accessorFn: (row: EventRegistrationItem) => row.status,
      sortable: true,
      cell: (row) => {
        const colors: Record<RegistrationStatus, string> = {
          REGISTERED: "bg-blue-500/20 text-blue-300 border-blue-500/30",
          CONFIRMED: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
          WAITLISTED: "bg-amber-500/20 text-amber-300 border-amber-500/30",
          CANCELLED: "bg-slate-800 text-slate-500 border-slate-700",
          ATTENDED: "bg-teal-500/20 text-teal-300 border-teal-500/30",
          ABSENT: "bg-rose-500/20 text-rose-300 border-rose-500/30",
        };

        return (
          <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${colors[row.status]}`}>
            {row.status}
          </span>
        );
      },
    },
    {
      id: "attendance",
      header: "Attendance",
      accessorFn: (row: EventRegistrationItem) => row.attendanceStatus || (row.attendanceMarked ? "MARKED" : "PENDING"),
      cell: (row) => (
        <span
          className={`text-xs font-bold ${
            row.attendanceStatus === "PRESENT" || row.status === "ATTENDED"
              ? "text-emerald-400"
              : row.attendanceStatus === "ABSENT" || row.status === "ABSENT"
              ? "text-rose-400"
              : "text-slate-500"
          }`}
        >
          {row.attendanceStatus || (row.attendanceMarked ? "MARKED" : "PENDING")}
        </span>
      ),
    },
    {
      id: "actions",
      header: "Actions",
      cell: (row) => (
        <div className="flex items-center gap-2">
          <Link
            href={`/app/campus/events/${row.eventId}`}
            className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800"
            title="Inspect Event"
          >
            <Eye className="h-4 w-4" />
          </Link>
          {row.status !== "CANCELLED" && row.status !== "ATTENDED" && (
            <button
              onClick={() => setCancelRegId(row.id)}
              className="text-[10px] text-rose-400 hover:text-rose-300 font-semibold"
            >
              Cancel
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6 animate-fade-in pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <Link href="/app/campus" className="text-xs text-slate-400 hover:text-indigo-400">
              Campus Hub
            </Link>
            <span className="text-slate-600">/</span>
            <span className="text-xs text-slate-200 font-semibold">Event Registrations</span>
          </div>
          <h1 className="mt-1 text-2xl font-black tracking-tight text-white flex items-center gap-2.5">
            <Ticket className="h-6 w-6 text-indigo-400" />
            Event Registration Ledger
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Participant tracking, hall entry tickets, and cohort attendance cross-referencing.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/app/campus/events">
            <Button variant="outline" size="sm">
              Browse Events
            </Button>
          </Link>
        </div>
      </div>

      {feedback && (
        <div className="p-3.5 rounded-xl border border-emerald-500/30 bg-emerald-950/20 text-emerald-300 text-xs flex items-center justify-between">
          <span>{feedback}</span>
          <button onClick={() => setFeedback(null)} className="text-emerald-400 hover:text-white">
            Dismiss
          </button>
        </div>
      )}

      {/* Primary View Switcher: All Registrations vs My Registrations */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
        <button
          onClick={() => setActiveTab("all")}
          className={`px-4 py-2 text-xs font-semibold rounded-xl transition-all cursor-pointer ${
            activeTab === "all"
              ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
              : "bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
          }`}
        >
          All Registrations ({registrations.length})
        </button>
        <button
          onClick={() => setActiveTab("my_registrations")}
          className={`px-4 py-2 text-xs font-semibold rounded-xl transition-all cursor-pointer ${
            activeTab === "my_registrations"
              ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
              : "bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
          }`}
        >
          My Registrations ({myRegistrations.length})
        </button>
      </div>

      {/* VIEW 1: MY REGISTRATIONS (STUDENT EXPERIENCE) */}
      {activeTab === "my_registrations" && (
        <div className="space-y-6">
          {/* Sub-tabs: Upcoming, Completed, Cancelled */}
          <div className="flex items-center gap-2">
            {[
              { id: "upcoming", label: "Upcoming Events" },
              { id: "completed", label: "Completed Events" },
              { id: "cancelled", label: "Cancelled Passes" },
            ].map((st) => (
              <button
                key={st.id}
                onClick={() => setMySubTab(st.id as any)}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors cursor-pointer ${
                  mySubTab === st.id
                    ? "bg-slate-800 text-white border border-slate-700 font-bold"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {st.label}
              </button>
            ))}
          </div>

          {filteredMyRegistrations.length === 0 ? (
            <div className="p-8 text-center rounded-2xl border border-slate-800 bg-slate-900/40 space-y-3">
              <Ticket className="h-8 w-8 text-slate-600 mx-auto" />
              <div className="text-sm font-semibold text-white">No registrations in this category</div>
              <p className="text-xs text-slate-400">
                Discover upcoming hackathons, tech bootcamps, and fests from the catalog.
              </p>
              <Link href="/app/campus/events">
                <Button variant="primary" size="sm" className="mt-2 bg-indigo-600 hover:bg-indigo-500">
                  Discover Campus Events
                </Button>
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredMyRegistrations.map((reg) => (
                <div
                  key={reg.id}
                  className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60 flex flex-col justify-between space-y-4 hover:border-slate-700 transition-all"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                        {reg.eventCategory}
                      </span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
                        {reg.status}
                      </span>
                    </div>

                    <h3 className="text-sm font-bold text-white line-clamp-2">
                      {reg.eventTitle}
                    </h3>

                    <div className="space-y-1 text-xs text-slate-400 pt-2 border-t border-slate-800/80">
                      <div className="flex items-center gap-1.5">
                        <Calendar className="h-3.5 w-3.5 text-slate-500" />
                        <span>{reg.eventDate} ({reg.eventTime})</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <MapPin className="h-3.5 w-3.5 text-slate-500" />
                        <span className="truncate">{reg.eventVenue}</span>
                      </div>
                    </div>

                    <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between font-mono text-xs">
                      <span className="text-slate-500 text-[10px]">PASS TICKET:</span>
                      <span className="font-bold text-indigo-400">{reg.ticketCode}</span>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
                    <Link
                      href={`/app/campus/events/${reg.eventId}`}
                      className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold"
                    >
                      View Details →
                    </Link>

                    {reg.status !== "CANCELLED" && reg.status !== "ATTENDED" && (
                      <button
                        onClick={() => setCancelRegId(reg.id)}
                        className="text-xs text-rose-400 hover:text-rose-300 font-medium"
                      >
                        Cancel Pass
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* VIEW 2: ALL REGISTRATIONS (ENTERPRISE DATAGRID) */}
      {activeTab === "all" && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl border border-slate-800 bg-slate-900/60">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">Status:</span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-white"
              >
                <option value="ALL">All Statuses</option>
                {ALL_STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>

              {statusFilter !== "ALL" && (
                <button
                  onClick={() => setStatusFilter("ALL")}
                  className="text-xs text-rose-400 hover:text-rose-300 ml-2"
                >
                  Clear
                </button>
              )}
            </div>

            <div className="text-xs text-slate-400 font-mono">
              Total Records: <strong className="text-white">{filteredAllRegistrations.length}</strong>
            </div>
          </div>

          <DataGrid
            data={filteredAllRegistrations}
            columns={columns}
            keyExtractor={(item) => item.id}
            loading={loading}
            error={error}
            onRetry={loadData}
            searchPlaceholder="Search by student name, roll number, ticket, or event..."
            onSearchChange={setSearchQuery}
            exportFileName="event-registrations"
            enableExport={true}
            enableDensityToggle={true}
            emptyTitle="No registrations found"
            emptyDescription="There are no registration records matching your filter parameters."
          />
        </div>
      )}

      {/* Cancel Registration Confirmation Modal */}
      <Dialog
        open={Boolean(cancelRegId)}
        onClose={() => setCancelRegId(null)}
        title="Cancel Event Registration"
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-300">
            Are you sure you want to cancel this registration? Your entry ticket code will be invalidated.
          </p>
          <textarea
            value={cancelReason}
            onChange={(e) => setCancelReason(e.target.value)}
            rows={3}
            placeholder="Cancellation reason (optional)..."
            className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-white"
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" size="sm" onClick={() => setCancelRegId(null)}>
              Keep Registration
            </Button>
            <Button
              variant="destructive"
              size="sm"
              isLoading={actionLoading}
              onClick={handleCancelRegistration}
            >
              Confirm Cancellation
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
