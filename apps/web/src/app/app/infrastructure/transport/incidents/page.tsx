"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  transportService,
  TransportIncidentItem,
  transportVehiclesService,
  transportRoutesService,
} from "@/services/transport.service";
import { TransportVehicle, TransportRoute } from "@campusos/types";
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
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Plus,
  RefreshCw,
  ArrowLeft,
  FileText,
  Bus,
  Compass,
  MapPin,
  PhoneCall,
  Flame,
  CheckCircle,
} from "lucide-react";

export default function TransportIncidentsPage() {
  const [loading, setLoading] = useState(true);
  const [incidents, setIncidents] = useState<TransportIncidentItem[]>([]);
  const [vehicles, setVehicles] = useState<TransportVehicle[]>([]);
  const [routes, setRoutes] = useState<TransportRoute[]>([]);
  const [severityFilter, setSeverityFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [refreshing, setRefreshing] = useState(false);

  // Report Dialog State
  const [reportDialogOpen, setReportDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [selectedVehicleId, setSelectedVehicleId] = useState("");
  const [selectedRouteId, setSelectedRouteId] = useState("");
  const [incidentType, setIncidentType] = useState("BREAKDOWN");
  const [severity, setSeverity] = useState("MEDIUM");
  const [locationDescription, setLocationDescription] = useState("");
  const [description, setDescription] = useState("");
  const [emergencyServicesContacted, setEmergencyServicesContacted] = useState(false);

  // Resolve Dialog State
  const [resolveDialogOpen, setResolveDialogOpen] = useState(false);
  const [resolvingIncident, setResolvingIncident] = useState<TransportIncidentItem | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState("");
  const [actionTaken, setActionTaken] = useState("");
  const [resolving, setResolving] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [incRes, vRes, rRes] = await Promise.all([
        transportService.listIncidents({
          severity: severityFilter !== "ALL" ? severityFilter : undefined,
          status: statusFilter !== "ALL" ? statusFilter : undefined,
        }),
        transportVehiclesService.listVehicles(),
        transportRoutesService.listRoutes(),
      ]);

      if (incRes.success && incRes.data) {
        setIncidents(incRes.data);
      }
      if (vRes.data) setVehicles(vRes.data);
      if (rRes.data) setRoutes(rRes.data);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [severityFilter, statusFilter]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
  };

  const handleOpenReport = () => {
    setSelectedVehicleId(vehicles[0]?.id || "");
    setSelectedRouteId(routes[0]?.id || "");
    setIncidentType("BREAKDOWN");
    setSeverity("MEDIUM");
    setLocationDescription("");
    setDescription("");
    setEmergencyServicesContacted(false);
    setReportDialogOpen(true);
  };

  const handleSubmitReport = async () => {
    if (!description.trim() || !locationDescription.trim()) return;
    setSubmitting(true);
    try {
      const res = await transportService.reportIncident({
        vehicleId: selectedVehicleId || undefined,
        routeId: selectedRouteId || undefined,
        incidentType,
        severity,
        locationDescription,
        description,
        emergencyServicesContacted,
      });

      if (res.success) {
        setReportDialogOpen(false);
        await loadData();
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleOpenResolve = (item: TransportIncidentItem) => {
    setResolvingIncident(item);
    setResolutionNotes("");
    setActionTaken("");
    setResolveDialogOpen(true);
  };

  const handleSubmitResolve = async () => {
    if (!resolvingIncident || !resolutionNotes.trim()) return;
    setResolving(true);
    try {
      const res = await transportService.resolveIncident(
        resolvingIncident.id,
        resolutionNotes,
        actionTaken || undefined
      );
      if (res.success) {
        setResolveDialogOpen(false);
        await loadData();
      }
    } finally {
      setResolving(false);
    }
  };

  const criticalCount = incidents.filter((i) => i.severity === "CRITICAL").length;
  const activeCount = incidents.filter(
    (i) => i.status === "REPORTED" || i.status === "UNDER_INVESTIGATION"
  ).length;
  const resolvedCount = incidents.filter((i) => i.status === "RESOLVED" || i.status === "CLOSED").length;

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-slate-400">
        <Link
          href="/app/infrastructure/transport"
          className="hover:text-blue-400 flex items-center gap-1"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Transport Management
        </Link>
        <span>/</span>
        <span className="text-white">Safety, Incidents & Breakdown Logs</span>
      </div>

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold text-rose-400 uppercase tracking-wider flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5" />
              Operational Safety Protocol
            </span>
          </div>
          <h1 className="text-2xl lg:text-3xl font-bold text-white tracking-tight">
            Transport Incidents & Emergency Logging
          </h1>
          <p className="text-slate-400 text-sm mt-1 max-w-3xl">
            Controlled logging for transit breakdowns, safety occurrences, service disruptions, and emergency response. All entries are tenant-isolated and audit-preserved.
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
            Refresh
          </Button>
          <Button
            size="sm"
            onClick={handleOpenReport}
            className="bg-rose-600 hover:bg-rose-500 text-white gap-2"
          >
            <Plus className="w-4 h-4" />
            Report Safety Incident
          </Button>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-xs text-slate-400 font-medium">Total Logged Events</div>
          <div className="text-2xl font-bold text-white mt-1">{incidents.length}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Historical and active entries</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-amber-500/30 bg-amber-500/5">
          <div className="text-xs text-amber-400 font-medium flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" />
            Active / Investigating
          </div>
          <div className="text-2xl font-bold text-amber-400 mt-1">{activeCount}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Pending response or repair</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-rose-500/30 bg-rose-500/5">
          <div className="text-xs text-rose-400 font-medium flex items-center gap-1.5">
            <Flame className="w-3.5 h-3.5" />
            Critical Severity
          </div>
          <div className="text-2xl font-bold text-rose-400 mt-1">{criticalCount}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Immediate escalation required</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-emerald-500/30 bg-emerald-500/5">
          <div className="text-xs text-emerald-400 font-medium flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Resolved & Closed
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{resolvedCount}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Signed off with post-review</div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-slate-900/40 border border-slate-800">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Severity:</span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1 text-xs text-white focus:outline-none focus:border-blue-500"
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1 text-xs text-white focus:outline-none focus:border-blue-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="REPORTED">Reported</option>
              <option value="UNDER_INVESTIGATION">Under Investigation</option>
              <option value="RESOLVED">Resolved</option>
              <option value="CLOSED">Closed</option>
            </select>
          </div>
        </div>

        <span className="text-xs text-slate-500 font-mono">
          Showing {incidents.length} record(s)
        </span>
      </div>

      {/* Incidents Table / List */}
      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full rounded-xl" />
          ))}
        </div>
      ) : incidents.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800 space-y-3">
          <ShieldCheck className="w-10 h-10 text-emerald-500 mx-auto" />
          <h3 className="text-base font-semibold text-white">No Incidents Reported</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            All transit corridors and fleet vehicles are operating safely under current filter parameters.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {incidents.map((item) => {
            const isCritical = item.severity === "CRITICAL";
            const isHigh = item.severity === "HIGH";
            const isResolved = item.status === "RESOLVED" || item.status === "CLOSED";

            const vMatch = vehicles.find((v) => v.id === item.vehicleId);
            const rMatch = routes.find((r) => r.id === item.routeId);

            return (
              <div
                key={item.id}
                className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs font-bold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
                      {item.incidentNumber}
                    </span>
                    <span className="text-sm font-semibold text-white">
                      {item.incidentType.replace(/_/g, " ")}
                    </span>
                    <Badge
                      variant="outline"
                      className={
                        isCritical
                          ? "bg-rose-500/20 text-rose-300 border-rose-500/40"
                          : isHigh
                          ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                          : "bg-blue-500/10 text-blue-400 border-blue-500/20"
                      }
                    >
                      {item.severity}
                    </Badge>
                  </div>

                  <div className="flex items-center gap-3">
                    <Badge
                      variant="outline"
                      className={
                        isResolved
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                          : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                      }
                    >
                      {item.status}
                    </Badge>

                    {!isResolved && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleOpenResolve(item)}
                        className="border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/10 text-xs h-7 gap-1"
                      >
                        <CheckCircle className="w-3.5 h-3.5" />
                        Resolve Incident
                      </Button>
                    )}
                  </div>
                </div>

                {/* Details & Location */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs pt-1">
                  <div className="flex items-center gap-2 text-slate-300">
                    <MapPin className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                    <span>Location: <strong className="text-white">{item.locationDescription}</strong></span>
                  </div>

                  <div className="flex items-center gap-2 text-slate-300">
                    <Bus className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    <span>Vehicle: <strong className="text-white">{vMatch?.registrationNumber || item.vehicleId || "N/A"}</strong></span>
                  </div>

                  <div className="flex items-center gap-2 text-slate-300">
                    <Compass className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                    <span>Route: <strong className="text-white">{rMatch?.name || item.routeId || "Transit Fleet"}</strong></span>
                  </div>
                </div>

                {/* Description */}
                <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs text-slate-300 leading-relaxed">
                  {item.description}
                </div>

                {/* Resolution Notes (if any) */}
                {item.resolutionNotes && (
                  <div className="p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/20 text-xs text-emerald-300 space-y-1">
                    <div className="font-semibold flex items-center gap-1.5 text-emerald-400">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Incident Resolution Notes:
                    </div>
                    <p className="text-slate-300">{item.resolutionNotes}</p>
                    {item.actionTaken && (
                      <p className="text-[11px] text-slate-400">Action: {item.actionTaken}</p>
                    )}
                  </div>
                )}

                <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                  <span>Reported at: {new Date(item.incidentTime).toLocaleString("en-IN")}</span>
                  {item.resolvedAt && (
                    <span>Resolved at: {new Date(item.resolvedAt).toLocaleString("en-IN")}</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Report Incident Dialog */}
      <Dialog open={reportDialogOpen} onOpenChange={setReportDialogOpen}>
        <DialogContent className="sm:max-w-lg bg-slate-900 border-slate-800 text-white">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-white">
              <ShieldAlert className="w-5 h-5 text-rose-400" />
              Log Safety Incident or Breakdown
            </DialogTitle>
            <DialogDescription className="text-slate-400 text-xs">
              Record a service disruption, mechanical breakdown, or passenger safety occurrence.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2 text-xs">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs text-slate-300">Incident Category</Label>
                <select
                  value={incidentType}
                  onChange={(e) => setIncidentType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="BREAKDOWN">Mechanical Breakdown</option>
                  <option value="ACCIDENT_MINOR">Minor Traffic Impact</option>
                  <option value="ACCIDENT_MAJOR">Major Collision</option>
                  <option value="MEDICAL_EMERGENCY">Student Medical Event</option>
                  <option value="ROUTE_DISRUPTION">Road Closure / Blockade</option>
                  <option value="PASSENGER_MISCONDUCT">Safety Rule Violation</option>
                </select>
              </div>

              <div className="space-y-1">
                <Label className="text-xs text-slate-300">Severity Level</Label>
                <select
                  value={severity}
                  onChange={(e) => setSeverity(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="LOW">Low (Minor Delay)</option>
                  <option value="MEDIUM">Medium (Replacement Needed)</option>
                  <option value="HIGH">High (Immediate Dispatch Intervention)</option>
                  <option value="CRITICAL">Critical (Emergency Services Active)</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs text-slate-300">Involved Vehicle</Label>
                <select
                  value={selectedVehicleId}
                  onChange={(e) => setSelectedVehicleId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="">No Vehicle Assigned</option>
                  {vehicles.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.registrationNumber} ({v.make} {v.model})
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <Label className="text-xs text-slate-300">Impacted Route</Label>
                <select
                  value={selectedRouteId}
                  onChange={(e) => setSelectedRouteId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="">Campus Fleet / General</option>
                  {routes.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.routeCode} - {r.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="space-y-1">
              <Label className="text-xs text-slate-300">Location Description</Label>
              <Input
                value={locationDescription}
                onChange={(e) => setLocationDescription(e.target.value)}
                placeholder="e.g. Ring Road Junction, near Metro Pillar 142"
                className="bg-slate-950 border-slate-800 text-xs text-white"
              />
            </div>

            <div className="space-y-1">
              <Label className="text-xs text-slate-300">Incident Details & Symptoms</Label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe what occurred, vehicle behavior, driver actions, or passenger safety status..."
                rows={3}
                className="w-full bg-slate-950 border border-slate-800 rounded-md p-2.5 text-xs text-white focus:outline-none focus:border-blue-500"
              />
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950 border border-slate-800">
              <div className="space-y-0.5">
                <div className="text-xs font-medium text-white flex items-center gap-1.5">
                  <PhoneCall className="w-3.5 h-3.5 text-rose-400" />
                  Emergency Services Contacted
                </div>
                <div className="text-[11px] text-slate-400">
                  Check if 112 / ambulance / traffic police was notified.
                </div>
              </div>
              <input
                type="checkbox"
                checked={emergencyServicesContacted}
                onChange={(e) => setEmergencyServicesContacted(e.target.checked)}
                className="w-4 h-4 rounded border-slate-800 text-rose-600 focus:ring-0 bg-slate-900"
              />
            </div>
          </div>

          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setReportDialogOpen(false)}
              className="border-slate-800 text-slate-400 hover:text-white"
            >
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={handleSubmitReport}
              disabled={submitting || !description.trim() || !locationDescription.trim()}
              className="bg-rose-600 hover:bg-rose-500 text-white gap-2"
            >
              <CheckCircle2 className="w-4 h-4" />
              {submitting ? "Logging..." : "Submit Incident Report"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Resolve Incident Dialog */}
      <Dialog open={resolveDialogOpen} onOpenChange={setResolveDialogOpen}>
        <DialogContent className="sm:max-w-md bg-slate-900 border-slate-800 text-white">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-white">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              Resolve Transport Incident
            </DialogTitle>
            <DialogDescription className="text-slate-400 text-xs">
              Record closure notes and actions taken for event{" "}
              <strong className="text-white">{resolvingIncident?.incidentNumber}</strong>.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2 text-xs">
            <div className="space-y-1">
              <Label className="text-xs text-slate-300">Action Taken</Label>
              <Input
                value={actionTaken}
                onChange={(e) => setActionTaken(e.target.value)}
                placeholder="e.g. Substitute bus deployed; mechanic cleared brake sensor."
                className="bg-slate-950 border-slate-800 text-xs text-white"
              />
            </div>

            <div className="space-y-1">
              <Label className="text-xs text-slate-300">Resolution & Sign-off Notes</Label>
              <textarea
                value={resolutionNotes}
                onChange={(e) => setResolutionNotes(e.target.value)}
                placeholder="Document cause of incident, student safety confirmation, and post-service inspection outcome..."
                rows={4}
                className="w-full bg-slate-950 border border-slate-800 rounded-md p-2.5 text-xs text-white focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setResolveDialogOpen(false)}
              className="border-slate-800 text-slate-400 hover:text-white"
            >
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={handleSubmitResolve}
              disabled={resolving || !resolutionNotes.trim()}
              className="bg-emerald-600 hover:bg-emerald-500 text-white gap-2"
            >
              <CheckCircle2 className="w-4 h-4" />
              {resolving ? "Resolving..." : "Mark as Resolved"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
