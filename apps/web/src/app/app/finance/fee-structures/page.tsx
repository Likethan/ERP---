"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  Layers,
  Plus,
  Search,
  Filter,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  Clock,
  Trash2,
  Eye,
  FileCheck2,
  DollarSign,
  AlertTriangle,
  Send,
  Lock,
} from "lucide-react";
import { DataGrid, ColumnDef } from "@/components/data-grid/data-grid";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/ui/stat-card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/toast";
import { useAuth } from "@/lib/auth-context";
import { financeService } from "@/services/finance.service";
import { formatMoney } from "@/services/financial-calculator";
import { FeeStructure, FeeCategory, FeeStructureStatus } from "@/types/finance";

const PROGRAMS = [
  "B.Tech Computer Science & Engineering",
  "B.Tech Electronics & Communication",
  "B.Tech AI & Data Science",
  "B.Tech Mechanical Engineering",
  "All Residential Students",
];

const SEMESTERS = [1, 2, 3, 4, 5, 6, 7, 8];

export default function FeeStructuresPage() {
  const { hasPermission } = useAuth();
  const { showToast } = useToast();

  const [structures, setStructures] = useState<FeeStructure[]>([]);
  const [categories, setCategories] = useState<FeeCategory[]>([]);
  const [loading, setLoading] = useState(true);

  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [programFilter, setProgramFilter] = useState<string>("ALL");

  // 6-Step Guided Creation Modal State
  const [wizardOpen, setWizardOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [saving, setSaving] = useState(false);

  // Wizard Form Fields
  const [wizardName, setWizardName] = useState("");
  const [wizardCode, setWizardCode] = useState("");
  const [wizardProgram, setWizardProgram] = useState(PROGRAMS[0]);
  const [wizardAcademicYear, setWizardAcademicYear] = useState("2026-2027");
  const [wizardSemester, setWizardSemester] = useState(5);
  const [wizardNotes, setWizardNotes] = useState("");
  const [wizardComponents, setWizardComponents] = useState<
    Array<{ id: string; title: string; categoryName: string; amount: number; isMandatory: boolean }>
  >([
    { id: "c-1", title: "Academic Tuition Fee", categoryName: "Tuition Fee", amount: 55000, isMandatory: true },
    { id: "c-2", title: "Laboratory & Computing Levy", categoryName: "Laboratory Fee", amount: 15000, isMandatory: true },
    { id: "c-3", title: "Semester Examination Fee", categoryName: "Examination Fee", amount: 3500, isMandatory: true },
  ]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [structRes, catRes] = await Promise.all([
        financeService.getFeeStructures(),
        financeService.getFeeCategories(),
      ]);
      setStructures(structRes.data);
      setCategories(catRes.data);
    } catch (err: unknown) {
      showToast({
        title: "Error Loading Fee Structures",
        message: err instanceof Error ? err.message : "Unable to retrieve fee structures",
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const openWizard = () => {
    setCurrentStep(1);
    setWizardName("B.Tech Standard Tuition Scheme");
    setWizardCode(`FS-2026-${Date.now().toString().slice(-4)}`);
    setWizardProgram(PROGRAMS[0]);
    setWizardAcademicYear("2026-2027");
    setWizardSemester(5);
    setWizardNotes("Draft fee structure created for departmental review.");
    setWizardComponents([
      { id: "c-1", title: "Academic Tuition Fee", categoryName: "Tuition Fee", amount: 55000, isMandatory: true },
      { id: "c-2", title: "Laboratory & Computing Levy", categoryName: "Laboratory Fee", amount: 15000, isMandatory: true },
      { id: "c-3", title: "Semester Examination Fee", categoryName: "Examination Fee", amount: 3500, isMandatory: true },
    ]);
    setWizardOpen(true);
  };

  const handleAddComponent = () => {
    setWizardComponents((prev) => [
      ...prev,
      {
        id: `c-${Date.now()}`,
        title: "Campus Development & Student Welfare",
        categoryName: categories[0]?.name || "Development Fee",
        amount: 5000,
        isMandatory: true,
      },
    ]);
  };

  const handleRemoveComponent = (idx: number) => {
    if (wizardComponents.length <= 1) {
      showToast({ title: "Validation Error", message: "At least one component is required.", type: "error" });
      return;
    }
    setWizardComponents((prev) => prev.filter((_, i) => i !== idx));
  };

  const grossCalculated = useMemo(() => {
    return wizardComponents.reduce((acc, c) => acc + (c.amount || 0), 0);
  }, [wizardComponents]);

  const handleSaveDraft = async () => {
    try {
      setSaving(true);
      await financeService.createFeeStructure({
        code: wizardCode,
        name: wizardName,
        program: wizardProgram,
        academicYear: wizardAcademicYear,
        semester: wizardSemester,
        components: wizardComponents,
        grossTotal: grossCalculated,
        notes: wizardNotes,
      });

      showToast({
        title: "Draft Saved",
        message: "Fee Structure saved in DRAFT state. Awaiting formal approval.",
        type: "success",
      });
      setWizardOpen(false);
      loadData();
    } catch (err: unknown) {
      showToast({
        title: "Save Failed",
        message: err instanceof Error ? err.message : "Unable to save fee structure",
        type: "error",
      });
    } finally {
      setSaving(false);
    }
  };

  const filteredStructures = useMemo(() => {
    return structures.filter((s) => {
      const matchesSearch =
        s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.program.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus = statusFilter === "ALL" || s.status === statusFilter;
      const matchesProgram = programFilter === "ALL" || s.program === programFilter;
      return matchesSearch && matchesStatus && matchesProgram;
    });
  }, [structures, searchQuery, statusFilter, programFilter]);

  const activeCount = structures.filter((s) => s.status === "ACTIVE").length;
  const pendingCount = structures.filter((s) => s.status === "PENDING_APPROVAL").length;
  const totalStudents = structures.reduce((acc, s) => acc + (s.totalStudentsAssigned || 0), 0);

  const getStatusBadge = (status: FeeStructureStatus) => {
    switch (status) {
      case "ACTIVE":
        return <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Active</span>;
      case "PENDING_APPROVAL":
        return <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">Pending Approval</span>;
      case "APPROVED":
        return <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">Approved</span>;
      case "DRAFT":
        return <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700/60">Draft</span>;
      case "RETIRED":
        return <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">Retired</span>;
    }
  };

  const columns: ColumnDef<FeeStructure>[] = [
    {
      id: "code",
      header: "Scheme Code",
      accessorKey: "code",
      sortable: true,
      cell: (row) => (
        <span className="font-mono text-xs font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
          {row.code}
        </span>
      ),
    },
    {
      id: "name",
      header: "Structure & Program",
      accessorKey: "name",
      sortable: true,
      cell: (row) => (
        <div>
          <Link
            href={`/app/finance/fee-structures/${row.id}`}
            className="font-medium text-slate-200 hover:text-indigo-400 transition-colors"
          >
            {row.name}
          </Link>
          <p className="text-xs text-slate-400">
            {row.program} • Semester {row.semester} ({row.academicYear})
          </p>
        </div>
      ),
    },
    {
      id: "components",
      header: "Components",
      cell: (row) => (
        <span className="text-xs text-slate-300">
          {row.components.length} heads
        </span>
      ),
    },
    {
      id: "total",
      header: "Gross Total",
      accessorKey: "grossTotal",
      sortable: true,
      cell: (row) => (
        <span className="font-mono text-xs font-semibold text-slate-200">
          {formatMoney(row.grossTotal)}
        </span>
      ),
    },
    {
      id: "students",
      header: "Assigned",
      cell: (row) => (
        <span className="text-xs text-slate-300">
          {row.totalStudentsAssigned || 0} students
        </span>
      ),
    },
    {
      id: "status",
      header: "Status",
      accessorKey: "status",
      sortable: true,
      cell: (row) => getStatusBadge(row.status),
    },
    {
      id: "actions",
      header: "Actions",
      cell: (row) => (
        <div className="flex items-center gap-2">
          <Link href={`/app/finance/fee-structures/${row.id}`}>
            <Button variant="ghost" size="sm" className="h-7 text-xs text-slate-300 hover:text-white">
              <Eye className="h-3.5 w-3.5 mr-1" />
              View
            </Button>
          </Link>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-medium text-slate-400 mb-1">
            <Link href="/app/finance" className="hover:text-slate-200 transition-colors">
              Finance
            </Link>
            <span>/</span>
            <span className="text-slate-200">Fee Structures</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <Layers className="h-6 w-6 text-indigo-400" />
            Fee Structures Directory
          </h1>
          <p className="mt-1 text-xs text-slate-400 max-w-2xl">
            Configure academic, laboratory, examination, and hostel billing schedules. Structures follow strict approval lifecycles before student fee assignment.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="primary" size="sm" onClick={openWizard} className="gap-1.5 text-xs">
            <Plus className="h-3.5 w-3.5" />
            Configure Fee Structure
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          title="Active Fee Schedules"
          value={activeCount}
          description="In-effect for academic billing"
          icon={<CheckCircle2 className="h-5 w-5 text-emerald-400" />}
        />
        <StatCard
          title="Pending Approval"
          value={pendingCount}
          description="Awaiting Senate ratification"
          icon={<Clock className="h-5 w-5 text-amber-400" />}
        />
        <StatCard
          title="Assigned Students"
          value={totalStudents}
          description="Total enrolled billing accounts"
          icon={<Layers className="h-5 w-5 text-indigo-400" />}
        />
      </div>

      {/* Filters Toolbar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <Input
            placeholder="Search code, title, program..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 h-9 text-xs bg-slate-950/60 border-slate-800 text-slate-200"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Select
            value={programFilter}
            onChange={(e) => setProgramFilter(e.target.value)}
            className="h-9 text-xs w-56 bg-slate-950/60 border-slate-800 text-slate-200"
          >
            <option value="ALL">All Academic Programs</option>
            {PROGRAMS.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </Select>

          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="h-9 text-xs w-36 bg-slate-950/60 border-slate-800 text-slate-200"
          >
            <option value="ALL">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="PENDING_APPROVAL">Pending Approval</option>
            <option value="APPROVED">Approved</option>
            <option value="DRAFT">Draft</option>
            <option value="RETIRED">Retired</option>
          </Select>
        </div>
      </div>

      {/* Structures DataGrid */}
      <DataGrid
        data={filteredStructures}
        columns={columns}
        keyExtractor={(row) => row.id}
        loading={loading}
        emptyState={
          <div className="py-12 text-center">
            <Layers className="mx-auto h-10 w-10 text-slate-600 mb-2" />
            <p className="text-sm font-semibold text-slate-300">No Fee Structures Found</p>
            <p className="text-xs text-slate-500 mt-1">Try resetting search criteria or configure a new fee structure.</p>
          </div>
        }
      />

      {/* 6-Step Guided Creation Modal */}
      <Dialog open={wizardOpen} onOpenChange={setWizardOpen}>
        <DialogContent className="max-w-2xl bg-slate-900 border-slate-800 text-slate-200">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold text-white flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Layers className="h-5 w-5 text-indigo-400" />
                Configure Fee Structure Wizard
              </span>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                Step {currentStep} of 6
              </span>
            </DialogTitle>
          </DialogHeader>

          {/* Step Indicator Bar */}
          <div className="grid grid-cols-6 gap-1 py-1">
            {[1, 2, 3, 4, 5, 6].map((s) => (
              <div
                key={s}
                className={`h-1.5 rounded-full transition-all ${
                  s === currentStep
                    ? "bg-indigo-500"
                    : s < currentStep
                    ? "bg-emerald-500"
                    : "bg-slate-800"
                }`}
              />
            ))}
          </div>

          <div className="py-3">
            {/* Step 1: Program & Academic Period */}
            {currentStep === 1 && (
              <div className="space-y-4 animate-fade-in">
                <h3 className="text-sm font-semibold text-white">Step 1: Program & Academic Context</h3>
                <div className="grid grid-cols-2 gap-3">
                  <div className="col-span-2">
                    <label className="text-xs font-semibold text-slate-300 block mb-1">
                      Structure Name <span className="text-rose-400">*</span>
                    </label>
                    <Input
                      value={wizardName}
                      onChange={(e) => setWizardName(e.target.value)}
                      placeholder="e.g. B.Tech Computer Science Semester 5 Standard Fee Scheme"
                      className="h-8 text-xs bg-slate-950 border-slate-800"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-slate-300 block mb-1">
                      Scheme Code <span className="text-rose-400">*</span>
                    </label>
                    <Input
                      value={wizardCode}
                      onChange={(e) => setWizardCode(e.target.value.toUpperCase())}
                      className="h-8 text-xs font-mono uppercase bg-slate-950 border-slate-800"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-slate-300 block mb-1">
                      Academic Year
                    </label>
                    <Select
                      value={wizardAcademicYear}
                      onChange={(e) => setWizardAcademicYear(e.target.value)}
                      className="h-8 text-xs bg-slate-950 border-slate-800"
                    >
                      <option value="2026-2027">2026-2027</option>
                      <option value="2025-2026">2025-2026</option>
                    </Select>
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-slate-300 block mb-1">
                      Academic Program
                    </label>
                    <Select
                      value={wizardProgram}
                      onChange={(e) => setWizardProgram(e.target.value)}
                      className="h-8 text-xs bg-slate-950 border-slate-800"
                    >
                      {PROGRAMS.map((p) => (
                        <option key={p} value={p}>
                          {p}
                        </option>
                      ))}
                    </Select>
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-slate-300 block mb-1">
                      Semester
                    </label>
                    <Select
                      value={wizardSemester.toString()}
                      onChange={(e) => setWizardSemester(parseInt(e.target.value, 10))}
                      className="h-8 text-xs bg-slate-950 border-slate-800"
                    >
                      {SEMESTERS.map((sem) => (
                        <option key={sem} value={sem}>
                          Semester {sem}
                        </option>
                      ))}
                    </Select>
                  </div>
                </div>
              </div>
            )}

            {/* Step 2: Select Fee Categories / Items */}
            {currentStep === 2 && (
              <div className="space-y-3 animate-fade-in">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-white">Step 2: Select Fee Categories & Heads</h3>
                  <Button variant="outline" size="sm" onClick={handleAddComponent} className="h-7 text-xs gap-1">
                    <Plus className="h-3 w-3" />
                    Add Head
                  </Button>
                </div>

                <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                  {wizardComponents.map((comp, idx) => (
                    <div
                      key={comp.id}
                      className="flex items-center gap-2 p-2.5 rounded-lg bg-slate-950 border border-slate-800"
                    >
                      <span className="font-mono text-xs text-slate-500 w-6">#{idx + 1}</span>
                      <Input
                        value={comp.title}
                        onChange={(e) => {
                          const val = e.target.value;
                          setWizardComponents((prev) =>
                            prev.map((c, i) => (i === idx ? { ...c, title: val } : c))
                          );
                        }}
                        className="h-8 text-xs flex-1 bg-slate-900 border-slate-800"
                        placeholder="Component Title"
                      />
                      <Select
                        value={comp.categoryName}
                        onChange={(e) => {
                          const val = e.target.value;
                          setWizardComponents((prev) =>
                            prev.map((c, i) => (i === idx ? { ...c, categoryName: val } : c))
                          );
                        }}
                        className="h-8 text-xs w-44 bg-slate-900 border-slate-800"
                      >
                        {categories.map((cat) => (
                          <option key={cat.id} value={cat.name}>
                            {cat.name}
                          </option>
                        ))}
                      </Select>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemoveComponent(idx)}
                        className="h-8 w-8 p-0 text-slate-500 hover:text-rose-400"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Step 3: Configure Amounts */}
            {currentStep === 3 && (
              <div className="space-y-3 animate-fade-in">
                <h3 className="text-sm font-semibold text-white">Step 3: Configure Component Amounts</h3>
                <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                  {wizardComponents.map((comp, idx) => (
                    <div
                      key={comp.id}
                      className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950 border border-slate-800"
                    >
                      <div>
                        <p className="text-xs font-semibold text-slate-200">{comp.title}</p>
                        <p className="text-[11px] text-slate-400">{comp.categoryName}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono text-slate-400">₹</span>
                        <Input
                          type="number"
                          min="0"
                          value={comp.amount.toString()}
                          onChange={(e) => {
                            const val = parseFloat(e.target.value) || 0;
                            setWizardComponents((prev) =>
                              prev.map((c, i) => (i === idx ? { ...c, amount: val } : c))
                            );
                          }}
                          className="h-8 text-xs w-32 font-mono text-right bg-slate-900 border-slate-800"
                        />
                      </div>
                    </div>
                  ))}
                </div>
                <div className="flex justify-between items-center pt-2 border-t border-slate-800">
                  <span className="text-xs font-semibold text-slate-400">Gross Total Calculation:</span>
                  <span className="font-mono text-sm font-bold text-emerald-400">
                    {formatMoney(grossCalculated)}
                  </span>
                </div>
              </div>
            )}

            {/* Step 4: Configure Applicability */}
            {currentStep === 4 && (
              <div className="space-y-3 animate-fade-in">
                <h3 className="text-sm font-semibold text-white">Step 4: Configure Applicability Rules</h3>
                <p className="text-xs text-slate-400">
                  Designate mandatory vs optional levies (e.g. hostel accommodation or student bus transit).
                </p>
                <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                  {wizardComponents.map((comp, idx) => (
                    <div
                      key={comp.id}
                      className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950 border border-slate-800"
                    >
                      <div>
                        <p className="text-xs font-semibold text-slate-200">{comp.title}</p>
                        <p className="font-mono text-[11px] text-slate-400">{formatMoney(comp.amount)}</p>
                      </div>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={comp.isMandatory}
                          onChange={(e) => {
                            const checked = e.target.checked;
                            setWizardComponents((prev) =>
                              prev.map((c, i) => (i === idx ? { ...c, isMandatory: checked } : c))
                            );
                          }}
                          className="rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-indigo-500"
                        />
                        <span className="text-xs font-medium text-slate-300">
                          {comp.isMandatory ? "Mandatory" : "Optional / Opt-in"}
                        </span>
                      </label>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Step 5: Notes & Documentation */}
            {currentStep === 5 && (
              <div className="space-y-3 animate-fade-in">
                <h3 className="text-sm font-semibold text-white">Step 5: Governance Notes & Effective Date</h3>
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">
                    Administrative Notes & Committee Sanction
                  </label>
                  <Textarea
                    rows={4}
                    value={wizardNotes}
                    onChange={(e) => setWizardNotes(e.target.value)}
                    placeholder="Reference Senate approval minutes, statutory guidelines, or installment policies..."
                    className="text-xs bg-slate-950 border-slate-800"
                  />
                </div>
              </div>
            )}

            {/* Step 6: Review & Save Draft */}
            {currentStep === 6 && (
              <div className="space-y-3 animate-fade-in">
                <h3 className="text-sm font-semibold text-white">Step 6: Review Scheme Specifications</h3>
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Scheme Code:</span>
                    <span className="font-mono font-bold text-indigo-400">{wizardCode}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Program:</span>
                    <span className="text-slate-200">{wizardProgram} (Sem {wizardSemester})</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Academic Year:</span>
                    <span className="text-slate-200">{wizardAcademicYear}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Billing Heads:</span>
                    <span className="text-slate-200">{wizardComponents.length} components</span>
                  </div>
                  <div className="flex justify-between border-t border-slate-800 pt-2 font-bold text-sm">
                    <span className="text-white">Gross Scheme Total:</span>
                    <span className="font-mono text-emerald-400">{formatMoney(grossCalculated)}</span>
                  </div>
                </div>

                <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 flex items-start gap-2">
                  <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                  <span>
                    This structure will be saved in <strong>DRAFT</strong> status. Per institutional governance, it will not be activated or billed to students until formally approved.
                  </span>
                </div>
              </div>
            )}
          </div>

          <DialogFooter className="pt-3 border-t border-slate-800 flex justify-between items-center sm:justify-between">
            <div>
              {currentStep > 1 && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentStep((s) => s - 1)}
                  className="gap-1 text-xs"
                >
                  <ArrowLeft className="h-3.5 w-3.5" />
                  Previous
                </Button>
              )}
            </div>

            <div className="flex items-center gap-2">
              <Button type="button" variant="ghost" size="sm" onClick={() => setWizardOpen(false)}>
                Cancel
              </Button>
              {currentStep < 6 ? (
                <Button
                  type="button"
                  variant="primary"
                  size="sm"
                  onClick={() => setCurrentStep((s) => s + 1)}
                  className="gap-1 text-xs"
                >
                  Next Step
                  <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              ) : (
                <Button
                  type="button"
                  variant="primary"
                  size="sm"
                  onClick={handleSaveDraft}
                  disabled={saving}
                  className="gap-1 text-xs"
                >
                  {saving ? "Saving Draft..." : "Save Structure Draft"}
                </Button>
              )}
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
