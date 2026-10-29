"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  Calendar,
  CheckCircle2,
  Clock,
  Download,
  ExternalLink,
  Eye,
  FileCheck2,
  FileText,
  Filter,
  Plus,
  Search,
  ShieldCheck,
  Upload,
  X,
  XCircle,
} from "lucide-react";
import { InternationalNav } from "@/components/international/international-nav";
import { internationalService } from "@/services/international.service";
import { MobilityDocument } from "@/types/international";

export default function DocumentsChecklistPage() {
  const [documents, setDocuments] = useState<MobilityDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [selectedDocForVerification, setSelectedDocForVerification] = useState<MobilityDocument | null>(null);
  const [verifyStatus, setVerifyStatus] = useState<"VERIFIED" | "REJECTED">("VERIFIED");
  const [rejectionReason, setRejectionReason] = useState("");
  const [submittingVerification, setSubmittingVerification] = useState(false);

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  async function loadData() {
    setLoading(true);
    try {
      const data = await internationalService.getDocuments({
        verification_status: statusFilter !== "ALL" ? statusFilter : undefined,
      });
      setDocuments(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleVerify(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedDocForVerification) return;
    setSubmittingVerification(true);
    try {
      await internationalService.verifyDocument(
        selectedDocForVerification.id,
        verifyStatus,
        rejectionReason
      );
      alert(`Document ${verifyStatus.toLowerCase()} successfully.`);
      setSelectedDocForVerification(null);
      setRejectionReason("");
      loadData();
    } catch (err) {
      console.error(err);
      alert("Failed to verify document");
    } finally {
      setSubmittingVerification(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <InternationalNav />

      <main className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <FileCheck2 className="h-5 w-5 text-cyan-400" />
              Mobility Documents & Compliance Verification
            </h2>
            <p className="text-xs text-slate-400">
              Administrative repository for passports, health coverage certificates, official transcripts, and foreign visas
            </p>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="ALL">All Document Statuses</option>
              <option value="PENDING">Pending Verification</option>
              <option value="VERIFIED">Verified</option>
              <option value="REJECTED">Rejected</option>
            </select>
          </div>
        </div>

        {/* Documents Table */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider text-[10px] border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Document Title & Filename</th>
                  <th className="py-3 px-4">Classification</th>
                  <th className="py-3 px-4">Expiry Date</th>
                  <th className="py-3 px-4">Verification Status</th>
                  <th className="py-3 px-4 text-right">Verification Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {loading ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-500">
                      Loading mobility documents...
                    </td>
                  </tr>
                ) : documents.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-500">
                      No documents found for this filter.
                    </td>
                  </tr>
                ) : (
                  documents.map((doc) => (
                    <tr key={doc.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-white flex items-center gap-2">
                          <FileText className="h-4 w-4 text-cyan-400" />
                          <span>{doc.document_name || doc.documentName}</span>
                        </div>
                        {doc.application_id && (
                          <div className="text-[11px] text-slate-500 font-mono mt-0.5 ml-6">
                            App: {doc.application_id}
                          </div>
                        )}
                      </td>

                      <td className="py-3.5 px-4 font-mono text-slate-300">
                        {doc.document_type || doc.documentType}
                      </td>

                      <td className="py-3.5 px-4 text-slate-400">
                        {doc.document_expiry_date || doc.documentExpiryDate || "Indefinite"}
                      </td>

                      <td className="py-3.5 px-4">
                        <span
                          className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase ${
                            (doc.verification_status || doc.verificationStatus) === "VERIFIED"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                              : (doc.verification_status || doc.verificationStatus) === "REJECTED"
                              ? "bg-rose-500/10 text-rose-300 border border-rose-500/30"
                              : "bg-amber-500/10 text-amber-300 border border-amber-500/30"
                          }`}
                        >
                          {doc.verification_status || doc.verificationStatus}
                        </span>
                      </td>

                      <td className="py-3.5 px-4 text-right space-x-2">
                        <a
                          href={doc.file_storage_url || doc.fileStorageUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium inline-flex items-center gap-1 transition-colors"
                        >
                          <Eye className="h-3.5 w-3.5 text-cyan-400" />
                          View
                        </a>
                        <button
                          onClick={() => {
                            setSelectedDocForVerification(doc);
                            setVerifyStatus("VERIFIED");
                          }}
                          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs font-medium transition-colors"
                        >
                          Audit Document
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Audit Document Modal */}
        {selectedDocForVerification && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
              <button
                onClick={() => setSelectedDocForVerification(null)}
                className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>

              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-cyan-400" />
                Audit & Verify Mobility Document
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Document: <strong className="text-slate-200">{selectedDocForVerification.document_name}</strong> (
                {selectedDocForVerification.document_type})
              </p>

              <form onSubmit={handleVerify} className="mt-5 space-y-4">
                <div>
                  <label className="text-xs font-medium text-slate-300 block mb-1">Verification Status *</label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={() => setVerifyStatus("VERIFIED")}
                      className={`py-2 px-3 rounded-lg text-xs font-bold border transition-all ${
                        verifyStatus === "VERIFIED"
                          ? "bg-emerald-600 border-emerald-500 text-white"
                          : "bg-slate-950 border-slate-800 text-slate-400 hover:text-white"
                      }`}
                    >
                      VERIFY AS AUTHENTIC
                    </button>
                    <button
                      type="button"
                      onClick={() => setVerifyStatus("REJECTED")}
                      className={`py-2 px-3 rounded-lg text-xs font-bold border transition-all ${
                        verifyStatus === "REJECTED"
                          ? "bg-rose-600 border-rose-500 text-white"
                          : "bg-slate-950 border-slate-800 text-slate-400 hover:text-white"
                      }`}
                    >
                      REJECT (Unclear / Expired)
                    </button>
                  </div>
                </div>

                {verifyStatus === "REJECTED" && (
                  <div>
                    <label className="text-xs font-medium text-slate-300 block mb-1">Reason for Rejection *</label>
                    <input
                      required
                      type="text"
                      placeholder="e.g. Passport scan unreadable or expires within 6 months of travel."
                      value={rejectionReason}
                      onChange={(e) => setRejectionReason(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                )}

                <div className="mt-6 flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setSelectedDocForVerification(null)}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submittingVerification}
                    className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md shadow-cyan-900/30 disabled:opacity-50"
                  >
                    {submittingVerification ? "Committing..." : "Commit Verification"}
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
