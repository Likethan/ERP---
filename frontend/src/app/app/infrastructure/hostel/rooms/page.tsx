"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { hostelRoomsService } from "@/services/hostel-rooms.service";
import { hostelsService } from "@/services/hostels.service";
import {
  HostelRoom,
  Hostel,
  RoomStatus,
  RoomType,
  BedStatus,
} from "@campusos/types";
import { DataGrid, ColumnDef } from "@/components/data-grid/data-grid";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Dialog } from "@/components/ui/dialog";
import {
  DoorOpen,
  BedDouble,
  Search,
  Filter,
  Plus,
  Eye,
  CheckCircle2,
  AlertTriangle,
  Building2,
} from "lucide-react";

export default function RoomsListPage() {
  const [rooms, setRooms] = useState<HostelRoom[]>([]);
  const [hostels, setHostels] = useState<Hostel[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [hostelFilter, setHostelFilter] = useState("ALL");
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [genderFilter, setGenderFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Create Room Modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createForm, setCreateForm] = useState({
    hostelId: "hst-raman",
    blockName: "Block A",
    floor: 1,
    roomNumber: "",
    roomType: RoomType.DOUBLE,
    capacity: 2,
    gender: "MALE" as "MALE" | "FEMALE" | "ANY",
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [rRes, hRes] = await Promise.all([
        hostelRoomsService.listRooms({
          hostelId: hostelFilter,
          roomType: typeFilter,
          status: statusFilter,
          gender: genderFilter,
          search: searchQuery,
        }),
        hostelsService.listHostels(),
      ]);

      if (rRes.success && rRes.data) setRooms(rRes.data);
      if (hRes.success && hRes.data) setHostels(hRes.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [hostelFilter, typeFilter, statusFilter, genderFilter, searchQuery]);

  const handleCreateRoom = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.roomNumber) return;

    const selectedHostel = hostels.find((h) => h.id === createForm.hostelId);

    await hostelRoomsService.createRoom({
      hostelId: createForm.hostelId,
      hostelName: selectedHostel?.name || "Sir C. V. Raman Hall",
      blockId: `blk-${createForm.blockName.toLowerCase().replace(/\s+/g, "-")}`,
      blockName: createForm.blockName,
      floor: Number(createForm.floor),
      roomNumber: createForm.roomNumber,
      roomType: createForm.roomType,
      capacity: Number(createForm.capacity),
      gender: createForm.gender,
    });

    setCreateModalOpen(false);
    loadData();
  };

  const columns: ColumnDef<HostelRoom>[] = useMemo(
    () => [
      {
        id: "roomNumber",
        header: "Room Number",
        accessorKey: "roomNumber",
        cell: (r) => (
          <Link
            href={`/app/infrastructure/hostel/rooms/${r.id}`}
            className="font-bold text-white hover:text-indigo-400 transition-colors flex items-center gap-1.5"
          >
            <DoorOpen className="h-4 w-4 text-indigo-400 shrink-0" />
            <span>Room {r.roomNumber}</span>
          </Link>
        ),
      },
      {
        id: "hostel",
        header: "Hostel & Block",
        cell: (r) => (
          <div>
            <div className="text-xs font-medium text-slate-200">
              {r.hostelName}
            </div>
            <div className="text-[11px] text-slate-400">
              {r.blockName} • Floor {r.floor}
            </div>
          </div>
        ),
      },
      {
        id: "roomType",
        header: "Type",
        accessorKey: "roomType",
        cell: (r) => (
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
            {r.roomType.replace("_", " ")}
          </span>
        ),
      },
      {
        id: "capacity",
        header: "Capacity",
        accessorKey: "capacity",
        cell: (r) => (
          <span className="text-xs font-semibold text-white">
            {r.capacity} Beds
          </span>
        ),
      },
      {
        id: "occupancy",
        header: "Occupied / Available",
        cell: (r) => (
          <div className="text-xs">
            <span className="text-indigo-400 font-semibold">
              {r.occupied} occ
            </span>
            <span className="text-slate-500 mx-1">/</span>
            <span className="text-emerald-400 font-semibold">
              {r.available} avail
            </span>
          </div>
        ),
      },
      {
        id: "gender",
        header: "Gender",
        accessorKey: "gender",
        cell: (r) => <span className="text-xs text-slate-300">{r.gender}</span>,
      },
      {
        id: "status",
        header: "Status",
        accessorKey: "status",
        cell: (r) => {
          const map: Record<string, string> = {
            AVAILABLE:
              "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
            PARTIALLY_OCCUPIED: "bg-sky-500/10 text-sky-400 border-sky-500/20",
            FULL: "bg-rose-500/10 text-rose-400 border-rose-500/20",
            MAINTENANCE:
              "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
            BLOCKED: "bg-slate-500/10 text-slate-400 border-slate-500/20",
          };
          return (
            <Badge variant="outline" className={map[r.status] || ""}>
              {r.status.replace("_", " ")}
            </Badge>
          );
        },
      },
      {
        id: "actions",
        header: "Actions",
        cell: (r) => (
          <Link href={`/app/infrastructure/hostel/rooms/${r.id}`}>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 text-xs text-indigo-400 hover:text-indigo-300 hover:bg-slate-800"
            >
              <Eye className="h-3.5 w-3.5 mr-1" />
              View Beds
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
            <span className="text-indigo-400">Rooms & Beds</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <DoorOpen className="h-6 w-6 text-indigo-400" />
            Rooms & Bed Inventory
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Operational floor-level room inventory with bed-level status
            indicators and occupancy metrics.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <Button
            onClick={() => setCreateModalOpen(true)}
            className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
          >
            <Plus className="h-4 w-4 mr-1.5" />
            Register Room
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
              placeholder="Search room number, hostel, student name..."
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
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
            >
              <option value="ALL">All Room Types</option>
              <option value="SINGLE">Single</option>
              <option value="DOUBLE">Double</option>
              <option value="TRIPLE">Triple</option>
              <option value="FOUR_SHARING">Four Sharing</option>
              <option value="DORMITORY">Dormitory</option>
            </select>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
            >
              <option value="ALL">All Statuses</option>
              <option value="AVAILABLE">Available</option>
              <option value="PARTIALLY_OCCUPIED">Partially Occupied</option>
              <option value="FULL">Full</option>
              <option value="MAINTENANCE">Maintenance</option>
              <option value="BLOCKED">Blocked</option>
            </select>
          </div>
        </div>
      </div>

      {/* DataGrid */}
      <DataGrid
        data={rooms}
        columns={columns}
        loading={loading}
        emptyMessage="No rooms found matching your criteria."
      />

      {/* Create Room Modal */}
      <Dialog
        open={createModalOpen}
        onOpenChange={setCreateModalOpen}
        title="Register Room Inventory"
        description="Add a physical room unit with default bed slots to a designated hostel and block."
      >
        <form onSubmit={handleCreateRoom} className="space-y-4 pt-2">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Hostel *
              </label>
              <select
                value={createForm.hostelId}
                onChange={(e) =>
                  setCreateForm({ ...createForm, hostelId: e.target.value })
                }
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
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Block Name
              </label>
              <Input
                placeholder="Block A"
                value={createForm.blockName}
                onChange={(e) =>
                  setCreateForm({ ...createForm, blockName: e.target.value })
                }
                className="bg-slate-900 border-slate-700 text-xs"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Floor
              </label>
              <Input
                type="number"
                min={1}
                value={createForm.floor}
                onChange={(e) =>
                  setCreateForm({
                    ...createForm,
                    floor: Number(e.target.value),
                  })
                }
                className="bg-slate-900 border-slate-700 text-xs"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Room Number *
              </label>
              <Input
                required
                placeholder="e.g. 204"
                value={createForm.roomNumber}
                onChange={(e) =>
                  setCreateForm({ ...createForm, roomNumber: e.target.value })
                }
                className="bg-slate-900 border-slate-700 text-xs"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Bed Capacity
              </label>
              <Input
                type="number"
                min={1}
                max={10}
                value={createForm.capacity}
                onChange={(e) =>
                  setCreateForm({
                    ...createForm,
                    capacity: Number(e.target.value),
                  })
                }
                className="bg-slate-900 border-slate-700 text-xs"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Room Type
              </label>
              <select
                value={createForm.roomType}
                onChange={(e) =>
                  setCreateForm({
                    ...createForm,
                    roomType: e.target.value as RoomType,
                  })
                }
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200"
              >
                <option value="SINGLE">Single</option>
                <option value="DOUBLE">Double</option>
                <option value="TRIPLE">Triple</option>
                <option value="FOUR_SHARING">Four Sharing</option>
                <option value="DORMITORY">Dormitory</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Gender
              </label>
              <select
                value={createForm.gender}
                onChange={(e) =>
                  setCreateForm({
                    ...createForm,
                    gender: e.target.value as any,
                  })
                }
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200"
              >
                <option value="MALE">Male</option>
                <option value="FEMALE">Female</option>
                <option value="ANY">Any / Unrestricted</option>
              </select>
            </div>
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
              Confirm & Create Room
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
