"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { hostelLeavesService } from "@/services/hostel-leaves.service";
import { HostelLeave, LeaveStatus } from "@campusos/types";
import { useAuth } from "@/lib/auth-context";
import { DataGrid, ColumnDef } from "@/components/data-grid/data-grid";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Dialog } from "@/components/ui/dialog";
import {
  FileCheck2,
  Calendar,
  Search,
  Filter,
  Plus,
  Eye,
  CheckCircle2,
  XCircle,
  Phone,
  ArrowRight,
} from "lucide-react";

export default function HostelLeavesPage() {
  const { user } = useAuth();
  const [leaves, setLeaves] = useState<HostelLeave[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Submit Leave Modal
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState({
    startDate: "2026-10-10",
    endDate: "2026-10-14",
    destination: "Mysuru, Karnataka",
    reason: "Family event / festival vacation",
    emergencyName: "Suresh Patel",
    emergencyRelation: "Father",
    emergencyPhone: "+91 98450 99881",
  });

  const isStudent = user?.roles?.[0]?.name === "STUDENT";

  const loadLeaves = async () => {
    setLoading(true);
    try {
      const res = await hostelLeavesService.listHostelLeaves({
        studentId: isStudent ? "stu-24cse0101" : undefined,
        approvalStatus: statusFilter,
        search: searchQuery,
      });
      if (res.success && res.data) {
        setLeaves(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLeaves();
  }, [statusFilter, searchQuery, isStudent]);

  const handleSubmitLeave = async (e: React.FormEvent) => {
    e.preventDefault();
    await hostelLeavesService.submitHostelLeave({
      studentId: isStudent ? "stu-24cse0101" : "stu-24cse0101",
      studentName: isStudent ? `${user?.first_name} ${user?.last_name}` : "Aarav Patel",
      registerNumber: "24CSE0101",
      hostelId: "hst-raman",
      hostelName: "Sir C. V. Raman Hall of Residence",
      roomNumber: "304",
      startDate: form.startDate,
      endDate: form.endDate,
      destination: form.destination,
      reason: form.reason,
      emergencyContact: {
        name: form.emergencyName,
        relationship: form.emergencyRelation,
        phone: form.emergencyPhone,
      },
    });

    setModalOpen(false);
    loadLeaves();
  };

  const columns: ColumnDef<HostelLeave>[] = useMemo(
    () => [
      {
        id: "student",
        header: "Student & Room",
        accessorKey: "studentName",
        cell: (l) => (
          <div>
            <Link
              href={`/app/infrastructure/hostel/leaves/${l.id}`}
              className="font-semibold text-white hover:text-indigo-400 transition-colors"
            >
              {l.studentName}
            </Link>
            <div className="text-[11px] text-slate-400 font-mono">
              {l.registerNumber} • Room {l.roomNumber}
            </div>
          </div>
        ),
      },
      {
        id: "hostel",
        header: "Hostel",
        accessorKey: "hostelName",
        cell: (l) => <span className="text-xs text-slate-300">{l.hostelName}</span>,
      },
      {
        id: "dates",
        header: "Leave Duration",
        cell: (l) => (
          <div className="text-xs font-mono text-slate-200">
            {l.startDate} <span className="text-slate-500">→</span> {l.endDate}
          </div>
        ),
      },
      {
        id: "destination",
        header: "Destination",
        accessorKey: "destination",
        cell: (l) => <span className="text-xs text-white">{l.destination}</span>,
      },
      {
        id: "reason",
        header: "Reason",
        accessorKey: "reason",
        cell: (l) => (
          <span className="text-xs text-slate-300 truncate max-w-[200px] block" title={l.reason}>
            {l.reason}
          </span>
        ),
      },
      {
        id: "status",
        header: "Approval Status",
        accessorKey: "approvalStatus",
        cell: (l) => {
          const map: Record<string, string> = {
            APPROVED: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
            PENDING: "bg-amber-500/10 text-amber-400 border-amber-500/20",
            REJECTED: "bg-rose-500/10 text-rose-400 border-rose-500/20",
            COMPLETED: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
            CANCELLED: "bg-slate-500/10 text-slate-400 border-slate-500/20",
          };
          return (
            <Badge variant="outline" className={map[l.approvalStatus] || ""}>
              {l.approvalStatus}
            </Badge>
          );
        },
      },
      {
        id: "actions",
        header: "Actions",
        cell: (l) => (
          <Link href={`/app/infrastructure/hostel/leaves/${l.id}`}>
            <Button size="sm" variant="ghost" className="h-7 text-xs text-indigo-400 hover:text-indigo-300 hover:bg-slate-800">
              <Eye className="h-3.5 w-3.5 mr-1" />
              Review
            </Button>
          </Link>
        ),
      },
    ],
    []
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
            <Link href="/app/infrastructure/hostel" className="hover:text-white">
              Hostel
            </Link>
            <span>/</span>
            <span className="text-indigo-400">Hostel Leaves</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <FileCheck2 className="h-6 w-6 text-indigo-400" />
            Hostel Leaves & Gate-Pass Permits
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            {isStudent
              ? "Submit outing & vacation gate passes and track approval by your hall warden."
              : "Review, approve, and track student leaves, gate passes, and campus return timestamps."}
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <Button
            onClick={() => setModalOpen(true)}
            className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
          >
            <Plus className="h-4 w-4 mr-1.5" />
            Apply For Leave
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
              placeholder="Search student, destination, reason, room..."
              className="pl-9 bg-slate-900 border-slate-800 text-xs text-white"
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter className="h-3.5 w-3.5 text-slate-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
            >
              <option value="ALL">All Statuses</option>
              <option value="PENDING">Pending Approval</option>
              <option value="APPROVED">Approved</option>
              <option value="REJECTED">Rejected</option>
              <option value="COMPLETED">Returned / Completed</option>
            </select>
          </div>
        </div>
      </div>

      {/* DataGrid */}
      <DataGrid
        data={leaves}
        columns={columns}
        loading={loading}
        emptyMessage="No hostel leaves found."
      />

      {/* Apply Leave Modal */}
      <Dialog
        open={modalOpen}
        onOpenChange={setModalOpen}
        title="Apply For Hostel Leave / Outing Permit"
        description="Submit leave application with emergency contact details and destination address."
      >
        <form onSubmit={handleSubmitLeave} className="space-y-4 pt-2">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Departure Date *</label>
              <Input
                type="date"
                required
                value={form.startDate}
                onChange={(e) => setForm({ ...form, startDate: e.target.value })}
                className="bg-slate-900 border-slate-700 text-xs"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Expected Return Date *</label>
              <Input
                type="date"
                required
                value={form.endDate}
                onChange={(e) => setForm({ ...form, endDate: e.target.value })}
                className="bg-slate-900 border-slate-700 text-xs"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Destination Location *</label>
            <Input
              required
              placeholder="e.g. Mysuru, Karnataka"
              value={form.destination}
              onChange={(e) => setForm({ ...form, destination: e.target.value })}
              className="bg-slate-900 border-slate-700 text-xs"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Reason for Leave *</label>
            <Input
              required
              placeholder="e.g. Family wedding / medical appointment"
              value={form.reason}
              onChange={(e) => setForm({ ...form, reason: e.target.value })}
              className="bg-slate-900 border-slate-700 text-xs"
            />
          </div>

          <div className="border-t border-slate-800 pt-3 space-y-3">
            <h4 className="text-xs font-bold text-slate-300 uppercase">Emergency Parent / Guardian Contact</h4>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Contact Name</label>
                <Input
                  value={form.emergencyName}
                  onChange={(e) => setForm({ ...form, emergencyName: e.target.value })}
                  className="bg-slate-900 border-slate-700 text-xs"
                />
              </div>
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Relationship</label>
                <Input
                  value={form.emergencyRelation}
                  onChange={(e) => setForm({ ...form, emergencyRelation: e.target.value })}
                  className="bg-slate-900 border-slate-700 text-xs"
                />
              </div>
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Phone Number</label>
                <Input
                  value={form.emergencyPhone}
                  onChange={(e) => setForm({ ...form, emergencyPhone: e.target.value })}
                  className="bg-slate-900 border-slate-700 text-xs"
                />
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-2.5 pt-4 border-t border-slate-800">
            <Button
              type="button"
              variant="outline"
              onClick={() => setModalOpen(false)}
              className="border-slate-700 text-slate-300 text-xs"
            >
              Cancel
            </Button>
            <Button type="submit" className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs">
              Submit Gate Pass Request
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
