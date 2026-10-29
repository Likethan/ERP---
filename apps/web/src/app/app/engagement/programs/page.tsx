"use client";

import { useEffect, useState } from "react";
import {
  AlertCircle,
  Calendar,
  CheckCircle2,
  Clock,
  Filter,
  Globe2,
  HandHeart,
  MapPin,
  PlusCircle,
  Search,
  ShieldAlert,
  Users2,
  X,
} from "lucide-react";
import { EngagementNav } from "@/components/engagement/engagement-nav";
import { EngagementService } from "@/services/engagement.service";
import {
  CommunityPartner,
  DeliveryMode,
  EngagementProgram,
  ProgramCategory,
  ProgramCreateInput,
  ProgramStatus,
} from "@/types/engagement";

const CATEGORIES: ProgramCategory[] = [
  "COMMUNITY_DEVELOPMENT",
  "ENVIRONMENTAL_SUSTAINABILITY",
  "HEALTH_WELLBEING",
  "EDUCATION_LITERACY",
  "DISASTER_RELIEF",
  "YOUTH_MENTORING",
  "ELDER_CARE",
  "CIVIC_ADVOCACY",
  "CULTURAL_HERITAGE",
  "DIGITAL_INCLUSION",
  "OTHER",
];

export default function EngagementProgramsPage() {
  const [programs, setPrograms] = useState<EngagementProgram[]>([]);
  const [partners, setPartners] = useState<CommunityPartner[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedProgram, setSelectedProgram] = useState<EngagementProgram | null>(null);

  // Form state
  const [formCode, setFormCode] = useState("");
  const [formName, setFormName] = useState("");
  const [formCategory, setFormCategory] = useState<ProgramCategory>("ENVIRONMENTAL_SUSTAINABILITY");
  const [formPartnerId, setFormPartnerId] = useState("");
  const [formStartDate, setFormStartDate] = useState(new Date().toISOString().split("T")[0]);
  const [formEndDate, setFormEndDate] = useState(
    new Date(Date.now() + 30 * 86400000).toISOString().split("T")[0]
  );
  const [formHours, setFormHours] = useState(15);
  const [formCapacity, setFormCapacity] = useState(50);
  const [formDescription, setFormDescription] = useState("");
  const [formDelivery, setFormDelivery] = useState<DeliveryMode>("ON_SITE");
  const [formLocation, setFormLocation] = useState("");
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [progs, parts] = await Promise.all([
        EngagementService.listPrograms(),
        EngagementService.listPartners(),
      ]);
      setPrograms(progs);
      setPartners(parts);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateProgram(e: React.FormEvent) {
    e.preventDefault();
    if (!formCode || !formName) return;

    try {
      const input: ProgramCreateInput = {
        code: formCode,
        name: formName,
        slug: formName.toLowerCase().replace(/[^a-z0-9]+/g, "-"),
        description: formDescription,
        category: formCategory,
        community_partner_id: formPartnerId || undefined,
        start_date: formStartDate,
        end_date: formEndDate,
        delivery_mode: formDelivery,
        location_address: formLocation,
        target_service_hours: Number(formHours),
        max_participants: Number(formCapacity),
        consent_required: true,
        un_sdg_goals: [11, 13],
      };

      await EngagementService.createProgram(input);
      setActionMessage("Program created successfully in DRAFT status.");
      setIsCreateOpen(false);
      resetForm();
      await loadData();
    } catch (err: any) {
      setActionMessage(`Error creating program: ${err.message}`);
    }
  }

  async function handleTransition(progId: string, targetStatus: ProgramStatus) {
    try {
      await EngagementService.transitionProgram(progId, targetStatus);
      setActionMessage(`Program transitioned to ${targetStatus}.`);
      await loadData();
      if (selectedProgram && selectedProgram.id === progId) {
        setSelectedProgram((prev) => (prev ? { ...prev, status: targetStatus } : null));
      }
    } catch (err: any) {
      setActionMessage(`Status transition failed: ${err.message}`);
    }
  }

  function resetForm() {
    setFormCode("");
    setFormName("");
    setFormDescription("");
    setFormLocation("");
  }

  const filteredPrograms = programs.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.code.toLowerCase().includes(search.toLowerCase()) ||
      (p.description && p.description.toLowerCase().includes(search.toLowerCase()));

    const matchesCategory =
      selectedCategory === "ALL" || p.category === selectedCategory;

    const matchesStatus =
      selectedStatus === "ALL" || p.status === selectedStatus;

    return matchesSearch && matchesCategory && matchesStatus;
  });

  return (
    <div className="min-h-screen bg-background">
      <EngagementNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Banner Notification */}
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
              <HandHeart className="h-6 w-6 text-emerald-500" />
              Community Engagement Programs
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Institution-approved civic service, volunteering missions, and outreach initiatives
            </p>
          </div>

          <button
            onClick={() => setIsCreateOpen(true)}
            className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-semibold shadow hover:opacity-95"
          >
            <PlusCircle className="h-4 w-4" />
            <span>Create Program</span>
          </button>
        </div>

        {/* Filter Controls */}
        <div className="bg-card border border-border rounded-xl p-4 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 shadow-sm">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search by code, title, or keywords..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-lg border border-border bg-background text-xs focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          <div className="flex items-center space-x-2">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-3 py-2 rounded-lg border border-border bg-background text-xs text-foreground focus:outline-none"
            >
              <option value="ALL">All Categories</option>
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c.replace(/_/g, " ")}
                </option>
              ))}
            </select>

            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="px-3 py-2 rounded-lg border border-border bg-background text-xs text-foreground focus:outline-none"
            >
              <option value="ALL">All Statuses</option>
              <option value="DRAFT">Draft</option>
              <option value="PENDING_APPROVAL">Pending Approval</option>
              <option value="APPROVED">Approved</option>
              <option value="PUBLISHED">Published</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="COMPLETED">Completed</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>
        </div>

        {/* Programs Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredPrograms.map((prog) => (
            <div
              key={prog.id}
              className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-4 hover:border-primary/50 transition-all flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 font-bold border border-emerald-500/20">
                    {prog.code}
                  </span>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded font-semibold ${
                      prog.status === "PUBLISHED" || prog.status === "IN_PROGRESS"
                        ? "bg-emerald-500/10 text-emerald-500"
                        : prog.status === "APPROVED"
                        ? "bg-blue-500/10 text-blue-500"
                        : prog.status === "PENDING_APPROVAL"
                        ? "bg-amber-500/10 text-amber-500"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {prog.status.replace(/_/g, " ")}
                  </span>
                </div>

                <div>
                  <h3 className="text-base font-bold text-foreground line-clamp-1">{prog.name}</h3>
                  <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                    {prog.description || "Institution civic engagement initiative."}
                  </p>
                </div>

                <div className="space-y-1.5 text-xs text-muted-foreground border-t border-border pt-3">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Calendar className="h-3.5 w-3.5" /> Timeline:
                    </span>
                    <span className="text-foreground font-medium">
                      {prog.start_date} → {prog.end_date}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Clock className="h-3.5 w-3.5" /> Target Hours:
                    </span>
                    <span className="text-foreground font-medium">{prog.target_service_hours} hrs</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Users2 className="h-3.5 w-3.5" /> Enrolled Capacity:
                    </span>
                    <span className="text-foreground font-medium">
                      {prog.current_enrolled_count} / {prog.max_participants || "Open"}
                    </span>
                  </div>

                  {prog.location_address && (
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-1.5">
                        <MapPin className="h-3.5 w-3.5" /> Mode:
                      </span>
                      <span className="text-foreground font-medium">
                        {prog.delivery_mode.replace(/_/g, " ")}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Lifecycle Actions */}
              <div className="border-t border-border pt-3 space-y-2">
                <div className="flex items-center gap-1.5 flex-wrap">
                  {prog.status === "DRAFT" && (
                    <button
                      onClick={() => handleTransition(prog.id, "PENDING_APPROVAL")}
                      className="px-2.5 py-1 rounded bg-amber-500/10 text-amber-500 hover:bg-amber-500/20 text-[11px] font-semibold"
                    >
                      Submit for Review
                    </button>
                  )}
                  {prog.status === "PENDING_APPROVAL" && (
                    <button
                      onClick={() => handleTransition(prog.id, "APPROVED")}
                      className="px-2.5 py-1 rounded bg-blue-500/10 text-blue-500 hover:bg-blue-500/20 text-[11px] font-semibold"
                    >
                      Approve Program
                    </button>
                  )}
                  {prog.status === "APPROVED" && (
                    <button
                      onClick={() => handleTransition(prog.id, "PUBLISHED")}
                      className="px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 text-[11px] font-semibold"
                    >
                      Publish
                    </button>
                  )}
                  {prog.status === "PUBLISHED" && (
                    <button
                      onClick={() => handleTransition(prog.id, "IN_PROGRESS")}
                      className="px-2.5 py-1 rounded bg-indigo-500/10 text-indigo-500 hover:bg-indigo-500/20 text-[11px] font-semibold"
                    >
                      Start Execution
                    </button>
                  )}
                  {prog.status === "IN_PROGRESS" && (
                    <button
                      onClick={() => handleTransition(prog.id, "COMPLETED")}
                      className="px-2.5 py-1 rounded bg-purple-500/10 text-purple-500 hover:bg-purple-500/20 text-[11px] font-semibold"
                    >
                      Mark Completed
                    </button>
                  )}
                  <button
                    onClick={() => setSelectedProgram(prog)}
                    className="px-2.5 py-1 rounded border border-border text-foreground hover:bg-accent text-[11px] font-medium ml-auto"
                  >
                    View Details
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {filteredPrograms.length === 0 && !loading && (
          <div className="p-12 text-center bg-card border border-dashed border-border rounded-xl space-y-3">
            <HandHeart className="h-10 w-10 text-muted-foreground mx-auto" />
            <h3 className="text-sm font-semibold text-foreground">No programs match criteria</h3>
            <p className="text-xs text-muted-foreground">
              Try adjusting your search query, status, or category filter.
            </p>
          </div>
        )}

        {/* Create Program Modal */}
        {isCreateOpen && (
          <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-card border border-border rounded-xl max-w-xl w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <h2 className="text-base font-bold text-foreground flex items-center gap-2">
                  <PlusCircle className="h-5 w-5 text-emerald-500" />
                  Create Civic Engagement Program
                </h2>
                <button onClick={() => setIsCreateOpen(false)} className="text-muted-foreground hover:text-foreground">
                  <X className="h-4 w-4" />
                </button>
              </div>

              <form onSubmit={handleCreateProgram} className="space-y-4 text-xs">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">Program Code *</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. CIVIC-ENV-26"
                      value={formCode}
                      onChange={(e) => setFormCode(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">Category *</label>
                    <select
                      value={formCategory}
                      onChange={(e) => setFormCategory(e.target.value as ProgramCategory)}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    >
                      {CATEGORIES.map((c) => (
                        <option key={c} value={c}>
                          {c.replace(/_/g, " ")}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Program Title *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Coastal Mangrove Restoration & Cleanliness Drive"
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Community Partner Organization</label>
                  <select
                    value={formPartnerId}
                    onChange={(e) => setFormPartnerId(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                  >
                    <option value="">Internal Campus Initiative (No External Partner)</option>
                    {partners.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.organization_type})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Program Description & Objectives</label>
                  <textarea
                    rows={3}
                    placeholder="Describe program goals, student community deliverables, and impact target..."
                    value={formDescription}
                    onChange={(e) => setFormDescription(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">Start Date *</label>
                    <input
                      type="date"
                      required
                      value={formStartDate}
                      onChange={(e) => setFormStartDate(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">End Date *</label>
                    <input
                      type="date"
                      required
                      value={formEndDate}
                      onChange={(e) => setFormEndDate(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">Target Hours *</label>
                    <input
                      type="number"
                      min={1}
                      max={200}
                      value={formHours}
                      onChange={(e) => setFormHours(Number(e.target.value))}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">Max Capacity</label>
                    <input
                      type="number"
                      min={1}
                      value={formCapacity}
                      onChange={(e) => setFormCapacity(Number(e.target.value))}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">Delivery Mode</label>
                    <select
                      value={formDelivery}
                      onChange={(e) => setFormDelivery(e.target.value as DeliveryMode)}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    >
                      <option value="ON_SITE">On Site</option>
                      <option value="VIRTUAL">Virtual</option>
                      <option value="HYBRID">Hybrid</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Location / Field Site</label>
                  <input
                    type="text"
                    placeholder="e.g. Marina Beach Sector 4 / Remote Portal"
                    value={formLocation}
                    onChange={(e) => setFormLocation(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                  />
                </div>

                <div className="flex items-center justify-end space-x-2 pt-3 border-t border-border">
                  <button
                    type="button"
                    onClick={() => setIsCreateOpen(false)}
                    className="px-4 py-2 rounded-lg border border-border text-foreground hover:bg-accent"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-lg bg-primary text-primary-foreground font-semibold shadow hover:opacity-95"
                  >
                    Save Program (Draft)
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Program Detail Modal */}
        {selectedProgram && (
          <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-card border border-border rounded-xl max-w-2xl w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto text-xs">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 font-bold border border-emerald-500/20">
                    {selectedProgram.code}
                  </span>
                  <h2 className="text-base font-bold text-foreground mt-1">
                    {selectedProgram.name}
                  </h2>
                </div>
                <button onClick={() => setSelectedProgram(null)} className="text-muted-foreground hover:text-foreground">
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="space-y-3">
                <p className="text-muted-foreground">{selectedProgram.description}</p>

                <div className="grid grid-cols-2 gap-4 bg-muted/30 p-3 rounded-lg border border-border">
                  <div>
                    <span className="text-muted-foreground block">Category</span>
                    <span className="font-semibold text-foreground">
                      {selectedProgram.category.replace(/_/g, " ")}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block">Lifecycle Status</span>
                    <span className="font-semibold text-emerald-500">
                      {selectedProgram.status.replace(/_/g, " ")}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block">Duration</span>
                    <span className="font-semibold text-foreground">
                      {selectedProgram.start_date} to {selectedProgram.end_date}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block">Target Service Hours</span>
                    <span className="font-semibold text-foreground">
                      {selectedProgram.target_service_hours} hrs
                    </span>
                  </div>
                </div>

                {selectedProgram.objectives && selectedProgram.objectives.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-foreground mb-1">Key Objectives:</h4>
                    <ul className="list-disc pl-5 text-muted-foreground space-y-0.5">
                      {selectedProgram.objectives.map((obj, i) => (
                        <li key={i}>{obj}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {selectedProgram.un_sdg_goals && (
                  <div>
                    <h4 className="font-semibold text-foreground mb-1">UN SDG Alignments:</h4>
                    <div className="flex flex-wrap gap-1">
                      {selectedProgram.un_sdg_goals.map((g) => (
                        <span key={g} className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500 font-medium">
                          SDG {g}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="flex justify-end pt-3 border-t border-border">
                <button
                  onClick={() => setSelectedProgram(null)}
                  className="px-4 py-2 rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 font-medium"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

