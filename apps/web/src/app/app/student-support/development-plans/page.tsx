"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { StudentSupportService } from "@/services/student-support.service";
import { StudentDevelopmentPlanItem, MenteeItem } from "@/types/student-support";
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
  Sparkles,
  PlusCircle,
  Calendar,
  Clock,
  Target,
  CheckCircle2,
  ChevronRight,
  TrendingUp,
  UserCheck,
} from "lucide-react";

export default function StudentDevelopmentPlansPage() {
  const [plans, setPlans] = useState<StudentDevelopmentPlanItem[]>([]);
  const [mentees, setMentees] = useState<MenteeItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [createModalOpen, setCreateModalOpen] = useState(false);

  // Form State
  const [title, setTitle] = useState("");
  const [selectedStudentId, setSelectedStudentId] = useState("");
  const [reviewFrequency, setReviewFrequency] = useState<"MONTHLY" | "QUARTERLY" | "SEMESTER">("SEMESTER");
  const [strengths, setStrengths] = useState("");
  const [growthAreas, setGrowthAreas] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);

  useEffect(() => {
    loadPlans();
  }, []);

  async function loadPlans() {
    setLoading(true);
    try {
      const [allPlans, allMentees] = await Promise.all([
        StudentSupportService.getDevelopmentPlans(),
        StudentSupportService.getAssignedMentees(),
      ]);
      setPlans(allPlans);
      setMentees(allMentees);
      if (allMentees.length > 0) {
        setSelectedStudentId(allMentees[0].student_id || allMentees[0].studentId || "");
      }
    } catch (err) {
      console.error("Failed to load development plans:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreatePlan(e: React.FormEvent) {
    e.preventDefault();
    if (!title || !selectedStudentId) return;
    setSubmitting(true);
    try {
      await StudentSupportService.createDevelopmentPlan({
        student_id: selectedStudentId,
        title,
        academic_year: "2026-2027",
        review_frequency: reviewFrequency,
        strengths_summary: strengths,
        growth_areas_summary: growthAreas,
      });

      setNotification("Student Development Plan initialized successfully.");
      setCreateModalOpen(false);
      setTitle("");
      setStrengths("");
      setGrowthAreas("");
      loadPlans();
    } catch (err) {
      console.error("Failed to create plan:", err);
      alert("Error creating development plan.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6 pb-12">
      <div>
        <Breadcrumbs
          items={[
            { label: "Dashboard", href: "/app/dashboard" },
            { label: "Student Support", href: "/app/student-support" },
            { label: "Development Plans", href: "/app/student-support/development-plans" },
          ]}
        />
        <div className="mt-2 flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-purple-400" />
              Individual Student Development Plans (IDP)
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Collaborative goal-setting framework connecting students and mentors across academic, technical, leadership, and personal domains.
            </p>
          </div>
          <Button
            onClick={() => setCreateModalOpen(true)}
            className="bg-indigo-600 hover:bg-indigo-700 text-xs text-white"
          >
            <PlusCircle className="mr-1.5 h-3.5 w-3.5" />
            Create Development Plan
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

      {/* Plans Grid */}
      {loading ? (
        <div className="py-12 text-center text-sm text-slate-500">Loading student development plans...</div>
      ) : plans.length === 0 ? (
        <Card className="border-slate-800 bg-slate-900/60 p-8 text-center text-slate-400">
          No individual development plans found. Click "Create Development Plan" to initialize an IDP.
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {plans.map((plan) => (
            <Card
              key={plan.id}
              className="border-slate-800 bg-slate-900/60 p-5 space-y-4 hover:border-slate-700 transition flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="font-semibold text-white text-base">{plan.title}</h3>
                    <div className="text-xs text-slate-400">Student Ref: {plan.student_id}</div>
                  </div>
                  <Badge
                    variant="outline"
                    className={
                      plan.status === "ACTIVE"
                        ? "border-emerald-500/30 text-emerald-400 bg-emerald-500/10 text-xs"
                        : "border-slate-700 text-slate-400 text-xs"
                    }
                  >
                    {plan.status}
                  </Badge>
                </div>

                {/* Overall Progress Meter */}
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400 font-medium">Overall Progress</span>
                    <span className="text-indigo-400 font-bold">{plan.overall_progress_pct}%</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-500"
                      style={{ width: `${plan.overall_progress_pct}%` }}
                    />
                  </div>
                </div>

                <div className="text-xs text-slate-300 space-y-1.5 pt-1">
                  {plan.strengths_summary && (
                    <div className="p-2 rounded bg-slate-950 border border-slate-800">
                      <span className="text-slate-400 font-medium">Strengths: </span>
                      {plan.strengths_summary}
                    </div>
                  )}
                  {plan.growth_areas_summary && (
                    <div className="p-2 rounded bg-slate-950 border border-slate-800">
                      <span className="text-slate-400 font-medium">Growth Focus: </span>
                      {plan.growth_areas_summary}
                    </div>
                  )}
                </div>

                <div className="text-xs text-slate-400 space-y-1 pt-1 border-t border-slate-800/60">
                  <div className="flex justify-between">
                    <span>Review Cadence:</span>
                    <strong className="text-slate-200">{plan.review_frequency}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span>Next Review Date:</span>
                    <strong className="text-slate-200">
                      {plan.next_review_date ? new Date(plan.next_review_date).toLocaleDateString() : "Pending"}
                    </strong>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800/80">
                <Link href={`/app/student-support/goals?plan_id=${plan.id}`} className="block">
                  <Button className="w-full bg-indigo-600 hover:bg-indigo-700 text-xs text-white">
                    <Target className="mr-1.5 h-3.5 w-3.5" />
                    Manage Goals & Milestones
                    <ChevronRight className="ml-1 h-3.5 w-3.5" />
                  </Button>
                </Link>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create Plan Modal */}
      <Dialog open={createModalOpen} onOpenChange={setCreateModalOpen}>
        <DialogContent className="max-w-md bg-slate-900 border-slate-800 text-white">
          <DialogHeader>
            <DialogTitle className="text-base font-bold flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-purple-400" />
              Create Student Development Plan
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreatePlan} className="space-y-4 pt-2 text-xs">
            <div className="space-y-1">
              <label className="text-slate-400 font-medium">Plan Title *</label>
              <Input
                required
                placeholder="e.g. 2026-2027 Professional & Placement Readiness IDP"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="bg-slate-950 border-slate-800 text-xs"
              />
            </div>

            <div className="space-y-1">
              <label className="text-slate-400 font-medium">Student *</label>
              {mentees.length > 0 ? (
                <select
                  value={selectedStudentId}
                  onChange={(e) => setSelectedStudentId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-white"
                >
                  {mentees.map((m) => (
                    <option key={m.student_id || m.studentId} value={m.student_id || m.studentId}>
                      {m.student_name || m.studentName} ({m.student_reg_no || m.rollNumber}) - {m.program_name || m.programName}
                    </option>
                  ))}
                </select>
              ) : (
                <Input
                  required
                  placeholder="Enter Student UUID or Identifier"
                  value={selectedStudentId}
                  onChange={(e) => setSelectedStudentId(e.target.value)}
                  className="bg-slate-950 border-slate-800 text-xs"
                />
              )}
            </div>

            <div className="space-y-1">
              <label className="text-slate-400 font-medium">Review Frequency *</label>
              <select
                value={reviewFrequency}
                onChange={(e) => setReviewFrequency(e.target.value as any)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-white"
              >
                <option value="MONTHLY">Monthly</option>
                <option value="QUARTERLY">Quarterly</option>
                <option value="SEMESTER">Every Semester</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-slate-400 font-medium">Identified Strengths</label>
              <Textarea
                placeholder="Key technical, analytical, or interpersonal strengths..."
                value={strengths}
                onChange={(e) => setStrengths(e.target.value)}
                className="bg-slate-950 border-slate-800 text-xs"
                rows={2}
              />
            </div>

            <div className="space-y-1">
              <label className="text-slate-400 font-medium">Target Growth Areas</label>
              <Textarea
                placeholder="Specific areas to develop (e.g. communication, algorithms, public speaking)..."
                value={growthAreas}
                onChange={(e) => setGrowthAreas(e.target.value)}
                className="bg-slate-950 border-slate-800 text-xs"
                rows={2}
              />
            </div>

            <DialogFooter className="pt-2">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setCreateModalOpen(false)}
                className="text-xs text-slate-400"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={submitting}
                className="bg-indigo-600 hover:bg-indigo-700 text-xs text-white"
              >
                {submitting ? "Initializing..." : "Create Plan"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
