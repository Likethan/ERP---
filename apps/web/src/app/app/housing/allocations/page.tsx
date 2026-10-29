"use client";

import { useEffect, useState } from "react";
import {
  Key,
  Plus,
  ArrowLeftRight,
  CheckCircle,
  XCircle,
  Clock,
  Building2,
  FileText,
  X,
  Sparkles,
} from "lucide-react";
import { HousingNav } from "@/components/housing/housing-nav";
import { HousingService } from "@/services/housing.service";
import {
  AccommodationBed,
  AccommodationProperty,
  AccommodationUnit,
  HousingAssignment,
  HousingAssignmentCreateInput,
  HousingAssignmentStatus,
  HousingOffer,
  HousingOfferCreateInput,
  HousingOfferStatus,
  HousingTransferInput,
  StudentHousingRequest,
} from "@/types/housing";

export default function AllocationsAndOffersPage() {
  const [offers, setOffers] = useState<HousingOffer[]>([]);
  const [assignments, setAssignments] = useState<HousingAssignment[]>([]);
  const [properties, setProperties] = useState<AccommodationProperty[]>([]);
  const [requests, setRequests] = useState<StudentHousingRequest[]>([]);
  const [units, setUnits] = useState<AccommodationUnit[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"ASSIGNMENTS" | "OFFERS">("ASSIGNMENTS");

  // Modals
  const [isOfferModalOpen, setIsOfferModalOpen] = useState(false);
  const [isDirectAllocateModalOpen, setIsDirectAllocateModalOpen] = useState(false);
  const [selectedAssignmentForTransfer, setSelectedAssignmentForTransfer] = useState<HousingAssignment | null>(null);

  // Form states
  const [newOffer, setNewOffer] = useState<HousingOfferCreateInput>({
    request_id: "",
    property_id: "",
    unit_id: "",
    bed_id: "",
    offered_rent_monthly: 8500,
    offered_deposit: 15000,
    occupancy_start_date: "2026-07-01",
    occupancy_end_date: "2027-05-31",
    offer_valid_days: 3,
  });

  const [directAllocate, setDirectAllocate] = useState<HousingAssignmentCreateInput>({
    student_id: "",
    property_id: "",
    unit_id: "",
    bed_id: "",
    start_date: new Date().toISOString().split("T")[0],
    end_date: "2027-05-31",
    monthly_rent: 8500,
    security_deposit: 15000,
  });

  const [transferData, setTransferData] = useState<HousingTransferInput>({
    target_unit_id: "",
    target_bed_id: "",
    transfer_reason: "Academic compatibility and room change request",
  });

  const [actionLoading, setActionLoading] = useState(false);
  const [selectedOfferPropertyId, setSelectedOfferPropertyId] = useState("");

  const loadAll = async () => {
    try {
      const [allOffers, allAssignments, allProps, allReqs] = await Promise.all([
        HousingService.listOffers(),
        HousingService.listAssignments(),
        HousingService.listProperties(false),
        HousingService.listRequests(),
      ]);
      setOffers(allOffers);
      setAssignments(allAssignments);
      setProperties(allProps);
      setRequests(
        allReqs.filter((r: StudentHousingRequest) => r.status === "WAITLISTED" || r.status === "SUBMITTED")
      );
      if (allProps.length > 0) {
        setSelectedOfferPropertyId(allProps[0].id);
        setNewOffer((prev) => ({ ...prev, property_id: allProps[0].id }));
        setDirectAllocate((prev) => ({ ...prev, property_id: allProps[0].id }));
      }
    } catch (err) {
      console.error("Failed to load allocations", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  useEffect(() => {
    if (!selectedOfferPropertyId) return;
    async function loadUnitsForProperty() {
      try {
        const u = await HousingService.listUnits(selectedOfferPropertyId);
        setUnits(u);
        if (u.length > 0) {
          setNewOffer((prev) => ({ ...prev, unit_id: u[0].id }));
          setDirectAllocate((prev) => ({ ...prev, unit_id: u[0].id }));
        }
      } catch (err) {
        console.error("Failed to load units for property", err);
      }
    }
    loadUnitsForProperty();
  }, [selectedOfferPropertyId]);

  const handleIssueOffer = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      await HousingService.createOffer(newOffer);
      setIsOfferModalOpen(false);
      loadAll();
    } catch (err) {
      alert("Failed to issue offer: " + (err as Error).message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDirectAllocate = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      await HousingService.allocateStudent(directAllocate);
      setIsDirectAllocateModalOpen(false);
      loadAll();
    } catch (err) {
      alert("Direct allocation failed: " + (err as Error).message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAssignmentForTransfer) return;
    setActionLoading(true);
    try {
      await HousingService.transferRoom(selectedAssignmentForTransfer.id, transferData);
      setSelectedAssignmentForTransfer(null);
      loadAll();
    } catch (err) {
      alert("Room transfer failed: " + (err as Error).message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRespondOffer = async (offerId: string, accept: boolean) => {
    setActionLoading(true);
    try {
      await HousingService.respondOffer(offerId, {
        decision: accept ? "ACCEPTED" : "DECLINED",
      });
      loadAll();
    } catch (err) {
      alert("Offer response failed: " + (err as Error).message);
    } finally {
      setActionLoading(false);
    }
  };

  const getAssignmentStatusBadge = (status: HousingAssignmentStatus) => {
    switch (status) {
      case "ACTIVE":
      case "CHECKED_IN":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle className="w-3.5 h-3.5" />
            {status.replace(/_/g, " ")}
          </span>
        );
      case "ASSIGNED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/30">
            Assigned (Pending Check-in)
          </span>
        );
      case "TRANSFER_REQUESTED":
      case "TRANSFERRED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/30">
            <ArrowLeftRight className="w-3.5 h-3.5" />
            {status.replace(/_/g, " ")}
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400">
            {status.replace(/_/g, " ")}
          </span>
        );
    }
  };

  const getOfferStatusBadge = (status: HousingOfferStatus) => {
    switch (status) {
      case "OFFERED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <Clock className="w-3.5 h-3.5" />
            Awaiting Acceptance
          </span>
        );
      case "ACCEPTED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle className="w-3.5 h-3.5" />
            Accepted
          </span>
        );
      case "DECLINED":
      case "REVOKED":
      case "EXPIRED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">
            <XCircle className="w-3.5 h-3.5" />
            {status}
          </span>
        );
      default:
        return null;
    }
  };

  // Available beds across units
  const availableBeds = units.flatMap((u) =>
    (u.beds || [])
      .filter((b) => b.status === "AVAILABLE")
      .map((b) => ({ ...b, unit_number: u.unit_number, unit_id: u.id }))
  );

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <HousingNav />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <Key className="w-7 h-7 text-indigo-400" />
              Allocations, Formal Offers & Room Transfers
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Concurrency-safe bed assignments, binding electronic offers, and inter-room transfer audit trails.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsOfferModalOpen(true)}
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs transition-colors shadow-sm"
            >
              <Sparkles className="w-4 h-4" />
              Issue Formal Offer
            </button>
            <button
              onClick={() => setIsDirectAllocateModalOpen(true)}
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs transition-colors"
            >
              <Plus className="w-4 h-4" />
              Direct Bed Allocation
            </button>
          </div>
        </div>

        {/* Tab Toggle */}
        <div className="flex items-center border-b border-slate-800 space-x-6 text-sm">
          <button
            onClick={() => setActiveTab("ASSIGNMENTS")}
            className={`pb-3 font-semibold transition-colors flex items-center gap-2 border-b-2 ${
              activeTab === "ASSIGNMENTS"
                ? "border-indigo-500 text-indigo-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Key className="w-4 h-4" />
            Active Occupants & Room Allocations ({assignments.length})
          </button>
          <button
            onClick={() => setActiveTab("OFFERS")}
            className={`pb-3 font-semibold transition-colors flex items-center gap-2 border-b-2 ${
              activeTab === "OFFERS"
                ? "border-indigo-500 text-indigo-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <FileText className="w-4 h-4" />
            Formal Offers Queue ({offers.length})
          </button>
        </div>

        {/* Loading state */}
        {loading ? (
          <div className="py-20 text-center text-slate-400">Loading allocation records...</div>
        ) : activeTab === "ASSIGNMENTS" ? (
          /* Assignments Table */
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-950/80 border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <tr>
                    <th className="px-5 py-3">Scholar Details</th>
                    <th className="px-5 py-3">Property / Facility</th>
                    <th className="px-5 py-3">Assigned Bed</th>
                    <th className="px-5 py-3">Lease Period</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {assignments.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-5 py-12 text-center text-slate-500">
                        No active bed assignments found.
                      </td>
                    </tr>
                  ) : (
                    assignments.map((asg) => (
                      <tr key={asg.id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="px-5 py-4">
                          <div className="font-semibold text-white">
                            {asg.student_name || "Enrolled Scholar"}
                          </div>
                          <div className="text-xs font-mono text-indigo-400">
                            {asg.student_roll_number || asg.student_id.slice(0, 8)}
                          </div>
                        </td>
                        <td className="px-5 py-4">
                          <div className="text-xs text-slate-200 font-medium">
                            {asg.property_name || "Campus Residential Facility"}
                          </div>
                          <div className="text-[11px] text-slate-500">
                            Room {asg.unit_number || "N/A"}
                          </div>
                        </td>
                        <td className="px-5 py-4">
                          <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-800 text-emerald-400 font-bold">
                            Bed {asg.bed_code || "B-1"}
                          </span>
                        </td>
                        <td className="px-5 py-4">
                          <div className="text-xs text-slate-300">{asg.start_date} to {asg.end_date}</div>
                          <div className="text-xs text-emerald-400 font-mono">₹{asg.monthly_rent}/mo</div>
                        </td>
                        <td className="px-5 py-4">{getAssignmentStatusBadge(asg.status)}</td>
                        <td className="px-5 py-4 text-right">
                          {asg.status !== "CHECKED_OUT" && asg.status !== "TERMINATED" && (
                            <button
                              onClick={() => {
                                setSelectedAssignmentForTransfer(asg);
                              }}
                              className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-md bg-slate-800 hover:bg-slate-700 text-indigo-300 transition-colors"
                            >
                              <ArrowLeftRight className="w-3.5 h-3.5" />
                              Transfer Room
                            </button>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          /* Offers Table */
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-950/80 border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <tr>
                    <th className="px-5 py-3">Student / Request</th>
                    <th className="px-5 py-3">Offered Accommodation</th>
                    <th className="px-5 py-3">Commercial Terms</th>
                    <th className="px-5 py-3">Expires At</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3 text-right">Offer Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {offers.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-5 py-12 text-center text-slate-500">
                        No pending or past accommodation offers found.
                      </td>
                    </tr>
                  ) : (
                    offers.map((off) => (
                      <tr key={off.id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="px-5 py-4">
                          <div className="font-semibold text-white">
                            {off.student_name || "Applicant Scholar"}
                          </div>
                          <div className="text-xs text-slate-500">
                            Ref: {off.request_id.slice(0, 8)}
                          </div>
                        </td>
                        <td className="px-5 py-4">
                          <div className="text-xs text-slate-200">
                            Bed {off.bed_code} (Room {off.unit_number})
                          </div>
                          <div className="text-[11px] text-indigo-400">
                            {off.property_name}
                          </div>
                        </td>
                        <td className="px-5 py-4">
                          <div className="text-xs font-medium text-emerald-400">
                            ₹{off.offered_rent_monthly.toLocaleString("en-IN")}/month
                          </div>
                          <div className="text-[11px] text-slate-400">
                            Deposit: ₹{off.offered_deposit.toLocaleString("en-IN")}
                          </div>
                        </td>
                        <td className="px-5 py-4">
                          <span className="text-xs font-mono text-slate-300">
                            {new Date(off.offer_valid_until).toLocaleString()}
                          </span>
                        </td>
                        <td className="px-5 py-4">{getOfferStatusBadge(off.status)}</td>
                        <td className="px-5 py-4 text-right">
                          {off.status === "OFFERED" && (
                            <div className="flex items-center justify-end gap-2">
                              <button
                                disabled={actionLoading}
                                onClick={() => handleRespondOffer(off.id, true)}
                                className="px-3 py-1 text-xs font-medium rounded bg-emerald-600 hover:bg-emerald-500 text-white"
                              >
                                Accept & Lock Bed
                              </button>
                              <button
                                disabled={actionLoading}
                                onClick={() => handleRespondOffer(off.id, false)}
                                className="px-2 py-1 text-xs font-medium rounded bg-rose-600/20 text-rose-300 hover:bg-rose-600/40 border border-rose-500/30"
                              >
                                Decline
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Modal: Issue Formal Offer */}
        {isOfferModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
            <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto shadow-2xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-indigo-400" />
                  Issue Formal Electronic Accommodation Offer
                </h3>
                <button onClick={() => setIsOfferModalOpen(false)} className="text-slate-400 hover:text-white">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleIssueOffer} className="space-y-4 text-sm">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Select Waitlisted Request *
                  </label>
                  <select
                    required
                    value={newOffer.request_id}
                    onChange={(e) => setNewOffer({ ...newOffer, request_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                  >
                    <option value="">-- Select Approved Student Request --</option>
                    {requests.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.student_name} ({r.academic_term}) — Budget ₹{r.budget_max}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Target Property
                    </label>
                    <select
                      value={selectedOfferPropertyId}
                      onChange={(e) => {
                        setSelectedOfferPropertyId(e.target.value);
                        setNewOffer((prev) => ({ ...prev, property_id: e.target.value }));
                      }}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    >
                      {properties.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Available Bed Slot *
                    </label>
                    <select
                      required
                      value={newOffer.bed_id}
                      onChange={(e) => {
                        const bed = availableBeds.find((b) => b.id === e.target.value);
                        setNewOffer({
                          ...newOffer,
                          bed_id: e.target.value,
                          unit_id: bed?.unit_id || newOffer.unit_id,
                        });
                      }}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    >
                      <option value="">-- Choose Bed --</option>
                      {availableBeds.map((b) => (
                        <option key={b.id} value={b.id}>
                          Room {b.unit_number} - Bed {b.bed_code}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Agreed Monthly Rent (₹) *
                    </label>
                    <input
                      required
                      type="number"
                      value={newOffer.offered_rent_monthly}
                      onChange={(e) =>
                        setNewOffer({ ...newOffer, offered_rent_monthly: parseFloat(e.target.value) || 0 })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Security Deposit (₹) *
                    </label>
                    <input
                      required
                      type="number"
                      value={newOffer.offered_deposit}
                      onChange={(e) =>
                        setNewOffer({ ...newOffer, offered_deposit: parseFloat(e.target.value) || 0 })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Occupancy Start Date
                    </label>
                    <input
                      type="date"
                      value={newOffer.occupancy_start_date}
                      onChange={(e) =>
                        setNewOffer({ ...newOffer, occupancy_start_date: e.target.value })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Offer Validity (Days)
                    </label>
                    <input
                      type="number"
                      value={newOffer.offer_valid_days || 3}
                      onChange={(e) =>
                        setNewOffer({ ...newOffer, offer_valid_days: parseInt(e.target.value) || 3 })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setIsOfferModalOpen(false)}
                    className="px-4 py-2 text-xs font-medium rounded-md bg-slate-800 text-slate-300 hover:bg-slate-700"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={actionLoading}
                    className="px-4 py-2 text-xs font-medium rounded-md bg-indigo-600 hover:bg-indigo-500 text-white"
                  >
                    Issue Offer & Reserve Bed
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Direct Allocation */}
        {isDirectAllocateModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
            <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-lg font-bold text-white">Direct Student Bed Allocation</h3>
                <button onClick={() => setIsDirectAllocateModalOpen(false)} className="text-slate-400 hover:text-white">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleDirectAllocate} className="space-y-4 text-sm">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Student ID / UUID *
                  </label>
                  <input
                    required
                    type="text"
                    value={directAllocate.student_id}
                    onChange={(e) =>
                      setDirectAllocate({ ...directAllocate, student_id: e.target.value })
                    }
                    placeholder="e.g. stu-uuid-001 or registration number"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Target Property
                    </label>
                    <select
                      value={selectedOfferPropertyId}
                      onChange={(e) => {
                        setSelectedOfferPropertyId(e.target.value);
                        setDirectAllocate((prev) => ({ ...prev, property_id: e.target.value }));
                      }}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    >
                      {properties.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Available Bed *
                    </label>
                    <select
                      required
                      value={directAllocate.bed_id}
                      onChange={(e) => {
                        const bed = availableBeds.find((b) => b.id === e.target.value);
                        setDirectAllocate({
                          ...directAllocate,
                          bed_id: e.target.value,
                          unit_id: bed?.unit_id || directAllocate.unit_id,
                        });
                      }}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    >
                      <option value="">-- Choose Bed --</option>
                      {availableBeds.map((b) => (
                        <option key={b.id} value={b.id}>
                          Room {b.unit_number} - Bed {b.bed_code}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Start Date
                    </label>
                    <input
                      type="date"
                      value={directAllocate.start_date}
                      onChange={(e) =>
                        setDirectAllocate({ ...directAllocate, start_date: e.target.value })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      End Date
                    </label>
                    <input
                      type="date"
                      value={directAllocate.end_date}
                      onChange={(e) =>
                        setDirectAllocate({ ...directAllocate, end_date: e.target.value })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setIsDirectAllocateModalOpen(false)}
                    className="px-4 py-2 text-xs font-medium rounded-md bg-slate-800 text-slate-300 hover:bg-slate-700"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={actionLoading}
                    className="px-4 py-2 text-xs font-medium rounded-md bg-indigo-600 hover:bg-indigo-500 text-white"
                  >
                    Confirm Direct Bed Assignment
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Room Transfer */}
        {selectedAssignmentForTransfer && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
            <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <ArrowLeftRight className="w-5 h-5 text-indigo-400" />
                  Initiate Room / Bed Transfer
                </h3>
                <button
                  onClick={() => setSelectedAssignmentForTransfer(null)}
                  className="text-slate-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="p-3 rounded-lg bg-slate-950 text-xs space-y-1">
                <div>
                  Occupant: <strong className="text-white">{selectedAssignmentForTransfer.student_name}</strong>
                </div>
                <div>
                  Current Bed: <span className="font-mono text-indigo-400">Bed {selectedAssignmentForTransfer.bed_code}</span> (Room {selectedAssignmentForTransfer.unit_number})
                </div>
              </div>

              <form onSubmit={handleTransfer} className="space-y-4 text-sm">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Select Destination Bed Slot *
                  </label>
                  <select
                    required
                    value={transferData.target_bed_id}
                    onChange={(e) => {
                      const bed = availableBeds.find((b) => b.id === e.target.value);
                      setTransferData({
                        ...transferData,
                        target_bed_id: e.target.value,
                        target_unit_id: bed?.unit_id || "",
                      });
                    }}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                  >
                    <option value="">-- Choose New Bed --</option>
                    {availableBeds.map((b) => (
                      <option key={b.id} value={b.id}>
                        Room {b.unit_number} - Bed {b.bed_code}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Reason for Relocation *
                  </label>
                  <textarea
                    required
                    rows={2}
                    value={transferData.transfer_reason}
                    onChange={(e) =>
                      setTransferData({ ...transferData, transfer_reason: e.target.value })
                    }
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200 text-xs"
                  />
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setSelectedAssignmentForTransfer(null)}
                    className="px-4 py-2 text-xs font-medium rounded-md bg-slate-800 text-slate-300 hover:bg-slate-700"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={actionLoading}
                    className="px-4 py-2 text-xs font-medium rounded-md bg-indigo-600 hover:bg-indigo-500 text-white"
                  >
                    Execute Bed Transfer
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
