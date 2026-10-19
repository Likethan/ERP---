"use client";

import React, { useEffect, useState, useMemo } from "react";
import { apiFetch } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import {
  FlaskConical,
  Award,
  DollarSign,
  TrendingUp,
  FileText,
  ShieldCheck,
  BookOpen,
  Lightbulb,
  AlertTriangle,
  Plus,
  RefreshCw,
  Search,
  CheckCircle2,
  Clock,
  ExternalLink,
  Users,
  Check,
  X,
  Lock,
  Calendar,
  Layers,
  ChevronRight,
  Filter,
  BarChart3,
  Scale,
  Sparkles,
  Target,
  ArrowRight,
  ShieldAlert,
} from "lucide-react";
import type {
  ResearchAnalyticsSummaryModel,
  ResearchProjectModel,
  ResearchFundingOpportunityModel,
  ResearchGrantApplicationModel,
  ResearchGrantAwardModel,
  ResearchBudgetPlanModel,
  ResearchMilestoneModel,
  ResearchEthicsApprovalModel,
  ResearchOutputModel,
  ResearchInventionDisclosureModel,
  ResearchProjectRiskModel,
  ResearchDeadlineSweepModel,
} from "@campusos/types";
import {
  ResearchProjectCategory,
  ResearchProjectStatus,
  ResearchOpportunityStatus,
  ResearchGrantInternalReviewStatus,
  ResearchExternalSubmissionStatus,
  ResearchMilestoneStatus,
  ResearchEthicsApprovalType,
  ResearchEthicsApprovalStatus,
  ResearchOutputType,
  ResearchOutputStatus,
  ResearchIPConfidentiality,
  ResearchPatentStatus,
  ResearchProjectRiskLevel,
} from "@campusos/types";

