"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { transportVehiclesService } from "@/services/transport-vehicles.service";
import { TransportVehicle, VehicleStatus } from "@campusos/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Bus,
  ArrowLeft,
  ShieldCheck,
  Clock,
  Wrench,
  Fuel,
  Users,
  Compass,
  Calendar,
  AlertTriangle,
  Plus,
  CheckCircle2,
  FileText,
} from "lucide-react";

export default function TransportVehicleDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const vehicleId = resolvedParams.id;

  const [loading, setLoading] = useState(true);
  const [vehicle, setVehicle] = useState<TransportVehicle | null>(null);

  // Add Service Modal
  const [serviceModalOpen, setServiceModalOpen] = useState(false);
  const [serviceForm, setServiceForm] = useState({
    serviceDate: new Date().toISOString().split("T")[0],
    serviceType: "Periodic Maintenance & Brake Pad Replacement",
    mileageKm: 32000,
    costInr: 18500,
    nextServiceDate: "2027-04-15",
    vendorName: "Authorized Tata Motors Commercial Workshop",
    notes: "",
  });

  const loadVehicle = async () => {
    setLoading(true);
    try {
      const res = await transportVehiclesService.getVehicleById(vehicleId);
      if (res.success && res.data) {
        setVehicle(res.data);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVehicle();
  }, [vehicleId]);

  const handleAddService = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!vehicle) return;

    await transportVehiclesService.addServiceRecord(vehicle.id, serviceForm);
    setServiceModalOpen(false);
    loadVehicle();
  };

  if (loading) {
    return (
      <div className="p-6 lg:p-8 space-y-6 max-w-6xl mx-auto">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full rounded-2xl" />
        <Skeleton className="h-96 w-full rounded-2xl" />
      </div>
    );
  }

  if (!vehicle) {
    return (
      <div className="p-12 text-center text-slate-400">
        <h2 className="text-lg font-bold text-white mb-2">
          Fleet Vehicle Record Not Found
        </h2>
        <Link href="/app/infrastructure/transport/vehicles">
          <Button variant="outline" className="border-slate-700">
            Back to Vehicles
          </Button>
        </Link>
      </div>
    );
  }

  const isAct =
    vehicle.status === VehicleStatus.ACTIVE ||
    vehicle.status === VehicleStatus.AVAILABLE;
  const isMaint = vehicle.status === VehicleStatus.MAINTENANCE;

  const totalServiceSpend = (vehicle.services || []).reduce(
    (acc, s) => acc + (s.costInr || 0),
    0,
  );

  return (
    <div className="p-6 lg:p-8 space-y-8 max-w-6xl mx-auto">
      {/* Back button */}
      <div>
        <Link
          href="/app/infrastructure/transport/vehicles"
          className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Vehicles
        </Link>
      </div>

      {/* Hero Header */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 lg:p-8 backdrop-blur-sm relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-3">
              <span className="font-mono text-sm font-bold text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-md border border-emerald-500/20">
                {vehicle.registrationNumber}
              </span>
              <span className="font-mono text-xs text-slate-400">
                ({vehicle.vehicleNumber})
              </span>
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
                {vehicle.status}
              </Badge>
              <Badge
                variant="outline"
                className="bg-slate-800 text-slate-300 border-slate-700"
              >
                {vehicle.type}
              </Badge>
            </div>
            <h1 className="text-2xl lg:text-3xl font-bold text-white tracking-tight">
              {vehicle.makeModel || `${vehicle.make} ${vehicle.model}`}
            </h1>
            <p className="text-slate-400 text-sm flex items-center gap-3">
              <span>{vehicle.capacity} Passenger Capacity</span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Fuel className="w-3.5 h-3.5 text-slate-500" />
                {vehicle.fuelType || "DIESEL"}
              </span>
            </p>
          </div>

          <Button
            onClick={() => setServiceModalOpen(true)}
            className="bg-emerald-600 hover:bg-emerald-500 text-white gap-2 self-start lg:self-auto"
          >
            <Plus className="w-4 h-4" />
            Log Service Audit
          </Button>
        </div>
      </div>

      {/* Compliance & Current Assignment Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Fitness Card */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">
              Fitness Certificate
            </span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-lg font-bold text-white font-mono">
            {vehicle.fitnessCertificateValidUntil
              ? new Date(
                  vehicle.fitnessCertificateValidUntil,
                ).toLocaleDateString("en-IN")
              : "Valid"}
          </div>
          <div className="text-[11px] text-slate-500">
            RTO roadworthiness certificate
          </div>
        </div>

        {/* Insurance Card */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">
              Commercial Insurance
            </span>
            <FileText className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-lg font-bold text-white font-mono">
            {vehicle.insuranceValidUntil
              ? new Date(vehicle.insuranceValidUntil).toLocaleDateString(
                  "en-IN",
                )
              : "Active"}
          </div>
          <div className="text-[11px] text-slate-500">
            {vehicle.insurancePolicyNumber || "Comprehensive Cover"}
          </div>
        </div>

        {/* Assigned Corridor */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">
              Transit Assignment
            </span>
            <Compass className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-sm font-semibold text-white truncate">
            {vehicle.currentRouteName || "Unassigned"}
          </div>
          <div className="text-[11px] text-slate-500">
            Scheduled college bus route
          </div>
        </div>

        {/* Total Service Spend in INR */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">
              Service Expenditure
            </span>
            <Wrench className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-lg font-bold text-amber-400 font-mono">
            ₹{totalServiceSpend.toLocaleString("en-IN")}
          </div>
          <div className="text-[11px] text-slate-500">
            Lifetime recorded maintenance
          </div>
        </div>
      </div>

      {/* Service History Logbook Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 lg:p-8 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <Wrench className="w-4 h-4 text-emerald-400" />
              Service & Workshop Logbook
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Chronological log of periodic servicing, replacement parts, and
              expenditures
            </p>
          </div>
          <span className="text-xs text-slate-500 font-mono">
            {(vehicle.services || []).length} Records
          </span>
        </div>

        <div className="space-y-4">
          {(vehicle.services || []).length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-sm">
              No historical workshop records logged for this vehicle yet.
            </div>
          ) : (
            (vehicle.services || []).map((srv, idx) => (
              <div
                key={srv.id || idx}
                className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/80 hover:border-slate-700 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-white text-sm">
                      {srv.serviceType}
                    </span>
                    <Badge
                      variant="outline"
                      className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 text-[10px]"
                    >
                      {srv.status || "COMPLETED"}
                    </Badge>
                  </div>
                  <div className="text-xs text-slate-400 flex flex-wrap items-center gap-3">
                    <span>
                      Workshop:{" "}
                      <strong className="text-slate-300">
                        {srv.vendorName}
                      </strong>
                    </span>
                    <span>•</span>
                    <span>
                      Odometer:{" "}
                      <strong className="font-mono text-slate-300">
                        {srv.mileageKm?.toLocaleString("en-IN")} KM
                      </strong>
                    </span>
                    <span>•</span>
                    <span>
                      Serviced on:{" "}
                      <strong className="text-slate-300">
                        {new Date(srv.serviceDate).toLocaleDateString("en-IN")}
                      </strong>
                    </span>
                  </div>
                  {srv.notes && (
                    <p className="text-xs text-slate-400 mt-1 italic">
                      {srv.notes}
                    </p>
                  )}
                </div>

                <div className="text-right shrink-0">
                  <span className="text-xs text-slate-500 block">
                    Cost (INR)
                  </span>
                  <span className="font-mono text-base font-bold text-white">
                    ₹{srv.costInr?.toLocaleString("en-IN")}
                  </span>
                  {srv.nextServiceDate && (
                    <span className="text-[11px] text-slate-400 block mt-0.5">
                      Next due:{" "}
                      {new Date(srv.nextServiceDate).toLocaleDateString(
                        "en-IN",
                      )}
                    </span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Add Service Modal */}
      {serviceModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-6 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Wrench className="w-5 h-5 text-emerald-400" />
                Record Workshop Service Audit
              </h3>
              <button
                onClick={() => setServiceModalOpen(false)}
                className="text-slate-400 hover:text-white text-lg"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddService} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">
                  Service / Repair Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 30,000 KM Engine Oil & Filter Service"
                  value={serviceForm.serviceType}
                  onChange={(e) =>
                    setServiceForm({
                      ...serviceForm,
                      serviceType: e.target.value,
                    })
                  }
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Service Date *
                  </label>
                  <input
                    type="date"
                    required
                    value={serviceForm.serviceDate}
                    onChange={(e) =>
                      setServiceForm({
                        ...serviceForm,
                        serviceDate: e.target.value,
                      })
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Next Due Date
                  </label>
                  <input
                    type="date"
                    value={serviceForm.nextServiceDate}
                    onChange={(e) =>
                      setServiceForm({
                        ...serviceForm,
                        nextServiceDate: e.target.value,
                      })
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Cost in INR (₹) *
                  </label>
                  <input
                    type="number"
                    required
                    min={0}
                    placeholder="18500"
                    value={serviceForm.costInr}
                    onChange={(e) =>
                      setServiceForm({
                        ...serviceForm,
                        costInr: parseInt(e.target.value) || 0,
                      })
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500 font-mono"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">
                    Odometer Mileage (KM)
                  </label>
                  <input
                    type="number"
                    min={0}
                    placeholder="32000"
                    value={serviceForm.mileageKm}
                    onChange={(e) =>
                      setServiceForm({
                        ...serviceForm,
                        mileageKm: parseInt(e.target.value) || 0,
                      })
                    }
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">
                  Workshop / Vendor Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Authorized Tata Commercial Center"
                  value={serviceForm.vendorName}
                  onChange={(e) =>
                    setServiceForm({
                      ...serviceForm,
                      vendorName: e.target.value,
                    })
                  }
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setServiceModalOpen(false)}
                  className="border-slate-800 text-slate-400"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  className="bg-emerald-600 hover:bg-emerald-500 text-white"
                >
                  Record Log
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
