"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { infrastructureService } from "@/services/infrastructure.service";
import {
  HostelItem,
  HostelRoomItem,
} from "@/mocks/infrastructure.mock";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { useToast } from "@/components/ui/toast";
import {
  Building2,
  Bed,
  Users,
  Wrench,
  Search,
  Filter,
  CheckCircle2,
  Phone,
  DoorOpen,
} from "lucide-react";

export default function HostelManagementPage() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [hostels, setHostels] = useState<HostelItem[]>([]);
  const [rooms, setRooms] = useState<HostelRoomItem[]>([]);

  // Filter states
  const [selectedHostel, setSelectedHostel] = useState<string>("ALL");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState<"rooms" | "hostels" | "wardens">("rooms");

  // Allocate Room Modal
  const [allocateModalOpen, setAllocateModalOpen] = useState(false);
  const [allocatingRoom, setAllocatingRoom] = useState<HostelRoomItem | null>(null);
  const [allocateForm, setAllocateForm] = useState({
    studentName: "",
    rollNumber: "",
    remarks: "",
  });

  async function loadData() {
    try {
      setLoading(true);
      const [hstRes, rmRes] = await Promise.all([
        infrastructureService.getHostels(),
        infrastructureService.getRooms(),
      ]);
      setHostels(hstRes.data || []);
      setRooms(rmRes.data || []);
    } catch {
      toast({
        title: "Error loading hostel data",
        description: "Falling back to local cache.",
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const totalCapacity = hostels.reduce((acc, h) => acc + h.capacityBeds, 0);
  const totalOccupied = hostels.reduce((acc, h) => acc + h.occupiedBeds, 0);
  const totalAvailable = totalCapacity - totalOccupied;
  const occupancyRate = totalCapacity > 0 ? Math.round((totalOccupied / totalCapacity) * 100) : 0;

  const filteredRooms = rooms.filter((rm) => {
    const matchesHostel =
      selectedHostel === "ALL" || rm.hostelName.toLowerCase().includes(selectedHostel.toLowerCase());
    const matchesStatus = selectedStatus === "ALL" || rm.status === selectedStatus;
    const matchesSearch =
      rm.roomNumber.includes(searchQuery) ||
      rm.block.toLowerCase().includes(searchQuery.toLowerCase()) ||
      rm.occupants.some((occ) => occ.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesHostel && matchesStatus && matchesSearch;
  });

  const handleOpenAllocate = (room: HostelRoomItem) => {
    setAllocatingRoom(room);
    setAllocateForm({ studentName: "", rollNumber: "", remarks: "" });
    setAllocateModalOpen(true);
  };

  const handleConfirmAllocation = (e: React.FormEvent) => {
    e.preventDefault();
    if (!allocatingRoom || !allocateForm.studentName.trim()) return;

    setRooms((prev) =>
      prev.map((r) => {
        if (r.id === allocatingRoom.id) {
          const newOccupants = [...r.occupants, `${allocateForm.studentName} (${allocateForm.rollNumber || "24CSE0101"})`];
          const newOccupied = r.occupiedBeds + 1;
          return {
            ...r,
            occupiedBeds: newOccupied,
            occupants: newOccupants,
            status: newOccupied >= r.capacityBeds ? "FULL" : "AVAILABLE",
          };
        }
        return r;
      })
    );

    toast({
      title: "Bed Allocated Successfully",
      description: `${allocateForm.studentName} allocated to Room ${allocatingRoom.roomNumber} (${allocatingRoom.block}).`,
      variant: "success",
    });

    setAllocateModalOpen(false);
    setAllocatingRoom(null);
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 mb-1">
            <Link href="/app/dashboard" className="hover:text-indigo-600 transition">
              CampusOS
            </Link>
            <span>/</span>
            <span className="font-semibold text-slate-700 dark:text-slate-300">Infrastructure</span>
            <span>/</span>
            <span className="text-slate-500">Hostel Residence</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2.5">
            <Building2 className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
            Hostel & Residential Life Management
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Authoritative room and bed occupancy matrix, warden supervisory roster, and student room allocation.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            onClick={() =>
              toast({
                title: "Maintenance Ticket Created",
                description: "Campus facilities dispatch has been notified.",
                variant: "info",
              })
            }
          >
            <Wrench className="h-4 w-4 mr-1.5" />
            Log Maintenance
          </Button>
          <Button
            variant="primary"
            onClick={() => {
              const available = rooms.find((r) => r.status === "AVAILABLE");
              if (available) handleOpenAllocate(available);
              else
                toast({
                  title: "No Available Rooms",
                  description: "All rooms in current inventory are at full capacity.",
                  variant: "warning",
                });
            }}
          >
            <Bed className="h-4 w-4 mr-1.5" />
            Allocate Bed
          </Button>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Bed Capacity"
          value={totalCapacity.toLocaleString()}
          description="Across 3 residential halls"
          variant="indigo"
          icon={<Bed className="h-5 w-5" />}
        />
        <StatCard
          label="Occupied Beds"
          value={totalOccupied.toLocaleString()}
          description={`${occupancyRate}% institutional occupancy`}
          variant="emerald"
          icon={<Users className="h-5 w-5" />}
        />
        <StatCard
          label="Vacant Beds"
          value={totalAvailable.toLocaleString()}
          description="Ready for allocation"
          variant="amber"
          icon={<DoorOpen className="h-5 w-5" />}
        />
        <StatCard
          label="Residential Halls"
          value={hostels.length.toString()}
          description="Boys, Girls & PG Houses"
          variant="purple"
          icon={<Building2 className="h-5 w-5" />}
        />
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-800">
        <button
          onClick={() => setActiveTab("rooms")}
          className={`py-3 px-5 text-sm font-medium border-b-2 transition ${
            activeTab === "rooms"
              ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
              : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400"
          }`}
        >
          Room & Bed Inventory ({rooms.length})
        </button>
        <button
          onClick={() => setActiveTab("hostels")}
          className={`py-3 px-5 text-sm font-medium border-b-2 transition ${
            activeTab === "hostels"
              ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
              : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400"
          }`}
        >
          Halls of Residence ({hostels.length})
        </button>
        <button
          onClick={() => setActiveTab("wardens")}
          className={`py-3 px-5 text-sm font-medium border-b-2 transition ${
            activeTab === "wardens"
              ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
              : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400"
          }`}
        >
          Warden & Supervisory Staff
        </button>
      </div>

      {/* Tab: Rooms & Beds */}
      {activeTab === "rooms" && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-4 rounded-xl border border-slate-200 dark:bg-slate-900 dark:border-slate-800">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search room number, block, or occupant..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 text-sm rounded-lg border border-slate-200 bg-slate-50/50 dark:border-slate-700 dark:bg-slate-800/50 text-slate-900 dark:text-white focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="flex flex-wrap items-center gap-2.5">
              <select
                value={selectedHostel}
                onChange={(e) => setSelectedHostel(e.target.value)}
                className="text-xs rounded-lg border border-slate-200 bg-white py-2 px-3 text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
              >
                <option value="ALL">All Halls</option>
                <option value="Raman">Sir C. V. Raman Hall</option>
                <option value="Kalpana">Kalpana Chawla Hall</option>
                <option value="Kalam">Dr. A. P. J. Abdul Kalam</option>
              </select>

              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="text-xs rounded-lg border border-slate-200 bg-white py-2 px-3 text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
              >
                <option value="ALL">All Statuses</option>
                <option value="AVAILABLE">Available</option>
                <option value="FULL">Fully Occupied</option>
                <option value="MAINTENANCE">Under Maintenance</option>
              </select>
            </div>
          </div>

          {/* Rooms Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredRooms.map((rm) => {
              const isFull = rm.status === "FULL" || rm.occupiedBeds >= rm.capacityBeds;
              return (
                <div
                  key={rm.id}
                  className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs hover:border-indigo-400 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900 dark:hover:border-indigo-600"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-xs font-mono font-bold text-indigo-600 dark:text-indigo-400">
                        {rm.block} &bull; Floor {rm.floor}
                      </span>
                      <h3 className="text-lg font-bold text-slate-900 dark:text-white mt-0.5">
                        Room {rm.roomNumber}
                      </h3>
                      <p className="text-xs text-slate-500 dark:text-slate-400">{rm.hostelName}</p>
                    </div>

                    <Badge
                      variant={
                        rm.status === "AVAILABLE" ? "success" : rm.status === "FULL" ? "secondary" : "warning"
                      }
                      dot
                    >
                      {rm.status}
                    </Badge>
                  </div>

                  {/* Bed Capacity Bar */}
                  <div className="mt-4">
                    <div className="flex items-center justify-between text-xs text-slate-600 dark:text-slate-400 mb-1.5">
                      <span>Occupancy</span>
                      <span className="font-semibold font-mono">
                        {rm.occupiedBeds} / {rm.capacityBeds} Beds
                      </span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          isFull ? "bg-slate-400 dark:bg-slate-600" : "bg-emerald-500"
                        }`}
                        style={{ width: `${(rm.occupiedBeds / rm.capacityBeds) * 100}%` }}
                      />
                    </div>
                  </div>

                  {/* Occupants List */}
                  <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800">
                    <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block mb-1">
                      Current Occupants:
                    </span>
                    {rm.occupants.length === 0 ? (
                      <p className="text-xs text-slate-400 italic">No occupants currently allocated.</p>
                    ) : (
                      <div className="space-y-1">
                        {rm.occupants.map((occ, i) => (
                          <div
                            key={i}
                            className="text-xs text-slate-700 dark:text-slate-300 flex items-center gap-1.5"
                          >
                            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                            <span className="font-medium truncate">{occ}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Allocation Action */}
                  <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex justify-end">
                    <Button
                      variant={isFull ? "outline" : "primary"}
                      size="sm"
                      disabled={isFull}
                      onClick={() => handleOpenAllocate(rm)}
                    >
                      {isFull ? "Room Full" : "Allocate Bed"}
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Tab: Halls of Residence */}
      {activeTab === "hostels" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {hostels.map((hst) => (
            <div
              key={hst.id}
              className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:border-slate-800 dark:bg-slate-900"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-400">
                  {hst.code}
                </span>
                <Badge variant={hst.status === "ACTIVE" ? "success" : "warning"} dot>
                  {hst.status}
                </Badge>
              </div>

              <h2 className="mt-3 text-base font-bold text-slate-900 dark:text-white">{hst.name}</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Type: <strong className="text-slate-700 dark:text-slate-300">{hst.type}</strong>
              </p>

              <div className="mt-4 grid grid-cols-2 gap-3 text-xs border-t border-slate-100 dark:border-slate-800 pt-3">
                <div>
                  <span className="text-slate-500 block">Blocks / Wings</span>
                  <span className="font-bold text-slate-900 dark:text-white font-mono text-sm">
                    {hst.totalBlocks} Blocks
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block">Total Rooms</span>
                  <span className="font-bold text-slate-900 dark:text-white font-mono text-sm">
                    {hst.totalRooms} Rooms
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block">Bed Capacity</span>
                  <span className="font-bold text-slate-900 dark:text-white font-mono text-sm">
                    {hst.capacityBeds} Beds
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block">Occupied Beds</span>
                  <span className="font-bold text-emerald-600 dark:text-emerald-400 font-mono text-sm">
                    {hst.occupiedBeds} Beds
                  </span>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs">
                <span className="text-slate-500">Chief Warden:</span>
                <span className="font-medium text-slate-900 dark:text-white">{hst.wardenName}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab: Wardens */}
      {activeTab === "wardens" && (
        <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <table className="w-full text-left text-sm text-slate-700 dark:text-slate-300">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500 border-b border-slate-200 dark:bg-slate-800/50 dark:border-slate-800">
              <tr>
                <th className="px-4 py-3">Residence Hall</th>
                <th className="px-4 py-3">Warden Name</th>
                <th className="px-4 py-3">Emergency Phone</th>
                <th className="px-4 py-3">Residence Type</th>
                <th className="px-4 py-3 text-right">Duty Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {hostels.map((hst) => (
                <tr key={hst.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition">
                  <td className="px-4 py-3 font-semibold text-slate-900 dark:text-white">{hst.name}</td>
                  <td className="px-4 py-3">{hst.wardenName}</td>
                  <td className="px-4 py-3 font-mono text-xs text-indigo-600 dark:text-indigo-400 flex items-center gap-1.5">
                    <Phone className="h-3.5 w-3.5" />
                    {hst.wardenPhone}
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200">
                      {hst.type}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        toast({
                          title: `Connecting to ${hst.wardenName}`,
                          description: `Calling emergency line: ${hst.wardenPhone}`,
                          variant: "info",
                        })
                      }
                    >
                      Call Warden
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Allocation Modal Dialog */}
      <Dialog
        open={allocateModalOpen}
        onClose={() => setAllocateModalOpen(false)}
        title={`Allocate Bed in Room ${allocatingRoom?.roomNumber || ""}`}
        description={`Allocate student bed occupancy in ${allocatingRoom?.hostelName || ""}, ${allocatingRoom?.block || ""}.`}
      >
        <form onSubmit={handleConfirmAllocation} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Student Full Name <span className="text-red-400">*</span>
            </label>
            <Input
              placeholder="e.g. Aarav Patel"
              value={allocateForm.studentName}
              onChange={(e) => setAllocateForm({ ...allocateForm, studentName: e.target.value })}
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Roll Number / Admission ID <span className="text-red-400">*</span>
            </label>
            <Input
              placeholder="e.g. 24CSE0101"
              value={allocateForm.rollNumber}
              onChange={(e) => setAllocateForm({ ...allocateForm, rollNumber: e.target.value })}
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Special Allocation Notes (Optional)
            </label>
            <Input
              placeholder="e.g. Approved medical accommodation, ground floor request"
              value={allocateForm.remarks}
              onChange={(e) => setAllocateForm({ ...allocateForm, remarks: e.target.value })}
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
            <Button variant="outline" type="button" onClick={() => setAllocateModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              Confirm Allocation
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