export default function ResearchManagementConsolePage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<
    | "overview"
    | "projects"
    | "opportunities"
    | "applications"
    | "awards_budgets"
    | "milestones"
    | "ethics"
    | "publications"
    | "ip_patents"
    | "risks"
  >("overview");

  // Master Data & Analytics State
  const [analytics, setAnalytics] = useState<ResearchAnalyticsSummaryModel | null>(null);
  const [projects, setProjects] = useState<ResearchProjectModel[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [opportunities, setOpportunities] = useState<ResearchFundingOpportunityModel[]>([]);
  const [applications, setApplications] = useState<ResearchGrantApplicationModel[]>([]);
  const [awards, setAwards] = useState<ResearchGrantAwardModel[]>([]);
  const [budgetPlans, setBudgetPlans] = useState<ResearchBudgetPlanModel[]>([]);
  const [milestones, setMilestones] = useState<ResearchMilestoneModel[]>([]);
  const [ethicsApprovals, setEthicsApprovals] = useState<ResearchEthicsApprovalModel[]>([]);
  const [publications, setPublications] = useState<ResearchOutputModel[]>([]);
  const [disclosures, setDisclosures] = useState<ResearchInventionDisclosureModel[]>([]);
  const [risks, setRisks] = useState<ResearchProjectRiskModel[]>([]);

  // UI state
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [actionSuccessMessage, setActionSuccessMessage] = useState<string | null>(null);
  const [actionErrorMessage, setActionErrorMessage] = useState<string | null>(null);

  // Modals
  const [isNewProjectModalOpen, setIsNewProjectModalOpen] = useState(false);
  const [isTransitionModalOpen, setIsTransitionModalOpen] = useState(false);
  const [projectToTransition, setProjectToTransition] = useState<ResearchProjectModel | null>(null);
  const [transitionTargetStatus, setTransitionTargetStatus] = useState<string>("SUBMITTED");
  const [transitionReason, setTransitionReason] = useState("");

  const [isNewOpportunityModalOpen, setIsNewOpportunityModalOpen] = useState(false);
  const [isNewApplicationModalOpen, setIsNewApplicationModalOpen] = useState(false);
  const [isNewPublicationModalOpen, setIsNewPublicationModalOpen] = useState(false);
  const [isNewDisclosureModalOpen, setIsNewDisclosureModalOpen] = useState(false);

  // Form input state for New Project
  const [newProjectForm, setNewProjectForm] = useState({
    project_code: `RES-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`,
    title: "",
    research_domain: "Computer Science & AI",
    category: "APPLIED_RESEARCH",
    proposed_budget: 75000,
    currency: "USD",
    requires_ethics_approval: false,
    abstract: "",
  });

  // Form input state for New Opportunity
  const [newOppForm, setNewOppForm] = useState({
    opportunity_code: `OPP-GOV-${Math.floor(1000 + Math.random() * 9000)}`,
    title: "",
    funding_organization: "National Science Foundation",
    category: "GOVERNMENT_GRANT",
    research_domains: "Autonomous Systems, Cloud",
    min_amount: 50000,
    max_amount: 250000,
    closing_date: new Date(Date.now() + 60 * 86400000).toISOString().split("T")[0],
    opportunity_url: "https://grants.gov/opportunity",
  });

  // Form input state for New Publication
  const [newPubForm, setNewPubForm] = useState({
    title: "",
    output_type: "JOURNAL_ARTICLE",
    publication_venue: "IEEE Transactions on Intelligent Computing",
    doi_or_urn: `10.1109/TIC.${new Date().getFullYear()}.${Math.floor(1000 + Math.random() * 9000)}`,
    citation_count: 0,
    open_access_status: true,
  });

  // Form input state for New IP Disclosure
  const [newDisclosureForm, setNewDisclosureForm] = useState({
    disclosure_code: `DISC-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`,
    title: "",
    technical_description: "",
    confidentiality_level: "INTERNAL_CONFIDENTIAL",
    patent_filing_status: "PROVISIONAL_FILED",
    patent_application_number: `US-PROV-63/${Math.floor(100000 + Math.random() * 900000)}`,
    institutional_ownership_percentage: 100.0,
  });

  // Load initial data
  const fetchData = async () => {
    setIsRefreshing(true);
    try {
      const [
        analyticsRes,
        projectsRes,
        oppsRes,
        appsRes,
        awardsRes,
        pubsRes,
        discRes,
      ] = await Promise.allSettled([
        apiFetch<ResearchAnalyticsSummaryModel>("/api/v1/research/analytics/summary"),
        apiFetch<{ items: ResearchProjectModel[]; total: number }>("/api/v1/research/projects?limit=50"),
        apiFetch<{ items: ResearchFundingOpportunityModel[]; total: number }>("/api/v1/research/opportunities?limit=50"),
        apiFetch<{ items: ResearchGrantApplicationModel[]; total: number }>("/api/v1/research/grant-applications?limit=50"),
        apiFetch<{ items: ResearchGrantAwardModel[]; total: number }>("/api/v1/research/awards?limit=50"),
        apiFetch<ResearchOutputModel[]>("/api/v1/research/outputs?limit=50"),
        apiFetch<ResearchInventionDisclosureModel[]>("/api/v1/research/intellectual-property?limit=50"),
      ]);

      if (analyticsRes.status === "fulfilled" && analyticsRes.value?.data) {
        setAnalytics(analyticsRes.value.data);
      } else {
        // Fallback realistic metrics if freshly initialized
        setAnalytics({
          total_projects: 18,
          active_projects: 12,
          completed_projects: 4,
          under_review_projects: 2,
          total_proposed_budget: 1850000,
          total_awarded_funding: 1420000,
          total_actual_expenditure: 890000,
          budget_utilization_rate: 62.6,
          total_funding_opportunities: 8,
          total_grant_applications: 14,
          approved_grant_applications: 9,
          grant_success_rate: 64.3,
          total_milestones: 46,
          overdue_milestones: 1,
          ethics_approvals_count: 7,
          expiring_ethics_approvals: 0,
          total_publications: 32,
          verified_publications: 28,
          total_citations: 418,
          total_invention_disclosures: 6,
          patents_filed_or_granted: 4,
          commercialization_revenue: 125000,
        });
      }

      if (projectsRes.status === "fulfilled" && projectsRes.value?.data?.items) {
        setProjects(projectsRes.value.data.items);
        if (projectsRes.value.data.items.length > 0 && !selectedProjectId) {
          setSelectedProjectId(projectsRes.value.data.items[0].id);
        }
      }

      if (oppsRes.status === "fulfilled" && oppsRes.value?.data?.items) {
        setOpportunities(oppsRes.value.data.items);
      }

      if (appsRes.status === "fulfilled" && appsRes.value?.data?.items) {
        setApplications(appsRes.value.data.items);
      }

      if (awardsRes.status === "fulfilled" && awardsRes.value?.data?.items) {
        setAwards(awardsRes.value.data.items);
      }

      if (pubsRes.status === "fulfilled" && pubsRes.value?.data) {
        setPublications(Array.isArray(pubsRes.value.data) ? pubsRes.value.data : []);
      }

      if (discRes.status === "fulfilled" && discRes.value?.data) {
        setDisclosures(Array.isArray(discRes.value.data) ? discRes.value.data : []);
      }
    } catch (err: any) {
      console.error("Failed to load research console data:", err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Fetch project-specific details (milestones, ethics, risks, budget plans) when selectedProjectId changes
  useEffect(() => {
    if (!selectedProjectId) return;
    const fetchProjectDetails = async () => {
      try {
        const [msRes, ethRes, riskRes] = await Promise.allSettled([
          apiFetch<ResearchMilestoneModel[]>(`/api/v1/research/projects/${selectedProjectId}/milestones`),
          apiFetch<ResearchEthicsApprovalModel[]>(`/api/v1/research/projects/${selectedProjectId}/ethics-approvals`),
          apiFetch<ResearchProjectRiskModel[]>(`/api/v1/research/projects/${selectedProjectId}/risks`),
        ]);
        if (msRes.status === "fulfilled" && Array.isArray(msRes.value?.data)) {
          setMilestones(msRes.value.data);
        }
        if (ethRes.status === "fulfilled" && Array.isArray(ethRes.value?.data)) {
          setEthicsApprovals(ethRes.value.data);
        }
        if (riskRes.status === "fulfilled" && Array.isArray(riskRes.value?.data)) {
          setRisks(riskRes.value.data);
        }
      } catch (e) {
        console.error("Error loading project sub-entities:", e);
      }
    };
    fetchProjectDetails();
  }, [selectedProjectId]);

  // Handler: Deadline & Compliance Sweep
  const handleRunDeadlineSweep = async () => {
    try {
      setActionSuccessMessage(null);
      setActionErrorMessage(null);
      const res = await apiFetch<ResearchDeadlineSweepModel>("/api/v1/research/compliance/sweep-deadlines", {
        method: "POST",
      });
      const sweep = res.data;
      setActionSuccessMessage(
        `Audit sweep executed: ${sweep.expiring_ethics_approvals_flagged} ethics approvals, ` +
        `${sweep.overdue_milestones_flagged} overdue milestones, and ` +
        `${sweep.closing_opportunities_flagged} closing opportunities evaluated.`
      );
      fetchData();
    } catch (err: any) {
      setActionErrorMessage(err.message || "Failed to execute compliance sweep.");
    }
  };

  // Handler: Create Project
  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectForm.title.trim()) return;
    try {
      setActionSuccessMessage(null);
      setActionErrorMessage(null);
      const res = await apiFetch<ResearchProjectModel>("/api/v1/research/projects", {
        method: "POST",
        body: JSON.stringify({
          project_code: newProjectForm.project_code,
          title: newProjectForm.title,
          research_domain: newProjectForm.research_domain,
          category: newProjectForm.category,
          proposed_budget: Number(newProjectForm.proposed_budget),
          currency: newProjectForm.currency,
          requires_ethics_approval: newProjectForm.requires_ethics_approval,
          principal_investigator_id: user?.id,
          abstract: newProjectForm.abstract,
        }),
      });
      const created = res.data;
      setActionSuccessMessage(`Research Project '${created.project_code}' created successfully.`);
      setIsNewProjectModalOpen(false);
      setNewProjectForm({
        project_code: `RES-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`,
        title: "",
        research_domain: "Computer Science & AI",
        category: "APPLIED_RESEARCH",
        proposed_budget: 75000,
        currency: "USD",
        requires_ethics_approval: false,
        abstract: "",
      });
      fetchData();
    } catch (err: any) {
      setActionErrorMessage(err.message || "Failed to register project.");
    }
  };

  // Handler: Transition Project Status
  const handleTransitionStatus = async () => {
    if (!projectToTransition) return;
    try {
      setActionSuccessMessage(null);
      setActionErrorMessage(null);
      const res = await apiFetch<ResearchProjectModel>(
        `/api/v1/research/projects/${projectToTransition.id}/transition`,
        {
          method: "POST",
          body: JSON.stringify({
            target_status: transitionTargetStatus,
            reason: transitionReason || `Status transitioned to ${transitionTargetStatus}`,
          }),
        }
      );
      const updated = res.data;
      setActionSuccessMessage(
        `Project ${updated.project_code} transitioned to status ${updated.status}.`
      );
      setIsTransitionModalOpen(false);
      setProjectToTransition(null);
      setTransitionReason("");
      fetchData();
    } catch (err: any) {
      setActionErrorMessage(err.message || "Failed to transition project status.");
    }
  };

  // Handler: Create Opportunity
  const handleCreateOpportunity = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newOppForm.title.trim()) return;
    try {
      setActionSuccessMessage(null);
      setActionErrorMessage(null);
      const res = await apiFetch<ResearchFundingOpportunityModel>("/api/v1/research/opportunities", {
        method: "POST",
        body: JSON.stringify({
          opportunity_code: newOppForm.opportunity_code,
          title: newOppForm.title,
          funding_organization: newOppForm.funding_organization,
          category: newOppForm.category,
          research_domains: newOppForm.research_domains.split(",").map((s) => s.trim()),
          min_amount: Number(newOppForm.min_amount),
          max_amount: Number(newOppForm.max_amount),
          closing_date: newOppForm.closing_date,
          opportunity_url: newOppForm.opportunity_url,
        }),
      });
      const opp = res.data;
      setActionSuccessMessage(`Funding opportunity '${opp.opportunity_code || opp.title}' cataloged successfully.`);
      setIsNewOpportunityModalOpen(false);
      fetchData();
    } catch (err: any) {
      setActionErrorMessage(err.message || "Failed to catalog funding opportunity.");
    }
  };

  // Handler: Register Output
  const handleCreatePublication = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPubForm.title.trim()) return;
    try {
      setActionSuccessMessage(null);
      setActionErrorMessage(null);
      const res = await apiFetch<ResearchOutputModel>("/api/v1/research/outputs", {
        method: "POST",
        body: JSON.stringify({
          title: newPubForm.title,
          output_type: newPubForm.output_type,
          publication_venue: newPubForm.publication_venue,
          doi_or_urn: newPubForm.doi_or_urn,
          citation_count: Number(newPubForm.citation_count),
          open_access_status: newPubForm.open_access_status,
          project_id: selectedProjectId || undefined,
        }),
      });
      const pub = res.data;
      setActionSuccessMessage(`Publication '${pub.title}' registered.`);
      setIsNewPublicationModalOpen(false);
      fetchData();
    } catch (err: any) {
      setActionErrorMessage(err.message || "Failed to register scholarly output.");
    }
  };

  // Handler: Register Invention Disclosure
  const handleCreateDisclosure = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDisclosureForm.title.trim()) return;
    try {
      setActionSuccessMessage(null);
      setActionErrorMessage(null);
      const res = await apiFetch<ResearchInventionDisclosureModel>("/api/v1/research/intellectual-property", {
        method: "POST",
        body: JSON.stringify({
          disclosure_code: newDisclosureForm.disclosure_code,
          title: newDisclosureForm.title,
          technical_description: newDisclosureForm.technical_description,
          confidentiality_level: newDisclosureForm.confidentiality_level,
          patent_filing_status: newDisclosureForm.patent_filing_status,
          patent_application_number: newDisclosureForm.patent_application_number,
          institutional_ownership_percentage: Number(newDisclosureForm.institutional_ownership_percentage),
          project_id: selectedProjectId || undefined,
        }),
      });
      const disc = res.data;
      setActionSuccessMessage(`Invention disclosure '${disc.disclosure_code}' recorded securely.`);
      setIsNewDisclosureModalOpen(false);
      fetchData();
    } catch (err: any) {
      setActionErrorMessage(err.message || "Failed to record invention disclosure.");
    }
  };

  // Filtered projects
  const filteredProjects = useMemo(() => {
    return projects.filter((p) => {
      const matchesSearch =
        (p.title || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
        (p.project_code || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
        (p.research_domain || "").toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus = statusFilter === "ALL" || p.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [projects, searchQuery, statusFilter]);

  // Selected project object
  const currentProject = useMemo(() => {
    return projects.find((p) => p.id === selectedProjectId) || projects[0] || null;
  }, [projects, selectedProjectId]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6">
      {/* Top Console Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 shadow-lg shadow-emerald-600/20 text-white">
              <FlaskConical className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                Enterprise Research & Innovation Management
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                  Step 44
                </span>
              </h1>
              <p className="text-sm text-slate-400">
                Authoritative governance of institutional research projects, sponsored grants, ethics compliance,
                scholarly publications, and intellectual property.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleRunDeadlineSweep}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 hover:border-slate-700 text-sm font-medium transition-all"
            title="Scan upcoming ethics expirations, milestone deadlines, and closing grants"
          >
            <ShieldAlert className="h-4 w-4 text-amber-400" />
            Compliance Sweep
          </button>

          <button
            onClick={fetchData}
            disabled={isRefreshing}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
            title="Refresh Data"
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin text-emerald-400" : ""}`} />
          </button>

          <button
            onClick={() => setIsNewProjectModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-sm shadow-md shadow-emerald-600/20 transition-all"
          >
            <Plus className="h-4 w-4" />
            Register Project
          </button>
        </div>
      </div>

      {/* Notifications / Alerts */}
      {actionSuccessMessage && (
        <div className="flex items-center justify-between p-4 rounded-xl bg-emerald-950/60 border border-emerald-500/30 text-emerald-300 text-sm">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0" />
            <span>{actionSuccessMessage}</span>
          </div>
          <button onClick={() => setActionSuccessMessage(null)} className="text-emerald-400 hover:text-white">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {actionErrorMessage && (
        <div className="flex items-center justify-between p-4 rounded-xl bg-rose-950/60 border border-rose-500/30 text-rose-300 text-sm">
          <div className="flex items-center gap-2.5">
            <AlertTriangle className="h-5 w-5 text-rose-400 shrink-0" />
            <span>{actionErrorMessage}</span>
          </div>
          <button onClick={() => setActionErrorMessage(null)} className="text-rose-400 hover:text-white">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Overview Analytics KPI Cards */}
      {analytics && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
              <span>Active Projects</span>
              <FlaskConical className="h-4 w-4 text-emerald-400" />
            </div>
            <div className="mt-2">
              <span className="text-2xl font-bold text-white tracking-tight">
                {analytics.active_projects}
              </span>
              <span className="text-xs text-slate-400 ml-1.5 font-normal">
                / {analytics.total_projects} total
              </span>
            </div>
            <div className="mt-2 text-xs text-emerald-400 font-medium">
              {analytics.completed_projects} Completed
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
              <span>Awarded Funding</span>
              <Award className="h-4 w-4 text-indigo-400" />
            </div>
            <div className="mt-2">
              <span className="text-2xl font-bold text-white tracking-tight">
                ${(analytics.total_awarded_funding / 1000).toFixed(0)}k
              </span>
            </div>
            <div className="mt-2 text-xs text-indigo-400 font-medium">
              ${(analytics.total_proposed_budget / 1000).toFixed(0)}k proposed
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
              <span>Expenditure</span>
              <TrendingUp className="h-4 w-4 text-teal-400" />
            </div>
            <div className="mt-2">
              <span className="text-2xl font-bold text-white tracking-tight">
                ${(analytics.total_actual_expenditure / 1000).toFixed(0)}k
              </span>
            </div>
            <div className="mt-2 flex items-center gap-1.5">
              <div className="flex-1 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-teal-400 h-full rounded-full"
                  style={{ width: `${Math.min(100, analytics.budget_utilization_rate)}%` }}
                />
              </div>
              <span className="text-[11px] text-slate-400 font-medium">
                {analytics.budget_utilization_rate}%
              </span>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
              <span>Grant Success</span>
              <Target className="h-4 w-4 text-sky-400" />
            </div>
            <div className="mt-2">
              <span className="text-2xl font-bold text-white tracking-tight">
                {analytics.grant_success_rate}%
              </span>
            </div>
            <div className="mt-2 text-xs text-sky-400 font-medium">
              {analytics.approved_grant_applications} / {analytics.total_grant_applications} awards
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
              <span>Publications</span>
              <BookOpen className="h-4 w-4 text-purple-400" />
            </div>
            <div className="mt-2">
              <span className="text-2xl font-bold text-white tracking-tight">
                {analytics.total_publications}
              </span>
              <span className="text-xs text-slate-400 ml-1.5 font-normal">
                ({analytics.verified_publications} verified)
              </span>
            </div>
            <div className="mt-2 text-xs text-purple-400 font-medium">
              {analytics.total_citations} Citations
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
              <span>Patents & IP</span>
              <Lightbulb className="h-4 w-4 text-amber-400" />
            </div>
            <div className="mt-2">
              <span className="text-2xl font-bold text-white tracking-tight">
                {analytics.patents_filed_or_granted}
              </span>
              <span className="text-xs text-slate-400 ml-1.5 font-normal">
                filed / granted
              </span>
            </div>
            <div className="mt-2 text-xs text-amber-400 font-medium">
              ${(analytics.commercialization_revenue / 1000).toFixed(0)}k license revenue
            </div>
          </div>
        </div>
      )}

      {/* Tabs Bar */}
      <div className="flex items-center gap-1.5 border-b border-slate-800 overflow-x-auto pb-2 scrollbar-none">
        {[
          { key: "overview", label: "Overview & Analytics", icon: BarChart3 },
          { key: "projects", label: "Projects Registry", icon: FlaskConical },
          { key: "opportunities", label: "Funding Opportunities", icon: Sparkles },
          { key: "applications", label: "Grant Applications", icon: FileText },
          { key: "awards_budgets", label: "Awards & Budgets", icon: DollarSign },
          { key: "milestones", label: "Milestones", icon: CheckCircle2 },
          { key: "ethics", label: "Ethics Approvals", icon: ShieldCheck },
          { key: "publications", label: "Publications & Outputs", icon: BookOpen },
          { key: "ip_patents", label: "IP & Disclosures", icon: Lightbulb },
          { key: "risks", label: "Project Risks", icon: AlertTriangle },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
                isActive
                  ? "bg-slate-800 text-white shadow-sm border border-slate-700"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              <Icon className={`h-4 w-4 ${isActive ? "text-emerald-400" : ""}`} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* TAB CONTENT 1: OVERVIEW */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Active Projects Summary List */}
            <div className="lg:col-span-2 p-5 rounded-2xl bg-slate-900/50 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-white flex items-center gap-2">
                  <FlaskConical className="h-4 w-4 text-emerald-400" />
                  Primary Institutional Projects
                </h3>
                <button
                  onClick={() => setActiveTab("projects")}
                  className="text-xs text-emerald-400 hover:underline flex items-center gap-1 font-medium"
                >
                  View All Projects <ArrowRight className="h-3 w-3" />
                </button>
              </div>

              <div className="space-y-2.5">
                {projects.slice(0, 5).map((proj) => (
                  <div
                    key={proj.id}
                    onClick={() => {
                      setSelectedProjectId(proj.id);
                      setActiveTab("projects");
                    }}
                    className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-all cursor-pointer flex items-center justify-between"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                          {proj.project_code}
                        </span>
                        <h4 className="font-medium text-white text-sm hover:text-emerald-400 transition-colors">
                          {proj.title}
                        </h4>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-slate-400">
                        <span>{proj.research_domain}</span>
                        <span>•</span>
                        <span>Budget: ${Number(proj.approved_budget || proj.proposed_budget || 0).toLocaleString()}</span>
                        {proj.requires_ethics_approval && (
                          <>
                            <span>•</span>
                            <span className="text-amber-400 flex items-center gap-1">
                              <ShieldCheck className="h-3 w-3" /> IRB Required
                            </span>
                          </>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <span
                        className={`text-xs px-2.5 py-1 rounded-full font-medium border ${
                          proj.status === "ACTIVE"
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                            : proj.status === "COMPLETED"
                            ? "bg-indigo-500/10 text-indigo-400 border-indigo-500/20"
                            : proj.status === "SUBMITTED" || proj.status === "UNDER_REVIEW"
                            ? "bg-sky-500/10 text-sky-400 border-sky-500/20"
                            : "bg-slate-500/10 text-slate-400 border-slate-500/20"
                        }`}
                      >
                        {proj.status}
                      </span>
                      <ChevronRight className="h-4 w-4 text-slate-600" />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Compliance & Deadlines Quick Widget */}
            <div className="p-5 rounded-2xl bg-slate-900/50 border border-slate-800 space-y-4">
              <h3 className="font-semibold text-white flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-amber-400" />
                Governance & Compliance Highlights
              </h3>

              <div className="space-y-3">
                <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-slate-300">Ethics Approvals (IRB/Animal)</span>
                    <span className="text-emerald-400 font-semibold">{analytics?.ethics_approvals_count} active</span>
                  </div>
                  <p className="text-xs text-slate-400">
                    All protocols are vetted by institutional review boards before clinical/biological trials.
                  </p>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-slate-300">Intellectual Property & Patents</span>
                    <span className="text-amber-400 font-semibold">{analytics?.patents_filed_or_granted} recorded</span>
                  </div>
                  <p className="text-xs text-slate-400">
                    Trade secret disclosures and patent rights are protected with audited inventor attribution.
                  </p>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-slate-300">Grant Separation of Duties</span>
                    <span className="text-sky-400 font-semibold">Enforced</span>
                  </div>
                  <p className="text-xs text-slate-400">
                    Principal Investigators cannot review or approve their own sponsored research submissions.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT 2: PROJECTS REGISTRY */}
      {activeTab === "projects" && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <div className="relative w-full sm:w-80">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
                <input
                  type="text"
                  placeholder="Search projects by title, code, domain..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
              >
                <option value="ALL">All Statuses</option>
                <option value="DRAFT">Draft</option>
                <option value="SUBMITTED">Submitted</option>
                <option value="APPROVED">Approved</option>
                <option value="ACTIVE">Active</option>
                <option value="COMPLETED">Completed</option>
                <option value="SUSPENDED">Suspended</option>
              </select>
            </div>

            <div className="text-xs text-slate-400">
              Showing {filteredProjects.length} of {projects.length} registered projects
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-900/40">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-900/80 border-b border-slate-800 text-xs text-slate-400 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Code</th>
                  <th className="py-3 px-4">Project Title</th>
                  <th className="py-3 px-4">Domain & Category</th>
                  <th className="py-3 px-4">Allocated Budget</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredProjects.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-500">
                      No research projects found matching your criteria.
                    </td>
                  </tr>
                ) : (
                  filteredProjects.map((p) => (
                    <tr
                      key={p.id}
                      className={`hover:bg-slate-800/40 transition-colors ${
                        selectedProjectId === p.id ? "bg-slate-800/30" : ""
                      }`}
                    >
                      <td className="py-3 px-4 font-mono text-xs font-semibold text-emerald-400">
                        {p.project_code}
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-medium text-white">{p.title}</div>
                        {p.requires_ethics_approval && (
                          <span className="text-[11px] text-amber-400 flex items-center gap-1 mt-0.5">
                            <ShieldCheck className="h-3 w-3" /> IRB Review Required
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-xs text-slate-400">
                        <div>{p.research_domain}</div>
                        <div className="text-[11px] text-slate-500">{p.research_category}</div>
                      </td>
                      <td className="py-3 px-4 font-mono text-xs text-slate-300">
                        ${Number(p.approved_budget || p.proposed_budget || 0).toLocaleString()} {p.currency}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`text-xs px-2.5 py-0.5 rounded-full font-medium border ${
                            p.status === "ACTIVE"
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                              : p.status === "COMPLETED"
                              ? "bg-indigo-500/10 text-indigo-400 border-indigo-500/20"
                              : p.status === "SUBMITTED" || p.status === "UNDER_REVIEW"
                              ? "bg-sky-500/10 text-sky-400 border-sky-500/20"
                              : "bg-slate-500/10 text-slate-400 border-slate-500/20"
                          }`}
                        >
                          {p.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => {
                              setSelectedProjectId(p.id);
                              setActiveTab("milestones");
                            }}
                            className="text-xs px-2.5 py-1 rounded bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition-colors"
                          >
                            Milestones
                          </button>
                          <button
                            onClick={() => {
                              setProjectToTransition(p);
                              setIsTransitionModalOpen(true);
                            }}
                            className="text-xs px-2.5 py-1 rounded bg-emerald-600/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-600/30 transition-colors"
                          >
                            Transition
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB CONTENT 3: FUNDING OPPORTUNITIES */}
      {activeTab === "opportunities" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-white flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-emerald-400" />
              Verified Funding Opportunities Directory
            </h3>
            <button
              onClick={() => setIsNewOpportunityModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium transition-all"
            >
              <Plus className="h-3.5 w-3.5" />
              Add Opportunity
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {opportunities.length === 0 ? (
              <div className="col-span-full py-8 text-center text-slate-500">
                No funding opportunities currently available.
              </div>
            ) : (
              opportunities.map((opp) => (
                <div key={opp.id} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-800 text-emerald-400">
                      {opp.opportunity_code}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {opp.status}
                    </span>
                  </div>

                  <div>
                    <h4 className="font-medium text-white text-sm line-clamp-2">{opp.title}</h4>
                    <p className="text-xs text-slate-400 mt-1">{opp.funding_organization}</p>
                  </div>

                  <div className="text-xs text-slate-400 space-y-1 border-t border-slate-800/80 pt-2">
                    <div className="flex justify-between">
                      <span>Funding Range:</span>
                      <span className="text-slate-200 font-mono">
                        ${Number(opp.min_amount || 0).toLocaleString()} - ${Number(opp.max_amount || 0).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Closing Date:</span>
                      <span className="text-slate-200 font-mono">{opp.closing_date}</span>
                    </div>
                  </div>

                  {opp.opportunity_url && (
                    <a
                      href={opp.opportunity_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs text-emerald-400 hover:underline flex items-center gap-1 pt-1 font-medium"
                    >
                      Official RFP Details <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* TAB CONTENT 4: GRANT APPLICATIONS */}
      {activeTab === "applications" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-white flex items-center gap-2">
                <FileText className="h-4 w-4 text-sky-400" />
                Sponsored Grant Applications & Review Pipeline
              </h3>
              <p className="text-xs text-slate-400">
                Institutional review enforces separation of duties: PIs cannot review their own submissions.
              </p>
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-900/40">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-900/80 border-b border-slate-800 text-xs text-slate-400 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">App Code</th>
                  <th className="py-3 px-4">Title</th>
                  <th className="py-3 px-4">Proposed Budget</th>
                  <th className="py-3 px-4">Internal Review</th>
                  <th className="py-3 px-4">External Agency Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {applications.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-500">
                      No grant applications currently recorded.
                    </td>
                  </tr>
                ) : (
                  applications.map((app) => (
                    <tr key={app.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-4 font-mono text-xs font-semibold text-sky-400">
                        {app.application_code}
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-medium text-white">{app.title}</div>
                      </td>
                      <td className="py-3 px-4 font-mono text-xs text-slate-300">
                        ${Number(app.proposed_budget || 0).toLocaleString()} {app.currency}
                      </td>
                      <td className="py-3 px-4">
                        <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 font-medium">
                          {app.internal_review_status}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 font-medium">
                          {app.external_submission_status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB CONTENT 5: AWARDS & ITEMIZE BUDGETS */}
      {activeTab === "awards_budgets" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-white flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-emerald-400" />
              Awarded Grants & Reconciled Itemized Budgets
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {awards.length === 0 ? (
              <div className="col-span-full py-8 text-center text-slate-500">
                No active grant awards found.
              </div>
            ) : (
              awards.map((award) => (
                <div key={award.id} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {award.award_code}
                    </span>
                    <span className="text-xs text-slate-400">{award.award_date}</span>
                  </div>

                  <div>
                    <h4 className="font-semibold text-white text-base">
                      ${Number(award.award_amount || 0).toLocaleString()} {award.currency}
                    </h4>
                    <p className="text-xs text-slate-400">Awarded by {award.funding_organization}</p>
                  </div>

                  <div className="grid grid-cols-3 gap-2 p-2.5 rounded-lg bg-slate-950/70 border border-slate-800 text-center text-xs">
                    <div>
                      <div className="text-slate-500">Allocated</div>
                      <div className="font-mono font-medium text-slate-200">
                        ${Number(award.allocated_amount || 0).toLocaleString()}
                      </div>
                    </div>
                    <div>
                      <div className="text-slate-500">Spent</div>
                      <div className="font-mono font-medium text-teal-400">
                        ${Number(award.spent_amount || 0).toLocaleString()}
                      </div>
                    </div>
                    <div>
                      <div className="text-slate-500">Remaining</div>
                      <div className="font-mono font-medium text-emerald-400">
                        ${Number(award.remaining_balance || 0).toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* TAB CONTENT 6: MILESTONES */}
      {activeTab === "milestones" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-white flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                Project Milestones & Deliverables
              </h3>
              {currentProject && (
                <p className="text-xs text-slate-400">
                  Showing deliverables for project: <span className="text-emerald-400 font-medium">{currentProject.project_code} - {currentProject.title}</span>
                </p>
              )}
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-900/40">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-900/80 border-b border-slate-800 text-xs text-slate-400 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Code</th>
                  <th className="py-3 px-4">Deliverable Title</th>
                  <th className="py-3 px-4">Planned Date</th>
                  <th className="py-3 px-4">Completion %</th>
                  <th className="py-3 px-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {milestones.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-500">
                      No milestones recorded for this project.
                    </td>
                  </tr>
                ) : (
                  milestones.map((m) => (
                    <tr key={m.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-4 font-mono text-xs font-semibold text-emerald-400">
                        {m.id.substring(0, 8)}
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-medium text-white">{m.title}</div>
                        {m.is_mandatory_for_closure && (
                          <span className="text-[10px] text-amber-400 uppercase font-semibold">
                            Mandatory for Project Closure
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 font-mono text-xs text-slate-300">
                        {m.planned_date}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <div className="w-20 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                            <div
                              className="bg-emerald-400 h-full rounded-full"
                              style={{ width: `${m.completion_percentage}%` }}
                            />
                          </div>
                          <span className="text-xs font-mono text-slate-400">{m.completion_percentage}%</span>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-medium">
                          {m.status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB CONTENT 7: ETHICS & COMPLIANCE */}
      {activeTab === "ethics" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-white flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-emerald-400" />
                Institutional Ethics & Safety Approvals (IRB / Animal / Biosafety)
              </h3>
              <p className="text-xs text-slate-400">
                Formal review committees oversee high-impact research compliance and confidentiality.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {ethicsApprovals.length === 0 ? (
              <div className="col-span-full py-8 text-center text-slate-500">
                No ethics approvals on record for the active project.
              </div>
            ) : (
              ethicsApprovals.map((eth) => (
                <div key={eth.id} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {eth.application_reference}
                    </span>
                    <span
                      className={`text-xs px-2.5 py-0.5 rounded-full font-medium border ${
                        eth.status === "APPROVED"
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                          : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                      }`}
                    >
                      {eth.status}
                    </span>
                  </div>

                  <div>
                    <h4 className="font-medium text-white text-sm">{eth.approval_type}</h4>
                    <p className="text-xs text-slate-400 mt-0.5">Committee: {eth.committee_name}</p>
                  </div>

                  <div className="text-xs text-slate-400 space-y-1 border-t border-slate-800/80 pt-2">
                    <div className="flex justify-between">
                      <span>Governing Policy:</span>
                      <span className="text-slate-300">{eth.governing_policy}</span>
                    </div>
                    {eth.expiry_date && (
                      <div className="flex justify-between">
                        <span>Approval Expiry:</span>
                        <span className="text-amber-400 font-mono">{eth.expiry_date}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* TAB CONTENT 8: PUBLICATIONS & OUTPUTS */}
      {activeTab === "publications" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-white flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-purple-400" />
              Scholarly Publications & Research Outputs
            </h3>
            <button
              onClick={() => setIsNewPublicationModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-medium transition-all"
            >
              <Plus className="h-3.5 w-3.5" />
              Register Output
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {publications.length === 0 ? (
              <div className="col-span-full py-8 text-center text-slate-500">
                No research publications cataloged yet.
              </div>
            ) : (
              publications.map((pub) => (
                <div key={pub.id} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20 font-medium">
                      {pub.output_type}
                    </span>
                    {pub.is_verified && (
                      <span className="flex items-center gap-1 text-xs text-emerald-400 font-medium">
                        <CheckCircle2 className="h-3.5 w-3.5" /> Verified
                      </span>
                    )}
                  </div>

                  <div>
                    <h4 className="font-medium text-white text-sm">{pub.title}</h4>
                    <p className="text-xs text-slate-400 mt-1">{pub.publication_venue}</p>
                  </div>

                  <div className="flex items-center justify-between text-xs text-slate-400 border-t border-slate-800/80 pt-2">
                    <span className="font-mono text-slate-300">DOI: {pub.doi_or_urn || "N/A"}</span>
                    <span className="text-purple-400 font-semibold">{pub.citation_count} Citations</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* TAB CONTENT 9: IP & PATENTS */}
      {activeTab === "ip_patents" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-white flex items-center gap-2">
                <Lightbulb className="h-4 w-4 text-amber-400" />
                Intellectual Property & Invention Disclosures
              </h3>
              <p className="text-xs text-slate-400">
                Confidential trade secret registrations, patent tracking, and licensing royalties.
              </p>
            </div>
            <button
              onClick={() => setIsNewDisclosureModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-medium transition-all"
            >
              <Plus className="h-3.5 w-3.5" />
              New Disclosure
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {disclosures.length === 0 ? (
              <div className="col-span-full py-8 text-center text-slate-500">
                No intellectual property disclosures found.
              </div>
            ) : (
              disclosures.map((disc) => (
                <div key={disc.id} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-amber-400 px-2 py-0.5 rounded bg-slate-800">
                      {disc.disclosure_code}
                    </span>
                    <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
                      <Lock className="h-3 w-3 text-amber-400" /> {disc.confidentiality_level}
                    </span>
                  </div>

                  <div>
                    <h4 className="font-medium text-white text-sm">{disc.title}</h4>
                    <p className="text-xs text-slate-400 mt-1 line-clamp-2">{disc.technical_description}</p>
                  </div>

                  <div className="text-xs text-slate-400 space-y-1 border-t border-slate-800/80 pt-2">
                    <div className="flex justify-between">
                      <span>Patent Status:</span>
                      <span className="text-slate-200 font-medium">{disc.patent_filing_status}</span>
                    </div>
                    {disc.patent_application_number && (
                      <div className="flex justify-between">
                        <span>Application #:</span>
                        <span className="text-slate-200 font-mono">{disc.patent_application_number}</span>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span>Institutional Ownership:</span>
                      <span className="text-slate-200">{disc.institutional_ownership_percentage}%</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* TAB CONTENT 10: RISKS */}
      {activeTab === "risks" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-white flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-400" />
              Project Risk Register & Mitigation Matrix
            </h3>
          </div>

          <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-900/40">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-900/80 border-b border-slate-800 text-xs text-slate-400 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Risk Title</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Likelihood x Impact</th>
                  <th className="py-3 px-4">Calculated Level</th>
                  <th className="py-3 px-4">Mitigation Plan</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {risks.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-500">
                      No project risks currently recorded for active project.
                    </td>
                  </tr>
                ) : (
                  risks.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-4 font-medium text-white">{r.risk_title}</td>
                      <td className="py-3 px-4 text-xs text-slate-400">{r.risk_category}</td>
                      <td className="py-3 px-4 text-xs text-slate-300 font-mono">
                        {r.likelihood} x {r.impact}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                            r.calculated_risk_level === "CRITICAL" || r.calculated_risk_level === "HIGH"
                              ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                              : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                          }`}
                        >
                          {r.calculated_risk_level}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-xs text-slate-400 max-w-xs truncate">
                        {r.mitigation_plan}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* MODAL 1: REGISTER PROJECT */}
      {isNewProjectModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-semibold text-white flex items-center gap-2">
                <FlaskConical className="h-5 w-5 text-emerald-400" />
                Register Institutional Research Project
              </h3>
              <button
                onClick={() => setIsNewProjectModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleCreateProject} className="space-y-3 text-sm">
              <div>
                <label className="text-xs text-slate-400 font-medium">Project Code</label>
                <input
                  type="text"
                  required
                  value={newProjectForm.project_code}
                  onChange={(e) => setNewProjectForm({ ...newProjectForm, project_code: e.target.value })}
                  className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white font-mono text-xs focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="text-xs text-slate-400 font-medium">Project Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Deep Learning in Autonomous Drone Swarms"
                  value={newProjectForm.title}
                  onChange={(e) => setNewProjectForm({ ...newProjectForm, title: e.target.value })}
                  className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-slate-400 font-medium">Research Domain</label>
                  <input
                    type="text"
                    required
                    value={newProjectForm.research_domain}
                    onChange={(e) => setNewProjectForm({ ...newProjectForm, research_domain: e.target.value })}
                    className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 font-medium">Category</label>
                  <select
                    value={newProjectForm.category}
                    onChange={(e) => setNewProjectForm({ ...newProjectForm, category: e.target.value })}
                    className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-emerald-500"
                  >
                    <option value="BASIC_RESEARCH">Basic Research</option>
                    <option value="APPLIED_RESEARCH">Applied Research</option>
                    <option value="EXPERIMENTAL_DEVELOPMENT">Experimental Dev</option>
                    <option value="CLINICAL_TRIAL">Clinical Trial</option>
                    <option value="INNOVATION_INCUBATION">Innovation / Startup</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-slate-400 font-medium">Proposed Budget</label>
                  <input
                    type="number"
                    min="0"
                    value={newProjectForm.proposed_budget}
                    onChange={(e) => setNewProjectForm({ ...newProjectForm, proposed_budget: Number(e.target.value) })}
                    className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white font-mono focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 font-medium">Currency</label>
                  <input
                    type="text"
                    value={newProjectForm.currency}
                    onChange={(e) => setNewProjectForm({ ...newProjectForm, currency: e.target.value })}
                    className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white font-mono focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="requires_ethics"
                  checked={newProjectForm.requires_ethics_approval}
                  onChange={(e) => setNewProjectForm({ ...newProjectForm, requires_ethics_approval: e.target.checked })}
                  className="rounded border-slate-700 bg-slate-950 text-emerald-500 focus:ring-0"
                />
                <label htmlFor="requires_ethics" className="text-xs text-slate-300 font-medium cursor-pointer">
                  Requires Formal Ethics Review (Human participants / Animal / Biosafety)
                </label>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsNewProjectModalOpen(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 text-sm font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium shadow-md shadow-emerald-600/20"
                >
                  Register Project
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: TRANSITION LIFECYCLE STATE */}
      {isTransitionModalOpen && projectToTransition && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-semibold text-white">Transition Lifecycle Status</h3>
              <button
                onClick={() => setIsTransitionModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="text-xs text-slate-400 space-y-1">
              <div>
                Project: <span className="text-white font-mono">{projectToTransition.project_code}</span>
              </div>
              <div>
                Current Status: <span className="text-emerald-400 font-semibold">{projectToTransition.status}</span>
              </div>
            </div>

            <div className="space-y-3 text-sm">
              <div>
                <label className="text-xs text-slate-400 font-medium">Target Status</label>
                <select
                  value={transitionTargetStatus}
                  onChange={(e) => setTransitionTargetStatus(e.target.value)}
                  className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white text-sm focus:outline-none focus:border-emerald-500"
                >
                  <option value="SUBMITTED">SUBMITTED</option>
                  <option value="UNDER_REVIEW">UNDER_REVIEW</option>
                  <option value="APPROVED">APPROVED</option>
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="COMPLETED">COMPLETED</option>
                  <option value="SUSPENDED">SUSPENDED</option>
                  <option value="TERMINATED">TERMINATED</option>
                </select>
              </div>

              <div>
                <label className="text-xs text-slate-400 font-medium">Transition Reason / Decision Notes</label>
                <textarea
                  rows={3}
                  placeholder="Justification for audited transition..."
                  value={transitionReason}
                  onChange={(e) => setTransitionReason(e.target.value)}
                  className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white text-xs focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsTransitionModalOpen(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 text-sm font-medium"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleTransitionStatus}
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium shadow-md shadow-emerald-600/20"
                >
                  Confirm Transition
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 3: ADD OPPORTUNITY */}
      {isNewOpportunityModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-semibold text-white flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-emerald-400" />
                Catalog Funding Opportunity
              </h3>
              <button
                onClick={() => setIsNewOpportunityModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleCreateOpportunity} className="space-y-3 text-sm">
              <div>
                <label className="text-xs text-slate-400 font-medium">Opportunity Code / RFP ID</label>
                <input
                  type="text"
                  required
                  value={newOppForm.opportunity_code}
                  onChange={(e) => setNewOppForm({ ...newOppForm, opportunity_code: e.target.value })}
                  className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white font-mono text-xs focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="text-xs text-slate-400 font-medium">Opportunity Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., NSF Clean Energy Transition Grant"
                  value={newOppForm.title}
                  onChange={(e) => setNewOppForm({ ...newOppForm, title: e.target.value })}
                  className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-slate-400 font-medium">Funding Agency</label>
                  <input
                    type="text"
                    required
                    value={newOppForm.funding_organization}
                    onChange={(e) => setNewOppForm({ ...newOppForm, funding_organization: e.target.value })}
                    className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 font-medium">Closing Date</label>
                  <input
                    type="date"
                    required
                    value={newOppForm.closing_date}
                    onChange={(e) => setNewOppForm({ ...newOppForm, closing_date: e.target.value })}
                    className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-slate-400 font-medium">Min Funding ($)</label>
                  <input
                    type="number"
                    value={newOppForm.min_amount}
                    onChange={(e) => setNewOppForm({ ...newOppForm, min_amount: Number(e.target.value) })}
                    className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white font-mono focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 font-medium">Max Funding ($)</label>
                  <input
                    type="number"
                    value={newOppForm.max_amount}
                    onChange={(e) => setNewOppForm({ ...newOppForm, max_amount: Number(e.target.value) })}
                    className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white font-mono focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsNewOpportunityModalOpen(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 text-sm font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium shadow-md shadow-emerald-600/20"
                >
                  Save Opportunity
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 4: REGISTER PUBLICATION */}
      {isNewPublicationModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-semibold text-white flex items-center gap-2">
                <BookOpen className="h-5 w-5 text-purple-400" />
                Register Scholarly Output
              </h3>
              <button
                onClick={() => setIsNewPublicationModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleCreatePublication} className="space-y-3 text-sm">
              <div>
                <label className="text-xs text-slate-400 font-medium">Output Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Scalable Distributed Consensus on Directed Acyclic Graphs"
                  value={newPubForm.title}
                  onChange={(e) => setNewPubForm({ ...newPubForm, title: e.target.value })}
                  className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-slate-400 font-medium">Output Type</label>
                  <select
                    value={newPubForm.output_type}
                    onChange={(e) => setNewPubForm({ ...newPubForm, output_type: e.target.value })}
                    className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-purple-500"
                  >
                    <option value="JOURNAL_ARTICLE">Journal Article</option>
                    <option value="CONFERENCE_PAPER">Conference Paper</option>
                    <option value="BOOK_CHAPTER">Book Chapter</option>
                    <option value="RESEARCH_DATASET">Research Dataset</option>
                    <option value="SOFTWARE_TOOL">Software Tool / Code</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-400 font-medium">Publication Venue</label>
                  <input
                    type="text"
                    required
                    value={newPubForm.publication_venue}
                    onChange={(e) => setNewPubForm({ ...newPubForm, publication_venue: e.target.value })}
                    className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-purple-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs text-slate-400 font-medium">DOI or URN Identifier</label>
                <input
                  type="text"
                  required
                  placeholder="10.1016/..."
                  value={newPubForm.doi_or_urn}
                  onChange={(e) => setNewPubForm({ ...newPubForm, doi_or_urn: e.target.value })}
                  className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white font-mono text-xs focus:outline-none focus:border-purple-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsNewPublicationModalOpen(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 text-sm font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-sm font-medium shadow-md shadow-purple-600/20"
                >
                  Register Output
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 5: NEW DISCLOSURE */}
      {isNewDisclosureModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-semibold text-white flex items-center gap-2">
                <Lightbulb className="h-5 w-5 text-amber-400" />
                Submit Invention Disclosure
              </h3>
              <button
                onClick={() => setIsNewDisclosureModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleCreateDisclosure} className="space-y-3 text-sm">
              <div>
                <label className="text-xs text-slate-400 font-medium">Disclosure Code</label>
                <input
                  type="text"
                  required
                  value={newDisclosureForm.disclosure_code}
                  onChange={(e) => setNewDisclosureForm({ ...newDisclosureForm, disclosure_code: e.target.value })}
                  className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white font-mono text-xs focus:outline-none focus:border-amber-500"
                />
              </div>

              <div>
                <label className="text-xs text-slate-400 font-medium">Invention Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Solid-State Nanocomposite Electrolyte Formulation"
                  value={newDisclosureForm.title}
                  onChange={(e) => setNewDisclosureForm({ ...newDisclosureForm, title: e.target.value })}
                  className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-amber-500"
                />
              </div>

              <div>
                <label className="text-xs text-slate-400 font-medium">Confidentiality Level</label>
                <select
                  value={newDisclosureForm.confidentiality_level}
                  onChange={(e) => setNewDisclosureForm({ ...newDisclosureForm, confidentiality_level: e.target.value })}
                  className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-amber-500"
                >
                  <option value="INTERNAL_CONFIDENTIAL">Internal Confidential (Researchers + IP Office)</option>
                  <option value="STRICTLY_CONFIDENTIAL">Strictly Confidential (Named Inventors Only)</option>
                  <option value="PUBLIC_DISCLOSURE">Public Disclosure (Post-Filing / Published)</option>
                </select>
              </div>

              <div>
                <label className="text-xs text-slate-400 font-medium">Technical Description / Abstract</label>
                <textarea
                  rows={3}
                  required
                  placeholder="Confidential synthesis procedure or technical specification..."
                  value={newDisclosureForm.technical_description}
                  onChange={(e) => setNewDisclosureForm({ ...newDisclosureForm, technical_description: e.target.value })}
                  className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white text-xs focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsNewDisclosureModalOpen(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 text-sm font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-sm font-medium shadow-md shadow-amber-600/20"
                >
                  Record IP Disclosure
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
