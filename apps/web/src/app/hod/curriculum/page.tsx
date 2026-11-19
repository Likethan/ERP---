"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { hodService, HodCurriculumData, HodSubjectItem } from "@/services/hod.service";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { EmptyState } from "@/components/ui/empty-state";
import {
  BookOpen,
  Search,
  Filter,
  CheckCircle2,
  Layers,
  Award,
  GraduationCap,
  Sparkles,
  FileText,
  AlertTriangle,
  UserCheck,
  ChevronRight,
  Download,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function HodCurriculumPage() {
  const { activePersona } = useAuth();
  const deptName = activePersona.department || "Computer Science & Engineering";

  const [data, setData] = useState<HodCurriculumData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"subjects" | "scheme" | "copo">("subjects");
  const [search, setSearch] = useState("");
  const [selectedSemester, setSelectedSemester] = useState<number | "ALL">("ALL");

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const res = await hodService.getCurriculum(
          selectedSemester === "ALL" ? undefined : selectedSemester
        );
        if (res.success && res.data) {
          setData(res.data);
        }
      } catch (err) {
        console.error("Failed to load curriculum data", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [selectedSemester]);

  const filteredSubjects = (data?.subjects || []).filter((s) => {
    const q = search.toLowerCase();
    return (
      s.code.toLowerCase().includes(q) ||
      s.name.toLowerCase().includes(q) ||
      s.assignedFaculty.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-yellow-800 bg-yellow-100 px-2 py-0.5 rounded-full border border-yellow-300">
              Academic Management
            </span>
            <span className="text-[11px] font-mono text-slate-500">Regulation R-2026</span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
            <BookOpen className="h-6 w-6 text-yellow-600" />
            Subjects & Curriculum Management
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Department-wide academic curriculum, subject-faculty mapping, CO-PO correlation matrix, and syllabus completion monitoring.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            className="text-xs bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
            onClick={() => alert("Downloading NBA Course Articulation Matrix (PDF)...")}
          >
            <Download className="h-3.5 w-3.5 mr-1.5" />
            Export Articulation Matrix
          </Button>
        </div>
      </div>

      {/* KPI Overview Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-slate-200 bg-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Total Subjects
              </span>
              <BookOpen className="h-4 w-4 text-blue-600" />
            </div>
            <div className="text-2xl font-black text-slate-900 mt-2">
              {data?.allocationSummary.totalSubjects || 8}
            </div>
            <div className="text-[11px] text-slate-500 mt-1 font-medium">
              Autonomous Core & Electives
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Faculty Allocation
              </span>
              <UserCheck className="h-4 w-4 text-emerald-600" />
            </div>
            <div className="text-2xl font-black text-emerald-700 mt-2">
              {data?.allocationSummary.allocatedSubjects || 8} / {data?.allocationSummary.totalSubjects || 8}
            </div>
            <div className="text-[11px] text-emerald-600 font-bold mt-1 flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3" />
              100% Fully Allocated
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Unallocated / Conflicts
              </span>
              <AlertTriangle className="h-4 w-4 text-amber-500" />
            </div>
            <div className="text-2xl font-black text-slate-900 mt-2">
              {data?.allocationSummary.unallocatedSubjects || 0}
            </div>
            <div className="text-[11px] text-emerald-600 font-semibold mt-1">
              Zero allocation clashes detected
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Avg Syllabus Completion
              </span>
              <Sparkles className="h-4 w-4 text-yellow-600" />
            </div>
            <div className="text-2xl font-black text-slate-900 mt-2">
              {data?.curriculumScheme.averageSyllabusCompletion || 82.8}%
            </div>
            <div className="text-[11px] text-yellow-800 font-medium mt-1">
              On track for Nov/Dec ESE Exams
            </div>
          </CardContent>
        </Card>
      </div>

      {/* View Tabs */}
      <div className="flex border-b border-slate-200">
        <button
          onClick={() => setActiveTab("subjects")}
          className={cn(
            "px-4 py-2.5 text-xs font-bold transition-all border-b-2 flex items-center gap-2",
            activeTab === "subjects"
              ? "border-yellow-500 text-yellow-900 bg-yellow-50/50"
              : "border-transparent text-slate-600 hover:text-slate-900"
          )}
        >
          <BookOpen className="h-3.5 w-3.5" />
          Subject Directory & Allocation ({filteredSubjects.length})
        </button>

        <button
          onClick={() => setActiveTab("scheme")}
          className={cn(
            "px-4 py-2.5 text-xs font-bold transition-all border-b-2 flex items-center gap-2",
            activeTab === "scheme"
              ? "border-yellow-500 text-yellow-900 bg-yellow-50/50"
              : "border-transparent text-slate-600 hover:text-slate-900"
          )}
        >
          <Layers className="h-3.5 w-3.5" />
          Curriculum Scheme (R-2026)
        </button>

        <button
          onClick={() => setActiveTab("copo")}
          className={cn(
            "px-4 py-2.5 text-xs font-bold transition-all border-b-2 flex items-center gap-2",
            activeTab === "copo"
              ? "border-yellow-500 text-yellow-900 bg-yellow-50/50"
              : "border-transparent text-slate-600 hover:text-slate-900"
          )}
        >
          <Award className="h-3.5 w-3.5" />
          Course Outcomes & CO-PO Articulation Matrix
        </button>
      </div>

      {/* Tab 1: Subject Directory & Allocation */}
      {activeTab === "subjects" && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-white p-3 rounded-lg border border-slate-200">
            <div className="relative w-full sm:w-80">
              <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
              <Input
                placeholder="Search subject code, name, faculty..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 text-xs h-9"
              />
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto">
              <span className="text-xs font-bold text-slate-500">Semester:</span>
              <div className="flex gap-1">
                {(["ALL", 3, 5, 7] as const).map((sem) => (
                  <button
                    key={sem}
                    onClick={() => setSelectedSemester(sem)}
                    className={cn(
                      "px-2.5 py-1 text-xs rounded-md font-bold transition-colors",
                      selectedSemester === sem
                        ? "bg-yellow-400 text-slate-950 shadow-xs"
                        : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                    )}
                  >
                    {sem === "ALL" ? "All Semesters" : `Sem ${sem}`}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <Card className="border-slate-200 shadow-xs bg-white">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50/75 text-[10px] font-bold uppercase tracking-wider text-slate-600">
                    <th className="py-3 px-4">Subject Code & Name</th>
                    <th className="py-3 px-4">Sem / Type</th>
                    <th className="py-3 px-4">Credits</th>
                    <th className="py-3 px-4">Assigned Faculty</th>
                    <th className="py-3 px-4">Sections</th>
                    <th className="py-3 px-4">Syllabus Progress</th>
                    <th className="py-3 px-4 text-center">CO / PO</th>
                    <th className="py-3 px-4 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs">
                  {filteredSubjects.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="py-12 text-center text-slate-400">
                        <EmptyState
                          title="No subjects found"
                          description="Try modifying search keywords or semester filters."
                        />
                      </td>
                    </tr>
                  ) : (
                    filteredSubjects.map((subject) => (
                      <tr key={subject.id} className="hover:bg-yellow-50/30 transition-colors">
                        <td className="py-3 px-4">
                          <div className="font-bold text-slate-900">{subject.name}</div>
                          <div className="flex items-center gap-1.5 mt-0.5">
                            <span className="font-mono text-[11px] font-bold text-yellow-800 bg-yellow-100 px-1.5 py-0.2 rounded">
                              {subject.code}
                            </span>
                            <span className="text-[10px] text-slate-400 font-mono">
                              {subject.regulation}
                            </span>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-semibold text-slate-700">Sem {subject.semester}</div>
                          <span
                            className={cn(
                              "text-[10px] font-semibold px-1.5 py-0.2 rounded",
                              subject.type.includes("LAB")
                                ? "bg-purple-100 text-purple-800"
                                : "bg-blue-100 text-blue-800"
                            )}
                          >
                            {subject.type}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="font-mono font-bold text-slate-800">
                            {subject.credits} Credits
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-semibold text-slate-900 flex items-center gap-1.5">
                            <UserCheck className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
                            {subject.assignedFaculty}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex gap-1">
                            {subject.sections.map((sec) => (
                              <span
                                key={sec}
                                className="px-1.5 py-0.5 bg-slate-100 text-slate-700 font-bold rounded text-[10px]"
                              >
                                Sec {sec}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="py-3 px-4 w-44">
                          <div className="flex items-center justify-between text-[11px] mb-1">
                            <span className="font-bold text-slate-700">
                              {subject.syllabusCompletion}%
                            </span>
                            <span className="text-[10px] text-slate-500">
                              {subject.syllabusCompletion >= 80 ? "On Track" : "In Progress"}
                            </span>
                          </div>
                          <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                            <div
                              className={cn(
                                "h-1.5 rounded-full transition-all",
                                subject.syllabusCompletion >= 80 ? "bg-emerald-500" : "bg-yellow-500"
                              )}
                              style={{ width: `${subject.syllabusCompletion}%` }}
                            />
                          </div>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <Badge variant="outline" className="text-[10px] bg-slate-50 font-mono">
                            {subject.coCount} COs / {subject.poMapped} POs
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200 text-[10px] font-semibold">
                            ALLOCATED
                          </Badge>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* Tab 2: Curriculum Scheme */}
      {activeTab === "scheme" && (
        <div className="space-y-4">
          <Card className="border-slate-200 bg-white">
            <CardHeader className="pb-3 border-b border-slate-100">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base font-bold text-slate-900">
                    B.Tech Computer Science & Engineering — Autonomous Scheme R-2026
                  </CardTitle>
                  <CardDescription className="text-xs text-slate-500">
                    Statutory curriculum framework adhering to AICTE and NBA outcome-based criteria.
                  </CardDescription>
                </div>
                <Badge className="bg-yellow-100 text-yellow-900 border-yellow-300">
                  Approved by Academic Council
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="pt-4 space-y-4 text-xs">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-50 p-4 rounded-lg border border-slate-200">
                <div>
                  <div className="font-bold text-slate-500 uppercase tracking-wider text-[10px]">
                    Degree & Program
                  </div>
                  <div className="font-bold text-slate-900 text-sm mt-0.5">
                    Bachelor of Technology (B.Tech)
                  </div>
                  <div className="text-slate-600 text-[11px]">Computer Science & Engineering</div>
                </div>

                <div>
                  <div className="font-bold text-slate-500 uppercase tracking-wider text-[10px]">
                    Total Graduation Credits
                  </div>
                  <div className="font-bold text-slate-900 text-sm mt-0.5">
                    164 Credits (8 Semesters)
                  </div>
                  <div className="text-slate-600 text-[11px]">
                    Theory: 98 | Lab: 36 | Elective: 18 | Project: 12
                  </div>
                </div>

                <div>
                  <div className="font-bold text-slate-500 uppercase tracking-wider text-[10px]">
                    Curriculum In-charge
                  </div>
                  <div className="font-bold text-slate-900 text-sm mt-0.5">
                    Dr. K. S. Anand (HOD)
                  </div>
                  <div className="text-slate-600 text-[11px]">Department of CSE, V.S.B.</div>
                </div>
              </div>

              {/* Semester breakdown summary */}
              <div className="border border-slate-200 rounded-lg overflow-hidden">
                <table className="w-full text-left">
                  <thead className="bg-slate-50 border-b border-slate-200 text-[10px] uppercase font-bold text-slate-600">
                    <tr>
                      <th className="py-2.5 px-4">Semester</th>
                      <th className="py-2.5 px-4">Theory Courses</th>
                      <th className="py-2.5 px-4">Practical / Lab Courses</th>
                      <th className="py-2.5 px-4">Electives</th>
                      <th className="py-2.5 px-4">Total Credits</th>
                      <th className="py-2.5 px-4 text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-xs">
                    {[
                      { sem: "Semester 1", th: 4, lab: 2, el: 0, cr: 21 },
                      { sem: "Semester 2", th: 4, lab: 2, el: 0, cr: 21 },
                      { sem: "Semester 3", th: 5, lab: 2, el: 0, cr: 23 },
                      { sem: "Semester 4", th: 5, lab: 2, el: 0, cr: 23 },
                      { sem: "Semester 5 (Active)", th: 4, lab: 2, el: 1, cr: 22 },
                      { sem: "Semester 6", th: 4, lab: 2, el: 1, cr: 22 },
                      { sem: "Semester 7 (Active)", th: 3, lab: 1, el: 2, cr: 18 },
                      { sem: "Semester 8", th: 0, lab: 0, el: 2, cr: 14 },
                    ].map((row) => (
                      <tr key={row.sem} className="hover:bg-yellow-50/30">
                        <td className="py-2.5 px-4 font-bold text-slate-900">{row.sem}</td>
                        <td className="py-2.5 px-4 text-slate-600">{row.th} Subjects</td>
                        <td className="py-2.5 px-4 text-slate-600">{row.lab} Labs</td>
                        <td className="py-2.5 px-4 text-slate-600">{row.el} Electives</td>
                        <td className="py-2.5 px-4 font-mono font-bold text-slate-900">
                          {row.cr} Credits
                        </td>
                        <td className="py-2.5 px-4 text-right">
                          <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                            CONFIRMED
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tab 3: CO-PO Matrix */}
      {activeTab === "copo" && (
        <div className="space-y-4">
          <Card className="border-slate-200 bg-white">
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base font-bold text-slate-900">
                Sample Course Outcomes (CS301 Advanced Data Structures)
              </CardTitle>
              <CardDescription className="text-xs text-slate-500">
                Mapped against Revised Bloom's Taxonomy and institutional Graduate Attributes.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-4 space-y-3">
              {(data?.courseOutcomesSample || []).map((co) => (
                <div
                  key={co.coCode}
                  className="flex items-start gap-3 p-3 rounded-lg border border-slate-200 bg-slate-50/50"
                >
                  <div className="h-7 w-12 rounded bg-yellow-400 font-bold text-slate-950 flex items-center justify-center text-xs shrink-0 shadow-xs border border-yellow-500">
                    {co.coCode}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-semibold text-slate-900">{co.description}</p>
                    <div className="text-[11px] font-mono text-slate-500 mt-1">
                      Bloom Level: <span className="font-bold text-blue-700">{co.bloomLevel}</span>
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Articulation Matrix Table */}
          <Card className="border-slate-200 bg-white">
            <CardHeader className="pb-3 border-b border-slate-100">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base font-bold text-slate-900">
                    CO-PO Correlation Matrix (CS301)
                  </CardTitle>
                  <CardDescription className="text-xs text-slate-500">
                    Correlation levels: 3 - Substantial (High), 2 - Moderate (Medium), 1 - Slight (Low), - (No Correlation).
                  </CardDescription>
                </div>
                <Badge className="bg-blue-50 text-blue-800 border-blue-200 text-xs">
                  NBA Tier-1 Criteria 3
                </Badge>
              </div>
            </CardHeader>
            <div className="overflow-x-auto p-4">
              <table className="w-full text-center border-collapse">
                <thead>
                  <tr className="bg-slate-100 border border-slate-300 text-[10px] font-black text-slate-700">
                    <th className="py-2 px-3 text-left">Course Outcome</th>
                    <th className="py-2 px-2">PO1</th>
                    <th className="py-2 px-2">PO2</th>
                    <th className="py-2 px-2">PO3</th>
                    <th className="py-2 px-2">PO4</th>
                    <th className="py-2 px-2">PO5</th>
                    <th className="py-2 px-2">PSO1</th>
                    <th className="py-2 px-2">PSO2</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 text-xs font-mono">
                  {(data?.coPoMatrix || []).map((row, idx) => (
                    <tr key={idx} className="hover:bg-yellow-50/50">
                      <td className="py-2.5 px-3 text-left font-bold text-slate-900 font-sans">
                        {row.co}
                      </td>
                      <td className="py-2 px-2 font-bold text-slate-800 bg-emerald-50/40">{row.PO1}</td>
                      <td className="py-2 px-2 font-bold text-slate-800 bg-emerald-50/40">{row.PO2}</td>
                      <td className="py-2 px-2 font-bold text-slate-800">{row.PO3}</td>
                      <td className="py-2 px-2 font-bold text-slate-800">{row.PO4}</td>
                      <td className="py-2 px-2 font-bold text-slate-800">{row.PO5}</td>
                      <td className="py-2 px-2 font-black text-blue-900 bg-blue-50/40">{row.PSO1}</td>
                      <td className="py-2 px-2 font-black text-blue-900 bg-blue-50/40">{row.PSO2}</td>
                    </tr>
                  ))}
                  <tr className="bg-slate-100 font-bold border-t-2 border-slate-300">
                    <td className="py-2 px-3 text-left font-sans text-slate-900">Average Correlation</td>
                    <td className="py-2 px-2 text-emerald-800">2.8</td>
                    <td className="py-2 px-2 text-emerald-800">2.6</td>
                    <td className="py-2 px-2 text-slate-800">2.2</td>
                    <td className="py-2 px-2 text-slate-800">2.0</td>
                    <td className="py-2 px-2 text-slate-800">1.6</td>
                    <td className="py-2 px-2 text-blue-800">2.6</td>
                    <td className="py-2 px-2 text-blue-800">2.2</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
