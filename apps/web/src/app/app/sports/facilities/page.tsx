"use client";

import React, { useState, useEffect } from "react";
import { sportsService } from "@/services/sports.service";
import { SportsFacilityItem } from "@/types/sports";
import { SportsNav } from "@/components/sports/sports-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import { SearchInput } from "@/components/ui/search-input";
import { useToast } from "@/components/ui/toast";
import {
  DoorOpen,
  PlusCircle,
  Wrench,
  CheckCircle,
  AlertTriangle,
  Clock,
  Layers,
  Users,
} from "lucide-react";

export default function SportsFacilitiesPage() {
  const { addToast } = useToast();
  const [facilities, setFacilities] = useState<SportsFacilityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedFacility, setSelectedFacility] = useState<SportsFacilityItem | null>(null);
  const [isMaintenanceOpen, setIsMaintenanceOpen] = useState(false);
  const [maintenanceNotes, setMaintenanceNotes] = useState("");

  const [formData, setFormData] = useState({
    code: "",
    name: "",
    facilityType: "BASKETBALL_COURT",
    surface: "WOOD",
    isIndoor: true,
    capacity: 200,
    maintenanceNotes: "",
  });

  useEffect(() => {
    loadFacilities();
  }, [typeFilter]);

  async function loadFacilities() {
    setLoading(true);
    const res = await sportsService.listFacilities("ALL", typeFilter);
    if (res.success && res.data) {
      setFacilities(res.data);
    }
    setLoading(false);
  }

  const filtered = facilities.filter((f) => {
    const matchesSearch =
      f.name.toLowerCase().includes(search.toLowerCase()) ||
      f.code.toLowerCase().includes(search.toLowerCase());
    return matchesSearch;
  });

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!formData.name || !formData.code) {
      addToast({ type: "error", title: "Validation Error", message: "Code and Name are required." });
      return;
    }

    const res = await sportsService.createFacility({
      code: formData.code.toUpperCase(),
      name: formData.name,
      facilityType: formData.facilityType as any,
      surface: formData.surface as any,
      isIndoor: formData.isIndoor,
      capacity: Number(formData.capacity) || 100,
      maintenanceNotes: formData.maintenanceNotes,
    });

    if (res.success) {
      addToast({ type: "success", title: "Created", message: `Facility "${formData.name}" registered.` });
      setIsCreateOpen(false);
      setFormData({
        code: "",
        name: "",
        facilityType: "BASKETBALL_COURT",
        surface: "WOOD",
        isIndoor: true,
        capacity: 200,
        maintenanceNotes: "",
      });
      loadFacilities();
    }
  }

  async function handleToggleMaintenance() {
    if (!selectedFacility) return;
    const isClosing = selectedFacility.status === "AVAILABLE";

    const res = await sportsService.setFacilityMaintenance(
      selectedFacility.id,
      isClosing,
      maintenanceNotes || (isClosing ? "Routine resurfacing and equipment check" : "Maintenance completed and approved")
    );

    if (res.success) {
      addToast({
        type: isClosing ? "warning" : "success",
        title: isClosing ? "Facility Closed" : "Facility Reopened",
        message: `${selectedFacility.name} is now ${isClosing ? "closed for maintenance" : "open and available for bookings"}.`,
      });
      setIsMaintenanceOpen(false);
      setSelectedFacility(null);
      setMaintenanceNotes("");
      loadFacilities();
    }
  }

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: "Dashboard", href: "/app/dashboard" },
          { label: "Sports & Athletics", href: "/app/sports" },
          { label: "Facilities & Courts", href: "/app/sports/facilities" },
        ]}
      />

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Sports Facilities & Courts Management
          </h1>
          <p className="text-xs sm:text-sm text-slate-400">
            Indoor stadiums, outdoor pitches, courts, pools, gymnasiums, and maintenance state control.
          </p>
        </div>

        <Button
          size="sm"
          className="gap-1.5 text-xs bg-indigo-600 hover:bg-indigo-500"
          onClick={() => setIsCreateOpen(true)}
        >
          <PlusCircle className="h-3.5 w-3.5" />
          Register Facility
        </Button>
      </div>

      <SportsNav />

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="w-full sm:w-72">
          <SearchInput
            placeholder="Search venue or code..."
            value={search}
            onChange={(val) => setSearch(val)}
          />
        </div>
        <div className="w-full sm:w-56">
          <Select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            options={[
              { value: "ALL", label: "All Facility Types" },
              { value: "FOOTBALL_FIELD", label: "Football Fields" },
              { value: "CRICKET_GROUND", label: "Cricket Grounds" },
              { value: "BASKETBALL_COURT", label: "Basketball Courts" },
              { value: "BADMINTON_COURT", label: "Badminton Courts" },
              { value: "SWIMMING_POOL", label: "Swimming Pools" },
              { value: "GYMNASIUM", label: "Gymnasiums" },
              { value: "TENNIS_COURT", label: "Tennis Courts" },
              { value: "ATHLETIC_TRACK", label: "Athletic Tracks" },
            ]}
          />
        </div>
      </div>

      {/* Facilities Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((facility) => {
          const isClosed = facility.status === "MAINTENANCE_CLOSED";

          return (
            <Card
              key={facility.id}
              className={`p-5 border-slate-800 bg-slate-900/40 hover:border-slate-700 transition-all flex flex-col justify-between ${
                isClosed ? "border-amber-500/40 bg-amber-950/10" : ""
              }`}
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <span className="font-mono text-xs font-bold text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-2 py-0.5 rounded">
                    {facility.code}
                  </span>
                  <Badge variant={isClosed ? "warning" : "success"}>
                    {facility.status}
                  </Badge>
                </div>

                <h3 className="text-base font-bold text-white mb-1">{facility.name}</h3>
                <div className="flex items-center gap-2 text-xs text-slate-400 mb-3">
                  <span className="capitalize">{facility.facilityType.toLowerCase().replace("_", " ")}</span>
                  <span>&bull;</span>
                  <span className="font-medium text-slate-300">{facility.surface} Surface</span>
                  <span>&bull;</span>
                  <span>{facility.isIndoor ? "Indoor" : "Outdoor"}</span>
                </div>

                {isClosed && (
                  <div className="mb-3 rounded-lg border border-amber-500/30 bg-amber-950/30 p-2.5 text-xs text-amber-200 flex items-start gap-2">
                    <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold">Closure Alert:</span>{" "}
                      {facility.maintenanceNotes || "Under maintenance"}
                    </div>
                  </div>
                )}

                <div className="space-y-1.5 text-xs text-slate-300 border-t border-slate-800/80 pt-3">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400 flex items-center gap-1.5">
                      <Users className="h-3.5 w-3.5 text-slate-500" /> Max Capacity:
                    </span>
                    <span className="font-semibold text-white">{facility.capacity} persons</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400 flex items-center gap-1.5">
                      <Clock className="h-3.5 w-3.5 text-slate-500" /> Operating Window:
                    </span>
                    <span className="font-mono text-slate-300">
                      {facility.operatingHours?.open || "06:00"} - {facility.operatingHours?.close || "20:00"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Maintenance Toggle Action */}
              <div className="mt-5 pt-3 border-t border-slate-800 flex items-center justify-between">
                <span className="text-[11px] text-slate-500 font-mono">
                  Asset ID: {facility.equipmentAssetIds?.[0] || "ASSET-LINKED"}
                </span>

                <Button
                  size="sm"
                  variant={isClosed ? "outline" : "outline"}
                  className={`text-xs gap-1.5 ${
                    isClosed
                      ? "border-emerald-500/40 text-emerald-400 hover:bg-emerald-950/20"
                      : "border-amber-500/40 text-amber-400 hover:bg-amber-950/20"
                  }`}
                  onClick={() => {
                    setSelectedFacility(facility);
                    setIsMaintenanceOpen(true);
                  }}
                >
                  <Wrench className="h-3.5 w-3.5" />
                  {isClosed ? "Reopen Facility" : "Close for Maintenance"}
                </Button>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Maintenance State Dialog */}
      <Dialog open={isMaintenanceOpen} onOpenChange={setIsMaintenanceOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Wrench className="h-5 w-5 text-amber-400" />
              {selectedFacility?.status === "AVAILABLE"
                ? `Initiate Maintenance Closure: ${selectedFacility?.name}`
                : `Authorize Reopening: ${selectedFacility?.name}`}
            </DialogTitle>
          </DialogHeader>

          <div className="py-2 space-y-3">
            <p className="text-xs text-slate-400">
              {selectedFacility?.status === "AVAILABLE"
                ? "Closing this facility will immediately block all new training and match reservations. Existing reservations will flag a conflict alert."
                : "Reopening this facility confirms all required repairs, surface inspections, and health clearances are completed."}
            </p>

            <div>
              <Label htmlFor="maintNotes" className="text-xs">
                {selectedFacility?.status === "AVAILABLE" ? "Closure Reason / Work Order Ref *" : "Inspection & Clearance Notes *"}
              </Label>
              <Textarea
                id="maintNotes"
                placeholder={
                  selectedFacility?.status === "AVAILABLE"
                    ? "e.g. Surface crack repair and hoop replacement per WO-2026-901"
                    : "e.g. Surface resurfacing inspected and certified safe by estate division"
                }
                value={maintenanceNotes}
                onChange={(e) => setMaintenanceNotes(e.target.value)}
                className="text-xs mt-1"
                rows={3}
                required
              />
            </div>
          </div>

          <DialogFooter className="pt-2">
            <Button variant="outline" size="sm" onClick={() => setIsMaintenanceOpen(false)}>
              Cancel
            </Button>
            <Button
              size="sm"
              className={
                selectedFacility?.status === "AVAILABLE"
                  ? "bg-amber-600 hover:bg-amber-500 text-white"
                  : "bg-emerald-600 hover:bg-emerald-500 text-white"
              }
              onClick={handleToggleMaintenance}
            >
              {selectedFacility?.status === "AVAILABLE" ? "Confirm Closure" : "Confirm Reopening"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Facility Dialog */}
      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <DoorOpen className="h-5 w-5 text-indigo-400" />
              Register Sports Facility / Court
            </DialogTitle>
          </DialogHeader>

          <form onSubmit={handleCreate} className="space-y-4 py-2">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="facCode" className="text-xs">Facility Code *</Label>
                <Input
                  id="facCode"
                  placeholder="e.g. FAC-VOLL-02"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  className="font-mono uppercase text-xs mt-1"
                  required
                />
              </div>
              <div>
                <Label htmlFor="facType" className="text-xs">Venue Type *</Label>
                <Select
                  id="facType"
                  value={formData.facilityType}
                  onChange={(e) => setFormData({ ...formData, facilityType: e.target.value })}
                  options={[
                    { value: "BASKETBALL_COURT", label: "Basketball Court" },
                    { value: "FOOTBALL_FIELD", label: "Football Field" },
                    { value: "CRICKET_GROUND", label: "Cricket Ground" },
                    { value: "BADMINTON_COURT", label: "Badminton Court" },
                    { value: "SWIMMING_POOL", label: "Swimming Pool" },
                    { value: "GYMNASIUM", label: "Gymnasium" },
                    { value: "TENNIS_COURT", label: "Tennis Court" },
                    { value: "ATHLETIC_TRACK", label: "Athletic Track" },
                  ]}
                  className="text-xs mt-1"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="facName" className="text-xs">Facility / Court Name *</Label>
              <Input
                id="facName"
                placeholder="e.g. South Pavilion Badminton Court"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="text-xs mt-1"
                required
              />
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <Label htmlFor="surface" className="text-xs">Surface</Label>
                <Select
                  id="surface"
                  value={formData.surface}
                  onChange={(e) => setFormData({ ...formData, surface: e.target.value })}
                  options={[
                    { value: "WOOD", label: "Wood / Maple" },
                    { value: "SYNTHETIC", label: "Synthetic" },
                    { value: "TURF", label: "Turf" },
                    { value: "GRASS", label: "Grass" },
                    { value: "CLAY", label: "Clay" },
                    { value: "WATER", label: "Water" },
                  ]}
                  className="text-xs mt-1"
                />
              </div>
              <div>
                <Label htmlFor="capacity" className="text-xs">Max Capacity</Label>
                <Input
                  id="capacity"
                  type="number"
                  value={formData.capacity}
                  onChange={(e) => setFormData({ ...formData, capacity: Number(e.target.value) })}
                  className="text-xs mt-1 font-mono"
                />
              </div>
              <div>
                <Label htmlFor="isIndoor" className="text-xs">Setting</Label>
                <Select
                  id="isIndoor"
                  value={formData.isIndoor ? "indoor" : "outdoor"}
                  onChange={(e) => setFormData({ ...formData, isIndoor: e.target.value === "indoor" })}
                  options={[
                    { value: "indoor", label: "Indoor Hall" },
                    { value: "outdoor", label: "Outdoor Pitch" },
                  ]}
                  className="text-xs mt-1"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="notes" className="text-xs">Initial Condition & Safety Notes</Label>
              <Textarea
                id="notes"
                placeholder="Surface inspection remarks, equipment anchors..."
                value={formData.maintenanceNotes}
                onChange={(e) => setFormData({ ...formData, maintenanceNotes: e.target.value })}
                className="text-xs mt-1"
                rows={2}
              />
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" size="sm" onClick={() => setIsCreateOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" size="sm" className="bg-indigo-600 hover:bg-indigo-500">
                Register Venue
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
