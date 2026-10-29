"use client";

import { useEffect, useState } from "react";
import {
  Building2,
  Calendar,
  Clock,
  FileCheck2,
  Mail,
  MapPin,
  Phone,
  PlusCircle,
  Search,
  ShieldCheck,
  TrendingUp,
  Users2,
  X,
} from "lucide-react";
import { EngagementNav } from "@/components/engagement/engagement-nav";
import { EngagementService } from "@/services/engagement.service";
import { CommunityPartner, PartnerCreateInput } from "@/types/engagement";

export default function EngagementPartnersPage() {
  const [partners, setPartners] = useState<CommunityPartner[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [selectedPartner, setSelectedPartner] = useState<CommunityPartner | null>(null);

  // Form State
  const [name, setName] = useState("");
  const [orgType, setOrgType] = useState("Non-Governmental Organization (NGO)");
  const [contactPerson, setContactPerson] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [mouRef, setMouRef] = useState("");
  const [validFrom, setValidFrom] = useState(new Date().toISOString().split("T")[0]);
  const [validTo, setValidTo] = useState(
    new Date(Date.now() + 365 * 86400000).toISOString().split("T")[0]
  );
  const [purpose, setPurpose] = useState("");
  const [city, setCity] = useState("Chennai");
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  useEffect(() => {
    loadPartners();
  }, []);

  async function loadPartners() {
    setLoading(true);
    try {
      const data = await EngagementService.listPartners();
      setPartners(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function handleRegisterPartner(e: React.FormEvent) {
    e.preventDefault();
    if (!name || !contactEmail) return;

    try {
      const input: PartnerCreateInput = {
        name,
        slug: name.toLowerCase().replace(/[^a-z0-9]+/g, "-"),
        organization_type: orgType,
        contact_person_name: contactPerson,
        contact_email: contactEmail,
        contact_phone: contactPhone,
        mou_reference: mouRef,
        mou_valid_from: validFrom,
        mou_valid_to: validTo,
        purpose_statement: purpose,
        city,
        state: "Tamil Nadu",
      };

      await EngagementService.createPartner(input);
      setActionMessage("Community partner registered successfully.");
      setIsRegisterOpen(false);
      resetForm();
      await loadPartners();
    } catch (err: any) {
      setActionMessage(`Error registering partner: ${err.message}`);
    }
  }

  function resetForm() {
    setName("");
    setContactPerson("");
    setContactEmail("");
    setContactPhone("");
    setMouRef("");
    setPurpose("");
  }

  const filteredPartners = partners.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.contact_person_name.toLowerCase().includes(search.toLowerCase()) ||
      (p.purpose_statement && p.purpose_statement.toLowerCase().includes(search.toLowerCase()));

    const matchesStatus = statusFilter === "ALL" || p.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="min-h-screen bg-background">
      <EngagementNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {actionMessage && (
          <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-medium flex items-center justify-between">
            <span>{actionMessage}</span>
            <button onClick={() => setActionMessage(null)} className="text-muted-foreground hover:text-foreground">
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <Users2 className="h-6 w-6 text-blue-500" />
              Community Partner Directory
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Verified NGOs, non-profits, healthcare foundations, and civic bodies with active MoUs
            </p>
          </div>

          <button
            onClick={() => setIsRegisterOpen(true)}
            className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-semibold shadow hover:opacity-95"
          >
            <PlusCircle className="h-4 w-4" />
            <span>Register Partner</span>
          </button>
        </div>

        {/* Search & Filters */}
        <div className="bg-card border border-border rounded-xl p-4 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 shadow-sm">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search partner by name, contact, or mission..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-lg border border-border bg-background text-xs focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          <div className="flex items-center space-x-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 rounded-lg border border-border bg-background text-xs text-foreground focus:outline-none"
            >
              <option value="ALL">All Statuses</option>
              <option value="ACTIVE">Active MoU</option>
              <option value="UNDER_REVIEW">Under Review</option>
              <option value="SUSPENDED">Suspended</option>
            </select>
          </div>
        </div>

        {/* Partners Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredPartners.map((partner) => (
            <div
              key={partner.id}
              className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-4 hover:border-blue-500/50 transition-all flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-500 font-semibold border border-blue-500/20">
                    {partner.organization_type}
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500 font-bold">
                    {partner.status}
                  </span>
                </div>

                <div>
                  <h3 className="text-base font-bold text-foreground line-clamp-1">{partner.name}</h3>
                  <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                    {partner.purpose_statement || "Community service and social impact collaborator."}
                  </p>
                </div>

                {/* MoU & Representative Details */}
                <div className="space-y-1.5 text-xs text-muted-foreground border-t border-border pt-3">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <FileCheck2 className="h-3.5 w-3.5" /> MoU Ref:
                    </span>
                    <span className="text-foreground font-mono font-medium">
                      {partner.mou_reference || "MOU-ACTIVE"}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Mail className="h-3.5 w-3.5" /> Contact:
                    </span>
                    <span className="text-foreground font-medium truncate max-w-[150px]">
                      {partner.contact_person_name}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Clock className="h-3.5 w-3.5" /> Total Verified Hours:
                    </span>
                    <span className="text-foreground font-bold text-emerald-500">
                      {partner.verified_hours_contributed} hrs
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Users2 className="h-3.5 w-3.5" /> Volunteers Engaged:
                    </span>
                    <span className="text-foreground font-semibold">
                      {partner.total_volunteers_engaged}
                    </span>
                  </div>
                </div>
              </div>

              <div className="border-t border-border pt-3 flex justify-end">
                <button
                  onClick={() => setSelectedPartner(partner)}
                  className="px-3 py-1.5 rounded-lg border border-border text-foreground hover:bg-accent text-xs font-medium w-full text-center"
                >
                  View Profile & History
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Partner Profile Modal */}
        {selectedPartner && (
          <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-card border border-border rounded-xl max-w-xl w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto text-xs">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-500 font-bold border border-blue-500/20">
                    {selectedPartner.organization_type}
                  </span>
                  <h2 className="text-base font-bold text-foreground mt-1">
                    {selectedPartner.name}
                  </h2>
                </div>
                <button onClick={() => setSelectedPartner(null)} className="text-muted-foreground hover:text-foreground">
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="space-y-3">
                <p className="text-muted-foreground">{selectedPartner.purpose_statement}</p>

                <div className="bg-muted/30 p-3 rounded-lg border border-border space-y-2">
                  <h4 className="font-semibold text-foreground">Authorized Contact & Address</h4>
                  <div className="grid grid-cols-2 gap-2 text-muted-foreground">
                    <div>
                      <span>Representative:</span>
                      <p className="text-foreground font-medium">{selectedPartner.contact_person_name}</p>
                    </div>
                    <div>
                      <span>Email:</span>
                      <p className="text-foreground font-medium">{selectedPartner.contact_email}</p>
                    </div>
                    <div>
                      <span>Phone:</span>
                      <p className="text-foreground font-medium">{selectedPartner.contact_phone || "Not listed"}</p>
                    </div>
                    <div>
                      <span>Location:</span>
                      <p className="text-foreground font-medium">{selectedPartner.city}, {selectedPartner.state}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-muted/30 p-3 rounded-lg border border-border space-y-2">
                  <h4 className="font-semibold text-foreground">MoU Agreement & Audited Contributions</h4>
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="bg-background p-2 rounded border border-border">
                      <span className="text-[10px] text-muted-foreground block">Programs Hosted</span>
                      <span className="text-sm font-bold text-foreground">{selectedPartner.programs_hosted}</span>
                    </div>
                    <div className="bg-background p-2 rounded border border-border">
                      <span className="text-[10px] text-muted-foreground block">Volunteers</span>
                      <span className="text-sm font-bold text-foreground">{selectedPartner.total_volunteers_engaged}</span>
                    </div>
                    <div className="bg-background p-2 rounded border border-border">
                      <span className="text-[10px] text-muted-foreground block">Verified Hours</span>
                      <span className="text-sm font-bold text-emerald-500">{selectedPartner.verified_hours_contributed}</span>
                    </div>
                  </div>
                </div>

                {selectedPartner.impact_summary && (
                  <div className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/20 text-foreground">
                    <h5 className="font-semibold text-emerald-500 mb-1 flex items-center gap-1.5">
                      <TrendingUp className="h-3.5 w-3.5" /> Impact Summary
                    </h5>
                    <p className="text-muted-foreground">{selectedPartner.impact_summary}</p>
                  </div>
                )}
              </div>

              <div className="flex justify-end pt-3 border-t border-border">
                <button
                  onClick={() => setSelectedPartner(null)}
                  className="px-4 py-2 rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 font-medium"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Register Partner Modal */}
        {isRegisterOpen && (
          <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-card border border-border rounded-xl max-w-xl w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto text-xs">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <h2 className="text-base font-bold text-foreground flex items-center gap-2">
                  <PlusCircle className="h-5 w-5 text-blue-500" />
                  Register Community Partner
                </h2>
                <button onClick={() => setIsRegisterOpen(false)} className="text-muted-foreground hover:text-foreground">
                  <X className="h-4 w-4" />
                </button>
              </div>

              <form onSubmit={handleRegisterPartner} className="space-y-4">
                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Organization Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Blue Cross Animal Welfare Society"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">Organization Type *</label>
                    <select
                      value={orgType}
                      onChange={(e) => setOrgType(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    >
                      <option value="Non-Governmental Organization (NGO)">NGO</option>
                      <option value="Registered Trust">Registered Trust</option>
                      <option value="Healthcare Foundation">Healthcare Foundation</option>
                      <option value="Civic/Municipal Body">Civic/Municipal Body</option>
                      <option value="Educational Non-Profit">Educational Non-Profit</option>
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">MoU Reference Code</label>
                    <input
                      type="text"
                      placeholder="e.g. MOU/2026/CIVIC-099"
                      value={mouRef}
                      onChange={(e) => setMouRef(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">Authorized Representative *</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Dr. Ramesh Kumar"
                      value={contactPerson}
                      onChange={(e) => setContactPerson(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">Official Email *</label>
                    <input
                      type="email"
                      required
                      placeholder="contact@bluecross.org"
                      value={contactEmail}
                      onChange={(e) => setContactEmail(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">Contact Phone</label>
                    <input
                      type="text"
                      placeholder="+91 98450 12345"
                      value={contactPhone}
                      onChange={(e) => setContactPhone(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">Operating City</label>
                    <input
                      type="text"
                      value={city}
                      onChange={(e) => setCity(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Partnership Mission & Scope</label>
                  <textarea
                    rows={3}
                    placeholder="Describe collaboration goals, student volunteering modalities, and institutional alignment..."
                    value={purpose}
                    onChange={(e) => setPurpose(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                  />
                </div>

                <div className="flex items-center justify-end space-x-2 pt-3 border-t border-border">
                  <button
                    type="button"
                    onClick={() => setIsRegisterOpen(false)}
                    className="px-4 py-2 rounded-lg border border-border text-foreground hover:bg-accent"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-lg bg-primary text-primary-foreground font-semibold shadow hover:opacity-95"
                  >
                    Save Partner Record
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

