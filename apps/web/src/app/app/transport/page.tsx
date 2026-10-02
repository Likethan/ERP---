"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { infrastructureService } from "@/services/infrastructure.service";
import {
  TransportRouteItem,
  TransportVehicleItem,
} from "@/mocks/infrastructure.mock";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { TableSkeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import {
  Bus,
  MapPin,
  Clock,
  Phone,
  Shield,
  Search,
  Ticket,
  Users,
  Navigation,
} from "lucide-react";

export default function TransportManagementPage() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [routes, setRoutes] = useState<TransportRouteItem[]>([]);
  const [vehicles, setVehicles] = useState<TransportVehicleItem[]>([]);

  // Filter states
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [activeTab, setActiveTab] = useState<"routes" | "fleet" | "passes">("routes");

  // Bus Pass Booking Modal
  const [passModalOpen, setPassModalOpen] = useState(false);
  const [selectedRoute, setSelectedRoute] = useState<TransportRouteItem | null>(null);
  const [passForm, setPassForm] = useState({
    studentName: "Aarav Patel",
    rollNumber: "24CSE0101",
    stopName: "Koramangala 4th Block",
  });

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [rtRes, vhRes] = await Promise.all([
        infrastructureService.getTransportRoutes(),
        infrastructureService.getVehicles(),
      ]);
      setRoutes(rtRes.data || []);
      setVehicles(vhRes.data || []);
    } catch {
      toast({
        title: "Error loading transport network",
        description: "Falling back to local cache.",
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const totalCommuters = routes.reduce((acc, r) => acc + r.allocatedStudents, 0);
  const totalFleetCapacity = routes.reduce((acc, r) => acc + r.capacity, 0);

  const filteredRoutes = routes.filter((r) => {
    const matchesStatus = statusFilter === "ALL" || r.status === statusFilter;
    const matchesSearch =
      r.routeName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.routeCode.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.driverName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.vehicleNumber.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const handleOpenBookPass = (route: TransportRouteItem) => {
    setSelectedRoute(route);
    setPassModalOpen(true);
  };

  const handleConfirmPass = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRoute) return;

    setRoutes((prev) =>
      prev.map((r) =>
        r.id === selectedRoute.id ? { ...r, allocatedStudents: r.allocatedStudents + 1 } : r
      )
    );

    toast({
      title: "Transport Pass Issued",
      description: `Bus Pass generated for ${passForm.studentName} on ${selectedRoute.routeName} (${passForm.stopName}).`,
      variant: "success",
    });

    setPassModalOpen(false);
    setSelectedRoute(null);
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
            <span className="text-slate-500">Transport Network</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2.5">
            <Bus className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
            Campus Transport & Transit Fleet Network
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Route coverage timetables, fleet vehicles, driver duty rosters, and digital student bus passes.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            onClick={() => {
              const openRoute = routes[0];
              if (openRoute) handleOpenBookPass(openRoute);
            }}
          >
            <Ticket className="h-4 w-4 mr-1.5" />
            Issue Bus Pass
          </Button>
          <Button
            variant="primary"
            onClick={() =>
              toast({
                title: "Dispatch Schedule Re-synced",
                description: "Real-time fleet GPS tracking is online across 6 routes.",
                variant: "success",
              })
            }
          >
            <Navigation className="h-4 w-4 mr-1.5" />
            Live Fleet Dispatch
          </Button>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Active Bus Routes"
          value={routes.length.toString()}
          description="Connecting metropolitan nodes"
          variant="indigo"
          icon={<Bus className="h-5 w-5" />}
        />
        <StatCard
          label="Fleet Capacity"
          value={totalFleetCapacity.toString()}
          description={`${totalCommuters} registered commuters`}
          variant="emerald"
          icon={<Users className="h-5 w-5" />}
        />
        <StatCard
          label="On-Time Dispatch"
          value="98.6%"
          description="Average transit punctuality"
          variant="amber"
          icon={<Clock className="h-5 w-5" />}
        />
        <StatCard
          label="Fleet Vehicles"
          value={vehicles.length.toString()}
          description="Inspected and GPS enabled"
          variant="purple"
          icon={<Shield className="h-5 w-5" />}
        />
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-800">
        <button
          onClick={() => setActiveTab("routes")}
          className={`py-3 px-5 text-sm font-medium border-b-2 transition ${
            activeTab === "routes"
              ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
              : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400"
          }`}
        >
          Transit Routes ({routes.length})
        </button>
        <button
          onClick={() => setActiveTab("fleet")}
          className={`py-3 px-5 text-sm font-medium border-b-2 transition ${
            activeTab === "fleet"
              ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
              : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400"
          }`}
        >
          Fleet Vehicles ({vehicles.length})
        </button>
      </div>

      {/* Tab: Routes */}
      {activeTab === "routes" && (
        <div className="space-y-4">
          {/* Search bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-4 rounded-xl border border-slate-200 dark:bg-slate-900 dark:border-slate-800">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search route code, destination, or driver..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 text-sm rounded-lg border border-slate-200 bg-slate-50/50 dark:border-slate-700 dark:bg-slate-800/50 text-slate-900 dark:text-white focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-xs rounded-lg border border-slate-200 bg-white py-2 px-3 text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
            >
              <option value="ALL">All Statuses</option>
              <option value="ACTIVE">Active</option>
              <option value="IDLE">Idle</option>
              <option value="MAINTENANCE">Maintenance</option>
            </select>
          </div>

          {/* Routes Grid */}
          {loading ? (
            <div className="p-4 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800">
              <TableSkeleton rows={4} cols={4} />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {filteredRoutes.map((rt) => {
              const isFull = rt.allocatedStudents >= rt.capacity;
              return (
                <div
                  key={rt.id}
                  className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs hover:border-indigo-400 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900 dark:hover:border-indigo-600"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-xs font-mono font-bold text-indigo-600 dark:text-indigo-400 px-2 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950/60">
                        {rt.routeCode}
                      </span>
                      <h3 className="text-base font-bold text-slate-900 dark:text-white mt-1.5">
                        {rt.routeName}
                      </h3>
                      <p className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1 mt-0.5">
                        <MapPin className="h-3 w-3" />
                        {rt.stopsCount} Stops on Circuit
                      </p>
                    </div>

                    <Badge variant={rt.status === "ACTIVE" ? "success" : "warning"} dot>
                      {rt.status}
                    </Badge>
                  </div>

                  {/* Schedule Timings */}
                  <div className="mt-4 grid grid-cols-2 gap-2 text-xs bg-slate-50 dark:bg-slate-800/50 p-2.5 rounded-lg border border-slate-100 dark:border-slate-800">
                    <div>
                      <span className="text-slate-400 block font-medium">Morning Pickup</span>
                      <span className="font-bold text-slate-900 dark:text-white font-mono flex items-center gap-1 mt-0.5">
                        <Clock className="h-3.5 w-3.5 text-indigo-500" />
                        {rt.morningDeparture}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 block font-medium">Evening Return</span>
                      <span className="font-bold text-slate-900 dark:text-white font-mono flex items-center gap-1 mt-0.5">
                        <Clock className="h-3.5 w-3.5 text-emerald-500" />
                        {rt.eveningReturn}
                      </span>
                    </div>
                  </div>

                  {/* Capacity Progress */}
                  <div className="mt-4">
                    <div className="flex items-center justify-between text-xs text-slate-600 dark:text-slate-400 mb-1">
                      <span>Seat Allocation</span>
                      <span className="font-mono font-semibold">
                        {rt.allocatedStudents} / {rt.capacity} Seats
                      </span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          isFull ? "bg-amber-500" : "bg-emerald-500"
                        }`}
                        style={{ width: `${Math.min(100, (rt.allocatedStudents / rt.capacity) * 100)}%` }}
                      />
                    </div>
                  </div>

                  {/* Driver Contact */}
                  <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs">
                    <div>
                      <span className="text-slate-400 block">Duty Driver</span>
                      <span className="font-medium text-slate-900 dark:text-white">{rt.driverName}</span>
                    </div>
                    <div className="text-right">
                      <span className="text-slate-400 block font-mono text-[10px]">{rt.vehicleNumber}</span>
                      <span className="font-mono text-indigo-600 dark:text-indigo-400 flex items-center gap-1">
                        <Phone className="h-3 w-3" />
                        {rt.driverPhone}
                      </span>
                    </div>
                  </div>

                  {/* Booking Action */}
                  <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex justify-end">
                    <Button
                      variant={isFull ? "outline" : "primary"}
                      size="sm"
                      disabled={isFull}
                      onClick={() => handleOpenBookPass(rt)}
                    >
                      {isFull ? "Route Full" : "Book Bus Pass"}
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
          )}
        </div>
      )}

      {/* Tab: Fleet Vehicles */}
      {activeTab === "fleet" && (
        <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs dark:border-slate-800 dark:bg-slate-900">
          {loading ? (
            <TableSkeleton rows={4} cols={6} />
          ) : (
            <table className="w-full text-left text-sm text-slate-700 dark:text-slate-300">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500 border-b border-slate-200 dark:bg-slate-800/50 dark:border-slate-800">
              <tr>
                <th className="px-4 py-3">Registration Plate</th>
                <th className="px-4 py-3">Model / Make</th>
                <th className="px-4 py-3">Seating Capacity</th>
                <th className="px-4 py-3">Powertrain</th>
                <th className="px-4 py-3">Insurance Validity</th>
                <th className="px-4 py-3 text-right">Fitness Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {vehicles.map((v) => (
                <tr key={v.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition">
                  <td className="px-4 py-3 font-mono font-bold text-slate-900 dark:text-white">
                    {v.registrationNumber}
                  </td>
                  <td className="px-4 py-3">{v.model}</td>
                  <td className="px-4 py-3 font-mono">{v.capacitySeats} Passenger Seats</td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300">
                      {v.fuelType}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-500 font-mono text-xs">{v.insuranceValidUntil}</td>
                  <td className="px-4 py-3 text-right">
                    <Badge variant={v.status === "IN_SERVICE" ? "success" : "warning"} dot>
                      {v.status}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          )}
        </div>
      )}

      {/* Bus Pass Modal */}
      <Dialog
        open={passModalOpen}
        onClose={() => setPassModalOpen(false)}
        title={`Issue Bus Pass: ${selectedRoute?.routeName || ""}`}
        description={`Allocate annual transit commuter pass on Route ${selectedRoute?.routeCode || ""}.`}
      >
        <form onSubmit={handleConfirmPass} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Student Full Name <span className="text-red-400">*</span>
            </label>
            <Input
              value={passForm.studentName}
              onChange={(e) => setPassForm({ ...passForm, studentName: e.target.value })}
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Roll Number / Admission ID <span className="text-red-400">*</span>
            </label>
            <Input
              value={passForm.rollNumber}
              onChange={(e) => setPassForm({ ...passForm, rollNumber: e.target.value })}
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Designated Boarding Stop <span className="text-red-400">*</span>
            </label>
            <Input
              value={passForm.stopName}
              onChange={(e) => setPassForm({ ...passForm, stopName: e.target.value })}
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
            <Button variant="outline" type="button" onClick={() => setPassModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              Confirm & Issue Pass
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
