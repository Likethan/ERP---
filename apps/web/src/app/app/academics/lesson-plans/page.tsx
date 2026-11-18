"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { teachingService } from "@/services/teaching.service";
import { LessonPlanUnit } from "@/types/teaching";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { StatCard } from "@/components/ui/stat-card";
import { useToast } from "@/components/ui/toast";
import {
  Layers,
  Plus,
  BookOpen,
  CheckCircle2,
  Clock,
  Calendar,
  ArrowRight,
  TrendingUp,
  FileText,
  AlertCircle,
  Sparkles,
} from "lucide-react";

export default function LessonPlansPage() {
  const { user, activePersona } = useAuth();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [plans, setPlans] = useState<LessonPlanUnit[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<string>("co-cs301-a");

  // Create Modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    courseOfferingId: "co-cs301-a",
    courseCode: "CS301",
    courseName: "Data Structures & Algorithms",
    section: "A",
    unitNumber: 4,
    unitTitle: "",
    plannedHours: 8,
    completedHours: 0,
    topicsText: "",
    learningOutcomes: "",
  });

  // Edit hours modal
  const [editHoursModalOpen, setEditHoursModalOpen] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<LessonPlanUnit | null>(null);
  const [newCompletedHours, setNewCompletedHours] = useState<number>(0);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await teachingService.getLessonPlans(selectedCourse);
      if (res.success) {
        setPlans(res.data);
      }
    } catch (err) {
      console.error(err);
      showToast({ type: "error", title: "Error", message: "Failed to load lesson plans." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedCourse]);

  // Overall metrics
  const totalPlannedHours = useMemo(
    () => plans.reduce((acc, p) => acc + p.plannedHours, 0),
    [plans]
  );
  const totalCompletedHours = useMemo(
    () => plans.reduce((acc, p) => acc + p.completedHours, 0),
    [plans]
  );
  const overallSyllabusCompletion = useMemo(
    () =>
      totalPlannedHours > 0
        ? Math.round((totalCompletedHours / totalPlannedHours) * 100)
        : 0,
    [totalPlannedHours, totalCompletedHours]
  );

  const handleCreatePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.unitTitle.trim()) {
      showToast({ type: "error", title: "Validation Error", message: "Unit Title is required." });
      return;
    }
    try {
      setSubmitting(true);
      const topics = formData.topicsText
        .split("\n")
        .map((t) => t.trim())
        .filter(Boolean);

      const res = await teachingService.createLessonPlan({
        courseOfferingId: formData.courseOfferingId,
        courseCode: formData.courseCode,
        courseName: formData.courseName,
        section: formData.section,
        unitNumber: Number(formData.unitNumber),
        unitTitle: formData.unitTitle,
        plannedHours: Number(formData.plannedHours),
        completedHours: Number(formData.completedHours),
        topics,
        learningOutcomes: formData.learningOutcomes,
        status: Number(formData.completedHours) >= Number(formData.plannedHours) ? "COMPLETED" : "NOT_STARTED",
        completionPercentage: 0,
      });

      if (res.success) {
        showToast({
          type: "success",
          title: "Unit Added",
          message: `Unit ${formData.unitNumber} added to lesson plan successfully.`,
        });
        setCreateModalOpen(false);
        setFormData({
          ...formData,
          unitTitle: "",
          topicsText: "",
          learningOutcomes: "",
        });
        await loadData();
      }
    } catch (err: any) {
      showToast({ type: "error", title: "Creation Failed", message: err.message || "Could not add unit." });
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdateHours = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPlan) return;
    try {
      setSubmitting(true);
      const res = await teachingService.updateLessonPlanHours(selectedPlan.id, Number(newCompletedHours));
      if (res.success) {
        showToast({
          type: "success",
          title: "Hours Updated",
          message: `Completed hours updated to ${newCompletedHours} (${res.data.completionPercentage}% complete).`,
        });
        setEditHoursModalOpen(false);
        await loadData();
      }
    } catch (err: any) {
      showToast({ type: "error", title: "Update Failed", message: err.message });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-xs border-l-4 border-l-yellow-400">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-semibold text-yellow-950 border border-yellow-300 mb-2">
            <span className="h-1.5 w-1.5 rounded-full bg-yellow-600" />
            Curriculum Delivery & Syllabus Monitoring
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
            Lesson Plan Management
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-slate-500">
            Unit-wise lecture planning, learning outcomes mapping, and institutional syllabus completion tracking.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/app/academics/class-diary">
            <Button variant="outline" size="sm" leftIcon={<Calendar className="h-3.5 w-3.5" />}>
              Class Diary / Log
            </Button>
          </Link>
          <Button
            variant="primary"
            size="sm"
            leftIcon={<Plus className="h-3.5 w-3.5" />}
            onClick={() => setCreateModalOpen(true)}
          >
            Add Syllabus Unit
          </Button>
        </div>
      </div>

      {/* KPI Metric Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Syllabus Completion"
          value={`${overallSyllabusCompletion}%`}
          change={{ value: overallSyllabusCompletion >= 50 ? "On Track" : "Lagging", trend: "up" }}
          description={`${totalCompletedHours} of ${totalPlannedHours} planned lecture hours`}
          variant="amber"
          icon={<TrendingUp className="h-4 w-4" />}
        />
        <StatCard
          label="Total Units Mapped"
          value={plans.length}
          description="Curriculum syllabus modules"
          variant="indigo"
          icon={<Layers className="h-4 w-4" />}
        />
        <StatCard
          label="Delivered Hours"
          value={`${totalCompletedHours} Hrs`}
          description="Across completed & ongoing units"
          variant="emerald"
          icon={<Clock className="h-4 w-4" />}
        />
        <StatCard
          label="Planned Term Hours"
          value={`${totalPlannedHours} Hrs`}
          description="Prescribed by University Board"
          variant="sky"
          icon={<BookOpen className="h-4 w-4" />}
        />
      </div>

      {/* Course Selector Filter */}
      <div className="flex items-center justify-between p-4 bg-white rounded-xl border border-slate-200 shadow-xs">
        <div className="flex items-center gap-3">
          <BookOpen className="h-4 w-4 text-yellow-600" />
          <span className="text-xs font-semibold text-slate-800">Assigned Course Offering:</span>
          <select
            value={selectedCourse}
            onChange={(e) => setSelectedCourse(e.target.value)}
            className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-yellow-400"
          >
            <option value="co-cs301-a">CS301 — Data Structures & Algorithms (Sec A)</option>
            <option value="co-cs501-a">CS501 — Compiler Design (Sec A)</option>
            <option value="co-cs402-b">CS402 — Operating Systems (Sec B)</option>
          </select>
        </div>

        <div className="text-xs text-slate-500">
          Academic Year 2026-2027 • Odd Semester
        </div>
      </div>

      {/* Unit Progression Cards */}
      <div className="space-y-4">
        {loading ? (
          <div className="p-8 text-center text-xs text-slate-400">Loading lesson plan units...</div>
        ) : plans.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-400">No lesson plan units configured yet.</div>
        ) : (
          plans.map((unit) => (
            <Card key={unit.id} className="overflow-hidden hover:border-yellow-300 transition-all">
              <CardContent className="p-5 sm:p-6 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-yellow-100 text-yellow-950 font-bold text-xs border border-yellow-300">
                      U{unit.unitNumber}
                    </div>
                    <div>
                      <h3 className="text-sm sm:text-base font-bold text-slate-900">
                        Unit {unit.unitNumber}: {unit.unitTitle}
                      </h3>
                      <p className="text-xs text-slate-500">
                        {unit.courseCode} • Section {unit.section}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <Badge
                      variant={
                        unit.status === "COMPLETED"
                          ? "success"
                          : unit.status === "IN_PROGRESS"
                            ? "warning"
                            : "outline"
                      }
                      dot
                    >
                      {unit.status.replace("_", " ")}
                    </Badge>
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-xs h-7 px-2.5"
                      onClick={() => {
                        setSelectedPlan(unit);
                        setNewCompletedHours(unit.completedHours);
                        setEditHoursModalOpen(true);
                      }}
                    >
                      Log Hours
                    </Button>
                  </div>
                </div>

                {/* Progress Bar */}
                <div>
                  <div className="flex items-center justify-between text-xs mb-1.5 font-medium">
                    <span className="text-slate-600">
                      Syllabus Progress: {unit.completedHours} of {unit.plannedHours} Hours Completed
                    </span>
                    <span className="text-slate-900 font-bold font-mono">
                      {unit.completionPercentage}%
                    </span>
                  </div>
                  <div className="h-2.5 w-full rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className={`h-full transition-all duration-300 ${
                        unit.completionPercentage >= 100
                          ? "bg-emerald-500"
                          : unit.completionPercentage > 0
                            ? "bg-yellow-500"
                            : "bg-slate-300"
                      }`}
                      style={{ width: `${Math.min(100, unit.completionPercentage)}%` }}
                    />
                  </div>
                </div>

                {/* Topics Covered Grid */}
                <div className="rounded-xl bg-slate-50 p-3.5 border border-slate-100 text-xs">
                  <div className="font-semibold text-slate-800 mb-2 flex items-center gap-1.5">
                    <BookOpen className="h-3.5 w-3.5 text-yellow-600" />
                    Syllabus Topics & Pedagogical Scope:
                  </div>
                  <ul className="grid grid-cols-1 md:grid-cols-2 gap-1.5 list-disc list-inside text-slate-600">
                    {unit.topics.map((t, idx) => (
                      <li key={idx} className="truncate">
                        {t}
                      </li>
                    ))}
                  </ul>

                  {unit.learningOutcomes && (
                    <div className="mt-2.5 pt-2 border-t border-slate-200/60 text-[11px] text-slate-500">
                      <span className="font-semibold text-slate-700">Course Outcome (CO): </span>
                      {unit.learningOutcomes}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Add Unit Dialog */}
      <Dialog
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Add Lesson Plan Unit"
      >
        <form onSubmit={handleCreatePlan} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-700">Unit Number</label>
              <Input
                type="number"
                min="1"
                max="10"
                value={formData.unitNumber}
                onChange={(e) => setFormData({ ...formData, unitNumber: Number(e.target.value) })}
                required
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-700">Planned Hours</label>
              <Input
                type="number"
                min="1"
                max="40"
                value={formData.plannedHours}
                onChange={(e) => setFormData({ ...formData, plannedHours: Number(e.target.value) })}
                required
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700">Unit Title</label>
            <Input
              placeholder="e.g. Hierarchical Structures & Balanced Trees"
              value={formData.unitTitle}
              onChange={(e) => setFormData({ ...formData, unitTitle: e.target.value })}
              required
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700">Topics (one per line)</label>
            <textarea
              rows={4}
              className="w-full rounded-lg border border-slate-200 bg-white p-2.5 text-xs text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-yellow-400"
              placeholder="Topic 1&#10;Topic 2&#10;Topic 3"
              value={formData.topicsText}
              onChange={(e) => setFormData({ ...formData, topicsText: e.target.value })}
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700">Course Outcome / Learning Objective</label>
            <Input
              placeholder="State what the student will be able to demonstrate..."
              value={formData.learningOutcomes}
              onChange={(e) => setFormData({ ...formData, learningOutcomes: e.target.value })}
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
            <Button variant="ghost" size="sm" type="button" onClick={() => setCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" disabled={submitting}>
              {submitting ? "Saving..." : "Add Unit"}
            </Button>
          </div>
        </form>
      </Dialog>

      {/* Edit Hours Dialog */}
      <Dialog
        isOpen={editHoursModalOpen}
        onClose={() => setEditHoursModalOpen(false)}
        title={`Log Hours: Unit ${selectedPlan?.unitNumber}`}
      >
        <form onSubmit={handleUpdateHours} className="space-y-4">
          <div className="text-xs text-slate-600">
            Update completed lecture hours for <strong className="text-slate-900">{selectedPlan?.unitTitle}</strong>.
            Total planned: <strong>{selectedPlan?.plannedHours} Hours</strong>.
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700">Completed Lecture Hours</label>
            <Input
              type="number"
              min="0"
              max={selectedPlan?.plannedHours || 50}
              value={newCompletedHours}
              onChange={(e) => setNewCompletedHours(Number(e.target.value))}
              required
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
            <Button variant="ghost" size="sm" type="button" onClick={() => setEditHoursModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" disabled={submitting}>
              {submitting ? "Updating..." : "Save Progress"}
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
