"use client";

import React, { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type {
  AdoptionJourneyModel,
  UserJourneyProgressModel,
  TrainingAssignmentModel,
  ProductAnnouncementModel,
  ContextualGuidanceModel,
  AdoptionSummaryDashboardModel,
} from "@campusos/types";

export default function AdoptionEnablementPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<"journeys" | "training" | "announcements" | "guidance" | "admin_analytics">("journeys");

  const [journeys, setJourneys] = useState<AdoptionJourneyModel[]>([]);
  const [selectedJourney, setSelectedJourney] = useState<AdoptionJourneyModel | null>(null);
  const [journeyProgress, setJourneyProgress] = useState<UserJourneyProgressModel | null>(null);

  const [trainings, setTrainings] = useState<TrainingAssignmentModel[]>([]);
  const [announcements, setAnnouncements] = useState<ProductAnnouncementModel[]>([]);
  const [guidanceList, setGuidanceList] = useState<ContextualGuidanceModel[]>([]);
  const [dashboardSummary, setDashboardSummary] = useState<AdoptionSummaryDashboardModel | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const isAdmin = user?.role === "SUPER_ADMIN" || user?.role === "INSTITUTION_ADMIN" || user?.role === "PLATFORM_OPERATOR";

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [journeysRes, trainingRes, announcementsRes, guidanceRes, summaryRes] = await Promise.all([
        apiFetch<AdoptionJourneyModel[]>("/api/v1/adoption/journeys").catch(() => ({ data: [] })),
        apiFetch<TrainingAssignmentModel[]>("/api/v1/adoption/training/assigned").catch(() => ({ data: [] })),
        apiFetch<ProductAnnouncementModel[]>("/api/v1/adoption/announcements").catch(() => ({ data: [] })),
        apiFetch<ContextualGuidanceModel[]>("/api/v1/adoption/guidance?route_path=/dashboard").catch(() => ({ data: [] })),
        isAdmin
          ? apiFetch<AdoptionSummaryDashboardModel>("/api/v1/adoption/admin/dashboard").catch(() => ({ data: null }))
          : Promise.resolve({ data: null }),
      ]);

      const jList = journeysRes.data || [];
      setJourneys(jList);
      if (jList.length > 0 && !selectedJourney) {
        setSelectedJourney(jList[0]);
        loadJourneyProgress(jList[0].id);
      }

      setTrainings(trainingRes.data || []);
      setAnnouncements(announcementsRes.data || []);
      setGuidanceList(guidanceRes.data || []);
      setDashboardSummary(summaryRes.data || null);
    } catch (err: any) {
      setError(err?.message || "Failed to load adoption and enablement data.");
    } finally {
      setLoading(false);
    }
  };

  const loadJourneyProgress = async (journeyId: string) => {
    try {
      const res = await apiFetch<UserJourneyProgressModel>(`/api/v1/adoption/journeys/${journeyId}/progress`);
      setJourneyProgress(res.data || null);
    } catch (err: any) {
      console.error("Could not fetch journey progress", err);
    }
  };

  useEffect(() => {
    loadData();
  }, [user]);

  const handleCompleteStep = async (journeyId: string, stepKey: string) => {
    try {
      setError(null);
      const res = await apiFetch<UserJourneyProgressModel>(`/api/v1/adoption/journeys/${journeyId}/steps/complete`, {
        method: "POST",
        body: JSON.stringify({ step_key: stepKey, notes: "Completed via web portal checklist" }),
      });
      setJourneyProgress(res.data);
      setActionSuccess(`Completed step ${stepKey}!`);
      setTimeout(() => setActionSuccess(null), 3500);
    } catch (err: any) {
      setError(err?.message || "Failed to complete step.");
    }
  };

  const handleCompleteModule = async (programId: string, moduleKey: string) => {
    try {
      setError(null);
      await apiFetch(`/api/v1/adoption/training/programs/${programId}/modules/complete?module_key=${moduleKey}`, {
        method: "POST",
      });
      setActionSuccess(`Verified completion for module ${moduleKey}!`);
      setTimeout(() => setActionSuccess(null), 3500);
      loadData();
    } catch (err: any) {
      setError(err?.message || "Failed to complete module.");
    }
  };

  const handleAcknowledgeAnnouncement = async (announcementId: string) => {
    try {
      setError(null);
      await apiFetch(`/api/v1/adoption/announcements/${announcementId}/acknowledge`, {
        method: "POST",
        body: JSON.stringify({ acknowledgement_notes: "Acknowledged by user" }),
      });
      setActionSuccess("Announcement acknowledged successfully.");
      setTimeout(() => setActionSuccess(null), 3500);
      loadData();
    } catch (err: any) {
      setError(err?.message || "Failed to acknowledge announcement.");
    }
  };

  const handleSeedDefaults = async () => {
    try {
      setLoading(true);
      await apiFetch("/api/v1/adoption/admin/journeys/seed-defaults", { method: "POST" });
      setActionSuccess("Standard role-aware onboarding journeys seeded!");
      setTimeout(() => setActionSuccess(null), 3500);
      loadData();
    } catch (err: any) {
      setError(err?.message || "Failed to seed defaults.");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10 font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-3">
            <span className="px-2.5 py-1 text-xs font-semibold rounded bg-sky-950 text-sky-400 border border-sky-800">
              CampusOS Step 37
            </span>
            <span className="text-xs text-slate-400">Enterprise Product Adoption & Change Management</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white mt-1">
            Product Adoption & Enablement Center
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Role-tailored onboarding journeys, certified learning programs, contextual walkthroughs, and change rollouts.
          </p>
        </div>

        {isAdmin && (
          <div className="flex items-center gap-3">
            <button
              onClick={handleSeedDefaults}
              className="px-4 py-2 text-xs font-semibold rounded-lg bg-sky-600 hover:bg-sky-500 text-white transition shadow"
            >
              Seed Default Role Journeys
            </button>
          </div>
        )}
      </div>

      {/* Alerts */}
      {error && (
        <div className="my-4 p-4 rounded-lg bg-rose-950/80 border border-rose-800 text-rose-300 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-rose-400 hover:text-white text-xs font-bold">
            Dismiss
          </button>
        </div>
      )}
      {actionSuccess && (
        <div className="my-4 p-4 rounded-lg bg-emerald-950/80 border border-emerald-800 text-emerald-300 text-sm flex items-center justify-between">
          <span>{actionSuccess}</span>
          <button onClick={() => setActionSuccess(null)} className="text-emerald-400 hover:text-white text-xs font-bold">
            Dismiss
          </button>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex border-b border-slate-800 mt-6 gap-2 overflow-x-auto">
        <button
          onClick={() => setActiveTab("journeys")}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition whitespace-nowrap ${
            activeTab === "journeys"
              ? "border-sky-500 text-sky-400 bg-sky-950/20"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Role Onboarding Journeys ({journeys.length})
        </button>
        <button
          onClick={() => setActiveTab("training")}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition whitespace-nowrap ${
            activeTab === "training"
              ? "border-sky-500 text-sky-400 bg-sky-950/20"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Assigned Training ({trainings.length})
        </button>
        <button
          onClick={() => setActiveTab("announcements")}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition whitespace-nowrap ${
            activeTab === "announcements"
              ? "border-sky-500 text-sky-400 bg-sky-950/20"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Product Announcements ({announcements.length})
        </button>
        <button
          onClick={() => setActiveTab("guidance")}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition whitespace-nowrap ${
            activeTab === "guidance"
              ? "border-sky-500 text-sky-400 bg-sky-950/20"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Contextual In-App Guidance ({guidanceList.length})
        </button>
        {isAdmin && (
          <button
            onClick={() => setActiveTab("admin_analytics")}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition whitespace-nowrap ${
              activeTab === "admin_analytics"
                ? "border-sky-500 text-sky-400 bg-sky-950/20"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Adoption Analytics & Rollouts
          </button>
        )}
      </div>

      {/* Main Content Area */}
      <div className="mt-6">
        {loading ? (
          <div className="flex items-center justify-center py-20 text-slate-500">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-500 mr-3"></div>
            Loading adoption configuration and personal progress...
          </div>
        ) : (
          <>
            {/* 1. Onboarding Journeys Tab */}
            {activeTab === "journeys" && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Journeys List */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                  <h2 className="text-base font-semibold text-white mb-4">Available Onboarding Journeys</h2>
                  {journeys.length === 0 ? (
                    <div className="text-center py-8 text-slate-500 text-sm">
                      No published onboarding journeys found for your role.
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {journeys.map((j) => (
                        <div
                          key={j.id}
                          onClick={() => {
                            setSelectedJourney(j);
                            loadJourneyProgress(j.id);
                          }}
                          className={`p-4 rounded-lg cursor-pointer border transition ${
                            selectedJourney?.id === j.id
                              ? "bg-sky-950/40 border-sky-600"
                              : "bg-slate-950/60 border-slate-800 hover:border-slate-700"
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-mono font-semibold text-sky-400">{j.code}</span>
                            <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                              {j.steps.length} steps
                            </span>
                          </div>
                          <div className="font-medium text-white text-sm">{j.title}</div>
                          <p className="text-xs text-slate-400 line-clamp-2 mt-1">{j.description}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Selected Journey Execution View */}
                <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6">
                  {selectedJourney ? (
                    <div>
                      <div className="flex items-start justify-between pb-4 border-b border-slate-800">
                        <div>
                          <div className="flex items-center gap-2">
                            <h2 className="text-lg font-bold text-white">{selectedJourney.title}</h2>
                            <span className="px-2 py-0.5 text-xs font-semibold rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                              {journeyProgress?.status || "IN_PROGRESS"}
                            </span>
                          </div>
                          <p className="text-xs text-slate-400 mt-1">{selectedJourney.description}</p>
                        </div>
                        <div className="text-right">
                          <div className="text-xs text-slate-400">Journey Progress</div>
                          <div className="text-2xl font-black text-sky-400">
                            {journeyProgress?.progress_pct ?? 0}%
                          </div>
                        </div>
                      </div>

                      {/* Progress bar */}
                      <div className="w-full bg-slate-800 h-2 rounded-full mt-4 overflow-hidden">
                        <div
                          className="bg-sky-500 h-2 transition-all duration-300"
                          style={{ width: `${journeyProgress?.progress_pct ?? 0}%` }}
                        ></div>
                      </div>

                      {/* Steps Checklist */}
                      <div className="mt-6 space-y-4">
                        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
                          Journey Milestones & Steps
                        </h3>
                        {selectedJourney.steps.map((st) => {
                          const isDone = journeyProgress?.completed_step_keys?.includes(st.step_key);
                          return (
                            <div
                              key={st.id}
                              className={`p-4 rounded-lg border flex items-start justify-between gap-4 transition ${
                                isDone
                                  ? "bg-emerald-950/20 border-emerald-900/60"
                                  : "bg-slate-950/60 border-slate-800"
                              }`}
                            >
                              <div className="flex items-start gap-3">
                                <div
                                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold mt-0.5 ${
                                    isDone
                                      ? "bg-emerald-600 text-white"
                                      : "bg-slate-800 text-slate-400"
                                  }`}
                                >
                                  {isDone ? "✓" : st.step_order}
                                </div>
                                <div>
                                  <div className="flex items-center gap-2">
                                    <span className="font-semibold text-sm text-white">{st.title}</span>
                                    {st.is_required && (
                                      <span className="text-[10px] uppercase font-bold text-amber-400 bg-amber-950/60 px-1.5 py-0.5 rounded border border-amber-900">
                                        Required
                                      </span>
                                    )}
                                  </div>
                                  <p className="text-xs text-slate-400 mt-1">{st.description}</p>
                                  {st.route_path && (
                                    <div className="mt-2 text-xs text-sky-400 flex items-center gap-1 font-mono">
                                      <span>Route:</span> {st.route_path}
                                    </div>
                                  )}
                                </div>
                              </div>

                              <div>
                                {isDone ? (
                                  <span className="text-xs font-semibold text-emerald-400 px-3 py-1 rounded bg-emerald-950 border border-emerald-800">
                                    Completed
                                  </span>
                                ) : (
                                  <button
                                    onClick={() => handleCompleteStep(selectedJourney.id, st.step_key)}
                                    className="px-3 py-1.5 text-xs font-semibold rounded bg-sky-600 hover:bg-sky-500 text-white transition shadow"
                                  >
                                    Mark Done
                                  </button>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-20 text-slate-500 text-sm">
                      Select an onboarding journey from the left to view milestones and checklist progress.
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 2. Assigned Training Tab */}
            {activeTab === "training" && (
              <div className="space-y-6">
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                  <h2 className="text-base font-semibold text-white mb-2">My Enrolled & Assigned Training</h2>
                  <p className="text-xs text-slate-400 mb-6">
                    Mandatory compliance and skill enablement programs assigned to your role or department.
                  </p>

                  {trainings.length === 0 ? (
                    <div className="text-center py-12 text-slate-500 text-sm">
                      You have no active training assignments at this time.
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {trainings.map((t) => (
                        <div key={t.id} className="p-5 rounded-xl bg-slate-950/70 border border-slate-800">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-mono font-semibold text-sky-400">
                              {t.program?.code || "TRAIN-PRG"}
                            </span>
                            <span
                              className={`text-xs px-2.5 py-0.5 rounded font-semibold ${
                                t.status === "COMPLETED"
                                  ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                                  : t.status === "OVERDUE"
                                  ? "bg-rose-950 text-rose-400 border border-rose-800"
                                  : "bg-sky-950 text-sky-400 border border-sky-800"
                              }`}
                            >
                              {t.status}
                            </span>
                          </div>
                          <h3 className="text-base font-bold text-white">{t.program?.title || "Training Program"}</h3>
                          <p className="text-xs text-slate-400 mt-1 line-clamp-2">{t.program?.description}</p>

                          <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between">
                            <span className="text-xs text-slate-400">
                              Progress: <strong className="text-white">{t.progress_pct}%</strong>
                            </span>
                            {t.certificate_reference && (
                              <span className="text-[11px] font-mono text-emerald-400">
                                {t.certificate_reference}
                              </span>
                            )}
                          </div>

                          {/* Modules List */}
                          {t.program?.modules && (
                            <div className="mt-4 space-y-2">
                              {t.program.modules.map((m) => {
                                const isModDone = t.completed_module_keys?.includes(m.module_key);
                                return (
                                  <div
                                    key={m.id}
                                    className="p-2.5 rounded bg-slate-900 border border-slate-800/80 flex items-center justify-between text-xs"
                                  >
                                    <span className="text-slate-300 font-medium">{m.title}</span>
                                    {isModDone ? (
                                      <span className="text-emerald-400 font-bold">✓ Complete</span>
                                    ) : (
                                      <button
                                        onClick={() => handleCompleteModule(t.program_id, m.module_key)}
                                        className="px-2.5 py-1 text-[11px] font-semibold rounded bg-sky-600 hover:bg-sky-500 text-white transition"
                                      >
                                        Verify & Complete
                                      </button>
                                    )}
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 3. Announcements Tab */}
            {activeTab === "announcements" && (
              <div className="space-y-4">
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                  <h2 className="text-base font-semibold text-white mb-2">Product & Change Announcements</h2>
                  <p className="text-xs text-slate-400 mb-6">
                    Stay informed regarding new capabilities, scheduled maintenance windows, and policy revisions.
                  </p>

                  {announcements.length === 0 ? (
                    <div className="text-center py-12 text-slate-500 text-sm">
                      No active product announcements for your profile.
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {announcements.map((ann) => (
                        <div
                          key={ann.id}
                          className="p-5 rounded-xl bg-slate-950/70 border border-slate-800 flex flex-col md:flex-row md:items-start justify-between gap-4"
                        >
                          <div className="space-y-2">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-mono font-semibold text-sky-400">
                                {ann.announcement_code}
                              </span>
                              <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                                {ann.category}
                              </span>
                              <span
                                className={`text-xs px-2 py-0.5 rounded font-bold ${
                                  ann.priority === "URGENT" || ann.priority === "HIGH"
                                    ? "bg-rose-950 text-rose-400 border border-rose-800"
                                    : "bg-slate-800 text-slate-400"
                                }`}
                              >
                                {ann.priority}
                              </span>
                            </div>
                            <h3 className="text-base font-bold text-white">{ann.title}</h3>
                            <p className="text-xs text-slate-300 whitespace-pre-line">{ann.content}</p>
                            {ann.doc_link_url && (
                              <div className="text-xs text-sky-400 pt-1">
                                <a href={ann.doc_link_url} target="_blank" rel="noreferrer" className="underline">
                                  View Release Notes & Documentation →
                                </a>
                              </div>
                            )}
                          </div>

                          <div className="shrink-0 flex flex-col items-end gap-2">
                            {ann.requires_acknowledgement ? (
                              ann.user_is_acknowledged ? (
                                <span className="text-xs font-semibold text-emerald-400 px-3 py-1.5 rounded bg-emerald-950 border border-emerald-800">
                                  ✓ Acknowledged
                                </span>
                              ) : (
                                <button
                                  onClick={() => handleAcknowledgeAnnouncement(ann.id)}
                                  className="px-4 py-2 text-xs font-bold rounded-lg bg-amber-600 hover:bg-amber-500 text-white transition shadow"
                                >
                                  Acknowledge Notice
                                </button>
                              )
                            ) : (
                              <span className="text-xs text-slate-500">Informational Notice</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 4. Contextual Guidance Tab */}
            {activeTab === "guidance" && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                <h2 className="text-base font-semibold text-white mb-2">In-App Walkthroughs & Guidance</h2>
                <p className="text-xs text-slate-400 mb-6">
                  Context-sensitive hints and step-by-step guidance applicable to active CampusOS routes.
                </p>

                {guidanceList.length === 0 ? (
                  <div className="text-center py-12 text-slate-500 text-sm">
                    No contextual guidance configured for this view.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {guidanceList.map((g) => (
                      <div key={g.id} className="p-4 rounded-lg bg-slate-950 border border-slate-800">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-mono text-sky-400">{g.guidance_key}</span>
                          <span className="text-xs text-slate-500">{g.guidance_type}</span>
                        </div>
                        <div className="font-semibold text-white text-sm">{g.title}</div>
                        <p className="text-xs text-slate-300 mt-1">{g.content}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* 5. Admin Analytics Tab */}
            {activeTab === "admin_analytics" && isAdmin && (
              <div className="space-y-6">
                {/* Metric Summary Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
                    <span className="text-xs text-slate-400">Active Journeys</span>
                    <div className="text-2xl font-bold text-white mt-1">
                      {dashboardSummary?.active_journeys_count ?? 0}
                    </div>
                    <span className="text-[11px] text-emerald-400">
                      {dashboardSummary?.journey_overall_completion_rate ?? 0}% overall completion
                    </span>
                  </div>
                  <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
                    <span className="text-xs text-slate-400">Active Trainings</span>
                    <div className="text-2xl font-bold text-white mt-1">
                      {dashboardSummary?.active_training_programs_count ?? 0}
                    </div>
                    <span className="text-[11px] text-emerald-400">
                      {dashboardSummary?.training_overall_completion_rate ?? 0}% completed
                    </span>
                  </div>
                  <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
                    <span className="text-xs text-slate-400">Overdue Trainings</span>
                    <div className="text-2xl font-bold text-rose-400 mt-1">
                      {dashboardSummary?.overdue_trainings_count ?? 0}
                    </div>
                    <span className="text-[11px] text-slate-500">Requires follow-up</span>
                  </div>
                  <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
                    <span className="text-xs text-slate-400">Pending Acknowledgements</span>
                    <div className="text-2xl font-bold text-amber-400 mt-1">
                      {dashboardSummary?.pending_acknowledgements_count ?? 0}
                    </div>
                    <span className="text-[11px] text-slate-500">Policy change notices</span>
                  </div>
                </div>

                {/* Tracked Capabilities */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                  <h3 className="text-base font-semibold text-white mb-4">Adoption Milestones & Feature Targets</h3>
                  <div className="text-xs text-slate-400 mb-4">
                    Monitoring institutional adoption rates across key ERP workflows and newly rolled-out modules.
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {dashboardSummary?.top_adopted_features?.map((f) => (
                      <span
                        key={f}
                        className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-sky-400"
                      >
                        {f}
                      </span>
                    )) || <span className="text-slate-500 text-xs">No active targets defined.</span>}
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
