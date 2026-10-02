"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import Link from "next/link";
import { maintenanceService } from "@/services/maintenance.service";
import {
  MaintenanceRequest,
  MaintenanceStatus,
  MaintenancePriority,
} from "@campusos/types";
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
  Wrench,
  Search,
  Filter,
  Plus,
  AlertTriangle,
  Clock,
  CheckCircle2,
  FileCheck2,
  DollarSign,
  UserCheck,
  Building2,
  History,
  XCircle,
  AlertCircle,
  Truck,
  Layers,
  MapPin,
} from "lucide-react";

export default function MaintenanceOperationsPage() {
  const { user } = useAuth();
  const { toast } = useToast();

  const [loading, setLoading] = useState(true);
  const [requests, setRequests] = useState<MaintenanceRequest[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPriority, setSelectedPriority] = useState<string>("ALL");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");

  // Selected for View / Update
  const [selectedOrder, setSelectedOrder] = useState<MaintenanceRequest | null>(null);
  const [statusModalOpen, setStatusModalOpen] = useState(false);
  const [assignModalOpen, setAssignModalOpen] = useState(false);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  // Status transition form state
  const [newStatus, setNewStatus] = useState<MaintenanceStatus>(MaintenanceStatus.IN_PROGRESS);
  const [statusNotes, setStatusNotes] = useState("");
  const [resolutionSummary, setResolutionSummary] = useState("");
  const [actualCostInr, setActualCostInr] = useState<number | undefined>(undefined);

  // Assignment form state
  const [assigneeName, setAssigneeName] = useState("");
  const [assigneeDept, setAssigneeDept] = useState("Estate & Maintenance Directorate");
  const [assigneePhone, setAssigneePhone] = useState("");

  // Create form state
  const [createForm, setCreateForm] = useState({
    title: "",
    category: "CIVIL" as const,
    sourceType: "FACILITY" as const,
    assetOrFacilityName: "",
    location: "",
    description: "",
    priority: MaintenancePriority.HIGH,
    slaTargetHours: 24,
    estimatedCostInr: 5000,
  });

  const loadRequests = useCallback(async () => {
    setLoading(true);
    try {
      const res = await maintenanceService.listMaintenanceRequests({
        priority: selectedPriority !== "ALL" ? selectedPriority : undefined,
        status: selectedStatus !== "ALL" ? selectedStatus : undefined,
        category: selectedCategory !== "ALL" ? selectedCategory : undefined,
        search: searchQuery || undefined,
      });
      if (res.success && res.data) {
        setRequests(res.data);
      }
    } catch {
      toast({
        title: "Error",
        description: "Failed to load maintenance work orders.",
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  }, [selectedPriority, selectedStatus, selectedCategory, searchQuery, toast]);

  useEffect(() => {
    loadRequests();
  }, [loadRequests]);

  const handleCreateOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.title.trim() || !createForm.assetOrFacilityName.trim()) {
      toast({
        title: "Validation Error",
        description: "Please specify work order title and target asset/facility.",
        variant: "error",
      });
      return;
    }

    setActionLoading(true);
    try {
      const res = await maintenanceService.createMaintenanceRequest({
        ...createForm,
        assetOrFacilityId: "asset-custom-01",
        reportedBy: {
          userId: user?.id || "usr-admin",
          name: (user as any)?.name || (user?.first_name ? `${user.first_name} ${user.last_name}` : "Maintenance Desk Administrator"),
          role: (user as any)?.role || user?.roles?.[0]?.name || "FACILITY_OFFICER",
          phone: "+91 94480 00000",
        },
      });

      if (res.success) {
        toast({
          title: "Work Order Issued",
          description: `Work Order ${res.data.workOrderNumber} created and queued.`,
          variant: "success",
        });
        setCreateModalOpen(false);
        setCreateForm({
          title: "",
          category: "CIVIL",
          sourceType: "FACILITY",
          assetOrFacilityName: "",
          location: "",
          description: "",
          priority: MaintenancePriority.HIGH,
          slaTargetHours: 24,
          estimatedCostInr: 5000,
        });
        loadRequests();
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateStatus = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrder) return;

    setActionLoading(true);
    try {
      const res = await maintenanceService.updateMaintenanceStatus(selectedOrder.id, {
        status: newStatus,
        changedBy: (user as any)?.name || (user?.first_name ? `${user.first_name} ${user.last_name}` : "Estate Supervisor"),
        notes: statusNotes,
        resolutionSummary: resolutionSummary || undefined,
        actualCostInr: actualCostInr || undefined,
      });

      if (res.success) {
        toast({
          title: "Status Updated",
          description: `Work order transitioned to ${newStatus}.`,
          variant: "success",
        });
        setStatusModalOpen(false);
        setSelectedOrder(res.data);
        setStatusNotes("");
        setResolutionSummary("");
        loadRequests();
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleAssignTechnician = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrder || !assigneeName.trim()) return;

    setActionLoading(true);
    try {
      const res = await maintenanceService.assignMaintenanceTechnician(selectedOrder.id, {
        staffId: `stf-tech-${Date.now().toString().slice(-4)}`,
        name: assigneeName,
        department: assigneeDept,
        phone: assigneePhone || "+91 94480 99999",
      });

      if (res.success) {
        toast({
          title: "Technician Assigned",
          description: `Assigned ${assigneeName} to ${selectedOrder.workOrderNumber}.`,
          variant: "success",
        });
        setAssignModalOpen(false);
        setSelectedOrder(res.data);
        setAssigneeName("");
        loadRequests();
      }
    } finally {
      setActionLoading(false);
    }
  };

  const stats = useMemo(() => {
    const total = requests.length;
    const open = requests.filter(
      (r) => r.status !== MaintenanceStatus.RESOLVED && r.status !== MaintenanceStatus.CLOSED && r.status !== MaintenanceStatus.CANCELLED
    ).length;
    const critical = requests.filter(
      (r) => r.priority === MaintenancePriority.CRITICAL && r.status !== MaintenanceStatus.CLOSED
    ).length;
    const slaBreached = requests.filter((r) => r.isSlaBreached).length;
    const totalEstimatedCost = requests.reduce((acc, r) => acc + (r.estimatedCostInr || 0), 0);

    return { total, open, critical, slaBreached, totalEstimatedCost };
  }, [requests]);

  const getPriorityBadge = (priority: MaintenancePriority) => {
    switch (priority) {
      case MaintenancePriority.CRITICAL:
        return <Badge variant="danger" className="animate-pulse">CRITICAL SLA</Badge>;
      case MaintenancePriority.HIGH:
        return <Badge variant="warning">High Priority</Badge>;
      case MaintenancePriority.MEDIUM:
        return <Badge variant="info">Medium</Badge>;
      case MaintenancePriority.LOW:
      default:
        return <Badge variant="neutral">Low</Badge>;
    }
  };

  const getStatusBadge = (status: MaintenanceStatus) => {
    switch (status) {
      case MaintenanceStatus.REQUESTED:
        return <Badge variant="neutral">Requested</Badge>;
      case MaintenanceStatus.ASSIGNED:
        return <Badge variant="info">Assigned</Badge>;
      case MaintenanceStatus.IN_PROGRESS:
        return <Badge variant="warning">In Progress</Badge>;
      case MaintenanceStatus.ON_HOLD:
        return <Badge variant="neutral">On Hold</Badge>;
      case MaintenanceStatus.RESOLVED:
        return <Badge variant="success">Resolved</Badge>;
      case MaintenanceStatus.CLOSED:
        return <Badge variant="success">Closed</Badge>;
      case MaintenanceStatus.CANCELLED:
        return <Badge variant="danger">Cancelled</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
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
            <span className="text-xs text-indigo-400 font-medium">Work Orders</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2 mt-1">
            <Wrench className="h-6 w-6 text-indigo-400" />
            Infrastructure Maintenance & Work Orders
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Preventive & corrective work orders, SLA tracking, civil/electrical/HVAC repair logs, and estate contractor assignments.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link href="/app/infrastructure/facilities">
            <Button variant="outline" size="sm" className="gap-2">
              <Building2 className="h-4 w-4" />
              Facilities Registry
            </Button>
          </Link>
          <Button
            size="sm"
            onClick={() => setCreateModalOpen(true)}
            className="gap-2 bg-indigo-600 hover:bg-indigo-500 text-white"
          >
            <Plus className="h-4 w-4" />
            Issue Work Order
          </Button>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Open Work Orders"
          value={stats.open.toString()}
          description={`${stats.total} total logged this term`}
          icon={<Wrench className="h-5 w-5 text-indigo-400" />}
        />
        <StatCard
          title="Critical Emergencies"
          value={stats.critical.toString()}
          description={stats.critical > 0 ? "Immediate technician dispatch" : "Zero critical issues"}
          icon={<AlertTriangle className="h-5 w-5 text-rose-400" />}
        />
        <StatCard
          title="SLA Compliance"
          value={`${Math.round(((stats.total - stats.slaBreached) / Math.max(1, stats.total)) * 100)}%`}
          description={`${stats.slaBreached} SLA breach records`}
          icon={<Clock className="h-5 w-5 text-emerald-400" />}
        />
        <StatCard
          title="Estimated Budget Incurred"
          value={`₹${(stats.totalEstimatedCost / 1000).toFixed(1)}k`}
          description="Civil, HVAC, & Electrical repair budget"
          icon={<DollarSign className="h-5 w-5 text-purple-400" />}
        />
      </div>

      {/* Filters */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row gap-4 justify-between items-center backdrop-blur-sm">
        <div className="relative w-full md:w-80">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search work order #, asset, location, technician..."
            className="pl-9 bg-slate-950/70 border-slate-800 text-white w-full text-xs"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Category:</span>
            <Select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-slate-950 border-slate-800 text-xs text-white h-9"
            >
              <option value="ALL">All Categories</option>
              <option value="CIVIL">Civil & Carpentry</option>
              <option value="ELECTRICAL">Electrical & Power</option>
              <option value="PLUMBING">Plumbing & Water</option>
              <option value="HVAC">HVAC & Air Conditioning</option>
              <option value="IT_EQUIPMENT">IT & Network Equipment</option>
              <option value="TRANSPORT_VEHICLE">Fleet & Bus Repair</option>
              <option value="OTHER">General Maintenance</option>
            </Select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Priority:</span>
            <Select
              value={selectedPriority}
              onChange={(e) => setSelectedPriority(e.target.value)}
              className="bg-slate-950 border-slate-800 text-xs text-white h-9"
            >
              <option value="ALL">All Priorities</option>
              <option value={MaintenancePriority.CRITICAL}>Critical</option>
              <option value={MaintenancePriority.HIGH}>High</option>
              <option value={MaintenancePriority.MEDIUM}>Medium</option>
              <option value={MaintenancePriority.LOW}>Low</option>
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
              <option value={MaintenanceStatus.REQUESTED}>Requested</option>
              <option value={MaintenanceStatus.ASSIGNED}>Assigned</option>
              <option value={MaintenanceStatus.IN_PROGRESS}>In Progress</option>
              <option value={MaintenanceStatus.RESOLVED}>Resolved</option>
              <option value={MaintenanceStatus.CLOSED}>Closed</option>
            </Select>
          </div>
        </div>
      </div>

      {/* Work Orders List */}
      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex justify-between items-center">
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-6 w-24" />
            </div>
          ))}
        </div>
      ) : requests.length === 0 ? (
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-12 text-center space-y-3">
          <Wrench className="h-12 w-12 text-slate-600 mx-auto" />
          <h3 className="text-base font-semibold text-white">No Work Orders Matching Filter</h3>
          <p className="text-sm text-slate-400 max-w-md mx-auto">
            All equipment, hostel blocks, and academic facilities are in optimal operational order.
          </p>
        </div>
      ) : (
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl overflow-hidden divide-y divide-slate-800">
          {requests.map((order) => (
            <div
              key={order.id}
              className="p-5 hover:bg-slate-800/40 transition-colors flex flex-col lg:flex-row justify-between lg:items-center gap-4 group"
            >
              <div className="space-y-1.5 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-xs font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                    {order.workOrderNumber}
                  </span>
                  <span className="text-[10px] font-mono uppercase bg-slate-800 text-slate-300 px-2 py-0.5 rounded">
                    {order.category}
                  </span>
                  {getPriorityBadge(order.priority)}
                  {getStatusBadge(order.status)}
                  {order.isSlaBreached && (
                    <span className="text-[10px] font-bold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/30 flex items-center gap-1">
                      <Clock className="h-3 w-3" /> SLA BREACHED
                    </span>
                  )}
                </div>

                <h3 className="text-sm font-bold text-white group-hover:text-indigo-300 transition-colors">
                  {order.title}
                </h3>

                <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
                  <span className="flex items-center gap-1">
                    <Building2 className="h-3.5 w-3.5 text-slate-500" />
                    <span className="text-slate-300 font-medium">{order.assetOrFacilityName}</span>
                  </span>
                  <span className="flex items-center gap-1">
                    <MapPin className="h-3.5 w-3.5 text-slate-500" /> {order.location}
                  </span>
                  <span className="font-mono text-slate-400">
                    Est: <span className="text-white font-semibold">₹{order.estimatedCostInr.toLocaleString()}</span>
                  </span>
                  {order.assignedTo ? (
                    <span className="flex items-center gap-1 text-emerald-400">
                      <UserCheck className="h-3.5 w-3.5" /> {order.assignedTo.name}
                    </span>
                  ) : (
                    <span className="text-amber-400 flex items-center gap-1">
                      <AlertCircle className="h-3.5 w-3.5" /> Unassigned
                    </span>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2 self-end lg:self-center">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedOrder(order)}
                  className="text-xs h-8"
                >
                  View Details
                </Button>
                {order.status !== MaintenanceStatus.CLOSED && order.status !== MaintenanceStatus.CANCELLED && (
                  <Button
                    size="sm"
                    onClick={() => {
                      setSelectedOrder(order);
                      setNewStatus(order.status);
                      setStatusModalOpen(true);
                    }}
                    className="text-xs h-8 bg-slate-800 hover:bg-slate-700 text-white border border-slate-700"
                  >
                    Update Status
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Work Order Detail Drawer / Modal */}
      {selectedOrder && !statusModalOpen && !assignModalOpen && (
        <Dialog
          open={!!selectedOrder}
          onClose={() => setSelectedOrder(null)}
          title={`Work Order ${selectedOrder.workOrderNumber}`}
          className="max-w-2xl"
        >
          <div className="space-y-5 text-xs">
            <div className="flex items-center justify-between bg-slate-950 p-3 rounded-lg border border-slate-800">
              <div className="flex items-center gap-2">
                {getPriorityBadge(selectedOrder.priority)}
                {getStatusBadge(selectedOrder.status)}
                <span className="font-mono text-slate-400">• SLA Target: {selectedOrder.slaTargetHours} hrs</span>
              </div>
              <span className="font-mono text-slate-400 text-[11px]">{selectedOrder.createdAt}</span>
            </div>

            <div>
              <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">Issue Title</h4>
              <p className="text-sm font-semibold text-white bg-slate-950 p-3 rounded-lg border border-slate-800">
                {selectedOrder.title}
              </p>
            </div>

            <div>
              <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">Description</h4>
              <p className="text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                {selectedOrder.description}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-1">
                <span className="text-slate-500 font-medium">Asset / Facility</span>
                <p className="font-semibold text-white text-xs">{selectedOrder.assetOrFacilityName}</p>
                <span className="text-[11px] text-slate-400">{selectedOrder.location}</span>
              </div>

              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-1">
                <span className="text-slate-500 font-medium">Estimated vs Actual Cost</span>
                <p className="font-mono text-white text-xs">
                  Est: ₹{selectedOrder.estimatedCostInr.toLocaleString()}{" "}
                  {selectedOrder.actualCostInr ? (
                    <span className="text-emerald-400 font-bold ml-1">
                      • Act: ₹{selectedOrder.actualCostInr.toLocaleString()}
                    </span>
                  ) : (
                    <span className="text-slate-500 ml-1">• Final cost pending</span>
                  )}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-1">
                <span className="text-slate-500 font-medium">Reported By</span>
                <p className="font-semibold text-white">{selectedOrder.reportedBy.name}</p>
                <span className="text-[11px] text-slate-400">{selectedOrder.reportedBy.role} ({selectedOrder.reportedBy.phone})</span>
              </div>

              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-1">
                <span className="text-slate-500 font-medium">Assigned Technician</span>
                {selectedOrder.assignedTo ? (
                  <div>
                    <p className="font-semibold text-emerald-400">{selectedOrder.assignedTo.name}</p>
                    <span className="text-[11px] text-slate-400">{selectedOrder.assignedTo.department}</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-between">
                    <span className="text-amber-400">Unassigned</span>
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-6 text-[10px]"
                      onClick={() => setAssignModalOpen(true)}
                    >
                      Assign Now
                    </Button>
                  </div>
                )}
              </div>
            </div>

            {selectedOrder.history && selectedOrder.history.length > 0 && (
              <div>
                <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <History className="h-3.5 w-3.5" /> Work Order Lifecycle Timeline
                </h4>
                <div className="space-y-2 bg-slate-950 p-3 rounded-lg border border-slate-800 divide-y divide-slate-800/80">
                  {selectedOrder.history.map((h) => (
                    <div key={h.id} className="pt-2 first:pt-0 space-y-0.5 text-[11px]">
                      <div className="flex items-center justify-between font-mono">
                        <span className="font-semibold text-white">
                          {h.fromStatus} → <span className="text-indigo-400">{h.toStatus}</span>
                        </span>
                        <span className="text-slate-500">{h.timestamp}</span>
                      </div>
                      <div className="text-slate-400">
                        <span className="text-slate-500">By:</span> {h.changedBy}
                      </div>
                      {h.notes && <p className="text-slate-300 italic text-[11px]">"{h.notes}"</p>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
              <Button variant="ghost" size="sm" onClick={() => setSelectedOrder(null)}>
                Close
              </Button>
              {selectedOrder.status !== MaintenanceStatus.CLOSED && (
                <>
                  {!selectedOrder.assignedTo && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setAssignModalOpen(true)}
                    >
                      Assign Technician
                    </Button>
                  )}
                  <Button
                    size="sm"
                    onClick={() => {
                      setNewStatus(selectedOrder.status);
                      setStatusModalOpen(true);
                    }}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white"
                  >
                    Advance Status
                  </Button>
                </>
              )}
            </div>
          </div>
        </Dialog>
      )}

      {/* Status Transition Dialog */}
      {statusModalOpen && selectedOrder && (
        <Dialog
          open={statusModalOpen}
          onClose={() => setStatusModalOpen(false)}
          title={`Update Work Order ${selectedOrder.workOrderNumber}`}
          className="max-w-md"
        >
          <form onSubmit={handleUpdateStatus} className="space-y-4 text-xs">
            <div>
              <label className="text-slate-300 font-medium block mb-1">New Workflow Status</label>
              <Select
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value as MaintenanceStatus)}
                className="bg-slate-950 border-slate-800 text-white text-xs w-full"
              >
                <option value={MaintenanceStatus.ASSIGNED}>ASSIGNED</option>
                <option value={MaintenanceStatus.IN_PROGRESS}>IN_PROGRESS</option>
                <option value={MaintenanceStatus.ON_HOLD}>ON_HOLD</option>
                <option value={MaintenanceStatus.RESOLVED}>RESOLVED</option>
                <option value={MaintenanceStatus.CLOSED}>CLOSED</option>
                <option value={MaintenanceStatus.CANCELLED}>CANCELLED</option>
              </Select>
            </div>

            <div>
              <label className="text-slate-300 font-medium block mb-1">Audit Transition Notes *</label>
              <Textarea
                value={statusNotes}
                onChange={(e) => setStatusNotes(e.target.value)}
                placeholder="Document progress, procured materials, contractor notes..."
                required
                rows={2}
                className="bg-slate-950 border-slate-800 text-white text-xs"
              />
            </div>

            {(newStatus === MaintenanceStatus.RESOLVED || newStatus === MaintenanceStatus.CLOSED) && (
              <>
                <div>
                  <label className="text-slate-300 font-medium block mb-1">Resolution Summary</label>
                  <Textarea
                    value={resolutionSummary}
                    onChange={(e) => setResolutionSummary(e.target.value)}
                    placeholder="e.g. Capacitor replaced, motor aligned, tested under load for 2 hours."
                    rows={2}
                    className="bg-slate-950 border-slate-800 text-white text-xs"
                  />
                </div>

                <div>
                  <label className="text-slate-300 font-medium block mb-1">Actual Incurred Cost (₹)</label>
                  <Input
                    type="number"
                    value={actualCostInr || ""}
                    onChange={(e) => setActualCostInr(parseFloat(e.target.value) || 0)}
                    placeholder="e.g. 4200"
                    className="bg-slate-950 border-slate-800 text-white text-xs font-mono"
                  />
                </div>
              </>
            )}

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
              <Button type="button" variant="ghost" size="sm" onClick={() => setStatusModalOpen(false)}>
                Back
              </Button>
              <Button type="submit" size="sm" isLoading={actionLoading} className="bg-indigo-600 hover:bg-indigo-500 text-white">
                Save Status
              </Button>
            </div>
          </form>
        </Dialog>
      )}

      {/* Assign Technician Dialog */}
      {assignModalOpen && selectedOrder && (
        <Dialog
          open={assignModalOpen}
          onClose={() => setAssignModalOpen(false)}
          title={`Assign Technician to ${selectedOrder.workOrderNumber}`}
          className="max-w-md"
        >
          <form onSubmit={handleAssignTechnician} className="space-y-4 text-xs">
            <div>
              <label className="text-slate-300 font-medium block mb-1">Technician / Contractor Name *</label>
              <Input
                value={assigneeName}
                onChange={(e) => setAssigneeName(e.target.value)}
                placeholder="e.g. Muniswamy (Lead Carpenter)"
                required
                className="bg-slate-950 border-slate-800 text-white text-xs"
              />
            </div>

            <div>
              <label className="text-slate-300 font-medium block mb-1">Department / Unit</label>
              <Input
                value={assigneeDept}
                onChange={(e) => setAssigneeDept(e.target.value)}
                placeholder="e.g. Estate Civil & Carpentry Unit"
                className="bg-slate-950 border-slate-800 text-white text-xs"
              />
            </div>

            <div>
              <label className="text-slate-300 font-medium block mb-1">Contact Phone</label>
              <Input
                value={assigneePhone}
                onChange={(e) => setAssigneePhone(e.target.value)}
                placeholder="+91 94480 11223"
                className="bg-slate-950 border-slate-800 text-white text-xs"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
              <Button type="button" variant="ghost" size="sm" onClick={() => setAssignModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" size="sm" isLoading={actionLoading} className="bg-indigo-600 hover:bg-indigo-500 text-white">
                Confirm Assignment
              </Button>
            </div>
          </form>
        </Dialog>
      )}

      {/* Create Work Order Dialog */}
      <Dialog
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Issue New Maintenance Work Order"
        className="max-w-xl"
      >
        <form onSubmit={handleCreateOrder} className="space-y-4 text-xs">
          <div>
            <label className="text-slate-300 font-medium block mb-1">Work Order Title *</label>
            <Input
              value={createForm.title}
              onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
              placeholder="e.g. Precision AC Unit 2 tripping on high pressure fault"
              required
              className="bg-slate-950 border-slate-800 text-white text-xs"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-slate-300 font-medium block mb-1">Target Asset or Facility *</label>
              <Input
                value={createForm.assetOrFacilityName}
                onChange={(e) => setCreateForm({ ...createForm, assetOrFacilityName: e.target.value })}
                placeholder="e.g. Turing Advanced Computing & AI Lab"
                required
                className="bg-slate-950 border-slate-800 text-white text-xs"
              />
            </div>

            <div>
              <label className="text-slate-300 font-medium block mb-1">Precise Location *</label>
              <Input
                value={createForm.location}
                onChange={(e) => setCreateForm({ ...createForm, location: e.target.value })}
                placeholder="e.g. Academic Block A, 3rd Floor East"
                required
                className="bg-slate-950 border-slate-800 text-white text-xs"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-slate-300 font-medium block mb-1">Category</label>
              <Select
                value={createForm.category}
                onChange={(e) => setCreateForm({ ...createForm, category: e.target.value as any })}
                className="bg-slate-950 border-slate-800 text-white text-xs"
              >
                <option value="CIVIL">Civil</option>
                <option value="ELECTRICAL">Electrical</option>
                <option value="PLUMBING">Plumbing</option>
                <option value="HVAC">HVAC</option>
                <option value="IT_EQUIPMENT">IT Equipment</option>
                <option value="CARPENTRY">Carpentry</option>
                <option value="TRANSPORT_VEHICLE">Vehicle</option>
                <option value="OTHER">Other</option>
              </Select>
            </div>

            <div>
              <label className="text-slate-300 font-medium block mb-1">Priority</label>
              <Select
                value={createForm.priority}
                onChange={(e) => setCreateForm({ ...createForm, priority: e.target.value as MaintenancePriority })}
                className="bg-slate-950 border-slate-800 text-white text-xs"
              >
                <option value={MaintenancePriority.CRITICAL}>Critical (Immediate)</option>
                <option value={MaintenancePriority.HIGH}>High (12-24h)</option>
                <option value={MaintenancePriority.MEDIUM}>Medium (48h)</option>
                <option value={MaintenancePriority.LOW}>Low (Routine)</option>
              </Select>
            </div>

            <div>
              <label className="text-slate-300 font-medium block mb-1">SLA Target (Hours)</label>
              <Input
                type="number"
                value={createForm.slaTargetHours}
                onChange={(e) => setCreateForm({ ...createForm, slaTargetHours: parseInt(e.target.value) || 24 })}
                min={1}
                className="bg-slate-950 border-slate-800 text-white text-xs font-mono"
              />
            </div>
          </div>

          <div>
            <label className="text-slate-300 font-medium block mb-1">Estimated Budget (₹)</label>
            <Input
              type="number"
              value={createForm.estimatedCostInr}
              onChange={(e) => setCreateForm({ ...createForm, estimatedCostInr: parseFloat(e.target.value) || 0 })}
              className="bg-slate-950 border-slate-800 text-white text-xs font-mono"
            />
          </div>

          <div>
            <label className="text-slate-300 font-medium block mb-1">Detailed Description *</label>
            <Textarea
              value={createForm.description}
              onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
              rows={3}
              placeholder="Describe technical symptoms, failure causes, immediate risk, and recommended parts..."
              required
              className="bg-slate-950 border-slate-800 text-white text-xs"
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
            <Button type="button" variant="ghost" size="sm" onClick={() => setCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm" isLoading={actionLoading} className="bg-indigo-600 hover:bg-indigo-500 text-white">
              Issue Work Order
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
