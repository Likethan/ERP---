"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { transportVehiclesService } from "@/services/transport-vehicles.service";
import { TransportVehicle, VehicleStatus, VehicleType } from "@campusos/types";
import { DataGrid, ColumnDef } from "@/components/data-grid/data-grid";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Bus,
  Plus,
  Search,
  Eye,
  Clock,
  ShieldCheck,
  AlertTriangle,
  Wrench,
  Fuel,
} from "lucide-react";

export default function TransportVehiclesListPage() {
  const [vehicles, setVehicles] = useState<TransportVehicle[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Create Vehicle Modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createForm, setCreateForm] = useState({
    registrationNumber: "",
    vehicleNumber: "",
    type: VehicleType.BUS,
    makeModel: "Tata Starbus Ultra 52-Seater",
    capacity: 52,
    fuelType: "DIESEL" as "DIESEL" | "EV" | "CNG" | "PETROL",
    insuranceValidUntil: "2027-06-30",
    fitnessCertificateValidUntil: "2027-05-31",
  });

  const loadVehicles = async () => {
    setLoading(true);
    try {
      const res = await transportVehiclesService.listVehicles({
        type: typeFilter,
        status: statusFilter,
        search: searchQuery,
      });
      if (res.success && res.data) {
        setVehicles(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVehicles();
  }, [typeFilter, statusFilter, searchQuery]);

  const handleCreateVehicle = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.registrationNumber || !createForm.vehicleNumber) return;

    await transportVehiclesService.createVehicle({
      ...createForm,
      status: VehicleStatus.AVAILABLE,
    });

    setCreateModalOpen(false);
    setCreateForm({
      registrationNumber: "",
      vehicleNumber: "",
      type: VehicleType.BUS,
      makeModel: "Tata Starbus Ultra 52-Seater",
      capacity: 52,
      fuelType: "DIESEL" as "DIESEL" | "EV" | "CNG" | "PETROL",
      insuranceValidUntil: "2027-06-30",
      fitnessCertificateValidUntil: "2027-05-31",
    });
    loadVehicles();
  };

  // KPIs
  const totalFleet = vehicles.length;
  const activeFleet = vehicles.filter(
    (v) =>
      v.status === VehicleStatus.AVAILABLE || v.status === VehicleStatus.ACTIVE,
  ).length;
  const maintenanceFleet = vehicles.filter(
    (v) => v.status === VehicleStatus.MAINTENANCE,
  ).length;
  const totalSeats = vehicles.reduce((acc, v) => acc + (v.capacity || 0), 0);

  const columns: ColumnDef<TransportVehicle>[] = useMemo(
    () => [
      {
        id: "regNumber",
        header: "Registration & Fleet ID",
        cell: (v) => (
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                {v.registrationNumber}
              </span>
              <span className="font-mono text-xs text-slate-400">
                ({v.vehicleNumber})
              </span>
            </div>
            <span className="text-xs text-slate-400 block mt-1">
              {v.makeModel}
            </span>
          </div>
        ),
      },
      {
        id: "type",
        header: "Fleet Type & Capacity",
        cell: (v) => (
          <div className="text-xs">
            <span className="font-semibold text-white">{v.type}</span>
            <span className="text-slate-400 block mt-0.5">
              {v.capacity} Seating Capacity
            </span>
          </div>
        ),
      },
      {
        id: "assignment",
        header: "Route & Driver",
        cell: (v) => (
          <div className="text-xs space-y-0.5">
            <div className="text-white font-medium">
              {v.currentRouteName || "Unassigned Corridor"}
            </div>
            <div className="text-slate-400">
              Driver: {v.assignedDriverName || "Not assigned"}
            </div>
          </div>
        ),
      },
      {
        id: "fitness",
        header: "Compliance Validity",
        cell: (v) => {
          const fitDate = v.fitnessCertificateValidUntil;
          const insDate = v.insuranceValidUntil;
          return (
            <div className="text-xs space-y-1 text-slate-300">
              {fitDate && (
                <div className="flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3 text-emerald-400" />
                  <span>
                    FC: {new Date(fitDate).toLocaleDateString("en-IN")}
                  </span>
                </div>
              )}
              {insDate && (
                <div className="flex items-center gap-1 text-slate-400">
                  <Clock className="w-3 h-3 text-slate-500" />
                  <span>
                    Ins: {new Date(insDate).toLocaleDateString("en-IN")}
                  </span>
                </div>
              )}
            </div>
          );
        },
      },
      {
        id: "status",
        header: "Status",
        accessorKey: "status",
        cell: (v) => {
          const isAct =
            v.status === VehicleStatus.ACTIVE ||
            v.status === VehicleStatus.AVAILABLE;
          const isMaint = v.status === VehicleStatus.MAINTENANCE;
          return (
            <Badge
              variant="outline"
              className={
                isAct
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                  : isMaint
                    ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                    : "bg-slate-800 text-slate-400 border-slate-700"
              }
            >
              {v.status}
            </Badge>
          );
        },
      },
      {
        id: "actions",
        header: "Actions",
        cell: (v) => (
          <Link href={`/app/infrastructure/transport/vehicles/${v.id}`}>
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
            <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">
              Vehicles
            </span>
          </div>
          <h1 className="text-2xl lg:text-3xl font-bold text-white tracking-tight">
            Fleet Vehicle Roster
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Manage heavy college buses, minibuses, road fitness certificates,
            and service logbooks.
          </p>
        </div>

        <Button
          onClick={() => setCreateModalOpen(true)}
          className="bg-emerald-600 hover:bg-emerald-500 text-white gap-2 self-start md:self-auto"
        >
          <Plus className="w-4 h-4" />
          Register Vehicle
        </Button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="text-slate-400 text-xs font-medium">Total Fleet</div>
          <div className="text-2xl font-bold text-white mt-1">{totalFleet}</div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="text-slate-400 text-xs font-medium">
            Operational Buses
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">
            {activeFleet}
          </div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="text-slate-400 text-xs font-medium">
            In Workshop / Service
          </div>
          <div className="text-2xl font-bold text-amber-400 mt-1">
            {maintenanceFleet}
          </div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="text-slate-400 text-xs font-medium">
            Fleet Passenger Capacity
          </div>
          <div className="text-2xl font-bold text-blue-400 mt-1">
            {totalSeats} seats
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col md:flex-row items-center gap-4">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <Input
            placeholder="Search by registration number, model, fleet ID, or driver..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 bg-slate-950/60 border-slate-800 text-sm text-white placeholder:text-slate-500 w-full"
          />
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-emerald-500"
          >
            <option value="ALL">All Fleet Types</option>
            <option value="BUS">Buses</option>
            <option value="MINIBUS">Minibuses</option>
            <option value="VAN">Vans</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-emerald-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="AVAILABLE">Available</option>
            <option value="ACTIVE">Active</option>
            <option value="MAINTENANCE">Maintenance</option>
          </select>
        </div>
      </div>

      {/* DataGrid */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden backdrop-blur-sm">
        <DataGrid
          data={vehicles}
          columns={columns}
          loading={loading}
          emptyMessage="No vehicles found matching your criteria."
          keyExtractor={(item) => item.id}
        />
      </div>

      {/* Register Vehicle Modal */}
      {createModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-6 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Bus className="w-5 h-5 text-emerald-400" />
                Register New Fleet Vehicle
              </h3>
              <button
                onClick={() => setCreateModalOpen(false)}
                className="text-slate-400 hover:text-white text-lg"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateVehicle} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Registration No (RTO) *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. KA-04-E-9921"
                    value={createForm.registrationNumber}
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        registrationNumber: e.target.value,
                      })
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500 uppercase font-mono"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Fleet ID Code *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. BUS-09"
                    value={createForm.vehicleNumber}
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        vehicleNumber: e.target.value,
                      })
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500 uppercase font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">
                  Make & Model *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Ashok Leyland Viking 52-Seater"
                  value={createForm.makeModel}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, makeModel: e.target.value })
                  }
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Vehicle Type
                  </label>
                  <select
                    value={createForm.type}
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        type: e.target.value as VehicleType,
                      })
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                  >
                    <option value="BUS">Bus</option>
                    <option value="MINIBUS">Minibus</option>
                    <option value="VAN">Van</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Seat Capacity
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
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Fuel
                  </label>
                  <select
                    value={createForm.fuelType}
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        fuelType: e.target.value as
                          "DIESEL" | "EV" | "CNG" | "PETROL",
                      })
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                  >
                    <option value="DIESEL">Diesel</option>
                    <option value="CNG">CNG</option>
                    <option value="EV">Electric (EV)</option>
                    <option value="PETROL">Petrol</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Fitness Certificate Expiry
                  </label>
                  <input
                    type="date"
                    value={createForm.fitnessCertificateValidUntil}
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        fitnessCertificateValidUntil: e.target.value,
                      })
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Insurance Expiry
                  </label>
                  <input
                    type="date"
                    value={createForm.insuranceValidUntil}
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        insuranceValidUntil: e.target.value,
                      })
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
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
                <Button
                  type="submit"
                  className="bg-emerald-600 hover:bg-emerald-500 text-white"
                >
                  Register Vehicle
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
