"use client";

import { useEffect, useState } from "react";
import {
  AlertCircle,
  Calendar,
  CheckCircle2,
  Clock,
  Compass,
  Filter,
  HandHeart,
  MapPin,
  PlusCircle,
  Search,
  ShieldCheck,
  Users2,
  X,
} from "lucide-react";
import { EngagementNav } from "@/components/engagement/engagement-nav";
import { EngagementService } from "@/services/engagement.service";
import {
  ApplicationCreateInput,
  EngagementProgram,
  OpportunityCreateInput,
  VolunteerOpportunity,
} from "@/types/engagement";

export default function EngagementOpportunitiesPage() {
  const [opportunities, setOpportunities] = useState<VolunteerOpportunity[]>([]);
  const [programs, setPrograms] = useState<EngagementProgram[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [skillFilter, setSkillFilter] = useState("ALL");
  const [selectedOpportunity, setSelectedOpportunity] = useState<VolunteerOpportunity | null>(null);

  // Apply Modal State
  const [isApplyOpen, setIsApplyOpen] = useState(false);
  const [targetOpp, setTargetOpp] = useState<VolunteerOpportunity | null>(null);
  const [statement, setStatement] = useState("");
  const [consentAcknowledged, setConsentAcknowledged] = useState(false);

  // Create Opportunity Modal State
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [progId, setProgId] = useState("");
  const [title, setTitle] = useState("");
  const [capacity, setCapacity] = useState(20);
  const [hours, setHours] = useState(10);
  const [startDate, setStartDate] = useState(new Date().toISOString().split("T")[0]);
  const [endDate, setEndDate] = useState(
    new Date(Date.now() + 20 * 86400000).toISOString().split("T")[0]
  );
  const [location, setLocation] = useState("");
  const [desc, setDesc] = useState("");
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [opps, progs] = await Promise.all([
        EngagementService.listOpportunities(),
        EngagementService.listPrograms(),
      ]);
      setOpportunities(opps);
      setPrograms(progs);
      if (progs.length > 0) setProgId(progs[0].id);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function handleApply(e: React.FormEvent) {
    e.preventDefault();
    if (!targetOpp || !consentAcknowledged) return;

    try {
      const input: ApplicationCreateInput = {
        opportunity_id: targetOpp.id,
        statement_of_interest: statement,
        relevant_skills: targetOpp.required_skills,
      };

      await EngagementService.applyToOpportunity(input);
      setActionMessage("Application submitted successfully for review!");
      setIsApplyOpen(false);
      setStatement("");
      setConsentAcknowledged(false);
      await loadData();
    } catch (err: any) {
      setActionMessage(`Application error: ${err.message}`);
    }
  }

  async function handleCreateOpportunity(e: React.FormEvent) {
    e.preventDefault();
    if (!progId || !title) return;

    try {
      const input: OpportunityCreateInput = {
        program_id: progId,
        title,
        description: desc,
        capacity: Number(capacity),
        waitlist_capacity: 10,
        expected_hours_per_student: Number(hours),
        start_date: startDate,
        end_date: endDate,
        location_details: location,
        delivery_mode: "ON_SITE",
        required_skills: ["Teamwork", "Civic Orientation"],
      };

      await EngagementService.createOpportunity(input);
      setActionMessage("Volunteering opportunity published successfully!");
      setIsCreateOpen(false);
      setTitle("");
      setDesc("");
      await loadData();
    } catch (err: any) {
      setActionMessage(`Error creating opportunity: ${err.message}`);
    }
  }

  const filteredOpps = opportunities.filter((o) => {
    const matchesSearch =
      o.title.toLowerCase().includes(search.toLowerCase()) ||
      (o.description && o.description.toLowerCase().includes(search.toLowerCase())) ||
      (o.service_category && o.service_category.toLowerCase().includes(search.toLowerCase()));

    const matchesSkill =
      skillFilter === "ALL" ||
      (o.required_skills && o.required_skills.some((s) => s.toLowerCase().includes(skillFilter.toLowerCase())));

    return matchesSearch && matchesSkill;
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
              <Compass className="h-6 w-6 text-emerald-500" />
              Volunteering Opportunities
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Discover verified service roles, field tasks, and civic learning opportunities
            </p>
          </div>

          <button
            onClick={() => setIsCreateOpen(true)}
            className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-semibold shadow hover:opacity-95"
          >
            <PlusCircle className="h-4 w-4" />
            <span>Publish Opportunity</span>
          </button>
        </div>

        {/* Search & Filter */}
        <div className="bg-card border border-border rounded-xl p-4 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 shadow-sm">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search opportunity by role, mission, or category..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-lg border border-border bg-background text-xs focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          <div className="flex items-center space-x-2">
            <select
              value={skillFilter}
              onChange={(e) => setSkillFilter(e.target.value)}
              className="px-3 py-2 rounded-lg border border-border bg-background text-xs text-foreground focus:outline-none"
            >
              <option value="ALL">All Skills</option>
              <option value="Waste Segregation">Waste Segregation</option>
              <option value="Python/Scratch">Python / Scratch</option>
              <option value="Active Listening">Active Listening</option>
              <option value="First Aid">First Aid</option>
              <option value="Leadership">Leadership</option>
            </select>
          </div>
        </div>

        {/* Opportunities Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredOpps.map((opp) => {
            const isFull = opp.assigned_count >= opp.capacity;

            return (
              <div
                key={opp.id}
                className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-4 hover:border-emerald-500/50 transition-all flex flex-col justify-between"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 font-semibold border border-emerald-500/20">
                      {opp.service_category || "Civic Service"}
                    </span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                        isFull
                          ? "bg-amber-500/10 text-amber-500"
                          : "bg-emerald-500/10 text-emerald-500"
                      }`}
                    >
                      {isFull ? "Waitlist Active" : "Open for Registration"}
                    </span>
                  </div>

                  <div>
                    <h3 className="text-base font-bold text-foreground line-clamp-1">{opp.title}</h3>
                    <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                      {opp.description || "Active community volunteering opportunity."}
                    </p>
                  </div>

                  {opp.required_skills && opp.required_skills.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {opp.required_skills.map((skill, i) => (
                        <span
                          key={i}
                          className="text-[10px] px-2 py-0.5 rounded bg-muted text-muted-foreground font-medium"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="space-y-1.5 text-xs text-muted-foreground border-t border-border pt-3">
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-1.5">
                        <Users2 className="h-3.5 w-3.5" /> Enrolled:
                      </span>
                      <span className="text-foreground font-semibold">
                        {opp.assigned_count} / {opp.capacity} slots
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-1.5">
                        <Clock className="h-3.5 w-3.5" /> Expected Commitment:
                      </span>
                      <span className="text-foreground font-medium">
                        {opp.expected_hours_per_student} hrs
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-1.5">
                        <Calendar className="h-3.5 w-3.5" /> Service Dates:
                      </span>
                      <span className="text-foreground font-medium">
                        {opp.start_date} → {opp.end_date}
                      </span>
                    </div>

                    {opp.location_details && (
                      <div className="flex items-center justify-between">
                        <span className="flex items-center gap-1.5">
                          <MapPin className="h-3.5 w-3.5" /> Location:
                        </span>
                        <span className="text-foreground font-medium truncate max-w-[160px]">
                          {opp.location_details}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="border-t border-border pt-3 flex items-center gap-2">
                  <button
                    onClick={() => {
                      setTargetOpp(opp);
                      setIsApplyOpen(true);
                    }}
                    className="flex-1 py-1.5 rounded-lg bg-primary text-primary-foreground font-semibold text-xs shadow hover:opacity-95 text-center"
                  >
                    {isFull ? "Join Waitlist" : "Apply to Volunteer"}
                  </button>
                  <button
                    onClick={() => setSelectedOpportunity(opp)}
                    className="px-3 py-1.5 rounded-lg border border-border text-foreground hover:bg-accent text-xs font-medium"
                  >
                    Details
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Opportunity Detail Modal */}
        {selectedOpportunity && (
          <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-card border border-border rounded-xl max-w-xl w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto text-xs">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 font-bold border border-emerald-500/20">
                    {selectedOpportunity.service_category || "Field Task"}
                  </span>
                  <h2 className="text-base font-bold text-foreground mt-1">
                    {selectedOpportunity.title}
                  </h2>
                </div>
                <button onClick={() => setSelectedOpportunity(null)} className="text-muted-foreground hover:text-foreground">
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="space-y-3">
                <p className="text-muted-foreground">{selectedOpportunity.description}</p>

                <div className="bg-muted/30 p-3 rounded-lg border border-border space-y-2">
                  <h4 className="font-semibold text-foreground">Operational Details</h4>
                  <div className="grid grid-cols-2 gap-2 text-muted-foreground">
                    <div>
                      <span>Capacity:</span>
                      <p className="text-foreground font-medium">
                        {selectedOpportunity.assigned_count} filled / {selectedOpportunity.capacity} total
                      </p>
                    </div>
                    <div>
                      <span>Service Hours:</span>
                      <p className="text-foreground font-medium">
                        {selectedOpportunity.expected_hours_per_student} hrs credited upon verification
                      </p>
                    </div>
                    <div>
                      <span>Field Location:</span>
                      <p className="text-foreground font-medium">
                        {selectedOpportunity.location_details || "Designated Community Center"}
                      </p>
                    </div>
                    <div>
                      <span>Delivery Mode:</span>
                      <p className="text-foreground font-medium">
                        {selectedOpportunity.delivery_mode}
                      </p>
                    </div>
                  </div>
                </div>

                {selectedOpportunity.prerequisites && (
                  <div className="p-3 rounded-lg bg-blue-500/5 border border-blue-500/20 text-foreground">
                    <span className="font-semibold text-blue-500 block mb-0.5">Prerequisites:</span>
                    <p className="text-muted-foreground">{selectedOpportunity.prerequisites}</p>
                  </div>
                )}

                {selectedOpportunity.safety_guidelines && (
                  <div className="p-3 rounded-lg bg-amber-500/5 border border-amber-500/20 text-foreground">
                    <span className="font-semibold text-amber-500 block mb-0.5">Safety Guidance:</span>
                    <p className="text-muted-foreground">{selectedOpportunity.safety_guidelines}</p>
                  </div>
                )}
              </div>

              <div className="flex justify-end pt-3 border-t border-border">
                <button
                  onClick={() => setSelectedOpportunity(null)}
                  className="px-4 py-2 rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 font-medium"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Apply Modal */}
        {isApplyOpen && targetOpp && (
          <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-card border border-border rounded-xl max-w-lg w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto text-xs">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div>
                  <span className="text-[10px] text-muted-foreground block">Apply for Civic Role</span>
                  <h2 className="text-base font-bold text-foreground">{targetOpp.title}</h2>
                </div>
                <button onClick={() => setIsApplyOpen(false)} className="text-muted-foreground hover:text-foreground">
                  <X className="h-4 w-4" />
                </button>
              </div>

              <form onSubmit={handleApply} className="space-y-4">
                <div className="space-y-1">
                  <label className="font-semibold text-foreground">
                    Statement of Interest & Relevant Experience *
                  </label>
                  <textarea
                    rows={4}
                    required
                    placeholder="Briefly state why you want to serve in this initiative and your relevant background..."
                    value={statement}
                    onChange={(e) => setStatement(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                  />
                </div>

                <div className="p-3 rounded-lg bg-muted/40 border border-border space-y-2">
                  <div className="flex items-start space-x-2">
                    <input
                      type="checkbox"
                      id="consent-check"
                      checked={consentAcknowledged}
                      onChange={(e) => setConsentAcknowledged(e.target.checked)}
                      className="mt-0.5 rounded border-border"
                      required
                    />
                    <label htmlFor="consent-check" className="text-muted-foreground">
                      I agree to abide by institutional civic codes of conduct, field safety guidelines, and complete all required orientation modules.
                    </label>
                  </div>
                </div>

                <div className="flex items-center justify-end space-x-2 pt-3 border-t border-border">
                  <button
                    type="button"
                    onClick={() => setIsApplyOpen(false)}
                    className="px-4 py-2 rounded-lg border border-border text-foreground hover:bg-accent"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={!consentAcknowledged}
                    className="px-4 py-2 rounded-lg bg-primary text-primary-foreground font-semibold shadow hover:opacity-95 disabled:opacity-50"
                  >
                    Submit Application
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Create Opportunity Modal */}
        {isCreateOpen && (
          <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-card border border-border rounded-xl max-w-xl w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto text-xs">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <h2 className="text-base font-bold text-foreground flex items-center gap-2">
                  <PlusCircle className="h-5 w-5 text-emerald-500" />
                  Publish Volunteer Opportunity
                </h2>
                <button onClick={() => setIsCreateOpen(false)} className="text-muted-foreground hover:text-foreground">
                  <X className="h-4 w-4" />
                </button>
              </div>

              <form onSubmit={handleCreateOpportunity} className="space-y-4">
                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Linked Engagement Program *</label>
                  <select
                    value={progId}
                    onChange={(e) => setProgId(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    required
                  >
                    {programs.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.code} — {p.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Opportunity Title *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Estuary Zone Marshall / STEM Coding Tutor"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">Total Capacity (Slots) *</label>
                    <input
                      type="number"
                      min={1}
                      required
                      value={capacity}
                      onChange={(e) => setCapacity(Number(e.target.value))}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">Expected Hours per Volunteer *</label>
                    <input
                      type="number"
                      min={1}
                      max={100}
                      required
                      value={hours}
                      onChange={(e) => setHours(Number(e.target.value))}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">Start Date *</label>
                    <input
                      type="date"
                      required
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-semibold text-foreground">End Date *</label>
                    <input
                      type="date"
                      required
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Location / Field Coordinates</label>
                  <input
                    type="text"
                    placeholder="e.g. Marina Beach Post 3 / Sulur Govt School"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Role Description & Responsibilities</label>
                  <textarea
                    rows={3}
                    placeholder="Detail the tasks volunteers will undertake during their shifts..."
                    value={desc}
                    onChange={(e) => setDesc(e.target.value)}
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
                    Publish Opportunity
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

