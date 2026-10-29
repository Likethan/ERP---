"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { transportRoutesService } from "@/services/transport-routes.service";
import { transportVehiclesService } from "@/services/transport-vehicles.service";
import { transportDriversService } from "@/services/transport-drivers.service";
import { TransportRoute, RouteStatus } from "@campusos/types";
import { DataGrid, ColumnDef } from "@/components/data-grid/data-grid";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Compass,
  Plus,
  Search,
  ArrowRight,
  Eye,
  Bus,
  Clock,
  Filter,
  Users,
  CheckCircle2,
} from "lucide-react";

export default function TransportRoutesListPage() {
  const [routes, setRoutes] = useState<TransportRoute[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Create Route Modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createForm, setCreateForm] = useState({
    routeCode: "",
    name: "",
    startPoint: "",
    endPoint: "",
    capacity: 52,
    morningStartTime: "07:15 AM",
    eveningReturnTime: "05:15 PM",
    description: "",
  });

  const loadRoutes = async () => {
    setLoading(true);
    try {
      const res = await transportRoutesService.listRoutes({
        status: statusFilter,
        search: searchQuery,
      });
      if (res.success && res.data) {
        setRoutes(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRoutes();
  }, [statusFilter, searchQuery]);

  const handleCreateRoute = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.routeCode || !createForm.name || !createForm.startPoint)
      return;

    await transportRoutesService.createRoute({
      ...createForm,
      status: RouteStatus.ACTIVE,
      allocatedStudents: 0,
      stopsCount: 0,
    });

    setCreateModalOpen(false);
    setCreateForm({
      routeCode: "",
      name: "",
      startPoint: "",
      endPoint: "",
      capacity: 52,
      morningStartTime: "07:15 AM",
      eveningReturnTime: "05:15 PM",
      description: "",
    });
    loadRoutes();
  };

  // KPIs
  const totalCapacity = routes.reduce((acc, r) => acc + (r.capacity || 0), 0);
  const totalAllocated = routes.reduce(
    (acc, r) => acc + (r.allocatedStudents || 0),
    0,
  );
  const avgUtil =
    totalCapacity > 0 ? Math.round((totalAllocated / totalCapacity) * 100) : 0;
  const activeRoutes = routes.filter(
    (r) => r.status === RouteStatus.ACTIVE,
  ).length;

  const columns: ColumnDef<TransportRoute>[] = useMemo(
    () => [
      {
        id: "routeCode",
        header: "Route Code",
        accessorKey: "routeCode",
        cell: (r) => (
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold text-blue-400 bg-blue-500/10 px-2.5 py-1 rounded border border-blue-500/20">
              {r.routeCode}
            </span>
          </div>
        ),
      },
      {
        id: "name",
        header: "Route Name & Corridor",
        cell: (r) => (
          <div>
            <Link
              href={`/app/infrastructure/transport/routes/${r.id}`}
              className="font-medium text-white hover:text-blue-300 text-sm block"
            >
              {r.name}
            </Link>
            <span className="text-xs text-slate-400">
              {r.startPoint} → {r.endPoint}
            </span>
          </div>
        ),
      },
      {
        id: "schedule",
        header: "Schedule",
        cell: (r) => (
          <div className="text-xs space-y-0.5 text-slate-300">
            <div className="flex items-center gap-1.5">
              <Clock className="w-3 h-3 text-slate-500" />
              <span>AM: {r.morningStartTime || "07:30 AM"}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Clock className="w-3 h-3 text-slate-500" />
              <span>PM: {r.eveningReturnTime || "05:00 PM"}</span>
            </div>
          </div>
        ),
      },
      {
        id: "vehicleDriver",
        header: "Vehicle & Driver",
        cell: (r) => (
          <div className="text-xs">
            <div className="font-medium text-white flex items-center gap-1">
              <Bus className="w-3 h-3 text-emerald-400" />
              {r.vehicleNumber || "Unassigned"}
            </div>
            <div className="text-slate-400 mt-0.5">
              {r.driverName || "No driver assigned"}
            </div>
          </div>
        ),
      },
      {
        id: "utilization",
        header: "Seats & Utilization",
        cell: (r) => {
          const util =
            r.capacity > 0
              ? Math.round((r.allocatedStudents / r.capacity) * 100)
              : 0;
          return (
            <div className="w-36 space-y-1">
              <div className="flex justify-between text-xs">
                <span className="font-mono text-slate-300">
                  {r.allocatedStudents} / {r.capacity}
                </span>
                <span
                  className={`font-semibold ${
                    util >= 90
                      ? "text-red-400"
                      : util >= 75
                        ? "text-amber-400"
                        : "text-emerald-400"
                  }`}
                >
                  {util}%
                </span>
              </div>
              <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    util >= 90
                      ? "bg-red-500"
                      : util >= 75
                        ? "bg-amber-500"
                        : "bg-blue-500"
                  }`}
                  style={{ width: `${Math.min(util, 100)}%` }}
                />
              </div>
            </div>
          );
        },
      },
      {
        id: "status",
        header: "Status",
        accessorKey: "status",
        cell: (r) => (
          <Badge
            variant="outline"
            className={
              r.status === RouteStatus.ACTIVE
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                : "bg-slate-800 text-slate-400 border-slate-700"
            }
          >
            {r.status}
          </Badge>
        ),
      },
      {
        id: "actions",
        header: "Actions",
        cell: (r) => (
          <Link href={`/app/infrastructure/transport/routes/${r.id}`}>
            <Button
              size="sm"
              variant="ghost"
              className="h-8 w-8 p-0 text-slate-400 hover:text-white"
            >
              <Eye className="w-4 h-4" />
            </Button>
          </Link>
        ),
      },
    ],
    [],
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
            <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider">
              Routes
            </span>
          </div>
          <h1 className="text-2xl lg:text-3xl font-bold text-white tracking-tight">
            Bus Transit Corridors
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Manage arterial college bus lines, morning pickups, evening runs,
            and passenger loads.
          </p>
        </div>

        <Button
          onClick={() => setCreateModalOpen(true)}
          className="bg-blue-600 hover:bg-blue-500 text-white gap-2 self-start md:self-auto"
        >
          <Plus className="w-4 h-4" />
          Create Route
        </Button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="text-slate-400 text-xs font-medium">
            Total Corridors
          </div>
          <div className="text-2xl font-bold text-white mt-1">
            {routes.length}
          </div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="text-slate-400 text-xs font-medium">
            Active Services
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">
            {activeRoutes}
          </div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="text-slate-400 text-xs font-medium">
            Fleet Capacity
          </div>
          <div className="text-2xl font-bold text-blue-400 mt-1">
            {totalCapacity} seats
          </div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="text-slate-400 text-xs font-medium">
            Seat Utilization
          </div>
          <div className="text-2xl font-bold text-amber-400 mt-1">
            {avgUtil}%
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col md:flex-row items-center gap-4">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <Input
            placeholder="Search routes by name, code, vehicle, driver, or pickup points..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 bg-slate-950/60 border-slate-800 text-sm text-white placeholder:text-slate-500 w-full"
          />
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-blue-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="INACTIVE">Inactive</option>
            <option value="SUSPENDED">Suspended</option>
          </select>
        </div>
      </div>

      {/* DataGrid */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden backdrop-blur-sm">
        <DataGrid
          data={routes}
          columns={columns}
          loading={loading}
          emptyMessage="No transit routes found matching your criteria."
        />
      </div>

      {/* Create Route Modal */}
      {createModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-6 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Compass className="w-5 h-5 text-blue-400" />
                Create New Transit Route
              </h3>
              <button
                onClick={() => setCreateModalOpen(false)}
                className="text-slate-400 hover:text-white text-lg"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateRoute} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Route Code *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. RT-05"
                    value={createForm.routeCode}
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        routeCode: e.target.value,
                      })
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Max Seating Capacity *
                  </label>
                  <input
                    type="number"
                    required
                    min={10}
                    max={100}
                    value={createForm.capacity}
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        capacity: parseInt(e.target.value) || 52,
                      })
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">
                  Route Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Whitefield Express Transit"
                  value={createForm.name}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, name: e.target.value })
                  }
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Origin / Start Point *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Hope Farm Junction"
                    value={createForm.startPoint}
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        startPoint: e.target.value,
                      })
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Destination / End Point *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Main Engineering Campus"
                    value={createForm.endPoint}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, endPoint: e.target.value })
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Morning Pickup Time
                  </label>
                  <input
                    type="text"
                    placeholder="07:15 AM"
                    value={createForm.morningStartTime}
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        morningStartTime: e.target.value,
                      })
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Evening Departure Time
                  </label>
                  <input
                    type="text"
                    placeholder="05:15 PM"
                    value={createForm.eveningReturnTime}
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        eveningReturnTime: e.target.value,
                      })
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">
                  Description / Landmarks
                </label>
                <textarea
                  rows={2}
                  placeholder="Notes regarding stops, highway routing, tollway clearance..."
                  value={createForm.description}
                  onChange={(e) =>
                    setCreateForm({
                      ...createForm,
                      description: e.target.value,
                    })
                  }
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                />
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
                <Button
                  type="submit"
                  className="bg-blue-600 hover:bg-blue-500 text-white"
                >
                  Create Route
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
