"use client";

import React, { useEffect, useState } from "react";
import {
  CheckCircle2,
  Clock,
  Filter,
  Plus,
  Search,
  Shield,
  UserCheck,
  Users,
  XCircle,
} from "lucide-react";
import { SecurityNav } from "@/components/campus-security/security-nav";
import { CampusSecurityService } from "@/services/campus-security.service";
import { VisitorProfile, VisitorRequest } from "@/types/campus-security";

export default function VisitorDirectoryPage() {
  const [requests, setRequests] = useState<VisitorRequest[]>([]);
  const [visitors, setVisitors] = useState<VisitorProfile[]>([]);
  const [activeTab, setActiveTab] = useState<"REQUESTS" | "DIRECTORY">("REQUESTS");
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [loading, setLoading] = useState(true);

  // New Request Form Modal State
  const [showModal, setShowModal] = useState(false);
  const [visitorName, setVisitorName] = useState("");
  const [visitorEmail, setVisitorEmail] = useState("");
  const [visitorPhone, setVisitorPhone] = useState("");
  const [visitorCategory, setVisitorCategory] = useState("GUEST");
  const [hostName, setHostName] = useState("");
  const [visitPurpose, setVisitPurpose] = useState("");
  const [destination, setDestination] = useState("");
  const [arrivalDate, setArrivalDate] = useState("");
  const [departureDate, setDepartureDate] = useState("");

  async function loadData() {
    setLoading(true);
    try {
      const [reqs, vis] = await Promise.all([
        CampusSecurityService.listRequests(),
        CampusSecurityService.listVisitors(),
      ]);
      setRequests(reqs);
      setVisitors(vis);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleCreateRequest(e: React.FormEvent) {
    e.preventDefault();
    try {
      await CampusSecurityService.submitRequest({
        visitor_name: visitorName,
        visitor_email: visitorEmail,
        visitor_phone: visitorPhone,
        visitor_category: visitorCategory as any,
        host_name: hostName,
        visit_purpose: visitPurpose,
        destination_description: destination,
        expected_arrival_at: arrivalDate || new Date().toISOString(),
        expected_departure_at:
          departureDate || new Date(Date.now() + 4 * 3600000).toISOString(),
      });
      setShowModal(false);
      resetForm();
      loadData();
    } catch (err) {
      alert("Failed to submit request: " + (err as Error).message);
    }
  }

  function resetForm() {
    setVisitorName("");
    setVisitorEmail("");
    setVisitorPhone("");
    setVisitorCategory("GUEST");
    setHostName("");
    setVisitPurpose("");
    setDestination("");
    setArrivalDate("");
    setDepartureDate("");
  }

  async function handleReview(requestId: string, decision: "APPROVED" | "REJECTED") {
    try {
      await CampusSecurityService.reviewRequest(requestId, decision);
      loadData();
    } catch (err) {
      alert("Error reviewing request: " + (err as Error).message);
    }
  }

  const filteredRequests = requests.filter((r) => {
    const matchesSearch =
      r.visitor_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.request_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.host_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "ALL" || r.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const filteredVisitors = visitors.filter((v) =>
    v.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    v.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    v.phone.includes(searchTerm)
  );

  return (
    <div className="min-h-screen bg-background text-foreground pb-16">
      <SecurityNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-black tracking-tight">Visitor Management & Pre-Registration</h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Guest lifecycle, host approvals, ID verification, and gate entry authorizations.
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-primary text-primary-foreground font-semibold rounded-xl text-sm shadow-sm hover:opacity-95 transition-all"
          >
            <Plus className="h-4 w-4" />
            <span>Pre-Register Guest</span>
          </button>
        </div>

        {/* Tab switch */}
        <div className="flex items-center space-x-2 border-b border-border">
          <button
            onClick={() => setActiveTab("REQUESTS")}
            className={`pb-3 text-sm font-semibold border-b-2 transition-all px-2 ${
              activeTab === "REQUESTS"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            Visit Requests ({requests.length})
          </button>
          <button
            onClick={() => setActiveTab("DIRECTORY")}
            className={`pb-3 text-sm font-semibold border-b-2 transition-all px-2 ${
              activeTab === "DIRECTORY"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            Verified Visitor Profiles ({visitors.length})
          </button>
        </div>

        {/* Filter bar */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search by visitor name, phone, host, or reference..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-card border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          {activeTab === "REQUESTS" && (
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 bg-card border border-border rounded-xl text-sm focus:outline-none"
            >
              <option value="ALL">All Statuses</option>
              <option value="PENDING">Pending Approval</option>
              <option value="APPROVED">Approved</option>
              <option value="REJECTED">Rejected</option>
            </select>
          )}
        </div>

        {/* Content table */}
        {activeTab === "REQUESTS" ? (
          <div className="bg-card border border-border rounded-2xl overflow-hidden shadow-xs">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-muted/50 border-b border-border text-xs text-muted-foreground uppercase font-semibold">
                  <tr>
                    <th className="px-5 py-3.5">Reference / Visitor</th>
                    <th className="px-5 py-3.5">Category</th>
                    <th className="px-5 py-3.5">Host & Destination</th>
                    <th className="px-5 py-3.5">Expected Window</th>
                    <th className="px-5 py-3.5">Status</th>
                    <th className="px-5 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {filteredRequests.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-5 py-8 text-center text-muted-foreground">
                        No visitor requests found.
                      </td>
                    </tr>
                  ) : (
                    filteredRequests.map((req) => (
                      <tr key={req.id} className="hover:bg-muted/20 transition-colors">
                        <td className="px-5 py-4">
                          <div className="font-bold text-sm text-foreground">{req.visitor_name}</div>
                          <div className="text-xs text-muted-foreground font-mono">
                            {req.request_number} • {req.visitor_phone}
                          </div>
                        </td>
                        <td className="px-5 py-4">
                          <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20">
                            {req.visitor_category}
                          </span>
                        </td>
                        <td className="px-5 py-4">
                          <div className="font-medium text-xs text-foreground">{req.host_name}</div>
                          <div className="text-[11px] text-muted-foreground">{req.destination_description}</div>
                        </td>
                        <td className="px-5 py-4 text-xs">
                          <div>{new Date(req.expected_arrival_at).toLocaleDateString()}</div>
                          <div className="text-muted-foreground text-[11px]">
                            {new Date(req.expected_arrival_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                          </div>
                        </td>
                        <td className="px-5 py-4">
                          <span
                            className={`text-xs px-2.5 py-1 rounded-full font-bold ${
                              req.status === "APPROVED"
                                ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20"
                                : req.status === "PENDING"
                                ? "bg-amber-500/10 text-amber-500 border border-amber-500/20"
                                : "bg-rose-500/10 text-rose-500 border border-rose-500/20"
                            }`}
                          >
                            {req.status}
                          </span>
                        </td>
                        <td className="px-5 py-4 text-right">
                          {req.status === "PENDING" ? (
                            <div className="flex items-center justify-end space-x-2">
                              <button
                                onClick={() => handleReview(req.id, "APPROVED")}
                                className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg text-xs"
                              >
                                Approve
                              </button>
                              <button
                                onClick={() => handleReview(req.id, "REJECTED")}
                                className="px-3 py-1 bg-rose-600 hover:bg-rose-700 text-white font-medium rounded-lg text-xs"
                              >
                                Reject
                              </button>
                            </div>
                          ) : (
                            <span className="text-xs text-muted-foreground">Decided</span>
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
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {filteredVisitors.map((vis) => (
              <div key={vis.id} className="p-5 bg-card border border-border rounded-xl space-y-2 shadow-xs">
                <div className="flex items-center justify-between">
                  <div className="font-bold text-sm">{vis.full_name}</div>
                  {vis.is_vip && (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400">
                      VIP
                    </span>
                  )}
                </div>
                <div className="text-xs text-muted-foreground">{vis.organization || "Independent Visitor"}</div>
                <div className="text-xs pt-1 border-t border-border/60 text-muted-foreground space-y-0.5">
                  <div>Email: <span className="text-foreground">{vis.email}</span></div>
                  <div>Phone: <span className="text-foreground">{vis.phone}</span></div>
                  <div>ID Type: <span className="text-foreground">{vis.id_document_type} ({vis.id_document_number_masked || "Verified"})</span></div>
                  <div>Total Visits: <span className="text-foreground font-semibold">{vis.total_visits}</span></div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-2xl w-full max-w-lg p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <h3 className="font-bold text-lg">Pre-Register Campus Visitor</h3>
              <button onClick={() => setShowModal(false)} className="text-muted-foreground hover:text-foreground">
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateRequest} className="space-y-4 text-sm">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Visitor Full Name</label>
                  <input
                    type="text"
                    required
                    value={visitorName}
                    onChange={(e) => setVisitorName(e.target.value)}
                    className="w-full mt-1 px-3 py-2 bg-muted/30 border border-border rounded-xl text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Category</label>
                  <select
                    value={visitorCategory}
                    onChange={(e) => setVisitorCategory(e.target.value)}
                    className="w-full mt-1 px-3 py-2 bg-muted/30 border border-border rounded-xl text-sm"
                  >
                    <option value="GUEST">Guest</option>
                    <option value="PARENT">Parent</option>
                    <option value="VENDOR">Vendor</option>
                    <option value="OFFICIAL">Official</option>
                    <option value="VIP">VIP</option>
                    <option value="INTERVIEW_CANDIDATE">Candidate</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Email</label>
                  <input
                    type="email"
                    required
                    value={visitorEmail}
                    onChange={(e) => setVisitorEmail(e.target.value)}
                    className="w-full mt-1 px-3 py-2 bg-muted/30 border border-border rounded-xl text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Phone</label>
                  <input
                    type="tel"
                    required
                    value={visitorPhone}
                    onChange={(e) => setVisitorPhone(e.target.value)}
                    className="w-full mt-1 px-3 py-2 bg-muted/30 border border-border rounded-xl text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">Host Name (Faculty/Staff/Student)</label>
                <input
                  type="text"
                  required
                  value={hostName}
                  onChange={(e) => setHostName(e.target.value)}
                  className="w-full mt-1 px-3 py-2 bg-muted/30 border border-border rounded-xl text-sm"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">Visit Purpose</label>
                <input
                  type="text"
                  required
                  value={visitPurpose}
                  onChange={(e) => setVisitPurpose(e.target.value)}
                  className="w-full mt-1 px-3 py-2 bg-muted/30 border border-border rounded-xl text-sm"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">Destination / Building</label>
                <input
                  type="text"
                  required
                  value={destination}
                  onChange={(e) => setDestination(e.target.value)}
                  className="w-full mt-1 px-3 py-2 bg-muted/30 border border-border rounded-xl text-sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Expected Arrival</label>
                  <input
                    type="datetime-local"
                    value={arrivalDate}
                    onChange={(e) => setArrivalDate(e.target.value)}
                    className="w-full mt-1 px-3 py-2 bg-muted/30 border border-border rounded-xl text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Expected Departure</label>
                  <input
                    type="datetime-local"
                    value={departureDate}
                    onChange={(e) => setDepartureDate(e.target.value)}
                    className="w-full mt-1 px-3 py-2 bg-muted/30 border border-border rounded-xl text-sm"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border border-border rounded-xl text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-primary text-primary-foreground font-semibold rounded-xl text-xs shadow-xs"
                >
                  Submit Pre-Registration
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

