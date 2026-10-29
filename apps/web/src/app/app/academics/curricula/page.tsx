"use client";

import React, { useEffect, useState, useMemo, useCallback } from "react";
import Link from "next/link";
import { academicsService } from "@/services/academics.service";
import { CurriculumScheme, CurriculumStatus } from "@/types/academics";
import { DepartmentItem, ProgramItem } from "@/mocks/academics.mock";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatCard } from "@/components/ui/stat-card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { useAuth } from "@/lib/auth-context";
import { DataGrid, ColumnDef, BulkAction } from "@/components/data-grid";
import {
  FileSpreadsheet,
  Plus,
  Eye,
  CheckCircle2,
  Layers,
  Calendar,
  AlertCircle,
  GitBranch,
  ShieldCheck,
} from "lucide-react";

export default function CurriculaDirectoryPage() {
  const { showToast } = useToast();
  const { hasPermission } = useAuth();
  const [curricula, setCurricula] = useState<CurriculumScheme[]>([]);
  const [departments, setDepartments] = useState<DepartmentItem[]>([]);
  const [programs, setPrograms] = useState<ProgramItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Filter states
  const [search, setSearch] = useState("");
  const [selectedDept, setSelectedDept] = useState("ALL");
  const [selectedStatus, setSelectedStatus] = useState("ALL");
  const [selectedRegulation, setSelectedRegulation] = useState("ALL");
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [selectedKeys, setSelectedKeys] = useState<Set<string>>(new Set());

  // Creation Modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  // Form Fields
  const [programName, setProgramName] = useState(
    "B.Tech Computer Science & Engineering",
  );
  const [programCode, setProgramCode] = useState("B.Tech CSE");
  const [department, setDepartment] = useState(
    "Computer Science & Engineering",
  );
  const [regulation, setRegulation] = useState("R-2026");
  const [version, setVersion] = useState("v1.0");
  const [academicYear, setAcademicYear] = useState("2026-2027");
  const [effectiveDate, setEffectiveDate] = useState("July 2026");
  const [totalCredits, setTotalCredits] = useState<number>(160);
  const [totalSemesters, setTotalSemesters] = useState<number>(8);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [currRes, deptRes, progRes] = await Promise.all([
        academicsService.getCurriculumSchemes(),
        academicsService.getDepartments(),
        academicsService.getPrograms(),
      ]);
      setCurricula(currRes.data);
      setDepartments(deptRes.data);
      setPrograms(progRes.data);
    } catch (err) {
      console.error("Failed to load curricula:", err);
      showToast({ title: "Failed to load curricula", type: "error" });
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Regulations distinct list
  const regulationsList = useMemo(() => {
    return Array.from(new Set(curricula.map((c) => c.regulation)));
  }, [curricula]);

  // Filtering
  const filteredCurricula = useMemo(() => {
    return curricula.filter((c) => {
      if (
        selectedDept !== "ALL" &&
        !c.department.toLowerCase().includes(selectedDept.toLowerCase())
      ) {
        return false;
      }
      if (selectedStatus !== "ALL" && c.status !== selectedStatus) {
        return false;
      }
      if (selectedRegulation !== "ALL" && c.regulation !== selectedRegulation) {
        return false;
      }
      if (search) {
        const q = search.toLowerCase();
        return (
          c.programName.toLowerCase().includes(q) ||
          c.regulation.toLowerCase().includes(q) ||
          c.version.toLowerCase().includes(q) ||
          c.department.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [curricula, selectedDept, selectedStatus, selectedRegulation, search]);

  const paginatedCurricula = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredCurricula.slice(start, start + pageSize);
  }, [filteredCurricula, currentPage, pageSize]);

  // Validation
  const validateForm = () => {
    const errors: Record<string, string> = {};
    if (!programName.trim()) errors.programName = "Program name is required";
    if (!regulation.trim())
      errors.regulation = "Regulation is required (e.g. R-2026)";
    if (!version.trim()) errors.version = "Version is required (e.g. v1.0)";
    if (totalCredits < 1)
      errors.totalCredits = "Total credits must be positive";
    if (totalSemesters < 1 || totalSemesters > 12)
      errors.totalSemesters = "Semesters must be between 1 and 12";
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleCreateCurriculum = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    try {
      setIsSubmitting(true);
      // Generate empty semesters
      const sems = Array.from({ length: totalSemesters }, (_, i) => ({
        semesterNumber: i + 1,
        totalCredits: Math.round(totalCredits / totalSemesters),
        subjects: [],
      }));

      const res = await academicsService.createCurriculumScheme({
        programName,
        programCode,
        department,
        regulation,
        version,
        academicYear,
        effectiveDate,
        totalCredits: Number(totalCredits),
        totalSemesters: Number(totalSemesters),
        status: "DRAFT",
        semesters: sems,
      });

      if (res.success) {
        showToast({
          title: "Curriculum Scheme Created",
          message: `Created scheme for ${res.data.programName} (${res.data.regulation} ${res.data.version})`,
          type: "success",
        });
        setCreateModalOpen(false);
        setFormErrors({});
        loadData();
      }
    } catch (err: any) {
      showToast({
        title: "Failed to create curriculum",
        message: err.message,
        type: "error",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Bulk Actions
  const bulkActions: BulkAction<CurriculumScheme>[] = [
    {
      label: "Mark Approved",
      variant: "outline",
      icon: <CheckCircle2 className="h-4 w-4 text-emerald-400" />,
      onClick: async (items) => {
        for (const item of items) {
          await academicsService.updateCurriculumScheme(item.id, {
            status: "APPROVED",
          });
        }
        showToast({
          title: `Updated ${items.length} schemes to APPROVED`,
          type: "success",
        });
        setSelectedKeys(new Set());
        loadData();
      },
    },
  ];

  // DataGrid Columns
  const columns: ColumnDef<CurriculumScheme>[] = useMemo(
    () => [
      {
        id: "program",
        header: "Program & Regulation Scheme",
        sortable: true,
        accessorKey: "programName",
        cell: (item) => (
          <div className="space-y-1">
            <Link
              href={`/app/academics/curricula/${item.id}`}
              className="font-semibold text-white hover:text-indigo-400 transition-colors flex items-center gap-2"
            >
              <span>{item.programName}</span>
              {item.isActiveVersion && (
                <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  Active Cohort
                </span>
              )}
            </Link>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span className="font-mono text-slate-300 font-medium">
                {item.regulation}
              </span>
              <span>•</span>
              <span className="font-mono text-slate-400">{item.version}</span>
              <span>•</span>
              <span>Effective: {item.effectiveDate}</span>
            </div>
          </div>
        ),
      },
      {
        id: "department",
        header: "Department",
        sortable: true,
        accessorKey: "department",
        cell: (item) => (
          <span className="text-xs text-slate-300">{item.department}</span>
        ),
      },
      {
        id: "semesters",
        header: "Structure",
        cell: (item) => (
          <div className="text-xs font-mono text-slate-300">
            <div>{item.totalSemesters} Semesters</div>
            <div className="text-[11px] text-slate-500">
              {item.semesters.reduce((acc, s) => acc + s.subjects.length, 0)}{" "}
              Subjects mapped
            </div>
          </div>
        ),
      },
      {
        id: "credits",
        header: "Total Credits",
        sortable: true,
        accessorKey: "totalCredits",
        cell: (item) => (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
            {item.totalCredits} Credits
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
            CurriculumStatus,
            "success" | "warning" | "destructive" | "info" | "secondary"
          > = {
            PUBLISHED: "success",
            APPROVED: "info",
            UNDER_REVIEW: "warning",
            DRAFT: "secondary",
            RETIRED: "destructive",
          };
          return (
            <Badge variant={statusMap[item.status] || "secondary"} dot>
              {item.status.replace("_", " ")}
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
            <Link href={`/app/academics/curricula/${item.id}`}>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 text-xs"
                leftIcon={<Eye className="h-3 w-3" />}
              >
                Builder
              </Button>
            </Link>
          </div>
        ),
      },
    ],
    [],
  );

  // Custom filter slot
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
        {departments.map((d) => (
          <option key={d.id} value={d.name}>
            {d.code} - {d.name}
          </option>
        ))}
      </select>

      <select
        value={selectedRegulation}
        onChange={(e) => {
          setSelectedRegulation(e.target.value);
          setCurrentPage(1);
        }}
        className="h-8 rounded-lg border border-slate-700 bg-slate-900 px-2.5 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
      >
        <option value="ALL">All Regulations</option>
        {regulationsList.map((r) => (
          <option key={r} value={r}>
            {r} Regulation
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
        <option value="PUBLISHED">Published</option>
        <option value="APPROVED">Approved</option>
        <option value="UNDER_REVIEW">Under Review</option>
        <option value="DRAFT">Draft</option>
        <option value="RETIRED">Retired</option>
      </select>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Page Header */}
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
            <span className="text-white">Curricula Management</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Curricula Schemes & Versioning
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            Degree regulations, CBCS program structures, semester credit
            distributions, and elective groupings.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="primary"
            size="sm"
            leftIcon={<Plus className="h-4 w-4" />}
            onClick={() => setCreateModalOpen(true)}
          >
            New Curriculum Scheme
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Curricula"
          value={curricula.length}
          description="Across all degree programs"
          variant="indigo"
          icon={<FileSpreadsheet className="h-4 w-4" />}
        />
        <StatCard
          label="Published Schemes"
          value={curricula.filter((c) => c.status === "PUBLISHED").length}
          description="Live & active for student cohorts"
          variant="emerald"
          icon={<CheckCircle2 className="h-4 w-4" />}
        />
        <StatCard
          label="Regulations Tracked"
          value={regulationsList.length}
          description="Autonomous revision guidelines"
          variant="sky"
          icon={<GitBranch className="h-4 w-4" />}
        />
        <StatCard
          label="Drafts / Under Review"
          value={
            curricula.filter(
              (c) => c.status === "DRAFT" || c.status === "UNDER_REVIEW",
            ).length
          }
          description="Pending Academic Council sign-off"
          variant="amber"
          icon={<ShieldCheck className="h-4 w-4" />}
        />
      </div>

      {/* Enterprise DataGrid */}
      <DataGrid<CurriculumScheme>
        data={paginatedCurricula}
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
        totalRecords={filteredCurricula.length}
        onPageChange={setCurrentPage}
        onPageSizeChange={(sz) => {
          setPageSize(sz);
          setCurrentPage(1);
        }}
        onSearchChange={(q) => {
          setSearch(q);
          setCurrentPage(1);
        }}
        searchPlaceholder="Search curriculum by program, regulation, or department..."
        customFilterSlot={customFilterSlot}
        exportFileName="campusos-curricula-schemes"
        emptyTitle="No Curricula Found"
        emptyDescription="No curriculum scheme records matched your filter criteria."
        emptyActionLabel="Clear Filters"
        onEmptyAction={() => {
          setSearch("");
          setSelectedDept("ALL");
          setSelectedStatus("ALL");
          setSelectedRegulation("ALL");
        }}
      />

      {/* Create Curriculum Dialog */}
      <Dialog
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Initialize New Curriculum Scheme"
      >
        <form onSubmit={handleCreateCurriculum} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Degree Program <span className="text-red-400">*</span>
            </label>
            <select
              value={programName}
              onChange={(e) => {
                setProgramName(e.target.value);
                const prog = programs.find((p) => p.name === e.target.value);
                if (prog) {
                  setProgramCode(prog.code);
                  setDepartment(prog.department);
                  setTotalCredits(prog.totalCredits || 160);
                  setTotalSemesters(prog.totalSemesters || 8);
                }
              }}
              className="w-full h-9 rounded-lg border border-slate-700 bg-slate-900 px-3 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
            >
              {programs.map((p) => (
                <option key={p.id} value={p.name}>
                  {p.name} ({p.code})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Regulation Framework <span className="text-red-400">*</span>
              </label>
              <Input
                placeholder="e.g. R-2026"
                value={regulation}
                onChange={(e) => setRegulation(e.target.value)}
                className={formErrors.regulation ? "border-red-500" : ""}
              />
              {formErrors.regulation && (
                <span className="text-[11px] text-red-400">
                  {formErrors.regulation}
                </span>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Scheme Version <span className="text-red-400">*</span>
              </label>
              <Input
                placeholder="e.g. v1.0"
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                className={formErrors.version ? "border-red-500" : ""}
              />
              {formErrors.version && (
                <span className="text-[11px] text-red-400">
                  {formErrors.version}
                </span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Academic Year
              </label>
              <Input
                value={academicYear}
                onChange={(e) => setAcademicYear(e.target.value)}
                placeholder="2026-2027"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Effective Date
              </label>
              <Input
                value={effectiveDate}
                onChange={(e) => setEffectiveDate(e.target.value)}
                placeholder="July 2026"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Total Prescribed Credits
              </label>
              <Input
                type="number"
                value={totalCredits}
                onChange={(e) => setTotalCredits(Number(e.target.value))}
                min="60"
                max="240"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Total Semesters
              </label>
              <Input
                type="number"
                value={totalSemesters}
                onChange={(e) => setTotalSemesters(Number(e.target.value))}
                min="1"
                max="12"
              />
            </div>
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
              Create Scheme
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
