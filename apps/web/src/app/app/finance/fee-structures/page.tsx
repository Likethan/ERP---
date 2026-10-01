"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { financeService } from "@/services/finance.service";
import type { FeeCategory, FeeStructure, FeeStructureStatus } from "@campusos/types";

interface ProgramItem {
  id: string;
  name: string;
  code: string;
}

interface AcademicYearItem {
  id: string;
  name: string;
}

interface SemesterItem {
  id: string;
  name: string;
}

export default function FeeStructuresPage() {
  const { hasPermission } = useAuth();
  const [structures, setStructures] = useState<FeeStructure[]>([]);
  const [categories, setCategories] = useState<FeeCategory[]>([]);
  const [programs, setPrograms] = useState<ProgramItem[]>([]);
  const [academicYears, setAcademicYears] = useState<AcademicYearItem[]>([]);
  const [semesters, setSemesters] = useState<SemesterItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Form Fields
  const [name, setName] = useState("");
  const [programId, setProgramId] = useState("");
  const [academicYearId, setAcademicYearId] = useState("");
  const [semesterId, setSemesterId] = useState("");
  const [quotaType, setQuotaType] = useState("GENERAL");
  const [feeItems, setFeeItems] = useState<
    Array<{ category_id: string; name: string; amount: number; is_optional: boolean; sequence: number }>
  >([{ category_id: "", name: "Tuition Fee", amount: 50000, is_optional: false, sequence: 1 }]);

  const canManage = hasPermission("finance:manage_fee_structures");

  async function loadData() {
    try {
      setLoading(true);
      setError(null);
      const [structRes, catRes, progRes, ayRes, semRes] = await Promise.all([
        apiFetch<FeeStructure[]>("/api/v1/finance/fee-structures"),
        apiFetch<FeeCategory[]>("/api/v1/finance/fee-categories"),
        apiFetch<ProgramItem[]>("/api/v1/programs").catch(() => ({ data: [] })),
        apiFetch<AcademicYearItem[]>("/api/v1/academic-years").catch(() => ({ data: [] })),
        apiFetch<SemesterItem[]>("/api/v1/semesters").catch(() => ({ data: [] })),
      ]);

      setStructures(structRes.data);
      setCategories(catRes.data);
      setPrograms(progRes.data || []);
      setAcademicYears(ayRes.data || []);
      setSemesters(semRes.data || []);

      if (catRes.data.length > 0 && !feeItems[0].category_id) {
        setFeeItems([{ category_id: catRes.data[0].id, name: "Tuition Fee", amount: 50000, is_optional: false, sequence: 1 }]);
      }
    } catch {
      const mockRes = await financeService.getFeeStructures();
      const mapped = (mockRes.data || []).map((fs) => ({
        id: fs.id,
        name: fs.name,
        academic_year_id: "ay-2026-27",
        program_id: "prog-cse",
        quota_type: "GENERAL",
        status: fs.status as FeeStructureStatus,
        total_amount: fs.totalAnnualFee,
        program_name: fs.program,
        academic_year_name: fs.academicYear,
        items: [
          { id: "fsi-1", name: "Core Tuition Fee", amount: fs.totalAnnualFee * 0.7, is_optional: false, category_name: "Tuition" },
          { id: "fsi-2", name: "Advanced Computing Lab", amount: fs.totalAnnualFee * 0.2, is_optional: false, category_name: "Laboratory" },
          { id: "fsi-3", name: "Library & Digital Journals", amount: fs.totalAnnualFee * 0.1, is_optional: false, category_name: "Library" },
        ],
      } as unknown as FeeStructure));
      setStructures(mapped);
      setCategories([
        { id: "cat-1", name: "Tuition", code: "TUI" } as unknown as FeeCategory,
        { id: "cat-2", name: "Laboratory", code: "LAB" } as unknown as FeeCategory,
        { id: "cat-3", name: "Library", code: "LIB" } as unknown as FeeCategory,
      ]);
      setPrograms([
        { id: "prog-cse", name: "B.Tech Computer Science & Engineering", code: "BTECH_CSE" },
        { id: "prog-ece", name: "B.Tech Electronics & Communication", code: "BTECH_ECE" },
      ]);
      setAcademicYears([{ id: "ay-2026-27", name: "2026-2027" }]);
      setSemesters([
        { id: "sem-5", name: "Semester 5" },
        { id: "sem-6", name: "Semester 6" },
      ]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const handleAddItem = () => {
    setFeeItems([
      ...feeItems,
      {
        category_id: categories[0]?.id || "",
        name: "",
        amount: 0,
        is_optional: false,
        sequence: feeItems.length + 1,
      },
    ]);
  };

  const handleRemoveItem = (index: number) => {
    setFeeItems(feeItems.filter((_, i) => i !== index));
  };

  const handleItemChange = (index: number, field: string, value: unknown) => {
    const updated = [...feeItems];
    updated[index] = { ...updated[index], [field]: value };
    setFeeItems(updated);
  };

  const calculateTotal = () => {
    return feeItems.reduce((acc, curr) => acc + (Number(curr.amount) || 0), 0);
  };

  const handleCreateStructure = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      setFormError(null);

      if (!name.trim()) throw new Error("Fee structure name is required.");
      if (!programId) throw new Error("Please select a target program.");
      if (!academicYearId) throw new Error("Please select an academic year.");
      if (feeItems.length === 0) throw new Error("At least one fee head item is required.");

      for (const item of feeItems) {
        if (!item.category_id) throw new Error("Every line item must have a category.");
        if (!item.name.trim()) throw new Error("Every line item must have a description/name.");
        if (Number(item.amount) <= 0) throw new Error("Item amount must be greater than zero.");
      }

      await apiFetch("/api/v1/finance/fee-structures", {
        method: "POST",
        body: JSON.stringify({
          name: name.trim(),
          program_id: programId,
          academic_year_id: academicYearId,
          semester_id: semesterId || undefined,
          quota_type: quotaType,
          items: feeItems.map((item, idx) => ({
            category_id: item.category_id,
            name: item.name.trim(),
            amount: Number(item.amount),
            is_optional: item.is_optional,
            sequence: idx + 1,
          })),
        }),
      });

      setShowCreateModal(false);
      setName("");
      await loadData();
    } catch {
      await financeService.createFeeStructure({
        name: name.trim(),
        totalAnnualFee: calculateTotal(),
      });
      setShowCreateModal(false);
      setName("");
      await loadData();
    } finally {
      setSubmitting(false);
    }
  };

  const handleStatusTransition = async (structureId: string, action: "approve" | "activate" | "retire") => {
    try {
      await apiFetch(`/api/v1/finance/fee-structures/${structureId}/${action}`, {
        method: "POST",
      });
      await loadData();
    } catch {
      const targetStatus: FeeStructureStatus =
        action === "approve" ? "APPROVED" : action === "activate" ? "ACTIVE" : "RETIRED";
      setStructures((prev) =>
        prev.map((s) => (s.id === structureId ? { ...s, status: targetStatus } : s))
      );
    }
  };

  const formatCurrency = (amount: number | string | undefined) => {
    const num = typeof amount === "string" ? parseFloat(amount) : (amount ?? 0);
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(num);
  };

  const getStatusBadge = (status: FeeStructureStatus | string) => {
    switch (status) {
      case "ACTIVE":
        return "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300";
      case "APPROVED":
        return "bg-sky-100 text-sky-800 dark:bg-sky-950/60 dark:text-sky-300";
      case "RETIRED":
        return "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300";
      default:
        return "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300";
    }
  };

  return (
    <div className="space-y-8">
      {/* Breadcrumb & Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 mb-1">
            <Link href="/app/finance" className="hover:text-emerald-600 transition">
              Finance Hub
            </Link>
            <span>/</span>
            <span className="font-semibold text-slate-700 dark:text-slate-300">Fee Structures</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Fee Structures Matrix & Versioning
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Define programmatic fee templates for academic terms, quotas, and tuition slabs.
          </p>
        </div>

        {canManage && (
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center justify-center rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white shadow-xs hover:bg-emerald-700 transition"
          >
            + Create Fee Structure
          </button>
        )}
      </div>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300">
          <p className="font-semibold">Unable to load Fee Structures</p>
          <p className="mt-0.5">{error}</p>
        </div>
      )}

      {/* Fee Structures Grid */}
      {loading ? (
        <div className="text-center py-16 text-slate-500">Loading fee structures...</div>
      ) : structures.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 p-12 text-center dark:border-slate-800">
          <p className="text-sm font-medium text-slate-900 dark:text-white">No fee structures configured.</p>
          <p className="mt-1 text-xs text-slate-500">Create your first fee structure to start assigning student billing obligations.</p>
          {canManage && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-4 inline-flex items-center justify-center rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-emerald-700"
            >
              + Create Template
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {structures.map((s) => (
            <div
              key={s.id}
              className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs flex flex-col justify-between dark:border-slate-800 dark:bg-slate-900"
            >
              <div>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${getStatusBadge(
                        s.status
                      )}`}
                    >
                      {s.status} (v{s.version})
                    </span>
                    <h2 className="mt-2 text-lg font-bold text-slate-900 dark:text-white">{s.name}</h2>
                    <p className="text-xs text-slate-500">
                      Quota: <span className="font-medium text-slate-700 dark:text-slate-300">{s.quota_type}</span>
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-slate-400">Total Fee</span>
                    <div className="text-xl font-bold text-emerald-600 dark:text-emerald-400">
                      {formatCurrency(s.total_amount)}
                    </div>
                  </div>
                </div>

                {/* Line Items Breakdown */}
                <div className="mt-5 border-t border-slate-100 pt-4 dark:border-slate-800">
                  <h4 className="text-xs font-semibold uppercase text-slate-400 tracking-wider mb-2">Itemized Heads</h4>
                  <div className="space-y-1.5 text-xs text-slate-600 dark:text-slate-300">
                    {s.items?.map((item) => (
                      <div key={item.id} className="flex justify-between py-1 border-b border-slate-50 dark:border-slate-800/50">
                        <span>
                          {item.name} {item.is_optional && <span className="text-slate-400">(Optional)</span>}
                        </span>
                        <span className="font-mono font-medium">{formatCurrency(item.amount)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              {canManage && (
                <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-end gap-2 dark:border-slate-800">
                  {s.status === "DRAFT" && (
                    <button
                      onClick={() => handleStatusTransition(s.id, "approve")}
                      className="px-3 py-1.5 text-xs font-medium bg-sky-50 text-sky-700 rounded-lg hover:bg-sky-100 transition dark:bg-sky-950/60 dark:text-sky-300"
                    >
                      Approve
                    </button>
                  )}
                  {s.status === "APPROVED" && (
                    <button
                      onClick={() => handleStatusTransition(s.id, "activate")}
                      className="px-3 py-1.5 text-xs font-medium bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition"
                    >
                      Activate for Billing
                    </button>
                  )}
                  {s.status === "ACTIVE" && (
                    <button
                      onClick={() => handleStatusTransition(s.id, "retire")}
                      className="px-3 py-1.5 text-xs font-medium bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition dark:bg-slate-800 dark:text-slate-300"
                    >
                      Retire Version
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Create Fee Structure Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs overflow-y-auto">
          <div className="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900 border border-slate-200 dark:border-slate-800 my-8">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">Create Fee Structure Template</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-600 text-xl font-bold"
              >
                ×
              </button>
            </div>

            {formError && (
              <div className="mt-4 rounded-lg bg-rose-50 p-3 text-xs text-rose-700 dark:bg-rose-950/50 dark:text-rose-300">
                {formError}
              </div>
            )}

            <form onSubmit={handleCreateStructure} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                  Template Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. B.Tech Computer Science 2026-27 Regular"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                    Program *
                  </label>
                  <select
                    required
                    value={programId}
                    onChange={(e) => setProgramId(e.target.value)}
                    className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  >
                    <option value="">Select Program</option>
                    {programs.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.code})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                    Academic Year *
                  </label>
                  <select
                    required
                    value={academicYearId}
                    onChange={(e) => setAcademicYearId(e.target.value)}
                    className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  >
                    <option value="">Select Year</option>
                    {academicYears.map((ay) => (
                      <option key={ay.id} value={ay.id}>
                        {ay.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                    Semester (Optional)
                  </label>
                  <select
                    value={semesterId}
                    onChange={(e) => setSemesterId(e.target.value)}
                    className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  >
                    <option value="">All Semesters</option>
                    {semesters.map((sem) => (
                      <option key={sem.id} value={sem.id}>
                        {sem.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                    Quota Type
                  </label>
                  <select
                    value={quotaType}
                    onChange={(e) => setQuotaType(e.target.value)}
                    className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  >
                    <option value="GENERAL">GENERAL</option>
                    <option value="MANAGEMENT">MANAGEMENT</option>
                    <option value="GOVERNMENT">GOVERNMENT</option>
                    <option value="NRI">NRI</option>
                    <option value="MERIT">MERIT</option>
                  </select>
                </div>
              </div>

              {/* Fee Heads Array */}
              <div className="border-t border-slate-100 pt-4 dark:border-slate-800">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold uppercase text-slate-500 tracking-wider">
                    Fee Line Items
                  </span>
                  <button
                    type="button"
                    onClick={handleAddItem}
                    className="text-xs font-semibold text-emerald-600 hover:text-emerald-700 dark:text-emerald-400"
                  >
                    + Add Head
                  </button>
                </div>

                <div className="space-y-3 max-h-60 overflow-y-auto pr-1">
                  {feeItems.map((item, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-sm">
                      <select
                        value={item.category_id}
                        onChange={(e) => handleItemChange(idx, "category_id", e.target.value)}
                        className="w-1/3 rounded-lg border border-slate-300 px-2 py-1.5 text-xs text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                      >
                        {categories.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.name}
                          </option>
                        ))}
                      </select>

                      <input
                        type="text"
                        placeholder="Description (e.g. Tuition)"
                        value={item.name}
                        onChange={(e) => handleItemChange(idx, "name", e.target.value)}
                        className="flex-1 rounded-lg border border-slate-300 px-2 py-1.5 text-xs text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                      />

                      <input
                        type="number"
                        placeholder="Amount"
                        value={item.amount}
                        onChange={(e) => handleItemChange(idx, "amount", e.target.value)}
                        className="w-24 rounded-lg border border-slate-300 px-2 py-1.5 text-xs text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white font-mono"
                      />

                      {feeItems.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleRemoveItem(idx)}
                          className="text-slate-400 hover:text-rose-500 px-1 text-base"
                        >
                          ×
                        </button>
                      )}
                    </div>
                  ))}
                </div>

                <div className="mt-4 flex items-center justify-between font-bold text-sm bg-slate-50 p-3 rounded-lg dark:bg-slate-800">
                  <span>Total Calculated Amount</span>
                  <span className="text-emerald-600 dark:text-emerald-400">{formatCurrency(calculateTotal())}</span>
                </div>
              </div>

              {/* Submit Actions */}
              <div className="mt-6 flex justify-end gap-3 border-t border-slate-100 pt-4 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-emerald-700 disabled:opacity-50"
                >
                  {submitting ? "Saving..." : "Save Draft Structure"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
