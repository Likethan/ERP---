"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { hostelsService } from "@/services/hostels.service";
import { Hostel, HostelStatus, HostelType } from "@campusos/types";
import { useAuth } from "@/lib/auth-context";
import { DataGrid, ColumnDef } from "@/components/data-grid/data-grid";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  BedDouble,
  Building2,
  Users,
  Search,
  Plus,
  Filter,
  Eye,
  Phone,
  Mail,
  DoorOpen,
  Layers,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";

export default function HostelListPage() {
  const { user } = useAuth();
  const [hostels, setHostels] = useState<Hostel[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [campusFilter, setCampusFilter] = useState("ALL");
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [genderFilter, setGenderFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Create Modal State
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createForm, setCreateForm] = useState({
    name: "",
    code: "",
    type: "BOYS" as HostelType,
    gender: "BOYS" as "BOYS" | "GIRLS" | "MIXED",
    wardenName: "",
    wardenPhone: "",
    wardenEmail: "",
    totalBlocks: 2,
    totalRooms: 100,
    totalBeds: 200,
  });

  const loadHostels = async () => {
    setLoading(true);
    try {
      const res = await hostelsService.listHostels({
        campusId: campusFilter,
        type: typeFilter,
        gender: genderFilter,
        status: statusFilter,
        search: searchQuery,
      });
      if (res.success && res.data) {
        setHostels(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHostels();
  }, [campusFilter, typeFilter, genderFilter, statusFilter, searchQuery]);

  const handleCreateHostel = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.name || !createForm.code) return;

    await hostelsService.createHostel({
      name: createForm.name,
      code: createForm.code,
      type: createForm.type,
      gender: createForm.gender,
      wardenName: createForm.wardenName || "Assigned Warden",
      wardenPhone: createForm.wardenPhone || "+91 94480 00000",
      wardenEmail: createForm.wardenEmail || "warden@campusos.edu",
      totalBlocks: Number(createForm.totalBlocks),
      totalRooms: Number(createForm.totalRooms),
      totalBeds: Number(createForm.totalBeds),
      occupiedBeds: 0,
      status: HostelStatus.ACTIVE,
    });

    setCreateModalOpen(false);
    loadHostels();
  };

  const columns: ColumnDef<Hostel>[] = useMemo(
    () => [
      {
        id: "name",
        header: "Hostel & Code",
        accessorKey: "name",
        cell: (h) => (
          <div>
            <Link
              href={`/app/infrastructure/hostel/${h.id}`}
              className="font-semibold text-white hover:text-indigo-400 transition-colors flex items-center gap-1.5"
            >
              <BedDouble className="h-4 w-4 text-indigo-400 shrink-0" />
              <span>{h.name}</span>
            </Link>
            <div className="text-[11px] font-mono text-slate-400 mt-0.5">
              {h.code}
            </div>
          </div>
        ),
      },
      {
        id: "campus",
        header: "Campus",
        accessorKey: "campusName",
        cell: (h) => (
          <span className="text-slate-300 text-xs">{h.campusName}</span>
        ),
      },
      {
        id: "type",
        header: "Type",
        accessorKey: "type",
        cell: (h) => {
          const colorMap: Record<string, string> = {
            BOYS: "bg-blue-500/10 text-blue-400 border-blue-500/20",
            GIRLS: "bg-pink-500/10 text-pink-400 border-pink-500/20",
            MIXED: "bg-purple-500/10 text-purple-400 border-purple-500/20",
            STAFF: "bg-amber-500/10 text-amber-400 border-amber-500/20",
            GUEST: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
          };
          return (
            <Badge variant="outline" className={colorMap[h.type] || ""}>
              {h.type}
            </Badge>
          );
        },
      },
      {
        id: "capacity",
        header: "Beds & Capacity",
        cell: (h) => (
          <div>
            <div className="text-xs font-semibold text-white">
              {h.occupiedBeds} / {h.totalBeds} Beds
            </div>
            <div className="text-[11px] text-slate-400">
              {h.totalBlocks} Blocks • {h.totalRooms} Rooms
            </div>
          </div>
        ),
      },
      {
        id: "available",
        header: "Available",
        accessorKey: "availableBeds",
        cell: (h) => (
          <span className="font-semibold text-emerald-400 text-xs">
            {h.availableBeds} vacant
          </span>
        ),
      },
      {
        id: "occupancy",
        header: "Occupancy %",
        accessorKey: "occupancyPercentage",
        cell: (h) => {
          const pct = h.occupancyPercentage;
          const barColor =
            pct >= 90
              ? "bg-rose-500"
              : pct >= 75
                ? "bg-emerald-500"
                : "bg-sky-500";
          return (
            <div className="w-28 space-y-1">
              <div className="flex justify-between text-[11px]">
                <span className="font-medium text-white">{pct}%</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                <div
                  className={`${barColor} h-1.5 rounded-full`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        },
      },
      {
        id: "warden",
        header: "Warden",
        cell: (h) => (
          <div>
            <div className="text-xs font-medium text-slate-200">
              {h.wardenName}
            </div>
            <div className="text-[11px] text-slate-400 flex items-center gap-2 mt-0.5">
              <span>{h.wardenPhone}</span>
            </div>
          </div>
        ),
      },
      {
        id: "status",
        header: "Status",
        accessorKey: "status",
        cell: (h) => {
          const isAct = h.status === HostelStatus.ACTIVE;
          return (
            <Badge
              variant="outline"
              className={
                isAct
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                  : "bg-yellow-500/10 text-yellow-400 border-yellow-500/20"
              }
            >
              {h.status.replace("_", " ")}
            </Badge>
          );
        },
      },
      {
        id: "actions",
        header: "Actions",
        cell: (h) => (
          <div className="flex items-center gap-1.5">
            <Link href={`/app/infrastructure/hostel/${h.id}`}>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 px-2 text-indigo-400 hover:text-indigo-300 hover:bg-slate-800"
              >
                <Eye className="h-3.5 w-3.5 mr-1" />
                View 360°
              </Button>
            </Link>
          </div>
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
            <span className="text-indigo-400">Hostel Directory</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <BedDouble className="h-6 w-6 text-indigo-400" />
            Hostels & Residential Dormitories
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Manage residential halls, wardens, capacity quotas, occupancy
            levels, and dormitory blocks.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <Link href="/app/infrastructure/hostel/rooms">
            <Button
              variant="outline"
              className="border-slate-700 hover:bg-slate-800 text-slate-300 text-xs"
            >
              <DoorOpen className="h-3.5 w-3.5 mr-1.5 text-sky-400" />
              Room Inventory
            </Button>
          </Link>
          <Button
            onClick={() => setCreateModalOpen(true)}
            className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
          >
            <Plus className="h-4 w-4 mr-1.5" />
            Add Hostel Hall
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
              placeholder="Search hostel name, code, warden, campus..."
              className="pl-9 bg-slate-900 border-slate-800 text-xs text-white"
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter className="h-3.5 w-3.5 text-slate-400" />
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
            >
              <option value="ALL">All Types</option>
              <option value="BOYS">Boys Hostel</option>
              <option value="GIRLS">Girls Hostel</option>
              <option value="MIXED">Mixed / PG House</option>
              <option value="STAFF">Staff Quarters</option>
              <option value="GUEST">Guest Residence</option>
            </select>

            <select
              value={genderFilter}
              onChange={(e) => setGenderFilter(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
            >
              <option value="ALL">All Genders</option>
              <option value="BOYS">Boys</option>
              <option value="GIRLS">Girls</option>
              <option value="MIXED">Mixed</option>
            </select>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200"
            >
              <option value="ALL">All Statuses</option>
              <option value="ACTIVE">Active</option>
              <option value="UNDER_MAINTENANCE">Under Maintenance</option>
              <option value="CLOSED">Closed</option>
            </select>
          </div>
        </div>
      </div>

      {/* DataGrid */}
      <DataGrid
        data={hostels}
        columns={columns}
        loading={loading}
        emptyMessage="No hostels found matching your criteria."
      />

      {/* Create Hostel Modal */}
      <Dialog
        open={createModalOpen}
        onOpenChange={setCreateModalOpen}
        title="Register New Hostel Hall of Residence"
        description="Establish a new residential hall with designated blocks, initial capacity, and warden contact."
      >
        <form onSubmit={handleCreateHostel} className="space-y-4 pt-2">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Hostel Name *
              </label>
              <Input
                required
                placeholder="e.g. Homi Bhabha Hall of Residence"
                value={createForm.name}
                onChange={(e) =>
                  setCreateForm({ ...createForm, name: e.target.value })
                }
                className="bg-slate-900 border-slate-700 text-xs"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Hostel Code *
              </label>
              <Input
                required
                placeholder="e.g. HOSTEL-BHABHA"
                value={createForm.code}
                onChange={(e) =>
                  setCreateForm({ ...createForm, code: e.target.value })
                }
                className="bg-slate-900 border-slate-700 text-xs"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Hostel Type
              </label>
              <select
                value={createForm.type}
                onChange={(e) =>
                  setCreateForm({
                    ...createForm,
                    type: e.target.value as HostelType,
                  })
                }
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200"
              >
                <option value="BOYS">Boys</option>
                <option value="GIRLS">Girls</option>
                <option value="MIXED">Mixed / PG</option>
                <option value="STAFF">Staff Residence</option>
                <option value="GUEST">Guest House</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Gender Restriction
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
                <option value="BOYS">Boys Only</option>
                <option value="GIRLS">Girls Only</option>
                <option value="MIXED">Mixed Gender</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Total Blocks
              </label>
              <Input
                type="number"
                min={1}
                value={createForm.totalBlocks}
                onChange={(e) =>
                  setCreateForm({
                    ...createForm,
                    totalBlocks: Number(e.target.value),
                  })
                }
                className="bg-slate-900 border-slate-700 text-xs"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Total Rooms
              </label>
              <Input
                type="number"
                min={1}
                value={createForm.totalRooms}
                onChange={(e) =>
                  setCreateForm({
                    ...createForm,
                    totalRooms: Number(e.target.value),
                  })
                }
                className="bg-slate-900 border-slate-700 text-xs"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Total Beds
              </label>
              <Input
                type="number"
                min={1}
                value={createForm.totalBeds}
                onChange={(e) =>
                  setCreateForm({
                    ...createForm,
                    totalBeds: Number(e.target.value),
                  })
                }
                className="bg-slate-900 border-slate-700 text-xs"
              />
            </div>
          </div>

          <div className="border-t border-slate-800 pt-3">
            <h4 className="text-xs font-bold text-slate-300 uppercase mb-2">
              Warden In-Charge
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">
                  Warden Name
                </label>
                <Input
                  placeholder="Prof. Name"
                  value={createForm.wardenName}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, wardenName: e.target.value })
                  }
                  className="bg-slate-900 border-slate-700 text-xs"
                />
              </div>
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">
                  Phone Number
                </label>
                <Input
                  placeholder="+91 94480 00000"
                  value={createForm.wardenPhone}
                  onChange={(e) =>
                    setCreateForm({
                      ...createForm,
                      wardenPhone: e.target.value,
                    })
                  }
                  className="bg-slate-900 border-slate-700 text-xs"
                />
              </div>
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">
                  Email
                </label>
                <Input
                  placeholder="warden@campusos.edu"
                  value={createForm.wardenEmail}
                  onChange={(e) =>
                    setCreateForm({
                      ...createForm,
                      wardenEmail: e.target.value,
                    })
                  }
                  className="bg-slate-900 border-slate-700 text-xs"
                />
              </div>
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
              Confirm & Create Hall
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
