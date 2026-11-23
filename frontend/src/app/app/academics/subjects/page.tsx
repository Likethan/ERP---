"use client";

import React, { useEffect, useState, useMemo, useCallback } from "react";
import Link from "next/link";
import { academicsService } from "@/services/academics.service";
import {
  AcademicSubject,
  SubjectType,
  SubjectCategory,
  SubjectStatus,
} from "@/types/academics";
import { DepartmentItem } from "@/mocks/academics.mock";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatCard } from "@/components/ui/stat-card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { useAuth } from "@/lib/auth-context";
import { DataGrid, ColumnDef, BulkAction } from "@/components/data-grid";
import {
  BookOpen,
  Plus,
  Eye,
  Layers,
  Clock,
  Sparkles,
  CheckCircle2,
  FileSpreadsheet,
  AlertCircle,
} from "lucide-react";

const SUBJECT_TYPES: SubjectType[] = [
  "THEORY",
  "PRACTICAL",
  "LAB",
  "PROJECT",
  "INTERNSHIP",
  "SEMINAR",
  "ELECTIVE",
  "OTHER",
];

const SUBJECT_CATEGORIES: { value: SubjectCategory; label: string }[] = [
  { value: "CORE", label: "Program Core (PC)" },
  { value: "PROFESSIONAL_ELECTIVE", label: "Professional Elective (PE)" },
  { value: "OPEN_ELECTIVE", label: "Open Elective (OE)" },
  { value: "BASIC_SCIENCES", label: "Basic Sciences (BS)" },
  { value: "HUMANITIES", label: "Humanities & Social Sciences (HSMC)" },
  { value: "ENGINEERING_SCIENCES", label: "Engineering Sciences (ESC)" },
  { value: "MANDATORY_NON_CREDIT", label: "Mandatory Non-Credit (MC)" },
];

