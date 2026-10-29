"use client";

import React, { useState } from "react";
import { SportsNav } from "@/components/sports/sports-nav";
import {
  CreditCard,
  DollarSign,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  ShieldCheck,
  FileText,
  Percent,
} from "lucide-react";

interface FeeRecord {
  id: string;
  participant_name: string;
  activity_title: string;
  activity_type: "tournament_entry" | "training_camp" | "facility_booking" | "equipment_damage";
  amount: number;
  invoice_reference: string;
  status: "paid" | "pending" | "waived";
  date: string;
  waiver_reason?: string;
}

const INITIAL_FEES: FeeRecord[] = [
  {
    id: "fee-01",
    participant_name: "Rahul Verma",
    activity_title: "South Zone Inter-University Tournament Entry",
    activity_type: "tournament_entry",
    amount: 1500,
    invoice_reference: "INV-SP-2026-0081",
    status: "paid",
    date: "2026-10-12",
  },
  {
    id: "fee-02",
    participant_name: "Ananya Iyer",
    activity_title: "Varsity Badminton High Performance Academy",
    activity_type: "training_camp",
    amount: 3500,
    invoice_reference: "INV-SP-2026-0092",
    status: "paid",
    date: "2026-10-15",
  },
  {
    id: "fee-03",
    participant_name: "Karan Patel",
    activity_title: "Campus Badminton Open 2026 Entry",
    activity_type: "tournament_entry",
    amount: 500,
    invoice_reference: "INV-SP-2026-0104",
    status: "pending",
    date: "2026-10-20",
  },
  {
    id: "fee-04",
    participant_name: "Sneha Reddy",
    activity_title: "Sprint Mechanics Clinic",
    activity_type: "training_camp",
    amount: 2000,
    invoice_reference: "INV-SP-2026-0115",
    status: "waived",
    date: "2026-10-18",
    waiver_reason: "Merit Athletic Scholarship (Chancellor Sports Fellowship)",
  },
  {
    id: "fee-05",
    participant_name: "Vikram Malhotra",
    activity_title: "Tennis Court Floodlight Surcharge",
    activity_type: "facility_booking",
    amount: 400,
    invoice_reference: "INV-SP-2026-0128",
    status: "paid",
    date: "2026-10-22",
  },
];

