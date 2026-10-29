"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  BookOpen,
  CheckCircle2,
  ExternalLink,
  FileCheck,
  FileText,
  Lightbulb,
  Plus,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Tag,
  UserCheck,
} from "lucide-react";
import { ResearchNav } from "@/components/research/research-nav";
import { ResearchService } from "@/services/research.service";
import {
  ResearchInventionDisclosure,
  ResearchOutput,
  ResearchProject,
} from "@/types/research";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export default function ResearchOutputsPage() {
  const [activeTab, setActiveTab] = useState<"outputs" | "disclosures">("outputs");
  const [outputs, setOutputs] = useState<ResearchOutput[]>([]);
  const [disclosures, setDisclosures] = useState<ResearchInventionDisclosure[]>([]);
  const [projects, setProjects] = useState<ResearchProject[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  // Modals
  const [showCreateOutputModal, setShowCreateOutputModal] = useState(false);
  const [showCreateDisclosureModal, setShowCreateDisclosureModal] = useState(false);
  const [showVerifyModal, setShowVerifyModal] = useState(false);
  const [selectedOutput, setSelectedOutput] = useState<ResearchOutput | null>(null);

  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Form states for Output
  const [newOutput, setNewOutput] = useState({
    title: "",
    output_type: "JOURNAL_ARTICLE",
    authors: "Lead Investigator, Co-Author",
    publication_venue: "",
    doi: "",
    repository_url: "",
    publication_date: new Date().toISOString().split("T")[0],
  });

  // Form states for Disclosure
  const [newDisclosure, setNewDisclosure] = useState({
    disclosure_code: "",
    title: "",
    summary_of_invention: "",
    commercial_potential: "",
    lead_inventor_id: "",
  });

  // Verification state
  const [verifyData, setVerifyData] = useState({
    verified_doi: "",
    verified_venue: "",
    verification_notes: "",
  });

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    loadData();
  }, [selectedProjectId]);

  async function loadProjects() {
    try {
      const res = await ResearchService.getProjects({ limit: 100 });
      setProjects(Array.isArray(res) ? res : []);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load projects");
    }
  }

  async function loadData() {
    try {
      setLoading(true);
      const [outputsRes, disclosuresRes] = await Promise.all([
        ResearchService.getResearchOutputs(selectedProjectId || undefined),
        ResearchService.getInventionDisclosures(selectedProjectId || undefined),
      ]);
      setOutputs(Array.isArray(outputsRes) ? outputsRes : []);
      setDisclosures(Array.isArray(disclosuresRes) ? disclosuresRes : []);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load outputs and disclosures");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateOutput(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedProjectId) {
      setErrorMsg("Please select a project to attribute this publication/output to.");
      return;
    }
    if (!newOutput.title) {
      setErrorMsg("Title is required.");
      return;
    }

    try {
      setSubmitting(true);
      setErrorMsg(null);
      await ResearchService.createResearchOutput({
        project_id: selectedProjectId,
        title: newOutput.title,
        output_type: newOutput.output_type,
        authors_json: newOutput.authors.split(",").map((a) => a.trim()),
        venue_name: newOutput.publication_venue,
        doi: newOutput.doi || undefined,
        repository_url: newOutput.repository_url || undefined,
        publication_date: newOutput.publication_date || undefined,
      });
      setSuccessMsg("Research publication registered.");
      setShowCreateOutputModal(false);
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to register output.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCreateDisclosure(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedProjectId) {
      setErrorMsg("Please select a project to attribute this invention to.");
      return;
    }
    if (!newDisclosure.title) {
      setErrorMsg("Invention title is required.");
      return;
    }

    try {
      setSubmitting(true);
      setErrorMsg(null);
      await ResearchService.createInventionDisclosure({
        project_id: selectedProjectId,
        disclosure_code: newDisclosure.disclosure_code || `IP-${Date.now().toString().slice(-6)}`,
        title: newDisclosure.title,
        summary_of_invention: newDisclosure.summary_of_invention,
        commercial_potential: newDisclosure.commercial_potential,
      });
      setSuccessMsg("Intellectual property invention disclosure registered.");
      setShowCreateDisclosureModal(false);
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to register disclosure.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleVerifyOutput(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedOutput) return;

    try {
      setSubmitting(true);
      setErrorMsg(null);
      const res = await fetch(`http://localhost:8000/api/v1/research/outputs/${selectedOutput.id}/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          is_verified: true,
          verification_notes: verifyData.verification_notes || "Verified via institutional bibliographic index",
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Verification failed");
      }
      setSuccessMsg("Publication verified and confirmed in institutional repository.");
      setShowVerifyModal(false);
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to verify publication.");
    } finally {
      setSubmitting(false);
    }
  }

  const filteredOutputs = outputs.filter((o) => {
    const q = search.toLowerCase();
    const title = (o.title || "").toLowerCase();
    const venue = (o.venue_name || "").toLowerCase();
    const doi = (o.doi || "").toLowerCase();
    return title.includes(q) || venue.includes(q) || doi.includes(q);
  });

  const filteredDisclosures = disclosures.filter((d) => {
    const q = search.toLowerCase();
    const title = (d.title || "").toLowerCase();
    const code = (d.disclosure_code || "").toLowerCase();
    return title.includes(q) || code.includes(q);
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <ResearchNav />

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
        {/* Alerts */}
        {errorMsg && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-rose-400" />
              <span>{errorMsg}</span>
            </div>
            <button onClick={() => setErrorMsg(null)} className="text-rose-400 hover:text-rose-200">✕</button>
          </div>
        )}
        {successMsg && (
          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-sm flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              <span>{successMsg}</span>
            </div>
            <button onClick={() => setSuccessMsg(null)} className="text-emerald-400 hover:text-emerald-200">✕</button>
          </div>
        )}

        {/* Header & Controls */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              <Lightbulb className="h-6 w-6 text-emerald-400" />
              Research Outputs, Scholarly Impact & Intellectual Property
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Peer-reviewed publications, open datasets, invention disclosures, and patent filings.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <select
              className="h-9 px-3 rounded-md bg-slate-900 border border-slate-800 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
            >
              <option value="">All Institutional Projects</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.project_code} — {p.title.slice(0, 36)}...
                </option>
              ))}
            </select>
            {activeTab === "outputs" ? (
              <Button
                onClick={() => setShowCreateOutputModal(true)}
                className="bg-emerald-600 hover:bg-emerald-500 text-white gap-2 shadow-sm text-xs"
              >
                <Plus className="h-3.5 w-3.5" />
                Register Publication
              </Button>
            ) : (
              <Button
                onClick={() => setShowCreateDisclosureModal(true)}
                className="bg-indigo-600 hover:bg-indigo-500 text-white gap-2 shadow-sm text-xs"
              >
                <Plus className="h-3.5 w-3.5" />
                New Invention Disclosure
              </Button>
            )}
          </div>
        </div>

        {/* Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <Card className="p-4 bg-slate-900/60 border-slate-800">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Publications</span>
            <div className="text-2xl font-bold text-white mt-1">{outputs.length}</div>
            <p className="text-xs text-slate-500 mt-1">Articles & manuscripts</p>
          </Card>
          <Card className="p-4 bg-slate-900/60 border-slate-800">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">DOI Verified</span>
            <div className="text-2xl font-bold text-emerald-400 mt-1">
              {outputs.filter((o) => o.is_verified).length}
            </div>
            <p className="text-xs text-slate-500 mt-1">Indexed in repository</p>
          </Card>
          <Card className="p-4 bg-slate-900/60 border-slate-800">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Invention Disclosures</span>
            <div className="text-2xl font-bold text-indigo-400 mt-1">{disclosures.length}</div>
            <p className="text-xs text-slate-500 mt-1">Tech transfer evaluations</p>
          </Card>
          <Card className="p-4 bg-slate-900/60 border-slate-800">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Patents Filed</span>
            <div className="text-2xl font-bold text-amber-400 mt-1">
              {disclosures.filter((d) => d.patent_filing_status && d.patent_filing_status !== "NONE").length}
            </div>
            <p className="text-xs text-slate-500 mt-1">Patent office applications</p>
          </Card>
        </div>

        {/* Tab Switcher & Search */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
            <button
              onClick={() => setActiveTab("outputs")}
              className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-colors ${
                activeTab === "outputs"
                  ? "bg-emerald-600 text-white"
                  : "bg-slate-900 text-slate-400 hover:text-white"
              }`}
            >
              <BookOpen className="h-4 w-4" />
              Scholarly Publications & Outputs ({outputs.length})
            </button>
            <button
              onClick={() => setActiveTab("disclosures")}
              className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition-colors ${
                activeTab === "disclosures"
                  ? "bg-indigo-600 text-white"
                  : "bg-slate-900 text-slate-400 hover:text-white"
              }`}
            >
              <Lightbulb className="h-4 w-4" />
              Invention Disclosures & IP ({disclosures.length})
            </button>
          </div>

          <div className="relative max-w-sm w-full">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <Input
              placeholder="Filter by title, DOI, or reference code..."
              className="pl-9 bg-slate-900/60 border-slate-800 text-slate-200 placeholder:text-slate-500 text-xs"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>

        {/* Active Tab Content */}
        {activeTab === "outputs" ? (
          <Card className="border-slate-800 bg-slate-900/60 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="bg-slate-800/60 text-xs font-medium text-slate-400 uppercase tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Publication Title</th>
                    <th className="py-3 px-4">Type</th>
                    <th className="py-3 px-4">Venue</th>
                    <th className="py-3 px-4">DOI / Repository</th>
                    <th className="py-3 px-4">Verification</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {loading ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-slate-500">
                        <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-slate-400" />
                        Loading publications...
                      </td>
                    </tr>
                  ) : filteredOutputs.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-slate-500">
                        No publications found. Click &quot;Register Publication&quot; to index a research output.
                      </td>
                    </tr>
                  ) : (
                    filteredOutputs.map((out) => (
                      <tr key={out.id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-3 px-4">
                          <span className="font-semibold text-white block">{out.title}</span>
                          <span className="text-xs text-slate-400">
                            {Array.isArray(out.authors_json) ? out.authors_json.join(", ") : "Contributors"}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <Badge className="bg-slate-800 text-slate-300 border-slate-700 text-xs">
                            {out.output_type}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-slate-300 font-medium">
                          {out.venue_name || "—"}
                        </td>
                        <td className="py-3 px-4 text-xs font-mono">
                          {out.doi ? (
                            <a
                              href={`https://doi.org/${out.doi}`}
                              target="_blank"
                              rel="noreferrer"
                              className="text-emerald-400 hover:underline flex items-center gap-1"
                            >
                              {out.doi}
                              <ExternalLink className="h-3 w-3" />
                            </a>
                          ) : out.repository_url ? (
                            <a
                              href={out.repository_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-sky-400 hover:underline flex items-center gap-1"
                            >
                              Repository
                              <ExternalLink className="h-3 w-3" />
                            </a>
                          ) : (
                            <span className="text-slate-500">Unassigned</span>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <Badge
                            className={
                              out.is_verified
                                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                                : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                            }
                          >
                            {out.is_verified ? "VERIFIED" : "PENDING_VERIFY"}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-right">
                          {!out.is_verified && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setSelectedOutput(out);
                                setVerifyData({
                                  verified_doi: out.doi || "",
                                  verified_venue: out.venue_name || "",
                                  verification_notes: "",
                                });
                                setShowVerifyModal(true);
                              }}
                              className="h-8 border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700 text-xs"
                            >
                              <UserCheck className="h-3.5 w-3.5 mr-1" />
                              Verify Index
                            </Button>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        ) : (
          <Card className="border-slate-800 bg-slate-900/60 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="bg-slate-800/60 text-xs font-medium text-slate-400 uppercase tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Invention Reference</th>
                    <th className="py-3 px-4">Title</th>
                    <th className="py-3 px-4">Evaluation Status</th>
                    <th className="py-3 px-4">Patent Filing</th>
                    <th className="py-3 px-4">Commercialization</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {loading ? (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-slate-500">
                        <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-slate-400" />
                        Loading disclosures...
                      </td>
                    </tr>
                  ) : filteredDisclosures.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-slate-500">
                        No invention disclosures found. Click &quot;New Invention Disclosure&quot; to record intellectual property.
                      </td>
                    </tr>
                  ) : (
                    filteredDisclosures.map((d) => (
                      <tr key={d.id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-3 px-4">
                          <span className="font-semibold text-white block">{d.disclosure_code}</span>
                          <span className="text-xs text-slate-500">ID: {d.id.slice(0, 8)}...</span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-semibold text-white">{d.title}</div>
                          <div className="text-xs text-slate-400 line-clamp-1 mt-0.5">
                            {d.summary_of_invention}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <Badge className="bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                            {d.status || "UNDER_EVALUATION"}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-xs">
                          {d.patent_application_number ? (
                            <div>
                              <span className="font-mono text-emerald-400">{d.patent_application_number}</span>
                              <div className="text-slate-500">{d.patent_filing_status}</div>
                            </div>
                          ) : (
                            <span className="text-slate-500">Unfiled</span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-xs text-slate-400">
                          {d.commercial_potential || "Internal Academic Use"}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {/* Modal: Register Publication */}
        <Dialog open={showCreateOutputModal} onOpenChange={setShowCreateOutputModal}>
          <DialogContent className="max-w-lg bg-slate-900 border-slate-800 text-slate-100">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-white">
                <BookOpen className="h-5 w-5 text-emerald-400" />
                Register Scholarly Publication
              </DialogTitle>
            </DialogHeader>

            <form onSubmit={handleCreateOutput} className="space-y-4 pt-2">
              <div>
                <Label className="text-xs text-slate-400">Attributed Research Project *</Label>
                <select
                  required
                  className="w-full h-10 px-3 mt-1 rounded-md bg-slate-950 border border-slate-800 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  value={selectedProjectId}
                  onChange={(e) => setSelectedProjectId(e.target.value)}
                >
                  <option value="">Select Research Project</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.project_code} — {p.title.slice(0, 40)}...
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <Label className="text-xs text-slate-400">Publication Title *</Label>
                <Input
                  required
                  placeholder="e.g. Distributed Consensus in Mission-Critical Satellite Swarms"
                  className="bg-slate-950 border-slate-800 mt-1"
                  value={newOutput.title}
                  onChange={(e) => setNewOutput({ ...newOutput, title: e.target.value })}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-xs text-slate-400">Output Classification *</Label>
                  <select
                    className="w-full h-10 px-3 mt-1 rounded-md bg-slate-950 border border-slate-800 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    value={newOutput.output_type}
                    onChange={(e) => setNewOutput({ ...newOutput, output_type: e.target.value })}
                  >
                    <option value="JOURNAL_ARTICLE">Peer-Reviewed Journal Article</option>
                    <option value="CONFERENCE_PROCEEDING">Conference Proceeding</option>
                    <option value="BOOK_CHAPTER">Book Chapter</option>
                    <option value="DATASET">Open Research Dataset</option>
                    <option value="SOFTWARE_ARTIFACT">Software / Algorithm Artifact</option>
                  </select>
                </div>
                <div>
                  <Label className="text-xs text-slate-400">Venue / Journal Name</Label>
                  <Input
                    placeholder="e.g. IEEE Transactions on Robotics"
                    className="bg-slate-950 border-slate-800 mt-1"
                    value={newOutput.publication_venue}
                    onChange={(e) => setNewOutput({ ...newOutput, publication_venue: e.target.value })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-xs text-slate-400">Digital Object Identifier (DOI)</Label>
                  <Input
                    placeholder="e.g. 10.1109/TRO.2026.1234567"
                    className="bg-slate-950 border-slate-800 mt-1"
                    value={newOutput.doi}
                    onChange={(e) => setNewOutput({ ...newOutput, doi: e.target.value })}
                  />
                </div>
                <div>
                  <Label className="text-xs text-slate-400">Open Access Repository URL</Label>
                  <Input
                    placeholder="e.g. https://github.com/campus/research"
                    className="bg-slate-950 border-slate-800 mt-1"
                    value={newOutput.repository_url}
                    onChange={(e) => setNewOutput({ ...newOutput, repository_url: e.target.value })}
                  />
                </div>
              </div>

              <div>
                <Label className="text-xs text-slate-400">Contributing Authors (Comma-separated)</Label>
                <Input
                  className="bg-slate-950 border-slate-800 mt-1"
                  value={newOutput.authors}
                  onChange={(e) => setNewOutput({ ...newOutput, authors: e.target.value })}
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => setShowCreateOutputModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={submitting} className="bg-emerald-600 hover:bg-emerald-500 text-white">
                  {submitting ? "Registering..." : "Register Output"}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>

        {/* Modal: New Invention Disclosure */}
        <Dialog open={showCreateDisclosureModal} onOpenChange={setShowCreateDisclosureModal}>
          <DialogContent className="max-w-lg bg-slate-900 border-slate-800 text-slate-100">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-white">
                <Lightbulb className="h-5 w-5 text-indigo-400" />
                Register Invention Disclosure (Confidential IP)
              </DialogTitle>
            </DialogHeader>

            <form onSubmit={handleCreateDisclosure} className="space-y-4 pt-2">
              <div>
                <Label className="text-xs text-slate-400">Originating Project *</Label>
                <select
                  required
                  className="w-full h-10 px-3 mt-1 rounded-md bg-slate-950 border border-slate-800 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  value={selectedProjectId}
                  onChange={(e) => setSelectedProjectId(e.target.value)}
                >
                  <option value="">Select Research Project</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.project_code} — {p.title.slice(0, 40)}...
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <Label className="text-xs text-slate-400">Invention Title *</Label>
                <Input
                  required
                  placeholder="e.g. Nanocomposite Self-Healing Ceramic Matrix"
                  className="bg-slate-950 border-slate-800 mt-1"
                  value={newDisclosure.title}
                  onChange={(e) => setNewDisclosure({ ...newDisclosure, title: e.target.value })}
                />
              </div>

              <div>
                <Label className="text-xs text-slate-400">Technical Summary of Invention *</Label>
                <Textarea
                  required
                  placeholder="Describe the novelty, mechanism, and distinguishing prior art characteristics..."
                  className="bg-slate-950 border-slate-800 mt-1"
                  rows={3}
                  value={newDisclosure.summary_of_invention}
                  onChange={(e) => setNewDisclosure({ ...newDisclosure, summary_of_invention: e.target.value })}
                />
              </div>

              <div>
                <Label className="text-xs text-slate-400">Commercial & Licensing Potential</Label>
                <Textarea
                  placeholder="Target market sectors, potential corporate licensees, and commercial viability..."
                  className="bg-slate-950 border-slate-800 mt-1"
                  rows={2}
                  value={newDisclosure.commercial_potential}
                  onChange={(e) => setNewDisclosure({ ...newDisclosure, commercial_potential: e.target.value })}
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => setShowCreateDisclosureModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={submitting} className="bg-indigo-600 hover:bg-indigo-500 text-white">
                  {submitting ? "Registering..." : "Submit Disclosure"}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>

        {/* Modal: Verify Publication */}
        <Dialog open={showVerifyModal} onOpenChange={setShowVerifyModal}>
          <DialogContent className="max-w-md bg-slate-900 border-slate-800 text-slate-100">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-white">
                <UserCheck className="h-5 w-5 text-emerald-400" />
                Bibliographic Indexing Verification
              </DialogTitle>
            </DialogHeader>

            <form onSubmit={handleVerifyOutput} className="space-y-4 pt-2">
              <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 text-xs">
                <div className="font-semibold text-white">{selectedOutput?.title}</div>
                <div className="text-slate-400 mt-1">DOI: {selectedOutput?.doi || "Not provided"}</div>
              </div>

              <div>
                <Label className="text-xs text-slate-400">Verification Notes *</Label>
                <Textarea
                  required
                  placeholder="Confirm journal indexing in Scopus/WoS/IEEE Xplore or crossref DOI confirmation..."
                  className="bg-slate-950 border-slate-800 mt-1"
                  rows={3}
                  value={verifyData.verification_notes}
                  onChange={(e) => setVerifyData({ ...verifyData, verification_notes: e.target.value })}
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="outline" onClick={() => setShowVerifyModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={submitting} className="bg-emerald-600 hover:bg-emerald-500 text-white">
                  {submitting ? "Verifying..." : "Confirm Indexing"}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </main>
    </div>
  );
}
