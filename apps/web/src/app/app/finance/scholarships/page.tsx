"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type { ConcessionType, StudentFeeConcession } from "@campusos/types";

interface StudentItem {
  id: string;
  first_name: string;
  last_name: string;
  admission_number: string;
}

interface AcademicYearItem {
  id: string;
  name: string;
}

export default function ScholarshipsPage() {
  const { hasPermission } = useAuth();
  const [scholarships, setScholarships] = useState<StudentFeeConcession[]>([]);
  const [students, setStudents] = useState<StudentItem[]>([]);
  const [academicYears, setAcademicYears] = useState<AcademicYearItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Form Fields
  const [studentId, setStudentId] = useState("");
  const [academicYearId, setAcademicYearId] = useState("");
  const [concessionName, setConcessionName] = useState("");
  const [concessionType, setConcessionType] = useState<ConcessionType>("MERIT");
  const [amount, setAmount] = useState<number | string>("");
  const [remarks, setRemarks] = useState("");

  const canCreate = hasPermission("scholarships:create");
  const canApprove = hasPermission("scholarships:approve");

  async function loadData() {
    try {
      setLoading(true);
      setError(null);
      const [scholRes, stuRes, ayRes] = await Promise.all([
        apiFetch<StudentFeeConcession[]>("/api/v1/finance/scholarships?limit=100"),
        apiFetch<StudentItem[]>("/api/v1/students?limit=200").catch(() => ({ data: [] })),
        apiFetch<AcademicYearItem[]>("/api/v1/academic-years").catch(() => ({ data: [] })),
      ]);

      setScholarships(scholRes.data);
      setStudents(stuRes.data || []);
      setAcademicYears(ayRes.data || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load scholarships.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateConcession = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      setFormError(null);

      const amountNum = Number(amount);
      if (!studentId) throw new Error("Please select a student.");
      if (!academicYearId) throw new Error("Please select an academic year.");
      if (!concessionName.trim()) throw new Error("Concession title/name is required.");
      if (isNaN(amountNum) || amountNum <= 0) throw new Error("Amount must be greater than zero.");

      await apiFetch("/api/v1/finance/scholarships", {
        method: "POST",
        body: JSON.stringify({
          student_id: studentId,
          academic_year_id: academicYearId,
          concession_name: concessionName.trim(),
          concession_type: concessionType,
          amount: amountNum,
          remarks: remarks.trim() || undefined,
        }),
      });

      setShowModal(false);
      setStudentId("");
      setConcessionName("");
      setAmount("");
      setRemarks("");
      await loadData();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to award scholarship.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleApprove = async (id: string) => {
    try {
      await apiFetch(`/api/v1/finance/scholarships/${id}/approve`, { method: "POST" });
      await loadData();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to approve scholarship.");
    }
  };

  const formatCurrency = (amountVal: number | string | undefined) => {
    const num = typeof amountVal === "string" ? parseFloat(amountVal) : (amountVal ?? 0);
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(num);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 mb-1">
            <Link href="/app/finance" className="hover:text-emerald-600 transition">
              Finance Hub
            </Link>
            <span>/</span>
            <span className="font-semibold text-slate-700 dark:text-slate-300">Scholarships & Concessions</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Scholarships, Fee Concessions & Waivers
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Manage institutional merit grants, need-based tuition waivers, and sibling concessions with audit control.
          </p>
        </div>

        {canCreate && (
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center justify-center rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white shadow-xs hover:bg-emerald-700 transition"
          >
            + Award Scholarship
          </button>
        )}
      </div>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/50 dark:bg-rose-950/40 dark:text-rose-300">
          <p className="font-semibold">Unable to load Scholarships</p>
          <p className="mt-0.5">{error}</p>
        </div>
      )}

      {/* Table */}
      {loading ? (
        <div className="text-center py-16 text-slate-500">Loading scholarships ledger...</div>
      ) : scholarships.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 p-12 text-center dark:border-slate-800">
          <p className="text-sm font-medium text-slate-900 dark:text-white">No scholarships or fee waivers awarded.</p>
          <p className="mt-1 text-xs text-slate-500">Awarded concessions automatically deduct from generated student invoices.</p>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-700 dark:text-slate-300">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500 border-b border-slate-200 dark:bg-slate-800/50 dark:border-slate-800">
                <tr>
                  <th className="px-4 py-3">Concession Title</th>
                  <th className="px-4 py-3">Student</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Amount</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Remarks</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {scholarships.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition">
                    <td className="px-4 py-3 font-semibold text-slate-900 dark:text-white">{s.concession_name}</td>
                    <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">
                      {s.student_name || "Enrolled Student"}
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 dark:bg-slate-800">
                        {s.concession_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-bold text-emerald-600 dark:text-emerald-400">
                      {formatCurrency(s.amount)}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                          s.status === "APPROVED"
                            ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                            : "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300"
                        }`}
                      >
                        {s.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">{s.remarks || "—"}</td>
                    <td className="px-4 py-3 text-right">
                      {s.status === "PENDING" && canApprove && (
                        <button
                          onClick={() => handleApprove(s.id)}
                          className="text-xs font-semibold text-emerald-600 hover:text-emerald-700"
                        >
                          Approve
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Award Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs overflow-y-auto">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900 border border-slate-200 dark:border-slate-800 my-8">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">Award Scholarship / Concession</h3>
              <button
                onClick={() => setShowModal(false)}
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

            <form onSubmit={handleCreateConcession} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                  Target Student *
                </label>
                <select
                  required
                  value={studentId}
                  onChange={(e) => setStudentId(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                >
                  <option value="">Select Student</option>
                  {students.map((stu) => (
                    <option key={stu.id} value={stu.id}>
                      {stu.first_name} {stu.last_name} ({stu.admission_number})
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
                  className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
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
                  Concession / Grant Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Dean's Merit Scholarship or Sibling Discount"
                  value={concessionName}
                  onChange={(e) => setConcessionName(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                    Concession Type *
                  </label>
                  <select
                    value={concessionType}
                    onChange={(e) => setConcessionType(e.target.value as ConcessionType)}
                    className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                  >
                    <option value="MERIT">MERIT</option>
                    <option value="NEED_BASED">NEED_BASED</option>
                    <option value="SIBLING">SIBLING</option>
                    <option value="STAFF_WARD">STAFF_WARD</option>
                    <option value="SPORTS">SPORTS</option>
                    <option value="SPECIAL">SPECIAL</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                    Benefit Amount (₹) *
                  </label>
                  <input
                    type="number"
                    required
                    min="1"
                    placeholder="e.g. 25000"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                  Justification / Remarks
                </label>
                <input
                  type="text"
                  placeholder="e.g. Rank 1 in state entrance examination"
                  value={remarks}
                  onChange={(e) => setRemarks(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                />
              </div>

              <div className="mt-6 flex justify-end gap-3 border-t border-slate-100 pt-4 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-emerald-700 disabled:opacity-50"
                >
                  {submitting ? "Saving..." : "Award Concession"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
