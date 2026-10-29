"use client";

import { useEffect, useState } from "react";
import {
  Award,
  CheckCircle2,
  Copy,
  ExternalLink,
  FileCheck2,
  Globe2,
  PlusCircle,
  QrCode,
  Search,
  ShieldCheck,
  UserCheck,
  X,
} from "lucide-react";
import { EngagementNav } from "@/components/engagement/engagement-nav";
import { EngagementService } from "@/services/engagement.service";
import {
  CertificateIssueInput,
  EngagementCertificate,
  EngagementProgram,
} from "@/types/engagement";

export default function EngagementCertificatesPage() {
  const [certificates, setCertificates] = useState<EngagementCertificate[]>([]);
  const [programs, setPrograms] = useState<EngagementProgram[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedCert, setSelectedCert] = useState<EngagementCertificate | null>(null);

  // Verification Dialog
  const [isVerifyOpen, setIsVerifyOpen] = useState(false);
  const [verifyHashInput, setVerifyHashInput] = useState("");
  const [verifiedCertResult, setVerifiedCertResult] = useState<EngagementCertificate | null>(null);
  const [verifyError, setVerifyError] = useState<string | null>(null);

  // Issue Certificate Modal
  const [isIssueOpen, setIsIssueOpen] = useState(false);
  const [progId, setProgId] = useState("");
  const [studentId, setStudentId] = useState("stu-101");
  const [issuedTitle, setIssuedTitle] = useState("Dean of Student Affairs & Civic Engagement");
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [certs, progs] = await Promise.all([
        EngagementService.listCertificates(),
        EngagementService.listPrograms(),
      ]);
      setCertificates(certs);
      setPrograms(progs);
      if (progs.length > 0) setProgId(progs[0].id);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function handleVerifyHash(e: React.FormEvent) {
    e.preventDefault();
    if (!verifyHashInput) return;
    setVerifyError(null);
    setVerifiedCertResult(null);

    try {
      const result = await EngagementService.verifyCertificateHash(verifyHashInput.trim());
      setVerifiedCertResult(result);
    } catch (err: any) {
      setVerifyError("Certificate hash could not be verified in institutional ledger.");
    }
  }

  async function handleIssueCertificate(e: React.FormEvent) {
    e.preventDefault();
    if (!progId || !studentId) return;

    try {
      const input: CertificateIssueInput = {
        student_id: studentId,
        program_id: progId,
        issued_by_title: issuedTitle,
      };

      await EngagementService.issueCertificate(input);
      setActionMessage("Certificate issued with tamper-evident cryptographic hash!");
      setIsIssueOpen(false);
      await loadData();
    } catch (err: any) {
      setActionMessage(`Error issuing certificate: ${err.message}`);
    }
  }

  const filteredCerts = certificates.filter((c) => {
    return (
      c.recipient_name.toLowerCase().includes(search.toLowerCase()) ||
      c.program_name.toLowerCase().includes(search.toLowerCase()) ||
      c.certificate_number.toLowerCase().includes(search.toLowerCase()) ||
      c.verification_hash.toLowerCase().includes(search.toLowerCase())
    );
  });

  return (
    <div className="min-h-screen bg-background">
      <EngagementNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {actionMessage && (
          <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-medium flex items-center justify-between">
            <span>{actionMessage}</span>
            <button onClick={() => setActionMessage(null)} className="text-muted-foreground hover:text-foreground">
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
              <Award className="h-6 w-6 text-purple-500" />
              Verified Co-Curricular Records & Certificates
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Tamper-evident credentials, cryptographic SHA-256 hash checks, and verified civic transcripts
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => {
                setVerifyHashInput("");
                setVerifiedCertResult(null);
                setVerifyError(null);
                setIsVerifyOpen(true);
              }}
              className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-lg border border-border text-foreground hover:bg-accent text-xs font-medium"
            >
              <QrCode className="h-4 w-4 text-purple-500" />
              <span>Verify Any Certificate</span>
            </button>
            <button
              onClick={() => setIsIssueOpen(true)}
              className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-semibold shadow hover:opacity-95"
            >
              <PlusCircle className="h-4 w-4" />
              <span>Issue Certificate</span>
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="bg-card border border-border rounded-xl p-4 shadow-sm">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search by student recipient, certificate number, or hash..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-lg border border-border bg-background text-xs focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
        </div>

        {/* Certificates Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredCerts.map((cert) => (
            <div
              key={cert.id}
              className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-4 hover:border-purple-500/50 transition-all flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-500 font-bold border border-purple-500/20">
                    {cert.certificate_number}
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500 font-semibold">
                    {cert.status}
                  </span>
                </div>

                <div>
                  <h3 className="text-base font-bold text-foreground line-clamp-1">
                    {cert.recipient_name}
                  </h3>
                  <p className="text-xs text-muted-foreground line-clamp-1 mt-0.5">
                    {cert.program_name}
                  </p>
                </div>

                <div className="bg-muted/30 p-3 rounded-lg border border-border space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Verified Service:</span>
                    <span className="font-bold text-foreground">{cert.total_verified_hours} Hours</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Issuance Date:</span>
                    <span className="text-foreground">{new Date(cert.issued_at).toLocaleDateString()}</span>
                  </div>
                </div>

                {cert.skills_recognized && cert.skills_recognized.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {cert.skills_recognized.map((s, i) => (
                      <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-foreground">
                        {s}
                      </span>
                    ))}
                  </div>
                )}

                <div className="p-2 rounded bg-muted/50 border border-border text-[10px] font-mono text-muted-foreground break-all">
                  <span className="text-purple-500 font-semibold block text-[9px] uppercase font-sans">
                    SHA-256 Ledger Hash:
                  </span>
                  {cert.verification_hash}
                </div>
              </div>

              <div className="border-t border-border pt-3">
                <button
                  onClick={() => setSelectedCert(cert)}
                  className="w-full py-1.5 rounded-lg border border-border text-foreground hover:bg-accent text-xs font-medium text-center"
                >
                  View Credential & QR Verification
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Certificate Credential View Modal */}
        {selectedCert && (
          <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-card border-2 border-purple-500/30 rounded-2xl max-w-xl w-full p-8 shadow-2xl space-y-5 text-center text-xs">
              <div className="space-y-1">
                <div className="flex justify-center mb-2">
                  <div className="p-3 bg-purple-500/10 rounded-full border border-purple-500/20">
                    <Award className="h-8 w-8 text-purple-500" />
                  </div>
                </div>
                <span className="text-[10px] text-muted-foreground uppercase tracking-widest block">
                  CampusOS — Office of Civic Engagement
                </span>
                <h2 className="text-xl font-extrabold text-foreground tracking-tight">
                  Certificate of Community Service & Civic Impact
                </h2>
                <span className="text-[11px] font-mono text-purple-500 font-bold">
                  {selectedCert.certificate_number}
                </span>
              </div>

              <div className="border-y border-border py-4 space-y-2">
                <p className="text-xs text-muted-foreground">This is to officially certify that</p>
                <h3 className="text-lg font-bold text-foreground">{selectedCert.recipient_name}</h3>
                <p className="text-xs text-muted-foreground max-w-md mx-auto">
                  has successfully performed <span className="font-bold text-foreground">{selectedCert.total_verified_hours} verified service hours</span> in community service and institutional civic mission:
                </p>
                <p className="text-sm font-semibold text-foreground italic">&ldquo;{selectedCert.program_name}&rdquo;</p>
              </div>

              <div className="text-[11px] text-muted-foreground space-y-1">
                <p>Issued by: <span className="font-semibold text-foreground">{selectedCert.issued_by_title}</span></p>
                <p>Date of Award: {new Date(selectedCert.issued_at).toLocaleDateString()}</p>
              </div>

              <div className="bg-muted/40 p-3 rounded-lg border border-border text-left font-mono text-[10px] space-y-1 break-all">
                <div className="flex items-center justify-between font-sans text-foreground font-semibold">
                  <span>Cryptographic Proof</span>
                  <ShieldCheck className="h-4 w-4 text-emerald-500" />
                </div>
                <p className="text-muted-foreground">{selectedCert.verification_hash}</p>
              </div>

              <div className="flex justify-center gap-3 pt-2">
                <button
                  onClick={() => setSelectedCert(null)}
                  className="px-5 py-2 rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 font-medium"
                >
                  Close Record
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Verify Any Certificate Modal */}
        {isVerifyOpen && (
          <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-card border border-border rounded-xl max-w-md w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto text-xs">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <h2 className="text-base font-bold text-foreground flex items-center gap-2">
                  <ShieldCheck className="h-5 w-5 text-purple-500" />
                  Verify Credential Authenticity
                </h2>
                <button onClick={() => setIsVerifyOpen(false)} className="text-muted-foreground hover:text-foreground">
                  <X className="h-4 w-4" />
                </button>
              </div>

              <form onSubmit={handleVerifyHash} className="space-y-4">
                <div className="space-y-1">
                  <label className="font-semibold text-foreground">SHA-256 Certificate Hash</label>
                  <input
                    type="text"
                    required
                    placeholder="Enter 64-character SHA-256 hash or scan QR..."
                    value={verifyHashInput}
                    onChange={(e) => setVerifyHashInput(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground font-mono text-[11px]"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full py-2 rounded-lg bg-primary text-primary-foreground font-semibold shadow hover:opacity-95"
                >
                  Query Ledger
                </button>
              </form>

              {verifiedCertResult && (
                <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 space-y-1.5">
                  <div className="flex items-center gap-1.5 text-emerald-500 font-bold">
                    <CheckCircle2 className="h-4 w-4" /> Verified Authenticity
                  </div>
                  <p className="text-foreground font-medium">{verifiedCertResult.recipient_name}</p>
                  <p className="text-muted-foreground">{verifiedCertResult.program_name}</p>
                  <span className="text-[10px] text-muted-foreground block">
                    {verifiedCertResult.total_verified_hours} Hours • Issued {new Date(verifiedCertResult.issued_at).toLocaleDateString()}
                  </span>
                </div>
              )}

              {verifyError && (
                <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-500 text-xs">
                  {verifyError}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Issue Certificate Modal */}
        {isIssueOpen && (
          <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-card border border-border rounded-xl max-w-md w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto text-xs">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <h2 className="text-base font-bold text-foreground flex items-center gap-2">
                  <PlusCircle className="h-5 w-5 text-purple-500" />
                  Issue Civic Impact Certificate
                </h2>
                <button onClick={() => setIsIssueOpen(false)} className="text-muted-foreground hover:text-foreground">
                  <X className="h-4 w-4" />
                </button>
              </div>

              <form onSubmit={handleIssueCertificate} className="space-y-4">
                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Program *</label>
                  <select
                    value={progId}
                    onChange={(e) => setProgId(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                    required
                  >
                    {programs.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.code} — {p.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Recipient Student ID *</label>
                  <input
                    type="text"
                    required
                    value={studentId}
                    onChange={(e) => setStudentId(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-foreground">Signatory Title</label>
                  <input
                    type="text"
                    value={issuedTitle}
                    onChange={(e) => setIssuedTitle(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                  />
                </div>

                <div className="flex items-center justify-end space-x-2 pt-3 border-t border-border">
                  <button
                    type="button"
                    onClick={() => setIsIssueOpen(false)}
                    className="px-4 py-2 rounded-lg border border-border text-foreground hover:bg-accent"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-lg bg-primary text-primary-foreground font-semibold shadow hover:opacity-95"
                  >
                    Generate Certificate
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

