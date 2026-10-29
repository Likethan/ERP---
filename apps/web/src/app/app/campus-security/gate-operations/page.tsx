"use client";

import React, { useEffect, useState } from "react";
import {
  AlertOctagon,
  AlertTriangle,
  Check,
  CheckCircle2,
  Clock,
  DoorOpen,
  LogOut,
  QrCode,
  Search,
  Shield,
  ShieldAlert,
  XCircle,
} from "lucide-react";
import { SecurityNav } from "@/components/campus-security/security-nav";
import { CampusSecurityService } from "@/services/campus-security.service";
import { SecurityCheckpoint, VisitorPass } from "@/types/campus-security";

export default function GateOperationsPage() {
  const [passes, setPasses] = useState<VisitorPass[]>([]);
  const [checkpoints, setCheckpoints] = useState<SecurityCheckpoint[]>([]);
  const [selectedCheckpoint, setSelectedCheckpoint] = useState<string>("");
  const [qrTokenInput, setQrTokenInput] = useState("");
  const [verifiedPass, setVerifiedPass] = useState<VisitorPass | null>(null);
  const [tokenError, setTokenError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [vehicleNumber, setVehicleNumber] = useState("");
  const [loading, setLoading] = useState(true);

  // Revoke Dialog State
  const [revokeModalPass, setRevokeModalPass] = useState<VisitorPass | null>(null);
  const [revokeReason, setRevokeReason] = useState("");

  async function loadData() {
    try {
      const [allPasses, chkpts] = await Promise.all([
        CampusSecurityService.listPasses(),
        CampusSecurityService.listCheckpoints(),
      ]);
      setPasses(allPasses);
      setCheckpoints(chkpts);
      if (chkpts.length > 0 && !selectedCheckpoint) {
        setSelectedCheckpoint(chkpts[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleVerifyToken(e: React.FormEvent) {
    e.preventDefault();
    setTokenError(null);
    setVerifiedPass(null);
    if (!qrTokenInput.trim()) return;

    try {
      const pass = await CampusSecurityService.verifyPassToken(qrTokenInput.trim());
      setVerifiedPass(pass);
    } catch (err) {
      setTokenError((err as Error).message);
    }
  }

  async function handleGateCheckIn(passId: string) {
    try {
      const chkptId = selectedCheckpoint || checkpoints[0]?.id || "chkpt-001";
      await CampusSecurityService.gateCheckIn(passId, chkptId, vehicleNumber);
      setVerifiedPass(null);
      setQrTokenInput("");
      setVehicleNumber("");
      loadData();
    } catch (err) {
      alert("Check-in error: " + (err as Error).message);
    }
  }

  async function handleGateCheckOut(passId: string) {
    try {
      const chkptId = selectedCheckpoint || checkpoints[0]?.id || "chkpt-001";
      await CampusSecurityService.gateCheckOut(passId, chkptId);
      loadData();
    } catch (err) {
      alert("Check-out error: " + (err as Error).message);
    }
  }

  async function handleRevokeSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!revokeModalPass) return;
    try {
      await CampusSecurityService.revokePass(revokeModalPass.id, revokeReason);
      setRevokeModalPass(null);
      setRevokeReason("");
      loadData();
    } catch (err) {
      alert("Revocation error: " + (err as Error).message);
    }
  }

  const filteredPasses = passes.filter((p) => {
    if (statusFilter === "ALL") return true;
    return p.status === statusFilter;
  });

  return (
    <div className="min-h-screen bg-background text-foreground pb-16">
      <SecurityNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-black tracking-tight">Gate Operations & Access Verification</h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Live checkpoint terminal for fast biometric turnstile, vehicle gate, and visitor pass verification.
            </p>
          </div>

          <div className="flex items-center space-x-3 bg-card border border-border p-2 rounded-xl">
            <span className="text-xs font-semibold text-muted-foreground pl-2">Current Post:</span>
            <select
              value={selectedCheckpoint}
              onChange={(e) => setSelectedCheckpoint(e.target.value)}
              className="bg-muted/40 border border-border rounded-lg px-3 py-1.5 text-xs font-bold text-foreground focus:outline-none"
            >
              {checkpoints.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.code} — {c.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* QR Scanner / Token Terminal */}
        <div className="bg-card border-2 border-primary/30 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
              <QrCode className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-base font-bold">Fast Pass Token Scanner</h2>
              <p className="text-xs text-muted-foreground">
                Scan barcode or paste cryptographically signed visitor QR token (HMAC-SHA256 authenticated)
              </p>
            </div>
          </div>

          <form onSubmit={handleVerifyToken} className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <input
                type="text"
                placeholder="Scan or enter token (e.g. VT-tenant-default:VP-2026-0081:...)"
                value={qrTokenInput}
                onChange={(e) => setQrTokenInput(e.target.value)}
                className="w-full px-4 py-2.5 bg-muted/30 border border-border rounded-xl text-xs font-mono focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <button
              type="submit"
              className="px-5 py-2.5 bg-primary text-primary-foreground font-semibold rounded-xl text-xs shadow-xs hover:opacity-90 transition-all shrink-0"
            >
              Verify Token
            </button>
          </form>

          {/* Verification Result Card */}
          {tokenError && (
            <div className="p-4 bg-destructive/10 border border-destructive/30 rounded-xl text-destructive flex items-center space-x-3 text-xs font-semibold">
              <XCircle className="h-5 w-5 shrink-0" />
              <span>{tokenError}</span>
            </div>
          )}

          {verifiedPass && (
            <div className="p-5 bg-emerald-500/10 border border-emerald-500/30 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                  <span className="font-bold text-sm text-foreground">
                    Verified: {verifiedPass.visitor_name}
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-sm bg-emerald-500/20 text-emerald-400">
                    {verifiedPass.pass_number}
                  </span>
                </div>
                <div className="text-xs text-muted-foreground">
                  Host: <span className="text-foreground">{verifiedPass.host_name}</span> • Dest:{" "}
                  <span className="text-foreground">{verifiedPass.destination}</span>
                </div>
                <div className="text-[11px] text-muted-foreground">
                  Valid Until: {new Date(verifiedPass.valid_until).toLocaleString()}
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <input
                  type="text"
                  placeholder="Vehicle plate (optional)"
                  value={vehicleNumber}
                  onChange={(e) => setVehicleNumber(e.target.value)}
                  className="px-3 py-1.5 bg-background border border-border rounded-lg text-xs"
                />
                <button
                  type="button"
                  onClick={() => handleGateCheckIn(verifiedPass.id)}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold shadow-xs transition-colors"
                >
                  Confirm Check-in
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Passes Table */}
        <div className="bg-card border border-border rounded-2xl overflow-hidden shadow-xs">
          <div className="p-5 border-b border-border flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <h2 className="font-bold text-base">All Visitor Passes</h2>
              <p className="text-xs text-muted-foreground">
                Track arrivals, active sessions, overdue departures, and revocations
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-1.5 bg-muted/40 border border-border rounded-lg text-xs focus:outline-none"
              >
                <option value="ALL">All Statuses</option>
                <option value="CHECKED_IN">Checked-In</option>
                <option value="ISSUED">Issued (Expected)</option>
                <option value="CHECKED_OUT">Checked-Out</option>
                <option value="OVERDUE">Overdue</option>
                <option value="REVOKED">Revoked</option>
              </select>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-muted/50 border-b border-border text-xs text-muted-foreground uppercase font-semibold">
                <tr>
                  <th className="px-5 py-3.5">Pass / Guest</th>
                  <th className="px-5 py-3.5">Host & Destination</th>
                  <th className="px-5 py-3.5">Validity Window</th>
                  <th className="px-5 py-3.5">Check-In / Out</th>
                  <th className="px-5 py-3.5">Status</th>
                  <th className="px-5 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {filteredPasses.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-5 py-8 text-center text-muted-foreground">
                      No visitor passes matching filter.
                    </td>
                  </tr>
                ) : (
                  filteredPasses.map((p) => (
                    <tr key={p.id} className="hover:bg-muted/20 transition-colors">
                      <td className="px-5 py-4">
                        <div className="font-bold text-sm">{p.visitor_name}</div>
                        <div className="text-xs text-muted-foreground font-mono">
                          {p.pass_number} • {p.visitor_category}
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <div className="font-medium text-xs">{p.host_name}</div>
                        <div className="text-[11px] text-muted-foreground">{p.destination}</div>
                      </td>
                      <td className="px-5 py-4 text-xs">
                        <div>Till {new Date(p.valid_until).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</div>
                        <div className="text-[11px] text-muted-foreground">
                          {new Date(p.valid_until).toLocaleDateString()}
                        </div>
                      </td>
                      <td className="px-5 py-4 text-xs text-muted-foreground">
                        {p.check_in_at ? (
                          <div>In: {new Date(p.check_in_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</div>
                        ) : (
                          <div>Not entered</div>
                        )}
                        {p.check_out_at && (
                          <div>Out: {new Date(p.check_out_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</div>
                        )}
                      </td>
                      <td className="px-5 py-4">
                        <span
                          className={`text-xs px-2.5 py-1 rounded-full font-bold ${
                            p.status === "CHECKED_IN"
                              ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20"
                              : p.status === "OVERDUE"
                              ? "bg-rose-500/10 text-rose-500 border border-rose-500/20"
                              : p.status === "REVOKED"
                              ? "bg-zinc-800 text-rose-400 border border-rose-900"
                              : "bg-muted text-muted-foreground"
                          }`}
                        >
                          {p.status}
                        </span>
                      </td>
                      <td className="px-5 py-4 text-right">
                        <div className="flex items-center justify-end space-x-2">
                          {p.status === "ISSUED" && (
                            <button
                              onClick={() => handleGateCheckIn(p.id)}
                              className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-lg text-xs"
                            >
                              Check-In
                            </button>
                          )}
                          {p.status === "CHECKED_IN" && (
                            <button
                              onClick={() => handleGateCheckOut(p.id)}
                              className="px-3 py-1 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold rounded-lg text-xs flex items-center space-x-1"
                            >
                              <LogOut className="h-3.5 w-3.5" />
                              <span>Check-Out</span>
                            </button>
                          )}
                          {p.status !== "REVOKED" && p.status !== "CHECKED_OUT" && (
                            <button
                              onClick={() => setRevokeModalPass(p)}
                              className="px-2.5 py-1 text-xs text-rose-500 hover:bg-rose-500/10 rounded-lg font-medium"
                            >
                              Revoke
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* Revoke Modal */}
      {revokeModalPass && (
        <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-2xl w-full max-w-md p-6 space-y-4 shadow-xl">
            <div className="flex items-center space-x-2 text-rose-500">
              <AlertOctagon className="h-6 w-6" />
              <h3 className="font-bold text-lg">Revoke Visitor Pass</h3>
            </div>
            <p className="text-xs text-muted-foreground">
              Are you sure you want to cancel access for{" "}
              <strong className="text-foreground">{revokeModalPass.visitor_name}</strong> (Pass{" "}
              {revokeModalPass.pass_number})? This action is immediately audited.
            </p>

            <form onSubmit={handleRevokeSubmit} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-muted-foreground">
                  Reason for Revocation
                </label>
                <textarea
                  required
                  rows={3}
                  value={revokeReason}
                  onChange={(e) => setRevokeReason(e.target.value)}
                  placeholder="Specify violation or security alert details..."
                  className="w-full mt-1 px-3 py-2 bg-muted/30 border border-border rounded-xl text-xs"
                />
              </div>

              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setRevokeModalPass(null)}
                  className="px-4 py-2 border border-border rounded-xl text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white font-semibold rounded-xl text-xs shadow-xs"
                >
                  Confirm Revocation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

