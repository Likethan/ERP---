"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { transportStopsService } from "@/services/transport-stops.service";
import { transportRoutesService } from "@/services/transport-routes.service";
import { TransportStop, TransportRoute, StopStatus } from "@campusos/types";
import { DataGrid, ColumnDef } from "@/components/data-grid/data-grid";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  MapPin,
  Plus,
  Search,
  Eye,
  Clock,
  Compass,
  Users,
} from "lucide-react";

export default function TransportStopsListPage() {
  const [stops, setStops] = useState<TransportStop[]>([]);
  const [routes, setRoutes] = useState<TransportRoute[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [routeFilter, setRouteFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Create Stop Modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createForm, setCreateForm] = useState({
    name: "",
    code: "",
    routeId: "route-01",
    landmark: "",
    sequence: 1,
    pickupTime: "07:30 AM",
    dropTime: "05:40 PM",
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [stopsRes, routesRes] = await Promise.all([
        transportStopsService.listStops({
          routeId: routeFilter,
          status: statusFilter,
          search: searchQuery,
        }),
        transportRoutesService.listRoutes(),
      ]);

      if (stopsRes.success && stopsRes.data) setStops(stopsRes.data);
      if (routesRes.success && routesRes.data) setRoutes(routesRes.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [routeFilter, statusFilter, searchQuery]);

  const handleCreateStop = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.name || !createForm.code) return;

    const selectedRoute = routes.find((r) => r.id === createForm.routeId);

    await transportStopsService.createStop({
      ...createForm,
      routeCode: selectedRoute?.routeCode || "R-01",
      routeName: selectedRoute?.name || "Bus Route",
      studentCount: 0,
      status: StopStatus.ACTIVE,
    });

    setCreateModalOpen(false);
    setCreateForm({
      name: "",
      code: "",
      routeId: "route-01",
      landmark: "",
      sequence: 1,
      pickupTime: "07:30 AM",
      dropTime: "05:40 PM",
    });
    loadData();
  };

  const columns: ColumnDef<TransportStop>[] = useMemo(
    () => [
      {
        id: "code",
        header: "Stop Code",
        accessorKey: "code",
        cell: (s) => (
          <span className="font-mono text-xs font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
            {s.code}
          </span>
        ),
      },
      {
        id: "name",
        header: "Stop Name & Landmark",
        cell: (s) => (
          <div>
            <Link
              href={`/app/infrastructure/transport/stops/${s.id}`}
              className="font-medium text-white hover:text-indigo-300 text-sm block"
            >
              {s.name}
            </Link>
            <span className="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
              <MapPin className="w-3 h-3 text-slate-500" />
              {s.landmark || "General Landmark"}
            </span>
          </div>
        ),
      },
      {
        id: "route",
        header: "Transit Line",
        cell: (s) => (
          <div className="text-xs">
            <span className="font-mono font-bold text-blue-400">{s.routeCode || "R-01"}</span>
            <span className="text-slate-400 block">{s.routeName || "Corridor Route"}</span>
          </div>
        ),
      },
      {
        id: "sequence",
        header: "Stop Order",
        cell: (s) => (
          <div className="w-6 h-6 rounded-full bg-slate-900 border border-slate-700 flex items-center justify-center text-xs font-bold text-white">
            {s.sequence}
          </div>
        ),
      },
      {
        id: "timings",
        header: "Boarding Times",
        cell: (s) => (
          <div className="text-xs space-y-0.5 text-slate-300">
            <div>Pickup: <span className="font-mono text-white">{s.pickupTime}</span></div>
            <div>Drop: <span className="font-mono text-slate-400">{s.dropTime}</span></div>
          </div>
        ),
      },
      {
        id: "studentCount",
        header: "Boarders",
        cell: (s) => (
          <div className="flex items-center gap-1.5 text-xs">
            <Users className="w-3.5 h-3.5 text-violet-400" />
            <span className="font-semibold text-white">{s.studentCount || 0}</span>
            <span className="text-slate-500">students</span>
          </div>
        ),
      },
      {
        id: "status",
        header: "Status",
        accessorKey: "status",
        cell: (s) => (
          <Badge
            variant="outline"
            className={
              s.status === StopStatus.ACTIVE
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                : "bg-slate-800 text-slate-400 border-slate-700"
            }
          >
            {s.status}
          </Badge>
        ),
      },
      {
        id: "actions",
        header: "Actions",
        cell: (s) => (
          <Link href={`/app/infrastructure/transport/stops/${s.id}`}>
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
            <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">
              Stops
            </span>
          </div>
          <h1 className="text-2xl lg:text-3xl font-bold text-white tracking-tight">
            Designated Boarding Stops
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Configure pickup points, sequence markers, morning and evening arrival times.
          </p>
        </div>

        <Button
          onClick={() => setCreateModalOpen(true)}
          className="bg-indigo-600 hover:bg-indigo-500 text-white gap-2 self-start md:self-auto"
        >
          <Plus className="w-4 h-4" />
          Add Stop
        </Button>
      </div>

      {/* Filter Bar */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col md:flex-row items-center gap-4">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <Input
            placeholder="Search stops by name, code, landmark or route..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 bg-slate-950/60 border-slate-800 text-sm text-white placeholder:text-slate-500 w-full"
          />
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <select
            value={routeFilter}
            onChange={(e) => setRouteFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
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
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="INACTIVE">Inactive</option>
          </select>
        </div>
      </div>

      {/* DataGrid */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden backdrop-blur-sm">
        <DataGrid
          data={stops}
          columns={columns}
          loading={loading}
          emptyMessage="No stops found matching your criteria."
        />
      </div>

      {/* Create Stop Modal */}
      {createModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-6 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <MapPin className="w-5 h-5 text-indigo-400" />
                Add Boarding Stop
              </h3>
              <button
                onClick={() => setCreateModalOpen(false)}
                className="text-slate-400 hover:text-white text-lg"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateStop} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Stop Code *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. HBL-02"
                    value={createForm.code}
                    onChange={(e) => setCreateForm({ ...createForm, code: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Sequence Number *
                  </label>
                  <input
                    type="number"
                    required
                    min={1}
                    value={createForm.sequence}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, sequence: parseInt(e.target.value) || 1 })
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">
                  Stop Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Nagawara Junction Ring Road"
                  value={createForm.name}
                  onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">
                  Route Corridor *
                </label>
                <select
                  value={createForm.routeId}
                  onChange={(e) => setCreateForm({ ...createForm, routeId: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                >
                  {routes.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.routeCode} - {r.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">
                  Landmark Description
                </label>
                <input
                  type="text"
                  placeholder="e.g. Near Petrol Bunk, opposite bus shelter"
                  value={createForm.landmark}
                  onChange={(e) => setCreateForm({ ...createForm, landmark: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Morning Pickup Time
                  </label>
                  <input
                    type="text"
                    placeholder="07:30 AM"
                    value={createForm.pickupTime}
                    onChange={(e) => setCreateForm({ ...createForm, pickupTime: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Evening Drop Time
                  </label>
                  <input
                    type="text"
                    placeholder="05:40 PM"
                    value={createForm.dropTime}
                    onChange={(e) => setCreateForm({ ...createForm, dropTime: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  />
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
                <Button type="submit" className="bg-indigo-600 hover:bg-indigo-500 text-white">
                  Add Stop
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
