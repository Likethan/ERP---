"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  transportService,
  TransportLiveTelemetry,
  transportVehiclesService,
} from "@/services/transport.service";
import { TransportVehicle } from "@campusos/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Radio,
  Signal,
  SignalZero,
  ShieldCheck,
  ShieldAlert,
  Compass,
  MapPin,
  RefreshCw,
  Settings,
  ArrowLeft,
  Clock,
  Bus,
  CheckCircle2,
  Info,
} from "lucide-react";

export default function TransportTrackingPage() {
  const [loading, setLoading] = useState(true);
  const [vehicles, setVehicles] = useState<TransportVehicle[]>([]);
  const [telemetryMap, setTelemetryMap] = useState<Record<string, TransportLiveTelemetry>>({});
  const [selectedVehicle, setSelectedVehicle] = useState<TransportVehicle | null>(null);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [providerName, setProviderName] = useState("AIS140_STANDARD");
  const [deviceIdentifier, setDeviceIdentifier] = useState("");
  const [isEnabled, setIsEnabled] = useState(true);
  const [savingConfig, setSavingConfig] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  const loadData = async () => {
    setLoading(true);
    try {
      const vRes = await transportVehiclesService.listVehicles();
      const vList = vRes.data || [];
      setVehicles(vList);

      // Fetch telematics for each vehicle in parallel
      const telemEntries = await Promise.all(
        vList.map(async (v) => {
          try {
            const tRes = await transportService.getLiveTelemetry(v.id);
            if (tRes.success && tRes.data) {
              return [v.id, tRes.data] as const;
            }
          } catch {
            // Truthful fallback state: NOT_CONFIGURED
          }
          const defaultTelem: TransportLiveTelemetry = {
            vehicleId: v.id,
            registrationNumber: v.registrationNumber,
            trackingEnabled: false,
            status: "NOT_CONFIGURED",
            isDataStale: false,
            telemetryMessage: "No authorized telematics modem connected to this asset.",
          };
          return [v.id, defaultTelem] as const;
        })
      );

      const mapping: Record<string, TransportLiveTelemetry> = {};
      for (const [vId, tData] of telemEntries) {
        mapping[vId] = tData;
      }
      setTelemetryMap(mapping);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
  };

  const handleOpenConfig = (v: TransportVehicle) => {
    setSelectedVehicle(v);
    const curr = telemetryMap[v.id];
    setProviderName("AIS140_STANDARD");
    setDeviceIdentifier(v.registrationNumber ? `MODEM-${v.registrationNumber.replace(/[^A-Za-z0-9]/g, "")}` : "");
    setIsEnabled(curr?.trackingEnabled ?? true);
    setConfigDialogOpen(true);
  };

  const handleSaveConfig = async () => {
    if (!selectedVehicle) return;
    setSavingConfig(true);
    try {
      const res = await transportService.configureTracking(selectedVehicle.id, {
        providerName,
        deviceIdentifier: deviceIdentifier || undefined,
        isEnabled,
      });
      if (res.success) {
        setConfigDialogOpen(false);
        await loadData();
      }
    } finally {
      setSavingConfig(false);
    }
  };

  const filteredVehicles = vehicles.filter((v) => {
    if (statusFilter === "ALL") return true;
    const t = telemetryMap[v.id];
    return t?.status === statusFilter;
  });

  const activeCount = Object.values(telemetryMap).filter((t) => t.status === "ACTIVE").length;
  const offlineCount = Object.values(telemetryMap).filter((t) => t.status === "OFFLINE").length;
  const unconfiguredCount = Object.values(telemetryMap).filter((t) => t.status === "NOT_CONFIGURED").length;

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Breadcrumb & Navigation */}
      <div className="flex items-center gap-2 text-xs text-slate-400">
        <Link
          href="/app/infrastructure/transport"
          className="hover:text-blue-400 flex items-center gap-1"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Transport Management
        </Link>
        <span>/</span>
        <span className="text-white">Fleet Telematics & Truthful Tracking</span>
      </div>

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
              <Radio className="w-3.5 h-3.5 animate-pulse" />
              Real-Time Fleet Boundaries
            </span>
          </div>
          <h1 className="text-2xl lg:text-3xl font-bold text-white tracking-tight">
            Vehicle Telematics & Status
          </h1>
          <p className="text-slate-400 text-sm mt-1 max-w-3xl">
            Privacy-conscious fleet telemetry. Status is only reported when an authorized AIS-140 GPS or telematics gateway transmits verified signals. Location data is never fabricated or simulated.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={refreshing || loading}
            className="border-slate-800 text-slate-300 hover:text-white gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
            Refresh Telematics
          </Button>
          <Link href="/app/infrastructure/transport/trips">
            <Button size="sm" className="bg-blue-600 hover:bg-blue-500 text-white gap-2">
              <Compass className="w-4 h-4" />
              View Trip Dispatch
            </Button>
          </Link>
        </div>
      </div>

      {/* Privacy Notice Banner */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
        <div className="text-xs text-slate-300 space-y-1">
          <strong className="text-white font-medium">Compliance & Privacy Policy:</strong>
          <p className="text-slate-400">
            Per institutional safety standards, student identities are decoupled from raw GPS streams. Passenger manifests only record authorized boarding events at designated stops. Geolocation is restricted to fleet operations personnel and vehicle maintenance coordinators.
          </p>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div
          onClick={() => setStatusFilter("ALL")}
          className={`p-4 rounded-xl bg-slate-900/60 border cursor-pointer transition-all ${
            statusFilter === "ALL" ? "border-blue-500/50 bg-blue-500/5" : "border-slate-800 hover:border-slate-700"
          }`}
        >
          <div className="text-xs text-slate-400 font-medium">Total Registered Fleet</div>
          <div className="text-2xl font-bold text-white mt-1">{vehicles.length}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Asset Registry Connected</div>
        </div>

        <div
          onClick={() => setStatusFilter("ACTIVE")}
          className={`p-4 rounded-xl bg-slate-900/60 border cursor-pointer transition-all ${
            statusFilter === "ACTIVE" ? "border-emerald-500/50 bg-emerald-500/5" : "border-slate-800 hover:border-slate-700"
          }`}
        >
          <div className="text-xs text-emerald-400 font-medium flex items-center gap-1.5">
            <Signal className="w-3.5 h-3.5" />
            Online & Transmitting
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{activeCount}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Fresh telemetry pings</div>
        </div>

        <div
          onClick={() => setStatusFilter("OFFLINE")}
          className={`p-4 rounded-xl bg-slate-900/60 border cursor-pointer transition-all ${
            statusFilter === "OFFLINE" ? "border-amber-500/50 bg-amber-500/5" : "border-slate-800 hover:border-slate-700"
          }`}
        >
          <div className="text-xs text-amber-400 font-medium flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" />
            Stale / Offline
          </div>
          <div className="text-2xl font-bold text-amber-400 mt-1">{offlineCount}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Signal timed out (&gt;15 min)</div>
        </div>

        <div
          onClick={() => setStatusFilter("NOT_CONFIGURED")}
          className={`p-4 rounded-xl bg-slate-900/60 border cursor-pointer transition-all ${
            statusFilter === "NOT_CONFIGURED" ? "border-slate-600 bg-slate-800/40" : "border-slate-800 hover:border-slate-700"
          }`}
        >
          <div className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
            <SignalZero className="w-3.5 h-3.5" />
            Unconfigured Telematics
          </div>
          <div className="text-2xl font-bold text-slate-300 mt-1">{unconfiguredCount}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Modem registration pending</div>
        </div>
      </div>

      {/* Fleet Telematics Grid */}
      {loading ? (
        <div className="space-y-4">
          <Skeleton className="h-12 w-full rounded-xl" />
          <Skeleton className="h-64 w-full rounded-xl" />
        </div>
      ) : filteredVehicles.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800 space-y-3">
          <Bus className="w-10 h-10 text-slate-600 mx-auto" />
          <h3 className="text-base font-semibold text-white">No Vehicles Match Filter</h3>
          <p className="text-xs text-slate-400">
            Switch filter to &quot;All&quot; to review the complete institutional fleet.
          </p>
          <Button size="sm" variant="outline" onClick={() => setStatusFilter("ALL")}>
            Reset Filter
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredVehicles.map((v) => {
            const telem = telemetryMap[v.id];
            const isOnline = telem?.status === "ACTIVE";
            const isOffline = telem?.status === "OFFLINE";
            const isNotConfigured = !telem || telem.status === "NOT_CONFIGURED";

            return (
              <div
                key={v.id}
                className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all space-y-4 flex flex-col justify-between"
              >
                <div>
                  {/* Top Bar: Reg + Status Badge */}
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <div>
                      <div className="font-mono text-sm font-bold text-white flex items-center gap-2">
                        <Bus className="w-4 h-4 text-slate-400" />
                        {v.registrationNumber}
                      </div>
                      <div className="text-xs text-slate-400 mt-0.5">
                        {v.make} {v.model} ({v.type || "Bus"})
                      </div>
                    </div>

                    <Badge
                      variant="outline"
                      className={
                        isOnline
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 gap-1.5"
                          : isOffline
                          ? "bg-amber-500/10 text-amber-400 border-amber-500/20 gap-1.5"
                          : "bg-slate-800 text-slate-400 border-slate-700 gap-1.5"
                      }
                    >
                      {isOnline && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />}
                      {isOffline && <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />}
                      {isNotConfigured && <SignalZero className="w-3 h-3" />}
                      {telem?.status || "NOT_CONFIGURED"}
                    </Badge>
                  </div>

                  {/* Telematics Metrics or Truthful Unavailable State */}
                  <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2 text-xs">
                    {isOnline && telem.lastKnownLocation ? (
                      <>
                        <div className="flex justify-between items-center text-slate-400">
                          <span className="flex items-center gap-1.5 text-slate-300">
                            <MapPin className="w-3.5 h-3.5 text-blue-400" />
                            GPS Position:
                          </span>
                          <span className="font-mono text-white">
                            {telem.lastKnownLocation.latitude.toFixed(4)}°N, {telem.lastKnownLocation.longitude.toFixed(4)}°E
                          </span>
                        </div>
                        <div className="flex justify-between items-center text-slate-400">
                          <span className="flex items-center gap-1.5 text-slate-300">
                            <Compass className="w-3.5 h-3.5 text-emerald-400" />
                            Speed & Heading:
                          </span>
                          <span className="font-mono text-white">
                            {telem.lastKnownLocation.speedKmh} km/h • {telem.lastKnownLocation.headingDegrees ?? 0}°
                          </span>
                        </div>
                        <div className="flex justify-between items-center text-slate-400 pt-1 border-t border-slate-800/60">
                          <span className="flex items-center gap-1.5 text-slate-300">
                            <Clock className="w-3.5 h-3.5 text-slate-400" />
                            Last Ping:
                          </span>
                          <span className="text-slate-400 text-[11px]">
                            {new Date(telem.lastKnownLocation.recordedAt).toLocaleTimeString("en-IN", {
                              hour: "2-digit",
                              minute: "2-digit",
                              second: "2-digit",
                            })}
                          </span>
                        </div>
                      </>
                    ) : isOffline ? (
                      <div className="space-y-1.5">
                        <div className="flex items-center gap-2 text-amber-400 font-medium">
                          <Clock className="w-3.5 h-3.5" />
                          Modem Signal Stale
                        </div>
                        <p className="text-[11px] text-slate-400 leading-relaxed">
                          Last heartbeat received over 15 minutes ago. Vehicle ignition may be OFF or operating in an area with restricted cellular signal.
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-1.5">
                        <div className="flex items-center gap-2 text-slate-400 font-medium">
                          <Info className="w-3.5 h-3.5 text-slate-500" />
                          Truthful Telematics State
                        </div>
                        <p className="text-[11px] text-slate-500 leading-relaxed">
                          No GPS modem connected to this asset. In accordance with system policy, coordinates are not simulated.
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Bottom Actions */}
                <div className="pt-2 flex items-center justify-between border-t border-slate-800/60">
                  <span className="text-[11px] text-slate-500">
                    Cap: {v.capacity} Seats
                  </span>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleOpenConfig(v)}
                    className="border-slate-800 text-slate-300 hover:text-white text-xs h-7 gap-1.5"
                  >
                    <Settings className="w-3 h-3 text-slate-400" />
                    Configure Modem
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modem Configuration Dialog */}
      <Dialog open={configDialogOpen} onOpenChange={setConfigDialogOpen}>
        <DialogContent className="sm:max-w-md bg-slate-900 border-slate-800 text-white">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-white">
              <Radio className="w-5 h-5 text-emerald-400" />
              Configure Telematics Modem
            </DialogTitle>
            <DialogDescription className="text-slate-400 text-xs">
              Link an authorized AIS-140 GPS or IoT tracking device to institutional vehicle{" "}
              <strong className="text-white">{selectedVehicle?.registrationNumber}</strong>.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-3">
            <div className="space-y-1.5">
              <Label className="text-xs text-slate-300">Telematics Protocol / Provider</Label>
              <select
                value={providerName}
                onChange={(e) => setProviderName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
              >
                <option value="AIS140_STANDARD">AIS-140 Certified Commercial GPS</option>
                <option value="TELTONIKA_FMB">Teltonika FMB920 Fleet Tracker</option>
                <option value="GEOTAB_GO9">Geotab GO9 Telematics Unit</option>
                <option value="CAMPUS_WEBHOOK">Institutional IoT Gateway (Webhook)</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs text-slate-300">Device Hardware IMEI / Serial Number</Label>
              <Input
                value={deviceIdentifier}
                onChange={(e) => setDeviceIdentifier(e.target.value)}
                placeholder="e.g. 865239049281001"
                className="bg-slate-950 border-slate-800 text-xs text-white"
              />
              <p className="text-[11px] text-slate-500">
                Found on the physical modem label or vehicle telematics registration logbook.
              </p>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950 border border-slate-800">
              <div className="space-y-0.5">
                <div className="text-xs font-medium text-white">Enable Telemetry Stream</div>
                <div className="text-[11px] text-slate-400">
                  Allow verified incoming location pings for dispatch tracking.
                </div>
              </div>
              <input
                type="checkbox"
                checked={isEnabled}
                onChange={(e) => setIsEnabled(e.target.checked)}
                className="w-4 h-4 rounded border-slate-800 text-blue-600 focus:ring-0 bg-slate-900"
              />
            </div>
          </div>

          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setConfigDialogOpen(false)}
              className="border-slate-800 text-slate-400 hover:text-white"
            >
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={handleSaveConfig}
              disabled={savingConfig}
              className="bg-emerald-600 hover:bg-emerald-500 text-white gap-2"
            >
              <CheckCircle2 className="w-4 h-4" />
              {savingConfig ? "Saving..." : "Save Modem Settings"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
