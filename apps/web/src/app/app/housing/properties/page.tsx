"use client";

import { useEffect, useState } from "react";
import {
  Building2 as BuildingOffice2Icon,
  Plus as PlusIcon,
  Filter as FunnelIcon,
  Search as MagnifyingGlassIcon,
  MapPin as MapPinIcon,
  CheckCircle2 as CheckCircleIcon,
  AlertTriangle as ExclamationTriangleIcon,
  X as XMarkIcon,
} from "lucide-react";
import { HousingNav } from "@/components/housing/housing-nav";
import { HousingService } from "@/services/housing.service";
import {
  AccommodationProperty,
  AccommodationProvider,
  PropertyCreateInput,
  PropertyLifecycleStatus,
  PropertyType,
} from "@/types/housing";

export default function PropertiesDirectoryPage() {
  const [properties, setProperties] = useState<AccommodationProperty[]>([]);
  const [providers, setProviders] = useState<AccommodationProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isTransitioning, setIsTransitioning] = useState<string | null>(null);

  // New property form state
  const [formData, setFormData] = useState<PropertyCreateInput>({
    code: "",
    name: "",
    slug: "",
    property_type: "CAMPUS_HOSTEL",
    address: "",
    city: "Bengaluru",
    state: "Karnataka",
    postal_code: "560100",
    distance_to_campus_km: 0.5,
    monthly_rent_min: 7500,
    monthly_rent_max: 12000,
    security_deposit_amount: 15000,
    amenities: ["WIFI", "AIR_CONDITIONING", "MESS_FACILITY"],
    utilities_included: ["WATER", "ELECTRICITY"],
    accessibility_features: ["WHEELCHAIR_RAMP"],
    safety_features: ["CCTV", "24x7_SECURITY"],
  });

  const loadData = async () => {
    try {
      const [props, provs] = await Promise.all([
        HousingService.listProperties(false),
        HousingService.listProviders(),
      ]);
      setProperties(props);
      setProviders(provs);
    } catch (err) {
      console.error("Failed to load properties", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await HousingService.createProperty(formData);
      setIsModalOpen(false);
      loadData();
    } catch (err) {
      alert("Failed to create property: " + (err as Error).message);
    }
  };

  const handleTransition = async (propertyId: string, targetStatus: PropertyLifecycleStatus) => {
    setIsTransitioning(propertyId);
    try {
      await HousingService.transitionProperty(propertyId, { target_status: targetStatus });
      await loadData();
    } catch (err) {
      alert("Transition failed: " + (err as Error).message);
    } finally {
      setIsTransitioning(null);
    }
  };

  const filteredProperties = properties.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.code.toLowerCase().includes(search.toLowerCase()) ||
      p.address.toLowerCase().includes(search.toLowerCase());
    const matchesType = typeFilter === "ALL" || p.property_type === typeFilter;
    const matchesStatus = statusFilter === "ALL" || p.lifecycle_status === statusFilter;
    return matchesSearch && matchesType && matchesStatus;
  });

  return (
    <div className="min-h-screen bg-gray-50 pb-12">
      <HousingNav
        title="Accommodation Properties & Residence Halls"
        subtitle="Vetted on-campus halls, approved private accommodations, and student apartment complexes"
      />

      <div className="max-w-7xl mx-auto px-6 space-y-6">
        {/* Controls Bar */}
        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex flex-1 items-center gap-3">
            <div className="relative flex-1 max-w-md">
              <MagnifyingGlassIcon className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Search by property name, code, or address..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="border border-gray-200 rounded-lg px-3 py-2 text-xs text-gray-700 bg-white"
            >
              <option value="ALL">All Types</option>
              <option value="CAMPUS_HOSTEL">Campus Hostel</option>
              <option value="OFF_CAMPUS_HOSTEL">Off-Campus Hostel</option>
              <option value="STUDENT_VILLAGE">Student Village</option>
              <option value="PRIVATE_APARTMENT">Private Apartment</option>
            </select>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="border border-gray-200 rounded-lg px-3 py-2 text-xs text-gray-700 bg-white"
            >
              <option value="ALL">All Statuses</option>
              <option value="PUBLISHED">Published (Discoverable)</option>
              <option value="APPROVED">Approved</option>
              <option value="PENDING_REVIEW">Pending Review</option>
              <option value="DRAFT">Draft</option>
              <option value="SUSPENDED">Suspended</option>
            </select>
          </div>

          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs transition shadow-sm"
          >
            <PlusIcon className="w-4 h-4" />
            Add Property
          </button>
        </div>

        {/* Properties Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProperties.map((prop) => {
            const occupancyRate =
              prop.total_bed_capacity > 0
                ? Math.round((prop.occupied_beds / prop.total_bed_capacity) * 100)
                : 0;

            return (
              <div
                key={prop.id}
                className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition overflow-hidden flex flex-col justify-between"
              >
                <div className="p-5">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                        {prop.code}
                      </span>
                      <h3 className="font-bold text-gray-900 text-base mt-1.5 leading-snug">
                        {prop.name}
                      </h3>
                    </div>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        prop.lifecycle_status === "PUBLISHED"
                          ? "bg-emerald-100 text-emerald-800"
                          : prop.lifecycle_status === "APPROVED"
                          ? "bg-blue-100 text-blue-800"
                          : prop.lifecycle_status === "SUSPENDED"
                          ? "bg-rose-100 text-rose-800"
                          : "bg-gray-100 text-gray-700"
                      }`}
                    >
                      {prop.lifecycle_status}
                    </span>
                  </div>

                  <p className="text-xs text-gray-500 mt-2 line-clamp-2">{prop.description}</p>

                  <div className="flex items-center gap-1.5 mt-3 text-xs text-gray-600">
                    <MapPinIcon className="w-4 h-4 text-gray-400 shrink-0" />
                    <span className="truncate">{prop.address}</span>
                  </div>

                  {/* Bed stats */}
                  <div className="grid grid-cols-3 gap-2 mt-4 p-3 bg-gray-50 rounded-lg text-center border border-gray-100">
                    <div>
                      <span className="text-[10px] font-medium text-gray-500 block">Total Beds</span>
                      <span className="text-sm font-bold text-gray-900">{prop.total_bed_capacity}</span>
                    </div>
                    <div>
                      <span className="text-[10px] font-medium text-gray-500 block">Occupied</span>
                      <span className="text-sm font-bold text-amber-700">{prop.occupied_beds}</span>
                    </div>
                    <div>
                      <span className="text-[10px] font-medium text-gray-500 block">Available</span>
                      <span className="text-sm font-bold text-emerald-700">{prop.available_beds}</span>
                    </div>
                  </div>

                  {/* Pricing and Distance */}
                  <div className="flex items-center justify-between text-xs mt-4 pt-3 border-t border-gray-100">
                    <span className="text-gray-500">Rent Range:</span>
                    <span className="font-bold text-gray-900">
                      ₹{prop.monthly_rent_min.toLocaleString()} - ₹{prop.monthly_rent_max.toLocaleString()} / mo
                    </span>
                  </div>
                </div>

                {/* Card Actions & Lifecycle State Buttons */}
                <div className="bg-gray-50 px-5 py-3 border-t border-gray-100 flex items-center justify-between gap-2">
                  <span className="text-[11px] text-gray-500">
                    {prop.distance_to_campus_km} km to campus
                  </span>
                  <div className="flex items-center gap-1.5">
                    {prop.lifecycle_status === "DRAFT" && (
                      <button
                        onClick={() => handleTransition(prop.id, "PENDING_REVIEW")}
                        className="px-2.5 py-1 bg-amber-500 hover:bg-amber-600 text-white rounded text-[11px] font-medium"
                      >
                        Submit Review
                      </button>
                    )}
                    {prop.lifecycle_status === "PENDING_REVIEW" && (
                      <button
                        onClick={() => handleTransition(prop.id, "APPROVED")}
                        className="px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-[11px] font-medium"
                      >
                        Approve
                      </button>
                    )}
                    {prop.lifecycle_status === "APPROVED" && (
                      <button
                        onClick={() => handleTransition(prop.id, "PUBLISHED")}
                        className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-[11px] font-medium"
                      >
                        Publish
                      </button>
                    )}
                    {prop.lifecycle_status === "PUBLISHED" && (
                      <button
                        onClick={() => handleTransition(prop.id, "SUSPENDED")}
                        className="px-2.5 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded text-[11px] font-medium"
                      >
                        Suspend
                      </button>
                    )}
                    {prop.lifecycle_status === "SUSPENDED" && (
                      <button
                        onClick={() => handleTransition(prop.id, "APPROVED")}
                        className="px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-[11px] font-medium"
                      >
                        Re-Approve
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Add Property Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-5 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-bold text-gray-900 text-base">Register Accommodation Property</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreate} className="p-5 space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-gray-700 block mb-1">Property Code *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. SAP-CRT"
                    value={formData.code}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        code: e.target.value.toUpperCase(),
                        slug: e.target.value.toLowerCase(),
                      })
                    }
                    className="w-full p-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="font-semibold text-gray-700 block mb-1">Property Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Sapphire Court"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full p-2 border rounded-lg"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-gray-700 block mb-1">Property Type</label>
                  <select
                    value={formData.property_type}
                    onChange={(e) =>
                      setFormData({ ...formData, property_type: e.target.value as PropertyType })
                    }
                    className="w-full p-2 border rounded-lg bg-white"
                  >
                    <option value="CAMPUS_HOSTEL">Campus Hostel (On-Site)</option>
                    <option value="OFF_CAMPUS_HOSTEL">Off-Campus Hostel</option>
                    <option value="STUDENT_VILLAGE">Student Village</option>
                    <option value="PRIVATE_APARTMENT">Private Apartment</option>
                  </select>
                </div>
                <div>
                  <label className="font-semibold text-gray-700 block mb-1">Provider / Landlord</label>
                  <select
                    value={formData.provider_id || ""}
                    onChange={(e) => setFormData({ ...formData, provider_id: e.target.value || undefined })}
                    className="w-full p-2 border rounded-lg bg-white"
                  >
                    <option value="">Institution Managed</option>
                    {providers.map((pr) => (
                      <option key={pr.id} value={pr.id}>
                        {pr.name} ({pr.provider_type})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="font-semibold text-gray-700 block mb-1">Address *</label>
                <input
                  type="text"
                  required
                  placeholder="Street address, sector or block"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  className="w-full p-2 border rounded-lg"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="font-semibold text-gray-700 block mb-1">Distance (km)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.distance_to_campus_km}
                    onChange={(e) =>
                      setFormData({ ...formData, distance_to_campus_km: parseFloat(e.target.value) || 0 })
                    }
                    className="w-full p-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="font-semibold text-gray-700 block mb-1">Min Rent (₹/mo)</label>
                  <input
                    type="number"
                    value={formData.monthly_rent_min}
                    onChange={(e) =>
                      setFormData({ ...formData, monthly_rent_min: parseInt(e.target.value) || 0 })
                    }
                    className="w-full p-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="font-semibold text-gray-700 block mb-1">Max Rent (₹/mo)</label>
                  <input
                    type="number"
                    value={formData.monthly_rent_max}
                    onChange={(e) =>
                      setFormData({ ...formData, monthly_rent_max: parseInt(e.target.value) || 0 })
                    }
                    className="w-full p-2 border rounded-lg"
                  />
                </div>
              </div>

              <div>
                <label className="font-semibold text-gray-700 block mb-1">Description</label>
                <textarea
                  rows={3}
                  placeholder="Overview of amenities, student policies, quiet hours..."
                  value={formData.description || ""}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full p-2 border rounded-lg"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-gray-100">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 border rounded-lg text-gray-600 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-semibold"
                >
                  Save Property
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

