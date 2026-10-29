"use client";

import React, { useState, useEffect } from "react";
import { StudentSupportService } from "@/services/student-support.service";
import {
  DevelopmentGoalItem,
  StudentDevelopmentPlanItem,
} from "@/types/student-support";
import { StudentSupportNav } from "@/components/student-support/student-support-nav";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Target,
  PlusCircle,
  CheckCircle2,
  Clock,
  Sparkles,
  Search,
  Filter,
  CheckSquare,
  Square,
  TrendingUp,
} from "lucide-react";

const GOAL_CATEGORIES = [
  "ACADEMIC",
  "CAREER",
  "TECHNICAL",
  "LEADERSHIP",
  "COMMUNICATION",
  "PERSONAL",
];

export default function GoalsAndActionItemsPage() {
  const [plans, setPlans] = useState<StudentDevelopmentPlanItem[]>([]);
  const [selectedPlanId, setSelectedPlanId] = useState<string>("");
  const [goals, setGoals] = useState<DevelopmentGoalItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [categoryFilter, setCategoryFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  // Add Goal Modal State
  const [addGoalModalOpen, setAddGoalModalOpen] = useState(false);
  const [goalTitle, setGoalTitle] = useState("");
  const [category, setCategory] = useState("ACADEMIC");
  const [targetDate, setTargetDate] = useState("");
  const [successMetrics, setSuccessMetrics] = useState("");
  const [submittingGoal, setSubmittingGoal] = useState(false);

  const [notification, setNotification] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const allPlans = await StudentSupportService.getDevelopmentPlans();
      setPlans(allPlans);
      if (allPlans.length > 0) {
        const firstId = allPlans[0].id;
        setSelectedPlanId(firstId);
        const planGoals = await StudentSupportService.getGoalsForPlan(firstId);
        setGoals(planGoals);
      }
    } catch (err) {
      console.error("Failed to load goals:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSelectPlan(planId: string) {
    setSelectedPlanId(planId);
    setLoading(true);
    try {
      const planGoals = await StudentSupportService.getGoalsForPlan(planId);
      setGoals(planGoals);
    } catch (err) {
      console.error("Failed to load goals for plan:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateGoal(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedPlanId || !goalTitle || !targetDate) return;
    setSubmittingGoal(true);
    try {
      await StudentSupportService.addGoalToPlan(selectedPlanId, {
        category,
        title: goalTitle,
        target_completion_date: new Date(targetDate).toISOString(),
        success_metric: successMetrics,
      });

      setNotification("New development goal established successfully.");
      setAddGoalModalOpen(false);
      setGoalTitle("");
      setTargetDate("");
      setSuccessMetrics("");
      // reload goals
      const updatedGoals = await StudentSupportService.getGoalsForPlan(selectedPlanId);
      setGoals(updatedGoals);
    } catch (err) {
      console.error("Failed to add goal:", err);
      alert("Error adding goal.");
    } finally {
      setSubmittingGoal(false);
    }
  }

  async function handleUpdateGoalProgress(goalId: string, newPct: number) {
    try {
      const newStatus = newPct >= 100 ? "COMPLETED" : newPct > 0 ? "IN_PROGRESS" : "PENDING";
      await StudentSupportService.updateGoal(goalId, {
        progress_pct: newPct,
        status: newStatus,
      });
      // reload goals
      const updatedGoals = await StudentSupportService.getGoalsForPlan(selectedPlanId);
      setGoals(updatedGoals);
    } catch (err) {
      console.error("Failed to update goal progress:", err);
      alert("Unable to update progress.");
    }
  }

  const filteredGoals = goals.filter((g) => {
    const matchesCategory = categoryFilter === "ALL" || g.category === categoryFilter;
    const matchesSearch =
      g.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (g.success_metric && g.success_metric.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="space-y-6 pb-12">
      <div>
        <Breadcrumbs
          items={[
            { label: "Dashboard", href: "/app/dashboard" },
            { label: "Student Support", href: "/app/student-support" },
            { label: "Goals & Action Items", href: "/app/student-support/goals" },
          ]}
        />
        <div className="mt-2 flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <Target className="h-6 w-6 text-indigo-400" />
              Development Goals & Action Items
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Track progress against measurable milestones, self-reflections, and task completion metrics.
            </p>
          </div>
          <Button
            onClick={() => setAddGoalModalOpen(true)}
            disabled={!selectedPlanId}
            className="bg-indigo-600 hover:bg-indigo-700 text-xs text-white"
          >
            <PlusCircle className="mr-1.5 h-3.5 w-3.5" />
            Add Goal
          </Button>
        </div>
      </div>

      <StudentSupportNav />

      {notification && (
        <div className="rounded-lg border border-emerald-800/50 bg-emerald-950/30 p-3 text-xs text-emerald-300 flex items-center justify-between">
          <span className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            {notification}
          </span>
          <button onClick={() => setNotification(null)} className="text-emerald-400 hover:text-emerald-200">
            Dismiss
          </button>
        </div>
      )}

      {/* Plan Selector & Filter Bar */}
      <Card className="border-slate-800 bg-slate-900/60 p-4">
        <div className="flex flex-col md:flex-row gap-3">
          <div className="space-y-1 md:w-1/3">
            <label className="text-[11px] text-slate-400 font-medium">Select Development Plan</label>
            <select
              value={selectedPlanId}
              onChange={(e) => handleSelectPlan(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-white"
            >
              {plans.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.title} ({p.overall_progress_pct}%)
                </option>
              ))}
            </select>
          </div>

          <div className="flex-1 flex flex-col sm:flex-row gap-2 md:items-end">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
              <Input
                placeholder="Search milestones..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 bg-slate-950 border-slate-800 text-xs"
              />
            </div>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-300"
            >
              <option value="ALL">All Categories</option>
              {GOAL_CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      {/* Goals List */}
      {loading ? (
        <div className="py-12 text-center text-sm text-slate-500">Loading development goals...</div>
      ) : filteredGoals.length === 0 ? (
        <Card className="border-slate-800 bg-slate-900/60 p-8 text-center text-slate-400">
          No goals established under this category yet. Click "Add Goal" to set milestones.
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredGoals.map((goal) => (
            <Card
              key={goal.id}
              className="border-slate-800 bg-slate-900/60 p-5 space-y-4"
            >
              <div className="flex items-start justify-between gap-2 border-b border-slate-800/80 pb-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-white text-sm">{goal.title}</span>
                    <Badge
                      variant="outline"
                      className={
                        goal.status === "COMPLETED"
                          ? "border-emerald-500/30 text-emerald-400 bg-emerald-500/10 text-[10px]"
                          : "border-blue-500/30 text-blue-400 bg-blue-500/10 text-[10px]"
                      }
                    >
                      {goal.status}
                    </Badge>
                  </div>
                  <span className="text-[11px] text-indigo-400 bg-indigo-950/40 px-2 py-0.5 rounded border border-indigo-900/30 inline-block">
                    {goal.category}
                  </span>
                </div>

                <div className="text-right text-xs text-slate-400">
                  <span>Target Date:</span>
                  <div className="font-medium text-slate-200">
                    {new Date(goal.target_completion_date || goal.targetDate || "").toLocaleDateString()}
                  </div>
                </div>
              </div>

              {goal.success_metric && (
                <div className="text-xs space-y-1">
                  <span className="text-slate-400 font-medium">Measurable Metric:</span>
                  <p className="text-slate-200 bg-slate-950 p-2.5 rounded border border-slate-800">
                    {goal.success_metric}
                  </p>
                </div>
              )}

              {/* Progress Slider */}
              <div className="space-y-2 pt-1">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400 font-medium">Goal Progress</span>
                  <span className="text-indigo-400 font-bold">{goal.progress_pct}%</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-2 flex-1 rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className="h-full bg-indigo-500 rounded-full transition-all"
                      style={{ width: `${goal.progress_pct}%` }}
                    />
                  </div>
                  <div className="flex gap-1">
                    {[0, 25, 50, 75, 100].map((pct) => (
                      <button
                        key={pct}
                        type="button"
                        onClick={() => handleUpdateGoalProgress(goal.id, pct)}
                        className={`text-[10px] px-1.5 py-0.5 rounded border transition ${
                          goal.progress_pct === pct
                            ? "bg-indigo-600 text-white border-indigo-500"
                            : "bg-slate-950 text-slate-400 border-slate-800 hover:bg-slate-800"
                        }`}
                      >
                        {pct}%
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Action Items List */}
              {goal.action_items && goal.action_items.length > 0 && (
                <div className="space-y-2 pt-2 border-t border-slate-800/80">
                  <span className="text-xs text-slate-400 font-medium">Action Items:</span>
                  <div className="space-y-1.5">
                    {goal.action_items.map((act) => (
                      <div
                        key={act.id}
                        className="flex items-center justify-between p-2 rounded bg-slate-950/40 border border-slate-800 text-xs"
                      >
                        <div className="flex items-center gap-2">
                          {act.status === "COMPLETED" ? (
                            <CheckSquare className="h-3.5 w-3.5 text-emerald-400" />
                          ) : (
                            <Square className="h-3.5 w-3.5 text-slate-500" />
                          )}
                          <span className={act.status === "COMPLETED" ? "line-through text-slate-500" : "text-slate-200"}>
                            {act.title}
                          </span>
                        </div>
                        <Badge variant="outline" className="text-[9px] border-slate-700 text-slate-400">
                          {act.assigned_to_role}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}

      {/* Add Goal Modal */}
      <Dialog open={addGoalModalOpen} onOpenChange={setAddGoalModalOpen}>
        <DialogContent className="max-w-md bg-slate-900 border-slate-800 text-white">
          <DialogHeader>
            <DialogTitle className="text-base font-bold flex items-center gap-2">
              <Target className="h-4 w-4 text-indigo-400" />
              Establish Development Goal
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateGoal} className="space-y-4 pt-2 text-xs">
            <div className="space-y-1">
              <label className="text-slate-400 font-medium">Goal Title *</label>
              <Input
                required
                placeholder="e.g. Master distributed algorithms & publish research preprint"
                value={goalTitle}
                onChange={(e) => setGoalTitle(e.target.value)}
                className="bg-slate-950 border-slate-800 text-xs"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Category *</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white"
                >
                  {GOAL_CATEGORIES.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-medium">Target Date *</label>
                <Input
                  required
                  type="date"
                  value={targetDate}
                  onChange={(e) => setTargetDate(e.target.value)}
                  className="bg-slate-950 border-slate-800 text-xs"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-slate-400 font-medium">Measurable Success Metric</label>
              <Textarea
                placeholder="How will progress be validated? (e.g. score >= 85% on mock placement exam)"
                value={successMetrics}
                onChange={(e) => setSuccessMetrics(e.target.value)}
                className="bg-slate-950 border-slate-800 text-xs"
                rows={3}
              />
            </div>

            <DialogFooter className="pt-2">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setAddGoalModalOpen(false)}
                className="text-xs text-slate-400"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={submittingGoal}
                className="bg-indigo-600 hover:bg-indigo-700 text-xs text-white"
              >
                {submittingGoal ? "Establishing..." : "Save Goal"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
