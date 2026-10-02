"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { examinationsService } from "@/services/examinations.service";
import {
  Assessment,
  AssessmentType,
  AssessmentStatus,
  AssessmentComponent,
} from "@/types/examinations";
import { calculateAssessmentTotal } from "@/services/grading-calculator";
import { DataGrid } from "@/components/data-grid/data-grid";
import { ColumnDef } from "@/components/data-grid/data-grid.types";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { useToast } from "@/components/ui/toast";
import {
  FileText,
  Plus,
  Trash2,
  Lock,
  ArrowRight,
  Filter,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Sparkles,
  BookOpen,
} from "lucide-react";

export default function AssessmentConfigurationPage() {
  const { hasPermission } = useAuth();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [selectedDept, setSelectedDept] = useState<string>("ALL");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [selectedType, setSelectedType] = useState<string>("ALL");

  // Create Modal State
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);

  // Form State
  const [name, setName] = useState("");
  const [courseOfferingId, setCourseOfferingId] = useState("co-cs301-a");
  const [courseCode, setCourseCode] = useState("CS301");
  const [courseName, setCourseName] = useState("Data Structures & Algorithms");
  const [section, setSection] = useState("A");
  const [department, setDepartment] = useState("Computer Science & Engineering");
  const [facultyName, setFacultyName] = useState("Dr. Ramesh Sundaram");
  const [semester, setSemester] = useState<number>(5);
  const [assessmentType, setAssessmentType] = useState<AssessmentType>("INTERNAL");
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);

  // Assessment Components builder
  const [components, setComponents] = useState<AssessmentComponent[]>([
    { id: "c-1", name: "Assignment 1", type: "ASSIGNMENT", maxMarks: 20, passingMarks: 8, weightage: 10, sequence: 1 },
    { id: "c-2", name: "Quiz 1", type: "QUIZ", maxMarks: 20, passingMarks: 8, weightage: 10, sequence: 2 },
    { id: "c-3", name: "Mid-Term Written Test", type: "MIDTERM", maxMarks: 60, passingMarks: 24, weightage: 20, sequence: 3 },
  ]);

  const loadAssessments = async () => {
    try {
      setLoading(true);
      const res = await examinationsService.getAssessments({
        department: selectedDept !== "ALL" ? selectedDept : undefined,
        status: selectedStatus !== "ALL" ? selectedStatus : undefined,
        type: selectedType !== "ALL" ? selectedType : undefined,
      });
      setAssessments(res.data);
    } catch {
      showToast({ title: "Error", message: "Failed to load assessments", type: "error" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAssessments();
  }, [selectedDept, selectedStatus, selectedType]);

  const { totalMaxMarks, totalWeightage, isValidWeightage } = useMemo(() => {
    return calculateAssessmentTotal(components);
  }, [components]);

  const handleAddComponent = () => {
    const nextSeq = components.length + 1;
    setComponents([
      ...components,
      {
        id: `c-${Date.now()}`,
        name: `Component ${nextSeq}`,
        type: "ASSIGNMENT",
        maxMarks: 20,
        passingMarks: 8,
        weightage: 10,
        sequence: nextSeq,
      },
    ]);
  };

  const handleRemoveComponent = (id: string) => {
    if (components.length <= 1) {
      showToast({ title: "Validation", message: "Assessment requires at least 1 component", type: "error" });
      return;
    }
    setComponents(components.filter((c) => c.id !== id));
  };

  const handleUpdateComponent = (
    id: string,
    field: keyof AssessmentComponent,
    val: string | number
  ) => {
    setComponents(
      components.map((c) => {
        if (c.id === id) {
          return { ...c, [field]: val };
        }
        return c;
      })
    );
  };

  const handleCreateAssessment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      showToast({ title: "Validation Error", message: "Assessment title is required.", type: "error" });
      return;
    }

    if (totalMaxMarks <= 0) {
      showToast({ title: "Validation Error", message: "Total marks must be greater than zero.", type: "error" });
      return;
    }

    try {
      setSaving(true);
      await examinationsService.createAssessment({
        name,
        type: assessmentType,
        courseOfferingId,
        courseCode,
        courseName,
        section,
        department,
        facultyName,
        semester,
        maxMarks: totalMaxMarks,
        passingMarks: Math.round(totalMaxMarks * 0.4),
        weightage: totalWeightage,
        date,
        components,
      });

      showToast({ title: "Success", message: "Assessment scheme configured successfully.", type: "success" });
      setCreateModalOpen(false);
      setName("");
      loadAssessments();
    } catch (err: unknown) {
      showToast({
        title: "Error",
        message: err instanceof Error ? err.message : "Failed to create assessment",
        type: "error",
      });
    } finally {
      setSaving(false);
    }
  };

  const columns: ColumnDef<Assessment>[] = useMemo(
    () => [
      {
        id: "name",
        header: "Assessment Name",
        cell: (row) => (
          <div>
            <Link
              href={`/app/examinations/assessments/${row.id}`}
              className="font-semibold text-slate-900 hover:text-indigo-600 dark:text-white dark:hover:text-indigo-400"
            >
              {row.name}
            </Link>
            <div className="flex items-center gap-2 mt-0.5 text-xs text-slate-500">
              <span className="font-mono font-medium text-slate-600 dark:text-slate-300">
                {row.courseCode}
              </span>
              <span>•</span>
              <span>Sec {row.section}</span>
              <span>•</span>
              <span>{row.facultyName}</span>
            </div>
          </div>
        ),
      },
      {
        id: "type",
        header: "Type",
        cell: (row) => (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
            {row.type}
          </span>
        ),
      },
      {
        id: "marks",
        header: "Score Matrix",
        cell: (row) => (
          <div className="text-xs">
            <span className="font-semibold text-slate-900 dark:text-white">
              Max: {row.maxMarks}
            </span>
            <span className="text-slate-400 ml-1.5">(Pass: {row.passingMarks})</span>
            <div className="text-[11px] text-indigo-600 dark:text-indigo-400 font-medium">
              Weightage: {row.weightage}%
            </div>
          </div>
        ),
      },
      {
        id: "components",
        header: "Sub-Components",
        cell: (row) => (
          <div className="flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-300">
            <Layers className="h-3.5 w-3.5 text-slate-400" />
            <span>{row.components?.length || 1} component(s)</span>
          </div>
        ),
      },
      {
        id: "completion",
        header: "Marks Roster",
        cell: (row) => {
          const pct = Math.round(((row.totalEntered || 0) / (row.totalEnrolled || 1)) * 100);
          return (
            <div className="w-28 space-y-1">
              <div className="flex justify-between text-[11px] text-slate-500">
                <span>{row.totalEntered} of {row.totalEnrolled}</span>
                <span className="font-medium">{pct}%</span>
              </div>
              <div className="h-1.5 w-full rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    pct === 100 ? "bg-emerald-500" : pct > 0 ? "bg-amber-500" : "bg-slate-300"
                  }`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        },
      },
      {
        id: "status",
        header: "Status",
        cell: (row) => {
          const isDone = row.isFinalized || row.status === "FINALIZED";
          return (
            <span
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold ${
                isDone
                  ? "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300"
                  : row.status === "OPEN"
                  ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                  : "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300"
              }`}
            >
              {isDone && <Lock className="h-3 w-3" />}
              {row.status}
            </span>
          );
        },
      },
      {
        id: "actions",
        header: "Actions",
        cell: (row) => (
          <div className="flex items-center gap-2">
            <Link href={`/app/examinations/assessments/${row.id}`}>
              <Button size="sm" variant="outline" className="h-7 text-xs gap-1">
                Details
                <ArrowRight className="h-3 w-3" />
              </Button>
            </Link>
            <Link href={`/app/examinations/marks?course_offering_id=${row.courseOfferingId}&assessment_id=${row.id}`}>
              <Button size="sm" variant="primary" className="h-7 text-xs">
                Marks
              </Button>
            </Link>
          </div>
        ),
      },
    ],
    []
  );

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300">
              Course Offerings
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">Continuous Assessment Schemes</span>
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Assessment Schemes & Components
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Define multi-component evaluation frameworks (quizzes, assignments, mid-terms, and end-semesters) with weighted aggregates.
          </p>
        </div>

        <Button variant="primary" className="gap-2" onClick={() => setCreateModalOpen(true)}>
          <Plus className="h-4 w-4" />
          Configure Assessment
        </Button>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3 bg-slate-50/70 p-3 rounded-xl border border-slate-200 dark:bg-slate-900/60 dark:border-slate-800 text-xs">
        <div className="flex items-center gap-1.5 text-slate-500 font-medium">
          <Filter className="h-3.5 w-3.5" />
          Filters:
        </div>

        <select
          value={selectedDept}
          onChange={(e) => setSelectedDept(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
        >
          <option value="ALL">All Departments</option>
          <option value="Computer Science & Engineering">Computer Science & Engineering</option>
          <option value="Electronics & Communication">Electronics & Communication</option>
        </select>

        <select
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
        >
          <option value="ALL">All Types</option>
          <option value="INTERNAL">Internal Continuous</option>
          <option value="MIDTERM">Midterm</option>
          <option value="END_SEMESTER">End Semester</option>
          <option value="LABORATORY">Laboratory</option>
        </select>

        <select
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
        >
          <option value="ALL">All Statuses</option>
          <option value="OPEN">Open for Marks</option>
          <option value="SCHEDULED">Scheduled</option>
          <option value="FINALIZED">Finalized / Locked</option>
        </select>
      </div>

      {/* Enterprise DataGrid */}
      <DataGrid<Assessment>
        data={assessments}
        columns={columns}
        keyExtractor={(row) => row.id}
        loading={loading}
        searchPlaceholder="Search assessments by name, course code, title, or faculty..."
        emptyTitle="No assessment schemes configured"
        emptyDescription="Create a new assessment scheme for your course offering."
      />

      {/* Assessment Creation & Component Builder Modal */}
      <Dialog open={createModalOpen} onClose={() => setCreateModalOpen(false)}>
        <form onSubmit={handleCreateAssessment} className="p-6 space-y-5 max-w-2xl">
          <div className="border-b border-slate-200 pb-3 dark:border-slate-800">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-indigo-600" />
              Configure Assessment Scheme
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Associate an evaluation scheme with a course offering and construct its components.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="sm:col-span-2">
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Assessment Scheme Title *
              </label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. CS301 Continuous Internal Assessment (CIA)"
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>

            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Course Offering *
              </label>
              <select
                value={courseOfferingId}
                onChange={(e) => {
                  setCourseOfferingId(e.target.value);
                  if (e.target.value === "co-cs301-a") {
                    setCourseCode("CS301");
                    setCourseName("Data Structures & Algorithms");
                    setFacultyName("Dr. Ramesh Sundaram");
                  } else if (e.target.value === "co-cs302-a") {
                    setCourseCode("CS302");
                    setCourseName("Database Management Systems");
                    setFacultyName("Dr. Anita Roy");
                  } else {
                    setCourseCode("CS303");
                    setCourseName("Operating Systems & Concurrency");
                    setFacultyName("Prof. Meenakshi Sundaram");
                  }
                }}
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              >
                <option value="co-cs301-a">CS301 - Data Structures (Section A)</option>
                <option value="co-cs302-a">CS302 - Database Systems (Section A)</option>
                <option value="co-cs303-a">CS303 - Operating Systems (Section A)</option>
              </select>
            </div>

            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Assessment Category *
              </label>
              <select
                value={assessmentType}
                onChange={(e) => setAssessmentType(e.target.value as AssessmentType)}
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              >
                <option value="INTERNAL">Internal Continuous (Theory)</option>
                <option value="MIDTERM">Midterm Examination</option>
                <option value="END_SEMESTER">End Semester University Exam</option>
                <option value="LABORATORY">Practical / Lab Exam</option>
                <option value="PROJECT">Project / Dissertation</option>
                <option value="VIVA">Oral VIVA Voce</option>
              </select>
            </div>

            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Target Evaluation Date
              </label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>

            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Faculty Instructor
              </label>
              <input
                type="text"
                disabled
                value={facultyName}
                className="w-full rounded-lg border border-slate-200 bg-slate-100 p-2 text-slate-500 dark:border-slate-800 dark:bg-slate-900"
              />
            </div>
          </div>

          {/* Assessment Components Builder */}
          <div className="space-y-3 pt-2 border-t border-slate-200 dark:border-slate-800">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                  Assessment Components
                </h3>
                <p className="text-xs text-slate-400">
                  Total Weightage: {totalWeightage}% • Total Marks: {totalMaxMarks}
                </p>
              </div>
              <Button type="button" size="sm" variant="outline" onClick={handleAddComponent} className="h-7 text-xs gap-1">
                <Plus className="h-3 w-3" />
                Add Component
              </Button>
            </div>

            <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
              {components.map((c, idx) => (
                <div
                  key={c.id}
                  className="flex items-center gap-2 p-2.5 rounded-lg border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900/60 text-xs"
                >
                  <span className="font-mono text-slate-400 w-4">{idx + 1}.</span>
                  <input
                    type="text"
                    value={c.name}
                    onChange={(e) => handleUpdateComponent(c.id, "name", e.target.value)}
                    placeholder="Component Name"
                    className="flex-1 rounded border border-slate-300 bg-white px-2 py-1 dark:border-slate-700 dark:bg-slate-800 dark:text-white text-xs"
                  />
                  <div className="w-20">
                    <input
                      type="number"
                      min={1}
                      value={c.maxMarks}
                      onChange={(e) => handleUpdateComponent(c.id, "maxMarks", Number(e.target.value))}
                      placeholder="Max"
                      title="Maximum Marks"
                      className="w-full rounded border border-slate-300 bg-white px-2 py-1 dark:border-slate-700 dark:bg-slate-800 dark:text-white text-xs"
                    />
                  </div>
                  <div className="w-20">
                    <input
                      type="number"
                      min={0}
                      value={c.passingMarks}
                      onChange={(e) => handleUpdateComponent(c.id, "passingMarks", Number(e.target.value))}
                      placeholder="Pass"
                      title="Passing Marks"
                      className="w-full rounded border border-slate-300 bg-white px-2 py-1 dark:border-slate-700 dark:bg-slate-800 dark:text-white text-xs"
                    />
                  </div>
                  <div className="w-20">
                    <input
                      type="number"
                      min={1}
                      max={100}
                      value={c.weightage}
                      onChange={(e) => handleUpdateComponent(c.id, "weightage", Number(e.target.value))}
                      placeholder="Weight%"
                      title="Weightage Percent"
                      className="w-full rounded border border-slate-300 bg-white px-2 py-1 dark:border-slate-700 dark:bg-slate-800 dark:text-white text-xs"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRemoveComponent(c.id)}
                    className="text-slate-400 hover:text-rose-600 p-1"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
            <Button type="button" variant="outline" onClick={() => setCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={saving}>
              {saving ? "Saving..." : "Save Assessment Scheme"}
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
