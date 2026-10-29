"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Building2,
  ExternalLink,
  Globe,
  Mail,
  MapPin,
  Phone,
  Plus,
  Search,
  ShieldCheck,
  X,
} from "lucide-react";
import { InternationalNav } from "@/components/international/international-nav";
import { internationalService } from "@/services/international.service";
import { InternationalPartner, PartnershipCategory } from "@/types/international";

export default function PartnersDirectoryPage() {
  const [partners, setPartners] = useState<InternationalPartner[]>([]);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("ALL");
  const [countryFilter, setCountryFilter] = useState<string>("ALL");
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);

  // New Partner Form State
  const [formData, setFormData] = useState({
    partner_name: "",
    country_name: "",
    country_code: "",
    city: "",
    official_website: "",
    category: "UNIVERSITY" as PartnershipCategory,
    primary_contact_name: "",
    primary_contact_email: "",
    primary_contact_phone: "",
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadPartners();
  }, [categoryFilter, countryFilter]);

  async function loadPartners() {
    setLoading(true);
    try {
      const data = await internationalService.getPartners({
        category: categoryFilter !== "ALL" ? categoryFilter : undefined,
        country_code: countryFilter !== "ALL" ? countryFilter : undefined,
        search: search || undefined,
      });
      setPartners(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleAddPartner(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await internationalService.createPartner(formData);
      setPartners([res, ...partners]);
      setShowAddModal(false);
      setFormData({
        partner_name: "",
        country_name: "",
        country_code: "",
        city: "",
        official_website: "",
        category: "UNIVERSITY",
        primary_contact_name: "",
        primary_contact_email: "",
        primary_contact_phone: "",
      });
    } catch (err) {
      console.error(err);
      alert("Failed to register partner. Check console for details.");
    } finally {
      setSubmitting(false);
    }
  }

  const countries = Array.from(new Set(partners.map((p) => p.country_name || p.country || p.countryName || "Unknown"))).filter(Boolean);

  const filteredPartners = partners.filter((p) => {
    const nameMatch = (p.partner_name || p.name || "").toLowerCase().includes(search.toLowerCase());
    const cityMatch = (p.city || "").toLowerCase().includes(search.toLowerCase());
    const countryMatch = (p.country_name || p.country || "").toLowerCase().includes(search.toLowerCase());
    return nameMatch || cityMatch || countryMatch;
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <InternationalNav />

      <main className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <Building2 className="h-5 w-5 text-cyan-400" />
              Partner Institutions Registry
            </h2>
            <p className="text-xs text-slate-400">
              Accredited global universities, international research laboratories, and academic consortiums
            </p>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-3.5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md shadow-cyan-900/30 flex items-center gap-2 transition-all self-start sm:self-auto"
          >
            <Plus className="h-4 w-4" />
            Register Partner Institution
          </button>
        </div>

        {/* Filters Bar */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col md:flex-row items-center gap-4">
          <div className="relative flex-1 w-full">
            <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search partner by name, city, or country..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div className="flex items-center gap-3 w-full md:w-auto">
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="ALL">All Categories</option>
              <option value="UNIVERSITY">University</option>
              <option value="COLLEGE">College</option>
              <option value="RESEARCH_INSTITUTE">Research Institute</option>
              <option value="ACADEMIC_EXCHANGE">Academic Exchange</option>
              <option value="DUAL_DEGREE_CONSORTIUM">Dual Degree</option>
            </select>

            <select
              value={countryFilter}
              onChange={(e) => setCountryFilter(e.target.value)}
              className="px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="ALL">All Countries</option>
              {countries.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Partner Cards Grid */}
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-500">Loading partner directory...</div>
        ) : filteredPartners.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500 bg-slate-900/40 rounded-xl border border-slate-800">
            No partner institutions matching your filter criteria.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filteredPartners.map((partner) => (
              <div
                key={partner.id}
                className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-cyan-500/40 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold tracking-wider px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                      {partner.category || partner.partnership_category || "UNIVERSITY"}
                    </span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                        partner.is_active || partner.status === "ACTIVE"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-slate-800 text-slate-400"
                      }`}
                    >
                      {partner.is_active || partner.status === "ACTIVE" ? "Active" : "Inactive"}
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-white mt-3 line-clamp-1">
                    {partner.partner_name || partner.name}
                  </h3>

                  <p className="text-xs text-slate-400 mt-1 flex items-center gap-1.5">
                    <MapPin className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
                    <span>
                      {partner.city ? `${partner.city}, ` : ""}
                      {partner.country_name || partner.country || partner.country_code}
                    </span>
                  </p>

                  <div className="mt-4 pt-3 border-t border-slate-800/80 space-y-1.5 text-xs text-slate-300">
                    {partner.primary_contact_name && (
                      <p className="flex items-center gap-2">
                        <span className="text-slate-500">Contact:</span>
                        <span className="text-slate-300">{partner.primary_contact_name}</span>
                      </p>
                    )}
                    {partner.primary_contact_email && (
                      <p className="flex items-center gap-2 truncate">
                        <Mail className="h-3 w-3 text-slate-500 shrink-0" />
                        <span className="truncate">{partner.primary_contact_email}</span>
                      </p>
                    )}
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-slate-800 flex items-center justify-between">
                  {partner.official_website ? (
                    <a
                      href={partner.official_website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
                    >
                      Website
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  ) : (
                    <span className="text-xs text-slate-600">No URL</span>
                  )}

                  <Link
                    href={`/app/international/partners/${partner.id}`}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-medium transition-colors"
                  >
                    View MoUs &rarr;
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Add Partner Modal */}
        {showAddModal && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 shadow-2xl relative">
              <button
                onClick={() => setShowAddModal(false)}
                className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>

              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Building2 className="h-4 w-4 text-cyan-400" />
                Register International Partner Institution
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Add an accredited foreign university or international research organization to CampusOS
              </p>

              <form onSubmit={handleAddPartner} className="mt-5 space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="sm:col-span-2">
                    <label className="text-xs font-medium text-slate-300 block mb-1">Institution Name *</label>
                    <input
                      required
                      type="text"
                      placeholder="e.g. University of Tokyo"
                      value={formData.partner_name}
                      onChange={(e) => setFormData({ ...formData, partner_name: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Country Name *</label>
                    <input
                      required
                      type="text"
                      placeholder="e.g. Japan"
                      value={formData.country_name}
                      onChange={(e) => setFormData({ ...formData, country_name: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Country Code (ISO-2) *</label>
                    <input
                      required
                      type="text"
                      maxLength={3}
                      placeholder="e.g. JP"
                      value={formData.country_code}
                      onChange={(e) => setFormData({ ...formData, country_code: e.target.value.toUpperCase() })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white uppercase focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">City</label>
                    <input
                      type="text"
                      placeholder="e.g. Tokyo"
                      value={formData.city}
                      onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Partnership Category</label>
                    <select
                      value={formData.category}
                      onChange={(e) => setFormData({ ...formData, category: e.target.value as PartnershipCategory })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    >
                      <option value="UNIVERSITY">University</option>
                      <option value="COLLEGE">College</option>
                      <option value="RESEARCH_INSTITUTE">Research Institute</option>
                      <option value="ACADEMIC_EXCHANGE">Academic Exchange</option>
                      <option value="DUAL_DEGREE_CONSORTIUM">Dual Degree</option>
                    </select>
                  </div>

                  <div className="sm:col-span-2">
                    <label className="text-xs font-medium text-slate-300 block mb-1">Official Website</label>
                    <input
                      type="url"
                      placeholder="https://..."
                      value={formData.official_website}
                      onChange={(e) => setFormData({ ...formData, official_website: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Primary Contact Name</label>
                    <input
                      type="text"
                      placeholder="e.g. Prof. Taro Yamada"
                      value={formData.primary_contact_name}
                      onChange={(e) => setFormData({ ...formData, primary_contact_name: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Primary Contact Email</label>
                    <input
                      type="email"
                      placeholder="international@partner.ac.jp"
                      value={formData.primary_contact_email}
                      onChange={(e) => setFormData({ ...formData, primary_contact_email: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                </div>

                <div className="mt-6 flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md shadow-cyan-900/30 disabled:opacity-50"
                  >
                    {submitting ? "Registering..." : "Register Partner"}
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
