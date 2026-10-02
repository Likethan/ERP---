"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { hostelRoomsService } from "@/services/hostel-rooms.service";
import { HostelRoom, BedStatus, RoomStatus } from "@campusos/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import {
  DoorOpen,
  BedDouble,
  User,
  Wrench,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ArrowLeft,
  Building2,
  ExternalLink,
} from "lucide-react";

export default function RoomDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const roomId = resolvedParams.id;

  const [loading, setLoading] = useState(true);
  const [room, setRoom] = useState<HostelRoom | null>(null);

  // Status Change Dialog
  const [selectedBedId, setSelectedBedId] = useState<string | null>(null);
  const [newBedStatus, setNewBedStatus] = useState<BedStatus>(BedStatus.MAINTENANCE);
  const [statusModalOpen, setStatusModalOpen] = useState(false);

  const loadRoom = async () => {
    setLoading(true);
    try {
      const res = await hostelRoomsService.getRoomById(roomId);
      if (res.success && res.data) {
        setRoom(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRoom();
  }, [roomId]);

  const handleUpdateBedStatus = async () => {
    if (!selectedBedId || !room) return;
    await hostelRoomsService.updateBedStatus(room.id, selectedBedId, newBedStatus);
    setStatusModalOpen(false);
    loadRoom();
  };

  if (loading) {
    return (
      <div className="p-6 lg:p-8 space-y-6 max-w-5xl mx-auto">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 w-full rounded-xl" />
        <Skeleton className="h-64 w-full rounded-xl" />
      </div>
    );
  }

  if (!room) {
    return (
      <div className="p-12 text-center text-slate-400">
        <h2 className="text-lg font-bold text-white mb-2">Room Record Not Found</h2>
        <p className="text-xs mb-4">No room was found matching &ldquo;{roomId}&rdquo;.</p>
        <Link href="/app/infrastructure/hostel/rooms">
          <Button variant="outline" className="border-slate-700">
            Back to Room Inventory
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-5xl mx-auto text-slate-100">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-slate-400">
        <Link href="/app/infrastructure" className="hover:text-white">
          Infrastructure
        </Link>
        <span>/</span>
        <Link href="/app/infrastructure/hostel/rooms" className="hover:text-white">
          Rooms
        </Link>
        <span>/</span>
        <span className="text-indigo-400 font-mono">Room {room.roomNumber}</span>
      </div>

      {/* Header Card */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <Badge variant="outline" className="bg-indigo-500/10 text-indigo-400 border-indigo-500/20">
              {room.roomType.replace("_", " ")}
            </Badge>
            <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
              {room.status}
            </Badge>
          </div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <DoorOpen className="h-6 w-6 text-indigo-400" />
            Room {room.roomNumber}
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            {room.hostelName} • {room.blockName} • Floor {room.floor} • Capacity: {room.capacity} Beds
          </p>
        </div>

        <div className="flex items-center gap-3 text-center">
          <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 min-w-[90px]">
            <div className="text-[10px] text-slate-400 uppercase font-semibold">Occupied</div>
            <div className="text-lg font-bold text-white mt-0.5">{room.occupied}</div>
          </div>
          <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 min-w-[90px]">
            <div className="text-[10px] text-slate-400 uppercase font-semibold">Available</div>
            <div className="text-lg font-bold text-emerald-400 mt-0.5">{room.available}</div>
          </div>
        </div>
      </div>

      {/* Bed Slots Grid */}
      <div className="space-y-3">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <BedDouble className="h-4 w-4 text-indigo-400" />
          Individual Bed Slots Allocation State
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {room.beds?.map((bed) => {
            const isAllocated = bed.status === BedStatus.ALLOCATED;
            const isAvailable = bed.status === BedStatus.AVAILABLE;
            const isMaintenance = bed.status === BedStatus.MAINTENANCE;

            return (
              <div
                key={bed.id}
                className={`p-4 rounded-xl border transition-all ${
                  isAllocated
                    ? "border-indigo-500/30 bg-slate-900/80"
                    : isAvailable
                    ? "border-emerald-500/30 bg-emerald-950/10"
                    : "border-yellow-500/30 bg-yellow-950/10"
                }`}
              >
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <BedDouble
                      className={`h-5 w-5 ${
                        isAllocated ? "text-indigo-400" : isAvailable ? "text-emerald-400" : "text-yellow-400"
                      }`}
                    />
                    <span className="font-bold text-white text-sm">{bed.bedNumber}</span>
                  </div>
                  <Badge
                    variant="outline"
                    className={
                      isAllocated
                        ? "bg-indigo-500/20 text-indigo-300 border-indigo-500/40"
                        : isAvailable
                        ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                        : "bg-yellow-500/20 text-yellow-300 border-yellow-500/40"
                    }
                  >
                    {bed.status}
                  </Badge>
                </div>

                <div className="py-3 text-xs space-y-1.5">
                  {isAllocated ? (
                    <div>
                      <div className="font-semibold text-white flex items-center gap-1.5">
                        <User className="h-3.5 w-3.5 text-slate-400" />
                        <span>{bed.studentName}</span>
                      </div>
                      <div className="text-slate-400 font-mono text-[11px] pl-5">
                        Roll: {bed.studentRollNumber}
                      </div>
                      {bed.studentId && (
                        <div className="pl-5 pt-1">
                          <Link
                            href={`/app/students/${bed.studentId}`}
                            className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1 text-[11px]"
                          >
                            Open Student 360° Profile <ExternalLink className="h-2.5 w-2.5" />
                          </Link>
                        </div>
                      )}
                    </div>
                  ) : isAvailable ? (
                    <div className="text-emerald-400/90 font-medium flex items-center gap-1.5">
                      <CheckCircle2 className="h-4 w-4" />
                      Ready for immediate student allocation
                    </div>
                  ) : (
                    <div className="text-yellow-400/90 font-medium flex items-center gap-1.5">
                      <Wrench className="h-4 w-4" />
                      Bed slot under maintenance inspection
                    </div>
                  )}
                </div>

                <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      setSelectedBedId(bed.id);
                      setNewBedStatus(
                        isMaintenance ? BedStatus.AVAILABLE : BedStatus.MAINTENANCE
                      );
                      setStatusModalOpen(true);
                    }}
                    className="text-xs text-slate-400 hover:text-white"
                  >
                    Change Bed Status
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Bed Status Update Modal */}
      <Dialog
        open={statusModalOpen}
        onOpenChange={setStatusModalOpen}
        title="Update Bed Slot Status"
        description="Modify the operational availability of this bed slot."
      >
        <div className="space-y-4 pt-2">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">New Bed Status</label>
            <select
              value={newBedStatus}
              onChange={(e) => setNewBedStatus(e.target.value as BedStatus)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200"
            >
              <option value={BedStatus.AVAILABLE}>AVAILABLE</option>
              <option value={BedStatus.MAINTENANCE}>MAINTENANCE</option>
              <option value={BedStatus.BLOCKED}>BLOCKED</option>
            </select>
          </div>

          <div className="flex justify-end gap-2.5 pt-4 border-t border-slate-800">
            <Button
              type="button"
              variant="outline"
              onClick={() => setStatusModalOpen(false)}
              className="border-slate-700 text-slate-300 text-xs"
            >
              Cancel
            </Button>
            <Button onClick={handleUpdateBedStatus} className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs">
              Confirm Status Update
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
