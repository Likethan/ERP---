"use client";

import React, { useCallback, useEffect, useState } from "react";
import type {
  AcademicYear,
  Semester,
  Regulation,
  Batch,
  Section,
  Program,
} from "@campusos/types";
import { organizationService } from "@/services/organization.service";
import { useAuth } from "@/lib/auth-context";

type ActiveTab = "years" | "semesters" | "regulations" | "batches" | "sections";

export default function AcademicStructurePage() {
  const { hasPermission } = useAuth();
  const [activeTab, setActiveTab] = useState<ActiveTab>("years");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Data states
  const [years, setYears] = useState<AcademicYear[]>([]);
  const [semesters, setSemesters] = useState<Semester[]>([]);
  const [regulations, setRegulations] = useState<Regulation[]>([]);
  const [batches, setBatches] = useState<Batch[]>([]);
  const [sections, setSections] = useState<Section[]>([]);
  const [programs, setPrograms] = useState<Program[]>([]);

  // Filter states
  const [selectedYearId, setSelectedYearId] = useState<string>("");
  const [selectedProgramId, setSelectedProgramId] = useState<string>("");

  // Modal / Form state
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Form states by entity
  const [yearName, setYearName] = useState("");
  const [yearStart, setYearStart] = useState("");
  const [yearEnd, setYearEnd] = useState("");
  const [yearIsCurrent, setYearIsCurrent] = useState(false);

  const [semYearId, setSemYearId] = useState("");
  const [semName, setSemName] = useState("");
  const [semNumber, setSemNumber] = useState(1);
  const [semTermType, setSemTermType] = useState("ODD");
  const [semStart, setSemStart] = useState("");
  const [semEnd, setSemEnd] = useState("");

  const [regCode, setRegCode] = useState("");
  const [regTitle, setRegTitle] = useState("");
  const [regYear, setRegYear] = useState(new Date().getFullYear());
  const [regDesc, setRegDesc] = useState("");

  const [batchProgId, setBatchProgId] = useState("");
  const [batchRegId, setBatchRegId] = useState("");
  const [batchName, setBatchName] = useState("");
  const [batchAdmYear, setBatchAdmYear] = useState(new Date().getFullYear());
  const [batchGradYear, setBatchGradYear] = useState(new Date().getFullYear() + 4);

  const [secProgId, setSecProgId] = useState("");
  const [secBatchId, setSecBatchId] = useState("");
  const [secSemId, setSecSemId] = useState("");
  const [secName, setSecName] = useState("");
  const [secCapacity, setSecCapacity] = useState(60);

  const canManageYears = hasPermission("core:academic_years:manage");
  const canManagePrograms = hasPermission("core:programs:manage");
  const canManageSections = hasPermission("core:sections:manage");
  const canManageRegulations = hasPermission("core:regulations:manage");
  const canManageTab = activeTab === "years" || activeTab === "semesters"
    ? canManageYears
    : activeTab === "regulations"
      ? canManageRegulations
      : activeTab === "batches"
        ? canManagePrograms
        : canManageSections;

  const loadAll = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [yRes, sRes, rRes, bRes, secRes, pRes] = await Promise.all([
        organizationService.listAcademicYears(),
        organizationService.listSemesters(),
        organizationService.listRegulations(),
        organizationService.listBatches(),
        organizationService.listSections(),
        organizationService.listPrograms(),
      ]);

      setYears(yRes.data);
      setSemesters(sRes.data);
      setRegulations(rRes.data);
      setBatches(bRes.data);
      setSections(secRes.data);
      setPrograms(pRes.data);

      if (yRes.data.length > 0) {
        const curr = yRes.data.find((y) => y.is_current) || yRes.data[0];
        setSelectedYearId((current) => current || curr.id);
      }
      if (pRes.data.length > 0) {
        setSelectedProgramId((current) => current || pRes.data[0].id);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load academic structure");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadAll();
  }, [loadAll]);

  const handleOpenModal = () => {
    setFormError(null);
    if (activeTab === "semesters" && selectedYearId) setSemYearId(selectedYearId);
    if (activeTab === "batches" && selectedProgramId) setBatchProgId(selectedProgramId);
    if (activeTab === "sections") {
      if (selectedProgramId) setSecProgId(selectedProgramId);
      const progBatches = batches.filter((b) => !selectedProgramId || b.program_id === selectedProgramId);
      if (progBatches.length > 0) setSecBatchId(progBatches[0].id);
      if (semesters.length > 0) setSecSemId(semesters[0].id);
    }
    setShowModal(true);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setSubmitting(true);

    try {
      if (activeTab === "years") {
        await organizationService.createAcademicYear({
          name: yearName.trim(),
          start_date: yearStart,
          end_date: yearEnd,
          is_current: yearIsCurrent,
        });
        setYearName("");
      } else if (activeTab === "semesters") {
        await organizationService.createSemester({
          academic_year_id: semYearId,
          name: semName.trim(),
          semester_number: Number(semNumber),
          term_type: semTermType,
          start_date: semStart,
          end_date: semEnd,
        });
        setSemName("");
      } else if (activeTab === "regulations") {
        await organizationService.createRegulation({
          code: regCode.trim().toUpperCase(),
          title: regTitle.trim(),
          effective_year: Number(regYear),
          description: regDesc.trim() || undefined,
        });
        setRegCode("");
        setRegTitle("");
      } else if (activeTab === "batches") {
        await organizationService.createBatch({
          program_id: batchProgId,
          regulation_id: batchRegId,
          name: batchName.trim(),
          admission_year: Number(batchAdmYear),
          graduation_year: Number(batchGradYear),
        });
        setBatchName("");
      } else if (activeTab === "sections") {
        await organizationService.createSection({
          program_id: secProgId,
          batch_id: secBatchId,
          semester_id: secSemId,
          name: secName.trim().toUpperCase(),
          capacity: Number(secCapacity),
        });
        setSecName("");
      }

      setShowModal(false);
      await loadAll();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to create entry");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Academic Structure</h1>
          <p className="mt-1 text-sm text-slate-400">
            Configure Academic Years, Semesters, Curriculum Regulations, Student Batches, and Class Sections.
          </p>
        </div>
        {canManageTab && (
          <button
            onClick={handleOpenModal}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-500 rounded-lg shadow-sm transition-colors self-start sm:self-auto"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add {activeTab === "years" ? "Academic Year" : activeTab === "semesters" ? "Semester" : activeTab === "regulations" ? "Regulation" : activeTab === "batches" ? "Batch" : "Section"}
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 space-x-1 sm:space-x-8 overflow-x-auto">
        {[
          { id: "years", label: `Academic Years (${years.length})` },
          { id: "semesters", label: `Semesters (${semesters.length})` },
          { id: "regulations", label: `Regulations (${regulations.length})` },
          { id: "batches", label: `Batches (${batches.length})` },
          { id: "sections", label: `Sections (${sections.length})` },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => { setActiveTab(tab.id as ActiveTab); setFormError(null); }}
            className={`pb-3 px-1 text-sm font-medium whitespace-nowrap transition-colors border-b-2 ${
              activeTab === tab.id
                ? "border-blue-500 text-blue-400 font-semibold"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 rounded-lg bg-red-950/40 border border-red-800 text-red-300 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={loadAll} className="underline hover:text-red-200">
            Retry
          </button>
        </div>
      )}

      {/* Main Tab Content */}
      {loading ? (
        <div className="flex items-center justify-center p-12 text-slate-500 text-sm">
          <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          Loading academic structure...
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
          {/* TAB 1: ACADEMIC YEARS */}
          {activeTab === "years" && (
            <div>
              {years.length === 0 ? (
                <div className="p-12 text-center text-slate-500">
                  <p className="text-base font-medium text-slate-400">No academic years defined yet.</p>
                  <p className="text-sm mt-1">Create an academic year (e.g. 2024-2025) to begin scheduling terms.</p>
                </div>
              ) : (
                <table className="w-full text-left text-sm text-slate-300">
                  <thead className="bg-slate-950/50 text-slate-400 uppercase text-xs border-b border-slate-800">
                    <tr>
                      <th className="px-6 py-3 font-semibold">Academic Year</th>
                      <th className="px-6 py-3 font-semibold">Start Date</th>
                      <th className="px-6 py-3 font-semibold">End Date</th>
                      <th className="px-6 py-3 font-semibold">Status</th>
                      <th className="px-6 py-3 font-semibold text-right">Semesters</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {years.map((y) => {
                      const semCount = semesters.filter((s) => s.academic_year_id === y.id).length;
                      return (
                        <tr key={y.id} className="hover:bg-slate-800/30 transition-colors">
                          <td className="px-6 py-4 font-semibold text-white flex items-center gap-3">
                            {y.name}
                            {y.is_current && (
                              <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-emerald-950/80 text-emerald-400 border border-emerald-800">
                                Current Active
                              </span>
                            )}
                          </td>
                          <td className="px-6 py-4 text-slate-400">{y.start_date}</td>
                          <td className="px-6 py-4 text-slate-400">{y.end_date}</td>
                          <td className="px-6 py-4">
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-950/80 text-blue-300 border border-blue-800/80">
                              Configured
                            </span>
                          </td>
                          <td className="px-6 py-4 text-right font-medium text-slate-300">{semCount} terms</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {/* TAB 2: SEMESTERS */}
          {activeTab === "semesters" && (
            <div>
              {/* Year Filter */}
              <div className="p-4 bg-slate-950/30 border-b border-slate-800 flex items-center gap-3">
                <span className="text-xs font-medium text-slate-400 uppercase">Filter Academic Year:</span>
                <select
                  value={selectedYearId}
                  onChange={(e) => setSelectedYearId(e.target.value)}
                  className="bg-slate-800 text-white text-xs rounded-lg px-3 py-1.5 border border-slate-700 focus:outline-none focus:border-blue-500"
                >
                  <option value="">All Academic Years</option>
                  {years.map((y) => (
                    <option key={y.id} value={y.id}>
                      {y.name} {y.is_current ? "(Current)" : ""}
                    </option>
                  ))}
                </select>
              </div>

              {semesters.filter((s) => !selectedYearId || s.academic_year_id === selectedYearId).length === 0 ? (
                <div className="p-12 text-center text-slate-500">
                  <p className="text-base font-medium text-slate-400">No semesters found.</p>
                  <p className="text-sm mt-1">Add semesters under this academic year to structure terms.</p>
                </div>
              ) : (
                <table className="w-full text-left text-sm text-slate-300">
                  <thead className="bg-slate-950/50 text-slate-400 uppercase text-xs border-b border-slate-800">
                    <tr>
                      <th className="px-6 py-3 font-semibold">Semester / Term</th>
                      <th className="px-6 py-3 font-semibold">Term Type</th>
                      <th className="px-6 py-3 font-semibold">Number</th>
                      <th className="px-6 py-3 font-semibold">Start Date</th>
                      <th className="px-6 py-3 font-semibold">End Date</th>
                      <th className="px-6 py-3 font-semibold">Status</th>
                      <th className="px-6 py-3 font-semibold text-right">Sections</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {semesters
                      .filter((s) => !selectedYearId || s.academic_year_id === selectedYearId)
                      .map((s) => {
                        const secCount = sections.filter((sec) => sec.semester_id === s.id).length;
                        return (
                          <tr key={s.id} className="hover:bg-slate-800/30 transition-colors">
                            <td className="px-6 py-4 font-semibold text-white">{s.name}</td>
                            <td className="px-6 py-4">
                              <span className="px-2 py-0.5 text-xs rounded font-medium bg-indigo-950/80 text-indigo-300 border border-indigo-800">
                                {s.term_type}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-slate-400">Sem {s.semester_number}</td>
                            <td className="px-6 py-4 text-slate-400">{s.start_date}</td>
                            <td className="px-6 py-4 text-slate-400">{s.end_date}</td>
                            <td className="px-6 py-4"><span className={`px-2 py-0.5 text-xs rounded-full font-medium border ${s.is_active ? "bg-emerald-950/80 text-emerald-400 border-emerald-800" : "bg-slate-800 text-slate-400 border-slate-700"}`}>{s.is_active ? "Active" : "Inactive"}</span></td>
                            <td className="px-6 py-4 text-right font-medium text-slate-300">{secCount} sections</td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {/* TAB 3: REGULATIONS */}
          {activeTab === "regulations" && (
            <div>
              {regulations.length === 0 ? (
                <div className="p-12 text-center text-slate-500">
                  <p className="text-base font-medium text-slate-400">No regulations defined.</p>
                  <p className="text-sm mt-1">Regulations define degree curriculum structures (e.g. R2021, R2023).</p>
                </div>
              ) : (
                <table className="w-full text-left text-sm text-slate-300">
                  <thead className="bg-slate-950/50 text-slate-400 uppercase text-xs border-b border-slate-800">
                    <tr>
                      <th className="px-6 py-3 font-semibold">Code</th>
                      <th className="px-6 py-3 font-semibold">Title</th>
                      <th className="px-6 py-3 font-semibold">Effective Year</th>
                      <th className="px-6 py-3 font-semibold">Description</th>
                      <th className="px-6 py-3 font-semibold text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {regulations.map((r) => (
                      <tr key={r.id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="px-6 py-4 font-mono font-bold text-blue-400">{r.code}</td>
                        <td className="px-6 py-4 font-semibold text-white">{r.title}</td>
                        <td className="px-6 py-4 text-slate-400">{r.effective_year}</td>
                        <td className="px-6 py-4 text-slate-400 text-xs max-w-xs truncate">{r.description || "—"}</td>
                        <td className="px-6 py-4 text-right">
                          <span className={`px-2 py-0.5 text-xs rounded-full font-medium border ${r.is_active ? "bg-emerald-950/80 text-emerald-400 border-emerald-800" : "bg-slate-800 text-slate-400 border-slate-700"}`}>
                            {r.is_active ? "Active" : "Inactive"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {/* TAB 4: BATCHES */}
          {activeTab === "batches" && (
            <div>
              <div className="p-4 bg-slate-950/30 border-b border-slate-800 flex items-center gap-3">
                <span className="text-xs font-medium text-slate-400 uppercase">Filter Program:</span>
                <select
                  value={selectedProgramId}
                  onChange={(e) => setSelectedProgramId(e.target.value)}
                  className="bg-slate-800 text-white text-xs rounded-lg px-3 py-1.5 border border-slate-700 focus:outline-none focus:border-blue-500"
                >
                  <option value="">All Programs</option>
                  {programs.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.code})
                    </option>
                  ))}
                </select>
              </div>

              {batches.filter((b) => !selectedProgramId || b.program_id === selectedProgramId).length === 0 ? (
                <div className="p-12 text-center text-slate-500">
                  <p className="text-base font-medium text-slate-400">No student cohorts / batches configured.</p>
                  <p className="text-sm mt-1">Batches group students admitted in a specific calendar year.</p>
                </div>
              ) : (
                <table className="w-full text-left text-sm text-slate-300">
                  <thead className="bg-slate-950/50 text-slate-400 uppercase text-xs border-b border-slate-800">
                    <tr>
                      <th className="px-6 py-3 font-semibold">Batch Name</th>
                      <th className="px-6 py-3 font-semibold">Program</th>
                      <th className="px-6 py-3 font-semibold">Admission Year</th>
                      <th className="px-6 py-3 font-semibold">Expected Graduation</th>
                      <th className="px-6 py-3 font-semibold text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {batches
                      .filter((b) => !selectedProgramId || b.program_id === selectedProgramId)
                      .map((b) => {
                        const prog = programs.find((p) => p.id === b.program_id);
                        return (
                          <tr key={b.id} className="hover:bg-slate-800/30 transition-colors">
                            <td className="px-6 py-4 font-semibold text-white">{b.name}</td>
                            <td className="px-6 py-4 text-slate-300">{prog?.name || b.program_id}</td>
                            <td className="px-6 py-4 text-slate-400">{b.admission_year}</td>
                            <td className="px-6 py-4 text-slate-400">{b.graduation_year}</td>
                            <td className="px-6 py-4 text-right">
                              <span className={`px-2 py-0.5 text-xs rounded-full font-medium border ${b.is_active ? "bg-blue-950/80 text-blue-300 border-blue-800" : "bg-slate-800 text-slate-400 border-slate-700"}`}>
                                {b.is_active ? "Active Cohort" : "Inactive"}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {/* TAB 5: SECTIONS */}
          {activeTab === "sections" && (
            <div>
              <div className="p-4 bg-slate-950/30 border-b border-slate-800 flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-slate-400 uppercase">Program:</span>
                  <select
                    value={selectedProgramId}
                    onChange={(e) => setSelectedProgramId(e.target.value)}
                    className="bg-slate-800 text-white text-xs rounded-lg px-3 py-1.5 border border-slate-700 focus:outline-none focus:border-blue-500"
                  >
                    <option value="">All Programs</option>
                    {programs.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.code})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {sections.filter((s) => !selectedProgramId || s.program_id === selectedProgramId).length === 0 ? (
                <div className="p-12 text-center text-slate-500">
                  <p className="text-base font-medium text-slate-400">No class sections found.</p>
                  <p className="text-sm mt-1">Create sections (e.g. Section A, Section B) to assign students.</p>
                </div>
              ) : (
                <table className="w-full text-left text-sm text-slate-300">
                  <thead className="bg-slate-950/50 text-slate-400 uppercase text-xs border-b border-slate-800">
                    <tr>
                      <th className="px-6 py-3 font-semibold">Section Name</th>
                      <th className="px-6 py-3 font-semibold">Program</th>
                      <th className="px-6 py-3 font-semibold">Batch</th>
                      <th className="px-6 py-3 font-semibold">Semester</th>
                      <th className="px-6 py-3 font-semibold text-right">Student Capacity</th>
                      <th className="px-6 py-3 font-semibold text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {sections
                      .filter((s) => !selectedProgramId || s.program_id === selectedProgramId)
                      .map((s) => {
                        const prog = programs.find((p) => p.id === s.program_id);
                        const bth = batches.find((b) => b.id === s.batch_id);
                        const sem = semesters.find((sm) => sm.id === s.semester_id);
                        return (
                          <tr key={s.id} className="hover:bg-slate-800/30 transition-colors">
                            <td className="px-6 py-4 font-bold text-white flex items-center gap-2">
                              <span className="w-7 h-7 rounded-lg bg-blue-950/80 border border-blue-800 text-blue-400 flex items-center justify-center font-mono text-xs">
                                {s.name}
                              </span>
                              Section {s.name}
                            </td>
                            <td className="px-6 py-4 text-slate-300">{prog?.name || s.program_id}</td>
                            <td className="px-6 py-4 text-slate-400">{bth?.name || s.batch_id}</td>
                            <td className="px-6 py-4 text-slate-400">{sem?.name || s.semester_id}</td>
                            <td className="px-6 py-4 text-right font-mono text-slate-300">{s.capacity} seats</td>
                            <td className="px-6 py-4 text-right"><span className={`px-2 py-0.5 text-xs rounded-full font-medium border ${s.is_active ? "bg-emerald-950/80 text-emerald-400 border-emerald-800" : "bg-slate-800 text-slate-400 border-slate-700"}`}>{s.is_active ? "Active" : "Inactive"}</span></td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </div>
      )}

      {/* CREATE MODAL */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4 my-8">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-lg font-bold text-white">
                Add {activeTab === "years" ? "Academic Year" : activeTab === "semesters" ? "Semester" : activeTab === "regulations" ? "Regulation" : activeTab === "batches" ? "Batch" : "Section"}
              </h2>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            {formError && (
              <div className="p-3 bg-red-950/40 border border-red-800 text-red-300 text-xs rounded-lg">
                {formError}
              </div>
            )}

            <form onSubmit={handleCreate} className="space-y-4 text-sm">
              {/* YEARS FORM */}
              {activeTab === "years" && (
                <>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Academic Year Label (e.g. 2025-2026) *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="2025-2026"
                      value={yearName}
                      onChange={(e) => setYearName(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Start Date *</label>
                      <input
                        type="date"
                        required
                        value={yearStart}
                        onChange={(e) => setYearStart(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">End Date *</label>
                      <input
                        type="date"
                        required
                        value={yearEnd}
                        onChange={(e) => setYearEnd(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                      />
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="yearIsCurrent"
                      checked={yearIsCurrent}
                      onChange={(e) => setYearIsCurrent(e.target.checked)}
                      className="rounded bg-slate-950 border-slate-700 text-blue-600 focus:ring-blue-500"
                    />
                    <label htmlFor="yearIsCurrent" className="text-xs text-slate-300">
                      Set as current active academic year
                    </label>
                  </div>
                </>
              )}

              {/* SEMESTERS FORM */}
              {activeTab === "semesters" && (
                <>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Academic Year *</label>
                    <select
                      required
                      value={semYearId}
                      onChange={(e) => setSemYearId(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    >
                      <option value="">Select Academic Year</option>
                      {years.map((y) => (
                        <option key={y.id} value={y.id}>
                          {y.name} {y.is_current ? "(Current)" : ""}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Semester Name *</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Fall 2025 (Semester 1)"
                      value={semName}
                      onChange={(e) => setSemName(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Semester Number *</label>
                      <input
                        type="number"
                        min="1"
                        max="12"
                        required
                        value={semNumber}
                        onChange={(e) => setSemNumber(Number(e.target.value))}
                        className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Term Type *</label>
                      <select
                        value={semTermType}
                        onChange={(e) => setSemTermType(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                      >
                        <option value="ODD">ODD</option>
                        <option value="EVEN">EVEN</option>
                        <option value="SUMMER">SUMMER</option>
                      </select>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Start Date *</label>
                      <input
                        type="date"
                        required
                        value={semStart}
                        onChange={(e) => setSemStart(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">End Date *</label>
                      <input
                        type="date"
                        required
                        value={semEnd}
                        onChange={(e) => setSemEnd(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                      />
                    </div>
                  </div>
                </>
              )}

              {/* REGULATIONS FORM */}
              {activeTab === "regulations" && (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Code *</label>
                      <input
                        type="text"
                        required
                        placeholder="R2023"
                        value={regCode}
                        onChange={(e) => setRegCode(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Effective Year *</label>
                      <input
                        type="number"
                        min="2000"
                        max="2100"
                        required
                        value={regYear}
                        onChange={(e) => setRegYear(Number(e.target.value))}
                        className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Regulation Title *</label>
                    <input
                      type="text"
                      required
                      placeholder="Choice Based Credit System (CBCS) 2023"
                      value={regTitle}
                      onChange={(e) => setRegTitle(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Description</label>
                    <textarea
                      rows={2}
                      placeholder="Curriculum governance details..."
                      value={regDesc}
                      onChange={(e) => setRegDesc(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </>
              )}

              {/* BATCHES FORM */}
              {activeTab === "batches" && (
                <>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Program *</label>
                    <select
                      required
                      value={batchProgId}
                      onChange={(e) => setBatchProgId(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    >
                      <option value="">Select Degree Program</option>
                      {programs.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name} ({p.code})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Curriculum Regulation *</label>
                    <select
                      required
                      value={batchRegId}
                      onChange={(e) => setBatchRegId(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    >
                      <option value="">Select Regulation</option>
                      {regulations.map((r) => (
                        <option key={r.id} value={r.id}>
                          {r.code} - {r.title}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Batch Label *</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. 2024-2028 Cohort"
                      value={batchName}
                      onChange={(e) => setBatchName(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Admission Year *</label>
                      <input
                        type="number"
                        min="2000"
                        max="2100"
                        required
                        value={batchAdmYear}
                        onChange={(e) => setBatchAdmYear(Number(e.target.value))}
                        className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Graduation Year *</label>
                      <input
                        type="number"
                        min="2000"
                        max="2100"
                        required
                        value={batchGradYear}
                        onChange={(e) => setBatchGradYear(Number(e.target.value))}
                        className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                      />
                    </div>
                  </div>
                </>
              )}

              {/* SECTIONS FORM */}
              {activeTab === "sections" && (
                <>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">Program *</label>
                    <select
                      required
                      value={secProgId}
                      onChange={(e) => setSecProgId(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    >
                      <option value="">Select Program</option>
                      {programs.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name} ({p.code})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Batch Cohort *</label>
                      <select
                        required
                        value={secBatchId}
                        onChange={(e) => setSecBatchId(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                      >
                        <option value="">Select Batch</option>
                        {batches
                          .filter((b) => !secProgId || b.program_id === secProgId)
                          .map((b) => (
                            <option key={b.id} value={b.id}>
                              {b.name}
                            </option>
                          ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Semester *</label>
                      <select
                        required
                        value={secSemId}
                        onChange={(e) => setSecSemId(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                      >
                        <option value="">Select Semester</option>
                        {semesters.map((s) => (
                          <option key={s.id} value={s.id}>
                            {s.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Section Name *</label>
                      <input
                        type="text"
                        required
                        placeholder="A"
                        value={secName}
                        onChange={(e) => setSecName(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500 uppercase font-bold"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-300 mb-1">Capacity *</label>
                      <input
                        type="number"
                        min="1"
                        max="300"
                        required
                        value={secCapacity}
                        onChange={(e) => setSecCapacity(Number(e.target.value))}
                        className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                      />
                    </div>
                  </div>
                </>
              )}

              {/* Modal Actions */}
              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-sm text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-500 rounded-lg disabled:opacity-50"
                >
                  {submitting ? "Saving..." : "Save"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
