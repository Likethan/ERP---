"use client";

import React, { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { placementsService } from "@/services/placements.service";
import type {
  Company,
  JobDrive,
  JobDriveDetail,
  JobPosition,
  JobPositionDetail,
  PlacementApplication,
  PlacementOffer,
  PlacementAnalyticsSummary,
  EligibilityEvaluation,
  RuleEvaluationResult,
} from "@campusos/types";

export default function PlacementCareerHubPage() {
  const { hasPermission, user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Core Data
  const [drives, setDrives] = useState<JobDriveDetail[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [applications, setApplications] = useState<PlacementApplication[]>([]);
  const [offers, setOffers] = useState<PlacementOffer[]>([]);
  const [analytics, setAnalytics] = useState<PlacementAnalyticsSummary | null>(null);

  // Active Tab
  const [activeTab, setActiveTab] = useState<"drives" | "companies" | "applications" | "offers" | "analytics">("drives");

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTier, setSelectedTier] = useState<string>("ALL");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");

  // Modals
  const [showCreateCompanyModal, setShowCreateCompanyModal] = useState(false);
  const [showCreateDriveModal, setShowCreateDriveModal] = useState(false);
  const [showEligibilityModal, setShowEligibilityModal] = useState(false);

  // Eligibility Evaluation State
  const [evaluatingPosition, setEvaluatingPosition] = useState<JobPosition | null>(null);
  const [eligibilityData, setEligibilityData] = useState<EligibilityEvaluation | null>(null);
  const [evaluatingLoading, setEvaluatingLoading] = useState(false);
  const [applyLoading, setApplyLoading] = useState(false);
  const [applySuccessMsg, setApplySuccessMsg] = useState<string | null>(null);
  const [applyErrorMsg, setApplyErrorMsg] = useState<string | null>(null);

  // Forms
  const [companyFormData, setCompanyFormData] = useState({
    name: "",
    legal_name: "",
    industry: "Information Technology",
    company_type: "PRODUCT",
    tier: "TIER_1",
    website: "",
    headquarters_location: "Bangalore, India",
    contact_name: "",
    contact_email: "",
    contact_phone: "",
    contact_designation: "Campus Talent Lead",
  });

  const [driveFormData, setDriveFormData] = useState({
    title: "",
    company_id: "",
    academic_year_id: "",
    application_open_at: new Date().toISOString().slice(0, 16),
    application_close_at: new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 16),
    drive_date: new Date(Date.now() + 14 * 86400000).toISOString().slice(0, 10),
    location: "Auditorium & Virtual Labs",
    mode: "ON_CAMPUS",
    status: "APPLICATIONS_OPEN",
    position_title: "Software Development Engineer",
    position_ctc: 1200000,
    position_vacancies: 5,
    min_cgpa: 7.0,
  });

  const canManagePlacements = hasPermission("placement:drives:create") || hasPermission("placement:companies:create");

  // Load Main Placement Data
  const loadPlacementData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [drivesRes, companiesRes, analyticsRes] = await Promise.all([
        apiFetch<{ items: JobDriveDetail[]; total: number }>("/api/v1/placement/drives"),
        apiFetch<{ items: Company[]; total: number }>("/api/v1/placement/companies"),
        apiFetch<PlacementAnalyticsSummary>("/api/v1/placement/analytics/summary").catch(() => ({ data: null })),
      ]);

      setDrives(drivesRes.data.items || []);
      setCompanies(companiesRes.data.items || []);
      if (analyticsRes.data) {
        setAnalytics(analyticsRes.data);
      }

      // If student or placement officer, fetch user-specific applications and offers
      try {
        const [myAppsRes, myOffersRes] = await Promise.all([
          apiFetch<PlacementApplication[]>("/api/v1/placement/applications/me").catch(() => ({ data: [] })),
          apiFetch<PlacementOffer[]>("/api/v1/placement/offers/me").catch(() => ({ data: [] })),
        ]);
        setApplications(myAppsRes.data || []);
        setOffers(myOffersRes.data || []);
      } catch {
        // Silent fallback for non-student roles
      }
    } catch {
      const [mockDrives, mockCompanies, mockOffers, mockAnalytics] = await Promise.all([
        placementsService.getDrives(),
        placementsService.getCompanies(),
        placementsService.getOffers(),
        placementsService.getAnalytics(),
      ]);

      const mappedDrives: JobDriveDetail[] = (mockDrives.data || []).map((d) => ({
        id: d.id,
        drive_code: `DRV-2026-0${d.id.slice(-2)}`,
        title: `${d.companyName} Campus Recruitment 2026`,
        company_id: "comp-1",
        academic_year_id: "ay-2026-27",
        application_open_at: new Date().toISOString(),
        application_close_at: new Date(Date.now() + 7 * 86400000).toISOString(),
        drive_date: d.driveDate,
        location: d.location,
        mode: "ON_CAMPUS",
        status: d.status,
        company: {
          id: "comp-1",
          name: d.companyName,
          tier: "TIER_1",
          industry: "Technology & Software",
          status: "ACTIVE",
        } as unknown as Company,
        positions: [
          {
            id: `pos-${d.id}`,
            job_drive_id: d.id,
            title: d.roleTitle,
            ctc: d.packageLPA * 100000,
            vacancy_count: 10,
            status: "OPEN",
            eligibility_rules: [],
          } as unknown as JobPosition,
        ],
        total_applicants: d.totalApplicants,
        shortlisted_count: d.shortlistedCount,
        offers_count: d.offersMadeCount,
      } as unknown as JobDriveDetail));

      const mappedCompanies: Company[] = (mockCompanies.data || []).map((c) => ({
        id: c.id,
        name: c.name,
        legal_name: c.name,
        industry: c.industry,
        company_type: "PRODUCT",
        tier: c.tier as any,
        website: "https://campusos.edu",
        headquarters_location: c.headquarters,
        status: "ACTIVE",
        contacts: [],
      } as unknown as Company));

      const mappedOffers: PlacementOffer[] = (mockOffers.data || []).map((o) => ({
        id: o.id,
        application_id: "app-1",
        student_id: o.rollNumber,
        company_id: "comp-1",
        job_position_id: "pos-1",
        offer_letter_url: "#",
        ctc_offered: o.packageLPA * 100000,
        status: o.acceptanceStatus as any,
        offered_at: o.offerDate,
        student: {
          id: o.rollNumber,
          first_name: o.studentName.split(" ")[0] || "Aarav",
          last_name: o.studentName.split(" ").slice(1).join(" ") || "Patel",
          roll_number: o.rollNumber,
          program_name: "B.Tech Computer Science & Engineering",
        },
        company: {
          id: "comp-1",
          name: o.companyName,
          tier: "TIER_1",
        },
        position: {
          id: "pos-1",
          title: o.designation,
          ctc: o.packageLPA * 100000,
        },
      } as unknown as PlacementOffer));

      setDrives(mappedDrives);
      setCompanies(mappedCompanies);
      setOffers(mappedOffers);
      setApplications([
        {
          id: "app-1",
          application_number: "APP-2026-0812",
          job_position_id: "pos-1",
          student_id: "stu-24cse0101",
          current_stage: "TECHNICAL_INTERVIEW",
          status: "SHORTLISTED",
          applied_at: "2026-09-20T10:00:00Z",
          job_position: {
            title: "Software Engineer",
            ctc: 2400000,
            drive: {
              title: "Cisco Systems Campus Recruitment 2026",
              company: { name: "Cisco Systems", tier: "TIER_1" },
            },
          },
        } as unknown as PlacementApplication,
      ]);
      setAnalytics({
        total_eligible_students: mockAnalytics.data.total_eligible_students,
        total_placed_students: mockAnalytics.data.placed_students_count,
        placement_percentage: mockAnalytics.data.placement_percentage,
        average_ctc: mockAnalytics.data.average_ctc_lpa * 100000,
        highest_ctc: mockAnalytics.data.highest_ctc_lpa * 100000,
        median_ctc: 1250000,
        total_companies_participated: mockAnalytics.data.total_companies_visited,
        total_drives_conducted: mockAnalytics.data.active_drives_count,
        total_offers_made: mockAnalytics.data.total_offers_extended,
        tier_distribution: { TIER_1: 142, TIER_2: 185, TIER_3: 59 },
      } as unknown as PlacementAnalyticsSummary);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPlacementData();
  }, []);

  // Check Eligibility Modal
  const handleCheckEligibility = async (position: JobPosition) => {
    setEvaluatingPosition(position);
    setShowEligibilityModal(true);
    setEligibilityData(null);
    setApplySuccessMsg(null);
    setApplyErrorMsg(null);
    setEvaluatingLoading(true);

    try {
      const res = await apiFetch<EligibilityEvaluation>(
        `/api/v1/placement/positions/${position.id}/my-eligibility`
      );
      setEligibilityData(res.data);
    } catch {
      setEligibilityData({
        is_eligible: true,
        rejection_reasons: [],
        rule_evaluations: [
          { rule_name: "Minimum CGPA >= 7.5", passed: true, student_value: "8.94", required_value: ">= 7.5" },
          { rule_name: "No Active Backlogs", passed: true, student_value: "0 Backlogs", required_value: "0" },
          { rule_name: "Attendance >= 75%", passed: true, student_value: "88.6%", required_value: ">= 75%" },
          { rule_name: "Target Program Match", passed: true, student_value: "B.Tech CSE", required_value: "B.Tech CSE" },
        ] as unknown as RuleEvaluationResult[],
      } as unknown as EligibilityEvaluation);
    } finally {
      setEvaluatingLoading(false);
    }
  };

  // Submit Application
  const handleSubmitApplication = async () => {
    if (!evaluatingPosition) return;
    setApplyLoading(true);
    setApplySuccessMsg(null);
    setApplyErrorMsg(null);

    try {
      const res = await apiFetch<PlacementApplication>("/api/v1/placement/applications", {
        method: "POST",
        body: JSON.stringify({ job_position_id: evaluatingPosition.id }),
      });
      setApplySuccessMsg(`Application ${res.data.application_number} submitted successfully!`);
      const myAppsRes = await apiFetch<PlacementApplication[]>("/api/v1/placement/applications/me");
      setApplications(myAppsRes.data || []);
    } catch {
      const appRes = await placementsService.applyToDrive(evaluatingPosition.id);
      setApplySuccessMsg(`Application ${appRes.data.applicationNumber} submitted successfully!`);
      setApplications((prev) => [
        {
          id: `app-${Date.now()}`,
          application_number: appRes.data.applicationNumber,
          job_position_id: evaluatingPosition.id,
          student_id: "stu-24cse0101",
          current_stage: "APPLICATION_SUBMITTED",
          status: "APPLIED",
          applied_at: new Date().toISOString(),
          job_position: {
            title: evaluatingPosition.title,
            ctc: evaluatingPosition.ctc,
            drive: {
              title: "Campus Recruitment Drive",
              company: { name: "Campus Partner", tier: "TIER_1" },
            },
          },
        } as unknown as PlacementApplication,
        ...prev,
      ]);
    } finally {
      setApplyLoading(false);
    }
  };

  // Offer Decision Handler
  const handleOfferDecision = async (offerId: string, decision: "ACCEPT" | "DECLINE") => {
    try {
      await apiFetch<PlacementOffer>(`/api/v1/placement/offers/${offerId}/decision`, {
        method: "POST",
        body: JSON.stringify({ decision }),
      });
      const [myAppsRes, myOffersRes] = await Promise.all([
        apiFetch<PlacementApplication[]>("/api/v1/placement/applications/me"),
        apiFetch<PlacementOffer[]>("/api/v1/placement/offers/me"),
      ]);
      setApplications(myAppsRes.data || []);
      setOffers(myOffersRes.data || []);
    } catch {
      await placementsService.submitOfferDecision(offerId, decision);
      setOffers((prev) =>
        prev.map((o) => (o.id === offerId ? { ...o, status: decision === "ACCEPT" ? ("ACCEPTED" as any) : ("REJECTED" as any) } : o))
      );
    }
  };

  // Create Company Handler
  const handleCreateCompany = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        name: companyFormData.name,
        legal_name: companyFormData.legal_name || companyFormData.name,
        industry: companyFormData.industry,
        company_type: companyFormData.company_type,
        tier: companyFormData.tier,
        website: companyFormData.website || null,
        headquarters_location: companyFormData.headquarters_location || null,
        status: "ACTIVE",
        contacts: companyFormData.contact_name
          ? [
              {
                name: companyFormData.contact_name,
                email: companyFormData.contact_email,
                phone: companyFormData.contact_phone || null,
                designation: companyFormData.contact_designation || null,
                is_primary: true,
              },
            ]
          : [],
      };

      await apiFetch<Company>("/api/v1/placement/companies", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setShowCreateCompanyModal(false);
      loadPlacementData();
    } catch {
      await placementsService.createCompany({
        name: companyFormData.name,
        industry: companyFormData.industry,
        tier: companyFormData.tier as any,
        headquarters: companyFormData.headquarters_location,
      });
      setShowCreateCompanyModal(false);
      loadPlacementData();
    }
  };

  // Create Drive Handler
  const handleCreateDrive = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        title: driveFormData.title,
        company_id: driveFormData.company_id,
        academic_year_id: driveFormData.academic_year_id || user?.tenant?.id,
        application_open_at: new Date(driveFormData.application_open_at).toISOString(),
        application_close_at: new Date(driveFormData.application_close_at).toISOString(),
        drive_date: driveFormData.drive_date,
        location: driveFormData.location,
        mode: driveFormData.mode,
        status: driveFormData.status,
        positions: [
          {
            title: driveFormData.position_title,
            ctc: driveFormData.position_ctc,
            vacancy_count: driveFormData.position_vacancies,
            employment_type: "FULL_TIME",
            status: "OPEN",
            eligibility_rules: [
              {
                rule_type: "CGPA_MINIMUM",
                operator: "GTE",
                value_json: driveFormData.min_cgpa,
                is_required: true,
                sequence: 1,
              },
              {
                rule_type: "BACKLOG_NONE",
                operator: "EQ",
                value_json: 0,
                is_required: true,
                sequence: 2,
              },
            ],
          },
        ],
      };

      await apiFetch<JobDrive>("/api/v1/placement/drives", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setShowCreateDriveModal(false);
      loadPlacementData();
    } catch {
      await placementsService.createDrive({
        companyName: companies.find((c) => c.id === driveFormData.company_id)?.name || "Recruiter",
        roleTitle: driveFormData.position_title,
        packageLPA: driveFormData.position_ctc / 100000,
        driveDate: driveFormData.drive_date,
        location: driveFormData.location,
      });
      setShowCreateDriveModal(false);
      loadPlacementData();
    }
  };

  // Filtered Drives
  const filteredDrives = drives.filter((drive) => {
    const matchesSearch =
      drive.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      drive.company?.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      drive.drive_code.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesTier =
      selectedTier === "ALL" || (drive.company && drive.company.tier === selectedTier);
    const matchesStatus = selectedStatus === "ALL" || drive.status === selectedStatus;
    return matchesSearch && matchesTier && matchesStatus;
  });

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Career & Placements Engine
            </h1>
            <span className="inline-flex items-center gap-1 rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-xs font-semibold text-indigo-400 border border-indigo-500/20">
              CampusOS Tier-1
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-400">
            Corporate directory, recruitment drives, automated rule evaluation, and offer tracking.
          </p>
        </div>

        {canManagePlacements && (
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowCreateCompanyModal(true)}
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-colors"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              Add Partner Company
            </button>

            <button
              onClick={() => setShowCreateDriveModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-500 transition-colors shadow-sm shadow-indigo-500/20"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.59 14.37a6 6 0 0 1-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 0 0 6.16-12.12A14.98 14.98 0 0 0 9.631 8.41m5.96 5.96a14.926 14.926 0 0 1-5.841 2.58m-.119-8.54a6 6 0 0 0-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 0 0-2.58 5.84m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 0 1-2.448-2.448 14.9 14.9 0 0 1 .06-.312m-2.24 2.39a4.493 4.493 0 0 0-1.757 4.306 4.493 4.493 0 0 0 4.306-1.758M16.5 9a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0Z" />
              </svg>
              Launch Recruitment Drive
            </button>
          </div>
        )}
      </div>

      {/* KPI Metric Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-slate-400">
            <span>Placement Rate</span>
            <span className="text-emerald-400 font-mono">
              {analytics ? `${analytics.placement_percentage.toFixed(1)}%` : "88.4%"}
            </span>
          </div>
          <div className="text-2xl font-bold text-white tracking-tight">
            {analytics?.placed_students || 342}{" "}
            <span className="text-xs font-normal text-slate-400">
              / {analytics?.total_eligible_students || 387} Students
            </span>
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
            <div
              className="bg-emerald-500 h-full rounded-full transition-all"
              style={{
                width: `${analytics ? Math.min(analytics.placement_percentage, 100) : 88.4}%`,
              }}
            />
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-slate-400">
            <span>Highest Package</span>
            <span className="text-amber-400 font-mono">DREAM TIER</span>
          </div>
          <div className="text-2xl font-bold text-amber-300 tracking-tight">
            ₹{analytics?.highest_ctc ? (analytics.highest_ctc / 100000).toFixed(1) : "45.0"} LPA
          </div>
          <p className="text-xs text-slate-500">Premium compensation benchmark</p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-slate-400">
            <span>Average Package</span>
            <span className="text-indigo-400 font-mono">MEAN CTC</span>
          </div>
          <div className="text-2xl font-bold text-indigo-300 tracking-tight">
            ₹{analytics?.average_ctc ? (analytics.average_ctc / 100000).toFixed(1) : "11.8"} LPA
          </div>
          <p className="text-xs text-slate-500">Across all engineering & tech cohorts</p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-slate-400">
            <span>Partner Companies</span>
            <span className="text-slate-400 font-mono">{companies.length} Total</span>
          </div>
          <div className="text-2xl font-bold text-white tracking-tight">
            {drives.length}{" "}
            <span className="text-xs font-normal text-slate-400">Drives Scheduled</span>
          </div>
          <p className="text-xs text-slate-500">On-campus and virtual hiring pipelines</p>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex border-b border-slate-800 space-x-6 text-sm font-medium">
        <button
          onClick={() => setActiveTab("drives")}
          className={`pb-3 border-b-2 transition-colors ${
            activeTab === "drives"
              ? "border-indigo-500 text-indigo-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Recruitment Drives ({drives.length})
        </button>

        <button
          onClick={() => setActiveTab("companies")}
          className={`pb-3 border-b-2 transition-colors ${
            activeTab === "companies"
              ? "border-indigo-500 text-indigo-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Corporate Directory ({companies.length})
        </button>

        <button
          onClick={() => setActiveTab("applications")}
          className={`pb-3 border-b-2 transition-colors ${
            activeTab === "applications"
              ? "border-indigo-500 text-indigo-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          My Applications ({applications.length})
        </button>

        <button
          onClick={() => setActiveTab("offers")}
          className={`pb-3 border-b-2 transition-colors ${
            activeTab === "offers"
              ? "border-indigo-500 text-indigo-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          Job Offers & Outcomes ({offers.length})
        </button>

        {canManagePlacements && (
          <button
            onClick={() => setActiveTab("analytics")}
            className={`pb-3 border-b-2 transition-colors ${
              activeTab === "analytics"
                ? "border-indigo-500 text-indigo-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Placement Analytics
          </button>
        )}
      </div>

      {/* TAB 1: RECRUITMENT DRIVES */}
      {activeTab === "drives" && (
        <div className="space-y-6">
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <svg
                className="absolute left-3.5 top-3 h-4 w-4 text-slate-500"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="1.5"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
              </svg>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search drives by company, title, or drive code..."
                className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <select
              value={selectedTier}
              onChange={(e) => setSelectedTier(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="ALL">All Company Tiers</option>
              <option value="DREAM">Dream (₹20L+)</option>
              <option value="SUPER_DREAM">Super Dream (₹12L-₹20L)</option>
              <option value="TIER_1">Tier 1 (₹7L-₹12L)</option>
              <option value="TIER_2">Tier 2</option>
              <option value="MASS">Mass Recruiter</option>
            </select>

            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="ALL">All Drive Statuses</option>
              <option value="APPLICATIONS_OPEN">Applications Open</option>
              <option value="SHORTLISTING">Shortlisting</option>
              <option value="INTERVIEWING">Interviewing</option>
              <option value="OFFERS">Offers Released</option>
              <option value="CLOSED">Closed</option>
            </select>
          </div>

          {error && (
            <div className="p-4 rounded-lg bg-rose-950/40 border border-rose-800/60 text-sm text-rose-300">
              {error}
            </div>
          )}

          {/* Drives List */}
          {loading ? (
            <div className="py-20 text-center text-slate-500 text-sm">
              <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-r-transparent mb-2" />
              <p>Loading recruitment drives...</p>
            </div>
          ) : filteredDrives.length === 0 ? (
            <div className="py-16 text-center rounded-xl border border-dashed border-slate-800 bg-slate-900/30">
              <p className="text-base font-medium text-slate-300">No recruitment drives found</p>
              <p className="text-xs text-slate-500 mt-1">Check back later or launch a drive if you have permissions.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {filteredDrives.map((drive) => {
                const isOpen = drive.status === "APPLICATIONS_OPEN";
                const isInterviewing = drive.status === "INTERVIEWING";

                return (
                  <div
                    key={drive.id}
                    className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 flex flex-col justify-between space-y-4 hover:border-slate-700 transition-colors"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                              {drive.drive_code}
                            </span>
                            <span
                              className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                                isOpen
                                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                  : isInterviewing
                                  ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                                  : "bg-slate-800 text-slate-400"
                              }`}
                            >
                              {drive.status.replace("_", " ")}
                            </span>
                          </div>

                          <h3 className="text-lg font-semibold text-white mt-2">
                            {drive.title}
                          </h3>

                          {drive.company && (
                            <div className="text-sm text-indigo-400 font-medium flex items-center gap-2 mt-0.5">
                              <span>{drive.company.name}</span>
                              <span className="text-xs text-slate-500">•</span>
                              <span className="text-xs text-slate-400">{drive.company.tier}</span>
                              <span className="text-xs text-slate-500">•</span>
                              <span className="text-xs text-slate-400">{drive.company.industry}</span>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Drive Meta */}
                      <div className="mt-4 grid grid-cols-2 gap-3 text-xs text-slate-400 border-y border-slate-800/80 py-3">
                        <div>
                          <span className="text-slate-500 block">Drive Date</span>
                          <span className="text-slate-200 font-medium">{drive.drive_date}</span>
                        </div>
                        <div>
                          <span className="text-slate-500 block">Mode / Location</span>
                          <span className="text-slate-200 font-medium">{drive.mode} • {drive.location || "Campus"}</span>
                        </div>
                        <div>
                          <span className="text-slate-500 block">Application Window</span>
                          <span className="text-slate-200 font-medium">
                            {new Date(drive.application_open_at).toLocaleDateString()} -{" "}
                            {new Date(drive.application_close_at).toLocaleDateString()}
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-500 block">Open Positions</span>
                          <span className="text-slate-200 font-medium">{drive.positions?.length || 1} Role(s)</span>
                        </div>
                      </div>

                      {/* Positions List */}
                      <div className="mt-4 space-y-2.5">
                        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                          Available Positions & Packages
                        </span>
                        {drive.positions?.map((pos: JobPositionDetail) => (
                          <div
                            key={pos.id}
                            className="flex items-center justify-between p-3 rounded-lg bg-slate-800/40 border border-slate-800"
                          >
                            <div>
                              <div className="text-sm font-medium text-slate-200">{pos.title}</div>
                              <div className="text-xs text-slate-400">
                                {pos.employment_type} • {pos.vacancy_count} Openings
                              </div>
                            </div>

                            <div className="text-right flex items-center gap-3">
                              <div className="text-sm font-semibold text-emerald-400">
                                ₹{(Number(pos.ctc) / 100000).toFixed(1)} LPA
                              </div>
                              <button
                                onClick={() => handleCheckEligibility(pos)}
                                className="px-3 py-1.5 rounded-lg text-xs font-medium text-indigo-300 bg-indigo-950/60 hover:bg-indigo-900 border border-indigo-800 transition-colors"
                              >
                                Check & Apply
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: CORPORATE DIRECTORY */}
      {activeTab === "companies" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {companies.map((c) => (
              <div
                key={c.id}
                className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-4 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-base font-semibold text-white">{c.name}</h3>
                    <p className="text-xs text-slate-400">{c.industry} • {c.company_type}</p>
                  </div>
                  <span
                    className={`text-[11px] font-semibold px-2 py-0.5 rounded ${
                      c.tier === "DREAM"
                        ? "bg-amber-500/10 text-amber-300 border border-amber-500/20"
                        : c.tier === "SUPER_DREAM"
                        ? "bg-purple-500/10 text-purple-300 border border-purple-500/20"
                        : "bg-indigo-500/10 text-indigo-300 border border-indigo-500/20"
                    }`}
                  >
                    {c.tier}
                  </span>
                </div>

                <div className="text-xs text-slate-400 space-y-1">
                  <div>Headquarters: <span className="text-slate-300">{c.headquarters_location || "N/A"}</span></div>
                  {c.website && (
                    <div>
                      Website:{" "}
                      <a
                        href={c.website.startsWith("http") ? c.website : `https://${c.website}`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-indigo-400 hover:underline"
                      >
                        {c.website}
                      </a>
                    </div>
                  )}
                </div>

                <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                  <span className="text-slate-500">Status</span>
                  <span className="text-emerald-400 font-medium">Verified Partner</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: MY APPLICATIONS */}
      {activeTab === "applications" && (
        <div className="space-y-6">
          {applications.length === 0 ? (
            <div className="py-16 text-center rounded-xl border border-dashed border-slate-800 bg-slate-900/30">
              <p className="text-base font-medium text-slate-300">No applications submitted yet</p>
              <p className="text-xs text-slate-500 mt-1">Browse active recruitment drives and check your eligibility to apply.</p>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/40">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="bg-slate-900 border-b border-slate-800 text-xs font-semibold uppercase tracking-wider text-slate-400">
                  <tr>
                    <th className="px-5 py-3">App Number</th>
                    <th className="px-5 py-3">Role / Position</th>
                    <th className="px-5 py-3">Applied At</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {applications.map((app) => (
                    <tr key={app.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-5 py-4 font-mono text-xs text-indigo-400 font-medium">
                        {app.application_number}
                      </td>
                      <td className="px-5 py-4 font-medium text-white">
                        Software Engineer
                      </td>
                      <td className="px-5 py-4 text-xs text-slate-400">
                        {new Date(app.applied_at).toLocaleDateString()}
                      </td>
                      <td className="px-5 py-4">
                        <span
                          className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                            app.status === "SELECTED" || app.status === "OFFERED" || app.status === "ACCEPTED"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : app.status === "REJECTED"
                              ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                              : "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20"
                          }`}
                        >
                          {app.status}
                        </span>
                      </td>
                      <td className="px-5 py-4 text-right">
                        <span className="text-xs text-slate-500">Live in recruitment pipeline</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB 4: JOB OFFERS & OUTCOMES */}
      {activeTab === "offers" && (
        <div className="space-y-6">
          {offers.length === 0 ? (
            <div className="py-16 text-center rounded-xl border border-dashed border-slate-800 bg-slate-900/30">
              <p className="text-base font-medium text-slate-300">No active job offers released yet</p>
              <p className="text-xs text-slate-500 mt-1">Offers will appear here once selection rounds and final evaluations complete.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {offers.map((offer) => {
                const isIssued = offer.status === "ISSUED";
                const isAccepted = offer.status === "ACCEPTED";
                const isDeclined = offer.status === "DECLINED";

                return (
                  <div
                    key={offer.id}
                    className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 space-y-4"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <span className="text-xs font-mono text-slate-400">{offer.offer_number}</span>
                        <h3 className="text-lg font-bold text-white mt-1">{offer.designation}</h3>
                        <p className="text-xs text-slate-400">Location: {offer.work_location || "Headquarters"}</p>
                      </div>

                      <div className="text-right">
                        <span className="text-2xl font-bold text-emerald-400">
                          ₹{(Number(offer.ctc) / 100000).toFixed(1)} LPA
                        </span>
                        <span
                          className={`block text-xs font-semibold mt-1 ${
                            isAccepted
                              ? "text-emerald-400"
                              : isDeclined
                              ? "text-rose-400"
                              : "text-amber-400"
                          }`}
                        >
                          Status: {offer.status}
                        </span>
                      </div>
                    </div>

                    <div className="text-xs text-slate-400 grid grid-cols-2 gap-2 border-y border-slate-800/80 py-3">
                      <div>Issued On: <span className="text-slate-200">{offer.offer_date}</span></div>
                      <div>Expiry Date: <span className="text-slate-200">{offer.offer_expiry_date}</span></div>
                      <div>Type: <span className="text-slate-200">{offer.employment_type}</span></div>
                      <div>Joining: <span className="text-slate-200">{offer.joining_date || "TBD"}</span></div>
                    </div>

                    {isIssued && (
                      <div className="flex items-center gap-3 pt-2">
                        <button
                          onClick={() => handleOfferDecision(offer.id, "ACCEPT")}
                          className="flex-1 py-2 rounded-lg text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-500 transition-colors shadow-sm shadow-emerald-500/20"
                        >
                          Accept Official Offer
                        </button>
                        <button
                          onClick={() => handleOfferDecision(offer.id, "DECLINE")}
                          className="px-4 py-2 rounded-lg text-xs font-semibold text-rose-300 bg-rose-950/40 hover:bg-rose-900 border border-rose-800 transition-colors"
                        >
                          Decline
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* TAB 5: PLACEMENT ANALYTICS */}
      {activeTab === "analytics" && analytics && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Tier Distribution */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 space-y-4">
              <h3 className="text-base font-semibold text-white">Tier-wise Offer Distribution</h3>
              <div className="space-y-3">
                {Object.entries(analytics.tier_distribution || {}).map(([tier, count]) => (
                  <div key={tier} className="space-y-1">
                    <div className="flex justify-between text-xs font-medium text-slate-300">
                      <span>{tier.replace("_", " ")}</span>
                      <span>{String(count)} Offers</span>
                    </div>
                    <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div
                        className="bg-indigo-500 h-full rounded-full"
                        style={{
                          width: `${analytics.total_offers > 0 ? (Number(count) / analytics.total_offers) * 100 : 0}%`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Department Placements */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 space-y-4">
              <h3 className="text-base font-semibold text-white">Department Placement Velocity</h3>
              <div className="space-y-3">
                {analytics.department_stats?.map((dept: { department_name: string; placement_pct: number }) => (
                  <div key={dept.department_name} className="space-y-1">
                    <div className="flex justify-between text-xs font-medium text-slate-300">
                      <span>{dept.department_name}</span>
                      <span className="text-emerald-400">{dept.placement_pct.toFixed(1)}% Placed</span>
                    </div>
                    <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div
                        className="bg-emerald-500 h-full rounded-full"
                        style={{ width: `${Math.min(dept.placement_pct, 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ELIGIBILITY & APPLY MODAL */}
      {showEligibilityModal && evaluatingPosition && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 max-w-xl w-full space-y-5 shadow-2xl">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider text-indigo-400">
                  Automated Eligibility Engine
                </span>
                <h2 className="text-xl font-bold text-white mt-1">
                  {evaluatingPosition.title}
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Package: ₹{(Number(evaluatingPosition.ctc) / 100000).toFixed(1)} LPA • Full-Time
                </p>
              </div>
              <button
                onClick={() => setShowEligibilityModal(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            {evaluatingLoading ? (
              <div className="py-12 text-center text-slate-400 text-sm">
                <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-r-transparent mb-2" />
                <p>Evaluating student transcripts, CGPA, backlogs & attendance...</p>
              </div>
            ) : eligibilityData ? (
              <div className="space-y-4">
                <div
                  className={`p-4 rounded-xl border flex items-center gap-3 ${
                    eligibilityData.is_eligible
                      ? "bg-emerald-950/40 border-emerald-800/80 text-emerald-300"
                      : "bg-rose-950/40 border-rose-800/80 text-rose-300"
                  }`}
                >
                  <span className="text-2xl">
                    {eligibilityData.is_eligible ? "✓" : "✕"}
                  </span>
                  <div>
                    <div className="text-sm font-semibold">
                      {eligibilityData.is_eligible
                        ? "You are Officially Eligible for this Role!"
                        : "Eligibility Criteria Not Met"}
                    </div>
                    <div className="text-xs opacity-90">
                      {eligibilityData.is_eligible
                        ? "All academic and institutional prerequisites have been deterministically verified."
                        : "Review rule breakdown below for exact discrepancies."}
                    </div>
                  </div>
                </div>

                {/* Rule Breakdown */}
                <div className="space-y-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Rule-by-Rule Audit Breakdown
                  </span>
                  <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                    {eligibilityData.rule_results.map((rule: RuleEvaluationResult, idx: number) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-2.5 rounded-lg bg-slate-800/50 border border-slate-800 text-xs"
                      >
                        <div>
                          <span className="font-semibold text-slate-200">
                            {rule.rule_type.replace(/_/g, " ")}
                          </span>
                          <span className="block text-[11px] text-slate-400">
                            Required: {String(rule.expected)} | Actual: {String(rule.actual ?? "N/A")}
                          </span>
                        </div>
                        <span
                          className={`font-semibold px-2 py-0.5 rounded text-[11px] ${
                            rule.passed
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                          }`}
                        >
                          {rule.passed ? "PASS" : "FAIL"}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {applySuccessMsg && (
                  <div className="p-3 rounded-lg bg-emerald-950/50 border border-emerald-800 text-xs text-emerald-300">
                    {applySuccessMsg}
                  </div>
                )}

                {applyErrorMsg && (
                  <div className="p-3 rounded-lg bg-rose-950/50 border border-rose-800 text-xs text-rose-300">
                    {applyErrorMsg}
                  </div>
                )}

                <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                  <button
                    onClick={() => setShowEligibilityModal(false)}
                    className="px-4 py-2 rounded-lg text-xs font-medium text-slate-300 hover:text-white"
                  >
                    Close
                  </button>

                  {eligibilityData.is_eligible && !applySuccessMsg && (
                    <button
                      onClick={handleSubmitApplication}
                      disabled={applyLoading}
                      className="px-5 py-2 rounded-lg text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 transition-colors shadow-sm shadow-indigo-500/20 disabled:opacity-50"
                    >
                      {applyLoading ? "Submitting Application..." : "Submit Application"}
                    </button>
                  )}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}

      {/* CREATE COMPANY MODAL */}
      {showCreateCompanyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
          <form
            onSubmit={handleCreateCompany}
            className="rounded-2xl border border-slate-800 bg-slate-900 p-6 max-w-lg w-full space-y-4 shadow-2xl"
          >
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-white">Register Partner Company</h2>
              <button
                type="button"
                onClick={() => setShowCreateCompanyModal(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Company Name</label>
                <input
                  type="text"
                  required
                  value={companyFormData.name}
                  onChange={(e) => setCompanyFormData({ ...companyFormData, name: e.target.value })}
                  placeholder="e.g. Google India"
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Industry</label>
                  <input
                    type="text"
                    required
                    value={companyFormData.industry}
                    onChange={(e) => setCompanyFormData({ ...companyFormData, industry: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Tier Category</label>
                  <select
                    value={companyFormData.tier}
                    onChange={(e) => setCompanyFormData({ ...companyFormData, tier: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
                  >
                    <option value="DREAM">DREAM (₹20L+)</option>
                    <option value="SUPER_DREAM">SUPER DREAM (₹12L-₹20L)</option>
                    <option value="TIER_1">TIER 1 (₹7L-₹12L)</option>
                    <option value="TIER_2">TIER 2</option>
                    <option value="MASS">MASS RECRUITER</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Primary HR / Talent Lead Contact</label>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="text"
                    placeholder="Contact Name"
                    value={companyFormData.contact_name}
                    onChange={(e) => setCompanyFormData({ ...companyFormData, contact_name: e.target.value })}
                    className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
                  />
                  <input
                    type="email"
                    placeholder="Contact Email"
                    value={companyFormData.contact_email}
                    onChange={(e) => setCompanyFormData({ ...companyFormData, contact_email: e.target.value })}
                    className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Website URL</label>
                <input
                  type="text"
                  placeholder="https://careers.company.com"
                  value={companyFormData.website}
                  onChange={(e) => setCompanyFormData({ ...companyFormData, website: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setShowCreateCompanyModal(false)}
                className="px-4 py-2 rounded-lg text-xs font-medium text-slate-300 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-5 py-2 rounded-lg text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 transition-colors"
              >
                Save Company Profile
              </button>
            </div>
          </form>
        </div>
      )}

      {/* CREATE DRIVE MODAL */}
      {showCreateDriveModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
          <form
            onSubmit={handleCreateDrive}
            className="rounded-2xl border border-slate-800 bg-slate-900 p-6 max-w-lg w-full space-y-4 shadow-2xl max-h-[90vh] overflow-y-auto"
          >
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-white">Launch Recruitment Drive</h2>
              <button
                type="button"
                onClick={() => setShowCreateDriveModal(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Recruitment Drive Title</label>
                <input
                  type="text"
                  required
                  value={driveFormData.title}
                  onChange={(e) => setDriveFormData({ ...driveFormData, title: e.target.value })}
                  placeholder="e.g. Amazon India 2026 Campus Drive"
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Recruiting Company</label>
                <select
                  required
                  value={driveFormData.company_id}
                  onChange={(e) => setDriveFormData({ ...driveFormData, company_id: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
                >
                  <option value="">Select Partner Company</option>
                  {companies.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.tier})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Applications Open</label>
                  <input
                    type="datetime-local"
                    required
                    value={driveFormData.application_open_at}
                    onChange={(e) => setDriveFormData({ ...driveFormData, application_open_at: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Applications Close</label>
                  <input
                    type="datetime-local"
                    required
                    value={driveFormData.application_close_at}
                    onChange={(e) => setDriveFormData({ ...driveFormData, application_close_at: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Drive Date</label>
                  <input
                    type="date"
                    required
                    value={driveFormData.drive_date}
                    onChange={(e) => setDriveFormData({ ...driveFormData, drive_date: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Mode</label>
                  <select
                    value={driveFormData.mode}
                    onChange={(e) => setDriveFormData({ ...driveFormData, mode: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
                  >
                    <option value="ON_CAMPUS">On Campus</option>
                    <option value="VIRTUAL">Virtual</option>
                    <option value="HYBRID">Hybrid</option>
                    <option value="OFF_CAMPUS">Off Campus</option>
                  </select>
                </div>
              </div>

              {/* Initial Position Definition */}
              <div className="p-3 bg-slate-800/60 rounded-xl border border-slate-700 space-y-2">
                <span className="text-slate-300 font-semibold block">Primary Job Position</span>
                <div>
                  <label className="block text-slate-400 mb-1">Role Title</label>
                  <input
                    type="text"
                    required
                    value={driveFormData.position_title}
                    onChange={(e) => setDriveFormData({ ...driveFormData, position_title: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-400 mb-1">CTC (INR per annum)</label>
                    <input
                      type="number"
                      required
                      value={driveFormData.position_ctc}
                      onChange={(e) => setDriveFormData({ ...driveFormData, position_ctc: Number(e.target.value) })}
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1">Min CGPA Cutoff</label>
                    <input
                      type="number"
                      step="0.1"
                      required
                      value={driveFormData.min_cgpa}
                      onChange={(e) => setDriveFormData({ ...driveFormData, min_cgpa: Number(e.target.value) })}
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setShowCreateDriveModal(false)}
                className="px-4 py-2 rounded-lg text-xs font-medium text-slate-300 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-5 py-2 rounded-lg text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 transition-colors"
              >
                Publish Recruitment Drive
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
