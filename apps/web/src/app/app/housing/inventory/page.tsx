"use client";

import { useEffect, useState } from "react";
import {
  Layers,
  Plus,
  Building2,
  ShieldAlert,
  Lock,
  Unlock,
  X,
  CheckCircle,
  Ban,
  User,
} from "lucide-react";
import { HousingNav } from "@/components/housing/housing-nav";
import { HousingService } from "@/services/housing.service";
import {
  AccommodationBed,
  AccommodationProperty,
  AccommodationUnit,
  UnitCreateInput,
  UnitType,
} from "@/types/housing";

export default function InventoryUnitsPage() {
  const [properties, setProperties] = useState<AccommodationProperty[]>([]);
  const [selectedPropertyId, setSelectedPropertyId] = useState<string>("");
  const [units, setUnits] = useState<AccommodationUnit[]>([]);
  const [loading, setLoading] = useState(true);
  const [unitsLoading, setUnitsLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedBedToBlock, setSelectedBedToBlock] = useState<AccommodationBed | null>(null);
  const [blockReason, setBlockReason] = useState("Annual maintenance repainting & electrical overhaul");
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const [formData, setFormData] = useState<UnitCreateInput>({
    property_id: "",
    unit_number: "",
    floor_number: 1,
    unit_type: "DOUBLE_OCCUPANCY",
    bed_capacity: 2,
    rent_per_bed: 9500,
    security_deposit_per_bed: 15000,
    has_attached_bath: true,
    is_accessible: false,
    is_furnished: true,
  });

  useEffect(() => {
    async function loadProperties() {
      try {
        const props = await HousingService.listProperties(false);
        setProperties(props);
        if (props.length > 0) {
          setSelectedPropertyId(props[0].id);
          setFormData((prev) => ({ ...prev, property_id: props[0].id }));
        }
      } catch (err) {
        console.error("Failed to load properties", err);
      } finally {
        setLoading(false);
      }
    }
    loadProperties();
  }, []);

  useEffect(() => {
    if (!selectedPropertyId) return;
    async function loadUnits() {
      setUnitsLoading(true);
      try {
        const data = await HousingService.listUnits(selectedPropertyId);
        setUnits(data);
      } catch (err) {
        console.error("Failed to load units", err);
      } finally {
        setUnitsLoading(false);
      }
    }
    loadUnits();
  }, [selectedPropertyId]);

  const handleCreateUnit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPropertyId) return;
    try {
      await HousingService.createUnit({
        ...formData,
        property_id: selectedPropertyId,
      });
      setIsModalOpen(false);
      setFormData({
        property_id: selectedPropertyId,
        unit_number: "",
        floor_number: 1,
        unit_type: "DOUBLE_OCCUPANCY",
        bed_capacity: 2,
        rent_per_bed: 9500,
        security_deposit_per_bed: 15000,
        has_attached_bath: true,
        is_accessible: false,
        is_furnished: true,
      });
      const data = await HousingService.listUnits(selectedPropertyId);
      setUnits(data);
    } catch (err) {
      alert("Failed to create unit: " + (err as Error).message);
    }
  };

  const handleToggleBlock = async (bed: AccommodationBed, block: boolean) => {
    setActionLoading(bed.id);
    try {
      await HousingService.toggleBedBlock(
        bed.id,
        block,
        block ? blockReason : undefined
      );
      setSelectedBedToBlock(null);
      const data = await HousingService.listUnits(selectedPropertyId);
      setUnits(data);
    } catch (err) {
      alert("Failed to toggle bed block: " + (err as Error).message);
    } finally {
      setActionLoading(null);
    }
  };

  const selectedProperty = properties.find((p) => p.id === selectedPropertyId);

  const getBedStatusBadge = (status: string) => {
    switch (status) {
      case "AVAILABLE":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle className="w-3 h-3" /> Available
          </span>
        );
      case "RESERVED":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/30">
            Reserved
          </span>
        );
      case "OCCUPIED":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
            <User className="w-3 h-3" /> Occupied
          </span>
        );
      case "BLOCKED_MAINTENANCE":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/30">
            <Ban className="w-3 h-3" /> Blocked
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-400">
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
              <Layers className="w-7 h-7 text-indigo-400" />
              Units & Addressable Bed Capacity Inventory
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Live unit configurations, individual bed assignment slots, concurrency locks, and quarantine maintenance blocks.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsModalOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-colors shadow-sm"
            >
              <Plus className="w-4 h-4" />
              Add Unit / Room
            </button>
          </div>
        </div>

        {/* Property Selector Bar */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Building2 className="w-5 h-5 text-indigo-400" />
            <span className="text-sm font-semibold text-slate-300">Select Facility:</span>
            <select
              value={selectedPropertyId}
              onChange={(e) => setSelectedPropertyId(e.target.value)}
              className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-indigo-500"
            >
              {properties.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.code}) — {p.property_type.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </div>

          {selectedProperty && (
            <div className="flex items-center gap-6 text-xs text-slate-400">
              <div>
                Total Capacity: <span className="font-semibold text-white">{selectedProperty.total_bed_capacity} Beds</span>
              </div>
              <div>
                Occupied: <span className="font-semibold text-indigo-400">{selectedProperty.occupied_beds}</span>
              </div>
              <div>
                Available: <span className="font-semibold text-emerald-400">{selectedProperty.available_beds}</span>
              </div>
            </div>
          )}
        </div>

        {/* Units & Beds List */}
        {loading || unitsLoading ? (
          <div className="py-20 text-center text-slate-400">Loading units and real-time bed inventories...</div>
        ) : units.length === 0 ? (
          <div className="py-16 text-center border border-dashed border-slate-800 rounded-xl bg-slate-900/30">
            <p className="text-slate-400">No rooms/units configured yet for this property.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {units.map((unit) => (
              <div
                key={unit.id}
                className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-all"
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-bold text-white">
                        Room {unit.unit_number}
                      </h3>
                      <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                        Floor {unit.floor_number}
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 font-medium">
                        {unit.unit_type.replace(/_/g, " ")}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 mt-2">
                      <span>Rent: <strong className="text-slate-200">₹{unit.rent_per_bed.toLocaleString("en-IN")}/mo</strong></span>
                      <span>Deposit: <strong className="text-slate-200">₹{unit.security_deposit_per_bed.toLocaleString("en-IN")}</strong></span>
                      {unit.has_attached_bath && <span className="text-teal-400">Ensuite Bath</span>}
                      {unit.is_furnished && <span className="text-emerald-400">Furnished</span>}
                      {unit.is_accessible && <span className="text-purple-400 font-medium">♿ Accessible</span>}
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="text-right text-xs">
                      <div className="text-slate-400">Occupancy</div>
                      <div className="font-semibold text-white">
                        {unit.occupied_beds} / {unit.bed_capacity} Beds
                      </div>
                    </div>
                  </div>
                </div>

                {/* Bed Slots Grid */}
                <div className="mt-4">
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                    Addressable Bed Slots
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
                    {unit.beds?.map((bed) => (
                      <div
                        key={bed.id}
                        className={`p-3 rounded-lg border flex flex-col justify-between ${
                          bed.status === "AVAILABLE"
                            ? "bg-slate-950/80 border-slate-800"
                            : bed.status === "OCCUPIED"
                            ? "bg-indigo-950/20 border-indigo-900/40"
                            : bed.status === "BLOCKED_MAINTENANCE"
                            ? "bg-rose-950/20 border-rose-900/40"
                            : "bg-amber-950/20 border-amber-900/40"
                        }`}
                      >
                        <div>
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-sm text-white font-mono">
                              Bed {bed.bed_code}
                            </span>
                            {getBedStatusBadge(bed.status)}
                          </div>
                          {bed.blocked_reason && (
                            <div className="text-[11px] text-rose-400 mt-1 italic">
                              {bed.blocked_reason}
                            </div>
                          )}
                        </div>

                        <div className="mt-3 pt-2 border-t border-slate-800/60 flex justify-end">
                          {bed.status === "AVAILABLE" && (
                            <button
                              onClick={() => setSelectedBedToBlock(bed)}
                              className="inline-flex items-center gap-1 text-[11px] font-medium text-rose-400 hover:text-rose-300"
                            >
                              <Lock className="w-3.5 h-3.5" />
                              Block for Maintenance
                            </button>
                          )}
                          {bed.status === "BLOCKED_MAINTENANCE" && (
                            <button
                              disabled={actionLoading === bed.id}
                              onClick={() => handleToggleBlock(bed, false)}
                              className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-400 hover:text-emerald-300"
                            >
                              <Unlock className="w-3.5 h-3.5" />
                              Unblock & Restore
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Modal: Block Bed Confirmation */}
        {selectedBedToBlock && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
            <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-5 space-y-4 shadow-2xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <ShieldAlert className="w-5 h-5 text-rose-400" />
                  Block Bed {selectedBedToBlock.bed_code}
                </h3>
                <button
                  onClick={() => setSelectedBedToBlock(null)}
                  className="text-slate-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <p className="text-xs text-slate-300">
                Blocking this bed removes it from available student allocation inventory until repairs or sanitization are verified.
              </p>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Reason for Maintenance Quarantine *
                </label>
                <textarea
                  rows={3}
                  value={blockReason}
                  onChange={(e) => setBlockReason(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-xs text-slate-200 focus:outline-none focus:border-rose-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setSelectedBedToBlock(null)}
                  className="px-3 py-1.5 text-xs rounded bg-slate-800 text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={actionLoading === selectedBedToBlock.id}
                  onClick={() => handleToggleBlock(selectedBedToBlock, true)}
                  className="px-3 py-1.5 text-xs font-semibold rounded bg-rose-600 hover:bg-rose-500 text-white"
                >
                  Confirm Quarantine Block
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal: Add Unit */}
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
            <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto shadow-2xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h2 className="text-lg font-bold text-white">Add Room / Unit to Facility</h2>
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="text-slate-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleCreateUnit} className="space-y-4 text-sm">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Room / Unit # *
                    </label>
                    <input
                      required
                      type="text"
                      value={formData.unit_number}
                      onChange={(e) => setFormData({ ...formData, unit_number: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                      placeholder="e.g. 204"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Floor Number *
                    </label>
                    <input
                      required
                      type="number"
                      value={formData.floor_number || 1}
                      onChange={(e) =>
                        setFormData({ ...formData, floor_number: parseInt(e.target.value) || 1 })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Unit Type *
                    </label>
                    <select
                      value={formData.unit_type}
                      onChange={(e) => {
                        const ut = e.target.value as UnitType;
                        let cap = 2;
                        if (ut === "SINGLE_OCCUPANCY") cap = 1;
                        else if (ut === "TRIPLE_OCCUPANCY") cap = 3;
                        else if (ut === "DORMITORY") cap = 4;
                        setFormData({
                          ...formData,
                          unit_type: ut,
                          bed_capacity: cap,
                        });
                      }}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    >
                      <option value="SINGLE_OCCUPANCY">Single Occupancy (1 Bed)</option>
                      <option value="DOUBLE_OCCUPANCY">Double Occupancy (2 Beds)</option>
                      <option value="TRIPLE_OCCUPANCY">Triple Occupancy (3 Beds)</option>
                      <option value="DORMITORY">Dormitory (4+ Beds)</option>
                      <option value="STUDIO_APARTMENT">Studio Apartment</option>
                      <option value="MULTI_BED_APARTMENT">Multi-Bed Apartment</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Bed Capacity
                    </label>
                    <input
                      type="number"
                      value={formData.bed_capacity}
                      onChange={(e) =>
                        setFormData({ ...formData, bed_capacity: parseInt(e.target.value) || 1 })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Monthly Rent Per Bed (₹) *
                    </label>
                    <input
                      required
                      type="number"
                      value={formData.rent_per_bed}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          rent_per_bed: parseFloat(e.target.value) || 0,
                        })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Security Deposit Per Bed (₹) *
                    </label>
                    <input
                      required
                      type="number"
                      value={formData.security_deposit_per_bed}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          security_deposit_per_bed: parseFloat(e.target.value) || 0,
                        })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    />
                  </div>
                </div>

                <div className="space-y-2 border-t border-slate-800 pt-3">
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Unit Features
                  </h4>
                  <div className="grid grid-cols-3 gap-2 text-xs text-slate-300">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={formData.has_attached_bath}
                        onChange={(e) =>
                          setFormData({ ...formData, has_attached_bath: e.target.checked })
                        }
                        className="rounded bg-slate-950 border-slate-800 text-indigo-600"
                      />
                      Attached Bath
                    </label>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={formData.is_furnished}
                        onChange={(e) =>
                          setFormData({ ...formData, is_furnished: e.target.checked })
                        }
                        className="rounded bg-slate-950 border-slate-800 text-indigo-600"
                      />
                      Furnished
                    </label>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={formData.is_accessible}
                        onChange={(e) =>
                          setFormData({ ...formData, is_accessible: e.target.checked })
                        }
                        className="rounded bg-slate-950 border-slate-800 text-indigo-600"
                      />
                      ♿ Accessible
                    </label>
                  </div>
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="px-4 py-2 text-xs font-medium rounded-md bg-slate-800 text-slate-300 hover:bg-slate-700"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 text-xs font-medium rounded-md bg-indigo-600 hover:bg-indigo-500 text-white"
                  >
                    Generate Unit & Beds
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
