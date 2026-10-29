"use client";

import { useEffect, useState } from "react";
import {
  ClipboardCheck,
  Plus,
  LogIn,
  LogOut,
  Key,
  AlertTriangle,
  X,
  CheckCircle,
} from "lucide-react";
import { HousingNav } from "@/components/housing/housing-nav";
import { HousingService } from "@/services/housing.service";
import {
  HousingAssignment,
  HousingCheckInOutInput,
  HousingCheckInOutRecord,
} from "@/types/housing";

export default function CheckInOutPage() {
  const [records, setRecords] = useState<HousingCheckInOutRecord[]>([]);
  const [assignments, setAssignments] = useState<HousingAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const [formData, setFormData] = useState<HousingCheckInOutInput>({
    assignment_id: "",
    record_type: "CHECK_IN",
    scheduled_date: new Date().toISOString().split("T")[0],
    key_card_issued_or_returned: true,
    key_identifier: "RFID-CARD-8819",
    room_condition_rating: "EXCELLENT",
    damage_assessed_amount: 0,
    damage_description: "",
    notes: "Move-in orientation completed. Rules acknowledged.",
  });

  const loadData = async () => {
    try {
      const [allRecords, allAssignments] = await Promise.all([
        HousingService.listCheckIns(),
        HousingService.listAssignments(),
      ]);
      setRecords(allRecords);
      setAssignments(allAssignments);
      if (allAssignments.length > 0) {
        setFormData((prev) => ({ ...prev, assignment_id: allAssignments[0].id }));
      }
    } catch (err) {
      console.error("Failed to load check-in records", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      await HousingService.recordCheckInOut(formData);
      setIsModalOpen(false);
      loadData();
    } catch (err) {
      alert("Failed to record check-in/out: " + (err as Error).message);
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
              <ClipboardCheck className="w-7 h-7 text-indigo-400" />
              Check-In, Check-Out & Room Inventory Condition Audits
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Physical asset handovers, biometric/RFID access card logging, and move-out security deposit damage reconciliation.
            </p>
          </div>

          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            Record Check-In / Check-Out
          </button>
        </div>

        {/* Records Table */}
        {loading ? (
          <div className="py-20 text-center text-slate-400">Loading check-in & handover records...</div>
        ) : records.length === 0 ? (
          <div className="py-16 text-center border border-dashed border-slate-800 rounded-xl bg-slate-900/30">
            <p className="text-slate-400">No move-in or move-out inspections recorded yet.</p>
          </div>
        ) : (
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-950/80 border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <tr>
                    <th className="px-5 py-3">Event Type</th>
                    <th className="px-5 py-3">Assignment Ref</th>
                    <th className="px-5 py-3">Event Date</th>
                    <th className="px-5 py-3">Key / RFID Handover</th>
                    <th className="px-5 py-3">Inventory Condition</th>
                    <th className="px-5 py-3">Damage Settlement</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {records.map((rec) => (
                    <tr key={rec.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-5 py-4">
                        {rec.record_type === "CHECK_IN" ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                            <LogIn className="w-3.5 h-3.5" />
                            Check-In
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                            <LogOut className="w-3.5 h-3.5" />
                            Check-Out
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-4">
                        <div className="font-mono text-xs text-indigo-400">
                          {rec.assignment_id.slice(0, 8)}
                        </div>
                        <div className="text-xs text-slate-400">
                          Rating: {rec.room_condition_rating}
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <span className="font-mono text-xs text-slate-300">
                          {rec.scheduled_date}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-1 text-xs text-slate-200">
                          <Key className="w-3.5 h-3.5 text-indigo-400" />
                          <span>{rec.key_card_issued_or_returned ? "Key Issued" : "Pending Key"}</span>
                        </div>
                        {rec.key_identifier && (
                          <div className="text-[11px] font-mono text-slate-500">
                            Card: {rec.key_identifier}
                          </div>
                        )}
                      </td>
                      <td className="px-5 py-4">
                        <div className="text-xs text-slate-300 max-w-xs truncate">
                          {rec.notes || "All checklist items verified by resident & warden."}
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        {rec.damage_assessed_amount > 0 ? (
                          <span className="inline-flex items-center gap-1 text-xs font-bold text-rose-400">
                            <AlertTriangle className="w-3.5 h-3.5" />
                            -₹{rec.damage_assessed_amount.toLocaleString("en-IN")}
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-xs text-emerald-400 font-medium">
                            <CheckCircle className="w-3.5 h-3.5" />
                            Zero Damage
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

        {/* Modal: Record Check In / Out */}
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
            <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto shadow-2xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <ClipboardCheck className="w-5 h-5 text-indigo-400" />
                  Perform Physical Handover Audit
                </h3>
                <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-white">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4 text-sm">
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

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Event Action *
                    </label>
                    <select
                      value={formData.record_type}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          record_type: e.target.value as "CHECK_IN" | "CHECK_OUT",
                        })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    >
                      <option value="CHECK_IN">Move-In Check-In</option>
                      <option value="CHECK_OUT">Move-Out Check-Out</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Scheduled Date *
                    </label>
                    <input
                      required
                      type="date"
                      value={formData.scheduled_date}
                      onChange={(e) =>
                        setFormData({ ...formData, scheduled_date: e.target.value })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    RFID Access Card UID / Key Fob Serial
                  </label>
                  <input
                    type="text"
                    value={formData.key_identifier || ""}
                    onChange={(e) =>
                      setFormData({ ...formData, key_identifier: e.target.value })
                    }
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200 font-mono"
                    placeholder="RFID-CARD-8819"
                  />
                </div>

                {formData.record_type === "CHECK_OUT" && (
                  <div className="p-3 bg-rose-950/20 border border-rose-900/40 rounded-lg space-y-3">
                    <h4 className="text-xs font-semibold text-rose-300 uppercase tracking-wider">
                      Damage Assessment & Forfeiture
                    </h4>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-medium text-slate-300 mb-1">
                          Assessed Damage Deduction (₹)
                        </label>
                        <input
                          type="number"
                          value={formData.damage_assessed_amount || 0}
                          onChange={(e) =>
                            setFormData({
                              ...formData,
                              damage_assessed_amount: parseFloat(e.target.value) || 0,
                            })
                          }
                          className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-slate-300 mb-1">
                          Damage Justification
                        </label>
                        <input
                          type="text"
                          value={formData.damage_description || ""}
                          onChange={(e) =>
                            setFormData({ ...formData, damage_description: e.target.value })
                          }
                          placeholder="e.g. Broken wardrobe lock cylinder"
                          className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                        />
                      </div>
                    </div>
                  </div>
                )}

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Inspector & Student Handover Notes
                  </label>
                  <textarea
                    rows={2}
                    value={formData.notes || ""}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200 text-xs"
                  />
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
                    Save Handover Audit
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
