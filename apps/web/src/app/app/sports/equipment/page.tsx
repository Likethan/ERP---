"use client";

import React, { useState, useEffect } from "react";
import { SportsNav } from "@/components/sports/sports-nav";
import { sportsService } from "@/services/sports.service";
import { SportsEquipmentAssignmentItem } from "@/types/sports";
import {
  Package,
  Plus,
  Search,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
} from "lucide-react";

export default function EquipmentPage() {
  const [assignments, setAssignments] = useState<SportsEquipmentAssignmentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  // Modals
  const [isCheckoutModalOpen, setIsCheckoutModalOpen] = useState(false);
  const [returnModalItem, setReturnModalItem] = useState<SportsEquipmentAssignmentItem | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Checkout form
  const [checkoutData, setCheckoutData] = useState({
    equipmentName: "FIFA Match Ball Pro Pack (Set of 6)",
    itemCode: "EQ-FB-BALL-01",
    responsibleUserName: "Coach Sneha Kulkarni",
    allocatedQuantity: 1,
    checkoutDate: "2026-10-24",
    dueDate: "2026-10-27",
  });

  // Return form
  const [returnCondition, setReturnCondition] = useState("GOOD");
  const [damageFee, setDamageFee] = useState(0);
  const [returnNotes, setReturnNotes] = useState("");

  useEffect(() => {
    loadEquipment();
  }, []);

  const loadEquipment = async () => {
    setLoading(true);
    const res = await sportsService.listEquipmentAssignments();
    if (res.success && res.data) {
      setAssignments(res.data);
    }
    setLoading(false);
  };

  const handleCheckout = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await sportsService.checkoutEquipment({
      itemCode: checkoutData.itemCode,
      equipmentName: checkoutData.equipmentName,
      responsibleUserName: checkoutData.responsibleUserName,
      allocatedQuantity: Number(checkoutData.allocatedQuantity),
      checkoutDate: checkoutData.checkoutDate,
      dueDate: checkoutData.dueDate,
    });

    if (res.success && res.data) {
      setActionSuccess(
        `Checked out ${checkoutData.allocatedQuantity}x ${checkoutData.equipmentName} to ${checkoutData.responsibleUserName}.`
      );
      setIsCheckoutModalOpen(false);
      loadEquipment();
    }
  };

  const handleReturn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!returnModalItem) return;

    const res = await sportsService.returnEquipment(
      returnModalItem.id,
      returnCondition,
      returnNotes,
      damageFee
    );

    if (res.success && res.data) {
      setActionSuccess(
        `Returned ${returnModalItem.equipmentName}. Condition logged: ${returnCondition}${
          damageFee > 0 ? ` (Damage Fee ₹${damageFee} flagged)` : ""
        }.`
      );
      setReturnModalItem(null);
      loadEquipment();
    }
  };

  const filtered = assignments.filter((a) => {
    const matchesSearch =
      a.equipmentName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.responsibleUserName.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || a.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      <SportsNav />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Sports Equipment & Gear Allocation
          </h1>
          <p className="text-sm text-slate-500">
            Integrated equipment checkout, wear-and-tear audits, and inventory asset tracking.
          </p>
        </div>
        <button
          onClick={() => setIsCheckoutModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm font-medium shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          Checkout Gear
        </button>
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

      {/* Metrics Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="p-2.5 bg-blue-50 text-blue-600 rounded-lg">
            <Package className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Active Gear Loans</p>
            <p className="text-xl font-bold text-slate-900">
              {assignments.filter((a) => a.status === "ISSUED").length} Out on Field
            </p>
          </div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-lg">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Returned & Inspected</p>
            <p className="text-xl font-bold text-slate-900">
              {assignments.filter((a) => a.status === "RETURNED").length} Returned
            </p>
          </div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
          <div className="p-2.5 bg-amber-50 text-amber-600 rounded-lg">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Damaged / Overdue Items</p>
            <p className="text-xl font-bold text-slate-900">
              {assignments.filter((a) => a.status === "OVERDUE" || a.returnCondition === "DAMAGED").length} Flagged
            </p>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-wrap items-center gap-3 bg-white p-3 rounded-lg border border-slate-200">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search gear loans by item name or recipient..."
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
          <option value="all">All Statuses</option>
          <option value="ISSUED">Active Loan</option>
          <option value="RETURNED">Returned</option>
          <option value="OVERDUE">Overdue</option>
        </select>
      </div>

      {/* Equipment Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
              <tr>
                <th className="py-3 px-4">Equipment Description</th>
                <th className="py-3 px-4">Asset Code</th>
                <th className="py-3 px-4">Custodian / Team</th>
                <th className="py-3 px-4 text-center">Qty</th>
                <th className="py-3 px-4">Checkout Date</th>
                <th className="py-3 px-4">Due Date</th>
                <th className="py-3 px-4">Status & Condition</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filtered.map((item) => {
                const isActive = item.status === "ISSUED";
                return (
                  <tr key={item.id} className="hover:bg-slate-50/60">
                    <td className="py-3 px-4 font-semibold text-slate-900">{item.equipmentName}</td>
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-500">
                      {item.itemCode}
                    </td>
                    <td className="py-3 px-4 text-slate-800">{item.responsibleUserName}</td>
                    <td className="py-3 px-4 text-center font-bold">{item.allocatedQuantity}</td>
                    <td className="py-3 px-4 text-slate-500">{item.checkoutDate}</td>
                    <td className="py-3 px-4 text-slate-500 font-medium">{item.dueDate}</td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1.5">
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                            isActive
                              ? "bg-blue-100 text-blue-800"
                              : item.status === "RETURNED"
                              ? "bg-emerald-100 text-emerald-800"
                              : "bg-red-100 text-red-800"
                          }`}
                        >
                          {item.status}
                        </span>
                        {item.returnCondition && (
                          <span className="text-[10px] text-slate-500 uppercase font-medium">
                            ({item.returnCondition})
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-right">
                      {isActive ? (
                        <button
                          onClick={() => {
                            setReturnModalItem(item);
                            setReturnCondition("GOOD");
                            setDamageFee(0);
                            setReturnNotes("");
                          }}
                          className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 rounded hover:bg-indigo-100 transition-colors"
                        >
                          <RotateCcw className="w-3.5 h-3.5" />
                          Process Return
                        </button>
                      ) : (
                        <span className="text-slate-400 text-xs italic">Closed</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Checkout Equipment */}
      {isCheckoutModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl border border-slate-200 max-w-md w-full p-6 shadow-xl space-y-4">
            <h2 className="text-lg font-bold text-slate-900">Checkout Sports Equipment</h2>
            <form onSubmit={handleCheckout} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Equipment Name</label>
                <input
                  type="text"
                  required
                  value={checkoutData.equipmentName}
                  onChange={(e) => setCheckoutData({ ...checkoutData, equipmentName: e.target.value })}
                  className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Inventory Asset Code</label>
                  <input
                    type="text"
                    required
                    value={checkoutData.itemCode}
                    onChange={(e) => setCheckoutData({ ...checkoutData, itemCode: e.target.value })}
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Quantity</label>
                  <input
                    type="number"
                    min={1}
                    required
                    value={checkoutData.allocatedQuantity}
                    onChange={(e) => setCheckoutData({ ...checkoutData, allocatedQuantity: Number(e.target.value) })}
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Custodian (Coach / Athlete)</label>
                <input
                  type="text"
                  required
                  value={checkoutData.responsibleUserName}
                  onChange={(e) => setCheckoutData({ ...checkoutData, responsibleUserName: e.target.value })}
                  className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Checkout Date</label>
                  <input
                    type="date"
                    required
                    value={checkoutData.checkoutDate}
                    onChange={(e) => setCheckoutData({ ...checkoutData, checkoutDate: e.target.value })}
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Return Due Date</label>
                  <input
                    type="date"
                    required
                    value={checkoutData.dueDate}
                    onChange={(e) => setCheckoutData({ ...checkoutData, dueDate: e.target.value })}
                    className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsCheckoutModalOpen(false)}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-xs bg-indigo-600 text-white rounded font-medium hover:bg-indigo-700 shadow-sm"
                >
                  Confirm Issue
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Return Equipment */}
      {returnModalItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl border border-slate-200 max-w-md w-full p-6 shadow-xl space-y-4">
            <div>
              <h2 className="text-lg font-bold text-slate-900">Return & Inspect Equipment</h2>
              <p className="text-xs text-slate-500 mt-0.5">
                {returnModalItem.equipmentName} • Issued to {returnModalItem.responsibleUserName}
              </p>
            </div>

            <form onSubmit={handleReturn} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Return Inspection Condition</label>
                <select
                  value={returnCondition}
                  onChange={(e) => setReturnCondition(e.target.value)}
                  className="w-full text-sm border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none bg-white"
                >
                  <option value="EXCELLENT">Excellent (Re-shelve immediately)</option>
                  <option value="GOOD">Good (Normal athletic wear)</option>
                  <option value="DAMAGED">Damaged (Needs repair / replacement)</option>
                  <option value="LOST">Lost / Unreturned</option>
                </select>
              </div>

              {(returnCondition === "DAMAGED" || returnCondition === "LOST") && (
                <div>
                  <label className="block text-xs font-semibold text-red-700 mb-1">
                    Damage / Replacement Surcharge (₹)
                  </label>
                  <input
                    type="number"
                    min={0}
                    value={damageFee}
                    onChange={(e) => setDamageFee(Number(e.target.value))}
                    className="w-full text-sm border border-red-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-red-500 focus:outline-none bg-red-50"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Inspection Notes</label>
                <textarea
                  rows={2}
                  placeholder="Record condition details or return remarks..."
                  value={returnNotes}
                  onChange={(e) => setReturnNotes(e.target.value)}
                  className="w-full text-xs border border-slate-300 rounded px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setReturnModalItem(null)}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-xs bg-indigo-600 text-white rounded font-medium hover:bg-indigo-700 shadow-sm"
                >
                  Complete Return
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
