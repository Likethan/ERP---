"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { attendanceService } from "@/services/attendance.service";
import { AttendancePolicy } from "@/types/attendance";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { useToast } from "@/components/ui/toast";
import {
  Sliders,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  Clock,
  Plus,
  ArrowLeft,
  FileCheck2,
  Save,
} from "lucide-react";

export default function AttendancePoliciesPage() {
  const { hasPermission } = useAuth();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [policies, setPolicies] = useState<AttendancePolicy[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);

  const [formData, setFormData] = useState({
    name: "New Departmental Regulation Policy",
    departmentId: "dept-cse",
    departmentName: "Computer Science & Engineering",
    academicYear: "2026-2027",
    minimumPercentage: 75,
    warningThreshold: 80,
    criticalThreshold: 65,
    includeExcusedInTotal: true,
    lateArrivalWeight: 0.5,
    requireApprovalForCorrections: true,
    maxLeaveDaysConsecutive: 5,
    status: "ACTIVE" as const,
  });

  const loadPolicies = async () => {
    try {
      setLoading(true);
      const res = await attendanceService.getPolicies();
      if (res.success) {
        setPolicies(res.data);
      }
    } catch (err) {
      console.error("Failed to load policies", err);
      showToast({
        type: "error",
        title: "Load Error",
        message: "Failed to load attendance policies.",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPolicies();
  }, []);

  const handleCreatePolicy = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      const res = await attendanceService.createPolicy(formData);
      if (res.success) {
        showToast({
          type: "success",
          title: "Policy Created",
          message: `Policy "${res.data.name}" configured and active.`,
        });
        setModalOpen(false);
        await loadPolicies();
      }
    } catch (err) {
      console.error("Failed to create policy", err);
      showToast({
        type: "error",
        title: "Creation Failed",
        message: "Could not create policy.",
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5 dark:border-slate-800">
        <div className="flex items-center gap-3">
          <Link href="/app/attendance">
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300">
                Regulations Engine
              </span>
              <span className="text-xs text-slate-500 dark:text-slate-400">
                Institutional Governance
              </span>
            </div>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Attendance Rules & Policies
            </h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Configure minimum attendance thresholds, late penalty weighting,
              medical excuse inclusions, and condonation rules.
            </p>
          </div>
        </div>

        <Button
          variant="primary"
          className="gap-2"
          onClick={() => setModalOpen(true)}
        >
          <Plus className="h-4 w-4" />
          Add Policy Scheme
        </Button>
      </div>

      {/* Policy Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {policies.map((policy) => (
          <div
            key={policy.id}
            className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs flex flex-col justify-between dark:border-slate-800 dark:bg-slate-900"
          >
            <div>
              <div className="flex items-start justify-between gap-2">
                <div>
                  <Badge
                    variant={
                      policy.status === "ACTIVE" ? "success" : "secondary"
                    }
                  >
                    {policy.status}
                  </Badge>
                  <h3 className="mt-2 text-base font-semibold text-slate-900 dark:text-white">
                    {policy.name}
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {policy.departmentName} • AY {policy.academicYear}
                  </p>
                </div>
              </div>

              {/* Threshold Indicators */}
              <div className="mt-4 grid grid-cols-3 gap-2 text-center">
                <div className="rounded-lg bg-emerald-50 p-2 dark:bg-emerald-950/40">
                  <div className="text-lg font-bold text-emerald-700 dark:text-emerald-300">
                    {policy.minimumPercentage}%
                  </div>
                  <div className="text-[10px] text-emerald-600 font-medium">
                    Min Required
                  </div>
                </div>

                <div className="rounded-lg bg-amber-50 p-2 dark:bg-amber-950/40">
                  <div className="text-lg font-bold text-amber-700 dark:text-amber-300">
                    {policy.warningThreshold}%
                  </div>
                  <div className="text-[10px] text-amber-600 font-medium">
                    Warning Threshold
                  </div>
                </div>

                <div className="rounded-lg bg-rose-50 p-2 dark:bg-rose-950/40">
                  <div className="text-lg font-bold text-rose-700 dark:text-rose-300">
                    {policy.criticalThreshold}%
                  </div>
                  <div className="text-[10px] text-rose-600 font-medium">
                    Critical Debar
                  </div>
                </div>
              </div>

              {/* Feature Checklist */}
              <div className="mt-4 space-y-2 text-xs border-t border-slate-100 pt-3 dark:border-slate-800">
                <div className="flex items-center justify-between text-slate-600 dark:text-slate-300">
                  <span>Late Arrival Weight</span>
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {policy.lateArrivalWeight === 1
                      ? "1.0x (Full)"
                      : policy.lateArrivalWeight === 0.5
                        ? "0.5x (Half Present)"
                        : "0.0x (Absent)"}
                  </span>
                </div>
                <div className="flex items-center justify-between text-slate-600 dark:text-slate-300">
                  <span>Include Approved Excused</span>
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {policy.includeExcusedInTotal
                      ? "Yes (Counted Present)"
                      : "No"}
                  </span>
                </div>
                <div className="flex items-center justify-between text-slate-600 dark:text-slate-300">
                  <span>Correction HOD Sign-off</span>
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {policy.requireApprovalForCorrections
                      ? "Mandatory"
                      : "Direct"}
                  </span>
                </div>
                <div className="flex items-center justify-between text-slate-600 dark:text-slate-300">
                  <span>Max Consecutive Leave</span>
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {policy.maxLeaveDaysConsecutive} Days
                  </span>
                </div>
              </div>
            </div>

            <div className="mt-5 pt-3 border-t border-slate-100 dark:border-slate-800 flex justify-end">
              <Button size="sm" variant="outline" className="text-xs">
                Configure Thresholds
              </Button>
            </div>
          </div>
        ))}
      </div>

      {/* Add Policy Modal */}
      <Dialog
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Configure New Attendance Policy"
      >
        <form onSubmit={handleCreatePolicy} className="space-y-4 text-xs">
          <p className="text-slate-500">
            Define compliance thresholds and penalty weighting for university
            degree conferral eligibility.
          </p>

          <div>
            <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
              Policy Scheme Name
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
              className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Department
              </label>
              <select
                value={formData.departmentName}
                onChange={(e) =>
                  setFormData({ ...formData, departmentName: e.target.value })
                }
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              >
                <option value="Computer Science & Engineering">
                  Computer Science & Engineering
                </option>
                <option value="Electronics & Communication Engineering">
                  Electronics & Communication
                </option>
                <option value="Mechanical Engineering">
                  Mechanical Engineering
                </option>
                <option value="All Departments">
                  All Departments (Institutional)
                </option>
              </select>
            </div>

            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Academic Year
              </label>
              <input
                type="text"
                value={formData.academicYear}
                onChange={(e) =>
                  setFormData({ ...formData, academicYear: e.target.value })
                }
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Min Required (%)
              </label>
              <input
                type="number"
                min="50"
                max="100"
                value={formData.minimumPercentage}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    minimumPercentage: Number(e.target.value),
                  })
                }
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>

            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Warning (%)
              </label>
              <input
                type="number"
                min="50"
                max="100"
                value={formData.warningThreshold}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    warningThreshold: Number(e.target.value),
                  })
                }
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>

            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Critical Shortage (%)
              </label>
              <input
                type="number"
                min="40"
                max="100"
                value={formData.criticalThreshold}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    criticalThreshold: Number(e.target.value),
                  })
                }
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Late Arrival Weight
              </label>
              <select
                value={formData.lateArrivalWeight}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    lateArrivalWeight: Number(e.target.value),
                  })
                }
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              >
                <option value={0.5}>0.5x — Half Attendance</option>
                <option value={1.0}>1.0x — Full Attendance</option>
                <option value={0.0}>0.0x — Marked Absent</option>
              </select>
            </div>

            <div>
              <label className="block font-medium text-slate-700 dark:text-slate-300 mb-1">
                Max Consecutive Leaves
              </label>
              <input
                type="number"
                min="1"
                max="30"
                value={formData.maxLeaveDaysConsecutive}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    maxLeaveDaysConsecutive: Number(e.target.value),
                  })
                }
                className="w-full rounded-lg border border-slate-300 bg-white p-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
              />
            </div>
          </div>

          <div className="flex items-center gap-2 pt-2">
            <input
              type="checkbox"
              id="includeExcused"
              checked={formData.includeExcusedInTotal}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  includeExcusedInTotal: e.target.checked,
                })
              }
              className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
            />
            <label
              htmlFor="includeExcused"
              className="text-slate-700 dark:text-slate-300 font-medium"
            >
              Count approved Medical / On-Duty leaves as Present in percentage
              calculations
            </label>
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              onClick={() => setModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={saving}>
              {saving ? "Saving..." : "Save Policy"}
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
