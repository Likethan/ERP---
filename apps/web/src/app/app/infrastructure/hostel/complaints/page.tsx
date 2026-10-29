"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { hostelComplaintsService } from "@/services/hostel-complaints.service";
import {
  HostelComplaint,
  ComplaintCategory,
  ComplaintStatus,
  ComplaintPriority,
} from "@campusos/types";
import { useAuth } from "@/lib/auth-context";
import { DataGrid, ColumnDef } from "@/components/data-grid/data-grid";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Dialog } from "@/components/ui/dialog";
import {
  AlertCircle,
  Search,
  Filter,
  Plus,
  Eye,
  Clock,
  CheckCircle2,
  Wrench,
  AlertTriangle,
  DoorOpen,
} from "lucide-react";

export default function HostelComplaintsPage() {
  const { user } = useAuth();
  const [complaints, setComplaints] = useState<HostelComplaint[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [categoryFilter, setCategoryFilter] = useState("ALL");
  const [priorityFilter, setPriorityFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Create Modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [form, setForm] = useState({
    title: "",
    description: "",
    category: ComplaintCategory.ELECTRICAL,
    priority: ComplaintPriority.MEDIUM,
    roomNumber: "304",
  });

  const isStudent = user?.roles?.[0]?.name === "STUDENT";

  const loadComplaints = async () => {
    setLoading(true);
    try {
      const res = await hostelComplaintsService.listHostelComplaints({
        studentId: isStudent ? "stu-24cse0101" : undefined,
        status: statusFilter,
        category: categoryFilter,
        priority: priorityFilter,
        search: searchQuery,
      });
      if (res.success && res.data) {
        setComplaints(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadComplaints();
  }, [statusFilter, categoryFilter, priorityFilter, searchQuery, isStudent]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title || !form.description) return;

    await hostelComplaintsService.createHostelComplaint({
      studentId: isStudent ? "stu-24cse0101" : "stu-24cse0101",
      studentName: isStudent
        ? `${user?.first_name} ${user?.last_name}`
        : "Aarav Patel",
      registerNumber: "24CSE0101",
      hostelId: "hst-raman",
      hostelName: "Sir C. V. Raman Hall of Residence",
      roomNumber: form.roomNumber,
      category: form.category,
      priority: form.priority,
      title: form.title,
      description: form.description,
    });

    setCreateModalOpen(false);
    loadComplaints();
  };

  const columns: ColumnDef<HostelComplaint>[] = useMemo(
    () => [
      {
        id: "ticket",
        header: "Complaint ID & Title",
        accessorKey: "ticketNumber",
        cell: (c) => (
          <div>
            <Link
              href={`/app/infrastructure/hostel/complaints/${c.id}`}
              className="font-semibold text-white hover:text-indigo-400 transition-colors"
            >
              {c.ticketNumber}
            </Link>
            <div
              className="text-xs text-slate-300 font-medium truncate max-w-[240px]"
              title={c.title}
            >
              {c.title}
            </div>
          </div>
        ),
      },
      {
        id: "student",
        header: "Student & Room",
        cell: (c) => (
          <div className="text-xs">
            <span className="font-medium text-white">{c.studentName}</span>
            <div className="text-[11px] text-slate-400 font-mono">
              Room {c.roomNumber} ({c.hostelName.split(" ")[0]})
            </div>
          </div>
        ),
      },
      {
        id: "category",
        header: "Category",
        accessorKey: "category",
        cell: (c) => (
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
            {c.category}
          </span>
        ),
      },
      {
        id: "priority",
        header: "Priority",
        accessorKey: "priority",
        cell: (c) => {
          const pMap: Record<string, string> = {
            CRITICAL: "bg-red-500/10 text-red-400 border-red-500/20",
            HIGH: "bg-orange-500/10 text-orange-400 border-orange-500/20",
            MEDIUM: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
            LOW: "bg-slate-500/10 text-slate-400 border-slate-500/20",
          };
          return (
            <Badge variant="outline" className={pMap[c.priority] || ""}>
              {c.priority}
            </Badge>
          );
        },
      },
      {
        id: "assignedStaff",
        header: "Assigned Staff",
        accessorKey: "assignedStaffName",
        cell: (c) => (
          <span className="text-xs text-slate-300">
            {c.assignedStaffName || (
              <span className="text-slate-500 italic">Unassigned</span>
            )}
          </span>
        ),
      },
      {
        id: "status",
        header: "Status",
        accessorKey: "status",
        cell: (c) => {
          const sMap: Record<string, string> = {
            OPEN: "bg-blue-500/10 text-blue-400 border-blue-500/20",
            ASSIGNED: "bg-purple-500/10 text-purple-400 border-purple-500/20",
            IN_PROGRESS:
              "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
            RESOLVED:
              "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
            CLOSED: "bg-slate-500/10 text-slate-400 border-slate-500/20",
          };
          return (
            <Badge variant="outline" className={sMap[c.status] || ""}>
              {c.status.replace("_", " ")}
            </Badge>
          );
        },
      },
      {
        id: "sla",
        header: "SLA Indicator",
        cell: (c) => (
          <span
            className={`text-xs font-mono flex items-center gap-1 ${
              c.slaBreached ? "text-red-400 font-bold" : "text-emerald-400"
            }`}
          >
            <Clock className="h-3 w-3" />
            {c.slaTargetHours}h Target
          </span>
        ),
      },
      {
        id: "actions",
        header: "Actions",
        cell: (c) => (
          <Link href={`/app/infrastructure/hostel/complaints/${c.id}`}>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 text-xs text-indigo-400 hover:text-indigo-300 hover:bg-slate-800"
            >
              <Eye className="h-3.5 w-3.5 mr-1" />
              Inspect
            </Button>
          </Link>
        ),
      },
    ],
    [],
  );

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto text-slate-100">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Link href="/app/infrastructure" className="hover:text-white">
              Infrastructure
            </Link>
            <span>/</span>
            <Link
              href="/app/infrastructure/hostel"
              className="hover:text-white"
            >
              Hostel
            </Link>
            <span>/</span>
            <span className="text-indigo-400">Complaints</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <AlertCircle className="h-6 w-6 text-indigo-400" />
            Hostel Maintenance Complaints
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Log, assign, track SLAs, and resolve resident electrical, plumbing,
            WiFi, and furniture tickets.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <Button
            onClick={() => setCreateModalOpen(true)}
            className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
          >
            <Plus className="h-4 w-4 mr-1.5" />
            Report Issue
          </Button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[220px]">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search complaint title, ticket ID, student, room..."
              className="pl-9 bg-slate-900 border-slate-800 text-xs text-white"
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter className="h-3.5 w-3.5 text-slate-400" />
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
            >
              <option value="ALL">All Categories</option>
              <option value="ELECTRICAL">Electrical</option>
              <option value="PLUMBING">Plumbing</option>
              <option value="CLEANING">Cleaning</option>
              <option value="WIFI">WiFi & Network</option>
              <option value="FURNITURE">Furniture</option>
              <option value="ROOM">Room Structural</option>
              <option value="SAFETY">Safety</option>
            </select>

            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
            >
              <option value="ALL">All Priorities</option>
              <option value="CRITICAL">Critical (4h SLA)</option>
              <option value="HIGH">High (12h SLA)</option>
              <option value="MEDIUM">Medium (24h SLA)</option>
              <option value="LOW">Low (48h SLA)</option>
            </select>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
            >
              <option value="ALL">All Statuses</option>
              <option value="OPEN">Open</option>
              <option value="ASSIGNED">Assigned</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="RESOLVED">Resolved</option>
              <option value="CLOSED">Closed</option>
            </select>
          </div>
        </div>
      </div>

      {/* DataGrid */}
      <DataGrid
        data={complaints}
        columns={columns}
        loading={loading}
        emptyMessage="No hostel complaints found matching your criteria."
      />

      {/* Report Issue Modal */}
      <Dialog
        open={createModalOpen}
        onOpenChange={setCreateModalOpen}
        title="Report Hostel Room Issue"
        description="Submit an infrastructure maintenance ticket to the hostel warden and estate office."
      >
        <form onSubmit={handleCreate} className="space-y-4 pt-2">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Issue Category *
              </label>
              <select
                value={form.category}
                onChange={(e) =>
                  setForm({
                    ...form,
                    category: e.target.value as ComplaintCategory,
                  })
                }
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200"
              >
                <option value="ELECTRICAL">Electrical & Power</option>
                <option value="PLUMBING">Plumbing & Water</option>
                <option value="CLEANING">Cleaning & Hygiene</option>
                <option value="WIFI">WiFi & Internet</option>
                <option value="FURNITURE">Furniture & Bed Frame</option>
                <option value="SAFETY">Safety Hazard</option>
                <option value="ROOM">Room Structure</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Urgency Priority *
              </label>
              <select
                value={form.priority}
                onChange={(e) =>
                  setForm({
                    ...form,
                    priority: e.target.value as ComplaintPriority,
                  })
                }
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200"
              >
                <option value="LOW">Low (48 Hours)</option>
                <option value="MEDIUM">Medium (24 Hours)</option>
                <option value="HIGH">High (12 Hours)</option>
                <option value="CRITICAL">Critical Emergency (4 Hours)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">
              Room Number *
            </label>
            <Input
              required
              value={form.roomNumber}
              onChange={(e) => setForm({ ...form, roomNumber: e.target.value })}
              className="bg-slate-900 border-slate-700 text-xs"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">
              Subject / Summary *
            </label>
            <Input
              required
              placeholder="e.g. Ceiling fan humming loudly at speed 3"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="bg-slate-900 border-slate-700 text-xs"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">
              Detailed Description *
            </label>
            <textarea
              required
              rows={3}
              placeholder="Describe the exact location, symptoms, and when the issue started..."
              value={form.description}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200"
            />
          </div>

          <div className="flex justify-end gap-2.5 pt-4 border-t border-slate-800">
            <Button
              type="button"
              variant="outline"
              onClick={() => setCreateModalOpen(false)}
              className="border-slate-700 text-slate-300 text-xs"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs"
            >
              Submit Ticket
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
