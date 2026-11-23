"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import Link from "next/link";
import { facilitiesService } from "@/services/facilities.service";
import { Facility, FacilityType, FacilityStatus } from "@campusos/types";
import { useAuth } from "@/lib/auth-context";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/toast";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Building2,
  Search,
  Filter,
  Plus,
  Users,
  Wrench,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Layers,
  MapPin,
  Calendar,
  Phone,
  Mail,
  SlidersHorizontal,
  Sparkles,
  ExternalLink,
} from "lucide-react";

export default function FacilitiesManagementPage() {
  const { user } = useAuth();
  const { toast } = useToast();

  const [loading, setLoading] = useState(true);
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedType, setSelectedType] = useState<string>("ALL");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [selectedFacility, setSelectedFacility] = useState<Facility | null>(
    null,
  );

  // Create Facility Modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    code: "",
    building: "Academic Block A",
    floor: "1",
    type: FacilityType.LABORATORY,
    capacity: 60,
    managerName: "",
    managerEmail: "",
    managerPhone: "",
    description: "",
  });

  const loadFacilities = useCallback(async () => {
    setLoading(true);
    try {
      const res = await facilitiesService.listFacilities({
        type: selectedType !== "ALL" ? selectedType : undefined,
        status: selectedStatus !== "ALL" ? selectedStatus : undefined,
        search: searchQuery || undefined,
      });
      if (res.success && res.data) {
        setFacilities(res.data);
      }
    } catch {
      toast({
        title: "Error",
        description: "Failed to load facilities directory.",
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  }, [selectedType, selectedStatus, searchQuery, toast]);

  useEffect(() => {
    loadFacilities();
  }, [loadFacilities]);

  const handleCreateFacility = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.code.trim()) {
      toast({
        title: "Validation Error",
        description: "Please enter facility name and code.",
        variant: "error",
      });
      return;
    }

    setSubmitting(true);
    try {
      const res = await facilitiesService.createFacility({
        ...formData,
        campusId: "cmp-main-01",
        campusName: "Main Engineering Campus",
        status: FacilityStatus.ACTIVE,
        connectedEventsCount: 0,
        activeWorkOrdersCount: 0,
        equipment: [],
      });

      if (res.success) {
        toast({
          title: "Facility Created",
          description: `${formData.name} successfully chartered into registry.`,
          variant: "success",
        });
        setCreateModalOpen(false);
        setFormData({
          name: "",
          code: "",
          building: "Academic Block A",
          floor: "1",
          type: FacilityType.LABORATORY,
          capacity: 60,
          managerName: "",
          managerEmail: "",
          managerPhone: "",
          description: "",
        });
        loadFacilities();
      }
    } finally {
      setSubmitting(false);
    }
  };

  const stats = useMemo(() => {
    const total = facilities.length;
    const active = facilities.filter(
      (f) => f.status === FacilityStatus.ACTIVE,
    ).length;
    const maintenance = facilities.filter(
      (f) => f.status === FacilityStatus.UNDER_MAINTENANCE,
    ).length;
    const totalCapacity = facilities.reduce(
      (acc, f) => acc + (f.capacity || 0),
      0,
    );
    const activeOrders = facilities.reduce(
      (acc, f) => acc + (f.activeWorkOrdersCount || 0),
      0,
    );

    return { total, active, maintenance, totalCapacity, activeOrders };
  }, [facilities]);

  const getStatusBadge = (status: FacilityStatus) => {
    switch (status) {
      case FacilityStatus.ACTIVE:
        return <Badge variant="success">Operational</Badge>;
      case FacilityStatus.UNDER_MAINTENANCE:
        return <Badge variant="warning">Maintenance</Badge>;
      case FacilityStatus.RESERVED:
        return <Badge variant="info">Reserved</Badge>;
      case FacilityStatus.INACTIVE:
      default:
        return <Badge variant="neutral">Offline</Badge>;
    }
  };

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Link
              href="/app/infrastructure"
              className="text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors"
            >
              Infrastructure
            </Link>
            <span className="text-xs text-slate-600">/</span>
            <span className="text-xs text-indigo-400 font-medium">
              Facilities & Venues
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2 mt-1">
            <Building2 className="h-6 w-6 text-indigo-400" />
            Campus Facilities & Venue Operations
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Central registry of auditoriums, high-performance computing labs,
            seminar halls, sports complexes, and institutional facilities.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link href="/app/infrastructure/maintenance">
            <Button variant="outline" size="sm" className="gap-2">
              <Wrench className="h-4 w-4" />
              Work Orders
            </Button>
          </Link>
          <Button
            size="sm"
            onClick={() => setCreateModalOpen(true)}
            className="gap-2 bg-indigo-600 hover:bg-indigo-500 text-white"
          >
            <Plus className="h-4 w-4" />
            Register Facility
          </Button>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Facilities"
          value={stats.total.toString()}
          description="Auditoriums, Labs & Centers"
          icon={<Building2 className="h-5 w-5 text-indigo-400" />}
          change={{ value: "+12%", trend: "up" }}
        />
        <StatCard
          title="Active & Ready"
          value={stats.active.toString()}
          description={`${Math.round((stats.active / Math.max(1, stats.total)) * 100)}% Operational Readiness`}
          icon={<CheckCircle2 className="h-5 w-5 text-emerald-400" />}
        />
        <StatCard
          title="Total Aggregate Capacity"
          value={stats.totalCapacity.toLocaleString()}
          description="Simultaneous Seating Footprint"
          icon={<Users className="h-5 w-5 text-purple-400" />}
        />
        <StatCard
          title="Active Work Orders"
          value={stats.activeOrders.toString()}
          description={
            stats.maintenance > 0
              ? `${stats.maintenance} facilities undergoing repair`
              : "Optimal condition"
          }
          icon={<Wrench className="h-5 w-5 text-amber-400" />}
        />
      </div>

      {/* Search & Filters */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row gap-4 justify-between items-center backdrop-blur-sm">
        <div className="relative w-full md:w-96">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by facility name, code, manager, building..."
            className="pl-9 bg-slate-950/70 border-slate-800 text-white w-full"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-slate-400" />
            <span className="text-xs text-slate-400 font-medium">Type:</span>
            <Select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="bg-slate-950 border-slate-800 text-xs text-white h-9"
            >
              <option value="ALL">All Facility Types</option>
              <option value={FacilityType.AUDITORIUM}>Auditorium</option>
              <option value={FacilityType.LABORATORY}>Laboratory</option>
              <option value={FacilityType.SEMINAR_HALL}>Seminar Hall</option>
              <option value={FacilityType.SPORTS_COMPLEX}>
                Sports Complex
              </option>
              <option value={FacilityType.LIBRARY}>Library</option>
              <option value={FacilityType.CAFETERIA}>Cafeteria</option>
              <option value={FacilityType.CLASSROOM_BLOCK}>
                Classroom Block
              </option>
              <option value={FacilityType.ADMINISTRATIVE}>
                Administrative
              </option>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Status:</span>
            <Select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-slate-950 border-slate-800 text-xs text-white h-9"
            >
              <option value="ALL">All Statuses</option>
              <option value={FacilityStatus.ACTIVE}>Operational</option>
              <option value={FacilityStatus.UNDER_MAINTENANCE}>
                Under Maintenance
              </option>
              <option value={FacilityStatus.RESERVED}>Reserved</option>
              <option value={FacilityStatus.INACTIVE}>Offline</option>
            </Select>
          </div>
        </div>
      </div>

      {/* Facilities Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4"
            >
              <Skeleton className="h-6 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
              <Skeleton className="h-20 w-full" />
              <div className="flex justify-between">
                <Skeleton className="h-8 w-24" />
                <Skeleton className="h-8 w-24" />
              </div>
            </div>
          ))}
        </div>
      ) : facilities.length === 0 ? (
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-12 text-center space-y-3">
          <Building2 className="h-12 w-12 text-slate-600 mx-auto" />
          <h3 className="text-base font-semibold text-white">
            No Facilities Found
          </h3>
          <p className="text-sm text-slate-400 max-w-md mx-auto">
            No campus facilities matched your search criteria. Try modifying
            your filters or register a new facility.
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setSearchQuery("");
              setSelectedType("ALL");
              setSelectedStatus("ALL");
            }}
          >
            Clear Filters
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {facilities.map((facility) => (
            <div
              key={facility.id}
              className="bg-slate-900/70 border border-slate-800 hover:border-indigo-500/50 rounded-xl p-5 space-y-4 transition-all duration-200 flex flex-col justify-between group shadow-sm hover:shadow-indigo-500/5"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-1">
                    <span className="text-[10px] font-mono font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                      {facility.code}
                    </span>
                    <h3 className="text-base font-bold text-white group-hover:text-indigo-300 transition-colors line-clamp-1 mt-1">
                      {facility.name}
                    </h3>
                  </div>
                  {getStatusBadge(facility.status)}
                </div>

                <p className="text-xs text-slate-400 mt-2 line-clamp-2 min-h-[32px]">
                  {facility.description ||
                    "State-of-the-art academic and institutional campus infrastructure facility."}
                </p>

                <div className="mt-4 pt-4 border-t border-slate-800/80 space-y-2.5 text-xs">
                  <div className="flex items-center justify-between text-slate-300">
                    <span className="text-slate-500 flex items-center gap-1.5">
                      <MapPin className="h-3.5 w-3.5 text-slate-400" /> Location
                    </span>
                    <span className="font-medium text-white truncate max-w-[180px]">
                      {facility.building} (Fl. {facility.floor})
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-slate-300">
                    <span className="text-slate-500 flex items-center gap-1.5">
                      <Users className="h-3.5 w-3.5 text-slate-400" /> Seating
                      Capacity
                    </span>
                    <span className="font-mono font-semibold text-emerald-400">
                      {facility.capacity.toLocaleString()} seats
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-slate-300">
                    <span className="text-slate-500 flex items-center gap-1.5">
                      <Calendar className="h-3.5 w-3.5 text-slate-400" />{" "}
                      Connected Events
                    </span>
                    <span className="font-mono text-slate-300">
                      {facility.connectedEventsCount || 0} scheduled
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-slate-300">
                    <span className="text-slate-500 flex items-center gap-1.5">
                      <Wrench className="h-3.5 w-3.5 text-slate-400" /> Active
                      Work Orders
                    </span>
                    <span
                      className={`font-mono font-semibold ${
                        (facility.activeWorkOrdersCount || 0) > 0
                          ? "text-amber-400"
                          : "text-slate-500"
                      }`}
                    >
                      {facility.activeWorkOrdersCount || 0} open
                    </span>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-800 flex items-center justify-between gap-2">
                <div className="text-[11px] text-slate-400 truncate">
                  <span className="text-slate-500">Manager:</span>{" "}
                  {facility.managerName}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedFacility(facility)}
                  className="text-xs h-8"
                >
                  View Specs
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Facility Details Modal */}
      {selectedFacility && (
        <Dialog
          open={!!selectedFacility}
          onClose={() => setSelectedFacility(null)}
          title={selectedFacility.name}
          className="max-w-2xl"
        >
          <div className="space-y-5 text-sm">
            <div className="flex items-center justify-between bg-slate-950 p-3 rounded-lg border border-slate-800">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                  {selectedFacility.code}
                </span>
                <span className="text-xs text-slate-400">
                  • {selectedFacility.type}
                </span>
              </div>
              {getStatusBadge(selectedFacility.status)}
            </div>

            <div>
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">
                Overview
              </h4>
              <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                {selectedFacility.description}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-950/50 p-3 rounded-lg border border-slate-800 space-y-1">
                <span className="text-xs text-slate-500">Building & Floor</span>
                <p className="font-semibold text-white">
                  {selectedFacility.building}, Floor {selectedFacility.floor}
                </p>
                <span className="text-[11px] text-slate-400">
                  {selectedFacility.campusName}
                </span>
              </div>

              <div className="bg-slate-950/50 p-3 rounded-lg border border-slate-800 space-y-1">
                <span className="text-xs text-slate-500">
                  Seating & Occupancy
                </span>
                <p className="font-semibold text-emerald-400 font-mono text-base">
                  {selectedFacility.capacity.toLocaleString()} Max Capacity
                </p>
                <span className="text-[11px] text-slate-400">
                  Institutional Fire Safety Approved
                </span>
              </div>
            </div>

            <div>
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                Facility Officer & In-Charge
              </h4>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 flex items-center justify-between">
                <div>
                  <p className="font-semibold text-white">
                    {selectedFacility.managerName}
                  </p>
                  <div className="flex items-center gap-4 text-xs text-slate-400 mt-1">
                    <span className="flex items-center gap-1">
                      <Mail className="h-3 w-3 text-slate-500" />{" "}
                      {selectedFacility.managerEmail}
                    </span>
                    <span className="flex items-center gap-1">
                      <Phone className="h-3 w-3 text-slate-500" />{" "}
                      {selectedFacility.managerPhone}
                    </span>
                  </div>
                </div>
                <Badge variant="neutral">Estate Directorate</Badge>
              </div>
            </div>

            {selectedFacility.equipment &&
              selectedFacility.equipment.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                    Key Installed Equipment & Assets (
                    {selectedFacility.equipment.length})
                  </h4>
                  <div className="divide-y divide-slate-800 bg-slate-950 rounded-lg border border-slate-800 overflow-hidden">
                    {selectedFacility.equipment.map((eq) => (
                      <div
                        key={eq.id}
                        className="p-3 flex items-center justify-between text-xs"
                      >
                        <div>
                          <div className="font-semibold text-white">
                            {eq.name}
                          </div>
                          <div className="text-[11px] text-slate-400 font-mono">
                            {eq.code} • Qty: {eq.quantity}
                          </div>
                        </div>
                        <div className="text-right">
                          <Badge
                            variant={
                              eq.condition === "EXCELLENT"
                                ? "success"
                                : eq.condition === "GOOD"
                                  ? "info"
                                  : "warning"
                            }
                          >
                            {eq.condition}
                          </Badge>
                          <div className="text-[10px] text-slate-500 mt-1 font-mono">
                            Insp: {eq.lastInspectedDate}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedFacility(null)}
              >
                Close
              </Button>
              <Link href={`/app/campus/events/create`}>
                <Button variant="outline" size="sm" className="gap-2">
                  <Calendar className="h-4 w-4" /> Book Venue
                </Button>
              </Link>
              <Link href={`/app/infrastructure/maintenance`}>
                <Button
                  size="sm"
                  className="gap-2 bg-indigo-600 hover:bg-indigo-500 text-white"
                >
                  <Wrench className="h-4 w-4" /> Log Work Order
                </Button>
              </Link>
            </div>
          </div>
        </Dialog>
      )}

      {/* Create Facility Modal */}
      <Dialog
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Register New Campus Facility"
        className="max-w-xl"
      >
        <form onSubmit={handleCreateFacility} className="space-y-4 text-xs">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-slate-300 font-medium block mb-1">
                Facility Name *
              </label>
              <Input
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                placeholder="e.g. Alan Turing Computing Lab"
                required
                className="bg-slate-950 border-slate-800 text-white text-xs"
              />
            </div>
            <div>
              <label className="text-slate-300 font-medium block mb-1">
                Facility Code *
              </label>
              <Input
                value={formData.code}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    code: e.target.value.toUpperCase(),
                  })
                }
                placeholder="e.g. FAC-LAB-CSE-02"
                required
                className="bg-slate-950 border-slate-800 text-white text-xs font-mono"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-slate-300 font-medium block mb-1">
                Facility Type
              </label>
              <Select
                value={formData.type}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    type: e.target.value as FacilityType,
                  })
                }
                className="bg-slate-950 border-slate-800 text-white text-xs"
              >
                <option value={FacilityType.LABORATORY}>Laboratory</option>
                <option value={FacilityType.AUDITORIUM}>Auditorium</option>
                <option value={FacilityType.SEMINAR_HALL}>Seminar Hall</option>
                <option value={FacilityType.SPORTS_COMPLEX}>
                  Sports Complex
                </option>
                <option value={FacilityType.LIBRARY}>Library</option>
                <option value={FacilityType.CAFETERIA}>Cafeteria</option>
                <option value={FacilityType.CLASSROOM_BLOCK}>
                  Classroom Block
                </option>
                <option value={FacilityType.ADMINISTRATIVE}>
                  Administrative
                </option>
              </Select>
            </div>
            <div>
              <label className="text-slate-300 font-medium block mb-1">
                Capacity (Seats)
              </label>
              <Input
                type="number"
                value={formData.capacity}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    capacity: parseInt(e.target.value) || 0,
                  })
                }
                min={1}
                required
                className="bg-slate-950 border-slate-800 text-white text-xs font-mono"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-slate-300 font-medium block mb-1">
                Building
              </label>
              <Input
                value={formData.building}
                onChange={(e) =>
                  setFormData({ ...formData, building: e.target.value })
                }
                placeholder="e.g. Academic Block A"
                className="bg-slate-950 border-slate-800 text-white text-xs"
              />
            </div>
            <div>
              <label className="text-slate-300 font-medium block mb-1">
                Floor Level
              </label>
              <Input
                value={formData.floor}
                onChange={(e) =>
                  setFormData({ ...formData, floor: e.target.value })
                }
                placeholder="e.g. 2nd Floor East"
                className="bg-slate-950 border-slate-800 text-white text-xs"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-slate-300 font-medium block mb-1">
                Manager / In-Charge
              </label>
              <Input
                value={formData.managerName}
                onChange={(e) =>
                  setFormData({ ...formData, managerName: e.target.value })
                }
                placeholder="Dr. Rajesh Rao"
                className="bg-slate-950 border-slate-800 text-white text-xs"
              />
            </div>
            <div>
              <label className="text-slate-300 font-medium block mb-1">
                Email
              </label>
              <Input
                type="email"
                value={formData.managerEmail}
                onChange={(e) =>
                  setFormData({ ...formData, managerEmail: e.target.value })
                }
                placeholder="rajesh.rao@campusos.edu"
                className="bg-slate-950 border-slate-800 text-white text-xs"
              />
            </div>
            <div>
              <label className="text-slate-300 font-medium block mb-1">
                Phone
              </label>
              <Input
                value={formData.managerPhone}
                onChange={(e) =>
                  setFormData({ ...formData, managerPhone: e.target.value })
                }
                placeholder="+91 94480 12345"
                className="bg-slate-950 border-slate-800 text-white text-xs"
              />
            </div>
          </div>

          <div>
            <label className="text-slate-300 font-medium block mb-1">
              Description & Specs
            </label>
            <Textarea
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
              rows={3}
              placeholder="Provide technical specifications, intended usage, and equipment available..."
              className="bg-slate-950 border-slate-800 text-white text-xs"
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setCreateModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              size="sm"
              isLoading={submitting}
              className="bg-indigo-600 hover:bg-indigo-500 text-white"
            >
              Register Facility
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
