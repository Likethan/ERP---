"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { transportAllocationsService } from "@/services/transport-allocations.service";
import { transportRoutesService } from "@/services/transport-routes.service";
import { transportStopsService } from "@/services/transport-stops.service";
import { TransportAllocation, TransportRoute, TransportStop, TransportAllocationStatus } from "@campusos/types";
import { DataGrid, ColumnDef } from "@/components/data-grid/data-grid";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  ShieldCheck,
  Plus,
  Search,
  Eye,
  MapPin,
  Compass,
  User,
  CreditCard,
  CheckCircle2,
} from "lucide-react";

export default function TransportAllocationsListPage() {
  const [allocations, setAllocations] = useState<TransportAllocation[]>([]);
  const [routes, setRoutes] = useState<TransportRoute[]>([]);
  const [stops, setStops] = useState<TransportStop[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [routeFilter, setRouteFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Create Allocation Modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createForm, setCreateForm] = useState({
    studentId: "stu-24cse0105",
    studentName: "Devansh Nair",
    registerNumber: "REG2024CS005",
    routeId: "route-01",
    stopId: "stp-01",
    seatNumber: "24",
    feeStatus: "PAID" as "PAID" | "PENDING",
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [allocRes, routesRes, stopsRes] = await Promise.all([
        transportAllocationsService.listTransportAllocations({
          routeId: routeFilter,
          status: statusFilter,
          search: searchQuery,
        }),
        transportRoutesService.listRoutes(),
        transportStopsService.listStops(),
      ]);

      if (allocRes.success && allocRes.data) setAllocations(allocRes.data);
      if (routesRes.success && routesRes.data) setRoutes(routesRes.data);
      if (stopsRes.success && stopsRes.data) setStops(stopsRes.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [routeFilter, statusFilter, searchQuery]);

  const handleCreateAllocation = async (e: React.FormEvent) => {
    e.preventDefault();
    const selRoute = routes.find((r) => r.id === createForm.routeId);
    const selStop = stops.find((s) => s.id === createForm.stopId);

    await transportAllocationsService.createTransportAllocation({
      studentId: createForm.studentId,
      studentName: createForm.studentName,
      registerNumber: createForm.registerNumber,
      routeId: createForm.routeId,
      routeName: selRoute?.name || "Bus Route",
      routeCode: selRoute?.routeCode || "R-01",
      stopId: createForm.stopId,
      stopName: selStop?.name || "Boarding Stop",
      seatNumber: createForm.seatNumber,
      vehicleNumber: selRoute?.vehicleNumber || "KA-04-E-1892",
      feeStatus: createForm.feeStatus,
      status: TransportAllocationStatus.ACTIVE,
    });

    setCreateModalOpen(false);
    loadData();
  };

  const activePasses = allocations.filter((a) => a.status === TransportAllocationStatus.ACTIVE).length;
  const paidPasses = allocations.filter((a) => a.feeStatus === "PAID").length;

  const columns: ColumnDef<TransportAllocation>[] = useMemo(
    () => [
      {
        id: "student",
        header: "Student & Register No",
        cell: (a) => (
          <div>
            <Link
              href={`/app/students/${a.studentId}`}
              className="font-medium text-white hover:text-violet-300 text-sm flex items-center gap-1.5"
            >
              <User className="w-3.5 h-3.5 text-violet-400" />
              {a.studentName}
            </Link>
            <span className="font-mono text-xs text-slate-500 block mt-0.5">
              {a.registerNumber}
            </span>
          </div>
        ),
      },
      {
        id: "route",
        header: "Transit Corridor",
        cell: (a) => (
          <div className="text-xs">
            <span className="font-mono font-bold text-blue-400">{a.routeCode || "R-01"}</span>
            <span className="text-slate-300 block">{a.routeName}</span>
            <span className="text-slate-500">Bus: {a.vehicleNumber}</span>
          </div>
        ),
      },
      {
        id: "stop",
        header: "Boarding Stop",
        cell: (a) => (
          <div className="text-xs flex items-center gap-1.5 text-slate-300">
            <MapPin className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
            <span>{a.stopName}</span>
          </div>
        ),
      },
      {
        id: "seat",
        header: "Seat Number",
        cell: (a) => (
          <span className="font-mono text-xs font-semibold text-white bg-slate-950 px-2 py-1 rounded border border-slate-800">
            #{a.seatNumber || "General"}
          </span>
        ),
      },
      {
        id: "feeStatus",
        header: "Fee Status",
        cell: (a) => (
          <Badge
            variant="outline"
            className={
              a.feeStatus === "PAID"
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                : "bg-amber-500/10 text-amber-400 border-amber-500/20"
            }
          >
            {a.feeStatus}
          </Badge>
        ),
      },
      {
        id: "status",
        header: "Pass Status",
        accessorKey: "status",
        cell: (a) => (
          <Badge
            variant="outline"
            className={
              a.status === TransportAllocationStatus.ACTIVE
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                : "bg-slate-800 text-slate-400 border-slate-700"
            }
          >
            {a.status}
          </Badge>
        ),
      },
      {
        id: "actions",
        header: "Actions",
        cell: (a) => (
          <Link href={`/app/infrastructure/transport/allocations/${a.id}`}>
            <Button size="sm" variant="ghost" className="h-8 w-8 p-0 text-slate-400 hover:text-white">
              <Eye className="w-4 h-4" />
            </Button>
          </Link>
        ),
      },
    ],
    []
  );

  return (
    <div className="p-6 lg:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link
              href="/app/infrastructure/transport"
              className="text-xs font-semibold text-slate-400 hover:text-white uppercase tracking-wider"
            >
              Transport
            </Link>
            <span className="text-slate-600">/</span>
            <span className="text-xs font-semibold text-violet-400 uppercase tracking-wider">
              Student Passes
            </span>
          </div>
          <h1 className="text-2xl lg:text-3xl font-bold text-white tracking-tight">
            Student Transport Allocations
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Manage student bus transit passes, designated pickup stops, seat assignments, and fee clearances.
          </p>
        </div>

        <Button
          onClick={() => setCreateModalOpen(true)}
          className="bg-violet-600 hover:bg-violet-500 text-white gap-2 self-start md:self-auto"
        >
          <Plus className="w-4 h-4" />
          Allocate Bus Pass
        </Button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="text-slate-400 text-xs font-medium">Total Issued Passes</div>
          <div className="text-2xl font-bold text-white mt-1">{allocations.length}</div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="text-slate-400 text-xs font-medium">Active Passes</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{activePasses}</div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="text-slate-400 text-xs font-medium">Fee Cleared</div>
          <div className="text-2xl font-bold text-blue-400 mt-1">{paidPasses}</div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="text-slate-400 text-xs font-medium">Fee Pending</div>
          <div className="text-2xl font-bold text-amber-400 mt-1">{allocations.length - paidPasses}</div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col md:flex-row items-center gap-4">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <Input
            placeholder="Search by student name, register number, stop, or route..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 bg-slate-950/60 border-slate-800 text-sm text-white placeholder:text-slate-500 w-full"
          />
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <select
            value={routeFilter}
            onChange={(e) => setRouteFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-violet-500"
          >
            <option value="ALL">All Routes</option>
            {routes.map((r) => (
              <option key={r.id} value={r.id}>
                {r.routeCode} - {r.name}
              </option>
            ))}
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-violet-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="CANCELLED">Cancelled</option>
            <option value="EXPIRED">Expired</option>
          </select>
        </div>
      </div>

      {/* DataGrid */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden backdrop-blur-sm">
        <DataGrid
          data={allocations}
          columns={columns}
          loading={loading}
          emptyMessage="No student transport allocations found matching your criteria."
        />
      </div>

      {/* Allocate Pass Modal */}
      {createModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-6 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-violet-400" />
                Issue Student Transport Pass
              </h3>
              <button
                onClick={() => setCreateModalOpen(false)}
                className="text-slate-400 hover:text-white text-lg"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateAllocation} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Student Name *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Devansh Nair"
                    value={createForm.studentName}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, studentName: e.target.value })
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-violet-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Register Number *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. REG2024CS005"
                    value={createForm.registerNumber}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, registerNumber: e.target.value })
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-violet-500 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">
                  Transit Route *
                </label>
                <select
                  value={createForm.routeId}
                  onChange={(e) => setCreateForm({ ...createForm, routeId: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-violet-500"
                >
                  {routes.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.routeCode} - {r.name} ({r.allocatedStudents}/{r.capacity} seats)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">
                  Boarding Stop *
                </label>
                <select
                  value={createForm.stopId}
                  onChange={(e) => setCreateForm({ ...createForm, stopId: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-violet-500"
                >
                  {stops
                    .filter((s) => s.routeId === createForm.routeId)
                    .map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.code} - {s.name} ({s.pickupTime})
                      </option>
                    ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Seat Number
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. 24"
                    value={createForm.seatNumber}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, seatNumber: e.target.value })
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-violet-500 font-mono"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Transport Fee Status
                  </label>
                  <select
                    value={createForm.feeStatus}
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        feeStatus: e.target.value as "PAID" | "PENDING",
                      })
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-violet-500"
                  >
                    <option value="PAID">Paid</option>
                    <option value="PENDING">Pending</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setCreateModalOpen(false)}
                  className="border-slate-800 text-slate-400"
                >
                  Cancel
                </Button>
                <Button type="submit" className="bg-violet-600 hover:bg-violet-500 text-white">
                  Issue Pass
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
