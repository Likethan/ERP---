"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  Award,
  Plus,
  Search,
  Filter,
  Eye,
  CheckCircle2,
  DollarSign,
  Users,
  ShieldCheck,
  BookOpen,
} from "lucide-react";
import { DataGrid, ColumnDef } from "@/components/data-grid";
import { Button } from "@/components/ui/button";
import { StatCard } from "@/components/ui/stat-card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { useToast, ToastType } from "@/components/ui/toast";
import { useAuth } from "@/lib/auth-context";
import { financeService } from "@/services/finance.service";
import { formatMoney } from "@/services/financial-calculator";
import {
  Scholarship,
  ScholarshipStatus,
  ScholarshipType,
} from "@/types/finance";

export default function ScholarshipsPage() {
  const { hasPermission } = useAuth();
  const { showToast } = useToast();
  const notify = (title: string, type: ToastType = "info") =>
    showToast({ title, type });

  const [scholarships, setScholarships] = useState<Scholarship[]>([]);
  const [loading, setLoading] = useState(true);

  // Filter & Search
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [typeFilter, setTypeFilter] = useState<string>("ALL");

  // Create Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [type, setType] = useState<ScholarshipType>("MERIT");
  const [description, setDescription] = useState("");
  const [discountType, setDiscountType] = useState<"PERCENTAGE" | "FIXED">(
    "PERCENTAGE",
  );
  const [value, setValue] = useState<number>(20);
  const [maxDiscountAmount, setMaxDiscountAmount] = useState<number>(25000);
  const [eligibilityCriteria, setEligibilityCriteria] = useState("");
  const [academicYear, setAcademicYear] = useState("2026-2027");
  const [submitting, setSubmitting] = useState(false);

  const canManage =
    hasPermission("finance.manage_scholarships") ||
    hasPermission("scholarships:create");

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await financeService.getScholarships();
      setScholarships(res.data);
    } catch {
      notify("Error loading scholarship schemes", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateScheme = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      notify("Scholarship name is required.", "error");
      return;
    }
    if (value <= 0) {
      notify("Discount value must be greater than zero.", "error");
      return;
    }

    try {
      setSubmitting(true);
      await financeService.createScholarship({
        name: name.trim(),
        code: code.trim() || `SCH-${Date.now().toString().slice(-4)}`,
        type,
        description: description.trim(),
        discountType,
        value: Number(value),
        maxDiscountAmount: maxDiscountAmount
          ? Number(maxDiscountAmount)
          : undefined,
        eligibilityCriteria: eligibilityCriteria.trim(),
        academicYear,
      });

      notify("Scholarship scheme created successfully!", "success");
      setModalOpen(false);
      setName("");
      setCode("");
      setDescription("");
      setValue(20);
      setMaxDiscountAmount(25000);
      setEligibilityCriteria("");
      loadData();
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Failed to create scholarship.";
      notify(msg, "error");
    } finally {
      setSubmitting(false);
    }
  };

  // Metrics
  const activeCount = useMemo(() => {
    return scholarships.filter((s) => s.status === "APPROVED").length;
  }, [scholarships]);

  const totalRecipients = useMemo(() => {
    return scholarships.reduce((sum, s) => sum + (s.totalRecipients || 0), 0);
  }, [scholarships]);

  const filteredScholarships = useMemo(() => {
    return scholarships.filter((s) => {
      const matchesSearch =
        searchQuery === "" ||
        s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.type.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesStatus = statusFilter === "ALL" || s.status === statusFilter;
      const matchesType = typeFilter === "ALL" || s.type === typeFilter;

      return matchesSearch && matchesStatus && matchesType;
    });
  }, [scholarships, searchQuery, statusFilter, typeFilter]);

  const columns: ColumnDef<Scholarship>[] = [
    {
      id: "code",
      header: "Scheme Code",
      accessorKey: "code",
      sortable: true,
      cell: ({ row }) => (
        <Link
          href={`/app/finance/scholarships/${row.id}`}
          className="font-mono text-sm font-semibold text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 hover:underline"
        >
          {row.code}
        </Link>
      ),
    },
    {
      id: "name",
      header: "Scholarship / Assistance Name",
      accessorKey: "name",
      sortable: true,
      cell: ({ row }) => (
        <div>
          <div className="font-semibold text-slate-900 dark:text-white">
            {row.name}
          </div>
          <div className="text-xs text-slate-500 line-clamp-1">
            {row.description}
          </div>
        </div>
      ),
    },
    {
      id: "type",
      header: "Type",
      accessorKey: "type",
      cell: ({ row }) => (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
          {row.type}
        </span>
      ),
    },
    {
      id: "benefit",
      header: "Grant Benefit",
      cell: ({ row }) => (
        <div>
          <span className="font-bold text-emerald-700 dark:text-emerald-400">
            {row.discountType === "PERCENTAGE"
              ? `${row.value}% Waiver`
              : formatMoney(row.value)}
          </span>
          {row.maxDiscountAmount && (
            <div className="text-[11px] text-slate-500">
              Capped at {formatMoney(row.maxDiscountAmount)}
            </div>
          )}
        </div>
      ),
    },
    {
      id: "academicYear",
      header: "Academic Year",
      accessorKey: "academicYear",
      cell: ({ row }) => (
        <span className="text-xs text-slate-600">{row.academicYear}</span>
      ),
    },
    {
      id: "recipients",
      header: "Recipients",
      accessorKey: "totalRecipients",
      sortable: true,
      cell: ({ row }) => (
        <span className="font-semibold text-slate-900 dark:text-white">
          {row.totalRecipients || 0} students
        </span>
      ),
    },
    {
      id: "status",
      header: "Status",
      accessorKey: "status",
      cell: ({ row }) => {
        const badges: Record<string, string> = {
          APPROVED:
            "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300",
          PENDING_APPROVAL:
            "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300",
          DRAFT:
            "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300",
          REJECTED:
            "bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300",
          EXPIRED:
            "bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-400",
        };
        return (
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
              badges[row.status] || "bg-slate-100 text-slate-700"
            }`}
          >
            {row.status}
          </span>
        );
      },
    },
    {
      id: "actions",
      header: "Actions",
      cell: ({ row }) => (
        <Link href={`/app/finance/scholarships/${row.id}`}>
          <Button variant="ghost" size="sm" className="h-8 px-2 text-xs">
            <Eye className="w-3.5 h-3.5 mr-1" />
            Manage
          </Button>
        </Link>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 mb-1">
            <Link
              href="/app/finance"
              className="hover:text-emerald-600 transition"
            >
              Finance Hub
            </Link>
            <span>/</span>
            <span className="font-semibold text-slate-700 dark:text-slate-300">
              Scholarships
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Scholarship Schemes & Concessions
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Institutional fee discounts, merit grants, socio-economic waivers,
            and student allocations.
          </p>
        </div>

        {canManage && (
          <Button
            variant="primary"
            onClick={() => setModalOpen(true)}
            className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs"
          >
            <Plus className="w-4 h-4" />
            Define Scheme
          </Button>
        )}
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          title="Active Schemes"
          value={activeCount.toString()}
          description="Approved institutional funding grants"
          icon={<Award className="w-5 h-5 text-emerald-600" />}
        />
        <StatCard
          title="Benefited Students"
          value={`${totalRecipients} Awardees`}
          description="Students receiving verified financial assistance"
          icon={<Users className="w-5 h-5 text-blue-600" />}
        />
        <StatCard
          title="Institutional Budget"
          value="₹12.50 Lakhs"
          description="Earmarked endowment & merit subsidy"
          icon={<DollarSign className="w-5 h-5 text-teal-600" />}
        />
      </div>

      {/* Filter and Search */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-white p-4 rounded-xl border border-slate-200 dark:bg-slate-900 dark:border-slate-800">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <Input
            placeholder="Search Scheme Name, Code, Type..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 text-sm"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2.5 w-full sm:w-auto">
          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
            <Filter className="w-3.5 h-3.5" />
            Status:
          </div>
          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs h-9 w-36"
          >
            <option value="ALL">All Status</option>
            <option value="APPROVED">Approved</option>
            <option value="PENDING_APPROVAL">Pending Approval</option>
            <option value="DRAFT">Draft</option>
            <option value="REJECTED">Rejected</option>
          </Select>

          <Select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="text-xs h-9 w-36"
          >
            <option value="ALL">All Types</option>
            <option value="MERIT">Merit</option>
            <option value="MEANS">Means</option>
            <option value="SPORTS">Sports</option>
            <option value="STAFF_CHILD">Staff Ward</option>
            <option value="GOVERNMENT">Government</option>
            <option value="INSTITUTIONAL">Institutional</option>
          </Select>
        </div>
      </div>

      {/* Main DataGrid */}
      <DataGrid
        columns={columns}
        data={filteredScholarships}
        loading={loading}
        keyExtractor={(row) => row.id}
        emptyMessage="No scholarship schemes found matching the filters."
      />

      {/* Create Scheme Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-lg font-bold">
              <Award className="w-5 h-5 text-emerald-600" />
              Define New Scholarship / Waiver Scheme
            </DialogTitle>
          </DialogHeader>

          <form onSubmit={handleCreateScheme} className="space-y-4 pt-2">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Scheme Code <span className="text-rose-500">*</span>
                </label>
                <Input
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="e.g. MERIT-BTECH-2026"
                  className="mt-1 font-mono uppercase"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Category / Type <span className="text-rose-500">*</span>
                </label>
                <Select
                  value={type}
                  onChange={(e) => setType(e.target.value as ScholarshipType)}
                  className="mt-1"
                >
                  <option value="MERIT">Merit Scheme</option>
                  <option value="MEANS">Need / Means Based</option>
                  <option value="SPORTS">Sports Excellence</option>
                  <option value="STAFF_CHILD">Staff Child Concession</option>
                  <option value="GOVERNMENT">Government Sponsored</option>
                  <option value="INSTITUTIONAL">Institutional Trust</option>
                </Select>
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Scheme Name / Title <span className="text-rose-500">*</span>
              </label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Academic Dean's Honors Merit Scholarship"
                className="mt-1"
                required
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Calculation Method
                </label>
                <Select
                  value={discountType}
                  onChange={(e) =>
                    setDiscountType(e.target.value as "PERCENTAGE" | "FIXED")
                  }
                  className="mt-1"
                >
                  <option value="PERCENTAGE">Percentage (%)</option>
                  <option value="FIXED">Fixed Amount (₹)</option>
                </Select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Value ({discountType === "PERCENTAGE" ? "%" : "₹"}){" "}
                  <span className="text-rose-500">*</span>
                </label>
                <Input
                  type="number"
                  min={1}
                  max={discountType === "PERCENTAGE" ? 100 : 500000}
                  value={value}
                  onChange={(e) => setValue(Number(e.target.value))}
                  className="mt-1"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Max Cap Limit (₹)
                </label>
                <Input
                  type="number"
                  value={maxDiscountAmount || ""}
                  onChange={(e) => setMaxDiscountAmount(Number(e.target.value))}
                  placeholder="Optional max cap"
                  className="mt-1"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Eligibility Criteria & Regulations
              </label>
              <Input
                value={eligibilityCriteria}
                onChange={(e) => setEligibilityCriteria(e.target.value)}
                placeholder="e.g. CGPA >= 9.0 without standing backlogs"
                className="mt-1"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Scheme Description
              </label>
              <Input
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Institutional description and terms"
                className="mt-1"
              />
            </div>

            <DialogFooter className="pt-3">
              <Button
                type="button"
                variant="outline"
                onClick={() => setModalOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={submitting}
                className="bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                {submitting ? "Saving..." : "Create Scheme"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
