"use client";

import { useEffect, useState } from "react";
import {
  BookOpenCheck,
  CheckCircle2,
  FileCheck2,
  Globe2,
  MessageSquare,
  PlusCircle,
  Search,
  Sparkles,
  Star,
  Users2,
  X,
} from "lucide-react";
import { EngagementNav } from "@/components/engagement/engagement-nav";
import { EngagementService } from "@/services/engagement.service";
import {
  EngagementProgram,
  ReflectionSubmission,
  ReflectionSubmitInput,
} from "@/types/engagement";

const AVAILABLE_SDGS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17];

export default function EngagementReflectionsPage() {
  const [reflections, setReflections] = useState<ReflectionSubmission[]>([]);
  const [programs, setPrograms] = useState<EngagementProgram[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedReflection, setSelectedReflection] = useState<ReflectionSubmission | null>(null);

  // Submit Reflection Modal State
  const [isSubmitOpen, setIsSubmitOpen] = useState(false);
  const [progId, setProgId] = useState("");
  const [reflectionText, setReflectionText] = useState("");
  const [learningOutcomes, setLearningOutcomes] = useState("Environmental auditing, Field safety protocols");
  const [skillsAcquired, setSkillsAcquired] = useState("Team Leadership, Data Logging");
  const [impactSummary, setImpactSummary] = useState("");
  const [selectedSdgs, setSelectedSdgs] = useState<number[]>([11, 13]);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [r, p] = await Promise.all([
        EngagementService.listReflections(),
        EngagementService.listPrograms(),
      ]);
      setReflections(r);
      setPrograms(p);
      if (p.length > 0) setProgId(p[0].id);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  function toggleSdg(sdg: number) {
    if (selectedSdgs.includes(sdg)) {
      setSelectedSdgs(selectedSdgs.filter((s) => s !== sdg));
    } else {
      setSelectedSdgs([...selectedSdgs, sdg]);
    }
  }

  async function handleSubmitReflection(e: React.FormEvent) {
    e.preventDefault();
    if (!progId || !reflectionText) return;

    try {
      const input: ReflectionSubmitInput = {
        program_id: progId,
        reflection_text: reflectionText,
        learning_outcomes: learningOutcomes.split(",").map((s) => s.trim()).filter(Boolean),
        skills_acquired: skillsAcquired.split(",").map((s) => s.trim()).filter(Boolean),
        community_impact_summary: impactSummary,
        un_sdg_contributions: selectedSdgs,
      };

      await EngagementService.submitReflection(input);
      setActionMessage("Civic reflection submitted successfully for faculty review!");
      setIsSubmitOpen(false);
      setReflectionText("");
      setImpactSummary("");
      await loadData();
    } catch (err: any) {
      setActionMessage(`Error submitting reflection: ${err.message}`);
    }
  }

  const filteredReflections = reflections.filter((r) => {
    return (
      (r.student_name && r.student_name.toLowerCase().includes(search.toLowerCase())) ||
      r.reflection_text.toLowerCase().includes(search.toLowerCase()) ||
      (r.community_impact_summary && r.community_impact_summary.toLowerCase().includes(search.toLowerCase()))
    );
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
              <BookOpenCheck className="h-6 w-6 text-emerald-500" />
              Student Reflections & SDG Impact Evidence
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Reflective learning synthesis, acquired skills, and audited UN Sustainable Development Goal alignments
            </p>
          </div>

          <button
            onClick={() => setIsSubmitOpen(true)}
            className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-semibold shadow hover:opacity-95"
          >
            <PlusCircle className="h-4 w-4" />
            <span>Submit Reflection</span>
          </button>
        </div>

        {/* Search */}
        <div className="bg-card border border-border rounded-xl p-4 shadow-sm">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search reflections by student, learning outcome, or narrative..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-lg border border-border bg-background text-xs focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
        </div>

        {/* Reflections Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {filteredReflections.map((refl) => (
            <div
              key={refl.id}
              className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-4 hover:border-emerald-500/50 transition-all flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-foreground">
                    {refl.student_name || "Enrolled Student Volunteer"}
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500 font-semibold border border-emerald-500/20">
                    {refl.status}
                  </span>
                </div>

                <p className="text-xs text-muted-foreground italic line-clamp-3">
                  &ldquo;{refl.reflection_text}&rdquo;
                </p>

                {/* SDG Goals */}
                {refl.un_sdg_contributions && (
                  <div className="flex flex-wrap gap-1 items-center">
                    <Globe2 className="h-3.5 w-3.5 text-emerald-500 mr-1" />
                    {refl.un_sdg_contributions.map((g) => (
                      <span key={g} className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-foreground font-medium">
                        SDG {g}
                      </span>
                    ))}
                  </div>
                )}

                {/* Acquired Skills */}
                {refl.skills_acquired && refl.skills_acquired.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {refl.skills_acquired.map((skill, i) => (
                      <span key={i} className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-500 font-medium">
                        {skill}
                      </span>
                    ))}
                  </div>
                )}

                {/* Reviewer Feedback */}
                {refl.reviewer_feedback && (
                  <div className="p-3 rounded-lg bg-muted/40 border border-border text-xs space-y-1">
                    <div className="flex items-center justify-between text-foreground font-semibold">
                      <span>Faculty Reviewer Feedback</span>
                      {refl.rubric_score && (
                        <span className="text-emerald-500 font-bold flex items-center gap-0.5">
                          <Star className="h-3 w-3 fill-emerald-500" /> {refl.rubric_score}/100
                        </span>
                      )}
                    </div>
                    <p className="text-muted-foreground italic text-[11px]">&ldquo;{refl.reviewer_feedback}&rdquo;</p>
                  </div>
                )}
              </div>

              <div className="border-t border-border pt-3">
                <button
                  onClick={() => setSelectedReflection(refl)}
                  className="w-full py-1.5 rounded-lg border border-border text-foreground hover:bg-accent text-xs font-medium text-center"
                >
                  View Complete Dossier
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Detail Modal */}
        {selectedReflection && (
          <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-card border border-border rounded-xl max-w-lg w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto text-xs">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div>
                  <span className="text-[10px] text-muted-foreground block">Reflection Synthesis</span>
                  <h2 className="text-base font-bold text-foreground">
                    {selectedReflection.student_name || "Volunteer Reflection"}
                  </h2>
                </div>
                <button onClick={() => setSelectedReflection(null)} className="text-muted-foreground hover:text-foreground">
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="space-y-3">
                <div className="bg-muted/30 p-3 rounded-lg border border-border space-y-1">
                  <h4 className="font-semibold text-foreground">Student Civic Reflection</h4>
                  <p className="text-muted-foreground whitespace-pre-wrap">{selectedReflection.reflection_text}</p>
                </div>

                {selectedReflection.community_impact_summary && (
                  <div className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/20 space-y-1">
                    <h4 className="font-semibold text-emerald-500">Documented Community Outcomes:</h4>
                    <p className="text-foreground">{selectedReflection.community_impact_summary}</p>
                  </div>
                )}

                {selectedReflection.learning_outcomes && (
                  <div>
                    <h4 className="font-semibold text-foreground mb-1">Learning Outcomes:</h4>
                    <ul className="list-disc pl-5 text-muted-foreground space-y-0.5">
                      {selectedReflection.learning_outcomes.map((lo, i) => (
                        <li key={i}>{lo}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              <div className="flex justify-end pt-3 border-t border-border">
                <button
                  onClick={() => setSelectedReflection(null)}
                  className="px-4 py-2 rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 font-medium"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Submit Reflection Modal */}
        {isSubmitOpen && (
          <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-card border border-border rounded-xl max-w-xl w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto text-xs">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <h2 className="text-base font-bold text-foreground flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-emerald-500" />
                  Submit Civic Service Reflection
                </h2>
                <button onClick={() => setIsSubmitOpen(false)} className="text-muted-foreground hover:text-foreground">
                  <X className="h-4 w-4" />
                </button>
              </div>

              <form onSubmit={handleSubmitReflection} className="space-y-4">
                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Completed Program *</label>
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
                  <label className="font-semibold text-foreground">Civic & Personal Reflection *</label>
                  <textarea
                    rows={4}
                    required
                    placeholder="Reflect deeply on what you learned, challenges faced in the field, and how this service impacted your worldview..."
                    value={reflectionText}
                    onChange={(e) => setReflectionText(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Learning Outcomes (comma separated)</label>
                  <input
                    type="text"
                    value={learningOutcomes}
                    onChange={(e) => setLearningOutcomes(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Skills Developed (comma separated)</label>
                  <input
                    type="text"
                    value={skillsAcquired}
                    onChange={(e) => setSkillsAcquired(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Tangible Community Deliverable Summary</label>
                  <textarea
                    rows={2}
                    placeholder="e.g. Cleared 2 km of shoreline, tutored 14 children..."
                    value={impactSummary}
                    onChange={(e) => setImpactSummary(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Select Contributing UN SDGs:</label>
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {AVAILABLE_SDGS.map((sdg) => {
                      const isSelected = selectedSdgs.includes(sdg);
                      return (
                        <button
                          type="button"
                          key={sdg}
                          onClick={() => toggleSdg(sdg)}
                          className={`px-2 py-1 rounded text-[10px] font-semibold transition-colors ${
                            isSelected
                              ? "bg-emerald-500 text-white"
                              : "bg-muted text-muted-foreground hover:bg-accent"
                          }`}
                        >
                          SDG {sdg}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div className="flex items-center justify-end space-x-2 pt-3 border-t border-border">
                  <button
                    type="button"
                    onClick={() => setIsSubmitOpen(false)}
                    className="px-4 py-2 rounded-lg border border-border text-foreground hover:bg-accent"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-lg bg-primary text-primary-foreground font-semibold shadow hover:opacity-95"
                  >
                    Submit Reflection
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

