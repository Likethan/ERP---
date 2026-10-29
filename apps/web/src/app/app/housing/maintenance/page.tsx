"use client";

import { useEffect, useState } from "react";
import {
  Wrench,
  Plus,
  Search,
  Filter,
  AlertCircle,
  CheckCircle,
  Clock,
  X,
  Star,
  User,
  RotateCw,
} from "lucide-react";
import { HousingNav } from "@/components/housing/housing-nav";
import { HousingService } from "@/services/housing.service";
import {
  AccommodationProperty,
  AccommodationUnit,
  HousingMaintenanceCreateInput,
  HousingMaintenanceRequest,
  HousingMaintenanceUpdateInput,
  MaintenanceCategory,
  MaintenancePriority,
  MaintenanceStatus,
} from "@/types/housing";

export default function MaintenanceTicketsPage() {
  const [tickets, setTickets] = useState<HousingMaintenanceRequest[]>([]);
  const [properties, setProperties] = useState<AccommodationProperty[]>([]);
  const [units, setUnits] = useState<AccommodationUnit[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [priorityFilter, setPriorityFilter] = useState<string>("ALL");

  const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
  const [selectedTicketToUpdate, setSelectedTicketToUpdate] = useState<HousingMaintenanceRequest | null>(null);

  const [newTicket, setNewTicket] = useState<HousingMaintenanceCreateInput>({
    property_id: "",
    unit_id: "",
    category: "ELECTRICAL",
    priority: "HIGH",
    title: "",
    description: "",
  });

  const [updateData, setUpdateData] = useState<HousingMaintenanceUpdateInput>({
    status: "IN_PROGRESS",
    assigned_technician_name: "",
    completion_notes: "",
    tenant_satisfaction_rating: 5,
  });

  const [actionLoading, setActionLoading] = useState(false);

  const loadData = async () => {
    try {
      const [allTickets, allProps] = await Promise.all([
        HousingService.listMaintenance(),
        HousingService.listProperties(false),
      ]);
      setTickets(allTickets);
      setProperties(allProps);
      if (allProps.length > 0) {
        setNewTicket((prev) => ({ ...prev, property_id: allProps[0].id }));
      }
    } catch (err) {
      console.error("Failed to load maintenance tickets", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (!newTicket.property_id) return;
    async function loadUnitsForProp() {
      try {
        const u = await HousingService.listUnits(newTicket.property_id);
        setUnits(u);
      } catch (err) {
        console.error("Failed to load units", err);
      }
    }
    loadUnitsForProp();
  }, [newTicket.property_id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      await HousingService.submitMaintenance(newTicket);
      setIsSubmitModalOpen(false);
      setNewTicket({
        property_id: properties[0]?.id || "",
        unit_id: "",
        category: "ELECTRICAL",
        priority: "HIGH",
        title: "",
        description: "",
      });
      loadData();
    } catch (err) {
      alert("Failed to create maintenance ticket: " + (err as Error).message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTicketToUpdate) return;
    setActionLoading(true);
    try {
      await HousingService.updateMaintenance(selectedTicketToUpdate.id, updateData);
      setSelectedTicketToUpdate(null);
      loadData();
    } catch (err) {
      alert("Failed to update ticket: " + (err as Error).message);
    } finally {
      setActionLoading(false);
    }
  };

  const filteredTickets = tickets.filter((t) => {
    const matchesSearch =
      t.title.toLowerCase().includes(search.toLowerCase()) ||
      t.description.toLowerCase().includes(search.toLowerCase());

    const matchesStatus = statusFilter === "ALL" || t.status === statusFilter;
    const matchesPriority = priorityFilter === "ALL" || t.priority === priorityFilter;

    return matchesSearch && matchesStatus && matchesPriority;
  });

  const getPriorityBadge = (priority: MaintenancePriority) => {
    switch (priority) {
      case "EMERGENCY":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40">
            Emergency
          </span>
        );
      case "HIGH":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/40">
            High Priority
          </span>
        );
      case "MEDIUM":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-sky-500/10 text-sky-400 border border-sky-500/30">
            Medium
          </span>
        );
      case "LOW":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-slate-800 text-slate-400">
            Low
          </span>
        );
      default:
        return null;
    }
  };

  const getStatusBadge = (status: MaintenanceStatus) => {
    switch (status) {
      case "REPORTED":
      case "ASSIGNED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-sky-500/10 text-sky-400 border border-sky-500/30">
            <Clock className="w-3.5 h-3.5" />
            {status}
          </span>
        );
      case "IN_PROGRESS":
      case "WAITING_PARTS":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <RotateCw className="w-3.5 h-3.5 animate-spin" />
            In Progress
          </span>
        );
      case "COMPLETED":
      case "VERIFIED_BY_TENANT":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle className="w-3.5 h-3.5" />
            {status}
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs bg-slate-800 text-slate-400">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <HousingNav />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <Wrench className="w-7 h-7 text-indigo-400" />
              Residential Maintenance Tickets & Facility Work Orders
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Student defect reports, ERP work order linkages, certified artisan dispatch, and tenant satisfaction auditing.
            </p>
          </div>

          <button
            onClick={() => setIsSubmitModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            Report Issue / Ticket
          </button>
        </div>

        {/* Filter bar */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="relative md:col-span-2">
            <Search className="w-5 h-5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search by defect description or title..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-300 focus:outline-none focus:border-indigo-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="REPORTED">Reported</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="COMPLETED">Completed</option>
              <option value="VERIFIED_BY_TENANT">Verified by Tenant</option>
            </select>
          </div>

          <div>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-300 focus:outline-none focus:border-indigo-500"
            >
              <option value="ALL">All Priorities</option>
              <option value="EMERGENCY">Emergency</option>
              <option value="HIGH">High Priority</option>
              <option value="MEDIUM">Medium Priority</option>
              <option value="LOW">Low Priority</option>
            </select>
          </div>
        </div>

        {/* Table */}
        {loading ? (
          <div className="py-20 text-center text-slate-400">Loading maintenance tickets...</div>
        ) : filteredTickets.length === 0 ? (
          <div className="py-16 text-center border border-dashed border-slate-800 rounded-xl bg-slate-900/30">
            <p className="text-slate-400">No maintenance tickets matching your filters.</p>
          </div>
        ) : (
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-950/80 border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <tr>
                    <th className="px-5 py-3">Ticket Info</th>
                    <th className="px-5 py-3">Facility / Room</th>
                    <th className="px-5 py-3">Category & Priority</th>
                    <th className="px-5 py-3">Technician Assignment</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredTickets.map((t) => (
                    <tr key={t.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-5 py-4">
                        <div className="font-semibold text-white mt-0.5">{t.title}</div>
                        <div className="text-xs text-slate-400 line-clamp-1">{t.description}</div>
                      </td>
                      <td className="px-5 py-4">
                        <div className="text-xs text-slate-200">
                          {t.property_name || "Facility"}
                        </div>
                        <div className="text-[11px] text-slate-500">
                          {t.unit_number ? `Room ${t.unit_number}` : "Common Area"}
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <div className="text-xs text-slate-300 font-medium">
                          {t.category.replace(/_/g, " ")}
                        </div>
                        <div className="mt-1">{getPriorityBadge(t.priority)}</div>
                      </td>
                      <td className="px-5 py-4">
                        {t.assigned_technician_name ? (
                          <div className="text-xs text-slate-200">
                            <span className="font-medium">{t.assigned_technician_name}</span>
                          </div>
                        ) : (
                          <span className="text-xs text-slate-500 italic">Unassigned</span>
                        )}
                        {t.tenant_satisfaction_rating && (
                          <div className="flex items-center gap-1 text-amber-400 text-xs mt-1">
                            <Star className="w-3.5 h-3.5 fill-amber-400" />
                            <span>{t.tenant_satisfaction_rating} / 5</span>
                          </div>
                        )}
                      </td>
                      <td className="px-5 py-4">{getStatusBadge(t.status)}</td>
                      <td className="px-5 py-4 text-right">
                        <button
                          onClick={() => {
                            setSelectedTicketToUpdate(t);
                            setUpdateData({
                              status: t.status,
                              assigned_technician_name: t.assigned_technician_name || "",
                              completion_notes: t.completion_notes || "",
                              tenant_satisfaction_rating: t.tenant_satisfaction_rating || 5,
                            });
                          }}
                          className="px-3 py-1.5 text-xs font-medium rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
                        >
                          Dispatch / Resolve
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Modal: Update Ticket */}
        {selectedTicketToUpdate && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
            <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Wrench className="w-5 h-5 text-indigo-400" />
                  Update Ticket Resolution
                </h3>
                <button
                  onClick={() => setSelectedTicketToUpdate(null)}
                  className="text-slate-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="p-3 bg-slate-950 rounded-lg text-xs space-y-1">
                <div className="font-semibold text-white">{selectedTicketToUpdate.title}</div>
                <div className="text-slate-400">{selectedTicketToUpdate.description}</div>
              </div>

              <form onSubmit={handleUpdate} className="space-y-4 text-sm">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Ticket Resolution Status *
                  </label>
                  <select
                    value={updateData.status}
                    onChange={(e) =>
                      setUpdateData({
                        ...updateData,
                        status: e.target.value as MaintenanceStatus,
                      })
                    }
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                  >
                    <option value="REPORTED">Reported</option>
                    <option value="ASSIGNED">Assigned</option>
                    <option value="IN_PROGRESS">In Progress</option>
                    <option value="COMPLETED">Completed</option>
                    <option value="VERIFIED_BY_TENANT">Verified by Tenant</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Assigned Artisan / Technician
                  </label>
                  <input
                    type="text"
                    value={updateData.assigned_technician_name || ""}
                    onChange={(e) =>
                      setUpdateData({
                        ...updateData,
                        assigned_technician_name: e.target.value,
                      })
                    }
                    placeholder="e.g. Ramesh K (Electrician)"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Work Notes & Corrective Actions
                  </label>
                  <textarea
                    rows={2}
                    value={updateData.completion_notes || ""}
                    onChange={(e) =>
                      setUpdateData({
                        ...updateData,
                        completion_notes: e.target.value,
                      })
                    }
                    placeholder="e.g. Capacitor replaced; circuit tested and operational."
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200 text-xs"
                  />
                </div>

                {updateData.status === "COMPLETED" && (
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Tenant Satisfaction Rating (1-5 Stars)
                    </label>
                    <select
                      value={updateData.tenant_satisfaction_rating || 5}
                      onChange={(e) =>
                        setUpdateData({
                          ...updateData,
                          tenant_satisfaction_rating: parseInt(e.target.value) || 5,
                        })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    >
                      <option value="5">★★★★★ Excellent (5/5)</option>
                      <option value="4">★★★★☆ Good (4/5)</option>
                      <option value="3">★★★☆☆ Satisfactory (3/5)</option>
                      <option value="2">★★☆☆☆ Subpar (2/5)</option>
                      <option value="1">★☆☆☆☆ Poor (1/5)</option>
                    </select>
                  </div>
                )}

                <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setSelectedTicketToUpdate(null)}
                    className="px-4 py-2 text-xs font-medium rounded-md bg-slate-800 text-slate-300 hover:bg-slate-700"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={actionLoading}
                    className="px-4 py-2 text-xs font-medium rounded-md bg-indigo-600 hover:bg-indigo-500 text-white"
                  >
                    Save & Dispatch
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Submit New Ticket */}
        {isSubmitModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
            <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto shadow-2xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-lg font-bold text-white">Report Maintenance / Facility Defect</h3>
                <button
                  onClick={() => setIsSubmitModalOpen(false)}
                  className="text-slate-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4 text-sm">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Select Facility *
                  </label>
                  <select
                    required
                    value={newTicket.property_id}
                    onChange={(e) =>
                      setNewTicket({ ...newTicket, property_id: e.target.value })
                    }
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                  >
                    {properties.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.code})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Affected Unit / Room
                    </label>
                    <select
                      value={newTicket.unit_id || ""}
                      onChange={(e) =>
                        setNewTicket({ ...newTicket, unit_id: e.target.value })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    >
                      <option value="">Common Area / General</option>
                      {units.map((u) => (
                        <option key={u.id} value={u.id}>
                          Room {u.unit_number} (Floor {u.floor_number})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Defect Category *
                    </label>
                    <select
                      value={newTicket.category}
                      onChange={(e) =>
                        setNewTicket({
                          ...newTicket,
                          category: e.target.value as MaintenanceCategory,
                        })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    >
                      <option value="ELECTRICAL">Electrical & Lighting</option>
                      <option value="PLUMBING">Plumbing & Sanitary</option>
                      <option value="CARPENTRY">Carpentry & Locks</option>
                      <option value="HVAC">Air Conditioning & HVAC</option>
                      <option value="PEST_CONTROL">Pest Control</option>
                      <option value="INTERNET_WIFI">Wi-Fi & Network</option>
                      <option value="CLEANING">Cleaning & Sanitization</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Priority Level *
                    </label>
                    <select
                      value={newTicket.priority}
                      onChange={(e) =>
                        setNewTicket({
                          ...newTicket,
                          priority: e.target.value as MaintenancePriority,
                        })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    >
                      <option value="LOW">Low (within 5 days)</option>
                      <option value="MEDIUM">Medium (within 48 hours)</option>
                      <option value="HIGH">High (within 24 hours)</option>
                      <option value="EMERGENCY">Emergency (Immediate)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Defect Headline *
                    </label>
                    <input
                      required
                      type="text"
                      value={newTicket.title}
                      onChange={(e) =>
                        setNewTicket({ ...newTicket, title: e.target.value })
                      }
                      placeholder="e.g. Geyser tripping MCB"
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Detailed Problem Description *
                  </label>
                  <textarea
                    required
                    rows={3}
                    value={newTicket.description}
                    onChange={(e) =>
                      setNewTicket({ ...newTicket, description: e.target.value })
                    }
                    placeholder="Describe the defect, when it started, and exact room location..."
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200 text-xs"
                  />
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setIsSubmitModalOpen(false)}
                    className="px-4 py-2 text-xs font-medium rounded-md bg-slate-800 text-slate-300 hover:bg-slate-700"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={actionLoading}
                    className="px-4 py-2 text-xs font-medium rounded-md bg-indigo-600 hover:bg-indigo-500 text-white"
                  >
                    File Maintenance Ticket
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
