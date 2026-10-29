"use client";

import { useEffect, useState } from "react";
import {
  FileCheck2,
  Plus,
  Clock,
  Download,
  X,
  Banknote,
  ShieldCheck,
  CheckCircle2,
} from "lucide-react";
import { HousingNav } from "@/components/housing/housing-nav";
import { HousingService } from "@/services/housing.service";
import {
  HousingAgreementCreateInput,
  HousingAgreementReference,
  HousingAssignment,
} from "@/types/housing";

export default function HousingAgreementsPage() {
  const [agreements, setAgreements] = useState<HousingAgreementReference[]>([]);
  const [assignments, setAssignments] = useState<HousingAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const [formData, setFormData] = useState<HousingAgreementCreateInput>({
    assignment_id: "",
    agreement_title: "CampusOS Standard Residential Tenancy Lease 2026-27",
    valid_from: new Date().toISOString().split("T")[0],
    valid_to: new Date(Date.now() + 365 * 24 * 3600 * 1000).toISOString().split("T")[0],
    rent_amount: 8500,
    deposit_amount: 15000,
    payment_frequency: "MONTHLY_ADVANCE",
    finance_invoice_reference: `INV-${new Date().getFullYear()}-${Math.floor(1000 + Math.random() * 9000)}`,
    deposit_invoice_reference: `DEP-${new Date().getFullYear()}-${Math.floor(1000 + Math.random() * 9000)}`,
  });

  const loadData = async () => {
    try {
      const [allAgreements, allAssignments] = await Promise.all([
        HousingService.listAgreements(),
        HousingService.listAssignments(),
      ]);
      setAgreements(allAgreements);
      setAssignments(allAssignments);
      if (allAssignments.length > 0) {
        setFormData((prev) => ({
          ...prev,
          assignment_id: allAssignments[0].id,
        }));
      }
    } catch (err) {
      console.error("Failed to load agreements", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      await HousingService.createAgreement(formData);
      setIsModalOpen(false);
      loadData();
    } catch (err) {
      alert("Failed to record agreement: " + (err as Error).message);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <HousingNav />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <FileCheck2 className="w-7 h-7 text-indigo-400" />
              Residential Tenancy Agreements & Finance References
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Legally binding digital leases, ERP invoice linkages, and security deposit escrow reconciliation.
            </p>
          </div>

          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            Generate Tenancy Agreement
          </button>
        </div>

        {/* Agreements Table */}
        {loading ? (
          <div className="py-20 text-center text-slate-400">Loading digital lease records...</div>
        ) : agreements.length === 0 ? (
          <div className="py-16 text-center border border-dashed border-slate-800 rounded-xl bg-slate-900/30">
            <p className="text-slate-400">No active housing tenancy agreements registered yet.</p>
          </div>
        ) : (
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-950/80 border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <tr>
                    <th className="px-5 py-3">Agreement Ref / Title</th>
                    <th className="px-5 py-3">Term Dates</th>
                    <th className="px-5 py-3">Rent & Deposit</th>
                    <th className="px-5 py-3">Signature Status</th>
                    <th className="px-5 py-3">Deposit Escrow</th>
                    <th className="px-5 py-3 text-right">Invoices</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {agreements.map((agr) => (
                    <tr key={agr.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-5 py-4">
                        <div className="font-mono font-bold text-white text-xs">
                          {agr.agreement_number}
                        </div>
                        <div className="text-xs text-slate-300 mt-0.5">
                          {agr.agreement_title}
                        </div>
                        {agr.finance_invoice_reference && (
                          <div className="text-[11px] font-mono text-indigo-400">
                            Inv: {agr.finance_invoice_reference}
                          </div>
                        )}
                      </td>
                      <td className="px-5 py-4">
                        <div className="text-xs text-slate-300">
                          {agr.valid_from} to {agr.valid_to}
                        </div>
                        <div className="text-[11px] text-slate-500">
                          {agr.payment_frequency}
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <div className="text-xs font-medium text-emerald-400">
                          ₹{agr.rent_amount.toLocaleString("en-IN")}/mo
                        </div>
                        <div className="text-[11px] text-slate-400">
                          Deposit: ₹{agr.deposit_amount.toLocaleString("en-IN")}
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        {agr.student_signed_at ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            Digitally Signed
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                            <Clock className="w-3.5 h-3.5" />
                            Pending Sign
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-4">
                        <span
                          className={`text-xs px-2 py-0.5 rounded font-mono font-medium ${
                            agr.deposit_refund_status === "HELD"
                              ? "bg-slate-800 text-slate-300"
                              : agr.deposit_refund_status === "REFUNDED"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                              : "bg-rose-500/10 text-rose-400 border border-rose-500/30"
                          }`}
                        >
                          {agr.deposit_refund_status}
                        </span>
                      </td>
                      <td className="px-5 py-4 text-right">
                        {agr.deposit_invoice_reference && (
                          <span className="font-mono text-xs text-slate-300 block">
                            {agr.deposit_invoice_reference}
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Modal: New Agreement */}
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
            <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto shadow-2xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-indigo-400" />
                  Generate Tenancy Agreement Reference
                </h3>
                <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-white">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleCreate} className="space-y-4 text-sm">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Select Resident Assignment *
                  </label>
                  <select
                    required
                    value={formData.assignment_id}
                    onChange={(e) => setFormData({ ...formData, assignment_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                  >
                    {assignments.map((asg) => (
                      <option key={asg.id} value={asg.id}>
                        {asg.student_name} — Bed {asg.bed_code} ({asg.property_name})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Agreement Title *
                  </label>
                  <input
                    required
                    type="text"
                    value={formData.agreement_title}
                    onChange={(e) =>
                      setFormData({ ...formData, agreement_title: e.target.value })
                    }
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Lease Valid From *
                    </label>
                    <input
                      required
                      type="date"
                      value={formData.valid_from}
                      onChange={(e) => setFormData({ ...formData, valid_from: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Lease Valid To *
                    </label>
                    <input
                      required
                      type="date"
                      value={formData.valid_to}
                      onChange={(e) => setFormData({ ...formData, valid_to: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Monthly Rent (₹) *
                    </label>
                    <input
                      required
                      type="number"
                      value={formData.rent_amount}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          rent_amount: parseFloat(e.target.value) || 0,
                        })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Security Deposit Escrow (₹) *
                    </label>
                    <input
                      required
                      type="number"
                      value={formData.deposit_amount}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          deposit_amount: parseFloat(e.target.value) || 0,
                        })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Payment Frequency
                    </label>
                    <select
                      value={formData.payment_frequency || "MONTHLY_ADVANCE"}
                      onChange={(e) =>
                        setFormData({ ...formData, payment_frequency: e.target.value })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    >
                      <option value="MONTHLY_ADVANCE">Monthly in Advance</option>
                      <option value="SEMESTER_UPFRONT">Semester Upfront</option>
                      <option value="ANNUAL_ONE_TIME">Annual Lump-sum</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Finance Invoice Ref
                    </label>
                    <input
                      type="text"
                      value={formData.finance_invoice_reference || ""}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          finance_invoice_reference: e.target.value,
                        })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200 font-mono"
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="px-4 py-2 text-xs font-medium rounded-md bg-slate-800 text-slate-300 hover:bg-slate-700"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={actionLoading}
                    className="px-4 py-2 text-xs font-medium rounded-md bg-indigo-600 hover:bg-indigo-500 text-white"
                  >
                    Register Agreement
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
