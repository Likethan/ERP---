"use client";

import React, { useEffect, useState, useMemo, useCallback } from "react";
import Link from "next/link";
import { academicsService } from "@/services/academics.service";
import { staffService } from "@/services/staff.service";
import {
  CourseOfferingDetail,
  CourseOfferingStatus,
  FacultyAssignmentRole,
  AcademicSubject,
} from "@/types/academics";
import { DepartmentItem, ProgramItem } from "@/mocks/academics.mock";
import { StaffDetailView } from "@/types/domain";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatCard } from "@/components/ui/stat-card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { useAuth } from "@/lib/auth-context";
import { DataGrid, ColumnDef, BulkAction } from "@/components/data-grid";
import {
  CheckSquare,
  Plus,
  Eye,
  CheckCircle2,
  Calendar,
  Users,
  UserCheck,
  AlertCircle,
  GraduationCap,
  ArrowRight,
  ArrowLeft,
  ChevronRight,
  Clock,
  Sparkles,
} from "lucide-react";

export default function CourseOfferingsDirectoryPage() {
  const { showToast } = useToast();
  const { hasPermission } = useAuth();

  const [offerings, setOfferings] = useState<CourseOfferingDetail[]>([]);
  const [subjects, setSubjects] = useState<AcademicSubject[]>([]);
  const [departments, setDepartments] = useState<DepartmentItem[]>([]);
  const [programs, setPrograms] = useState<ProgramItem[]>([]);
  const [facultyStaff, setFacultyStaff] = useState<StaffDetailView[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters state
  const [search, setSearch] = useState("");
  const [selectedYear, setSelectedYear] = useState("ALL");
  const [selectedSemester, setSelectedSemester] = useState("ALL");
  const [selectedDept, setSelectedDept] = useState("ALL");
  const [selectedSection, setSelectedSection] = useState("ALL");
  const [selectedStatus, setSelectedStatus] = useState("ALL");
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [selectedKeys, setSelectedKeys] = useState<Set<string>>(new Set());

  // 5-Step Guided Wizard State
  const [wizardOpen, setWizardOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [wizardErrors, setWizardErrors] = useState<Record<string, string>>({});

  // Wizard Form Fields
  // Step 1: Term
  const [academicYear, setAcademicYear] = useState("2026-2027");
  const [semester, setSemester] = useState<number>(5);

  // Step 2: Program, Section & Subject
  const [selectedProgramId, setSelectedProgramId] = useState("prog-btech-cse");
  const [selectedSectionVal, setSelectedSectionVal] = useState("A");
  const [selectedSubjectId, setSelectedSubjectId] = useState("");
  const [maxCapacity, setMaxCapacity] = useState<number>(60);

  // Step 3: Faculty Assignment
  const [selectedFacultyId, setSelectedFacultyId] = useState("");
  const [facultyRole, setFacultyRole] = useState<FacultyAssignmentRole>("PRIMARY_INSTRUCTOR");
  const [assignedHours, setAssignedHours] = useState<number>(4);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [offRes, subRes, deptRes, progRes, staffRes] = await Promise.all([
        academicsService.getCourseOfferingDetails(),
        academicsService.getAcademicSubjects(),
        academicsService.getDepartments(),
        academicsService.getPrograms(),
        staffService.list(),
      ]);
      setOfferings(offRes.data);
      setSubjects(subRes.data);
      setDepartments(deptRes.data);
      setPrograms(progRes.data);
      // Filter staff that are faculty
      const facs = staffRes.data.filter((s: StaffDetailView) => s.role.toLowerCase().includes("prof") || s.role.toLowerCase().includes("faculty"));
      setFacultyStaff(facs.length > 0 ? facs : staffRes.data);
      if (subRes.data.length > 0 && !selectedSubjectId) {
        setSelectedSubjectId(subRes.data[0].id);
      }
    } catch (err) {
      console.error("Failed to load course offerings data:", err);
      showToast({ title: "Failed to load course offerings", type: "error" });
    } finally {
      setLoading(false);
    }
  }, [showToast, selectedSubjectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Filtering
  const filteredOfferings = useMemo(() => {
    return offerings.filter((o) => {
      if (selectedYear !== "ALL" && o.academicYear !== selectedYear) {
        return false;
      }
      if (selectedSemester !== "ALL" && o.semester !== Number(selectedSemester)) {
        return false;
      }
      if (selectedDept !== "ALL" && !o.department.toLowerCase().includes(selectedDept.toLowerCase())) {
        return false;
      }
      if (selectedSection !== "ALL" && o.section !== selectedSection) {
        return false;
      }
      if (selectedStatus !== "ALL" && o.status !== selectedStatus) {
        return false;
      }
      if (search) {
        const q = search.toLowerCase();
        return (
          o.subjectCode.toLowerCase().includes(q) ||
          o.subjectName.toLowerCase().includes(q) ||
          o.programName.toLowerCase().includes(q) ||
          o.facultyAssignments.some((f) => f.facultyName.toLowerCase().includes(q))
        );
      }
      return true;
    });
  }, [offerings, selectedYear, selectedSemester, selectedDept, selectedSection, selectedStatus, search]);

  const paginatedOfferings = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredOfferings.slice(start, start + pageSize);
  }, [filteredOfferings, currentPage, pageSize]);

  // Wizard Validation
  const validateStep = (step: number) => {
    const errors: Record<string, string> = {};
    if (step === 1) {
      if (!academicYear.trim()) errors.academicYear = "Academic year is required";
      if (!semester || semester < 1 || semester > 10) errors.semester = "Valid semester is required";
    }
    if (step === 2) {
      if (!selectedSubjectId) errors.selectedSubjectId = "Please select a subject from catalog";
      if (!selectedSectionVal) errors.selectedSectionVal = "Section is required";
      if (maxCapacity < 1) errors.maxCapacity = "Capacity must be at least 1";
    }
    if (step === 3) {
      if (!selectedFacultyId) errors.selectedFacultyId = "Please select a faculty instructor";
      if (assignedHours < 1) errors.assignedHours = "Assigned hours must be positive";
    }
    setWizardErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleNextStep = () => {
    if (validateStep(currentStep)) {
      setCurrentStep((prev) => Math.min(prev + 1, 4));
    }
  };

  const handlePrevStep = () => {
    setCurrentStep((prev) => Math.max(prev - 1, 1));
  };

  // Submit Offering Creation (Step 4)
  const handleCreateOffering = async () => {
    const subjectObj = subjects.find((s) => s.id === selectedSubjectId);
    const progObj = programs.find((p) => p.id === selectedProgramId);
    const facultyObj = facultyStaff.find((f) => f.id === selectedFacultyId);

    if (!subjectObj || !progObj) return;

    try {
      setIsSubmitting(true);
      const assignments = facultyObj
        ? [
            {
              id: `fa-${Date.now()}`,
              facultyId: facultyObj.id,
              facultyName: `${facultyObj.firstName} ${facultyObj.lastName}`,
              employeeCode: facultyObj.employeeCode,
              email: facultyObj.email,
              role: facultyRole,
              assignedWeeklyHours: assignedHours,
              status: "CONFIRMED" as const,
            },
          ]
        : [];

      const res = await academicsService.createCourseOffering({
        subjectId: subjectObj.id,
        subjectCode: subjectObj.code,
        subjectName: subjectObj.name,
        programId: progObj.id,
        programName: progObj.name,
        department: progObj.department,
        academicYear,
        semester: Number(semester),
        section: selectedSectionVal,
        credits: subjectObj.credits,
        type: subjectObj.type,
        lectureHours: subjectObj.lectureHours,
        labHours: subjectObj.practicalHours,
        maxCapacity: Number(maxCapacity),
        status: "OPEN",
        facultyAssignments: assignments,
      });

      if (res.success) {
        showToast({
          title: "Course Offering Created",
          message: `Created offering for ${res.data.subjectCode} (Sec ${res.data.section})`,
          type: "success",
        });
        setWizardOpen(false);
        setCurrentStep(1);
        loadData();
      }
    } catch (err: any) {
      showToast({ title: "Failed to create offering", message: err.message, type: "error" });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Bulk Actions
  const bulkActions: BulkAction<CourseOfferingDetail>[] = [
    {
      label: "Activate Selected",
      variant: "outline",
      icon: <CheckCircle2 className="h-4 w-4 text-emerald-400" />,
      onClick: async (items) => {
        for (const item of items) {
          await academicsService.updateCourseOffering(item.id, { status: "ACTIVE" });
        }
        showToast({ title: `Activated ${items.length} course offerings`, type: "success" });
        setSelectedKeys(new Set());
        loadData();
      },
    },
  ];

  // DataGrid Columns
  const columns: ColumnDef<CourseOfferingDetail>[] = useMemo(
    () => [
      {
        id: "subject",
        header: "Subject & Code",
        sortable: true,
        accessorKey: "subjectCode",
        cell: (item) => (
          <Link
            href={`/app/academics/course-offerings/${item.id}`}
            className="group block font-semibold text-white hover:text-indigo-400 transition-colors"
          >
            <div className="flex items-center gap-1.5 font-mono">
              <span>{item.subjectCode}</span>
              <span className="opacity-0 group-hover:opacity-100 text-[10px] text-indigo-400 transition-opacity">↗</span>
            </div>
            <div className="text-xs font-normal text-slate-300 line-clamp-1">{item.subjectName}</div>
            <div className="text-[10px] text-slate-500 font-mono">{item.credits} Cr • {item.type}</div>
          </Link>
        ),
      },
      {
        id: "cohort",
        header: "Program & Term",
        sortable: true,
        accessorKey: "programName",
        cell: (item) => (
          <div className="text-xs">
            <div className="font-medium text-slate-200">{item.programName}</div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="rounded bg-slate-800 px-1.5 py-0.2 font-mono text-[11px] text-slate-300 border border-slate-700">
                Sem {item.semester} • Sec {item.section}
              </span>
              <span className="text-[11px] text-slate-500 font-mono">AY {item.academicYear}</span>
            </div>
          </div>
        ),
      },
      {
        id: "faculty",
        header: "Faculty Assignment",
        cell: (item) => {
          const primary = item.facultyAssignments.find((f) => f.role === "PRIMARY_INSTRUCTOR") || item.facultyAssignments[0];
          return (
            <div className="text-xs">
              {primary ? (
                <div>
                  <div className="font-medium text-slate-200">{primary.facultyName}</div>
                  <div className="text-[10px] text-indigo-400 font-mono">
                    {primary.role.replace("_", " ")} ({primary.assignedWeeklyHours} hrs)
                  </div>
                  {item.facultyAssignments.length > 1 && (
                    <div className="text-[10px] text-slate-500">
                      +{item.facultyAssignments.length - 1} co-instructor(s)
                    </div>
                  )}
                </div>
              ) : (
                <span className="text-amber-400 font-medium italic flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" /> Unassigned
                </span>
              )}
            </div>
          );
        },
      },
      {
        id: "enrollment",
        header: "Enrollment / Capacity",
        sortable: true,
        accessorFn: (item) => item.enrolledCount,
        cell: (item) => {
          const pct = Math.round((item.enrolledCount / item.maxCapacity) * 100);
          return (
            <div className="text-xs font-mono">
              <div className="flex items-center justify-between text-[11px] mb-1">
                <span className="text-slate-200 font-semibold">{item.enrolledCount} Students</span>
                <span className="text-slate-500">Cap: {item.maxCapacity}</span>
              </div>
              <div className="w-28 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                <div
                  className={`h-1.5 rounded-full ${
                    pct >= 100 ? "bg-red-500" : pct >= 80 ? "bg-amber-500" : "bg-indigo-500"
                  }`}
                  style={{ width: `${Math.min(100, pct)}%` }}
                />
              </div>
            </div>
          );
        },
      },
      {
        id: "status",
        header: "Status",
        sortable: true,
        accessorKey: "status",
        cell: (item) => {
          const statusMap: Record<CourseOfferingStatus, "success" | "warning" | "destructive" | "info" | "secondary"> = {
            ACTIVE: "success",
            OPEN: "info",
            PLANNED: "warning",
            COMPLETED: "secondary",
            CANCELLED: "destructive",
          };
          return (
            <Badge variant={statusMap[item.status] || "secondary"} dot>
              {item.status}
            </Badge>
          );
        },
      },
      {
        id: "actions",
        header: "Actions",
        align: "right",
        cell: (item) => (
          <div className="flex items-center justify-end gap-1.5">
            <Link href={`/app/academics/course-offerings/${item.id}`}>
              <Button size="sm" variant="ghost" className="h-7 text-xs" leftIcon={<Eye className="h-3 w-3" />}>
                Details
              </Button>
            </Link>
          </div>
        ),
      },
    ],
    []
  );

  // Custom filter slot
  const customFilterSlot = (
    <div className="flex flex-wrap items-center gap-2">
      <select
        value={selectedYear}
        onChange={(e) => {
          setSelectedYear(e.target.value);
          setCurrentPage(1);
        }}
        className="h-8 rounded-lg border border-slate-700 bg-slate-900 px-2.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
      >
        <option value="ALL">All Academic Years</option>
        <option value="2026-2027">AY 2026-2027</option>
        <option value="2025-2026">AY 2025-2026</option>
      </select>

      <select
        value={selectedSemester}
        onChange={(e) => {
          setSelectedSemester(e.target.value);
          setCurrentPage(1);
        }}
        className="h-8 rounded-lg border border-slate-700 bg-slate-900 px-2.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
      >
        <option value="ALL">All Semesters</option>
        {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
          <option key={s} value={s}>
            Semester {s}
          </option>
        ))}
      </select>

      <select
        value={selectedDept}
        onChange={(e) => {
          setSelectedDept(e.target.value);
          setCurrentPage(1);
        }}
        className="h-8 rounded-lg border border-slate-700 bg-slate-900 px-2.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
      >
        <option value="ALL">All Departments</option>
        {departments.map((d) => (
          <option key={d.id} value={d.name}>
            {d.code} - {d.name}
          </option>
        ))}
      </select>

      <select
        value={selectedSection}
        onChange={(e) => {
          setSelectedSection(e.target.value);
          setCurrentPage(1);
        }}
        className="h-8 rounded-lg border border-slate-700 bg-slate-900 px-2.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
      >
        <option value="ALL">All Sections</option>
        <option value="A">Section A</option>
        <option value="B">Section B</option>
        <option value="C">Section C</option>
      </select>

      <select
        value={selectedStatus}
        onChange={(e) => {
          setSelectedStatus(e.target.value);
          setCurrentPage(1);
        }}
        className="h-8 rounded-lg border border-slate-700 bg-slate-900 px-2.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
      >
        <option value="ALL">All Statuses</option>
        <option value="ACTIVE">Active</option>
        <option value="OPEN">Open</option>
        <option value="PLANNED">Planned</option>
        <option value="COMPLETED">Completed</option>
        <option value="CANCELLED">Cancelled</option>
      </select>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Link href="/app/academics" className="hover:text-white transition-colors">
              Academics
            </Link>
            <span>/</span>
            <span className="text-white">Course Offerings</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Classroom Course Offerings
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Subject + Term + Section staffing, faculty assignments, and cohort student registrations.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="primary"
            size="sm"
            leftIcon={<Plus className="h-4 w-4" />}
            onClick={() => {
              setCurrentStep(1);
              setWizardOpen(true);
            }}
          >
            Create Course Offering
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Active Offerings"
          value={offerings.length}
          description="Sections scheduled this term"
          variant="indigo"
          icon={<CheckSquare className="h-4 w-4" />}
        />
        <StatCard
          label="Assigned Faculty Leads"
          value={offerings.reduce((sum, o) => sum + o.facultyAssignments.length, 0)}
          description="Instructors & Lab in-charges"
          variant="emerald"
          icon={<GraduationCap className="h-4 w-4" />}
        />
        <StatCard
          label="Enrolled Students"
          value={offerings.reduce((sum, o) => sum + o.enrolledCount, 0)}
          description="Live registrations"
          variant="sky"
          icon={<Users className="h-4 w-4" />}
        />
        <StatCard
          label="Unassigned Offerings"
          value={offerings.filter((o) => o.facultyAssignments.length === 0).length}
          description="Require immediate staffing"
          variant="amber"
          icon={<AlertCircle className="h-4 w-4" />}
        />
      </div>

      {/* Enterprise DataGrid */}
      <DataGrid<CourseOfferingDetail>
        data={paginatedOfferings}
        columns={columns}
        keyExtractor={(item) => item.id}
        loading={loading}
        selectable
        selectedKeys={selectedKeys}
        onSelectionChange={setSelectedKeys}
        bulkActions={bulkActions}
        paginated
        pageSize={pageSize}
        currentPage={currentPage}
        totalRecords={filteredOfferings.length}
        onPageChange={setCurrentPage}
        onPageSizeChange={(sz) => {
          setPageSize(sz);
          setCurrentPage(1);
        }}
        onSearchChange={(q) => {
          setSearch(q);
          setCurrentPage(1);
        }}
        searchPlaceholder="Search offering by subject code, name, or faculty instructor..."
        customFilterSlot={customFilterSlot}
        exportFileName="campusos-course-offerings"
        emptyTitle="No Course Offerings Found"
        emptyDescription="No course offerings matched your filter settings."
        emptyActionLabel="Reset Filters"
        onEmptyAction={() => {
          setSearch("");
          setSelectedYear("ALL");
          setSelectedSemester("ALL");
          setSelectedDept("ALL");
          setSelectedSection("ALL");
          setSelectedStatus("ALL");
        }}
      />

      {/* Guided 5-Step Creation Wizard Dialog */}
      <Dialog
        open={wizardOpen}
        onClose={() => setWizardOpen(false)}
        title="Guided Course Offering Wizard"
      >
        <div className="space-y-6">
          {/* Stepper Header */}
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            {[
              { num: 1, label: "Academic Term" },
              { num: 2, label: "Subject & Section" },
              { num: 3, label: "Faculty Staffing" },
              { num: 4, label: "Review & Confirm" },
            ].map((st) => (
              <div
                key={st.num}
                className={`flex items-center gap-1.5 text-xs ${
                  currentStep === st.num
                    ? "font-semibold text-indigo-400"
                    : currentStep > st.num
                    ? "text-emerald-400"
                    : "text-slate-500"
                }`}
              >
                <div
                  className={`h-6 w-6 rounded-full flex items-center justify-center text-xs font-mono font-bold border ${
                    currentStep === st.num
                      ? "bg-indigo-600 border-indigo-500 text-white"
                      : currentStep > st.num
                      ? "bg-emerald-500/20 border-emerald-500 text-emerald-400"
                      : "bg-slate-800 border-slate-700 text-slate-400"
                  }`}
                >
                  {currentStep > st.num ? "✓" : st.num}
                </div>
                <span className="hidden sm:inline">{st.label}</span>
              </div>
            ))}
          </div>

          {/* Step 1: Academic Year & Semester */}
          {currentStep === 1 && (
            <div className="space-y-4">
              <h4 className="text-xs font-semibold text-white">Step 1: Select Academic Term</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Academic Year <span className="text-red-400">*</span>
                  </label>
                  <select
                    value={academicYear}
                    onChange={(e) => setAcademicYear(e.target.value)}
                    className="w-full h-9 rounded-lg border border-slate-700 bg-slate-900 px-3 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="2026-2027">2026-2027 (Active)</option>
                    <option value="2025-2026">2025-2026</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Semester <span className="text-red-400">*</span>
                  </label>
                  <Input
                    type="number"
                    min="1"
                    max="10"
                    value={semester}
                    onChange={(e) => setSemester(Number(e.target.value))}
                    className={wizardErrors.semester ? "border-red-500" : ""}
                  />
                  {wizardErrors.semester && (
                    <span className="text-[11px] text-red-400">{wizardErrors.semester}</span>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Program, Section & Subject */}
          {currentStep === 2 && (
            <div className="space-y-4">
              <h4 className="text-xs font-semibold text-white">Step 2: Choose Program, Section & Catalog Subject</h4>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Degree Program</label>
                <select
                  value={selectedProgramId}
                  onChange={(e) => setSelectedProgramId(e.target.value)}
                  className="w-full h-9 rounded-lg border border-slate-700 bg-slate-900 px-3 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
                >
                  {programs.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.code})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Catalog Subject <span className="text-red-400">*</span>
                </label>
                <select
                  value={selectedSubjectId}
                  onChange={(e) => setSelectedSubjectId(e.target.value)}
                  className="w-full h-9 rounded-lg border border-slate-700 bg-slate-900 px-3 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
                >
                  <option value="">-- Select Subject from Catalog --</option>
                  {subjects.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.code} - {s.name} ({s.credits} Cr • {s.departmentName})
                    </option>
                  ))}
                </select>
                {wizardErrors.selectedSubjectId && (
                  <span className="text-[11px] text-red-400">{wizardErrors.selectedSubjectId}</span>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Section</label>
                  <select
                    value={selectedSectionVal}
                    onChange={(e) => setSelectedSectionVal(e.target.value)}
                    className="w-full h-9 rounded-lg border border-slate-700 bg-slate-900 px-3 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="A">Section A</option>
                    <option value="B">Section B</option>
                    <option value="C">Section C</option>
                    <option value="D">Section D</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Max Student Capacity</label>
                  <Input
                    type="number"
                    min="10"
                    max="120"
                    value={maxCapacity}
                    onChange={(e) => setMaxCapacity(Number(e.target.value))}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Faculty Assignment */}
          {currentStep === 3 && (
            <div className="space-y-4">
              <h4 className="text-xs font-semibold text-white">Step 3: Assign Canonical Faculty Instructor</h4>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Faculty Instructor <span className="text-red-400">*</span>
                </label>
                <select
                  value={selectedFacultyId}
                  onChange={(e) => setSelectedFacultyId(e.target.value)}
                  className="w-full h-9 rounded-lg border border-slate-700 bg-slate-900 px-3 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
                >
                  <option value="">-- Select Faculty Member --</option>
                  {facultyStaff.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.firstName} {f.lastName} ({f.employeeCode}) • {f.department}
                    </option>
                  ))}
                </select>
                {wizardErrors.selectedFacultyId && (
                  <span className="text-[11px] text-red-400">{wizardErrors.selectedFacultyId}</span>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Instructional Role</label>
                  <select
                    value={facultyRole}
                    onChange={(e) => setFacultyRole(e.target.value as FacultyAssignmentRole)}
                    className="w-full h-9 rounded-lg border border-slate-700 bg-slate-900 px-3 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="PRIMARY_INSTRUCTOR">Primary Instructor</option>
                    <option value="CO_INSTRUCTOR">Co-Instructor</option>
                    <option value="LAB_INSTRUCTOR">Lab Instructor</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Assigned Weekly Hours</label>
                  <Input
                    type="number"
                    min="1"
                    max="12"
                    value={assignedHours}
                    onChange={(e) => setAssignedHours(Number(e.target.value))}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Review & Confirm */}
          {currentStep === 4 && (
            <div className="space-y-4">
              <h4 className="text-xs font-semibold text-white">Step 4: Review Course Offering Configuration</h4>
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-400">Subject:</span>
                  <span className="font-semibold text-white font-mono">
                    {subjects.find((s) => s.id === selectedSubjectId)?.code} - {subjects.find((s) => s.id === selectedSubjectId)?.name}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Term & Section:</span>
                  <span className="text-slate-200">
                    AY {academicYear} • Sem {semester} (Section {selectedSectionVal})
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Max Capacity:</span>
                  <span className="text-slate-200">{maxCapacity} Students</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Assigned Instructor:</span>
                  <span className="text-indigo-400 font-medium">
                    {facultyStaff.find((f) => f.id === selectedFacultyId)?.firstName} {facultyStaff.find((f) => f.id === selectedFacultyId)?.lastName} ({facultyRole.replace("_", " ")})
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Stepper Navigation Buttons */}
          <div className="flex items-center justify-between pt-3 border-t border-slate-800">
            {currentStep > 1 ? (
              <Button variant="outline" size="sm" onClick={handlePrevStep} leftIcon={<ArrowLeft className="h-3.5 w-3.5" />}>
                Previous
              </Button>
            ) : (
              <div />
            )}

            {currentStep < 4 ? (
              <Button variant="primary" size="sm" onClick={handleNextStep} rightIcon={<ArrowRight className="h-3.5 w-3.5" />}>
                Continue
              </Button>
            ) : (
              <Button
                variant="primary"
                size="sm"
                onClick={handleCreateOffering}
                isLoading={isSubmitting}
                leftIcon={<CheckSquare className="h-3.5 w-3.5" />}
              >
                Create Course Offering
              </Button>
            )}
          </div>
        </div>
      </Dialog>
    </div>
  );
}
