"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  Tag,
  Plus,
  Search,
  Filter,
  Layers,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Edit,
  Power,
  ShieldCheck,
  FileText,
  DollarSign,
} from "lucide-react";
import { DataGrid, ColumnDef } from "@/components/data-grid/data-grid";
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
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/toast";
import { useAuth } from "@/lib/auth-context";
import { financeService } from "@/services/finance.service";
import {
  FeeCategory,
  FeeCategoryType,
  FeeCategoryStatus,
} from "@/types/finance";

const CATEGORY_TYPE_LABELS: Record<string, string> = {
  TUITION: "Tuition & Instruction",
  EXAMINATION: "Examination & Evaluation",
  LABORATORY: "Laboratory & Computing",
  LIBRARY: "Library & E-Resources",
  TRANSPORT: "Transit & Commuter Bus",
  HOSTEL: "Hostel & Dining Facility",
  DEVELOPMENT: "Campus Welfare & Infrastructure",
  SPORTS: "Sports & Physical Education",
  OTHER: "Institutional Miscellaneous",
};

export default function FeeCategoriesPage() {
  const { hasPermission } = useAuth();
  const { showToast } = useToast();

  const [categories, setCategories] = useState<FeeCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // Create / Edit modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState<FeeCategory | null>(
    null,
  );
  const [saving, setSaving] = useState(false);

  const [formName, setFormName] = useState("");
  const [formCode, setFormCode] = useState("");
  const [formDescription, setFormDescription] = useState("");
  const [formType, setFormType] = useState<FeeCategoryType>("TUITION");
  const [formIsTaxable, setFormIsTaxable] = useState(false);
  const [formIsRefundable, setFormIsRefundable] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await financeService.getFeeCategories();
      setCategories(res.data);
    } catch (err: unknown) {
      showToast({
        title: "Error Loading Categories",
        message:
          err instanceof Error ? err.message : "Failed to load fee categories",
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const openCreateModal = () => {
    setEditingCategory(null);
    setFormName("");
    setFormCode("");
    setFormDescription("");
    setFormType("TUITION");
    setFormIsTaxable(false);
    setFormIsRefundable(false);
    setModalOpen(true);
  };

  const openEditModal = (cat: FeeCategory) => {
    setEditingCategory(cat);
    setFormName(cat.name);
    setFormCode(cat.code);
    setFormDescription(cat.description);
    setFormType(cat.type);
    setFormIsTaxable(cat.isTaxable);
    setFormIsRefundable(cat.isRefundable);
    setModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName.trim() || !formCode.trim()) {
      showToast({
        title: "Validation Error",
        message: "Please enter category name and unique code.",
        type: "error",
      });
      return;
    }

    try {
      setSaving(true);
      if (editingCategory) {
        await financeService.updateFeeCategory(editingCategory.id, {
          name: formName.trim(),
          code: formCode.trim().toUpperCase(),
          description: formDescription.trim(),
          type: formType,
          isTaxable: formIsTaxable,
          isRefundable: formIsRefundable,
        });
        showToast({
          title: "Updated",
          message: "Fee category updated successfully.",
          type: "success",
        });
      } else {
        await financeService.createFeeCategory({
          name: formName.trim(),
          code: formCode.trim().toUpperCase(),
          description: formDescription.trim(),
          type: formType,
          isTaxable: formIsTaxable,
          isRefundable: formIsRefundable,
        });
        showToast({
          title: "Created",
          message: "New fee category registered.",
          type: "success",
        });
      }
      setModalOpen(false);
      loadData();
    } catch (err: unknown) {
      showToast({
        title: "Save Failed",
        message: err instanceof Error ? err.message : "Unable to save category",
        type: "error",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleToggleStatus = async (cat: FeeCategory) => {
    try {
      await financeService.toggleCategoryStatus(cat.id);
      showToast({
        title: "Status Changed",
        message: `${cat.name} is now ${cat.status === "ACTIVE" ? "Inactive" : "Active"}.`,
        type: "info",
      });
      loadData();
    } catch (err: unknown) {
      showToast({
        title: "Toggle Error",
        message:
          err instanceof Error
            ? err.message
            : "Could not toggle category status",
        type: "error",
      });
    }
  };

  const filteredCategories = useMemo(() => {
    return categories.filter((c) => {
      const matchesSearch =
        c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.description.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesType = typeFilter === "ALL" || c.type === typeFilter;
      const matchesStatus = statusFilter === "ALL" || c.status === statusFilter;
      return matchesSearch && matchesType && matchesStatus;
    });
  }, [categories, searchQuery, typeFilter, statusFilter]);

  const activeCount = categories.filter((c) => c.status === "ACTIVE").length;
  const refundableCount = categories.filter((c) => c.isRefundable).length;

  const columns: ColumnDef<FeeCategory>[] = [
    {
      id: "code",
      header: "Code",
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
      header: "Category Name",
      accessorKey: "name",
      sortable: true,
      cell: (row) => (
        <div>
          <p className="font-medium text-slate-200">{row.name}</p>
          <p className="text-xs text-slate-400 line-clamp-1">
            {row.description}
          </p>
        </div>
      ),
    },
    {
      id: "type",
      header: "Category Type",
      accessorKey: "type",
      sortable: true,
      cell: (row) => (
        <span className="text-xs text-slate-300">
          {CATEGORY_TYPE_LABELS[row.type] || row.type}
        </span>
      ),
    },
    {
      id: "attributes",
      header: "Taxable / Refundable",
      cell: (row) => (
        <div className="flex items-center gap-1.5 text-xs">
          <span
            className={`px-1.5 py-0.5 rounded text-[11px] font-medium ${
              row.isRefundable
                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                : "bg-slate-800 text-slate-400 border border-slate-700/60"
            }`}
          >
            {row.isRefundable ? "Refundable" : "Non-refundable"}
          </span>
          {row.isTaxable && (
            <span className="px-1.5 py-0.5 rounded text-[11px] font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
              Taxable
            </span>
          )}
        </div>
      ),
    },
    {
      id: "status",
      header: "Status",
      accessorKey: "status",
      sortable: true,
      cell: (row) => (
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${
            row.status === "ACTIVE"
              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
              : "bg-slate-800 text-slate-400 border border-slate-700/60"
          }`}
        >
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              row.status === "ACTIVE" ? "bg-emerald-400" : "bg-slate-500"
            }`}
          />
          {row.status}
        </span>
      ),
    },
    {
      id: "actions",
      header: "Actions",
      cell: (row) => (
        <div className="flex items-center gap-1.5">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => openEditModal(row)}
            className="h-7 w-7 p-0 text-slate-400 hover:text-slate-200"
            title="Edit category"
          >
            <Edit className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleToggleStatus(row)}
            className={`h-7 w-7 p-0 ${
              row.status === "ACTIVE"
                ? "text-slate-400 hover:text-rose-400"
                : "text-slate-400 hover:text-emerald-400"
            }`}
            title={row.status === "ACTIVE" ? "Deactivate" : "Activate"}
          >
            <Power className="h-3.5 w-3.5" />
          </Button>
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
            <Link
              href="/app/finance"
              className="hover:text-slate-200 transition-colors"
            >
              Finance
            </Link>
            <span>/</span>
            <span className="text-slate-200">Fee Categories</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <Tag className="h-6 w-6 text-indigo-400" />
            Fee Categories & Billing Heads
          </h1>
          <p className="mt-1 text-xs text-slate-400 max-w-2xl">
            Standard institutional fee classifications for tuition, laboratory,
            examinations, facilities, hostel accommodation, and statutory
            levies.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="primary"
            size="sm"
            onClick={openCreateModal}
            className="gap-1.5 text-xs"
          >
            <Plus className="h-3.5 w-3.5" />
            New Category
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          title="Total Fee Categories"
          value={categories.length}
          description="Institutional heads of account"
          icon={<Tag className="h-5 w-5 text-indigo-400" />}
        />
        <StatCard
          title="Active Categories"
          value={activeCount}
          description="Available for fee structures"
          icon={<CheckCircle2 className="h-5 w-5 text-emerald-400" />}
        />
        <StatCard
          title="Refundable Categories"
          value={refundableCount}
          description="Subject to caution reimbursement"
          icon={<ShieldCheck className="h-5 w-5 text-cyan-400" />}
        />
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <Input
            placeholder="Search code, name, description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 h-9 text-xs bg-slate-950/60 border-slate-800 text-slate-200"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="h-9 text-xs w-48 bg-slate-950/60 border-slate-800 text-slate-200"
          >
            <option value="ALL">All Category Types</option>
            <option value="TUITION">Tuition & Instruction</option>
            <option value="EXAMINATION">Examination & Evaluation</option>
            <option value="LABORATORY">Laboratory & Computing</option>
            <option value="LIBRARY">Library & E-Resources</option>
            <option value="HOSTEL">Hostel & Dining</option>
            <option value="TRANSPORT">Transit & Transport</option>
            <option value="DEVELOPMENT">Campus Development</option>
          </Select>

          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="h-9 text-xs w-32 bg-slate-950/60 border-slate-800 text-slate-200"
          >
            <option value="ALL">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="INACTIVE">Inactive</option>
          </Select>
        </div>
      </div>

      {/* Categories DataGrid */}
      <DataGrid
        data={filteredCategories}
        columns={columns}
        keyExtractor={(row) => row.id}
        loading={loading}
        emptyState={
          <div className="py-12 text-center">
            <Tag className="mx-auto h-10 w-10 text-slate-600 mb-2" />
            <p className="text-sm font-semibold text-slate-300">
              No Fee Categories Found
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Try adjusting search query or active filters.
            </p>
          </div>
        }
      />

      {/* Create / Edit Dialog */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-md bg-slate-900 border-slate-800 text-slate-200">
          <DialogHeader>
            <DialogTitle className="text-lg font-bold text-white flex items-center gap-2">
              <Tag className="h-5 w-5 text-indigo-400" />
              {editingCategory
                ? "Edit Fee Category"
                : "Register New Fee Category"}
            </DialogTitle>
          </DialogHeader>

          <form onSubmit={handleSave} className="space-y-4 py-2">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Category Code <span className="text-rose-400">*</span>
                </label>
                <Input
                  required
                  placeholder="e.g. TUI, LAB"
                  value={formCode}
                  onChange={(e) => setFormCode(e.target.value.toUpperCase())}
                  className="h-8 text-xs font-mono uppercase bg-slate-950 border-slate-800"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Classification Type <span className="text-rose-400">*</span>
                </label>
                <Select
                  value={formType}
                  onChange={(e) =>
                    setFormType(e.target.value as FeeCategoryType)
                  }
                  className="h-8 text-xs bg-slate-950 border-slate-800"
                >
                  <option value="TUITION">Tuition Fee</option>
                  <option value="EXAMINATION">Examination Fee</option>
                  <option value="LABORATORY">Laboratory Fee</option>
                  <option value="LIBRARY">Library Fee</option>
                  <option value="HOSTEL">Hostel & Mess</option>
                  <option value="TRANSPORT">Transport</option>
                  <option value="DEVELOPMENT">Campus Development</option>
                  <option value="SPORTS">Sports & Recreation</option>
                  <option value="OTHER">Other Institutional</option>
                </Select>
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Category Title <span className="text-rose-400">*</span>
              </label>
              <Input
                required
                placeholder="e.g. Academic Tuition Fee"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                className="h-8 text-xs bg-slate-950 border-slate-800"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Description & Statutory Notes
              </label>
              <Textarea
                placeholder="Explain fee head allocation and statutory applicability..."
                value={formDescription}
                onChange={(e) => setFormDescription(e.target.value)}
                rows={2}
                className="text-xs bg-slate-950 border-slate-800"
              />
            </div>

            <div className="flex items-center gap-6 pt-1">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formIsRefundable}
                  onChange={(e) => setFormIsRefundable(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-950 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="text-xs text-slate-300 font-medium">
                  Refundable on exit
                </span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formIsTaxable}
                  onChange={(e) => setFormIsTaxable(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-950 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="text-xs text-slate-300 font-medium">
                  Subject to GST / Tax
                </span>
              </label>
            </div>

            <DialogFooter className="pt-4 border-t border-slate-800">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setModalOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                disabled={saving}
              >
                {saving
                  ? "Saving..."
                  : editingCategory
                    ? "Update Category"
                    : "Create Category"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
