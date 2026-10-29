"use client";

import React, { useEffect, useState } from "react";
import {
  Briefcase,
  CheckCircle2,
  FileBadge,
  HardHat,
  Plus,
  Shield,
  ShieldAlert,
  UserCheck,
  XCircle,
} from "lucide-react";
import { SecurityNav } from "@/components/campus-security/security-nav";
import { CampusSecurityService } from "@/services/campus-security.service";
import { ContractorAccessProfile } from "@/types/campus-security";

export default function ContractorAccessPage() {
  const [contractors, setContractors] = useState<ContractorAccessProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  // Form State
  const [orgName, setOrgName] = useState("");
  const [contractorName, setContractorName] = useState("");
  const [phone, setPhone] = useState("");
  const [serviceType, setServiceType] = useState("");
  const [workOrder, setWorkOrder] = useState("");
  const [validUntil, setValidUntil] = useState("");
  const [safetyInducted, setSafetyInducted] = useState(false);

  async function loadData() {
    try {
      const data = await CampusSecurityService.listContractors();
      setContractors(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      await CampusSecurityService.createContractor({
        organization_name: orgName,
        contractor_name: contractorName,
        contractor_phone: phone,
        service_type: serviceType,
        work_order_reference: workOrder,
        valid_from: new Date().toISOString().split("T")[0],
        valid_until: validUntil || "2026-12-31",
        is_safety_induction_completed: safetyInducted,
      });
      setShowModal(false);
      setOrgName("");
      setContractorName("");
      setPhone("");
      setServiceType("");
      setWorkOrder("");
      setValidUntil("");
      setSafetyInducted(false);
      loadData();
    } catch (err) {
      alert("Error creating contractor profile: " + (err as Error).message);
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground pb-16">
      <SecurityNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-black tracking-tight">Contractor & Service Provider Access</h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Approved vendors, maintenance technicians, safety induction compliance, and work order badges.
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-primary text-primary-foreground font-semibold rounded-xl text-sm shadow-xs hover:opacity-90 transition-all"
          >
            <Plus className="h-4 w-4" />
            <span>Register Contractor</span>
          </button>
        </div>

        {/* Contractor Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {contractors.map((c) => (
            <div key={c.id} className="p-6 bg-card border border-border rounded-2xl shadow-xs space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-sm bg-muted text-muted-foreground">
                    {c.contractor_code}
                  </span>
                  <h3 className="font-bold text-base mt-1">{c.organization_name}</h3>
                  <div className="text-xs text-muted-foreground font-medium">{c.contractor_name}</div>
                </div>
                <span
                  className={`text-xs px-2.5 py-1 rounded-full font-bold ${
                    c.status === "ACTIVE"
                      ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20"
                      : "bg-rose-500/10 text-rose-500 border border-rose-500/20"
                  }`}
                >
                  {c.status}
                </span>
              </div>

              <div className="text-xs space-y-1.5 pt-2 border-t border-border/60 text-muted-foreground">
                <div className="flex items-center justify-between">
                  <span>Service:</span>
                  <span className="font-semibold text-foreground">{c.service_type}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Work Order:</span>
                  <span className="font-mono text-foreground">{c.work_order_reference || "Direct Campus MoU"}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Badge Ref:</span>
                  <span className="font-mono text-foreground">{c.badge_reference || "PENDING"}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Phone:</span>
                  <span className="text-foreground">{c.contractor_phone}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Valid Until:</span>
                  <span className="text-foreground">{c.valid_until}</span>
                </div>
              </div>

              {/* Safety Induction Verification */}
              <div
                className={`p-3 rounded-xl border flex items-center justify-between text-xs ${
                  c.is_safety_induction_completed
                    ? "bg-emerald-500/5 border-emerald-500/20 text-emerald-600 dark:text-emerald-400"
                    : "bg-amber-500/5 border-amber-500/20 text-amber-600 dark:text-amber-400"
                }`}
              >
                <div className="flex items-center space-x-2">
                  <HardHat className="h-4 w-4" />
                  <span className="font-semibold">
                    {c.is_safety_induction_completed ? "Safety Induction Certified" : "Induction Pending"}
                  </span>
                </div>
                {c.is_safety_induction_completed && (
                  <CheckCircle2 className="h-4 w-4 shrink-0" />
                )}
              </div>
            </div>
          ))}
        </div>
      </main>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-2xl w-full max-w-lg p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <h3 className="font-bold text-lg">Register Contractor or Service Provider</h3>
              <button onClick={() => setShowModal(false)} className="text-muted-foreground hover:text-foreground">
                ✕
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4 text-sm">
              <div>
                <label className="text-xs font-medium text-muted-foreground">Contractor / Vendor Organization</label>
                <input
                  type="text"
                  required
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  placeholder="e.g. Siemens Building Technologies Ltd"
                  className="w-full mt-1 px-3 py-2 bg-muted/30 border border-border rounded-xl text-sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Lead Contractor Name</label>
                  <input
                    type="text"
                    required
                    value={contractorName}
                    onChange={(e) => setContractorName(e.target.value)}
                    className="w-full mt-1 px-3 py-2 bg-muted/30 border border-border rounded-xl text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Contact Phone</label>
                  <input
                    type="tel"
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="w-full mt-1 px-3 py-2 bg-muted/30 border border-border rounded-xl text-sm"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Service / Trade Type</label>
                  <input
                    type="text"
                    required
                    value={serviceType}
                    onChange={(e) => setServiceType(e.target.value)}
                    placeholder="e.g. Electrical / HVAC / Plumbing"
                    className="w-full mt-1 px-3 py-2 bg-muted/30 border border-border rounded-xl text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground">Work Order Reference</label>
                  <input
                    type="text"
                    value={workOrder}
                    onChange={(e) => setWorkOrder(e.target.value)}
                    placeholder="e.g. WO-2026-90"
                    className="w-full mt-1 px-3 py-2 bg-muted/30 border border-border rounded-xl text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-muted-foreground">Validity Expiration Date</label>
                <input
                  type="date"
                  required
                  value={validUntil}
                  onChange={(e) => setValidUntil(e.target.value)}
                  className="w-full mt-1 px-3 py-2 bg-muted/30 border border-border rounded-xl text-sm"
                />
              </div>

              <div className="flex items-center space-x-2 pt-2">
                <input
                  type="checkbox"
                  id="safetyCheck"
                  checked={safetyInducted}
                  onChange={(e) => setSafetyInducted(e.target.checked)}
                  className="rounded text-primary focus:ring-primary"
                />
                <label htmlFor="safetyCheck" className="text-xs font-medium text-foreground cursor-pointer">
                  Mandatory Campus Safety & Fire Induction Completed
                </label>
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
                  Register Profile
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

