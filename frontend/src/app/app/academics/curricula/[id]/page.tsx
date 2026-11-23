"use client";

import React, { useEffect, useState, useMemo, use } from "react";
import Link from "next/link";
import { academicsService } from "@/services/academics.service";
import {
  CurriculumScheme,
  CurriculumSemester,
  CurriculumSubject,
  ElectiveGroup,
  AcademicSubject,
  SubjectType,
  SubjectCategory,
} from "@/types/academics";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { TableSkeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { useAuth } from "@/lib/auth-context";
import {
  FileSpreadsheet,
  ArrowLeft,
  Plus,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  GitBranch,
  ShieldCheck,
  BookOpen,
  Layers,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Lock,
} from "lucide-react";

interface CurriculumDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function CurriculumBuilderPage({
  params,
}: CurriculumDetailPageProps) {
  const resolvedParams = use(params);
  const id = resolvedParams.id;
  const { showToast } = useToast();
  const { hasPermission } = useAuth();

  const [curriculum, setCurriculum] = useState<CurriculumScheme | null>(null);
  const [availableSubjects, setAvailableSubjects] = useState<AcademicSubject[]>(
    [],
  );
  const [activeTab, setActiveTab] = useState<
    "builder" | "electives" | "validation" | "history"
  >("builder");
  const [selectedSemesterNumber, setSelectedSemesterNumber] =
    useState<number>(1);
  const [loading, setLoading] = useState(true);

  // Add Subject to Semester Modal
  const [addSubjectModalOpen, setAddSubjectModalOpen] = useState(false);
  const [targetSemester, setTargetSemester] = useState<number>(1);
  const [selectedCatalogSubjectId, setSelectedCatalogSubjectId] = useState("");
  const [customCredits, setCustomCredits] = useState<number>(3);
  const [isSubmittingSubject, setIsSubmittingSubject] = useState(false);

  // Create Elective Group Modal
  const [createElectiveModalOpen, setCreateElectiveModalOpen] = useState(false);
  const [electiveGroupName, setElectiveGroupName] = useState(
    "Professional Elective I",
  );
  const [electiveMin, setElectiveMin] = useState<number>(1);
  const [electiveMax, setElectiveMax] = useState<number>(1);
  const [selectedElectiveSubjectIds, setSelectedElectiveSubjectIds] = useState<
    string[]
  >([]);

  // Publish Dialog
  const [publishModalOpen, setPublishModalOpen] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);

  const canManage = hasPermission("academics:curriculum:manage");

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [currRes, subRes] = await Promise.all([
          academicsService.getCurriculumSchemeById(id),
          academicsService.getAcademicSubjects(),
        ]);
        setCurriculum(currRes.data);
        setAvailableSubjects(subRes.data);
        if (currRes.data?.semesters.length) {
          setSelectedSemesterNumber(currRes.data.semesters[0].semesterNumber);
        }
      } catch (err) {
        console.error("Failed to load curriculum:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [id]);

  // Frontend Validation Analysis
  const validationResults = useMemo(() => {
    if (!curriculum)
      return {
        errors: [],
        warnings: [],
        isValid: true,
        currentTotalCredits: 0,
      };

    const errors: string[] = [];
    const warnings: string[] = [];

    // Calculate total credits
    const currentTotalCredits = curriculum.semesters.reduce((sum, sem) => {
      const semTotal = sem.subjects.reduce((sSum, s) => sSum + s.credits, 0);
      return sum + semTotal;
    }, 0);

    // 1. Credit discrepancy check
    if (currentTotalCredits !== curriculum.totalCredits) {
      warnings.push(
        `Mapped credits (${currentTotalCredits} Cr) do not match the prescribed curriculum total of ${curriculum.totalCredits} Cr.`,
      );
    }

    // 2. Duplicate subject check
    const seenSubjects = new Map<string, number>();
    for (const sem of curriculum.semesters) {
      for (const sub of sem.subjects) {
        const key = sub.subjectCode.toUpperCase();
        if (seenSubjects.has(key)) {
          errors.push(
            `Duplicate subject "${sub.subjectCode} - ${sub.subjectName}" is assigned in both Semester ${seenSubjects.get(key)} and Semester ${sem.semesterNumber}.`,
          );
        } else {
          seenSubjects.set(key, sem.semesterNumber);
        }
      }
    }

    // 3. Empty semester check
    for (const sem of curriculum.semesters) {
      if (sem.subjects.length === 0) {
        warnings.push(
          `Semester ${sem.semesterNumber} has 0 subjects assigned.`,
        );
      }
    }

    // 4. Elective groups checks
    for (const sem of curriculum.semesters) {
      if (sem.electiveGroups) {
        for (const eg of sem.electiveGroups) {
          if (eg.minSelect > eg.maxSelect) {
            errors.push(
              `Elective group "${eg.name}" in Sem ${sem.semesterNumber} has min selection (${eg.minSelect}) greater than max (${eg.maxSelect}).`,
            );
          }
          if (eg.subjects.length < eg.maxSelect) {
            warnings.push(
              `Elective group "${eg.name}" has fewer subjects (${eg.subjects.length}) than maximum allowed selection (${eg.maxSelect}).`,
            );
          }
        }
      }
    }

    return {
      errors,
      warnings,
      isValid: errors.length === 0,
      currentTotalCredits,
    };
  }, [curriculum]);

  // Add Subject to Semester
  const handleAddSubject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!curriculum || !selectedCatalogSubjectId) return;

    const catalogSub = availableSubjects.find(
      (s) => s.id === selectedCatalogSubjectId,
    );
    if (!catalogSub) return;

    try {
      setIsSubmittingSubject(true);
      const newCurrSubject: CurriculumSubject = {
        id: `cs-${Date.now()}`,
        subjectId: catalogSub.id,
        subjectCode: catalogSub.code,
        subjectName: catalogSub.name,
        credits: Number(customCredits),
        type: catalogSub.type,
        category: catalogSub.category,
        lectureHours: catalogSub.lectureHours,
        tutorialHours: catalogSub.tutorialHours,
        practicalHours: catalogSub.practicalHours,
      };

      const res = await academicsService.addSubjectToCurriculum(
        curriculum.id,
        targetSemester,
        newCurrSubject,
      );

      if (res.success) {
        setCurriculum({ ...res.data });
        showToast({
          title: "Subject Added",
          message: `Added ${catalogSub.code} to Semester ${targetSemester}`,
          type: "success",
        });
        setAddSubjectModalOpen(false);
        setSelectedCatalogSubjectId("");
      }
    } catch (err: any) {
      showToast({
        title: "Failed to add subject",
        message: err.message,
        type: "error",
      });
    } finally {
      setIsSubmittingSubject(false);
    }
  };

  // Remove Subject from Semester
  const handleRemoveSubject = async (
    semesterNumber: number,
    subjectId: string,
  ) => {
    if (!curriculum) return;
    try {
      const res = await academicsService.removeSubjectFromCurriculum(
        curriculum.id,
        semesterNumber,
        subjectId,
      );
      if (res.success) {
        setCurriculum({ ...res.data });
        showToast({ title: "Subject Removed from Semester", type: "info" });
      }
    } catch (err: any) {
      showToast({
        title: "Failed to remove subject",
        message: err.message,
        type: "error",
      });
    }
  };

  // Add Elective Group
  const handleCreateElectiveGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!curriculum) return;

    const groupSubjects = availableSubjects
      .filter((s) => selectedElectiveSubjectIds.includes(s.id))
      .map((s) => ({
        id: `eg-sub-${s.id}`,
        subjectId: s.id,
        subjectCode: s.code,
        subjectName: s.name,
        credits: s.credits,
        type: s.type,
        category: s.category,
        lectureHours: s.lectureHours,
        tutorialHours: s.tutorialHours,
        practicalHours: s.practicalHours,
        isElective: true,
      }));

    const newGroup: ElectiveGroup = {
      id: `eg-${Date.now()}`,
      name: electiveGroupName,
      code: electiveGroupName.replace(/\s+/g, "_").toUpperCase(),
      minSelect: electiveMin,
      maxSelect: electiveMax,
      subjects: groupSubjects,
    };

    try {
      const res = await academicsService.createElectiveGroup(
        curriculum.id,
        selectedSemesterNumber,
        newGroup,
      );
      if (res.success) {
        setCurriculum({ ...res.data });
        showToast({
          title: "Elective Group Created",
          message: `Created group ${newGroup.name} in Semester ${selectedSemesterNumber}`,
          type: "success",
        });
        setCreateElectiveModalOpen(false);
        setSelectedElectiveSubjectIds([]);
      }
    } catch (err: any) {
      showToast({
        title: "Failed to create elective group",
        message: err.message,
        type: "error",
      });
    }
  };

  // Publish Scheme
  const handlePublishCurriculum = async () => {
    if (!curriculum) return;
    try {
      setIsPublishing(true);
      const res = await academicsService.publishCurriculumScheme(curriculum.id);
      if (res.success) {
        setCurriculum({ ...res.data });
        showToast({
          title: "Curriculum Officially Published",
          message: `Gazetted ${curriculum.regulation} (${curriculum.version}) as active version.`,
          type: "success",
        });
        setPublishModalOpen(false);
      }
    } catch (err: any) {
      showToast({
        title: "Publish failed",
        message: err.message,
        type: "error",
      });
    } finally {
      setIsPublishing(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-24 bg-slate-900/60 rounded-xl animate-pulse" />
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div
              key={i}
              className="h-24 bg-slate-900/60 rounded-xl animate-pulse"
            />
          ))}
        </div>
        <TableSkeleton rows={5} />
      </div>
    );
  }

  if (!curriculum) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-12 text-center">
        <FileSpreadsheet className="mx-auto h-12 w-12 text-slate-600 mb-3" />
        <h3 className="text-lg font-semibold text-white">
          Curriculum Scheme Not Found
        </h3>
        <p className="text-xs text-slate-400 mt-1 mb-6">
          The requested curriculum identifier does not exist.
        </p>
        <Link href="/app/academics/curricula">
          <Button
            variant="outline"
            size="sm"
            leftIcon={<ArrowLeft className="h-4 w-4" />}
          >
            Back to Curricula Schemes
          </Button>
        </Link>
      </div>
    );
  }

  const currentSemesterObj = curriculum.semesters.find(
    (s) => s.semesterNumber === selectedSemesterNumber,
  );

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Link
              href="/app/academics"
              className="hover:text-white transition-colors"
            >
              Academics
            </Link>
            <span>/</span>
            <Link
              href="/app/academics/curricula"
              className="hover:text-white transition-colors"
            >
              Curricula
            </Link>
            <span>/</span>
            <span className="text-white font-mono">
              {curriculum.regulation} {curriculum.version}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              {curriculum.programName}
            </h1>
            <Badge variant="info">{curriculum.regulation}</Badge>
            <Badge variant="secondary">{curriculum.version}</Badge>
            {curriculum.isActiveVersion ? (
              <Badge variant="success" dot>
                Active Regulation
              </Badge>
            ) : (
              <Badge variant="warning">Historical / Draft</Badge>
            )}
          </div>
          <p className="mt-1 text-xs text-slate-400">
            {curriculum.department} • Effective: {curriculum.effectiveDate} •
            Total Prescribed: {curriculum.totalCredits} Credits
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/app/academics/curricula">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<ArrowLeft className="h-3.5 w-3.5" />}
            >
              Back to Schemes
            </Button>
          </Link>
          {curriculum.status !== "PUBLISHED" && (
            <Button
              variant="primary"
              size="sm"
              leftIcon={<ShieldCheck className="h-3.5 w-3.5" />}
              onClick={() => setPublishModalOpen(true)}
            >
              Publish Scheme
            </Button>
          )}
        </div>
      </div>

      {/* KPI Stats Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="text-[11px] font-medium text-slate-400">
            Prescribed Credits
          </div>
          <div className="mt-1 text-2xl font-bold text-indigo-400 font-mono">
            {validationResults.currentTotalCredits} / {curriculum.totalCredits}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            {validationResults.currentTotalCredits ===
            curriculum.totalCredits ? (
              <span className="text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3" /> Fully Balanced
              </span>
            ) : (
              <span className="text-amber-400 flex items-center gap-1">
                <AlertTriangle className="h-3 w-3" /> Credit Discrepancy
              </span>
            )}
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="text-[11px] font-medium text-slate-400">
            Total Semesters
          </div>
          <div className="mt-1 text-2xl font-bold text-white font-mono">
            {curriculum.totalSemesters} Semesters
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            4 Academic Years (UG)
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="text-[11px] font-medium text-slate-400">
            Subjects Mapped
          </div>
          <div className="mt-1 text-2xl font-bold text-emerald-400 font-mono">
            {curriculum.semesters.reduce(
              (acc, s) => acc + s.subjects.length,
              0,
            )}{" "}
            Courses
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            Core + Labs + Electives
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="text-[11px] font-medium text-slate-400">
            Frontend Validation
          </div>
          <div className="mt-1 text-2xl font-bold font-mono">
            {validationResults.isValid &&
            validationResults.warnings.length === 0 ? (
              <span className="text-emerald-400">PASS</span>
            ) : validationResults.errors.length > 0 ? (
              <span className="text-red-400">
                {validationResults.errors.length} Errors
              </span>
            ) : (
              <span className="text-amber-400">
                {validationResults.warnings.length} Warnings
              </span>
            )}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            Preliminary Engine Check
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-slate-800 text-xs">
        <button
          onClick={() => setActiveTab("builder")}
          className={`px-4 py-2.5 font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "builder"
              ? "border-indigo-500 text-white"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <FileSpreadsheet className="h-3.5 w-3.5" />
          Semester Structure & Builder
        </button>
        <button
          onClick={() => setActiveTab("electives")}
          className={`px-4 py-2.5 font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "electives"
              ? "border-indigo-500 text-white"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Layers className="h-3.5 w-3.5" />
          Elective Baskets & Tracks
        </button>
        <button
          onClick={() => setActiveTab("validation")}
          className={`px-4 py-2.5 font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "validation"
              ? "border-indigo-500 text-white"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
          Curriculum Validation
          {(validationResults.errors.length > 0 ||
            validationResults.warnings.length > 0) && (
            <span className="rounded-full bg-amber-500/20 px-1.5 py-0.2 text-[10px] font-mono text-amber-300">
              {validationResults.errors.length +
                validationResults.warnings.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab("history")}
          className={`px-4 py-2.5 font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "history"
              ? "border-indigo-500 text-white"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <GitBranch className="h-3.5 w-3.5" />
          Version Audit Trail
        </button>
      </div>

      {/* Tab 1: Semester Structure Builder */}
      {activeTab === "builder" && (
        <div className="space-y-6">
          {/* Semester Selector Pills */}
          <div className="flex flex-wrap items-center gap-2">
            {curriculum.semesters.map((sem) => {
              const semCredits = sem.subjects.reduce(
                (sum, s) => sum + s.credits,
                0,
              );
              const isSelected = sem.semesterNumber === selectedSemesterNumber;
              return (
                <button
                  key={sem.semesterNumber}
                  onClick={() => setSelectedSemesterNumber(sem.semesterNumber)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                    isSelected
                      ? "bg-indigo-600 border-indigo-500 text-white shadow-md shadow-indigo-600/20"
                      : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700"
                  }`}
                >
                  <span>Semester {sem.semesterNumber}</span>
                  <span
                    className={`ml-2 text-[10px] font-mono ${isSelected ? "text-indigo-200" : "text-slate-500"}`}
                  >
                    ({semCredits} Cr • {sem.subjects.length} courses)
                  </span>
                </button>
              );
            })}
          </div>

          {/* Active Semester Subjects Table */}
          {currentSemesterObj && (
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>
                    Semester {currentSemesterObj.semesterNumber} Structure
                  </CardTitle>
                  <CardDescription>
                    Prescribed course lineup •{" "}
                    {currentSemesterObj.subjects.reduce(
                      (sum, s) => sum + s.credits,
                      0,
                    )}{" "}
                    Total Credits
                  </CardDescription>
                </div>
                <Button
                  variant="primary"
                  size="sm"
                  leftIcon={<Plus className="h-3.5 w-3.5" />}
                  onClick={() => {
                    setTargetSemester(currentSemesterObj.semesterNumber);
                    setAddSubjectModalOpen(true);
                  }}
                >
                  Add Subject
                </Button>
              </CardHeader>
              <CardContent className="p-0">
                {currentSemesterObj.subjects.length === 0 ? (
                  <div className="p-12 text-center text-xs text-slate-400">
                    <p>
                      No subjects mapped to Semester{" "}
                      {currentSemesterObj.semesterNumber} yet.
                    </p>
                    <Button
                      variant="outline"
                      size="sm"
                      className="mt-3"
                      leftIcon={<Plus className="h-3.5 w-3.5" />}
                      onClick={() => {
                        setTargetSemester(currentSemesterObj.semesterNumber);
                        setAddSubjectModalOpen(true);
                      }}
                    >
                      Assign Subject from Catalog
                    </Button>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs text-left text-slate-300">
                      <thead className="bg-slate-950/60 text-[11px] font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
                        <tr>
                          <th className="px-5 py-3">Code</th>
                          <th className="px-4 py-3">Subject Name</th>
                          <th className="px-4 py-3">Category</th>
                          <th className="px-4 py-3">Type</th>
                          <th className="px-4 py-3">L-T-P</th>
                          <th className="px-4 py-3">Credits</th>
                          <th className="px-4 py-3 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60">
                        {currentSemesterObj.subjects.map((sub) => (
                          <tr
                            key={sub.id}
                            className="hover:bg-slate-800/40 transition-colors"
                          >
                            <td className="px-5 py-3.5 font-mono font-semibold text-white">
                              <Link
                                href={`/app/academics/subjects/${sub.subjectId || sub.subjectCode}`}
                                className="hover:text-indigo-400 transition-colors"
                              >
                                {sub.subjectCode}
                              </Link>
                            </td>
                            <td className="px-4 py-3.5 font-medium text-slate-200">
                              {sub.subjectName}
                            </td>
                            <td className="px-4 py-3.5">
                              <span className="font-mono text-xs text-slate-400">
                                {sub.category.replace("_", " ")}
                              </span>
                            </td>
                            <td className="px-4 py-3.5">
                              <Badge
                                variant={
                                  sub.type === "THEORY" ? "info" : "success"
                                }
                              >
                                {sub.type}
                              </Badge>
                            </td>
                            <td className="px-4 py-3.5 font-mono text-slate-300">
                              {sub.lectureHours}-{sub.tutorialHours}-
                              {sub.practicalHours}
                            </td>
                            <td className="px-4 py-3.5 font-mono font-bold text-indigo-400">
                              {sub.credits} Cr
                            </td>
                            <td className="px-4 py-3.5 text-right">
                              <button
                                onClick={() =>
                                  handleRemoveSubject(
                                    currentSemesterObj.semesterNumber,
                                    sub.id,
                                  )
                                }
                                className="p-1 text-slate-400 hover:text-red-400 transition-colors rounded hover:bg-red-500/10"
                                title="Remove from semester"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Tab 2: Elective Groups */}
      {activeTab === "electives" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-white">
                Semester {selectedSemesterNumber} Elective Baskets
              </h3>
              <p className="text-xs text-slate-400">
                Groupings of specialized elective courses offering choice-based
                credit enrollment.
              </p>
            </div>
            <Button
              variant="primary"
              size="sm"
              leftIcon={<Plus className="h-3.5 w-3.5" />}
              onClick={() => setCreateElectiveModalOpen(true)}
            >
              New Elective Basket
            </Button>
          </div>

          {currentSemesterObj?.electiveGroups &&
          currentSemesterObj.electiveGroups.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {currentSemesterObj.electiveGroups.map((eg) => (
                <Card key={eg.id}>
                  <CardHeader className="flex flex-row items-center justify-between pb-3">
                    <div>
                      <CardTitle className="text-sm">{eg.name}</CardTitle>
                      <CardDescription>
                        Rule: Choose {eg.minSelect} of {eg.subjects.length}{" "}
                        courses
                      </CardDescription>
                    </div>
                    <Badge variant="info">Elective Group</Badge>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="divide-y divide-slate-800 text-xs">
                      {eg.subjects.map((sub) => (
                        <div
                          key={sub.id}
                          className="py-2 flex items-center justify-between"
                        >
                          <div>
                            <span className="font-mono font-medium text-white">
                              {sub.subjectCode}
                            </span>
                            <span className="ml-2 text-slate-300">
                              {sub.subjectName}
                            </span>
                          </div>
                          <span className="font-mono text-indigo-400 font-semibold">
                            {sub.credits} Cr
                          </span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-8 text-center text-xs text-slate-400">
              No elective baskets defined for Semester {selectedSemesterNumber}.
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Curriculum Validation */}
      {activeTab === "validation" && (
        <div className="space-y-6">
          <div className="rounded-xl border border-indigo-500/20 bg-indigo-500/10 p-4 text-xs text-indigo-200">
            <h4 className="font-semibold text-white flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-indigo-400" />
              Preliminary Frontend Academic Integrity Validation
            </h4>
            <p className="mt-1">
              Validates semester integrity, credit balance, duplicate
              assignments, and elective rules prior to Academic Council
              ratification.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm text-red-400 flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  Critical Integrity Errors ({validationResults.errors.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {validationResults.errors.length === 0 ? (
                  <p className="text-xs text-emerald-400 flex items-center gap-1.5">
                    <CheckCircle2 className="h-4 w-4" /> No duplicate course
                    collisions or structure faults.
                  </p>
                ) : (
                  <ul className="space-y-2 text-xs text-red-300">
                    {validationResults.errors.map((err, idx) => (
                      <li
                        key={idx}
                        className="p-2 rounded bg-red-500/10 border border-red-500/20"
                      >
                        {err}
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm text-amber-400 flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  Advisory Warnings ({validationResults.warnings.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {validationResults.warnings.length === 0 ? (
                  <p className="text-xs text-emerald-400 flex items-center gap-1.5">
                    <CheckCircle2 className="h-4 w-4" /> All semesters are
                    populated and credits match 100%.
                  </p>
                ) : (
                  <ul className="space-y-2 text-xs text-amber-300">
                    {validationResults.warnings.map((warn, idx) => (
                      <li
                        key={idx}
                        className="p-2 rounded bg-amber-500/10 border border-amber-500/20"
                      >
                        {warn}
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Tab 4: Version Audit Trail */}
      {activeTab === "history" && (
        <Card>
          <CardHeader>
            <CardTitle>Curriculum Scheme Version History</CardTitle>
            <CardDescription>
              Autonomous Board of Studies and Academic Council revision history.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left text-slate-300">
                <thead className="bg-slate-950/60 text-[11px] font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="px-5 py-3">Version</th>
                    <th className="px-4 py-3">Date</th>
                    <th className="px-4 py-3">Sign-off Authority</th>
                    <th className="px-4 py-3">Revision Notes</th>
                    <th className="px-4 py-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {curriculum.versionHistory.map((v, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/40">
                      <td className="px-5 py-3.5 font-mono font-semibold text-white">
                        {v.version}
                      </td>
                      <td className="px-4 py-3.5 font-mono text-slate-400">
                        {v.date}
                      </td>
                      <td className="px-4 py-3.5 text-slate-200">{v.author}</td>
                      <td className="px-4 py-3.5 text-slate-300">{v.notes}</td>
                      <td className="px-4 py-3.5">
                        <Badge
                          variant={
                            v.status === "PUBLISHED" ? "success" : "info"
                          }
                          dot
                        >
                          {v.status}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Add Subject to Semester Modal */}
      <Dialog
        open={addSubjectModalOpen}
        onClose={() => setAddSubjectModalOpen(false)}
        title={`Assign Subject to Semester ${targetSemester}`}
      >
        <form onSubmit={handleAddSubject} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Select Subject from Catalog{" "}
              <span className="text-red-400">*</span>
            </label>
            <select
              value={selectedCatalogSubjectId}
              onChange={(e) => {
                setSelectedCatalogSubjectId(e.target.value);
                const match = availableSubjects.find(
                  (s) => s.id === e.target.value,
                );
                if (match) setCustomCredits(match.credits);
              }}
              className="w-full h-9 rounded-lg border border-slate-700 bg-slate-900 px-3 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
            >
              <option value="">-- Choose Subject --</option>
              {availableSubjects.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.code} - {s.name} ({s.credits} Cr • {s.departmentName})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Semester Prescribed Credits
            </label>
            <Input
              type="number"
              value={customCredits}
              onChange={(e) => setCustomCredits(Number(e.target.value))}
              min="1"
              max="20"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setAddSubjectModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={isSubmittingSubject}
              disabled={!selectedCatalogSubjectId}
            >
              Assign to Semester
            </Button>
          </div>
        </form>
      </Dialog>

      {/* Create Elective Basket Modal */}
      <Dialog
        open={createElectiveModalOpen}
        onClose={() => setCreateElectiveModalOpen(false)}
        title={`New Elective Basket in Semester ${selectedSemesterNumber}`}
      >
        <form onSubmit={handleCreateElectiveGroup} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Elective Basket Name
            </label>
            <Input
              value={electiveGroupName}
              onChange={(e) => setElectiveGroupName(e.target.value)}
              placeholder="e.g. Professional Elective I"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Min Selection
              </label>
              <Input
                type="number"
                value={electiveMin}
                onChange={(e) => setElectiveMin(Number(e.target.value))}
                min="1"
                max="5"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Max Selection
              </label>
              <Input
                type="number"
                value={electiveMax}
                onChange={(e) => setElectiveMax(Number(e.target.value))}
                min="1"
                max="5"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Select Elective Pool Subjects
            </label>
            <div className="max-h-48 overflow-y-auto rounded-lg border border-slate-700 bg-slate-900 p-2 space-y-1">
              {availableSubjects.map((sub) => {
                const checked = selectedElectiveSubjectIds.includes(sub.id);
                return (
                  <label
                    key={sub.id}
                    className="flex items-center gap-2 p-1.5 rounded hover:bg-slate-800 text-xs text-slate-200 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => {
                        if (checked) {
                          setSelectedElectiveSubjectIds(
                            selectedElectiveSubjectIds.filter(
                              (x) => x !== sub.id,
                            ),
                          );
                        } else {
                          setSelectedElectiveSubjectIds([
                            ...selectedElectiveSubjectIds,
                            sub.id,
                          ]);
                        }
                      }}
                      className="rounded border-slate-700 bg-slate-950 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span className="font-mono text-indigo-400">
                      {sub.code}
                    </span>
                    <span>{sub.name}</span>
                  </label>
                );
              })}
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setCreateElectiveModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={selectedElectiveSubjectIds.length === 0}
            >
              Save Elective Basket
            </Button>
          </div>
        </form>
      </Dialog>

      {/* Publish Scheme Dialog */}
      <Dialog
        open={publishModalOpen}
        onClose={() => setPublishModalOpen(false)}
        title="Publish Curriculum Scheme"
      >
        <div className="space-y-3 text-xs text-slate-300">
          <p>
            Publishing gazettes{" "}
            <strong className="text-white">
              {curriculum.programName} ({curriculum.regulation}{" "}
              {curriculum.version})
            </strong>{" "}
            as the official active regulation for cohort degree progression.
          </p>
          <div className="rounded-lg border border-amber-500/20 bg-amber-500/10 p-3 text-amber-200">
            Once published, the structure becomes authoritative for course
            offerings and student graduation audits.
          </div>
          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPublishModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handlePublishCurriculum}
              isLoading={isPublishing}
            >
              Confirm Publication
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
