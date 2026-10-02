"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { academicsService } from "@/services/academics.service";
import {
  AcademicSubject,
  CurriculumScheme,
  CourseOfferingDetail,
} from "@/types/academics";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { TableSkeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import {
  BookOpen,
  ArrowLeft,
  FileSpreadsheet,
  CheckSquare,
  Users,
  Clock,
  History,
  CheckCircle2,
  Calendar,
  Layers,
  GraduationCap,
  ExternalLink,
} from "lucide-react";

interface SubjectDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function SubjectDetailPage({ params }: SubjectDetailPageProps) {
  const resolvedParams = use(params);
  const id = resolvedParams.id;
  const { showToast } = useToast();

  const [subject, setSubject] = useState<AcademicSubject | null>(null);
  const [curricula, setCurricula] = useState<CurriculumScheme[]>([]);
  const [offerings, setOfferings] = useState<CourseOfferingDetail[]>([]);
  const [activeTab, setActiveTab] = useState<"overview" | "curriculum" | "offerings" | "faculty" | "history">("overview");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadSubjectData() {
      setLoading(true);
      try {
        const [subRes, currRes, offRes] = await Promise.all([
          academicsService.getAcademicSubjectById(id),
          academicsService.getCurriculumSchemes(),
          academicsService.getCourseOfferingDetails(),
        ]);

        if (!subRes.data) {
          setSubject(null);
        } else {
          setSubject(subRes.data);
          // Filter curricula that include this subject
          const matchedCurr = currRes.data.filter((c) =>
            c.semesters.some((sem) =>
              sem.subjects.some((s) => s.subjectId === subRes.data!.id || s.subjectCode === subRes.data!.code)
            )
          );
          setCurricula(matchedCurr);

          // Filter course offerings for this subject
          const matchedOff = offRes.data.filter(
            (o) => o.subjectId === subRes.data!.id || o.subjectCode === subRes.data!.code
          );
          setOfferings(matchedOff);
        }
      } catch (err) {
        console.error("Failed to load subject details:", err);
      } finally {
        setLoading(false);
      }
    }
    loadSubjectData();
  }, [id]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-24 bg-slate-900/60 rounded-xl animate-pulse" />
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 bg-slate-900/60 rounded-xl animate-pulse" />
          ))}
        </div>
        <TableSkeleton rows={4} />
      </div>
    );
  }

  if (!subject) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-12 text-center">
        <BookOpen className="mx-auto h-12 w-12 text-slate-600 mb-3" />
        <h3 className="text-lg font-semibold text-white">Subject Not Found</h3>
        <p className="text-xs text-slate-400 mt-1 mb-6">
          The requested subject with identifier &ldquo;{id}&rdquo; does not exist in the academic catalog.
        </p>
        <Link href="/app/academics/subjects">
          <Button variant="outline" size="sm" leftIcon={<ArrowLeft className="h-4 w-4" />}>
            Back to Subjects Catalog
          </Button>
        </Link>
      </div>
    );
  }

  // Aggregate faculty across offerings
  const assignedFaculty = offerings.flatMap((o) =>
    o.facultyAssignments.map((f) => ({
      ...f,
      offeringSection: `Sem ${o.semester} Sec ${o.section}`,
      offeringAcademicYear: o.academicYear,
    }))
  );

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Link href="/app/academics" className="hover:text-white transition-colors">
              Academics
            </Link>
            <span>/</span>
            <Link href="/app/academics/subjects" className="hover:text-white transition-colors">
              Subjects
            </Link>
            <span>/</span>
            <span className="text-white font-mono">{subject.code}</span>
          </div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white font-mono">
              {subject.code}
            </h1>
            <span className="text-slate-500">•</span>
            <span className="text-xl font-medium text-slate-200">{subject.name}</span>
            <Badge variant="success" dot className="ml-2">
              {subject.status}
            </Badge>
          </div>
          <p className="mt-1 text-xs text-slate-400">
            {subject.departmentName} • {subject.category.replace("_", " ")}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/app/academics/subjects">
            <Button variant="outline" size="sm" leftIcon={<ArrowLeft className="h-3.5 w-3.5" />}>
              Back to Catalog
            </Button>
          </Link>
          <Link href="/app/academics/course-offerings">
            <Button variant="primary" size="sm" leftIcon={<CheckSquare className="h-3.5 w-3.5" />}>
              Create Course Offering
            </Button>
          </Link>
        </div>
      </div>

      {/* Metrics Banner */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="text-[11px] font-medium text-slate-400">Credits</div>
          <div className="mt-1 text-2xl font-bold text-indigo-400 font-mono">
            {subject.credits} Cr
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">CBCS Normalized</div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="text-[11px] font-medium text-slate-400">Contact Hours (L-T-P)</div>
          <div className="mt-1 text-2xl font-bold text-white font-mono">
            {subject.lectureHours}-{subject.tutorialHours}-{subject.practicalHours}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">Weekly Periods</div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="text-[11px] font-medium text-slate-400">Curricula Enrolled In</div>
          <div className="mt-1 text-2xl font-bold text-emerald-400 font-mono">
            {curricula.length} Schemes
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">R-2024 / R-2026 regulations</div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="text-[11px] font-medium text-slate-400">Active Course Offerings</div>
          <div className="mt-1 text-2xl font-bold text-sky-400 font-mono">
            {offerings.length} Sections
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">Current Academic Year</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-slate-800 text-xs">
        <button
          onClick={() => setActiveTab("overview")}
          className={`px-4 py-2.5 font-medium border-b-2 transition-colors ${
            activeTab === "overview"
              ? "border-indigo-500 text-white"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Overview & Syllabus
        </button>
        <button
          onClick={() => setActiveTab("curriculum")}
          className={`px-4 py-2.5 font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "curriculum"
              ? "border-indigo-500 text-white"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Curriculum Usage
          <span className="rounded-full bg-slate-800 px-1.5 py-0.2 text-[10px] font-mono text-slate-400">
            {curricula.length}
          </span>
        </button>
        <button
          onClick={() => setActiveTab("offerings")}
          className={`px-4 py-2.5 font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "offerings"
              ? "border-indigo-500 text-white"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Course Offerings
          <span className="rounded-full bg-slate-800 px-1.5 py-0.2 text-[10px] font-mono text-slate-400">
            {offerings.length}
          </span>
        </button>
        <button
          onClick={() => setActiveTab("faculty")}
          className={`px-4 py-2.5 font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
            activeTab === "faculty"
              ? "border-indigo-500 text-white"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Faculty Instructors
          <span className="rounded-full bg-slate-800 px-1.5 py-0.2 text-[10px] font-mono text-slate-400">
            {assignedFaculty.length}
          </span>
        </button>
        <button
          onClick={() => setActiveTab("history")}
          className={`px-4 py-2.5 font-medium border-b-2 transition-colors ${
            activeTab === "history"
              ? "border-indigo-500 text-white"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Academic Lifecycle History
        </button>
      </div>

      {/* Tab 1: Overview */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Course Description & Objectives</CardTitle>
                <CardDescription>
                  Autonomous academic curriculum syllabus outline.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 text-xs text-slate-300 leading-relaxed">
                <p>{subject.description || "Comprehensive foundational syllabus covering theoretical concepts, algorithms, and practical implementations as approved by the Board of Studies."}</p>

                <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-4 space-y-3">
                  <h4 className="text-xs font-semibold text-white">Prerequisites & Corequisites</h4>
                  {subject.prerequisites && subject.prerequisites.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {subject.prerequisites.map((p) => (
                        <span key={p} className="rounded bg-indigo-500/10 px-2 py-1 text-xs font-mono text-indigo-300 border border-indigo-500/20">
                          {p}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-500">None specified. Open to eligible cohort levels.</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Specification Matrix</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="divide-y divide-slate-800 text-xs">
                  <div className="flex justify-between px-4 py-2.5">
                    <span className="text-slate-400">Subject Type</span>
                    <span className="font-semibold text-white">{subject.type}</span>
                  </div>
                  <div className="flex justify-between px-4 py-2.5">
                    <span className="text-slate-400">Academic Category</span>
                    <span className="font-semibold text-white">{subject.category.replace("_", " ")}</span>
                  </div>
                  <div className="flex justify-between px-4 py-2.5">
                    <span className="text-slate-400">Owning Department</span>
                    <span className="font-semibold text-white">{subject.departmentName}</span>
                  </div>
                  <div className="flex justify-between px-4 py-2.5">
                    <span className="text-slate-400">Status</span>
                    <Badge variant="success" dot>{subject.status}</Badge>
                  </div>
                  <div className="flex justify-between px-4 py-2.5">
                    <span className="text-slate-400">Total Credits</span>
                    <span className="font-mono font-bold text-indigo-400">{subject.credits} Credits</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Tab 2: Curriculum Usage */}
      {activeTab === "curriculum" && (
        <Card>
          <CardHeader>
            <CardTitle>Curricula Incorporating {subject.code}</CardTitle>
            <CardDescription>
              Degree schemes and regulations that include this subject within their prescribed semester structure.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {curricula.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400">
                This subject has not yet been assigned to any curriculum scheme.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left text-slate-300">
                  <thead className="bg-slate-950/60 text-[11px] font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="px-5 py-3">Program & Scheme</th>
                      <th className="px-4 py-3">Regulation</th>
                      <th className="px-4 py-3">Prescribed Semester</th>
                      <th className="px-4 py-3">Curriculum Status</th>
                      <th className="px-4 py-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {curricula.map((c) => {
                      const semNumber = c.semesters.find((sem) =>
                        sem.subjects.some((s) => s.subjectId === subject.id || s.subjectCode === subject.code)
                      )?.semesterNumber || 1;

                      return (
                        <tr key={c.id} className="hover:bg-slate-800/40 transition-colors">
                          <td className="px-5 py-3.5 font-medium text-white">
                            <div>{c.programName}</div>
                            <div className="text-[11px] text-slate-400 font-normal">{c.department}</div>
                          </td>
                          <td className="px-4 py-3.5 font-mono">{c.regulation} ({c.version})</td>
                          <td className="px-4 py-3.5 font-mono">Semester {semNumber}</td>
                          <td className="px-4 py-3.5">
                            <Badge variant={c.status === "PUBLISHED" ? "success" : "info"} dot>
                              {c.status}
                            </Badge>
                          </td>
                          <td className="px-4 py-3.5 text-right">
                            <Link href={`/app/academics/curricula/${c.id}`}>
                              <Button variant="ghost" size="sm" className="h-7 text-xs text-indigo-400">
                                View Curriculum
                              </Button>
                            </Link>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab 3: Course Offerings */}
      {activeTab === "offerings" && (
        <Card>
          <CardHeader>
            <CardTitle>Course Offerings Roster</CardTitle>
            <CardDescription>
              Active and planned classroom offerings for this subject across departments and academic terms.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {offerings.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400">
                No active course offerings found for {subject.code}.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left text-slate-300">
                  <thead className="bg-slate-950/60 text-[11px] font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="px-5 py-3">Section & Term</th>
                      <th className="px-4 py-3">Program</th>
                      <th className="px-4 py-3">Assigned Faculty</th>
                      <th className="px-4 py-3">Enrolled</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {offerings.map((off) => (
                      <tr key={off.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="px-5 py-3.5 font-medium text-white">
                          <div>Sem {off.semester} • Section {off.section}</div>
                          <div className="text-[11px] text-slate-400 font-mono">AY {off.academicYear}</div>
                        </td>
                        <td className="px-4 py-3.5 text-slate-300">{off.programName}</td>
                        <td className="px-4 py-3.5 text-slate-200">
                          {off.facultyAssignments.length > 0 ? (
                            off.facultyAssignments.map((f) => (
                              <div key={f.id} className="text-xs">
                                <span className="font-medium">{f.facultyName}</span>
                                <span className="text-[10px] text-slate-400 ml-1.5 font-mono">({f.role.replace("_", " ")})</span>
                              </div>
                            ))
                          ) : (
                            <span className="text-amber-400 font-medium italic">Unassigned</span>
                          )}
                        </td>
                        <td className="px-4 py-3.5 font-mono">
                          {off.enrolledCount} / {off.maxCapacity} Students
                        </td>
                        <td className="px-4 py-3.5">
                          <Badge variant={off.status === "ACTIVE" ? "success" : "info"} dot>
                            {off.status}
                          </Badge>
                        </td>
                        <td className="px-4 py-3.5 text-right">
                          <Link href={`/app/academics/course-offerings/${off.id}`}>
                            <Button variant="ghost" size="sm" className="h-7 text-xs text-indigo-400">
                              Details
                            </Button>
                          </Link>
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

      {/* Tab 4: Faculty */}
      {activeTab === "faculty" && (
        <Card>
          <CardHeader>
            <CardTitle>Assigned Faculty Instructors</CardTitle>
            <CardDescription>
              Academic staff allocated to deliver lectures, lab sessions, and tutorials for this course.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {assignedFaculty.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400">
                No faculty members are currently assigned to this course.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left text-slate-300">
                  <thead className="bg-slate-950/60 text-[11px] font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="px-5 py-3">Faculty Member</th>
                      <th className="px-4 py-3">Instructional Role</th>
                      <th className="px-4 py-3">Offering Section</th>
                      <th className="px-4 py-3">Weekly Assigned Hours</th>
                      <th className="px-4 py-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {assignedFaculty.map((fac, idx) => (
                      <tr key={`${fac.id}-${idx}`} className="hover:bg-slate-800/40 transition-colors">
                        <td className="px-5 py-3.5 font-medium text-white">
                          <div className="font-semibold">{fac.facultyName}</div>
                          <div className="text-[11px] text-slate-400 font-mono">{fac.employeeCode} • {fac.email}</div>
                        </td>
                        <td className="px-4 py-3.5 text-slate-200">
                          <span className="font-mono text-xs text-indigo-300">
                            {fac.role.replace("_", " ")}
                          </span>
                        </td>
                        <td className="px-4 py-3.5 font-mono text-slate-300">
                          {fac.offeringSection} ({fac.offeringAcademicYear})
                        </td>
                        <td className="px-4 py-3.5 font-mono font-medium text-white">
                          {fac.assignedWeeklyHours} hrs/week
                        </td>
                        <td className="px-4 py-3.5">
                          <Badge variant={fac.status === "CONFIRMED" ? "success" : "warning"} dot>
                            {fac.status}
                          </Badge>
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

      {/* Tab 5: Academic Lifecycle History */}
      {activeTab === "history" && (
        <Card>
          <CardHeader>
            <CardTitle>Academic History & Revision Audit Trail</CardTitle>
            <CardDescription>
              Governance milestones, credit revisions, and syllabus changes for {subject.code}.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="relative border-l border-slate-800 ml-3 pl-6 space-y-6">
              <div className="relative">
                <span className="absolute -left-[31px] top-1 h-3 w-3 rounded-full bg-emerald-500 border-2 border-slate-900" />
                <div className="text-xs font-semibold text-white">Syllabus Active for Academic Year 2026–2027</div>
                <div className="text-[11px] text-slate-400 mt-0.5">August 1, 2026 • Board of Studies approval</div>
                <p className="text-xs text-slate-300 mt-1">
                  Aligned with autonomous R-2024 / R-2026 guidelines. Prescribed contact hours set to {subject.lectureHours}-{subject.tutorialHours}-{subject.practicalHours}.
                </p>
              </div>

              <div className="relative">
                <span className="absolute -left-[31px] top-1 h-3 w-3 rounded-full bg-indigo-500 border-2 border-slate-900" />
                <div className="text-xs font-semibold text-white">Credit Structure Harmonization</div>
                <div className="text-[11px] text-slate-400 mt-0.5">May 15, 2026 • Academic Council Committee</div>
                <p className="text-xs text-slate-300 mt-1">
                  Credits ratified at {subject.credits} Cr with integrated laboratory module.
                </p>
              </div>

              <div className="relative">
                <span className="absolute -left-[31px] top-1 h-3 w-3 rounded-full bg-slate-600 border-2 border-slate-900" />
                <div className="text-xs font-semibold text-white">Initial Course Cataloguing</div>
                <div className="text-[11px] text-slate-400 mt-0.5">January 10, 2026 • Department of {subject.departmentName}</div>
                <p className="text-xs text-slate-300 mt-1">
                  Draft course specification created by department curriculum committee.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
