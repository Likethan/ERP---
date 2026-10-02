"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { hostelAllocationsService } from "@/services/hostel-allocations.service";
import { hostelsService } from "@/services/hostels.service";
import { hostelRoomsService } from "@/services/hostel-rooms.service";
import { HostelAllocation, Hostel, HostelRoom, AllocationStatus, BedStatus } from "@campusos/types";
import { DataGrid, ColumnDef } from "@/components/data-grid/data-grid";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Dialog } from "@/components/ui/dialog";
import {
  UserCheck,
  BedDouble,
  Search,
  Filter,
  Plus,
  Eye,
  ArrowRight,
  DoorOpen,
  Calendar,
} from "lucide-react";

export default function HostelAllocationsPage() {
  const [allocations, setAllocations] = useState<HostelAllocation[]>([]);
  const [hostels, setHostels] = useState<Hostel[]>([]);
  const [rooms, setRooms] = useState<HostelRoom[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [hostelFilter, setHostelFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [programFilter, setProgramFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // New Allocation Modal
  const [allocateModalOpen, setAllocateModalOpen] = useState(false);
  const [form, setForm] = useState({
    studentName: "",
    registerNumber: "",
    programCode: "BTECH-CSE",
    year: 3,
    semester: 5,
    hostelId: "hst-raman",
    blockName: "Block A (Senior Wing)",
    floor: 3,
    roomId: "rm-305-a",
    roomNumber: "305",
    bedId: "bed-305-a2",
    bedNumber: "Bed B",
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [aRes, hRes, rRes] = await Promise.all([
        hostelAllocationsService.listHostelAllocations({
          hostelId: hostelFilter,
          status: statusFilter,
          programCode: programFilter,
          search: searchQuery,
        }),
        hostelsService.listHostels(),
        hostelRoomsService.listRooms(),
      ]);

      if (aRes.success && aRes.data) setAllocations(aRes.data);
      if (hRes.success && hRes.data) setHostels(hRes.data);
      if (rRes.success && rRes.data) setRooms(rRes.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [hostelFilter, statusFilter, programFilter, searchQuery]);

  const handleAllocate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.studentName || !form.registerNumber) return;

    const selectedHostel = hostels.find((h) => h.id === form.hostelId);

    await hostelAllocationsService.createHostelAllocation({
      studentId: `stu-${Date.now().toString(36)}`,
      studentName: form.studentName,
      registerNumber: form.registerNumber,
      programCode: form.programCode,
      programName: `${form.programCode} Degree`,
      departmentCode: form.programCode.split("-")[1] || "ENGG",
      year: Number(form.year),
      semester: Number(form.semester),
      hostelId: form.hostelId,
      hostelName: selectedHostel?.name || "Sir C. V. Raman Hall",
      blockId: `blk-${form.blockName.toLowerCase().slice(0, 4)}`,
      blockName: form.blockName,
      floor: Number(form.floor),
      roomId: form.roomId,
      roomNumber: form.roomNumber,
      bedId: form.bedId,
      bedNumber: form.bedNumber,
    });

    setAllocateModalOpen(false);
    loadData();
  };

  const columns: ColumnDef<HostelAllocation>[] = useMemo(
    () => [
      {
        id: "student",
        header: "Student Name",
        accessorKey: "studentName",
        cell: (a) => (
          <div>
            <Link
              href={`/app/infrastructure/hostel/allocations/${a.id}`}
              className="font-semibold text-white hover:text-indigo-400 transition-colors"
            >
              {a.studentName}
            </Link>
            <div className="text-[11px] font-mono text-slate-400">{a.registerNumber}</div>
          </div>
        ),
      },
      {
        id: "program",
        header: "Program & Year",
        cell: (a) => (
          <div className="text-xs">
            <span className="text-white font-medium">{a.programCode}</span>
            <div className="text-[11px] text-slate-400">Year {a.year} • Sem {a.semester}</div>
          </div>
        ),
      },
      {
        id: "location",
        header: "Hostel & Room",
        cell: (a) => (
          <div className="text-xs">
            <div className="text-white font-medium">{a.hostelName}</div>
            <div className="text-[11px] text-slate-400">
              {a.blockName} • Room {a.roomNumber} ({a.bedNumber})
            </div>
          </div>
        ),
      },
      {
        id: "allocatedDate",
        header: "Allocated Date",
        accessorKey: "allocatedDate",
        cell: (a) => <span className="text-xs text-slate-300 font-mono">{a.allocatedDate}</span>,
      },
      {
        id: "status",
        header: "Status",
        accessorKey: "status",
        cell: (a) => {
          const map: Record<string, string> = {
            ALLOCATED: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
            PENDING: "bg-amber-500/10 text-amber-400 border-amber-500/20",
            TRANSFER_REQUESTED: "bg-purple-500/10 text-purple-400 border-purple-500/20",
            TRANSFERRED: "bg-sky-500/10 text-sky-400 border-sky-500/20",
            VACATED: "bg-slate-500/10 text-slate-400 border-slate-500/20",
            CANCELLED: "bg-rose-500/10 text-rose-400 border-rose-500/20",
          };
          return (
            <Badge variant="outline" className={map[a.status] || ""}>
              {a.status.replace("_", " ")}
            </Badge>
          );
        },
      },
      {
        id: "actions",
        header: "Actions",
        cell: (a) => (
          <Link href={`/app/infrastructure/hostel/allocations/${a.id}`}>
            <Button size="sm" variant="ghost" className="h-7 text-xs text-indigo-400 hover:text-indigo-300 hover:bg-slate-800">
              <Eye className="h-3.5 w-3.5 mr-1" />
              Manage 360°
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
            <span className="text-indigo-400">Allocations</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <UserCheck className="h-6 w-6 text-indigo-400" />
            Hostel Allocations & Room Assignments
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Student hostel eligibility pipeline, room/bed assignment tracking, transfers, and clearance workflows.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <Button
            onClick={() => setAllocateModalOpen(true)}
            className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
          >
            <Plus className="h-4 w-4 mr-1.5" />
            Allocate Student
          </Button>
        </div>
      </div>

      {/* Allocation Pipeline Diagram */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">
          Hostel Allocation Pipeline
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs font-mono text-slate-300">
          <span className="px-2.5 py-1 rounded bg-slate-800 border border-slate-700">1. Student</span>
          <ArrowRight className="h-3.5 w-3.5 text-slate-600" />
          <span className="px-2.5 py-1 rounded bg-slate-800 border border-slate-700">2. Eligibility Check</span>
          <ArrowRight className="h-3.5 w-3.5 text-slate-600" />
          <span className="px-2.5 py-1 rounded bg-slate-800 border border-slate-700">3. Hostel Hall</span>
          <ArrowRight className="h-3.5 w-3.5 text-slate-600" />
          <span className="px-2.5 py-1 rounded bg-slate-800 border border-slate-700">4. Room & Bed</span>
          <ArrowRight className="h-3.5 w-3.5 text-slate-600" />
          <span className="px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-semibold">
            5. Allocation & Key Handover
          </span>
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
              placeholder="Search student name, register number, room, hostel..."
              className="pl-9 bg-slate-900 border-slate-800 text-xs text-white"
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter className="h-3.5 w-3.5 text-slate-400" />
            <select
              value={hostelFilter}
              onChange={(e) => setHostelFilter(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
            >
              <option value="ALL">All Hostels</option>
              {hostels.map((h) => (
                <option key={h.id} value={h.id}>
                  {h.name}
                </option>
              ))}
            </select>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
            >
              <option value="ALL">All Statuses</option>
              <option value="ALLOCATED">Allocated</option>
              <option value="PENDING">Pending</option>
              <option value="TRANSFER_REQUESTED">Transfer Requested</option>
              <option value="TRANSFERRED">Transferred</option>
              <option value="VACATED">Vacated</option>
            </select>
          </div>
        </div>
      </div>

      {/* DataGrid */}
      <DataGrid
        data={allocations}
        columns={columns}
        loading={loading}
        emptyMessage="No hostel allocations found."
      />

      {/* Allocate Student Modal */}
      <Dialog
        open={allocateModalOpen}
        onOpenChange={setAllocateModalOpen}
        title="Hostel Bed Allocation"
        description="Allocate an eligible student to a vacant hostel room and bed slot."
      >
        <form onSubmit={handleAllocate} className="space-y-4 pt-2">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Student Full Name *</label>
              <Input
                required
                placeholder="e.g. Siddharth Rao"
                value={form.studentName}
                onChange={(e) => setForm({ ...form, studentName: e.target.value })}
                className="bg-slate-900 border-slate-700 text-xs"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Registration / Roll No. *</label>
              <Input
                required
                placeholder="e.g. REG2024CS099"
                value={form.registerNumber}
                onChange={(e) => setForm({ ...form, registerNumber: e.target.value })}
                className="bg-slate-900 border-slate-700 text-xs"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Program Code</label>
              <Input
                value={form.programCode}
                onChange={(e) => setForm({ ...form, programCode: e.target.value })}
                className="bg-slate-900 border-slate-700 text-xs"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Academic Year</label>
              <Input
                type="number"
                min={1}
                max={5}
                value={form.year}
                onChange={(e) => setForm({ ...form, year: Number(e.target.value) })}
                className="bg-slate-900 border-slate-700 text-xs"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Semester</label>
              <Input
                type="number"
                min={1}
                max={10}
                value={form.semester}
                onChange={(e) => setForm({ ...form, semester: Number(e.target.value) })}
                className="bg-slate-900 border-slate-700 text-xs"
              />
            </div>
          </div>

          <div className="border-t border-slate-800 pt-3 space-y-3">
            <h4 className="text-xs font-bold text-slate-300 uppercase">Target Bed Slot</h4>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Hostel</label>
                <select
                  value={form.hostelId}
                  onChange={(e) => setForm({ ...form, hostelId: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200"
                >
                  {hostels.map((h) => (
                    <option key={h.id} value={h.id}>
                      {h.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Room Number</label>
                <Input
                  value={form.roomNumber}
                  onChange={(e) => setForm({ ...form, roomNumber: e.target.value })}
                  className="bg-slate-900 border-slate-700 text-xs"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Block</label>
                <Input
                  value={form.blockName}
                  onChange={(e) => setForm({ ...form, blockName: e.target.value })}
                  className="bg-slate-900 border-slate-700 text-xs"
                />
              </div>
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Bed Designation</label>
                <Input
                  value={form.bedNumber}
                  onChange={(e) => setForm({ ...form, bedNumber: e.target.value })}
                  className="bg-slate-900 border-slate-700 text-xs"
                />
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-2.5 pt-4 border-t border-slate-800">
            <Button
              type="button"
              variant="outline"
              onClick={() => setAllocateModalOpen(false)}
              className="border-slate-700 text-slate-300 text-xs"
            >
              Cancel
            </Button>
            <Button type="submit" className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs">
              Confirm & Issue Allocation
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