export default function SportsFeesPage() {
  const [fees, setFees] = useState<FeeRecord[]>(INITIAL_FEES);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [selectedFee, setSelectedFee] = useState<FeeRecord | null>(null);
  const [waiverReason, setWaiverReason] = useState("");
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const totalBilled = fees.reduce((sum, f) => sum + f.amount, 0);
  const totalPaid = fees.filter((f) => f.status === "paid").reduce((sum, f) => sum + f.amount, 0);
  const totalWaived = fees.filter((f) => f.status === "waived").reduce((sum, f) => sum + f.amount, 0);
  const totalPending = fees.filter((f) => f.status === "pending").reduce((sum, f) => sum + f.amount, 0);

  const handleApplyWaiver = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFee || !waiverReason.trim()) return;

    setFees((prev) =>
      prev.map((f) =>
        f.id === selectedFee.id
          ? { ...f, status: "waived", waiver_reason: waiverReason }
          : f
      )
    );

    setActionSuccess(`Athletic fee waiver granted for ${selectedFee.participant_name}.`);
    setSelectedFee(null);
    setWaiverReason("");
  };

  const filtered = fees.filter((f) => {
    const matchesSearch =
      f.participant_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.activity_title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.invoice_reference.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || f.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      <SportsNav />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Sports Registrations & Financial Operations
          </h1>
          <p className="text-sm text-slate-500">
            Authoritative invoice linkages, competition entry reconciliations, and athletic waivers.
          </p>
        </div>
      </div>

      {actionSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center justify-between text-emerald-800 text-sm">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>{actionSuccess}</span>
          </div>
          <button onClick={() => setActionSuccess(null)} className="text-emerald-700 font-bold hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Financial Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs text-slate-500 font-medium">Total Billed</p>
          <p className="text-2xl font-bold text-slate-900 mt-1">₹{totalBilled.toLocaleString()}</p>
          <p className="text-[11px] text-slate-400 mt-1">All athletic entries</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs text-slate-500 font-medium">Reconciled / Paid</p>
          <p className="text-2xl font-bold text-emerald-600 mt-1">₹{totalPaid.toLocaleString()}</p>
          <p className="text-[11px] text-emerald-700 mt-1">
            {Math.round((totalPaid / totalBilled) * 100)}% collection rate
          </p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs text-slate-500 font-medium">Scholarships & Waivers</p>
          <p className="text-2xl font-bold text-indigo-600 mt-1">₹{totalWaived.toLocaleString()}</p>
          <p className="text-[11px] text-slate-400 mt-1">Approved fellowship grants</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs text-slate-500 font-medium">Outstanding Balance</p>
          <p className="text-2xl font-bold text-amber-600 mt-1">₹{totalPending.toLocaleString()}</p>
          <p className="text-[11px] text-amber-700 mt-1">Pending payments</p>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-wrap items-center gap-3 bg-white p-3 rounded-lg border border-slate-200">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by student name, invoice reference, or activity..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-sm border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="text-sm border border-slate-300 rounded-md px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
        >
          <option value="all">All Payment Statuses</option>
          <option value="paid">Paid & Reconciled</option>
          <option value="pending">Pending Payment</option>
          <option value="waived">Waived / Fellowship</option>
        </select>
      </div>

      {/* Ledger Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
              <tr>
                <th className="py-3 px-4">Invoice Ref</th>
                <th className="py-3 px-4">Athlete / Participant</th>
                <th className="py-3 px-4">Activity Description</th>
                <th className="py-3 px-4 text-right">Fee (₹)</th>
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filtered.map((item) => (
                <tr key={item.id} className="hover:bg-slate-50/60">
                  <td className="py-3 px-4 font-mono font-bold text-slate-900">{item.invoice_reference}</td>
                  <td className="py-3 px-4 font-medium text-slate-900">{item.participant_name}</td>
                  <td className="py-3 px-4">
                    <span className="text-slate-800">{item.activity_title}</span>
                    {item.waiver_reason && (
                      <p className="text-[11px] text-indigo-600 italic mt-0.5">{item.waiver_reason}</p>
                    )}
                  </td>
                  <td className="py-3 px-4 text-right font-mono font-bold text-slate-900">
                    ₹{item.amount.toLocaleString()}
                  </td>
                  <td className="py-3 px-4 text-slate-500">{item.date}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                        item.status === "paid"
                          ? "bg-emerald-100 text-emerald-800"
                          : item.status === "waived"
                          ? "bg-indigo-100 text-indigo-800"
                          : "bg-amber-100 text-amber-800"
                      }`}
                    >
                      {item.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    {item.status === "pending" ? (
                      <button
                        onClick={() => setSelectedFee(item)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 rounded hover:bg-indigo-100"
                      >
                        <Percent className="w-3.5 h-3.5" />
                        Grant Waiver
                      </button>
                    ) : (
                      <span className="text-slate-400 text-xs">Reconciled</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Grant Waiver */}
      {selectedFee && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl border border-slate-200 max-w-md w-full p-6 shadow-xl space-y-4">
            <div>
              <h2 className="text-lg font-bold text-slate-900">Authorize Athletic Fee Waiver</h2>
              <p className="text-xs text-slate-500 mt-0.5">
                {selectedFee.participant_name} • Invoice: {selectedFee.invoice_reference} (₹{selectedFee.amount})
              </p>
            </div>

            <form onSubmit={handleApplyWaiver} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Justification / Institutional Scholarship Reason
                </label>
                <textarea
                  rows={3}
                  required
                  placeholder="e.g. Merit Sports Scholarship / Varsity Representation Grant approved by Sports Board..."
                  value={waiverReason}
                  onChange={(e) => setWaiverReason(e.target.value)}
                  className="w-full text-xs border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setSelectedFee(null)}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-xs bg-indigo-600 text-white rounded font-medium hover:bg-indigo-700 shadow-sm"
                >
                  Confirm Waiver Grant
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
