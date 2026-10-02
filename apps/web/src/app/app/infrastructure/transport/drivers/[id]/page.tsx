"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { transportDriversService } from "@/services/transport-drivers.service";
import { TransportDriver, DriverStatus } from "@campusos/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Users,
  ArrowLeft,
  Phone,
  Mail,
  ShieldCheck,
  Bus,
  Compass,
  Calendar,
  Clock,
  AlertCircle,
} from "lucide-react";

export default function TransportDriverDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const driverId = resolvedParams.id;

  const [loading, setLoading] = useState(true);
  const [driver, setDriver] = useState<TransportDriver | null>(null);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const res = await transportDriversService.getDriverById(driverId);
        if (res.success && res.data) {
          setDriver(res.data);
        }
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [driverId]);

  if (loading) {
    return (
      <div className="p-6 lg:p-8 space-y-6 max-w-5xl mx-auto">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full rounded-2xl" />
      </div>
    );
  }

  if (!driver) {
    return (
      <div className="p-12 text-center text-slate-400">
        <h2 className="text-lg font-bold text-white mb-2">Driver Dossier Not Found</h2>
        <Link href="/app/infrastructure/transport/drivers">
          <Button variant="outline" className="border-slate-700">
            Back to Drivers
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 space-y-8 max-w-5xl mx-auto">
      {/* Back button */}
      <div>
        <Link
          href="/app/infrastructure/transport/drivers"
          className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Drivers
        </Link>
      </div>

      {/* Hero Header */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 lg:p-8 backdrop-blur-sm relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-3">
              <span className="font-mono text-sm font-bold text-cyan-400 bg-cyan-500/10 px-3 py-1 rounded-md border border-cyan-500/20">
                {driver.employeeId}
              </span>
              <Badge
                variant="outline"
                className={
                  driver.status === DriverStatus.ACTIVE
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                    : "bg-slate-800 text-slate-400 border-slate-700"
                }
              >
                {driver.status}
              </Badge>
              <Badge variant="outline" className="bg-slate-800 text-slate-300 border-slate-700">
                {driver.experienceYears || 8} Years Commercial Experience
              </Badge>
            </div>
            <h1 className="text-2xl lg:text-3xl font-bold text-white tracking-tight">
              {driver.name}
            </h1>
            <p className="text-slate-400 text-sm flex items-center gap-4">
              <span className="flex items-center gap-1.5 font-mono text-white">
                <Phone className="w-4 h-4 text-cyan-400" />
                {driver.phone}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1.5 text-slate-300">
                <Mail className="w-4 h-4 text-slate-500" />
                {driver.email || "driver.ops@campusos.edu"}
              </span>
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 min-w-[200px]">
            <span className="text-xs text-slate-500 block mb-1">Roster Assignment</span>
            <div className="text-sm font-semibold text-white">
              {driver.assignedVehicleNumber ? (
                <div className="flex items-center gap-1.5 text-emerald-400">
                  <Bus className="w-4 h-4" />
                  {driver.assignedVehicleNumber}
                </div>
              ) : (
                <span className="text-slate-400">Reserve / Standby Crew</span>
              )}
            </div>
            <div className="text-xs text-slate-400 mt-1">
              {driver.assignedRouteName || "No active corridor"}
            </div>
          </div>
        </div>
      </div>

      {/* Driver Credentials & Safety Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Heavy Commercial License Card */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
            Driving License & RTO Credentials
          </h2>
          <div className="space-y-3 text-sm">
            <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800/80">
              <span className="text-xs text-slate-500 block mb-1">License Number (HMV / Transport)</span>
              <span className="font-mono text-base font-bold text-white">
                {driver.licenseNumber}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="bg-slate-950/50 p-3 rounded-xl border border-slate-800/80">
                <span className="text-slate-500 block">Valid Until</span>
                <span className="font-semibold text-white mt-0.5 block">
                  {driver.licenseExpiry
                    ? new Date(driver.licenseExpiry).toLocaleDateString("en-IN")
                    : "31 Dec 2029"}
                </span>
              </div>
              <div className="bg-slate-950/50 p-3 rounded-xl border border-slate-800/80">
                <span className="text-slate-500 block">Endorsements</span>
                <span className="font-semibold text-emerald-400 mt-0.5 block">
                  Heavy Passenger (HPV)
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Emergency & Medical Clearance */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-400" />
            Emergency Contacts & Medical
          </h2>
          <div className="space-y-3 text-sm">
            <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800/80">
              <span className="text-xs text-slate-500 block mb-1">Emergency Contact</span>
              <span className="font-medium text-white">
                {driver.emergencyContact || "+91 98455 99001 (Spouse)"}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="bg-slate-950/50 p-3 rounded-xl border border-slate-800/80">
                <span className="text-slate-500 block">Blood Group</span>
                <span className="font-semibold text-white mt-0.5 block">O Positive (O+)</span>
              </div>
              <div className="bg-slate-950/50 p-3 rounded-xl border border-slate-800/80">
                <span className="text-slate-500 block">Annual Medical Test</span>
                <span className="font-semibold text-emerald-400 mt-0.5 block">Cleared (2026)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
