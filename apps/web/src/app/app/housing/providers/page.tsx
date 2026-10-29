"use client";

import { useEffect, useState } from "react";
import {
  ShieldCheck,
  Plus,
  Search,
  Filter,
  Mail,
  Phone,
  FileCheck2,
  AlertCircle,
  CheckCircle2,
  X,
  Star,
} from "lucide-react";
import { HousingNav } from "@/components/housing/housing-nav";
import { HousingService } from "@/services/housing.service";
import {
  AccommodationProvider,
  ProviderCreateInput,
  ProviderType,
  ProviderVerificationStatus,
} from "@/types/housing";

export default function ProvidersDirectoryPage() {
  const [providers, setProviders] = useState<AccommodationProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const [formData, setFormData] = useState<ProviderCreateInput>({
    name: "",
    slug: "",
    provider_type: "HOUSING_COMPANY",
    contact_name: "",
    contact_email: "",
    contact_phone: "",
    emergency_phone: "",
    tax_id: "",
    address: "",
    city: "Bengaluru",
    state: "Karnataka",
    mou_reference: "",
    mou_valid_from: "2026-06-01",
    mou_valid_to: "2027-05-31",
  });

  const loadProviders = async () => {
    try {
      const data = await HousingService.listProviders();
      setProviders(data);
    } catch (err) {
      console.error("Failed to load providers", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProviders();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload: ProviderCreateInput = {
        ...formData,
        slug: formData.slug || formData.name.toLowerCase().replace(/[^a-z0-9]+/g, "-"),
      };
      await HousingService.createProvider(payload);
      setIsModalOpen(false);
      setFormData({
        name: "",
        slug: "",
        provider_type: "HOUSING_COMPANY",
        contact_name: "",
        contact_email: "",
        contact_phone: "",
        emergency_phone: "",
        tax_id: "",
        address: "",
        city: "Bengaluru",
        state: "Karnataka",
        mou_reference: "",
        mou_valid_from: "2026-06-01",
        mou_valid_to: "2027-05-31",
      });
      loadProviders();
    } catch (err) {
      alert("Failed to create provider: " + (err as Error).message);
    }
  };

  const handleVerify = async (id: string, isVerified: boolean) => {
    setActionLoading(id);
    try {
      await HousingService.verifyProvider(id, isVerified);
      await loadProviders();
    } catch (err) {
      alert("Action failed: " + (err as Error).message);
    } finally {
      setActionLoading(null);
    }
  };

  const filteredProviders = providers.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.contact_name.toLowerCase().includes(search.toLowerCase()) ||
      p.contact_email.toLowerCase().includes(search.toLowerCase()) ||
      (p.tax_id && p.tax_id.toLowerCase().includes(search.toLowerCase()));

    const matchesType = typeFilter === "ALL" || p.provider_type === typeFilter;
    const matchesStatus =
      statusFilter === "ALL" || p.verification_status === statusFilter;

    return matchesSearch && matchesType && matchesStatus;
  });

  const getStatusBadge = (status: ProviderVerificationStatus) => {
    switch (status) {
      case "VERIFIED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Verified Partner
          </span>
        );
      case "PENDING":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <AlertCircle className="w-3.5 h-3.5" />
            Pending Due Diligence
          </span>
        );
      case "SUSPENDED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">
            Suspended
          </span>
        );
      case "TERMINATED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-500/10 text-slate-400 border border-slate-500/30">
            Terminated
          </span>
        );
      default:
        return null;
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
              <ShieldCheck className="w-7 h-7 text-indigo-400" />
              Accommodation Providers & Landlord Directory
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Accredited private landlords, university trusts, and corporate accommodation operators with vetted institutional MoUs.
            </p>
          </div>

          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            Add Provider / Landlord
          </button>
        </div>

        {/* Filter bar */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="relative md:col-span-2">
            <Search className="w-5 h-5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search providers by organization, contact person, email, or GSTIN..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-300 focus:outline-none focus:border-indigo-500"
            >
              <option value="ALL">All Provider Types</option>
              <option value="HOUSING_COMPANY">Housing Company</option>
              <option value="PRIVATE_LANDLORD">Private Landlord</option>
              <option value="STUDENT_RESIDENCE_TRUST">Student Residence Trust</option>
              <option value="UNIVERSITY_AFFILIATE">University Affiliate</option>
              <option value="HOMESTAY_HOST">Homestay Host</option>
            </select>
          </div>

          <div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-300 focus:outline-none focus:border-indigo-500"
            >
              <option value="ALL">All Statuses</option>
              <option value="VERIFIED">Verified</option>
              <option value="PENDING">Pending Review</option>
              <option value="SUSPENDED">Suspended</option>
              <option value="TERMINATED">Terminated</option>
            </select>
          </div>
        </div>

        {/* Providers list */}
        {loading ? (
          <div className="py-20 text-center text-slate-400">Loading providers and verification profiles...</div>
        ) : filteredProviders.length === 0 ? (
          <div className="py-16 text-center border border-dashed border-slate-800 rounded-xl bg-slate-900/30">
            <p className="text-slate-400">No accommodation providers found matching your filter criteria.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProviders.map((prov) => (
              <div
                key={prov.id}
                className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 flex flex-col justify-between hover:border-slate-700 transition-all shadow-sm"
              >
                <div className="space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h3 className="text-base font-semibold text-white leading-tight">
                        {prov.name}
                      </h3>
                      <p className="text-xs text-indigo-400 font-medium mt-0.5">
                        {prov.provider_type.replace(/_/g, " ")}
                      </p>
                    </div>
                    {getStatusBadge(prov.verification_status)}
                  </div>

                  {/* Rating & MoU */}
                  <div className="flex items-center justify-between text-xs text-slate-400 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/60">
                    <div className="flex items-center gap-1 text-amber-400 font-semibold">
                      <Star className="w-4 h-4 fill-amber-400" />
                      <span>{prov.rating ? prov.rating.toFixed(1) : "N/A"} / 5.0</span>
                    </div>
                    {prov.mou_reference && (
                      <div className="flex items-center gap-1 text-slate-300">
                        <FileCheck2 className="w-4 h-4 text-emerald-400" />
                        <span>MoU: {prov.mou_reference}</span>
                      </div>
                    )}
                  </div>

                  {/* Contact details */}
                  <div className="space-y-1.5 text-xs text-slate-300">
                    <p className="font-medium text-slate-200">Contact: {prov.contact_name}</p>
                    <div className="flex items-center gap-2 text-slate-400">
                      <Mail className="w-3.5 h-3.5" />
                      <span className="truncate">{prov.contact_email}</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-400">
                      <Phone className="w-3.5 h-3.5" />
                      <span>{prov.contact_phone}</span>
                    </div>
                    {prov.emergency_phone && (
                      <div className="text-rose-400 font-mono text-[11px]">
                        Emergency Line: {prov.emergency_phone}
                      </div>
                    )}
                  </div>

                  {prov.tax_id && (
                    <div className="text-[11px] font-mono text-slate-500">
                      GST / Tax ID: {prov.tax_id}
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="pt-4 mt-4 border-t border-slate-800/80 flex items-center justify-end gap-2">
                  {prov.verification_status === "PENDING" && (
                    <>
                      <button
                        disabled={actionLoading === prov.id}
                        onClick={() => handleVerify(prov.id, true)}
                        className="px-3 py-1.5 text-xs font-medium rounded-md bg-emerald-600 hover:bg-emerald-500 text-white transition-colors"
                      >
                        Approve MoU
                      </button>
                      <button
                        disabled={actionLoading === prov.id}
                        onClick={() => handleVerify(prov.id, false)}
                        className="px-3 py-1.5 text-xs font-medium rounded-md bg-rose-600/20 text-rose-300 hover:bg-rose-600/40 border border-rose-500/30 transition-colors"
                      >
                        Suspend
                      </button>
                    </>
                  )}
                  {prov.verification_status === "VERIFIED" && (
                    <button
                      disabled={actionLoading === prov.id}
                      onClick={() => handleVerify(prov.id, false)}
                      className="px-3 py-1.5 text-xs font-medium rounded-md bg-amber-600/20 text-amber-300 hover:bg-amber-600/30 border border-amber-500/30 transition-colors"
                    >
                      Suspend Partnership
                    </button>
                  )}
                  {prov.verification_status === "SUSPENDED" && (
                    <button
                      disabled={actionLoading === prov.id}
                      onClick={() => handleVerify(prov.id, true)}
                      className="px-3 py-1.5 text-xs font-medium rounded-md bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600/40 border border-indigo-500/30 transition-colors"
                    >
                      Re-Instate
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Modal for new provider */}
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
            <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-xl w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto shadow-2xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h2 className="text-lg font-bold text-white">Add Accommodation Provider / Landlord</h2>
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="text-slate-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleCreate} className="space-y-4 text-sm">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Organization / Landlord Name *
                  </label>
                  <input
                    required
                    type="text"
                    value={formData.name}
                    onChange={(e) =>
                      setFormData({ ...formData, name: e.target.value })
                    }
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200 focus:outline-none focus:border-indigo-500"
                    placeholder="e.g. Apex Living Student Spaces Ltd"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Provider Category *
                    </label>
                    <select
                      value={formData.provider_type}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          provider_type: e.target.value as ProviderType,
                        })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200 focus:outline-none focus:border-indigo-500"
                    >
                      <option value="HOUSING_COMPANY">Housing Company</option>
                      <option value="PRIVATE_LANDLORD">Private Landlord</option>
                      <option value="STUDENT_RESIDENCE_TRUST">Student Residence Trust</option>
                      <option value="UNIVERSITY_AFFILIATE">University Affiliate</option>
                      <option value="HOMESTAY_HOST">Homestay Host</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      City
                    </label>
                    <input
                      type="text"
                      value={formData.city || ""}
                      onChange={(e) =>
                        setFormData({ ...formData, city: e.target.value })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                      placeholder="e.g. Bengaluru"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      GSTIN / Tax ID
                    </label>
                    <input
                      type="text"
                      value={formData.tax_id || ""}
                      onChange={(e) =>
                        setFormData({ ...formData, tax_id: e.target.value })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200 font-mono"
                      placeholder="29AAAAA0000A1Z5"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Institutional MoU Ref No
                    </label>
                    <input
                      type="text"
                      value={formData.mou_reference || ""}
                      onChange={(e) =>
                        setFormData({ ...formData, mou_reference: e.target.value })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200 font-mono"
                      placeholder="MOU-VSB-2026-H04"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      MoU Valid From
                    </label>
                    <input
                      type="date"
                      value={formData.mou_valid_from}
                      onChange={(e) =>
                        setFormData({ ...formData, mou_valid_from: e.target.value })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      MoU Valid To
                    </label>
                    <input
                      type="date"
                      value={formData.mou_valid_to}
                      onChange={(e) =>
                        setFormData({ ...formData, mou_valid_to: e.target.value })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    />
                  </div>
                </div>

                <div className="border-t border-slate-800 pt-3">
                  <h4 className="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">
                    Contact & Emergency Channels
                  </h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">
                        Contact Person *
                      </label>
                      <input
                        required
                        type="text"
                        value={formData.contact_name}
                        onChange={(e) =>
                          setFormData({ ...formData, contact_name: e.target.value })
                        }
                        className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">
                        Contact Email *
                      </label>
                      <input
                        required
                        type="email"
                        value={formData.contact_email}
                        onChange={(e) =>
                          setFormData({ ...formData, contact_email: e.target.value })
                        }
                        className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mt-3">
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">
                        Phone Number *
                      </label>
                      <input
                        required
                        type="tel"
                        value={formData.contact_phone}
                        onChange={(e) =>
                          setFormData({ ...formData, contact_phone: e.target.value })
                        }
                        className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">
                        Emergency 24x7 Helpline
                      </label>
                      <input
                        type="tel"
                        value={formData.emergency_phone || ""}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            emergency_phone: e.target.value,
                          })
                        }
                        className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                      />
                    </div>
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
                    Save & Submit for Verification
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
