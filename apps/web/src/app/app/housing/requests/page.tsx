"use client";

import { useEffect, useState } from "react";
import {
  ClipboardList,
  Plus,
  Search,
  CheckCircle2,
  Clock,
  XCircle,
  AlertCircle,
  CheckCircle,
  X,
  Eye,
} from "lucide-react";
import { HousingNav } from "@/components/housing/housing-nav";
import { HousingService } from "@/services/housing.service";
import {
  AccommodationProperty,
  HousingRequestCreateInput,
  HousingRequestReviewInput,
  HousingRequestStatus,
  StudentHousingRequest,
  UnitType,
} from "@/types/housing";

export default function StudentHousingRequestsPage() {
  const [requests, setRequests] = useState<StudentHousingRequest[]>([]);
  const [properties, setProperties] = useState<AccommodationProperty[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
  const [selectedRequestToReview, setSelectedRequestToReview] = useState<StudentHousingRequest | null>(null);
  const [reviewData, setReviewData] = useState<HousingRequestReviewInput>({
    status: "UNDER_REVIEW",
    review_notes: "",
    priority_score: 50,
  });
  const [actionLoading, setActionLoading] = useState(false);

  // New Request form state
  const [newRequest, setNewRequest] = useState<HousingRequestCreateInput>({
    academic_term: "2026-27 Odd Semester",
    preferred_unit_type: "DOUBLE_OCCUPANCY",
    requested_move_in_date: "2026-07-01",
    requested_move_out_date: "2027-05-31",
    budget_max: 10000,
    accessibility_required: false,
    special_requests: "",
    dietary_preference: "VEGETARIAN",
  });

  const loadData = async () => {
    try {
      const [reqs, props] = await Promise.all([
        HousingService.listRequests(),
        HousingService.listProperties(false),
      ]);
      setRequests(reqs);
      setProperties(props);
    } catch (err) {
      console.error("Failed to load requests", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSubmitRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await HousingService.submitRequest(newRequest);
      setIsSubmitModalOpen(false);
      loadData();
    } catch (err) {
      alert("Failed to submit request: " + (err as Error).message);
    }
  };

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRequestToReview) return;
    setActionLoading(true);
    try {
      await HousingService.reviewRequest(selectedRequestToReview.id, reviewData);
      setSelectedRequestToReview(null);
      loadData();
    } catch (err) {
      alert("Failed to review request: " + (err as Error).message);
    } finally {
      setActionLoading(false);
    }
  };

  const filteredRequests = requests.filter((r) => {
    const studentName = r.student_name || "";
    const regNo = r.student_roll_number || "";
    const matchesSearch =
      studentName.toLowerCase().includes(search.toLowerCase()) ||
      regNo.toLowerCase().includes(search.toLowerCase()) ||
      r.academic_term.toLowerCase().includes(search.toLowerCase());

    const matchesStatus = statusFilter === "ALL" || r.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (status: HousingRequestStatus) => {
    switch (status) {
      case "SUBMITTED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/30">
            <Clock className="w-3.5 h-3.5" />
            Submitted
          </span>
        );
      case "UNDER_REVIEW":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            Under Review
          </span>
        );
      case "WAITLISTED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/30">
            Waitlisted
          </span>
        );
      case "OFFERED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
            Offer Issued
          </span>
        );
      case "ALLOCATED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle className="w-3.5 h-3.5" />
            Allocated
          </span>
        );
      case "REJECTED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">
            <XCircle className="w-3.5 h-3.5" />
            Rejected
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400">
            {status}
          </span>
        );
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
              <ClipboardList className="w-7 h-7 text-indigo-400" />
              Student Housing Requests & Waitlist Queue
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Merit, distance, and special-need weighted student accommodation applications, waitlist rankings, and warden verification.
            </p>
          </div>

          <button
            onClick={() => setIsSubmitModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            Submit New Housing Request
          </button>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="relative md:col-span-3">
            <Search className="w-5 h-5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search by student name, registration number, or academic term..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-300 focus:outline-none focus:border-indigo-500"
            >
              <option value="ALL">All Request Statuses</option>
              <option value="SUBMITTED">Submitted</option>
              <option value="UNDER_REVIEW">Under Review</option>
              <option value="WAITLISTED">Waitlisted</option>
              <option value="OFFERED">Offer Issued</option>
              <option value="ALLOCATED">Allocated</option>
              <option value="REJECTED">Rejected</option>
            </select>
          </div>
        </div>

        {/* Requests Table */}
        {loading ? (
          <div className="py-20 text-center text-slate-400">Loading student housing applications...</div>
        ) : filteredRequests.length === 0 ? (
          <div className="py-16 text-center border border-dashed border-slate-800 rounded-xl bg-slate-900/30">
            <p className="text-slate-400">No student housing requests found matching criteria.</p>
          </div>
        ) : (
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-950/80 border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <tr>
                    <th className="px-5 py-3">Student Info</th>
                    <th className="px-5 py-3">Academic Term</th>
                    <th className="px-5 py-3">Preference & Budget</th>
                    <th className="px-5 py-3">Priority / Rank</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredRequests.map((req) => (
                    <tr key={req.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-5 py-4">
                        <div className="font-semibold text-white">
                          {req.student_name || "Enrolled Scholar"}
                        </div>
                        <div className="text-xs font-mono text-indigo-400">
                          {req.student_roll_number || req.student_id.slice(0, 8)}
                        </div>
                        {req.accessibility_required && (
                          <span className="inline-block mt-1 text-[11px] font-semibold text-purple-400">
                            ♿ Accessibility Priority
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-4">
                        <span className="font-medium text-slate-200">{req.academic_term}</span>
                        <div className="text-xs text-slate-500">
                          Applied: {new Date(req.created_at).toLocaleDateString()}
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <div className="text-xs text-slate-300">
                          Type: <strong className="text-white">{req.preferred_unit_type.replace(/_/g, " ")}</strong>
                        </div>
                        <div className="text-xs text-slate-400 mt-0.5">
                          Budget: ₹{(req.budget_max || 0).toLocaleString("en-IN")}/mo
                        </div>
                        {req.dietary_preference && (
                          <div className="text-[11px] text-slate-500">
                            Diet: {req.dietary_preference}
                          </div>
                        )}
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-2">
                          <span
                            className={`px-2 py-0.5 rounded text-xs font-bold ${
                              req.priority_score >= 80
                                ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                                : req.priority_score >= 60
                                ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                                : "bg-slate-800 text-slate-300"
                            }`}
                          >
                            Score: {req.priority_score}
                          </span>
                          {req.waitlist_position && (
                            <span className="text-xs text-purple-400 font-mono">
                              Waitlist #{req.waitlist_position}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-5 py-4">{getStatusBadge(req.status)}</td>
                      <td className="px-5 py-4 text-right">
                        <button
                          onClick={() => {
                            setSelectedRequestToReview(req);
                            setReviewData({
                              status:
                                req.status === "SUBMITTED"
                                  ? "UNDER_REVIEW"
                                  : (req.status as any),
                              review_notes: req.review_notes || "",
                              priority_score: req.priority_score,
                            });
                          }}
                          className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          Review / Rank
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Modal: Review Housing Request */}
        {selectedRequestToReview && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
            <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-lg font-bold text-white">
                  Review Housing Application
                </h3>
                <button
                  onClick={() => setSelectedRequestToReview(null)}
                  className="text-slate-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800/80 space-y-1 text-xs">
                <div>
                  Student: <strong className="text-white">{selectedRequestToReview.student_name}</strong> ({selectedRequestToReview.student_roll_number})
                </div>
                <div>
                  Term: <span className="text-slate-300">{selectedRequestToReview.academic_term}</span>
                </div>
                <div>
                  Preferences: <span className="text-slate-300">{selectedRequestToReview.preferred_unit_type.replace(/_/g, " ")} | Max ₹{selectedRequestToReview.budget_max}/mo</span>
                </div>
                {selectedRequestToReview.special_requests && (
                  <div className="text-amber-300">
                    Notes/Special: {selectedRequestToReview.special_requests}
                  </div>
                )}
              </div>

              <form onSubmit={handleReviewSubmit} className="space-y-4 text-sm">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Application Decision / Status *
                  </label>
                  <select
                    value={reviewData.status}
                    onChange={(e) =>
                      setReviewData({
                        ...reviewData,
                        status: e.target.value as any,
                      })
                    }
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="UNDER_REVIEW">Under Review</option>
                    <option value="WAITLISTED">Approve & Place on Waitlist</option>
                    <option value="REJECTED">Reject Application</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Priority Score (0-100) — based on distance & special needs
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={reviewData.priority_score}
                    onChange={(e) =>
                      setReviewData({
                        ...reviewData,
                        priority_score: parseInt(e.target.value) || 0,
                      })
                    }
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Reviewer Notes / Verification Justification
                  </label>
                  <textarea
                    rows={3}
                    value={reviewData.review_notes || ""}
                    onChange={(e) =>
                      setReviewData({
                        ...reviewData,
                        review_notes: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200 text-xs"
                    placeholder="e.g. Distance exceeds 45km; first-year scholar priority verified."
                  />
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setSelectedRequestToReview(null)}
                    className="px-4 py-2 text-xs font-medium rounded-md bg-slate-800 text-slate-300 hover:bg-slate-700"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={actionLoading}
                    className="px-4 py-2 text-xs font-medium rounded-md bg-indigo-600 hover:bg-indigo-500 text-white"
                  >
                    Save Review & Update Ranking
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: New Housing Request Submission */}
        {isSubmitModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
            <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto shadow-2xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h2 className="text-lg font-bold text-white">Submit Student Housing Request</h2>
                <button
                  onClick={() => setIsSubmitModalOpen(false)}
                  className="text-slate-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleSubmitRequest} className="space-y-4 text-sm">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Academic Term *
                  </label>
                  <input
                    required
                    type="text"
                    value={newRequest.academic_term}
                    onChange={(e) =>
                      setNewRequest({ ...newRequest, academic_term: e.target.value })
                    }
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    placeholder="e.g. 2026-27 Odd Semester"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Preferred Unit Type *
                    </label>
                    <select
                      value={newRequest.preferred_unit_type}
                      onChange={(e) =>
                        setNewRequest({
                          ...newRequest,
                          preferred_unit_type: e.target.value as UnitType,
                        })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    >
                      <option value="SINGLE_OCCUPANCY">Single Occupancy</option>
                      <option value="DOUBLE_OCCUPANCY">Double Occupancy</option>
                      <option value="TRIPLE_OCCUPANCY">Triple Occupancy</option>
                      <option value="DORMITORY">Dormitory</option>
                      <option value="STUDIO_APARTMENT">Studio Apartment</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Max Monthly Budget (₹) *
                    </label>
                    <input
                      required
                      type="number"
                      value={newRequest.budget_max || 0}
                      onChange={(e) =>
                        setNewRequest({
                          ...newRequest,
                          budget_max: parseFloat(e.target.value) || 0,
                        })
                      }
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Dietary Preference
                  </label>
                  <select
                    value={newRequest.dietary_preference || "VEGETARIAN"}
                    onChange={(e) =>
                      setNewRequest({
                        ...newRequest,
                        dietary_preference: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200"
                  >
                    <option value="VEGETARIAN">Vegetarian</option>
                    <option value="NON_VEGETARIAN">Non-Vegetarian</option>
                    <option value="JAIN">Jain Food</option>
                    <option value="VEGAN">Vegan</option>
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="req_acc"
                    checked={newRequest.accessibility_required}
                    onChange={(e) =>
                      setNewRequest({
                        ...newRequest,
                        accessibility_required: e.target.checked,
                      })
                    }
                    className="rounded bg-slate-950 border-slate-800 text-indigo-600"
                  />
                  <label htmlFor="req_acc" className="text-xs text-slate-300">
                    Require ground-floor or wheelchair accessible accommodation
                  </label>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Special Requirements / Medical Notes
                  </label>
                  <textarea
                    rows={2}
                    value={newRequest.special_requests || ""}
                    onChange={(e) =>
                      setNewRequest({
                        ...newRequest,
                        special_requests: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-md text-slate-200 text-xs"
                    placeholder="e.g. Asthma — requires well-ventilated room."
                  />
                </div>

                <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setIsSubmitModalOpen(false)}
                    className="px-4 py-2 text-xs font-medium rounded-md bg-slate-800 text-slate-300 hover:bg-slate-700"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 text-xs font-medium rounded-md bg-indigo-600 hover:bg-indigo-500 text-white"
                  >
                    Submit Application
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
