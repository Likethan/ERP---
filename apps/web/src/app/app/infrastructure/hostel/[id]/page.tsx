"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { hostelsService } from "@/services/hostels.service";
import { hostelRoomsService } from "@/services/hostel-rooms.service";
import { hostelAllocationsService } from "@/services/hostel-allocations.service";
import { hostelLeavesService } from "@/services/hostel-leaves.service";
import { hostelComplaintsService } from "@/services/hostel-complaints.service";
import { maintenanceService } from "@/services/maintenance.service";
import {
  Hostel,
  HostelRoom,
  HostelAllocation,
  HostelLeave,
  HostelComplaint,
  MaintenanceRequest,
} from "@campusos/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import {
  BedDouble,
  Building2,
  Users,
  Phone,
  Mail,
  DoorOpen,
  FileCheck2,
  AlertCircle,
  Wrench,
  Clock,
  ArrowLeft,
  ChevronRight,
  ShieldCheck,
  CheckCircle2,
  Calendar,
  Layers,
} from "lucide-react";

export default function HostelDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const hostelId = resolvedParams.id;

  const [loading, setLoading] = useState(true);
  const [hostel, setHostel] = useState<Hostel | null>(null);
  const [rooms, setRooms] = useState<HostelRoom[]>([]);
  const [allocations, setAllocations] = useState<HostelAllocation[]>([]);
  const [leaves, setLeaves] = useState<HostelLeave[]>([]);
  const [complaints, setComplaints] = useState<HostelComplaint[]>([]);
  const [maintenance, setMaintenance] = useState<MaintenanceRequest[]>([]);

  useEffect(() => {
    async function loadAll() {
      setLoading(true);
      try {
        const [hRes, rRes, aRes, lRes, cRes, mRes] = await Promise.all([
          hostelsService.getHostelById(hostelId),
          hostelRoomsService.listRooms({ hostelId }),
          hostelAllocationsService.listHostelAllocations({ hostelId }),
          hostelLeavesService.listHostelLeaves({ hostelId }),
          hostelComplaintsService.listHostelComplaints({ hostelId }),
          maintenanceService.listMaintenanceRequests({ sourceType: "HOSTEL" }),
        ]);

        if (hRes.success && hRes.data) setHostel(hRes.data);
        if (rRes.success && rRes.data) setRooms(rRes.data);
        if (aRes.success && aRes.data) setAllocations(aRes.data);
        if (lRes.success && lRes.data) setLeaves(lRes.data);
        if (cRes.success && cRes.data) setComplaints(cRes.data);
        if (mRes.success && mRes.data) setMaintenance(mRes.data);
      } finally {
        setLoading(false);
      }
    }
    loadAll();
  }, [hostelId]);

  if (loading) {
    return (
      <div className="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 w-full rounded-xl" />
        <Skeleton className="h-96 w-full rounded-xl" />
      </div>
    );
  }

  if (!hostel) {
    return (
      <div className="p-12 text-center text-slate-400">
        <h2 className="text-lg font-bold text-white mb-2">Hostel Not Found</h2>
        <p className="text-xs mb-4">No residential hall matched ID &ldquo;{hostelId}&rdquo;.</p>
        <Link href="/app/infrastructure/hostel">
          <Button variant="outline" className="border-slate-700">
            Back to Hostels
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto text-slate-100">
      {/* Breadcrumb & Navigation */}
      <div className="flex items-center gap-2 text-xs text-slate-400">
        <Link href="/app/infrastructure" className="hover:text-white">
          Infrastructure
        </Link>
        <span>/</span>
        <Link href="/app/infrastructure/hostel" className="hover:text-white">
          Hostels
        </Link>
        <span>/</span>
        <span className="text-indigo-400 font-mono">{hostel.code}</span>
      </div>

      {/* Hero 360 Header */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              {hostel.code}
            </span>
            <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
              {hostel.status}
            </Badge>
            <Badge variant="outline" className="bg-sky-500/10 text-sky-400 border-sky-500/20">
              {hostel.type} • {hostel.gender}
            </Badge>
          </div>
          <h1 className="text-2xl lg:text-3xl font-bold text-white flex items-center gap-2">
            <BedDouble className="h-7 w-7 text-indigo-400" />
            {hostel.name}
          </h1>
          <p className="text-xs text-slate-400 max-w-xl">
            {hostel.campusName} • Managed by Chief Warden {hostel.wardenName}
          </p>
        </div>

        {/* Quick KPI meters */}
        <div className="grid grid-cols-3 gap-3 border-t lg:border-t-0 lg:border-l border-slate-800 pt-4 lg:pt-0 lg:pl-6 text-center">
          <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">Total Beds</div>
            <div className="text-xl font-bold text-white mt-0.5">{hostel.totalBeds}</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">Occupancy</div>
            <div className="text-xl font-bold text-indigo-400 mt-0.5">{hostel.occupancyPercentage}%</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">Vacant</div>
            <div className="text-xl font-bold text-emerald-400 mt-0.5">{hostel.availableBeds}</div>
          </div>
        </div>
      </div>

      {/* 360 Operational Tabs */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="bg-slate-900 border border-slate-800 p-1 rounded-xl flex flex-wrap gap-1">
          <TabsTrigger value="overview" className="text-xs data-[state=active]:bg-indigo-600 data-[state=active]:text-white">
            Overview
          </TabsTrigger>
          <TabsTrigger value="blocks" className="text-xs data-[state=active]:bg-indigo-600 data-[state=active]:text-white">
            Blocks Hierarchy
          </TabsTrigger>
          <TabsTrigger value="rooms" className="text-xs data-[state=active]:bg-indigo-600 data-[state=active]:text-white">
            Rooms ({rooms.length})
          </TabsTrigger>
          <TabsTrigger value="residents" className="text-xs data-[state=active]:bg-indigo-600 data-[state=active]:text-white">
            Residents ({allocations.length})
          </TabsTrigger>
          <TabsTrigger value="leaves" className="text-xs data-[state=active]:bg-indigo-600 data-[state=active]:text-white">
            Leaves ({leaves.length})
          </TabsTrigger>
          <TabsTrigger value="complaints" className="text-xs data-[state=active]:bg-indigo-600 data-[state=active]:text-white">
            Complaints ({complaints.length})
          </TabsTrigger>
          <TabsTrigger value="maintenance" className="text-xs data-[state=active]:bg-indigo-600 data-[state=active]:text-white">
            Maintenance ({maintenance.length})
          </TabsTrigger>
          <TabsTrigger value="activity" className="text-xs data-[state=active]:bg-indigo-600 data-[state=active]:text-white">
            Activity Timeline
          </TabsTrigger>
        </TabsList>

        {/* Tab 1: Overview */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Building2 className="h-4 w-4 text-indigo-400" />
                Administrative & Capacity Details
              </h3>
              <div className="space-y-2.5 text-xs text-slate-300">
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-400">Campus Location:</span>
                  <span className="text-white font-medium">{hostel.campusName}</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-400">Hostel Classification:</span>
                  <span>{hostel.type} Dormitory</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-400">Total Structural Blocks:</span>
                  <span>{hostel.totalBlocks} Blocks</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-400">Room Inventory:</span>
                  <span>{hostel.totalRooms} Rooms</span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-slate-800">
                  <span className="text-slate-400">Occupancy Status:</span>
                  <span className="text-emerald-400 font-semibold">
                    {hostel.occupiedBeds} occupied / {hostel.availableBeds} beds available
                  </span>
                </div>
                <div className="flex justify-between py-1.5">
                  <span className="text-slate-400">Operating Status:</span>
                  <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
                    {hostel.status}
                  </Badge>
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Users className="h-4 w-4 text-indigo-400" />
                Warden & Caretaker Office
              </h3>
              <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-3">
                <div className="text-sm font-semibold text-white">{hostel.wardenName}</div>
                <div className="text-xs text-slate-400">Chief Hall Warden • Faculty In-Charge</div>
                <div className="pt-2 border-t border-slate-800/80 space-y-2 text-xs">
                  <div className="flex items-center gap-2 text-slate-300">
                    <Phone className="h-3.5 w-3.5 text-indigo-400" />
                    <span>{hostel.wardenPhone}</span>
                  </div>
                  <div className="flex items-center gap-2 text-slate-300">
                    <Mail className="h-3.5 w-3.5 text-indigo-400" />
                    <span>{hostel.wardenEmail}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* Tab 2: Blocks Hierarchy Visualization */}
        <TabsContent value="blocks" className="space-y-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-2 flex items-center gap-2">
              <Layers className="h-4 w-4 text-indigo-400" />
              Structural Hierarchy Tree
            </h3>
            <p className="text-xs text-slate-400 mb-6">
              Institutional hierarchy: {hostel.campusName} → {hostel.name} → Blocks → Floors → Rooms.
            </p>

            <div className="space-y-6">
              {hostel.blocks?.map((block) => (
                <div key={block.id} className="border border-slate-800 rounded-xl bg-slate-900/80 p-4">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                    <div className="flex items-center gap-2 font-bold text-white text-sm">
                      <Building2 className="h-4 w-4 text-indigo-400" />
                      <span>{block.name}</span>
                    </div>
                    <span className="text-xs font-mono text-slate-400">
                      {block.occupiedBeds} / {block.totalBeds} Beds ({block.floorsCount} Floors, {block.roomsCount} Rooms)
                    </span>
                  </div>

                  <div className="mt-4 pl-4 border-l-2 border-slate-800 space-y-4">
                    {block.floors?.map((floor) => (
                      <div key={floor.floorNumber} className="space-y-2">
                        <div className="text-xs font-semibold text-indigo-300 flex items-center gap-2">
                          <span className="h-1.5 w-1.5 rounded-full bg-indigo-400" />
                          Floor {floor.floorNumber} ({floor.name})
                        </div>
                        <div className="pl-4 flex flex-wrap gap-2">
                          {rooms
                            .filter((r) => r.blockId === block.id && r.floor === floor.floorNumber)
                            .map((room) => (
                              <Link
                                key={room.id}
                                href={`/app/infrastructure/hostel/rooms/${room.id}`}
                                className="px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-950 hover:border-indigo-500/50 hover:bg-slate-900 text-xs transition-colors flex items-center gap-2"
                              >
                                <DoorOpen className="h-3.5 w-3.5 text-slate-400" />
                                <span className="font-semibold text-white">Room {room.roomNumber}</span>
                                <Badge
                                  variant="outline"
                                  className={
                                    room.status === "FULL"
                                      ? "bg-rose-500/10 text-rose-400 text-[10px]"
                                      : "bg-emerald-500/10 text-emerald-400 text-[10px]"
                                  }
                                >
                                  {room.occupied}/{room.capacity}
                                </Badge>
                              </Link>
                            ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </TabsContent>

        {/* Tab 3: Rooms Inventory */}
        <TabsContent value="rooms" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {rooms.map((room) => (
              <div key={room.id} className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="font-bold text-white text-sm flex items-center gap-1.5">
                    <DoorOpen className="h-4 w-4 text-indigo-400" />
                    Room {room.roomNumber}
                  </div>
                  <Badge variant="outline" className="text-[10px]">
                    {room.status}
                  </Badge>
                </div>
                <div className="text-xs text-slate-400">
                  {room.blockName} • Floor {room.floor} • {room.roomType}
                </div>
                <div className="text-xs text-slate-300 font-mono">
                  Capacity: {room.capacity} | Occupied: {room.occupied} | Available: {room.available}
                </div>
                <div className="pt-2 border-t border-slate-800 flex justify-between items-center">
                  <Link
                    href={`/app/infrastructure/hostel/rooms/${room.id}`}
                    className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                  >
                    Inspect Beds <ChevronRight className="h-3 w-3" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </TabsContent>

        {/* Tab 4: Residents */}
        <TabsContent value="residents" className="space-y-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 overflow-x-auto">
            <table className="w-full text-xs text-left text-slate-300">
              <thead className="border-b border-slate-800 text-[11px] uppercase font-bold text-slate-400">
                <tr>
                  <th className="py-2.5 px-3">Student Name</th>
                  <th className="py-2.5 px-3">Register No.</th>
                  <th className="py-2.5 px-3">Program</th>
                  <th className="py-2.5 px-3">Room & Bed</th>
                  <th className="py-2.5 px-3">Allocated Date</th>
                  <th className="py-2.5 px-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {allocations.map((alloc) => (
                  <tr key={alloc.id} className="hover:bg-slate-800/50">
                    <td className="py-3 px-3 font-semibold text-white">{alloc.studentName}</td>
                    <td className="py-3 px-3 font-mono">{alloc.registerNumber}</td>
                    <td className="py-3 px-3">{alloc.programCode} (Yr {alloc.year})</td>
                    <td className="py-3 px-3">
                      Room {alloc.roomNumber} ({alloc.bedNumber})
                    </td>
                    <td className="py-3 px-3">{alloc.allocatedDate}</td>
                    <td className="py-3 px-3">
                      <Link
                        href={`/app/infrastructure/hostel/allocations/${alloc.id}`}
                        className="text-indigo-400 hover:underline"
                      >
                        Allocation 360°
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </TabsContent>

        {/* Tab 5: Leaves */}
        <TabsContent value="leaves" className="space-y-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 overflow-x-auto">
            <table className="w-full text-xs text-left text-slate-300">
              <thead className="border-b border-slate-800 text-[11px] uppercase font-bold text-slate-400">
                <tr>
                  <th className="py-2.5 px-3">Student</th>
                  <th className="py-2.5 px-3">Dates</th>
                  <th className="py-2.5 px-3">Destination</th>
                  <th className="py-2.5 px-3">Reason</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {leaves.map((l) => (
                  <tr key={l.id} className="hover:bg-slate-800/50">
                    <td className="py-3 px-3 font-semibold text-white">
                      {l.studentName}
                      <div className="text-[10px] text-slate-400 font-mono">Room {l.roomNumber}</div>
                    </td>
                    <td className="py-3 px-3">
                      {l.startDate} → {l.endDate}
                    </td>
                    <td className="py-3 px-3">{l.destination}</td>
                    <td className="py-3 px-3 truncate max-w-xs">{l.reason}</td>
                    <td className="py-3 px-3">
                      <Badge variant="outline" className="text-[10px]">
                        {l.approvalStatus}
                      </Badge>
                    </td>
                    <td className="py-3 px-3">
                      <Link href={`/app/infrastructure/hostel/leaves/${l.id}`} className="text-indigo-400 hover:underline">
                        Review
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </TabsContent>

        {/* Tab 6: Complaints */}
        <TabsContent value="complaints" className="space-y-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3">
            {complaints.map((c) => (
              <div key={c.id} className="p-3.5 rounded-lg border border-slate-800 bg-slate-900 flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-xs text-indigo-400">{c.ticketNumber}</span>
                    <Badge variant="outline" className="text-[10px]">
                      {c.category}
                    </Badge>
                    <Badge variant="outline" className="text-[10px] text-yellow-400 border-yellow-500/20">
                      {c.priority} Priority
                    </Badge>
                  </div>
                  <h4 className="text-xs font-semibold text-white">{c.title}</h4>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Room {c.roomNumber} • Logged by {c.studentName} • {c.createdAt.split("T")[0]}
                  </p>
                </div>
                <Link href={`/app/infrastructure/hostel/complaints/${c.id}`}>
                  <Button size="sm" variant="ghost" className="text-indigo-400 hover:bg-slate-800 text-xs">
                    Inspect Ticket
                  </Button>
                </Link>
              </div>
            ))}
          </div>
        </TabsContent>

        {/* Tab 7: Maintenance */}
        <TabsContent value="maintenance" className="space-y-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3">
            {maintenance.map((m) => (
              <div key={m.id} className="p-3.5 rounded-lg border border-slate-800 bg-slate-900 flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-xs text-rose-400">{m.workOrderNumber}</span>
                    <Badge variant="outline" className="text-[10px]">
                      {m.category}
                    </Badge>
                    <span className="text-[10px] font-mono text-slate-400">Est. ₹{m.estimatedCostInr.toLocaleString("en-IN")}</span>
                  </div>
                  <h4 className="text-xs font-semibold text-white">{m.title}</h4>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    {m.location} • Status: {m.status}
                  </p>
                </div>
                <Link href={`/app/infrastructure/maintenance/${m.id}`}>
                  <Button size="sm" variant="ghost" className="text-rose-400 hover:bg-slate-800 text-xs">
                    View Work Order
                  </Button>
                </Link>
              </div>
            ))}
          </div>
        </TabsContent>

        {/* Tab 8: Activity Timeline */}
        <TabsContent value="activity" className="space-y-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
              <Clock className="h-4 w-4 text-indigo-400" />
              Hostel Operational Activity Log
            </h3>
            <div className="space-y-4 pl-4 border-l-2 border-slate-800">
              <div className="relative">
                <span className="absolute -left-[23px] top-1 h-3 w-3 rounded-full bg-indigo-500 border-2 border-slate-950" />
                <div className="text-xs font-semibold text-white">Bed 304 Bed A Allocation Handover</div>
                <div className="text-[11px] text-slate-400">Key handover confirmed by resident Aarav Patel • 2024-08-05</div>
              </div>
              <div className="relative">
                <span className="absolute -left-[23px] top-1 h-3 w-3 rounded-full bg-emerald-500 border-2 border-slate-950" />
                <div className="text-xs font-semibold text-white">WiFi AP-304 Ticket Logged</div>
                <div className="text-[11px] text-slate-400">Student complaint logged for 3rd floor corridor • Yesterday</div>
              </div>
              <div className="relative">
                <span className="absolute -left-[23px] top-1 h-3 w-3 rounded-full bg-yellow-500 border-2 border-slate-950" />
                <div className="text-xs font-semibold text-white">Bed 204 Bed 04 Placed in Maintenance</div>
                <div className="text-[11px] text-slate-400">Ladder repair order WO-2026-107 issued • Today</div>
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
