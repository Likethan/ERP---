"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { transportDriversService } from "@/services/transport-drivers.service";
import { transportVehiclesService } from "@/services/transport-vehicles.service";
import { transportRoutesService } from "@/services/transport-routes.service";
import { TransportDriver, DriverStatus } from "@campusos/types";
import { DataGrid, ColumnDef } from "@/components/data-grid/data-grid";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Users,
  Plus,
  Search,
  Eye,
  Phone,
  Bus,
  ShieldCheck,
  Compass,
} from "lucide-react";

export default function TransportDriversListPage() {
  const [drivers, setDrivers] = useState<TransportDriver[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Create Driver Modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createForm, setCreateForm] = useState({
    name: "",
    employeeId: "",
    phone: "+91 ",
    licenseNumber: "",
    licenseExpiry: "2029-12-31",
    experienceYears: 8,
  });

  const loadDrivers = async () => {
    setLoading(true);
    try {
      const res = await transportDriversService.listDrivers({
        status: statusFilter,
        search: searchQuery,
      });
      if (res.success && res.data) {
        setDrivers(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDrivers();
  }, [statusFilter, searchQuery]);

  const handleCreateDriver = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.name || !createForm.licenseNumber) return;

    await transportDriversService.createDriver({
      ...createForm,
      status: DriverStatus.ACTIVE,
    });

    setCreateModalOpen(false);
    setCreateForm({
      name: "",
      employeeId: "",
      phone: "+91 ",
      licenseNumber: "",
      licenseExpiry: "2029-12-31",
      experienceYears: 8,
    });
    loadDrivers();
  };

  const activeDrivers = drivers.filter((d) => d.status === DriverStatus.ACTIVE).length;

  const columns: ColumnDef<TransportDriver>[] = useMemo(
    () => [
      {
        id: "driver",
        header: "Driver & Employee ID",
        cell: (d) => (
          <div>
            <Link
              href={`/app/infrastructure/transport/drivers/${d.id}`}
              className="font-medium text-white hover:text-cyan-300 text-sm block"
            >
              {d.name}
            </Link>
            <span className="font-mono text-xs text-slate-500">{d.employeeId}</span>
          </div>
        ),
      },
      {
        id: "license",
        header: "Heavy Transport License",
        cell: (d) => (
          <div className="text-xs space-y-0.5">
            <span className="font-mono text-slate-300 font-semibold">{d.licenseNumber}</span>
            <div className="text-slate-500">
              Valid till: {d.licenseExpiry ? new Date(d.licenseExpiry).toLocaleDateString("en-IN") : "2029"}
            </div>
          </div>
        ),
      },
      {
        id: "contact",
        header: "Contact Info",
        cell: (d) => (
          <div className="text-xs space-y-0.5 text-slate-300">
            <div className="flex items-center gap-1 font-mono">
              <Phone className="w-3 h-3 text-cyan-400" />
              {d.phone}
            </div>
            {d.emergencyContact && (
              <div className="text-[11px] text-slate-500">Emg: {d.emergencyContact}</div>
            )}
          </div>
        ),
      },
      {
        id: "assignment",
        header: "Vehicle & Corridor",
        cell: (d) => (
          <div className="text-xs space-y-0.5">
            <div className="flex items-center gap-1 text-white font-medium">
              <Bus className="w-3 h-3 text-emerald-400" />
              {d.assignedVehicleNumber || "Unassigned"}
            </div>
            <div className="text-slate-400">{d.assignedRouteName || "Standby Pool"}</div>
          </div>
        ),
      },
      {
        id: "status",
        header: "Duty Status",
        accessorKey: "status",
        cell: (d) => (
          <Badge
            variant="outline"
            className={
              d.status === DriverStatus.ACTIVE
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                : "bg-slate-800 text-slate-400 border-slate-700"
            }
          >
            {d.status}
          </Badge>
        ),
      },
      {
        id: "actions",
        header: "Actions",
        cell: (d) => (
          <Link href={`/app/infrastructure/transport/drivers/${d.id}`}>
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
            <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wider">
              Drivers
            </span>
          </div>
          <h1 className="text-2xl lg:text-3xl font-bold text-white tracking-tight">
            Driver & Crew Roster
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Manage commercial heavy transport licensed drivers, duty rosters, and verified credentials.
          </p>
        </div>

        <Button
          onClick={() => setCreateModalOpen(true)}
          className="bg-cyan-600 hover:bg-cyan-500 text-white gap-2 self-start md:self-auto"
        >
          <Plus className="w-4 h-4" />
          Add Driver
        </Button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="text-slate-400 text-xs font-medium">Total Crew</div>
          <div className="text-2xl font-bold text-white mt-1">{drivers.length}</div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="text-slate-400 text-xs font-medium">On Duty / Active</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{activeDrivers}</div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="text-slate-400 text-xs font-medium">Assigned to Routes</div>
          <div className="text-2xl font-bold text-cyan-400 mt-1">
            {drivers.filter((d) => d.assignedRouteName).length}
          </div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
          <div className="text-slate-400 text-xs font-medium">Standby / Relievers</div>
          <div className="text-2xl font-bold text-slate-400 mt-1">
            {drivers.filter((d) => !d.assignedRouteName).length}
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col md:flex-row items-center gap-4">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <Input
            placeholder="Search drivers by name, employee ID, phone, license, or route..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 bg-slate-950/60 border-slate-800 text-sm text-white placeholder:text-slate-500 w-full"
          />
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="ON_LEAVE">On Leave</option>
            <option value="SUSPENDED">Suspended</option>
          </select>
        </div>
      </div>

      {/* DataGrid */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden backdrop-blur-sm">
        <DataGrid
          data={drivers}
          columns={columns}
          loading={loading}
          emptyMessage="No drivers found matching your criteria."
        />
      </div>

      {/* Add Driver Modal */}
      {createModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-6 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Users className="w-5 h-5 text-cyan-400" />
                Add Fleet Driver
              </h3>
              <button
                onClick={() => setCreateModalOpen(false)}
                className="text-slate-400 hover:text-white text-lg"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateDriver} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Driver Full Name *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Anand Kumar"
                    value={createForm.name}
                    onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Employee ID
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. EMP-TR-108"
                    value={createForm.employeeId}
                    onChange={(e) => setCreateForm({ ...createForm, employeeId: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500 font-mono"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Primary Phone Number *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="+91 98455 12009"
                    value={createForm.phone}
                    onChange={(e) => setCreateForm({ ...createForm, phone: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500 font-mono"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Experience (Years)
                  </label>
                  <input
                    type="number"
                    min={1}
                    value={createForm.experienceYears}
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        experienceYears: parseInt(e.target.value) || 5,
                      })
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Driving License Number *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. KA-04-2018-0091823"
                    value={createForm.licenseNumber}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, licenseNumber: e.target.value })
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500 font-mono"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    License Expiry Date
                  </label>
                  <input
                    type="date"
                    value={createForm.licenseExpiry}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, licenseExpiry: e.target.value })
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
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
                <Button type="submit" className="bg-cyan-600 hover:bg-cyan-500 text-white">
                  Add Driver
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
