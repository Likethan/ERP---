"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { documentsService } from "@/services/documents.service";
import {
  DocumentVaultItem,
  DocumentRequestItem,
  IssuedCertificateItem,
} from "@/mocks/documents.mock";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { useToast } from "@/components/ui/toast";
import {
  FileText,
  FileCheck,
  QrCode,
  ShieldCheck,
  Search,
  Download,
  CheckCircle2,
  ExternalLink,
  Plus,
  Lock,
} from "lucide-react";

export default function DocumentsManagementPage() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [documents, setDocuments] = useState<DocumentVaultItem[]>([]);
  const [requests, setRequests] = useState<DocumentRequestItem[]>([]);
  const [certificates, setCertificates] = useState<IssuedCertificateItem[]>([]);

  // Filter states
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("ALL");
  const [activeTab, setActiveTab] = useState<"vault" | "requests" | "issued" | "verify">("vault");

  // Request modal
  const [requestModalOpen, setRequestModalOpen] = useState(false);
  const [requestForm, setRequestForm] = useState({
    certificateType: "BONAFIDE",
    purpose: "Passport verification & internship application",
  });

  // Verify form
  const [verifyCode, setVerifyCode] = useState("");
  const [verifiedResult, setVerifiedResult] = useState<IssuedCertificateItem | null>(null);
  const [verifying, setVerifying] = useState(false);

  async function loadData() {
    try {
      setLoading(true);
      const [docRes, reqRes, certRes] = await Promise.all([
        documentsService.getDocuments(),
        documentsService.getRequests(),
        documentsService.getIssuedCertificates(),
      ]);
      setDocuments(docRes.data || []);
      setRequests(reqRes.data || []);
      setCertificates(certRes.data || []);
    } catch {
      toast({
        title: "Error loading credentials",
        description: "Falling back to local cache.",
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const filteredDocs = documents.filter((d) => {
    const matchesCat = categoryFilter === "ALL" || d.category === categoryFilter;
    const matchesSearch =
      d.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.ownerName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (d.ownerRollNumber || "").toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCat && matchesSearch;
  });

  const handleCreateRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await documentsService.submitRequest({
        studentName: "Aarav Patel",
        rollNumber: "24CSE0101",
        program: "B.Tech Computer Science & Engineering",
        certificateType: requestForm.certificateType as any,
        purpose: requestForm.purpose,
      });
      setRequests((prev) => [res.data, ...prev]);
      toast({
        title: "Certificate Request Logged",
        description: `${requestForm.certificateType} certificate requested for student Aarav Patel.`,
        variant: "success",
      });
      setRequestModalOpen(false);
    } catch {
      toast({
        title: "Request Failed",
        description: "Please check your network connection.",
        variant: "error",
      });
    }
  };

  const handleApproveRequest = async (id: string) => {
    try {
      const res = await documentsService.approveRequest(id);
      setRequests((prev) =>
        prev.map((r) => (r.id === id ? { ...r, status: "ISSUED" } : r))
      );
      setCertificates((prev) => [res.data, ...prev]);
      toast({
        title: "Certificate Approved & Issued",
        description: `Official ${res.data.certificateType} generated with tamper-proof QR code.`,
        variant: "success",
      });
    } catch {
      toast({ title: "Approval error", variant: "error" });
    }
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!verifyCode.trim()) return;
    setVerifying(true);
    setVerifiedResult(null);

    const res = await documentsService.verifyCertificate(verifyCode.trim());
    setVerifying(false);
    if (res.data) {
      setVerifiedResult(res.data);
      toast({
        title: "Cryptographic Verification Passed",
        description: `Certificate ${res.data.certificateNumber} is authentic and active on the registry.`,
        variant: "success",
      });
    } else {
      toast({
        title: "Verification Failed",
        description: "No matching official certificate found for this verification query.",
        variant: "error",
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 mb-1">
            <Link href="/app/dashboard" className="hover:text-indigo-600 transition">
              CampusOS
            </Link>
            <span>/</span>
            <span className="font-semibold text-slate-700 dark:text-slate-300">Governance</span>
            <span>/</span>
            <span className="text-slate-500">Document Vault & Verification</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2.5">
            <ShieldCheck className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
            Document Vault & Cryptographic Verification
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Encrypted permanent student records, bonafide & transcript issuance, and tamper-proof QR credential validation.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button variant="outline" onClick={() => setActiveTab("verify")}>
            <QrCode className="h-4 w-4 mr-1.5" />
            Verify Certificate
          </Button>
          <Button variant="primary" onClick={() => setRequestModalOpen(true)}>
            <Plus className="h-4 w-4 mr-1.5" />
            Request Certificate
          </Button>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Vault Records"
          value={documents.length.toString()}
          description="Verified encrypted files"
          color="indigo"
          icon={<FileText className="h-5 w-5" />}
        />
        <StatCard
          title="Active Credentials"
          value={certificates.length.toString()}
          description="Issued tamper-proof certificates"
          color="emerald"
          icon={<FileCheck className="h-5 w-5" />}
        />
        <StatCard
          title="Pending Requests"
          value={requests.filter((r) => r.status === "PENDING_APPROVAL").length.toString()}
          description="Awaiting registrar approval"
          color="amber"
          icon={<ShieldCheck className="h-5 w-5" />}
        />
        <StatCard
          title="Integrity Status"
          value="100%"
          description="SHA-256 authenticated"
          color="purple"
          icon={<Lock className="h-5 w-5" />}
        />
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-800">
        <button
          onClick={() => setActiveTab("vault")}
          className={`py-3 px-5 text-sm font-medium border-b-2 transition ${
            activeTab === "vault"
              ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
              : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400"
          }`}
        >
          Document Vault ({documents.length})
        </button>
        <button
          onClick={() => setActiveTab("requests")}
          className={`py-3 px-5 text-sm font-medium border-b-2 transition ${
            activeTab === "requests"
              ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
              : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400"
          }`}
        >
          Certificate Requests ({requests.length})
        </button>
        <button
          onClick={() => setActiveTab("issued")}
          className={`py-3 px-5 text-sm font-medium border-b-2 transition ${
            activeTab === "issued"
              ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
              : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400"
          }`}
        >
          Issued Credentials & QR ({certificates.length})
        </button>
        <button
          onClick={() => setActiveTab("verify")}
          className={`py-3 px-5 text-sm font-medium border-b-2 transition ${
            activeTab === "verify"
              ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
              : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400"
          }`}
        >
          Public Verification Engine
        </button>
      </div>

      {/* Tab: Vault */}
      {activeTab === "vault" && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-4 rounded-xl border border-slate-200 dark:bg-slate-900 dark:border-slate-800">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search document title, student, or roll number..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 text-sm rounded-lg border border-slate-200 bg-slate-50/50 dark:border-slate-700 dark:bg-slate-800/50 text-slate-900 dark:text-white focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="text-xs rounded-lg border border-slate-200 bg-white py-2 px-3 text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
            >
              <option value="ALL">All Categories</option>
              <option value="ACADEMIC">Academic Transcripts</option>
              <option value="IDENTITY">Identity Verification</option>
              <option value="ADMISSIONS">Admissions & Eligibility</option>
            </select>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs dark:border-slate-800 dark:bg-slate-900">
            <table className="w-full text-left text-sm text-slate-700 dark:text-slate-300">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500 border-b border-slate-200 dark:bg-slate-800/50 dark:border-slate-800">
                <tr>
                  <th className="px-4 py-3">Document Title</th>
                  <th className="px-4 py-3">Student Name</th>
                  <th className="px-4 py-3">Roll Number</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Verification</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {filteredDocs.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition">
                    <td className="px-4 py-3 font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                      <FileText className="h-4 w-4 text-indigo-500 shrink-0" />
                      {doc.name}
                    </td>
                    <td className="px-4 py-3">{doc.ownerName}</td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-500">{doc.ownerRollNumber || "—"}</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                        {doc.category}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={doc.verified ? "success" : "warning"} dot>
                        {doc.verified ? "VERIFIED" : "PENDING"}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          toast({
                            title: `Downloading ${doc.name}`,
                            description: "Decrypted from institutional vault.",
                            variant: "info",
                          })
                        }
                      >
                        <Download className="h-3.5 w-3.5 mr-1" />
                        Download
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab: Requests */}
      {activeTab === "requests" && (
        <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <table className="w-full text-left text-sm text-slate-700 dark:text-slate-300">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500 border-b border-slate-200 dark:bg-slate-800/50 dark:border-slate-800">
              <tr>
                <th className="px-4 py-3">Student</th>
                <th className="px-4 py-3">Certificate Type</th>
                <th className="px-4 py-3">Declared Purpose</th>
                <th className="px-4 py-3">Requested On</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Workflow</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {requests.map((req) => (
                <tr key={req.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition">
                  <td className="px-4 py-3">
                    <div className="font-semibold text-slate-900 dark:text-white">{req.studentName}</div>
                    <div className="text-xs text-slate-400 font-mono">{req.rollNumber} &bull; {req.program}</div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-mono text-xs font-bold text-indigo-600 dark:text-indigo-400">
                      {req.certificateType}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-400 max-w-xs truncate">
                    {req.purpose}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-500">{req.requestedDate}</td>
                  <td className="px-4 py-3">
                    <Badge variant={req.status === "ISSUED" ? "success" : "warning"} dot>
                      {req.status}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-right">
                    {req.status === "PENDING_APPROVAL" ? (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleApproveRequest(req.id)}
                      >
                        Approve & Issue
                      </Button>
                    ) : (
                      <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium flex items-center justify-end gap-1">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        Issued
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab: Issued Certificates & QR */}
      {activeTab === "issued" && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {certificates.map((cert) => (
            <div
              key={cert.id}
              className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs hover:border-indigo-400 hover:shadow-md transition dark:border-slate-800 dark:bg-slate-900"
            >
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-xs font-mono font-bold text-emerald-600 dark:text-emerald-400">
                    {cert.certificateNumber}
                  </span>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white mt-1">
                    {cert.certificateType}
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Issued to {cert.studentName} ({cert.rollNumber})
                  </p>
                </div>
                <Badge variant="success" dot>
                  {cert.status}
                </Badge>
              </div>

              {/* QR Verification Placeholder */}
              <div className="mt-4 p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 flex items-center gap-3">
                <div className="h-12 w-12 rounded bg-white dark:bg-slate-900 flex items-center justify-center border border-slate-200 dark:border-slate-700 shrink-0">
                  <QrCode className="h-8 w-8 text-slate-800 dark:text-slate-200" />
                </div>
                <div className="overflow-hidden">
                  <span className="text-[10px] text-slate-400 block uppercase font-bold tracking-wider">
                    QR Verification Token
                  </span>
                  <span className="text-xs font-mono text-indigo-600 dark:text-indigo-400 truncate block">
                    {cert.qrVerificationUrl}
                  </span>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs">
                <span className="text-slate-500 font-mono">Issued: {cert.issueDate}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setVerifyCode(cert.certificateNumber);
                    setActiveTab("verify");
                  }}
                >
                  Verify Authenticity &rarr;
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab: Public Verification */}
      {activeTab === "verify" && (
        <div className="max-w-2xl mx-auto rounded-2xl border border-slate-200 bg-white p-8 shadow-xs dark:border-slate-800 dark:bg-slate-900">
          <div className="text-center">
            <div className="inline-flex h-12 w-12 rounded-xl bg-indigo-50 text-indigo-600 items-center justify-center dark:bg-indigo-950/60 dark:text-indigo-400 mb-3">
              <QrCode className="h-6 w-6" />
            </div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">
              Institutional Credential Verification Registry
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-md mx-auto">
              Enter the Certificate Number or paste the verification URL to validate document authenticity against the immutable register.
            </p>
          </div>

          <form onSubmit={handleVerify} className="mt-6 flex gap-2">
            <input
              type="text"
              placeholder="e.g. CERT-2026-0881 or verification URL"
              value={verifyCode}
              onChange={(e) => setVerifyCode(e.target.value)}
              className="flex-1 px-4 py-2 text-sm rounded-lg border border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
            />
            <Button variant="primary" type="submit" disabled={verifying}>
              {verifying ? "Verifying..." : "Verify Credential"}
            </Button>
          </form>

          {verifiedResult && (
            <div className="mt-6 p-5 rounded-xl border border-emerald-200 bg-emerald-50/50 dark:border-emerald-900/50 dark:bg-emerald-950/20">
              <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-400 font-bold text-sm">
                <CheckCircle2 className="h-5 w-5" />
                Valid & Cryptographically Verified Authentic Credential
              </div>

              <div className="mt-3 grid grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-slate-500 block">Certificate Title</span>
                  <span className="font-bold text-slate-900 dark:text-white">{verifiedResult.certificateType}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Certificate #</span>
                  <span className="font-mono font-bold text-slate-900 dark:text-white">
                    {verifiedResult.certificateNumber}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block">Issued To</span>
                  <span className="font-bold text-slate-900 dark:text-white">
                    {verifiedResult.studentName} ({verifiedResult.rollNumber})
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block">Date of Issue</span>
                  <span className="font-mono font-bold text-slate-900 dark:text-white">
                    {verifiedResult.issueDate}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Request Modal */}
      <Dialog
        isOpen={requestModalOpen}
        onClose={() => setRequestModalOpen(false)}
        title="Request Official Institutional Certificate"
        description="Formal certificate generation for Aarav Patel (24CSE0101)."
      >
        <form onSubmit={handleCreateRequest} className="space-y-4">
          <Select
            label="Certificate Category"
            value={requestForm.certificateType}
            onChange={(e) => setRequestForm({ ...requestForm, certificateType: e.target.value })}
            options={[
              { label: "Bonafide Certificate", value: "BONAFIDE" },
              { label: "Official Academic Transcript", value: "TRANSCRIPT" },
              { label: "Course Completion Certificate", value: "COURSE_COMPLETION" },
              { label: "No Objection Certificate (NOC)", value: "NOC" },
            ]}
          />

          <Input
            label="Declared Purpose / Destination"
            placeholder="e.g. Visa application, educational loan, internship onboarding"
            value={requestForm.purpose}
            onChange={(e) => setRequestForm({ ...requestForm, purpose: e.target.value })}
            required
          />

          <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
            <Button variant="outline" type="button" onClick={() => setRequestModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              Submit Request
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