export default function SubjectsMasterCatalogPage() {
  const { showToast } = useToast();
  const { hasPermission } = useAuth();
  const [subjects, setSubjects] = useState<AcademicSubject[]>([]);
  const [departments, setDepartments] = useState<DepartmentItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters state
  const [search, setSearch] = useState("");
  const [selectedDept, setSelectedDept] = useState("ALL");
  const [selectedType, setSelectedType] = useState("ALL");
  const [selectedStatus, setSelectedStatus] = useState("ALL");
  const [selectedCredits, setSelectedCredits] = useState("ALL");
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [selectedKeys, setSelectedKeys] = useState<Set<string>>(new Set());

  // Create Subject Modal State
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  // Form Fields
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [shortName, setShortName] = useState("");
  const [deptId, setDeptId] = useState("dept-cse");
  const [credits, setCredits] = useState<number>(3);
  const [lectureHours, setLectureHours] = useState<number>(3);
  const [tutorialHours, setTutorialHours] = useState<number>(0);
  const [practicalHours, setPracticalHours] = useState<number>(0);
  const [type, setType] = useState<SubjectType>("THEORY");
  const [category, setCategory] = useState<SubjectCategory>("CORE");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<SubjectStatus>("ACTIVE");

  const canManage = hasPermission("academics:subjects:manage");

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [subRes, deptRes] = await Promise.all([
        academicsService.getAcademicSubjects(),
        academicsService.getDepartments(),
      ]);
      setSubjects(subRes.data);
      setDepartments(deptRes.data);
    } catch (err) {
      console.error("Failed to load subjects:", err);
      showToast({ title: "Failed to load subjects", type: "error" });
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Client-side filtering & search
  const filteredSubjects = useMemo(() => {
    return subjects.filter((s) => {
      if (
        selectedDept !== "ALL" &&
        s.departmentId !== selectedDept &&
        !s.departmentName.toLowerCase().includes(selectedDept.toLowerCase())
      ) {
        return false;
      }
      if (selectedType !== "ALL" && s.type !== selectedType) {
        return false;
      }
      if (selectedStatus !== "ALL" && s.status !== selectedStatus) {
        return false;
      }
      if (selectedCredits !== "ALL" && s.credits !== Number(selectedCredits)) {
        return false;
      }
      if (search) {
        const q = search.toLowerCase();
        return (
          s.code.toLowerCase().includes(q) ||
          s.name.toLowerCase().includes(q) ||
          s.shortName.toLowerCase().includes(q) ||
          s.departmentName.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [
    subjects,
    selectedDept,
    selectedType,
    selectedStatus,
    selectedCredits,
    search,
  ]);

  const paginatedSubjects = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredSubjects.slice(start, start + pageSize);
  }, [filteredSubjects, currentPage, pageSize]);

  // Form Validation
  const validateForm = () => {
    const errors: Record<string, string> = {};
    if (!code.trim()) errors.code = "Subject code is required (e.g. CS301)";
    if (!name.trim()) errors.name = "Subject name is required";
    if (credits < 0 || credits > 30)
      errors.credits = "Credits must be between 0 and 30";
    if (lectureHours < 0)
      errors.lectureHours = "Lecture hours cannot be negative";
    if (tutorialHours < 0)
      errors.tutorialHours = "Tutorial hours cannot be negative";
    if (practicalHours < 0)
      errors.practicalHours = "Practical hours cannot be negative";
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleCreateSubject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    try {
      setIsSubmitting(true);
      const selectedDeptObj = departments.find((d) => d.id === deptId);
      const deptName = selectedDeptObj
        ? selectedDeptObj.name
        : "Computer Science & Engineering";

      const res = await academicsService.createAcademicSubject({
        code: code.trim().toUpperCase(),
        name: name.trim(),
        shortName: shortName.trim() || code.trim().toUpperCase(),
        departmentId: deptId,
        departmentName: deptName,
        credits: Number(credits),
        lectureHours: Number(lectureHours),
        tutorialHours: Number(tutorialHours),
        practicalHours: Number(practicalHours),
        type,
        category,
        description: description.trim(),
        status,
      });

      if (res.success) {
        showToast({
          title: "Subject Catalogued",
          message: `Successfully created subject ${res.data.code} - ${res.data.name}`,
          type: "success",
        });
        setCreateModalOpen(false);
        // Reset form
        setCode("");
        setName("");
        setShortName("");
        setDescription("");
        setFormErrors({});
        loadData();
      }
    } catch (err: any) {
      showToast({
        title: "Failed to create subject",
        message: err.message,
        type: "error",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Bulk Actions
  const bulkActions: BulkAction<AcademicSubject>[] = [
    {
      label: "Mark as Active",
      variant: "outline",
      icon: <CheckCircle2 className="h-4 w-4 text-emerald-400" />,
      onClick: async (items) => {
        for (const item of items) {
          await academicsService.updateAcademicSubject(item.id, {
            status: "ACTIVE",
          });
        }
        showToast({
          title: `Updated ${items.length} subjects to ACTIVE`,
          type: "success",
        });
        setSelectedKeys(new Set());
        loadData();
      },
    },
    {
      label: "Archive Selected",
      variant: "destructive",
      onClick: async (items) => {
        for (const item of items) {
          await academicsService.updateAcademicSubject(item.id, {
            status: "ARCHIVED",
          });
        }
        showToast({
          title: `Archived ${items.length} subjects`,
          type: "warning",
        });
        setSelectedKeys(new Set());
        loadData();
      },
    },
  ];

  // DataGrid Columns Definition
  const columns: ColumnDef<AcademicSubject>[] = useMemo(
    () => [
      {
        id: "code",
        header: "Subject Code",
        sortable: true,
        accessorKey: "code",
        cell: (item) => (
          <Link
            href={`/app/academics/subjects/${item.id}`}
            className="group block font-mono font-semibold text-white hover:text-indigo-400 transition-colors"
          >
            <div className="flex items-center gap-1.5">
              <span>{item.code}</span>
              <span className="opacity-0 group-hover:opacity-100 text-[10px] text-indigo-400 transition-opacity">
                ↗
              </span>
            </div>
            {item.shortName && item.shortName !== item.code && (
              <span className="text-[10px] font-normal text-slate-400">
                {item.shortName}
              </span>
            )}
          </Link>
        ),
      },
      {
        id: "name",
        header: "Subject Title & Category",
        sortable: true,
        accessorKey: "name",
        cell: (item) => (
          <div>
            <Link
              href={`/app/academics/subjects/${item.id}`}
              className="font-medium text-slate-200 hover:text-white transition-colors"
            >
              {item.name}
            </Link>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-[10px] text-slate-400 font-mono">
                {item.category.replace("_", " ")}
              </span>
              {item.prerequisites && item.prerequisites.length > 0 && (
                <span className="text-[10px] text-amber-400 font-mono">
                  Prereq: {item.prerequisites.join(", ")}
                </span>
              )}
            </div>
          </div>
        ),
      },
      {
        id: "department",
        header: "Department",
        sortable: true,
        accessorKey: "departmentName",
        cell: (item) => (
          <span className="text-xs text-slate-300">{item.departmentName}</span>
        ),
      },
      {
        id: "credits",
        header: "Credits",
        sortable: true,
        accessorKey: "credits",
        cell: (item) => (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
            {item.credits} Cr
          </span>
        ),
      },
      {
        id: "type",
        header: "Type",
        sortable: true,
        accessorKey: "type",
        cell: (item) => {
          const typeBadgeMap: Record<
            SubjectType,
            "info" | "warning" | "success" | "secondary"
          > = {
            THEORY: "info",
            PRACTICAL: "success",
            LAB: "success",
            PROJECT: "warning",
            INTERNSHIP: "secondary",
            SEMINAR: "secondary",
            ELECTIVE: "warning",
            OTHER: "secondary",
          };
          return (
            <Badge variant={typeBadgeMap[item.type] || "secondary"}>
              {item.type}
            </Badge>
          );
        },
      },
      {
        id: "hours",
        header: "Hours (L-T-P)",
        cell: (item) => (
          <span className="font-mono text-xs text-slate-300">
            {item.lectureHours} - {item.tutorialHours} - {item.practicalHours}
          </span>
        ),
      },
      {
        id: "status",
        header: "Status",
        sortable: true,
        accessorKey: "status",
        cell: (item) => {
          const statusMap: Record<
            string,
            "success" | "warning" | "destructive" | "secondary"
          > = {
            ACTIVE: "success",
            DRAFT: "warning",
            INACTIVE: "secondary",
            ARCHIVED: "destructive",
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
            <Link href={`/app/academics/subjects/${item.id}`}>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 text-xs"
                leftIcon={<Eye className="h-3 w-3" />}
              >
                Details
              </Button>
            </Link>
          </div>
        ),
      },
    ],
    [],
  );

  // Custom filters slot for DataGrid toolbar
  const customFilterSlot = (
    <div className="flex flex-wrap items-center gap-2">
      <select
        value={selectedDept}
        onChange={(e) => {
          setSelectedDept(e.target.value);
          setCurrentPage(1);
        }}
        className="h-8 rounded-lg border border-slate-700 bg-slate-900 px-2.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
      >
        <option value="ALL">All Departments</option>
        {departments.map((dept) => (
          <option key={dept.id} value={dept.id}>
            {dept.code} - {dept.name}
          </option>
        ))}
      </select>

      <select
        value={selectedType}
        onChange={(e) => {
          setSelectedType(e.target.value);
          setCurrentPage(1);
        }}
        className="h-8 rounded-lg border border-slate-700 bg-slate-900 px-2.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
      >
        <option value="ALL">All Subject Types</option>
        {SUBJECT_TYPES.map((t) => (
          <option key={t} value={t}>
            {t}
          </option>
        ))}
      </select>

      <select
        value={selectedCredits}
        onChange={(e) => {
          setSelectedCredits(e.target.value);
          setCurrentPage(1);
        }}
        className="h-8 rounded-lg border border-slate-700 bg-slate-900 px-2.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
      >
        <option value="ALL">All Credits</option>
        {[1, 2, 3, 4, 6, 8, 12].map((cr) => (
          <option key={cr} value={cr}>
            {cr} Credits
          </option>
        ))}
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
        <option value="DRAFT">Draft</option>
        <option value="INACTIVE">Inactive</option>
        <option value="ARCHIVED">Archived</option>
      </select>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
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
            <span className="text-white">Subjects Catalog</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Subjects & Courses Catalog
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Regulated CBCS course repository, credit definitions, and weekly
            lecture-tutorial-practical (L-T-P) allocations.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="primary"
            size="sm"
            leftIcon={<Plus className="h-4 w-4" />}
            onClick={() => setCreateModalOpen(true)}
          >
            New Subject
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Catalogued"
          value={subjects.length}
          description="Across all engineering & sciences"
          variant="indigo"
          icon={<BookOpen className="h-4 w-4" />}
        />
        <StatCard
          label="Active Subjects"
          value={subjects.filter((s) => s.status === "ACTIVE").length}
          description="Eligible for course offerings"
          variant="emerald"
          icon={<CheckCircle2 className="h-4 w-4" />}
        />
        <StatCard
          label="Electives & Seminars"
          value={
            subjects.filter(
              (s) =>
                s.type === "ELECTIVE" ||
                s.category === "PROFESSIONAL_ELECTIVE" ||
                s.category === "OPEN_ELECTIVE",
            ).length
          }
          description="CBCS specialized tracks"
          variant="sky"
          icon={<Layers className="h-4 w-4" />}
        />
        <StatCard
          label="Practical & Lab Courses"
          value={
            subjects.filter((s) => s.type === "LAB" || s.type === "PRACTICAL")
              .length
          }
          description="Hands-on computing & hardware"
          variant="amber"
          icon={<Clock className="h-4 w-4" />}
        />
      </div>

      {/* Enterprise DataGrid */}
      <DataGrid<AcademicSubject>
        data={paginatedSubjects}
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
        totalRecords={filteredSubjects.length}
        onPageChange={setCurrentPage}
        onPageSizeChange={(sz) => {
          setPageSize(sz);
          setCurrentPage(1);
        }}
        onSearchChange={(q) => {
          setSearch(q);
          setCurrentPage(1);
        }}
        searchPlaceholder="Search subject by code, name, or department..."
        customFilterSlot={customFilterSlot}
        exportFileName="campusos-subjects-catalog"
        emptyTitle="No Subjects Found"
        emptyDescription="No subjects matched your filter criteria. Broaden your search or reset filters."
        emptyActionLabel="Reset Filters"
        onEmptyAction={() => {
          setSearch("");
          setSelectedDept("ALL");
          setSelectedType("ALL");
          setSelectedStatus("ALL");
          setSelectedCredits("ALL");
        }}
      />

      {/* New Subject Creation Dialog */}
      <Dialog
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Catalogue New Academic Subject"
      >
        <form onSubmit={handleCreateSubject} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Subject Code <span className="text-red-400">*</span>
              </label>
              <Input
                placeholder="e.g. CS301"
                value={code}
                onChange={(e) => setCode(e.target.value.toUpperCase())}
                className={formErrors.code ? "border-red-500" : ""}
              />
              {formErrors.code && (
                <span className="text-[11px] text-red-400">
                  {formErrors.code}
                </span>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Short Name / Acronym
              </label>
              <Input
                placeholder="e.g. DBMS"
                value={shortName}
                onChange={(e) => setShortName(e.target.value.toUpperCase())}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Full Subject Name <span className="text-red-400">*</span>
            </label>
            <Input
              placeholder="e.g. Database Management Systems"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className={formErrors.name ? "border-red-500" : ""}
            />
            {formErrors.name && (
              <span className="text-[11px] text-red-400">
                {formErrors.name}
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Owning Department
              </label>
              <select
                value={deptId}
                onChange={(e) => setDeptId(e.target.value)}
                className="w-full h-9 rounded-lg border border-slate-700 bg-slate-900 px-3 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
              >
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name} ({d.code})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Subject Type
              </label>
              <select
                value={type}
                onChange={(e) => setType(e.target.value as SubjectType)}
                className="w-full h-9 rounded-lg border border-slate-700 bg-slate-900 px-3 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
              >
                {SUBJECT_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Academic Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value as SubjectCategory)}
              className="w-full h-9 rounded-lg border border-slate-700 bg-slate-900 px-3 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
            >
              {SUBJECT_CATEGORIES.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
          </div>

          {/* L-T-P-C Breakdown */}
          <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3">
            <h4 className="text-xs font-semibold text-slate-300 mb-2">
              Credit & Contact Hours Structure (L-T-P-C)
            </h4>
            <div className="grid grid-cols-4 gap-2">
              <div>
                <label className="block text-[10px] text-slate-400 mb-1">
                  Lecture (L)
                </label>
                <Input
                  type="number"
                  min="0"
                  max="10"
                  value={lectureHours}
                  onChange={(e) => setLectureHours(Number(e.target.value))}
                />
              </div>
              <div>
                <label className="block text-[10px] text-slate-400 mb-1">
                  Tutorial (T)
                </label>
                <Input
                  type="number"
                  min="0"
                  max="10"
                  value={tutorialHours}
                  onChange={(e) => setTutorialHours(Number(e.target.value))}
                />
              </div>
              <div>
                <label className="block text-[10px] text-slate-400 mb-1">
                  Practical (P)
                </label>
                <Input
                  type="number"
                  min="0"
                  max="10"
                  value={practicalHours}
                  onChange={(e) => setPracticalHours(Number(e.target.value))}
                />
              </div>
              <div>
                <label className="block text-[10px] text-slate-400 mb-1">
                  Credits (C)
                </label>
                <Input
                  type="number"
                  min="0"
                  max="30"
                  value={credits}
                  onChange={(e) => setCredits(Number(e.target.value))}
                  className={formErrors.credits ? "border-red-500" : ""}
                />
              </div>
            </div>
            {formErrors.credits && (
              <span className="text-[11px] text-red-400 mt-1 block">
                {formErrors.credits}
              </span>
            )}
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Description / Course Objectives
            </label>
            <textarea
              rows={3}
              placeholder="Brief course objectives and syllabus modules..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-900 p-2.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setCreateModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={isSubmitting}
            >
              Catalogue Subject
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
