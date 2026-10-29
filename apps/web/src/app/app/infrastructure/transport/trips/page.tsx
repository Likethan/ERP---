"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  transportService,
  TransportTripItem,
  TripManifestData,
} from "@/services/transport.service";
import { transportRoutesService } from "@/services/transport-routes.service";
import { transportVehiclesService } from "@/services/transport-vehicles.service";
import { transportDriversService } from "@/services/transport-drivers.service";
import { TransportRoute, TransportVehicle, TransportDriver } from "@campusos/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Bus,
  Calendar,
  CheckCircle2,
  Clock,
  Compass,
  FileText,
  Navigation,
  Play,
  QrCode,
  ShieldAlert,
  ShieldCheck,
  UserCheck,
  Users,
  Wrench,
  XCircle,
} from "lucide-react";

export default function TransportTripsPage() {
  const [loading, setLoading] = useState(true);
  const [trips, setTrips] = useState<TransportTripItem[]>([]);
  const [routes, setRoutes] = useState<TransportRoute[]>([]);
  const [vehicles, setVehicles] = useState<TransportVehicle[]>([]);
  const [drivers, setDrivers] = useState<TransportDriver[]>([]);
  const [selectedRoute, setSelectedRoute] = useState("ALL");
  const [selectedStatus, setSelectedStatus] = useState("ALL");

  // Schedule modal
  const [isScheduleOpen, setIsScheduleOpen] = useState(false);
  const [scheduleRouteId, setScheduleRouteId] = useState("");
  const [scheduleVehicleId, setScheduleVehicleId] = useState("");
  const [scheduleDriverId, setScheduleDriverId] = useState("");
  const [scheduleDate, setScheduleDate] = useState(new Date().toISOString().split("T")[0]);
  const [scheduleWindow, setScheduleWindow] = useState("MORNING_PICKUP");

  // Dispatch modal
  const [isDispatchOpen, setIsDispatchOpen] = useState(false);
  const [activeTrip, setActiveTrip] = useState<TransportTripItem | null>(null);
  const [startOdometer, setStartOdometer] = useState(50000);
  const [brakesOk, setBrakesOk] = useState(true);
  const [tiresOk, setTiresOk] = useState(true);
  const [lightsOk, setLightsOk] = useState(true);
  const [emergencyExitOk, setEmergencyExitOk] = useState(true);
  const [firstAidKitOk, setFirstAidKitOk] = useState(true);

  // Manifest modal
  const [isManifestOpen, setIsManifestOpen] = useState(false);
  const [manifestData, setManifestData] = useState<TripManifestData | null>(null);

  // Complete Trip modal
  const [isCompleteOpen, setIsCompleteOpen] = useState(false);
  const [endOdometer, setEndOdometer] = useState(50025);

  // Action status message
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  async function loadData() {
    setLoading(true);
    try {
      const [tripsRes, routesRes, vehiclesRes, driversRes] = await Promise.all([
        transportService.listTrips({
          routeId: selectedRoute,
          status: selectedStatus,
        }),
        transportRoutesService.listRoutes(),
        transportVehiclesService.listVehicles(),
        transportDriversService.listDrivers(),
      ]);

      if (tripsRes.success && tripsRes.data) {
        setTrips(tripsRes.data);
      } else {
        // Fallback demo data
        setTrips([
          {
            id: "trip-01",
            tripNumber: "TRIP-20261023-0001",
            routeId: "r-101",
            routeName: "Gandhipuram to Campus Express",
            vehicleId: "v-01",
            vehicleRegistration: "TN-38-BZ-1001",
            driverId: "d-01",
            driverName: "Murugan Ramasamy",
            tripDate: "2026-10-23",
            serviceWindow: "MORNING_PICKUP",
            scheduledStartTime: "2026-10-23T07:30:00Z",
            scheduledEndTime: "2026-10-23T08:30:00Z",
            startOdometerKm: 48250,
            status: "IN_PROGRESS",
            preTripChecklistCompleted: true,
          },
          {
            id: "trip-02",
            tripNumber: "TRIP-20261023-0002",
            routeId: "r-102",
            routeName: "Peelamedu Airport Transit",
            vehicleId: "v-02",
            vehicleRegistration: "TN-38-BZ-1002",
            driverId: "d-02",
            driverName: "Ravi Chandran",
            tripDate: "2026-10-23",
            serviceWindow: "MORNING_PICKUP",
            scheduledStartTime: "2026-10-23T07:45:00Z",
            scheduledEndTime: "2026-10-23T08:45:00Z",
            status: "SCHEDULED",
            preTripChecklistCompleted: false,
          },
        ]);
      }

      if (routesRes.success && routesRes.data) setRoutes(routesRes.data);
      if (vehiclesRes.success && vehiclesRes.data) setVehicles(vehiclesRes.data);
      if (driversRes.success && driversRes.data) setDrivers(driversRes.data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [selectedRoute, selectedStatus]);

  async function handleScheduleSubmit() {
    if (!scheduleRouteId || !scheduleVehicleId || !scheduleDriverId) {
      setFeedback({ type: "error", message: "Please select route, vehicle, and authorized driver." });
      return;
    }

    try {
      const res = await transportService.scheduleTrip({
        routeId: scheduleRouteId,
        vehicleId: scheduleVehicleId,
        driverId: scheduleDriverId,
        tripDate: scheduleDate,
        serviceWindow: scheduleWindow,
        scheduledStartTime: `${scheduleDate}T07:30:00Z`,
        scheduledEndTime: `${scheduleDate}T08:30:00Z`,
      });

      if (res.success) {
        setFeedback({ type: "success", message: `Trip ${res.data.tripNumber} scheduled successfully!` });
        setIsScheduleOpen(false);
        loadData();
      } else {
        setFeedback({ type: "error", message: "Failed to schedule trip: compliance or conflict detected." });
      }
    } catch (err: any) {
      setFeedback({ type: "error", message: err.message || "Failed to schedule trip" });
    }
  }

  async function handleDispatchSubmit() {
    if (!activeTrip) return;
    try {
      const res = await transportService.dispatchTrip(activeTrip.id, {
        startOdometerKm: Number(startOdometer),
        preTripChecklistCompleted: brakesOk && tiresOk && lightsOk && emergencyExitOk && firstAidKitOk,
        checklistNotes: { brakesOk, tiresOk, lightsOk, emergencyExitOk, firstAidKitOk },
      });

      if (res.success) {
        setFeedback({ type: "success", message: `Trip ${activeTrip.tripNumber} dispatched successfully!` });
        setIsDispatchOpen(false);
        loadData();
      } else {
        setFeedback({ type: "error", message: "Dispatch blocked by pre-trip safety checks." });
      }
    } catch (err: any) {
      setFeedback({ type: "error", message: err.message || "Failed to dispatch trip" });
    }
  }

  async function handleCompleteSubmit() {
    if (!activeTrip) return;
    try {
      const res = await transportService.completeTrip(activeTrip.id, Number(endOdometer));
      if (res.success) {
        setFeedback({ type: "success", message: `Trip ${activeTrip.tripNumber} completed. Vehicle odometer updated.` });
        setIsCompleteOpen(false);
        loadData();
      }
    } catch (err: any) {
      setFeedback({ type: "error", message: err.message || "Failed to complete trip" });
    }
  }

  async function openManifest(trip: TransportTripItem) {
    setActiveTrip(trip);
    try {
      const res = await transportService.getTripManifest(trip.id);
      if (res.success && res.data) {
        setManifestData(res.data);
      } else {
        // Fallback manifest
        setManifestData({
          trip,
          totalManifestCount: 3,
          boardedCount: 1,
          absentCount: 0,
          pendingCount: 2,
          passengers: [
            {
              id: "p-01",
              studentId: "s-101",
              studentName: "Aditya Varma",
              admissionNumber: "ADM-2026-001",
              stopId: "st-01",
              stopName: "Gandhipuram",
              boardingStatus: "BOARDED",
              verificationMethod: "QR_CODE",
            },
            {
              id: "p-02",
              studentId: "s-102",
              studentName: "Deepa Rao",
              admissionNumber: "ADM-2026-002",
              stopId: "st-02",
              stopName: "Lakshmi Mills",
              boardingStatus: "EXPECTED",
              verificationMethod: "MANUAL",
            },
            {
              id: "p-03",
              studentId: "s-103",
              studentName: "Karthik Sundaram",
              admissionNumber: "ADM-2026-003",
              stopId: "st-03",
              stopName: "Peelamedu",
              boardingStatus: "EXPECTED",
              verificationMethod: "MANUAL",
            },
          ],
        });
      }
      setIsManifestOpen(true);
    } catch {
      //
    }
  }

  async function verifyPassenger(studentId: string, stopId: string) {
    if (!activeTrip) return;
    try {
      await transportService.recordBoarding(activeTrip.id, {
        studentId,
        stopId,
        verificationMethod: "QR_CODE",
        boardingStatus: "BOARDED",
      });
      openManifest(activeTrip);
    } catch {
      //
    }
  }

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <Link href="/app/infrastructure/transport" className="hover:underline">
              Transport Operations
            </Link>
            <span>/</span>
            <span className="text-foreground font-medium">Trip Scheduling & Dispatch</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Trip Dispatch Operations</h1>
          <p className="text-sm text-muted-foreground">
            Schedule transit runs, conduct pre-trip safety checks, dispatch vehicles, and track passenger boarding.
          </p>
        </div>
        <Button onClick={() => setIsScheduleOpen(true)} className="gap-2 bg-blue-600 hover:bg-blue-700">
          <Calendar className="h-4 w-4" />
          Schedule New Trip
        </Button>
      </div>

      {/* Feedback Alert */}
      {feedback && (
        <div
          className={`p-4 rounded-lg flex items-center justify-between text-sm ${
            feedback.type === "success"
              ? "bg-emerald-50 text-emerald-800 border border-emerald-200 dark:bg-emerald-950 dark:text-emerald-200"
              : "bg-red-50 text-red-800 border border-red-200 dark:bg-red-950 dark:text-red-200"
          }`}
        >
          <div className="flex items-center gap-2">
            {feedback.type === "success" ? <CheckCircle2 className="h-4 w-4" /> : <ShieldAlert className="h-4 w-4" />}
            <span>{feedback.message}</span>
          </div>
          <button onClick={() => setFeedback(null)} className="text-xs underline hover:no-underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center gap-3 bg-slate-900/40 p-3 rounded-xl border border-slate-800">
        <select
          value={selectedRoute}
          onChange={(e) => setSelectedRoute(e.target.value)}
          className="h-9 px-3 rounded-lg border border-slate-800 bg-slate-950 text-xs text-white focus:outline-none focus:border-blue-500 w-56"
        >
          <option value="ALL">All Transit Routes</option>
          {routes.map((r) => (
            <option key={r.id} value={r.id}>
              {r.routeCode} - {r.name}
            </option>
          ))}
        </select>

        <select
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
          className="h-9 px-3 rounded-lg border border-slate-800 bg-slate-950 text-xs text-white focus:outline-none focus:border-blue-500 w-44"
        >
          <option value="ALL">All Statuses</option>
          <option value="SCHEDULED">Scheduled</option>
          <option value="IN_PROGRESS">In Progress</option>
          <option value="COMPLETED">Completed</option>
          <option value="CANCELLED">Cancelled</option>
        </select>
      </div>

      {/* Trips Table */}
      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-20 rounded-xl" />
          ))}
        </div>
      ) : trips.length === 0 ? (
        <div className="text-center p-12 bg-muted/20 border rounded-xl space-y-3">
          <Bus className="h-10 w-10 text-muted-foreground mx-auto" />
          <h3 className="text-lg font-semibold">No Scheduled Trips</h3>
          <p className="text-sm text-muted-foreground">No transit runs scheduled for the selected filters.</p>
        </div>
      ) : (
        <div className="border rounded-xl overflow-hidden bg-card shadow-sm">
          <table className="w-full text-left text-sm">
            <thead className="bg-muted/50 border-b text-xs uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="p-4">Trip Details</th>
                <th className="p-4">Route</th>
                <th className="p-4">Vehicle & Driver</th>
                <th className="p-4">Service Window</th>
                <th className="p-4">Pre-Trip Safety</th>
                <th className="p-4">Status</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {trips.map((trip) => (
                <tr key={trip.id} className="hover:bg-muted/30 transition-colors">
                  <td className="p-4">
                    <div className="font-semibold">{trip.tripNumber}</div>
                    <div className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                      <Calendar className="h-3 w-3" />
                      {trip.tripDate}
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="font-medium text-foreground">{trip.routeName || "Gandhipuram Express"}</div>
                    <div className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                      <Clock className="h-3 w-3" />
                      {new Date(trip.scheduledStartTime).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} -{" "}
                      {new Date(trip.scheduledEndTime).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="font-medium">{trip.vehicleRegistration || "TN-38-BZ-1001"}</div>
                    <div className="text-xs text-muted-foreground">{trip.driverName || "Authorized Driver"}</div>
                  </td>
                  <td className="p-4">
                    <Badge variant="outline" className="text-xs">
                      {trip.serviceWindow.replace("_", " ")}
                    </Badge>
                  </td>
                  <td className="p-4">
                    {trip.preTripChecklistCompleted ? (
                      <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200 gap-1 dark:bg-emerald-950 dark:text-emerald-300">
                        <ShieldCheck className="h-3 w-3" />
                        Verified
                      </Badge>
                    ) : (
                      <Badge variant="destructive" className="gap-1">
                        <ShieldAlert className="h-3 w-3" />
                        Pending
                      </Badge>
                    )}
                  </td>
                  <td className="p-4">
                    <Badge
                      className={
                        trip.status === "COMPLETED"
                          ? "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950 dark:text-emerald-300"
                          : trip.status === "IN_PROGRESS"
                          ? "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950 dark:text-blue-300 animate-pulse"
                          : trip.status === "SCHEDULED"
                          ? "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950 dark:text-amber-300"
                          : "bg-red-50 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-300"
                      }
                    >
                      {trip.status}
                    </Badge>
                  </td>
                  <td className="p-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button variant="ghost" size="sm" onClick={() => openManifest(trip)} className="gap-1">
                        <FileText className="h-3.5 w-3.5" />
                        Manifest
                      </Button>

                      {trip.status === "SCHEDULED" && (
                        <Button
                          size="sm"
                          onClick={() => {
                            setActiveTrip(trip);
                            setIsDispatchOpen(true);
                          }}
                          className="bg-emerald-600 hover:bg-emerald-700 text-white gap-1"
                        >
                          <Play className="h-3 w-3" />
                          Dispatch
                        </Button>
                      )}

                      {trip.status === "IN_PROGRESS" && (
                        <Button
                          size="sm"
                          onClick={() => {
                            setActiveTrip(trip);
                            setIsCompleteOpen(true);
                          }}
                          className="bg-blue-600 hover:bg-blue-700 text-white gap-1"
                        >
                          <CheckCircle2 className="h-3 w-3" />
                          Complete
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Schedule Trip Dialog */}
      <Dialog open={isScheduleOpen} onOpenChange={setIsScheduleOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Schedule Transit Run</DialogTitle>
            <DialogDescription>
              Assign a compliant vehicle and licensed driver to an authorized transit route corridor.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <Label className="text-xs">Transit Route</Label>
              <select
                value={scheduleRouteId}
                onChange={(e) => setScheduleRouteId(e.target.value)}
                className="mt-1 flex h-9 w-full rounded-md border border-slate-800 bg-slate-950 px-3 py-1 text-xs text-white focus:outline-none focus:border-blue-500"
              >
                <option value="">Select route</option>
                {routes.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.routeCode} - {r.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <Label className="text-xs">Fleet Vehicle</Label>
              <select
                value={scheduleVehicleId}
                onChange={(e) => setScheduleVehicleId(e.target.value)}
                className="mt-1 flex h-9 w-full rounded-md border border-slate-800 bg-slate-950 px-3 py-1 text-xs text-white focus:outline-none focus:border-blue-500"
              >
                <option value="">Select vehicle</option>
                {vehicles.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.registrationNumber} ({v.type || "BUS"} - Cap: {v.capacity})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <Label className="text-xs">Authorized Driver</Label>
              <select
                value={scheduleDriverId}
                onChange={(e) => setScheduleDriverId(e.target.value)}
                className="mt-1 flex h-9 w-full rounded-md border border-slate-800 bg-slate-950 px-3 py-1 text-xs text-white focus:outline-none focus:border-blue-500"
              >
                <option value="">Select driver</option>
                {drivers.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name} (Lic: {d.licenseNumber})
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-xs">Trip Date</Label>
                <Input
                  type="date"
                  value={scheduleDate}
                  onChange={(e) => setScheduleDate(e.target.value)}
                  className="mt-1"
                />
              </div>
              <div>
                <Label className="text-xs">Service Window</Label>
                <select
                  value={scheduleWindow}
                  onChange={(e) => setScheduleWindow(e.target.value)}
                  className="mt-1 flex h-9 w-full rounded-md border border-slate-800 bg-slate-950 px-3 py-1 text-xs text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="MORNING_PICKUP">Morning Pickup</option>
                  <option value="EVENING_RETURN">Evening Return</option>
                  <option value="SPECIAL_TRIP">Special Run</option>
                </select>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsScheduleOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleScheduleSubmit} className="bg-blue-600 hover:bg-blue-700">
              Confirm Schedule
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Pre-Trip Checklist & Dispatch Dialog */}
      <Dialog open={isDispatchOpen} onOpenChange={setIsDispatchOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Pre-Trip Safety Inspection & Dispatch</DialogTitle>
            <DialogDescription>
              Verify mandatory safety equipment and record vehicle starting odometer before authorization.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="bg-muted/40 p-3 rounded-lg text-xs space-y-1">
              <div>
                <span className="text-muted-foreground">Trip:</span> {activeTrip?.tripNumber}
              </div>
              <div>
                <span className="text-muted-foreground">Route:</span> {activeTrip?.routeName}
              </div>
              <div>
                <span className="text-muted-foreground">Vehicle:</span> {activeTrip?.vehicleRegistration}
              </div>
            </div>

            <div>
              <Label className="text-xs">Starting Odometer (km)</Label>
              <Input
                type="number"
                value={startOdometer}
                onChange={(e) => setStartOdometer(Number(e.target.value))}
                className="mt-1"
              />
            </div>

            <div className="space-y-2">
              <Label className="text-xs font-semibold">Mandatory Safety Checklist</Label>
              <div className="space-y-2 text-sm">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={brakesOk}
                    onChange={(e) => setBrakesOk(e.target.checked)}
                    className="rounded text-blue-600"
                  />
                  <span>Pneumatic Brakes & Pressure Gauge Normal</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={tiresOk}
                    onChange={(e) => setTiresOk(e.target.checked)}
                    className="rounded text-blue-600"
                  />
                  <span>Tires Pressure & Tread Condition Inspected</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={lightsOk}
                    onChange={(e) => setLightsOk(e.target.checked)}
                    className="rounded text-blue-600"
                  />
                  <span>Headlamps, Tail Indicators & Horn Operating</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={emergencyExitOk}
                    onChange={(e) => setEmergencyExitOk(e.target.checked)}
                    className="rounded text-blue-600"
                  />
                  <span>Emergency Exit Clear & Operational</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={firstAidKitOk}
                    onChange={(e) => setFirstAidKitOk(e.target.checked)}
                    className="rounded text-blue-600"
                  />
                  <span>First Aid Kit & Fire Extinguisher Present and Valid</span>
                </label>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDispatchOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleDispatchSubmit}
              disabled={!brakesOk || !tiresOk || !lightsOk || !emergencyExitOk || !firstAidKitOk}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              Authorize Dispatch
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Manifest & Boarding Drawer/Dialog */}
      <Dialog open={isManifestOpen} onOpenChange={setIsManifestOpen}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Passenger Manifest & Boarding Reconciliation</DialogTitle>
            <DialogDescription>
              Trip: {activeTrip?.tripNumber} | Passenger Count: {manifestData?.totalManifestCount}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 bg-muted/40 rounded-xl border text-center">
                <div className="text-xl font-bold text-foreground">{manifestData?.totalManifestCount}</div>
                <div className="text-xs text-muted-foreground">Expected</div>
              </div>
              <div className="p-3 bg-emerald-50 dark:bg-emerald-950/40 rounded-xl border border-emerald-200 dark:border-emerald-900 text-center">
                <div className="text-xl font-bold text-emerald-600">{manifestData?.boardedCount}</div>
                <div className="text-xs text-emerald-700 dark:text-emerald-300">Boarded</div>
              </div>
              <div className="p-3 bg-amber-50 dark:bg-amber-950/40 rounded-xl border border-amber-200 dark:border-amber-900 text-center">
                <div className="text-xl font-bold text-amber-600">{manifestData?.pendingCount}</div>
                <div className="text-xs text-amber-700 dark:text-amber-300">Pending</div>
              </div>
            </div>

            <div className="border rounded-xl divide-y">
              {manifestData?.passengers.map((p) => (
                <div key={p.id} className="p-3 flex items-center justify-between hover:bg-muted/30">
                  <div>
                    <div className="font-semibold text-sm">{p.studentName || "Aditya Varma"}</div>
                    <div className="text-xs text-muted-foreground">
                      Pass: {p.admissionNumber || "ADM-2026-001"} | Stop: {p.stopName || "Gandhipuram"}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge
                      className={
                        p.boardingStatus === "BOARDED"
                          ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                          : "bg-muted text-muted-foreground"
                      }
                    >
                      {p.boardingStatus}
                    </Badge>
                    {p.boardingStatus !== "BOARDED" && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => verifyPassenger(p.studentId, p.stopId)}
                        className="gap-1 h-7 text-xs"
                      >
                        <QrCode className="h-3 w-3" />
                        Verify
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <DialogFooter>
            <Button onClick={() => setIsManifestOpen(false)}>Close Manifest</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Complete Trip Dialog */}
      <Dialog open={isCompleteOpen} onOpenChange={setIsCompleteOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Complete Trip</DialogTitle>
            <DialogDescription>
              Record concluding odometer reading to close out operational run {activeTrip?.tripNumber}.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <Label className="text-xs">End Odometer (km)</Label>
              <Input
                type="number"
                value={endOdometer}
                onChange={(e) => setEndOdometer(Number(e.target.value))}
                className="mt-1"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Must be greater than start odometer ({activeTrip?.startOdometerKm || 50000} km).
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCompleteOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCompleteSubmit} className="bg-blue-600 hover:bg-blue-700">
              Confirm Trip Completion
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
